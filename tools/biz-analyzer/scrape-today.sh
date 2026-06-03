#!/usr/bin/env bash
# Run the full daily scrape across all priority sectors and sources.
# Safe to re-run — skips sources already scraped today.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"
source .venv/bin/activate

SECTORS=("saas" "healthtech" "agtech" "retail")
CITIES=("Santiago" "Providencia" "Las Condes" "Vitacura" "Ñuñoa")

for sector in "${SECTORS[@]}"; do
  for city in "${CITIES[@]}"; do
    echo "Scraping google_maps — $sector — $city"
    python3 cli.py scrape --source google_maps --sector "$sector" --city "$city" || true
  done
done

echo ""
echo "Scrape complete. Run ./run.sh review to approve leads."
python3 cli.py stats
