import pytest
from datetime import date, timedelta
from chat.models import Feature, Source
from tagger.staleness import find_stale_features


def _feat(days_old: int) -> Feature:
    d = date.today() - timedelta(days=days_old)
    return Feature(
        id="f1", name="Feature", mechanism="Does X",
        jobs=["crm-sync"], verdict=True,
        sources=[Source(url="https://x.com", date=d, type="vendor_docs")],
    )


def test_finds_stale():
    stale = find_stale_features({"warmly": [_feat(100)]}, max_age_days=90)
    assert len(stale) == 1
    assert stale[0]["product"] == "warmly"


def test_fresh_not_stale():
    stale = find_stale_features({"warmly": [_feat(30)]}, max_age_days=90)
    assert stale == []


def test_mixed():
    stale = find_stale_features(
        {"warmly": [_feat(100), _feat(10)]},
        max_age_days=90,
    )
    assert len(stale) == 1
