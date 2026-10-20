-- Создание базы данных для службы заказа такси
CREATE DATABASE IF NOT EXISTS taxi_service CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE taxi_service;

-- 1. Таблица Пассажир (Сущность: Пассажир)
CREATE TABLE Passenger (
    passenger_id INT AUTO_INCREMENT COMMENT 'ID_Пассажира',
    name VARCHAR(100) NOT NULL COMMENT 'Имя',
    phone VARCHAR(20) NOT NULL UNIQUE COMMENT 'Телефон',
    email VARCHAR(100) COMMENT 'Email',
    rating DECIMAL(3, 2) DEFAULT 5.00 COMMENT 'Рейтинг',
    PRIMARY KEY (passenger_id)
) ENGINE=InnoDB COMMENT='Пассажиры службы такси';

-- 2. Таблица Водитель (Сущность: Водитель)
CREATE TABLE Driver (
    driver_id INT AUTO_INCREMENT COMMENT 'ID_Водителя',
    name VARCHAR(100) NOT NULL COMMENT 'Имя',
    phone VARCHAR(20) NOT NULL UNIQUE COMMENT 'Телефон',
    license_number VARCHAR(50) NOT NULL UNIQUE COMMENT 'Номер_лицензии',
    rating DECIMAL(3, 2) DEFAULT 5.00 COMMENT 'Рейтинг',
    status VARCHAR(50) NOT NULL DEFAULT 'Свободен' COMMENT 'Статус',
    PRIMARY KEY (driver_id)
) ENGINE=InnoDB COMMENT='Водители такси';

-- 3. Таблица Автомобиль (Сущность: Автомобиль)
-- Связь: Водитель -> Автомобиль (1:1). ID_Водителя вынесен как внешний ключ с ограничением UNIQUE.
CREATE TABLE Car (
    car_id INT AUTO_INCREMENT COMMENT 'ID_Автомобиля',
    brand VARCHAR(50) NOT NULL COMMENT 'Марка',
    model VARCHAR(50) NOT NULL COMMENT 'Модель',
    license_plate VARCHAR(20) NOT NULL UNIQUE COMMENT 'Гос_номер',
    color VARCHAR(30) NOT NULL COMMENT 'Цвет',
    driver_id INT UNIQUE NOT NULL COMMENT 'ID_Водителя (FK)',
    PRIMARY KEY (car_id),
    CONSTRAINT fk_car_driver FOREIGN KEY (driver_id)
        REFERENCES Driver(driver_id)
        ON DELETE CASCADE
        ON UPDATE CASCADE
) ENGINE=InnoDB COMMENT='Автомобили водителей';

-- 4. Таблица Поездка (Сущность: Поездка)
-- Связи: Пассажир -> Поездка (1:N), Водитель -> Поездка (1:N)
CREATE TABLE Ride (
    ride_id INT AUTO_INCREMENT COMMENT 'ID_Поездки',
    passenger_id INT NOT NULL COMMENT 'ID_Пассажира (FK)',
    driver_id INT NOT NULL COMMENT 'ID_Водителя (FK)',
    pickup_location VARCHAR(255) NOT NULL COMMENT 'Точка_отправления',
    dropoff_location VARCHAR(255) NOT NULL COMMENT 'Точка_прибытия',
    start_time DATETIME NOT NULL COMMENT 'Время_начала',
    cost DECIMAL(10, 2) NOT NULL COMMENT 'Стоимость',
    status VARCHAR(50) NOT NULL DEFAULT 'Создана' COMMENT 'Статус',
    PRIMARY KEY (ride_id),
    CONSTRAINT fk_ride_passenger FOREIGN KEY (passenger_id)
        REFERENCES Passenger(passenger_id)
        ON DELETE RESTRICT
        ON UPDATE CASCADE,
    CONSTRAINT fk_ride_driver FOREIGN KEY (driver_id)
        REFERENCES Driver(driver_id)
        ON DELETE RESTRICT
        ON UPDATE CASCADE
) ENGINE=InnoDB COMMENT='Информация о поездках';

-- 5. Таблица Оплата (Сущность: Оплата)
-- Связь: Поездка -> Оплата (1:1). ID_Поездки вынесен как внешний ключ с ограничением UNIQUE.
CREATE TABLE Payment (
    payment_id INT AUTO_INCREMENT COMMENT 'ID_Оплаты',
    ride_id INT UNIQUE NOT NULL COMMENT 'ID_Поездки (FK)',
    amount DECIMAL(10, 2) NOT NULL COMMENT 'Сумма',
    payment_method VARCHAR(50) NOT NULL COMMENT 'Способ_оплаты',
    payment_time DATETIME NOT NULL COMMENT 'Время_оплаты',
    PRIMARY KEY (payment_id),
    CONSTRAINT fk_payment_ride FOREIGN KEY (ride_id)
        REFERENCES Ride(ride_id)
        ON DELETE CASCADE
        ON UPDATE CASCADE
) ENGINE=InnoDB COMMENT='Информация об оплате поездок';
