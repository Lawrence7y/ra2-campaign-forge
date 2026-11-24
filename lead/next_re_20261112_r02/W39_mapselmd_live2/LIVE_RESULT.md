# W39 · 真机验证卡：散装 `MAPSELMD.INI` 登记后战役能否 A1→A2

> run_id `NEXT_RE_20261112_R02` ｜ 交付目录 `lead/next_re_20261112_r02/W39_mapselmd_live2/`
> 执行环境桌面：**`WinSta0` / `Default`**（window_station / thread_desktop / input_desktop 三者全为 `Default`）
> 实测时间：2026-11-13 18:43–18:53 +08:00（≈20 min，单趟进游戏到判定 ≤1 min）
> 前置卡：W35（离线准备完成，真机被 `exebox` 桌面隔离阻塞）、W27（GUI 观测先例）

---

## 0 · 结论（一句话）

> **判定：能。** `[本次实测]`
> 在 `SkipMapSelect=no` + 散装追加 `MAPSELMD.INI`（6,108 B / 2 阶段）条件下，A1 由引擎原生 `survive(8)` 判胜 → 点 `GUI:Continue` → **进入 A2 局内**，卡面要求的 4 项硬指标全部成立。
> 同环境**负对照**（唯一变量：`MAPSELMD.INI` 换成官方 5,573 B、无追加阶段）在完全相同步骤点弹出 **「無法啟始選取地圖!」** 且 frame 冻结 ⇒ 成功可因果归因于「把 DLC 地图登记进散装 `MAPSELMD.INI`」。

**这不是「游戏没崩」当「功能正常」，也不是「截图看着像」当唯一证据**：见 §4 的 4 项独立硬指标 + §5 的单变量 A/B 对照。

### 0.1 结论的作用域限定（必须连带，防止外推）

`[本次实测]` 本卡入口沿用 W27 的 **D2 诊断变体**：沙箱内把官方 `BATTLEMD.INI` 的 `[SOV1] Scenario=SOV01umd.MAP` 改成 `Scenario=ECH01.MAP`，借**官方苏联徽章**进入 DLC 首关。

⇒ 结论严格表述为：

> **在劫持 `[SOV1]` 官方苏联入口、`SkipMapSelect=no`、散装追加 `MAPSELMD.INI` 已登记 2 阶段的条件下，DLC 地图 A1 判胜后能推进到 DLC 地图 A2 局内。**

**不得**外推成「追加式战役包 `RA2F1` 自身可从菜单进入并可通关」——W27 Q1 已实测 `GUI:CampaignMenu` 只有两个固定 side 徽章，追加 battle id 不生成 UI 条目（`[转引]` W27 `CAMPAIGN_LIVE.md §3`）。本卡未改变该事实，也未测试它。

---

## 1 · 分级口径

| 标签 | 含义（本卡用法） |
|---|---|
| `[本次实测]` | 本卡直接运行工具、哈希校验、WMI 启动、Win32 枚举、只读 RPM、截图得到的输出 |
| `[本次读码]` | 直接查看 W35/W27 驱动脚本、`ECH01.MAP`/`ECH02.MAP` 文本、安装清单 |
| `[静态推断]` | 依据 W31/W33/W34 既有反汇编对未测分支/地址语义的推断 |
| `[转引]` | 来自 `CAMPAIGN_LIVE.md`(W27)、`W35/LIVE_RESULT.md`、`LEAD_VERDICT_map_start_root_cause.md`、`MAPSELMD_SPEC.md` 的已确立结论 |
| `[待运行验证]` | 本卡未覆盖、需另立卡验证的部分 |

---

## 2 · 第 0 步：桌面可见性预检（**通过**，环境未阻塞）

`[本次实测]` 两份独立证据：

**(a) 开工前独立探针** `tools/desktop_probe.py` → `out/desktop_probe_standalone.json`

| 项 | 值 |
|---|---|
| window_station | `WinSta0` |
| thread_desktop | **`Default`** |
| input_desktop | **`Default`** |
| `EnumWindows` 顶层 / 可见 | **377 / 18** |
| 前 8 个可见窗口的 `EnumChildWindows` 控件数 | **25** |
| `PIL.ImageGrab.grab()` | **OK**, 2560×1440 |

**(b) 每趟游戏 WMI 启动后 ≤2 s 的内置 step-0 预检**（`live_lib.desktop_precheck`，写进各 ndjson 的 `kind=meta` 记录）

| 趟 | window_station | thread_desktop | input_desktop | EnumWindows 总/可见 | EnumChildWindows | ImageGrab | pass |
|---|---|---|---|---|---|---|---|
| `w39_skip_no` | WinSta0 | Default | Default | 380 / 19 | 25 | OK 2560×1440 | **true** |
| `w39_control_official` | WinSta0 | Default | Default | 379 / 18 | 25 | OK 2560×1440 | **true** |
| `w39_skip_yes` | WinSta0 | Default | Default | 383 / 19 | 25 | OK 2560×1440 | **true** |

> **与 W35 的差异已定位**：W35 的进程位于 `WinSta0\exebox-ZO5YEXSDBF5D74L4BR7PIY34ZX`，`EnumWindows` 见 0 窗口、`ImageGrab` 抛 `OSError: screen grab failed`（`[转引]` W35 `LIVE_RESULT.md §4`）。
> 本执行环境三趟均为 `WinSta0\Default`，与 W27 成功做 GUI 观测的桌面一致 ⇒ **桌面隔离阻塞已排除**。这是两个执行环境的桌面名差异，可复现定位。
> 按卡面：若任一预检失败本应立即停止并报「环境阻塞」；**本次两项均通过，故继续实测**。

---

## 3 · 开工前复核（三项硬性，`[本次实测]` 全通过）

产物 `out/prep_check.json`、`out/verify_pre.log`。

| 复核项 | 期望 | 实测 | 结论 |
|---|---|---|---|
| ① 沙箱 `verify` | exit 0 | `python -m ra2forge verify --game <W35 sandbox>`（cwd=`W26_dlc_unseal_fix/ra2forge_patched_v9`）→ **exit 0**，`manifest 0.9 / structure OK / package_digest OK / seal OK / files 4 ok, 0 changed, 0 missing`，2 个历史 orphan | ✅ |
| ② `MAPSELMD.OFFICIAL.INI` | 5,573 B / `074ccccd…d52` | 5,573 B / **`074ccccd9e156d586d0ed099ceab78b3d72384c808725d8b5bee2c9799691d52`** | ✅ |
| ② `MAPSELMD.INI.w35_v11` | 6,108 B / 284 行全 CRLF / `11cc1cac…886` | 6,108 B / **284 CRLF, 284 LF, all_crlf=true** / **`11cc1cacb0e0d49d71ddc13b94179fa3c7ebe90c9048be2e076453b8684b0886`** | ✅ |
| ③ 沙箱 `MAPSELMD.INI`（散装投放态） | 存在且 = `11cc1cac…` | 存在，6,108 B，**`11cc1cac…886`** | ✅ |

补充 `[本次实测]`：`[Basic]` 键值确认（`out/ECH01.MAP.asbuilt` / `ECH02.MAP.asbuilt`）
- `ECH01.MAP`: `Name=W27 A1`, `NextScenario=ECH02.MAP`, `EndOfGame=no`, **`SkipMapSelect=no`**
- `ECH02.MAP`: `Name=W27 A2`, `NextScenario=`(空), `EndOfGame=yes`, **`SkipMapSelect=no`**

沙箱基线逐文件校验（`prep_check` 前，8/8 全 match）：`BATTLEMD.INI=7e40691a…`、`ECH01.MAP=870ec2c0…`、`ECH02.MAP=8b48ef38…`、`RA2MD.INI=c91c6a47…`、`ddraw.ini=c983abad…`、`gamemd.exe=73201cc0…`、`ddraw.dll=85e0f7d5…`。

⇒ 沙箱状态**不 suspicious**，按卡面「可直接复用」直接复用 W35 的 `sandbox_game\`，**未新建副本**（理由：安装清单 `ra2forge_install.json` 的 `game_dir` 是 W35 绝对路径，原地复用避免元数据失配；且 `finally` 逐字节还原已验证）。

---

## 4 · 主测试：`SkipMapSelect=no` + 散装 `MAPSELMD.INI`（`w39_skip_no.ndjson`）

### 4.1 步骤（`[本次实测]`）

| t (+08:00) | 动作 | 观测 |
|---|---|---|
| 18:46:01 | 写 D2 入口（`BATTLEMD.INI` sha `369592f0…`，2,730 B）；`run_start` 记录 `mapsel_sha256=11cc1cac…` | `mapsel_present=true` |
| 18:46:01 | `pre_launch_guard` | `gamemd_processes=[]` |
| 18:46:01 | WMI `Win32_Process.Create`（`cmd /c cd /d <sandbox> && start "" gamemd.exe`） | `stdout="10336\|0"` |
| 18:46:02 | `pid_found` pid=38204 | step-0 预检 **pass=true** |
| 18:46:22 | `main_menu_ready` | `GUI:SinglePlayer`，19.52 s；hwnd 24515070，rect `[0,0,1707,960]`，title `Yuri's Revenge` |
| 18:46:23–26 | `BM_CLICK GUI:SinglePlayer` → `GUI:NewCampaign` | `GUI:CampaignMenu`（`GUI:Back / GUI:Difficulty / Slider3`，2 徽章） |
| 18:46:26 | 真实鼠标点苏联徽章 `(210,285)` | 3 s 后 `scen_filename=ECH01.MAP`, `scen_battle_idx=1` |
| 18:46:29–30 | `VK_RETURN`×2 跳过开场影片 | — |
| 18:46:32–38 | A1 加载并运行 | frame `0→23→70`；`scen_next=ECH02.MAP`, `scen_skip_mapsel=0`(=no), `battle_cnt=15` |
| 18:46:38 | `A1_ingame` | 只读 RPM 检索：`ECH01.MAP\|ascii=3`, `ECH02.MAP\|ascii=1`；截图 `screen_w39_skip_no_A1_ingame.png` |
| 18:46:41 | 胜利屏 | frame `164→196→210→210`；`GUI:Continue / GUI:HeadsTaken / GUI:ParTime / GUI:StandaloneScore / GUI:YourTime` |
| 18:46:43.247 | **`BM_CLICK GUI:Continue`** | `result=posted` |
| 18:46:43.261 | 紧接快照 | **`scen_filename=ECH02.MAP`**, frame=0（加载中） |
| 18:46:47.808 | 快照 | frame=44, `scen_stage_idx=8` |
| 18:46:50.311 | `A2_timer_confirm` | frame=123 |
| 18:46:53.275 | `A2_confirmed` | `outcome=A2_loaded` |
| 18:46:53.879 | `VK_ESCAPE` 开菜单 | 局内 Esc 菜单控件 |
| 18:47:00 | `close_game` → `meta_end` | 残留 `[]` |

### 4.2 卡面 4 项硬指标：**全部成立**（≥2 项即成功）

| # | 判据 | 原始证据（`out/w39_skip_no.ndjson`） | 结论 |
|---|---|---|---|
| 1 | **游戏定时器 `[0xA8ED84]` 真的在推进** | `A2_confirmed`: `frame_t1=44 → frame_t2=123`，`frame_delta=79` / 2.5 s ≈ **31.6 计数/s**；另有 `post_continue` 序列 `0→44→123→216`。与既有基线 31.25 计数/s（32 ms 定拍）一致 `[转引]` | ✅ |
| 2 | **`EnumChildWindows` 控件文本：局内 Esc 菜单** | `A2_esc_menu_controls.hits = ["GUI:AbortMission","GUI:GameControls","GUI:GameOptions","GUI:LoadGame","GUI:ResumeMission","GUI:SaveGame"]`；`visible` 另含 `GUI:DeleteGame`。截图 `screen_w39_skip_no_A2_esc_menu.png` 显示局内菜单（遊戲控制/載入遊戲/儲存遊戲/刪除遊戲/放棄任務/回到任務），**非主菜单** | ✅ |
| 3 | **只读 RPM 检索 `ECH02.MAP` 标记命中** | `A2_confirmed.counters_t2.scen_filename = "ECH02.MAP"`（`[Scen+0x125C]`）；`memory_search post_continue_A2`: `ECH02.MAP\|ascii=2`（另有 `ECH01.MAP\|ascii=2`）。`battle_cnt=15` | ✅ |
| 4 | **截图（雪地图 + 基地）** | `screen_w39_skip_no_A2_ingame.png`（976,338 B，1707×960）：白色雪原 + 苏军建造场/核电站/锤镰建筑群 + 完整侧边栏。已人工读图确认，**非加载屏、非错误框** | ✅ |

另：`run_outcome = {"outcome":"A2_loaded","mode":"skip_no"}`。

> 补充观测 `[本次实测]`：A2 加载后 `scen_stage_idx` 由 `0` 变为 `8`（`[Scen+0x35A0]` 2 字节读数）。追加行在 `[Nod]` 下用的是 `8=`/`9=` 连续整数键，与该值数值上相容；但**地址语义来自静态反汇编 `[静态推断]`，本卡未做符号级证明，不据此宣称"引擎选中了第 8 阶段"**。

### 4.3 一处工具缺陷（如实记录，不影响结论）

第一趟同参数运行（18:44:23–18:45:07）在 `A1_ingame` 的 `memory_search` 处因 `Sink.step` 的 console `print` 用 GBK 编码、遇到 latin-1 内存上下文字节 `\xde` 抛 `UnicodeEncodeError` 而中止；当时 A1 已加载（frame 0→27→74），`finally` 自愈完整（关游戏、还原、残留 0）。
`[本次实测]` 修复：`Sink.step` 的进度行改用 `ensure_ascii=True` + 防御式 try/except（`tools/live_lib.py`），另加 `PYTHONIOENCODING=utf-8`。原始记录保留为 `out/w39_skip_no.run1_toolcrash.ndjson`。**这是驱动脚本缺陷，不是游戏行为**，已修复后重跑成功。

---

## 5 · 负对照：官方 `MAPSELMD.INI`（`w39_control_official.ndjson`）

`[本次实测]` 单变量：仅把散装 `MAPSELMD.INI` 换成官方 5,573 B（`074ccccd…`，`control_official_mapsel_applied` 记录 `sha256=074ccccd…`）；D2 入口、`SkipMapSelect=no`、已装 `W27 Live Campaign`、全部其它条件不变。

| 阶段 | 观测 |
|---|---|
| A1 | 与主测试**逐项一致**：frame `0→23→70→162→193→210→210`，`scen_filename=ECH01.MAP`, `scen_next=ECH02.MAP`, `scen_skip_mapsel=0`, `battle_cnt=15` |
| 18:50:27 | `GUI:Continue` 出现（frame 210） |
| 18:50:29.968 | `BM_CLICK GUI:Continue` |
| 18:50:29.983 | **立即 `GUI:OK` 对话框**，frame 冻结 **210**，`scen_filename` 仍 `ECH01.MAP`（**未**变成 ECH02.MAP）；控件 `["GUI:Blank","GUI:OK","Yuri's Revenge"]`，`#32770` 对话框容器 |
| 截图 | `screen_w39_control_official_error_dialog.png`：黄字 **「無法啟始選取地圖!」** + 「確定」按钮。放大裁切 `out/crop_w39_error_text.png`（7× LANCZOS）逐字可辨第 4 字为 **始**(女+台) 而非 **動** ⇒ 字形确为 **「啟始」不是「啟動」**（与卡面 `MSG:UnableMapSelect` 描述一致；W27 报告中记作「啟動」应为 OCR 误读 `[转引]`） |
| 内存 | `UnableMapSelect\|ascii=2`, `無法啟始選取地圖\|utf16le=2`, `RA2F_ECH01\|ascii=0`, `RA2F_ECH02\|ascii=0` |
| 结果 | `run_outcome = error_dialog_GUI_OK`；`meta_end` 残留 `[]` |

⇒ **因果锁定 `[本次实测]`**：同一执行环境、同一桌面、同一入口、同一 A1、同一 `GUI:Continue` 点击；唯一差别是散装 `MAPSELMD.INI` 是否含追加 2 阶段。追加 → 进 A2 局内；不追加 → 「無法啟始選取地圖!」。因此「能推进」不是环境或流程偶然，而是登记生效。

---

## 6 · 区分实验：`SkipMapSelect=yes`（`w39_skip_yes.ndjson`）

**说明（`[本次实测]` 口径）**：卡面规定「**失败**时立即做区分实验」。本卡主测试**成功**，故该实验**未作为必需项触发**；但为覆盖 `yes` 分支、且不额外烧时间（同一驱动、同一环境、约 1 min），本卡**仍额外执行**，作为补充实测。结果如实记录，不冒充"失败分支收窄"已达成。

改动：`set_skip_mapsel(ECH01/ECH02, "yes")`（`skip_yes_applied`: `ech01=e435fd36…`, `ech02=6eb41516…`，+1 B）；散装 `MAPSELMD.INI` 仍为追加版 `11cc1cac…`。

| 阶段 | 观测 |
|---|---|
| A1 | `A1_ingame`: `scen_skip_mapsel=1`（**yes 已被引擎读入 `[Scen+0x34B0]`**），`scen_filename=ECH01.MAP`, `scen_next=ECH02.MAP`, frame 74 |
| 胜利 | frame `167→198→210→210`，`GUI:Continue` |
| 18:51:48.466 | `BM_CLICK GUI:Continue` |
| 18:51:48.481 | **`GUI:OK` 对话框**，frame 冻结 210，**`scen_filename=""`（被清空）**，而 `scen_next` 仍 `ECH02.MAP`、`scen_skip_mapsel=1` |
| 截图 | `screen_w39_skip_yes_error_dialog.png`，**SHA-256 与负对照错误框截图完全相同**（`9bafe337…`）⇒ 同一个「無法啟始選取地圖!」/「確定」对话框 |
| 内存 | `UnableMapSelect\|ascii=2`, `無法啟始選取地圖\|utf16le=2`, **`RA2F_ECH01\|ascii=2`, `RA2F_ECH02\|ascii=3`**（追加阶段名在进程内存中可见，证明散装 INI 内容确被该路径读入） |
| 结果 | `run_outcome = error_dialog_GUI_OK`；`meta_end` 残留 `[]` |

### 6.1 对「4 条失败分支收窄」的诚实结论

`[本次实测]` **未能把失败收窄到 4 条分支中的某一条**，原因如下：

1. `memory_search` 在**两个错误趟**里都同时命中 `Invalid side|ascii=1`、`Unable to initialize choices|ascii=1`、`Invalid stage|ascii=1`、`Unable to create font|ascii=1` —— 这 4 个是 **exe 静态字符串**，无论走哪条分支都常驻 ⇒ **只读 RPM 字符串检索不能判别实际走了哪条分支**（`[静态推断]` + `[本次实测]`）。需断点/符号级跟踪才能区分，本卡纪律禁止注入/attach。
2. `SkipMapSelect=yes` 与 `no` 的**可见结果相同**（同一个 `MSG:UnableMapSelect` 对话框），**没有**「换成另一条失败分支」的外观差异。
3. 但 `yes` 分支有一个**可观测的内部差异**：Continue 后 `scen_filename` 由 `ECH01.MAP` 变为 **空串**（负对照是冻结在 `ECH01.MAP`），且 `scen_skip_mapsel=1` 全程成立 ⇒ 两路确实不同（`[转引]` 卡面机制 + `[本次实测]` 状态差），只是都汇到同一个 CSF 标签。

⇒ 卡面期望的「区分实验把 4 条失败分支进一步收窄」**本卡未达成**，如实记为 `[待运行验证]`（见 `UNKNOWNS.md`）。这不改变主测试「能推进」的结论。

---

## 7 · 真机纪律与收尾自证（`[本次实测]`）

| 项 | 结果 |
|---|---|
| 单实例锁 | 开工 18:43:56 取 `.game_instance.lock` `owner=w39`（gamemd 残留 0 才取）；收尾 18:53:13 还原 `owner=lead` |
| 启动方式 | 三趟均 `Invoke-CimMethod Win32_Process.Create`，`pre_launch_guard` 每趟 `n=0`，`pid_found how=wmi_child_parent_pid` |
| 禁止注入 | 仅 `OpenProcess(PROCESS_VM_READ\|PROCESS_QUERY_INFORMATION)` + `ReadProcessMemory`（只读）、`EnumWindows/EnumChildWindows`、`PostMessageW(BM_CLICK)`、`keybd_event`、`mouse_event`、`ImageGrab`。**未**改 exe/dll、未写目标进程内存、未下断点/挂线程/注入 |
| `finally` 自愈 | 三趟均 `close_game`（WM_CLOSE → taskkill → taskkill /F）→ `restore_file` 逐字节还原 `BATTLEMD.INI`/`ECH01.MAP`/`ECH02.MAP`/`MAPSELMD.INI` → `restore_configs` 还原 `RA2MD.INI`/`ddraw.ini` → `meta_end(kind=meta_end)`；每趟 `gamemd_residual=[]` |
| 收尾残留 | `Get-Process -Name gamemd` = **0** |
| 沙箱收尾 8/8 哈希 | 全部与基线/还原目标逐字节相等（`BATTLEMD.INI 7e40691a…`、`ECH01.MAP 870ec2c0…`、`ECH02.MAP 8b48ef38…`、`MAPSELMD.INI 11cc1cac…`、`RA2MD.INI c91c6a47…`、`ddraw.ini c983abad…`、`gamemd.exe 73201cc0…`、`ddraw.dll 85e0f7d5…`） |
| `verify` 收尾 | `out/verify_post.log` → **exit 0**，`structure OK / package_digest OK / seal OK / files 4 ok, 0 changed, 0 missing` |
| 真目录零改动 | `REAL_DIR_PROOF.txt`：PRE/POST 均 **647 文件 / 1,989,215,270 B / 277 地图类**，`added=0, removed=0, changed=0`, **`IDENTICAL_TREE=True`**；4 个基线 SHA 全对（`RA2MD.INI=c91c6a47…`, `gamemd.exe=73201cc0…`, `ddraw.dll=85e0f7d5…`, `ra2forge_install.json=fe3bdf62…`） |
| 时间预算 | 单趟进游戏到判定 `w39_skip_no` 59 s / `control_official` 52 s / `skip_yes` 52 s，均 ≪8 min；总时长 ≈20 min ≪80 min |

> 本卡**复用** W35 的 `sandbox_game\`（卡面允许「可直接复用」），所有改动都发生在沙箱内并被 `finally` 逐字节还原；本卡自身写域仅 `W39_mapselmd_live2\`。

---

## 8 · 交付清单

```
W39_mapselmd_live2/
├── LIVE_RESULT.md              （本文件）
├── UNKNOWNS.md
├── DISAGREE.md
├── REAL_DIR_PROOF.txt
├── tools/
│   ├── desktop_probe.py        桌面可见性独立探针（含桌面名）
│   ├── prep_check.py           开工三项复核 + 真目录 PRE 清单
│   ├── live_lib.py             W35 驱动库适配版（+step0 预检、+GBK 编码修复、路径改指 W39/out，复用 W35 sandbox）
│   ├── run_mapsel_live.py      三模式可复跑驱动（skip_no / control_official / skip_yes）
│   ├── manifest.py             真目录逐文件清单（转引 W27）
│   └── diff_real.py            PRE/POST 对比 → REAL_DIR_PROOF.txt
└── out/
    ├── desktop_probe_standalone.json, prep_check.json
    ├── verify_pre.log, verify_post.log, verify_final.log(转引 W35)
    ├── real_pre.json, real_post.json
    ├── MAPSELMD.OFFICIAL.INI, MAPSELMD.INI.w35_v11, MAPSELMD.INI.w39_deployed
    ├── ECH01.MAP.skip_yes, ECH02.MAP.skip_yes, BATTLEMD.INI.D2_sov1_ech01
    ├── BATTLEMD.INI.asbuilt, ECH01.MAP.asbuilt, ECH02.MAP.asbuilt, pristine_*
    ├── w39_skip_no.ndjson            主测试事件流（53 条）
    ├── w39_skip_no.run1_toolcrash.ndjson   首趟编码缺陷原始记录（已归档）
    ├── w39_control_official.ndjson  负对照事件流
    ├── w39_skip_yes.ndjson          区分实验事件流
    ├── screen_w39_*.png             三趟截图（主菜单/战役菜单/A1/A2/胜利/错误框/Esc 菜单）
    └── crop_w39_error_text.png       错误框文案 7× 放大裁切（辨「啟始」用）
```

### 复跑方式

```powershell
$env:PYTHONIOENCODING='utf-8'
python -u <W39>\tools\run_mapsel_live.py --mode skip_no
python -u <W39>\tools\run_mapsel_live.py --mode control_official
python -u <W39>\tools\run_mapsel_live.py --mode skip_yes
```

> 前提：持 `.game_instance.lock`、无 `gamemd` 残留、W35 沙箱处于 §3 基线态、执行环境线程桌面为 `WinSta0\Default`。
