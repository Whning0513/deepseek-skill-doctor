from __future__ import annotations

import json
from pathlib import Path

from deepseek_skill_doctor.cli import main

FIXTURES = Path(__file__).parent.parent / "fixtures"


def test_json_output(capsys) -> None:
    status = main(["check", str(FIXTURES / "valid-skill"), "--format", "json"])
    output = json.loads(capsys.readouterr().out)
    assert status == 0
    assert output["ok"] is True
    assert output["skills_checked"] == ["valid-skill"]


def test_errors_fail(capsys) -> None:
    status = main(["check", str(FIXTURES / "problematic-skill")])
    capsys.readouterr()
    assert status == 1

