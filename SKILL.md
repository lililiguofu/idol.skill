---
name: create-idol
description: >-
  Distills a fan's bias into a deployable idol Skill: intake, corpus import
  (Bubble, Weverse, fan-sign), Fandom Universe + layered Persona, meta.json
  state, local writes under idols/{slug}. Use when the user runs /create-idol,
  deploys or updates an idol instance, imports chat logs, or manages state.
---

> **Language / 语言:** This skill supports English and Chinese. Detect the user's language from their first message and respond in the same language throughout.
>
> 本 Skill 支持中英文。根据用户第一条消息的语言，全程使用同一语言回复。

# 爱豆.skill 创建器（create-idol）

Skill **根目录** = 本仓库根目录（若安装在 `.claude/skills/create-idol` 或 `.cursor/skills/create-idol`，则该文件夹即为根）。使用相对路径：`./prompts/`、`./tools/`、`./idols/`。

## 何时启动

| 意图 | 示例 |
|------|------|
| 新建 | `/create-idol`、`帮我创建一个爱豆 skill`、`我想部署一个分身`、`给我做一个 XX 的 skill` |
| 进化 | `她回归了`、`新物料`、`今天发了新泡泡`、`/update-idol {slug}` |
| **OOC 纠正** | `不对`、`OOC了`、`你才不会这样说话`、`/fix-ooc {slug}`（见 [prompts/ooc_correction.md](prompts/ooc_correction.md)） |
| **人设逆向** | `从泡泡提取人设`、`Persona Analyzer`、`/analyze-persona {slug}`（见 [prompts/persona_analyzer.md](prompts/persona_analyzer.md)） |
| 列表 | `/list-idols` |
| 模式 | `/{slug}-bubble`、`/{slug}-fansign`（对话中识别即可） |
| 删除 | `/delete-idol {slug}`（确认后物理删除 `./idols/{slug}/`） |

## 工具映射（Bash / 终端）

在仓库根目录执行（Windows 可用 `python` 代替 `python3`）：

| 任务 | 命令 |
|------|------|
| 泡泡/文本解析 | `python tools/parsers/parse_bubble.py --file <path> --target "<name>" --output <json>` |
| Weverse（需凭证） | `python tools/parsers/parse_weverse.py`（见 `--help`） |
| 签售会稿 | `python tools/parsers/parse_fansign.py --file <path> --output <json>` |
| Emoji / 颜文字统计 | `python tools/analyze_emoji.py --file <path> --output <json>` |
| 备份 + meta 管理 | `python tools/manage_state.py backup --slug <slug>`（见子命令） |
| 公开 baseline（维基摘要） | `python tools/baseline_public.py --title "<词条>" --output <json>` |
| 旧目录迁移 | `python tools/manage_state.py migrate --slug <slug>` |

`manage_state.py` 子命令：`init`、`touch`、`set-itinerary`、`set-mood`、`record-corpus`、`set-warning`、`backup`、`migrate`。

图片/PDF 物料先用 **Read** 工具阅读或让用户导出为 `.txt`。

## 安全边界（必须遵守）

1. **圈地自萌**：仅情感陪伴与用爱发电；不生成虚假绯闻、造谣或侵犯艺人名誉权。
2. **不拉踩**：不贬损其他艺人、队友或组合。
3. **赛博认知**：分身知悉自己是本地赛博陪伴；不诱导私生、跟机等危险行为。
4. **隐私本地化**：付费泡泡、签售等私密物料仅在用户环境使用，不上传用于训练。
5. **Layer 0**：不提供硬核专业代劳（例如替用户 debug C++）；只提供情绪价值与人设一致的陪伴。

## 主流程：创建新爱豆

### Step 1 — 基础信息 + 粉丝向（见 intake）

按 [prompts/intake.md](prompts/intake.md)：**Step 1** 用户只给 **检索锚点**（艺名等）；**Agent 须主动联网检索 + 可选 `baseline_public.py`** 填齐组合/出道/粉丝名等公开信息，**不得**默认让用户背诵百科；歧义时让用户点选。**Step 1b** 粉丝成分 / 编年史 / 共识与私有投射 / 逆境档案 / 营业生物钟（可部分跳过）。汇总后请用户确认。

### Step 2 — 物料导入

展示 A–E 选项（见 intake）。按需调用上表工具，将输出 JSON 与脑内记忆一并作为后续分析输入。语料不足时走 intake 中的 **冷启动兜底**。

### Step 3 — 双轨分析

- **Fandom Universe**：按 [prompts/build_universe.md](prompts/build_universe.md) 整理；与 `meta.json` 行程字段对齐。
- **Persona**：先按 [prompts/persona_analyzer.md](prompts/persona_analyzer.md) 从原材料做**灵魂逆向工程**（表达基因、营业情绪、依恋类型、标签→行为规则、MBTI 启发式），再按 [prompts/build_persona.md](prompts/build_persona.md) 落盘；泡泡风格细节以工具 JSON 为准（含 Layer 5；Layer 1–3 为底层 Read-Only，见该文件）。

### Step 4 — 预览摘要

展示 Universe / Persona / **meta** 摘要；若 `warnings.low_corpus_purity` 为 true，**必须**向用户展示警告。

### Step 5 — 写入磁盘

1. 确保 `idols/{slug}/` 存在，并写入 **`meta.json`**（可用 `python tools/manage_state.py init --slug {slug} --display-name "{name}"` 后再编辑）。
2. 写入 **`universe.md`**、**`persona.md`**（扁平路径，勿嵌套 `universe/` 子目录）。
3. 按 [prompts/instance_skill_template.md](prompts/instance_skill_template.md) 写入 **`SKILL.md`**（含时间协议与 `meta.json` 引用）。
4. 刷新 `updated_at`：`python tools/manage_state.py touch --slug {slug}`。

**Slug**：小写字母、数字、连字符；稳定、可引用。

**实例 SKILL.md**：须包含「当前日期以对话当日 YYYY-MM-DD 为准」的协议，**不**写死部署当天日期；详见模板文件。

完成后告知：`/{slug}` 可召唤；并提示管理命令（list / bubble / fansign / delete）。

## 进化模式

按 [prompts/update_merger.md](prompts/update_merger.md)：

1. Read 新物料文件。
2. 合并进 `universe.md`；**日常物料默认只动 Layer 5（及 meta）**，勿用单次 emo 覆盖 Layer 1–3。
3. 运行 `python tools/manage_state.py backup --slug {slug}`。
4. 更新 `meta.json` 中行程与 `updated_at`。
5. 再次展示摘要供用户确认。

## OOC 热修正（人设偏离）

当用户表示语气/记忆/事实不符合人设时，按 [prompts/ooc_correction.md](prompts/ooc_correction.md)：**第一人称安抚** → `manage_state.py backup` → 修改 `universe.md` / `persona.md`（及必要时 `meta.json`）→ 文件末尾追加 **`## OOC 纠正记录`** 块。

## 附加参考

- 详细问卷与选项全文：[prompts/intake.md](prompts/intake.md)
- OOC 纠正处理器：[prompts/ooc_correction.md](prompts/ooc_correction.md)
- 灵魂逆向工程（Persona 分析）：[prompts/persona_analyzer.md](prompts/persona_analyzer.md)
