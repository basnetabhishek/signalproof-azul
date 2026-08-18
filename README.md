# SignalProof / Azul

An evidence-grounded account-to-campaign briefing MVP built as a portfolio project for applied AI in enterprise marketing. It turns public company pages plus **clearly labeled mock CRM/intent context** into a reviewable Azul product hypothesis—or returns **INSUFFICIENT** when the evidence cannot support one.

This is an independent portfolio project. It is not an Azul product and is not affiliated with Azul Systems.

## Why this exists

Account research is easy to summarize and hard to trust. A conventional LLM can collapse a weak public mention, an intent signal, and product copy into a confident sales claim. SignalProof treats traceability and refusal as product features:

1. Fetch a small, intentional set of public company, careers, engineering, technology, and jobs pages.
2. Clean and deterministically segment text. IDs include URL and content hashes, so citations are stable and changes are visible.
3. Extract observations that may reference only supplied segment IDs.
4. Validate every ID in the backend and retrieve the exact source text from SQLite.
5. Retrieve relevant product evidence from a small official Azul corpus using BM25.
6. Apply deterministic confidence and post-generation guardrails.
7. Require a human to approve, edit, or reject. Approval can call a Zapier-compatible webhook; nothing auto-publishes.

## Run locally

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
streamlit run app.py
```

The default mode is deterministic and needs no API key. Copy `.env.example` values into your environment to use an LLM or approval webhook. The interface does not automatically load `.env` files.

Optional JavaScript-rendered page fallback:

```powershell
pip install -e ".[browser]"
playwright install chromium
```

Optional API:

```powershell
uvicorn api:app --reload
```

## Deploy on Vercel from GitHub

The repository contains two interfaces:

- `app.py`: the richer local Streamlit review UI.
- `public/index.html` + `api.py`: the Vercel-hosted browser UI and FastAPI function.

Push the repository to GitHub, open [Vercel's new project page](https://vercel.com/new), import the repository, and deploy with the default settings. Vercel detects the `api:app` entry point from `pyproject.toml`; no build command or output directory is needed.

Optional Vercel environment variables:

- `OPENAI_API_KEY` and `OPENAI_MODEL` enable constrained LLM extraction.
- `APPROVAL_WEBHOOK_URL` enables approved-brief delivery to Zapier.

The hosted SQLite database uses Vercel's temporary `/tmp` filesystem. It can support one request's evidence validation, but it is **not durable audit storage** and may disappear between function instances. For a production version, replace it with managed Postgres or another durable store. The local Streamlit version continues to use `data/evidence.db`.

Vercel runs FastAPI as a serverless function. Playwright fallback is intentionally disabled in the hosted browser interface; static fetching remains available.

## Evaluation and tests

```powershell
pytest
python evaluation/run_eval.py
```

The offline benchmark contains 18 synthetic company-page fixtures and manually defined labels. It reports extraction precision/recall, attribution accuracy, unsupported-claim rate, insufficient-evidence agreement, BM25 retrieval precision@3, and product-fit agreement. It also exposes the deliberately naive baseline's unsupported-claim behavior on negative cases. These fixtures make the harness reproducible; they do **not** claim real-world production performance. Replace them with dated, manually reviewed public-page snapshots for a stronger study.

## Guardrails

- Account observations without valid segment IDs are removed.
- Product hypotheses without valid Azul corpus IDs are removed.
- Mock CRM/intent fields are displayed as context but never promoted to verified public evidence.
- Certainty language and invented ROI/performance promises cause the draft to be withheld.
- Confidence is deterministic: no evidence/retrieval → INSUFFICIENT; one supported signal → LOW; two → MEDIUM; three across multiple sources → HIGH.
- Review is mandatory and approvals are logged before any optional webhook call.

## Public Azul corpus

The compact corpus in `data/azul_corpus.json` is paraphrased from official public pages for [Azul Core](https://www.azul.com/products/core/), [Azul Prime](https://www.azul.com/products/prime/faq/), [why Prime differs](https://www.azul.com/tutorials/why-is-prime-different/), and [Azul Intelligence Cloud](https://docs.azul.com/intelligence-cloud/about/what-is-azul-intelligence-cloud). Each record retains its source URL and corpus ID. Product claims must cite one of these records.

## Deliberate scope boundaries

No graph database, LangGraph, multi-agent orchestration, production authentication, Salesforce/Marketo/6sense connection, embeddings dependency, or automated publishing. Static fetching is primary; browser rendering is optional. BM25 is interpretable and sufficient for the six-item corpus. Real deployments would need robots/terms review, rate limiting, source freshness policies, PII controls, stronger claim-level entailment checks, adversarial evaluation, access control, and monitoring.

## Layout

`app.py` review UI · `api.py` optional API · `azulbrief/` pipeline · `data/` corpus/database · `evaluation/` benchmark · `tests/` reliability tests.
