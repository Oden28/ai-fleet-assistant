"""Application configuration loaded from environment variables."""

from __future__ import annotations

import os
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict
from dotenv import load_dotenv

# Load .env from project root
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(_PROJECT_ROOT / ".env")


class Settings(BaseSettings):
    """Central configuration for the fleet assistant."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    # -- LLM -----------------------------------------------------------------
    openai_api_key: str = ""
    llm_model: str = "gpt-4o"

    # -- Embeddings -----------------------------------------------------------
    embedding_model: str = "all-MiniLM-L6-v2"

    # -- Retrieval ------------------------------------------------------------
    retrieval_top_k: int = 5
    chunk_size: int = 512  # approximate characters per chunk

    # -- Paths ----------------------------------------------------------------
    project_root: Path = _PROJECT_ROOT
    input_dir: Path = _PROJECT_ROOT / "input"
    docs_dir: Path = _PROJECT_ROOT / "input" / "docs"
    data_dir: Path = _PROJECT_ROOT / "input" / "data"
    schema_path: Path = _PROJECT_ROOT / "input" / "schema.md"
    seed_questions_path: Path = _PROJECT_ROOT / "input" / "questions_seed.csv"


# Singleton
settings = Settings()
