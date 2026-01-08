from __future__ import annotations

from dataclasses import dataclass


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
