# RE-N05 · UNKNOWNS.md（未证项 / 最小缺失证据 / 替代方法）

> 本轮零真机。凡需运行才能回答的一律标 `[待运行验证]` 并给出**最小观测方案**；不把有限静态搜索写成运行期全称证明，不把"这趟录到过一次"写成机制已确认。
> 证据分级与写域同 `WAIT_CHAIN.md`；所有 `[本次实测]` 都能在 `EVIDENCE/stdout_*.txt` 找到命令与 EXITCODE。

## 1 · 未证项总表

| # | 未证项 | 当前最好的静态结论 | 最小缺失证据 | 建议替代方法（本轮未做） | 等级 |
|---|---|---|---|---|---|
| U1 | `gamemd` IAT `0x7E1484` 与 `ddraw` 槽 `0x54803A68` 的**运行期值**：hook 是否已装、槽是否被 MinHook trampoline 覆写 | 磁盘字节只能给出导入名 `USER32!PeekMessageA` 与槽初值 `0x1002786A`（→ `jmp [IAT USER32!PeekMessageA]`）；`.data` hook 表把 `0x10022AA0` 标为 `"PeekMessageA"` 钩子（`stdout_step4b.txt:152-181, 192, 212-213`） | 一次**只读**读取两处 4 字节值 + 目标 PID/TID/模块基址 + 该趟 SHA-256 | 若不做真机：取得 `cnc-ddraw 7.1.0.0` 源码，静态读 hook 安装代码，推断安装时序与覆写行为（仍是静态推断，不能证明"这趟已装"） | `[待运行验证]`（RE-N06 最小批次） |
| U2 | 编译期**符号名** `fake_PeekMessageA` 的定义与 vtable/接口归属的完整排除 | 静态已排除 COM `Blt`：无 `this`、无 vtable 槽、5 参数 + `ret 0x14`、`[ebp+8]=lpMsg`、hook 表命名、槽跳到 `USER32!PeekMessageA`（`WAIT_CHAIN.md` §4.8） | 与 `7.1.0.0` **版本匹配的 cnc-ddraw 源码或 `ddraw.pdb`**（能把 RVA `0x22AA0` 映射到编译期符号） | 从 `CnCNet/cnc-ddraw` 对应 tag 取源码/PDB（本轮未出网）；或解析 `cnc-ddraw config.exe` 的资源/字符串（`vendor zip` 里 4,915,712 B，未展开） | `[待运行验证]` / 静态材料缺失 |
| U3 | 三个 gamemd **FPO 函数的精确大小/边界** | 起点可信：`0x53E770`（254 条无间隙到目标，收尾 `ret 0xC`）、`0x606800`（1598 条无间隙，6 处注册，内部 5 条条件 `ret`/`ret 8`）、`0x608070`（251 条无间隙，`ret` 于 `0x608370`）；`stdout_step6.txt` | 递归下降 / CFG 级函数识别，或带符号的映射文件 | 用 `lead/re_orphan_owners_20261110/_oo_disasm_out.txt`（74 MB 独立线性反汇编）按 `ret` + 对齐填充切函数；或用 Ghidra/IDA 的函数边界（本轮只用 capstone 线性 + 序言 + 严格链） | `[静态推断]`（大小未定谳） |
| U4 | 上游可达性：`0x53E770`、`0x608070` 的调用者 | whole-`.text`（4,060,045 B）直接 `call rel32` 命中 0；全文件 4 字节绝对 VA dword 命中 0（`stdout_step7.txt:10-11, 77-78`）；`0x606800` 有 6 处 `push 0x606800` 注册 | 函数指针表 / 虚表 / 寄存器间接调用的完整静态 xref，或更深的运行期栈 | 扫描 `.rdata`/`.data` 里所有指向 `0x53E770`/`0x608070` 的**重定位后** dword（含运行期写入）；或 RE-N06 采 32 帧完整栈 | `[静态推断]` 可达性未定 |
| U5 | `Sleep(30)` 轮询循环的**循环上限 `[esp+0xE4]`、`[0xAA0444]` 会话模式值、窗口焦点 `[0xA8ED80]`** 的运行期取值 | 字节层面确认 `0x607F29 jl 0x6076ED`、`0x53E773/0x53EB1E` 读 `[0xAA0444]`；docs 称 0=实时/1=录制/2=回放（`[转引]`） | 一次只读内存采样 + 同步状态标签 | 若不做真机：把静态 CFG 中所有写 `[0xAA0444]` / `[0xA8ED80]` 的点列出并分类（RE-N02 已规划） | `[待运行验证]` |
| U6 | 两条栈签名是否对应**不同上游状态** | 40500 event#2 与 14412 内 4 帧逐帧相同；两趟 `picked_by`/`paused_ms` 不同；40500 event#2 `frame=0`（报告称已退出）（`stdout_step1.txt:268-309`） | 同一事件的状态标签 + 画面 + 帧/tick 边沿 + 焦点 + 被选 TID + 全量 NDJSON | RE-N06 单变量对照；RE-N01 先补全量序列 | `[待运行验证]`（现阶段只写候选） |
| U7 | `ntdll+0x7858c` / `KERNELBASE+0x16a1f0` / `KERNELBASE+0x16a18f` / `USER32+0x74775` / `USER32+0x3505d` / `USER32+0xc7f51` / `win32u+0x11ac` 的**导出名** | 只做到"按模块基址归一 + 与调用契约吻合"的推断；本轮输入不含系统 DLL 字节 | 对应系统 DLL（SysWOW64）的 PE 字节 + 导出表 | **纯静态**读 `C:\Windows\SysWOW64\{ntdll,KERNELBASE,USER32,win32u}.dll` 解析 EAT/导出名（仍是只读磁盘字节，不违反授权）；本轮因写域/时间未做 | `[待运行验证]` / 静态可补 |
| U8 | `PeekMessageA` 钩子返回后 helper `0x100225C0` 是否触发 `SendMessage` 重入 / 跨线程等待 | 包装内只有 `InterlockedExchange`、`timeGetTime`、槽调用、helper；`0x100225C0` 未展开（`stdout_args.txt:354-386`） | helper 的完整反汇编 + 运行期深层栈 | 静态展开 `0x100225C0` 并解析其 IAT 调用；或 RE-N06 采更深的栈 | `[待运行验证]` |
| U9 | 229 s "永久冻结" 是否逐样本成立 | `STALL_CAPTURE_FINAL.md:92-94` 自承是三个统计数字自洽的**强推断**，JSON 未存 3493 个样本 | 全量 NDJSON 帧序列 + 单调时钟 | RE-N01 的流式落盘后离线重算 | `[待运行验证]`（转引，不采信） |
| U10 | 是否存在**其它等待对象**（事件/互斥量/临界区/信号量）造成这两趟现象 | `stdout_waitapi.txt` 在两镜像完整导入表 + 四位置 call 解码范围内**无命中**；gamemd 确实导入这些 API，但 IAT 槽都不匹配四个 call 点 | 若真机栈出现 `WaitForSingleObject` / `EnterCriticalSection`，取句柄与唤醒方 | 扩大到全 `.text` 所有 `call [IAT wait slot]` 的静态 xref（RE-N07 的活儿），本轮未做全量 | `[静态推断]`（有限范围，非全称证明） |
| U11 | cnc-ddraw `maxfps`/`vsync`/`windowed` 是否造成呈现同步等待 | `ddraw.ini` 有这些键；但四位置无呈现等待调用，`0x22B06` 是消息钩子 | 一次只改一个变量的配对观测 | RE-N06 实验矩阵 + 未抓栈对照 | `[待运行验证]` |

## 2 · "扫描无命中"的口径声明（质量红线）

本轮出现 3 处"无命中"，均按任务卡要求记录范围/编码/反例：

1. **仓库内无版本匹配的 cnc-ddraw 源码/符号**（`stdout_step5b.txt:75-108`）
   - 文件名范围：本轮 `glob` 工具实跑 `**/*.{c,cpp,h,hpp,cc,cxx,pdb,map,def,idb,i64}` → 1283 条路径（完整列表由工具转存到临时结果文件）；`**/*ddraw*` → 126 条路径。结果：无 `*.pdb`/`*.idb`/`*.i64`，C/C++ 文件均为 YRpp 引擎头文件，非 cnc-ddraw 源码。
   - 内容范围：**11 个显式列出**的仓库文件（`ra2opt/cddraw.py`、vendor zip、两份 `ddraw.ini`、若干 docs/lead 报告、`ref/yrpp/Unsorted.h`），**不是全仓内容 grep**。
   - 编码：原始字节 ASCII 大小写不敏感 + 精确 UTF-16LE；二进制安全，无解码失败。
   - 正例：`cnc-ddraw` 41 命中、`PeekMessageA` 21 命中 ⇒ 零命中不是扫描器失效。
   - 反例/负控制：`ZZZ_NO_SUCH_TOKEN_9F3C` = 0 命中。
   - 内容无命中项：`fake_GetMessageA` 0、`IDirectDrawSurface7` 0、`IDirectDrawSurface` 0；`fake_PeekMessageA` 仅 1 处，位于 `lead/ROUND_SUBAGENT_LOG_TRIGOAL_20261017.md:2028`（`[转引]` 文本标注，不是源码）。
2. **四位置无事件/互斥/临界区等待 API**（`stdout_waitapi.txt`）
   - 范围：两镜像完整导入表（gamemd 372 条导入项，其中 369 条具名 / ddraw 247 条，`stdout_waitapi.txt:13-14`）+ 四位置 capstone 解码；编码 = PE 导入名 ASCII + 序号，无编码歧义。
   - 反例：同一枚举能命中 `Sleep(0x7E11F0)`、`PeekMessageA(0x7E1484)`、`EnumChildWindows(0x7E14E4)`。
3. **上游直接 xref 零命中**（`stdout_step7.txt`）
   - 范围：gamemd 整段 `.text`（RVA `0x1000..0x3E038C`，4,060,045 B）全部线性解码出的 `call` + 全文件 4 字节绝对 VA dword 精确搜索；无编码歧义。
   - 反例：`0x606800` 用同法命中 6 处 `push 0x606800`，证明搜索器工作正常。
   - 口径：这只排除了**直接 call 与静态绝对地址引用**，不排除运行期写入的函数指针/虚表 ⇒ 写"可达性未定"，不写"无调用者"。

## 3 · 明确**不**主张的事情

- 不主张"机制已确认"：两趟各只有 1～3 张单时刻栈；`[本次实测]` 只到"该趟录到过这些帧"。
- 不主张"两条独立根因"：`WAIT_CHAIN.md` §6 与假设 H07 已把该说法降级/否定。
- 不主张"永久死锁"：静态看到的都是**可正常返回**的 API（`PeekMessageA` 非阻塞、`Sleep(30)` 定时、`EnumChildWindows` 同步返回）。
- 不主张"运行期全称证明"：所有静态搜索都标注了范围；例如"该 DLL 无 vtable 槽"只写到"在 411,648 B 文件的精确 dword 搜索 + 22 个导出 + hook 表范围内未发现 COM vtable 证据"。
- 不主张"原版对照"：`ra2bench/gamemd.exe` 只是本轮**分析镜像**，与游戏目录镜像同哈希（`docs/re/NEXT_RE_TASKS_20261112.md:83-84` 转引），但不是官方未修改原版的来源证明。

## 4 · 交给 RE-N06 的最小观测包（按优先级）

1. **只读 IAT/槽值**：`gamemd!0x7E1484`、`ddraw!0x54803A68`、`ddraw!0x54803A98`（GetMessageA 槽）；绑定 PID/模块基址/该趟 SHA-256。→ 关闭 U1。
2. **状态同步**：同一事件记录 `LOADING/IN_TACTICAL/PAUSED/MENU/SCORE_SCREEN/EXITING`、画面、帧/tick 边沿、窗口焦点、被选 TID、`picked_by`。→ 关闭 U6/U8。
3. **低扰动重复**：同一 TID 连续 ≥3 次取栈 + 恢复时间戳 + 线程 CPU 时间；另设未抓栈对照。→ 关闭 U5/H05/H11。
4. **单变量对照**：一次只改 `windowed` / `maxfps` / `vsync` 之一，先记原值/候选值/预期。→ 关闭 H10/U11。
5. **系统 DLL 静态补名**：只读解析 SysWOW64 四个 DLL 的导出表，把 7 个 `模块+偏移` 映射到导出名（纯静态，可离线做）。→ 关闭 U7。
