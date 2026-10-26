IF OBJECT_ID('dbo.OrderHistory', 'U') IS NULL
CREATE TABLE dbo.OrderHistory (
    OrderHistoryId INT IDENTITY(1,1) PRIMARY KEY,
    carrier NVARCHAR(20) NOT NULL,
    distance_km INT NOT NULL,
    weight_kg DECIMAL(6,2) NOT NULL,
    items INT NOT NULL,
    order_hour TINYINT NOT NULL CHECK (order_hour BETWEEN 0 AND 23),
    is_sale_day BIT NOT NULL,
    warehouse_backlog INT NOT NULL,
    weather_index DECIMAL(5,3) NOT NULL,
    delayed BIT NOT NULL
);
