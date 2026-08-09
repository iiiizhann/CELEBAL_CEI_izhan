#!/usr/bin/env python3ls
from __future__ import annotations

import argparse
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd

EMAIL_RE = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")
VALID_STATUSES = {"completed", "shipped", "processing", "cancelled", "returned"}
STATUS_MAP = {
    "shippd": "shipped",
    "complet": "completed",
    "cancel": "cancelled",
    "CANCEL": "cancelled",
    "pendingg": "processing",
    "unknown": "processing",
}


def load_raw(raw_dir: Path) -> dict[str, pd.DataFrame]:
    return {
        "customers": pd.read_csv(raw_dir / "customers.csv"),
        "products": pd.read_csv(raw_dir / "products.csv"),
        "orders": pd.read_csv(raw_dir / "orders.csv"),
        "order_items": pd.read_csv(raw_dir / "order_items.csv"),
    }


def clean_customers(df: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, Any]]:
    report: dict[str, Any] = {"table": "customers", "issues": {}}
    original = len(df)

    before = len(df)
    df = df.drop_duplicates(subset=["customer_id"], keep="first")
    report["issues"]["duplicate_customer_ids_removed"] = before - len(df)

    df["email"] = df["email"].astype(str).str.strip().str.lower()
    df.loc[df["email"].isin(["nan", "none", ""]), "email"] = pd.NA
    invalid = df["email"].notna() & ~df["email"].str.match(EMAIL_RE, na=False)
    report["issues"]["invalid_emails_nullified"] = int(invalid.sum())
    df.loc[invalid, "email"] = pd.NA

    df["city"] = df["city"].astype(str).str.strip()
    df.loc[df["city"].isin(["nan", "None", ""]), "city"] = pd.NA
    df["state"] = df["state"].astype(str).str.strip().str.upper()
    df.loc[df["state"].isin(["NAN", "NONE", ""]), "state"] = pd.NA

    df["signup_date"] = pd.to_datetime(df["signup_date"], errors="coerce")
    report["issues"]["bad_signup_dates"] = int(df["signup_date"].isna().sum())

    df["is_active"] = (
        pd.to_numeric(df["is_active"], errors="coerce").fillna(0).astype(int)
    )

    report["rows_before"] = original
    report["rows_after"] = len(df)
    return df, report


def clean_products(df: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, Any]]:
    report: dict[str, Any] = {"table": "products", "issues": {}}
    original = len(df)

    df = df.drop_duplicates(subset=["product_id"], keep="first")

    neg = df["unit_price"] <= 0
    report["issues"]["non_positive_prices_fixed"] = int(neg.sum())
    if neg.any():
        medians = (
            df.loc[df["unit_price"] > 0]
            .groupby("category")["unit_price"]
            .median()
        )
        overall = df.loc[df["unit_price"] > 0, "unit_price"].median()
        for idx in df[neg].index:
            cat = df.at[idx, "category"]
            df.at[idx, "unit_price"] = medians.get(cat, overall)

    df["unit_cost"] = pd.to_numeric(df["unit_cost"], errors="coerce").clip(lower=0)
    df["stock_qty"] = (
        pd.to_numeric(df["stock_qty"], errors="coerce").fillna(0).astype(int)
    )
    df["is_active"] = (
        pd.to_numeric(df["is_active"], errors="coerce").fillna(0).astype(int)
    )

    report["rows_before"] = original
    report["rows_after"] = len(df)
    return df, report


def clean_orders(
    df: pd.DataFrame,
    valid_customer_ids: set[int],
) -> tuple[pd.DataFrame, dict[str, Any]]:
    report: dict[str, Any] = {"table": "orders", "issues": {}}
    original = len(df)

    df = df.drop_duplicates(subset=["order_id"], keep="first")

    df["status"] = df["status"].astype(str).str.strip().str.lower()
    df["status"] = df["status"].replace(STATUS_MAP)
    bad = ~df["status"].isin(VALID_STATUSES)
    report["issues"]["invalid_status_set_to_processing"] = int(bad.sum())
    df.loc[bad, "status"] = "processing"

    df["order_date"] = pd.to_datetime(df["order_date"], errors="coerce")
    max_dt = datetime.now()
    future = df["order_date"] > max_dt
    report["issues"]["future_dates_capped"] = int(future.sum())
    df.loc[future, "order_date"] = max_dt

    orphan = ~df["customer_id"].isin(valid_customer_ids)
    report["issues"]["orphan_orders_dropped"] = int(orphan.sum())
    df = df.loc[~orphan].copy()

    df["shipping_cost"] = (
        pd.to_numeric(df["shipping_cost"], errors="coerce").fillna(0).clip(lower=0)
    )
    df["discount_pct"] = (
        pd.to_numeric(df["discount_pct"], errors="coerce").fillna(0).clip(0, 100)
    )

    report["rows_before"] = original
    report["rows_after"] = len(df)
    return df, report


def clean_order_items(
    df: pd.DataFrame,
    valid_order_ids: set[int],
    valid_product_ids: set[int],
    product_prices: pd.Series,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    report: dict[str, Any] = {"table": "order_items", "issues": {}}
    original = len(df)

    df = df.drop_duplicates(subset=["order_item_id"], keep="first")

    bad_order = ~df["order_id"].isin(valid_order_ids)
    bad_prod = ~df["product_id"].isin(valid_product_ids)
    report["issues"]["items_with_missing_order_dropped"] = int(bad_order.sum())
    report["issues"]["items_with_missing_product_dropped"] = int(bad_prod.sum())
    df = df.loc[~bad_order & ~bad_prod].copy()

    df["quantity"] = (
        pd.to_numeric(df["quantity"], errors="coerce")
        .fillna(1)
        .clip(lower=1)
        .astype(int)
    )

    df["unit_price"] = pd.to_numeric(df["unit_price"], errors="coerce")
    bad_price = df["unit_price"].isna() | (df["unit_price"] <= 0)
    report["issues"]["bad_unit_prices_replaced_from_catalog"] = int(bad_price.sum())
    df.loc[bad_price, "unit_price"] = df.loc[bad_price, "product_id"].map(product_prices)

    still_bad = df["unit_price"].isna()
    report["issues"]["items_unrecoverable_price_dropped"] = int(still_bad.sum())
    df = df.loc[~still_bad].copy()

    report["rows_before"] = original
    report["rows_after"] = len(df)
    return df, report


def run_pipeline(raw_dir: Path, clean_dir: Path) -> dict[str, Any]:
    raw = load_raw(raw_dir)
    reports: list[dict[str, Any]] = []

    customers, r = clean_customers(raw["customers"])
    reports.append(r)

    products, r = clean_products(raw["products"])
    reports.append(r)

    valid_cust = set(customers["customer_id"].tolist())
    orders, r = clean_orders(raw["orders"], valid_cust)
    reports.append(r)

    valid_orders = set(orders["order_id"].tolist())
    valid_prods = set(products["product_id"].tolist())
    price_map = products.set_index("product_id")["unit_price"]
    items, r = clean_order_items(
        raw["order_items"], valid_orders, valid_prods, price_map
    )
    reports.append(r)

    items = items[items["order_id"].isin(valid_orders)]

    clean_dir.mkdir(parents=True, exist_ok=True)
    customers.to_csv(clean_dir / "customers_clean.csv", index=False)
    products.to_csv(clean_dir / "products_clean.csv", index=False)
    orders.to_csv(clean_dir / "orders_clean.csv", index=False)
    items.to_csv(clean_dir / "order_items_clean.csv", index=False)

    summary = {
        "generated_at": datetime.now().isoformat(),
        "tables": reports,
        "totals": {
            "customers": len(customers),
            "products": len(products),
            "orders": len(orders),
            "order_items": len(items),
        },
    }
    with open(clean_dir / "validation_report.json", "w") as f:
        json.dump(summary, f, indent=2, default=str)

    return summary


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description="Clean & validate e-commerce CSVs")
    parser.add_argument("--raw-dir", default=str(root / "data" / "raw"))
    parser.add_argument("--clean-dir", default=str(root / "data" / "cleaned"))
    args = parser.parse_args()

    summary = run_pipeline(Path(args.raw_dir), Path(args.clean_dir))
    print("Cleaning complete.")
    print(json.dumps(summary, indent=2, default=str))


if __name__ == "__main__":
    main()