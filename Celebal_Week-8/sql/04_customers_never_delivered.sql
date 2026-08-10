-- Q4: Customers Who Placed Orders But Never Had Any Item Delivered

SELECT DISTINCT o.customer_id
FROM orders o
WHERE o.status <> 'DELIVERED'
  AND o.customer_id NOT IN (
      SELECT customer_id FROM orders WHERE status = 'DELIVERED'
  )
  AND o.customer_id <> 'UNKNOWN';
