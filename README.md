# Address Correction Trace

A service-like Python tool that validates, corrects, and traces changes made to mailing addresses. Includes a deepeval-style evaluation framework with AI behavior analysis metrics and an HTML findings dashboard.

## Features

- **Address Correction** — Parses and corrects addresses: state abbreviation, ZIP formatting, directional expansion, suffix standardization, case normalization
- **Trace Artifacts** — Structured JSON artifacts documenting every correction with before/after values and rule references
- **Evaluation Framework** — deepeval-style test cases, metrics, `evaluate()`, and `assert_test()` for scoring corrector behavior
- **AI Behavior Metrics** — Accuracy, completeness, over-correction, under-correction, confidence calibration, field-level accuracy
- **Findings Dashboard** — Self-contained HTML dashboard with charts, behavioral insights, and per-test detail
- **Service Layer** — Programmatic API + HTTP server for integration

## Installation

```bash
pip install -r requirements.txt
```

## Usage

### CLI — Correct Addresses

```bash
# Single address
python -m address_tracer correct "123 N Main St, Springfield, illinois, 62704"

# Batch file (one address per line)
python -m address_tracer batch addresses.txt -o results/

# JSON trace artifact
python -m address_tracer correct "456 Oak Ave, NY, NY 10001" --format json
```

### CLI — Evaluate Against Golden Dataset

```bash
# Run evaluation and print results
python -m address_tracer evaluate examples/golden_dataset.json

# Generate HTML findings dashboard
python -m address_tracer dashboard examples/golden_dataset.json -o report.html

# Start as HTTP service
python -m address_tracer serve --port 8080
```

### Python API — Correction

```python
from address_tracer.corrector import AddressCorrector

corrector = AddressCorrector()
result = corrector.correct("123 N Main St, Springfield, illinois, 62704")
print(result.corrected_address)
print(result.trace.to_json())
```

### Python API — Evaluation (deepeval-style)

```python
from address_tracer.evaluation import (
    AddressTestCase, AccuracyMetric, CompletenessMetric,
    OverCorrectionMetric, evaluate, assert_test,
    EvaluationDataset,
)
from address_tracer.corrector import AddressCorrector

# Load golden dataset and generate test cases
dataset = EvaluationDataset.from_json("examples/golden_dataset.json")
dataset.generate_test_cases(AddressCorrector())

# Evaluate with metrics
result = evaluate(dataset, metrics=[
    AccuracyMetric(threshold=0.8),
    CompletenessMetric(threshold=0.8),
    OverCorrectionMetric(threshold=0.8),
])
print(f"Pass rate: {result.pass_rate:.1%}")

# Or use assert_test() in pytest
def test_address():
    tc = AddressTestCase(
        input="123 N Main St, Springfield, illinois, 62704",
        actual_output="123 North Main Street, Springfield, IL, 62704",
        expected_output="123 North Main Street, Springfield, IL, 62704",
    )
    assert_test(tc, [AccuracyMetric(threshold=0.9)])
```

### Python API — Service

```python
from address_tracer.service import AddressTracerService

svc = AddressTracerService()

# Correct
trace = svc.correct("123 N Main St, Springfield, illinois, 62704")

# Evaluate + dashboard in one call
summary = svc.run_full_pipeline("examples/golden_dataset.json", "dashboard.html")
```

### HTTP API

```bash
# Start server
python -m address_tracer serve --port 8080

# Correct an address
curl -X POST http://localhost:8080/correct \
  -H "Content-Type: application/json" \
  -d '{"address": "123 N Main St, Springfield, illinois, 62704"}'

# Evaluate against golden records
curl -X POST http://localhost:8080/evaluate \
  -H "Content-Type: application/json" \
  -d '{"goldens": [{"input": "...", "expected_output": "..."}]}'
```

## Evaluation Metrics

| Metric | What It Detects |
|--------|----------------|
| **AccuracyMetric** | Whether corrected output matches expected — detects wrong corrections, data loss |
| **CompletenessMetric** | Whether all expected corrections were applied — detects missed fixes |
| **OverCorrectionMetric** | Corrections applied unnecessarily — detects hallucinated/spurious changes |
| **UnderCorrectionMetric** | Expected corrections that were skipped — detects silent failures |
| **ConfidenceCalibrationMetric** | Whether confidence scores align with actual correctness — detects overconfidence |
| **FieldLevelAccuracyMetric** | Per-field correctness — reveals systematic weaknesses in specific fields |

## Project Structure

```
address_tracer/
  __init__.py
  corrector.py          # Core correction engine
  parser.py             # Address parsing logic
  trace.py              # Trace artifact model
  rules.py              # Correction rules and reference data
  cli.py                # CLI entry point
  service.py            # Service layer (orchestrator)
  server.py             # HTTP server
  evaluation/
    __init__.py
    test_case.py        # AddressTestCase (deepeval-style)
    metrics.py          # BaseMetric + 6 evaluation metrics
    evaluate.py         # evaluate() and assert_test()
    results.py          # MetricResult, TestResult, EvaluationResult
    dataset.py          # EvaluationDataset, Golden
  dashboard/
    __init__.py
    generator.py        # HTML dashboard generator
examples/
  sample_addresses.txt  # Sample batch input
  golden_dataset.json   # Golden evaluation dataset
tests/
  test_corrector.py
  test_parser.py
  test_trace.py
  test_evaluation.py
  test_service.py
```

## License

MIT
