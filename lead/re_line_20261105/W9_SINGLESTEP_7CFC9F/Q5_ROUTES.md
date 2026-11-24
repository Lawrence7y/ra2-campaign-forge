被核对象 = gamemd.exe + EXCEPT_SINGLESTEP_0x7CFC9F_20261019T1352.txt
gamemd.exe SHA256 = 73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476，字节数 = 4825360
EXCEPT 件 SHA256 = 6694b75e46a6e773e1d37c42b0b0de0545cc35eae5a8f5425502e17898aac251，字节数 = 26405
Engine 自证 = COVERAGE 99.998375677293% / IMAGEBASE 0x400000
回件时刻 = 2026-11-06 02:57:32

# Q5 · 目标② 下一步的候选路线（只给路线，不执行；零采样代码）

> TASK.md §2 Q5（:70-73）：基于 Q1–Q4 结论，给 2–3 条候选路线，每条写
> **需要什么数据 / 是否受 D-13 限制 / 代价**。本节**不写任何采样代码**、不执行任何路线。

---

## 0 · 定谳依据（Q1–Q4 结论的收敛，均带本次实跑或文件:行）

Q5 不是脱离前四项的空想，先把「路线为何长这样」钉死：

| 来源 | 结论 | 对「下一步」的约束力 |
|---|---|---|
| **Q1**（CONFIRMED） | `0x7CFC9F` = 2B `8B0A mov ecx,[edx]`，在重同步流内（`va in e.by()=True`），前 8 条 size-class 计算；磁盘 `e.rd(VA,32)` 与 EXCEPT L17 32/32 零差异 | 代码本身**没有可修的字节错误**；「继续分析这条指令」不再产生新信息 |
| **Q2**（CONFIRMED） | 函数 `__sbh_alloc_block` 起 `0x7CFB13`–`0x7CFE1B`（唯一 ret）、0x309 B / 275 指令；在 `docs/re`、`lead`、`crashspec*` 被密集分析过 | 「未覆盖的新函数」这条路已否定，别再开反汇编支线 |
| **Q3**（PARTIAL） | 「TF=0 却单步」是假悖论；`0x286` 是异常帧 `CONTEXT.EFlags`；③游戏自抛被字节排除，①②（TF / DR-exec）**因本件无 DR6/DR 字段无法定谳**；`Esi/Edi` 只是 class=1 小分配的普通态 | 想「定谳 #DB 机制」必须补 **DR6/DR0-3/DR7/trap-frame EFlags** 这类本件没有的数据 |
| **Q4**（REFUTED） | 本 EXCEPT 件 = 全仓 **113 份** `except_post_*.txt` 的同一份基线残件（113/113 同哈希 + 逐字节相同）；harness `copy_post_except_evidence` 在 `finalize_trip` 的 `finally` 收尾项**无条件复制**载体 `except.txt`；最早快照早于声称崩溃约 2 天；旧分析把它当真实 #DB 现场作机制定谳属实质错误 | **目标② 目前没有一件「把某次异常归因到某趟游戏运行」的证据**。第一要务不是再分析崩点，而是**重定位观测/证据** |

**本次会话独立复核（不采信前置回件文字）**——命令与输出见 §5：

- `python -I -X utf8 …\_w9_q5.py` → `EXIT=0`；自算 exe/except 两个 SHA256 与头部一致；
  `Engine()` 真跑 `COVERAGE 99.998375677293% / 1394120 insns / 66 resync-fails`；
  `e.rd(0x7CFC9F,32)` 32/32 与 L17 一致；`e.by()` 命中 `8b0a size=2`；
  `e.disasm(VA,0x30)` 18 条，前 8 条与 Q1 同；`e.func_rets(0x7CFB13,0x7CFE1C)` ret 数=1 @`0x7CFE1B`。
  （`_w9_q5_out.txt`）
- `/usr/bin/find . -name 'except_post_*.txt' | xargs sha256sum | … | uniq -c` →
  `113 6694b75e…a8c251`（113/113 同哈希）；`wc -l` → `113`。
- `stat` EXCEPT 件 mtime `2026-10-19 13:54:38`；最早 `except_post` mtime
  `2026-10-17T08:14:58`（`archive_T5/…081458810997.txt`）；最晚 `2026-11-04T18:26:58`。
- 源码亲读：`qc151_trip.py:4561-4599` `copy_post_except_evidence`（`blob=src.read_bytes()` →
  `dst.write_bytes(blob)`，文件名=`except_post_<复制时刻>`，与「是否发生异常」无关）；
  `:6042-6052` 在 `run_guarded_steps` 第 1 项、`:7117` 位于 `main()` 的 `finally`；
  `:672-708` `except_set_diff` 以「新增含 `Exception occurred at` 的行」判新异常；
  `:228-230` `EXCEPT_MASTER = ra2bench/except.txt`（`ca175a71…`，26,515 B，AV@`0x6F9DB6`）。

**★ 一条校正 Q4 叙事边界的实跑事实（本节自己算的，非引用）**：
Q4 证「这份 SINGLE_STEP 件是残件」，但**不等于目标② 全部证据都是残件**。
全仓 `except*.txt`/`*.final_isolated` 共 **20 个 distinct 哈希**；其中

- `6694b75e…`（SINGLE_STEP 基线）**206 份** —— 被复制的残件（[H] 命名口径下的计数）；
- `b42c7014…`（**RC-1 AV@`0x7CFC9F`，`Edx=FE00FFFF`，26,830 B**，
  `out/re_work/zcode_live/zc11/evidence/closeout/except.txt.final_isolated`，
  `RC_SPEC_V4.md:51,57-62` 记 mtime 2026-09-29 22:38:24）在 [H] 的
  `except*.txt`/`*.final_isolated` 口径下**仅 1 份**；另 1 份同哈希件
  `except.txt.ra2bench.zc11_window`（文件名不以 `.txt` 结尾、不在该 glob 内）由
  本次直接 `sha256sum` 命中（[I]）⇒ **本次核到的同哈希文件共 2 个**（非全仓全扩展名
  绝对计数）。**不是 113 份那种残件**，但「它是不是一次真机原生崩溃」本次未验（见下）。

⇒ 目标② 的**代码侧根因链**（UAF 写穿 freelist `next` 槽 → 毒指针 `FE00FFFF` 被
`mov ecx,[edx]` 解引用）来自 `RC_SPEC_V4.md` 那条**独立**证据，与本次被推翻的 SINGLE_STEP 件
是**两件不同的 except 文本**（不同哈希/不同字节数/不同异常码/不同 Edx）。
**但这条证据本身是不是真机原生、有没有被同一套 harness 污染，本次未验**（见 §4 未验）。
这条区分直接决定下面三条路线的排序。

---

## 1 · 路线 A（推荐 · 纯静态 · 立即可做）：先修「观测/证据链」，再谈崩溃

**做什么**（只描述路线，不执行）：
把目标② 的锚点从「`0x7CFC9F` 指令流」整体移到「**证据是怎么产生、怎么被复制、哪些 except 件
是真的**」。具体三步，全部是磁盘文本/源码/哈希比对：

1. **坐实基线来源与复制链**：读 `qc151_trip.py` 的 `reset_except_from_master`（:616-666）、
   `copy_post_except_evidence`（:4561-4599）、`except_set_diff`（:672-708）、`finalize_trip`
   （:5900, :6042-6052, :7117），把「跑前从只读母本复位 → 跑后无条件另存 → 集合差判新异常」
   三段串成一条可复核链；确认 Q4 已证的「113 份同哈希」是**设计/缺陷**而非重复崩溃。
   （`PENDING_DECISIONS.md:65-67` 的 A 项已把这一步列为「先修观测」，本节与之一致。）
2. **给全仓 except 语料做 provenance 分档**：以哈希为主键，把 20 个 distinct 哈希按
   「异常码 / EIP / Edx / 份数 / 最早 mtime / 是否来自 harness 复制」归档，明确分出
   (i) `6694b75e…` 残件类、(ii) `b42c7014…` RC-1 类、(iii) `ca175a71…` ra2bench 母本类、
   (iv) 其余 17 类（含 3 份 `e369a911…`、3 份 `584069ad…` 等多副本件，性质待定）。
3. **闭合 §555 诚实账第 3 条**（`GOAL_THREE_TARGETS_20261018.md:5570`）：逐趟读 37 个
   archive 的 `except_set_diff.json` / `qc151_run_log.json` / console / error.txt，
   独立验证「37 趟零游戏崩溃」到底成立到什么程度；本节已实跑
   `find … -name 'except_set_diff.json'` = **68 份**，`new_exception_count` 聚合 **68 份全为 0**
   ——这只是**必要条件的一个面**，不等于逐趟 console 已核。

**需要什么数据**：`gamemd.exe`（已自证）、EXCEPT 件与全仓 `except*.txt`（已在盘）、
各版本 harness 源码（`qc151_trip.py` 及 `W5_HARNESS_EXT` 副本）、37 个 archive 的
`except_set_diff.json` / `qc151_run_log.json` / console / error.txt、`RC_SPEC_V4.md` 证据索引、
两套母本（`ra2bench/except.txt` 与 `_src_L3_sf10c_20261021/except.txt`）。**全是仓内既有静态文件。**

**是否受 D-13 限制**：**不受**。`PENDING_DECISIONS.md:67` 明写「本条纯静态、不需真机、
不受 D-13 限制」；`PENDING_DECISIONS.md:301-302` 的禁令针对
`E3 / MiniDump / SuspendThread / StackWalk / 真机发射 / 活进程采集` 及「相应采样候选代码」，
本路线不写采样代码、不启动游戏、不读活进程。**E3 维持暂停（D-13）不变。**

**代价**：最低。纯文本/源码/哈希，零真机、零注入、零授权门槛，一轮静态普查即可交付
「证据分档表 + 观测链结论」。**局限**：它只能回答「手上有没有可用证据 / 证据可不可信」，
**不能产出一次新的真实崩溃样本**，也不能定谳 #DB 机制；若结论是「证据链确已污染」，
目标② 仍需走 B 或 C 才有新数据。它同时是 B/C 的**前置**（`:73-74` 明示：harness 写入
逻辑不修，新抓的证据仍会被同样污染）。

---

## 2 · 路线 B（静态 · 重估 RC-1 根因链的证据强度）：把 ② 的「真崩溃」锚点换到 AV 件上独立定谳

**做什么**（只描述路线，不执行）：
Q1/Q2 已把 `0x7CFC9F` 的代码与函数钉死，Q3 已给 ①② 的判别判据、Q4 已推翻 SINGLE_STEP 件。
目标② 真正还站得住的崩溃叙述是 **RC-1 AV**（`RC_SPEC_V4.md:16,51,57-62,95-113`）：
`Edx=FE00FFFF` 毒指针 → `mov ecx,[edx]` 解引用 → UAF 写穿 freelist `next` 槽；
修复侧已有 PW-1 守卫补丁设计（`0x7CFC9B` 6B 窗，`RC_SPEC_V4.md:18,20`）与
`lead/goal2_sbh_guard_20261020/` 交付件。路线 B = **不新增任何采样**，只做静态证据重估：

1. 用 `Engine` 复核 RC-1 现场字节与磁盘一致（`RC_SPEC_V4.md:74` 记 `identical=True`，
   本次 W9 各探针已自证 `e.rd(0x7CFC9F,32)` 32/32；RC-1 件的 L17 同样是这 32 字节——
   我本次亲读 `except.txt.final_isolated` 头部，:62 与 EXCEPT 件 :17 字节串相同）。
2. 重算「`FE00FFFF` 在映像内 imm32 零命中」「`0x7CFD30/0x7CFD39` 摘链写点」等
   `RC_SPEC_V4.md:85,99-101` 的静态断言（限定地址窗口的 `e.disasm` / `disp_hits`，非全仓遍历）。
3. **关键新问**：`except.txt.final_isolated`（`b42c7014…`）与 `except.txt.ra2bench.zc11_window`
   （同哈希）到底是「一次真机崩溃的两个副本」还是「同一模板的两次复制」——
   按 Q4 的方法核其 mtime、复制链、上游 `except.txt` 哈希、以及它是否进过 `except_post_*`。
   **本次只证「它不是 6694b75e 残件、命中 2 个同哈希文件（非 113 份那种残件）」，
   未证其真机原生性，也未做全仓全扩展名的绝对计数。**
4. 顺带闭合 Q3 遗留的「② RC-1 现场 `Esi` 同为 `0x7FFFFFFF`」（`Q3_MECHANISM.md:388-390`
   标未验），把两条 `0x7CFC9F` 现场（AV / SINGLE_STEP）的寄存器语义对齐，避免旧分析
   `SINGLESTEP_0x7CFC9F_ANALYSIS.md:45` 的 class 勘误被误引。

**需要什么数据**：`except.txt.final_isolated` 及同哈希窗口副本、`RC_SPEC_V4.md` /
`UAF_WRITER_REPORT.md` / `sbh_freelist_deep_dive.md` 的实证段、`gamemd.exe`（`Engine` 重反汇编
`0x7CFB13–0x7CFE1B` 与 `0x7CFD30/0x7CFD39` 窗口）、`goal2_sbh_guard_20261020/` 补丁件、
PW-1 相关历史探针产物（`RC_SPEC_V4.md:44` 的 `except_U0050_pilot1_isolated.txt` 等，
用于剔除「插桩产物 ≠ 自发崩溃」）。**全是仓内既有静态文件。**

**是否受 D-13 限制**：**不受**（纯静态 `Engine` + 磁盘读，同 A）。
但**有另一道闸**：`PENDING_DECISIONS.md:301-302`、`:248-250` 的 D-13/D-16 暂停覆盖的是
「采样代码/真机/活进程采集」，本路线不触碰；若要**实施/验证 PW-1 守卫补丁**则超出「只给路线」，
且属改既有件（TASK §6 禁止改 `ra2youli/` 等），须另案授权——**本节不写补丁、不改任何既有文件**。

**代价**：低-中。静态可复核，但 `crashspec` 语料本身厚（`RC_SPEC_V4.md` 113+ 行实证、
`UAF_WRITER_REPORT.md` 多轮），逐条重算需若干轮 `Engine` 有界窗口扫描（单次约 1–2 min，
Q1–Q4 探针实测 62–140 s）。**局限**：它只能**加强/削弱既有 RC-1 叙述**，
仍不产生新崩溃样本；`RC_SPEC_V4.md:16` 自陈「具体写点 VA 未指认」，
静态面无法补出「谁写穿了 next 槽」——那需要运行期数据（C）。

---

## 3 · 路线 C（受 D-13 限制 · 需用户明示授权）：修好观测后，另起一趟「可信的新崩溃证据」

**做什么**（只描述路线，不执行；**本节不写任何采样代码**）：
A 修好观测链之后，若目标② 仍要拿「一次真实、可归因到某趟游戏运行的崩溃」，
唯一能补 Q3/Q4 缺口的数据是**运行期证据**。两条子路，任一都**先过授权**：

- **C1（不侵入，仅被动读 + 修 harness）**：在已修 `copy_post_except_evidence` /
  `except_set_diff` 的前提下发一趟，靠游戏自身的最后机会过滤器写 `except.txt`
  （`Q3_MECHANISM.md:163-165` 已证该文本来自异常 `CONTEXT`），
  以「跑前母本哈希 + 跑后 `except_post` 哈希 + `new_exception_count` + 时间戳」四元组
  证明「这份 except 是本趟新产生、不是模板复制」。**不写 hook、不注入、不挂线程。**
  这能补 Q4 的归因缺口，但**仍拿不到 DR6/DR0-3**（except.txt 格式里没有这些字段，
  `Q3_MECHANISM.md:243-247` 全文零命中），所以**不能定谳 ①/② 的 #DB 机制**。
- **C2（侵入性，明确属 D-13 管）**：若要回答 Q3 的 `DR6.BS vs B0..B3`、
  trap-frame 原始 EFLAGS、崩溃线程 `DR0-3/DR7`，需要崩溃态全量 CONTEXT / dump
  （旧分析 `SINGLESTEP_0x7CFC9F_ANALYSIS.md:98-105` 的 E1/E3 正是此类）。
  `PENDING_DECISIONS.md:154-177, 301-302` 明列 `E3 / MiniDump / SuspendThread / StackWalk /
  真机发射 / 活进程采集` **一律暂停，未经用户明示授权不得执行、也不得编写相应采样候选代码**。
  ⇒ **C2 在本轮不可提、不可写、不可执行，只能登记为「待 D-13 另裁 + 用户明示授权」的挂账项。**

**需要什么数据**：
- C1：修好的 harness 源码 + 一趟真机运行的 `except.txt` 前后件哈希、`except_set_diff.json`、
  `qc151_run_log.json`、`final_exit`、console；（**仅需被动读盘，不读活进程内存**）。
- C2：崩溃进程全量 `CONTEXT`（含 `Dr0-3/Dr6/Dr7` / `CONTEXT_DEBUG_REGISTERS`）、
  `EXCEPTION_RECORD.ExceptionInformation/NumberParameters`、可信的崩溃态 dump
  （`Q3_MECHANISM.md:426-435` 未验清单）。**这些正是本件/仓内 except 文本全部缺失的字段。**

**是否受 D-13 限制**：
- **C1：受**（真机发射）。`PENDING_DECISIONS.md:72` 把「申请真机趟专抓崩溃」明确写为
  「需用户明示授权、受 D-13 约束」；`:248-250`、`:301-302` 要求候选代码与指定批次真机/采集
  **分别授权**。它不写采样代码，故不触 D-13 的「不得编写采样候选代码」条款，
  但**真机发射**这一动作在暂停面内。
- **C2：完全受 D-13 且当前被禁**（`E3 / MiniDump / SuspendThread / StackWalk`）。
  `PENDING_DECISIONS.md:171` 现处置为「**(暂停)** E3 暂不执行」；`:176` 证据件
  `E3_FOR_GOAL1_CARD_20261103.md` 等原文零改动。
- 两条子路**都不放宽 D-13**（`:77`「不因为本条而放宽 D-13」）。

**代价**：最高。①需用户当轮明示授权（C1 一趟 / C2 另裁）且无时间表（`PENDING_DECISIONS.md:70`
B 项「暂挂」的代价同源）；②C2 的 E3 方案自述「**可能自造死锁**」、会污染目标② 的
正常退出读数（`:169-172`）；③`:73-74` 的硬前提——**harness 写入逻辑没修，新抓的证据仍会
被同样的 `except_post` 污染**（即必须先做 A）；④即便全跑通，也只能回答「这次崩没崩 /
什么机制」，**不自动等于找到 UAF 写者**（`RC_SPEC_V4.md:16` 写点 VA 仍未指认）。

---

## 4 · 排序与「未验」边界（不许补造）

**推荐顺序：A →（按 A 的结论选）B 或 C1；C2 挂账等 D-13 另裁 + 用户明示授权。**
理由：Q4 已废掉唯一「有异常上下文」的锚点，Q3 判 ①② 缺 DR 字段不可定谳，
Q1/Q2 判崩点代码/函数无新信息 ⇒ **先修观测（A）是所有后续路线的公共前置**
（`PENDING_DECISIONS.md:65-67, 73-74` 同此判断）。B 是「不花真机把 ② 的静态根因链
重估一遍」的低成本续命；C1/C2 才补新样本，但都要授权。

**本路线书未验 / 不把「查不到」当「不存在」**（TASK.md:109-110）：

1. **RC-1 AV 件（`b42c7014…`）是否真机原生、是否被 harness 复制过** —— 本次只证
   「≠ 6694b75e 残件、命中 2 个同哈希文件（非全仓全扩展名绝对计数）」；其 mtime 链 / 上游 `except.txt` / 是否进过
   `except_post_*` **未逐份核**（属路线 B 第 3 步）。不得写成「已证是真崩溃」。
2. **37 个 archive 逐趟 console / 有无别的崩溃形态** —— §555 诚实账第 3 条
   （`GOAL_THREE_TARGETS_20261018.md:5570`）仍未闭；本次只实跑 68 份
   `except_set_diff.json` 全为 `new_exception_count=0`，**不等于逐趟已核**。
3. **除 20 个 distinct 哈希外的其它异常证据（WER `LiveKernelEvent 193/0x80e ×2`，
   `ROUND_SUBAGENT_LOG:1964`；dump / 截图 / 非 `except*.txt` 命名的件）** —— 静态未全面普查，
   记未验；`Q4_RELATION.md:243` 亦把 WER 记未验。
4. **两个基线母本（AV@`0x6F9DB6` 的 `ra2bench/except.txt` vs
   SINGLE_STEP@`0x7CFC9F` 的 `_src_L3_sf10c_20261021/except.txt`）各自的来源与写入时序**
   —— 本次只确认两者哈希/首行/字节数不同（`ca175a71…`/26,515 B vs `6694b75e…`/26,405 B），
   来源未验（`Q4_RELATION.md:246` 同登记）。
5. **Q3 的 `DR6 / DR0-3 / DR7 / CONTEXT 全文 / ExceptionInformation`** —— 本件零命中，
   静态不可得；**C1 也拿不到**，只有 C2 能补，而 C2 被 D-13 暂停。
6. **「游戏是否会崩」** —— 不能由 Q4 结论推出；本节只说现有 `except_post` 语料无信息量
   （`GOAL_THREE_TARGETS_20261018.md:8541`）。
7. **Q1/Q2/Q3/Q4 四份回件本身** —— 本项只按任务书「基于 Q1–Q4 的结论」使用，
   不复核、不反驳其定谳；仅对 §0 标「本次独立复核」的字节/SHA/源码/哈希数字自负。

---

## 5 · 本次实跑命令清单（每个数字可追）

| 编号 | 命令（`python -I -X utf8` + 绝对路径；其余为 Git-Bash 静态命令） | 关键输出 |
|---|---|---|
| [A] | `python -I -X utf8 …\W9_SINGLESTEP_7CFC9F\_w9_q5.py` | `EXIT=0`；`_w9_q5_out.txt`。自算 exe/except SHA + `Engine()` 真跑：COVERAGE `99.998375677293%` / `1394120 insns` / `66 resync-fails` / IMAGEBASE `0x400000`；`e.rd(0x7CFC9F,32)` 32/32 与 L17 一致；`0x7CFC9F in e.by()=True`（`8b0a size=2`）；`e.disasm(VA,0x30)` 18 条；前 8 条 `mov ecx,[edx] / sub ecx,[ebp-0x10] / mov esi,ecx / mov [ebp-8],ecx / sar esi,4 / dec esi / cmp esi,0x3f / jle 0x7cfcb5`；`e.func_rets(0x7CFB13,0x7CFE1C)` ret 数=1 @`0x7CFE1B`；函数长 `0x309/0x308` B；前序 `0x7CFC9B 8b54f904` 末址=`0x7CFC9F` |
| [B] | `/usr/bin/find . -type f -name 'except_post_*.txt' -not -path './.git/*' -print0 \| xargs -0 sha256sum \| awk '{print $1}' \| sort \| uniq -c` | `113 6694b75e…a8c251`（113/113 同哈希） |
| [C] | `/usr/bin/find . -type f -name 'except_post_*.txt' -not -path './.git/*' \| wc -l` | `113` |
| [D] | `stat -c '%y %s %n' <EXCEPT>` + `find … -printf '%TY…%p\n' \| sort \| head -3` / `tail -1` | EXCEPT mtime `2026-10-19 13:54:38` / 26405 B；最早 `2026-10-17T08:14:58` `archive_T5/…081458810997.txt`；最晚 `2026-11-04T18:26:58` |
| [E] | `grep -n` + `Read` `qc151_trip.py:4561-4599, 6042-6052, 7117, 672-708, 228-230` | `copy_post_except_evidence` 无条件 `read_bytes→write_bytes`；`run_guarded_steps` 第 1 项；`main() finally`；`except_set_diff` 判据；`EXCEPT_MASTER` 哈希 |
| [F] | `/usr/bin/find . -name 'except_set_diff.json' \| wc -l`；`xargs grep -h '"new_exception_count"' \| sort \| uniq -c` | `68` 份；`68 "new_exception_count": 0` |
| [G] | `sha256sum except.txt.final_isolated` + `wc -c` + `head -17` | `b42c7014…5870` / `26830` B / `EXCEPTION_ACCESS_VIOLATION` `Access address:FE00FFFF` `Edx:FE00FFFF` `Esi:7FFFFFFF Edi:4` `EFlags:00010286` |
| [H] | `find except*.txt / *.final_isolated \| xargs sha256sum \| sort \| uniq -c \| sort -rn` | `206 6694b75e…`；`1 b42c7014…`（该 glob 口径）；`3 e369a911…`、`3 584069ad…`；distinct 哈希 `20`（`sort -u \| wc -l`）。`except.txt.ra2bench.zc11_window` 因不以 `.txt` 结尾不在此 glob，另见 [I] |
| [I] | `sha256sum except.txt.ra2bench.zc11_window`；`sha256sum except_crash_r1off_nr.txt`；`sha256sum ra2youli/except.txt` | `b42c7014…`（同 RC-1，26830 B）；`e5ed1a45…`（26650 B，AV@`0x7C9B92`）；`584069ad…`（27631 B，AV@`0x724737`，`:40` RC-2 现场）——**`RC_SPEC_V4.md:41` 的「与上同 sha256」按当前盘面字节未复现（三件互不同哈希）；该措辞所指对象本次未追，记未验** |
| [J] | `sha256sum ra2bench/except.txt` + `head -6` + `wc -c`；`sha256sum _src_L3_sf10c_20261021/except.txt` | `ca175a71…f39d` / `26515` B / AV@`0x6F9DB6` `Access address:00000030`；`6694b75e…a8c251`（L3 模板母本） |
| [K] | `find lead/goal2_sbh_guard_20261020 -maxdepth 1 -type f`；`grep -n 'FE00FFFF\|0x7CFC9F' crashspec_v4/RC_SPEC_V4.md` | 4 件（含 `sbh_guard.diff` / `RECEIPT.md`）；`RC_SPEC_V4.md:16,18,20,41,51,57-62,74,85,95-113` |

**铁律遵守**：零真机（未启动 gamemd.exe / ra2loader / YURI.exe，未 taskkill，未读活进程内存）；
零采样代码（未写 hook / MiniDump / SuspendThread / StackWalk / 探针注入；**E3 维持暂停 D-13**；
本节三条路线**均不含采样代码**，C2 更明确列为「不可写、不可执行」）；只读
`ra2youli/`、`out/re_work/…`、`lead/GOAL_*`、现场台账、W1–W8 既有件；
唯一写域 `W9_SINGLESTEP_7CFC9F/`（本次仅新增 `Q5_ROUTES.md` + `_w9_q5.py` / `_w9_q5_out.txt`）；
Python 全部 `python -I -X utf8` + 绝对路径；不 commit / 不 push；
不改任何既有文件。探针 `[A]` 单次 EXIT=0 自退出（< 8 min）。

---

## 6 · 判定档

**Q5 是「只给路线、不执行」的规划题**（TASK.md:70-73），不产生新的字节级事实定谳，
故不套 §4 的 CONFIRMED/PARTIAL/REFUTED 三分档；本回件的可核性建立在
§0 强制头部（自己实算）+ §5 实跑命令 + 每条路线的「数据/D-13/代价」三字段齐备。
按 Q1–Q4 的收敛，**Q4 的 REFUTED 是本节全部路线的起点**：目标② 必须重新定位观测，
而非继续分析 `0x7CFC9F` 的指令。
