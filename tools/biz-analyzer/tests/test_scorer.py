from scorer import score

def base(**kw):
    return {"source": "test", "company": "Acme", "sector": "saas",
            "city": None, "headcount": None, "founded_year": None,
            "has_website": 1, **kw}

def test_saas_base():
    assert score(base())["composite_score"] == 4

def test_healthtech_base():
    assert score(base(sector="healthtech"))["composite_score"] == 3

def test_agtech_base():
    assert score(base(sector="agtech"))["composite_score"] == 2

def test_retail_base():
    assert score(base(sector="retail"))["composite_score"] == 1

def test_location_las_condes():
    assert score(base(city="Las Condes"))["composite_score"] == 5

def test_location_providencia():
    assert score(base(city="Providencia"))["composite_score"] == 5

def test_location_vitacura():
    assert score(base(city="Vitacura"))["composite_score"] == 5

def test_no_location_boost_santiago():
    assert score(base(city="Santiago"))["composite_score"] == 4

def test_headcount_1_5():
    assert score(base(headcount="1-5"))["composite_score"] == 6

def test_headcount_large_no_boost():
    assert score(base(headcount="50-100"))["composite_score"] == 4

def test_founded_recent():
    assert score(base(founded_year=2025))["composite_score"] == 6

def test_founded_old_no_boost():
    assert score(base(founded_year=2020))["composite_score"] == 4

def test_no_website_boost():
    assert score(base(has_website=0))["composite_score"] == 7

def test_max_score():
    lead = base(city="Las Condes", headcount="1-5", founded_year=2025, has_website=0)
    assert score(lead)["composite_score"] == 12

def test_mutates_in_place():
    lead = base()
    result = score(lead)
    assert result is lead
    assert "composite_score" in lead
