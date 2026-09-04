# Dictation Practice｜听写小助手

把学校布置的中文或英文听写内容，直接生成一个学生可以独立使用的 HTML 听写页面。

这个仓库同时服务三种使用方式：

1. **ChatGPT Skills**：直接使用仓库里的 `SKILL.md`、`agents/`、`scripts/`、`assets/`。
2. **其他 AI / Agent**：把 `prompts/UNIVERSAL_PROMPT.md` 交给支持文件和代码执行的 AI，让它按同一流程生成。
3. **本地 Python**：直接运行 `scripts/generate_dictation.py`。

## 当前版本的核心设计

- 中文、英文、中英混合听写均可。
- 对话中已经有听写内容时，AI 直接读取并生成；不要重复询问。
- 没有听写内容时，只问用户把听写内容发来，支持文字、照片、截图或文件。
- 每行作为一个听写条目；句子中的逗号、分号不拆分。
- **不使用浏览器 Web Speech / speechSynthesis。**
- 英文固定使用 Microsoft neural voice：`en-GB-SoniaNeural`。
- 中文固定使用 Microsoft neural voice：`zh-CN-XiaoxiaoNeural`（晓晓）。
- 通过 `edge_tts` Python API 直接预先生成 MP3，再嵌入最终 HTML，所以学生端不依赖设备自带音色。
- 最终产出是**单个自包含 `dictation.html`**，生成完成后可离线播放。

## 学生端交互

页面采用面向小学生的简化交互：

- 不提供男声 / 女声切换，也不要求学生配置声音。
- 播放设置保留：语速、朗读次数、书写时间。
- 设置使用明显的 `− / 数值 / +`，不依赖拖动条。
- 播放控制直接显示文字：`上一条`、`再听一次`、`下一条`、`播放这一条`。
- 不使用看起来像播放按钮、实际却不能点击的装饰图标。
- 听写过程中隐藏答案，完成后再通过 `检查答案` 查看。

## 仓库结构

```text
dictation-practice/
├── .gitignore
├── README.md
├── SKILL.md
├── agents/
│   └── openai.yaml
├── assets/
│   ├── dictation-template.html
│   └── icon.svg
├── examples/
│   ├── english-demo.html
│   ├── english-items.txt
│   └── mixed-items.txt
├── prompts/
│   └── UNIVERSAL_PROMPT.md
└── scripts/
    └── generate_dictation.py
```

## ChatGPT Skill 使用方式

将本仓库作为 Skill 使用时，核心入口是 `SKILL.md`。

典型输入：

```text
帮我生成今天的听写：
environment
responsibility
communicate
achievement
```

如果用户已经在对话中上传了学校作业照片或列出了听写内容，Skill 应直接读取并生成，不要再次追问音色、语速、朗读次数等设置。

如果用户只说：

```text
给我生成听写
```

只需要回复：

```text
把今天要听写的内容发给我吧。可以直接粘贴文字，也可以发学校作业的照片。
```

拿到内容后立即生成。

## 其他 AI 使用方式

如果对方没有安装 ChatGPT Skill，可以打开：

`prompts/UNIVERSAL_PROMPT.md`

把其中的提示词和本仓库一起交给支持 Python / 文件生成的 AI。这个提示词保留了相同的前置交互、内容整理规则、固定语音和 HTML 输出规范。

## 本地运行

环境要求：

- Python 3
- `edge-tts`
- 生成音频时需要联网访问对应的 TTS 服务

安装（**使用与你运行生成脚本相同的 Python 解释器**）：

```bash
python -m pip install edge-tts
```

如果你的环境使用 `python3` 或 Windows `py`，对应使用：`python3 -m pip install edge-tts` 或 `py -m pip install edge-tts`。

### 跨平台实现说明

生成脚本直接 `import edge_tts` 并调用 `edge_tts.Communicate`。它**不会**寻找或调用 `edge-tts` 命令行程序，因此不依赖系统 `PATH`，也不需要 `edge-tts.exe`、`.cmd/.bat`、shell wrapper 或 `subprocess`。Windows、macOS、Linux 统一走同一条 Python API 路径。

如果另一个 AI 发现 `edge_tts` 无法导入，应只检查“当前运行脚本的 Python 环境是否安装了该包”；不要转而排查 `where/which edge-tts` 或创建命令行 shim。

准备一个 UTF-8 文本文件，每行一个听写条目，例如：

```text
environment
responsibility
After school, I went to the library.
锲而不舍
全神贯注
```

运行：

```bash
python scripts/generate_dictation.py --items-file examples/mixed-items.txt --out dictation.html
```

生成后的 `dictation.html` 已经把 MP3 音频嵌入文件内部，可以单独发送给学生。

## 关于示例页

`examples/english-demo.html` 用于预览学生端 V5 页面布局和操作逻辑。仓库本身不提交 Microsoft 语音生成出来的示例音频；真实听写页请运行生成脚本，以确保最终音频确实来自固定的 Sonia / 晓晓声音。

## 固定声音

| 内容 | Voice ID |
|---|---|
| 英文 | `en-GB-SoniaNeural` |
| 中文 | `zh-CN-XiaoxiaoNeural` |

不要自动替换成浏览器系统声音。固定音色是这个项目的核心要求之一。
