from sources import _decode_email, _extract_email_from_html, _extract_contacts, PRIORITY_ROLES
from bs4 import BeautifulSoup

def soup(html):
    return BeautifulSoup(html, "lxml")

def test_mailto_link():
    assert _extract_email_from_html(soup('<a href="mailto:ceo@empresa.cl">contacto</a>')) == "ceo@empresa.cl"

def test_data_email_attr():
    assert _extract_email_from_html(soup('<span data-email="info[at]empresa[dot]cl"></span>')) == "info@empresa.cl"

def test_obfuscated_text():
    assert _extract_email_from_html(soup('<p>hola [at] empresa [dot] cl</p>')) == "hola@empresa.cl"

def test_plain_email_in_text():
    assert _extract_email_from_html(soup('<p>Escríbenos: info@empresa.cl</p>')) == "info@empresa.cl"

def test_no_email_returns_none():
    assert _extract_email_from_html(soup('<p>Sin contacto</p>')) is None

def test_decode_bracket_at():
    assert _decode_email("info[at]empresa[dot]cl") == "info@empresa.cl"

def test_decode_spaced_at():
    assert _decode_email("info at empresa dot cl") == "info@empresa.cl"

def test_priority_roles_has_fundador():
    assert "fundador" in PRIORITY_ROLES

def test_priority_roles_has_fundadora():
    assert "fundadora" in PRIORITY_ROLES

def test_priority_roles_has_ceo():
    assert "ceo" in PRIORITY_ROLES

def test_priority_roles_has_representante_legal():
    assert "representante legal" in PRIORITY_ROLES

def test_extract_contacts_finds_ceo():
    html = "<div><p>María González</p><p>CEO</p><p>Pedro Ruiz</p><p>Vendedor</p></div>"
    contacts = _extract_contacts(soup(html))
    assert len(contacts) == 1
    assert contacts[0]["name"] == "María González"
    assert contacts[0]["title"] == "CEO"

def test_extract_contacts_max_3():
    html = "".join(f"<p>Person {i} García</p><p>CEO</p>" for i in range(10))
    assert len(_extract_contacts(soup(html))) <= 3

def test_extract_contacts_skips_non_priority():
    assert _extract_contacts(soup("<p>Ana Martínez</p><p>Vendedora</p>")) == []

def test_extract_contacts_linkedin():
    html = "<p>Ana López</p><p>Fundadora</p><p>https://linkedin.com/in/analopez</p>"
    contacts = _extract_contacts(soup(html))
    assert contacts[0]["linkedin"] == "https://linkedin.com/in/analopez"
