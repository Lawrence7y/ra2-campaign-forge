# R09 工具链盘点与验证（2026-11-14）

> 用户指令本轮：「先不要开发，先找几个好用的逆向工具、反汇编工具」。
> 本文件只记**工具现状与验证结果**，不含项目开发内容。
> 验证方式一律是**真跑一次**，不是"装上了就算"。

---

## 1 · 已装并实测可用

### 1-1 **Ghidra 12.1.4 PUBLIC**（本轮最大收获）

| 项 | 值 |
|---|---|
| 安装位置 | `D:\ghidra\ghidra_12.1.4_PUBLIC`（另留 `ghidra_12.1.4_PUBLIC_20260921.zip`） |
| Java | 要求 **21**（`application.java.min=21`）；`support\launch.properties` 已设 `JAVA_HOME_OVERRIDE=D:\jdk21\jdk-21.0.12.1+1` |
| 环境变量 | `GHIDRA_INSTALL_DIR=D:\ghidra\ghidra_12.1.4_PUBLIC`（用户级） |
| 自带扩展 | `Eclipse` / `Ghidra` / **`IDAPro`** |

**实测记录**（全部 exit=0）：

| 步骤 | 命令要点 | 结果 |
|---|---|---|
| 导入（不分析） | `analyzeHeadless <proj> gamemd_test -import ra2youli\gamemd.exe -noanalysis` | 成功；自动套用自带 win32 符号库，解析 16 个导入库（`XYR.DLL`/`KERNEL32.DLL`/`DDRAW.DLL`/`BINKW32.DLL`…） |
| **全量分析** | `analyzeHeadless <proj> gamemd_auto -import … -postScript …` | **3.4 分钟**；识别 **8,948 个函数** |
| 反编译复核 | `-process gamemd.exe -noanalysis -postScript DecompVerify.java` | 15.7 秒；函数边界与 Lead 手工逐指令核**完全吻合** |

**函数边界对照（自动 vs 手工）**：

| 地址 | Ghidra 判定 | Lead 手工 | 一致性 |
|---|---|---|---|
| `0x0047C520` | `FUN_0047c520`，body **47 B** | 47 B（`0x47C520–0x47C54E`） | ✅ |
| `0x0047C4D0` | `FUN_0047c4d0`，body **73 B** | 73 B（`0x47C4D0–0x47C518`） | ✅ |
| `0x0047EA90` | `FUN_0047ea90`，body **263 B** | —— | 新 |
| `0x568940` | **在 `FUN_005687f0`（945 B）内部** | W99 误当函数首 | **Ghidra 纠正** |

**反编译质量示例（`FUN_0047ea90`，即摘链函数）**，一次就给出且**多给三条 Lead 手工没有的信息**：

```c
void __thiscall FUN_0047ea90(int param_1, int *param_2, char param_3) {
  if (param_2 != NULL) {
    piVar3 = (param_3 == 0) ? *(int**)(param_1+0xe4) : *(int**)(param_1+0xe8);
    if (piVar3 == param_2) {                      // 是链头
      *(int*)(param_1 + (param_3==0 ? 0xe4 : 0xe8)) = param_2[0xc];
    } else {                                      // 在链中
      do { piVar1 = piVar3; if (!piVar1) goto L; piVar3 = piVar1[0xc]; }
      while (piVar1[0xc] != param_2);
      piVar1[0xc] = param_2[0xc];
    }
    param_2[0xc] = 0;
L:  iVar4 = (**(code**)(*param_2 + 0x2c))();      // WhatAmI()
    if (iVar4 != 0xf && (**(code**)(*param_2 + 0xc0))()) {
      if ((**(code**)(*param_2 + 0x2c))() == 6) {
        iStack_c = *(short*)(param_1 + 0x24) * 0x100 + 0x80;   // <<< 格→世界坐标 row*256+128
        iStack_8 = *(short*)(param_1 + 0x26) * 0x100 + 0x80;   // <<<
        (**(code**)(*param_2 + 0xf4))(&iStack_c);
      } else { … (**(code**)(*param_2 + 0xf4))(&param_2[0x27]); }
    }
  }
}
```

- `param_2[0xc]` = **next 指针 `+0x30`**（印证 Lead 手算 `mov esi,[esi+0x30]`）
- **新信息**：摘链后 `WhatAmI()==6` 时用 `(cell+0x24)*0x100+0x80` 与 `(cell+0x26)*0x100+0x80` → **格坐标转世界坐标**
- **新信息**：`DAT_00a8e9a0` 是守卫全局（Lead 手工普查**失败**的那个）
- 反编译器同时确认摘链逻辑"既处理链头也处理链中"⇒ 与台账 §640-2 一致

**结论**：Ghidra headless 应作为静态分析**主力**；`capstone` 退为"批量脚本/定制过滤"用途。
本轮 Lead 的 7 次方法错误中，**5 次（指令边界、函数边界、交叉引用、全局识别、结构布局）在这个工具下不会发生**。

### 1-2 **PresentMon 2.6.0 Console**（Intel，免费）

| 项 | 值 |
|---|---|
| 命令 | `presentmon`（winget 别名）→ `…\WinGet\Links\presentmon.exe` |
| 实测 | `presentmon --version` → **PresentMon 2.6.0**（注意：`--version` 会先报 unrecognized option 再打版本号） |

**为什么它重要**：裁决 Q3 明确「没有**独立画面参照**时，只能产出'开启观测时看到的节奏'，**不得**裁定原始画面」。
PresentMon 采的是 DWM/显示层的 present 时序（`msBetweenPresents` / `msUntilDisplayed`），**正是这个缺失的独立参照**。
`[未证]` 尚未在本项目场景下采过一次，指标语义与 RA2 的 ddraw 通道如何对齐仍需一张卡验证。

### 1-3 **Detect It Easy 4.0.0**（`diec.exe` 命令行 / `die.exe` GUI）

安装位置 `…\WinGet\Packages\horsicq.DIE-engine_…\`（PATH 已由 winget 写入用户变量，但**已启动的进程需重启才生效**）。

实测（这就是"真能干活"的证据）：

| 目标 | DIE 输出 |
|---|---|
| `ra2youli\gamemd.exe` | `PE32` · Compiler: **Microsoft Visual C/C++ 6.0 (1720-9782)** · Library: DirectDraw / DirectSound / RAD Video Tools · Debug data: Records [Misc] |
| `ra2youli\ddraw.dll` | `PE32` · Linker: **MS Linker 14.39.33523** · Compiler: **MSVC 19.39.33523 [LTCG/C]** · Library: AVIFIL · Tool: **Visual Studio 2022 17.9.1** · Debug data: CodeView / VC Feature / POGO |

⇒ 独立印证 `ddraw.dll` 是**现代 VS2022 重建**（cnc-ddraw），非原厂件；`gamemd.exe` 是 MSVC 6.0 编译。两条与项目既有记录相容。

### 1-4 **x64dbg**（用户本轮明确授权安装）

| 项 | 值 |
|---|---|
| 32 位调试器 | `…\x64dbg.x64dbg_…\release\x32\x32dbg.exe` ← **本项目要用的就是这个**（`gamemd.exe` 是 PE32） |
| 64 位 | `…\release\x64\x64dbg.exe` |
| 启动器 | `x96dbg.exe`（winget 生成别名 `x32dbg` / `x64dbg` / `x96dbg`） |

**⚠ 这条安装改变了项目边界**（见 §3 授权变更）。

### 1-5 **Resource Hacker 5.2.8**

`C:\Program Files (x86)\Resource Hacker\ResourceHacker.exe`。
用途：**对话框模板**。第三徽章 R1 路线（`CreateDialogIndirectParamA` + 模板 `0x52EC00` / `cmp ecx,0x94`）正好需要它。

### 1-6 **WPR（Windows 自带，无需安装）**

`C:\Windows\System32\wpr.exe` 已存在 ⇒ **ETW 采集现在就能做**。
`wpa.exe`（GUI 分析器）**不在**本机 —— 它在 Windows ADK 的 Windows Performance Toolkit 里，需另装（约 1–2 GB）。
替代路径：`tracerpt -of CSV` 可把 `.etl` 转 CSV 做离线分析（粗糙但可用）。

---

## 2 · 装了但失败 / 未装

| 工具 | 状态 | 原因与后补方式 |
|---|---|---|
| **Sysinternals Suite**（Procmon/ProcExp/Vmmap） | **失败** | winget 报 `Installer hash does not match; this cannot be overridden when running as admin`（清单哈希过期）；直连 `download.sysinternals.com` 两次都被传输中断（curl 卡住 10 min 后转后台，已 kill）。⇒ **待网络好转后从官方 zip 重取**，或用 winget 降级版本。**不影响本轮其它结论** |
| **HxD 2.5** | **失败** | 厂商下载站 `mh-nexus.de` 返回 **502 Bad Gateway**。可选工具（十六进制编辑已有 Ghidra/DIE 覆盖），暂不补 |
| CFF Explorer | 未装 | winget 无包。可用 **PE-bear**（GitHub 直下）或 **pestudio** 替代 |
| Windows ADK / WPA | 未装 | 需下 ADK 安装器（体积大）。要分析 WPR trace 时才需要 |
| IDA Free 8.4 / Rizin+Cutter / Binary Ninja | 未装 | 均已确认 winget 可装（`Hex-Rays.IDA.Free` / `Rizin.Rizin` / `Rizin.Cutter` / `Vector35.BinaryNinja`）。作为**第二意见反编译器**有价值（不同引擎给不同线索），非必需 |

---

## 3 · **授权变更记录（重要，影响后续所有卡片）**

- **本轮用户明示选择安装 x64dbg** ⇒ 等于**放开"附加调试器"**。
- 与之冲突的旧边界（须按下列方式重读，不再自动适用）：
  - `OBSERVER_ABBA_PROTOCOL.md` / 各真机卡的「禁止注入/禁附加调试器」；
  - 台账 `§629-4` 把"minidump 或运行期监视"列为「**须单独授权**」——**该授权现已取得**。
- **仍然不变的红线**（未获授权，继续禁止）：
  1. **禁写** `gamemd.exe` / `ddraw.dll` / `ra2youli\` 任何文件；
  2. **禁写目标进程内存**（`PROCESS_VM_WRITE` / `WriteProcessMemory`）；
  3. **禁改 `.detour` 段**；
  4. **禁改主台账**（append-only）；
  5. **禁 taskkill 非本卡进程**。
- ⇒ **允许**：只读附加调试器（`x32dbg`）、抓崩溃现场、生成/分析 minidump、软件断点（会改内存 → **需逐次声明**，不属本条概括授权）。
  - **`[边界待确认]`** 软件断点（`int3` 补丁）本质是写目标内存。本条授权措辞是"放开调试器附加"，**未明说允许软件断点**。⇒ 首次使用软件断点前须再向用户确认一次。

---

## 4 · 建议的用法分工（给后续卡片）

| 任务类型 | 用哪个 | 理由 |
|---|---|---|
| 反编译读语义、函数边界、交叉引用、结构布局 | **Ghidra headless** | 一次跑 3.4 min 建库，之后秒级查询；避免手写 capstone 的边界错误 |
| 大范围字节/位移普查（如 `+0xE4` 写入点） | capstone 自写脚本 | 定制过滤比 Ghidra 脚本快，但**必须**用 Ghidra 复核边界 |
| 二进制身份/编译器指纹 | DIE `diec` | 一条命令 |
| 崩溃现场（谁写坏 vptr） | **x32dbg** / minidump | 静态已证查不出（§640-4） |
| 显示帧时长（① 的"卡不卡"） | **PresentMon** | 裁决 Q3 要的独立画面参照 |
| 对话框模板（第三徽章 R1） | Resource Hacker + Ghidra | 模板在 `.rsrc` 与 `0x52EC00` |
| 邻居负载/独占机器纪律核查 | Procmon/ProcExp（待补） / 现有 `Get-Process` | 定性够用 |

---

## 5 · 环境备注（可复现）

- Python `3.12.10`；已装 `capstone 5.0.7`、`pefile 2024.8.26`
- Java：PATH 上是 `Microsoft jdk-17.0.19.10-hotspot`；Ghidra 走 `D:\jdk21\jdk-21.0.12.1+1`（**不要**改 PATH，改 `launch.properties` 即可）
- 包管理器：`winget` 可用；无 choco / scoop
- 磁盘：C 余 168 GB / D 余 492.5 GB
- 网络：`github.com` 200；`api.github.com` 403（限流）；`download.sysinternals.com` 不稳定；`mh-nexus.de` 502
- Ghidra 工程目录本轮建于 `D:\Project\ra2-campaign-forge\_ghidra_proj`（`gamemd_auto` 已含全量分析，可直接 `-process` 复用，不必重新分析）
