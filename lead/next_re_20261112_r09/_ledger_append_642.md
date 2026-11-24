
---

## §642 · 工具链升级与**授权边界变更**：Ghidra 实测可用；用户授权 x64dbg ⇒ 放开调试器附加（2026-11-14）

- **性质**：用户本轮指令「先不要开发，先找几个好用的逆向工具、反汇编工具」＋ 用户明示选择「只装第一档 + 再加 x64dbg」。Lead 亲测并落盘 `lead\next_re_20261112_r09\TOOLCHAIN_R09.md`。条目标号 `§642-1…4`。
- **§642-1 [已证] Ghidra 12.1.4 已装且实测可用**（`D:\ghidra\ghidra_12.1.4_PUBLIC`；需 JDK 21，`launch.properties` 已设 `JAVA_HOME_OVERRIDE=D:\jdk21\jdk-21.0.12.1+1`）
  - 导入 `gamemd.exe` exit=0，自动套用自带 win32 符号库，解析 16 个导入库。
  - **全量分析 3.4 分钟，识别 8,948 个函数**。
  - **函数边界与 Lead 手工逐指令核完全吻合**：`0x47C520` body **47 B**、`0x47C4D0` **73 B**。
  - **纠正一处**：`0x568940` 不是函数首，它在 `FUN_005687f0`（945 B）内部（W99 判错）。
  - 反编译 `FUN_0047ea90`（摘链函数）一次给出 C 伪码，并**多给三条 Lead 手工未得的信息**：① `param_2[0xc]` 即 `+0x30` 的 next；② 摘链后 `WhatAmI()==6` 时用 `(cell+0x24)*0x100+0x80` / `(cell+0x26)*0x100+0x80` ⇒ **格→世界坐标 `row*256+128`**；③ `DAT_00a8e9a0` 即 Lead 手工普查失败的那个守卫全局。
  - ⇒ **Ghidra headless 定为静态分析主力**；`capstone` 退为"批量定制普查"，且**普查结果必须用 Ghidra 复核边界**。
  - `[已证·方法学]` 本轮 Lead 的 7 次方法错误里，**5 次（指令边界 / 函数边界 / 交叉引用 / 全局识别 / 结构布局）在此工具下不会发生**。⇒ 今后「手工逐指令重建」不再作为默认手段。
  - 工程目录 `_ghidra_proj`（库名 `gamemd_auto`）已含全量分析，**后续可直接 `-process` 复用，不需重跑 3.4 分钟**。
- **§642-2 [已证] 新装并实测的工具**
  | 工具 | 版本/位置 | 实测 |
  |---|---|---|
  | **PresentMon Console** | 2.6.0，`presentmon` 别名 | `--version` → `PresentMon 2.6.0` |
  | **Detect It Easy** | 4.0.0，`diec.exe` | `gamemd.exe` → PE32 / **MSVC 6.0** / DirectDraw·DirectSound·RAD；`ddraw.dll` → PE32 / **MSVC 19.39 LTCG / VS2022 17.9.1** / AVIFIL ⇒ 独立印证 ddraw 是现代重建件 |
  | **x64dbg** | `…\release\x32\x32dbg.exe`（32 位，本项目用这个） | 已装 |
  | **Resource Hacker** | 5.2.8，`C:\Program Files (x86)\Resource Hacker\` | 已装（第三徽章 R1 的对话框模板需要） |
  | **WPR** | `C:\Windows\System32\wpr.exe`（**系统自带**） | ETW 采集现成可用；`wpa.exe` 不在本机（在 ADK 里） |
  - **PresentMon 的意义**：裁决 Q3 明确「没有独立画面参照时不得裁定原始画面」。PresentMon 采 DWM/显示层 present 时序，**正是该缺失的参照**。`[未证]` 尚未在本项目场景采集，与 ddraw 通道的指标对齐需一张卡。
- **§642-3 [已证·装失败] 两个工具未装成**（不影响本轮结论）
  - **Sysinternals Suite**：winget 报 `Installer hash does not match; this cannot be overridden when running as admin`（清单哈希过期）；直连 `download.sysinternals.com` 两次传输中断。⇒ 待网络好转从官方 zip 重取。
  - **HxD 2.5**：厂商站 `mh-nexus.de` 返回 **502 Bad Gateway**。可选工具，暂缺。
  - 未装但确认 winget 可装（备选第二意见）：`Hex-Rays.IDA.Free` 8.4 / `Rizin.Rizin` / `Rizin.Cutter` / `Vector35.BinaryNinja`。
- **§642-4 [授权变更·必须遵守] 用户授权安装 x64dbg ⇒ 放开「附加调试器」**
  - **新允许**：只读附加调试器（`x32dbg` 对 PE32）；抓崩溃现场；生成/分析 **minidump**。
  - **据此失效的旧约束**：各真机卡的「禁附加调试器」；`§629-4` 把「minidump 或运行期监视」列为"**须单独授权**"——**该授权已取得**。凡引用 `§629-4` 的"离线不可证"措辞，今后须按本条重读为「**静态不可证，但已获动态取证授权**」。
  - **仍然有效的红线（未授权，继续禁）**：① 禁写 `gamemd.exe` / `ddraw.dll` / `ra2youli\` 任何文件；② **禁写目标进程内存**（`PROCESS_VM_WRITE` / `WriteProcessMemory`）；③ 禁改 `.detour` 段；④ 禁改主台账（append-only）；⑤ 禁 taskkill 非本卡进程。
  - **`[边界待确认]` 软件断点**（`int3` 补丁 = 写目标内存）**不在**本次概括授权内。首次使用前须再向用户明示确认一次。硬件断点/只读观察不属此列。
