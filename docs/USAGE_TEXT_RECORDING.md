# 文本自动记录工具

本仓库新增 `scripts/capture_text.py`，用于把你的文本自动分类并落盘。

## 分类规则
- command：看起来是终端命令（如 `git status`、`ls -la`、命令行代码块）
- prompt：疑似 prompt / 指令型提问（含“请你、请帮我、could you、please”等）
- dialogue：一般对话文本
- other：既不明显是命令，也不明显是 prompt 的文本

默认目录：`text_records/`

## 记录结构
- `text_records/ledger.jsonl`：结构化元数据（时间、分类、来源、路径、hash）
- `text_records/entries/YYYY-MM-DD/<category>/<id>.md`：原始文本内容

## 示例
```bash
# 终端命令（自动归入 command）
python scripts/capture_text.py "git status --short"

# 提示词（自动归入 prompt）
python scripts/capture_text.py "请帮我写一个日报总结模板"

# 对话（自动归入 dialogue）
python scripts/capture_text.py "今天把同步脚本再检查一遍"

# 手动指定分类（避免误判）
python scripts/capture_text.py --category dialogue "ls -la"
```

## 常用参数
- `--category {auto,command,prompt,dialogue,other}`：自动分类或指定分类
- `--source <label>`：来源标签（可选）
- `--out-dir <path>`：自定义输出目录
- `--tag a,b`：添加标签（可重复）
- `--json`：只输出 JSON 结果
