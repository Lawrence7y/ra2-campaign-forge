# FORBIDDEN_OPS.md — 「禁止操作」硬清单（真机卡逐条自证用）

> 适用对象：**后续任何执行 ②-b 取证的真机卡**（本卡 `R17-D48-B2B-DESIGN` 是纯设计卡，未做任何真机操作，本清单对它无自证义务，仅作交付物）。
> 用法：真机卡开工前整体过一遍，收尾时**逐条打勾**并把勾选结果写进该卡自己的产物；任一条无法打勾 ⇒ 该次会话作废，不得对外出结论。
>
> 授权基线（**不要自行扩权**）：
> - 常设真机授权：启动/关闭本卡启动的 `ra2youli\gamemd.exe`；**只读**进程内存与线程上下文；合成鼠标键盘输入；读游戏目录日志与 `except.txt`。
> - **D-48**（用户 2026-11-20 明示授权）：以 `DebugActiveProcess` 作调试器 attach；仍受上述只读范围约束，禁区不变。
> - **D-36(A)**（2026-11-19，**未被 D-48 撤销**）：不设硬件执行断点、不写线程上下文、不写进程内存。
> - 真机**严格串行**（`LIVE_LOCK`），一次一卡。

---

## 1 · 禁止写目标进程内存（含"看起来只是改保护"的写法）

- [ ] 未调用 `WriteProcessMemory`
- [ ] 未用 `VirtualProtectEx` / `VirtualProtect` 修改目标进程任何页的保护属性
- [ ] 未向目标进程写入软件断点 `0xCC` / `0xCD` / 任何字节
- [ ] 未设置 `PAGE_GUARD`（不制造 `STATUS_GUARD_PAGE_VIOLATION`）
- [ ] 未用 `NtWriteVirtualMemory` / `NtProtectVirtualMemory` 等等价未文档化路径绕过上述三条
- [ ] 未通过 `ReadProcessMemory` 的"读改写"组合间接写内存

## 2 · 禁止写线程上下文（D-36(A)）

- [ ] 未调用 `SetThreadContext` / `Wow64SetThreadContext` / `NtSetContextThread`
- [ ] 未写 `Dr0`–`Dr3` / `Dr7`（硬件执行断点）
- [ ] 未写 `EFLAGS.TF`（单步）
- [ ] 未写任何线程寄存器（含 `EIP`/`ESP`/`EBP`/通用寄存器）
- [ ] 未写非本进程线程的上下文

> 注：「撤销 D-36(A) 的这一条」属于**需另行明示授权**的事项（见 `DESIGN.md` §3.3）。在授权到手之前，本节任何一条不得打勾为"已做"。

## 3 · 禁止 DLL 注入 / Hook

- [ ] 未 `CreateRemoteThread` / `QueueUserAPC` / `SetWindowsHookEx` 注入
- [ ] 未改写目标进程 IAT / EAT / 内联代码
- [ ] 未在游戏目录放置任何代理 DLL（`ddraw.dll` / `ra2render.dll` / `WSOCK32.DLL` / `xyr.dll` 等一律不动）
- [ ] 未使用 `AppInit_DLLs` / `Detours` / `EasyHook` / `MinHook` 等驻留机制

## 4 · 禁止改 `ra2youli\` 下任何文件（只读）

- [ ] 未创建 / 修改 / 删除 / 重命名 `ra2youli\` 下任何文件
- [ ] 未修改 `gamemd.exe`（会话前后 SHA-256 必须仍为 `73201CC021497C9567742F718BF1DC78C22E9AE16C7E7365354B65F3FCF67476`）
- [ ] 未修改 / 删除 / 清零 `except.txt`（**游戏自己写日志属游戏行为；本卡只读**）
- [ ] 未修改 `RA2MD.INI` / `ra2.ini` / `ddraw.ini` / `ra2render.ini` / `BATTLEMD*.INI` / `*.lcf` / `ra2forge_install.json`
- [ ] 未修改 / 新建 `*.sav` / `*.mix` / `*.mmx` / `*.map` / `*.mpr` / `*.yrm`
- [ ] 未在 `ra2youli\` 下新建任何文件（含日志、dump、截图）
- [ ] 本卡所有产物只落在 `lead\next_re_20261117_r14\<卡号>\`

## 5 · 禁止联网 / 禁止碰第三方会话

- [ ] 未进行联网对战 / 未加入 Westwood Online / 未开 `xwis.dll` 相关功能
- [ ] 未 attach 非本卡启动的 `gamemd.exe`（若系统里已有别的会话：先确认 `LIVE_LOCK`，不是自己的就等）
- [ ] 未 attach 其它任何进程（`ra2loader.exe` / `YURI.exe` / `game.exe` / `explorer.exe` 等）

## 6 · 禁止写工程控制文件（越权写域）

- [ ] 未改 `COVERAGE\coverage.tsv`
- [ ] 未改 `COVERAGE\PANEL.md`
- [ ] 未改 `R14_COMMON.md`
- [ ] 未改台账（`lead\` 下 `*.md` 台账正文）
- [ ] 未改看板（`STATUS_BOARD.md` / `BOARD_ARCHIVE.md`）
- [ ] 未改 `_drafts\` / `_cards\` / 任何其它卡目录
- [ ] 未改 `lead\PENDING_DECISIONS.md`（裁决由用户/Lead 写）

## 7 · 禁止把"未观测到"写成"已证明不存在"（错源⑨）

- [ ] 每条"未观测到"都配了灵敏度正对照（臂 A）
- [ ] 每条否定性结论都写了预注册的二项检验门槛与实测命中率
- [ ] 未出现"引擎不允许"/"仅 UI 限制"/"闸拒绝"等**超出观测能力**的措辞
- [ ] 「0x47C620 的直接调用者」与「哪一层拒绝」两个概念**未混写**（后者需 R7 闭合）
- [ ] `0x449440` 走 `0x449493`（`BType vt[0xA8]`）支路的情形**未被计入**"闸拒绝"

## 8 · 真机纪律

- [ ] 开工前读过 `LIVE_LOCK` 且确认归属本卡
- [ ] 全流程只启动**一个** `gamemd.exe`
- [ ] 收尾释放 `LIVE_LOCK`
- [ ] 会话前后各记一次基线：`gamemd.exe` SHA-256、`except.txt` 的 `size`/`mtime`/SHA-256、游戏目录文件数
- [ ] 若 attach：已调用 `DebugSetProcessKillOnExit(FALSE)`，收尾用 `DebugActiveProcessStop` 脱离
- [ ] 异常一律 `DBG_EXCEPTION_NOT_HANDLED` 放行，**未**用 `DBG_CONTINUE` 吞掉真实异常

## 9 · 授权灰区（默认不做；要做必须先拿到明示授权）

- [ ] 未调用 `SuspendThread` / `ResumeThread`（D-48 只写"只读"，未明列挂起线程）
- [ ] 未调用 `DebugBreakProcess` / `DebugSetProcessKillOnExit(TRUE)`
- [ ] 未使用 `MiniDumpWriteDump`（常设授权里列了 MiniDump，但 dump 会把目标内存落盘到本卡目录之外的位置需另行确认）
- [ ] 未修改调度优先级 / 亲和性 / 任何进程级属性

---

## 自证签署模板（真机卡复制到自己产物里）

```
卡号：
会话时间（本地）：
gamemd.exe SHA-256 前/后：
except.txt size/mtime/SHA-256 前/后：
LIVE_LOCK 取得/释放时间：
第 1–9 节：全部打勾 = 是 / 否    若有未打勾，逐条说明：
本会话是否越界：否
```
