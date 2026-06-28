
-- Section C — Aggregation (GROUP BY, SUM, COUNT, AVG, MIN, MAX)
USE superstore_db;

-- Q13. Count the total number of orders in the orders table.
SELECT COUNT(*) AS total_orders 
FROM orders;


-- Q14. Find the total revenue (SUM of total_amount) from all 'Delivered' orders.
SELECT SUM(total_amount) AS total_delivered_revenue 
FROM orders 
WHERE status = 'Delivered';


-- Q15. Calculate the average unit_price of products in each category.
SELECT category, AVG(unit_price) AS average_unit_price 
FROM products 
GROUP BY category;


-- Q16. For each order status, find the count of orders and the total revenue. Sort the result by total revenue in descending order.
SELECT status, 
       COUNT(order_id) AS order_count, 
       SUM(total_amount) AS total_revenue
FROM orders 
GROUP BY status
ORDER BY total_revenue DESC;


-- Q17. Find the most expensive (MAX) and cheapest (MIN) product in each category.
SELECT category, 
       MAX(unit_price) AS most_expensive_product, 
       MIN(unit_price) AS cheapest_product 
FROM products 
GROUP BY category;


-- Q18. List all product categories where the average unit_price is greater than ₹2000. (Hint: Use HAVING clause)
SELECT category, AVG(unit_price) AS average_unit_price 
FROM products 
GROUP BY category
HAVING AVG(unit_price) > 2000;