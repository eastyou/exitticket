# exitticket

[![CI](https://github.com/eastyou/exitticket/actions/workflows/ci.yml/badge.svg)](https://github.com/eastyou/exitticket/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.9%2B-brightgreen.svg)](pyproject.toml)

给老师用的课堂出门条生成器：下课前 3 分钟，让学生写一张小卡片，快速了解「今天学会了什么、哪里还没懂」。一条命令生成 **A4 纵向、可打印、可裁剪** 的卡片，每页 4 张。**零依赖，不联网，打印即用。**

出门条（exit ticket）是课堂形成性评价的常用工具：学生离场前用一两句话反馈，老师据此调整下一节课的节奏。本项目把排版、分页、裁剪线都预先做好，老师只需要选模板、填标题、按打印。

## 特性

- **5 种模板**：三二一回顾、一句话总结、最困惑的地方、自评量表、快速检测，文字按小学生阅读习惯编写
- **每页 4 张**：A4 纵向 2×2 排列，张数 1~8 自动分页，编号跨页连续
- **可裁剪**：卡片之间留出虚线裁剪线，打印后沿虚线剪开即可分发
- **手写空间充足**：书写行按字段自动分配高度，低年级学生也写得开
- **信息完整**：每张卡片都有标题、姓名/日期填写行、模板填写区、卡片编号与页脚页码
- **自包含 HTML**：CSS 内嵌、无网络资源，电脑或一体机离线打开即可
- **严格校验**：模板、份数、标题、输出路径全部检查，错误信息为中文；HTML 自动转义
- **101 个单元测试**：覆盖模板注册、别名解析、分页编号、转义、渲染与命令行退出码

## 安装

```bash
pip install exitticket
```

也可以直接使用源码，在项目根目录运行：

```bash
python -m exitticket --help
```

要求 Python 3.9 及以上，无第三方依赖。

## 用法

生成 4 张「三二一」出门条：

```bash
python -m exitticket --template 321 --copies 4 --title 课堂出门条 -o examples/课堂出门条.html
```

用浏览器打开生成的 HTML，按 `Ctrl/Cmd + P` 打印即可。

### 参数

| 参数 | 说明 | 默认 |
| --- | --- | --- |
| `--template` | 模板编号或中文别名 | `321` |
| `--copies` | 张数，1~8，每页 4 张自动分页 | `4` |
| `--title` | 卡片标题，1~40 个字符 | `课堂出门条` |
| `-o, --output` | 输出 HTML 路径 | `课堂出门条.html` |
| `--version` | 显示版本 | — |

模板编号与中文别名都可以用，大小写不敏感：

| 编号 | 中文名 | 卡片填写区 | 适合场景 |
| --- | --- | --- | --- |
| `321` | 三二一回顾 | 3 个收获、2 个疑问、1 个还想知道 | 常规课末回顾，信息量较全 |
| `oneline` | 一句话总结 | 今天最重要的一点、还不确定的一点 | 收束一个重点，30 秒完成 |
| `muddiest` | 最困惑的地方 | 一个最不明白的问题、一个例子 | 找教学盲点，安排下节课补救 |
| `selfcheck` | 自评量表 | 理解程度 1~4 勾选、理由 | 单元小结、复习课前自评 |
| `quickquiz` | 快速检测 | 两道短答题、信心指数 1~5 | 检查当堂目标是否达成 |

常用中文别名：`三二一`、`一句话`、`困惑`、`自评`、`小检测`。

```bash
# 中文别名同样可用
python -m exitticket --template 自评 --copies 8 --title 数学课出门条 -o 自评.html
```

### 退出码与报错

- `0`：生成成功
- `1`：读取或写入文件失败（例如目录不存在）
- `2`：参数不合法（未知模板、份数越界、标题超长等），错误信息为中文

未知模板时，程序会列出全部可选模板，例如：

```text
错误: 未知模板「quiz」，可选：321（三二一回顾）、oneline（一句话总结）、muddiest（最困惑的地方）、selfcheck（自评量表）、quickquiz（快速检测）
```

## 打印与裁剪

1. 用浏览器打开 HTML，按 `Ctrl/Cmd + P`
2. 纸张：**A4**
3. 方向：**纵向**
4. 缩放：**100%（默认）**
5. 边距：**无 / 默认**；如需看清卡片边框，勾选「背景图形」

每页 2×2 共 4 张，页与页之间的虚线是裁剪线。建议先沿中间的横竖虚线把整页切成 4 份，再用剪刀修齐边缘。每张卡片右上角有连续编号，便于按座位分发和回收统计。

屏幕预览会随窗口宽度等比缩放，不会出现横向滚动条；手机上也能看清整页布局。

## 教学用法（3 分钟）

1. **第 1 分钟**：发卡片，请学生填好姓名和日期，安静读题。
2. **第 2 分钟**：学生独立写，不讨论、不翻书，写多少算多少。
3. **第 3 分钟**：收卡。老师快速翻看，把「疑问」和「最困惑」的卡片单独放一叠。

第二天上课前，用 2~3 分钟回应出现最多的疑问；个别学生的问题可以课后单独聊。出门条不评分，只用来了解学情，学生才敢写真话。

## 项目结构

```text
exitticket/
├── exitticket/
│   ├── model.py    # 模板、字段、别名注册、参数校验、分页
│   ├── render.py   # A4 纵向 2×2 排版、裁剪线与卡片 HTML
│   ├── cli.py      # 命令行入口、中文报错与退出码
│   └── __main__.py # python -m exitticket
├── tests/          # 101 个单元测试
├── examples/       # 示例出门条 HTML
├── .github/workflows/ci.yml
├── pyproject.toml
└── LICENSE
```

## 开发

```bash
# 运行全部单元测试
python -m unittest discover -s tests

# 重新生成示例
python -m exitticket --template 321 --copies 4 --title 课堂出门条 -o examples/课堂出门条.html
```

自定义模板时，可在 `exitticket/model.py` 的 `TEMPLATES` 中新增 `TicketTemplate`：填写区用 `Field(title, lines, kind)` 描述，`kind` 支持 `lines`（书写行）、`scale4`、`scale5`（勾选量表）。新增后记得补一条别名解析测试。

## 许可证

[MIT](LICENSE) © 2026 eastyou
