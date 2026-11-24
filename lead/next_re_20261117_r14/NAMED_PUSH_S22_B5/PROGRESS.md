# NAMED-PUSH S22 B5 — Progress

先建目录 → 写 REPORT 骨架 → 逐行核。vector 族独立判据（不套工厂 C1）。
③ 可伪证性：多值状态码 / Find -1 算；{0,1} bool 不算。④ 锚点落析构器判 FAIL（㉓）。

- [x] 建目录 + REPORT 骨架
- [x] 材料自校验（SHA256 / capstone / pefile）
- [x] 筛选得 9 行 vector 族 [62:71]
- [x] ② vtable+RTTI+slot2 全 9 行钉住（wide COL 扫描，slot_off=8 / slot_no=2）
- [x] ③b 全 9 行 = {0,1} bool 返回 → FAIL（operator new 空判断 + AL bool 出口）
- [x] ④ 逐行分类：DynamicVectorClass 5 行 ctor/global-init 锚 PASS；VectorClass 4 行仅 dtor/atexit 锚 FAIL(㉓)

## 逐行落盘记录（每 5 行追加）

### 批次 1（行 1-5）
| # | entry | ① | ② | ③b | ④ | 四环 | EVIDENCE |
|---:|---|---|---|---|---|---|---|
| 1 | 007642E0 | PASS | PASS | FAIL(bool) | PASS(ctor) | NO | ROW_007642E0.txt |
| 2 | 00765840 | PASS | PASS | FAIL(bool) | FAIL(dtor ㉓) | NO | ROW_00765840.txt |
| 3 | 007659F0 | PASS | PASS | FAIL(bool) | PASS(ctor) | NO | ROW_007659F0.txt |
| 4 | 00766C10 | PASS | PASS | FAIL(bool) | FAIL(atexit/dtor ㉓) | NO | ROW_00766C10.txt |
| 5 | 00766DC0 | PASS | PASS | FAIL(bool) | PASS(global-init) | NO | ROW_00766DC0.txt |

### 批次 2（行 6-9）
| # | entry | ① | ② | ③b | ④ | 四环 | EVIDENCE |
|---:|---|---|---|---|---|---|---|
| 6 | 00769E30 | PASS | PASS | FAIL(bool) | FAIL(dtor ㉓) | NO | ROW_00769E30.txt |
| 7 | 00769FE0 | PASS | PASS | FAIL(bool) | PASS(ctor) | NO | ROW_00769FE0.txt |
| 8 | 0076B8C0 | PASS | PASS | FAIL(bool) | FAIL(dtor ㉓) | NO | ROW_0076B8C0.txt |
| 9 | 0076BA70 | PASS | PASS | FAIL(bool) | PASS(ctor) | NO | ROW_0076BA70.txt |

## 完成汇总
- rows_checked=9 | ② ok=9 | ③b ok=0 | ④ ok=5 | all_four=0 | rate=0.0000
- 瓶颈：③b（全部 {0,1} bool，按任务规则不计） ⇒ delta.tsv 0 行（卡片允许 0 行）。
- S22 named 池 71 行：B1(18)+B2(18)+B3(13)+B4(13)+B5(9)=71 全部核完 ⇒ **池彻底清空**。
