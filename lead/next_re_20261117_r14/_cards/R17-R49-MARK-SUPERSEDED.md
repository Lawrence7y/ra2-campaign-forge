# 卡 R17-R49-MARK-SUPERSEDED · 给 7 个过期 `FACT_INDEX` 版本目录加作废标记

**产物目录必须写 `lead\next_re_20261117_r14\R17_R49_MARK_SUPERSEDED\`；产物不得含 CR。**
本卡**只新建标记文件**，**不改任何既有文件**。

## 〇、问题（Lead 实测）
盘上并存 **8 个**与 `FACT_INDEX` 相关的目录，**零个带作废标记**：

```
R17_R34_FACT_INDEX        ← v1（16 条）
R17_R38_FACTINDEX_FIX     ← v2（21 条）
R17_R40_FACTINDEX_V3      ← v3（26 条）
R17_R42_F23_FIX           ← v3.1（26 条，修 F23）
R17_R44_FACTINDEX_V32     ← v3.2（26 条，修路径/锚）
R17_R45_FACTINDEX_V4      ← v4.0（38 条）
R17_R46_FACTINDEX_V5      ← v5.0（49 条）
R17_R47_GRADE_NORM        ← v5.1（49 条，grade 规范化）★ 当前权威
```

**风险**：下任或任何读者可能打开**任意一个**并当作事实底座入口引错版本 —— 与之前 `R17_LEDGER_1063` 那次同类（那次已加 `SUPERSEDED.md` 修好）。

## 一、要做的

**1. 给下列 **7 个**目录各新建一份 `SUPERSEDED.md`**（`R17_R47_GRADE_NORM` 是权威版，**不要加**）：
 `R17_R34_FACT_INDEX` / `R17_R38_FACTINDEX_FIX` / `R17_R40_FACTINDEX_V3` / `R17_R42_F23_FIX` / `R17_R44_FACTINDEX_V32` / `R17_R45_FACTINDEX_V4` / `R17_R46_FACTINDEX_V5`

**每份内容按此模板**（把 `<...>` 填成该目录实际值）：

```markdown
# 本目录已作废 —— 请勿引用

本目录是 `FACT_INDEX` 的 <版本号>（<条数> 条），**已被 `R17_R47_GRADE_NORM`（v5.1，49 条）取代**。

## 当前权威版本
`lead\next_re_20261117_r14\R17_R47_GRADE_NORM\FACT_INDEX.tsv`（v5.1，49 条，grade 四档）

## 版本沿革
| 版本 | 目录 | 条数 | 作废原因 |
|---|---|---|---|
| v1 | R17_R34_FACT_INDEX | 16 | 被 v2 取代（内容审计后新增 M1/M2 等条目） |
| v2 | R17_R38_FACTINDEX_FIX | 21 | 被 v3 取代（补 coverage 头条数字 F22–F26） |
| v3 | R17_R40_FACTINDEX_V3 | 26 | 被 v3.1 取代（F23 的宽松正则口径未钉死） |
| v3.1 | R17_R42_F23_FIX | 26 | 被 v3.2 取代（路径基准混用 + 行号锚腐烂） |
| v3.2 | R17_R44_FACTINDEX_V32 | 26 | 被 v4.0 取代（补技术条/方法学 F27–F38） |
| v4.0 | R17_R45_FACTINDEX_V4 | 38 | 被 v5.0 取代（补完 U13–U23 → F39–F49） |
| v5.0 | R17_R46_FACTINDEX_V5 | 49 | 被 v5.1 取代（grade 列被污染成 10 种取值，规范化为 4 档） |
| **v5.1** | **R17_R47_GRADE_NORM** | **49** | **★ 当前权威** |

⇒ **凡在本目录看到的条目/数字，一律以 v5.1 为准。**
```

**2. 每份 `SUPERSEDED.md` 的「本目录是…」第一句要写对**：版本号与该目录的条数必须准确（见上表）。

## 二、硬约束
1. **不得修改这 7 个目录里已有的任何文件**（只**新建** `SUPERSEDED.md`）；也不得在 `R17_R47_GRADE_NORM` 里加标记。
2. 若某目录**已有** `SUPERSEDED.md`，**报错退出**，不要覆盖（本轮实测 7 个都没有）。
3. 产物：7 份 `SUPERSEDED.md`（**分别落在各自目录**）+ 本卡目录下的 `REPORT.md`（列出 7 个路径、各自新建时的字节数、以及**核验「原有文件未被改动」**的方法与结果——可给各目录原有文件的 mtime/sha 前后对照）。
4. 7 份 `SUPERSEDED.md` 与 `REPORT.md` 均**不得含 CR**。
5. 严格 **6 分钟**。