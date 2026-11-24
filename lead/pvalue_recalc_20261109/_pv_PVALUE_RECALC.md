# _pv_PVALUE_RECALC.md — p 值三口径重算 · 设计效应 · 循环论证判定

**写域**：`lead/pvalue_recalc_20261109/`（唯一写域；本会话全部写入均在此，前缀 `_pv_`）。
**铁律**：零真机（未启动 gamemd.exe / ra2loader / YURI.exe，未 taskkill，未读活进程内存）；零采样代码（未写 hook / MiniDump / SuspendThread / StackWalk / 探针注入 / 动态内存解析）；五个只读目录与两件台账一律只读；**未改任何既有脚本、语料、产物**；不 commit、不 push。Python 一律 `python -I -X utf8` + 绝对路径，指纹用 `hashlib`。
**证据口径**：本会话实跑命令与逐字输出见 §0；引用上游一律给 `文件:行`；拿不到写「未验」，不补造。

---

## 0 本会话实跑命令与输出（证据台账）

| # | 命令（逐字要点） | 输出落盘 |
|---|---|---|
| C1 | `python -I -X utf8 -c "<8 件 hashlib sha256 + len>"` | 8/8 OK，见 §0.1 |
| C2 | `python -I -X utf8 -c "<inspect 74 JSON keys>"` / `"<dump row0 both JSONs>"` | 见 §1 |
| C3 | `python -I -X utf8 "D:/Project/ra2-campaign-forge/lead/pvalue_recalc_20261109/_pv_recompute.py" \| tee .../_pv_recompute_out.txt` | `_pv_recompute_out.txt`（4,604 B） |
| C4 | `python -I -X utf8 "D:/Project/ra2-campaign-forge/lead/pvalue_recalc_20261109/_pv_ci_check.py" \| tee .../_pv_ci_check_out.txt` | `_pv_ci_check_out.txt`（1,323 B） |
| C5 | `python -I -X utf8 "D:/Project/ra2-campaign-forge/lead/pvalue_recalc_20261109/_pv_final_checks.py" \| tee .../_pv_final_checks_out.txt` | `_pv_final_checks_out.txt`（3,854 B） |
| C6 | `grep -n "K9\|20 条\|FP\|..." lead/gate_pipeline_20261109/{_gp_pipeline.py,_gp_DESIGN.md,GATE_PIPELINE_COMPOSE.md,_gp_regression.py}` | 命中见 §4(a) |
| C7 | `python -I -X utf8 -c "<按行号读 COMPARABILITY_AUDIT.md:210-225,328-365；_gp_regression.py:140-152；_gp_DESIGN.md:345-356>"` | 见 §4(a) |
| C8 | `python -I -X utf8 -c "<会话末 8 件指纹 + 5 个只读目录 mtime + 写域清单>"` | 见 §0.2 |
| C9 | `ls -la` / `wc -l` / `mkdir -p lead/pvalue_recalc_20261109` / 目录 mtime 复核等辅助命令 | 见 §0.2 |

**C3 输出逐字（关键段）**：
```
74 sha256 = d3543657aa4f9914c9023710f6daef8348a12ca0aa11957110e8b7c45baec6fe bytes = 38575
72 sha256 = 68c7ecd3aafc94be87092bf65f1e3d05ab28cc5a20de5193117f994882e16358 bytes = 37461
common = 71 onlyA = ['GP-A1', 'GP-A2', 'GP-A3'] onlyB = ['GP-C03']
s(74,all74) = 69 s(72,all72) = 48 total delta = 21
flips (expect changed) = 3 ['GP-C05', 'GP-C06', 'GP-C07']
n_frozen = 68
frozen: chain72 = 48 chain74 = 66 delta = 18
paired b = 18 c = 0 n_discordant = 18
b-c == frozen delta ? True
gains = 18 losses = 0
all gains expect == PASS ? True
all gains 72chain CATCH -> 74chain PASS ? True
n_distinct_texts = 16 of 18
dup_texts = [{"text": "### 1(c) 有没有已入账的？", "count": 2}, {"text": "**已入账核查实跑命令**：", "count": 2}]
  dup ids for '### 1(c) 有没有已入账的？' = ['N13-P01', 'R10-CTX-10']
  dup ids for '**已入账核查实跑命令**：' = ['N13-P05', 'R10-CTX-07']
families = {'N13_POS': 12, 'R10_CTX': 5, 'REAL3': 1} n_families = 3
72 FP in frozen = 20 74 still FP = 2 ['REAL-SLOT', 'REAL-TRUTH']
repaired = 18
all_units n = 18 k = 18 P(X>=n) = 1/262144 p_two exact = 1/131072 p_two float = 7.62939453125e-06
distinct_texts n = 16 k = 16 P(X>=n) = 1/65536 p_two exact = 1/32768 p_two float = 3.0517578125e-05
family_level n = 3 k = 3 P(X>=n) = 1/8 p_two exact = 1/4 p_two float = 0.25
rho = 0.0 n_eff = 18.0 / 0.3 n_eff = 2.9508 / 0.5 n_eff = 1.8947 / 0.8 n_eff = 1.2329 / 0.9 n_eff = 1.1043 / 1.0 n_eff = 1.0
```

**C4 输出逐字（关键段）**：
```
n = 18 k = 18 CP95 (二分) = [ 0.8146980318621477 , 1.0 ]  校验 sf(n,n,lo_closed) = 0.02499999999999999
n = 16 k = 16 CP95 (二分) = [ 0.7940927857921773 , 1.0 ]  校验 = 0.024999999999999988
n = 3  k = 3  CP95 (二分) = [ 0.2924017738212866 , 1.0 ]  校验 = 0.025000000000000005
Wilson95: n=18 [0.8241207763533425, 1.0] ; n=16 [0.8063923194655636, 1.0] ; n=3 [0.4385029682449546, 1.0]
bootstrap 200000 percentile 95% CI = [ 0.16176470588235295 , 0.36764705882352944 ]
```

**★ 如实登记脚本缺陷**：`_pv_recompute.py` 的 `cp_two_sided()` 两处二分判反（k=n 时 `sf` 随 p 递增却写 `lo=m`；上界 `cdf(k=n,n,p)≡1` 恒 > α/2 使 `hi` 塌到 0），故 C3 里那段 CP 输出是**错的**（打印出 `3.11e-61`）。本会话遵守「不改任何既有脚本、语料、产物」，**未回头改它**，另建 `_pv_ci_check.py` 用「闭式 `(α/2)^(1/n)` + 校正二分」独立重算并逐项校验 `sf(n,n,p_lo)=0.025`，见 C4。本报告所有 CI 取 C4 结果，C3 的 CP 段作废。

**C5 输出逐字（关键段）**：
```
2*2^-n_eff < 0.05  =>  n_eff > log2(40) = 5.321928094887363
连续外推: rho < 0.14013134380964332 ; 离散 n_eff>=6: rho <= 0.11764705882352941 = 2/17
族级/全单元 倍数 = 32768.0  log10 差 = 4.515449934959718
compliant = 8 / 8 ; MATCH × 8（会话末零漂移）
```

### 0.1 编排方实跑指纹（本会话 `hashlib` 独立复算，8/8 MATCH）

命令 C1：`python -I -X utf8 -c "import hashlib,os; ... 8 件逐件 sha256+len ..."`
输出逐字（节选，8 行全 `OK`）：
```
OK lead/score_decomp_20261109/SCORE_DECOMP.md sha=dfe7f68692eb7ae752358782acaaa1fc5a42ecbd0a6930205e0dcfe4f6544dcb bytes=42573
OK lead/score_decomp_20261109/_sd_report.md sha=58e71cefc024d6874b353cde69d1b39b450f4a79ad08c35e9d235c01dbd725ff bytes=49202
OK lead/comparability_20261109/COMPARABILITY_AUDIT.md sha=c00833b3fef5b8b5f93cdfd9d5223f22149878dd868200c1a070d76e553d8ae1 bytes=51927
OK lead/gate_pipeline_20261109/_gp_regression_out.json sha=d3543657aa4f9914c9023710f6daef8348a12ca0aa11957110e8b7c45baec6fe bytes=38575
OK lead/gate_pipeline_20261109/_gp_regression_v1_union_out.json sha=68c7ecd3aafc94be87092bf65f1e3d05ab28cc5a20de5193117f994882e16358 bytes=37461
OK lead/chain_vs_single_20261109/_cs_BASELINE_ALIGNMENT_20261109.md sha=3397c1c41b0a81e85699f07ce608b9b13e0ab45cba51280a3e78883581768ed2 bytes=49850
OK lead/PENDING_DECISIONS.md sha=3765eddbe96deeb65eeb1f05dc81e1dc171e7ea3b2c826e2692a1d15e1c8f2d7 bytes=52419
OK lead/GOAL_THREE_TARGETS_20261018.md sha=2baa0de45d4125549262eb595d7518c9ce99efeee120384bf640cded8a933ede bytes=759518
```

### 0.2 只读域零漂移（C5 / C8 会话末复算）
`score_decomp_20261109/`、`comparability_20261109/`、`gate_pipeline_20261109/`、`chain_vs_single_20261109/`、`evidence_indep_20261109/` 五目录及两件台账：**8/8 指纹 MATCH**，目录 mtime 分别 `17:24:22 / 13:51:58 / 15:15:38 / 17:16:19`，均早于本会话首次写入 `18:44`。
如实登记一处观察：`SCORE_DECOMP.md` 的 mtime 为 `2026-11-09 18:42:05`（早于本会话首次 `ls` 约 `18:44`），文件名下**内容**在会话始（C1）与会话末（C5）两次 `hashlib` 实算均等于 `dfe7f686…4dcb / 42,573 B`，即**字节零漂移**；本会话未对该文件做任何写入，mtime 来源本会话内**未验**（不补造解释）。

---

## 1 第一步：基线复核

### (a) `b=18 / c=0 / n_disc=18` —— **能复现**
C3 由两件只读 JSON 独立按 id 对齐构造：`common=71`，`onlyA=['GP-A1','GP-A2','GP-A3']`，`onlyB=['GP-C03']`；3 条 `expect` 变更 `GP-C05/C06/C07` 剔除后 `n_frozen=68`；逐行比较 `chain==expect` 得 `frozen chain72=48 chain74=66`，配对 `b=18 c=0 n_discordant=18`，`b-c=18` 与分差自洽（`True`）。`s(74,all74)=69`、`s(72,all72)=48`、`delta=21` 亦复现。
凭据：`_pv_recompute_out.txt`（C3）；`SCORE_DECOMP.md:50-59,156`、`COMPARABILITY_AUDIT.md:334-335`（引用，未修改）。

### (b) 全单元 `p = 7.629e-06` 的算式 —— **对**
H0：18 个不一致对两方向等概率（`p=0.5`，McNemar 精确版）。观测 `k=b=18, c=0, n=b+c=18`。
**小 p 值法（双侧）**：
```
p = min(1, 2 × P(X ≥ 18 | X ~ Bin(18, 0.5)))
  = 2 × C(18,18) × (1/2)^18
  = 2 × 2^-18 = 2^-17 = 1/131072
  = 7.62939453125e-06
```
C3 用 `Fraction` + `math.comb` 实算得 `P(X>=n) = 1/262144 = 3.814697265625e-06`、`p_two exact = 1/131072`。单侧 `= 3.814697265625e-06`。与 `SCORE_DECOMP.md:157-158` 一致。
（等价核验：小 p 值法对 `k=n` 亦等于 `P(X=0)+P(X=18)=2×2^-18`；两种写法同值。）

### (c) ★ 16 个独立文本 / 3 个族 —— **都能复现**
C3 对 18 条增益取 `text_head` 去重：`n_distinct_texts = 16 of 18`，重复 2 组各 2 次，逐字为 `### 1(c) 有没有已入账的？`（ids `N13-P01 / R10-CTX-10`）与 `**已入账核查实跑命令**：`（ids `N13-P05 / R10-CTX-07`），与编排方 `dup_texts` 及 `SCORE_DECOMP.md:171` 逐字一致。
族计数 `{'N13_POS':12, 'R10_CTX':5, 'REAL3':1}`，`n_families=3`，与编排方 `families` 一致。
另复现降级事实：18 条增益**全部** `expect=PASS`（`all gains expect == PASS ? True`）、**全部** `72:chain=CATCH → 74:chain=PASS`；72 版冻结集内 FP=20、74 版仍 FP=2（`REAL-SLOT / REAL-TRUTH`）、修好 18 条。凭据：`_pv_recompute_out.txt`（C3）、`SCORE_DECOMP.md:171,249`。

### (d) GP-A1/A2/A3 的 `chain` —— **能复现，均为 `PASS`（漏判），不是 CATCH**
C3 转储 74 版：
```
74 GP-A1 expect = CATCH chain = PASS naive/r10/r12/n13 = ['CATCH','PASS','PASS','PASS']
74 GP-A2 expect = CATCH chain = PASS naive/r10/r12/n13 = ['PASS','PASS','PASS','PASS']
74 GP-A3 expect = CATCH chain = PASS naive/r10/r12/n13 = ['PASS','PASS','PASS','PASS']
72 GP-C03 expect = CATCH chain = PASS naive/r10/r12/n13 = ['CATCH','PASS','PASS','PASS']
GP-C03[72] vs GP-A1[74] text_head equal ? True
```
**口径更正（如实）**：`GP-A1/A2/A3` 是 `onlyA`，**只存在于 74 版**，72 版无同名行，故「两版 chain 值」对这三行字面不成立。72 侧可对照的只有 `GP-C03`（与 `GP-A1` 同文本换 id 换族，`COMPARABILITY_AUDIT.md:99`、`SCORE_DECOMP.md:91,201`），其 `chain=PASS`；`GP-A2/A3` 在 72 版**无对照行 → 未验/不存在**。编排方「三行在 74 版全部 `expect=CATCH chain=PASS r10=PASS r12=PASS n13=PASS`」本会话逐字复现成立。
根因（引用未重跑）：`_gp_regression.py:145-150` 的 `chain` 只数 `ADJUDICATED/NEEDS_HUMAN`；`SCORE_DECOMP.md:225,230-231,235` 记 `CATCH` 只出现在 `naive`/`v12` 的 S3 DEFAULT fail-closed / 未实装 DG Shim 三列，74 评分列逐 span 走 K5 → PASS。本会话**未重跑** `_gp_pipeline.gate_check` 的 18 条全量重放（那是 `SCORE_DECOMP.md:251` 的命令 4），据「引用未重跑」登记。

---

## 2 第二步：三口径重算 p（本任务核心）

统一口径：`n` 个独立单元全部朝一个方向（ successes = n ），H0 每单元 `p=0.5`；双侧 exact binomial 小 p 值法 `p_two = min(1, 2·2^-n)`；CP 95% 双侧在 `k=n` 有闭式 `CI = [(α/2)^(1/n), 1.0]`（α/2=0.025），C4 用校正二分逐项验 `sf(n,n,p_lo)=0.025`；Wilson 95% 附作对照。

### (a) 全单元口径（n=18）
- `p = 2×2^-18 = 2^-17 = 1/131072 = 7.62939453125e-06`
- CP 95% CI = `[0.8146980318621477, 1.0]`（上游 `SCORE_DECOMP.md:159` 给 `[0.8147, 1.0]`，一致）
- Wilson 95% = `[0.8241207763533425, 1.0]`
- 单侧 `p = 3.814697265625e-06`

### (b) 独立文本口径（n=16）
- `p = 2×2^-16 = 2^-15 = 1/32768 = 3.0517578125e-05`
- CP 95% CI = `[0.7940927857921772, 1.0]`；Wilson 95% = `[0.8063923194655636, 1.0]`

### (c) 族级口径（n=3，符号检验）
- `p = 2×2^-3 = 1/4 = 0.25` —— **不显著**（α=0.05）
- CP 95% CI = `[0.2924017738212866, 1.0]`；Wilson 95% = `[0.4385029682449546, 1.0]`。两者下界都把 0.5 包进去，与 `p=0.25` 一致地不拒绝 H0。
- 族构成 `N13_POS 12 / R10_CTX 5 / REAL3 1`；`REAL3` 只有 1 条，该族的方向信息本来就来自单条样本。

附：配对正确率差 `18/68 = 0.2647058823529412`；C4 以 `seed=20261109 / 200000` 次 bootstrap 复现 percentile 95% CI `= [0.16176470588235295, 0.36764705882352944]`，与 `SCORE_DECOMP.md:162` 逐字一致。

### (d) ★ 数量级对比表

| 口径 | 独立单元 n | 双侧 exact p | log₁₀(p) | 相对全单元倍数 | CP 95% 下界 | 显著性(α=.05) |
|---|---|---|---|---|---|---|
| 全单元 | 18 | `7.62939453125e-06` | −5.1175 | ×1 | 0.8147 | 显著（**但抽样模型不成立**） |
| 独立文本 | 16 | `3.0517578125e-05` | −4.5154 | ×4 | 0.7941 | 显著（**但仍高估独立性**） |
| 族级 | 3 | `0.25` | −0.6021 | **×32768** | 0.2924 | **不显著** |

族级相对全单元抬升 **32,768 倍 = 2^15**，跨 **4.515 个数量级**（C5 实算 `log10 差 = 4.515449934959718`）。从「极显著」到「不显著」，全靠把分析单元从「行」换成「族」。

### (e) ★★ 哪一个口径最正当 —— **族级（n=3, p=0.25，不显著）；且严格说三个口径没有一个能当推断性 p 用**

**判断**：按「不许挑宽松口径」的要求，应报**最保守**的族级口径，并把它当作**证据强度的上界**，而不是把 `7.63e-06` 或 `3.05e-05` 当结论。理由：

1. **全单元口径的独立性假设被直接证伪**：18 条里只有 16 个 `text_head`（C3 逐字列出 2 组重复），把同一文本的两个 id 当两次独立 Bernoulli 试验，是重复计数；且 18 条聚成 3 族，族内同构。
2. **独立文本口径仍不成立**：去重后 16 条仍全部来自同一个 K9 分支（`_gp_pipeline.py:168-171`）、全部 `expect=PASS`、全部 `CATCH→PASS`（C3 三个 `True`），簇内相关接近 1；把 16 个同族模板当独立样本，仍是高估。
3. **族级是这三个里唯一把「同一机制/同一失败形态」合并计数的口径**：3 个族各自只贡献 1 个方向，`2×2^-3=0.25`，**不显著**。这恰是 `SCORE_DECOMP.md:183` 与 `COMPARABILITY_AUDIT.md:344` 的定性。
4. **但族级本身也不是有效 p**：3 族同属 K9 定向修复集（post-selection），`ρ̄≈1` 使 `n_eff≈1`（§3），真实有效单元连 3 都不到；族级 `0.25` 只是「最不宽松」的界，不是合法推断 p。

**结论**：不许为了让 p 好看而选 `n=18` 或 `n=16`。**宁可给「不显著」**：对外只报族级 `p=0.25（不显著）` + `n_eff≈1` + 盲留出「未验」，并把 `7.63e-06` 明确降格为**描述性内部一致性指标**。`SCORE_DECOMP.md:187,275` 与编排方任务书「四条降级理由」同向。

---

## 3 第三步：设计效应与有效样本量

### (a) `n_eff = n/(1+(n−1)ρ̄)`，n=18（C3 实算，与编排方逐项一致）

| ρ̄ | 设计效应 `1+17ρ̄` | n_eff | floor(n_eff) 对应双侧 p |
|---|---|---|---|
| 0.0 | 1.0 | **18.0000** | `7.62939453125e-06` |
| 0.3 | 6.1 | **2.9508** | n=2 → `0.5` |
| 0.5 | 9.5 | **1.8947** | n=1 → `1.0` |
| 0.8 | 14.6 | **1.2329** | n=1 → `1.0` |
| 0.9 | 16.3 | **1.1043** | n=1 → `1.0` |
| 1.0 | 18.0 | **1.0000** | n=1 → `1.0` |

（`deff` 与 `n_eff` 的 4 位小数与编排方 `design_effect` 数组逐项相同。）

### (b) ★ ρ̄ 该取多少 —— **ρ̄ = 1.0（保守且可辩护）；真值「未定/未验」**
依据：C3 实算 18 条增益 `expect` 清一色 `PASS`、`72:chain=CATCH→74:chain=PASS` 清一色、方向零反向；`SCORE_DECOMP.md:104,251` 记 18/18 逐行追到 `_gp_pipeline.py:168-171` 的 K3+K9（**本会话未重跑该重放，引用未重跑**）；`_gp_DESIGN.md:287` 明写 K9 是「为了让 N13 的 A/B 精筛压过 R10 的宽进（消掉 20 条 FP）」；`COMPARABILITY_AUDIT.md:219,344` 判「正是设计 K9 时点名的失败形态 ⇒ in-sample 调参收益」。同一分支、同一失败形态、同一修复方向、同一批被选中样本 ⇒ 簇内相关取上界 `ρ̄≈1`，即 **18 条实质上等于 1 个独立观测**。
如实登记：`ρ̄` 无调参日志可定（`SCORE_DECOMP.md:185,291` 列为未验），故 `ρ̄=1.0` 是**保守取值而非实测**；但 ρ̄ 的定义域上界就是 1，取 1 不会低估设计效应，符合「宁可给不显著」。

### (c) 按 ρ̄=1.0 的有效样本量与对应 p
- `n_eff = 18/(1+17·1) = 18/18 = 1.0`
- **对应 p = 1.0**：`p_two(n=1,k=1) = min(1, 2·P(X≥1|Bin(1,0.5))) = min(1, 2×0.5) = 1.0`（C3 实算 `p_two(n_eff=1,k=1)=1.0`）。
- 诚实限定：`n_eff` 不是整数样本量，把它代回 exact binomial 只是量级示意；**严格说 post-selection 下推断性 p 无定义（未验）**，`p≈1` 的正确读法是「零证据强度」。
- 交叉印证：C5 实算连续外推 `2·2^-n_eff` 在 ρ̄=0.3 已为 `0.2587`、ρ̄=0.5 为 `0.5378`、ρ̄=1.0 为 `1.0`。

### (d) 设计效应把 p 抬到什么程度
从 `7.62939453125e-06` 抬到 `1.0`，约 **131,072 倍 / 5.12 个数量级**，**显著性被完全抹掉**。更关键的阈值（C5 实算）：要保住名义 `p<0.05` 需 `n_eff > log₂40 = 5.3219`，即 `ρ̄ < 0.1401`；按整数 `n_eff≥6` 需 **`ρ̄ ≤ 2/17 ≈ 0.1176`**。而本例 ρ̄≈1 远超该阈值 —— **任何不低于 0.118 的簇内相关都足以让结论翻成「不显著」**，无需争辩 ρ̄ 的精确值。

---

## 4 第四步：循环论证的严重程度

### (a) K9 是为消这 20 条 FP 而写的吗 —— **是**，源码 + 设计件 + 独立重算三重可证
- `_gp_pipeline.py:168-171`（本会话 C 直接打开逐行读）：
  ```
  168  elif n13_v == "PASS" and r10_v == "CATCH":
  169      # K3：A/B 放过 vs R10 抓住，输入契约不同
  170      if n13_veto:
  171          verdict = "PASS"; rule += ["K3", "K9"]   # K9 精筛覆盖宽进
  ```
  K9 不是独立规则，是 K3 分支里「`n13_veto` 为真就判 PASS」的那一行，专门覆盖 R10 宽进误报。
- `_gp_DESIGN.md:259`（K9 定义行）、`:287`「为了让 N13 的 A/B 精筛压过 R10 的宽进（**消掉 20 条 FP**）」、`:352`「20 条新增误报全部来自『N13 已判 A/B 放过、R10 宽进仍报 assertion』…第二版改为逐 span 裁决后 FP 降到 2。**这条失败证据保留不删**」、`:348-350` 实测 `chain 正确=48 FP=20`。
- `GATE_PIPELINE_COMPOSE.md:431`「20 条新增误报全部来自…（`r10=CATCH/n13=PASS` 共 20 条）。第二版改逐 span 裁决后 FP 降到 2」；`:247` 同向。
- `COMPARABILITY_AUDIT.md:219`「本次 K9『精筛覆盖宽进』是**为消 20 条 FP 而写**」、`:344`「18 条全正向、0 条反向：正是设计 K9 时点名的失败形态」。
- `SCORE_DECOMP.md:105,170,183-186` 自述「K9 为消这 20 条 FP 而写，18 条恰是照着答案改完的答案 → 循环论证」。
- **独立重算印证**（C3，非引用）：72 版冻结集内 `FP = 20`，74 版仍 `FP = 2 ['REAL-SLOT','REAL-TRUTH']`，`repaired = 18` —— 18 条增益恰好等于「20 条 FP 中修好的 18 条」，`b=18 c=0` 与 `FP 20→2` 是同一组行的两种数法。
- 如实登记：72 版（v1 并集）**生成脚本未留盘**（`COMPARABILITY_AUDIT.md:343`、`GATE_PIPELINE_COMPOSE.md:431,465`），本会话只核 JSON 内部自洽，未重跑该生成器，标「未验重跑」。

### (b) 若 18 条是「照着答案改完的答案」，这个 p 还有意义吗 —— **没有推断意义，只剩描述/回归意义**
`p=7.63e-06` 的抽样模型是「18 个独立不一致对，各自 50/50」。但样本入选规则本身就是「K9 要修的失败行」，且 K9 写成后这些行必然朝 PASS 方向变：
1. **抽样模型被违反**：不是从目标总体随机抽的，是按结果选出的（post-selection / in-sample）。
2. **「惊喜」是选择偏差的伪影**：条件于「已知这 18 条是 K9 失败样本」，观测到 18/18 朝同一方向几乎是必然；把选择事件从概率模型里抹掉，才得到虚假的 `2^-18`。
3. **不能乘常数修正**：`SCORE_DECOMP.md:179` 明写「in-sample 偏差不能靠给 p 乘常数修好，`2^-18` 的抽样模型本身失效」；Bonferroni 也需要调参次数 `M`，`M` 无日志（`SCORE_DECOMP.md:185`）⇒ 标未验，不得反推「p 仍稳健」。
4. **还能用的部分**：它可以当**确定性回归测试**——证明「逐 span K1–K9 确实在这 18 行上把 72 版的误拦改成了放行」，即内部效度/实现一致性；`COMPARABILITY_AUDIT.md:340` 称其为「本次唯一具有内部效度的因果陈述」。它**不能**支撑「算法更好」「合成链优于单层」「泛化」「生产置信界」。

### (c) ★ post-selection 下的信息量 —— **≈ 0 bit**
条件事件 `S = 「这 18 条是 K9 的失败样本 / 被点名修复集」`。观测 `E = 「18/18 修好（全朝 PASS）」` 在该条件下按构造近乎必然：`P(E|S) ≈ 1`。
- 自信息 `−log₂ P(E|S) ≈ 0 bit`（C3 PART 4c 实算打印 `surprisal = 0 bits`）。
- 对 H0 的似然比**不可识别**：`P(E|H0)=2^-18` 是在「未选择」模型下算的，而实际抽样分布是 `P(·|S)`，两者不在同一概率空间；分子分母不可比 ⇒ **不存在有效的 post-selection p**。
- 诚实补充（不掩盖不利事实）：定向失败集上的实测修复率是 **18/20 = 0.9，不是 20/20**；剩下的 `REAL-SLOT / REAL-TRUTH` 两条 FP（C3 实算）说明修复并不彻底，且它们与「18/18」不是同一统计量。这 2 条失败反而提供了信息，但那是对「K9 覆盖不全」的信息，不是对「算法更好」的支持。
- 另：`SCORE_DECOMP.md:186` 独立给出同一结论「post-selection 条件分布：在『已知这 18 条是 K9 失败样本』条件下观测 18/18 修好的概率 ≈ 1、信息量 ≈ 0」。

### (d) ★ 这个 p 值应当如何表述 —— **降格为「描述性内部效度指标」，不得单独作显著性证据**
必须同时给出：`n=18`、`b=18/c=0`、方向全为 `expect=PASS`、独立文本 16、族 3、**族级 p=0.25（不显著）**、`ρ̄≈1 → n_eff≈1 → 名义 p≈1.0`、in-sample / post-selection、E 轴「未验重跑」、M 轴列定义已变、盲留出「未验」、修正后真实 p「未验」。
**禁止**写成「p=7.63e-06，显著，算法改进」「合成链优于单层」「置信界 [0.8147,1.0] 可用于生产」。此结论与 `SCORE_DECOMP.md:175,187,272-275`、`COMPARABILITY_AUDIT.md:340,344` 一致。

---

## 5 第五步：结论与建议

### (a) ★ 唯一站得住的统计表述（一句话）
> 「在这 68 条冻结考题上，两版 `chain` 列有 18 处不一致且全部朝同一方向（72 误拦 → 74 放行，`expect` 全为 PASS）；这 18 处是 K9 为消 20 条 FP 而定向修复的样本，只含 16 个独立文本、聚 3 族，`ρ̄≈1` 使 `n_eff≈1`，族级符号检验 `p=0.25`（不显著）、设计效应下名义 `p≈1.0`，故**不存在可用于推断算法优劣的有效 p 值**；`7.62939453125e-06` 只是未校正的描述性内部一致性指标，不得作为显著性或泛化证据。」

### (b) 要把 p 提到可信水平，需要什么样的新数据（**方案，未执行**）
按 `COMPARABILITY_AUDIT.md:356-362`、`SCORE_DECOMP.md:181,283` 与本次新增要求：
1. **物理隔离盲留出集**：一次性出题、按域 × `expect` 分层配额，`train/dev/test` 三集封 SHA，`test` 一次性使用、用过即作废；`N19–N26 / GP-A` 及本轮 18 条 K9 失败样本**只进 train，禁进 test**。
2. **人员与标注分离**：出题人 ≠ 改规则人 ≠ 批卷人（名单留盘）；双盲标注，Cohen's κ ≥ 0.8；标注手册（「什么算真断言」）单独成文封 SHA，评测期禁改 `expect`。
3. **一次性预注册**：先写死假设、分析单元、主检验（族级/簇自助）、α、停止规则，再封 SHA；**调参搜索次数 M 全程留日志**（这是 post-selection 修正与 Bonferroni 的前提）。
4. **单轴变更 + 全列重跑**：五轴 `S/G/I/E/M` 每侧 `path+sha256+bytes` 入 manifest；只改 `I` 一轴，两格**都实跑**、不复用旧列；生成器 `.py` 同批留盘封 SHA（**无脚本的 JSON 作废**，72 版即反例）；统一输入契约消除 `_gp_regression.py:143-145` 的分叉。
5. **在 test 上重算**：配对 `b/c` + exact binomial 双侧 p + bootstrap CI + macro-F1 + 按 `expect`/族分报 FP/FN + **按簇重抽样或 `n_eff` 修正的 p**；`p>0.05` 一律写「未检出差异」。
6. **独立复核**：第三方按同一 manifest 复现、逐字节比对、独立跑断言得同一 verdict，未经复核不得进入报告。

### (c) 以后报 p 值必须同时给什么（清单）
基础 18 项见 `SCORE_DECOMP.md:283`（五轴 manifest / 冻结语料 / 冻结标注手册 / 冻结评测脚本 / 冻结依赖 / 变更单 / 全列重跑 / 统一输入契约 / 可比性 verdict / 配对统计 / 归因范围 / 分母口径 / 留盘复现状态 / 盲留出 / 逐分逐行归因 / 选择过程与 n_eff / 兜底机制披露 / 收尾零漂移）。本任务**必须补齐以下 ★ 项**：
1. **★ 三口径 p 并列**：全单元 / 独立文本 / 族级各自 `n`、p、CI，明确声明**分析单元**；禁止只报最宽松那个。
2. **★ 独立单元核对证据**：`text_head`（或全文）去重结果与重复 id 清单、族划分与各族计数。
3. **★ 方向分布**：`b/c` 之外必须给增益/损失的 `expect` 分布、被比较列的 CATCH 召回是否变化（本例 18/18 `PASS` 且 CATCH 召回 36/36 不变，`SCORE_DECOMP.md:172,240`）。
4. **★ ρ̄ 的取值依据与 `n_eff` 全表**：ρ̄ 取哪个值、凭什么、是否实测；同时给 `p` 随 ρ̄ 的敏感性与「保住 p<0.05 所需 ρ̄ 上界」（本例 `≤0.1176`）。
5. **★ post-selection 状态**：in-sample / holdout 明确标注；调参次数 `M` 与选择日志；若 in-sample，p 必须标「描述性、非生产置信界」，并给「修正后真实 p = 未验」。
6. **★ 不显著时的措辞**：`p ≥ 0.05` 一律写「未检出差异」，禁止「边缘显著」「趋势向好」等软化表述。
7. **★ 绑定行**：被核对象 SHA256（完整 64 hex）+ 字节数，格式固定，会话始/末各复算一次。

### (d) 这条工作判不了什么（如实列）
① 判不了「算法有没有改进 / 能否泛化」（train=test、无盲留出、无 κ）；② 判不了「合成链 vs 单层谁更好」（frozen68 内 chain 66/68 仍劣于 n13 68/68，`SCORE_DECOMP.md:172,193`）；③ 判不了 72 版 `48/72` 怎么算出来的（v1 并集生成脚本全仓/git 零命中，E 轴「未验重跑」）；④ 判不了 `ρ̄` 真值与调参次数 `M`（无日志，本会话 ρ̄=1.0 是保守取值而非实测）；⑤ 判不了 **post-selection 修正后的真实 p**（本会话只给界与「未验」，不补造）；⑥ 判不了 3 条翻标的绝对正确性（标注手册未封 SHA、无双盲 κ）；⑦ 判不了 `text_head` 之外的正文是否改动（截断到 90 字，`COMPARABILITY_AUDIT.md:141`）；⑧ 判不了 18/18 逐行 K3+K9 重放（本会话**未重跑**该重放，引用 `SCORE_DECOMP.md:104,251`）；⑨ 判不了 `GP-A2/A3` 在 72 版的 chain（无对照行，仅 `GP-C03≡GP-A1` 可对照）；⑩ 判不了 `SCORE_DECOMP.md` mtime `18:42:05` 的来源（内容零漂移已证，mtime 来源未验）；⑪ 判不了任何真机/运行时行为（零真机零采样，铁律所限）；⑫ 判不了上游对齐实验 `b=0 c=3 p=0.25` 与 `_cmp_assert.py` 修正版（引用未重跑 / 未实装）。

---

## 6 复核回件 · 绑定行（格式固定）

被核对象 SHA256 = dfe7f68692eb7ae752358782acaaa1fc5a42ecbd0a6930205e0dcfe4f6544dcb，字节数 = 42573
被核对象 SHA256 = 58e71cefc024d6874b353cde69d1b39b450f4a79ad08c35e9d235c01dbd725ff，字节数 = 49202
被核对象 SHA256 = c00833b3fef5b8b5f93cdfd9d5223f22149878dd868200c1a070d76e553d8ae1，字节数 = 51927
被核对象 SHA256 = d3543657aa4f9914c9023710f6daef8348a12ca0aa11957110e8b7c45baec6fe，字节数 = 38575
被核对象 SHA256 = 68c7ecd3aafc94be87092bf65f1e3d05ab28cc5a20de5193117f994882e16358，字节数 = 37461
被核对象 SHA256 = 3397c1c41b0a81e85699f07ce608b9b13e0ab45cba51280a3e78883581768ed2，字节数 = 49850
被核对象 SHA256 = 3765eddbe96deeb65eeb1f05dc81e1dc171e7ea3b2c826e2692a1d15e1c8f2d7，字节数 = 52419
被核对象 SHA256 = 2baa0de45d4125549262eb595d7518c9ce99efeee120384bf640cded8a933ede，字节数 = 759518

格式自检（C5 实跑正则 `^被核对象 SHA256 = ([0-9a-f]{64})，字节数 = (\d+)$`）：`compliant = 8 / 8`。每行「被核对象 SHA256 = 」后紧跟完整 64 位十六进制，中间无路径、括号、星号、反引号或空格；随后「，字节数 = 」再写数字。

---

## 7 纪律与自证

- 唯一写入 = `lead/pvalue_recalc_20261109/` 下新建 `_pv_*` 文件（本报告 + 3 个脚本 + 3 个输出）。**未修改任何既有脚本、语料、产物**；五个只读目录与两件台账会话始/末 `hashlib` 8/8 MATCH（C1 / C5-D 段）。
- `_pv_ci_check.py` 使用 `random.Random(20261109)` 是为**可复现统计 bootstrap**（与上游 `SCORE_DECOMP.md:162` 同 seed 得同 CI），非加密用途；Mimosa 静态提示「弱随机数」在本场景下属误报，如实登记，不改用 `secrets`（会破坏可复现性）。
- 零真机、零采样、不 commit、不 push。所有 Python 均为 `python -I -X utf8` + 绝对路径；指纹均 `hashlib`。
- 本会话实跑 shell 命令数 = 16（含 3 次 `python -I -X utf8 <_pv_*.py>` 脚本实跑、会话始指纹 1 次、会话末零漂移/绑定行终检 2 次）。另有 `Read` 工具读源码（`SCORE_DECOMP.md` 全文、`_gp_pipeline.py:155-184`、`_gp_DESIGN.md:282-299`）、`Write` 工具创建 4 个 `_pv_*` 文件（`_pv_recompute.py` 初次写入后整体覆写一次以修掉尾段笔误）、`Edit` 工具数次校正本节措辞（本节含自指计数，故不列具体次数）、`TodoWrite` 工具维护任务台账，均未计入 shell 命令数。
