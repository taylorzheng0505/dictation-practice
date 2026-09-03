# 听写小助手 / Dictation Practice

把学校里的中文或英文听写内容，生成一个适合学生独立使用的单文件 HTML 听写练习页。

这个仓库同时支持三种使用方式：

1. **作为 ChatGPT Skill 使用**：直接使用仓库根目录的 `SKILL.md`、`agents/`、`scripts/` 和 `assets/`。
2. **交给其他 AI 使用**：把仓库提供给能读取文件/运行 Python 的 AI，并使用 `prompts/UNIVERSAL_PROMPT.md` 中的提示词。
3. **完全不用 AI，直接运行脚本**：准备一个“一行一个听写项”的 UTF-8 文本文件，然后运行生成脚本。

## 能做什么

- 支持英文、中文，以及中英混合听写。
- 英文任务在页面内提供 **美音 / 英音** 选择。
- 中文-only 任务自动隐藏英语口音设置。
- 语速、重复次数、书写时间都在页面内用明确的 `− / 数值 / +` 控件调整。
- 练习过程中使用 `上一条`、`再听一次`、`下一条`、`播放这一条` 等明确文字按钮。
- 听写时隐藏答案，结束后通过 `检查答案` 查看。
- 最终产物是一个独立 HTML 文件，浏览器打开即可使用。
- 播放使用浏览器自带 Speech Synthesis，不需要额外语音 API。

## 仓库结构

```text
dictation-practice/
├── README.md
├── SKILL.md
├── agents/
│   └── openai.yaml
├── assets/
│   ├── dictation-template.html
│   └── icon.svg
├── scripts/
│   └── generate_dictation.py
├── prompts/
│   └── UNIVERSAL_PROMPT.md
└── examples/
    ├── english-items.txt
    ├── mixed-items.txt
    └── english-demo.html
```

## 方法一：作为 ChatGPT Skill 使用

仓库根目录已经保留标准 Skill 结构。核心工作流定义在 `SKILL.md` 中。

典型请求：

> 帮我把下面这些做成听写练习：library、usually、because、take care of……

如果用户已经在对话中提供了听写内容，AI 应直接读取并生成页面；如果没有提供，只询问一次听写内容，不额外询问口音、语速、重复次数或书写时间，这些都由学生在页面内设置。

## 方法二：给其他 AI 使用

把这个仓库作为附件、工作区或代码仓库提供给 AI，然后把 `prompts/UNIVERSAL_PROMPT.md` 的内容发给它。

最关键的一句可以简化成：

> 请按照这个仓库的 `prompts/UNIVERSAL_PROMPT.md` 执行，把我提供的听写内容生成一个可直接打开的 HTML 听写练习页。

只要对应 AI 能读取仓库文件并运行 Python，就不需要支持 ChatGPT Skills，也能复用完全相同的生成器和页面模板。

## 方法三：不使用 AI，直接生成

项目只使用 Python 标准库，无需安装第三方依赖。

先准备一个 UTF-8 文本文件，例如 `items.txt`：

```text
library
usually
take care of
After school, I went to the library.
```

注意：**一行就是一个完整听写项**。句子内部的逗号、分号和中英文标点不会被拆分。

运行：

```bash
python3 scripts/generate_dictation.py \
  --items-file items.txt \
  --out dictation.html
```

如果需要自定义标题：

```bash
python3 scripts/generate_dictation.py \
  --items-file items.txt \
  --out dictation.html \
  --title "四年级英语 Unit 3 听写练习"
```

然后直接用浏览器打开 `dictation.html`。

## 输入规则

生成前应遵循这些规则：

- 每个单词、短语或句子视为一个独立听写项。
- 保留用户原文的拼写、中文字符、标点、大小写和措辞。
- 不要因为逗号、分号或中文标点拆分句子。
- 如果来源本身是编号/项目符号列表，只移除列表编号，不改正文。
- 不自动添加释义、翻译、音标、例句或教学材料，除非用户明确要求。
- 不猜测缺失的听写内容。

## 浏览器说明

听写页使用设备浏览器的 Speech Synthesis 功能。正常情况下直接打开即可；如果设备没有可用的英文语音或播放异常，可以换 Chrome、Edge 或 Safari 尝试。

## 示例

- `examples/english-items.txt`：英文示例输入
- `examples/mixed-items.txt`：中英混合示例输入
- `examples/english-demo.html`：由本仓库脚本实际生成的示例页面

## 适合分享到哪里

这个项目本身不依赖某一家 AI 平台。因此 GitHub 仓库可以同时作为：

- ChatGPT Skill 源码
- Claude / Gemini / Cursor / Codex 等工具的参考工作流
- Python 命令行小工具
- 听写页面模板源码

不同 AI 是否能直接执行仓库脚本，取决于它自身是否具备文件和代码运行能力；生成逻辑本身不依赖特定模型 API。
