"""
cleanup.py — filter today's CSV down to actionable outreach leads.

Removes:
  - has_website=1 (they already have a site — not our target)
  - No email AND no contact_1_name (nothing to reach them with)
  - composite_score == 0 (fintech or unscored)

Writes: outputs/DD-MM-YYYY-clean.csv
"""

import csv, json, sys
from datetime import datetime
from pathlib import Path

OUTPUT_DIR = Path(__file__).parent / "outputs"


def main():
    today = datetime.now().strftime("%d-%m-%Y")
    src = OUTPUT_DIR / f"{today}.json"
    if not src.exists():
        print(f"No data file found: {src}")
        sys.exit(1)

    with open(src, encoding="utf-8") as f:
        data = json.load(f)

    before = len(data)

    cleaned = []
    for row in data:
        sector = row.get("sector", "")
        # Mining: keep regardless of has_website — pitch is industry software, not basic sites
        if sector != "mining":
            if row.get("has_website") == 1:
                continue
        # Skip if no way to reach them at all
        if not row.get("email") and not row.get("contacts"):
            continue
        # Skip zero-score leads
        if row.get("composite_score", 0) == 0:
            continue
        cleaned.append(row)

    after = len(cleaned)
    removed = before - after
    print(f"Before: {before}  After: {after}  Removed: {removed}")
    print(f"  - has website: {sum(1 for r in data if r.get('has_website')==1)}")
    print(f"  - no contact:  {sum(1 for r in data if not r.get('email') and not r.get('contacts'))}")
    print(f"  - score=0:     {sum(1 for r in data if r.get('composite_score',0)==0)}")

    if not cleaned:
        print("No leads remain after cleanup.")
        return

    # Sort by composite_score DESC
    cleaned.sort(key=lambda r: r.get("composite_score", 0), reverse=True)

    # Flatten contacts → contact_N_* columns
    flat = []
    for row in cleaned:
        r = {k: v for k, v in row.items() if k != "contacts"}
        contacts = row.get("contacts") or []
        for i in range(3):
            c = contacts[i] if i < len(contacts) else {}
            r[f"contact_{i+1}_name"] = c.get("name", "")
            r[f"contact_{i+1}_title"] = c.get("title", "")
            r[f"contact_{i+1}_linkedin"] = c.get("linkedin") or ""
        flat.append(r)

    out = OUTPUT_DIR / f"{today}-clean.csv"
    with open(out, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=flat[0].keys())
        w.writeheader()
        w.writerows(flat)

    print(f"\nClean CSV: {out}")
    print(f"With email: {sum(1 for r in cleaned if r.get('email'))}")
    print(f"No email, has contact: {sum(1 for r in cleaned if not r.get('email') and r.get('contacts'))}")


if __name__ == "__main__":
    main()
