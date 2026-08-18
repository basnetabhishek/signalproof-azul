import hashlib, re
from html import unescape
from .models import Source, Segment

def clean_html(html: str) -> str:
    html = re.sub(r"<(script|style|nav|footer|form|noscript|svg)\b[^>]*>.*?</\1>", " ", html, flags=re.I|re.S)
    html = re.sub(r"</(?:p|div|section|article|h[1-6]|li|br)\s*>", "\n", html, flags=re.I)
    text = unescape(re.sub(r"<[^>]+>", " ", html))
    lines = [re.sub(r"\s+", " ", x).strip() for x in text.splitlines()]
    return "\n".join(dict.fromkeys(x for x in lines if len(x) > 30))

def segment_sources(sources: list[Source], max_chars: int = 900) -> list[Segment]:
    out = []
    for source in sources:
        paragraphs = [p.strip() for p in source.text.split("\n") if p.strip()]
        chunks, buf = [], ""
        for p in paragraphs:
            if buf and len(buf) + len(p) + 1 > max_chars:
                chunks.append(buf); buf = p
            else: buf = f"{buf}\n{p}".strip()
        if buf: chunks.append(buf)
        url_hash = hashlib.sha256(source.url.encode()).hexdigest()[:8].upper()
        for i, text in enumerate(chunks, 1):
            content_hash = hashlib.sha256(text.encode()).hexdigest()[:8].upper()
            out.append(Segment(id=f"SEG-{url_hash}-{i:03d}-{content_hash}", url=source.url,
                title=source.title, source_type=source.source_type, text=text))
    return out
