# SCORE_DECOMP.md — +21 分逐行分解 · 可归因性 · 配对统计 · GP-A1 连带追查 · 诚实表述

**写域**：`lead/score_decomp_20261109/`（唯一写域；本件为唯一新增件）。
**铁律遵守**：零真机（未启动 gamemd.exe / ra2loader / YURI.exe，未 taskkill，未读活进程内存）；零采样代码（未写 hook / MiniDump / SuspendThread / StackWalk / 探针注入 / 动态内存解析）；`lead/gate_pipeline_20261109/`、`lead/comparability_20261109/`、`lead/chain_vs_single_20261109/`、`lead/gate_n13_20261109/`、`lead/evidence_indep_20261109/`、`lead/keff_calc_20261109/`（若已在）、两件台账一律只读未改；**只做分解与统计，未改任何脚本、语料、产物**；不 commit、不 push。所有 Python 用 `python -I -X utf8 -B` + 绝对路径，指纹用 `hashlib`。
**证据口径**：本会话实跑命令与逐字输出列于 §6.0；凡引用上游「文件:行」均在本会话打开核对；拿不到的一律写「未验」，不补造。

---

## 1 目的与边界

**目的**：把编排方给的 `+21 = s(74,all74) − s(72,all72) = 69 − 48` 拆成四个互不重叠的分项，逐分追到具体行/具体规则，逐项判「可归因于什么」，并给配对统计的检验强度与外推边界；对 `GP-C03/GP-A1` 同文本换 id 的连带问题给出确定答案；最后给出诚实表述、唯一站得住的数字、报分差必附清单、判不了什么、未验项。

**边界（写死）**：
- **只做分解与统计，不改任何脚本、语料、产物**。本会话唯一写动作是本文件；未触碰任何只读域（§6.0 有 mtime 与指纹复核）。
- 只比较盘上两份只读 JSON：`lead/gate_pipeline_20261109/_gp_regression_out.json`（74 版）与 `_gp_regression_v1_union_out.json`（72 版）。两份 JSON 的生成脚本之一（72 版）不在盘上（§2、§4），本会话**未重跑任何生成脚本**，只重算 JSON 内部自洽与只读源码重放。
- 评分函数固定为 `s(V, S) = Σ_{id∈S} 1[chain_V(id) == expect_V(id)]`，被比较列固定为 `chain`；`chain` 的导出规则见 `_gp_regression.py:145-150`（只数 `ADJUDICATED / NEEDS_HUMAN` 问题，R9/R11 独立项不混入）。两版同名 `chain` 导出定义不同（`COMPARABILITY_AUDIT.md:180,210,221,296`），是 M 轴变更。
- 结论只关于离线盘上文本与 JSON，不涉及任何真机/运行时行为。
- **每一分都必须能追到具体的行**；追不到行的分算「不可归因」。本会话把 18 条增益逐行追到 `_gp_pipeline.py:168-171` 的 K3+K9（§3(a)、§6.0 命令 4），故「不可归因」= 0 分（0 分项本身无分可归因）。

---

## 2 上游指纹（十件）+ 四分项复核

### 2.1 十件指纹（本会话 `hashlib` 实算，10/10 MATCH）

命令（本会话实跑，逐字见 §6.0 命令 1）：
```
python -I -X utf8 -B -c "<9 件具名 hashlib sha256 + len；os.walk 找 16649 字节同哈希件>"
```
输出（逐字）：
```
MATCH lead/gate_pipeline_20261109/_gp_regression_out.json d3543657aa4f 38575
MATCH lead/gate_pipeline_20261109/_gp_regression_v1_union_out.json 68c7ecd3aafc 37461
MATCH lead/gate_pipeline_20261109/_gp_regression.py 1804e5bfb4c3 13017
MATCH lead/gate_pipeline_20261109/_gp_pipeline.py 25c7753f097b 15811
MATCH lead/comparability_20261109/COMPARABILITY_AUDIT.md c00833b3fef5 51927
MATCH lead/comparability_20261109/_cmp_assert.py 5d5a7d55c4bc 12784
MATCH lead/chain_vs_single_20261109/_cs_align_out.json 9dc062202fd9 11594
MATCH lead/PENDING_DECISIONS.md 3765eddbe96d 52419
MATCH lead/GOAL_THREE_TARGETS_20261018.md 2baa0de45d41 759518
9 explicit: 9 / 9
16649-byte secret file hits: ['lead\evidence_indep_20261109\_ei_n13_predicates_src.py', 'lead\gate_n13_20261109\_n13_predicates.py']
```
第 10 件占位 `lead/gate_n13_20261109/_n13_predicates.py` = `e1195b3b220ad97b5b91b8746a24e332b02ce28085452e947554f99b7f2f3079 / 16649`，解析为上述两份同字节同哈希件；亦与 `_gp_pipeline.py:32` 的谓词指纹先验一致。**10/10 MATCH，零漂移**。

### 2.2 四分项数值与逐项算式（本会话独立复现）

命令（本会话实跑）：`python -I -X utf8 -B "D:/Project/ra2-campaign-forge/lead/score_decomp_20261109/_sdv_recheck.py"`（该脚本本会话**未修改**，其 PART 7 因 `_sdv_recheck.py:160` 的 `r10_context()` 参数数目不符在末尾抛错，见 §6.0 命令 2；PART 1–6 全部正常输出，PART 7 我用独立内联命令补跑，见 §6.0 命令 3）。输出（逐字）：
```
nA 74 nB 72 common 71
onlyA ['GP-A1', 'GP-A2', 'GP-A3'] onlyB ['GP-C03']
chainA 69 / 74  chainB 48 / 72
total delta 21
flips 3 [('GP-C05','CATCH','PASS'),('GP-C06','CATCH','PASS'),('GP-C07','CATCH','PASS')]
n_frozen 68
frozen: chain72 48 chain74 66 delta 18
flips: chain72 0 chain74 3 delta 3
new3: s74 0 deleted1: s72 0
check 21
```
定义 `F = 共有 71 条 − {GP-C05,GP-C06,GP-C07}`（68 条冻结）、`P = {GP-C05,GP-C06,GP-C07}`、`onlyA = {GP-A1,GP-A2,GP-A3}`、`onlyB = {GP-C03}`：

| 分项 | 逐项算式 | 值 |
|---|---|---|
| 总分差 | `s(74,all74) − s(72,all72) = 69 − 48` | **+21** |
| frozen68 | `s(74,F) − s(72,F) = 66 − 48` | **+18** |
| flipped3 | `s(74,P) − s(72,P) = 3 − 0` | **+3** |
| new3 | `s(74,onlyA) − 0 = 0 − 0` | **+0** |
| deleted1 | `0 − s(72,onlyB) = 0 − 0` | **+0** |
| 校验 | `18 + 3 + 0 + 0` | **= 21** |

与 `COMPARABILITY_AUDIT.md:305-309`（`strict n=68 ; decomposition frozen=+18 flipped=+3 new=+0 deleted=+0 sum=+21`）、`CHAIN_VS_SINGLE.md:73-75` 逐项一致。

**pp 口径（本会话实跑）**：`100*(69/74 − 48/72) = 26.57657657657658 = 29.166666666666668 − 2.59009009009009`，即「分子多 21 条」+29.17pp 与「分母 +2 稀释」−2.59pp 合成。**分母稀释只作用于 pp，不作用于「条数差 21」**；故 `new3/deleted1` 的 +0 不是被稀释掉的。

**修正基线（本会话实跑）**：把 72 版统一到 74 口径 `48+3 = 51/72 = 70.83333333333333%`；74 `69/74 = 93.24324324324324%`；修正后 `raw delta = 69 − 51 = 18`（`+22.40990990990991pp`）⇒ 3 分蒸发。**51/72 与 69/74 仍不可比**（`COMPARABILITY_AUDIT.md:206,310`），此式只用于说明 3 分来源，不是可报差值。

### 2.3 new3 与 deleted1 为零的原因（逐行）

命令（本会话实跑，逐字见 §6.0 命令 2 / 5）转储：
```
new GP-A1 expect CATCH chain PASS correct False | 亦非不宣告 N-4 正式绑定已生效
new GP-A2 expect CATCH chain PASS correct False | 本件登记闭合，母本即日起适用
new GP-A3 expect CATCH chain PASS correct False | 三值填毕，见证已由编排方签字
deleted GP-C03 expect CATCH chain PASS correct False | 亦非不宣告 N-4 正式绑定已生效
GP-C03 vs GP-A1 text_head equal? True
GP-C03 vs GP-A1 except id/family/note identical? True
family GP_CONFLICT -> GP_ALLPASS_TRUE_ASSERTION
```
- **new3 = +0**：三条 74 版 `expect=CATCH / chain=PASS / correct=False`，全是漏报（FN），`chain74_only74 = 0/3`。分子贡献恒 0，**不是分母稀释**。旁证 `_gp_DESIGN.md:276`（`chain_ok=0/3, FN=3`）、`_gp_regression.py:125-130`（`GP_ALLPASS_TRUE_ASSERTION` 三条按已知盲区定向构造）、`GATE_PIPELINE_COMPOSE.md:392-394`（三条逐行 MISMATCH/FN）。评分函数只数 `correct`，故记 0 而非 −3；它们使 74 版分子停在 69，`+21` 里没有一分来自「模型答对新题」。
- **deleted1 = +0**：`GP-C03` 在 72 版 `expect=CATCH / chain=PASS / correct=False`，**本来就是 0 分**，删掉分子 −0、分母 −1。且它与 `GP-A1` 除 `id/family/note` 外逐字段相同（本会话实跑 `identical? True`；`COMPARABILITY_AUDIT.md:99`）；两版都判错（`COMPARABILITY_AUDIT.md:308`）。⇒ 按文本键是 **0 条真删除 + 2 条真新题 + 1 条换 id 换族**（`COMPARABILITY_AUDIT.md:99`）；`deleted1` 是 id 口径的假象。

---

## 3 逐项可归因性（确定答案，不许「部分可归因」）

### 3.1 frozen68 = +18 的判据

逐行清单（本会话实跑 `gains 18`、`losses 0`，全部 `72:chain=CATCH/expect=PASS → 74:chain=PASS/expect=PASS`）：`N13-P01,N13-P02,N13-P03,N13-P04,N13-P05,N13-P06,N13-P07,N13-P11,N13-P12,N13-P14,N13-P15,N13-P16,R10-CTX-07,R10-CTX-08,R10-CTX-09,R10-CTX-10,R10-CTX-11,REAL-BOUND`。

判据（逐条给确定结论）：
1. **同一批题/同一真值**：68 条两版 `id/text_head/tokens/expect` 相同（3 翻标已剔除），本会话按 id 对齐复现 ✔（`COMPARABILITY_AUDIT.md:183,338`）。
2. **模型输出确实变了**：18 行 `CATCH→PASS`；72 版这 18 行 `layer_unresolved` 合计 22、74 版合计 0；74 版全表 `layer_unresolved>0` 的行数 = 0，72 版 = 18（§6.0 命令 2）。`chain_conflicts_total` 两版恒 31 ⇒ 变的是「冲突是否被裁决」而非冲突数 ✔。
3. **每一分都能追到具体行与具体规则**：本会话用 `P.resolve_conflicts` 重放**全部 18 条**（不只 3 条），输出 `gains with K3+K9 present = 18 / 18`；17 条 `n13_kind=A|B`、`rules=['K3','K9']`、`verdict=PASS`；`REAL-BOUND` 用 90 字 `text_head` 重放得 `spans=0`（必须按 `_gp_regression.py:104,106-107` 读全文 `LEDGER_BOUND_VOLUME.md` 才得 `spans=7`、`rules` 含 `('K3','K9')` 与 `('K5',)`、`pass=7`）。⇒ 18/18 逐行追到 `_gp_pipeline.py:168-171` 的「K3 冲突 + K9 精筛覆盖宽进」，**无一分不可归因** ✔（§6.0 命令 4）。根因：72 版是三层 problems 朴素并集（`_gp_regression.py:147-149` 注释、`GATE_PIPELINE_COMPOSE.md:431`），74 版是逐 span K1–K9 `ADJUDICATED`。
4. **但前提不成立**：`chain` 两版导出定义不同（M 轴变更，`COMPARABILITY_AUDIT.md:221`）；72 版生成脚本全仓与 git 历史零命中（本会话 `find . -iname "*v1_union*" -type f` 只出 `.json/.txt`；`git log --all --oneline --name-only | grep -i v1_union` 无输出，`COMPARABILITY_AUDIT.md:310,343` 标「未验重跑」）；K9 是为消这 20 条 FP 而写（`_gp_pipeline.py:168-172`、`GATE_PIPELINE_COMPOSE.md:431`、`COMPARABILITY_AUDIT.md:219,344`），18 条 = 72 版 20 条 FP 中修好的 18 条、仍 FP=2（`REAL-SLOT/REAL-TRUTH`，§6.0 命令 2）⇒ **in-sample 循环论证** ✘。

**确定答案**：`+18` **可归因于「在 68 条冻结考题上把合成裁决从三层朴素并集换成逐 span K1–K9」这一处实现替换（配对效应）**；**不可归因于「算法改进/更好/泛化」= 0 分**。条件性：in-sample、E 轴未验重跑、M 轴列定义已变、仅 `chain` 列、仅这 68 个 id。

### 3.2 flipped3 = +3 逐条判「改标注是否合理」

本会话实跑（§6.0 命令 5）：三条 `naive/r10/r12/n13/chain/layer_conflicts/layer_unresolved` **7 个判定列两版逐列相同 = True**（例如 C05 两版都是 `[CATCH,PASS,PASS,PASS,PASS,0,0]`），只有 `expect` 与 `note` 变：
```
GP-C05 '未核 grep 结果：已入账 0 命中'  CATCH→PASS
  note72='★ 三层全说放过但实际真断言（构造）' → note74='前置否定标签 + A 检索结果；人工判检索结果，非完成断言'
GP-C06 '未核 grep 结果：已生效 0 命中'  CATCH→PASS  note72='★ 同族构造（已生效）' → note74='同上（已生效）'
GP-C07 '未核：已入账 grep 结果 = 0 命中' CATCH→PASS  note72='★ 前置否定标签 + A 结果' → note74='同上（标签在冒号前）'
```
`COMPARABILITY_AUDIT.md:105-116` 逐字同；`:139` 定性为「什么算真断言」的判读口径改写，属真值判读本体变更，**不是注记润色**；`_gp_regression.py:113-115` 现写 `PASS`。

逐条判（依据 = 上游 A 类「检索结果非完成断言」口径 `GATE_N13_QUOTED_ASSERTION.md:23`「A = 检索动作（`grep`/清点/核查/`有没有…？`/`grep=0`/`0 命中`）」、`_gp_DESIGN.md:237`「`grep 结果：已生效 0 命中` … 按 K9 判 PASS」）：
- **GP-C05**：`未核` 标签 + `grep 结果` + `0 命中`，是检索结果读数，不是「本笔已入账」完成断言 ⇒ **改得合理**。
- **GP-C06**：仅把完成词从「已入账」换成「已生效」，结构完全相同 ⇒ **改得合理**（同族）。
- **GP-C07**：标签移到冒号前，`grep 结果 = 0 命中` 仍是读数 ⇒ **改得合理**。

**反证边界（不能只挑有利证据）**：本会话实跑列出 72 版含 `0 命中/grep=0` 的行，`N13-P02/P11/P12/P14/P08/P10` 都 `expect=PASS`，唯 `GP-C05/C06/C07` 标 `CATCH` ⇒ **72 版内部不自洽**，74 版改 `PASS` 使口径一致。但标注手册未冻结封 SHA（`COMPARABILITY_AUDIT.md:421`）、无双盲 κ（`:357`）、`_n13_regression.py:110` N24「`grep 结果：已入账`（裸完成词）→ 拿不准默认 FAIL」与 C05 只差「`0 命中`」读数（`GATE_N13_QUOTED_ASSERTION.md:311`）⇒ 三条判为「**合理但未经冻结手册/双盲 κ 核对，未证实绝对正确**」。

**确定答案**：`+3` **0 分来自模型**（模型输出一个字节没改，7 列逐列相同），**3 分纯来自改标注 = 修正基线**，不可归因于算法。

### 3.3 修正基线 vs 改良（确定区分）

72 版三条 `expect=CATCH` 而 `chain=PASS` 被记为 FN（`CHAIN_VS_SINGLE.md:74` 明写 72 版 N13 的 `fn=4` 正是 `C03/C05/C06/C07`）；翻标后其中 3 条自动「判对」。把标注统一到 74 口径：`72 = 48+3 = 51/72`，`74 = 69/74`，`69 − 51 = 18` ⇒ **`+21` 立刻缩成 `+18`，3 分蒸发**。这 3 分是「72 版基线被错标注压低」的虚增，是 **baseline correction**，不是「模型变强 3 分」（`COMPARABILITY_AUDIT.md:116,310`、`CHAIN_VS_SINGLE.md:74`）。注意 `51/72` 与 `69/74` 分母/样本集/列定义/评分器都不同，**仍不可比**，此式只用于说明 3 分来源。

### 3.4 new3 / deleted1 的可归因性

两项都是 **0 分可归因于算法、0 分可归因于标注修正**（分子贡献恒 0 的算术恒等式，见 §2.3）。`new3` 对 74 版是负向信息（暴露共同盲区：`_gp_DESIGN.md:284-287` A1 = R12 枚举表外分离型双重否定、A2/A3 = `spans=0` 时 K7 死分支），只是评分函数只数 `correct`；`deleted1` 是换 id 换族（§5.1）。但两项改变了分母与类别先验（`by_family` 7→8，新族 `GP_ALLPASS_TRUE_ASSERTION` 未登记进两版相同的 `sources` 键，本会话实跑 `in 74 sources? False`），故 pp 口径不可直接相减（`COMPARABILITY_AUDIT.md:148,468`）。

### 3.5 ★ +21 里有几分可归因于「算法改进」—— **严格答案：0 分**

| 分项 | 分数 | 确定答案（不用「部分可归因」） |
|---|---|---|
| frozen68 | +18 | **可归因于「实现替换」18 分（条件性、in-sample、不可泛化）；可归因于「算法改进」0 分** |
| flipped3 | +3 | **可归因于「修正基线」3 分；可归因于「算法改进」0 分** |
| new3 | +0 | **算法 0 / 标注 0**，全 FN |
| deleted1 | +0 | **算法 0 / 标注 0**，本来 0 分 |
| 合计 | +21 | **可归因于「算法改进」= 0 分** |

理由：「算法改进」隐含「在新数据上更好」的泛化主张；本会话无盲留出集（`CHAIN_VS_SINGLE.md:129,131`「训练集=测试集」「正式盲留出集本次未做，标未验」；`COMPARABILITY_AUDIT.md:357` 把 κ 列为设计），74 行 train=test（`EVIDENCE_INDEPENDENCE.md:157`）。**唯一放宽口径**（若把措辞放宽为「在冻结题集上换掉一处实现带来多少分差」）= 18 分，且必须同时带 §4.4 外推边界。此答案与 `_sd_report.md:209-219` 的「严格答案：0 分」一致（复核 verdict `confirmed`，见 §6.1）。

---

## 4 配对统计（frozen68）

### 4.1 配对 b/c 与 exact binomial p、CI（本会话实跑，§6.0 命令 2/8）

```
frozen n= 68 b= 18 c= 0 n_discordant= 18
p_two_sided_exact (small-p method) = 7.62939453125e-06 = 2*2^-18 = 1/131072
p_one_sided = 3.814697265625e-06
Clopper-Pearson 95% CI lower = 0.8146980318621477 upper = 1.0  (sf(b,p_low)=0.025 实算校验)
Wilson 95% CI = 0.8241207763533424 1.0
paired acc diff = 18/68 = 0.2647058823529412
bootstrap 200000 次 (seed=20261109) percentile 95% CI = [0.16176470588235295, 0.36764705882352944]
normal SE = 0.05350050552272051  (sqrt(p(1-p)/n) 口径；样本方差/(n-1) 口径 = 0.053898284274840544)
```
与编排方 `paired_b=18/paired_c=0/paired_n=18` 精确一致，亦 `COMPARABILITY_AUDIT.md:334-335` 逐字一致。H0：不一致对两方向等概率 p=0.5（McNemar 精确版）。数字全部由本会话 `math.comb` + `Fraction` + 二分求 CP + `statistics.NormalDist().inv_cdf(0.975)=1.9599639845400536` + bootstrap 实算，未拿上游数值充当「已跑」。注：`_sd_report.md:255` 的 `SE=0.0535` 与 `_sdv_recheck.py:109` 的 `0.05389828` 是两种口径，本会话两个都实算并在上列并列，不掩盖差异。

### 4.2 这个 p 能否支撑「算法更好」—— **不能**

1. p 只测「18 个不一致对是否随机对称」，不测目标总体更优；这一侧恰好是「72 误拦的 PASS 题被放行」。
2. **in-sample**：K9 为消 20 条 FP 而写（`_gp_pipeline.py:168-172`、`GATE_PIPELINE_COMPOSE.md:431`、`COMPARABILITY_AUDIT.md:219,344`），18 条正是点名失败形态 ⇒ 「照着答案改完的答案对上了」是循环论证。
3. **样本非独立**：18 条只有 16 个独立 `text_head`（`N13-P01↔R10-CTX-10`、`N13-P05↔R10-CTX-07` 逐字重复），聚 3 族 `{N13_POS:12, R10_CTX:5, REAL3:1}`（§6.0 命令 2）；按独立行的 `2^-18` 高估样本量。
4. **对照物不是「更好」**：frozen68 内 74 版 `chain 66/68` 仍劣于 `n13 68/68`（`b=2 c=0 n=2 p=0.5`，不显著）；72 版 `chain 48/72` 劣于 `n13 68/72` 的 `p=1.9073486328125e-06` 只关于**已弃用并集算法**（`COMPARABILITY_AUDIT.md:337,346`）。`CATCH` 召回两版 36/36 不变（§6.0 命令 2）。
5. E 轴未验重跑、M 轴列定义变 ⇒ 前提「两格只 I 不同」不成立（`COMPARABILITY_AUDIT.md:221,343`）。

**p 支撑的极窄一句话**：「在这 68 条冻结行上，两版 `chain` 列的 18 处不一致全部朝同一方向（72 误拦→74 放行）」。**不支撑「算法更好」「合成链优于单层」或任何总体/泛化主张**（`COMPARABILITY_AUDIT.md:328,340`）。

### 4.3 in-sample 修正方案（给方案，未算出修正后真 p，标未验）

**核心认识**：in-sample 偏差**不能靠给 p 乘常数修好**，`2^-18` 的抽样模型本身失效（18 条不是从目标总体独立抽的，是被 K9 失败清单选出的）。按 `COMPARABILITY_AUDIT.md:357-362`、`CHAIN_VS_SINGLE.md:278,280`：

- **主方案（本会话未跑，未验）**：物理隔离盲留出集 + 一次性预注册 + 出题人≠改规则人≠批卷人 + `train/dev/test` 封 SHA + 双盲 κ≥0.8 + N19–N26/GP-A 只进 train，**在 test 上重算 b/c 与 exact binomial** —— 这才是有效 p。
- **降级校正（现有数据，本会话逐项实算）**：
  - (i) 按独立单元：`16 文本` → `p = 2×2^-16 = 3.0517578125e-05`；按 `3 族` 符号检验 → `p = 2×2^-3 = 0.25`（**不显著**）。
  - (ii) 设计效应 `n_eff = n/(1+(n−1)ρ̄)`：`ρ̄=0→18 / 0.3→2.9508 / 0.5→1.8947 / 0.8→1.2329 / 0.9→1.1043 / 1.0→1.0`；18 条全属同一 K9 分支，保守 `ρ̄≈1 ⇒ n_eff≈1`。
  - (iii) 多重比较：Bonferroni 临界 `0.05/7.62939453125e-06 = 6553.6`，即 `M ≥ 6554` 才抹掉显著性；但调参搜索次数 `M` 无日志可定 ⇒ **标未验，不得反推「p 仍稳健」**。
  - (iv) post-selection 条件分布：在「已知这 18 条是 K9 失败样本」条件下观测 18/18 修好的概率 ≈ 1、信息量 ≈ 0。
- **报法**：把 `p` 降格为「**描述性内部效度指标**」，同时给 `n_eff≈1`、族级 `p=0.25`、盲留出「未验」；**不得把 `p=7.63e-06` 单独写成显著性证据**。修正后的真实 p = **未验**（不补造）。

### 4.4 外推边界（写死）

**能外推到**：仅这 68 个 id（§3.1 清单，完整 68 条见 `COMPARABILITY_AUDIT.md:332`）；仅冻结 `text_head`（前 90 字）/`tokens`/`expect`（第 91 字后正文属「未验」，`COMPARABILITY_AUDIT.md:141`；本会话实跑 `REAL-BOUND text_head` 长 92 字仍 `spans=0`，须读全文才复现 K3+K9）；仅「三层朴素并集 → 逐 span K1–K9」一处替换；仅 `chain` 列；仅「18 条 `expect=PASS` 误拦被放行，CATCH 召回 36/36 不变」。

**不能外推到**（`COMPARABILITY_AUDIT.md:342-346,468`）：❌ 全语料 / 74 条 / 72 条（3 翻标 + 2 真新题 + 1 换 id 不在 F 内）；❌ 「合成链 vs 单层」（对照物是同一 `chain` 的两种算法，frozen68 内 `p=0.5`）；❌ 目标总体 / 生产置信界 / 泛化（train=test，无盲留出；`EVIDENCE_INDEPENDENCE.md:157`）；❌ 新形态（`spans=0` 死分支、词表外同义改写、分离型双重否定仍全漏，`_gp_DESIGN.md:284-287`）；❌ 「其余输入相同」断言（E 轴未验重跑）；❌ 与另一版本数字相减或用 `→` 连接不同 `n` 的分数。

---

## 5 GP-C03 / GP-A1 连带追查

### 5.1 同文本换 id 的原因（能证实 / 未验分开）

本会话实跑（§6.0 命令 5）：`GP-C03[72]` 与 `GP-A1[74]` 除 `id/family/note` 外逐字段相同；差异仅 `id: GP-C03→GP-A1`、`family: GP_CONFLICT→GP_ALLPASS_TRUE_ASSERTION`、`note: 'GV-L 分离型双重否定残余（人工真值=肯定）'→'分离型双重否定=肯定；编排方背景点名的 GV-L 残余'`。`GP_ALLPASS_TRUE_ASSERTION` 新族未登记进 `sources`（两版 `sources` 键逐字相同，本会话实跑 `in 74 sources? False`）。

- **能证实（字段级 + 语义级）**：`_gp_regression.py:121-130` 把三条「三层全说放过但实际有真断言」构造样本成族写入 `GP_ALLPASS_TRUE_ASSERTION`，此句被收编并顺号命名 A1；72 版归在 `GP_CONFLICT` 但它根本不是冲突——`r10=negation / r12=0 / n13=C 转发 R10`，三层给同一个（错的）答案，`layer_conflicts=0`、`layer_unresolved=0`（本会话两版转储）。`_gp_DESIGN.md:285`「A1 是共同盲区，不是冲突」、`GATE_PIPELINE_COMPOSE.md:216`「无冲突，共同盲区，判错」⇒ 换族是分类纠错，换 id 是随之的编号重排。按文本键 = **0 删 + 2 真新增 + 1 换 id**（`COMPARABILITY_AUDIT.md:99`）。
- **未验**：盘上无任何「为什么换 id」的书面裁决/变更单；`COMPARABILITY_AUDIT.md:444-450` 记原始派发任务书未留盘 ⇒ 书面动机**未验**，只能推断到「成族重编 + 分类纠错」。

### 5.2 ★ 任务第四步前提更正（必须写）

任务书称「72 版判 CATCH、74 版也判 CATCH」。本会话实跑：两版 `expect` 都是 `CATCH`，但 **`chain` 都是 `PASS`（漏判）**：
```
74 GP-A1 expect CATCH chain PASS naive CATCH r10 PASS r12 PASS n13 PASS | 亦非不宣告 N-4 正式绑定已生效
72 GP-C03 expect CATCH chain PASS naive CATCH r10 PASS r12 PASS n13 PASS | 亦非不宣告 N-4 正式绑定已生效
```
`_gp_regression_out.txt:47` / `_gp_regression_v1_union_out.txt:45`、`GATE_PIPELINE_COMPOSE.md:392`、`_gp_DESIGN.md:280`、`COMPARABILITY_AUDIT.md:308` 逐字一致。`r12_regex=false`（即 `r12=0`）属实：本会话实读 `_dg_step34_out.json:step3a_gaps[0] = {"construct":"亦非不","r12_regex":false,"h5_regex":true,"dg_catch":true,"dg_hit":"亦非不宣告"}`、`_dg_step34.py:41` 为 19 式首项。

### 5.3 74 版 CATCH 靠什么「抓到」—— 分列追查（本会话重放，§6.0 命令 3/9）

```
text='亦非不宣告 N-4 正式绑定已生效' tokens=['已入账','已追加','已生效']
R10 hits = [{'token':'已生效','pos':14,'kind':'negation','neg_count':2,'in_span':False}]
R12 hits = []
N13 details = [{'kind':'C','exempt':true,'rule':'C 否定式（R10 negation 已覆盖，微段内直接否定）','r10_kind':'negation'}]
span summary = {'spans':1,'catch':0,'pass':1,'conflicts':0,'unresolved':0}
ROW tok=已生效 pos=14 r10=PASS r12=ABSENT n13=PASS n13_kind=C n13_veto=False rules=['K5'] verdict=PASS
```
`chain` 列导出（`_gp_regression.py:145-150`）只数 `ADJUDICATED/NEEDS_HUMAN` = 0 ⇒ **`chain=PASS`**。注：`gate_check` 顶层 `verdict=FAIL` 来自 R9/R11 独立项（本会话实跑 `problem rule_ids=['R9','R9','R9','R11']`），`_gp_regression.py:146` 明写「R9/R11 是独立项，不混入本判定」，故不影响 `chain`。**74 版评分列什么都没抓到，逐 span 走 `_gp_pipeline.py:179-180` 的 K5 → PASS**；根因 `_gp_DESIGN.md:285`（`DOUBLE_NEG_RE` 是枚举构式，「亦非不」GV-L 分离型不在表内；N13 的 C 只是转发 R10）。

`CATCH` 只出现在三列，均非 74 版评分列：
1. `naive=CATCH`：`已生效` 字面命中，非语义判别（`_gp_regression.py:136-137`）。
2. **`v12=CATCH` = S3 DEFAULT fail-closed**：本会话实跑 `_v12_rule.py` `classify_v12('亦非不宣告 N-4 正式绑定已生效',14,17,'已生效')` →
   `{"verdict":"V2","hard":[],"weak":[],"override":"","review_flag":true,"reason":"无任何 V1 形状、亦无硬性完成宣称：机器判不了，fail-closed 默认 V2（宁可误拦），须人工复核或改写为显式规定式"}`（`_v12_rule.py:167-170`；`EVIDENCE_INDEPENDENCE.md:169,173` 逐字「**S3 DEFAULT「判不了→fail-closed」，不是语义识别**」「任何拿不准的行都会同样 CATCH」；`_eind_verify_out.json:302` `only_default=true`）。`_cs_holdout_out.txt:22` 的 `U-N12 … v12=CATCH` 就是这一列。
3. **`DG_chain=CATCH`**：`_dg_step34_out.json:590-592` 本会话实读 `{"id":"GP-A1_DG","expect":"CATCH","dg_chain":"CATCH"}`（其 `adjudicated` 数组实际在 `:601-603`：`裁决=CATCH rules=K1`）；`_dg_DESIGN.md:1-5,242-251` 明写是**内存 `_Shim` 设计实验、未实装**（`EVIDENCE_INDEPENDENCE.md:195` 亦记所有第四层变体均未实装）。

### 5.4 fail-closed vs 语义识别 —— **兜底碰巧，且更弱：恒真兜底**

**确定答案**：S3 DEFAULT 对**任何**拿不准的行都返回 CATCH，不读「亦非不」、不识别双重否定（`_v12_rule.py:167-170`、`EVIDENCE_INDEPENDENCE.md:169,173`）；在这句上「判对」只是先验 `expect=CATCH` 恰好与恒 CATCH 兜底同号，是**恒真兜底在正类样本上的必然命中，信息量 = 0**，不算算法改进。代价可量化：V12 单层 74 行 `47/74`（`fp=18`），装进链 `naive_OR_all4` 净 **−13**（56/74），只有限死 `spans==0` 且单调 OR 才净 `+1`（70/74，`±2.7%` 不显著）且 **GP-A1 仍漏**（`EVIDENCE_INDEPENDENCE.md:177,188-195`）。DG 的 CATCH 靠「扩构式表」定向修复，仍是 in-sample 且未实装。

### 5.5 对 +18 的影响 —— 直接影响 0，间接抽掉一根泛化支柱

- **直接影响 = 0**：本会话实跑 18 条增益 74 版 `layer_unresolved` 合计 0、全 74 表无 `layer_unresolved>0` 行；`_gp_pipeline.py:175` 的 `FAIL_CLOSED` 分支必置 `unresolved=True` ⇒ 18 条**没有一条来自 FAIL_CLOSED / S3 兜底**，18/18 追到 K3+K9（§3.1）。且该句本身是 `onlyB(GP-C03)/onlyA(GP-A1)`，两版都 0 分，不在 F 内，按分解恒等式对 `+18` 无贡献。
- **间接影响**：`+18` 是清一色放行方向（18/18 `expect=PASS` 的 FP 消减），与「正类召回兜不住」是**同一 K9 取舍两面**（`_gp_DESIGN.md:287`「A1 正是这个代价的兑现」）；`CATCH` 召回 36/36 两版不变 ⇒ `b=18,c=0` 的方向偏倚使「算法更好」更不成立。若有一条增益靠 fail-closed 碰巧得到，那一条须按铁律改判「**不可归因**」——本会话已逐行排除，本例不成立；但报分差时仍须把「该分由哪条规则/哪列产生」列进 §6.3 清单。V12/DG 的 CATCH 不得计入 `69/74`，也不得用来给 74 版加分（`COMPARABILITY_AUDIT.md:345`）。

---

## 6 复核回件 · 结论 · 清单 · 未验项

### 6.0 本会话实跑命令与输出（证据台账）

1. **指纹 10 件**：`python -I -X utf8 -B -c "<9 件 hashlib + os.walk 找 16649 字节件>"` → `9 explicit: 9 / 9`，`16649-byte secret file hits: [lead\evidence_indep_20261109\_ei_n13_predicates_src.py, lead\gate_n13_20261109\_n13_predicates.py]`（§2.1 逐字）。工作结束后复跑仍 10/10 MATCH；只读域目录 mtime 最早 `gate_n13_20261109 12:32:13`、次 `gate_pipeline_20261109 13:51:58`、最晚 `comparability_20261109 17:24:22` / `evidence_indep_20261109 17:16:19`，均早于本会话，无本次写入。
2. **分解/配对/pp/bootstrap 复现**：`python -I -X utf8 -B "D:/Project/ra2-campaign-forge/lead/score_decomp_20261109/_sdv_recheck.py"` → PART 1–6 输出逐字（§2.2、§4.1）；`losses 0 []`、`flip judge cols identical both versions? True`、`72 FP in frozen = 20 repaired by 74 = 18 still FP = 2`、`still-FP ids ['REAL-SLOT','REAL-TRUTH']`、`unique text_head among 18 = 16 of 18`、`family Counter = {'N13_POS':12,'R10_CTX':5,'REAL3':1}`、`74 layer_unresolved on gains total = 0`、`74 rows with layer_unresolved>0 = []`、`CATCH recall frozen 72 = 36/36 / 74 = 36/36`、`n13 correct frozen 74 = 68 chain = 66`、`bootstrap 200000 = [0.16176470588235295, 0.36764705882352944]`。**该脚本 PART 7 在 `:160` 抛 `TypeError: r10_context() missing 1 required positional argument: 'end'`** —— 本会话遵守「不改任何脚本」，未修它，改用命令 3 独立内联补跑。
3. **GP-A1 74 版 chain 重放（补 PART 7）**：`python -I -X utf8 -B -c "<load _gp_pipeline.py；P.gate_check / run_layers 重放>"` → `gate_check verdict=FAIL summary={'spans':1,'catch':0,'pass':1,'raise':0,'conflicts':0,'unresolved':0}`、`ROW tok=已生效 pos=14 r10=PASS r10_kind=negation r12=ABSENT n13=PASS n13_kind=C n13_veto=False rules=['K5'] verdict=PASS`、`R10 hits=[{'token':'已生效','pos':14,'kind':'negation','neg_count':2,'in_span':False}]`、`R12 hits=[]`、`N13 details=[{'kind':'C','exempt':true,...,'r10_kind':'negation'}]`。
4. **18 条增益逐行 K3+K9 全量重放**：`python -I -X utf8 -B -c "<P.resolve_conflicts 对 18 条；REAL-BOUND 读全文 LEDGER_BOUND_VOLUME.md>"` → 18 行逐条 `hasK3K9= True`、`gains with K3+K9 present = 18 / 18`；`REAL-BOUND` 用 `text_head`（92 字）得 `spans=0 hasK3K9=False`，用全文（43705 字）得 `spans=7 hasK3K9=True pass=7`。机制落在 `_gp_pipeline.py:168-171`。
5. **翻标逐条 / GP-C03≡A1**：`python -I -X utf8 -B -c "<转储 3 flips 全字段 + 72 版 0命中行 + GP-C03/A1 差 + by_family/sources>"` → 7 判定列 `identical=True` 三条；`GP-C03 vs GP-A1 except id/family/note identical? True`；`family GP_CONFLICT -> GP_ALLPASS_TRUE_ASSERTION`；72 版 `N13-P02/P03/P04/P07/P08/P10/P11/P12/P14/P15/P16/R10-CTX-08/R10-CTX-11 expect=PASS`，`GP-C05/C06/C07 expect=CATCH`；`GP_ALLPASS_TRUE_ASSERTION in 74 sources? False`。
6. **统计常量**：`python -I -X utf8 -B -c "<math/statistics 实算>"` → `p_two=7.62939453125e-06`、`p_one=3.814697265625e-06`、`SE 两口径 0.05350050552272051 / 0.053898284274840544`、`z=1.9599639845400536`、`Wilson lower=0.8241207763533424`、`p 16-text=3.0517578125e-05`、`p 3-family=0.25`、`Bonf=6553.6`、`n_eff ρ̄=0.3→2.9508 / 0.5→1.8947 / 0.8→1.2329 / 0.9→1.1043 / 1.0→1.0`。
7. **脚本缺失复核**：`find . -iname "*v1_union*" -type f` → 仅 `_gp_regression_v1_union_out.json` / `.txt`；`git log --all --oneline --name-only | grep -i v1_union` → 无输出。与 `COMPARABILITY_AUDIT.md:310,343`、`CHAIN_VS_SINGLE.md:76` 一致。
8. **r12=0 / DG / v12 / 绑定行格式**：`python -I -X utf8 -B -c "<读 _dg_step34_out.json；_sd_report.md 绑定行正则>"` → `step3a_gaps[0]={"construct":"亦非不","r12_regex":false,"h5_regex":true,"dg_catch":true,"dg_hit":"亦非不宣告"}`；`_dg_step34_out.json:590-592` 为 `id/expect/dg_chain`，`adjudicated` 在 `:601-603`（复核回件已记此行号微瑕）；`_sd_report.md` 绑定行 `total=7 compliant=7`；`classify_v12` 输出见 §5.3（命令 2 内亦实跑）；`_sd_report.md` 实算 `sha256=58e71cefc024d6874b353cde69d1b39b450f4a79ad08c35e9d235c01dbd725ff / 49202 B`。
9. **gate_check FAIL 归因**：`python -I -X utf8 -B -c "<打印 problem rule_ids>"` → `['R9','R9','R9','R11']`、`ADJUDICATED/NEEDS_HUMAN count = 0`、`=> chain column = PASS`（§5.3）。
10. **源码行核对**：本会话打开并逐行核对 `_gp_regression.py`（全文，尤 `:104,113-115,121-130,136-137,143-150,159`）、`_gp_pipeline.py`（全文，尤 `:32,98,168-180,223-265`）、`_v12_rule.py:167-170`、`GATE_N13_QUOTED_ASSERTION.md:23`、`_gp_DESIGN.md:237,274-287`、`EVIDENCE_INDEPENDENCE.md:167-195`、`_dg_DESIGN.md:1-5,240-251`、`_dg_step34.py:40-60`、`COMPARABILITY_AUDIT.md:99,105-116,131-139,217-221,303-313,332-347,357-363,416-436,464-468`、`CHAIN_VS_SINGLE.md:71-76,110-114,125-133,276-282`、`GATE_PIPELINE_COMPOSE.md:429-431`、`_sd_report.md`（全文 442 行）、`_sdv_recheck.py`（全文 182 行）。

### 6.1 复核回件（绑定行格式固定）+ verdict 如实记

被核对象 SHA256 = d3543657aa4f9914c9023710f6daef8348a12ca0aa11957110e8b7c45baec6fe，字节数 = 38575

（格式自检：写「被核对象 SHA256 = 」紧跟完整 64 位十六进制，中间无路径、括号、星号、反引号或空格；随后「，字节数 = 」再写数字。本会话实跑正则 `^被核对象 SHA256 = ([0-9a-f]{64})，字节数 = (\d+)$` 对 `_sd_report.md:36,38,40,42,44,46,48` 得 `7/7 compliant`。）

**复核 verdict 如实记**：编排方给的 `【复核】` 字段 `verdict = "confirmed"`、`ranCommands = 36`、7 项点名检查全部通过、未发现「模糊答案」与「in-sample p 未修正」两大陷阱；其「登记级微瑕」4 条（① 原报告 §3(a)/§4(d) 只重放 3 条却写「逐行核到 K3+K9」——本会话命令 4 已补跑 18/18 成立，但 `REAL-BOUND` 须读全文，原报告未交代；② `_dg_step34_out.json` `adjudicated` 行号 `:590-592` 偏移，实际 `:601-603`，本会话命令 8 已核；③ Wilson 下界末位 `0.8241207763533425` vs `0.8241207763533424` 属浮点差，本会话命令 6 实算后者；④ 原报告 `ranCommands=27` 属其会话内计数，本会话无法独立核对，标未验）。**本件按 `confirmed` 登记，不标 `unconfirmed`**；若 `verdict` 为 `refuted` 或 `partial` 才须标 `unconfirmed`——本次不是。本会话自身的独立复核（命令 1–10）与 `_sdv_recheck.py` 的 PART 1–6 一致；`_sdv_recheck.py` PART 7 的脚本缺陷如上如实登记，未修改任何脚本。

### 6.2 结论：+21 的诚实表述 / 唯一站得住的数字 / 判不了什么

**一句话版**：
> 「+21 = frozen68(+18) + flipped3(+3) + new3(+0) + deleted1(+0)；其中 3 分是把 3 条真值标注从 CATCH 改成 PASS（模型 7 个判定列逐列未变，属**修正基线**），18 分是在 68 条冻结考题上把合成裁决从三层朴素并集换成逐 span K1–K9 的**配对**差值（**in-sample**、72 版脚本未留盘、`chain` 列定义已变），新增 3 条全漏、删 1 条本来 0 分；**可归因于「算法改进」= 0 分**，两版 `48/72` 与 `69/74` 不可比，`+21` 与 `+26.58pp` 无因果含义。」

**解释版**：72 版（朴素并集）`chain 48/72=66.67%`，74 版（逐 span K1–K9）`chain 69/74=93.24%`，`raw delta 21 / +26.58pp`。按 id 对齐：共有 71 条，3 条 `expect` 翻转、68 条冻结；74 独有 `GP-A1/A2/A3`，72 独有 `GP-C03`（与 `GP-A1` 同文本换 id 换族，`GP_CONFLICT→GP_ALLPASS_TRUE_ASSERTION`）。分解 `18+3+0+0=21`。3 条翻标（`GP-C05/C06/C07`）按上游 A 类「检索结果非完成断言」口径判为「合理但未经冻结手册/双盲 κ 核对」，72 版内部同形行不自洽；把 72 版基线修正为 `51/72` 后 `+21` 缩成 `+18` ⇒ **修正基线**而非改良。18 分逐条追到 `_gp_pipeline.py:168-171` 的 K3+K9（72 版 20 条 FP 修好 18 条），配对 `b=18 c=0 n=18`、`exact binomial` 双侧 `p=7.62939453125e-06`、CP 95% CI `[0.8147,1.0]`、bootstrap 配对差 `[0.1618,0.3676]` —— 但这是同一批、且为修这批失败样本而调出的题上的 **in-sample** 收益：18 条只有 16 个独立文本、聚 3 族（族级 `p=0.25`）、`n_eff(ρ̄≈1)≈1`；`chain` 两版导出定义不同（M 轴）、72 版生成脚本全仓与 git 零命中（E 轴「未验重跑」）；frozen68 内 `chain 66/68` 仍劣于 `n13 68/68`（`b=2 c=0 p=0.5`）。`GP-C03/GP-A1` 的 `CATCH` 只出现在 `naive`（字面）、`v12`（**S3 DEFAULT fail-closed 恒真兜底**）、`DG`（未实装内存 Shim）三列，**74 版评分列 `chain=PASS` 根本没抓到**（任务第四步前提更正，`r12=0` 属实）。故 `+21` 与 `+26.58pp` 必须整体撤回（`COMPARABILITY_AUDIT.md:301-313`）。

**当前唯一站得住的数字**（`_sd_report.md:378-388`、`COMPARABILITY_AUDIT.md:340`）：
> **只有 frozen68 上的配对 `b=18 / c=0 / n_discordant=18`，及其配套 `exact binomial` 双侧 `p=7.62939453125e-06`、CP 95% CI `[0.8147,1.0]`、bootstrap 配对正确率差 `18/68=0.2647 [0.1618,0.3676]`** —— 且必须标为「**描述性内部效度指标**」，同时声明 in-sample、E 轴未验重跑、M 轴列定义已变、不得外推、不得写成「算法更好」。

其余全部站不住或只作留盘观测值：`48/72`、`69/74`、`+21`、`+26.58pp`（不可比）；`51/72`（仅说明 3 分来源）；`chain vs n13` 的 `p=0.5` 与 `p=1.9073486328125e-06`（后者只关于已弃用并集算法）；上游对齐 `b=0 c=3 p=0.25`（`CHAIN_VS_SINGLE.md:112`，本会话**引用未重跑**）；V12 净 `+1` / DG `GP-A1_DG=CATCH`（设计实验、未实装）。

**判不了什么（如实列）**：① 判不了「算法有没有改进 / 能否泛化」（无盲留出、无 κ、train=test）；② 判不了「合成链 vs 单层谁更好」（frozen68 内 `p=0.5`，`COMPARABILITY_AUDIT.md:328`）；③ 判不了「72 版 48/72 怎么算出来的」（生成脚本零命中，E 轴未验重跑）；④ 判不了「除合成裁决外其余输入相同」（仅由四单层列相同反推，非脚本级）；⑤ 判不了 3 条翻标的「绝对正确性」（标注手册未冻结封 SHA、无双盲 κ、原始任务书未留盘，只能判「与上游 A 类口径一致、合理」）；⑥ 判不了「换 id」书面动机（无变更单，标未验）；⑦ 判不了第 91 字之后正文是否改动（`text_head` 是 `text[:90]`，`COMPARABILITY_AUDIT.md:141`）；⑧ 判不了 in-sample 修正后的真实 p（`M`、`ρ̄` 无日志可定，§4.3 给的是方案）；⑨ 判不了「74 版能抓到 19 式双重否定」（`chain=PASS`）；⑩ 判不了任何真机/运行时行为（零真机零采样）；⑪ 判不了上游对齐实验与 `_cmp_assert.py` 修正版（引用未重跑 / 未实装）；⑫ 判不了「+26.58pp 里 −2.59pp 之外还要归因到哪个分项」（跨分项 pp 不可加）。

### 6.3 报分差必附清单（`COMPARABILITY_AUDIT.md:416-436,457-467` 16+9 项，本任务补 ★3 项）

1. **五轴 manifest**：`S/G/I/E/M` 每轴每侧 `path + sha256 + bytes`，`hashlib` 复算任一失配 `sys.exit(1)`；2. **冻结语料**：逐行 `(id, 全文 sha256, tokens, expect, family, note)` 封 SHA，`n` 与类别先验入 manifest；3. **冻结标注手册**：「什么算正类」单独成文封 SHA，本轮禁止改 `expect`（本次 3 分即由此而来）；4. **冻结评测脚本**：生成每份 JSON 的 `.py` 同批留盘封 SHA，**无脚本的 JSON 作废**（72 版即反例）；5. **冻结依赖**：谓词/词表/骨架/语料路径逐件指纹；6. **变更单**：`changed_axis` 只能 1 个，old/new 指纹 + 签字，多轴拒跑；7. **全列重跑**：改一项即重算 `naive/r10/r12/n13/chain`，禁止复制旧列；8. **统一输入契约**：所有层（含 chain 第二词表 `n13_tokens`）消费同一份 `tokens`（`_gp_regression.py:143-145` 的分叉须消除）；9. **可比性 verdict 留盘**：`∈ {COMPARABLE, REPLICATION, COMPARABLE_CROSSED}` 且 `differing_axes ≤ 1`，断言先过单轴反例自检；10. **配对统计**：`b/c + exact binomial 双侧 p + bootstrap CI + macro-F1 + 按 expect 分报 FP/FN`，禁止只报点估计；11. **归因范围 scope**：写死 id 列表 +「不得外推」；12. **分母口径声明**：每个 `X/N` 带 `n`、CATCH/PASS 先验、被比较列导出规则；禁止用 `→` 连接不同 `n`；13. **留盘/复现状态**：脚本是否留盘、两侧是否全量重跑、独立复核 verdict、未验项逐条列出；14. **盲留出**：要写「更好/更差」必须有封 SHA test 集 + Cohen's κ ≥ 0.8，N19–N26/GP-A 只进 train；15. **★ 每一分的逐行归因**：`Δ` 拆到「哪个 id、哪一列、由哪条规则（K1–K9 / S3 DEFAULT / 翻标 / 增删）产生」，追不到行的分记「**不可归因**」；16. **★ 选择过程与有效样本量**：调参日志/预注册、`n_eff = n/(1+(n−1)ρ̄)` 或按独立文本/族聚簇后的符号检验 p；in-sample 的 p 标「描述性、非生产置信界」；17. **★ 兜底与恒真机制披露**：某分来自 `fail-closed` / `ABSENT→PASS` / `spans=0` 死分支 / 恒 CATCH 兜底时单列标出并判「不可归因于语义识别」（§5.4）；18. **收尾**：复算只读件指纹零漂移、`git status` 核对、不 commit 不 push。

### 6.4 未验项（不补造）

- 72 版生成脚本重跑（脚本不在盘，`find`/`git log` 零命中，E 轴 INDETERMINATE，标「未验重跑」）；
- 原始派发任务书 / 换 id 书面动机（未留盘，本会话 `grep` 只出审计描述，无决策记录，`COMPARABILITY_AUDIT.md:444-450`）；
- 标注手册冻结指纹与双盲 Cohen's κ（未做，`COMPARABILITY_AUDIT.md:357,421`）；
- 第 91 字之后正文是否改动（`text_head` 截断头，`COMPARABILITY_AUDIT.md:141`）；
- 正式盲留出集、post-selection 修正后真实 p、调参次数 `M`、`ρ̄` 真值（未做/未定，§4.3 只给方案）；
- 上游 74 条完整对齐实验 `b=0 c=3 p=0.25`（`CHAIN_VS_SINGLE.md:112`，本会话引用未重跑）；
- `_cmp_assert.py` 修正版与 2×2 交叉实测（`COMPARABILITY_AUDIT.md:266,297`，未实装/未跑）；
- V12 第四层与 DG 生成式是否实装进交付链（明写未实装，`EVIDENCE_INDEPENDENCE.md:195`、`_dg_DESIGN.md:1-5`）；
- 原报告 `ranCommands=27` 与复核 `ranCommands=36` 属各自会话内计数，本会话无法独立核对，标未验；本会话实跑为 §6.0 的 10 类命令调用。
