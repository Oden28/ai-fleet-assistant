"""Documentation pipeline — RAG over the fleet management knowledge base.

Responsibilities:
  1. Chunk markdown documents by ## headers
  2. Tag chunks with authority metadata (current vs. superseded)
  3. Embed chunks and store in ChromaDB
  4. Retrieve relevant chunks at query time with authority-aware ranking
  5. Generate grounded, cited answers via LLM
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Optional

import chromadb
from sentence_transformers import SentenceTransformer

from src.config import settings
from src.models import (
    AssistantResponse,
    Confidence,
    DocChunkMeta,
    Evidence,
    ReasoningArtifact,
)

# ---------------------------------------------------------------------------
# Document authority mapping
# ---------------------------------------------------------------------------

_AUTHORITY_MAP: dict[str, dict] = {
    "legacy_error_codes_2023.md": {
        "authority": "superseded",
        "is_legacy": True,
        "effective_date": None,
    },
    "error_codes_current.md": {
        "authority": "current",
        "is_legacy": False,
        "effective_date": "2026-01-15",
    },
}


def _get_authority(filename: str) -> dict:
    return _AUTHORITY_MAP.get(filename, {
        "authority": "current",
        "is_legacy": False,
        "effective_date": None,
    })


# ---------------------------------------------------------------------------
# Chunking
# ---------------------------------------------------------------------------

def chunk_markdown(text: str, source_file: str) -> list[tuple[str, DocChunkMeta]]:
    """Split a markdown document into chunks by ## headers.

    Returns a list of (chunk_text, metadata) tuples.
    """
    auth = _get_authority(source_file)
    sections = re.split(r"(?=^## )", text, flags=re.MULTILINE)
    chunks: list[tuple[str, DocChunkMeta]] = []

    # The first section may be the title / preamble before any ##
    for section in sections:
        section = section.strip()
        if not section:
            continue

        # Extract heading
        heading_match = re.match(r"^##?\s*(.*)", section)
        title = heading_match.group(1) if heading_match else "Preamble"

        meta = DocChunkMeta(
            source_file=source_file,
            section_title=title,
            authority=auth["authority"],
            is_legacy=auth["is_legacy"],
            effective_date=auth.get("effective_date"),
        )
        chunks.append((section, meta))

    return chunks


# ---------------------------------------------------------------------------
# DocPipeline class
# ---------------------------------------------------------------------------

class DocPipeline:
    """RAG pipeline for documentation-grounded answers."""

    def __init__(self, openai_client=None):
        self._embedder = SentenceTransformer(settings.embedding_model)
        self._chroma = chromadb.Client()  # ephemeral in-memory
        self._collection = self._chroma.get_or_create_collection(
            name="fleet_docs",
            metadata={"hnsw:space": "cosine"},
        )
        self._openai = openai_client
        self._indexed = False

    # ------------------------------------------------------------------
    # Indexing
    # ------------------------------------------------------------------

    def index_docs(self, docs_dir: Path | None = None) -> int:
        """Read all markdown files, chunk, embed, and store."""
        docs_dir = docs_dir or settings.docs_dir
        all_chunks: list[tuple[str, DocChunkMeta]] = []

        for md_file in sorted(docs_dir.glob("*.md")):
            text = md_file.read_text(encoding="utf-8")
            chunks = chunk_markdown(text, md_file.name)
            all_chunks.extend(chunks)

        if not all_chunks:
            raise ValueError(f"No documentation chunks found in {docs_dir}")

        texts = [c[0] for c in all_chunks]
        metas = [c[1] for c in all_chunks]
        embeddings = self._embedder.encode(texts, show_progress_bar=False).tolist()

        self._collection.add(
            ids=[f"chunk_{i}" for i in range(len(texts))],
            embeddings=embeddings,
            documents=texts,
            metadatas=[
                {k: v for k, v in m.model_dump().items() if v is not None}
                for m in metas
            ],
        )
        self._indexed = True
        return len(texts)

    # ------------------------------------------------------------------
    # Retrieval
    # ------------------------------------------------------------------

    def retrieve(self, query: str, top_k: int | None = None) -> list[tuple[str, dict]]:
        """Retrieve the most relevant chunks for a query.

        Returns list of (chunk_text, metadata_dict), re-ranked so that
        current/authoritative docs appear before legacy ones.
        """
        if not self._indexed:
            self.index_docs()

        top_k = top_k or settings.retrieval_top_k
        query_emb = self._embedder.encode([query], show_progress_bar=False).tolist()

        results = self._collection.query(
            query_embeddings=query_emb,
            n_results=top_k,
        )

        chunks: list[tuple[str, dict, float]] = []
        for doc, meta, dist in zip(
            results["documents"][0],
            results["metadatas"][0],
            results["distances"][0],
        ):
            # Authority-aware boost: penalise legacy docs
            effective_score = dist
            if meta.get("is_legacy"):
                effective_score += 0.15  # push legacy further away
            chunks.append((doc, meta, effective_score))

        # Re-sort by effective score (lower = better for cosine distance)
        chunks.sort(key=lambda x: x[2])
        return [(doc, meta) for doc, meta, _ in chunks]

    # ------------------------------------------------------------------
    # Generation
    # ------------------------------------------------------------------

    def answer(self, question: str) -> AssistantResponse:
        """Full RAG pipeline: retrieve → generate → return structured response."""
        from src.prompts import DOC_RAG_SYSTEM, DOC_RAG_USER

        retrieved = self.retrieve(question)

        # Build context string for the LLM
        context_parts: list[str] = []
        for doc_text, meta in retrieved:
            label = f"[{meta['source_file']}]"
            if meta.get("is_legacy"):
                label += " (LEGACY — SUPERSEDED)"
            context_parts.append(f"{label}\n{doc_text}")
        context = "\n\n---\n\n".join(context_parts)

        # LLM generation
        messages = [
            {"role": "system", "content": DOC_RAG_SYSTEM.format(context=context)},
            {"role": "user", "content": DOC_RAG_USER.format(question=question)},
        ]

        response = self._openai.chat.completions.create(
            model=settings.llm_model,
            messages=messages,
            temperature=0.1,
            response_format={"type": "json_object"},
        )

        raw = response.choices[0].message.content
        parsed = json.loads(raw)

        # Build evidence list from retrieved chunks
        evidence = [
            Evidence(
                source=meta["source_file"],
                excerpt=doc_text[:200] + ("…" if len(doc_text) > 200 else ""),
                authority=meta.get("authority", "current"),
            )
            for doc_text, meta in retrieved
        ]

        return AssistantResponse(
            answer=parsed.get("answer", ""),
            confidence=Confidence(parsed.get("confidence", "medium")),
            evidence=evidence,
            reasoning_artifacts=[
                ReasoningArtifact(
                    artifact_type="retrieved_chunks",
                    content=context,
                )
            ],
            caveats=parsed.get("caveats", []),
            sources_used=parsed.get("sources_used", []),
        )
