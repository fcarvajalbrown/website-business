import pytest
from final_filter import _professional_score, _assign_phase

def test_score_all_four_signals():
    row = {
        "email": "ceo@empresa.cl",
        "phone": "+56 9 1234 5678",
        "city": "Las Condes",
        "company": "Empresa SPA",
    }
    assert _professional_score(row) == 4

def test_score_gmail_no_phone_generic_city():
    row = {"email": "empresa@gmail.com", "phone": None, "city": "Santiago", "company": "Empresa"}
    assert _professional_score(row) == 0

def test_score_company_email_only():
    row = {"email": "info@acme.cl", "phone": None, "city": "Santiago", "company": "Acme"}
    assert _professional_score(row) == 1

def test_score_phone_and_company_email():
    row = {"email": "v@empresa.cl", "phone": "(2)22034072", "city": "Santiago", "company": "X"}
    assert _professional_score(row) == 2

def test_score_premium_city_providencia():
    row = {"email": "v@gmail.com", "phone": None, "city": "Providencia", "company": "X"}
    assert _professional_score(row) == 1

def test_score_premium_city_vitacura():
    row = {"email": "v@gmail.com", "phone": None, "city": "Vitacura", "company": "X"}
    assert _professional_score(row) == 1

def test_score_registered_suffix_ltda():
    row = {"email": "v@gmail.com", "phone": None, "city": "Santiago", "company": "Acme Ltda."}
    assert _professional_score(row) == 1

def test_score_registered_suffix_spa():
    row = {"email": "v@gmail.com", "phone": None, "city": "Santiago", "company": "BetaTech SPA"}
    assert _professional_score(row) == 1

def test_score_hotmail_not_professional():
    row = {"email": "info@hotmail.com", "phone": None, "city": "Santiago", "company": "X"}
    assert _professional_score(row) == 0

def test_assign_phase_mining_always_mining():
    row = {"sector": "mining", "composite_score": 3}
    assert _assign_phase(row, 4, True) == "mining"

def test_assign_phase3_requires_all_three():
    row = {"sector": "saas", "composite_score": 9}
    assert _assign_phase(row, 3, True) == "phase3"

def test_assign_phase3_fails_without_dns():
    row = {"sector": "saas", "composite_score": 9}
    assert _assign_phase(row, 3, False) == "phase2"

def test_assign_phase3_fails_without_quality():
    row = {"sector": "saas", "composite_score": 9}
    assert _assign_phase(row, 2, True) == "phase2"

def test_assign_phase2_mid_score_two_signals():
    row = {"sector": "saas", "composite_score": 7}
    assert _assign_phase(row, 2, False) == "phase2"

def test_assign_phase2_dns_confirmed_bumps():
    row = {"sector": "healthtech", "composite_score": 6}
    assert _assign_phase(row, 2, True) == "phase2"

def test_assign_phase1_low_score():
    row = {"sector": "retail", "composite_score": 4}
    assert _assign_phase(row, 1, False) == "phase1"

def test_assign_phase1_default_for_zero_quality():
    row = {"sector": "agtech", "composite_score": 5}
    assert _assign_phase(row, 0, False) == "phase1"
