-- Q10: Multi-Level CTE – Monthly Revenue Category Count per Month
-- Level 1: monthly revenue per customer
-- Level 2: categorise as High (>10000) / Medium (5000-10000) / Low (<5000)
-- Level 3: count customers in each category per month

WITH monthly_rev AS (
    SELECT
        strftime('%Y-%m', o.order_date) AS month,
        o.customer_id,
        SUM(oi.quantity * oi.unit_price * (1.0 - oi.discount_percent / 100.0)) AS revenue
    FROM orders o
    JOIN order_items oi ON o.order_id = oi.order_id
    WHERE oi.quantity > 0
      AND o.customer_id <> 'UNKNOWN'
    GROUP BY month, o.customer_id
),
categorised AS (
    SELECT
        month,
        customer_id,
        revenue,
        CASE
            WHEN revenue > 10000 THEN 'High'
            WHEN revenue >= 5000  THEN 'Medium'
            ELSE                       'Low'
        END AS revenue_category
    FROM monthly_rev
)
SELECT
    month,
    revenue_category,
    COUNT(*) AS customer_count
FROM categorised
GROUP BY month, revenue_category
ORDER BY month, revenue_category;
