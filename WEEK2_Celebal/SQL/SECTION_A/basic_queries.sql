
-- Section A — SQL Basics
USE superstore_db;

-- Q1. Write a query to display all columns and rows from the customer's table.
SELECT * FROM customers;

-- Q2. Retrieve only the first_name, last_name, and city of all customers.
SELECT first_name, last_name, city 
FROM customers;

-- Q3. List all unique categories available in the products table.
SELECT DISTINCT `Category` 
FROM products;

-- Q4.
 SELECT TABLE_NAME, COLUMN_NAME
 FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE
 WHERE TABLE_SCHEMA = 'superstore_db' 
  AND CONSTRAINT_NAME = 'PRIMARY';
  

-- Q6. Try inserting a product with unit_price = -50. What happens and which constraint prevents it? Write both the INSERT statement and explain the error.

 INSERT INTO products (product_id, product_name, category, brand, unit_price, stock_qty)
 VALUES (209, 'Negative Price Test Product', 'Electronics', 'TestBrand', -50.00, 10);