# chat/models.py
from pydantic import BaseModel
from typing import Optional
from datetime import date


class Source(BaseModel):
    url: str
    date: date
    type: str  # vendor_docs | g2_review | changelog | community
    quote: Optional[str] = None


class Feature(BaseModel):
    id: str
    name: str
    mechanism: str
    jobs: list[str]
    verdict: bool
    notes: Optional[str] = None
    sources: list[Source]


class ICP(BaseModel):
    sweet_spot: list[str]  # startup | smb | mid_market | enterprise
    min_team_size: Optional[int] = None
    max_team_size: Optional[int] = None
    source: str
    date: date


class Pricing(BaseModel):
    free_tier: bool
    entry_price_usd: Optional[float] = None  # None = custom / contact sales
    model: str  # per_seat | usage | flat | custom
    source: str
    date: date


class Product(BaseModel):
    product: str
    url: str
    category: str
    last_scraped: date
    icp: ICP
    pricing: Pricing
    features: list[Feature]


class Job(BaseModel):
    id: str
    label: str
    outcome: str
    category: str
    weight: float  # 0-1; importance across all buyers; community-editable


class Taxonomy(BaseModel):
    jobs: list[Job]


class ChatMessage(BaseModel):
    role: str  # user | assistant
    content: str


class ChatRequest(BaseModel):
    messages: list[ChatMessage]
    team_size: Optional[int] = None
    budget_usd: Optional[float] = None
    products: Optional[list[str]] = None  # product slugs for step 2


class ChatResponse(BaseModel):
    message: str
    step: str  # clarify | candidates | comparison
    candidates: Optional[list[str]] = None
