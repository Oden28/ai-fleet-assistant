# Powerfleet AI Fleet Intelligence

A production-minded **AI fleet management platform** combining real-time fleet monitoring, operational analytics, and an AI copilot for natural-language querying over documentation and structured data.

The system has three layers:

| Layer | Technology | Purpose |
|---|---|---|
| **AI Pipelines** | Python (Router + RAG + Pandas) | Intent classification, doc retrieval, data analysis |
| **Backend API** | FastAPI + Uvicorn | REST + WebSocket endpoints serving pipelines & fleet data |
| **Frontend** | React + Vite | 10-screen mobile-first dashboard with AI copilot |

---

## Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+
- An OpenAI API key (GPT-4o)

### 1. Backend Setup

```bash
# Install Python dependencies
pip install -r requirements.txt

# Configure your API key
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY

# Start the API server
python -m uvicorn api.server:app --reload --port 8000
```

The API server will load the embedding model, index documentation into ChromaDB, and serve at `http://localhost:8000`. Swagger docs at `/api/docs`.

### 2. Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

The frontend dev server starts at `http://localhost:5173` (or next available port).

### 3. CLI Mode (Optional)

The original CLI is still available:

```bash
# Interactive mode
python -m src.main interactive

# Single question
python -m src.main ask "What does error code E104 mean?"

# Batch mode — run all seed questions
python -m src.main batch

# Verbose — show reasoning artefacts
python -m src.main interactive -v
```

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                      React Frontend (Vite)                      │
│  Login │ Dashboard │ Map │ Vehicles │ Alerts │ AI Copilot │ ... │
└────────────────────────────┬────────────────────────────────────┘
                             │ REST / WebSocket
┌────────────────────────────▼────────────────────────────────────┐
│                     FastAPI Backend (api/)                       │
│                                                                  │
│  AI Endpoints                    Fleet Data Endpoints            │
│  ─────────────                   ─────────────────────           │
│  POST /api/ask                   GET /api/fleet/summary          │
│  POST /api/query-docs            GET /api/fleet/vehicles         │
│  POST /api/query-data            GET /api/fleet/vehicles/{id}    │
│  WS   /api/ws/copilot            GET /api/fleet/alerts           │
│                                  GET /api/fleet/metrics          │
│                                  GET /api/fleet/maintenance      │
│                                  GET /api/fleet/drivers          │
│                                  GET /api/fleet/reports/fuel     │
└────────────────────────────┬────────────────────────────────────┘
                             │ imports
┌────────────────────────────▼────────────────────────────────────┐
│                    AI Pipeline Layer (src/)                      │
│                                                                  │
│  Router ──┬── DocPipeline (RAG: ChromaDB + sentence-transformers)│
│           ├── DataPipeline (Pandas code gen + sandboxed exec)    │
│           ├── HybridPipeline (both + synthesis)                  │
│           └── ClarificationHandler                               │
│                                                                  │
│  Preprocessor ── FleetData (assets, metrics, alerts DataFrames)  │
└─────────────────────────────────────────────────────────────────┘
```

### Design: Router-Based Orchestration

A single LLM call classifies intent → dispatches to the correct pipeline. Not a full agentic loop.

| Component | Technology | Purpose |
|---|---|---|
| Intent Classifier | GPT-4o (structured JSON) | Routes questions to the right pipeline |
| Doc Pipeline | sentence-transformers + ChromaDB | RAG over 7 markdown documents |
| Data Pipeline | GPT-4o → pandas code gen → sandboxed exec | Structured reasoning over CSV data |
| Clarification Handler | GPT-4o | Generates targeted clarifying questions |

**Why this design:**
1. **Predictability** — single routing step, not multi-hop agent loops
2. **Transparency** — every classification logged with reasoning
3. **Latency** — 1 routing call + 1-2 answering calls
4. **Extensibility** — new pipeline = new intent + handler

---

## Project Structure

```
├── api/                    # FastAPI backend
│   ├── server.py           # App with lifespan, CORS, route mounting
│   ├── schemas.py          # Request/response Pydantic models
│   └── routes/
│       ├── ai.py           # /ask, /query-docs, /query-data, /ws/copilot
│       └── fleet.py        # /fleet/summary, /vehicles, /alerts, etc.
│
├── src/                    # AI pipeline layer (unchanged from assessment)
│   ├── main.py             # CLI entrypoint
│   ├── router.py           # Intent classifier + dispatch
│   ├── doc_pipeline.py     # RAG pipeline (chunk → embed → retrieve → generate)
│   ├── data_pipeline.py    # Pandas code generation pipeline
│   ├── preprocessor.py     # Data loading + cleaning (FleetData)
│   ├── models.py           # Pydantic domain models
│   ├── prompts.py          # All LLM prompt templates
│   └── config.py           # Settings from .env
│
├── frontend/               # React SPA (Vite)
│   └── src/
│       ├── api/client.js   # Fetch wrappers for all API endpoints
│       ├── hooks/          # useFleetData, useCopilot hooks
│       ├── components/     # Layout (BottomNav, TopBar), Charts (Gauge, KPI)
│       ├── pages/          # 10 screens (see below)
│       └── styles/         # Design system (CSS custom properties)
│
├── input/                  # Source data
│   ├── data/               # 3 CSVs (asset_registry, daily_metrics, alerts)
│   ├── docs/               # 7 markdown knowledge base documents
│   └── schema.md           # Data dictionary
│
├── eval/                   # Evaluation suite
│   ├── run_eval.py         # Automated evaluation script
│   └── seed_results.json   # Batch results
│
├── requirements.txt        # Python dependencies
└── .env.example            # Environment variable template
```

---

## Frontend Screens

| Screen | Route | Data Source |
|---|---|---|
| Login / Splash | `/` | Mock auth (localStorage) |
| Dashboard | `/dashboard` | `GET /fleet/summary` + `/fleet/alerts` |
| Live Map | `/map` | `GET /fleet/vehicles` + Leaflet (dark tiles) |
| Vehicles List | `/vehicles` | `GET /fleet/vehicles` (filterable) |
| Vehicle Detail | `/vehicles/:id` | `GET /fleet/vehicles/{id}` |
| Alerts | `/alerts` | `GET /fleet/alerts` (severity tabs) |
| Maintenance | `/maintenance` | `GET /fleet/maintenance` |
| Driver Scorecard | `/drivers` | `GET /fleet/drivers` |
| Reports | `/reports` | `GET /fleet/reports/fuel` + `/fleet/metrics` |
| AI Copilot | `/copilot` | `POST /api/ask` (contextual prompts) |

---

## API Reference

### AI Copilot

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/ask` | Unified question → auto-classifies and routes |
| `POST` | `/api/query-docs` | Direct RAG over documentation |
| `POST` | `/api/query-data` | Direct pandas code generation |
| `WS` | `/api/ws/copilot` | WebSocket for streaming copilot |

**Request body** (`/api/ask`):
```json
{
  "question": "What does error code E104 mean?",
  "context": { "vehicle_id": "A108", "screen": "vehicle_detail" }
}
```

**Response**:
```json
{
  "answer": "Error code E104 indicates ignition voltage instability...",
  "confidence": "high",
  "sources_used": ["error_codes_current.md"],
  "evidence": [{ "source": "...", "excerpt": "...", "authority": "current" }],
  "caveats": ["The legacy document lists a different meaning..."],
  "reasoning_artifacts": [{ "artifact_type": "retrieved_chunks", "content": "..." }],
  "is_clarification": false
}
```

### Fleet Data

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/fleet/summary` | Dashboard KPIs |
| `GET` | `/api/fleet/vehicles` | Vehicle list (`?region=`, `?status=`, `?search=`) |
| `GET` | `/api/fleet/vehicles/{id}` | Vehicle detail + metrics + alert history |
| `GET` | `/api/fleet/alerts` | Alert feed (`?severity=`, `?asset_id=`) |
| `GET` | `/api/fleet/metrics` | Daily metrics (`?asset_id=`, `?date=`) |
| `GET` | `/api/fleet/maintenance` | Maintenance schedule |
| `GET` | `/api/fleet/drivers` | Driver scorecards |
| `GET` | `/api/fleet/reports/fuel` | Fuel efficiency by asset/region |
| `GET` | `/api/health` | Readiness check |

Interactive API docs: `http://localhost:8000/api/docs`

---

## Assumptions

1. **LLM Provider**: Uses OpenAI GPT-4o. Architecture is provider-agnostic — swapping to Claude or Gemini requires only changing the client initialisation.
2. **Relative Time**: Questions with relative references ("yesterday") trigger clarification since the system cannot resolve them without a known current date.
3. **Data Scope**: Only 2 days of metrics data (2026-03-10, 2026-03-11). The system acknowledges this limitation.
4. **Authentication**: Frontend uses mock auth (localStorage flag). No JWT/session auth on the API — add before production.

---

## Trade-Offs

| Decision | Alternative | Rationale |
|---|---|---|
| Router, not agent | LangChain Agent / ReAct | More predictable for 2 pipelines |
| Pandas code gen | Direct LLM over data | Auditable and production-transferable |
| Local embeddings (MiniLM) | OpenAI embeddings | No API cost; sufficient for 7 docs |
| In-memory ChromaDB | Persistent store | Tiny corpus; rebuilt on startup |
| Vanilla CSS | Tailwind | Maximum flexibility, no build deps |
| Leaflet | Google Maps | Free, no API key needed |

---

## Limitations

1. **No conversation memory** — each question is independent
2. **Basic exec() sandbox** — not production-safe; use Docker in prod
3. **Single LLM dependency** — entire system fails if OpenAI API is down
4. **Two days of data** — time-series analysis severely limited
5. **Mock auth** — no real authentication on the API layer
6. **Code gen reliability** — LLM-generated pandas code occasionally fails on complex queries
