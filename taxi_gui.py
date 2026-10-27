import tkinter as tk
from tkinter import ttk, messagebox, colorchooser
import pymysql


DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': '12345',  # Ваш актуальный пароль
    'database': 'taxi_service',
    'charset': 'utf8mb4',
    'cursorclass': pymysql.cursors.DictCursor
}

class DatabaseManager:
    """Класс инкапсулирует все запросы к базе данных."""
    @staticmethod
    def connect():
        try:
            return pymysql.connect(**DB_CONFIG)
        except Exception as e:
            messagebox.showerror("Ошибка БД", f"Не удалось подключиться к MySQL:\n{e}")
            return None

    @classmethod
    def authenticate_user(cls, username):
        conn = cls.connect()
        if not conn:
            return None
        try:
            with conn.cursor() as cursor:
                cursor.execute("SELECT name, is_admin FROM Passenger WHERE name = %s LIMIT 1", (username,))
                return cursor.fetchone()
        finally:
            conn.close()

    @classmethod
    def get_cars(cls, search_text="", filter_color=""):
        conn = cls.connect()
        if not conn:
            return []
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
                return cursor.fetchall()
        finally:
            conn.close()

    @classmethod
    def check_driver_exists(cls, driver_id):
        conn = cls.connect()
        if not conn:
            return False
        try:
            with conn.cursor() as cursor:
                cursor.execute("SELECT driver_id FROM Driver WHERE driver_id = %s", (driver_id,))
                return bool(cursor.fetchone())
        finally:
            conn.close()

    @classmethod
    def insert_car(cls, brand, model, plate, color, driver_id):
        conn = cls.connect()
        if not conn:
            return False
        try:
            with conn.cursor() as cursor:
                sql = "INSERT INTO Car (brand, model, license_plate, color, driver_id) VALUES (%s, %s, %s, %s, %s)"
                cursor.execute(sql, (brand, model, plate, color, int(driver_id)))
            conn.commit()
            return True
        finally:
            conn.close()

    @classmethod
    def insert_driver(cls, name, phone, license_num, rating):
        conn = cls.connect()
        if not conn:
            return False
        try:
            with conn.cursor() as cursor:
                sql = "INSERT INTO Driver (name, phone, license_number, rating, status) VALUES (%s, %s, %s, %s, 'Свободен')"
                cursor.execute(sql, (name, phone, license_num, float(rating)))
            conn.commit()
            return True
        finally:
            conn.close()

    @classmethod
    def insert_passenger(cls, name, phone, email, is_admin):
        conn = cls.connect()
        if not conn:
            return False
        try:
            with conn.cursor() as cursor:
                sql = "INSERT INTO Passenger (name, phone, email, is_admin) VALUES (%s, %s, %s, %s)"
                cursor.execute(sql, (name, phone, email, is_admin))
            conn.commit()
            return True
        finally:
            conn.close()

    @classmethod
    def delete_car(cls, car_id):
        conn = cls.connect()
        if not conn:
            return False
        try:
            with conn.cursor() as cursor:
                cursor.execute("DELETE FROM Car WHERE car_id = %s", (car_id,))
            conn.commit()
            return True
        finally:
            conn.close()


class LoginScreen(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg=controller.bg_color)
        self.controller = controller
        
        frame = tk.Frame(self, bg=controller.bg_color)
        frame.place(relx=0.5, rely=0.5, anchor="center")
        
        tk.Label(frame, text="Вход в систему такси", font=("Arial", 16, "bold"), bg=controller.bg_color).pack(pady=10)
        tk.Label(frame, text="Имя пользователя (Из таблицы Passenger):", bg=controller.bg_color).pack(anchor="w")
        
        self.login_entry = tk.Entry(frame, font=("Arial", 12), width=30)
        self.login_entry.pack(pady=5)
        self.login_entry.insert(0, "Иван")
        
        login_btn = tk.Button(frame, text="Войти", font=("Arial", 11, "bold"), bg=controller.accent_color, fg="white", 
                              command=self.validate_login, width=15)
        login_btn.pack(pady=15)
        
        tk.Label(frame, text="*Доступ разрешен только зарегистрированным в БД пользователям.\nДля роли Администратора войдите под именем 'Администратор'.", 
                 font=("Arial", 8, "italic"), bg=controller.bg_color, fg="gray").pack()

    def validate_login(self):
        username = self.login_entry.get().strip()
        if not username:
            messagebox.showwarning("Внимание", "Введите имя!")
            return
            
        user = DatabaseManager.authenticate_user(username)
        if user:
            self.controller.current_user = user['name']
            self.controller.is_admin_user = bool(user['is_admin'])
            
            role_text = "Администратор" if self.controller.is_admin_user else "Пользователь"
            messagebox.showinfo("Успех", f"Добро пожаловать, {user['name']}!\nВаша роль: {role_text}")
            self.controller.show_main_screen()
        else:
            messagebox.showerror("Ошибка доступа", f"Пользователь '{username}' не найден в базе данных.\nДоступ отклонен.")


class MainScreen(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg=controller.bg_color)
        self.controller = controller
        
        # Верхняя панель управления
        top_bar = tk.Frame(self, bg=controller.accent_color, height=50)
        top_bar.pack(fill="x", side="top")
        
        role_label = " (Администратор)" if controller.is_admin_user else " (Пользователь)"
        tk.Label(top_bar, text=f"Пользователь: {controller.current_user}{role_label}", fg="white", bg=controller.accent_color, font=("Arial", 11, "bold")).pack(side="left", padx=15, pady=12)
        
        style_btn = tk.Button(top_bar, text="🎨 Изменить цвет интерфейса", bg="white", command=controller.change_style)
        style_btn.pack(side="right", padx=15, pady=10)
        
        # Рабочая зона
        main_frame = tk.Frame(self, bg=controller.bg_color)
        main_frame.pack(fill="both", expand=True, padx=15, pady=15)
        
        # Левая панель со скроллбаром
        canvas = tk.Canvas(main_frame, bg=controller.bg_color, width=320, highlightthickness=0)
        scrollbar = ttk.Scrollbar(main_frame, orient="vertical", command=canvas.yview)
        left_panel = tk.Frame(canvas, bg=controller.bg_color)
        
        left_panel.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=left_panel, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="y", padx=(0, 5))
        scrollbar.pack(side="left", fill="y", padx=(0, 10))
        
        # Блок: Поиск и Фильтрация
        tk.Label(left_panel, text="Поиск и Фильтрация машин", font=("Arial", 11, "bold"), bg=controller.bg_color).pack(anchor="w", pady=(0,5))
        tk.Label(left_panel, text="Поиск по марке/модели:", bg=controller.bg_color).pack(anchor="w")
        
        self.search_entry = tk.Entry(left_panel, font=("Arial", 10), width=35)
        self.search_entry.pack(fill="x", pady=2)
        self.search_entry.bind("<KeyRelease>", lambda event: self.load_data())
        
        tk.Label(left_panel, text="Фильтр по цвету авто:", bg=controller.bg_color).pack(anchor="w", pady=(5,0))
        self.filter_color_entry = tk.Entry(left_panel, font=("Arial", 10), width=35)
        self.filter_color_entry.pack(fill="x", pady=2)
        self.filter_color_entry.bind("<KeyRelease>", lambda event: self.load_data())

        # Отрисовка админ-панелей или инфо-панели пассажира
        if controller.is_admin_user:
            self._build_admin_forms(left_panel)
        else:
            self._build_passenger_info(left_panel)

        # Правая панель: Таблица автомобилей
        right_panel = tk.Frame(main_frame, bg=controller.bg_color)
        right_panel.pack(side="right", fill="both", expand=True)
        
        tk.Label(right_panel, text="Доступный автопарк (Товары / Услуги)", font=("Arial", 12, "bold"), bg=controller.bg_color).pack(anchor="w", pady=(0,5))
        
        columns = ("car_id", "brand", "model", "license_plate", "color", "driver_id")
        self.tree = ttk.Treeview(right_panel, columns=columns, show="headings")
        
        headings = {"car_id": "ID", "brand": "Марка", "model": "Модель", "license_plate": "Гос. номер", "color": "Цвет", "driver_id": "ID Водителя"}
        for col, text in headings.items():
            self.tree.heading(col, text=text)
            
        self.tree.column("car_id", width=40, anchor="center")
        self.tree.column("brand", width=120)
        self.tree.column("model", width=120)
        self.tree.column("license_plate", width=100, anchor="center")
        self.tree.column("color", width=100)
        self.tree.column("driver_id", width=80, anchor="center")
        
        self.tree.pack(fill="both", expand=True, side="top")
        
        if controller.is_admin_user:
            delete_btn = tk.Button(right_panel, text="🗑️  Удалить выбранный автомобиль", bg="#e74c3c", fg="white", font=("Arial", 10, "bold"), command=self.delete_car)
            delete_btn.pack(anchor="e", pady=10)
        
        self.load_data()

    def _build_admin_forms(self, parent):
        # Блок 1: Добавить автомобиль
        tk.Label(parent, text="Добавить новый автомобиль", font=("Arial", 11, "bold"), bg=self.controller.bg_color).pack(anchor="w", pady=(20,5))
        self.add_brand = self._create_entry(parent, "Марка:")
        self.add_model = self._create_entry(parent, "Модель:")
        self.add_plate = self._create_entry(parent, "Гос. номер:")
        self.add_color = self._create_entry(parent, "Цвет:")
        self.add_driver_id = self._create_entry(parent, "ID Водителя (цифра):")
        
        tk.Button(parent, text="➕ Добавить автомобиль", bg="#2ecc71", fg="white", font=("Arial", 10, "bold"), command=self.add_car).pack(fill="x", pady=8)

        # Блок 2: Добавить водителя
        tk.Label(parent, text="Добавить нового водителя", font=("Arial", 11, "bold"), bg=self.controller.bg_color).pack(anchor="w", pady=(20,5))
        self.add_dr_name = self._create_entry(parent, "ФИО Водителя:")
        self.add_dr_phone = self._create_entry(parent, "Телефон (+7...):")
        self.add_dr_license = self._create_entry(parent, "Номер лицензии:")
        self.add_dr_rating = self._create_entry(parent, "Рейтинг (например, 4.9):", default="5.00")
        
        tk.Button(parent, text="🚖 Добавить водителя", bg="#3498db", fg="white", font=("Arial", 10, "bold"), command=self.add_driver).pack(fill="x", pady=8)

        # Блок 3: Добавить пользователя
        tk.Label(parent, text="Добавить пользователя / админа", font=("Arial", 11, "bold"), bg=self.controller.bg_color).pack(anchor="w", pady=(20,5))
        self.add_ps_name = self._create_entry(parent, "Имя / Логин:")
        self.add_ps_phone = self._create_entry(parent, "Телефон:")
        self.add_ps_email = self._create_entry(parent, "Email:")
        
        self.add_ps_is_admin = tk.IntVar(value=0)
        tk.Checkbutton(parent, text="Назначить Администратором", variable=self.add_ps_is_admin, bg=self.controller.bg_color, activebackground=self.controller.bg_color).pack(anchor="w", pady=5)
        
        tk.Button(parent, text="👤 Добавить пользователя", bg="#9b59b6", fg="white", font=("Arial", 10, "bold"), command=self.add_passenger).pack(fill="x", pady=(5, 20))

    def _build_passenger_info(self, parent):
        info_frame = tk.Frame(parent, bg="#e8f4fd", bd=1, relief="solid")
        info_frame.pack(fill="x", pady=30, padx=5)
        tk.Label(info_frame, text="🔒 Режим Пассажира\n\nВам доступен только\nпросмотр и поиск авто.\nРедактирование ограничено.", 
                 font=("Arial", 10, "italic"), bg="#e8f4fd", fg="#2980b9").pack(pady=15)

    def _create_entry(self, parent, label_text, default=None):
        tk.Label(parent, text=label_text, bg=self.controller.bg_color).pack(anchor="w")
        entry = tk.Entry(parent, width=35)
        entry.pack(fill="x", pady=2)
        if default:
            entry.insert(0, default)
        return entry

    def load_data(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
            
        search_text = self.search_entry.get().strip()
        filter_color = self.filter_color_entry.get().strip()
        
        cars = DatabaseManager.get_cars(search_text, filter_color)
        if cars:
            for car in cars:
                self.tree.insert("", "end", values=(
                    car['car_id'], car['brand'], car['model'],
                    car['license_plate'], car['color'], car['driver_id']
                ))

    def add_car(self):
        brand = self.add_brand.get().strip()
        model = self.add_model.get().strip()
        plate = self.add_plate.get().strip()
        color = self.add_color.get().strip()
        driver = self.add_driver_id.get().strip()
        
        if not (brand and model and plate and color and driver):
            messagebox.showwarning("Внимание", "Заполните все поля для добавления авто!")
            return
            
        if not DatabaseManager.check_driver_exists(driver):
            messagebox.showerror("Ошибка", f"Водитель с ID {driver} не найден!")
            return
            
        try:
            if DatabaseManager.insert_car(brand, model, plate, color, driver):
                messagebox.showinfo("Успех", "Автомобиль успешно внесен в базу данных!")
                for entry in (self.add_brand, self.add_model, self.add_plate, self.add_color, self.add_driver_id):
                    entry.delete(0, tk.END)
                self.load_data()
        except pymysql.err.IntegrityError:
            messagebox.showerror("Ошибка", "Этот гос. номер или ID водителя уже заняты!")

    def add_driver(self):
        name = self.add_dr_name.get().strip()
        phone = self.add_dr_phone.get().strip()
        license_num = self.add_dr_license.get().strip()
        rating = self.add_dr_rating.get().strip()
        
        if not (name and phone and license_num and rating):
            messagebox.showwarning("Внимание", "Заполните все поля для добавления водителя!")
            return
            
        try:
            if DatabaseManager.insert_driver(name, phone, license_num, rating):
                messagebox.showinfo("Успех", "Новый водитель успешно добавлен в БД!")
                for entry in (self.add_dr_name, self.add_dr_phone, self.add_dr_license):
                    entry.delete(0, tk.END)
        except pymysql.err.IntegrityError:
            messagebox.showerror("Ошибка", "Водитель с таким телефоном или номером лицензии уже существует!")
        except ValueError:
            messagebox.showerror("Ошибка", "Неверный формат рейтинга (должно быть число)!")

    def add_passenger(self):
        name = self.add_ps_name.get().strip()
        phone = self.add_ps_phone.get().strip()
        email = self.add_ps_email.get().strip() or None
        is_admin = self.add_ps_is_admin.get()
        
        if not (name and phone):
            messagebox.showwarning("Внимание", "Поля 'Имя' и 'Телефон' обязательны для заполнения!")
            return
            
        try:
            if DatabaseManager.insert_passenger(name, phone, email, is_admin):
                messagebox.showinfo("Успех", f"Пользователь '{name}' успешно внесен в базу!")
                for entry in (self.add_ps_name, self.add_ps_phone, self.add_ps_email):
                    entry.delete(0, tk.END)
                self.add_ps_is_admin.set(0)
        except pymysql.err.IntegrityError:
            messagebox.showerror("Ошибка", "Пользователь с таким номером телефона уже существует!")

    def delete_car(self):
        selected_item = self.tree.selection()
        if not selected_item:
            messagebox.showwarning("Внимание", "Пожалуйста, выберите строчку в таблице!")
            return
            
        values = self.tree.item(selected_item)['values']
        if not values:
            return
            
        car_id = values[0]
        if messagebox.askyesno("Подтверждение", f"Вы уверены, что хотите удалить автомобиль с ID {car_id}?"):
            if DatabaseManager.delete_car(car_id):
                messagebox.showinfo("Успех", "Запись удалена!")
                self.load_data()


class TaxiApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Система Управления Такси")
        self.geometry("1100x700")
        
        # Стилизация
        self.bg_color = "#f0f2f5"
        self.accent_color = "#4a90e2"
        self.configure(bg=self.bg_color)
        
        # Данные сессии
        self.current_user = None
        self.is_admin_user = False
        
        # Посадочный контейнер для экранов
        self.container = tk.Frame(self, bg=self.bg_color)
        self.container.pack(fill="both", expand=True)
        
        self.show_login_screen()

    def clear_screen(self):
        for widget in self.container.winfo_children():
            widget.destroy()

    def show_login_screen(self):
        self.clear_screen()
        login_frame = LoginScreen(self.container, self)
        login_frame.pack(fill="both", expand=True)

    def show_main_screen(self):
        self.clear_screen()
        main_frame = MainScreen(self.container, self)
        main_frame.pack(fill="both", expand=True)

    def change_style(self):
        chosen_color = colorchooser.askcolor(title="Выберите основной цвет для кнопок и меню")
        if chosen_color:
            self.accent_color = chosen_color[1]
            self.show_main_screen()

if __name__ == "__main__":
    app = TaxiApp()
    app.mainloop()
