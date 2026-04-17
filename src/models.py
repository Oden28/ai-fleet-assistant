"""Pydantic models for request/response types used throughout the assistant."""

from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Intent classification
# ---------------------------------------------------------------------------

class Intent(str, Enum):
    """Possible user intents recognised by the router."""
    TECHNICAL = "technical"
    DATA = "data"
    AMBIGUOUS = "ambiguous"
    HYBRID = "hybrid"


class RouteDecision(BaseModel):
    """Structured output from the intent classifier."""
    intent: Intent
    reasoning: str = Field(description="Brief justification for the routing decision")
    clarification_needed: bool = False
    clarification_question: Optional[str] = None


# ---------------------------------------------------------------------------
# Evidence & reasoning artefacts
# ---------------------------------------------------------------------------

class Evidence(BaseModel):
    """A single piece of evidence supporting an answer."""
    source: str = Field(description="Filename or table name the evidence came from")
    excerpt: str = Field(description="Quoted or summarised excerpt")
    authority: str = Field(default="current", description="'current' or 'superseded'")


class ReasoningArtifact(BaseModel):
    """An intermediate artefact produced during answer generation."""
    artifact_type: str = Field(description="e.g. 'pandas_code', 'query_result', 'retrieved_chunks'")
    content: str


# ---------------------------------------------------------------------------
# Confidence
# ---------------------------------------------------------------------------

class Confidence(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


# ---------------------------------------------------------------------------
# Final assistant response
# ---------------------------------------------------------------------------

class AssistantResponse(BaseModel):
    """The complete response returned to the user."""
    answer: str
    confidence: Confidence = Confidence.MEDIUM
    evidence: list[Evidence] = Field(default_factory=list)
    reasoning_artifacts: list[ReasoningArtifact] = Field(default_factory=list)
    caveats: list[str] = Field(default_factory=list)
    sources_used: list[str] = Field(default_factory=list)
    is_clarification: bool = False
    clarification_question: Optional[str] = None


# ---------------------------------------------------------------------------
# Document chunk metadata
# ---------------------------------------------------------------------------

class DocChunkMeta(BaseModel):
    """Metadata attached to each documentation chunk in the vector store."""
    source_file: str
    section_title: str
    authority: str = "current"  # "current" | "superseded"
    is_legacy: bool = False
    effective_date: Optional[str] = None
