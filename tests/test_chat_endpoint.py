# tests/test_chat_endpoint.py
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock


@pytest.fixture
def client():
    with patch("chat.main._llm_chat", new_callable=AsyncMock) as mock_llm:
        mock_llm.return_value = "I need a bit more info. What's your team size?"
        from chat.main import app
        yield TestClient(app), mock_llm


def test_health(client):
    c, _ = client
    r = c.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_chat_vague_query_returns_clarify(client):
    c, mock_llm = client
    mock_llm.return_value = "What's your team size and monthly budget?"
    r = c.post("/chat", json={
        "messages": [{"role": "user", "content": "I need a GTM tool"}]
    })
    assert r.status_code == 200
    data = r.json()
    assert data["step"] in ("clarify", "candidates")
    assert isinstance(data["message"], str)


def test_chat_specific_query_returns_candidates(client):
    c, mock_llm = client
    mock_llm.return_value = (
        '{"step": "candidates", "job_ids": ["voice-first-interaction", "engage-visitor-without-rep"], '
        '"team_size": 5, "budget_usd": 200, '
        '"message": "Based on your use case, here are the top matches: percepto, intercom"}'
    )
    r = c.post("/chat", json={
        "messages": [
            {"role": "user", "content": "I want to engage website visitors with voice, team of 5, budget $200/mo"}
        ]
    })
    assert r.status_code == 200
    assert r.json()["step"] in ("clarify", "candidates", "comparison")


def test_chat_step2_with_products(client):
    c, mock_llm = client
    mock_llm.return_value = "Warmly uses Slack alerts; Percepto speaks to visitors directly via voice."
    r = c.post("/chat", json={
        "messages": [
            {"role": "user", "content": "Compare warmly and percepto for engaging visitors"},
            {"role": "assistant", "content": "Top matches: warmly, percepto. Want a deep comparison?"},
            {"role": "user", "content": "Yes, compare them"},
        ],
        "products": ["warmly", "percepto"],
        "team_size": 10,
        "budget_usd": 500,
    })
    assert r.status_code == 200
    assert r.json()["step"] == "comparison"
