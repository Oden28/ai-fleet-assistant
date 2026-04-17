# Walkthrough — Powerfleet AI Fleet Assistant

## How the System Works

The assistant processes questions through a four-stage pipeline:

### Stage 1: Intent Classification
A single LLM call classifies the user's question as `technical`, `data`, `hybrid`, or `ambiguous`. This is the only routing step — no multi-hop agent loops. The classification returns structured JSON with reasoning, making every routing decision transparent and debuggable.

### Stage 2: Pipeline Execution
Based on the classification:

- **Technical questions** go through a RAG pipeline: the 7 documentation files are chunked by section headers, embedded with `sentence-transformers`, stored in ChromaDB, and retrieved at query time. The retrieval includes authority-aware ranking that demotes the legacy error code document.

- **Data questions** go through a code-generation pipeline: the LLM receives the dataset schema and caveats, generates a pandas snippet, the code runs in a sandboxed `exec()` (no builtins, no imports), and a second LLM call interprets the results.

- **Hybrid questions** run both pipelines and a final LLM call synthesises the combined evidence.

- **Ambiguous questions** trigger a clarification response that asks the user to be more specific.

### Stage 3: Evidence Assembly
Every response includes: cited evidence sources, confidence level (high/medium/low), reasoning artefacts (retrieved chunks or generated code), and caveats about data or knowledge limitations.

### Stage 4: Output
Responses are rendered in the CLI using Rich panels with colour-coded confidence indicators.

---

## One Important Design Trade-Off

**Code generation vs. in-context data analysis.**

I chose to have the LLM generate pandas code rather than placing all data directly in the LLM's context window. Both approaches would work at this scale (the entire dataset is ~60 rows).

I chose code generation because:
1. **Auditability**: The generated code is logged and visible to the user. You can verify exactly what computation was performed.
2. **Production-readiness**: In production, data won't fit in a context window. Code generation is the pattern that scales.
3. **Reproducibility**: The same code can be re-run to verify results, unlike LLM in-context reasoning which may vary.

The trade-off is **reliability**: code generation sometimes produces syntactically invalid or logically incorrect code. The system handles this by reporting errors honestly, but a production version would add retry-with-error-feedback.

---

## One Failure Case

**Relative time references in ambiguous questions.**

Question Q7: *"Why did asset A108 have issues yesterday?"*

This fails gracefully — the system correctly identifies it as ambiguous and asks for clarification. But a real user would find this frustrating if they expect "yesterday" to be resolved automatically.

The root cause is that the CLI has no concept of "today," so relative time cannot be resolved. In a production web application, the system would know the current timestamp and could resolve "yesterday" to a specific date.

Additionally, "issues" is undefined — A108 has temperature alerts and could have connectivity or trip-related problems too. The system correctly asks the user to specify which type of issue they mean.

---

## One Change I Would Make First in Production

**Add LLM-as-judge evaluation with regression test suite.**

The current evaluation uses automated heuristics (does the response contain evidence? did it ask for clarification on ambiguous questions?). These are useful but shallow.

In production, I would:
1. Create a golden test set with human-annotated expected answers
2. Use a second, stronger LLM (e.g., GPT-4 Turbo or Claude 3.5 Opus) to score each response on groundedness, correctness, and helpfulness
3. Run this as a CI gate — any prompt change, model upgrade, or code change triggers the full eval suite
4. Track metrics over time to catch regressions early

This is the single highest-leverage change because it transforms evaluation from a manual spot-check into a continuous, automated quality gate.
