from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Literal

Severity = Literal["error", "warning", "info"]


@dataclass(frozen=True)
class Finding:
    code: str
    severity: Severity
    message: str
    path: str | None = None
    skill: str | None = None
    hint: str | None = None

    def to_dict(self) -> dict[str, str]:
        return {key: value for key, value in asdict(self).items() if value is not None}


@dataclass
class Report:
    source: Path
    skills: list[str] = field(default_factory=list)
    findings: list[Finding] = field(default_factory=list)

    def add(
        self,
        code: str,
        severity: Severity,
        message: str,
        *,
        path: str | None = None,
        skill: str | None = None,
        hint: str | None = None,
    ) -> None:
        self.findings.append(Finding(code, severity, message, path, skill, hint))

    def count(self, severity: Severity) -> int:
        return sum(item.severity == severity for item in self.findings)

    def to_dict(self) -> dict[str, object]:
        errors = self.count("error")
        warnings = self.count("warning")
        infos = self.count("info")
        return {
            "tool": "deepseek-skill-doctor",
            "source": str(self.source),
            "ok": errors == 0,
            "skills_checked": self.skills,
            "summary": {"errors": errors, "warnings": warnings, "infos": infos},
            "findings": [item.to_dict() for item in self.findings],
        }

