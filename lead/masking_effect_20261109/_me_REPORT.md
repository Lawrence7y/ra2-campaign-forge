# 掩蔽效应审计与「可区分的通过」设计 — _me_REPORT.md

写域：`lead/masking_effect_20261109/`，全部产出前缀 `_me_`。
零真机、零采样代码、只读复核、不 commit / 不 push、Python 一律 `python -I -X utf8` + 绝对路径，指纹用 `hashlib`。
**未修改 `_rs_carrier_scan.py` 或任何既有脚本**；全部实验用本写域独立脚本。

## 0. 复核回件绑定行

被核对象 SHA256 = 9ccca808d52f44aaee895e30f9a84f6f3b6ae5ee292ea71281e2b46e627a1c57，字节数 = 16053

（被核对象 = `lead/refsync_scope_20261109/_rs_carrier_scan.py`；本会话开头与收尾各算一次 `hashlib.sha256`，两次一致；编排方给的同值。）
其余 7 件编排方指纹（`REFSYNC_SCOPE_FIX.md` / `_rs_CARRIER_MAP.md` / `_nn_REPORT.md` / `NEEDLE_NORMALIZATION.md` / `_ve_DRAFT_S609.md` / `PENDING_DECISIONS.md` / `GOAL_THREE_TARGETS_20261018.md`）逐件 sha256 + 字节数核对，8/8 一致；收尾复算仍 8/8 未变。

## 1. 第一步 复核掩蔽

### (a) 五个数字可复现 — 是

实跑：`python -I -X utf8 "D:/Project/ra2-campaign-forge/lead/masking_effect_20261109/_me_repro.py"`，输出 `_me_repro_summary.txt`。
该脚本用**未修改的上游扫描器**跑两次，参数为 `--include-refuting --max-depth 2 --ext .md`（这组参数由本会话 `sweep` 8 组组合实跑定位，见 `.tmp/_me_stage/sweep_*.txt`；`--ext .md --max-depth 2` 唯一给出 637/79/122）。

| 组 | EXIT | SELF_TEST | scanned files | carrier occurrences | :22 判定 |
|---|---|---|---|---|---|
| 单 needle | 1 | FAIL | 637 | 79 | `FAIL ... got=<not-scanned>` |
| 双 needle | 0 | PASS | 637 | 122 | `PASS ... got=REFUTING_QUOTE` |

与编排方给的五个数字**逐项一致**（`_me_repro_summary.txt:8-11` / `:16-19`；原始输出 `_me_repro_single_out.txt:10` / `_me_repro_double_out.txt:10`）。
注：本会话稍后并行任务新建了 `lead/chain_vs_single_20261109/_cs_BASELINE_ALIGNMENT_20261109.md`（mtime 14:18:40，49850 B，两 needle 均不命中），此后重跑 `scanned files` 变 638，**carrier occurrences 仍 79 / 122 不变**。语料漂移已如实登记，不掩盖。

### (b) :22 是否同时含两个 needle — **否**（需纠正一处表述）

`python -I -X utf8 .../_me_analyze.py` → `_me_analyze_out.txt:4-10`：

- 行长 711（与编排方 `len=711` 一致）。
- `N1 = 只能判「不可复现」` → `find = -1`（**不在行内**）。
- `N2 = 不能定位当年错误步骤` → `find = 172`（与编排方 `posN2=172` 一致）。
- 归一化变体 `只能判『不可复现』` → `find = 162`。
- 原文片段：`「只能判『不可复现』、不能定位当年错误步骤」`。

即：**`:22` 只含第二 needle；第一 needle 的直角引号 `「」`(U+300C/D) 与原文内层的弯引号 `『』`(U+300E/F) 不一致，逐字匹配失败**。编排方实跑给的 `hasN1=false, hasN2=true` 是正确的；ask 叙述里「:22 同时逐字包含第二个 needle」若理解为「含两个 needle」则不成立，此处按实跑数据纠正。
「三个行号的引号码位」：`_ve_DRAFT_S609.md:22` 内 `:111-124`(pos 110) / `:123`(pos 184) / `:138`(pos 367) / `:136`(pos 475) 等，均为 ASCII 冒号+数字，不构成 needle 匹配差异；标点码位实测含 `U+3001 U+3002 U+300C U+300D U+300E U+300F`，与编排方 `cjkPunctCodepoints` 一致。

### (c) 四道门机制（追到行号）

源码 `lead/refsync_scope_20261109/_rs_carrier_scan.py`：

| 门 | 行 | 原文 | 作用 |
|---|---|---|---|
| 门1 文件级 | :229 | `if not any(n in txt for n in a.needle): continue` | 整件无任一 needle ⇒ 整件跳过，`splitlines()`/`:232` 都不跑 |
| 门2 行级 | :165 | `pos = min((line.find(n) for n in needles if n in line), default=-1)` | 取命中 needle 的**最小位置**；全不命中 ⇒ -1 |
| 门3 角色前置 | :166-168 / :239 | `if pos < 0: return None` / `if not c: continue` | `None` ⇒ 该行**根本不进 `carriers`** |
| 门4 负控查表 | :327-331 / :346 | `role_of()` 在 `carriers` 里按 `(rel,line)` 找；找不到返回 `"<not-scanned>"` | 自检只查「在不在 carriers」，不查「哪根 needle 命中」 |

单 needle：`:22` 无 N1 ⇒ 门2 `pos=-1` ⇒ `:166-167 return None` ⇒ 门3 `continue` ⇒ 该行不在 `carriers` ⇒ 门4 `got=<not-scanned>`（**不是判错角色，是根本没被扫描**）。
双 needle：N2 在 pos 172 命中 ⇒ 门2 `pos=172` ⇒ `:168 q = quoted_containing(line,172)` 命中引号跨度 `(161,183,'「')`（`_me_analyze_out.txt:13,17`）⇒ `:173` `q and negs`（同行 `不再成立/过时/已定谳/自本节起/...` 11 个否定词）⇒ `role=REFUTING_QUOTE` ⇒ 门4 `PASS`。

**关键**：`REFUTING_QUOTE` 是由 N2 落在外层 `「」` 引号内这一事实判对的，与 N1 是否工作**无关**。N1 从未参与 :22 的判定。

**决定性反证**（本会话实跑）：`--needle "不能定位当年错误步骤" --needle "TOTALLY_BROKEN_NEEDLE_SENTINEL_XYZ"`（把 N1 换成保证零命中的坏串）→ `_me_broken_needle_out.txt`：`EXIT=0`、`SELF_TEST = PASS`、`carrier occurrences = 84`。即**一根 needle 完全坏掉，自检照样 6/6 PASS**。另 `--needle "不能定位当年错误步骤"` 单跑亦 `SELF_TEST = PASS`（`_me_n2only_out.txt`）——N2 一根就足以满足全部 6 条负控（`_me_analyze_out.txt:47-53` 给出每条负控的 `hit_set`：5 条为 `{N1,N2}`、:22 为 `{N2}`，因为其它 5 行同时含两串，N2 独立也能命中）。

### (d) 定性：**测试设计缺陷**，不是「脚本的正确行为」

- 脚本按它的规格工作：`any` 并集 + `min(pos)` + 负控查表，代码与文档 `_rs_carrier_scan.py:10-27,207-216,312-322` 一致，无实现 bug。
- 但「`SELF_TEST = PASS`」被当成「载体扫描口径已修正、6 条负控都覆盖」的证据交付（`REFSYNC_SCOPE_FIX.md:243,251`）。该 PASS 实际只证明「**N1∪N2 的并集**覆盖了这 6 个样本」，不证明「**每根 needle 独立工作**」。`:22` 的漏检被 N2 撞对掩盖。
- 区别：脚本正确 = 实现符合规格；测试有效 = PASS 能排除「某输入坏了」这一假设。此处规格本身把 k 个输入压成 1 bit（`ok` 布尔，`:324,:343,:346,:349`），**信息量不足以支撑「每根都工作」的结论**。按【铁律】「掩蔽不是眼下的 bug，是测试设计缺陷；即使结果碰巧正确也必须标为不可信」——判为测试设计缺陷，上一轮 PASS 不可信。

## 2. 第二步 量化掩蔽面

`_me_analyze_out.txt:21-45`，语料 = 扫描器同口径（`--root lead --ext .md --max-depth 2`，R2 行级 occurrence）。

| 量 | 值 |
|---|---|
| `\|U1\|` N1 命中行 | 79 |
| `\|U2\|` N2 命中行 | 84 |
| `\|only1\|` | 38 |
| `\|only2\|`（只被 N2 命中、不被 N1 命中） | **43** ← (a) |
| `\|both\|` | 41 |
| `\|union\|` | 122 |

交叉校验：`|U1|=79` = 扫描器单 needle `carrier occurrences`；`|union|=122` = 双 needle `carrier occurrences`（`_me_analyze_out.txt:35-38`，两项 `match=True`）。**差异 43 = |only2|**，即第二 needle 恰好补回 43 行。

(b) 相对双 needle 并集的漏检行数：**只用 N1 漏 43 行**（= only2）；**只用 N2 漏 38 行**（= only1）；**两个都用漏 0 行**（并集按定义完备）。命中集合直方图（`_me_analyze_out.txt:42-45`）：`{N2}` 43 行 / `{N1,N2}` 41 行 / `{N1}` 38 行。`:22 ∈ only2`（`:40`）。

**掩蔽量**：41 行（33.6%（41/122）被两根 needle 同时命中（`hit set` 势 ≥2），对这 41 行而言任一根失效都不会被扫描结果察觉；这正是「本次 PASS 里被掩蔽的行数」（`_me_design_out.txt:27`）。

(c) N 增到 3/4/N 是否更严重 — **是**（`_me_analyze_out.txt:74-85` 实跑）：

| N | union 行数 | 各 needle 命中行数 | 实际 hit-set 型 | 2^N−1 |
|---|---|---|---|---|
| 2 | 122 | [79, 84] | 3 | 3 |
| 3 | 122 | [79, 84, 4] | 4 | 7 |
| 4 | 125 | [79, 84, 4, 7] | 5 | 15 |

推演：
1. **并集单调不减**：`any()` 与 `min(find)` 对「是否进 carriers」是单调的，加 needle 只能增行不能减行（本次 122→122→125）。
2. **可归因性单调下降**：k 根 needle 的命中型有 2^k−1 种，而输出仍只有 6 条负控 + 1 个 `SELF_TEST` 布尔（`:332-346`），即**证明 1 bit，却要声称 k bit**。任一 needle 失效，只要它命中的行被别的 needle 也命中，就零信号。
3. **负控被「并集化」的概率上升**：本例 6 条负控中 5 条 `hit_set={N1,N2}`，只有 :22 是 `{N2}` 独占；正因为有 1 条独占负控，单 needle 才暴露 N1 的漏。若再加一根 needle 把这唯一独占行也变成共现，则 6/6 负控全部可由「任意一根活着的 needle」满足 ⇒ **完全不可分辨**。
4. **反向掩蔽概率上升**：见 (d)，每多一根 needle 就多一次 `min(pos)` 抢占机会。

(d) **反向掩蔽存在**，且与「扫不到」不同：

- 「加 needle 让本来能扫到的行变成扫不到」：**不可能**（门1 `any` / 门2 `min` 单调，`:229,:165`）。已实测：N=3 时 union 仍 122，未减少。
- 「加 needle 让本来判对的行变成判错 / 从修复清单消失」：**可能且已实跑复现**。机制：`:165` 取 `min(pos)`，`:168` 用该 pos 求 `quoted_containing`，`:173-182` 角色全依赖这个 `q`。新增 needle 若命中更靠前且落在引号内（或落在引号外），`q` 会改变。

真实语料 **端到端实跑（未修改扫描器）**：
`--needle "只能判「不可复现」" --needle "不能定位当年错误步骤" --needle "登记效力说明"` → `_me_reverse3_out.txt`：`EXIT=1`、`SELF_TEST = FAIL`、`FAIL ... :22 want=REFUTING_QUOTE got=ANALYSIS_MENTION`（`carrier occurrences = 122` 不变，行**仍在 carriers**，只是角色被改）。`登记效力说明` 在 :22 pos=17、在引号外，`min` 把 pos 从 172 拉到 17，`q` 变 `None` ⇒ 从 `REFUTING_QUOTE` 掉到 `ANALYSIS_MENTION`（`_me_analyze_out.txt:58-72`）。换成 `与既有草案`(pos=4) 同样 `FAIL`（`_me_reverse3b_out.txt`）。**即：加一根 needle 让原本 PASS 的自检变 FAIL，这是「反向掩蔽」的对称形态；若没有负控这条线，它会静默改判而不报错。**

更强构造（`_me_reverse_synthetic_out.txt:5-13`，用未修改的 `classify_line`）：
- `「核对」 只能判「不可复现」`：`[N]` → `ASSERTION`(pos=5, q=None)；`[N,'核对']` → `QUOTED`(pos=1, q=`「核对」`)。**`needs_fix: True → False`**，真载体从修复清单静默消失。
- `「逐字」 复算数字 只能判「不可复现」`：`ANALYSIS_MENTION → REFUTING_QUOTE`。
- 如实登记：真实语料 24 条 `ASSERTION` 行 × 9 个候选额外 needle 的搜索中**未观察到**该类翻转（`_me_reverse_assertion_out.txt:3` `flip count = 0`）；风险是构造验证成立、本语料未实证，不夸大。

结论：**「scanned」单调，「role / needs_fix」不单调**。多输入不仅掩盖漏检，还能主动制造改判。

## 3. 第三步 「可区分的通过」设计（核心产出）

### (a) 理想 PASS 的判据

一次 PASS 必须同时给出：
1. **逐输入结果**：每根 needle 一个 `PASS/FAIL`（k 行，不是 1 行）。
2. **每根 needle 的独立见证**：`exclusive(k) = U_k \ ∪_{j≠k} U_j` 非空，且至少有 1 条负控落在该独占集里；`|exclusive(k)| = 0` ⇒ 该 needle **不可独立验证**，整体必须 FAIL，不得报 PASS。
3. **命中溯源**：每个 carrier 行打印 `hits=[命中的 needle 下标]`，使「并集覆盖」与「逐根覆盖」可分开计算。
4. **合总规则**：`AGGREGATE = AND_k PASS_k`，且总 `SELF_TEST` 必须等于这个 AND，不得另起一个独立布尔。

### (b) 三个方案（均已在本写域实跑，可粘贴代码见 `_me_design.py` 的 `PLAN_A/B/C`）

**方案甲：逐 needle 独立跑自检**（`_me_design_out.txt:6-10`）
每根 needle 单独一次完整扫描，各出 `EXIT`/`SELF_TEST`，再 `AGGREGATE=AND`。实跑：
```
NEEDLE '只能判「不可复现」'      EXIT=1 SELF_TEST=FAIL | carrier occurrences = 79
NEEDLE '不能定位当年错误步骤'     EXIT=0 SELF_TEST=PASS | carrier occurrences = 84
AGGREGATE = FAIL ; per-needle = 1/2 PASS ; proven_bits = 2
```
故障注入（把 N1 换成 `BROKEN_SENTINEL_NO_HIT_XYZ`）→ `_me_faultinject_out.txt:1` `AGGREGATE = FAIL`，正确捕获。
优点：零改动上游脚本；缺点：k 次全量扫描（本例 k=2，637 文件 ×2）；对「某根 needle 只影响某个角色」不敏感（自检仍只看 6 条固定负控）。

**方案乙：每根 needle 的「只被它命中」行做负控**（`_me_design_out.txt:12-16`）
自动算 `exclusive(k)` 并设为覆盖度门禁，任一根 `exclusive=0` 即 `COVERAGE_GATE=FAIL` 且 `sys.exit(1)`：
```
NEEDLE '只能判「不可复现」'   |U|=79  |exclusive|=38
NEEDLE '不能定位当年错误步骤' |U|=84  |exclusive|=43
COVERAGE_GATE = PASS
```
故障注入 → `_me_faultinject_out.txt:2` `COVERAGE_GATE = FAIL`（EXIT=1），正确捕获。
比方案甲更强：直接针对「这根 needle 是否还有独占贡献」，且一次扫描即可。缺点：需要把 exclusive 负控**绑定到具体行号**（否则只是集合大小门禁，行被删了但计数凑巧不变仍可骗过）。

**方案丙（推荐）：命中溯源台账 + 覆盖度门禁**（`_me_design_out.txt:18-29`）
一次扫描，每个 carrier 补 `hits` 字段，输出 `HITSET` 直方图 + `EXCLUSIVE(k)` + `MASKED_LINES` + `PER_NEEDLE_SELFTEST`，PASS 只在 `every exclusive(k)>0 AND all controls pass` 时给出：
```
HITSET (0,)     -> 38 lines  exclusive
HITSET (0, 1)   -> 41 lines  <-- MASKED by union
HITSET (1,)     -> 43 lines  exclusive
TOTAL carrier lines = 122
EXCLUSIVE(needle[0]) = 38  OK
EXCLUSIVE(needle[1]) = 43  OK
MASKED_LINES = 41 / 122  (33.6%)
COVERAGE_GATE = PASS
PER_NEEDLE_SELFTEST = {0: 'PASS', 1: 'PASS'}
```
最优：一次运行、零额外扫描、直接回答 (d)，且天然扩展到 k 根（2^k−1 个 HITSET 型逐型打印）。另可加「**坏针注入自检**」：把每根 needle 依次换成一个保证零命中的哨兵串，要求 `|U|` 严格下降且对应负控 FAIL——本会话 `_me_broken_needle_out.txt` 已证明现行脚本**通不过**这条自检。

### (c) 改动量与输出格式破坏性

| 方案 | 对 `_rs_carrier_scan.py` 的改动 | 对外壳/新脚本 | 对既有输出格式 |
|---|---|---|---|
| 甲 | **0 行** | 新外壳 ~15 行（本写域 `_me_design.py` `PLAN_A`），跑 k 次 | **完全不破坏**：每次输出仍是原格式，只多一层汇总；既有 `_fix_*.txt` 解析不变 |
| 乙 | 0 行（若用外部脚本预计算 exclusive）；若内嵌需 ~20–30 行（新增 `hits` 计算 + exclusive 负控表 + 门禁） | ~25 行 | **弱破坏**：新增 `COVERAGE_GATE` / `PER_NEEDLE` 行，A–E 段不变；旧解析器按行首匹配可兼容 |
| 丙 | ~30–50 行：`:238` 处把 `classify_line` 结果补 `hits`；`:282` 附近多打一行 `hits=`；新增 `=== F. HITSET PROVENANCE ===` 段 + `COVERAGE_GATE` 并入 `ok`（`:324`） | 0（脚本内） | **中等破坏**：A 段每 carrier 多一行 `hits=`，新增 F 段；`SELF_TEST` 语义从「6 负控全过」扩为「负控全过 ∧ 每根有独占见证」，旧 PASS 可能变 FAIL（这正是目的） |
| 坏针注入 | 0 行（外部） | ~20 行 | 不破坏 |

数量级：甲 10 行级（零侵入）；乙 10–30 行级；丙 30–50 行级。三者都不需改 `:165/:229` 判定逻辑本身。

### (d) ★ 掩蔽检测判据（从输出直接看出「这次 PASS 里有几条被掩蔽」）

现行输出**做不到**：`_me_repro_double_out.txt` 的 E 段只有 6 条 `PASS ... want/got` + 1 行 `SELF_TEST = PASS`，**零条 per-needle 行、零个 hit-set 字段**，所以「有几根 needle 被掩蔽」在现行输出里**不可知（UNKNOWABLE）**——不是 0，也不是 1，是未报告（`_me_design_out.txt:31-35`）。这本身就是缺陷的证据。

建议的判据（可直接粘进扫描器输出）：
```
# 1) 每根 needle 的独占见证数；=0 即该针不可验证
EXCLUSIVE(k) = |{ line : hits(line) == {k} }|
# 2) 被掩蔽的行数（本次 PASS 里 "换掉某根针也看不出来" 的行）
MASKED_LINES = |{ line : |hits(line)| >= 2 }|
# 3) 被掩蔽的针数（最直接的答案）
MASKED_NEEDLES = |{ k : EXCLUSIVE(k) == 0 }|
# 4) 本次 PASS 的可信度上界
DISTINGUISHABLE_PASS = (SELF_TEST == PASS) AND (MASKED_NEEDLES == 0) AND (COVERAGE_GATE == PASS)
```
本例代入：`EXCLUSIVE = [38, 43]`、`MASKED_LINES = 41/122 (33.6%)`、`MASKED_NEEDLES = 0`、**但 `DISTINGUISHABLE_PASS = FALSE`**——因为现行 `SELF_TEST` 不是由 `AND_k` 算出来的，缺少 per-needle 结果，无法通过判据第 4 条。换言之：**结果碰巧对（N1 确实在别处命中了 79 行），这次 PASS 依然不可信**。

### (e) 可粘贴代码片段

完整三方案 + 判据实现在 `lead/masking_effect_20261109/_me_design.py`（`PLAN_A` / `PLAN_B` / `PLAN_C` 三字符串常量即为可直接独立运行的脚本，均由 `_me_design.py` 实跑验证）。最小可用片段（方案丙核心，约 12 行）：

```python
from collections import Counter
NEEDLES = ["只能判「不可复现」", "不能定位当年错误步骤"]
pat, excl, total = Counter(), Counter(), 0
for rel, txt in corpus():                 # 与扫描器同口径的 (文件, 行) 迭代
    for L in txt.splitlines():
        hs = tuple(i for i, n in enumerate(NEEDLES) if n in L)
        if not hs: continue
        total += 1; pat[hs] += 1
        if len(hs) == 1: excl[hs[0]] += 1
masked = total - sum(excl.values())
print("HITSET", dict(pat))
print("EXCLUSIVE", [excl[k] for k in range(len(NEEDLES))])
print("MASKED_LINES = %d / %d" % (masked, total))
print("MASKED_NEEDLES = %d" % sum(1 for k in range(len(NEEDLES)) if not excl[k]))
print("DISTINGUISHABLE_PASS = %s" % (all(excl[k] for k in range(len(NEEDLES))) and self_test_pass))
```

（方案甲/乙/丙全文见 `_me_design.py:PLAN_A/B/C`；故障注入验证见 `_me_faultinject_out.txt`。）

## 4. 第四步 其它「多参数/多输入」测试同类审计

### (a) 搜索命令与结果

实跑命令（本写域独立脚本）：
```
python -I -X utf8 "D:/Project/ra2-campaign-forge/lead/masking_effect_20261109/_me_search_git.py" > ".../_me_search_stdout.txt"
```
输出 `_me_search_out.txt`（819 行）。三条正则：`action="append"`/`--needle|--pattern|--keyword...`、`any(...for...)/min(...for...)`、`SELF_TEST|self.test|负控|negative.control`。
范围：`git ls-files`（3293 条）+ `lead/` 下深度≤3 的未跟踪扫描，universe 5847 条路径、实读 4962 个文本文件。**范围限制如实申报**：无界 `os.walk` 在 `lead/o1prime_reach_20261109/_o1_tmp/long_B3_longpath/`（超长路径树，ugrep 亦告警 `cannot open directory`）停滞，该树在跟踪集合内无 `.py/.md` 测试脚本；`_me_search.py`（无界版）与 `_me_search_scoped.py` 两次尝试分别超时/被停，已 `TaskStop`，结果以 `_me_search_git.py` 为准，不把受限扫描冒充全库。

结果摘要：
- A 段 `action=append` / needle 类 CLI 定义 **11 处**：`_rs_carrier_scan.py:194`、`ra2opt/cli.py:78,102`、`tools/atlas_apply_patches.py:140`、`tools/bench_diff.py:244-246`、`tools/verify_kit/boundary_scan.py:104`、`tools/verify_kit/snapshot.py:63` 等。
- B 段 多输入 `any()/min()` **194 处**；≥3 处的重灾脚本：`_v12_rule.py`(11)、`_n13v_independent.py`(7)、`_n4gv_refs.py`(6)、`tools/extract_hook_tables.py`(6)、`_c7a_independent.py`(3)、`_mhv_scan.py`(3)、`_mhv_verify.py`(3)、`_pf2_fp_scan.py`(3)。
- C 段 一行传 ≥2 个 needle-like 标志 **130 处**，绝大多数是本写域自身输出与文档转述；真实 CLI 多输入以 `--exclude` 类为主（`snapshot.py` / `boundary_scan.py` / `docs/re/dispatch/verify_card_template.md:45`）。
- D 段 提及自检/负控的文件 **492 个**（面很广，未逐个实跑，见 (b) 的「未验」声明）。

### (b) 逐个掩蔽风险清单

| 对象 | 行 | 形态 | 风险 | 依据 |
|---|---|---|---|---|
| `lead/refsync_scope_20261109/_rs_carrier_scan.py` | :165/:229/:325-346 | 双 needle 并集 + 1 布尔自检 | **已实证 HIGH** | 本会话 `_me_broken_needle_out.txt`；坏针仍 PASS |
| `lead/d27_ruling_20261106/check_d27.py` | :81-88, :100 | `any(keyword in body for ...)`，第 6 项 `("外推","卡顿不存在")` 二选一 OR | **HIGH 同类**：任一词失效，另一词命中即 `PASS` | 源码直读；`python -I -X utf8 -c` 最小复现：删掉「卡顿不存在」后 `any` 仍 True |
| `lead/d29_ruling_20261106/check_d29.py` | :76-89, :105 | `require_all=False` 时 `any(word in body for word in words)`，且 `if not any(matches)` 再取一次 OR | **HIGH 同类**（双层 OR） | 同上；词表 `("93.98","误报率")` / `("互斥","前提")` |
| `lead/d30_ruling_20261106/check_d30.py` | :76-89, :105 | 与 d29 同构 | **HIGH 同类** | 源码直读 |
| `lead/gate_pipeline_20261109/_gp_regression.py` | :137 | `"CATCH" if any(t in text for t in toks) else "PASS"`（naive 基线） | **MEDIUM**：多 token 并集，坏 token 无感；但它是**被比较的基线**，且:139-145 另有 r10/r12/n13/chain 对照 | 源码直读 + 搜索 B 段 |
| `lead/gate_fp7_20261108/_g7_predicates.py` | :98, :101 | `any(mk in span for mk in SELF_MARKERS)` | **MEDIUM**：多个 marker 并集判定「自指标记」，坏 marker 被其它 marker 掩盖；`_g7_patch.md:70,73` / `gate_false_positive_5_6_7.md:114,117` 同款 | 源码直读 |
| `lead/gate_n13_20261109/_n13v_independent.py` | :69, :73, :83-84, :91, :103, :109 | 6 组多 token `any()` 组合守卫 | **MEDIUM**：同类 OR 掩盖，且组合后语义随 min/位置可能变 | 源码直读 |
| `lead/gate_v1v2_20261109/_v12_rule.py` | :116-140 | 11 处 `any(k in U for k in ...)`，词表 `PROHIBIT/H1_QUESTION/H2_QUOTE/...` | **MEDIUM–HIGH**：词表最长，最易有死词 | 源码直读（本次未逐词做存活率实跑，标「未验」） |
| `tools/verify_kit/boundary_scan.py` | :104, :113, :143-151 | `--wordlist` 多 token；`for tok, rx in pats` 逐 token 记录 `HIT ... token=%s` | **LOW（相对最好）**：**有 per-token 溯源**（:145,:149 打印 `tok`）+ `--no-self-exclude` 作为正控开关（:108, 文件头 :11-14）⇒ 坏 token 可从「某 token 零 HIT」直接看出；但**无 per-token 覆盖度门禁**，词表里混进死串仍不会自动 FAIL | 源码直读 |
| `tools/verify_kit/snapshot.py` | :35-37, :63 | `--exclude action=append` + `any(c in pat for c in "*?[")` | **LOW–MEDIUM**：多 pattern 并集（跳过更多文件），坏 pattern 会让快照少排除文件但仍成功；有 `snapshot: %d files` 计数可间接察觉 | 源码直读 |
| `ra2opt/cli.py` | :78, :102 | `--exe action=append` | **LOW**：多 exe 路径，非自检/非判定门禁 | 搜索 A 段 |
| `tools/atlas_apply_patches.py` | :140 | 单个 `--pattern` 默认 `R*.md` | **LOW**：非多输入 | 搜索 A 段 |

**未验声明**：D 段 492 个提及自检/负控的文件、B 段 194 处 `any()` 未逐个实跑；上表只对我直读了源码或做了最小复现的对象给判断，其余标「未验」，不补造。

### (c) 通用形态（抽象）

> 设测试有 k 个输入（needle / pattern / keyword / token / case），内部用**存在量词**把它们合成一个布尔：
> `covered(x) = ∃i: match(input_i, x)`，而自检把 `∀ sample s: covered(s)` 压成**单一比特** `PASS`。
> 于是 `PASS` 的所有可能世界中，包含「`input_1` 完全失效、但每个 sample 都被某个 `input_{j≠1}` 命中」这一世界，且与「全部 k 根正常」**观测等价**。
> 缺陷不在 `match` 实现，而在**从 k 个输入到 1 个布尔的有损压缩**：证明目标（∀i 有效）强于观测量（∃i 命中），且没有保留 `i` 的溯源。
> 两个附加形态：① **min/argmin 位置依赖**——若判定还依赖 `argmin_i pos_i`（本例 `:165`），加输入会改变 `argmin`，使「已扫到」的集合单调而「已判对」的集合不单调（反向掩蔽）；② **无独占见证**——若 `exclusive(i) = U_i \ ∪_{j≠i} U_j = ∅`，该输入在原理上不可独立验证，任何并集式 PASS 都无意义。

### (d) 一般性防掩蔽设计原则

1. **逐输入出结果**：输出 k 行 `input_i: PASS/FAIL`，总判定 = `AND_i`，禁止把并集结果直接叫 PASS。
2. **独占见证门禁**：要求每根输入至少 1 条 `exclusive` 负控；`exclusive(i)=0` ⇒ 显式报 `UNPROVEN` 并整体 FAIL（不可跳过）。
3. **保留溯源**：每个命中记录 `hits=[...]`，使 `HITSET` 直方图可直接算出 `MASKED_LINES` / `MASKED_NEEDLES`。
4. **坏输入注入自检**：把每根输入依次替换为保证零命中的哨兵，要求**扫描计数严格下降且对应负控 FAIL**；本例现行脚本通不过（已实证）。
5. **OR 改 AND 或改枚举**：词表型检查（`check_d27/d29/d30`）把 `any(word...)` 改为逐词报告命中数，`require_all=False` 也要打印每个词的存活状态。
6. **单调性声明**：明确区分「scanned 单调」与「role/needs_fix 非单调」；对依赖 `min(pos)` 的判定，改为对每根 needle **独立求角色**再按明确规则合并，而不是先取 `min` 再判一次。
7. **固定语料指纹**：报 PASS/FAIL 时绑定语料 SHA256 + 文件数，防止并行写入造成 `scanned files` 漂移被误读为「测试变好」（本会话亲历 637→638）。

## 5. 第五步 事件定性与后续建议

### (a) 上一轮 `SELF_TEST = PASS` 定性 — **不可信**

理由：
1. 实测 `--needle "不能定位当年错误步骤" --needle "TOTALLY_BROKEN_NEEDLE_SENTINEL_XYZ"` 仍 `EXIT=0` / `SELF_TEST = PASS`（`_me_broken_needle_out.txt`）⇒ 该 PASS 与「N1 是否工作」逻辑无关。
2. 6 条负控里 5 条 `hit_set={N1,N2}`、1 条 `{N2}`（`_me_analyze_out.txt:47-53`），N2 一根即可 6/6（`_me_n2only_out.txt`）。
3. 而 N1 的实际缺陷（直角/弯引号不归一）客观存在：单 needle 下 `:22 got=<not-scanned>`、`carrier occurrences` 79 vs 122，漏 43 行。
4. 按【铁律】：「若某处通过是被掩蔽的，即使结果碰巧正确，也必须标为不可信」。此处 N1 在别处确实命中 79 行（结果碰巧部分正确），但 :22 的通过纯由 N2 撞对 ⇒ **不可信**，不是「部分可信」。

### (b) 上一轮交付件是否需加注 — **建议加注，本任务不执行**

- `lead/refsync_scope_20261109/REFSYNC_SCOPE_FIX.md:243`（R6 描述）、`:251`（登记的双 needle 命令 + `SELF_TEST = PASS 6/6`）、`:252-253`（另两条 PASS 登记）：建议由台账所有者追加一条限定——「本 PASS 系 N1∪N2 并集口径，不构成逐 needle 有效性证据；`:22` 仅由第二 needle 命中，直角引号 needle 未覆盖该行；详见 `lead/masking_effect_20261109/_me_REPORT.md`」。
- `lead/refsync_scope_20261109/_fix_d2_out.txt` 等在盘输出：建议在句首加「口径限定」，不改写原始数字。
- 已有的 `lead/needle_norm_20261109/_nn_REPORT.md:90-100,365,400-402` 与 `NEEDLE_NORMALIZATION.md:91,293,364,393` **已经登记了「掩盖效应」并给出「每个 needle 单独跑一次自检」的建议**——即下一轮已发现，但**上一轮交付件本身未加注**，且 `REFSYNC_SCOPE_FIX.md` 全文搜不到「掩盖/假 PASS」（本会话直读确认，只有 :71 一处无关「关键词」字样）。建议补的是这个缺口。

### (c) 方法论问题 + 对编排方验证命令的如实评估

**暴露的方法论问题**：把「多输入并集 + 单一布尔自检」当成「每个输入都有效」的证明；负控样本未做**逐输入覆盖度**设计；PASS 未绑定语料指纹；命令口径（单 vs 双 needle）与交付登记不一致却未标注，导致同一脚本给出相反结论而无人察觉。

**编排方「只跑单 needle 就报 FAIL」算不算另一种偏差 — 算，但性质不同，且不抵消原问题**：
- 它是**口径偏差 / 非登记命令偏差**：`REFSYNC_SCOPE_FIX.md:251` 登记的正式命令是双 needle，编排方实跑的是单 needle（`--needle "只能判「不可复现」" --include-refuting`），两者只差一个 `--needle`。按「报 FAIL 前必须确认与登记口径一致」，这个 FAIL **不能直接当作交付件的验收结论**，应写作「在单 needle 口径下 FAIL」。
- 它**不是掩蔽**（没有用另一个输入掩盖失败），而是**反向的口径错配**：用非交付口径去判交付件。
- 但它**碰巧是唯一发现通道**：`_nn_REPORT.md:402` 自己登记「本次 FAIL 之所以暴露，是编排方用单 needle 重跑了负控」。如实评价：**结论方向对（N1 确有漏检），论证路径不严谨（口径与登记不符）**；若无本任务的双/单对照 + 坏针注入，单靠那一条 FAIL 无法区分「N1 坏了」与「我少传了一个参数」。
- 反过来说，编排方这次「跑错了口径」反而暴露了掩蔽，这本身说明**正式口径的自检设计失效**——这正是本任务要修的东西。不护同僚，也不过度自责：两边都有缺陷，缺陷类型不同。

### (d) 「以后报 PASS/FAIL 前必须做什么」清单

1. **核对命令与登记口径逐字一致**（含每个 `--needle` / `--pattern` / `--ext` / `--max-depth`），不一致就标明「非登记口径」，不得据此下交付结论。
2. **绑定被核对象 SHA256 + 字节数 + 语料文件数**（本回件第 0 节格式），PASS/FAIL 与指纹同发。
3. **逐输入跑一遍**：k 个输入出 k 个 `PASS/FAIL`，总判定 = `AND`，禁止只报一个 `SELF_TEST`。
4. **查独占见证**：`EXCLUSIVE(i)>0` 对每根输入成立；否则报 `UNPROVEN` 并整体 FAIL。
5. **打印命中溯源**：`hits=[...]` / `HITSET` 直方图，算出 `MASKED_LINES` 与 `MASKED_NEEDLES`。
6. **做坏输入注入**：每根输入依次换成哨兵，确认计数严格下降 + 对应负控 FAIL；若注入坏针仍 PASS，则原 PASS 作废。
7. **跑 PASS/FAIL 双向对照**：既报正式口径，也报去掉一根输入的对照口径，两者差异必须可解释（本例 79 vs 122，差 43 = |only2|）。
8. **登记输出全文**：原始 stdout 落盘并算 SHA256，正文只引用「命令 + 输出文件:行」，不得凭记忆写数字。
9. **检查单调性声明**：若判定依赖 `min(pos)`/argmin，额外跑「多加一根输入」的对照，确认角色未被改判（本例 `:22` 实测被改判为 `ANALYSIS_MENTION`）。
10. **未验项显式写「未验」**：搜不全、跑不动、没实跑的对象一律标注，不用 plausible 值填空（本任务已对 492 个自检文件、长路径树、真实语料反向翻转数如实标注）。

## 6. 本会话实跑命令清单（可复核）

| # | 命令 | 输出 |
|---|---|---|
| 1 | `python -I -X utf8 -c "...sha256 8 件..."` | 8/8 与编排方指纹一致（开头 + 收尾各一次） |
| 2 | `python -I -X utf8 ".../_me_repro.py"` | `_me_repro_summary.txt` / `_me_repro_{single,double}_out.txt` → 五数字复现 |
| 3 | 8 组参数 sweep（`--ext` × `--max-depth` × 单/双 needle） | `.tmp/_me_stage/sweep_*.txt` → 定位 637/79/122 口径 |
| 4 | `python -I -X utf8 ".../_me_analyze.py"` | `_me_analyze_out.txt` → 行集量化 / 四门追踪 / N=2,3,4 / 反向掩蔽构造 |
| 5 | 未修改扫描器 `--needle N1 --needle N2 --needle "登记效力说明"` | `_me_reverse3_out.txt` → `EXIT=1`，`:22 got=ANALYSIS_MENTION` |
| 6 | 同上第三针换 `与既有草案` | `_me_reverse3b_out.txt` → 同结果 |
| 7 | 未修改扫描器 `--needle N2 --needle TOTALLY_BROKEN_NEEDLE_SENTINEL_XYZ` | `_me_broken_needle_out.txt` → **`SELF_TEST = PASS`** |
| 8 | 未修改扫描器单 N2 / 单 N1 | `_me_n2only_out.txt`(PASS) / `_me_n1only_out.txt`(FAIL) |
| 9 | `python -I -X utf8 ".../_me_design.py"` | `_me_design_out.txt` → 甲乙丙三方案实跑 + 掩蔽判据 |
| 10 | 故障注入（把 N1 换成哨兵后跑甲/乙） | `_me_faultinject_out.txt` → 两方案均 EXIT=1 捕获 |
| 11 | `python -I -X utf8 ".../_me_reverse_assertion.py"` | `_me_reverse_assertion_out.txt` → 真实语料 flip count = 0（如实阴性） |
| 12 | `python -I -X utf8 ".../_me_reverse_synthetic.py"` | `_me_reverse_synthetic_out.txt` → 构造 `ASSERTION → QUOTED` 翻转 |
| 13 | `python -I -X utf8 ".../_me_search_git.py"` | `_me_search_out.txt`（819 行）→ 全库多输入测试清单 |
| 14 | `python -I -X utf8 -c "...check_d29 OR-gate..."` | 最小复现：删掉一个关键词后 `any` 仍 True |
| 15 | 收尾 `python -I -X utf8 -c "...sha256 8 件..."` | 8/8 未变（绝对只读件零改动） |

零真机：未启动 `gamemd.exe` / `ra2loader` / `YURI.exe`，未 `taskkill`，未读活进程内存。
零采样代码：未写 hook / MiniDump / SuspendThread / StackWalk / 探针注入 / 动态内存解析。
绝对只读件零改动（收尾 hashlib 复核 8/8）。唯一写域 `lead/masking_effect_20261109/`，前缀 `_me_`。未 commit / 未 push。
