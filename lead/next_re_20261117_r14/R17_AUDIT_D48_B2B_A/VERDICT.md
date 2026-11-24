# R17-AUDIT-D48-B2B-A 裁定

本卡 6 条中有 **1 条 DISAGREE**（C5）。必改项清单：**1 项** —— C5 把“已发现的概率性栈哨兵通道”写成“唯一区分通道”，需限定为“已审候选中的唯一/一条可行通道”，并保留命中率、嵌套、OTHER 调用者与假阴性的限制。C3 的“净收益 0”结论：**在 ②-b 区分这一问题范围内成立**；D-48 给的是调试器身份，不是写内存/写上下文打断点的权利，栈哨兵也不需要 attach。

## 逐条依据

### C1 · AGREE
Win32 `DEBUG_EVENT.dwDebugEventCode` 定义为 9 类（1–9）：`EXCEPTION`、`CREATE_THREAD`、`CREATE_PROCESS`、`EXIT_THREAD`、`EXIT_PROCESS`、`LOAD_DLL`、`UNLOAD_DLL`、`OUTPUT_DEBUG_STRING`、`RIP_EVENT`。加一个非 `DEBUG_EVENT` 的 `GetThreadContext`/`ReadProcessMemory` 采样通道，合计 10。补 `UNLOAD_DLL_DEBUG_EVENT` 是对的。

### C2 · AGREE
软件断点 `0xCC` 需要写目标进程内存；硬件执行断点需要写 `Dr0–Dr3/Dr7`；单步需要写 `EFLAGS.TF`，均需要被 D-36(A)/禁区排除的写权限。因此在当前约束下，“可证明某条具体指令执行过”的通用通道为 0。普通异常/故障不是任意指令执行证明通道，未据此翻转结论。

### C3 · AGREE
D-48 增加的是 attach/调试器身份及调试事件接收，不包含写进程内存或写线程上下文。无断点则没有 gate 路径上的指令级事件；已识别的栈返回地址哨兵属于常设只读能力，attach 前后均可做。因此 D-48 对 ②-b 的有效新增通道为 0、净收益 0；该结论不应外推成“D-48 对所有调试用途都无收益”。

### C5 · DISAGREE
“不依赖 attach”这一半成立：`GetThreadContext` + `ReadProcessMemory` 只需相应进程/线程句柄，不需要 `DebugActiveProcess`。但“概率性、需命中微秒级窗口”的采样结论不能单独支撑“唯一区分”：设计只覆盖了有限候选，未穷尽其它只读/外部可观测面；嵌套调用、OTHER caller、假阴性和窗口外样本都会限制结论。建议改为“已发现的一条可行通道 / 已审候选中的唯一可区分通道”，不要写成无条件的“唯一区分”。

### C6 · AGREE（实测：无）
对 shard 一致的 `ra2youli/gamemd.exe` 做定点 PE 导入表解析：ImageBase `0x400000`，16 个 DLL、372 个导入项，delay-import 目录 VA=0；未发现 `OutputDebugStringA` 或 `OutputDebugStringW`。对两个符号名做原始字节计数也均为 0。结论：**IAT 中无这两个符号**。被审文本中的“558 个导入”与本卡解析数不一致，但不影响“符号缺失”的判定。

### C7 · AGREE（仅作为推理可接受）
attach 后 `#DB` 作为第一机会 `EXCEPTION_SINGLE_STEP` 交给调试器、由 `DBG_CONTINUE` 续跑，在一般 Win32 语义下可消解“无人处理 ⇒ 必崩”的绝对说法；因此该推理可保留为 `[推理]`。本卡未真机验证。反例方向至少包括：
1. 反调试：动态解析的 `IsDebuggerPresent`/`CheckRemoteDebuggerPresent`、`xyr.dll` 或 SecuROM 相关探测可能使 attach 后行为改变。
2. `#DB` 交付/恢复语义：需结合 `Dr6` 区分 fault/trap 和触发源，并正确处理 `RF`，否则可能重复陷入或分类错误。
3. `ExceptionAddress` 偏差：硬件断点的报告地址可能受 fault/trap 与恢复标志影响，不能未验证就等同于“被拦截指令地址”。
4. SEH/VEH/`UnhandledExceptionFilter` 或 WOW64/Win10-11 调试语义差异也可能改变交付路径。
