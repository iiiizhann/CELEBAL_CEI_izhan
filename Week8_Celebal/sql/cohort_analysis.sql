
WITH first_order AS (
    SELECT
        customer_id,
        MIN(strftime('%Y-%m', order_date)) AS cohort_month
    FROM orders
    WHERE status IN ('completed', 'shipped')
    GROUP BY customer_id
),
activity AS (
    SELECT
        customer_id,
        strftime('%Y-%m', order_date) AS activity_month
    FROM orders
    WHERE status IN ('completed', 'shipped')
    GROUP BY customer_id, activity_month
),
cohort_size AS (
    SELECT cohort_month, COUNT(*) AS cohort_customers
    FROM first_order
    GROUP BY cohort_month
),
retention AS (
    SELECT
        f.cohort_month,
        a.activity_month,
        COUNT(DISTINCT a.customer_id) AS active_customers,
        (CAST(substr(a.activity_month, 1, 4) AS INT) - CAST(substr(f.cohort_month, 1, 4) AS INT)) * 12
            + (CAST(substr(a.activity_month, 6, 2) AS INT) - CAST(substr(f.cohort_month, 6, 2) AS INT))
            AS month_number
    FROM first_order f
    JOIN activity a ON f.customer_id = a.customer_id
    GROUP BY f.cohort_month, a.activity_month
)
SELECT
    r.cohort_month,
    cs.cohort_customers,
    r.month_number,
    r.active_customers,
    ROUND(100.0 * r.active_customers / cs.cohort_customers, 1) AS retention_pct
FROM retention r
JOIN cohort_size cs ON r.cohort_month = cs.cohort_month
WHERE r.month_number BETWEEN 0 AND 12
ORDER BY r.cohort_month, r.month_number;

-- 6b. Churned vs repeat
WITH cust_stats AS (
    SELECT
        c.customer_id,
        COUNT(DISTINCT o.order_id) AS order_count,
        SUM(oi.quantity * oi.unit_price) AS lifetime_value
    FROM customers c
    JOIN orders o ON c.customer_id = o.customer_id
    JOIN order_items oi ON o.order_id = oi.order_id
    WHERE o.status IN ('completed', 'shipped')
    GROUP BY c.customer_id
)
SELECT
    CASE
        WHEN order_count = 1 THEN 'one-time (churn risk)'
        WHEN order_count BETWEEN 2 AND 3 THEN 'repeat (occasional)'
        ELSE 'loyal (repeat)'
    END AS customer_type,
    COUNT(*) AS customers,
    ROUND(AVG(lifetime_value), 2) AS avg_ltv,
    ROUND(AVG(order_count), 1) AS avg_orders
FROM cust_stats
GROUP BY customer_type
ORDER BY avg_ltv DESC;

-- 7a. Frequency segments
WITH freq AS (
    SELECT c.customer_id, COUNT(DISTINCT o.order_id) AS n_orders
    FROM customers c
    JOIN orders o ON c.customer_id = o.customer_id
    WHERE o.status IN ('completed', 'shipped')
    GROUP BY c.customer_id
)
SELECT
    CASE
        WHEN n_orders = 1 THEN 'one-time'
        WHEN n_orders BETWEEN 2 AND 4 THEN 'occasional'
        ELSE 'loyal'
    END AS frequency_segment,
    COUNT(*) AS customers
FROM freq
GROUP BY frequency_segment
ORDER BY customers DESC;

-- 7b. Spend tiers
WITH spend AS (
    SELECT
        c.customer_id,
        SUM(oi.quantity * oi.unit_price) AS total_spend
    FROM customers c
    JOIN orders o ON c.customer_id = o.customer_id
    JOIN order_items oi ON o.order_id = oi.order_id
    WHERE o.status IN ('completed', 'shipped')
    GROUP BY c.customer_id
),
bounds AS (
    SELECT
        (SELECT total_spend FROM spend ORDER BY total_spend LIMIT 1 OFFSET (SELECT COUNT(*) / 3 FROM spend)) AS p33,
        (SELECT total_spend FROM spend ORDER BY total_spend LIMIT 1 OFFSET (SELECT 2 * COUNT(*) / 3 FROM spend)) AS p66
)
SELECT
    CASE
        WHEN s.total_spend <= b.p33 THEN 'low'
        WHEN s.total_spend <= b.p66 THEN 'medium'
        ELSE 'high'
    END AS spend_tier,
    COUNT(*) AS customers,
    ROUND(MIN(s.total_spend), 2) AS min_spend,
    ROUND(MAX(s.total_spend), 2) AS max_spend,
    ROUND(AVG(s.total_spend), 2) AS avg_spend
FROM spend s, bounds b
GROUP BY spend_tier
ORDER BY avg_spend;

-- 7c. RFM analysis
WITH cust_metrics AS (
    SELECT
        c.customer_id,
        c.first_name || ' ' || c.last_name AS customer_name,
        MAX(o.order_date) AS last_order,
        COUNT(DISTINCT o.order_id) AS frequency,
        SUM(oi.quantity * oi.unit_price) AS monetary
    FROM customers c
    JOIN orders o ON c.customer_id = o.customer_id
    JOIN order_items oi ON o.order_id = oi.order_id
    WHERE o.status IN ('completed', 'shipped')
    GROUP BY c.customer_id
),
scored AS (
    SELECT
        *,
        JULIANDAY('2025-07-01') - JULIANDAY(last_order) AS recency_days,
        NTILE(5) OVER (ORDER BY JULIANDAY('2025-07-01') - JULIANDAY(last_order) DESC) AS r_score,
        NTILE(5) OVER (ORDER BY frequency) AS f_score,
        NTILE(5) OVER (ORDER BY monetary) AS m_score
    FROM cust_metrics
)
SELECT
    customer_id,
    customer_name,
    ROUND(recency_days, 0) AS recency_days,
    frequency,
    ROUND(monetary, 2) AS monetary,
    r_score, f_score, m_score,
    CASE
        WHEN r_score >= 4 AND f_score >= 4 AND m_score >= 4 THEN 'Champions'
        WHEN r_score >= 3 AND f_score >= 3 AND m_score >= 3 THEN 'Loyal'
        WHEN r_score >= 4 AND f_score <= 2                  THEN 'New / Promising'
        WHEN r_score <= 2 AND f_score >= 3                  THEN 'At Risk'
        WHEN r_score <= 2 AND f_score <= 2                  THEN 'Lost'
        ELSE 'Potential'
    END AS segment
FROM scored
ORDER BY monetary DESC
LIMIT 50;