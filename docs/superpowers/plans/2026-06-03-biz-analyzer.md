# biz-analyzer v1 — Scrape Pipeline Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a crash-safe Chilean SME lead scraper that writes a sorted CSV with emails and key contacts for same-day outreach.

**Architecture:** Scaffold (scorer → db → cli) built and unit-tested first with no network dependency. Scrapers added one source at a time — inspect real HTML before writing selectors — amarillas end-to-end first, then direcmin, then pymesdechile.

**Tech Stack:** Python 3.13 in `.venv`, httpx, BeautifulSoup4/lxml, SQLite, JSON (crash-safe append), pytest. Playwright as selective fallback only.

---

## File map

| File | Role |
|------|------|
| `scorer.py` | Sector priority + composite score — no deps |
| `db.py` | SQLite INSERT + JSON append per-record + CSV export |
| `cli.py` | argparse: scrape / stats / export + SIGINT handler |
| `sources/__init__.py` | PRIORITY_ROLES, email regex, shared parsing helpers |
| `sources/amarillas.py` | httpx scraper — amarillas.emol.com |
| `sources/direcmin.py` | httpx scraper — direcmin.com |
| `sources/pymesdechile.py` | httpx scraper — pymesdechile.cl |
| `tests/conftest.py` | sys.path fix so tests import from project root |
| `tests/test_scorer.py` | Unit tests for scorer |
| `tests/test_db.py` | Integration tests for db (temp files) |
| `tests/test_sources.py` | Unit tests for email/contact parsing helpers |
| `setup.sh` | Add beautifulsoup4, lxml, pytest; add UNIQUE index |
| `scrape-today.sh` | Replace google_maps loop with fast sources + sector order |

All paths relative to `tools/biz-analyzer/`.

---

### Task 1: Dependencies + test infrastructure

**Files:**
- Modify: `tools/biz-analyzer/setup.sh`
- Create: `tools/biz-analyzer/tests/__init__.py`
- Create: `tools/biz-analyzer/tests/conftest.py`

- [ ] **Step 1: Update setup.sh — add deps and UNIQUE index**

In `setup.sh`, change the pip install line:
```bash
pip install --quiet httpx rich playwright beautifulsoup4 lxml pytest
```

Also extend the `executescript` string to add the UNIQUE index after the `CREATE TABLE` block:
```python
conn.executescript("""
CREATE TABLE IF NOT EXISTS leads (
  id INTEGER PRIMARY KEY,
  source TEXT,
  company TEXT,
  sector TEXT,
  sector_score INTEGER,
  city TEXT,
  headcount TEXT,
  founded_year INTEGER,
  phone TEXT,
  email TEXT,
  contacts TEXT,
  domain TEXT,
  has_website INTEGER,
  composite_score INTEGER,
  approved INTEGER DEFAULT 0,
  contacted INTEGER DEFAULT 0,
  created_at TEXT DEFAULT (datetime('now'))
);
CREATE UNIQUE INDEX IF NOT EXISTS idx_company_source ON leads(company, source);
""")
```

- [ ] **Step 2: Run setup**
```bash
cd tools/biz-analyzer && bash setup.sh
```
Expected: "DB initialized at leads.db" with no pip errors.

- [ ] **Step 3: Create test files**

`tests/__init__.py` — empty file.

`tests/conftest.py`:
```python
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
```

- [ ] **Step 4: Verify pytest works**
```bash
cd tools/biz-analyzer && .venv/bin/pytest tests/ -v
```
Expected: "no tests ran" or "0 passed" — no import errors.

---

### Task 2: scorer.py

**Files:**
- Create: `tools/biz-analyzer/tests/test_scorer.py`
- Create: `tools/biz-analyzer/scorer.py`

- [ ] **Step 1: Write failing tests**

`tests/test_scorer.py`:
```python
from scorer import score

def base(**kw):
    return {"source": "test", "company": "Acme", "sector": "saas",
            "city": None, "headcount": None, "founded_year": None,
            "has_website": 1, **kw}

def test_saas_base():
    assert score(base())["composite_score"] == 4

def test_healthtech_base():
    assert score(base(sector="healthtech"))["composite_score"] == 3

def test_agtech_base():
    assert score(base(sector="agtech"))["composite_score"] == 2

def test_retail_base():
    assert score(base(sector="retail"))["composite_score"] == 1

def test_location_las_condes():
    assert score(base(city="Las Condes"))["composite_score"] == 5

def test_location_providencia():
    assert score(base(city="Providencia"))["composite_score"] == 5

def test_location_vitacura():
    assert score(base(city="Vitacura"))["composite_score"] == 5

def test_no_location_boost_santiago():
    assert score(base(city="Santiago"))["composite_score"] == 4

def test_headcount_1_5():
    assert score(base(headcount="1-5"))["composite_score"] == 6

def test_headcount_large_no_boost():
    assert score(base(headcount="50-100"))["composite_score"] == 4

def test_founded_recent():
    assert score(base(founded_year=2025))["composite_score"] == 6

def test_founded_old_no_boost():
    assert score(base(founded_year=2020))["composite_score"] == 4

def test_no_website_boost():
    assert score(base(has_website=0))["composite_score"] == 7

def test_max_score():
    lead = base(city="Las Condes", headcount="1-5", founded_year=2025, has_website=0)
    assert score(lead)["composite_score"] == 12

def test_mutates_in_place():
    lead = base()
    result = score(lead)
    assert result is lead
    assert "composite_score" in lead
```

- [ ] **Step 2: Run — expect ImportError**
```bash
cd tools/biz-analyzer && .venv/bin/pytest tests/test_scorer.py -v
```

- [ ] **Step 3: Implement scorer.py**

```python
SECTOR_SCORES = {
    "saas": 4,
    "healthtech": 3,
    "agtech": 2,
    "retail": 1,
    "fintech": 0,
}

_LOCATION_BOOST = {"las condes", "providencia", "vitacura"}
_SMALL_HEADCOUNTS = {"1-5", "1 a 5", "1-10", "1 a 10"}


def score(lead: dict) -> dict:
    s = SECTOR_SCORES.get((lead.get("sector") or "").lower(), 0)

    city = (lead.get("city") or "").lower()
    if any(loc in city for loc in _LOCATION_BOOST):
        s += 1

    hc = (lead.get("headcount") or "").strip().lower()
    if hc in _SMALL_HEADCOUNTS or hc.startswith("1-5") or hc.startswith("1 a 5"):
        s += 2

    fy = lead.get("founded_year")
    if fy and int(fy) >= 2024:
        s += 2

    if lead.get("has_website") == 0:
        s += 3

    lead["composite_score"] = s
    return lead
```

- [ ] **Step 4: Run — expect all green**
```bash
cd tools/biz-analyzer && .venv/bin/pytest tests/test_scorer.py -v
```
Expected: 15 tests PASS.

- [ ] **Step 5: Commit**
```bash
cd tools/biz-analyzer && git add scorer.py tests/test_scorer.py tests/__init__.py tests/conftest.py && git commit -m "feat(biz-analyzer): scorer — composite score"
```

---

### Task 3: db.py

**Files:**
- Create: `tools/biz-analyzer/tests/test_db.py`
- Create: `tools/biz-analyzer/db.py`

- [ ] **Step 1: Write failing tests**

`tests/test_db.py`:
```python
import csv, json, os, sqlite3, pytest

@pytest.fixture
def tmp_env(tmp_path, monkeypatch):
    db = tmp_path / "leads.db"
    outputs = tmp_path / "outputs"
    outputs.mkdir()
    conn = sqlite3.connect(str(db))
    conn.executescript("""
        CREATE TABLE leads (
          id INTEGER PRIMARY KEY,
          source TEXT, company TEXT, sector TEXT, sector_score INTEGER,
          city TEXT, headcount TEXT, founded_year INTEGER,
          phone TEXT, email TEXT, contacts TEXT, domain TEXT,
          has_website INTEGER, composite_score INTEGER,
          approved INTEGER DEFAULT 0, contacted INTEGER DEFAULT 0,
          created_at TEXT DEFAULT (datetime('now'))
        );
        CREATE UNIQUE INDEX idx_company_source ON leads(company, source);
    """)
    conn.close()
    monkeypatch.setattr("db.DB_PATH", str(db))
    monkeypatch.setattr("db.OUTPUT_DIR", str(outputs))
    return tmp_path

def sample(**kw):
    return {"source": "amarillas", "company": "TechCo", "sector": "saas",
            "sector_score": 4, "city": "Santiago", "headcount": "1-5",
            "founded_year": 2024, "phone": "+56 2 1234 5678",
            "email": "ceo@techco.cl", "contacts": None,
            "domain": "techco.cl", "has_website": 1, "composite_score": 8, **kw}

def test_append_writes_json(tmp_env):
    import db
    db.append_lead(sample())
    files = list((tmp_env / "outputs").glob("*.json"))
    assert len(files) == 1
    data = json.loads(files[0].read_text())
    assert data[0]["company"] == "TechCo"

def test_append_writes_sqlite(tmp_env):
    import db
    db.append_lead(sample())
    conn = sqlite3.connect(str(tmp_env / "leads.db"))
    row = conn.execute("SELECT company, email FROM leads").fetchone()
    conn.close()
    assert row == ("TechCo", "ceo@techco.cl")

def test_append_deduplicates(tmp_env):
    import db
    db.append_lead(sample())
    db.append_lead(sample())
    conn = sqlite3.connect(str(tmp_env / "leads.db"))
    count = conn.execute("SELECT COUNT(*) FROM leads").fetchone()[0]
    conn.close()
    assert count == 1

def test_load_seen_empty(tmp_env):
    import db
    assert db.load_seen() == set()

def test_load_seen_after_append(tmp_env):
    import db
    db.append_lead(sample())
    assert ("TechCo", "amarillas") in db.load_seen()

def test_contacts_serialized_as_json(tmp_env):
    import db
    contacts = [{"name": "María", "title": "CEO", "linkedin": None}]
    db.append_lead(sample(email=None, contacts=contacts))
    conn = sqlite3.connect(str(tmp_env / "leads.db"))
    row = conn.execute("SELECT contacts FROM leads").fetchone()
    conn.close()
    assert json.loads(row[0]) == contacts

def test_export_csv_sorted_by_score(tmp_env):
    import db
    db.append_lead(sample(company="Low", composite_score=2))
    db.append_lead(sample(company="High", source="direcmin", composite_score=9))
    csv_path = db.export_csv()
    rows = list(csv.DictReader(open(csv_path)))
    assert rows[0]["company"] == "High"
    assert rows[1]["company"] == "Low"

def test_export_csv_flattens_contacts(tmp_env):
    import db
    contacts = [
        {"name": "Ana López", "title": "CEO", "linkedin": "https://linkedin.com/in/ana"},
        {"name": "Pedro Cruz", "title": "CTO", "linkedin": None},
    ]
    db.append_lead(sample(email=None, contacts=contacts))
    content = open(db.export_csv()).read()
    assert "Ana López" in content
    assert "contact_1_name" in content
    assert "contact_2_name" in content
    assert "contact_3_name" in content

def test_stats(tmp_env):
    import db
    db.append_lead(sample())
    db.append_lead(sample(company="NoEmail", source="direcmin", email=None))
    s = db.stats()
    assert s["total"] == 2
    assert s["with_email"] == 1
```

- [ ] **Step 2: Run — expect ImportError**
```bash
cd tools/biz-analyzer && .venv/bin/pytest tests/test_db.py -v
```

- [ ] **Step 3: Implement db.py**

```python
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
```

- [ ] **Step 4: Run — expect all green**
```bash
cd tools/biz-analyzer && .venv/bin/pytest tests/test_db.py -v
```
Expected: 9 tests PASS.

- [ ] **Step 5: Commit**
```bash
cd tools/biz-analyzer && git add db.py tests/test_db.py && git commit -m "feat(biz-analyzer): db — crash-safe JSON + SQLite + CSV export"
```

---

### Task 4: sources/__init__.py — shared parsing utilities

**Files:**
- Create: `tools/biz-analyzer/sources/__init__.py`
- Create: `tools/biz-analyzer/tests/test_sources.py`

- [ ] **Step 1: Write failing tests**

`tests/test_sources.py`:
```python
from sources import _decode_email, _extract_email_from_html, _extract_contacts, PRIORITY_ROLES
from bs4 import BeautifulSoup

def soup(html):
    return BeautifulSoup(html, "lxml")

def test_mailto_link():
    assert _extract_email_from_html(soup('<a href="mailto:ceo@empresa.cl">contacto</a>')) == "ceo@empresa.cl"

def test_data_email_attr():
    assert _extract_email_from_html(soup('<span data-email="info[at]empresa[dot]cl"></span>')) == "info@empresa.cl"

def test_obfuscated_text():
    assert _extract_email_from_html(soup('<p>hola [at] empresa [dot] cl</p>')) == "hola@empresa.cl"

def test_plain_email_in_text():
    assert _extract_email_from_html(soup('<p>Escríbenos: info@empresa.cl</p>')) == "info@empresa.cl"

def test_no_email_returns_none():
    assert _extract_email_from_html(soup('<p>Sin contacto</p>')) is None

def test_decode_bracket_at():
    assert _decode_email("info[at]empresa[dot]cl") == "info@empresa.cl"

def test_decode_spaced_at():
    assert _decode_email("info at empresa dot cl") == "info@empresa.cl"

def test_priority_roles_has_fundador():
    assert "fundador" in PRIORITY_ROLES

def test_priority_roles_has_fundadora():
    assert "fundadora" in PRIORITY_ROLES

def test_priority_roles_has_ceo():
    assert "ceo" in PRIORITY_ROLES

def test_priority_roles_has_representante_legal():
    assert "representante legal" in PRIORITY_ROLES

def test_extract_contacts_finds_ceo():
    html = "<div><p>María González</p><p>CEO</p><p>Pedro Ruiz</p><p>Vendedor</p></div>"
    contacts = _extract_contacts(soup(html))
    assert len(contacts) == 1
    assert contacts[0]["name"] == "María González"
    assert contacts[0]["title"] == "CEO"

def test_extract_contacts_max_3():
    html = "".join(f"<p>Person {i}</p><p>CEO</p>" for i in range(10))
    assert len(_extract_contacts(soup(html))) <= 3

def test_extract_contacts_skips_non_priority():
    assert _extract_contacts(soup("<p>Ana Martínez</p><p>Vendedora</p>")) == []

def test_extract_contacts_linkedin():
    html = "<p>Ana López</p><p>Fundadora</p><p>https://linkedin.com/in/analopez</p>"
    contacts = _extract_contacts(soup(html))
    assert contacts[0]["linkedin"] == "https://linkedin.com/in/analopez"
```

- [ ] **Step 2: Run — expect ImportError**
```bash
cd tools/biz-analyzer && .venv/bin/pytest tests/test_sources.py -v
```

- [ ] **Step 3: Implement sources/__init__.py**

```python
import re
from html import unescape
from bs4 import BeautifulSoup

PRIORITY_ROLES = [
    "ceo", "chief executive officer",
    "director ejecutivo", "directora ejecutiva",
    "gerente general", "gerente",
    "presidente", "presidenta", "presidente ejecutivo",
    "director general", "directora general",
    "director", "directora",
    "dueño", "dueña", "propietario", "propietaria",
    "fundador", "fundadora",
    "co-fundador", "co-fundadora", "cofundador", "cofundadora",
    "founder", "co-founder",
    "socio principal", "socia principal",
    "socio gerente", "socia gerente",
    "socio fundador", "socia fundadora",
    "representante legal",
    "apoderado", "apoderada",
    "cto", "chief technology officer",
    "owner", "emprendedor", "emprendedora",
]

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "es-CL,es;q=0.9",
}

_EMAIL_RE = re.compile(r'[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}')


def _decode_email(text: str) -> str | None:
    text = unescape(text)
    text = (
        text.replace("[at]", "@").replace("[dot]", ".")
            .replace(" [at] ", "@").replace(" [dot] ", ".")
            .replace(" at ", "@").replace(" dot ", ".")
    )
    m = _EMAIL_RE.search(text)
    return m.group() if m else None


def _extract_email_from_html(soup: BeautifulSoup) -> str | None:
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if href.lower().startswith("mailto:"):
            return href[7:].split("?")[0].strip()
    for el in soup.find_all(attrs={"data-email": True}):
        e = _decode_email(el["data-email"])
        if e:
            return e
    return _decode_email(soup.get_text(" "))


def _role_priority(title: str) -> int:
    t = title.lower()
    for i, role in enumerate(PRIORITY_ROLES):
        if role in t:
            return i
    return len(PRIORITY_ROLES)


def _extract_contacts(soup: BeautifulSoup) -> list[dict]:
    lines = [l.strip() for l in soup.get_text("\n").splitlines() if l.strip()]
    seen: set[str] = set()
    candidates = []

    for i, line in enumerate(lines):
        line_lower = line.lower()
        for role in PRIORITY_ROLES:
            if role in line_lower:
                name = lines[i - 1] if i > 0 else None
                if (
                    name
                    and 1 < len(name.split()) <= 5
                    and not re.search(r'\d', name)
                    and name not in seen
                ):
                    linkedin = None
                    for j in range(max(0, i - 3), min(len(lines), i + 4)):
                        if "linkedin.com/in/" in lines[j].lower():
                            linkedin = lines[j].strip()
                            break
                    candidates.append({
                        "name": name, "title": line, "linkedin": linkedin,
                        "_p": _role_priority(line),
                    })
                    seen.add(name)
                break

    candidates.sort(key=lambda c: c["_p"])
    return [{"name": c["name"], "title": c["title"], "linkedin": c["linkedin"]}
            for c in candidates[:3]]


def fetch_website_email(domain: str) -> str | None:
    import httpx
    if not domain:
        return None
    for path in ["/contacto", "/contactenos", "/about", "/nosotros", "/contact"]:
        try:
            r = httpx.get(
                f"https://{domain}{path}", timeout=8,
                follow_redirects=True, headers=HEADERS,
            )
            if r.status_code == 200:
                from bs4 import BeautifulSoup as BS
                email = _extract_email_from_html(BS(r.text, "lxml"))
                if email:
                    return email
        except Exception:
            pass
    return None
```

- [ ] **Step 4: Run — expect all green**
```bash
cd tools/biz-analyzer && .venv/bin/pytest tests/test_sources.py -v
```
Expected: 15 tests PASS.

- [ ] **Step 5: Commit**
```bash
cd tools/biz-analyzer && git add sources/__init__.py tests/test_sources.py && git commit -m "feat(biz-analyzer): shared email/contact parsing + 30+ Chilean role variants"
```

---

### Task 5: cli.py

**Files:**
- Create: `tools/biz-analyzer/cli.py`

- [ ] **Step 1: Implement cli.py**

```python
import argparse, importlib, signal
from db import append_lead, export_csv, load_seen, stats as db_stats
from scorer import score

_stop = False

def _handle_sigint(sig, frame):
    global _stop
    print("\nInterrupt — finishing current record then stopping.", flush=True)
    _stop = True

signal.signal(signal.SIGINT, _handle_sigint)

SOURCE_MAP = {
    "amarillas": "sources.amarillas",
    "direcmin": "sources.direcmin",
    "pymesdechile": "sources.pymesdechile",
}

SECTORS_IN_ORDER = ["saas", "healthtech", "agtech", "retail"]


def cmd_scrape(args):
    sources = list(SOURCE_MAP.keys()) if args.all_sources else [args.source]
    sectors = SECTORS_IN_ORDER if args.all_sectors else [args.sector]
    seen = load_seen()
    count = 0

    for src_name in sources:
        mod = importlib.import_module(SOURCE_MAP[src_name])
        for sector in sectors:
            print(f"[{src_name}] {sector}...", flush=True)
            for lead in mod.scrape(sector, city=args.city):
                if _stop:
                    break
                key = (lead.get("company", ""), lead.get("source", ""))
                if key in seen:
                    continue
                seen.add(key)
                lead = score(lead)
                if lead["composite_score"] == 0:
                    continue
                append_lead(lead)
                count += 1
                tag = lead.get("email") or "no-email"
                print(f"  + [{lead['composite_score']}] {lead['company']} — {tag}", flush=True)
            if _stop:
                break
        if _stop:
            break

    print(f"\nSaved {count} new leads.")
    csv_path = export_csv()
    print(f"CSV: {csv_path}")


def cmd_stats(args):
    s = db_stats()
    print(f"Total: {s['total']}  With email: {s['with_email']}")
    for sector, n in sorted(s["by_sector"].items()):
        print(f"  {sector}: {n}")


def cmd_export(args):
    print(f"Exported: {export_csv()}")


def main():
    parser = argparse.ArgumentParser(description="biz-analyzer — Chilean SME lead scraper")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("scrape")
    g1 = p.add_mutually_exclusive_group(required=True)
    g1.add_argument("--source", choices=list(SOURCE_MAP.keys()))
    g1.add_argument("--all-sources", action="store_true")
    g2 = p.add_mutually_exclusive_group(required=True)
    g2.add_argument("--sector", choices=SECTORS_IN_ORDER)
    g2.add_argument("--all-sectors", action="store_true")
    p.add_argument("--city", default=None)
    p.set_defaults(func=cmd_scrape)

    q = sub.add_parser("stats")
    q.set_defaults(func=cmd_stats)

    e = sub.add_parser("export")
    e.set_defaults(func=cmd_export)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Smoke — stats on empty DB**
```bash
cd tools/biz-analyzer && .venv/bin/python cli.py stats
```
Expected:
```
Total: 0  With email: 0
```

- [ ] **Step 3: Smoke — export on empty DB**
```bash
cd tools/biz-analyzer && .venv/bin/python cli.py export
```
Expected: "Exported: outputs/DD-MM-YYYY.csv" with no error.

- [ ] **Step 4: Commit**
```bash
cd tools/biz-analyzer && git add cli.py && git commit -m "feat(biz-analyzer): cli — scrape/stats/export + SIGINT"
```

---

### Task 6: sources/amarillas.py — inspect → parse → scrape

**Files:**
- Create: `tools/biz-analyzer/sources/amarillas.py`

This task inspects the live site first. CSS selectors marked `ADJUST AFTER INSPECTION` must be updated based on real HTML output from Step 1.

- [ ] **Step 1: Inspect listing page structure**
```bash
cd tools/biz-analyzer && .venv/bin/python3 - <<'EOF'
import httpx
from bs4 import BeautifulSoup

headers = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "es-CL,es;q=0.9",
}
r = httpx.get("https://amarillas.emol.com/buscar?q=software", headers=headers, follow_redirects=True, timeout=15)
print("Status:", r.status_code, "URL:", r.url)
soup = BeautifulSoup(r.text, "lxml")
print(soup.body.prettify()[:4000] if soup.body else r.text[:4000])
EOF
```
Note the CSS selector for:
- A single listing card (the repeating container element)
- Company name inside a card
- Phone, email/mailto link, website link, city
- "Next page" link

- [ ] **Step 2: Inspect pagination**
```bash
cd tools/biz-analyzer && .venv/bin/python3 - <<'EOF'
import httpx
from bs4 import BeautifulSoup

headers = {"User-Agent": "Mozilla/5.0 Chrome/120.0.0.0 Safari/537.36"}
r = httpx.get("https://amarillas.emol.com/buscar?q=software", headers=headers, follow_redirects=True, timeout=15)
soup = BeautifulSoup(r.text, "lxml")
for a in soup.find_all("a", href=True):
    h = a["href"]
    if any(x in h.lower() for x in ["page", "pagina", "p=", "siguiente"]):
        print(repr(a)[:200])
EOF
```
Note the pagination URL pattern and update `NEXT_SELECTOR` below.

- [ ] **Step 3: Implement sources/amarillas.py**

Replace `ADJUST AFTER INSPECTION` selectors with what you found in Steps 1–2.

```python
import httpx
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urljoin
from sources import (
    HEADERS, _extract_email_from_html, _extract_contacts, fetch_website_email,
)

BASE_URL = "https://amarillas.emol.com"
SEARCH_PATH = "/buscar"

SECTOR_KEYWORDS = {
    "saas": ["software", "tecnología", "plataforma digital"],
    "healthtech": ["salud", "telemedicina", "clínica digital"],
    "agtech": ["agricultura", "ganaderia", "campo"],
    "retail": ["tienda", "comercio", "retail"],
}

# ADJUST AFTER INSPECTION ─────────────────────────────────────────
CARD_SELECTOR = ".listing-item, .business-card, article.result, li.empresa"
NAME_SELECTOR = "h2, h3, .business-name, .nombre"
PHONE_SELECTOR = ".phone, .telefono, [itemprop='telephone']"
WEBSITE_SELECTOR = "a[href^='http']:not([href*='amarillas.emol'])"
CITY_SELECTOR = ".city, .ciudad, [itemprop='addressLocality']"
NEXT_SELECTOR = "a[rel='next'], .pagination a.next, a.siguiente"
# ─────────────────────────────────────────────────────────────────

_SECTOR_SCORES = {"saas": 4, "healthtech": 3, "agtech": 2, "retail": 1}


def _parse_card(card, sector: str) -> dict | None:
    name_el = card.select_one(NAME_SELECTOR)
    if not name_el:
        return None
    company = name_el.get_text(strip=True)
    if not company:
        return None

    phone = None
    el = card.select_one(PHONE_SELECTOR)
    if el:
        phone = el.get_text(strip=True)

    domain = None
    el = card.select_one(WEBSITE_SELECTOR)
    if el and el.get("href", "").startswith("http"):
        domain = urlparse(el["href"]).netloc.lstrip("www.").lower()

    city = None
    el = card.select_one(CITY_SELECTOR)
    if el:
        city = el.get_text(strip=True)

    email = _extract_email_from_html(card)

    contacts = None
    if not email:
        if domain:
            email = fetch_website_email(domain)
        if not email:
            contacts = _extract_contacts(card) or None

    return {
        "source": "amarillas",
        "company": company,
        "sector": sector,
        "sector_score": _SECTOR_SCORES.get(sector, 0),
        "city": city,
        "headcount": None,
        "founded_year": None,
        "phone": phone,
        "email": email,
        "contacts": contacts,
        "domain": domain,
        "has_website": 1 if domain else 0,
    }


def scrape(sector: str, city: str | None = None):
    keywords = SECTOR_KEYWORDS.get(sector, [sector])
    seen: set[str] = set()

    for keyword in keywords:
        url = f"{BASE_URL}{SEARCH_PATH}"
        params: dict = {"q": keyword}
        if city:
            params["ciudad"] = city

        while url:
            try:
                r = httpx.get(url, params=params, timeout=15, headers=HEADERS, follow_redirects=True)
                r.raise_for_status()
                params = {}
            except Exception as e:
                print(f"  [amarillas] error: {e}", flush=True)
                break

            soup = BeautifulSoup(r.text, "lxml")
            cards = soup.select(CARD_SELECTOR)
            if not cards:
                print(f"  [amarillas] no cards at {r.url} — check CARD_SELECTOR", flush=True)
                break

            for card in cards:
                lead = _parse_card(card, sector)
                if not lead or lead["company"] in seen:
                    continue
                seen.add(lead["company"])
                yield lead

            next_el = soup.select_one(NEXT_SELECTOR)
            url = urljoin(str(r.url), next_el["href"]) if next_el and next_el.get("href") else None
```

- [ ] **Step 4: End-to-end test**
```bash
cd tools/biz-analyzer && .venv/bin/python cli.py scrape --source amarillas --sector saas
```
Expected:
- Lines like `+ [8] SomeCo — ceo@someco.cl` or `+ [4] OtherCo — no-email`
- Final: `Saved N new leads. CSV: outputs/DD-MM-YYYY.csv`

If "no cards found": re-run Step 1, identify the correct CARD_SELECTOR, update it, and re-run.
If HTTP 403: add `import time; time.sleep(1)` between page fetches in the `while url:` loop.

- [ ] **Step 5: Inspect CSV**
```bash
cd tools/biz-analyzer && head -n 3 outputs/$(date +%d-%m-%Y).csv
```
Verify header contains `email`, `contact_1_name`, `contact_1_title`, `contact_1_linkedin`, etc.

- [ ] **Step 6: Commit**
```bash
cd tools/biz-analyzer && git add sources/amarillas.py && git commit -m "feat(biz-analyzer): amarillas.emol.com scraper"
```

---

### Task 7: sources/direcmin.py

**Files:**
- Create: `tools/biz-analyzer/sources/direcmin.py`

- [ ] **Step 1: Inspect direcmin.com**
```bash
cd tools/biz-analyzer && .venv/bin/python3 - <<'EOF'
import httpx
from bs4 import BeautifulSoup

headers = {"User-Agent": "Mozilla/5.0 Chrome/120.0.0.0 Safari/537.36", "Accept-Language": "es-CL,es;q=0.9"}
for url in [
    "https://www.direcmin.com/buscar?q=software",
    "https://www.direcmin.com/empresa?rubro=tecnologia",
    "https://direcmin.com/empresas?categoria=tecnologia",
    "https://www.direcmin.com",
]:
    try:
        r = httpx.get(url, headers=headers, follow_redirects=True, timeout=12)
        print(url, "->", r.status_code, r.url)
        if r.status_code == 200:
            soup = BeautifulSoup(r.text, "lxml")
            print(soup.body.prettify()[:3000] if soup.body else r.text[:3000])
            break
    except Exception as e:
        print(url, "->", e)
EOF
```
Identify: working search URL pattern, card/name/phone/email/city/next selectors.

- [ ] **Step 2: Implement sources/direcmin.py**

```python
import httpx
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urljoin
from sources import (
    HEADERS, _extract_email_from_html, _extract_contacts, fetch_website_email,
)

BASE_URL = "https://www.direcmin.com"

SECTOR_KEYWORDS = {
    "saas": ["software", "tecnologia", "plataforma"],
    "healthtech": ["salud", "clinica", "medico"],
    "agtech": ["agricultura", "ganaderia", "campo"],
    "retail": ["tienda", "comercio", "retail"],
}

# ADJUST AFTER INSPECTION ─────────────────────────────────────────
SEARCH_PATH = "/buscar"
CARD_SELECTOR = ".empresa, .listing, article, li.result"
NAME_SELECTOR = "h2, h3, .nombre, .company-name"
PHONE_SELECTOR = ".telefono, .phone, [itemprop='telephone']"
WEBSITE_SELECTOR = "a[href^='http']:not([href*='direcmin'])"
CITY_SELECTOR = ".ciudad, .city, .location"
NEXT_SELECTOR = "a[rel='next'], a.next, a.siguiente"
# ─────────────────────────────────────────────────────────────────

_SECTOR_SCORES = {"saas": 4, "healthtech": 3, "agtech": 2, "retail": 1}


def _parse_card(card, sector: str) -> dict | None:
    name_el = card.select_one(NAME_SELECTOR)
    if not name_el:
        return None
    company = name_el.get_text(strip=True)
    if not company:
        return None

    phone = None
    el = card.select_one(PHONE_SELECTOR)
    if el:
        phone = el.get_text(strip=True)

    domain = None
    el = card.select_one(WEBSITE_SELECTOR)
    if el and el.get("href", "").startswith("http"):
        domain = urlparse(el["href"]).netloc.lstrip("www.").lower()

    city = None
    el = card.select_one(CITY_SELECTOR)
    if el:
        city = el.get_text(strip=True)

    email = _extract_email_from_html(card)

    contacts = None
    if not email:
        if domain:
            email = fetch_website_email(domain)
        if not email:
            contacts = _extract_contacts(card) or None

    return {
        "source": "direcmin",
        "company": company,
        "sector": sector,
        "sector_score": _SECTOR_SCORES.get(sector, 0),
        "city": city,
        "headcount": None,
        "founded_year": None,
        "phone": phone,
        "email": email,
        "contacts": contacts,
        "domain": domain,
        "has_website": 1 if domain else 0,
    }


def scrape(sector: str, city: str | None = None):
    keywords = SECTOR_KEYWORDS.get(sector, [sector])
    seen: set[str] = set()

    for keyword in keywords:
        url = f"{BASE_URL}{SEARCH_PATH}"
        params: dict = {"q": keyword}
        if city:
            params["ciudad"] = city

        while url:
            try:
                r = httpx.get(url, params=params, timeout=15, headers=HEADERS, follow_redirects=True)
                r.raise_for_status()
                params = {}
            except Exception as e:
                print(f"  [direcmin] error: {e}", flush=True)
                break

            soup = BeautifulSoup(r.text, "lxml")
            cards = soup.select(CARD_SELECTOR)
            if not cards:
                print(f"  [direcmin] no cards at {r.url} — check CARD_SELECTOR", flush=True)
                break

            for card in cards:
                lead = _parse_card(card, sector)
                if not lead or lead["company"] in seen:
                    continue
                seen.add(lead["company"])
                yield lead

            next_el = soup.select_one(NEXT_SELECTOR)
            url = urljoin(str(r.url), next_el["href"]) if next_el and next_el.get("href") else None
```

- [ ] **Step 3: Smoke test**
```bash
cd tools/biz-analyzer && .venv/bin/python cli.py scrape --source direcmin --sector saas
```
If "no cards": fix selectors from inspection output.

- [ ] **Step 4: Commit**
```bash
cd tools/biz-analyzer && git add sources/direcmin.py && git commit -m "feat(biz-analyzer): direcmin.com scraper"
```

---

### Task 8: sources/pymesdechile.py

**Files:**
- Create: `tools/biz-analyzer/sources/pymesdechile.py`

- [ ] **Step 1: Inspect pymesdechile.cl**
```bash
cd tools/biz-analyzer && .venv/bin/python3 - <<'EOF'
import httpx
from bs4 import BeautifulSoup

headers = {"User-Agent": "Mozilla/5.0 Chrome/120.0.0.0 Safari/537.36", "Accept-Language": "es-CL,es;q=0.9"}
for url in [
    "https://www.pymesdechile.cl/empresas?categoria=tecnologia",
    "https://www.pymesdechile.cl/buscar?q=software",
    "https://pymesdechile.cl",
]:
    try:
        r = httpx.get(url, headers=headers, follow_redirects=True, timeout=12)
        print(url, "->", r.status_code, r.url)
        if r.status_code == 200:
            soup = BeautifulSoup(r.text, "lxml")
            print(soup.body.prettify()[:3000] if soup.body else r.text[:3000])
            break
    except Exception as e:
        print(url, "->", e)
EOF
```

- [ ] **Step 2: Implement sources/pymesdechile.py**

```python
import httpx
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urljoin
from sources import (
    HEADERS, _extract_email_from_html, _extract_contacts, fetch_website_email,
)

BASE_URL = "https://www.pymesdechile.cl"

SECTOR_KEYWORDS = {
    "saas": ["software", "tecnologia", "plataforma"],
    "healthtech": ["salud", "clinica", "medico"],
    "agtech": ["agricultura", "ganaderia", "campo"],
    "retail": ["tienda", "comercio", "retail"],
}

# ADJUST AFTER INSPECTION ─────────────────────────────────────────
SEARCH_PATH = "/empresas"
CARD_SELECTOR = ".empresa, .pyme, article, li.empresa, .listing-item"
NAME_SELECTOR = "h2, h3, .nombre, .company-name"
PHONE_SELECTOR = ".telefono, .phone, [itemprop='telephone']"
WEBSITE_SELECTOR = "a[href^='http']:not([href*='pymesdechile'])"
CITY_SELECTOR = ".ciudad, .city, .region"
NEXT_SELECTOR = "a[rel='next'], a.next, a.siguiente"
# ─────────────────────────────────────────────────────────────────

_SECTOR_SCORES = {"saas": 4, "healthtech": 3, "agtech": 2, "retail": 1}


def _parse_card(card, sector: str) -> dict | None:
    name_el = card.select_one(NAME_SELECTOR)
    if not name_el:
        return None
    company = name_el.get_text(strip=True)
    if not company:
        return None

    phone = None
    el = card.select_one(PHONE_SELECTOR)
    if el:
        phone = el.get_text(strip=True)

    domain = None
    el = card.select_one(WEBSITE_SELECTOR)
    if el and el.get("href", "").startswith("http"):
        domain = urlparse(el["href"]).netloc.lstrip("www.").lower()

    city = None
    el = card.select_one(CITY_SELECTOR)
    if el:
        city = el.get_text(strip=True)

    email = _extract_email_from_html(card)

    contacts = None
    if not email:
        if domain:
            email = fetch_website_email(domain)
        if not email:
            contacts = _extract_contacts(card) or None

    return {
        "source": "pymesdechile",
        "company": company,
        "sector": sector,
        "sector_score": _SECTOR_SCORES.get(sector, 0),
        "city": city,
        "headcount": None,
        "founded_year": None,
        "phone": phone,
        "email": email,
        "contacts": contacts,
        "domain": domain,
        "has_website": 1 if domain else 0,
    }


def scrape(sector: str, city: str | None = None):
    keywords = SECTOR_KEYWORDS.get(sector, [sector])
    seen: set[str] = set()

    for keyword in keywords:
        url = f"{BASE_URL}{SEARCH_PATH}"
        params: dict = {"categoria": keyword}
        if city:
            params["ciudad"] = city

        while url:
            try:
                r = httpx.get(url, params=params, timeout=15, headers=HEADERS, follow_redirects=True)
                r.raise_for_status()
                params = {}
            except Exception as e:
                print(f"  [pymesdechile] error: {e}", flush=True)
                break

            soup = BeautifulSoup(r.text, "lxml")
            cards = soup.select(CARD_SELECTOR)
            if not cards:
                print(f"  [pymesdechile] no cards at {r.url} — check CARD_SELECTOR", flush=True)
                break

            for card in cards:
                lead = _parse_card(card, sector)
                if not lead or lead["company"] in seen:
                    continue
                seen.add(lead["company"])
                yield lead

            next_el = soup.select_one(NEXT_SELECTOR)
            url = urljoin(str(r.url), next_el["href"]) if next_el and next_el.get("href") else None
```

- [ ] **Step 3: Smoke test**
```bash
cd tools/biz-analyzer && .venv/bin/python cli.py scrape --source pymesdechile --sector saas
```

- [ ] **Step 4: Commit**
```bash
cd tools/biz-analyzer && git add sources/pymesdechile.py && git commit -m "feat(biz-analyzer): pymesdechile.cl scraper"
```

---

### Task 9: Update scrape-today.sh + full run

**Files:**
- Modify: `tools/biz-analyzer/scrape-today.sh`

- [ ] **Step 1: Replace scrape-today.sh**

```bash
#!/usr/bin/env bash
# Daily scrape: fast sources first, sectors highest-priority-first.
# Safe to re-run — skips already-scraped records (name+source dedup).
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"
source .venv/bin/activate

SECTORS=("saas" "healthtech" "agtech" "retail")
SOURCES=("amarillas" "direcmin" "pymesdechile")

for source in "${SOURCES[@]}"; do
  for sector in "${SECTORS[@]}"; do
    echo "── $source / $sector"
    python3 cli.py scrape --source "$source" --sector "$sector" || true
  done
done

echo ""
echo "Done. Stats:"
python3 cli.py stats
echo ""
echo "CSV: outputs/$(date +%d-%m-%Y).csv"
```

- [ ] **Step 2: Run the full scrape**
```bash
cd tools/biz-analyzer && bash scrape-today.sh
```
Watch output. "no cards found" messages mean a selector needs fixing — go back to that source's Task and re-run the inspection step. Everything else should stream new leads to the terminal.

- [ ] **Step 3: Verify CSV**
```bash
cd tools/biz-analyzer && .venv/bin/python3 - <<'EOF'
import csv, datetime
fname = f"outputs/{datetime.date.today().strftime('%d-%m-%Y')}.csv"
rows = list(csv.DictReader(open(fname, encoding="utf-8")))
with_email = [r for r in rows if r.get("email")]
no_email_with_contact = [r for r in rows if not r.get("email") and r.get("contact_1_name")]
print(f"Total rows:            {len(rows)}")
print(f"With email:            {len(with_email)}")
print(f"No email + contact:    {len(no_email_with_contact)}")
print("\nTop 5 leads:")
for r in rows[:5]:
    print(f"  [{r['composite_score']}] {r['company']} | {r['email'] or 'no-email'} | {r['contact_1_name']}")
EOF
```

- [ ] **Step 4: Final commit**
```bash
cd tools/biz-analyzer && git add scrape-today.sh && git commit -m "feat(biz-analyzer): scrape-today.sh — fast sources in sector priority order"
```
