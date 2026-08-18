import os
from .models import *
from .fetcher import fetch_sources, normalize_domain
from .segmenter import segment_sources
from .extractor import heuristic_extract, llm_extract
from .retrieval import ProductRetriever
from .store import EvidenceStore
from .guardrails import validate_brief

def confidence_for(observations, product_docs):
    independent=len({sid.split("-")[1] for o in observations for sid in o.segment_ids})
    if not observations or not product_docs: return "INSUFFICIENT"
    if len(observations)>=3 and independent>=2: return "HIGH"
    if len(observations)>=2: return "MEDIUM"
    return "LOW"

def build_brief(req:AnalyzeRequest, store:EvidenceStore|None=None, sources=None):
    domain=normalize_domain(req.domain); store=store or EvidenceStore()
    sources=sources if sources is not None else fetch_sources(domain,req.allow_browser_fallback)
    segments=segment_sources(sources); store.save_segments(segments)
    observations=llm_extract(segments) if req.use_llm and os.getenv("OPENAI_API_KEY") else heuristic_extract(segments)
    # Validate extractor IDs before the model output can influence retrieval.
    valid={s.id for s in segments}
    observations=[o for o in observations if o.segment_ids and set(o.segment_ids)<=valid]
    query=" ".join(o.statement+" "+" ".join(store.exact_text(o.segment_ids).values()) for o in observations)
    docs=ProductRetriever().search(query,k=3) if query else []
    hypothesis=None
    if docs:
        top=docs[0]; hypothesis=ProductHypothesis(product=top["product"],
          rationale=f"A reviewable hypothesis based on the cited account evidence and {top['id']}; validation with the account is still required.",
          corpus_ids=[top["id"]],supporting_observation_indexes=list(range(min(2,len(observations)))))
    conf=confidence_for(observations,docs)
    limits=[]
    if not sources: limits.append("No accessible public pages were retrieved.")
    if len(sources)<2: limits.append("Fewer than two public source pages were available.")
    limits += ["Mock CRM/intent inputs are context only and are not treated as verified public evidence.",
               "Public mentions do not establish company-wide use, urgency, budget, or purchase intent."]
    angle=(f"Explore whether {hypothesis.product} is relevant to the verified signals—without assuming a current initiative." if hypothesis else "No campaign angle: evidence is insufficient.")
    draft=(f"We noticed public material related to {observations[0].statement.lower()} Would it be useful to compare that context with {hypothesis.product}?" if hypothesis and observations else "")
    corpus={d["id"]:d["text"] for d in ProductRetriever().docs}
    brief=Brief(company_domain=domain,observations=observations,product_hypothesis=hypothesis,
      limitations=limits,campaign_angle=angle,draft_messaging=draft,confidence=conf,
      retrieved_product_evidence={d["id"]:d["text"] for d in docs},mock_signals=req.mock_signals)
    brief=validate_brief(brief,segments,corpus)
    return brief,segments,store.save_brief(brief)

