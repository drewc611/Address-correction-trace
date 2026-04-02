"""Tests for the service layer and dashboard generation."""

import json
import os
import tempfile

from address_tracer.service import AddressTracerService


class TestAddressTracerService:
    def setup_method(self):
        self.svc = AddressTracerService()

    def test_correct_single(self):
        result = self.svc.correct("123 N Main St, Springfield, illinois, 62704")
        assert result["status"] == "corrected"
        assert len(result["corrections"]) >= 3

    def test_correct_batch(self):
        results = self.svc.correct_batch([
            "123 N Main St, Springfield, illinois, 62704",
            "456 Oak Ave, new york, NY, 10001",
        ])
        assert len(results) == 2
        assert all(r["status"] == "corrected" for r in results)

    def test_evaluate_goldens(self):
        goldens = [
            {
                "input": "123 N Main St, Springfield, illinois, 62704",
                "expected_output": "123 North Main Street, Springfield, IL, 62704",
                "expected_corrections": [
                    {"field": "state", "original": "illinois", "corrected": "IL"},
                    {"field": "street_direction", "original": "N", "corrected": "North"},
                    {"field": "street_suffix", "original": "St", "corrected": "Street"},
                ],
            }
        ]
        result = self.svc.evaluate_goldens(goldens, identifier="test_run")
        assert result.total == 1
        assert result.identifier == "test_run"

    def test_evaluate_dataset_file(self):
        goldens = [{
            "input": "100 Main St, Boston, MA, 2101",
            "expected_output": "100 Main Street, Boston, MA, 02101",
        }]
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(goldens, f)
            path = f.name

        result = self.svc.evaluate_dataset(path)
        assert result.total == 1
        os.unlink(path)

    def test_generate_dashboard(self):
        goldens = [{
            "input": "123 N Main St, Springfield, illinois, 62704",
            "expected_output": "123 North Main Street, Springfield, IL, 62704",
        }]
        eval_result = self.svc.evaluate_goldens(goldens)
        with tempfile.NamedTemporaryFile(suffix=".html", delete=False) as f:
            path = f.name

        self.svc.generate_dashboard(eval_result, path)
        content = open(path).read()
        assert "<!DOCTYPE html>" in content
        assert "accuracy" in content
        os.unlink(path)

    def test_full_pipeline(self):
        goldens = [{
            "input": "456 Oak Ave, new york, NY, 10001",
            "expected_output": "456 Oak Avenue, New York, NY, 10001",
        }]
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as ds_f:
            json.dump(goldens, ds_f)
            ds_path = ds_f.name

        with tempfile.NamedTemporaryFile(suffix=".html", delete=False) as dash_f:
            dash_path = dash_f.name

        result = self.svc.run_full_pipeline(ds_path, dash_path)
        assert result["summary"]["total"] == 1
        assert os.path.isfile(dash_path)

        os.unlink(ds_path)
        os.unlink(dash_path)
