# Business Analyzer CLI — PRD

**Build trigger:** After first 3 clients close. Do not build before.
**Folder:** `tools/biz-analyzer/`
**Language:** Python 3.11+

---

## What it does

Combines industry priority, geographic targeting, and business size filtering to produce a scored, ranked lead queue — ready for outreach. Confirms no working website via DNS + HTTP before surfacing any lead.

---

## Sector Priority (hardcoded, from business plan)

| Score | Sector | Filter keywords |
|-------|--------|----------------|
| 4 | SaaS / B2B Software | "software", "SaaS", "tecnología B2B", "plataforma" |
| 3 | HealthTech | "salud digital", "health tech", "telemedicina", "medical software" |
| 2 | AgTech | "agricultura", "agtech", "campo", "ganadería digital" |
| 1 | Retail / E-commerce | "tienda", "comercio", "retail", "e-commerce" |
| 0 | **SKIP — Fintech** | "fintech", "pagos", "crédito digital" — crowded, hire in-house |

---

## Lead Sources

### Tier 1 — Startups
| Source | Method |
|--------|--------|
| Apollo.io free | Filter: Chile, founded ≤2yr, headcount 1–5, no website |
| Crunchbase free | Cross-reference funding stage (pre-seed/seed only) |
| Start-Up Chile alumni | CORFO cohort lists — verified startups |
| NuMarket | Chilean startup ranking with founding year filter |

### Tier 2 — Pymes fallback
| Source | Method |
|--------|--------|
| Google Maps | Category + city search; filter entries with no website field |
| Páginas Amarillas (amarillas.cl) | Category + contact scrape |
| directorio-chile.com | Open directory, no login |
| directorioempresaschile.cl | 33k user-registered businesses |
| SII public registry | Official Chilean tax authority company data |

---

## Scoring Model

Each lead receives a composite score:

```
score = sector_priority (0–4)
      + no_website_confirmed (0 or 3)
      + headcount_1_to_5 (0 or 2)
      + founded_lte_2yr (0 or 2)
      + location_boost (0 or 1)  # Las Condes / Providencia / Vitacura
```

Max score: 12. Output sorted descending. Leads scoring 0 (Fintech) are excluded.

---

## Website Check (`filter.py`)

For each lead with a domain field:
1. `socket.getaddrinfo(domain)` — NXDOMAIN → no website ✓
2. `httpx.get(f"http://{domain}", timeout=5)` — refused or empty body → no website ✓
3. Both pass → `has_website = True` → excluded from queue

---

## Architecture

```
tools/biz-analyzer/
├── cli.py              # Entry point — argparse, orchestrates pipeline
├── sources/
│   ├── apollo.py       # Apollo.io free tier scraper
│   ├── google_maps.py  # Playwright-based (JS-rendered)
│   ├── amarillas.py    # httpx static scrape
│   ├── directorio.py   # directorio-chile.com + directorioempresaschile.cl
│   └── sii.py          # SII public registry
├── filter.py           # DNS + HTTP website check
├── scorer.py           # Composite score calculation
├── db.py               # SQLite storage + CSV export
├── tui.py              # Rich TUI — approve (a) / skip (s) / quit (q)
├── templates.py        # Render personalised cold email per approved lead
└── README.md
```

---

## CLI Interface

```bash
# Scrape by source and sector
python cli.py scrape --source google_maps --sector saas --city Santiago

# Review queue sorted by score
python cli.py review

# Export approved, uncontacted leads to CSV
python cli.py export

# Stats
python cli.py stats
```

---

## TUI Review Screen

Displays per lead:
- Company name · Sector · Score · City
- Headcount · Founded · Source
- Domain (raw) · Website check result
- Phone · Email

Keys: `a` = approve + render email · `s` = skip · `q` = quit

---

## Storage Schema

```sql
CREATE TABLE leads (
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
  domain TEXT,
  has_website INTEGER,
  composite_score INTEGER,
  approved INTEGER DEFAULT 0,
  contacted INTEGER DEFAULT 0,
  created_at TEXT
);
```

---

## Output per approved lead

```
To: {email}
Subject: {company} no tiene sitio web — te lo resuelvo en 2 semanas

Hola {contact_name or "equipo"},
...
```

---

## Dependencies

- `httpx` — async HTTP checks
- `playwright` — Google Maps (JS-rendered)
- `rich` — TUI table
- `sqlite3` — stdlib
- `argparse` — stdlib

---

## Out of scope (v1)

- Paid APIs
- LinkedIn scraping (manual verification only)
- Automatic email sending (output is a rendered draft, sending is manual)
- Fintech leads
