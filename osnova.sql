
DROP DATABASE IF EXISTS taxi_service;


CREATE DATABASE taxi_service CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE taxi_service;

CREATE TABLE Passenger (
    passenger_id INT AUTO_INCREMENT,
    name VARCHAR(100) NOT NULL,
    phone VARCHAR(20) NOT NULL UNIQUE,
    email VARCHAR(100),
    rating DECIMAL(3, 2) DEFAULT 5.00,
    PRIMARY KEY (passenger_id)
) ENGINE=InnoDB;


CREATE TABLE Driver (
    driver_id INT AUTO_INCREMENT,
    name VARCHAR(100) NOT NULL,
    phone VARCHAR(20) NOT NULL UNIQUE,
    license_number VARCHAR(50) NOT NULL UNIQUE,
    rating DECIMAL(3, 2) DEFAULT 5.00,
    status VARCHAR(50) NOT NULL DEFAULT 'Свободен',
    PRIMARY KEY (driver_id)
) ENGINE=InnoDB;


CREATE TABLE Car (
    car_id INT AUTO_INCREMENT,
    brand VARCHAR(50) NOT NULL,
    model VARCHAR(50) NOT NULL,
    license_plate VARCHAR(20) NOT NULL UNIQUE,
    color VARCHAR(30) NOT NULL,
    driver_id INT UNIQUE NOT NULL,
    PRIMARY KEY (car_id),
    CONSTRAINT fk_car_driver FOREIGN KEY (driver_id)
        REFERENCES Driver(driver_id)
        ON DELETE CASCADE
        ON UPDATE CASCADE
) ENGINE=InnoDB;


CREATE TABLE Ride (
    ride_id INT AUTO_INCREMENT,
    passenger_id INT NOT NULL,
    driver_id INT NOT NULL,
    pickup_location VARCHAR(255) NOT NULL,
    dropoff_location VARCHAR(255) NOT NULL,
    start_time DATETIME NOT NULL,
    cost DECIMAL(10, 2) NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'Создана',
    PRIMARY KEY (ride_id),
    CONSTRAINT fk_ride_passenger FOREIGN KEY (passenger_id)
        REFERENCES Passenger(passenger_id)
        ON DELETE RESTRICT
        ON UPDATE CASCADE,
    CONSTRAINT fk_ride_driver FOREIGN KEY (driver_id)
        REFERENCES Driver(driver_id)
        ON DELETE RESTRICT
        ON UPDATE CASCADE
) ENGINE=InnoDB;


CREATE TABLE Payment (
    payment_id INT AUTO_INCREMENT,
    ride_id INT UNIQUE NOT NULL,
    amount DECIMAL(10, 2) NOT NULL,
    payment_method VARCHAR(50) NOT NULL,
    payment_time DATETIME NOT NULL,
    PRIMARY KEY (payment_id),
    CONSTRAINT fk_payment_ride FOREIGN KEY (ride_id)
        REFERENCES Ride(ride_id)
        ON DELETE CASCADE
        ON UPDATE CASCADE
) ENGINE=InnoDB;