# _c97_ §9.7「高档 ≥100ms」四档辖域独立重评报告（2026-11-08）

执行者：辖域重评员 · 本件为独立重评，事实层与辖域层分开表述；不由 PASS 文案自动升格。
铁律遵守：零真机、零采样代码、只读既有件、唯一写域 `lead/c97_scope_recheck_20261108/`、不 commit、不 push。
实跑方式：`python -I -X utf8` + 绝对路径；指纹用 hashlib；主检查脚本 `_c97_check.py`，输出 `_c97_check_out.txt`（SHA256 = 38d5541f8c3ce04afb2be1adde15fe740e50a110138e2fa4fe84514b1a9e2023，字节数 = 7375），stderr 0 字节，EXIT=0。

## 0 被核对象绑定（hashlib 实算）

- 被核对象 SHA256 = 0ebd68dd11a2a54a33e30c6c658d12656fb1af77f14ef4c5724f829d3d90c653，字节数 = 16514（lead/direction_ruling_20261108/RULING_DIRECTION.md）——与编排方指纹 MATCH
- 被核对象 SHA256 = c6fa7a0a3315cdc95bd71916c40c4b565f5066ee2c51ad239d01db5977330316，字节数 = 20942（lead/direction_ruling_20261108/_dr_RULING.md）
- 被核对象 SHA256 = affaeae091178c13935caa283f861799b33358e4a162ece130671bb0ea3468dd，字节数 = 24904（lead/r2_unclosed_cd_20261108/CD_BREAKPOINTS.md）——MATCH
- 被核对象 SHA256 = 4a3424050125b98c0dd3a9a76ec6603fc03ad976e0b9fdecfb34d3b683b94726，字节数 = 48343（lead/dtrigger_compare_20261107/CRITERIA_COMPARE.md）——MATCH
- 被核对象 SHA256 = f0177d2cbafdb4dbd388d6b38b97d14ae73688f36f58df4f0fff7edc31a59b66，字节数 = 5088（lead/dtrigger_compare_20261107/_dtrigger_supplement_out.txt）
- 被核对象 SHA256 = ec64adac558e87e5cdf53563368c7aacea712222e70f303ca85deb83eb08ee3a，字节数 = 23115（lead/dtrigger_round2_20261107/_dC_recompute.py）——MATCH
- 被核对象 SHA256 = a0deb34a4aed83efe3d0b80dfff4f05eb28eeec5fac5613ff49316fd8081337a，字节数 = 13473（lead/dtrigger_round2_20261107/_dC_out.txt）——MATCH

（六件编排方指纹全部 MATCH；supplement 原件与 _dr_RULING.md 为本件另加的核对对象。）

## 1 任务①：上游明列四档的原文依据（不臆造）

**明列处 = `lead/dtrigger_compare_20261107/CRITERIA_COMPARE.md:146`**，本件直读 + 程序化逐名核对（`_c97_check_out.txt:12-21`）：

> 越线事实：`_dtrigger_supplement_out.txt:11-24` 记 C2 未截断族全部触发 >50ms；
> `C2-P95x3` / `C2-P99x3` / `C3-r4/r8` 的补算行触发等待已 ≥100ms（同文件 :12,14,21-22，锚口径见 §3.2）；

（上两行分别是 CRITERIA_COMPARE.md:145 与 :146；「四档」明列在 :146。）

- 四档 = **C2-P95x3、C2-P99x3、C3-r4、C3-r8**。注意原文形态：后两档以斜杠缩写 `` `C3-r4/r8` `` 点名；展开缩写后，对 26 档判据全集逐名核对，:146 恰点名这 4 档、无第五档（`_c97_check_out.txt:16-18`：点名数 26 档口径 = 4，恰为四档集合 = True）。
- :146 同时给出 supplement 行号引用 `:12,14,21-22`，与 supplement 原件四行逐一对应（见 §2）。
- 旁证（本件直读）：`CD_BREAKPOINTS.md:80` 四档分类行「全部触发 ≥100ms | 4 | C2-P95x3(19/19)、C2-P99x3(18/18)、C3-r4(24/24)、C3-r8(16/16)」；`RULING_DIRECTION.md:35` 与 `_dr_RULING.md:96` 均逐名含此四档（程序核对 True，`_c97_check_out.txt:20-21`）。
- 佐证行：`_dtrigger_supplement_out.txt:12/14/21/22` 四行的 ≥100占比 列均为 100.00%（本件亲读 + 解析）。

## 2 任务②：四档辖域下 §9.7 的判定（本件独立实跑，非转引）

从 supplement 原件 `_dtrigger_supplement_out.txt` 表行独立解析（`_c97_check_out.txt:23-29`）：

| 档 | supplement 行 | nTrig | >50 | >=100 | ≥100占比 | ge100==nTrig |
|:--|:--|---:|---:|---:|---:|:--|
| C2-P95x3 | :12 | 19 | 19 | 19 | 100.00% | 是 |
| C2-P99x3 | :14 | 18 | 18 | 18 | 100.00% | 是 |
| C3-r4 | :21 | 24 | 24 | 24 | 100.00% | 是 |
| C3-r8 | :22 | 16 | 16 | 16 | 100.00% | 是 |

**判定：4/4 档全部触发 ≥100ms，§9.7「高档 ≥100ms」在四档辖域内成立。**

**越界指控（四档辖域下）＝ 不成立**：§9.7 后一子句在裁定辖域内与上游登记一致（_dr_RULING.md:96「更正为『断言与上游四档登记一致』」）。

口径边界（如实登记，不扩裁）：

- 13 档按 supplement 原件分类 = **4 全部 / 5 部分 / 4 无行**（`_c97_check_out.txt:31-35`），与 CD_BREAKPOINTS.md:80-82 一致：部分档 C2-P95x2(4/27)、C2-P99x2(1/24)、C2-N16-P95x2(18/45)、C3-r2(148/180)、C3-N16-r2(156/195)；无行档 C2-abs-P95x2、C3-r12、C3-r4-clean、C3-r8-clean。**7/13 档读法下的无支撑档数继续并列保留**，不从四档裁定推成全档 ≥100（_dr_RULING.md:96 明文）。
- 本件交叉对账：`_dC_out.txt` 7b 段 9 行 ↔ supplement 原件逐档（行号+nTrig+>50+>=100）**不一致 = 0**；`_dC_out.txt:80` 13 档名单与本件一致（`_c97_check_out.txt:37-38`）。
- 锚语义：以上均为 S_hat 观测锚下的既有实跑读回（supplement_out.txt:44-45 自报物理 S 不可测），非重算（_dC_out.txt §7g/§8.1 同口径）。

## 3 任务③：语义层缺陷独立评定（不因辖域裁决消失）

**事实层（本件 AST + 直读复证，`_c97_check_out.txt:42-74`）**：

- `all_pass` 门（`_dC_recompute.py:391-401`）：Compare=11、not=5；门内 Name 集合 = A, A_collapse_gt0, A_nf_eq_ideal, A_preempt0, A_recall0, B, B_preempt0, B_preempt0_and_upideal, B_up_eq_ideal, bad_within50, chain_fail, decomp_fail, n_cells, nonneg_fail, probe_bad（+len/all_pass 自身）——**不含 ge100、不含 supp_rows、不含 probe_rows**；
- 全模块含 ge100 的 Compare 节点 = **0**；ge100 仅 :297 赋值、:340 展示；
- :356-369 六处 emit 全为纯字面串（6/6，无插值）；
- :420 `emit("  总判定 = %s" % ("PASS（上述 9.1–9.7 均按本轮实跑成立）" if all_pass else "FAIL"))`——含「9.1–9.7」字面量、以 all_pass 为条件；`_dC_out.txt:148` 已实际输出该 PASS。

**评定：构成「可追溯性缺陷（主）+ 有限语义误导（次）」，不是「可接受」。**

理由：

1. **可追溯性缺陷成立**：总判定行是机器验证的唯一汇总出口。:420 把「9.1–9.7 均成立」整体绑在 all_pass 上，而 all_pass 对 §9.7 的承重子句（≥100ms）没有任何检查项。以 :148 为机器验证凭据的审计者会把「门内未检」误读为「门内已检」——验证链在判定出口断裂。这与 CD_BREAKPOINTS.md:64 对同类 emit 常量串的定性一致：「脚本内未解析/未校验的可追溯性缺陷，非内容虚假」。
2. **语义误导有限（降格理由）**：本实例中该子句在裁定辖域（四档）下数据为真（§2 的 4/4，本件独立证实）；§9.7 文案自带「supplement/probe 中可逐行读回的档」限定与「不是从 _cost_quota_data.json 重算」的证据边界声明；缺陷的危害是「未经门检的断言被 PASS 文案背书」的结构性风险，不是已兑现的假结论。
3. **不判「可接受」**：PASS 文案的证明力恰恰来自门。让文案承担门没有的证明力，等于允许任何后续维护者在不动门的情况下改文案而总判定不变。这是必须修的缺陷（改 :420 文案，或在门内补 §9.7 检查项），但不推翻四档辖域内的实质结论。
4. **辖域独立性**：该缺陷的成立不依赖 4/7/13 档任何一种辖域读法——门内无 §9.7 检查项是脚本静态事实（AST 计数 0）。裁决定调一致（_dr_RULING.md:96「硬编码 PASS 文案及门内不含§9.7的事实不撤销」）。

**severity = medium**：位于判定出口（非注释/非附属文案）故非 low；但裁定辖域内数据为真、上游已登记且明令禁止凭 PASS 文案升格、C 维整体 unconfirmed 使其无法触发下游自动升格，故不至 high。

## 4 任务④：纠正后的表述

§9.7 应改为（辖域显式、逐档计数、口径边界自带的写法）：

> 9.7 「触发等待越线」经既有实跑输出交叉核对（S_hat 锚下界读回，非从 _cost_quota_data.json 重算）：
> ① 71 格涉及的 13 档判据在 metrics_out.txt 中 within50 全为 0.000000；
> ② **上游明列的高档四档**（C2-P95x3、C2-P99x3、C3-r4、C3-r8，CRITERIA_COMPARE.md:146；supplement 行 :12,14,21-22）逐档 nTrig == >=100（19/19、18/18、24/24、16/16），即**该四档全部触发 ≥100ms**；
> ③ 其余 9 档不适用「高档 ≥100ms」表述：5 档部分 ≥100ms（C2-P95x2 4/27、C2-P99x2 1/24、C2-N16-P95x2 18/45、C3-r2 148/180、C3-N16-r2 156/195），4 档 supplement 无行（C2-abs-P95x2、C3-r12、C3-r4-clean、C3-r8-clean；仅 metrics latP50/within50 汇总可读回，中位数不能证「全部触发≥100」）。

即把泛称「高档 ≥100ms」改为「上游明列四档高档判据全部触发 ≥100ms」，并把部分/无行档显式排除。

配套的 :420 修复（二选一，本件不改脚本，仅建议）：

- 文案改为：「PASS（9.1–9.6 门内实跑成立；9.7 为既有输出读回性描述，未设门，见 §8 未验项）」；或
- 门内补 §9.7 检查项：对四档逐一要求 `supp_rows[t]` 存在且 `ge100 == nTrig`，并入库 all_pass。

## 5 任务⑤：升格状态

C 维整体仍 **unconfirmed**。本件只做辖域重评：四档辖域下越界指控不成立、语义层缺陷保留登记；**不改变 R2_FINAL_GRADE 的升格判定，不凭旧 PASS 文案升格**（RULING_DIRECTION.md:31、:35；_dr_RULING.md:90、:96）。

## 6 实跑命令记录（本会话）

1. `python -I -X utf8 -c`（hashlib 对六件编排方指纹对象整读计算 SHA256+bytes）→ 六件全 MATCH
2. `ls` 两目录（定位 supplement 原件）
3. `mkdir -p D:/Project/ra2-campaign-forge/lead/c97_scope_recheck_20261108`
4. `python -I -X utf8 .../_c97_check.py > .../_c97_check_out.txt 2> .../_c97_check_stderr.txt`（第一版：暴露 :146 缩写形态与 :80 冒号匹配两处需修正，如实修正后重跑）
5. 同命令重跑（EXIT=0，stderr=0 字节，out SHA256 = 38d5541f8c3ce04afb2be1adde15fe740e50a110138e2fa4fe84514b1a9e2023，7375 字节）

ranCommands = 5（Bash 计）。

## 7 未验项（单列，不并入结论）

1. supplement 表行数据本身对 1125992 采样点 / 28381 游程原始重放的忠实性：本件只做既有输出读回与解析，未重放语料（铁律禁真机），未验。
2. probe 侧（_dtrigger_probe_out.txt）逐行未在本件重解析：四档 ≥100 断言已由 supplement 单源闭合，probe 仅涉 >50ms 子句（该子句经 7c 在 CD_BREAKPOINTS.md:90 闭合）；本件未重复。
3. `_dC_recompute.py` 的 22 个检查变量中「10 个未入门」的总数口径：本件 AST 实证其承重部分（11 Compare/5 not、ge100 与 supp_rows/probe_rows 均不在门内），22/10 总数转引自 CD_BREAKPOINTS.md:60（其底稿为 _cdreport_check_out.txt:26、:28），本件未逐一重列 22 个变量名。
4. 真机、进程内存、hook/栈采样类证据：铁律禁止，未验。
