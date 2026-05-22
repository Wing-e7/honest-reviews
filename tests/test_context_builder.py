# tests/test_context_builder.py
import pytest
from datetime import date, timedelta
from chat.models import Feature, Source
from chat.context_builder import (
    is_stale,
    mechanism_quality_score,
    build_comparison_context,
)
from chat.store import ChromaStore
from chat.loader import load_product, load_taxonomy
import pathlib

PRODUCTS_DIR = pathlib.Path(__file__).parent.parent / "products"
JOBS_DIR = pathlib.Path(__file__).parent.parent / "jobs"


def _make_feature(source_types: list[str], days_old: int = 10) -> Feature:
    d = date.today() - timedelta(days=days_old)
    return Feature(
        id="test", name="Test", mechanism="Does something",
        jobs=["engage-visitor-without-rep"], verdict=True,
        sources=[Source(url="https://x.com", date=d, type=t) for t in source_types],
    )


def test_is_stale_old_source():
    f = _make_feature(["vendor_docs"], days_old=100)
    assert is_stale(f, max_age_days=90) is True


def test_is_stale_fresh_source():
    f = _make_feature(["vendor_docs"], days_old=30)
    assert is_stale(f, max_age_days=90) is False


def test_mechanism_quality_vendor_only():
    f = _make_feature(["vendor_docs"])
    assert mechanism_quality_score(f) == 1


def test_mechanism_quality_with_g2():
    f = _make_feature(["vendor_docs", "g2_review"])
    assert mechanism_quality_score(f) == 2


def test_mechanism_quality_with_community():
    f = _make_feature(["vendor_docs", "community"])
    assert mechanism_quality_score(f) == 3


def test_build_comparison_context_contains_products(tmp_path):
    store = ChromaStore(persist_dir=str(tmp_path / "chroma"))
    warmly = load_product("warmly", PRODUCTS_DIR)
    percepto = load_product("percepto", PRODUCTS_DIR)
    taxonomy = load_taxonomy(JOBS_DIR)
    ctx = build_comparison_context(
        products=[warmly, percepto],
        taxonomy=taxonomy,
        job_ids=["engage-visitor-without-rep"],
        use_case="engage visitors without SDRs",
        store=store,
    )
    assert "warmly" in ctx.lower()
    assert "percepto" in ctx.lower()
    assert "engage" in ctx.lower()
