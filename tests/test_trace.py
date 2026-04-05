"""Tests for trace artifact model."""

import json

from address_tracer.trace import TraceArtifact, Correction


class TestTraceArtifact:
    def test_empty_trace(self):
        trace = TraceArtifact(input_address="123 Main St, City, ST, 12345")
        trace.finalize("123 Main St, City, ST, 12345")
        assert trace.status == "unchanged"
        assert trace.confidence == 1.0

    def test_add_correction(self):
        trace = TraceArtifact(input_address="test")
        trace.add_correction("state", "illinois", "IL", "state_abbreviation")
        assert len(trace.corrections) == 1
        assert trace.corrections[0].field == "state"

    def test_finalize_with_corrections(self):
        trace = TraceArtifact(input_address="test")
        trace.add_correction("state", "illinois", "IL", "state_abbreviation")
        trace.finalize("corrected")
        assert trace.status == "corrected"
        assert trace.confidence == 1.0

    def test_finalize_with_errors(self):
        trace = TraceArtifact(input_address="test")
        trace.errors.append("Parse error")
        trace.finalize("test")
        assert trace.status == "error"
        assert trace.confidence == 0.0

    def test_to_dict(self):
        trace = TraceArtifact(input_address="input")
        trace.add_correction("state", "illinois", "IL", "state_abbreviation")
        trace.finalize("corrected")
        d = trace.to_dict()
        assert d["input"] == "input"
        assert d["corrected"] == "corrected"
        assert d["status"] == "corrected"
        assert len(d["corrections"]) == 1

    def test_to_json(self):
        trace = TraceArtifact(input_address="input")
        trace.finalize("input")
        result = trace.to_json()
        parsed = json.loads(result)
        assert parsed["input"] == "input"
        assert "errors" not in parsed  # None values stripped

    def test_timestamp_auto_set(self):
        trace = TraceArtifact(input_address="test")
        assert trace.timestamp != ""

    def test_correction_to_dict(self):
        c = Correction(field="state", original="illinois", corrected="IL", rule="state_abbreviation")
        d = c.to_dict()
        assert d["field"] == "state"
        assert d["original"] == "illinois"
        assert d["corrected"] == "IL"
        assert d["rule"] == "state_abbreviation"
