# website-business

## Session start

At the start of every session, before anything else, remind Felipe: **check `docs/pna0.5.md`** — it contains the running grey-area SEO tactics and business notes that should inform any site or outreach work.

Personal business/freelance landing page for Felipe Carvajal Brown — software development services for Chilean startups and SMEs.

## i18n convention

**Two self-contained HTML files, never a JS translation dictionary.**
- `index.html` = full Spanish content, hardcoded
- `en/index.html` = full English content, hardcoded
- Nav toggle = plain anchor links between `/` and `/en/`
- `hreflang` tags in `<head>` of both declare them as language alternates
- `main.js` is shared and language-neutral (portfolio renderer, timers, interactions)
- Reason: JS-based i18n risks EN content not being indexed by Google in the first crawl wave

## Stack

- Vanilla HTML/CSS/JS — no build step, no framework
- `index.html` — single-page site
- `src/styles.css` — all styles
- `src/main.js` — countdown timer, interactivity
- `assets/` — SVG business cards, palette JSON, images
- `docs/plan.pdf` — business plan (do not rename or move)

## Development

Open `index.html` directly in a browser — no server needed.

## Design

Color palette defined in `assets/palette.json`. Site targets Chilean market; copy is in Spanish.

## Commit conventions

Use **conventional commits** with **functional blocks** before pushing.

- Format: `type(scope): description`
- Types: `feat`, `fix`, `chore`, `docs`, `refactor`, `test`
- Before pushing: squash granular WIP commits into one commit per logical unit of work (a scraper, a tool, a feature, a doc). Never push more than one commit per functional block.
- Scope = the directory or tool name: `biz-analyzer`, `wa-automate`, `site`, `docs`

Examples:
```
feat(biz-analyzer): amarillas scraper — ES API, email fallback, 2421 leads
feat(wa-automate): WhatsApp batch sender — 30-90s delay, dry-run, send log
docs: outreach strategy spec — Brevo + WA-Automate, 6-touch sequence
chore(biz-analyzer): setup — bs4, lxml, pytest, UNIQUE index
```
