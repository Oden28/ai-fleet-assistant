"""Intent router — classifies user questions and dispatches to the correct pipeline.

Supports four intents: technical, data, hybrid, ambiguous.
Uses a single LLM call with structured JSON output for classification.
"""

from __future__ import annotations

import json

from src.config import settings
from src.models import (
    AssistantResponse,
    Confidence,
    Intent,
    RouteDecision,
)
from src.doc_pipeline import DocPipeline
from src.data_pipeline import DataPipeline
from src.preprocessor import FleetData


class Router:
    """Classifies user intent and orchestrates the appropriate pipeline(s)."""

    def __init__(self, openai_client=None):
        self._openai = openai_client
        self._fleet_data = FleetData()
        self._doc_pipeline = DocPipeline(openai_client=openai_client)
        self._data_pipeline = DataPipeline(
            fleet_data=self._fleet_data,
            openai_client=openai_client,
        )
        # Index docs on init
        n = self._doc_pipeline.index_docs()
        print(f"[router] Indexed {n} documentation chunks")

    # ------------------------------------------------------------------
    # Intent classification
    # ------------------------------------------------------------------

    def classify(self, question: str) -> RouteDecision:
        """Classify a user question into an intent."""
        from src.prompts import INTENT_SYSTEM, INTENT_USER

        messages = [
            {"role": "system", "content": INTENT_SYSTEM},
            {"role": "user", "content": INTENT_USER.format(question=question)},
        ]

        response = self._openai.chat.completions.create(
            model=settings.llm_model,
            messages=messages,
            temperature=0.0,
            response_format={"type": "json_object"},
        )

        raw = response.choices[0].message.content
        parsed = json.loads(raw)

        return RouteDecision(
            intent=Intent(parsed["intent"]),
            reasoning=parsed.get("reasoning", ""),
            clarification_needed=parsed.get("clarification_needed", False),
            clarification_question=parsed.get("clarification_question"),
        )

    # ------------------------------------------------------------------
    # Clarification generation
    # ------------------------------------------------------------------

    def _ask_clarification(self, question: str, route: RouteDecision) -> AssistantResponse:
        """Generate a clarifying question for ambiguous/underspecified input."""
        from src.prompts import CLARIFICATION_SYSTEM, CLARIFICATION_USER

        asset_ids = ", ".join(sorted(self._fleet_data.assets["asset_id"].tolist()))

        messages = [
            {
                "role": "system",
                "content": CLARIFICATION_SYSTEM.format(asset_ids=asset_ids),
            },
            {
                "role": "user",
                "content": CLARIFICATION_USER.format(question=question),
            },
        ]

        response = self._openai.chat.completions.create(
            model=settings.llm_model,
            messages=messages,
            temperature=0.2,
            response_format={"type": "json_object"},
        )

        parsed = json.loads(response.choices[0].message.content)

        return AssistantResponse(
            answer=parsed.get("clarification_question", route.clarification_question or ""),
            confidence=Confidence.LOW,
            is_clarification=True,
            clarification_question=parsed.get("clarification_question"),
            caveats=[f"Routing reasoning: {route.reasoning}"],
        )

    # ------------------------------------------------------------------
    # Hybrid — merge doc + data
    # ------------------------------------------------------------------

    def _handle_hybrid(self, question: str) -> AssistantResponse:
        """Answer questions that need both documentation and data evidence."""
        from src.prompts import HYBRID_SYSTEM, HYBRID_USER

        doc_resp = self._doc_pipeline.answer(question)
        data_resp = self._data_pipeline.answer(question)

        messages = [
            {
                "role": "system",
                "content": HYBRID_SYSTEM.format(
                    doc_evidence=doc_resp.answer,
                    data_evidence=data_resp.answer,
                ),
            },
            {"role": "user", "content": HYBRID_USER.format(question=question)},
        ]

        response = self._openai.chat.completions.create(
            model=settings.llm_model,
            messages=messages,
            temperature=0.1,
            response_format={"type": "json_object"},
        )

        parsed = json.loads(response.choices[0].message.content)

        # Merge evidence and artifacts from both pipelines
        return AssistantResponse(
            answer=parsed.get("answer", ""),
            confidence=Confidence(parsed.get("confidence", "medium")),
            evidence=doc_resp.evidence + data_resp.evidence,
            reasoning_artifacts=doc_resp.reasoning_artifacts + data_resp.reasoning_artifacts,
            caveats=parsed.get("caveats", []),
            sources_used=parsed.get("sources_used", []),
        )

    # ------------------------------------------------------------------
    # Main dispatch
    # ------------------------------------------------------------------

    def ask(self, question: str) -> AssistantResponse:
        """Classify the question and route to the appropriate pipeline."""
        route = self.classify(question)
        print(f"[router] Intent: {route.intent.value} | Reasoning: {route.reasoning}")

        if route.intent == Intent.AMBIGUOUS or route.clarification_needed:
            return self._ask_clarification(question, route)

        if route.intent == Intent.TECHNICAL:
            return self._doc_pipeline.answer(question)

        if route.intent == Intent.DATA:
            return self._data_pipeline.answer(question)

        if route.intent == Intent.HYBRID:
            return self._handle_hybrid(question)

        # Fallback — should not reach here
        return self._doc_pipeline.answer(question)
