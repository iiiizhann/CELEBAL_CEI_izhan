SELECT
    c.customer_id,
    c.first_name || ' ' || c.last_name AS customer_name,
    COUNT(DISTINCT o.order_id) AS order_count,
    ROUND(SUM(oi.quantity * oi.unit_price), 2) AS total_revenue
FROM customers c
JOIN orders o       ON c.customer_id = o.customer_id
JOIN order_items oi ON o.order_id = oi.order_id
WHERE o.status IN ('completed', 'shipped')
GROUP BY c.customer_id
ORDER BY total_revenue DESC
LIMIT 30;

-- 2. Total revenue per category
SELECT
    p.category,
    COUNT(DISTINCT o.order_id) AS orders,
    SUM(oi.quantity) AS units_sold,
    ROUND(SUM(oi.quantity * oi.unit_price), 2) AS revenue
FROM order_items oi
JOIN products p ON oi.product_id = p.product_id
JOIN orders o   ON oi.order_id = o.order_id
WHERE o.status IN ('completed', 'shipped')
GROUP BY p.category
ORDER BY revenue DESC;

-- 3. Total revenue per month
SELECT
    strftime('%Y-%m', o.order_date) AS month,
    COUNT(DISTINCT o.order_id) AS orders,
    ROUND(SUM(oi.quantity * oi.unit_price), 2) AS revenue,
    ROUND(SUM(oi.quantity * oi.unit_price) / COUNT(DISTINCT o.order_id), 2) AS aov
FROM orders o
JOIN order_items oi ON o.order_id = oi.order_id
WHERE o.status IN ('completed', 'shipped')
GROUP BY 1
ORDER BY 1;

-- 4. Top products by quantity sold and revenue
SELECT
    p.product_id,
    p.product_name,
    p.category,
    SUM(oi.quantity) AS units_sold,
    ROUND(SUM(oi.quantity * oi.unit_price), 2) AS revenue
FROM order_items oi
JOIN products p ON oi.product_id = p.product_id
JOIN orders o   ON oi.order_id = o.order_id
WHERE o.status IN ('completed', 'shipped')
GROUP BY p.product_id
ORDER BY units_sold DESC
LIMIT 25;

-- 5. AOV by customer segment
WITH cust_orders AS (
    SELECT
        c.customer_id,
        COUNT(DISTINCT o.order_id) AS n_orders,
        SUM(oi.quantity * oi.unit_price) AS revenue
    FROM customers c
    JOIN orders o ON c.customer_id = o.customer_id
    JOIN order_items oi ON o.order_id = oi.order_id
    WHERE o.status IN ('completed', 'shipped')
    GROUP BY c.customer_id
)
SELECT
    CASE
        WHEN n_orders = 1 THEN 'one-time'
        WHEN n_orders BETWEEN 2 AND 4 THEN 'occasional'
        ELSE 'loyal'
    END AS segment,
    COUNT(*) AS customers,
    ROUND(AVG(revenue / n_orders), 2) AS avg_order_value,
    ROUND(AVG(revenue), 2) AS avg_lifetime_value
FROM cust_orders
GROUP BY segment
ORDER BY avg_lifetime_value DESC;