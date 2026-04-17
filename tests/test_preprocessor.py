"""Tests for the data preprocessor — validates cleaning, normalisation, and loading."""

import pandas as pd
import pytest

from src.preprocessor import normalise_asset_id, load_asset_registry, load_alert_events, FleetData


class TestNormaliseAssetId:
    """Test the asset ID normalisation function."""

    def test_legacy_format_normalised(self):
        assert normalise_asset_id("A-108") == "A108"

    def test_already_normal_unchanged(self):
        assert normalise_asset_id("A108") == "A108"

    def test_whitespace_stripped(self):
        assert normalise_asset_id("  A101  ") == "A101"

    def test_other_legacy_format(self):
        assert normalise_asset_id("B-42") == "B42"

    def test_non_matching_format_unchanged(self):
        assert normalise_asset_id("ASSET-001") == "ASSET-001"


class TestLoadAssetRegistry:
    """Test asset_registry.csv loading."""

    def test_loads_correct_count(self):
        df = load_asset_registry()
        assert len(df) == 12

    def test_all_ids_normalised(self):
        df = load_asset_registry()
        for aid in df["asset_id"]:
            assert "-" not in aid, f"ID {aid} still has a dash"

    def test_expected_columns(self):
        df = load_asset_registry()
        expected = {"asset_id", "asset_name", "region", "device_model", "asset_type", "refrigerated"}
        assert set(df.columns) == expected


class TestLoadAlertEvents:
    """Test alert_events.csv loading with deduplication."""

    def test_duplicate_removed(self):
        df = load_alert_events()
        # The original file has 15 data rows; one is a duplicate → 14 unique
        assert len(df) == 14

    def test_asset_ids_normalised(self):
        df = load_alert_events()
        for aid in df["asset_id"]:
            assert "-" not in aid, f"ID {aid} still has a dash"


class TestFleetData:
    """Test the FleetData container."""

    def test_creates_successfully(self):
        data = FleetData()
        assert len(data.assets) > 0
        assert len(data.metrics) > 0
        assert len(data.alerts) > 0

    def test_schema_summary_contains_tables(self):
        data = FleetData()
        summary = data.schema_summary()
        assert "asset_registry" in summary
        assert "daily_asset_metrics" in summary
        assert "alert_events" in summary

    def test_caveats_text_not_empty(self):
        data = FleetData()
        caveats = data.caveats_text()
        assert len(caveats) > 50
        assert "A-108" in caveats or "A108" in caveats
