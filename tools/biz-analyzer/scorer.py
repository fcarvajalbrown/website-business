SECTOR_SCORES = {
    "saas": 4,
    "healthtech": 3,
    "mining": 3,
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
