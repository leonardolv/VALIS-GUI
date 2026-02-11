"""Tests for error metrics service."""
from __future__ import annotations

import pandas as pd
import pytest

from valis_workstation.services.error_metrics import (
    ErrorSummary,
    select_metric_column,
    summarize_error_dataframe,
    summarize_errors,
)


class TestErrorSummary:
    def test_acceptable_when_below_threshold(self) -> None:
        s = ErrorSummary(mean_error=1.0, max_error=4.0, threshold=5.0)
        assert s.is_acceptable

    def test_not_acceptable_when_above_threshold(self) -> None:
        s = ErrorSummary(mean_error=3.0, max_error=6.0, threshold=5.0)
        assert not s.is_acceptable

    def test_acceptable_at_boundary(self) -> None:
        s = ErrorSummary(mean_error=2.0, max_error=5.0, threshold=5.0)
        assert s.is_acceptable


class TestSummarizeErrors:
    def test_empty_list(self) -> None:
        result = summarize_errors([], threshold=5.0)
        assert result.mean_error == 0.0
        assert result.max_error == 0.0

    def test_single_value(self) -> None:
        result = summarize_errors([3.0], threshold=5.0)
        assert result.mean_error == 3.0
        assert result.max_error == 3.0

    def test_multiple_values(self) -> None:
        result = summarize_errors([1.0, 2.0, 3.0], threshold=5.0)
        assert result.mean_error == 2.0
        assert result.max_error == 3.0
        assert result.is_acceptable


class TestSelectMetricColumn:
    def test_prefers_non_rigid_tre(self) -> None:
        df = pd.DataFrame({
            "non_rigid_TRE": [1],
            "rigid_TRE": [2],
        })
        assert select_metric_column(df) == "non_rigid_TRE"

    def test_falls_back_to_rigid_tre(self) -> None:
        df = pd.DataFrame({
            "rigid_TRE": [1],
            "other_col": [2],
        })
        assert select_metric_column(df) == "rigid_TRE"

    def test_falls_back_to_any_tre(self) -> None:
        df = pd.DataFrame({
            "custom_TRE": [1],
            "other": [2],
        })
        assert select_metric_column(df) == "custom_TRE"

    def test_falls_back_to_d_column(self) -> None:
        df = pd.DataFrame({
            "displacement_D": [1],
            "other": [2],
        })
        assert select_metric_column(df) == "displacement_D"

    def test_returns_none_when_no_match(self) -> None:
        df = pd.DataFrame({"x": [1], "y": [2]})
        assert select_metric_column(df) is None


class TestSummarizeErrorDataframe:
    def test_with_valid_column(self) -> None:
        df = pd.DataFrame({"non_rigid_TRE": [1.0, 2.0, 3.0]})
        result = summarize_error_dataframe(df)
        assert result["metric_column"] == "non_rigid_TRE"
        assert result["mean"] == 2.0
        assert result["max"] == 3.0
        assert len(result["values"]) == 3

    def test_with_no_valid_column(self) -> None:
        df = pd.DataFrame({"x": [1, 2, 3]})
        result = summarize_error_dataframe(df)
        assert result["metric_column"] is None
        assert result["values"] == []

    def test_handles_nan_values(self) -> None:
        df = pd.DataFrame({"rigid_TRE": [1.0, float("nan"), 3.0]})
        result = summarize_error_dataframe(df)
        # NaN should be filled with 0
        assert len(result["values"]) == 3
        assert 0.0 in result["values"]
