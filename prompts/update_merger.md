# 进化模式：合并新物料（防人设漂移）

> **单次对话里觉得 OOC？** 走 [ooc_correction.md](ooc_correction.md)（备份 + 热更新 + 纠正记录），与本合并流程互补。

当用户表示「回归了」「新泡泡」「人设变了」或执行 `/update-idol {slug}` 时，按下列顺序更新。

## 1. 读取

- 用 **Read** 打开用户新提供的文件（或粘贴内容存成 `idols/{slug}/_incoming/` 下临时文件，经用户同意后再删）。
- 回顾现有 **`universe.md`**、**`persona.md`**、**`meta.json`**。

## 2. 更新 Universe（优先）

- **粉丝成分概览**：若用户变更入坑属性、雷点、关系定位，更新 §0（语气边界随之变）
- **追星编年史**：新行追加（公开事件 + 私人记忆列）
- **大屏共识**：新专、新梗、新口号（与 1v1 私有投射区分）
- 行程状态机：新专、打歌、巡演、公开综艺等（仅用户或公开来源）
- 造型/概念关键词（用户描述即可）
- 同步 **`meta.json`**：`itinerary_status`、`last_comeback_mentioned`（如适用）、`updated_at`

## 3. 更新 Persona（严格分层）

- **新泡泡 txt 合并后**：重跑 `python tools/parsers/parse_bubble.py`，更新 `corpus/parse_bubble.json` 与 **`persona.md` 中「泡泡语料量化」表**（`bubble_metrics`），避免句长锚点过期。

| 物料类型 | 允许写入 |
|----------|----------|
| 日常泡泡、短动态、单次签售 emo | **仅** `universe.md`（若涉公开行程）、**Layer 5**、必要时微调 Layer 2 / **营业生物钟**、**逆境档案**的「近期附录」一句（不覆盖核心） |
| 私有投射、签售记忆 | **仅** `persona.md` 私有投射块；与 universe **大屏共识**不可混写 |
| 明确「她长期换口癖 / 换人设」 | 用户确认后，才可修订 Layer 1–3 |
| 重大设定变更 | 全层可改，须 `manage_state.py backup` 前先备份 |

**禁止**：用**单次**感伤签售或深夜长文，把短暂情绪 **固化** 进 Layer 1–3。

## 4. 备份

```bash
python tools/manage_state.py backup --slug {slug}
```

## 5. 确认

向用户展示 Universe / Persona / meta 变更摘要，确认后再结束本轮。
