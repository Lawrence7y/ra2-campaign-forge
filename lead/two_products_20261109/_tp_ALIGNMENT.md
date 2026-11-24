# _TP_ALIGNMENT.md — 两份机读件口径对齐设计与差异核查

> 交付：两产物对齐设计员。只做差异核查与单点定义设计，**未改**任何生产者、机读件、台账、门禁。
> 唯一写域 `lead/two_products_20261109/`，本会话新增件前缀 `_tp_`。
> 零真机（未启动 gamemd.exe / ra2loader / YURI.exe，未 taskkill，未读活进程内存）；
> 零采样代码（未写 hook / MiniDump / SuspendThread / StackWalk / 探针注入 / 动态内存解析）。
> Python 一律 `python -I -X utf8` + 绝对路径；指纹用 `hashlib`；不 commit、不 push。

---

## 0 复核绑定行（被核对象 = 两份机读件之 A）

被核对象 SHA256 = 148ea8d689eaaf582af05ea1bf4650605e104d6d74f8c7765e75a6eec662c7b1，字节数 = 44958

（对象：`lead/r11_f2_fix_20261109/_f2_compare_out.json`；本会话 `hashlib` 实算，见 §6 命令 C1）

被核对象 SHA256 = a62ee13e3afe88a421d31859c8f11c11e95b78b9b6b5d362807b6ba990c50905，字节数 = 25200

（对象：`lead/r11_f2_fix_20261109/_f2v_run_out.json`；同上）

生产者绑定行（本会话实算，C1）：
- 被核对象 SHA256 = 12e55acf42441aca846986a2447abffef77d774ee694cedf56a012c1c8907106，字节数 = 4821（`_f2_compare.py`）
- 被核对象 SHA256 = 75108dcaee4985f8623b59de18f8650ec6b78b73fbbd93ca3197f3057efdbd9a，字节数 = 3469（`_f2v_run.py`）

编排方【编排方实跑指纹】9 件全等（C1 逐件比对，无一漂移），故以下所有「现状」结论都在编排方锁定的同一份盘上成立。

---

## 1 第一步：两份产物现状核实

### 1(a) totals 键集差异

C2 实跑输出：

```
A keys ['results', 'totals']
B keys ['declared_mismatch_files', 'results', 'totals']
A totals {"bindings": 19, "orig_match": 0, "orig_path": 1, "orig_problems": 24, "plus_match": 9, "plus_path": 9, "plus_problems": 23}
B totals {"bindings": 19, "orig_collected": 1, "orig_match": 0, "orig_problems": 24, "orig_warnings": 18, "plus_collected": 9, "plus_match": 9, "plus_problems": 23}
onlyA ['orig_path', 'plus_path']
onlyB ['orig_collected', 'orig_warnings', 'plus_collected', 'plus_warnings']
common ['bindings', 'orig_match', 'orig_problems', 'plus_match', 'plus_problems']
```

- **B 的键多**：A 7 键、B 9 键。A 顶层 2 键、B 顶层 3 键（多 `declared_mismatch_files`）。
- B 多 4 个 totals 键，其中 2 个是新维度（`orig_warnings`/`plus_warnings`），另 2 个是 A 已有维度的**改名**（`orig_collected`↔`orig_path`、`plus_collected`↔`plus_path`），详见 §2(c)。
- 因此「实质维度数」= 9（A 少报 warnings 2 项）；键名差 = 4 项但只有 2 项是真实新增维度。

依据：`_f2_compare.py:35-36`（7 键初始化）、`_f2v_run.py:25-27`（9 键初始化）、C2。

### 1(b) 共同键值是否一致 —— **全一致，0 差**

C2 实跑 `value_diff {}`；5 个共同键逐一：

| 共同键 | A | B | 差 |
|---|---|---|---|
| bindings | 19 | 19 | 0 |
| orig_match | 0 | 0 | 0 |
| plus_match | 9 | 9 | 0 |
| orig_problems | 24 | 24 | 0 |
| plus_problems | 23 | 23 | 0 |

无不一致，故「逐键说明差在哪、为什么」不适用。别名对也相等：`A.orig_path=1 == B.orig_collected=1`、`A.plus_path=9 == B.plus_collected=9`（C2）。

**更深的核验**：C5 从两份各自 `results[]` 独立重算 9 个 canonical 维度，两份的 canonical 向量**逐项全等**：

```
canonical_from_A = {"bindings": 19, "orig_collected": 1, "orig_match": 0, "orig_problems": 24, "orig_warnings": 18, "plus_collected": 9, "plus_match": 9, "plus_problems": 23, "plus_warnings": 11}
canonical_from_B = {"bindings": 19, "orig_collected": 1, "orig_match": 0, "orig_problems": 24, "orig_warnings": 18, "plus_collected": 9, "plus_match": 9, "plus_problems": 23, "plus_warnings": 11}
canonical_equal  = True ; violations = 0 ; RESULT = OK
```

即：连 A 没有写入 totals 的 warnings 两维，也能从 A 的 `results[].orig.warnings/plus.warnings` 重算得 18/11，与 B 完全相同。C5 同时验证 `A.totals == recomputed(A.results)` 且 `B.totals == recomputed(B.results)` 均为 True（TP-6）。

### 1(c) results[] 条数与结构

| 项 | A | B | 结论 |
|---|---|---|---|
| 条数 | 30 | 30 | 一致（C2） |
| 顶层键 | `['results','totals']` | `['declared_mismatch_files','results','totals']` | 不同 |
| result 键集 | `file, orig, orig_overall, other_predicates_fail, plus, plus_overall`（6） | `idx, rel, orig_verdict_r11, plus_verdict_r11, file_verdict_regression, n_bindings, declared_seq_same, orig_paths, plus_paths, orig_match, plus_match, plus_tiers, orig_problems, plus_problems, orig_warnings, plus_warnings, new_problems_vs_orig`（17） | **结构完全不同**：A 嵌套字典 + 完整 binding 对象；B 扁平 + 平行数组 |
| 文件集 | 30 件，绝对路径 `file` | 30 件，相对路径 `rel` | 归一后**全等**、顺序全等 |

C3/C4 实跑：`onlyA []` / `onlyB []` / `equal True`（`normcase+normpath`、`realpath` 两种归一均如此），`order same True`，30 件全部在盘。

**★ 编排方给的 `files_only_A` 6 件是路径表示差异，不是文件集差异**：`_g9_regression_out.json:results_30` 每行同时带 `file`（绝对）与 `rel`（相对），A 取 `file`（`_f2_compare.py:38`）、B 取 `rel`（`_f2v_run.py:30-31`）。C3 逐件对照 + C6 显示这 6 件（`GOAL3T_CRITERIA_STATUS_20261021.md`、`GOAL3T_e4_VERIFY_20261026.md`、`PENDING_DECISIONS.md`、`A_REDUCED_FORM.md`、`A_RESIDUAL_REFERENCES.md`、`TASK.md`）在 B 的 `rel` 里逐一存在；C6 用后缀归一得到 `A without match = 0 / B rel without A match = 0`。若不归一，裸字符串集合是 `onlyA 30 / onlyB 30`（C7），所以编排方报的 6 件必然来自某种部分归一。如实记为**口径差异的表示层**，非漏件。

### 1(d) ★ 是「不同口径」还是「算错了」？

**本会话实测：两份数值现在没有任何不一致**，所以第 4 步的二分问题在**当前盘上不成立**。准确定性如下：

- 两份 `totals` 的**键集/键名/维度覆盖不同** → 这是**不同口径（schema 分歧）**，不是算错。A 只写 7 维、B 写 9 维；`plus_path` 与 `plus_collected` 是对同一表达式的两个名字（§2(c)）。
- 但**计数语义本身是同一套**：C5 的 9 维 canonical 向量逐项相等、C9 的逐绑定行 `path/match/tier` 值 0 处不一致。也就是说，「不同口径」只发生在**投影/命名/布局**，不发生在**数什么**。
- 两者共享同一个**已知口径缺陷**（任务书背景明示，本会话 `rg` 确认两份生产者都无 `merged|by_kind|schema_version|counting_policy` 命中，C12）：`plus_match` 把 merged 计入、`path` 不计入（`_f2_compare.py:67/69`、`_f2v_run.py:62/64`）。这是**两份一起缺同一个维度**，不是「一份对一份错」。

**处理方式**（强调二者不同）：
- 若是「不同口径」→ 不能靠改一个数字修，要做**单点定义**（§3）：统一 canonical 键名 + `counting_policy`/`schema_version`，或让一份读另一份。
- 若是「算错了」→ 才去改那个聚合表达式的值、并重算受影响产物。
- 本盘的现实风险是第三种：**口径分歧掩盖了「只改一处」的漏改**。当前相等只是因为两份都还没加 merged；一旦只改 A，数值就会变成不一致，而那时它是「漏改导致的算错」而非「口径不同」。§4 详述。

---

## 2 第二步：逐行追聚合代码

### 2(a) 差异表（`_f2_compare.py:65-71` vs `_f2v_run.py:60-68`）

| # | 维度 | A：`_f2_compare.py` | B：`_f2v_run.py` | 差异性质 |
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
| 12 | 写盘 | `:100` `{"totals": tot, "results": results}`，`indent=2` | `:70-72` `{"totals": tot, "declared_mismatch_files":…, "results": out}`，`indent=1` | 布局/序列化不同 |
| 13 | 前置断言 | `:24` 校验 g7 指纹；`:44-46` 绑行数/declared 序列；`:48-50` 原 T1 path 不丢 | **无任何 assert**；`:39-41` 只把 `seq_ok` 记进结果 | A 三段硬断言、B 只记录 |
| 14 | 读文本 | `:39` `read_bytes().decode("utf-8")` | `:32` `read_text(encoding="utf-8")` | CRLF 行为不同（§2(d) 注） |

### 2(b) 差异性质

**没有实质口径分歧**（没有「一个算 path、一个算 collected」这种语义对立）。差异分三类：

1. **纯增量**：B 多的 `orig_warnings/plus_warnings`（`:67-68`）与 `declared_mismatch_files`（`:28,40-41,71`）。A 的 `results[]` 里其实有 warnings 数据（`_f2_compare.py:57,60`），只是没聚合进 totals；C5 证明从 A 的 results 重算得 18/11。
2. **纯改名**：`orig_path`↔`orig_collected`、`plus_path`↔`plus_collected`，表达式完全一样。
3. **布局/序列化**：嵌套 binding 对象 vs 平行数组、`indent=2` vs `indent=1`、顶层键数。

真正需要警惕的是第 2 类：**同名不同维、同维不同名**混在一起，使「键集比较」看起来像 4 个差异，实际只有 2 个真差异；任何按键名写的交叉校验都会误报。

### 2(c) ★ `plus_collected` 与 `plus_path` 是不是同一个东西 —— **是，依据如下**

1. **代码级**：`_f2_compare.py:67` = `tot["plus_path"] += sum(1 for b in n_bind if b.get("path"))`；`_f2v_run.py:62` = `tot["plus_collected"] += sum(1 for b in pb if b.get("path"))`。除累加器变量名外逐字同式，输入都是 `r11_scan_plus(...)` 返回的绑定列表（`:42` / `:35`）。
2. **数据级**：C2 实跑 `alias plus_path vs plus_collected 9 9 True`；C5 从两份各自 results 重算 `plus_collected` 均为 9。
3. **结构级**：B 的 `results[].plus_paths`（`:49`）与 A 的 `results[].plus.bindings[].path`（`:59`）逐条相等（C9 `per-binding value mismatches: []`）；`orig` 侧同理（1 = 1）。
4. **语义级**：`_f2_r11plus.py:196` 建 `rec = {"declared","path","match","citation"}`，`:268` 命中时 `rec.update({"match": True, "path": verified["candidate"], ...})`。`path` 是「解析到的单一对象路径」，`:306` 追加进 bindings。两个生产者都在数「`path` 真值的绑定行条数」，即「采到单一路径的条数」。B 叫它 `collected`，A 叫它 `path`，**同一计数**。

同名对里唯一名实不符的是「`plus_match`」：它数 `match is True`（`:69`/`:64`），而 merged 行 `path=None, match=True`（`_mm_project_out.txt:12`），所以 match 不是「有路径且已回验」而是「判定为真」——这正是两份共享的维度缺失（§1(d)）。

### 2(d) results[] 里绑定行结构是否一致 —— **不一致（布局），但语义投影一致**

| | A | B |
|---|---|---|
| 载体 | `results[i].orig.bindings[]` / `results[i].plus.bindings[]`，嵌套 dict | `results[i].orig_paths[]` / `plus_paths[]` / `orig_match[]` / `plus_match[]` / `plus_tiers[]`，5 条平行数组 |
| 键集 | orig 3 键 `{declared, match, path}`；plus 11 键 `{alt, bytes, citation, declared, match, path, recomputed, suffix_stripped, tier, tried, verified_path}`（C8 实读全量并集；出现次数不一：`alt`1/`bytes`8/`verified_path`8 等） | 无 binding 对象；只有 `path`/`match`/`tier` 三条投影 + `n_bindings`/`declared_seq_same` |
| declared 文本 | 逐行完整保留 | **不保留**；只留 `declared_seq_same` 布尔 |
| problems/warnings | 嵌套 list | 顶层 list |
| 逐条值 | — | C9：30 件 × 5 数组与 A 逐条相等，`declared_seq_same` 全 True，`n_bindings` 全等于 A 的绑行数 |

结论：**绑定行的「信息结构」不同（A 是超集、B 是投影），但重叠字段的语义与取值完全一致**。B 丢掉了 `declared`/`recomputed`/`verified_path`/`citation`/`tried` 等字段，因此 B 无法独立做「SHA 逐字比对」这类语义核验，只能做计数核验。

补充（C13）：A 用 `read_bytes().decode`、B 用 `read_text`，30 件中 `B2B_PREAUDIT.md` 有 195 个 CRLF，两种读法文本长度 14467 vs 14272；但该件 `n_bindings=0`、problems/warnings 逐项相同（C14），故当前盘上**未造成数值差**。这是潜在漂移点，不是现盘错误。

---

## 3 第三步：单点定义方案（核心产出）

### 3(a) 现状 → 理想

现状：`_f2_compare.py:35-36,65-71,100` 与 `_f2v_run.py:25-27,60-68,70-72` **各自硬编码一份维度清单 + 各自写一遍 7~9 条 `sum(...)`**，没有任何共享定义、没有 `schema_version`、没有 `counting_policy`（C15 实读两份 JSON 顶层无此类键）。两份的相等只是「同一段逻辑被抄了两遍且都没改」的巧合基线；`COUNT_INVARIANTS.md:669` 已把「第二份产物漂移无监控」列为长期代价。

理想：**维度清单与聚合表达式只存在一处**，两个生产者只负责「产出 results[]」与「调用共享聚合器」，并让自己写出的 `totals` 携带可机检的策略标识。

### 3(b) 方案（含推荐）

#### 甲：抽出共享聚合函数，两个生产者都调它

新增（新写域内的交付骨架，不改既有件）一个 `_counting_policy` 模块，导出：
- `DIMENSIONS`：canonical 键 → 从统一 binding view 取值的函数；
- `aggregate(binding_rows) -> dict`；
- `POLICY_ID` / `SCHEMA_VERSION`（把策略本身做成可被 hash 的字符串）。

两个生产者各自把 `results[]` 规整成统一的 `binding_rows`（或由适配层把嵌套/平行数组转成同一 view），调 `aggregate()` 得到 canonical totals，再按各自历史别名投影写盘。新增维度只改 `DIMENSIONS` 一处。

- 优点：保留两份产物各自用途与全部消费者；新增维度天然同步；`POLICY_ID` 可直接做 §3(d) 断言。
- 缺点：两个生产者文件仍要改（各一行 import + 一处调用），指纹锁必 DRIFT；两份 `results[]` 布局仍不同，需要适配层且适配层本身可能写错。
- 适用：想保留双产物、且愿意一次性重基线。

#### 乙：只保留一份产物，另一份改为读取它

把 `_f2_compare_out.json` 定为唯一权威（它有完整 binding 对象、被 4 个消费者 + 3 件指纹锁引用）；`_f2v_run.py` 不再自算 9 键，改为读 A、把嵌套结构投影成 B 的历史 schema（含 `declared_mismatch_files`、平行数组、warnings 两维）后写 B，或干脆让 B 的读者改读 A。

- 优点：**结构上不可能只改一处**——B 没有独立聚合路径；最彻底。
- 缺点：B 现有 `results[]` 的 `idx/rel/parallel arrays` 形状是审计脚本 `_mkv_consumers.py:120`、`_mm_probe.py:124` 依赖的，投影层要兼容；若删除 B，这两个读者 + 任何引用 B 指纹的报告都要改；且 B 的「独立对跑」语义（F2V-03，`_f2v_run.py:2-4`）会消失——不再是独立复算，而是同一数据的二次投影。
- 适用：认定双产物是历史冗余、不需要独立交叉验证。

#### 丙：两份各自算，加一个交叉校验（算完互比，不一致报警）

保留两份完全不动，新增一个门禁（本交付的 `_tp_crosscheck.py` 即原型）：从两份 `results[]` **独立重算** 9 个 canonical 维度，别名归一后比对，并各自检查 `totals` 与 `results[]` 自洽；任一不等即 `rc=1`。

- 优点：**零改动既有件**（本任务铁律下唯一可立即落地的方案）；C5 实跑现盘 `violations=0 RESULT=OK`；C10 三个「只改一处」反例全部报警（2/5/1 条）。
- 缺点：是**事后检测**不是事前预防；必须有人真的跑它并让 CI 卡 rc；它只能发现「结果不一致」，不能自动修、也不能阻止「两份一起漏改同一个维度」（§5(c)）。
- 适用：本任务、以及任何禁止改生产者的窗口期。

#### 丁（推荐，甲+丙组合）：共享聚合 + 策略标识 + 必跑交叉门禁

把甲的 `DIMENSIONS` 作为唯一定义，两份产物各写 `counting_policy: <hashlib.sha256(DIMENSIONS 规范化字节).hexdigest()>` 与 `schema_version`；同时保留丙的门禁，断言「两份 `counting_policy` 相等」+「canonical totals 相等」+「各自 totals 自洽」。这样：
- 新增维度只改一处（甲）；
- 漏改会在**策略哈希**层面立刻暴露，而不是等数值碰巧不等（补上丙的盲区：`merged` 若被同时漏加到两份，数值仍相等但策略哈希应与裁决后的新策略不符，需配合 owner 登记的目标策略哈希）；
- 门禁不改生产者即可上线，生产者改造可分阶段进行。

推荐理由：甲单独做「没人跑门禁就白搭」，丙单独做「两份一起漏改抓不到」，乙破坏 B 的独立复算能力。丁以最小破坏面同时拿到三者优点。**本会话只交付丁的门禁原型与实现片段，不落地任何生产者改造。**

### 3(c) 各方案对 4 个消费者与指纹锁的影响

4 个既有消费者（`_f2w_checks.py:14,17,26`、`_f2w_extract.py:13,17,20`、`_f2w_pass.py:6-7,11,21-24`、`_f2w_final.py:31-33`）：C16 实跑 `rg -n "totals" lead/r11_f2_fix_20261109/_f2w_*.py` **0 命中**，四个全只读 `cmp_["results"]`；`COUNT_INVARIANTS.md:472` 亦记此事实。

| 方案 | 对 4 消费者 | 对 3 件 `_f2d*_fpcheck` | 其他指纹/快照 |
|---|---|---|---|
| 甲 | 若 A 的 `results[]` 形状不动 → **0 影响**；若顺带改 results 形状则 4 个全要改 | A 产物字节变 → **3 件全 DRIFT**，需重基线（C18 模拟：合法改 totals 后 A sha=`0dfa0309…`/43797 ≠ `148ea8d6…`/44958） | 生产者 `.py` 指纹变 → `_mm_fp.py:8`、`_mkv_fp.py`、`_mk_probe.py`（C20 命中 3 件）失配；`_ow_raw_hits.json:15259` 四件 fileMeta 快照 stale（`MERGED_MERGE_CONTRACT.md:384`） |
| 乙 | 若保留 A 形状 → 0 影响；若删 B 或改 B 读者 → `_mkv_consumers.py:120`、`_mm_probe.py:124` 要改 | 若 A 不变 → **3 件仍 MATCH**（C17 实跑现盘 3 件全 MATCH）；若 A 重写则同甲 | B 产品指纹 `a62ee13e…` 变/废；`_ow_raw_hits.json:15279` stale |
| 丙 | **0 影响**（新增只读门禁，不碰两份 JSON） | **3 件仍 MATCH**（C17） | 新增门禁自身指纹，无既有锁变化；`_ci_checks.py` 仍只覆盖 A（C16 实跑其无 B 引用） |
| 丁（推荐） | 门禁阶段 0 影响；共享聚合落地阶段同甲 | 门禁阶段 MATCH；聚合落地阶段同甲需重基线 | 同甲 + 需在台账登记目标 `counting_policy` 哈希 |

**关键不对称（C19）**：3 件 `_f2d*_fpcheck.py` 的 `EXPECT`/`FULL`/`ITEMS` 里**都没有** `_f2v_run_out.json`、也没有两个生产者 `.py`（`_f2d_fpcheck.py:7-17`、`_f2dw_fpcheck.py:14-33`、`_f2dv_fpcheck.py:18-55`，C19 实跑 `locks_B_product=False / locks_A_producer=False / locks_B_producer=False`）。所以「只漏改 B」这件事**3 件指纹锁一件都抓不到**；「只改 A 的 totals」反而会被 3 件锁报 DRIFT——而那恰好是**合法**改动。这正是 `COUNT_INVARIANTS.md:668` 说的「合法改动与篡改不可分」。

### 3(d) ★ 「口径一致性」可机检断言

**核心主张**：不能只比 `totals` 键集（会误判改名），也不能只比共同键的值（只改一处时共同键可能仍相等）。必须同时断言 4 层：

```
TP-1  文件集/顺序：normcase(normpath(A.results[i].file))
                    == normcase(normpath(REPO / B.results[i].rel))    ∀i，且集合相等
TP-2  条数：len(A.results) == len(B.results)
TP-3  逐件绑行数：len(A.results[i].orig.bindings) == B.results[i].n_bindings
TP-4  逐绑定行投影：A.orig.bindings[].path / A.plus.bindings[].{path,match,tier}
                    == B.{orig_paths,plus_paths,orig_match,plus_match,plus_tiers}[]   逐条
TP-5  canonical 向量相等：canon_from_A(A.results) == canon_from_B(B.results)
       9 维 = {bindings, orig_collected, plus_collected, orig_match, plus_match,
               orig_problems, plus_problems, orig_warnings, plus_warnings}
       别名表：A.orig_path↔orig_collected, A.plus_path↔plus_collected
       （A 未写 totals 的 warnings 两维也从其 results 重算纳入）
TP-6  自洽：A.totals[k_A] == canon_from_A(A.results)[k] ∧ B.totals[k_B] == canon_from_B(B.results)[k]
TP-7（推荐补）策略标识：A.counting_policy == B.counting_policy == 目标策略哈希
                        ∧ A.schema_version == B.schema_version
```

**「同一套口径」的直接判据**（从两份产物本身、不需要读生产者源码）：
> `TP-1..TP-6` 全通过 ∧ 两份 `counting_policy` 字符串相等。
> 若两份都还没有 `counting_policy`（当前盘，C15 实读顶层无此键），则退化为 `TP-1..TP-6` 全通过 —— 此时只能证明「本次两份数值同口径」，**不能证明将来新增维度仍同口径**；故 TP-7 是长期必需项。

**实跑结果**：C5 `python -I -X utf8 …/_tp_crosscheck.py` → `canonical_equal = True / violations = 0 / RESULT = OK / rc=0`。
**有效性反例**（C10，均只改一处）：
- 只改 A.totals（`plus_match=18, plus_path=17`）→ 2 条 TP-6 报警；
- 只改 A.results（插入 `path=None/match=True/tier=SAMEDOC_LINK_EQ` 的 merged 行）→ 5 条报警（TP-4×3、TP-5、TP-6）；
- 只改 B.totals（`plus_collected=17`）→ 1 条 TP-6 报警。

### 3(e) 可粘贴实现片段

**(i) 单点定义（甲/丁的共享聚合器骨架 —— 只作设计，未落地、未改任何既有件）**

```python
# _counting_policy.py —— 唯一定义处（新模块，须落在合适的写域）
import hashlib, json

# 统一 view = 逐「件」记录 files[]；每件带 bindings[] + 逐件 problems/warnings 列表。
# ★ 必须是逐件而非扁平逐绑行：30 件里有 0 绑行件（如 idx 0/22，C4/C14），
#   它们的 problems/warnings 仍要计入 totals，扁平化会丢（C24 首跑实证）。
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
    return {alias: canon[k] for k, pair in ALIASES.items()
            if (alias := pair[i]) is not None and k in canon}
```

> 片段自测（本会话 C24 实跑，见 §6）：把现盘 `A.results` 规整成 30 条逐件 view 后，
> `policy_id()` = `8b6015a9a51ef1cf59cf2a7a43f9ebca57a7fd6948ed1aa4de3dbe139282aeb0`（64 hex）；
> `project(aggregate(files), 0)` 得 A 的 7 键、**与现盘 `A.totals` 全等**（`A equals disk totals = True`）；
> `…, 1)` 得 B 的 9 键、**与现盘 `B.totals` 全等**（`B equals disk totals = True`）。
> 首跑曾用扁平 `rows` view，得 `orig_problems=1 / plus_problems=0` 与真值 24/23 不符（0 绑行件被丢），故改为逐件 view —— 这条自测失败已如实记录并修正。`k in canon` 保护另可避免维度裁剪时的 `KeyError`。**本会话未把该模块落地到任何既有生产者。**

两个生产者改动（各一处，示意）：
```python
# _f2_compare.py / _f2v_run.py 各自：把 for 循环里的 7~9 条 tot[...] += 全部删掉，改为
from _counting_policy import aggregate, project, policy_id
tot = project(aggregate(files), SIDE)         # SIDE=0 或 1
doc["counting_policy"] = policy_id()
doc["schema_version"] = 2
```
> 注：`rows` 是两生产者把各自 `results[]` 规整成的统一 view；这段是**设计片段**，本会话未执行、未写入任何生产者。

**(ii) 交叉校验门禁（丙/丁，已实跑）**：完整可粘贴代码即本写域 `lead/two_products_20261109/_tp_crosscheck.py`（C5/C10 实跑），核心断言：

```python
CANON = {...}                       # 见文件 :20-31
def canon_from_A(doc): ...          # 只看 A.results，不看 A.totals  :34-52
def canon_from_B(doc): ...          # 只看 B.results，不看 B.totals  :55-73
def check(A, B):                    # TP-1..TP-6                    :86-...
    ...
    if os.path.normcase(os.path.normpath(...)) != ...: v.append("TP-1 ...")
    if canon_from_A(A) != canon_from_B(B):               v.append("TP-5 ...")
    for k, alias in ALIASES.items():
        if doc["totals"].get(alias) != calc[k]:           v.append("TP-6 ...")
    return v
```

运行命令与输出（C5）：
```
python -I -X utf8 D:/Project/ra2-campaign-forge/lead/two_products_20261109/_tp_crosscheck.py
→ canonical_equal  = True ; violations = 0 ; RESULT = OK ; rc=0
```

**(iii) TP-7 策略标识断言（在门禁里加 6 行）**
```python
def policy_check(A, B, expected=None):
    pa, pb = A.get("counting_policy"), B.get("counting_policy")
    if pa is None or pb is None:
        return ["TP-7 缺 counting_policy（当前盘预期；新增维度后必须补）"]
    if pa != pb:
        return ["TP-7 counting_policy 不一致 A=%s B=%s" % (pa, pb)]
    if expected is not None and pa != expected:
        return ["TP-7 counting_policy 未跟上裁决后的目标策略 %s" % expected]
    return []
```
当前盘 C15 实读两份顶层均无 `counting_policy`/`schema_version`，故此函数在当前盘会返回「缺」——如实标注，不伪造通过。

---

## 4 第四步：「只改一处」风险评估

### 4(a) 传导链（只给 `_f2_compare.py` 加 merged 维度，漏 `_f2v_run.py`）

依据既有实跑投影 `lead/merged_contract_20261109/_mm_project_out.txt:2-7,12,22-24`（本会话 C11 实读）与本会话 C10 反例：

1. **改 A 的聚合/谓词**：`_f2_r11plus.py` 若接入 merged，`_mm_project_out.txt:12` 显示 merged 行形状 `tier=SAMEDOC_LINK_EQ, match=True, path=None, members_n=2`。
2. **A 的 totals 变**：`_mm_project_out.txt:2-4` BEFORE `{plus_path:9, plus_match:9}` → AFTER `{plus_path:17, plus_match:18}`（8 条 unique + 1 条 merged）；`_mm_project_out.txt:22` 记 `_f2_compare.py:67/69` 对该 merged 单条计 `(0,1)`。A 产物字节与指纹变（C18 模拟 sha `0dfa0309…`/43797）。
3. **B 不动**（漏改）：`_f2v_run.py:62,64` 仍按旧口径，其 9 键 totals 保持 `{plus_collected:9, plus_match:9, …}`（`_mk_CONTRACT_DESIGN.md:586` 明确记「不受影响但口径不一致」）。
4. **两份出现数值不一致**：别名归一后 `plus_collected` A=17 / B=9、`plus_match` A=18 / B=9；`_mm_project_out.txt:24` C7 记「`_f2v_run.py:49-52` `plus_paths=[None] plus_match=[True]` 且 9 键 totals 同步漂移」——注意那是**同时改两份**的情形；只改 A 时 B 的 `plus_paths` 连 `None` 都不会出现，两份 `results[]` 直接分叉。
5. **消费者侧静默**：4 个 `_f2w_*` 只读 A 的 `results[]` 且 0 处读 `totals`（C16），`_mm_project_out.txt:19-27` C1–C10 逐项记它们的反应：`_f2w_checks.py:29` `sha_ok=False`、`_f2w_extract.py:26-33` `verified='' bytes='-'`、`_f2w_pass.py:17` merged 混入单一回验统计、`_f2v_verify9.py:24` 甚至 `TypeError`。**没有一个是「B 与 A 不一致」的报警。**
6. **`_ci_checks.py` 只覆盖 A**（C16 实跑其无 B 引用；`COUNT_INVARIANTS.md:659` 明说「判不了跨文件一致」），故它对 B 的漂移 0 输出。
7. **结论**：漏改可以一路走到「A 已升级、B 仍旧、无人报警」，直到有人手工对账或接入本交付的 `_tp_crosscheck.py`。C10 反例 2 证明该门禁能抓（5 条报警）。

### 4(b) 有没有消费者同时读两份、撞出矛盾？

**没有。** C21 全仓 `.py` 搜索 `_f2v_run_out.json` 的运行期读者只有 3 件：生产者自己（`_f2v_run.py:70` 写）、`_mm_probe.py:124`、`_mkv_consumers.py:120`。C22 找出同时提到两件文件名的也只有这两件审计脚本（`_mm_probe.py`、`_mkv_consumers.py`）。

- `_mkv_consumers.py:118-125` 的 G 段只是分别 `print` 两件的 `top_keys/totals/results_n`，`:127-142` 的 H 段只对 **A** 做重算与 `EQUALS` 比较；**没有任何 A-vs-B 断言**（C23 逐行核对）。
- `_mm_probe.py:89-113` 的 §CMP 只对 A 重算并判 `EQUALS`，`:123-126` 的 §RUN 只 `print` B 的 `top_keys` 与 `totals`；同样**零交叉断言**（C23）。
- 这两个脚本都是一次性审计输出（`_mkv_consumers_out.txt:149-165`、`_mm_probe_out.txt:21-24` 记录结构快照），不是常驻门禁，也不 `assert`。

因此「撞出矛盾」目前不会发生——不是因为一致，而是因为**根本没人把两份放在一起比**。这正是 `COUNT_INVARIANTS.md:669`「两份口径不同键却无人对账」的实证。

### 4(c) 3 件 `_f2d*_fpcheck` 会不会抓到漏改？—— **不会**

C17 实跑现盘 3 件全部 MATCH（`_f2d_fpcheck.py` 9/9 MATCH；`_f2dw_fpcheck.py` `bad=0`；`_f2dv_fpcheck.py` `MATCH=20 MISMATCH=0`）。C19 逐件检查三件的锁定清单：

| 锁 | 锁 A 产物 | 锁 B 产物 | 锁两生产者 .py |
|---|---|---|---|
| `_f2d_fpcheck.py:7-17` | ✅ `148ea8d6…/44958` | ❌ | ❌ |
| `_f2dw_fpcheck.py:14-33` | ✅ 同上 | ❌ | ❌ |
| `_f2dv_fpcheck.py:18-55` | ✅ 同上 | ❌ | ❌ |

结论：
- **只漏改 B**：B 完全不在三件的指纹清单里 → 三件全 `MATCH`，**0 报警**。
- **只改 A**：三件都会报 `DRIFT/MISMATCH`（C18 模拟：合法 totals 改写后 A sha 与基线不等）。但它们报的是「A 变了」，**不区分合法口径升级与篡改**，也不会告诉你「B 该同步却没同步」。
- 二者合起来是 `COUNT_INVARIANTS.md:668` 的准确复现：指纹锁与口径改动互相掣肘——该抓的漏改抓不到，不该拦的合法改动会拦。

### 4(d) 「防漏改」机制建议（按成本递增）

1. **立刻、零改动**：把 `_tp_crosscheck.py` 接成必跑门禁（`rc!=0` 即卡）。C5 现盘 OK、C10 三类单边改动全报警。至少把「数值分叉」堵住。
2. **补策略标识**：两份都写 `counting_policy` + `schema_version`（§3(e)(i)），门禁加 TP-7 并比对**所有者登记的目标策略哈希**。这样「两份一起漏加 merged」也能被抓——这是纯数值交叉校验的盲区（§5(c)）。
3. **收口到一处定义**：按甲/丁把 `DIMENSIONS` 做成唯一来源，删掉两份生产者里的 7~9 条 `totals[...] +=`；新增维度只改 `DIMENSIONS` + 目标策略哈希，两个生产者零改动。
4. **指纹锁分层重基线**：把「内容指纹」（随合法口径升级而变）与「策略指纹」（`counting_policy` 哈希，须与裁决一致）分开；3 件 `_f2d*_fpcheck` 改为校验策略指纹 + 校验 B 产物也在清单内，避免 §4(c) 的两个盲点。重基线须登记 owner/触发 SOP（`MERGED_MERGE_CONTRACT.md:639` 亦要求先补）。
5. **清单化触发**：见 §5(d)。

---

## 5 第五步：边界与建议

### 5(a) 两份产物并存的合理性 —— **部分不同用途 + 明显历史冗余，判断：冗余为主**

支持「不同用途」的证据：
- `_f2_compare.py:2-6` 自述「第三步：同一份 30 件清单，原版 vs 增强版实跑对比」，带 3 段断言（g7 指纹、declared 序列、T1 path 保留），`results[]` 保留**完整 binding 对象**，供 `_f2w_extract.py:29-33` 做逐条交付表、`_f2w_checks.py:29` 做 SHA 逐字比对。
- `_f2v_run.py:2-4` 自述「F2V-03：独立对跑……覆盖率、match、problems/warnings 增量、绑定行 declared 序列一致性，全部自算」，额外产出 `declared_mismatch_files`、warnings 两维、平行数组，是**独立复核视角**。
- 布局差异（嵌套 vs 平行）使二者确非字节级重复。

支持「历史冗余」的证据（更强）：
- 同一输入 `_g9_regression_out.json:results_30`、同一对函数 `g7.r11_scan` / `f2p.r11_scan_plus`（`:41-42` / `:34-35`）、同一 30 件、同一 19 绑定行。
- C5/C9 证明 9 个 canonical 计数维与逐绑定行投影**完全相同**；B 的额外 2 个 totals 键能从 A 的 `results[]` 完整重算。
- C21/C22：B 在**生产链上没有下游消费者**，只有 2 件一次性审计脚本读它；A 有 4 个交付消费者 + 3 件指纹锁 + `count_invariant` 全套不变量。
- `COUNT_INVARIANTS.md:659,669`、`MERGED_MERGE_CONTRACT.md:163-165` 都把 B 记为「第二件带 totals 的机读件」「须单独裁决是否同步」，即项目内部已把它当作待裁决的重复面而非独立权威。

**结论**：B 的价值是「独立复跑的交叉验证」这一**过程**价值，不是「不可替代的数据」这一**产物**价值。其产物形态可保留，但**计数定义不应有第二份**。

### 5(b) 若合并成一份，损失什么

1. **独立复算能力**（最主要）：`_f2v_run.py` 现在自己 `load()` 两个模块、自己跑 30 件、自己算 9 维。若改成读 A（方案乙），两份就不再是两条独立路径，任何 A 的聚合错误会同时污染「A」和「B」，交叉校验退化为自我比对。
2. **B 独有字段**：`declared_mismatch_files`、`results[].new_problems_vs_orig`（集合差）、`file_verdict_regression`、warnings 两维的显式 totals。A 需增字段才能覆盖，否则 `_mkv_consumers.py:120`、`_mm_probe.py:124` 的结构快照失效。
3. **B 的「无断言」记录语义**：A 用 `assert` 硬失败（`:44-50`），B 把 `declared_seq_same` 记成布尔（`:39-41`）继续跑完 30 件并统计 `declared_mismatch_files`。合并后若要保留「跑完全场再汇总」的行为需额外设计。
4. **指纹/快照登记面**：B 的 `a62ee13e…/25200` 出现在 `_ow_raw_hits.json:15279`、`_mm_fp_out.txt`/`_mm_probe_out.txt`（C20 实读），删除或改写会使这些登记 stale。
5. **不损失的东西**：4 个既有交付消费者（它们只读 A）。

### 5(c) 这条对齐工作判不了什么（如实列）

1. **判不了语义正确**：`match=True` 是否真对应正确被核对象；`COUNT_INVARIANTS.md:652` 记 `_f2w_checks.py:29` 实跑 `sha 逐字一致条数 = 8`（9 条 match 里 1 条走 `alt` 无 `recomputed`）。本会话**未重算** 19 条绑定所指向对象的 SHA256。
2. **判不了该不该有 merged / 该用哪套裁决口径**：甲/乙/丙、`plus_match` 是否含 merged、键名与 `schema_version` 起点，按 `MERGED_MERGE_CONTRACT.md:28,572,639` 均属**所有者裁决**；本件不作拍板。
3. **判不了「两份一起漏改」**：若新增维度在两处同时被漏加且都不写 `counting_policy`，TP-1..TP-6 全通过（C5 型基线）。只有 TP-7 + 目标策略哈希能判，而当前盘两份都无该字段（C15）。
4. **判不了 verdict 业务正确性 / tier 值语义 / 30 件清单代表性**（`COUNT_INVARIANTS.md:653-657` 同）。
5. **判不了 B 的读法差异是否永远无害**：A `read_bytes().decode` vs B `read_text` 在 `B2B_PREAUDIT.md` 上文本不同（C13，195 处 CRLF），当前因该件 0 绑定行而未显现（C14）；换语料是否仍一致**未验**。
6. **判不了各方案落地后的 totals**：本会话**未跑** `_f2_compare.py` / `_f2v_run.py` 本体（纪律禁止改/重跑产物），也未执行甲/乙/丁的生产者改造；`_mm_project_out.txt:3` 的 `(17,18)` 是既有实跑投影值，本会话只实读、未复跑。
7. **未验**：`_g9_gate.py` 是否可达、CI 是否真会调用 `_tp_crosscheck.py`、3 件指纹锁重基线后的 SOP、`_f2v_run_out.json` 是否同步的最终裁决（`MERGED_MERGE_CONTRACT.md:735` 亦列「未验」）。

### 5(d) 以后新增计数维度时的清单

1. **先定单点**：只在 `DIMENSIONS`（或等价的唯一定义处）增键 + 取值函数；**禁止**在两个生产者里各写一条 `totals[...] +=`。
2. **更新别名表**：写明新维度在 A/B 的历史键名（或标记 `None` = 该产物不写）；同步更新 `_tp_crosscheck.py:CANON` 与 `canon_from_A/B`。
3. **算新 `policy_id()`**：用 `hashlib` 对规范化维度清单取 SHA256；把目标值登记到台账/判定书（owner + 生效 SOP），并把两份产物的 `counting_policy`/`schema_version` 一起升。
4. **两份同步落地或显式裁决不同步**：若裁决「B 不同步」，必须登记理由与 B 的预期值，否则门禁会误报；`MERGED_MERGE_CONTRACT.md:639` 把此项列为 step 0 裁决内容。
5. **跑门禁**：`python -I -X utf8 …/_tp_crosscheck.py`，要求 `violations=0` 且 TP-7 策略哈希等于登记的目标值；再跑 `COUNT_INVARIANTS.md` 的 INV-1..5 与反例集（条件化 `--expect-merged`）。
6. **补反例**：至少造 3 个「只改 A / 只改 B / 两份一起漏改」的构造输入，实跑确认门禁能报（本会话 C10 已给前两类、第三类需 TP-7）。
7. **重基线登记面**：3 件 `_f2d*_fpcheck`（A 产物 + 建议纳入 B）、`_mm_fp.py:8` 等生产者指纹锁、`_ow_raw_hits.json` 四件 fileMeta、报告中的指纹文字；**逐处记录新 sha/bytes**，不静默改。
8. **回放双向兼容**：旧 JSON 读新代码 / 新 JSON 读旧代码各跑一遍（`_mk_CONTRACT_DESIGN.md:696` 亦要求），确认 4 个 `_f2w_*` 消费者 `rc=0` 且输出字段不缺。
9. **最后**：`hashlib` 复算全部只读对象指纹，确认两件台账与只读域 `UNCHANGED`；不 commit、不 push（除非所有者另行指示）。

---

## 6 本会话实跑命令与输出（逐条可复核）

| 编号 | 命令（均在 `D:/Project/ra2-campaign-forge` 下） | 关键输出 |
|---|---|---|
| C1 | `python -I -X utf8 -c "…hashlib…9 件…"` | 9 件 sha/bytes 与【编排方实跑指纹】全等；A `148ea8d6…`/44958、B `a62ee13e…`/25200、A 生产者 `12e55acf…`/4821、B 生产者 `75108dca…`/3469 |
| C2 | `python -I -X utf8 -c "…json 结构比较…"` | `A keys ['results','totals']`；`B keys [...,'totals']`；`onlyA ['orig_path','plus_path']`；`onlyB ['orig_collected','orig_warnings','plus_collected','plus_warnings']`；`value_diff {}`；`alias … 1 1 True` / `9 9 True`；`n_results 30 30`；`files onlyA [] / onlyB [] / common n 30 / order same True` |
| C3 | `python -I -X utf8 -c "…normcase+realpath 集合…"` | `onlyA [] onlyB [] equal True`（两种归一）；`A missing [] B missing []`；G9OUT `results_30` 每行同时有 `file`/`rel` |
| C4 | `python -I -X utf8 -c "…逐件打印 30 件 file/rel…"` | 30/30 一一对应，绝对 vs 相对 |
| C5 | `python -I -X utf8 D:/…/_tp_crosscheck.py` → `_tp_crosscheck_out.txt` | `canonical_equal = True`；`violations = 0`；`RESULT = OK`；`rc=0`；两份 canonical 9 维逐项相等 |
| C6 | `python -I -X utf8 -c "…6 件 flagged…"` | 6 件在 B 的 `rel` 中逐一存在；`A without match 0 / B rel without A match 0` |
| C7 | `python -I -X utf8 -c "…裸字符串集合…"` | `raw string set: onlyA 30 onlyB 30` |
| C8 | `python -I -X utf8 -c "…binding 键集…"` | A orig 3 键 / plus 11 键；B 平行数组长度全等于 `n_bindings`：`OK` |
| C9 | `python -I -X utf8 -c "…逐绑定行交叉比对 + A 重算 warnings…"` | `per-binding value mismatches: []`；`B declared_seq_same all true: True`；`orig_warnings 18 plus_warnings 11`（与 B totals 相等） |
| C10 | `python -I -X utf8 -c "…3 个单边反例…"` → `_tp_counterexamples_out.txt` | 反例1 `violations=2`；反例2 `violations=5`（含 `TP-5 canonical plus_match A=10 B=9`）；反例3 `violations=1` |
| C11 | `python -I -X utf8 -c "…读 _mm_project_out.txt:1-40…"` | BEFORE `(9,9)` / AFTER `(17,18)`；merged rec `path=None match=True tier=SAMEDOC_LINK_EQ`；C7 记 B 同步漂移 |
| C12 | `rg -n "merged\|by_kind\|schema_version\|counting_policy" _f2_compare.py _f2v_run.py` | `(no hits in either producer)` |
| C13 | `python -I -X utf8 -c "…read_bytes.decode vs read_text…"` | `files where … != …: 1` → `('B2B_PREAUDIT.md', 195, 14467, 14272)` |
| C14 | `python -I -X utf8 -c "…该件 A/B 逐项…"` | idx 22 A/B 均 `n_bindings 0, orig_problems 1, plus_problems 1, warnings 0/0` |
| C15 | `python -I -X utf8 -c "…顶层 policy/schema 键 + _ow_raw_hits fileMeta…"` | `A top keys ['results','totals']`、`B top keys ['declared_mismatch_files','results','totals']`；`any policy/… marker: [] []`；fileMeta 四件快照与 C1 全等 |
| C16 | `rg -n "totals" lead/r11_f2_fix_20261109/_f2w_*.py` + `rg -n "_f2v_run\|plus_collected\|orig_warnings" _ci_checks.py` | 前者 `(0 hits across 4 consumers)`；后者 `(no hits -> scope is A only)` |
| C17 | 依次实跑 3 件 `_f2d*_fpcheck.py` | `_f2d`: 9/9 `MATCH`；`_f2dw`: `== RESULT bad=0 ==`；`_f2dv`: `MATCH=20 MISMATCH=0` |
| C18 | `python -I -X utf8 -c "…模拟 A.totals 合法改写…"` → `_tp_fpcheck_out.txt` | `new A sha= 0dfa03090ed19dc32a46a1a1dd4d230414c3c1e601cc4b4513b304d0dd067dba bytes= 43797`，≠ 基线 `148ea8d6…/44958`；B 指纹不变 |
| C19 | `python -I -X utf8 -c "…3 件锁是否含 B 产品/生产者…"` → `_tp_fpcheck_out.txt` | 三件均 `locks_B_product=False locks_A_producer=False locks_B_producer=False`；`rg` 亦 `(no hits)` |
| C20 | `rg -l "12e55acf…\|75108dca…" --glob '*.py' lead` | 命中 `_mk_probe.py`、`_mkv_fp.py`、`_mm_fp.py` 三件生产者指纹锁 |
| C21 | `rg -n --glob '*.py' "_f2v_run_out\.json" lead` | 运行期读者仅 `_mm_probe.py:84,124`、`_mkv_consumers.py:120`、`_f2v_run.py:70`（写）、本写域 `_tp_crosscheck.py:117` |
| C22 | `for f in $(rg -l "_f2v_run_out\.json" …); do rg -q "_f2_compare_out\.json" …` | `BOTH: _mm_probe.py` / `BOTH: _mkv_consumers.py`（仅审计脚本） |
| C23 | `rg -n "assert\|==\|!=" _mm_probe.py _mkv_consumers.py` + 逐行读 `:89-126`/`:118-149` | 两件只有 `EQUALS`（A 自洽）与 `print`，**无 A-vs-B 断言** |
| C5' | `python -I -X utf8 -c "…A/B totals 各自从 results 重算…"` | `A stored == recomputed from A.results: True`；`B stored == recomputed from B.results: True`；`declared_mismatch_files 0 == count(!seq_same) 0` |
| C24 | `python -I -X utf8 -c "…§3(e)(i) 共享聚合器片段自测（两次）…"` → `_tp_snippet_out.txt` | **首跑（扁平 rows view）**：`A equals disk totals = False`，`orig_problems=1 / plus_problems=0`（0 绑行件 problems 丢失）→ 片段设计缺陷，已改为逐件 view；**复跑（逐件 files[]）**：`A equals disk totals = True`、`B equals disk totals = True`，`policy_id = 8b6015a9…`（64 hex）。两次实跑均如实记录 |
| C25 | `python -I -X utf8 -c "…只读域 9 件指纹末次复算…"` → `_tp_readonly_out.txt` | 9 件 `MATCH=True`，`ALL_UNCHANGED=True`（本会话未改任何只读对象） |

**未跑 / 未验**（如实，不补造）：`_f2_compare.py` 与 `_f2v_run.py` 本体（纪律禁止改/重跑产物）；`_g9_gate.py` 可达性；甲/乙/丁的生产者改造落地；CI 是否真调用门禁；19 条绑定对象 SHA256 独立重算；两份一起漏改的反例（需 TP-7，当前盘无 `counting_policy`，未造）。

---

## 7 写域产出件

- `lead/two_products_20261109/_tp_ALIGNMENT.md`（本件）
- `lead/two_products_20261109/_tp_crosscheck.py`（只读交叉校验门禁，C5/C10 实跑）
- `lead/two_products_20261109/_tp_crosscheck_out.txt`（C5 输出）
- `lead/two_products_20261109/_tp_counterexamples_out.txt`（C10 输出）
- `lead/two_products_20261109/_tp_fpcheck_out.txt`（C18/C19 输出）
- `lead/two_products_20261109/_tp_snippet_out.txt`（C24 片段自测输出）

**声明**：本会话未修改 `lead/r11_f2_fix_20261109/`、`lead/count_invariant_20261109/`、`lead/merged_contract_20261109/`、`lead/gate_r9r12_20261109/`、两件台账中的任何文件；未 commit、未 push。
