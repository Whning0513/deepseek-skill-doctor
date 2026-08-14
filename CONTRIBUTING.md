# Contributing

Please keep new checks narrow and reproducible. A rule should cover behavior specific to DeepSeek or DSH; general Agent Skills checks belong in the upstream specification or `skill-validator`.

For a bug or false positive, include a minimal `SKILL.md`, the command you ran, and the expected finding codes. Do not submit private prompts, API keys, or unredacted production captures.

Run before opening a pull request:

```bash
uv sync --locked --all-groups
uv run ruff check .
uv run pytest
uv run dsskill-doctor check skills/deepseek-skill-doctor --strict
```

Use one focused commit where practical. If a rule needs broad heuristics or an LLM judge, open an issue first so the trade-off can be discussed.

