import os
import re
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
import pymysql

app = Flask(__name__)
app.secret_key = os.urandom(24)

DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': '12345',
    'database': 'taxi_service',
    'charset': 'utf8mb4',
    'cursorclass': pymysql.cursors.DictCursor
}

DEFAULT_THEME = '#6366f1'
HEX_COLOR_RE = re.compile(r'^#[0-9a-fA-F]{6}$')
MAX_TARIFF = Decimal('99999999.99')


def get_db_connection():
    try:
        return pymysql.connect(**DB_CONFIG)
    except Exception as e:
        print(f"Ошибка подключения к БД: {e}")
        return None


def parse_tariff(raw):
    try:
        value = Decimal(str(raw).strip().replace(',', '.').replace(' ', ''))
        if not value.is_finite():
            raise ValueError('not finite')
        value = value.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    except (InvalidOperation, ValueError):
        raise ValueError('invalid tariff')
    if value < 0 or value > MAX_TARIFF:
        raise ValueError('tariff out of range')
    return value


def serialize_car(row):
    car = dict(row)
    tariff = car.get('tariff')
    car['tariff'] = float(tariff) if tariff is not None else 0.0
    return car


def ensure_schema():
    conn = get_db_connection()
    if not conn:
        return
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT COUNT(*) AS cnt FROM information_schema.COLUMNS "
                "WHERE TABLE_SCHEMA = %s AND LOWER(TABLE_NAME) = 'car' AND COLUMN_NAME = 'tariff'",
                (DB_CONFIG['database'],)
            )
            row = cursor.fetchone()
            if row and int(row['cnt']) == 0:
                cursor.execute(
                    "ALTER TABLE Car ADD COLUMN tariff DECIMAL(10, 2) NOT NULL DEFAULT 0.00 "
                    "COMMENT 'Тариф (цена поездки)'"
                )
        conn.commit()
    except Exception as e:
        print(f"Не удалось проверить структуру БД: {e}")
    finally:
        conn.close()


@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        if not username:
            flash('Введите имя пользователя!', 'warning')
            return redirect(url_for('login'))

        conn = get_db_connection()
        if conn:
            try:
                with conn.cursor() as cursor:
                    cursor.execute("SELECT name, is_admin FROM Passenger WHERE name = %s LIMIT 1", (username,))
                    user = cursor.fetchone()

                    if user:
                        session['current_user'] = user['name']
                        session['is_admin_user'] = bool(user['is_admin'])
                        session['theme_color'] = DEFAULT_THEME
                        return redirect(url_for('main_screen'))
                    else:
                        flash(f"Пользователь '{username}' не найден в системе. Доступ отклонен.", 'danger')
            finally:
                conn.close()
        else:
            flash('Внутренняя ошибка базы данных.', 'danger')

    return render_template('login.html')


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))


@app.route('/main')
def main_screen():
    if 'current_user' not in session:
        return redirect(url_for('login'))
    theme_color = session.get('theme_color', DEFAULT_THEME)
    if not HEX_COLOR_RE.match(str(theme_color)):
        theme_color = DEFAULT_THEME
    return render_template('main.html',
                           user=session['current_user'],
                           is_admin=bool(session.get('is_admin_user')),
                           theme_color=theme_color)


@app.route('/api/save_theme', methods=['POST'])
def save_theme():
    if 'current_user' in session:
        data = request.get_json(silent=True)
        if data and isinstance(data.get('color'), str) and HEX_COLOR_RE.match(data['color']):
            session['theme_color'] = data['color']
            return jsonify({'status': 'success'})
    return jsonify({'status': 'error'}), 400


@app.route('/api/cars')
def api_load_data():
    if 'current_user' not in session:
        return jsonify([])

    search_text = request.args.get('search', '').strip()
    filter_color = request.args.get('color', '').strip()

    conn = get_db_connection()
    cars = []
    if conn:
        try:
            with conn.cursor() as cursor:
                query = "SELECT * FROM Car WHERE 1=1"
                params = []

                if search_text:
                    query += " AND (brand LIKE %s OR model LIKE %s)"
                    params.extend([f"%{search_text}%", f"%{search_text}%"])

                if filter_color:
                    query += " AND color LIKE %s"
                    params.append(f"%{filter_color}%")

                query += " ORDER BY car_id"
                cursor.execute(query, params)
                cars = [serialize_car(row) for row in cursor.fetchall()]
        finally:
            conn.close()
    return jsonify(cars)


@app.route('/api/update_tariff/<int:car_id>', methods=['POST'])
def update_tariff(car_id):
    if not session.get('is_admin_user'):
        return jsonify({'status': 'error', 'message': 'Недостаточно прав для изменения тарифа.'}), 403

    data = request.get_json(silent=True) or {}
    try:
        tariff = parse_tariff(data.get('tariff', ''))
    except ValueError:
        return jsonify({'status': 'error', 'message': 'Тариф должен быть числом от 0 до 99 999 999.99.'}), 400

    conn = get_db_connection()
    if not conn:
        return jsonify({'status': 'error', 'message': 'Внутренняя ошибка базы данных.'}), 500
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT car_id FROM Car WHERE car_id = %s", (car_id,))
            if not cursor.fetchone():
                return jsonify({'status': 'error', 'message': 'Автомобиль не найден.'}), 404
            cursor.execute("UPDATE Car SET tariff = %s WHERE car_id = %s", (tariff, car_id))
        conn.commit()
        return jsonify({'status': 'success', 'car_id': car_id, 'tariff': float(tariff)})
    except Exception as e:
        print(f"Ошибка обновления тарифа: {e}")
        return jsonify({'status': 'error', 'message': 'Не удалось сохранить тариф.'}), 500
    finally:
        conn.close()


BULK_OPERATORS = {'lt': '<', 'lte': '<=', 'eq': '=', 'gte': '>=', 'gt': '>', 'all': None}


@app.route('/api/bulk_tariff', methods=['POST'])
def bulk_tariff():
    if not session.get('is_admin_user'):
        return jsonify({'status': 'error', 'message': 'Недостаточно прав для изменения тарифов.'}), 403

    data = request.get_json(silent=True) or {}
    operator = data.get('operator')
    if operator not in BULK_OPERATORS:
        return jsonify({'status': 'error', 'message': 'Неизвестное условие отбора.'}), 400

    try:
        new_tariff = parse_tariff(data.get('new_tariff', ''))
    except ValueError:
        return jsonify({'status': 'error', 'message': 'Новый тариф должен быть числом от 0 до 99 999 999.99.'}), 400

    threshold = None
    if operator != 'all':
        try:
            threshold = parse_tariff(data.get('threshold', ''))
        except ValueError:
            return jsonify({'status': 'error', 'message': 'Пороговое значение должно быть числом от 0 до 99 999 999.99.'}), 400

    conn = get_db_connection()
    if not conn:
        return jsonify({'status': 'error', 'message': 'Внутренняя ошибка базы данных.'}), 500
    try:
        with conn.cursor() as cursor:
            if operator == 'all':
                cursor.execute("SELECT COUNT(*) AS cnt FROM Car")
                matched = int(cursor.fetchone()['cnt'])
                cursor.execute("UPDATE Car SET tariff = %s", (new_tariff,))
            else:
                sql_op = BULK_OPERATORS[operator]
                cursor.execute("SELECT COUNT(*) AS cnt FROM Car WHERE tariff " + sql_op + " %s", (threshold,))
                matched = int(cursor.fetchone()['cnt'])
                cursor.execute("UPDATE Car SET tariff = %s WHERE tariff " + sql_op + " %s", (new_tariff, threshold))
        conn.commit()
        return jsonify({'status': 'success', 'updated': matched, 'tariff': float(new_tariff)})
    except Exception as e:
        conn.rollback()
        print(f"Ошибка массового обновления тарифов: {e}")
        return jsonify({'status': 'error', 'message': 'Не удалось обновить тарифы.'}), 500
    finally:
        conn.close()


@app.route('/add_car', methods=['POST'])
def add_car():
    if not session.get('is_admin_user'):
        flash('Доступ ограничен.', 'danger')
        return redirect(url_for('main_screen'))

    brand = request.form.get('brand', '').strip()
    model = request.form.get('model', '').strip()
    plate = request.form.get('plate', '').strip()
    color = request.form.get('color', '').strip()
    driver = request.form.get('driver_id', '').strip()
    tariff_raw = request.form.get('tariff', '').strip()

    if not (brand and model and plate and color and driver and tariff_raw):
        flash('Заполните абсолютно все поля спецификации автомобиля.', 'warning')
        return redirect(url_for('main_screen'))

    try:
        driver_id = int(driver)
    except ValueError:
        flash('ID водителя должен быть целым числом.', 'danger')
        return redirect(url_for('main_screen'))

    try:
        tariff = parse_tariff(tariff_raw)
    except ValueError:
        flash('Тариф должен быть числом от 0 до 99 999 999.99.', 'danger')
        return redirect(url_for('main_screen'))

    conn = get_db_connection()
    if conn:
        try:
            with conn.cursor() as cursor:
                cursor.execute("SELECT driver_id FROM Driver WHERE driver_id = %s", (driver_id,))
                if not cursor.fetchone():
                    flash(f"Водитель с ID {driver_id} отсутствует в реестре!", 'danger')
                    return redirect(url_for('main_screen'))

                sql = ("INSERT INTO Car (brand, model, license_plate, color, driver_id, tariff) "
                       "VALUES (%s, %s, %s, %s, %s, %s)")
                cursor.execute(sql, (brand, model, plate, color, driver_id, tariff))
            conn.commit()
            flash('Транспортное средство успешно интегрировано в автопарк.', 'success')
        except pymysql.err.IntegrityError:
            flash('Конфликт данных: Этот гос. номер или ID водителя уже зарегистрированы!', 'danger')
        finally:
            conn.close()
    else:
        flash('Внутренняя ошибка базы данных.', 'danger')
    return redirect(url_for('main_screen'))


@app.route('/add_driver', methods=['POST'])
def add_driver():
    if not session.get('is_admin_user'):
        return redirect(url_for('main_screen'))

    name = request.form.get('name', '').strip()
    phone = request.form.get('phone', '').strip()
    license_num = request.form.get('license', '').strip()
    rating = request.form.get('rating', '5.00').strip()

    if not (name and phone and license_num and rating):
        flash('Заполните анкету водителя полностью.', 'warning')
        return redirect(url_for('main_screen'))

    conn = get_db_connection()
    if conn:
        try:
            with conn.cursor() as cursor:
                sql = "INSERT INTO Driver (name, phone, license_number, rating, status) VALUES (%s, %s, %s, %s, 'Свободен')"
                cursor.execute(sql, (name, phone, license_num, float(rating)))
            conn.commit()
            flash(f"Водитель {name} добавлен в штат сотрудников.", 'success')
        except pymysql.err.IntegrityError:
            flash('Водитель с указанным телефоном или лицензией уже числится в штате.', 'danger')
        except ValueError:
            flash('Рейтинг должен быть корректным числом (например, 4.85).', 'danger')
        finally:
            conn.close()
    return redirect(url_for('main_screen'))


@app.route('/add_passenger', methods=['POST'])
def add_passenger():
    if not session.get('is_admin_user'):
        return redirect(url_for('main_screen'))

    name = request.form.get('name', '').strip()
    phone = request.form.get('phone', '').strip()
    email = request.form.get('email', '').strip() or None
    is_admin = 1 if request.form.get('is_admin') else 0

    if not (name and phone):
        flash("Укажите обязательные данные: имя и номер телефона.", 'warning')
        return redirect(url_for('main_screen'))

    conn = get_db_connection()
    if conn:
        try:
            with conn.cursor() as cursor:
                sql = "INSERT INTO Passenger (name, phone, email, is_admin) VALUES (%s, %s, %s, %s)"
                cursor.execute(sql, (name, phone, email, is_admin))
            conn.commit()
            flash(f"Учетная запись '{name}' успешно сгенерирована.", 'success')
        except pymysql.err.IntegrityError:
            flash('Данный телефонный номер уже привязан к другому аккаунту.', 'danger')
        finally:
            conn.close()
    return redirect(url_for('main_screen'))


@app.route('/delete_car/<int:car_id>', methods=['POST'])
def delete_car(car_id):
    if not session.get('is_admin_user'):
        flash('Недостаточно прав для удаления.', 'danger')
        return redirect(url_for('main_screen'))

    conn = get_db_connection()
    if conn:
        try:
            with conn.cursor() as cursor:
                cursor.execute("DELETE FROM Car WHERE car_id = %s", (car_id,))
            conn.commit()
            flash('Автомобиль успешно списан и удален из базы.', 'success')
        finally:
            conn.close()
    return redirect(url_for('main_screen'))


ensure_schema()

if __name__ == '__main__':
    app.run(debug=True)
