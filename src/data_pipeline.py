"""Data pipeline — structured reasoning over fleet CSVs via pandas code generation.

Flow:
  1. Receive a data-oriented question
  2. Build a schema-aware prompt with table definitions, sample rows, and caveats
  3. LLM generates a short pandas snippet
  4. Execute the snippet in a restricted sandbox
  5. LLM interprets the result in natural language
"""

from __future__ import annotations

import json
import traceback

import numpy as np
import pandas as pd

from src.config import settings
from src.models import (
    AssistantResponse,
    Confidence,
    Evidence,
    ReasoningArtifact,
)
from src.preprocessor import FleetData


class DataPipeline:
    """Pandas-based data question answering pipeline."""

    def __init__(self, fleet_data: FleetData, openai_client=None):
        self._data = fleet_data
        self._openai = openai_client

    # ------------------------------------------------------------------
    # Code generation
    # ------------------------------------------------------------------

    def _generate_code(self, question: str) -> str:
        """Ask the LLM to produce a pandas snippet for the question."""
        from src.prompts import DATA_CODEGEN_SYSTEM, DATA_CODEGEN_USER

        system = DATA_CODEGEN_SYSTEM.format(
            schema=self._data.schema_summary(),
            caveats=self._data.caveats_text(),
        )

        messages = [
            {"role": "system", "content": system},
            {"role": "user", "content": DATA_CODEGEN_USER.format(question=question)},
        ]

        response = self._openai.chat.completions.create(
            model=settings.llm_model,
            messages=messages,
            temperature=0.0,
        )

        code = response.choices[0].message.content.strip()
        # Strip markdown fencing if the LLM added it anyway
        if code.startswith("```"):
            lines = code.split("\n")
            lines = [l for l in lines if not l.startswith("```")]
            code = "\n".join(lines)
        return code

    # ------------------------------------------------------------------
    # Sandboxed execution
    # ------------------------------------------------------------------

    def _execute_code(self, code: str) -> tuple[str, bool]:
        """Execute generated pandas code in a restricted namespace.

        Returns (result_string, success_bool).
        """
        # Allow a curated subset of safe builtins
        _SAFE_BUILTINS = {
            "abs": abs, "all": all, "any": any, "bool": bool,
            "dict": dict, "enumerate": enumerate, "filter": filter,
            "float": float, "frozenset": frozenset, "int": int,
            "isinstance": isinstance, "len": len, "list": list,
            "map": map, "max": max, "min": min, "print": print,
            "range": range, "reversed": reversed, "round": round,
            "set": set, "slice": slice, "sorted": sorted, "str": str,
            "sum": sum, "tuple": tuple, "type": type, "zip": zip,
            "True": True, "False": False, "None": None,
        }

        namespace = {
            "__builtins__": _SAFE_BUILTINS,
            "pd": pd,
            "np": np,
            "assets": self._data.assets.copy(),
            "metrics": self._data.metrics.copy(),
            "alerts": self._data.alerts.copy(),
        }

        try:
            exec(code, namespace)  # noqa: S102
            result = namespace.get("result", "No 'result' variable was set by the code.")
            # Convert DataFrames to string
            if isinstance(result, pd.DataFrame):
                result_str = result.to_string(index=False)
            elif isinstance(result, pd.Series):
                result_str = result.to_string()
            else:
                result_str = str(result)
            return result_str, True
        except Exception:
            return f"Execution error:\n{traceback.format_exc()}", False

    # ------------------------------------------------------------------
    # Result interpretation
    # ------------------------------------------------------------------

    def _interpret_result(self, question: str, code: str, result: str) -> dict:
        """Ask the LLM to explain the data result in natural language."""
        from src.prompts import DATA_INTERPRET_SYSTEM, DATA_INTERPRET_USER

        system = DATA_INTERPRET_SYSTEM.format(code=code, result=result)

        messages = [
            {"role": "system", "content": system},
            {"role": "user", "content": DATA_INTERPRET_USER.format(question=question)},
        ]

        response = self._openai.chat.completions.create(
            model=settings.llm_model,
            messages=messages,
            temperature=0.1,
            response_format={"type": "json_object"},
        )

        return json.loads(response.choices[0].message.content)

    # ------------------------------------------------------------------
    # Full pipeline
    # ------------------------------------------------------------------

    def answer(self, question: str) -> AssistantResponse:
        """Generate code, execute it, interpret the result."""
        # Step 1: generate pandas code
        code = self._generate_code(question)

        # Step 2: execute
        result_str, success = self._execute_code(code)

        # Step 3: interpret
        if success:
            interpretation = self._interpret_result(question, code, result_str)
        else:
            interpretation = {
                "answer": (
                    f"I attempted to analyse the data but encountered an error. "
                    f"This may indicate the question cannot be answered with the "
                    f"available data, or a code generation issue.\n\n"
                    f"Error details: {result_str}"
                ),
                "confidence": "low",
                "sources_used": [],
                "caveats": ["Code execution failed — result may be incomplete"],
            }

        # Determine which tables were likely used
        sources = interpretation.get("sources_used", [])
        evidence = [
            Evidence(
                source=s,
                excerpt=f"Queried via generated pandas code",
            )
            for s in sources
        ]

        return AssistantResponse(
            answer=interpretation.get("answer", ""),
            confidence=Confidence(interpretation.get("confidence", "medium")),
            evidence=evidence,
            reasoning_artifacts=[
                ReasoningArtifact(
                    artifact_type="pandas_code",
                    content=code,
                ),
                ReasoningArtifact(
                    artifact_type="query_result",
                    content=result_str,
                ),
            ],
            caveats=interpretation.get("caveats", []),
            sources_used=sources,
        )
