"""Evaluation metrics for address correction — modeled after deepeval's BaseMetric.

Each metric implements measure() which scores a test case and sets self.score,
self.success, and self.reason. Metrics detect specific AI behaviors:
over-correction, under-correction, confidence miscalibration, field-level errors.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List, Optional

from .test_case import AddressTestCase


class BaseMetric(ABC):
    """Abstract base metric following deepeval's pattern."""

    def __init__(
        self,
        threshold: float = 0.5,
        include_reason: bool = True,
        strict_mode: bool = False,
    ):
        self.threshold = threshold
        self.include_reason = include_reason
        self.strict_mode = strict_mode
        self.score: Optional[float] = None
        self.reason: str = ""
        self.success: bool = False

    @property
    @abstractmethod
    def name(self) -> str:
        ...

    @abstractmethod
    def measure(self, test_case: AddressTestCase) -> float:
        """Evaluate the test case. Must set self.score, self.success, self.reason."""
        ...

    def is_successful(self) -> bool:
        if self.score is None:
            return False
        if self.strict_mode:
            return self.score == 1.0
        return self.score >= self.threshold

    def __repr__(self):
        return f"{self.name}(score={self.score}, threshold={self.threshold}, success={self.success})"


class AccuracyMetric(BaseMetric):
    """Measures whether the corrected address matches the expected output.

    Detects: wrong corrections, hallucinated fields, data loss.
    """

    @property
    def name(self) -> str:
        return "accuracy"

    def measure(self, test_case: AddressTestCase) -> float:
        if not test_case.expected_output:
            self.score = 1.0 if test_case.status != "error" else 0.0
            self.reason = "No expected output provided; scored on error-free completion."
            self.success = self.is_successful()
            return self.score

        expected_norm = _normalize(test_case.expected_output)
        actual_norm = _normalize(test_case.actual_output)

        if expected_norm == actual_norm:
            self.score = 1.0
            self.reason = "Corrected address exactly matches expected output."
        else:
            # Partial credit: ratio of matching tokens
            expected_tokens = set(expected_norm.split())
            actual_tokens = set(actual_norm.split())
            if expected_tokens:
                overlap = len(expected_tokens & actual_tokens)
                self.score = overlap / max(len(expected_tokens), len(actual_tokens))
                diff = expected_tokens.symmetric_difference(actual_tokens)
                self.reason = f"Partial match. Differences: {diff}"
            else:
                self.score = 0.0
                self.reason = "Expected output is empty after normalization."

        self.success = self.is_successful()
        return self.score


class CompletenessMetric(BaseMetric):
    """Measures whether all expected corrections were applied.

    Detects: missed corrections (under-correction at the correction level).
    """

    @property
    def name(self) -> str:
        return "completeness"

    def measure(self, test_case: AddressTestCase) -> float:
        if not test_case.expected_corrections:
            self.score = 1.0
            self.reason = "No expected corrections specified; assumed complete."
            self.success = self.is_successful()
            return self.score

        expected_fields = {c["field"] for c in test_case.expected_corrections}
        actual_fields = {c["field"] for c in test_case.actual_corrections}

        applied = expected_fields & actual_fields
        missed = expected_fields - actual_fields

        self.score = len(applied) / len(expected_fields) if expected_fields else 1.0

        if missed:
            self.reason = f"Missed corrections on fields: {missed}"
        else:
            self.reason = "All expected corrections were applied."

        self.success = self.is_successful()
        return self.score


class OverCorrectionMetric(BaseMetric):
    """Detects corrections that were applied but should not have been.

    AI behavior detected: hallucinated fixes, unnecessary changes, data mutation.
    Higher score = less over-correction (good).
    """

    @property
    def name(self) -> str:
        return "over_correction"

    def measure(self, test_case: AddressTestCase) -> float:
        if not test_case.expected_corrections:
            # Without golden corrections, flag any correction on an already-correct input
            if test_case.input == test_case.expected_output and test_case.actual_corrections:
                self.score = 0.0
                self.reason = (
                    f"Input was already correct but {len(test_case.actual_corrections)} "
                    f"corrections were applied: over-correction detected."
                )
                self.success = self.is_successful()
                return self.score
            self.score = 1.0
            self.reason = "No expected corrections to compare; no over-correction detected."
            self.success = self.is_successful()
            return self.score

        expected_fields = {c["field"] for c in test_case.expected_corrections}
        actual_fields = {c["field"] for c in test_case.actual_corrections}
        spurious = actual_fields - expected_fields

        if not test_case.actual_corrections:
            self.score = 1.0
            self.reason = "No corrections applied; no over-correction."
        elif spurious:
            self.score = max(0.0, 1.0 - len(spurious) / len(test_case.actual_corrections))
            self.reason = f"Spurious corrections on fields: {spurious}"
        else:
            self.score = 1.0
            self.reason = "All corrections correspond to expected changes."

        self.success = self.is_successful()
        return self.score


class UnderCorrectionMetric(CompletenessMetric):
    """Alias for CompletenessMetric — measures missed corrections.

    Kept for backwards compatibility. Prefer CompletenessMetric directly.
    """

    @property
    def name(self) -> str:
        return "under_correction"


class ConfidenceCalibrationMetric(BaseMetric):
    """Measures whether reported confidence aligns with actual accuracy.

    AI behavior detected: overconfident wrong answers, underconfident correct ones.
    A well-calibrated system reports high confidence when correct and low when wrong.
    """

    @property
    def name(self) -> str:
        return "confidence_calibration"

    def measure(self, test_case: AddressTestCase) -> float:
        if not test_case.expected_output:
            self.score = 1.0
            self.reason = "No expected output; cannot assess calibration."
            self.success = self.is_successful()
            return self.score

        is_correct = _normalize(test_case.actual_output) == _normalize(test_case.expected_output)
        confidence = test_case.confidence

        if is_correct:
            # Correct answer: confidence should be high
            self.score = confidence
            if confidence < 0.7:
                self.reason = f"Correct answer but underconfident ({confidence:.2f}). System doubts valid corrections."
            else:
                self.reason = f"Well-calibrated: correct answer with confidence {confidence:.2f}."
        else:
            # Wrong answer: confidence should be low
            self.score = 1.0 - confidence
            if confidence > 0.7:
                self.reason = f"Wrong answer but overconfident ({confidence:.2f}). System is not flagging its errors."
            else:
                self.reason = f"Appropriately uncertain: wrong answer with low confidence {confidence:.2f}."

        self.success = self.is_successful()
        return self.score


class FieldLevelAccuracyMetric(BaseMetric):
    """Evaluates correction accuracy at the individual field level.

    AI behavior detected: which specific fields the corrector gets wrong,
    revealing systematic weaknesses (e.g., always mangles ZIP codes).
    """

    def __init__(self, target_field: Optional[str] = None, **kwargs):
        super().__init__(**kwargs)
        self.target_field = target_field
        self.field_scores: dict = {}

    @property
    def name(self) -> str:
        if self.target_field:
            return f"field_accuracy_{self.target_field}"
        return "field_accuracy"

    def measure(self, test_case: AddressTestCase) -> float:
        if not test_case.expected_corrections:
            self.score = 1.0
            self.reason = "No expected corrections to compare field-level accuracy."
            self.success = self.is_successful()
            return self.score

        expected_map = {c["field"]: c.get("corrected", "") for c in test_case.expected_corrections}
        actual_map = {c["field"]: c.get("corrected", "") for c in test_case.actual_corrections}

        if self.target_field:
            fields_to_check = {self.target_field} & set(expected_map.keys())
        else:
            fields_to_check = set(expected_map.keys())

        if not fields_to_check:
            self.score = 1.0
            self.reason = "No relevant fields to evaluate."
            self.success = self.is_successful()
            return self.score

        correct = 0
        wrong_fields = []
        for f in fields_to_check:
            expected_val = _normalize(expected_map.get(f, ""))
            actual_val = _normalize(actual_map.get(f, ""))
            if expected_val == actual_val:
                correct += 1
                self.field_scores[f] = 1.0
            else:
                self.field_scores[f] = 0.0
                wrong_fields.append(f"{f}: expected '{expected_map.get(f)}' got '{actual_map.get(f, '<missing>')}'")

        self.score = correct / len(fields_to_check)

        if wrong_fields:
            self.reason = f"Field errors: {'; '.join(wrong_fields)}"
        else:
            self.reason = "All evaluated fields are correct."

        self.success = self.is_successful()
        return self.score


def _normalize(s: str) -> str:
    """Normalize a string for comparison: lowercase, collapse whitespace, strip punctuation."""
    import re
    s = s.lower().strip()
    s = re.sub(r"[,.\-#]+", " ", s)
    s = re.sub(r"\s+", " ", s)
    return s.strip()
