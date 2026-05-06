"""AI Copilot API routes.

Endpoints:
  POST /api/ask        — unified question routing (docs, data, hybrid, clarification)
  POST /api/query-docs — direct RAG over documentation
  POST /api/query-data — direct structured data query
  WS   /api/ws/copilot — WebSocket for streaming copilot interaction
"""

from __future__ import annotations

import asyncio
import json
import traceback
from typing import Any

from fastapi import APIRouter, HTTPException, Request, WebSocket, WebSocketDisconnect

from api.schemas import AskRequest, QueryDataRequest, QueryDocsRequest

router = APIRouter(prefix="/api", tags=["AI Copilot"])


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _response_to_dict(resp) -> dict:
    """Convert an AssistantResponse to a JSON-serialisable dict."""
    return {
        "answer": resp.answer,
        "confidence": resp.confidence.value,
        "is_clarification": resp.is_clarification,
        "clarification_question": resp.clarification_question,
        "sources_used": resp.sources_used,
        "caveats": resp.caveats,
        "evidence": [e.model_dump() for e in resp.evidence],
        "reasoning_artifacts": [a.model_dump() for a in resp.reasoning_artifacts],
    }


def _enrich_question(question: str, context: dict | None) -> str:
    """Optionally prepend UI context to the question for better routing."""
    if not context:
        return question

    parts: list[str] = []
    if vehicle_id := context.get("vehicle_id"):
        parts.append(f"Regarding asset {vehicle_id}")
    if screen := context.get("screen"):
        parts.append(f"(user is viewing the {screen} screen)")
    if parts:
        return f"{' '.join(parts)}: {question}"
    return question


# ---------------------------------------------------------------------------
# POST /api/ask — unified question
# ---------------------------------------------------------------------------

@router.post("/ask")
async def ask_question(body: AskRequest, request: Request) -> dict[str, Any]:
    """Route a natural-language question through the AI pipeline.

    The Router classifies intent and dispatches to the appropriate pipeline:
    - technical → DocPipeline (RAG)
    - data → DataPipeline (pandas code generation)
    - hybrid → both pipelines + synthesis
    - ambiguous → clarification request
    """
    ai_router = request.app.state.ai_router

    enriched = _enrich_question(body.question, body.context)

    try:
        # Run in a thread pool because the pipeline makes synchronous OpenAI calls
        loop = asyncio.get_event_loop()
        resp = await loop.run_in_executor(None, ai_router.ask, enriched)
    except Exception as exc:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Pipeline error: {exc}") from exc

    return _response_to_dict(resp)


# ---------------------------------------------------------------------------
# POST /api/query-docs — direct RAG
# ---------------------------------------------------------------------------

@router.post("/query-docs")
async def query_docs(body: QueryDocsRequest, request: Request) -> dict[str, Any]:
    """Query the documentation pipeline directly (bypasses intent routing)."""
    doc_pipeline = request.app.state.doc_pipeline

    try:
        loop = asyncio.get_event_loop()
        resp = await loop.run_in_executor(None, doc_pipeline.answer, body.question)
    except Exception as exc:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Doc pipeline error: {exc}") from exc

    return _response_to_dict(resp)


# ---------------------------------------------------------------------------
# POST /api/query-data — direct data pipeline
# ---------------------------------------------------------------------------

@router.post("/query-data")
async def query_data(body: QueryDataRequest, request: Request) -> dict[str, Any]:
    """Query the data pipeline directly (bypasses intent routing)."""
    data_pipeline = request.app.state.data_pipeline

    try:
        loop = asyncio.get_event_loop()
        resp = await loop.run_in_executor(None, data_pipeline.answer, body.question)
    except Exception as exc:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Data pipeline error: {exc}") from exc

    return _response_to_dict(resp)


# ---------------------------------------------------------------------------
# WebSocket /api/ws/copilot — streaming copilot
# ---------------------------------------------------------------------------

@router.websocket("/ws/copilot")
async def copilot_websocket(websocket: WebSocket):
    """WebSocket endpoint for real-time copilot interaction.

    Protocol:
      Client sends:  {"question": "...", "context": {...}}
      Server sends:  {"type": "status", "message": "Classifying intent..."}
                     {"type": "status", "message": "Running data pipeline..."}
                     {"type": "result", "data": {<AssistantResponse>}}
                     {"type": "error", "message": "..."}
    """
    await websocket.accept()
    ai_router = websocket.app.state.ai_router

    try:
        while True:
            raw = await websocket.receive_text()
            try:
                msg = json.loads(raw)
            except json.JSONDecodeError:
                await websocket.send_json({"type": "error", "message": "Invalid JSON"})
                continue

            question = msg.get("question", "").strip()
            if not question:
                await websocket.send_json({"type": "error", "message": "Empty question"})
                continue

            context = msg.get("context")
            enriched = _enrich_question(question, context)

            # Send status updates
            await websocket.send_json({"type": "status", "message": "Thinking..."})

            try:
                loop = asyncio.get_event_loop()
                resp = await loop.run_in_executor(None, ai_router.ask, enriched)

                await websocket.send_json({
                    "type": "result",
                    "data": _response_to_dict(resp),
                })
            except Exception as exc:
                traceback.print_exc()
                await websocket.send_json({
                    "type": "error",
                    "message": f"Pipeline error: {str(exc)}",
                })

    except WebSocketDisconnect:
        pass
