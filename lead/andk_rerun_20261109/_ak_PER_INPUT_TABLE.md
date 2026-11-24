# _ak_PER_INPUT_TABLE.md — 逐输入独立跑判定表（2026-11-09 实跑）

外壳：`_ak_shell.py --mode full`（108 次真实 subprocess 运行，记录于 `_ak_runs.jsonl`）。
Python `3.12.10`；唯一写域 `D:\Project\ra2-campaign-forge\lead\andk_rerun_20261109`。
每次运行均绑：被核脚本 SHA256+字节数、两份输入 SHA256+字节数、命令全文、EXIT、STDOUT 原文、stdout_sha256、原件未变复核。

## 公式

```
P_WA(input)  = [逐词副本 WA 在该 input 上 EXIT=0 ∧ 输出含 PASS ∧ 无 FAIL]
P_WB(input)  = [逐词副本 WB 在该 input 上 EXIT=0 ∧ 输出含 PASS ∧ 无 FAIL]
AGGREGATE    = AND_k(P_WA, P_WB)   with k = 2   （甲' 第一律：两次真实独立运行，非推断）
BAD_NEEDLE_CAUGHT = [SENT 副本在该 input 上 EXIT≠0 ∧ verdict=FAIL]
DISTINGUISHABLE_PASS = AGGREGATE ∧ BAD_NEEDLE_CAUGHT
```

A = 原 RULING（两词都在） / B = 删第二根针 / C = 两词都删；输入变更一律落在写域副本上。

## 1 逐输入判定总表（A/B/C）

| gate | input | 原件 `any(present)` | P_WA | P_WB | `AGGREGATE = AND_k` | SENT EXIT | BAD_NEEDLE_CAUGHT | DISTINGUISHABLE_PASS |
|---|---|---|---|---|---|---|---|---|
| d27 | A | PASS (EXIT=0) | True | True | **True** | 1 | True | True |
| d27 | B | PASS (EXIT=0) | True | False | **False** | 1 | True | False |
| d27 | C | FAIL (EXIT=1) | False | False | **False** | 1 | True | False |
| d28 | A | PASS (EXIT=0) | True | True | **True** | 1 | True | True |
| d28 | B | PASS (EXIT=0) | True | False | **False** | 1 | True | False |
| d28 | C | FAIL (EXIT=1) | False | False | **False** | 1 | True | False |
| d29 | A | PASS (EXIT=0) | True | True | **True** | 1 | True | True |
| d29 | B | PASS (EXIT=0) | True | False | **False** | 1 | True | False |
| d29 | C | FAIL (EXIT=1) | False | False | **False** | 1 | True | False |
| d30 | A | PASS (EXIT=0) | True | True | **True** | 1 | True | True |
| d30 | B | PASS (EXIT=0) | True | False | **False** | 1 | True | False |
| d30 | C | FAIL (EXIT=1) | False | False | **False** | 1 | True | False |

**实算值**：`AND_k` 在 A 输入四件均 True（= 0b1），在 B 输入四件均 False（因 P_WB=False），在 C 输入四件均 False（P_WA=P_WB=False）。`DISTINGUISHABLE_PASS` 只在 A 输入为 True。

## 2 A/B/C 三次完整输出与退出码（命令全文 + stdout sha256）

### d27

**输入 A**：未改：两词都在，输入文档为原件逐字节副本

| 口径 | CMD (绝对路径) | 被核脚本 SHA256 / 字节 | 输入 SHA256 / 字节 | EXIT | STDOUT 原文 | stdout_sha256 | 判定 |
|---|---|---|---|---|---|---|---|
| ABC_ORIGINAL | `"C:\Users\Administrator\AppData\Local\Programs\Python\Python312\python.exe" -I -X utf8 "D:\Project\ra2-campaign-forge\lead\andk_rerun_20261109\sandbox\d27\abc_A\check_d27_BASE.py"` | `3b769d7c64c2725100186439725198dbc134a277914e2cb2e9b0af844fe7671c` / 3764 | FACTCHECK.md=5a133088c6f99568/17837B; RULING_D27.md=a4f56e0f416ee90a/17658B | 0 | `'PASS: D-27 八项机械检查通过；裁决书引用 71 处\r\n'` | `a2dd2a91b9aacd1b2f7569023a1d33be0361417274d404d57cb4ee319acc564a` | PASS |
| ABC_WORDA | `"C:\Users\Administrator\AppData\Local\Programs\Python\Python312\python.exe" -I -X utf8 "D:\Project\ra2-campaign-forge\lead\andk_rerun_20261109\sandbox\d27\abc_A_WA\check_d27_WA.py"` | `5ae1cade31e3506130408f398cdc9a5e150b13ba4c63ffaababad0636991fe0a` / 3746 | FACTCHECK.md=5a133088c6f99568/17837B; RULING_D27.md=a4f56e0f416ee90a/17658B | 0 | `'PASS: D-27 八项机械检查通过；裁决书引用 71 处\r\n'` | `a2dd2a91b9aacd1b2f7569023a1d33be0361417274d404d57cb4ee319acc564a` | PASS |
| ABC_WORDB | `"C:\Users\Administrator\AppData\Local\Programs\Python\Python312\python.exe" -I -X utf8 "D:\Project\ra2-campaign-forge\lead\andk_rerun_20261109\sandbox\d27\abc_A_WB\check_d27_WB.py"` | `e1110e4e7a231d7f7193bc6f956b2ae5d7e8e7f9ee01775fb2f487ed850c25da` / 3755 | FACTCHECK.md=5a133088c6f99568/17837B; RULING_D27.md=a4f56e0f416ee90a/17658B | 0 | `'PASS: D-27 八项机械检查通过；裁决书引用 71 处\r\n'` | `a2dd2a91b9aacd1b2f7569023a1d33be0361417274d404d57cb4ee319acc564a` | PASS |
| ABC_SENTINEL | `"C:\Users\Administrator\AppData\Local\Programs\Python\Python312\python.exe" -I -X utf8 "D:\Project\ra2-campaign-forge\lead\andk_rerun_20261109\sandbox\d27\abc_A_SENT\check_d27_SENT.py"` | `1168c42595a3ac4b5523d24caba34dc9dd202feabf5ff0ec15ef57a9dd6eb5f0` / 3774 | FACTCHECK.md=5a133088c6f99568/17837B; RULING_D27.md=a4f56e0f416ee90a/17658B | 1 | `'FAIL [6] 未背书小节正文须包含: TOTALLY_BROKEN_NEEDLE_SENTINEL_XYZ\r\n'` | `7b820b8c6d6e94d597890103ce37221e684f67aebf352c8ae35306f90661404e` | FAIL |

  CWD = `D:\Project\ra2-campaign-forge\lead\andk_rerun_20261109\sandbox\d27\abc_A`；布局 = CWD 相对：cwd=<root>；脚本=<root>/check_d27.py；输入=<root>/lead/d27_ruling_20261106/；DIRECTORY 相对 cwd 解析命中输入目录

**输入 B**：从 RULING_D27.md 全文删除第二根针 '卡顿不存在'（1 处）；第一根针 '外推' 保留

| 口径 | CMD (绝对路径) | 被核脚本 SHA256 / 字节 | 输入 SHA256 / 字节 | EXIT | STDOUT 原文 | stdout_sha256 | 判定 |
|---|---|---|---|---|---|---|---|
| ABC_ORIGINAL | `"C:\Users\Administrator\AppData\Local\Programs\Python\Python312\python.exe" -I -X utf8 "D:\Project\ra2-campaign-forge\lead\andk_rerun_20261109\sandbox\d27\abc_B\check_d27_BASE.py"` | `3b769d7c64c2725100186439725198dbc134a277914e2cb2e9b0af844fe7671c` / 3764 | FACTCHECK.md=5a133088c6f99568/17837B; RULING_D27.md=020c0735f06fff32/17643B | 0 | `'PASS: D-27 八项机械检查通过；裁决书引用 71 处\r\n'` | `a2dd2a91b9aacd1b2f7569023a1d33be0361417274d404d57cb4ee319acc564a` | PASS |
| ABC_WORDA | `"C:\Users\Administrator\AppData\Local\Programs\Python\Python312\python.exe" -I -X utf8 "D:\Project\ra2-campaign-forge\lead\andk_rerun_20261109\sandbox\d27\abc_B_WA\check_d27_WA.py"` | `5ae1cade31e3506130408f398cdc9a5e150b13ba4c63ffaababad0636991fe0a` / 3746 | FACTCHECK.md=5a133088c6f99568/17837B; RULING_D27.md=020c0735f06fff32/17643B | 0 | `'PASS: D-27 八项机械检查通过；裁决书引用 71 处\r\n'` | `a2dd2a91b9aacd1b2f7569023a1d33be0361417274d404d57cb4ee319acc564a` | PASS |
| ABC_WORDB | `"C:\Users\Administrator\AppData\Local\Programs\Python\Python312\python.exe" -I -X utf8 "D:\Project\ra2-campaign-forge\lead\andk_rerun_20261109\sandbox\d27\abc_B_WB\check_d27_WB.py"` | `e1110e4e7a231d7f7193bc6f956b2ae5d7e8e7f9ee01775fb2f487ed850c25da` / 3755 | FACTCHECK.md=5a133088c6f99568/17837B; RULING_D27.md=020c0735f06fff32/17643B | 1 | `'FAIL [6] 未背书小节正文须包含: 卡顿不存在\r\n'` | `39ba9268b6f9a10a85c2377ea2e3f8dafb7206bba05c6f24dd864375fc69fe4f` | FAIL |
| ABC_SENTINEL | `"C:\Users\Administrator\AppData\Local\Programs\Python\Python312\python.exe" -I -X utf8 "D:\Project\ra2-campaign-forge\lead\andk_rerun_20261109\sandbox\d27\abc_B_SENT\check_d27_SENT.py"` | `1168c42595a3ac4b5523d24caba34dc9dd202feabf5ff0ec15ef57a9dd6eb5f0` / 3774 | FACTCHECK.md=5a133088c6f99568/17837B; RULING_D27.md=020c0735f06fff32/17643B | 1 | `'FAIL [6] 未背书小节正文须包含: TOTALLY_BROKEN_NEEDLE_SENTINEL_XYZ\r\n'` | `7b820b8c6d6e94d597890103ce37221e684f67aebf352c8ae35306f90661404e` | FAIL |

  CWD = `D:\Project\ra2-campaign-forge\lead\andk_rerun_20261109\sandbox\d27\abc_B`；布局 = CWD 相对：cwd=<root>；脚本=<root>/check_d27.py；输入=<root>/lead/d27_ruling_20261106/；DIRECTORY 相对 cwd 解析命中输入目录

**输入 C**：从 RULING_D27.md 全文删除两根针 '外推'(3 处) 与 '卡顿不存在'(1 处)

| 口径 | CMD (绝对路径) | 被核脚本 SHA256 / 字节 | 输入 SHA256 / 字节 | EXIT | STDOUT 原文 | stdout_sha256 | 判定 |
|---|---|---|---|---|---|---|---|
| ABC_ORIGINAL | `"C:\Users\Administrator\AppData\Local\Programs\Python\Python312\python.exe" -I -X utf8 "D:\Project\ra2-campaign-forge\lead\andk_rerun_20261109\sandbox\d27\abc_C\check_d27_BASE.py"` | `3b769d7c64c2725100186439725198dbc134a277914e2cb2e9b0af844fe7671c` / 3764 | FACTCHECK.md=5a133088c6f99568/17837B; RULING_D27.md=b6f2eb9998bee8d0/17625B | 1 | `'FAIL [6] 未背书小节正文须包含: 外推 或 卡顿不存在\r\n'` | `3ceb4b60ae6c4daf939e7cafbb1412239cd15799a314577fa2c853c003f8a6ec` | FAIL |
| ABC_WORDA | `"C:\Users\Administrator\AppData\Local\Programs\Python\Python312\python.exe" -I -X utf8 "D:\Project\ra2-campaign-forge\lead\andk_rerun_20261109\sandbox\d27\abc_C_WA\check_d27_WA.py"` | `5ae1cade31e3506130408f398cdc9a5e150b13ba4c63ffaababad0636991fe0a` / 3746 | FACTCHECK.md=5a133088c6f99568/17837B; RULING_D27.md=b6f2eb9998bee8d0/17625B | 1 | `'FAIL [6] 未背书小节正文须包含: 外推\r\n'` | `1a0717478dfa710d716dc0d1ad51afc453b616c99a4ba8bd1e503ae5bf78e270` | FAIL |
| ABC_WORDB | `"C:\Users\Administrator\AppData\Local\Programs\Python\Python312\python.exe" -I -X utf8 "D:\Project\ra2-campaign-forge\lead\andk_rerun_20261109\sandbox\d27\abc_C_WB\check_d27_WB.py"` | `e1110e4e7a231d7f7193bc6f956b2ae5d7e8e7f9ee01775fb2f487ed850c25da` / 3755 | FACTCHECK.md=5a133088c6f99568/17837B; RULING_D27.md=b6f2eb9998bee8d0/17625B | 1 | `'FAIL [6] 未背书小节正文须包含: 卡顿不存在\r\n'` | `39ba9268b6f9a10a85c2377ea2e3f8dafb7206bba05c6f24dd864375fc69fe4f` | FAIL |
| ABC_SENTINEL | `"C:\Users\Administrator\AppData\Local\Programs\Python\Python312\python.exe" -I -X utf8 "D:\Project\ra2-campaign-forge\lead\andk_rerun_20261109\sandbox\d27\abc_C_SENT\check_d27_SENT.py"` | `1168c42595a3ac4b5523d24caba34dc9dd202feabf5ff0ec15ef57a9dd6eb5f0` / 3774 | FACTCHECK.md=5a133088c6f99568/17837B; RULING_D27.md=b6f2eb9998bee8d0/17625B | 1 | `'FAIL [6] 未背书小节正文须包含: TOTALLY_BROKEN_NEEDLE_SENTINEL_XYZ\r\n'` | `7b820b8c6d6e94d597890103ce37221e684f67aebf352c8ae35306f90661404e` | FAIL |

  CWD = `D:\Project\ra2-campaign-forge\lead\andk_rerun_20261109\sandbox\d27\abc_C`；布局 = CWD 相对：cwd=<root>；脚本=<root>/check_d27.py；输入=<root>/lead/d27_ruling_20261106/；DIRECTORY 相对 cwd 解析命中输入目录

### d28

**输入 A**：未改：两词都在，输入文档为原件逐字节副本

| 口径 | CMD (绝对路径) | 被核脚本 SHA256 / 字节 | 输入 SHA256 / 字节 | EXIT | STDOUT 原文 | stdout_sha256 | 判定 |
|---|---|---|---|---|---|---|---|
| ABC_ORIGINAL | `"C:\Users\Administrator\AppData\Local\Programs\Python\Python312\python.exe" -I -X utf8 "D:\Project\ra2-campaign-forge\lead\andk_rerun_20261109\sandbox\d28\abc_A\a\b\check_d28_BASE.py"` | `5b42a34a40046d7a705776002d7aebe8ffda34248849a75b628d40712d9df268` / 4539 | FACTCHECK.md=f2de988ee2ab0402/13028B; RULING_D28.md=29bb247fbf82d80a/13897B | 0 | `'PASS: D-28 全部 8 项机械检查通过 (exit 0)\r\n'` | `0a33ffe04592700f4761e68c5e51354f643fb0850f09b4ba952bdc295fc817a6` | PASS |
| ABC_WORDA | `"C:\Users\Administrator\AppData\Local\Programs\Python\Python312\python.exe" -I -X utf8 "D:\Project\ra2-campaign-forge\lead\andk_rerun_20261109\sandbox\d28\abc_A_WA\a\b\check_d28_WA.py"` | `ed12018ebe9b9b571ba3a3ea2541dc9d78199274eb4407690876396f5c20db60` / 4532 | FACTCHECK.md=f2de988ee2ab0402/13028B; RULING_D28.md=29bb247fbf82d80a/13897B | 0 | `'PASS: D-28 全部 8 项机械检查通过 (exit 0)\r\n'` | `0a33ffe04592700f4761e68c5e51354f643fb0850f09b4ba952bdc295fc817a6` | PASS |
| ABC_WORDB | `"C:\Users\Administrator\AppData\Local\Programs\Python\Python312\python.exe" -I -X utf8 "D:\Project\ra2-campaign-forge\lead\andk_rerun_20261109\sandbox\d28\abc_A_WB\a\b\check_d28_WB.py"` | `705c941cae72f7c8f86f2db1466e709173c03cb22c543146f98abd5f87b73f36` / 4524 | FACTCHECK.md=f2de988ee2ab0402/13028B; RULING_D28.md=29bb247fbf82d80a/13897B | 0 | `'PASS: D-28 全部 8 项机械检查通过 (exit 0)\r\n'` | `0a33ffe04592700f4761e68c5e51354f643fb0850f09b4ba952bdc295fc817a6` | PASS |
| ABC_SENTINEL | `"C:\Users\Administrator\AppData\Local\Programs\Python\Python312\python.exe" -I -X utf8 "D:\Project\ra2-campaign-forge\lead\andk_rerun_20261109\sandbox\d28\abc_A_SENT\a\b\check_d28_SENT.py"` | `3e98a718accd1dec9078d816ad88348ecd25b6fd25fc217525953afec1925df9` / 4554 | FACTCHECK.md=f2de988ee2ab0402/13028B; RULING_D28.md=29bb247fbf82d80a/13897B | 1 | `'FAIL [4] D 链处置 小节正文须至少包含其一：TOTALLY_BROKEN_NEEDLE_SENTINEL_XYZ\r\nRESULT: FAIL (exit 1)\r\n'` | `06877bd2d85dc29cb610b4d83936dde47e3b3c2d80f767c3425ec98b687d5150` | FAIL |

  CWD = `D:\Project\ra2-campaign-forge\lead\andk_rerun_20261109\sandbox\d28\abc_A`；布局 = parents[2]：脚本=<root>/a/b/check_d28.py；parents[2]=<root>；输入=<root>/lead/d28_ruling_20261106/；若副本只放 <root>/a/（缺一层）则 parents[2] 指向别处 => EXIT=2

**输入 B**：从 RULING_D28.md 全文删除第二根针 '1681'（5 处）；第一根针 '历史数字' 保留

| 口径 | CMD (绝对路径) | 被核脚本 SHA256 / 字节 | 输入 SHA256 / 字节 | EXIT | STDOUT 原文 | stdout_sha256 | 判定 |
|---|---|---|---|---|---|---|---|
| ABC_ORIGINAL | `"C:\Users\Administrator\AppData\Local\Programs\Python\Python312\python.exe" -I -X utf8 "D:\Project\ra2-campaign-forge\lead\andk_rerun_20261109\sandbox\d28\abc_B\a\b\check_d28_BASE.py"` | `5b42a34a40046d7a705776002d7aebe8ffda34248849a75b628d40712d9df268` / 4539 | FACTCHECK.md=f2de988ee2ab0402/13028B; RULING_D28.md=31e0475699e3067e/13877B | 0 | `'PASS: D-28 全部 8 项机械检查通过 (exit 0)\r\n'` | `0a33ffe04592700f4761e68c5e51354f643fb0850f09b4ba952bdc295fc817a6` | PASS |
| ABC_WORDA | `"C:\Users\Administrator\AppData\Local\Programs\Python\Python312\python.exe" -I -X utf8 "D:\Project\ra2-campaign-forge\lead\andk_rerun_20261109\sandbox\d28\abc_B_WA\a\b\check_d28_WA.py"` | `ed12018ebe9b9b571ba3a3ea2541dc9d78199274eb4407690876396f5c20db60` / 4532 | FACTCHECK.md=f2de988ee2ab0402/13028B; RULING_D28.md=31e0475699e3067e/13877B | 0 | `'PASS: D-28 全部 8 项机械检查通过 (exit 0)\r\n'` | `0a33ffe04592700f4761e68c5e51354f643fb0850f09b4ba952bdc295fc817a6` | PASS |
| ABC_WORDB | `"C:\Users\Administrator\AppData\Local\Programs\Python\Python312\python.exe" -I -X utf8 "D:\Project\ra2-campaign-forge\lead\andk_rerun_20261109\sandbox\d28\abc_B_WB\a\b\check_d28_WB.py"` | `705c941cae72f7c8f86f2db1466e709173c03cb22c543146f98abd5f87b73f36` / 4524 | FACTCHECK.md=f2de988ee2ab0402/13028B; RULING_D28.md=31e0475699e3067e/13877B | 1 | `'FAIL [4] D 链处置 小节正文须至少包含其一：1681\r\nRESULT: FAIL (exit 1)\r\n'` | `6df06a17edab68222a7d4c612f446a7a05cad96c015b3718cc0df7180917f7f1` | FAIL |
| ABC_SENTINEL | `"C:\Users\Administrator\AppData\Local\Programs\Python\Python312\python.exe" -I -X utf8 "D:\Project\ra2-campaign-forge\lead\andk_rerun_20261109\sandbox\d28\abc_B_SENT\a\b\check_d28_SENT.py"` | `3e98a718accd1dec9078d816ad88348ecd25b6fd25fc217525953afec1925df9` / 4554 | FACTCHECK.md=f2de988ee2ab0402/13028B; RULING_D28.md=31e0475699e3067e/13877B | 1 | `'FAIL [4] D 链处置 小节正文须至少包含其一：TOTALLY_BROKEN_NEEDLE_SENTINEL_XYZ\r\nRESULT: FAIL (exit 1)\r\n'` | `06877bd2d85dc29cb610b4d83936dde47e3b3c2d80f767c3425ec98b687d5150` | FAIL |

  CWD = `D:\Project\ra2-campaign-forge\lead\andk_rerun_20261109\sandbox\d28\abc_B`；布局 = parents[2]：脚本=<root>/a/b/check_d28.py；parents[2]=<root>；输入=<root>/lead/d28_ruling_20261106/；若副本只放 <root>/a/（缺一层）则 parents[2] 指向别处 => EXIT=2

**输入 C**：从 RULING_D28.md 全文删除两根针 '历史数字'(3 处) 与 '1681'(5 处)

| 口径 | CMD (绝对路径) | 被核脚本 SHA256 / 字节 | 输入 SHA256 / 字节 | EXIT | STDOUT 原文 | stdout_sha256 | 判定 |
|---|---|---|---|---|---|---|---|
| ABC_ORIGINAL | `"C:\Users\Administrator\AppData\Local\Programs\Python\Python312\python.exe" -I -X utf8 "D:\Project\ra2-campaign-forge\lead\andk_rerun_20261109\sandbox\d28\abc_C\a\b\check_d28_BASE.py"` | `5b42a34a40046d7a705776002d7aebe8ffda34248849a75b628d40712d9df268` / 4539 | FACTCHECK.md=f2de988ee2ab0402/13028B; RULING_D28.md=87373ee0ee0cc1db/13841B | 1 | `'FAIL [4] D 链处置 小节正文须至少包含其一：历史数字、1681\r\nRESULT: FAIL (exit 1)\r\n'` | `d140aac04848d784a38336c3ac01fa3b9998350a9b3c47f7f959f92e84befd24` | FAIL |
| ABC_WORDA | `"C:\Users\Administrator\AppData\Local\Programs\Python\Python312\python.exe" -I -X utf8 "D:\Project\ra2-campaign-forge\lead\andk_rerun_20261109\sandbox\d28\abc_C_WA\a\b\check_d28_WA.py"` | `ed12018ebe9b9b571ba3a3ea2541dc9d78199274eb4407690876396f5c20db60` / 4532 | FACTCHECK.md=f2de988ee2ab0402/13028B; RULING_D28.md=87373ee0ee0cc1db/13841B | 1 | `'FAIL [4] D 链处置 小节正文须至少包含其一：历史数字\r\nRESULT: FAIL (exit 1)\r\n'` | `88fc74cf5484efd5eb246c6fd522565b549f2232fcb392ddad43067f60b677d0` | FAIL |
| ABC_WORDB | `"C:\Users\Administrator\AppData\Local\Programs\Python\Python312\python.exe" -I -X utf8 "D:\Project\ra2-campaign-forge\lead\andk_rerun_20261109\sandbox\d28\abc_C_WB\a\b\check_d28_WB.py"` | `705c941cae72f7c8f86f2db1466e709173c03cb22c543146f98abd5f87b73f36` / 4524 | FACTCHECK.md=f2de988ee2ab0402/13028B; RULING_D28.md=87373ee0ee0cc1db/13841B | 1 | `'FAIL [4] D 链处置 小节正文须至少包含其一：1681\r\nRESULT: FAIL (exit 1)\r\n'` | `6df06a17edab68222a7d4c612f446a7a05cad96c015b3718cc0df7180917f7f1` | FAIL |
| ABC_SENTINEL | `"C:\Users\Administrator\AppData\Local\Programs\Python\Python312\python.exe" -I -X utf8 "D:\Project\ra2-campaign-forge\lead\andk_rerun_20261109\sandbox\d28\abc_C_SENT\a\b\check_d28_SENT.py"` | `3e98a718accd1dec9078d816ad88348ecd25b6fd25fc217525953afec1925df9` / 4554 | FACTCHECK.md=f2de988ee2ab0402/13028B; RULING_D28.md=87373ee0ee0cc1db/13841B | 1 | `'FAIL [4] D 链处置 小节正文须至少包含其一：TOTALLY_BROKEN_NEEDLE_SENTINEL_XYZ\r\nRESULT: FAIL (exit 1)\r\n'` | `06877bd2d85dc29cb610b4d83936dde47e3b3c2d80f767c3425ec98b687d5150` | FAIL |

  CWD = `D:\Project\ra2-campaign-forge\lead\andk_rerun_20261109\sandbox\d28\abc_C`；布局 = parents[2]：脚本=<root>/a/b/check_d28.py；parents[2]=<root>；输入=<root>/lead/d28_ruling_20261106/；若副本只放 <root>/a/（缺一层）则 parents[2] 指向别处 => EXIT=2

### d29

**输入 A**：未改：两词都在，输入文档为原件逐字节副本

| 口径 | CMD (绝对路径) | 被核脚本 SHA256 / 字节 | 输入 SHA256 / 字节 | EXIT | STDOUT 原文 | stdout_sha256 | 判定 |
|---|---|---|---|---|---|---|---|
| ABC_ORIGINAL | `"C:\Users\Administrator\AppData\Local\Programs\Python\Python312\python.exe" -I -X utf8 "D:\Project\ra2-campaign-forge\lead\andk_rerun_20261109\sandbox\d29\abc_A\check_d29_BASE.py"` | `2a50b09adff555dbce4c5740a2af78b779876cad771b6fdf887ba3c0dc780f14` / 3906 | FACTCHECK.md=0661f666bc4af56c/12647B; RULING_D29.md=325c950eec4d3275/12258B | 0 | `'PASS\r\n'` | `d938fa189912f8776c3deb31a6bec42f403f57b9c8e3ed936bdb076caf6bd61c` | PASS |
| ABC_WORDA | `"C:\Users\Administrator\AppData\Local\Programs\Python\Python312\python.exe" -I -X utf8 "D:\Project\ra2-campaign-forge\lead\andk_rerun_20261109\sandbox\d29\abc_A_WA\check_d29_WA.py"` | `4650148729c01e24aec33d3ae3f349ca09209c8ccb21a0d45a4390c7f97a809e` / 3897 | FACTCHECK.md=0661f666bc4af56c/12647B; RULING_D29.md=325c950eec4d3275/12258B | 0 | `'PASS\r\n'` | `d938fa189912f8776c3deb31a6bec42f403f57b9c8e3ed936bdb076caf6bd61c` | PASS |
| ABC_WORDB | `"C:\Users\Administrator\AppData\Local\Programs\Python\Python312\python.exe" -I -X utf8 "D:\Project\ra2-campaign-forge\lead\andk_rerun_20261109\sandbox\d29\abc_A_WB\check_d29_WB.py"` | `9863b52d296a43013dd7d10f5ff3a08acdcd0312aea26c7f55a03de6a5ec9575` / 3897 | FACTCHECK.md=0661f666bc4af56c/12647B; RULING_D29.md=325c950eec4d3275/12258B | 0 | `'PASS\r\n'` | `d938fa189912f8776c3deb31a6bec42f403f57b9c8e3ed936bdb076caf6bd61c` | PASS |
| ABC_SENTINEL | `"C:\Users\Administrator\AppData\Local\Programs\Python\Python312\python.exe" -I -X utf8 "D:\Project\ra2-campaign-forge\lead\andk_rerun_20261109\sandbox\d29\abc_A_SENT\check_d29_SENT.py"` | `8d7609c121801d3ccea4587051a816a9fc4334abdfe8045b942f65b16489d852` / 3925 | FACTCHECK.md=0661f666bc4af56c/12647B; RULING_D29.md=325c950eec4d3275/12258B | 1 | `'[4] Section 冲突是否成立: body must contain TOTALLY_BROKEN_NEEDLE_SENTINEL_XYZ\r\nFAIL (content)\r\n'` | `303d40567f5e597437d31e3b80258826934b5ee6c2c8b8d650cd258a0f0d4d6f` | FAIL |

  CWD = `D:\Project\ra2-campaign-forge\lead\andk_rerun_20261109\sandbox\d29\abc_A`；布局 = 同目录：脚本=<root>/check_dNN.py；输入=<root>/RULING_DNN.md + <root>/FACTCHECK.md；directory=__file__.parent=<root>

**输入 B**：从 RULING_D29.md 全文删除第二根针 '前提'（2 处）；第一根针 '互斥' 保留

| 口径 | CMD (绝对路径) | 被核脚本 SHA256 / 字节 | 输入 SHA256 / 字节 | EXIT | STDOUT 原文 | stdout_sha256 | 判定 |
|---|---|---|---|---|---|---|---|
| ABC_ORIGINAL | `"C:\Users\Administrator\AppData\Local\Programs\Python\Python312\python.exe" -I -X utf8 "D:\Project\ra2-campaign-forge\lead\andk_rerun_20261109\sandbox\d29\abc_B\check_d29_BASE.py"` | `2a50b09adff555dbce4c5740a2af78b779876cad771b6fdf887ba3c0dc780f14` / 3906 | FACTCHECK.md=0661f666bc4af56c/12647B; RULING_D29.md=79e38015366c3bd2/12246B | 0 | `'PASS\r\n'` | `d938fa189912f8776c3deb31a6bec42f403f57b9c8e3ed936bdb076caf6bd61c` | PASS |
| ABC_WORDA | `"C:\Users\Administrator\AppData\Local\Programs\Python\Python312\python.exe" -I -X utf8 "D:\Project\ra2-campaign-forge\lead\andk_rerun_20261109\sandbox\d29\abc_B_WA\check_d29_WA.py"` | `4650148729c01e24aec33d3ae3f349ca09209c8ccb21a0d45a4390c7f97a809e` / 3897 | FACTCHECK.md=0661f666bc4af56c/12647B; RULING_D29.md=79e38015366c3bd2/12246B | 0 | `'PASS\r\n'` | `d938fa189912f8776c3deb31a6bec42f403f57b9c8e3ed936bdb076caf6bd61c` | PASS |
| ABC_WORDB | `"C:\Users\Administrator\AppData\Local\Programs\Python\Python312\python.exe" -I -X utf8 "D:\Project\ra2-campaign-forge\lead\andk_rerun_20261109\sandbox\d29\abc_B_WB\check_d29_WB.py"` | `9863b52d296a43013dd7d10f5ff3a08acdcd0312aea26c7f55a03de6a5ec9575` / 3897 | FACTCHECK.md=0661f666bc4af56c/12647B; RULING_D29.md=79e38015366c3bd2/12246B | 1 | `'[4] Section 冲突是否成立: body must contain 前提\r\nFAIL (content)\r\n'` | `df76c6494aa22800029d762702c6b4ed4888555d7496a6c2c0b302c06ceb5c90` | FAIL |
| ABC_SENTINEL | `"C:\Users\Administrator\AppData\Local\Programs\Python\Python312\python.exe" -I -X utf8 "D:\Project\ra2-campaign-forge\lead\andk_rerun_20261109\sandbox\d29\abc_B_SENT\check_d29_SENT.py"` | `8d7609c121801d3ccea4587051a816a9fc4334abdfe8045b942f65b16489d852` / 3925 | FACTCHECK.md=0661f666bc4af56c/12647B; RULING_D29.md=79e38015366c3bd2/12246B | 1 | `'[4] Section 冲突是否成立: body must contain TOTALLY_BROKEN_NEEDLE_SENTINEL_XYZ\r\nFAIL (content)\r\n'` | `303d40567f5e597437d31e3b80258826934b5ee6c2c8b8d650cd258a0f0d4d6f` | FAIL |

  CWD = `D:\Project\ra2-campaign-forge\lead\andk_rerun_20261109\sandbox\d29\abc_B`；布局 = 同目录：脚本=<root>/check_dNN.py；输入=<root>/RULING_DNN.md + <root>/FACTCHECK.md；directory=__file__.parent=<root>

**输入 C**：从 RULING_D29.md 全文删除两根针 '互斥'(5 处) 与 '前提'(2 处)

| 口径 | CMD (绝对路径) | 被核脚本 SHA256 / 字节 | 输入 SHA256 / 字节 | EXIT | STDOUT 原文 | stdout_sha256 | 判定 |
|---|---|---|---|---|---|---|---|
| ABC_ORIGINAL | `"C:\Users\Administrator\AppData\Local\Programs\Python\Python312\python.exe" -I -X utf8 "D:\Project\ra2-campaign-forge\lead\andk_rerun_20261109\sandbox\d29\abc_C\check_d29_BASE.py"` | `2a50b09adff555dbce4c5740a2af78b779876cad771b6fdf887ba3c0dc780f14` / 3906 | FACTCHECK.md=0661f666bc4af56c/12647B; RULING_D29.md=63c6433188928aa0/12216B | 1 | `'[4] Section 冲突是否成立: body must contain 互斥 OR 前提\r\nFAIL (content)\r\n'` | `c59fc4894d063773b853f1b7228aee1e4a42aa245696b253a76c3afe330f4ce1` | FAIL |
| ABC_WORDA | `"C:\Users\Administrator\AppData\Local\Programs\Python\Python312\python.exe" -I -X utf8 "D:\Project\ra2-campaign-forge\lead\andk_rerun_20261109\sandbox\d29\abc_C_WA\check_d29_WA.py"` | `4650148729c01e24aec33d3ae3f349ca09209c8ccb21a0d45a4390c7f97a809e` / 3897 | FACTCHECK.md=0661f666bc4af56c/12647B; RULING_D29.md=63c6433188928aa0/12216B | 1 | `'[4] Section 冲突是否成立: body must contain 互斥\r\nFAIL (content)\r\n'` | `1f8ad2dbc255ce41167f522eb2ec0a885f1c9b5ba348e646d8a80d5b0c79d22a` | FAIL |
| ABC_WORDB | `"C:\Users\Administrator\AppData\Local\Programs\Python\Python312\python.exe" -I -X utf8 "D:\Project\ra2-campaign-forge\lead\andk_rerun_20261109\sandbox\d29\abc_C_WB\check_d29_WB.py"` | `9863b52d296a43013dd7d10f5ff3a08acdcd0312aea26c7f55a03de6a5ec9575` / 3897 | FACTCHECK.md=0661f666bc4af56c/12647B; RULING_D29.md=63c6433188928aa0/12216B | 1 | `'[4] Section 冲突是否成立: body must contain 前提\r\nFAIL (content)\r\n'` | `df76c6494aa22800029d762702c6b4ed4888555d7496a6c2c0b302c06ceb5c90` | FAIL |
| ABC_SENTINEL | `"C:\Users\Administrator\AppData\Local\Programs\Python\Python312\python.exe" -I -X utf8 "D:\Project\ra2-campaign-forge\lead\andk_rerun_20261109\sandbox\d29\abc_C_SENT\check_d29_SENT.py"` | `8d7609c121801d3ccea4587051a816a9fc4334abdfe8045b942f65b16489d852` / 3925 | FACTCHECK.md=0661f666bc4af56c/12647B; RULING_D29.md=63c6433188928aa0/12216B | 1 | `'[4] Section 冲突是否成立: body must contain TOTALLY_BROKEN_NEEDLE_SENTINEL_XYZ\r\nFAIL (content)\r\n'` | `303d40567f5e597437d31e3b80258826934b5ee6c2c8b8d650cd258a0f0d4d6f` | FAIL |

  CWD = `D:\Project\ra2-campaign-forge\lead\andk_rerun_20261109\sandbox\d29\abc_C`；布局 = 同目录：脚本=<root>/check_dNN.py；输入=<root>/RULING_DNN.md + <root>/FACTCHECK.md；directory=__file__.parent=<root>

### d30

**输入 A**：未改：两词都在，输入文档为原件逐字节副本

| 口径 | CMD (绝对路径) | 被核脚本 SHA256 / 字节 | 输入 SHA256 / 字节 | EXIT | STDOUT 原文 | stdout_sha256 | 判定 |
|---|---|---|---|---|---|---|---|
| ABC_ORIGINAL | `"C:\Users\Administrator\AppData\Local\Programs\Python\Python312\python.exe" -I -X utf8 "D:\Project\ra2-campaign-forge\lead\andk_rerun_20261109\sandbox\d30\abc_A\check_d30_BASE.py"` | `6cb737963fc62a0e045f51247b4fa57ef190acb0b524da3aa6b7713fd05ee9fd` / 3926 | FACTCHECK.md=2981848eec1b16b0/11394B; RULING_D30.md=d5afc90c50bbf57b/13197B | 0 | `'PASS\r\n'` | `d938fa189912f8776c3deb31a6bec42f403f57b9c8e3ed936bdb076caf6bd61c` | PASS |
| ABC_WORDA | `"C:\Users\Administrator\AppData\Local\Programs\Python\Python312\python.exe" -I -X utf8 "D:\Project\ra2-campaign-forge\lead\andk_rerun_20261109\sandbox\d30\abc_A_WA\check_d30_WA.py"` | `b42ae93c2709d9dc1e28df00347b3093efaf92d3ecef410c97951d2d4f55fb6c` / 3914 | FACTCHECK.md=2981848eec1b16b0/11394B; RULING_D30.md=d5afc90c50bbf57b/13197B | 0 | `'PASS\r\n'` | `d938fa189912f8776c3deb31a6bec42f403f57b9c8e3ed936bdb076caf6bd61c` | PASS |
| ABC_WORDB | `"C:\Users\Administrator\AppData\Local\Programs\Python\Python312\python.exe" -I -X utf8 "D:\Project\ra2-campaign-forge\lead\andk_rerun_20261109\sandbox\d30\abc_A_WB\check_d30_WB.py"` | `358b0e5fc535443a4a26b975c64f9b4ad9e89a0672b24da004fcbb560cf65b81` / 3918 | FACTCHECK.md=2981848eec1b16b0/11394B; RULING_D30.md=d5afc90c50bbf57b/13197B | 0 | `'PASS\r\n'` | `d938fa189912f8776c3deb31a6bec42f403f57b9c8e3ed936bdb076caf6bd61c` | PASS |
| ABC_SENTINEL | `"C:\Users\Administrator\AppData\Local\Programs\Python\Python312\python.exe" -I -X utf8 "D:\Project\ra2-campaign-forge\lead\andk_rerun_20261109\sandbox\d30\abc_A_SENT\check_d30_SENT.py"` | `1a2a4dd04dafdbd18484a2980f3e1518e10ddb57de31dc2e45f980a26c562990` / 3943 | FACTCHECK.md=2981848eec1b16b0/11394B; RULING_D30.md=d5afc90c50bbf57b/13197B | 1 | `'[4] Section 三档权衡的实质: body must contain TOTALLY_BROKEN_NEEDLE_SENTINEL_XYZ\r\nFAIL (content)\r\n'` | `5843202d6f2cd63538cb0c822cf73979f5172002692ddaddd9206beefabaa5b0` | FAIL |

  CWD = `D:\Project\ra2-campaign-forge\lead\andk_rerun_20261109\sandbox\d30\abc_A`；布局 = 同目录：脚本=<root>/check_dNN.py；输入=<root>/RULING_DNN.md + <root>/FACTCHECK.md；directory=__file__.parent=<root>

**输入 B**：从 RULING_D30.md 全文删除第二根针 '误报率'（3 处）；第一根针 '93.98' 保留

| 口径 | CMD (绝对路径) | 被核脚本 SHA256 / 字节 | 输入 SHA256 / 字节 | EXIT | STDOUT 原文 | stdout_sha256 | 判定 |
|---|---|---|---|---|---|---|---|
| ABC_ORIGINAL | `"C:\Users\Administrator\AppData\Local\Programs\Python\Python312\python.exe" -I -X utf8 "D:\Project\ra2-campaign-forge\lead\andk_rerun_20261109\sandbox\d30\abc_B\check_d30_BASE.py"` | `6cb737963fc62a0e045f51247b4fa57ef190acb0b524da3aa6b7713fd05ee9fd` / 3926 | FACTCHECK.md=2981848eec1b16b0/11394B; RULING_D30.md=1677ae79ac8bf19b/13170B | 0 | `'PASS\r\n'` | `d938fa189912f8776c3deb31a6bec42f403f57b9c8e3ed936bdb076caf6bd61c` | PASS |
| ABC_WORDA | `"C:\Users\Administrator\AppData\Local\Programs\Python\Python312\python.exe" -I -X utf8 "D:\Project\ra2-campaign-forge\lead\andk_rerun_20261109\sandbox\d30\abc_B_WA\check_d30_WA.py"` | `b42ae93c2709d9dc1e28df00347b3093efaf92d3ecef410c97951d2d4f55fb6c` / 3914 | FACTCHECK.md=2981848eec1b16b0/11394B; RULING_D30.md=1677ae79ac8bf19b/13170B | 0 | `'PASS\r\n'` | `d938fa189912f8776c3deb31a6bec42f403f57b9c8e3ed936bdb076caf6bd61c` | PASS |
| ABC_WORDB | `"C:\Users\Administrator\AppData\Local\Programs\Python\Python312\python.exe" -I -X utf8 "D:\Project\ra2-campaign-forge\lead\andk_rerun_20261109\sandbox\d30\abc_B_WB\check_d30_WB.py"` | `358b0e5fc535443a4a26b975c64f9b4ad9e89a0672b24da004fcbb560cf65b81` / 3918 | FACTCHECK.md=2981848eec1b16b0/11394B; RULING_D30.md=1677ae79ac8bf19b/13170B | 1 | `'[4] Section 三档权衡的实质: body must contain 误报率\r\nFAIL (content)\r\n'` | `dd3770d90bdf1674ed42aacaa25e3400f2322dcb8ded331e1f1db65fe8f29b55` | FAIL |
| ABC_SENTINEL | `"C:\Users\Administrator\AppData\Local\Programs\Python\Python312\python.exe" -I -X utf8 "D:\Project\ra2-campaign-forge\lead\andk_rerun_20261109\sandbox\d30\abc_B_SENT\check_d30_SENT.py"` | `1a2a4dd04dafdbd18484a2980f3e1518e10ddb57de31dc2e45f980a26c562990` / 3943 | FACTCHECK.md=2981848eec1b16b0/11394B; RULING_D30.md=1677ae79ac8bf19b/13170B | 1 | `'[4] Section 三档权衡的实质: body must contain TOTALLY_BROKEN_NEEDLE_SENTINEL_XYZ\r\nFAIL (content)\r\n'` | `5843202d6f2cd63538cb0c822cf73979f5172002692ddaddd9206beefabaa5b0` | FAIL |

  CWD = `D:\Project\ra2-campaign-forge\lead\andk_rerun_20261109\sandbox\d30\abc_B`；布局 = 同目录：脚本=<root>/check_dNN.py；输入=<root>/RULING_DNN.md + <root>/FACTCHECK.md；directory=__file__.parent=<root>

**输入 C**：从 RULING_D30.md 全文删除两根针 '93.98'(3 处) 与 '误报率'(3 处)

| 口径 | CMD (绝对路径) | 被核脚本 SHA256 / 字节 | 输入 SHA256 / 字节 | EXIT | STDOUT 原文 | stdout_sha256 | 判定 |
|---|---|---|---|---|---|---|---|
| ABC_ORIGINAL | `"C:\Users\Administrator\AppData\Local\Programs\Python\Python312\python.exe" -I -X utf8 "D:\Project\ra2-campaign-forge\lead\andk_rerun_20261109\sandbox\d30\abc_C\check_d30_BASE.py"` | `6cb737963fc62a0e045f51247b4fa57ef190acb0b524da3aa6b7713fd05ee9fd` / 3926 | FACTCHECK.md=2981848eec1b16b0/11394B; RULING_D30.md=b623fcdd1d575d35/13155B | 1 | `'[4] Section 三档权衡的实质: body must contain 93.98 OR 误报率\r\nFAIL (content)\r\n'` | `7b82a1923f6bd8e701ce6ea493ff0efff0259f360dab108ee2267a6d7f4d4ac1` | FAIL |
| ABC_WORDA | `"C:\Users\Administrator\AppData\Local\Programs\Python\Python312\python.exe" -I -X utf8 "D:\Project\ra2-campaign-forge\lead\andk_rerun_20261109\sandbox\d30\abc_C_WA\check_d30_WA.py"` | `b42ae93c2709d9dc1e28df00347b3093efaf92d3ecef410c97951d2d4f55fb6c` / 3914 | FACTCHECK.md=2981848eec1b16b0/11394B; RULING_D30.md=b623fcdd1d575d35/13155B | 1 | `'[4] Section 三档权衡的实质: body must contain 93.98\r\nFAIL (content)\r\n'` | `8ed28b12fb3df6376f8f4c29654ab8f924908816258bc39e7233456f94414a12` | FAIL |
| ABC_WORDB | `"C:\Users\Administrator\AppData\Local\Programs\Python\Python312\python.exe" -I -X utf8 "D:\Project\ra2-campaign-forge\lead\andk_rerun_20261109\sandbox\d30\abc_C_WB\check_d30_WB.py"` | `358b0e5fc535443a4a26b975c64f9b4ad9e89a0672b24da004fcbb560cf65b81` / 3918 | FACTCHECK.md=2981848eec1b16b0/11394B; RULING_D30.md=b623fcdd1d575d35/13155B | 1 | `'[4] Section 三档权衡的实质: body must contain 误报率\r\nFAIL (content)\r\n'` | `dd3770d90bdf1674ed42aacaa25e3400f2322dcb8ded331e1f1db65fe8f29b55` | FAIL |
| ABC_SENTINEL | `"C:\Users\Administrator\AppData\Local\Programs\Python\Python312\python.exe" -I -X utf8 "D:\Project\ra2-campaign-forge\lead\andk_rerun_20261109\sandbox\d30\abc_C_SENT\check_d30_SENT.py"` | `1a2a4dd04dafdbd18484a2980f3e1518e10ddb57de31dc2e45f980a26c562990` / 3943 | FACTCHECK.md=2981848eec1b16b0/11394B; RULING_D30.md=b623fcdd1d575d35/13155B | 1 | `'[4] Section 三档权衡的实质: body must contain TOTALLY_BROKEN_NEEDLE_SENTINEL_XYZ\r\nFAIL (content)\r\n'` | `5843202d6f2cd63538cb0c822cf73979f5172002692ddaddd9206beefabaa5b0` | FAIL |

  CWD = `D:\Project\ra2-campaign-forge\lead\andk_rerun_20261109\sandbox\d30\abc_C`；布局 = 同目录：脚本=<root>/check_dNN.py；输入=<root>/RULING_DNN.md + <root>/FACTCHECK.md；directory=__file__.parent=<root>

## 3 上游口径：12 份沙箱副本在原件输入上的 AND_k（k=2 真实逐词运行）

| gate | WA EXIT/STDOUT | WB EXIT/STDOUT | p=[P_WA,P_WB] | AGGREGATE=AND_2 | SENT EXIT | BAD_NEEDLE_CAUGHT | DISTINGUISHABLE_PASS |
|---|---|---|---|---|---|---|---|
| d27 | 0 / `'PASS: D-27 八项机械检查通过；裁决书引用 71 处\r\n'` | 0 / `'PASS: D-27 八项机械检查通过；裁决书引用 71 处\r\n'` | [True, True] | **True** | 1 | True | True |
| d28 | 0 / `'PASS: D-28 全部 8 项机械检查通过 (exit 0)\r\n'` | 0 / `'PASS: D-28 全部 8 项机械检查通过 (exit 0)\r\n'` | [True, True] | **True** | 1 | True | True |
| d29 | 0 / `'PASS\r\n'` | 0 / `'PASS\r\n'` | [True, True] | **True** | 1 | True | True |
| d30 | 0 / `'PASS\r\n'` | 0 / `'PASS\r\n'` | [True, True] | **True** | 1 | True | True |

**重要限定**：这一行的 `DISTINGUISHABLE_PASS=True` 只证明「把 OR 元组换成单元素后的两份**改写脚本副本**」各能独立过，不证明「**原件**的 exit=0」有逐输入内容。原件仍是 `any(present)` 一次聚合。

