"""Service layer — provides a programmatic API for running corrections and evaluations.

This module acts as the central orchestrator. It can be used directly from Python,
from the CLI, or exposed via HTTP (see server.py).
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Dict, List, Optional

from .corrector import AddressCorrector, CorrectionResult
from .evaluation import (
    AddressTestCase,
    EvaluationDataset,
    EvaluationResult,
    Golden,
    AccuracyMetric,
    CompletenessMetric,
    OverCorrectionMetric,
    UnderCorrectionMetric,
    ConfidenceCalibrationMetric,
    FieldLevelAccuracyMetric,
    evaluate,
)
from .dashboard import DashboardGenerator


# Default metric suite
def default_metrics(threshold: float = 0.5):
    return [
        AccuracyMetric(threshold=threshold),
        CompletenessMetric(threshold=threshold),
        OverCorrectionMetric(threshold=threshold),
        UnderCorrectionMetric(threshold=threshold),
        ConfidenceCalibrationMetric(threshold=threshold),
        FieldLevelAccuracyMetric(threshold=threshold),
    ]


class AddressTracerService:
    """High-level service for address correction, evaluation, and dashboard generation."""

    def __init__(self):
        self.corrector = AddressCorrector()
        self.dashboard_gen = DashboardGenerator()

    # -- Correction ----------------------------------------------------------

    def correct(self, address: str) -> Dict:
        """Correct a single address and return the trace artifact."""
        result = self.corrector.correct(address)
        return result.trace.to_dict()

    def correct_batch(self, addresses: List[str]) -> List[Dict]:
        """Correct multiple addresses and return their trace artifacts."""
        results = self.corrector.correct_batch(addresses)
        return [r.trace.to_dict() for r in results]

    # -- Evaluation ----------------------------------------------------------

    def evaluate_dataset(
        self,
        dataset_path: str,
        metrics: Optional[list] = None,
        identifier: str = "",
    ) -> EvaluationResult:
        """Load a golden dataset, run the corrector, and evaluate."""
        ds = EvaluationDataset.from_json(dataset_path)
        ds.generate_test_cases(self.corrector)
        return evaluate(
            ds,
            metrics=metrics or default_metrics(),
            identifier=identifier,
        )

    def evaluate_goldens(
        self,
        goldens: List[Dict],
        metrics: Optional[list] = None,
        identifier: str = "",
    ) -> EvaluationResult:
        """Evaluate from in-memory golden records (dicts)."""
        ds = EvaluationDataset()
        for g in goldens:
            ds.add_golden(Golden(
                input=g["input"],
                expected_output=g["expected_output"],
                expected_corrections=g.get("expected_corrections"),
                tags=g.get("tags", []),
                name=g.get("name", ""),
            ))
        ds.generate_test_cases(self.corrector)
        return evaluate(
            ds,
            metrics=metrics or default_metrics(),
            identifier=identifier,
        )

    # -- Dashboard -----------------------------------------------------------

    def generate_dashboard(
        self,
        eval_result: EvaluationResult,
        output_path: str = "dashboard.html",
        title: str = "Address Correction Evaluation",
    ) -> str:
        """Generate an HTML dashboard from evaluation results."""
        return self.dashboard_gen.write(eval_result, output_path, title=title)

    # -- Full pipeline -------------------------------------------------------

    def run_full_pipeline(
        self,
        dataset_path: str,
        dashboard_path: str = "dashboard.html",
        identifier: str = "",
    ) -> Dict:
        """Run correction, evaluation, and dashboard generation in one call."""
        eval_result = self.evaluate_dataset(dataset_path, identifier=identifier)
        self.generate_dashboard(eval_result, dashboard_path)
        return {
            "summary": {
                "total": eval_result.total,
                "passed": eval_result.passed,
                "failed": eval_result.failed,
                "pass_rate": round(eval_result.pass_rate, 4),
            },
            "dashboard": dashboard_path,
        }
