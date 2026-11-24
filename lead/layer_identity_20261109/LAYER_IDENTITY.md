# LAYER_IDENTITY.md — 层恒等复核、性质判定与「层数」结论影响评估

> 本件**只做证明与影响评估**：未改任何脚本、语料、产物、台账；七个只读目录与两件台账一字未动。
> 唯一写域 `lead/layer_identity_20261109/`；零真机、零采样代码、不 commit / 不 push。
> Python 一律 `python -I -X utf8 -c`（或 `-I -X utf8 <绝对路径脚本>`）+ 绝对路径；指纹用 `hashlib.sha256`。
> 引用只追到「本次会话实跑命令 + 输出」或「文件:行」；拿不到的一律写**未验**。
> 上游被核对象 = `lead/layer_identity_20261109/_li_LAYER_IDENTITY_PROOF_20261109.md`（下称「前件」），其【复核】`verdict = partial`，按交付规则标 **`unconfirmed`**（见 §6.0）。

---

## 1 目的与边界

**目的**：判定「`{三层全 PASS}` 与 `{r10&r13 双 PASS}` 逐 id 相等、`P(r12=PASS|n13=PASS)=38/38=1`」这一恒等，究竟是**逻辑必然**还是**本批语料 + 输入契约的巧合**；据此逐处评估它对一切「层数」结论的影响，澄清「证据根 / 层 / k_eff」三种量纲，并给出「三层」的**精确表述**、置信度宣称修正清单与报层数准则。

**边界**（铁律，逐条遵守并实跑核验，见 §6.5）：
- 零真机：不启 `gamemd.exe` / `ra2loader` / `YURI.exe`，不 `taskkill`，不读活进程内存。
- 零采样代码：不写 hook / MiniDump / SuspendThread / StackWalk / 探针注入 / 动态内存解析。
- 绝对只读：`lead/metric_audit_20261109/`、`lead/keff_calc_20261109/`、`lead/evidence_indep_20261109/`、`lead/score_decomp_20261109/`、`lead/pvalue_recalc_20261109/`、`lead/gate_pipeline_20261109/`、`lead/chain_vs_single_20261109/`、两件台账 —— 一律不修改、不追加、不覆盖（本次会话两次 10 件指纹重算全等，见 §2.1 / §6.4）。
- **★★ 只做证明与影响评估，不改任何脚本、语料、产物**：本次会话未对任何既有件执行写入；唯一新建件即本 `LAYER_IDENTITY.md`（写域内）。前件与其复核脚本 `_liv_verify.py` 是上游既有件，只读加载、未改。
- 不 commit、不 push（`git log -1 = 2657458` 未变，见 §6.5）。

**要害**：恒等性必须在**逻辑上**成立，不能只在 74 行样本上成立。本次会话的判定是「**不是逻辑必然，是巧合**」，并且**前件自身的论证里还残留一处把巧合说成必然**（见 §3.1 修正①，来自【复核】并已独立复现）—— 这一区别是本任务的核心。

---

## 2 上游指纹（十件）+ 恒等复核

### 2.1 十件上游指纹（本次会话 `hashlib` 现盘重算，逐行全等编排方基线）

实跑命令（要点）：`python -I -X utf8 -c "<10 件 read_bytes + hashlib.sha256 + len + 对照编排方基线>"`；输出 `ALL_10_MATCH = True`，逐行 `OK`。逐件值（完整 64 位 + 字节数）见 §6.1 绑定行；此处列路径与结果：

| # | 文件 | SHA256（前 12 位） | 字节数 | 本次结果 |
|---|---|---|---|---|
| 1 | `lead/metric_audit_20261109/METRIC_CONVENTION_AUDIT.md` | `f737d8a52b51…` | 45362 | OK |
| 2 | `lead/metric_audit_20261109/_ma_verify_out.txt` | `18818d765c93…` | 6360 | OK |
| 3 | `lead/keff_calc_20261109/KEFF_CALC.md` | `4ad16cdb7dbb…` | 34964 | OK |
| 4 | `lead/evidence_indep_20261109/EVIDENCE_INDEPENDENCE.md` | `aeab4fc30822…` | 36194 | OK |
| 5 | `lead/score_decomp_20261109/SCORE_DECOMP.md` | `dfe7f68692eb…` | 42573 | OK |
| 6 | `lead/pvalue_recalc_20261109/_pv_PVALUE_RECALC.md` | `277df9910d46…` | 29780 | OK |
| 7 | `lead/gate_pipeline_20261109/_gp_regression_out.json` | `d3543657aa4f…` | 38575 | OK |
| 8 | `lead/chain_vs_single_20261109/CHAIN_VS_SINGLE.md` | `efde3e8e1308…` | 39558 | OK |
| 9 | `lead/PENDING_DECISIONS.md` | `3765eddbe96d…` | 52419 | OK |
| 10 | `lead/GOAL_THREE_TARGETS_20261018.md` | `2baa0de45d41…` | 759518 | OK |

补充指纹（非十件、供源码引据绑定，本次会话实跑）：
- 前件 `_li_LAYER_IDENTITY_PROOF_20261109.md`：`13453a000c61cb211c51931cc8a7bd3d1912a9e1714d46cb8be349686fe9c957`，47501 字节 = 【复核】`sha256Line` 全等；`len(splitlines())=400`（【复核】记 400 行属实，前件 `what` 自报「396 行」不准，见 §6.0）。
- `lead/evidence_indep_20261109/_ei_n13_predicates_src.py`：`e1195b3b220ad97b5b91b8746a24e332b02ce28085452e947554f99b7f2f3079`，16649 字节；`lead/gate_fp7_20261108/_g7_predicates.py`：`02c17e49764a6f87f2b0d26c6689f0cbeb96498509e5c75bf843104829c51120`，11743 字节。`_liv_verify.py:33-37` 实跑另证 N13 只读副本与生产件 `_n13_predicates.py` 逐字节相同（`production == read-only copy bytes ? True`）。

### 2.2 两集合逐 id 比对（本次会话实跑，数据源 `lead/gate_pipeline_20261109/_gp_regression_out.json:rows`，74 行）

实跑命令：`python -I -X utf8 -c "<读 rows；A={r10=PASS&r12=PASS&n13=PASS}；B={r10=PASS&n13=PASS}；逐 id 比对>"`。
输出：`A_n 18 B_n 18 A==B True only_A [] only_B []`；字段定义见 `lead/gate_pipeline_20261109/_gp_regression.py:157-181`（`row` 写 `id/…/r10/r12/n13/chain`）。

**18 个 id 逐个对齐全等**（下表 `inA / inB / equal` 三列逐行 `True`；本次会话 `python -I -X utf8 -c "<逐 id 打印>"` 输出 18 行，`union ids n= 18`、`A-only []`、`B-only []`）：

| id | expect | r10 r12 n13 | inA inB | equal |
|---|---|---|---|---|
| N13-P08 | PASS | PASS PASS PASS | True True | True |
| N13-P09 | PASS | PASS PASS PASS | True True | True |
| N13-P10 | PASS | PASS PASS PASS | True True | True |
| N13-P13 | PASS | PASS PASS PASS | True True | True |
| R10-REAL-CANDIDATE_RESIGN_YES_V2 | PASS | PASS PASS PASS | True True | True |
| R10-REAL-LEDGER_APPENDIX_DRAFT | PASS | PASS PASS PASS | True True | True |
| R10-REAL-OBSERVATION_PROTOCOL_SPEC | PASS | PASS PASS PASS | True True | True |
| R10-REAL-C97_SCOPE_RECHECK | PASS | PASS PASS PASS | True True | True |
| R10-CTX-01 | PASS | PASS PASS PASS | True True | True |
| R10-CTX-02 | PASS | PASS PASS PASS | True True | True |
| R10-CTX-03 | PASS | PASS PASS PASS | True True | True |
| R10-CTX-04 | PASS | PASS PASS PASS | True True | True |
| GP-C05 | PASS | PASS PASS PASS | True True | True |
| GP-C06 | PASS | PASS PASS PASS | True True | True |
| GP-C07 | PASS | PASS PASS PASS | True True | True |
| GP-A1 | CATCH | PASS PASS PASS | True True | True |
| GP-A2 | CATCH | PASS PASS PASS | True True | True |
| GP-A3 | CATCH | PASS PASS PASS | True True | True |

`expect=CATCH` 恰 3 行 = `GP-A1/A2/A3`（本次会话实跑；`lead/metric_audit_20261109/_ma_verify_out.txt:15` 同值）。**编排方 `(a)` 成立**。

### 2.3 `P(r12=PASS|n13=PASS)` 分子分母 + 列联表

实跑命令：`python -I -X utf8 -c "<读 rows；分母/分子/列联表/比值>"`。
输出：`P(r12=P|n13=P) den 38 num 38 ratio 1`、`cells_n13P_r12CATCH []`。

- **分母 = 38**：全 74 行里 `n13=PASS` 的行数（不是 39、不是 74、不是 35）。
- **分子 = 38**：其中 `r12=PASS` 的行数；`r12=CATCH` 0 行 ⇒ `38/38 = 1`。
- 全 74 行列联表（本次会话实跑）：`n13=PASS & r12=PASS : 38`、`n13=PASS & r12=CATCH : 0`、`n13=CATCH & r12=PASS : 32`、`n13=CATCH & r12=CATCH : 4`。空的是 `n13=PASS & r12=CATCH` 格。
- **另一格也是 0 且是巧合**：`r10=CATCH & n13=PASS & r12=CATCH` 计数 = 0（本次会话实跑）。它在 74 行上恰好为空，才让「集合恒等」与「`P(r12=PASS|n13=PASS)=1`」看起来等价；逻辑上二者并不等价（见 §3.1 修正①，这是【复核】点名的要害）。
- 在 `E = expect=CATCH`（39 行）上（本次会话实跑）：`q_r10=19/39`、`q_r12=35/39`、`q_n13=3/39=1/13`；`n13=PASS` 仅 3 行（`GP-A1/A2/A3`），且三层全 PASS 也是这 3 行 ⇒ `P(all3PASS|E)=3/39=1/13`。`q_r12=35/39` 分解为 `n13=PASS&r12=PASS : 3` + `n13=CATCH&r12=PASS : 32`（本次会话实跑）—— 即 `q_r12` 的数值绝大部分来自与 `n13=PASS` 不相交的 32 行，这一点决定 §4.3 的精确错处。

### 2.4 R12 四次 CATCH 的位置

实跑命令：`python -I -X utf8 -c "<筛 r12=CATCH 行；重建 r12_scan 命中 token；读盘 TV3>"`。
输出 4 行全 `expect=CATCH / r10=PASS / r12=CATCH / n13=CATCH / chain=CATCH`，命中 token 全部 `已生效` ∈ N13 三词表 `T=(已入账,已追加,已生效)`（`all in T? True`，逐行）：

| id | expect | r10 | r12 | n13 | chain | r12 命中 token（本次实跑） | text_head / 读盘 |
|---|---|---|---|---|---|---|---|
| `R10-TV3` | CATCH | PASS | CATCH | CATCH | CATCH | `已生效`×2（pos 245, 299），读盘 `lead/gate_fp7_20261108/_g7_tv3_double_negation.md` | `<!-- _g7_tv3_double_negation.md …` |
| `R10-CTX-05` | CATCH | PASS | CATCH | CATCH | CATCH | `已生效` (pos 7) | `本件并非不宣告已生效` |
| `R10-CTX-06` | CATCH | PASS | CATCH | CATCH | CATCH | `已生效` (pos 10) | `审阅不得不承认本候选已生效` |
| `GP-C04` | CATCH | PASS | CATCH | CATCH | CATCH | `已生效` (pos 5) | `并非不宣告已生效` |

语料来源见 `lead/gate_pipeline_20261109/_gp_regression.py:67-73`（TV3 逐字读盘）、`:90-91`（CTX-05/06 双重否定构造）、`:112`（GP-C04）。`lead/keff_calc_20261109/KEFF_CALC.md:344-352` 同判「4 次正确命中都被 N13 覆盖，相对最终合成判定增量为 0」。

**为什么不破坏集合恒等**：`A={r10&r12&n13 PASS}`、`B={r10&n13 PASS}`，`A ⊆ B` 是去掉一个合取项的重言式；非平凡方向 `B ⊆ A` 只排除 `(r10=PASS & n13=PASS & r12=CATCH)`。这 4 行 `n13` 全是 `CATCH`，落在 `B` 之外，故与 `B ⊆ A` 无关。

**顺带（如实）**：`r12=CATCH ⇒ r10=PASS` 也不是定理。`_liv_verify.py:81-82` 本次会话实跑 `C2 '本笔已入账。不得不承认已生效'` → `r10=CATCH r12=CATCH n13=CATCH`；根因 `lead/gate_fp7_20261108/_g7_predicates.py:102-109`（`r10_context` 对单个 span 只返回一个 `kind`），同一文本另一 span 仍可给 `assertion`。故「4 行全 `r10=PASS`」是本批语料事实，不是代码定理。

### 2.5 ★ 逻辑必然还是巧合

**判定：不是逻辑必然，是本批语料 + 输入契约的巧合（样本巧合 + 契约巧合）。** 前件 §1(d)/:131 同判；`lead/keff_calc_20261109/KEFF_CALC.md:314,340`（`:340` 逐字「样本巧合 + 契约巧合，不是恒等式」）、`lead/evidence_indep_20261109/EVIDENCE_INDEPENDENCE.md:310`、`lead/metric_audit_20261109/METRIC_CONVENTION_AUDIT.md:290`（明记「是否定理 ⇒ 未验」）已是正确先验。本次会话不仅复核数值，还**独立实跑构造反例**（§3.2），把「预言」升级为「可复现的破坏构造」。

**关键补充**：这一判定**不因【复核】`partial` 而翻转**。【复核】`whatBreaksIt` 首句即「主结论已独立复现、成立：恒等不是逻辑必然：我实跑构造 X1/X2/X3 三例，均 r10=PASS r12=CATCH n13=PASS、∈B 且 ∉A，同时破集合恒等与 P(r12=PASS|n13=PASS)=1」。`partial` 针对的是前件**论证措辞**的三处瑕疵（§3.1）、不是主结论。按交付规则，`partial` 标 **`unconfirmed`**，本件不自行升 `confirmed`。

---

## 3 恒等性质判定（源码 + 证明 / 反例 + 「三层」合法性）

### 3.0 先修正前件自身的三处论证瑕疵（【复核】`partial` 的三点，本次会话逐条独立复现）

> 这三点**恰是「把巧合说成必然」在被核对象自身论证里的复发**，必须写进性质判定，否则本件会重犯要害。

**修正①（要害）：「`B⊆A ⟺ 无 n13=PASS&r12=CATCH 行 ⟺ P(r12=PASS|n13=PASS)=1 是同一命题的重写」不成立。**
前件 `:125`、`:146` 这样写；【复核】点名并给反例。本次会话实跑逻辑与真值表：

- 定义：`A = {r10=P & r12=P & n13=P}`，`B = {r10=P & n13=P}`。
- `A ⊆ B` 重言式；`B ⊆ A` ⟺ 不存在格 `(r10=P & n13=P & r12=C)` ⟺ **`P(r12=PASS | r10=PASS & n13=PASS) = 1`**。
- `P(r12=PASS | n13=PASS) = 1` ⟺ 不存在格 `(n13=P & r12=C)`，它**还额外排除** `(r10=C & n13=P & r12=C)`。该格与 `B⊆A` 无关。
- **正确等价式**：`A = B ⟺ P(r12=PASS | r10=PASS & n13=PASS) = 1`。`A=B` 与 `P(r12=PASS|n13=PASS)=1` **不是同一命题**；二者在 74 行上同真，靠的正是 `cells_r10C_n13P_r12C = 0` 这一额外巧合（§2.3）。
- 本次会话实跑反例（破 P 但不破 `B⊆A`）：`python -I -X utf8 -c "<judge('已入账 grep 结果。不得不承认放行 N-5', BAD_BAN, T)>"` → `r10=CATCH r12=CATCH n13=PASS | inB=False inA=False | B-subset-A violated=False | n13P&r12C=True`。即【复核】给的 `'已入账 grep 结果。不得不承认放行 N-5'` 复现成立。
- 8 种真值格局枚举（本次会话实跑）显示 `A=B` 与 `P(r12|n13)=1` 在 `(r10=C,r12=C,n13=P)` 上分叉；「forbidden sets equal (theorems)? `False`」。

**修正②：「链式法则只剩 1 个非 1 因子」是因式分解顺序依赖的描述，不是决定性的「自由度」论据。**
前件 `:110`、`:194`、`:197`、`:236`、`:320`、`:325` 把「1 个非 1 因子」当结构性结论。本次会话实跑 6 种排列（`python -I -X utf8 -c "<itertools.permutations(labels) 精确分数>"`）：乘积**恒为 `1/13 = 0.076923`**，但非 1 因子数随顺序变：

| 顺序 | 非 1 因子数 | 因子 |
|---|---|---|
| `n13 > r10 > r12` | **1** | `1/13 · 1 · 1` |
| `n13 > r12 > r10` | **1** | `1/13 · 1 · 1` |
| `r10 > n13 > r12` | 2 | `19/39 · 3/19 · 1` |
| `r12 > n13 > r10` | 2 | `35/39 · 3/35 · 1` |
| `r10 > r12 > n13` | 3 | `19/39 · 15/19 · 1/5` |
| `r12 > r10 > n13` | 3 | `35/39 · 3/7 · 1/5` |

故「只有 1 个有效因子」只能作「选定 `n13` 优先这一种因子化」下的描述，**不能**用来支持「两个自由度不成立 / 可用独立因子 = 1」的结构判定。后者必须靠 §4.4 方法 A 的依赖图与五检。前件 `:236`「不是两个自由度，而是只有一个非 1 因子」须降级为「在 `n13` 优先因子化下，两个条件因子为 1」。

**修正③：根层混用轻症 —— 「根=1 不依赖 38/38 是否为定理」这句话本身成立，但前件 `:300` 把 `EVIDENCE_INDEPENDENCE.md:299-306` 六条统称为「结构性判定」不准。**
本次会话实读 `lead/evidence_indep_20261109/EVIDENCE_INDEPENDENCE.md:299-306`：六条里 `:301` 是依赖图（结构性，单独足以支撑 ≤1 层）；`:302`（「R12 增量 0.0 bit」，挂在 `:294` 的 `38/38` 与 `:149`）、`:303`（72/74 行词表统计）、`:304`（三估计量 `0.6064/0.6697/0.8042`、`n_eff=1.0526`）、`:305`（`3/18` 错误率 / 2.0526 倍 / Fréchet）、`:306`（消融 `71/74 ≥ 69/74`）都是**统计量**，其中 `:302` 的 `0 bit` 直接依赖 38/38。⇒ 须把「六条结构性理由」改标「1 条结构性 + 5 条本 74 行统计佐证」；`:302` 的 `0 bit` 按前件自己 §3.1 #7 改标「本 74 行观测」。`≤1 层` 主结论由 `:301` 依赖图 + `:111` 五检单独成立，**不受影响**。

### 3.1 源码级：R12 / N13 的数据依赖（本次会话逐行实读）

| 事实 | 文件:行 | 内容 |
|---|---|---|
| N13 签名收 R10/R12 回调 | `lead/evidence_indep_20261109/_ei_n13_predicates_src.py:183` | `def r13_scan(text, tokens=DEFAULT_TOKENS, r10_scan=None, r12_scan=None)` |
| N13 内部用**自己的** `tokens` 回调 R12 | 同件 `:196-202` | `:196` `r10_scan(text, list(tokens))` 收 `r10_map`；`:200` `_, dhits = r12_scan(text, list(tokens))`；`:202` `r12_pos.add((h["token"], h["pos"]))` |
| 遍历 `tokens` 逐处 span，`gpos` 用 `len(line)+1` 累加 | 同件 `:208-215, :224-225, :293` | `for tok in tokens: for m in re.finditer(..., body)`；`gpos = abs_base + off + bs` |
| 行级肯定守卫一律 D 且 `continue` | 同件 `:233-239` | `if mixed: rec.update(kind="D", ...); details.append(rec); continue` |
| **R12 命中无条件提升为 D（CATCH）** | 同件 `:241-245` | `if (tok, gpos) in r12_pos: rec.update(kind="D", exempt=False, rule="R12 双重否定构式=肯定"); ...; continue` |
| A/B 放过分支在 D 之后 | 同件 `:273-285` | `:282` `kind="A"` / `:278` `kind="B"`，`exempt=True` |
| 只有 D 类进 `problems` | 同件 `:307-313` | `problems = [... for d in details if d["kind"] == "D"]` |
| R12 是 R10 `double_neg` 的确定性子集 | `lead/gate_fp7_20261108/_g7_predicates.py:134-148`，命中 `:144-145` | `ctx = r10_context(...); if ctx["kind"] == "double_neg"` |
| N13.C 转发 R10.kind | `_ei_n13_predicates_src.py:247-256` | `k = rec["r10_kind"]; if k in ("negation","quote_mention"): kind="C"` |
| 编排层注入两回调 | `lead/gate_pipeline_20261109/_gp_pipeline.py:76-81` | `:78` R10 用行 `tokens`；`:79` `r12_scan(text, tokens)`；`:80-81` `n13.r13_assertions(text, n13_tokens, r10_scan=..., r12_scan=...)` |
| **运行时词表契约分叉** | `lead/gate_pipeline_20261109/_gp_regression.py:141,143` | `:141` R12 单层用**该行 `tokens`**；`:143` N13 单层**恒用固定 `T`**（`r13_assertions(text, T, ...)`） |
| 位置口径自认会错位 | `lead/gate_pipeline_20261109/_gp_pipeline.py:60-70` | `:61`「CRLF 文档须先记录 eol 类型」；`:70`「CRLF 时 N13.gpos 与 R10.pos 相差行号数」 |

依赖图（源码级，非语料统计）：`R10 → {R12, N13.C}`，N13 消费 R12 命中；`lead/gate_pipeline_20261109/GATE_PIPELINE_COMPOSE.md:272` 编排方自认「三层证据不独立」；`lead/evidence_indep_20261109/EVIDENCE_INDEPENDENCE.md:111`「现有 4 层中没有任何一对能同时过 5 检，故一律不得按 2 层计」。

### 3.2 若必然给证明 / 若巧合给破坏构造

**(a) 受限蕴含的证明（「`n13=PASS ⟹ r12=PASS`」的条件版）**：设 `P1` = R12 单层与 `r13_scan` 内部使用**同一 `tokens` 集合**；`P2` = 文本 LF、两处 `(token,pos)` 口径一致；`P3` = R12 命中 token ∈ `T`（或在 `r13_scan` 的 `occ` 遍历范围内）。在 `P1∧P2∧P3` 下：R12 单层 CATCH ⇒ 存在命中 `(t,p)` 使 `r10_context` 给 `double_neg`（`_g7_predicates.py:144-147`）；由 `P1∧P2`，`r12_pos` 含同一 `(t,p)`（`_ei_n13_predicates_src.py:199-202`）；遍历该 span 时 `:233-239` 或 `:241-245` 必先置 `kind="D"` 且 `continue`，不可能落到 `:273-285` 的 A/B 放过分支；由 `:307-313` 该 D 进 `problems` ⇒ `n13=CATCH`。逆否得 **`n13=PASS ⟹ r12=PASS`**。∎

本次会话实跑受限域验证：`python -I -X utf8 "D:/Project/ra2-campaign-forge/lead/layer_identity_20261109/_liv_verify.py"` → `combos=180 broken=0`（3 token × 10 构式 × 6 前缀）、`r12=CATCH=1200 violations=0`（随机 1200 次）。**但这只是受限定理**，前提 `P1/P2` 会被下面 (b) 破。

**(b) 巧合的破坏构造（本次会话实跑，非纸面推测；`_liv_verify.py:69-79` 输出逐字复现）**：

| # | 构造输入 | 行 tokens | r10 | r12 | n13 | ∈B | ∈A | 机制 |
|---|---|---|---|---|---|---|---|---|
| X1 | `不得不承认放行 N-5` | BAD_BAN 五词 | PASS | CATCH | PASS | True | False | 词表契约分叉 |
| X2 | `不得不承认可应用母本` | BAD_BAN 五词 | PASS | CATCH | PASS | True | False | 词表契约分叉 |
| X3 | `第一行文字\r\n不得不承认，已入账 grep 结果` | T 三词 | PASS | CATCH | PASS | True | False | CRLF 位置错位 |

`_liv_verify.py:76-79` 输出：`X1/X2/X3: inB=True inA=False => A!=B ? True ; n13=PASS&r12=CATCH ? True`。**三例同时破集合恒等与 `P(r12=PASS|n13=PASS)=1`**（注意：它们 `r10=PASS`，故落在 `B⊆A` 的排除格内，两命题在这三例上恰好同破；这**不**救回 §3.0 修正①的等价性错误，见该节反例）。

- **X1/X2 机制**：`_gp_regression.py:141` 让 R12 用行 `tokens`（BAD_BAN 五词含 `放行 N-5`/`可应用母本`），`:143` 让 N13 恒用 `T` 三词；`_ei_n13_predicates_src.py:200` 内部回调也用自身 `T`。故 R12 在超集专有 token 上命中 `double_neg` 时，`r12_scan(text, T)` 在 N13 内部**不命中**，`r12_pos` 为空 ⇒ `:242` 提升不触发 ⇒ `n13=PASS`。`KEFF_CALC.md:333-340` 已预言此机制；本次会话 `_liv_verify.py:126-130` 实跑 74 行中 `not_subset n=19`（17 行 BAD_BAN 超集 + 2 行 C07 词表），`distinct token sets` 4 种 —— 破口在语料里真实存在，只是这 19 行恰好没在超集 token 上命中双重否定。
- **X3 机制（本次会话新增源码级展开）**：`python -I -X utf8 -c "<r12_scan / r13_scan 直调，打印 hits 与 details>"` 输出：`r12 hits (token,pos): [('已入账', 13)]`；`n13 details: token=已入账 gpos=12 kind=A rule=A 检索动作…`；`splitlines` 累加 `第一行文字` 长 5 → `+1=6`，第二行 `bs` 算得 `gpos=12`。`r12_pos={('已入账',13)}` ≠ `n13 (tok,gpos)={('已入账',12)}` ⇒ `:242` 不触发，落到 `:273-285` 的 A 豁免 ⇒ `n13=PASS`。`_gp_pipeline.py:60-70` 自认此错位。`_liv_verify.py:101-109` 实跑 `prior_lines=1/2/3 violations=10/10`（共 30/30 违例）。
  - **如实限定**：`Path.read_text` 归一 CRLF→LF（本次会话实跑 `read_text CRLF repr = 'line1\nline2\n'`；`_gp_regression.py:72/82/106` 为读盘路径）；本次会话实跑 9 件读盘真件 `CRLF=0`（`_g7_tv2/tv3`、四件 R10-REAL、`C07_IDENTITY_SLOT`、`C07_TRUTH_SELF_PROOF`、`LEDGER_BOUND_VOLUME`）。故 X3 需「内联 / 直接文本入口」才在生产可达；**生产可达性未验**。它是代码层面的真反例，不是本批语料里已发生的事。
- **采样涨破**：`lead/keff_calc_20261109/KEFF_CALC.md:315-326` 给零命中 38 次四种 95% 上界 `0.075808 / 0.078947 / 0.091810 / 0.092513`（7.6%–9.3%），真比例不为 0 ⇒ 更大语料撞出反例概率非零。

**(c) 结论**：无条件的**逻辑必然性 = 否**。恒等只在「同一 `tokens` 集合 + LF 对齐位置 + 命中 token 在 `T` 内」的受限契约下由源码蕴含；契约一破即破。`METRIC_CONVENTION_AUDIT.md:104,108,272` 的「不是近似省一层」「决定性集合等式」「必附独立性依据」须撤回（改「本 74 行观测等式」）。这正是本任务要害：**74 行样本上成立 ≠ 逻辑上成立**。

### 3.3 「三层」说法的合法性

| 用法 | 合法？ | 依据 |
|---|---|---|
| 描述「编排里串了 3 个判据 R10/R12/N13」 | ✅ 合法 | `_gp_pipeline.py:76-90` L2/L3/L4 三个调用点；`KEFF_CALC.md:287`「3 个判据 / 1 个独立证据根」 |
| 描述「3 个独立证据 / 3 层独立 / 置信度可乘 3 次」 | ❌ 不合法 | `GATE_PIPELINE_COMPOSE.md:272` 自认不独立；`EVIDENCE_INDEPENDENCE.md:111` 无任何一对过五检；根 = 1 |
| 用集合恒等推出「**两个自由度** / 有 2 个独立层」 | ❌ 不合法 | 恒等是**观察等式**（§3.0 修正①的正确等价式只到 `P(r12|r10&r13)=1`），不增加独立性；且「1 个非 1 因子」是因式分解顺序依赖（§3.0 修正②），不能当自由度判定 |
| 「三层全 PASS ⇒ 自动放行」 | ❌ 不合法 | 18 行里 3 行真断言（`GP-A1/A2/A3`，§2.2）；`CHAIN_VS_SINGLE.md:263`、`KEFF_CALC.md:301-302` 已禁 |

> **对编排方「两个自由度」的精确修正**：全 74 行标签三元组确有 5/8 种可观测组合（本次会话实跑 `distinct = 5 of 8`），作**描述**勉强可用；但这是「标签自由度」，不是「可用独立因子数」。恒等既非逻辑必然，又与 `P(r12|n13)=1` 不等价，更不能用「集合相等」推出「2 个独立层」。三层连乘与两层连乘都错（§4.3）。

---

## 4 对层数结论的影响（逐处 + 三层连乘错在哪 + 正确算法）

### 4.1 逐处清单（本次会话实跑 10 份文档强模式普查 + 前件 §3.1 十九类落点复核）

普查命令：`python -I -X utf8 -c "<读 10 份文档；强模式 ['决定性集合等式','不是近似省一层','两个自由度','≈1～1.3','≈1～1.5','乐观 1.5','0.61 层','0 bit','不提供任何新信息','按 3 层','绝不可按 3 层','独立证据根','38/38','1.000'] 逐行命中>"`；输出 `METRIC_CONVENTION_AUDIT.md 21 / KEFF_CALC.md 20 / EVIDENCE_INDEPENDENCE.md 9 / SCORE_DECOMP.md 0 / _pv_PVALUE_RECALC.md 3 / GATE_PIPELINE_COMPOSE.md 0 / CHAIN_VS_SINGLE.md 5 / _cs_BASELINE_ALIGNMENT 7 / PENDING_DECISIONS.md 0 / GOAL 8（均为别论域数值 1.0000）`。逐处判定如下（**受影响**列指「恒等被判为巧合」是否改变该落点的措辞/数值合法性；主结论列指「≤1 层 / 绝不按 3 层」是否翻转）：

| # | 位置 | 结论原文要点 | 受影响？ | 逐处判定 |
|---|---|---|---|---|
| 1 | `KEFF_CALC.md:102-104` | `3.75%` 两层乘积 / `3.36%` 硬乘三层，差 0.38pp | **间接** | 数值不受影响；但两层乘积解释也错（§4.3），`:103` 把「R12 零增量」当根因应改挂依赖图 |
| 2 | `KEFF_CALC.md:140-150` | `p2=p3=3/18`、k_eff 三口径 `0.606/0.670/0.804`、R12 bit 增量 `0.000000000` | **直接** | `p2=p3` 完全靠恒等；恒等一破 `p3≠p2`、三值全变。已标「描述性、不可靠、不可用于放行」(`:191-200,390-392`)，恒等偶然性是**再加一条**不可靠理由 |
| 3 | `KEFF_CALC.md:165-168,234-236,287-288,399-407` | 「≤1 层」「独立证据根=1」「numeric=1 保守取整」「3 判据/1 根」「绝不可按 3 层」 | **不受影响** | 依据是依赖图与 A1–A5 五检（`EVIDENCE_INDEPENDENCE.md:111,301`），**不是** 38/38；反而更稳（见 §3.0 修正③限定） |
| 4 | `KEFF_CALC.md:255-258,282-305` | Bayes 2 层 91.12% / 3 层 91.96%、置信度声明模板 | **不受影响** | 明确是「独立宣称下的**反事实点值**」并自标「无区间、非实测」(`:293-295`) |
| 5 | `KEFF_CALC.md:311-362` §5 | `38/38=1.000` 是**观测值非定理**；`:340`「样本巧合 + 契约巧合，不是恒等式」；`:354-362` R12 是「R10 派生守卫」 | **不受影响，且是本件最强先验** | X1/X2/X3 把 `:333-340` 的预言实跑化；该件结论**成立并被本次会话强化** |
| 6 | `KEFF_CALC.md:409-443` 17 条重述清单 | 第 10/11/15 条要求把 `1.000` 标观测值、第 4/12/14/16/17 条改 `≈1～1.3/1.5` | **不受影响** | 已正确处置，与本件 §5.3 同向 |
| 7 | `EVIDENCE_INDEPENDENCE.md:149,294` | 「R12 增量判别力 = 0 bit」`38/38=1.000` | **直接** | 应改标「本 74 行观测」并附 `KEFF_CALC.md:315-326` 四种 95% 上界与 §3.2 破口；`:155` 的「有效独立层数 ≈1」靠 `:301` 依赖图，稳 |
| 8 | `EVIDENCE_INDEPENDENCE.md:240-260` | `Πq_i ≤ q_max^n`、H1–H4、Fréchet `min q_i` | **不受影响** | `:247` 明记 H1 已证伪、`:256` 明令不得用 `Πq_i`；与本件 §4.3 一致 |
| 9 | `EVIDENCE_INDEPENDENCE.md:289-308` | 三层分类表、`:299` 按 1 层计 `numeric=1`、`:301` 根=1、`:310` 自限「只在这 74 行上成立」 | **部分（措辞）** | `:299/:301` 不受影响；但**六条理由须按 §3.0 修正③重标**：`:302/:304/:305/:306` 是统计量、`:302` 的 `0 bit` 挂 38/38 |
| 10 | `CHAIN_VS_SINGLE.md:190-206,263` | 「≈1～1.3 层（乐观 1.5）」「有效独立层数 ≈1」「三层一致即放行→禁止」 | **部分** | `:206` 的 `1.000` 与 `k_eff=0.6064` 直接受影响；`:263`「禁止自动放行」不受影响（靠 3/18 实测） |
| 11 | `_cs_BASELINE_ALIGNMENT_20261109.md:213,222-228,266,277,334` | `1.000 零增量`、`≈1～1.3（乐观 1.5）`、`≈1` | **直接** | 同 #10；`KEFF_CALC.md:436-443` 已列须改 |
| 12 | `_cs_info.py:39-43` / `_cs_info_out.txt:9-11` | `k_eff=0.61`、`≈1～1.5 层，不是 3 层` | **直接** | `k_eff` 分子 `p3` 靠 `p2=p3`；恒等破则数值破 |
| 13 | `_cs_holdout.py:127-128` / `_cs_holdout_out.txt:40` / `_csv_holdout_replay.txt:40` | 「R12 不提供任何新信息 → 有效独立层数约 1～1.3 层」 | **直接** | 「不提供任何新信息」是全称断言，被 X1/X2/X3 证伪 → 改「本 74 行上未提供」 |
| 14 | `_ei_07_final.py:89` / `_ei_07_final_out.json:154,157` | 「1 层（保守）／0.61 层（按后验信息量折算）」「2.6 倍乐观」 | **直接 + 已判错置** | `METRIC_CONVENTION_AUDIT.md:124,213` 已判 `0.61` 张冠李戴、`2.6` 未验；本件再加「恒等偶然性」 |
| 15 | `METRIC_CONVENTION_AUDIT.md:96-111` | `q10·q13=19/507`、`q10·q12·q13=665/19773`、`:108`「**决定性集合等式**」、`:104`「不是近似省一层」 | **★ 须修正措辞** | 数值全对（本次会话 §2.3/§4.3 复现）；但 `:108/:104` 把恒等当结构性定理 → 与 `KEFF_CALC.md:340` 冲突，改「本批语料的观测等式」 |
| 16 | `METRIC_CONVENTION_AUDIT.md:132,208-212,267,272,279` | 第 12 行「层数点值无区间」、2.2872「口径不适用本链」、`:272` 把集合等式列为「必附独立性依据」 | **部分** | `:272` 应改列**依赖图 file:line**；其余不受影响 |
| 17 | `METRIC_CONVENTION_AUDIT.md:189,267` / `KEFF_CALC.md:267,399-407` | 主结论「按 1 层计、绝不可按 3 层、三层全 PASS 不可自动放行」 | **不受影响** | 由结构性根论证支撑；恒等是否为定理都**不改变**这条结论 |
| 18 | `SCORE_DECOMP.md` / `lead/pvalue_recalc_20261109/*` | 「0 bit / ≈1」属 **K9 post-selection 自信息**（`_pv_PVALUE_RECALC.md:226-228`） | **不适用** | 论域不同（配对 b/c、信息量），非层数结论；本次会话强模式普查 `SCORE_DECOMP.md 0` 命中、`GATE_PIPELINE_COMPOSE.md 0` 命中 |
| 19 | `PENDING_DECISIONS.md:209,358` / `GOAL:784,1338,1363` | 「−16.67%(1/6)」「不能写成三趟全过」「三层空白」「两层消解」 | **不适用** | 属 D-21 裁决 / harness7 真机趟数 / 真 GDI 截屏 / 帧时 q-r 张力，**非 R10/R12/N13 论域**（`KEFF_CALC.md:445-455` 同判）；本次会话强模式普查两件台账 0 命中 |

**汇总**：
- **稳（不受影响）**：所有「按 ≤1 层计 / 绝不可按 3 层 / 不得自动放行 / 独立证据根 = 1 / R9·R11 正交 / Fréchet `min q_i`」—— 靠代码级依赖图（`_g7_predicates.py:144-145`、`_ei_n13_predicates_src.py:199-202,241-245,253-256`、`_gp_pipeline.py:80-81`）与 `GATE_PIPELINE_COMPOSE.md:272` 自认，不靠 38/38。恒等被判巧合后，这些结论**更干净**：不能再被误读为「因为集合相等所以只有 2 层」。
- **须降级/改措辞**：把 `38/38=1.000`、`p2=p3`、集合恒等当**全称命题或结构性依据**的落点（#2、#7、#10–#14、#15 措辞、#16 的 `:272`、#9 的六条理由标法）。统一改「本 74 行观测」并附 §3.2 破口。
- **数值须重算但不是结论**：k_eff 三口径、`0 bit`、2.2872 —— 本就标「描述性/未确认/未作结论」（`KEFF_CALC.md:390-392`、`METRIC_CONVENTION_AUDIT.md:212`）。
- **不受影响但解释也错**：#1 的两层乘积（§4.3）。

### 4.2 ★ 「两个自由度」与「条件概率 1」的精确关系（承接 §3.0 修正①②）

- `P(r12=PASS|n13=PASS)=1` 是真观测（38/38），但它**不是** `A=B` 的等价式；正确等价式是 `P(r12=PASS|r10=PASS & n13=PASS)=1`（§3.0 修正①）。
- 在 `E` 上链式法则的 6 种因子化乘积恒为 `1/13`，非 1 因子数 1/2/3 随顺序变（§3.0 修正②）；故「条件概率 1」与「两个自由度」都不能用来数独立层。
- 结论：恒等把「`n13=PASS&r12=CATCH` 格为空」与「`r10=C&n13=P&r12=C` 格为空」两件**本批语料事实**打包成一个观察等式；它不提供任何独立性，也不提供「2 层」或「1 层」的结构计数。

### 4.3 ★ 三层连乘 `q_r10×q_r12×q_n13` 精确错在哪（本次会话 `fractions.Fraction` 实跑）

实跑命令：`python -I -X utf8 -c "<读 rows；E=expect=CATCH；q_i / 两乘积 / 三层乘积 / 链式 / 比值 精确分数>"`。输出逐字：
`q10 19/39 q12 35/39 q13 1/13`；`prod2 19/507 0.03747534516765286`；`prod3 665/19773 0.033631720022252565`；`chain_e 1/13`；`prod3/chain 665/1521 0.43721236028928334`；`chain/prod3 1521/665 2.287218045112782`；`FRECHET min 1/13 all3E==min? True`。

**正确的联合漏报必须走链式法则（不假设独立）**，取 `n13` 优先因子化：
```
P(all3 PASS | E) = P(n13=P|E) · P(r10=P | n13=P,E) · P(r12=P | n13=P & r10=P, E)
                 = 1/13        · 3/3 = 1                    · 3/3 = 1
                 = 3/39 = 1/13        （chain-rule == measured ? True）
```

三层连乘 `q_r10·q_r12·q_n13` 的三层错误：

1. **把条件因子偷换成边缘 `q_i`**：把 `P(r10=P|n13=P,E)=1` 换成 `q_r10=19/39`；把 `P(r12=P|n13&r10=P,E)=1` 换成 `q_r12=35/39`。于是乘了 `19/39 × 35/39 = 665/1521 = 0.4372` 而不是 `1×1`。
2. **算术后果**：得 `665/19773 = 0.033632`（3.36%），**低估** `1521/665 = 2.287218045112782` 倍（即 `METRIC_CONVENTION_AUDIT.md:212` 的 2.2872）。`q_r12=35/39` 的 35 里只有 3 行与 `n13=PASS` 相交，另 32 行来自 `n13=CATCH`（§2.3 本次会话实跑），把这部分乘进「三层全 PASS」是范畴错误。
3. **更根本的错（模型假设）**：乘边缘 `q_i` 只在 **H1「各层误差在给定真值 E 下条件独立」** 下成立，而 `EVIDENCE_INDEPENDENCE.md:246-247` 明记 H1 已被证伪（N13.C 转发 R10、R12 是 R10 子集、共用词表）。这不是「少乘/多乘一项」的算术误差，是**模型假设错误**。`EVIDENCE_INDEPENDENCE.md:256` 已明令「不得用 `Πq_i`」。
4. **连「两层乘积」也错**：`q_r10×q_n13 = 19/507 = 0.037475` 同样把条件因子 `3/3=1` 换成 `19/39`。`METRIC_CONVENTION_AUDIT.md:111` 已正确指出它是「**反事实基线期望**，不是 2 个独立层的联合漏报、也不是上界」。真正的分布无关上界是 Fréchet `min_i q_i = q_n13 = 1/13`，且被实测**取等（饱和、零余量）**（`KEFF_CALC.md:260-266`、本次会话 `FRECHET min 1/13 all3E==min? True`）。

> 一句话：**错在把「条件概率」当「独立层似然」相乘**；且「三层→两层」的改写本身不够（§3.0 修正②：因子化顺序依赖，不能据此数「两个自由度」）。

### 4.4 正确算法（三条，禁止混用）

**方法 A（决定性、结构性）—— 依赖图源节点数 + A1–A5 五检**：
1. 从源码建数据流图：谁调用谁、谁消费谁的返回容器、谁共用 `tokens` / 提取器 / `re` 正则对象。
2. 本链实读：`R12 = f(R10.double_neg)`（`_g7_predicates.py:144-145`）、`N13.C = g(R10.kind)`（`_ei_n13_predicates_src.py:253-256`）、N13 消费 R12 命中（`:199-202,242-243`）、编排注入（`_gp_pipeline.py:80-81`）⇒ 图 `R10 → {R12, N13.C}`，**源节点 = 1**。
3. 逐对跑 A1–A5 五检（`EVIDENCE_INDEPENDENCE.md:101-111`）：`V12|G7`、`V12|N13` 不过 A2′，`G7|N13` 不过 A3，`R10|R12` 不过 A3/A2 ⇒ **没有任何一对全过** ⇒ 连 2 层都不能计。
4. `lead/evidence_indep_20261109/_eiv_03_stats.py:182-184` 留 `structural_max_independent_roots = 1`，`why` 逐字写明上述依赖图；`_eiv_03_stats_out.json:114` 同值（本次会话 `grep` 实读）。
5. 结论：**可用独立因子数 ≤ 1**；`numeric=1` 是保守取整的工程约定，非测量值（`KEFF_CALC.md:165-167,236`）。`EVIDENCE_INDEPENDENCE.md:295` 把 N13 A/B 判「部分独立」，故严格表述是「1 个完全独立根 + 1 条部分独立分支」。
6. **本方法不依赖 38/38、不依赖集合恒等**（§3.0 修正③）：这是「根=1」唯一的结构性来源。

**方法 B（统计、不得当作层数计数）**：链式法则条件 LR：`odds(post) = odds(π)·Π LR_i`（`EVIDENCE_INDEPENDENCE.md:243`），逐因子用条件概率而非边缘 `q_i`；`k_eff` 只报「**相对 N13 单层的判别力比值**」，三口径并列 + bootstrap/Wilson/CP 区间 + 「描述性、不可用于放行」（`KEFF_CALC.md:191-200`）；前置封 SHA 盲留出集含 r10/r12/n13 全判定列（现状缺列 ⇒ `EVIDENCE_INDEPENDENCE.md:315` 标**未验**）。

**方法 C（兜底）**：报 Fréchet `min_i q_i` 与 `P(E|allPASS)` 的 Wilson/CP 区间，不报 `Πq_i`（`KEFF_CALC.md:260-269`）。

**禁止**：把「标签三元组的自由度」「判据个数」「集合恒等」「某一因子化下非 1 因子个数」任一个当独立层数。

---

## 5 根与层

### 5.1 「证据根 = 1」的「1」怎么定的

**定义**：数据依赖 DAG 中**无入边**的源节点数；信息的最初出处。本次会话实读依据：
- `EVIDENCE_INDEPENDENCE.md:301`「依赖图为单一根 `R10 → {R12, N13.C}`，独立证据根 = 1」；逐行证据 `:55-72`；`GATE_PIPELINE_COMPOSE.md:272` 自认「三层证据不独立」。
- `EVIDENCE_INDEPENDENCE.md:111` 硬性机检：「现有 4 层中没有任何一对能同时过 5 检，故一律不得按 2 层计」（A1–A5 定义 `:105-109`）。
- `_eiv_03_stats.py:182-184` / `_eiv_03_stats_out.json:114`：`structural_max_independent_roots = 1`。
- `:299` 的 `numeric = 1` 是**保守取整的工程约定**，`KEFF_CALC.md:165-167,236` 明写「不是 k_eff 测量值，且比 k_eff 点值更乐观」。

**★ 关键澄清（承接 §3.0 修正③）**：`:299-306` 列了六条理由，**只有 `:301` 是结构性**；`:302`（`0 bit`，挂 `:294` 的 38/38 与 `:149`）、`:303`（72/74 行词表统计）、`:304`（`0.6064/0.6697/0.8042`、`n_eff=1.0526`）、`:305`（`3/18`、2.0526 倍）、`:306`（消融 `71/74 ≥ 69/74`）都是**本 74 行统计量**。故：
- 「根 = 1 不依赖 38/38 是否为定理」这句话**成立**，但成立的原因是 `:301` 依赖图 + `:111` 五检**单独**够用，不是因为「六条都是结构性」。
- 前件 `:300`「六条结构理由」的标法须降级；`:302` 的 `0 bit` 按前件自己 §3.1 #7 改「本 74 行观测」。
- `≤1 层` 主结论**不受影响**；被改的是佐证的分类标签。

### 5.2 `k_eff` 是否还合理

三口径本次会话沿用前件 `#21` 与 `KEFF_CALC.md:139-147` 实算值：`k_prob=0.6064124084`、`k_odds=0.6696629281`、`k_info=0.8042328042`（本次会话未重跑 bootstrap，故**区间未验**，只引 `KEFF_CALC.md:191-200` 的记载）。

1. **与根=1 不矛盾，但不同量纲**：`k_eff` 量的是「三层一致通过相对 N13 单层的后验/几率/信息量比值」（`_cs_info.py:36-41`、`KEFF_CALC.md:139-147`），不是根计数。根=1 且层间相关/负贡献时三层一致反而更差 ⇒ `k_eff<1` 是预期内（`EVIDENCE_INDEPENDENCE.md:150`：`n13=PASS & r10=PASS` 富集了 GP-A 三条共同盲区）。
2. **作为「层数」不合理，必须停用该标签**：`KEFF_CALC.md:156-158,164-167` 自写「`I=π−p` 不是 bit，不能解释为层数」「仍是相对判别力比值，不是层数计数」「三者共用同一 3 个错例，不是三个独立估计」。`_ei_07_final.py:89` 的「0.61 层」与 `METRIC_CONVENTION_AUDIT.md:124` 已判**张冠李戴**。根=1 时的正确结构答案是「≤1 层，`numeric=1` 保守取整」。
3. **作为描述性统计量也不可靠**：`KEFF_CALC.md:191-200` 三套 bootstrap 上限触 1.0000、全距含负值、删 1 个错例即 `0.7899`、`k=1 → 1.1851>1`，标「描述性、不可靠、不可用于放行」；`:390-392` 因复核 `verdict=partial` 全件标 `unconfirmed`。**本次会话新增第四条不可靠理由**：`p3=p2` 只在集合恒等成立时成立，而恒等已被 X1/X2/X3 构造性证伪 ⇒ `k_eff` 的分子是**本批语料的偶然量**。

**结论**：带「宽区间 + 描述性 + 不可用于放行 + 三口径并列」标签、且明确改名「判别力比值」时**可留作描述**；作为「k_eff / 有效独立层数估计」**不合理**，应从层数结论中移除，只保留结构性 `≤1 层`。**本次会话未重跑 k_eff 点值/bootstrap**（只读引用），该重算标**未验**。

### 5.3 根与层的关系（澄清）

| 概念 | 定义 | 本链取值 | 性质 | 出处 |
|---|---|---|---|---|
| **根（independent evidence root）** | 依赖 DAG 中无入边的源节点 | **1**（`R10`；N13.A/B 为部分独立分支） | 代码级、结构性；给定谓词 SHA 即确定，与语料抽样无关 | `EVIDENCE_INDEPENDENCE.md:301`；`_eiv_03_stats.py:182-184` |
| **层（pipeline layer / 判据）** | 编排里被调用的一个谓词/阶段 | **3**（L2 R10 / L3 R12 / L4 N13） | 实现事实；只说明执行了几次检查 | `_gp_pipeline.py:76-90` |
| **可用独立因子** | 能合法写入 `Πq_i` 的因子个数 | **≤1**（H1 已证伪 ⇒ 连 2 个都不成立） | 由根数与 H1 共同决定，**不是**由某一链式因子化的非 1 因子数决定（§3.0 修正②） | `EVIDENCE_INDEPENDENCE.md:240-250` |
| **k_eff / 有效独立层数** | 拟合比值「若干同 LR 独立层能给同样后验偏移」 | `0.606/0.670/0.804`（描述性、不可用） | 统计量；可 <1、可非整数，**不是计数** | `KEFF_CALC.md:139-147,156-158` |

**关系（严格偏序）**：`可用独立因子数 ≤ 独立证据根数 ≤ 判据/层数`；`k_eff` 与三者**不同量纲**，不可互相换算。`k_eff<1` 与「根=1」并存不矛盾：前者说「这批判据组合的判别力比不上一个 N13」，后者说「信息只有一处原始出处」。

### 5.4 混用「根」与「层」的误导（逐条）

1. **「根=1 ⇒ 可以按 2 层相乘」**：把结构计数当乘积因子数。实际 `q_r10×q_n13` 也错（§4.3），因为 `P(r10=P|n13=P,E)=1`。这是最危险的误导，正是 `METRIC_CONVENTION_AUDIT.md:96-111` 的措辞风险。
2. **「0.61 个独立证据根」**：把拟合比值当根计数，产生「分数个信息源」伪概念；`METRIC_CONVENTION_AUDIT.md:156` 已列此类张冠李戴。
3. **「3 个判据 = 3 次独立确认 ⇒ 置信度可乘」**：直接推出 91.96% 宣称正确率 vs 实测 83.33%（`KEFF_CALC.md:255-256`），低 8.63 pp。
4. **把 `numeric=1` 读成 k_eff 测量值**：`KEFF_CALC.md:166-167,236` 明说它是保守取整约定、比点值更乐观；混用会把工程约定包装成实测。
5. **「≈1～1.3 层（乐观 1.5）」**（`CHAIN_VS_SINGLE.md:206`、`_cs_BASELINE_ALIGNMENT:228`）：把统计比值与结构计数并置，给出 **>1** 的「层数」，与根=1、与 `k_eff<1` 同时冲突；`KEFF_CALC.md:418-419,436-443` 已列须改为 ≤1 层 + 宽区间。
6. **「两个自由度」→「2 个独立层」**：混淆「标签三元组自由度」（全 74 行 5/8 种，本次会话实跑）与「可用独立因子数」（≤1，靠依赖图）；且集合恒等与 `P(r12|n13)=1` 不等价（§3.0 修正①），不能作桥梁。
7. **方向性误导**：混用会让人以为「加判据 = 加置信」，而结构性结论恰恰是「加判据不改变信息根，还可能富集共同盲区」（`EVIDENCE_INDEPENDENCE.md:150,156`）。

---

## 6 复核回件（绑定行）+ 结论 + 未验项

### 6.0 复核 verdict 如实登记

- 前件 `_li_LAYER_IDENTITY_PROOF_20261109.md` 的【复核】`verdict = partial`；其 `sha256Line` 记录的 64 位十六进制为 `13453a000c61cb211c51931cc8a7bd3d1912a9e1714d46cb8be349686fe9c957`、字节数为 47501（本次会话 `hashlib` 现盘重算全等，§2.1；规范绑定行见 §6.1 补测第 1 行）。
- 按交付规则：**`partial` ⇒ 标 `unconfirmed`**。本件不自行升 `confirmed`。
- `partial` 的三处瑕疵（【复核】`whatBreaksIt`）本次会话逐条独立复现并写入 §3.0：① `B⊆A` 与 `P(r12|n13)=1` 不等价，正确等价式是 `A=B ⟺ P(r12|r10&r13)=1`，并实跑 `'已入账 grep 结果。不得不承认放行 N-5'` 破 P 不破 `B⊆A`；② 链式法则「1 个非 1 因子」是因式分解顺序依赖（6 排列实跑，乘积恒 `1/13`，非 1 因子数 1/2/3）；③ 六条理由中 `:302/:304/:305/:306` 是统计量、`:302` 的 `0 bit` 挂 38/38，须降级。
- 【复核】明确「主结论已独立复现、成立」：X1/X2/X3 三例均 `r10=PASS r12=CATCH n13=PASS`、∈B 且 ∉A，同时破集合恒等与 `P(r12=PASS|n13=PASS)=1`；② 逐 id 集合比对 `18=18`、`38/38`、4 次 CATCH 全在 `n13=CATCH` 侧全等；④ 源码判成立；⑤ 精确分数与 2.2872 全对。本次会话 §2 / §3.2 / §4.3 全部独立重跑一致。
- 【复核】升级条件（如实记，均**未验**）：若给出代码级证明「`(r10=CATCH & n13=PASS & r12=CATCH)` 在任何输入下不可达」，瑕疵①消失；若进一步证明 X1/X2/X3 类输入在生产契约下全部不可达，则「恒等不是逻辑必然」应改「在给定生产契约下是定理」，主结论翻转。本次会话**未做**这两项全称证明（见 §6.6）。`minor`：前件 `what` 自报「396 行」，实跑 `len(splitlines())=400`、47501 字节（§2.1）。

### 6.1 复核回件绑定行（十件上游指纹，`hashlib.sha256` 现盘重算）

> 格式严格：固定前缀「被核对象」+ 空格 + 「SHA256 = 」+ 完整 64 位十六进制（中间不插路径/括号/星号/反引号/空格）+「，字节数 = 」+ 数字。以下 10 行与编排方【编排方指纹】逐字全等（§2.1 实跑 `ALL_10_MATCH = True`）。

被核对象 SHA256 = f737d8a52b51ded87e2f20cd1368f73b4cf3fb7331c34384b0d4b802caf9c503，字节数 = 45362
被核对象 SHA256 = 18818d765c9344c7d3f5c897c7c9d0edd30e71926484d5d5de97d4aea2b59743，字节数 = 6360
被核对象 SHA256 = 4ad16cdb7dbb4b9e97ea306b55af6d51e2c262a52b10c75e56e1f5ffa1126e16，字节数 = 34964
被核对象 SHA256 = aeab4fc30822dfde9c21489aef9a42a1558dde1f21f091f486bbd94453f7a523，字节数 = 36194
被核对象 SHA256 = dfe7f68692eb7ae752358782acaaa1fc5a42ecbd0a6930205e0dcfe4f6544dcb，字节数 = 42573
被核对象 SHA256 = 277df9910d4611e0072faf83bd65e3639667a01b511191d5f74b575e448911ac，字节数 = 29780
被核对象 SHA256 = d3543657aa4f9914c9023710f6daef8348a12ca0aa11957110e8b7c45baec6fe，字节数 = 38575
被核对象 SHA256 = efde3e8e13084d840d08ad9243c91ac1f83c3b445a71f525cc4d2335402dc4ed，字节数 = 39558
被核对象 SHA256 = 3765eddbe96deeb65eeb1f05dc81e1dc171e7ea3b2c826e2692a1d15e1c8f2d7，字节数 = 52419
被核对象 SHA256 = 2baa0de45d4125549262eb595d7518c9ce99efeee120384bf640cded8a933ede，字节数 = 759518

补测（前件本体 + 两件谓词源码，本次会话 `hashlib` 实算，供引据绑定）：

被核对象 SHA256 = 13453a000c61cb211c51931cc8a7bd3d1912a9e1714d46cb8be349686fe9c957，字节数 = 47501
被核对象 SHA256 = e1195b3b220ad97b5b91b8746a24e332b02ce28085452e947554f99b7f2f3079，字节数 = 16649
被核对象 SHA256 = 02c17e49764a6f87f2b0d26c6689f0cbeb96498509e5c75bf843104829c51120，字节数 = 11743

### 6.2 「三层」的精确表述（可直接引用；已含 §3.0 三处修正）

> **「R10 / R12 / N13 是在同一运行时输入契约上串行装配的 3 个判据（3 个 pipeline 层），其数据依赖图为 `R10 → {R12, N13.C}`（R12 是 R10 `double_neg` 的确定性子集；N13.C 转发 R10.kind；N13 消费 R12 命中），故独立证据根 = 1、可用独立乘积因子 ≤ 1。
> 本批 74 行上，`{r10&r12&n13 全 PASS}` 与 `{r10&n13 双 PASS}` 是同一个 18 个 id 的集合，`P(r12=PASS|n13=PASS)=38/38=1`；但这**只是本批语料的观测等式**。它与 `A=B` **不是同一命题**：`A=B` 的正确等价式是 `P(r12=PASS | r10=PASS & n13=PASS)=1`；`P(r12=PASS|n13=PASS)=1` 还额外要求 `(r10=CATCH & n13=PASS & r12=CATCH)` 格为空，而该格在 74 行上恰为 0 也是巧合。观测等式成立依赖 (i) 行 tokens 与 N13 固定三词表一致、(ii) LF 对齐位置、(iii) 命中 token 在 N13 词表内；三者任一破即不成立（本次会话已实跑构造出词表分叉 X1/X2 与 CRLF 错位 X3 两类反例，均同时破集合恒等与 `P(r12=PASS|n13=PASS)=1`）。
> 因此：工程上按 `≤1 层` 计（`numeric=1` 为保守取整约定，非测量值；结构性依据只有依赖图 `:301` + 五检 `:111`，六条理由中其余五条是本 74 行统计佐证）；**不得按 2 层或 3 层相乘**，不得把 `q_r10×q_n13` 或 `q_r10×q_r12×q_n13` 当联合漏报概率；联合漏报上界用 Fréchet `min_i q_i = 1/13`（本 74 行取等），精确值用链式法则 `1/13×1×1`（注意：非 1 因子个数随因子化顺序变，不是自由度计数）；`三层全 PASS` 只表示『三个判据都未触发』，不构成自动放行依据。」**

依据：`_g7_predicates.py:144-145`；`_ei_n13_predicates_src.py:183,196-202,233-245,253-256,307-313`；`_gp_pipeline.py:60-70,76-81`；`_gp_regression.py:141,143`；`EVIDENCE_INDEPENDENCE.md:111,240-250,289-310`；`KEFF_CALC.md:311-340,399-407`；`METRIC_CONVENTION_AUDIT.md:104,108,272`（须改措辞处）；本次会话 §2 / §3.0 / §3.2 / §4.3 实跑。

### 6.3 置信度宣称修正清单（10 项）

> 前提：本次会话判定恒等**不是逻辑必然**（§2.5/§3.2），故编排方「若恒等是逻辑必然」那一支是**反事实**；但清单仍须执行 —— 因为无论恒等性质如何，「三层独立」都不成立，且恒等的偶然性使「R12 零增量」类宣称更须降级。清单含【复核】新增的三项（第 1、9、10 项）。

| # | 落点 | 修正动作 |
|---|---|---|
| 1 | `METRIC_CONVENTION_AUDIT.md:104,108,272`；前件 `:125,146`（§3.0 修正①） | 「不是近似省一层」「决定性集合等式」→ 改「本 74 行观测等式」；**删除「`B⊆A ⟺ P(r12|n13)=1` 是同一命题」**，改「`A=B ⟺ P(r12|r10&r13)=1`；`P(r12|n13)=1` 额外排除 `(r10=C&n13=P&r12=C)` 格，该格为空亦为巧合」；独立性依据改列依赖图 `file:line`，不再把集合等式列为必附条件 |
| 2 | `EVIDENCE_INDEPENDENCE.md:149,294` / `_cs_BASELINE_ALIGNMENT:334` | `38/38=1.000 / 0 bit` → 标「本 74 行观测」，附 `KEFF_CALC.md:315-326` 四种 95% 上界 7.6–9.3% 与本件 §3.2 破口 |
| 3 | `_cs_holdout.py:128` / `_cs_holdout_out.txt:40` / `_csv_holdout_replay.txt:40` / `_cs_info.py:43` | 「R12 不提供任何新信息」「至少一层纯冗余」→ 改「本 74 行上未提供」；去掉全称式 |
| 4 | `CHAIN_VS_SINGLE.md:206,263` / `_cs_BASELINE_ALIGNMENT:213,225,228,266,277` | `≈1～1.3 层（乐观 1.5）`/`≈1～1.5` → 统一 `≤1 层（numeric=1 保守取整）` + 宽 bootstrap 区间 + 「不得自动放行」（`KEFF_CALC.md:418-419,436-443` 已列） |
| 5 | `_ei_07_final.py:89` / `_ei_07_final_out.json:154,157` | 「0.61 层（按后验信息量折算）」→ 改「判别力比值 0.606（概率比口径），非层数」；「2.6 倍」标**未验**（`METRIC_CONVENTION_AUDIT.md:124,213`） |
| 6 | `KEFF_CALC.md:102-104` / `METRIC_CONVENTION_AUDIT.md:96-97,110` | `3.75%` 标注完整：「反事实基线期望，非 2 个独立层联合漏报、非上界」；`3.36%` 标「仅『若真有 3 独立层』的算式」；补一句「链式法则精确值为 `3/39 = 1/13`」 |
| 7 | `KEFF_CALC.md:287-288,293-295` 模板 | 「3 个判据 / 1 个独立证据根」保留；Bayes 2/3 层点值显式加「反事实、无区间、非实测、不得作为置信度宣称」 |
| 8 | `METRIC_CONVENTION_AUDIT.md:209-212`（1.88/2.05/2.07/2.2872） | 四个倍数各自 tag 保留；2.2872 补注「其分母正是把两个条件因子 1 换成边缘 `q_i` 的错置乘积」（§4.3） |
| 9 | 前件 `:110,194,197,236,320,325`（§3.0 修正②） | 「只剩 1 个非 1 因子 / 只有 1 个有效因子 / 不是两个自由度」→ 改「在 `n13` 优先的链式因子化下两个条件因子为 1；非 1 因子数随因子化顺序为 1/2/3，乘积恒 `1/13`，**不能当自由度或独立层数的决定性论据**」 |
| 10 | 前件 `:300` / `EVIDENCE_INDEPENDENCE.md:299-306`（§3.0 修正③） | 「六条结构理由 / 根=1 不依赖 38/38」→ 改「`:301` 依赖图 + `:111` 五检为结构性、单独成立；`:302/:304/:305/:306` 为本 74 行统计佐证，`:302` 的 `0 bit` 挂 38/38，须标观测」；一切 `Πq_i` 与「上界」措辞改 Fréchet `min_i q_i`（`EVIDENCE_INDEPENDENCE.md:252,256` 已自纠）；凡「三层都过 ⇒ 可信 / 可放行」一律禁 |

### 6.4 报层数准则（12 条）

1. **先分四类再开口**：报「判据/层数」必写清是 `pipeline 层` / `独立证据根` / `可用独立因子` / `k_eff 判别力比值` 中的哪一个；禁止裸写「N 层」。
2. **根数用依赖图，不用统计**：给源码 `file:line`（谁调用谁、谁消费谁的返回、谁共用 `tokens`/正则/`extract_spans`），并跑 A1–A5 五检；源节点数即根数。**不得**把 `:302/:304/:305/:306` 的统计量当结构性理由（§3.0 修正③）。
3. **乘积公式必附 H1 状态**：`Πq_i` 只有在「给定 E 条件独立」成立时合法；不成立就用链式法则的条件因子或 Fréchet `min_i q_i`。
4. **条件因子与边缘 `q_i` 分列**：每个因子写 `(事件, 条件类, 分母 N, 数据 SHA)`；禁止用边缘 `q_i` 顶替条件因子（§4.3）。
5. **集合恒等只能作描述**：任何 `A==B` 必须声明「本批语料 / 本谓词 SHA / 本 tokens / 本换行口径」，并给「什么输入会破」的构造或实跑反例；**且必须写对等价式** `A=B ⟺ P(r12|r10&r13)=1`（§3.0 修正①）。
6. **不把观测 0/1 当定理**：零命中给单侧精确/Wilson/CP 上界并分列口径（`KEFF_CALC.md:315-326` 范式）。
7. **契约锁 SHA**：`(predicate_sha, tokens_sha, text_sha, eol)` 逐行登记；CRLF/LF 归一差异列为显式前提（`_gp_pipeline.py:60-70` 的教训）。
8. **层间词表必须对齐**才能计「一致」；`ABSENT` 保持 `ABSENT`，不得折成 `PASS`（`_gp_pipeline.py:113` K7、`EVIDENCE_INDEPENDENCE.md:249` H3）。
9. **k_eff 只报比值**：三口径并列、附 bootstrap/Wilson/CP 区间、标「描述性、不可用于放行」；禁止「折算几层」「0.61 层」措辞。
10. **置信度宣称给区间不给点值**：`P(E|allPASS)` 附先验 π、train=test 声明、CP95；宣称正确率与实测正确率分列，不混 2.05（似然）与 2.07（后验）。
11. **盲留出集为前置**：`ρ=corr(1{err_i},1{err_j})` 需含全部层判定列；缺列即判该结论**未验**（现状 `EVIDENCE_INDEPENDENCE.md:315`）。
12. **负例哨兵机检**：把 `三层独立 / 按 3 层乘 / 0.61 层 / 38/38 为定理 / 两层乘积=联合漏报 / B⊆A⟺P(r12|n13)=1 / 两个自由度 / 只剩 1 个非 1 因子` 列为生成时禁用串；`METRIC_CONVENTION_AUDIT.md:177,283` 记该类哨兵**仍是提案、未实装**。

### 6.5 纪律核验（本次会话实跑）

- 唯一写域 `lead/layer_identity_20261109/`：本次会话**只新建本件 `LAYER_IDENTITY.md`**；未改任何脚本、语料、产物、台账。写域内既有件 `_li_LAYER_IDENTITY_PROOF_20261109.md`（47501 B）与 `_liv_verify.py`（5274 B）只读加载/执行，未写入。
- 十件只读指纹本次会话重算两次（§2.1 与收尾命令）全等编排方基线，`ALL_10_MATCH = True`；七只读目录与两件台账未动。
- `git log -1 --oneline` = `2657458`（实跑，未变）⇒ 未 commit / 未 push；`git status --porcelain -- lead/layer_identity_20261109/` = `?? lead/layer_identity_20261109/`。
- 零真机、零采样代码：所有计算为 `python -I -X utf8 -c` 内联或 `-I -X utf8 <绝对路径 _liv_verify.py>`，只用 `json / re / math / fractions / collections / pathlib / itertools / importlib.util / hashlib / random / tempfile`；无 subprocess、无进程内存、无 hook / MiniDump / SuspendThread / StackWalk / 探针注入 / 动态内存解析。指纹一律 `hashlib.sha256` 现盘重算。
- 绑定行格式：§6.1 的 10 行 + 3 行补测均严格合规（「固定前缀 + 64 位十六进制 + 字节数」三要素，中间无路径/括号/星号/反引号/空格）。
- 本次会话实跑命令与输出要点（可复核清单）：① `python -I -X utf8 -c "<10 件指纹>"` → `ALL_10_MATCH = True`；② `... "<rows 结构+分布>"` → `N 74 / DIST expect CATCH 39 PASS 35`；③ `... "<A/B 逐 id + 条件概率 + 精确分数>"` → `A_n 18 B_n 18 A==B True`、`den 38 num 38 ratio 1`、`q10 19/39 q12 35/39 q13 1/13`、`chain/prod3 1521/665 2.287218045112782`；④ `... "<逐 id 打印 18 行>"` → `union ids n= 18 / A-only [] B-only []`；⑤ `... "<逻辑等价 + 8 真值格局>"` → `forbidden sets equal (theorems)? False`；⑥ `... "<6 排列链式法则>"` → `prod=1/13` 恒等、非 1 因子 1/2/3；⑦ `python -I -X utf8 "D:/…/_liv_verify.py"` → `X1/X2/X3 BROKEN`、`combos=180 broken=0`、`prior_lines=1/2/3 violations=10/10`、`r12=CATCH=1200 violations=0`、`not_subset n=19`；⑧ `... "<judge 反例 破P不破B⊆A>"` → `r10=CATCH r12=CATCH n13=PASS | B-subset-A violated=False | n13P&r12C=True`；⑨ `... "<X3 位置展开>"` → `r12 hits [('已入账', 13)]` / `n13 gpos=12 kind=A`；⑩ `... "<CRLF 归一 + 9 件读盘>"` → `read_text CRLF repr = 'line1\nline2\n'` / 9 件 `CRLF= 0`；⑪ `... "<10 份文档强模式普查>"` → 逐份命中数见 §4.1；⑫ `... "<写域行数 + git>"` → `bytes 47501 lines 400` / `2657458`。

### 6.6 未验项（逐条如实列，不补造）

- **真机运行态**：铁律零真机（`gamemd.exe` / `ra2loader` / `YURI.exe`、活进程内存）⇒ **未验**。
- **生产语料上恒等是否成立 / `q_i / c_i / ρ / k_eff` 的泛化**：74 行 train=test 且含定向构造对抗样本；X1/X2/X3 是**构造输入**，不是生产观测 ⇒ **未验**（`EVIDENCE_INDEPENDENCE.md:310,316`）。
- **CRLF 破口在生产链上是否可达**：本次会话实跑 `read_text` 归一 CRLF→LF、9 件读盘真件 `CRLF=0`；是否存在内联/直接文本入口 ⇒ **未验**。
- **X1/X2 加入同款语料后整体统计量变化**：本次会话只跑谓词直调，未重跑 `_gp_regression.py` 全 74+2 行、未重算 `q_i`/k_eff/CI；铁律不改语料/产物 ⇒ 设计实验，**未验**。
- **盲留出集误差相关双检**：`_cs_holdout_out.json` 缺 r10/r12 列且 3 条逐字重复（`EVIDENCE_INDEPENDENCE.md:157,315`）⇒ **未验**。
- **改谓词 / 补正交层 / 修 CRLF 归一后的效果**：全部为设计、未实装（`CHAIN_VS_SINGLE.md:210`、`EVIDENCE_INDEPENDENCE.md:321`）⇒ **未验**。
- **`2.6 倍`、`4.4474` 等错置数的确切构造**：沿用 `METRIC_CONVENTION_AUDIT.md:124,213,294` 的「未验，不补造」。
- **两件台账其它论域「独立证据」措辞**：本次会话只做 10 份文档强模式普查（两件台账 0 命中），未全仓逐行普查 ⇒ **未验**（`KEFF_CALC.md:445-455` 检索范围内无本论域条目）。
- **【复核】的两条升级条件**：① 代码级证明「`(r10=CATCH & n13=PASS & r12=CATCH)` 在任何输入下不可达」；② 证明 X1/X2/X3 类输入在生产契约（固定 tokens=T、LF 归一、无内联文本入口）下全部不可达 —— 本次会话**未做**全称证明 ⇒ **未验**。若成立，瑕疵①消失 / 主结论翻转（如实记，不预判）。
- **k_eff 点值与 bootstrap 区间的本次会话重算**：只引用 `KEFF_CALC.md:139-147,191-200` 与前件 `#21` 记载，本次会话**未重跑** ⇒ 该重算 **未验**。
- **`_gp_regression_out.json` 的生成过程归属**：本次会话以现盘 SHA `d3543657…` 重算全等，但**未重跑生成脚本** `_gp_regression.py`（只读）⇒ 生成过程 **未验**。
- **前件自报 25 条 Bash / §0 #7 路径占位失败登记**：本次会话未逐条核对该计数 ⇒ **未验**（【复核】亦记「本复核未验证」）。
- **本件自身 verdict**：未请求第三方复核，不自行标 `confirmed`；前件 `partial` 按规则标 **`unconfirmed`**。

---

*本件结束。所有「实跑」均为本次会话内执行的命令；所有「文件:行」均为本次会话内 Read / grep 实读。未跑项一律标「未验」，未把任何未验写成通过。*
