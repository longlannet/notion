**🌐 Language / 语言：** [English](./README.md) | [简体中文](./README.zh-CN.md)

# Notion Skill

> 面向 **OpenClaw** 与本地自动化场景的 Notion Data API 工具箱。  
> 用一套统一 CLI、若干高频 helper 和一组验证脚本，把最有价值的 Notion 本地工作流做成 **可复用、可维护、可验证** 的工程化工具链。

**状态速览**

- **API 版本**：`2026-03-11`
- **核心入口**：`scripts/notion_api.py`
- **当前形态**：底层统一 CLI + 高频辅助脚本 + 回归验证脚本
- **脚本规模**：32 个 Python 脚本 / 12 个 Shell 脚本
- **主要能力**：页面、块、Markdown、数据源/数据库、字段、文件、评论、视图、模板

---

## 快速导航

- [这个仓库解决什么问题](#这个仓库解决什么问题)
- [亮点](#亮点)
- [项目结构](#项目结构)
- [安装与配置](#安装与配置)
- [快速开始](#快速开始)
- [常用命令](#常用命令)
- [验证与回归](#验证与回归)
- [覆盖范围与边界](#覆盖范围与边界)
- [适用场景](#适用场景)
- [许可证](#许可证)
- [相关文件](#相关文件)

---

## 这个仓库解决什么问题

如果你只是偶尔手调一下 Notion API，请求自己拼也能做。

这个仓库要解决的是另一类问题：

- 同一类 Notion 操作会反复出现
- 手拼 JSON 成本高、容易错
- 主流程需要更稳定、更短的调用方式
- 改完脚本后，希望能快速知道有没有把主路径改坏
- 需要在 OpenClaw、本地 shell、自动化任务里反复复用

所以它不是单纯的 API 示例集合，而是一个 **本地 Notion 自动化工具箱**。

---

## 亮点

- **统一入口**：底层能力集中在 `scripts/notion_api.py`
- **高频任务有 helper**：不用每次手拼复杂请求体
- **不仅能跑 happy path**：包含自检、能力诊断、模板就绪等待、属性项读取等实用配套
- **不是“文档说支持”**：有可执行的验证与回归脚本
- **主线版本明确**：当前已固定到 `2026-03-11`
- **边界清楚**：哪些强覆盖、哪些边界面、哪些不在主目标内，写得比较明确

---

## 你可以用它做什么

### 页面与内容

- 搜索页面和数据源
- 读取页面、块、Markdown、属性项
- 创建页面和子页面
- 更新页面标题和属性
- 追加、更新、删除、恢复块
- 用 Markdown 替换、插入、更新页面内容

### 数据源与数据库

- 创建 database / data source
- 查询数据源
- 创建结构化条目
- 更新条目字段
- 管理字段、属性和选项
- 处理 relation / rollup / formula / files 等常见 schema

### 文件、评论、视图、模板

- 上传文件并附加媒体内容
- 设置页面 / 数据库图标与封面
- 创建、读取、更新、删除评论
- 创建、读取、更新、删除视图
- 基于模板创建页面
- 等待模板内容异步就绪

### 工程化能力

- 环境自检
- 能力诊断
- 全表面验证
- helper 回归验证
- 版本迁移验证
- 回归矩阵验证

---

## 项目结构

```text
notion/
├── README.md
├── README.zh-CN.md
├── SKILL.md
├── scripts/
│   ├── notion_api.py
│   ├── selfcheck.py
│   ├── diagnose_capabilities.py
│   ├── page_ops.py
│   ├── append_block.py
│   ├── update_page_markdown.py
│   ├── wait_for_page_content.py
│   ├── create_data_source.py
│   ├── create_database_item.py
│   ├── update_database_item.py
│   ├── update_database_item_value.py
│   ├── create_view_preset.py
│   ├── import_external_file.py
│   ├── import_webpage.py
│   ├── set_page_media.py
│   ├── set_database_media.py
│   ├── validate_full_surface.py
│   ├── validate_helper_wrappers.py
│   ├── validate_2026_migration.sh
│   └── validate_regression_matrix.sh
└── .gitignore
```

根目录下的临时样例文件和非必要说明性杂项已经清掉。

### 分层说明

**1）底层统一 CLI**

`scripts/notion_api.py` 是核心入口，负责：

- 统一加载认证信息
- 统一设置 Notion API 版本头
- 统一处理 JSON 输入
- 统一输出错误结果
- 暴露主要能力面的子命令

**2）高频辅助脚本**

把常见任务变成更短、更稳、更适合自动化的调用方式，例如：

- `page_ops.py`
- `append_block.py`
- `update_page_markdown.py`
- `create_data_source.py`
- `create_database_item.py`
- `update_database_item_value.py`
- `create_view_preset.py`
- `set_page_media.py`
- `set_database_media.py`

**3）验证与回归脚本**

用于证明：

- 底层能力是真的通的
- helper 不是摆设
- 升级 API 版本后主路径没坏
- 后续改动可以快速回归确认

---

## 安装与配置

### 1）准备运行环境

确保本机可用：

- Python 3
- `requests`

安装依赖：

```bash
pip install requests
```

### 2）获取 Notion API Key

这个仓库走的是 **token 模式**，不是先走 OAuth 才能用的那条主路径。

你需要先在 Notion 创建一个 integration，然后拿到它的 API Key。

拿到 key 之后，脚本会按下面的顺序读取：

1. `NOTION_API_KEY`
2. `~/.config/notion/api_key`

也就是说：

- **如果环境变量和文件同时存在，优先使用环境变量**
- **如果你不想每次 export，推荐直接写到文件里**

### 3）API Key 放在哪里

你有两种放法。

#### 方式 A：放环境变量（临时会话最方便）

```bash
export NOTION_API_KEY="你的_notion_api_key"
```

这种方式适合：

- 临时测试
- 当前 shell 会话里跑几条命令
- CI / 自动化环境注入变量

#### 方式 B：放到本地配置文件（长期使用最方便）

**文件路径：**

```bash
~/.config/notion/api_key
```

**推荐直接这样创建：**

```bash
mkdir -p ~/.config/notion
printf '%s\n' '你的_notion_api_key' > ~/.config/notion/api_key
chmod 600 ~/.config/notion/api_key
```

**注意：**

- 文件内容就只放 **一行 key 本身**
- 不要写成 JSON
- 不要写变量名
- 不要额外包一层注释说明

正确示例：

```text
secret_xxx 或 notion_key_xxx
```

错误示例：

```text
NOTION_API_KEY=secret_xxx
```

```json
{"api_key":"secret_xxx"}
```

### 4）别忘了共享页面/数据库给 integration

就算 API Key 是对的，如果目标页面、数据库或数据源 **没有共享给这个 integration**，也一样会报权限错误。

所以配置完成后，记得把你要操作的目标资源分享给对应的 integration。

### 5）验证配置是否成功

最简单的检查方式：

```bash
python3 scripts/selfcheck.py
```

如果你想更直接一点，也可以执行：

```bash
python3 scripts/notion_api.py get-self
```

### 当前固定 API 版本

- **Notion-Version: `2026-03-11`**

### 可选：OAuth helper 的位置

这个仓库主线不是 OAuth 流程，但如果你后面真的要用到保留的 OAuth helper，代码里读取的位置是：

- `NOTION_CLIENT_ID` 或 `~/.config/notion/client_id`
- `NOTION_CLIENT_SECRET` 或 `~/.config/notion/client_secret`

不过对大多数本地使用场景来说，**你先配好 `api_key` 就够了**。

---

## 快速开始

### 1）先做环境自检

```bash
python3 scripts/selfcheck.py
```

### 2）搜索并读取页面

```bash
bash scripts/search_pages.sh "关键词"
bash scripts/read_page.sh PAGE_ID
python3 scripts/page_ops.py read-markdown PAGE_ID
```

### 3）创建子页面并追加内容

```bash
python3 scripts/page_ops.py create-subpage PARENT_PAGE_ID "新页面"
python3 scripts/append_block.py PAGE_ID paragraph "一段正文"
python3 scripts/append_block.py PAGE_ID heading 2 "章节标题"
```

### 4）创建数据源并写入一条记录

```bash
python3 scripts/create_data_source.py PARENT_PAGE_ID "示例库" rich
python3 scripts/create_database_item.py DATA_SOURCE_ID "Name" "第一条记录"
python3 scripts/update_database_item_value.py PAGE_ID "状态" status "进行中"
```

### 5）用 Markdown 更新内容或创建评论

```bash
python3 scripts/update_page_markdown.py PAGE_ID replace --content-file page.md
python3 scripts/notion_api.py create-comment --page-id PAGE_ID --text "这页看起来没问题"
```

---

## 常用命令

下面只放最常用的 80% 场景，尽量保持速查风格。

### 搜索与读取

如果你要录屏、贴日志或公开演示，建议打开脱敏模式：

```bash
NOTION_REDACT_OUTPUT=1 bash scripts/search_pages.sh "关键词"
```

常用 shell wrapper 也支持 `--redact`。很多原本会直接打印 JSON 的 Python helper 也会响应 `NOTION_REDACT_OUTPUT=1`，底层的 `scripts/notion_api.py`、`scripts/selfcheck.py`、`scripts/diagnose_capabilities.py` 现在也支持显式 `--redact`。注意：`--json` 仍然会返回原始 JSON。

```bash
bash scripts/search_pages.sh "关键词"
bash scripts/search_data_sources.sh "关键词"
bash scripts/read_page.sh PAGE_ID
bash scripts/get_data_source.sh DATA_SOURCE_ID
bash scripts/query_data_source.sh DATA_SOURCE_ID
python3 scripts/page_ops.py get-property PAGE_ID PROPERTY_ID
```

### 页面与块

```bash
python3 scripts/page_ops.py create-subpage PARENT_PAGE_ID "标题"
python3 scripts/page_ops.py update-title PAGE_ID "更新后的标题"
python3 scripts/append_block.py PAGE_ID paragraph "文字"
python3 scripts/append_block.py PAGE_ID todo "待办事项" false
python3 scripts/notion_api.py delete-block --block-id BLOCK_ID
python3 scripts/notion_api.py restore-block --block-id BLOCK_ID
```

### Markdown

```bash
python3 scripts/update_page_markdown.py PAGE_ID replace --content-file page.md
python3 scripts/update_page_markdown.py PAGE_ID insert "内容" "selector"
python3 scripts/wait_for_page_content.py PAGE_ID
```

### 数据源、条目、字段

```bash
python3 scripts/create_data_source.py PARENT_PAGE_ID "数据库" minimal
python3 scripts/create_database_item.py DATA_SOURCE_ID "Name" "条目"
python3 scripts/update_database_item.py PAGE_ID "文本" "更新内容" rich_text
python3 scripts/update_database_item_value.py PAGE_ID "状态" status "已完成"
python3 scripts/add_database_property.py DATA_SOURCE_ID "附件" files
python3 scripts/add_select_property.py DATA_SOURCE_ID "类型" "A,B,C"
python3 scripts/add_relation_property.py DATA_SOURCE_ID "关联项" RELATED_DATA_SOURCE_ID
```

### 文件、视图、评论

```bash
python3 scripts/import_external_file.py "https://example.com/file.pdf" sample.pdf application/pdf
python3 scripts/set_page_media.py PAGE_ID icon external "https://example.com/icon.png"
python3 scripts/create_view_preset.py DATABASE_ID DATA_SOURCE_ID table-basic "总览"
python3 scripts/notion_api.py list-views --data-source-id DATA_SOURCE_ID
python3 scripts/notion_api.py create-comment --page-id PAGE_ID --text "评论内容"
python3 scripts/notion_api.py update-comment --comment-id COMMENT_ID --markdown "**更新后的评论**"
```

如果你要更完整的命令面，直接看：

- `SKILL.md`
- `scripts/notion_api.py --help`

---

## 验证与回归

在运行验证脚本前，先显式设置一个已共享给 integration 的父页面 ID：

```bash
export NOTION_TEST_PARENT_PAGE_ID="你的共享父页面ID"
```

如果你想把原始验证产物保留在 `/tmp` 里方便排查，再额外设置：

```bash
export NOTION_KEEP_VALIDATION_ARTIFACTS=1
```

### 版本迁移验证

```bash
bash scripts/validate_2026_migration.sh
```

主要检查：

- 版本固定是否正确
- trash / restore 语义是否正确
- 兼容别名是否还能工作
- comment create / update / get / delete 是否正常

### 回归矩阵验证

```bash
bash scripts/validate_regression_matrix.sh
```

对主要工作流做更广的实时回归检查。

### 底层接口全表面验证

```bash
python3 scripts/validate_full_surface.py
```

成功标志：

```text
OK_NOTION_FULL_SURFACE=1
```

### 高层辅助脚本验证

```bash
python3 scripts/validate_helper_wrappers.py
```

成功标志：

```text
OK_NOTION_HELPER_WRAPPERS=1
```

两类验证脚本都会输出 `summary.json`，其中包含：

- PASS / BLOCKED / WARN 明细
- 临时资源 ID
- 清理备注

---

## 覆盖范围与边界

这个项目追求的是：

> **在本地自动化场景里，对 Notion Data API 做高实用度覆盖。**

### 当前强覆盖区域

- pages
- blocks
- markdown
- databases / data sources
- schema / property 操作
- files / media
- views
- comments
- templates

### 明确不是当前主目标的内容

- public OAuth 生命周期作为主工作流
- webhooks / event delivery
- compliance / SIEM
- MCP 产品面
- link previews 产品面
- integration gallery / publishing

### 已知边界

下面这些能力更适合作为边界面理解，而不是当前 helper 的核心承诺范围：

- 版本敏感的特殊块类型，如 `meeting_notes` / `transcription`
- returned-only / unsupported block 家族
- 某些依赖环境的能力，例如网页导入
- 某些高基数字段边界行为，更受工作区条件影响，而不是脚本本身限制

上面的范围与边界，就是这个仓库当前的实际使用基线。

---

## 适用场景

适合以下情况：

- 需要本地、可脚本化地操作 Notion
- 需要稳定的页面和内容自动化
- 需要结构化的数据源 / 数据库写入
- 需要字段与 schema 管理
- 需要文件、媒体、评论、视图相关自动化
- 需要有回归验证能力的 Notion 工具链

如果你只是一次性试几个 API，直接手写请求也可以。

如果你要的是：

- 可复用
- 可维护
- 可验证
- 适合 OpenClaw 或 shell 自动化

那这套仓库更合适。

---

## 许可证

这个仓库使用 **MIT License**。见 [`LICENSE`](./LICENSE)。

---

## 相关文件

- `SKILL.md`：面向代理运行时的操作说明
- `scripts/notion_api.py`：底层统一 CLI 入口

---

## 总结

这不是一个“给 Notion API 写几个示例脚本”的仓库。

它更像一个已经成型的 **本地 Notion 自动化工具箱**：

- 主线 Data API 能力覆盖广
- 分层清晰：底层 CLI + 高频 helper + 验证脚本
- 适合重复使用的本地自动化任务
- 有明确回归与版本迁移意识
- 有清晰的范围边界

如果你的目标是“偶尔调一下接口”，它可能有点重。

如果你的目标是“把 Notion 工作流稳定接进 OpenClaw、本地 shell 或自动化任务里”，它正是为这个方向设计的。

> **把最有价值的本地 Notion 工作流做得可靠、可脚本化、可验证。**
