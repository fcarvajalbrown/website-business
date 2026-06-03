import csv, sqlite3, pytest
from pathlib import Path
from mark_contacted import mark_contacted


@pytest.fixture
def tmp_env(tmp_path, monkeypatch):
    db = tmp_path / "leads.db"
    conn = sqlite3.connect(str(db))
    conn.executescript("""
        CREATE TABLE leads (
            id INTEGER PRIMARY KEY, source TEXT, company TEXT,
            contacted INTEGER DEFAULT 0, created_at TEXT
        );
        INSERT INTO leads (company, source, contacted) VALUES ('Acme', 'amarillas', 0);
        INSERT INTO leads (company, source, contacted) VALUES ('Beta SPA', 'amarillas', 0);
        INSERT INTO leads (company, source, contacted) VALUES ('Gamma', 'direcmin', 0);
    """)
    conn.close()
    monkeypatch.setattr("mark_contacted.DB_PATH", db)
    return tmp_path


def test_marks_matching_rows(tmp_env):
    csv_file = tmp_env / "phase1.csv"
    csv_file.write_text("company,source,email\nAcme,amarillas,ceo@acme.cl\n", encoding="utf-8")
    n = mark_contacted(csv_file)
    assert n == 1
    conn = sqlite3.connect(str(tmp_env / "leads.db"))
    assert conn.execute("SELECT contacted FROM leads WHERE company='Acme'").fetchone()[0] == 1
    assert conn.execute("SELECT contacted FROM leads WHERE company='Beta SPA'").fetchone()[0] == 0
    conn.close()


def test_marks_multiple_rows(tmp_env):
    csv_file = tmp_env / "phase1.csv"
    csv_file.write_text(
        "company,source,email\nAcme,amarillas,a@a.cl\nBeta SPA,amarillas,b@b.cl\n",
        encoding="utf-8",
    )
    n = mark_contacted(csv_file)
    assert n == 2


def test_source_mismatch_not_marked(tmp_env):
    csv_file = tmp_env / "phase1.csv"
    csv_file.write_text("company,source,email\nGamma,amarillas,g@g.cl\n", encoding="utf-8")
    n = mark_contacted(csv_file)
    assert n == 0
    conn = sqlite3.connect(str(tmp_env / "leads.db"))
    assert conn.execute("SELECT contacted FROM leads WHERE company='Gamma'").fetchone()[0] == 0
    conn.close()


def test_missing_company_skipped(tmp_env):
    csv_file = tmp_env / "phase1.csv"
    csv_file.write_text("company,source,email\n,amarillas,nobody@x.cl\n", encoding="utf-8")
    n = mark_contacted(csv_file)
    assert n == 0


def test_idempotent_double_mark(tmp_env):
    csv_file = tmp_env / "phase1.csv"
    csv_file.write_text("company,source,email\nAcme,amarillas,a@a.cl\n", encoding="utf-8")
    mark_contacted(csv_file)
    n = mark_contacted(csv_file)
    assert n == 1
