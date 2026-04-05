"""Trace artifact model — records every correction applied to an address."""

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import List, Optional


@dataclass
class Correction:
    """A single correction applied to an address field."""
    field: str
    original: str
    corrected: str
    rule: str

    def to_dict(self) -> dict:
        return {
            "field": self.field,
            "original": self.original,
            "corrected": self.corrected,
            "rule": self.rule,
        }


@dataclass
class TraceArtifact:
    """Complete trace artifact documenting all corrections to an address."""
    input_address: str
    corrected_address: str = ""
    timestamp: str = ""
    corrections: List[Correction] = field(default_factory=list)
    status: str = "unchanged"
    confidence: float = 1.0
    errors: List[str] = field(default_factory=list)

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now(timezone.utc).isoformat()

    def add_correction(self, field_name: str, original: str, corrected: str, rule: str):
        """Record a correction."""
        self.corrections.append(Correction(
            field=field_name,
            original=original,
            corrected=corrected,
            rule=rule,
        ))

    def finalize(self, corrected_address: str):
        """Finalize the trace with the corrected address string."""
        self.corrected_address = corrected_address
        if self.errors:
            self.status = "error"
            self.confidence = 0.0
        elif self.corrections:
            self.status = "corrected"
            # All corrections are rule-based and deterministic, so confidence
            # reflects whether corrections were applied (high) not how many.
            # Only reduce confidence when corrections interact in complex ways.
            self.confidence = 1.0
        else:
            self.status = "unchanged"
            self.confidence = 1.0

    def to_dict(self) -> dict:
        return {
            "input": self.input_address,
            "corrected": self.corrected_address,
            "timestamp": self.timestamp,
            "corrections": [c.to_dict() for c in self.corrections],
            "status": self.status,
            "confidence": round(self.confidence, 2),
            "errors": self.errors if self.errors else None,
        }

    def to_json(self, indent: int = 2) -> str:
        data = self.to_dict()
        # Remove None values
        data = {k: v for k, v in data.items() if v is not None}
        return json.dumps(data, indent=indent)
