# B_BREAKPOINTS_2_6.md —— 维度 B 崩点 2-6 补证交付件（报告撰写员·GLM，2026-11-08）

汇总对象：①补证回件（崩点补证员，2026-11-08）`lead/r2_unclosed_b_20261108/_b_breakpoints_2_6_evidence.md`（SHA256 = e283f2ac78730bde8f36655d0b753c1236bf83a9c47f16ac4e4fb20e62e750f9，字节数 = 14423，本轮 hashlib 实算）＋其 5 个 `_b_` 脚本与 5 份实跑输出；②复核回件（复核员，verdict = **confirmed**）＋其 `_verify_hy4_` 4 件。所有「直读」行号均为本轮撰写员亲读，所有指纹均为本轮 `python -I -X utf8` + hashlib 实算；无法亲证处明确标注引自哪份回件，未验处如实写「未验」，不补造。

## 1 目的与边界（只补证崩点、不选判据）

- **任务来源**：`lead/criteria_r3_verify_20261108/R2_BREAKPOINTS_CLOSURE.md:74`（直读）登记维度 B 五项「未核未闭合」崩点：崩点 2 evidence 指纹串损坏（`_verify_B_out.txt:64-66`）、崩点 3 自检硬编码（`_dB_anchor_recompute.py:401-413`）、崩点 4 `+e>50` 空列零判别力、崩点 5 「统一锚」是选择非推导（runStart 敏感性 C2-abs-P95x2 → 27/4/27，`_verify_B_out.txt:48`）、崩点 6 og=None 答非所问（`_dB_anchor_recompute_out.txt:31-39`）；`:115` 未验项清单第 2 条同列此五项。
- **边界（铁律，全文有效）**：本件只补证崩点事实——**不选判据、不改口径 B、不改 `STALL_EVENT_DEFINITION.md:177/:190/:191`、不改台账**；零真机、零采样代码（无进程启动/终止、无内存读取、无探针注入）；未 commit、未 push（本轮 `git rev-parse HEAD` = 26574589aa8401e8f3f2934680a1ea7109bafa2d）；唯一写域 = `lead/r2_unclosed_b_20261108/`（本轮 `ls` 实查：既有 16 件均为 `_b_`/`_verify_` 前缀件，本件新增仅 `B_BREAKPOINTS_2_6.md`）。
- **判定词口径（如实登记，不重定义）**：「闭合」= 该崩点的两问/指控已被实跑或实读直接回答且证据链完整；「部分闭合」= 部分子项已实判、部分子项**未验**；「未验」= 拿不到实跑命令+输出或文件:行证据，不补造。

## 2 崩点2（evidence 指纹串损坏）——**部分闭合**（未闭合残留：损坏成因）

**三行原文（本轮 Read `lead/dtrigger_round2_20261107/_verify_B_out.txt:64-66` 直读；该件 SHA256 = 4ee6a6b78d80a336c3431a6f71d9f5a77fec93ef65b7a4c642a49b669368c107，字节数 = 7229，本轮实算）**：

- `:64` 「[交叉校验 F] 回件 evidence 中的 _dB_ 指纹字符串是否与实际吻合」
- `:65` 「回件称脚本 hash 尾=26f3fb61829756dfeecf；实算脚本 hash 含该尾? False；该尾出现在 data.json? False」
- `:66` 「回件称 out.txt hash 尾=b6f95763794；实算 out.txt hash 含该尾? False；该尾出现在 data.json? True」

与 `R2_BREAKPOINTS_CLOSURE.md:74` 转述逐句相符（直读）。

**三相关文件实算指纹（本轮 `python -I -X utf8 -c` + hashlib 实算；补证轮 `_b_fp_core_out.txt:1-3`、复核轮 `_verify_hy4_fp_out.txt:2-25` 两轮独立实算同值，与编排方指纹全部 MATCH）**：

| 文件（lead/dtrigger_round2_20261107/） | SHA256 | 字节 | 本轮实算 |
|:--|:--|--:|:--|
| `_dB_anchor_recompute.py` | 44b10371cdc258e7db5c232f53d9d64dfdf4f34cb084115d0bb8c7a05a5a382b | 27324 | MATCH |
| `_dB_anchor_recompute_out.txt` | 3e9588ce1def2ebc5b9ad77a3ce242b47bcada4ae1ab1bc4ea606775edd40807 | 14479 | MATCH |
| `_dB_anchor_recompute_data.json` | 8fb149f21e9b41d7c808e8f8c2e1cb35ca62b881ebe65bfba7029b6f95763794 | 42910 | MATCH |

**尾串归属判定（实算）**：

- `b6f95763794`：不在 `_dB_anchor_recompute_out.txt` 摘要中，恰为 `data.json` 摘要 `pos=53`、`sha[-11:]`（`_b_fp_core_out.txt:18` 直读 endswith=True；复核轮 `_verify_hy4_fp_out.txt:34-40` 独立实算 `sha[-11:]==True、sha[-12:]==False`）——**是末 11 位**；`CRITERIA_ROUND2.md:75`「尾 12 位被混入」系误计（直读，经 textgrep 输出）。
- `26f3fb61829756dfeecf`：在三件任一摘要中均不存在（`_b_fp_core_out.txt:13-15`）。
- **全树猎尾**：补证轮 `_b_tail_hunt_out.txt:1-5`（lead/ 全树+根一级散件 4352 件）——`26f3fb…` 摘要命中 **0** 件、`b6f95763794` 摘要命中**恰好 1** 件 = `_dB_anchor_recompute_data.json`；复核轮独立实现 `_verify_hy4_checks_out.txt:1-5`（4378 件，件数差=写域随轮次增长）同判 0/1、唯一命中同件。
- **字面检索**：`_b_textgrep_out.txt`（3272 文本件）与复核独立分类（`_verify_hy4_checks_out.txt:26-31`）一致：`26f3fb61829756dfeecf` 写域外既有件 5 处字面命中 = `R2_BREAKPOINTS_CLOSURE.md:74`（登记转述）、`CRITERIA_ROUND2.md:75`（登记转述）、`_verify_B_out.txt:65`、`_verify_B_recompute.py:315`（复核常量 `ev_script_tail`，直读 :315-316 成对还有 `ev_out_tail`）、`_verify_B_stdout.txt:65`——全是转述/登记/复核常量，**调查 B 回件 evidence 原文不在盘上**。
- **需更正的次要瑕疵（复核指出，不改判定）**：补证回件 §1 称该串「仅出现于 `_verify_B_recompute.py:315` 及其输出件」，「仅」字与上述 5 处既有命中（含两处台账登记文本）矛盾，属措辞过度收缩；因其均非 evidence 原文，「回件原文不在盘上」与成因未验的结论不倒。
- **损坏成因**：**未验**。回件原文不在盘上、所称脚本尾 4352/4378 件全树零摘要命中，无法区分「转抄了被覆盖的旧版脚本指纹」与「转写错误」。

**判定：部分闭合**——尾串归属已实判（b6f95763794=data.json 末 11 位、全树唯一；26f3fb… 无任何盘上摘要对应物），指纹串损坏事实成立；**成因未定位（未验）**。

## 3 崩点3（自检硬编码）——**闭合**；崩点4（+e>50 空列）——**闭合**

### 3a 崩点3：`_dB_anchor_recompute.py:401-413` 自检硬编码

- **直读 `:400-413`**：`:401-406` `probe_expect` 字典把四档期望值写成**字面元组**（`C2-abs-P95x2=(29,66.334,70.931,321.002)`、`C3-r4=(24,125.884,127.491,440.389)`、`C3-r8=(16,251.709,256.261,258.378)`、`C3-r12=(15,377.385,387.990)`——直读原文为 385.601/387.990 两中位/最大值）；`:407-413` 用本轮 `RESULTS` 与这批字面常量比对（容差 0.002，`:409-410`）。
- **期望值来源实判（补证轮实跑 `_b_probe_expect.py` → `_b_probe_expect_out.txt:1-20`，本轮直读）**：四组字面值与主探针 `_dtrigger_probe_out.txt` 首次出现行 `:136/:138`、`:147/:149`、`:158/:160`、`:169/:171` **逐值相等 = True**——字面常量是对既有探针落盘记录的**转抄（冻结先验）**，非本轮从语料推导。（如实披露：该脚本首跑把 C3-r12 误配到 :235/:237 后段同名行，系补证员解析 bug，改取首次出现后重跑，两次均留痕。）
- **脚本读件普查（补证轮 grep + 复核轮独立 grep，引两回件）**：全脚本仅读 measure_w*.json（:160）、manifest（:173）、events（:182）、CRITERIA_METRICS.json（:381）；`_dtrigger_probe_out.txt` 只出现在 UPSTREAM 指纹清单 :117、于 :150-152 仅作 `sha()` 哈希、**内容从不解析**。故自检 (2) = 「自己本轮重算结果 vs 自己写死常量」。
- **能自证**：本轮重算的 4 个 lastEdge id 的 wait 分布与冻结探针记录一致（能抓本轮重算漂移与转抄笔误）。**不能自证**：探针记录本身或共享锚定义假设的正确性（两侧同源，一致≠各自为真）；2 个 runStart 档不在 `probe_expect` 内；`>=100`/`+e>50` 两列不在该检查范围（只核 n/min/med/max）。

**判定：闭合**——「是否写死期望值」= 是（:401-406 字面直读）；「是否从实际计算结果推导」= 否（期望侧为转抄常量、比对侧为本轮实算）；能/不能自证范围已逐项列明。

### 3b 崩点4：`+e>50` 「空列」

- **列非空（补证轮实跑 `_b_data_cells.py` → `_b_data_cells_out.txt`，本轮直读 :8-24）**：data.json `cells` 六档 `nGt50PlusE` 全为整数 29/24/24/16/16/15，判定行（:22）「全为整数=True、任一 None=False、任一缺失=False」。直读 `_dB_anchor_recompute_out.txt:50-55` 主表 +e>50 列同值实值；逐格明细 `:59-87`（「+e>50 = 29/29」等 + wait 有序表）；§六表 `:137-144` 同值。**「空列占位」字面读法不成立。**
- **独立重算（`_b_data_cells_out.txt:10-20`）**：由 `trigger_details` 逐触发 wait 数组（行样例 :6 `{"wait": 75.840…, "og": 2.5169…}`）重算，+e>50 在 e=0 与 e=2.510999999 两种取法下、≥100（5/24/24/16/16/15）均与 cells 逐档全等；复核轮独立解析 `_verify_hy4_checks_out.txt:8-15` 同判（「6/6恒等+重算全等=True」）。
- **零判别力属实**：min(wait) = 66.334/125.884/128.284/251.709/254.247/377.385，六档全 >50 ⇒ 6/6 档 +e>50 == nTrig == nGt50（>50 列，eq 标志全 True）——该列被 min(wait)>50 结构性决定，与 >50 列零差异。原始登记 `CRITERIA_ROUND2.md:77`（textgrep 输出直读）的实义即「恒等、零判别力（50−66.334=−16.334ms）」且「>=100 五档恒等、仅 C2-abs-P95x2 5/29 有区分」——与重算一致；R2 登记行的「空列」二字面不成立，特此更正登记。

**判定：闭合**——两问均已实答：列**有实际数值**（两轮两件皆可复算复现），且该列**退化恒等、零判别力**属实。

## 4 崩点5（「统一锚」是选择非推导）——**闭合**；崩点6（og=None 答非所问）——**部分闭合**

### 4a 崩点5：口径 U1 = 选择，非推导

- **直读 `_dB_anchor_recompute_out.txt:44-46`**：U1 =「id 权威谓词锚」；`:129`：「本轮『统一』的准确含义：一条统一规则（每个 id 取其权威登记的锚）无例外地施加于全部 6 个 id 与全部 12 格」。
- **U1 的全部依据是登记本身**：直读脚本 `:14-18`——「取 `_dtrigger_metrics.py` 为该 id 登记的锚……依据：_dtrigger_metrics.py:217,223,224,225,226,227 与 CRITERIA_METRICS.json 各 id 的 "note" 字段」。直读 `_dtrigger_metrics.py:217`（`"上一帧沿锚;近64条P95*2"`）与 `:223-227`（C3-r4=lastEdge、C3-r4-clean=runStart、C3-r8=lastEdge、C3-r8-clean=runStart、C3-r12=lastEdge）——**锚是登记行 note 字符串里的定义参数**，非从语料推导的量。
- **选择有实质后果、数据不能定夺（直读 `_dB_anchor_recompute_out.txt:115-128`）**：全 runStart 敏感性表给出 C2-abs-P95x2 → 27/4/27（vs U1 主表 :50 = 29/5/29）、C3-r12 waitMed 387.348 vs 385.601；`:128` 拒绝该读法的理由是「会替换 4 个 id 的触发集，与 CRITERIA_METRICS.json 及主探针已落账的 id 定义不符」——**取舍准则是「与登记一致」（约定自洽），不是任何从数据/物理推出的必然**；敏感性证明选择改变结果（29/5/29 ↔ 27/4/27）。`_verify_B_out.txt:47-53`（复核轮直读引）同值。
- **佐证**：主探针 `_dtrigger_probe_out.txt` 档位清单（17 档）中无 `C3-r4-clean`/`C3-r8-clean` 独立行（补证轮 grep 0 命中；复核轮独立证实）——两 `-clean` 档的 wait 分布依赖 U1 约定下的重算，`CRITERIA_ROUND2.md:78`「非独立同 id 实测」属实。

**判定：闭合**——U1 = 纯选择（内容=镜像权威登记；理由=与落账定义一致）；无任何推导程序存在；敏感性证明该选择改变结果。

### 4b 崩点6：og=None 论证与「§3.2 为何未验」正交

- **§3.2 未验的真实原因（直读 `lead/dtrigger_compare_20261107/CRITERIA_COMPARE.md:242-252`）**：`:245-246` C2-abs-P95x2 的 ≥100/+e>50 未验 = 补算表 :15 曾误标 + 主探针 `:132-141` 未算该两列；`:247-250` C3-r4/r8/r12 未验 = **锚不一致**（`_dtrigger_metrics.py:223-227` 定义上一帧沿锚 vs `_dtrigger_supplement.py:106-118` f_rate 恒 runStart——直读 supplement.py `:115` `el = (ts[idx] - ts[r[2]]) * 1000.0`，补算表 :21-22 与主探针 :43-45 不同源）；`:251` C3-r4-clean/r8-clean 三列全未验 = 补算表无独立行；`:252` 全触发 wait 中位与仅真实命中 latP50 两母体不可互换。**真实原因 = 锚不一致（+误标+缺行+母体），不是 og=None。**
- **og=None 论证内容（直读 `_dB_anchor_recompute_out.txt:31-39`、`:146`）**：`:33` 自认「og=None 且 he>=64 的游程 n=0（i==0 ⇒ he=0，故必为 0）」——**结构恒真式属实**（`CRITERIA_ROUND2.md:79` 原登记同义，textgrep 输出直读）。
- **U6 归因错置属实**：`:146` 称「4 个 lastEdge id 与 2 个 runStart id 都在 U6 下直接不触发」；但直读脚本 `:252` `if he < N_HIST or (anchor == "lastEdge" and og is None):   # U6`、`:257` `off = og if anchor == "lastEdge" else 0.0`——runStart 档仅由 `he<64` 拦下，og 不进 runStart 谓词。`CRITERIA_ROUND2.md:79` 第二半句属实。
- **「答非所问」的边界**：og=None 论证回答的是「格子可否补算」，作为对「§3.2 为何未验」的解释不切题（此义上成立）。**但**落盘件并未把 og=None 呈现为未验解释：`:39` 自标「此事实须作为限制单列」、`:146` 标题即「结构性理由说明」，且对锚错配有独立正面定量定位（`:127`「这是 §3.2 标签/锚错配的定量定位」）——R2 的转述形式（「拿 og=None 解释未验」）在落盘件中**无文本支持**。另 `CRITERIA_ROUND2.md:70`（textgrep 输出直读）记录：og=None 之问来自调查 B 任务 what 的框架，而复核 grep「不可补算」全件 0 命中；**该框架由谁/为何如此措辞：未验**（任务史，非本轮可判，不选判据）。

**判定：部分闭合**——真实原因（锚不一致等）已实读锁定；恒真式与 U6 归因错置两子指控属实；「把 og=None 冒充为 §3.2 未验的解释」无文本支持；「任务框架来源」未验。

## 5 复核回件（verdict = confirmed）与五项闭合状态汇总表

**复核方式**：复核员未复用补证员 5 个 `_b_` 脚本，另写 `_verify_hy4_fp.py`/`_verify_hy4_checks.py` 独立实现等价检查（指纹核验 + 全树摘要猎尾 + data.json 独立解析 + probe_expect 独立比对 + 字面出现分类），共 14 条实跑命令；未跑真机/采样；其 4 个核验件均落本写域。全树 mtime 全量扫描因超时中止，改用 targeted mtime + git diff 替代（复核回件如实登记）。

**复核绑定行（原文照录）**：「被核对象 SHA256 = bf426786db82c34dd6b6d21e3022678285e3e22f52dbdaa5085d85c3b6f8fbde，字节数 = 22351（我本轮 python -I -X utf8 + hashlib 独立实算，编排方指纹 MATCH）」——被核对象 = `lead/criteria_r3_verify_20261108/R2_BREAKPOINTS_CLOSURE.md`。**本轮撰写员第三次实算**（`python -I -X utf8 -c` + hashlib）：该件连同 `_dB_` 三件、`_verify_B_out.txt`（7229）、`CRITERIA_COMPARE.md`（48343）、补证回件本体（14423）共 7 件 **SHA256+字节数全部 MATCH**。

**复核分项结论（①–⑦ 全部通过）**：① 指纹 6 件 MATCH、独立猎尾 0/1 同判、末 11 位实算成立；② probe_expect 字面值独立正则提取后与探针记录四组逐值相等=True；③ data.json 独立解析六档重算全等、min>50 六档成立；④ U1 选择非推导、敏感性同值证实；⑤ 真实原因非 og=None、恒真式与归因错置属实、无文本支持成立；⑥ closedCount=3 无拔高（部分闭合均显式列未验项，未升格）；⑦ 铁律实查通过（`_b_*.py` 全部无采样类调用 NO_MATCH；三处只读域 MM 件 mtime 早于本轮且会话起始快照已列为 MM，非本轮所改；HEAD 未动、未 commit/push）。**verdict = confirmed**（非 refuted/partial，不标 unconfirmed）。复核另指出一处需更正的次要瑕疵（§2 已录入：「仅」字措辞与 5 处既有字面命中矛盾）与一件数差异（4352 vs 4378，写域随轮次增长），均不改判定。

**五项闭合状态汇总表**：

| 崩点 | 判定 | 核心证据（实跑/实读） | 未验残留 |
|:--|:--|:--|:--|
| 崩点2 指纹串损坏 | **部分闭合（未闭合）** | 三行原文直读（`_verify_B_out.txt:64-66`）；三件指纹三轮实算 MATCH；b6f95763794=data.json 末 11 位、全树唯一命中；26f3fb… 摘要 0 命中、字面仅存于转述/登记/复核常量 | 损坏成因（evidence 原文不在盘上，无法定位） |
| 崩点3 自检硬编码 | **闭合** | `:401-406` 字面元组直读；四组字面值与主探针落盘记录逐值相等实跑证实；脚本读件普查 + UPSTREAM 只哈希不解析 | —（能/不能自证范围已列明） |
| 崩点4 +e>50 空列 | **闭合** | cells 六档 nGt50PlusE 全整数、无 None 无缺失；trigger_details 独立重算全等；min(wait) 六档全>50 ⇒ 列退化恒等、零判别力属实 | —（「空列」字面已更正登记） |
| 崩点5 统一锚选择 | **闭合** | U1 依据=登记行与 note 字段（metrics.py:217/:223-227 直读）；敏感性 29/5/29 ↔ 27/4/27；主探针无 -clean 独立行（grep 0 命中） | — |
| 崩点6 og=None 答非所问 | **部分闭合（未闭合）** | 真实原因=锚不一致等（CRITERIA_COMPARE.md:242-252 直读 + supplement.py:115 直读）；恒真式（out.txt:33）与 U6 归因错置（脚本 :252/:257 对照 :146）属实 | 「og=None 任务框架由谁/为何插入」 |

**closedCount = 3**（崩点 3、4、5 闭合；崩点 2、6 部分闭合即未闭合）。

## 6 结论（closedCount、可升格判定、未验项、不选判据声明）

- **closedCount = 3**：崩点3（自检硬编码）、崩点4（+e>50 空列）、崩点5（统一锚选择）闭合；崩点2（指纹串损坏）、崩点6（og=None 答非所问）部分闭合（未闭合）。复核 verdict = confirmed，判定无拔高。
- **可升格判定**：本件**不选判据**，不作出维度升格裁决。登记事实：`R2_BREAKPOINTS_CLOSURE.md:106` 既有判定为「维度 B 部分闭合……不可升格」；本轮补证使崩点3/4/5 由「未核未闭合」变为「闭合」，崩点2/6 仍留未验子项（崩点2 成因、崩点6 任务框架来源）。五项现状是否满足升格判据、:106 判定是否变更，归编排方/台账决定，本件只提供事实。
- **未验项清单（如实登记，不补造）**：
  1. 崩点2 损坏成因：回件自称脚本尾 `26f3fb61829756dfeecf` 的来源——全树摘要 0 命中、evidence 原文不在盘上（无法区分旧版指纹被覆盖 vs 转写错误）。
  2. 全树猎尾/字面检索的 scope = lead/ 全树 + 仓库根一级散件；lead/ 之外范围未扫（回件所涉件均在 lead/ 内）。
  3. 崩点6：`CRITERIA_ROUND2.md:70` 所记「og=None 任务框架」由谁/为何插入——任务史，非本轮可判。
  4. 复核侧：未重跑补证员 5 个 `_b_` 脚本（以独立实现等价检查代替）；全树 mtime 全量扫描中止（改 targeted mtime + git diff）。补证侧：`_b_probe_expect.py` 首跑解析 bug 已修复重跑、两次留痕。
- **不选判据声明**：本件及所汇总的补证/复核两轮全程**不选判据、不改口径 B、不改 `STALL_EVENT_DEFINITION.md:177/:190/:191`、不改台账**；未 commit、未 push；零真机、零采样代码；判定词（闭合/部分闭合/未验）均按实跑命令+输出或文件:行证据如实登记，未把未闭合写成闭合，未伪造任何通过。
