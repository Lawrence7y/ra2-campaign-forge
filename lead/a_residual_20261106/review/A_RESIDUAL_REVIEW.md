# A_RESIDUAL_REVIEW.md · A 组残余引用账及验收记录独立复核报告

- **复核员角色**：交付件复核员（新上下文独立复核）
- **复核时间**：2026-11-06
- **被核交付件**：
  - `lead/a_residual_20261106/A_RESIDUAL_REFERENCES.md`
  - `lead/a_residual_20261106/ACCEPTANCE_RECORDS.json`
  - `lead/a_residual_20261106/check_a_residual.py`

```yaml
subjectSha256: 746b66d4c0290243f57e402bc1741f49e91b56ab1bce63bf98dce1e4fde4656f
subjectBytes: 28384
checkedEveryRow: true
tierInflationFound: false
gateExitCode: 0
```

附备查伴随交付件哈希：
- `lead/a_residual_20261106/ACCEPTANCE_RECORDS.json`: SHA256 = `d421f8bc5cc02eee2a0ea908a60477cdb313541cbff3cfd96a65728528d0efda` / 37,517 字节。

---

## 0 复核执行说明与纪律执行

本复核严格执行本项目铁律：
1. **零真机**：未启动 `gamemd.exe` / `ra2loader` / `YURI.exe`，不 `taskkill`，不读活进程内存；
2. **零采样代码**：未编写或运行 hook / MiniDump / SuspendThread / StackWalk / 探针注入；
3. **只读母本与既有件**：未修改 `ra2youli/**`、`out/re_work/**`、`lead/re_line_20261105/**`、`lead/GOAL_*`、`lead/PENDING_DECISIONS.md` 等任何既有件；
4. **唯一写域**：仅写入本复核文件 `lead/a_residual_20261106/review/A_RESIDUAL_REVIEW.md`；
5. **不 commit、不 push**；
6. **Python 命令**：统一使用 `python -I -X utf8`；
7. **逐条核验不抽样**：对 17 项条目的全部行号断言逐一打开比对原文，重跑门禁，专项抓档位通胀。

---

## 1 门禁脚本重跑结果（检查项 2）

复核员在仓库根目录下实跑确定性门禁脚本：
```bash
python -I -X utf8 lead/a_residual_20261106/check_a_residual.py
```

### 1.1 执行输出与退出码
- **exitCode** = `0`
- **完整输出**：
```
GATE PASS
  1) 交付件与解析:   lead/a_residual_20261106/A_RESIDUAL_REFERENCES.md 与 lead/a_residual_20261106/ACCEPTANCE_RECORDS.json 均存在且解析正常 (非空数组，共 17 条)
  2) 字段完整性:     全部条目均包含全部 13 个必需字段
  3) 唯一性与覆盖度: itemId 全部唯一，itemClass 完整覆盖 ['R1', 'R2', 'R3']
  4) 档位与裁决枚举: tier 与 decision 取值全部合法
  5) 文件哈希实算:   回文件系统实算比对 93 次，SHA256 全部 100% 吻合
  6) 账目双向一致:   Markdown (### 标题 17 项) 与 JSON (共 17 项) 完全双向一致
  7) 未验小节校验:   「## 4 未验」小节存在且非空 (1102 字符)
```

门禁 7 项检查全绿，93 次文件 SHA256 哈希回盘核验 100% 吻合，Markdown 与 JSON 之间 17 条条目双向严格一致。

---

## 2 逐条行号断言核对（检查项 1，无抽样，17/17 全核）

复核员逐一打开对应文件，核对每一处「文件:行」是否属实：

### 2.1 R1 类：部分落实（3 条）

1. **R1-W9-2**：
   - 依据引用：`lead/re_line_20261105/A1_ERRATA_MAP/ERRATA_W9.md:48-55`（定义 W9-2 补登记 QC124 写入链）、`lead/re_line_20261105/A1_ERRATA_MAP/A1_ERRATA_MAP.md:88`（矩阵行注明已落实 `:155-157` 但正文漏引 `QC124_VERDICT.json:74-87` 与 `BASELINE_A4_PROPOSAL.md:79,92,104`）、`lead/re_line_20261105/W9_SINGLESTEP_7CFC9F/W9_SINGLESTEP.md:155-157,193,230`（正文 `:155-157` 已入主链，`:193` 为 §7 登记处，`:230` 声明零真机未复现）、`reviews/Q4_review.md:425-431,436`（L11-14 寄存器比对与口径收窄）；
   - 实跑验证：`grep -n "BASELINE_A4_PROPOSAL\|74-87" lead/re_line_20261105/W9_SINGLESTEP_7CFC9F/W9_SINGLESTEP.md` 确实全件仅命中 `:193` 一行；
   - 历史证据核对：`QC124_VERDICT.json:8,36,47-50,60-63,74-87`、`VERDICT_T11.md:148`、`ERRATA_EXCEPT_RESTORE.md:12,16,17`、`BASELINE_A4_PROPOSAL.md:79,92,104` 逐行实读核验，内容完全吻合；原断言 `Q4_RELATION.md:31`「这件 EXCEPT 不是任何一趟的崩溃，是历史基线残件」逐字属实。
   - **核验结论**：全部行号真实，表述完全吻合。

2. **R1-W9-9**：
   - 依据引用：`lead/re_line_20261105/A1_ERRATA_MAP/ERRATA_W9.md:111-118`、`lead/re_line_20261105/A1_ERRATA_MAP/A1_ERRATA_MAP.md:89`、`lead/re_line_20261105/W9_SINGLESTEP_7CFC9F/W9_SINGLESTEP.md:182,184,200`、`reviews/Q5_review.md:514-519`；
   - 原文核对：`Q5_ROUTES.md:89`（「是否受 D-13 限制：不受。PENDING_DECISIONS.md:67 明写…」）、`Q5_ROUTES.md:177`（`PENDING_DECISIONS.md:171` 现处置为「(暂停) E3 暂不执行」）；
   - 盘面核对：实测 `lead/PENDING_DECISIONS.md` 当前版本 305 行，历史 07:50 锚点 `:78-80/:114` 现已不可复现；`D22_RULING/TASK.md:29,31` 确为「纯静态、不需真机、不受 D-13 限制」与「申请真机趟专抓崩溃。需用户明示授权，受 D-13 约束」。
   - **核验结论**：全部行号真实，表述完全吻合。

3. **R1-W9-19**：
   - 依据引用：`lead/re_line_20261105/A1_ERRATA_MAP/ERRATA_W9.md:201-208`、`lead/re_line_20261105/A1_ERRATA_MAP/A1_ERRATA_MAP.md:90`、`lead/re_line_20261105/W9_SINGLESTEP_7CFC9F/W9_SINGLESTEP.md:151,184,210`、`reviews/Q4_review.md:456-457`、`reviews/Q5_review.md:415-417,522-526`；
   - 代码实读：`out/re_work/work_chain/CONTINUE_20261003/lead/qc151_u0400_trip/qc151_trip.py:4575` 逐行实读确实为 `    if not src.exists():` 守卫；
   - 原文与搜索：`Q4_RELATION.md:14` 为 `回件时刻 = 2026-11-06 02:12`，`Q5_ROUTES.md:5` 为 `回件时刻 = 2026-11-06 02:57:32`；`grep -n "02:15:47\|02:10:46" lead/re_line_20261105/W9_SINGLESTEP_7CFC9F/W9_SINGLESTEP.md` 确实全件仅命中 `:210`（§7 条目自身）。
   - **核验结论**：全部行号真实，表述完全吻合。

---

### 2.2 R2 类：结构缺口（12 条）

汇总件 `lead/re_line_20261105/W8_STATIC_LOCATE/W8_STATIC_LOCATE.md:198` 破折号清单实读逐字为：
> `口径修正生效声明：本汇总凡与回件原文冲突处一律采用复核后口径——F6 +0xD80 族 ctor「装入非清零」与 0x4326B3 宿主区间；F7 %14 门周期（PatrolScan INI 键、写点恰 2）与 0x736664 三条件门；F8 0xB0CE88 域界/写者数与「139 零计数」窗口限定。`

确仅点名 6 条（W8-1、W8-2、W8-4、W8-5、W8-9、W8-10），遗漏 6 条（W8-3、W8-6、W8-7、W8-8、W8-11、W8-12）。

4. **R2-W8-1**：
   - 引用核对：`W8_STATIC_LOCATE.md:169,198`；`ERRATA_W8.md:60-68`；`W8_review.md:55`；
   - 实测：`:169` 确为 `0x432690..0x4326BD`，正文 §2/§2.3 表确未重述该区间，仅 `:169` 一处。
   - **核验结论**：属实。

5. **R2-W8-2**：
   - 引用核对：`W8_STATIC_LOCATE.md:59,170,198`；`ERRATA_W8.md:69-77`；`W8_review.md:56`；
   - 实测：正文 §2.1 表 `:59` 明文注明「复核改正：非清零」；`:198` 显式点名。
   - **核验结论**：属实。

6. **R2-W8-3**：
   - 引用核对：`W8_STATIC_LOCATE.md:59,82,171,198`；`ERRATA_W8.md:78-86`；`W8_review.md:57`；
   - 实测：正文 `:59` 确实引 `_f6rev_probe_out.txt:659-662`，`:82` 确实引 `out:669-682`；`:198` 未显式点名。
   - **核验结论**：属实。

7. **R2-W8-4**：
   - 引用核对：`W8_STATIC_LOCATE.md:101,159,175,198`；`ERRATA_W8.md:87-96`；`W8_review.md:58`；
   - 实测：正文 `:101` 全文重述，`:159` 规定「先读 PatrolScan，不得写死 14」；`:198` 显式点名。
   - **核验结论**：属实。

8. **R2-W8-5**：
   - 引用核对：`W8_STATIC_LOCATE.md:102,176,198`；`ERRATA_W8.md:97-106`；`W8_review.md:59`；
   - 实测：正文 `:102` 全文重述三条件门；`:198` 显式点名。
   - **核验结论**：属实。

9. **R2-W8-6**：
   - 引用核对：`W8_STATIC_LOCATE.md:177,198`；`ERRATA_W8.md:107-115`；`W8_review.md:60`；
   - 实测：`grep -n "6FB03D\|6FB040\|6FB048" W8_STATIC_LOCATE.md` 全件仅命中 `:177`（§6 条目自身），正文完全无落点；`:198` 未点名。
   - **核验结论**：属实。

10. **R2-W8-7**：
    - 引用核对：`W8_STATIC_LOCATE.md:112,178,198`；`ERRATA_W8.md:116-125`；`W8_review.md:61,101-103`；
    - 实测：正文 `:112` 确已承接（「起点按复核修正 ≈0x740B60，0x740B51 落 nop 填充」）；但被修原文「fn 0x740B51..0x740DED」在 `F7_TARGETING.md` 中全文 grep 0 命中；`:198` 未点名。
    - **核验结论**：属实。

11. **R2-W8-8**：
    - 引用核对：`W8_STATIC_LOCATE.md:96-97,179,196,198`；`ERRATA_W8.md:126-134`；`W8_review.md:62`；
    - 实测：`:196` 确将「12 窗宿主名」列入自曝未验，但正文表 `:96-97` 径用「House 级」且标 ✅（无存疑限定）；`:198` 未点名。
    - **核验结论**：属实。

12. **R2-W8-9**：
    - 引用核对：`W8_STATIC_LOCATE.md:125,183,198`；`ERRATA_W8.md:135-144`；`W8_review.md:63,99`；
    - 实测：正文 `:125` 全文重述（写者 6 个，零交集不变）；代码截断实为 `_w8_f8.py:358`（`for t in h[:14]:`）；`:198` 显式点名。
    - **核验结论**：属实。

13. **R2-W8-10**：
    - 引用核对：`W8_STATIC_LOCATE.md:126,139,184,198`；`ERRATA_W8.md:145-153`；`W8_review.md:64`；
    - 实测：正文 `:126` 与 `:139` 均明确包含「调用点后 8 条指令窗口内零内存计数」限定措辞；`:198` 显式点名。
    - **核验结论**：属实。

14. **R2-W8-11**：
    - 引用核对：`W8_STATIC_LOCATE.md:185,198`；`ERRATA_W8.md:154-162`；`W8_review.md:65`；
    - 实测：`_w8_f8_out.txt:54` 确实为 `NEXT_INSN_DIST`，`F8_VISIBILITY.md:68` 误写为 `NEXT_INSN1_DIST`；汇总件全件仅 `:185` 命中，正文完全无落点；`:198` 未点名。
    - **核验结论**：属实。

15. **R2-W8-12**：
    - 引用核对：`W8_STATIC_LOCATE.md:127,186,198`；`ERRATA_W8.md:163-171`；`W8_review.md:66,94-96`；
    - 实测：正文 `:127` 已全文承接（注明实际范围为 .text 并引复核全文件扫描 0 额外命中）；但 `:198` 声明未显式点名。
    - **核验结论**：属实。

---

### 2.3 R3 类：引用不可定位（2 条）

16. **R3-W8-7**：
    - 引用核对：`F7_review.md:94-95,193`（M4 明确指认 0x740B51 落 nop 填充内，实际 ≈0x740B60）、`_f7rev_out.txt:433-434`（`:433` `ret` / `:434` `nop`）、`W8_STATIC_LOCATE.md:112,178`；
    - 检索验证：`grep -in "740b51" lead/re_line_20261105/W8_STATIC_LOCATE/F7_TARGETING.md` 输出退出码 1，完全 0 命中；
    - **核验结论**：回件出处不可定位完全属实，本条判定档定为 `PARTIAL` 准确。

17. **R3-W8-8**：
    - 引用核对：`F7_review.md:195,202`（M5「House 级」标签维持存疑登记；:202 12 窗未重扫 CFG）、`W8_STATIC_LOCATE.md:96-97,179,196`、`F7_TARGETING.md:182,199,300-301,328`、`ERRATA_W8.md:126-133`、`A1_ERRATA_MAP.md:145,161`；
    - 实测：正文 §3 表 `:96-97` 确实直用「House 级」且带 ✅，未加注存疑限定；汇总件 `:196` 列入未验，正文仅半承接。
    - **核验结论**：属实。

---

### 2.4 说明小节与未验小节核对（§0 与 §4）
- `A_RESIDUAL_REFERENCES.md:6` 引 `D24_RULING/RULING_D24.md:48,58,60` 及 `NEXT_STEPS_20261106.md`，比对核实 D-24 决议文本及 N-1 项完全对应；
- `A_RESIDUAL_REFERENCES.md:224` 引 `RULING_D24.md:48,75`，核实 D-24 决议第 48 行及第 75 行均明文禁止重建或恢复 W7 phase 2，要求仅按 PARTIAL 采信；
- `A_RESIDUAL_REFERENCES.md` 中的「## 4 未验与拒绝固定」小节非空，长度 1102 字符，包含拒绝固定清单、未验场景、真机运行期事件仓内限制、静态深度扫描未跑限制及台账漂移说明。

---

## 3 专项检查：档位通胀与落点虚构核查（检查项 3）

专项排查重点：
1. **是否存在任何一条将 `PARTIAL` 抬格为 `CONFIRMED`？**
2. **是否存在任何一条将「无落点」写成「已承接」？**

### 3.1 档位核查结果
- 上游 `A1_ERRATA_MAP.md` 及各自回件中被裁定为 `PARTIAL` 或部分落实的项目：
  - W9-2：在 `A_RESIDUAL_REFERENCES.md` 与 `ACCEPTANCE_RECORDS.json` 中明确记为 `tier = PARTIAL`，`decision = PARTIAL`；
  - W9-9：明确记为 `tier = PARTIAL`，`decision = PARTIAL`；
  - W9-19：明确记为 `tier = PARTIAL`，`decision = PARTIAL`；
  - W8-7（R2-W8-7 与 R3-W8-7）：明确记为 `tier = PARTIAL`，`decision = PARTIAL`；
- 其余各项（如 W8-1、W8-2、W8-4、W8-5、W8-9、W8-10 以及事实勘误本身经复核确证的 W8-3、W8-6、W8-8、W8-11、W8-12）在回件与 `A1_ERRATA_MAP.md` 中判定档本来即为 `CONFIRMED`，未出现任何档位虚标或越级提升；
- 《A1 汇总》总评：在 `A_RESIDUAL_REFERENCES.md:6` 中明确写明「总判为 **PARTIAL**」，在 §0.2 条 1 中明确规定「严禁越级提升档位：`PARTIAL` 绝对不许升格为 `CONFIRMED`」；
- W7 组：在 §4.2 条 4 中明确声明「W7 phase 2 坚决不予恢复与重建，相关条目一律按 PARTIAL 级初判采信」；
- **排查结论**：**零档位通胀，未发现任何将 PARTIAL 抬格为 CONFIRMED 的情形**。

### 3.2 落点状态核查结果
- W8-6：`A_RESIDUAL_REFERENCES.md:117` 明确注明「落点状态：:198 漏点名；**正文完全无落点（仅存在于 §6 :177）**」，并在 `unresolved` 中明记「汇总件正文完全无落点」；
- W8-11：`A_RESIDUAL_REFERENCES.md:162` 明确注明「落点状态：:198 漏点名；**正文完全无落点（全件仅 §6 :185 一处命中）**」，并在 `unresolved` 中明记「汇总件正文完全无落点」；
- W8-8：`A_RESIDUAL_REFERENCES.md:135` 明确注明「落点状态：:198 漏点名；**正文仅半承接（:196 承接一半，表 :96-97 漏限定）**」；
- 只有正文确有落点的条目（如 W8-2、W8-4、W8-5、W8-9、W8-10、W8-12、W8-3、W8-7）才记录其具体正文行号；
- **排查结论**：**零落点虚构，未发现任何将「无落点」篡改或声称为「已承接」的情形**。

综上，`tierInflationFound = false`。

---

## 4 复核结论

- **checkedEveryRow** = `true`（全量 17 条逐条核实，非抽样）
- **subjectSha256** = `746b66d4c0290243f57e402bc1741f49e91b56ab1bce63bf98dce1e4fde4656f`
- **subjectBytes** = `28384`
- **tierInflationFound** = `false`
- **issues** = `[]`（无任何硬性问题与合规缺陷）
- **复核结论判定**：**ACCEPT（合格，准予入账）**。
