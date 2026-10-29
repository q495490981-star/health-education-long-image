# 医学科普长图 Skill

将中文医学文章或科普文案制作成温暖、易读的手绘风格长图：保留用户原文，内容过长时分段制作并按顺序拼接。

## 效果展示

以下是同一篇腰痛科普文章的两张分段图片，以及由多个分段拼接后的完整长图。点击图片可查看原图。

### 分段图片

| 阶梯治疗 | 红旗信号 |
| :---: | :---: |
| [![阶梯治疗分段图](examples/stepwise-care.jpg)](examples/stepwise-care.jpg) | [![红旗信号分段图](examples/red-flags.jpg)](examples/red-flags.jpg) |

### 拼接后的完整长图

[![拼接后的完整腰痛科普长图](examples/lumbar-complete.jpg)](examples/lumbar-complete.jpg)

示例展示排版和插画风格；图片中的文字与医学内容用于示例，实际宣教或发布前应结合原文及可靠资料核对。

## 特点

- **尊重原文**：默认保留标题、正文、关键数字、参考文献和免责声明，不擅自改写或删减。
- **温暖手绘**：米白底色、橘棕色标题、深色正文和手绘水彩插画，适合手机阅读。
- **长文分段**：文字较多时分段生成，逐段核对，再按顺序拼成长图。
- **按需调整**：默认不署名；当次明确指定的署名、文字和风格要求优先。
- **医学核查**：发现实质性疑点时单独说明，不悄悄修改用户文案。

## 安装到 Codex

### 方法一：让 Codex 帮你安装

在 Codex 对话中发送：

```text
请使用 $skill-installer，安装这个 GitHub 仓库里的技能：
https://github.com/q495490981-star/health-education-long-image/tree/main/health-education-long-image
```

根据 Codex 的提示完成安装。如果你的环境没有 `$skill-installer`，可以使用下面的手动方法。

### 方法二：手动安装（macOS / Linux）

需要安装 Git。在终端中运行以下命令，把技能安装到当前用户的技能目录：

```bash
mkdir -p ~/.agents/skills
work_dir="$(mktemp -d)"
git clone https://github.com/q495490981-star/health-education-long-image.git "$work_dir/repo"
cp -R "$work_dir/repo/health-education-long-image" ~/.agents/skills/
```

安装前请确认 `~/.agents/skills/health-education-long-image` 不存在；如已有同名技能，请先备份，避免覆盖。也可以把技能文件夹放到某个项目的 `.agents/skills/` 下，仅在该项目中使用。

### 方法三：手动安装（Windows PowerShell）

需要安装 Git。在 PowerShell 中运行：

```powershell
$workDir = Join-Path $env:TEMP "health-education-long-image-install"
git clone https://github.com/q495490981-star/health-education-long-image.git $workDir
New-Item -ItemType Directory -Force "$HOME\.agents\skills" | Out-Null
Copy-Item -Recurse "$workDir\health-education-long-image" "$HOME\.agents\skills\"
```

运行前请确认临时目录和目标目录均不存在；如已存在，请先处理同名目录。

以上是 Codex 的**本地技能安装**方法；ChatGPT Work 等其他环境的安装方式可能不同。详情参见 [OpenAI 官方技能文档](https://learn.chatgpt.com/docs/build-skills)。

## 如何使用

1. 在 Codex 中打开新对话，使用 `/skills` 查看技能，或输入 `$` 后选择 `health-education-long-image`。
2. 提供文章、文案或文件，描述本次需要的图片。示例：

   > 使用 $health-education-long-image，把我提供的文章做成一张科普长图。请保留全部原文，内容太长可以分段制作后拼接，不要署名。

3. 核对生成结果中的文字、医学内容、动作和解剖图示，再用于宣教或发布。

Codex 也可能根据任务自动选用匹配的技能；如果没有自动触发，可在提示中明确写出技能名称。

## 使用条件与注意事项

### 有图片生成能力的 Agent

优先使用该 Agent 当前可用的图片生成工具，按技能中的风格生成；如有原文，应逐段检查是否有错字或漏字。用户提供的风格参考图可在任务中单独附上。

### 没有图片生成能力的 Agent：本地素材与排版

如果 Agent 能读取文件并运行本地程序，可以使用技能自带的素材和 Python 排版程序。此路径无需图片生成接口或 API 密钥；需要 Python 3、Pillow 与本机中文字体。生成的插画仅限现有素材，素材不足时不能凭空创造新的插画。

首次使用需安装 Pillow（如已安装可跳过）：

```bash
python -m pip install Pillow
```

准备 UTF-8 编码的 JSON 文件，例如 `article.json`：

```json
{
  "title": "文章原文标题",
  "subtitle": "文章原文副标题",
  "sections": [
    {"heading": "原文小标题", "body": "这里放入完整的原文段落。", "illustration": "low-back"},
    {"heading": "另一个小标题", "body": "这里放入下一段完整的原文。", "illustration": "rehab-walk"}
  ]
}
```

在仓库根目录运行：

```bash
python health-education-long-image/scripts/render_long_image.py --input article.json --output long-image.png
```

如提示找不到中文字体，在命令后追加 `--font /字体文件的路径`；也可设置环境变量 `HEALTH_IMAGE_FONT`。安装后的脚本位于技能目录的 `scripts/` 下。可用素材名称和对应内容见 `health-education-long-image/assets/illustrations/manifest.json`；没有适合段落的图片时可省略 `illustration` 字段。程序不会联网下载字体或素材。

部分 Agent 不允许执行程序或读取本地文件，这些环境需要另行配置相应工具；单独的技能文件不能突破平台限制。极长文章可按原文顺序分批生成再拼接。

不同模型可能出现错字、漏字或改写，发布前应核对全文；医学内容应由具备相应专业能力的人审核。插画为通用场景，不作为解剖图或动作教学依据。

本公开项目使用文字描述参考风格，不包含原参考图。示例图片用于展示效果，非医疗建议。

## 文件结构

- `health-education-long-image/SKILL.md`：技能触发条件和操作说明。
- `health-education-long-image/agents/openai.yaml`：技能界面元数据。
- `health-education-long-image/assets/illustrations/`：五张通用手绘素材与清单。
- `health-education-long-image/scripts/render_long_image.py`：本地离线排版程序。
- `examples/`：长图和分段效果示例。

## 许可证

MIT，详见 [LICENSE](LICENSE)。
