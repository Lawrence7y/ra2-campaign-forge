# _cd_ 四项崩点补证回件（C 崩点1/2 + D 独立证成/硬阻断解除条件）

撰写者：崩点补证员·GLM。日期 2026-11-08。
任务：逐条补证 `lead/criteria_r3_verify_20261108/R2_BREAKPOINTS_CLOSURE.md` 记录的四项未闭合崩点（:81-82 C 证据链两项、:90-94/:108/:115 D 两项）。只补证崩点事实，不选判据、不改口径 B、不改 STALL_EVENT_DEFINITION.md:177/:190/:191、不改台账、不 commit、不 push；零真机、零采样代码；唯一写域 = `lead/r2_unclosed_cd_20261108/`。

**实跑方式**：`python -I -X utf8 D:/Project/ra2-campaign-forge/lead/r2_unclosed_cd_20261108/_cd_check.py`（exit=0），输出落盘 `_cd_check_out.txt`（22652 字节）。本件行号引用 `_cd_*` 均指本轮实跑输出。

## 0 被核对象指纹（本轮 hashlib 实算，`_cd_check_out.txt:4-18`）

| 对象 | SHA256 | 字节数 |
|:--|:--|--:|
| lead/dtrigger_round2_20261107/_dC_recompute.py | ec64adac558e87e5cdf53563368c7aacea712222e70f303ca85deb83eb08ee3a | 23115 |
| lead/dtrigger_round2_20261107/_dC_out.txt | a0deb34a4aed83efe3d0b80dfff4f05eb28eeec5fac5613ff49316fd8081337a | 13473 |
| lead/dtrigger_round2_20261107/CRITERIA_ROUND2.md | bcd7c8e53f6987a899f78fd1bd8ae90247193f1897aadf15cc58daa45211982a | 49968 |
| lead/dtrigger_round2_20261107/_dD_PHYSICAL_S_ALIGNMENT.md | bb61eedbddea61e9ffcb1ac8981dadd8b3ee0fb12c715ccb3e600ca78c50fac1 | 18262 |
| lead/dtrigger_round2_20261107/_dD_check.py | f2f3c561ded7b209f9206891e688642913ae15410fd2abbe8b075a0165f91907 | 7909 |
| lead/dtrigger_round2_20261107/_dD_check_out.txt | 7cdfcf9efb76ddffec3a8ea68a536b28f0099d2d571fc18c64d52cf0a8c9491b | 5117 |
| lead/dtrigger_round2_20261107/_dD_align.py | 446978109968bf3d9d3fab49a6a176c5f504ddfdc5d46e6f95c87c8b463dc6e6 | 18733 |
| lead/dtrigger_round2_20261107/_verify_D_out3.txt | 0e5e84331b2126bd487b526c71095f432303974cdc3960b28794c32807bef84a | 3352 |
| lead/dtrigger_compare_20261107/CRITERIA_COMPARE.md | 4a3424050125b98c0dd3a9a76ec6603fc03ad976e0b9fdecfb34d3b683b94726 | 48343 |
| lead/dtrigger_compare_20261107/_dtrigger_supplement_out.txt | f0177d2cbafdb4dbd388d6b38b97d14ae73688f36f58df4f0fff7edc31a59b66 | 5088 |
| lead/dtrigger_compare_20261107/_dtrigger_probe_out.txt | 3be36ba259b50c88751d2c1fca73a242421671e27676f3b629e8f523b8383a51 | 17525 |
| lead/stall_event_def_20261106/STALL_EVENT_DEFINITION.md | ed8951e72bd61cd322b1687c4496ec9fc0e8a362c1425d4020901228d885a001 | 27271 |
| lead/d30_ruling_20261106/RULING_D30.md | d5afc90c50bbf57be1e58bf9000b1940392337b6c57a444e3b084fe57983d04f | 13197 |
| lead/criteria_r3_verify_20261108/R2_BREAKPOINTS_CLOSURE.md | bf426786db82c34dd6b6d21e3022678285e3e22f52dbdaa5085d85c3b6f8fbde | 22351 |

与编排方实跑指纹 6 项全部逐位一致。**未重跑**任何调查/复核脚本（`_dC_recompute.py`、`_dD_check.py`、`_dD_align.py` 等只读冻结）；本轮检查 = AST 解析 + 既有输出解析 + supplement/probe 原件独立解析。

## 1 C 崩点1（emit 常量串 + all_pass 门不含子断言）→ **闭合（崩点属实，实跑证实）**

**(a) emit 判定文字性质 = 混合：数值行按实算生成，证据链文字与 PASS 文案为硬编码常量。**
- AST 实算（`_cd_check_out.txt:21-36`）：`:356-:369` 区间 emit 共 **6 处，纯字面串 6 处、含插值 0 处**（:356=7c-2、:358=7d、:360=7e、:362=7f、:364=7g、:367=7h）。R2:81 所记「:356-368 emit 常量串」属实。
- 对照：逐检 PASS/FAIL 标记与数值行是按结果生成的（`_dC_recompute.py:330/:354` 的 `"PASS" if not bad_within50 else "FAIL"` 等插值），总判定的 PASS/FAIL **选择**也按 `all_pass` 生成（`:420`）。
- **总判定 PASS 分支的文案是硬编码常量**：`_dC_recompute.py:420` `emit("  总判定 = %s" % ("PASS（上述 9.1–9.7 均按本轮实跑成立）" if all_pass else "FAIL"))`——该文案宣称 9.1–9.7 全部成立（`_cd_check_out.txt:77`）。

**(b) all_pass 门不覆盖全部子断言——属实。**
- AST 提取（`_cd_check_out.txt:37-50`）：门 = 11 个比较项（156/54/102/156/54/54/0/54/71/71/73）+ `not decomp_fail/nonneg_fail/chain_fail` + `not bad_within50` + `not probe_bad`。
- 22 个检查型变量中 **10 个 NOT in gate**（`_cd_check_out.txt:51-73`）：`A_cap_eq_up`、`A_up_eq_ideal`、`A_maxloss_eq`（=§9.3「附加结构」三断言）、`B_preempt0_recall_gt0`（§9.4「71 格召回损失>0」）、`B_upideal_but_preempt_gt0`（§9.5「多出 2 格是 C3-N16-r2 trip3/trip5、preempt 2/3」）、`named_set`/`not_named`（§9.6「7 档只覆盖 42 格」）、`B_nf_eq_ideal`、`B_recall0`、`cap_eq_ideal`。另 §4「两种分组逐格相同」检查是内联 emit（`:190-193`）未存变量、不可能入门。
- **「高档 ≥100ms」完全无门**：`ge100` 全脚本仅 2 处出现——`:297`（解析赋值）、`:340`（emit 展示），无任何比较（`_cd_check_out.txt:74-76`）。7b supplement「全部越 50ms」逐行 emit（`:338-340`）亦无聚合变量入 all_pass（`_cd_check_out.txt:78-79`）。

**(c) 「部分通过也输出 PASS」的可能 = 成立（结构性），且本次运行已实际兑现于 §9.7 子句。**
- 若任一无门子断言为假，`:420` 仍输出「PASS（上述 9.1–9.7 均按本轮实跑成立）」。
- 本次运行如实登记：被门遗漏的其余数值断言经查**实际全部成立**（`_dC_out.txt:37` 分组相同 PASS、`:46` 附加结构 54/54·54/54·0/54、`:54` 71/71、`:55-57` 两格 preempt=2/3、`:72-73` 42/29 格、7b 九行全部越 50ms——后者经本轮对 supplement 原件独立解析逐档全等，`_cd_check_out.txt:86-103`）；**但 §9.7「高档 ≥100ms」子句无门且数据仅部分支撑**（见 §2），总判定仍输出 PASS（`_dC_out.txt:148`）。
- 补充事实（定性）：6 处常量串的**内容**经直读与被引文件相符——probe:106/128/150/161/172 五行均为「nTriggersBeyond50ms=n/n (100.00%)」（`_cd_check_out.txt:113-118`）、7e 的 probe:171 min=377.385/med=385.601 相符、7f 的 STALL_EVENT_DEFINITION.md:190/:191 与 RULING_D30.md:52 原文相符（`_cd_check_out.txt:128-133`）、7g 的 supplement:44-45 相符（`_cd_check_out.txt:161-162`）。即常量串问题属**脚本内未解析/未校验的可追溯性缺陷**，非内容虚假。

## 2 C 崩点2（§9.7「高档 ≥100ms」越界）→ **闭合（越界事实成立；辖域归属不裁）**

- **指称澄清**：CRITERIA_ROUND2.md 本身无 §9.7 节（其标题仅 §1–§8，本轮 grep 实证）；§9.7 位于 `_dC_out.txt:147`（= 脚本 `:417-419` 的输出），由 CRITERIA_ROUND2.md:98/:387 以「`:147` §9.7」转引。本轮两处均已实读。
- **实算（双源）**：13 档（`_dC_out.txt:80` 名单）中「全部触发 ≥100ms」（supplement 行级 ge100==nTrig）= **4 档**：C2-P95x3(19/19)、C2-P99x3(18/18)、C3-r4(24/24)、C3-r8(16/16)；**部分 5 档**：C2-N16-P95x2(18/45)、C2-P95x2(4/27)、C2-P99x2(1/24)、C3-N16-r2(156/195)、C3-r2(148/180)；**supplement 无行 4 档**：C2-abs-P95x2、C3-r12、C3-r4-clean、C3-r8-clean（`_cd_check_out.txt:99-103`）。`_dC_out.txt:97-109` 7b 表与 supplement 原件独立解析 **nTrig/gt50/ge100 逐档全等**（`_cd_check_out.txt:103`）。与复核登记（CRITERIA_ROUND2.md:98「13 档中仅 4 档全部触发 ≥100ms、5 档只是部分、4 档无行」）一致。
- **越界判定：成立。** §9.7 原文「supplement/probe 中可逐行读回的档全部触发 >50ms、高档 ≥100ms」（`_dC_out.txt:147`）的后一子句**无「可读回」限定词**：按文档自身定义（脚本 `:39-42` NAMED_HIGH；§9.6 `_dC_out.txt:146`「7 档『高档』」），4 档有行级全≥100 证据、C3-r12 由 probe 细部行 min=377.385ms 支持（probe:171，`_cd_check_out.txt:117`），**C3-r4-clean/C3-r8-clean 在 supplement/probe 均无任何行级数据**（唯一读回 = metrics latP50 347.249/259.514ms 中位数，`_dC_out.txt:126`；中位数不能证「全部触发≥100」）→ 2/7 档无支撑；按 13 档读法 → 9/13 档无支撑。两种主要读法下断言均超出可读回数据，即把「部分/无行」写成「已验」。
- 前一子句「可逐行读回的档全部触发 >50ms」**为真**（7b 九行 + 7c 八行全部越 50ms，本轮独立解析一致；probe 主表 `>50`=nTrig 且 100.00% 列，probe:38-45 直读）。
- **不裁部分**：「高档」指括注 7 档还是 13 档 = CRITERIA_ROUND2.md:98/:387 已登记的待裁决项②，本件不裁定；上游 CRITERIA_COMPARE.md:146（本轮直读，`_cd_check_out.txt:167`）本就把「≥100ms」限定在恰这 4 档（C2-P95x3/C2-P99x3/C3-r4/r8）。本轮 4/5/4 计数对任一裁决均可用。

## 3 D 独立证成（B3/B4 computed=0 下还剩多少支撑）→ **闭合（崩塌定性获独立复算支持；剩余支撑=三层，已量化）**

- **computed=0 独立复现**：AST 实算 `_dD_check.py` B3 块（:114-125）out() **computed=0 / literal_prose=12**、B4 块（:128-137）**computed=0 / literal_prose=10**（`_cd_check_out.txt:136-137`），与 `_verify_D_out3.txt:7-10`（T3）同值。对照 B1（:82-94）computed=2/literal=6、B2（:97-112）computed=3/literal=5（`_cd_check_out.txt:139`）——**B1/B2 是实算块，B3/B4 是纯文字块**。
- **D 未复算逐档越线数（本轮 grep 实证）**：`_dD_check.py` 全文仅 :121 一处提到 supplement（纯文字引用）；`_dD_align.py` 命中 4 处——:66-67 为指纹清单路径串、:348/:362 为纯文字 out()，**无任何解析/重算 supplement 表行的代码**（`_cd_check_out.txt:140-147`）。
- **D 自己实算的只有母体级量**（`_dD_align_out.txt` 直读）：e>0=28317/28317（:29）、U>50ms=56（:41）、B⊂A 逐事件相等 1677/1677（:47-48）、d_final>=100=1704/1681（:50）——支撑「观测锚为严格下界」的**母体前提**，不支撑任何判据的逐档越线计数。
- **逐档前提 = 单源读回**：B3(iii) 纯文字自引 `_dtrigger_supplement_out.txt:11-24,29`（`_dD_check.py:121`）；被引行原文本轮直读相符（supp:11-14/20-22/24：C2 族 >50=nTrig、四档 >=100=nTrig；supp:29 C4-t48 加 e 后 5168/5168；`_cd_check_out.txt:148-158`）；上游登记 CRITERIA_COMPARE.md:34-35/:145-147 原文相符（`_cd_check_out.txt:163-168`）。
- **剩余支撑（对「观测锚下界越线独立证成不合规方向」主张）**：
  1. 逻辑层：不等式 (iii)（C−S ≥ C−S_hat > 50 ⟹ C−S > 50）**有效但平凡**——无需计算即可成立，该层站立；
  2. 母体层：D 自算的 e>0=28317/28317、U>50=56 支持下界普遍严格的**前提背景**；
  3. 数据层：逐档越线计数**全部来自外部单源读回**（supplement_out.txt），D 未独立复算；上游登记（compare:34-35,145-147）为同源转记。
- **结论**：「独立于 S」的推理方向成立；「独立证成」作为「由 D 自身确定性计算独立证成」**不成立**——强度降为「有效逻辑 + 母体级旁证 + 单源读回」，非归零。R2:90「崩塌成立、弱化形式站立（调查件 :88/:104/:108-110）」获本轮独立复算支持。

## 4 D 硬阻断解除条件（§4 O1–O5 是否可验收）→ **部分闭合（不是纯名称列表；「可验收」未完全确证）**

- **清单形态（`_dD_PHYSICAL_S_ALIGNMENT.md:124-130` 直读，`_cd_check_out.txt:172-179`）**：O1–O5 每项含名称+口径定义+精度要求，另有结构性约束——O1 须与 S_hat 逐事件配对、保留区间校验 S∈(S_low,S_hat]、覆盖声明母体每条事件；O2 与 O1 一一配对；O3 残差 ≤1ms 且明写「若不满足则 C−S 不可判定，P 不闭合」；O4 缺失数=0、归属误配数=0；O5 为条件项（仅当覆盖 4 条 startTick=0 事件时必需，否则须显式声明覆盖母体）。并有充分性主张（:132）：「O1–O4 到位后，逐事件直接计算 C−S 并与 50ms 比较即可闭合 P」。**→ 不是纯名称列表**：含可检验谓词与充分性结构。
- **但三点缺口（本轮实跑/直读证实）**：
  1. **必要性是纯断言**：:122 指「逐项必要性见 `_dD_check_out.txt:46-55`」，该段（B4 块）AST 复算 computed=0/literal=10——「缺一则不可闭合」为逐行文字，无构造性证明或反例计算（`_cd_check_out.txt:137,185-186`）。
  2. **O1 精度括注算术不一致（本轮实算）**：:126「时间分辨率 ≤1ms；逐事件不确定度上界 ≤1ms（合计 ≤ :177 的 50ms 预算的 2%…）」——合计 2ms/50ms = **4.0%**，仅单项 1ms/50ms = 2.0%（`_cd_check_out.txt:183-184`）；「合计」措辞与「2%」在求和读法下矛盾（与 `_verify_D_out3.txt:17` T5 同向，本轮独立复算）。
  3. **验收程序缺席且未执行**：:134 纪律声明「只列观测量名称、口径与精度要求；不含任何获取手段…本轮未获取任何新观测量」——清单定义「观测什么、到什么精度」，未定义「如何获取/由谁核验 ≤1ms 不确定度上界」；解除条件本身未被执行（无新观测量落盘）。
- **「需同时补 S 与 C 才解除」的说法**：与清单结构一致（O1=S、O2=C、O3=时基关系量、O4=标记；:114「解除前者至少需要同时补 S 与 C（见 §4）」、:122「最小集 = O1–O4（缺一即 P 不可闭合）」）。

## 5 汇总

| # | 崩点 | 判定 | 一句话事实 |
|:--|:--|:--|:--|
| 1 | C emit 常量串 + all_pass 门 | **闭合** | :356-369 六处 emit 全字面；门漏 10 个检查变量+ge100 无比较+7b 无聚合；PASS 文案硬编码覆盖 9.1–9.7 全体；部分通过输出 PASS 的可能成立并已兑现于 §9.7 子句（其余无门断言本次实查恰好全真） |
| 2 | C §9.7「高档 ≥100ms」 | **闭合（越界成立；辖域不裁）** | 实算 13 档全部≥100 恰 4 档（5 部分、4 无行），双源对账全等；断言无「可读回」限定，7 档读法下 2 档无行级支撑、13 档读法下 9 档无支撑 |
| 3 | D 独立证成 | **闭合（崩塌属实）** | B3/B4 computed=0 复现；D 未复算逐档越线；剩余支撑=有效平凡逻辑+母体级自算旁证+单源外部读回，非归零 |
| 4 | D 硬阻断解除条件 | **部分闭合** | O1–O5 有口径/精度/配对/覆盖谓词与充分性主张，非纯名称列表；但必要性纯断言（computed=0）、O1 括注 2%≠4% 算术不一致、验收程序缺席且未执行 |

**closedCount = 3 / 4。** 未重跑任何调查/复核脚本；未改任何只读件；未 commit、未 push；零真机、零采样代码。
