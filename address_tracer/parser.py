"""Address parsing logic — breaks raw address strings into structured components."""

import re
from dataclasses import dataclass, field
from typing import Optional

from .rules import STREET_SUFFIXES, DIRECTIONALS, UNIT_DESIGNATORS


@dataclass
class ParsedAddress:
    """Structured representation of a parsed address."""
    street_number: str = ""
    street_direction: str = ""
    street_name: str = ""
    street_suffix: str = ""
    secondary_designator: str = ""
    secondary_value: str = ""
    city: str = ""
    state: str = ""
    zip_code: str = ""
    raw: str = ""
    parse_errors: list = field(default_factory=list)

    def to_string(self) -> str:
        """Reassemble the address into a single formatted string."""
        street_parts = []
        if self.street_number:
            street_parts.append(self.street_number)
        if self.street_direction:
            street_parts.append(self.street_direction)
        if self.street_name:
            street_parts.append(self.street_name)
        if self.street_suffix:
            street_parts.append(self.street_suffix)

        street_line = " ".join(street_parts)

        if self.secondary_designator:
            street_line += f" {self.secondary_designator}"
            if self.secondary_value:
                street_line += f" {self.secondary_value}"

        parts = [street_line, self.city, self.state]
        result = ", ".join(p for p in parts if p)

        if self.zip_code:
            result += f", {self.zip_code}"

        return result


def parse_address(raw: str) -> ParsedAddress:
    """Parse a raw address string into structured components.

    Expects a format like:
        "123 N Main St, Springfield, IL, 62704"
        "456 Oak Ave Apt 2, New York, NY, 10001"
    """
    addr = ParsedAddress(raw=raw)

    if not raw or not raw.strip():
        addr.parse_errors.append("Empty address string")
        return addr

    # Split on commas to separate major components
    parts = [p.strip() for p in raw.split(",")]

    if len(parts) < 2:
        addr.parse_errors.append("Address must contain at least street and city separated by commas")
        return addr

    # Parse street line (first part)
    _parse_street_line(parts[0], addr)

    # Parse city (second part)
    addr.city = parts[1].strip() if len(parts) > 1 else ""

    # Parse state (third part)
    addr.state = parts[2].strip() if len(parts) > 2 else ""

    # Parse ZIP (fourth part)
    if len(parts) > 3:
        addr.zip_code = parts[3].strip()

    return addr


def _parse_street_line(street_line: str, addr: ParsedAddress) -> None:
    """Parse the street line into number, direction, name, and suffix."""
    tokens = street_line.split()
    if not tokens:
        addr.parse_errors.append("Empty street line")
        return

    idx = 0

    # Street number — first token if it starts with a digit
    if tokens[idx] and tokens[idx][0].isdigit():
        addr.street_number = tokens[idx]
        idx += 1

    if idx >= len(tokens):
        return

    # Pre-directional
    if tokens[idx].lower().rstrip(".") in {k.rstrip(".") for k in DIRECTIONALS}:
        addr.street_direction = tokens[idx]
        idx += 1

    if idx >= len(tokens):
        return

    # Collect street name tokens. Look ahead to identify the suffix — it must
    # be followed only by a secondary designator (or nothing), to avoid
    # greedily matching mid-name tokens like "Dr" in "Dr Martin Luther King Blvd".
    suffix_keys = {k.rstrip(".") for k in STREET_SUFFIXES}
    unit_keys = {k.rstrip(".") for k in UNIT_DESIGNATORS}
    name_tokens = []

    # First pass: find the suffix position (scan from the end).
    # Skip past secondary unit sections (e.g., "Apt 2", "Ste 300") then
    # look for the suffix token.
    suffix_idx = None
    j = len(tokens) - 1
    # Skip unit designator values (e.g., "2" in "Apt 2")
    while j >= idx:
        lower = tokens[j].lower().rstrip(".")
        if lower in unit_keys:
            j -= 1  # skip the designator itself
            break
        if lower in suffix_keys:
            suffix_idx = j
            break
        j -= 1  # skip unit value tokens
    else:
        # Reached idx without finding a unit designator — rescan for suffix only
        pass
    if suffix_idx is None:
        for j2 in range(len(tokens) - 1, idx - 1, -1):
            lower = tokens[j2].lower().rstrip(".")
            if lower in suffix_keys:
                # Only accept if everything after it is a unit section or nothing
                rest_ok = True
                k = j2 + 1
                if k < len(tokens) and tokens[k].lower().rstrip(".") in unit_keys:
                    rest_ok = True
                elif k >= len(tokens):
                    rest_ok = True
                else:
                    rest_ok = False
                if rest_ok:
                    suffix_idx = j2
                    break

    # Collect name tokens up to the suffix (or end)
    end = suffix_idx if suffix_idx is not None else len(tokens)
    while idx < end:
        lower = tokens[idx].lower().rstrip(".")
        if lower in unit_keys:
            break
        name_tokens.append(tokens[idx])
        idx += 1

    addr.street_name = " ".join(name_tokens)

    # Consume suffix
    if suffix_idx is not None and idx == suffix_idx:
        addr.street_suffix = tokens[idx]
        idx += 1

    # Secondary designator (e.g., Apt 2)
    if idx < len(tokens):
        lower = tokens[idx].lower().rstrip(".")
        if lower in {k.rstrip(".") for k in UNIT_DESIGNATORS}:
            addr.secondary_designator = tokens[idx]
            idx += 1
            if idx < len(tokens):
                addr.secondary_value = " ".join(tokens[idx:])
