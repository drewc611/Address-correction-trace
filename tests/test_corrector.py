"""Tests for address corrector."""

from address_tracer.corrector import AddressCorrector


class TestAddressCorrector:
    def setup_method(self):
        self.corrector = AddressCorrector()

    def test_state_abbreviation(self):
        result = self.corrector.correct("123 N Main St, Springfield, illinois, 62704")
        assert "IL" in result.corrected_address
        rules = [c.rule for c in result.trace.corrections]
        assert "state_abbreviation" in rules

    def test_directional_expansion(self):
        result = self.corrector.correct("123 N Main St, Springfield, IL, 62704")
        assert "North" in result.corrected_address
        rules = [c.rule for c in result.trace.corrections]
        assert "directional_expansion" in rules

    def test_suffix_standardization(self):
        result = self.corrector.correct("123 Main St, Springfield, IL, 62704")
        assert "Street" in result.corrected_address
        rules = [c.rule for c in result.trace.corrections]
        assert "suffix_standardization" in rules

    def test_zip_padding(self):
        result = self.corrector.correct("123 Main St, Boston, MA, 2101")
        assert "02101" in result.corrected_address

    def test_city_case_normalization(self):
        result = self.corrector.correct("123 Main St, new york, NY, 10001")
        assert "New York" in result.corrected_address

    def test_no_corrections_needed(self):
        result = self.corrector.correct("123 North Main Street, Springfield, IL, 62704")
        assert result.trace.status == "unchanged"
        assert result.trace.confidence == 1.0
        assert len(result.trace.corrections) == 0

    def test_multiple_corrections(self):
        result = self.corrector.correct("123 N Main St, springfield, illinois, 62704")
        assert result.trace.status == "corrected"
        assert len(result.trace.corrections) >= 3

    def test_parse_error_handling(self):
        result = self.corrector.correct("")
        assert result.trace.status == "error"
        assert result.trace.confidence == 0.0

    def test_batch_correction(self):
        addresses = [
            "123 N Main St, Springfield, illinois, 62704",
            "456 Oak Ave, new york, NY, 10001",
        ]
        results = self.corrector.correct_batch(addresses)
        assert len(results) == 2
        assert all(r.trace.status == "corrected" for r in results)

    def test_unit_designator_standardization(self):
        result = self.corrector.correct("456 Oak Ave Apt 2, New York, NY, 10001")
        assert "Apartment" in result.corrected_address

    def test_state_case_normalization(self):
        result = self.corrector.correct("123 Main St, Springfield, il, 62704")
        assert "IL" in result.corrected_address
