Q1 | DISC_ESTABLISH.tsv = 28 行 + 表头 ; 置信度: 高18/中10/低0 ; 落盘=lead\next_re_20261117_r14\DISC_ESTABLISH.tsv
Q2 | recheck_verify.py 实现 4+2 条校验（R1 行存在且唯一 / R2 discipline 对齐 / R3 at 晚于立条上界 / R4 round 序号+窗口 / R5 anchors 哈希 / R6 conclusion 闭集合） ; fail-closed: 是（无 None，缺字段/格式不符/时刻不可解析/表缺行一律 False） ; 接口=verify_recheck_line(root,row)->(ok:bool,detail:str)
Q3 | 现成合规 0/28 ; 缺行可补 12/28 ; 无法补 16/28 ; 无法补原因: <类A 叙述/他人报告、无自产出机制=7条(16,18,19,21,23,24,25)> <类B 手编或一次性产物、无可重跑生成器=5条(5,6,7,8,10)> <类C 底座/门禁文档自指或本卡禁改=4条(1,2,9,20)>
Q4 | 正控 1/1 通过 ; 反控 4/4 均 False ; 明细=<正控: 真实 TSV 第11行+合法自述行(round=R52,at=2026-11-22T16:20:00+08:00)→True> <反控1 discipline 11→12→False(R2)> <反控2 at 16:20→11:00(早于立条12:00:54)→False(R3)> <反控3 at→15:00(落在 R52 窗[16:17:50,16:28:03]外)→False(R4)> <反控4 anchors 改为全0哈希→False(R5)> ; 另测 8 项 fail-closed 边界全 False
FALSIFY | 这套校验什么情况下会误判为真: <① 协同伪造：行为者同时改 col7「无→有」并在产物手写一条六字段全合法的自述行（discipline 对、at>立条上界、round 在窗、anchors 按第4列重算、conclusion 合法），R1–R6 全过而从未回跑——at/立条表/轮窗表皆同一行为者自写、无外部可信时钟（git 未跟踪、mtime 被批量重置）> <② 注册表回填：把 DISC_ESTABLISH 落盘时刻前移、或把内嵌 ROUND_WINDOWS 窗口放宽，任意 at 过 R3/R4> <③ 事后补冒充自写：产物在立条当轮已含 grep 目标串，事后仅追加行并把 at 写成回跑时刻；校验器只读「行+命中」，不核内容写入时刻> <④ 只证声称不证判据：自述行证明「某时刻声称跑过」，不证明真按该纪律判据 ran；anchors 哈希可被同一自写者重算，R5 非独立证据> <⑤ 窗口粒度：R53 无后继快照、end 取当日 23:59:59，当日任意晚间 at 都过 R4；窗口来自 board 快照文件名（分钟级），非真实轮边界> <⑥ 单向右：C11 只校 col7 以「有」开头者，写「无」却实际回跑的行不被检（漏报方向，不产生误真但不对称）>
OVERALL | 第 7 列能从「纯自述、无→有造假仍 PASS」收窄到「12/28 条有结构化自述行 + 跨字段一致性 + 显式不可验证计数、16/28 无自产出机制保持 unverifiable」；但因无外部可信时钟/独立执行日志，只能校「自述一致」，校不到「回跑事实已证」——未取得外部时钟前不得把 PASS 读作已证。

---

# R53-T2-ESTABLISH · 实现报告（t2-establish）

> 只读 `lead\`；唯一新建：`lead\next_re_20261117_r14\DISC_ESTABLISH.tsv`、
> `lead\next_re_20261117_r14\recheck_verify.py`；本报告写在 `R17_R92_T2_ESTABLISH\`。
> `check_disc.py` 与 `DISC_RECHECK.tsv` 一个字节未改（仅只读）。取不到写「未取得」，不编造。

## 落盘路径
- `lead\next_re_20261117_r14\DISC_ESTABLISH.tsv`（3,661 B，28 数据行 + 1 表头，6 列，LF-only，UTF-8）
- `lead\next_re_20261117_r14\recheck_verify.py`（15,271 B，含 `verify_recheck_line` 与 `--self-test`）
- 本报告：`lead\next_re_20261117_r14\R17_R92_T2_ESTABLISH\REPORT.md`

## Q1 明细 · 立条时刻表如何推断
方法（严格照卡）：`R14_COMMON` 的 §2.14–§2.37 节标题只写「R17 追加，2026-11-22」，无时分秒
（§2.51 已指出）。故取 `R17_LEAD_BASELINE\R14_COMMON.before_HHMMSS_.bak` 的文件名时分秒
（mtime 已核对与文件名一致，全为 2026-11-22）：某节文字**首次出现**在哪个备份，
该备份时间戳即该节落盘时刻的**上界**；上一备份不含 ⇒ 相邻两备份夹住 ⇒ 置信度「高」；
最早备份就含、无更早 .bak 可夹 ⇒ 只有上界 ⇒ 置信度「中」；完全推不出 ⇒「低」（本次 0 条）。

逐节首次出现（实测，字节级搜 `## X.Y ` 标题）：

| 节 | 首次出现的 .bak | 上一 .bak | 夹住? | 上界(ISO8601+08:00) | 置信度 | 覆盖纪律号 |
|---|---|---|---|---|---|---|
| §2.14 | before_114835 | 无更早 .bak | 否 | 11:48:35 | 中 | 1,2,3 |
| §2.17 | before_114835 | 无 | 否 | 11:48:35 | 中 | 4 |
| §2.19 | before_114835 | 无 | 否 | 11:48:35 | 中 | 5,6 |
| §2.20 | before_114835 | 无 | 否 | 11:48:35 | 中 | 7 |
| §2.21 | before_114835 | 无 | 否 | 11:48:35 | 中 | 8,9 |
| §2.22 | before_114835 | 无 | 否 | 11:48:35 | 中 | 10 |
| §2.24 | before_120054 | before_114835 不含 | 是 | 12:00:54 | 高 | 11,12 |
| §2.25 | before_122605 | before_120054 不含 | 是 | 12:26:05 | 高 | 13,14,15 |
| §2.26 | before_123632 | before_122605 不含 | 是 | 12:36:32 | 高 | 16,17 |
| §2.27 | before_131044 | before_123632 不含 | 是 | 13:10:44 | 高 | 18,19,20 |
| §2.28 | before_131044 | before_123632 不含 | 是 | 13:10:44 | 高 | 21,22 |
| §2.29 | before_131332 | before_131044 不含 | 是 | 13:13:32 | 高 | 23 |
| §2.30 | before_132405 | before_131332 不含 | 是 | 13:24:05 | 高 | 24 |
| §2.31 | before_134151 | before_132405 不含 | 是 | 13:41:51 | 高 | 25 |
| §2.34 | before_140857 | before_135928 不含 | 是 | 14:08:57 | 高 | 26 |
| §2.36 | before_142000 | before_141620 不含 | 是 | 14:20:00 | 高 | 27 |
| §2.37 | before_143628 | before_142000 不含 | 是 | 14:36:28 | 高 | 28 |

注意（不抬高精度）：§2.14–§2.23 在**最早** .bak（before_114835, 11:48:35）就已存在，
虽另有更早的 `before_21X.md` / `before_AZ1X_*.md` 非本卡指定的 `.before_*.bak` 系列，
本卡口径只用 `.bak`，故这 10 条按「只能给上界」记「中」，不伪造下界凑完整时间线。
`落盘时刻` 列写的是**上界**而非精确落盘秒；校验器 R3 用「at 严格晚于上界」，
方向保守（宁可把「上界与真实落盘之间」的 at 误判为非回跑，不与造假同向）。

## Q2 明细 · recheck_verify.py 设计
接口：`verify_recheck_line(root, row) -> (ok: bool, detail: str)`，无 None。
`row` 为 `DISC_RECHECK.tsv` 一行 split('\t')（7 列）。产物路径 `row[4]` 相对 `root` 解析。

六条校验（均 fail-closed，任一不满足即返回 False + 原因）：
1. **R1** 产物可读且含且仅含一条 `DISC_RECHECK ` 开头行；再用严格正则核
   `DISC_RECHECK discipline=<N> round=<Rxx> at=<ISO> anchors=<sha256:HEX64> conclusion=<X>`，
   字段集必须是 {discipline,round,at,anchors,conclusion} 五者、无重复键、单空格、行首顶格。
2. **R2** `discipline` 为无前导零十进制，且 `== int(row[0])`。
3. **R3** `at` 严格 `YYYY-MM-DDTHH:MM:SS+HH:MM`（strptime+正则双重），且 `at > DISC_ESTABLISH.tsv`
   该纪律的落盘上界；立条表缺文件/缺行/时刻不可解析 ⇒ False。
4. **R4** `round` 为 `R\d{2,3}`，序号 > 立条轮次序号（立条表第 3 列，本表全为 R17⇒17），
   且 `at ∈ [start,end]` 轮窗。
5. **R5** `anchors == 'sha256:' + sha256(UTF-8(row[3] 『必查的现有数据锚』逐字串))`
   —— 已用 §2.51 示例复算验证：`v5.8 基线：人工核验类 0` ⇒
   `22395a6103650a4840fe208f6a00fd2ae02f14dce68fd37d9098e5917b616ffa`（与 §2.51 逐字吻合）。
6. **R6** `conclusion ∈ {PASS,FAIL,UNKNOWN}` 闭集合。

**round 窗口来源（如实声明）**：`DISC_ROUNDS.tsv` 在本盘上**不存在**；
本卡只允许新建两个文件，不能新建第三张表。故窗口表 `ROUND_WINDOWS` **内嵌于模块**，
且不是自造数——来自 `R17_LEAD_BASELINE\STATUS_BOARD.before_rNN_HHMMSS.md` 的文件名时分秒
（r35=11:22:34 … r53=16:28:03，全 2026-11-22+08:00），每条在源码注释里给出起止来源文件名。
窗口 = [本轮 before 快照时刻, 下一存在快照的轮次时刻)；r41 无 before 快照，R40 的 end 落到
R42 的 13:11:09；R53 无后继快照，end 取当日 23:59:59（保守，见 FALSIFY⑤）。
**不覆盖的轮次一律 False（fail-closed）** —— 这是「未取得窗口即不可验证」，不是通过。

**fail-closed 边界实测**（8/8 全 False）：无行 / 两行 / 缺字段 / 无时区时刻 /
round=R99 无窗口 / 多字段 / 产物文件缺失 / row 列数≠7。

## Q3 明细 · 逐条试跑（只检测，不补任何产物）
用真实 `DISC_RECHECK.tsv` 28 行逐条调 `verify_recheck_line`：**28/28 在 R1 直接 False**
（line_count=0）——现有产物**无一条**含 `DISC_RECHECK ` 自述行，故
**现成合规 = 0/28**（与 §2.51 R51-T2 的 Q1 结论「有 0/28」一致）。

「缺行可补 = 12/28」判据：目录内存在可重跑的检查器/生成器，运行时能在产物内自写该行，
不需要人手编造时间戳。已逐一核存在：
- 3,4：`R17_R61_FACTINDEX_V58\verify_anchors.ts` ✓
- 11,12：`_r38\checkC3.py` ✓；13,14：同脚本自身 ✓；15：`_r38\settle_iat.py` ✓
- 17：`R16_MEASURE_EVID675\mev675.py` ✓
- 22：`R17_R84_T1_NARRATIVE\q1_narrative.py` / `q4_sample.py` ✓
- 26：`R17_R78_T1_RECLASS\decide_cprime.py` ✓
- 27：`R17_R81_T2_EVID\judge_q4.py` / `judge_q4_v2.py` ✓
- 28：`R17_R88_T1_SEMDEF\decide_semdef.py` / `closure.py` ✓

「无法补 = 16/28」原因分类（沿用 §2.51 的可复核缺口，未取得项照写）：
- 类A 叙述/他人报告、无自产出机制（7）：16,18,19,21,23,24,25 —— 产物为 T1/T2/T4 执行员
  `REPORT.md`，叙述写出、无重跑生成器；21/24 同文件却 col7 相反，直接证「第7列非文件属性」。
- 类B 手编/一次性产物、无可重跑生成器（5）：5,6,7,8,10 ——
  `lead_recheck2.tsv`/`lead_recheck.tsv` 为 Lead 手编复核表（目录内**未取得**生成器）；
  `CHANGES.md` 为叙述日志。
- 类C 底座/门禁文档自指或本卡禁改（4）：1,2,9 产物是 `R14_COMMON.md` 自身（写自述行=自我引用、
  无独立回跑量）；20 是 `check_disc.py`（门自身，本卡禁改；「禁不可见字符断言」在产物中
  **未取得**）。

算术核对：12 + 7 + 5 + 4 = 28，四类互斥无重叠。

## Q4 明细 · 正反控（`python recheck_verify.py --self-test`，5/5 PASS）
正控取**真实** `DISC_RECHECK.tsv` 第 11 行（锚 `C3 双相反向注入`），仅把产物路径改向临时文件
`R17_R92_T2_ESTABLISH\_posctl_product.tmp`（跑完即删），写入一条合法自述行：
```
DISC_RECHECK discipline=11 round=R52 at=2026-11-22T16:20:00+08:00 anchors=sha256:ac0e7be5...df999 conclusion=PASS
```
→ `ok=True`（R1–R6 全过；R52 窗 [16:17:50,16:28:03] 来自 before_r52/r53 文件名）。

| 控制 | 改动（相对正控一处） | 期望 | 实测 | 失败码 |
|---|---|---|---|---|
| 正控 | 无 | True | True | ok R1–R6 |
| 反控1 | discipline 11→12 | False | False | R2 discipline 12 != row 11 |
| 反控2 | at 16:20→11:00（早于立条 12:00:54） | False | False | R3 at<=establish |
| 反控3 | at→15:00（落在 R52 窗外） | False | False | R4 at outside R052 window |
| 反控4 | anchors→sha256:000…0 | False | False | R5 anchors mismatch |

## FALSIFY 详细（硬要求，未跳过）
这套校验在以下情形会把「假回跑」误判为真（前四条为 §2.51 继承的主风险）：
1. **协同伪造（无法靠本方案关闭）**：行为者同时改 col7「无→有」并在产物手写一条六字段全合法
   自述行——discipline 对、at 晚于立条上界、round 在窗、anchors 按第 4 列重算、conclusion 合法。
   R1–R6 全过而从未回跑。根因：`at`、`DISC_ESTABLISH` 落盘时刻、内嵌 `ROUND_WINDOWS` 皆同一
   行为者可写，无外部可信时钟（lead 全树 git 未跟踪；产物 mtime 被批量重置为 11-22 同日）。
2. **注册表回填**：把 `DISC_ESTABLISH` 落盘时刻前移、或把内嵌轮窗放宽（如把 R53 end 再延后），
   任意 at 过 R3/R4。注册表本身无防篡改（无外部哈希/签名）。
3. **事后补冒充产物自写**：产物在立条当轮已含 grep 目标串（纪律 5/8/10/11 等确为当轮自带），
   事后仅追加自述行、把 at 写成回跑时刻；校验器只读「行 + 命中」，不核内容写入时刻 ⇒ PASS。
4. **只证声称、不证判据**：自述行证明「某时刻声称跑过」，不证明真按该纪律判据 ran；
   `anchors` 哈希可被同一自写者重算，R5 不是独立证据。
5. **窗口粒度**：R53 无后继 before 快照、end 取当日 23:59:59，当日任意晚间 at 都过 R4；
   窗口来自 board 快照文件名（分钟级、且 r41 缺快照被并入 R40），非真实轮边界。
6. **单向右**：拟议 C11 只校 col7 以「有」开头者，写「无」却实际回跑的行不被检——这是漏报
   方向（不直接产生误真），但使 PASS 的语义不对称，必须与 unverifiable 计数一起打印。

## OVERALL
第 7 列能从「纯自述、无→有造假仍 PASS」收窄到「12/28 条有结构化自述行 + 跨字段一致性 +
显式不可验证计数、16/28 无自产出机制保持 unverifiable」；但因无外部可信时钟/独立执行日志
（均未取得），只能校「自述一致」，校不到「回跑事实已证」。未取得外部时钟前，不得把 PASS
读作「28 条回跑全证」。

## 未取得清单
- 各纪律立条的**精确**落盘秒（§2.14–§2.37 仅记日期；本表给的是上界，10 条仅「中」置信度）。
- `DISC_ROUNDS.tsv`（盘上不存在，本卡只准建两文件）→ 轮窗改用 board 快照文件名内嵌，覆盖 r35–r53。
- R53 之后轮次的窗口（无后继 before 快照）→ 不覆盖即 False，未取得。
- 跨轮、独立的纪律回跑执行日志 / 外部可信时钟（git 未跟踪、mtime 批量重置）。
- 类 B 纪律 5/6/7/8/10 的可重跑生成器（目录内未见）。
