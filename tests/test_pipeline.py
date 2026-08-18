from azulbrief.models import AnalyzeRequest, MockSignals, Source
from azulbrief.pipeline import build_brief
from azulbrief.store import EvidenceStore
def test_pipeline_grounded(tmp_path):
    store=EvidenceStore(str(tmp_path/"test.db"))
    src=[Source(url="https://acme.test/engineering",title="Acme",source_type="engineering",text="Our Java services have strict low latency requirements.")]
    brief,segs,_=build_brief(AnalyzeRequest(domain="acme.test",mock_signals=MockSignals()),store,sources=src)
    assert brief.observations
    assert all(x in {s.id for s in segs} for o in brief.observations for x in o.segment_ids)
    assert brief.product_hypothesis is not None
def test_insufficient_path(tmp_path):
    store=EvidenceStore(str(tmp_path/"test.db"))
    src=[Source(url="https://acme.test",title="Acme",source_type="company",text="We sell handmade furniture to local customers.")]
    brief,_,_=build_brief(AnalyzeRequest(domain="acme.test"),store,sources=src)
    assert brief.confidence=="INSUFFICIENT" and brief.product_hypothesis is None

