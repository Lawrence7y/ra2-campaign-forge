# W9 汇总判定书 · `EXCEPTION_SINGLE_STEP @ 0x7CFC9F` 静态定谳

> 汇总对象：五项回件 `Q1_CODE.md` / `Q2_FUNCTION.md` / `Q3_MECHANISM.md` / `Q4_RELATION.md` / `Q5_ROUTES.md`
> ＋ 五道独立复核 `reviews/Q1_review.md` … `reviews/Q5_review.md`。
> 依据：`TASK.md:35-96`（五项问题、判定档、交付物）、本汇总员在本会话实跑的命令与亲读的文件行。
> 铁律：零真机、零采样代码、零活进程读取；本次唯一写域 = `W9_SINGLESTEP_7CFC9F/`；未 commit / 未 push。

---

## 0 总判

**总判 = PARTIAL**（按本次任务的门槛规则逐条套用）。

判定档汇总表（「汇总采用」一律不高于复核档，复核判 PARTIAL/REFUTED 的项按复核意见降级）：

| 项 | 回件 verdict | 独立复核 verdict | 汇总采用 | 范围限定 |
|---|---|---|---|---|
| Q1 代码 | CONFIRMED | CONFIRMED | **CONFIRMED** | 仅「磁盘镜像 0x7CFC9F 处的代码身份 / 32 字节一致」；不证明 EXCEPT 件来源，更不证明 13:52 崩了 |
| Q2 函数 | CONFIRMED | CONFIRMED | **CONFIRMED** | 仅「函数归属与边界」；不涉及机制、不涉及异常真实性 |
| Q3 机制 | PARTIAL | PARTIAL | **PARTIAL** | ①② 不可判别；「这是一次真实 #DB」前提未验，只作文本内容静态分析 |
| Q4 与主崩溃关系 | REFUTED | **PARTIAL** | **PARTIAL（降级）** | 二选一「同哈希」成立；但「不是任何一趟的崩溃 / 历史基线残件 / 无一件归因证据」被仓内书面记录反证，不得写成已定谳 |
| Q5 路线 | CONFIRMED | **PARTIAL** | **PARTIAL（降级）** | 三条路线方向（A 首选）保留；起点断言、分档、行号引用、AV 行号均须改 |

门槛套用：`TASK.md:87-89`；本次规则「任一项 REFUTED ⇒ 总体至少 PARTIAL；有 PARTIAL ⇒ 总判 PARTIAL；全 CONFIRMED 才可 CONFIRMED」。
本表存在 Q3/Q4/Q5 三项 PARTIAL，且 Q4 回件原本为 REFUTED（复核降为 PARTIAL），故**总判只能是 PARTIAL**，不是 CONFIRMED。

**总判的三条落点**：
1. 静态代码面完全可靠：`0x7CFC9F` = `8B0A` `mov ecx,[edx]`，属于 `0x7CFB13–0x7CFE1B`（唯一 ret）函数；证据件 L17 的 32 字节与磁盘 32/32 零差异。
2. 机制面不可定谳：`0x286` 是**异常帧 CONTEXT.EFlags**（handler 从 `[ebp+0xC0]` 打印），`EXCEPTION_SINGLE_STEP=0x80000004` 覆盖整类 #DB；①② 因本件无 DR6/DR 字段而**未验**，③ 游戏二进制自抛被字节排除。
3. 证据来源面被改写：手上这件 EXCEPT 与 113 份 `except_post_*.txt` 逐字节相同；它**不是 2026-10-19 13:52 那趟**的产物，但仓内 `QC124_VERDICT.json:36,47-50,60-63` 书面记 `6694b75e…` 是 QC124 group2 人为 `DR0=0x007CFC9F` 断点命中后运行期写出的 `except.txt`（`PD:144` / `GOAL_THREE_TARGETS_20261018.md:9229-9290` §599 已订正）⇒ 精确状态是「**有一件人为注入断点造成的异常记录，无任何游戏自身崩溃证据**」，不是「历史基线残件」也不是「从未在任何一趟发生」。

**目标② 的主崩溃**是否**因本判定书而改变状态：未改变** —— 理由：本判定书没有修好主崩溃，也没有新增或撤销任何「游戏自身崩溃」证据；D-22=A 仍有效（`RULING_D22.md:3`）、E3 仍暂停、D-13 仍维持（`PENDING_DECISIONS.md:78-80,248-249`）。改变的是**证据归属与判定档**（该 EXCEPT 件由「13:52 真实 #DB 现场」改判为「QC124 人为断点产物＋其复制件」，总判降为 PARTIAL），而这一状态在 2026-11-06 的 `PD:144` 与 §599 已先行确立，W9 汇总只是追认并对范围作收窄。

目标② 的主崩溃**是否**因本判定书而改变状态：**未改变**；理由同上（无新增/撤销游戏自身崩溃证据，裁决与暂停状态未动，仅证据归属与判定档被订正）。

---

## 1 SHA256 绑定

两件被核对象，哈希与字节数均为**本汇总员本会话自算**（`sha256sum` + `wc -c`），并与五份回件头部及五道复核的独立实算一致：

- **gamemd.exe**（`ra2youli/gamemd.exe`）
  - SHA256 = `73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476`
  - 字节数 = `4825360` B（`4,825,360`）
  - 路径 / 期望值见 `TASK.md:18-21`；`ra2tool.py:28-29` 的 `EXPECT_SHA` 是 `Engine()` 构造内断言，不是头部数据来源（复核证据 Q2_review §1）。
- **EXCEPT 件**（`out/re_work/work_chain/CONTINUE_20261003/lead/boot_hang_triage_20261018/EXCEPT_SINGLESTEP_0x7CFC9F_20261019T1352.txt`）
  - SHA256 = `6694b75e46a6e773e1d37c42b0b0de0545cc35eae5a8f5425502e17898aac251`
  - 字节数 = `26405` B（`26,405`）
  - 路径见 `TASK.md:9`；mtime 实读 `2026-10-19 13:54:38.293170200 +0800`（`stat -c '%y | %s | %n'`）。

实跑命令与输出：

```
cd D:/Project/ra2-campaign-forge
sha256sum ra2youli/gamemd.exe && wc -c ra2youli/gamemd.exe
EX="out/re_work/work_chain/CONTINUE_20261003/lead/boot_hang_triage_20261018/EXCEPT_SINGLESTEP_0x7CFC9F_20261019T1352.txt"
sha256sum "$EX" && wc -c "$EX"
→ 73201cc0…f67476 *ra2youli/gamemd.exe ; 4825360 ra2youli/gamemd.exe
→ 6694b75e…a8c251 *out/…/EXCEPT_SINGLESTEP_…T1352.txt ; 26405 out/…/EXCEPT_SINGLESTEP_…T1352.txt
```

Engine 自证（本会话实跑 `python -I -X utf8 -c`，`sys.path` 指向 `lead/goal3t_nightwatch_20261102/swarm_20261104`）：
`IB 0x400000`、`COVERAGE (99.99837567729335, 1394120, 66)`、`fo(0x7CFC9F)=0x3cfc9f`（= VA−0x400000）。`ra2tool.py:51-55,76-88,91-123`。

**口径修补（复核意见，必须随绑定一起读）**：
- `Q1_CODE.md:29` 的「与 §555 所记 107 份哈希前缀相同」只是 8 位前缀、Q1 未跑 `except_post_*` 哈希，**不得**当作已建立的 SHA256 绑定；本节的绑定由上述实跑命令独立成立。
- `Q2_FUNCTION.md:8` 的「回件时刻 = 2026-11-06 01:28:18」是**正文成稿时刻**；探针运行时刻为 `_w9_q2_out.txt:2` 的 `01:20:23`，输出落盘 `01:22:16`（Q2_review §Objection 1）。
- `Q1_CODE.md:20/:237` 的「235 行」应为 **236 行**（`wc -l _w9_q1_out.txt` = 236；`PROBE DONE -- exit 0` 在第 235 行，疑把行号当总数）；`:24` 的「1046 行」是 `splitlines` 口径（实测 `LF=1045 / CR=1046 / CRLF=1045 / loneCR=1 / wc -l=1045`）。仅为口径问题，不改 Q1 结论。
- 行号口径：EXCEPT 件的 `Bytes at CS:EIP` 在 `grep -n` / `LF` 口径是 **L17**，在 `splitlines` 口径是 L18（L17 为空行）。本文统一声明「EXCEPT L17」= `grep -n` 口径。

---

## 2 Q1 代码

**Q1 = CONFIRMED（仅代码身份范围）**。

- 磁盘原始字节（本会话实跑 `e.rd(0x7CFC9F,32)`）：
  `8B 0A 2B 4D F0 8B F1 89 4D F8 C1 FE 04 4E 83 FE 3F 7E 03 6A 3F 5E 3B F7 0F 84 0D 01 00 00 8B 4A`
- 三方 32/32 零差异：正则提取 EXCEPT L17 的 32 字节 vs `e.rd(VA,32)` vs `TASK.md:40` 字符串 →
  `L17_bytes 32 rd32 32 EQUAL True diff_idx []`；`TASK40_EQUAL True`。
- 指令流：`e.disasm(VA,0x30)` 18 条，与 `e.by()` 重同步流窗口内 18 条**前 18 条 (addr,mnem,op_str) 全等**（`FIRST18_EQUAL True`），末址 `0x7CFCCF`。
- 前 8 条（本会话实跑）：
  1. `0x7CFC9F 8b0a` `mov ecx, dword ptr [edx]`
  2. `0x7CFCA1 2b4df0` `sub ecx, dword ptr [ebp-0x10]`
  3. `0x7CFCA4 8bf1` `mov esi, ecx`
  4. `0x7CFCA6 894df8` `mov dword ptr [ebp-8], ecx`
  5. `0x7CFCA9 c1fe04` `sar esi, 4`
  6. `0x7CFCAC 4e` `dec esi`
  7. `0x7CFCAD 83fe3f` `cmp esi, 0x3f`
  8. `0x7CFCB0 7e03` `jle 0x7cfcb5`
- `0x7CFC9F in e.by() = True`，`by()[VA] = 8b0a size=2`；本会话全流枚举 `IMM_TARGETS_TO_VA 0`（1,394,120 条指令中以 VA 为立即数的直接分支/调用落点 0 条），前序 `0x7CFC9B 8B 54 F9 04`（`mov edx,[ecx+edi*8+4]`，size 4）恰好结束于 `0x7CFC9F` ⇒ **顺序落下、非数据区、非直接 call/jmp 落点**。间接跳转表落点 Q1 与复核均标「未验」，不写成不存在（`TASK.md:109-110`）。
- 旧分析 `SINGLESTEP_0x7CFC9F_ANALYSIS.md:25-37` 的 14/14 字节流吻合；±32B 内 `0xF0@0x7CFCA3`（`2B 4D F0` 的 disp8）、`0xF1@0x7CFCA5`（`8B F1` 的 ModRM）**均非指令起始**（本会话 `by()` 查询 `NOT_START`），属措辞精度缺陷，非实质错误。

**CONFIRMED 的边界（Q1_review mustFix #1，必须写）**：
> 32/32 字节一致**仅证明该文本抄录自 gamemd.exe 的 `0x7CFC9F..0x7CFCBE`，不证明该 EXCEPT 件记录了一次真实发生于 2026-10-19 13:52 的异常**；证据件来源与「主崩溃」关系由 Q4 定谳（本项未验）。因此 Q1 CONFIRMED 与 §5 的 PARTIAL/判定并不冲突，不得把 Q1 读成「主崩溃锚点证据已验证」。

---

## 3 Q2 函数

**Q2 = CONFIRMED（仅函数归属范围）**。

- 最近函数序言 `0x7CFB13`：`e.rd(0x7CFB13,5)=55 8B EC 83 EC`（`push ebp; mov ebp,esp; sub esp,0x14`）；紧邻前 1 字节 `0x7CFB12=C3 ret`；前一函数尾声 `pop edi/esi/ebx, leave, ret`。
- 函数起 `0x7CFB13`，止 `0x7CFE1B`（`e.rd(0x7CFE1B,1)=c3`），`END(不含)=0x7CFE1C`；长度 `0x309=777 B`（含 ret）/ `0x308=776 B`（不含）；275 条指令；EIP 相对头 `+0x18C=+396 B`。
- `e.func_rets(0x7CFB13,0x7CFE1C)` 返回 1 条 ret（`0x7cfe1b [c3]`）。本会话另核：区间内 5 个 `C3` 字节为 `0x7cfb80/0x7cfba7/0x7cfbbb/0x7cfbd7/0x7cfe1b`，其中 `in_by` 仅 `0x7cfe1b`（4 个内部者是 `add ebx,0x14 (83 C3 14)` 的第 3 字节）。
- `e.rd(0x7CFE1C,8)=A1 94 8B B7 00 8B 0D 84` ⇒ 下一函数首指令 `mov eax,[0xB78B94]`；`0x7CFB13` 有 3 处直接 call xref（`0x7C9484 E8 8A 66 00 00` 本会话实读、`0x7D0FB6`、`0x7D33AB`）。既有命名 `__sbh_alloc_block`。
- 「未覆盖」被明确否定：Q2 用 10 种写法搜索（截 2026-11-06 01:22 时点数原始 80 / 净 66，`docs/re 10 / lead 56`；复核时点 A=109 / 净 71，多出 5 个是 02:25–03:07 后创建的 D22/PD 文件，`REMOVED=[]`）。净 66 中 6 份与 EXCEPT 件逐字节相同（基线残件副本），宜表述为「66 个含该 VA 的既有文件，其中 60 个非基线副本」（`reviews/_q2_review_redundancy_out.txt`）。`crashspec` 语料实位于 `out/re_work/.../crashspec{,v3,v4}/`。
- 旧分析 `SINGLESTEP_0x7CFC9F_ANALYSIS.md:43` 的三条 Q2 范围断言（入口 / 体 / 唯一 ret）逐字节复核一致 ⇒ Q2 范围内无实质错误。

**Q2_review 的两条补强/限定**：
- 「`0x7CFC9F in by()` ⇒ 非 call/jmp 落点」原论证跳步；本汇总员本会话补跑全流立即数目标枚举 `IMM_TARGETS_TO_VA 0`（复核 `reviews/_q2_review_counter_out.txt:1` 同结论），把该命题从推断升格为已证。
- `e.func_rets` 是 `[lo,hi)` 线性区间枚举（`ra2tool.py:216-218`），**不是 CFG 可达性证明**；运行期 hook / 间接跳转的运行期落点静态不可证，Q2_FUNCTION.md:368-370 已记未验。
- Q2 CONFIRMED 仅核函数边界，与 §5 的 Q4 判定并排不冲突（`Q2_FUNCTION.md:349-353,365-371` 已把机制/语义/Q4 列为未验）。

---

## 4 Q3 机制

**Q3 = PARTIAL**（回件与复核同档，不升级）。

**决定性前提**：`EFlags=0x286` 置位 `[1,2,7,9]` = reserved-b1 / PF / SF / IF；`TF(bit8)=0`、`RF(bit16)=0`、`VM(bit17)=0`、`IF=1`、`ZF=0`、`SF=1`（本会话实跑 `EF_0x286_bits [1, 2, 7, 9] TF False`；旧件 `:51` 把 SF 误标成 ZF）。
但打印的 `0x286` 来自**异常帧 `CONTEXT.EFlags`**：`e.rd(0x4C8C63,11)=8B 8D C0 00 00 00 8D 54 24 34 51` = `mov ecx,[ebp+0xC0]`，紧接 `e.rd(0x4C8C6E,5)=68 50 1E 82 00` = `push 0x821E50`（串 `EFlags:%08X`）；全组 10/10 寄存器取数偏移吻合 CONTEXT（Q3_review `_Q3_review_probe_out.txt:70-76`）。
异常码表 `e.rd(0x7E8840,16)=03 00 00 80 02 00 00 80 8D 00 00 C0 8E 00 00 C0`，`e.rd(0x7E8880,4)=04 00 00 80` ⇒ `0x80000004`；`0x7E8888=FF FF FF FF`（见 §7 必须改项 #10）。
⇒ **「TF=0 却单步」是假悖论**：`EXCEPTION_SINGLE_STEP` 覆盖整类 #DB，DR 执行断点不需 TF；`TASK.md:55` 的「TF=0 ⇒ 硬件单步不可能」只对 TF 子机制成立，且需附加「CONTEXT 保留陷阱前 TF」这个未验前提；`ROUND_SUBAGENT_LOG_TRIGOAL_20261017.md:1898` 的「无 TF ⇒ 非 DR 非调试端口」是非推论（DR 与 TF 正交）。

**四候选逐条给支持—排除判据**（不是只列可能性；统一边界：本件 `Dr0-Dr7 / DR6 / ExceptionInformation / NumberParameters / CONTEXT` 全文零命中，是「报告没印」，不是「寄存器当时为零」）：

| 候选 | 支持判据（满足才可判支持） | 排除判据（满足才可判排除） | 本件实测 / 结论 |
|---|---|---|---|
| **① `SetThreadContext` 置 TF 后又清掉** | 需 `DR6.BS=1`，或崩溃前采到 `EFlags.TF=1` 的活样本，或可核的外部 agent 调用记录 | 需 `DR6.BS=0 且 Bn=1`（⇒ 归 DR 系），或 trap-frame 原始 EFLAGS 显示陷阱前 TF=0 且 CONTEXT 未被改写 | 两类证据**全缺**（无 DR6 字段、零活进程、无 agent 日志）。时序兼容（`0x7CFC9B` 末址=VA、trap-after 成立、`Edx` 已载入）；静态面 `gamemd.exe` 导入表无 `SetThreadContext/GetThreadContext/SuspendThread/AddVectoredExceptionHandler/IsDebuggerPresent/DebugActiveProcess`（本会话全镜像计数全 0，仅 `RaiseException=2 / SetUnhandledExceptionFilter=2 / UnhandledExceptionFilter=4`）⇒ 若①成立施动者必在游戏进程之外，但身份零证据。**结论：不能支持也不能排除 ⇒ 未验**。注：「后又清掉」并非必要步骤（#DB 入口 CPU 清活 TF）；旧件 `:68` 的施动者名单属推测，不采信 |
| **② DR0–DR3 执行断点命中** | 需 `DR6.B0..B3` 置位、`DR0..3` 含 `0x7CFC9F`、`DR7` 对应 L/G 使能；fault-before 语义本件具备 | 需 `DR6=0 / BS=1`，或可信的崩溃态 `DR0-7` 全零读 | DR 值**全缺**，故两类判据都不能落实。**仓内有施动者书面记录**：`QC124_VERDICT.json:36` `single_bp {"name":"RC1","va":"0x007CFC9F","dr":"DR0"}`，`:47-50` `except_setdiff_new_lines=["007CFC9F"] / except_file_rewritten=true / except_post_sha256=6694b75e…`，`:60-63`  regs 与 EXCEPT L12-14 全等；但该记录**本次未独立复现**（零真机），只作静态书面证据。旧件 `:61` 把 `DR0-DR7=0` 判不可用是对的（那来自 `gamemd_crawl.dmp` 的 14:11 logo 趟，非 13:52 进程）。**结论：不能支持也不能排除 ⇒ 未验（与①并列开放）**；DR 数据读断点为同族第三变体，按 x86 约定 EIP 应指向 `0x7CFCA1`，倾向不符但无 DR6，不写死排除 |
| **③ `RaiseException(EXCEPTION_SINGLE_STEP,…)` 手工抛** | 需 .text 中 `call [KERNEL32!RaiseException]` 且实参含立即数 `0x80000004`，且 `CONTEXT.Eip` = call 之后那条指令、`ExceptionAddress` = RaiseException 返回地址 | 上述任一必要条件被字节反证即可排除「游戏二进制自抛」 | 本会话实跑 `CALL_RaiseException_IAT 2 ['0x7d2f92','0x7db8a0']`、`IMM_0x80000004_IN_TEXT 0`；调用点 1 模板 `0x7F9928` 首 dword `0xE06D7363`（MSVC C++ throw，`__CxxThrowException`）非 SINGLE_STEP；调用点 2 第一实参为运行时 `[ebp+0x10]`，静态无该常量来源；EXCEPT 栈返回链 `0x007C9489` = `call 0x7CFB13 @0x7C9484 +5`（本会话 `e.rd(0x7C9484,8)=E8 8A 66 00 00 6A 09 8B`），是一条正常分配链，栈上无 KERNEL32/RaiseException 帧。**结论：`gamemd.exe` 自身手工抛 0x80000004 ⇒ 排除（有字节依据）**。残口：外部施动者在本线程注入一次 RaiseException 不是本件能排除的（需先劫持线程，折回①/②），记为「未验且零支持证据」，只在 EXCEPT:20-38 部分栈窗口成立，属原始 dump 非符号化调用栈 |
| **④ 其它** | 逐子项：a) 异常码应为 `0x80000003` 且指令起始有 `0xCC`；b) 若 ICEBP/0xF1 造成 trap-after 且 EIP=VA，则 `0xF1` 必须是 `0x7CFC9E` 处的独立 1 字节指令；c) RF/VM/V86 相关需相应置位；d) handler 误报需异常码表与描述串不符；e) 镜像错位需 32 字节不符 | a–e 各自字节反证即可排除；f/g 需 DR6/DR7 或进程/端口/agent 日志，缺则未验 | a) 异常码表 `0x7E8840` 的 `0x80000003` 是独立表项，窗口内指令起始无 `0xCC` ⇒ **排除**；b) `e.rd(0x7CFC9E,1)=04`、`0x7CFC9E in by()=False`（是 `8B 54 F9 04` 的 disp8），`0xF0@0x7CFCA3` / `0xF1@0x7CFCA5` 均 `NOT_START` ⇒ **排除**；c) `RF=0 / VM=0 / CS=0x23` ⇒ **排除**；d) 表项 `0x7E8880=0x80000004` + 描述串 `0x820F74` 与 EXCEPT:1-3 逐字一致、`[ebp+0xB8]` 同源 ⇒ **排除**（查表循环本体未逐条反汇编，标局部未验）；e) 32/32 零差异 ⇒ **排除**（就本异常而言）；f) DR 数据/I/O 断点、DR7.GD ⇒ **未验**；g) 外部 agent 身份 / 调试端口 ⇒ **未验**。**④ 汇总：5 个子项字节排除，2 项未验；排除掉的全是「别的异常码 / 别的指令字节」，并未排除 #DB 的两个主流触发源** |

`Esi=0x7FFFFFFF` / `Edi=1` 不是任何陷阱候选特征值：本会话实读 `0x7CFB45 83 CE FF` `or esi,0xffffffff` + `0x7CFB48 D3 EE` `shr esi,cl` ⇒ 位图掩码（class_req=1，req 9–24B）；`0x7CFC68 33 FF` `xor edi,edi` + `0x7CFC95 47` `inc edi` 是位扫描循环、`0x7CFC9B 8B 54 F9 04` 用其作 class 索引；`[0x7CFB13,0x7CFC9F)` 窗口内 `0x7FFFFFFF` 立即数 0 条（仅 5 条 `0xFFFFFFFF`）。

**Q3 的两条边界（Q3_review 要求，必须写）**：
- Q3 正文 `:33-34/:228-231/:293/:320` 隐含「这次异常真实发生」，与 Q4 复核/`PD:144`/§599 相冲突；本汇总件把「本件是否是一次真实发生的异常」列为**未验**，Q3 全部机制判据只作**对文本内容的静态分析**，不是对 13:52 那趟 CPU 现场的定谳。
- `Q3_MECHANISM.md:13/:406` 的 `substantiveDefect=false` 与 Q4 的 REFUTED 互斥，只在「**字节级事实**」限定口径下成立（不得据此否认 §5 的实质错误），见 §7 #11。

---

## 5 Q4 与主崩溃的关系

★ 二选一（逐字写死）：**与 107 份 except_post 同哈希**。

**比对了几份**：本汇总员本会话实跑 `find . -path ./.git -prune -o -type f -name 'except_post_*.txt' -print0 | sort -z | xargs -0 sha256sum > /tmp/w9_posts_hashes.txt` → `wc -l = 113`，`cut -d' ' -f1 | sort | uniq -c` → `113 6694b75e46a6e773e1d37c42b0b0de0545cc35eae5a8f5425502e17898aac251`；尺寸分布 `113 26405`；另跑 `cmp -s` 循环 → `compared=113 differing=0`。
即**整仓比对 113 份，113/113 同哈希、113/113 逐字节全文相同、0 份不同、distinct 哈希数=1**。任务书/§555 的「107」是 `out/.../qc161_u0400_trip` 子树口径（本会话 `find …/qc161_u0400_trip -name 'except_post_*.txt' | wc -l` = **107**），整仓多 6 份；五道复核各自用 `find|sha256sum` 与 `cmp` 独立复现同一结果（`reviews/Q1_review.md` C-R6、`Q2_review.md` `_q2_review_hash_out.txt`、`Q3_review.md` §3、`Q4_review.md` C-R5、`Q5_review.md` C-R4/C-R5）。

**成立的部分（可定谳）**：
- 手上这件 EXCEPT **不是 2026-10-19 13:52 那趟的产物**：`stat` 实读 EXCEPT mtime `2026-10-19 13:54:38`，而 `archive_T5/except_post_20261017T081458810997.txt` mtime `2026-10-17T08:14:58.8125028000` 且与其逐字节全等（早约 2 天）；`qc151_trip.py:4561-4578` 的 `copy_post_except_evidence` 在载体 `except.txt` 存在时无条件复制（`:4575` 有 `if not src.exists(): return None` 守卫，故「无条件」应表述为「载体存在时无条件、不以本趟是否异常为条件」），调用点在 `:5939`，另见 `:6042-6052` / `main() finally`（`:7117`）。⇒ 旧分析 `SINGLESTEP_0x7CFC9F_ANALYSIS.md:12/51/89/92` 把该件当成 **13:52 那趟真实 #DB 现场**作机制定谳，这一条实质错误被推翻。

**不成立／必须收窄的部分（Q4 复核判 PARTIAL 的根据）**：
- 「**不是任何一趟的崩溃**」「**该异常从未在任何一趟发生**」「**历史基线残件**」「**目标② 目前没有一件把某次异常归因到某趟游戏运行的证据**」——全部被仓内书面记录反证，必须删除（`reviews/Q4_review.md:374-378` 逐条判 REFUTED）。
  `QC124_VERDICT.json:8` `answer_detail` 明写「挂 RC1 后命中 ⇒ 进程在挂点后 0.63 s 终止，载体 except.txt 记为 EXCEPTION_SINGLE_STEP @ 007CFC9F（= 我设的 DR0）。这是断点异常无人处理的必然后果，不是游戏本身的崩溃」；`:36` `single_bp {RC1, 0x007CFC9F, DR0}`；`:47-50` `except_setdiff_new_lines=["007CFC9F"] / except_file_rewritten=true / except_post_sha256=6694b75e…`；`:60-63` `regs_at_hit_from_carrier_dump` 与 EXCEPT L12-14 逐字全等（本会话比对 `Eip 007CFC9F / Esp 00F9C614 / Eax 0D94B7B8 / Edx 0E73276C / Esi 7FFFFFFF / Edi 00000001 / EFlags 00000286` 全等）。
  独立登记链：`VERDICT_T11.md:148`（`26,405 B / 6694B75E… / mtime 2026-10-16 19:21:11（qc124 观测趟运行期写出）`）、`ERRATA_EXCEPT_RESTORE.md:12,16,17`（`before` 同哈希同尺寸同 mtime；`reason` = 「漂移系 qc124 观测趟运行期写出」）；漂移实体 `qc164_a4_prep_20261017/raw/except.drift.6694B75E.26405B.bin` 本会话实算 `6694b75e…a8c251 / 26405 B / mtime 2026-10-16T19:21:11.8163891000`。台账订正见 `GOAL_THREE_TARGETS_20261018.md:9229-9290` §599 与 `PENDING_DECISIONS.md:144`：「**它既不是『历史基线残件』，也不是『游戏自身崩溃的证据』，而是一次人为断点造成的真实异常记录**」。
  ⇒ 正确结论限定为：**手上这件 EXCEPT 与 113 份 `except_post_*.txt` 是同一份字节；不是 13:52 那趟的产物；except_post 语料对判定该趟崩溃无信息量**。QC124 运行期写出这件事本次**零真机、未独立复现**，只静态读了仓内书面记录。
- 口径外反例（**不得**写「仓内 7CFC9F 异常证据全为同一残件」）：本会话 `find . -iname '*except*.txt'` = 259 份、`grep -l 'Exception occurred at 007CFC9F' --include='except*.txt'` = 211 份；其中 5 份 basename 非 `except_post_*` 且哈希不同，逐件实算：

  | 文件（carrier/） | SHA256 | B | Edx |
  |---|---|---|---|
  | `qc119_after_entry/carrier/except.txt` | `77f5a4cb1350ccc3e75bc375eb8cfa953906a59e84930479e1faec6ff4cb822f` | 26324 | `0E75276C` |
  | `qc120_entry_then_arm/carrier/except.txt` | `27eef06bca05fa7d4aeecf3d63b291265e3250d0d9672544eea4e10e47778ce0` | 26459 | `0E74276C` |
  | `qc121_entry_then_arm/carrier/except.txt` | `ca1acc378bf6cee0e3fe056842c8a40aeeabbfb9d57703433290b7a98c1ed05f` | 26468 | `0EFA276C` |
  | `qc123_rc1_only/carrier/except.txt` | `94656085fbd0ef81a730d5258307c8af76fd92cdfcc10dcd3eddd6c6277e5d33` | 26621 | `0E7EA76C` |
  | `qc124_observe_chain/_backup/except_pre_qc124.txt` | `ca1acc378bf6cee0e3fe056842c8a40aeeabbfb9d57703433290b7a98c1ed05f` | 26468 | `0EFA276C` |

  均为 `EXCEPTION_SINGLE_STEP @ 007CFC9F`、`Esi=7FFFFFFF / Edi=00000001`，但 Esp/Eax/Edx 与栈 dump 各异，mtime 2026-10-16 ⇒ 它们是**独立的同地址 SINGLE_STEP 记录**，不是 `6694b75e…` 基线。这 5 件的来源/写入时序/是否真捕获本汇总员**未验**，只列事实。
- 其余被复核纠正的 Q4 措辞：`_src_L3_sf10c_20261021/except.txt` mtime `2026-10-17T22:16:07` **晚于** drift 实体 `2026-10-16T19:21:11` 和最早副本 `2026-10-17T08:14:58`，是**后续副本**而非「历史固有基线母模板」；107 份子树 mtime 实为 `2026-10-17T08:14:58 .. 2026-11-04T18:26:58`、`-newermt '2026-10-18 04:41' ! -newermt '2026-10-19 22:39'` = 44/107，§590 的「42 小时」不能归因为单子树口径；「TF/DR 施动者全部失去观测基础」不成立（QC124 书面记录支持 DR0 施动者）。
- 判定档：**Q4 回件 REFUTED 降为 PARTIAL** —— 二选一与「13:52 非本趟产物」成立，但 REFUTED 依赖的全局性断言被反证；不得按 confirmed 写。

---

## 6 Q5 路线

**Q5 = PARTIAL（降级）**。三条路线的**方向与 A 首选保留**（`RULING_D22.md:3` 已定谳 D-22=A，`PD:144` 明写「裁决本身（A）不受影响」），但 `Q5_ROUTES.md:23,192,252` 把「目标② 目前没有一件把某次异常归因到某趟游戏运行的证据」「Q4 的 REFUTED 是本节全部路线的起点」当作起点，须按 `PD:144` / §599 的精确表述替换；三条路线均**零采样代码**（`TASK.md:73,102`）。

| 路线 | 需要什么数据 | 是否受 D-13 限制 | 代价 |
|---|---|---|---|
| **A（推荐）先修观测/证据链** | 静态读 `qc151_trip.py:4561-4599,5939,6042-6052,7117` 的复制链与 `except_set_diff` 判据（`:672-708`）；按 `6694b75e…` 的 provenance 分档：不是「(i) 残件类」，而是**「QC124 人为 DR0 断点产物 + 其复制件」**；补 `QC124_VERDICT.json:8,36,47-50,60-63`、`VERDICT_T11.md:148`、`ERRATA_EXCEPT_RESTORE.md:12,16,17`、drift bin 实算哈希/字节/mtime、§599、`PD:144` | **纯静态、不受 D-13 限制**（`D22_RULING/TASK.md:29`）；但把 W11 离线候选应用到**正式 harness 仍需用户授权**（`RULING_D22.md` nextSteps 第 5 条、`PD:144`） | 最低，但须扣除**已做部分**：`RULING_D22.md:3,30-35`（02:31 已裁 A 并列 5 步 nextSteps）、`PD:144`/§598（W11 `dwfrun-7d468cc0` 离线候选 14/14 全绿、`qc151_trip.py` 未被改动）；故「立即可做 / 代价最低」应按剩余工作量重估，不是从零开始 |
| **B 静态重估 RC-1 AV 根因链** | 重算 `except.txt.final_isolated` 的 `Bytes at CS:EIP` 与磁盘 32/32、`FE00FFFF` 在映像内 imm32 命中、`0x7CFD30/0x7CFD39` 摘链写点；核 AV 件 `b42c7014…`（26,830 B、`Edx=FE00FFFF`） | 纯静态、不受 D-13 限制 | 中；须改 `Q5_ROUTES.md:112-113` 的行号归属（见 §7 #8） |
| **C 修好观测后另起可信新样本**（C1 真机新趟 / C2 采样候选） | C1 补「**游戏自身崩溃可归因证据**」的缺口（不是「补 Q4 的归因缺口」）；仍拿不到 DR6/DR0-3 的原始读数 | **C1 受 D-13 真机授权**（`D22_RULING/TASK.md:31` 需用户明示授权）；**C2 完全受 D-13 且当前被禁**（`RULING_D22.md` nextSteps 6、`PENDING_DECISIONS.md:78-80,206,248-249`），不得写相应采样候选代码；`PD:155-171` 与同文件 `:78-80,146,194-195,206,248-249` 存在授权口径冲突，C2 状态交最新裁决定 | 最高；三条路线均不写采样代码，不执行 |

**Q5 复核的其余降级理由**（不得当 CONFIRMED）：`PENDING_DECISIONS.md` 行号系统性失效（Q5 引的 `:67/:72/:301-302/:171/:176/:77/:169-172/:73-74` 八组本会话 `sed -n` 逐条对不上，实为「原 A 数据分层」「33=22+11 fps_avg」「D-04 裁决」等；D-13 禁令实在 `:78-80/:248-249/:206`，E3 暂停实在 `:114`，「纯静态/申请真机趟」实际出自 `D22_RULING/TASK.md:29,31`）；Q5 全文对 `QC124 / 断点 / 人为 / 运行期写出 / §599 / D-22` 零命中；`Q5_ROUTES.md:249-251` 判定档自述「不套三分档」与 `partVerdict=CONFIRMED` 冲突；回件时刻 `02:57:32` / 探针自报 `02:47:12` / 文件 mtime `03:05:03` 三口径未说明。

---

## 7 必须改项

**共 20 条（五道复核原始 mustFix 合计 27 条：Q1 3 / Q2 4 / Q3 4 / Q4 8 / Q5 8，去重合并为下列 20 条）**。每条给出「要改什么 / 改到哪 / 依据」。除标注「汇总件已落实」者外，均为对各自回件正文的待办修补；本汇总件不修改既有回件（`TASK.md:104` 只读铁律），只登记。

1. **Q4 结论收窄到受命口径**（Q4_review #1；Q1 #2、Q2 #4、Q3 #3 同型）：`Q4_RELATION.md:23-32,164-175,179-201` 与 headline 删除「不是任何一趟的崩溃」「该异常从未在任何一趟发生」「目标② 无一件归因证据」「历史基线残件」，改为「手上这件 EXCEPT 与整仓 113 份 `except_post_*.txt` 同一份字节；不是 2026-10-19 13:52 那趟的产物；except_post 语料对判定该趟崩溃无信息量」。**汇总件 §5 已按此写**。
2. **补登记 QC124 运行期写入链**（Q4 #2、Q5 #1/#2、Q3 #2）：逐件引用 `QC124_VERDICT.json:8,36,47-50,60-63,74-87`、`VERDICT_T11.md:148`、`ERRATA_EXCEPT_RESTORE.md:12,16,17`、`BASELINE_A4_PROPOSAL.md:79,92,104`，给出 drift bin 的实算 SHA/26,405 B/mtime 与「其寄存器 == EXCEPT L12-14」比对；把「历史基线残件」改判为「QC124 某趟运行期写出的 except.txt 快照，后被 harness 反复复制」，并注明该运行期事件本次未独立复现。**汇总件 §5 已按此写**。
3. **逐件处理 5 份不同哈希反例**（Q1 #2、Q3 #3、Q4 #3）：列出 qc119/qc120/qc121/qc123 `carrier/except.txt` 与 `except_pre_qc124.txt` 的 SHA256、size、Eip/Esp/Edx，说明其不是 `6694b75e…` 基线并删除「仓内 7CFC9F 异常证据全为同一残件」的任何等价表述；无法定性处标未验。**汇总件 §5 已逐件列表**。
4. **Q4 REFUTED 判定档降为 PARTIAL 并收窄论据**（Q4 #6）：`:184-201` 把实质错误精确限定为「把非 13:52 产物的残件当成 13:52 那趟真实 #DB 现场」，删去「若该异常从未在任何一趟发生 ⇒ TF/DR 施动者全部失去观测基础」，改为「仓内另有 QC124 书面记录支持 DR0 施动者，其可靠性未独立复核」。**汇总件 §0/§5 已降级**。
5. **Q1 CONFIRMED 补边界限定句**（Q1 #1、Q2 #4）：`Q1_CODE.md:206-208`（及 `:111-112`、headline）加「32/32 字节一致仅证明该文本抄录自 gamemd.exe 的 `0x7CFC9F..0x7CFCBE`，不证明该 EXCEPT 件记录了一次真实发生于 2026-10-19 13:52 的异常；证据件来源与『主崩溃』关系由 Q4 定谳（本项未验）」；`W9_SINGLESTEP.md` 的 Q1/Q2 节须带各自范围限定，避免与 §5 打架。**汇总件 §2/§3 已写**。
6. **Q5 起点与排序理由改写**（Q5 #1、Q3 #2）：`Q5_ROUTES.md:23,192,252` 用 `PD:144`/§599 的精确表述替换「没有一件归因证据」「废掉唯一锚点」「Q4 REFUTED 是全部路线起点」；保留 A 为首选（与 D-22=A 一致）但不得依赖被反证的全局断言；注明 QC124 属仓内书面记录、零真机未独立复现。**汇总件 §6 已写**。
7. **Q5 路线 A 分档与 C1 缺口表述**（Q5 #2/#3）：`:74-77` 的「(i) 残件类」改称「QC124 人为 DR0 断点产物 + 其复制件」并补证据索引；`:148,155` 「补 Q4 的归因缺口」→「补『游戏自身崩溃可归因证据』的缺口」，保留「C1 仍拿不到 DR6/DR0-3」的正确表述。**汇总件 §6 已写**。
8. **Q5 的 RC-1 AV 行号归属勘误**（Q5 #5）：`:112-113` 改为「`except.txt.final_isolated` 的 `Bytes at CS:EIP` 在 L18（`splitlines` 计 L19，因 L1 含双 CR），`RC_SPEC_V4.md:62` 是其压缩重排版块；本次实跑该行 32 字节 == EXCEPT 件 L17」。本汇总员 `python -I -X utf8` 实读 `out/re_work/zcode_live/zc11/evidence/closeout/except.txt.final_isolated`：`L1=b'Error code: EXCEPTION_ACCESS_VIOLATION\r\r'`、`L17=b'\r'`（空行）、`L18=b'Bytes at CS:EIP (007CFC9F) : 8B 0A …'`、`L62=b'00F9D1EC: 00000000 DATA_PTR\r'`，`splitlines_total=1047 / LF=1046`。Q5 自述只 `head -17` 却声称亲读到该字节行，须撤回。
9. **Q5 的 `PENDING_DECISIONS.md` 引用全部改为可复核形式**（Q5 #4）：纯静态/真机授权改引 `D22_RULING/TASK.md:29,31,38,54`；D-13 禁令改引 `PD:78-80`（或 `:248-249/:206`）、E3 暂停改引 `PD:114`；撤换 `:301-302/:171/:176/:77/:169-172/:73-74`；标注当前盘面行号 + 版本时刻（04:23 有 258+/24- 漂移）；并核 `PD:155-171` 的全开授权与暂停口径冲突，C2 状态交最新裁决定。**汇总件 §6 已换引**。
10. **Q3 探针异常码表 VA 勘误**（Q3 #1）：`_w9_q3_final.py:79`（`TBL + 0x40 + 8`）与 `_w9_q3_final_out.txt:89` 的「含 0x80000004 的表项 VA = 0x7E8888」改为 **`0x7E8880`**；本会话实跑 `e.rd(0x7E8880,4)=04 00 00 80`、`e.rd(0x7E8888,4)=FF FF FF FF`。`Q3_MECHANISM.md:200,461` 写的就是 `0x7E8880`（错值未进回件正文），若继续把该输出件列为内联依据须加勘误注。
11. **Q3 与 Q4 判定档互斥的口径声明**（Q3 #4、Q4 #6）：`Q3_MECHANISM.md:13/:400/:406` 的 `substantiveDefect=false` 须明写「非实质」是**「字节级事实」限定口径**，否则 `W9_SINGLESTEP.md` §7 会同时收到 `false` 与 Q4 REFUTED 两个互斥结论；同时把「本件是否是一次真实发生的异常」补进 Q3 §8 未验清单，并给 `:33-34/:228-231/:293/:320` 的实在论表述加静态分析边界。**汇总件 §4 已写**。
12. **Q3 的 113 份「全量」补范围声明**（Q3 #3、Q1 #2）：`:75-76` 注明 `except_post_*` 全量 = 113/113 同哈希，但仓内 `-iname '*except*.txt'` 共 259 份、含 5 份 glob 外不同哈希的同地址 SINGLE_STEP 记录（见 §7 #3 表），Q4 全量比对未覆盖；「全量」只针对指定 glob，不是全仓异常证据全量。
13. **Q1 数字口径订正**（Q1 #3）：`Q1_CODE.md:20/:237` 的「235 行」→「236 行（`wc -l` / `splitlines`；`PROBE DONE` 在第 235 行）」；`:24` 的「1046 行」注明 `splitlines` 口径（`wc -l=1045`，因 1 个 lone CR）。本汇总员 `wc -l _w9_q1_out.txt = 236`、`grep -n 'PROBE DONE' = 235:` 实跑坐实。
14. **Q2 头部时刻口径**（Q2 #1）：`Q2_FUNCTION.md:8` 的 `01:28:18` 注明是正文成稿时刻，探针运行时刻 `01:20:23`（`_w9_q2_out.txt:2`）、输出落盘 `01:22:16`。**汇总件 §1 已写**。
15. **Q2 分支落点补实跑依据**（Q2 #2）：`Q2_FUNCTION.md:208` 的「`in by()` ⇒ 非 call/jmp 落点」补 `reviews/_q2_review_counter_out.txt:1` 的全流立即数目标枚举 = 0 与 `:2` 的前序指令末址；本汇总员本会话另独立跑 `IMM_TARGETS_TO_VA 0` 坐实。**汇总件 §3 已写**。
16. **Q2 覆盖度数字标时点并扣除冗余**（Q2 #3）：引用时标「截至 2026-11-06 01:22 的时点数：原始 80 / 净 66（docs/re 10 / lead 56）」，复核时点 109 / 71；并注明净 66 含 6 份与 EXCEPT 逐字节相同的基线副本，宜表述为「66 个含该 VA 的既有文件，其中 60 个非基线副本」。**汇总件 §3 已写**。
17. **Q4 母模板时序倒置订正**（Q4 #4）：`:112-115,:223` 按 `stat` 把 `_src_L3_sf10c_20261021/except.txt`（mtime `2026-10-17T22:16:07`）改称「后续副本」，注明 XVERIFY「历史固有基线」说法未经时序核对（drift 实体 `2026-10-16T19:21:11`、最早副本 `2026-10-17T08:14:58` 均更早）。
18. **Q4 §590「42 小时」归因订正**（Q4 #5）：`:70-73` 改为「同一 107 份子树 mtime 实为 `2026-10-17T08:14:58 .. 2026-11-04T18:26:58`（约 18 天），仅 44/107 落在 §590 窗口内；42 小时不能归因为单子树口径」（本会话 `find … -newermt … ! -newermt … | wc -l` = 44）。
19. **「无条件复制」措辞订正**（Q4 #8、Q5 #7）：Q4/Q5 与汇总件统一为「**载体 except.txt 存在时无条件、不以本趟是否发生异常为条件**」；`qc151_trip.py:4575` 有 `if not src.exists(): return None` 守卫。另在头部或 §6 注明「回件时刻」是正文成稿时刻而非探针运行时刻（Q4 `02:12 / 02:15:47 / 02:10:46`；Q5 `02:47:12 / 02:57:32 / 03:05:03`）。**汇总件 §5 已按守卫措辞写**。
20. **Q5 补登记 D-22/W11 既有工作、统一判定档**（Q5 #6/#7）：路线 A 的「代价/需要什么数据」注明 `RULING_D22.md:3,30-35`（02:31 已裁 A、5 步 nextSteps）与 `PD:144`（W11 14/14 全绿、正式 harness 未改、应用仍需授权），按已做部分重估「立即可做/代价最低」；同时统一 `partVerdict=CONFIRMED` 与「规划题不套三分档」的自相矛盾。**汇总件 §6 已写**。

---

## 8 诚实账

**本汇总员本会话亲跑的命令（数字全部可追）**：
- `sha256sum ra2youli/gamemd.exe && wc -c …` → `73201cc0…f67476 / 4825360`；`sha256sum <EXCEPT> && wc -c <EXCEPT>` → `6694b75e…a8c251 / 26405`。
- `find . -path ./.git -prune -o -type f -name 'except_post_*.txt' -print0 | sort -z | xargs -0 sha256sum` → `113` 行、`uniq -c = 113 6694b75e…a8c251`、尺寸 `113 26405`；`cmp -s` 循环 → `compared=113 differing=0`；`find …/qc161_u0400_trip -name 'except_post_*.txt' | wc -l` → `107`；`-newermt '2026-10-18 04:41' ! -newermt '2026-10-19 22:39' | wc -l` → `44`。
- `find . -iname '*except*.txt' | wc -l` → `259`；`find . -name 'except*.txt' -print0 | xargs -0 grep -l 'Exception occurred at 007CFC9F' | wc -l` → `211`；5 份不同哈希件逐件 `wc -c` + `sha256sum` + `grep -m1 'Exception occurred at'` + `grep -m1 '^Edx:'`（表见 §5）。
- `python -I -X utf8 -c` 多次（绝对路径 `sys.path.insert` + `from ra2tool import Engine`）：`IB 0x400000 / COVERAGE (99.99837567729335,1394120,66) / fo=0x3cfc9f / rd32 / by[VA] / rd(0x7CFC9E,1)=04 NOT_START / rd(0x7CFC9B,4)=8B 54 F9 04 / rd(0x7CFB13,5)=55 8B EC 83 EC / rets=[0x7cfe1b c3] / rd(0x4C8C63,11)=8B 8D C0 00 00 00 … / rd(0x4C8C6E,5)=68 50 1E 82 00 / rd(0x7E8840,16) / rd(0x7E8880,4)=04 00 00 80 / rd(0x7E8888,4)=FF FF FF FF / disasm 前 8 条 / FIRST18_EQUAL True / END_ADDR 0x7cfccf`。
- 全流枚举：`IMM_TARGETS_TO_VA 0 / IMM_0x80000004_IN_TEXT 0 / CALL_RaiseException_IAT 2 ['0x7d2f92','0x7db8a0'] / EF_0x286_bits [1,2,7,9] TF False / IMPORT_NAMES / C3_BYTES_IN_FUNC / DISASM_N 18 RESYNC_N 18`。
- 三方字节：`L17_bytes 32 rd32 32 EQUAL True diff_idx []`；`TASK40_EQUAL True`；EXCEPT 件 `splitlines 1046 / LF 1045 / CR 1046 / CRLF 1045 / loneCR 1`；`grep -n 'Bytes at CS:EIP' = 17`。
- `stat -c '%y | %s | %n'`：EXCEPT `2026-10-19 13:54:38.293170200`、drift bin `2026-10-16 19:21:11.8163891000 / 26405`、最早 except_post `2026-10-17T08:14:58.8125028000`、`_src_L3_sf10c_20261021/except.txt` `2026-10-17T22:16:07.9801372000`；drift bin `sha256sum = 6694b75e…a8c251`。
- `python -I -X utf8` 读 `QC124_VERDICT.json` 与 EXCEPT L12-14 比对寄存器全等；读 `except.txt.final_isolated` 得 L17 空行 / L18 字节行 / L62 栈 dump / `splitlines_total 1047`。
- `sed -n` 亲读 `TASK.md:35-96`、`Q1_CODE.md:20,24,29,206-208`、`Q2_FUNCTION.md:1-10`、`Q3_MECHANISM.md:241-317`、`Q4_RELATION.md:23-32,179-204`、`Q5_ROUTES.md:23,110-114,192,252`、`PD:67,72,78-80,114,144,248-249,301-302`、`GOAL…:9229-9236`、`RULING_D22.md:1-5,29-36`、`D22_RULING/TASK.md:28-32`、`qc151_trip.py:4561-4578,5939`、`Q4_review.md:370-378`。
- `wc -l _w9_q1_out.txt = 236`、`grep -n 'PROBE DONE' = 235:`；`grep -n '7E888' _w9_q3_final_out.txt / _w9_q3_final.py` 坐实 `:89` 错值。

**亲读但未独立复现（不得当已验）**：
- QC124 group2 的 DR0 断点命中、进程 0.63 s 终止、`except.txt` 运行期重写 —— 只有仓内书面记录（`QC124_VERDICT.json:8,35-72`、`VERDICT_T11.md:148`、`ERRATA_EXCEPT_RESTORE.md:12,16`、§599、`PD:144`）；本次零真机、未复现该运行期事件。
- 5 份不同哈希件的来源 / 写入时序 / 是否真捕获 —— 只读了头、哈希、size、mtime，标**未验**。
- 间接分支 / 跳转表落点、运行期 hook 与镜像改写 —— Q1/Q2 与复核均标**未验**，本汇总件不写成「不存在」。
- Q3 三条主探针原脚本、Q1/Q2/Q4/Q5 原探针的逐字重跑 —— 本汇总员**未逐字重跑**（五道复核各自已做并留有 `reviews/_Q1_exact_rerun*`、`_q2_replay_out.txt`、`_Q4_exact_rerun*`、`_Q5_exact_rerun*`）；本汇总员是按同一 `Engine` 重跑关键字节读/常量/落点/枚举，结论一致。这是**等价关键项复核，不是原脚本逐字重放**。
- 全仓全扩展名 `b42c7014…` 绝对计数 —— Q5 复核 300 s 超时被终止，本汇总员**未跑**；Q5 亦自述非全仓绝对计数，不冒充已核。
- 五份回件正文、五份复核正文及探针输出件在本次汇总中**一律只读未改**（`TASK.md:104`）；本汇总件未修改任何既有件，唯一新建/写入 = `W9_SINGLESTEP.md`。
- 未 commit、未 push；零真机、零采样注入、零活进程读取；所有 Python 均为 `python -I -X utf8` + 绝对路径。

**口径差异诚实登记**：任务书/§555 的「107 份」= `qc161_u0400_trip` 子树；本次整仓 `except_post_*.txt` = **113 份**（复核记录仓库在两次运行间有漂移，但 `except_post_*` 计数与哈希结论各次均 113/113 一致）。Q2 覆盖度数字是 01:22 时点快照，复核时点 03:16 为 109/71，差额已归因到 02:25–03:07 新建的 D22/PD 文件。EXCEPT 件「L17」在 `grep -n`/LF 口径为字节行、在 `splitlines` 口径为 L18，本文统一用 `grep -n` 口径并已声明。
