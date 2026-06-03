import csv, json, os, sqlite3, pytest

@pytest.fixture
def tmp_env(tmp_path, monkeypatch):
    db = tmp_path / "leads.db"
    outputs = tmp_path / "outputs"
    outputs.mkdir()
    conn = sqlite3.connect(str(db))
    conn.executescript("""
        CREATE TABLE leads (
          id INTEGER PRIMARY KEY,
          source TEXT, company TEXT, sector TEXT, sector_score INTEGER,
          city TEXT, headcount TEXT, founded_year INTEGER,
          phone TEXT, email TEXT, contacts TEXT, domain TEXT,
          has_website INTEGER, composite_score INTEGER,
          approved INTEGER DEFAULT 0, contacted INTEGER DEFAULT 0,
          created_at TEXT DEFAULT (datetime('now'))
        );
        CREATE UNIQUE INDEX idx_company_source ON leads(company, source);
    """)
    conn.close()
    monkeypatch.setattr("db.DB_PATH", str(db))
    monkeypatch.setattr("db.OUTPUT_DIR", str(outputs))
    return tmp_path

def sample(**kw):
    return {"source": "amarillas", "company": "TechCo", "sector": "saas",
            "sector_score": 4, "city": "Santiago", "headcount": "1-5",
            "founded_year": 2024, "phone": "+56 2 1234 5678",
            "email": "ceo@techco.cl", "contacts": None,
            "domain": "techco.cl", "has_website": 1, "composite_score": 8, **kw}

def test_append_writes_json(tmp_env):
    import db
    db.append_lead(sample())
    files = list((tmp_env / "outputs").glob("*.json"))
    assert len(files) == 1
    data = json.loads(files[0].read_text())
    assert data[0]["company"] == "TechCo"

def test_append_writes_sqlite(tmp_env):
    import db
    db.append_lead(sample())
    conn = sqlite3.connect(str(tmp_env / "leads.db"))
    row = conn.execute("SELECT company, email FROM leads").fetchone()
    conn.close()
    assert row == ("TechCo", "ceo@techco.cl")

def test_append_deduplicates(tmp_env):
    import db
    db.append_lead(sample())
    db.append_lead(sample())
    conn = sqlite3.connect(str(tmp_env / "leads.db"))
    count = conn.execute("SELECT COUNT(*) FROM leads").fetchone()[0]
    conn.close()
    assert count == 1

def test_load_seen_empty(tmp_env):
    import db
    assert db.load_seen() == set()

def test_load_seen_after_append(tmp_env):
    import db
    db.append_lead(sample())
    assert ("TechCo", "amarillas") in db.load_seen()

def test_contacts_serialized_as_json(tmp_env):
    import db
    contacts = [{"name": "María", "title": "CEO", "linkedin": None}]
    db.append_lead(sample(email=None, contacts=contacts))
    conn = sqlite3.connect(str(tmp_env / "leads.db"))
    row = conn.execute("SELECT contacts FROM leads").fetchone()
    conn.close()
    assert json.loads(row[0]) == contacts

def test_export_csv_sorted_by_score(tmp_env):
    import db
    db.append_lead(sample(company="Low", composite_score=2))
    db.append_lead(sample(company="High", source="direcmin", composite_score=9))
    csv_path = db.export_csv()
    rows = list(csv.DictReader(open(csv_path)))
    assert rows[0]["company"] == "High"
    assert rows[1]["company"] == "Low"

def test_export_csv_flattens_contacts(tmp_env):
    import db
    contacts = [
        {"name": "Ana López", "title": "CEO", "linkedin": "https://linkedin.com/in/ana"},
        {"name": "Pedro Cruz", "title": "CTO", "linkedin": None},
    ]
    db.append_lead(sample(email=None, contacts=contacts))
    content = open(db.export_csv()).read()
    assert "Ana López" in content
    assert "contact_1_name" in content
    assert "contact_2_name" in content
    assert "contact_3_name" in content

def test_stats(tmp_env):
    import db
    db.append_lead(sample())
    db.append_lead(sample(company="NoEmail", source="direcmin", email=None))
    s = db.stats()
    assert s["total"] == 2
    assert s["with_email"] == 1
