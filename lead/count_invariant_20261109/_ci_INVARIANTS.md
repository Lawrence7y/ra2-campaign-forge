# _ci_INVARIANTS.md — 计数不变量 / 反例验证 / merged 判别式 / 回归门槛

> 任务：给一组能检出「巧合恒等掩盖维度缺失」的回归不变量。
> 写域 = `lead/count_invariant_20261109/`，前缀 `_ci_`。零真机、零采样代码、不 commit、不 push。
> 只读域全程未改（见 §6 复验）。Python 一律 `python -I -X utf8` + 绝对路径；指纹用 `hashlib`。

---

## 0 复核回件（绑定行，格式固定）

被核对象 SHA256 = 148ea8d689eaaf582af05ea1bf4650605e104d6d74f8c7765e75a6eec662c7b1，字节数 = 44958

被核对象 = `lead/r11_f2_fix_20261109/_f2_compare_out.json`（本任务第一被核对象）。
实跑命令：`python -I -X utf8 -c "import hashlib,pathlib; b=pathlib.Path(r'D:\Project\ra2-campaign-forge\lead\r11_f2_fix_20261109\_f2_compare_out.json').read_bytes(); print(hashlib.sha256(b).hexdigest(),len(b))"`
实跑输出：`148ea8d689eaaf582af05ea1bf4650605e104d6d74f8c7765e75a6eec662c7b1 44958`

**编排方 8 件指纹全等**（本会话 `hashlib` 实算，输出见 §6）：
`_f2_compare.py` 12e55acf…/4821、`_f2v_run.py` 75108dca…/3469、`_f2_compare_out.json` 148ea8d6…/44958、
`_f2_r11plus.py` 83f8217f…/15723、`_mk_CONTRACT_DESIGN.md` a968a17d…/56237、
`_re_linked.py` 7ca339c6…/19481、`PENDING_DECISIONS.md` 3765eddb…/52419、
`GOAL_THREE_TARGETS_20261018.md` 2baa0de4…/759518。另实算 `MERGED_MERGE_CONTRACT.md`
`2c4f60a76e1b4fe9d4b90a4ee705f6e15008d4673b515dcbe27c8e0f11205ad2`/64208。

---

## 1 第一步：复核巧合恒等（全部本会话实跑）

### (a) 值相等？是
`totals` 七键（`_f2_compare_out.json:2-10`）：
`{"bindings":19,"orig_path":1,"plus_path":9,"orig_match":0,"plus_match":9,"orig_problems":24,"plus_problems":23}`
`plus_path = 9 = plus_match`。30 件 `results[]` 共 19 条 `plus.bindings`。

### (b) 集合相同，不只是数字相同
实跑（逐条编址 `(results 下标 i, 该件 bindings 下标 k)`）：
```
plus_path SET size = 9
plus_match SET size = 9
SET EQUAL = True  symmetric diff = []
```
计入两个计数的**是同一批 9 条绑定**：

| (i,k) | 文件短名 | declared[:12] | path | tier | match |
|--:|:--|:--|:--|:--|:--|
| (3,0) | A_REDUCED_FORM.md | 28cd3794a571 | lead/a_dim_reduced_20261108/_ar_out.txt | T2N | True |
| (19,1) | INTEGRATION_REPORT.md | ca23c116064b | lead/b2b_isolated_20261107/qc151_trip.isolated.py | T3 | True |
| (27,3) | B_EXECUTION_SPEC.md | cb4f3011a75f | _n4_SPEC_N4_B2B_MATRIX.md | T2 | True |
| (29,0) | B_BREAKPOINT2_TRACE.md | 3aad3bddda08 | lead/r2_unclosed_b_20261108/B_BREAKPOINTS_2_6.md | T2 | True |
| (29,1) | B_BREAKPOINT2_TRACE.md | 7ce09812f7bd | lead/r2_final_grade_20261108/R2_FINAL_GRADE.md | T2 | True |
| (29,2) | B_BREAKPOINT2_TRACE.md | 4ee6a6b78d80 | lead/dtrigger_round2_20261107/_verify_B_out.txt | T2 | True |
| (29,3) | B_BREAKPOINT2_TRACE.md | 793e06d27845 | lead/b_unclosed_trace_20261108/_bt_B崩点2_尾串追溯_20261108.md | T2 | True |
| (29,4) | B_BREAKPOINT2_TRACE.md | 4a3424050125 | _dB_anchor_recompute_out.txt:18-19 | T1 | True |
| (29,5) | B_BREAKPOINT2_TRACE.md | 793e06d27845 | lead/b_unclosed_trace_20261108/_bt_B崩点2_尾串追溯_20261108.md | T2N | True |

其余 10 条一律 `path=None, match=None, tier=None`。crosstab：
`{(path=True,match=True):9, (path=False,match≠True):10}` —— 两个谓词在**每条绑定上逐点等价**，
文件级亦同（有任一 plus_path 的件 = 有任一 plus_match 的件 = 4）。

### (c) 为什么恰好相等：设计使然（不是本批语料巧合），但只对**现版本代码**成立
依据 `_f2_compare.py:65-71` 的聚合表达式：
- `:66/:67` `orig_path/plus_path += sum(1 for b in ... if b["path"] / b.get("path"))`
- `:68/:69` `orig_match/plus_match += sum(1 for b in ... if b["match"] is True / b.get("match") is True)`

再看 `_f2_r11plus.py` 如何写 `path`/`match`：
- `:196` 初始 `{"path": path, "match": None}`。
- **有 T1 path 分支** `:201-248`：成功 `:248` `match=True`；失配 `:209/:240` `match=False`；
  但 `:213-223` 的同行替代锚命中时 `:223` `match=True` —— 此时 `path` 仍是**原 T1 字符串**（真值），
  故仍 `path∧match`。现盘 `(29,4)` 正是此形态（`tier=T1`、`alt` 有、`recomputed` 无，实读确认）。
- **无 T1 path 分支** `:250-305`：any-match-wins 成功 `:267-272` 用
  `rec.update({"match":True,"path":verified["candidate"],...})` **同时写 path 与 match**；
  所有失败分支 `:276/:286/:293/:299` 都 `match=False` 且 `path` 保持 `None`；`:303-305` 只设
  `tier=None`（`path`/`match` 保持初值 `None`）。

⇒ 在**当前 r11_scan_plus** 里，`match is True` ⟺ `path` 真值，是控制流的结构性后果，
不是这 30 件语料碰巧。`_f2_compare.py:47-50` 还强制「原版采到 path 的绑定增强版必须仍采到」，
进一步锁死这个耦合。

**但它是「版本相关恒等」，不是维度律**：`_re_linked.py:320-329` 的 merged rec 明确
`path=None` + `match=True`（`:306-308` 注释：match 仅指声明 hex 与全体成员逐位一致）。
一旦接入该分支，`:67` 不计、`:69` 计 ⇒ 恒等立刻破。这恰是「缺一个维度」的意思：
现盘两个计数在**同一根轴**上（有无单一锚），`match` 没有独立的「匹配性质」自由度。

### (d) tier 分布 / 有无 SAMEDOC_LINK_EQ
实跑 `TIER COUNTS = {'T2N':2, None:10, 'T3':1, 'T2':5, 'T1':1} SUM = 19`；
`SAMEDOC_LINK_EQ count = 0`；`tier` 键在 19/19 条均显式存在。`None` 桶 = 10 条「无路径无匹配」。
⇒ **没有 merged**，也没有 `SAMEDOC_LINK`（unique）。这一 0 值是后续所有 merged 判别式的基线。

补充实跑：`RECOMPUTED == STORED = True`（按 `_f2_compare.py:65-71` 从 `results[]` 独立重算 7/7 全等）。

---

## 2 第二步：≥5 条可机检不变量（9 条），每条都有实跑反例

不变量实现：`lead/count_invariant_20261109/_ci_checks.py`（可粘贴代码见 §4(d)）。
反例构造与实跑：`lead/count_invariant_20261109/_ci_counterexamples.py`，输出
`lead/count_invariant_20261109/_ci_counterexamples_out.txt`。

**基线实跑**（证明「现在成立」）：
```
python -I -X utf8 D:/Project/ra2-campaign-forge/lead/count_invariant_20261109/_ci_checks.py D:/Project/ra2-campaign-forge/lead/r11_f2_fix_20261109/_f2_compare_out.json
FACTS: {"E_merged_tier":0,"M_match_no_path":0,"bindings":19,"match_true":9,"merged_present":false,
        "n_results":30,"path_and_match":9,"plus_match":9,"plus_path":9,"set_equal":true,
        "tiers":{"NONE":10,"T1":1,"T2":5,"T2N":2,"T3":1},...}
OK violations=0 (all invariants hold)   EXIT=0
```

**反例实跑**（证明「能被违反 / 会报警」）：
```
python -I -X utf8 .../lead/count_invariant_20261109/_ci_counterexamples.py
ALL_ALERT = True  COUNT = 10   EXIT=0
```

| # | 可机检等式/不等式 | 现在成立 | 违反它的构造输入（临时目录） | 实跑报警 | 防哪类维度缺失 |
|--:|:--|:--|:--|:--|:--|
| INV-01 | `totals[k] == recomputed[k]` ∀k∈7键（复刻 `:65-71`） | 7/7 全等 | CE-01：`totals.plus_match=8`，`results[]` 不动 | `INV-01 totals.plus_match=8 != recomputed=9` | **计数口径与明细脱钩**：硬编码/漏计/改口径后 totals 不跟 `results[]` 变 |
| INV-02 | `0 ≤ orig_path,plus_path,orig_match,plus_match ≤ bindings` ∧ `sum(len(orig.bindings)) == bindings` | 19/1/9/0/9 全满足 | CE-02：`totals.plus_path=20` | `INV-02 plus_path=20 > bindings=19` | 计数越界；分母维度（bindings）丢失 |
| INV-03 | `orig_path ≤ plus_path` ∧ `orig_match ≤ plus_match` | 1≤9, 0≤9 | CE-03：`totals.orig_path=12` | `INV-03 orig_path=12 > plus_path=9` | 覆盖单调性（`:47-50` 断言的聚合版）；增强版丢原版已采锚 |
| INV-04 | `orig_problems,plus_problems ∈ ℤ≥0` ∧ `len(problems)==0 ⟺ verdict=="PASS"` | 24/23，逐件一致 | CE-04：`plus_problems=-1` 且 `#0 plus.verdict="FAIL"` 而 problems=[] | `INV-04 plus_problems=-1 is negative/non-int` | 负数计数、verdict 与 problem 明细不同步 |
| INV-05 | `Σ_tier count == bindings` ∧ **每条 plus 绑定显式带 `tier` 键** ∧ tier∈白名单 | 2+10+1+5+1=19，19/19 有键 | CE-05：删 `(3,0)` 的 `tier` 键 | `INV-05 binding (3,0) missing explicit tier key` | **分类维度完备性**。★ 关键教训：只用 `b.get("tier")` 计数时，删键会被悄悄归进 `None` 桶、`Σ` 仍是 19 → 不报警。必须查键存在性 |
| INV-06 | `plus_path == plus_match`（**基线锁，非物理律**） | 9==9 | CE-06：把 1 条 `match=True` 改 False 并同步 totals | `INV-06 plus_path=9 != plus_match=8` | 检测「两个计数失去耦合」= merged/新维度到来的**触发器**；见第三步 |
| INV-07 | `M == E`，其中 `M=\|{¬path ∧ match=True}\|`，`E=\|{tier=="SAMEDOC_LINK_EQ"}\|`；且每条 merged 行有 `members`、无 `verified_path/recomputed/bytes` | M=0,E=0 | CE-07：构造 1 条 `path=None,match=True,tier="T2"` 带 `members` 但不打 merged 标 | `INV-07 M(match_no_path)=1 != E(merged_tier)=0` | **匹配性质维度缺失**：merged 语义存在却没有 merged 标记（正是本任务要防的那件事） |
| INV-08 | `plus_path==plus_match ⟹ P==S`（P=path 行集合，S=match 行集合） | 9==9 且 P==S | CE-08：把 `(3,0).match=False`、`(6,0).match=True`，totals 仍 9/9 | `INV-08 plus_path==plus_match numerically but SET differs: path\match=[(3,0)] match\path=[(6,0)]` | **数字相等掩盖集合不等**（本题核心风险的最直接一击）：一对对称错值让所有 totals 恒等式仍成立 |
| INV-09 | `schema_version≥2 ⟹ counting_policy 存在 ∧ plus_match_by_kind.{single_path,merged_eq} 存在 ∧ single_path+merged_eq==plus_match ∧ single_path==plus_path` | 现盘 sv=1，条件假，不触发 | CE-09：只加 `schema_version=2`；CE-09b：加 `by_kind={9,1}` 而 `plus_match=9` | `INV-09 …no counting_policy / no plus_match_by_kind`；`single_path+merged_eq=10 != plus_match=9` | 改口径后**新维度声明了却没落地/自相矛盾** |

每条都满足任务要求 (a) 等式/不等式 (b) 现在成立（基线 `violations=0`）(c) 有实跑报警反例
(d) 指明防的维度缺失。**反例全部落在 `tempfile.mkdtemp(prefix="_ci_ce_")` 临时目录**，不落既有写域。

---

## 3 第三步：merged 出现后哪些不变量必须改变（核心）

### (a) 恒等不再成立；预期变化 = 上一轮方案值
**本会话独立实跑投影**（`_ci_merged_projection.py`，用
`lead/merged_contract_20261109/_mk_r11plus_candidate.py` 替换 `r11_scan_plus`、
逐行复刻 `_f2_compare.py:35-71`、30 件全量对跑、只写临时目录）：
```
BEFORE: {"bindings":19,"orig_match":0,"orig_path":1,"orig_problems":24,"plus_match":9,"plus_path":9,"plus_problems":23}
AFTER : {"bindings":19,"orig_match":0,"orig_path":1,"orig_problems":24,"plus_match":18,"plus_path":17,"plus_problems":23}
DRIFT : {'plus_path': (9, 17), 'plus_match': (9, 18)}
changed_docs=5 changed_bindings=10
TIER AFTER: {'T2N':2, None:1, 'SAMEDOC_LINK':8, 'T3':1, 'SAMEDOC_LINK_EQ':1, 'T2':5, 'T1':1}
M (match_no_path) = 1   E (merged_tier) = 1   U (unique_tier) = 8
```
与 `MERGED_MERGE_CONTRACT.md:359`、`_mm_project_out.txt:2-5` 给出的 `9→17 / 9→18` 一致。
对这份投影跑 `_ci_checks.py`：
```
ALERT violations=1
  - INV-06 plus_path=17 != plus_match=18 (baseline identity broken; must reconcile with plus_match_by_kind)
```
⇒ **必须改变的只有 INV-06**：它从「基线恒等」降级为 `plus_path ≤ plus_match ∧
plus_match - plus_path == merged_eq`（或等价的分类恒等式）。
INV-01/02/03/04/05/08/09 在 merged 投影上**仍全部成立**（`violations=1` 仅 INV-06），
说明它们 captures 的是结构性约束、不是语料巧合。INV-07 从 `0==0` 变 `1==1` 且 `merged_present=true`。

### (b) 为什么 +8 与 +9；那个 1 是 merged
`changed_bindings=10`，分两类（`_mk_r11plus_candidate.py:345-361`、`_re_linked.py:310-329`）：

- **8 条 unique**（`tier="SAMEDOC_LINK"`、`:356-361` 写 `verified_path/recomputed/bytes`）：
  `_re_linked.py:314-319` 对 `verdict=="unique"` 设 `rec["path"]=reverify["path"]`、`rec["match"]=True`。
  ⇒ 每条贡献 `(plus_path +1, plus_match +1)`。
  另有 1 条从 `None` 变成 `multi/zero` 类（`tier=None, path=None, match=None`），贡献 `(0,0)`；
  `10 = 8 + 1(merged) + 1(零贡献)`。
- **1 条 merged**（`tier="SAMEDOC_LINK_EQ"`，来自
  `lead/b2b_isolated_20261107/_integ_INTEGRATION_REPORT.md`，`_mm_project_out.txt:9-14`
  `members_n=2 decl_lines=[13]`）：`_re_linked.py:320-329` **只**写
  `match=True`、`members`、`decl_lines`，`path` 保持 `None`，且 `:322-325` 明令
  「不写 `verified_path/recomputed/bytes`」。
  ⇒ 贡献 `(plus_path +0, plus_match +1)`。

合计：`plus_path 9+8+0 = 17`，`plus_match 9+8+1 = 18`。
**`18 - 17 = 1` 就是这一条 merged**：它是唯一「`match=True` 但没有单一 path」的绑定
（投影实跑 `M (match_no_path)=1`、`E (merged_tier)=1`）。
`_mm_project_out.txt:22` 亦直接记 `C5 _f2_compare.py:67/69 对 merged 单条 = (0,1)`。

### (c) 只看 `plus_match > plus_path` 能不能判 merged？**不能**
三层反证（全部本会话实跑）：

1. **非 merged 也能造出差**。实跑构造（把 1 条 `(path=None,match=None,tier=None)` 仅改成
   `match=True`，totals 同步为 10）：
   ```
   CONSTRUCTED: plus_path=9 plus_match=10  plus_match>plus_path=True
   M=1 E=0 merged_present=False
   ALERTS=2  - INV-06 ...  - INV-07 M=1 != E=0 => non-merged cause OR missing merged dimension
   ```
   即一个纯计数 bug / 谓词误写就能产生同样的 `+1` 差，语义上完全没有 merged。
2. **差可以反向**。实跑构造（把 1 条 `match=True` 改 False、保留 path）：
   `plus_path=9 plus_match=8  E=0` ⇒ `plus_path > plus_match`。代码面支持此形态：
   `_f2_r11plus.py:239-246`（T1 失配 `match=False` 但 `path` 仍真值）、`:276/:286/:293/:299`。
   ⇒ 差值符号不是 merged 的单向指标。
3. **差 1 不是「恰好一条 merged」的充分条件**。若同时漏计 2 条 unique 的 path 又多出 3 条
   merged，差仍可凑成 1；`plus_path`/`plus_match` 是两个标量，信息量不足以分解分类。
   尤其 `MERGED_MERGE_CONTRACT.md:147-148` 已指出 merged 与「失配但也有 0 path」在
   totals 里不可分辨。

⇒ `plus_match > plus_path` 只能作为**「恒等被打破」的触发器**（INV-06 的用途），
不能作为 merged 的**判别式**。它把「有新维度进来 / 有计数错」混为一谈。

### (d) 判别式：存在，但必须带正交维度；纯计数判别不存在

**纯 7 键计数集上不存在**「merged 出现 ⟺ 某等式」的判别式 —— 反证见 (c)1：存在两份
`results[]` 不同、但 7 键 `totals` 完全相同的输入，一份有 merged 一份没有
（差 1 可由非 merged 原因产生）。7 键是从 19 条绑定的二维布尔表压到 7 个标量的有损投影，
必然多对一。

**加上 `results[].plus.bindings[].tier` 后存在充分必要判别式**（本任务推荐，可机检）：

```
M := |{ b ∈ plus.bindings : not b.path and b.match is True }|          # 无单一锚却匹配
E := |{ b ∈ plus.bindings : b.tier == "SAMEDOC_LINK_EQ" }|             # merged 标记数
U := |{ b ∈ plus.bindings : b.tier == "SAMEDOC_LINK" and b.path }|     # unique 标记数

merged_present := (E > 0)
              ∧ (M == E)
              ∧ (∀ b with tier=="SAMEDOC_LINK_EQ":
                     b.path is None ∧ b.match is True
                   ∧ "members" in b ∧ len(b.members) >= 2
                   ∧ {"verified_path","recomputed","bytes"} ∩ keys(b) == ∅)
              ∧ (plus_match - plus_path == E)
              ∧ (plus_path == U + |{旧 T1/T2/T2N/T3 中 match=True 且 path 真值}|)
```
现盘：`E=0, M=0` ⇒ `merged_present=false`（基线实跑）；
merged 投影：`E=1, M=1, plus_match-plus_path=1` ⇒ `merged_present=true`（投影实跑）。
`_ci_checks.py` 的 `facts["merged_present"]` 实算 `(M>0 ∧ E>0 ∧ M==E)`，基线 `false`、
投影 `true`，两向都验过。

**「必然不成立」的那一半**要如实收窄：若 merged 存在却**不打 `tier` 标记**（维度彻底缺失，
CE-07 构造），`E=0`、`M=1`，判别式给 `false` —— 但此时 INV-07 报
`M != E`（`_ci_counterexamples_out.txt` CE-07 实跑）⇒ 报警说「要么有非 merged 原因、
要么维度缺失」，而不是静默判成「无 merged」。这就是能做到的最强保证：
**任何 merged 出现（无论标不标记）都会触发至少一条报警**；而「零报警」可严格推出
「无 merged 且无缺失维度」。语义标签本身必须由生产者写入，计数无法凭空造出来。

---

## 4 第四步：回归门槛

### (a) 改口径前后必查清单
| 阶段 | 必查不变量 | 期望 |
|:--|:--|:--|
| 改前基线 | INV-01..09（全部） | `violations=0`、`merged_present=false`、`set_equal=true`、`E=0` |
| 改口径（甲/乙/丙任一）后 | INV-01/02/03/04/05/**07**/08/**09** | 仍 `0`；INV-09 在 `schema_version≥2` 时强制生效 |
| 改口径后 | **INV-06 必须显式重定义**，不得原样保留 | 新恒等式 `plus_match == plus_path + merged_eq`（丙），或 `plus_by_kind` 三态和 == bindings |
| 接入 merged 后 | INV-07 | `M==E>0`、`merged_present=true`、merged 行形状合规 |
| 接入 merged 后 | 逐条 set 级 INV-08 | `plus_path==plus_match` 时集合必等；不等时差集必须恰为 merged 行 |
| 全程 | 独立重算（INV-01） | 永远以 `results[]` 为准，`totals` 不得当权威 |
| 全程 | 指纹锁 | 改口径必然 DRIFT，须重基线；但**不得把指纹锁当计数不变量**（见 4c） |

### (b) 怎么防「改了计数但恒等式仍成立所以测试误通过」（本次核心风险）
三条硬要求，缺一不可：

1. **断言源必须是 `results[]`，不是 `totals`**。INV-01 逐键复刻 `:65-71` 从明细重算。
   若测试写成 `assert totals["plus_path"] == totals["plus_match"]`，那么把两键一起硬编码成
   同一个错值（如都写 9）会**通过** —— 这正是「恒等掩盖一切」。
2. **用「成对对称错值」做变异测试（mutation test）**。必须有一条断言在
   `totals` 一个字节都没变的情况下报警：本任务 INV-08 就是。CE-08 实跑证明
   「`(3,0)` 关 match、`(6,0)` 开 match」后 `plus_path=9,plus_match=9` 全部 7 键恒等式
   （INV-01/02/03/06）仍成立，只有集合级 `P != S` 报警。⇒ 把 CE-08 列为回归必跑反例。
3. **加「维度存在性」断言而非只加恒等式**。INV-05 查 `tier` 键存在（CE-05 证明缺键时
   `Σ` 不变）、INV-09 查 `schema_version/counting_policy/plus_match_by_kind`。
   再加一条**反恒等哨兵**：若声明了 merged 维度，则
   `plus_match > plus_path` **必须**成立（否则 merged 被吞了）；反之若 `E==0`，
   则 `plus_match == plus_path` **必须**成立（否则有非 merged 原因或漏标）。
   即把「恒等」从默认状态改成**有条件、可证伪**的状态。

一句话：**不要让任何一条断言只看两个标量相不相等；每条不变量都要有一个「值不变但
输入已坏」的反例在 CI 里实跑。**

### (c) 故意改坏：`plus_match` 硬编码成 9，现有测试能不能发现？
实跑 `_ci_hardcode9.py`（输出 `_ci_hardcode9_out.txt`）：

**CASE B**：拿 merged 投影（真值 `plus_match=18`），把 `totals.plus_match` 硬编码为 `9`：
```
  _f2w_checks.py   rc=0  output_has_totals=False   sha 逐字一致条数 = 8
  _f2w_pass.py     rc=0  output_has_totals=False   R11 PASS: orig=6 plus=7 | overall PASS: orig=6 plus=7
  _f2w_extract.py  rc=0  output_has_totals=False
  _f2w_final.py    rc=0  output_has_totals=False
  --- _ci_checks.py 对 B ---
  ALERT violations=2
    - INV-01 totals.plus_match=9 != recomputed=18
    - INV-06 plus_path=17 != plus_match=9
```
⇒ **现有 4 个 JSON 消费者一个都发现不了**。依据：
`_f2w_checks.py:14,17,26`、`_f2w_extract.py:13,17,20`、`_f2w_pass.py:7,11,21-24`、
`_f2w_final.py:31-33` 全部只取 `cmp_["results"]`，`totals` 字样 0 命中（本会话实跑
`grep -n -E "totals|results|..."`，与 `MERGED_MERGE_CONTRACT.md:521`、编排方独立核实一致）。
`_f2_compare.py:100` 只写、`_f2v_run.py:71` 只写 totals，也不做自校验。

**CASE A**（baseline 副本硬编码 9，值恰好等于真值）：4 个消费者全部 `rc=0`；
三个指纹锁 `_f2d_fpcheck.py` / `_f2dw_fpcheck.py` / `_f2dv_fpcheck.py` 对**原件**实跑全部
`MATCH`（因为它们读的是原路径，副本不落原路径；见 `_ci_hardcode9_out.txt:8-11`）。
另实算：把 baseline 另存一份（indent 改为 1）即得
`sha256=5a7afc7a… / 39425 B`，硬编码指纹锁必然 `DRIFT` —— 但那是**字节变化检测器**，
合法的口径改写（甲/乙/丙皆然）也会 DRIFT，故它既会误报合法改动、又检测不出
「原路径上 totals 被改而指纹基线被一并更新」的情形。`MERGED_MERGE_CONTRACT.md:382`
亦记「一旦 `:100` 重写 JSON ⇒ MISMATCH/DRIFT」。

**缺什么检查**：
- 缺 INV-01（totals vs `results[]` 独立重算）—— 本会话 `_ci_checks.py` 对 CASE B `rc=1`、报
  `INV-01 totals.plus_match=9 != recomputed=18`，是**唯一**抓到它的断言；
- 缺 INV-06/07 的条件化版本（merged 时 `plus_match` 必须 > `plus_path` 且差 == E）；
- 缺「反例必须实跑」的 CI 门槛：现有测试全是正向断言，没有任何 mutation 用例。

### (d) 可粘贴回归代码片段

完整实现：`lead/count_invariant_20261109/_ci_checks.py`（`evaluate(doc) -> (violations, facts)`，
只读、不 import 项目模块、不写盘）。最小可粘贴门槛：

```python
# 粘贴到回归脚本；json_doc = json.loads(Path(json_path).read_text(encoding="utf-8"))
import json
from collections import Counter

def gate(json_doc, expect_merged=False):
    T, R = json_doc.get("totals", {}), json_doc.get("results", [])
    v = []
    rows = [(i, k, b) for i, r in enumerate(R)
            for k, b in enumerate(r.get("plus", {}).get("bindings", []))]
    # (1) totals 必须从 results[] 独立重算，绝不当权威  —— INV-01
    rec = dict(bindings=0, orig_path=0, plus_path=0, orig_match=0,
               plus_match=0, orig_problems=0, plus_problems=0)
    for r in R:
        ob, nb = r["orig"]["bindings"], r["plus"]["bindings"]
        rec["bindings"]      += len(ob)
        rec["orig_path"]     += sum(1 for b in ob if b["path"])
        rec["plus_path"]     += sum(1 for b in nb if b.get("path"))          # _f2_compare.py:67
        rec["orig_match"]    += sum(1 for b in ob if b["match"] is True)
        rec["plus_match"]    += sum(1 for b in nb if b.get("match") is True)  # _f2_compare.py:69
        rec["orig_problems"] += len(r["orig"]["problems"])
        rec["plus_problems"] += len(r["plus"]["problems"])
    for k in rec:
        if T.get(k) != rec[k]:
            v.append("INV-01 totals.%s=%r != recomputed=%r" % (k, T.get(k), rec[k]))
    # (2) 上界、单调、非负  —— INV-02/03/04
    for k in ("orig_path", "plus_path", "orig_match", "plus_match"):
        if not (0 <= T.get(k, -1) <= T.get("bindings", 0)):
            v.append("INV-02 %s out of [0,bindings]" % k)
    if T.get("orig_path", 0) > T.get("plus_path", 0) or \
       T.get("orig_match", 0) > T.get("plus_match", 0):
        v.append("INV-03 coverage not monotone")
    if any(T.get(k, -1) < 0 for k in ("orig_problems", "plus_problems")):
        v.append("INV-04 negative problems")
    # (3) tier 完备 + 键存在性（缺键会被 .get() 吞进 None 桶）  —— INV-05
    tiers = Counter("<ABSENT>" if "tier" not in b else b.get("tier") for _, _, b in rows)
    if sum(tiers.values()) != T.get("bindings") or tiers.get("<ABSENT>"):
        v.append("INV-05 tier partition incomplete %r" % dict(tiers))
    # (4) merged 判别：必须靠正交维度，不能只靠两个标量  —— INV-07
    M = sum(1 for _, _, b in rows if not b.get("path") and b.get("match") is True)
    E = sum(1 for _, _, b in rows if b.get("tier") == "SAMEDOC_LINK_EQ")
    if M != E:
        v.append("INV-07 M=%d != E=%d (non-merged cause OR missing merged dimension)" % (M, E))
    merged_present = (M > 0 and E > 0 and M == E)
    if merged_present != expect_merged:
        v.append("INV-07 merged_present=%r != expected=%r" % (merged_present, expect_merged))
    # (5) ★ 集合级：防「数字相等掩盖集合不等」  —— INV-08（本次核心风险）
    P = {(i, k) for i, k, b in rows if bool(b.get("path"))}
    S = {(i, k) for i, k, b in rows if b.get("match") is True}
    if T.get("plus_path") == T.get("plus_match") and P != S:
        v.append("INV-08 numeric equal but SET differs: %r / %r" % (sorted(P-S), sorted(S-P)))
    # (6) 条件化恒等：merged 时必须破恒等，不出现时必须守恒等  —— INV-06 重定义
    if expect_merged:
        if T.get("plus_match", 0) - T.get("plus_path", 0) != E:
            v.append("INV-06 plus_match-plus_path != merged_eq=%d" % E)
    elif T.get("plus_path") != T.get("plus_match"):
        v.append("INV-06 baseline identity broken without merged")
    # (7) 改口径后强制新维度  —— INV-09
    if json_doc.get("schema_version", T.get("schema_version", 1)) >= 2:
        k = T.get("plus_match_by_kind")
        if not k or k.get("single_path") != T.get("plus_path") or \
           k.get("single_path", 0) + k.get("merged_eq", 0) != T.get("plus_match"):
            v.append("INV-09 by_kind inconsistent with totals")
    return v

# CI 用法：
#   v = gate(json.loads(Path(p).read_text(encoding="utf-8")), expect_merged=False)
#   assert not v, "\n".join(v)
# 且 CI 必须同时跑 _ci_counterexamples.py：ALL_ALERT 为 True 才算门槛有效。
```

实跑记录：`_ci_checks.py` 对现盘 `violations=0`；对 merged 投影 `violations=1`（仅 INV-06，
符合「必须改变」）；对 10 个反例 `ALL_ALERT=True`。
独立封装 `_ci_gate.py` 实跑（`_ci_gate_out.txt`）：`--selftest` 三类输入
`SELFTEST_ALL_PASS = True`；对现盘 `OK violations=0`；
对 merged 投影加 `--expect-merged` 亦 `OK violations=0` —— 证明 INV-06 条件化重定义后，
同一套门槛在「无 merged」与「有 merged」两态都能通过，且对两类变异仍报警。

---

## 5 第五步：边界与建议

### (a) 这些不变量判不了什么（如实列）
1. **判不了语义正确**：`match=True` 是否真的对应正确的被核对象，只有逐字 SHA 比对能判；
   INV-01 只保证 totals 与 `results[]` 自洽。`_f2w_checks.py` 实跑
   `sha 逐字一致条数 = 8`（9 条 match 里 `(29,4)` 走 `alt`，无 `recomputed` 键，
   `:29` 判 `sha_ok=False`）—— 不变量完全看不出这件事。
2. **判不了 hash 是否被正确重算**：`recomputed/declared` 的一致性需独立 `hashlib` 复算
   （本任务只对保护件做了指纹复验，未重算 19 条绑定的对象哈希）。
3. **判不了 verdict 的业务正确性**：INV-04 只查 `problems[]` 与 `verdict` 的形式一致性，
   不查 R3-3a/3b/3c 判定是否该报。`MERGED_MERGE_CONTRACT.md:160` 已指出 merged
   `problems=[]` ⇒ `plus.verdict="PASS"`，不变量不会报警。
4. **判不了 tier 值的语义**（`T1/T2/T2N/T3` 采集是否恰当），只查完备性与白名单。
5. **判不了 30 件清单是否有代表性 / 是否漏件**：`n_results=30` 只是本批事实，非目标值。
6. **判不了 `members` 内容真实性**：INV-07 只查 `members` 键存在与 `len≥2`，不查两个成员的
   sha/bytes 是否真的相等。
7. **判不了「该有 merged 却没有」**：若谓词整体漏检 merged，M=E=0、全部不变量通过。
   这需要一个独立 oracle（如人工标注的 merged 清单）才能判。
8. **判不了跨文件一致**：`_f2v_run_out.json` 的 9 键 totals 是第二份产物
   （`_f2v_run.py:25,70-72`），本任务不变量只覆盖 `_f2_compare_out.json`；两者同步需另加断言。

### (b) 计数对了是否代表判定对了？**不代表**
计数是**投影**，判定是**语义**。本批正是反例：`plus_match=9` 计数自洽且 7 键全等，
但 `MERGED_MERGE_CONTRACT.md:143-148` 指出这 9 条既可能是 unique 单一回验，也可能是
merged 副本群 —— 计数无法区分，而「能否由该条推导单一对象授权结论」正是纪律二
（`_re_linked.py:30-33`）的核心。反过来 CASE B 实跑证明：把 `plus_match` 写成错的 9，
4 个消费者全部 `rc=0`、报告照出（`sha 逐字一致条数 = 8`、`R11 PASS: orig=6 plus=7`），
即**判定/统计看起来完全正常而计数已坏**。⇒ 计数自洽是必要非充分条件；
必须叠加 `results[]` 逐条证据键（INV-05/07/08/09）与独立 hashlib 复算才接近语义层。

### (c) 若模板所有者决定不引入新维度（保持现 7 键）的长期代价
1. **merged 永久不可分辨**：`plus_match` 会同时含 unique 与 merged
   （投影 18 = 17 unique + 1 merged），旧消费者 `_f2w_pass.py:17` 继续把 merged 计入
   「已回验」；`MERGED_MERGE_CONTRACT.md:372,380` 已记「merged 被计入已回验统计」、
   「门禁 `:160` 仍 PASS，1 条零单一锚定 merged 被静默放过」。
2. **恒等式是脆基线**：`plus_path==plus_match` 只因当前控制流成立（§1c）；
   任何一次谓词改动（新 tier、新 match 来源）都会破它，而没有分类键就无法判断
   「是 merged 来了」还是「计数写错了」—— 即本次的差 1 永远要人工考古。
3. **回归测试失去灵敏度**：CE-08 证明可以构造 7 键全等但集合已坏的输入；
   `grep` 实跑确认读 totals 的消费者 = 0，硬编码 9 无人发现（CASE B）。
   不变量只能退化为「totals vs results 重算」，防不了语义维度缺失。
4. **指纹锁与口径改动互相掣肘**：3 件 `_f2d*_fpcheck.py` 硬编码
   `148ea8d6…/44958`（`:11`/`:21-22`/`:26-27`），任何合法口径改写都 DRIFT，
   长期要么不改进、要么每次重基线并承担「合法改动与篡改不可分」的风险。
5. **第二份产物漂移无监控**：`_f2v_run_out.json` 9 键 totals 会随接入同步变
   （`_mm_project_out.txt:24` C7），两份口径不同键却无人对账。
6. **代价会复利**：每新增一种匹配形态（multi、zero、跨文档等价类）都会在
   `(plus_path, plus_match)` 平面上加一个新的不可分辨点；7 个标量无法承载 N 态分类，
   最终只能靠人读 `results[]` 逐条判。

建议（不作裁决）：采用 `MERGED_MERGE_CONTRACT.md:472-496` 的方案丙骨架，并把本文件
INV-01..09 + CE-01..09b 全部反例接进 CI；最低限度也要加 `plus_match_by_kind` 与
`schema_version`，否则 §5(c)1/3 两条无法缓解。

---

## 6 实跑命令与输出索引（本会话全部执行）

| # | 命令 | 输出 / 落点 |
|--:|:--|:--|
| 1 | `python -I -X utf8 -c "…hashlib…8 件 + MERGED_MERGE_CONTRACT.md…"` | 8 件全等编排方指纹；`MERGED_MERGE_CONTRACT.md` = 2c4f60a7…/64208 |
| 2 | `python -I -X utf8 -c "…读 _f2_compare_out.json 统计…"` | `SET EQUAL = True symmetric diff = []`；`TIER COUNTS={'T2N':2,None:10,'T3':1,'T2':5,'T1':1} SUM=19`；`SAMEDOC_LINK_EQ count=0`；`RECOMPUTED == STORED = True` |
| 3 | `python -I -X utf8 lead/f2d_rootcause_20261109/_f2d_fpcheck.py` | 9 件 `MATCH`，含 compare_out `148ea8d6…/44958` |
| 4 | `python -I -X utf8 lead/r11_f2_fix_20261109/_f2w_checks.py` / `_f2w_pass.py` / `_f2w_final.py` | `sha 逐字一致条数 = 8`；`R11 PASS: orig=6 plus=7`；六保护件 `UNCHANGED=True` |
| 5 | `grep -n -E "totals\|results\|..." 4 个 _f2w_*.py` | `totals` 0 命中，全用 `cmp_["results"]` |
| 6 | `python -I -X utf8 lead/count_invariant_20261109/_ci_checks.py <baseline>` | `OK violations=0 EXIT=0` |
| 7 | `python -I -X utf8 lead/count_invariant_20261109/_ci_counterexamples.py` | `ALL_ALERT = True COUNT = 10 EXIT=0`；落 `_ci_counterexamples_out.txt` |
| 8 | `python -I -X utf8 lead/count_invariant_20261109/_ci_merged_projection.py` | `(9,17)/(9,18)`、`M=1 E=1 U=8`；落 `_ci_merged_out.txt` |
| 9 | `python -I -X utf8 …/_ci_checks.py <临时 merged_projection.json>` | `ALERT violations=1` 仅 INV-06 |
| 10 | `python -I -X utf8 …/_ci_hardcode9.py` | CASE B：4 消费者全 `rc=0`；`_ci_checks` 报 INV-01+INV-06；落 `_ci_hardcode9_out.txt` |
| 11 | `python -I -X utf8 -c "…构造非 merged 的 plus_match>plus_path…"` | `plus_match>plus_path=True M=1 E=0 merged_present=False` |
| 12 | `python -I -X utf8 -c "…只读域 8 件指纹复验…"` | 8 件全 `UNCHANGED` |

**未验 / 如实声明**：
- 未重算 19 条绑定所指向对象的 SHA256（本任务只做计数不变量，见 §5(a)2）。
- 未跑 `_f2_compare.py` / `_f2v_run.py` 本体（纪律：不改、不重跑产物；投影用独立副本复刻 `:65-71`）。
- 未接入/修改任何门禁；`_g9_gate.py:155` 当前不可达，本任务未验证其改接 plus 后的行为
  （仅引用 `MERGED_MERGE_CONTRACT.md:380`、`_mm_project_out.txt:26` 的既有实跑）。
- 未验证方案甲/乙/丙各自落盘后的 totals（本任务只读方案件文字，未执行 `_mk_*` 写盘分支）。
- 零真机、零采样代码：全程未启动任何游戏进程、未写 hook/探针/内存解析。

**写域产出清单**（全部前缀 `_ci_`，仅此目录）：
`_ci_INVARIANTS.md`（本件）、`_ci_checks.py`、`_ci_counterexamples.py`、
`_ci_counterexamples_out.txt`、`_ci_merged_projection.py`、`_ci_merged_out.txt`、
`_ci_hardcode9.py`、`_ci_hardcode9_out.txt`、`_ci_gate.py`（可选封装，见下）、
`_ci_gate_out.txt`。
