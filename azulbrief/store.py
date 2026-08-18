import json, os, sqlite3
from pathlib import Path
from .models import Segment, Brief

SCHEMA = """
CREATE TABLE IF NOT EXISTS segments(id TEXT PRIMARY KEY,url TEXT,title TEXT,source_type TEXT,text TEXT,fetched_at TEXT DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE IF NOT EXISTS briefs(id INTEGER PRIMARY KEY AUTOINCREMENT,domain TEXT,status TEXT,brief_json TEXT,created_at TEXT DEFAULT CURRENT_TIMESTAMP,reviewed_at TEXT);
"""
class EvidenceStore:
    def __init__(self, path: str | None = None):
        default = "/tmp/evidence.db" if os.getenv("VERCEL") else "data/evidence.db"
        self.path = path or os.getenv("AZUL_DB_PATH", default)
        Path(self.path).parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(self.path) as c: c.executescript(SCHEMA)
    def save_segments(self, segments: list[Segment]):
        with sqlite3.connect(self.path) as c:
            c.executemany("INSERT OR REPLACE INTO segments(id,url,title,source_type,text) VALUES(?,?,?,?,?)",
                [(s.id,s.url,s.title,s.source_type,s.text) for s in segments])
    def exact_text(self, ids: list[str]) -> dict[str,str]:
        if not ids: return {}
        q = ",".join("?"*len(ids))
        with sqlite3.connect(self.path) as c:
            return dict(c.execute(f"SELECT id,text FROM segments WHERE id IN ({q})", ids).fetchall())
    def save_brief(self, brief: Brief, status="draft") -> int:
        with sqlite3.connect(self.path) as c:
            cur=c.execute("INSERT INTO briefs(domain,status,brief_json) VALUES(?,?,?)",(brief.company_domain,status,brief.model_dump_json()))
            return cur.lastrowid
    def review(self, brief_id:int, status:str, brief:Brief|None=None):
        if status not in {"approved","edited","rejected"}: raise ValueError("Invalid status")
        with sqlite3.connect(self.path) as c:
            if brief: c.execute("UPDATE briefs SET status=?,brief_json=?,reviewed_at=CURRENT_TIMESTAMP WHERE id=?",(status,brief.model_dump_json(),brief_id))
            else: c.execute("UPDATE briefs SET status=?,reviewed_at=CURRENT_TIMESTAMP WHERE id=?",(status,brief_id))
