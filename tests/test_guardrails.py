from azulbrief.models import *
from azulbrief.guardrails import validate_brief
def fixture_brief(obs, draft="Could we explore this hypothesis?"):
    return Brief(company_domain="example.com",observations=obs,limitations=[],campaign_angle="Explore",
      draft_messaging=draft,mock_signals=MockSignals())
def test_invalid_segment_claim_is_blocked():
    b=validate_brief(fixture_brief([Observation(statement="Uses Java",segment_ids=["FAKE"])]),[],{})
    assert not b.observations and b.blocked_reasons
def test_guarantee_is_withheld():
    b=validate_brief(fixture_brief([],"This will save 50% faster."),[],{})
    assert b.draft_messaging=="" and b.blocked_reasons

