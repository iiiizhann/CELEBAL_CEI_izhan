-- Q11: NTILE(4) – Divide Customers into 4 Quartiles by Lifetime Value
-- Quartile labels: Platinum (1st) / Gold (2nd) / Silver (3rd) / Bronze (4th)

WITH ltv AS (
    SELECT
        c.customer_id,
        c.customer_name,
        ROUND(SUM(oi.quantity * oi.unit_price * (1.0 - oi.discount_percent / 100.0)), 2) AS total_value
    FROM customers c
    JOIN orders      o  ON c.customer_id = o.customer_id
    JOIN order_items oi ON o.order_id    = oi.order_id
    WHERE oi.quantity > 0
    GROUP BY c.customer_id
)
SELECT
    customer_id,
    customer_name,
    total_value,
    NTILE(4) OVER (ORDER BY total_value DESC) AS quartile,
    CASE NTILE(4) OVER (ORDER BY total_value DESC)
        WHEN 1 THEN 'Platinum'
        WHEN 2 THEN 'Gold'
        WHEN 3 THEN 'Silver'
        ELSE        'Bronze'
    END AS quartile_label
FROM ltv
ORDER BY total_value DESC;
