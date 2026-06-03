"""
mark_contacted.py — stamp contacted=1 in leads.db for every row in a CSV.

Usage:
  python3 mark_contacted.py outputs/03-06-2026-phase1.csv
  python3 mark_contacted.py outputs/03-06-2026-test.csv
"""

import csv, sqlite3, sys
from pathlib import Path

DB_PATH = Path(__file__).parent / "leads.db"


def mark_contacted(csv_path: Path) -> int:
    """Mark all leads in csv_path as contacted. Returns number of rows updated."""
    with open(csv_path, encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    conn = sqlite3.connect(DB_PATH)
    count = 0
    try:
        for row in rows:
            company = (row.get("company") or "").strip()
            source = (row.get("source") or "").strip()
            if not company:
                continue
            cursor = conn.execute(
                "UPDATE leads SET contacted=1 WHERE company=? AND source=?",
                (company, source),
            )
            count += cursor.rowcount
        conn.commit()
    finally:
        conn.close()
    return count


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 mark_contacted.py <csv_file>")
        sys.exit(1)
    path = Path(sys.argv[1])
    if not path.exists():
        print(f"File not found: {path}")
        sys.exit(1)
    n = mark_contacted(path)
    print(f"Marked {n} leads as contacted in {DB_PATH.name}")


if __name__ == "__main__":
    main()
