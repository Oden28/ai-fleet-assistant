"""FastAPI server for the Fleet Intelligence AI Copilot.

Serves:
  - AI Copilot endpoints (ask, query-docs, query-data, WebSocket)
  - Fleet data REST API (vehicles, alerts, metrics, maintenance, etc.)

Usage:
  uvicorn api.server:app --reload --port 8000
"""

from __future__ import annotations

import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from openai import OpenAI

from src.config import settings
from src.preprocessor import FleetData
from src.router import Router


# ---------------------------------------------------------------------------
# Lifespan — initialise heavy resources once on startup
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler.

    Initialises the OpenAI client, fleet data, and AI router on startup.
    These are expensive to create (embedding model load, ChromaDB indexing)
    so we do it once and store on app.state.
    """
    print("[server] Initialising fleet data...")
    fleet_data = FleetData()
    app.state.fleet_data = fleet_data

    print("[server] Initialising OpenAI client...")
    openai_client = OpenAI(api_key=settings.openai_api_key)

    print("[server] Initialising AI router (this loads embeddings and indexes docs)...")
    ai_router = Router(openai_client=openai_client)
    app.state.ai_router = ai_router

    # Expose individual pipelines for direct-access endpoints
    app.state.doc_pipeline = ai_router._doc_pipeline
    app.state.data_pipeline = ai_router._data_pipeline

    print("[server] ✅ Ready to serve requests")
    yield
    print("[server] Shutting down...")


# ---------------------------------------------------------------------------
# App factory
# ---------------------------------------------------------------------------

app = FastAPI(
    title="Fleet Intelligence AI Copilot",
    description=(
        "Backend API for the Fleet Intelligence platform. "
        "Provides AI-powered fleet analysis (RAG + data pipelines) "
        "and structured fleet data endpoints."
    ),
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
)


# ---------------------------------------------------------------------------
# CORS — allow frontend dev servers
# ---------------------------------------------------------------------------

_default_origins = [
    "http://localhost:3000",    # React dev server
    "http://localhost:5173",    # Vite dev server
    "http://localhost:5174",    # Vite alt port
    "http://127.0.0.1:3000",
    "http://127.0.0.1:5173",
]

_env_origins = os.getenv("CORS_ORIGINS", "")
_extra_origins = [o.strip() for o in _env_origins.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_default_origins + _extra_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Mount routers
# ---------------------------------------------------------------------------

from api.routes.ai import router as ai_router_routes      # noqa: E402
from api.routes.fleet import router as fleet_router_routes  # noqa: E402

app.include_router(ai_router_routes)
app.include_router(fleet_router_routes)


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------

@app.get("/api/health", tags=["System"])
async def health():
    """Readiness check — returns OK if the server is up and pipelines are loaded."""
    return {
        "status": "ok",
        "service": "Fleet Intelligence AI Copilot",
        "pipelines_loaded": hasattr(app.state, "ai_router"),
    }
