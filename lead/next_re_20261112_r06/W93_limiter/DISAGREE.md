# W93 DISAGREE · 与既有背景/前人卡的分歧清单

> 本文件仅记录经本卡独立反汇编或实测字节证实、与背景摘要或 W86/W90 口径存在差异的条目。

1. **与背景摘要「`0x10015E83 mov [0x1005EE48], 0x3C`（唯一的立即数写入 = 60）」及 W86「`+0x5EE48 参考上限（自洽校验：应=60）`」存在根本语义分歧 `[静态读码]+[本次实测]`**
   - **既有口径**：W86 仅注意到 `0x10015E83` 的立即数 `0x3C` (60)，将 `0x1005EE48` 命名为「参考上限」，并在 `exp_rpm_framebeat.py` L14/L112 写死期望值 `60`。
   - **实测/反汇编事实**：
     - `0x1005EDD0..0x1005EE6B`（`RVA 0x5EDD0..0x5EE6B`，大小 `0x9C = 156 B`）是 Win32 `DEVMODEA` 结构体；`0x1005EE48` 即 `DEVMODEA + 0x78` = **`dmDisplayFrequency`**（显示器当前刷新率 Hz）。
     - `0x10015E34..0x10015E50`（`off 0x015234..0x015250`）先将 `dmSize` (`[0x1005EDF4]`) 置 `0x9C` 并调用 `USER32!EnumDisplaySettingsA(NULL, ENUM_CURRENT_SETTINGS=-1, 0x1005EDD0)`（通过动态指针槽 `[0x10053A58]`）。
     - 若 `EnumDisplaySettingsA` 成功（`eax != 0`），`0x10015E50 jne 0x10015ea7` **直接跳过** `0x10015E83`！此时 `[0x1005EE48]` 持有操作系统返回的显示器实际刷新率。`0x10015E83` 的 `0x3C` (60) **只是 `EnumDisplaySettingsA` 失败（返回 0）时的兜底默认值**。
     - 本机只读调用 `EnumDisplaySettingsA(NULL, -1, &dm)` `[本次实测]` 返回 `2560x1440, 32bpp, dmDisplayFrequency=210`，直接解释了 W90 `clamp=210` 的由来。

2. **与背景摘要「每帧门闸 `sub_10006AE0`：用 `timeGetTime` 比 `[0x1005F120]`，不足则 `Sleep` 补差」存在运行路径分歧 `[静态读码]+[本次实测]`**
   - **既有口径**：背景与 W86 将 `timeGetTime` + `[0x1005F120]` + `Sleep`（`0x10006D66..0x10006D8A`）描述为 `sub_10006AE0` 的主要/唯一限帧实现。
   - **实测/反汇编事实**：
     - `sub_10006AE0` 在 `[0x1005F128] != 0` 后首先检查 `[0x1005F138]`（`0x10006C5D`），即 `sub_10017AC0`（`0x10017AC6..0x10017B11`）经 `CreateWaitableTimerExW` / `CreateWaitableTimerA` 创建的 WaitableTimer 句柄。
     - 当 `[0x1005F138] != 0`（Windows 正常路径）且 `vsync=0` 或 `0 < maxfps < dmDisplayFrequency`（例如本机基线 `maxfps=60 < 210`）时，`0x10006C7E jb 0x10006cd1` 走 **`GetSystemTimeAsFileTime` + `CompareFileTime` + `WaitForSingleObject` + `SetWaitableTimer`** 支路（`0x10006CD1..0x10006D65`），**既不读取 `[0x1005F120]`，也不写入 `[0x1005F124]` (`cur_t`)**。
     - `0x10006D66` 的 `timeGetTime + [0x1005F120] + Sleep` 仅是 **`[0x1005F138] == 0`（WaitableTimer 创建失败）时的兜底支路**。
     - 交叉实证 `[本次实测]`：W90 真机产物 `lead\next_re_20261112_r05\W90_replicates\out\trip_C6_c\render_channel\framebeat_1794640742.csv` 中全部 9,000 行的 `cur_t` 列**恒为 `0`**，证明真机运行期走的是 `WaitableTimer` 支路而非 `0x10006D66`。
     - 即使如此，三条渲染主循环顶部的 `[0x1005F120]` 写入点（`0x1001B01A` / `0x1001CD51` / `0x1001D2D2`）仍按 `[0x1005F128] > 0` 每帧写入 `timeGetTime()`，因此**不影响** `[0x1005F120]` 在 `interval > 0` 时作为限帧层节拍观测通道的有效性（但严格语义是「渲染线程每帧开始/取帧前戳记」，而非门闸内部比较时刻）。

3. **与背景摘要「`[0x1005F120]` 每帧写入（3 处写入点，对应三条 renderer 路径）」的语义精确化 `[静态读码]`**
   - 三个写入点（`0x1001B01A` / `0x1001CD51` / `0x1001D2D2`）确实分别位于 D3D9 (`0x10019310`->`0x1001AEC0`)、OpenGL (`0x1001CCC0`)、GDI (`0x1001D1D0`) 三条渲染循环中，但均位于循环**顶部**（渲染/Present **之前**、`WaitForSingleObject([0x1005EF30])` **之后**），且均以 `[0x1005F128] > 0`（即 `interval > 0`）为唯一写入门控。`sub_10006AE0` 门闸则在循环**底部**调用（`0x1001BB6E` / `0x1001D18E` / `0x1001D694`）。
   - 同时实读 `W93_limiter\bin\ddraw.ini` L35 为 `vsync=false`（L355 `[gamemd]` 未覆盖 `vsync`），故基线配置下 `[0x100594EC]=0`、`[0x100594E8]=60`、`[0x1005EE48]=210`、`[0x1005F128]=16`，走的是 `0x10006B0B je 0x10006C4F -> 0x10006C72 je 0x10006CD1`（`WaitableTimer` 绝对时间支路）。
