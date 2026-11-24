# W164 PROGRESS

> 每完成一步追加一行（时间 + 做了什么 + 结论/下一步）。时间 Asia/Shanghai。

- 2026-11-16 19:28 读取 `R11_COMMON.md`(193 行) 与 `R12_FACTS.md`(402 行) 全文；建立卡目录 `work/`、`EVIDENCE/`；复核 gamemd.exe SHA256=`73201CC0...476`、imageBase=0x400000、pefile/capstone 版本。
- 19:30 写 `pehelp.py`（VA→file off、u32、capstone skipdata=True 线性反汇编）；从 `vtables_canonical.json` 解析出全部 Locomotion 主表/子表地址（`loco_vtables_raw.txt`）。
- 19:32 `loco_vtable_bounds.py` 双通道（COL 指针 vftable[-4]==col）确认：主表 10 槽、offset=4 子表 **50** 槽（台账记 49，进 DISAGREE）、offset=24 子表 8 槽。`resolve_ai_slots.py` 得到各 AI 槽地址 + Locomotion 槽 23(+0x5C) 初值。
- 19:33 写 Ghidra `W164_AI.java`（`-noanalysis`）导出 6 个 AI 函数反编译+全部 CALL；确认 FootClass::AI=0x4DA530 被 3 个子类 AI 直调；`0x736210`/`0x51BB7A` 处 `call [EAX+0x5C]`（NULL 门）。
- 19:35 `W164_Focus.java` 反汇编 Unit AI 的 `+0x5C` 调用与 FootClass::AI 入口/尾部；`W164_LocoCall.java` 从正确指令边界（capstone）确认 `0x736204` 字节与 `0x4DAEF3` 字节。
- 19:37 识别调用约定矛盾：`+0x5C` 派发点为 thiscall 无栈参，而 Locomotion 槽 23 的 `0x55A910` 是 stdcall `ret 4`（1 栈参）⇒ 槽 23 不是每帧更新槽。`find_process_slot.py` + `rdata_bytescan.py`（全 .rdata 字节扫描，双通道）确认大 Process（0x4B2630 等）0 命中 = 不在任何虚表，是内部 callee。
- 19:39 `W164_Path.java`：寻路 xref 链闭合——0x4CBBA0←0x4D3920；0x42C900←0x4CBC31；0x4D3920←5 个大 Process（Drive/Walk/Mech/Ship/Hover）；FootClass::AI←3 子类。
- 19:41 `check_off4_process.py`（byte-level 逐槽查直接 callee）锁定 **每帧更新槽 = offset=4 子表槽 16 `+0x40`**（Drive→0x4B0500→大 Process 0x4B2630 等）。`W164_ProcCallers.java` 确认这些 wrapper 无直接调用者（纯虚表调用）。
- 19:43 `W164_Gates.java` 反编译 UpdatePathfinding(0x4D3920) 与 Drive wrapper；`0x4B055A` 原始字节（capstone 复核）钉死**移动门控 `[loco+0x54]==-1 || byte[loco+0x5F]==0 → 跳 0x4B066C`**。这是 Q1 关键结论。
- 19:44 `count_instr.py`（skipdata 全节 1,394,186 条，与 §6.2 吻合）测出各函数指令数；SearchCore=544 指令单循环；`scan_cell.py` 得到 MapClass 格表 0x87F924 引用 30+ 处、`[reg+0xE4]` 99 处。
- 19:46 主台账 grep + 分段精读（§562/§563/§710/§719/§785/§853）：确认 0xFFF7=65527 轮数上限、格链不登记单位、MaxUnitCount 语义、引擎无单位上限、N 1500→1230 无可测影响。
- 19:47 写 `LOCOMOTION_COST.md`（5 行摘要 + Q1–Q5 + LEAD_AUDIT）。判决：**结构支持成立、数量级静态不可判（偏向成立）**。

下一步（若续时）：追 `0x8871E0` 初始化点求节流除数 N；对 `0x4B066C` 之后分支做逐字节确认 short-circuit；记录 DISAGREE 给 Lead。
