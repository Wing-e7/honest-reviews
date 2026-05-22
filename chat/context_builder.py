# chat/context_builder.py
from datetime import date
from typing import Optional
from .models import Product, Taxonomy, Feature
from .store import ChromaStore

MAX_CLAIM_AGE_DAYS = 90


def is_stale(feature: Feature, max_age_days: int = MAX_CLAIM_AGE_DAYS) -> bool:
    today = date.today()
    return all((today - s.date).days > max_age_days for s in feature.sources)


def mechanism_quality_score(feature: Feature) -> int:
    types = {s.type for s in feature.sources}
    if "community" in types or "changelog" in types:
        return 3
    if "g2_review" in types:
        return 2
    return 1


def _feature_block(feature: Feature, product_slug: str) -> dict:
    stale = is_stale(feature)
    quality = mechanism_quality_score(feature)
    citations = [
        {"url": s.url, "date": str(s.date), "type": s.type, "quote": s.quote}
        for s in feature.sources
    ]
    return {
        "product": product_slug,
        "feature": feature.name,
        "mechanism": feature.mechanism,
        "verdict": feature.verdict,
        "jobs": feature.jobs,
        "quality_score": quality,
        "stale": stale,
        "citations": citations,
    }


def build_comparison_context(
    products: list[Product],
    taxonomy: Taxonomy,
    job_ids: list[str],
    use_case: str,
    store: ChromaStore,
    top_k: int = 3,
) -> str:
    job_map = {j.id: j for j in taxonomy.jobs}
    relevant_jobs = [job_map[jid] for jid in job_ids if jid in job_map]

    sections: list[str] = []
    sections.append(f"USER USE CASE: {use_case}\n")
    sections.append(f"RELEVANT JOBS: {', '.join(j.label for j in relevant_jobs)}\n")

    for product in products:
        sections.append(f"\n## Product: {product.product} ({product.url})")
        sections.append(f"Category: {product.category}")
        if product.pricing.entry_price_usd:
            sections.append(
                f"Pricing: {'Free tier available. ' if product.pricing.free_tier else 'No free tier. '}"
                f"Entry: ${product.pricing.entry_price_usd}/mo ({product.pricing.model})"
            )
        else:
            sections.append(
                f"Pricing: {'Free tier. ' if product.pricing.free_tier else ''}Custom pricing."
            )

        # Features relevant to the requested jobs
        relevant_features = [
            f for f in product.features if any(j in f.jobs for j in job_ids)
        ]
        if relevant_features:
            sections.append("\n### Feature claims (relevant to your use case):")
            for feat in relevant_features:
                block = _feature_block(feat, product.product)
                stale_note = " [STALE — verify before relying on this]" if block["stale"] else ""
                verdict_str = "YES" if feat.verdict else "NO"
                sections.append(
                    f"- [{verdict_str}] {feat.name}{stale_note}\n"
                    f"  Mechanism: {feat.mechanism}\n"
                    f"  Evidence quality: {block['quality_score']}/3"
                )
                for c in block["citations"]:
                    quote_str = f' ("{c["quote"]}")' if c.get("quote") else ""
                    sections.append(f"  Source ({c['type']}, {c['date']}): {c['url']}{quote_str}")

        # RAG evidence
        for job_id in job_ids:
            chunks = store.query_chunks(product=product.product, query=job_id, top_k=top_k)
            if chunks:
                sections.append(f"\n### User evidence for '{job_id}':")
                for chunk in chunks:
                    sections.append(
                        f"  [{chunk.get('source_type', 'unknown')}, {chunk.get('source_date', '?')}] "
                        f"{chunk['text'][:300]}"
                    )

    return "\n".join(sections)
