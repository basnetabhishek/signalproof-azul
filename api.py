from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from typing import Literal
from azulbrief.models import AnalyzeRequest, Brief
from azulbrief.pipeline import build_brief
from azulbrief.store import EvidenceStore
from azulbrief.webhook import send_approval

app=FastAPI(title="Azul Evidence Brief API",version="0.1.0")
@app.get("/",include_in_schema=False)
def home(): return RedirectResponse("/index.html")
@app.get("/health")
def health(): return {"status":"ok"}
@app.post("/analyze")
def analyze(req:AnalyzeRequest):
    brief,segments,brief_id=build_brief(req)
    return {"brief_id":brief_id,"brief":brief,"segments":segments}
class ReviewRequest(BaseModel):
    brief: Brief
    decision: Literal["approved","edited","rejected"]

@app.post("/briefs/{brief_id}/review")
def review(brief_id:int, req:ReviewRequest):
    # Hosted SQLite is transient; the full reviewed brief is accepted and logged per invocation.
    EvidenceStore().review(brief_id,req.decision,req.brief)
    webhook=send_approval(brief_id,req.brief) if req.decision=="approved" else {"sent":False,"reason":"No webhook for this decision"}
    return {"saved":True,"decision":req.decision,"webhook":webhook}
