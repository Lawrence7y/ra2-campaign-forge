# B2B_DESIGN_REVIEW.md · 独立设计复核件

**复核员**：B2b 设计复核员（新上下文，独立复核）。**日期**：2026-11-06。
**被核对象**：`lead/b2b_design_20261106/B2B_DESIGN.md` 与 `lead/b2b_design_20261106/STATE_MATRIX.json`。
**探针**：`lead/b2b_design_20261106/_b2b_probe.py` / `_b2b_probe_out.txt`。
**写域**：只写 `lead/b2b_design_20261106/review/B2B_DESIGN_REVIEW.md`（唯一写域内）；母本、只读域一字未改；零真机、零采样、不 commit / 不 push；Python 全部 `python -I -X utf8` + 绝对路径。

---

## 0 复核结论（机器可读字段）

```
subjectSha256: 565771d8b31c516dc7a1e0100ea047484406a203390492df9f57170a6532feaf
subjectBytes: 66735
checkedEveryRow: true
hunksMatchManifest: true
earlyReturnsCovered: 5/5
unknownToHigh: false
```

指纹实算命令（本机无 `sha256sum` / `wc`，用 `hashlib`）：

```
python -I -X utf8 -c "import hashlib;d=open(r'D:\Project\ra2-campaign-forge\lead\b2b_design_20261106\B2B_DESIGN.md','rb').read();print(hashlib.sha256(d).hexdigest(),len(d))"
```

输出：`565771d8b31c516dc7a1e0100ea047484406a203390492df9f57170a6532feaf 66735`
（`B2B_DESIGN.md` 全文 693 行；`splitlines` 结果与 `ls -la` 的 66,735 B 一致。）

**三项专项判定**：专项一 PASS（9 == 9）／专项二 PASS（0 条 `unknown → high`）／专项三 PASS（5/5）。逐 hunk 行号锚点 9/9 原文命中。探针重跑输出逐字节一致。无阻断问题，`issues` 为空。

---

## 1 前置：指纹与母本基线

用 `python -I -X utf8 -c "import hashlib,sys;for p in sys.argv[1:]:d=open(p,'rb').read();print(hashlib.sha256(d).hexdigest(),len(d),len(d.splitlines()),p)" <5 个绝对路径>` 实算：

| 文件 | SHA256 | 字节 | 行 |
|:--|:--|--:|--:|
| `B2B_DESIGN.md` | `565771d8b31c516dc7a1e0100ea047484406a203390492df9f57170a6532feaf` | 66735 | 693 |
| `STATE_MATRIX.json` | `1d4ccc937cfa78f1ac5144c15fd3e87152e45d41565bf5031bde53202667e016` | 3558 | 16 |
| `_b2b_probe.py` | `48b70fd69ed0330778c5717ab5bb79276c833b1c657164569225728cf8199564` | 13329 | 342 |
| `_b2b_probe_out.txt`（跑前） | `9334460bf394b398f5ac7ef1fd0f183523b4a8c7a3177590e16ea5686fe097a1` | 10811 | 182 |
| 母本 `qc151_trip.py` | `517889c68f037ab63f9c38300e627d34457b7be9fab0362e425783c7ec5ba636` | 399508 | 7291 |

母本指纹与 `TASK.md:21`、`B2B_DESIGN.md:24/:31` 头部一致，与探针输出 `_b2b_probe_out.txt:5-7` 一致 ⇒ 母本未漂移，行号锚点可用。复核结束时重算母本仍为 `517889c6… / 399508`（见 §6 回套命令末尾输出），**母本一个字节未改**。

---

## 2 逐项 1：逐个 hunk 的行号锚点核对（不抽样，9/9 全核）

**方法**：用 `python -I -X utf8` 内嵌脚本解析 `B2B_DESIGN.md`，正则 `^@@ -(\d+),(\d+) \+(\d+),(\d+) @@` 抓全部 hunk 头，取每个 hunk 体内所有「上下文行 + `-` 行」组成 minus 侧，按 hunk 头 `-起始,行数` 从起始行开始**逐行**与母本 `splitlines()` 的 1-based 原文比对；同时核对 minus 侧行数 == 声明的 `B`、plus 侧行数 == 声明的 `D`。

命中的 9 个 `@@` 头（设计文件行号 → 头）：

| # | 设计行 | hunk 头 | minus 侧行数 / 声明 B | plus 侧行数 / 声明 D | 逐行原文不符数 |
|:--|--:|:--|:--|:--|--:|
| H01 | `B2B_DESIGN.md:205` | `@@ -212,6 +212,21 @@` | 6 / 6 | 21 / 21 | 0 |
| H02 | `B2B_DESIGN.md:230` | `@@ -4458,6 +4473,10 @@` | 6 / 6 | 10 / 10 | 0 |
| H03 | `B2B_DESIGN.md:244` | `@@ -4558,8 +4577,131 @@` | 8 / 8 | 131 / 131 | 0 |
| H04 | `B2B_DESIGN.md:380` | `@@ -4572,20 +4714,105 @@` | 20 / 20 | 105 / 105 | 0 |
| H05 | `B2B_DESIGN.md:498` | `@@ -5906,7 +6133,8 @@` | 7 / 7 | 8 / 8 | 0 |
| H06 | `B2B_DESIGN.md:511` | `@@ -5936,7 +6164,8 @@` | 7 / 7 | 8 / 8 | 0 |
| H07 | `B2B_DESIGN.md:524` | `@@ -6294,6 +6523,9 @@` | 6 / 6 | 9 / 9 | 0 |
| H08 | `B2B_DESIGN.md:537` | `@@ -6386,6 +6618,15 @@` | 6 / 6 | 15 / 15 | 0 |
| H09 | `B2B_DESIGN.md:556` | `@@ -7122,7 +7363,8 @@` | 7 / 7 | 8 / 8 | 0 |

命令输出尾部：`=== TOTAL ISSUES: 0`。**9 个 hunk、共 73 条 minus 侧行，逐行与母本原文相等，0 处对不上**。

**§7 各行宣称的母本锚点原文**（另跑一段 `python -I -X utf8` 打印，逐条追到「文件:行」）：

| 清单行 | 宣称锚点 | 母本原文（实读） |
|:--|:--|:--|
| H01 | `:214` 后插常量 | `qc151_trip.py:214` = `                 "ra2opt_play.bat", "except.txt")` |
| H02 | `:4460` 后 | `qc151_trip.py:4460` = `        bak[name] = {"path": str(dst), "size": dst.stat().st_size, "sha256": h}` |
| H03 | `:4561` 前 / def `:4561-4562` | `qc151_trip.py:4561` = `def copy_post_except_evidence(rec: Recorder, carrier_dir: Path,` |
| H04 | `:4574-4599` 函数体 | `qc151_trip.py:4574` = `    src = carrier_dir / "except.txt"`；`:4583-4586` 为 5 键 `info`（探针 `[9]`） |
| H05 | `:5909` 签名 | `qc151_trip.py:5909` = `                  created_receipt: dict | None = None) -> int:` |
| H06 | `:5939` 唯一调用点 | `qc151_trip.py:5939` = `        copy_post_except_evidence(rec, carrier_dir, out_dir)` |
| H07 | `:6296` 后 / `:6313 try` 前 | `qc151_trip.py:6296` = `    pre_except_txt = None`；`:6313` = `    try:`；`:6387` = `        bak = backup_carrier(rec, carrier_dir)` |
| H08 | `:6388` 后 | `qc151_trip.py:6388` = `        budget.end_stage("backup")` |
| H09 | `:7125` 后 / `:7117` 调用 | `qc151_trip.py:7125` = `                created_receipt=(TRIP_CARRIER.get("receipt") or created_receipt))`；`:7117` = `            FINALIZE_CODE[0] = finalize_trip(` |

**回套可应用性补验**（`python -I -X utf8` 内嵌脚本）：按 9 个 hunk 自底向上替换回母本副本，输出 `HUNKS_APPLIED: 9`、`APPLIED_LINES: 7533 MOTHER_LINES: 7291`、`ast.parse(applied) = PASS`；`if not setdiff.get("no_new_exception", True):` 在母本与套用后各 1 处，`def except_set_diff` 各 1 处（E 判据块未被 9 个 hunk 改动）。此为内存操作，未写出任何候选 `.py`。

**结论**：`checkedEveryRow: true` —— 每个 hunk 的行号锚点都逐行打开母本核过，不是抽样；对不上 ⇒ 记 issues，实际 0 条。

---

## 3 逐项 2：亲自重跑探针并核输出一致

**命令**（`python -I -X utf8`，参数即脚本绝对路径，按 `_b2b_probe.py:6` 的用法）：

```
python -I -X utf8 D:\Project\ra2-campaign-forge\lead\b2b_design_20261106\_b2b_probe.py
```

**实跑输出**（复核脚本以 `subprocess.run` 捕获，未改探针、未改门禁）：

```
BEFORE sha256: 9334460bf394b398f5ac7ef1fd0f183523b4a8c7a3177590e16ea5686fe097a1
BEFORE bytes: 10811 splitlines: 182
RUN CMD: C:\Users\Administrator\AppData\Local\Programs\Python\Python312\python.exe -I -X utf8 D:\Project\ra2-campaign-forge\lead\b2b_design_20261106\_b2b_probe.py
RETURNCODE: 0
STDERR: ''
AFTER  sha256: 9334460bf394b398f5ac7ef1fd0f183523b4a8c7a3177590e16ea5686fe097a1
AFTER  bytes: 10811 splitlines: 182
FILE_BYTE_IDENTICAL_BEFORE_AFTER: True
STDOUT bytes: 10940
PROBE_TRAILER: ['[PROBE] 输出已写入: D:\\Project\\ra2-campaign-forge\\lead\\b2b_design_20261106\\_b2b_probe_out.txt', '[PROBE] 输出行数: 182']
STDOUT_STARTS_WITH_FILE_TEXT: True
STDOUT_LINES_EQ_FILE_LINES: True
OUTPUT_MATCH: True
```

- 探针 `exitCode = 0`，`stderr` 空，官方尾行 `[PROBE] 输出行数: 182`（`_b2b_probe.py:338`）。
- 探针写出的 `_b2b_probe_out.txt` 跑前 / 跑后 **SHA256 完全相同**（`9334460b…`），10811 B / 182 行不变 ⇒ 与交付的 `_b2b_probe_out.txt` 逐字节一致。
- 同时核 `stdout` 前缀与文件文本逐行相等（`STDOUT_STARTS_WITH_FILE_TEXT: True` / `STDOUT_LINES_EQ_FILE_LINES: True`）；`stdout` 比文件多出的 129 B 仅为探针自己 `print` 的两条 `[PROBE]` 尾行，属预期（`_b2b_probe.py:336-338`）。
- 探针头部实算母本 `sha256=517889c6… / 399508 B / 7291 行`（`_b2b_probe_out.txt:4-7`）与 §1 实算一致；`[5]` 列出 main 顶层 10 个 return、其中 5 个标 `[早于 6387]`（`_b2b_probe_out.txt:66-77`），供专项三对照。

**结论**：输出一致，PASS。

---

## 4 专项一：改动清单条数 == `@@` hunk 条数

**命令**（`python -I -X utf8` 内嵌脚本，切 `## 7`..`## 8` 段落，正则 `^\|\s*H\d+` 数数据行；全文正则 `^@@ ` 数 hunk 行）：

```
## 7 数据行(Hxx): 9
全文 '^@@ ' 行数: 9
清单数据行 == @@ 行数 : True => 9 vs 9
```

- §7（`B2B_DESIGN.md:656-670`）数据行 H01–H09 共 **9** 行，逐行打印其「对应 hunk」列与 §4 的 9 个头一一对应：H01→`-212,6 +212,21`、H02→`-4458,6 +4473,10`、H03→`-4558,8 +4577,131`、H04→`-4572,20 +4714,105`、H05→`-5906,7 +6133,8`、H06→`-5936,7 +6164,8`、H07→`-6294,6 +6523,9`、H08→`-6386,6 +6618,15`、H09→`-7122,7 +7363,8`。
- 全文以 `@@ ` 开头的行恰 **9** 行（`B2B_DESIGN.md:205/230/244/380/498/511/524/537/556`），无第 10 个、无遗漏。
- 9 == 9 ⇒ **`hunksMatchManifest: true`**。

---

## 5 专项二：状态矩阵 `unknown → high`

**命令**（`python -I -X utf8` 内嵌脚本，`json.loads` 读 `STATE_MATRIX.json`，逐项打印 `state / preState / verdict / confidence` 并扫 `state=='unknown' & confidence=='high'`；另扫 §2 markdown 表）：

```
STATE_MATRIX.json 项数: 14
  [ 1] state=unknown                 preState=unknown           verdict=unknown                conf=none
  [ 2] state=unknown                 preState=unknown           verdict=unknown                conf=none
  [ 3] state=error                   preState=error             verdict=error_pre_snapshot     conf=none
  [ 4] state=post_read_error         preState=present           verdict=post_read_error        conf=none
  [ 5] state=absent_confirmed        preState=absent_confirmed  verdict=new_first_appearance   conf=high
  [ 6] state=absent_both             preState=absent_confirmed  verdict=absent_both            conf=low
  [ 7] state=leftover_unchanged      preState=present           verdict=leftover_unchanged     conf=high
  [ 8] state=leftover_unchanged      preState=present           verdict=leftover_unchanged     conf=medium
  [ 9] state=new_write               preState=present           verdict=new_write              conf=high
  [10] state=rewritten_same_content  preState=present           verdict=rewritten_same_content conf=medium
  [11] state=rewritten_same_content  preState=present           verdict=rewritten_same_content conf=low
  [12] state=missing_sha             preState=present           verdict=error_pre_snapshot     conf=none
  [13] state=missing_sha             preState=present           verdict=post_read_error        conf=none
  [14] state=vanished                preState=present           verdict=vanished               conf=none
unknown->high 行数: 0
## 2 markdown 里含 unknown 且含 high 的行: 0
```

- 两条 `state=unknown`（`STATE_MATRIX.json:2-3`）置信均为 `none`；`high` 只出现在 `absent_confirmed`（第 5 行）、`leftover_unchanged` mtime 齐全（第 7 行）、`new_write`（第 9 行），均非 unknown。
- 加严口径（把 `preState=='unknown'` 或 `verdict=='unknown'` 也算「unknown 行」）复扫仍为 0 条命中 high。
- §2 markdown 表（`B2B_DESIGN.md:146-161`）14 行与 `STATE_MATRIX.json` 14 项**逐行**核 `state / preState / verdict / confidence`：不一致数 0。
- ⇒ **`unknownToHigh: false`**。

**附带核对（非缺陷，登记备查）**：`B2B_DESIGN.md:646` 引 `verify` 输出 `STATE_MATRIX.json 行数 = 12`，而交付的 `STATE_MATRIX.json` 为 14 项。实读 `_draft_semantics_check.py:586/:596/:602` 得知该 `verify` 的计数对象是 `_draft_semantics.md` §2 内嵌 ```json 块（实算 12 项）；设计在 `B2B_DESIGN.md:685-686` 已明示「`verify` 检查对象是 `_draft_semantics.md`，不是本稿」。故 12 指的是草稿内嵌块，不是交付矩阵，**不构成清单/矩阵不一致**，不列入 issues。

---

## 6 专项三：五个早退路径覆盖

**方法**（`python -I -X utf8` 内嵌脚本）：不照抄探针结论，用 `ast.parse` 独立从母本取 `main` 顶层 `return`（跳嵌套函数/类），取 `< 6387`（快照构造点，母本 `:6387` = `bak = backup_carrier(...)`，设计 H08 在 `:6388` 后构造快照）的早退；再在 §3（`B2B_DESIGN.md:172-194`）表格中逐行查 `:行号` 命中。

```
母本 main 顶层 return: [6340, 6349, 6361, 6374, 6377, 6445, 6478, 6496, 7021, 7029]
早于快照构造点 6387 的早退: [6340, 6349, 6361, 6374, 6377] 共 5
## 3 表格数据行(Pxx): 11
  早退 :6340  -> §3 命中行数=1  PASS   (P1, B2B_DESIGN.md:179)
  早退 :6349  -> §3 命中行数=1  PASS   (P2, B2B_DESIGN.md:180)
  早退 :6361  -> §3 命中行数=1  PASS   (P3, B2B_DESIGN.md:181)
  早退 :6374  -> §3 命中行数=1  PASS   (P4, B2B_DESIGN.md:182)
  早退 :6377  -> §3 命中行数=1  PASS   (P5, B2B_DESIGN.md:183)
earlyReturnsCovered = 5/5
```

- 5 个早退与 `TASK.md:36/:68`、`B2B_DESIGN.md:58`、探针 `_b2b_probe_out.txt:68-72` 完全一致；每个都恰有 1 行对应（P1–P5），且每行给出 `snapshotValue / finalizeReceives / outputVerdict / crashes` 四列结论。
- §3 另含 P6（try 内抛异常）、P7a/P7b（finally `:7048..7116` 失败两段）、P8（正常路径）、P9（其余 4 个 return）、P10（复制失败），共 11 行数据 ≥ `TASK.md:88` 要求的 7 行。
- ⇒ **`earlyReturnsCovered: 5/5`**。

---

## 7 issues 与其它说明

**issues**：`[]`（无）。三项专项全 PASS，逐 hunk 行号锚点 9/9 命中，探针重跑逐字节一致，回套 `ast.parse` PASS，母本指纹复核前后不变。

**如实登记的边界（非缺陷，不做补造）**：

1. 本复核**只做静态核对**：逐行原文比对、AST 独立取 return、`json` 解析、hunk 内存回套 + `ast.parse`。按铁律 1「零真机」，未运行 `qc151_trip.py` 本体、未启动任何游戏进程；§3 表中「不会崩 / 不进退出码」等运行时结论由设计方以结构性论证给出（`B2B_DESIGN.md:175/:652/:676`），本复核**未做运行时复现**，不把静态通过冒充运行时通过。
2. 复核范围内未运行 `_draft_semantics_check.py` 的 `verify` 作为判定依据（其对象是草稿，非本稿，见 §5）；本复核的三项专项均为**本会话亲自另跑**的独立脚本，命令与输出见 §2–§6。
3. `TASK.md:121-130` 的 `check_b2b.py` 门禁不在本次复核授权范围内（`B2B_DESIGN.md:685-686` 记其不存在）；本复核未创建、未运行、未修改任何门禁脚本。
4. `subjectSha256` / `subjectBytes` 仅对 `B2B_DESIGN.md` 实算；`STATE_MATRIX.json` 的指纹另列于 §1 表格，供对照。

---

## 8 实跑命令清单（全部 `python -I -X utf8` + 绝对路径）

| # | 用途 | 命令 / 形式 | 结果 |
|:--|:--|:--|:--|
| 1 | 五个文件指纹 | `python -I -X utf8 -c "import hashlib,sys;for p in sys.argv[1:]:..." <5 路径>` | 见 §1 |
| 2 | 重跑探针 | `python -I -X utf8 D:\Project\ra2-campaign-forge\lead\b2b_design_20261106\_b2b_probe.py` | `exit 0`，输出逐字节一致 |
| 3 | 逐 hunk 行号锚点 | `python -I -X utf8 - <<'PY' … 解析 @@ 头 + 逐行比母本 … PY` | `TOTAL ISSUES: 0`，9/9 |
| 4 | 专项一 / 二 / 三 + 锚点原文 | `python -I -X utf8 - <<'PY' … PY` | `9 vs 9` / `0` / `5/5` |
| 5 | §7 锚点 + §2↔JSON 逐行 | `python -I -X utf8 - <<'PY' … PY` | 不一致数 0 / 14==14 |
| 6 | 草稿 §2 内嵌块计数 | `python -I -X utf8 - <<'PY' … PY` | 草稿 12 / 交付 14（见 §5） |
| 7 | 9 hunk 回套 + `ast.parse` | `python -I -X utf8 - <<'PY' … PY` | `HUNKS_APPLIED: 9` / `PASS` / 母本 `517889c6… 399508` 未变 |
| 8 | 复核件指纹 | `python -I -X utf8 -c "import hashlib;d=open(<B2B_DESIGN.md>,'rb').read();print(...)"` | `565771d8… 66735` |
