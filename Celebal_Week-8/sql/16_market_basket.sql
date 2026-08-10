-- Q16: Market Basket Analysis – Products Frequently Bought Together
-- Uses a self-join on order_items to find product pairs in the same order.
-- A-B and B-A are treated as one pair (product_id_a < product_id_b).
-- Excludes same-product pairs.

SELECT
    p1.product_name          AS product_a,
    p2.product_name          AS product_b,
    COUNT(*)                 AS times_bought_together
FROM order_items a
JOIN order_items b  ON a.order_id = b.order_id
                   AND a.product_id < b.product_id   -- ensures A-B only, no duplicates
JOIN products p1 ON a.product_id = p1.product_id
JOIN products p2 ON b.product_id = p2.product_id
GROUP BY a.product_id, b.product_id
ORDER BY times_bought_together DESC
LIMIT 10;
