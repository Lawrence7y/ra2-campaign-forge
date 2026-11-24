# R17_R57_FACTINDEX_V54 — FACT_INDEX v5.4

**这是当前权威版本。**

- 条数：**54**（F01–F54 连续）
- grade：`[已证]` **27** / `[静态推断]` **1** / `[流程]` **24** / `未取得` **2** = 54
- `evidence_paths`：**139** 个路径项，文件 **139/139** 存在；其中 **117** 项带锚点，锚点 **117/117** 可解析，**MISS 0**
- 全部路径仓库根相对；无裸行号；括号内无分号
- 产物均 LF，CR 字节 0

## 目录内容

| 文件 | 说明 |
|---|---|
| FACT_INDEX.tsv | 事实底座主表（5 列：fact_id / statement / grade / evidence_paths / limitations） |
| CHANGES.md | v5.3 → v5.4 逐条改动与依据 |
| anchor_check.tsv | 139 个路径项 + 117 个锚点的逐项核验结果 |
| REPORT.md | 自证与边界 |

## v5.4 只做一件事

把 16 条**已随归档失效**的看板段锚改指 `BOARD_ARCHIVE.md`。`statement` / `grade` / `limitations` **一字未动**。

根因不是笔误，是结构：**看板是会被周期性归档的文件，所以「看板段锚」天生不可长期有效**；`BOARD_ARCHIVE.md` 只追加、段标题稳定，才是可长期引用的锚载体。

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
| **v5.4** | **R17_R57_FACTINDEX_V54** | **54** | **★ 当前权威** |
