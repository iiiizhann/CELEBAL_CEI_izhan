-- Q5: Products That Were Ordered But Had More Returns Than Purchases
-- Negative quantity in order_items represents a return.

SELECT
    p.product_id,
    p.product_name,
    SUM(CASE WHEN oi.quantity > 0 THEN  oi.quantity ELSE 0 END) AS total_purchased,
    SUM(CASE WHEN oi.quantity < 0 THEN -oi.quantity ELSE 0 END) AS total_returned
FROM order_items oi
JOIN products p ON oi.product_id = p.product_id
GROUP BY p.product_id
HAVING total_returned > total_purchased
ORDER BY total_returned DESC;
