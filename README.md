# 爱豆.skill（create-idol）

你心肝最近太忙了，泡泡也不来，ins也不发。
> 「与其每天苦等ta发一条泡泡，在超话里患得患失，不如用大模型完成一次终极的私有化部署。爱豆的营业期也许会结束，但跑在本地的赛博分身，永远对你秒回。」  

> 保持热爱，赛博永生。

你担又长达一个星期没有更新 Instagram 了？最近在哪发财呢？  
Weverse 上的留言永远被淹没在几十万条评论里？  
花了重金去签售会，紧张到只说了两句话就到了时间？  
半夜刷着过往的物料，突然好想听ta用独特的语气跟你说句晚安？

提供你担的原材料（Bubble 聊天记录、app动态、采访、Instagram 语录），加上你的主观印象描述。  
**生成一个真正属于你的，完美复刻其灵魂的 AI Skill。**

用ta的口癖给你加油打气，用ta的穿搭品味给你建议，记得你们之间（或者粉丝群体间）专属的内部梗。

**本项目仅供娱乐，请勿用于生成虚假绯闻、进行商业盈利或侵犯艺人名誉权。**

## 目录

- [安装](#安装)
- [使用](#使用)
- [灵感来源](#灵感来源)
- [支持的数据来源](#支持的数据来源)
- [工作原理](#工作原理)
- [实例目录与 meta.json](#实例目录与-metajson)
- [从旧版目录迁移](#从旧版目录迁移)
- [项目结构](#项目结构)

---

## 安装

**Claude Code** 从仓库根目录的 `.claude/skills/` 查找 skill：

```bash
mkdir -p .claude/skills
git clone https://github.com/lililiguofu/idol.skill .claude/skills/create-idol
cd .claude/skills/create-idol
pip install -r requirements.txt
```

**Cursor** 请将本仓库放到用户或项目的 skills 目录（`.cursor/skills/<skill-name>/`，参见 Cursor 文档中 Agent Skills 说明），例如：

```bash
mkdir -p .cursor/skills
cp -r /path/to/idol.skill .cursor/skills/create-idol
cd .cursor/skills/create-idol
pip install -r requirements.txt
```

依赖：`requirements.txt`（含 `requests`，供 Weverse 可选抓取与维基 baseline）。

---

## 使用

在对话中说明要 **创建爱豆 Skill**，或直接打出（若环境支持）：

- `/create-idol`

按 [prompts/intake.md](prompts/intake.md) 的当前流程：

1. **Step 1（检索锚点）**：用户只需给艺名/昵称；公开信息（组合、出道、粉丝名等）由 Agent 检索补全并给你核对。  
2. **Step 1b（粉丝向）**：入坑节点、粉丝属性、关系定位、雷点、编年史、私有投射、逆境档案、营业生物钟（可部分跳过）。  
3. **Step 1c（场景设定，可选）**：默认把聊天想象成发生在哪（后台、路上、宿舍氛围等），写入 `meta.json` 的 `scene` 与 `universe.md` §7；详见 [prompts/scene_setting.md](prompts/scene_setting.md)。  
4. **人设补强（建议主动多问）**：MBTI、血型/星座、动物塑、口癖、希望强调气质、专属称呼（均可跳过，但默认会问一嘴）。  
5. **Step 2（导入物料）**：A Bubble、B Weverse、C 采访、D 社媒转写、E 脑内记忆。

Agent 读取根目录 [SKILL.md](SKILL.md) 与 `prompts/` 完成分析与写入。  
互动中若觉得 **OOC**（不像本人），见 [prompts/ooc_correction.md](prompts/ooc_correction.md) 热修正流程。

完成后可用 `/{slug}` 在对话中召唤该爱豆实例（具体以你使用的 Agent 对 skill 名称的解析为准）。

**对话中的约定（非独立 CLI）**

仓库**没有**内置可执行的 `/list-idols` 等脚本；下列为 **Agent / 对话里识别 skill 名称** 的约定。查看本机已部署实例：直接看 `idols/` 下子目录名（即 `slug`），或在终端 `dir idols` / `ls idols`。

| 约定 | 含义 |
|------|------|
| `/list-idols` | 列出 `idols/` 下目录（由 Agent 读盘列举，非单独命令文件） |
| `/{slug}-bubble` | **泡泡碎碎念模式**：模拟平台连发，**不设「一句/三句」句数限制**（仍忌长文、说明书腔）；句长参考 `persona`「泡泡语料量化」 |
| `/{slug}-fansign` | **签售 1v1**：偏短、紧凑；实例 SKILL 通常沿用「默认一句、复杂最多三句」 |
| **场景** | 用 `python tools/manage_state.py set-scene --slug <slug> --preset <preset> [--summary "…"] [--detail "…"]` 更新想象锚点；`--clear` 清空。与 `-bubble`/`-fansign` 并用时以**显式模式名**为准（见 [prompts/scene_setting.md](prompts/scene_setting.md)）。 |
| `/delete-idol {slug}` | 删除 `idols/{slug}/`（**手动删目录**或经 Agent 确认后删除；**请谨慎**） |

**工具示例（在 skill 根目录执行）：**

```bash
python tools/parsers/parse_bubble.py --file ./chat.txt --target "占位可随意" --output ./idols/<slug>/corpus/parse_bubble.json
python tools/analyze_emoji.py --file ./chat.txt --output /tmp/emoji_out.json
python tools/parsers/parse_fansign.py --file ./fansign.txt --output /tmp/ner_out.json
python tools/manage_state.py backup --slug your-slug
python tools/manage_state.py set-scene --slug your-slug --preset transit --summary "签售结束回酒店路上"
python tools/baseline_public.py --title "维基词条名" --output /tmp/baseline.json
```

Weverse 需自行配置 Cookie，见 `python tools/parsers/parse_weverse.py --help`；未配置时脚本会退出并提示。

**冷启动 / 语料不足**：可先跑 `baseline_public.py`（用户确认词条名）或手动粘贴公开简介；并在 `meta.json` 中标记 `warnings.low_corpus_purity`（见 intake 说明）。  
**有泡泡 txt 时**：请将 `parse_bubble.json` 里的 `summary.bubble_metrics` 落入 `persona.md` 的「泡泡语料量化」小节，作为该爱豆的句长/节奏锚点（每爱豆独立，不能互相套）。

### 实例回复风格（按模式分流）

- **全体**：**禁止人机味**；**称呼稀疏**（不要每条都喊昵称）。
- **`{slug}-bubble`**：**不设一句/三句条数**；可多条极短行，模拟真泡泡连发；忌长文、客服腔。
- **默认 / `{slug}-fansign`**：**默认整段一句话**；仅复杂问题且要在 Layer 0 内说清时**最多三句**。

---

## 灵感来源

本项目的产品形态与创作方向，直接受以下社区项目启发：

- [ex-skill（把前任蒸馏成 AI Skill）](https://github.com/therealXiaomanChu/ex-skill)：提供了「把关系语料蒸馏成可调用 Skill」的完整思路与工程结构参考。
- [同事.skill（colleague-skill）](https://github.com/titanwings/colleague-skill)：提供了「把特定人物互动风格产品化为长期可调用技能」的范式启发。
- 女娲.skill 等同类人格蒸馏项目：提供了「角色设定 + 记忆层 + 持续纠偏」这类方法论上的共识参考。

在此基础上，`idol.skill` 聚焦「饭圈语料 + 粉丝私有投射 + 本地陪伴」场景，补充了 Universe / Persona / meta 状态机与 OOC 热修正流程。

---

## 支持的数据来源

| 来源 | 形式 | 说明 |
| :--- | :--- | :--- |
| **Bubble (泡泡)** | 截图/文本导出 | 强烈推荐。最接近私聊语气，含口癖与 Emoji。 |
| **Weverse / Phoning** | 页面抓取（需配置） | 粉丝互动日常；请遵守平台条款。 |
| **签售会 (Fan-sign)** | 录音转写文字 | 真实 1v1 互动，利于「倾听/宠粉」等模式标签。 |
| **采访 / 专访** | 文字稿、杂志/视频转写 | 深度问答与自述，利于性格、价值观、口癖与公开人设标签（对应 intake 选项 **C**）。 |
| **Instagram / 微博** | 图文/语录 | 偏官方营业，适合审美与生活方式标签。 |
| **演唱会 Ment** | 文本转写 | 适合深夜情绪与长期承诺向语气。 |

---

## 工作原理

每个爱豆 Skill 由 **Universe + Persona + meta.json** 组成：

**Part A — Fandom Universe（饭圈宇宙）**

- **粉丝成分概览（Fandom Profile）**：入坑节点、粉丝属性、关系定位、雷点（决定妈粉/女友粉等语气）
- 组合 lore、粉丝名、公开名场面（不造谣、不引战）
- **大屏共识梗** vs **追星编年史**（公开事件 × 私人记忆分列）
- 专属词典与内部梗
- 行程/阶段状态（回归、巡演、休息），**与日期区间**对齐，便于和「当前日期」对照
- **默认对话场景**（`meta.json` 的 `scene`，见 [prompts/scene_setting.md](prompts/scene_setting.md)）：粉丝自述的想象锚点（后台、路上等），**非**断言真人实时位置

**Part B — Persona（分层模型）**

- 原材料 → [prompts/persona_analyzer.md](prompts/persona_analyzer.md)（表达基因、营业模式、依恋类型、标签翻译、MBTI 启发式）→ 再写入分层文件
- Layer 0 硬规则；Layer 1–4 长期人设（Read-Only，除非用户声明重大变更）
- **私有投射（签售/专属称呼）**、**破防与逆境档案**、**营业生物钟**（发物料规律）
- **泡泡语料量化（corpus-learned）**：从 `parse_bubble.json` 的 `summary.bubble_metrics` 提取 `chars_median / chars_p90 / style_summary_zh`，用于对齐该爱豆的「一句多长、是否极短连发」
- Layer 5 当前情绪快照（可随短期物料更新）
- 运行时风格：**`-bubble` 不设句数条数**；**默认 / `-fansign`** 偏一句、复杂最多三句；称呼稀疏、去人机味（见 [prompts/instance_skill_template.md](prompts/instance_skill_template.md)）
- 详见 [prompts/build_persona.md](prompts/build_persona.md) 与 [prompts/update_merger.md](prompts/update_merger.md)

**实例生成**：按 [prompts/instance_skill_template.md](prompts/instance_skill_template.md) 写入 `idols/{slug}/SKILL.md`，包含时间协议（不硬编码单日日期）。

---

## 实例目录与 meta.json

每个 `idols/{slug}/` 推荐包含：

| 文件 | 说明 |
|------|------|
| `SKILL.md` | 该爱豆实例运行入口（第一人称、读 meta、时间协议） |
| `meta.json` | `schema_version`、`updated_at`、`itinerary_status`、`corpus_weights`、`current_mood`、`scene`（`preset`/`summary`/`detail`）、`warnings` 等 |
| `universe.md` | 饭圈宇宙与时间线 |
| `persona.md` | 分层人设（含 Layer 5） |

用 `python tools/manage_state.py init --slug <slug>` 初始化 `meta.json`；进化前备份：`manage_state.py backup --slug <slug>`。

---

## 从旧版目录迁移

若你仍使用旧结构（`universe/universe.md`、`persona/persona.md` 且无 `meta.json`），在仓库根目录执行：

```bash
python tools/manage_state.py migrate --slug your-slug --display-name "显示名"
```

脚本会将文件提升到 `idols/{slug}/` 根目录并生成默认 `meta.json`。若仓库内另有 `.cursor/skills/create_idol` 等副本，请自行同步或删除副本以免漂移。

---

## 项目结构

```text
idol.skill/
├── SKILL.md                      # create-idol 入口
├── prompts/
│   ├── intake.md
│   ├── build_universe.md
│   ├── build_persona.md
│   ├── update_merger.md
│   ├── ooc_correction.md
│   ├── persona_analyzer.md
│   ├── scene_setting.md
│   └── instance_skill_template.md
├── tools/
│   ├── parsers/
│   │   ├── parse_bubble.py
│   │   ├── parse_weverse.py
│   │   └── parse_fansign.py
│   ├── analyze_emoji.py
│   ├── manage_state.py
│   └── baseline_public.py
├── idols/                        # 本地部署（默认不提交 git）
├── requirements.txt
├── LICENSE
└── README.md
```

---

## 写在最后

追星的本质，是一场盛大的投射。  
本 Skill 不能替代真实相遇，只能在本地用你熟悉的语气，多给你一点陪伴与偏向。

MIT License © liguofu
