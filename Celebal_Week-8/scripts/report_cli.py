#!/usr/bin/env python3

import argparse
import sqlite3
import sys
from pathlib import Path

DEFAULT_DB = Path(__file__).resolve().parents[1] / "data" / "ecommerce.db"


# ---------------------------------------------------------------------------
# DB helpers
# ---------------------------------------------------------------------------

def _connect(db_path: Path) -> sqlite3.Connection:
    if not db_path.exists():
        print(f"ERROR: Database not found at {db_path}", file=sys.stderr)
        print("Run: python scripts/generate_data.py && python scripts/clean_data.py && python scripts/load_db.py",
              file=sys.stderr)
        sys.exit(1)
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    return conn


def _fetch(conn: sqlite3.Connection, sql: str, params: tuple = ()) -> list:
    cur = conn.execute(sql, params)
    return [dict(row) for row in cur.fetchall()]


# ---------------------------------------------------------------------------
# Period helper
# ---------------------------------------------------------------------------

def _period_filter(report_type: str, start: str, end: str):
    """Return the SQLite strftime format and the WHERE snippet for the period."""
    fmt_map = {"daily": "%Y-%m-%d", "weekly": "%Y-%W", "monthly": "%Y-%m"}
    fmt = fmt_map.get(report_type, "%Y-%m")
    where = (
        f"strftime('{fmt}', o.order_date) >= strftime('{fmt}', ?)"
        f" AND strftime('{fmt}', o.order_date) <= strftime('{fmt}', ?)"
    )
    return where, fmt


def _prev_dates(report_type: str, start: str, end: str):
    """Compute the previous-period start/end dates (simple offset)."""
    from datetime import datetime, timedelta
    fmt_full = "%Y-%m-%d"
    try:
        s = datetime.strptime(start, fmt_full)
        e = datetime.strptime(end, fmt_full)
    except ValueError:
        return None, None
    span = (e - s).days + 1
    prev_end = s - timedelta(days=1)
    prev_start = prev_end - timedelta(days=span - 1)
    return prev_start.strftime(fmt_full), prev_end.strftime(fmt_full)


# ---------------------------------------------------------------------------
# Core metrics
# ---------------------------------------------------------------------------

def _metrics(conn, where_clause, params):
    sql = f"""
        SELECT
            COUNT(DISTINCT o.order_id)  AS total_orders,
            ROUND(SUM(oi.quantity * oi.unit_price * (1.0 - oi.discount_percent / 100.0)), 2) AS total_revenue,
            COUNT(DISTINCT o.customer_id) AS unique_customers
        FROM orders o
        JOIN order_items oi ON o.order_id = oi.order_id
        WHERE oi.quantity > 0 AND o.customer_id <> 'UNKNOWN'
          AND {where_clause}
    """
    rows = _fetch(conn, sql, params)
    return rows[0] if rows else {"total_orders": 0, "total_revenue": 0.0, "unique_customers": 0}


def _top_products(conn, where_clause, params):
    sql = f"""
        SELECT
            p.product_name,
            SUM(oi.quantity) AS units_sold,
            ROUND(SUM(oi.quantity * oi.unit_price * (1.0 - oi.discount_percent / 100.0)), 2) AS revenue
        FROM orders o
        JOIN order_items oi ON o.order_id   = oi.order_id
        JOIN products    p  ON oi.product_id = p.product_id
        WHERE oi.quantity > 0
          AND {where_clause}
        GROUP BY p.product_id
        ORDER BY revenue DESC
        LIMIT 3
    """
    return _fetch(conn, sql, params)


# ---------------------------------------------------------------------------
# Report printer
# ---------------------------------------------------------------------------

def _pct(new, old):
    if old and old != 0:
        return round(((new - old) / abs(old)) * 100, 1)
    return None


def _fmt_pct(val):
    if val is None:
        return "N/A (no prior period)"
    sign = "+" if val >= 0 else ""
    return f"{sign}{val}%"


def print_report(report_type, start, end, cur, prev, top_prods, prev_start, prev_end):
    w = 52
    print("\n" + "=" * w)
    print(f"  E-COMMERCE SUMMARY REPORT  [{report_type.upper()}]")
    print(f"  Period : {start}  to  {end}")
    print("=" * w)
    print(f"\n{'Metric':<25} {'Current':>10}  {'Previous':>10}  {'Change':>12}")
    print("-" * w)

    metrics = [
        ("Total Orders",      cur["total_orders"],      prev["total_orders"] if prev else None,      ""),
        ("Total Revenue ($)", cur["total_revenue"],     prev["total_revenue"] if prev else None,     ""),
        ("Unique Customers",  cur["unique_customers"],  prev["unique_customers"] if prev else None,  ""),
    ]
    for label, c_val, p_val, _ in metrics:
        pct = _pct(c_val or 0, p_val) if p_val is not None else None
        c_str = f"{c_val}" if c_val is not None else "N/A"
        prev_str = f"{p_val:>10}" if p_val is not None else "       N/A"
        print(f"  {label:<23} {c_str:>10}  {prev_str}  {_fmt_pct(pct):>12}")


    print(f"\n{'-' * w}")
    print("  TOP 3 PRODUCTS (by revenue)")
    print(f"{'-' * w}")

    if top_prods:
        for rank, p in enumerate(top_prods, 1):
            print(f"  {rank}. {p['product_name'][:35]:<35}  ${p['revenue']:>10,.2f}  ({p['units_sold']} units)")
    else:
        print("  (no data for this period)")

    if prev_start:
        print(f"\n  Comparison period: {prev_start} to {prev_end}")

    print("=" * w + "\n")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="E-Commerce Analytics – Summary Report")
    parser.add_argument("--db",     default=str(DEFAULT_DB), help="Path to SQLite database")
    parser.add_argument("--report", choices=["daily", "weekly", "monthly"], help="Report period type")
    parser.add_argument("--from",   dest="date_from", help="Start date YYYY-MM-DD")
    parser.add_argument("--to",     dest="date_to",   help="End date   YYYY-MM-DD")
    args = parser.parse_args()

    # Interactive prompts if flags not provided
    report_type = args.report
    if not report_type:
        report_type = input("Report type [daily / weekly / monthly]: ").strip().lower()
    if report_type not in ("daily", "weekly", "monthly"):
        print("ERROR: report type must be daily, weekly, or monthly.", file=sys.stderr)
        sys.exit(1)

    date_from = args.date_from
    if not date_from:
        date_from = input("Start date (YYYY-MM-DD): ").strip()

    date_to = args.date_to
    if not date_to:
        date_to = input("End date   (YYYY-MM-DD): ").strip()

    conn = _connect(Path(args.db))
    try:
        where, _ = _period_filter(report_type, date_from, date_to)
        cur_params = (date_from, date_to)

        cur_metrics   = _metrics(conn, where, cur_params)
        cur_top_prods = _top_products(conn, where, cur_params)

        prev_start, prev_end = _prev_dates(report_type, date_from, date_to)
        prev_metrics = None
        if prev_start and prev_end:
            prev_metrics = _metrics(conn, where, (prev_start, prev_end))

        print_report(report_type, date_from, date_to,
                     cur_metrics, prev_metrics, cur_top_prods,
                     prev_start, prev_end)
    finally:
        conn.close()


if __name__ == "__main__":
    main()