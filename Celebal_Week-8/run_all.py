#!/usr/bin/env python3
"""run_all.py – Full pipeline runner.

Executes the complete project pipeline in order:
  1. generate_data.py  – create raw CSVs
  2. clean_data.py     – clean + validate, save cleaned CSVs & report
  3. load_db.py        – load cleaned data into SQLite
  4. test_edge_cases.py (optional, pass --test flag)

Usage:
  python run_all.py           # runs generate → clean → load
  python run_all.py --test    # also runs edge-case tests
  python run_all.py --report monthly --from 2025-01-01 --to 2025-06-30
"""

import subprocess
import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent / "scripts"


def run(script: str, extra_args: list = None):
    args = [sys.executable, str(SCRIPTS / script)] + (extra_args or [])
    print(f"\n>>> Running: {' '.join(args)}\n")
    result = subprocess.run(args, check=False)
    if result.returncode != 0:
        print(f"ERROR: {script} failed (exit {result.returncode})", file=sys.stderr)
        sys.exit(result.returncode)


def main():
    import argparse
    parser = argparse.ArgumentParser(description="E-Commerce Analytics – Full Pipeline")
    parser.add_argument("--test",   action="store_true", help="Also run edge-case tests")
    parser.add_argument("--report", choices=["daily", "weekly", "monthly"],
                        help="Run CLI report after pipeline")
    parser.add_argument("--from",   dest="date_from", help="Start date YYYY-MM-DD for report")
    parser.add_argument("--to",     dest="date_to",   help="End date   YYYY-MM-DD for report")
    args = parser.parse_args()

    run("generate_data.py")
    run("clean_data.py")
    run("load_db.py")

    if args.test:
        run("test_edge_cases.py")

    if args.report:
        report_args = ["--report", args.report]
        if args.date_from:
            report_args += ["--from", args.date_from]
        if args.date_to:
            report_args += ["--to", args.date_to]
        run("report_cli.py", report_args)

    print("\n[OK] Pipeline complete.")


if __name__ == "__main__":
    main()
