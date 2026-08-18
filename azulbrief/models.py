from typing import Literal
from pydantic import BaseModel, Field, HttpUrl

Confidence = Literal["HIGH", "MEDIUM", "LOW", "INSUFFICIENT"]

class MockSignals(BaseModel):
    account_stage: str = "Target"
    intent_topics: list[str] = Field(default_factory=list)
    engagement_notes: str = ""

class Source(BaseModel):
    url: str
    title: str
    source_type: str
    text: str

class Segment(BaseModel):
    id: str
    url: str
    title: str
    source_type: str
    text: str

class Observation(BaseModel):
    statement: str
    segment_ids: list[str]
    kind: str = "public_evidence"

class ProductHypothesis(BaseModel):
    product: str
    rationale: str
    corpus_ids: list[str]
    supporting_observation_indexes: list[int] = Field(default_factory=list)

class Brief(BaseModel):
    company_domain: str
    observations: list[Observation]
    product_hypothesis: ProductHypothesis | None = None
    limitations: list[str] = Field(default_factory=list)
    campaign_angle: str = ""
    draft_messaging: str = ""
    confidence: Confidence = "INSUFFICIENT"
    blocked_reasons: list[str] = Field(default_factory=list)
    retrieved_product_evidence: dict[str, str] = Field(default_factory=dict)
    mock_signals: MockSignals

class AnalyzeRequest(BaseModel):
    domain: str
    mock_signals: MockSignals = Field(default_factory=MockSignals)
    use_llm: bool = False
    allow_browser_fallback: bool = False

