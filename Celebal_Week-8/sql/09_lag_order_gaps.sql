-- Q9: LAG Analysis – Days Between Consecutive Orders per Customer
-- Flags customers as "At Risk" if average gap between orders > 30 days.

WITH order_gaps AS (
    SELECT
        customer_id,
        order_date,
        LAG(order_date) OVER (PARTITION BY customer_id ORDER BY order_date) AS prev_order_date,
        JULIANDAY(order_date) - JULIANDAY(
            LAG(order_date) OVER (PARTITION BY customer_id ORDER BY order_date)
        ) AS days_gap
    FROM orders
    WHERE customer_id <> 'UNKNOWN'
),
avg_gaps AS (
    SELECT
        customer_id,
        ROUND(AVG(days_gap), 1) AS avg_gap_days
    FROM order_gaps
    WHERE days_gap IS NOT NULL
    GROUP BY customer_id
)
SELECT
    customer_id,
    avg_gap_days,
    CASE WHEN avg_gap_days > 30 THEN 'At Risk' ELSE 'Active' END AS customer_status
FROM avg_gaps
ORDER BY avg_gap_days DESC;
