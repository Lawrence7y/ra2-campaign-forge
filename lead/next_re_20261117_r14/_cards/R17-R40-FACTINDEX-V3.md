# 卡 R17-R40-FACTINDEX-V3 · 把「引用最多的那批数字」补进 `FACT_INDEX`（v2 → v3）

**产物目录必须写 `lead\next_re_20261117_r14\R17_R40_FACTINDEX_V3\`；产物不得含 CR；`fact_id` 用 `## §` 无关，是 TSV 列。**
本卡是**文档编辑**卡：不执行逆向、不启动 gamemd。

## 〇、缺口（本卡的理由）
`FACT_INDEX` v2 有 21 条，覆盖了二进制结构类事实（vtable 定名、`0x43F180`/`0x449440`、调用方链、②-b 收口等）。
**但它没有收录全项目「引用最多、也最容易被断章引用」的那批 coverage 数字**：
`[已证] 1,654`、strict `1,331`、④ 三口径 `458/291/293`、完全无 ④ `1,196`、`R_OK 863`、`R_TRACE_ONLY 791`、`R_MISSING 0`。
这些数字在交付摘要里是**带三项限定**的（L1/L2/L3），在 `PANEL` M69–M102 里也有强制披露。
**若索引不收录它们（连同限定），下任从索引出发就会裸引 1,654。**

## 一、要新增的条目（`F22`–`F26`，逐条照此写）

**`F22` · `[已证]` 1,654 与它的三项限定（必须同框）**
 `statement`：`全表 [已证] 1,654 行；引用时必须与三项限定同框：① 其中 791 行以 classification_trace 为唯一 evidence_path；② ④ 口径 A 458（27.69%）vs 口径 B 291（17.59%）并列；③ 同格两条 ④ 的真两链 65 行（字面数 304 虚高 4–5 倍，勿引 304）。单独引用 1,654 = 把「按现行口径计分」误读成「四环齐全」。`
 `grade`：`[已证]`（数字）/ 限定为强制同引；
 `evidence_paths`：`R17_DELIVERY\DELIVERY_SUMMARY.md(§1 L1–L3); COVERAGE\PANEL.md(L146–337, M69–M102); R14_COMMON.md(§12.6, §16.1 判据)`；
 `limitations`：`三项限定不可拆；引 1,654 必须同引①②③。`

**`F23` · ④ 三口径与「A 不得当四环齐全」**
 `statement`：`④（第 4 列语义）三口径并列：口径 A（含字符 ④）458 行 / 27.69%；口径 B（含「④ 活表槽位见证」）291 行 / 17.59%；宽口径（B ∪ 「④ direct call」2 行，交集 0）293 行 / 17.71%；完全无 ④ 1,196 行。A − B = 167 行形态混杂（含仅 ③b④ 环标签、仅「④ 不同源」否定句等）⇒ 引用 ④ 必须注明口径，不得把口径 A 当作「四环齐全」。`
 `grade`：`[已证]`；`evidence_paths`：`R17_DELIVERY\DELIVERY_SUMMARY.md(§2); COVERAGE\PANEL.md(M86–M93)`；
 `limitations`：`口径必须写明；宽松正则 /direct call/ 会多计 10 行（「无 direct caller」等字样），判形态须用全串「④ direct call」。`

**`F24` · `R_OK` / `R_TRACE_ONLY` 与「事实层面无证据」的边界**
 `statement`：`证据可解析度：R_OK 863 / 1,654（52.18%）为上限；R_MISSING 0；R_TRACE_ONLY 791 行（= 116 dump-only + 675 零候选）。675 行已做有界内容级搜索（23,791 文件 / 1.29 GB），真实四环回指 = 0（检测器对已知 11 行正控召回 11/11，故该 0 有判别力）⇒ 791 行属「事实层面没有逐 entry 四环证据」，不是「指针没连上」，**改指针无解，不再投卡**。`
 `grade`：`[已证]`（数字与负结论）/ 归因见 `§16.1`；
 `evidence_paths`：`R17_DELIVERY\DELIVERY_SUMMARY.md(§3 行 5); R14_COMMON.md(§16.1 判据); MED675 相关产物; R16 续线台账 §1054`；
 `limitations`：`R_OK 863 是「至少一个路径解析到真实文件」，不等于「逐 entry 专属证据」；引 §16.1 只能引其「判据」，其表内数字是历史快照（旧 478/374/802），数字须取现盘。`

**`F25` · strict 1,331 的**界向**（上界不是下界）**
 `statement`：`TOTAL strict = 1,331（口径：atlas 内 ∧ [已证] ∧ 语义不含字面「[未证]」），名义 3/22（S15/S16/S17）、严格 1/22（S17）；该 1,331 是**上界不是下界** —— 它排不掉「语义引自文档、从不自陈未证」的行 ⇒ 1,331 不是「合规已证总量」。`
 `grade`：`[已证]`（数字）/ 界向为强制同引；
 `evidence_paths`：`RULING_R15_20261119\work\strict_panel.py(L78); R17_DELIVERY\DELIVERY_SUMMARY.md(§1 表); COVERAGE\PANEL.md(L139–140, M58 界向更正)`；
 `limitations`：`界向不可省；对外声明按 D-44 一律用严格列 1/22，名义 3/22 并列报告。`

**`F26` · DoD 上限与 D-49 裁定**
 `statement`：`DoD 已证不可达，上限 3/22（S15/S16/S17 且这三个已达标）；用户 D-49 正式裁定「DoD 判据不改；接受 3/22 收口，目标改为事实底座可交付完整度」。`
 `grade`：`[流程]`（裁定）；`evidence_paths`：`PENDING_DECISIONS.md(D-49 已裁决条); R14_COMMON.md`；
 `limitations`：`对外口径不变（D-44）：严格 1/22 与名义 3/22 并列报告。`

## 二、硬约束
1. **以 v2（`R17_R38_FACTINDEX_FIX\FACT_INDEX.tsv`）为基底**，保留 `F01`–`F21` **原文不动**，只在末尾追加 `F22`–`F26`。
2. **不得新增卡面以外的数字**；每条 `statement` 必须能在所示 evidence 里找到依据。
3. **每条 `limitations` 不得写 `—`**（`F22`–`F25` 都有强制同引约束）；只有 `F26` 可写口径说明。
4. 产物：`FACT_INDEX.tsv`（26 条）、`README.md`（更新用法：强调 F22–F25 是「引用最多且最易断章」的四条）、`conflicts.md`（沿用 v2，若有新矛盾另记）、`REPORT.md`。
5. **不得修改** `R17_R34_FACT_INDEX` 与 `R17_R38_FACTINDEX_FIX` 下任何文件。
6. 产物**不得含 CR**（写盘后自校验）。
7. 严格 **9 分钟**。