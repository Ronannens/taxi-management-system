USE taxi_service;

SET @tariff_exists = (
    SELECT COUNT(*)
    FROM information_schema.COLUMNS
    WHERE TABLE_SCHEMA = 'taxi_service'
      AND LOWER(TABLE_NAME) = 'car'
      AND COLUMN_NAME = 'tariff'
);

SET @tariff_sql = IF(
    @tariff_exists = 0,
    "ALTER TABLE Car ADD COLUMN tariff DECIMAL(10, 2) NOT NULL DEFAULT 0.00 COMMENT 'Тариф (цена поездки)'",
    "SELECT 'Колонка tariff уже существует' AS info"
);

PREPARE tariff_stmt FROM @tariff_sql;
EXECUTE tariff_stmt;
DEALLOCATE PREPARE tariff_stmt;
