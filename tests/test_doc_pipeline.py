"""Tests for the document pipeline — chunking and metadata tagging.

Note: Tests that require the OpenAI API or embedding model are marked with
@pytest.mark.integration and skipped by default. Run with:
    pytest -m integration
"""

import pytest

from src.doc_pipeline import chunk_markdown, DocPipeline


class TestChunkMarkdown:
    """Test markdown chunking logic."""

    def test_splits_on_h2_headers(self):
        text = "# Title\nIntro\n## Section A\nContent A\n## Section B\nContent B"
        chunks = chunk_markdown(text, "test.md")
        assert len(chunks) >= 2

    def test_preserves_content(self):
        text = "# Title\nIntro\n## Section A\nContent A"
        chunks = chunk_markdown(text, "test.md")
        all_text = " ".join(c[0] for c in chunks)
        assert "Content A" in all_text

    def test_legacy_doc_tagged(self):
        text = "# Legacy\n## Old Codes\nE104 was GPS"
        chunks = chunk_markdown(text, "legacy_error_codes_2023.md")
        for _, meta in chunks:
            assert meta.is_legacy is True
            assert meta.authority == "superseded"

    def test_current_doc_tagged(self):
        text = "# Current\n## Codes\nE104 is ignition"
        chunks = chunk_markdown(text, "error_codes_current.md")
        for _, meta in chunks:
            assert meta.is_legacy is False
            assert meta.authority == "current"
            assert meta.effective_date == "2026-01-15"

    def test_regular_doc_defaults_to_current(self):
        text = "# Battery\n## Troubleshooting\nCheck voltage"
        chunks = chunk_markdown(text, "battery_alerts.md")
        for _, meta in chunks:
            assert meta.authority == "current"
            assert meta.is_legacy is False

    def test_empty_text_returns_no_chunks(self):
        chunks = chunk_markdown("", "empty.md")
        assert len(chunks) == 0


@pytest.mark.integration
class TestDocPipelineIndexing:
    """Integration tests — require embedding model to be downloadable."""

    def test_indexes_all_docs(self):
        pipeline = DocPipeline()
        n = pipeline.index_docs()
        assert n > 0

    def test_retrieval_returns_results(self):
        pipeline = DocPipeline()
        pipeline.index_docs()
        results = pipeline.retrieve("What does error code E104 mean?")
        assert len(results) > 0
