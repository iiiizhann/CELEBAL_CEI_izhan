-- Q1: Total Revenue per Category
-- Revenue = quantity * unit_price * (1 - discount_percent / 100)

SELECT
    p.category,
    ROUND(SUM(oi.quantity * oi.unit_price * (1.0 - oi.discount_percent / 100.0)), 2) AS total_revenue
FROM order_items oi
JOIN products p ON oi.product_id = p.product_id
WHERE oi.quantity > 0
GROUP BY p.category
ORDER BY total_revenue DESC;
