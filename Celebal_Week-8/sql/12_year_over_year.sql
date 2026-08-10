-- Q12: Year-over-Year Revenue Comparison
-- Shows each year+month's revenue vs the same month in the previous year.
-- NULL prev_year_revenue means no data for that month last year.

WITH yearly AS (
    SELECT
        strftime('%Y', o.order_date) AS yr,
        strftime('%m', o.order_date) AS mo,
        ROUND(SUM(oi.quantity * oi.unit_price * (1.0 - oi.discount_percent / 100.0)), 2) AS revenue
    FROM orders o
    JOIN order_items oi ON o.order_id = oi.order_id
    WHERE oi.quantity > 0
    GROUP BY yr, mo
)
SELECT
    yr                                                              AS year,
    mo                                                              AS month,
    revenue,
    LAG(revenue) OVER (PARTITION BY mo ORDER BY yr)                AS prev_year_revenue,
    CASE
        WHEN LAG(revenue) OVER (PARTITION BY mo ORDER BY yr) IS NULL THEN NULL
        ELSE ROUND(
            100.0 * (revenue - LAG(revenue) OVER (PARTITION BY mo ORDER BY yr))
            / NULLIF(LAG(revenue) OVER (PARTITION BY mo ORDER BY yr), 0), 1)
    END                                                             AS yoy_growth_percent
FROM yearly
ORDER BY yr, mo;
