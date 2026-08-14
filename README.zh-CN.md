# DeepSeek Skill Doctor

[English](README.md) | 中文

Agent Skills 已经有正式规范，也有成熟的通用检查器。这个项目不再重写一遍，只补 DSH 和 DeepSeek 容易踩到的几条：

- `SKILL.md` 藏得太深，DSH 根本发现不了；
- 真正的触发条件只写在 `whenToUse`，但 DSH 给模型看的目录不包含它；
- description 超过 DSH 默认的 500 字符目录上限；
- 只写 `.claude/skills`，没有 `.agents/skills` 或 `.dsh/skills` 的可移植路径；
- 以为 DSH 会执行 `allowed-tools` 限制；
- 建议伪造 `reasoning_content`，或者一出错就先关 thinking。

基础格式解析直接使用 [`agentskills/agentskills`](https://github.com/agentskills/agentskills) 的参考实现，并在 `uv.lock` 里固定 commit。

## 试一下

需要 Python 3.11+ 和 [uv](https://docs.astral.sh/uv/)：

```bash
uvx --from git+https://github.com/Whning0513/deepseek-skill-doctor.git \
  dsskill-doctor check path/to/my-skill
```

也可以输出 JSON 或 GitHub Actions annotation：

```bash
dsskill-doctor check path/to/my-skill --format json
dsskill-doctor check .agents/skills --format github --strict
```

传一个 Skill 目录就检查单个包；传 Skill 根目录时，还会模拟 DSH 的单层发现规则。

## 和通用检查器一起用

[`skill-validator`](https://github.com/agent-ecosystem/skill-validator) 负责结构、链接、token、孤立文件和内容指标；本项目负责 DSH/DeepSeek profile：

```bash
skill-validator check path/to/my-skill
dsskill-doctor check path/to/my-skill
```

CI 固定使用 `skill-validator v1.6.0`，下载后会先核对上游发布的 SHA-256。

## 它不做什么

这是静态检查。它不会执行 Skill 里的脚本，不会调用模型，也不能证明一个 Skill 安全或效果好。通过只表示目前这些已知兼容问题没有被发现。

如果规则误报，或者你手里有可以公开的 DSH 小案例，欢迎提 [Issue](https://github.com/Whning0513/deepseek-skill-doctor/issues)。

MIT License。第三方社区项目，不是 DeepSeek 官方组件。

