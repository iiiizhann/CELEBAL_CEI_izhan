#!/usr/bin/env python3


import sqlite3
from pathlib import Path

import pandas as pd

BASE_DIR = Path(__file__).resolve().parents[1]
CLEAN_DIR = BASE_DIR / "data" / "cleaned"
DB_PATH = BASE_DIR / "data" / "ecommerce.db"
SCHEMA_SQL = BASE_DIR / "sql" / "schema.sql"


def create_tables(conn: sqlite3.Connection) -> None:
    with open(SCHEMA_SQL, "r") as f:
        conn.executescript(f.read())
    conn.commit()


def load_csv(conn: sqlite3.Connection, csv_path: Path, table: str) -> int:
    df = pd.read_csv(csv_path)
    df.to_sql(table, conn, if_exists="append", index=False)
    return len(df)


def main() -> None:
    if DB_PATH.exists():
        DB_PATH.unlink()
    conn = sqlite3.connect(str(DB_PATH))
    conn.execute("PRAGMA foreign_keys = OFF")
    create_tables(conn)

    counts = {}
    counts["customers"]   = load_csv(conn, CLEAN_DIR / "customers_clean.csv",   "customers")
    counts["products"]    = load_csv(conn, CLEAN_DIR / "products_clean.csv",    "products")
    counts["orders"]      = load_csv(conn, CLEAN_DIR / "orders_clean.csv",      "orders")
    counts["order_items"] = load_csv(conn, CLEAN_DIR / "order_items_clean.csv", "order_items")
    conn.commit()
    conn.execute("PRAGMA foreign_keys = ON")
    conn.close()

    print("=== SQLite Load Summary ===")
    for tbl, n in counts.items():
        print(f"  {tbl:<14}: {n} rows")
    print(f"\nDatabase saved to: {DB_PATH}")


if __name__ == "__main__":
    main()