#!/usr/bin/env python3
from __future__ import annotations

import argparse
import shutil
import sqlite3
import tempfile
from pathlib import Path

import pandas as pd


def load(clean_dir: Path, db_path: Path, schema_path: Path) -> None:
    db_path.parent.mkdir(parents=True, exist_ok=True)

    tmp = Path(tempfile.gettempdir()) / "ecom_build.db"
    if tmp.exists():
        tmp.unlink()

    conn = sqlite3.connect(tmp)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.executescript(schema_path.read_text())

    mapping = {
        "customers": "customers_clean.csv",
        "products": "products_clean.csv",
        "orders": "orders_clean.csv",
        "order_items": "order_items_clean.csv",
    }
    for table, fname in mapping.items():
        df = pd.read_csv(clean_dir / fname)
        df.to_sql(table, conn, if_exists="append", index=False)
        print(f"  loaded {table}: {len(df):,} rows")

    counts = conn.execute(
        """
        SELECT
            (SELECT COUNT(*) FROM customers),
            (SELECT COUNT(*) FROM products),
            (SELECT COUNT(*) FROM orders),
            (SELECT COUNT(*) FROM order_items)
        """
    ).fetchone()
    print(
        f"\nIntegrity snapshot → customers={counts[0]}, products={counts[1]}, "
        f"orders={counts[2]}, items={counts[3]}"
    )

    orphans = conn.execute(
        """
        SELECT COUNT(*) FROM orders o
        LEFT JOIN customers c ON o.customer_id = c.customer_id
        WHERE c.customer_id IS NULL
        """
    ).fetchone()[0]
    assert orphans == 0, f"Found {orphans} orphan orders"

    item_orphans = conn.execute(
        """
        SELECT COUNT(*) FROM order_items i
        LEFT JOIN orders o ON i.order_id = o.order_id
        WHERE o.order_id IS NULL
        """
    ).fetchone()[0]
    assert item_orphans == 0, f"Found {item_orphans} orphan order_items"

    conn.commit()
    conn.close()

    if db_path.exists():
        db_path.unlink()
    shutil.copy2(tmp, db_path)
    print(f"\nDatabase ready: {db_path.resolve()}")


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description="Load cleaned data into SQLite")
    parser.add_argument("--clean-dir", default=str(root / "data" / "cleaned"))
    parser.add_argument("--db", default=str(root / "data" / "ecommerce.db"))
    parser.add_argument("--schema", default=str(root / "sql" / "schema.sql"))
    args = parser.parse_args()

    load(Path(args.clean_dir), Path(args.db), Path(args.schema))


if __name__ == "__main__":
    main()