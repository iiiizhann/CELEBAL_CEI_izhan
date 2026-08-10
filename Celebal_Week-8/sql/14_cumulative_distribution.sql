-- Q14: Cumulative Distribution – % of Total Revenue from Top N% of Customers
-- Uses CUME_DIST() and cumulative SUM window functions.

WITH ltv AS (
    SELECT
        o.customer_id,
        SUM(oi.quantity * oi.unit_price * (1.0 - oi.discount_percent / 100.0)) AS revenue
    FROM orders o
    JOIN order_items oi ON o.order_id = oi.order_id
    WHERE oi.quantity > 0
      AND o.customer_id <> 'UNKNOWN'
    GROUP BY o.customer_id
),
ranked AS (
    SELECT
        customer_id,
        revenue,
        CUME_DIST() OVER (ORDER BY revenue DESC)                              AS cum_pct_customers,
        SUM(revenue) OVER (ORDER BY revenue DESC ROWS UNBOUNDED PRECEDING)
            / SUM(revenue) OVER ()                                            AS cum_pct_revenue
    FROM ltv
)
SELECT
    customer_id,
    ROUND(revenue, 2)                  AS revenue,
    ROUND(cum_pct_customers * 100, 1)  AS cumulative_percent_customers,
    ROUND(cum_pct_revenue   * 100, 1)  AS cumulative_revenue_percent
FROM ranked
ORDER BY cum_pct_customers;
