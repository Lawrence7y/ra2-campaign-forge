# _ak_REPORT.md — P0-2 甲' 外壳重跑：四件 PASS 在逐输入口径下还剩什么

日期 2026-11-09；执行者 = 动态工作流子代理「ANDk重跑执行员」；零真机、零采样代码、不 commit、不 push。
唯一写域 = `lead/andk_rerun_20261109/`（本任务新建）。所有副本、注入、输出均在此目录 `sandbox/` 下。
本任务**没有**修改、追加或覆盖任何绝对只读文件；纪律清单见 §7。

---

## 0 一句话结论

**四件的 `exit=0` 在甲' 逐输入口径下都不是「8 项 × 逐输入全过」的实质通过**：四件各有一项
（`check_d27.py:84` / `check_d28.py:90` / `check_d29.py:76` / `check_d30.py:76`）是
`any(present)` 的二词 OR，杀掉其中一根针后仍 PASS、输出逐字不变。8 个编号项逐项注射坏针**全部**被抓（8/8 非零退出，
含 OR 项「两词全删」），但额外加的「OR 项只杀一根针」四件全部漏抓（`AND_9=False`）
⇒ 判 **「部分空转」**：其余 7 项真的在工作，那一项 OR 在逐输入口径下半工作。不是「形式通过」（不是任一项都可单独通过），也不是「实质通过」。

---

## 1 被核对象绑定行（复核回件固定格式，题给【铁律】）

四件门禁脚本（依次对应 `check_d27.py` / `check_d28.py` / `check_d29.py` / `check_d30.py`），
跑前/跑后均用 `hashlib.sha256` 与编排方基线逐一对齐（`_ak_guard_before.json` /
`_ak_guard_after.json`，212 个只读文件全量快照，`diff = 0`）：

```
被核对象 SHA256 = 3b769d7c64c2725100186439725198dbc134a277914e2cb2e9b0af844fe7671c，字节数 = 3764
被核对象 SHA256 = 5b42a34a40046d7a705776002d7aebe8ffda34248849a75b628d40712d9df268，字节数 = 4539
被核对象 SHA256 = 2a50b09adff555dbce4c5740a2af78b779876cad771b6fdf887ba3c0dc780f14，字节数 = 3906
被核对象 SHA256 = 6cb737963fc62a0e045f51247b4fa57ef190acb0b524da3aa6b7713fd05ee9fd，字节数 = 3926
```

两件台账与上游清点件（依次为 `PENDING_DECISIONS.md` / `GOAL_THREE_TARGETS_20261018.md` /
`STALE_PASS_INVENTORY.md`；同批复核，均未变）：

```
被核对象 SHA256 = 3765eddbe96deeb65eeb1f05dc81e1dc171e7ea3b2c826e2692a1d15e1c8f2d7，字节数 = 52419
被核对象 SHA256 = 2baa0de45d4125549262eb595d7518c9ce99efeee120384bf640cded8a933ede，字节数 = 759518
被核对象 SHA256 = a72d79b23b1329207a2c612d4244dec407ffaa4e0b91c397c3febb7a9cddd798，字节数 = 63656
```

输入文档（8 份，逐字节副本）的 SHA256 + 字节数绑定逐次运行记录在 `_ak_runs.jsonl` 的
`inputs` 字段；四件 `RULING` / `FACTCHECK` 值与题给【编排方实跑：基线指纹】全等。
**每次跑完复核原件 SHA256 未变**：`_ak_full_console.txt:2`
`ORIGINALS_UNCHANGED_AFTER_EVERY_RUN = True`（108 次运行逐次复核，非抽样）；
`_ak_full_console.txt:3` `READONLY_SNAPSHOT_DIFF = 0`（212 文件 / 7,695,927 B 前后全等）。

---

## 2 第一步：可部署甲' 外壳（本任务主要工程）

### 2(a) 交付物与实跑命令

| 文件 | 作用 |
|---|---|
| `_ak_shell.py` | 可粘贴/可部署外壳：`--mode full` 生成→落盘→驱动；`--mode selftest` 正控/负控自检 |
| `_ak_tables.py` | 从 `_ak_runs.jsonl` 生成三张表（只读本写域产物） |
| `_ak_selftest_out.txt` | 自检完整输出 |
| `_ak_full_console.txt` | 全量驱动 stdout |
| `_ak_runs.jsonl` | **108 次真实独立运行**的逐次记录（命令全文 / EXIT / STDOUT / stdout_sha256 / 脚本与输入指纹 / 原件未变复核） |
| `_ak_summary.json` | 汇总判定表、矩阵、复现、布局、12 份副本清单 |
| `_ak_twelve.json` / `_ak_twelve_out.txt` | 12 份沙箱副本的完整落点与 SHA256 |
| `_ak_layout_out.txt` | 三套路径布局方案 + 基线 EXIT/STDOUT |
| `_ak_abc_out.txt` | A/B/C 三次完整输出、退出码、指纹、AND_k 实算 |
| `_ak_PER_INPUT_TABLE.md` | 逐输入判定表（含命令全文与 stdout_sha256） |
| `_ak_BAD_NEEDLE_MATRIX.md` | 坏针哨兵全矩阵 |
| `_ak_REPRO.md` | 与上游 `STALE_PASS_INVENTORY.md:94-101` 对齐 |
| `_ak_guard_before.json` / `_ak_guard_after.json` | 绝对只读域 212 文件全量 SHA256+字节数快照 |

实跑命令（本会话，仓库根 `D:/Project/ra2-campaign-forge`）：

```
python -I -X utf8 "D:/Project/ra2-campaign-forge/lead/andk_rerun_20261109/_ak_shell.py" --mode selftest
  -> SELF_TEST = PASS ; 正控 好输入 EXIT=0 PASS ; 负控 缺文件 EXIT=2 FAIL ; 加控 OR 双删 EXIT=1 FAIL ; EXIT=0
     （见 _ak_selftest_out.txt）

python -I -X utf8 "D:/Project/ra2-campaign-forge/lead/andk_rerun_20261109/_ak_shell.py" --mode full > ".../_ak_full_console.txt" 2>&1
  -> EXIT=0 ; TOTAL_RUNS = 108 ; ORIGINALS_UNCHANGED_AFTER_EVERY_RUN = True ; READONLY_SNAPSHOT_DIFF = 0
     （见 _ak_full_console.txt:1-7）

python -I -X utf8 "D:/Project/ra2-campaign-forge/lead/andk_rerun_20261109/_ak_tables.py"
  -> WROTE 3 tables ; EXIT=0
```

Python = `3.12.10`（`_ak_summary.json:python`）；全部 `python -I -X utf8` + 绝对路径；
指纹一律 `hashlib.sha256`。外壳**不运行原件**：它把原件 `.read_bytes()` 后写到写域沙箱再
`subprocess.run([sys.executable,"-I","-X","utf8", <副本绝对路径>], cwd=..., capture_output=True)`。

### 2(b) ★ 三套路径布局：显式、逐件不同、可复现

源码依据（本会话逐行实读）：`check_d27.py:8`、`check_d28.py:54-55`、
`check_d29.py:50`、`check_d30.py:50`；题给【背景】与 `STALE_PASS_INVENTORY.md:255,258` 同述。

令 `R_<exp> = <写域>/sandbox/<gate>/<exp>/`（每次实验一个全新空目录，`shutil.rmtree` 后重建）：

| 件 | 源码解析 | 副本脚本落点 | 输入文档落点 | CWD | 为什么这样放 |
|---|---|---|---|---|---|
| **d27** | `DIRECTORY = Path("lead/d27_ruling_20261106")` **CWD 相对** | `R/check_d27_*.py` | `R/lead/d27_ruling_20261106/{RULING_D27.md,FACTCHECK.md}` | `R` | `Path("lead/d27_ruling_20261106")` 相对 `cwd=R` 恰好命中 `R/lead/d27_ruling_20261106`。**不能**从仓库根跑副本，否则读到只读原件。 |
| **d28** | `root = __file__.resolve().parents[2]`；`directory = root/"lead"/"d28_ruling_20261106"` | `R/a/b/check_d28_*.py` | `R/lead/d28_ruling_20261106/{RULING_D28.md,FACTCHECK.md}` | `R` | 脚本在 `R/a/b/` ⇒ `parents[2] = R` ⇒ 拼出 `R/lead/d28_ruling_20261106`。**深度必须正好 3 层**；放 `R/a/` 会让 `parents[2]` 指到 `<写域>/sandbox/d28/<exp>/..` 之外 ⇒ `EXIT=2`。这正是 `STALE_PASS_INVENTORY.md:255` 记「漏此点得 6 个 EXIT=2 作废」的坑。 |
| **d29** | `directory = __file__.resolve().parent` | `R/check_d29_*.py` | `R/{RULING_D29.md,FACTCHECK.md}`（**同目录**） | `R` | `parent = R`，输入必须在脚本旁边。 |
| **d30** | `directory = __file__.resolve().parent` | `R/check_d30_*.py` | `R/{RULING_D30.md,FACTCHECK.md}`（**同目录**） | `R` | 同 d29。 |

`_ak_layout_out.txt` 逐件给出 `script_dir / input_dir / cwd / note` 与本件基线 EXIT/STDOUT；
`_ak_shell.py` 的 `Layout` 类把四件落点写成显式分支（不是一个模板硬套四件）。

### 2(c) ★ 基线（未改的原件逐字节副本，逐输入）→ 四件全 PASS

`_ak_full_console.txt:4-7`：

| 件 | 基线 CMD（绝对路径，见 `_ak_runs.jsonl` / `_ak_summary.json:baseline`） | EXIT | STDOUT |
|---|---|---|---|
| d27 | `python -I -X utf8 ".../sandbox/d27/baseline/check_d27_BASE.py"` (cwd=该 baseline 目录) | 0 | `PASS: D-27 八项机械检查通过；裁决书引用 71 处` |
| d28 | `.../sandbox/d28/baseline/a/b/check_d28_BASE.py` | 0 | `PASS: D-28 全部 8 项机械检查通过 (exit 0)` |
| d29 | `.../sandbox/d29/baseline/check_d29_BASE.py` | 0 | `PASS` |
| d30 | `.../sandbox/d30/baseline/check_d30_BASE.py` | 0 | `PASS` |

四件基线脚本 SHA256/字节数与 §1 四个绑定行全等（即确为原件逐字节副本）。
没有出现路径错/输入缺 ⇒ 无需停下。

### 2(d) 12 份沙箱副本（生成→落盘→驱动序列完整）

`_ak_shell.py:main_full()` 序列：① `snapshot_all()` 只读域全量指纹 → ② 逐件按 `Layout` 建
`twelve/` 目录 → ③ 逐字节写两份输入 → ④ 对 `WA/WB/SENT` 三个变体分别把 OR 元组替换为
单元素词表并落盘（12 份）→ ⑤ 逐份 `subprocess.run` 真实驱动 → ⑥ 每次跑完 `verify_originals()`。
12 份副本路径与 SHA256 全列在 `_ak_twelve_out.txt`；驱动结果在 `_ak_summary.json:twelve_runs`。
与上游 `_sp_andk.py:7-15`（`STALE_PASS_INVENTORY.md:268` 自认「演示外壳、非可部署门禁」）的差别：
本外壳**自带生成步骤**，清空 `sandbox/` 后单条命令即可重建并跑完，不依赖任何预生成文件。

### 2(e) 外壳自检

`_ak_selftest_out.txt`（实跑 `EXIT=0`）：
- 正控（好输入）：d29 `BASE` + 两份原件输入 ⇒ `EXIT=0` / `PASS`。
- 负控（缺文件）：同一副本删 `FACTCHECK.md` ⇒ `EXIT=2` / `[1] Missing file: ...` + `FAIL (missing files)`。
- 加控（OR 双删）：删 `互斥`+`前提` ⇒ `EXIT=1` / `[4] Section 冲突是否成立: body must contain 互斥 OR 前提`。
`SELF_TEST = PASS`。三次运行的 `originals_unchanged` 均为 True。

---

## 3 第二步：逐输入独立跑 + 显式 AND_k

### 3(a) A/B/C 三次完整输出与退出码

输入定义（注射只在写域副本的 `RULING_D##.md` 上做，`FACTCHECK.md` 保持原件副本）：

| input | 定义 | d27 | d28 | d29 | d30 |
|---|---|---|---|---|---|
| **A** | 原 RULING，两词都在 | 外推 + 卡顿不存在 | 历史数字 + 1681 | 互斥 + 前提 | 93.98 + 误报率 |
| **B** | 删掉**第二**根针 | 删「卡顿不存在」 | 删「1681」 | 删「前提」 | 删「误报率」 |
| **C** | 两词**都**删 | 删两词 | 删两词 | 删两词 | 删两词 |

每个 input 各跑 4 次：原件副本 `BASE`、逐词副本 `WA`（只查第一词）、`WB`（只查第二词）、
`SENT`（只查保证零命中的 `TOTALLY_BROKEN_NEEDLE_SENTINEL_XYZ`）。
**完整输出、退出码、命令全文、脚本/输入 SHA256、stdout_sha256** 逐行列在
`_ak_PER_INPUT_TABLE.md` §2 与 `_ak_abc_out.txt`；以下为判定摘要（全部来自实跑）：

| 件 | input | 原件 `BASE` | WA | WB | SENT |
|---|---|---|---|---|---|
| d27 | A | EXIT=0 `PASS: D-27 八项机械检查通过；裁决书引用 71 处` | 0 PASS | 0 PASS | 1 `FAIL [6] 未背书小节正文须包含: TOTALLY_BROKEN_NEEDLE_SENTINEL_XYZ` |
| d27 | B | **EXIT=0 同 A，逐字不变** | 0 PASS | **1** `FAIL [6] … 须包含: 卡顿不存在` | 1 FAIL |
| d27 | C | 1 `FAIL [6] … 须包含: 外推 或 卡顿不存在` | 1 FAIL | 1 FAIL | 1 FAIL |
| d28 | A | EXIT=0 `PASS: D-28 全部 8 项机械检查通过 (exit 0)` | 0 PASS | 0 PASS | 1 `FAIL [4] … 至少包含其一：SENTINEL` |
| d28 | B | **EXIT=0 同 A，逐字不变** | 0 PASS | **1** `FAIL [4] … 至少包含其一：1681` | 1 FAIL |
| d28 | C | 1 `FAIL [4] … 历史数字、1681` | 1 FAIL | 1 FAIL | 1 FAIL |
| d29 | A | EXIT=0 `PASS` | 0 PASS | 0 PASS | 1 `[4] … TOTALLY_BROKEN…` + `FAIL (content)` |
| d29 | B | **EXIT=0 同 A，逐字不变** | 0 PASS | **1** `[4] … 前提` + `FAIL (content)` | 1 FAIL |
| d29 | C | 1 `[4] … 互斥 OR 前提` + `FAIL` | 1 FAIL | 1 FAIL | 1 FAIL |
| d30 | A | EXIT=0 `PASS` | 0 PASS | 0 PASS | 1 `[4] … TOTALLY_BROKEN…` + `FAIL (content)` |
| d30 | B | **EXIT=0 同 A，逐字不变** | 0 PASS | **1** `[4] … 误报率` + `FAIL (content)` | 1 FAIL |
| d30 | C | 1 `[4] … 93.98 OR 误报率` + `FAIL` | 1 FAIL | 1 FAIL | 1 FAIL |

**读法**：B 输入下原件 `any(present)` 仍 PASS（第一根针单独就够 ⇒ 第二根针是死的）；
但把「k 个输入」拆成两次真实独立运行后，WB 那次必 FAIL ⇒ `AND_k=False`。C 输入证明这一项
并非完全没工作（两词都删即 FAIL），但它是 **OR 而非 AND**。

### 3(b) ★ 显式 AND_k 与 DISTINGUISHABLE_PASS

公式（`_ak_PER_INPUT_TABLE.md` 公式段，来自 `_ak_shell.py:main_full` 实算）：

```
P_WA(input)  = [逐词副本 WA 在该 input 上 EXIT=0 ∧ 输出含 PASS ∧ 无 FAIL]
P_WB(input)  = [逐词副本 WB 在该 input 上 EXIT=0 ∧ 输出含 PASS ∧ 无 FAIL]
AGGREGATE    = AND_k(P_WA, P_WB)   with k = 2   （两次真实独立运行，非推断）
BAD_NEEDLE_CAUGHT = [SENT 副本在该 input 上 EXIT≠0 ∧ verdict=FAIL]
DISTINGUISHABLE_PASS = AGGREGATE ∧ BAD_NEEDLE_CAUGHT
```

实算值（`_ak_summary.json:abc`，12 行全表见 `_ak_PER_INPUT_TABLE.md` §1）：

| gate | input | 原件 `any(present)` | P_WA | P_WB | `AGGREGATE = AND_k` | SENT EXIT | BAD_NEEDLE_CAUGHT | `DISTINGUISHABLE_PASS` |
|---|---|---|---|---|---|---|---|---|
| d27 | A | PASS (0) | True | True | **True** | 1 | True | **True** |
| d27 | B | PASS (0) | True | False | **False** | 1 | True | **False** |
| d27 | C | FAIL (1) | False | False | **False** | 1 | True | False |
| d28 | A | PASS (0) | True | True | **True** | 1 | True | **True** |
| d28 | B | PASS (0) | True | False | **False** | 1 | True | **False** |
| d28 | C | FAIL (1) | False | False | **False** | 1 | True | False |
| d29 | A | PASS (0) | True | True | **True** | 1 | True | **True** |
| d29 | B | PASS (0) | True | False | **False** | 1 | True | **False** |
| d29 | C | FAIL (1) | False | False | **False** | 1 | True | False |
| d30 | A | PASS (0) | True | True | **True** | 1 | True | **True** |
| d30 | B | PASS (0) | True | False | **False** | 1 | True | **False** |
| d30 | C | FAIL (1) | False | False | **False** | 1 | True | False |

`DISTINGUISHABLE_PASS` 语义（题给 `STALE_PASS_INVENTORY.md:202-211` / `:253`）：每个输入都被
**单独**验证过，而不是一个总 PASS。本实跑：**只在 A 输入为 True**；B 输入下四件全 False。

**上游口径的 12 份副本结果**（`_ak_summary.json:per_word`，`_ak_PER_INPUT_TABLE.md` §3）：
四件均 `k=2, p=[True,True], AGGREGATE=AND_2=True, BAD_NEEDLE_CAUGHT=True,
DISTINGUISHABLE_PASS=True` —— 与 `STALE_PASS_INVENTORY.md:263` 的 4/4 演示一致。
★ **但这一行不能当门禁可信**：它证明的是「把 OR 元组改成单元素后的两份**改写脚本副本**」
各能独立过，**原件的 `exit=0` 仍是 `any(present)` 一次聚合**，从未被改写。
题给【铁律】「不得把演示外壳跑通当成门禁可信」在此按字面遵守。

### 3(c) 对照表：原件 `any(present)` 与外壳 `AND_k` 的判定差异

| 件 × input | 原件一次运行 `any(present)` | 外壳 `AND_k`（2 次真实运行） | 差异 |
|---|---|---|---|
| 四件 × A | PASS / EXIT=0 | PASS / True | 无差异（两词都在，任何口径都过） |
| 四件 × B（杀第二根针） | **PASS / EXIT=0，输出逐字不变** | **FAIL / False** | **实质差异**：原件看不见死输入，外壳看得见 |
| 四件 × C（两词全删） | FAIL / EXIT=1 | FAIL / False | 无差异（这一项确实在工作，只是 OR 语义） |

差异根因：`check_d27.py:86-87` / `check_d28.py:96-97` / `check_d29.py:82-87` /
`check_d30.py:82-87` 用 `any(...)`（或 `any(matches)`）把 k 个词折成一个布尔；
`AND_k` 要求 k 次真实运行各自 `EXIT=0`。B 输入下 `any([True,False])=True` 而
`AND_2(True,False)=False`。

---

## 4 第三步：坏针哨兵全矩阵

### 4(a)(b) 件 × 项 × {注入前 / 注入后 / 是否被抓}

完整 36 行矩阵（4 件 × 9 行）、每行注射动作、注入后 STDOUT 原文与 CMD 见
`_ak_BAD_NEEDLE_MATRIX.md` / `_ak_matrix_out.txt` / `_ak_summary.json:matrix`。
判据：`是否被抓 = 注入后 EXIT≠0 ∧ verdict=FAIL`（`_ak_shell.py:main_full`）。
注射一律在**写域副本输入文档**上做；被核脚本一律 BASE（原件逐字节副本，SHA256 见 §1）。

| 件 | 项 | 注射动作 | 注入前 | 注入后 | 是否被抓 |
|---|---|---|---|---|---|
| d27 | [1] | 删 `FACTCHECK.md` | PASS (0) | FAIL (2) | ✔ |
| d27 | [2] | `main: B` → `main: NEEDLE_DELETED` | PASS (0) | FAIL (1) | ✔ |
| d27 | [3] | `## 7 诚实账` 标题改名 | PASS (0) | FAIL (1) | ✔ |
| d27 | [4] | 删「循环论证」 | PASS (0) | FAIL (1) | ✔ |
| d27 | [5] | 删「本次不授权」 | PASS (0) | FAIL (1) | ✔ |
| d27 | [6] | OR 两词全删 | PASS (0) | FAIL (1) | ✔ |
| **d27** | **[6b]** | **OR 项只杀一根针（删「卡顿不存在」）** | PASS (0) | **PASS (0)** | **✘ 漏抓** |
| d27 | [7] | 71 处 `file:line` 行号改非数字 | PASS (0) | FAIL (1) | ✔ |
| d27 | [8] | FACTCHECK 删 `selfBias` | PASS (0) | FAIL (1) | ✔ |
| d28 | [1] | 删 `FACTCHECK.md` | PASS (0) | FAIL (2) | ✔ |
| d28 | [2] | `q1/q2` 声明行改坏 | PASS (0) | FAIL (1) | ✔ |
| d28 | [3] | `## 7 诚实账` 标题改名 | PASS (0) | FAIL (1) | ✔ |
| d28 | [4] | OR 两词全删 | PASS (0) | FAIL (1) | ✔ |
| **d28** | **[4b]** | **OR 项只杀一根针（删「1681」）** | PASS (0) | **PASS (0)** | **✘ 漏抓** |
| d28 | [5] | 删「本次不授权」 | PASS (0) | FAIL (1) | ✔ |
| d28 | [6] | 删 AND 词表里的「外推」 | PASS (0) | FAIL (1) | ✔ |
| d28 | [7] | 69 处引用行号改非数字 | PASS (0) | FAIL (1) | ✔ |
| d28 | [8] | FACTCHECK 删 `selfBias` | PASS (0) | FAIL (1) | ✔ |
| d29 | [1] | 删 `FACTCHECK.md` | PASS (0) | FAIL (2) | ✔ |
| d29 | [2] | `q1` 声明行改坏 | PASS (0) | FAIL (1) | ✔ |
| d29 | [3] | `## 7 诚实账` 标题改名 | PASS (0) | FAIL (1) | ✔ |
| d29 | [4] | OR 两词全删 | PASS (0) | FAIL (1) | ✔ |
| **d29** | **[4b]** | **OR 项只杀一根针（删「前提」）** | PASS (0) | **PASS (0)** | **✘ 漏抓** |
| d29 | [5] | 删「本次不授权」 | PASS (0) | FAIL (1) | ✔ |
| d29 | [6] | 删 AND 词表里的「外推」 | PASS (0) | FAIL (1) | ✔ |
| d29 | [7] | 52 处引用行号改非数字 | PASS (0) | FAIL (1) | ✔ |
| d29 | [8] | FACTCHECK 删 `selfBias` | PASS (0) | FAIL (1) | ✔ |
| d30 | [1] | 删 `FACTCHECK.md` | PASS (0) | FAIL (2) | ✔ |
| d30 | [2] | `q1` 声明行改坏 | PASS (0) | FAIL (1) | ✔ |
| d30 | [3] | `## 7 诚实账` 标题改名 | PASS (0) | FAIL (1) | ✔ |
| d30 | [4] | OR 两词全删 | PASS (0) | FAIL (1) | ✔ |
| **d30** | **[4b]** | **OR 项只杀一根针（删「误报率」）** | PASS (0) | **PASS (0)** | **✘ 漏抓** |
| d30 | [5] | 删「本次不授权」 | PASS (0) | FAIL (1) | ✔ |
| d30 | [6] | 删 AND 词表里的「外推」 | PASS (0) | FAIL (1) | ✔ |
| d30 | [7] | 51 处引用行号改非数字 | PASS (0) | FAIL (1) | ✔ |
| d30 | [8] | FACTCHECK 删 `selfBias` | PASS (0) | FAIL (1) | ✔ |

| 件 | `AND_8`（8 个编号项） | `AND_9`（含「只杀一根针」） | 抓到 | 漏抓 |
|---|---|---|---|---|
| d27 | True | **False** | 8/9 | [6b] |
| d28 | True | **False** | 8/9 | [4b] |
| d29 | True | **False** | 8/9 | [4b] |
| d30 | True | **False** | 8/9 | [4b] |

**任何一格「注入后仍 PASS」都是实质缺陷**：四件各 1 格（共 4 格），全部落在那一项 OR 上。

### 4(c) ★ 7 项「单一字面量」在逐输入口径下能不能被抓到

能，四件 **8/8 全被抓**（`AND_8=True`）。逐项源码机理：

- d27 `[4]` `("循环论证",)` / `[5]` `("本次不授权",)`：`check_d27.py:81-88` 的
  `any(keyword in body ... for keyword in keywords)` 在单元素词表上退化为「该词必须在」，
  删词即 `[4]`/`[5]` FAIL（`_ak_matrix_out.txt` d27 段）。
- d28 `[5]` `require_all=True` + 单元素、`[6]` `require_all=True` + 三元素 AND：
  `check_d28.py:91-92,94-99` `all(present)`，删「本次不授权」或「外推」即 FAIL。
- d29/d30 `[5]` 单元素 AND、`[6]` 三元素 AND：`check_d29.py:77-89` /
  `check_d30.py:77-89` 的 `all(word in body for word in words)` + `any(matches)`，删词即 FAIL。
- `[1]/[2]/[3]/[7]/[8]` 是存在性/正则/计数检查，同样各自被抓。

⇒ **本实跑没有发现「某一项删掉字面量仍 PASS」的情况**；唯一空转的是 OR 项里的第二根针。
这与题给【背景】「其余 7 项是单一字面量/小节存在性」一致，也与
`STALE_PASS_INVENTORY.md:117` 的 A 级判据（「检验本身经坏输入注射实证失效」）对齐：
失效面精确等于那一项 `any()`，不是整把尺子全坏。

---

## 5 第四步：判这四件的 PASS 还剩什么

### 5(a) 逐件结论

| 件 | 甲' 口径下的 PASS | 判据（本会话实跑） |
|---|---|---|
| **d27** | **部分空转**：8 项里 7 项真的在工作，第 [6] 项 `("外推","卡顿不存在")` 是 OR，杀「卡顿不存在」仍 PASS / 输出逐字不变 | `_ak_BAD_NEEDLE_MATRIX.md` d27 行：`AND_8=True / AND_9=False`；`_ak_REPRO.md` d27 |
| **d28** | **部分空转**：同上，第 [4] 项 `("历史数字","1681")` OR，杀「1681」仍 PASS | `check_d28.py:90` `require_all=False`；矩阵 `AND_8=True / AND_9=False` |
| **d29** | **部分空转**：第 [4] 项 `("互斥","前提")` OR，杀「前提」仍 PASS | `check_d29.py:76`；矩阵 `AND_8=True / AND_9=False` |
| **d30** | **部分空转**：第 [4] 项 `("93.98","误报率")` OR，杀「误报率」仍 PASS | `check_d30.py:76`；矩阵 `AND_8=True / AND_9=False` |

**不是**「实质通过」（B 输入下 `AND_k=False`、`DISTINGUISHABLE_PASS=False`），
**也不是**「形式通过 / 任一项都可单独通过」（`AND_8=True`：删任何一项的必需字面量都会 FAIL）。
按题给三档措辞：**四件均为「8 项里只有若干项真的在工作」= 部分空转**（7/8 项工作，1 项半工作）。

**出口分支复核**（题给【背景】）：`check_d27.py:99-101,107` `return 1 / return 0 / sys.exit(main())`；
`check_d28.py:109-116` / `check_d29.py:101-106` / `check_d30.py:101-106` 三路 `return 2/1/0`。
本实跑确实观测到三种出口：基线 `EXIT=0`、内容注射 `EXIT=1`、缺文件 `EXIT=2`
（`_ak_BAD_NEEDLE_MATRIX.md` [1] 行）⇒ `EXIT=0` 在这四件里**有内容**，
其内容是「8 项全过，但其中一项是 `any(present)` 的二词 OR」，不是「任一针命中即过整个门禁」。

### 5(b) ★ 与上游注射实证对齐：`STALE_PASS_INVENTORY.md:94-101`

上游实证（本会话 `Read` 实读 `:94-101`）：`_sp_4gate_compare.py` 实跑 `EXIT=0`，
四组 `BASE → INJ` 输出逐字一致、`EXIT=0/0`。
本任务在外壳里**按上游口径复刻**（只把脚本副本里第二根针换成哨兵，OR 结构不变、输入原件副本）：

| 件 | BASE EXIT / STDOUT | INJ EXIT / STDOUT | 逐字一致 | stdout_sha256 一致 | 能否复现 |
|---|---|---|---|---|---|
| d27 | 0 / `PASS: D-27 八项机械检查通过；裁决书引用 71 处` | 0 / 同左 | True | True | **能** |
| d28 | 0 / `PASS: D-28 全部 8 项机械检查通过 (exit 0)` | 0 / 同左 | True | True | **能** |
| d29 | 0 / `PASS` | 0 / 同左 | True | True | **能** |
| d30 | 0 / `PASS` | 0 / 同左 | True | True | **能** |

注射副本 SHA256（与上游 `:98-101` 登记 INJ 前缀逐字符相符）：
d27 `f404f58783ab4da0…7d7af89` / d28 `f5ae184c…4692314` /
d29 `2399e95a43eaafa4…580ced5` / d30 `b1670537e12a6d7c…9a7129`（完整 64 位见 `_ak_REPRO.md`）。
**差异原因**：上游注射改的是**脚本词表**里的一个词、输入保持不变 ⇒ 另一根针在输入里仍命中，
`any(present)` 必然仍 PASS；本任务 B 输入改的是**输入文档**里的那根针，再配 `AND_k` 逐词副本，
WB 那次必 FAIL。两者是同一 OR 塌缩的两个观测面，不矛盾。
逐件「能否复现」= **4/4 能**，无差异件。

### 5(c) ★ 重跑之后 `PENDING:92/105/117/129` 四行「exit=0」应改成什么措辞

四行原文（本会话 `Read` 实读 `lead/PENDING_DECISIONS.md:92,105,117,129`）：
`:92`「…门禁 `check_d30.py` 实跑 **exit=0**（2026-11-07 复跑仍 PASS）。」；
`:105`「…门禁 `check_d29.py` 实跑 **exit=0**。」；
`:117`「…门禁 `check_d28.py` 实跑 **exit=0**。」；
`:129`「…门禁 `check_d27.py` 实跑 **exit=0**。」

应改成：**保留历史 `exit=0` 事实，但明确它只是「一次 `any()` 聚合的格式/机械检查」，
不得再以「已验证 / 逐项通过」身份被引用；按 `STALE_PASS_INVENTORY.md:117` 加注
`UNTRUSTWORTHY`，并指向本次甲' 重跑登记。** 可直接粘贴的加注文本（**本任务不真的加注**，
两件台账绝对只读，由 Leader 执行）：

```
★【2026-11-09 甲' 重跑加注 · 由 Leader 登记】本行原「门禁 check_d30.py 实跑 exit=0」仅为
历史事实，指一次「8 项格式/机械检查」的单次聚合运行；其中第 4 项
check_d30.py:76 (4, "三档权衡的实质", ("93.98", "误报率"), False) 为 any(present) 二词 OR。
2026-11-09 实跑（lead/andk_rerun_20261109/_ak_REPORT.md）：杀掉「误报率」后原件仍
EXIT=0、stdout 逐字不变；逐输入 AND_k(k=2) 在 B 输入 = FALSE、DISTINGUISHABLE_PASS = FALSE；
8 个编号项坏针注射 8/8 被抓，但「OR 项只杀一根针」漏抓 ⇒ AND_9 = FALSE。
结论：该 PASS 判为「部分空转（7/8 项工作，1 项 OR 半工作）」，标记 UNTRUSTWORTHY；
不得以「已验证 / 逐项通过 / 全绿」身份沿引用链放大，亦不改写或删除本行历史数字。
本加注只涉形式要件的证据资格，不重审、不推翻 D-30 实质裁决（DETECT_TRIAGE.md:162）。
```

```
★【2026-11-09 甲' 重跑加注 · 由 Leader 登记】本行原「门禁 check_d29.py 实跑 exit=0」仅为
历史事实，指一次「8 项格式/机械检查」的单次聚合运行；其中第 4 项
check_d29.py:76 (4, "冲突是否成立", ("互斥", "前提"), False) 为 any(present) 二词 OR。
2026-11-09 实跑（lead/andk_rerun_20261109/_ak_REPORT.md）：杀掉「前提」后原件仍
EXIT=0、stdout 逐字不变；逐输入 AND_k(k=2) 在 B 输入 = FALSE、DISTINGUISHABLE_PASS = FALSE；
8 个编号项坏针注射 8/8 被抓，「OR 项只杀一根针」漏抓 ⇒ AND_9 = FALSE。
结论：该 PASS 判为「部分空转（7/8 项工作，1 项 OR 半工作）」，标记 UNTRUSTWORTHY；
不得以「已验证 / 逐项通过 / 全绿」身份沿引用链放大，亦不改写或删除本行历史数字。
本加注只涉形式要件的证据资格，不重审、不推翻 D-29 实质裁决（DETECT_TRIAGE.md:162）。
```

```
★【2026-11-09 甲' 重跑加注 · 由 Leader 登记】本行原「门禁 check_d28.py 实跑 exit=0」仅为
历史事实，指一次「8 项格式/机械检查」的单次聚合运行；其中第 4 项
check_d28.py:90 (4, "D 链处置", ("历史数字", "1681"), False) 为 any(present) 二词 OR。
2026-11-09 实跑（lead/andk_rerun_20261109/_ak_REPORT.md）：杀掉「1681」后原件仍
EXIT=0、stdout 逐字不变；逐输入 AND_k(k=2) 在 B 输入 = FALSE、DISTINGUISHABLE_PASS = FALSE；
8 个编号项坏针注射 8/8 被抓，「OR 项只杀一根针」漏抓 ⇒ AND_9 = FALSE。
结论：该 PASS 判为「部分空转（7/8 项工作，1 项 OR 半工作）」，标记 UNTRUSTWORTHY；
不得以「已验证 / 逐项通过 / 全绿」身份沿引用链放大，亦不改写或删除本行历史数字。
本加注只涉形式要件的证据资格，不重审、不推翻 D-28 实质裁决（DETECT_TRIAGE.md:162）。
```

```
★【2026-11-09 甲' 重跑加注 · 由 Leader 登记】本行原「门禁 check_d27.py 实跑 exit=0」仅为
历史事实，指一次「8 项格式/机械检查」的单次聚合运行；其中第 6 项
check_d27.py:84 (6, "未背书", ("外推", "卡顿不存在")) 为 any(keyword in body ...) 二词 OR。
2026-11-09 实跑（lead/andk_rerun_20261109/_ak_REPORT.md）：杀掉「卡顿不存在」后原件仍
EXIT=0、stdout 逐字不变；逐输入 AND_k(k=2) 在 B 输入 = FALSE、DISTINGUISHABLE_PASS = FALSE；
8 个编号项坏针注射 8/8 被抓，「OR 项只杀一根针」漏抓 ⇒ AND_9 = FALSE。
结论：该 PASS 判为「部分空转（7/8 项工作，1 项 OR 半工作）」，标记 UNTRUSTWORTHY；
不得以「已验证 / 逐项通过 / 全绿」身份沿引用链放大，亦不改写或删除本行历史数字。
本加注只涉形式要件的证据资格，不重审、不推翻 D-27 实质裁决（DETECT_TRIAGE.md:162）。
```

四段均按 `STALE_PASS_INVENTORY.md:249`（删行会破坏台账可追溯性）保留原行、只加注；
`UNTRUSTWORTHY` 措辞取自 `:115-117` A 级定义。

---

## 6 第五步：最小处置、可推广性、判不了什么

### 6(a) 四件各自需要改什么才能让 PASS 有内容（只给设计，**本任务不改原件**）

最小改动 = 把那一项从 OR 改成逐输入 AND，并让「每个词各自被单独验证」成为登记口径：

| 件 | 设计（不改原件，供 Leader 决策） |
|---|---|
| d27 | `check_d27.py:81-88` 对 `("外推","卡顿不存在")` 由 `any(...)` 改为要求**两词各自独立命中**（例如 `all(keyword in body ... for keyword in keywords)` 或拆成两次真实运行再 `AND_k`）；同时把「两词都删 / 只删一词」的负控写进自检，输出逐词 `input_i: PASS/FAIL`。 |
| d28 | `check_d28.py:90` 把 `(4, "D 链处置", ("历史数字","1681"), False)` 的 `require_all` 由 `False` 改 `True`（或等价地逐词跑 + AND_k）；`:98` 的提示语相应改「同时包含」。 |
| d29 | `check_d29.py:76` 把 `(4, "冲突是否成立", ("互斥","前提"), False)` 改 `True`；注意 `:82-87` 的 `any(matches)` 是「任一**小节副本**满足」，若同一标题有多个 body 仍须逐词独立验证，不能只翻一个布尔。 |
| d30 | `check_d30.py:76` 把 `(4, "三档权衡的实质", ("93.98","误报率"), False)` 改 `True`；同上处理 `any(matches)`。 |

共同要求（题给 `STALE_PASS_INVENTORY.md:257-261,388-399` 十条清单）：
① 每个词一根**真实独立运行**，`AGGREGATE = AND_k(rc==0 ∧ 含 PASS ∧ 无 FAIL)`；
② 每根针各换一次 `TOTALLY_BROKEN_NEEDLE_SENTINEL_XYZ`，要求 `AGGREGATE` 变 FAIL；
③ 输出 `input_i: PASS/FAIL` 逐行 + `DISTINGUISHABLE_PASS`；
④ 绑定「被核脚本 SHA256 + 字节数 + 逐输入文档 SHA256 + 字节数 + 命令全文 + stdout sha256」；
⑤ `HITSET / MASKED_LINES / EXCLUSIVE(k)` 只作诊断量，不得替代 `AND_k`；
⑥ 门禁/诊断分离；⑦ 单调性对照（若依赖 `min/argmin`；本四件不依赖）；⑧ 未验项逐条写「未验」。
`python -I -X utf8` + 绝对路径 + 三套路径布局（§2(b)）必须随改一并固化。

### 6(b) 这套外壳能否推广到其余「已引用 PASS」的件：可行性与成本

**可行性 = 部分可行，不能整体套用。**

- 对**同族**（`check_d*.py` 格式门禁、同类 OR 词表、同类三套路径布局）：本外壳的
  `Layout` / `script_bytes` / `make_docs` / `do_run` 可直接参数化复用，只需替换
  `GATES` 配置（源码路径、OR 元组、词表、声明正则、必需小节、引用正则）。
  分诊 `DETECT_TRIAGE.md:184` 记 `check_*.py` 全库 **173 件**、`_cf_filelist.txt` 三集合差为空；
  `STALE_PASS_INVENTORY.md:107` 记两账另约 **~170 行** PASS 类未逐条注射实证。
- 对**异质件**：`STALE_PASS_INVENTORY.md:245` 明记其余 ~170 行是「真机/编译/单测/工作流门槛/
  历史观测」异质混合；`DETECT_TRIAGE.md:179-180,190-192` 另点名
  `lead/refsync_scope_20261109/_rs_carrier_scan.py`（非 `check_` 前缀、`--needle` 参数、
  `min/argmin` 反向掩蔽、6 条负控、3 行 `REFSYNC_SCOPE_FIX.md:251-253` PASS）与
  `PENDING:162/186/199` 三行 C 级。这类件的「k 个输入」不是源码里的词表，而是命令行参数/
  语料文件/扫描目标 ⇒ 必须重定义 `k`、重写生成器与布局，**本外壳不能照搬**。
  且 `:267` 记「`--include-refuting` 口径陷阱」：照抄模板会引入第三套口径。

**成本（本会话实跑数据，非估算）**：本任务四件共 **108 次真实 subprocess 运行**
（12 份副本驱动 + 4 基线 + 48 次 A/B/C 逐词 + 8 次上游复现 + 36 次坏针矩阵），
`_ak_shell.py` 单条命令完成，控制台输出 854 B、逐次记录 197,059 B；另 1 次自检（3 运行）。
按此单位成本外推到 173 件同族门禁约 173/4 × 108 ≈ **4,671 次**只读执行（**此为线性外推、
未按单件实跑验证，记为估算**）；异质件另需逐件定义 k 与布局，成本**未验**。
`DETECT_TRIAGE.md:173` 记上游「约 10–30 分钟人工/脚本编排」是估算且本会话未计时 ⇒
本任务**不给秒数、不给异质件工时**。

### 6(c) ★ 这条工作判不了什么（如实列）

1. **判不了 D-27..D-30 实质结论的对错**。四件自述「格式/机械检查」
   （`check_d27.py:1` / `check_d28.py:1` / `check_d29.py:1` / `check_d30.py:1`），
   `DETECT_TRIAGE.md:162` 与 `STALE_PASS_INVENTORY.md:196,219-220` 明记「无任何数值/逻辑断言、
   形式要件失效 7 处而实质结论失效 0 处」。本任务只判 **PASS 的证据资格**。
2. **判不了其余 ~170 行 PASS 类、173 件 `check_*.py`、carrier scanner、以及
   `PENDING:162/186/199` 的可信性**：本任务只跑了题给的四件，其余**未验**
   （`STALE_PASS_INVENTORY.md:107` / `DETECT_TRIAGE.md:179-180`）。
3. **判不了 2026-11-06/11-07 那几次历史实跑的当时输入与口径**：本任务绑的是**当前盘**
   输入指纹（与题给【编排方实跑：基线指纹】全等）；`STALE_PASS_INVENTORY.md:139` 记输入未变，
   但本会话没有独立取证历史时点的文件字节 ⇒ 标「未验」。
4. **判不了「语义正确性」**：全部检查是字面量/正则/标题/计数，字在 ≠ 命题真；
   `check_d27.py:18` 的 `REFERENCE` 只数 `file:line` 形状，不校验引用是否真实存在或内容相符。
5. **判不了真机/运行时/性能/扰动**：零真机、零采样代码（题给铁律）；
   `PENDING:97` 自记 Q5 扰动 `verified=false`、4 项依赖全需真机 ⇒ 不在本任务范围内。
6. **判不了「改了之后会不会引入新问题」**：§6(a) 只给设计，未改原件、未跑修复后回归
   （`STALE_PASS_INVENTORY.md:268,361` 同记上游演示「未部署成门禁、未跑修复后回归」）。
7. **判不了 `AND_k=True` 就等于门禁可信**：`_ak_PER_INPUT_TABLE.md` §3 的 4/4
   `DISTINGUISHABLE_PASS=True` 来自**改写后的副本**；原件 `any(present)` 从未被改写
   （题给【铁律】「不得把演示外壳跑通当成门禁可信」）。
8. **判不了台账加注的执行**：两件台账绝对只读，本任务未加注、未 commit、未 push；
   §5(c) 文本仅供 Leader 粘贴（`STALE_PASS_INVENTORY.md:5,247,209`）。
9. **判不了「杀第一根针」的对称性**：本任务 B 输入按题给定义只删**第二**根针
   （四件各一次），未逐件删第一根针 ⇒ 第一根针是否同样致死**未验**。
   上游 `STALE_PASS_INVENTORY.md:98-101` 的注射实证也只覆盖第二根针。
10. **判不了 d29/d30 `any(matches)` 多 body 情形**：本会话前置统计命令
    `python -I -X utf8 -c "...统计 OR 词在目标小节内的出现次数并列出二级标题..."` 显示四份
    RULING 的受检标题各只出现 1 次（`HEADINGS` 列表无重名标题），但未构造「同标题多小节」
    输入做实跑 ⇒ 该分支**未验**。

---

## 7 纪律自证

- 零真机：未启动 `gamemd.exe` / `ra2loader` / `YURI.exe`，未 `taskkill`，未读活进程内存。
- 零采样代码：外壳只做 `pathlib` 读写副本、`subprocess.run` 跑纯文本检查脚本、`hashlib`；
  无 hook / MiniDump / SuspendThread / StackWalk / 探针注入 / 动态内存解析。
- ★ 绝对只读：两件台账、`lead/d2[7890]_ruling_20261106/`、`lead/stale_pass_20261109/`、
  `lead/k1bit_detect_20261109/`、`lead/detect_triage_20261109/`、`lead/refsync_scope_20261109/`
  一律未修改、未追加、未覆盖。`_ak_guard_before.json` 与 `_ak_guard_after.json` 的
  SHA256 均为 `e8a495465df09ab4f587f8067bc0b6def89970a7a711e81697653ae068e82d31`（212 文件全量
  指纹逐字节相同），`diff = 0`（`_ak_full_console.txt:3`）。
- 唯一写域：`lead/andk_rerun_20261109/`；`sandbox/` 下所有副本、注入、输出均在此。
- Python 一律 `python -I -X utf8` + 绝对路径；指纹用 `hashlib.sha256`。
- 不 commit、不 push（本会话未执行任何 `git` 写操作）。
- 产出前缀 `_ak_`。
