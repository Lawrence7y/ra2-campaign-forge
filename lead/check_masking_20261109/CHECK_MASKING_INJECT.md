# CHECK_MASKING_INJECT.md — 坏输入注入审计（check_d27 / check_d29 / check_d30）

回件日期 2026-11-09 · 角色：注入审计件撰写员 · 唯一写域 `lead/check_masking_20261109/`
零真机 / 零采样代码 / 绝对只读被审件 / 不 commit 不 push / Python 一律 `python -I -X utf8` + 绝对路径 / 指纹用 `hashlib`。

本回件的每一条判词都锚定「本会话实跑命令 + 输出原文」或「文件:行」。凡只从上游材料继承、本会话未重跑的，逐处标「直读/未重跑」；凡本会话拿不到的，标「未验」，不补造。

---

## 1 目的与边界

**目的**：对编排方点名的三件自检脚本 `check_d27.py` / `check_d29.py` / `check_d30.py` 做**坏输入注入**，判定它们是否与第四件 `lead/refsync_scope_20261109/_rs_carrier_scan.py` 同属「k 个输入压成 1 bit」缺陷；给出共有模式、一次性修复方案、修复优先级与项目整体含义。

**★ 边界铁律（本回件自我约束）**：

1. **只做注入审计，不改任何被审脚本一个字节**。坏输入只在**临时副本 / CLI 参数层**注入：三 gate 用写域内 `_cm_tmp/` / `_cmv_tmp/` / `_cmd_tmp/` 的逐字节副本替换字面量；扫描器用 `--needle` 参数注入坏针。源文件零字节改动（§6 有前后 hashlib 自证）。
2. **零真机**：未启动 `gamemd.exe` / `ra2loader` / `YURI.exe`，未 `taskkill`，未读活进程内存。
3. **零采样代码**：未写 hook / MiniDump / SuspendThread / StackWalk / 探针注入 / 动态内存解析。
4. **绝对只读**：`lead/masking_effect_20261109/` 全部件、被点名的 `check_d27/d29/d30` 及其所在写域、`lead/refsync_scope_20261109/_rs_carrier_scan.py`、任何既有自检脚本，一律不修改、不追加、不覆盖。
5. 唯一写域 = `lead/check_masking_20261109/`；本回件新增件前缀 `_cmd_`（外加交付件 `CHECK_MASKING_INJECT.md`）。
6. 不 commit、不 push（`git log -1 --oneline` 本会话实跑仍为 `2657458`，见 §6）。

**被审四件**：三 gate（本次注入主对象）+ `_rs_carrier_scan.py`（第四件，用于 4/4 计数与对照；参数层注入，不改源）。

**用语约定**：下文「压成 1 bit」一律指 `any()` / `ok &= good` / `min(pos)` 把 k≥2 个输入的存活情况合成单一布尔，最终只输出一行 `PASS`/`SELF_TEST = PASS`。

---

## 2 上游指纹（四件）+ 三件定位与结构核查

### 2.1 上游指纹（四件）+ 被审件指纹 — 本会话 hashlib 独立实算

实跑命令（本会话，repo root）：

```
python -I -X utf8 -c "
import hashlib, pathlib
files = [
 'lead/d27_ruling_20261106/check_d27.py',
 'lead/d29_ruling_20261106/check_d29.py',
 'lead/d30_ruling_20261106/check_d30.py',
 'lead/refsync_scope_20261109/_rs_carrier_scan.py',
 'lead/masking_effect_20261109/_me_REPORT.md',
 'lead/masking_effect_20261109/MASKING_EFFECT_AUDIT.md',
 'lead/PENDING_DECISIONS.md',
 'lead/GOAL_THREE_TARGETS_20261018.md',
]
for f in files:
    p = pathlib.Path('D:/Project/ra2-campaign-forge') / f
    b = p.read_bytes()
    print('%s bytes=%d sha256=%s' % (f, len(b), hashlib.sha256(b).hexdigest()))
"
```

输出原文：

```
lead/d27_ruling_20261106/check_d27.py bytes=3764 sha256=3b769d7c64c2725100186439725198dbc134a277914e2cb2e9b0af844fe7671c
lead/d29_ruling_20261106/check_d29.py bytes=3906 sha256=2a50b09adff555dbce4c5740a2af78b779876cad771b6fdf887ba3c0dc780f14
lead/d30_ruling_20261106/check_d30.py bytes=3926 sha256=6cb737963fc62a0e045f51247b4fa57ef190acb0b524da3aa6b7713fd05ee9fd
lead/refsync_scope_20261109/_rs_carrier_scan.py bytes=16053 sha256=9ccca808d52f44aaee895e30f9a84f6f3b6ae5ee292ea71281e2b46e627a1c57
lead/masking_effect_20261109/_me_REPORT.md bytes=33313 sha256=7fb133c682e08af29b3de58bdd58819312a1d3036a07d7c5eb5ec0be5bf347ac
lead/masking_effect_20261109/MASKING_EFFECT_AUDIT.md bytes=45536 sha256=2f55283ef3380c6cb5915b2e8654a5506061ccb667a986d397b45a10a2f9119f
lead/PENDING_DECISIONS.md bytes=52419 sha256=3765eddbe96deeb65eeb1f05dc81e1dc171e7ea3b2c826e2692a1d15e1c8f2d7
lead/GOAL_THREE_TARGETS_20261018.md bytes=759518 sha256=2baa0de45d4125549262eb595d7518c9ce99efeee120384bf640cded8a933ede
```

**编排方【定位】给的「上游指纹四件」**（`_me_REPORT.md` 33313 / `7fb133c6…`、`MASKING_EFFECT_AUDIT.md` 45536 / `2f55283e…`、`PENDING_DECISIONS.md` 52419 / `3765eddb…`、`GOAL_THREE_TARGETS_20261018.md` 759518 / `2baa0de4…`）—— 与上列实算 **4/4 MATCH**（依据：本会话上列输出 + 编排方 `fp` 字段）。

**编排方【定位】给的三件 16 位前缀** `3b769d7c64c27251` / `2a50b09adff555db` / `6cb737963fc62a0e`，与本次完整 64 位实算一致；字节数 3764 / 3906 / 3926 一致（`lead/check_masking_20261109/_cm_injection_out.txt:6-9` 为撰写人实跑件，本会话直读复核一致）。

### 2.2 三件定位（路径 / 大小 / 指纹）

| 件 | 路径（本会话直读） | bytes | sha256（完整） |
|---|---|---|---|
| check_d27 | `lead/d27_ruling_20261106/check_d27.py` | 3764 | `3b769d7c64c2725100186439725198dbc134a277914e2cb2e9b0af844fe7671c` |
| check_d29 | `lead/d29_ruling_20261106/check_d29.py` | 3906 | `2a50b09adff555dbce4c5740a2af78b779876cad771b6fdf887ba3c0dc780f14` |
| check_d30 | `lead/d30_ruling_20261106/check_d30.py` | 3926 | `6cb737963fc62a0e045f51247b4fa57ef190acb0b524da3aa6b7713fd05ee9fd` |

三件各自位于裁决域 `lead/dNN_ruling_20261106/`，与两份输入文档 `RULING_DNN.md` / `FACTCHECK.md` 同目录（本会话 `ls -la` 实见）。它们的 PASS 是台账的承重证据：`lead/PENDING_DECISIONS.md:129`（D-27）、`:105`（D-29）、`:92`（D-30）三处都写着「门禁 `check_dNN.py` 实跑 **exit=0**」（本会话 `grep -n -E "check_d(27|29|30)|门禁|exit=0" lead/PENDING_DECISIONS.md` 实跑确认）。

### 2.3 结构核查：SELF_TEST / any / all / min

编排方给的【自检结构】是空对象 `{}`。本会话独立补齐。实跑命令：

```
grep -n -E "SELF_TEST|any\(|all\(|min\(|&=\|sys\.exit|SystemExit|return [0-9]|PASS|FAIL" lead/d27_ruling_20261106/check_d27.py
grep -n -E "SELF_TEST|any\(|all\(|min\(|&=\|sys\.exit|SystemExit|return [0-9]|PASS|FAIL" lead/d29_ruling_20261106/check_d29.py
grep -n -E "SELF_TEST|any\(|all\(|min\(|&=\|sys\.exit|SystemExit|return [0-9]|PASS|FAIL" lead/d30_ruling_20261106/check_d30.py
grep -n -E "SELF_TEST|any\(|all\(|min\(|&=\|sys\.exit|SystemExit|return [0-9]|PASS|FAIL|--needle|NEVER writes" lead/refsync_scope_20261109/_rs_carrier_scan.py
```

输出原文（节选，压缩点 + 汇总出口）：

```
=== d27 structure ===
86:        if not any(keyword in body for body in bodies.get(title, [])
100:    print(f"PASS: D-27 八项机械检查通过；裁决书引用 {count} 处")
101:    return 0
=== d29 structure ===
83:                all(word in body for word in words) if require_all
84:                else any(word in body for word in words)
87:            if not any(matches):
105:    print("PASS")
106:    return 0
110:    raise SystemExit(main())
=== d30 structure ===
83:                all(word in body for word in words) if require_all
84:                else any(word in body for word in words)
87:            if not any(matches):
105:    print("PASS")
106:    return 0
110:    raise SystemExit(main())
=== rs scanner structure ===
7:script NEVER writes a file (redirect stdout to the write domain if a record
165:    pos = min((line.find(n) for n in needles if n in line), default=-1)
194:    ap.add_argument("--needle", action="append", required=True)
229:        if not any(n in txt for n in a.needle):
345:              ("PASS" if good else "FAIL", rel, n, want, got))
346:        P("SELF_TEST = %s" % ("PASS" if ok else "FAIL"))
349:    return 0 if ok else 1
```

本会话另实跑 `grep -n -c -F "SELF_TEST"` 得 **d27/d29/d30 = 0 / 0 / 0，scanner = 1**（§4 的 30 秒判据第 3 步输出），即：

- **三件都没有字面 `SELF_TEST` 汇总行，也都没有 `min()`**；汇总就是末行 `print("PASS")`（d29/d30 `check_d29.py:105` / `check_d30.py:105`）或 `print("PASS: …")`（`check_d27.py:100`）+ `return 0` / `sys.exit(main())`。编排方的 `{}` 不是「无结构」，而是「无 `SELF_TEST` 记号」；本回件用「PASS 行」当等价汇总位。
- **三件都有 `any()`**：d27 `check_d27.py:86-88` 是「body × keyword 双重存在量词」，OR 词表 `("外推","卡顿不存在")` 在 `check_d27.py:84`；d29/d30 `check_d29.py:82-89` / `check_d30.py:82-89` 是内层 `any(word in body …)` + 外层 `if not any(matches)` 的**双层 OR**，OR 词表分别 `("互斥","前提")`（`check_d29.py:76`）与 `("93.98","误报率")`（`check_d30.py:76`）。
- **`all()` 只在 d29/d30 的 `require_all=True` 分支**（`check_d29.py:83` / `check_d30.py:83`），d27 没有。
- 第四件 scanner 独有 `min(pos)`（`_rs_carrier_scan.py:165`）、`any(n in txt …)`（`:229`）、`ok &= good`（`:343`，本会话直读）、单 `SELF_TEST`（`:346`）与 `return 0 if ok else 1`（`:349`）。

### 2.4 是否逐输入可归因

**结论：三件都是「逐检查项可归因」，但「逐输入可归因」= 没有，三件都不是。**

依据（本会话直读源码）：

- `check_d27.py:58,67,70,74,79,88,92,94` 用 `errors.append(...)` 逐项累积 8 条；`check_d27.py:96-101` 汇总 `if errors: … return 1` / `print("PASS") return 0`。`check_d29.py:62,65,70,74,89,92,95` / `check_d29.py:97-106` 与 `check_d30.py`（逐行同构）同理。FAIL 时会打印 `[4] …` / `[6] …` 编号 → **逐检查项可归因**。
- 但每个 `require_all=False` 检查项内部把 k≥2 个词用 `any()` 合成 `covered = ∃w ∈ words: w in body`，只 append 一条「须包含 A 或 B」。**哪根词死了、哪根活着，输出里完全没有**。这就是「压成 1 bit」的有损压缩；与 `_rs_carrier_scan.py:229` 的 `any(n in txt …)` + `:343` `ok &= good` + `:346` 单 `SELF_TEST` 同形。
- `require_all=True` 分支内层是 `all(...)`：删任一必需词该项必 FAIL（本会话负控实证，见 §3），对「词是否存活」**敏感**；但它同样**不打印逐词存活状态**，只是整项 FAIL。即「逐项敏感、逐词不可见」。
- 编排方【复核】①(d) 的判定与本节一致：本次直读 `check_d27.py:81-88` / `check_d29.py:75-89` / `check_d30.py:75-89` 确认 `_cm_AUDIT.md:130-133`「逐输入：没有，三件都不是」正确。

**局部如实补充**：三件是「8 个 1-bit 检查并列」，比 scanner 的「6 条负控塞进同一个 `ok`（`_rs_carrier_scan.py:343`）」粒度更好；但**目标 OR 项本身没有任何改进**，坏针依旧不可见（§3 实证）。

---

## 3 逐件坏输入注入（完整命令与输出原文）

### 3.1 注入设计（不改源文件一个字节）

- **哨兵**：`TOTALLY_BROKEN_NEEDLE_SENTINEL_XYZ`（保证零命中，与背景材料同串）。
- **A 族（文档侧）**：把裁决书**副本**里某个词换成哨兵，OR 兄弟词保持存活 → 制造「一根输入失效、其余正常」。
- **B 族（脚本侧临时副本）**：把脚本**副本**里 OR 词表的一个字面量换成哨兵，其余 7 项检查一字不动 → scanner「坏 needle」在三 gate 上的等价物。
- **沙箱**：逐字节复制 gate 脚本 + 两份文档到写域内 `_cm_tmp/<tag>/<slug>/`（撰写人）或 `_cmv_tmp/`（复核人）/ `_cmd_tmp/`（本会话），`subprocess` 以 `cwd=沙箱` 跑；写入 `resolve()` 限制在写域内（`lead/check_masking_20261109/_cm_inject.py:43-49`，本会话直读）。
- **d27 特有坑**：`check_d27.py:8` 用 CWD 相对 `DIRECTORY = Path("lead/d27_ruling_20261106")`，沙箱内须另建同名子目录放文档；`check_d29.py:50` / `check_d30.py:50` 用 `Path(__file__).resolve().parent`，副本同目录即命中。撰写人第一次驱动漏此点致 6 个 d27 场景 `EXIT=2 文件缺失`，**已判无效运行、作废重跑**（`_cm_AUDIT.md:143`，本会话直读）；结论只取第二次输出。
- **19 场景矩阵**：撰写人驱动 `lead/check_masking_20261109/_cm_inject.py` 的实跑输出在 `_cm_injection_out.txt:1-186`（本会话**直读**该输出件，**未重跑驱动**）。本会话另用 `lead/check_masking_20261109/_cmv_repro.py` **独立重跑**三件 B 族 headline + A 族 + 负控（见 3.3），输出落 `_cmd_repro_out.txt`。

**基线（本会话实跑，未注入、repo root）**：

```
$ python -I -X utf8 "D:/Project/ra2-campaign-forge/lead/d27_ruling_20261106/check_d27.py"
PASS: D-27 八项机械检查通过；裁决书引用 71 处
EXIT=0
$ python -I -X utf8 "D:/Project/ra2-campaign-forge/lead/d29_ruling_20261106/check_d29.py"
PASS
EXIT=0
$ python -I -X utf8 "D:/Project/ra2-campaign-forge/lead/d30_ruling_20261106/check_d30.py"
PASS
EXIT=0
```

### 3.2 三分类口径（先定义，避免歧义）

按「注入后能观测到什么」划分三分类：

| 类 | 定义 | 本次计数 |
|---|---|---|
| **FAIL** | 注入被抓到：`EXIT≠0` 且打印 `FAIL`/`[n]` 编号 | 撰写人 19 场景中 **5**（d27 `neg_ctrl` 1；d29 `neg_ctrl_all`+`and_kill_1` 2；d30 `neg_ctrl_all`+`and_kill_1` 2） |
| **仍PASS** | 注入被掩蔽：`EXIT=0` 且打印 `PASS` | 撰写人 19 场景中 **14**（`_cm_injection_out.txt:222-224` 的 `injected scenarios = 19 / still EXIT=0 (PASS) = 14`，本会话直读）；本会话独立重跑另 4 例仍PASS |
| **无自检** | **结构类**：该件没有 `SELF_TEST` 行、没有负控表、没有逐输入打印行，其 PASS 只是一行裸布尔，无法从输出判断哪根输入死了 | 三 gate **全件**属于此类（§2.3 `grep -c` = 0/0/0）；scanner 有 1 个 `SELF_TEST` 行但 6 条负控压成同一布尔，属「有自检名、无逐输入自检实」 |

如实说明：**本次没有任何场景落到「无输出 / 无法判定」**——22 个撰写人场景（19 注入 + 3 control）与 5 个本会话重跑场景全部拿到完整 stdout + EXIT。「无自检」是**结构/可观测性**类，与「仍PASS」重叠：三 gate 的「仍PASS」正是「无自检件的一行 PASS」。

### 3.3 ★ 三件逐件：注入后仍 PASS，完整命令与输出原文

以下每件先给**本会话独立重跑**的完整命令与输出（来源 `lead/check_masking_20261109/_cmd_repro_out.txt`，命令 `python -I -X utf8 D:/Project/ra2-campaign-forge/lead/check_masking_20261109/_cmv_repro.py`），再给撰写人驱动内嵌的**不缩写** CMD/CWD/EXIT/输出原文（`_cm_injection_out.txt` 直读），最后给该件 FAIL 负控原文。三件**逐件**列出，不以「同样缺陷」概括。

#### 3.3.1 check_d27.py（3764 B，sha `3b769d7c…`）

缺陷点 `check_d27.py:86-88`「`if not any(keyword in body for body in bodies.get(title, []) for keyword in keywords)`」，OR 词表 `check_d27.py:84` `("外推","卡顿不存在")`，汇总 `check_d27.py:100` 单行 PASS。

注入：脚本副本 `'"卡顿不存在"'` → `'"TOTALLY_BROKEN_NEEDLE_SENTINEL_XYZ"'`（occurrences 1→0，副本 sha `3b769d7c64c27251…` → `f404f58783ab4da0…`）。

**完整命令与输出原文（本会话独立重跑，输出 `_cmd_repro_out.txt`）：**

```
[d27] v_b_kill_2: kill 2nd OR word '卡顿不存在' in script tuple
  copy mutation: '"卡顿不存在"' -> '"TOTALLY_BROKEN_NEEDLE_SENTINEL_XYZ"'; occurrences 1 -> 1
  copy sha256 = 3b769d7c64c2725100186439725198dbc134a277914e2cb2e9b0af844fe7671c -> f404f58783ab4da0e59ef94afda5bcc97e69d58914465dad2a36769ab5d7af89  bytes = 3764 -> 3783
  CMD = C:\Users\Administrator\AppData\Local\Programs\Python\Python312\python.exe -I -X utf8 D:\Project\ra2-campaign-forge\lead\check_masking_20261109\_cmv_tmp\d27\v_b_kill_2\check_d27.py
  CWD = D:\Project\ra2-campaign-forge\lead\check_masking_20261109\_cmv_tmp\d27\v_b_kill_2
  EXIT = 0
  | PASS: D-27 八项机械检查通过；裁决书引用 71 处
  VERDICT = STILL_PASS (masked)
```

**完整命令与输出原文（撰写人驱动内嵌，不缩写，`_cm_injection_out.txt:35-41`）：**

```
==============================================================================
[d27] B: script tuple -> ('外推', SENTINEL)
  SCRIPT check_d27.py: '"卡顿不存在"' -> '"TOTALLY_BROKEN_NEEDLE_SENTINEL_XYZ"'; occurrences 1 -> 0; bytes 3764 -> 3783; sha256 3b769d7c64c27251 -> f404f58783ab4da0
  CMD = C:\Users\Administrator\AppData\Local\Programs\Python\Python312\python.exe -I -X utf8 D:\Project\ra2-campaign-forge\lead\check_masking_20261109\_cm_tmp\d27\b_kill_2\check_d27.py
  CWD = D:\Project\ra2-campaign-forge\lead\check_masking_20261109\_cm_tmp\d27\b_kill_2
  EXIT = 0
  | PASS: D-27 八项机械检查通过；裁决书引用 71 处
```

本会话还重跑了撰写人自己的副本（`_cmd_repro_out.txt` PART 2）：`copy sha256 = f404f587…d7af89`、`EXIT = 0`、`| PASS: D-27 八项机械检查通过；裁决书引用 71 处`。

A 族（文档侧杀 `卡顿不存在`，`_cm_injection_out.txt:28-33` / 本会话 `_cmv_repro.py` PART 3 重跑）：

```
=== PART 3: A-FAMILY (DOC-side) fresh sandbox, d27 kill sole '卡顿不存在' ===
  DOC mutation: '卡顿不存在' occurrences 1 -> 0; bytes 17658 -> 17677
  CMD = C:\Users\Administrator\AppData\Local\Programs\Python\Python312\python.exe -I -X utf8 D:\Project\ra2-campaign-forge\lead\check_masking_20261109\_cmv_tmp\d27\v_a_kill_2\check_d27.py
  CWD = D:\Project\ra2-campaign-forge\lead\check_masking_20261109\_cmv_tmp\d27\v_a_kill_2
  EXIT = 0
  | PASS: D-27 八项机械检查通过；裁决书引用 71 处
```

**杀光 `卡顿不存在` 后输出一字不变**（连引用计数 71 都不漂移）。另 `_cm_injection_out.txt:20-25`（杀 `外推`）、`:43-49`（杀 `外推` 换哨兵）亦全 `EXIT = 0` / PASS。

**FAIL 负控原文（`_cm_injection_out.txt:52-57`）—— 证明源不是假 PASS：**

```
==============================================================================
[d27] NEG-CONTROL: kill sole keyword '循环论证' of check [4]
  DOC RULING_D27.md: '循环论证' -> 'TOTALLY_BROKEN_NEEDLE_SENTINEL_XYZ' x1; occurrences 1 -> 0; bytes 17658 -> 17680
  CMD = C:\Users\Administrator\AppData\Local\Programs\Python\Python312\python.exe -I -X utf8 D:\Project\ra2-campaign-forge\lead\check_masking_20261109\_cm_tmp\d27\neg_ctrl\check_d27.py
  CWD = D:\Project\ra2-campaign-forge\lead\check_masking_20261109\_cm_tmp\d27\neg_ctrl
  EXIT = 1
  | FAIL [4] 新证据是否成立小节正文须包含: 循环论证
```

⇒ **check_d27 定性：坏掉一根 OR 词针仍 PASS（`EXIT=0`，输出逐字不变）；单元素词表项能抓，OR 项抓不到。无自检件。**

#### 3.3.2 check_d29.py（3906 B，sha `2a50b09a…`）

缺陷点 `check_d29.py:82-87` 内层 `any(word in body …)` + 外层 `if not any(matches)`（双层 OR），OR 词表 `check_d29.py:76` `("互斥","前提")`，汇总 `check_d29.py:105` `print("PASS")`。

注入：脚本副本 `'"前提"'` → `'"TOTALLY_BROKEN_NEEDLE_SENTINEL_XYZ"'`（occurrences 1→0，副本 sha `2a50b09adff555db…` → `2399e95a43eaafa4…`）。

**完整命令与输出原文（本会话独立重跑，输出 `_cmd_repro_out.txt`）：**

```
[d29] v_b_kill_2: kill 2nd OR word '前提' in script tuple
  copy mutation: '"前提"' -> '"TOTALLY_BROKEN_NEEDLE_SENTINEL_XYZ"'; occurrences 1 -> 1
  copy sha256 = 2a50b09adff555dbce4c5740a2af78b779876cad771b6fdf887ba3c0dc780f14 -> 2399e95a43eaafa4ba5409b0850a89e3ed27a0ef345a8f9628bfbf641580ced5  bytes = 3906 -> 3934
  CMD = C:\Users\Administrator\AppData\Local\Programs\Python\Python312\python.exe -I -X utf8 D:\Project\ra2-campaign-forge\lead\check_masking_20261109\_cmv_tmp\d29\v_b_kill_2\check_d29.py
  CWD = D:\Project\ra2-campaign-forge\lead\check_masking_20261109\_cmv_tmp\d29\v_b_kill_2
  EXIT = 0
  | PASS
  VERDICT = STILL_PASS (masked)
```

**完整命令与输出原文（撰写人驱动内嵌，不缩写，`_cm_injection_out.txt:84-89`）：**

```
==============================================================================
[d29] B: script tuple -> ('互斥', SENTINEL)
  SCRIPT check_d29.py: '"前提"' -> '"TOTALLY_BROKEN_NEEDLE_SENTINEL_XYZ"'; occurrences 1 -> 0; bytes 3906 -> 3934; sha256 2a50b09adff555db -> 2399e95a43eaafa4
  CMD = C:\Users\Administrator\AppData\Local\Programs\Python\Python312\python.exe -I -X utf8 D:\Project\ra2-campaign-forge\lead\check_masking_20261109\_cm_tmp\d29\b_kill_2\check_d29.py
  CWD = D:\Project\ra2-campaign-forge\lead\check_masking_20261109\_cm_tmp\d29\b_kill_2
  EXIT = 0
  | PASS
```

A 族 `_cm_injection_out.txt:76-81` 把全文 5 处 `互斥` **全杀光**、只剩 `前提` 一根活针，仍：

```
[d29] A: kill ALL '互斥' in 冲突是否成立, sibling '前提' alive
  DOC RULING_D29.md: '互斥' -> 'TOTALLY_BROKEN_NEEDLE_SENTINEL_XYZ' x99; occurrences 5 -> 0; bytes 12258 -> 12398
  CMD = C:\Users\Administrator\AppData\Local\Programs\Python\Python312\python.exe -I -X utf8 D:\Project\ra2-campaign-forge\lead\check_masking_20261109\_cm_tmp\d29\a_kill_2\check_d29.py
  CWD = D:\Project\ra2-campaign-forge\lead\check_masking_20261109\_cm_tmp\d29\a_kill_2
  EXIT = 0
  | PASS
```

（与 scanner 单 N2 一根 6/6 PASS 完全同构。）另 `_cm_injection_out.txt:68-73`（杀 `前提`）、`:92-97`（杀 `互斥` 换哨兵）亦全 `EXIT = 0` / `PASS`。

**FAIL 负控原文（本会话 `_cmv_repro.py` PART 4 独立重跑，`_cmd_repro_out.txt`）：**

```
=== PART 4: NEG-CONTROL (d29 AND-path must FAIL when all '191' killed) ===
  DOC mutation: '191' occurrences 9 -> 0
  CMD = C:\Users\Administrator\AppData\Local\Programs\Python\Python312\python.exe -I -X utf8 D:\Project\ra2-campaign-forge\lead\check_masking_20261109\_cmv_tmp\d29\v_neg_ctrl_all\check_d29.py
  EXIT = 1
  | [3] RULING_D29.md: missing section: :191 的适用边界
  | [6] Section 未背书: body must contain 口径 B AND 外推 AND 191
  | FAIL (content)
```

撰写人同场景 `_cm_injection_out.txt:108-115` 输出一致；另有 `and_kill_1`（`_cm_injection_out.txt:118-124`）、`neg_ctrl`（`:100-105`，只杀 1 处 `191`，仍 `EXIT = 0` / `PASS`）。

⇒ **check_d29 定性：坏掉一根 OR 词针仍 PASS；`require_all=True` 的 `all()` 项（删光必需词）能出 FAIL 并打印 `AND` 词表，但同样不打印逐词存活状态。无自检件。**

#### 3.3.3 check_d30.py（3926 B，sha `6cb73796…`）

缺陷点 `check_d30.py:82-87` 与 d29 **逐行同构**（`check_d30.py:75-89`、`check_d30.py:97-106` 结构相同，只换词表与标题），OR 词表 `check_d30.py:76` `("93.98","误报率")`，汇总 `check_d30.py:105` `print("PASS")`。

注入：脚本副本 `'"误报率"'` → `'"TOTALLY_BROKEN_NEEDLE_SENTINEL_XYZ"'`（occurrences 1→0，副本 sha `6cb737963fc62a0e…` → `b1670537e12a6d7c…`）。

**完整命令与输出原文（本会话独立重跑，输出 `_cmd_repro_out.txt`）：**

```
[d30] v_b_kill_2: kill 2nd OR word '误报率' in script tuple
  copy mutation: '"误报率"' -> '"TOTALLY_BROKEN_NEEDLE_SENTINEL_XYZ"'; occurrences 1 -> 1
  copy sha256 = 6cb737963fc62a0e045f51247b4fa57ef190acb0b524da3aa6b7713fd05ee9fd -> b1670537e12a6d7ccc48e636088016a0c482ae00bd3ee5280b810d88af9c7129  bytes = 3926 -> 3951
  CMD = C:\Users\Administrator\AppData\Local\Programs\Python\Python312\python.exe -I -X utf8 D:\Project\ra2-campaign-forge\lead\check_masking_20261109\_cmv_tmp\d30\v_b_kill_2\check_d30.py
  CWD = D:\Project\ra2-campaign-forge\lead\check_masking_20261109\_cmv_tmp\d30\v_b_kill_2
  EXIT = 0
  | PASS
  VERDICT = STILL_PASS (masked)
```

**完整命令与输出原文（撰写人驱动内嵌，不缩写，`_cm_injection_out.txt:151-156`）：**

```
==============================================================================
[d30] B: script tuple -> ('93.98', SENTINEL)
  SCRIPT check_d30.py: '"误报率"' -> '"TOTALLY_BROKEN_NEEDLE_SENTINEL_XYZ"'; occurrences 1 -> 0; bytes 3926 -> 3951; sha256 6cb737963fc62a0e -> b1670537e12a6d7c
  CMD = C:\Users\Administrator\AppData\Local\Programs\Python\Python312\python.exe -I -X utf8 D:\Project\ra2-campaign-forge\lead\check_masking_20261109\_cm_tmp\d30\b_kill_2\check_d30.py
  CWD = D:\Project\ra2-campaign-forge\lead\check_masking_20261109\_cm_tmp\d30\b_kill_2
  EXIT = 0
  | PASS
```

A 族 `_cm_injection_out.txt:135-148` 把 3 处 `93.98` 或 3 处 `误报率` 分别全杀光，均 `EXIT = 0` / `PASS`；B 族 `:159-164`（杀 `93.98` 换哨兵）亦 `EXIT = 0` / `PASS`。原文：

```
[d30] A: kill ALL '93.98' in 三档权衡的实质, sibling '误报率' alive
  DOC RULING_D30.md: '93.98' -> 'TOTALLY_BROKEN_NEEDLE_SENTINEL_XYZ' x99; occurrences 3 -> 0; bytes 13197 -> 13284
  CMD = C:\Users\Administrator\AppData\Local\Programs\Python\Python312\python.exe -I -X utf8 D:\Project\ra2-campaign-forge\lead\check_masking_20261109\_cm_tmp\d30\a_kill_1\check_d30.py
  CWD = D:\Project\ra2-campaign-forge\lead\check_masking_20261109\_cm_tmp\d30\a_kill_1
  EXIT = 0
  | PASS
```

**FAIL 负控原文（`_cm_injection_out.txt:175-181`）：**

```
==============================================================================
[d30] NEG-CONTROL(all): kill ALL '栈采样' -> AND-path must FAIL
  DOC RULING_D30.md: '栈采样' -> 'TOTALLY_BROKEN_NEEDLE_SENTINEL_XYZ' x99; occurrences 2 -> 0; bytes 13197 -> 13247
  CMD = C:\Users\Administrator\AppData\Local\Programs\Python\Python312\python.exe -I -X utf8 D:\Project\ra2-campaign-forge\lead\check_masking_20261109\_cm_tmp\d30\neg_ctrl_all\check_d30.py
  CWD = D:\Project\ra2-campaign-forge\lead\check_masking_20261109\_cm_tmp\d30\neg_ctrl_all
  EXIT = 1
  | [6] Section 未背书: body must contain 外推 AND 栈采样
  | FAIL (content)
```

另 `and_kill_1`（`:184-190`，全杀 4 处 `外推`）`EXIT = 1`；`neg_ctrl`（`:167-172`，只杀 1 处 `栈采样`）仍 `EXIT = 0` / `PASS`。

⇒ **check_d30 定性：坏掉一根 OR 词针仍 PASS；AND 项能抓「整词删光」，逐词存活状态不打印。无自检件。**

#### 3.3.4 第四件 `_rs_carrier_scan.py` — 本会话独立复现（4/4 计数用）

`_rs_carrier_scan.py:7` 自述「script NEVER writes a file」（本会话直读），`_rs_carrier_scan.py:194` `--needle` 为 `action="append"`，故参数层注入不违反只读铁律。

实跑命令（本会话）：

```
python -I -X utf8 "D:/Project/ra2-campaign-forge/lead/refsync_scope_20261109/_rs_carrier_scan.py" --needle "不能定位当年错误步骤" --needle "TOTALLY_BROKEN_NEEDLE_SENTINEL_XYZ" > "D:/Project/ra2-campaign-forge/lead/check_masking_20261109/_cmd_rs_broken_out.txt" 2>&1; echo "EXIT=$?"
```

输出原文（`_cmd_rs_broken_out.txt:8,10,155961-155968`；`wc -l` = 155968）：

```
EXIT=0
8:needles = ['不能定位当年错误步骤', 'TOTALLY_BROKEN_NEEDLE_SENTINEL_XYZ']
10:scanned files = 6122 ; carrier occurrences = 35152 ; distinct files = 236
155961:=== E. NEGATIVE-CONTROL SELF-TEST (R6) ===
155962:  PASS  ledger_appendix_20261108/LEDGER_APPENDIX_DRAFT.md:123 want=ASSERTION        got=ASSERTION
155963:  PASS  ledger_appendix_20261108/_la_draft3_s604_gapdiff.md:25 want=ASSERTION        got=ASSERTION
155964:  PASS  ledger_bound_20261109/LEDGER_BOUND_VOLUME.md:196 want=ASSERTION        got=ASSERTION
155965:  PASS  ledger_bound_20261109/_lb_BOUND_VOLUME.md:129 want=ASSERTION        got=ASSERTION
155966:  PASS  s604_verdict_entry_20261109/_ve_DRAFT_S609.md:22 want=REFUTING_QUOTE   got=REFUTING_QUOTE
155967:  PASS  ledger_appendix_20261108/LEDGER_APPENDIX_DRAFT.md:215 want=ASSERTION        got=ASSERTION
155968:SELF_TEST = PASS
```

6 条负控全 PASS，`SELF_TEST = PASS`，`EXIT=0` —— 坏针完全被掩蔽。撰写人本次为 `6030/8998/222`（`_cm_rs_broken_out.txt:8,10`），复核人为 `6088/17843/230`，背景为 `638/84/20`（`REFSYNC_SCOPE_FIX.md:251`），本会话为 `6122/35152/236`：**三次数都不同，属 `--root` 默认语料/并行写入口径差，如实登记，不冒充复现同一数字**；只能判「坏针仍 `SELF_TEST=PASS`」这一性质。

### 3.4 三分类逐场景归档（撰写人 19 注入 + 3 control）

| 场景（`_cm_injection_out.txt` 行） | 类 | EXIT | 输出 |
|---|---|---|---|
| d27 control `:12-17` | 仍PASS（control） | 0 | `PASS: D-27 八项机械检查通过；裁决书引用 71 处` |
| d27 a_kill_1 杀 `外推` `:20-25` | 仍PASS | 0 | 同上 |
| d27 a_kill_2 杀 `卡顿不存在` `:27-33` | 仍PASS | 0 | 同上 |
| d27 b_kill_2 词表换哨兵 `:35-41` | 仍PASS | 0 | 同上 |
| d27 b_kill_1 词表换哨兵 `:43-49` | 仍PASS | 0 | 同上 |
| d27 neg_ctrl 杀 `循环论证` `:52-57` | **FAIL** | 1 | `FAIL [4] … 循环论证` |
| d29 control `:60-65` | 仍PASS（control） | 0 | `PASS` |
| d29 a_kill_1 杀 `前提` `:68-73` | 仍PASS | 0 | `PASS` |
| d29 a_kill_2 全杀 `互斥` `:76-81` | 仍PASS | 0 | `PASS` |
| d29 b_kill_2 / b_kill_1 `:84-97` | 仍PASS | 0 | `PASS` |
| d29 neg_ctrl 杀 1 处 `191` `:100-105` | 仍PASS | 0 | `PASS` |
| d29 neg_ctrl_all 全杀 `191` `:108-115` | **FAIL** | 1 | `[3] …` + `[6] … AND 191` + `FAIL (content)` |
| d29 and_kill_1 全杀 `外推` `:118-124` | **FAIL** | 1 | `[6] … AND 外推 AND 191` + `FAIL (content)` |
| d30 control `:127-132` | 仍PASS（control） | 0 | `PASS` |
| d30 a_kill_1 / a_kill_2 `:135-148` | 仍PASS | 0 | `PASS` |
| d30 b_kill_2 / b_kill_1 `:151-164` | 仍PASS | 0 | `PASS` |
| d30 neg_ctrl 杀 1 处 `栈采样` `:167-172` | 仍PASS | 0 | `PASS` |
| d30 neg_ctrl_all 全杀 `栈采样` `:175-181` | **FAIL** | 1 | `[6] … 外推 AND 栈采样` + `FAIL (content)` |
| d30 and_kill_1 全杀 `外推` `:184-190` | **FAIL** | 1 | `[6] … 外推 AND 栈采样` + `FAIL (content)` |

`_cm_injection_out.txt:222-224`（同 `_cm_run_console.txt:222-224`）原文：

```
injected scenarios = 19
injected scenarios still EXIT=0 (PASS) = 14
DONE
```

**结构类「无自检」覆盖三 gate 全部 22 个场景**（`grep -c -F "SELF_TEST"` = 0/0/0，§2.3）：它们没有逐输入自检行、没有负控表，PASS 只是一行裸布尔。

**是否有一件比 scanner 强**：没有一件在「坏输入仍 PASS」上更强（三件 B 族全 `EXIT=0`）；但如实说三件是「8 个 1-bit 检查并列 + 逐项 append 到 errors/failures」，比 scanner「6 条负控压进同一个 `ok &= good`」粒度更好（FAIL 会打印 `[4]`/`[6]` 编号）。目标 OR 项本身无任何改进。

---

## 4 共有缺陷模式

### 4.1 四件计数：**4 / 4**

| # | 对象 | 压缩点（文件:行） | 本次实证 |
|---|---|---|---|
| 1 | `check_d27.py` | `check_d27.py:86-88` `any(keyword … for … for keyword in keywords)` / `:100` 单行 PASS | A 族 2/2 + B 族 2/2 全 `EXIT=0` PASS（§3.3.1） |
| 2 | `check_d29.py` | `check_d29.py:84` `any(word …)` + `:87` `if not any(matches)` / `:105` 单行 PASS | A 族 2/2 + B 族 2/2 全 `EXIT=0` PASS（§3.3.2） |
| 3 | `check_d30.py` | `check_d30.py:84` + `:87` / `:105`（与 d29 逐行同构） | A 族 2/2 + B 族 2/2 全 `EXIT=0` PASS（§3.3.3） |
| 4 | `_rs_carrier_scan.py` | `_rs_carrier_scan.py:165` `min(pos)`、`:229` `any(n in txt)`、`:343` `ok &= good`、`:346` 单 `SELF_TEST`、`:349` `return 0 if ok else 1` | 本会话 `--needle …哨兵` → `EXIT=0` / `SELF_TEST = PASS` / 6/6（§3.3.4） |

限定语：四件的 OR/并集项都压成 1 bit；d29/d30 另有 `all()` AND 项、d27 另有 6 个单输入项，这些**不**属于该缺陷，但也没能阻止整体 PASS。

### 4.2 抽象描述

> 设自检有 k≥2 个同类输入（needle / pattern / keyword / token / case），内部用**存在量词**合成 `covered(x) = ∃i: match(input_i, x)`，随后把这 k 个输入的存活情况**压成 1 bit**（`ok &= good` / `if not any(...)` / `print("PASS")` / 单 `SELF_TEST = PASS`）。
> 于是 `PASS` 的可达世界必然包含「`input_1` 完全失效、但每个样本都被某个 `input_{j≠1}` 命中」，与「k 根全正常」**观测等价**。
> 缺陷不在 `match` 实现，而在**从 k 个输入到 1 bit 的有损压缩**：待证命题是 ∀i 有效，观测量只有 ∃i 命中，且不保留 `hits=[命中下标]` 溯源 → **逐输入可归因**为否。
> 判据式：`DISTINGUISHABLE_PASS = AND_k(真实逐输入自检)`；`EXCLUSIVE / HITSET / MASKED_LINES` 只诊断、不门禁（`lead/masking_effect_20261109/MASKING_EFFECT_AUDIT.md:160,176,335` 的复核 `partial` 教训，本会话直读 `:156-195`）。

### 4.3 ★ 30 秒判据（4 步，全是 grep 级）

1. `grep -n -E "needle|keywords|words|TOKENS|--[a-z-]+"` 找长度≥2 的字面量元组 / `action="append"`，记 k；
2. `grep -n -E "any\(|all\(|min\(|&="` —— 出现 `any()` 把多输入并成一个布尔、或 `ok&=` / `min()` 丢 argmin 即标红（`all()` 对本类**不**红）；
3. `grep -n -E "SELF_TEST|PASS|FAIL|return 0|sys.exit"` —— 只有一行 PASS 出口且无 `for i,inp` 逐输入打印行 ⇒ k→1 bit 成立；
4. 把一根输入换零命中哨兵重跑，仍 `EXIT=0` / `PASS` 即确诊。

**一句话**：三项齐 ⇒ 本类；坏针仍 PASS ⇒ 实证。

本会话实跑（repo root）：

```
grep -n -E '"[^"]+", *"[^"]+"|action="append"|--[a-z-]+' lead/d27_ruling_20261106/check_d27.py lead/d29_ruling_20261106/check_d29.py lead/d30_ruling_20261106/check_d30.py
grep -n -E "any\(|all\(|min\(|&=\|" <四件>
grep -n -c -F "SELF_TEST" <四件>
```

输出原文（节选）：

```
### STEP1 literal tuples / append (d27/d29/d30)
--- lead/d27_ruling_20261106/check_d27.py
84:        (6, "未背书", ("外推", "卡顿不存在")),
--- lead/d29_ruling_20261106/check_d29.py
76:            (4, "冲突是否成立", ("互斥", "前提"), False),
78:            (6, "未背书", ("口径 B", "外推", "191"), True),
--- lead/d30_ruling_20261106/check_d30.py
76:            (4, "三档权衡的实质", ("93.98", "误报率"), False),
78:            (6, "未背书", ("外推", "栈采样"), True),
### STEP2 any/all/min/&= (four scripts)
--- lead/d27_ruling_20261106/check_d27.py
86:        if not any(keyword in body for body in bodies.get(title, [])
--- lead/d29_ruling_20261106/check_d29.py
83:                all(word in body for word in words) if require_all
84:                else any(word in body for word in words)
87:            if not any(matches):
--- lead/d30_ruling_20261106/check_d30.py
83:                all(word in body for word in words) if require_all
84:                else any(word in body for word in words)
87:            if not any(matches):
--- lead/refsync_scope_20261109/_rs_carrier_scan.py
165:    pos = min((line.find(n) for n in needles if n in line), default=-1)
229:        if not any(n in txt for n in a.needle):
### STEP3 SELF_TEST / PASS / FAIL / exit (four scripts)
--- lead/d27_ruling_20261106/check_d27.py
0
100:    print(f"PASS: D-27 八项机械检查通过；裁决书引用 {count} 处")
--- lead/d29_ruling_20261106/check_d29.py
0
105:    print("PASS")
--- lead/d30_ruling_20261106/check_d30.py
0
105:    print("PASS")
--- lead/refsync_scope_20261109/_rs_carrier_scan.py
1
346:        P("SELF_TEST = %s" % ("PASS" if ok else "FAIL"))
```

四项三项齐，第 4 步全实证（§3.3 四件全部 `EXIT=0`）。

### 4.4 修复优先级

1. **`_rs_carrier_scan.py` 最该先修** —— 唯一被当作交付口径证据写进 `lead/refsync_scope_20261109/REFSYNC_SCOPE_FIX.md:251`（本会话 `grep -n -F "SELF_TEST"` 实见该行把 `SELF_TEST = PASS` 列为交付命令结果）的一件；`MASKING_EFFECT_AUDIT.md:109-110` 判 high 且不可信（本会话直读 `:98-110`）。压缩最彻底（6 负控→1 个 `ok`），且独有 `_rs_carrier_scan.py:165` `min(pos)` 反向掩蔽（审计 `:148` 加一根针把 PASS 变 FAIL，role 非单调）。修正版甲'/乙'/丙' 四场景矩阵已被复核确认可落地（审计 `:186-195`，`ALL_SCENARIOS_MATCH_EXPECTATION = True`）。
2. **`check_d27.py`** —— OR 词表落在「未背书」承重段；输出「八项机械检查通过；引用 71 处」最像逐项已验却最易误读，杀光一根词后输出一字不变；另有 `check_d27.py:8` CWD 相对路径的脆弱性。
3. ≈ 4. **`check_d29.py` / `check_d30.py`** —— 逐行同构可一次套改，虽多一层 `all()` 兜底但 OR 项同样中招。三件都在 `lead/PENDING_DECISIONS.md:92,105,129` 登记「门禁 exit=0」，故三件的 PASS 均应标**不可信 / 待重跑**。

---

## 5 一次性修复方案

### 5.1 三套方案能否通吃四件

**结论：能通吃四件的只有「甲'（逐输入独立跑自检 + `AND_k`）」，且必须用 `MASKING_EFFECT_AUDIT.md:176` 的修正版；撰写人原版乙/丙已被复核判 `partial`。**

上游审计依据（本会话直读 `lead/masking_effect_20261109/MASKING_EFFECT_AUDIT.md:156-195`）：

- `:160`：复核人实跑证明原方案乙/丙（含「推荐」的丙）在「交付的双针掩蔽 PASS」上仍报 `COVERAGE_GATE=PASS`；`PLAN_C` 的 `PER_NEEDLE_SELFTEST` 是**误称**（只由语料独占行数推出，从不跑自检）→ 「三方案均能区分」不成立，verdict=partial。
- `:172`：**唯一被复核确认能抓的核心 = 甲（逐 needle 独立跑自检 + `AND_k`）**。
- `:176`：统一 GATE `AGGREGATE = AND_k(REAL per-input self-test)`，`HITSET / MASKED_LINES / EXCLUSIVE / EXCLUSIVE_CONTROLS` 一律只报告、不门禁；`PER_NEEDLE_SELFTEST` 必须来自真实 k 次运行。
- `:186-195`：四场景矩阵 S1–S4 全中（甲'/乙'/丙' 均 FAIL/FAIL/PASS/FAIL，`ALL_SCENARIOS_MATCH_EXPECTATION = True`，该矩阵是审计件内实跑，**本会话只直读、未复跑，标未验**）。

甲' 是**外部外壳**（不改被审脚本 0 行、完全不破坏既有输出，审计 `:180`）：scanner 定义「`for n in needles: 跑 --needle n`」；三 gate 定义「`for w in OR词表: 用只含 w 的词表跑一次该检查项`」，`AGGREGATE = AND_k`。乙'/丙' 只能当诊断层。

### 5.2 四件差异（原则通吃、适配器不能一行通吃）

1. **输入来源**：scanner 输入是 CLI `--needle`（`_rs_carrier_scan.py:194` `action="append"`，参数层可注入）；三 gate 是**源码硬编码字面量元组**（`check_d27.py:81-85`、`check_d29.py:75-79`、`check_d30.py:75-79`），且脚本**不接受任何 CLI**（本会话 `grep -n -E "argparse|sys\.argv|add_argument"` 三件 → 0 命中，grep exit=1）。→ 三 gate 只能走**临时副本**。
2. **k 的语义**：scanner k=2 是并列 needle 且 `min(pos)` 有位置依赖；三 gate k=2 是同小节 OR 关键词、无反向掩蔽。→ `HITSET`/`EXCLUSIVE` 对三 gate 基本无意义，只需「逐词命中数」。
3. **汇总出口**：scanner 有字面 `SELF_TEST = PASS`（`_rs_carrier_scan.py:346`）+ `return 0 if ok else 1`（`:349`）；三 gate 只有 `print("PASS")` + `return 0`（`check_d27.py:100-101` / `check_d29.py:105-106` / `check_d30.py:105-106`），FAIL 时逐条打印。→ 外壳解析规则不同。
4. **AND 项处理**：d29/d30 的 `require_all=True` 项（`check_d29.py:83` / `check_d30.py:83`）单跑一词会天然 FAIL（本次 `and_kill_1` 实证 `EXIT=1`），故 `AND_k` 门禁**必须只针对 OR 项**，否则误伤。这是三 gate 独有、scanner 没有的差异。

### 5.3 ★ 通用补丁模板（本会话实跑修正版）

**先如实记录复核 finding (A)**：`_cm_AUDIT.md:469-536` 自称「可粘贴」的模板，套进 `check_d29.py` 后**不能工作**。本会话实跑 `python -I -X utf8 D:/Project/ra2-campaign-forge/lead/check_masking_20261109/_cmv_template_port.py`（输出 `_cmd_tplport_out.txt`）：

```
  input[0] = '互斥': SELF_TEST=PASS controls=1/1
  input[1] = '前提': SELF_TEST=PASS controls=1/1
  broken[0] -> TOTALLY_BROKEN_NEEDLE_SENTINEL_XYZ: caught=False  (rc=0)
  broken[1] -> TOTALLY_BROKEN_NEEDLE_SENTINEL_XYZ: caught=False  (rc=0)
BASE_PASS=True  AND_k=True  BAD_NEEDLE_CAUGHT=False
DISTINGUISHABLE_PASS = False
PORT_EXIT=1
```

根因（`_cm_AUDIT.md:507-520` 的 `bad_needle_injection()` 用「坏针并集跑一次」的 aggregate 判 `caught`，**正是被掩蔽的那个布尔**，对 OR 压缩 gate 恒为 False）。本会话三路对照实跑 `python -I -X utf8 D:/Project/ra2-campaign-forge/lead/check_masking_20261109/_cmv_template_3way.py`（输出 `_cmd_tpl3way_out.txt`）：

```
V1_published: BASE_PASS=True AND_k=True BAD_NEEDLE_CAUGHT=False DISTINGUISHABLE_PASS=False
V2_AND_k:     BASE_PASS=True AND_k=True BAD_NEEDLE_CAUGHT=True  DISTINGUISHABLE_PASS=True
V3_liveness:  BASE_PASS=True AND_k=True BAD_NEEDLE_CAUGHT=True  DISTINGUISHABLE_PASS=True
sanity single-SENTINEL run: EXIT=1 PASS_parsed=False lines=['[4] Section 冲突是否成立: body must contain TOTALLY_BROKEN_NEEDLE_SENTINEL_XYZ', 'FAIL (content)']
```

另三处接口不一致（编排方【复核】finding A）：`_cm_AUDIT.md:490` 的 `parse(lines)` 文档写 `aggregate=(exit==0)` 但签名收不到 `rc`；`controls` 需调用方凭空造非空列表否则 `all(controls)` 恒真；k=1 词表替换须留尾逗号否则元组退化为字符串。

**修正版模板**（落 `lead/check_masking_20261109/_cmd_template_fixed.py`，外部外壳、被审脚本 0 行改动、所有临时目录限定在唯一写域 `_cmd_tmp/`）：

```python
SENTINEL = "TOTALLY_BROKEN_NEEDLE_SENTINEL_XYZ"

def run_once(inputs, workdir):
    # 适配器(b)：硬编码词表 -> 沙箱副本替换，绝不写回源
    # k==1 也必须保留尾逗号，否则元组退化为字符串
    dst = ", ".join('"%s"' % x for x in inputs) + ","
    sp.write_text(text.replace(ORIGINAL_TUPLE, dst, 1), encoding="utf-8")
    p = subprocess.run([sys.executable, "-I", "-X", "utf8", str(sp)],
                       cwd=str(sb), capture_output=True, text=True)
    return p.returncode, (p.stdout + p.stderr).splitlines()

def parse(rc, lines):                    # 修正①：签名收 rc
    txt = "\n".join(lines)
    aggregate_pass = (rc == 0) and ("PASS" in txt) and ("FAIL" not in txt)
    controls = ["[4]" not in txt]      # 修正②：非空，由实现保证
    return aggregate_pass, controls

def real_per_input_selftest(inputs, workdir):
    per = []
    for i, x in enumerate(inputs):
        rc, lines = run_once([x], workdir)          # 单输入，不是并集
        ok, controls = parse(rc, lines)
        per.append(ok and rc == 0 and all(controls))
        print("  input[%d] = %r: SELF_TEST=%s controls=%d/%d" %
              (i, x, "PASS" if per[-1] else "FAIL", sum(controls), len(controls)))
    return all(per)                                  # AGGREGATE = AND_k

def bad_needle_injection(inputs, workdir):
    # 修正③（根因）：不信任并集运行的 aggregate，要求 AND_k(broken) 变 FAIL
    results = []
    for i in range(len(inputs)):
        broken = list(inputs); broken[i] = SENTINEL
        caught = not real_per_input_selftest(broken, workdir)
        results.append(caught)
        print("  broken[%d] -> %s: caught=%s" % (i, SENTINEL, caught))
    return all(results)

# main(): BASE_PASS + AND_k + BAD_NEEDLE_CAUGHT -> DISTINGUISHABLE_PASS
```

**本会话实跑命令与输出原文**（`python -I -X utf8 D:/Project/ra2-campaign-forge/lead/check_masking_20261109/_cmd_template_fixed.py`，输出 `_cmd_template_fixed_out.txt`）：

```
BASE CMD = C:\Users\Administrator\AppData\Local\Programs\Python\Python312\python.exe -I -X utf8 D:\Project\ra2-campaign-forge\lead\check_masking_20261109\_cmd_tmp\tmpot34mp6o\run_0001\check_d29.py
BASE EXIT = 0 lines = ['PASS']
  input[0] = '互斥': SELF_TEST=PASS controls=1/1
  input[1] = '前提': SELF_TEST=PASS controls=1/1
  input[0] = 'TOTALLY_BROKEN_NEEDLE_SENTINEL_XYZ': SELF_TEST=FAIL controls=0/1
  input[1] = '前提': SELF_TEST=PASS controls=1/1
  broken[0] -> TOTALLY_BROKEN_NEEDLE_SENTINEL_XYZ: caught=True
  input[0] = '互斥': SELF_TEST=PASS controls=1/1
  input[1] = 'TOTALLY_BROKEN_NEEDLE_SENTINEL_XYZ': SELF_TEST=FAIL controls=0/1
  broken[1] -> TOTALLY_BROKEN_NEEDLE_SENTINEL_XYZ: caught=True
BASE_PASS=True  AND_k=True  BAD_NEEDLE_CAUGHT=True
DISTINGUISHABLE_PASS = True
TEMPLATE_EXIT=0
```

即：修正版甲' 外壳能同时给出「真通过放行」与「坏针被抓」。**边界如实**：这只是**演示外壳本会话实跑**，不是把它部署成门禁；**未在三 gate / scanner 上落地、未跑修复后回归**（本任务铁律只做注入审计）。三 gate 内嵌「逐词 HIT/DEAD 打印」最小改法见 `_cm_AUDIT.md:538-555`（对应审计 `:343` 第 5 条），本会话**未执行**。

### 5.4 落地成本（本会话直读 `_cm_AUDIT.md:559-569` + 审计 `:178-184`）

| 方案 | 行数量级 | 对既有输出破坏性 |
|---|---|---|
| **甲' 外部外壳（推荐）** | 外壳 ~15–25 行；被审脚本 **0 行** | **完全不破坏**（每次单跑输出仍是原格式，只多 `AND_k` 汇总） |
| 逐词打印（内嵌，三 gate 专用） | 每 gate ~5–10 行 | 弱破坏：新增 `word …: HIT/DEAD` 行 |
| 乙'（逐针负控表） | 0 行或内嵌 ~20–30 行 | 弱破坏：新增 `PER_NEEDLE` 行 |
| 丙'（溯源台账） | ~30–50 行 | 中等破坏：A 段多 `hits=`、新增 F 段、旧 PASS 可能变 FAIL |
| 三 gate 内嵌合计 | 3 × ~10 + 共用外壳 ~25 ≈ **55 行级** | 弱；但需改 3 处源码（本任务未做） |

另需 ~10 行 `hashlib` 指纹绑定（审计 `:345` 第 7 条），防并行写入让计数漂移被误读为「测试变好」——§3.3.4 的四组不同计数正是实例。

**修复建议一句话**：先给 `_rs_carrier_scan.py` 套甲' 外壳并把 `REFSYNC_SCOPE_FIX.md:251` 的旧 PASS 标不可信，再对三 gate 的 OR 项做逐词 HIT/DEAD 报告 + 同一 `AND_k` 门禁，最后把 `PENDING_DECISIONS.md:92,105,129` 三处 `exit=0` 换成「逐输入 PASS 表 + 指纹」。

---

## 6 复核回件 + 结论 + 未验

### 6.1 绑定行（被核对象 = 三件自检脚本各自独立指纹）

被核对象 SHA256 = 3b769d7c64c2725100186439725198dbc134a277914e2cb2e9b0af844fe7671c，字节数 = 3764
被核对象 SHA256 = 2a50b09adff555dbce4c5740a2af78b779876cad771b6fdf887ba3c0dc780f14，字节数 = 3906
被核对象 SHA256 = 6cb737963fc62a0e045f51247b4fa57ef190acb0b524da3aa6b7713fd05ee9fd，字节数 = 3926

（依次对应 `check_d27.py` / `check_d29.py` / `check_d30.py`；本会话 `python -I -X utf8 -c "import re,pathlib; … re.compile(r'被核对象 SHA256 = ([0-9a-f]{64})，字节数 = (\d+)')"` 对 `_cm_AUDIT.md:8-10` 实跑得 `matches = 3` 且 `STRICT_FULL_MATCH=True` 3/3，本回件三行同格式同值。）

### 6.2 复核 verdict 如实登记

编排方【复核】给出 **`verdict = "partial"`**，`ranCommands = 24`。按交付要求，**refuted 或 partial 一律标 `unconfirmed`**：

> **复核 verdict = partial → 标 `unconfirmed`。**

定 partial 的两项（本会话均独立复现，输出见 §5.3 与下）：

- **(A) 补丁模板不可用**：`_cm_AUDIT.md:469-536` 的「可粘贴」模板移植到 `check_d29.py` 后 `DISTINGUISHABLE_PASS = False` / `PORT_EXIT=1`；根因是 `bad_needle_injection()` 判 `caught` 用了被掩蔽的并集布尔。另 3 处接口不一致（`parse` 收不到 `rc`、`controls` 需凭空造、k=1 元组退化）。本会话 `_cmv_template_port.py` 与 `_cmv_template_3way.py` 实跑复现，并给出/实跑修正版（§5.3）。**审计 §4.2 的 `AND_k` 原则是对的，错的是那份外壳实现。**
- **(B) 出处缺陷**：`_cm_AUDIT.md:163` 的 `DRIVER_EXIT=0`、`:169-171` 三条 `BASELINE … EXIT=0`、`:221-224` / `:277-280` / `:337-340` 三块「★ 完整命令与输出原文（独立复跑）」里的 `EXIT=0`，在 `_cm_run_console.txt` / `_cm_injection_out.txt` 中**无对应行**。本会话实跑：

```
$ grep -n -F "DRIVER_EXIT" lead/check_masking_20261109/_cm_run_console.txt lead/check_masking_20261109/_cm_injection_out.txt
(exit of grep above = 1，0 命中)
$ grep -n -F "EXIT=0" lead/check_masking_20261109/_cm_run_console.txt lead/check_masking_20261109/_cm_injection_out.txt
lead/check_masking_20261109/_cm_injection_out.txt:223:injected scenarios still EXIT=0 (PASS) = 14
lead/check_masking_20261109/_cm_run_console.txt:223:injected scenarios still EXIT=0 (PASS) = 14
```

  console 尾部（本会话 `tail -n 12`）只有 `injected scenarios = 19 / 14 / DONE / [written]`（`:222-226`）。且 `:207,213,231,263,269,323` 的 `CMD = …\_cm_tmp\…` 与 `cwd=…` 是缩写。**这不构成「只写结论不给输出」**——驱动内嵌的完整 CMD/CWD/EXIT/PASS 在 `_cm_injection_out.txt:35-41,84-89,151-156` 齐全（本回件 §3.3 已逐条不缩写引用）；问题是「独立复跑」这一说是重构文本、无原始输出背书，**标未验**。本会话用 `_cmv_repro.py` 独立重跑补齐了等价证据（§3.3 三件 + 负控，输出 `_cmd_repro_out.txt`）。

**通过的六项**（编排方【复核】原文，本会话对其中可复现项已实跑）：① 指纹与 3/3 严格绑定行；②(b) 完整命令+输出；②(c) 全新沙箱独立重跑三件 B 族仍 PASS；①(d) 逐检查项可归因、逐词不可归因；③(a) 4/4 逐件有据；⑤(b) 未回避项目整体含义；⑧ 未见越界。本会话另复跑 `git status --porcelain -- <五个只读域>` → 五个域全部 `??`（目录整体未跟踪），无 `M`/`D`；`git log -1 --oneline` → `2657458`，无 commit/push。

### 6.3 三件逐件定性 + 整体含义

| 件 | 定性 | 依据 |
|---|---|---|
| `check_d27.py` | **有缺陷（HIGH，同族）** | `check_d27.py:86-88` OR 词表压成 1 bit；A 族 2/2 + B 族 2/2 全 `EXIT=0` PASS，杀光 `卡顿不存在` 后输出一字不变（§3.3.1） |
| `check_d29.py` | **有缺陷（HIGH，同族）** | `check_d29.py:82-89` 双层 OR；A 族 2/2 + B 族 2/2 全 `EXIT=0` PASS；`all()` 项能抓整词删光但不打印逐词（§3.3.2） |
| `check_d30.py` | **有缺陷（HIGH，同族）** | `check_d30.py:82-89` 与 d29 逐行同构；A 族 2/2 + B 族 2/2 全 `EXIT=0` PASS（§3.3.3），**逐件独立给过输出原文，不概括为「同样缺陷」** |

三件都**不是「无缺陷」，也不是「判不了」**：坏输入注入执行了、完整命令与输出拿到了、源指纹前后一致（本会话 `_cmd_repro_out.txt` PART 5：`d27/d29/d30 … MATCH=True` 3/3）。局部如实补充：三件的 `require_all=True` / 单元素词表 / 缺文件 / 引用数 / `selfBias` 项**不**属此缺陷，且本次实证能出 FAIL。

**★ 整体含义（项目自检质量）**：

1. **不是孤例，是模板复用**：d29 与 d30 逐行同构，d27 是同一模式的早期版本，加上 scanner 的 `any`+`min`+单布尔，四件跨 3 个写域、不同轮次 → 「多输入并集 + 单行 PASS」是本项目**默认的自检写法，而非某次手误**（`_cm_AUDIT.md:587`，本会话直读；审计 `:286-302` 的有界扫描报 `B (any()/min() over multiple inputs) = 1436` 处命中，但那是正则计数、未逐个实跑，**标未验**）。
2. **台账里的 `exit=0` 不能当「逐项已验」读**：`lead/PENDING_DECISIONS.md:92,105,129` 三处把「门禁 exit=0」写成裁决交付证据；本次证明这 3 个 `exit=0` 与「OR 词表里有一根死词」观测等价。按审计 `:110` 铁律「若某处通过是被掩蔽的，即使结果碰巧正确，也必须标为不可信」，三处登记的 PASS 应标**不可信 / 待重跑**。本会话 `grep` 全文未见 `逐输入 PASS|per-input|hits=` 落地。
3. **系统性问题**：自检普遍只验「文档在不在 / 有没有某串」，不验「每个判据输入是否存活」；没有逐输入可归因、没有坏针注入、没有语料/脚本指纹绑定。四件里连「可见」都少见，更别说「门禁」。**别把 `exit=0` 直接写进台账当逐项已验**（`_cm_AUDIT.md:611`）。

**判不了什么（如实列）**：① 判不了裁决书事实与推理（三件 docstring 自称 format gate，`check_d27.py:1` / `check_d29.py:1` / `check_d30.py:1`）；② 判不了「真实历史上是否真有死词」——本次是**主动注入**，三件原词在文档里都实际命中，故**结果碰巧对，判的是 PASS 不可信，不是结论错**；③ 判不了其它未点名脚本；④ 判不了修复后效果（模板未落地、未跑修复后回归）；⑤ 判不了 scanner 当时数字（口径差，§3.3.4）；⑥ 判不了 d27 CWD 依赖是否算 bug（跑法坑，非 k→1 bit）；⑦ 判不了 `require_all=True` 项是否也有 1-bit 问题（只证对「整词删光」敏感，未证会打印逐词存活状态，事实上不打印）。

**以后写自检「必做」清单**（`_cm_AUDIT.md:601-611`，本会话直读）：① 列输入、报 `k=` 与每个 `input[i]`；② 禁止裸 `any()` 当门禁，`require_all=False` 也要逐词打印 `HIT/DEAD`；③ `AND_k` 真实逐输入自检，`PER_INPUT_SELFTEST` 必须来自真实 k 次运行、不得由语料独占行数推断；④ 保留 `hits=[命中输入下标]`；⑤ 坏针注入自检（k 次换哨兵，每次要求整体变 FAIL）；⑥ 门禁/诊断分离；⑦ 报 PASS 时绑定输入语料 SHA256 + 文件数 + 被审脚本 SHA256；⑧ 单调性声明（`min(pos)`/`argmin` 要每根独立求角色再合并）；⑨ 别把 `exit=0` 直接写进台账。

### 6.4 本会话实跑命令台账（供复核）

| # | 命令（均为 `python -I -X utf8` + 绝对路径，或 grep/git） | 输出件 / 行 |
|---|---|---|
| 1 | `python -I -X utf8 -c "import hashlib,pathlib; …"`（8 件指纹） | 见 §2.1 输出原文 |
| 2 | `grep -n -E "SELF_TEST\|any\(\|all\(\|min\(\|…` 四件 + `grep -n -c -F "SELF_TEST"` | §2.3 / §4.3 输出原文 |
| 3 | `python -I -X utf8 "D:/…/lead/check_masking_20261109/_cmv_repro.py"` | `_cmd_repro_out.txt`（PART 1–5，含 `MATCH=True` 3/3） |
| 4 | `python -I -X utf8 "…/_cmv_template_3way.py"` | `_cmd_tpl3way_out.txt`（V1/V2/V3） |
| 5 | `python -I -X utf8 "…/_cmv_template_port.py"` | `_cmd_tplport_out.txt`（`PORT_EXIT=1`） |
| 6 | `python -I -X utf8 "…/_cmd_template_fixed.py"` | `_cmd_template_fixed_out.txt`（`DISTINGUISHABLE_PASS = True`，`TEMPLATE_EXIT=0`） |
| 7 | `python -I -X utf8 "…/_rs_carrier_scan.py" --needle "不能定位当年错误步骤" --needle "TOTALLY_BROKEN_NEEDLE_SENTINEL_XYZ" > "…/_cmd_rs_broken_out.txt" 2>&1; echo "EXIT=$?"` | `EXIT=0` + `SELF_TEST = PASS`（`:155968`） |
| 8 | 三件未注入基线（repo root） | §3.1 输出原文，`EXIT=0` ×3 |
| 9 | `python -I -X utf8 -c` 严格绑定行正则校验 | `matches = 3` / `STRICT_FULL_MATCH=True` 3/3 |
| 10 | `grep -n -F "DRIVER_EXIT"` / `grep -n -F "EXIT=0"` / `tail -n 12 _cm_run_console.txt` | §6.2 输出原文 |
| 11 | `git status --porcelain -- <五个只读域>` / `git log -1 --oneline` | 五域全 `??` 无 M/D；`2657458` |
| 12 | `grep -n -E "check_d(27\|29\|30)\|门禁\|exit=0" lead/PENDING_DECISIONS.md` / `grep -n -F "SELF_TEST" lead/refsync_scope_20261109/REFSYNC_SCOPE_FIX.md` | `:92,105,129`；`REFSYNC_SCOPE_FIX.md:251` |

### 6.5 未验项（逐条如实，不补造）

1. **未验** `_cm_AUDIT.md:163,169-171,221-224,277-280,337-340` 声称的「独立复跑 / DRIVER_EXIT=0」——无原始输出件背书（§6.2 已 grep 反证）；本会话用 `_cmv_repro.py` 补齐等价证据，但**原始那次独立复跑本身未验**。
2. **未验** 撰写人驱动 `_cm_inject.py` 的 19 场景矩阵——本会话**直读** `_cm_injection_out.txt`，**未重跑驱动**；三件 headline 与负控已由本会话 `_cmv_repro.py` 独立复现。
3. **未验** 审计 `MASKING_EFFECT_AUDIT.md:186-195` 甲'/乙'/丙' 四场景矩阵——本会话只直读，未复跑；本会话实跑的是自己的修正版外壳（§5.3），不等同该矩阵。
4. **未验** 审计 §5.2 其它脚本（`_gp_regression` / `_g7_predicates` / `_n13v_independent` / `_v12_rule` / `boundary_scan` / `snapshot`）与其余 `check_*.py`——未注入、未实跑；审计 `:404-405` 自认这些坏针注入未做。
5. **未验** 三 gate 内嵌逐词打印改法（`_cm_AUDIT.md:538-555`）与任何修复后回归——本任务铁律只做注入审计，**模板未落地到被审脚本**。
6. **未验** scanner 的当时数字（638/84/20）与本次数字（6122/35152/236）的一致性——属 `--root` 语料/并行写入口径差，只判性质不冒充复现。
7. **未验** 裁决书内容本身、真实历史是否已有死词、d27 CWD 依赖是否算 bug、`require_all=True` 项逐词可归因性（见 §6.3 判不了什么）。
8. **未验** 审计 `:286-302` 报的 `1436` 处 `any()/min()` 命中——正则计数、未逐个实跑，方向一致但不作逐件结论。
