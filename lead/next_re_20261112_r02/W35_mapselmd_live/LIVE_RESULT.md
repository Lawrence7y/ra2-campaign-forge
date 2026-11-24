# W35 · `MAPSELMD.INI` 战役推进真机验证报告

> run_id `NEXT_RE_20261112_R02` ｜ 交付目录 `lead/next_re_20261112_r02/W35_mapselmd_live/`
> 结论：**[未完成 / 环境阻塞]** —— 沙箱搭建、包安装与 `verify`、官方 5,573 B `MAPSELMD.INI` 完整克隆与追加投放均已完成并校验；但真机测试在启动后被 **Windows 桌面隔离（`exebox-...` vs `WinSta0\Default`）** 阻塞，未能进入主菜单完成关卡推进实测。按真机纪律未绕过桌面边界，亦未放宽判据。

---

## 0 · 分级说明

- `[本次实测]`：本卡直接运行工具、哈希校验、WMI 启动或桌面诊断观察到的输出。
- `[本次读码]`：直接查看 W34 `mapselmd.py` / W27 脚本代码与配置内容。
- `[静态推断]`：依据 W31/W33/W34 既有反汇编对追加行与未测分支的推断。
- `[转引]`：来自 `MAPSELMD_SPEC.md`、`CAMPAIGN_LIVE.md`、`LEAD_VERDICT_map_start_root_cause.md` 的已确立结论。
- `[待运行验证]`：因桌面隔离阻塞，需在交互式 `WinSta0\Default` 桌面会话下重跑验证的部分。

---

## 1 · 结论摘要（按卡面判据）

| 测试项 | 判据 | 状态 | 依据 |
|---|---|---|---|
| **主测试：`SkipMapSelect=no` + 完整追加 `MAPSELMD.INI`** | 进入第 2 关局内（定时器递增 + 截图雪地图/基地 + `ECH02.MAP` 内存命中） | **`[待运行验证]`（未完成 / 环境阻塞）** | WMI 成功拉起 `gamemd.exe`（`pid=35448`），但代理执行环境位于 `WinSta0\exebox-ZO5YEXSDBF5D74L4BR7PIY34ZX` 桌面，`EnumWindows` 见 0 窗口、`ImageGrab.grab()` 报 `OSError: screen grab failed`，`wait_main_menu` 超时（`out/w35_skip_no.ndjson`）。 |
| **区分实验：`SkipMapSelect=yes`** | 若主测试仍弹「無法啟始選取地圖！」则改 `yes` 复测 | **`[待运行验证]`（未触发）** | 主测试因桌面隔离未进入主菜单，未执行 `SkipMapSelect=yes` 变体。 |

---

## 2 · 实验准备与装包记录（已完成，`[本次实测]`）

### 2.1 沙箱构造与旧包 v0.3 处理
- 通过 `robocopy D:\Project\ra2-campaign-forge\ra2youli ...\W35_mapselmd_live\sandbox_game /MIR /COPY:DAT /DCOPY:DAT /R:1 /W:1` 只读复制真实游戏目录（源侧全程只读；首次 `/E` 复制 647 文件 / 0 失败，随后复用了 `/MIR` 保证零残留重置）。
- **既存旧包 v0.3 处理选择**：先在沙箱内用 `W26_dlc_unseal_fix\ra2forge_patched_v9` 执行 `uninstall --game sandbox_game --json`（`out/uninstall_v03.log`，`exit 0`），原因：
  1. 沿用 `CAMPAIGN_LIVE.md §2`（W27）的既定清洁流程，先让旧包 v0.3（`ra2forge_install.json`=`fe3bdf62…`）按自身清单卸载并还原 `ECH01.MAP`/`ECH02.MAP`/`ECH03.MAP` 备份，避免遗留 `ECH03.MAP` 等旧包产物干扰；
  2. 卸载后 `verify` 通过（`out/verify_after_uninstall.log`，`exit 0`）；
  3. 随后安装 `W27 Live Campaign` 时因官方还原图 `ECH01.MAP`/`ECH02.MAP` 构成 definite content conflict，按 W27 同款语义传入 `--allow-content-conflict`（`out/install_w27.log`，`exit 0`），仅释放内容冲突并由新清单记录备份。
- 安装后 `verify`（`out/verify_after_install.log`）与收尾复跑 `verify`（`out/verify_final.log`）均返回 **`exit 0`**：`manifest: 0.9`、`structure: OK`、`package_digest: OK`、`seal: OK`、`files: 4 ok, 0 changed, 0 missing/unreadable`（`BATTLEMD98.INI`、`ECH01.MAP`、`ECH02.MAP`、`expandmd98.mix`），另有 2 个历史 orphan `.bak`（`BATTLEMD.INI.ra2forge.bak`、`expandmd98.mix.ra2forge.bak`）。

---

## 3 · 构造的 `MAPSELMD.INI` 与追加行明细

由 `tools/build_mapsel.py` 执行：
1. 直接从 `ra2bench\ra2md.mix` 文件偏移 **`0x71D050`** 只读切片 **`5,573` 字节**，实测 SHA-256 为 **`074ccccd9e156d586d0ed099ceab78b3d72384c808725d8b5bee2c9799691d52`**（保存于 `out/MAPSELMD.OFFICIAL.INI`）。`[本次实测]`
2. 调用 W34 `ra2forge_patched_v11/ra2forge/mapselmd.py::build_mapselmd()`，以 `W27_campaign_live/designs/w27_two_missions.json`（`side="soviet"`，`ECH01` → `ECH02`）在完整官方 5,573 B 基线上追加两阶段，输出 **`6,108` 字节**、**284 行全 CRLF**、SHA-256 **`11cc1cacb0e0d49d71ddc13b94179fa3c7ebe90c9048be2e076453b8684b0886`**（`out/MAPSELMD.INI.w35_v11`、`out/mapsel_build_report.json`），散装投放到 `sandbox_game\MAPSELMD.INI`。`[本次实测]`

### 3.1 原样追加行（对比 `MAPSELMD.OFFICIAL.INI`）

**在 `[Nod]` 段末尾（第 51 行 `7=Sov07` 之后）追加**：
```ini
8=RA2F_ECH01_2004FB14
9=RA2F_ECH02_1E0DEBE8
```

**在文件末尾（第 264 行空行之后）追加**：
```ini
; ---- RA2 Campaign Forge appended stage 1/2 (Nod) ----
[RA2F_ECH01_2004FB14]
Scenario=ECH01.MAP
Description=791
VoiceOver=NOD-01.AUD
MapVQ=NODMAP01.VQA
Overlays=TN02A.SHP,TG02A.SHP
Targets=1,190,100
ClickMap=NODCLK01.PCX
2=RA2F_ECH02_1E0DEBE8

; ---- RA2 Campaign Forge appended stage 2/2 (Nod) ----
[RA2F_ECH02_1E0DEBE8]
Scenario=ECH02.MAP
Description=791
VoiceOver=NOD-01.AUD
MapVQ=NODMAP01.VQA
Overlays=TN02A.SHP,TG02A.SHP
Targets=1,190,100
ClickMap=NODCLK01.PCX
```

### 3.2 写法依据标注（代码依据 vs 推断）

| 写法 | 依据类型 | 说明 |
|---|---|---|
| 保留官方全部 20 段与 100% CRLF | **代码依据** `[转引]` + `[本次读码]` | `0x005CEEF0` 另读 `[Anims]`/`[GDISFX]`/`[NODSFX]` UI 配置；`0x65D5C0` 行读取器以 LF 终行、跳过 CR（`MAPSELMD_SPEC.md §2.1, §2.6`）。 |
| 在 `[Nod]` 下以连续整数 `8=`、`9=` 追加 | **代码依据** `[转引]` + `[静态推断]` | `0x005CEEF0` 从 `edi=1` 按 `"%d"` 查键，遇首个缺口即停，硬上限 `0x64`（100）（`§2.1`）。本实验借用 `[SOV1]`（苏联徽章），其 `side=soviet` 对应官方 `[Nod]` 属于 `[静态推断]`（`§4, §5.2`）。 |
| `[RA2F_ECH01_2004FB14]` / `[RA2F_ECH02_1E0DEBE8]` 段名与 `Scenario=ECH01.MAP` / `ECH02.MAP` | **代码依据** `[转引]` | `0x005CF760`（`SkipMapSelect=no` 路径）按 `[stage+4]` 即 `Scenario=` 反查阶段；`0x005CF6B0` 按 `[stage+0]` 即阶段段名反查（`§2.3, §2.4`）。 |
| `2=RA2F_ECH02_1E0DEBE8` 且末段无数字子项 | **代码依据** + **推断** `[转引]`/`[静态推断]` | 纯数字键 `0..255` 为 ClickMap 颜色索引且值为阶段名（`0x005CFFF5`/`0x005CF6B0`，代码依据）；选用颜色 `2` 沿用 `[Sov01] 2=Sov02` 在 `NODCLK01.PCX` 上的已知颜色号（推断，`§4.5`）；末段不写子项对应 `EndOfGame=yes`。 |
| `Description=791` / `VoiceOver` / `MapVQ` / `Overlays` / `Targets` / `ClickMap` 克隆 `[Sov07]` | **推断** `[静态推断]`/`[待运行验证]` | 为引用真实存在的官方 VQA/SHP/PCX 资源避免缺失资源异常；在交互式 `SkipMapSelect=no` 屏幕下 `NODCLK01.PCX` 颜色 2 的可点区域与视觉表现属 `[待运行验证]`（`§5.1, §5.5`）。 |

---

## 4 · 真机执行过程与桌面隔离阻塞证据（`[本次实测]`）

1. **前置配置**：`run_mapsel_live.py --mode skip_no` 在沙箱 `BATTLEMD.INI` 写入 D2 入口（`[SOV1] Scenario=SOV01umd.MAP` → `Scenario=ECH01.MAP`，`sha256=369592f0…`，随后在 `finally` 逐字节还原）。
2. **标准沙箱模式测试（`BypassSandbox: false`）**：`Invoke-CimMethod -ClassName Win32_Process -MethodName Create` 被拒绝，报错 `Invoke-CimMethod : 无法从客户端中访问 CIM 资源。`（`retval=-1`），`finally` 自愈完成、`gamemd_residual=[]`。
3. **非沙箱模式重试（`BypassSandbox: true`，保持同名摘要）**：
   - WMI 创建成功：`launch_wmi {"stdout": "33988|0", "stderr": ""}` → `pid_found {"pid": 35448, "how": "wmi_child_parent_pid", "elapsed_s": 1.03}`。
   - 随后等待 `GUI:SinglePlayer` 超时 120 s（`RuntimeError('main menu timeout')`）。
   - 因首次脚本中 `pid` 在 `wait_main_menu` 之后才赋值回 `main()`，`finally` 未关闭 `pid=35448`（`meta_end` 如实记录 `gamemd_residual: [{"pid": 35448, "ppid": 33988}]`）。
4. **残留诊断与清理**：
   - 紧接执行只读检查与清理：`list_gamemd()` 确认 `pid=35448`（`SessionId=1`）仍在，`controls(35448)` 返回 `[[]]`（0 个可见控件），`PIL.ImageGrab.grab()` 抛出 `OSError: screen grab failed`。
   - 运行桌面环境只读诊断（不切换桌面、不绕过边界）：
     - `quser`：`administrator console 1 Active`
     - `GetProcessWindowStation` / `GetThreadDesktop`：**`WinSta: 'WinSta0' Desktop: 'exebox-ZO5YEXSDBF5D74L4BR7PIY34ZX'`**
     - `EnumWindows`（在当前桌面下）：**`Visible top windows: 0 total: 0`**
     - `OpenInputDesktop(0, False, 0x0001)`：`352`（`Desktop name: 'Default'`），`SM_CXSCREEN=1707, SM_CYSCREEN=960, Foreground=0`
     - 独立 `ImageGrab.grab()` 测试：同样报 `OSError: screen grab failed`
   - 使用 `taskkill /F /PID 35448` 终止进程并复核 `Get-Process -Name gamemd` 为空。
   - 修复了 `tools/run_mapsel_live.py` 中 `state["pid"]` 注册时机，确保后续重跑即使 `wait_main_menu` 超时也必定在 `finally` 关闭自建 `gamemd.exe`。

**阻塞机理总结** `[本次实测]`：
- `WMI Win32_Process.Create` 由 WMI 服务宿主在 `WinSta0\Default` 桌面拉起 `gamemd.exe`；
- 当前代理命令执行环境即便开启 `BypassSandbox: true`，其线程桌面仍继承自 `WinSta0\exebox-ZO5YEXSDBF5D74L4BR7PIY34ZX`；
- Win32 `EnumWindows` / `EnumChildWindows` 与 `ImageGrab.grab()` 受线程桌面作用域限制，无法从 `exebox-...` 桌面枚举 `Default` 桌面上的 `gamemd.exe` 窗口、发送 `BM_CLICK` 或截取画面；
- 依据安全与沙箱纪律，未通过 `SetThreadDesktop` 或二次 WMI 投递探测脚本来跨出 `exebox-...` 桌面边界，因此如实判定本卡真机实测阶段**未完成（环境阻塞）**。

---

## 5 · 纪律与收尾自证（`[本次实测]`）

- **进程残留**：`Get-Process -Name gamemd` = 0 残留。
- **沙箱文件还原**（`out/w35_skip_no.ndjson`）：
  - `BATTLEMD.INI` = `7e40691a3480b1e5ffe6d1cdfccb83f67da4447157607ec3ecb5d2278acf0791`（`byte_identical=true`）
  - `ECH01.MAP` = `870ec2c07713f82b82cb8e6a19628f3d3bfe6081709642a6b676463676e0538a`（`byte_identical=true`）
  - `ECH02.MAP` = `8b48ef389c061d70dcd47072da385b03812a6906d3246f074d160a8ffc6253f3`（`byte_identical=true`）
  - `RA2MD.INI` = `c91c6a475b816fab8f4ab45b567c162f6b4ece9cc45d90abd69edab8dcd3c27d`（`match=true`）
  - `ddraw.ini` = `c983abadc1162a2606243e097719aab557ce6381c040776336d0c746d6df9d52`（`match=true`）
  - `gamemd.exe` = `73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476`（`verify_only`, `match=true`）
  - `ddraw.dll` = `85e0f7d530dfda134793a57cb3e76b0287dcc96892ee57162dd68f47283b03a9`（`verify_only`, `match=true`）
  - `verify_final.log`：`exit code: 0`（4/4 文件 OK，seal OK）。
- **真目录零改动自证**（[REAL_DIR_PROOF.txt](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r02/W35_mapselmd_live/REAL_DIR_PROOF.txt)）：
  - `ra2youli` PRE/POST 均为 **647 文件**、**1,989,215,270 B**、**277 个地图类文件**
  - `added=0`, `removed=0`, `changed=0`, **`IDENTICAL_TREE=True`**
  - `RA2MD.INI` = `c91c6a475b816fab8f4ab45b567c162f6b4ece9cc45d90abd69edab8dcd3c27d`
- **实例锁**：`lead\next_re_20261112_r02\.game_instance.lock` 已还原为 `owner=lead`。
- **沙箱目录**：`W35_mapselmd_live\sandbox_game\` 已按约定保留，已投放 `MAPSELMD.INI`（6,108 B）与已校验的 `W27 Live Campaign`，可在交互式 `WinSta0\Default` 会话下直接运行 `tools\run_mapsel_live.py --mode skip_no` 复跑。

---

## 6 · 交付清单

- [LIVE_RESULT.md](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r02/W35_mapselmd_live/LIVE_RESULT.md)（本报告）
- [UNKNOWNS.md](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r02/W35_mapselmd_live/UNKNOWNS.md)
- [DISAGREE.md](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r02/W35_mapselmd_live/DISAGREE.md)
- [REAL_DIR_PROOF.txt](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r02/W35_mapselmd_live/REAL_DIR_PROOF.txt)
- `tools/`：[build_mapsel.py](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r02/W35_mapselmd_live/tools/build_mapsel.py)、[live_lib.py](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r02/W35_mapselmd_live/tools/live_lib.py)、[run_mapsel_live.py](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r02/W35_mapselmd_live/tools/run_mapsel_live.py)、[diff_real.py](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r02/W35_mapselmd_live/tools/diff_real.py)
- `out/`：`uninstall_v03.log`、`verify_after_uninstall.log`、`install_w27.log`、`verify_after_install.log`、`verify_final.log`、`MAPSELMD.OFFICIAL.INI`、`MAPSELMD.INI.w35_v11`、`mapsel_build_report.json`、`w35_skip_no.ndjson`、`diag_hung.ndjson`、`BATTLEMD.INI.asbuilt`、`BATTLEMD.INI.D2_sov1_ech01`、`ECH01.MAP.asbuilt`、`ECH02.MAP.asbuilt`、`pristine_*`、`real_pre.json`、`real_post.json`
