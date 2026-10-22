# 开机会话指纹采集脚本 (GOAL-3T 待办 3)

对应 `lead/goal1_v11_env_gate_20261021/V11_ENV_GATE_DESIGN.md` §2：同一台机器、同一个
`gamemd.exe`，**31 档**（2026-10-19 14:31 开机会话，31.24 fps ×2）与 **10 档**
（2026-10-21 09:45 开机会话，8.76–11.64 fps ×4）严格按开机会话分离、零交叠。
本脚本把「开机会话的软硬件环境」全部落成一个可比对的 JSON 指纹，用来在两档之间做字段级 diff。

> 已推翻的假说：**GameViewer 私有窗口名不是变量**（`l1a_20261020` 无该窗口仍 31.24 fps）。
> 因此本脚本**刻意不采集任何窗口标题/窗口名**，避免把已排除的变量重新混进指纹。

---

## 1. 用法

```bash
# 最简：在任意目录执行，JSON 落到该目录（cwd，不是脚本目录）
python D:\Project\ra2-campaign-forge\lead\goal1_boot_fingerprint_20261022\boot_session_fingerprint.py

# 指定输出目录
python ...\boot_session_fingerprint.py --out-dir D:\out\fingerprints

# 跳过事件日志查询（只读，但某些受限账户会拒绝）
python ...\boot_session_fingerprint.py --no-boot-history

# 只落 JSON，不打印人读摘要
python ...\boot_session_fingerprint.py --quiet
```

环境要求：**Windows + CPython 3.12，零第三方包**（仅标准库 + `ctypes`）。
外部只调用 `powershell` / `wmic` / `powercfg`，全部是查询类子命令。

### 退出码

| 码 | 含义 |
|---|---|
| `0` | 采集完成。全部字段取到，或部分字段失败但失败原因已写入 JSON 的 `errors` |
| `1` | 脚本自身异常（未捕获的致命错误，traceback 打到 stderr） |
| `3` | 非 Windows 平台 |

### 输出文件

`boot_fingerprint_<YYYYmmddTHHMMSS>_<sha16>.json`，写入**当前工作目录**（可用 `--out-dir` 覆盖）。
文件编码 UTF-8、无 BOM、`\n` 换行、2 空格缩进。

---

## 2. 输出字段说明

### 2.1 顶层

| 字段 | 说明 |
|---|---|
| `schema` | `ra2cf.boot_fingerprint/1` |
| `fingerprint_id` | **会话指纹 ID**：`sha256(规范化 JSON(全部采集段 + process_id + captured_at_local))[:16]`。每次运行唯一 |
| `env_digest` | **环境摘要**：`sha256(规范化 JSON(稳定子集))[:16]`。**同一开机会话内多次运行应相等**，换开机会话则不等 —— 这是 V11-c「环境一致性」门禁的机器可读判据 |
| `fingerprint` | 上述两个 ID 的输入定义与排除清单（自描述） |
| `captured_at_local` / `captured_at_utc` | 采集时刻 |
| `host` | `computer_name`（运行期取 `COMPUTERNAME`）、`machine` |
| `errors` | `{字段路径: "异常类型: 原因"}`；**无失败时为 `{}`** |
| `collection_backends` | 每个 Win32_* 类实际用的后端（`powershell:Get-CimInstance` 或 `wmic`） |
| `backend_probe` | `powershell` 与 `wmic` 两条链路的**探测结果**（工具路径、是否可用、成功/失败的类、错误文本） |

`fingerprint_id` 与 `env_digest` 的分工：前者标识「这一次运行」，后者标识「这一个开机会话」。
做 31 档 vs 10 档比对时用 `env_digest` 分组，用各字段做 diff。

### 2.2 第 1 类：显示器（`displays`）

ctypes：`EnumDisplayMonitors` + `GetMonitorInfoW` + `EnumDisplaySettingsW(ENUM_CURRENT_SETTINGS)`，
另调 `shcore!GetDpiForMonitor` 取每台显示器 DPI（不可用时字段为 `null`）。

| 字段 | 说明 |
|---|---|
| `monitors[]` | 每台显示器一条 |
| `.device` | 如 `\\.\DISPLAY1` |
| `.primary` | 是否主显示器（`MONITORINFOF_PRIMARY`） |
| `.flags` / `.rect` / `.work_rect` | 原始 flags、显示器矩形、工作区矩形（含 width/height） |
| `.current_mode` | 当前模式：`width` / `height` / `refresh_hz` / `bpp` / `orientation` / `position` / `display_flags` |
| `.dpi.effective` | 有效 DPI（`GetDpiForMonitor(MDT_EFFECTIVE_DPI)`） |
| `monitor_count` | 枚举到的显示器台数 |
| `system_dpi` | `GetDpiForSystem()` |
| `system_metrics` | `SM_CXSCREEN` / `SM_CYSCREEN` / `SM_CMONITORS` / 虚拟屏宽高 |

### 2.3 第 2 类：显卡与驱动（`gpu`）

来源 `Win32_VideoController`。**PowerShell `Get-CimInstance` 与 `wmic` 两条链路都会被实际执行**，
各自结果记在 `backend_probe`；某类 PowerShell 取到就用 PowerShell，缺失的类用 `wmic` 补。

| 字段 | 对应 WMI 属性 |
|---|---|
| `.name` | `Name` |
| `.driver_version` | `DriverVersion` |
| `.driver_date` | `DriverDate` |
| `.adapter_ram` | `AdapterRAM` |
| `.current_width` / `.current_height` | `CurrentHorizontalResolution` / `CurrentVerticalResolution` |
| `.current_refresh_hz` | `CurrentRefreshRate` |
| `.video_mode_description` / `.video_processor` | 同名属性 |
| `.pnp_device_id` / `.status` / `.config_manager_error_code` | 同名属性 |

### 2.4 第 3 类：远程会话类型（`session`）

| 字段 | 说明 |
|---|---|
| `remote_session` | `GetSystemMetrics(SM_REMOTESESSION=0x1000)`，`0` = 非远程 |
| `process_session_id` | 本进程所在会话 ID（`ProcessIdToSessionId`） |
| `active_console_session_id` | `WTSGetActiveConsoleSessionId()`；无活动控制台时为 `null` |
| `env_session_name` | `%SESSIONNAME%`（`Console` / `RDP-Tcp#n` 等） |
| `monitor_count_sm` / `screen` | `SM_CMONITORS`、`SM_CXSCREEN`/`SM_CYSCREEN` |
| `process_id` | `GetCurrentProcessId()` |
| `computer_system` | `Win32_ComputerSystem` 的 `Manufacturer` / `Model` / `SystemType` / `TotalPhysicalMemory` / `HypervisorPresent` |
| `is_vm_guess` | 由 Manufacturer/Model/SystemType 关键字（virtual / vmware / vbox / hyper-v / kvm / qemu / xen / parallels / bochs / cloud）推断是否虚拟机 |

### 2.5 第 4 类：DWM（`dwm`）

| 字段 | 说明 |
|---|---|
| `composition_enabled` | `dwmapi!DwmIsCompositionEnabled` 的布尔结果 |
| `dwm_process_running` | 综合判断（CIM 有 dwm.exe 行 **或** toolhelp 快照里有 dwm.exe） |
| `dwm_exe_in_process_snapshot` / `dwm_exe_count_in_snapshot` | 纯 ctypes `CreateToolhelp32Snapshot` 结果 |
| `win32_process_dwm[]` | `Win32_Process where Name='dwm.exe'`：`process_id` / `parent_process_id` / `session_id` / `thread_count` / `working_set_size` / `creation_date` |

### 2.6 第 5 类：电源计划（`power`）

| 字段 | 说明 |
|---|---|
| `active_scheme_raw` | `powercfg /getactivescheme` 的**原始 stdout**（已解码） |
| `active_scheme_guid` | 从原始输出正则抽取的 GUID（小写） |
| `active_scheme_name` | 最后一个括号内的方案名（`Turbo` / `Balanced` / 本地化名） |
| `battery_present` | `Win32_Battery` 是否有实例；后端完全失败时为 `null` |
| `battery[]` | `Name` / `Status` / `BatteryStatus` / `EstimatedChargeRemaining` / `DeviceID` |

### 2.7 第 6 类：显示设备连接方式（`display_devices`）

「开机时外接显示器状态」无法回溯，故记录**当前**连接方式，作为可比对代理。
ctypes：`EnumDisplayDevicesW` 的 **adapter 级** 与 **monitor 级** 两次枚举。

| 字段 | 说明 |
|---|---|
| `adapters[]` | 每个显示适配器一条 |
| `.device_name` / `.device_string` / `.device_id` / `.device_key` | 原始字段 |
| `.state_flags` / `.state_flags_hex` / `.state_flag_names` | 原始 flags + 解码位名（`ATTACHED_TO_DESKTOP` 0x1 / `PRIMARY_DEVICE` 0x4 / `MIRRORING_DRIVER` 0x8 / `REMOVABLE` 0x20 / `DISCONNECT` 0x2000000 / `REMOTE` 0x4000000 / `MODESPRUNED` 0x8000000 …） |
| `.attached_to_desktop` / `.primary` | 上述两位的布尔化 |
| `.current_mode` | 该适配器 `ENUM_CURRENT_SETTINGS` |
| `.modes` | 该适配器**全部**模式的去重列表：`scanned` / `distinct_count` / `refresh_rates_hz[]` / `max_refresh_hz` / `modes[]`（超 64 条截断并置 `modes_truncated`） |
| `.monitors[]` | monitor 级 `EnumDisplayDevicesW`：`device_name` / `device_string` / `device_id` / `device_key` / `state_flags*` / `attached_to_desktop` / `primary` |
| `summary` | `adapter_count` / `attached_count` / `detached_count` / `attached[]` / `detached[]` / `primary[]` |

未挂到桌面的适配器（如 GameViewer 虚拟适配器）没有当前模式属正常，**不计入 `errors`**；
已挂到桌面却取不到模式才记错。

### 2.8 第 7 类：辅助可比字段（`system` + `processes` + `boot_history`）

| 字段 | 说明 |
|---|---|
| `system.uptime_ms_tick` | `GetTickCount64()` 原值（ms） |
| `system.uptime_human` | `Nd HHh MMm SSs` |
| `system.boot_time_utc_from_tick` / `_local_from_tick` | 由 tick 反推的开机时刻（注意：`GetTickCount64` **不计睡眠/休眠时间**） |
| `system.boot_key` | **开机键**：`LastBootUpTime` 归一化到分钟（`YYYY-MM-DDTHH:MM`）；缺失时回退 tick 反推值 |
| `system.boot_key_source` | 上面用了哪个来源 |
| `system.os` | `Win32_OperatingSystem` 的 `Caption` / `Version` / `BuildNumber` / `OSArchitecture` / `LastBootUpTime` / `InstallDate` / 内存 |
| `system.cpu` | `Win32_Processor` 的 `Name` / `Manufacturer` / `NumberOfCores` / `NumberOfLogicalProcessors` / `MaxClockSpeed` / `CurrentClockSpeed` |
| `system.python` | 解释器版本/实现/路径/平台 |
| `system.timezone` | 时区名、UTC 偏移秒、是否夏令时 |
| `system.collector` | 脚本绝对路径 + **脚本自身 sha256**（用于证明两次采集跑的是同一份脚本） |
| `processes.count` | 当前进程数（toolhelp 快照） |
| `processes.names[]` | 全部进程映像名 |
| `boot_history` | 只读查询 System 日志 `Microsoft-Windows-Kernel-General` Id 12(开机)/13(关机)，最多 24 条；失败时 `errors.boot_history` 记因 |

### 2.9 第 8 类：会话唯一标识

```
fingerprint_id = sha256( 规范化JSON(全字段 − {fingerprint_id, env_digest, errors}
                                  + session.process_id + captured_at_local) )[:16]
```

规范化 = `json.dumps(sort_keys=True, separators=(",",":"), ensure_ascii=False)`。
**没有硬编码任何本机标识**：机器名、进程号、时间、路径全部运行期取。

`env_digest` 的稳定子集**排除**（并在 `fingerprint.env_digest_excludes` 中自述）：
采集时刻、`process_id`、uptime、tick 反推的开机时刻（改用 `boot_key`）、进程列表与计数、
dwm 的 pid/创建时间、`boot_history`、`collection_backends`、`errors`。

---

## 3. 字段 ↔「31 档 vs 10 档」假说对应表

分组键 = `system.boot_key`（或 `env_digest`）。下表把 `V11_ENV_GATE_DESIGN.md` §2.3 的
四候选 A–D 与本脚本新增的可判别字段对齐；「预期差异」列是**该假说成立时两档应出现的差异**。

| 假说 | 代码 | 本脚本对应字段 | 预期差异（31 档 vs 10 档） |
|---|---|---|---|
| **A. 开机后 GPU/显示栈电源/时钟状态不同** | `V11 §2.3-A` | `power.active_scheme_guid`、`power.active_scheme_name`、`power.active_scheme_raw`、`power.battery_present`、`system.cpu.current_clock_mhz` / `max_clock_mhz` | 两档活动电源方案 GUID 不同（如 `Turbo` vs `Balanced`），或 `current_clock/max_clock` 比值不同 |
| **B. GameViewer 虚拟显示适配器被重新枚举** | `V11 §2.3-B` | `display_devices.adapters[].device_string`（含 `GameViewer` / `Virtual Display`）、`.state_flags_hex`、`.attached_to_desktop`、`display_devices.summary.detached[]` / `detached_count` | 10 档会话里出现一批 `DISPLAY2x` 虚拟适配器且全 `attached=false`（当前实测 10 个全 inactive）；31 档会话里数量/挂载状态不同 |
| **C. `ddraw` 的 `maxfps=-1` 跟随当前刷新率** | `V11 §2.3-C` | `displays.monitors[].current_mode.refresh_hz`、`display_devices.adapters[].current_mode.refresh_hz`、`.modes.refresh_rates_hz[]`、`.modes.max_refresh_hz`、`gpu.controllers[].current_refresh_hz` | 两档当前刷新率不同（如 210 Hz vs 60 Hz），或可用刷新率集合整体不同 |
| **D. 单纯时间/热状态（笔记本降频）** | `V11 §2.3-D` | `system.boot_key`、`system.uptime_ms_tick`、`system.cpu.current_clock_mhz` vs `max_clock_mhz`、`power.battery_present` | 开机时刻必然不同（已知）；若成立，`current/max clock` 在两档应有稳定差异 |
| **E. 远程会话类型（RDP / 控制台）** | 新增 | `session.remote_session`、`session.process_session_id` vs `session.active_console_session_id`、`session.env_session_name` | 31 档 = console（`remote_session=0`、两个 session id 相等），10 档 = RDP（`remote_session=1` 或 session id 不等） |
| **F. 显示器拓扑 / 主显示器变化** | 新增 | `displays.monitor_count`、`monitors[].primary`、`monitors[].rect`、`display_devices.summary.primary`、`display_devices.summary.attached_count` | 两档接的显示器台数、主显示器设备名或分辨率不同 |
| **G. DWM 合成开关差异** | 新增 | `dwm.composition_enabled`、`dwm.dwm_process_running`、`dwm.win32_process_dwm[].session_id` | 一档 DWM 关闭/未运行，另一档开启 |
| **H. 不是同一物理机 / 虚拟机切换** | 新增 | `session.computer_system.manufacturer` / `.model` / `.system_type`、`session.is_vm_guess`、`session.computer_system.hypervisor_present` | `Model` 不同 ⇒ 两档根本不在同一台机器上，整组不可横比 |
| **I. 期间 Windows / 显卡驱动更新** | 新增 | `system.os.version` / `build_number` / `install_date`、`gpu.controllers[].driver_version` / `driver_date` | 驱动版本或 OS build 在两档之间变化 |
| **J. 显卡/驱动集合变化（多卡切换）** | 新增 | `gpu.controllers[].name` / `.pnp_device_id` / `.status` / `.config_manager_error_code`、`gpu.controller_count` | 两档枚举到的 GPU 数量或设备 ID 不同 |
| — | 已排除 | *（刻意不采集窗口标题）* | GameViewer 私有窗口名已被 `l1a_20261020` 反例推翻，不进指纹 |

### 3.1 判读流程（真机时段）

1. 在 31 档会话里跑一次，存 `boot_fingerprint_*_<sha16>.json`。
2. 重启进入 10 档会话，再跑一次。
3. 先比 `env_digest`：**不等**才说明环境确实变了（相等 ⇒ 同一个开机会话，谈不上跨会话比对）。
4. 再按上表逐行 diff：`jq -S` 或任意 JSON diff 工具，重点看 A/B/C/E/G 五行对应的字段。
5. 若 `session.computer_system.model` 不同 ⇒ 走 H，两档不可横比，先修机位。
6. 若 `errors` 非空，先看 `backend_probe`：`powershell` 挂了会整片走 `wmic`，两档要用**同一后端**才可比。

### 3.2 与 V11 门禁的接口

- `V11-b（环境指纹，记录不拦）`：本 JSON 即该层产物。
- `V11-c（环境一致性，硬门禁）`：本趟 `system.boot_key` 必须**等于**基线臂首趟的 `system.boot_key`；
  不等 ⇒ 整组作废。`env_digest` 可作为更强的一致性判据（它还会捕获同会话内的显示拓扑变化）。
- 本脚本**不**产出 `pre_fps15`，也不判档位；档位仍由 `V11-a` 的实测 fps 判定。

---

## 4. 只读契约

脚本**不写**任何系统状态，唯一的写操作是输出 JSON 文件。

- 无 `winreg` / `winreg.SetValue` / `RegSetValue*` / `RegCreateKey*` / `RegDelete*`。
- 无 `subprocess` 的 `shell=True`；所有子进程都是 `[exe, args...]` 直调，`stdin=DEVNULL`。
- 子进程白名单（全部查询类）：
  - `powercfg /getactivescheme`
  - `wmic path <Win32_*> get ... /format:list`
  - `powershell -NoProfile -NonInteractive -Command <Get-CimInstance / Get-WinEvent>`
- 无 `Set-*` / `New-ItemProperty` / `reg add` / `Start-Process` / `Stop-Process`。
- Win32 侧只调 `Get*` / `Enum*` / `DwmIsCompositionEnabled` / `CloseHandle`；**不调** `ChangeDisplaySettings*`、
  `SetThreadExecutionState`、`OpenProcess`、`TerminateProcess`、任何 `Set*`。
- 唯一的 `os.makedirs` 用于创建输出目录；唯一的 `open(..., "w")` 用于写报告。

### 4.1 自查命令

```bash
cd lead/goal1_boot_fingerprint_20261022

# 1) 无注册表写入
grep -nE "winreg|RegSetValue|RegCreateKey|RegDeleteKey|RegDeleteValue|reg add|Set-ItemProperty|New-ItemProperty" \
  boot_session_fingerprint.py        # 期望：无输出

# 2) 无 shell 拼接
grep -n "shell=True" boot_session_fingerprint.py          # 期望：无输出

# 3) 子进程只有查询类命令
grep -nE "powercfg|wmic|powershell|Get-CimInstance|Get-WinEvent" boot_session_fingerprint.py

# 4) 只有一处写文件
grep -nE "open\(.*[\"']w|makedirs|os\.remove|os\.rename|shutil\.(copy|move)" \
  boot_session_fingerprint.py        # 期望：write_report 的 open + main 的 makedirs

# 5) 无 set 类 Win32 调用
grep -nE "ChangeDisplaySettings|SetThreadExecutionState|TerminateProcess|OpenProcess|SetConsole|SetPriority" \
  boot_session_fingerprint.py        # 期望：无输出

# 6) 每个 ctypes 调用都有 argtypes/restype（两数应相等，17/17）
grep -c "\.argtypes = " boot_session_fingerprint.py
grep -c "\.restype = " boot_session_fingerprint.py
```

---

## 5. 验收清单

- [x] **8 类字段全部有采集代码路径**
  1. 显示器 → `collect_displays`（`EnumDisplayMonitors` + `GetMonitorInfoW` + `EnumDisplaySettingsW`）
  2. 显卡与驱动 → `collect_gpu`（`Win32_VideoController`，PowerShell/wmic 双链路）
  3. 远程会话类型 → `collect_session`（`SM_REMOTESESSION` + `Win32_ComputerSystem.Model`）
  4. DWM → `collect_dwm`（`DwmIsCompositionEnabled` + `Win32_Process` dwm.exe + toolhelp）
  5. 电源计划 → `collect_power`（`powercfg /getactivescheme` + `Win32_Battery`）
  6. 显示设备连接方式 → `collect_display_devices`（`EnumDisplayDevicesW` adapter 级 + monitor 级 + 全模式枚举）
  7. 辅助可比字段 → `collect_system` + `collect_processes` + `collect_boot_history`
  8. 会话唯一标识 → `build_document`（pid + 时间 + 规范化 JSON 的 sha256 前 16）

- [x] **每个 ctypes 调用都有 `argtypes` / `restype`**：17 个 `argtypes` 声明、17 个 `restype` 声明；
  句柄类统一 `HANDLE = ctypes.c_void_p`（`CreateToolhelp32Snapshot` / `EnumDisplayMonitors` /
  `GetMonitorInfoW` / `EnumDisplayDevicesW` / `CreateToolhelp32Snapshot` 的 restype 均为句柄/BOOL，
  不存在 `int too long` 截断路径）。

- [x] **单字段失败不影响其它字段**：`_attempt()` 包单个字段、`_run_section()` 包整段、
  `collect_displays` 的枚举回调内部另有 try/except（回调抛异常会被 ctypes 吞成 0 并让枚举提前结束，
  故必须先兜住）、`collect_display_devices` 对每个适配器单独隔离 mode/monitor 探测。

- [x] **JSON 输出含 `errors` 与指纹 ID**：`errors`（无失败时 `{}`）、`fingerprint_id`、
  `env_digest`、`fingerprint`（输入定义自述）。

- [x] **零写操作**：见 §4.1 六条 grep，全部符合预期。

- [x] **`ast.parse` 通过**（用 `ast.parse` 而非 `py_compile`，避免落 `.pyc` 破坏 mtime 门禁）：

  ```bash
  python -c "import ast;ast.parse(open(r'<path>',encoding='utf-8').read());print('OK')"
  ```

---

## 6. 已知限制

| 限制 | 影响 | 处理 |
|---|---|---|
| `GetTickCount64` 不计睡眠/休眠 | tick 反推的开机时刻会偏晚 | `boot_key` 优先用 `LastBootUpTime`；tick 值只作辅助 |
| 「开机时外接显示器状态」不可回溯 | 只能拿到**采集时**的拓扑 | 真机时段应在**每次开机后尽快**跑一次；`boot_history` 提供历次开/关机时刻用于对齐 |
| `AdapterRAM` 是 uint32 | 显存 > 4 GB 时会回绕 | 只作参考，不做容量判据 |
| `wmic` 在 Windows 11 24H2+ 默认移除 | 无 wmic 时该链路记为 `backend_probe.wmic.ok=false` | PowerShell 链路为主；`collection_backends` 会显式标注实际来源 |
| `powercfg` / `Get-WinEvent` 可能需要权限 | 受限账户下这两个字段失败 | 失败原因进 `errors`，退出码仍为 0；可用 `--no-boot-history` 跳过事件日志 |
| 中文/日文控制台代码页 | `wmic` 输出可能乱码 | `_decode_console` 按 `locale.getencoding()` 判 CJK 后回退 `cp936`，最后兜 `cp1252`/`latin-1` |
