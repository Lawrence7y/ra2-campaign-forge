# W93 LIMITER · cnc-ddraw 限帧通道完整定谳与 `clamp=210` 归因

> 对象：`W93_limiter\bin\ddraw.dll`（411,648 B，SHA-256 `85e0f7d530dfda134793a57cb3e76b0287dcc96892ee57162dd68f47283b03a9`，ImageBase `0x10000000`，`DllCharacteristics=0x0140` / `DYNAMICBASE` 开）及 `W93_limiter\bin\ddraw.ini`（SHA-256 `c983abadc1162a2606243e097719aab557ce6381c040776336d0c746d6df9d52`）
> 反汇编证据留档：[disasm_evidence.txt](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r06/W93_limiter/EVIDENCE/disasm_evidence.txt)、[limiter_full_disasm.txt](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r06/W93_limiter/EVIDENCE/limiter_full_disasm.txt)
> 纪律：离线只读分析，未启动游戏、未附加进程、未注入、未修改任何二进制。

---

## 0 · 一句话定谳

1. **`clamp=210` 的根因**：W90 脚本 `exp_rpm_framebeat.py` **没有读错偏移、也没有做错换算**，运行期 `[ddraw_base + 0x5EE48]` 确实等于 **`210`**。因为 `0x1005EDD0..0x1005EE6B`（`0x9C = 156 B`）是 Win32 **`DEVMODEA`** 结构体，`0x1005EE48`（`+0x78`）即 **`DEVMODEA.dmDisplayFrequency`**（当前显示器刷新率 Hz）；`0x10015E48` 调用 `USER32!EnumDisplaySettingsA(NULL, -1, 0x1005EDD0)` 直接填充该结构体，成功时跳过 `0x10015E83`（`mov [0x1005EE48], 0x3C` 仅是 API 失败兜底）。本机实测 `EnumDisplaySettingsA` 返回 `2560x1440 @ 32bpp, 210 Hz`。
2. **`[0x1005F120]` 能否作逐帧仪器**：**在 `interval > 0`（`[0x1005F128] > 0`）的全部常规配置下均每帧写入一次**（D3D9/OpenGL/GDI 三条渲染主循环顶部均独立检查 `[0x1005F128] > 0` 后调用 `timeGetTime()` 写入 `[0x1005F120]`，不依赖 `sub_10006AE0` 内部走哪条睡眠/VSync 支路）；**仅当 `vsync=false` 且 `maxfps=0` 或 `maxfps>1000`（导致 `interval == 0`）时，写入被跳过、`[0x1005F120]` 停止更新**。

---

## 1 · 核验一：`exp_rpm_framebeat.py` 到底读了哪里？（排除脚本计算/偏移错误）

`[静态读码]` 逐行检查仓库内两份脚本（字节全等，188 行）：
- [exp_rpm_framebeat.py](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r03/W86_render_channel/experiment/exp_rpm_framebeat.py#L103-L112)
- [exp_rpm_framebeat.py](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r05/W90_replicates/work/tools/exp_rpm_framebeat.py#L103-L112)

关键行：
- **L104**：`A_CLAMP = base_i + 0x5EE48`（`base_i` 为目标进程 `ddraw.dll` 基址，W90 日志中为 `0x54400000`）
- **L110**：`clamp = read_u32(h, A_CLAMP)`（直接调用 `ReadProcessMemory` 读 4 字节无符号整数，**没有任何算术换算**）
- **L112**：`print("[SELF-CHECK] maxfps=%s clamp=%s interval=%s  (期望 60/60/16)" % (maxfps, clamp, interval))`

对照 W90 真机实测输出 [framebeat_console.log](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r05/W90_replicates/out/trip_C6_c/render_channel/framebeat_console.log#L1-L3)：
```
[OK] ddraw.dll runtime base = 0x54400000
[SELF-CHECK] maxfps=60 clamp=210 interval=16  (期望 60/60/16)
```

**结论**：`210` **不是**脚本偏移或换算口径问题；脚本中唯一的错误是 **L14 与 L112 的预期注释 `(期望 60/60/16)`**——W86 误把 `0x10015E83` 的失败兜底立即数 `60` 当成运行期恒定值。

---

## 2 · 核验二：`[0x1005EE48]` 的真实语义与非立即数写入路径

### 2.1 `EnumDisplaySettingsA` 结构体填充路径 `[静态读码]`

`0x1005EDD0`（`RVA 0x5EDD0`）开始的 `0x9C`（156）字节 `.data` 区域（`0x1005EDD0..0x1005EE6B`）即 Win32 `DEVMODEA` 全局实例（各字段偏移与引用与 Win32 SDK `wingdi.h` 定义逐字节吻合）：

| VA | RVA | 相对 `0x1005EDD0` 偏移 | `DEVMODEA` 字段 | 引用/写入证据 |
|---|---|---|---|---|
| `0x1005EDD0` | `0x5EDD0` | `+0x00` | `dmDeviceName[32]` | `0x10015E34: push 0x1005edd0` 传给 `EnumDisplaySettingsA` |
| `0x1005EDF4` | `0x5EDF4` | `+0x24` | `dmSize` (`WORD`) | `0x10015E42` 写 `0x9C` (156) |
| `0x1005EDF8` | `0x5EDF8` | `+0x28` | `dmFields` (`DWORD`) | 兜底分支 `0x10015E5A` 写 `0x5C0000` (`DM_BITSPERPEL\|DM_PELSWIDTH\|DM_PELSHEIGHT\|DM_DISPLAYFREQUENCY`) |
| `0x1005EE38` | `0x5EE38` | `+0x68` | `dmBitsPerPel` | 兜底分支 `0x10015E8D` 写 `0x20` (32) |
| `0x1005EE3C` | `0x5EE3C` | `+0x6C` | `dmPelsWidth` | 兜底分支 `0x10015E6C` 写 `GetSystemMetrics(0)` |
| `0x1005EE40` | `0x5EE40` | `+0x70` | `dmPelsHeight` | 兜底分支 `0x10015E7E` 写 `GetSystemMetrics(1)` |
| **`0x1005EE48`** | **`0x5EE48`** | **`+0x78`** | **`dmDisplayFrequency`** | **`EnumDisplaySettingsA` 写入实际刷新率；仅失败兜底 `0x10015E83` 写 `0x3C` (60)** |

反汇编关键流（`0x10015E1D..0x10015EA7`，见 [disasm_evidence.txt](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r06/W93_limiter/EVIDENCE/disasm_evidence.txt#L22-L50)）：
```
0x10015E1D (off 0x01521D)  83 3d 3c ee 05 10 00       cmp  dword ptr [0x1005ee3c], 0    ; dmPelsWidth 已初始化则跳过
0x10015E24 (off 0x015224)  0f 85 83 00 00 00          jne  0x10015ead
...
0x10015E34 (off 0x015234)  68 d0 ed 05 10             push 0x1005edd0                    ; ★ lpDevMode = &g_dm
0x10015E39 (off 0x015239)  6a ff                      push -1                            ; ENUM_CURRENT_SETTINGS
0x10015E3B (off 0x01523B)  be 9c 00 00 00             mov  esi, 0x9c                     ; sizeof(DEVMODEA) = 156
0x10015E40 (off 0x015240)  6a 00                      push 0                             ; lpszDeviceName = NULL
0x10015E42 (off 0x015242)  89 35 f4 ed 05 10          mov  dword ptr [0x1005edf4], esi    ; dmSize = 0x9C
0x10015E48 (off 0x015248)  ff 15 58 3a 05 10          call dword ptr [0x10053a58]        ; ★ USER32!EnumDisplaySettingsA
0x10015E4E (off 0x01524E)  85 c0                      test eax, eax
0x10015E50 (off 0x015250)  75 55                      jne  0x10015ea7                    ; ★ 成功则跳过下面的兜底赋值！
; --- 以下仅当 EnumDisplaySettingsA 返回 0 时执行 ---
0x10015E83 (off 0x015283)  c7 05 48 ee 05 10 3c 00 00 00  mov dword ptr [0x1005ee48], 0x3c ; 兜底 60 Hz
0x10015E8D (off 0x01528D)  c7 05 38 ee 05 10 20 00 00 00  mov dword ptr [0x1005ee38], 0x20 ; 兜底 32 bpp
```

- 动态函数槽 `0x10053A58`（`off 0x051900`）旁的导入描述串实测为 `"EnumDisplaySettingsA"`；`0x10053AA8`（`off 0x05158C`）旁实测为 `"GetSystemMetrics"`。
- `[本次实测]` 本机只读调用 `USER32!EnumDisplaySettingsA(NULL, -1, &dm)`（未启动游戏）实测返回：`ok=1, w=2560, h=1440, bpp=32, dmDisplayFrequency=210`。与 W90 运行期自检 `clamp=210` 完全吻合。

### 2.2 全二进制穷尽搜索范围声明（证明无其它写入者）`[静态读码]`

为排除 `[0x1005EE48]` 存在其它写入者（`A3`、`89 /r`、`mov [reg+disp]`、`memcpy`/`memset` 等），本次搜索覆盖：
1. **`.reloc` 重定位表全扫描**（全文件 `411,648 B`、`7` 个节 `.text/.rdata/.data/.detourc/.detourd/.rsrc/.reloc`）：因 `DYNAMICBASE=1`（`DllCharacteristics=0x0140`），一切静态编码绝对 VA 引用均须登记在 `.reloc`（`HIGHLOW`）。扫遍 `0x1005EDD0..0x1005EE6B` 全区间，指向 `0x1005EE48` 仅 4 处（`0x1000688E` 读、`0x10006B17` 读、`0x10006C7A` 读、`0x10015E85` 兜底写）；指向结构基址 `0x1005EDD0` 仅 1 处（`0x10015E35` 传参给 `EnumDisplaySettingsA`）；指向 `0x1005EDD1..0x1005EE6B` 其它字节的仅 `0x1005EDF4`/`0x1005EDF8`/`0x1005EE38`/`0x1005EE3C`/`0x1005EE40`（全部见 `scan_ee48_writes.py` 输出）。**未发现任何 `A3 48 EE 05 10` 或 `89 xx 48 EE 05 10` 写入，亦未发现向 `0x1005EDD0` 传参的 `memcpy`/`RtlZeroMemory`。**
2. **代码节 `[reg+0x78]` 间接写扫描**（`.text` `246,272 B` + `.detourc` `14,336 B`，Capstone 扫描所有内存写指令 `disp == 0x78`）：**0 命中**。
3. **小端字节流直搜**：`48 ee 05 10` 全文件出现 4 次，与 `.reloc` 结果 100% 一致。

---

## 3 · 核验三：限帧全链与三分支走查（`sub_10006880` + `sub_10006AE0` + 3 处写入点）

### 3.1 真实调用架构（含与背景描述的修正）`[静态读码]`

通过扫描 `.text` 与 `.detourc` 全部 `E8 rel32` 调用指令，确认全链路结构如下：

```
ddraw.ini 解析 (0x1001E16C..0x1001E191)
  ├─ [0x100594E8] = maxfps   (默认 -1；本机 [gamemd] 段生效值 = 60)
  └─ [0x100594EC] = vsync    (默认 1；本机 ddraw.ini L35 vsync=false -> 0)

显示器模式初始化 (0x10015E34..0x10015E83)
  └─ [0x1005EE48] = dmDisplayFrequency (EnumDisplaySettingsA -> 本机 210；失败兜底 60)

WaitableTimer 初始化 (0x10017AC6..0x10017B11)
  └─ [0x1005F138] = CreateWaitableTimerExW(HIGH_RESOLUTION) / CreateWaitableTimerA 句柄

渲染主循环 (三条路径各自执行一次 sub_10006880 初始化)：
  ├─ D3D9   (0x10019310 -> 0x10019481 call 0x10006880 -> 循环 0x1001AF70..0x1001BB88)
  ├─ OpenGL (0x1001CCC0 -> 0x1001CCE2 call 0x10006880 -> 循环 0x1001CD18..0x1001D1A2)
  └─ GDI    (0x1001D1D0 -> 0x1001D26E call 0x10006880 -> 循环 0x1001D2A0..0x1001D6AC)

每帧渲染循环顺序：
  1. WaitForSingleObject([0x1005EF30], ...)
  2. ★ 循环顶部记录 last_t（0x1001B00C / 0x1001CD42 / 0x1001D2C7）：
       if ([0x1005F128] > 0) { [0x1005F120] = timeGetTime(); }
  3. 渲染 + Present / Blt / SwapBuffers
  4. 循环底部调用限帧门闸 sub_10006AE0（0x1001BB6E / 0x1001D18E / 0x1001D694）
```

### 3.2 `sub_10006880` (`limiter_init`) 完整规则 `[静态读码]`

输入：`eax = maxfps ([0x100594E8])`，`ecx = refresh_hz ([0x1005EE48])`，`vsync ([0x100594EC])`。
1. 先清零 `[0x1005F130..0x1005F134] = 0`（100 ns 单位 64 位整数）与 `[0x1005F128] = 0`（ms 单位 `interval`）。
2. 计算有效 `fps`（`0x100068A4..0x100068B9`）：
   - 若 `maxfps < 0`（如 `-1`）→ `fps = refresh_hz`；
   - Else 若 `vsync == 0` → `fps = maxfps`（不钳位到 `refresh_hz`）；
   - Else（`vsync != 0` 且 `maxfps >= 0`）：若 `maxfps == 0` 或 `maxfps >= refresh_hz`（无符号比较 `jb`）→ `fps = refresh_hz`；否则 `fps = maxfps`。
3. 有效范围门控（`0x100068BB..0x100068C7`）：仅当 `0 < fps <= 1000` (`0x3E8`) 时计算周期，否则直接跳过赋值（`[0x1005F128]` 保持 **`0`**）：
   - `[0x1005F130..0x1005F134] = int64((1000.0f / fps) * 10000.0f)`（100 ns 步长）
   - `[0x1005F128] = int32(1000.0f / fps)`（毫秒整数截断，如 `fps=60 -> 16`、`fps=210 -> 4`）。
4. 加载 `gdi32.dll` + `dwmapi.dll`，解析 `DwmFlush`、`DwmIsCompositionEnabled`、`D3DKMTWaitForVerticalBlankEvent`、`D3DKMTOpenAdapterFromHdc`、`D3DKMTCloseAdapter`。

### 3.3 `sub_10006AE0` (`frame_gate`) 全分支走查与 `[0x1005F120]` 逐帧更新判决 `[静态读码]`

`sub_10006AE0` 内部由两级分支构成：**一级**决定是否先走 DWM/D3DKMT VSync 同步（`0x10006B21`）；**二级**（若跳过 VSync 或 VSync API 失败）在 `0x10006C4F` 检查 `interval ([0x1005F128])` 与 WaitableTimer 句柄 `([0x1005F138])`：

| 配置场景（`vsync`, `maxfps`, `interval`） | `sub_10006880` 算出的 `interval` (`[0x1005F128]`) | `sub_10006AE0` 一级分支（`0x10006AFA..0x10006B1B`） | `sub_10006AE0` 二级分支（`0x10006C4F..0x10006D90`） | `[0x1005F120]` (`last_t`) 是否每帧更新？ |
|---|---|---|---|---|
| **1. `vsync=0`, `1 <= maxfps <= 1000`**<br>*(含本机实测基线：`vsync=0, maxfps=60`)* | `int(1000/maxfps) > 0`<br>*(基线 `= 16 ms`)* | `0x10006B0B je 0x10006C4F`：**跳过** DWM/D3DKMT | `handle != 0` → `0x10006C72 je 0x10006CD1`：**`SetWaitableTimer` 绝对时刻节拍**（不写 `cur_t`）<br>`handle == 0` → `0x10006D66` **`timeGetTime + [0x1005F120] + Sleep` 兜底**（写 `cur_t`） | **是（每帧更新）**<br>`[0x1005F128] > 0` 成立，渲染循环顶部每帧写入 |
| **2. `vsync=1`, `1 <= maxfps < [0x1005EE48]`**<br>*(如 `maxfps=60 < 210`)* | `int(1000/maxfps) > 0`<br>*(60 fps `= 16 ms`)* | `0x10006B1B jb 0x10006C4F`：**跳过** DWM/D3DKMT | 同上：`handle != 0` → `0x10006C7E jb 0x10006CD1`（`SetWaitableTimer` 绝对时刻）；`handle == 0` → `0x10006D66` 兜底 | **是（每帧更新）**<br>`[0x1005F128] > 0` 成立，渲染循环顶部每帧写入 |
| **3. `vsync=1`, `maxfps >= [0x1005EE48]`** 或 `maxfps == 0` | `int(1000/refresh_hz)`<br>*(210 Hz `= 4 ms`；60 Hz `= 16 ms`；若 `refresh_hz==0` 或 `>1000` 则为 `0`)* | **进入 `0x10006B21` VSync 支路**：<br>① 非 Wine 且 (非 D3D9 或 Win≥8) 且 DWM 开启 → `DwmFlush()`；成功(`S_OK`)则直接 `ret`<br>② 否则 `call 0x10006A40` (`D3DKMTWaitForVerticalBlankEvent`)；成功则返回 `ret` | 若上述 VSync API 均失败且 `interval > 0`：`handle != 0` → `0x10006C80` **相对 `-interval` `SetWaitableTimer`**；`handle == 0` → `0x10006D66` 兜底 | **是（只要 `1 <= refresh_hz <= 1000` 使 `interval > 0`）**<br>即使走 `DwmFlush`/`D3DKMT` 返回，渲染循环顶部只看 `[0x1005F128] > 0` 仍每帧写 `[0x1005F120]` |
| **4. `maxfps == -1`（无论 `vsync=0/1`）** | `int(1000/refresh_hz)`<br>*(210 Hz `= 4 ms`；60 Hz `= 16 ms`；若 `refresh_hz==0` 或 `>1000` 则为 `0`)* | `0x10006B02 js 0x10006B21`：**无视 `vsync` 直接进入 `0x10006B21` VSync 支路**（同第 3 行） | 同第 3 行（VSync 失败后若 `interval > 0` 走 `0x10006C80` 或 `0x10006D66`） | **是（只要 `1 <= refresh_hz <= 1000` 使 `interval > 0`）**；若遇到异常显示器报告 `dmDisplayFrequency=0` 或 `>1000` 则 `interval=0` **不更新** |
| **5. `vsync=0`, `maxfps == 0`** 或 **`maxfps > 1000`**（任意导致 **`interval == 0`** 的配置） | **`0`**（`0x1000689A` 清零后被 `0x100068C7 jle` 跳过赋值） | 若 `maxfps==0`：`0x10006B0B je 0x10006C4F`<br>若 `maxfps>1000`：`0x10006B0B je 0x10006C4F` | `0x10006C55 test ecx, ecx; je 0x10006D90`：**直接返回，无限帧节流** | **否（不更新！保持初值 0）**<br>三条渲染循环 `0x1001B00C` / `0x1001CD42` / `0x1001D2C7` 均检查 `cmp [0x1005F128], 0; jbe skip`，直接跳过写 `[0x1005F120]`！ |

### 3.4 仪器可用性补充边界

1. **基线配置（`[gamemd] maxfps=60`, `vsync=false`）下**：`[0x1005F128]=16 > 0`，D3D9 渲染循环顶部 `0x1001B01A` **确定每帧更新 `[0x1005F120]`**。同时因 `CreateWaitableTimerExW` 生效（`[0x1005F138] != 0`），`[0x1005F124]` (`cur_t`) 保持 `0`（已被 W90 `framebeat_1794640742.csv` 实测证实）。
2. **`[0x1005F120]` 对静态/无重绘帧的局限 `[静态推断]`**：渲染线程循环顶部有 `WaitForSingleObject([0x1005EF30], ...)`，且写入在 `timeGetTime()`（1 ms 粒度，非 QPC）。因此轮询 `[0x1005F120]` 测得的是「**cnc-ddraw 渲染线程每轮循环启动时刻间隔**（即限帧放行层节拍）」，而非显示帧输出时刻；若改用 `vsync=false, maxfps=0`（完全无限帧），本通道直接失效（`interval=0`，`last_t` 不再更新）。

---

## 4 · 核验四：只读自检脚本 `verify_ddraw_globals.py`

脚本路径：[verify_ddraw_globals.py](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r06/W93_limiter/verify_ddraw_globals.py)（纯 Python 标准库，已在 Python 3.13.9 / 兼容 3.12 通过 `--help` 与本机进程只读自测）。

- **RVA `0x5EE30..0x5EE70`（16 个 DWORD）布局**：
  - `+0x5EE30`, `+0x5EE34`：`DEVMODEA` 内部字段（`dmPosition`/`dmDisplayOrientation` 等，通常为 0）
  - `+0x5EE38`：`DEVMODEA.dmBitsPerPel`（期望 `32`）
  - `+0x5EE3C`：`DEVMODEA.dmPelsWidth`（与当前显示器宽一致，如本机 `2560`）
  - `+0x5EE40`：`DEVMODEA.dmPelsHeight`（与当前显示器高一致，如本机 `1440`）
  - `+0x5EE44`：`DEVMODEA.dmDisplayFlags`（通常为 `0`）
  - **`+0x5EE48`**：`DEVMODEA.dmDisplayFrequency` — 期望等于当前 `EnumDisplaySettingsA(NULL, -1)` 返回的 `dmDisplayFrequency`（本机实测 `210` Hz；仅当 `EnumDisplaySettingsA` 失败时才为 `60`）。脚本通过本机只读 `EnumDisplaySettingsA` 动态获取期望刷新率（也支持 `--expect-hz` 显式覆盖），容差为 `0`（精确整数匹配；或若 `--expect-hz` 未传且 API 失败时容许 `{60}`）。
  - `+0x5EE4C..+0x5EE68`：`DEVMODEA` 尾部字段（`dmICMMethod`..`dmPanningHeight`）
  - `+0x5EE6C`：渲染器表面/上下文指针（非 `DEVMODEA` 成员，运行期非零即有效）
- **主断言**：
  - `[base + 0x594E8]` (`maxfps`) `== 60`（容差 `0`，可通过 `--expect-maxfps` 调整）
  - `[base + 0x5F128]` (`interval`) `in [15, 17]`（针对 `maxfps=60` 的 `int(1000/60)=16` 给出 `16 ± 1` 容差，默认严格校验 `16` 并单独标明可接受 `±1`）
  - `[base + 0x5EE48]` (`dmDisplayFrequency`) `== expected_hz`（动态取自 `EnumDisplaySettingsA`，本机为 `210`；若不匹配则打印完整 16-dword dump 与原始小端 hex 字节并退出非零，绝不崩溃）。
