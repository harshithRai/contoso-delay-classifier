-- Count must be exactly 10,000.
SELECT COUNT(*) AS row_count FROM dbo.OrderHistory;

-- Carrier association is descriptive, not proof that a carrier causes delays.
SELECT carrier, COUNT(*) AS orders, SUM(CAST(delayed AS INT)) AS delayed_orders,
       ROUND(100.0 * AVG(CAST(delayed AS FLOAT)), 2) AS delay_rate_percent
FROM ml.DelayTraining GROUP BY carrier ORDER BY delay_rate_percent DESC;

SELECT is_sale_day, COUNT(*) AS orders, SUM(CAST(delayed AS INT)) AS delayed_orders,
       ROUND(100.0 * AVG(CAST(delayed AS FLOAT)), 2) AS delay_rate_percent
FROM ml.DelayTraining GROUP BY is_sale_day ORDER BY is_sale_day;

SELECT CASE WHEN warehouse_backlog < 30 THEN 'under 30'
            WHEN warehouse_backlog < 50 THEN '30 to 49' ELSE '50+' END AS backlog_bucket,
       COUNT(*) AS orders, SUM(CAST(delayed AS INT)) AS delayed_orders,
       ROUND(100.0 * AVG(CAST(delayed AS FLOAT)), 2) AS delay_rate_percent
FROM ml.DelayTraining
GROUP BY CASE WHEN warehouse_backlog < 30 THEN 'under 30'
              WHEN warehouse_backlog < 50 THEN '30 to 49' ELSE '50+' END
ORDER BY delay_rate_percent DESC;
