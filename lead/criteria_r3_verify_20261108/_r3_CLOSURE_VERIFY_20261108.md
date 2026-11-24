# _r3_ 四维崩点闭合查证（离线只读 · 零真机 · 零采样代码）

撰写者：崩点查证员·GLM（r3 轮）。被核对象 = `lead/dtrigger_round2_20261107/CRITERIA_ROUND2.md`（SHA256 = bcd7c8e53f6987a899f78fd1bd8ae90247193f1897aadf15cc58daa45211982a，字节数 = 49968）登记的 A/B/C/D 四维崩点。
本件只查证崩点能否闭合，不选判据、不改口径 B、不改 `STALL_EVENT_DEFINITION.md:177/:190/:191`、不改台账；不 commit、不 push。唯一写域 = `lead/criteria_r3_verify_20261108/`。

## 0 实跑命令（本轮全部 Bash/Python 命令，`python -I -X utf8` + 绝对路径 + hashlib）

1. `mkdir -p …/lead/criteria_r3_verify_20261108 && ls -la` 两调查目录（列件）。
2. 指纹批一（9 件，落 `_r3_fp_out.txt`）：CRITERIA_ROUND2.md / CRITERIA_COMPARE.md / _verify_A_out.txt / _dA_out.txt / _dB_anchor_recompute_out.txt / _dC_out.txt / _dC_cells.txt / _verify_D_out3.txt / _dD_PHYSICAL_S_ALIGNMENT.md。
3. 数据级复算批一（落 `_r3_data_recheck_out.txt`）：解析 `_dC_cells.txt` 全部 156 行重算分解式/非负/链式/A+B/54/71/73/0；peek `_dB_anchor_recompute_data.json` 顶层键。
4. peek `cells` 键结构。
5. 数据级复算批二（落 `_r3_b12_recheck_out.txt`）：从 `waits` 原始数组全量重算 12 格并与主表比对。
6. metrics 交叉批一（realHits 对上；nTrig 键名不符，未断言，覆写至批二前作废）。
7. peek `CRITERIA_METRICS.json` 条目键名（发现 `triggers`）。
8. metrics 交叉批二（落 `_r3_metrics_cross_out.txt`，`triggers`/`realHits` 六档 ALL_MATCH=True）。
9. 指纹批二（追加至 `_r3_fp_out.txt`）：_verify_A_recompute.py / _dB_anchor_recompute_data.json / _dD_check.py / CRITERIA_METRICS.json / _dA_design.md。

未重跑任何调查/复核脚本（`_dA_run.py`、`_verify_*` 等会覆写既有件）；本ask要求的核对全部以实读+实算完成，无「以快代慢」替代。

## 1 维 A —— 部分闭合

被核对象 SHA256 = 145d4fa12e0e618f859c8f98305034d0ddb2952ae47b668e7a6a4c37290ca3b7，字节数 = 11204（`_verify_A_out.txt`，本轮实算）

**三行实读（全部真实存在、数值与 ask 所述一致）**：
- `:110` `UNIVERSAL_WORDING_CANDIDATES=["191:【形式化证据 ①：谓词无关的配额硬上界 —— 捕获维度对任何 (t,f) 前缀判据一律成立】", "206:P(该次为真实 | 在 τ 处触发) <= A_real(τ)/A(τ)（对读 (t,f) 前缀的任意谓词皆成立）。", "253:…故 in50_strict <= 1621/1681 = 96.4307% 是**任何 (t,f) 前缀判据的上确界**。"]` ✓
- `:119` `PASS exact-signature lookup predicate refutes universal 33.2279% precision bound :: trig=1679 real=1678 false=1 precision=0.999404 (bound=0.332279)` ✓（trig/real/false/precision/bound 五个数逐位一致）
- `:120` `EXACT_LOOKUP in50_strict=1619/1681 W1/W3/W5={1: 26, 3: 73, 5: 117} (still not an engineering feasibility claim: physical S/C/Q5 unverified)`；`:121` `PASS counterexample: differential firing beats max single-τ base-rate bound :: precision=0.980432 > max_base_rate=0.332279` ✓

**反例性质（实读 `_verify_A_recompute.py` SHA256 = 5d906aa00069a4b9d484221db37368efe9cb83930cfeee85a4b0c5c53124fd4e，字节数 = 36794，`:707-745`）**：`exact_lookup_trigger` 只读游程 ≤50ms 的 (t,f) 前缀签名、确定性、每游程至多一触，但查表集合 `real_exact_sigs` 由**同语料** `r["is_real"]==True` 事件的签名构成（`:720-722`，训练=测试、需 oracle 标签）；脚本自注「仍非工程可行性主张」（`:734`）。`:121` 差分反例不是语料实跑谓词，是抽象算术混合：real 触发率 1.0、false 触发率 0.01 → 1681/(1681+3355×0.01)=0.980432（`:740-745`）。

**「不可兼得」剔除该措辞后的残存量**：
- **死亡**：`_dA_out.txt:206-207`「任意前缀谓词 precision ≤ max 基准率」被 :119（实跑反例）与 :121（逻辑反例）直接推翻；`:253` 的强读法（1621/1681 是**在线/物理**普遍上界）被 :111-112 推翻（offline verifiable=1621 vs conceptual online possible=1681，且 `S_OBSERVABILITY.md:173-179` 明示离线 U 不约束在线探针）。三维「不可兼得」作为**任意 (t,f) 前缀谓词的不可能性**命题不再成立——存在一个确定性前缀读取谓词同时达到 precision=0.999404、W={26,73,117}=理想配额、in50_strict=1619/1681。
- **存活①**：配额上界 captured ≤ Σmin(N,c_w)（`_dA_out.txt:191-201`）是组合恒等式，反例恰好**达到** W={26,73,117}=理想值、未违反——上界成立且被证实紧；但它证明的是**配额政策**（每窗 N 次）封顶覆盖率，不是谓词不可能性。
- **存活③**：LB1 下界仍限「形状/序数/相邻游程摘要」特征类（`_dA_out.txt:249`、U5 自限在先）；1µs 精确签名 LB1=0 本就是调查件 U5 登记内容（`_dA_out.txt:280`），复核 :93-94 亦复现——反例是 U5 的具体化，不是新领域。
- **存活④（降格）**：1621/1681 只作「固定外部采样器下的离线可证计数」，不作在线/物理上界（复核 :111-112 的原话）。
- **存活（狭义）**：「不是调参能绕过」在 11+4 档粗特征类及其调参空间内仍成立——反例不是 D1–D5 的调参，是新谓词类（1µs 签名记忆查表）。
- 反例自身明确不构成工程可行性（:120 括注、`:734`），故不能由它宣布「区分度问题已解」。

**判定**：崩点为真（复核指控属实）；剔除越界措辞后，「不可兼得」仅以「已测 11+4 档粗特征类判据的性质 + 配额政策上限 + 离线可证计数 + 自限特征类 LB1」的缩减形式成立；通用命题（任意前缀谓词、在线/物理上界）死亡。**部分闭合，不可升格。**

## 2 维 B —— 崩点 1（指错对象）闭合，且不影响 12 格数值；维整体部分闭合

被核对象一 SHA256 = 4a3424050125b98c0dd3a9a76ec6603fc03ad976e0b9fdecfb34d3b683b94726，字节数 = 48343（`lead/dtrigger_compare_20261107/CRITERIA_COMPARE.md`，本轮实算）
被核对象二 SHA256 = 3e9588ce1def2ebc5b9ad77a3ce242b47bcada4ae1ab1bc4ea606775edd40807，字节数 = 14479（`_dB_anchor_recompute_out.txt`，本轮实算）

- **指纹核实**：`4a342405…/48343` 确属 CRITERIA_COMPARE.md，不是 `_dB_anchor_recompute_out.txt`（后者为 `3e9588ce…/14479`）——复核「指错对象」在指纹层面属实（`_verify_B_out.txt:61-63` 同判，该件本轮实算 SHA256 = 4ee6a6b78d80a336c3431a6f71d9f5a77fec93ef65b7a4c642a49b669368c107，字节数 = 7229）。
- **但**：`_dB_anchor_recompute_out.txt:18-19` 自标「被核对象 = lead/dtrigger_compare_20261107/CRITERIA_COMPARE.md §3.2；铁律 9 指纹行」——该指纹与其自述对象内部自洽；「指错」是证据链引用瑕疵，不在数值计算路径上。
- **12 格数值不受影响（本独立验证，`_dB_anchor_recompute_data.json` SHA256 = 8fb149f21e9b41d7c808e8f8c2e1cb35ca62b881ebe65bfba7029b6f95763794，字节数 = 42910）**：从每档 `waits` 原始数组重算 (nTrig, >=100, +e>50, min/med/max) 六组值，与主表 `_dB_anchor_recompute_out.txt:50-55` 逐值全等（29/5/29/66.334/70.931/321.002、24/24/24/125.884/127.491/440.389、24/24/24/128.284/130.237/461.598、16/16/16/251.709/256.261/258.378、16/16/16/254.247/258.835/260.904、15/15/15/377.385/385.601/387.990）；realHits 8/8/8/1/1/0 与 data.json cells 一致；再与上游 `CRITERIA_METRICS.json`（SHA256 = 7e2533eabf795e8aa0063a16ee875d95742880dcefab55d596cfc5aa6e7f958b，字节数 = 17926）的 `triggers`/`realHits` 六档 ALL_MATCH=True（`_r3_metrics_cross_out.txt`）。`e_med_full = 2.510999998776242` 与 U4 一致。输出：`_r3_b12_recheck_out.txt`。
- **注意**：复核 B 其余崩点（2 evidence 指纹串损坏、3 自检硬编码 `_dB_anchor_recompute.py:401-413`、4 `+e>50` 六格空列零判别力、5 「统一锚」是选择非推导、6 og=None 答非所问）不在本 ask 核对范围、未见闭合证据；崩点 5 的 runStart 敏感性（C2-abs-P95x2 → 27/4/27，`_verify_B_out.txt:48`）仍登记在案。**判定：指错对象崩点闭合、12 格数值经三层独立对账成立；B 维整体部分闭合，不可升格。**

## 3 维 C —— 三条主张闭合（读数层 + 数据层双验）

被核对象 SHA256 = a0deb34a4aed83efe3d0b80dfff4f05eb28eeec5fac5613ff49316fd8081337a，字节数 = 13473（`_dC_out.txt`，本轮实算）

- **读数层（实读）**：`:28` 格数=156（26 判据 × 6 情景）；`:29` 分解式不成立的格 = 0/156 PASS；`:30` 两项均>=0 违例 = 0/156 PASS；`:31` 链式违例 = 0/156 PASS；`:36` A + B = 54 + 102 = 156（PASS）；`:41` A 族 noFalse == 理想 = 54/54 PASS。三条全部成立。
- **数据层（本轮独立复算，`_dC_cells.txt` SHA256 = 8e05b65e8d4bface4e80b5df5bc246a41ea1800c808bf5b69b4a7587c747e6f1，字节数 = 25324）**：解析全部 156 数据行 → decomp 违例 0、非负违例 0、链式违例 0；A=54 / B=102 / 未归类 0 / A+B=156；A 族 noFalse==ideal 54/54；附带复核 B 族 noFalse−captured==0 = 71/102、capUpper==ideal = 73/102、交集 71、captured==ideal = 0——与 `_dC_out.txt` 及 CRITERIA_ROUND2.md §4 所引全部一致。输出：`_r3_data_recheck_out.txt`。
- **残留（不阻这三条）**：报告 §4 崩点 1（`_dC_recompute.py:356-368` emit 常量串、all_pass 门不含子断言）与崩点 2（§9.7「高档 ≥100ms」13 档仅 4 档全部≥100）属证据链/措辞层，本 ask 未核、未见闭合证据。**判定：本 ask 三条崩点查证闭合；C 维整体部分闭合，不可升格。**

## 4 维 D —— 部分闭合（「独立证成」强度崩塌；硬阻断以弱化形式站立）

被核对象 SHA256 = 0e5e84331b2126bd487b526c71095f432303974cdc3960b28794c32807bef84a，字节数 = 3352（`_verify_D_out3.txt`，本轮实算）

- **实读 `:7-10`**：`T3 _dD_check.py B4 block lines 128-137 … computed=0 literal_prose=10`；`T3 B3 block lines 114-125: computed=0 literal_prose=12` ✓ 与 ask 所述一致。
- **源码级亲读（`_dD_check.py` SHA256 = f2f3c561ded7b209f9206891e688642913ae15410fd2abbe8b075a0165f91907，字节数 = 7909）**：B3 块 `:114-125` 恰 12 个 `out()`、B4 块 `:128-137` 恰 10 个 `out()`，全部为字面串、无任何 `%` 插值——含 `:117`「本轮实跑 e>0 计数=28317/28317」、`:119`「本轮实跑 U>50ms 真实事件=56 条」也是硬编码文字（数字在 B1 块另有实算，但 B3 行未引用计算值）。复核 T3 主张在源头成立。
- **硬阻断判定**：
  - **被削掉的**：调查件 `_dD_PHYSICAL_S_ALIGNMENT.md:114`（SHA256 = bb61eedbddea61e9ffcb1ac8981dadd8b3ee0fb12c715ccb3e600ca78c50fac1，字节数 = 18262）把「观测锚下界越线」称作「独立证成的不合规方向结论，不依赖 S」——该**强度**主张不成立：B3/B4 零计算、纯文字；「两个不等式」中 (iii) 是平凡逻辑蕴涵（C−S ≥ C−S_hat >50 ⟹ C−S >50），其前提（观测锚下已 >50ms 的触发）依赖**其它文件**的既有实跑读回（`_dD_check_out.txt:40-41` 自引 supplement），非 D 自己的确定性计算。
  - **仍站立的**：①「物理 S 不可得 → 离线语料肯定性合规确证证据不足」——调查件自身 `:108-110` 原文即「证据不足，未验，不是已证明不合规」，复核未反证该弱化表述，作为未验方向登记仍立；②描述统计层有实跑支撑（`_verify_D_out3.txt:1-3` T1 独立重算 1704/1681/23；`_dD_check_out.txt:9-20` B1 门限表 U>50=56 为实算）；③上游 `CRITERIA_COMPARE.md:34-35,145-147`「不合规方向」记载保持原状。
  - **结论**：「硬阻断」作为已证明的独立证成结论**不成立**（该崩点闭合——强度主张被证实为高估）；作为阻断肯定性合规确证的方向性登记仍站立，但只能是「文字论证 + 上游记载 + 观测锚侧描述统计」，不得升格 verified。**部分闭合。**

## 5 汇总

| 维 | 崩点查证结果 | 判定 |
|:--|:--|:--|
| A | 三行反证真实存在、数值逐位一致；三处通用措辞被推翻，①③④以缩减形式存活，反例依赖同语料记忆查表、非工程主张 | 部分闭合 |
| B | 指错对象属实（4a342405/48343=CRITERIA_COMPARE.md）；12 格数值经 waits 全量重算+上游 metrics 三层对账逐值成立，指错不影响数值；其余 5 崩点未核 | 部分闭合（崩点 1 闭合） |
| C | 分解式 0/156、A+B=156、noFalse==理想 54/54 三条在 `_dC_out.txt:29/:36/:41` 成立，且由 `_dC_cells.txt` 156 行数据独立复算全等 | 部分闭合（本三条闭合） |
| D | :7-10 属实，B3/B4 块源码级确认 0 计算/纯文字；「独立证成」强度崩塌，硬阻断以「证据不足、未验」弱化形式站立 | 部分闭合 |

**promotable = 0**：四维均有未闭合崩点或依赖未验前提（A 通用命题已死、反例工程可行性未验；B 崩点 2-6 未闭合且「统一锚」是选择；C 证据链崩点未闭合；D 硬阻断只剩文字+上游记载），无一维满足「崩点全部闭合且不依赖未验前提」。

红线遵守：零真机、零采样代码、未改 ra2youli/**、out/re_work/**、lead/GOAL_*、PENDING_DECISIONS.md、re_line_20261105/**、dtrigger_round2_20261107/**、dtrigger_compare_20261107/** 任一既有件；写域内新增 `_r3_fp_out.txt`、`_r3_data_recheck_out.txt`、`_r3_b12_recheck_out.txt`、`_r3_metrics_cross_out.txt`、本件；未 commit、未 push。
