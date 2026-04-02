"""Tests for address parser."""

from address_tracer.parser import parse_address


class TestParseAddress:
    def test_basic_address(self):
        result = parse_address("123 N Main St, Springfield, IL, 62704")
        assert result.street_number == "123"
        assert result.street_direction == "N"
        assert result.street_name == "Main"
        assert result.street_suffix == "St"
        assert result.city == "Springfield"
        assert result.state == "IL"
        assert result.zip_code == "62704"

    def test_address_with_secondary_unit(self):
        result = parse_address("456 Oak Ave Apt 2, New York, NY, 10001")
        assert result.street_number == "456"
        assert result.street_name == "Oak"
        assert result.street_suffix == "Ave"
        assert result.secondary_designator == "Apt"
        assert result.secondary_value == "2"

    def test_no_directional(self):
        result = parse_address("789 Elm Blvd, Portland, OR, 97201")
        assert result.street_direction == ""
        assert result.street_name == "Elm"
        assert result.street_suffix == "Blvd"

    def test_empty_address(self):
        result = parse_address("")
        assert len(result.parse_errors) > 0

    def test_minimal_address(self):
        result = parse_address("100 Main St, Boston")
        assert result.street_number == "100"
        assert result.city == "Boston"
        assert result.state == ""

    def test_to_string_roundtrip(self):
        result = parse_address("123 N Main St, Springfield, IL, 62704")
        output = result.to_string()
        assert "123" in output
        assert "Springfield" in output
        assert "IL" in output
        assert "62704" in output
