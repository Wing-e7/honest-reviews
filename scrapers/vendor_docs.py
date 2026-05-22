import os
import json
import httpx
import yaml
from datetime import date
from typing import Optional
from .base import chunk_text, clean_html
from chat.store import ChromaStore

_MODEL = os.getenv("HONEST_REVIEWS_LLM_MODEL", "gpt-4o-mini")
_llm = None


def _get_llm():
    global _llm
    if _llm is None:
        from openai import OpenAI
        _llm = OpenAI(
            base_url=os.getenv("HONEST_REVIEWS_LLM_BASE_URL", "https://api.openai.com/v1"),
            api_key=os.getenv("HONEST_REVIEWS_LLM_API_KEY", "no-key"),
        )
    return _llm


def scrape_vendor_docs(
    product_slug: str,
    url: str,
    store: Optional[ChromaStore] = None,
) -> dict:
    """
    Fetches a product URL, extracts feature claims via LLM, writes a draft YAML patch,
    and upserts evidence chunks to ChromaDB.
    Returns the draft claims dict.
    """
    resp = httpx.get(url, follow_redirects=True, timeout=15)
    resp.raise_for_status()
    text = clean_html(resp.text)

    prompt = (
        f"Extract all distinct product features from this page for product '{product_slug}'.\n"
        f"For each feature return a JSON object with: id, name, mechanism, verdict (true/false), notes.\n"
        f"Return a JSON array only. No markdown fences.\n\nPage text:\n{text[:6000]}"
    )
    raw = _get_llm().chat.completions.create(
        model=_MODEL,
        messages=[{"role": "user", "content": prompt}],
    ).choices[0].message.content or "[]"

    try:
        claims = json.loads(raw)
    except json.JSONDecodeError:
        claims = []

    today = str(date.today())
    for claim in claims:
        claim.setdefault("jobs", [])
        claim.setdefault("sources", [{"url": url, "date": today, "type": "vendor_docs"}])

    draft_path = f"products/{product_slug}.draft.yaml"
    with open(draft_path, "w") as f:
        yaml.dump({"features": claims}, f, allow_unicode=True, default_flow_style=False)
    print(f"Draft written to {draft_path} — review and merge into {product_slug}.yaml")

    if store:
        chunks = chunk_text(text)
        metadatas = [{"source_url": url, "source_type": "vendor_docs", "source_date": today}] * len(chunks)
        store.upsert_chunks(product=product_slug, chunks=chunks, metadatas=metadatas)

    return {"claims": claims, "draft_path": draft_path}
