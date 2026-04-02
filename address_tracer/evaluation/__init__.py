"""Evaluation framework for address correction — deepeval-style test cases, metrics, and evaluation."""

from .test_case import AddressTestCase
from .metrics import (
    BaseMetric,
    AccuracyMetric,
    CompletenessMetric,
    OverCorrectionMetric,
    UnderCorrectionMetric,
    ConfidenceCalibrationMetric,
    FieldLevelAccuracyMetric,
)
from .evaluate import evaluate, assert_test
from .results import MetricResult, TestResult, EvaluationResult
from .dataset import EvaluationDataset, Golden

__all__ = [
    "AddressTestCase",
    "BaseMetric",
    "AccuracyMetric",
    "CompletenessMetric",
    "OverCorrectionMetric",
    "UnderCorrectionMetric",
    "ConfidenceCalibrationMetric",
    "FieldLevelAccuracyMetric",
    "evaluate",
    "assert_test",
    "MetricResult",
    "TestResult",
    "EvaluationResult",
    "EvaluationDataset",
    "Golden",
]
