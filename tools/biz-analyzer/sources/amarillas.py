import httpx, json
from urllib.parse import urlparse
from bs4 import BeautifulSoup
from sources import HEADERS, _extract_email_from_html, _extract_contacts, fetch_website_email

ES_URL = "https://amarillas.emol.com/elasticsearch/amarillas/_search?"
_ES_HEADERS = {**HEADERS, "Content-Type": "application/json", "Referer": "https://amarillas.emol.com/"}

SECTOR_KEYWORDS = {
    "saas": ["software", "plataforma", "tecnologia"],
    "healthtech": ["salud", "telemedicina", "clinica"],
    "agtech": ["agricultura", "ganaderia", "campo"],
    "retail": ["tienda", "comercio", "retail"],
}

_SECTOR_SCORES = {"saas": 4, "healthtech": 3, "agtech": 2, "retail": 1}
_PAGE = 100


def _search(keyword: str, offset: int = 0) -> list[dict]:
    payload = {
        "query": {"function_score": {"query": {"bool": {"must": [{"multi_match": {
            "query": keyword,
            "minimum_should_match": "100%",
            "fields": ["anunciador.anunciador_nodic^3", "anunciador", "anunciador.anunciador_syn",
                       "categorias.rubro^3", "categorias.rubro_syn", "marcas"],
            "operator": "and",
        }}]}}, "functions": [], "score_mode": "first", "boost_mode": "max"}},
        "from": offset,
        "size": _PAGE,
    }
    try:
        r = httpx.post(ES_URL, content=json.dumps(payload), headers=_ES_HEADERS, timeout=15)
        r.raise_for_status()
        return r.json().get("hits", {}).get("hits", [])
    except Exception as e:
        print(f"  [amarillas] search error: {e}", flush=True)
        return []


def _parse_hit(hit: dict, sector: str) -> dict | None:
    src = hit.get("_source", {})
    company = src.get("anunciador", "").strip()
    if not company:
        return None

    emails = src.get("emails", [])
    email = emails[0].get("direccion", "").strip() if emails else None
    if email and "@" not in email:
        email = None

    dirs = src.get("direcciones", [])
    phone = dirs[0].get("numero_telefono", "").strip() if dirs else None
    city = dirs[0].get("comuna", "").strip() if dirs else None

    sitios = src.get("sitios", [])
    website_url = sitios[0].get("url", "").strip() if sitios else None
    domain = None
    if website_url:
        try:
            domain = urlparse(website_url).netloc.lstrip("www.").lower() or None
        except Exception:
            pass

    contacts = None
    if not email:
        if domain:
            email = fetch_website_email(domain)
        if not email and domain:
            try:
                r = httpx.get(f"https://{domain}", timeout=8, follow_redirects=True, headers=HEADERS)
                if r.status_code == 200:
                    soup = BeautifulSoup(r.text, "lxml")
                    contacts = _extract_contacts(soup) or None
            except Exception:
                pass

    return {
        "source": "amarillas",
        "company": company,
        "sector": sector,
        "sector_score": _SECTOR_SCORES.get(sector, 0),
        "city": city,
        "headcount": None,
        "founded_year": None,
        "phone": phone,
        "email": email,
        "contacts": contacts,
        "domain": domain,
        "has_website": 1 if domain else 0,
    }


def scrape(sector: str, city: str | None = None):
    seen: set[str] = set()
    for keyword in SECTOR_KEYWORDS.get(sector, [sector]):
        offset = 0
        while True:
            hits = _search(keyword, offset)
            if not hits:
                break
            for hit in hits:
                lead = _parse_hit(hit, sector)
                if not lead or lead["company"] in seen:
                    continue
                if city and lead.get("city") and city.lower() not in (lead["city"] or "").lower():
                    continue
                seen.add(lead["company"])
                yield lead
            if len(hits) < _PAGE:
                break
            offset += _PAGE
