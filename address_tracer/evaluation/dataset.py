"""Evaluation datasets and golden test sets for address correction evaluation."""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

from .test_case import AddressTestCase


@dataclass
class Golden:
    """A single golden record — the ground truth for one address."""
    input: str
    expected_output: str
    expected_corrections: Optional[List[Dict[str, str]]] = None
    tags: List[str] = field(default_factory=list)
    name: str = ""

    def to_dict(self) -> dict:
        return {
            "input": self.input,
            "expected_output": self.expected_output,
            "expected_corrections": self.expected_corrections,
            "tags": self.tags,
            "name": self.name,
        }


class EvaluationDataset:
    """A dataset of golden records that can generate AddressTestCases via a corrector."""

    def __init__(self, goldens: Optional[List[Golden]] = None):
        self.goldens: List[Golden] = goldens or []
        self.test_cases: List[AddressTestCase] = []

    def add_golden(self, golden: Golden):
        self.goldens.append(golden)

    def generate_test_cases(self, corrector) -> List[AddressTestCase]:
        """Run the corrector on each golden input and build test cases with results."""
        self.test_cases = []
        for i, g in enumerate(self.goldens):
            start = time.perf_counter()
            result = corrector.correct(g.input)
            elapsed = time.perf_counter() - start

            tc = AddressTestCase(
                input=g.input,
                actual_output=result.corrected_address,
                expected_output=g.expected_output,
                expected_corrections=g.expected_corrections,
                actual_corrections=[c.to_dict() for c in result.trace.corrections],
                confidence=result.trace.confidence,
                status=result.trace.status,
                completion_time=elapsed,
                name=g.name or f"golden_{i}",
                tags=g.tags,
            )
            self.test_cases.append(tc)

        return self.test_cases

    @classmethod
    def from_json(cls, path: str) -> "EvaluationDataset":
        """Load a dataset from a JSON file.

        Expected format:
        [
          {
            "input": "...",
            "expected_output": "...",
            "expected_corrections": [...],
            "tags": [...],
            "name": "..."
          }
        ]
        """
        data = json.loads(Path(path).read_text())
        goldens = []
        for item in data:
            goldens.append(Golden(
                input=item["input"],
                expected_output=item["expected_output"],
                expected_corrections=item.get("expected_corrections"),
                tags=item.get("tags", []),
                name=item.get("name", ""),
            ))
        return cls(goldens=goldens)

    def to_json(self, path: str):
        """Save the dataset to a JSON file."""
        data = [g.to_dict() for g in self.goldens]
        Path(path).write_text(json.dumps(data, indent=2))

    def __len__(self):
        return len(self.goldens)
