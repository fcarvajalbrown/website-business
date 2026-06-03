# biz-analyzer v1 — Design Spec

**Date:** 2026-06-03  
**Goal:** CSV of Chilean SME/startup leads with emails for same-day WhatsApp/email outreach.

---

## Scope (today)

Build the scrape pipeline only. Skip: `filter.py`, `tui.py`, `templates.py`.

---

## Files to build

```
tools/biz-analyzer/
├── scorer.py              # sector priority + composite score (no deps)
├── db.py                  # SQLite + append_lead() + export_csv()
├── cli.py                 # argparse: scrape / stats / export
└── sources/
    ├── __init__.py
    ├── amarillas.py       # httpx — FIRST, end-to-end before adding others
    ├── direcmin.py        # httpx — second
    └── pymesdechile.py    # httpx — third
```

---

## Sector priority (hardcoded)

| Score | Sector | Keywords |
|-------|--------|----------|
| 4 | saas | "software", "SaaS", "tecnología B2B", "plataforma" |
| 3 | healthtech | "salud digital", "health tech", "telemedicina", "medical software" |
| 2 | agtech | "agricultura", "agtech", "campo", "ganadería digital" |
| 1 | retail | "tienda", "comercio", "retail", "e-commerce" |
| 0 | fintech | SKIP — do not scrape |

Run order: saas → healthtech → agtech → retail.

---

## Composite score

```
score = sector_priority (0–4)
      + no_website_confirmed (0 or 3)
      + headcount_1_to_5 (0 or 2)
      + founded_lte_2yr (0 or 2)
      + location_boost (0 or 1)   # Las Condes / Providencia / Vitacura
```

Max 12. Leads with score 0 excluded from CSV.

---

## Data flow

```
cli.py scrape --source amarillas --sector saas [--city Santiago]
  → sources/amarillas.py: httpx page-by-page, yields lead dicts
  → scorer.py.score(lead): adds composite_score field
  → db.py.append_lead(lead): SQLite INSERT + JSON append (both per-record)
  → after all pages: db.py.export_csv(): subprocess generates CSV sorted DESC
```

---

## Email extraction — fallback chain

For each listing:
1. Parse `<a href="mailto:...">` or visible email text from listing HTML
2. Try contact-reveal: attempt GET/POST to the reveal endpoint (httpx); decode `[at]`/`[dot]`, entity chars, `data-email` attrs
3. If reveal is JS-gated: use Playwright selectively for that one click
4. Fall back: scrape linked website's `/contacto` or `/about` page with httpx
5. If all fail: `email: null` (lead still saved, see below)

Start httpx-only. Add Playwright only if a source consistently requires it.

### No-email leads — save key people anyway

When `email: null`, capture up to **3 key contacts** from the listing / linked website's contact-about page. Only keep roles that matter for cold outreach:

**Priority roles (matched case-insensitively, Chilean Spanish + English variants):**

```
CEO, Chief Executive Officer,
Director Ejecutivo, Directora Ejecutiva,
Gerente General, Gerente,
Presidente, Presidenta, Presidente Ejecutivo,
Director General, Directora General,
Director, Directora,
Dueño, Dueña, Propietario, Propietaria,
Fundador, Fundadora,
Co-Fundador, Co-Fundadora, Cofundador, Cofundadora,
Founder, Co-founder,
Socio Principal, Socia Principal,
Socio Gerente, Socia Gerente,
Socio Fundador, Socia Fundadora,
Representante Legal,
Apoderado, Apoderada,
CTO, Chief Technology Officer,
Owner, Emprendedor, Emprendedora
```

Skip: Vendedor, Ejecutivo de Ventas, Soporte, Atención al Cliente, Asistente, Secretaria, Contador, RRHH, and any title without a decision-maker signal.

Stored as a JSON array in a single `contacts` SQLite column:
```json
[
  {"name": "María González", "title": "CEO", "linkedin": "https://linkedin.com/in/..."},
  {"name": "Carlos Ruiz", "title": "CTO", "linkedin": null}
]
```

In the CSV export, flattened to columns for easy spreadsheet use:
`contact_1_name | contact_1_title | contact_1_linkedin | contact_2_name | contact_2_title | contact_2_linkedin | contact_3_name | contact_3_title | contact_3_linkedin`

These columns are empty when `email` is present (redundant) and only populated when `email: null`.

---

## Crash safety

- `db.py.append_lead()`: SQLite INSERT first, then JSON append. Both per-record, never batched.
- On startup: load today's JSON → build `seen = set of (company, source)` → skip dupes.
- `SIGINT` caught in `cli.py`: graceful exit after current record completes. Never `os._exit()`.

---

## Output

```
tools/biz-analyzer/outputs/
  03-06-2026.json     # primary, written record-by-record
  03-06-2026.csv      # generated via subprocess, sorted composite_score DESC
```

Multiple runs same day: append + dedup. Resume from existing JSON.

---

## CLI

```bash
# Scrape one source + sector
python cli.py scrape --source amarillas --sector saas

# Scrape one source, all sectors in priority order
python cli.py scrape --source amarillas --all-sectors

# Scrape all fast sources, all sectors
python cli.py scrape --all-sources --all-sectors

# Stats
python cli.py stats

# Export CSV from current SQLite state
python cli.py export
```

---

## `scrape-today.sh` update

Replace `google_maps` loop with: amarillas → direcmin → pymesdechile, across sectors saas → healthtech → agtech → retail. Google Maps stays in the script as an optional fallback flag.

---

## Build order

1. `scorer.py` — no deps, test immediately
2. `db.py` — depends on scorer output shape
3. `cli.py` — wires scrape/stats/export; no scrapers yet
4. `sources/amarillas.py` — get it producing emailed rows end-to-end
5. Verify: `python cli.py scrape --source amarillas --sector saas` → check JSON + CSV
6. `sources/direcmin.py` — add and test
7. `sources/pymesdechile.py` — add and test
8. Update `scrape-today.sh`

---

## Dependencies (in .venv)

- `httpx` — HTTP scraping (primary)
- `beautifulsoup4` — HTML parsing
- `playwright` — selective JS fallback only
- `rich` — CLI output (already in setup.sh)
- `sqlite3` — stdlib
- `argparse` — stdlib

---

## Out of scope (v1 today)

- `filter.py` (DNS/HTTP website check) — adds scoring accuracy later
- `tui.py` (approve/skip review screen)
- `templates.py` (cold email rendering)
- Google Maps scraping
- Apollo.io, LinkedIn
- Automatic email sending
