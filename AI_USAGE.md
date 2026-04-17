# AI_USAGE.md

## AI Tools Used
- **Gemini Code Assist (Antigravity)**: Used as a pair-programming partner throughout the exercise for code generation, architecture discussion, and document drafting.
- **OpenAI GPT-4o**: Used as the runtime LLM within the application itself for intent classification, RAG generation, and data analysis code generation.

## Where AI Helped
- **Architecture design**: Discussed trade-offs between agentic vs. router-based designs; AI helped structure the comparison but the final decision was mine.
- **Boilerplate code**: Initial file scaffolding (project structure, pyproject.toml, CLI setup) was generated with AI assistance.
- **Prompt engineering**: AI suggested initial prompt templates; I iterated on them to improve grounding, citation, and calibration behaviour.
- **Test case design**: AI helped generate unit test scaffolding; I designed the specific assertions and edge cases.
- **Documentation drafting**: README structure and wording were drafted with AI assistance; I reviewed and edited for accuracy and tone.

## Where You Disagreed With Or Overrode AI
- **Router vs. Agent**: AI initially suggested a LangChain Agent approach. I chose a simpler router-based design because the question space is well-scoped and predictability matters more than flexibility here.
- **SQL vs. Pandas**: AI suggested SQLite for the data pipeline. I chose pandas because the datasets are tiny (26 rows, 16 rows) and standing up a database adds complexity with no benefit at this scale.
- **Prompt refinement**: Multiple iterations on the RAG generation prompt were needed to get the model to properly cite sources and flag legacy doc conflicts. The initial AI-suggested prompt was too permissive about fabrication.
- **Sandbox approach**: AI suggested using `subprocess` for code execution sandboxing. I chose `exec()` with restricted builtins as a pragmatic trade-off for assessment scope, while documenting it as a known limitation.

## Independent Design Decisions
- **Router-based orchestration architecture**: My decision to use a single LLM classification step instead of a multi-step agent loop.
- **Authority-aware document ranking**: The scheme for tagging documents as current vs. superseded and the specific re-ranking penalty was my design.
- **Data quality preprocessing strategy**: The decision to fix known issues (ID normalisation, deduplication) at load time rather than at query time.
- **Evaluation framework design**: The choice to combine automated heuristic scoring with human review criteria rather than relying solely on LLM-as-judge.
- **Adversarial test cases**: All six adversarial questions were designed by me to probe specific failure modes I identified during architecture design.
- **Confidence calibration approach**: The three-level confidence system and the instructions for when to use each level.

## Confidence And Limitations
**Confident in:**
- Architecture selection — the router pattern is well-suited to this problem scope
- Data preprocessing — all documented caveats are handled
- Test coverage for core logic (preprocessor, chunking, sandbox)
- Honest handling of uncertainty and data limitations

**Remaining weaknesses:**
- RAG retrieval quality depends on the embedding model; `MiniLM` is a trade-off for speed
- Code generation can fail on complex multi-step data questions
- No conversation memory limits the user experience
- Evaluation is heuristic-based; production would need human annotation or LLM-as-judge
