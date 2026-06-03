"""
direcmin.com — Chilean mining-industry supplier directory (~3,000 providers).

Strategy:
  1. POST keyword search → get company listing pages
  2. For each company card: extract /{slug}/informacion-de-contacto URL
  3. GET contact page → parse email, phone, website, city
  4. If no email: try /{slug}/ejecutivos for key contacts

Sector: always "mining" (score=3). Ignores the `sector` arg from cli.py;
only yields when sector=="mining" to avoid being called 4 unnecessary times.
"""

import re
import time
import httpx
from bs4 import BeautifulSoup
from urllib.parse import urlparse
from sources import HEADERS, _extract_email_from_html, _extract_contacts, fetch_website_email

BASE = "https://www.direcmin.com"
SEARCH_URL = f"{BASE}/buscar-proveedores-para-la-mineria/resultados"
SEARCH_HEADERS = {
    **HEADERS,
    "Referer": f"{BASE}/buscar-proveedores-para-la-mineria",
    "Content-Type": "application/x-www-form-urlencoded",
}

# Keywords that surface tech/digital providers relevant to website-building outreach
SEARCH_TERMS = [
    "tecnologia",
    "software",
    "sistemas",
    "digital",
    "automatizacion",
    "informatica",
    "gestion",
    "consultoria",
    "seguridad",
    "ingenieria",
]

_SECTOR_SCORE = 3


def _search_slugs(keyword: str) -> list[str]:
    """Return list of /slug strings from a keyword search result page."""
    try:
        r = httpx.post(SEARCH_URL, data={"buscar": keyword}, headers=SEARCH_HEADERS,
                       follow_redirects=True, timeout=15)
        r.raise_for_status()
    except Exception as e:
        print(f"  [direcmin] search '{keyword}' error: {e}", flush=True)
        return []

    soup = BeautifulSoup(r.text, "lxml")
    centro = soup.find("div", id="centro")
    if not centro:
        return []

    slugs = []
    for a in centro.find_all("a", href=True):
        href = a["href"]
        if "/informacion-de-contacto" in href:
            slug = href.replace(BASE, "").replace("/informacion-de-contacto", "")
            slugs.append(slug.strip("/"))
    return slugs


def _parse_contact_page(html: str) -> dict:
    """Parse a /informacion-de-contacto page into a partial lead dict."""
    soup = BeautifulSoup(html, "lxml")
    centro = soup.find("div", id="centro")
    if not centro:
        return {}

    result: dict = {}

    # Company name — the bold h1 with font-size:18px
    h1s = centro.find_all("h1")
    for h in h1s:
        text = h.get_text(strip=True)
        if text and text != "Información Proveedor":
            result["company"] = text
            break

    # Label/value rows in the INFO BASICA table
    for row in centro.find_all("tr"):
        tds = row.find_all("td")
        if len(tds) < 2:
            continue
        label = tds[0].get_text(strip=True).lower()
        val_td = tds[1]
        value = val_td.get_text(strip=True)

        if "ciudad" in label:
            result["city"] = value
        elif "teléfono" in label or "telefono" in label:
            result["phone"] = value
        elif "email" in label:
            mailto = val_td.find("a", href=lambda h: h and h.startswith("mailto:"))
            if mailto:
                result["email"] = mailto["href"][7:].strip()
            elif "@" in value:
                result["email"] = value
        elif "sitio web" in label:
            web_a = val_td.find("a", href=True)
            if web_a:
                result["domain"] = urlparse(web_a["href"]).netloc.lstrip("www.").lower() or web_a.get_text(strip=True).lstrip("www.")
            elif value:
                result["domain"] = value.lstrip("www.")

    return result


def _fetch_contact(slug: str) -> dict:
    url = f"{BASE}/{slug}/informacion-de-contacto"
    try:
        r = httpx.get(url, headers=HEADERS, follow_redirects=True, timeout=12)
        r.raise_for_status()
        return _parse_contact_page(r.text)
    except Exception as e:
        print(f"  [direcmin] contact fetch error {slug}: {e}", flush=True)
        return {}


def _fetch_contacts_when_no_email(slug: str, domain: str | None) -> list[dict] | None:
    """Try ejecutivos page or company website for key people."""
    # Try ejecutivos page
    try:
        r = httpx.get(f"{BASE}/{slug}/ejecutivos", headers=HEADERS, follow_redirects=True, timeout=12)
        if r.status_code == 200:
            soup = BeautifulSoup(r.text, "lxml")
            acc = soup.find("div", id="accordion")
            if acc:
                exec_section = None
                for h3 in acc.find_all("h3"):
                    if "EJECUTIVOS" in h3.get_text():
                        exec_section = h3.find_next_sibling("div")
                        break
                if exec_section and exec_section.get_text(strip=True):
                    contacts = _extract_contacts(exec_section)
                    if contacts:
                        return contacts
    except Exception:
        pass

    # Fall back to company website
    if domain:
        try:
            r = httpx.get(f"https://{domain}", timeout=8, follow_redirects=True, headers=HEADERS)
            if r.status_code == 200:
                from bs4 import BeautifulSoup as BS
                contacts = _extract_contacts(BS(r.text, "lxml"))
                if contacts:
                    return contacts
        except Exception:
            pass

    return None


def scrape(sector: str, city: str | None = None):
    # direcmin is mining-only — only run when sector=="mining"
    if sector != "mining":
        return

    seen_slugs: set[str] = set()

    for keyword in SEARCH_TERMS:
        slugs = _search_slugs(keyword)
        for slug in slugs:
            if slug in seen_slugs:
                continue
            seen_slugs.add(slug)

            data = _fetch_contact(slug)
            if not data.get("company"):
                continue

            email = data.get("email")
            domain = data.get("domain")
            contacts = None

            if not email:
                if domain:
                    email = fetch_website_email(domain)
                if not email:
                    contacts = _fetch_contacts_when_no_email(slug, domain) or None

            yield {
                "source": "direcmin",
                "company": data["company"],
                "sector": "mining",
                "sector_score": _SECTOR_SCORE,
                "city": data.get("city"),
                "headcount": None,
                "founded_year": None,
                "phone": data.get("phone"),
                "email": email,
                "contacts": contacts,
                "domain": domain,
                "has_website": 1 if domain else 0,
            }

            time.sleep(0.3)  # be polite to the server
