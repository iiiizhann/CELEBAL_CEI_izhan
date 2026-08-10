-- Q3: Month-wise Order Count for the Last 12 Months

SELECT
    strftime('%Y-%m', order_date) AS month,
    COUNT(*) AS order_count
FROM orders
WHERE order_date >= date('now', '-12 months')
GROUP BY month
ORDER BY month;
