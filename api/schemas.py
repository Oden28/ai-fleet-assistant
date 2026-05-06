"""API-specific request and response schemas.

These wrap the existing pipeline models for HTTP transport.
The core domain models in src/models.py are reused directly in responses.
"""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# AI Copilot — requests
# ---------------------------------------------------------------------------

class AskRequest(BaseModel):
    """Unified question request for the AI copilot."""
    question: str = Field(..., min_length=1, description="The user's question")
    context: Optional[dict] = Field(
        default=None,
        description=(
            "Optional UI context (e.g. current screen, selected vehicle) "
            "to help the copilot give more relevant answers"
        ),
    )


class QueryDocsRequest(BaseModel):
    """Direct documentation RAG query."""
    question: str = Field(..., min_length=1)


class QueryDataRequest(BaseModel):
    """Direct structured-data query."""
    question: str = Field(..., min_length=1)


# ---------------------------------------------------------------------------
# Fleet data — responses
# ---------------------------------------------------------------------------

class FleetSummaryResponse(BaseModel):
    """Dashboard-level KPIs."""
    total_vehicles: int
    active_vehicles: int
    inactive_vehicles: int
    total_alerts: int
    critical_alerts: int
    warning_alerts: int
    info_alerts: int
    fleet_health_score: float = Field(
        description="0–100 composite score based on alerts and metrics"
    )
    avg_fuel_efficiency: Optional[float] = None
    regions: list[str] = Field(default_factory=list)


class VehicleResponse(BaseModel):
    """Single vehicle summary for list and detail views."""
    asset_id: str
    asset_name: str
    region: str
    device_model: str
    asset_type: str
    refrigerated: bool
    # Latest metrics (may be None if no metrics available)
    latest_idle_minutes: Optional[float] = None
    latest_trip_count: Optional[int] = None
    latest_engine_hours: Optional[float] = None
    latest_battery_voltage: Optional[float] = None
    latest_refrigeration_temp: Optional[float] = None
    latest_odometer_km: Optional[float] = None
    # Alert counts
    alert_count: int = 0
    critical_alert_count: int = 0
    # Status derived from alerts
    status: str = "normal"


class VehicleDetailResponse(VehicleResponse):
    """Extended vehicle detail with full metrics and alert history."""
    metrics_history: list[dict] = Field(default_factory=list)
    alert_history: list[dict] = Field(default_factory=list)


class VehicleListResponse(BaseModel):
    """Paginated vehicle list."""
    vehicles: list[VehicleResponse]
    total: int


class AlertResponse(BaseModel):
    """Single alert event."""
    timestamp: str
    asset_id: str
    asset_name: Optional[str] = None
    alert_type: str
    severity: str
    sensor_value: str
    note: str


class AlertListResponse(BaseModel):
    """Filtered alert list."""
    alerts: list[AlertResponse]
    total: int
    critical: int
    warning: int
    info: int


class MetricsResponse(BaseModel):
    """Daily metrics for one or more assets."""
    metrics: list[dict]
    total: int


class MaintenanceItem(BaseModel):
    """A maintenance item derived from alerts and metrics patterns."""
    asset_id: str
    asset_name: str
    maintenance_type: str
    severity: str
    description: str
    due_status: str  # "overdue" | "upcoming" | "completed"
    last_alert_timestamp: Optional[str] = None
    alert_count: int = 0


class MaintenanceResponse(BaseModel):
    """Maintenance schedule."""
    upcoming: list[MaintenanceItem]
    completed: list[MaintenanceItem]
    total: int


class DriverScore(BaseModel):
    """Driver scorecard entry (derived from asset metrics)."""
    asset_id: str
    asset_name: str
    region: str
    idle_score: float = Field(description="Lower idle = better score, 0-100")
    trip_score: float = Field(description="Higher trip count = better, 0-100")
    efficiency_score: float = Field(description="Engine hours efficiency, 0-100")
    composite_score: float = Field(description="Weighted composite 0-100")
    grade: str = Field(description="A/B/C/D/F letter grade")


class DriverScoreboardResponse(BaseModel):
    """Fleet driver scoreboard."""
    drivers: list[DriverScore]
    fleet_average: float


class FuelReportResponse(BaseModel):
    """Fuel efficiency report data."""
    by_asset: list[dict]
    by_region: list[dict]
    fleet_average_efficiency: Optional[float] = None
