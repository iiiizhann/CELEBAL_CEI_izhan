-- Q13: First & Last Purchased Category per Customer
-- category_shift = 'Yes' if first and last purchased categories differ.

WITH cat_orders AS (
    SELECT
        o.customer_id,
        p.category,
        o.order_date,
        ROW_NUMBER() OVER (PARTITION BY o.customer_id ORDER BY o.order_date ASC)  AS rn_first,
        ROW_NUMBER() OVER (PARTITION BY o.customer_id ORDER BY o.order_date DESC) AS rn_last
    FROM orders o
    JOIN order_items oi ON o.order_id    = oi.order_id
    JOIN products    p  ON oi.product_id = p.product_id
    WHERE o.customer_id <> 'UNKNOWN'
),
first_last AS (
    SELECT
        customer_id,
        MAX(CASE WHEN rn_first = 1 THEN category END) AS first_category,
        MAX(CASE WHEN rn_last  = 1 THEN category END) AS last_category
    FROM cat_orders
    GROUP BY customer_id
)
SELECT
    customer_id,
    first_category,
    last_category,
    CASE WHEN first_category <> last_category THEN 'Yes' ELSE 'No' END AS category_shift
FROM first_last
ORDER BY customer_id;
