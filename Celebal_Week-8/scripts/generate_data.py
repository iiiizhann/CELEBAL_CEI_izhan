#!/usr/bin/env python3

import random
from pathlib import Path
from datetime import datetime
import pandas as pd
import numpy as np
from faker import Faker

# Fixed seed for reproducibility
SEED = 42
random.seed(SEED)
np.random.seed(SEED)
fake = Faker()
Faker.seed(SEED)

# Output directories
RAW_DIR = Path(__file__).resolve().parents[1] / "data" / "raw"
RAW_DIR.mkdir(parents=True, exist_ok=True)

# Configuration
NUM_ORDERS = 600
NUM_CUSTOMERS = 560
NUM_PRODUCTS = 120
NUM_ORDER_ITEMS = 1200
REGION_CODES = ["NORTH", "SOUTH", "EAST", "WEST", "CENTRAL"]
PRODUCT_CATEGORIES = {
    "Electronics": ["TV", "Mobile", "Laptop", "Camera"],
    "Clothing": ["Shirt", "Pants", "Shoes", "Jacket"],
    "Home": ["Furniture", "Kitchen", "Bedding", "Decor"],
    "Books": ["Fiction", "Non‑Fiction", "Science", "History"]
}
CUSTOMER_TYPES = ["REGULAR", "PREMIUM", "VIP"]

def generate_customers() -> pd.DataFrame:
    rows = []
    for i in range(1, NUM_CUSTOMERS + 1):
        name = fake.name()
        email = fake.email()
        # ~2% invalid emails
        if random.random() < 0.02:
            if "@" in email:
                email = email.replace("@", "")
            else:
                email = email + "invalid"
        reg_date = fake.date_between(start_date="-2y", end_date="today")
        cust_type = random.choice(CUSTOMER_TYPES)
        rows.append([i, name, email, reg_date.strftime("%Y-%m-%d"), cust_type])
    return pd.DataFrame(rows, columns=["customer_id", "customer_name", "email", "registration_date", "customer_type"])

def generate_products() -> pd.DataFrame:
    rows = []
    pid = 1
    for cat, subs in PRODUCT_CATEGORIES.items():
        for sub in subs:
            count = max(1, NUM_PRODUCTS // (len(PRODUCT_CATEGORIES) * len(subs)))
            for _ in range(count):
                name = f"{sub} {fake.word().title()}"
                # Intentional extra spaces / mixed case
                if random.random() < 0.1:
                    name = "  " + name.upper() + "  "
                cost = round(random.uniform(5, 200), 2)
                rows.append([pid, name, cat, sub, cost])
                pid += 1
    return pd.DataFrame(rows, columns=["product_id", "product_name", "category", "subcategory", "cost_price"])

def generate_orders() -> pd.DataFrame:
    rows = []
    for i in range(1, NUM_ORDERS + 1):
        # ~5% NULL/empty customer_id
        cust_id = random.randint(1, NUM_CUSTOMERS) if random.random() > 0.05 else ""
        base = fake.date_time_between(start_date="-1y", end_date="now")
        if random.random() < 0.15:
            order_date = base.strftime("%d-%m-%Y")
        else:
            order_date = base.strftime("%Y-%m-%d %H:%M:%S")
        status = random.choice(["PLACED", "SHIPPED", "DELIVERED", "CANCELLED", "RETURNED"])
        region = random.choice(REGION_CODES)
        rows.append([i, cust_id, order_date, status, region])
    return pd.DataFrame(rows, columns=["order_id", "customer_id", "order_date", "status", "region_code"])

def generate_order_items(orders_df: pd.DataFrame, products_df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    item_id = 1
    for _ in range(NUM_ORDER_ITEMS):
        order_id = random.choice(orders_df["order_id"].tolist())
        product_id = random.choice(products_df["product_id"].tolist())
        quantity = random.randint(1, 10)
        # ~3% negative quantity (returns)
        if random.random() < 0.03:
            quantity = -quantity
        unit_price = round(random.uniform(10, 500), 2)
        discount = round(random.uniform(0, 100), 2)
        rows.append([item_id, order_id, product_id, quantity, unit_price, discount])
        item_id += 1
    return pd.DataFrame(rows, columns=["item_id", "order_id", "product_id", "quantity", "unit_price", "discount_percent"])

def main():
    customers = generate_customers()
    products = generate_products()
    orders = generate_orders()
    order_items = generate_order_items(orders, products)
    customers.to_csv(RAW_DIR / "customers.csv", index=False)
    products.to_csv(RAW_DIR / "products.csv", index=False)
    orders.to_csv(RAW_DIR / "orders.csv", index=False)
    order_items.to_csv(RAW_DIR / "order_items.csv", index=False)
    print("Data generated in", RAW_DIR)

if __name__ == "__main__":
    main()