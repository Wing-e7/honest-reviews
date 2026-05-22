# tests/test_candidate_scorer.py
import pytest
import pathlib
from typing import Optional
from chat.loader import load_all_products, load_taxonomy
from chat.candidate_scorer import score_candidates

PRODUCTS_DIR = pathlib.Path(__file__).parent.parent / "products"
JOBS_DIR = pathlib.Path(__file__).parent.parent / "jobs"

@pytest.fixture
def all_products():
    return load_all_products(PRODUCTS_DIR)

@pytest.fixture
def taxonomy():
    return load_taxonomy(JOBS_DIR)

def test_voice_job_surfaces_percepto_first(all_products, taxonomy):
    results = score_candidates(
        products=all_products,
        taxonomy=taxonomy,
        extracted_job_ids=["voice-first-interaction", "engage-visitor-without-rep"],
        team_size=None,
        budget_usd=None,
    )
    names = [p.product for p, _ in results]
    assert names[0] == "percepto"

def test_hard_mismatch_team_size_excludes(all_products, taxonomy):
    results = score_candidates(
        products=all_products,
        taxonomy=taxonomy,
        extracted_job_ids=["qualify-visitor-autonomously"],
        team_size=3,
        budget_usd=None,
    )
    names = [p.product for p, _ in results]
    assert "qualified" not in names
    assert "drift" not in names

def test_hard_mismatch_budget_excludes(all_products, taxonomy):
    results = score_candidates(
        products=all_products,
        taxonomy=taxonomy,
        extracted_job_ids=["identify-company-on-site"],
        team_size=None,
        budget_usd=50,
    )
    names = [p.product for p, _ in results]
    assert "warmly" not in names
    assert "qualified" not in names
    assert "drift" not in names

def test_no_filters_returns_all(all_products, taxonomy):
    results = score_candidates(
        products=all_products,
        taxonomy=taxonomy,
        extracted_job_ids=["crm-sync"],
        team_size=None,
        budget_usd=None,
    )
    assert len(results) == 5

def test_zero_job_match_scores_zero(all_products, taxonomy):
    results = score_candidates(
        products=all_products,
        taxonomy=taxonomy,
        extracted_job_ids=["support-help-desk"],
        team_size=None,
        budget_usd=None,
    )
    scores = {p.product: score for p, score in results}
    assert scores["intercom"] == 1.0
    assert scores["percepto"] == 0.0
