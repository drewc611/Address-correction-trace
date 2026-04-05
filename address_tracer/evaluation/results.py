"""Evaluation result models — individual metric results, test results, and aggregate results."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional


@dataclass
class MetricResult:
    """Result of a single metric evaluation on a single test case."""
    metric_name: str
    score: float
    threshold: float
    success: bool
    reason: str = ""

    def to_dict(self) -> dict:
        return {
            "metric": self.metric_name,
            "score": round(self.score, 4),
            "threshold": self.threshold,
            "success": self.success,
            "reason": self.reason,
        }


@dataclass
class TestResult:
    """Result of evaluating one test case against all metrics."""
    name: str
    input: str
    actual_output: str
    expected_output: Optional[str]
    success: bool
    metrics_data: List[MetricResult] = field(default_factory=list)
    actual_corrections: List[Dict[str, str]] = field(default_factory=list)
    expected_corrections: Optional[List[Dict[str, str]]] = None
    confidence: float = 0.0
    completion_time: float = 0.0
    tags: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "input": self.input,
            "actual_output": self.actual_output,
            "expected_output": self.expected_output,
            "success": self.success,
            "metrics": [m.to_dict() for m in self.metrics_data],
            "actual_corrections": self.actual_corrections,
            "expected_corrections": self.expected_corrections,
            "confidence": self.confidence,
            "completion_time": self.completion_time,
            "tags": self.tags,
        }


@dataclass
class EvaluationResult:
    """Aggregate result of evaluating a full dataset."""
    test_results: List[TestResult] = field(default_factory=list)
    timestamp: str = ""
    identifier: str = ""

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now(timezone.utc).isoformat()

    @property
    def total(self) -> int:
        return len(self.test_results)

    @property
    def passed(self) -> int:
        return sum(1 for r in self.test_results if r.success)

    @property
    def failed(self) -> int:
        return self.total - self.passed

    @property
    def pass_rate(self) -> float:
        if self.total == 0:
            return float("nan")
        return self.passed / self.total

    @property
    def metric_summaries(self) -> Dict[str, Dict[str, float]]:
        """Aggregate stats per metric across all test results."""
        from collections import defaultdict
        scores: Dict[str, List[float]] = defaultdict(list)
        for tr in self.test_results:
            for md in tr.metrics_data:
                scores[md.metric_name].append(md.score)

        summaries = {}
        for name, vals in scores.items():
            summaries[name] = {
                "mean": sum(vals) / len(vals),
                "min": min(vals),
                "max": max(vals),
                "count": len(vals),
                "pass_rate": sum(1 for v in vals if v >= self._threshold_for(name)) / len(vals),
            }
        return summaries

    def _threshold_for(self, metric_name: str) -> float:
        """Look up the threshold used for a given metric."""
        for tr in self.test_results:
            for md in tr.metrics_data:
                if md.metric_name == metric_name:
                    return md.threshold
        return 0.5

    def to_dict(self) -> dict:
        return {
            "timestamp": self.timestamp,
            "identifier": self.identifier,
            "summary": {
                "total": self.total,
                "passed": self.passed,
                "failed": self.failed,
                "pass_rate": round(self.pass_rate, 4),
            },
            "metric_summaries": {
                k: {sk: round(sv, 4) for sk, sv in v.items()}
                for k, v in self.metric_summaries.items()
            },
            "test_results": [r.to_dict() for r in self.test_results],
        }
