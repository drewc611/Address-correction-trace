"""Core evaluation functions — evaluate() for batch runs, assert_test() for pytest integration."""

from __future__ import annotations

import time
from typing import List, Optional, Union

from .test_case import AddressTestCase
from .metrics import BaseMetric
from .results import MetricResult, TestResult, EvaluationResult
from .dataset import EvaluationDataset


def evaluate(
    test_cases: Union[List[AddressTestCase], EvaluationDataset],
    metrics: List[BaseMetric],
    identifier: str = "",
) -> EvaluationResult:
    """Evaluate a batch of test cases against all metrics.

    Follows deepeval's evaluate() signature. Runs each metric's measure()
    on every test case and aggregates the results.

    Args:
        test_cases: List of AddressTestCase or an EvaluationDataset.
        metrics: List of metric instances to evaluate.
        identifier: Optional label for this evaluation run.

    Returns:
        EvaluationResult with per-test and aggregate scores.
    """
    if isinstance(test_cases, EvaluationDataset):
        cases = test_cases.test_cases
    else:
        cases = test_cases

    eval_result = EvaluationResult(identifier=identifier)

    for i, tc in enumerate(cases):
        case_name = tc.name or f"test_case_{i}"
        metric_results = []
        all_passed = True

        for metric in metrics:
            metric.score = None
            metric.reason = ""
            metric.success = False

            metric.measure(tc)

            mr = MetricResult(
                metric_name=metric.name,
                score=metric.score if metric.score is not None else 0.0,
                threshold=metric.threshold,
                success=metric.success,
                reason=metric.reason,
            )
            metric_results.append(mr)

            if not metric.success:
                all_passed = False

        test_result = TestResult(
            name=case_name,
            input=tc.input,
            actual_output=tc.actual_output,
            expected_output=tc.expected_output,
            success=all_passed,
            metrics_data=metric_results,
            actual_corrections=tc.actual_corrections,
            expected_corrections=tc.expected_corrections,
            confidence=tc.confidence,
            completion_time=tc.completion_time,
            tags=tc.tags,
        )
        eval_result.test_results.append(test_result)

    return eval_result


def assert_test(
    test_case: AddressTestCase,
    metrics: List[BaseMetric],
) -> None:
    """Evaluate a single test case and raise AssertionError if any metric fails.

    Designed for pytest integration, mirroring deepeval's assert_test().

    Usage:
        def test_address_correction():
            tc = AddressTestCase(input=..., actual_output=..., expected_output=...)
            assert_test(tc, [AccuracyMetric(threshold=0.8)])
    """
    result = evaluate([test_case], metrics)
    tr = result.test_results[0]

    failures = [m for m in tr.metrics_data if not m.success]
    if failures:
        msgs = []
        for f in failures:
            msgs.append(
                f"  {f.metric_name}: score={f.score:.4f} "
                f"(threshold={f.threshold}) — {f.reason}"
            )
        raise AssertionError(
            f"Address test case '{tr.name}' failed {len(failures)} metric(s):\n"
            + "\n".join(msgs)
        )
