
-- Section D — Joins & Relationships

USE superstore_db;

-- Q19. Write an INNER JOIN query to display each order along with the customer's first_name and last_name. Show: order_id, order_date, first_name, last_name, total_amount.
SELECT o.order_id, o.order_date, c.first_name, c.last_name, o.total_amount
FROM orders o
INNER JOIN customers c ON o.customer_id = c.customer_id;


-- Q20. Using a LEFT JOIN, list ALL customers and their orders (if any). Customers with no orders should still appear with NULL values for order columns.
SELECT c.customer_id, c.first_name, c.last_name, o.order_id, o.order_date, o.total_amount
FROM customers c
LEFT JOIN orders o ON c.customer_id = o.customer_id;


-- Q21. Write a query using JOINs across three tables (orders → order_items → products) to show: order_id, product_name, quantity, unit_price, and discount_pct for each order item.
SELECT oi.order_id, p.product_name, oi.quantity, oi.unit_price, oi.discount_pct
FROM orders o
INNER JOIN order_items oi ON o.order_id = oi.order_id
INNER JOIN products p     ON oi.product_id = p.product_id;