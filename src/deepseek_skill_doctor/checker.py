from __future__ import annotations

import os
import re
from collections.abc import Iterable
from pathlib import Path

from skills_ref.errors import ParseError
from skills_ref.parser import parse_frontmatter
from skills_ref.validator import validate as validate_agent_skill

from .model import Report

DSH_DESCRIPTION_LIMIT = 500
MAX_INSPECTED_FILE_SIZE = 1_000_000
TEXT_SUFFIXES = {".md", ".py", ".sh", ".js", ".mjs", ".ts", ".json", ".yaml", ".yml"}

TRIGGER_MARKER = re.compile(
    r"\b(use|used|when|whenever|for\s+(?:tasks|requests|workflows))\b|用于|适合|当.+时|在.+时",
    re.IGNORECASE,
)
HOST_SKILL_PATH = re.compile(
    r"(?:~?/)?(?:\.claude|\.codex|\.cursor|\.gemini)/skills(?:/|\b)",
    re.IGNORECASE,
)
SHARED_SKILL_PATH = re.compile(r"(?:\.agents|\.dsh)/skills(?:/|\b)", re.IGNORECASE)
REASONING_SYNTHESIS = re.compile(
    r"(?:invent|fabricat\w*|synthesi[sz]\w*|make\s+up|placeholder|dummy|伪造|编造|占位)"
    r".{0,100}reasoning_content",
    re.IGNORECASE,
)
DISABLE_THINKING = re.compile(
    r"(?:always|just|simply|first|default(?:\s+fix)?)"
    r".{0,50}(?:disable|turn\s+off).{0,30}(?:thinking|reasoning)"
    r"|(?:总是|直接|首先|默认).{0,30}(?:关闭|禁用).{0,20}(?:思考|推理)",
    re.IGNORECASE,
)
NEGATION = re.compile(r"\b(?:never|not|do\s+not|don't|mustn't|avoid)\b|不要|不得|禁止|避免", re.I)


def check_path(source: Path) -> Report:
    source = source.resolve()
    report = Report(source=source)
    if not source.exists():
        report.add("INPUT_NOT_FOUND", "error", "path does not exist", path=str(source))
        return report

    if source.is_file() and source.name.lower() == "skill.md":
        bundles = [source.parent]
    elif source.is_dir() and _skill_file(source) is not None:
        bundles = [source]
    elif source.is_dir():
        bundles = _discover_direct_bundles(source, report)
    else:
        report.add(
            "INPUT_NOT_SKILL",
            "error",
            "pass a skill directory, SKILL.md, or a DSH skill root",
            path=str(source),
        )
        return report

    if not bundles:
        report.add(
            "NO_SKILLS_FOUND",
            "error",
            "no direct <name>/SKILL.md bundles were found",
            path=str(source),
            hint="DSH only discovers one directory level beneath a configured skill root.",
        )
        return report

    for bundle in bundles:
        report.skills.append(bundle.name)
        _check_bundle(bundle, report)
    return report


def _discover_direct_bundles(root: Path, report: Report) -> list[Path]:
    bundles = [
        child
        for child in sorted(root.iterdir(), key=lambda item: item.name)
        if child.is_dir() and not child.is_symlink() and _skill_file(child) is not None
    ]
    direct_files = {(_skill_file(bundle) or Path()).resolve() for bundle in bundles}

    for current, directories, files in os.walk(root, followlinks=False):
        directories[:] = sorted(
            name
            for name in directories
            if not (Path(current) / name).is_symlink() and name not in {".git", ".venv"}
        )
        for filename in files:
            if filename.lower() != "skill.md":
                continue
            candidate = (Path(current) / filename).resolve()
            if candidate in direct_files:
                continue
            relative = candidate.relative_to(root)
            report.add(
                "DSH_NESTED_SKILL_UNDISCOVERED",
                "error",
                "DSH will not discover this nested SKILL.md from the supplied root",
                path=str(candidate),
                skill=candidate.parent.name,
                hint=(
                    f"Move {relative.parent.name} directly under the skill root or add its "
                    "parent as a custom root."
                ),
            )

    for flat_file in sorted(root.glob("*.md")):
        if flat_file.name.lower() in {"readme.md", "contributing.md", "security.md"}:
            continue
        if flat_file.name.lower() == "skill.md":
            continue
        text = _read_text(flat_file)
        if text is not None and text.startswith("---"):
            report.add(
                "DSH_FLAT_SKILL_NOT_PORTABLE",
                "warning",
                (
                    "DSH accepts flat Markdown skills, but the Agent Skills spec expects "
                    "<name>/SKILL.md"
                ),
                path=str(flat_file),
                skill=flat_file.stem,
            )
    return bundles


def _check_bundle(bundle: Path, report: Report) -> None:
    skill_file = _skill_file(bundle)
    if skill_file is None:
        return

    for message in validate_agent_skill(bundle):
        report.add(
            "AGENT_SKILLS_SPEC_INVALID",
            "error",
            message,
            path=str(skill_file),
            skill=bundle.name,
            hint="Fix the base Agent Skills format before applying the DSH profile.",
        )

    text = _read_text(skill_file)
    if text is None:
        report.add(
            "SKILL_NOT_UTF8",
            "error",
            "SKILL.md must be readable UTF-8 text",
            path=str(skill_file),
            skill=bundle.name,
        )
        return
    try:
        metadata, _ = parse_frontmatter(text)
    except ParseError:
        return

    description = metadata.get("description")
    if isinstance(description, str):
        if len(description) > DSH_DESCRIPTION_LIMIT:
            report.add(
                "DSH_DESCRIPTION_TRUNCATED",
                "warning",
                (
                    f"description is {len(description)} characters; DSH catalogs default to "
                    f"{DSH_DESCRIPTION_LIMIT}"
                ),
                path=str(skill_file),
                skill=bundle.name,
                hint="Put the task and trigger words in the first 500 characters.",
            )
        if not TRIGGER_MARKER.search(description):
            code = "DSH_WHEN_TO_USE_HIDDEN" if "whenToUse" in metadata else "DSH_TRIGGER_WEAK"
            hint = (
                "Move the trigger into description; DSH does not show whenToUse to the model."
                if "whenToUse" in metadata
                else "State what the skill does and when to use it in description."
            )
            report.add(
                code,
                "warning",
                "description does not state a recognizable usage trigger",
                path=str(skill_file),
                skill=bundle.name,
                hint=hint,
            )

    if "allowed-tools" in metadata:
        report.add(
            "DSH_ALLOWED_TOOLS_NOT_ENFORCED",
            "warning",
            "DSH's filesystem skill provider does not enforce allowed-tools",
            path=str(skill_file),
            skill=bundle.name,
            hint="Apply tool visibility in the DSH agent/plugin configuration as well.",
        )

    inspected = list(_text_files(bundle))
    combined = "\n".join(text for _, text in inspected)
    if HOST_SKILL_PATH.search(combined) and not SHARED_SKILL_PATH.search(combined):
        path, line = _first_match(inspected, HOST_SKILL_PATH)
        report.add(
            "HOST_PATH_LOCK_IN",
            "warning",
            (
                "skill hard-codes a host-specific skills directory without a shared "
                "DSH/Agent Skills path"
            ),
            path=_line_path(path, line),
            skill=bundle.name,
            hint="Also support .agents/skills or .dsh/skills, or declare the host requirement.",
        )

    reasoning_match = _first_non_negated(inspected, REASONING_SYNTHESIS)
    if reasoning_match is not None:
        path, line = reasoning_match
        report.add(
            "DEEPSEEK_REASONING_SYNTHESIS",
            "error",
            "skill appears to recommend inventing reasoning_content",
            path=_line_path(path, line),
            skill=bundle.name,
            hint="Preserve the exact reasoning_content returned by DeepSeek; never manufacture it.",
        )

    thinking_match = _first_non_negated(inspected, DISABLE_THINKING)
    if thinking_match is not None:
        path, line = thinking_match
        report.add(
            "DEEPSEEK_DISABLE_THINKING_WORKAROUND",
            "warning",
            "skill presents disabling thinking as a default or first-line fix",
            path=_line_path(path, line),
            skill=bundle.name,
            hint=(
                "Check request/history reconstruction first and describe disabling thinking "
                "as an explicit mode choice."
            ),
        )


def _skill_file(bundle: Path) -> Path | None:
    for name in ("SKILL.md", "skill.md"):
        candidate = bundle / name
        if candidate.is_file():
            return candidate
    return None


def _text_files(bundle: Path) -> Iterable[tuple[Path, str]]:
    for current, directories, files in os.walk(bundle, followlinks=False):
        directories[:] = sorted(
            name
            for name in directories
            if not (Path(current) / name).is_symlink() and name not in {".git", ".venv"}
        )
        for filename in sorted(files):
            path = Path(current) / filename
            if path.suffix.lower() not in TEXT_SUFFIXES or path.is_symlink():
                continue
            text = _read_text(path)
            if text is not None:
                yield path, text


def _read_text(path: Path) -> str | None:
    try:
        if path.stat().st_size > MAX_INSPECTED_FILE_SIZE:
            return None
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeError):
        return None


def _first_match(
    files: Iterable[tuple[Path, str]], pattern: re.Pattern[str]
) -> tuple[Path, int]:
    for path, text in files:
        match = pattern.search(text)
        if match:
            return path, text.count("\n", 0, match.start()) + 1
    raise ValueError("pattern was expected to match")


def _first_non_negated(
    files: Iterable[tuple[Path, str]], pattern: re.Pattern[str]
) -> tuple[Path, int] | None:
    for path, text in files:
        for line_number, line in enumerate(text.splitlines(), start=1):
            for match in pattern.finditer(line):
                prefix = line[max(0, match.start() - 40) : match.start()]
                if not NEGATION.search(prefix):
                    return path, line_number
    return None


def _line_path(path: Path, line: int) -> str:
    return f"{path}:{line}"
