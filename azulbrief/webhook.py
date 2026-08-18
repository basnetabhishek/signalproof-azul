import os, httpx
from .models import Brief
def send_approval(brief_id:int, brief:Brief, url:str|None=None):
    target=url or os.getenv("APPROVAL_WEBHOOK_URL")
    if not target: return {"sent":False,"reason":"APPROVAL_WEBHOOK_URL is not configured"}
    payload={"event":"brief.approved","brief_id":brief_id,"domain":brief.company_domain,
             "confidence":brief.confidence,"product":brief.product_hypothesis.product if brief.product_hypothesis else None,
             "campaign_angle":brief.campaign_angle,"draft_messaging":brief.draft_messaging}
    r=httpx.post(target,json=payload,timeout=10); r.raise_for_status()
    return {"sent":True,"status_code":r.status_code}

