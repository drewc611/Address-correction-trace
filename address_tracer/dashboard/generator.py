"""HTML dashboard generator — produces a self-contained findings dashboard from evaluation results."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

from ..evaluation.results import EvaluationResult


class DashboardGenerator:
    """Generates a self-contained HTML dashboard from evaluation results."""

    def generate(self, result: EvaluationResult, title: str = "Address Correction Evaluation") -> str:
        """Generate the full HTML dashboard as a string."""
        data_json = json.dumps(result.to_dict(), indent=2)
        return _TEMPLATE.replace("{{TITLE}}", title).replace("{{DATA_JSON}}", data_json)

    def write(
        self,
        result: EvaluationResult,
        output_path: str,
        title: str = "Address Correction Evaluation",
    ):
        """Generate and write the dashboard to a file."""
        html = self.generate(result, title=title)
        Path(output_path).write_text(html)
        return output_path


_TEMPLATE = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{{TITLE}}</title>
<style>
  :root {
    --bg: #0f172a; --surface: #1e293b; --surface2: #334155;
    --text: #e2e8f0; --text-muted: #94a3b8; --accent: #38bdf8;
    --green: #4ade80; --red: #f87171; --yellow: #fbbf24;
    --border: #475569; --radius: 8px;
  }
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    background: var(--bg); color: var(--text); padding: 24px; line-height: 1.6;
  }
  h1 { font-size: 1.8rem; margin-bottom: 4px; }
  h2 { font-size: 1.2rem; color: var(--accent); margin-bottom: 12px; }
  .header { margin-bottom: 24px; }
  .header .meta { color: var(--text-muted); font-size: 0.85rem; }

  /* Summary cards row */
  .cards { display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 16px; margin-bottom: 28px; }
  .card {
    background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius);
    padding: 20px; text-align: center;
  }
  .card .value { font-size: 2rem; font-weight: 700; }
  .card .label { font-size: 0.8rem; color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.05em; }
  .card.pass .value { color: var(--green); }
  .card.fail .value { color: var(--red); }
  .card.rate .value { color: var(--accent); }

  /* Metric summary bars */
  .metrics-section { margin-bottom: 28px; }
  .metric-bar-wrap { margin-bottom: 12px; }
  .metric-bar-label { display: flex; justify-content: space-between; font-size: 0.85rem; margin-bottom: 4px; }
  .metric-bar-bg {
    background: var(--surface2); border-radius: 4px; height: 22px; overflow: hidden; position: relative;
  }
  .metric-bar-fill {
    height: 100%; border-radius: 4px; transition: width 0.6s ease;
    display: flex; align-items: center; justify-content: flex-end; padding-right: 6px;
    font-size: 0.7rem; font-weight: 600; color: var(--bg);
  }

  /* Behavior insights */
  .insights { background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius); padding: 20px; margin-bottom: 28px; }
  .insight-item { padding: 8px 0; border-bottom: 1px solid var(--surface2); display: flex; align-items: flex-start; gap: 10px; }
  .insight-item:last-child { border-bottom: none; }
  .insight-icon { font-size: 1.1rem; flex-shrink: 0; margin-top: 2px; }
  .insight-text { font-size: 0.9rem; }
  .insight-text strong { color: var(--accent); }

  /* Results table */
  .table-wrap { overflow-x: auto; margin-bottom: 28px; }
  table { width: 100%; border-collapse: collapse; font-size: 0.85rem; }
  th { background: var(--surface); color: var(--accent); text-align: left; padding: 10px 12px; border-bottom: 2px solid var(--border); white-space: nowrap; }
  td { padding: 10px 12px; border-bottom: 1px solid var(--surface2); vertical-align: top; }
  tr:hover td { background: var(--surface); }
  .badge {
    display: inline-block; padding: 2px 8px; border-radius: 12px; font-size: 0.75rem; font-weight: 600;
  }
  .badge-pass { background: #065f46; color: var(--green); }
  .badge-fail { background: #7f1d1d; color: var(--red); }
  .score-cell { font-weight: 600; }
  .corrections-list { list-style: none; font-size: 0.8rem; }
  .corrections-list li { padding: 2px 0; }
  .corrections-list .rule { color: var(--text-muted); }

  /* Detail expandable */
  details { margin-bottom: 6px; }
  details summary { cursor: pointer; color: var(--accent); font-size: 0.85rem; }
  details .detail-content { padding: 8px 12px; background: var(--surface); border-radius: var(--radius); margin-top: 4px; font-size: 0.82rem; }
  .reason { color: var(--text-muted); font-style: italic; font-size: 0.8rem; }
</style>
</head>
<body>

<div class="header">
  <h1>{{TITLE}}</h1>
  <div class="meta" id="meta"></div>
</div>

<div class="cards" id="cards"></div>

<div class="metrics-section">
  <h2>Metric Scores</h2>
  <div id="metric-bars"></div>
</div>

<div class="insights">
  <h2>AI Behavior Insights</h2>
  <div id="insights"></div>
</div>

<h2>Test Results</h2>
<div class="table-wrap">
  <table>
    <thead><tr>
      <th>Name</th><th>Status</th><th>Input</th><th>Output</th><th>Expected</th><th>Corrections</th><th>Metrics</th>
    </tr></thead>
    <tbody id="results-body"></tbody>
  </table>
</div>

<script>
const DATA = {{DATA_JSON}};

// Meta
document.getElementById('meta').innerHTML =
  `Run: ${DATA.identifier || 'unnamed'} &middot; ${new Date(DATA.timestamp).toLocaleString()} &middot; ${DATA.summary.total} test cases`;

// Summary cards
const cards = document.getElementById('cards');
function addCard(label, value, cls) {
  cards.innerHTML += `<div class="card ${cls}"><div class="value">${value}</div><div class="label">${label}</div></div>`;
}
addCard('Total', DATA.summary.total, '');
addCard('Passed', DATA.summary.passed, 'pass');
addCard('Failed', DATA.summary.failed, 'fail');
addCard('Pass Rate', (DATA.summary.pass_rate * 100).toFixed(1) + '%', 'rate');

// Metric bars
const barsEl = document.getElementById('metric-bars');
for (const [name, stats] of Object.entries(DATA.metric_summaries)) {
  const pct = (stats.mean * 100).toFixed(1);
  const color = stats.mean >= 0.8 ? 'var(--green)' : stats.mean >= 0.5 ? 'var(--yellow)' : 'var(--red)';
  barsEl.innerHTML += `
    <div class="metric-bar-wrap">
      <div class="metric-bar-label"><span>${name}</span><span>mean ${pct}% &middot; pass rate ${(stats.pass_rate*100).toFixed(0)}%</span></div>
      <div class="metric-bar-bg"><div class="metric-bar-fill" style="width:${pct}%;background:${color}">${pct}%</div></div>
    </div>`;
}

// Behavior insights
const insightsEl = document.getElementById('insights');
function addInsight(icon, html) { insightsEl.innerHTML += `<div class="insight-item"><span class="insight-icon">${icon}</span><div class="insight-text">${html}</div></div>`; }

const ms = DATA.metric_summaries;
if (ms.over_correction && ms.over_correction.mean < 0.9) {
  addInsight('&#x26A0;', `<strong>Over-correction detected.</strong> The corrector is making unnecessary changes (mean score: ${(ms.over_correction.mean*100).toFixed(1)}%). Review spurious corrections in failed cases.`);
}
if (ms.under_correction && ms.under_correction.mean < 0.9) {
  addInsight('&#x26A0;', `<strong>Under-correction detected.</strong> The corrector is missing expected fixes (mean score: ${(ms.under_correction.mean*100).toFixed(1)}%). Check the completeness metric for missed fields.`);
}
if (ms.confidence_calibration && ms.confidence_calibration.mean < 0.7) {
  addInsight('&#x26A0;', `<strong>Confidence miscalibration.</strong> Reported confidence does not match actual accuracy (mean: ${(ms.confidence_calibration.mean*100).toFixed(1)}%). The system may be overconfident on wrong answers.`);
}
if (ms.accuracy) {
  const lvl = ms.accuracy.mean >= 0.9 ? 'high' : ms.accuracy.mean >= 0.7 ? 'moderate' : 'low';
  addInsight('&#x1F4CA;', `<strong>Overall accuracy is ${lvl}</strong> (${(ms.accuracy.mean*100).toFixed(1)}%). ${ms.accuracy.mean >= 0.9 ? 'Corrections closely match golden expectations.' : 'Review failing cases for systematic issues.'}`);
}
if (ms.field_accuracy) {
  addInsight('&#x1F50D;', `<strong>Field-level accuracy:</strong> mean ${(ms.field_accuracy.mean*100).toFixed(1)}%. ${ms.field_accuracy.mean < 0.8 ? 'Some field types are consistently miscorrected.' : 'Individual fields are generally correct.'}`);
}
if (insightsEl.innerHTML === '') {
  addInsight('&#x2705;', 'No significant behavioral issues detected. All metrics are within acceptable ranges.');
}

// Results table
const tbody = document.getElementById('results-body');
for (const r of DATA.test_results) {
  const badge = r.success ? '<span class="badge badge-pass">PASS</span>' : '<span class="badge badge-fail">FAIL</span>';
  const corrections = r.actual_corrections.map(c =>
    `<li><strong>${c.field}:</strong> ${c.original} &rarr; ${c.corrected} <span class="rule">(${c.rule})</span></li>`
  ).join('') || '<li>None</li>';
  const metrics = r.metrics.map(m => {
    const cls = m.success ? 'badge-pass' : 'badge-fail';
    return `<details><summary><span class="badge ${cls}">${m.metric}: ${(m.score*100).toFixed(0)}%</span></summary><div class="detail-content"><div class="reason">${m.reason}</div></div></details>`;
  }).join('');

  tbody.innerHTML += `<tr>
    <td>${r.name}</td>
    <td>${badge}</td>
    <td style="max-width:200px;word-break:break-word">${r.input}</td>
    <td style="max-width:200px;word-break:break-word">${r.actual_output}</td>
    <td style="max-width:200px;word-break:break-word">${r.expected_output || '—'}</td>
    <td><ul class="corrections-list">${corrections}</ul></td>
    <td>${metrics}</td>
  </tr>`;
}
</script>
</body>
</html>"""
