"""Edge-case and boundary tests for parser, corrector, and evaluation."""

import math

from address_tracer.parser import parse_address
from address_tracer.corrector import AddressCorrector
from address_tracer.evaluation import (
    EvaluationResult,
    evaluate,
    AddressTestCase,
    AccuracyMetric,
)


class TestParserEdgeCases:
    def test_whitespace_only(self):
        result = parse_address("   ")
        assert len(result.parse_errors) > 0

    def test_no_commas(self):
        result = parse_address("123 Main St Springfield IL 62704")
        assert len(result.parse_errors) > 0

    def test_suffix_like_street_name(self):
        """Street names that contain tokens matching suffix abbreviations.
        'Dr' is a suffix key — ensure it's not greedily consumed mid-name."""
        result = parse_address("100 Dr Martin Luther King Blvd, Atlanta, GA, 30303")
        assert "Martin Luther King" in result.street_name or "Dr Martin Luther King" in result.street_name
        assert result.street_suffix == "Blvd"

    def test_no_suffix(self):
        result = parse_address("100 Main, Springfield, IL, 62704")
        assert result.street_name == "Main"
        assert result.street_suffix == ""

    def test_multi_word_street_name(self):
        result = parse_address("500 Martin Luther King Blvd, Memphis, TN, 38103")
        assert "Martin Luther King" in result.street_name
        assert result.street_suffix == "Blvd"

    def test_only_street_number(self):
        result = parse_address("100, City, ST, 12345")
        assert result.street_number == "100"
        assert result.city == "City"

    def test_extra_commas(self):
        result = parse_address("123 Main St, Springfield, IL, 62704,")
        assert result.street_number == "123"

    def test_long_zip_code(self):
        result = parse_address("123 Main St, Springfield, IL, 627041234")
        assert result.zip_code == "627041234"


class TestCorrectorEdgeCases:
    def setup_method(self):
        self.corrector = AddressCorrector()

    def test_idempotent(self):
        """Correcting an already-correct address should not change it."""
        addr = "123 North Main Street, Springfield, IL, 62704"
        result = self.corrector.correct(addr)
        assert result.corrected_address == addr
        assert result.trace.status == "unchanged"
        assert len(result.trace.corrections) == 0

    def test_double_correction_idempotent(self):
        """Correcting twice should produce the same result."""
        result1 = self.corrector.correct("123 N Main St, springfield, illinois, 62704")
        result2 = self.corrector.correct(result1.corrected_address)
        assert result2.corrected_address == result1.corrected_address
        assert result2.trace.status == "unchanged"

    def test_nine_digit_zip(self):
        result = self.corrector.correct("123 Main St, Boston, MA, 021013456")
        assert "02101-3456" in result.corrected_address

    def test_confidence_is_deterministic(self):
        """Rule-based corrections should always have full confidence."""
        result = self.corrector.correct("123 N Main St, springfield, illinois, 62704")
        assert result.trace.confidence == 1.0

    def test_state_not_found(self):
        """Unknown state should be left as-is."""
        result = self.corrector.correct("123 Main St, City, XQ, 12345")
        assert "XQ" in result.corrected_address

    def test_missing_zip(self):
        result = self.corrector.correct("123 Main St, Springfield, IL")
        assert result.trace.status in ("corrected", "unchanged")
        assert "Springfield" in result.corrected_address

    def test_empty_string_returns_error(self):
        result = self.corrector.correct("")
        assert result.trace.status == "error"
        assert result.trace.confidence == 0.0

    def test_single_field_address(self):
        result = self.corrector.correct("garbage")
        assert result.trace.status == "error"


class TestEvaluationEdgeCases:
    def test_empty_dataset_pass_rate_is_nan(self):
        result = EvaluationResult()
        assert math.isnan(result.pass_rate)

    def test_evaluate_empty_list(self):
        result = evaluate([], [AccuracyMetric()])
        assert result.total == 0
        assert math.isnan(result.pass_rate)

    def test_metric_without_expected_output(self):
        """Metrics should degrade gracefully when golden data is missing."""
        tc = AddressTestCase(
            input="123 N Main St, Springfield, IL, 62704",
            actual_output="123 North Main Street, Springfield, IL, 62704",
            expected_output=None,
        )
        m = AccuracyMetric()
        m.measure(tc)
        assert m.score == 1.0  # no expected output, assumes ok if no error
