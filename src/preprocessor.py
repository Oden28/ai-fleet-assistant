"""Data preprocessor — loads, cleans, and normalises input datasets.

Handles the intentional data-quality issues documented in schema.md:
  • Asset ID normalisation  (A-108 → A108)
  • Duplicate alert row deduplication
  • NaN handling for non-applicable fields
"""

from __future__ import annotations

import re
from pathlib import Path

import pandas as pd

from src.config import settings


# ---------------------------------------------------------------------------
# Asset-ID normalisation
# ---------------------------------------------------------------------------

_LEGACY_ID_RE = re.compile(r"^([A-Z])-(\d+)$")


def normalise_asset_id(raw_id: str) -> str:
    """Normalise legacy formats like 'A-108' → 'A108'."""
    m = _LEGACY_ID_RE.match(raw_id.strip())
    if m:
        return f"{m.group(1)}{m.group(2)}"
    return raw_id.strip()


# ---------------------------------------------------------------------------
# Load & clean individual CSVs
# ---------------------------------------------------------------------------

def load_asset_registry(path: Path | None = None) -> pd.DataFrame:
    """Load and return the asset registry."""
    path = path or settings.data_dir / "asset_registry.csv"
    df = pd.read_csv(path)
    df["asset_id"] = df["asset_id"].apply(normalise_asset_id)
    return df


def load_daily_metrics(path: Path | None = None) -> pd.DataFrame:
    """Load daily asset metrics with proper types."""
    path = path or settings.data_dir / "daily_asset_metrics.csv"
    df = pd.read_csv(path, parse_dates=["date"])
    df["asset_id"] = df["asset_id"].apply(normalise_asset_id)
    return df


def load_alert_events(path: Path | None = None) -> pd.DataFrame:
    """Load alert events, normalise IDs, and deduplicate."""
    path = path or settings.data_dir / "alert_events.csv"
    df = pd.read_csv(path, parse_dates=["timestamp"])
    df["asset_id"] = df["asset_id"].apply(normalise_asset_id)

    before = len(df)
    df = df.drop_duplicates()
    after = len(df)
    if before != after:
        print(f"[preprocessor] Removed {before - after} duplicate alert row(s)")

    return df


# ---------------------------------------------------------------------------
# Convenience: load everything at once
# ---------------------------------------------------------------------------

class FleetData:
    """Container holding all three cleaned DataFrames."""

    def __init__(self) -> None:
        self.assets: pd.DataFrame = load_asset_registry()
        self.metrics: pd.DataFrame = load_daily_metrics()
        self.alerts: pd.DataFrame = load_alert_events()

    # ------------------------------------------------------------------
    # Helpers for schema-context prompting
    # ------------------------------------------------------------------

    def schema_summary(self) -> str:
        """Return a concise text description of each table's schema + sample rows."""
        parts: list[str] = []
        for name, df in [("asset_registry", self.assets),
                         ("daily_asset_metrics", self.metrics),
                         ("alert_events", self.alerts)]:
            cols = ", ".join(f"{c} ({df[c].dtype})" for c in df.columns)
            sample = df.head(3).to_string(index=False)
            parts.append(
                f"### {name}\nColumns: {cols}\n"
                f"Rows: {len(df)}\nSample:\n```\n{sample}\n```"
            )
        return "\n\n".join(parts)

    def caveats_text(self) -> str:
        """Return plain-text caveats the LLM should know about."""
        return (
            "Data caveats:\n"
            "- Only 2 days of metrics data (2026-03-10 and 2026-03-11)\n"
            "- alert_events spans 2026-03-10 to 2026-03-12\n"
            "- refrigeration_avg_temp_c is NaN for non-refrigerated assets\n"
            "- One duplicate alert row was removed during preprocessing\n"
            "- Legacy asset ID 'A-108' was normalised to 'A108'\n"
            "- Not all business conclusions can be proven from this data; "
            "acknowledge limits when necessary"
        )
