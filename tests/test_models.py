# tests/test_models.py
import pytest
from datetime import date
from typing import Optional
from chat.models import (
    Source, Feature, ICP, Pricing, Product,
    Job, Taxonomy, ChatRequest, ChatResponse, ChatMessage,
)

def test_source_parses():
    s = Source(url="https://example.com", date=date(2026, 5, 1), type="vendor_docs")
    assert s.type == "vendor_docs"
    assert s.quote is None

def test_feature_defaults():
    f = Feature(
        id="test_feat",
        name="Test feature",
        mechanism="Does something",
        jobs=["identify-company-on-site"],
        verdict=True,
        sources=[Source(url="https://x.com", date=date(2026, 1, 1), type="vendor_docs")],
    )
    assert f.notes is None
    assert f.verdict is True

def test_icp_optional_bounds():
    icp = ICP(sweet_spot=["smb"], source="https://x.com", date=date(2026, 1, 1))
    assert icp.min_team_size is None
    assert icp.max_team_size is None

def test_pricing_no_price():
    p = Pricing(free_tier=True, model="flat", source="https://x.com", date=date(2026, 1, 1))
    assert p.entry_price_usd is None

def test_chat_request_defaults():
    req = ChatRequest(messages=[ChatMessage(role="user", content="hi")])
    assert req.team_size is None
    assert req.budget_usd is None
    assert req.products is None

def test_chat_response_step_values():
    r = ChatResponse(message="ok", step="candidates")
    assert r.step == "candidates"
    assert r.candidates is None

from chat.loader import load_product, load_all_products, load_taxonomy
import pathlib

PRODUCTS_DIR = pathlib.Path(__file__).parent.parent / "products"
JOBS_DIR = pathlib.Path(__file__).parent.parent / "jobs"

def test_load_product_warmly():
    p = load_product("warmly", products_dir=PRODUCTS_DIR)
    assert p.product == "warmly"
    assert len(p.features) > 0
    assert p.pricing.entry_price_usd == 799

def test_load_product_missing():
    with pytest.raises(FileNotFoundError):
        load_product("nonexistent", products_dir=PRODUCTS_DIR)

def test_load_all_products():
    products = load_all_products(products_dir=PRODUCTS_DIR)
    slugs = [p.product for p in products]
    assert "warmly" in slugs
    assert "percepto" in slugs
    assert len(products) == 5

def test_load_taxonomy():
    t = load_taxonomy(jobs_dir=JOBS_DIR)
    job_ids = [j.id for j in t.jobs]
    assert "identify-company-on-site" in job_ids
    assert "engage-visitor-without-rep" in job_ids
