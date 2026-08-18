"""Offline, deterministic evaluation over curated synthetic company-page fixtures."""
import json
from pathlib import Path
from statistics import mean
from azulbrief.models import Source
from azulbrief.segmenter import segment_sources
from azulbrief.extractor import heuristic_extract, baseline_naive_summary
from azulbrief.retrieval import ProductRetriever

def choose_product(labels):
    joined=" ".join(labels)
    if "licensing or migration" in joined: return "Azul Platform Core"
    if "Performance or latency" in joined: return "Azul Platform Prime"
    if "visibility or modernization" in joined: return "Azul Intelligence Cloud"
    if "Java runtime evidence" in joined: return "Azul Platform Core"

def run():
    cases=json.loads(Path("evaluation/benchmark.json").read_text())
    rows=[]
    totals={"tp":0,"fp":0,"fn":0,"attribution":[],"unsupported":[],"insufficient":[],"retrieval":[],"fit":[],"baseline_unsupported":[]}
    retriever=ProductRetriever()
    for n,c in enumerate(cases):
        source=Source(url=f"https://fixture.local/{n}",title=c["company"],source_type="fixture",text=c["text"])
        segs=segment_sources([source]); obs=heuristic_extract(segs); got=[o.statement.removesuffix(" appears in public materials.") for o in obs]
        exp=set(c["expected_signals"]); actual=set(got)
        totals["tp"]+=len(exp&actual); totals["fp"]+=len(actual-exp); totals["fn"]+=len(exp-actual)
        totals["attribution"].append(all(set(o.segment_ids)<={s.id for s in segs} for o in obs))
        totals["unsupported"].append(sum(not o.segment_ids for o in obs)/max(1,len(obs)))
        totals["insufficient"].append((not obs)==(not exp))
        query=" ".join(c["text"]+" "+x for x in got); retrieved=retriever.search(query,3)
        totals["retrieval"].append(any(d["product"]==c["expected_product"] for d in retrieved) if c["expected_product"] else True)
        predicted=choose_product(got); totals["fit"].append(predicted==c["expected_product"])
        totals["baseline_unsupported"].append(1.0 if not exp and "benefit" in baseline_naive_summary(segs) else 0.0)
        rows.append({"company":c["company"],"signals":got,"expected":list(exp),"product":predicted,"expected_product":c["expected_product"]})
    precision=totals["tp"]/max(1,totals["tp"]+totals["fp"])
    report={"cases":len(cases),"extraction_precision":precision,"extraction_recall":totals["tp"]/max(1,totals["tp"]+totals["fn"]),
      "attribution_accuracy":mean(totals["attribution"]),"unsupported_claim_rate":mean(totals["unsupported"]),
      "naive_baseline_unsupported_rate_on_negative_cases":sum(totals["baseline_unsupported"])/sum(not c["expected_signals"] for c in cases),
      "insufficient_evidence_agreement":mean(totals["insufficient"]),"retrieval_precision_at_3":mean(totals["retrieval"]),
      "product_fit_agreement":mean(totals["fit"]),"details":rows,
      "notes":"Synthetic fixtures and manually defined labels; not a claim of production performance."}
    Path("evaluation/results.json").write_text(json.dumps(report,indent=2)); print(json.dumps(report,indent=2))
if __name__=="__main__": run()

