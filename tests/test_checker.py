from __future__ import annotations

from pathlib import Path

import pytest

from deepseek_skill_doctor.checker import check_path

FIXTURES = Path(__file__).parent.parent / "fixtures"


def codes(name: str) -> set[str]:
    return {item.code for item in check_path(FIXTURES / name).findings}


def test_valid_skill_has_no_findings() -> None:
    report = check_path(FIXTURES / "valid-skill")
    assert report.to_dict()["ok"] is True
    assert report.findings == []


def test_deepseek_and_portability_rules_are_specific() -> None:
    findings = codes("problematic-skill")
    assert "AGENT_SKILLS_SPEC_INVALID" in findings
    assert "DSH_WHEN_TO_USE_HIDDEN" in findings
    assert "DSH_ALLOWED_TOOLS_NOT_ENFORCED" in findings
    assert "HOST_PATH_LOCK_IN" in findings
    assert "DEEPSEEK_REASONING_SYNTHESIS" in findings
    assert "DEEPSEEK_DISABLE_THINKING_WORKAROUND" in findings


def test_negated_safety_instruction_does_not_trigger() -> None:
    findings = codes("valid-skill")
    assert "DEEPSEEK_REASONING_SYNTHESIS" not in findings
    assert "DEEPSEEK_DISABLE_THINKING_WORKAROUND" not in findings


def test_dsh_root_reports_nested_skill() -> None:
    findings = codes("nested-root")
    assert "DSH_NESTED_SKILL_UNDISCOVERED" in findings
    assert "NO_SKILLS_FOUND" in findings


def test_nested_symlinked_skill_is_reported_without_resolving_outside_root(tmp_path: Path) -> None:
    root = tmp_path / "skills"
    nested = root / "team" / "nested-skill"
    nested.mkdir(parents=True)
    external = tmp_path / "outside" / "SKILL.md"
    external.parent.mkdir()
    external.write_text(
        "---\nname: external\ndescription: Use this external skill for tasks.\n---\n",
        encoding="utf-8",
    )
    link = nested / "SKILL.md"
    try:
        link.symlink_to(external)
    except OSError as error:
        pytest.skip(f"symbolic links are unavailable: {error}")

    report = check_path(root)

    assert "DSH_NESTED_SKILL_UNDISCOVERED" in {item.code for item in report.findings}
    assert "NO_SKILLS_FOUND" in {item.code for item in report.findings}

