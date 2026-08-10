-- Q15: Cohort Analysis by Registration Month
-- For each registration cohort, shows how many customers ordered in
-- months 0, 1, 2, and 3 after registration, and the retention rate.

WITH cohort AS (
    SELECT
        c.customer_id,
        strftime('%Y-%m', c.registration_date) AS cohort_month
    FROM customers c
),
activity AS (
    SELECT
        o.customer_id,
        strftime('%Y-%m', o.order_date) AS activity_month
    FROM orders o
    WHERE o.customer_id <> 'UNKNOWN'
    GROUP BY o.customer_id, activity_month
),
cohort_size AS (
    SELECT cohort_month, COUNT(*) AS cohort_customers
    FROM cohort
    GROUP BY cohort_month
),
retention_raw AS (
    SELECT
        co.cohort_month,
        (
            (CAST(substr(ac.activity_month, 1, 4) AS INT) - CAST(substr(co.cohort_month, 1, 4) AS INT)) * 12
            + CAST(substr(ac.activity_month, 6, 2) AS INT) - CAST(substr(co.cohort_month, 6, 2) AS INT)
        ) AS months_since_signup,
        COUNT(DISTINCT ac.customer_id) AS active_customers
    FROM cohort co
    JOIN activity ac ON co.customer_id = ac.customer_id
    GROUP BY co.cohort_month, months_since_signup
)
SELECT
    r.cohort_month,
    cs.cohort_customers,
    r.months_since_signup,
    r.active_customers,
    ROUND(100.0 * r.active_customers / cs.cohort_customers, 1) AS retention_pct
FROM retention_raw r
JOIN cohort_size cs ON r.cohort_month = cs.cohort_month
WHERE r.months_since_signup BETWEEN 0 AND 3
ORDER BY r.cohort_month, r.months_since_signup;
