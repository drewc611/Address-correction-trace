"""Tests for the evaluation framework."""

import json
import tempfile

from address_tracer.corrector import AddressCorrector
from address_tracer.evaluation import (
    AddressTestCase,
    AccuracyMetric,
    CompletenessMetric,
    OverCorrectionMetric,
    UnderCorrectionMetric,
    ConfidenceCalibrationMetric,
    FieldLevelAccuracyMetric,
    evaluate,
    assert_test,
    EvaluationDataset,
    Golden,
)


# -- Test case helpers --------------------------------------------------------

def _make_case(**overrides) -> AddressTestCase:
    defaults = dict(
        input="123 N Main St, Springfield, illinois, 62704",
        actual_output="123 North Main Street, Springfield, IL, 62704",
        expected_output="123 North Main Street, Springfield, IL, 62704",
        actual_corrections=[
            {"field": "state", "original": "illinois", "corrected": "IL", "rule": "state_abbreviation"},
            {"field": "street_direction", "original": "N", "corrected": "North", "rule": "directional_expansion"},
            {"field": "street_suffix", "original": "St", "corrected": "Street", "rule": "suffix_standardization"},
        ],
        expected_corrections=[
            {"field": "state", "original": "illinois", "corrected": "IL", "rule": "state_abbreviation"},
            {"field": "street_direction", "original": "N", "corrected": "North", "rule": "directional_expansion"},
            {"field": "street_suffix", "original": "St", "corrected": "Street", "rule": "suffix_standardization"},
        ],
        confidence=0.85,
        status="corrected",
    )
    defaults.update(overrides)
    return AddressTestCase(**defaults)


# -- Metric tests -------------------------------------------------------------

class TestAccuracyMetric:
    def test_exact_match(self):
        tc = _make_case()
        m = AccuracyMetric(threshold=0.5)
        m.measure(tc)
        assert m.score == 1.0
        assert m.success

    def test_no_expected_output(self):
        tc = _make_case(expected_output=None, status="corrected")
        m = AccuracyMetric()
        m.measure(tc)
        assert m.score == 1.0

    def test_partial_match(self):
        tc = _make_case(actual_output="123 North Main Street, Springfield, XX, 62704")
        m = AccuracyMetric(threshold=0.5)
        m.measure(tc)
        assert 0 < m.score < 1.0


class TestCompletenessMetric:
    def test_all_corrections_applied(self):
        tc = _make_case()
        m = CompletenessMetric()
        m.measure(tc)
        assert m.score == 1.0

    def test_missing_correction(self):
        tc = _make_case(actual_corrections=[
            {"field": "state", "original": "illinois", "corrected": "IL", "rule": "state_abbreviation"},
        ])
        m = CompletenessMetric()
        m.measure(tc)
        assert m.score < 1.0
        assert "street_direction" in m.reason or "street_suffix" in m.reason


class TestOverCorrectionMetric:
    def test_no_over_correction(self):
        tc = _make_case()
        m = OverCorrectionMetric()
        m.measure(tc)
        assert m.score == 1.0

    def test_spurious_correction(self):
        tc = _make_case(actual_corrections=[
            {"field": "state", "original": "illinois", "corrected": "IL", "rule": "state_abbreviation"},
            {"field": "city", "original": "Springfield", "corrected": "SPRINGFIELD", "rule": "made_up_rule"},
        ])
        m = OverCorrectionMetric()
        m.measure(tc)
        assert m.score < 1.0
        assert "city" in m.reason


class TestUnderCorrectionMetric:
    def test_all_corrected(self):
        tc = _make_case()
        m = UnderCorrectionMetric()
        m.measure(tc)
        assert m.score == 1.0

    def test_missed_field(self):
        tc = _make_case(actual_corrections=[])
        m = UnderCorrectionMetric()
        m.measure(tc)
        assert m.score == 0.0


class TestConfidenceCalibrationMetric:
    def test_correct_and_confident(self):
        tc = _make_case(confidence=0.9)
        m = ConfidenceCalibrationMetric()
        m.measure(tc)
        assert m.score == 0.9

    def test_wrong_and_overconfident(self):
        tc = _make_case(
            actual_output="WRONG ADDRESS",
            confidence=0.95,
        )
        m = ConfidenceCalibrationMetric()
        m.measure(tc)
        assert m.score < 0.5
        assert "overconfident" in m.reason.lower()


class TestFieldLevelAccuracyMetric:
    def test_all_fields_correct(self):
        tc = _make_case()
        m = FieldLevelAccuracyMetric()
        m.measure(tc)
        assert m.score == 1.0

    def test_target_field(self):
        tc = _make_case()
        m = FieldLevelAccuracyMetric(target_field="state")
        m.measure(tc)
        assert m.score == 1.0


# -- evaluate() and assert_test() --------------------------------------------

class TestEvaluate:
    def test_batch_evaluation(self):
        cases = [_make_case(name="case_1"), _make_case(name="case_2")]
        result = evaluate(cases, [AccuracyMetric()])
        assert result.total == 2
        assert result.passed == 2
        assert result.pass_rate == 1.0

    def test_mixed_results(self):
        good = _make_case(name="good")
        bad = _make_case(name="bad", actual_output="WRONG", confidence=0.99)
        result = evaluate([good, bad], [AccuracyMetric(threshold=0.9)])
        assert result.passed == 1
        assert result.failed == 1

    def test_metric_summaries(self):
        cases = [_make_case(name=f"case_{i}") for i in range(3)]
        result = evaluate(cases, [AccuracyMetric(), CompletenessMetric()])
        summaries = result.metric_summaries
        assert "accuracy" in summaries
        assert "completeness" in summaries


class TestAssertTest:
    def test_passing(self):
        tc = _make_case()
        assert_test(tc, [AccuracyMetric(threshold=0.5)])

    def test_failing(self):
        tc = _make_case(actual_output="WRONG")
        try:
            assert_test(tc, [AccuracyMetric(threshold=0.99)])
            assert False, "Should have raised"
        except AssertionError as e:
            assert "accuracy" in str(e)


# -- Dataset ------------------------------------------------------------------

class TestEvaluationDataset:
    def test_from_json(self):
        goldens = [
            {
                "input": "123 N Main St, Springfield, illinois, 62704",
                "expected_output": "123 North Main Street, Springfield, IL, 62704",
                "name": "test_1",
            }
        ]
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(goldens, f)
            f.flush()
            ds = EvaluationDataset.from_json(f.name)

        assert len(ds) == 1
        assert ds.goldens[0].input == goldens[0]["input"]

    def test_generate_test_cases(self):
        ds = EvaluationDataset(goldens=[
            Golden(
                input="123 N Main St, Springfield, illinois, 62704",
                expected_output="123 North Main Street, Springfield, IL, 62704",
            )
        ])
        corrector = AddressCorrector()
        cases = ds.generate_test_cases(corrector)
        assert len(cases) == 1
        assert cases[0].actual_output != ""
        assert cases[0].status == "corrected"
