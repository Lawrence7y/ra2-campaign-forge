# W63 · RUNLOG.md

> 执行者 Hy4（W63，非 Lead）｜所有时间 `+08:00`｜退出码均为实收，非推断
> 卡目录：`lead\next_re_20261112_r02\W63_route_a_e2e\`（只写本卡目录；git 只读）

## 0 · 时间线

| 时刻 | 阶段 | 事件 | 退出码 / 结果 |
|---|---|---|---|
| 23:25:37Z (=23:25 本地前) | 起步 | 创建卡目录 + `out\` + `work\` | — |
| 23:25:37Z | 起步 | 写 `STARTED.txt`（ISO + `Hy4` + `lock will be taken per trip`）**在读任何文件之前** | — |
| 23:25:37Z | 起步 | 写 `HEARTBEAT.txt`（Phase 0） | — |
| 23:26–23:35 | 读码 | 读 `LEAD_RULING_C_line_route_a_first.md` / `LEAD_VERDICT_W59.md` / `LEAD_VERDICT_C_line_E2E.md` / W60 `INPLACE_MODE.md` / `s5_cases.py` / v15 `builder.py`/`cli.py`/`mapselmd.py`/`feature_subset.py`/`resolve_integration.py`/`design.py`/`maplib.py`/`triggers.py` / W44 `w44_lib.py`/`w44_phase_*.py`/`w44_two_missions.json` / W55b `w55b_dual_track.py` 函数表 / W34/W39/W59 关于 `2=` 与 `cmp reg,0x64` 的讨论 | `[本次读码]` |
| 23:35:22–23:35:32 | 离线 | `w63_design.json` + `w63_feature_set.json`；`validate` OK 3 missions；`build` **exit 0**；包核验；MAPSELMD 变体 A/B；`real_pre`；robocopy；`sandbox_pre`；pristine；`verify_pre`=0；`uninstall v0.3`=0；孤儿 `.bak` 预处理；`install inplace`=0；`verify after install`=0；inplace 断言 | **offline exit 0** |
| 23:37:04 | 预检 | 独立桌面预检（不启动、不取锁）：`WinSta0\Default`、390 窗口 / 20 可见、`ImageGrab OK [2560,1440]`、pass=True | — |
| 23:37:11.780 | 真机 | `w63_run.py` 起跑；读锁 `owner=lead`、`gamemd` 活体 0 → 取锁 `owner=w63` | — |
| 23:37:12.293 | 真机 | WMI `Win32_Process.Create` 启动沙箱 `gamemd.exe`（launcher pid 35736） | retval=0 |
| 23:37:13.323 | 真机 | 找到 pid **34668** | — |
| 23:37:13.412 | 真机 | `step0_desktop_precheck`（WMI 后 1.1 s）：392 窗口 / 20 可见、`WinSta0\Default`、ImageGrab OK、pass=True | — |
| 23:37:35.451 | 真机 | 主菜单 `GUI:SinglePlayer` 就绪（21.03 s）；窗口 rect `[0,0,1707,960]` | — |
| 23:37:37 / 23:37:39 | 真机 | 点 `GUI:SinglePlayer` → `GUI:NewCampaign` → 战役菜单（`GUI:CampaignMenu`），截图 | — |
| 23:37:39.733 | 真机 | `real_mouse_click` 苏联徽章 `(210,285)` + 两次 Enter 跳简报 | — |
| 23:37:48.666 | 真机 | **进 M1**：`0x125C=RA2F_M1.MAP` `stage=0` `eog=0` `frame=75`（4.64 s）截图 | `level_entered` |
| 23:37:56.786 | 真机 | **通关 M1**：`GUI:Continue`、`frame` 210→210 停滞（8.12 s）截图 | `level_victory` |
| 23:38:02.943 | 真机 | 点 `GUI:Continue` → **推进 M2**：`0x125C=RA2F_M2.MAP` `stage=8` `eog=0` `frame` 15→92（4.16 s）截图 | `level_advance` |
| 23:38:10 | 真机 | **通关 M2**：`GUI:Continue`、`frame` 210 停滞（7.11 s）截图 | `level_victory` |
| 23:38:16 | 真机 | 点 `GUI:Continue` → **推进 M3**：`0x125C=RA2F_M3.MAP` `stage=9` **`eog=1`** `frame` 15→93（4.16 s）截图 | `level_advance` |
| 23:38:23.316 | 真机 | **通关 M3**：`GUI:Continue`、`frame` 210→210 停滞（7.11 s）截图 | `level_victory` |
| 23:38:25.319 | 真机 | 点最后一次 `GUI:Continue` | — |
| 23:38:25–23:39:36 | 真机 | EOG 观察：71.38 s / **47 次采样** `0x125C` 恒 `RA2F_M3.MAP`、`stage` 恒 9、`eog` 恒 1、`frame` 恒 210 → `no_fourth_start=True`；截图为片尾职员表 | — |
| 23:39:36.695 | 真机 | `trip_result`: `ok=true` `outcome=FULL_CHAIN_M1_M2_M3`；`run.ndjson` 198 行，`blocked/fatal/error events=0` | **run exit 0** |
| 23:39:42.482 | 真机 | `close_game`: `WM_CLOSE(hwnd=331606)` 未关 → `taskkill /PID 34668` → `/F /PID 34668`（均本卡自己的 pid）；`residual_own_pid=0` | — |
| 23:39:42.496 | 真机 | **放锁** `owner=lead` + 状态注明（ok/ outcome / residual=0） | — |
| 23:39:42.498 | 真机 | `meta_end` ok=True，写 `TRIP_RESULT.json` | — |
| 23:41:32–23:41:43 | 收尾 | `w63_finalize.py`：uninstall=0 → BATTLEMD 逐字节还原实算 → 21 配置还原 → `.sav` 清理 → 沙箱 `identical_tree=True` → 真目录 `IDENTICAL_TREE=True` → `verify_post`=0 → 删沙箱目录 → 复核锁 | **finalize exit 0** |
| 23:42 起 | 交付 | 写 `E2E_RESULT.md` / `REAL_DIR_PROOF.txt` / `UNKNOWNS.md` / `DISAGREE.md` / 本文件 | — |

HEARTBEAT 更新：Phase 0 / 1（读码）/ 2（离线完成）/ 3（离线 exit 0、真机前）/ 4（真机+收尾完成）。

## 1 · 命令与退出码总表（`out\cmd_*.log` 保存 argv/cwd/EXIT/stdout/stderr）

| 命令 | 日志 | EXIT |
|---|---|---|
| `python -m ra2forge validate work\w63_design.json` | （控制台） | 0 |
| `python -m ra2forge build --design … --out work\pkg --feature-set …` | （控制台） | 0 |
| `python w63_offline.py` | `out\offline.ndjson` | **0** |
| `robocopy REAL -> sandbox_game /E /COPY:DAT /DCOPY:DAT` | `cmd_robocopy_sandbox.log` | 1（成功码 0..7） |
| `verify --game sandbox --json`（PRE） | `cmd_verify_pre.log` | 0 |
| `verify --game sandbox --json`（v0.3） | `cmd_verify_v03.log` | 0 |
| `uninstall --game sandbox --json`（v0.3） | `cmd_uninstall_v03.log` | 0 |
| `verify --game sandbox --json`（卸载 v0.3 后） | `cmd_verify_after_uninstall_v03.log` | 0 |
| `install --package … --game sandbox --feature-set …` | `cmd_install_inplace_plain.log` | 0 |
| `verify --game sandbox --json`（装包后） | `cmd_verify_after_install.log` | 0 |
| `python w63_run.py` | `out\run.ndjson` / `out\TRIP_RESULT.json` | **0** |
| `python w63_finalize.py` | `out\finalize.ndjson` / `out\FINALIZE.json` | **0** |
| `uninstall --game sandbox --json`（收尾） | `cmd_uninstall_final.log` | 0 |
| `verify --game sandbox --json`（还原态） | `cmd_verify_post_restored_sandbox.log` | 0 |

## 2 · 产物清单（`out\`）

- 采样 / 事件：`offline.ndjson`(37,393 B)、`run.ndjson`(98,948 B)、`finalize.ndjson`(27,379 B)、`desktop_probe.ndjson`(411 B)
- 判定 JSON：`TRIP_RESULT.json`、`PACKAGE_VERIFY.json`、`MAPSELMD_VARIANTS.json`、`INPLACE_INSTALL.json`、`FINALIZE.json`
- 全树清单：`real_pre.json` / `real_post.json` / `sandbox_pre.json` / `sandbox_pre_uninstall.json` / `sandbox_post.json`
- 命令日志：`cmd_*.log`（9 份）
- 截图：`screen_*.png`（10 张，SHA 见 `E2E_RESULT.md` §3）
- 采样 ndjson：4 份（`offline` / `run` / `finalize` / `desktop_probe`）；判定 JSON 5 份；全树清单 5 份；`pristine\` 20 个文件（21 项基线中 `ra2forge_install.json.seal` 基线不存在）；MAPSELMD 变体 2 份
- 字节基线：`pristine\`（20 个文件；21 项基线里 `ra2forge_install.json.seal` 基线不存在）
- MAPSELMD 变体：`MAPSELMD.INI.variant_from1`（主用）/ `.variant_from2`（回退对照，未运行）
- 设计/构建产物在 `work\`：`w63_design.json`、`w63_feature_set.json`、`pkg\W63RouteA\`（BATTLEMD.INI / 3 张 MAP / MAPSELMD.INI / expandmd98.mix / BUILD_REPORT.txt / INSTALL.txt / ra2forge_package.json / ra2forge_plan_reconciliation.json / story.md）、`MAPSELMD.INI.variant_from*`、`tools\w63_*.py`

## 3 · 进程归因口径

`[本次实测]` 本卡 **launched 1**（WMI，pid 34668，仅沙箱 `gamemd.exe`）、**attached 1**（`OpenProcess(PROCESS_VM_READ|PROCESS_QUERY_INFORMATION)` 只读 RPM，未写内存/未下断点/未挂线程/未注入）；观察到的 gamemd 只此一个，属本卡自己，未触碰任何其他实例。收尾 `gamemd` 残留 0。离线阶段与收尾阶段 launched 0 / attached 0。

## 4 · 失败与重试记录（如实）

- 无失败、无重试、无回退。真机一趟即 `FULL_CHAIN_M1_M2_M3`；`run.ndjson` 中 `trip_blocked` / `FATAL` / `error_dialog_observed` / `advance_timeout` / `poll_timeout` **均为 0 条**。
- 因此 `MSG:UnableMapSelect` 弹窗原文、卡住分支、`2=` 回退对比 **本卡均无需产出**（按卡面「若失败请记录并回退对比」，主用变体 A 未失败）。这与「编造成功」的区别：所有成功判据都有独立 ndjson 事件 + 截图 + 逐帧 RPM 读数，不是自述。
- 唯一一次「非 0 退出码」是 `robocopy` rc=1，属 robocopy 文档规定的成功码（0..7），已按 W44/W55b 先例判成功。

## 5 · 纪律自检

| 项 | 结果 |
|---|---|
| `STARTED.txt` 先于读文件 | ✅ |
| HEARTBEAT 每 10 分钟 | ✅（Phase 0/1/2/3/4 共 5 次，覆盖 23:25–23:42） |
| 只写本卡目录 / git 只读 | ✅（未 commit、未改他卡交付物、未改 v15 工具链） |
| 离线造包装沙箱**不占锁** | ✅（离线阶段锁始终 `owner=lead`） |
| 真机每趟取锁 / 结束必放锁 | ✅（23:37:11 取 w63 → 23:39:42 放 lead；收尾复核仍 lead） |
| 不写 `ra2youli` | ✅（`IDENTICAL_TREE=True`，详见 `REAL_DIR_PROOF.txt`） |
| 不 `taskkill` 用户进程 | ✅（仅本卡 pid 34668） |
| 启动前配置字节副本 + 哈希；收尾逐字节还原实算 | ✅（21/21 处置完成：20 项 `byte_identical=True` + 1 项基线不存在则删除现存） |
| 禁止写内存/断点/注入/改 exe | ✅（`gamemd.exe` PRE=POST `73201cc0…`） |
| 结论分级 / 口径纪律 | ✅（见 `E2E_RESULT.md` §7、`UNKNOWNS.md`、`DISAGREE.md`） |
