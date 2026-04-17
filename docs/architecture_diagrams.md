# Architecture Diagrams

## 1. High-Level System Architecture

```mermaid
flowchart TB
    subgraph UserInterface["User Interface Layer"]
        CLI["CLI (Click + Rich)"]
        BATCH["Batch Mode"]
        JSON_OUT["JSON Output"]
    end

    subgraph Orchestration["Orchestration Layer"]
        ROUTER["Router (router.py)"]
        IC["Intent Classifier"]
        DISPATCH["Pipeline Dispatcher"]
    end

    subgraph Pipelines["Execution Pipelines"]
        subgraph DocPipe["Documentation Pipeline"]
            CHUNK["Doc Chunker"]
            EMBED["Embedder (MiniLM-L6-v2)"]
            CHROMA["ChromaDB (In-Memory)"]
            RERANK["Authority-Aware Re-Ranker"]
            DOC_GEN["Doc Answer Generator"]
        end

        subgraph DataPipe["Data Pipeline"]
            SCHEMA_CTX["Schema Context Builder"]
            CODEGEN["Pandas Code Generator"]
            SANDBOX["Sandboxed Executor"]
            INTERPRET["Result Interpreter"]
        end

        subgraph ClarifyPipe["Clarification Pipeline"]
            DETECT["Ambiguity Detector"]
            CLARIFY_GEN["Clarification Generator"]
        end

        subgraph HybridPipe["Hybrid Pipeline"]
            MERGE["Evidence Merger"]
        end
    end

    subgraph DataLayer["Data Layer"]
        DOCS["7 Markdown Docs"]
        ASSETS["asset_registry.csv"]
        METRICS["daily_asset_metrics.csv"]
        ALERTS["alert_events.csv"]
        PREPROC["Preprocessor"]
    end

    subgraph LLMLayer["LLM Layer"]
        GPT["OpenAI GPT-4o"]
        PROMPTS["Prompt Templates (prompts.py)"]
    end

    subgraph OutputLayer["Response Layer"]
        RESP["AssistantResponse"]
        EVIDENCE["Evidence + Citations"]
        CONFIDENCE["Confidence Score"]
        CAVEATS["Caveats"]
        ARTIFACTS["Reasoning Artifacts"]
    end

    CLI --> ROUTER
    BATCH --> ROUTER
    ROUTER --> IC
    IC -->|"LLM call #1"| GPT
    IC --> DISPATCH

    DISPATCH -->|technical| DocPipe
    DISPATCH -->|data| DataPipe
    DISPATCH -->|ambiguous| ClarifyPipe
    DISPATCH -->|hybrid| HybridPipe

    CHUNK --> EMBED --> CHROMA
    CHROMA --> RERANK --> DOC_GEN
    DOC_GEN -->|"LLM call #2"| GPT

    SCHEMA_CTX --> CODEGEN
    CODEGEN -->|"LLM call #2"| GPT
    CODEGEN --> SANDBOX --> INTERPRET
    INTERPRET -->|"LLM call #3"| GPT

    DETECT --> CLARIFY_GEN
    CLARIFY_GEN -->|"LLM call #2"| GPT

    HybridPipe --> DocPipe
    HybridPipe --> DataPipe
    MERGE -->|"LLM call #4"| GPT

    DOCS --> CHUNK
    PREPROC --> ASSETS
    PREPROC --> METRICS
    PREPROC --> ALERTS
    ASSETS --> SANDBOX
    METRICS --> SANDBOX
    ALERTS --> SANDBOX

    PROMPTS --> GPT

    DOC_GEN --> RESP
    INTERPRET --> RESP
    CLARIFY_GEN --> RESP
    MERGE --> RESP

    RESP --> EVIDENCE
    RESP --> CONFIDENCE
    RESP --> CAVEATS
    RESP --> ARTIFACTS
    RESP --> CLI
    RESP --> JSON_OUT
```

---

## 2. Request Processing Flow (Sequence Diagram)

```mermaid
sequenceDiagram
    actor User
    participant CLI as CLI (main.py)
    participant Router as Router (router.py)
    participant LLM as GPT-4o
    participant DocPipe as Doc Pipeline
    participant ChromaDB as ChromaDB
    participant DataPipe as Data Pipeline
    participant Sandbox as Pandas Sandbox

    User->>CLI: Ask question
    CLI->>Router: router.ask(question)

    Note over Router,LLM: Step 1: Intent Classification
    Router->>LLM: Classify intent (structured JSON)
    LLM-->>Router: {intent, reasoning, clarification_needed}

    alt intent == "technical"
        Note over Router,ChromaDB: Step 2a: Documentation RAG
        Router->>DocPipe: doc_pipeline.answer(question)
        DocPipe->>ChromaDB: Retrieve top-k chunks
        ChromaDB-->>DocPipe: Ranked chunks + metadata
        DocPipe->>DocPipe: Authority-aware re-ranking
        DocPipe->>LLM: Generate answer from chunks
        LLM-->>DocPipe: {answer, confidence, sources, caveats}
        DocPipe-->>Router: AssistantResponse

    else intent == "data"
        Note over Router,Sandbox: Step 2b: Data Analysis
        Router->>DataPipe: data_pipeline.answer(question)
        DataPipe->>LLM: Generate pandas code
        LLM-->>DataPipe: Python code string
        DataPipe->>Sandbox: Execute in restricted namespace
        Sandbox-->>DataPipe: Result string
        DataPipe->>LLM: Interpret result
        LLM-->>DataPipe: {answer, confidence, sources, caveats}
        DataPipe-->>Router: AssistantResponse

    else intent == "hybrid"
        Note over Router,Sandbox: Step 2c: Both Pipelines
        Router->>DocPipe: doc_pipeline.answer(question)
        DocPipe-->>Router: Doc evidence
        Router->>DataPipe: data_pipeline.answer(question)
        DataPipe-->>Router: Data evidence
        Router->>LLM: Merge both evidence sets
        LLM-->>Router: Synthesised AssistantResponse

    else intent == "ambiguous"
        Note over Router,LLM: Step 2d: Clarification
        Router->>LLM: Generate clarifying question
        LLM-->>Router: {clarification_question, reasoning}
    end

    Router-->>CLI: AssistantResponse
    CLI-->>User: Formatted answer + evidence + confidence
```

---

## 3. Documentation Pipeline Detail

```mermaid
flowchart LR
    subgraph Indexing["Indexing Phase (Startup)"]
        direction TB
        MD1["battery_alerts.md"]
        MD2["communication_loss.md"]
        MD3["error_codes_current.md"]
        MD4["ignition_anomalies.md"]
        MD5["legacy_error_codes_2023.md\n⚠️ SUPERSEDED"]
        MD6["refrigerated_temperature_monitoring.md"]
        MD7["trip_detection_px200.md"]

        SPLIT["Split by ## Headers"]
        TAG["Tag Metadata:\n• source_file\n• authority\n• is_legacy\n• effective_date"]
        EMBED_IDX["Embed with\nMiniLM-L6-v2"]
        STORE["Store in\nChromaDB"]
    end

    subgraph Retrieval["Retrieval Phase (Query Time)"]
        direction TB
        QUERY["User Question"]
        Q_EMBED["Embed Query"]
        COSINE["Cosine Similarity\nSearch (top-k=5)"]
        RERANK_R["Authority-Aware\nRe-Ranking\n(legacy += 0.15 penalty)"]
        CONTEXT["Build Context String\nwith source labels"]
    end

    subgraph Generation["Generation Phase"]
        direction TB
        PROMPT["System Prompt:\n• Cite sources in brackets\n• Prefer current over legacy\n• Flag conflicts\n• Never fabricate"]
        LLM_CALL["GPT-4o\n(temp=0.1, JSON mode)"]
        PARSE["Parse JSON:\n{answer, confidence,\nsources, caveats}"]
    end

    MD1 & MD2 & MD3 & MD4 & MD5 & MD6 & MD7 --> SPLIT
    SPLIT --> TAG --> EMBED_IDX --> STORE

    QUERY --> Q_EMBED --> COSINE
    STORE -.->|vector search| COSINE
    COSINE --> RERANK_R --> CONTEXT

    CONTEXT --> PROMPT --> LLM_CALL --> PARSE
```

---

## 4. Data Pipeline Detail

```mermaid
flowchart TB
    subgraph Preprocessing["Data Preprocessing (Startup)"]
        RAW_A["asset_registry.csv\n12 assets"]
        RAW_M["daily_asset_metrics.csv\n24 rows (2 days)"]
        RAW_E["alert_events.csv\n15 rows (after dedup)"]

        NORM["Normalise IDs\nA-108 → A108"]
        DEDUP["Deduplicate\nidentical rows"]
        DTYPE["Parse dates,\nhandle NaN"]
    end

    subgraph CodeGen["Code Generation"]
        SCHEMA["Schema Context:\n• Column names + types\n• Sample rows\n• Data caveats"]
        QUESTION["User Question"]
        PROMPT_CG["Code Generation Prompt:\n'Write pandas code,\nstore result in `result`'"]
        LLM_CG["GPT-4o\n(temp=0.0)"]
        CODE["Generated Python Code"]
    end

    subgraph Execution["Sandboxed Execution"]
        SAFE["Safe Builtins Only:\nlen, max, min, sorted,\nstr, int, float, range...\n\n❌ open, exec, eval,\n❌ __import__, os, sys"]
        NS["Namespace:\n• pd (pandas)\n• np (numpy)\n• assets DataFrame\n• metrics DataFrame\n• alerts DataFrame"]
        EXEC["exec(code, namespace)"]
        RESULT["Result Variable"]
    end

    subgraph Interpretation["Result Interpretation"]
        CODE_LOG["Code (logged as artifact)"]
        RES_STR["Result String"]
        PROMPT_INT["Interpretation Prompt:\n'Explain in natural language,\nacknowledge data limits'"]
        LLM_INT["GPT-4o\n(temp=0.1, JSON mode)"]
        FINAL["Final Answer +\nConfidence + Caveats"]
    end

    RAW_A --> NORM --> DTYPE
    RAW_M --> DTYPE
    RAW_E --> NORM --> DEDUP --> DTYPE

    SCHEMA --> PROMPT_CG
    QUESTION --> PROMPT_CG
    PROMPT_CG --> LLM_CG --> CODE

    DTYPE --> NS
    CODE --> EXEC
    SAFE --> EXEC
    NS --> EXEC
    EXEC --> RESULT

    CODE --> CODE_LOG
    RESULT --> RES_STR
    CODE_LOG --> PROMPT_INT
    RES_STR --> PROMPT_INT
    PROMPT_INT --> LLM_INT --> FINAL
```

---

## 5. Intent Classification Decision Tree

```mermaid
flowchart TD
    Q["User Question"] --> CLASSIFY["LLM Intent Classifier"]

    CLASSIFY --> CHECK_CLAR{"Clarification\nNeeded?"}

    CHECK_CLAR -->|Yes| AMB["Return: AMBIGUOUS\n→ Ask clarifying question"]

    CHECK_CLAR -->|No| INTENT{"What Intent?"}

    INTENT -->|"technical\n(error codes, troubleshooting,\ndevice behavior)"| TECH["Route → Doc Pipeline\n(RAG)"]

    INTENT -->|"data\n(asset metrics, rankings,\nalert patterns)"| DATA["Route → Data Pipeline\n(Pandas)"]

    INTENT -->|"hybrid\n(error code + specific asset,\ntroubleshooting + data context)"| HYBRID["Route → Both Pipelines\n→ Merge Evidence"]

    INTENT -->|"ambiguous\n(vague, relative time,\ntoo broad)"| AMB

    TECH --> RESP["AssistantResponse"]
    DATA --> RESP
    HYBRID --> RESP
    AMB --> RESP

    style AMB fill:#f9a825,stroke:#f57f17
    style TECH fill:#66bb6a,stroke:#388e3c
    style DATA fill:#42a5f5,stroke:#1976d2
    style HYBRID fill:#ab47bc,stroke:#7b1fa2
```

---

## 6. Data Model Relationships

```mermaid
classDiagram
    class RouteDecision {
        +Intent intent
        +str reasoning
        +bool clarification_needed
        +str clarification_question
    }

    class Intent {
        <<enumeration>>
        TECHNICAL
        DATA
        AMBIGUOUS
        HYBRID
    }

    class AssistantResponse {
        +str answer
        +Confidence confidence
        +list~Evidence~ evidence
        +list~ReasoningArtifact~ reasoning_artifacts
        +list~str~ caveats
        +list~str~ sources_used
        +bool is_clarification
        +str clarification_question
    }

    class Confidence {
        <<enumeration>>
        HIGH
        MEDIUM
        LOW
    }

    class Evidence {
        +str source
        +str excerpt
        +str authority
    }

    class ReasoningArtifact {
        +str artifact_type
        +str content
    }

    class DocChunkMeta {
        +str source_file
        +str section_title
        +str authority
        +bool is_legacy
        +str effective_date
    }

    RouteDecision --> Intent
    AssistantResponse --> Confidence
    AssistantResponse --> "0..*" Evidence
    AssistantResponse --> "0..*" ReasoningArtifact
```

---

## 7. Module Dependency Graph

```mermaid
flowchart BT
    CONFIG["config.py\n(Settings)"]
    MODELS["models.py\n(Pydantic Models)"]
    PROMPTS["prompts.py\n(Prompt Templates)"]
    PREPROC["preprocessor.py\n(Data Cleaning)"]
    DOC["doc_pipeline.py\n(RAG Pipeline)"]
    DATA["data_pipeline.py\n(Pandas Pipeline)"]
    ROUTER["router.py\n(Orchestrator)"]
    MAIN["main.py\n(CLI Entrypoint)"]
    EVAL["eval/run_eval.py\n(Evaluation)"]

    CONFIG --> PREPROC
    CONFIG --> DOC
    CONFIG --> DATA
    CONFIG --> ROUTER
    CONFIG --> MAIN

    MODELS --> DOC
    MODELS --> DATA
    MODELS --> ROUTER
    MODELS --> MAIN

    PROMPTS --> DOC
    PROMPTS --> DATA
    PROMPTS --> ROUTER

    PREPROC --> DATA
    PREPROC --> ROUTER

    DOC --> ROUTER
    DATA --> ROUTER

    ROUTER --> MAIN
    ROUTER --> EVAL

    style MAIN fill:#e3f2fd,stroke:#1976d2
    style EVAL fill:#fce4ec,stroke:#c62828
    style ROUTER fill:#f3e5f5,stroke:#7b1fa2
    style DOC fill:#e8f5e9,stroke:#388e3c
    style DATA fill:#fff3e0,stroke:#ef6c00
```

---

## 8. Evaluation Pipeline

```mermaid
flowchart LR
    subgraph Input["Test Questions"]
        SEED["Seed Questions\n(10 questions)"]
        ADV["Adversarial Questions\n(6 questions)"]
    end

    subgraph Execution["Run Each Question"]
        ROUTER_E["Router.ask()"]
        TIMER["⏱ Elapsed Time"]
    end

    subgraph AutoScore["Automated Scoring"]
        S1["has_evidence?\n(sources cited)"]
        S2["confidence_set?\n(level assigned)"]
        S3["asked_clarification?\n(for ambiguous only)"]
        S4["has_caveats?\n(limitations noted)"]
        S5["avoided_fabrication?\n(for adversarial only)"]
    end

    subgraph Output["Results"]
        TABLE["Rich Summary Table"]
        JSON_R["full_results.json"]
        STATS["📊 Quick Stats"]
    end

    SEED --> ROUTER_E
    ADV --> ROUTER_E
    ROUTER_E --> TIMER
    TIMER --> S1 & S2 & S3 & S4 & S5
    S1 & S2 & S3 & S4 & S5 --> TABLE
    S1 & S2 & S3 & S4 & S5 --> JSON_R
    TABLE --> STATS
```
