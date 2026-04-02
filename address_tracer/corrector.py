"""Core address correction engine — applies rules and generates trace artifacts."""

import re

from .parser import parse_address, ParsedAddress
from .trace import TraceArtifact
from .rules import (
    STATE_ABBREVIATIONS,
    VALID_STATE_ABBREVS,
    STREET_SUFFIXES,
    DIRECTIONALS,
    UNIT_DESIGNATORS,
)


class CorrectionResult:
    """Holds the corrected address and its trace artifact."""

    def __init__(self, corrected_address: str, trace: TraceArtifact):
        self.corrected_address = corrected_address
        self.trace = trace

    def __repr__(self):
        return f"CorrectionResult(address={self.corrected_address!r}, corrections={len(self.trace.corrections)})"


class AddressCorrector:
    """Validates and corrects mailing addresses, producing a trace artifact."""

    def correct(self, raw_address: str) -> CorrectionResult:
        """Correct an address and return the result with a full trace artifact."""
        trace = TraceArtifact(input_address=raw_address)
        parsed = parse_address(raw_address)

        if parsed.parse_errors:
            trace.errors.extend(parsed.parse_errors)
            trace.finalize(raw_address)
            return CorrectionResult(raw_address, trace)

        self._correct_state(parsed, trace)
        self._correct_zip(parsed, trace)
        self._correct_directional(parsed, trace)
        self._correct_suffix(parsed, trace)
        self._correct_unit_designator(parsed, trace)
        self._correct_city_case(parsed, trace)
        self._correct_street_name_case(parsed, trace)

        corrected = parsed.to_string()
        trace.finalize(corrected)
        return CorrectionResult(corrected, trace)

    def correct_batch(self, addresses: list[str]) -> list[CorrectionResult]:
        """Correct multiple addresses."""
        return [self.correct(addr) for addr in addresses]

    def _correct_state(self, parsed: ParsedAddress, trace: TraceArtifact):
        """Normalize state to two-letter abbreviation."""
        state = parsed.state
        if not state:
            return

        state_lower = state.lower().strip()

        # Already a valid abbreviation
        if state.upper() in VALID_STATE_ABBREVS:
            if state != state.upper():
                trace.add_correction("state", state, state.upper(), "state_case_normalization")
                parsed.state = state.upper()
            return

        # Full name -> abbreviation
        if state_lower in STATE_ABBREVIATIONS:
            abbrev = STATE_ABBREVIATIONS[state_lower]
            trace.add_correction("state", state, abbrev, "state_abbreviation")
            parsed.state = abbrev

    def _correct_zip(self, parsed: ParsedAddress, trace: TraceArtifact):
        """Normalize ZIP code formatting."""
        zip_code = parsed.zip_code
        if not zip_code:
            return

        # Remove non-digit/hyphen characters
        cleaned = re.sub(r"[^\d-]", "", zip_code)

        # Pad short ZIP codes with leading zeros
        digits_only = cleaned.replace("-", "")
        if digits_only.isdigit():
            if len(digits_only) < 5:
                cleaned = digits_only.zfill(5)
            elif len(digits_only) == 9:
                cleaned = f"{digits_only[:5]}-{digits_only[5:]}"

        if cleaned != zip_code:
            trace.add_correction("zip_code", zip_code, cleaned, "zip_format_normalization")
            parsed.zip_code = cleaned

    def _correct_directional(self, parsed: ParsedAddress, trace: TraceArtifact):
        """Expand abbreviated directionals (N -> North)."""
        direction = parsed.street_direction
        if not direction:
            return

        key = direction.lower().rstrip(".")
        lookup = {k.rstrip("."): v for k, v in DIRECTIONALS.items()}
        if key in lookup:
            expanded = lookup[key]
            if direction != expanded:
                trace.add_correction("street_direction", direction, expanded, "directional_expansion")
                parsed.street_direction = expanded

    def _correct_suffix(self, parsed: ParsedAddress, trace: TraceArtifact):
        """Standardize street suffix (St -> Street)."""
        suffix = parsed.street_suffix
        if not suffix:
            return

        key = suffix.lower().rstrip(".")
        lookup = {k.rstrip("."): v for k, v in STREET_SUFFIXES.items()}
        if key in lookup:
            standard = lookup[key]
            if suffix != standard:
                trace.add_correction("street_suffix", suffix, standard, "suffix_standardization")
                parsed.street_suffix = standard

    def _correct_unit_designator(self, parsed: ParsedAddress, trace: TraceArtifact):
        """Standardize secondary unit designator (Apt -> Apartment)."""
        designator = parsed.secondary_designator
        if not designator:
            return

        key = designator.lower().rstrip(".")
        lookup = {k.rstrip("."): v for k, v in UNIT_DESIGNATORS.items()}
        if key in lookup:
            standard = lookup[key]
            if designator != standard:
                trace.add_correction("secondary_designator", designator, standard, "unit_designator_standardization")
                parsed.secondary_designator = standard

    def _correct_city_case(self, parsed: ParsedAddress, trace: TraceArtifact):
        """Title-case the city name."""
        city = parsed.city
        if not city:
            return

        title_cased = city.title()
        if title_cased != city:
            trace.add_correction("city", city, title_cased, "city_case_normalization")
            parsed.city = title_cased

    def _correct_street_name_case(self, parsed: ParsedAddress, trace: TraceArtifact):
        """Title-case the street name."""
        name = parsed.street_name
        if not name:
            return

        title_cased = name.title()
        if title_cased != name:
            trace.add_correction("street_name", name, title_cased, "street_name_case_normalization")
            parsed.street_name = title_cased
