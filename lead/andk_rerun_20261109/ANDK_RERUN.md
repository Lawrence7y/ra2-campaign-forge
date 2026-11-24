# ANDK_RERUN.md — 甲' 外壳重跑成件：四件 PASS 在逐输入口径下还剩什么

日期 2026-11-09；撰写者 = 动态工作流子代理「ANDk成件撰写员」。依据 = 本会话实跑与实读（凡「实跑」均给出命令+输出，凡「实读」均给出 `文件:行`），以及编排方随任务下发的【执行】【复核】【交付】材料。
**铁律核对**：零真机（未启动 `gamemd.exe` / `ra2loader` / `YURI.exe`，未 `taskkill`，未读活进程内存）；零采样代码（本会话写的脚本只用 `pathlib` / `hashlib` / `json` / `subprocess` / `shutil` / `re` / `sys`）；两件台账与六个只读目录一律未修改、未追加、未覆盖；不 commit、不 push；Python 一律 `python -I -X utf8` + 绝对路径；指纹一律 `hashlib.sha256`。
**本成件自身只写 `lead/andk_rerun_20261109/ANDK_RERUN.md` 及同目录 `_writer_*` 辅助件**；未真的给台账加注。

---

## 1 目的与边界

### 1.1 目的（只重跑，不改原件）

本任务判的是：**`lead/PENDING_DECISIONS.md:92/105/117/129` 四行登记的「门禁 `check_dNN.py` 实跑 `exit=0`」，在甲' 逐输入口径下还剩什么证据资格**（题给【交付】「不得把演示外壳跑通当成门禁可信」）。四行原文我本会话实读（`PENDING_DECISIONS.md:92/105/117/129`）：`:92` 记 `check_d30.py`、`:105` 记 `check_d29.py`、`:117` 记 `check_d28.py`、`:129` 记 `check_d27.py`，均为「实跑 **exit=0**」；`:160` 上游分诊同述（`detect_triage_20261109/DETECT_TRIAGE.md:160`）。
被核对象 = 四件门禁脚本 `lead/d27_ruling_20261106/check_d27.py`、`lead/d28_ruling_20261106/check_d28.py`、`lead/d29_ruling_20261106/check_d29.py`、`lead/d30_ruling_20261106/check_d30.py`；各自输入 = 同目录 `RULING_D##.md` + `FACTCHECK.md`（逐字节副本，见 §2）。
**只重跑**：本会话未改四件门禁一个字节、未改八份输入文档一个字节、未改两件台账一个字节。注入全部发生在写域 `sandbox/` 的副本上；每次 `subprocess.run` 之后由 `_ak_shell.py:285` 调 `verify_originals(strict=True)`（`_ak_shell.py:115-128`）复核 15 件基线指纹。

### 1.2 写域（唯一）

- `lead/andk_rerun_20261109/` —— 唯一写域，本任务新建。落点：`ANDK_RERUN.md`（本成件）、`_ak_shell.py` / `_ak_tables.py` 等 `_ak_*` 与复核件 `_akv_*`、本撰写会话的 `_writer_*`、以及 `sandbox/` 下全部 12 份逐词副本 + A/B/C 输入副本 + 注射副本 + 三套布局目录。

### 1.3 绝对只读域（逐条列，一律不得修改/追加/覆盖）

| # | 只读对象 | 本会话处置 |
|---|---|---|
| 1 | `lead/PENDING_DECISIONS.md`（台账 1） | 只 `Read` / `read_bytes()` 取指纹；**未加注**（本会话实跑 `ANY_2026_11_09_ANNOTATION = False`） |
| 2 | `lead/GOAL_THREE_TARGETS_20261018.md`（台账 2） | 只取指纹 |
| 3 | `lead/d27_ruling_20261106/` | 只读；`check_d27.py` / `RULING_D27.md` / `FACTCHECK.md` 逐字节副本进写域 |
| 4 | `lead/d28_ruling_20261106/` | 同上 |
| 5 | `lead/d29_ruling_20261106/` | 同上 |
| 6 | `lead/d30_ruling_20261106/` | 同上 |
| 7 | `lead/stale_pass_20261109/` | 只读；实读 `STALE_PASS_INVENTORY.md:94-101,107,115-119,245-268` |
| 8 | `lead/k1bit_detect_20261109/` | 只读，纳入 212 文件全量快照 |
| 9 | `lead/detect_triage_20261109/` | 只读；实读 `DETECT_TRIAGE.md:160,162,172-173,274` |
| 10 | `lead/refsync_scope_20261109/` | 只读，纳入 212 文件全量快照 |

**只读自证（本会话实跑）**：`python -I -X utf8 -c "<读 4 份 guard json + 比对 212 文件>"` → `_ak_guard_before.json` / `_ak_guard_after.json` / `_akv_guard_before.json` / `_akv_guard_after.json` 四份 SHA256 同为 `e8a495465df09ab4f587f8067bc0b6def89970a7a711e81697653ae068e82d31`（`count=212`，`bytes=31776`），`GUARD_DIFF = []`，`GUARD_TOTAL_BYTES = 7695927`；`_ak_full_console.txt:2-3` `ORIGINALS_UNCHANGED_AFTER_EVERY_RUN = True` / `READONLY_SNAPSHOT_DIFF = 0`。
`git log -1` 仍 `2657458`、`git reflog -3` 无新 commit ⇒ 未 commit / 未 push（本会话实跑）。
`git status --short` 中两件台账为 `MM`（会话开始时就已如此，属既有工作树状态），六只读目录为 `??`；**本会话未对它们执行任何写操作**。

---

## 2 甲' 外壳

### 2.1 交付物与本次会话实跑命令

主件 `_ak_shell.py`（`sha256 = c33e35b02eb48b78fcefc942786a47fe145f694740c67aeff143203fb5700268`，32122 B，本会话 `hashlib` 实算）：**可部署**甲' 外壳，自带「生成→落盘→驱动」序列，不依赖预生成副本（`_ak_shell.py:354-418` `main_full()`、`_ak_shell.py:263-303` `do_run()`）。这一点区别于上游 `_sp_andk.py:7-15` 被 `STALE_PASS_INVENTORY.md:268` 自认的「演示外壳、非可部署门禁」。

本撰写会话**不采信交付件自报输出，自己重跑**（命令均为 `python -I -X utf8` + 绝对路径）：

```
python -I -X utf8 "D:/Project/ra2-campaign-forge/lead/andk_rerun_20261109/_ak_shell.py" --mode selftest > ".../_writer_selftest_console.txt" 2>&1
  -> SELFTEST_PROCESS_EXIT=0
  -> SELF_TEST = PASS
     正控 好输入: EXIT=0 verdict=PASS STDOUT='PASS\r\n'
     负控 缺文件: EXIT=2 verdict=FAIL STDOUT='[1] Missing file: ...\sandbox\d29\selftest_neg\FACTCHECK.md\r\nFAIL (missing files)\r\n'
     加控 OR 双删: EXIT=1 verdict=FAIL STDOUT='[4] Section 冲突是否成立: body must contain 互斥 OR 前提\r\nFAIL (content)\r\n'
     （_writer_selftest_console.txt；逐次 CMD/CWD/脚本 SHA256/输入指纹/原件未变复核见 _ak_selftest_out.txt:1-36）

python -I -X utf8 "D:/Project/ra2-campaign-forge/lead/andk_rerun_20261109/_ak_shell.py" --mode full > ".../_writer_full_console.txt" 2>&1
  -> FULL_PROCESS_EXIT=0
  -> TOTAL_RUNS = 108
     ORIGINALS_UNCHANGED_AFTER_EVERY_RUN = True
     READONLY_SNAPSHOT_DIFF = 0
       d27 baseline EXIT=0 'PASS: D-27 八项机械检查通过；裁决书引用 71 处\r\n' ; AND_k(k=2)=True ; AND_8=True ; AND_9=False ; missed=['[6b] …卡顿不存在…'] ; repro_identical=True
       d28 baseline EXIT=0 'PASS: D-28 全部 8 项机械检查通过 (exit 0)\r\n' ; AND_k(k=2)=True ; AND_8=True ; AND_9=False ; missed=['[4b] …1681…'] ; repro_identical=True
       d29 baseline EXIT=0 'PASS\r\n' ; AND_k(k=2)=True ; AND_8=True ; AND_9=False ; missed=['[4b] …前提…'] ; repro_identical=True
       d30 baseline EXIT=0 'PASS\r\n' ; AND_k(k=2)=True ; AND_8=True ; AND_9=False ; missed=['[4b] …误报率…'] ; repro_identical=True
     （_writer_full_console.txt:1-8；与交付 _ak_full_console.txt:1-8 逐字一致）
```

**重跑可复现性（本会话实跑）**：`python -I -X utf8 ".../_writer_verify.py" before` → `BEFORE_EXIT=0`；重跑 selftest+full 后 `python -I -X utf8 ".../_writer_verify.py" after` → `AFTER_EXIT=0`，输出 `ARTIFACT_HASH_DIFFS_AFTER_RERUN = []`、`ARTIFACTS_BYTE_IDENTICAL_AFTER_RERUN = True`、`TOTAL_RUNS_IN_JSONL = 108`、`TAG_COUNTS = {'ABC_ORIGINAL': 12, 'ABC_SENTINEL': 12, 'ABC_WORDA': 12, 'ABC_WORDB': 12, 'BAD_NEEDLE': 36, 'BASELINE': 4, 'REPRO_BASE': 4, 'REPRO_INJECTED': 4, 'TWELVE': 12}`、`ALL_ORIGINALS_UNCHANGED = True`（`_writer_after_console.txt:11-15`）。
逐次命令全文 / EXIT / STDOUT / stdout_sha256 / 脚本与输入 SHA256 全在 `_ak_runs.jsonl`（197059 B，108 行）；汇总在 `_ak_summary.json`（67597 B）；控制台在 `_ak_full_console.txt`（854 B）；三张表由 `_ak_tables.py` 生成（`_ak_PER_INPUT_TABLE.md` 34055 B / `_ak_BAD_NEEDLE_MATRIX.md` 10500 B / `_ak_REPRO.md` 3495 B）。Python `3.12.10`（`_ak_summary.json:python`）。

### 2.2 落点方案（逐件）与三套路径布局怎么解

源码依据（本会话逐行实读，逐字核对）：

| 件 | 源码行 | 解析方式 | 若照抄一套模板会怎样 |
|---|---|---|---|
| d27 | `check_d27.py:8` `DIRECTORY = Path("lead/d27_ruling_20261106")`；`:54` `paths = {name: DIRECTORY / name ...}` | **CWD 相对** | 从仓库根跑副本会读到只读原件，违反铁律 |
| d28 | `check_d28.py:54-55` `root = Path(__file__).resolve().parents[2]` / `directory = root / "lead" / "d28_ruling_20261106"`；`:60` `path = directory / name` | **脚本位置相对 parents[2]，深度必须正好 3 层** | 少一层则 `parents[2]` 指到别处 ⇒ `EXIT=2`（`STALE_PASS_INVENTORY.md:255` 记漏此点得 6 个 `EXIT=2` 作废） |
| d29 | `check_d29.py:50` `directory = Path(__file__).resolve().parent`；`:56` `path = directory / name` | **输入与脚本同目录** | 输入放子目录则缺文件 |
| d30 | `check_d30.py:50` / `:56` 同 d29 | **输入与脚本同目录** | 同 d29 |

令 `R = <写域>/sandbox/<gate>/<exp>/`（每次实验全新空目录，`shutil.rmtree` 后重建，`_ak_shell.py:265-270`）。外壳 `Layout` 类（`_ak_shell.py:132-159`）**逐件显式分支**，不是一套模板硬套四件：

| 件 | 副本脚本落点 | 输入文档落点 | CWD |
|---|---|---|---|
| **d27** | `R/check_dNN_<variant>.py` | `R/lead/d27_ruling_20261106/{RULING_D27.md,FACTCHECK.md}` | `R` |
| **d28** | `R/a/b/check_d28_<variant>.py` | `R/lead/d28_ruling_20261106/{RULING_D28.md,FACTCHECK.md}` | `R` |
| **d29** | `R/check_d29_<variant>.py` | `R/{RULING_D29.md,FACTCHECK.md}` | `R` |
| **d30** | `R/check_d30_<variant>.py` | `R/{RULING_D30.md,FACTCHECK.md}` | `R` |

**三套布局实跑输出**（`_ak_layout_out.txt:1-29`，本会话实读；四件基线均 `EXIT=0`、无路径错/输入缺，`:28` `before=212 files / after=212 files / diff=0`）：d27 `script_dir=…/d27/<exp>`、`input_dir=…/d27/<exp>/lead/d27_ruling_20261106`；d28 `script_dir=…/d28/<exp>/a/b`、`input_dir=…/d28/<exp>/lead/d28_ruling_20261106`；d29/d30 `script_dir=input_dir=…/dNN/<exp>`。

**d28 深度坑我本会话独立实跑复现**（不采信报告）：`python -I -X utf8 -c "<在 _writer_depth/ 下分别以 depth=3/2/1 落盘 check_d28.py 原件副本并驱动>"` →
`depth=3 ...\a\b\check_d28.py` `EXIT=0` `'PASS: D-28 全部 8 项机械检查通过 (exit 0)\r\n'`；
`depth=2 ...\a\check_d28.py` `EXIT=2` `'FAIL [1] 文件缺失：lead/d28_ruling_20261106/RULING_D28.md\r\nFAIL [1] 文件缺失：lead/d28_ruling_20261106/FACTCHECK.md\r\nRESULT: FILE MISSING (exit 2)\r\n'`；
`depth=1 ...\check_d28.py` 同样 `EXIT=2`；三份副本脚本 SHA256 与原件全等。⇒ **路径坑真实存在且被外壳正确规避**。

### 2.3 12 份逐词副本（生成→落盘→驱动序列）

`_ak_shell.py:361-418`：① 逐件建 `twelve/` 目录 → ② 逐字节写两份原件输入 → ③ 把 OR 元组替换为单元素词表生成 `WA` / `WB` / `SENT`（`_ak_shell.py:162-181` `script_bytes()`，断言 `t.count(or_tuple)==1`）→ ④ 12 份逐个 `subprocess.run` 真实驱动 → ⑤ 每次跑完 `verify_originals()`。落点与 SHA256 全列 `_ak_twelve_out.txt`；例如 d27 `WA` = `sandbox/d27/twelve/_w_d27_A.py`，`sha256=5ae1cade31e3506130408f398cdc9a5e150b13ba4c63ffaababad0636991fe0a`，3746 B，`("外推", "卡顿不存在") -> ("外推",)`；d28 `WA` = `sandbox/d28/twelve/a/b/_w_d28_A.py`，`sha256=ed12018ebe9b9b571ba3a3ea2541dc9d78199274eb4407690876396f5c20db60`，4532 B。
**★ 这 12 份是「改写脚本副本」，不是原件**：原件 OR 元组从未被改写（§6 判不了什么第 7 条）。

### 2.4 外壳自检：正控 / 负控 / 加控（本会话实跑输出见 §2.1）

- 正控（好输入）：d29 `BASE` + 两份原件输入 ⇒ `EXIT=0` / `PASS`（`_ak_selftest_out.txt:2,5-14`）。
- 负控（缺文件）：同副本删 `FACTCHECK.md` ⇒ `EXIT=2` / `[1] Missing file: …` + `FAIL (missing files)`（`:3,16-25`）。
- 加控（OR 双删）：删 `互斥`+`前提` ⇒ `EXIT=1` / `[4] Section 冲突是否成立: body must contain 互斥 OR 前提` + `FAIL (content)`（`:4,27-36`）。
- 三次 `原件未变 = True`（`_ak_selftest_out.txt:14,25,36`）；`SELF_TEST = PASS`（`:1`）。

### 2.5 可粘贴代码

**① 单条命令重建并跑完（可部署外壳，清空 `sandbox/` 后亦可用）**

```bash
python -I -X utf8 "D:/Project/ra2-campaign-forge/lead/andk_rerun_20261109/_ak_shell.py" --mode selftest
python -I -X utf8 "D:/Project/ra2-campaign-forge/lead/andk_rerun_20261109/_ak_shell.py" --mode full  > "D:/Project/ra2-campaign-forge/lead/andk_rerun_20261109/_ak_full_console.txt" 2>&1
python -I -X utf8 "D:/Project/ra2-campaign-forge/lead/andk_rerun_20261109/_ak_tables.py"
```

**② 外壳核心片段（逐字摘自 `_ak_shell.py:132-181,263-303`，可直接粘进自己的门禁）**

```python
# 三套路径布局：逐件显式分支，不可套一个模板
class Layout:
    def __init__(self, gate, root):
        self.gate, self.root, self.cwd = gate, root, root
        if gate == "d27":                       # check_d27.py:8 CWD 相对
            self.script_dir = root
            self.input_dir  = root / "lead" / "d27_ruling_20261106"
        elif gate == "d28":                     # check_d28.py:54-55 parents[2] 必须深 3 层
            self.script_dir = root / "a" / "b"
            self.input_dir  = root / "lead" / "d28_ruling_20261106"
        else:                                   # check_d29.py:50 / check_d30.py:50 同目录
            self.script_dir = root
            self.input_dir  = root

def script_bytes(gate, variant):
    """BASE=原件逐字节副本；WA/WB/SENT=OR 元组单元素化（仅写域副本）"""
    p = SRC / GATES[gate]["dir"] / GATES[gate]["check"]
    b, t = p.read_bytes(), p.read_bytes().decode("utf-8")
    if variant == "BASE": return b, "原件逐字节副本（未改一个字节）"
    word = {"WA": GATES[gate]["words"][0], "WB": GATES[gate]["words"][1],
            "SENT": "TOTALLY_BROKEN_NEEDLE_SENTINEL_XYZ"}[variant]
    or_tuple = GATES[gate]["or_tuple"]
    assert t.count(or_tuple) == 1
    return t.replace(or_tuple, '("%s",)' % word, 1).encode("utf-8"), "OR -> 单元素"

def do_run(gate, exp, variant, mut, tag):
    root = WORK / gate / exp
    if root.exists(): shutil.rmtree(root)
    lay = Layout(gate, root)
    lay.script_dir.mkdir(parents=True, exist_ok=True)
    lay.input_dir.mkdir(parents=True, exist_ok=True)
    sb, _ = script_bytes(gate, variant)
    spath = lay.script_dir / ("check_%s_%s.py" % (gate, variant))
    spath.write_bytes(sb)
    for name, data in make_docs(gate, mut)[0].items():
        (lay.input_dir / name).write_bytes(data)          # 注射只落写域副本
    cmd = [sys.executable, "-I", "-X", "utf8", str(spath)]
    p = subprocess.run(cmd, cwd=str(lay.cwd), capture_output=True)
    out = p.stdout.decode("utf-8", errors="replace")
    unchanged = verify_originals(strict=True)             # ★ 每次跑完复核原件 SHA256 未变
    verdict = "PASS" if (p.returncode == 0 and "PASS" in out and "FAIL" not in out) else "FAIL"
    return dict(cmd=cmd, cwd=str(lay.cwd), script_sha256=hashlib.sha256(sb).hexdigest(),
                script_bytes=len(sb), exit=p.returncode, stdout=out,
                stdout_sha256=hashlib.sha256(p.stdout).hexdigest(),
                verdict=verdict, fail_items=sorted(set(int(x) for x in re.findall(r"\[(\d+)\]", out))),
                originals_unchanged=unchanged)
```

**③ 逐格核对/绑定行复核（本撰写会话自写，可直接粘）**

```bash
python -I -X utf8 "D:/Project/ra2-campaign-forge/lead/andk_rerun_20261109/_writer_verify.py" before
python -I -X utf8 "D:/Project/ra2-campaign-forge/lead/andk_rerun_20261109/_writer_verify.py" after
python -I -X utf8 "D:/Project/ra2-campaign-forge/lead/andk_rerun_20261109/_writer_table.py"
```

---

## 3 ★ 逐输入判定表（A B C 三输入 × 8 项，完整表）

本节为 **A B C 三输入** × 每件 8 个编号项的完整逐格判定（4 × 3 × 8 = 96 行），并给出显式 `AND_k` 公式、实算值与 `DISTINGUISHABLE_PASS`。

### 3.1 输入定义与公式

| input | 定义 | d27 | d28 | d29 | d30 |
|---|---|---|---|---|---|
| **A** | 原 RULING，两词都在（逐字节副本） | 外推 + 卡顿不存在 | 历史数字 + 1681 | 互斥 + 前提 | 93.98 + 误报率 |
| **B** | 删**第二**根针 | 删「卡顿不存在」(1 处) | 删「1681」(5 处) | 删「前提」(2 处) | 删「误报率」(3 处) |
| **C** | 两词**都**删 | 外推(3)+卡顿不存在(1) | 历史数字(3)+1681(5) | 互斥(5)+前提(2) | 93.98(3)+误报率(3) |

（输入定义与删除处数据见 `_ak_PER_INPUT_TABLE.md:42,53,64,77,88,99,112,123,134,147,158,169`，本会话实读；注射实现 `_ak_shell.py:200-211`。`FACTCHECK.md` 在 A/B/C 中保持原件副本。）

每个 input 跑 4 次真实独立运行：`BASE`（原件逐字节副本，SHA256 见 §6 绑定行）、`WA`（只查第一词的改写副本）、`WB`（只查第二词）、`SENT`（只查零命中哨兵 `TOTALLY_BROKEN_NEEDLE_SENTINEL_XYZ`）。**显式公式**（`_ak_PER_INPUT_TABLE.md:7-15`、`_ak_shell.py:466-486` 实算）：

```
P_WA(input)  = [逐词副本 WA 在该 input 上 EXIT=0 ∧ 输出含 PASS ∧ 无 FAIL]
P_WB(input)  = [逐词副本 WB 在该 input 上 EXIT=0 ∧ 输出含 PASS ∧ 无 FAIL]
AGGREGATE    = AND_k(P_WA, P_WB)   with k = 2   （两次真实独立运行，非推断）
BAD_NEEDLE_CAUGHT = [SENT 副本在该 input 上 EXIT≠0 ∧ verdict=FAIL]
DISTINGUISHABLE_PASS = AGGREGATE ∧ BAD_NEEDLE_CAUGHT
```

### 3.2 ★ 完整逐格表：4 件 × 3 输入 × 8 项 = 96 行

表中 `BASE/WA/WB/SENT` 列 = 该运行对该编号项的判定（脚本只输出失败项编号，故 `PASS` = 该项号未出现在 `fail_items`；`FAIL` = 该项号出现在 `fail_items`）。**逐格依据** = `_ak_runs.jsonl` 中该次运行的 `exit` 与 `fail_items`（本会话 `python -I -X utf8 ".../_writer_table.py"` 从重跑后的 108 行生成，输出 `WROTE _writer_96_table.md rows=96`，落盘 `_writer_96_table.md:1-99`）；命令全文、被核脚本 SHA256、输入 SHA256、STDOUT 原文、stdout_sha256 逐行在 `_ak_PER_INPUT_TABLE.md` §2（d27 A `:46-49`、B `:57-60`、C `:68-71`；d28 A `:81-84`、B `:92-95`、C `:103-106`；d29 A `:116-119`、B `:127-130`、C `:138-141`；d30 A `:151-154`、B `:162-165`、C `:173-176`）。

| gate | 输入 | 项 | 检查内容 | BASE | WA | WB | SENT | 逐格依据（运行记录） |
|---|---|---|---|---|---|---|---|---|
| d27 | A | [1] | 两文件存在/非空/UTF-8 | PASS | PASS | PASS | PASS | `_ak_runs.jsonl` d27/abc_A `EXIT=0 fail_items=[]` |
| d27 | A | [2] | `^main:(A|B|C)$` 声明行 | PASS | PASS | PASS | PASS | 同上 |
| d27 | A | [3] | 7 个必需二级标题 | PASS | PASS | PASS | PASS | 同上 |
| d27 | A | [4] | 新证据是否成立 ⊇ 循环论证 | PASS | PASS | PASS | PASS | 同上 |
| d27 | A | [5] | 授权边界 ⊇ 本次不授权 | PASS | PASS | PASS | PASS | 同上 |
| d27 | A | [6] | 未背书 ⊇ 外推 OR 卡顿不存在（OR 项） | PASS | PASS | PASS | **FAIL** | `_ak_PER_INPUT_TABLE.md:46-49`；WA/WB EXIT=0、SENT EXIT=1 `FAIL [6] …TOTALLY_BROKEN…` |
| d27 | A | [7] | 裁决书引用 ≥8 处 | PASS | PASS | PASS | PASS | `EXIT=0 fail_items=[]` |
| d27 | A | [8] | FACTCHECK ⊇ selfBias | PASS | PASS | PASS | PASS | 同上 |
| d27 | B | [1] | 两文件存在/非空/UTF-8 | PASS | PASS | PASS | PASS | `_ak_PER_INPUT_TABLE.md:57-60` `EXIT=0 fail_items=[]` |
| d27 | B | [2] | `^main:(A|B|C)$` 声明行 | PASS | PASS | PASS | PASS | 同上 |
| d27 | B | [3] | 7 个必需二级标题 | PASS | PASS | PASS | PASS | 同上 |
| d27 | B | [4] | 新证据是否成立 ⊇ 循环论证 | PASS | PASS | PASS | PASS | 同上 |
| d27 | B | [5] | 授权边界 ⊇ 本次不授权 | PASS | PASS | PASS | PASS | 同上 |
| d27 | B | [6] | 未背书 ⊇ 外推 OR 卡顿不存在（OR 项） | **PASS** | PASS | **FAIL** | **FAIL** | `:57` BASE `EXIT=0` stdout 与 A 逐字同（`a2dd2a91…`）；`:59` WB `EXIT=1 'FAIL [6] …卡顿不存在\r\n'`；`:60` SENT `EXIT=1` |
| d27 | B | [7] | 裁决书引用 ≥8 处 | PASS | PASS | PASS | PASS | `EXIT=0 fail_items=[]` |
| d27 | B | [8] | FACTCHECK ⊇ selfBias | PASS | PASS | PASS | PASS | 同上 |
| d27 | C | [1] | 两文件存在/非空/UTF-8 | PASS | PASS | PASS | PASS | `_ak_PER_INPUT_TABLE.md:68-71` `EXIT=1 fail_items=[6]` |
| d27 | C | [2] | `^main:(A|B|C)$` 声明行 | PASS | PASS | PASS | PASS | 同上 |
| d27 | C | [3] | 7 个必需二级标题 | PASS | PASS | PASS | PASS | 同上 |
| d27 | C | [4] | 新证据是否成立 ⊇ 循环论证 | PASS | PASS | PASS | PASS | 同上 |
| d27 | C | [5] | 授权边界 ⊇ 本次不授权 | PASS | PASS | PASS | PASS | 同上 |
| d27 | C | [6] | 未背书 ⊇ 外推 OR 卡顿不存在（OR 项） | **FAIL** | FAIL | FAIL | FAIL | `:68` `EXIT=1 'FAIL [6] …外推 或 卡顿不存在\r\n'`；`:69-71` WA/WB/SENT 全 `EXIT=1` |
| d27 | C | [7] | 裁决书引用 ≥8 处 | PASS | PASS | PASS | PASS | `EXIT=1 fail_items=[6]` |
| d27 | C | [8] | FACTCHECK ⊇ selfBias | PASS | PASS | PASS | PASS | 同上 |
| d28 | A | [1] | 两文件存在/非空/UTF-8 | PASS | PASS | PASS | PASS | `_ak_runs.jsonl` d28/abc_A `EXIT=0 fail_items=[]` |
| d28 | A | [2] | q1/q2 恰一行合法声明 | PASS | PASS | PASS | PASS | 同上 |
| d28 | A | [3] | 7 个必需小节 | PASS | PASS | PASS | PASS | 同上 |
| d28 | A | [4] | D 链处置 ⊇ 历史数字 OR 1681（OR 项） | PASS | PASS | PASS | **FAIL** | `_ak_PER_INPUT_TABLE.md:81-84`；SENT `EXIT=1 'FAIL [4] …SENTINEL\r\nRESULT: FAIL (exit 1)\r\n'` |
| d28 | A | [5] | 授权边界 ⊇ 本次不授权 | PASS | PASS | PASS | PASS | `EXIT=0 fail_items=[]` |
| d28 | A | [6] | 未背书 AND 词表(外推,口径 B) | PASS | PASS | PASS | PASS | 同上 |
| d28 | A | [7] | 裁决书引用 ≥8 处 | PASS | PASS | PASS | PASS | 同上 |
| d28 | A | [8] | FACTCHECK ⊇ selfBias | PASS | PASS | PASS | PASS | 同上 |
| d28 | B | [1] | 两文件存在/非空/UTF-8 | PASS | PASS | PASS | PASS | `_ak_PER_INPUT_TABLE.md:92-95` `EXIT=0 fail_items=[]` |
| d28 | B | [2] | q1/q2 恰一行合法声明 | PASS | PASS | PASS | PASS | 同上 |
| d28 | B | [3] | 7 个必需小节 | PASS | PASS | PASS | PASS | 同上 |
| d28 | B | [4] | D 链处置 ⊇ 历史数字 OR 1681（OR 项） | **PASS** | PASS | **FAIL** | **FAIL** | `:92` BASE `EXIT=0` stdout 与 A 逐字同（`0a33ffe0…`）；`:94` WB `EXIT=1 'FAIL [4] …1681\r\nRESULT: FAIL (exit 1)\r\n'`；`:95` SENT `EXIT=1` |
| d28 | B | [5] | 授权边界 ⊇ 本次不授权 | PASS | PASS | PASS | PASS | `EXIT=0 fail_items=[]` |
| d28 | B | [6] | 未背书 AND 词表(外推,口径 B) | PASS | PASS | PASS | PASS | 同上 |
| d28 | B | [7] | 裁决书引用 ≥8 处 | PASS | PASS | PASS | PASS | 同上 |
| d28 | B | [8] | FACTCHECK ⊇ selfBias | PASS | PASS | PASS | PASS | 同上 |
| d28 | C | [1] | 两文件存在/非空/UTF-8 | PASS | PASS | PASS | PASS | `_ak_PER_INPUT_TABLE.md:103-106` `EXIT=1 fail_items=[4]` |
| d28 | C | [2] | q1/q2 恰一行合法声明 | PASS | PASS | PASS | PASS | 同上 |
| d28 | C | [3] | 7 个必需小节 | PASS | PASS | PASS | PASS | 同上 |
| d28 | C | [4] | D 链处置 ⊇ 历史数字 OR 1681（OR 项） | **FAIL** | FAIL | FAIL | FAIL | `:103` `EXIT=1 'FAIL [4] …历史数字、1681\r\nRESULT: FAIL (exit 1)\r\n'`；`:104-106` 全 `EXIT=1` |
| d28 | C | [5] | 授权边界 ⊇ 本次不授权 | PASS | PASS | PASS | PASS | `EXIT=1 fail_items=[4]` |
| d28 | C | [6] | 未背书 AND 词表(外推,口径 B) | PASS | PASS | PASS | PASS | 同上 |
| d28 | C | [7] | 裁决书引用 ≥8 处 | PASS | PASS | PASS | PASS | 同上 |
| d28 | C | [8] | FACTCHECK ⊇ selfBias | PASS | PASS | PASS | PASS | 同上 |
| d29 | A | [1] | 两文件存在/非空/UTF-8 | PASS | PASS | PASS | PASS | `_ak_runs.jsonl` d29/abc_A `EXIT=0 fail_items=[]` |
| d29 | A | [2] | q1 恰一行合法声明 | PASS | PASS | PASS | PASS | 同上 |
| d29 | A | [3] | 7 个必需小节 | PASS | PASS | PASS | PASS | 同上 |
| d29 | A | [4] | 冲突是否成立 ⊇ 互斥 OR 前提（OR 项） | PASS | PASS | PASS | **FAIL** | `_ak_PER_INPUT_TABLE.md:116-119`；SENT `EXIT=1 '[4] …TOTALLY_BROKEN…\r\nFAIL (content)\r\n'` |
| d29 | A | [5] | 授权边界 ⊇ 本次不授权 | PASS | PASS | PASS | PASS | `EXIT=0 fail_items=[]` |
| d29 | A | [6] | 未背书 AND 词表(口径 B,外推,191) | PASS | PASS | PASS | PASS | 同上 |
| d29 | A | [7] | 裁决书引用 ≥8 处 | PASS | PASS | PASS | PASS | 同上 |
| d29 | A | [8] | FACTCHECK ⊇ selfBias | PASS | PASS | PASS | PASS | 同上 |
| d29 | B | [1] | 两文件存在/非空/UTF-8 | PASS | PASS | PASS | PASS | `_ak_PER_INPUT_TABLE.md:127-130` `EXIT=0 fail_items=[]` |
| d29 | B | [2] | q1 恰一行合法声明 | PASS | PASS | PASS | PASS | 同上 |
| d29 | B | [3] | 7 个必需小节 | PASS | PASS | PASS | PASS | 同上 |
| d29 | B | [4] | 冲突是否成立 ⊇ 互斥 OR 前提（OR 项） | **PASS** | PASS | **FAIL** | **FAIL** | `:127` BASE `EXIT=0 stdout='PASS\r\n'`（`d938fa18…`，与 A 逐字同）；`:129` WB `EXIT=1 '[4] …前提\r\nFAIL (content)\r\n'`；`:130` SENT `EXIT=1` |
| d29 | B | [5] | 授权边界 ⊇ 本次不授权 | PASS | PASS | PASS | PASS | `EXIT=0 fail_items=[]` |
| d29 | B | [6] | 未背书 AND 词表(口径 B,外推,191) | PASS | PASS | PASS | PASS | 同上 |
| d29 | B | [7] | 裁决书引用 ≥8 处 | PASS | PASS | PASS | PASS | 同上 |
| d29 | B | [8] | FACTCHECK ⊇ selfBias | PASS | PASS | PASS | PASS | 同上 |
| d29 | C | [1] | 两文件存在/非空/UTF-8 | PASS | PASS | PASS | PASS | `_ak_PER_INPUT_TABLE.md:138-141` `EXIT=1 fail_items=[4]` |
| d29 | C | [2] | q1 恰一行合法声明 | PASS | PASS | PASS | PASS | 同上 |
| d29 | C | [3] | 7 个必需小节 | PASS | PASS | PASS | PASS | 同上 |
| d29 | C | [4] | 冲突是否成立 ⊇ 互斥 OR 前提（OR 项） | **FAIL** | FAIL | FAIL | FAIL | `:138` `EXIT=1 '[4] …互斥 OR 前提\r\nFAIL (content)\r\n'`；`:139-141` 全 `EXIT=1` |
| d29 | C | [5] | 授权边界 ⊇ 本次不授权 | PASS | PASS | PASS | PASS | `EXIT=1 fail_items=[4]` |
| d29 | C | [6] | 未背书 AND 词表(口径 B,外推,191) | PASS | PASS | PASS | PASS | 同上 |
| d29 | C | [7] | 裁决书引用 ≥8 处 | PASS | PASS | PASS | PASS | 同上 |
| d29 | C | [8] | FACTCHECK ⊇ selfBias | PASS | PASS | PASS | PASS | 同上 |
| d30 | A | [1] | 两文件存在/非空/UTF-8 | PASS | PASS | PASS | PASS | `_ak_runs.jsonl` d30/abc_A `EXIT=0 fail_items=[]` |
| d30 | A | [2] | q1 恰一行合法声明 | PASS | PASS | PASS | PASS | 同上 |
| d30 | A | [3] | 7 个必需小节 | PASS | PASS | PASS | PASS | 同上 |
| d30 | A | [4] | 三档权衡的实质 ⊇ 93.98 OR 误报率（OR 项） | PASS | PASS | PASS | **FAIL** | `_ak_PER_INPUT_TABLE.md:151-154`；SENT `EXIT=1 '[4] …TOTALLY_BROKEN…\r\nFAIL (content)\r\n'` |
| d30 | A | [5] | 授权边界 ⊇ 本次不授权 | PASS | PASS | PASS | PASS | `EXIT=0 fail_items=[]` |
| d30 | A | [6] | 未背书 AND 词表(外推,栈采样) | PASS | PASS | PASS | PASS | 同上 |
| d30 | A | [7] | 裁决书引用 ≥8 处 | PASS | PASS | PASS | PASS | 同上 |
| d30 | A | [8] | FACTCHECK ⊇ selfBias | PASS | PASS | PASS | PASS | 同上 |
| d30 | B | [1] | 两文件存在/非空/UTF-8 | PASS | PASS | PASS | PASS | `_ak_PER_INPUT_TABLE.md:162-165` `EXIT=0 fail_items=[]` |
| d30 | B | [2] | q1 恰一行合法声明 | PASS | PASS | PASS | PASS | 同上 |
| d30 | B | [3] | 7 个必需小节 | PASS | PASS | PASS | PASS | 同上 |
| d30 | B | [4] | 三档权衡的实质 ⊇ 93.98 OR 误报率（OR 项） | **PASS** | PASS | **FAIL** | **FAIL** | `:162` BASE `EXIT=0 stdout='PASS\r\n'`（`d938fa18…`，与 A 逐字同）；`:164` WB `EXIT=1 '[4] …误报率\r\nFAIL (content)\r\n'`；`:165` SENT `EXIT=1` |
| d30 | B | [5] | 授权边界 ⊇ 本次不授权 | PASS | PASS | PASS | PASS | `EXIT=0 fail_items=[]` |
| d30 | B | [6] | 未背书 AND 词表(外推,栈采样) | PASS | PASS | PASS | PASS | 同上 |
| d30 | B | [7] | 裁决书引用 ≥8 处 | PASS | PASS | PASS | PASS | 同上 |
| d30 | B | [8] | FACTCHECK ⊇ selfBias | PASS | PASS | PASS | PASS | 同上 |
| d30 | C | [1] | 两文件存在/非空/UTF-8 | PASS | PASS | PASS | PASS | `_ak_PER_INPUT_TABLE.md:173-176` `EXIT=1 fail_items=[4]` |
| d30 | C | [2] | q1 恰一行合法声明 | PASS | PASS | PASS | PASS | 同上 |
| d30 | C | [3] | 7 个必需小节 | PASS | PASS | PASS | PASS | 同上 |
| d30 | C | [4] | 三档权衡的实质 ⊇ 93.98 OR 误报率（OR 项） | **FAIL** | FAIL | FAIL | FAIL | `:173` `EXIT=1 '[4] …93.98 OR 误报率\r\nFAIL (content)\r\n'`；`:174-176` 全 `EXIT=1` |
| d30 | C | [5] | 授权边界 ⊇ 本次不授权 | PASS | PASS | PASS | PASS | `EXIT=1 fail_items=[4]` |
| d30 | C | [6] | 未背书 AND 词表(外推,栈采样) | PASS | PASS | PASS | PASS | 同上 |
| d30 | C | [7] | 裁决书引用 ≥8 处 | PASS | PASS | PASS | PASS | 同上 |
| d30 | C | [8] | FACTCHECK ⊇ selfBias | PASS | PASS | PASS | PASS | 同上 |

### 3.3 `AND_k` 实算与 `DISTINGUISHABLE_PASS`（12 行，本会话从 `_ak_summary.json` 重算）

`python -I -X utf8 ".../_writer_verify.py" after` 输出 `_writer_after_console.txt:75-93`（逐行打印 `s["abc"]` 与 `s["per_word"]`，与 `_ak_PER_INPUT_TABLE.md:21-36,182-189` 逐格一致）：

| gate | 输入 | 原件 `any(present)` | P_WA | P_WB | `AGGREGATE=AND_k` | SENT EXIT | BAD_NEEDLE_CAUGHT | `DISTINGUISHABLE_PASS` |
|---|---|---|---|---|---|---|---|---|
| d27 | A | PASS (0) | True | True | **True** | 1 | True | **True** |
| d27 | B | PASS (0) | True | **False** | **False** | 1 | True | **False** |
| d27 | C | FAIL (1) | False | False | **False** | 1 | True | False |
| d28 | A | PASS (0) | True | True | **True** | 1 | True | **True** |
| d28 | B | PASS (0) | True | **False** | **False** | 1 | True | **False** |
| d28 | C | FAIL (1) | False | False | **False** | 1 | True | False |
| d29 | A | PASS (0) | True | True | **True** | 1 | True | **True** |
| d29 | B | PASS (0) | True | **False** | **False** | 1 | True | **False** |
| d29 | C | FAIL (1) | False | False | **False** | 1 | True | False |
| d30 | A | PASS (0) | True | True | **True** | 1 | True | **True** |
| d30 | B | PASS (0) | True | **False** | **False** | 1 | True | **False** |
| d30 | C | FAIL (1) | False | False | **False** | 1 | True | False |

8 项通过计数（本会话 `python -I -X utf8 ".../_writer_table.py"` 生成 `_writer_96_summary.md`，`EXIT=0`）：`A` 四件 `BASE/WA/WB = 8/8`、`SENT = 7/8`；`B` 四件 `BASE/WA = 8/8`、`WB = 7/8`、`SENT = 7/8`；`C` 四件 `BASE/WA/WB/SENT = 7/8`。
★ **如实写「全过」**：`A` 输入下四件 `BASE` 的 8 个编号项**全过**（8/8，无差异），`AND_k=True`、`DISTINGUISHABLE_PASS=True`；这不是挑格，是 A 输入真实结果。但 **B 输入下四件 `BASE` 仍 8/8 全过且 `EXIT=0`、stdout 与 A 逐字不变**（`_writer_after_console.txt:18-29,69-73`），而 `AND_k=False` ⇒ 原件的「全过」在逐输入口径下**看不见被杀掉的那根针**。

**原件 `any` vs 外壳 `AND_k` 对照**（`_ak_REPORT.md:213-224`）：A 无差异；**B 实质差异**（原件 PASS/EXIT=0 输出逐字不变，外壳 `AND_2(True,False)=False`）；C 无差异（都 FAIL）。根因 = `check_d27.py:86-87` `any(keyword in body ... for keyword in keywords)`、`check_d28.py:94-99` `all(present) if require_all else any(present)`、`check_d29.py:82-87` / `check_d30.py:82-87` `any(matches)` 把 k 个词折成一个布尔（`_ak_shell.py:172-175` 把 OR 元组改成单元素后 WB 才独立成一次运行）。

**★ 12 份逐词副本在原件输入上 `DISTINGUISHABLE_PASS=True` 的限定**：`_writer_after_console.txt:89-93` 四件均 `k=2 p=[True,True] AGG=True CAUGHT=True DP=True`，与 `STALE_PASS_INVENTORY.md:263` 的 4/4 演示一致；**但这一行不能当门禁可信**——它证明的是「把 OR 元组改成单元素后的改写脚本副本」各能独立过，原件 `any(present)` 一次聚合从未被改写（题给【铁律】）。

---

## 4 ★ 坏针哨兵矩阵（件 × 项，逐格，不许只给计数）

**判据**：注入前 = 该件 `BASE` 基线；注射一律落在写域副本输入文档上，被核脚本一律 `BASE`（原件逐字节副本）；`是否被抓 = 注入后 EXIT≠0 ∧ verdict=FAIL`（`_ak_shell.py:454-461`）。
**逐格证据**：交付 `_ak_BAD_NEEDLE_MATRIX.md:8-43`（36 行，每行含注射动作、注入前/后、STDOUT 原文、是否被抓）；本会话独立实跑 `python -I -X utf8 ".../_writer_verify.py" after` 从重跑后的 `_ak_runs.jsonl` 打印 36 行 `mut / EXIT / verdict / fail_items / stdout / caught`（`_writer_after_console.txt:31-67`）；复核方逐格比对 `_akv_cells_out.txt:1-3`（`EXEC_BAD_NEEDLE_ROWS = 36` / `OWN_MATRIX_CELLS = 36` / `MD_TABLE_ROWS = 36`）、`:48` `PROBLEMS = 0`、`:49` `PATH_ONLY_DIFFS = 2 [('d29', '1'), ('d30', '1')]`（仅 d29/1、d30/1 两处绝对路径因沙箱层级不同，已显式归一化核对语义一致）。**下表 36 行逐行给依据，不只给计数。**

| gate | 项 | 注射动作（写域副本） | 注入前 | 注入后 | 是否被抓 | 该格依据 |
|---|---|---|---|---|---|---|
| d27 | [1] | 删 `FACTCHECK.md` | PASS (0) | FAIL (2) | ✔ True | `_writer_after_console.txt:32` `'FAIL [1] 文件缺失或不是普通文件: lead/d27_ruling_20261106/FACTCHECK.md\r\n'`；矩阵 `:8` |
| d27 | [2] | `main:` 声明改 `NEEDLE_DELETED` | PASS (0) | FAIL (1) | ✔ True | `:33` `'FAIL [2] 裁决书须含匹配 ^main:\s*(A|B|C)\s*$ 的一行\r\n'`；`check_d27.py:73-74`；矩阵 `:9` |
| d27 | [3] | 「## 7 诚实账」改名 | PASS (0) | FAIL (1) | ✔ True | `:34` `'FAIL [3] 缺少二级标题: 诚实账\r\n'`；`check_d27.py:77-79`；矩阵 `:10` |
| d27 | [4] | 删单一字面量「循环论证」(1 处) | PASS (0) | FAIL (1) | ✔ True | `:35` `'FAIL [4] 新证据是否成立小节正文须包含: 循环论证\r\n'`；`check_d27.py:82`；矩阵 `:11` |
| d27 | [5] | 删「本次不授权」(1 处) | PASS (0) | FAIL (1) | ✔ True | `:36` `'FAIL [5] 授权边界小节正文须包含: 本次不授权\r\n'`；`check_d27.py:83`；矩阵 `:12` |
| d27 | [6] | OR 两词全删（外推 3 + 卡顿不存在 1） | PASS (0) | FAIL (1) | ✔ True | `:37` `'FAIL [6] 未背书小节正文须包含: 外推 或 卡顿不存在\r\n'`；`check_d27.py:84,86-88`；矩阵 `:13` |
| **d27** | **[6b]** | **OR 项只杀一根针：删「卡顿不存在」(1 处)** | PASS (0) | **PASS (0)** | **✘ False 漏抓** | `:38` `'PASS: D-27 八项机械检查通过；裁决书引用 71 处\r\n'`；`:70` `stdout==A_baseline=True`；矩阵 `:14`；`check_d27.py:84,86-87` |
| d27 | [7] | 71 处 `file:line` 行号改非数字 | PASS (0) | FAIL (1) | ✔ True | `:39` `'FAIL [7] 裁决书引用须至少 8 处，实际 0 处\r\n'`；`check_d27.py:18,90-92`；矩阵 `:15` |
| d27 | [8] | FACTCHECK 删 `selfBias`(7 处) | PASS (0) | FAIL (1) | ✔ True | `:40` `'FAIL [8] FACTCHECK.md 须包含 selfBias\r\n'`；`check_d27.py:93-94`；矩阵 `:16` |
| d28 | [1] | 删 `FACTCHECK.md` | PASS (0) | FAIL (2) | ✔ True | `:41` `'FAIL [1] 文件缺失：lead/d28_ruling_20261106/FACTCHECK.md\r\nRESULT: FILE MISSING (exit 2)\r\n'`；`check_d28.py:63-64,109-111`；矩阵 `:17` |
| d28 | [2] | q1/q2 两行声明改坏 | PASS (0) | FAIL (1) | ✔ True | `:42` `'FAIL [2] q1 …合法 0 行，声明 1 行\r\nFAIL [2] q2 …\r\nRESULT: FAIL (exit 1)\r\n'`；`check_d28.py:76-84`；矩阵 `:18` |
| d28 | [3] | 「## 7 诚实账」改名 | PASS (0) | FAIL (1) | ✔ True | `:43` `'FAIL [3] 缺少小节：诚实账\r\nRESULT: FAIL (exit 1)\r\n'`；`check_d28.py:86-88`；矩阵 `:19` |
| d28 | [4] | OR 两词全删（历史数字 3 + 1681 5） | PASS (0) | FAIL (1) | ✔ True | `:44` `'FAIL [4] D 链处置 小节正文须至少包含其一：历史数字、1681\r\nRESULT: FAIL (exit 1)\r\n'`；`check_d28.py:90,94-99`；矩阵 `:20` |
| **d28** | **[4b]** | **OR 项只杀一根针：删「1681」(5 处)** | PASS (0) | **PASS (0)** | **✘ False 漏抓** | `:45` `'PASS: D-28 全部 8 项机械检查通过 (exit 0)\r\n'`；`:71` `stdout==A_baseline=True`；矩阵 `:21`；`check_d28.py:90,97` |
| d28 | [5] | 删「本次不授权」(2 处) | PASS (0) | FAIL (1) | ✔ True | `:46` `'FAIL [5] 授权边界 小节正文须同时包含：本次不授权\r\nRESULT: FAIL (exit 1)\r\n'`；`check_d28.py:91,97`；矩阵 `:22` |
| d28 | [6] | 删 AND 词表「外推」(1 处) | PASS (0) | FAIL (1) | ✔ True | `:47` `'FAIL [6] 未背书 小节正文须同时包含：外推、口径 B\r\nRESULT: FAIL (exit 1)\r\n'`；`check_d28.py:92,97`；矩阵 `:23` |
| d28 | [7] | 69 处引用行号改非数字 | PASS (0) | FAIL (1) | ✔ True | `:48` `'FAIL [7] RULING_D28.md 全文引用须至少 8 处，实际 0 处\r\nRESULT: FAIL (exit 1)\r\n'`；`check_d28.py:100-102`；矩阵 `:24` |
| d28 | [8] | FACTCHECK 删 `selfBias`(7 处) | PASS (0) | FAIL (1) | ✔ True | `:49` `'FAIL [8] FACTCHECK.md 缺少 selfBias 字样\r\nRESULT: FAIL (exit 1)\r\n'`；`check_d28.py:104-106`；矩阵 `:25` |
| d29 | [1] | 删 `FACTCHECK.md` | PASS (0) | FAIL (2) | ✔ True | `:50` `'[1] Missing file: …\sandbox\d29\inj_1\FACTCHECK.md\r\nFAIL (missing files)\r\n'`；`check_d29.py:59-60,99-101`；矩阵 `:26` |
| d29 | [2] | q1 声明改坏 | PASS (0) | FAIL (1) | ✔ True | `:51` `'[2] RULING_D29.md: missing valid q1 line (甲/乙/丙/丁)\r\nFAIL (content)\r\n'`；`check_d29.py:69-70`；矩阵 `:27` |
| d29 | [3] | 「## 7 诚实账」改名 | PASS (0) | FAIL (1) | ✔ True | `:52` `'[3] RULING_D29.md: missing section: 诚实账\r\nFAIL (content)\r\n'`；`check_d29.py:72-74`；矩阵 `:28` |
| d29 | [4] | OR 两词全删（互斥 5 + 前提 2） | PASS (0) | FAIL (1) | ✔ True | `:53` `'[4] Section 冲突是否成立: body must contain 互斥 OR 前提\r\nFAIL (content)\r\n'`；`check_d29.py:76,82-89`；矩阵 `:29` |
| **d29** | **[4b]** | **OR 项只杀一根针：删「前提」(2 处)** | PASS (0) | **PASS (0)** | **✘ False 漏抓** | `:54` `'PASS\r\n'`；`:72` `stdout==A_baseline=True`；矩阵 `:30`；`check_d29.py:76,82-87` |
| d29 | [5] | 删「本次不授权」(2 处) | PASS (0) | FAIL (1) | ✔ True | `:55` `'[5] Section 授权边界: body must contain 本次不授权\r\nFAIL (content)\r\n'`；`check_d29.py:77,83-84`；矩阵 `:31` |
| d29 | [6] | 删 AND 词表「外推」(1 处) | PASS (0) | FAIL (1) | ✔ True | `:56` `'[6] Section 未背书: body must contain 口径 B AND 外推 AND 191\r\nFAIL (content)\r\n'`；`check_d29.py:78,83-84`；矩阵 `:32` |
| d29 | [7] | 52 处引用行号改非数字 | PASS (0) | FAIL (1) | ✔ True | `:57` `'[7] RULING_D29.md: found 0 citations; need at least 8\r\nFAIL (content)\r\n'`；`check_d29.py:90-92`；矩阵 `:33` |
| d29 | [8] | FACTCHECK 删 `selfBias`(6 处) | PASS (0) | FAIL (1) | ✔ True | `:58` `'[8] FACTCHECK.md: missing selfBias\r\nFAIL (content)\r\n'`；`check_d29.py:94-95`；矩阵 `:34` |
| d30 | [1] | 删 `FACTCHECK.md` | PASS (0) | FAIL (2) | ✔ True | `:59` `'[1] Missing file: …\sandbox\d30\inj_1\FACTCHECK.md\r\nFAIL (missing files)\r\n'`；`check_d30.py:59-60,99-101`；矩阵 `:35` |
| d30 | [2] | q1 声明改坏 | PASS (0) | FAIL (1) | ✔ True | `:60` `'[2] RULING_D30.md: missing valid q1 line (甲/乙/丙/丁/戊)\r\nFAIL (content)\r\n'`；`check_d30.py:69-70`；矩阵 `:36` |
| d30 | [3] | 「## 7 诚实账」改名 | PASS (0) | FAIL (1) | ✔ True | `:61` `'[3] RULING_D30.md: missing section: 诚实账\r\nFAIL (content)\r\n'`；`check_d30.py:72-74`；矩阵 `:37` |
| d30 | [4] | OR 两词全删（93.98 3 + 误报率 3） | PASS (0) | FAIL (1) | ✔ True | `:62` `'[4] Section 三档权衡的实质: body must contain 93.98 OR 误报率\r\nFAIL (content)\r\n'`；`check_d30.py:76,82-89`；矩阵 `:38` |
| **d30** | **[4b]** | **OR 项只杀一根针：删「误报率」(3 处)** | PASS (0) | **PASS (0)** | **✘ False 漏抓** | `:63` `'PASS\r\n'`；`:73` `stdout==A_baseline=True`；矩阵 `:39`；`check_d30.py:76,82-87` |
| d30 | [5] | 删「本次不授权」(2 处) | PASS (0) | FAIL (1) | ✔ True | `:64` `'[5] Section 授权边界: body must contain 本次不授权\r\nFAIL (content)\r\n'`；`check_d30.py:77,83-84`；矩阵 `:40` |
| d30 | [6] | 删 AND 词表「外推」(4 处) | PASS (0) | FAIL (1) | ✔ True | `:65` `'[6] Section 未背书: body must contain 外推 AND 栈采样\r\nFAIL (content)\r\n'`；`check_d30.py:78,83-84`；矩阵 `:41` |
| d30 | [7] | 51 处引用行号改非数字 | PASS (0) | FAIL (1) | ✔ True | `:66` `'[7] RULING_D30.md: found 0 citations; need at least 8\r\nFAIL (content)\r\n'`；`check_d30.py:90-92`；矩阵 `:42` |
| d30 | [8] | FACTCHECK 删 `selfBias`(8 处) | PASS (0) | FAIL (1) | ✔ True | `:67` `'[8] FACTCHECK.md: missing selfBias\r\nFAIL (content)\r\n'`；`check_d30.py:94-95`；矩阵 `:43` |

**逐件合取（`_writer_after_console.txt:94-97`、`_ak_BAD_NEEDLE_MATRIX.md:49-52`）**：

| gate | 8 个编号项 `AND_8` | 9 行（含只杀一根针）`AND_9` | 抓到 | 漏抓项 |
|---|---|---|---|---|
| d27 | True | **False** | 8/9 | [6b] 删「卡顿不存在」 |
| d28 | True | **False** | 8/9 | [4b] 删「1681」 |
| d29 | True | **False** | 8/9 | [4b] 删「前提」 |
| d30 | True | **False** | 8/9 | [4b] 删「误报率」 |

**读法**：8 个编号项逐项注射坏针 **32/32 全部被抓**（四件各 8/8），没有一项「根本没在工作」；**唯一漏抓**是每件额外加的第 9 行「OR 项只杀一根针」，四格全部 `注入后仍 PASS / EXIT=0` 且 stdout 与 A 基线逐字相同（`_writer_after_console.txt:69-73`）。这不是「单项检查没工作」，是 OR 语义允许另一根针单独满足 ⇒ `AND_9=False`。
**★ 对称性（原执行件标「未验」，本撰写会话独立实跑补证）**：`python -I -X utf8 ".../_writer_first_needle.py"` → `EXIT=0`，四件 `A / first / second` 三种输入均 `EXIT=0`，`A_vs_first stdout_identical=True`、`A_vs_second stdout_identical=True`，`FIRST_NEEDLE_SYMMETRY_ALL_STILL_PASS = True`（`_writer_first_needle_out.txt`）。即只删第一根针（外推 / 历史数字 / 互斥 / 93.98）四件仍全 PASS ⇒ OR 塌缩对两根针对称，该保守「未验」标注不是缺陷。

**上游脚本侧注射实证对齐（4/4 复现）**：`_ak_repro_out.txt`（本会话实读）四件 `BASE EXIT=0` / `INJ EXIT=0`、`stdout 逐字一致=True stdout_sha256 一致=True EXIT 一致=True 两者均 PASS=True`；`_writer_after_console.txt:94-97` `repro base/inj EXIT=0/0 identical=True both_pass=True`。与 `STALE_PASS_INVENTORY.md:94-101` 登记逐字相符；注射副本 SHA256 在 `_ak_REPRO.md:14-17` 依次为 `f404f58783ab4da0e59ef94afda5bcc97e69d58914465dad2a36769ab5d7af89` / `f5ae184ca7ddc6cfb9965124e26d506992903305aabbdd1a3beb500eb4692314` / `2399e95a43eaafa4ba5409b0850a89e3ed27a0ef345a8f9628bfbf641580ced5` / `b1670537e12a6d7ccc48e636088016a0c482ae00bd3ee5280b810d88af9c7129`。**两种口径不矛盾**：上游改脚本词表里的一个词、输入原件不变 ⇒ 另一根针仍命中、`any()` 必 PASS；本任务 B 输入改的是输入文档，再配 `AND_k` 逐词副本 ⇒ WB 必 FAIL。

---

## 5 四件结论

### 5.1 逐件判定（实质 / 部分空转 / 形式通过）

| 件 | 甲' 口径下的 PASS | 逐件逐格依据 | `AND_8` / `AND_9` | 上游复现 |
|---|---|---|---|---|
| **d27** | **部分空转**（7/8 项真工作，第 [6] 项 OR 半工作） | `check_d27.py:84` `(6, "未背书", ("外推", "卡顿不存在"))` + `:86-87` `any(...)`；B 输入 BASE `EXIT=0` stdout 与 A 逐字同（`_ak_PER_INPUT_TABLE.md:57`），WB `EXIT=1`（`:59`）；矩阵 `[6b]` 漏抓（`_ak_BAD_NEEDLE_MATRIX.md:14`） | True / **False**（8/9） | `_ak_repro_out.txt` d27 能 |
| **d28** | **部分空转**（第 [4] 项 OR 半工作） | `check_d28.py:90` `(4, "D 链处置", ("历史数字", "1681"), False)` + `:97` `any(present)`；`:92` BASE `EXIT=0` 同 A，`:94` WB `EXIT=1`；矩阵 `:21` 漏抓 | True / **False**（8/9） | d28 能 |
| **d29** | **部分空转**（第 [4] 项 OR 半工作） | `check_d29.py:76` `(4, "冲突是否成立", ("互斥", "前提"), False)` + `:82-87` `any(matches)`；`:127` BASE `EXIT=0` 同 A，`:129` WB `EXIT=1`；矩阵 `:30` 漏抓 | True / **False**（8/9） | d29 能 |
| **d30** | **部分空转**（第 [4] 项 OR 半工作） | `check_d30.py:76` `(4, "三档权衡的实质", ("93.98", "误报率"), False)` + `:82-87`；`:162` BASE `EXIT=0` 同 A，`:164` WB `EXIT=1`；矩阵 `:39` 漏抓 | True / **False**（8/9） | d30 能 |

**不是「实质通过」**：B 输入下四件 `AND_k(k=2)=False`、`DISTINGUISHABLE_PASS=False`（§3.3），`AND_9=False`（§4）。
**也不是「形式通过 / 任一项都可单独通过」**：`AND_8=True`（8 个编号项逐项注射 32/32 被抓，删任何一项必需字面量都 `EXIT≠0`）。
按题给三档措辞：**四件均为「部分空转」**——8 项里 7 项真的在工作，1 项是 `any(present)` 二词 OR，在逐输入口径下半工作（另一根针是死输入）。
**出口分支有内容**：`check_d27.py:99-101,107` / `check_d28.py:109-116` / `check_d29.py:101-106` / `check_d30.py:101-106` 三路 `return 2/1/0`；本会话实跑观测到基线 `EXIT=0`、内容注射 `EXIT=1`、缺文件 `EXIT=2`（§4 矩阵 [1] 行）⇒ `EXIT=0` 不是空壳。
**★ 演示外壳 ≠ 门禁可信**：§3.3 的 4/4 `DISTINGUISHABLE_PASS=True` 来自 12 份**改写脚本副本**；原件 `any()` 一次聚合从未被改写（题给【铁律】）。复核回件亦明确此点（题给【复核】「★ 演示外壳 ≠ 门禁可信」）。

### 5.2 与上游注射实证对齐

`STALE_PASS_INVENTORY.md:92` 判据（把 k≥2 输入中的一根换成零命中哨兵、输出仍 PASS 且与基线逐字一致 ⇒ 该 PASS 已证明不可信）、`:94-101` 四组 BASE/INJ 实证、`:107` 7 处 A 级 = 台账 4 行 + 交付件 3 行、`:117` A 级定义「检验本身经坏输入注射实证失效（尺子坏），判的是 PASS 的证据资格，不是结论错」、`:249` 删行会破坏可追溯性、`:251-268` 甲' 方案与两条陷阱（`:255` 漏路径布局得 6 个 `EXIT=2`、`:268` 自认演示外壳非可部署门禁）——本会话逐行实读。
本任务复现 4/4 能（`_ak_repro_out.txt`），并进一步把「杀一根仍 PASS」细化为「8 个编号项 8/8 被抓、但每件额外第 9 行单针漏抓」⇒ 失效面**精确等于那一项 `any()`**，与 `:117` A 级「不是结论错」、`:162` `DETECT_TRIAGE.md:162`「形式要件失效 7 处而实质结论失效 0 处」对齐。

### 5.3 `PENDING:92/105/117/129` 加注文本（四段可直接粘贴；**本任务未真的加注**）

按 `STALE_PASS_INVENTORY.md:249` 保留原行、只加注；`UNTRUSTWORTHY` 取自 `:115-117`；只涉形式要件的证据资格，不重审、不推翻 D-27..D-30 实质裁决（`DETECT_TRIAGE.md:162`）。四段由 Leader 执行，本会话实跑 `ANY_2026_11_09_ANNOTATION = False`、`PENDING_92` 原文逐字未变。

```
★【2026-11-09 甲' 重跑加注 · 由 Leader 登记】本行原「门禁 check_d30.py 实跑 exit=0」仅为
历史事实，指一次「8 项格式/机械检查」的单次聚合运行；其中第 4 项
check_d30.py:76 (4, "三档权衡的实质", ("93.98", "误报率"), False) 为 any(present) 二词 OR。
2026-11-09 实跑（lead/andk_rerun_20261109/ANDK_RERUN.md）：杀掉「误报率」后原件仍
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
2026-11-09 实跑（lead/andk_rerun_20261109/ANDK_RERUN.md）：杀掉「前提」后原件仍
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
2026-11-09 实跑（lead/andk_rerun_20261109/ANDK_RERUN.md）：杀掉「1681」后原件仍
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
2026-11-09 实跑（lead/andk_rerun_20261109/ANDK_RERUN.md）：杀掉「卡顿不存在」后原件仍
EXIT=0、stdout 逐字不变；逐输入 AND_k(k=2) 在 B 输入 = FALSE、DISTINGUISHABLE_PASS = FALSE；
8 个编号项坏针注射 8/8 被抓，「OR 项只杀一根针」漏抓 ⇒ AND_9 = FALSE。
结论：该 PASS 判为「部分空转（7/8 项工作，1 项 OR 半工作）」，标记 UNTRUSTWORTHY；
不得以「已验证 / 逐项通过 / 全绿」身份沿引用链放大，亦不改写或删除本行历史数字。
本加注只涉形式要件的证据资格，不重审、不推翻 D-27 实质裁决（DETECT_TRIAGE.md:162）。
```

---

## 6 复核回件 + 结论 + 未验项

### 6.1 复核回件（verdict 如实记）

编排方下发的【复核】回件 `verdict = "confirmed"`，`ranCommands = 36`（题给【复核】材料）。其 `whatBreaksIt` 逐项写明：① 15 件指纹全等于基线、212 只读文件 `diff=0`；② 自己重跑外壳 selftest/full 得 108 次、产物与预备份逐字节相同；③ 另写 `_akv_own.py` 独立实现 104 次运行，四件 A/B/C 逐格一致，d28 深度坑与沙箱读副本实跑证实；④ 逐格核 36 格矩阵 `PROBLEMS = 0`（`_akv_cells_out.txt:48`），四格「注入后仍 PASS」自己复现；另核对 `_akv_compare_out.txt:52-62` `BINDING_LINES_FOUND = 7` / `STRICT_FORMAT_LINES = 7` / `ALL_BINDING_LINES_MATCH_DISK = True`，`:64-68` 加注措辞 9 项四段全 True，`:75` `ANY_2026-11-09_ANNOTATION_IN_PENDING = False`；⑥ 越界检查 `EXECUTABLE_CODE_VIOLATIONS = 0`、`git log -1` 仍 `2657458`。
**按题给【交付】「复核 verdict 如实记；refuted 或 partial 标 unconfirmed」**：本回件 `verdict = confirmed`，**无需标 unconfirmed**。本撰写会话未发现与之矛盾的实跑结果：我自己重跑 `--mode selftest`（`SELFTEST_PROCESS_EXIT=0`）与 `--mode full`（`FULL_PROCESS_EXIT=0`，108 次，`ORIGINALS_UNCHANGED_AFTER_EVERY_RUN = True`，`READONLY_SNAPSHOT_DIFF = 0`），11 件 `_ak_*` 产物重跑前后逐字节相同（`_writer_after_console.txt:11-12`），36 格矩阵与 12 行逐输入判定逐格复现（`_writer_after_console.txt:31-97`）。

### 6.2 绑定行（固定格式，7 行）

本会话实跑 `python -I -X utf8 ".../_writer_verify.py" after` 用 `hashlib.sha256` 对磁盘逐文件 `read_bytes()` 计算 → `_writer_after_console.txt:2-10` 七行全 `MATCH`、`INPUT_DOCS_MATCH_BASELINE = True`、`ALL_BINDING_LINES_MATCH_DISK = True`。规定格式：**写「被核对象 SHA256 = 」，紧跟完整 64 位十六进制，中间不得插入路径、括号、星号、反引号或空格；随后写「，字节数 = 」再写数字**。

```
被核对象 SHA256 = 3b769d7c64c2725100186439725198dbc134a277914e2cb2e9b0af844fe7671c，字节数 = 3764
被核对象 SHA256 = 5b42a34a40046d7a705776002d7aebe8ffda34248849a75b628d40712d9df268，字节数 = 4539
被核对象 SHA256 = 2a50b09adff555dbce4c5740a2af78b779876cad771b6fdf887ba3c0dc780f14，字节数 = 3906
被核对象 SHA256 = 6cb737963fc62a0e045f51247b4fa57ef190acb0b524da3aa6b7713fd05ee9fd，字节数 = 3926
被核对象 SHA256 = 3765eddbe96deeb65eeb1f05dc81e1dc171e7ea3b2c826e2692a1d15e1c8f2d7，字节数 = 52419
被核对象 SHA256 = 2baa0de45d4125549262eb595d7518c9ce99efeee120384bf640cded8a933ede，字节数 = 759518
被核对象 SHA256 = a72d79b23b1329207a2c612d4244dec407ffaa4e0b91c397c3febb7a9cddd798，字节数 = 63656
```

（依次对应 `check_d27.py` / `check_d28.py` / `check_d29.py` / `check_d30.py` / `PENDING_DECISIONS.md` / `GOAL_THREE_TARGETS_20261018.md` / `STALE_PASS_INVENTORY.md`。八份输入文档 SHA256+字节数逐次运行记录在 `_ak_runs.jsonl:inputs`，值与编排方基线全等；**每次跑完复核原件 SHA256 未变**：`_ak_full_console.txt:2`、四份 guard json 同值 `e8a49546…8e2d31`。）

### 6.3 结论：最小处置设计 / 推广可行性 / 判不了什么

**(a) 最小处置设计（只给设计，本任务不改原件）**

| 件 | 最小改动 |
|---|---|
| d27 | `check_d27.py:81-88` 对 `("外推","卡顿不存在")` 由 `any(...)` 改为要求两词各自独立命中（或拆成两次真实运行再 `AND_k`）；把「两词都删/只删一词」负控写进自检，输出逐词 `input_i: PASS/FAIL` |
| d28 | `check_d28.py:90` 把 `(4, "D 链处置", ("历史数字","1681"), False)` 的 `require_all` 由 `False` 改 `True`；`:98` 提示语改「同时包含」 |
| d29 | `check_d29.py:76` 把 `(4, "冲突是否成立", ("互斥","前提"), False)` 改 `True`；注意 `:82-87` `any(matches)` 是「任一小节副本满足」，多 body 仍须逐词独立验证 |
| d30 | `check_d30.py:76` 把 `(4, "三档权衡的实质", ("93.98","误报率"), False)` 改 `True`；同上处理 `any(matches)` |

共同要求（`STALE_PASS_INVENTORY.md:257-261,388-399`）：① 每个词一根真实独立运行，`AGGREGATE = AND_k(rc==0 ∧ 含 PASS ∧ 无 FAIL)`；② 每根针各换一次零命中哨兵，要求 `AGGREGATE` 变 FAIL；③ 输出 `input_i: PASS/FAIL` + `DISTINGUISHABLE_PASS`；④ 绑定「被核脚本 SHA256+字节数 + 逐输入文档 SHA256+字节数 + 命令全文 + stdout sha256」；⑤ `HITSET / MASKED_LINES / EXCLUSIVE(k)` 只作诊断量，不得替代 `AND_k`；⑥ 门禁/诊断分离；⑦ 单调性对照（本四件不依赖 `min/argmin`）；⑧ 未验项逐条写「未验」。`python -I -X utf8` + 绝对路径 + 三套路径布局（§2.2）必须随改一并固化。**前置**：`STALE_PASS_INVENTORY.md:267` 的 `--include-refuting` 口径陷阱只影响 carrier scanner 侧，本四件登记口径无此参数；改动后**必须跑修复后回归**（本任务未跑，见 (c) 第 6 条）。

**(b) 推广可行性与成本**

**可行性 = 部分可行，不能整体套用。** 同族（`check_d*.py` 格式门禁、同类 OR 词表、同类三套布局）：`Layout` / `script_bytes` / `make_docs` / `do_run` 可参数化复用，只换 `GATES` 配置（`_ak_shell.py:65-78`）；分诊 `DETECT_TRIAGE.md:166` 记 `check_*.py` 全库 **173 件**，`STALE_PASS_INVENTORY.md:107` 记两账另约 **~170 行** PASS 类未逐条注射实证。异质件（`STALE_PASS_INVENTORY.md:245` 明记其余 ~170 行是真机/编译/单测/工作流门槛/历史观测异质混合；`DETECT_TRIAGE.md:179-180` 点名 `_rs_carrier_scan.py` 的 `--needle` / `min/argmin` 反向掩蔽、`PENDING:162/186/199` 三行 C 级）：「k 个输入」不是源码词表而是命令行参数/语料/扫描目标 ⇒ 必须重定义 k、重写生成器与布局，**本外壳不能照搬**，且 `:267` 记照抄模板会引入第三套口径。
**成本（本会话实跑数据）**：四件共 **108 次真实 subprocess 运行**（`_writer_after_console.txt:13-14` 的 TAG_COUNTS 逐项相加：12+12+12+12+36+4+4+4+12 = 108），`_ak_shell.py` 单条命令完成；控制台 854 B、逐次记录 197059 B；另 1 次自检（3 运行）。按此单位线性外推到 173 件同族门禁约 173/4 × 108 ≈ **4671 次**只读执行（**线性外推、未按单件实跑验证，记为估算**）；异质件另需逐件定义 k 与布局，成本**未验**。`DETECT_TRIAGE.md:173` 记上游「约 10–30 分钟人工/脚本编排」是估算且本会话未计时 ⇒ **不给秒数、不给异质件工时**。

**(c) 判不了什么（10 条，如实列）**

1. **判不了 D-27..D-30 实质结论的对错**。四件自述「格式/机械检查」（`check_d27.py:1` / `check_d28.py:1` / `check_d29.py:1` / `check_d30.py:1`），`DETECT_TRIAGE.md:162` 与 `STALE_PASS_INVENTORY.md:196,219-220` 明记「形式要件失效 7 处而实质结论失效 0 处」。本任务只判 **PASS 的证据资格**。
2. **判不了其余 ~170 行 PASS 类、173 件 `check_*.py`、carrier scanner、`PENDING:162/186/199` 的可信性**：只跑了题给四件，其余**未验**（`STALE_PASS_INVENTORY.md:107`、`DETECT_TRIAGE.md:179-180`）。
3. **判不了 2026-11-06/11-07 历史实跑的当时输入与口径**：本任务绑的是**当前盘**输入指纹（与编排方基线全等）；`STALE_PASS_INVENTORY.md:139` 记输入未变，但本会话没有独立取证历史时点文件字节 ⇒ **未验**。
4. **判不了语义正确性**：全部检查是字面量/正则/标题/计数，`check_d27.py:18` `REFERENCE` 只数 `file:line` 形状，不校验引用是否真实存在或内容相符。
5. **判不了真机/运行时/性能/扰动**：零真机、零采样代码（题给铁律）；`PENDING:97` 自记 Q5 扰动 `verified=false` ⇒ 不在本任务范围。
6. **判不了「改了之后会不会引入新问题」**：§6.3(a) 只给设计，未改原件、未跑修复后回归（`STALE_PASS_INVENTORY.md:268,361` 同记上游演示「未部署成门禁、未跑修复后回归」）。
7. **判不了 `AND_k=True` 就等于门禁可信**：§3.3 的 4/4 `DISTINGUISHABLE_PASS=True` 来自**改写后的副本**，原件 `any(present)` 从未被改写（题给【铁律】）。
8. **判不了台账加注的执行**：两件台账绝对只读，本任务未加注、未 commit、未 push；§5.3 文本仅供 Leader 粘贴（本会话实跑 `ANY_2026_11_09_ANNOTATION = False`）。
9. **判不了「杀第一根针」的对称性 —— 本撰写会话已补证，不再是未验**：原执行件 `_ak_REPORT.md:483-485` 标「未验」；本会话 `python -I -X utf8 ".../_writer_first_needle.py"` → `FIRST_NEEDLE_SYMMETRY_ALL_STILL_PASS = True`，四件只删第一根针仍 `EXIT=0` 且 stdout 与 A 逐字相同（`_writer_first_needle_out.txt`）。**如实记为已验**，不沿用旧「未验」措辞。
10. **判不了 d29/d30 `any(matches)` 多 body 情形**：`check_d29.py:81-87` / `check_d30.py:81-87` 对同名标题的多个 body 取 `any(matches)`；本会话未构造「同标题多小节」输入做实跑 ⇒ **未验**。

### 6.4 未验项汇总（本节显式列出，便于 Leader 沿引用链核对）

- **未验**：历史时点（2026-11-06/11-07）输入字节与口径；其余 ~170 行 / 173 件 / carrier scanner / `PENDING:162/186/199` 的可信性；修复后回归；d29/d30 同标题多 body 分支；异质件推广工时；173 件外推成本（线性估算，未单件实跑）。
- **已验但不得放大**：12 份逐词副本 `DISTINGUISHABLE_PASS=True`（改写副本，非原件门禁可信）；A 输入四件 `BASE` 8/8 全过（真实结果，但 B 输入同样 8/8 全过且输出逐字不变）。
- **本撰写会话新补证**：第一根针对称性（4/4 仍 PASS）、d28 `parents[2]` 深度坑（depth=3 PASS / depth=2,1 `EXIT=2`）、外壳 108 次重跑可复现且 11 件产物逐字节不变、7 行绑定行与 212 只读文件全量快照未变。
- **未执行**：真给台账加注（Leader 权限）、修改四件门禁、commit / push、任何真机或采样代码。
