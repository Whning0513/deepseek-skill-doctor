from __future__ import annotations

import json

from .model import Finding, Report


def render_text(report: Report) -> str:
    data = report.to_dict()
    summary = data["summary"]
    lines = [f"DeepSeek Skill Doctor: {report.source}"]
    if report.skills:
        lines.append(f"Checked: {', '.join(report.skills)}")
    for item in report.findings:
        location = f" ({item.path})" if item.path else ""
        lines.append(f"[{item.severity.upper()}] {item.code}{location}: {item.message}")
        if item.hint:
            lines.append(f"  hint: {item.hint}")
    if not report.findings:
        lines.append("No DSH or DeepSeek compatibility findings.")
    lines.append(
        "Summary: "
        f"{summary['errors']} error(s), {summary['warnings']} warning(s), {summary['infos']} info"
    )
    return "\n".join(lines) + "\n"


def render_json(report: Report) -> str:
    return json.dumps(report.to_dict(), ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def render_github(report: Report) -> str:
    return "\n".join(_github_line(item) for item in report.findings) + (
        "\n" if report.findings else ""
    )


def _github_line(item: Finding) -> str:
    if item.severity == "error":
        level = "error"
    elif item.severity == "warning":
        level = "warning"
    else:
        level = "notice"
    metadata = [f"title={_escape(item.code)}"]
    if item.path:
        path, _, line = item.path.rpartition(":")
        if line.isdigit():
            metadata.extend((f"file={_escape(path)}", f"line={line}"))
        else:
            metadata.append(f"file={_escape(item.path)}")
    message = item.message if item.hint is None else f"{item.message} {item.hint}"
    return f"::{level} {','.join(metadata)}::{_escape(message)}"


def _escape(value: str) -> str:
    return value.replace("%", "%25").replace("\r", "%0D").replace("\n", "%0A")
