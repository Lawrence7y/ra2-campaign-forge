# PVALUE_RECALC.md

p 值重算件（交付件）。六节 `## 1`…`## 6`；只做重算与推导，未改任何既有脚本、语料、产物。
本会话零真机（未启动 gamemd.exe / ra2loader / YURI.exe，未 taskkill，未读活进程内存）、零采样（未写 hook / MiniDump / SuspendThread / StackWalk / 探针注入 / 动态内存解析）、不 commit 不 push。
唯一写域：`lead/pvalue_recalc_20261109/`。本件即写在该域内，文件名 `PVALUE_RECALC.md`。

---

## 1 目的与边界

**目的**：对冻结 68 条考题上两版 `chain` 列的配对增益（b=18 / c=0）重算 p 值，核实基线、给出三口径 p 与数量级对比、评估设计效应与循环论证，产出唯一站得住的表述。

**边界（铁律，逐条照录执行）**：

- 只做重算与推导，**不改任何脚本、语料、产物**。只读域 `lead/score_decomp_20261109/`、`lead/comparability_20261109/`、`lead/gate_pipeline_20261109/`、`lead/chain_vs_single_20261109/`、`lead/evidence_indep_20261109/`、两件台账（`lead/PENDING_DECISIONS.md`、`lead/GOAL_THREE_TARGETS_20261018.md`）一律未修改、未追加、未覆盖。
- 引用追到「实跑命令+输出」或「文件:行」；拿不到写「未验」，不补造。
- **不许为了让 p 值好看而选宽松口径。宁可给「不显著」也不要给「边缘显著」。**
- 复核回件含固定格式绑定行：`被核对象 SHA256 = <64 位十六进制>，字节数 = <数字>`，中间不插路径、括号、星号、反引号或空格。

**本会话实跑命令清单**（全部 `python -I -X utf8`，绝对路径；指纹用 `hashlib`）：

| 代号 | 实跑命令（要点） | 输出要点 |
|---|---|---|
| V0 | `python -I -X utf8 -c "<8 件 hashlib sha256+len>"` | `FINGERPRINT_MATCH = 8 / 8` |
| V1 | `python -I -X utf8 -c "<从两份 JSON 原始 rows 自建冻子集，重算 b/c/文本/族/FP>"` | 见 §2，`b = 18 c = 0 n_discordant = 18` |
| V2 | `python -I -X utf8 -c "<math.comb+Fraction exact binomial / CP / Wilson / 数量级 / 设计效应 / bootstrap>"` | 见 §3 §4 |
| V3 | `python -I -X utf8 -c "<按行号读 _gp_pipeline.py / COMPARABILITY_AUDIT.md / SCORE_DECOMP.md / GATE_PIPELINE_COMPOSE.md>"` | 见 §5 文件:行 |
| V4 | `python -I -X utf8 -c "<ρ̄ 机制依据 / GP-C03≡GP-A1 文本 / 反向行>"` | 见 §4 §5 |
| V5 | `python -I -X utf8 -c "<会话末 8 件 hashlib>"` | `SESSION_END ZERO_DRIFT = 8 / 8` |
| V6 | `python -I -X utf8 -c "<CP 下界二项尾校验>"` | `P(X>=n|lo)=0.025 ? True`（三口径） |
| V7 | `git rev-parse HEAD` | `26574589aa8401e8f3f2934680a1ea7109bafa2d`（与会话开始快照一致，无 commit/push） |

> 说明：V1/V2/V4/V6 为 `python -I -X utf8 -c` 内联实跑，不写脚本文件；未 import 任何上游 `_pv_*` / `_pvv_*` 脚本，故为独立重算。原始输入为两份只读 JSON 的 `rows[]`：`lead/gate_pipeline_20261109/_gp_regression_v1_union_out.json`（72 条，v1 并集版）与 `_gp_regression_out.json`（74 条，v2 逐 span 版）。

---

## 2 上游指纹（八件）+ 基线复核

### 2.1 八件上游指纹（V0 会话始 + V5 会话末，两轮 hashlib 均 8/8 相符，零漂移）

与编排方【编排方指纹】逐位相符。会话末 `SESSION_END ZERO_DRIFT = 8 / 8`。

| # | 文件 | sha256 | 字节数 |
|---|---|---|---|
| 1 | `lead/score_decomp_20261109/SCORE_DECOMP.md` | dfe7f68692eb7ae752358782acaaa1fc5a42ecbd0a6930205e0dcfe4f6544dcb | 42573 |
| 2 | `lead/score_decomp_20261109/_sd_report.md` | 58e71cefc024d6874b353cde69d1b39b450f4a79ad08c35e9d235c01dbd725ff | 49202 |
| 3 | `lead/comparability_20261109/COMPARABILITY_AUDIT.md` | c00833b3fef5b8b5f93cdfd9d5223f22149878dd868200c1a070d76e553d8ae1 | 51927 |
| 4 | `lead/gate_pipeline_20261109/_gp_regression_out.json` | d3543657aa4f9914c9023710f6daef8348a12ca0aa11957110e8b7c45baec6fe | 38575 |
| 5 | `lead/gate_pipeline_20261109/_gp_regression_v1_union_out.json` | 68c7ecd3aafc94be87092bf65f1e3d05ab28cc5a20de5193117f994882e16358 | 37461 |
| 6 | `lead/chain_vs_single_20261109/_cs_BASELINE_ALIGNMENT_20261109.md` | 3397c1c41b0a81e85699f07ce608b9b13e0ab45cba51280a3e78883581768ed2 | 49850 |
| 7 | `lead/PENDING_DECISIONS.md` | 3765eddbe96deeb65eeb1f05dc81e1dc171e7ea3b2c826e2692a1d15e1c8f2d7 | 52419 |
| 8 | `lead/GOAL_THREE_TARGETS_20261018.md` | 2baa0de45d4125549262eb595d7518c9ce99efeee120384bf640cded8a933ede | 759518 |

### 2.2 基线复核（V1 独立重算，逐字输出）

```
nA= 72 nC= 74 common= 71 onlyA(72-only)= ['GP-C03'] onlyB(74-only)= ['GP-A1', 'GP-A2', 'GP-A3']
flips(expect changed)= 3 ['GP-C05', 'GP-C06', 'GP-C07']
n_frozen= 68
frozen chain72 ok = 48 chain74 ok = 66 delta = 18
paired b = 18 c = 0 n_discordant = 18 b-c == delta ? True
gains = 18 losses = 0
all gains expect==PASS ? True
all gains 72CATCH->74PASS ? True
n_distinct_texts = 16 of 18
families = {'N13_POS': 12, 'R10_CTX': 5, 'REAL3': 1} n_families = 3
72 FP in frozen = 20 74 still FP = 2 ['REAL-SLOT', 'REAL-TRUTH']
repaired = 18 gains set == repaired set ? True
```

- **配对基线**：`b=18`、`c=0`、`n_discordant=18`；`b-c == frozen delta`（18−0=66−48=18）成立。
- **全单元 p 算式**：exact binomial 双侧（小 p 值法，H0:p=0.5）
  `p = min(1, 2·P(X≥18 | Bin(18,0.5))) = 2×2^-18 = 2^-17 = 1/131072 = 7.62939453125e-06`（简写 `7.629e-06`）；单侧 `= 2^-18 = 3.814697265625e-06`。
  与 `SCORE_DECOMP.md:157` 及 `COMPARABILITY_AUDIT.md:335` 的 `paired b=18 c=0 p_2sided=7.62939453125e-06` 一致（算式本会话 V2 实算复现）。
- **16 文本 / 3 族**：18 条增益仅 16 个独立 `text_head`（2 组逐字重复：`### 1(c) 有没有已入账的？` → `N13-P01` / `R10-CTX-10`；`**已入账核查实跑命令**：` → `N13-P05` / `R10-CTX-07`），聚 3 族 `{N13_POS:12, R10_CTX:5, REAL3:1}`。与 `SCORE_DECOMP.md:171` 相符。
- **配对正确率差** `18/68 = 0.2647058823529412`；V2 bootstrap 200000 次 / seed=20261109 percentile 95% CI `= [0.16176470588235295, 0.36764705882352944]`，与 `SCORE_DECOMP.md:161-162` 一致。

### 2.3 GP-A1/A2/A3 的 chain 值（口径更正，V1 实跑）

```
74-only row GP-A1 expect= CATCH chain= PASS naive/r10/r12/n13= ['CATCH', 'PASS', 'PASS', 'PASS']
74-only row GP-A2 expect= CATCH chain= PASS naive/r10/r12/n13= ['PASS', 'PASS', 'PASS', 'PASS']
74-only row GP-A3 expect= CATCH chain= PASS naive/r10/r12/n13= ['PASS', 'PASS', 'PASS', 'PASS']
72-only row GP-C03 expect= CATCH chain= PASS naive/r10/r12/n13= ['CATCH', 'PASS', 'PASS', 'PASS']
```

- 三行在 **74 版**全部 `expect=CATCH`、`chain=PASS`、`r10=PASS`、`r12=PASS`、`n13=PASS`；**任务书「74 版 chain 是 CATCH」的前提为错**，本会话实跑证伪。
- 三行是 **74 版 onlyB**，72 版**无同名行** ⇒ 「两版 chain」字面不成立；72 侧仅 `GP-C03` 与 `GP-A1` 的 `text_head` 相等（V4 实跑 `GP-C03[72] text_head == GP-A1[74] text_head ? True`），`GP-A2/A3` 在 72 版无对照行（**未验/不存在**）。
- 三行不在 frozen68 内（属 onlyB 且另有 3 条翻标被剔除），**不参与 b/c 与任一 p 的计算**。

> ★ 如实登记标签瑕疵：撰写人回件 C3 段与 `_pv_PVALUE_RECALC.md:1(a)` 把 `onlyA/onlyB` 写反（实际 `onlyA=['GP-C03']` 为 72 独有、`onlyB=['GP-A1','GP-A2','GP-A3']` 为 74 独有）。集合本身正确，不影响 b/c、n=18/16/3 及任一 p。本件以 V1 实跑为准。

---

## 3 三口径 p（各自 p 与 CI + 数量级对比表 + 哪个最正当与理由）

### 3.1 三口径数字（V2 独立实算；CP 下界另由 V6 二项尾校验）

统一方法：exact binomial 双侧（小 p 值法 `p=min(1, 2·2^-n)`，因 k=n 全同向）+ Clopper-Pearson 95% 双侧 CI（k=n 时下界闭式 `(α/2)^(1/n)`、上界 `1.0`）+ Wilson 95% CI。`α=0.05`。

| 口径 | 分析单元 | n | 双侧 exact p | 单侧 p | CP95 | Wilson95 | CP/Wilson 下界包 0.5？ | 判定 |
|---|---|---|---|---|---|---|---|---|
| 全单元 | 18 条增益行 | 18 | `1/131072 = 7.62939453125e-06` | `3.814697265625e-06` | `[0.8146980318621477, 1.0]` | `[0.8241207763533425, 1.0]` | 否 / 否 | 名义显著，但独立性假设被证伪 |
| 独立文本 | 16 个独立 `text_head` | 16 | `1/32768 = 3.0517578125e-05` | `1.52587890625e-05` | `[0.7940927857921772, 1.0]` | `[0.8063923194655637, 1.0]` | 否 / 否 | 名义显著，仍非独立观测 |
| 族级 | 3 个族 | 3 | `1/4 = 0.25` | `0.125` | `[0.2924017738212866, 1.0]` | `[0.4385029682449546, 1.0]` | **是 / 是** | **不显著**（α=0.05） |

V6 校验逐字：`n= 18 CP_lo= 0.8146980318621477 P(X>=n|lo)= 0.02499999999999999 = 0.025 ? True`；`n= 16 … 0.024999999999999988 … True`；`n= 3 … 0.025000000000000005 … True`。仅族级 CI 下界把 0.5 包进去 ⇒ 仅族级不显著。

### 3.2 数量级对比表（V2 实算）

| 对比 | 倍数 | 2 的幂 | log10 差 | 结论 |
|---|---|---|---|---|
| 族级 / 全单元 | `0.25 / 7.62939453125e-06 = 32768.0` | `2^15` | `4.515449934959718` | 跨 **≈4.515 个数量级**，从「极显著」翻成「不显著」 |
| 独立文本 / 全单元 | `3.0517578125e-05 / 7.62939453125e-06 = 4.0` | `2^2` | `0.60206` | 抬 4 倍，仍显著（但口径仍不成立） |
| `1 / p_all` | `131072.0` | `2^17` | `5.11750992628768` | 供 §4「抬到 1.0」比较 |
| 配对正确率差 | `18/68 = 0.2647058823529412` | — | — | bootstrap CI `[0.16176470588235295, 0.36764705882352944]` |

### 3.3 哪个最正当（★ 不许挑宽松口径）

**报【族级 `n=3, p=0.25（不显著）`】作为证据强度的上界；绝不以 `n=18` 或 `n=16` 作结论。** 更进一步：**三个口径没有一个能当推断性 p 用**。

理由（V1/V2/V4 实跑 + 文件:行）：

1. **独立性假设被直接证伪**：18 条只有 16 个独立 `text_head`（`SCORE_DECOMP.md:171`），且 18 条清一色 `expect=PASS`、清一色 `72:CATCH→74:PASS`、反向 0 条（V1 `gains = 18 losses = 0`、V4 `reverse-direction rows (losses) = 0`）、18/18 的单层+chain 模式**完全相同**（V4 `distinct patterns = 1`：`('PASS','CATCH','CATCH','PASS','PASS','PASS')`），全属同一 K3+K9 分支（V1 `all 18 gains r10=CATCH and n13=PASS ? True`；`_gp_pipeline.py:168-171`）。全单元/独立文本口径所需的「独立同分布 Bernoulli 试验」不成立。
2. **族级是三者中 p 最大（最不显著）的口径**，且是唯一把「同一机制/同一失败形态」合并计数的口径（`SCORE_DECOMP.md:183`、`COMPARABILITY_AUDIT.md:344`）。按「宁可给不显著」，只能取它。
3. **post-selection 下连族级也不是推断性 p**：18 条是 K9 为消 20 条 FP 定向修复的样本（§5），`n_eff≈1`（§4），真实 p **无定义/未验**。`SCORE_DECOMP.md:179` 明写「in-sample 偏差不能靠给 p 乘常数修好，`2^-18` 的抽样模型本身失效」；`:187` 要求把 p 降格为「描述性内部效度指标」。

**结论**：`7.62939453125e-06` 只是**未校正的描述性内部一致性指标**，不得作为显著性或泛化证据。禁止「边缘显著」「趋势向好」「近似显著」等软化措辞（与 `_pv_PVALUE_RECALC.md:260` 同向）。

---

## 4 设计效应

### 4.1 公式与全表（V2 实算）

`n_eff = n / (1 + (n−1)·ρ̄)`，`n = 18`，`deff = 1 + (n−1)·ρ̄`。`n_eff` 非整数，代回 exact binomial 时用 `floor(n_eff)`（保守取整）作**量级示意**。

| ρ̄ | n_eff | deff | floor(n_eff) | 对应双侧 p（`k=floor`） |
|---|---|---|---|---|
| 0.0 | 18.0000 | 1.0 | 18 | `7.62939453125e-06` |
| 0.3 | 2.9508 | 6.1 | 2 | `0.5` |
| 0.5 | 1.8947 | 9.5 | 1 | `1.0` |
| 0.8 | 1.2329 | 14.6 | 1 | `1.0` |
| 0.9 | 1.1043 | 16.3 | 1 | `1.0` |
| 1.0 | 1.0000 | 18.0 | 1 | `1.0` |

与编排方【重算结果】`design_effect` 数组 4 位小数逐项一致，与 `SCORE_DECOMP.md:184` 一致。

### 4.2 ρ̄ 取值依据（取 **1.0**，保守上界；真值 **未验**）

- V1/V4 实跑：18 条增益 `expect` 清一色 PASS、`72:CATCH→74:PASS` 清一色、方向零反向、`all 18 gains r10=CATCH and n13=PASS ? True`（正是 `_gp_pipeline.py:168` 的 K3 条件）、18 条单层+chain 模式 `distinct patterns = 1`；20 条 V1 FP 亦全部 `r10=CATCH/n13=PASS`。⇒ 同一分支、同一失败形态、同一修复机制、同一批被选中样本。
- 文件:行：`SCORE_DECOMP.md:104,251`（18/18 追到 K3+K9，**本会话未重跑该逐行重放**，标未验/引用）、`_gp_DESIGN.md:287`（「为了让 N13 的 A/B 精筛压过 R10 的宽进（消掉 20 条 FP）」）、`COMPARABILITY_AUDIT.md:219,344`（「为消 20 条 FP 而写」「in-sample 调参收益」）。
- **诚实限定**：18 个结果全同向使簇内方差为 0，经验 ICC 严格说退化/不可估；`ρ̄` 无调参日志、无 18 行逐行重放（`SCORE_DECOMP.md:185,291` 列为未验），故 `ρ̄=1.0` 是**保守取值而非实测**。取定义域上界 1 不会低估设计效应，符合「宁可给不显著」。

### 4.3 有效样本量与对应 p

`ρ̄=1.0 ⇒ n_eff = 18/18 = 1.0`；双侧 `p = min(1, 2·P(X≥1 | Bin(1,0.5))) = min(1, 2×0.5) = 1.0`（V2 实算 `rho=1 -> n_eff = 1.0 p_two(n_eff=1,k=1) = 1.0`）。

> 限定：`n_eff` 非整数，代回 exact binomial 只是量级示意；post-selection 下**推断性 p 无定义**（修正后真实 p = **未验**，不补造）。

### 4.4 「p 被抬到什么程度」（V2 实算）

- 从 `7.62939453125e-06` 抬到 `1.0`：`1/7.62939453125e-06 = 131072.0` 倍，`log10 = 5.11750992628768`（≈**5.12 个数量级**）。**显著性被完全抹掉**。
- 保住名义 `p<0.05` 的阈值（V2 实算）：
  `2·2^-n_eff < 0.05 ⇒ n_eff > log₂40 = 5.321928094887363`；
  连续外推 `ρ̄ < 0.14013134380964332`；按整数 `n_eff ≥ 6` 需 **`ρ̄ ≤ 2/17 = 0.11764705882352941`**。
  本例 `ρ̄≈1` 远超阈值 ⇒ **任何 ≥0.1176 的簇内相关都足以把结论翻成「不显著」**，无需争辩 ρ̄ 精确值（与 `_pv_PVALUE_RECALC.md:197` 同向）。

---

## 5 循环论证评估

### 5.1 K9 是否为消这 20 条 FP 而写 —— **是**（源码 + 设计件 + V1 独立重算三重可证）

- 源码直读 `_gp_pipeline.py:168-171`：
  ```
  168 |             elif n13_v == "PASS" and r10_v == "CATCH":
  169 |                 # K3：A/B 放过 vs R10 抓住，输入契约不同
  170 |                 if n13_veto:
  171 |                     verdict = "PASS"; rule += ["K3", "K9"]   # K9 精筛覆盖宽进
  ```
  `_gp_pipeline.py:151-153` 给 `n13_veto` 的 A/B 条件。
- 设计件 `_gp_DESIGN.md:259`（K9 定义「K3 且 N13=A/B、该 span 有微段内标记、该行无 D → PASS（精筛覆盖宽进）」）、`:287`「为了让 N13 的 A/B 精筛压过 R10 的宽进（**消掉 20 条 FP**）」、`:344-352`（第一版并集 `chain 正确=48 FP=20`；「20 条新增误报全部来自『N13 已判 A/B 放过、R10 宽进仍报 assertion』…第二版改为逐 span 裁决后 FP 降到 2」）。
- `GATE_PIPELINE_COMPOSE.md:431` 同向（20 条全为 `r10=CATCH/n13=PASS`、FP 降到 2，并如实标「第一版脚本未留盘…未重跑、标未验」）；`COMPARABILITY_AUDIT.md:219`（「本次 K9『精筛覆盖宽进』是为消 20 条 FP 而写」）、`:344`（「18 条全正向、0 条反向：正是设计 K9 时点名的失败形态 ⇒ in-sample 调参收益」）。
- V1 独立重算逐字：`72 FP in frozen = 20 74 still FP = 2 ['REAL-SLOT', 'REAL-TRUTH']`、`repaired = 18 gains set == repaired set ? True`、`all 20 V1 FP r10=CATCH & n13=PASS ? True`。即 **18 条增益集合 ≡ 20 条 FP 被修好的 18 条**，一一对应。

⇒ **循环论证成立**：`SCORE_DECOMP.md:170`「K9 为消 20 条 FP 而写…18 条正是点名失败形态 ⇒『照着答案改完的答案对上了』是循环论证」。

### 5.2 p 还有无意义 —— **无推断意义，仅描述/回归意义**

- 抽样模型失效：`SCORE_DECOMP.md:179`「18 条不是从目标总体独立抽的，是被 K9 失败清单选出的」，`2^-18` 的抽样模型本身失效，不能靠乘常数修正（`:179`）。
- 唯一有内部效度的因果陈述（`COMPARABILITY_AUDIT.md:340`）：「在这 68 条冻结考题上，把合成裁决从『三层 problems 朴素并集』换成『逐 span K1–K9』只做了一件事——把 18 条应放行样本从误拦改为放行，正类召回一条没动」。这是**回归/描述**陈述，不是「算法更好」的推断。
- 对照物不是「更好」：`SCORE_DECOMP.md:172`（frozen68 内 74 版 `chain 66/68` 仍劣于 `n13 68/68`，`b=2 c=0 p=0.5` 不显著）、`COMPARABILITY_AUDIT.md:346`。

### 5.3 post-selection 信息量

- 条件分布：在「已知这 18 条是 K9 失败样本」条件下观测 18/18 修好的概率 **≈1**，自信息 **≈0 bit**（`SCORE_DECOMP.md:186`；`_pv_PVALUE_RECALC.md` 同向）。似然比不可识别（无独立留出集、无预注册、调参次数 M 无日志，`SCORE_DECOMP.md:185` ⇒ M **未验**，不得反推「p 仍稳健」）。
- 如实补充：定向失败集实测修复率 `18/20 = 0.9`（V4 实算 `repair rate on targeted failure set = 18/20 = 0.9`），剩 `REAL-SLOT` / `REAL-TRUTH` 仍 FP —— 这是对「K9 覆盖不全」的信息，**不是**对「算法更好」的支持。
- 修正后真实 p = **未验**（不补造，`SCORE_DECOMP.md:187,291`）。

### 5.4 应如何表述

把 `p` **降格为「描述性内部效度指标」**，同时给 `n_eff≈1`、族级 `p=0.25（不显著）`、三口径并列、post-selection 状态、盲留出「未验」；**不得把 `p=7.63e-06` 单独写成显著性证据**（`SCORE_DECOMP.md:187,275`）。禁止「算法更好」「优于单层」「可作为显著性」等表述。

---

## 6 复核回件（绑定行）+ 结论 + 未验项

### 6.1 复核 verdict 如实登记

编排方【复核】给出 `verdict = "confirmed"`，`ranCommands = 22`，`sha256Line` 为第 1 件绑定行；其七项点名检查（八件指纹、三口径独立重算、是否挑宽松口径、ρ̄ 取值依据、K9 定向关系、唯一站得住表述、越界检查）逐项判过。本件照录为 **`confirmed`**（非 `refuted`、非 `partial`，故不标 `unconfirmed`）。

复核方同时如实登记 5 处瑕疵（不掩盖、不改 verdict）：① 撰写人 `evidence` 自报的报告 sha256 `7ac03e66…` 为终检时点中间值，复核方实算盘上当前值 `277df9910d4611e0072faf83bd65e3639667a01b511191d5f74b575e448911ac` / 29780 B（撰写人已主动披露「其后 §7 措辞微调、最终值未再复算」）；② `_pv_recompute.py` 的 `cp_two_sided()` 二分判反，`_pv_recompute_out.txt` 的 `CP95 = [3.111507638930571e-61, …]` 作废，已另建 `_pv_ci_check.py` 重算，本件全部 CI 取 V2/V6 独立实算；③ `common = 71 onlyA/onlyB` 在 C3 与报告 §1(a) 写反（§2.3 已更正）；④ `_pv_final_checks_out.txt` E 段自列为 `0 B`（tee 截断自观察）；⑤ 复核方同样未重跑 18/18 逐行 K3+K9 重放、未验 ρ̄ 真值 / M / 修正后真实 p。

### 6.2 ★ 复核回件绑定行（固定格式，8/8）

被核对象 SHA256 = dfe7f68692eb7ae752358782acaaa1fc5a42ecbd0a6930205e0dcfe4f6544dcb，字节数 = 42573
被核对象 SHA256 = 58e71cefc024d6874b353cde69d1b39b450f4a79ad08c35e9d235c01dbd725ff，字节数 = 49202
被核对象 SHA256 = c00833b3fef5b8b5f93cdfd9d5223f22149878dd868200c1a070d76e553d8ae1，字节数 = 51927
被核对象 SHA256 = d3543657aa4f9914c9023710f6daef8348a12ca0aa11957110e8b7c45baec6fe，字节数 = 38575
被核对象 SHA256 = 68c7ecd3aafc94be87092bf65f1e3d05ab28cc5a20de5193117f994882e16358，字节数 = 37461
被核对象 SHA256 = 3397c1c41b0a81e85699f07ce608b9b13e0ab45cba51280a3e78883581768ed2，字节数 = 49850
被核对象 SHA256 = 3765eddbe96deeb65eeb1f05dc81e1dc171e7ea3b2c826e2692a1d15e1c8f2d7，字节数 = 52419
被核对象 SHA256 = 2baa0de45d4125549262eb595d7518c9ce99efeee120384bf640cded8a933ede，字节数 = 759518

### 6.3 结论：唯一站得住的表述（一句话）

> 在这 68 条冻结考题上，两版 `chain` 列有 18 处不一致且全部朝同一方向（72 误拦 → 74 放行，`expect` 全为 PASS）；这 18 处是 K9 为消 20 条 FP 而定向修复的样本，只含 16 个独立文本、聚 3 族，`ρ̄≈1` 使 `n_eff≈1`，族级符号检验 `p=0.25`（不显著）、设计效应下名义 `p≈1.0`，故**不存在可用于推断算法优劣的有效 p 值**；`7.62939453125e-06` 只是未校正的描述性内部一致性指标，不得作为显著性或泛化证据。

（与编排方【重算】`correctedP` 的唯一一句话表述、`_pv_PVALUE_RECALC.md:242` 一致。）

### 6.4 提到可信水平需要什么新数据（**方案，本会话未执行，标未验**）

依据 `COMPARABILITY_AUDIT.md:354-362`、`SCORE_DECOMP.md:181,283`：

1. **一次性出题 + 盲留出**：按域 × expect 分层配额，`train/dev/test` 物理隔离；test 封 SHA、双盲标注、Cohen's **κ ≥ 0.8**；出题人 ≠ 改规则人 ≠ 批卷人；N19–N26 / GP-A 只进 train、**禁进 test**；test 一次性使用。
2. **预注册**：在看到 test 结果前冻结标注手册、评分公式、分析单元、p 口径与 α；记录调参次数 M（当前 M **未验**）。
3. **单轴全列重跑**：五轴 `S/G/I/E/M` 每侧 `path+sha256+bytes` 入 manifest；两格都实跑、不复用旧列；统一 `tokens` 输入契约（修 `COMPARABILITY_AUDIT.md:221,343` 的 E 轴未验 / M 轴列定义变更）；逐行全列可配对。
4. **配对统计与不确定性**：在 test 上重算 b/c、exact binomial 双侧 p、bootstrap CI、macro-F1、按 expect/族分层条件错误率；`p>0.05` 只写「未检出差异」。
5. **独立复核**：第三方按同一 manifest 复现、逐字节比对、独立跑断言得同一 verdict；未经复核不得进入报告。

### 6.5 报 p 必附清单（缺项不得发布）

基础 18 项见 `SCORE_DECOMP.md:283`（五轴 manifest / 冻结语料 / 冻结标注手册 / 冻结评测脚本 / 冻结依赖 / 变更单 / 全列重跑 / 统一输入契约 / 可比性 verdict / 配对统计 / 归因范围 / 分母口径 / 留盘复现状态 / 盲留出 / 逐分逐行归因 / 选择过程与 n_eff / 兜底机制披露 / 收尾零漂移）。本任务**必须补齐的 ★ 项**：

1. **★ 三口径 p 并列**：全单元 `n=18 p=7.62939453125e-06`、独立文本 `n=16 p=3.0517578125e-05`、族级 `n=3 p=0.25（不显著）`，及各自 CP/Wilson CI；**禁止只报最宽松那个**。
2. **★ 独立单元核对**：18 条 → 16 个独立 `text_head`（列 2 组逐字重复及 id）、3 族 `{N13_POS:12, R10_CTX:5, REAL3:1}`。
3. **★ 方向分布**：`b=18 / c=0 / n_discordant=18`，全为 `expect=PASS`、全为 `72:CATCH→74:PASS`、反向 0 条。
4. **★ ρ̄ 依据与 `n_eff` 全表**：六档 `n_eff`（§4.1）、`ρ̄=1.0` 为保守上界（非实测）、`n_eff=1.0 → 名义 p=1.0`、`ρ̄ ≤ 2/17 ≈ 0.1176` 阈值。
5. **★ post-selection 状态**：K9 为消 20 条 FP 而写、18 条 = 20 条 FP 修好的 18 条、`P(18/18|入选失败集)≈1`、信息量 ≈0 bit、修复率 18/20=0.9。
6. **★ 不显著措辞**：`p ≥ 0.05` 一律写「未检出差异」；禁止「边缘显著」「趋势向好」「近似显著」「几乎显著」「显著改善」「算法更好」。
7. **★ E 轴 / M 轴 / 盲留出 / 修正后真实 p 一律标「未验」**，不得补造。
8. **★ 八件上游指纹绑定行**（§6.2 固定格式）与会话末零漂移结论（本会话 `8 / 8`）。

### 6.6 未验项（不补造）

- **72 版 v1 并集生成脚本**：全仓 / git 零命中（`COMPARABILITY_AUDIT.md:343`、`GATE_PIPELINE_COMPOSE.md:431,465`），标「未验重跑」；本会话只读其产物 JSON。
- **18/18 逐行 K3+K9 `resolve_conflicts` 重放**：本会话未跑（引用 `SCORE_DECOMP.md:104,251`）。
- **ρ̄ 真值、调参次数 M、post-selection 修正后真实 p**：无日志 / 无留出集（`SCORE_DECOMP.md:185,291`），一律未验。
- **3 条翻标（`GP-C05/C06/C07`）绝对正确性**、**`text_head` 第 91 字后正文**、**`GP-A2/A3` 的 72 版对照**（不存在 / 未验）。
- **上游 74 条完整对齐实验 `b=0 c=3 p=0.25`**（`CHAIN_VS_SINGLE.md:112`，引用未重跑）；`_cmp_assert.py` 修正版未实装。
- **E 轴「其余输入相同」**：仅由四单层列逐行相同反推（V4 实跑 `all frozen single-layer cols identical across versions ? True`），非脚本级复核（`COMPARABILITY_AUDIT.md:343`）。
- **真机 / 运行时行为**：铁律所限，零真机零采样，未做。
- **写到可信水平所需新数据（§6.4 全套方案）**：本会话未执行，标未验。

### 6.7 零漂移与越界声明（V5 / V7 实跑）

- `SESSION_END ZERO_DRIFT = 8 / 8`（会话始 V0 与会话末 V5 两轮 hashlib 全相符）。
- `git rev-parse HEAD` = `26574589aa8401e8f3f2934680a1ea7109bafa2d`，与会话开始快照一致 ⇒ 无 commit / 无 push。
- 本件只写在 `lead/pvalue_recalc_20261109/PVALUE_RECALC.md`；未修改、追加、覆盖任何只读域文件或两件台账；未改任何既有脚本、语料、产物（含写域内既有的 `_pv_*` / `_pvv_*` 文件，本会话全程未写入）。

---

**severity = high**：三口径 p 中唯一正当的族级口径给出 `p=0.25（不显著）`，设计效应把名义 `p` 抬到 `1.0`，循环论证使 post-selection 下推断性 p 无定义；`7.62939453125e-06` 必须降格，不得作显著性或泛化证据。
