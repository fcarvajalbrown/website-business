#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "Setting up biz-analyzer..."

# Create venv if it doesn't exist
if [ ! -d ".venv" ]; then
  python3 -m venv .venv
  echo "Created .venv"
fi

# Activate
source .venv/bin/activate

# Install dependencies
pip install --quiet --upgrade pip
pip install --quiet httpx rich playwright beautifulsoup4 lxml pytest

# Install playwright browsers (needed for Google Maps scraping)
playwright install chromium --with-deps

# Initialize SQLite DB schema
python3 - <<'EOF'
import sqlite3, os
db_path = os.path.join(os.path.dirname(__file__), "leads.db")
conn = sqlite3.connect(db_path)
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
conn.close()
print("DB initialized at leads.db")
EOF

echo ""
echo "Setup complete. Run ./run.sh --help to get started."
