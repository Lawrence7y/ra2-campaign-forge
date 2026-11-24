# TWO_PRODUCTS_ALIGN.md — 两份机读件现状核查 / 聚合代码差异 / 单点定义方案 / 只改一处风险 / 边界与清单

> 产出角色：两产物对齐件撰写员。本件为**新写**的对齐设计件，落唯一写域 `lead/two_products_20261109/`；与同写域既有 `_tp_ALIGNMENT.md` 并存，不覆盖、不修改它（后者 494 行，`wc -l` 实跑）。
> 引用口径：代码一律 `path:line`；实跑一律给出本次会话的「命令 + 输出」；未跑、未验、判不了的一律标注，不补造。
> 纪律：零真机（未启动 gamemd.exe / ra2loader / YURI.exe，未 taskkill，未读活进程内存）；零采样代码（未写 hook / MiniDump / SuspendThread / StackWalk / 探针注入 / 动态内存解析）；Python 一律 `python -I -X utf8` + 绝对路径；指纹用 `hashlib`；不 commit、不 push。

---

## 1 目的与边界

**目的**：对同一批次的两份机读产物做「现状核查 + 口径对齐设计 + 差异核查」。两件对象：

- **A** = `lead/r11_f2_fix_20261109/_f2_compare_out.json`（生产者 `_f2_compare.py`）
- **B** = `lead/r11_f2_fix_20261109/_f2v_run_out.json`（生产者 `_f2v_run.py`）

要回答的是：`totals` 的 7 键 / 9 键差在哪、值差在哪；`results[]` 结构差在哪；这算「不同口径」还是「算错」；聚合代码两段是不是同一套语义；`plus_collected` 和 `plus_path` 是不是同一个东西；怎么做**单点定义**；有哪些**一致性断言**可机检；**只改一处**会沿什么链条静默分叉、现有**指纹锁**能不能抓到、怎么**防漏改**。

**边界（硬约束，来自任务书铁律）**：

1. **只做对齐设计与差异核查**。**不改任何生产者**（`_f2_compare.py` / `_f2v_run.py` / `_f2_r11plus.py`）、**不改任何机读件**（A / B 两份 JSON）、不改台账、不改既有门禁。本会话唯一新增文件是本 `TWO_PRODUCTS_ALIGN.md`。
2. **绝对只读**域：`lead/r11_f2_fix_20261109/` 全部件、`lead/count_invariant_20261109/` 全部件、`lead/merged_contract_20261109/`、`lead/gate_r9r12_20261109/`、两件台账（`lead/PENDING_DECISIONS.md`、`lead/GOAL_THREE_TARGETS_20261018.md`）。一律不修改、不追加、不覆盖。
3. **唯一写域** = `lead/two_products_20261109/`。本会话对该目录既有 `_tp_*` / `_tpv_*` 件只**读取与执行**；执行复核员留下的 `_tpv_counterexamples*.py` 会重写写域内的 `_tpv_*.json` 构造样本，这些是写域内的构造输入，不是被保护的两份机读件。
4. **未跑两生产者本体**（`_f2_compare.py` / `_f2v_run.py`）重跑产物——纪律禁止改/重跑产物；故本件所有数值结论来自「读现盘 JSON + 独立重算」与「读生产者源码」，不是重跑生产者。

**结论状态预告**：本件**不以「已对齐」作结论**。当前盘数值零不一致、属**不同口径**（schema/命名/布局），但**单点定义尚未落地**、现盘门禁为 partial 实现、`counting_policy` 与策略目标哈希均未在台账登记。复核 verdict 为 `partial`，按任务书规则本件整体标 **unconfirmed**（详见 §6）。

末次盘面复核（本会话实跑）：`python -I -X utf8 -c "…9 件 hashlib…"` → `ALL_UNCHANGED = True`；`git log -1 --oneline` → `2657458 GOAL-3T: 台账 §400→§508 与 D-07..D-11 裁决登记入账`；`git status --porcelain -- lead/two_products_20261109/` → `?? lead/two_products_20261109/`（未 commit、未 push）。

---

## 2 上游指纹（九件）+ 现状核查

### 2(a) 九件上游指纹（本会话 `hashlib` 实算）

命令（本次会话实跑）：

```
python -I -X utf8 -c "import hashlib, pathlib; base='D:/Project/ra2-campaign-forge/'; [print(rel, hashlib.sha256((pathlib.Path(base)/rel).read_bytes()).hexdigest(), len((pathlib.Path(base)/rel).read_bytes())) for rel in <9 件清单>]"
```

输出（9/9 与任务书【编排方指纹】**逐件全等**，无一漂移）：

| # | 对象 | SHA256 | 字节数 |
|---|---|---|---|
| 1 | `lead/r11_f2_fix_20261109/_f2_compare.py` | `12e55acf42441aca846986a2447abffef77d774ee694cedf56a012c1c8907106` | 4821 |
| 2 | `lead/r11_f2_fix_20261109/_f2v_run.py` | `75108dcaee4985f8623b59de18f8650ec6b78b73fbbd93ca3197f3057efdbd9a` | 3469 |
| 3 | `lead/r11_f2_fix_20261109/_f2_compare_out.json` | `148ea8d689eaaf582af05ea1bf4650605e104d6d74f8c7765e75a6eec662c7b1` | 44958 |
| 4 | `lead/r11_f2_fix_20261109/_f2v_run_out.json` | `a62ee13e3afe88a421d31859c8f11c11e95b78b9b6b5d362807b6ba990c50905` | 25200 |
| 5 | `lead/r11_f2_fix_20261109/_f2_r11plus.py` | `83f8217fb9a194befdd389f0fd9e699660d3240f0cf1eec365cc3d612fdf8f75` | 15723 |
| 6 | `lead/count_invariant_20261109/_ci_checks.py` | `9e771bcbddf7fc3a0920a56b5e608a37b170c28517b0feaff7bfa2e448151964` | 10494 |
| 7 | `lead/count_invariant_20261109/COUNT_INVARIANTS.md` | `7a9a7a7d84b224cd583e571b64ba1060bf40ac3315207637a55f0b2800a3e159` | 53665 |
| 8 | `lead/PENDING_DECISIONS.md` | `3765eddbe96deeb65eeb1f05dc81e1dc171e7ea3b2c826e2692a1d15e1c8f2d7` | 52419 |
| 9 | `lead/GOAL_THREE_TARGETS_20261018.md` | `2baa0de45d4125549262eb595d7518c9ce99efeee120384bf640cded8a933ede` | 759518 |

末次复算同一命令 → 9 行 `MATCH` + `ALL_UNCHANGED = True`。故以下「现状」结论都锁定在编排方给定的同一份盘上。

### 2(b) `totals` 逐键差异（**必须逐键给出，不做概括**）

命令：`python -I -X utf8 -c "…json 结构比较…"`（本次会话实跑），输出：

```
A.top_keys ['results', 'totals']                       B.top_keys ['declared_mismatch_files', 'results', 'totals']
A.totals_n 7 keys ['bindings', 'orig_match', 'orig_path', 'orig_problems', 'plus_match', 'plus_path', 'plus_problems']
B.totals_n 9 keys ['bindings', 'orig_collected', 'orig_match', 'orig_problems', 'orig_warnings', 'plus_collected', 'plus_match', 'plus_problems', 'plus_warnings']
only_A ['orig_path', 'plus_path']
only_B ['orig_collected', 'orig_warnings', 'plus_collected', 'plus_warnings']
common_n 5 ['bindings', 'orig_match', 'orig_problems', 'plus_match', 'plus_problems']
common_value_diff {}
ALL_totals_A {'bindings': 19, 'orig_path': 1, 'plus_path': 9, 'orig_match': 0, 'plus_match': 9, 'orig_problems': 24, 'plus_problems': 23}
ALL_totals_B {'orig_collected': 1, 'plus_collected': 9, 'orig_match': 0, 'plus_match': 9, 'orig_problems': 24, 'plus_problems': 23, 'orig_warnings': 18, 'plus_warnings': 11, 'bindings': 19}
alias orig 1 1        alias plus 9 9
A.results_n 30 B.results_n 30        declared_mismatch_files(B) 0
```

逐键对照（canonical 维 = 实际数的事情；A 键 / B 键 = 各自写进 `totals` 的名字）：

| canonical 维 | A 键 | A 值 | B 键 | B 值 | 值差 | 差异性质 |
|---|---|---|---|---|---|---|
| 绑定行总数 | `bindings` | 19 | `bindings` | 19 | 0 | 同名同维 |
| orig 采到单一路径条数 | `orig_path` | 1 | `orig_collected` | 1 | 0 | **同维异名（别名）** |
| plus 采到单一路径条数 | `plus_path` | 9 | `plus_collected` | 9 | 0 | **同维异名（别名）** |
| orig `match is True` 条数 | `orig_match` | 0 | `orig_match` | 0 | 0 | 同名同维 |
| plus `match is True` 条数 | `plus_match` | 9 | `plus_match` | 9 | 0 | 同名同维 |
| orig problems 条数 | `orig_problems` | 24 | `orig_problems` | 24 | 0 | 同名同维 |
| plus problems 条数 | `plus_problems` | 23 | `plus_problems` | 23 | 0 | 同名同维 |
| orig warnings 条数 | **未写入 totals** | （可由 A.results 重算 = 18） | `orig_warnings` | 18 | — | **B 独有维度** |
| plus warnings 条数 | **未写入 totals** | （可由 A.results 重算 = 11） | `plus_warnings` | 11 | — | **B 独有维度** |
| declared 序列不一致件数 | **无** | — | 顶层 `declared_mismatch_files` | 0 | — | **B 独有顶层键** |

- **7 键 / 9 键**：A 的 `totals` 为 7 键，B 为 9 键；B 顶层还多 1 个键 `declared_mismatch_files = 0`（`_f2v_run.py:28,40-41,71`）。
- B 比 A 多 4 个 `totals` 键，但其中 **2 个只是改名**（`orig_collected`/`plus_collected`），**2 个才是真新增维度**（`orig_warnings=18` / `plus_warnings=11`）。「实质维度数」= 9。
- **值差**：共同 5 键 `value_diff {}`；别名对 `orig_path 1 == orig_collected 1`、`plus_path 9 == plus_collected 9`。
- **更深的核验**（`python -I -X utf8 D:/Project/ra2-campaign-forge/lead/two_products_20261109/_tp_crosscheck.py`，实跑）：从两份各自 `results[]` 独立重算 9 维 canonical 向量逐项全等，连 A **没写进** `totals` 的 warnings 两维也算得出 18/11；输出 `canonical_equal = True` / `violations = 0` / `RESULT = OK` / `rc=0`。复核员 `_tpv_independent.py` 的独立重算（本会话实跑）同样给出 `A canon == B canon`、`canonical_equal True`、9 维 `19/1/9/0/9/24/23/18/11` 全等。

### 2(c) `results[]` 结构差

命令输出（实跑）：

```
A.result_keys ['file', 'orig', 'orig_overall', 'other_predicates_fail', 'plus', 'plus_overall']            (6 键)
B.result_keys ['declared_seq_same', 'file_verdict_regression', 'idx', 'n_bindings', 'new_problems_vs_orig',
               'orig_match', 'orig_paths', 'orig_problems', 'orig_verdict_r11', 'orig_warnings',
               'plus_match', 'plus_paths', 'plus_problems', 'plus_tiers', 'plus_verdict_r11',
               'plus_warnings', 'rel']                                                                    (17 键)
A.result_keys_only = A 的 6 键；B.result_keys_only = B 的 17 键（零交集）
```

| 项 | A | B | 核查结论 |
|---|---|---|---|
| 条数 | 30 | 30 | 全等 |
| 载体 | `results[i].orig.bindings[]` / `plus.bindings[]` 嵌套完整 binding dict | 5 条平行数组 `orig_paths/plus_paths/orig_match/plus_match/plus_tiers` | **结构完全不同** |
| binding 键集 | orig 3 键 `{declared, match, path}`；plus 11 键 `{alt, bytes, citation, declared, match, path, recomputed, suffix_stripped, tier, tried, verified_path}` | 无 binding 对象，只留投影 | 本次会话实读全量并集 |
| `declared` 文本 | 逐行完整保留 | 不保留，只留 `declared_seq_same` 布尔 | B 是投影、A 是超集 |
| 文件表示 | 绝对 `file` | 相对 `rel` | 归一后**文件集与顺序全等** |

路径表示核验（本会话实跑 `python -I -X utf8 -c "…normcase+realpath…"`）：

```
normcase set onlyA/onlyB: 0 0   order same: True
realpath set onlyA/onlyB: 0 0   order same: True
A file sample: D:\Project\ra2-campaign-forge\lead\GOAL3T_CRITERIA_STATUS_20261021.md
B rel sample : lead/GOAL3T_CRITERIA_STATUS_20261021.md
per-binding mismatches: []
B declared_seq_same all True: True
B n_bindings == A orig.bindings len all: True
```

**任务书【两产物对比】给的 6 件 `files_only_A` 是路径表示差异，不是漏件**：`_g9_regression_out.json:results_30` 每行同时带 `file`（绝对）与 `rel`（相对），A 取 `file`（`_f2_compare.py:38`），B 取 `rel`（`_f2v_run.py:30-31`）；两种归一后 `onlyA 0 / onlyB 0 / order same True`。逐绑定行 `path/match/tier` 投影 0 处不一致。

### 2(d) ★「不同口径」还是「算错」？——判 **不同口径**

**当前盘两份数值零不一致，故「算错」不成立**。依据：

1. 共同 5 键 `value_diff {}`、别名对全等、9 维 canonical 向量逐项全等、30 件逐绑定行投影全等（§2(b)(c)）。
2. **计数语义其实是同一套**：`_f2_compare.py:66-69` 与 `_f2v_run.py:61-64` 逐字同式（仅累加器变量名 / 键名不同），输入同为 `g7.r11_scan(...)` 与 `f2p.r11_scan_plus(...)`（`_f2_compare.py:41-42` / `_f2v_run.py:34-35`）。所以**「不同口径」只发生在投影层**（键名 / 维度覆盖 / 布局），不发生在「数什么」。
3. 两份还**共享同一已知缺陷**：merged 计入 `match` 不计入 `path`（`_f2_compare.py:67,69` / `_f2v_run.py:62,64`）。本会话 `grep -n -E "merged|by_kind|schema_version|counting_policy" lead/r11_f2_fix_20261109/_f2_compare.py lead/r11_f2_fix_20261109/_f2v_run.py` → `grep_rc=1`（两生产者**零命中**）；`python -I -X utf8 -c "…顶层 marker…"` → 两份 JSON 顶层 `markers []`（无 `counting_policy`/`schema_version`/`by_kind`/`merged`）。这是「两份一起缺同一维度」，不是「一份对一份错」。

**处理方式必须分开，不能混**：

- **不同口径（本盘）** → 不能靠改某个数字修，要做**单点定义 / schema 统一**（§4）。差异会随维度增删复利。
- **算错** → 才去改聚合表达式的值并重算产物。
- **第三种（本盘真正的将来风险）**：口径分歧掩盖「**只改一处**」的漏改。当前相等只是因为两份都还没加 merged；一旦只改 A，数值就会变成真正的「漏改导致的算错」。§5 详述。

---

## 3 聚合代码差异（`:65-71` vs `:60-68` 逐行对照）

### 3(a) 逐行对照表（代码均本次会话实读）

| # | 维度 / 动作 | A：`_f2_compare.py` | B：`_f2v_run.py` | 差异性质 |
|---|---|---|---|---|
| 1 | 初始化 | `:35-36` 7 键 `tot={bindings, orig_path, plus_path, orig_match, plus_match, orig_problems, plus_problems}` | `:25-27` 9 键 `tot=dict(orig_collected, plus_collected, orig_match, plus_match, orig_problems, plus_problems, orig_warnings, plus_warnings, bindings)` | 键名 + 多 2 维 |
| 2 | 绑行总数 | `:65` `tot["bindings"] += len(o_bind)` | `:60` `tot["bindings"] += len(ob)` | **同式**（变量名不同） |
| 3 | orig 采集数 | `:66` `orig_path += sum(1 for b in o_bind if b["path"])` | `:61` `orig_collected += sum(1 for b in ob if b["path"])` | **同式、异名** |
| 4 | plus 采集数 | `:67` `plus_path += sum(1 for b in n_bind if b.get("path"))` | `:62` `plus_collected += sum(1 for b in pb if b.get("path"))` | **同式、异名** |
| 5 | orig match | `:68` `orig_match += sum(1 for b in o_bind if b["match"] is True)` | `:63` `orig_match += sum(1 for b in ob if b["match"] is True)` | **同式** |
| 6 | plus match | `:69` `plus_match += sum(1 for b in n_bind if b.get("match") is True)` | `:64` `plus_match += sum(1 for b in pb if b.get("match") is True)` | **同式** |
| 7 | orig problems | `:70` `orig_problems += len(o_prob)` | `:65` `orig_problems += len(op)` | **同式** |
| 8 | plus problems | `:71` `plus_problems += len(n_prob)` | `:66` `plus_problems += len(pp)` | **同式** |
| 9 | orig warnings | **无** | `:67` `orig_warnings += len(ow)` | B 纯增量 |
| 10 | plus warnings | **无** | `:68` `plus_warnings += len(pw)` | B 纯增量 |
| 11 | 顶层额外 | 无 | `:28,40-41,71` `declared_mismatch_files` 计数并写盘 | B 纯增量 |
| 12 | 写盘 | `:100` `{"totals": tot, "results": results}`，`indent=2` | `:70-72` `{"totals": tot, "declared_mismatch_files":…, "results": out}`，`indent=1` | 布局 / 序列化 |
| 13 | 前置断言 | `:24` g7 指纹；`:44-46` 绑行数 / declared 序列；`:48-50` 原 T1 path 不丢 | **无 assert**；`:39-41` 只把 `seq_ok` 记进结果 | A 三段硬断言、B 只记录 |
| 14 | 读文本 | `:39` `read_bytes().decode("utf-8")` | `:32` `read_text(encoding="utf-8")` | CRLF 行为不同（潜在漂移点，非现盘错误） |

### 3(b) 是否实质分歧 —— **没有实质口径分歧**

差异分三类，**没有「一个算 path、一个算 collected」的语义对立**：

1. **纯增量**：`orig_warnings`/`plus_warnings`（`_f2v_run.py:67-68`）与 `declared_mismatch_files`（`:28,40-41,71`）。A 的 `results[]` 里其实有 warnings 数据（`_f2_compare.py:57,60`），只是没聚合进 `totals`；从 A.results 重算得 18/11。
2. **纯改名**：`orig_path`↔`orig_collected`、`plus_path`↔`plus_collected`，表达式完全一样。
3. **布局 / 序列化**：嵌套 binding 对象 vs 5 条平行数组、`indent=2` vs `indent=1`、顶层键数、断言有无、读文本方式。

真正需警惕的是第 2 类：**同名不同维、同维不同名**混在一起，使「按键名比较」看起来像 4 个差异、实际只有 2 个真新增维度；任何按键名写的交叉校验都会误报。

### 3(c) ★ `plus_collected` 与 `plus_path` 是否同物 —— **是，同一计数**

1. **代码级**：`_f2_compare.py:67` = `tot["plus_path"] += sum(1 for b in n_bind if b.get("path"))`；`_f2v_run.py:62` = `tot["plus_collected"] += sum(1 for b in pb if b.get("path"))`。除累加器变量名外逐字同式，输入都是 `r11_scan_plus(...)` 返回的绑定列表（`:42` / `:35`）。
2. **数据级**：实跑 `alias orig 1 1` / `alias plus 9 9`；两份 `results[]` 各自重算 `plus_collected` 均为 9。
3. **结构级**：B 的 `results[].plus_paths`（`_f2v_run.py:49`）与 A 的 `results[].plus.bindings[].path`（`_f2_compare.py:59`）逐条相等（本会话实跑 `per-binding mismatches: []`）；orig 侧同理（1 = 1）。
4. **语义级**：`_f2_r11plus.py:196` 建 `rec = {"declared": …, "path": path, "match": None, "citation": …}`；`:268` 命中时 `rec.update({"match": True, "path": verified["candidate"], "tier": …, "verified_path": …, "recomputed": …, "bytes": …})`；`:306` `bindings.append(rec)`。`path` 是「解析到的单一对象路径」，两个生产者都在数「`path` 真值的绑定行条数」。B 叫它 `collected`，A 叫它 `path`，**同一计数**。

同名对里唯一名实不符的是 `plus_match`：它数 `match is True`（`_f2_compare.py:69` / `_f2v_run.py:64`），而 merged 行 `path=None, match=True`（`lead/merged_contract_20261109/_mm_project_out.txt:12` 实读：`tier='SAMEDOC_LINK_EQ' match=True path=None members_n=2`）。故 `match` 不是「有路径且已回验」而是「判定为真」——正是两份**共享的维度缺失**。

### 3(d) `results[]` 结构是否一致 —— **不一致（布局），语义投影一致**

| | A | B |
|---|---|---|
| 载体 | 嵌套 dict `orig.bindings[]` / `plus.bindings[]` | 5 条平行数组 `orig_paths/plus_paths/orig_match/plus_match/plus_tiers` |
| 键集 | orig 3 键；plus 11 键（本次实读全量并集） | 无 binding 对象；只有 `path`/`match`/`tier` 投影 + `n_bindings`/`declared_seq_same` |
| `declared` 文本 | 逐行完整保留 | 不保留，只留布尔 |
| problems/warnings | 嵌套 list | 顶层 list |
| 逐条值 | — | 30 件 × 5 数组与 A 逐条相等（实跑），`declared_seq_same` 全 True，`n_bindings` 全等于 A 绑行数 |

结论：**绑定行「信息结构」不同（A 是超集、B 是投影），但重叠字段的语义与取值完全一致**。B 丢掉 `declared`/`recomputed`/`verified_path`/`citation`/`tried`，无法独立做「SHA 逐字比对」类语义核验，只能做计数核验。

补充：A `read_bytes().decode` vs B `read_text` 的差异在现盘未造成数值差（既有 C13/C14 记录 `B2B_PREAUDIT.md` 有 195 处 CRLF、长度 14467 vs 14272，但该件 0 绑行、problems/warnings 逐项相同）。本会话另实跑确认「扁平 rows 会丢 problems」的规模：`A zero-binding files WITH problems` 共 **23 件**（每件 `orig_problems=1`）——这正是 §4 单点定义必须用**逐件 view** 而非扁平逐绑行的量化依据。

---

## 4 单点定义方案（≥2 方案 + 影响面 + 一致性断言 + 可粘贴片段）

### 4(a) 现状 → 理想

现状：`_f2_compare.py:35-36,65-71,100` 与 `_f2v_run.py:25-27,60-68,70-72` **各自硬编码一份维度清单 + 各写一遍 7~9 条 `sum(...)`**，无共享定义、无 `schema_version`、无 `counting_policy`（§2(d) 实读）。两份相等只是「同一段逻辑被抄两遍且都没改」的巧合基线；`COUNT_INVARIANTS.md:669` 已把「第二份产物漂移无监控」列为长期代价。

理想：**维度清单与聚合表达式只存在一处**（**单点定义**），两生产者只负责产出 `results[]` 与调用共享聚合器，并让自己写出的 `totals` 携带可机检的策略标识。

### 4(b) 四个方案（含推荐）

**甲：抽共享聚合函数，两生产者都调它。** 新增 `_counting_policy` 模块导出 `DIMENSIONS`（canonical 键 → 取值函数）、`aggregate(binding_rows)`、`ALIASES`（canonical → A/B 历史键）、`policy_id()`；两生产者删掉各自 7~9 条 `tot[...] +=`，改成把 `results[]` 规整成统一逐件 view 后调 `aggregate()` 再按别名投影写盘。新增维度只改 `DIMENSIONS` 一处。
- 优：保留两份用途与全部消费者；新增维度天然同步；`policy_id()` 可直接做断言。
- 缺：两个生产者文件仍要改（各一处 import + 一处调用），**指纹锁必 DRIFT**；两份 `results[]` 布局仍不同，适配层本身可能写错（首跑扁平 rows 就丢了 23 件 0 绑行件的 problems，见 §3(d)）。

**乙：只留一份产物，另一份改为读它。** 把 A 定为唯一权威（完整 binding 对象、4 消费者 + 3 件指纹锁引用），B 改为读 A 后投影成历史 schema，或让 B 的读者改读 A。
- 优：**结构上不可能只改一处**；最彻底。
- 缺：破坏 B 的「独立对跑」（`_f2v_run.py:2-4` F2V-03 自述「全部自算」）——不再有两条独立路径，A 的聚合错会同时污染 A 与 B，交叉校验退化为自我比对；且 `_mkv_consumers.py:120`、`_mm_probe.py:124` 依赖 B 的 `idx/rel/parallel arrays` 形状，投影层要兼容。

**丙：两份各自算 + 交叉校验门禁。** 保留两份完全不动，新增只读门禁（现盘 `_tp_crosscheck.py` 即原型）：从两份 `results[]` 独立重算 9 维、别名归一后互比，各自检查 `totals` 自洽。
- 优：**零改动既有件**（本任务铁律下唯一可立即落地）；现盘 `violations=0 RESULT=OK rc=0`（本会话实跑）。
- 缺：**事后检测**不是事前预防；只能发现「结果值不一致」，抓不到「两份一起漏改同一维度」。且**现盘实现为 partial**——见 §4(d) 与 §6。

**丁（推荐 = 甲 + 丙 + 策略标识）：共享聚合 + `counting_policy`/`schema_version` + 必跑修正版门禁。** 以甲的 `DIMENSIONS` 为唯一定义，两份产物各写 `counting_policy = hashlib.sha256(规范化维度清单).hexdigest()` 与 `schema_version`；门禁断言「两份策略哈希相等且等于**所有者登记的目标策略哈希**」+「canonical totals 全 9 维相等」+「各自 totals 自洽 + 键集等于别名表」。
- 新增维度只改一处（甲）；漏改在策略哈希层面立刻暴露；门禁不改生产者即可上线，生产者改造可分阶段。
- **本会话只交付丁的设计片段与实跑自测，不落地任何生产者改造。**

推荐理由：甲单独做「没人跑门禁就白搭」，丙单独做「两份一起漏改抓不到」，乙破坏 B 的独立复算能力。丁以最小破坏面同时拿到三者优点。

### 4(c) 对 4 个消费者与指纹锁的影响

实跑 `for f in lead/r11_f2_fix_20261109/_f2w_*.py; do grep -c "totals" "$f"; done` → **5 个 `_f2w_*.py` 全部 `totals_hits=0`**（任务书所指 4 消费者 `_f2w_checks.py` / `_f2w_extract.py` / `_f2w_pass.py` / `_f2w_final.py` 全 0，另有 `_f2w_dogfood.py` 亦 0）；`grep -n "totals" …/_f2w_*.py` → `rc_grep=1`。`grep -n "_f2v_run|plus_collected|orig_warnings" lead/count_invariant_20261109/_ci_checks.py` → `rc_grep=1`（`_ci_checks.py` 只覆盖 A，`COUNT_INVARIANTS.md:659` 明说「判不了跨文件一致」）。

| 方案 | 对 4 消费者 | 对 3 件 `_f2d*_fpcheck` | 其他登记面 |
|---|---|---|---|
| 甲 | A 的 `results[]` 形状不动 → 0 影响 | A 产物字节变 → **3 件全 DRIFT**，需重基线 | 生产者 `.py` 指纹变 → `_mm_fp.py` / `_mkv_fp.py` / `_mk_probe.py` 失配；`_ow_raw_hits.json` 四件 fileMeta stale |
| 乙 | 保留 A 形状 → 0 影响；删/改 B 读者则 `_mkv_consumers.py:120`、`_mm_probe.py:124` 要改 | A 不变则 3 件仍 MATCH | B 产品指纹 `a62ee13e…` 变 / 废 |
| 丙 | **0 影响**（新增只读门禁） | **3 件仍 MATCH** | 新增门禁自身指纹；`_ci_checks.py` 仍只覆盖 A |
| 丁（推荐） | 门禁阶段 0；共享聚合落地阶段同甲 | 门禁阶段 MATCH；聚合落地阶段同甲 | 同甲 + 需在台账登记目标 `counting_policy` 哈希 |

**关键不对称**：实跑 `python -I -X utf8 -c "…3 件锁是否含 B 产品/生产者…"` → 三件 `_f2d_fpcheck.py` / `_f2dw_fpcheck.py` / `_f2dv_fpcheck.py` 全部 `locks_B_product=False locks_A_producer=False locks_B_producer=False`（清单见 `_f2d_fpcheck.py:7-17`、`_f2dw_fpcheck.py:14-33`、`_f2dv_fpcheck.py:18-55`，均锁 A 产物 `148ea8d6…/44958`）。故「只漏改 B」三件**一件都抓不到**；「只改 A 的 totals」反而被三件报 DRIFT——而那恰好是**合法**改动（`COUNT_INVARIANTS.md:668` 「合法改动与篡改不可分」）。

### 4(d) ★ 口径一致性可机检断言（TP-1..TP-7）

不能只比 `totals` 键集（会误判改名），也不能只比共同键值（只改一处时共同键可能仍相等）。必须同时断言：

```
TP-1  文件集/顺序：normcase(normpath(A.results[i].file)) == normcase(normpath(REPO / B.results[i].rel))  ∀i，且集合相等
TP-2  条数：len(A.results) == len(B.results)
TP-3  逐件绑行数：len(A.results[i].orig.bindings) == B.results[i].n_bindings
TP-4  逐绑定行投影：A.orig.bindings[].path / A.plus.bindings[].{path,match,tier}
                    == B.{orig_paths,plus_paths,orig_match,plus_match,plus_tiers}[]  逐条
TP-5  canonical 向量相等（★ 全部 9 维，别名归一，不看 totals）：
       canon_from_A(A.results) == canon_from_B(B.results)
       9 维 = {bindings, orig_collected, plus_collected, orig_match, plus_match,
               orig_problems, plus_problems, orig_warnings, plus_warnings}
       别名表：A.orig_path↔orig_collected, A.plus_path↔plus_collected
TP-6  自洽：A.totals[k_A] == canon_from_A(A.results)[k] ∧ B.totals[k_B] == canon_from_B(B.results)[k]
TP-6b totals 键集：set(A.totals) == {ALIASES 中 A 侧非 None 的键} ∧ set(B.totals) == {B 侧非 None 的键}
TP-7  策略标识：A.counting_policy == B.counting_policy == 目标策略哈希（owner 登记）
               ∧ A.schema_version == B.schema_version
```

「同一套口径」的直接判据：`TP-1..TP-6b` 全通过 ∧ 两份 `counting_policy` 相等且等于目标值。当前盘两份均无 `counting_policy`（§2(d) 实读），TP-7 只能标 **unconfirmed**；此时最多证明「本次两份数值同口径」，**不能证明将来新增维度仍同口径**。

**必须如实披露：现盘 `_tp_crosscheck.py` 是 partial 实现，不等于上述 TP-1..TP-7**。本次会话实读 `_tp_crosscheck.py:28`（`COMMON` 只取 A 侧非 None 的 7 维）、`:98-102`（TP-5 只遍历 `COMMON`）、`:125`（只 `print` `canonical_equal` 9 维）、`:129-130`（`RESULT`/`rc` 只看 `v`，9 维不等不进 `v`）；无 `TP-6b` 键集断言、无 TP-7 落地（`_tp_ALIGNMENT.md:338-347` 的 6 行 `policy_check` 只是设计片段）。这与 `_tp_ALIGNMENT.md:231-235`（TP-5 声明 9 维）、`:324`（伪码 `if canon_from_A(A)!=canon_from_B(B): v.append`）、`:246`/`:393`（「三个只改一处反例全部报警 / 至少把数值分叉堵住」）不符。复核 verdict 因此为 `partial`（§6）。

### 4(e) 可粘贴片段（均本次会话以 `python -I -X utf8 -c "…"` 实跑自测，未写入任何文件）

**(i) 单点定义模块 `_counting_policy.py`（设计片段，未落地、未改任何既有件）**

```python
# 统一 view = 逐「件」记录 files[]；每件带 bindings[] + 逐件 problems/warnings 列表。
# ★ 必须逐件而非扁平逐绑行：30 件里 23 件是 0 绑行但仍有 orig_problems=1（§3(d) 实跑），
#   扁平化会丢掉它们的 problems/warnings。
import hashlib, json

DIMENSIONS = {
    "bindings":       lambda fs: sum(len(f["bindings"]) for f in fs),
    "orig_collected": lambda fs: sum(1 for f in fs for b in f["bindings"] if b["orig_path"]),
    "plus_collected": lambda fs: sum(1 for f in fs for b in f["bindings"] if b["plus_path"]),
    "orig_match":     lambda fs: sum(1 for f in fs for b in f["bindings"] if b["orig_match"] is True),
    "plus_match":     lambda fs: sum(1 for f in fs for b in f["bindings"] if b["plus_match"] is True),
    "orig_problems":  lambda fs: sum(len(f["orig_problems"]) for f in fs),
    "plus_problems":  lambda fs: sum(len(f["plus_problems"]) for f in fs),
    "orig_warnings":  lambda fs: sum(len(f["orig_warnings"]) for f in fs),
    "plus_warnings":  lambda fs: sum(len(f["plus_warnings"]) for f in fs),
}
ALIASES = {                      # canonical -> (A 历史键, B 历史键)
    "bindings":       ("bindings", "bindings"),
    "orig_collected": ("orig_path", "orig_collected"),
    "plus_collected": ("plus_path", "plus_collected"),
    "orig_match":     ("orig_match", "orig_match"),
    "plus_match":     ("plus_match", "plus_match"),
    "orig_problems":  ("orig_problems", "orig_problems"),
    "plus_problems":  ("plus_problems", "plus_problems"),
    "orig_warnings":  (None, "orig_warnings"),
    "plus_warnings":  (None, "plus_warnings"),
}
def policy_id():
    spec = json.dumps(sorted(DIMENSIONS), ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(spec.encode("utf-8")).hexdigest()
def aggregate(files):
    return {k: int(fn(files)) for k, fn in DIMENSIONS.items()}
def project(canon, side):        # side=0 -> A, 1 -> B
    i = 0 if side == 0 else 1
    return {pair[i]: canon[k] for k, pair in ALIASES.items()
            if pair[i] is not None and k in canon}

# 两生产者各自（示意，未执行）：把 for 循环里 7~9 条 tot[...] += 全删，改为
#   from _counting_policy import aggregate, project, policy_id
#   tot = project(aggregate(files), SIDE)          # SIDE=0 或 1
#   doc["counting_policy"] = policy_id(); doc["schema_version"] = 2
```

实跑自测输出（把现盘 `A.results` 规整成 30 条逐件 view 后）：

```
SNIPPET1 policy_id = 8b6015a9a51ef1cf59cf2a7a43f9ebca57a7fd6948ed1aa4de3dbe139282aeb0
SNIPPET1 canon = {"bindings": 19, "orig_collected": 1, "orig_match": 0, "orig_problems": 24, "orig_warnings": 18, "plus_collected": 9, "plus_match": 9, "plus_problems": 23, "plus_warnings": 11}
SNIPPET1 A equals disk totals = True {'bindings': 19, 'orig_path': 1, 'plus_path': 9, 'orig_match': 0, 'plus_match': 9, 'orig_problems': 24, 'plus_problems': 23}
SNIPPET1 B equals disk totals = True {'orig_collected': 1, 'plus_collected': 9, 'orig_match': 0, 'plus_match': 9, 'orig_problems': 24, 'plus_problems': 23, 'orig_warnings': 18, 'plus_warnings': 11, 'bindings': 19}
```

即 `project(aggregate(files), 0)` 得 A 的 **7 键**、`project(..., 1)` 得 B 的 **9 键**，分别与现盘 `A.totals` / `B.totals` 全等。`policy_id()` 的 8b6015a9… 是**片段自测值**，台账中**尚未登记**该目标策略哈希（未验，须所有者裁决登记，见 §5(d)）。

**(ii) 修正版交叉门禁 `check()`（闭合 §4(d) 的 partial 盲区；设计片段，未落地、未修改 `_tp_crosscheck.py`）**

```python
import json, os, pathlib
ROOT = pathlib.Path(r"D:\Project\ra2-campaign-forge")
CANON = {                       # canonical -> (A 别名, B 别名)；9 维全列，不裁 COMMON
    "bindings":       ("bindings", "bindings"),
    "orig_collected": ("orig_path", "orig_collected"),
    "plus_collected": ("plus_path", "plus_collected"),
    "orig_match":     ("orig_match", "orig_match"),
    "plus_match":     ("plus_match", "plus_match"),
    "orig_problems":  ("orig_problems", "orig_problems"),
    "plus_problems":  ("plus_problems", "plus_problems"),
    "orig_warnings":  (None, "orig_warnings"),
    "plus_warnings":  (None, "plus_warnings"),
}
EXPECT_A = {a for a, b in CANON.values() if a is not None}
EXPECT_B = {b for a, b in CANON.values() if b is not None}
TARGET = None                   # ★ 落地时改为 owner 登记的目标策略哈希；当前盘 None = 不假装有登记

def canon_A(d):                 # 只读 A.results，不看 A.totals
    R = d["results"]
    return {
      "bindings":       sum(len(r["orig"]["bindings"]) for r in R),
      "orig_collected": sum(1 for r in R for b in r["orig"]["bindings"] if b["path"]),
      "plus_collected": sum(1 for r in R for b in r["plus"]["bindings"] if b.get("path")),
      "orig_match":     sum(1 for r in R for b in r["orig"]["bindings"] if b["match"] is True),
      "plus_match":     sum(1 for r in R for b in r["plus"]["bindings"] if b.get("match") is True),
      "orig_problems":  sum(len(r["orig"]["problems"]) for r in R),
      "plus_problems":  sum(len(r["plus"]["problems"]) for r in R),
      "orig_warnings":  sum(len(r["orig"]["warnings"]) for r in R),
      "plus_warnings":  sum(len(r["plus"]["warnings"]) for r in R)}

def canon_B(d):                 # 只读 B.results，不看 B.totals
    R = d["results"]
    return {
      "bindings":       sum(r["n_bindings"] for r in R),
      "orig_collected": sum(1 for r in R for v in r["orig_paths"] if v),
      "plus_collected": sum(1 for r in R for v in r["plus_paths"] if v),
      "orig_match":     sum(1 for r in R for v in r["orig_match"] if v is True),
      "plus_match":     sum(1 for r in R for v in r["plus_match"] if v is True),
      "orig_problems":  sum(len(r["orig_problems"]) for r in R),
      "plus_problems":  sum(len(r["plus_problems"]) for r in R),
      "orig_warnings":  sum(len(r["orig_warnings"]) for r in R),
      "plus_warnings":  sum(len(r["plus_warnings"]) for r in R)}

def check(A, B, target=TARGET):
    v = []
    fa = [os.path.normcase(os.path.normpath(r["file"])) for r in A["results"]]
    fb = [os.path.normcase(os.path.normpath(os.path.join(str(ROOT), r["rel"].replace("/", os.sep))))
          for r in B["results"]]
    if fa != fb or set(fa) != set(fb): v.append("TP-1 文件集/顺序")
    if len(A["results"]) != len(B["results"]): v.append("TP-2 条数")
    if any(len(a["orig"]["bindings"]) != b["n_bindings"]
           for a, b in zip(A["results"], B["results"])): v.append("TP-3 n_bindings")
    for i, (a, b) in enumerate(zip(A["results"], B["results"])):
        ob, pb = a["orig"]["bindings"], a["plus"]["bindings"]
        for tag, x, y in (("orig_paths",  [t["path"] for t in ob],      b["orig_paths"]),
                          ("plus_paths",  [t.get("path") for t in pb],  b["plus_paths"]),
                          ("orig_match",  [t["match"] for t in ob],     b["orig_match"]),
                          ("plus_match",  [t.get("match") for t in pb], b["plus_match"]),
                          ("plus_tiers",  [t.get("tier") for t in pb],  b["plus_tiers"])):
            if x != y: v.append("TP-4 idx=%d %s" % (i, tag))
    ca, cb = canon_A(A), canon_B(B)
    for k in CANON:                          # ★ 全部 9 维（原实现只遍历 COMMON 7 维）
        if ca[k] != cb[k]: v.append("TP-5 canonical %s A=%r B=%r" % (k, ca[k], cb[k]))
    for label, doc, calc, side in (("A", A, ca, 0), ("B", B, cb, 1)):
        for k, (ka, kb) in CANON.items():
            alias = ka if side == 0 else kb
            if alias is None: continue
            if doc["totals"].get(alias, "<ABSENT>") != calc[k]:
                v.append("TP-6 %s.totals.%s=%r != %r" % (label, alias, doc["totals"].get(alias), calc[k]))
    for label, doc, exp in (("A", A, EXPECT_A), ("B", B, EXPECT_B)):   # ★ 键集断言（原实现无）
        got = set(doc["totals"])
        if got != exp:
            v.append("TP-6b %s.totals 键集多了 %s 少了 %s" % (label, sorted(got - exp), sorted(exp - got)))
    pa, pb_ = A.get("counting_policy"), B.get("counting_policy")
    if pa is None and pb_ is None:
        print("  TP-7 UNCONFIRMED: 两份均无 counting_policy（当前盘预期；不伪造通过、不纳入 rc）")
    elif pa is None or pb_ is None:
        v.append("TP-7 只有一份写了 counting_policy")
    else:
        if pa != pb_: v.append("TP-7 counting_policy 不一致 A=%s B=%s" % (pa, pb_))
        if target is not None and pa != target: v.append("TP-7 counting_policy != 登记目标 %s" % target)
        if A.get("schema_version") != B.get("schema_version"): v.append("TP-7 schema_version 不一致")
    return v, ca, cb
# main(): A=json.loads(A_path.read_text(...)); B=...; v,ca,cb=check(A,B); print("RESULT", "OK" if not v else "FAIL"); sys.exit(0 if not v else 1)
```

实跑自测（同一份 `python -I -X utf8 -c "…"` 内对现盘 + 复核员全部 `_tpv_*` 构造样本逐一调用，`TARGET` 用片段(i) 的 `8b6015a9…` 作**假定**目标值）：

| 样本 | 修正门禁 rc / 违规数 | 现盘 `_tp_crosscheck.py` rc | 说明 |
|---|---|---|---|
| baseline（A0/B0） | `rc=0 violations=0 canonical_equal=True` | `rc=0` | 现盘 OK；TP-7 打印 UNCONFIRMED |
| X1 只改 A.results plus.warnings +1 | `rc=1`（`TP-5 canonical plus_warnings A=12 B=11`） | **`rc=0`** | 现盘盲区（warnings 维） |
| X1b 只改 A.results orig.warnings +3 | `rc=1`（`TP-5 canonical orig_warnings A=21 B=18`） | **`rc=0`** | 现盘盲区（对应 `_mm_project_out.txt:7` 11→14 漂移） |
| X2 只改 A 插 merged 行 + totals 自洽 | `rc=1 violations=4`（TP-4×3 + TP-5） | `rc=1 violations=4` | 两者都抓 |
| X3 只改 A.totals | `rc=1 violations=2`（TP-6×2） | `rc=1 violations=2` | 两者都抓 |
| X4 只改 B.results orig_warnings +1 | `rc=1 violations=2`（TP-5 + TP-6） | `rc=1 violations=1` | 修正版多报 TP-5 |
| Y1 只给 A.totals 加 `merged_count=1` | `rc=1`（`TP-6b 多了 ['merged_count']`） | **`rc=0`** | 现盘盲区（新增维度键） |
| Y2 只给 B.totals 加 `merged_count=1` | `rc=1`（`TP-6b 多了 ['merged_count']`） | **`rc=0`** | 同上 |
| Y3 A 侧把 warnings 两维补进 totals | `rc=1`（`TP-6b 多了 ['orig_warnings','plus_warnings']`） | **`rc=0`** | 同上 |
| Y5 两份一起写相同假 `counting_policy` | `rc=1 violations=3`（TP-6b×2 + TP-7 与假定目标不符） | **`rc=0`** | 现盘无 TP-7 |
| X5 / Y4 只改 A 的 verdict / `other_predicates_fail` / `plus.verdict` | `rc=0` | `rc=0` | **诚实边界**：非计数业务字段不在本门禁口径内（§6 边界 3） |

自测说明：X1/X1b/Y1/Y2/Y3/Y5 在现盘门禁下 `canonical_equal=False` 或键集已变却仍 `RESULT=OK rc=0`，正是复核 verdict = `partial` 的实证；修正片段把它们全部转为 `rc=1`。**修正片段只是设计 + 实跑自测，未写入 `_tp_crosscheck.py`，未改任何生产者或机读件**；`TARGET` 为假定值，台账未登记（未验）。

---

## 5 只改一处风险（传导链 + 双读者 + 指纹锁 + 防漏改）

### 5(a) 传导链（以「只给 `_f2_compare.py` 接 merged、漏 `_f2v_run.py`」为例）

依据既有实跑投影 `lead/merged_contract_20261109/_mm_project_out.txt:2-7,12,22-24`（本会话实读）与本会话实跑反例：

1. **改 A 的谓词**：merged rec 形状 `tier=SAMEDOC_LINK_EQ, match=True, path=None, members_n=2`（`_mm_project_out.txt:12`）。
2. **A 的 totals 变**：`_mm_project_out.txt:2-4` BEFORE `{plus_path:9, plus_match:9}` → AFTER `{plus_path:17, plus_match:18}`；`:22` 记 `_f2_compare.py:67/69` 对该 merged 单条计 `(0,1)`。A 产物字节与指纹随之变（既有 C18 模拟 `0dfa0309…`/43797 ≠ 基线）。
3. **B 不动（漏改）**：`_f2v_run.py:62,64` 仍按旧口径，9 键 totals 保持 `{plus_collected:9, plus_match:9, …}`。
4. **数值分叉**：别名归一后 `plus_collected` A=17 / B=9、`plus_match` A=18 / B=9。`_mm_project_out.txt:24` C7 记的是**同时改两份**时 B 的 `plus_paths=[None] plus_match=[True]` 同步漂移；只改 A 时 B 的 `plus_paths` 连 None 都不会出现，两份 `results[]` 直接分叉。
5. **消费者侧静默**：4 个 `_f2w_*` 只读 A 的 `results[]` 且 0 处读 `totals`（§4(c) 实跑）；`_mm_project_out.txt:19-23` C2–C5 记它们对 merged 的反应（`sha_ok=False`、`verified='' bytes='-'`、`plus match +=1`），**没有一个是「B 与 A 不一致」的报警**。
6. **`_ci_checks.py` 只覆盖 A**（§4(c) 实跑无 B 引用；`COUNT_INVARIANTS.md:659` 明说「判不了跨文件一致」），对 B 的漂移 0 输出。
7. **结论**：只改一处可以一路走到「A 已升级、B 仍旧、无人报警」，直到人工对账或接入**修正版**门禁。现盘门禁对 X2 型（插 merged 行）能报 4 条，但对 X1/X1b/Y1/Y2/Y3/Y5 型静默（§4(e)(ii) 实跑）。

### 5(b) 谁同时读两份

实跑命令（全仓 `rglob` 版本 120s 超时后被 `TaskStop` 终止，**未作为结论依据**；改用下列 `lead/` 范围命令）：

```
grep -rl "_f2_compare_out.json" lead --include="*.py" | sort > /tmp/onlya.txt
grep -rl "_f2v_run_out.json"   lead --include="*.py" | sort > /tmp/onlyb.txt
comm -12 /tmp/onlya.txt /tmp/onlyb.txt
```

输出 BOTH = `lead/merged_contract_20261109/_mkv_consumers.py`、`lead/merged_contract_20261109/_mm_probe.py`（另 4 件是写域 `_tp_*`/`_tpv_*` 新增件）；ONLY B = `_f2v_run.py`（生产者自己写）。

逐行实读：
- `_mkv_consumers.py:118-125` 的 G 段只是分别 `print` 两件 `top_keys/totals/results_n`；`:127-142` 的 H 段只对 **A** 重算并在 `:142` 判 `EQUALS`；**零 A-vs-B 断言**。
- `_mm_probe.py:81-86` 打印 4 件 fileMeta；`:89-113` 的 §CMP 只对 A 重算并在 `:103` 判 `EQUALS`；`:116-120` 的 §JSONREAD 只查 4 消费者字面；`:123-126` 的 §RUN 只 `print` B 的 `top_keys`/`totals`；**零交叉断言**。

两件都是一次性审计输出、不 `assert`、非常驻门禁。因此「撞出矛盾」目前不会发生——不是因为一致，而是**根本没人把两份放一起比**（`COUNT_INVARIANTS.md:669`）。

### 5(c) 指纹锁能否抓到 —— **抓不到「只漏改 B」；「只改 A」会误报**

本会话实跑三件锁：`python -I -X utf8 D:/…/_f2d_fpcheck.py` 等 → `_f2d_fpcheck.py` 输出 JSON（9/9 全含 `sha256 == expect_sha`）、`rc=0`；`_f2dw_fpcheck.py` → `== RESULT bad=0 ==`、`rc=0`；`_f2dv_fpcheck.py` → `== baseline/prefix 比对小结: MATCH=20 MISMATCH=0 ==`、`rc=0`。

| 锁 | 锁 A 产物 | 锁 B 产物 | 锁两生产者 .py |
|---|---|---|---|
| `_f2d_fpcheck.py:7-17` | ✅ `148ea8d6…/44958` | ❌ | ❌ |
| `_f2dw_fpcheck.py:14-33` | ✅ 同上 | ❌ | ❌ |
| `_f2dv_fpcheck.py:18-55` | ✅ 同上 | ❌ | ❌ |

- **只漏改 B**：B 完全不在三件清单内 → 三件全 `MATCH`，**0 报警**。
- **只改 A**：三件都会报 DRIFT/MISMATCH，但报的是「A 变了」，**不区分合法口径升级与篡改**，也不提示「B 该同步却没同步」。
- 合起来正是 `COUNT_INVARIANTS.md:668`「指纹锁与口径改动互相掣肘」。

### 5(d) 防漏改机制（按成本递增；① 必须接「修正版」而非现盘版）

1. **立刻、零改动**：把**修正版**交叉门禁接成必跑门禁（`rc!=0` 即卡）。现盘 `_tp_crosscheck.py` 为 partial（X1/X1b/Y1/Y2/Y3/Y5 → `rc=0`），**不能直接当成「已堵住只改一处」**；须先按 §4(e)(ii) 落实 TP-5 全 9 维 + `canonical_equal` 并入 `v` + TP-6b 键集 + TP-7。
2. **补策略标识**：两份都写 `counting_policy` + `schema_version`（§4(e)(i)），门禁加 TP-7 并比对**所有者登记的目标策略哈希**；补上「两份一起漏改」的盲区。当前盘两份均无该字段 → TP-7 只能标 unconfirmed，不伪造通过。
3. **收口到单点定义**：按甲/丁把 `DIMENSIONS` 做唯一来源，删掉两生产者里 7~9 条 `totals[...] +=`；新增维度只改 `DIMENSIONS` + 目标策略哈希，两生产者零改动。
4. **指纹锁分层重基线**：把「内容指纹」（随合法口径升级而变）与「策略指纹」（`counting_policy` 哈希，须与裁决一致）分开；3 件 `_f2d*_fpcheck` 改为校验策略指纹 + **把 B 产物也纳入清单**（补 §5(c) 盲点）。重基线须登记 owner / 触发 SOP（`MERGED_MERGE_CONTRACT.md:735` 亦列「未验」）。
5. **清单化触发**：按 §6「新增维度清单」九条逐项跑；含至少 3 个「只改 A / 只改 B / 两份一起漏改」反例实跑确认门禁能报（本会话已给前两类与 Y5 型；纯「两份同步加同一新维度到 results 且 totals 一致」仍需 TP-7 + 已登记目标哈希才能判）。

---

## 6 复核回件（绑定行格式）+ 边界 + 未验项

### 6(a) 复核绑定行（本会话 `hashlib` 实算；固定格式）

被核对象 SHA256 = 148ea8d689eaaf582af05ea1bf4650605e104d6d74f8c7765e75a6eec662c7b1，字节数 = 44958

对象：`lead/r11_f2_fix_20261109/_f2_compare_out.json`（两份机读件之 A；§2(a) 命令 C1 实算）。

被核对象 SHA256 = a62ee13e3afe88a421d31859c8f11c11e95b78b9b6b5d362807b6ba990c50905，字节数 = 25200

对象：`lead/r11_f2_fix_20261109/_f2v_run_out.json`（两份机读件之 B）。

被核对象 SHA256 = 12e55acf42441aca846986a2447abffef77d774ee694cedf56a012c1c8907106，字节数 = 4821

对象：`lead/r11_f2_fix_20261109/_f2_compare.py`（A 生产者）。

被核对象 SHA256 = 75108dcaee4985f8623b59de18f8650ec6b78b73fbbd93ca3197f3057efdbd9a，字节数 = 3469

对象：`lead/r11_f2_fix_20261109/_f2v_run.py`（B 生产者）。

九件上游指纹全表见 §2(a)；末次复算 `ALL_UNCHANGED = True`。

### 6(b) 复核 verdict 如实记

- **verdict = `partial`**（如实照录任务书【复核】，不翻案、不美化）。
- **唯一不通过项**：④「只改一处」检不出。现盘 `_tp_crosscheck.py:28` 的 `COMMON` 只取 7 维、`:98-102` TP-5 只遍历 `COMMON`、`:125` 只 `print` `canonical_equal`、`:129-130` `RESULT`/`rc` 只看 `v`；与 `_tp_ALIGNMENT.md:231-235,324,246,393` 的 9 维 / 全报警表述冲突。本会话实跑复核员的 `_tpv_counterexamples.py` / `_tpv_counterexamples2.py` 复现：X1、X1b、Y1、Y2、Y3、Y5 → `rc=0 / RESULT=OK`（X1/X1b 还 `canonical_equal=False`）；控制组 X2/X3/X4 → `rc=1`（说明现盘门禁有部分价值）。
- **通过项**（复核员① ②③⑤⑥⑦）：九件指纹 9/9 全等；独立重算「零数值不一致 = 不同口径而非算错」成立；`plus_collected`≡`plus_path` 有代码级+数据级+结构级+语义级依据；全仓交集仅 `_mm_probe.py`/`_mkv_consumers.py` 且零 A-vs-B 断言；§5(a) 并存合理性有实据；只读域未改、HEAD 未变。
- **次要瑕疵**（如实）：`_tp_ALIGNMENT.md` 确为 494 行，但 §3(e)(ii):318-321 行号引用偏移（CANON 实 `:17-27`、`canon_from_A` 实 `:31`、`canon_from_B` 实 `:47`、`check` 实 `:71`，文档写 `:20-31/:34-52/:55-73/:86-…`）。
- **本件状态**：按任务书「refuted 或 partial 标 unconfirmed」，**本对齐件整体确认状态 = unconfirmed**。本件未把现盘门禁说成完整；§4(e)(ii) 给出的修正片段只是设计 + 实跑自测，**未落地**、未改 `_tp_crosscheck.py`、未改任何生产者或机读件。

### 6(c) 边界

**1. 两份并存合理性 —— 部分不同用途 + 明显历史冗余，判断：冗余为主。**
- 不同用途证据：`_f2_compare.py:2-6` 自述「第三步：30 件清单，原版 vs 增强版实跑对比」，带 3 段断言、保留完整 binding 对象供 `_f2w_extract.py:29-33` 逐条交付表 / `_f2w_checks.py:29` SHA 比对；`_f2v_run.py:2-4` 自述「F2V-03 独立对跑……全部自算」，额外产出 `declared_mismatch_files`、warnings 两维、平行数组。布局差异使二者确非字节级重复。
- 历史冗余证据（更强）：同一输入 `_g9_regression_out.json:results_30`、同一对函数、同一 30 件 / 19 绑行；9 个 canonical 维与逐绑定行投影全等；B 在生产链上**没有下游消费者**（§5(b) 只有 2 件一次性审计脚本读它），A 有 4 个交付消费者 + 3 件指纹锁 + `count_invariant` 全套；`COUNT_INVARIANTS.md:659,669`、`MERGED_MERGE_CONTRACT.md:163-165` 都把 B 记为「第二件带 totals 的机读件 / 须单独裁决是否同步」。
- 结论：B 的价值是「独立复跑的交叉验证」这一**过程**价值，不是「不可替代的数据」；其产物形态可保留，但**计数定义不应有第二份**。

**2. 若合并成一份，损失什么**：① 独立复算能力（最主要，乙会让 A 的错同时污染 A 与 B，交叉校验退化为自我比对）；② B 独有字段 `declared_mismatch_files` / `results[].new_problems_vs_orig` / `file_verdict_regression` / warnings 显式 totals，`_mkv_consumers.py:120`、`_mm_probe.py:124` 的结构快照会失效；③ B 的「无 assert、跑完全场再汇总」语义（`_f2v_run.py:39-41` vs `_f2_compare.py:44-50`）；④ B 指纹 `a62ee13e…/25200` 在 `_ow_raw_hits.json` 等登记面 stale。**不损失**：4 个既有交付消费者（只读 A）。

**3. 这条对齐工作判不了什么（如实列）**：
- 判不了语义正确（`match=True` 是否真对应正确对象；`COUNT_INVARIANTS.md:652` 记 `sha 逐字一致条数 = 8`），本会话**未重算** 19 条绑定所指向对象的 SHA256。
- 判不了该不该有 merged / 该用哪套裁决口径 / 键名与 `schema_version` 起点（`MERGED_MERGE_CONTRACT.md:28,572,639` 属所有者裁决），本件不拍板。
- 判不了「两份一起漏改」的**纯形态**：若新增维度在两处同时被加、两份 `results`/`totals` 同步且都不写 `counting_policy`，TP-1..TP-6b 全通过；只有 TP-7 + **已登记**的目标策略哈希能判。当前盘两份都无该字段，我在自测里用的 `TARGET=8b6015a9…` 只是片段假定值、台账未登记。
- 判不了 verdict 业务正确性 / tier 值语义 / 30 件清单代表性（`COUNT_INVARIANTS.md:653-657`）。本会话修正门禁对 X5/Y4（只改 `plus_overall`/`other_predicates_fail`/`plus.verdict`）仍 `rc=0`——这些非计数业务字段**不在本门禁口径内**，不冒称覆盖。
- 判不了 B 的读法差异是否永远无害：A `read_bytes().decode` vs B `read_text` 在 `B2B_PREAUDIT.md` 文本不同（既有 C13，195 处 CRLF），当前因该件 0 绑行而未显现；换语料是否仍一致**未验**。
- 判不了各方案落地后的 totals：本会话**未跑**两生产者本体（纪律禁止改/重跑产物）、未执行甲/乙/丁的生产者改造；`_mm_project_out.txt:2-4` 的 `(17,18)` 是既有实跑投影值，本会话只实读、未复跑。

**4. 以后新增计数维度时的清单（九条）**：
1. **先定单点**：只在 `DIMENSIONS`（或等价唯一定义处）增键 + 取值函数；**禁止**在两个生产者里各写一条 `totals[...] +=`。
2. **更新别名表**：写明新维度在 A/B 的历史键名（或 `None` = 该产物不写）；同步更新门禁 `CANON` 与 `canon_from_A/B`、`EXPECT_A/EXPECT_B`。
3. **算新 `policy_id()`**：`hashlib` 对规范化维度清单取 SHA256；把目标值登记到台账 / 判定书（owner + 生效 SOP），两份产物的 `counting_policy`/`schema_version` 一起升。
4. **两份同步落地或显式裁决不同步**：若裁决「B 不同步」，必须登记理由与 B 的预期值，否则门禁会误报；`MERGED_MERGE_CONTRACT.md:639` 把此项列为 step 0 裁决内容。
5. **跑修正版门禁**：`python -I -X utf8 …/crosscheck.py`，要求 `violations=0` 且 TP-7 策略哈希等于登记目标值；再跑 `COUNT_INVARIANTS.md` 的 INV-1..5 与反例集（条件化 `--expect-merged`）。
6. **补反例**：至少造 3 个「只改 A / 只改 B / 两份一起漏改」构造输入，实跑确认门禁 `rc=1`（本会话已给前两类与 Y5 型，第三类纯形态须 TP-7 + 已登记目标哈希）。
7. **重基线登记面**：3 件 `_f2d*_fpcheck`（A 产物 + 建议纳入 B）、`_mm_fp.py` 等生产者指纹锁、`_ow_raw_hits.json` 四件 fileMeta、报告中的指纹文字；**逐处记录新 sha/bytes**，不静默改；内容指纹与策略指纹分层。
8. **回放双向兼容**：旧 JSON 读新代码 / 新 JSON 读旧代码各跑一遍，确认 4 个 `_f2w_*` 消费者 `rc=0` 且输出字段不缺。
9. **最后**：`hashlib` 复算全部只读对象指纹，确认两件台账与只读域 `UNCHANGED`；不 commit、不 push（除非所有者另行指示）。

### 6(d) 未验项（如实，不补造）

- **未跑** `_f2_compare.py` / `_f2v_run.py` 本体（纪律禁止改/重跑产物）。
- **未验** `_g9_gate.py` 可达性与 CI 是否真会调用任一门禁（现盘或修正版）；「必跑门禁」目前只是设计建议，未落地。
- **未验** 甲 / 乙 / 丁的生产者改造、修正版门禁落盘、`counting_policy` 与 `schema_version` 写入两份产物、目标策略哈希在台账的登记（`TARGET` 为片段假定值）。
- **未独立重算** 19 条绑定对象 SHA256；`(17,18)` 与 warnings `11→14` 仅实读 `_mm_project_out.txt:2-7`、未复跑。
- **未造** 「两份一起加同一新维度到 results 且 totals 同步一致、不写 `counting_policy`」的纯形态反例（需 TP-7 + 已登记目标哈希，当前盘无该字段）。
- **未验** 3 件指纹锁重基线后的 owner / SOP、`_f2v_run_out.json` 是否同步的最终裁决（`MERGED_MERGE_CONTRACT.md:735` 亦列「未验」）。
- 全仓 `rglob` 版「谁同时读两份」检索 120s 超时后被 `TaskStop` 终止，未产出结论；本件采用的是 `lead/` 范围的 `grep -rl … | comm -12`（§5(b) 已给命令与输出）。

### 6(e) 交付声明

本会话只**新增** `lead/two_products_20261109/TWO_PRODUCTS_ALIGN.md`（本件）。**未修改** `lead/r11_f2_fix_20261109/`、`lead/count_invariant_20261109/`、`lead/merged_contract_20261109/`、`lead/gate_r9r12_20261109/`、两件台账中的任何文件；**未改**任何生产者、两份机读件、既有门禁；末次 `hashlib` 复算九件 `ALL_UNCHANGED = True`；`git log -1` 仍 `2657458`；`git status --porcelain -- lead/two_products_20261109/` → `?? lead/two_products_20261109/`；**未 commit、未 push**；零真机、零采样代码。
