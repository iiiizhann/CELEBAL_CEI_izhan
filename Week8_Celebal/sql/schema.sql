-- Step 3: Database schema with PK, FK, NOT NULL and domain constraints
PRAGMA foreign_keys = ON;

DROP TABLE IF EXISTS order_items;
DROP TABLE IF EXISTS orders;
DROP TABLE IF EXISTS products;
DROP TABLE IF EXISTS customers;

CREATE TABLE customers (
    customer_id   INTEGER PRIMARY KEY,
    first_name    TEXT    NOT NULL,
    last_name     TEXT    NOT NULL,
    email         TEXT,
    signup_date   TEXT,
    city          TEXT,
    state         TEXT,
    is_active     INTEGER NOT NULL DEFAULT 1 CHECK (is_active IN (0, 1))
);

CREATE TABLE products (
    product_id    INTEGER PRIMARY KEY,
    product_name  TEXT    NOT NULL,
    category      TEXT    NOT NULL,
    brand         TEXT,
    unit_price    REAL    NOT NULL CHECK (unit_price > 0),
    unit_cost     REAL    NOT NULL CHECK (unit_cost >= 0),
    stock_qty     INTEGER NOT NULL DEFAULT 0 CHECK (stock_qty >= 0),
    is_active     INTEGER NOT NULL DEFAULT 1 CHECK (is_active IN (0, 1))
);

CREATE TABLE orders (
    order_id        INTEGER PRIMARY KEY,
    customer_id     INTEGER NOT NULL REFERENCES customers(customer_id),
    order_date      TEXT    NOT NULL,
    status          TEXT    NOT NULL CHECK (
                        status IN ('completed', 'shipped', 'processing', 'cancelled', 'returned')
                    ),
    payment_method  TEXT,
    shipping_cost   REAL    NOT NULL DEFAULT 0 CHECK (shipping_cost >= 0),
    discount_pct    REAL    NOT NULL DEFAULT 0 CHECK (discount_pct >= 0 AND discount_pct <= 100)
);

CREATE TABLE order_items (
    order_item_id   INTEGER PRIMARY KEY,
    order_id        INTEGER NOT NULL REFERENCES orders(order_id) ON DELETE CASCADE,
    product_id      INTEGER NOT NULL REFERENCES products(product_id),
    quantity        INTEGER NOT NULL CHECK (quantity > 0),
    unit_price      REAL    NOT NULL CHECK (unit_price > 0)
);

CREATE INDEX idx_orders_customer   ON orders(customer_id);
CREATE INDEX idx_orders_date       ON orders(order_date);
CREATE INDEX idx_orders_status     ON orders(status);
CREATE INDEX idx_items_order       ON order_items(order_id);
CREATE INDEX idx_items_product     ON order_items(product_id);
CREATE INDEX idx_products_category ON products(category);
CREATE INDEX idx_customers_signup  ON customers(signup_date);