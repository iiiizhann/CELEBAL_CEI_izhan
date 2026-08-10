#!/usr/bin/env python3
"""run_queries.py – Execute all 16 analytics queries and display results."""

import sqlite3
import sys
from pathlib import Path

# Force UTF-8 output so product names with any Unicode chars print cleanly
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


DB_PATH = Path(__file__).resolve().parents[1] / "data" / "ecommerce.db"


def connect():
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def run(conn, title, sql, params=()):
    w = 70
    print(f"\n{'=' * w}")
    print(f"  {title}")
    print(f"{'=' * w}")
    try:
        cur = conn.execute(sql, params)
        rows = cur.fetchall()
        if not rows:
            print("  (no rows returned)")
            return
        cols = rows[0].keys()
        # header
        col_widths = [max(len(c), max(len(str(r[c])) for r in rows)) + 2 for c in cols]
        header = "  " + "  ".join(c.ljust(col_widths[i]) for i, c in enumerate(cols))
        print(header)
        print("  " + "-" * (sum(col_widths) + 2 * len(cols)))
        for r in rows[:25]:   # cap at 25 rows for readability
            print("  " + "  ".join(str(r[c]).ljust(col_widths[i]) for i, c in enumerate(cols)))
        if len(rows) > 25:
            print(f"  ... ({len(rows)} total rows, showing first 25)")
    except Exception as e:
        print(f"  ERROR: {e}")


def main():
    conn = connect()

    # ------------------------------------------------------------------
    # BASIC  (1-3)
    # ------------------------------------------------------------------
    run(conn, "Q1 – Total Revenue per Category",
        """
        SELECT p.category,
               ROUND(SUM(oi.quantity * oi.unit_price * (1.0 - oi.discount_percent/100.0)), 2) AS total_revenue
        FROM order_items oi
        JOIN products p ON oi.product_id = p.product_id
        WHERE oi.quantity > 0
        GROUP BY p.category
        ORDER BY total_revenue DESC
        """)

    run(conn, "Q2 – Top 10 Customers by Total Order Value",
        """
        SELECT c.customer_id, c.customer_name,
               ROUND(SUM(oi.quantity * oi.unit_price * (1.0 - oi.discount_percent/100.0)), 2) AS total_order_value
        FROM customers c
        JOIN orders      o  ON c.customer_id = o.customer_id
        JOIN order_items oi ON o.order_id    = oi.order_id
        WHERE oi.quantity > 0
        GROUP BY c.customer_id
        ORDER BY total_order_value DESC
        LIMIT 10
        """)

    run(conn, "Q3 – Month-wise Order Count (Last 12 Months)",
        """
        SELECT strftime('%Y-%m', order_date) AS month,
               COUNT(*) AS order_count
        FROM orders
        WHERE order_date >= date('now', '-12 months')
        GROUP BY month
        ORDER BY month
        """)

    # ------------------------------------------------------------------
    # INTERMEDIATE  (4-6)
    # ------------------------------------------------------------------
    run(conn, "Q4 – Customers Who Placed Orders But Never Had Any Item Delivered",
        """
        SELECT DISTINCT o.customer_id
        FROM orders o
        WHERE o.status <> 'DELIVERED'
          AND o.customer_id NOT IN (
              SELECT customer_id FROM orders WHERE status = 'DELIVERED'
          )
          AND o.customer_id <> 'UNKNOWN'
        LIMIT 20
        """)

    run(conn, "Q5 – Products With More Returns Than Purchases",
        """
        SELECT p.product_id, p.product_name,
               SUM(CASE WHEN oi.quantity > 0 THEN  oi.quantity ELSE 0 END) AS total_purchased,
               SUM(CASE WHEN oi.quantity < 0 THEN -oi.quantity ELSE 0 END) AS total_returned
        FROM order_items oi
        JOIN products p ON oi.product_id = p.product_id
        GROUP BY p.product_id
        HAVING total_returned > total_purchased
        ORDER BY total_returned DESC
        """)

    run(conn, "Q6 – Return Rate per Category",
        """
        SELECT p.category,
               SUM(CASE WHEN oi.quantity < 0 THEN -oi.quantity ELSE 0 END) AS returned_units,
               SUM(ABS(oi.quantity))                                          AS total_units,
               ROUND(
                   100.0 * SUM(CASE WHEN oi.quantity < 0 THEN -oi.quantity ELSE 0 END)
                   / NULLIF(SUM(ABS(oi.quantity)), 0), 2
               ) AS return_rate_pct
        FROM order_items oi
        JOIN products p ON oi.product_id = p.product_id
        GROUP BY p.category
        ORDER BY return_rate_pct DESC
        """)

    # ------------------------------------------------------------------
    # ADVANCED  (7-16)
    # ------------------------------------------------------------------
    run(conn, "Q7 – Running Total of Revenue per Region (Window Function)",
        """
        SELECT o.region_code,
               DATE(o.order_date) AS order_date,
               ROUND(SUM(oi.quantity * oi.unit_price * (1.0 - oi.discount_percent/100.0)), 2) AS daily_revenue,
               ROUND(SUM(SUM(oi.quantity * oi.unit_price * (1.0 - oi.discount_percent/100.0)))
                     OVER (PARTITION BY o.region_code ORDER BY DATE(o.order_date)), 2) AS running_total
        FROM orders o
        JOIN order_items oi ON o.order_id = oi.order_id
        WHERE oi.quantity > 0
        GROUP BY o.region_code, DATE(o.order_date)
        ORDER BY o.region_code, order_date
        LIMIT 20
        """)

    run(conn, "Q8 – DENSE_RANK Products by Revenue Within Each Category",
        """
        SELECT p.category, p.product_id, p.product_name,
               ROUND(SUM(oi.quantity * oi.unit_price * (1.0 - oi.discount_percent/100.0)), 2) AS total_revenue,
               DENSE_RANK() OVER (
                   PARTITION BY p.category
                   ORDER BY SUM(oi.quantity * oi.unit_price * (1.0 - oi.discount_percent/100.0)) DESC
               ) AS revenue_rank
        FROM order_items oi
        JOIN products p ON oi.product_id = p.product_id
        WHERE oi.quantity > 0
        GROUP BY p.category, p.product_id
        ORDER BY p.category, revenue_rank
        LIMIT 20
        """)

    run(conn, "Q9 – LAG: Days Between Consecutive Orders + At Risk Flag",
        """
        WITH order_gaps AS (
            SELECT customer_id, order_date,
                   LAG(order_date) OVER (PARTITION BY customer_id ORDER BY order_date) AS prev_order_date,
                   JULIANDAY(order_date) - JULIANDAY(
                       LAG(order_date) OVER (PARTITION BY customer_id ORDER BY order_date)
                   ) AS days_gap
            FROM orders
            WHERE customer_id <> 'UNKNOWN'
        ),
        avg_gaps AS (
            SELECT customer_id, ROUND(AVG(days_gap), 1) AS avg_gap_days
            FROM order_gaps
            WHERE days_gap IS NOT NULL
            GROUP BY customer_id
        )
        SELECT customer_id, avg_gap_days,
               CASE WHEN avg_gap_days > 30 THEN 'At Risk' ELSE 'Active' END AS customer_status
        FROM avg_gaps
        ORDER BY avg_gap_days DESC
        LIMIT 20
        """)

    run(conn, "Q10 – CTE Multi-Level: Monthly Revenue Category Count per Month",
        """
        WITH monthly_rev AS (
            SELECT strftime('%Y-%m', o.order_date) AS month,
                   o.customer_id,
                   SUM(oi.quantity * oi.unit_price * (1.0 - oi.discount_percent/100.0)) AS revenue
            FROM orders o
            JOIN order_items oi ON o.order_id = oi.order_id
            WHERE oi.quantity > 0 AND o.customer_id <> 'UNKNOWN'
            GROUP BY month, o.customer_id
        ),
        categorised AS (
            SELECT month, customer_id, revenue,
                   CASE
                       WHEN revenue > 10000 THEN 'High'
                       WHEN revenue >= 5000  THEN 'Medium'
                       ELSE                       'Low'
                   END AS revenue_category
            FROM monthly_rev
        )
        SELECT month, revenue_category, COUNT(*) AS customer_count
        FROM categorised
        GROUP BY month, revenue_category
        ORDER BY month, revenue_category
        LIMIT 20
        """)

    run(conn, "Q11 – NTILE(4) Lifetime Value: Platinum/Gold/Silver/Bronze",
        """
        WITH ltv AS (
            SELECT c.customer_id, c.customer_name,
                   ROUND(SUM(oi.quantity * oi.unit_price * (1.0 - oi.discount_percent/100.0)), 2) AS total_value
            FROM customers c
            JOIN orders      o  ON c.customer_id = o.customer_id
            JOIN order_items oi ON o.order_id    = oi.order_id
            WHERE oi.quantity > 0
            GROUP BY c.customer_id
        )
        SELECT customer_id, customer_name, total_value,
               NTILE(4) OVER (ORDER BY total_value DESC) AS quartile,
               CASE NTILE(4) OVER (ORDER BY total_value DESC)
                   WHEN 1 THEN 'Platinum'
                   WHEN 2 THEN 'Gold'
                   WHEN 3 THEN 'Silver'
                   ELSE        'Bronze'
               END AS quartile_label
        FROM ltv
        ORDER BY total_value DESC
        LIMIT 20
        """)

    run(conn, "Q12 – Year-over-Year Revenue Comparison",
        """
        WITH yearly AS (
            SELECT strftime('%Y', o.order_date) AS yr,
                   strftime('%m', o.order_date) AS mo,
                   ROUND(SUM(oi.quantity * oi.unit_price * (1.0 - oi.discount_percent/100.0)), 2) AS revenue
            FROM orders o
            JOIN order_items oi ON o.order_id = oi.order_id
            WHERE oi.quantity > 0
            GROUP BY yr, mo
        )
        SELECT yr AS year, mo AS month, revenue,
               LAG(revenue) OVER (PARTITION BY mo ORDER BY yr) AS prev_year_revenue,
               CASE
                   WHEN LAG(revenue) OVER (PARTITION BY mo ORDER BY yr) IS NULL THEN NULL
                   ELSE ROUND(100.0 * (revenue - LAG(revenue) OVER (PARTITION BY mo ORDER BY yr))
                        / NULLIF(LAG(revenue) OVER (PARTITION BY mo ORDER BY yr), 0), 1)
               END AS yoy_growth_percent
        FROM yearly
        ORDER BY yr, mo
        LIMIT 20
        """)

    run(conn, "Q13 – First & Last Purchased Category per Customer (Category Shift)",
        """
        WITH cat_orders AS (
            SELECT o.customer_id, p.category, o.order_date,
                   ROW_NUMBER() OVER (PARTITION BY o.customer_id ORDER BY o.order_date ASC)  AS rn_first,
                   ROW_NUMBER() OVER (PARTITION BY o.customer_id ORDER BY o.order_date DESC) AS rn_last
            FROM orders o
            JOIN order_items oi ON o.order_id    = oi.order_id
            JOIN products    p  ON oi.product_id = p.product_id
            WHERE o.customer_id <> 'UNKNOWN'
        ),
        first_last AS (
            SELECT customer_id,
                   MAX(CASE WHEN rn_first = 1 THEN category END) AS first_category,
                   MAX(CASE WHEN rn_last  = 1 THEN category END) AS last_category
            FROM cat_orders
            GROUP BY customer_id
        )
        SELECT customer_id, first_category, last_category,
               CASE WHEN first_category <> last_category THEN 'Yes' ELSE 'No' END AS category_shift
        FROM first_last
        LIMIT 20
        """)

    run(conn, "Q14 – Cumulative Distribution: Revenue from Top N% of Customers",
        """
        WITH ltv AS (
            SELECT o.customer_id,
                   SUM(oi.quantity * oi.unit_price * (1.0 - oi.discount_percent/100.0)) AS revenue
            FROM orders o
            JOIN order_items oi ON o.order_id = oi.order_id
            WHERE oi.quantity > 0 AND o.customer_id <> 'UNKNOWN'
            GROUP BY o.customer_id
        ),
        ranked AS (
            SELECT customer_id, revenue,
                   CUME_DIST() OVER (ORDER BY revenue DESC) AS cum_pct_customers,
                   SUM(revenue) OVER (ORDER BY revenue DESC ROWS UNBOUNDED PRECEDING)
                       / SUM(revenue) OVER () AS cum_pct_revenue
            FROM ltv
        )
        SELECT customer_id,
               ROUND(revenue, 2)              AS revenue,
               ROUND(cum_pct_customers * 100, 1) AS cumulative_percent_customers,
               ROUND(cum_pct_revenue   * 100, 1) AS cumulative_revenue_percent
        FROM ranked
        ORDER BY cum_pct_customers
        LIMIT 20
        """)

    run(conn, "Q15 – Cohort Analysis by Registration Month (Retention Months 0-3)",
        """
        WITH cohort AS (
            SELECT c.customer_id,
                   strftime('%Y-%m', c.registration_date) AS cohort_month
            FROM customers c
        ),
        activity AS (
            SELECT o.customer_id,
                   strftime('%Y-%m', o.order_date) AS activity_month
            FROM orders o
            WHERE o.customer_id <> 'UNKNOWN'
            GROUP BY o.customer_id, activity_month
        ),
        cohort_size AS (
            SELECT cohort_month, COUNT(*) AS cohort_customers
            FROM cohort GROUP BY cohort_month
        ),
        retention_raw AS (
            SELECT co.cohort_month,
                   (
                     (CAST(substr(ac.activity_month,1,4) AS INT) - CAST(substr(co.cohort_month,1,4) AS INT)) * 12
                     + CAST(substr(ac.activity_month,6,2) AS INT) - CAST(substr(co.cohort_month,6,2) AS INT)
                   ) AS months_since_signup,
                   COUNT(DISTINCT ac.customer_id) AS active_customers
            FROM cohort co
            JOIN activity ac ON co.customer_id = ac.customer_id
            GROUP BY co.cohort_month, months_since_signup
        )
        SELECT r.cohort_month, cs.cohort_customers, r.months_since_signup,
               r.active_customers,
               ROUND(100.0 * r.active_customers / cs.cohort_customers, 1) AS retention_pct
        FROM retention_raw r
        JOIN cohort_size cs ON r.cohort_month = cs.cohort_month
        WHERE r.months_since_signup BETWEEN 0 AND 3
        ORDER BY r.cohort_month, r.months_since_signup
        LIMIT 20
        """)

    run(conn, "Q16 – Market Basket: Products Frequently Bought Together (Self-Join)",
        """
        SELECT p1.product_name AS product_a,
               p2.product_name AS product_b,
               COUNT(*)         AS times_bought_together
        FROM order_items a
        JOIN order_items b  ON a.order_id = b.order_id AND a.product_id < b.product_id
        JOIN products p1 ON a.product_id = p1.product_id
        JOIN products p2 ON b.product_id = p2.product_id
        GROUP BY a.product_id, b.product_id
        ORDER BY times_bought_together DESC
        LIMIT 10
        """)

    conn.close()
    print(f"\n{'=' * 70}")
    print("  All 16 queries executed successfully.")
    print(f"{'=' * 70}\n")


if __name__ == "__main__":
    main()
