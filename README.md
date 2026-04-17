# Powerfleet AI Fleet Assistant

A minimal, production-minded AI assistant for fleet and asset management that handles technical support questions and structured data analysis.

## Quick Start

### Prerequisites
- Python 3.11+
- An OpenAI API key (GPT-4o)

### Setup
```bash
# 1. Create and activate a virtual environment
python -m venv venv
source venv/bin/activate  # macOS/Linux

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure your API key
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY

# 4. Run the assistant
python -m src.main interactive
```

### Usage Modes

```bash
# Interactive mode — ask questions one at a time
python -m src.main interactive

# Single question
python -m src.main ask "What does error code E104 mean?"

# Single question with JSON output
python -m src.main ask -j "Which 5 assets had the highest idle time on 2026-03-11?"

# Batch mode — run all seed questions, save results
python -m src.main batch

# Verbose mode — show reasoning artefacts (generated code, retrieved chunks)
python -m src.main interactive -v

# Run evaluation suite
python -m eval.run_eval
```

---

## Architecture Overview

### Design: Router-Based Orchestration

```
User Question
     │
     ▼
┌─────────────────────┐
│  Intent Classifier   │  ← LLM classifies: technical / data / hybrid / ambiguous
└─────────┬───────────┘
          │
    ┌─────┼──────────────────┐
    ▼     ▼                  ▼
┌──────┐ ┌──────────┐ ┌───────────┐
│ Doc  │ │   Data   │ │ Clarify   │
│ RAG  │ │  Pandas  │ │ Handler   │
│Pipe  │ │  Pipe    │ │           │
└──┬───┘ └────┬─────┘ └─────┬─────┘
   │          │              │
   └────┬─────┘              │
        ▼                    ▼
   ┌──────────────────────────┐
   │  Structured Response     │
   │  (answer, confidence,    │
   │   evidence, caveats)     │
   └──────────────────────────┘
```

### Why This Design

I chose a **router-based orchestration** pattern (not a full agentic loop) because:

1. **Predictability**: With only 2 well-defined pipelines, a single routing step is more predictable and debuggable than multi-step agent loops.
2. **Transparency**: Every classification decision is logged with reasoning, making failures easy to diagnose.
3. **Latency**: Single-step routing minimises LLM calls (1 for routing + 1-2 for answering).
4. **Extensibility**: Adding a new pipeline (e.g., anomaly detection) requires only adding a new intent and handler — the router pattern scales.

### Component Details

| Component | Technology | Purpose |
|---|---|---|
| Intent Classifier | GPT-4o (structured JSON) | Routes questions to the right pipeline |
| Doc Pipeline | sentence-transformers + ChromaDB | RAG over 7 markdown documents |
| Data Pipeline | GPT-4o → pandas code gen → sandboxed exec | Structured reasoning over CSV data |
| Clarification Handler | GPT-4o | Generates targeted clarifying questions |

### Documentation Pipeline (RAG)

- Documents chunked by `##` headers with authority metadata
- `legacy_error_codes_2023.md` tagged as superseded; current docs prioritised
- Cosine similarity retrieval with authority-aware re-ranking
- Generation prompt enforces citation and prevents fabrication

### Data Pipeline (Pandas Code Generation)

- Three-step flow: schema-aware code generation → sandboxed execution → result interpretation
- All three CSVs loaded with data quality fixes applied (ID normalisation, dedup)
- Generated code logged as a reasoning artefact for auditability
- Execution sandbox blocks filesystem access and imports

---

## Assumptions

1. **LLM Provider**: The system uses OpenAI GPT-4o. The architecture is provider-agnostic — swapping to Claude or Gemini requires only changing the client initialisation.
2. **Relative Time**: Questions with relative time references ("yesterday") are treated as ambiguous and trigger clarification, since we cannot know the user's current date in a CLI context.
3. **Data Scope**: The system acknowledges it only has 2 days of metrics data (2026-03-10, 2026-03-11) and limits conclusions accordingly.
4. **Regulatory Claims**: The system avoids making compliance or regulatory statements (e.g., food safety) since duration data is needed and unavailable.

---

## Trade-Offs Made Intentionally

| Decision          | Alternative               | Rationale                                           |
|----               |---                        |---                                                  |
| Router, not agent | LangChain Agent / ReAct   | More predictable for 2 pipelines; agent is overkill |
| Pandas code gen   | Direct LLM over data      | Code gen is auditable and production-transferable |
| Local embeddings (MiniLM)| OpenAI embeddings  | No API cost; sufficient for 7 docs |
| In-memory ChromaDB | Persistent store         | Tiny corpus; no persistence needed |
| CLI                | Streamlit/FastAPI        | Brief says no polished UI needed |
| `exec()` sandbox   | Docker/subprocess          | Simpler; adequate for assessment scope |

---

## Limitations & Known Failure Modes

1. **No conversation memory**: Each question is independent. Multi-turn follow-ups lose context.
2. **Basic sandbox**: `exec()` with restricted globals is not production-safe. Production would use Docker or a subprocess jail.
3. **Embedding quality**: `all-MiniLM-L6-v2` is lightweight and may miss subtle semantic matches on a larger corpus.
4. **Single LLM dependency**: If the OpenAI API is down, the entire system fails.
5. **Code gen reliability**: LLM-generated pandas code occasionally fails on complex queries. The system reports errors honestly but doesn't retry with a corrected approach.
6. **Two days of data**: Time-series analysis is severely limited. The system should (and does) acknowledge this.

---

## What I Would Do Next (1–2 Days)

1. **Conversation memory**: Add session state so follow-up questions work ("and what about A105?")
2. **Code gen retry**: If generated pandas code fails, retry once with the error message as context
3. **Streaming responses**: Use SSE or websocket streaming for real-time answer generation
4. **Better sandbox**: Run generated code in a Docker container or subprocess with resource limits
5. **Evaluation with LLM-as-judge**: Use a second LLM to automatically score groundedness and correctness
6. **Observability**: Add OpenTelemetry tracing for every LLM call (latency, token usage, cost)
7. **API mode**: Add a FastAPI server alongside the CLI for integration testing
# ai-fleet-assistant
# ai-fleet-assistant
