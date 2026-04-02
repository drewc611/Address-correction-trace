"""Test case definitions modeled after deepeval's LLMTestCase pattern."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class AddressTestCase:
    """A single evaluation test case for address correction.

    Mirrors deepeval's LLMTestCase: provides input, actual_output (from the
    corrector), and expected_output (the golden truth) so metrics can score
    the corrector's behavior.
    """

    # Required
    input: str
    actual_output: str

    # Optional — provide for supervised evaluation
    expected_output: Optional[str] = None
    expected_corrections: Optional[List[Dict[str, str]]] = None

    # Metadata produced by the corrector
    actual_corrections: List[Dict[str, str]] = field(default_factory=list)
    confidence: float = 0.0
    status: str = ""
    completion_time: float = 0.0

    # Bookkeeping
    name: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    comments: str = ""
    metadata: Dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "input": self.input,
            "actual_output": self.actual_output,
            "expected_output": self.expected_output,
            "actual_corrections": self.actual_corrections,
            "expected_corrections": self.expected_corrections,
            "confidence": self.confidence,
            "status": self.status,
            "completion_time": self.completion_time,
            "tags": self.tags,
            "comments": self.comments,
            "metadata": self.metadata,
        }
