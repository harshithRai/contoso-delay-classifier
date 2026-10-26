IF NOT EXISTS (SELECT 1 FROM sys.schemas WHERE name = 'ml') EXEC('CREATE SCHEMA ml');
GO
CREATE OR ALTER VIEW ml.DelayTraining AS
SELECT carrier, distance_km, weight_kg, items, order_hour, is_sale_day,
       warehouse_backlog, weather_index, delayed
FROM dbo.OrderHistory;
