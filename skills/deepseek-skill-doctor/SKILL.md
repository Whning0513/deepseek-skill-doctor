---
name: deepseek-skill-doctor
description: Check Agent Skills for DSH discovery, description routing, host-path portability, and unsafe DeepSeek reasoning or thinking workarounds. Use when reviewing a SKILL.md for DeepSeek Harness, preparing a skill catalog entry, or debugging why DSH does not discover or invoke a skill.
---

# DeepSeek Skill Doctor

Run the existing Agent Skills validators first, then add the DeepSeek/DSH profile. Keep both result sets; they answer different questions.

## Check a skill

If `skill-validator` is installed, run its deterministic checks:

```bash
skill-validator check path/to/skill
```

Then run the DSH profile:

```bash
dsskill-doctor check path/to/skill --format json
```

Inside this repository, use `uv run dsskill-doctor`. Without an installation, use:

```bash
uvx --from git+https://github.com/Whning0513/deepseek-skill-doctor.git \
  dsskill-doctor check path/to/skill --format json
```

Pass a configured skill root instead of one bundle to check DSH's one-level discovery behavior.

## Interpret the result

1. Fix `AGENT_SKILLS_SPEC_INVALID` findings before DSH-specific warnings.
2. Treat `DSH_NESTED_SKILL_UNDISCOVERED` as a placement error: DSH only scans direct children of a skill root.
3. Put task and trigger words in `description`. DSH's model catalog does not expose `whenToUse` and truncates descriptions at 500 characters by default.
4. Apply tool restrictions in DSH configuration when a skill uses `allowed-tools`; do not assume the filesystem provider enforces that field.
5. Remove any instruction to manufacture `reasoning_content`. Preserve the provider's exact value through the tool loop.
6. Investigate request reconstruction before presenting disabled thinking as a generic fix.

The checker reads text files only. It does not execute skill scripts, validate task quality with a model, or make API calls. Report static findings as evidence, not proof that a skill is safe or effective.

