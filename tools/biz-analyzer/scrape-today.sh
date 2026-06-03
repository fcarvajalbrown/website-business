#!/usr/bin/env bash
# Daily scrape: amarillas.emol.com (Elasticsearch API) + direcmin.com (mining).
# pymesdechile = defunct — skipped.
# Safe to re-run — skips already-scraped records (name+source dedup).
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"
source .venv/bin/activate

echo "=== amarillas.emol.com ==="
SECTORS=("saas" "healthtech" "agtech" "retail")
for sector in "${SECTORS[@]}"; do
  echo "── amarillas / $sector"
  python3 cli.py scrape --source amarillas --sector "$sector" || true
done

echo ""
echo "=== direcmin.com (mining) ==="
python3 cli.py scrape --source direcmin --sector mining || true

echo ""
echo "Done. Stats:"
python3 cli.py stats
echo ""
echo "CSV: outputs/$(date +%d-%m-%Y).csv"
echo ""
echo "Next: python3 cleanup.py && python3 sort.py"
