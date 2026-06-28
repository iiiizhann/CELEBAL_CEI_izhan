
-- Section E — Advanced Concepts (CASE, ACID, Transactions)
USE superstore_db;

-- Q24. Write a query using CASE to classify products into price tiers:
SELECT product_name, 
       unit_price,
       CASE 
           WHEN unit_price < 1000 THEN 'Budget'
           WHEN unit_price BETWEEN 1000 AND 3000 THEN 'Mid-Range'
           ELSE 'Premium'
       END AS price_tier
FROM products;


-- Q25. Using a CASE statement inside an aggregate function, count how many orders are 'Delivered' vs 'Not Delivered' (all other statuses). Display the result in a single row.
SELECT 
    SUM(CASE WHEN status = 'Delivered' THEN 1 ELSE 0 END) AS Delivered,
    SUM(CASE WHEN status <> 'Delivered' THEN 1 ELSE 0 END) AS Not_Delivered
FROM orders;

-- Q27. Write a SQL transaction that does the following atomically:
START TRANSACTION;

-- Step 1: Insert the new order
INSERT INTO orders (order_id, customer_id, order_date, status, total_amount) 
VALUES (1011, 102, CURDATE(), 'Pending', 1598.00);

-- Step 2: Insert two order items for that order
INSERT INTO order_items (item_id, order_id, product_id, quantity, unit_price, discount_pct) 
VALUES (5016, 1011, 206, 1, 1299.00, 0);

INSERT INTO order_items (item_id, order_id, product_id, quantity, unit_price, discount_pct) 
VALUES (5017, 1011, 208, 1, 599.00, 0);

-- Step 3: Update the stock_qty of the purchased products
UPDATE products 
SET stock_qty = stock_qty - 1 
WHERE product_id = 206;

UPDATE products 
SET stock_qty = stock_qty - 1 
WHERE product_id = 208;

-- Step 4: Commit all structural operations cleanly to disk
COMMIT;