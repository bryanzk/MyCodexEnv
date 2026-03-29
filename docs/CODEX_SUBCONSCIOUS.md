# Codex Subconscious

## Purpose
- 为 Codex Desktop 提供一个轻量级“后台脑”原型。
- 不改 Codex 本体；只读取本机已归档的 session transcript，并生成长期记忆与下次开局 briefing。
- 设计目标是先跑通 `读取历史 -> 聚合记忆 -> 生成 brief`，再用 automation 定时刷新。

## Inputs
- `~/.codex/archived_sessions/*.jsonl`
- `~/.codex/session_index.jsonl`

当前实现主要提取：
- 项目名 / cwd
- 最近 thread 标题
- 最近用户目标
- 常用工具
- 人类可读的阻塞信号

## Outputs
- `~/.codex/subconscious/index.json`
- `~/.codex/subconscious/memory.md`
- `~/.codex/subconscious/briefs/*.md`（启用 `--emit-briefs` 时）

## Commands
全量刷新：

```bash
python3 scripts/codex_subconscious.py build --emit-briefs
```

查看某个项目的 briefing：

```bash
python3 scripts/codex_subconscious.py brief --cwd /absolute/project/path
```

也可以把 brief 落盘：

```bash
python3 scripts/codex_subconscious.py brief \
  --cwd /absolute/project/path \
  --output ~/.codex/subconscious/latest-brief.md
```

发布到 Codex inbox：

```bash
python3 scripts/codex_subconscious.py publish-inbox \
  --cwd /absolute/project/path
```

发布最近 3 个活跃项目：

```bash
python3 scripts/codex_subconscious.py publish-inbox --limit 3
```

默认有 8 小时去重窗口；同标题 inbox 在窗口内已存在时会跳过。也可以显式指定：

```bash
python3 scripts/codex_subconscious.py publish-inbox --limit 3 --dedupe-hours 8
```

## Background Mode
推荐用 Codex automations 每小时刷新一次：
- 周期性执行 `build --emit-briefs`
- 若需要面向具体项目，可再单独跑一次 `brief --cwd ...`
- 若希望后台主动冒泡，可追加 `publish-inbox --cwd ...`
- 全局模式建议直接使用 `publish-inbox --limit 3`
- 全局模式建议保留默认 `--dedupe-hours 8`，避免每小时重复提醒同一项目

这样做的好处：
- 不依赖未公开 hook
- 不修改 `AGENTS.md`
- 不污染 repo
- 失败时只影响 companion，不影响正常 Codex 对话

## Current Limits
- 目前是离线/准实时方案，不是 Claude Subconscious 那种每轮 `PreToolUse` 注入。
- 记忆抽取是启发式聚合，不依赖外部模型；优点是零依赖、可验证，缺点是语义理解有限。
- 项目归并按 repo/worktree 名做，适合个人环境，不保证适用于所有目录结构。
- `publish-inbox` 目前只写 `~/.codex/sqlite/codex-dev.db` 的 `inbox_items` 表，不写 thread / logs / message 存储。
