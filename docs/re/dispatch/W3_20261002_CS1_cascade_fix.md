# W3-CS1 派工单 · **级联统一处置：6 个验证器的时点断言括号化升级**（ZCode 客户端 · 新会话）

> 工作目录 `D:\Project\ra2-campaign-forge` · 本卡只做这一包。
> **来源**（台账 §472 级联双案）：**APP1 授权追加 ATLAS**（`2a917e45f890/238788` → **`1dce588aa505/1212472` @18:17:38**）与 **SEM1 对 3 个 claims.txt 的 `#` 注释式勘误**，推翻了 6 个已验收验证器里的**时点性断言**（内容断言全绿）。**S2R2 已给模板**（`zcode_live/W3_20261002/s2r2_rebaseline/`：括号化 + 前缀逐字节 + sha 登记 ⇒ m36r/m31r 由红转绿）。

## 🔴 铁律（先读）
1. **只准动下表"允许动的断言"，其余断言一字不改**（内容断言必须原样通过）：
   | # | 文件 | 现红断言 | 允许动的处置 |
   |---|---|---|---|
   | 1 | `zcode_live/W3_20261002/s3_backfill/verify_s3.py` | `M25/M30/M33 claims.txt untouched`（子串 `'W3-S3'` 误报） | **改为精确块标记检查**（只认 `【W3-S3 回填】` 块首格式）；**必须保留对真实 S3 标记的检出力** |
   | 2 | `qc/W3_20261002/c1_ledger_fix/verify_c1.py` | live ATLAS 指纹（NOT CLEAN） | 双括：`pre@2a917e45f890/238788` + `post@1dce588aa505/1212472` + 允许 post 值 |
   | 3 | `workbuddy/W3_20261002/e1_claims_closure/verify_e1.py` | live ATLAS 指纹（FAIL=7） | 同上双括 |
   | 4 | `qc/W3_20261002/m43r_ch17_audit/verify_m43r.py` | T 系 + `V8/V9/V12`（锚点计数/只读括号） | V12 改双括；**V8/V9 改为"以 APP1 前括号值 与 APP1 后实测值 二选一皆可，但必须落在 {前,后} 集合内并打印所选"** |
   | 5 | `zcode_live/W3_20261001/m43_ch17_expand/verify_M43.py` | `V8/V9/V12` | 同 #4 |
   | 6 | `qc/W3_20261001/m27_claims_machinereadable/verify_m27fix.py` | `V15 正文指纹(live)` | 双括 |
2. **新断言必须更强**：双括值**必须逐字节实测登记**（来源：`qc/W3_20261002/app1_append/snapshots/` 有 APP1 改前快照；post 值现测），**并加"前缀可还原"检查**（pre 快照是现文件前缀 —— 取前 238,788 B 比对）。
3. **六验证器改前改后各跑一次（12 跑原文落 `runs/`）**：
   - 改前应为：#1 FAIL(3)、#2 NOT CLEAN、#3 FAIL(7)、#4 FAIL(4)、#5 FAIL(3)、#6 FAIL(1)（**逐一记录实况，与本卡预期不符即先停手报告**）
   - **改后须全部 EXIT=0**；改后仍红 ⇒ 回滚该文件并报告。
4. **负控（缺一不可）**：
   - **#1**：临时副本里**植入真实 `【W3-S3 回填】` 块 ⇒ 新断言必须 FAIL**（证明检出力没丢）；**植入纯字面 "W3-S3"（如 SEM1 那样引用）⇒ 必须 PASS**。
   - **#2–#6 任选一个**：临时把括号值改错 ⇒ 必须 FAIL。
5. **只读红线**：ATLAS、coverage_ledger、agy、minimax 原件、`ra2youli/**`、`tools/**` 不碰。
6. **写域**：上述 6 个 verify 文件（限铁律 1 范围）+ `out/re_work/zcode_live/W3_20261002/cs1_cascade/`

## 交付
`CS1_REPORT.md`（§A 十节骨架；`[0]` 直答：六文件各改了哪几行 diff、12 跑结果、负控结果）· `snapshots/`（6 文件改前副本+sha）· `runs/`（12 跑原文）· `verify_cs1.py`（**EXIT=0 + `verdict tally` 行**；断言：只动允许范围、内容断言数不变、12 跑全绿、负控全咬）

## 回报 `[0]`
① 六文件 diff 摘要 ② 12 跑 EXIT 表 ③ 负控结果 ④ 有无"改后仍红" ⑤ `verdict tally` 原文

## 底线
> **宁可交"6 个改了 5 个、第 6 个的某条内容断言因此变色你停手了"，也不要交一个把 V8/V9 删掉换 assert True 的全绿。**
