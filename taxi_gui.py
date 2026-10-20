import tkinter as tk
from tkinter import ttk, messagebox, colorchooser
import pymysql

# НАСТРОЙКИ ПОДКЛЮЧЕНИЯ К ВАШЕЙ БАЗЕ ДАННЫХ
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': '12345',
    'database': 'taxi_service',
    'charset': 'utf8mb4',
    'cursorclass': pymysql.cursors.DictCursor
}

class TaxiApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Система Управления Такси")
        self.geometry("950x600")
        
        # Начальная цветовая палитра (Цвет фона и элементов)
        self.bg_color = "#f0f2f5"
        self.accent_color = "#4a90e2"
        self.configure(bg=self.bg_color)
        
        self.current_user = None
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
        
        tk.Label(frame, text="Имя пользователя (Пассажир из БД):", bg=self.bg_color).pack(anchor="w")
        self.login_entry = tk.Entry(frame, font=("Arial", 12), width=30)
        self.login_entry.pack(pady=5)
        self.login_entry.insert(0, "Иван") # Дефолтное имя для удобства теста
        
        login_btn = tk.Button(frame, text="Войти", font=("Arial", 11, "bold"), bg=self.accent_color, fg="white", 
                              command=self.handle_login, width=15)
        login_btn.pack(pady=15)
        
        tk.Label(frame, text="*Для теста введите имя любого пассажира, который есть в таблице Passenger.\nЕсли таблица пуста, вход выполнится автоматически под 'Админ'.", 
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
                    # Проверяем существование такого пассажира в БД
                    cursor.execute("SELECT * FROM Passenger WHERE name = %s LIMIT 1", (username,))
                    user = cursor.fetchone()
                    if user:
                        self.current_user = user['name']
                        messagebox.showinfo("Успех", f"Добро пожаловать, пассажир {user['name']}!")
                    else:
                        # Если база пустая или совпадений нет — пускаем как админа
                        self.current_user = f"{username} (Админ)"
                        messagebox.showinfo("Успех", f"Вход выполнен в режиме администратора: {username}")
                    
                    self.show_main_screen()
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
        
        tk.Label(top_bar, text=f"Пользователь: {self.current_user}", fg="white", bg=self.accent_color, font=("Arial", 11, "bold")).pack(side="left", padx=15, pady=12)
        
        # 6) ФУНКЦИЯ: Задать стиль/цвет
        style_btn = tk.Button(top_bar, text="🎨 Изменить цвет интерфейса", bg="white", command=self.change_style)
        style_btn.pack(side="right", padx=15, pady=10)
        
        # Рабочая зона
        main_frame = tk.Frame(self, bg=self.bg_color)
        main_frame.pack(fill="both", expand=True, padx=15, pady=15)
        
        # Левая панель: Поиск, Фильтры и Добавление
        left_panel = tk.Frame(main_frame, bg=self.bg_color, width=300)
        left_panel.pack(side="left", fill="y", padx=(0, 15))
        
        # Блок: 4) ПОИСК И 3) ФИЛЬТРАЦИЯ
        tk.Label(left_panel, text="Поиск и Фильтрация машин", font=("Arial", 11, "bold"), bg=self.bg_color).pack(anchor="w", pady=(0,5))
        
        tk.Label(left_panel, text="Поиск по марке/модели:", bg=self.bg_color).pack(anchor="w")
        self.search_entry = tk.Entry(left_panel, font=("Arial", 10))
        self.search_entry.pack(fill="x", pady=2)
        self.search_entry.bind("<KeyRelease>", lambda event: self.load_data()) # Живой поиск
        
        tk.Label(left_panel, text="Фильтр по цвету авто:", bg=self.bg_color).pack(anchor="w", pady=(5,0))
        self.filter_color_entry = tk.Entry(left_panel, font=("Arial", 10))
        self.filter_color_entry.pack(fill="x", pady=2)
        self.filter_color_entry.bind("<KeyRelease>", lambda event: self.load_data())

        # Блок: 5) ДОБАВЛЕНИЕ новых данных (Быстрое добавление машины в БД)
        tk.Label(left_panel, text="Добавить новый автомобиль", font=("Arial", 11, "bold"), bg=self.bg_color).pack(anchor="w", pady=(25,5))
        
        tk.Label(left_panel, text="Марка:", bg=self.bg_color).pack(anchor="w")
        self.add_brand = tk.Entry(left_panel)
        self.add_brand.pack(fill="x", pady=2)
        
        tk.Label(left_panel, text="Модель:", bg=self.bg_color).pack(anchor="w")
        self.add_model = tk.Entry(left_panel)
        self.add_model.pack(fill="x", pady=2)
        
        tk.Label(left_panel, text="Гос. номер:", bg=self.bg_color).pack(anchor="w")
        self.add_plate = tk.Entry(left_panel)
        self.add_plate.pack(fill="x", pady=2)
        
        tk.Label(left_panel, text="Цвет:", bg=self.bg_color).pack(anchor="w")
        self.add_color = tk.Entry(left_panel)
        self.add_color.pack(fill="x", pady=2)
        
        tk.Label(left_panel, text="ID Водителя (цифра):", bg=self.bg_color).pack(anchor="w")
        self.add_driver_id = tk.Entry(left_panel)
        self.add_driver_id.pack(fill="x", pady=2)
        
        add_btn = tk.Button(left_panel, text="➕ Добавить в БД", bg="#2ecc71", fg="white", font=("Arial", 10, "bold"), command=self.add_car)
        add_btn.pack(fill="x", pady=10)

        # Правая панель: 2) ПРОСМОТР УСЛУГ/ТОВАРОВ (Таблица автомобилей)
        right_panel = tk.Frame(main_frame, bg=self.bg_color)
        right_panel.pack(side="right", fill="both", expand=True)
        
        tk.Label(right_panel, text="Доступный автопарк (Товары / Услуги)", font=("Arial", 12, "bold"), bg=self.bg_color).pack(anchor="w", pady=(0,5))
        
        # Настройка таблицы Treeview
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
        
        # Кнопка для 5) УДАЛЕНИЯ элементов
        delete_btn = tk.Button(right_panel, text="🗑️ Удалить выбранный автомобиль", bg="#e74c3c", fg="white", font=("Arial", 10, "bold"), command=self.delete_car)
        delete_btn.pack(anchor="e", pady=10)
        
        # Загрузка первичных данных из базы в таблицу
        self.load_data()

    # ==========================================
    # 2, 3, 4) ФУНКЦИИ: ПРОСМОТР, ПОИСК И ФИЛЬТРАЦИЯ
    # ==========================================
    def load_data(self):
        # Очищаем таблицу перед выводом обновленных данных
        for item in self.tree.get_children():
            self.tree.delete(item)
            
        search_text = self.search_entry.get().strip()
        filter_color = self.filter_color_entry.get().strip()
        
        conn = self.db_connect()
        if conn:
            try:
                with conn.cursor() as cursor:
                    # Динамический SQL запрос с учетом поиска и фильтрации
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
    # 5) ФУНКЦИЯ: ДОБАВЛЕНИЕ И УДАЛЕНИЕ
    # ==========================================
    def add_car(self):
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
                    # Сначала проверяем, существует ли указанный ID водителя в таблице Driver
                    cursor.execute("SELECT driver_id FROM Driver WHERE driver_id = %s", (driver,))
                    if not cursor.fetchone():
                        messagebox.showerror("Ошибка", f"Водитель с ID {driver} не найден в таблице Driver!\nСначала добавьте водителя в базу.")
                        return

                    sql = "INSERT INTO Car (brand, model, license_plate, color, driver_id) VALUES (%s, %s, %s, %s, %s)"
                    cursor.execute(sql, (brand, model, plate, color, int(driver)))
                conn.commit()
                messagebox.showinfo("Успех", "Автомобиль успешно внесен в базу данных!")
                
                # Очищаем поля ввода
                for entry in (self.add_brand, self.add_model, self.add_plate, self.add_color, self.add_driver_id):
                    entry.delete(0, tk.END)
                
                self.load_data()  # Обновляем таблицу на экране
            except pymysql.err.IntegrityError:
                messagebox.showerror("Ошибка", "Критическая ошибка: Этот гос. номер или данный ID водителя уже привязаны к другой машине (Связь 1:1)!")
            finally:
                conn.close()

    def delete_car(self):
        selected_item = self.tree.selection()
        if not selected_item:
            messagebox.showwarning("Внимание", "Пожалуйста, выберите строчку в таблице для удаления!")
            return
            
        values = self.tree.item(selected_item)['values']
        if not values:
            return
            
        car_id = values[0]
        if messagebox.askyesno("Подтверждение", f"Вы уверены, что хотите безвозвратно удалить автомобиль с ID {car_id}?"):
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
        # Открывает встроенную палитру цветов Windows/MacOS
        chosen_color = colorchooser.askcolor(title="Выберите основной цвет для кнопок и меню")[1]
        if chosen_color:
            self.accent_color = chosen_color
            # Перерисовываем экран, чтобы применить новый цвет
            self.show_main_screen()

    # Вспомогательная утилита для очистки оконного пространства
    def clear_screen(self):
        for widget in self.winfo_children():
            widget.destroy()

if __name__ == "__main__":
    app = TaxiApp()
    app.mainloop()
