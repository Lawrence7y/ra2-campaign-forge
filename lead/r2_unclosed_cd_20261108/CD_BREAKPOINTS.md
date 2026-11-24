# CD_BREAKPOINTS.md —— 四项崩点（C 崩点1/2 + D 独立证成/硬阻断解除条件）补证报告

撰写者：补证报告撰写员·GLM。日期 2026-11-08。
被核对象链：`lead/criteria_r3_verify_20261108/R2_BREAKPOINTS_CLOSURE.md`（SHA256 = bf426786db82c34dd6b6d21e3022678285e3e22f52dbdaa5085d85c3b6f8fbde，字节数 = 22351，本件 hashlib 实算，`_cdreport_check_out.txt:16`）登记的四项未闭合崩点（:81-82 C 证据链两项、:90-94/:108/:115 D 两项）→ 补证回件 `lead/r2_unclosed_cd_20261108/_cd_verdict.md`（**被核对象 SHA256 = 2b51dfe9c1cacaec631b7df92d53aa7db0a4ad6ce0a8e732cdacff3043557338，字节数 = 14604**，本件 hashlib 实算同值，`_cdreport_check_out.txt:19`）→ 复核回件（verdict = **partial**，ranCommands = 15，回件 JSON 转引；其落盘输出 `_verify_cd_out.txt` SHA256 = 11e4b0ff9684ee0102d7b2e811c79a8d04c21dd31d856da130724cfa3f4fc475 / 21874，`_cdreport_check_out.txt:20`）。

**本件实跑清单（全部 `python -I -X utf8` + 绝对路径，指纹用 hashlib）**：
- Bash 5 轮：①写域 `ls -la`；②编排方 6 项指纹批算（逐位 match）；③写域 7 件指纹批算（含 `_cd_check_err.txt`/`_verify_cd_err.txt` = 0 字节）；④`CRITERIA_ROUND2.md:98/:387` 读行；⑤主核验脚本实跑 `python -I -X utf8 D:/Project/ra2-campaign-forge/lead/r2_unclosed_cd_20261108/_cdreport_check.py > _cdreport_check_out.txt 2> _cdreport_check_err.txt` —— **EXIT=0，stdout 7802 字节，stderr 0 字节**。
- 文件直读 10 件（Read 工具）：`_cd_verdict.md`、`R2_BREAKPOINTS_CLOSURE.md`、`_dC_recompute.py`（:280-429）、`_dC_out.txt`（:70-152）、`_dD_check.py`（:78-141）、`_dD_PHYSICAL_S_ALIGNMENT.md`（:100-139）、`_dD_align_out.txt`（:20-89）、`_cd_check_out.txt`（全文）、`_verify_cd_out.txt`（全文）、`_cdreport_check_out.txt`（全文）。
- 证据分层标注：(i) **本件实跑** = `_cdreport_check_out.txt`（行号引用）；(ii) **本件直读**既有落盘件（文件:行）；(iii) **转引**补证/复核回件（凡本件追不到的标「未验」）。

## 1 目的与边界（只补证崩点、不选判据）

- **目的**：把四项崩点的补证事实与复核结论汇编成一份可追责的崩点事实报告——每条判定追到「实跑命令+输出」或「文件:行」；只如实写闭合状态，不选判据、不改口径、不补造。
- **边界（铁律）**：零真机（不启动任何游戏可执行件、不结束任何活进程、不读活进程内存）；零采样代码（不写任何 hook / 转储 / 线程挂起 / 栈回溯 / 探针注入 / 动态解析类代码）；只读既有件一律不改（本件对被读文件仅 open 读）；不改 `STALL_EVENT_DEFINITION.md:177/:190/:191`（本件实读 :177/:190/:191 当前原文与补证记录逐字一致，`_cdreport_check_out.txt:74-76`；该件 mtime = 2026-11-06T16:03:30，早于补证落盘窗口 2026-11-08 14:24~14:37，`_cdreport_check_out.txt:77`）；不改台账（`GOAL_THREE_TARGETS_20261018.md` mtime = 2026-11-06T06:53:04、`PENDING_DECISIONS.md` mtime = 2026-11-07T13:58:51，均早于本轮，`_cdreport_check_out.txt:78-79`）；不 commit、不 push；唯一写域 = `lead/r2_unclosed_cd_20261108/`（本件新增 `CD_BREAKPOINTS.md` + `_cdreport_check.py` / `_cdreport_check_out.txt` / `_cdreport_check_err.txt`）。
- **不裁事项（预先声明）**：§9.7「高档」辖域（括注 7 档 / 13 档 / 上游 4 档）= `CRITERIA_ROUND2.md:98/:387` 已登记的待裁决项②，本件只并列各读法下的数字，不裁定（不选判据）；probe:171 行级证据口径是否统一，同样不裁。

## 2 C 崩点1：emit 常量串（:356-368 原文 + all_pass 门覆盖判定）

登记处：`R2_BREAKPOINTS_CLOSURE.md:81`「`_dC_recompute.py:356-368` emit 常量串、all_pass 门不含子断言（崩点 1）」。

**(a) 被指行段原文（本件直读 `lead/dtrigger_round2_20261107/_dC_recompute.py:356-369`，逐字照录；登记写「:356-368」，实际 7h 的最后一个字面片段落在 :369）**：

```python
356	        emit("  7c-2 probe 细部行：C2-P95x3:106, C2-P99x3:128, C3-r4:150, C3-r8:161, C3-r12:172 "
357	             "均为 nTriggersBeyond50ms=nTrig/nTrig (100.00%)（_dtrigger_probe_out.txt 既有实跑文本）")
358	        emit("  7d 判据 -clean 变体（C3-r4-clean / C3-r8-clean）在 supplement/probe 无独立明细行；"
359	             "仅 metrics_out.txt:28,30 的 latP50=347.249/259.514ms 与 within50=0.000000 可读回。")
360	        emit("  7e C3-r12 特例：metrics_out.txt:31 因 realHits=0 记 latP50=0.000ms（非「不越线」）；"
361	             "probe_out.txt:171-172 记 15/15 >50ms、min=377.385ms、med=385.601ms。")
362	        emit("  7f 门槛定义：STALL_EVENT_DEFINITION.md:190 端到端 <50ms；:191 累积判定 >=100ms 不合格；"
363	             "RULING_D30.md:26,52 不得以等待 P95 突破牺牲时间约束。")
364	        emit("  7g 口径边界（如实登记）：supplement_out.txt:44-45 明写物理起点 S 不可测，"
365	             "现有 waitAfterS_hat 只是下界；因此「越线」为 S_hat 锚下的实测结论，"
366	             "不是相对物理 S 的严格核算。")
367	        emit("  7h 锚语义差异：C2-abs-P95x2 / C3-r4 / r8 / r12 主探针为「上一帧沿锚」，"
368	             "C3-r4-clean / r8-clean 与 C3-r2 为 runStart 锚（metrics_out.txt:21,26-31 的 note 列）；"
369	             "两组延迟数值不可直接互比，但均在 >50ms 一侧。")
```

**(b) emit 字面性判定（AST）**：:356-:369 区间 emit 共 6 处（7c-2/7d/7e/7f/7g/7h，行 356/358/360/362/364/367），**纯字面串 6/6、含插值/格式化 0**（本件实跑 `_cdreport_check_out.txt:23`；补证 `_cd_check_out.txt:21-36`；复核独立复现 `_verify_cd_out.txt:53-59`）。对照：逐检 PASS/FAIL 与数值行是按结果生成的插值（如 `_dC_recompute.py:330/:354`），故该段 6 处属「证据链文字硬编码」而非全部输出硬编码。

**(c) all_pass 门覆盖判定**。门定义原文（`_dC_recompute.py:391-401` 直读）：

```python
391	all_pass = (
392	    n_cells == 156
393	    and not decomp_fail and not nonneg_fail and not chain_fail
394	    and len(A) == 54 and len(B) == 102 and len(A) + len(B) == 156
395	    and len(A_nf_eq_ideal) == 54 and len(A_recall0) == 54 and len(A_preempt0) == 0
396	    and len(A_collapse_gt0) == 54
397	    and len(B_preempt0) == 71 and len(B_preempt0_and_upideal) == 71
398	    and len(B_up_eq_ideal) == 73
399	    and not bad_within50
400	    and not probe_bad
401	)
```

- 门 = **11 个比较项**（n_cells==156、len(A)==54、len(B)==102、len(A)+len(B)==156、len(A_nf_eq_ideal)==54、len(A_recall0)==54、len(A_preempt0)==0、len(A_collapse_gt0)==54、len(B_preempt0)==71、len(B_preempt0_and_upideal)==71、len(B_up_eq_ideal)==73）+ 5 个 `not` 否定项（`_cdreport_check_out.txt:24`；`_cd_check_out.txt:37-50`；`_verify_cd_out.txt:60-72`）。
- 22 个检查型变量中 **10 个 NOT in gate**：`cap_eq_ideal`、`A_cap_eq_up`、`A_up_eq_ideal`、`A_maxloss_eq`、`B_upideal_but_preempt_gt0`、`B_preempt0_recall_gt0`、`B_nf_eq_ideal`、`B_recall0`、`named_set`、`not_named`（本件实跑 `_cdreport_check_out.txt:25`；`_cd_check_out.txt:51-73`）。复核细分（本件采信）：其中仅 5 个（A_cap_eq_up / A_up_eq_ideal / A_maxloss_eq / B_preempt0_recall_gt0 / B_upideal_but_preempt_gt0）真正被写进 §9.3–§9.5 作结论断言，另 5 个是 §3/§6 只 emit 数字的展示计数（`_verify_cd_out.txt:73-75`）——补证回件把 10 个笼统称「遗漏的数值断言」略夸大，不动摇崩点。
- **「高档 ≥100ms」完全无门**：`ge100` 全脚本仅 2 处出现 = :297（解析赋值 `ge100=int(f0[8])`）、:340（emit 展示），含 ge100 的比较运算全模块 AST 计数 = **0**（本件实跑 `_cdreport_check_out.txt:26`；`_cd_check_out.txt:74-76`）；7b supplement「全部越 50ms」逐行 emit 亦无聚合变量入 all_pass（all_pass 引用中 supp/7b 相关名 = 无，`_cdreport_check_out.txt:28`；`_cd_check_out.txt:78-79`）。
- **总判定 PASS 分支文案硬编码**：`_dC_recompute.py:420` `emit("  总判定 = %s" % ("PASS（上述 9.1–9.7 均按本轮实跑成立）" if all_pass else "FAIL"))`（本件实跑读回 `_cdreport_check_out.txt:27`）——文案宣称 9.1–9.7 全部成立，而 §9.7 后一子句无门。**「部分通过也输出 PASS」的结构性可能成立，且本次运行已实际兑现**：`_dC_out.txt:148` 输出 `总判定 = PASS（上述 9.1–9.7 均按本轮实跑成立）`，而 §9.7「高档 ≥100ms」子句数据仅部分支撑（见 §3）。
- 被门遗漏的其余数值断言本次实查恰好全真（`_dC_out.txt:37/:46/:54-57/:72-73`；7b 九行与 supplement 原件逐档全等，`_cdreport_check_out.txt:35`）。

**(d) 常量串内容直读核对（可追溯性）**：6 处字面串的内容与被引文件相符——probe:106/128/150/161/172 均为「nTriggersBeyond50ms=n/n (100.00%)」、probe:171 `min=377.385 med=385.601`（`_cd_check_out.txt:113-118`；probe:171 本件独立读回 `_cdreport_check_out.txt:36`）；stall_def:190/:191（`_cd_check_out.txt:129-130`，与本件实读 `_cdreport_check_out.txt:75-76` 一致）；ruling_d30:52（`_cd_check_out.txt:133`）；supp:44-45（`_cd_check_out.txt:161-162`）。**即 emit 常量串问题属「脚本内未解析/未校验的可追溯性缺陷」，非内容虚假。**

**崩点1 判定：闭合**（补证与复核对事实层无分歧；崩点属实）。

## 3 C 崩点2：§9.7「高档 ≥100ms」越界（13 档实算 ≥100ms 档数）

登记处：`R2_BREAKPOINTS_CLOSURE.md:81`「§9.7『高档 ≥100ms』13 档仅 4 档全部≥100（崩点 2）」；`CRITERIA_ROUND2.md:98`（本件实读：复核独立解析 supplement 得 13 档中仅 4 档全部触发 ≥100ms、5 档部分、4 档无行，「本件不裁定这一口径冲突」）与 `:387` 待裁决项②（本件实读）。

**§9.7 原文**（`_dC_out.txt:147`，= 脚本 `_dC_recompute.py:417-419` 的输出；`CRITERIA_ROUND2.md` 本身无 §9.7 节）：

> 9.7 「触发等待越线」经既有实跑输出交叉核对：71 格涉及的 13 档判据在 metrics_out.txt 中 within50 全为 0.000000；supplement/probe 中可逐行读回的档全部触发 >50ms、**高档 ≥100ms**；但这是既有输出的读回，不是从 _cost_quota_data.json 重算。

后一子句「高档 ≥100ms」**无「可逐行读回」限定词**。13 档名单（`_dC_out.txt:80`）与实算（本件独立实跑，双源：supplement 原件解析 + `_dC_out.txt` 7b 段，`_cdreport_check_out.txt:31-35`）：

| 分类 | 档数 | 明细（ge100/nTrig） |
|:--|:--|:--|
| 全部触发 ≥100ms | **4** | C2-P95x3(19/19)、C2-P99x3(18/18)、C3-r4(24/24)、C3-r8(16/16) |
| 部分 ≥100ms | **5** | C2-N16-P95x2(18/45)、C2-P95x2(4/27)、C2-P99x2(1/24)、C3-N16-r2(156/195)、C3-r2(148/180) |
| supplement 无行 | **4** | C2-abs-P95x2、C3-r12、C3-r4-clean、C3-r8-clean |

7b 表 ↔ supplement 原件逐档对账（nTrig/gt50/ge100）**不一致 = 0**（`_cdreport_check_out.txt:35`；`_cd_check_out.txt:86-103`；`_verify_cd_out.txt:97`）。与 `CRITERIA_ROUND2.md:98` 登记一致。

**各辖域读法下的无行级支撑档数（本件不裁，只并列）**：
- **7 档读法**（脚本 `:39-42` NAMED_HIGH = C2-P95x3/C2-P99x3/C3-r4/C3-r4-clean/C3-r8/C3-r8-clean/C3-r12；§9.6 `_dC_out.txt:146`）：C3-r4-clean / C3-r8-clean 在 supplement/probe 均无独立明细行（`_dC_out.txt:126` 7d：仅 metrics latP50=347.249/259.514ms 中位数与 within50=0.000000 可读回——中位数不能证「全部触发≥100」）→ **2/7 无支撑**（C3-r12 以 probe:171 `min=377.385ms` 记行级支撑，本件读回 `_cdreport_check_out.txt:36`）。
- **13 档读法**：补证记 **9/13** 无支撑（`_cd_verdict.md:50`）；复核保持同一 probe 口径（probe:171 同样给 C3-r12 优待）独立实算 **8/13**（`_verify_cd_out.txt:102`）——差 1 档 = 补证在 7 档读法用了 probe:171、13 档读法未用，属未声明的口径切换。两数并列登记，本件不裁。
- **4 档读法**（复核发现的第三种有上游明文的读法）：`CRITERIA_COMPARE.md:146` 原文（本件直读，`_cdreport_check_out.txt:37`）：「`C2-P95x3` / `C2-P99x3` / `C3-r4/r8` 的补算行触发等待已 ≥100ms（同文件 :12,14,21-22，锚口径见 §3.2）」——上游本就把「≥100ms」限定在恰这 4 档，而这 4 档恰全部 ge100==nTrig → **该读法下无支撑 = 0/4，「越界」不成立**（`_verify_cd_out.txt:100/:107-112`）。§9.7 的「可逐行读回的档」措辞与该读法相容。
- 前一子句「可逐行读回的档全部触发 >50ms」为真（7b 九行 + 7c 八行全部越 50ms；probe 主表 >50=nTrig 且 100.00% 列，`_cd_check_out.txt:119-127`）。

**崩点2 判定：事实层闭合、「越界成立→崩点闭合」为辖域条件性（unconfirmed）**。4/5/4 计数与双源对账三方一致、已证；但「把部分/无行写成已验」的成立与否取决于待裁决项②的辖域归属（4 档读法下不成立、7 档读法下 2/7、13 档读法下 8/13 或 9/13）。补证判「越界判定：成立」（`_cd_verdict.md:50`）并记闭合，复核认定该闭合被拔高（verdict = partial 的主因）——本件按复核口径记：**闭合依赖待裁决项②，未完全闭合**。

## 4 D 独立证成与硬阻断解除条件（B3/B4 computed=0 + O1–O5 可验收性）

登记处：`R2_BREAKPOINTS_CLOSURE.md:90-94`（「独立证成」强度主张崩塌 / 解除条件未验）、:108/:115。

### 4.1 D 独立证成（崩点3）

- **B3/B4 computed=0 独立复现（AST）**：`_dD_check.py` B3 块（:114-125）out() 调用 **computed=0 / literal=12**；B4 块（:128-137）**computed=0 / literal=10**；对照 B1（:82-94）computed=2/literal=6、B2（:97-112）computed=3/literal=5 为实算块（本件实跑 `_cdreport_check_out.txt:40-43`；补证 `_cd_check_out.txt:136-139`；复核 `_verify_cd_out.txt:115-118`；与 `_verify_D_out3.txt:7-10` T3 同值）。B3/B4 全部为字面文字，例如 B3 的核心句原文（`_dD_check.py:120-121` 直读）：
  > (iii) 反向不等式（不合规方向的独立证成）：若某触发的 C-S_hat > 50ms，则 C-S > 50ms。
  > 该结论不依赖 S 的精确值；_dtrigger_supplement_out.txt:11-24,29 给出观测锚下已 >50ms 的触发数，
- **D 未复算逐档越线数（grep + 源码直读）**：`_dD_check.py` 仅 :121 一处提及 supplement（纯文字引用）；`_dD_align.py` 命中 3 处含「supplement」的行——:66 为 FPS 指纹清单中的路径串（本件实读 :55-74，FPS = 指纹文件列表定义，`_cdreport_check_out.txt:50-70`）、:348/:362 为纯文字 out()（本件实跑 `_cdreport_check_out.txt:44-49`）——**两脚本解析/重算 supplement 表行的代码行 = 0**（`_verify_cd_out.txt:127`）。
- **剩余支撑三层（量化）**：①逻辑层：不等式 (iii)（C−S ≥ C−S_hat > 50 ⟹ C−S > 50）有效但平凡，无需计算即成立；②母体层：D 自算 e>0=28317/28317（`_dD_align_out.txt:29`）、U>50ms=56（:41）、逐事件 U⊂A 相等 1677/1677（:47-48）、d_final>=100=1704/1681（:50）——只支撑「观测锚为严格下界」的母体前提，不支撑任何逐档越线计数；③数据层：逐档越线计数全部来自外部单源读回（supp:11-24,29 原文相符，`_cd_check_out.txt:148-158`；上游 `CRITERIA_COMPARE.md:34-35,145-147` 原文相符，`_cd_check_out.txt:163-168`）。
- **崩点3 判定：闭合**——「独立于 S」的推理方向站立；但「独立证成」作为「由 D 自身确定性计算独立证成」不成立，强度降为「有效平凡逻辑 + 母体级自算旁证 + 单源外部读回」，非归零。复核独立复现、无异议。

### 4.2 D 硬阻断解除条件（崩点4）

- **O1–O5 非纯名称列表**：`_dD_PHYSICAL_S_ALIGNMENT.md:124-130` 直读——每项含名称+口径定义+精度要求；O1 须与 S_hat 逐事件配对、保留区间校验 S∈(S_low,S_hat]、覆盖声明母体（:126）；O2 与 O1 一一配对（:127）；O3 残差 ≤1ms 且「若不满足则 C−S 不可判定，P 不闭合」（:128）；O4 缺失数=0、归属误配数=0（:129）；O5 条件项+覆盖母体显式声明（:130）。另有充分性主张（:132）：「O1–O4 到位后，逐事件直接计算 C−S 并与 50 ms 比较即可闭合 P」。复核程序化计数：时间分辨率×3、不确定度上界×2、逐事件×5、配对×2、覆盖×4、缺失数×1、误配数×1、残差上界×1、断档数×1、充分性×1（`_verify_cd_out.txt:146-157`）。
- **但「可验收的解除条件」未完全确证，三缺口（本件实算/直读证实）**：
  1. **必要性是纯断言**：:122「逐项必要性见 `_dD_check_out.txt:46-55`」指向的 B4 块 computed=0/literal=10——「缺一则不可闭合」为逐行文字，无构造性证明或反例计算（`_cd_check_out.txt:185-186`）。
  2. **O1 精度括注算术不一致（本件实算）**：:126 原文「时间分辨率 ≤ 1 ms；逐事件不确定度上界 ≤ 1 ms（合计 ≤ :177 的 50 ms 预算的 2%，且 ≤ :190 的 20 ms 安全裕量）」——求和读法 1ms+1ms=2ms，2/50 = **4.0%**，与所写「2%」矛盾；仅单项 1/50 = 2.0%；2/20 = 10.0%（本件实跑 `_cdreport_check_out.txt:73`；复核同值 `_verify_cd_out.txt:142-143`）。
  3. **验收程序缺席且未执行**：:134 纪律声明「只列观测量名称、口径与精度要求；不含任何获取手段…本轮**未获取任何新观测量**」——清单定义「观测什么、到什么精度」，未定义「如何获取/由谁核验 ≤1ms 上界」；解除条件本身未被执行（无新观测量落盘）。
- **崩点4 判定：部分闭合（未闭合）**——清单形态达标（非纯名称列表），但必要性纯断言、括注算术矛盾、验收程序缺席三缺口在案。

## 5 复核回件（含 SHA256 加字节数绑定）+ 四项闭合状态汇总表

- **复核 verdict = partial**（如实记录；按「refuted 或 partial 标 unconfirmed」规则，本补证链整体标 **unconfirmed**）。ranCommands = 15（回件 JSON 转引）；主核验 = `python -I -X utf8 .../_verify_cd.py`（EXIT=0，stdout 21874 字节，stderr 0 字节，`_verify_cd_out.txt` 指纹见文首）。
- **绑定**：**被核对象 SHA256 = 2b51dfe9c1cacaec631b7df92d53aa7db0a4ad6ce0a8e732cdacff3043557338，字节数 = 14604**（被核对象 = 落盘回件主体 `lead/r2_unclosed_cd_20261108/_cd_verdict.md`；本件 hashlib 实算同值，`_cdreport_check_out.txt:19`）。注：编排方内联的补证回件 JSON 文本**未落盘为任何磁盘文件**——本件 grep『四项崩点补证完成』over lead/ 命中 3 处均为核验脚本自身引用搜索串（`_cdreport_check.py` / `_verify_cd.py` / `_verify_cd_out.txt`，`_cdreport_check_out.txt:82`），复核全仓 grep 同向（`_verify_cd_out.txt:42-43`）→ 无指纹实体可算，按铁律记**未验**、不补造。
- **指纹核查**：编排方 6 项指纹本件 hashlib 实算全部逐位 match（含 `_dD_align_out.txt` = 4fd5a8a1…/9088，本件实算 `_cdreport_check_out.txt:10`）；补证自报 3 项产出 + 复核自报 2 项产出指纹本件实算全部 match（`_cdreport_check_out.txt:17-20`）；`_cd_check_err.txt` = 0 字节属实。
- **复核登记的瑕疵（本件核实采纳）**：
  1. closedCount=3/4 有拔高——崩点②闭合依赖待裁决项②（§3 已述）。
  2. 9/13 依赖未声明的口径切换，统一 probe:171 口径下为 8/13（§3 已述）。
  3. 补证 evidence 把 `_dD_align_out.txt` 指纹列为「本轮 hashlib 实算」，但 `_cd_check.py` 的 P 字典（14 键）与 `_cd_check_out.txt` §0 的 14 行输出均无该项（`_verify_cd_out.txt:45-50`；本件实读 `_cd_check_out.txt:5-18` 同证）——该值只能来自题给指纹抄录，属来源归属夸大；**值本身**本件独立实算 match，非内容虚假。
  4. 「10 个未入门变量」中仅 5 个为真结论断言（§2 已述）。
  5. 铁律合规复核通过：`_cd_check.py` 的 open() 全为 "r"/"rb"、唯一写入 sys.stdout（`_verify_cd_out.txt:171-175`）；禁词扫描命中 0（`_verify_cd_out.txt:168-170`）；只读件 mtime 均早于补证窗口（`_verify_cd_out.txt:176-184`）。
- **四项闭合状态汇总表**：

| # | 崩点 | 补证判定（`_cd_verdict.md`） | 复核判定 | 本件记法（最终状态） | 关键依据 |
|:--|:--|:--|:--|:--|:--|
| 1 | C emit 常量串 + all_pass 门 | 闭合 | 复现；仅「10 变量」表述略夸大 | **闭合** | 6/6 字面（`_cdreport_check_out.txt:23`）、11 比较项+10 变量未入门（:24-25）、ge100 无比较（:26）、:420 PASS 文案硬编码（:27）、部分通过输出 PASS 已兑现于 §9.7 子句（`_dC_out.txt:148`） |
| 2 | C §9.7「高档 ≥100ms」 | 闭合（越界成立；辖域不裁） | partial 主因：条件性 | **事实层闭合；「越界成立」条件性（unconfirmed，待裁决项②）** | 13 档 4/5/4（`_cdreport_check_out.txt:32-34`）、双源对账=0（:35）、compare:146 4 档读法下 0/4（:37）、8/13 vs 9/13（`_verify_cd_out.txt:102`） |
| 3 | D 独立证成 | 闭合（崩塌属实） | 复现，无异议 | **闭合** | B3/B4 computed=0/literal 12/10（`_cdreport_check_out.txt:42-43`）、D 无 supplement 表行解析（:44-49）、剩余支撑=平凡逻辑+母体旁证+单源读回（`_dD_align_out.txt:29/:41/:47-50`） |
| 4 | D 硬阻断解除条件 | 部分闭合 | 复现 | **部分闭合（未闭合）** | O1–O5 含谓词非纯名称列表（`_verify_cd_out.txt:146-157`）；必要性纯断言（computed=0）、O1 括注 2%≠4.0%（`_cdreport_check_out.txt:73`）、验收程序缺席（`_dD_PHYSICAL_S_ALIGNMENT.md:134`） |

## 6 结论（closedCount、可升格判定、未验项、不选判据声明）

- **closedCount**：补证报 **3/4**（`_cd_verdict.md:84`）；复核判 **partial**（其中崩点2闭合被拔高）。本件如实并记：**无条件闭合 2/4**（崩点1、崩点3）+ **崩点2 条件性闭合**（辖域归属 = 待裁决项②，未裁）+ **崩点4 部分闭合（未闭合）**。整体状态按复核规则标 **unconfirmed**（verdict = partial）。
- **可升格判定**：
  - 崩点1、崩点3：事实层经补证+复核+本件三轮独立实算一致，已闭合；除常规复核外无未验前提，可按「已闭合」升格使用。
  - 崩点2 升格条件 = 待裁决项②（`CRITERIA_ROUND2.md:98/:387`）落裁：若裁上游 `CRITERIA_COMPARE.md:146` 的 4 档读法 → 越界不成立（无支撑 0/4），崩点改判「断言与上游登记一致」；若裁 7 档读法 → 越界成立（2/7 无支撑）；若裁 13 档读法 → 越界成立（8/13 或 9/13，取决于 probe:171 口径是否统一，亦未裁）。
  - 崩点4 升格条件 = 三缺口补齐：必要性给出构造性证明或反例计算（替代 computed=0 的纯断言）、:126 括注「合计 ≤ 2%」算术修正（求和读法实为 4.0%）、验收/获取程序落地并有新观测量落盘。
- **未验项清单（如实登记，不补造）**：
  1. 编排方内联补证回件 JSON 文本未落盘（`_cd_verdict.md` 为其转述落盘件）——无磁盘指纹实体，未验。
  2. 补证 evidence 中 `_dD_align_out.txt` 指纹的「本轮实算」归属不成立（实为题给指纹抄录）；值本身经本件与复核独立实算 match。
  3. §9.7「高档」辖域归属（7 档 / 13 档 / 4 档）与 probe:171 行级证据口径是否统一——均属待裁决项②范围，未裁决。
  4. D 硬阻断解除条件：验收/核验程序未执行、未获取任何新观测量（`_dD_PHYSICAL_S_ALIGNMENT.md:134` 自declared）——未验。
  5. 本件未重跑任何调查/复核脚本（`_dC_recompute.py`/`_dD_check.py`/`_dD_align.py` 等会覆写只读件，只读铁律禁止）；补证/复核的「实跑」以落盘输出直读 + 本件对承重数字的独立复算为据。
- **不选判据声明**：本件只补证四项崩点事实并汇编复核结论，**不选判据、不改口径 B、不改 `STALL_EVENT_DEFINITION.md:177/:190/:191`（本件实读原文与补证记录一致、mtime 早于本轮）、不改台账（mtime 均早于本轮）**；不 commit、不 push；零真机、零采样代码；唯一写域 = `lead/r2_unclosed_cd_20261108/`。全部判定只回答「崩点闭合 / 条件性 / 未闭合、能否升格」，不对任何候选判据作取舍、排序或工程建议；§9.7 辖域各读法的数字并列呈现，裁定权留待待裁决项②。
