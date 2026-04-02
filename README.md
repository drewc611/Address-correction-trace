# Address Correction Trace

A Python tool that validates, corrects, and traces changes made to mailing addresses. It produces a structured trace artifact documenting every correction applied, useful for auditing, debugging, and compliance.

## Features

- **Address Parsing** — Breaks raw address strings into structured components (street, city, state, ZIP)
- **Address Correction** — Applies common fixes: state abbreviation normalization, ZIP code formatting, directional expansion, suffix standardization
- **Trace Artifact Generation** — Produces a detailed JSON artifact recording each correction with before/after values and rule references
- **CLI Interface** — Process single addresses or batch files from the command line

## Installation

```bash
pip install -r requirements.txt
```

## Usage

### CLI

```bash
# Correct a single address
python -m address_tracer correct "123 N Main St, Springfield, illinois, 62704"

# Process a batch file (one address per line)
python -m address_tracer batch addresses.txt -o results/

# Output trace artifact only
python -m address_tracer correct "456 Oak Ave, NY, NY 10001" --format json
```

### Python API

```python
from address_tracer.corrector import AddressCorrector

corrector = AddressCorrector()
result = corrector.correct("123 N Main St, Springfield, illinois, 62704")

print(result.corrected_address)
print(result.trace.to_dict())
```

## Trace Artifact Format

Each correction produces a trace artifact with the following structure:

```json
{
  "input": "123 N Main St, Springfield, illinois, 62704",
  "corrected": "123 North Main Street, Springfield, IL, 62704",
  "timestamp": "2026-04-02T12:00:00Z",
  "corrections": [
    {
      "field": "state",
      "original": "illinois",
      "corrected": "IL",
      "rule": "state_abbreviation"
    },
    {
      "field": "street_direction",
      "original": "N",
      "corrected": "North",
      "rule": "directional_expansion"
    },
    {
      "field": "street_suffix",
      "original": "St",
      "corrected": "Street",
      "rule": "suffix_standardization"
    }
  ],
  "status": "corrected",
  "confidence": 0.95
}
```

## Project Structure

```
address_tracer/
  __init__.py
  corrector.py      # Core correction engine
  parser.py         # Address parsing logic
  trace.py          # Trace artifact model and generation
  rules.py          # Correction rules and reference data
  cli.py            # CLI entry point
tests/
  test_corrector.py
  test_parser.py
  test_trace.py
```

## License

MIT
