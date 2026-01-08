from __future__ import annotations

from dataclasses import dataclass

import pandas as pd


@dataclass
class ErrorSummary:
    mean_error: float
    max_error: float
    threshold: float

    @property
    def is_acceptable(self) -> bool:
        return self.max_error <= self.threshold


def summarize_errors(errors: list[float], threshold: float) -> ErrorSummary:
    if not errors:
        return ErrorSummary(mean_error=0.0, max_error=0.0, threshold=threshold)
    mean_error = sum(errors) / len(errors)
    max_error = max(errors)
    return ErrorSummary(mean_error=mean_error, max_error=max_error, threshold=threshold)


def select_metric_column(summary_df: pd.DataFrame) -> str | None:
    candidates = [c for c in summary_df.columns if c.startswith("non_rigid") and c.endswith("TRE")]
    if not candidates:
        candidates = [c for c in summary_df.columns if c.startswith("rigid") and c.endswith("TRE")]
    if not candidates:
        candidates = [c for c in summary_df.columns if c.endswith("TRE")]
    if not candidates:
        candidates = [c for c in summary_df.columns if c.endswith("D")]
    return candidates[0] if candidates else None


def summarize_error_dataframe(summary_df: pd.DataFrame) -> dict:
    metric_column = select_metric_column(summary_df)
    if metric_column is None:
        return {
            "metric_column": None,
            "values": [],
            "mean": 0.0,
            "max": 0.0,
        }
    values = summary_df[metric_column].fillna(0).tolist()
    return {
        "metric_column": metric_column,
        "values": values,
        "mean": float(sum(values) / len(values)) if values else 0.0,
        "max": float(max(values)) if values else 0.0,
    }
