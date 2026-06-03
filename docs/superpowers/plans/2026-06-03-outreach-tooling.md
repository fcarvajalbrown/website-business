# Outreach Tooling Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build `final_filter.py` (DNS check + phase CSVs), `mark_contacted.py` (SQLite stamp), and `tools/wa-automate/send.js` (WhatsApp batch sender) so the full outreach pipeline is runnable today.

**Architecture:** Three independent scripts with no shared runtime dependencies. Python scripts follow existing patterns in `tools/biz-analyzer/`. The WA-Automate sender is a standalone Node.js project under `tools/wa-automate/`. All are single-file, flat, no abstractions beyond what's needed.

**Tech Stack:** Python 3.13 + `.venv` (httpx, csv, socket, sqlite3, concurrent.futures), Node.js 18+ (whatsapp-web.js, csv-parse, qrcode-terminal).

---

## File map

| File | Role |
|------|------|
| `tools/biz-analyzer/final_filter.py` | DNS check, professional signal scoring, 5 phase CSVs |
| `tools/biz-analyzer/tests/test_final_filter.py` | Unit tests for pure functions |
| `tools/biz-analyzer/mark_contacted.py` | Mark leads contacted=1 in SQLite |
| `tools/biz-analyzer/tests/test_mark_contacted.py` | Integration tests with temp DB |
| `tools/wa-automate/package.json` | Node deps |
| `tools/wa-automate/send.js` | WhatsApp batch sender |
| `tools/wa-automate/.gitignore` | Exclude session cache |

---

### Task 1: final_filter.py — tests

**Files:**
- Create: `tools/biz-analyzer/tests/test_final_filter.py`

- [ ] **Step 1: Write failing tests for `_professional_score`**

`tests/test_final_filter.py`:
```python
import pytest
from final_filter import _professional_score, _assign_phase

def test_score_all_four_signals():
    row = {
        "email": "ceo@empresa.cl",
        "phone": "+56 9 1234 5678",
        "city": "Las Condes",
        "company": "Empresa SPA",
    }
    assert _professional_score(row) == 4

def test_score_gmail_no_phone_generic_city():
    row = {"email": "empresa@gmail.com", "phone": None, "city": "Santiago", "company": "Empresa"}
    assert _professional_score(row) == 0

def test_score_company_email_only():
    row = {"email": "info@acme.cl", "phone": None, "city": "Santiago", "company": "Acme"}
    assert _professional_score(row) == 1

def test_score_phone_and_company_email():
    row = {"email": "v@empresa.cl", "phone": "(2)22034072", "city": "Santiago", "company": "X"}
    assert _professional_score(row) == 2

def test_score_premium_city_providencia():
    row = {"email": "v@gmail.com", "phone": None, "city": "Providencia", "company": "X"}
    assert _professional_score(row) == 1

def test_score_premium_city_vitacura():
    row = {"email": "v@gmail.com", "phone": None, "city": "Vitacura", "company": "X"}
    assert _professional_score(row) == 1

def test_score_registered_suffix_ltda():
    row = {"email": "v@gmail.com", "phone": None, "city": "Santiago", "company": "Acme Ltda."}
    assert _professional_score(row) == 1

def test_score_registered_suffix_spa():
    row = {"email": "v@gmail.com", "phone": None, "city": "Santiago", "company": "BetaTech SPA"}
    assert _professional_score(row) == 1

def test_score_hotmail_not_professional():
    row = {"email": "info@hotmail.com", "phone": None, "city": "Santiago", "company": "X"}
    assert _professional_score(row) == 0

def test_assign_phase_mining_always_mining():
    row = {"sector": "mining", "composite_score": 3}
    assert _assign_phase(row, 4, True) == "mining"

def test_assign_phase3_requires_all_three():
    row = {"sector": "saas", "composite_score": 9}
    assert _assign_phase(row, 3, True) == "phase3"

def test_assign_phase3_fails_without_dns():
    row = {"sector": "saas", "composite_score": 9}
    assert _assign_phase(row, 3, False) == "phase2"

def test_assign_phase3_fails_without_quality():
    row = {"sector": "saas", "composite_score": 9}
    assert _assign_phase(row, 2, True) == "phase2"

def test_assign_phase2_mid_score_two_signals():
    row = {"sector": "saas", "composite_score": 7}
    assert _assign_phase(row, 2, False) == "phase2"

def test_assign_phase2_dns_confirmed_bumps():
    row = {"sector": "healthtech", "composite_score": 6}
    assert _assign_phase(row, 2, True) == "phase2"

def test_assign_phase1_low_score():
    row = {"sector": "retail", "composite_score": 4}
    assert _assign_phase(row, 1, False) == "phase1"

def test_assign_phase1_default_for_zero_quality():
    row = {"sector": "agtech", "composite_score": 5}
    assert _assign_phase(row, 0, False) == "phase1"
```

- [ ] **Step 2: Run — expect ImportError**
```bash
cd tools/biz-analyzer && .venv/bin/pytest tests/test_final_filter.py -v 2>&1 | tail -5
```
Expected: `ModuleNotFoundError: No module named 'final_filter'`

---

### Task 2: final_filter.py — implementation

**Files:**
- Create: `tools/biz-analyzer/final_filter.py`

- [ ] **Step 1: Implement final_filter.py**

```python
"""
final_filter.py — DNS website check, professional signal scoring, phase assignment.

Input:  outputs/DD-MM-YYYY-clean.csv  (preferred, from cleanup.py)
        outputs/DD-MM-YYYY.json       (fallback)

Output: outputs/DD-MM-YYYY-test.csv      (5–10 leads, 1 per sector from phase1)
        outputs/DD-MM-YYYY-phase1.csv    (3rd tier — score 4-6, quality ≥ 1)
        outputs/DD-MM-YYYY-phase2.csv    (2nd tier — score 6-8, quality ≥ 2)
        outputs/DD-MM-YYYY-phase3.csv    (best — score 8+, quality ≥ 3, DNS confirmed)
        outputs/DD-MM-YYYY-mining.csv    (all direcmin leads)
"""

import csv, json, socket, sys, time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path

import httpx

OUTPUT_DIR = Path(__file__).parent / "outputs"

_GENERIC_DOMAINS = {
    "gmail.com", "hotmail.com", "yahoo.com", "outlook.com",
    "live.com", "yahoo.es", "hotmail.es", "icloud.com", "yahoo.cl",
}
_PREMIUM_CITIES = {"las condes", "providencia", "vitacura", "ñuñoa", "nunoa"}
_COMPANY_SUFFIXES = {
    "s.a.", "spa", "s.p.a", "ltda.", "ltda", "e.i.r.l.", "e.i.r.l",
    "s.a.c.", "limitada", "s.a.c",
}


def _check_website(domain: str | None) -> bool:
    """True = confirmed no live website. False = website exists or unknown."""
    if not domain:
        return True
    try:
        socket.getaddrinfo(domain, 80, proto=socket.IPPROTO_TCP)
    except socket.gaierror:
        return True  # NXDOMAIN — definitely no website

    # Domain resolves — check if HTTP returns real content
    for scheme in ("https", "http"):
        try:
            r = httpx.get(f"{scheme}://{domain}", timeout=4, follow_redirects=True)
            if r.status_code < 400 and len(r.text) > 200:
                return False  # live website found
        except Exception:
            pass
    return True  # resolves but no real content


def _professional_score(row: dict) -> int:
    """Return 0–4 based on signals that suggest a company can pay."""
    score = 0

    email = (row.get("email") or "").lower()
    if "@" in email:
        domain = email.split("@")[1].strip()
        if domain not in _GENERIC_DOMAINS:
            score += 1

    if (row.get("phone") or "").strip():
        score += 1

    city = (row.get("city") or "").lower()
    if any(loc in city for loc in _PREMIUM_CITIES):
        score += 1

    name = (row.get("company") or "").lower()
    if any(sfx in name for sfx in _COMPANY_SUFFIXES):
        score += 1

    return score


def _assign_phase(row: dict, quality: int, no_website_confirmed: bool) -> str:
    """Return phase string for this lead."""
    sector = (row.get("sector") or "").lower()
    score = int(row.get("composite_score") or 0)

    if sector == "mining":
        return "mining"
    if score >= 8 and quality >= 3 and no_website_confirmed:
        return "phase3"
    if score >= 6 and quality >= 2:
        return "phase2"
    # Default: phase1 for anything that passes cleanup
    return "phase1"


def _load_rows() -> list[dict]:
    today = datetime.now().strftime("%d-%m-%Y")
    clean = OUTPUT_DIR / f"{today}-clean.csv"
    raw = OUTPUT_DIR / f"{today}.json"

    if clean.exists():
        with open(clean, encoding="utf-8") as f:
            return list(csv.DictReader(f))

    if raw.exists():
        with open(raw, encoding="utf-8") as f:
            data = json.load(f)
        flat = []
        for row in data:
            r = {k: v for k, v in row.items() if k != "contacts"}
            contacts = row.get("contacts") or []
            for i in range(3):
                c = contacts[i] if i < len(contacts) else {}
                r[f"contact_{i+1}_name"] = c.get("name", "")
                r[f"contact_{i+1}_title"] = c.get("title", "")
                r[f"contact_{i+1}_linkedin"] = c.get("linkedin") or ""
            flat.append(r)
        return flat

    print("No input file. Run cleanup.py first.")
    sys.exit(1)


def _dns_check_concurrent(rows: list[dict]) -> dict[int, bool]:
    """Return {row_index: no_website_confirmed} for all non-mining rows."""
    results: dict[int, bool] = {}
    non_mining = [
        (i, (rows[i].get("domain") or "").strip() or None)
        for i in range(len(rows))
        if (rows[i].get("sector") or "").lower() != "mining"
    ]

    with ThreadPoolExecutor(max_workers=12) as ex:
        futures = {ex.submit(_check_website, domain): idx for idx, domain in non_mining}
        done = 0
        for future in as_completed(futures):
            idx = futures[future]
            results[idx] = future.result()
            done += 1
            print(f"  DNS checks: {done}/{len(non_mining)}", end="\r", flush=True)

    print()
    return results


def _write_csv(path: Path, rows: list[dict]):
    if not rows:
        return
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=rows[0].keys())
        w.writeheader()
        w.writerows(rows)


def main():
    rows = _load_rows()
    print(f"Loaded {len(rows)} leads. Running DNS checks concurrently...")

    confirmed = _dns_check_concurrent(rows)

    buckets: dict[str, list] = {
        "phase1": [], "phase2": [], "phase3": [], "mining": [],
    }

    for i, row in enumerate(rows):
        sector = (row.get("sector") or "").lower()
        no_web = confirmed.get(i, False) if sector != "mining" else False
        quality = _professional_score(row)
        phase = _assign_phase(row, quality, no_web)

        row = dict(row)
        row["quality_score"] = quality
        row["no_website_dns"] = "yes" if no_web else "no"
        row["phase"] = phase
        buckets[phase].append(row)

    # TEST: 1 lead per sector from phase1 (mid-tier — don't waste best leads on unproven copy)
    test_rows: list[dict] = []
    test_sectors_seen: set[str] = set()
    for row in buckets["phase1"]:
        sector = (row.get("sector") or "").lower()
        if sector not in test_sectors_seen:
            test_rows.append(row)
            test_sectors_seen.add(sector)
        if len(test_sectors_seen) >= 5:
            break

    today = datetime.now().strftime("%d-%m-%Y")
    to_write = {"test": test_rows, **buckets}

    for phase, leads in to_write.items():
        out = OUTPUT_DIR / f"{today}-{phase}.csv"
        _write_csv(out, leads)
        if leads:
            with_email = sum(1 for r in leads if r.get("email"))
            print(f"{phase:8s}: {len(leads):4d} leads  ({with_email} with email) → {out.name}")

    total = sum(len(v) for v in buckets.values())
    print(f"\nTotal assigned: {total}")


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Run tests — expect all green**
```bash
cd tools/biz-analyzer && .venv/bin/pytest tests/test_final_filter.py -v 2>&1
```
Expected: 17 tests PASS.

- [ ] **Step 3: Run on today's data (live smoke test)**

First ensure cleanup has run:
```bash
cd tools/biz-analyzer && .venv/bin/python3 cleanup.py
```

Then run final_filter:
```bash
.venv/bin/python3 final_filter.py
```
Expected output (approximate):
```
Loaded 840 leads. Running DNS checks concurrently...
  DNS checks: 840/840
test    :   5 leads  (5 with email) → 03-06-2026-test.csv
phase1  : 380 leads  (...) → 03-06-2026-phase1.csv
phase2  : 280 leads  (...) → 03-06-2026-phase2.csv
phase3  :  80 leads  (...) → 03-06-2026-phase3.csv
mining  : 121 leads  (121 with email) → 03-06-2026-mining.csv
```

- [ ] **Step 4: Verify test.csv has 1 lead per sector**
```bash
.venv/bin/python3 -c "
import csv
rows = list(csv.DictReader(open('outputs/03-06-2026-test.csv', encoding='utf-8')))
print('TEST leads:', len(rows))
for r in rows:
    print(f'  [{r[\"composite_score\"]}] {r[\"company\"][:35]} | {r[\"sector\"]} | {r[\"email\"]}')
"
```

- [ ] **Step 5: Commit**
```bash
cd /Users/felipecarvajalbrown/Desktop/PERSONAL/website-business && git add tools/biz-analyzer/final_filter.py tools/biz-analyzer/tests/test_final_filter.py && git commit -m "feat(biz-analyzer): final_filter — DNS check, quality score, 5 phase CSVs"
```

---

### Task 3: mark_contacted.py

**Files:**
- Create: `tools/biz-analyzer/tests/test_mark_contacted.py`
- Create: `tools/biz-analyzer/mark_contacted.py`

- [ ] **Step 1: Write failing tests**

`tests/test_mark_contacted.py`:
```python
import csv, sqlite3, pytest
from pathlib import Path
from mark_contacted import mark_contacted


@pytest.fixture
def tmp_env(tmp_path, monkeypatch):
    db = tmp_path / "leads.db"
    conn = sqlite3.connect(str(db))
    conn.executescript("""
        CREATE TABLE leads (
            id INTEGER PRIMARY KEY, source TEXT, company TEXT,
            contacted INTEGER DEFAULT 0, created_at TEXT
        );
        INSERT INTO leads (company, source, contacted) VALUES ('Acme', 'amarillas', 0);
        INSERT INTO leads (company, source, contacted) VALUES ('Beta SPA', 'amarillas', 0);
        INSERT INTO leads (company, source, contacted) VALUES ('Gamma', 'direcmin', 0);
    """)
    conn.close()
    monkeypatch.setattr("mark_contacted.DB_PATH", db)
    return tmp_path


def test_marks_matching_rows(tmp_env):
    csv_file = tmp_env / "phase1.csv"
    csv_file.write_text("company,source,email\nAcme,amarillas,ceo@acme.cl\n", encoding="utf-8")
    n = mark_contacted(csv_file)
    assert n == 1
    conn = sqlite3.connect(str(tmp_env / "leads.db"))
    assert conn.execute("SELECT contacted FROM leads WHERE company='Acme'").fetchone()[0] == 1
    assert conn.execute("SELECT contacted FROM leads WHERE company='Beta SPA'").fetchone()[0] == 0
    conn.close()


def test_marks_multiple_rows(tmp_env):
    csv_file = tmp_env / "phase1.csv"
    csv_file.write_text(
        "company,source,email\nAcme,amarillas,a@a.cl\nBeta SPA,amarillas,b@b.cl\n",
        encoding="utf-8",
    )
    n = mark_contacted(csv_file)
    assert n == 2


def test_source_mismatch_not_marked(tmp_env):
    csv_file = tmp_env / "phase1.csv"
    # Gamma is in direcmin, but CSV says amarillas
    csv_file.write_text("company,source,email\nGamma,amarillas,g@g.cl\n", encoding="utf-8")
    n = mark_contacted(csv_file)
    assert n == 0
    conn = sqlite3.connect(str(tmp_env / "leads.db"))
    assert conn.execute("SELECT contacted FROM leads WHERE company='Gamma'").fetchone()[0] == 0
    conn.close()


def test_missing_company_skipped(tmp_env):
    csv_file = tmp_env / "phase1.csv"
    csv_file.write_text("company,source,email\n,amarillas,nobody@x.cl\n", encoding="utf-8")
    n = mark_contacted(csv_file)
    assert n == 0


def test_idempotent_double_mark(tmp_env):
    csv_file = tmp_env / "phase1.csv"
    csv_file.write_text("company,source,email\nAcme,amarillas,a@a.cl\n", encoding="utf-8")
    mark_contacted(csv_file)
    n = mark_contacted(csv_file)  # second call
    assert n == 1  # rowcount still 1 (UPDATE matches 1 row even if already 1)
```

- [ ] **Step 2: Run — expect ImportError**
```bash
cd tools/biz-analyzer && .venv/bin/pytest tests/test_mark_contacted.py -v 2>&1 | tail -5
```
Expected: `ModuleNotFoundError: No module named 'mark_contacted'`

- [ ] **Step 3: Implement mark_contacted.py**

```python
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
```

- [ ] **Step 4: Run tests — expect all green**
```bash
.venv/bin/pytest tests/test_mark_contacted.py -v 2>&1
```
Expected: 5 tests PASS.

- [ ] **Step 5: Smoke test on real data**
```bash
.venv/bin/python3 mark_contacted.py outputs/03-06-2026-test.csv
```
Expected: `Marked 5 leads as contacted in leads.db`

- [ ] **Step 6: Commit**
```bash
cd /Users/felipecarvajalbrown/Desktop/PERSONAL/website-business && git add tools/biz-analyzer/mark_contacted.py tools/biz-analyzer/tests/test_mark_contacted.py && git commit -m "feat(biz-analyzer): mark_contacted — stamp contacted=1 for a phase CSV"
```

---

### Task 4: wa-automate setup + send.js

**Files:**
- Create: `tools/wa-automate/package.json`
- Create: `tools/wa-automate/.gitignore`
- Create: `tools/wa-automate/send.js`

No unit tests here — WhatsApp connection requires scanning a QR code. Test is a dry-run flag.

- [ ] **Step 1: Check Node.js is available**
```bash
node --version && npm --version
```
Expected: Node 18+ and npm 9+. If not installed: `brew install node`.

- [ ] **Step 2: Create tools/wa-automate/ and package.json**
```bash
mkdir -p /Users/felipecarvajalbrown/Desktop/PERSONAL/website-business/tools/wa-automate
```

`tools/wa-automate/package.json`:
```json
{
  "name": "wa-outreach",
  "version": "1.0.0",
  "description": "WhatsApp batch sender for outreach phase CSVs",
  "main": "send.js",
  "scripts": {
    "send": "node send.js",
    "dry-run": "node send.js --dry-run"
  },
  "dependencies": {
    "whatsapp-web.js": "^1.26.0",
    "qrcode-terminal": "^0.12.0",
    "csv-parse": "^5.5.6"
  }
}
```

- [ ] **Step 3: Create .gitignore for wa-automate**

`tools/wa-automate/.gitignore`:
```
node_modules/
.wwebjs_auth/
.wwebjs_cache/
*.log
```

- [ ] **Step 4: Install dependencies**
```bash
cd /Users/felipecarvajalbrown/Desktop/PERSONAL/website-business/tools/wa-automate && npm install
```
Expected: `added N packages` with no errors. Takes 30–60 seconds.

- [ ] **Step 5: Implement send.js**

`tools/wa-automate/send.js`:
```javascript
/**
 * send.js — WhatsApp batch sender for outreach phase CSVs.
 *
 * Usage:
 *   node send.js <path/to/phase.csv>            # real send
 *   node send.js <path/to/phase.csv> --dry-run  # print without sending
 *
 * Environment variables:
 *   WA_TEMPLATE  - Message template (default below). Use {company} and {city} as placeholders.
 *   WA_MAX       - Max sends per run (default 50)
 *   WA_MIN_DELAY - Min ms between sends (default 30000)
 *   WA_MAX_DELAY - Max ms between sends (default 90000)
 */

const { Client, LocalAuth } = require('whatsapp-web.js');
const qrcode = require('qrcode-terminal');
const fs = require('fs');
const path = require('path');
const { parse } = require('csv-parse/sync');

// ── Config ────────────────────────────────────────────────────────────────────
const CSV_PATH = process.argv[2];
const DRY_RUN = process.argv.includes('--dry-run');

const TEMPLATE = process.env.WA_TEMPLATE ||
    'Hola {company} 👋 Vi que no tienen sitio web todavía. Soy Felipe, desarrollador web freelance en Chile — ayudo a empresas como la suya a tener presencia online en 2 semanas. ¿Tienen 15 min esta semana para conversar? Pueden ver mi trabajo en fcarvajalbrown.cl';

const MAX_SENDS  = parseInt(process.env.WA_MAX       || '50',    10);
const MIN_DELAY  = parseInt(process.env.WA_MIN_DELAY || '30000', 10);
const MAX_DELAY  = parseInt(process.env.WA_MAX_DELAY || '90000', 10);

// ── Helpers ───────────────────────────────────────────────────────────────────
function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

function randomDelay() {
    return Math.floor(Math.random() * (MAX_DELAY - MIN_DELAY + 1)) + MIN_DELAY;
}

/**
 * Normalise a Chilean phone number to WhatsApp chat ID format: 56XXXXXXXXX@c.us
 * Handles formats like: (9)62063759, (2)22034072, +56 9 1234 5678, 56912345678
 */
function formatPhone(raw) {
    if (!raw || !raw.trim()) return null;

    // Strip everything except digits and leading +
    let num = raw.replace(/[\s\-()\.]/g, '');

    // Remove leading +
    if (num.startsWith('+')) num = num.slice(1);

    // Already has country code
    if (num.startsWith('56') && num.length >= 10) return num + '@c.us';

    // Mobile: 9 digits starting with 9
    if (num.startsWith('9') && num.length === 9) return '569' + num + '@c.us';

    // Landline: 8 digits starting with area code (2,32,41,42,43,45,51,52,53,55,57,58,61,63,64,65,67,71,72,73,75)
    if (num.length === 8 || num.length === 9) return '56' + num + '@c.us';

    return null;
}

function renderTemplate(template, row) {
    return template
        .replace(/\{company\}/g, row.company || 'equipo')
        .replace(/\{city\}/g,    row.city    || 'Chile')
        .replace(/\{sector\}/g,  row.sector  || '');
}

// ── Main ─────────────────────────────────────────────────────────────────────
async function main() {
    if (!CSV_PATH) {
        console.error('Usage: node send.js <path/to/phase.csv> [--dry-run]');
        process.exit(1);
    }

    const csvContent = fs.readFileSync(CSV_PATH, 'utf8');
    const rows = parse(csvContent, { columns: true, skip_empty_lines: true });
    const sendable = rows.filter(r => r.phone && r.phone.trim());

    console.log(`CSV: ${CSV_PATH}`);
    console.log(`Rows: ${rows.length} total, ${sendable.length} with phone`);
    console.log(`Will send up to ${MAX_SENDS} messages | delay ${MIN_DELAY/1000}–${MAX_DELAY/1000}s`);
    if (DRY_RUN) console.log('\n⚠️  DRY RUN — no messages will be sent\n');

    if (DRY_RUN) {
        // Print preview of first 5 messages
        for (const row of sendable.slice(0, 5)) {
            const chatId = formatPhone(row.phone);
            const msg = renderTemplate(TEMPLATE, row);
            console.log(`→ ${row.company} | ${row.phone} → ${chatId}`);
            console.log(`  "${msg}"\n`);
        }
        process.exit(0);
    }

    const logPath = CSV_PATH.replace('.csv', '-sent.log');
    const logStream = fs.createWriteStream(logPath, { flags: 'a' });

    const client = new Client({
        authStrategy: new LocalAuth({ clientId: 'biz-outreach' }),
        puppeteer: {
            headless: true,
            args: ['--no-sandbox', '--disable-setuid-sandbox'],
        },
    });

    client.on('qr', qr => {
        console.log('\nScan this QR code with WhatsApp on your phone:');
        qrcode.generate(qr, { small: true });
        console.log('(Open WhatsApp → ··· → Linked devices → Link a device)\n');
    });

    client.on('authenticated', () => console.log('✓ Authenticated'));
    client.on('ready', async () => {
        console.log('✓ WhatsApp connected. Starting sends...\n');

        let sent = 0;
        let skipped = 0;

        for (const row of sendable) {
            if (sent >= MAX_SENDS) {
                console.log(`\nReached limit of ${MAX_SENDS}. Run again tomorrow.`);
                break;
            }

            const chatId = formatPhone(row.phone);
            if (!chatId) {
                logStream.write(`${new Date().toISOString()} | SKIP | ${row.company} | bad phone: ${row.phone}\n`);
                skipped++;
                continue;
            }

            const message = renderTemplate(TEMPLATE, row);

            try {
                await client.sendMessage(chatId, message);
                sent++;
                const entry = `${new Date().toISOString()} | SENT | ${row.company} | ${row.phone}\n`;
                logStream.write(entry);
                console.log(`[${sent}/${MAX_SENDS}] ✓ ${row.company} (${row.phone})`);
            } catch (err) {
                const entry = `${new Date().toISOString()} | ERROR | ${row.company} | ${row.phone} | ${err.message}\n`;
                logStream.write(entry);
                console.error(`[${sent}/${MAX_SENDS}] ✗ ${row.company} — ${err.message}`);
                skipped++;
            }

            if (sent < MAX_SENDS) {
                const delay = randomDelay();
                console.log(`  ⏱  ${Math.round(delay / 1000)}s...`);
                await sleep(delay);
            }
        }

        logStream.end();
        console.log(`\nDone. Sent: ${sent} | Skipped: ${skipped}`);
        console.log(`Log: ${logPath}`);
        process.exit(0);
    });

    client.on('auth_failure', msg => {
        console.error('Auth failed:', msg);
        process.exit(1);
    });

    client.initialize();
}

main().catch(err => {
    console.error('Fatal:', err);
    process.exit(1);
});
```

- [ ] **Step 6: Dry-run test — verify phone formatting and template**
```bash
cd /Users/felipecarvajalbrown/Desktop/PERSONAL/website-business/tools/wa-automate && node send.js ../biz-analyzer/outputs/03-06-2026-test.csv --dry-run
```
Expected output (no real sends):
```
CSV: ../biz-analyzer/outputs/03-06-2026-test.csv
Rows: 5 total, N with phone
⚠️  DRY RUN — no messages will be sent

→ Empresa X | (9)62063759 → 56962063759@c.us
  "Hola Empresa X 👋 Vi que no tienen sitio web..."
```

If phone formatting looks wrong for any row, check the raw phone value and adjust `formatPhone()` accordingly.

- [ ] **Step 7: Commit**
```bash
cd /Users/felipecarvajalbrown/Desktop/PERSONAL/website-business && git add tools/wa-automate/package.json tools/wa-automate/.gitignore tools/wa-automate/send.js && git commit -m "feat(wa-automate): WhatsApp batch sender — 30-90s delay, dry-run flag, send log"
```

---

### Task 5: Full pipeline smoke test

No new files — just verify the end-to-end chain works.

- [ ] **Step 1: Run full pipeline from scratch**
```bash
cd /Users/felipecarvajalbrown/Desktop/PERSONAL/website-business/tools/biz-analyzer

# 1. Filter + phase
.venv/bin/python3 cleanup.py
.venv/bin/python3 final_filter.py

# 2. Verify all 5 phase files exist
ls -la outputs/$(date +%d-%m-%Y)-*.csv
```
Expected: 5 files — test, phase1, phase2, phase3, mining.

- [ ] **Step 2: Verify phase3 has DNS-confirmed leads**
```bash
.venv/bin/python3 -c "
import csv
rows = list(csv.DictReader(open('outputs/\$(date +%d-%m-%Y)-phase3.csv', encoding='utf-8')))
dns_confirmed = [r for r in rows if r.get('no_website_dns') == 'yes']
print(f'phase3 total: {len(rows)}')
print(f'DNS confirmed: {len(dns_confirmed)}')
for r in rows[:5]:
    print(f'  [{r[\"composite_score\"]}] {r[\"company\"][:35]} | q={r[\"quality_score\"]} | {r[\"email\"]}')
"
```

- [ ] **Step 3: Dry-run WhatsApp for mining leads**
```bash
cd /Users/felipecarvajalbrown/Desktop/PERSONAL/website-business/tools/wa-automate
node send.js ../biz-analyzer/outputs/$(date +%d-%m-%Y)-mining.csv --dry-run
```
Expected: shows message previews for each mining lead with a phone number.

- [ ] **Step 4: Mark test leads as contacted after your real test send**

After you send the test CSV emails in Brevo and WhatsApp:
```bash
cd /Users/felipecarvajalbrown/Desktop/PERSONAL/website-business/tools/biz-analyzer
.venv/bin/python3 mark_contacted.py outputs/$(date +%d-%m-%Y)-test.csv
```
Expected: `Marked N leads as contacted in leads.db`

- [ ] **Step 5: Commit all remaining output files and finish**
```bash
cd /Users/felipecarvajalbrown/Desktop/PERSONAL/website-business
git add tools/wa-automate/package-lock.json
git commit -m "chore(wa-automate): lock file after npm install"
```

---

## Self-Review

**Spec coverage:**
- ✅ DNS check (socket + httpx) — `_check_website()` in final_filter.py
- ✅ Professional signal scoring (4 signals) — `_professional_score()`
- ✅ Phase assignment (test/phase1/phase2/phase3/mining) — `_assign_phase()`
- ✅ TEST uses phase1 mid-tier leads, not best — TEST selection loop in `main()`
- ✅ Mining exempt from no-website filter — `_assign_phase()` returns "mining" immediately
- ✅ Concurrent DNS checks — `_dns_check_concurrent()` with ThreadPoolExecutor
- ✅ mark_contacted stamps contacted=1 by (company, source) — `UPDATE` in mark_contacted.py
- ✅ WA-Automate 30–90s delay — `randomDelay()` + `sleep()` in send.js
- ✅ Max 50 sends/run — `MAX_SENDS` env var + guard in loop
- ✅ Dry-run flag — `--dry-run` arg in send.js
- ✅ Send log per phase CSV — `-sent.log` sibling file
- ✅ Phone normalisation for Chilean numbers — `formatPhone()` handles all formats seen in data

**Placeholder scan:** None found.

**Type consistency:**
- `mark_contacted(csv_path: Path) -> int` — matches usage in test and main()
- `_check_website(domain: str | None) -> bool` — matches call in `_dns_check_concurrent`
- `_professional_score(row: dict) -> int` — matches test fixtures and main() call
- `_assign_phase(row: dict, quality: int, no_website_confirmed: bool) -> str` — matches all callers
