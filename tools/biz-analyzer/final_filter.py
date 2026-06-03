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

import csv, json, socket, sys
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

    for scheme in ("https", "http"):
        try:
            r = httpx.get(f"{scheme}://{domain}", timeout=4, follow_redirects=True)
            if r.status_code < 400 and len(r.text) > 200:
                return False
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
        # Brevo/GMass merge field aliases — templates use {{startup}} and {{nombre}}
        row["startup"] = row.get("company", "")
        row["nombre"] = row.get("contact_1_name", "") or ""
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
