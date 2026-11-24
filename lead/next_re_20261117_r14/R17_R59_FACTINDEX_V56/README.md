# R17_R59_FACTINDEX_V56 — FACT_INDEX v5.6

**这是当前权威版本。**

- 条数：**54**（F01–F54 连续）
- grade：`[已证]` **27** / `[静态推断]` **1** / `[流程]` **24** / `未取得` **2** = 54
- `evidence_paths`：**138** 路径项，文件 **138/138**；带锚点 **116** = 机械 **89** + 节号体例 **17** + 人工 **10**；**未核验 0**；**目录+锚 0**；**MISS 0**
- 另有 **13** 个「裸目录」路径项（`目录即卡`，可接受形态，单列计数）
- 产物均 LF，CR 字节 0

## 目录内容

| 文件 | 说明 |
|---|---|
| FACT_INDEX.tsv | 事实底座主表（5 列） |
| CHANGES.md | v5.5 → v5.6 改动、以及「未核验 40 → 0」的根因 |
| verify_anchors.ts | 可复跑核验器：8 项自检 + 六分类（机械/节号体例/人工/未核验/目录即卡/目录+锚），退出码 0/1/2/3 |
| anchor_check.txt | 本轮完整输出（冻结证据，退出码 0） |
| REPORT.md | 自证与边界 |

## 用法

```
node --experimental-strip-types verify_anchors.ts FACT_INDEX.tsv <repoRoot>
```

退出码：**0** 全通过 / **1** 有 MISS / **2** 自检失败（此时不输出任何核验数字）/ **3** 有锚点未能核验。

## 版本沿革

| 版本 | 目录 | 条数 | 状态 |
|---|---|---|---|
| v1 | R17_R34_FACT_INDEX | 16 | 作废 |
| v2 | R17_R38_FACTINDEX_FIX | 21 | 作废 |
| v3 | R17_R40_FACTINDEX_V3 | 26 | 作废 |
| v3.1 | R17_R42_F23_FIX | 26 | 作废 |
| v3.2 | R17_R44_FACTINDEX_V32 | 26 | 作废 |
| v4.0 | R17_R45_FACTINDEX_V4 | 38 | 作废 |
| v5.0 | R17_R46_FACTINDEX_V5 | 49 | 作废 |
| v5.1 | R17_R47_GRADE_NORM | 49 | 作废 |
| v5.2 | R17_R51_FACTINDEX_V52 | 54 | 作废 |
| v5.3 | R17_R56_FACTINDEX_V53 | 54 | 作废 |
| v5.4 | R17_R57_FACTINDEX_V54 | 54 | 作废 |
| v5.5 | R17_R58_FACTINDEX_V55 | 54 | 作废 |
| **v5.6** | **R17_R59_FACTINDEX_V56** | **54** | **★ 当前权威** |
