Q1 | 为凑数据构造 | 依据=R14_COMMON §2.56:4647 白纸黑字「最省事的修法是『把 r55 窗口起点前移到 17:00』——但那是我为了让门禁变绿而改判据，与 §2.55 我否决三态方案的理由完全一样……本轮我不选」，紧接着 §2.57:4682-4685 就把起点由 17:41:46 前移到 17:34:00 并改称 off-by-one；§2.57:4693 声称「20 条逐条重映射」，但 recheck_verify.py:68-71 的来源文件名列仍是 before_r55/before_r56（时刻已取 before_r54→before_r55），只改时刻未改来源，是补丁不是重定义；§2.57:4708「12 条仍 FAIL 故非放水」是无效辩护——那 12 条 line_count=0 本就无自述行，与窗口无关。⇒「实际 a、b 是开始/结束快照」是先看到 5 条 at、后补的解释，不是从数据独立发现的普遍规律 ; 历史反例=<有：recheck_verify.py:269 的正控 round=R52/at=16:20:00，R17_R92_T2_ESTABLISH/REPORT.md:112-118 明记「5/5 PASS，R52 窗 [16:17:50,16:28:03] 来自 before_r52/r53 文件名」，属「已知属于第 R52 轮的自述行」；§2.57 后新窗变 [16:01:44,16:17:50]，实测 `python recheck_verify.py --self-test` → POS FAIL「R4 at outside R052 window」、SELFTEST FAIL (4/5)、exit=1（R17_R95_T4_AUDIT57/q4_selftest_output.txt:3,8-10）。且 NEG4（坏 anchors）现在被 R4 抢先拦下、不再测 R5，自测形态已退化。>
Q2 | 吻合 | 执行员报告说的是<2026-11-22T17:35~17:45 (+08:00)，R17_R94_T1_RERUN/REPORT.md:14「时间：2026-11-22T17:35 ~ 17:45 (+08:00)」> ; 字节增量能否佐证=能<r55_append_go.txt:44-52 记 17:39:19 那次追加 disc3/22/27/28 分别 +161/+162/+163/+162 B，r55_append_go2.txt:48-50 记 17:40:02 那次仅 disc4 +161 B；盘上现值 1233 / 244144 / 112713 / 661259 B，与 REPORT.md:29-33「前→后」逐项相符，前缀 sha256 亦逐字节核过> ; at 是<产物自动> ⇒ 关键结论=<append_link.py:215 `now = datetime.datetime.now().astimezone().replace(microsecond=0).isoformat()`、232-233 用 `at=%s` 写入；r55_append_dryrun.txt(17:39:15)→go.txt(17:39:19)→go2.txt(17:40:02) 单调递增、全落在执行员所述 17:35~17:45 内，盘上 4 条 at=17:39:19 + 纪律 4 at=17:40:02 与 go/go2 输出逐字一致。⇒ lead 担心的「事后手写自述」不成立：他不是在为一个手写时间调判据，at 是两次真实脚本运行打上的机器时刻。但必须同时写明：at 仍是同一行为者控制的机器时钟、无外部可信时钟（§2.51:4304-4305、§2.58:4783），「自动」≠「不可伪造」，Q4 已实测可被事后伪造。>
Q3 | 绕开 | 理由=<根本问题是「自述行的时间戳永远由写它的人决定，任何时间窗口检查本质上不可靠」——§2.51:4297-4305 逐字记 FALSIFY 1「协同伪造……R1–R6 全过而从未回跑」并写「它的结论我完全接受……未取得外部时钟前不得把 PASS 读作已证」。§2.57 只把 r55 起点挪一格以容纳真实 at，既未引入外部时钟，也未引入独立凭证；§2.58:4783 自己承认「做不到真不可伪造」。Q4 实测一条全字段合法的自述行可事后伪造而 exit=0，直接证明窗口判据仍不可靠。§2.57 解决的是「窗口和记账时刻不对齐」这个局部问题，对「自述时间不可信」这个根本问题是绕过。>
Q4 | 未穷尽 | 我构造的第三种伪造: <对非冻结纪律 11，在其产物 `_r38\checkC3_report.md` 末尾追加一条全字段合法的自述行 `DISC_RECHECK discipline=11 round=R55 at=2026-11-22T17:35:00+08:00 anchors=sha256:ac0e7be5…（按 DISC_RECHECK.tsv 第 4 列 C3 双相反向注入 重算）conclusion=PASS`，并把 DISC_RECHECK.tsv 第 11 行第 7 列「无」改成「有」。不改 FREEZE_SHA256、不改 ROUND_WINDOWS、不动 DISC_UNVERIFIABLE.tsv、不碰 check_disc.py。此路径 §2.51:4297-4299 早已逐字描述且 lead「完全接受」，§2.58 的反控 A/B 都没覆盖（A 只测无→有且不带自述行，B 只测加冻结档）> ; 实测 exit=0<C11 由 `ok=5 fail=0 frozen-unverifiable=12 claims-none=11` 变为 `ok=6 fail=0 frozen-unverifiable=12 claims-none=10`，门禁仍绿；q4_forgery_output.txt:15-21> ; 结论=未抓<复原后 DISC_RECHECK.tsv(39af22f0…)/checkC3_report.md(42884d62…)/check_disc.py(f957c97b…) 三文件 sha256 逐字节相同，门禁回到 ok=5，q4_forgery_output.txt:22-32。另 §2.58:4782-4784 自认同时改档与 FREEZE_SHA256 也可绕过，更证「都验证过」过头。>
Q5 | §2.57「off-by-one」应改为=<把 r55 窗口起点从 17:41:46 前移到 17:34:00 以容纳 5 条真实 at；这是按结果改判据（§2.56:4647 自己认过「那是我为了让门禁变绿而改判据」），「先干活后记账」是事后补的解释、非事前从数据发现的规律；该定义使校验器自身正控 R52 失效、自测由 5/5 退为 4/5，故不得称「改正配对、不是放宽」> ; §2.58「两个方向都验证过」应改为=<只验证了两条窄路径；协同伪造一整条合法自述行（§2.51 FALSIFY 1）实测 exit=0 未被抓，同时改冻结档与 FREEZE_SHA256 也已自认可行。门只校「自述一致」、不校「回跑事实」，PASS≠已证，两个方向远未穷尽伪造。>
OVERALL | 两者都不成立：§2.57 的「off-by-one 非放宽」自辩应推翻（为真实 at 改判据且破坏校验器自测），§2.58 的「两个方向都验证过」需修正（第三种协同伪造实测 exit=0 未抓）——两者均需修正，不是成立。

---

# 证据附录（逐字引用 + 文件/行；实测退出码；复原验证）

## Q1 · off-by-one 是凑数据构造，且有历史反例

**自认在先、改口在后（逐字）：**
- `R14_COMMON.md:4647`（§2.56 四）："最省事的修法是「把 r55 窗口起点前移到 17:00」——**但那是我为了让门禁变绿而改判据**，与 `§2.55` 我否决三态方案的理由**完全一样**。"
- `R14_COMMON.md:4656`："⇒ **甲有害、乙过宽、丙不可用。本轮我不选，记账为「待定义」。**"
- `R14_COMMON.md:4682-4685`（§2.57 一）："而旧窗口把 r55 定义为 `[board_r55, board_r56)` = `[17:41:46, …)` —— 把工作排到了它自己的记账之后。⇒ **旧表的语义是错的**……**第 N 轮的工作区间 = `[board_r(N-1), board_rN)`**"

⇒ 上一节刚说「前移起点=改判据、不选」，下一节就把起点从 17:41:46 前移到 17:34:00（§2.57:4698），换了个名字叫 off-by-one。这是同一动作，不是新发现。

**「非放宽」的辩护无效（逐字）：**
- `R14_COMMON.md:4707-4708`："如果窗口只是被我放宽，那 12 条没干活的也该跟着过；但它们仍然 FAIL。"
- 但那 12 条是 `line_count=0`（§2.57:4710、§2.55:4555），产物里根本没有自述行——窗口再怎么挪也不会让它们过。该判据对「是否放宽」零区分力。

**历史反例（实测）：**
- `R17_R92_T2_ESTABLISH/REPORT.md:112-118`："## Q4 明细 · 正反控（`python recheck_verify.py --self-test`，5/5 PASS）…… `DISC_RECHECK discipline=11 round=R52 at=2026-11-22T16:20:00+08:00 … conclusion=PASS` → `ok=True`（R1–R6 全过；R52 窗 [16:17:50,16:28:03] 来自 before_r52/r53 文件名）。"
- `R17_R92_T2_ESTABLISH/REPORT.md:125`：旧反控3 是 "at→15:00（落在 R52 窗外）"。
- §2.57 后 `recheck_verify.py:66` R52 窗变为 `[16:01:44, 16:17:50]`。实测 `python recheck_verify.py --self-test`（详见 `R17_R95_T4_AUDIT57/q4_selftest_output.txt`）：
  - `POS 完全合法 ok=False expect=True FAIL | R4 at outside R052 window [2026-11-22T16:01:44+08:00, 2026-11-22T16:17:50+08:00]`
  - `NEG3 ... ok=False expect=False PASS | R4 at outside R052 window ...`
  - `NEG4 anchors 哈希不符 ok=False expect=False PASS | R4 at outside R052 window ...`
  - `SELFTEST FAIL (4/5)` / `EXITCODE=1`
- ⇒ 曾被文档确认为「属于 R52 且合法」的正控行现在落到窗外；NEG4 也被 R4 抢先拦下、R5 不再被单独测试。§2.57 的定义不是「历史上每轮都成立的正确答案」，而是让这批 at 通过的局部改判。
- 另注 `recheck_verify.py:68-71`：时刻已改为 `[before_r54, before_r55)` 等，但来源文件名列仍写 `STATUS_BOARD.before_r55_174146.md` / `before_r56...`，未随时刻重映射——进一步说明是补丁而非成对重定义。

## Q2 · at 是产物自动打点，字节增量完全吻合（最关键问题：lead 的担忧不成立）

**执行员自述时段：** `R17_R94_T1_RERUN/REPORT.md:14` "时间：2026-11-22T17:35 ~ 17:45 (+08:00)"。

**at 由脚本自动生成（逐字代码）：**
- `R17_R94_T1_RERUN/append_link.py:213-215`：
  ```
  # at 用真实本次运行时刻（+08:00）
  import datetime
  now = datetime.datetime.now().astimezone().replace(microsecond=0).isoformat()
  ```
- `append_link.py:232-233`：`line = ('DISC_RECHECK discipline=%d round=%s at=%s anchors=%s conclusion=%s' % (disc, ROUND, now, anchor_hash(row), conclusion))`

**两次真实运行，两个时刻，逐字对应盘上：**
- `r55_append_dryrun.txt:9,17,25,33,41`：dry-run（未写盘）at=17:39:15（5 条全同）。
- `r55_append_go.txt:9,17,25,33,41`：go at=17:39:19（5 条全同）；`:44` disc3 `911 -> 1072 (+161)`；`:46` disc4 `[ABORT] 字节数在测量后变化 911 -> 1072`；`:47` disc22 `243982 -> 244144 (+162)`；`:49` disc27 `112550 -> 112713 (+163)`；`:51` disc28 `661097 -> 661259 (+162)`；`:54` `[rc=1]`。
- `r55_append_go2.txt:9,18,26,35,44`：go2 at=17:40:02（5 条全同）；`:48-53` disc3/22/27/28 `[SKIP] 已有自描述行`；`:49` disc4 `1072 -> 1233 (+161)`；`:55` `[rc=0]`。
- 盘上实际行（`grep` 实测）：`anchor_check.txt:23` disc3 at=17:39:19；`:24` disc4 **at=17:40:02**；`should_exclude.tsv:1470` disc22 at=17:39:19；`_verdicts.tsv:1244` disc27 at=17:39:19；`tier_final.tsv:4520` disc28 at=17:39:19。与 go/go2 逐字一致。
- 当前文件大小实测：anchor_check.txt=1233 B、should_exclude.tsv=244144 B、_verdicts.tsv=112713 B、tier_final.tsv=661259 B——与 `REPORT.md:29-33` 的「前→后」及 go/go2 的 +Δ 完全吻合。

**关键结论：** 两个时刻不是「执行员事后手写的自述」，而是两次脚本真实执行时 `datetime.now()` 打上的机器时刻，且有 dryrun→go→go2 三个单调递增的脚本输出与字节增量交叉佐证。lead 在任务卡里的核心担忧（"若 at 是事后手写的，我就是在为一个自述时间调整判据"）**事实层面不成立**。但诚实边界：这仍是本机时钟、无外部可信时钟（§2.51:4320、§2.58:4783），「自动」不等于「不可伪造」，见 Q4 实测。

## Q3 · 绕开根本问题

- 根本问题逐字：`R14_COMMON.md:4297-4299`（§2.51 四 FALSIFY 1）："**协同伪造**：行为者同时把第 7 列改「有」、并在产物里手写一条六字段全合法的自述行（discipline 对、`at` 晚于立条、`round` 在窗、anchors 按第 4 列重算）⇒ R1–R6 全过而从未回跑。"；`:4304-4305` "**未取得外部时钟前不得把 PASS 读作已证**"。
- §2.57 的动作只是挪窗口起点（`:4698`），没有引入外部时钟或独立凭证；§2.58:4783 "**理论上仍可同时改档与常量**。……**做不到真不可伪造**。"
- Q4 实测协同伪造 exit=0（下），证明根本问题原样存在。⇒ 绕开，不是解决。

## Q4 · 第三种伪造路径（§2.58 未测）实测退出码 + 完整复原

见 `R17_R95_T4_AUDIT57/q4_forgery_output.txt`（脚本 `q4_forgery_test.py` 写在唯一允许的审计目录内）。

- 基线：`--- GATE BEFORE(基线) exit=0 ---`，`ok=5 fail=0 frozen-unverifiable=12 claims-none=11`。
- 构造：非冻结纪律 11，产物追加一条全字段合法自述行 + col7 无→有；未改 `FREEZE_SHA256`/`ROUND_WINDOWS`/冻结档/`check_disc.py`。
- 实测：`--- GATE AFTER-伪造C exit=0 ---`，`ok=6 fail=0 frozen-unverifiable=12 claims-none=10`，`VERDICT: exit=0 ; 门禁仍绿，伪造未被抓`。
- 复原（逐字节）：三文件 `identical=True`，sha256 分别为 `39af22f0f65f9a123b90bfea767463d75bd1410c41e243bfd3dea752f67a1b8f`（DISC_RECHECK.tsv）、`42884d6202a90edcac0ec797a0b3132c5aeb2080096f8bcdf3353792193094c9`（checkC3_report.md）、`f957c97bb90ee83969c8042f45e0a3c5ed95ec9b50fcc164706b2d07dbf104c0`（check_disc.py）；`RESTORE ALL_OK=True`；复原后 `GATE AFTER-复原 exit=0`，`ok=5 fail=0 frozen-unverifiable=12 claims-none=11`。
- 该路径被 lead 自己在 §2.51:4297-4299 描述并「完全接受」，§2.58 的两条反控都没覆盖；§2.58:4782-4784 另自认可同时改档与 FREEZE_SHA256。⇒「两个反伪造方向都验证过」过头。

## 写入范围与未取得

- 仅写 `lead\next_re_20261117_r14\R17_R95_T4_AUDIT57\`（REPORT.md、q4_forgery_test.py、q4_forgery_output.txt、capture_selftest.py、q4_selftest_output.txt）。反控对被测文件的临时改动已全部逐字节复原并复跑核验。
- 未取得：r41 看板备份（§2.57:4738 记为永久不可验证）；外部可信时钟（§2.51:4320）；真正不可伪造的凭证定义（§2.57:4737）。
