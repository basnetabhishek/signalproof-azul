import json
import streamlit as st
from azulbrief.models import AnalyzeRequest, MockSignals, Brief
from azulbrief.pipeline import build_brief
from azulbrief.store import EvidenceStore
from azulbrief.webhook import send_approval

st.set_page_config(page_title="SignalProof · Azul",page_icon="◈",layout="wide")
st.markdown("""<style>
.stApp{background:#07141d;color:#e9f3f5}.block-container{max-width:1280px;padding-top:2rem}
[data-testid=stSidebar]{background:#0b1d28}.hero{padding:26px 30px;border:1px solid #24404c;border-radius:18px;background:linear-gradient(130deg,#0c2430,#102d38)}
.eyebrow{color:#58d3c4;font-size:.78rem;letter-spacing:.13em;text-transform:uppercase}.hero h1{font-size:2.45rem;margin:.25rem 0}.muted{color:#9db0b8}
.pill{display:inline-block;padding:5px 10px;border-radius:99px;background:#173847;color:#93e8dc;font-size:.78rem;margin-right:6px}
.evidence{padding:16px;border-left:4px solid #42c8b5;background:#102732;border-radius:6px;margin:10px 0}.limit{padding:12px 14px;background:#302619;border:1px solid #765c2a;border-radius:8px;margin:7px 0;color:#f4dca6}
.blocked{padding:12px 14px;background:#321c21;border:1px solid #74313d;border-radius:8px;color:#ffc1c9}
</style>""",unsafe_allow_html=True)
st.markdown("""<div class='hero'><div class='eyebrow'>Evidence-grounded campaign intelligence</div>
<h1>SignalProof <span style='color:#58d3c4'>/ Azul</span></h1>
<p class='muted'>Turn public account signals into a traceable product hypothesis—or stop when the evidence is not enough.</p>
<span class='pill'>Human review required</span><span class='pill'>No autonomous publishing</span><span class='pill'>Mock CRM data</span></div>""",unsafe_allow_html=True)

with st.sidebar:
    st.header("Account input")
    domain=st.text_input("Company domain",placeholder="example.com")
    stage=st.selectbox("Mock CRM stage",["Target","Awareness","Engaged","Qualified"])
    topics=st.multiselect("Mock intent topics",["Java","OpenJDK","Oracle Java","Application performance","Cloud cost","Application modernization","Software security"])
    notes=st.text_area("Mock engagement notes",placeholder="Clearly labeled mock data—not evidence")
    use_llm=st.toggle("Use configured LLM",help="Falls back to deterministic extraction when no API key is present.")
    browser=st.toggle("Browser fallback",help="Requires the optional Playwright install.")
    run=st.button("Build evidence brief",type="primary",use_container_width=True)

if run:
    try:
        with st.spinner("Collecting and validating public evidence…"):
            req=AnalyzeRequest(domain=domain,mock_signals=MockSignals(account_stage=stage,intent_topics=topics,engagement_notes=notes),use_llm=use_llm,allow_browser_fallback=browser)
            st.session_state.result=build_brief(req)
    except Exception as e: st.error(f"Analysis could not be completed: {e}")

if "result" not in st.session_state:
    st.info("Enter a company domain to begin. For a reliable demo without live web access, run the included evaluation harness.")
else:
    brief,segments,brief_id=st.session_state.result
    a,b,c,d=st.columns(4)
    a.metric("Confidence",brief.confidence); b.metric("Verified observations",len(brief.observations)); c.metric("Public pages",len({s.url for s in segments})); d.metric("Blocked claims",len(brief.blocked_reasons))
    left,right=st.columns([1.6,1],gap="large")
    with left:
        st.subheader("Verified observations")
        if not brief.observations: st.warning("Insufficient evidence: no supported account observations passed validation.")
        exact=EvidenceStore().exact_text([x for o in brief.observations for x in o.segment_ids])
        by_id={s.id:s for s in segments}
        for i,o in enumerate(brief.observations,1):
            st.markdown(f"**{i}. {o.statement}**")
            for sid in o.segment_ids:
                seg=by_id.get(sid)
                with st.expander(f"{sid} · {seg.source_type if seg else 'source'}"):
                    st.write(exact.get(sid,"Evidence unavailable"));
                    if seg: st.caption(seg.url)
        st.subheader("Product hypothesis")
        if brief.product_hypothesis:
            st.markdown(f"### {brief.product_hypothesis.product}")
            st.write(brief.product_hypothesis.rationale)
            for cid in brief.product_hypothesis.corpus_ids:
                with st.expander(f"Azul support · {cid}"): st.write(brief.retrieved_product_evidence.get(cid))
        else: st.info("No product recommendation was produced.")
        st.subheader("Campaign angle"); st.write(brief.campaign_angle)
        st.subheader("Draft messaging")
        edited=st.text_area("Human-editable draft",brief.draft_messaging,height=120,label_visibility="collapsed")
    with right:
        st.subheader("Limitations")
        for x in brief.limitations: st.markdown(f"<div class='limit'>{x}</div>",unsafe_allow_html=True)
        if brief.blocked_reasons:
            st.subheader("Guardrail actions")
            for x in brief.blocked_reasons: st.markdown(f"<div class='blocked'>{x}</div>",unsafe_allow_html=True)
        st.subheader("Mock context")
        st.json(brief.mock_signals.model_dump())
        st.caption("Mock CRM/intent fields influence context only; they never count as verified public evidence.")
        st.subheader("Review decision")
        col1,col2,col3=st.columns(3)
        if col1.button("Approve",type="primary"):
            brief.draft_messaging=edited; EvidenceStore().review(brief_id,"approved",brief)
            st.success("Approved. "+send_approval(brief_id,brief).get("reason","Webhook sent."))
        if col2.button("Save edit"):
            brief.draft_messaging=edited; EvidenceStore().review(brief_id,"edited",brief); st.success("Edited draft saved.")
        if col3.button("Reject"):
            EvidenceStore().review(brief_id,"rejected"); st.warning("Brief rejected; nothing was published.")
        st.download_button("Download audit JSON",brief.model_dump_json(indent=2),f"{brief.company_domain}-brief.json","application/json",use_container_width=True)

