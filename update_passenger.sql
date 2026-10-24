-- Обновление структуры таблицы Passenger для добавления роли администратора
USE taxi_service;

ALTER TABLE Passenger 
ADD COLUMN is_admin TINYINT(1) NOT NULL DEFAULT 0 COMMENT 'Флаг администратора (0 - пользователь, 1 - админ)';

-- Сделаем Ивана администратором для тестов
INSERT INTO Passenger (name, phone, email, rating, is_admin) 
VALUES ('Администратор', '+79990000001', 'admin@taxi.ru', 5.00, 1)
ON DUPLICATE KEY UPDATE is_admin = 1;

-- Сделаем Егора обычным пользователем
UPDATE Passenger SET is_admin = 0 WHERE name = 'Егор Цинник';
