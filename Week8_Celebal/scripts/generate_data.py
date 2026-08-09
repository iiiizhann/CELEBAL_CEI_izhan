#!/usr/bin/env python3
from __future__ import annotations

import argparse
import random
from datetime import datetime, timedelta
from pathlib import Path

import numpy as np
import pandas as pd
from faker import Faker

SEED = 42
N_CUSTOMERS = 2_000
N_PRODUCTS = 150
N_ORDERS = 10_000
START_DATE = datetime(2023, 1, 1)
END_DATE = datetime(2025, 6, 30)

CATEGORIES = [
    "Electronics", "Clothing", "Home & Kitchen", "Books", "Sports",
    "Beauty", "Toys", "Grocery", "Automotive", "Health",
]
BRANDS = [
    "NovaTech", "UrbanWear", "HomeNest", "PageTurner", "FitPro",
    "GlowLab", "PlayZone", "FreshMart", "DriveMax", "VitalCare",
]
STATUSES = ["completed", "shipped", "processing", "cancelled", "returned"]
PAYMENT_METHODS = ["credit_card", "debit_card", "paypal", "upi", "cod", "wallet"]

MISSING_RATE = 0.05
DUPLICATE_RATE = 0.02
INVALID_EMAIL_RATE = 0.03
NEGATIVE_PRICE_RATE = 0.01
FUTURE_DATE_RATE = 0.008
ORPHAN_ORDER_RATE = 0.012
BAD_STATUS_RATE = 0.015
MISMATCHED_ITEM_RATE = 0.01


def set_seed(seed: int = SEED) -> None:
    random.seed(seed)
    np.random.seed(seed)
    Faker.seed(seed)


def random_date(start: datetime, end: datetime) -> datetime:
    delta = end - start
    return start + timedelta(seconds=random.randint(0, int(delta.total_seconds())))


def dirty_email(email: str) -> str:
    choice = random.random()
    if choice < 0.25:
        return email.replace("@", "")
    if choice < 0.5:
        return email.upper()
    if choice < 0.7:
        return email + " "
    if choice < 0.85:
        return "not-an-email"
    return ""


def generate_customers(n: int, fake: Faker) -> pd.DataFrame:
    rows = []
    for i in range(1, n + 1):
        first = fake.first_name()
        last = fake.last_name()
        email = f"{first.lower()}.{last.lower()}{i}@example.com"
        signup = random_date(START_DATE, END_DATE - timedelta(days=60))

        if random.random() < MISSING_RATE:
            email = None
        elif random.random() < INVALID_EMAIL_RATE:
            email = dirty_email(email)

        city = fake.city() if random.random() > MISSING_RATE else None
        state = fake.state_abbr() if random.random() > 0.02 else None

        rows.append({
            "customer_id": i,
            "first_name": first,
            "last_name": last,
            "email": email,
            "signup_date": signup.strftime("%Y-%m-%d"),
            "city": city,
            "state": state,
            "is_active": random.choices([1, 0], weights=[0.9, 0.1])[0],
        })

    df = pd.DataFrame(rows)

    n_dups = max(1, int(n * DUPLICATE_RATE))
    dups = df.sample(n_dups, random_state=SEED).copy()
    dups["email"] = dups["email"].apply(
        lambda e: f"dup_{e}" if isinstance(e, str) else "dup@example.com"
    )
    df = pd.concat([df, dups], ignore_index=True)
    return df


def generate_products(n: int, fake: Faker) -> pd.DataFrame:
    rows = []
    for i in range(1, n + 1):
        cat = random.choice(CATEGORIES)
        brand = random.choice(BRANDS)
        price = round(random.uniform(5.0, 799.99), 2)
        cost = round(price * random.uniform(0.35, 0.65), 2)

        if random.random() < NEGATIVE_PRICE_RATE:
            price = -abs(price)
        if random.random() < 0.005:
            price = 0.0

        rows.append({
            "product_id": i,
            "product_name": f"{brand} {cat} {fake.word().title()}-{i:03d}",
            "category": cat,
            "brand": brand,
            "unit_price": price,
            "unit_cost": cost,
            "stock_qty": random.randint(0, 400),
            "is_active": random.choices([1, 0], weights=[0.88, 0.12])[0],
        })
    return pd.DataFrame(rows)


def generate_orders_and_items(
    n_orders: int,
    customers: pd.DataFrame,
    products: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    valid_cids = customers["customer_id"].unique().tolist()
    valid_pids = products["product_id"].tolist()
    price_map = products.set_index("product_id")["unit_price"].to_dict()

    order_rows = []
    item_rows = []
    item_id = 1

    for oid in range(1, n_orders + 1):
        if random.random() < ORPHAN_ORDER_RATE:
            cust_id = max(valid_cids) + random.randint(100, 500)
        else:
            cust_id = random.choice(valid_cids)

        order_dt = random_date(START_DATE, END_DATE)
        if random.random() < FUTURE_DATE_RATE:
            order_dt = datetime(2026, 11, 1) + timedelta(days=random.randint(0, 40))

        status = random.choices(STATUSES, weights=[0.60, 0.18, 0.09, 0.08, 0.05])[0]
        if random.random() < BAD_STATUS_RATE:
            status = random.choice(["shippd", "complet", "CANCEL", "unknown", "", "pendingg"])

        order_rows.append({
            "order_id": oid,
            "customer_id": cust_id,
            "order_date": order_dt.strftime("%Y-%m-%d %H:%M:%S"),
            "status": status,
            "payment_method": random.choice(PAYMENT_METHODS),
            "shipping_cost": round(random.uniform(0, 22), 2) if status != "cancelled" else 0.0,
            "discount_pct": round(random.choice([0, 0, 0, 5, 10, 15, 20]), 1),
        })

        n_items = random.randint(1, 5)
        chosen = random.sample(valid_pids, min(n_items, len(valid_pids)))
        for pid in chosen:
            qty = random.randint(1, 4)
            unit_price = price_map.get(pid, 0.0)
            if random.random() < 0.025:
                unit_price = round(unit_price * random.uniform(0.6, 1.4), 2)
            item_rows.append({
                "order_item_id": item_id,
                "order_id": oid,
                "product_id": pid,
                "quantity": qty,
                "unit_price": unit_price,
            })
            item_id += 1

    n_bad = max(1, int(len(item_rows) * MISMATCHED_ITEM_RATE))
    for _ in range(n_bad):
        item_rows.append({
            "order_item_id": item_id,
            "order_id": n_orders + random.randint(50, 200),
            "product_id": random.choice(valid_pids),
            "quantity": random.randint(1, 3),
            "unit_price": round(random.uniform(10, 100), 2),
        })
        item_id += 1

    return pd.DataFrame(order_rows), pd.DataFrame(item_rows)


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate dirty e-commerce CSVs")
    parser.add_argument(
        "--out-dir",
        default=str(Path(__file__).resolve().parents[1] / "data" / "raw"),
    )
    parser.add_argument("--seed", type=int, default=SEED)
    args = parser.parse_args()

    set_seed(args.seed)
    fake = Faker("en_US")
    out = Path(args.out_dir)
    out.mkdir(parents=True, exist_ok=True)

    print("Generating customers …")
    customers = generate_customers(N_CUSTOMERS, fake)
    print("Generating products …")
    products = generate_products(N_PRODUCTS, fake)
    print("Generating orders & order_items …")
    orders, items = generate_orders_and_items(N_ORDERS, customers, products)

    customers.to_csv(out / "customers.csv", index=False)
    products.to_csv(out / "products.csv", index=False)
    orders.to_csv(out / "orders.csv", index=False)
    items.to_csv(out / "order_items.csv", index=False)

    print(f"\nWrote CSVs → {out.resolve()}")
    print(f"  customers   : {len(customers):,}")
    print(f"  products    : {len(products):,}")
    print(f"  orders      : {len(orders):,}")
    print(f"  order_items : {len(items):,}")
    print("\nIntentional inconsistencies:")
    print("  • null / invalid emails, missing cities")
    print("  • duplicate customer_ids")
    print("  • negative / zero product prices")
    print("  • future order dates")
    print("  • orphan customer_ids on orders")
    print("  • bad / empty status values")
    print("  • mismatched order_ids in order_items")
    print("  • occasional unit_price drift vs catalog")


if __name__ == "__main__":
    main()