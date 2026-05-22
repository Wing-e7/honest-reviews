# chat/candidate_scorer.py
from typing import Optional
from .models import Product, Taxonomy


def score_candidates(
    products: list[Product],
    taxonomy: Taxonomy,
    extracted_job_ids: list[str],
    team_size: Optional[int],
    budget_usd: Optional[float],
) -> list[tuple[Product, float]]:
    """
    Returns (product, score) pairs sorted by score descending.
    Hard mismatches on team size or budget are silently excluded.
    """
    results = []
    for product in products:
        # Hard mismatch: team size
        if team_size is not None:
            if product.icp.min_team_size and team_size < product.icp.min_team_size:
                continue
            if product.icp.max_team_size and team_size > product.icp.max_team_size:
                continue
        # Hard mismatch: budget
        if budget_usd is not None and product.pricing.entry_price_usd is not None:
            if budget_usd < product.pricing.entry_price_usd:
                continue

        # job_coverage: count of user jobs covered by this product (verdict=True features only)
        covered_jobs: set[str] = set()
        for feature in product.features:
            if feature.verdict:
                covered_jobs.update(feature.jobs)
        job_coverage = sum(1 for j in extracted_job_ids if j in covered_jobs)

        results.append((product, float(job_coverage)))

    return sorted(results, key=lambda x: x[1], reverse=True)
