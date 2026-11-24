# 锚定与双件规范 v2（ANCHOR_AND_DUALFILE_SPEC · 2026-11-08 · 复核吸收版）

DA-ANCHOR: sha256=b4e77933ad8f092a02473770d0ec848792971f3fb46f819511e805e493f37417 bytes=0000034637 rule=zeroed-field-v2 eol=raw

- 撰写：交付件撰写员·GLM（动态工作流子代理，新上下文；任务书 = 编排方「【交付】」段）。
- 任务：将本件写入唯一写域 `lead/deliverable_anchor_20261108/`，六节（§1–§6）。本轮**只做规范设计与实例盘点**：不修改任何既有交付件、不补写任何既有件绑定行、不删除任何双件、不改台账、不 commit、不 push；零真机（未启动游戏主程序／加载器可执行体、未用进程终止命令收尾、未读活进程内存）；零采样代码（未写 hook／内存转储／线程挂起／栈遍历／探针注入／ctypes／OpenProcess／ReadProcessMemory 类代码）。
- 指纹方法：本会话 `python -I -X utf8` + hashlib 独立实算（批量脚本 `_spec2_fp_all.py`，本写域内，纯只读遍历＋全域检索）；**未照抄**任务书【编排方指纹】与复核回件给值，但与两者逐位一致（§5.2）。
- 复核状态：前置审计件 `_da_ANCHOR_AUDIT_AND_SPEC_20261108.md`（24754 B）经独立复核 **verdict = partial**——按本轮铁律「refuted 或 partial 标 unconfirmed」，该件及其结论在本件一律标 **unconfirmed**；崩点 P1–P5 在 §5.2 逐条吸收。git status --porcelain 本会话实跑：六个交付写域维持 `??` 未跟踪，3 处 `MM` 均为会话开始前既有台账件；HEAD = `26574589aa8401e8f3f2934680a1ea7109bafa2d`（git log -1 实跑）。

## 1 目的与边界

1. **目的**：①把任务书指名的三个实例（版本锚指向被覆盖的 r1、双件并存×2）按「原文＋现盘实算」固化；②给出六写域锚与双件盘点表——并按复核回件把检索口径从「写域内 grep」修正为「全域 lead/ 检索」；③落五条规范（S1–S5，§5.3），逐条吸收复核崩点 P1–P5；④如实登记复核回件与未验项。
2. **边界（只设计，不代修）**：本件对既有件**零写入**——不补绑定行、不删双件、不改台账；规范条文（§5.3）的适用对象是**后续**新交付件与新验收回件；既有件是否按规范补锚属后续轮次决策，不由本件代行。本写域本轮新增 3 件：本件、`_spec2_fp_all.py`、`_spec2_anchor_check.py`（写域内既有 4 件——审计件、审计两脚本、复核员 `_verify_hy4_anchor.py`——一字未动，指纹见 §4.4）。
3. **上件关系**：本件承接 `_da_ANCHOR_AUDIT_AND_SPEC_20261108.md`（下称「审计件」，其 DA-SPEC v1 = R1–R7）与复核回件（verdict = partial，§5.1）；R1–R7 中被复核坐实的部分（R2–R6 实例基础）由 S3–S5 吸收，被复核证伪或失准的部分（R1 算法语义、R1:114/R4:133/R7:150 引用的「5 个正本完全无锚」基线）由 S1/S2 修正后重建。
4. **口径总声明**：凡本件断言「有锚/无锚」，均指本会话全域检索（§4.0）结果；凡「未验」，指本会话未实跑或证据未获得，不补造（§6.3）。

## 2 实例一 版本锚指向被覆盖的 r1（第 4/130/159 行原文 + 现盘实算）

被核件：`lead/a_residual_n1_20261108/A_RESIDUAL_REFERENCES.md`（r2 修订版）。**现盘自身**（本会话 hashlib 实算）：被核对象 SHA256 = 1209ca4c8149722fffd1731a0f435637a2988a6e90993f87ef632eb4763b585e，字节数 = 33431；同域 `ACCEPTANCE_RECORDS.json` = 被核对象 SHA256 = d847de88bb0c0c04290c877180a9c45c502df773ba297a36406bffecbe66796b，字节数 = 27965。

三行原文（本会话 Read 实读）：

- **:4**（替代声明）：「本件为 **r2 修订版**，就地替代同目录 r1：`A_RESIDUAL_REFERENCES.md`（SHA256 `3343cfbe467d38f442cd9e422e691d0123fc046938c4d242f57c629bd41d4125` / 26,435 B）与 `ACCEPTANCE_RECORDS.json`（SHA256 `15e4731c948b96e140b7c1260d0fa8ffe4b26654565955e12de891a9b463d420` / 18,045 B），两者均为本撰写会话**覆写前 hashlib 实算**。修订动因 = r1 的独立复核 **verdict = partial**（回件照录见 §5）……」
- **:130**（本件唯一「被核对象」**绑定行**，位于 §5.1 复核回件照录段，:128 明标「被核对象指纹行（照录……）」）：「**被核对象 SHA256 = 3343cfbe467d38f442cd9e422e691d0123fc046938c4d242f57c629bd41d4125，字节数 = 26435**」
- **:159**（未验项第 11 条）：「r1 两件被就地覆盖后**无独立副本留存**（写域限制仅两件）；r1 全文以编排方会话日志与本件 §5 照录承载，其指纹 `3343cfbe…`/`15e4731c…` 为**版本锚**。」

判定（承接审计件 §2.1 与复核回件，并按复核口径修正）：

1. **版本锚失效坐实**：:130 绑定行指向 r1 旧值 3343cfbe…/26435，而该路径现盘自身 = r2 值 1209ca4c…/33431（本会话实算）；任何按行复核者必得 mismatch。r1 两件本体已不存在，旧值**不可现盘复算**（未验·结构性不可验）。
2. **语境细化（防止误读为「锚值写错」）**：:4 是替代声明（明写「就地替代」「覆写前实算」），:130 在照录段且 :128 有标注——两处均未冒充现盘锚。缺陷实质 = r2 两件无件内自锚 + r1 覆盖不可复算。
3. **按复核 P1 修正的锚状态**：r2 MD 拥有**跨域验收锚**——`lead/n1_r2_verify_20261108/N1_R2_ACCEPTANCE.md:20`（表行绑定 1209ca4c…/33,431）、`:22`（绑 `_n1_records.py`）、`_v_evidence_log.txt:6`、`_v_verify_report.md:10`、`_v_r1gen_probe_err.txt:9`、`_v_r1gen_probe_out.txt:31/:57/:83/:109/:135/:161`；域内他绑 = `ACCEPTANCE_RECORDS.json` 内 **8 处**（本会话 `grep -c "1209ca4c"` = 8，行号 :52/:71/:99/:126/:153/:180/:207/:234）。r2 JSON 拥有**跨域验收锚** = `N1_R2_ACCEPTANCE.md:21`、`_v_evidence_log.txt:7`、`_v_verify_report.md:12`（N1_R2_ACCEPTANCE.md mtime 11-08 11:55，早于审计脚本 14:09——`ls -la` 实读）。**故审计件 §2.1-超纲B「JSON 全域 grep 0 命中/验收尚未发生」与 §6-4「验收方回件未获得」不成立**（unconfirmed 项）；「r2 两件无自锚、验收闭环依赖外部回件」仍成立（N1_R2_ACCEPTANCE.md:30 同此表述）。
4. **按复核 P5 修正的论据**：r1 JSON 旧值 15e4731c…/18045「不可复算」成立且有**负结果佐证**——`N1_R2_ACCEPTANCE.md:29` 记载：以现盘 r1 生成器 `_n1_records.py` 重构（stdout 18,045 B，恰等 r1 JSON 字节数）后替换指纹串，得 ec455e1f… 与 259ceb2e… 均不命中 15e4731c…；本会话实算 `_v_r1gen_probe_out.txt` = ab9dc7aebd381993cd363140f4a98ff54ba7ce51baab5809d01b6df72564513a / 18045（**字节数同、指纹不同**——重建输出，非 r1 原件）。审计件 §6-1「r1 JSON 连佐证输出件都没有」措辞失准（unconfirmed 项）；r1 MD 侧佐证 = `_n1_records_out.txt:9`「A_RESIDUAL_REFERENCES.md SHA256 = 3343cfbe… 字节数 = 26435」（mtime 10:04 早于 r2 落盘 10:47，本会话 ls -la 实读；该输出件自身全域无锚，§4.2）。

## 3 实例二与实例三 双件并存（字节数、指纹、正本归属）

### 3.1 实例二（N-11，perf_repair_n11_20261108）——审计判「部分成立」，复核未推翻，**unconfirmed（随全局 partial）**

- **双件并存坐实**（本会话 hashlib 实算）：正本 `PERF_REPAIR_HANDOFF.md` = 被核对象 SHA256 = 7a617a43b32fc2e38c7e46ff9d436f903810ad9cae919fc0eb891a0f9f5796e0，字节数 = 29619；前置草稿 `_n11_PERF_REPAIR_HANDOFF.md` = 被核对象 SHA256 = cf73fd80edbc538cd7fa5f2f6b69a759f8c00eeac903153146d533dd74a73269，字节数 = 22745。
- **正本归属**（件内明文，本会话 Read 实读）：正本 = `PERF_REPAIR_HANDOFF.md`。:1 自标「正式落位版」；:6-9「前置草稿 _n11_PERF_REPAIR_HANDOFF.md（同目录、22745 B）已经独立复核 verdict = confirmed……两件并存登记，内容承接，**本件为验收对象**」；:190「目录既有 8 件（前置草稿 5 件 + 复核员 3 件）并存不动」。
- **审计「均缺指向自身的清晰版本说明」按字面不成立**（审计与复核一致）：`_n11_:155`「本件自身指纹不入本件（自指），由回执另行登记」；正本 :132/:190 同款声明。真实缺口 = **两件均无件内自锚**。
- **绑定行方向**：本域唯一「被核对象」绑定行 = 正本 :117，指向**草稿**（被核对象 SHA256 = cf73fd80…73269，字节数 = 22745，语境为复核回件被核对象，正当）——验收链绑定停在草稿层。
- **按复核 P1 修正**：正本登记不止输出件一处——域内输出件 `_deliver_hash_post_out.txt:7`「交付件 SHA256 = 7a617a43…，字节数 = 29619」（该输出件现盘 = dd66937ac4927fe65099f6491b88cb154ae6aabc297fdd9853d31d4b500ecbaa/1168，**全域 0 命中**，自身无锚）；**另有 3 处跨域登记**：`lead/d13d14_cards_20261108/DECISION_QUESTIONS.md:31`（表行「MATCH」）、同域 `_n10_D13D14_CARDS_20261108.md:25`、`_n10_fingerprint_out.txt:6`。审计件 §3.2-2「仅输出件登记 1 件」作为「正本单点失锚」论据失准（unconfirmed 项）；「唯一域内锚是一自身无锚的输出件」仍成立。

### 3.2 实例三（N-10，d13d14_cards_20261108）——审计判「成立」（附角色纠正），复核未推翻，**unconfirmed（随全局 partial）**

- **双件并存坐实**（本会话实算）：承接正本 `DECISION_QUESTIONS.md` = 被核对象 SHA256 = 0a709f2da12e0234cd94ff0baf521652e7d1aed6cfd04929b9728adbfd85bf5f，字节数 = 27172；登记本体 `_n10_D13D14_CARDS_20261108.md` = 被核对象 SHA256 = 8a36d60a98ab6f19d3bc5229952e0318f492c2091d0bdc3b58b7d83cd9a12a7c，字节数 = 30122（本会话实算与绑定行同值）。
- **绑定行**：正本恰 1 条「被核对象」行 :130，指向 _n10_ 件（30122 B）；§1 表末行 :34 同值互证。_n10_ 无绑定行（:240 自认「本登记件自身指纹不入本件……由本轮运行回件登记」）。
- **角色纠正**（审计件 §2.3，复核维持）：`DECISION_QUESTIONS.md:3`「登记动作本体 = 同目录 `_n10_D13D14_CARDS_20261108.md`，本件为其承接汇总」——_n10_ 是被核**登记本体**，非废弃中间稿；两件为有分工的双件。真正缺陷 = 承接正本现盘自身在验收链内 0 锚（§4.1）。
- **复核 P5 补充语境（本会话实读坐实）**：`NEXT_STEPS_20261106.md:95`（N-10）字面「**本目录** DECISION_QUESTIONS.md」按计划件目录应为 `lead/nextstep_plan_20261106/`，实落 `lead/d13d14_cards_20261108/`——路径裂口在 DQ:18（「落位本件前 ls 实跑：该目录仅三件，DECISION_QUESTIONS.md 不存在」）与 _n10_:239 件内明文，属双件关系之外的第三层裂口；perf 域同类裂口（NEXT_STEPS:103「本目录 PERF_REPAIR_HANDOFF.md」→ 实落 perf 域，PERF_REPAIR_HANDOFF.md:6 自述）审计件已记，d13d14 这层系复核补充，本件予以登记。

## 4 本会话全部写域的锚与双件盘点表（复核口径修正版）

### 4.0 检索口径（S1 条落地，替代审计件 §1-3 的「grep <写域>」）

- 命令：`python -I -X utf8 D:\Project\ra2-campaign-forge\lead\deliverable_anchor_20261108\_spec2_fp_all.py`——①对 7 个写域（六交付域＋锚写域）58 个文件逐件实算 SHA256+字节数；②将全部实算指纹在 **lead/ 全树**做单遍跨域检索：扫描 4295 件、跳过 >2MB 共 43 件（42 件 .png＋1 件 .pkl，均为二进制，十六进制登记不可能在其中）、0 读错（脚本输出「scanned=4295 skipped_big=43 skipped_err=0」）。
- 锚分类三口径：**验收链锚**＝交付件/验收回件对现盘值的绑定；**输出件锚**＝同域脚本输出件登记；**审计记录锚**＝审计员/复核员盘点件中的登记（能锁值，但不属交付链，单列不计入「有锚」）。审计记录锚均落锚写域：`_da_ANCHOR_AUDIT_AND_SPEC_20261108.md` 与复核员 `_verify_hy4_anchor.py:50-85`（指纹清单表）。
- 编排方【编排方指纹】11 件与本会话实算**逐件 MATCH**（11/11）；审计件 §3.1 表 16 行逐值 MATCH；矩阵域聚合 524a98ca80b2bb8112a0e0c6b9a8608103964cebaf2168da59f49d7e0594cd4d/33357（五件按文件名升序拼接，本会话复算）与 `MATRIX_BINDING_FACTS.md:90` 逐位一致。

### 4.1 交付层 14 件锚状态表（全域检索结果；「锚落点」均本会话实读行号）

| # | 写域 | 件（角色） | SHA256 / 字节 | 交付链锚（全域） | 锚落点（file:line） | 审计件判定 → 修正 |
|---|---|---|---|---|---|---|
| 1 | a_residual_n1 | A_RESIDUAL_REFERENCES.md（r2 MD） | `1209ca4c…3b585e`/33431 | 跨域验收＋域内他绑 | N1_R2_ACCEPTANCE.md:20；_v_evidence_log.txt:6；_v_verify_report.md:10；_v_r1gen_probe_err.txt:9；_v_r1gen_probe_out.txt:31…；JSON 8 处（:52,:71,:99,:126,:153,:180,:207,:234） | 有他绑（维持） |
| 2 | a_residual_n1 | ACCEPTANCE_RECORDS.json（r2 JSON） | `d847de88…66796b`/27965 | 跨域验收 | N1_R2_ACCEPTANCE.md:21；_v_evidence_log.txt:7；_v_verify_report.md:12 | ~~完全无锚~~ → **跨域有锚**（P1） |
| 3 | perf_repair_n11 | PERF_REPAIR_HANDOFF.md（**正本**） | `7a617a43…796e0`/29619 | 输出件锚＋跨域登记 | _deliver_hash_post_out.txt:7；DECISION_QUESTIONS.md:31；_n10_:25；_n10_fingerprint_out.txt:6 | 仅输出件登记 → **＋3 处跨域登记**（P1） |
| 4 | perf_repair_n11 | _n11_PERF_REPAIR_HANDOFF.md（前置草稿） | `cf73fd80…73269`/22745 | 域内他绑 | PERF_REPAIR_HANDOFF.md:117；_deliver_hash_post_out.txt:5；_deliver_hash_pre_out.txt:5；_deliver_hash_check.py:23 | 有他绑（维持） |
| 5 | d13d14_cards | DECISION_QUESTIONS.md（**承接正本**） | `0a709f2d…85bf5f`/27172 | **无**（全域仅审计记录锚：审计件:53、_verify_hy4_anchor.py:54,:69） | — | 无锚（维持） |
| 6 | d13d14_cards | _n10_D13D14_CARDS_20261108.md（登记本体） | `8a36d60a…a12a7c`/30122 | 域内他绑 | DECISION_QUESTIONS.md:34,:130 | 有他绑（维持） |
| 7 | matrix_binding | MATRIX_BINDING_FACTS.md（核证正本） | `dbe00c85…5805f8b`/19663 | **无**（全域仅审计记录锚：_verify_hy4_anchor.py:56,:71） | — | 无锚（维持） |
| 8 | matrix_binding | _m_MATRIX_DIFF_20261108.md | `aa6aa58f…82dd47`/10077 | 域内他绑 | _facts_fp_out.txt:21；正本:90（单件＋聚合） | 有他绑（维持） |
| 9 | matrix_binding | _m_CHAIN_VERIFY_20261108.md | `636551f7…630162d`/7813 | 域内他绑 | _facts_fp_out.txt:19；正本:90 | 有他绑（维持） |
| 10 | matrix_binding | _m_DECISION_POINTS_20261108.md | `a8a7d2eb…01656`/4939 | 域内他绑 | _facts_fp_out.txt:20；正本:90 | 有他绑（维持） |
| 11 | slowframe_r3 | S604_GAP_RECHECK.md（**汇总正本**） | `5d1b0ecc…bdf726`/19291 | **无**（全域仅审计记录锚：_verify_hy4_anchor.py:57,:77） | —（其 :121-127 反向绑 6 个他件/输出件） | 无锚（维持） |
| 12 | slowframe_r3 | _r3_GAPDIFF_RECHECK.md（R3 复算件） | `98cd612f…cf6e`/11215 | 域内他绑 | S604_GAP_RECHECK.md:121；_verify_r3_out.txt:86,:93 | 有他绑（维持） |
| 13 | criteria_r3_verify | R2_BREAKPOINTS_CLOSURE.md（**闭链正本**） | `bf426786…f8fbde`/22351 | 跨域验收（9 文件） | r2_unclosed_b：_b_breakpoints_2_6_evidence.md:8（被核对象绑定行）,:17、_b_fp_core.py:34、_b_fp_core_out.txt:6,:25、_verify_hy4_fp.py:10、_verify_hy4_fp_out.txt:19；r2_unclosed_cd：_cd_check_out.txt:13、_cd_verdict.md:25、_verify_cd.py:47、_verify_cd_out.txt:20 | ~~完全无锚~~ → **跨域有锚**（P1） |
| 14 | criteria_r3_verify | _r3_CLOSURE_VERIFY_20261108.md（查证回件） | `80c472ac…5200e9`/13597 | 域内他绑 | R2_BREAKPOINTS_CLOSURE.md:34,:99；_verify_hy4_out.txt:1（「rv 80c472ac… 13597」） | 有他绑（维持） |

**分类汇总（自洽）**：交付链无锚 **3**（#5、#7、#11，全是正本层）；输出件锚＋跨域登记 **1**（#3）；有他绑·无自绑 **10**（#1、#2、#4、#6、#8、#9、#10、#12、#13、#14）；件内自锚 **0**（交付层）。3+1+10 = **14** ✓。

### 4.2 支撑层 35 件（脚本＋输出件；指纹本会话实算，供复核重放）

| 写域 | 件 | SHA256 / 字节 | 锚角色备注 |
|---|---|---|---|
| a_residual | _n1_hashcheck.py | `5cc906e7…7b9b48`/1291 | 无锚 |
| a_residual | _n1_records.py | `b089d809…05275`/11968 | 跨域登记：N1_R2_ACCEPTANCE.md:22 等 3 处 |
| a_residual | _n1_records_out.txt | `047eee39…65c79`/419 | r1 覆写前佐证（:9），**自身全域 0 命中** |
| a_residual | _verify_writescope.py | `de3c3a39…28674`/882 | 无锚 |
| perf | _deliver_hash_check.py | `6e2ced11…ee519`/2329 | 无锚 |
| perf | _deliver_hash_post_out.txt | `dd66937a…0ecbaa`/1168 | **正本唯一域内锚，自身全域 0 命中**（:7 登记 7a617a43） |
| perf | _deliver_hash_pre_out.txt | `51ed2eed…72ed6d`/1005 | 无锚（:5 绑草稿） |
| perf | _n11_anchor_out.txt | `ed6702cd…f603`/30320 | 无锚 |
| perf | _n11_anchor_read.py | `036b7677…23152`/3212 | 无锚 |
| perf | _n11_fingerprint_check.py | `f7b9d443…96117`/1515 | 无锚 |
| perf | _n11_fingerprint_out.txt | `0041a6dd…5d43a`/695 | 无锚 |
| perf | _verify_anchor.py | `98bd922f…be60f`/2638 | 无锚 |
| perf | _verify_hashes.py | `0b066765…0b55e3`/1657 | 无锚 |
| perf | _verify_scan.py | `9b73887b…9da5dfb`/2072 | 无锚 |
| d13d14 | _n10_fingerprint_out.txt | `52f93021…f2a08f`/1175 | 跨域登记 perf 正本（:6），**自身全域 0 命中** |
| d13d14 | _verify_n10_cards.py | `dfae5699…997d0`/6366 | 无锚 |
| matrix | _facts_fp.py | `ad471d39…27ba1`/5147 | 无锚 |
| matrix | _facts_fp_out.txt | `d1e1d5e9…93ca08`/3833 | 域内锚册：:19-:24 绑五件 _m_*＋聚合 |
| matrix | _facts_rerun_out.txt | `e768a2d3…3d4d2`/2199 | 与 _m_rebuild_out.txt、_verify_rerun_m_rebuild.txt **三件同指纹**（确定性重建输出） |
| matrix | _m_rebuild.py | `77c091d9…527793c`/8329 | 域内他绑（_facts_fp_out.txt:22） |
| matrix | _m_rebuild_out.txt | `e768a2d3…3d4d2`/2199 | 域内他绑（:23,:41） |
| matrix | _verify_hy4.py | `f545dfae…ae0636`/7434 | 无锚 |
| matrix | _verify_hy4_out.txt | `f5931dd4…8e1c6`/2498 | 无锚 |
| matrix | _verify_rerun_m_rebuild.txt | `e768a2d3…3d4d2`/2199 | 同上三件同指纹 |
| slowframe | _r3_recompute_gapdiff.py | `9e274952…9a78`/12659 | 域内他绑（S604:124） |
| slowframe | _r3_recompute_out.txt | `f1f55791…e54b`/9494 | 域内他绑（S604:125） |
| slowframe | _s604_delta_check.py | `9510589f…38bc94`/2076 | 无锚 |
| slowframe | _s604_fp_check.py | `0914e418…e32f4f7`/2636 | 无锚 |
| slowframe | _verify_r3_gapdiff.py | `253afec0…11bd49`/9811 | 域内他绑（S604:126） |
| slowframe | _verify_r3_out.txt | `0062bb41…30d81a`/6477 | 域内他绑（S604:127） |
| criteria | _r3_b12_recheck_out.txt | `9f4fc77f…c787aca`/1336 | 域内他绑（R2BC:37） |
| criteria | _r3_data_recheck_out.txt | `afe66269…cabe89`/668 | 域内他绑（R2BC:36） |
| criteria | _r3_fp_out.txt | `4e70dd45…6e6edf5b`/1357 | 域内他绑（R2BC:35） |
| criteria | _r3_metrics_cross_out.txt | `7ffb848e…1554960`/550 | 域内他绑（R2BC:38） |
| criteria | _verify_hy4_out.txt | `f38adf59…2cd675`/26210 | 域内他绑（R2BC:39）；**回件后追加漂移已合规披露**（R2BC:100） |

（表值说明：因表宽截断的哈希为末段省略，全文按本会话脚本输出为准；完整 64 位值已在 `_spec2_fp_all.py` 输出中，可重放。）

### 4.3 工具产物与锚写域

- 工具产物（不入锚分类）：matrix 域 `.mimosa/` 内 2 件 hook 状态 JSON（68e9d913…/684、4359bfc9…/406）、slowframe 域 `__pycache__/`。
- 锚写域盘点时点 5 件：审计件 `4ab44028…0376f9`/24754（**件内自锚成立**：本会话实跑 `_da_anchor_selfcheck.py` → 「ANCHOR OK / bytes=24754 / sha256(field)=eba320ec7f74aba09b5568d138f284b70d60241fe94fac7ece763f6b4e2fc96b」，exit=0；但 P3 指出其算法两语句语义不一致，§5.2）；`_da_fp_inventory.py` `e4518f25…bbdba`/1277；`_da_anchor_selfcheck.py` `5f26b553…34145`/1410；`_spec2_fp_all.py` `f8869a48…8bbbab`/4074（本轮新增）；`_verify_hy4_anchor.py` `13bf01a9…ad400`/13670（复核员唯一写入，:83 登记审计件全文件值）。
- 台账件（只读核对）：`PENDING_DECISIONS.md` = `7f68fc6c…fcd48`/50194、`GOAL_THREE_TARGETS_20261018.md` = `2baa0de4…33ede`/759518（本会话实算，与既有登记一致）。

### 4.4 计数自洽（P2 修正）

- 本会话枚举：六写域顶层 **49** 件文件（逐域 6+12+4+12+8+7）＋工具产物 2 件（.mimosa）＝51；其中交付层 **14**＋支撑层 **35**。锚写域盘点时点 5 件。
- 审计件计数三值互斥（复核 P2 坐实，本会话实读再证）：盘点文本称「18 件」；其 §3.1 表实 **16** 行（11 件编排方清单＋5 件 _m_*）；其 §3.2 分类 5+1+**11**=17，而 :86 标题「11 件」下列举实为 **10** 项（r2 MD、_n11_、_n10_、五件 _m_*、_r3_GAPDIFF、_r3_CLOSURE）。「18」无法由任何自然切分重构（审计件未给出成员清单）——**未验**。
- 本盘点计数由脚本输出直接支撑：分类和 = 交付层总数（3+1+10=14），表行 = 14，无第三值。

### 4.5 双件并存清单（本会话全域盘点）

| 域 | 双件 | 正本 | 关系明文落点 | a_residual 为什么不算 |
|---|---|---|---|---|
| perf_repair_n11_20261108 | PERF_REPAIR_HANDOFF.md（29619 B）↔ _n11_PERF_REPAIR_HANDOFF.md（22745 B） | PERF_REPAIR_HANDOFF.md | 正本 :6-9/:190；草稿 :155 | — |
| d13d14_cards_20261108 | DECISION_QUESTIONS.md（27172 B）↔ _n10_D13D14_CARDS_20261108.md（30122 B） | DECISION_QUESTIONS.md（承接）＋_n10_（登记本体，分工双件） | 正本 :3；_n10_ :240 | — |
| a_residual_n1_20261108 | MD 33431 B ＋ JSON 27965 B | — | JSON:52 writeDomain | **配对件非双件**：MD=交付正文、JSON=九字段台账，角色不同（审计件 §3.2-5 判定，复核维持） |

双件共同缺口：两域 4 件均**无件内自锚**（§4.1），正本锚依赖他件/输出件——S3 条针对点。

## 5 复核回件（含 SHA256 加字节数绑定）+ 规范五条

### 5.1 复核回件记录（如实转录，verdict = partial → **unconfirmed**）

- **verdict = partial**；复核自报 ranCommands = 27。按本轮铁律「refuted 或 partial 标 unconfirmed」：前置审计件连同本件引用的其全部结论标 **unconfirmed**。
- **绑定行（照录）**：「被核对象 SHA256 = 4ab44028140a878dcaf815b60debddcc5c0939334af6b27fdc4438aafe0376f9，字节数 = 24754」——被核对象 = `_da_ANCHOR_AUDIT_AND_SPEC_20261108.md`；本会话 hashlib 实算同值同字节数（§4.3），绑定成立。
- 复核同时坐实（照录摘要）：编排方清单 11/11 MATCH；审计件 §3.1 表 16/16 MATCH；聚合 524a98ca…/33357 MATCH；R1 自锚自证 ANCHOR OK；既有件零改动（HEAD 26574589… 不变、3 处 MM 台账件为既有、六写域全 `??`）。

### 5.2 崩点 P1–P5 与本会话独立验证（每条均本会话实跑/实读，非转抄）

| # | 复核崩点 | 本会话独立验证 | 处置 |
|---|---|---|---|
| P1 | 盘点把 grep 限于写域却下全域判定；r2 JSON、R2BC 实为跨域有锚；perf 正本另有 3 处跨域登记 | `_spec2_fp_all.py` 全域检索：d847de88 → n1_r2_verify 域 3 件（N1_R2_ACCEPTANCE.md:21 等）；bf426786 → r2_unclosed_b/cd **9 文件**（_b_breakpoints_2_6_evidence.md:8 为完整被核对象绑定行）；7a617a43 → d13d14 域 3 文件；0a709f2d/dbe00c85/5d1b0ecc 交付链 0 命中（仅审计记录锚命中，见 §4.1 注） | §4.1 表全部改判；S1 条 |
| P2 | 计数三值互斥（18/17/16；「11 件」列 10 项） | 审计件 :86 实读确认「11 件」下列举 10 项；本会话枚举 49 顶层件；§4.4 自洽 3+1+10=14 | §4.4；S1 条 |
| P3 | R1 算法 :105 行首定位 vs :111 首次出现替换语义不一致；未规范 EOL；无照录约束 | 内存实验（不落盘）：构造锚行照录先于真锚行出现的等语境字节流，:111 口径 canon = a2d0259dc5d0167d88bc591d136d5fedd2f6421357aa40c592d6b5b341583729，行级替换口径 canon = d564c4cada941cce5587a5694e4955bf4aa0becbd3ac89362b7ccbe6dd7ef182——同一字节流两个清零区间，语义分裂坐实；审计件 18 字节前缀全文件出现 **3 次**（:3 真锚＋:99/:105 规则文本照录，grep -n 实跑），v1 行首唯一性检查不可见；R1 条文（:96-113）确无 EOL 声明（复核员 CRLF 实验未重放——未验） | S2 条（行级语义＋前缀计数 1＋eol=raw） |
| P4 | 规范漏 4 项：跨写域检索边界、适用对象不含输出件/证据件、照录冲突、盘点计数自洽 | 审计件 §1-3（:14「grep <写域>」）、R1:98 适用对象清单、全文 grep 无照录/计数条文——实读坐实；实例二正本恰靠无锚输出件（dd66937a/1168，本会话实算） | S1/S2/S5 四处补齐 |
| P5 | 「r1 JSON 无佐证输出件」失准；d13d14 第三层路径裂口未登记 | N1_R2_ACCEPTANCE.md:29 实读（负结果记载 ec455e1f…/259ceb2e… 不命中 15e4731c…）；_v_r1gen_probe_out.txt 本会话实算 ab9dc7ae…/18045（字节数同指纹不同）；NEXT_STEPS_20261106.md:95/:103 与 DQ:18/_n10_:239/PERF:6 实读 | §2-4、§3.2-4 登记 |

### 5.3 规范五条（DA-SPEC v2 · S1–S5；每条 = 条文＋为什么需要＋违规/合规定位）

**S1 锚检索口径与盘点自洽（强制）**
- 条文：①判定「有锚/无锚」必须在**声明边界**内全域检索（默认 = 仓库 lead/ 全树；排除项逐项列出并说明理由，如二进制件），禁止以单写域 grep 结果下全域结论；②命中必须区分三类锚（验收链锚／输出件锚／审计记录锚），交付链结论只依据前两类；③盘点计数必须自洽：表行数＝分类和＝声称总数，且由脚本输出直接支撑；④检索命令、扫描件数、跳过件数与理由、exit 状态随盘点落盘。
- 为什么需要：审计件把 d847de88（r2 JSON）、bf426786（R2BC）判为「完全无锚」、把 7a617a43 判为「仅输出件登记」，全部因检索边界过窄；复核全域反证后「5 个正本完全无锚」基线降为 3 个（§4.1）——同一个错误口径同时污染实例判定与 R7 现状分级。
- 违规实例：审计件 §3.2-1（:84）五件清单中 2 件被 P1 反证；§1-3（:14）即口径根源。

**S2 件内自锚 v2（强制；替代 R1）**
- 条文：每个交付件（**含正本、登记件、复核回件、修订版、登记用输出件、证据输出件**）件内含唯一锚行，行首标记 = ASCII「`DA-ANCHOR:`」（10 字节）＋空格＋「`sha256=`」（7 字节），其后 64 位十六进制锚值、` bytes=`＋10 位零填充定宽字节数、` rule=zeroed-field-v2 eol=raw`。锚值 = 将**行首定位所选那一行**的 sha256 字段就地清零后全文件字节流的 SHA256（行级替换，与定位同语义）；18 字节前缀全文件仅允许出现 **1 次**（照录防护：规则文本引用格式必须拆写，不得形成连续前缀）；`eol=raw` 显式声明不做 EOL 归一化；字节数字段与 `len(原始字节流)` 相等。可执行算法 = `_spec2_anchor_check.py`（本写域，fill/check 两模式，与 v1 差异三点见其文件头）。
- 为什么需要：①自指悖论可解（规范化字节流哈希），而全会话既有件一律答「不可计算、移交登记」，致交付层 0 件自锚、3 个正本验收链 0 锚（§4.1）；②v1 算法两语句语义分裂已被实验坐实（canon 双值，§5.2-P3），照录即可能误伤；③登记链末端的输出件自身无锚时正本仍单点失锚（_deliver_hash_post_out.txt = dd66937a…/1168 全域 0 命中）——故适用对象必须扩到输出件。
- 违规实例：审计件自身（前缀 3 处、:105/:111 语义分裂）；交付层 14 件 0 自锚。

**S3 双件并存管理（强制；吸收 R3）**
- 条文：同写域同题双件：①恰好一件件内自标验收对象（正本），并明文指认另一件及字节数；②另一件回指正本或明示自身角色（前置草稿/登记本体）；③正本必须满足 S2；④配对件（角色不同的 MD＋JSON 类）不属双件，盘点不得误并，但两件各自适用 S2。
- 为什么需要：双件并存时「哪件算数」无件内明文则验收者只能靠大小/mtime 猜；两域双件关系明文化已做对（§4.5），缺的是正本自锚——R3(c) 全域未满足。
- 违规实例：两域 4 件均无件内自锚（§4.1/#3/#4/#5/#6）；perf 正本绑定行（:117）指向草稿，验收链停在草稿层。

**S4 验收绑定必须落到正本现盘自身（强制；吸收 R4/R5）**
- 条文：①验收记录/sha256Line/指纹清单最终必须绑定**当轮正本**的现盘自身全指纹（64 位）＋字节数；复核发生在草稿层时，正本落位后必须补正本绑定行并声明草稿判定传递方式；②绑定行引用登记用输出件时，该输出件自身须受 S2/S3 保护；③任何「记录值≠现盘实算」（覆盖漂移、回件后追加、行号漂移）禁止静默沿用：四要素登记（旧值、现值、发现方式=实跑命令、影响面），无法归因明写「主体/时点未验」；④聚合指纹必须给出拼接顺序与单件指纹。
- 为什么需要：实例三正本 27172 B 不被验收链任何件锁定；_verify_hy4_out.txt 回件后追加漂移（自报 0614af13/18694 → 现盘 f38adf59…/26210，本会话实算同值；R2BC:100 合规披露「主体/时点未验」）证明输出件登记可被事后污染；聚合无顺序则不可重放。
- 违规实例：DQ 域正本（0a709f2d…/27172）验收链 0 锚；PERF 域唯一被核对象行指向草稿。合规定位：R2BC:100（漂移披露）、A_RESIDUAL_REFERENCES.md:38（PD 行号锚不可沿用）、MATRIX_BINDING_FACTS.md:89-90（聚合模板，本会话复算命中）。

**S5 复核回件与未验显式化（强制；吸收 R6）**
- 条文：①复核回件必须含原文行「被核对象 SHA256 = <64位>，字节数 = <n>」，值为回件会话 hashlib 实算，多件逐件给行；②verdict ∈ {confirmed, partial, refuted}，partial/refuted 一律标 **unconfirmed**，下游文档必须逐条吸收崩点并回标哪条已独立复证、哪条未重放；③未验项单列，「未获得/未重放」不得写成「不存在/未发生」——检索边界不足导出的「全域无 X」结论必须带边界声明；④登记「由回件登记」的事项，下游须核对该回件是否实际存在再引用。
- 为什么需要：本轮全局 verdict = partial，直接推翻了上轮盘点的 4 项全局性表述（§5.2-P1）；「r1 JSON 无佐证」与「验收方回件未获得」都是把「我没搜到/没拿到」写成了「不存在」。
- 违规实例：审计件 §2.1-超纲B、§6-1、§6-4（均 unconfirmed）；对照合规定位 = 本件 §5.2（每条崩点标注本会话验证方式与未重放项）。

### 5.4 本件自身锚（S2 v2 落地自证）

- 本件头部锚行按 S2 生成与校验，命令（本会话实跑，输出见本会话回件）：`python -I -X utf8 D:\Project\ra2-campaign-forge\lead\deliverable_anchor_20261108\_spec2_anchor_check.py fill` / `… check`（同一文件路径）。预期输出 = 「ANCHOR OK (v2)」＋字节数＋锚值，exit=0。
- 本件全文件原样 SHA256（含锚行真值，不等于锚值）不入本件（自指不可计算），由本会话回件登记（§6-4）。
- 本写域本轮新增 3 件：本件、`_spec2_fp_all.py`、`_spec2_anchor_check.py`。既有 4 件零改动。

## 6 结论

1. **instanceCount = 3**（任务书盘点给值；severity = medium）：实例一（版本锚指向被覆盖 r1）成立但锚状态按 P1 修正；实例二（N-11 双件）部分成立；实例三（N-10 双件＋绑定指向登记件）成立（附角色纠正）。三实例的全部分析性结论随前置审计件 **unconfirmed**（复核 verdict = partial）；其中被复核反证的具体子结论（r2 JSON 全域无锚、验收尚未发生、验收方回件未获得、5 件完全无锚、R7 基线、r1 JSON 无佐证）在本件已按 §4/§5.2 改判或加语境。
2. **规范适用范围**：S1–S5 适用于后续 lead/ 写域的新交付件（正本/登记件/回件/输出件/证据件）、双件场景与验收绑定链；不溯及既往——既有件补锚、双件合并、台账登记均属后续轮次，须另获授权。本规范本身不构成对任何技术命题（卡顿/崩溃/安全改动）的放行或改判，纯为文书锚定纪律。
3. **未验项（如实登记，不补造）**：①r1 两件旧值（3343cfbe…/26435、15e4731c…/18045）现盘不可复算（覆盖前状态不存在；重构负结果见 N1_R2_ACCEPTANCE.md:29，过程本会话未重放）；②_verify_hy4_out.txt 追加的主体/时点未验（沿 R2BC:100）；③复核员 P3 的 CRLF 实验未重放（本会话以内存双 canon 实验替代验证语义分裂，见 §5.2）；④审计件「18 件」的成员清单不可重构（§4.4）；⑤编排方【编排方指纹】清单与复核回件的签发过程未验（本件只对现盘值与给值的一致性负责，一致性已 11/11 实算成立）；⑥各件自述的历史实跑（git 状态、mtime 时序）未逐项重放，本件仅对亲自实跑项负责；⑦全域检索跳过的 43 件 >2MB 文件均为二进制（42 png＋1 pkl，扩展名实查），其内容未读。
4. **不代修声明**：本件未修改任何既有交付件、未补写任何既有件绑定行、未删除任何双件、未改台账；唯一写域内仅新增 3 件（本件＋两脚本）；未 commit、未 push；零真机、零采样代码。既有件与规范的差距（交付层 0 自锚、3 正本交付链无锚、双件无自绑）如实留在 §4，留待有权轮次处置。
5. **本件登记（由回件承载）**：本件全文件 SHA256＋字节数由本会话回件登记；件内锚行已按 S2 自锚（§5.4）。写域内本轮新增件的指纹：`_spec2_fp_all.py` = `f8869a486b896ea0d2dd7edd1488a5681818e989680c8daa5cd577cc398bbbab`/4074；`_spec2_anchor_check.py` 见回件（fill 后随本件一并实算登记）。
