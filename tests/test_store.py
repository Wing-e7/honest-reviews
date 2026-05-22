# tests/test_store.py
import pytest
from chat.store import ChromaStore

@pytest.fixture
def store(tmp_path):
    return ChromaStore(persist_dir=str(tmp_path / "chroma"), collection_prefix="test")

def test_upsert_and_query(store):
    store.upsert_chunks(
        product="warmly",
        chunks=["Warmly fires Slack alerts when target accounts visit.", "IP enrichment via Clearbit."],
        metadatas=[
            {"source_url": "https://warmly.ai", "source_type": "vendor_docs", "source_date": "2026-05-01"},
            {"source_url": "https://warmly.ai/features", "source_type": "vendor_docs", "source_date": "2026-05-01"},
        ],
    )
    results = store.query_chunks(product="warmly", query="Slack notification", top_k=2)
    assert len(results) >= 1
    assert any("Slack" in r["text"] for r in results)

def test_query_returns_metadata(store):
    store.upsert_chunks(
        product="percepto",
        chunks=["Percepto speaks to visitors using voice before they leave."],
        metadatas=[{"source_url": "https://perceptoai.com", "source_type": "vendor_docs", "source_date": "2026-05-01"}],
    )
    results = store.query_chunks(product="percepto", query="voice", top_k=1)
    assert results[0]["source_url"] == "https://perceptoai.com"
    assert results[0]["source_type"] == "vendor_docs"

def test_query_empty_collection_returns_empty(store):
    results = store.query_chunks(product="unknown_product", query="anything", top_k=3)
    assert results == []
