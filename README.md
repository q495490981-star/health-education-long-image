# 医学科普长图 Skill

把中文医学文章或宣教文案制作成适合手机阅读的手绘风格长图。默认保留用户原文，不加署名，内容较长时可分段制作后拼接。

> **素材库持续更新中，介意者暂时勿用。** 目前仅有 5 张通用插画，离线模式可能找不到完全匹配的图片；离线程序的真实中文字体显示效果尚待进一步验证。

## 两种生成方案

技能会根据当前 Agent 可用的能力选择路径；用户的明确要求优先。

| | Agent 自带图片生成 | 本地素材与排版 |
| --- | --- | --- |
| **适用情况** | Agent 已有可用的图片生成或编辑功能 | Agent 没有图片生成功能，但能读取文件、运行本地程序 |
| **插画来源** | 使用 Agent 的图片工具生成，可以按主题创作新的插画 | 使用仓库自带的插画素材；暂无对应素材时可留白或提示补充 |
| **文字处理** | 分段生成并逐段检查，注意模型可能出现错字、漏字或改写 | 使用本地程序将提供的文字排入图片，仍需检查输入和最终效果 |
| **所需条件** | 图片生成工具、对应账户权限及可用额度 | Python 3、Pillow、中文字体和本地文件/程序执行权限；生成过程无需图片生成 API 或密钥 |
| **当前限制** | 可用性、效果和费用取决于 Agent 与其工具 | 素材仍较少，无法自行画出素材库中没有的新场景；实际中文字体显示尚待验证 |

两种方式都需在发布前核对原文、医学内容、解剖和动作。素材是通用场景插画，不作为精确解剖图或动作教学依据。

## 效果展示

以下为使用图片生成能力制作的腰痛科普示例，展示分段与拼接效果；不是离线素材排版的实测效果。

### 分段图片

| 阶梯治疗 | 红旗信号 |
| :---: | :---: |
| [![阶梯治疗分段图](examples/stepwise-care.jpg)](examples/stepwise-care.jpg) | [![红旗信号分段图](examples/red-flags.jpg)](examples/red-flags.jpg) |

### 拼接后的完整长图

[![拼接后的完整腰痛科普长图](examples/lumbar-complete.jpg)](examples/lumbar-complete.jpg)

示例中的文字与医学内容仅供展示排版风格；实际宣教或发布前应结合原文及可靠资料核对。

## 当前素材库

第一批包含医患交流、腰痛、颈肩不适、膝痛、康复步行五类场景。素材库仍在持续更新，不能覆盖所有疾病和动作。

| 医患交流 | 腰痛 | 颈肩不适 |
| :---: | :---: | :---: |
| <img src="health-education-long-image/assets/illustrations/doctor-patient.png" width="200" alt="医患交流"> | <img src="health-education-long-image/assets/illustrations/low-back.png" width="180" alt="腰痛"> | <img src="health-education-long-image/assets/illustrations/neck-shoulder.png" width="180" alt="颈肩不适"> |

| 膝痛 | 康复步行 |
| :---: | :---: |
| <img src="health-education-long-image/assets/illustrations/knee.png" width="180" alt="膝痛"> | <img src="health-education-long-image/assets/illustrations/rehab-walk.png" width="180" alt="康复步行"> |

[查看完整素材与清单](health-education-long-image/assets/illustrations/)

## 安装：Codex 与其他 Agent

安装的是同一份技能。**安装方式与两种生成方案是两回事**：安装后，如果 Agent 有图片生成功能，会优先使用该功能；没有时，符合本地运行条件才使用素材库排版。

### 方法一：在 Codex 中让它帮忙安装

在 Codex 对话中发送：

```text
请使用 $skill-installer，安装这个 GitHub 仓库里的技能：
https://github.com/q495490981-star/health-education-long-image/tree/main/health-education-long-image
```

按照 Codex 的提示完成安装。如果当前环境没有 `$skill-installer`，可以使用下面的 ZIP 方法。

### 方法二：下载 ZIP 后手动安装（macOS / Linux，无需 Git）

1. 回到本仓库首页，点击绿色 **Code** 按钮，再点击 **Download ZIP**。
2. 解压下载的压缩包。在解压出的仓库目录内，找到 **`health-education-long-image` 文件夹**；打开它应能看到 `SKILL.md`、`scripts` 和 `assets`。
3. 将整个 `health-education-long-image` 文件夹复制到对应 Agent 的技能目录：

   | Agent | 默认个人技能目录 |
   | --- | --- |
   | Codex | `~/.agents/skills/` |
   | DeepSeek Harness | `~/.dsh/skills/`；也可使用 `~/.agents/skills/` |
   | Claude Code | `~/.claude/skills/` |
   | Gemini CLI | `~/.gemini/skills/`；也可使用 `~/.agents/skills/` |
   | VS Code 中的 GitHub Copilot | `~/.copilot/skills/` 或 `~/.agents/skills/` |

4. 检查目标路径：以 Codex 为例，应为 `~/.agents/skills/health-education-long-image/SKILL.md`。如已有同名技能，请先备份，避免覆盖。
5. 按对应 Agent 的技能列表或提示使用。部分环境需要刷新技能列表或开启文件访问与程序执行权限。

`~` 表示当前用户的主目录；以点开头的文件夹可能默认隐藏。DeepSeek Harness 的配置可能更改默认目录，以上路径以默认配置为例。桌面应用、云端会话和本地 CLI 的技能目录不一定共享。

### 方法三：下载 ZIP 后手动安装（Windows，无需 Git）

1. 点击仓库首页的 **Code → Download ZIP**，下载并解压。
2. 在解压后的仓库中找到包含 `SKILL.md` 的 `health-education-long-image` 文件夹。
3. 打开文件资源管理器，在地址栏输入下列路径之一；目录不存在时可手动新建：

   | Agent | 默认个人技能目录 |
   | --- | --- |
   | Codex | `%USERPROFILE%\.agents\skills` |
   | DeepSeek Harness | `%USERPROFILE%\.dsh\skills` 或 `%USERPROFILE%\.agents\skills` |
   | Claude Code | `%USERPROFILE%\.claude\skills` |
   | Gemini CLI | `%USERPROFILE%\.gemini\skills` 或 `%USERPROFILE%\.agents\skills` |
   | VS Code 中的 GitHub Copilot | `%USERPROFILE%\.copilot\skills` 或 `%USERPROFILE%\.agents\skills` |

4. 将整个 `health-education-long-image` 文件夹复制进去，并检查文件夹内能找到 `SKILL.md`。已有同名文件夹时请先备份。

有关技能发现位置和环境限制，参见 [Codex 文档](https://learn.chatgpt.com/docs/build-skills)、[DeepSeek Harness 文档](https://github.com/deepseek-ai/deepseek-harness/blob/master/packages/skill/skill-filesystem/README.zh.md)、[Claude Code 文档](https://code.claude.com/docs/en/skills) 和 [Gemini CLI 文档](https://geminicli.com/docs/cli/skills/)。

## 使用方法

安装后，在支持技能的 Agent 对话中提供文案或文件，例如：

> 使用 health-education-long-image，把我提供的文章做成科普长图。请保留全部原文；太长可分段制作后拼接，不要署名。

Codex 可以使用 `/skills` 查看，或在提示中输入 `$health-education-long-image`。其他 Agent 的调用方式以其技能列表和当前版本为准。若没有自动调用，请明确要求使用该技能。

### 离线排版程序

如果 Agent 没有图片生成能力、但能执行程序，可以使用本地素材排版。需要 Python 3、Pillow 和中文字体；如已安装 Pillow，无需重复安装。

```bash
python -m pip install Pillow
```

准备 UTF-8 编码的 `article.json`：

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

在解压出的仓库根目录运行：

```bash
python health-education-long-image/scripts/render_long_image.py --input article.json --output long-image.png
```

如提示找不到中文字体，可在命令后添加 `--font 字体文件的路径`，或设置 `HEALTH_IMAGE_FONT`。可用素材名称及对应场景见 `health-education-long-image/assets/illustrations/manifest.json`；不需要插画时可以省略 `illustration` 字段。程序不会联网下载字体或素材。遇到特别长的文章，需要按原文顺序分批制作并另行拼接。

## 文件结构

- `health-education-long-image/SKILL.md`：技能说明和两种工作流程。
- `health-education-long-image/scripts/render_long_image.py`：本地排版程序。
- `health-education-long-image/assets/illustrations/`：插画素材和清单，持续更新中。
- `examples/`：图片生成模式的分段与长图示例。

## 许可证

MIT，详见 [LICENSE](LICENSE)。本公开项目使用文字描述参考风格，不包含最初的参考图。

## 意见与建议

**本版本不是最终版本。** 如有意见和建议，欢迎通过本仓库的 [Issues](https://github.com/q495490981-star/health-education-long-image/issues) 留言。
