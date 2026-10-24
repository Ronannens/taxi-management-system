import os
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

def get_db_connection():
    try:
        return pymysql.connect(**DB_CONFIG)
    except Exception as e:
        print(f"Ошибка подключения к БД: {e}")
        return None

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
                        # Задаем базовый приятный индиго-цвет по умолчанию
                        session['theme_color'] = '#6366f1' 
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
    return render_template('main.html', 
                           user=session['current_user'], 
                           is_admin=session['is_admin_user'],
                           theme_color=session.get('theme_color', '#6366f1'))

# API для сохранения кастомного цвета UI «на лету»
@app.route('/api/save_theme', methods=['POST'])
def save_theme():
    if 'current_user' in session:
        data = request.get_json()
        if data and 'color' in data:
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
                    
                cursor.execute(query, params)
                cars = cursor.fetchall()
        finally:
            conn.close()
    return jsonify(cars)

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
    
    if not (brand and model and plate and color and driver):
        flash('Заполните абсолютно все поля спецификации автомобиля.', 'warning')
        return redirect(url_for('main_screen'))
        
    conn = get_db_connection()
    if conn:
        try:
            with conn.cursor() as cursor:
                cursor.execute("SELECT driver_id FROM Driver WHERE driver_id = %s", (driver,))
                if not cursor.fetchone():
                    flash(f"Водитель с ID {driver} отсутствует в реестре!", 'danger')
                    return redirect(url_for('main_screen'))

                sql = "INSERT INTO Car (brand, model, license_plate, color, driver_id) VALUES (%s, %s, %s, %s, %s)"
                cursor.execute(sql, (brand, model, plate, color, int(driver)))
            conn.commit()
            flash('Транспортное средство успешно интегрировано в автопарк.', 'success')
        except pymysql.err.IntegrityError:
            flash('Конфликт данных: Этот гос. номер или ID водителя уже зарегистрированы!', 'danger')
        finally:
            conn.close()
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

if __name__ == '__main__':
    app.run(debug=True)
