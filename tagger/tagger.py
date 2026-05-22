import os
import json
import click
from typing import Optional
from chat.loader import load_product, load_taxonomy
from chat.models import Feature

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


def _suggest_jobs(feature: Feature, all_job_ids: list[str]) -> list[str]:
    prompt = (
        f"Given this feature:\n"
        f"Name: {feature.name}\n"
        f"Mechanism: {feature.mechanism}\n\n"
        f"Which of these job IDs does it address? Return a JSON array of job IDs only.\n"
        f"Available jobs: {json.dumps(all_job_ids)}"
    )
    resp = _get_llm().chat.completions.create(
        model=_MODEL,
        messages=[{"role": "user", "content": prompt}],
    )
    raw = resp.choices[0].message.content or "[]"
    try:
        suggested = json.loads(raw)
        return [j for j in suggested if j in all_job_ids]
    except json.JSONDecodeError:
        return []


@click.command()
@click.option("--product", required=True, help="Product slug to tag (e.g. warmly)")
@click.option("--untagged-only", is_flag=True, default=True, help="Only tag features with empty jobs list")
def tag(product: str, untagged_only: bool) -> None:
    """Suggest job tags for untagged features via LLM. Review suggestions, then edit the YAML."""
    p = load_product(product)
    taxonomy = load_taxonomy()
    all_job_ids = [j.id for j in taxonomy.jobs]

    features_to_tag = [f for f in p.features if not f.jobs] if untagged_only else p.features

    if not features_to_tag:
        click.echo(f"No untagged features found for {product}.")
        return

    click.echo(f"Suggesting job tags for {len(features_to_tag)} features in {product}...\n")
    for feat in features_to_tag:
        suggestions = _suggest_jobs(feat, all_job_ids)
        click.echo(f"Feature: {feat.id}")
        click.echo(f"  Mechanism: {feat.mechanism}")
        click.echo(f"  Suggested jobs: {suggestions}")
        click.echo(f"  → Edit products/{product}.yaml: set jobs: {suggestions}\n")
