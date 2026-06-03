import re
from html import unescape
from bs4 import BeautifulSoup

PRIORITY_ROLES = [
    "ceo", "chief executive officer",
    "director ejecutivo", "directora ejecutiva",
    "gerente general", "gerente",
    "presidente", "presidenta", "presidente ejecutivo",
    "director general", "directora general",
    "director", "directora",
    "dueño", "dueña", "propietario", "propietaria",
    "fundador", "fundadora",
    "co-fundador", "co-fundadora", "cofundador", "cofundadora",
    "founder", "co-founder",
    "socio principal", "socia principal",
    "socio gerente", "socia gerente",
    "socio fundador", "socia fundadora",
    "representante legal",
    "apoderado", "apoderada",
    "cto", "chief technology officer",
    "owner", "emprendedor", "emprendedora",
]

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "es-CL,es;q=0.9",
}

_EMAIL_RE = re.compile(r'[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}')


def _decode_email(text: str) -> str | None:
    text = unescape(text)
    text = (
        text.replace(" [at] ", "@").replace(" [dot] ", ".")
            .replace("[at]", "@").replace("[dot]", ".")
            .replace(" at ", "@").replace(" dot ", ".")
    )
    m = _EMAIL_RE.search(text)
    return m.group() if m else None


def _extract_email_from_html(soup: BeautifulSoup) -> str | None:
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if href.lower().startswith("mailto:"):
            return href[7:].split("?")[0].strip()
    for el in soup.find_all(attrs={"data-email": True}):
        e = _decode_email(el["data-email"])
        if e:
            return e
    return _decode_email(soup.get_text(" "))


def _role_priority(title: str) -> int:
    t = title.lower()
    for i, role in enumerate(PRIORITY_ROLES):
        if role in t:
            return i
    return len(PRIORITY_ROLES)


def _extract_contacts(soup: BeautifulSoup) -> list[dict]:
    lines = [l.strip() for l in soup.get_text("\n").splitlines() if l.strip()]
    seen: set[str] = set()
    candidates = []

    for i, line in enumerate(lines):
        line_lower = line.lower()
        for role in PRIORITY_ROLES:
            if role in line_lower:
                name = lines[i - 1] if i > 0 else None
                if (
                    name
                    and 1 < len(name.split()) <= 5
                    and not re.search(r'\d', name)
                    and name not in seen
                ):
                    linkedin = None
                    for j in range(max(0, i - 3), min(len(lines), i + 4)):
                        if "linkedin.com/in/" in lines[j].lower():
                            linkedin = lines[j].strip()
                            break
                    candidates.append({
                        "name": name, "title": line, "linkedin": linkedin,
                        "_p": _role_priority(line),
                    })
                    seen.add(name)
                break

    candidates.sort(key=lambda c: c["_p"])
    return [{"name": c["name"], "title": c["title"], "linkedin": c["linkedin"]}
            for c in candidates[:3]]


def fetch_website_email(domain: str) -> str | None:
    import httpx
    if not domain:
        return None
    for path in ["/contacto", "/contactenos", "/about", "/nosotros", "/contact"]:
        try:
            r = httpx.get(
                f"https://{domain}{path}", timeout=8,
                follow_redirects=True, headers=HEADERS,
            )
            if r.status_code == 200:
                from bs4 import BeautifulSoup as BS
                email = _extract_email_from_html(BS(r.text, "lxml"))
                if email:
                    return email
        except Exception:
            pass
    return None
