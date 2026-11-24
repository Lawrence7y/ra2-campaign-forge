# COUNT_INVARIANTS.md — 巧合恒等复核 / 5 条不变量与反例 / merged 变化 / 回归门槛 / 边界

> 本件是「不变量件撰写员」的交付。只做不变量设计与反例验证，**未改** `_f2_compare.py`、
> `_f2v_run.py`、`_f2_compare_out.json` 或任何既有产物；反例 JSON 全部落在临时目录。
> 唯一写域 `lead/count_invariant_20261109/`，本次新增文件前缀 `_cii_`。
> 零真机（未启动 gamemd.exe / ra2loader / YURI.exe，未 taskkill，未读活进程内存）；
> 零采样代码（未写 hook / MiniDump / SuspendThread / StackWalk / 探针注入 / 动态内存解析）。
> Python 一律 `python -I -X utf8` + 绝对路径；指纹用 `hashlib`；不 commit、不 push。

---

## 1 目的与边界

**目的**：给 `lead/r11_f2_fix_20261109/_f2_compare_out.json` 的 7 键 `totals` 设计一组**可机检的计数不变量**，使「`plus_path == plus_match` 这个巧合恒等掩盖了维度缺失」这件事能被回归门槛抓到；逐条给出**违反它**的构造输入并实跑证明**能触发报警**。

**边界（本件只做什么）**：

- 只设计不变量 + 构造反例 + 复核上游结论；**不改任何既有件**。实跑只读的校验脚本与临时目录内的副本，不改 `lead/r11_f2_fix_20261109/`、`lead/merged_contract_20261109/`、`lead/r33e_merge_20261109/`、`lead/merged_safety_20261109/`、`lead/gate_r9r12_20261109/`、两件台账中的任何文件。末次 `hashlib` 复验 9 件只读对象 `ALL_PROTECTED_UNCHANGED = True`（命令/输出见 §6）。
- **不变量必须能被违反才叫不变量**：§3 的 5 条每条都配一个「违反它」的构造输入，且本会话实跑该输入确实报出对应 `INV-x` 报警；只给等式不算交付。
- 本会话独立实现求值器 `_cii_checks.py`（与上游 `_ci_checks.py`、`_civ_lib.py` 不共享代码），基线态 `violations=0`、merged 态 `--expect-merged` `violations=0`；17 个构造反例 `ALL_ALERT = True COUNT = 17 EXIT=0`（`_cii_counterexamples_out.txt`）。
- 本件**不裁决**模板所有者该选甲/乙/丙哪套计数口径；§5 只给长期代价与「未验」清单。
- **复核 verdict 如实记**：上游复核件对本主题前一版交付的 verdict 是 `partial`，并列出 4 处实缺陷。按交付要求，`partial` 标 **unconfirmed**：即上游「9 条不变量 + 10 个反例 + merged 判别式 + 可粘贴门槛」这一整套结论**不整体确认为已通过**；本件只把其中在本会话被独立复现的部分标为 confirmed，并把 4 处缺陷逐条如实列出、在本件 §3/§5 的可粘贴片段中修正。详见 §6。

---

## 2 上游指纹（八件）+ 巧合恒等复核

### 2.1 八件指纹（本会话 `hashlib` 实算全等）

命令（本会话实跑）：

```
python -I -X utf8 -c '
import hashlib, pathlib
base = pathlib.Path("D:/Project/ra2-campaign-forge")
expected = { ...8 件 (sha256, bytes)... }
for rel,(h,n) in expected.items():
    b = (base/rel).read_bytes()
    print(rel, hashlib.sha256(b).hexdigest(), len(b), hashlib.sha256(b).hexdigest()==h and len(b)==n)
print("ALL_8_FINGERPRINTS_MATCH =", allok)
'
```

输出（逐行 `OK`，末行）：

```
OK lead/r11_f2_fix_20261109/_f2_compare.py sha256=12e55acf42441aca846986a2447abffef77d774ee694cedf56a012c1c8907106 bytes=4821
OK lead/r11_f2_fix_20261109/_f2v_run.py sha256=75108dcaee4985f8623b59de18f8650ec6b78b73fbbd93ca3197f3057efdbd9a bytes=3469
OK lead/r11_f2_fix_20261109/_f2_compare_out.json sha256=148ea8d689eaaf582af05ea1bf4650605e104d6d74f8c7765e75a6eec662c7b1 bytes=44958
OK lead/r11_f2_fix_20261109/_f2_r11plus.py sha256=83f8217fb9a194befdd389f0fd9e699660d3240f0cf1eec365cc3d612fdf8f75 bytes=15723
OK lead/merged_contract_20261109/_mk_CONTRACT_DESIGN.md sha256=a968a17d096b49ab0b8e5941ff1bfbb57eeae68da727820c4cc8807cfa112432 bytes=56237
OK lead/r33e_merge_20261109/_re_linked.py sha256=7ca339c6beb728f488903e1b0c748708accf45cd5e3bce45d532290c0c755b52 bytes=19481
OK lead/PENDING_DECISIONS.md sha256=3765eddbe96deeb65eeb1f05dc81e1dc171e7ea3b2c826e2692a1d15e1c8f2d7 bytes=52419
OK lead/GOAL_THREE_TARGETS_20261018.md sha256=2baa0de45d4125549262eb595d7518c9ce99efeee120384bf640cded8a933ede bytes=759518
ALL_8_FINGERPRINTS_MATCH = True
```

与编排方给出的 8 件指纹逐字一致。另实算 `lead/merged_contract_20261109/MERGED_MERGE_CONTRACT.md` = `2c4f60a76e1b4fe9d4b90a4ee705f6e15008d4673b515dcbe27c8e0f11205ad2` / 64208 B（末次只读复验里列为第 9 件）。

### 2.2 巧合恒等：值相等

`lead/r11_f2_fix_20261109/_f2_compare_out.json:2-10` 七键：

```json
"totals": { "bindings": 19, "orig_path": 1, "plus_path": 9, "orig_match": 0,
            "plus_match": 9, "orig_problems": 24, "plus_problems": 23 }
```

`plus_path = 9 = plus_match`，30 件 `results[]` 共 19 条 `plus.bindings`。本会话实跑（命令与完整输出见 §6 `#2`，落 `lead/count_invariant_20261109/_cii_identity_out.txt`）：

```
TOTALS: {"bindings": 19, ..., "plus_match": 9, "plus_path": 9, ...}
n_results = 30
RECOMPUTED == STORED = True  (7/7)
plus_path == plus_match = True
```

### 2.3 巧合恒等：集合相同，不只是数字相同

同一实跑输出：

```
plus_path SET size = 9  plus_match SET size = 9
SET EQUAL = True  symmetric diff = []
COMMON 9: [(3, 0), (19, 1), (27, 3), (29, 0), (29, 1), (29, 2), (29, 3), (29, 4), (29, 5)]
CROSSTAB: {(True, True): 9, (False, False): 10}
file-level docs with path = 4  with match = 4  equal = True
```

即两个计数在**每条绑定上逐点等价**：9 条共同计入，其余 10 条一律 `path=None / match≠True`；没有一条落在 `(True,False)` 或 `(False,True)` 象限；文件级也同为 4 件。这一点很关键：如果只是 9==9 两个标量相等，CE-08 类的对称错值就能静默通过（§3 INV-2 反例）。

### 2.4 是否设计使然：是「版本相关恒等」，不是维度律

**聚合表达式依据**：`lead/r11_f2_fix_20261109/_f2_compare.py:65-71`：

- `:65` `tot["bindings"] += len(o_bind)`
- `:66` `orig_path += sum(1 for b in o_bind if b["path"])`
- `:67` `plus_path += sum(1 for b in n_bind if b.get("path"))`
- `:68` `orig_match += sum(1 for b in o_bind if b["match"] is True)`
- `:69` `plus_match += sum(1 for b in n_bind if b.get("match") is True)`
- `:70/:71` `*_problems += len(*_prob)`
- `:100` `OUT.write_text(json.dumps({"totals": tot, "results": results}, ...))` 只写、不自校验；`:47-50` 强制「原版采到 path 的绑定，增强版必须仍采到（原样）」。

**控制流依据**：`lead/r11_f2_fix_20261109/_f2_r11plus.py`：

- `:196` 初值 `{"declared": ..., "path": path, "match": None, "citation": ...}`。
- 有 T1 path 分支 `:201-248`：成功 `:248` `match=True`；失配 `:209`（`hit is None`）/`:240`（sha 或 bytes 不符）`match=False`，此时 **`path` 仍为真值**；同行替代锚命中 `:223` `match=True` 而 `path` 仍为原 T1 字符串（现盘 `(29,4)` 即此形态，`tier=T1`、有 `alt`、无 `recomputed`）。
- 无 T1 path 分支 `:250-305`：any-match-wins 成功 `:267-272` 用 `rec.update({"match":True,"path":verified["candidate"],...})` **同时写 path 与 match**；失败分支 `:276/:286/:293/:299` 一律 `match=False` 且 `path` 保持 `None`；`:303-305` 只设 `tier=None`。

⇒ **单向 `match is True ⟹ path 真值` 在现版本成立**（这是 `:66-69` 两类计数在这 30 件上恰好相等的原因），加上 `:47-50` 的保 path 断言，两个计数被压在「有无单一锚」同一根轴上。

**但双向 `match is True ⟺ path 真值` 不成立——这是上游复核缺陷 1，本会话独立复现**：本会话实跑

```
python -I -X utf8 D:/Project/ra2-campaign-forge/lead/count_invariant_20261109/_civ_structural.py
```

输出（节选）：

```
binding = {"declared": "0000…", "path": "probe.txt", "match": false, ..., "tier": "T1",
           "recomputed": "2cf24dba…", "bytes": 5, "verified_path": "…\\probe.txt"}
path truthy      = True
match is True    = False
==> (path 真值, match=False) 在【现版本 r11_scan_plus】里可达 = True
==> §1(c)『match is True ⟺ path 真值是控制流结构性后果』是否成立 = False
```

对应 `_f2_r11plus.py:239-246`（T1 失配分支）。所以**只能说「现盘语料里没有一条 `(path 真值, match=False)`」，不能说控制流禁止它**；反向差 `plus_path > plus_match` 在现版本可达（§4(c)）。本件据此不把 `plus_path == plus_match` 写成无条件物理律，而写成 **条件化恒等**（§3 INV-5：仅在 `E==0` 时锁）。

**它缺的正是维度**：`lead/r33e_merge_20261109/_re_linked.py:306-308` 注释写 `merged` 的 `rec["match"]=True` 仅指「声明 hex 与全体成员现盘重算逐位一致」、`rec["path"]` 恒 `None`（纪律一：不做单一对象主张）；`:320-329` 落 `tier="SAMEDOC_LINK_EQ"`、`match=True`、`members`、`decl_lines`，且 `:322-325` 明令**不写** `verified_path/recomputed/bytes`。接入该形态 ⇒ `:67` 不计、`:69` 计 ⇒ 恒等立刻破。`MERGED_MERGE_CONTRACT.md:143-150` 把它定性为「巧合性恒等」：代码里没有任何一处表达「match = 单一回验」，`:67` 无法表达「有 members 但无 path」这第三态；`:147-148` 明记 merged 的 `(0,+1)` 与「失配但也有 0 path」在 totals 里不可分辨。

### 2.5 tier 分布 / SAMEDOC_LINK_EQ

同一实跑（§2.2 命令）输出：

```
TIER COUNTS = {'T2N': 2, None: 10, 'T3': 1, 'T2': 5, 'T1': 1}  SUM = 19
SAMEDOC_LINK_EQ count = 0
explicit tier keys = 19 / 19
```

`None` 桶 10 条 = 「无路径无匹配」；**没有 merged（`SAMEDOC_LINK_EQ`=0），也没有 unique（`SAMEDOC_LINK`=0）**。这个 0 是 §4 所有 merged 判别式的基线。`MERGED_MIN_SAFETY_PATCH.md:280` 的 U1 手工喂入 `totals={"plus_path":0,"plus_match":1}` 是单条形态、口径不同，`MERGED_MERGE_CONTRACT.md:151-152` 明确不互相冒充。

---

## 3 五条不变量（逐条：可机检形式 + 现成立 + 反例能触发报警 + 防哪类维度缺失）

实现：`lead/count_invariant_20261109/_cii_checks.py`（`evaluate(doc, expect_merged=False) -> (violations, facts)`；只读、不 import 项目业务模块、不写盘）。反例：`lead/count_invariant_20261109/_cii_counterexamples.py`，输出 `_cii_counterexamples_out.txt`。

**基线实跑**（本会话）：

```
python -I -X utf8 D:/Project/ra2-campaign-forge/lead/count_invariant_20261109/_cii_checks.py D:/Project/ra2-campaign-forge/lead/r11_f2_fix_20261109/_f2_compare_out.json
→ FACTS: {"E": 0, "M": 0, "P_size": 9, "S_size": 9, "bindings": 19,
          "merged_present": false, "n_results": 30, "plus_match": 9, "plus_path": 9,
          "set_equal": true, "tiers": {"NONE": 10, "T1": 1, "T2": 5, "T2N": 2, "T3": 1},
          "tier_explicit": 19, ...}
→ OK violations=0 (all 5 invariants hold)   EXIT=0
```

**反例实跑**（本会话）：

```
python -I -X utf8 D:/Project/ra2-campaign-forge/lead/count_invariant_20261109/_cii_counterexamples.py
→ ALL_ALERT = True  COUNT = 17  EXIT=0
```

所有反例 JSON 只写 `tempfile.mkdtemp(prefix="_cii_ce_")`，未落既有写域/只读域。下表 5 条；「实跑报警」栏是 `_cii_counterexamples_out.txt` 里的原文。

---

### INV-1 — 计数与明细自洽（totals 绝不当权威）

**可机检形式**：

```
∀ k ∈ {bindings,orig_path,plus_path,orig_match,plus_match,orig_problems,plus_problems}:
    totals[k] == recomputed[k]        # recomputed 独立复刻 _f2_compare.py:65-71
∧ orig_problems, plus_problems ∈ ℤ≥0
∧ ∀ (i,side): len(results[i][side].problems)==0  ⟺  results[i][side].verdict=="PASS"
```

注意第三条是**双向等价**：`verdict` 取 `UNKNOWN`/`None` 等第三值也必须报警（上游 `_ci_checks.py:87-90` 的两个单条件 `if` 漏掉；且 `:90` 有 1 个 `%s` 占位符却传 2 参的格式化崩溃，见 §6 缺陷 2）。

**现成立**：`RECOMPUTED == STORED = True (7/7)`；24/23 非负；逐件 `problems[]` 与 `verdict` 一致（基线 `violations=0`）。

**能触发报警的反例**（3 个，均实跑）：

| 构造输入 | 实跑报警（`_cii_counterexamples_out.txt`） |
|:--|:--|
| `totals.plus_match = 8`，`results[]` 一字不动 | `INV-1 totals.plus_match=8 != recomputed=9` |
| `results[3].plus.verdict = "FAIL"` 而 `problems=[]`（文件 `A_REDUCED_FORM.md`） | `INV-1 (3,plus) nproblems=0 verdict='FAIL' inconsistent` |
| `results[3].plus.verdict = "UNKNOWN"` | `INV-1 (3,plus) nproblems=0 verdict='UNKNOWN' inconsistent` |

**防哪类维度缺失**：**计数口径与明细脱钩**（硬编码 / 漏计 / 改口径后 `totals` 不跟 `results[]` 变），以及 verdict 这个「判定维度」与 problem 明细不同步。§5(c) 的硬编码 9 就靠这一条被发现。

---

### INV-2 — 上界、覆盖单调、集合级恒等

**可机检形式**：

```
∀ k ∈ {orig_path,plus_path,orig_match,plus_match}: 0 ≤ totals[k] ≤ totals.bindings
∧ sum(len(orig.bindings)) == totals.bindings == len(plus_rows)
∧ orig_path ≤ plus_path  ∧  orig_match ≤ plus_match
∧ (totals.plus_path == totals.plus_match) ⟹ P == S
   其中 P = {(i,k) : b.get("path") 真值}, S = {(i,k) : b.get("match") is True}
```

最后一条是**集合级**而非数值级，是本题核心风险的直接一击。`_f2_compare.py:47-50` 的逐条保 path 断言在这里升级为聚合单调。

**现成立**：`19/1/9/0/9` 全在上界内；`1≤9`、`0≤9`；`P_size=S_size=9` 且 `set_equal=true`（§2.3）。

**能触发报警的反例**（3 个，均实跑）：

| 构造输入 | 实跑报警 |
|:--|:--|
| `totals.plus_path = 20` | `INV-2 plus_path=20 not in [0,19]` |
| `totals.orig_path = 12` | `INV-2 orig_path=12 > plus_path=9 coverage not monotone` |
| **CE-08 对称错值**：`(3,0).match=False`、`(6,0).match=True`，**`totals` 七键一字未改** | `INV-2 plus_path==plus_match numerically but SET differs: path\match=[(3, 0)] match\path=[(6, 0)]` |

CE-08 处实跑同时打印 `CE-08 totals unchanged = True  recomputed==stored = True` —— 即 INV-1 不报、7 键恒等式全成立，只有集合级断言报警。**这就是「恒等式仍成立所以误通过」的实证**：没有任何一条只看两个标量相不相等的断言能发现它（另 `INV-4` 也报 `M=1 != E=0`，但那属于 merged 判别维度）。

**防哪类维度缺失**：计数越界、分母（`bindings`）维度丢失、增强版丢原版已采锚、以及**「数字相等掩盖集合不等」**（对称错值）。

---

### INV-3 — tier 分类维度完备（键存在性，不只是计数和）

**可机检形式**：

```
Σ_tier count == totals.bindings
∧ ∀ (i,k): "tier" ∈ plus.bindings[k]           # 显式键，不能用 .get() 吞进 None 桶
∧ ∀ (i,k): tier ∈ {T1,T2,T2N,T3,None,SAMEDOC_LINK,SAMEDOC_LINK_EQ}
```

**现成立**：`{T2N:2,None:10,T3:1,T2:5,T1:1}` SUM=19；19/19 显式带 `tier` 键（§2.5）。

**能触发报警的反例**（2 个，均实跑）：

| 构造输入 | 实跑报警 |
|:--|:--|
| 删 `(3,0)` 的 `tier` 键（`T2N`） | `INV-3 (3,0) missing explicit tier key` |
| `(3,0).tier = "T9_NOT_A_TIER"` | `INV-3 (3,0) tier 'T9_NOT_A_TIER' not whitelisted` |

反例脚本同时打印 `CE-05 weak .get-only partition sum = 19 (still 19, no alert)`：**只用 `b.get("tier")` 计数时，删键被悄悄归进 `None` 桶、`Σ` 仍是 19、不报警** —— 这是「维度缺失被恒等掩盖」的最小实证。所以必须查键**存在性**，不能只查计数和。

**防哪类维度缺失**：**分类维度完备性**。`tier` 是后续 merged 判别唯一的正交维度；它一缺，INV-4 的 `E` 就恒为 0。

---

### INV-4 — merged 判别：M/E 相等 + 形状全称量词

**可机检形式**（`MERGED_TIER = "SAMEDOC_LINK_EQ"`）：

```
M := |{ b : ¬b.path ∧ b.match is True }|        # 无单一锚却匹配
E := |{ b : b.tier == "SAMEDOC_LINK_EQ" }|
M == E
∧ ∀ b with b.tier == MERGED_TIER:               # ★ 全称量词：只看 tier，不要求 match is True
       b.path is None ∧ b.match is True
     ∧ isinstance(b.members, list) ∧ len(b.members) ≥ 2
     ∧ {"verified_path","recomputed","bytes"} ∩ keys(b) == ∅
∧ (recomputed.plus_match − recomputed.plus_path) == E
∧ merged_present := (E>0 ∧ M==E ∧ 无形状违规 ∧ 差==E) == expect_merged
```

形状全称量词修正上游复核缺陷 3：上游 `_ci_checks.py:143-149` 的条件是 `(not path) and match is True and tier==MERGED_TIER`，**只在 `match is True` 时才查**；构造一条 `tier=SAMEDOC_LINK_EQ` 但 `match=None`/无 `members` 的畸形行，再用另一条 `M=1` 凑成 `M==E==1`，等式不报、形状检查被跳过，`_ci_gate.py --expect-merged` 甚至 `rc=0 OK violations=0`（`_civ_shape_out.txt:9-11`、`_civ_gaps_out.txt:20-22`）。

**现成立**：`M=0, E=0`，无 merged 行，`merged_present=false`（基线 `expect_merged=false`）。

**能触发报警的反例**（4 个，均实跑）：

| 构造输入 | 实跑报警 |
|:--|:--|
| 构造 `path=None, match=True, tier="T2"` 带 `members` 却**不打 merged 标** | `INV-4 M(match_no_path)=1 != E(merged_tier)=0 (non-merged cause OR missing merged dimension)` |
| merged 投影删 `(20,0).members`（`--expect-merged`） | `INV-4 (20,0) merged-tier row missing members>=2` + `merged_present=False != expected=True` |
| merged 投影给 `(20,0)` 加 `verified_path/recomputed/bytes`（`--expect-merged`） | 3 条 `INV-4 (20,0) merged-tier row has single-object key '…'` |
| 畸形 merged-tier 行（`match=None`、无 `members`） | `INV-4 (19,0) merged-tier row not match=True/path=None` + `…missing members>=2` |

后 3 个正是 `_civ_gaps_out.txt` 里 G1/G2 与 `_civ_final_out.txt` 里 malformed merged 行被 `_ci_gate.py` 静默放过的变异；本门槛四个都报警。

**防哪类维度缺失**：**匹配性质维度缺失**（merged 语义存在却没有 merged 标记）、merged 行违反三纪律（不做单一对象主张 / 不推导授权 / 全列 members）、以及「等式碰巧相等但形状已坏」。

---

### INV-5 — 新维度存在性 + 条件化恒等（INV-06 的正确重定义）

**可机检形式**：

```
v2 := (schema_version ≥ 2) ∨ ("counting_policy" 存在于 doc 或 totals)
v2 ⟹ "counting_policy" 存在
    ∧ totals.plus_match_by_kind.{single_path,merged_eq} 存在且为 int
    ∧ single_path == recomputed.plus_path
    ∧ single_path + merged_eq == recomputed.plus_match
    ∧ merged_eq == E
条件化恒等：
    E == 0 ⟹ recomputed.plus_path == recomputed.plus_match     # 基线恒等锁
    E  > 0 ⟹ recomputed.plus_match − recomputed.plus_path == E  # merged 恒等
```

**关键**：`plus_path == plus_match` **不是物理律**，是「`E==0` 且当前控制流」下的基线快照；`MERGED_MERGE_CONTRACT.md:472-496` 方案丙骨架给出 `plus_tier_counts / plus_match_by_kind / schema_version` 与恒等式 `plus_path == single_path`、`plus_match == single_path + merged_eq`，本条把它落成机检断言。把恒等从默认状态改成**有条件、可证伪**的状态，是 §5(b) 防误通过的第 3 条硬要求。

**现成立**：现盘 `schema_version` 缺省视为 1、无 `counting_policy`，条件假；`E=0` 且 `9==9`，基线恒等锁成立。

**能触发报警的反例**（3 个，均实跑）：

| 构造输入 | 实跑报警 |
|:--|:--|
| 只加 `schema_version=2`，不写 `counting_policy`/`by_kind` | `INV-5 schema_version>=2 but no counting_policy` + `…but no plus_match_by_kind` |
| `counting_policy="D-XXX"`、`by_kind={single_path:9,merged_eq:1}` 而 `plus_match=9` | `INV-5 single_path+merged_eq=10 != plus_match=9` + `merged_eq=1 != E(merged_tier)=0` |
| merged 态 `--expect-merged` 但 `schema_version=2` 缺 `counting_policy` | `INV-5 schema_version>=2 but no counting_policy` |

另有 `REVERSE_diff`（把 1 条 `match=True` 改 `False`、保留 path ⇒ `plus_path=9, plus_match=8`）实跑报 `INV-5 E=0 but baseline identity broken: plus_path=9 != plus_match=8` —— 证明「反向差」也被条件化恒等抓住，且呼应 §2.4 的 `(path 真值, match=False)` 现版本可达。

**防哪类维度缺失**：改口径后**新维度声明了却没落地 / 自相矛盾**；以及把基线恒等无条件保留（merged 一来就误报）或无条件丢弃（新维度缺失却静默通过）。

---

### 3.1 五条与上游 9 条的对应关系（便于对账）

| 本件 | 覆盖上游 | 本件修正 |
|:--|:--|:--|
| INV-1 | INV-01 + INV-04 | verdict ↔ problems 改双向等价；修 `:90` 格式化崩溃与 CE-04 空操作 |
| INV-2 | INV-02 + INV-03 + INV-08 | 合为一条「计数结构」不变量；保留 CE-08 集合级断言 |
| INV-3 | INV-05 | 显式键存在 + 白名单（`None` 桶吞键实证） |
| INV-4 | INV-07 | 形状检查改 `∀ tier==MERGED_TIER` 全称量词；加 `差==E` |
| INV-5 | INV-06 + INV-09 | INV-06 重定义为条件化恒等；v2 触发条件扩展为 `schema_version ∨ counting_policy` |

上游 `INV-06` 的「基线锁」在 merged 态必然破（§4(a)），**它不是维度律**；本件不把它单列为不变量，而并入 INV-5 的条件分支。

---

## 4 merged 出现后的变化

### 4(a) 恒等还成立吗？预期投影

**不成立**。本会话实跑（命令 `python -I -X utf8 .../lead/count_invariant_20261109/_cii_checks.py <proj> --expect-merged`，输出见 §6 `#5`）：

```
FACTS: {"E": 1, "M": 1, "P_size": 17, "S_size": 18, "bindings": 19,
        "merged_present": true, "plus_match": 18, "plus_path": 17,
        "set_equal": false, "match_minus_path": [[20, 0]],
        "tiers": {"NONE": 1, "SAMEDOC_LINK": 8, "SAMEDOC_LINK_EQ": 1,
                  "T1": 1, "T2": 5, "T2N": 2, "T3": 1}, ...}
OK violations=0 (all 5 invariants hold)   EXIT=0
```

预期投影来自上游 `_ci_merged_projection.py`（用 `lead/merged_contract_20261109/_mk_r11plus_candidate.py` 替换 `r11_scan_plus`、逐行复刻 `_f2_compare.py:35-71`、30 件全量、只写临时目录）。本会话**读其产物** `C:\Users\Administrator\AppData\Local\Temp\_ci_merged_r8prxhqj\merged_projection.json`（105859 B，本会话 `ls -l` 确认存在）并独立重算，`lead/count_invariant_20261109/_ci_merged_out.txt:2-9` 记：

```
BEFORE: {"bindings": 19, ..., "plus_match": 9,  "plus_path": 9,  ...}
AFTER : {"bindings": 19, ..., "plus_match": 18, "plus_path": 17, ...}
DRIFT : {'plus_path': (9, 17), 'plus_match': (9, 18)}
changed_docs=5 changed_bindings=10
M (match_no_path) = 1   E (merged_tier) = 1   U (unique_tier) = 8
```

与 `MERGED_MERGE_CONTRACT.md:359-363` 的 `(9,9)→(17,18)`、`_mm_project_out.txt:2-5` 一致。本会话**未重跑** `_f2_compare.py` / `_f2v_run.py` 本体（纪律禁止改/重跑产物），也**未重跑** `_ci_merged_projection.py`；投影值来自既有实跑产物 + 本会话独立重算验证，如实标注。

对本件门槛：同一份投影 `--expect-merged` → `violations=0`；**不带** `--expect-merged`（仍按基线态）→ `ALERT violations=1 - INV-4 merged_present=True != expected=False`。即「任何 merged 出现必触发至少一条报警」**只在基线态（未确认新维度）成立**；在 `--expect-merged` 已确认态，合法 merged 是 0 报警，这是设计意图（上游复核缺陷 4 要求限定作用域，本件照办）。

### 4(b) 「差 1」逐条解释

本会话独立逐条 diff（`python -I -X utf8 -c '…逐 (i,k) 对齐…'`，完整输出 `_cii_delta_out.txt`）：

```
DELTA histogram = {(0, 0): 1, (1, 1): 8, (0, 1): 1}
TOTAL Δ(pp,pm) = (8, 9)
changed_docs = 5  changed_bindings = 10
M = 1  E = 1  U = 8  diff = 1
SPECIAL (i,k)=(20,0) Δ=(0,1) tier='SAMEDOC_LINK_EQ' path=None match=True members_n=2
    keys=['citation','decl_lines','declared','match','members','path',
          'samedoc_link','tier','tried']
MERGED row file = ['…\\lead\\b2b_isolated_20261107\\_integ_INTEGRATION_REPORT.md']
```

- **8 条 unique**：`lead/merged_contract_20261109/_mk_r11plus_candidate.py:356-361` 对 `tier=="SAMEDOC_LINK"` 写 `verified_path/recomputed/bytes`；`_re_linked.py:314-319` 对 `verdict=="unique"` 设 `rec["path"]=reverify["path"]`、`rec["match"]=True` ⇒ 每条贡献 `(+1,+1)`。
- **1 条零贡献**：`(6,0)` `Δ=(0,0)`，`tier=None, path=None, match=None`（`_mk_r11plus_candidate.py:362` multi/zero/invalid_hex 类）。
- **1 条 merged**：`tier="SAMEDOC_LINK_EQ"`，`_re_linked.py:320-329` **只**写 `match=True`、`members`、`decl_lines`，`path` 保持 `None`，`:322-325` 明令不写单对象三键；`_mk_r11plus_candidate.py:349-355` 同样只补 `members/decl_lines` ⇒ 贡献 `(0,+1)`。`_mm_project_out.txt:22` 亦记 `C5 _f2_compare.py:67/69 对 merged 单条 = (0,1)`。

合计 `9+8+0 = 17`、`9+8+1 = 18`，**`18 − 17 = 1` 就是这一条 merged**。它是唯一 `match=True` 但无单一 path 的绑定（本会话投影实算 `M=1, E=1, match_minus_path=[[20,0]]`）。这与复核件 `_civ_step34_out.txt:3-25` 的独立逐条 diff 完全一致。

### 4(c) 只靠计数能否判 merged？**不能**

三层反证，本会话全部实跑（`_cii_counterexamples_out.txt`）：

1. **非 merged 也能造出差 1**：把 1 条 `(path=None,match=None,tier=None)` 仅改成 `match=True` ⇒
   `NON-MERGED-DIFF: plus_path=9 plus_match=10 diff=1 M=1 E=0 merged_present=False`，
   报警 `INV-4 M(match_no_path)=1 != E(merged_tier)=0`。纯计数 bug 能产生同样的 `+1`。
2. **差可以反向**：`REVERSE-DIFF: plus_path=9 plus_match=8 E=0`（把 1 条 `match=True` 改 `False`、保留 path）。代码面 `_f2_r11plus.py:239-246` 支持此形态，§2.4 的 `_civ_structural.py` 实跑已在现版本造出 `(path 真值, match=False)`。⇒ 差值符号不是 merged 的单向指标。
3. **差 1 ≠ 恰好一条 merged**：`_civ_final_out.txt:1-5` 实跑 `plus_path=10 plus_match=11 diff=1 E=2 M=2 merged_present=True` —— 差 1 却 2 条 merged；差可由 unique 漏计与 merged 增量互相凑出。`MERGED_MERGE_CONTRACT.md:147-148` 亦指出 merged 与「失配但也有 0 path」在 totals 里不可分辨。

**更强的不可判证明（本会话实跑，输出 `_cii_manytoone_out.txt`）**：构造两份 `results[]` 不同、**7 键 `totals` 逐字相同**的输入——A 把 `(6,0)` 改成 `match=True` 且 `tier=None`；B 在同一 `(6,0)` 上把 `tier` 改成 `SAMEDOC_LINK_EQ` 并补 `members`（`path/match` 不变）：

```
target (i,k) = (6, 0)
A totals = {"bindings": 19, ..., "plus_match": 10, "plus_path": 9, "plus_problems": 23}
B totals = {"bindings": 19, ..., "plus_match": 10, "plus_path": 9, "plus_problems": 23}
7-key totals EQUAL = True
results[] EQUAL = False
A(no merged tier): M=1 E=0 merged_present=False ...
B(merged tier):    M=1 E=1 merged_present=True ...
```

⇒ 7 键是从 19 条绑定的二维布尔表压到 7 个标量的**有损多对一投影**，纯计数集上**不存在**「merged 出现 ⟺ 某等式」的充要判别式。

### 4(d) 判别式：加上正交 `tier` 维度后存在

```
M := |{ b : ¬b.path ∧ b.match is True }|
E := |{ b : b.tier == "SAMEDOC_LINK_EQ" }|
merged_present := (E > 0) ∧ (M == E)
              ∧ (∀ b with tier=="SAMEDOC_LINK_EQ":
                     b.path is None ∧ b.match is True
                   ∧ isinstance(b.members, list) ∧ len(b.members) ≥ 2
                   ∧ {"verified_path","recomputed","bytes"} ∩ keys(b) == ∅)
              ∧ (plus_match − plus_path == E)
              ∧ (schema_version≥2 ⟹ by_kind.single_path==plus_path
                                    ∧ by_kind.merged_eq==E
                                    ∧ single_path+merged_eq==plus_match)
```

本会话两态实跑：基线 `E=M=0` ⇒ `merged_present=false`；投影 `E=M=1`、`差=1`、形状 0 违规 ⇒ `merged_present=true`（`_cii_checks.py` 的 `facts["merged_present"]`）。这正是 INV-4 + INV-5 的组合。

**最强保证要限定作用域**：若 merged 存在却**不打 `tier` 标记**（CE-07 构造），`E=0, M=1` ⇒ `M != E` 报警，说「要么有非 merged 原因、要么维度缺失」，不会静默判成「无 merged」。所以在**基线态（`expect_merged=false`）**，「任何 merged 出现（无论标不标记）都会触发至少一条报警」成立；在**已确认态（`--expect-merged`）**，合法 merged 是 0 报警，但形状违规/维度未落地仍由 INV-4/INV-5 报警（§3 的 M-G1/G2/G3/G5 实跑）。语义标签本身必须由生产者写入，计数无法凭空造出来。

---

## 5 回归门槛

### 5(a) 改口径前后查哪些不变量

| 阶段 | 必查 | 期望 |
|:--|:--|:--|
| 改前基线 | INV-1..5 全跑（默认 `expect_merged=false`） | `violations=0`、`set_equal=true`、`E=0`、`tier_explicit=19` |
| 改口径（甲/乙/丙任一）后 | INV-1/2/3/4 全跑；INV-5 在 `schema_version≥2 ∨ counting_policy` 时强制生效 | `0`；`v2` 时 `single_path==plus_path`、`single_path+merged_eq==plus_match`、`merged_eq==E` |
| 接入 merged 后 | INV-4 加 `--expect-merged` | `M==E>0`、`merged_present=true`、形状 0 违规、`差==E` |
| 接入 merged 后 | INV-2 集合级 | `plus_path≠plus_match` 时 `S−P` 必须恰为 merged 行（投影实跑 `match_minus_path=[[20,0]]`） |
| 全程 | INV-1 独立重算 | 永远以 `results[]` 为准，`totals` 不得当权威 |
| 全程 | 17 个反例 CI 必跑 | `ALL_ALERT = True COUNT = 17 EXIT=0`，否则门槛本身失效 |
| 全程 | 指纹锁 | 改口径必然 DRIFT，须重基线；**不得把指纹锁当计数不变量**（`MERGED_MERGE_CONTRACT.md:382`） |

### 5(b) 防「恒等式仍成立所以误通过」的三条硬要求

1. **断言源必须是 `results[]`**。INV-1 逐键复刻 `_f2_compare.py:65-71` 从明细重算。若测试写成 `assert totals["plus_path"] == totals["plus_match"]`，两键一起硬编码成同一个错值（如都写 9）会**通过** —— 这正是「恒等掩盖一切」。
2. **必须跑「配对对称错值」变异测试 CE-08**：`totals` 一个字节未改、7 键重算仍全等、INV-1/基线恒等都不报，只有集合级 INV-2 报 `path\match=[(3,0)] match\path=[(6,0)]`（`_cii_counterexamples_out.txt`）。把 CE-08 列为回归必跑反例。
3. **加维度存在性断言而非只加恒等式**：INV-3 查 `tier` 键存在（CE-05 证明弱 `.get()` 版 `Σ` 不变不报警）、INV-5 查 `schema_version/counting_policy/plus_match_by_kind`，INV-4 的 merged 形状用全称量词。再加**条件化恒等哨兵**：`E==0` 必须 `plus_path==plus_match`；`E>0` 必须 `差==E`。

**上游复核缺陷 4 的修正**：§5(d) 的可粘贴片段是**完整 5 条门槛**，不是上游 `_ci_gate.py` 的弱化版。`_civ_gaps_out.txt:4-17,35-53` 实跑显示上游 gate 对 G1（merged 行删 members）、G2（加单对象三键）、G4（verdict 谎言）、G4b（UNKNOWN）、G5（未知 tier）、G6（v2 缺 policy）全部 `rc=0 OK violations=0` 静默放过；本件 `_cii_checks.py` 对同类变异全部报警（§3 反例表 + `_cii_counterexamples_out.txt` M-G1/G2/G3/G5）。上游「对变异仍报警」只对 CE-08 与非 merged 差两类成立，本件不作那样的全称宣称。

### 5(c) 硬编码 9 的反例能否被发现？

本会话实跑 `python -I -X utf8 .../lead/count_invariant_20261109/_cii_hardcode9.py`（输出 `_cii_hardcode9_out.txt`）：

**CASE B**：拿 merged 投影（真值 `plus_match=18`），把 `totals.plus_match` 硬编码为 `9`：

```
  _f2w_checks.py rc=0 output_has_totals=False notable=['sha 逐字一致条数 = 8']
  _f2w_pass.py   rc=0 output_has_totals=False notable=['R11 PASS: orig=6 plus=7 | overall PASS: orig=6 plus=7']
  _f2w_extract.py rc=0 output_has_totals=False notable=['rows=19 plus_bindings=19 orig_bindings=19']
  _f2w_final.py  rc=0 output_has_totals=False notable=[]
  _cii_checks --expect-merged rc=1 alerts=['ALERT violations=1', '- INV-1 totals.plus_match=9 != recomputed=18']
  _cii_checks (baseline mode) rc=1 alerts=['ALERT violations=2',
      '- INV-1 totals.plus_match=9 != recomputed=18', '- INV-4 merged_present=True != expected=False']
```

⇒ **现有 4 个 JSON 消费者一个都发现不了；本件门槛发现（INV-1）**。依据（本会话 `grep -n -E "totals|results|cmp_" lead/r11_f2_fix_20261109/_f2w_*.py` 实跑）：`_f2w_checks.py:14,17,26`、`_f2w_extract.py:13,17,20`、`_f2w_pass.py:7,11,21-24`、`_f2w_final.py:31-33` 全部只取 `cmp_["results"]`，`totals` **0 命中**；`_f2_compare.py:100` 与 `_f2v_run.py:70-72` 只写 totals、不做自校验。

**CASE A**（baseline 副本写 9，值恰好等于真值）：4 个消费者全 `rc=0`，本件门槛 `OK violations=0` —— 因为语义无误，本来就不该报。**CASE C**（投影写回正确 18）：4 个消费者仍 `rc=0`，`_cii_checks --expect-merged` `OK violations=0`，而上游 `_ci_checks.py` 仍报 `INV-06 plus_path=17 != plus_match=18`（`_ci_hardcode9_out.txt:29`）—— 证明无条件基线锁在 merged 态是误报，必须条件化。

三个指纹锁 `_f2d_fpcheck.py` / `_f2dw_fpcheck.py` / `_f2dv_fpcheck.py` 对**原件**实跑全 `MATCH`（`_civ_hardcode9_rerun.txt:8-11`、`_cii_hardcode9_out.txt` CASE A 未改原件），但它们读的是原路径，是**字节变化检测器**：合法口径改写也 DRIFT（`MERGED_MERGE_CONTRACT.md:382`），且检测不出「原路径上 totals 被改而指纹基线被一并更新」。

**缺的正是**：INV-1（totals vs `results[]` 独立重算）、条件化恒等（INV-5）、以及「反例必须实跑」的 CI 门槛 —— 现有测试全是正向断言，无 mutation 用例。

### 5(d) 可粘贴片段（完整 5 条门槛，非弱化版）

```python
# 粘贴到回归脚本；doc = json.loads(Path(json_path).read_text(encoding="utf-8"))
# 本片段 = lead/count_invariant_20261109/_cii_checks.py 的 evaluate() 等价实现；
# 零真机、零采样代码、只读、不写盘、不 import 项目业务模块。
from collections import Counter

SEVEN = ("bindings", "orig_path", "plus_path", "orig_match",
         "plus_match", "orig_problems", "plus_problems")
TIERS = {"T1", "T2", "T2N", "T3", None, "SAMEDOC_LINK", "SAMEDOC_LINK_EQ"}
MERGED = "SAMEDOC_LINK_EQ"

def ci_gate(doc, expect_merged=False):
    T, R = doc.get("totals", {}), doc.get("results", [])
    v = []
    rows = [(i, k, b) for i, r in enumerate(R)
            for k, b in enumerate(r.get("plus", {}).get("bindings", []))]
    # ---- INV-1: totals 必须从 results[] 独立重算（复刻 _f2_compare.py:65-71）----
    rec = dict.fromkeys(SEVEN, 0)
    for r in R:
        ob, nb = r["orig"]["bindings"], r["plus"]["bindings"]
        rec["bindings"]      += len(ob)                                        # :65
        rec["orig_path"]     += sum(1 for b in ob if b["path"])               # :66
        rec["plus_path"]     += sum(1 for b in nb if b.get("path"))           # :67
        rec["orig_match"]    += sum(1 for b in ob if b["match"] is True)      # :68
        rec["plus_match"]    += sum(1 for b in nb if b.get("match") is True)  # :69
        rec["orig_problems"] += len(r["orig"]["problems"])                    # :70
        rec["plus_problems"] += len(r["plus"]["problems"])                    # :71
    for k in SEVEN:
        if T.get(k) != rec[k]:
            v.append("INV-1 totals.%s=%r != recomputed=%r" % (k, T.get(k), rec[k]))
    if not all(isinstance(T.get(k), int) and T[k] >= 0
               for k in ("orig_problems", "plus_problems")):
        v.append("INV-1 negative/non-int problems")
    for i, r in enumerate(R):                     # 双向等价：第三值 verdict 也报警
        for side in ("orig", "plus"):
            s = r[side]
            if (len(s.get("problems", [])) == 0) != (s.get("verdict") == "PASS"):
                v.append("INV-1 (%d,%s) verdict/problems inconsistent" % (i, side))

    # ---- INV-2: 上界 / 单调 / ★集合级恒等 ----
    nb = T.get("bindings", 0)
    for k in ("orig_path", "plus_path", "orig_match", "plus_match"):
        if not (isinstance(T.get(k), int) and 0 <= T[k] <= nb):
            v.append("INV-2 %s out of [0,bindings]" % k)
    if rec["bindings"] != nb or len(rows) != nb:
        v.append("INV-2 bindings/plus_rows mismatch")
    if T.get("orig_path", 0) > T.get("plus_path", 0) or \
       T.get("orig_match", 0) > T.get("plus_match", 0):
        v.append("INV-2 coverage not monotone")
    P = {(i, k) for i, k, b in rows if bool(b.get("path"))}
    S = {(i, k) for i, k, b in rows if b.get("match") is True}
    if T.get("plus_path") == T.get("plus_match") and P != S:
        v.append("INV-2 numeric equal but SET differs: %r / %r"
                 % (sorted(P - S), sorted(S - P)))          # CE-08 唯一抓得到的断言

    # ---- INV-3: tier 显式键 + 白名单（.get() 会把缺键吞进 None 桶）----
    if sum(Counter("<NOKEY>" if "tier" not in b else b.get("tier")
                   for _, _, b in rows).values()) != nb:
        v.append("INV-3 tier partition incomplete")
    for i, k, b in rows:
        if "tier" not in b:
            v.append("INV-3 (%d,%d) missing explicit tier key" % (i, k))
        elif b.get("tier") not in TIERS:
            v.append("INV-3 (%d,%d) tier %r not whitelisted" % (i, k, b.get("tier")))

    # ---- INV-4: merged 判别；形状检查用全称量词 ∀ tier==MERGED ----
    M = sum(1 for _, _, b in rows if not b.get("path") and b.get("match") is True)
    E = sum(1 for _, _, b in rows if b.get("tier") == MERGED)
    if M != E:
        v.append("INV-4 M=%d != E=%d (non-merged cause OR missing merged dimension)" % (M, E))
    bad = 0
    for i, k, b in rows:
        if b.get("tier") != MERGED:
            continue
        if b.get("path") is not None or b.get("match") is not True:
            v.append("INV-4 (%d,%d) merged row not match=True/path=None" % (i, k)); bad += 1
        if not isinstance(b.get("members"), list) or len(b.get("members", [])) < 2:
            v.append("INV-4 (%d,%d) merged row missing members>=2" % (i, k)); bad += 1
        for key in ("verified_path", "recomputed", "bytes"):
            if key in b:
                v.append("INV-4 (%d,%d) merged row has %r" % (i, k, key)); bad += 1
    if rec["plus_match"] - rec["plus_path"] != E:
        v.append("INV-4 plus_match-plus_path != merged_eq=%d" % E)
    present = (E > 0 and M == E and not bad
               and rec["plus_match"] - rec["plus_path"] == E)
    if present != expect_merged:
        v.append("INV-4 merged_present=%r != expected=%r" % (present, expect_merged))

    # ---- INV-5: 新维度存在性 + 条件化恒等（INV-06 的正确重定义）----
    sv = doc.get("schema_version", T.get("schema_version", 1))
    policy = ("counting_policy" in doc) or ("counting_policy" in T)
    if (isinstance(sv, int) and sv >= 2) or policy:
        if not policy:
            v.append("INV-5 schema_version>=2 but no counting_policy")
        k = T.get("plus_match_by_kind")
        if not isinstance(k, dict):
            v.append("INV-5 no plus_match_by_kind")
        else:
            sp, me = k.get("single_path"), k.get("merged_eq")
            if not (isinstance(sp, int) and isinstance(me, int)):
                v.append("INV-5 by_kind incomplete")
            else:
                if sp != rec["plus_path"]:   v.append("INV-5 single_path != plus_path")
                if sp + me != rec["plus_match"]: v.append("INV-5 sp+me != plus_match")
                if me != E:                  v.append("INV-5 merged_eq != E")
    if E == 0:
        if rec["plus_path"] != rec["plus_match"]:
            v.append("INV-5 E=0 but baseline identity broken")
    elif rec["plus_match"] - rec["plus_path"] != E:
        v.append("INV-5 merged state identity incomplete")
    return v

# CI 用法（缺一不可）：
#   v = ci_gate(json.loads(Path(p).read_text(encoding="utf-8")), expect_merged=False)
#   assert not v, "\n".join(v)
#   且必须同时跑 _cii_counterexamples.py：ALL_ALERT=True COUNT=17 才算门槛有效；
#   改口径后另跑 ci_gate(proj, expect_merged=True)，期望 violations=0。
```

**实跑记录**：`_cii_checks.py` 对现盘 `OK violations=0 EXIT=0`；对 merged 投影 `--expect-merged` `OK violations=0 EXIT=0`；对同一投影按基线态 `ALERT violations=1 - INV-4 merged_present=True != expected=False EXIT=1`；17 个反例 `ALL_ALERT=True COUNT=17 EXIT=0`。同一套门槛两态皆可用、且对上述变异仍报警。

**可粘贴片段本身也实跑过**（不是只写在纸上）：本会话把 §5(d) 的 `python` 代码块原样抽出落 `lead/count_invariant_20261109/_cii_pasted_gate.py`，再对 10 个输入（baseline / merged `--expect-merged` / merged 基线态 / `pm8` / `verdict_UNKNOWN` / `tier_key_dropped` / CE-08 / G1 无 members / G2 单对象键 / v2 缺 policy）同时跑 `ci_gate()` 与 `_cii_checks.evaluate()`：

```
baseline               pasted=0 hard=0 prefixes_equal=True  []
merged                 pasted=0 hard=0 prefixes_equal=True  []
merged-baseline-mode   pasted=1 hard=1 prefixes_equal=True  ['INV-4']
pm8                    pasted=1 hard=1 prefixes_equal=True  ['INV-1']
verdict_UNKNOWN        pasted=1 hard=1 prefixes_equal=True  ['INV-1']
tier_key_dropped       pasted=1 hard=1 prefixes_equal=True  ['INV-3']
CE08                   pasted=2 hard=2 prefixes_equal=True  ['INV-2', 'INV-4']
G1_no_members          pasted=2 hard=2 prefixes_equal=True  ['INV-4', 'INV-4']
G2_single_key          pasted=2 hard=2 prefixes_equal=True  ['INV-4', 'INV-4']
v2_no_policy           pasted=2 hard=2 prefixes_equal=True  ['INV-5', 'INV-5']
SNIPPET_BEHAVIORALLY_EQUIVALENT = True
```

（`_cii_pasted_gate_out.txt`。）判定标准是**报警条数与 `INV-x` 前缀多重集全等**；两者的报警文本措辞略有差别（片段用短句，`_cii_checks.py` 带完整数值），但行为等价。

---

## 6 复核回件（绑定行）+ 边界 + 未验项

### 6.1 绑定行（格式固定）

被核对象 SHA256 = 148ea8d689eaaf582af05ea1bf4650605e104d6d74f8c7765e75a6eec662c7b1，字节数 = 44958

被核对象 = `lead/r11_f2_fix_20261109/_f2_compare_out.json`。实跑命令：

```
python -I -X utf8 -c "import hashlib,pathlib; b=pathlib.Path(r'D:\Project\ra2-campaign-forge\lead\r11_f2_fix_20261109\_f2_compare_out.json').read_bytes(); print(hashlib.sha256(b).hexdigest(),len(b))"
```

实跑输出：`148ea8d689eaaf582af05ea1bf4650605e104d6d74f8c7765e75a6eec662c7b1 44958`（同值亦见 §2.1 八件指纹实算与 §6.4 末次只读复验）。

### 6.2 复核 verdict 如实记

上游复核件（`【复核】` 段）对前一版交付的 verdict = **`partial`**，按本任务要求标 **`unconfirmed`**：整套「9 条不变量 + 10 反例 + merged 判别式 + 可粘贴门槛」**不整体确认为通过**。本会话能独立复现并标 confirmed 的部分：8 件指纹全等、7 键值与集合相同、tier 分布、`(9,9)→(17,18)` 与「差 1 就是 merged」、非 merged 也能造差 1、硬编码 9 的 4 个消费者全 `rc=0`、10 个反例全部报警（本会话 verbatim 重跑 `ALL_ALERT = True COUNT = 10`）。

**4 处实缺陷（上游复核指出，本会话逐条复现/修正）**：

1. **§1(c) 断言过强且自相矛盾**：`_ci_INVARIANTS.md:73` 称 `match is True ⟺ path 真值` 是「控制流结构性后果」；本会话 `_civ_structural.py` 实跑造出 `(path 真值, match=False, tier=T1)`（对应 `_f2_r11plus.py:239-246`），双向不成立。本件 §2.4 只承认单向蕴含，并把基线恒等条件化。
2. **CE-04 反例不实 + `_ci_checks.py:90` 崩溃**：回件称 CE-04 构造「`#0 plus.verdict=FAIL` 而 `problems=[]`」，但实读 `compare_out.json` 的 `results[0].plus.problems` 有 1 条、`verdict` 原就是 FAIL ⇒ 那句赋值是空操作；真正触发报警的只有 `plus_problems=-1`。且 `_ci_checks.py:90` 为 `"INV-04 %s.verdict=FAIL but problems=0" % (side, np)`（1 占位符传 2 参），真构造会 `TypeError: not all arguments converted during string formatting`（`_civ_gaps_out.txt:21` G4）。本件 INV-1 用双向等价实现，反例 CE01b/CE01c 真构造且实跑报警，无格式化崩溃。
3. **INV-07 的 §3(d) 全称量词未落地**：`_ci_checks.py:143-149` 只覆盖 `match is True` 的 merged 行；`_civ_shape_out.txt:9-11` 用 `M==E==1` 的畸形 merged 行使整套只剩 INV-06 报警，`_ci_gate.py --expect-merged` `rc=0 OK violations=0`。本件 INV-4 改为 `∀ tier==MERGED_TIER`，反例 M-G3 实跑报警。
4. **§4(d) 可粘贴门槛是弱化版**：`_civ_gaps_out.txt:45-53` 对 G1/G2/G4/G4b/G5/G6 六类变异 `_ci_gate.py` 全 `rc=0` 静默放过；且「任何 merged 出现必触发至少一条报警」未限定基线态（真实 merged 投影在 `--expect-merged` 下 0 报警）。本件 §5(d) 片段为完整 5 条、§4(a) 明确限定作用域。

### 6.3 边界：判不了什么 / 计数对 vs 判定对 / 不引入新维度的长期代价

**判不了什么（如实列，均为「未验」或「设计上超出范围」）**：

1. **判不了语义正确**：`match=True` 是否真对应正确被核对象，只有逐字 SHA 比对能判。`_f2w_checks.py:29` 实跑 `sha 逐字一致条数 = 8`（9 条 match 里 `(29,4)` 走 `alt`、无 `recomputed`，`:29` 判 `sha_ok=False`）—— 不变量完全看不出。
2. **判不了 hash 是否被正确重算**：`recomputed/declared` 一致需独立 `hashlib` 复算；本任务未重算 19 条绑定所指向对象的 SHA256。
3. **判不了 verdict 的业务正确性**：INV-1 只查 `problems[]` 与 `verdict` 形式一致，不查 R3-3a/3b/3c 该不该报；`MERGED_MERGE_CONTRACT.md:160` 指出 merged `problems=[] ⇒ plus.verdict="PASS"`，不变量不报警。
4. **判不了 tier 值语义**（T1/T2/T2N/T3 采集是否恰当），只查完备性与白名单。
5. **判不了 30 件清单代表性/是否漏件**：`n_results=30` 是本批事实，非目标值。
6. **判不了 `members` 内容真实性**：INV-4 只查 `len≥2` 与键存在，不查两成员 sha/bytes 是否真相等（本会话仅读投影 JSON 内 `members` 字段一致，未独立重算 `_integ_INTEGRATION_REPORT.md` 两成员现盘 sha）。
7. **判不了「该有 merged 却整体漏检」**：若谓词漏检，`M=E=0`、5 条全通过。需独立 oracle（人工标注 merged 清单）。
8. **判不了跨文件一致**：`_f2v_run.py:60-72` 写第二件 9 键 totals（`_f2v_run_out.json`），`MERGED_MERGE_CONTRACT.md:377`、`_mm_project_out.txt:24` 记它同步漂移；本件 5 条只覆盖 `_f2_compare_out.json`，两者对账需另加断言。

**计数对不等于判定对（核心）**：计数是**投影**，判定是**语义**。`MERGED_MERGE_CONTRACT.md:143-148` 指出这 9 条既可能是 unique 单一回验、也可能是 merged 副本群，计数无法区分，而「能否由该条推导单一对象授权结论」正是纪律二（`_re_linked.py:30-33`）的核心。反过来 §5(c) CASE B 实跑：把 `plus_match` 写成错的 9，4 个消费者全部 `rc=0`、报告照出 `sha 逐字一致条数 = 8` 与 `R11 PASS: orig=6 plus=7` ⇒ **判定/统计看起来完全正常而计数已坏**。计数自洽是必要非充分条件。

**不引入新维度（保持现 7 键）的长期代价**：

1. **merged 永久不可分辨**：投影 `plus_match=18 = 17 unique + 1 merged`，`_f2w_pass.py:17` 继续把 merged 计入「已回验」；`MERGED_MERGE_CONTRACT.md:372,380` 记「merged 被计入已回验统计」「门禁 `:160` 仍 PASS，1 条零单一锚定 merged 被静默放过」。
2. **恒等式是脆基线**：`plus_path==plus_match` 只因当前控制流与这批语料成立（§2.4，`(path 真值,match=False)` 现版本可达 ⇒ 反向差也成立）；任何新 tier / 新 match 来源都会破它，没有分类键就永远要人工考古「是 merged 来了还是计数写错了」。
3. **回归测试失去灵敏度**：CE-08 证明可构造 7 键全等但集合已坏的输入；本会话 `grep` 实跑确认读 `totals` 的消费者 = 0，硬编码 9 无人发现。
4. **指纹锁与口径改动互相掣肘**：3 件 `_f2d*_fpcheck.py` 硬编码 `148ea8d6…/44958`（`MERGED_MERGE_CONTRACT.md:382` 列 `:11`/`:22`/`:27`），任何合法口径改写都 DRIFT，长期要么不改进、要么每次重基线且承担「合法改动与篡改不可分」。
5. **第二份产物漂移无监控**：`_f2v_run_out.json` 9 键 totals 会随接入同步变（`_mm_project_out.txt:24` C7），两份口径不同键却无人对账。
6. **代价复利**：每新增一种匹配形态（multi、zero、跨文档等价类）都在 `(plus_path, plus_match)` 平面加一个不可分辨点；7 个标量承载不了 N 态分类（§4(c) 多对一实证）。

建议（**不作裁决**）：采用 `MERGED_MERGE_CONTRACT.md:472-496` 方案丙骨架（`plus_tier_counts / plus_match_by_kind / schema_version / counting_policy`），并把本件 INV-1..5 + 17 个反例接进 CI；最低限度也要加 `plus_match_by_kind` 与 `schema_version`，否则代价 1/3 无法缓解。

### 6.4 未验项（如实，不补造）

- **未重算** 19 条绑定所指向对象的 SHA256；**未独立重算** `_integ_INTEGRATION_REPORT.md` 两成员现盘 sha（仅读投影 JSON 的 `members` 字段一致）。
- **未跑** `_f2_compare.py` / `_f2v_run.py` 本体，也**未重跑** `_ci_merged_projection.py`（纪律：不改、不重跑产物）；§4 的投影值来自既有实跑产物 `_ci_merged_r8prxhqj/merged_projection.json` + 本会话独立逐条重算（`_cii_delta_out.txt`）。
- **未接入或修改**任何门禁；`_g9_gate.py:155` 当前不可达，仅引用 `MERGED_MERGE_CONTRACT.md:380` / `_mm_project_out.txt:26` 的既有实跑。
- **未验证**方案甲/乙/丙各自落盘后的 totals（只读方案件文字，未执行 `_mk_*` 写盘分支）。
- **未验** `results[]` 里 `match=True` 的对象哈希逐字一致性（见边界 1/2）。
- 零真机、零采样代码：全程未启动游戏进程、未写 hook / MiniDump / SuspendThread / StackWalk / 探针注入 / 动态内存解析；未 commit、未 push。

**末次只读复验**（本会话实跑，`_cii_readonly_out.txt`）：`hashlib` 对 8 件编排方指纹 + `MERGED_MERGE_CONTRACT.md` 共 9 件逐件重算 → 9 行 `UNCHANGED`，`ALL_PROTECTED_UNCHANGED = True`。`git status` 层面本件产物只在 `lead/count_invariant_20261109/`（前缀 `_cii_`），未触碰任何只读件。

### 6.5 本会话实跑命令与输出索引

| # | 命令（均在 `D:/Project/ra2-campaign-forge` 下） | 输出 |
|--:|:--|:--|
| 1 | `python -I -X utf8 -c '…8 件 hashlib…'` | `ALL_8_FINGERPRINTS_MATCH = True`，逐行 `OK rel sha256=… bytes=…`（§2.1） |
| 2 | `python -I -X utf8 -c '…读 compare_out 统计…'` → `tee lead/count_invariant_20261109/_cii_identity_out.txt` | `SET EQUAL = True symmetric diff = []`；`COMMON 9=[(3,0),(19,1),(27,3),(29,0..5)]`；`CROSSTAB={(True,True):9,(False,False):10}`；`TIER COUNTS={T2N:2,None:10,T3:1,T2:5,T1:1} SUM=19`；`SAMEDOC_LINK_EQ count=0`；`explicit tier keys=19/19`；`RECOMPUTED == STORED = True (7/7)` |
| 3 | `python -I -X utf8 lead/count_invariant_20261109/_civ_structural.py` | `path truthy=True / match value=False / tier=T1`；双向 `⟺` 不成立（§2.4） |
| 4 | `python -I -X utf8 lead/count_invariant_20261109/_cii_checks.py <baseline>` | `OK violations=0 (all 5 invariants hold) EXIT=0` |
| 5 | `python -I -X utf8 …/_cii_checks.py <merged_projection> --expect-merged` | `OK violations=0 EXIT=0`，`E=1 M=1 P_size=17 S_size=18 match_minus_path=[[20,0]]`；不带 flag → `ALERT violations=1 - INV-4 merged_present=True != expected=False EXIT=1` |
| 6 | `python -I -X utf8 …/_cii_counterexamples.py` → `tee _cii_counterexamples_out.txt` | `ALL_ALERT = True COUNT = 17 EXIT=0`（5 条各 ≥1 反例 + 4 个 merged 态变异 + 非 merged 差 + 反向差） |
| 7 | `python -I -X utf8 -c '…逐 (i,k) diff 投影…'` → `tee _cii_delta_out.txt` | `DELTA histogram={(0,0):1,(1,1):8,(0,1):1}`、`TOTAL Δ=(8,9)`、`changed_docs=5 changed_bindings=10`、`M=1 E=1 U=8`、merged 行 `(20,0)` |
| 8 | `python -I -X utf8 …/_cii_hardcode9.py` → `tee _cii_hardcode9_out.txt` | CASE B：4 消费者全 `rc=0`；`_cii_checks --expect-merged rc=1 - INV-1 totals.plus_match=9 != recomputed=18`；CASE C 写回 18 → `OK violations=0` |
| 9 | `python -I -X utf8 -c '…两份 results[] 同 7 键 totals…'` → `tee _cii_manytoone_out.txt` | `7-key totals EQUAL = True`、`results[] EQUAL = False`、A `merged_present=False` / B `merged_present=True`（§4(c)） |
| 10 | `python -I -X utf8 lead/count_invariant_20261109/_ci_counterexamples.py`（上游 verbatim） | `ALL_ALERT = True COUNT = 10`（§6.2 复现上游 10 反例） |
| 11 | `grep -n -E "totals\|results\|cmp_" lead/r11_f2_fix_20261109/_f2w_*.py` | 4 件只取 `cmp_["results"]`，`totals` 0 命中（`:14,17,26` / `:13,17,20` / `:7,11,21-24` / `:31-33`） |
| 12 | `python -I -X utf8 -c '…9 件 hashlib 复验…'` → `tee _cii_readonly_out.txt` | 9 行 `UNCHANGED`，`ALL_PROTECTED_UNCHANGED = True` |

**本会话写域产出**（全部 `lead/count_invariant_20261109/`，前缀 `_cii_`）：
`COUNT_INVARIANTS.md`（本件）、`_cii_checks.py`、`_cii_counterexamples.py`、
`_cii_counterexamples_out.txt`、`_cii_identity_out.txt`、`_cii_delta_out.txt`、
`_cii_hardcode9.py`、`_cii_hardcode9_out.txt`、`_cii_manytoone_out.txt`、
`_cii_readonly_out.txt`、`_cii_pasted_gate.py`、`_cii_pasted_gate_out.txt`。
