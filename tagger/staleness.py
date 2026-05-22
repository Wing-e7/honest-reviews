import click
from datetime import date
from typing import Optional
from chat.models import Feature
from chat.context_builder import is_stale
from chat.loader import load_all_products

MAX_AGE = 90


def find_stale_features(
    product_features: dict[str, list[Feature]],
    max_age_days: int = MAX_AGE,
) -> list[dict]:
    results = []
    for product_slug, features in product_features.items():
        for feat in features:
            if is_stale(feat, max_age_days=max_age_days):
                oldest = min((date.today() - s.date).days for s in feat.sources)
                results.append({
                    "product": product_slug,
                    "feature_id": feat.id,
                    "feature_name": feat.name,
                    "days_old": oldest,
                })
    return results


@click.command()
@click.option("--max-age", default=MAX_AGE, help="Stale threshold in days")
def check_stale(max_age: int) -> None:
    """List all feature claims older than --max-age days."""
    products = load_all_products()
    product_features = {p.product: p.features for p in products}
    stale = find_stale_features(product_features, max_age_days=max_age)
    if not stale:
        click.echo(f"All claims are fresh (< {max_age} days).")
        return
    click.echo(f"Stale claims (>{max_age} days):\n")
    for s in stale:
        click.echo(f"  {s['product']} / {s['feature_id']} — {s['days_old']} days old")
