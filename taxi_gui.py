import tkinter as tk
from tkinter import ttk, messagebox, colorchooser
import pymysql

# НАСТРОЙКИ ПОДКЛЮЧЕНИЯ К ВАШЕЙ БАЗЕ ДАННЫХ
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': '12345',  # Ваш актуальный пароль
    'database': 'taxi_service',
    'charset': 'utf8mb4',
    'cursorclass': pymysql.cursors.DictCursor
}

class TaxiApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Система Управления Такси")
        self.geometry("1100x700")  # Немного увеличили окно для размещения новых форм
        
        # Начальная цветовая палитра
        self.bg_color = "#f0f2f5"
        self.accent_color = "#4a90e2"
        self.configure(bg=self.bg_color)
        
        self.current_user = None
        self.is_admin_user = False  # Переменная для хранения роли текущего пользователя
        
        self.show_login_screen()

    def db_connect(self):
        try:
            return pymysql.connect(**DB_CONFIG)
        except Exception as e:
            messagebox.showerror("Ошибка БД", f"Не удалось подключиться к MySQL:\n{e}")
            return None

    # ==========================================
    # 1) ФУНКЦИЯ: АВТОРИЗАЦИЯ
    # ==========================================
    def show_login_screen(self):
        self.clear_screen()
        
        frame = tk.Frame(self, bg=self.bg_color)
        frame.place(relx=0.5, rely=0.5, anchor="center")
        
        tk.Label(frame, text="Вход в систему такси", font=("Arial", 16, "bold"), bg=self.bg_color).pack(pady=10)
        
        tk.Label(frame, text="Имя пользователя (Из таблицы Passenger):", bg=self.bg_color).pack(anchor="w")
        self.login_entry = tk.Entry(frame, font=("Arial", 12), width=30)
        self.login_entry.pack(pady=5)
        self.login_entry.insert(0, "Иван")  # Дефолтное имя для теста
        
        login_btn = tk.Button(frame, text="Войти", font=("Arial", 11, "bold"), bg=self.accent_color, fg="white", 
                              command=self.handle_login, width=15)
        login_btn.pack(pady=15)
        
        tk.Label(frame, text="*Доступ разрешен только зарегистрированным в БД пользователям.\nДля роли Администратора войдите под именем 'Администратор'.", 
                 font=("Arial", 8, "italic"), bg=self.bg_color, fg="gray").pack()

    def handle_login(self):
        username = self.login_entry.get().strip()
        if not username:
            messagebox.showwarning("Внимание", "Введите имя!")
            return
            
        conn = self.db_connect()
        if conn:
            try:
                with conn.cursor() as cursor:
                    # Запрашиваем у БД пользователя и его статус администратора
                    cursor.execute("SELECT name, is_admin FROM Passenger WHERE name = %s LIMIT 1", (username,))
                    user = cursor.fetchone()
                    
                    if user:
                        self.current_user = user['name']
                        self.is_admin_user = bool(user['is_admin'])  # 1 -> True, 0 -> False
                        
                        role_text = "Администратор" if self.is_admin_user else "Пользователь"
                        messagebox.showinfo("Успех", f"Добро пожаловать, {user['name']}!\nВаша роль: {role_text}")
                        self.show_main_screen()
                    else:
                        messagebox.showerror("Ошибка доступа", f"Пользователь '{username}' не найден в базе данных.\nДоступ отклонен.")
            finally:
                conn.close()

    # ==========================================
    # ГЛАВНЫЙ ЭКРАН И ИНТЕРФЕЙС
    # ==========================================
    def show_main_screen(self):
        self.clear_screen()
        
        # Верхняя панель управления
        top_bar = tk.Frame(self, bg=self.accent_color, height=50)
        top_bar.pack(fill="x", side="top")
        
        role_label = " (Администратор)" if self.is_admin_user else " (Пользователь)"
        tk.Label(top_bar, text=f"Пользователь: {self.current_user}{role_label}", fg="white", bg=self.accent_color, font=("Arial", 11, "bold")).pack(side="left", padx=15, pady=12)
        
        style_btn = tk.Button(top_bar, text="🎨 Изменить цвет интерфейса", bg="white", command=self.change_style)
        style_btn.pack(side="right", padx=15, pady=10)
        
        # Рабочая зона
        main_frame = tk.Frame(self, bg=self.bg_color)
        main_frame.pack(fill="both", expand=True, padx=15, pady=15)
        
        # Левая панель со скроллбаром (так как форм стало много)
        canvas = tk.Canvas(main_frame, bg=self.bg_color, width=320, highlightthickness=0)
        scrollbar = ttk.Scrollbar(main_frame, orient="vertical", command=canvas.yview)
        left_panel = tk.Frame(canvas, bg=self.bg_color)
        
        left_panel.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        canvas.create_window((0, 0), window=left_panel, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="y", padx=(0, 5))
        scrollbar.pack(side="left", fill="y", padx=(0, 10))
        
        # Блок: 4) ПОИСК И 3) ФИЛЬТРАЦИЯ
        tk.Label(left_panel, text="Поиск и Фильтрация машин", font=("Arial", 11, "bold"), bg=self.bg_color).pack(anchor="w", pady=(0,5))
        
        tk.Label(left_panel, text="Поиск по марке/модели:", bg=self.bg_color).pack(anchor="w")
        self.search_entry = tk.Entry(left_panel, font=("Arial", 10), width=35)
        self.search_entry.pack(fill="x", pady=2)
        self.search_entry.bind("<KeyRelease>", lambda event: self.load_data())
        
        tk.Label(left_panel, text="Фильтр по цвету авто:", bg=self.bg_color).pack(anchor="w", pady=(5,0))
        self.filter_color_entry = tk.Entry(left_panel, font=("Arial", 10), width=35)
        self.filter_color_entry.pack(fill="x", pady=2)
        self.filter_color_entry.bind("<KeyRelease>", lambda event: self.load_data())

        # ОГРАНИЧЕНИЕ ДОСТУПА: Блоки добавления видны только Администратору
        if self.is_admin_user:
            # --- БЛОК 1: Добавить автомобиль ---
            tk.Label(left_panel, text="Добавить новый автомобиль", font=("Arial", 11, "bold"), bg=self.bg_color).pack(anchor="w", pady=(20,5))
            
            tk.Label(left_panel, text="Марка:", bg=self.bg_color).pack(anchor="w")
            self.add_brand = tk.Entry(left_panel, width=35)
            self.add_brand.pack(fill="x", pady=2)
            
            tk.Label(left_panel, text="Модель:", bg=self.bg_color).pack(anchor="w")
            self.add_model = tk.Entry(left_panel, width=35)
            self.add_model.pack(fill="x", pady=2)
            
            tk.Label(left_panel, text="Гос. номер:", bg=self.bg_color).pack(anchor="w")
            self.add_plate = tk.Entry(left_panel, width=35)
            self.add_plate.pack(fill="x", pady=2)
            
            tk.Label(left_panel, text="Цвет:", bg=self.bg_color).pack(anchor="w")
            self.add_color = tk.Entry(left_panel, width=35)
            self.add_color.pack(fill="x", pady=2)
            
            tk.Label(left_panel, text="ID Водителя (цифра):", bg=self.bg_color).pack(anchor="w")
            self.add_driver_id = tk.Entry(left_panel, width=35)
            self.add_driver_id.pack(fill="x", pady=2)
            
            add_btn = tk.Button(left_panel, text="➕ Добавить автомобиль", bg="#2ecc71", fg="white", font=("Arial", 10, "bold"), command=self.add_car)
            add_btn.pack(fill="x", pady=8)

            # --- БЛОК 2: Добавить водителя ---
            tk.Label(left_panel, text="Добавить нового водителя", font=("Arial", 11, "bold"), bg=self.bg_color).pack(anchor="w", pady=(20,5))
            
            tk.Label(left_panel, text="ФИО Водителя:", bg=self.bg_color).pack(anchor="w")
            self.add_dr_name = tk.Entry(left_panel, width=35)
            self.add_dr_name.pack(fill="x", pady=2)
            
            tk.Label(left_panel, text="Телефон (+7...):", bg=self.bg_color).pack(anchor="w")
            self.add_dr_phone = tk.Entry(left_panel, width=35)
            self.add_dr_phone.pack(fill="x", pady=2)
            
            tk.Label(left_panel, text="Номер лицензии:", bg=self.bg_color).pack(anchor="w")
            self.add_dr_license = tk.Entry(left_panel, width=35)
            self.add_dr_license.pack(fill="x", pady=2)
            
            tk.Label(left_panel, text="Рейтинг (например, 4.9):", bg=self.bg_color).pack(anchor="w")
            self.add_dr_rating = tk.Entry(left_panel, width=35)
            self.add_dr_rating.pack(fill="x", pady=2)
            self.add_dr_rating.insert(0, "5.00")
            
            add_dr_btn = tk.Button(left_panel, text="🚖 Добавить водителя", bg="#3498db", fg="white", font=("Arial", 10, "bold"), command=self.add_driver)
            add_dr_btn.pack(fill="x", pady=8)

            # --- БЛОК 3: Добавить пользователя (пассажира) ---
            tk.Label(left_panel, text="Добавить пользователя / админа", font=("Arial", 11, "bold"), bg=self.bg_color).pack(anchor="w", pady=(20,5))
            
            tk.Label(left_panel, text="Имя / Логин:", bg=self.bg_color).pack(anchor="w")
            self.add_ps_name = tk.Entry(left_panel, width=35)
            self.add_ps_name.pack(fill="x", pady=2)
            
            tk.Label(left_panel, text="Телефон:", bg=self.bg_color).pack(anchor="w")
            self.add_ps_phone = tk.Entry(left_panel, width=35)
            self.add_ps_phone.pack(fill="x", pady=2)
            
            tk.Label(left_panel, text="Email:", bg=self.bg_color).pack(anchor="w")
            self.add_ps_email = tk.Entry(left_panel, width=35)
            self.add_ps_email.pack(fill="x", pady=2)
            
            # Флажок роли (Администратор)
            # Флажок роли (Администратор)
            self.add_ps_is_admin = tk.IntVar(value=0)
            chk_admin = tk.Checkbutton(left_panel, text="Назначить Администратором", variable=self.add_ps_is_admin, bg=self.bg_color, activebackground=self.bg_color)
            chk_admin.pack(anchor="w", pady=5)
            
            add_ps_btn = tk.Button(left_panel, text="👤 Добавить пользователя", bg="#9b59b6", fg="white", font=("Arial", 10, "bold"), command=self.add_passenger)
            add_ps_btn.pack(fill="x", pady=(5, 20))
        else:
            # Режим обычного пассажира
            info_frame = tk.Frame(left_panel, bg="#e8f4fd", bd=1, relief="solid")
            info_frame.pack(fill="x", pady=30, padx=5)
            tk.Label(info_frame, text="🔒 Режим Пассажира\n\nВам доступен только\nпросмотр и поиск авто.\nРедактирование ограничено.", 
                     font=("Arial", 10, "italic"), bg="#e8f4fd", fg="#2980b9").pack(pady=15)

        # Правая панель: Таблица автомобилей
        right_panel = tk.Frame(main_frame, bg=self.bg_color)
        right_panel.pack(side="right", fill="both", expand=True)
        
        tk.Label(right_panel, text="Доступный автопарк (Товары / Услуги)", font=("Arial", 12, "bold"), bg=self.bg_color).pack(anchor="w", pady=(0,5))
        
        columns = ("car_id", "brand", "model", "license_plate", "color", "driver_id")
        self.tree = ttk.Treeview(right_panel, columns=columns, show="headings")
        
        self.tree.heading("car_id", text="ID")
        self.tree.heading("brand", text="Марка")
        self.tree.heading("model", text="Модель")
        self.tree.heading("license_plate", text="Гос. номер")
        self.tree.heading("color", text="Цвет")
        self.tree.heading("driver_id", text="ID Водителя")
        
        self.tree.column("car_id", width=40, anchor="center")
        self.tree.column("brand", width=120)
        self.tree.column("model", width=120)
        self.tree.column("license_plate", width=100, anchor="center")
        self.tree.column("color", width=100)
        self.tree.column("driver_id", width=80, anchor="center")
        
        self.tree.pack(fill="both", expand=True, side="top")
        
        if self.is_admin_user:
            delete_btn = tk.Button(right_panel, text="🗑️  Удалить выбранный автомобиль", bg="#e74c3c", fg="white", font=("Arial", 10, "bold"), command=self.delete_car)
            delete_btn.pack(anchor="e", pady=10)
        
        self.load_data()

    # ==========================================
    # 2, 3, 4) ФУНКЦИИ: ПРОСМОТР, ПОИСК И ФИЛЬТРАЦИЯ
    # ==========================================
    def load_data(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
            
        search_text = self.search_entry.get().strip()
        filter_color = self.filter_color_entry.get().strip()
        
        conn = self.db_connect()
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
                    
                    for car in cars:
                        self.tree.insert("", "end", values=(
                            car['car_id'], car['brand'], car['model'],
                            car['license_plate'], car['color'], car['driver_id']
                        ))
            finally:
                conn.close()

    # ==========================================
    # 5) ФУНКЦИИ: ДОБАВЛЕНИЕ И УДАЛЕНИЕ (ADMIN ONLY)
    # ==========================================
    def add_car(self):
        if not self.is_admin_user:
            messagebox.showerror("Ошибка доступа", "Действие запрещено для обычных пользователей!")
            return

        brand = self.add_brand.get().strip()
        model = self.add_model.get().strip()
        plate = self.add_plate.get().strip()
        color = self.add_color.get().strip()
        driver = self.add_driver_id.get().strip()
        
        if not (brand and model and plate and color and driver):
            messagebox.showwarning("Внимание", "Заполните все поля для добавления авто!")
            return
            
        conn = self.db_connect()
        if conn:
            try:
                with conn.cursor() as cursor:
                    cursor.execute("SELECT driver_id FROM Driver WHERE driver_id = %s", (driver,))
                    if not cursor.fetchone():
                        messagebox.showerror("Ошибка", f"Водитель с ID {driver} не найден!")
                        return

                    sql = "INSERT INTO Car (brand, model, license_plate, color, driver_id) VALUES (%s, %s, %s, %s, %s)"
                    cursor.execute(sql, (brand, model, plate, color, int(driver)))
                conn.commit()
                messagebox.showinfo("Успех", "Автомобиль успешно внесен в базу данных!")
                
                for entry in (self.add_brand, self.add_model, self.add_plate, self.add_color, self.add_driver_id):
                    entry.delete(0, tk.END)
                
                self.load_data()
            except pymysql.err.IntegrityError:
                messagebox.showerror("Ошибка", "Этот гос. номер или ID водителя уже заняты!")
            finally:
                conn.close()

    def add_driver(self):
        if not self.is_admin_user:
            return
            
        name = self.add_dr_name.get().strip()
        phone = self.add_dr_phone.get().strip()
        license_num = self.add_dr_license.get().strip()
        rating = self.add_dr_rating.get().strip()
        
        if not (name and phone and license_num and rating):
            messagebox.showwarning("Внимание", "Заполните все поля для добавления водителя!")
            return
            
        conn = self.db_connect()
        if conn:
            try:
                with conn.cursor() as cursor:
                    sql = "INSERT INTO Driver (name, phone, license_number, rating, status) VALUES (%s, %s, %s, %s, 'Свободен')"
                    cursor.execute(sql, (name, phone, license_num, float(rating)))
                conn.commit()
                messagebox.showinfo("Успех", "Новый водитель успешно добавлен в БД!")
                
                for entry in (self.add_dr_name, self.add_dr_phone, self.add_dr_license):
                    entry.delete(0, tk.END)
            except pymysql.err.IntegrityError:
                messagebox.showerror("Ошибка", "Водитель с таким телефоном или номером лицензии уже существует!")
            except ValueError:
                messagebox.showerror("Ошибка", "Неверный формат рейтинга (должно быть число)!")
            finally:
                conn.close()

    def add_passenger(self):
        if not self.is_admin_user:
            return
            
        name = self.add_ps_name.get().strip()
        phone = self.add_ps_phone.get().strip()
        email = self.add_ps_email.get().strip() or None
        is_admin = self.add_ps_is_admin.get()  # Получаем 1 (админ) или 0 (пассажир)
        
        if not (name and phone):
            messagebox.showwarning("Внимание", "Поля 'Имя' и 'Телефон' обязательны для заполнения!")
            return
            
        conn = self.db_connect()
        if conn:
            try:
                with conn.cursor() as cursor:
                    sql = "INSERT INTO Passenger (name, phone, email, is_admin) VALUES (%s, %s, %s, %s)"
                    cursor.execute(sql, (name, phone, email, is_admin))
                conn.commit()
                messagebox.showinfo("Успех", f"Пользователь '{name}' успешно внесен в базу!")
                
                for entry in (self.add_ps_name, self.add_ps_phone, self.add_ps_email):
                    entry.delete(0, tk.END)
                self.add_ps_is_admin.set(0)
            except pymysql.err.IntegrityError:
                messagebox.showerror("Ошибка", "Пользователь с таким номером телефона уже существует!")
            finally:
                conn.close()

    def delete_car(self):
        if not self.is_admin_user:
            messagebox.showerror("Ошибка доступа", "Действие запрещено для обычных пользователей!")
            return

        selected_item = self.tree.selection()
        if not selected_item:
            messagebox.showwarning("Внимание", "Пожалуйста, выберите строчку в таблице!")
            return
            
        values = self.tree.item(selected_item)['values']
        if not values:
            return
            
        car_id = values[0]
        if messagebox.askyesno("Подтверждение", f"Вы уверены, что хотите удалить автомобиль с ID {car_id}?"):
            conn = self.db_connect()
            if conn:
                try:
                    with conn.cursor() as cursor:
                        cursor.execute("DELETE FROM Car WHERE car_id = %s", (car_id,))
                    conn.commit()
                    messagebox.showinfo("Успех", "Запись удалена!")
                    self.load_data()
                finally:
                    conn.close()

    # ==========================================
    # 6) ФУНКЦИЯ: ЗАДАТЬ СТИЛЬ / ЦВЕТ
    # ==========================================
    def change_style(self):
        chosen_color = colorchooser.askcolor(title="Выберите основной цвет для кнопок и меню")
        if chosen_color:
            self.accent_color = chosen_color[1]
            self.show_main_screen()

    def clear_screen(self):
        for widget in self.winfo_children():
            widget.destroy()

if __name__ == "__main__":
    app = TaxiApp()
    app.mainloop()