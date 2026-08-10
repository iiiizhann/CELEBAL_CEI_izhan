-- Q8: DENSE_RANK Products by Total Revenue Within Each Category
-- Same revenue gets the same rank (no gaps in ranking).

SELECT
    p.category,
    p.product_id,
    p.product_name,
    ROUND(SUM(oi.quantity * oi.unit_price * (1.0 - oi.discount_percent / 100.0)), 2) AS total_revenue,
    DENSE_RANK() OVER (
        PARTITION BY p.category
        ORDER BY SUM(oi.quantity * oi.unit_price * (1.0 - oi.discount_percent / 100.0)) DESC
    ) AS revenue_rank
FROM order_items oi
JOIN products p ON oi.product_id = p.product_id
WHERE oi.quantity > 0
GROUP BY p.category, p.product_id
ORDER BY p.category, revenue_rank;
