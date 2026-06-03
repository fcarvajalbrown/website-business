# biz-analyzer — Claude Code guide

## Token efficiency rule

**Never use WebFetch, WebSearch, or WebBrowser to get lead data.** All data comes from local scripts via Bash. One CLI call = one structured result. No fetching, no scraping in-session.

## How to get data (always use these instead of fetching)

```bash
# Scrape leads from a source into SQLite
python cli.py scrape --source google_maps --sector saas --city Santiago

# Review and approve leads interactively
python cli.py review

# Get current lead stats (counts, scores, sources)
python cli.py stats

# Export approved leads to CSV
python cli.py export --output leads.csv

# Check if a specific domain has a website
python cli.py check --domain empresa.cl

# Get the scored queue without opening TUI
python cli.py queue --limit 20 --min-score 5
```

## How to get sector/priority info

Do NOT search for it. It is hardcoded in `scorer.py`. Read the file.

## How to get lead details

Do NOT fetch LinkedIn or Apollo. Query SQLite directly:

```bash
sqlite3 leads.db "SELECT company, sector, composite_score, email FROM leads WHERE approved=0 ORDER BY composite_score DESC LIMIT 10;"
```

## File map

| File | What it does |
|------|-------------|
| `cli.py` | Entry point — always start here |
| `scorer.py` | Sector priority + composite score logic |
| `filter.py` | DNS + HTTP website check |
| `sources/` | One scraper module per source |
| `tui.py` | Rich TUI for lead review |
| `templates.py` | Cold email renderer |
| `db.py` | SQLite read/write |
| `leads.db` | Local database — source of truth |

## Adding a new source

1. Create `sources/newname.py` with a `scrape(sector, city) -> list[dict]` function
2. Register it in `cli.py` `--source` choices
3. Keys required: `company`, `sector`, `city`, `email`, `phone`, `domain`, `founded_year`, `headcount`

## Adding a new sector

Edit `scorer.py` — `SECTOR_SCORES` dict. Do not add Fintech (score stays 0, excluded).

## Running costs

All operations run locally. SQLite is the cache. If a scrape already ran today, read from DB — do not re-scrape.

```bash
# Check if today's scrape exists before re-running
sqlite3 leads.db "SELECT COUNT(*) FROM leads WHERE source='google_maps' AND DATE(created_at)=DATE('now');"
```
