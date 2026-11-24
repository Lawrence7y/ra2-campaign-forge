# NAMED-PUSH S22 B4 — PROGRESS

> 范围：S22 named 去伪名 71 行，B1[0:18]+B2[18:36]+B3[36:49]=49 行已核，B4 剩余 22 行；本批按 A 核工厂族 13 行（切片 [49:62]，006C3E90…006C6110），vector 族 9 行（007642E0…0076BA70）待 lead 裁定范围。

## 进度
- [x] 建目录（work/ + EVIDENCE/）
- [x] 写 REPORT 骨架
- [x] 筛选命令与候选行（make_rows.py / filter_b4.py）
- [x] b4_rows.json 生成（工厂族 13 行）
- [x] 复制并适配分析脚本（analyze/gather/probe_mainvt/ring4/finalize_b4/gen_outputs_b4/report_table_b4）
- [x] 逐行核验 13/13，全部落盘 EVIDENCE/

## 逐行落盘记录（每 5 行追加）

### 行 1–5（已核，EVIDENCE 已落盘）
| # | entry | C1 主vt槽0 | ③b | ④ | 四环 | EVIDENCE |
|---:|---|---|---|---|---|---|
| 1 | 006C3E90 | FAIL(004F6830) | PASS | PASS | 不成立 | `EVIDENCE/ROW_006C3E90.txt` |
| 2 | 006C4190 | FAIL(0054DC60) | FAIL(仅两态) | PASS | 不成立 | `EVIDENCE/ROW_006C4190.txt` |
| 3 | 006C5210 | PASS(00410260) | PASS | PASS | **成立** | `EVIDENCE/ROW_006C5210.txt` |
| 4 | 006C5390 | PASS(00410260) | PASS | PASS | **成立** | `EVIDENCE/ROW_006C5390.txt` |
| 5 | 006C5510 | PASS(00410260) | PASS | PASS | **成立** | `EVIDENCE/ROW_006C5510.txt` |
> 小计：5 行核完，3 成立 / 2 FAIL（C1 主虚表地址不满足）。

### 行 6–10（已核，EVIDENCE 已落盘）
| # | entry | C1 主vt槽0 | ③b | ④ | 四环 | EVIDENCE |
|---:|---|---|---|---|---|---|
| 6 | 006C5690 | PASS(00410260) | PASS | PASS | **成立** | `EVIDENCE/ROW_006C5690.txt` |
| 7 | 006C5810 | PASS(00410260) | PASS | PASS | **成立** | `EVIDENCE/ROW_006C5810.txt` |
| 8 | 006C5990 | PASS(00410260) | PASS | PASS | **成立** | `EVIDENCE/ROW_006C5990.txt` |
| 9 | 006C5B10 | PASS(00410260) | PASS | PASS | **成立** | `EVIDENCE/ROW_006C5B10.txt` |
| 10 | 006C5C90 | PASS(00410260) | PASS | PASS | **成立** | `EVIDENCE/ROW_006C5C90.txt` |
> 小计：累计 10 行核完，8 成立 / 2 FAIL。

### 行 11–13（已核，EVIDENCE 已落盘）
| # | entry | C1 主vt槽0 | ③b | ④ | 四环 | EVIDENCE |
|---:|---|---|---|---|---|---|
| 11 | 006C5E10 | PASS(00410260) | PASS | PASS | **成立** | `EVIDENCE/ROW_006C5E10.txt` |
| 12 | 006C5F90 | PASS(00410260) | PASS | PASS | **成立** | `EVIDENCE/ROW_006C5F90.txt` |
| 13 | 006C6110 | PASS(00410260) | PASS | PASS | **成立** | `EVIDENCE/ROW_006C6110.txt` |
> 小计：13 行全部核完，11 成立 / 2 FAIL。

## 收口
- 13 行全部逐行取证并落盘：`EVIDENCE/` × 13，`delta.tsv` 11 行，`base_rate.tsv` = `S22_B4 13 11 12 13 11 0.8462`。
- ② 主虚表 C1（slot0=00410260）11/13；③b 12/13；④（含 C2 非析构）13/13；四环齐全 11/13。
- 2 行 FAIL：006C3E90（C1=004F6830 非规范，登记待裁）、006C4190（C1=0054DC60 + ③b 仅两态）。
- 范围：工厂族已核完；vector 族 9 行未核，待 lead 裁定是否扩到本批。
