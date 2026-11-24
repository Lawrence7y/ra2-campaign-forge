# A 维缩减形式三项成分补证报告（A_REDUCED_FORM.md）

- 日期：2026-11-08。写域：`lead/a_dim_reduced_20261108/`（本件为该写域唯一新增交付文件）。
- 性质：对「A 维缩减形式」三项成分的**逐项补证登记**。只补证、不代裁——缩减形式是否立为新结论属判据采纳动作，本件不替用户裁定（见 §1、§6）。
- 上游只读输入：`lead/dtrigger_round2_20261107/`（`_dA_out.txt`/`_dA_design.md`/`_dA_probe_out.txt`/`_verify_A_out.txt`/`_verify_A_recompute.py`）、`lead/r2_final_grade_20261108/R2_FINAL_GRADE.md`、`lead/criteria_r3_verify_20261108/R2_BREAKPOINTS_CLOSURE.md`、`lead/stall_event_def_20261106/`、`lead/dstart_observable_20261107/S_OBSERVABILITY.md`、`lead/d30_ruling_20261106/RULING_D30.md`、`lead/dtrigger_compare_20261107/_cost_quota_data.json`、语料 `out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip`（104 件 measure_w*.json）。
- 同域同轮产物：补证 = `_ar_check.py`(25748B) + `_ar_out.txt`(24614B)（ranCommands=9）；复核 = `_verify_hy4_recompute.py`(19739B) + `_verify_hy4_out.txt`(8031B) + `_verify_hy4_stdout.txt`(8131B)（ranCommands=31）。
- 本件撰写会话实跑：① `python -I -X utf8` + hashlib 对 11 件指纹实算（六件编排方指纹 + 两件补证产出件 + 三件复核产出件，全部与回件一致，见 §5）；② 重跑 `python -I -X utf8 D:/Project/ra2-campaign-forge/lead/a_dim_reduced_20261108/_ar_check.py` → exit 0，`_ar_out.txt` 重写后 SHA256 不变（28cd3794…/24614，确定性复现，全部关键数字本次在终端再次输出）；③ 直读本件所引全部 file:line 原文。

## 1 目的与边界

**1.1 只补证、不代裁。** 本件登记三项成分（配额上界 / LB1 / 1621）的原文出处、本次实跑支撑度、oracle 依赖脱钩状态与依赖链未验项。是否把缩减形式立为新结论，属判据采纳动作：`R2_FINAL_GRADE.md:58` 原文已登记两读法——「按基线三条，G3 已足以判不可升格；若要把缩减形式（配额上界紧+LB1 限定特征类+1621/1681 离线可证计数）立为**新结论**走升格，则 **A 维需另派补证**（形式化缩减命题、界定适用域、处置 oracle/工程可行性未验项），且属判据采纳动作」。本件即该句所指「另派补证」的产物，但不越权作采纳裁定。

**1.2 强形式已被证伪的事实（补证前提）。** `_dA_out.txt` 三处强形式原文——`:191`「谓词无关的配额硬上界——…对任何 (t,f) 前缀判据一律成立」、`:206`「P(该次为真实 | 在 τ 处触发) <= A_real(τ)/A(τ)（对读 (t,f) 前缀的任意谓词皆成立）」、`:253`「in50_strict <= 1621/1681 = 96.4307% 是**任何 (t,f) 前缀判据的上确界**」——被实跑反例证伪（`R2_FINAL_GRADE.md:53` 登记原文；`_verify_A_out.txt:119` `precision=0.999404 (bound=0.332279)`、`:121` 差分反例 `precision=0.980432 > max_base_rate=0.332279`、`:124` SUMMARY PASS=54 FAIL=1，唯一 FAIL=`:111`）。`R2_BREAKPOINTS_CLOSURE.md:55` 判「已闭合项（通用措辞死亡）」；`:57-61` 登记「不可兼得」仅以缩减形式存活（存活①③④）。本件补证对象是缩减形式，不是被证伪的强形式。

**1.3 铁律遵守。** 零真机、零采样代码（补证脚本 import 仅 hashlib/json/os/re/statistics/collections/datetime/pathlib，无任何进程/采样类标识符，禁用字面量仅出现在铁律复述 docstring）；只读既有件未改（复核会话核对 `_dA` 系件哈希与 mtime 未变、git 无新提交）；唯一写域 = `lead/a_dim_reduced_20261108/`；未 commit、未 push。本件撰写会话同样零真机，未做任何在线测量。

## 2 缩减形式三项成分原文与出处

以下引文均为逐字抄录（复核会话分文件块比对：_dA_out.txt 57 行 / _dA_design.md 49 行 / R2_FINAL_GRADE.md 2 行 / R2_BREAKPOINTS_CLOSURE.md 5 行，不一致数均为 0，`_verify_hy4_out.txt:85-88`）。

**成分① 配额上界（存活①）** —— `_dA_out.txt:192-194`：

> 设配额组为 (trip,window)，26 个非空真实事件窗，N∈{1,3,5}。每组前 N 次「触发」消耗 N 个槽，
> 每槽最多对应 1 个真实事件，故 captured <= Σ_windows min(N, c_w) = 理想值，与谓词、前缀形状、
> 误触发多少完全无关（误触发只会让 captured 更小）。trip 口径同理。

推论 `:200-201`：「即使『:177 全合规 + 零误触发』的完美谓词存在，N=5 每窗 captured<=117/1681=6.96%」；实测最佳 W5=66/1681 (3.93%, D5-phase)。理想值 `:29`「每窗 W={1: 26, 3: 73, 5: 117}，每会话 T={1: 12, 3: 31, 5: 47}」。缩减形式定义：`R2_BREAKPOINTS_CLOSURE.md:58`「配额上界 captured ≤ Σmin(N,c_w) 是组合恒等式；反例恰好**达到** W={26,73,117} 理想值、未违反——上界成立且被证实紧，但它证的是**配额政策封顶**，不是谓词不可能性」。

**成分② LB1 限定特征类（存活③）** —— `_dA_out.txt:227`：

> 设 σ(r,a) = 平移不变前缀特征签名（间隔形状字 + 前一帧周期桶 + 前一游程长度桶），

`:233-234`：「下界 LB1 = max_R min_{s∈S_R} c(s)：为覆盖最贵的那条 R，W 至少含一个 s∈S_R，该 s 单独就使 >= c(s) >= min_{S_R} c 个不同 F 被强制触发（去重后仍成立）」。实跑表 `:238/:243`：τ=18 → LB1=4056（任意 φ precision≤29.1899%）、τ=50 → LB1=1638（precision≤50.6031%）。类限定 `:249`：「LB1 限定于『形状/序数/相邻游程摘要』特征类；对任意实值函数型谓词的信息论级断言见 U5」。设计件 `_dA_design.md:175-193`（定义+交叉核验）、诚实边界 `:200-204`（「对**任意实值函数型谓词**…`_dA_probe_out.txt:75-76` 显示 1µs 精确签名下 `LB1=0`、朴素 φ 的 `UB_naive=1`，故本件**不作**『任意谓词皆不可能』的信息论级断言，单列于 U5」）。缩减形式定义：`R2_BREAKPOINTS_CLOSURE.md:59`「LB1 自限…反例是 U5 的具体化，不是新领域」。

**成分③ 1621/1681（存活④，降格）** —— `_dA_out.txt:253`：

> 其中落在真实事件上的 e>50ms n=56；startTick=0 的真实事件 e 未验 n=4；合计 n=60/1681 无法给出 :177 严格合规证明，故 in50_strict <= 1621/1681 = 96.4307% 是**任何 (t,f) 前缀判据的上确界**。

（末句强读法已被 `_verify_A_out.txt:111-112` 推翻，见 §3.3。）缩减形式定义：`R2_BREAKPOINTS_CLOSURE.md:60`「1621/1681 只作『固定外部采样器下的离线可证计数』（`_verify_A_out.txt:111-112` 原话）」。

**缩减形式整体定义出处**：`R2_FINAL_GRADE.md:53` 末句「『不可兼得』仅以缩减形式存活（配额上界紧=组合恒等式、LB1 限定特征类、1621/1681 仅离线可证计数；`R2_BREAKPOINTS_CLOSURE.md:57-61`）」；`R2_BREAKPOINTS_CLOSURE.md:57`「剩余强度（未闭合、以缩减形式存活）」。

## 3 逐项可支撑度检验

检验方法：补证脚本 `_ar_check.py`（只读语料与既有件，独立重建，不 import 上游脚本）实跑产出 `_ar_out.txt`；复核脚本 `_verify_hy4_recompute.py` 不复用补证代码、从 104 个原始 (t,f) 文件再次全链路重建，产出 `_verify_hy4_out.txt`；两轮数字全等。以下数字本撰写会话重跑 `_ar_check.py` 再次输出确认。

### 3.1 成分① 配额上界紧性 —— 支撑成立（限定读法：组合恒等式 + 本语料紧性有见证；见证依赖 train=test）

- **语料独立重建**（`_ar_out.txt` S2；复核 F1/F2 独立一致）：files=104 / samples=1125992 / hz=[500] / runs=28381 / real aligned=1681；ideal_w={1:26, 3:73, 5:117}、ideal_t={1:12, 3:31, 5:47}（PASS True）；26 非空窗 c_w 分布 min=1 / med=70.0 / max=127，c_w>=5 共 22 窗。
- **上界紧（可达=紧）有实跑见证**：EXACT_LOOKUP（1µs 精确签名查表，train=test）实测 trig=1679 / real=1678 / false=1 / precision=0.999404 / in50_strict=1619，且恰好达 W={1:26, 3:73, 5:117} 与 T={1:12, 3:31, 5:47}（`_ar_out.txt` S4 PASS True；复核 F3 独立复现一致；与 `_verify_A_out.txt:119-120` 逐数一致）。即配额上界在**本语料**被一个实跑谓词恰好达到。
- **但既有判据无一达上界**：41 张表行（`_dA_out.txt:49-65` 的 15 档 + `_cost_quota_data.json` 的 26 档）中 W5 最大 66（D5-phase）与 102（C1-k50），无一 ≥117（`_ar_out.txt` S3；复核 F2 PASS「41 档无一达 117」）。
- **依赖登记**：上界等式本身是组合恒等式，不依赖任何标签（`R2_BREAKPOINTS_CLOSURE.md:58`）；依赖 oracle 标签的是**紧性见证**——EXACT_LOOKUP 查表集 `real_exact_sigs` 由同语料 `is_real` 标签构成（train=test，`_verify_A_recompute.py:720-722`；`_ar_out.txt:152` 自报；复核 F3 注：「紧性见证谓词的查表内容由同语料 is_real 标签构成——本复核据实登记」）。

### 3.2 成分② LB1 是否循环 —— 非循环（形式上），但仅类内可支撑

- **LB1 定义如 §2**：σ 为平移不变前缀特征签名，LB1 = max_R min_{s∈S_R} c(s)，限定「形状/序数/相邻游程摘要」特征类（`_dA_out.txt:227/:233/:249`）。
- **独立重算复现**（`_ar_out.txt` S6；复核 F5 独立一致）：τ=50 → n_cov=1678 / empty_real=3 / LB1=1638 / UB_naive=26617 / precision≤50.6031%；τ=18 → LB1=4056 / precision≤29.1899%——与 `_dA_out.txt:238-243` 全等（PASS True）。
- **循环论证判定：否。** 依据：特征类由 D1–D5 字母表（间隔序数桶 S/M/L/X/G 边界 0.05/0.5/2/5ms 等，`_dA_design.md:42-57`）事先划定；类外结果（1µs 精确签名 LB1=0、UB_naive=1）在 `_dA` 轮出件当时已作为 U5 自报（`_dA_out.txt:280` 引 `_dA_probe_out.txt:75-76`，该两行本次直读在案：τ=18/50 精确签名 LB1=0、UB_naive=1）；文件 mtime 时间线（probe 21:21:15 < out 21:21:39 < design 21:22:47 < verify 22:14:30/22:15:00）与文内证据方向一致——mtime 属文件系统弱证据，判定以 U5 文内自报在先为准（`R2_BREAKPOINTS_CLOSURE.md:59` 同判：「反例是 U5 的具体化，不是新领域」）。
- **限定**：类外（1µs 精确签名）LB1=0 → LB1 对反例所在谓词类**零约束力**，只支撑「类内强制误触发下界」，不支撑任意谓词不可兼得（`_ar_out.txt` S6 判读原文在案）。补充实测：粗签名（LB1 类）trip 留出（train 17 trips → test 17 trips，train real=1231 → test real=450）precision=2.7299%（test 触发 16496 = real 450 + falseB 16034，recall=100%）——类内即使用标签建表查表也不泛化（`_ar_out.txt:194`）。

### 3.3 成分③ 1621/1681 的性质 —— 支撑成立，但仅「固定外部采样器下的离线事后可证计数」

- **实算复现**（`_ar_out.txt` S5；复核 F4 独立一致）：real n=1681 中 e>50ms n=56（min=50.066 / med=88.112 / P90=205.739 / max=488.616 ms）、e 未验(startTick=0) n=4、e≤50ms n=1621；1621/1681 = 96.430696%（PASS (56,4,1621) True）。
- **e 的本质**：`e = (T[i] - T[i-1]) * 1000.0`（`_verify_A_recompute.py:154` 直读）= 外部 500Hz 采样器相邻采样间隔，观测装置产物（`_dA_design.md:96-101`：「`S_hat−S ∈ [0, e]`，`e = t[runStart]−t[runStart−1]`」）。离线用 S_hat−S∈[0,e] 区间夹逼（`S_OBSERVABILITY.md:47-59` 直读）只能证 w+e≤50ms → e>50 或 e 未验的 60 条**连离线核算都不可判定** → 离线可证计数 = 1681−60 = 1621。
- **在线硬界读法已死（既有登记，非本轮新判）**：`_verify_A_out.txt:111` 全件唯一 FAIL 原话「e hard bound is only an offline verifiability bound, NOT an online physical upper bound」；`:112`「offline verifiable=1621, conceptual online possible=1681」；`S_OBSERVABILITY.md:173-179` §5.3 标题即「S 不可精确观测不构成 :177 无法满足的证明」，其正文明确在线探针「完全不受外部 500Hz 采样工具历史掉拍的影响」。本件零真机，未做在线测量，1621 不被当作在线物理上界。
- **一致性核对**：EXACT_LOOKUP in50_strict=1619 ≤ 1621（S5 PASS True；1619/1681=96.3117%）；差值 2 条与查表谓词自身的空前缀不可达一致。

## 4 ★ oracle 依赖脱钩分析（方法与结果）

**问题设定**（`_ar_out.txt` S7 标题）：「不依赖（test 语料）oracle 标签的判据能否达到相近 precision」。反例工作点 = precision 0.999404 @ trig=1679（recall=1678/1681=99.82%）。**可脱钩判据** = 存在一个构造与触发决策均不读 `is_real` 标签的判据，在相近 recall 下达到相近 precision。四项检验（方法与结果均在 `_ar_out.txt` S7，复核 F6 独立复算全等）：

- **O1a 精确签名 leave-own-run-out**（查表内容仍需 oracle 标签建表，仅排除被测游程自身签名）：去自身后 real 触发 **0/1681**（recall=0.00%）、falseB 触发=1 → 反例 0.999404 纯属逐游程签名记忆，无跨游程泛化。
- **O1b 精确签名 trip 级留出**（trips=34 按 sorted 序号奇偶切 17/17，train real=1231 → test real=450）：test 侧触发仅 **1 次且是 falseB**，test-real recall=**0/450** → 换数据即失效。
- **O2 粗签名（LB1 特征类）trip 留出**：test 侧触发 16496（real=450 / falseB=16034），precision=**2.7299%** @ recall=100%——低于 test 侧基准率 25.0976%，类内标签建表查表也不泛化。
- **O3 无标签判据**（构造与触发决策不读 `is_real`；`is_real` 仅出现在事后计费元组——题给口径允许。复核静态检查：cal_abs / d4_burst / word_match_mmm 三函数体不含 `is_real`、不含 dfin，触发决策只读 (t,f) 前缀，`_ar_check.py:477-505` 直读）：C4-t40 precision=**27.9794%**@recall 100%、D4-burst **5.9336%**@100%、D1-word-MMM 100%@recall 0.42%（退化点）；matched recall≥99% 的无标签判据 precision≈6%（既有 4 方复算表 `_dA_out.txt:49-65`，如 D4-rising trig=27807 / hits=1679，直读在案）。
- **基准率复核**：τ=50 → A=5059 / real=1681 / br=**33.2279%**（S7 PASS；`_dA_out.txt:216` 同值）；差分反例算术 1681/(1681+3355×0.01)=**0.980432** 复核一致——但它是抽象算术、非语料谓词，不提供脱钩判据。

**结论：oracleDecouplable = no（本语料上不可脱钩，有界经验否定）。** 未找到任何不依赖 oracle 标签而达到相近 precision 的判据；反例谓词与成分①的紧性见证的 train=test 依赖是真实的、不可工程化的。限定（复核登记）：四项检验中 O1a/O1b/O2 仍由 oracle 标签建表（其作用是论证「高精见证依赖 oracle」，不是冒充脱钩证据），脱钩的实证支撑只落在 O3 抽测 3 档 + 既有 41 表行上——「no」是**本语料上未找到**的有界经验否定，非任意谓词级证明。唯一可设想的脱钩通道（用对局内部状态旗标区分 real/伪影）语料缺失（U4=`_dA_out.txt:279`、`RULING_D30.md:54` 直读），离线不可检验；对任意实值函数型谓词的信息论级断言未验（U5=`_dA_out.txt:280`）。

**依赖链分层（关键区分）**：三项成分自身的推导只需事后计费标签（题给口径允许），**不属** train=test；train=test 依赖属于反例谓词与成分①的**紧性见证**——即缩减形式的非平凡部分（紧性）建立在不可工程化前提上，而成分②③不依赖它。

**复核登记的三处真实缺陷（如实转录，均非材料性）**：
- (A) 内部数值不一致：`_ar_out.txt:205`（S8）写「C4-t40=27.87%@recall100%」，与同件 `:196`（S7）实测 27.9794% 不一致；27.8727% 实为 τ=40 基准率（`:183`，即 1681/6031）。**以 `:196` 的 27.9794% 为准**；两者均远低于 0.999404，不改变 §4 结论。
- (B) 措辞小过：补证回件任务3(d) 称 O3「构造与运行均不读 is_real」，而 `_ar_check.py:276` 的 `trigger_list` 确实读 `is_real`（仅事后计费元组，不参与触发决策）。准确表述应为「构造与触发决策不读、事后计费读（题给口径允许）」。
- (C) 「41 档」= 41 张表行（15+26），其中部分 CAL-* 行与 26 档内同规则重跑（两表 id 无字面交集、底层规则重叠）；「无一达 117」不受影响，且补证已透明写作「15+26」。

## 5 复核回件（SHA256 加字节数绑定）+ 三项支撑度汇总表

**复核 verdict = confirmed**（五项点名检查全部实跑通过，限「本语料/限定读法」范围）。verdict 非 refuted、非 partial，故按题面规则**不标 unconfirmed**。

**被核对象绑定**（复核回件原文；本撰写会话以 `python -I -X utf8` + hashlib 对下列每件重新实算，结果逐件一致）：

> 被核对象 SHA256 = 28cd3794a571d0ac8958b2fa98bc7906e61414f749111fc18f02de4294642a72，字节数 = 24614　　[lead/a_dim_reduced_20261108/_ar_out.txt]
> 同域产物 _ar_check.py = 6448574b92a151f43f637df5ef41f75e22515b13f5429eec1967ad00d725100c / 25748B
> 编排方六件指纹本会话 hashlib 全 MATCH

本撰写会话 hashlib 实算（命令：`python -I -X utf8 -c` 十一件 hashlib 循环）：

| 文件 | SHA256 | 字节数 | 对照 |
|---|---|---|---|
| lead/a_dim_reduced_20261108/_ar_out.txt | 28cd3794a571d0ac8958b2fa98bc7906e61414f749111fc18f02de4294642a72 | 24614 | 与复核回件 MATCH |
| lead/a_dim_reduced_20261108/_ar_check.py | 6448574b92a151f43f637df5ef41f75e22515b13f5429eec1967ad00d725100c | 25748 | 与复核回件 MATCH |
| lead/dtrigger_round2_20261107/_dA_out.txt | 8825e115f92bdf407cf20dde724e5633adc4e08e3f97bcee58299b95a8cb6d43 | 29813 | 与编排方指纹 MATCH |
| lead/dtrigger_round2_20261107/_dA_design.md | d5d487a7792da6ce89e143faa05727a4fe484cb66b400622c02511230770e0df | 20819 | 与编排方指纹 MATCH |
| lead/dtrigger_round2_20261107/_dA_probe_out.txt | 56a3e09bdd8453c3653aa480856e6358001a0bd4d54d751f7bf299e47cee6068 | 7976 | （补引件，无题给指纹） |
| lead/dtrigger_round2_20261107/_verify_A_out.txt | 145d4fa12e0e618f859c8f98305034d0ddb2952ae47b668e7a6a4c37290ca3b7 | 11204 | 与编排方指纹 MATCH |
| lead/dtrigger_round2_20261107/_verify_A_recompute.py | 5d906aa00069a4b9d484221db37368efe9cb83930cfeee85a4b0c5c53124fd4e | 36794 | 与编排方指纹 MATCH |
| lead/r2_final_grade_20261108/R2_FINAL_GRADE.md | 7ce09812f7bd905a95114a2cc2cea56b3dc3dbaef3d8e0d14c58685762ecab24 | 30140 | 与编排方指纹 MATCH |
| lead/criteria_r3_verify_20261108/R2_BREAKPOINTS_CLOSURE.md | bf426786db82c34dd6b6d21e3022678285e3e22f52dbdaa5085d85c3b6f8fbde | 22351 | 与编排方指纹 MATCH |

**确定性复现**：本撰写会话重跑 `python -I -X utf8 D:/Project/ra2-campaign-forge/lead/a_dim_reduced_20261108/_ar_check.py` → exit 0，重写后 `_ar_out.txt` SHA256 = 28cd3794…/24614 不变（输出件含 mtime 弱证据行，均指向 2026-11-07 的 `_dA` 系件，未受重跑影响）。

**复核要点（ranCommands=31，全 31 条均在复核会话执行；此处转录其回件）**：
1. 逐字抄录 = PASS：分文件块比对 57/49/2/5 行不一致=0（`_verify_hy4_out.txt:85-88`）；先做的跨文件粗比对曾报 56 处不一致，系把 design/grade/closure 引文对错源，已作废、未冒充全库结果。
2. 配额上界紧性 + 1621/1681 = PASS（限定读法）：不 import 被核脚本、从 104 个原始文件独立重建，ideal W/T、c_w 分布、EXACT_LOOKUP 五数、(56,4,1621) 全部复现（F1–F4）。
3. ★ oracle 脱钩 = PASS：静态源码检查（O3 三函数体不含 `is_real`/dfin，F6 :68-70）+ 独立复算（O1a/O1b/O2/O3 数字全等）；「no」判定可辩护。
4. 未代裁 = PASS：`_ar_out.txt:201` S8 标题「只报事实与依赖链状态，不代裁『是否立为新结论』」；文本扫描含「不代裁」=True、不含 necessaryCount/oracleDecouplable 字段（F8）。
5. necessaryCount / oracleDecouplable = PASS：未拔高、不乐观；「no」为保守否定答案。
真实缺陷 (A)/(B)/(C) 见 §4 末，均非材料性，不推翻三项支撑与脱钩结论。

**三项支撑度汇总表**（necessaryCount=3，oracleDecouplable=no）：

| 成分 | 内容（缩减形式） | 原文出处 | 本次实算（补证+复核双复现） | 支撑度 | 限定 / 依赖链状态 |
|---|---|---|---|---|---|
| ① | 配额上界 captured ≤ Σmin(N,c_w) = 26/73/117（W 口径；T=12/31/47） | `_dA_out.txt:191-201`、`R2_BREAKPOINTS_CLOSURE.md:58` | ideal 复现；EXACT_LOOKUP 恰达 W 与 T 理想值（紧性见证）；41 表行无一达 117 | 支撑成立 | 等式=组合恒等式（标签无关）；紧性见证依赖 train=test 查表（oracle 标签，不可工程化） |
| ② | LB1 类内强制误触发下界：τ=50 → 1638、τ=18 → 4056（precision≤50.6031%/29.1899%） | `_dA_out.txt:226-249`、`_dA_design.md:175-204`、`_dA_probe_out.txt:75-76` | 两 τ LB1 与 UB_naive 全等复现；类内留出 precision=2.7299% | 支撑成立（仅类内） | 非循环（类限定先于反例自报，U5 在先；mtime 为弱证据）；类外（1µs 精确签名）LB1=0，对反例谓词类零约束 |
| ③ | 1621/1681 = 96.430696%（56+4=60 条不可判定） | `_dA_out.txt:251-257`、`R2_BREAKPOINTS_CLOSURE.md:60`、`_verify_A_out.txt:111-112` | (56,4,1621) 复现；1619 ≤ 1621 核对 | 支撑成立 | 仅「固定外部 500Hz 采样器下的离线事后可证计数」；在线硬界读法已被既有登记推翻（:111 唯一 FAIL）；零真机未做在线测量 |

## 6 结论

- **supportCount = 3**：三项成分各自在其**限定读法**下经本次实跑支撑——①配额上界成立且紧性有实跑见证（见证依赖 train=test）；②LB1 类内成立且形式上非循环（仅类内，类外 LB1=0）；③1621/1681 离线可证计数成立（非在线硬界）。这是「限定读法下被支撑」，不是无条件的必要性证明。
- **oracleDecouplable = no**：按 §4 判据，本语料上未找到任何不依赖 oracle 标签而达到相近 precision 的判据。该「no」是有界经验否定（覆盖查表/无标签规则族在语料上的实证），不构成「任意谓词皆不可脱钩」的命题（U5 未验）。
- **依赖链状态**：
  - 已闭合段：强形式「任意前缀谓词」措辞死亡（`R2_BREAKPOINTS_CLOSURE.md:55`）；三项成分的数值层全部双轮独立复现并经本次重跑第三次确认。
  - 未验段（不并入结论，状态不被本件改变）：物理 S / 实际 C / Q5 四项工程依赖未验（`RULING_D30.md:22/:78` 直读：「工程耗时、扰动、实际捕获覆盖、真实修复、物理S及实际C均未验」）——零真机下离线不可闭合；U4 内部对局状态旗标语料缺失、离线不可检（`RULING_D30.md:54`）；U5 任意实值函数型谓词的信息论级断言未验（`_ar_out.txt:280` 转引）；U1–U8 其余未验项照 `_dA_out.txt:275-283` 登记；mtime 时间线为文件系统弱证据，判定以 U5 文内自报在先为准。
- **是否具备立为新结论的材料条件（只陈事实，不裁）**：材料侧——三项成分有独立实跑支撑、复核 verdict=confirmed、缺陷 (A)/(B)/(C) 均非材料性；缺口侧——紧性见证依赖不可工程化的 train=test 查表、oracle 在本语料不可脱钩、工程四依赖未验。既有登记（`R2_FINAL_GRADE.md:58`）已明示：若要把缩减形式立为新结论走升格，需「形式化缩减命题、界定适用域、处置 oracle/工程可行性未验项」，且属判据采纳动作。
- **不代裁声明**：本件及同轮 `_ar_out.txt` S8 均只报事实与依赖链状态；「缩减形式是否立为新结论」不由本件裁定，留给用户。
- **未验项汇总**：同上「未验段」；另本件零真机，任何在线/物理层读法（在线物理上界、在线捕获能力）均未验，不得由本件数字外推。
