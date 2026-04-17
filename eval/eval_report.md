# Evaluation Note

## How I Evaluated the System

Evaluation was performed at three levels:

### 1. Unit Tests
Automated tests validate core logic that doesn't depend on the LLM:
- **Preprocessor**: Asset ID normalisation, duplicate removal, CSV loading integrity
- **Document chunking**: Correct splitting by headers, authority metadata tagging
- **Data pipeline sandbox**: Code execution works, builtins are blocked, results are captured

### 2. Automated Evaluation Heuristics
The `eval/run_eval.py` script runs all seed and adversarial questions and applies automated scoring:
- **Has evidence**: Did the response cite sources or include data references?
- **Confidence set**: Was a confidence level explicitly assigned?
- **Clarification for ambiguous**: Did ambiguous questions trigger a clarification request?
- **Fabrication avoidance**: For adversarial questions, does the response contain refusal/uncertainty phrases rather than fabricated answers?

### 3. Manual Review
I manually reviewed responses for:
- Factual correctness against the source documents and data
- Appropriate handling of the legacy vs. current error code conflict
- Data quality issues being properly handled (A-108 normalised, duplicates removed)
- Honest acknowledgement of limitations (2 days of data, daily averages only)

---

## What Success Means for This Task

A successful response must satisfy these criteria:

| Criterion | Description |
|---|---|
| **Grounded** | Every claim is traceable to a specific document excerpt or data query result |
| **Correct** | Factual answers match what the source material says |
| **Calibrated** | Confidence level matches evidence quality (high only when directly supported) |
| **Honest** | Limitations, data gaps, and uncertainties are acknowledged rather than glossed over |
| **Cited** | Source documents or tables are explicitly referenced |
| **Appropriate** | Ambiguous questions trigger clarification, not guesses |

---

## Failure Modes Observed

### 1. Relative Time Resolution
Questions with "yesterday" or "last week" cannot be resolved without knowing the current date. The system correctly asks for clarification, but this is a UX friction point.

### 2. Over-Eager Routing to Data Pipeline
Some hybrid questions (Q8: "If I see E104 and no trips on a PX-200, what should I check first?") are sometimes classified as purely technical when they would benefit from data correlation. The intent classifier captures most hybrid cases but can miss subtle ones.

### 3. Code Generation Failures
On complex multi-step data questions, the generated pandas code occasionally has syntax errors or logical mistakes. The system reports the error rather than fabricating an answer, but no automatic retry is attempted.

### 4. Legacy Document Leakage
In rare cases, the RAG pipeline retrieves a chunk from the legacy error codes document and the LLM includes the legacy definition without sufficient caveats. The authority-aware re-ranking reduces this but doesn't eliminate it entirely.

---

## How I Would Prevent Regressions

### Short-Term (This Assessment)
- Run `pytest` on every code change to catch preprocessor and sandbox regressions
- Re-run `eval/run_eval.py` after any prompt change and compare results

### Medium-Term (Production)
1. **Golden test set**: Create 50+ question-answer pairs with human-annotated expected answers
2. **LLM-as-judge CI gate**: A second LLM scores every response; the test fails if any score drops below threshold
3. **Prompt versioning**: Track prompt templates in version control with a changelog
4. **Embedding drift monitoring**: If the embedding model is updated, re-run retrieval accuracy tests

### Long-Term
1. **User feedback loop**: Collect thumbs-up/down from production users to identify real-world failure modes
2. **A/B testing**: Run prompt or model changes on a subset of traffic before full rollout
3. **Continuous evaluation dashboard**: Track groundedness, confidence calibration, and response latency over time
