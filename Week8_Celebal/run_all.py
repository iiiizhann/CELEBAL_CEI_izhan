#!/usr/bin/env python3

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
def run(cmd: list[str]) ->None:
    print(f"\n>>{''.join(cmd)}")
    r = subprocess.run(cmd, cwd=ROOT)
    if r.returncode != 0:
        sys.exit(r.returncode)

def main() -> None:
    py = sys.executable
    run([py, "scripts/generate_data.py"])
    run([py, "scriipt/clean_data.py"])
    run([py, "scripts/load_db.py"])

    print("\n   Sample reports   ")
    for report in ["overview", "revenue","top_customers", "categories", "aov_segments"]:
        run([py, "scripts/report_cli.py", "--report", report])

        print("\n Pipeline Finished...")
        print("Try more report...")
        print("python scripts/report_cli.py --report retention")
        print("python scripts/report_cli.py --report rfm --limit 20 ")
        print("python scripts/report_cli.py --report churn --min-ltv 500")

    if __name__ == "__main__":
        main()
