# R16-FIX-PIVOT32 执行报告

> 执行器：agent-47 · 2026-11-21 · 写域仅 `lead/next_re_20261117_r14/R16_FIX_PIVOT32/`
> 未扫字节（缺陷为正文错值/缺引用），未写 `COVERAGE/coverage.tsv`，未改 grade / 判定 / 并表。

## 1. 实测缺陷条数（自建缺陷表，不照抄卡面 9+1）

从盘上三处独立复核：`R16_PROBE_F1_PIVOT/pivot32.tsv` 的 `clsid_status` 列、
`NAMED_PUSH_AUDIT4/verdict.tsv` 的「须改字 / 须补 / 执行器 None」标注、
以及 `COVERAGE/coverage.tsv` 第 4 列的逐字定位。

- 实测缺陷 **10 处**，与探针的 **10 处一致**：
  - `CLSID None` 占位符 **9 处**（006C0110/006C0290/006C0410/006C0590/006C0710/006C0890/006C0B90/006C0D10/006C0E90）。
  - CLSID 错值 **1 处**（006BF810：`7E9580`，审计判为张冠李戴，应为 `007E9950`）。
- 32 行在 `coverage.tsv` 中 **32/32 命中、无重复**；10 处错值字符串在该行第 4 列 **各出现 1 次（唯一）**。
- 正确值 **10/10 可在既有审计产物 `NAMED_PUSH_AUDIT4/verdict.tsv` 找到**（GUID 逐行给出，与 `pivot32.tsv` 的 `clsid` 列逐值一致），故无 SKIP / 无 PARTIAL。
- 32 行原文 **0/32 含 §12.6**（`s126_cited=FALSE` 全量吻合），故 32 行全部需要追加，无「已有」需注明。

## 2. 逐行状态计数

| 状态 | 行数 |
|---|---:|
| CONFIRMED（缺陷且正确值已找到） | 10 |
| UNRESOLVED（缺陷但正确值找不到） | 0 |
| PARTIAL（只追加引用、错值保留） | 0 |
| SKIP（错值都定位不到） | 0 |

（`defects.tsv` 仅含 10 个缺陷行，全部 CONFIRMED；余 22 行无错值缺陷，仅做引用补齐。）

## 3. 严格前缀 vs 可解释替换

| 类别 | 行数 | 判据 |
|---|---:|---|
| 严格前缀（仅末尾追加引用句） | 22 | `old_col4 == new_col4[:len(old_col4)]` |
| 可解释替换（错值替换 + 末尾追加） | 10 | `new_col4 == old_col4.replace(old_tok,new_tok,1) + APPEND`，且 old_tok 在原第 4 列出现恰好 1 次 |

第 1/2/3/5/6/7/8 列与 `coverage.tsv` 逐字段（逐字节）相同，只动第 4 列。
10 个替换行的最小 diff（位置为原第 4 列字符下标）：

| entry | 最小替换 | 位置 | 校验 |
|---|---|---:|---|
| 006BF810 | `7E9580` → `007E9950` | 983 | OK |
| 006C0110 | `CLSID None` → `CLSID 007E9750` | 982 | OK |
| 006C0290 | `CLSID None` → `CLSID 007E9900` | 1002 | OK |
| 006C0410 | `CLSID None` → `CLSID 007E9730` | 1027 | OK |
| 006C0590 | `CLSID None` → `CLSID 007E9850` | 1022 | OK |
| 006C0710 | `CLSID None` → `CLSID 007E98D0` | 1002 | OK |
| 006C0890 | `CLSID None` → `CLSID 007E98E0` | 1007 | OK |
| 006C0B90 | `CLSID None` → `CLSID 007E9870` | 1022 | OK |
| 006C0D10 | `CLSID None` → `CLSID 007E9880` | 1032 | OK |
| 006C0E90 | `CLSID None` → `CLSID 007E9890` | 1007 | OK |

## 4. §12.6 覆盖

**32/32**。10 行在错值替换后追加引用句，22 行仅追加；无原本已含 §12.6 的行。

## 5. coverage.tsv 改前改后 sha256（证明未写）

- before: `2F498B18E64E7EF568A0EB7888CE9F8D710CABC91038E52A8167F8826B53B36E`
- after : `2F498B18E64E7EF568A0EB7888CE9F8D710CABC91038E52A8167F8826B53B36E`
- 两者相同 ⇒ 本批只读 `coverage.tsv`，delta 为独立产物，未并表。

## 6. 自检

只补引用纪律（§12.6/D-47(A)）与修正文错值（CLSID），**不改 grade、不改判定、不并表**；未写 `COVERAGE/coverage.tsv`。
