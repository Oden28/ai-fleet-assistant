"""Tests for the data pipeline — code execution sandbox."""

import pytest
import pandas as pd
import numpy as np

from src.preprocessor import FleetData
from src.data_pipeline import DataPipeline


class TestCodeExecution:
    """Test the sandboxed pandas code execution."""

    @pytest.fixture
    def pipeline(self):
        data = FleetData()
        return DataPipeline(fleet_data=data, openai_client=None)

    def test_simple_code_executes(self, pipeline):
        code = "result = len(assets)"
        result, success = pipeline._execute_code(code)
        assert success is True
        assert "12" in result

    def test_pandas_operations_work(self, pipeline):
        code = (
            "result = metrics[metrics['date'] == '2026-03-11']"
            ".sort_values('idle_minutes', ascending=False)"
            ".head(5)[['asset_id', 'idle_minutes']]"
        )
        result, success = pipeline._execute_code(code)
        assert success is True
        assert "A110" in result  # A110 had highest idle on 03-11

    def test_no_builtins_access(self, pipeline):
        code = "result = open('/etc/passwd').read()"
        result, success = pipeline._execute_code(code)
        assert success is False
        assert "error" in result.lower() or "Error" in result

    def test_no_imports_allowed(self, pipeline):
        code = "import os; result = os.listdir('/')"
        result, success = pipeline._execute_code(code)
        assert success is False

    def test_missing_result_variable(self, pipeline):
        code = "x = 42"
        result, success = pipeline._execute_code(code)
        assert success is True
        assert "No 'result' variable" in result

    def test_alert_dedup_reflected(self, pipeline):
        code = "result = len(alerts)"
        result, success = pipeline._execute_code(code)
        assert success is True
        assert "14" in result  # 15 rows minus 1 duplicate
