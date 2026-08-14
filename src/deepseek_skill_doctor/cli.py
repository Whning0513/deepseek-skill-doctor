from __future__ import annotations

import argparse
from pathlib import Path

from . import __version__
from .checker import check_path
from .render import render_github, render_json, render_text


def main(argv: list[str] | None = None) -> int:
    parser = _parser()
    args = parser.parse_args(argv)
    if args.command is None:
        parser.print_help()
        return 0

    report = check_path(Path(args.path))
    renderer = {"text": render_text, "json": render_json, "github": render_github}[args.format]
    print(renderer(report), end="")
    if report.count("error") or (args.strict and report.count("warning")):
        return 1
    return 0


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="dsskill-doctor",
        description="Apply DeepSeek and DSH compatibility checks to Agent Skills.",
    )
    parser.add_argument("--version", action="version", version=__version__)
    subparsers = parser.add_subparsers(dest="command")
    check = subparsers.add_parser("check", help="check a skill bundle or DSH skill root")
    check.add_argument("path")
    check.add_argument("--format", choices=("text", "json", "github"), default="text")
    check.add_argument("--strict", action="store_true", help="fail when warnings are present")
    return parser


if __name__ == "__main__":
    raise SystemExit(main())

