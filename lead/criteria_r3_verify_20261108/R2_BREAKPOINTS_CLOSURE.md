# R2 崩点闭合报告 —— CRITERIA_ROUND2.md 四维崩点（r3 查证回件 + hy4 复核回件综合）

撰写者：闭合报告撰写员（r3 轮第三棒）。日期 2026-11-08。
总被核对象 = `lead/dtrigger_round2_20261107/CRITERIA_ROUND2.md`，SHA256 = bcd7c8e53f6987a899f78fd1bd8ae90247193f1897aadf15cc58daa45211982a，字节数 = 49968（本报告 hashlib 实算，与编排方指纹及查证回件 `_r3_CLOSURE_VERIFY_20261108.md:3` 自报一致）。
本件综合两份既有回件：r3 查证回件 `_r3_CLOSURE_VERIFY_20261108.md`（崩点查证员·GLM，verdict 详见 §5）与 hy4 复核回件（verdict = confirmed，ranCommands = 32，回件 JSON 转引），并把其中关键证据在本轮重新实算/直读。证据分三层标注：(i) 本报告本轮实算；(ii) 本轮直读既有落盘件（文件:行）；(iii) 回件自述（转引，凡本轮追不到的标「未验」）。

## 1 目的与边界（只查证崩点、不选判据）

- **目的**：只查证 CRITERIA_ROUND2.md 登记的维度 A / 维度 B / 维度 C / 维度 D 四维崩点能否闭合，逐维如实写闭合状态；不选判据、不排序、不给工程建议。
- **边界（铁律）**：不选判据、不改口径 B、不改 STALL_EVENT_DEFINITION.md:177/:190/:191（该件登记于 `lead/stall_event_def_20261106/STALL_EVENT_DEFINITION.md`，经 `_dB_anchor_recompute_out.txt:12` 直读）、不改台账（`lead/GOAL_THREE_TARGETS_20261018.md`、`lead/PENDING_DECISIONS.md`）；不 commit、不 push；零真机、零采样代码；唯一写域 = `lead/criteria_r3_verify_20261108/`。
- **本轮实跑清单**：有效 Bash 实算 4 轮（`python -I -X utf8` + 绝对路径 + hashlib）——①22 件指纹批算；②`CRITERIA_METRICS.json` 定位+指纹；③数据件结构探查+写域 mtime 盘点；④维度 B 12 格与维度 C 156 行独立复算；另有 1 轮全库 os.walk 超时无输出、不计。文件直读 17 次（含 `_dA_out.txt` 三段、查证回件与复核输出全文）。
- **写域开局盘点（本轮实列，共 6 件）**：`_r3_CLOSURE_VERIFY_20261108.md`(13597, mtime 12:46:41)、`_r3_fp_out.txt`(1357, 12:45:47)、`_r3_data_recheck_out.txt`(668, 12:43:48)、`_r3_b12_recheck_out.txt`(1336, 12:44:19)、`_r3_metrics_cross_out.txt`(550, 12:44:46)、`_verify_hy4_out.txt`(26210, 13:01:35)。本报告新增第 7 件 = 本文件；未改任何只读域文件（`_dC_cells.txt` mtime 仍为 2026-11-07T20:35:23，本轮实读）。
- **指纹表（本报告 hashlib 实算，格式 SHA256/字节）**：

| 文件（lead/ 下） | SHA256 | 字节 |
|:--|:--|--:|
| dtrigger_round2_20261107/CRITERIA_ROUND2.md | bcd7c8e53f6987a899f78fd1bd8ae90247193f1897aadf15cc58daa45211982a | 49968 |
| dtrigger_compare_20261107/CRITERIA_COMPARE.md | 4a3424050125b98c0dd3a9a76ec6603fc03ad976e0b9fdecfb34d3b683b94726 | 48343 |
| dtrigger_compare_20261107/CRITERIA_METRICS.json | 7e2533eabf795e8aa0063a16ee875d95742880dcefab55d596cfc5aa6e7f958b | 17926 |
| dtrigger_round2_20261107/_verify_A_out.txt | 145d4fa12e0e618f859c8f98305034d0ddb2952ae47b668e7a6a4c37290ca3b7 | 11204 |
| dtrigger_round2_20261107/_verify_A_recompute.py | 5d906aa00069a4b9d484221db37368efe9cb83930cfeee85a4b0c5c53124fd4e | 36794 |
| dtrigger_round2_20261107/_dA_out.txt | 8825e115f92bdf407cf20dde724e5633adc4e08e3f97bcee58299b95a8cb6d43 | 29813 |
| dtrigger_round2_20261107/_dA_design.md | d5d487a7792da6ce89e143faa05727a4fe484cb66b400622c02511230770e0df | 20819 |
| dtrigger_round2_20261107/_verify_B_out.txt | 4ee6a6b78d80a336c3431a6f71d9f5a77fec93ef65b7a4c642a49b669368c107 | 7229 |
| dtrigger_round2_20261107/_dB_anchor_recompute_out.txt | 3e9588ce1def2ebc5b9ad77a3ce242b47bcada4ae1ab1bc4ea606775edd40807 | 14479 |
| dtrigger_round2_20261107/_dB_anchor_recompute_data.json | 8fb149f21e9b41d7c808e8f8c2e1cb35ca62b881ebe65bfba7029b6f95763794 | 42910 |
| dtrigger_round2_20261107/_dB_anchor_recompute.py | 44b10371cdc258e7db5c232f53d9d64dfdf4f34cb084115d0bb8c7a05a5a382b | 27324 |
| dtrigger_round2_20261107/_dC_out.txt | a0deb34a4aed83efe3d0b80dfff4f05eb28eeec5fac5613ff49316fd8081337a | 13473 |
| dtrigger_round2_20261107/_dC_cells.txt | 8e05b65e8d4bface4e80b5df5bc246a41ea1800c808bf5b69b4a7587c747e6f1 | 25324 |
| dtrigger_round2_20261107/_verify_D_out3.txt | 0e5e84331b2126bd487b526c71095f432303974cdc3960b28794c32807bef84a | 3352 |
| dtrigger_round2_20261107/_dD_check.py | f2f3c561ded7b209f9206891e688642913ae15410fd2abbe8b075a0165f91907 | 7909 |
| dtrigger_round2_20261107/_dD_check_out.txt | 7cdfcf9efb76ddffec3a8ea68a536b28f0099d2d571fc18c64d52cf0a8c9491b | 5117 |
| dtrigger_round2_20261107/_dD_PHYSICAL_S_ALIGNMENT.md | bb61eedbddea61e9ffcb1ac8981dadd8b3ee0fb12c715ccb3e600ca78c50fac1 | 18262 |
| criteria_r3_verify_20261108/_r3_CLOSURE_VERIFY_20261108.md | 80c472acf6a902fcf29c628e305aa57ba96df9d3cdc9dcd2f312378ba15200e9 | 13597 |
| criteria_r3_verify_20261108/_r3_fp_out.txt | 4e70dd45dddb251f84d1bcad5f83cd3c05ad43b99132e6e7d44bb7456e6edf5b | 1357 |
| criteria_r3_verify_20261108/_r3_data_recheck_out.txt | afe6626962a06939baa1edeabc16afae24a8cbcfa69f53acfaf6065d08cabe89 | 668 |
| criteria_r3_verify_20261108/_r3_b12_recheck_out.txt | 9f4fc77ff7ea0421dc9d498a701b72c679e72d48888c233e5db1dba39c787aca | 1336 |
| criteria_r3_verify_20261108/_r3_metrics_cross_out.txt | 7ffb848ec242042bded2355689cbd6bea026657c478bc3c9673b0662d1554960 | 550 |
| criteria_r3_verify_20261108/_verify_hy4_out.txt | f38adf5971942692d31ad4760589409e51c3f6cd3d0d7a95407c02fdd32cd675 | 26210 |

- **未重跑声明**：本报告未重跑任何调查/复核脚本（`_dA_run.py`、`_verify_A_recompute.py`、`_dB_anchor_recompute.py`、`_dC_recompute.py`、`_dD_check.py` 等会覆写只读件）；上述件在指纹表中冻结在案。

## 2 维度 A 崩点查证（三行反证 + 不可兼得结论的剩余强度）

本维输出件 = `_verify_A_out.txt`（指纹见表，本报告实算 = 编排方指纹）。查证回件 §1 判「部分闭合」；本轮逐条追证如下。

**三行反证属实（本轮直读 `_verify_A_out.txt:110-121`）**：
- `:110` 登记 `UNIVERSAL_WORDING_CANDIDATES` 三处通用措辞，指向 `_dA_out.txt:191`（「谓词无关的配额硬上界 —— …对任何 (t,f) 前缀判据一律成立」）、`:206`（「P(该次为真实 | 在 τ 处触发) <= A_real(τ)/A(τ)（对读 (t,f) 前缀的任意谓词皆成立）」）、`:253`（「in50_strict <= 1621/1681 = 96.4307% 是**任何 (t,f) 前缀判据的上确界**」）——三行原文均经本轮直读 `_dA_out.txt:191/:206/:253` 核实存在。
- `:119` `trig=1679 real=1678 false=1 precision=0.999404 (bound=0.332279)` 五数逐位一致；bound 母体即 `_dA_out.txt:216`（τ=50：A(τ)=5059、A_real=1681、base_rate 上界=33.2279%，本轮直读）。
- `:120` `EXACT_LOOKUP in50_strict=1619/1681 W1/W3/W5={1: 26, 3: 73, 5: 117} (still not an engineering feasibility claim: physical S/C/Q5 unverified)`；`:121` 差分反例 `precision=0.980432 > max_base_rate=0.332279`。
- 全件结论 `:124` = `SUMMARY PASS=54 FAIL=1`，唯一 FAIL 即 `:111`（「e hard bound is only an offline verifiability bound, NOT an online physical upper bound」）；`:112` 给出 offline verifiable=1621 vs conceptual online possible=1681。

**反例性质（本轮直读 `_verify_A_recompute.py:707-745`）**：查表谓词的集合 `real_exact_sigs` 由**同语料** `r["is_real"]==True` 事件签名构成（`:720-722`，train=test、需 oracle 标签）；脚本自注「still not an engineering feasibility claim」（`:733-734`）；差分反例非语料实跑，是抽象算术混合 1681/(1681+3355×0.01)（`:740-745`）。算术值经复核输出 `_verify_hy4_out.txt:114-118` 独立复算一致（0.999404 / 0.980432 / 1619/1681=0.963117，直读）。

**已闭合项（通用措辞死亡）**：`_dA_out.txt:206-207`「任意前缀谓词 precision ≤ max 基准率」被 `:119` 实跑反例与 `:121` 逻辑反例直接推翻；`:253`「任何 (t,f) 前缀判据的上确界」的在线/物理强读法被 `_verify_A_out.txt:111-112` 推翻。此崩点**闭合**。

**剩余强度（未闭合、以缩减形式存活）**：
- 存活①：配额上界 captured ≤ Σmin(N,c_w)（`_dA_out.txt:191-201`，本轮直读）是组合恒等式；反例恰好**达到** W={26,73,117} 理想值、未违反——上界成立且被证实紧，但它证的是**配额政策封顶**，不是谓词不可能性。
- 存活③：LB1 自限「形状/序数/相邻游程摘要」特征类（`_dA_out.txt:249` 直读；U5 `:280` 直读在先，1µs 精确签名 LB1=0 本为调查件登记内容）——反例是 U5 的具体化，不是新领域。
- 存活④（降格）：1621/1681 只作「固定外部采样器下的离线可证计数」（`_verify_A_out.txt:111-112` 原话）。
- 存活（狭义）：「不是调参能绕过」限 11+4 档粗特征类及其调参空间（反例是新谓词类，非 D1–D5 调参）。

**未验项**：反例的工程可行性未验（查表依赖 oracle 标签、物理 S/C/Q5 未验——`:120` 括注、`_verify_A_recompute.py:733-734`）。

**维度 A 判定**：部分闭合——崩点为真（复核指控属实），通用措辞死亡已闭合；「不可兼得」仅以缩减形式成立。**不可升格。**

## 3 维度 B/C 崩点查证（指纹归属、156 格不变式）

### 维度 B

- **指纹归属（本轮实算）**：`4a342405…/48343` 确属 `lead/dtrigger_compare_20261107/CRITERIA_COMPARE.md`；`_dB_anchor_recompute_out.txt` 实算为 `3e9588ce…/14479`，二者不同——「指错对象」在指纹层面属实。
- **但（本轮直读 `_dB_anchor_recompute_out.txt:18-19`）**：该件自标「被核对象 SHA256 = 4a342405…，字节数 = 48343（被核对象 = lead/dtrigger_compare_20261107/CRITERIA_COMPARE.md §3.2；铁律 9 指纹行）」——指纹与其自述对象内部自洽；「指错」属证据链引用瑕疵，不在数值计算路径上。`_verify_B_out.txt:61-63`（直读）同判。**此崩点（崩点 1）闭合。**
- **12 格数值不受影响（本报告独立复算，第 4 层对账）**：从 `_dB_anchor_recompute_data.json`（指纹见表）每档 `waits` 原始数组、e = e_med_full = 2.510999998776242，重算 (nTrig, >=100, +e>50, min/med/max, realHits) 六档——与主表 `_dB_anchor_recompute_out.txt:50-55`（直读：(29,5,29,66.334,70.931,321.002,8)…(15,15,15,377.385,385.601,387.990,0)）逐值全等、与各 cell 自带字段全等、与上游 `CRITERIA_METRICS.json`（`lead/dtrigger_compare_20261107/`，指纹见表）triggers/realHits 全等，**B_ALL_OK = True**（本轮实跑输出）。此前三层：查证回件 `_r3_b12_recheck_out.txt`（直读 ALL_OK=True）、上游交叉 `_r3_metrics_cross_out.txt`（直读 ALL_MATCH=True）、复核 hy4 独立重算（`_verify_hy4_out.txt:53-67` 直读，首轮 8 字段解析误致 match_main=False、纠正为 9 字段后 B_ALL_OK_CORRECTED=True——复核员当场记录己方解析错误，非数据缺陷）。e=2.510999999ms(n=28317) 与 `_dB_anchor_recompute_out.txt:27` 直读一致。
- **未核未闭合（崩点 2-6）**：崩点 2 evidence 指纹串损坏——`_verify_B_out.txt:64-66`（直读）示回件自称脚本 hash 尾 `26f3fb61829756dfeecf` 未出现在实算件、out.txt 尾 `b6f95763794` 实为 data.json 的尾串；崩点 3 自检硬编码（`_dB_anchor_recompute.py:401-413`）——该行段本报告未直读，**未验**（脚本整体指纹 44b10371…/27324 在案）；崩点 4 `+e>50` 六格空列零判别力；崩点 5 「统一锚」是选择非推导（runStart 敏感性 C2-abs-P95x2 → 27/4/27，`_verify_B_out.txt:48` 直读）；崩点 6 og=None 答非所问（调查件自辩见 `_dB_anchor_recompute_out.txt:31-39` 直读：og=None 游程整体结构性不触发，12 格仍可补算——该崩点本身未核）。以上四项查证回件 §2 与复核回件均记「未核、未见闭合证据」。
- **维度 B 判定**：部分闭合（崩点 1 闭合；12 格数值多层对账成立；崩点 2-6 未核未闭合）。**不可升格。**

### 维度 C

- **读数层（本轮直读 `_dC_out.txt:28-46`）**：`:28` 格数=156（26 判据 × 6 情景）；`:29` 分解式不成立的格 = 0/156 PASS；`:30` 非负违例 = 0/156 PASS；`:31` 链式违例 = 0/156 PASS；`:36` `A + B = 54 + 102 = 156`（PASS）；`:41` `noFalse == 理想 = 54 / 54` PASS。
- **数据层（本报告独立复算，第 3 层）**：解析 `_dC_cells.txt`（指纹见表）全部 **156 数据行** → 分解式违例 0、列间不一致 0、非负违例 0、链式违例 0；A=54 / B=102 / 未归类 0 / A+B=156；A 族 noFalse==ideal **54/54**；附带 B 族 noFalse−captured==0 = **71/102**、capUpper==ideal = **73/102**、交集 71、captured==ideal = **0**——与 `_dC_out.txt` 读数及 CRITERIA_ROUND2.md §4 所引全部一致（本轮实跑输出）。此前两层：查证回件 `_r3_data_recheck_out.txt`（直读，同值）、复核 hy4（`_verify_hy4_out.txt:30-36` 直读，同值）。
- **未核未闭合（证据链层）**：`_dC_recompute.py:356-368` emit 常量串、all_pass 门不含子断言（崩点 1），§9.7「高档 ≥100ms」13 档仅 4 档全部≥100（崩点 2）——该脚本本报告未直读，**未验**；查证回件 §3 与复核回件同记「未核」。
- **维度 C 判定**：部分闭合——本 ask 三条主张（0/156 违例、A+B=156、54/54）读数层+数据层双验成立、已闭合；证据链崩点未核未闭合。**不可升格。**

## 4 维度 D 崩点查证（观测锚下界强度）

本维输出件 = `_verify_D_out3.txt`（指纹见表，本报告实算）。调查件 = `_dD_PHYSICAL_S_ALIGNMENT.md`（指纹见表）。

- **T3 属实（本轮直读 `_verify_D_out3.txt:7-10`）**：`B4 block lines 128-137 … computed=0 literal_prose=10`；`B3 block lines 114-125: computed=0 literal_prose=12`。
- **源码级确认（本轮直读 `_dD_check.py:114-125/:128-137`）**：B3 块恰 12 个 `out()`、B4 块恰 10 个 `out()`，全部字面串、无插值；`:117`「本轮实跑 e>0 计数=28317/28317」、`:119`「本轮实跑 U>50ms 真实事件=56 条」均为硬编码文字（数字在 B1 块另有实算：`_dD_check_out.txt:14` 直读 `U > 50.000 ms : n= 56`；B1 门限表 `:9-20` 直读完整）。复核 hy4 源码级统计同值（`_verify_hy4_out.txt:48-52` 直读，含 `:117/:119` 硬编码判定 True）。**T3 主张在源头成立。**
- **「独立证成」强度主张崩塌（此崩点闭合）**：调查件 `:114`（直读）「一句话裁决」把「已证明不合规 = 由下界越线独立证成」与「观测锚下界不足以证明合规（证据不足，未验）」并置，`:92`（直读）明写 D-2 证成路径「不依赖物理 S」。但 B3/B4 零计算、纯文字；「反向不等式 (iii)」（`_dD_check.py:120-122`、`_dD_check_out.txt:39-41` 直读）只是平凡逻辑蕴涵（C−S ≥ C−S_hat > 50 ⟹ C−S > 50），其前提（观测锚下已 >50ms 的触发数）依赖**其它文件**的既有实跑读回（自引 `_dtrigger_supplement_out.txt:11-24,29`），非 D 自己的确定性计算。故「独立证成、不依赖 S」的强度主张被证实为高估——**崩塌成立**。
- **仍站立（弱化形式）**：调查件 `:88`（直读）「这是『观测锚下界不足以证明合规』，即**证据不足 / 未闭合（未验）**……不是『已证明合规』，也**不是**『已证明不合规』，更不是『物理上不可满足』」；`:104`（直读）「缺失 S **不构成**『已证明不合规』的充分条件」；`:108-110`（直读）为 D-3 边界条款（硬阻断只落肯定性合规确证、不落否定性结论）。复核未反证该弱化表述——硬阻断以「证据不足、未验」形式站立。
- **新发现·引文行号错置（复核 hy4 发现，本轮核实）**：查证回件 `:67` 称「调查件自身 `:108-110` 原文即『证据不足，未验，不是已证明不合规』」；本轮直读 `_dD_PHYSICAL_S_ALIGNMENT.md:108-110` 实为 D-3 边界条款，不含这三串字样；「证据不足」实位于 `:88/:114`、「不是已证明不合规」实位于 `:88/:104`（复核输出 `_verify_hy4_out.txt:251-254` 程序化核对同判，直读）。属引文行号错置与拼接，非伪造；不改变维度 D 判定，**待修正**（本报告不改被核对象文件）。
- **描述统计支撑**：T1 独立重算 d_final>=100 runs=1704 / real=1681 / non-real=23（`_verify_D_out3.txt:1-3` 直读）；B1 门限表 U>50=56（`_dD_check_out.txt:9-20` 直读）。上游 `CRITERIA_COMPARE.md:34-35,145-147`「不合规方向」记载——本轮经复核输出摘录段读回（`_verify_hy4_out.txt:200-206`），CRITERIA_COMPARE.md 本体未直读，**转引**。
- **维度 D 判定**：部分闭合——「独立证成」强度主张崩塌已证（该崩点闭合）；硬阻断只剩「文字论证 + 上游记载 + 观测锚侧描述统计」的弱化形式，解除条件（补 S 与 C）**未验**。**不可升格。**

## 5 复核回件（含 SHA256 加字节数绑定）加四维闭合状态汇总表

- **复核回件（hy4）**：verdict = **confirmed**（按规则如实记录；非 refuted/partial，故不标 unconfirmed）；ranCommands = 32（回件 JSON 转引）；其自述两次 Write 核验脚本被安全钩子拦截未落盘、改内联实跑（转引，未验）。
- **被核对象绑定（本报告 hashlib 实算）**：**被核对象 SHA256 = 80c472acf6a902fcf29c628e305aa57ba96df9d3cdc9dcd2f312378ba15200e9，字节数 = 13597**（`lead/criteria_r3_verify_20261108/_r3_CLOSURE_VERIFY_20261108.md`）——与复核回件自报绑定及复核输出件第 1 行（`_verify_hy4_out.txt:1` 直读 `rv 80c472ac… 13597`）逐位一致。编排方 5 项指纹（round2/compare/vA/dA/dBout）本报告实算全部 match。
- **如实记录的差异**：复核回件自报其输出落盘件 = `0614af13…/18694`，但本报告实算现盘值 = **`f38adf59…/26210`**（mtime 2026-11-08T13:01:35.255708，本轮实读；查证回件落盘 12:46:41 在前）。即该文件在回件自报状态之后被追加（现 :114-255 为追加的更深核对段：A 算术独立复算、`_verify_A_recompute.py:707-745` 摘录、D 源 :103-115 摘录、:67 引文核对段等）；追加段内容与本报告本轮直读互证、与回件判定同向且补强行号错置证据；**追加行为主体/时点未验**。被核对象绑定不受影响（被核对象指纹与本报告实算一致）。
- **四维闭合状态汇总表**：

| 维 | 查证回件判定 | 已闭合（崩点层） | 未闭合 / 未验（残留） | 升格判定 |
|:--|:--|:--|:--|:--|
| 维度 A | 部分闭合 | 三处通用措辞死亡：`_dA_out.txt:206-207` 任意谓词精度上界、`:253` 在线/物理上确界被 `_verify_A_out.txt:119/:121/:111-112` 反证推翻 | 「不可兼得」只剩缩减形式；反例工程可行性未验（oracle 标签查表） | 不可升格 |
| 维度 B | 部分闭合（崩点 1 闭合） | 指错对象属实但指纹与 `:18-19` 自标对象自洽；12 格数值经本报告第 4 层复算 B_ALL_OK=True | 崩点 2-6 未核未闭合（指纹串损坏 / 自检硬编码未直读 / `+e>50` 空列 / 「统一锚」选择 / og=None） | 不可升格 |
| 维度 C | 部分闭合（本三条闭合） | `:29/:30/:31` 三类违例 0/156、`:36` A+B=156、`:41` 54/54——读数层直读 + 数据层本报告独立复算全等 | 证据链崩点未核：emit 常量串（未直读）、§9.7「高档 ≥100ms」 | 不可升格 |
| 维度 D | 部分闭合 | 「独立证成」强度主张崩塌（B3/B4 零计算纯文字，源码级确认）；:67 引文行号错置已证 | 「独立证成」本身未闭合；硬阻断只剩「证据不足、未验」弱化形式；解除条件未验 | 不可升格 |

**promotable = 0。**

## 6 结论（promotable 维度数、可升格与不可升格、未验项、不选判据声明）

- **promotable 维度数 = 0**：维度 A / 维度 B / 维度 C / 维度 D 四维均为**部分闭合**，无一维满足「崩点全部闭合且不依赖未验前提」，故无一维可升格；**可升格维度：无**。
- **不可升格原因（逐维）**：A 通用命题死亡后只剩缩减形式 + 反例工程可行性未验；B 崩点 2-6 未核未闭合且「统一锚」是选择非推导；C 证据链崩点（emit 常量串、§9.7）未核未闭合；D 「独立证成」未闭合，硬阻断只剩文字论证 + 上游记载 + 描述统计。
- **未验项清单（如实登记，不补造）**：
  1. 维度 A 反例的工程可行性（查表依赖 oracle 标签 / train=test；物理 S/C/Q5 未验）。
  2. 维度 B 崩点 2-6：evidence 指纹串损坏已见尾串证据（`_verify_B_out.txt:64-66`）但成因未核；自检硬编码 `_dB_anchor_recompute.py:401-413` 本报告未直读；`+e>50` 空列、「统一锚」选择、og=None 未核。
  3. 维度 C 证据链崩点：`_dC_recompute.py:356-368` emit 常量串、§9.7「高档 ≥100ms」越界，未核。
  4. 维度 D：「独立证成」的独立计算前提未闭合；硬阻断解除条件（同时补 S 与 C）未验；`CRITERIA_COMPARE.md` 本体未直读（:34-35/:145-147 为转引）。
  5. `_verify_hy4_out.txt` 现盘 26210 字节 ≠ 复核回件自报 18694 字节——追加行为主体/时点未验（追加内容与判定同向，绑定不受影响）。
  6. 本报告未重跑任何调查/复核脚本（只读铁律，见 §1 未重跑声明）；查证/复核回件的「实跑」以回件自述 + 落盘件直读为据，数值核心经多层独立对账与本报告复算核实。
- **复核 verdict 如实记录**：confirmed（非 refuted/partial，不标 unconfirmed）。复核发现的唯一实质缺陷 = 查证回件 :67 的维度 D 引文行号错置（实际弱化表述在 `:88/:104/:114`，误标 `:108-110`），已在 §4 如实登记，待修正；不改变任何维度判定。
- **不选判据声明**：本件只查证崩点能否闭合，**不选判据、不改口径 B、不改 STALL_EVENT_DEFINITION.md:177/:190/:191、不改台账**；不 commit、不 push；零真机、零采样代码。全部判定仅回答「崩点闭合 / 未闭合、能否升格」，不对任何候选判据作取舍、排序或工程建议。
