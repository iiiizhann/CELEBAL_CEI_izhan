-- Q7: Running Total of Revenue per Region Ordered by Date
-- Uses SUM() OVER() window function partitioned by region.

SELECT
    o.region_code,
    DATE(o.order_date)                                                                              AS order_date,
    ROUND(SUM(oi.quantity * oi.unit_price * (1.0 - oi.discount_percent / 100.0)), 2)               AS daily_revenue,
    ROUND(SUM(SUM(oi.quantity * oi.unit_price * (1.0 - oi.discount_percent / 100.0)))
          OVER (PARTITION BY o.region_code ORDER BY DATE(o.order_date)), 2)                         AS running_total
FROM orders o
JOIN order_items oi ON o.order_id = oi.order_id
WHERE oi.quantity > 0
GROUP BY o.region_code, DATE(o.order_date)
ORDER BY o.region_code, order_date;
