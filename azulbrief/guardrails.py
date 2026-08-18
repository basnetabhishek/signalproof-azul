import re
from .models import Brief, Segment

CERTAINTY = re.compile(r"\b(definitely|certainly|clearly needs|will save|guarantee[sd]?|proven ROI|must buy)\b",re.I)
PERFORMANCE = re.compile(r"\b\d+(?:\.\d+)?%\s+(?:faster|improvement|savings|reduction)|\bcut costs? by\b",re.I)

def validate_brief(brief:Brief, segments:list[Segment], corpus:dict[str,str]) -> Brief:
    valid_ids={s.id for s in segments}
    kept=[]
    for obs in brief.observations:
        if not obs.segment_ids or not set(obs.segment_ids)<=valid_ids:
            brief.blocked_reasons.append(f"Unsupported account claim blocked: {obs.statement}")
        else: kept.append(obs)
    brief.observations=kept
    if brief.product_hypothesis:
        if not brief.product_hypothesis.corpus_ids or not set(brief.product_hypothesis.corpus_ids)<=set(corpus):
            brief.blocked_reasons.append("Product hypothesis lacked valid Azul corpus support.")
            brief.product_hypothesis=None
    combined=" ".join([brief.campaign_angle,brief.draft_messaging]+([brief.product_hypothesis.rationale] if brief.product_hypothesis else []))
    if CERTAINTY.search(combined):
        brief.blocked_reasons.append("Certainty language detected; draft withheld.")
        brief.draft_messaging=""
    if PERFORMANCE.search(combined):
        brief.blocked_reasons.append("Unverified ROI/performance guarantee detected; draft withheld.")
        brief.draft_messaging=""
    return brief

