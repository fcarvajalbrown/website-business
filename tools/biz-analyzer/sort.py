"""
sort.py — re-sort any CSV by composite_score DESC.

Usage:
  python3 sort.py                         # sorts today's clean CSV
  python3 sort.py outputs/03-06-2026.csv  # sort any CSV

Writes: same filename with -sorted suffix.
"""

import csv, sys
from pathlib import Path
from datetime import datetime

OUTPUT_DIR = Path(__file__).parent / "outputs"


def sort_csv(src: Path) -> Path:
    with open(src, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    if not rows:
        print("Empty file.")
        sys.exit(1)

    rows.sort(key=lambda r: int(r.get("composite_score") or 0), reverse=True)

    out = src.with_stem(src.stem + "-sorted")
    with open(out, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=rows[0].keys())
        w.writeheader()
        w.writerows(rows)

    return out


def main():
    if len(sys.argv) > 1:
        src = Path(sys.argv[1])
    else:
        today = datetime.now().strftime("%d-%m-%Y")
        # prefer clean CSV if it exists
        clean = OUTPUT_DIR / f"{today}-clean.csv"
        raw = OUTPUT_DIR / f"{today}.csv"
        src = clean if clean.exists() else raw

    if not src.exists():
        print(f"File not found: {src}")
        sys.exit(1)

    out = sort_csv(src)
    rows_with_email = 0
    with open(out, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if row.get("email"):
                rows_with_email += 1

    total = sum(1 for _ in csv.DictReader(open(out, encoding="utf-8")))
    print(f"Sorted {total} rows → {out}")
    print(f"With email: {rows_with_email}")


if __name__ == "__main__":
    main()
