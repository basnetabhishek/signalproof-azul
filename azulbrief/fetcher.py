import ipaddress, re, socket
from urllib.parse import urljoin
import httpx
from .models import Source
from .segmenter import clean_html

PATHS = [("company", "/"), ("careers", "/careers"), ("engineering", "/engineering"),
         ("technology", "/technology"), ("jobs", "/jobs")]

def normalize_domain(domain: str) -> str:
    domain = re.sub(r"^https?://", "", domain.strip()).strip("/")
    if not re.fullmatch(r"[A-Za-z0-9.-]+(?::\d+)?", domain):
        raise ValueError("Enter a valid domain, without a path.")
    return domain.lower()

def ensure_public_domain(domain: str) -> None:
    host=domain.split(":",1)[0]
    if host in {"localhost","localhost.localdomain"} or host.endswith((".local",".internal")):
        raise ValueError("Private or local domains are not allowed.")
    try:
        addresses={x[4][0] for x in socket.getaddrinfo(host,None)}
    except socket.gaierror as exc:
        raise ValueError("Domain could not be resolved.") from exc
    if not addresses or any(not ipaddress.ip_address(x).is_global for x in addresses):
        raise ValueError("Domain must resolve only to public internet addresses.")

def fetch_sources(domain: str, browser_fallback: bool = False) -> list[Source]:
    domain = normalize_domain(domain); ensure_public_domain(domain); base = f"https://{domain}"
    results = []
    headers = {"User-Agent": "AzulEvidenceBrief/0.1 (portfolio research; public pages only)"}
    with httpx.Client(headers=headers, timeout=10, follow_redirects=True) as client:
        for kind, path in PATHS:
            url = urljoin(base, path)
            try:
                r = client.get(url)
                if r.status_code == 200 and "text/html" in r.headers.get("content-type", ""):
                    text = clean_html(r.text)
                    if len(text) >= 120:
                        match = re.search(r"<title[^>]*>(.*?)</title>", r.text, re.I|re.S)
                        title = re.sub(r"\s+", " ", match.group(1)).strip() if match else url
                        results.append(Source(url=str(r.url), title=title,
                                              source_type=kind, text=text))
            except httpx.HTTPError: pass
    if not results and browser_fallback:
        try:
            from playwright.sync_api import sync_playwright
            with sync_playwright() as p:
                b = p.chromium.launch(headless=True); page = b.new_page()
                for kind, path in PATHS[:3]:
                    try:
                        page.goto(urljoin(base, path), wait_until="domcontentloaded", timeout=15000)
                        text = clean_html(page.content())
                        if len(text) >= 120:
                            results.append(Source(url=page.url, title=page.title(), source_type=kind, text=text))
                    except Exception: pass
                b.close()
        except (ImportError, Exception): pass
    return results
