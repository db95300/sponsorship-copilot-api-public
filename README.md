# Sponsorship Copilot API (On‑Prem GenAI + Postgres + FastAPI)

A **sellable, demo-ready POC** that generates a structured **sponsorship outreach pack** for an athlete ↔ sponsor pairing:

- Fit score + explanations  
- Talking points grounded in internal “evidence” documents  
- Outreach email (EN/FR)  
- One‑pager (Markdown)  
- Offer tiers + measurement plan + recommended media slots  
- Optional **on‑prem LLM** generation via **Ollama** (fallback-safe)

---

## 1) What’s inside

**Backend**
- FastAPI app (Python)
- SQLAlchemy + Postgres
- Fake data seeder (`/seed`)
- Outreach pack generator (`/outreach-pack`)
- Optional Ollama LLM client (on‑prem)

**Infra**
- Postgres in Docker Compose
- Local dev runner via `uv` + `make`

---

## 2) Prerequisites

### Required
- **Docker Desktop** (includes Docker Compose)
- **Homebrew** (macOS package manager)
- **Python 3.11+**
- **uv** (Python package manager/runner)

### Optional (On‑prem GenAI)
- **Ollama** + a local model (e.g. `qwen2.5:7b`)

---

## 3) One-time setup (macOS)

### 3.1 Install Homebrew (if needed)
See Homebrew docs, then verify:
```bash
brew --version
```

### 3.2 Install `uv`
```bash
brew install uv
uv --version
```

### 3.3 Install / verify Docker
Install Docker Desktop, then verify:
```bash
docker --version
docker compose version
```

---

## 4) Project setup (in order)

> Run everything from the repository root.

### 4.1 Create the virtual environment + install dependencies
```bash
make init
```

If you don’t have `make` targets yet, the equivalent is usually:
```bash
uv sync
```

### 4.2 Configure environment variables
Create a `.env` file in the repo root.

Minimal required:
```env
COPILOT_ENV=local
COPILOT_LOG_LEVEL=INFO
COPILOT_DATABASE_URL=postgresql+psycopg://app:app@127.0.0.1:5432/copilot
```

Enable **on‑prem LLM** (optional):
```env
COPILOT_GENERATION_MODE=llm
COPILOT_LLM_PROVIDER=ollama
COPILOT_OLLAMA_BASE_URL=http://127.0.0.1:11434
COPILOT_OLLAMA_MODEL=qwen2.5:7b
COPILOT_OLLAMA_TEMPERATURE=0.4
```

To force deterministic output (no LLM), set:
```env
COPILOT_GENERATION_MODE=template
```

### 4.3 Start the database (Docker Compose)
```bash
make db-up
```

### 4.4 Run the API (FastAPI)
```bash
make run
```

Your API should be available at:
- Swagger UI: `http://127.0.0.1:8000/docs`
- OpenAPI JSON: `http://127.0.0.1:8000/openapi.json`

---

## 5) On‑prem LLM (Ollama) setup (optional but recommended)

### 5.1 Install Ollama
```bash
brew install ollama
```

### 5.2 Start Ollama
In a terminal:
```bash
ollama serve
```

### 5.3 Pull a model
In another terminal:
```bash
ollama pull qwen2.5:7b
```

If you want a lighter model:
```bash
ollama pull qwen2.5:3b
```

### 5.4 Quick check
```bash
curl http://127.0.0.1:11434/api/tags
```

---

## 6) How to use (demo flow)

### 6.1 Seed fake data
This creates fake athletes, sponsors, documents (evidence), interactions.

**From terminal**
```bash
curl -X POST http://127.0.0.1:8000/seed
```

**From Swagger**
Go to `http://127.0.0.1:8000/docs` → `POST /seed` → Try it out → Execute

### 6.2 Generate an outreach pack (French example)
```bash
curl -s -X POST http://127.0.0.1:8000/outreach-pack \
  -H "Content-Type: application/json" \
  -d '{
    "athlete_id":"ath_001",
    "sponsor_id":"sp_001",
    "locale":"fr-FR",
    "market":"FR",
    "tone":"premium_warm",
    "channel":"email"
  }'
```

### 6.3 Generate an outreach pack (English example)
```bash
curl -s -X POST http://127.0.0.1:8000/outreach-pack \
  -H "Content-Type: application/json" \
  -d '{
    "athlete_id":"ath_001",
    "sponsor_id":"sp_001",
    "locale":"en-GB",
    "market":"UK",
    "tone":"premium_warm",
    "channel":"email"
  }'
```

### 6.4 Print only the email (subject + body)
If `python` is not available on macOS, use `uv run python`:

```bash
curl -s -X POST http://127.0.0.1:8000/outreach-pack \
  -H "Content-Type: application/json" \
  -d '{"athlete_id":"ath_001","sponsor_id":"sp_001","locale":"fr-FR","market":"FR","tone":"premium_warm","channel":"email"}' \
| uv run python -c "import sys, json; d=json.load(sys.stdin); print('SUBJECT:\n'+d['email_outreach']['subject']+'\n\nBODY:\n'+d['email_outreach']['body'])"
```

---

## 7) Verify Postgres data (optional)

### 7.1 Open psql in the DB container
```bash
docker compose exec db psql -U app -d copilot
```

### 7.2 Useful commands
```sql
\dt
SELECT COUNT(*) FROM athletes;
SELECT COUNT(*) FROM sponsors;
SELECT COUNT(*) FROM documents;
SELECT COUNT(*) FROM interactions;
```

---

## 8) How the LLM integration works (important)

The system supports two modes:

### Template mode (deterministic)
- `COPILOT_GENERATION_MODE=template`
- Always produces predictable output
- Great for stable demos and tests

### LLM mode (on‑prem)
- `COPILOT_GENERATION_MODE=llm`
- Uses Ollama locally to generate:
  - `email_outreach` (subject/body)
  - `one_pager_markdown`
- If Ollama is unavailable or returns invalid JSON:
  - **automatic fallback** to template output (demo-safe)

---
---

## Project structure (arborescence)

> This is the **recommended** structure (your repo may include extra files).  
> Key folders are highlighted with short explanations.

```text
sponsorship-copilot-api/
├─ backend/
│  └─ app/
│     ├─ api/
│     │  └─ routes/
│     │     ├─ health.py            # GET /health
│     │     ├─ seed.py              # POST /seed (fake data)
│     │     └─ outreach.py          # POST /outreach-pack (main endpoint)
│     ├─ core/
│     │  └─ config.py               # Pydantic settings (.env, COPILOT_*)
│     ├─ db/
│     │  └─ session.py              # SQLAlchemy engine/session
│     ├─ schemas.py                 # Pydantic request/response models
│     ├─ services/
│     │  ├─ outreach_pack.py        # pack generation (template + optional LLM override)
│     │  ├─ llm_client.py           # Ollama client (on-prem JSON generation)
│     │  └─ seed_fake_data.py       # fake data generation logic
│     └─ main.py                    # FastAPI app wiring + routers
├─ docker-compose.yml               # Postgres container
├─ Makefile                         # make init / db-up / run / stop / lint / fmt ...
├─ .env                             # local config (NOT committed)
├─ .gitignore
└─ Sponsorship_Copilot_Walkthrough.ipynb
```

### Where the “magic” happens
- **`backend/app/services/outreach_pack.py`**
  - builds the full pack (fit_score, evidence, offer tiers, etc.)
  - creates **deterministic template** email/one-pager first
  - if `COPILOT_GENERATION_MODE=llm`, calls Ollama to **override** email/one-pager
  - if LLM fails → **falls back** to templates (demo-safe)

- **`backend/app/services/llm_client.py`**
  - one responsibility: call the local Ollama HTTP API and return JSON
  - returns structured JSON only (subject/body/one_pager_markdown)

- **`backend/app/api/routes/outreach.py`**
  - exposes `/outreach-pack`
  - maps internal objects into the final Pydantic response shape

---

## What works best (recommended settings & workflow)

### Recommended local workflow (fast iteration)
1) Start DB once
```bash
make db-up
```

2) Run API in reload mode
```bash
make run
```

3) Use Swagger for quick iteration
- `http://127.0.0.1:8000/docs`

4) Use `curl` for copy/paste demo scripts
- best for README + “how to demo” instructions

---

### Best “demo-safe” configuration (recommended for presentations)
Use deterministic templates (no LLM surprises):

```env
COPILOT_GENERATION_MODE=template
```

Why it’s best:
- output is stable (same input → same output)
- no dependency on Ollama/model availability
- perfect for live demos

---

### Best “agency-grade writing” configuration (recommended when you want higher quality)
Enable on-prem LLM:

```env
COPILOT_GENERATION_MODE=llm
COPILOT_LLM_PROVIDER=ollama
COPILOT_OLLAMA_BASE_URL=http://127.0.0.1:11434
COPILOT_OLLAMA_MODEL=qwen2.5:7b
COPILOT_OLLAMA_TEMPERATURE=0.4
```

Why it’s best:
- richer language, better flow, less “template vibe”
- still **safe**, because the system keeps templates as fallback

---

### Which Ollama model works best here?

**Default recommendation:** `qwen2.5:7b`  
- good balance of quality vs speed for EN/FR business writing

**If you want faster / lighter:** `qwen2.5:3b`  
- faster, smaller download
- slightly less strong writing

Tip: keep temperature low (`0.3–0.5`) for professional tone and consistency.

---

### How to tell if LLM mode is active
Call `/outreach-pack` twice with the same payload:
- if subject/body differs a bit → LLM is likely active
- if identical → template mode or LLM fallback

---

### Best practices (to keep the repo clean & pro)
- Keep **only one** LLM client file: `llm_client.py` (avoid duplicates like `llm_clients.py`)
- Always have **one return** at the end of `build_outreach_pack()` (prevents `UnboundLocalError`)
- Treat LLM output as “untrusted”:
  - validate JSON
  - fallback to templates when invalid
- Keep `.env` out of git (already in `.gitignore`)

---



## 9) Common issues & fixes

### 9.1 `Address already in use` (port 8000)
```bash
lsof -nP -iTCP:8000 -sTCP:LISTEN
kill -9 <PID>
```

### 9.2 zsh error: `no matches found: psycopg[binary]`
Quote extras:
```bash
uv add "psycopg[binary]" "uvicorn[standard]"
```

### 9.3 Missing `.env` / pydantic settings error (e.g. `database_url Field required`)
- Ensure `.env` exists at repo root
- Ensure your config loads it with:
  - `env_prefix="COPILOT_"`
  - `env_file=".env"`

### 9.4 Ollama not responding
- Make sure Ollama is running:
  ```bash
  ollama serve
  ```
- Verify:
  ```bash
  curl http://127.0.0.1:11434/api/tags
  ```

---

## 10) Recommended next steps (product-grade roadmap)

1) **RAG / embeddings** (pgvector)  
   - embed documents and retrieve top-k relevant evidence instead of random picks

2) **Orchestration**  
   - planner → writer → critic loop with strict JSON schema validation

3) **Media assets**  
   - store past campaigns / images / brand guidelines as assets to enrich packs

4) **Exports**  
   - HTML email export
   - PDF one‑pager export
   - store generated packs in DB to share/reuse

---

## 11) Notebook demo

A full walkthrough notebook is included/generated:

- `Sponsorship_Copilot_Walkthrough.ipynb`

It demonstrates:
- health check
- seeding
- generating packs
- extracting email + one pager
- verifying LLM mode
- optional Postgres queries
