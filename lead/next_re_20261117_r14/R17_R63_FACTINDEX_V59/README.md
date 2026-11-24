# R17_R63_FACTINDEX_V59 — FACT_INDEX v5.9

**这是当前权威版本。**

- 条数：**54**（F01–F54）
- grade：`[已证]` **27** / `[静态推断]` **1** / `[流程]` **24** / `未取得` **2** = 54
- `evidence_paths`：**140** 路径项，文件 **140/140**；带锚点 **116** = 机械 **101** + 节号体例 **15**；人工/未核验/裸目录/目录+锚 全 **0**；**MISS 0**
- 产物均 LF，CR 字节 0

## 与 v5.8 的区别：把「充分性」审计的真缺陷落地

v5.8 做了首次「锚充分性」审计（27 条 `[已证]`，判 18 SUPPORTED / 9 PARTIAL）。本版逐条复算那 9 条 gap，**驳回 5 条**，只修**真正成立的 3 条 + 1 条部分成立**：

| fact_id | 改动 |
|---|---|
| `F01` | 锚改指 archive「R17 第 20–21 轮 段」（954 限定语与 5-dword 上下文所在） |
| `F19` | 加锚 `R17_AUDIT_FACTINDEX\missing_entries.md`（正控「10 处」的真实出处） |
| `F27` | 加锚 `R17_R56_FACTINDEX_V53\lead_byte_checks.tsv`（68 的第二源，Lead 字节复算） |
| `F29` | `limitations` 记「InterlockedIncrement 为推断措辞」 |

被驳回的 5 条（`F04`/`F10`/`F21`/`F24`/`F31`）**无缺陷可修** —— 审计把「在自己的锚里找到」误报成锚位偏移、或把「单个锚未覆盖」当成证据缺口。详见 `CHANGES.md` §0。

## 目录内容

| 文件 | 说明 |
|---|---|
| FACT_INDEX.tsv | 事实底座主表（5 列） |
| CHANGES.md | v5.8 → v5.9 改动 + 9 条 PARTIAL 的逐条复算 |
| verify_anchors.ts | 可复跑核验器（8 项自检 + 六分类） |
| anchor_check.txt | 本轮输出（退出码 0） |
| REPORT.md | 自证与边界 |

## 用法

```
node --experimental-strip-types verify_anchors.ts FACT_INDEX.tsv <repoRoot>
```

## 版本沿革

| 版本 | 目录 | 条数 | 状态 |
|---|---|---|---|
| v5.0 | R17_R46_FACTINDEX_V5 | 49 | 作废 |
| v5.1 | R17_R47_GRADE_NORM | 49 | 作废 |
| v5.2 | R17_R51_FACTINDEX_V52 | 54 | 作废 |
| v5.3 | R17_R56_FACTINDEX_V53 | 54 | 作废 |
| v5.4 | R17_R57_FACTINDEX_V54 | 54 | 作废 |
| v5.5 | R17_R58_FACTINDEX_V55 | 54 | 作废 |
| v5.6 | R17_R59_FACTINDEX_V56 | 54 | 作废 |
| v5.7 | R17_R60_FACTINDEX_V57 | 54 | 作废 |
| v5.8 | R17_R61_FACTINDEX_V58 | 54 | 作废 |
| **v5.9** | **R17_R63_FACTINDEX_V59** | **54** | **★ 当前权威** |

（v1–v4.0 见各自目录的 `SUPERSEDED.md`。）
