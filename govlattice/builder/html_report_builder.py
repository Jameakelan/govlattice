"""Render policy evaluation results as self-contained HTML reports."""

from enum import Enum
from html import escape
import json
from pathlib import Path
from typing import Any
from typing import Mapping
from typing import Union

from govlattice.model.evaluation_result import PolicyEvaluationResult
from govlattice.model.evaluation_result import RequirementFinding
from govlattice.utils.helper.file_helper import write_text_atomically


PathInput = Union[str, Path]


class HtmlReportBuilder:
    """Build and atomically write an evaluation report without dependencies."""

    __slots__ = ("_result",)

    def __init__(self, result: PolicyEvaluationResult) -> None:
        if not isinstance(result, PolicyEvaluationResult):
            raise TypeError(
                "result must be a PolicyEvaluationResult"
            )
        self._result = result

    def build(self) -> str:
        """Return a complete, escaped, self-contained HTML document."""
        result = self._result
        actor = result.execution.actor
        actor_name = (
            actor.display_name or actor.subject_id
            if actor is not None
            else "Not provided"
        )
        rows = "".join(
            self._finding_row(finding)
            for finding in result.findings
        )
        if not rows:
            rows = (
                '<tr><td colspan="7" class="empty">'
                "No requirement findings were produced.</td></tr>"
            )

        return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{escape(result.policy_id)} · GovLattice Report</title>
  <style>
    :root {{
      color-scheme: light;
      --bg: #f4f7fb;
      --surface: #ffffff;
      --text: #172033;
      --muted: #64748b;
      --border: #dbe3ef;
      --passed: #15803d;
      --failed: #b91c1c;
      --error: #b45309;
      --skipped: #475569;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      background: var(--bg);
      color: var(--text);
      font: 14px/1.5 Inter, ui-sans-serif, system-ui, sans-serif;
    }}
    main {{ width: min(1200px, calc(100% - 32px)); margin: 32px auto; }}
    header, section {{
      background: var(--surface);
      border: 1px solid var(--border);
      border-radius: 14px;
      box-shadow: 0 8px 24px rgb(15 23 42 / 6%);
    }}
    header {{ padding: 28px; }}
    h1 {{ margin: 0 0 4px; font-size: 28px; }}
    h2 {{ margin: 0 0 18px; font-size: 18px; }}
    .subtitle {{ color: var(--muted); }}
    .status {{
      display: inline-block;
      margin-top: 18px;
      padding: 6px 12px;
      border-radius: 999px;
      color: white;
      font-weight: 700;
      text-transform: uppercase;
    }}
    .passed {{ background: var(--passed); }}
    .failed {{ background: var(--failed); }}
    .error {{ background: var(--error); }}
    .skipped {{ background: var(--skipped); }}
    .cards {{
      display: grid;
      grid-template-columns: repeat(4, minmax(120px, 1fr));
      gap: 12px;
      margin: 18px 0;
    }}
    .card {{
      background: var(--surface);
      border: 1px solid var(--border);
      border-radius: 12px;
      padding: 16px;
    }}
    .card span {{ color: var(--muted); }}
    .card strong {{ display: block; margin-top: 4px; font-size: 24px; }}
    section {{ margin-top: 18px; padding: 22px; overflow: hidden; }}
    .metadata {{
      display: grid;
      grid-template-columns: repeat(3, minmax(160px, 1fr));
      gap: 14px;
    }}
    .metadata dt {{ color: var(--muted); }}
    .metadata dd {{ margin: 2px 0 0; font-weight: 600; }}
    .table-wrap {{ overflow-x: auto; }}
    table {{ width: 100%; border-collapse: collapse; }}
    th, td {{
      padding: 12px;
      border-bottom: 1px solid var(--border);
      text-align: left;
      vertical-align: top;
    }}
    th {{ color: var(--muted); font-size: 12px; text-transform: uppercase; }}
    td .status {{ margin: 0; padding: 3px 8px; font-size: 11px; }}
    details {{ min-width: 150px; }}
    summary {{ color: #2563eb; cursor: pointer; }}
    pre {{
      max-width: 360px;
      overflow: auto;
      padding: 10px;
      border-radius: 8px;
      background: #f8fafc;
      white-space: pre-wrap;
      word-break: break-word;
    }}
    .empty {{ padding: 28px; color: var(--muted); text-align: center; }}
    footer {{ margin: 18px 4px; color: var(--muted); text-align: right; }}
    @media (max-width: 760px) {{
      .cards {{ grid-template-columns: repeat(2, 1fr); }}
      .metadata {{ grid-template-columns: 1fr; }}
      main {{ width: min(100% - 20px, 1200px); margin: 10px auto; }}
    }}
    @media print {{
      body {{ background: white; }}
      main {{ width: 100%; margin: 0; }}
      header, section {{ box-shadow: none; break-inside: avoid; }}
    }}
  </style>
</head>
<body>
  <main>
    <header>
      <h1>{escape(result.policy_id)}</h1>
      <div class="subtitle">State: {escape(result.state_id)}</div>
      <span class="status {escape(result.status.value)}">
        {escape(result.status.value)}
      </span>
    </header>

    <div class="cards" aria-label="Finding summary">
      {self._summary_card("Passed", result.passed_count)}
      {self._summary_card("Failed", result.failed_count)}
      {self._summary_card("Errors", result.error_count)}
      {self._summary_card("Skipped", result.skipped_count)}
    </div>

    <section>
      <h2>Execution</h2>
      <dl class="metadata">
        {self._metadata_item("Actor", actor_name)}
        {self._metadata_item("Environment", result.execution.environment)}
        {self._metadata_item("Run ID", result.execution.run_id)}
        {self._metadata_item("Source", result.execution.source)}
        {self._metadata_item("Started", result.started_at)}
        {self._metadata_item("Completed", result.completed_at)}
        {self._metadata_item(
            "Duration",
            f"{result.duration_ms:.3f} ms",
        )}
        {self._metadata_item(
            "Compliant",
            "Yes" if result.is_compliant else "No",
        )}
      </dl>
    </section>

    <section>
      <h2>Requirement Findings</h2>
      <div class="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Status</th>
              <th>Requirement</th>
              <th>Scope</th>
              <th>Severity</th>
              <th>Message</th>
              <th>Expected</th>
              <th>Observed</th>
            </tr>
          </thead>
          <tbody>{rows}</tbody>
        </table>
      </div>
    </section>

    <footer>Generated by GovLattice</footer>
  </main>
</body>
</html>
"""

    def write(self, output_path: PathInput) -> Path:
        """Write the report atomically and return its resolved path."""
        path = self._resolve_output_path(output_path)
        write_text_atomically(path, self.build())
        return path

    def _finding_row(self, finding: RequirementFinding) -> str:
        scope = finding.state_id
        if finding.segment_name is not None:
            scope = f"{scope} / {finding.segment_name}"
        return f"""
            <tr>
              <td><span class="status {escape(finding.status.value)}">
                {escape(finding.status.value)}
              </span></td>
              <td>{escape(finding.requirement_type)}</td>
              <td>{escape(scope)}</td>
              <td>{escape(finding.severity.value)}</td>
              <td>{escape(finding.message)}</td>
              <td>{self._details(finding.expected)}</td>
              <td>{self._details(finding.observed)}</td>
            </tr>"""

    @staticmethod
    def _summary_card(label: str, value: int) -> str:
        return (
            f'<div class="card"><span>{escape(label)}</span>'
            f"<strong>{value}</strong></div>"
        )

    @staticmethod
    def _metadata_item(label: str, value: Any) -> str:
        display = "Not provided" if value is None else str(value)
        return (
            f"<div><dt>{escape(label)}</dt>"
            f"<dd>{escape(display)}</dd></div>"
        )

    @classmethod
    def _details(cls, value: Mapping[str, Any]) -> str:
        normalized = cls._normalize(value)
        text = json.dumps(
            normalized,
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
        return (
            "<details><summary>View</summary>"
            f"<pre>{escape(text)}</pre></details>"
        )

    @classmethod
    def _normalize(cls, value: Any) -> Any:
        if isinstance(value, Enum):
            return value.value
        if isinstance(value, Mapping):
            return {
                str(key): cls._normalize(child)
                for key, child in value.items()
            }
        if isinstance(value, (list, tuple)):
            return [cls._normalize(child) for child in value]
        if value is None or isinstance(
            value,
            (str, int, float, bool),
        ):
            return value
        return str(value)

    @staticmethod
    def _resolve_output_path(output_path: PathInput) -> Path:
        if not isinstance(output_path, (str, Path)):
            raise TypeError("output_path must be a string or Path")
        if isinstance(output_path, str) and not output_path.strip():
            raise ValueError("output_path must not be empty")
        path = Path(output_path).expanduser()
        if path.suffix.lower() != ".html":
            raise ValueError("output_path must use the .html extension")
        if not path.is_absolute():
            path = Path.cwd() / path
        path.parent.mkdir(parents=True, exist_ok=True)
        return path.resolve()
