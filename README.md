# DeepSeek Skill Doctor

[中文](README.zh-CN.md)

Agent Skills already have a specification and good general-purpose validators. This project does not try to replace them. It adds a small static profile for the parts that are easy to miss when a skill is loaded by DeepSeek Harness (DSH) or gives DeepSeek-specific tool-loop advice.

It checks things such as:

- a `SKILL.md` that is nested too deeply for DSH to discover;
- a useful trigger placed only in `whenToUse`, which DSH does not show in the model catalog;
- descriptions that exceed DSH's default 500-character catalog limit;
- host-only paths such as `.claude/skills` with no `.agents/skills` or `.dsh/skills` alternative;
- `allowed-tools` treated as if DSH enforced it;
- instructions that manufacture `reasoning_content` or use disabled thinking as the first workaround.

The base format check comes from the reference implementation in [`agentskills/agentskills`](https://github.com/agentskills/agentskills), pinned to a commit in `uv.lock`.

## Try it

Python 3.11+ and [uv](https://docs.astral.sh/uv/) are enough:

```bash
uvx --from git+https://github.com/Whning0513/deepseek-skill-doctor.git \
  dsskill-doctor check path/to/my-skill
```

JSON and GitHub Actions output are available:

```bash
dsskill-doctor check path/to/my-skill --format json
dsskill-doctor check .agents/skills --format github --strict
```

Passing a single bundle checks that bundle. Passing a skill root also checks DSH's one-level discovery rule.

## Use it with the general validator

Run [`skill-validator`](https://github.com/agent-ecosystem/skill-validator) for structure, links, token counts, orphan files, and content metrics. Then run this project for the DSH/DeepSeek profile:

```bash
skill-validator check path/to/my-skill
dsskill-doctor check path/to/my-skill
```

CI downloads the pinned `skill-validator v1.6.0` Linux binary and verifies its published SHA-256 before checking this repository's bundled skill.

## What this does not claim

This is static analysis. It does not execute scripts, contact a model, audit a skill for malware, or prove that DeepSeek will choose the skill on a real task. A clean result means these known compatibility mistakes were not found.

The checks are intentionally few and have stable codes. False positives and small, reproducible DSH fixtures are welcome in [Issues](https://github.com/Whning0513/deepseek-skill-doctor/issues).

MIT licensed. This is a community project, not an official DeepSeek component.

