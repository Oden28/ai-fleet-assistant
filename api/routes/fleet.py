"""Fleet data REST API routes.

Serves the structured fleet data (assets, metrics, alerts) for the
dashboard, vehicle list, alerts, maintenance, driver scorecard, and
reports screens.

All data comes from the FleetData preprocessor (pandas DataFrames)
loaded at application startup.
"""

from __future__ import annotations

import math
from typing import Optional

import numpy as np
import pandas as pd
from fastapi import APIRouter, Query, Request

from api.schemas import (
    AlertListResponse,
    AlertResponse,
    DriverScore,
    DriverScoreboardResponse,
    FleetSummaryResponse,
    FuelReportResponse,
    MaintenanceItem,
    MaintenanceResponse,
    MetricsResponse,
    VehicleDetailResponse,
    VehicleListResponse,
    VehicleResponse,
)

router = APIRouter(prefix="/api/fleet", tags=["Fleet Data"])


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _safe(val):
    """Convert numpy/pandas NaN to None for JSON serialisation."""
    if val is None:
        return None
    if isinstance(val, float) and (math.isnan(val) or math.isinf(val)):
        return None
    if isinstance(val, (np.integer,)):
        return int(val)
    if isinstance(val, (np.floating,)):
        return float(val) if not math.isnan(val) else None
    if isinstance(val, (np.bool_,)):
        return bool(val)
    return val


def _derive_status(alerts_df: pd.DataFrame, asset_id: str) -> str:
    """Derive a vehicle status from its recent alerts."""
    asset_alerts = alerts_df[alerts_df["asset_id"] == asset_id]
    if asset_alerts.empty:
        return "normal"
    if (asset_alerts["severity"] == "high").any():
        return "critical"
    if (asset_alerts["severity"] == "medium").any():
        return "warning"
    return "info"


def _build_vehicle_response(
    row: pd.Series,
    metrics_df: pd.DataFrame,
    alerts_df: pd.DataFrame,
) -> VehicleResponse:
    """Build a VehicleResponse from an asset registry row + related data."""
    asset_id = row["asset_id"]

    # Get latest metrics
    asset_metrics = metrics_df[metrics_df["asset_id"] == asset_id].sort_values("date")
    latest = asset_metrics.iloc[-1] if not asset_metrics.empty else None

    # Count alerts
    asset_alerts = alerts_df[alerts_df["asset_id"] == asset_id]
    critical_count = int((asset_alerts["severity"] == "high").sum())

    # Parse refrigerated as bool
    refrig = row.get("refrigerated", False)
    if isinstance(refrig, str):
        refrig = refrig.lower() == "true"

    return VehicleResponse(
        asset_id=asset_id,
        asset_name=row["asset_name"],
        region=row["region"],
        device_model=row["device_model"],
        asset_type=row["asset_type"],
        refrigerated=bool(refrig),
        latest_idle_minutes=_safe(latest["idle_minutes"]) if latest is not None else None,
        latest_trip_count=int(latest["trip_count"]) if latest is not None else None,
        latest_engine_hours=_safe(latest["engine_hours"]) if latest is not None else None,
        latest_battery_voltage=_safe(latest["battery_min_voltage"]) if latest is not None else None,
        latest_refrigeration_temp=_safe(latest.get("refrigeration_avg_temp_c")) if latest is not None else None,
        latest_odometer_km=_safe(latest["odometer_km"]) if latest is not None else None,
        alert_count=len(asset_alerts),
        critical_alert_count=critical_count,
        status=_derive_status(alerts_df, asset_id),
    )


# ---------------------------------------------------------------------------
# GET /api/fleet/summary
# ---------------------------------------------------------------------------

@router.get("/summary", response_model=FleetSummaryResponse)
async def fleet_summary(request: Request) -> FleetSummaryResponse:
    """Dashboard-level fleet KPIs."""
    fleet = request.app.state.fleet_data
    assets = fleet.assets
    alerts = fleet.alerts
    metrics = fleet.metrics

    total = len(assets)
    # "Active" = had at least one trip in the data
    active_ids = set(metrics[metrics["trip_count"] > 0]["asset_id"].unique())
    active = len(active_ids)

    # Alert breakdown by severity
    critical = int((alerts["severity"] == "high").sum())
    warning = int((alerts["severity"] == "medium").sum())
    info = int((alerts["severity"] == "low").sum())

    # Fleet health: 100 - penalty for alerts (critical=10pts, warning=3pts, info=1pt)
    penalty = critical * 10 + warning * 3 + info * 1
    health = max(0.0, min(100.0, 100.0 - penalty))

    # Regions
    regions = sorted(assets["region"].unique().tolist())

    return FleetSummaryResponse(
        total_vehicles=total,
        active_vehicles=active,
        inactive_vehicles=total - active,
        total_alerts=len(alerts),
        critical_alerts=critical,
        warning_alerts=warning,
        info_alerts=info,
        fleet_health_score=round(health, 1),
        regions=regions,
    )


# ---------------------------------------------------------------------------
# GET /api/fleet/vehicles
# ---------------------------------------------------------------------------

@router.get("/vehicles", response_model=VehicleListResponse)
async def vehicle_list(
    request: Request,
    region: Optional[str] = Query(None, description="Filter by region"),
    asset_type: Optional[str] = Query(None, description="Filter by type (truck/van/trailer)"),
    status: Optional[str] = Query(None, description="Filter by status (normal/warning/critical)"),
    search: Optional[str] = Query(None, description="Search by ID or name"),
) -> VehicleListResponse:
    """List all vehicles with optional filters."""
    fleet = request.app.state.fleet_data
    assets = fleet.assets.copy()

    if region:
        assets = assets[assets["region"].str.lower() == region.lower()]
    if asset_type:
        assets = assets[assets["asset_type"].str.lower() == asset_type.lower()]
    if search:
        mask = (
            assets["asset_id"].str.contains(search, case=False, na=False)
            | assets["asset_name"].str.contains(search, case=False, na=False)
        )
        assets = assets[mask]

    vehicles = [
        _build_vehicle_response(row, fleet.metrics, fleet.alerts)
        for _, row in assets.iterrows()
    ]

    if status:
        vehicles = [v for v in vehicles if v.status == status.lower()]

    return VehicleListResponse(vehicles=vehicles, total=len(vehicles))


# ---------------------------------------------------------------------------
# GET /api/fleet/vehicles/{asset_id}
# ---------------------------------------------------------------------------

@router.get("/vehicles/{asset_id}", response_model=VehicleDetailResponse)
async def vehicle_detail(asset_id: str, request: Request) -> VehicleDetailResponse:
    """Detailed view of a single vehicle."""
    fleet = request.app.state.fleet_data
    asset_row = fleet.assets[fleet.assets["asset_id"] == asset_id]

    if asset_row.empty:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail=f"Asset {asset_id} not found")

    row = asset_row.iloc[0]
    base = _build_vehicle_response(row, fleet.metrics, fleet.alerts)

    # Full metrics history
    asset_metrics = fleet.metrics[fleet.metrics["asset_id"] == asset_id].copy()
    asset_metrics["date"] = asset_metrics["date"].dt.strftime("%Y-%m-%d")
    metrics_history = asset_metrics.replace({np.nan: None}).to_dict(orient="records")

    # Full alert history
    asset_alerts = fleet.alerts[fleet.alerts["asset_id"] == asset_id].copy()
    asset_alerts["timestamp"] = asset_alerts["timestamp"].dt.strftime("%Y-%m-%dT%H:%M:%SZ")
    alert_history = asset_alerts.to_dict(orient="records")

    return VehicleDetailResponse(
        **base.model_dump(),
        metrics_history=metrics_history,
        alert_history=alert_history,
    )


# ---------------------------------------------------------------------------
# GET /api/fleet/alerts
# ---------------------------------------------------------------------------

@router.get("/alerts", response_model=AlertListResponse)
async def alert_list(
    request: Request,
    severity: Optional[str] = Query(None, description="Filter: high/medium/low"),
    alert_type: Optional[str] = Query(None, description="Filter by alert type"),
    asset_id: Optional[str] = Query(None, description="Filter by asset ID"),
) -> AlertListResponse:
    """List all alerts with optional filters."""
    fleet = request.app.state.fleet_data
    alerts = fleet.alerts.copy()

    if severity:
        alerts = alerts[alerts["severity"].str.lower() == severity.lower()]
    if alert_type:
        alerts = alerts[alerts["alert_type"].str.lower() == alert_type.lower()]
    if asset_id:
        alerts = alerts[alerts["asset_id"] == asset_id]

    # Join with asset names
    merged = alerts.merge(
        fleet.assets[["asset_id", "asset_name"]],
        on="asset_id",
        how="left",
    )

    alert_items = []
    for _, row in merged.iterrows():
        alert_items.append(AlertResponse(
            timestamp=row["timestamp"].strftime("%Y-%m-%dT%H:%M:%SZ"),
            asset_id=row["asset_id"],
            asset_name=row.get("asset_name"),
            alert_type=row["alert_type"],
            severity=row["severity"],
            sensor_value=str(row["sensor_value"]),
            note=str(row["note"]),
        ))

    # Sort by timestamp descending (most recent first)
    alert_items.sort(key=lambda a: a.timestamp, reverse=True)

    all_alerts = fleet.alerts
    return AlertListResponse(
        alerts=alert_items,
        total=len(alert_items),
        critical=int((all_alerts["severity"] == "high").sum()),
        warning=int((all_alerts["severity"] == "medium").sum()),
        info=int((all_alerts["severity"] == "low").sum()),
    )


# ---------------------------------------------------------------------------
# GET /api/fleet/metrics
# ---------------------------------------------------------------------------

@router.get("/metrics", response_model=MetricsResponse)
async def metrics_list(
    request: Request,
    asset_id: Optional[str] = Query(None, description="Filter by asset ID"),
    date: Optional[str] = Query(None, description="Filter by date (YYYY-MM-DD)"),
) -> MetricsResponse:
    """Daily asset metrics."""
    fleet = request.app.state.fleet_data
    metrics = fleet.metrics.copy()

    if asset_id:
        metrics = metrics[metrics["asset_id"] == asset_id]
    if date:
        metrics = metrics[metrics["date"].dt.strftime("%Y-%m-%d") == date]

    metrics["date"] = metrics["date"].dt.strftime("%Y-%m-%d")
    records = metrics.replace({np.nan: None}).to_dict(orient="records")

    return MetricsResponse(metrics=records, total=len(records))


# ---------------------------------------------------------------------------
# GET /api/fleet/maintenance
# ---------------------------------------------------------------------------

@router.get("/maintenance", response_model=MaintenanceResponse)
async def maintenance_schedule(request: Request) -> MaintenanceResponse:
    """Maintenance items derived from alert patterns and metrics."""
    fleet = request.app.state.fleet_data
    alerts = fleet.alerts
    assets = fleet.assets

    items: list[MaintenanceItem] = []

    # Group alerts by asset to detect recurring issues needing maintenance
    for asset_id in assets["asset_id"].unique():
        asset_alerts = alerts[alerts["asset_id"] == asset_id]
        asset_name = assets[assets["asset_id"] == asset_id].iloc[0]["asset_name"]

        if asset_alerts.empty:
            continue

        # Battery-related maintenance
        battery_alerts = asset_alerts[asset_alerts["alert_type"] == "battery_low"]
        if not battery_alerts.empty:
            latest_ts = battery_alerts["timestamp"].max().strftime("%Y-%m-%dT%H:%M:%SZ")
            count = len(battery_alerts)
            items.append(MaintenanceItem(
                asset_id=asset_id,
                asset_name=asset_name,
                maintenance_type="Battery Inspection",
                severity="high" if count >= 3 else "medium",
                description=f"Recurring low battery alerts ({count} events). "
                            f"Inspect battery health and charging system.",
                due_status="overdue" if count >= 3 else "upcoming",
                last_alert_timestamp=latest_ts,
                alert_count=count,
            ))

        # Temperature-related maintenance (refrigerated units)
        temp_alerts = asset_alerts[asset_alerts["alert_type"] == "temperature_high"]
        if not temp_alerts.empty:
            latest_ts = temp_alerts["timestamp"].max().strftime("%Y-%m-%dT%H:%M:%SZ")
            count = len(temp_alerts)
            items.append(MaintenanceItem(
                asset_id=asset_id,
                asset_name=asset_name,
                maintenance_type="Refrigeration Service",
                severity="high",
                description=f"Temperature exceedance events ({count} alerts). "
                            f"Inspect refrigeration unit and door seals.",
                due_status="overdue" if count >= 2 else "upcoming",
                last_alert_timestamp=latest_ts,
                alert_count=count,
            ))

        # Error code related
        error_alerts = asset_alerts[asset_alerts["alert_type"] == "error_code"]
        if not error_alerts.empty:
            latest_ts = error_alerts["timestamp"].max().strftime("%Y-%m-%dT%H:%M:%SZ")
            count = len(error_alerts)
            # Get unique error codes
            codes = error_alerts["sensor_value"].unique().tolist()
            items.append(MaintenanceItem(
                asset_id=asset_id,
                asset_name=asset_name,
                maintenance_type="Diagnostic Check",
                severity="high" if any(
                    error_alerts["severity"] == "high"
                ) else "medium",
                description=f"Error codes {', '.join(str(c) for c in codes)} "
                            f"triggered {count} time(s). Run device diagnostics.",
                due_status="upcoming",
                last_alert_timestamp=latest_ts,
                alert_count=count,
            ))

    upcoming = [i for i in items if i.due_status in ("upcoming", "overdue")]
    completed: list[MaintenanceItem] = []  # No completed data in the CSV

    return MaintenanceResponse(
        upcoming=upcoming,
        completed=completed,
        total=len(items),
    )


# ---------------------------------------------------------------------------
# GET /api/fleet/drivers
# ---------------------------------------------------------------------------

@router.get("/drivers", response_model=DriverScoreboardResponse)
async def driver_scoreboard(request: Request) -> DriverScoreboardResponse:
    """Driver performance scorecards derived from asset metrics.

    Scores are normalised 0-100 where higher is better:
    - Idle score: lower idle minutes = higher score
    - Trip score: more trips = higher score
    - Efficiency: engine hours per trip ratio
    """
    fleet = request.app.state.fleet_data
    metrics = fleet.metrics
    assets = fleet.assets

    # Aggregate metrics per asset (mean across available days)
    agg = metrics.groupby("asset_id").agg(
        avg_idle=("idle_minutes", "mean"),
        avg_trips=("trip_count", "mean"),
        avg_engine_hours=("engine_hours", "mean"),
    ).reset_index()

    # Normalise to 0-100 scores
    idle_min, idle_max = agg["avg_idle"].min(), agg["avg_idle"].max()
    trip_min, trip_max = agg["avg_trips"].min(), agg["avg_trips"].max()

    drivers: list[DriverScore] = []
    for _, row in agg.iterrows():
        asset_id = row["asset_id"]
        asset_info = assets[assets["asset_id"] == asset_id]
        if asset_info.empty:
            continue
        asset_info = asset_info.iloc[0]

        # Idle score: inverse (less idle = better)
        idle_range = idle_max - idle_min if idle_max != idle_min else 1
        idle_score = round(100 * (1 - (row["avg_idle"] - idle_min) / idle_range), 1)

        # Trip score: more trips = better
        trip_range = trip_max - trip_min if trip_max != trip_min else 1
        trip_score = round(100 * (row["avg_trips"] - trip_min) / trip_range, 1)

        # Efficiency: trips per engine hour (higher = more efficient)
        eff = row["avg_trips"] / row["avg_engine_hours"] if row["avg_engine_hours"] > 0 else 0
        eff_score = round(min(100, eff * 50), 1)  # Scale factor

        composite = round(idle_score * 0.35 + trip_score * 0.35 + eff_score * 0.30, 1)

        # Letter grade
        if composite >= 85:
            grade = "A"
        elif composite >= 70:
            grade = "B"
        elif composite >= 55:
            grade = "C"
        elif composite >= 40:
            grade = "D"
        else:
            grade = "F"

        drivers.append(DriverScore(
            asset_id=asset_id,
            asset_name=asset_info["asset_name"],
            region=asset_info["region"],
            idle_score=idle_score,
            trip_score=trip_score,
            efficiency_score=eff_score,
            composite_score=composite,
            grade=grade,
        ))

    # Sort by composite score descending
    drivers.sort(key=lambda d: d.composite_score, reverse=True)

    fleet_avg = round(
        sum(d.composite_score for d in drivers) / len(drivers) if drivers else 0,
        1,
    )

    return DriverScoreboardResponse(drivers=drivers, fleet_average=fleet_avg)


# ---------------------------------------------------------------------------
# GET /api/fleet/reports/fuel
# ---------------------------------------------------------------------------

@router.get("/reports/fuel", response_model=FuelReportResponse)
async def fuel_report(request: Request) -> FuelReportResponse:
    """Fuel efficiency report data (derived from engine hours and distance)."""
    fleet = request.app.state.fleet_data
    metrics = fleet.metrics
    assets = fleet.assets

    # Calculate per-asset fuel efficiency proxy: km per engine hour
    agg = metrics.groupby("asset_id").agg(
        total_engine_hours=("engine_hours", "sum"),
        min_odometer=("odometer_km", "min"),
        max_odometer=("odometer_km", "max"),
    ).reset_index()

    agg["distance_km"] = agg["max_odometer"] - agg["min_odometer"]
    agg["km_per_engine_hour"] = agg.apply(
        lambda r: round(r["distance_km"] / r["total_engine_hours"], 2)
        if r["total_engine_hours"] > 0 else 0,
        axis=1,
    )

    # Merge with asset info
    merged = agg.merge(assets[["asset_id", "asset_name", "region", "asset_type"]], on="asset_id")

    by_asset = merged[[
        "asset_id", "asset_name", "region", "asset_type",
        "total_engine_hours", "distance_km", "km_per_engine_hour",
    ]].replace({np.nan: None}).to_dict(orient="records")

    # By region
    by_region = merged.groupby("region").agg(
        avg_km_per_engine_hour=("km_per_engine_hour", "mean"),
        total_distance=("distance_km", "sum"),
        total_engine_hours=("total_engine_hours", "sum"),
        vehicle_count=("asset_id", "count"),
    ).reset_index().round(2).to_dict(orient="records")

    fleet_avg = round(merged["km_per_engine_hour"].mean(), 2) if not merged.empty else None

    return FuelReportResponse(
        by_asset=by_asset,
        by_region=by_region,
        fleet_average_efficiency=fleet_avg,
    )
