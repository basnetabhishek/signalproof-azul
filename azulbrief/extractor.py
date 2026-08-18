import json, os, re
from .models import Segment, Observation

PATTERNS = {
 "Java runtime evidence": r"\b(java|jvm|jdk|openjdk|spring boot|kotlin)\b",
 "Performance or latency pressure": r"\b(latency|throughput|performance|garbage collection|real[ -]?time)\b",
 "Java licensing or migration pressure": r"\b(oracle java|java licen[cs]|jdk migration|openjdk migration)\b",
 "Java estate visibility or modernization need": r"\b(dead code|unused(?:\s+\w+){0,3}\s+code|application moderni[sz]|java estate|jvm inventory|technical debt)\b",
}

def heuristic_extract(segments: list[Segment]) -> list[Observation]:
    out=[]
    for label, pattern in PATTERNS.items():
        ids=[s.id for s in segments if re.search(pattern,s.text,re.I)][:3]
        if ids: out.append(Observation(statement=label+" appears in public materials.",segment_ids=ids))
    return out

def llm_extract(segments: list[Segment], model: str|None=None) -> list[Observation]:
    from openai import OpenAI
    payload=[{"id":s.id,"text":s.text[:1200]} for s in segments[:30]]
    prompt="""Extract only decision-relevant, explicit account observations. Return JSON object
{\"observations\":[{\"statement\":str,\"segment_ids\":[str]}]}. Every statement must be directly
supported by the referenced segment text. Do not infer product fit, company-wide adoption, pain,
budgets, or intent. Use only IDs supplied below. Prefer 0-6 high-quality observations.\n"""+json.dumps(payload)
    r=OpenAI().responses.create(model=model or os.getenv("OPENAI_MODEL","gpt-4.1-mini"),input=prompt)
    raw=r.output_text.strip().removeprefix("```json").removesuffix("```").strip()
    return [Observation.model_validate(x) for x in json.loads(raw).get("observations",[])]

def baseline_naive_summary(segments:list[Segment]) -> str:
    """Intentionally naive comparator: no citations or claim validation."""
    hits=heuristic_extract(segments)
    if not hits: return "This account may benefit from Azul's Java portfolio."
    return "The account likely has enterprise Java needs and should consider Azul products."
