# C97_SCOPE_RECHECK —— C 维 §9.7「高档 ≥100ms」四档辖域独立重评 · 最终交付（2026-11-08）

撰写：重评报告撰写员·GLM。本件是辖域重评链的末端交付件：材料 = 重评回件（辖域重评员，verdict4=不成立、wordingDefectStands=true、severity=medium）+ 复核回件（verdict=**confirmed**，未发现断点）。本件不重做裁决、不改判、**不升格**，只把已闭合的「辖域重评」与「语义缺陷」两个分离结论如实落盘成文，并给出全程 hashlib 指纹绑定。

铁律遵守（本件全链）：零真机（未启动 gamemd.exe / ra2loader / YURI.exe、不 taskkill、不读活进程内存）；零采样代码（无 hook / MiniDump / SuspendThread / StackWalk / 探针注入、无 ctypes / OpenProcess / ReadProcessMemory）；只读既有件（ra2youli/**、out/re_work/**、lead/GOAL_*、lead/PENDING_DECISIONS.md、lead/re_line_20261105/**、lead/dtrigger_*/**、lead/*_20261108/** 零改动）；唯一写域 = `lead/c97_scope_recheck_20261108/`；不 commit、不 push。实跑一律 `python -I -X utf8` + 绝对路径，指纹用 hashlib。

## 1 目的与边界（只做辖域重评、不升格）

- **目的**：对 C 维 §9.7「高档 ≥100ms」子句，在裁决给出的**四档辖域**内做独立重评，把两个分开的结论落盘：①「越界」指控在四档辖域下**不成立**（§3）；② `:420` PASS 文案硬编码的**语义缺陷**不因辖域裁决消失（§4）。二者分离表述，不由前者掩盖后者，也不由后者推翻前者。
- **辖域来源（裁决原文，本件直读）**：`lead/direction_ruling_20261108/RULING_DIRECTION.md:35`——「**C：** ≥100ms 子句辖域取上游明列四档 C2-P95x3、C2-P99x3、C3-r4、C3-r8。四档范围内越界指控不成立；纠正转述后可独立重评，**不凭旧 PASS 文案升格**」。底稿 `lead/direction_ruling_20261108/_dr_RULING.md:96` 同口径并加：「硬编码 PASS 文案及门内不含§9.7的事实不撤销」。
- **边界（不做什么）**：
  - **不升格**：C 维整体仍 **unconfirmed**（R2_FINAL_GRADE.md:139 汇总行、:149 逐维结论，本件直读）；本件不改 R2_FINAL_GRADE、不改台账、不凭 PASS 文案升格（RULING_DIRECTION.md:31「原四维继续 unconfirmed，不直接升格」、:35；_dr_RULING.md:90「保留 R2 原四维 unconfirmed、promotable=0/4」、:96）。
  - **不改口径与脚本**：不选判据、不改口径 B、不改 STALL_EVENT_DEFINITION.md :177/:190/:191、不改台账；`_dC_recompute.py`（被检脚本）与本件工具 `_c97_check.py` 均零写入——本件对 `_c97_check.py` 的精化静态核查：文件写入类 API（`.write(`/`json.dump`/`mkdir`/`shutil` 等）命中 = 0（grep 退出码 1），危险 API（ctypes/OpenProcess/ReadProcessMemory/SuspendThread/MiniDump/StackWalk/psutil/gamemd/ra2loader/YURI）命中 = 0。
  - **不扩裁**：13 档读法下的 4 全部 / 5 部分 / 4 无行分类并列保留，不从四档裁定推成全档 ≥100（_dr_RULING.md:96 明文「7/13档的部分≥100和无行记录继续保留，不从该裁定推成全档≥100」）。

## 2 「上游明列四档」的原文依据与四档定义

**明列处 = `lead/dtrigger_compare_20261107/CRITERIA_COMPARE.md:146`**（本件直读，含上行 :145）：

> :145 越线事实：`_dtrigger_supplement_out.txt:11-24` 记 C2 未截断族全部触发 >50ms；
> :146 `C2-P95x3` / `C2-P99x3` / `C3-r4/r8` 的补算行触发等待已 ≥100ms（同文件 :12,14,21-22，锚口径见 §3.2）；

- **四档定义** = **C2-P95x3、C2-P99x3、C3-r4、C3-r8**，分别锚定 supplement 原件 `_dtrigger_supplement_out.txt` 行 :12、:14、:21、:22（:146 自带行号引用）。
- **原文形态注意**：:146 的后两档以斜杠缩写 `` `C3-r4/r8` `` 点名。展开缩写后对 26 档判据全集逐名核对，恰点名这 4 档、无第五档——本件重跑 `_c97_check.py` 复现（`_c97_check_out.txt:16-18`：展开后 13 档口径与 26 档全集口径点名数均 = 4、「恰为四档集合 = True」）；复核轮改用权威源 `CRITERIA_METRICS.json`（顶层 31 键 = 26 判据 + 5 个 R/U 项）独立重核：原始 :146 点名 3 档、展开后恰 4 档无第五档（`_verify_counts.py` C 段，本件重跑复现，见 §5.2）。
- **裁决书逐名旁证**（`_c97_check_out.txt:19-21`，本件复现）：:146 内 supplement 行号引用「:12,14,21-22」在场 = True；`RULING_DIRECTION.md:35` 含四档逐名 = True；`_dr_RULING.md:96` 含四档逐名 = True（两处均本件直读确认）。
- **上游台账旁证**（本件直读）：`CD_BREAKPOINTS.md:80` 四档分类行「全部触发 ≥100ms | 4 | C2-P95x3(19/19)、C2-P99x3(18/18)、C3-r4(24/24)、C3-r8(16/16)」。

## 3 四档辖域下的越界成立性判定（四档各自 nTrig/ge100 实证）

数据源 = supplement 原件 `_dtrigger_supplement_out.txt` 表行（本件直读核对，非转引；`_c97_check_out.txt:25-29` 程序化解析同值）：

| 档 | supplement 行 | nTrig | >50 | >=100 | ≥100占比 | ge100==nTrig |
|:--|:--|---:|---:|---:|---:|:--|
| C2-P95x3 | :12 | 19 | 19 | 19 | 100.00% | 是 |
| C2-P99x3 | :14 | 18 | 18 | 18 | 100.00% | 是 |
| C3-r4 | :21 | 24 | 24 | 24 | 100.00% | 是 |
| C3-r8 | :22 | 16 | 16 | 16 | 100.00% | 是 |

- **判定：4/4 档 ge100==nTrig，§9.7「高档 ≥100ms」在四档辖域内成立**（`_c97_check_out.txt:29`「4/4 档 ge100==nTrig … = True」；本件重跑该脚本 diff=IDENTICAL，见 §5.2 命令 2；复核 `_verify_counts.py` B 段独立解析 supplement 23 行同值）。
- **越界指控（四档辖域下）＝ 不成立（verdict4 = 不成立）**：§9.7 后一子句在裁定辖域内与上游登记一致（_dr_RULING.md:96「四档全部达到阈值，故该辖域内『越界成立』指控不成立；更正为『断言与上游四档登记一致』」）。
- **对账与口径边界（如实登记，不扩裁）**：
  - `_dC_out.txt` 7b 段（:96-109，四档对应 :99/:101/:106/:108）↔ supplement 原件逐档对账不一致 = 0（`_c97_check_out.txt:37`；复核 `_verify_counts.py` E 段 9 行可解析、逐档不一致 = 0，本件重跑复现）。
  - 13 档分类 = **4 全部 / 5 部分 / 4 无行**（`_c97_check_out.txt:31-35`），与 CD_BREAKPOINTS.md:80-82 直读一致：部分档 C2-P95x2(4/27)、C2-P99x2(1/24)、C2-N16-P95x2(18/45)、C3-r2(148/180)、C3-N16-r2(156/195)；无行档 C2-abs-P95x2、C3-r12、C3-r4-clean、C3-r8-clean。**7/13 档读法下的无支撑档数继续并列保留**。
  - 锚口径：以上均为 S_hat 观测锚下界读回——supplement :44-45 自报物理起点 S「无法从语料测得……只能给观测锚 S_hat 下的实测值，作为下界」（本件直读；`_verify_counts.py` F 段同证）；「>=100」列为「触发等待已达/越过口径B 100ms 事后分类门槛」（supplement :35 列说明，本件直读）。非重算、非物理 S 严格核算。

## 4 ★ 语义层缺陷的独立评定（:420 PASS 文案硬编码不因辖域裁决消失）

**事实层（AST + 直读；`_c97_check_out.txt:42-74`；本件直读 `_dC_recompute.py:391-401` 与 :417-420 复核；复核 `_verify_ast.py` 自写遍历独立实证，本件重跑复现）**：

- `all_pass` 门 = `_dC_recompute.py:391-401`（本件直读全文）：**Compare=11、not=5**；门内 Name 集合 17 名 = A, A_collapse_gt0, A_nf_eq_ideal, A_preempt0, A_recall0, B, B_preempt0, B_preempt0_and_upideal, B_up_eq_ideal, all_pass, bad_within50, chain_fail, decomp_fail, len, n_cells, nonneg_fail, probe_bad —— **不含 ge100、不含 supp_rows、不含 probe_rows**（`_c97_check_out.txt:43-45`；`_verify_ast.py`「ge100/supp_rows/probe_rows 在门内 = False False False」）。
- 全模块含 ge100 的 Compare 节点 = **0**；ge100 仅 :296-297 解析赋值（keyword 形态）、:338-340 emit 展示（字符串下标形态）（`_c97_check_out.txt:46、:51-57`；`_verify_ast.py` dump 法 0 命中、Name 命中无、keyword 命中 :296）。
- 全模块无任何 `if` 条件含 supp_rows / probe_rows / ge100（`_verify_ast.py` 三项均「无」）。
- :420（本件直读）`emit("  总判定 = %s" % ("PASS（上述 9.1–9.7 均按本轮实跑成立）" if all_pass else "FAIL"))` —— 文案常量含「9.1–9.7」、IfExp 条件 = Name(all_pass)；`_dC_out.txt:148` 已实际输出「总判定 = PASS（上述 9.1–9.7 均按本轮实跑成立）」（本件直读；`_verify_counts.py` G 段同证）。

**评定：语义缺陷成立，定级「可追溯性缺陷（主）+ 有限语义误导（次）」，不可判「可接受」，severity = medium。** 理由（承重于重评回件 §3 与复核回件 ③，本件逐条核对无减损）：

1. **可追溯性缺陷（主）**：总判定行是机器验证的唯一汇总出口。:420 把「9.1–9.7 均成立」整体绑在不含 §9.7 承重子句（≥100ms）任何检查项的 all_pass 上；以 :148 为机器验证凭据的审计者会把「门内未检」误读为「门内已检」——验证链在判定出口断裂。与 CD_BREAKPOINTS.md:61（「部分通过也输出 PASS」的结构性可能成立且本次运行已实际兑现）与 :64（emit 常量串属「脚本内未解析/未校验的可追溯性缺陷，非内容虚假」）同口径。
2. **有限语义误导（次，降格理由）**：本实例中该子句在裁定辖域（四档）下数据为真（§3 的 4/4，本件独立复现）；§9.7 文案自带证据边界声明（_dC_out.txt:147「但这是既有输出的读回，不是从 _cost_quota_data.json 重算」）。危害是「未经门检的断言被 PASS 文案背书」的结构性风险，不是已兑现的假结论。
3. **不判「可接受」**：PASS 文案的证明力来自门；让文案承担门没有的证明力，等于允许后续维护者在不动门的情况下改文案而总判定不变。
4. **辖域独立性（本节要点）**：门内无 §9.7 检查项是脚本静态事实（含 ge100 的 Compare 节点 AST 计数 = 0），不依赖 4/7/13 档任何辖域读法；裁决本身明文不撤销该事实（_dr_RULING.md:96）。即：**四档辖域裁决只消灭「越界指控」，不消灭「PASS 文案硬编码」这一语义缺陷**——复核回件 ③ 原话「辖域裁决未被用来掩盖语义缺陷」。

**severity = medium 的定位**：位于判定出口（非注释/非附属文案）故非 low；裁定辖域内数据为真、上游已登记、明令禁止凭 PASS 文案升格、C 维整体 unconfirmed 使其无法触发下游自动升格，故不至 high。

## 5 复核回件（含 SHA256 加字节数绑定）+ 纠正后表述建议

### 5.1 复核回件转录与绑定

- **复核 verdict = confirmed（未发现断点，重评回件五项任务全部经复核独立复现成立）**。回件全文转录本落盘 `_review_reply_transcript.json`：被核对象 SHA256 = 91d1317f28b12285588155016542281da3eb43239b9787f8a6e2b106d26b2f33，字节数 = 4481（本件 hashlib 实算 + JSON 可解析校验；UTF-8 无 BOM 无尾换行。若编排方存档字节有异，以本转录本与 §5.2 交付件三哈希为准）。
- **被核对象（重评回件）转录本 `_verify_reply.json`**（复核轮产物）：被核对象 SHA256 = 1fe6b1b6160e218703627ce91d449e76452060cfe52b6cc5c3c8fbac04ded62f，字节数 = 4034（本件 hashlib 实算 MATCH，§5.2 命令 1）；本件解析其字段 = verdict4「不成立」、wordingDefectStands=True、severity=medium、ranCommands=5，与重评回件一致。如实登记一处形态细节：该回件 evidence 字段对输出件自报为缩写形态「out SHA256=38d5541f…2023/7375B」（本件解析确认），故对 evidence 做 64 位全哈希子串检索会失配；全哈希以 §5.2 交付件实算绑定为准，不构成矛盾。
- **复核回件要点（如实转录，全文见转录本）**：① CRITERIA_COMPARE.md:146 原文与重评引用逐字一致、斜杠缩写属实，CRITERIA_METRICS.json 权威源重核恰 4 档无第五档；② 四档计数 19/19(:12)、18/18(:14)、24/24(:21)、16/16(:22) 独立复现；③ ★辖域裁决未被用来掩盖语义缺陷（AST 独立实证 all_pass 门 Compare=11/not=5、门内 17 名不含 ge100/supp_rows/probe_rows、含 ge100 的 Compare=0、:420 以 all_pass 为条件、_dC_out.txt:148 已实际输出；wordingDefectStands=true、severity=medium 保留）；④⑤ 无升格无越写（R2_FINAL_GRADE.md 指纹与编排方一致未动；核验件全落本写域）。
- **复核登记的微瑕三条（复核自评「不动摇」，本件如实转录）**：(a) 重评回件把「22 个检查变量中 10 个未入门」转引 CD_BREAKPOINTS.md:60，该总数实印于 :59、:60 承载的是承重的「ge100 完全无门」部分（本件直读确认：:59 =「22 个检查型变量中 10 个 NOT in gate」、:60 =「『高档 ≥100ms』完全无门」；:58 的门定义 11 比较项 + 5 not 与 AST 计数一致）；(b) PENDING_DECISIONS.md mtime=2026-11-08 22:26:42 早于重评轮写域活动（22:31-22:33），时间线归编排方裁决登记轮、非被核轮所改，归属超出可完全证实范围、如实登记（本件 stat 复算同值，§5.2）；(c) `_c97_check.py` 将 FULL26/THIRTEEN 硬编码而非派生（本件 grep 确认 ：49 FULL26、:46 THIRTEEN），复核已分别对照 CRITERIA_METRICS.json 26 判据键集与 _dC_out.txt:80 实文验证集合全等，不构成循环论证。

### 5.2 本件指纹绑定与复现命令（hashlib 实算，`_report_fp.py` 输出）

**六件编排方指纹全 MATCH**：

| 对象 | SHA256 | 字节数 | 判定 |
|:--|:--|:--|:--|
| lead/direction_ruling_20261108/RULING_DIRECTION.md | 0ebd68dd11a2a54a33e30c6c658d12656fb1af77f14ef4c5724f829d3d90c653 | 16514 | MATCH |
| lead/r2_unclosed_cd_20261108/CD_BREAKPOINTS.md | affaeae091178c13935caa283f861799b33358e4a162ece130671bb0ea3468dd | 24904 | MATCH |
| lead/dtrigger_compare_20261107/CRITERIA_COMPARE.md | 4a3424050125b98c0dd3a9a76ec6603fc03ad976e0b9fdecfb34d3b683b94726 | 48343 | MATCH |
| lead/dtrigger_round2_20261107/_dC_recompute.py | ec64adac558e87e5cdf53563368c7aacea712222e70f303ca85deb83eb08ee3a | 23115 | MATCH |
| lead/dtrigger_round2_20261107/_dC_out.txt | a0deb34a4aed83efe3d0b80dfff4f05eb28eeec5fac5613ff49316fd8081337a | 13473 | MATCH |
| lead/r2_final_grade_20261108/R2_FINAL_GRADE.md | 7ce09812f7bd905a95114a2cc2cea56b3dc3dbaef3d8e0d14c58685762ecab24 | 30140 | MATCH |

另加核对对象（与重评自报一致）：_dr_RULING.md = c6fa7a0a3315cdc95bd71916c40c4b565f5066ee2c51ad239d01db5977330316/20942B；supplement 原件 _dtrigger_supplement_out.txt = f0177d2cbafdb4dbd388d6b38b97d14ae73688f36f58df4f0fff7edc31a59b66/5088B。

**重评三交付件**（复核 sha256Line 绑定与本件实算一致）：_c97_scope_recheck.md = ee7b3a167c9d99301474a59036cc5cc47c81bfe933cfbd653991b0d1d59ac0b1/10995B；_c97_check.py = 059aba6218c13e68a0d34d467d913fca33e47b0550aff7dcc0fe44f106c193ff/10698B；_c97_check_out.txt = 38d5541f8c3ce04afb2be1adde15fe740e50a110138e2fa4fe84514b1a9e2023/7375B；重评 stderr = e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855/0B。

**复核轮核验件**：_verify_reply.json = 1fe6b1b6160e218703627ce91d449e76452060cfe52b6cc5c3c8fbac04ded62f/4034B；_verify_fp.py = 4bd7701623c0cd10cc0780792c13f5caf8d4210be3c68a9ed5554256a66b3b7c/1445B；_verify_counts.py = bb5c4b28d586822a491fb78d698765612dede2782c82c77bec6ceabbb6c1c6c4/5422B；_verify_ast.py = bc682f9da698212034cea2cd85c4920a8f276e03fb8021b126ffd168d1ec1af9/3993B。

**本件撰写轮产物**：_report_fp.py = b8f95166d8408e7663fcff6a6f99ceb09a25648d6de410a5254008a68fc6e672/4969B；_review_reply_transcript.json = 91d1317f28b12285588155016542281da3eb43239b9787f8a6e2b106d26b2f33/4481B；_c97_rerun_out.txt（与 _c97_check_out.txt diff=IDENTICAL，故同哈希 38d5541f…2023/7375B）与 _c97_rerun_stderr.txt（0 字节）。

**本件实跑命令记录（Bash 计 7）**：
1. `python -I -X utf8 -c`（hashlib 对 _report_fp.py 自绑定）
2. `python -I -X utf8 D:/Project/ra2-campaign-forge/lead/c97_scope_recheck_20261108/_report_fp.py`（16 对象 SHA256+bytes + 3 项 mtime → 六件编排方指纹全 MATCH、全部带期望值条目全 MATCH）
3. `python -I -X utf8 …/_c97_check.py > …/_c97_rerun_out.txt 2> …/_c97_rerun_stderr.txt; echo PY_EXIT=$?; diff …/_c97_check_out.txt …/_c97_rerun_out.txt` → PY_EXIT=0、stderr 0B、**RERUN_DIFF=IDENTICAL**（重评结论可复现）
4. `python -I -X utf8 -c`（解析 _verify_reply.json：字段值 + evidence 缩写形态核验）
5. `python -I -X utf8 …/_verify_counts.py`、`python -I -X utf8 …/_verify_ast.py`（复核轮两件独立复算件在本件重跑，EXIT=0，结论逐项复现：§2/§3/§4 全部数字与布尔）
6. `grep`（_c97_check.py 写入类 API=0 命中、危险 API=0 命中、FULL26/THIRTEEN 在 :49/:46；R2_FINAL_GRADE.md 维度 C 行定位）
7. `ls -la`（写域与 lead/dtrigger_round2_20261107/、lead/direction_ruling_20261108/ 清点）＋ heredoc `python -I -X utf8 -`（转录本归一+绑定）

mtime 佐证（os.stat，_report_fp.py 输出）：R2_FINAL_GRADE.md = 2026-11-08 17:36:55、GOAL_THREE_TARGETS_20261018.md = 2026-11-06 06:53:04、PENDING_DECISIONS.md = 2026-11-08 22:26:42——均早于重评轮写域活动（写域件 22:31-22:33），重评/复核/撰写三轮均未动台账与终评件。

### 5.3 纠正后表述建议（重评任务④；仅建议，本件不改脚本、不改台账、不选判据）

§9.7 应改为（辖域显式、逐档计数、口径边界自带的写法）：

> 9.7 「触发等待越线」经既有实跑输出交叉核对（S_hat 锚下界读回，非从 _cost_quota_data.json 重算）：
> ① 71 格涉及的 13 档判据在 metrics_out.txt 中 within50 全为 0.000000；
> ② **上游明列的高档四档**（C2-P95x3、C2-P99x3、C3-r4、C3-r8，CRITERIA_COMPARE.md:146；supplement 行 :12,14,21-22）逐档 nTrig == >=100（19/19、18/18、24/24、16/16），即**该四档全部触发 ≥100ms**；
> ③ 其余 9 档不适用「高档 ≥100ms」表述：5 档部分 ≥100ms（C2-P95x2 4/27、C2-P99x2 1/24、C2-N16-P95x2 18/45、C3-r2 148/180、C3-N16-r2 156/195），4 档 supplement 无行（C2-abs-P95x2、C3-r12、C3-r4-clean、C3-r8-clean；仅 metrics latP50/within50 汇总可读回，中位数不能证「全部触发≥100」）。

即把泛称「高档 ≥100ms」改为「**上游明列四档高档判据全部触发 ≥100ms**」，并把 5 部分档与 4 无行档显式排除。

配套的 `_dC_recompute.py:420` 修复（二选一，仅建议、不改脚本）：
- 文案改为：「PASS（9.1–9.6 门内实跑成立；9.7 为既有输出读回性描述，未设门，见 §8 未验项）」；或
- 门内补 §9.7 检查项：对四档逐一要求 `supp_rows[t]` 存在且 `ge100 == nTrig`，并入库 all_pass。

## 6 结论

- **verdict4 = 不成立**：「高档 ≥100ms」越界指控在裁决四档辖域（C2-P95x3、C2-P99x3、C3-r4、C3-r8）下不成立——四档 ge100==nTrig = 19/19、18/18、24/24、16/16（4/4，§3 实证），§9.7 在该辖域内与上游登记一致。
- **wordingDefectStands = true，severity = medium**：`_dC_recompute.py:420` PASS 文案硬编码的语义缺陷（可追溯性缺陷为主 + 有限语义误导为次）**不因辖域裁决消失**，不可判「可接受」（§4）；修复建议见 §5.3，本件不改脚本。
- **复核 verdict 如实记 = confirmed**：复核未发现断点、五项任务独立复现成立；该 verdict 只覆盖「重评回件复现」，不构成对 C 维整体的肯定，更不构成升格依据。复核登记微瑕三条（:59/:60 行号、PENDING_DECISIONS mtime 归属、FULL26/THIRTEEN 硬编码）已转录并经本件抽查（§5.1）。
- **C 维整体仍 unconfirmed（不升格声明）**：本件只做辖域重评，不改变 R2_FINAL_GRADE 的升格判定（维度 C 汇总行 :139「**unconfirmed**｜否」、逐维结论 :149），promotable=0/4 维持（R2_FINAL_GRADE.md:142/:146）；不凭旧 PASS 文案升格、不凭本次 confirmed 复核升格（RULING_DIRECTION.md:31、:35；_dr_RULING.md:90、:96）。
- **未验项（单列，不并入结论）**：
  1. supplement 表行数据对 1125992 采样点 / 28381 游程原始重放的忠实性——禁真机未重放，未验（重评自列、复核同列、本件同）。
  2. probe 侧（_dtrigger_probe_out.txt）逐行未在本链重解析——四档 ≥100 已由 supplement 单源闭合，>50 子句经 7c 闭合（_dC_out.txt:124 主表 PASS）；本件未重复。
  3. 「22 个检查变量中 10 个未入门」总数转引 CD_BREAKPOINTS.md:59（复核微瑕 a 纠正后的行号），本链未逐一重列 22 个变量名；其承重部分（门 = 11 比较 + 5 not、ge100/supp_rows/probe_rows 均不在门内）已由 AST 实证闭合。
  4. PENDING_DECISIONS.md mtime 的时间线归属（微瑕 b）超出本链可完全证实范围，如实登记。
  5. 回件/转录本 JSON 的哈希绑定基于逐字节转录（本件 _review_reply_transcript.json、复核轮 _verify_reply.json）；存档字节若异，以 §5.2 交付件实算三哈希为准。
  6. 真机、进程内存、hook/栈采样类证据：铁律禁止，未验。

（本件自身 SHA256/字节数不在本件内登记——自引用不成立；以编排方对本落盘件 `lead/c97_scope_recheck_20261108/C97_SCOPE_RECHECK.md` 的 hashlib 实算为准。核验工具：`python -I -X utf8 D:/Project/ra2-campaign-forge/lead/c97_scope_recheck_20261108/_report_fp.py`。）
