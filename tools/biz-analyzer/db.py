import csv, json, os, sqlite3
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), "leads.db")
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "outputs")


def output_path(ext: str) -> str:
    return os.path.join(OUTPUT_DIR, datetime.now().strftime("%d-%m-%Y") + f".{ext}")


def load_seen() -> set:
    path = output_path("json")
    if not os.path.exists(path):
        return set()
    with open(path, encoding="utf-8") as f:
        try:
            data = json.load(f)
        except (json.JSONDecodeError, ValueError):
            return set()
    return {(r.get("company", ""), r.get("source", "")) for r in data}


def append_lead(lead: dict):
    _sqlite_insert(lead)
    _json_append(lead)


def _sqlite_insert(lead: dict):
    conn = sqlite3.connect(DB_PATH)
    try:
        conn.execute(
            """INSERT OR IGNORE INTO leads
               (source, company, sector, sector_score, city, headcount, founded_year,
                phone, email, contacts, domain, has_website, composite_score, created_at)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                lead.get("source"), lead.get("company"), lead.get("sector"),
                lead.get("sector_score"), lead.get("city"), lead.get("headcount"),
                lead.get("founded_year"), lead.get("phone"), lead.get("email"),
                json.dumps(lead["contacts"], ensure_ascii=False)
                if lead.get("contacts") is not None else None,
                lead.get("domain"), lead.get("has_website"),
                lead.get("composite_score"),
                lead.get("created_at", datetime.now().isoformat()),
            ),
        )
        conn.commit()
    finally:
        conn.close()


def _json_append(lead: dict):
    path = output_path("json")
    existing = []
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            try:
                existing = json.load(f)
            except (json.JSONDecodeError, ValueError):
                existing = []
    key = (lead.get("company", ""), lead.get("source", ""))
    if any((r.get("company", ""), r.get("source", "")) == key for r in existing):
        return
    existing.append(lead)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(existing, f, ensure_ascii=False, indent=2)


def export_csv() -> str:
    json_path = output_path("json")
    csv_path = output_path("csv")
    if not os.path.exists(json_path):
        return csv_path
    with open(json_path, encoding="utf-8") as f:
        try:
            data = json.load(f)
        except (json.JSONDecodeError, ValueError):
            return csv_path
    if not data:
        return csv_path

    data.sort(key=lambda r: r.get("composite_score", 0), reverse=True)

    flat = []
    for row in data:
        r = {k: v for k, v in row.items() if k != "contacts"}
        contacts = row.get("contacts") or []
        for i in range(3):
            c = contacts[i] if i < len(contacts) else {}
            r[f"contact_{i + 1}_name"] = c.get("name", "")
            r[f"contact_{i + 1}_title"] = c.get("title", "")
            r[f"contact_{i + 1}_linkedin"] = c.get("linkedin") or ""
        flat.append(r)

    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=flat[0].keys())
        w.writeheader()
        w.writerows(flat)

    return csv_path


def stats() -> dict:
    conn = sqlite3.connect(DB_PATH)
    try:
        total = conn.execute("SELECT COUNT(*) FROM leads").fetchone()[0]
        with_email = conn.execute(
            "SELECT COUNT(*) FROM leads WHERE email IS NOT NULL"
        ).fetchone()[0]
        by_sector = conn.execute(
            "SELECT sector, COUNT(*) FROM leads GROUP BY sector"
        ).fetchall()
        return {"total": total, "with_email": with_email, "by_sector": dict(by_sector)}
    finally:
        conn.close()
