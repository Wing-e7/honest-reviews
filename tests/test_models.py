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
