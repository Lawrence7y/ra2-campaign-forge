# RE-N05 · DISAGREE.md（纠错记录）

> 本文件记录三类纠错：**(1)** 被中断前次半成品 `EVIDENCE/step1_module_binding.py` 的错误；**(2)** 既有报告/仓库表述的纠错；**(3)** 本轮自己的自我纠错与作废脚本。
> 判据：每条都给 `[本次实测]`（命令/stdout/EXITCODE）、`[本次读码]`（文件:行）、`[静态推断]`（VA/RVA/FOFF/字节）或 `[转引]`（来源:行）。
> 前次半成品**未被采信、未被导入**；本轮只用全新脚本 `re_n05_step1_verify.py` 等独立复算。为查错，本轮**只读执行**了它一次并把输出留证：`EVIDENCE/stdout_interrupted_draft.txt`（COMMAND + EXITCODE=0）。

---

## 1 · 对 `EVIDENCE/step1_module_binding.py`（被中断半成品）的纠错

复核方式：逐行读 `step1_module_binding.py`（133 行），并实际运行一次与 `stdout_step1.txt` 对照。

| # | 位置 | 原内容 | 问题 | 正确值 / 证据 | 等级 |
|---|---|---|---|---|---|
| D1-1 | **第 119 行** | `("ddraw.dll", d_info, 0x022B06, 0x547A0000),` | **运行期基址硬编码错**：应为 `0x547B0000`。任务卡已提示此错，本轮独立复算确认 | `1417489158 − 0x22B06(142086) = 1417347072 = 0x547B0000`；`0x547B×0x10000 = 1417347072`；`+0x22B06 = 1417489158` 与 JSON `addr` 完全一致（`stdout_step1.txt:315-317`）。错误值的反例：`0x547A0000 + 0x22B06 = 1417423622`，比记录 addr **少 `0x10000` = 65,536**（`stdout_step1.txt:318`）。半成品输出里 `Run VA = 0x547C2B06 (1417423622) [RunBase 0x547A0000]`（`stdout_interrupted_draft.txt:92`）——**错值** | `[本次实测]` + `[本次读码]` |
| D1-2 | 第 116-118 行 | 三个 gamemd 目标的 `run_base` 直接写 `0x00400000` | **未经该趟 JSON 反算就写入结论表**：脚本虽在 §"STACK JSON BASE ADDRESS NORMALIZATION" 打印了每帧 `addr-off`，但目标表没有把两者挂钩、也没有 `recorded − run_VA = 0` 校验 ⇒ 无法发现基址写错（D1-1 正是这么漏掉的） | 本轮 `stdout_step1.txt:311-316, 331/341/351/361` 给出四行显式算式与 `Recovered RVA from recorded absolute addr` 校验，四行均为 0 偏差；且 `gamemd` 同趟多帧基址一致性检查 `CONSISTENT`（`:280-283, :305-309`） | `[本次实测]` |
| D1-3 | 第 84-95 行 / 全脚本 | 只**计算并打印** SHA-256，**没有与期望值比对、没有 mismatch 即停止的门槛** | 任务卡要求"开工前实算 SHA-256 与字节数写进报告首段；不一致立即停止并报告"；该脚本不满足 | 本轮 `re_n05_step1_verify.py:main()` 有 hard gate：两值不等则 `return 2`；`stdout_step1.txt:11-13, 128-130, 266` 显示 `MATCH=True` 与 `Hash gate: PASS` | `[本次读码]` + `[本次实测]` |
| D1-4 | 第 72-77 行 + 第 129-130 行 | `rva_to_file_offset()` 在 `VSize>RawSize` 尾部返回 `foff=None`；但 `main()` 无条件 `f"0x{foff:08X}"` | **潜在崩溃**：任一目标落在 BSS 尾部就会 `TypeError`（本次 4 个目标恰好都在 raw 内，所以没触发，属潜伏错误）；也从未演示"尾部不可映射" | 本轮 `stdout_step1.txt:362-364` 显式给出两个反例：`gamemd .data RVA 0x47E004` 与 `ddraw .data RVA 0x5DE04` → `file_offset=None, in_raw=False, TAIL(vsize>rawsize)`；脚本在 `foff=None` 时打印 `NONE` 不崩溃 | `[本次实测]` + `[本次读码]` |
| D1-5 | 第 84-98 行 / 结论缺失 | 打印了 `DYNAMIC_BASE`、`RELOCS_STRIPPED`、重定位目录，**但不给 ASLR 判据结论**，也不列 `.reloc` 段名、不数重定位项 | 任务卡第一步要求"该 PE 有无 DYNAMIC_BASE 与 .reloc、是否被 ASLR 重定位" | 本轮 `stdout_step1.txt:16-32, 133-157, 366-370`：gamemd `DYNAMIC_BASE=False` + `RELOCS_STRIPPED=True` + 无 `.reloc` 段 + 0 条重定位 ⇒ **本趟未重定位且无法被重定位**；ddraw `DYNAMIC_BASE=True` + `.reloc` 段 + 10,152 条重定位（10,120×type-3）⇒ **被 ASLR 重定位，delta `0x447B0000`** | `[本次实测]` |
| D1-6 | 第 114-130 行 | 目标表只有 4 个 RVA→VA→FOFF，**没有"该地址是返回地址还是执行点"的判据**、没有栈回溯器语义 | 任务卡核心区分力在"返回地址 ⇒ 前一条 call"；该脚本把 VA 当终点 | 本轮 `MODULE_BINDING.md` §3 + `WAIT_CHAIN.md` §0-§4：`e3_stackwalker.py:225-241` 真 StackWalk64 语义；四位置全部为返回地址，逐一给出前置 call 字节 | `[本次读码]` + `[本次实测]` |
| D1-7 | 第 20-27 行 | `pefile.PE(data=data, fast_load=True)` + `parse_data_directories(...)` | 本身可运行（`stdout_interrupted_draft.txt` EXITCODE=0），但 `DIRECTORY_ENTRY_DEBUG` 解析只取 `PdbFileName`，对 gamemd 得到 `{'type': 4}` 无 PDB；未记录 `Machine`/`TimeDateStamp`/`SizeOfImage`/`SectionAlignment`/`FileAlignment`，不利于版本绑定 | 本轮 `stdout_step1.txt:14-32, 131-157` 全字段实算；另由 UTF-16LE `7.1.0.0`（FOFF 389628/390004）与 vendor zip 字节同一性做版本绑定 | `[本次实测]` |

**结论**：该半成品的**结构可复用**（文件哈希 / PE 头 / 节表 / JSON 归一 / RVA→FOFF 表的骨架），但**每一行都要自己复核**：至少 1 处确定性数值错误（D1-1）、1 处方法论缺口（D1-2）、1 处门槛缺失（D1-3）、1 处潜伏崩溃（D1-4）与若干结论缺失（D1-5/6/7）。本轮未把它作为任何结论的依据。

---

## 2 · 对既有报告 / 仓库表述的纠错

### 2.1 `STALL_CAPTURE_SUCCESS.md:54-97`「推为 Blt」的判据链复核（任务卡特别点名）

| 判据 | 原表述（行） | 复核结果 | 等级 |
|---|---|---|---|
| ① `0x22b06` 紧跟 `call [0x10053A68]` ⇒ 返回地址语义 | `:80` | **成立**。`FF 15 68 3A 05 10` + `8B F0`，边界经整段线性扫描与严格前向解码双验（`stdout_disasm.txt:199-200, 183-196`） | `[本次实测]` |
| ② 调用前压 5 个参数 | `:82` | **成立**（`stdout_args.txt:367-372`） | `[本次实测]` |
| ③ `ret 0x14` ⇒ 恰好 5 个 dword | `:83` | **成立**（`C2 14 00` 于 RVA `0x22B26`，`stdout_args.txt:386`） | `[本次实测]` |
| ④ "DirectDraw 里 5 参数的标准方法是 `Blt(...)`" ⇒ 本处是 Blt | `:84-90` | **不成立，决定性错误**。COM `IDirectDrawSurface::Blt` 是 `this + 5 显式参数 = 6` 个栈 dword ⇒ `ret 0x18`；本处 `ret 0x14` 且 `[ebp+8]=LPMSG`、无 `this`/vtable/接口槽；`.data` RVA `0x5400C` 明确是 ASCII `"PeekMessageA"` 且 `0x5402C=hook 0x10022AA0`、`0x54030=槽 0x10053A68`；槽初值 `0x1002786A` 是 `jmp [IAT 0x1003E374] = USER32!PeekMessageA`（`stdout_step4b.txt:152-192`）。`ret 0x14`+5 参数**只是形状相似** | `[静态推断]` + `[本次实测]` |
| ⑤ `0x22b06` 不在 22 个导出内 | `:65` | **成立**（`stdout_disasm.txt:518-520`） | `[本次实测]` |
| ⑥ 第二次停滞 `win32u+0x11ac ← USER32+0xc7f51` ⇒ "Blt 内部进到 GDI/win32u 路径" | `:92-93` | **不成立/证据不足**：USER32+win32u 恰是消息 API 内核路径，外层还是 `gamemd+0x13EB1C`（`PeekMessageA` 调用点）；仅凭 win32u 不能判 GDI 渲染分支 | `[静态推断]` |
| ⑦ "0x22b06 在 cnc-ddraw 内部，不是原版 DirectDraw" | `:95-97` | **成立**；但由此得出的"阻塞在 Blt 的包装实现里"随之作废 | `[转引]` + `[本次实测]` |
| ⑧ 通篇用 `0x10022af3…` / `[0x10053A68]` 作地址 | `:68-76` | **混用 VA/RVA**：那是**首选 VA**。该趟 ddraw 实际基址 `0x547B0000`，运行期 VA 应为 `0x547D2AA0..0x547D2B26`、槽 `[0x54803A68]`；`call` 的 imm32 在 RVA `0x22B02` 有 type-3 HIGHLOW 重定位（`stdout_disasm.txt:201-206`）。`LEAD_INDEPENDENT_CHECKS.md:40` 也已指出这一点，**该项与其一致** | `[本次实测]` + `[转引]` |
| ⑨ `0x22b06` 被称"**停滞点**（= call 的返回地址）" | `:74` | 措辞自相矛盾：既是返回地址就不是"当时执行的阻塞点"；真正执行点在被调用者（`USER32!PeekMessageA` 及其内层） | `[本次读码]` |
| ⑩ 自承"只能靠 `ret 0x14` + 5 参数 + 调用上下文推断为 Blt，**没有符号级确认**" | `:139` | 该自承的**边界诚实**，但**推断对象错了**：本轮用 hook 表 + thunk + 版本同一二进制把语义确定到 `PeekMessageA` 钩子（仍无编译期符号，见 `WAIT_CHAIN.md` §4.8） | `[转引]` + `[本次实测]` |

### 2.2 `STALL_CAPTURE_FINAL.md` 的连锁错误

| # | 原表述 | 纠错 | 等级 |
|---|---|---|---|
| D2-2a | `:104` "对比上一趟（pid 40500）抓到的栈是 `DDRAW.dll+0x22b06`（DirectDraw `Blt`）" | 该 RVA 是 **cnc-ddraw 的 `PeekMessageA` 钩子包装**，不是 `Blt`（见 §2.1④） | `[本次实测]` |
| D2-2b | `:104-109` "两次冻结的签名不同 ⇒ 至少有两条不同的成因路径" | **逻辑错误**。① 40500 **自带两种签名**，其 event#2（`ntdll+0x7858c`/`KERNELBASE`×2/`gamemd+0x207F17`）与 14412 内 4 帧**逐帧相同**（`stdout_step1.txt:297-302`）；② 两趟 `picked_by`/`paused_ms`/可读率不同（14412 `only_tid`, 0.0ms, 3493/3493；40500 `most_gamemd_frames`, 63/78/94ms, 1792/3991）；③ 40500 event#2 `frame=0` 报告称游戏已退出 ⇒ 同一 RVA 可对应不同上游状态。**不同栈签名不能直接推导为不同根因**。`docs/re/NEXT_RE_TASKS_20261112.md:65` 已持此结论，本轮与其一致 | `[本次实测]` + `[转引]` |
| D2-2c | `:89` "这是一次**永久冻结**"、`:156` "~229 s 的永久冻结" | `:92-94` 自承未存全量 3493 样本、是三个数字自洽的强推断；且未排除暂停/结束/失焦。本轮按任务卡只写"帧号停推候选 + 一条等待栈" | `[转引]`（不采信） |

### 2.3 仓库内互相矛盾的旧标注

| # | 来源 | 表述 | 本轮裁定 |
|---|---|---|---|
| D2-3a | `lead/ROUND_SUBAGENT_LOG_TRIGOAL_20261017.md:2028` | "cnc-ddraw **fake_PeekMessageA**（ddraw.dll+0x22AA0）→ 垫片 timeGetTime …" | **与静态字节一致**：hook 表 `"PeekMessageA"` + `0x10022AA0` + `timeGetTime` 调用（`stdout_args.txt:365`）。作 `[转引]` 旁证，不作为定谳依据 |
| D2-3b | 同文件 `:2124` | "项④掩盖假说基本自洽（ddraw **0x22AB0=被 hook 的 Blt 路径**）" | **与 :2028 自相矛盾，且与静态字节不符**：`0x22AB0` 是同一 `PeekMessageA` 钩子内 `cmp [0x1005F0A0],0` 之后的指令区，不是 Blt。以本轮字节证据为准 | `[本次实测]` |
| D2-3c | `STALL_CAPTURE_SUCCESS.md:139` / `STALL_CAPTURE_FINAL.md:104` | "Blt" / "没有符号级确认" | 见 §2.1、§2.2 | — |
| D2-3d | `lead/next_re_20261112/REVIEW/LEAD_INDEPENDENT_CHECKS.md:33-40` | 两趟基址 `0x400000` / `0x547B0000`；指出 `STALL_CAPTURE_SUCCESS.md:68-76` 用的是首选 VA | **本轮独立复算完全一致**，并补充 PE 层理由（gamemd `RELOCS_STRIPPED` 无 `.reloc`；ddraw `DYNAMIC_BASE` + 10,152 条重定位）。属**一致项**，非纠错 | `[本次实测]` |
| D2-3e | `docs/re/NEXT_RE_TASKS_20261112.md:65, 196, 202-203` | "两个栈签名不同只说明捕获路径不同"、"它们通常是返回地址"、"五个显式参数加 `ret 0x14` 不能单独完成 `Blt` 的符号级确认" | **三条全部成立**，本轮逐条复核并落地；属任务卡自身正确约束 | `[转引]` + `[本次实测]` |

### 2.4 转引报告的边界（不推翻、只标注）

- `STACKWALK_RECEIPT.md:93-98`、`WOW64_RECEIPT.md:113-122` 自承"未对 gamemd 本体采样 / 栈的语义解读未做"——本轮正是补这一步（静态部分），**不把它们的运行时声明当成本轮已证**。
- `STATIC_FRAME_SEMANTICS.md:107-113` 的"帧号写点只有 1 处且是初始化"结论，任务卡 `:73` 已指出其指令边界/分类风险；本轮**未使用**该结论做任何等待链推断。

---

## 3 · 本轮自我纠错与作废脚本（如实登记）

| # | 位置 | 问题 | 修法 / 现状 |
|---|---|---|---|
| D3-1 | `stdout_disasm.txt:25-29`（`re_n05_disasm.py` 第一版） | 把 `0x53D330`（标准 `push ebp;mov ebp,esp`，且前一条是 `ret`）误选为 `0x13EB1C` 的所属函数。实际上那只是**前一个函数**的序言，因为 `0x53D330..0x53E770` 之间存在多条 `ret` | `stdout_step5b.txt:61-62` + `stdout_step6.txt:12-37` 证明真实起点是 **FPO 风格 `0x53E770`**（14 字节 NOP 填充 + `sub esp,0x34`），从它严格解码 254 条无间隙直达目标。`WAIT_CHAIN.md` §1.2 已采用正确值；`stdout_disasm.txt` 作为**原始 stdout 保留不改**（诚实留痕） |
| D3-2 | `stdout_disasm.txt:93-94, 110-111` | 对 `0x207F17` / `0x20833F` 报 "NO prologue verified"，因为只找 `55 8B EC` 标准序言 | 这两个函数都是 **FPO / 省略帧指针**：`0x606800`（`push ecx/ebx/ebp; mov ebp,[esp+0x10]`，6 处 `EnumChildWindows` 回调注册）、`0x608070`（`sub esp,0xC; mov ebp,ecx`，thiscall）。`stdout_step6.txt` 用严格无间隙链重新确认三处 `target IS an instruction start: True`；`stdout_disasm_gamemd_207F17.txt` / `_20833F.txt` 的 "trusted boundary" 只取到了**函数内部的 ret 后起点**（如 `0x207E29`、`0x2082E0`），已在本文件与 `WAIT_CHAIN.md` 中明确标注为"线性可解码但非函数起点" |
| D3-3 | `stdout_step4b.txt:212` | 版本串检查用了 `data[i:i+16] == "7.1.0.0".encode("utf-16-le")`（14 字节），16 vs 14 永不相等 ⇒ 误报 `UTF-16LE offsets: []` | `stdout_step5b.txt:68-70` 用 `len(u16)` 正确比较：ASCII 无命中、**UTF-16LE 命中 FOFF 389628 / 390004**（与 `stdout_step1.txt:264` 一致）。修正后结论写进 `WAIT_CHAIN.md` §4.8 |
| D3-4 | `re_n05_step3.py` / `re_n05_step4.py` / `re_n05_step5.py` | 三个脚本的**全仓递归 glob / 全仓内容扫描**在本机耗时数分钟未完成，已 `job_kill`（job `pwsh-659c3a6ea983491c`、`pwsh-d19cd1346ad5436f`、`pwsh-969b6891df6c4baa`），**未产生 stdout 证据文件** | 拆成有界脚本 `re_n05_step4b.py`（EXITCODE=0）、`re_n05_step5b.py`（EXITCODE=0）、`re_n05_step6.py`、`re_n05_step7.py`、`re_n05_args.py`、`re_n05_waitapi.py`；`stdout_step5b.txt:75-108` 明确声明内容扫描是**有界**的（11 个显式文件），不是全仓 grep。作废脚本保留在 `EVIDENCE/` 但不作为结论依据 |
| D3-5 | `stdout_args.txt` 第一版（EXITCODE=1） | 把 VA `0x607EC0` 当 RVA 传给 `r2o()` ⇒ `off=None` → `TypeError` | 改为 RVA `0x207EC0`（gamemd `ImageBase=0x400000`），并把第一段的起点从非边界 `0x13EAD0` 改为已验证函数起点 `0x13E770`；最终 `stdout_args.txt` EXITCODE=0。`stdout_step7.txt` 第一/二版分别因 skipdata 伪指令无 `operands`、缩进、`import sys` 失败，第三版 EXITCODE=0（失败留痕均被同名覆盖，最终文件只保留成功版；本表如实登记） |
| D3-6 | `re_n05_step1_verify.py` 第一版（EXITCODE=1，`stdout_step1.txt` 已被成功版覆盖） | 误把 `pefile.DIRECTORY_ENTRY`（双向 dict，`{int→name, name→int}`）当单向 `name→int` 遍历，`oh.DATA_DIRECTORY[idx]` 收到 str ⇒ `TypeError` | 改为只遍历 `isinstance(k, int)` 的一半；成功版 `stdout_step1.txt` EXITCODE=0。失败留痕在本表登记 |

> 说明：所有 `stdout_*.txt` 由 `EVIDENCE/run_evidence.ps1` 生成，文件头含 `RUN_ID / COMMAND / CWD / TIMESTAMP_LOCAL / EXITCODE` 与完整原始 stdout/stderr。保留成功版作为承重证据；上表把被覆盖的失败尝试逐条登记，避免"只报绿灯"。

---

## 4 · 一句话总账

- **半成品**：1 处确定性数值错误（ddraw 运行基址 `0x547A0000` → `0x547B0000`）+ 6 项方法/门槛/潜伏缺陷。
- **既有报告**：`Blt` 定性错（决定性）、"两条独立根因"逻辑错、`0x100xxxxx` 当作运行期 VA 的混用、仓库内旧标注自相矛盾；`LEAD_INDEPENDENT_CHECKS.md` 与任务书的基址/边界约束经独立复算**成立**。
- **本轮**：把 `0x22B06` 从"疑似 Blt"更正为"**cnc-ddraw `PeekMessageA` 钩子包装的返回地址**"（版本同一二进制 + hook 表 + thunk + 5 参数契约四重证据），并如实登记 6 项自我纠错与作废脚本。
