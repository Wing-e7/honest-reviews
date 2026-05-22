# chat/main.py
import os
import json
from typing import Optional
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from openai import AsyncOpenAI
from .models import ChatRequest, ChatResponse, ChatMessage
from .loader import load_all_products, load_taxonomy
from .candidate_scorer import score_candidates
from .context_builder import build_comparison_context
from .store import ChromaStore

app = FastAPI(title="honest-reviews", version="0.1.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

_store = ChromaStore()
_products = load_all_products()
_taxonomy = load_taxonomy()

_MODEL = os.getenv("HONEST_REVIEWS_LLM_MODEL", "gpt-4o-mini")
_llm: Optional[AsyncOpenAI] = None


def _get_llm() -> AsyncOpenAI:
    global _llm
    if _llm is None:
        _llm = AsyncOpenAI(
            base_url=os.getenv("HONEST_REVIEWS_LLM_BASE_URL", "https://api.openai.com/v1"),
            api_key=os.getenv("HONEST_REVIEWS_LLM_API_KEY", "sk-placeholder"),
        )
    return _llm


async def _llm_chat(system: str, messages: list[ChatMessage]) -> str:
    response = await _get_llm().chat.completions.create(
        model=_MODEL,
        messages=[{"role": "system", "content": system}]
        + [{"role": m.role, "content": m.content} for m in messages],
    )
    return response.choices[0].message.content or ""


_STEP1_SYSTEM = """You are honest-reviews, a product comparison assistant. Your job:
1. Understand the user's use case, team size, and budget from conversation history.
2. If any of these are missing and the query is vague, ask ONE clarifying question.
3. Once you have enough context, extract the relevant job IDs from this list:
   {job_ids}
4. Return a JSON object:
   {{"step": "candidates", "job_ids": [...], "team_size": N_or_null, "budget_usd": N_or_null, "message": "..."}}
   OR if still clarifying:
   {{"step": "clarify", "job_ids": [], "team_size": null, "budget_usd": null, "message": "your question"}}
Return ONLY valid JSON. No markdown fences."""

_STEP2_SYSTEM = """You are honest-reviews. Compare the following products for the user's use case.
Rules:
- Compare mechanism, not just whether a feature exists
- Flag stale claims explicitly
- Cite sources inline as (source_type, date, url)
- For each relevant job: explain how each product addresses it, or state it doesn't
- End with an overall recommendation and reasoning
- Never fabricate a feature not present in the structured data below

STRUCTURED DATA:
{context}"""


@app.get("/health")
async def health() -> dict:
    return {"status": "ok", "products": len(_products)}


@app.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest) -> ChatResponse:
    # Step 2: products explicitly selected
    if req.products:
        selected = [p for p in _products if p.product in req.products]
        job_ids = _extract_job_ids_from_messages(req.messages)
        use_case = req.messages[0].content if req.messages else ""
        context = build_comparison_context(
            products=selected,
            taxonomy=_taxonomy,
            job_ids=job_ids or [j.id for j in _taxonomy.jobs[:5]],
            use_case=use_case,
            store=_store,
        )
        message = await _llm_chat(
            system=_STEP2_SYSTEM.format(context=context),
            messages=req.messages,
        )
        return ChatResponse(message=message, step="comparison")

    # Step 1: discover candidates
    job_id_list = [j.id for j in _taxonomy.jobs]
    raw = await _llm_chat(
        system=_STEP1_SYSTEM.format(job_ids=", ".join(job_id_list)),
        messages=req.messages,
    )
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        return ChatResponse(message=raw, step="clarify")

    step = parsed.get("step", "clarify")
    message = parsed.get("message", raw)

    if step == "clarify":
        return ChatResponse(message=message, step="clarify")

    # Score candidates
    job_ids = parsed.get("job_ids", [])
    team_size = parsed.get("team_size")
    budget_usd = parsed.get("budget_usd")

    scored = score_candidates(
        products=_products,
        taxonomy=_taxonomy,
        extracted_job_ids=job_ids,
        team_size=team_size,
        budget_usd=budget_usd,
    )
    top = [p.product for p, _ in scored[:5] if _ > 0] or [p.product for p, _ in scored[:3]]

    summary = (
        f"{message}\n\nTop matches for your use case: **{', '.join(top)}**.\n"
        f"Want me to go deep on any 2-5 of these?"
    )
    return ChatResponse(message=summary, step="candidates", candidates=top)


def _extract_job_ids_from_messages(messages: list[ChatMessage]) -> list[str]:
    all_job_ids = {j.id for j in _taxonomy.jobs}
    found = []
    for msg in messages:
        for job_id in all_job_ids:
            if job_id.replace("-", " ") in msg.content.lower() or job_id in msg.content:
                found.append(job_id)
    return list(set(found))
