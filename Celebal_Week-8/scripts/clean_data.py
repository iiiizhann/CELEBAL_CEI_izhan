#!/usr/bin/env python3
"""Data cleaning for the E-Commerce Analytics project.

Reads raw CSVs from `data/raw/`, applies the four required cleaning functions,
writes cleaned CSVs to `data/cleaned/`, and saves `validation_report.json`.
"""

import json
import re
from pathlib import Path

import pandas as pd

BASE_DIR = Path(__file__).resolve().parents[1]
RAW_DIR = BASE_DIR / "data" / "raw"
CLEAN_DIR = BASE_DIR / "data" / "cleaned"
CLEAN_DIR.mkdir(parents=True, exist_ok=True)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _normalise_date(date_str: str) -> str:
    """Convert any supported date format to YYYY-MM-DD HH:MM:SS."""
    date_str = str(date_str).strip()
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d", "%d-%m-%Y"):
        try:
            return pd.to_datetime(date_str, format=fmt).strftime("%Y-%m-%d %H:%M:%S")
        except ValueError:
            continue
    return date_str  # leave unparseable values as-is


def _is_valid_email(email: str) -> bool:
    return bool(re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", str(email)))


# ---------------------------------------------------------------------------
# Required cleaning functions (assignment spec)
# ---------------------------------------------------------------------------

def clean_orders(df: pd.DataFrame) -> pd.DataFrame:
    """Fix date formats and handle NULL/empty customer_id (flag + fill)."""
    # Flag then fill missing customer_id
    df = df.copy()
    df["customer_id"] = df["customer_id"].replace("", pd.NA)
    df["customer_id_missing"] = df["customer_id"].isna()
    df["customer_id"] = df["customer_id"].fillna("UNKNOWN")
    # Normalise dates
    df["order_date"] = df["order_date"].apply(_normalise_date)
    return df


def clean_products(df: pd.DataFrame) -> pd.DataFrame:
    """Trim spaces and title-case product_name."""
    df = df.copy()
    df["product_name"] = df["product_name"].str.strip().str.title()
    return df


def validate_emails(df: pd.DataFrame) -> list:
    """Return list of customer_ids with invalid emails."""
    invalid = df[~df["email"].apply(_is_valid_email)]["customer_id"].tolist()
    return invalid


def check_referential_integrity(orders_df: pd.DataFrame, items_df: pd.DataFrame) -> pd.DataFrame:
    """Return order_items that reference non-existent orders."""
    valid_ids = set(orders_df["order_id"].astype(str))
    orphan_mask = ~items_df["order_id"].astype(str).isin(valid_ids)
    return items_df[orphan_mask].copy()


# ---------------------------------------------------------------------------
# Main driver
# ---------------------------------------------------------------------------

def main() -> None:
    # Load raw data
    orders_raw = pd.read_csv(RAW_DIR / "orders.csv", dtype=str)
    items_raw = pd.read_csv(RAW_DIR / "order_items.csv", dtype=str)
    customers_raw = pd.read_csv(RAW_DIR / "customers.csv", dtype=str)
    products_raw = pd.read_csv(RAW_DIR / "products.csv", dtype=str)

    # --- Clean ---
    orders_clean = clean_orders(orders_raw)
    products_clean = clean_products(products_raw)
    invalid_email_ids = validate_emails(customers_raw)
    orphan_items = check_referential_integrity(orders_raw, items_raw)

    # Add email validity flag to customers
    customers_clean = customers_raw.copy()
    customers_clean["invalid_email"] = ~customers_raw["email"].apply(_is_valid_email)

    # Remove orphan items for cleaned items file
    valid_ids = set(orders_raw["order_id"].astype(str))
    items_clean = items_raw[items_raw["order_id"].astype(str).isin(valid_ids)].copy()

    # --- Save cleaned CSVs ---
    orders_clean.to_csv(CLEAN_DIR / "orders_clean.csv", index=False)
    products_clean.to_csv(CLEAN_DIR / "products_clean.csv", index=False)
    customers_clean.to_csv(CLEAN_DIR / "customers_clean.csv", index=False)
    items_clean.to_csv(CLEAN_DIR / "order_items_clean.csv", index=False)

    # --- Compute issue counts for report ---
    missing_cust = int(orders_raw["customer_id"].replace("", pd.NA).isna().sum())
    bad_dates = int(
        orders_raw["order_date"]
        .apply(lambda x: bool(re.search(r"\d{2}-\d{2}-\d{4}", str(x))))
        .sum()
    )
    product_issues = int(
        products_raw["product_name"]
        .apply(lambda x: x != x.strip() or x != x.strip().title())
        .sum()
    )
    invalid_emails_cnt = len(invalid_email_ids)
    neg_qty = int((items_raw["quantity"].astype(float) < 0).sum())
    orphan_cnt = int(len(orphan_items))

    # --- Validation report (JSON) ---
    report = {
        "orders": {
            "total_rows": len(orders_raw),
            "missing_customer_id_fixed": missing_cust,
            "invalid_dates_normalised": bad_dates,
        },
        "products": {
            "total_rows": len(products_raw),
            "product_name_issues_fixed": product_issues,
        },
        "customers": {
            "total_rows": len(customers_raw),
            "invalid_emails": invalid_emails_cnt,
            "invalid_email_customer_ids": invalid_email_ids,
        },
        "order_items": {
            "total_rows": len(items_raw),
            "negative_quantities": neg_qty,
            "orphan_items_removed": orphan_cnt,
        },
    }
    with open(CLEAN_DIR / "validation_report.json", "w") as f:
        json.dump(report, f, indent=2)

    # --- Printed summary ---
    print("=" * 35)
    print("DATA CLEANING REPORT")
    print("=" * 35)
    print(f"\nOrders ({len(orders_raw)} rows)")
    print(f"  Missing customer_id flagged & filled : {missing_cust}")
    print(f"  DD-MM-YYYY dates normalised          : {bad_dates}")
    print(f"\nProducts ({len(products_raw)} rows)")
    print(f"  Product names fixed (trim + title)   : {product_issues}")
    print(f"\nCustomers ({len(customers_raw)} rows)")
    print(f"  Invalid emails flagged               : {invalid_emails_cnt}")
    print(f"\nOrder Items ({len(items_raw)} rows)")
    print(f"  Negative quantities                  : {neg_qty}")
    print(f"  Orphan items removed                 : {orphan_cnt}")
    print(f"\nCleaned CSVs saved to  : {CLEAN_DIR}")
    print(f"Validation report      : {CLEAN_DIR / 'validation_report.json'}")
    print("=" * 35)
    print("CLEANING COMPLETED")
    print("=" * 35)


if __name__ == "__main__":
    main()