# KEFF_CALC.md — k_eff 三口径、小样本区间、三层真实置信度与 R12 零增量评估

> 本件为**计算与推导交付件**。唯一写域 `lead/keff_calc_20261109/`。
> 主独立实跑（本任务内执行，EXIT=0）：
> `python -I -X utf8 -B D:/Project/ra2-campaign-forge/lead/keff_calc_20261109/_kc_verify.py`
> → 输出留盘 `lead/keff_calc_20261109/_kc_run_console.txt`（119 行）、`_kc_verify_out.json`、`_kc_run_console.txt`（控制台同文）。
> 另有前序同写域实跑件（本任务读取、未改）：`_ke_calc_stdout.txt`（173 行，`_ke_calc.py` 主计算）、
> `_ke_REPORT.md`、`_ke_calc_out.json`、`_kev_run_console.txt`（复核件）、`_kev_verify_out.json`。
> 指纹一律 `hashlib.sha256` 现盘重算；Python 一律 `python -I -X utf8` + 绝对路径。

---

## 1 目的与边界

**目的**：把「R10/R12/N13 三层一致通过」这件事，从「三次独立确认」的直觉里拆出来，给出
（a）基线逐项复核；（b）k_eff 三种口径的公式、差异与可信度；（c）三层全过的**真实置信度区间**；
（d）R12 零增量的性质判定；（e）「三层独立」的精确表述、连带影响清单与实用建议。

**边界（铁律，全部遵守）**：
- **只做计算与推导，不改任何模块、不改任何语料**：本任务对 `lead/evidence_indep_20261109/`、
  `lead/gate_pipeline_20261109/`、`lead/chain_vs_single_20261109/`、`lead/gate_n13_20261109/`、
  `lead/gate_v1v2_20261109/`、`lead/gate_fp7_20261108/`、`lead/falsifiable_no_relax_20261109/`、
  两件台账（`lead/PENDING_DECISIONS.md`、`lead/GOAL_THREE_TARGETS_20261018.md`）**一律只读**。
  十件上游指纹现盘重算全等编排方基线，`_kc_run_console.txt:1-11` 得 `FP_ALL_MATCH True count 9`，
  只读目录 `_eind_manifest_before/after.json` 全等由前序复核件 `_kev_verify_out.json:50-52` 记 `manifest_equal true / manifest_n 169`。
- **零真机**：不启动 `gamemd.exe` / `ra2loader` / `YURI.exe`，不 `taskkill`，不读活进程内存
  （`EVIDENCE_INDEPENDENCE.md:314` 明记真机运行态「未验」）。
- **零采样代码**：不写 hook / MiniDump / SuspendThread / StackWalk / 探针注入，不写动态内存解析。
  本任务 `_kc_verify.py` 只读 JSON + 纯统计计算，无 subprocess 真机/采样动作。
- **绝对只读**：上述目录与两件台账未修改、未追加、未覆盖；**唯一写域** = `lead/keff_calc_20261109/`。
- **不 commit、不 push**：`git log -1` 起始为 `2657458`，本任务未新建提交（见 §6 纪律核验）。
- **小样本铁律**：74 行、3 个真断言错例 → 比率极不稳定，**必须给置信区间或明说「这个数字本身不可靠」**；
  本文所有点估计均附区间，绝不用点估计冒充精确值。

**复核 verdict（如实记）**：编排方【复核】回件判 **`partial`**（`whatBreaksIt` 列：核心数值/区间/破口定位/纪律全部独立复现无误，
但「逐条连带影响」漏列 `EVIDENCE_INDEPENDENCE.md:149/:294` 等 6 处、模板含 3 个 `<填>` 占位符不能原样直贴、
行号 `:120-127`、bootstrap 455/456、CP 上界口径混列三处表述瑕疵）。按交付要求：
**`partial` ⇒ 本交付标注 `unconfirmed`**。本件 §6 已把复核方指出的遗漏全部补齐，并如实列出未消解瑕疵；
但上游 verdict 是编排方给出的既成事实，本件不改判。

---

## 2 上游指纹与基线复核

### 2.1 九件上游指纹（`hashlib` 现盘重算）

编排方【编排方指纹】给 9 件（含 `lead/gate_n13_20261109/_n13_predicates.py`，与
`lead/evidence_indep_20261109/_ei_n13_predicates_src.py` 同件同 SHA）。本任务用
`python -I -X utf8 -c "…hashlib.sha256(b).hexdigest()…"` 逐件现盘重算，`_kc_run_console.txt:1-11`
输出 `True` × 9 + `FP_ALL_MATCH True count 9`，与编排方基线逐件全等；前序主计算
`_ke_calc_stdout.txt:2-11`、复核件 `_kev_verify_out.json:2-48` 亦全等（复核件记 `fp_all_match true`）。
绑定行严格格式见 §6。

| # | 文件 | SHA256（前 12 位） | 字节数 |
|---|---|---|---|
| 1 | `lead/evidence_indep_20261109/EVIDENCE_INDEPENDENCE.md` | `aeab4fc30822…` | 36194 |
| 2 | `lead/gate_pipeline_20261109/_gp_regression_out.json` | `d3543657aa4f…` | 38575 |
| 3 | `lead/evidence_indep_20261109/_ei_04_v12_layer_out.json` | `3253eb8456ce…` | 51602 |
| 4 | `lead/gate_n13_20261109/_n13_predicates.py` = `…/_ei_n13_predicates_src.py` | `e1195b3b220a…` | 16649 |
| 5 | `lead/gate_v1v2_20261109/_v12_rule.py` | `15e4211ffe83…` | 9148 |
| 6 | `lead/gate_fp7_20261108/_g7_predicates.py` | `02c17e49764a…` | 11743 |
| 7 | `lead/falsifiable_no_relax_20261109/_fnr_check_out.json` | `f3112b225b1d…` | 8733 |
| 8 | `lead/PENDING_DECISIONS.md` | `3765eddbe96d…` | 52419 |
| 9 | `lead/GOAL_THREE_TARGETS_20261018.md` | `2baa0de45d41…` | 759518 |

### 2.2 数据源一致性与先验

`_kc_run_console.txt:13-16`：`_gp_regression_out.json:rows` 与 `_ei_04_v12_layer_out.json:rows`
各 74 行，`id` 序列全等、`r10/r12/n13/chain/expect` 5 列逐行全等；
`expect=CATCH`（真断言类）= **39**，`expect=PASS`（非断言类）= **35**，先验 `π=39/74=0.527027027`。

> **标签纠正（如实记）**：编排方【重算结果】写 `n_pos=35 / n_neg=39`，与文件 `expect` 计数相反。
> 数字可复现（`_kc_run_console.txt:23-26` 逐项 `True`），但标签须纠正：
> `fp_rate` 分母是 **35**（非断言被误拦），`miss_rate` 分母是 **39**（真断言被放过）。

### 2.3 逐层 fp / fn / rate（全部复现）

`_kc_run_console.txt:18-26`，`q_i = P(layer=PASS|E) = fn_i/39`，`c_i = P(layer=PASS|¬E) = (35−fp_i)/35`：

| 层 | CATCH | PASS | fp | fn | fp_rate (÷35) | miss_rate = q_i (÷39) | c_i |
|---|---|---|---|---|---|---|---|
| R10 | 40 | 34 | 20 | 19 | **0.5714** | **0.4872** | 0.4286 |
| R12 | 4 | 70 | 0 | 35 | **0.0000** | **0.8974** | 1.0000 |
| N13 | 36 | 38 | 0 | 3 | **0.0000** | **0.0769** | 1.0000 |
| chain | 38 | 36 | 2 | 3 | 0.0571 | 0.0769 | 0.9429 |

与编排方 `per_layer` 的 `fp/fn/fp_rate/miss_rate` 及 `layer_*` 计数逐项 `True`
（`_kc_run_console.txt:23-26`、`_ke_calc_stdout.txt:20-27`）。

### 2.4 三层全过 18 / 3

`_kc_run_console.txt:28-31`：三层全 `PASS` = **18** 行，其中 `expect=CATCH` 的错例 = **3** 行
（`GP-A1 / GP-A2 / GP-A3`），18 行 `chain` 全为 `PASS`。
`P(E|全PASS) = 3/18 =` **16.7%**（0.166667），`P(结论正确|全PASS) = 15/18 = 83.33%`。
明细见 `_ke_calc_stdout.txt:34-52`。

### 2.5 独立假设错率算式（3.75% / 2.05 倍 / 口径错置）

`_kc_run_console.txt:33-41`：

- `q_r10=19/39=0.487179`、`q_r12=35/39=0.897436`、`q_n13=3/39=0.076923`。
- **3.75% 是两层乘积**：`q_r10 × q_n13 = 0.487179×0.076923 = 0.037475345`（= 3.7475%）。
  因 R12 对「全 PASS」零增量，上游只按 R10|N13 两层算联合漏报期望。
  **硬乘三层** `q_r10·q_r12·q_n13 = 0.033631720`（3.36%），与 3.75% 差 0.38 pp。
  出处 `EVIDENCE_INDEPENDENCE.md:131`、`:252`（明记「3.75% 是独立假设下的**期望**，不是分布无关上界」）。
- 实测 `P(all3 PASS|E) = 3/39 = 0.076923`（7.69%）；**2.05 倍** = `0.076923/0.037475 = 2.052631579`
  （似然口径，`_kc_run_console.txt:37`）。
- **3/18=16.7% 是后验，3/39=7.69% 是似然，二者不可相除**：`0.1667/0.037475 = 4.4474`
  属类别错误，禁用（`_kc_run_console.txt:38`）。
- **编排方 `indep_wrong_prob=0.0` 判口径错置**：其来源是
  `fp_rate(r10)×fp_rate(r12)×fp_rate(n13) = 0.5714×0×0 = 0`，用的是「非断言被误拦率」，
  不是「真断言被放过率」（`_kc_run_console.txt:36`、`_ke_calc_stdout.txt:64-66`），**不能当独立假设错率**。
- Bayes 后验（π=39/74，`EVIDENCE_INDEPENDENCE.md:242` 公式）：
  2 层独立 `P(E|全PASS)=0.088785` → 宣称正确 **91.12%**；3 层独立 `0.080411` → 宣称正确 **91.96%**
  （`_kc_run_console.txt:39-40`）。

### 2.6 一致率 51.35% 与 k_eff 自洽性

`_kc_run_console.txt:43-45`：r10×n13 交叉表 `CATCH/CATCH=20`、`CATCH/PASS=20`、`PASS/CATCH=16`、
`PASS/PASS=18`，一致率 `38/74 =` **51.35%**（0.513514），与编排方 `r10_n13_agree=38 / 0.5135` 一致。

**自洽性**：低标签一致只说明「判定近乎统计独立」，k_eff 量的是**真值层误差依赖**
——3 个错例 100% 落在 `both_PASS` 的共同盲区（`EVIDENCE_INDEPENDENCE.md:131`）。
两套口径不冲突，正是 `EVIDENCE_INDEPENDENCE.md:142`「标签独立 ≠ 误差独立」的量化表现，
**不可混用**。代码级依据：R12 调 `r10_context` 且只取 `double_neg` 子集
（`lead/gate_fp7_20261108/_g7_predicates.py:144-145`）；N13 收 R10/R12 参数
（`lead/evidence_indep_20261109/_ei_n13_predicates_src.py:183`）、回调（`:196/:200`）、
记 `r10_kind`（`:231`）、消费 R12 命中（`:242-243`）、C 类放过仅在 R10 kind∈(negation,quote_mention)
（`:253-256`）；`lead/gate_pipeline_20261109/_gp_pipeline.py:147-149` 自述「C 只是转发，不构成独立证据」、
`:179-180` K5 静默 PASS；`lead/gate_pipeline_20261109/_gp_regression.py:141` R12 用行 `tokens`、
`:143` N13 恒用固定 `T`（契约分叉）。

---

## 3 k_eff 三口径：公式、差异、可信度、区间与样本量

### 3.1 阶梯与三口径公式（逐口径）

设 `π=39/74=0.527027`；`p1=P(E|n13 PASS)=3/38=0.078947`；
`p2=P(E|n13&r10 PASS)=3/18=0.166667`；`p3=P(E|三层全 PASS)=3/18=0.166667`
（`_kc_run_console.txt:47-48`）。上游公式见 `lead/chain_vs_single_20261109/_cs_info.py:35-42`。

| 口径 | 公式 | 点值 |
|---|---|---|
| ① 上游概率比 | `k_prob = ln(p3/π) / ln(p1/π)` | **0.606412**（≈ **0.61**） |
| ② 后验几率比 | `k_odds = ln[odds(p3)/odds(π)] / ln[odds(p1)/odds(π)]` | **0.669663**（≈ **0.670**） |
| ③ 信息增益比 | `k_info = I3/I1 = (π−p3)/(π−p1)` | **0.804233**（≈ **0.804**） |

`_kc_run_console.txt:49-52` 实跑三值；`_ke_calc_stdout.txt:74-83` 同值。
R12 真 bit 增量 `log2(odds(p3)/odds(p2)) = 0.000000000`（`_kc_run_console.txt:52`）。

### 3.2 三个数为什么不同

**主因是口径不同，不是抽样噪声**：①概率比 / ②几率比 / ③线性概率差，函数形式不同，
同一 `p1`、`p3` 必然给不同值（`_ke_calc_stdout.txt:81-83`）。
`I=π−p` **不是 bit**（不是互信息），随先验与单调变换而变，也不能解释为「层数」。
三者**共用同一 3 个错例，不是三个独立估计**，取平均、取并集、当置信区间都无统计意义。
仅「均 < 1」这一**方向**稳健。

### 3.3 最可信口径与理由

**② 后验几率比 0.670**：只有它落在可加的 log-似然比尺度上，与
`EVIDENCE_INDEPENDENCE.md:243` 的 `odds(post)=odds(π)·ΠLR_i` 同构
（`_ke_REPORT.md:49-50`）。但须明说：它仍是**相对判别力比值，不是层数计数**；
工程结论「≤1 层」的结构依据是**独立证据根 = 1**
（依赖图 `R10 → {R12, N13.C}`，`EVIDENCE_INDEPENDENCE.md:301`），其 `numeric=1`（`:299`）
是**保守取整的工程约定，不是 k_eff 测量值**，且比 k_eff 点值更乐观。
`EVIDENCE_INDEPENDENCE.md:304` 并列三个估计量 `0.6064/0.6697/0.8042` 亦标「均 ≈1 或更少」。

### 3.4 小样本能否支撑：必须给区间（★ 核心）

**74 行 / 3 个错例不能支撑 k_eff 估计。** 本任务用 `scipy.stats.norm.ppf / beta.ppf`
独立实算（`_kc_run_console.txt:54-59`，`z=1.959963985`）：

- `P(E|全PASS)=3/18`：**Wilson95 = [0.058366, 0.392220]**，**CP 精确95 = [0.035785, 0.414177]**；
- `P(结论正确)=15/18`：**Wilson95 = [0.607780, 0.941634]**，**CP95 = [0.585823, 0.964215]**
  （补集核对 `[1−0.414177, 1−0.035785]`，`_kc_run_console.txt:59`）；区间宽 **33.4 / 37.8 个百分点**；
- `q_n13=3/39`：Wilson95 = [0.026507, 0.203211]、CP95 = [0.016153, 0.208702]
  （与 `EVIDENCE_INDEPENDENCE.md:252` 的 z=1.96 值 `[0.026507,0.203214]` 末位差仅来自 z 精度）。

复核方用 scipy 独立实算得 Wilson `[0.058366,0.392220]`、CP `[0.035785,0.414177]`、
正确率 CP `[0.585823,0.964215]`，与本任务全等（【复核】③段）。前序 `_ke_calc_stdout.txt:84-87`
用 z=1.96 得 `[0.058365,0.392225]` / `[0.035785,0.414177]`，差在 z 精度，非错误。

**敏感性**（`_kc_run_console.txt:61-68`，固定 18 行分母改错例数 k）：
`k=1 → k_prob=1.1851`（>1）、`k=3 → 0.6064`、`k=6 → 0.2413`；删任一错例（2/17）即变 `0.7899`。
即「少 2 个错例」的反事实就把 k_eff 推过 1。

**三套独立 bootstrap（不同实现 / 不同种子，结论一致）**：

| 实现 | seed | k_prob 95% | k_odds 95% | k_info 95% | 出处 |
|---|---|---|---|---|---|
| 前序 LCG `B=10000` | 20261109 | [0.3417, 0.7922] | [0.4139, 0.8280] | [0.4979, 0.9499] | `_ke_calc_stdout.txt:98-102` |
| 复核 PCG64 `B=10000` | 424242 | [0.3355, 0.7897] | [0.4115, 0.8243] | [0.4891, 0.9487] | 【复核】③段 |
| **本任务 PCG64 `B=10000`** | **90210** | **[0.3360, 0.7905]** | **[0.4132, 0.8263]** | **[0.5025, 1.0000]** | `_kc_run_console.txt:70-75` |

本任务独立 bootstrap 全距含负值（`k_prob range=[-0.0890, 0.8894]`、`k_info` 上限触 1.0000），
前序全距亦含负（`k_odds min=-0.0202`）。⇒ **95% 区间虽整体落在 (0,1)，但上限逼近/触到 1、
全距含负值、k=1 反事实即 >1**，故 `0.61 / 0.670 / 0.804` 必须标
「**描述性、不可靠、不可用于放行**」，**这个数字本身不可靠**。

> **如实记两处前序瑕疵**（复核方指出、本任务查 `_ke_calc_out.json:step2_bootstrap` 确认）：
> ① `_ke_REPORT.md:61` / `_ke_calc_stdout.txt:104` 写「455/10000 次重抽越域」，但
> `_ke_calc_out.json:step2_bootstrap.invalid` = `{"boundary_p":455, "prob_ratio_out_of_domain":1}`
> 合计 **456** 剔除（对应 `k_prob valid=9544`；其余口径 `valid=9545` → 455 剔除）。
> ② 本任务与复核方均用不同 RNG 重跑，故不采信前序单一 LCG 的分位数为精确值，只采信其方向。

### 3.5 需要多少样本

`n ≈ z²p(1−p)/w²`（绝对半宽 w）或 `n ≈ z²(1−p)/(r²p)`（相对半宽 r），
`_kc_run_console.txt:77-84`：

| 目标 | 需真断言类 n_E | 按 39/74 配比折算总行 |
|---|---|---|
| 联合漏报 3/39 到 ±2pp | ≈ 682 | ≈ 1294 |
| 联合漏报 3/39 到 ±1pp | ≈ 2728 | ≈ 5176 |
| 后验 3/18 到 ±5pp | ≈ 214 | ≈ 405 |
| 后验 3/18 到 ±2pp | ≈ 1334 | ≈ 2531 |
| 联合漏报相对 ±10% | ≈ 4610 | ≈ 8747 |
| 联合漏报相对 ±5% | ≈ 18440 | ≈ 34987 |
| 拿到 100 个全PASS错例 | — | ≈ 600 个全PASS行 ≈ **2467** 总行 |

⇒ **10³ 起步、10⁴–10⁵ 才可用**（`_ke_calc_stdout.txt:116-117`）。**前提**：含 r10/r12/n13 全判定列、
无 train=test 泄漏、无定向对抗样本混入的**盲留出集**（`EVIDENCE_INDEPENDENCE.md:308` 亦要求封 SHA 盲留出集）。
且**单纯加样本不能把确定性依赖变成独立层**，n→∞ 只让一个「无层数含义的数」收敛得更稳
（`_ke_calc_stdout.txt:118-119`）。

---

## 4 三层真实置信度

### 4.1 k_eff 折算层数

按 k_eff = `0.606–0.804` 个「N13 等效独立层」（均 **< 1 层**）；结构层面**独立证据根 = 1**
（`EVIDENCE_INDEPENDENCE.md:301`）。**绝不可按 3 层计**（`:299`「三层一致按 1 层计，numeric=1」）。
注：上游 `numeric=1` 是保守取整约定，比 k_eff 点值更乐观，不是测量值。

### 4.2 真实正确概率：必须给区间，不给单点

实测 `P(结论正确|三层全 PASS) = 15/18 = 83.33%`（16.7% 错误率），本任务独立实算
（`_kc_run_console.txt:56-59`）：

- **Wilson 95% = [60.78%, 94.16%]**
- **Clopper–Pearson 精确 95% = [58.58%, 96.42%]**（宽 37.8 pp）
- 对应错误率 16.7%：Wilson95 = [5.84%, 39.22%]、CP95 = [3.58%, 41.42%]

复核方独立实算给 `CP95=[58.6%,96.4%]`（【计算】realConfidence 段），全等。
**必须同时声明**：这是 **74 行 train=test 上的描述性区间**，先验 `π=39/74`，
**不是生产置信界**；先验变化后后验随之变化（`_ke_calc_stdout.txt:126`）。

### 4.3 与「三层独立」宣称差多少

`_kc_run_console.txt:39-41`、`_ke_calc_stdout.txt:127-131`：

- 两层独立 Bayes 宣称正确 **91.1215%**、三层独立 **91.9589%**；实测 **83.3333%**
  ⇒ 正确率**低 7.79 pp / 8.63 pp**，后验错误率**放大 1.8772× / 2.0727×**。
- 若沿用编排方 `indep_wrong_prob=0.0`（错置口径）则宣称 **100%**，差 **16.67 pp**。
- **2.0526× 是似然口径**（7.69% vs 3.75%），**不得与后验混用**（§2.5）。

### 4.4 Fréchet 上界评估

`P(allPASS|E) ≤ min q_i = min(0.487179, 0.897436, 0.076923) = 0.076923`
（`_kc_run_console.txt:98-101`；`EVIDENCE_INDEPENDENCE.md:252,256` 明记「不得用 Πq_i 当上界」）：

- **作为本 74 行内描述性天花板：可用且逻辑正确**，且恰被实测 `3/39=0.076923` **取等（饱和、零余量）**。
  借 `c_i` 与 π 换后验得 `P(E|全PASS) ≤ 0.166667` → 正确率 `≥ 83.33%`（样本内）。
- **作为生产置信下界：不可用**，五条理由（`_ke_calc_stdout.txt:136-140`）：
  ① `q_i` 是 train=test 点估计，`q_n13` Wilson95 上界 `0.203211`，用它则上界升到 0.2032、
  后验正确率**仅 ≥ 65.43%**（`_kc_run_console.txt:101`）；② 上界已被实测取等、零余量；
  ③ 它约束的是**似然**，换后验还须借 `c_i` 与 π（同为训练值）；
  ④ 共同盲区子总体上 `q_i=1` 使上界平凡；⑤ `ABSENT` 被折成 `PASS` 违反 H3
  （`EVIDENCE_INDEPENDENCE.md:249`）。

### 4.5 报告必附「置信度声明」模板

> 前序 `_ke_REPORT.md:82-94` 的模板经复核方【复核】⑤判定**不能原样直接贴**：
> 含 3 个 `<填>` SHA 占位符、`92.0%` 是 Bayes 点值无区间、
> `spans==0 时 K7 循环体不执行` 仅据 `_gp_DESIGN.md:286` 自述（K7 可达性**未验**）、
> 硬编码「本 74 行」无语料/版本失效条款。以下为**补齐前置条件后**的可贴版本：

```text
[三层结论置信度声明]  结论：R10/R12/N13 全 PASS（chain=PASS）
0 绑定/失效条款：本声明仅在下列 9 件上游指纹与谓词/语料版本逐一匹配时有效；
  任一 SHA 变化、语料增删或谓词改动即失效，必须按 §3 重算，不得沿用本模板数值。
  (predicate_sha, tokens_sha, text_sha) = (<必须填实并绑定；未填则本声明不成立>, …, …)
  缺列则该行不计入一致计数。
1 证据结构：3 个判据 / 1 个独立证据根（R10→{R12,N13.C}）；
  k_eff 描述值 0.61–0.80，bootstrap95 上限达 0.95（本任务独立实现触 1.00），
  含负值全距，标「描述性、不可靠、不可用于放行」。
2 观测：本 74 行 train=test 上三层全 PASS 共 18 行，其中 3 行是真断言（GP-A1/A2/A3）；
  P(结论正确|全 PASS)=15/18=83.3%，Wilson95=[60.8%, 94.2%]，CP95=[58.6%, 96.4%]。
  先验 π=39/74；先验变化后后验随之变化，本区间不是生产置信界。
3 与独立宣称的差：三层独立 Bayes 点值应报正确率 92.0%（两层口径 91.1%）——
  ★该 92.0% 是 Bayes 点值、无区间、非实测；实测 83.3% 低 8.6 pp，
  后验错误率放大 2.07×；2.05× 是似然口径，不得与后验混用。
4 兜底：Fréchet min q_i=7.69% 仅为样本内天花板（已被实测取等、零余量），非生产置信界；
  不得写 Πq_i 为上界；q_n13 Wilson95 上界 0.2032 时后验正确率仅 ≥65.4%。
5 覆盖：本链判不了词表外同义改写 / 枚举外双重否定 / 跨行共指；
  「spans==0 时 K7 循环体不执行」据 _gp_DESIGN.md:286 与 GATE_PIPELINE_COMPOSE.md:272
  自述，K7/K8 可达性本任务未重跑 —— 未验。
6 处置：本结论不得作为自动放行依据；无层间冲突时按风险信号处理，
  必须人工复核 + coverage_note（GATE_PIPELINE_COMPOSE.md:501）。
7 未验：生产 q_i/ρ、盲留出集误差相关、Cohen's κ、正交层增益、改谓词效果、真机运行态
  —— 全部未验（EVIDENCE_INDEPENDENCE.md:314-321）。
```

---

## 5 R12 零增量评估

### 5.1 `P=1.000` 是精确还是观测

`_kc_run_console.txt:86-89`：`n13=PASS` 共 **38** 行，其中 `r12=CATCH` **0** 行
⇒ `P(r12=PASS|n13=PASS)=38/38=1.000` 是**本 74 行上的观测值，不是精确 1.000、不是定理**。
零命中 38 次的比例 95% 上界（**口径须分列，不可混列**；复核方【复核】④指出前序三值未标注口径）：

| 口径 | 上界 | 性质 |
|---|---|---|
| 单侧精确 95% `1−0.05^(1/38)` | **0.075808** | 单侧精确（`_kc_verify_out.json`） |
| rule-of-three `3/38` | **0.078947** | 单侧 95% 近似 |
| Wilson 双侧 95% | **0.091810** | 双侧 |
| 双侧精确 95% `1−0.025^(1/38)` | **0.092513** | 双侧（前序 `_ke_calc_stdout.txt:143` 的「CP 精确上界」） |

即「`r12=CATCH` 且 `n13=PASS`」的真比例在 95% 水平上仍可高达约 **7.6%–9.3%**（视单/双侧口径），
**1.000 不能当定理**。复核方独立算单侧精确 `0.075808`、Wilson `0.091810`
（`_kev_verify_out.json:146-147`），与本任务全等。

### 5.2 大样本会不会破

会破，两条路（`_ke_calc_stdout.txt:150-156`、`_kc_run_console.txt:90`）：

1. **采样**：反例比例 95% 上界仍可达 9.3%（§5.1），更大语料完全可能撞出 `r12=CATCH & n13=PASS`。
2. **★ 确定性契约分叉**：R12 判定用**该行 `tokens`**（`lead/gate_pipeline_20261109/_gp_regression.py:141`），
   N13 单层**恒用固定三词 `T`**（`:143`），且 N13 内部回调 `r12_scan` 也用自身 `T`
   （`lead/evidence_indep_20261109/_ei_n13_predicates_src.py:200`），
   故「R12 命中 ⇒ N13 判 D ⇒ CATCH」（`:242-243`）**只在 N13 自己的词表内成立**。
   本任务实算 `tokens≠T3` 的行 = **19**（17 行三词超集 + 2 行 C07 另一套词表，
   `_kc_run_console.txt:90`；`EVIDENCE_INDEPENDENCE.md:98` 记 72/74 行同词表、余 2 行 C07）。
   一旦某行在**行 tokens** 上命中双重否定而 `T` 里无该 token，记录列 `r12=CATCH` 完全可能与
   `n13=PASS` 共存。本 74 行内 0 行，但**机制存在 ⇒ 1.000 是样本巧合 + 契约巧合，不是恒等式**。

### 5.3 别的场景有无增量

`_kc_run_console.txt:91-92`：R12 的 4 行命中
（`R10-TV3 / R10-CTX-05 / R10-CTX-06 / GP-C04`）全部 `expect=CATCH` 且 `n13=CATCH`，
即**相对最终合成判定增量为 0**（4 次正确命中都被 N13 覆盖）。
`GP-A1/A2/A3` 三层全 `PASS` 且 `r12=PASS`：GP-A1 构式「亦非不」不在 `DOUBLE_NEG_RE` 枚举
（`lead/gate_fp7_20261108/_g7_predicates.py:76`），该行上 R12 零增量。

**非零增量的场景**：枚举内双重否定（如 `GATE_PIPELINE_COMPOSE.md:215` C3）相对
**构式标注/归因**与 **N13 内部 D 类**（`_ei_n13_predicates_src.py:242-243`）有作用；
但相对 chain 最终判定无新增。

### 5.4 存在价值结论

即便真零增量，R12 仍有存在价值（`_ke_calc_stdout.txt:165-168`）：
① 诊断/归因（把 `double_neg` 从 R10 的 `negation` 豁免里捞回）；
② 它是 N13 的**输入**（`_ei_n13_predicates_src.py:199-202/:242-243`），删掉会改变 N13 行为，
「边际为 0」≠「因果上无用」；③ fail-safe：在 R10 宽进豁免路径上提供反向证据。
**但绝不可计为独立证据层**：它是 R10 的 `double_neg` 子集
（`_g7_predicates.py:144-145`、`EVIDENCE_INDEPENDENCE.md:294`），
标签应写「**R10 派生守卫**」而非「第 2 个独立证人」。

---

## 6 复核回件（绑定行）+ 结论 + 未验项

### 6.1 复核回件绑定行（严格格式，9 件；`hashlib` 现盘重算与编排方基线全等）

顺序对应：`EVIDENCE_INDEPENDENCE.md` / `_gp_regression_out.json` / `_ei_04_v12_layer_out.json` /
`lead/gate_n13_20261109/_n13_predicates.py`(=`_ei_n13_predicates_src.py`) / `_v12_rule.py` / `_g7_predicates.py` /
`_fnr_check_out.json` / `PENDING_DECISIONS.md` / `GOAL_THREE_TARGETS_20261018.md`。
本任务实跑 `_kc_run_console.txt:1-11` 得 `FP_ALL_MATCH True count 9`。

被核对象 SHA256 = aeab4fc30822dfde9c21489aef9a42a1558dde1f21f091f486bbd94453f7a523，字节数 = 36194
被核对象 SHA256 = d3543657aa4f9914c9023710f6daef8348a12ca0aa11957110e8b7c45baec6fe，字节数 = 38575
被核对象 SHA256 = 3253eb8456ceab54df1b41629caa4eaee8fcabff5e016e18fd71a3a3606b4546，字节数 = 51602
被核对象 SHA256 = e1195b3b220ad97b5b91b8746a24e332b02ce28085452e947554f99b7f2f3079，字节数 = 16649
被核对象 SHA256 = 15e4211ffe8397027757aa4d0fb9b9cc5dc41126a08024b9f6cb5bbd8be4a1c0，字节数 = 9148
被核对象 SHA256 = 02c17e49764a6f87f2b0d26c6689f0cbeb96498509e5c75bf843104829c51120，字节数 = 11743
被核对象 SHA256 = f3112b225b1de35183ad4604554cb25689ed252b6a5a95d96d17fce53c8c140e，字节数 = 8733
被核对象 SHA256 = 3765eddbe96deeb65eeb1f05dc81e1dc171e7ea3b2c826e2692a1d15e1c8f2d7，字节数 = 52419
被核对象 SHA256 = 2baa0de45d4125549262eb595d7518c9ce99efeee120384bf640cded8a933ede，字节数 = 759518

> 编排方【复核】`sha256Line` 给同 9 行、`all_strict=True`（严格 regex
> `^被核对象 SHA256 = ([0-9a-f]{64})，字节数 = (\d+)$`）；本任务 §6.5 再自检本件格式。

### 6.2 复核 verdict 如实记

编排方【复核】`verdict = partial`（非 `confirmed`、非 `refuted`）。
**按交付要求 `partial` ⇒ 标 `unconfirmed`**：本件所有 k_eff 点值、置信度点值均为**描述性、
未确认、不可用于放行**。复核方 `whatBreaksIt` 的决定性理由是「逐条连带影响」漏列同论域
`EVIDENCE_INDEPENDENCE.md:149/:294`、`_cs_BASELINE_ALIGNMENT:213/225/228/334`、
`CHAIN_VS_SINGLE.md:195/263` 等句，且模板含 3 个 `<填>` 不能原样直贴、行号 `:120-127`
（9 条实为 `:120-128`）、bootstrap 455/456、CP 上界口径混列。本件 §4.5 已补模板前置条件、
§6.3 已补完整清单、§3.4/§5.1 已如实标注 bootstrap 与上界口径瑕疵；
**核心数值、区间、破口定位、纪律均经本任务独立实跑复现无误**（`_kc_run_console.txt:1-101`）。

### 6.3 「三层独立」的精确表述

> **「R10 / R12 / N13 是在同一运行时输入契约上串行装配的三个判据；
> 依赖图为 `R10 → {R12, N13.C}`，独立证据根 = 1。本 74 行上三层全 PASS 的等效判别力仅
> `0.61–0.80` 个 N13 单层（三口径 `0.606 / 0.670 / 0.804`，bootstrap95 上限达 0.95–1.00、
> 全距含负值、k=1 反事实即 >1，描述值不可靠），R10 相对 N13 为负贡献，R12 为零增量派生守卫。
> 工程上按 ≤1 层计（保守取整 1）；一致通过只表示『三个判据都未触发』，
> 不表示三次独立确认；真实正确率 83.3% 的 CP95 = [58.6%, 96.4%]（train=test 描述值），
> 亦不构成自动放行依据。」**

### 6.4 需重新表述的结论清单（逐条；均为只读件，本任务未改）

**A. 前序 `_ke_REPORT.md:120-128` 已列 9 条**（证据字段误写 `:120-127`，实为 `:120-128`）：

1. `lead/gate_pipeline_20261109/GATE_PIPELINE_COMPOSE.md:215` C3「三层一致，非冲突」
   → 同一 R10 根的派生判定一致，非三次确认。
2. `lead/gate_pipeline_20261109/_gp_DESIGN.md:220` C3「三层一致，非冲突」→ 同上。
3. `GATE_PIPELINE_COMPOSE.md:410`「未消解 0」+ 逐族全对 → 冲突计数为空不是通过证据，
   3 条共同盲区不进 `conflicts[]`（`FALSIFIABLE_NO_RELAX.md:320` 已自认）。
4. `lead/chain_vs_single_20261109/CHAIN_VS_SINGLE.md:206`「≈1～1.3 层（乐观 1.5）」
   → 与 k_eff `0.61–0.80` 不一致，应改 ≤1 层并附宽区间。
5. `CHAIN_VS_SINGLE.md:190` / `lead/chain_vs_single_20261109/_cs_BASELINE_ALIGNMENT_20261109.md:208`
   「一致通过概率被高估」→ 补量化：观测正确率 83.3% `[60.8%,94.2%]`。
6. `EVIDENCE_INDEPENDENCE.md:299`「按 1 层计 numeric=1」→ 标明是工程保守取整，非 k_eff 测量值。
7. `EVIDENCE_INDEPENDENCE.md:131`「独立假设下应为 3.75%」→ 标明是 `q_r10×q_n13` 的**期望**，
   且 3/18 与 3/39 不同量；Fréchet 真上界是 `min q_i=7.69%`（`:252,256`）。
8. `GATE_PIPELINE_COMPOSE.md:247/272` 与 `_gp_DESIGN.md:394` 已自认不独立，保留；
   其「合成链 69/74」应加「单层等效，非三层加成」。
9. `lead/falsifiable_no_relax_20261109/FALSIFIABLE_NO_RELAX.md:320` 已写「三层不是三个独立证人」，
   保留并补 §4.5 置信度声明。

**B. 复核方【复核】⑥指出的同论域遗漏（本件补齐，逐条给出精确处置）**：

10. `EVIDENCE_INDEPENDENCE.md:149`「R12 增量判别力 = 0 bit：`P(r12=PASS|n13=PASS)=38/38=1.000`」
    → `1.000` 是**观测值非定理**，须标单/双侧 95% 上界 7.6%–9.3%（§5.1）与契约分叉破口（§5.2）。
11. `EVIDENCE_INDEPENDENCE.md:294` 表格「`P(r12=PASS|n13=PASS)=1.000`，增量 0 bit」→ 同上，
    并改标「R10 派生守卫」而非「独立证人」（§5.4）。
12. `_cs_BASELINE_ALIGNMENT_20261109.md:213`「约 1 层，上限 1.5 层」→ 与 `0.61–0.80` 不一致，
    应改 ≤1 层并附 `bootstrap95` 宽区间。
13. `_cs_BASELINE_ALIGNMENT_20261109.md:225` `0.61` → 单点，须附 §3.4 区间与「不可用」标注。
14. `_cs_BASELINE_ALIGNMENT_20261109.md:228`「≈1～1.3 层（乐观 1.5）」→ 同第 12 条。
15. `_cs_BASELINE_ALIGNMENT_20261109.md:334`「`P(r12=PASS|n13=PASS)=1.000`，R12 增量信息 0 bit」
    → 同第 10 条，标观测值。
16. `CHAIN_VS_SINGLE.md:195` 标题「信息量 ≈ 1 层」→ 须附 §3.4 宽区间，不可只给点值。
17. `CHAIN_VS_SINGLE.md:263` 表格「有效独立层数 ≈1」→ 须附区间 + 「不得作为自动放行」。

**C. 两件台账检索结论（复核正确，无需改写；如实补列复核方指出的 `GOAL:784`）**：

- `GOAL_THREE_TARGETS_20261018.md:8366`「三条独立证据同向」= 帧时周期否证论域
  （`:8367-8369` 置换检验 / lag-8 ACF / 同进程三窗），**非本论域**。
- `GOAL_THREE_TARGETS_20261018.md:8535`「这件不是独立证据」= 崩溃残件论域（`107 份基线残件`）。
- `GOAL_THREE_TARGETS_20261018.md:784`「v2 故障注入未证的三层空白」= 真 GDI 截屏
  `3584×967` / S1-S2 判定器论域（`:784-786`），**含「三层」但非本论域，无需改写**；
  复核方指出前序检索结论未列出此行，本件如实补列。
- `PENDING_DECISIONS.md:358` D-08「不能写成三趟全过」= harness7 真机趟数（`:357-360`），**非本论域**。

⇒ 两件台账中**未发现**针对 R10/R12/N13 的「三层都过所以可信」条目，无需改写。

### 6.5 怎么用现有三层（实用建议）

① 把 chain 当**一个弱检测器**，不要当三次确认；以 N13 单层作基线并显式登记其「免考卷」问题
（`_gp_regression.py:143` 恒用 `T`）。
② 把「层间冲突」当唯一有信息量的信号：本任务实算 `_kc_run_console.txt:94-96`，
`layer_conflicts>0` 的 **25 行 chain 全判对**；`layer_conflicts==0` 的 **49 行里 5 行判错**
（`REAL-SLOT / REAL-TRUTH / GP-A1 / GP-A2 / GP-A3`）；chain 合计 `69/74`、fp2 fn3。
⇒ **「无冲突且全 PASS」应触发人工复核队列，而非自动放行**。
③ 全 PASS 行优先按共同盲区顺序查：词表覆盖 → 否定构式枚举 → 跨行/共指/转述
（`GATE_PIPELINE_COMPOSE.md:501`）。
④ 正交证据另起一路：R9/R11（hashlib 绑定行/文件存在，`EVIDENCE_INDEPENDENCE.md:296`）与
V1V2 限死 `spans==0` 的单调 OR（`:190`、`:297`），但**必须先在封 SHA 盲留出集上给独立 fp/fn**
（`:308`），否则不得计入层数。
⑤ 每条结论强制附 §4.5 模板 + `(predicate_sha, tokens_sha, text_sha)`；
把 3 个 GP-A 错例列为常驻回归哨兵。

### 6.6 纪律核验（本任务实跑）

- 实跑：`python -I -X utf8 -B D:/Project/ra2-campaign-forge/lead/keff_calc_20261109/_kc_verify.py`
  （`EXIT=0`，119 行留盘 `_kc_run_console.txt`）；`python -I -X utf8 -c "…"` 逐件 hashlib 指纹
  与 `file:line` 读取；`git status --porcelain -- <只读路径>` 与 `git log -1`。
- 只读件 9 件指纹全等编排方基线（§6.1），只读目录 `_eind_manifest_before/after.json` 全等
  （`_kev_verify_out.json:50-52`，`manifest_n=169`、`manifest_mismatches=[]`）。
- `git status --porcelain -- <只读路径>` 与会话起始快照一致
  （`MM` 两件台账 + `??` 各只读目录，均为既有状态），`git log -1` = `2657458` 未变
  ⇒ 未 commit / 未 push。
- 唯一写域 `?? lead/keff_calc_20261109/`；本任务新增 `_kc_verify.py`、`_kc_run_console.txt`、
  `_kc_verify_stdout.txt`、`_kc_verify_out.json` 共 4 件 + 本件 `KEFF_CALC.md`；
  前序 5 件 `_ke_*`、4 件 `_kev_*` 保持原样（收尾 `iterdir()` 实列 14 件，与上述计数一致）。
- 零真机、零采样代码；`_kc_verify.py` 仅读 JSON + scipy/numpy 纯统计，无 hook/进程/内存操作。

### 6.7 未验项（逐项如实列，不补造）

- **真机运行态**：`gamemd.exe` / `ra2loader` / `YURI.exe`、活进程内存 —— 铁律零真机，**未验**
  （`EVIDENCE_INDEPENDENCE.md:314`）。
- **盲留出集误差相关双检** `ρ=corr(1{err_i},1{err_j})`：只读
  `lead/chain_vs_single_20261109/_cs_holdout_out.json` 只有 `unseen` 且行内仅
  `id/expect/n13/chain/v12/note/text`（本任务读其结构确认**无 r10/r12 列**），
  `EVIDENCE_INDEPENDENCE.md:315` 亦记「缺 r10/r12 列且 3 条逐字重复」⇒ **未验**。
- **生产语料 `q_i / s_i / c_i / ρ` 与 k_eff 泛化有效性**：74 行 train=test 且含定向构造对抗样本，
  **未验**（`:316`）。
- **Cohen's κ / 双盲人工标注一致性**：未做，**未验**（`:317`）。
- **正交层（R9/R11、V1V2、第五层）实际增益**：无留盘盲评，**未验**（`:318`）。
- **K7/K8 可达性、`spans==0` 死分支、`ABSENT→PASS` 语义**：模板第 5 条已标「据自述、未重跑」，
  **未验**（`EVIDENCE_INDEPENDENCE.md:249`、`:320`）。
- **改谓词 / 改编排后的效果**：本任务零改动、未实装，**未验**（`:321`、`GATE_PIPELINE_COMPOSE.md:510`）。
- **「R12 在任何语料上都零增量」「k_eff 在任何语料上都 <1」「三层在任何语料上都 ≈1 层」**：
  只在本次 74 行成立，**未验**（`EVIDENCE_INDEPENDENCE.md:310`）。
- **两件台账中其它「独立证据」措辞是否成立**：检索范围内未发现本论域条目，不作判定（§6.4 C）。
