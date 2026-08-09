#!/usr/bin/env python3

from __future__ import annotations

import argparse
import sqlite3
import sys
from pathlib import Path
from typing import Any, Optional

from tabulate import tabulate

DEFAULT_DB = Path(__file__).resolve().parents[1] / "data" / "ecommerce.db"
VALID_REPORTS = [
    "overview",
    "revenue",
    "top_customers",
    "top_products",
    "categories",
    "aov_segments",
    "retention",
    "rfm",
    "churn",
    "frequency",
    "spend_tiers",
]


def connect(db_path: Path) -> sqlite3.Connection:
    if not db_path.exists():
        print(f"ERROR: Database not found at {db_path}", file=sys.stderr)
        print(
            "Run: python scripts/generate_data.py && python scripts/clean_data.py && python scripts/load_db.py",
            file=sys.stderr,
        )
        sys.exit(1)
    try:
        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        conn.execute("SELECT 1 FROM customers LIMIT 1")
        return conn
    except sqlite3.Error as e:
        print(f"ERROR: Could not connect to database: {e}", file=sys.stderr)
        sys.exit(2)


def fetch_all(conn: sqlite3.Connection, sql: str, params: tuple = ()) -> list[dict[str, Any]]:
    try:
        cur = conn.execute(sql, params)
        cols = [d[0] for d in cur.description]
        rows = cur.fetchall()
        return [dict(zip(cols, row)) for row in rows]
    except sqlite3.Error as e:
        print(f"SQL error: {e}", file=sys.stderr)
        return []


def print_table(rows: list[dict[str, Any]], title: str = "") -> None:
    if title:
        print(f"\n=== {title} ===\n")
    if not rows:
        print("  (no rows returned – empty result set)")
        return
    headers = list(rows[0].keys())
    table = [[r[h] for h in headers] for r in rows]
    print(tabulate(table, headers=headers, tablefmt="github", floatfmt=".2f"))
    print(f"\n  ({len(rows)} row(s))")


def report_overview(conn: sqlite3.Connection) -> None:
    counts = fetch_all(
        conn,
        """
        SELECT
            (SELECT COUNT(*) FROM customers) AS customers,
            (SELECT COUNT(*) FROM products) AS products,
            (SELECT COUNT(*) FROM orders) AS orders,
            (SELECT COUNT(*) FROM order_items) AS items
        """,
    )
    print_table(counts, "DATABASE OVERVIEW")

    status = fetch_all(
        conn,
        """
        SELECT status, COUNT(*) AS cnt,
               ROUND(100.0 * COUNT(*) / (SELECT COUNT(*) FROM orders), 1) AS pct
        FROM orders GROUP BY status ORDER BY cnt DESC
        """,
    )
    print_table(status, "ORDER STATUS DISTRIBUTION")

    rev = fetch_all(
        conn,
        """
        SELECT ROUND(SUM(oi.quantity * oi.unit_price), 2) AS gross_revenue
        FROM order_items oi
        JOIN orders o ON oi.order_id = o.order_id
        WHERE o.status IN ('completed', 'shipped')
        """,
    )
    print_table(rev, "GROSS REVENUE (completed/shipped)")


def report_revenue(
    conn: sqlite3.Connection,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
) -> None:
    clauses = ["o.status IN ('completed', 'shipped')"]
    params: list[Any] = []
    if date_from:
        clauses.append("strftime('%Y-%m', o.order_date) >= ?")
        params.append(date_from)
    if date_to:
        clauses.append("strftime('%Y-%m', o.order_date) <= ?")
        params.append(date_to)
    where = " AND ".join(clauses)

    sql = f"""
        WITH monthly AS (
            SELECT
                strftime('%Y-%m', o.order_date) AS month,
                COUNT(DISTINCT o.order_id) AS orders,
                SUM(oi.quantity * oi.unit_price) AS gross_revenue
            FROM orders o
            JOIN order_items oi ON o.order_id = oi.order_id
            WHERE {where}
            GROUP BY 1
        )
        SELECT
            month,
            orders,
            ROUND(gross_revenue, 2) AS gross_revenue,
            ROUND(gross_revenue / NULLIF(orders, 0), 2) AS aov,
            ROUND(
                (gross_revenue - LAG(gross_revenue) OVER (ORDER BY month))
                / NULLIF(LAG(gross_revenue) OVER (ORDER BY month), 0) * 100, 1
            ) AS mom_growth_pct
        FROM monthly
        ORDER BY month
    """
    rows = fetch_all(conn, sql, tuple(params))
    print_table(rows, "MONTHLY REVENUE & MoM GROWTH")


def report_top_customers(conn: sqlite3.Connection, limit: int = 25) -> None:
    sql = """
        SELECT
            c.customer_id,
            c.first_name || ' ' || c.last_name AS customer_name,
            COUNT(DISTINCT o.order_id) AS order_count,
            ROUND(SUM(oi.quantity * oi.unit_price), 2) AS total_revenue
        FROM customers c
        JOIN orders o ON c.customer_id = o.customer_id
        JOIN order_items oi ON o.order_id = oi.order_id
        WHERE o.status IN ('completed', 'shipped')
        GROUP BY c.customer_id
        ORDER BY total_revenue DESC
        LIMIT ?
    """
    rows = fetch_all(conn, sql, (limit,))
    print_table(rows, f"TOP {limit} CUSTOMERS BY REVENUE")


def report_top_products(conn: sqlite3.Connection, limit: int = 25) -> None:
    sql = """
        SELECT
            p.product_id,
            p.product_name,
            p.category,
            SUM(oi.quantity) AS units_sold,
            ROUND(SUM(oi.quantity * oi.unit_price), 2) AS revenue
        FROM order_items oi
        JOIN products p ON oi.product_id = p.product_id
        JOIN orders o ON oi.order_id = o.order_id
        WHERE o.status IN ('completed', 'shipped')
        GROUP BY p.product_id
        ORDER BY units_sold DESC
        LIMIT ?
    """
    rows = fetch_all(conn, sql, (limit,))
    print_table(rows, f"TOP {limit} PRODUCTS BY UNITS SOLD")


def report_categories(conn: sqlite3.Connection) -> None:
    sql = """
        SELECT
            p.category,
            COUNT(DISTINCT o.order_id) AS orders,
            SUM(oi.quantity) AS units_sold,
            ROUND(SUM(oi.quantity * oi.unit_price), 2) AS revenue
        FROM order_items oi
        JOIN products p ON oi.product_id = p.product_id
        JOIN orders o ON oi.order_id = o.order_id
        WHERE o.status IN ('completed', 'shipped')
        GROUP BY p.category
        ORDER BY revenue DESC
    """
    rows = fetch_all(conn, sql)
    print_table(rows, "REVENUE BY CATEGORY")


def report_aov_segments(conn: sqlite3.Connection) -> None:
    sql = """
        WITH cust_orders AS (
            SELECT
                c.customer_id,
                COUNT(DISTINCT o.order_id) AS n_orders,
                SUM(oi.quantity * oi.unit_price) AS revenue
            FROM customers c
            JOIN orders o ON c.customer_id = o.customer_id
            JOIN order_items oi ON o.order_id = oi.order_id
            WHERE o.status IN ('completed', 'shipped')
            GROUP BY c.customer_id
        )
        SELECT
            CASE
                WHEN n_orders = 1 THEN 'one-time'
                WHEN n_orders BETWEEN 2 AND 4 THEN 'occasional'
                ELSE 'loyal'
            END AS segment,
            COUNT(*) AS customers,
            ROUND(AVG(revenue / n_orders), 2) AS avg_order_value,
            ROUND(AVG(revenue), 2) AS avg_lifetime_value
        FROM cust_orders
        GROUP BY segment
        ORDER BY avg_lifetime_value DESC
    """
    rows = fetch_all(conn, sql)
    print_table(rows, "AOV BY CUSTOMER SEGMENT")


def report_retention(conn: sqlite3.Connection, cohort: Optional[str] = None) -> None:
    sql = """
        WITH first_order AS (
            SELECT customer_id, MIN(strftime('%Y-%m', order_date)) AS cohort_month
            FROM orders
            WHERE status IN ('completed', 'shipped')
            GROUP BY customer_id
        ),
        activity AS (
            SELECT customer_id, strftime('%Y-%m', order_date) AS activity_month
            FROM orders
            WHERE status IN ('completed', 'shipped')
            GROUP BY customer_id, activity_month
        ),
        cohort_size AS (
            SELECT cohort_month, COUNT(*) AS cohort_customers
            FROM first_order GROUP BY cohort_month
        ),
        retention AS (
            SELECT
                f.cohort_month,
                a.activity_month,
                COUNT(DISTINCT a.customer_id) AS active_customers,
                (CAST(substr(a.activity_month, 1, 4) AS INT) - CAST(substr(f.cohort_month, 1, 4) AS INT)) * 12
                    + (CAST(substr(a.activity_month, 6, 2) AS INT) - CAST(substr(f.cohort_month, 6, 2) AS INT))
                    AS month_number
            FROM first_order f
            JOIN activity a ON f.customer_id = a.customer_id
            GROUP BY f.cohort_month, a.activity_month
        )
        SELECT
            r.cohort_month,
            cs.cohort_customers,
            r.month_number,
            r.active_customers,
            ROUND(100.0 * r.active_customers / cs.cohort_customers, 1) AS retention_pct
        FROM retention r
        JOIN cohort_size cs ON r.cohort_month = cs.cohort_month
        WHERE r.month_number BETWEEN 0 AND 12
    """
    params: list[Any] = []
    if cohort:
        sql += " AND r.cohort_month = ?"
        params.append(cohort)
    sql += " ORDER BY r.cohort_month, r.month_number"
    rows = fetch_all(conn, sql, tuple(params))
    print_table(rows, "COHORT RETENTION (months 0–12)")


def report_rfm(conn: sqlite3.Connection, limit: int = 40) -> None:
    sql = """
        WITH cust_metrics AS (
            SELECT
                c.customer_id,
                c.first_name || ' ' || c.last_name AS customer_name,
                MAX(o.order_date) AS last_order,
                COUNT(DISTINCT o.order_id) AS frequency,
                SUM(oi.quantity * oi.unit_price) AS monetary
            FROM customers c
            JOIN orders o ON c.customer_id = o.customer_id
            JOIN order_items oi ON o.order_id = oi.order_id
            WHERE o.status IN ('completed', 'shipped')
            GROUP BY c.customer_id
        ),
        scored AS (
            SELECT
                *,
                JULIANDAY('2025-07-01') - JULIANDAY(last_order) AS recency_days,
                NTILE(5) OVER (ORDER BY JULIANDAY('2025-07-01') - JULIANDAY(last_order) DESC) AS r_score,
                NTILE(5) OVER (ORDER BY frequency) AS f_score,
                NTILE(5) OVER (ORDER BY monetary) AS m_score
            FROM cust_metrics
        )
        SELECT
            customer_id,
            customer_name,
            ROUND(recency_days, 0) AS recency_days,
            frequency,
            ROUND(monetary, 2) AS monetary,
            r_score, f_score, m_score,
            CASE
                WHEN r_score >= 4 AND f_score >= 4 AND m_score >= 4 THEN 'Champions'
                WHEN r_score >= 3 AND f_score >= 3 AND m_score >= 3 THEN 'Loyal'
                WHEN r_score >= 4 AND f_score <= 2 THEN 'New / Promising'
                WHEN r_score <= 2 AND f_score >= 3 THEN 'At Risk'
                WHEN r_score <= 2 AND f_score <= 2 THEN 'Lost'
                ELSE 'Potential'
            END AS segment
        FROM scored
        ORDER BY monetary DESC
        LIMIT ?
    """
    rows = fetch_all(conn, sql, (limit,))
    print_table(rows, f"RFM SEGMENTATION (top {limit})")

    dist = fetch_all(
        conn,
        """
        WITH cust_metrics AS (
            SELECT
                c.customer_id,
                MAX(o.order_date) AS last_order,
                COUNT(DISTINCT o.order_id) AS frequency,
                SUM(oi.quantity * oi.unit_price) AS monetary
            FROM customers c
            JOIN orders o ON c.customer_id = o.customer_id
            JOIN order_items oi ON o.order_id = oi.order_id
            WHERE o.status IN ('completed', 'shipped')
            GROUP BY c.customer_id
        ),
        scored AS (
            SELECT
                NTILE(5) OVER (ORDER BY JULIANDAY('2025-07-01') - JULIANDAY(last_order) DESC) AS r_score,
                NTILE(5) OVER (ORDER BY frequency) AS f_score,
                NTILE(5) OVER (ORDER BY monetary) AS m_score
            FROM cust_metrics
        )
        SELECT
            CASE
                WHEN r_score >= 4 AND f_score >= 4 AND m_score >= 4 THEN 'Champions'
                WHEN r_score >= 3 AND f_score >= 3 AND m_score >= 3 THEN 'Loyal'
                WHEN r_score >= 4 AND f_score <= 2 THEN 'New / Promising'
                WHEN r_score <= 2 AND f_score >= 3 THEN 'At Risk'
                WHEN r_score <= 2 AND f_score <= 2 THEN 'Lost'
                ELSE 'Potential'
            END AS segment,
            COUNT(*) AS customers
        FROM scored
        GROUP BY segment
        ORDER BY customers DESC
        """,
    )
    print_table(dist, "RFM SEGMENT DISTRIBUTION")


def report_churn(conn: sqlite3.Connection, min_ltv: float = 0.0) -> None:
    sql = """
        WITH cust_value AS (
            SELECT
                c.customer_id,
                c.first_name || ' ' || c.last_name AS name,
                c.email,
                SUM(oi.quantity * oi.unit_price) AS lifetime_value,
                MAX(o.order_date) AS last_order_date
            FROM customers c
            JOIN orders o ON c.customer_id = o.customer_id
            JOIN order_items oi ON o.order_id = oi.order_id
            WHERE o.status IN ('completed', 'shipped')
            GROUP BY c.customer_id
        )
        SELECT
            customer_id,
            name,
            email,
            ROUND(lifetime_value, 2) AS lifetime_value,
            last_order_date,
            CAST(JULIANDAY('2025-07-01') - JULIANDAY(last_order_date) AS INT) AS days_since_last
        FROM cust_value
        WHERE JULIANDAY('2025-07-01') - JULIANDAY(last_order_date) > 90
          AND lifetime_value >= ?
        ORDER BY lifetime_value DESC
        LIMIT 40
    """
    rows = fetch_all(conn, sql, (min_ltv,))
    print_table(rows, f"HIGH-VALUE CHURN RISK (LTV ≥ {min_ltv}, inactive > 90 days)")


def report_frequency(conn: sqlite3.Connection) -> None:
    sql = """
        WITH freq AS (
            SELECT c.customer_id, COUNT(DISTINCT o.order_id) AS n_orders
            FROM customers c
            JOIN orders o ON c.customer_id = o.customer_id
            WHERE o.status IN ('completed', 'shipped')
            GROUP BY c.customer_id
        )
        SELECT
            CASE
                WHEN n_orders = 1 THEN 'one-time'
                WHEN n_orders BETWEEN 2 AND 4 THEN 'occasional'
                ELSE 'loyal'
            END AS frequency_segment,
            COUNT(*) AS customers
        FROM freq
        GROUP BY frequency_segment
        ORDER BY customers DESC
    """
    rows = fetch_all(conn, sql)
    print_table(rows, "PURCHASE FREQUENCY SEGMENTS")


def report_spend_tiers(conn: sqlite3.Connection) -> None:
    sql = """
        WITH spend AS (
            SELECT
                c.customer_id,
                SUM(oi.quantity * oi.unit_price) AS total_spend
            FROM customers c
            JOIN orders o ON c.customer_id = o.customer_id
            JOIN order_items oi ON o.order_id = oi.order_id
            WHERE o.status IN ('completed', 'shipped')
            GROUP BY c.customer_id
        ),
        bounds AS (
            SELECT
                (SELECT total_spend FROM spend ORDER BY total_spend
                 LIMIT 1 OFFSET (SELECT COUNT(*) / 3 FROM spend)) AS p33,
                (SELECT total_spend FROM spend ORDER BY total_spend
                 LIMIT 1 OFFSET (SELECT 2 * COUNT(*) / 3 FROM spend)) AS p66
        )
        SELECT
            CASE
                WHEN s.total_spend <= b.p33 THEN 'low'
                WHEN s.total_spend <= b.p66 THEN 'medium'
                ELSE 'high'
            END AS spend_tier,
            COUNT(*) AS customers,
            ROUND(MIN(s.total_spend), 2) AS min_spend,
            ROUND(MAX(s.total_spend), 2) AS max_spend,
            ROUND(AVG(s.total_spend), 2) AS avg_spend
        FROM spend s, bounds b
        GROUP BY spend_tier
        ORDER BY avg_spend
    """
    rows = fetch_all(conn, sql)
    print_table(rows, "SPEND TIER SEGMENTS")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="E-commerce Analytics CLI Reporting Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Valid --report values: " + ", ".join(VALID_REPORTS),
    )
    parser.add_argument(
        "--report",
        required=True,
        choices=VALID_REPORTS,
        help="Report to generate",
    )
    parser.add_argument("--db", default=str(DEFAULT_DB), help="Path to SQLite DB")
    parser.add_argument("--from", dest="date_from", help="Start month YYYY-MM (revenue)")
    parser.add_argument("--to", dest="date_to", help="End month YYYY-MM (revenue)")
    parser.add_argument("--limit", type=int, default=25, help="Row limit for top_* reports")
    parser.add_argument("--cohort", help="Filter retention to cohort YYYY-MM")
    parser.add_argument("--min-ltv", type=float, default=0.0, help="Min LTV for churn report")
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if args.limit < 1:
        print("ERROR: --limit must be >= 1", file=sys.stderr)
        sys.exit(1)
    if args.min_ltv < 0:
        print("ERROR: --min-ltv must be >= 0", file=sys.stderr)
        sys.exit(1)

    conn = connect(Path(args.db))
    try:
        if args.report == "overview":
            report_overview(conn)
        elif args.report == "revenue":
            report_revenue(conn, args.date_from, args.date_to)
        elif args.report == "top_customers":
            report_top_customers(conn, args.limit)
        elif args.report == "top_products":
            report_top_products(conn, args.limit)
        elif args.report == "categories":
            report_categories(conn)
        elif args.report == "aov_segments":
            report_aov_segments(conn)
        elif args.report == "retention":
            report_retention(conn, args.cohort)
        elif args.report == "rfm":
            report_rfm(conn, args.limit)
        elif args.report == "churn":
            report_churn(conn, args.min_ltv)
        elif args.report == "frequency":
            report_frequency(conn)
        elif args.report == "spend_tiers":
            report_spend_tiers(conn)
    finally:
        conn.close()


if __name__ == "__main__":
    main()