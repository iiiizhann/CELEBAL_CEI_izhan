-- schema.sql
-- E-Commerce Analytics – SQLite schema
-- Matches columns in the cleaned CSV files produced by clean_data.py
-- Note: FK declarations omitted to allow UNKNOWN customer_id rows during bulk load.

DROP TABLE IF EXISTS order_items;
DROP TABLE IF EXISTS orders;
DROP TABLE IF EXISTS products;
DROP TABLE IF EXISTS customers;

CREATE TABLE customers (
    customer_id       TEXT PRIMARY KEY,
    customer_name     TEXT NOT NULL,
    email             TEXT,
    registration_date TEXT,
    customer_type     TEXT,          -- REGULAR | PREMIUM | VIP
    invalid_email     INTEGER DEFAULT 0
);

CREATE TABLE products (
    product_id   TEXT PRIMARY KEY,
    product_name TEXT NOT NULL,
    category     TEXT,
    subcategory  TEXT,
    cost_price   REAL
);

CREATE TABLE orders (
    order_id              TEXT PRIMARY KEY,
    customer_id           TEXT,
    order_date            TEXT,    -- YYYY-MM-DD HH:MM:SS after cleaning
    status                TEXT,    -- PLACED | SHIPPED | DELIVERED | CANCELLED | RETURNED
    region_code           TEXT,    -- NORTH | SOUTH | EAST | WEST | CENTRAL
    customer_id_missing   INTEGER DEFAULT 0
);

CREATE TABLE order_items (
    item_id          TEXT PRIMARY KEY,
    order_id         TEXT,
    product_id       TEXT,
    quantity         INTEGER,
    unit_price       REAL,
    discount_percent REAL
);