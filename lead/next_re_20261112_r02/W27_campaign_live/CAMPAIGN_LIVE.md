# W27 · C 线第一张真机卡：战役注册 / 关卡推进 / 跨进程存读档

> run_id `NEXT_RE_20261112_R02`｜执行：W27 subagent｜2026-11-13 13:34–14:39 +08:00
> 工具 `W26_dlc_unseal_fix/ra2forge_patched_v9/`（`TOOL_VERSION = 0.9`）
> 写域仅 `lead/next_re_20261112_r02/W27_campaign_live/`；实例锁开工认领、收尾恢复 `owner=lead`。

## 0 · 三问速判（按卡面判据）

| 问 | 判据 | 结论 | 一句话依据 |
|---|---|---|---|
| **Q1 包能否被引擎注册（菜单里看得到吗）** | 条目出现且可选中 = 成立 | **不成立**（引擎层注册成立，菜单层不成立） | 引擎全局 Battle 表 Count=**15**（14 官方 + `RA2F1`），`RA2F1` 对象含 `CD=2 / ECH01.MAP`；但 `GUI:CampaignMenu` 全屏只有 2 个官方徽章（盟军/苏联），控件文本枚举不到新条目，右侧 7 条空槽不可点，`GUI:Back` 只返回单人菜单。逐层检查记录见 §3。 |
| **Q2 能否推进到下一关（`NextScenario` 链）** | 进入 A2 = 链生效 | **不成立**（链触发但 A2 未启动；且只在 D2 诊断变体下观测到） | A1 加载并由引擎自身 `survive(8)` 触发器在 ~8 s 达成目标，出现「任務完成」+ `GUI:Continue`；点 `GUI:Continue` 后弹「無法啟動選取地圖!」+「確定」，frame 冻结。D3 证明 `ECH02.MAP` 直接启动完全正常 ⇒ 失败在「胜利后下一关解析」，不是 A2 文件坏。 |
| **Q3 跨进程存读档是否成立** | 能读回且状态一致 = 成立 | **成立（仅在 D3 诊断变体下）**；按卡面「Q1/Q2 任一处有对局」的前提，本卡**未取得包本身（追加战役）的局内对局** | D3 变体下 `SAVE4823.SAV`（559,553 B，SHA-256 `4800374b…b1e0`）→ 完全退出残留 0 → 重启 → `GUI:LoadSavedGame` / `GUI:Load` → 回到同一 A2 雪地图、同一苏军基地、frame 198→276、Esc 菜单为局内菜单（`GUI:ResumeMission/SaveGame/AbortMission`）、存档文件读后哈希不变。详见 §5。 |

> ⚠️ **能力边界**：Q2/Q3 的正向数据来自**沙箱内的诊断变体**（D2/D3，改写官方 `BATTLEMD.INI` 的 `[SOV1] Scenario`，见 §6），不是「追加战役 `RA2F1`」本身的链路。因此上表 Q2/Q3 的「成立」**不得**外推成「ra2forge 追加包可通关/可存读档」。按卡面顺序，追加包链路仍是**未验证**；卡在哪里见 §7。

---

## 1 · 沙箱构造与核对（真实 `ra2youli` 全程只读）

| 项 | 真实 `D:\Project\ra2-campaign-forge\ra2youli` | 沙箱 `W27_campaign_live\sandbox_game\` |
|---|---|---|
| 文件数 | 647 | **647** ✓ |
| 总字节 | 1,989,215,270 | **1,989,215,270** ✓ |
| 地图类文件（`.yrm`+`.mpr`+`.map`） | **277** | **277** ✓ |
| `RA2MD.INI` | `c91c6a475b816fab8f4ab45b567c162f6b4ece9cc45d90abd69edab8dcd3c27d` | 同 ✓ |
| `gamemd.exe` | `73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476` | 同 ✓ |
| `ddraw.dll` | `85e0f7d530dfda134793a57cb3e76b0287dcc96892ee57162dd68f47283b03a9` | 同 ✓ |
| `ra2forge_install.json` | `fe3bdf62…`（v0.3 旧包，mtime 2026-10-22） | 复制同值，随后在**沙箱**内 uninstall |

- 复制方式：`robocopy <real> <sandbox> /E /COPY:DAT /DCOPY:DAT /R:1 /W:1`，rc=1（复制成功、无错误），耗时 7.9 s。源侧全程只读；大 `.mix` 是 NTFS **硬链接**（非符号链接/重解析点），复制退化为普通文件，内容一致。
- **真实目录未被写的证明**：开工前全量清单 `out/real_pre.json`，收尾全量清单 `out/real_post.json`（逐文件 rel / size / mtime_ns / sha256）。`out/tools/diff_real.py` 结果：`added=0, removed=0, changed=0, IDENTICAL_TREE=True`；`RA2MD.INI` 收尾仍为 `c91c6a47…3c27d`，地图类仍 **277**。
- 每次启动前 `Get-Process -Name gamemd` 守卫 = 0 才启动；每阶段收尾 `WM_CLOSE → taskkill → taskkill /F`（仅本代理自己 WMI 启动的 pid），核对残留 0。全部 10 次游戏实例串行（P0×3、P0b、P1a、P1b、P2a、P3、P4×3、P5×2、P6 — 见各 `out/*.ndjson` 的 `pre_launch_guard` / `instance_closed` / `*_done` 记录）。

## 2 · 两关战役包与安装（工具层，全部有原始输出/退出码）

- design：`designs/w27_two_missions.json`（`package.id = w27-campaign-live`，`campaign.name = W27 Live Campaign`，`campaign.description = "W27LIVE two-mission chain probe A1 to A2"`，2 关 `ECH01` / `ECH02`，标题 `W27 A1` / `W27 A2`）。
- `python -m ra2forge validate` → `OK: 2 mission(s)`，**exit 0**（`out/validate.log`）。
- `python -m ra2forge build --design … --out pkg` → **exit 0**（`out/build.log`）。产物 `pkg/W27 Live Campaign/`：`ECH01.MAP`(4671 B) / `ECH02.MAP`(4647 B) / `BATTLEMD98.INI`(385 B) / `expandmd98.mix`(9352 B) / `ra2forge_package.json` / `BUILD_REPORT.txt`。
- 构建自检（`BUILD_REPORT.txt`）：`[PASS] ECH01.MAP: [Basic] NextScenario=ECH02.MAP -> chained, EndOfGame=no`；`[PASS] ECH02.MAP: NextScenario=(空), EndOfGame=yes`；`[PASS] BATTLEMD98.INI: [Battles] 15=RA2F1 -> ECH01.MAP`；`[PASS] expandmd98.mix: 2 entries, 0 INI`。A1 目标 `{"type":"survive","seconds":8}` 编译成 `ElapsedTime(8) → WinnerIs(player)`（引擎原生触发器，无作弊）；A2 用 `survive(1800)` 保持局内。
- 清旧包：`uninstall --game <sandbox> --json` → **exit 0**，`status=completed`，9 条 actions（移除 `expandmd98.mix`/`ECH03.MAP`/`ECH02.MAP`/`ECH01.MAP`/`BATTLEMD98.INI`/清单，还原 3 个 `.bak`），仅 1 条 degraded-mode 警告（v0.3 无 seal）。`out/uninstall_v03.log`。
- `verify` 卸载后 **exit 0**（无清单）。`out/verify_after_uninstall.log`。
- 装新包第一次：`install` → **exit 1**，`install blocked by preflight - no file has been written`，2 条 definite content conflicts（`ECH01.MAP`/`ECH02.MAP` 是 uninstall 还原出来的官方原图，新清单不认领）。`out/install_w27.log`。
- 按 W22/W23 既定语义加 `--allow-content-conflict`（只释放 definite content conflict、逐条记录）→ **exit 0**：`created BATTLEMD98.INI`、`backup+replaced ECH01/02.MAP`、`created expandmd98.mix`、`written ra2forge_install.json.seal`、`written ra2forge_install.json`。`out/install_w27_allow.log`。
- `verify` 装后 **exit 0**：`manifest 0.9 [seal era] / structure OK / package_digest OK / seal OK / files: 4 ok, 0 changed, 0 missing`；2 个历史 orphan（`BATTLEMD.INI.ra2forge.bak`、`expandmd98.mix.ra2forge.bak`，来自复制源，不阻断）。`out/verify_after_install.log`。
- 收尾复跑 `verify` → **exit 0**，同上（`out/verify_final.log`）。`BATTLEMD98.INI` 收尾哈希 `61ed5013603e4dbf323e46db2cc59bc788aa87d5b9f1a88ba802be008a3ec53c`，与安装时一致。

## 3 · Q1 逐层菜单枚举（原始控件文本）

启动：`WMI Win32_Process.Create` → `cmd /c cd /d <sandbox> && start "" gamemd.exe`；主菜单就绪耗时 **20.03 s**，证据控件 `GUI:SinglePlayer`（`out/p0_recon.ndjson:6`）。窗口标题 `Yuri's Revenge`，类 `Yuri's Revenge`。

| 层 | 操作（控件文字 / 点击） | 看到的控件文本 / 窗口标题 | 耗时 |
|---|---|---|---|
| S0 主菜单 | 无 | `Static GUI:MainMenu`；`Button GUI:SinglePlayer / GUI:WWOnline / GUI:Network / GUI:Options / GUI:MoviesAndCredits / GUI:ExitGame` | 启动后 20.0 s |
| S1 单人游戏 | `BM_CLICK GUI:SinglePlayer` → posted=True | `Static GUI:SinglePlayerMenu`；`Button GUI:NewCampaign / GUI:LoadSavedGame / GUI:Skirmish / GUI:MainMenu` | 1.5 s |
| S2 战役 | `BM_CLICK GUI:NewCampaign` → posted=True | `Static GUI:CampaignMenu`；`Button GUI:Back`；`Static GUI:Difficulty / GUI:Harder`；`msctls_trackbar32 Slider3`；**5 个空文字 Static**（含两个徽章 rect `[94,39,326,130]` / `[94,243,326,334]`）；**无 `ListBox` 有条目**（隐藏 ListBox id=1109 `LB_GETCOUNT=0`）；`Button GUI:Load`(隐藏) | 1.5 s |
| S2 画面证据 | 截图 `out/screen_p0b_S2_campaign_menu.png` | 左侧两张自绘徽章：盟军鹰 + 「點選盟軍圖示以開始盟軍戰役。」、苏联锤镰 + 「點選蘇聯圖示以開始蘇聯戰役。」；右侧 7 条**空**列表槽 + 「上一頁」红钮（= `GUI:Back`）；无第三条战役条目 | — |
| S3 返回 | `BM_CLICK GUI:Back` → posted=True | 回到 `GUI:SinglePlayerMenu`（`GUI:NewCampaign / LoadSavedGame / Skirmish / MainMenu`），**不是翻页** | 1.5 s |

尝试过的其它层（全部如实记录，`out/p1a_explore.ndjson`）：
- 物理鼠标点击经**校准**：点 `GUI:SinglePlayer` 矩形中心 `(481,147)` 后确实进入 `GUI:SinglePlayerMenu`（`calibration_verdict.physical_mouse_click_worked=True`）⇒ 控件 rect 是可用的屏幕坐标（DPI 虚拟化一致）。
- 键盘 `VK_DOWN×3 / VK_UP / VK_RETURN`：画面与控件文本**完全不变**（仍 `GUI:CampaignMenu`）。
- 右侧 7 条空槽逐个真实点击（rect 分隔线物理 y=199+42k，换算逻辑坐标后命中槽内）：**全部无状态变化**（mode=0、frame=0、控件集合不变）。
- 两张徽章真实点击：`badge_0` → 盟军开场动画（`out/screen_p1a_badge_0.png` 放大徽章），`badge_1` → 盟军过场（`out/screen_p1a_badge_1.png`）。⇒ 点击有效，但只有两个官方战役。
- `GUI:LoadSavedGame` 的列表/存档逻辑未被 Q1 使用（属 Q3）。

**引擎层注册证据（只读 RPM，非控件文本）**：
- `out/p1b_memory.ndjson`：引擎全局 Battle 表 `0xA83D08` = **15**（`battle_table_count`）；`0xA83CF8` 附近 dump 见 `memory_dump.battle_table_header`。
- RA2F1 对象 dump（`memory_dump.around_RA2F1`）：`0x…3164 "RA2F1"`、`0x…31a4 "RA2F1"`、`0x…31dc "ECH01.MAP"`，中间 `02 00 00 00` = `CD=2`。与 `docs/re/fs_mix_load_chain_deep.md §2.3`（表基址 `0xA83CF8`、Count `0xA83D08`、元素 `0x3A0`、名字 `+0x24`）一致。
- 主菜单内存即命中 `RA2F1|ascii=2`、`ECH01.MAP|ascii=1`、`W27LIVE|utf16le=2`，且 `W27LIVE` 上下文为 **`MISSING:'W27LIVE two-mission chain probe A1 to A2'`** ⇒ 引擎把 `Description` 当 CSF 标签查、未命中。
- 官方 `BATTLEMD.INI` 注释原文：`Description = string file label of text description of campaign for player choice list`，官方取值 `DESC:ALL1` / `DESC:SOV1`。

**Q1 结论**：按卡面判据「条目出现且可选中」= **不成立**。引擎确实把追加战役并进了全局表（Count 15 / RA2F1 对象），但 `GUI:CampaignMenu` 是**两个固定 side 徽章**，追加 battle id 不生成 UI 条目。「没看到」我们已用控件文本 + 截图 + 逐层点击穷举，不是只看一眼。

### 3.1 两个决定性诊断（澄清根因，均为沙箱内、逐字节还原）

| 诊断 | 改动（仅沙箱） | 观测 | 结论 |
|---|---|---|---|
| **D1** | `BATTLEMD98.INI` 的 `Description=W27LIVE…` → `Description=DESC:ALL1`（已知有效 CSF 标签）；385→354 B | `W27LIVE|utf16le` 由 2 → **0**（`MISSING:` 文案消失）；Battle Count 仍 **15**；`GUI:CampaignMenu` 截图与控件文本**逐项相同**（仍 2 徽章 / 7 空槽 / `GUI:Back`） | **CSF 文本不是不可见原因**。`out/p2a_D1_diagnostic.ndjson`、`out/screen_p2a_D1_campaign_menu.png` |
| **D4** | battle id `RA2F1` → `YURI1`（`15=YURI1` + `[YURI1]`） | 引擎内存 `YURI1|ascii=2`、`RA2F1|ascii=0`，Count=15；但该趟 `GUI:NewCampaign` 点击未生效、快照落在主菜单 ⇒ **菜单证据不可用（未验证）** | 只证明「改 id 后引擎仍并表」；不能判定是否出现第三徽章 |

> D1/D4 均已逐字节还原：`BATTLEMD98.INI` 收尾 `61ed5013…`（`D1_restore/D4_restore: byte_identical=true`）。D2/D3 改的 `BATTLEMD.INI` 收尾 `7e40691a3480b1e5ffe6d1cdfccb83f67da4447157607ec3ecb5d2278acf0791`（与开工基线一致，`byte_identical=true`）。

## 4 · Q2 `NextScenario` 链（只在 D2 诊断变体下取得数据）

**D2**（项目自有 runbook `docs/re/a3_campaign_install_runbook.md:53` 的一行改写）：沙箱内 `[SOV1] Scenario=SOV01umd.MAP` → `Scenario=ECH01.MAP`，`BATTLEMD98.INI` 保持原样。理由：Q1 证明追加战役不可选，只能借官方苏联徽章进入我们的 DLC 地图，以观测链与存读档。

时间线（`out/p3_D2_chains.ndjson`，截图 `out/screen_p3_I1_*.png`）：

| t | 操作 | 控件文本 / 画面 | 帧计数 |
|---|---|---|---|
| 14:09:51 | `BM_CLICK GUI:SinglePlayer` → `GUI:NewCampaign` | `GUI:CampaignMenu` | 0 |
| 14:09:52 | 真实鼠标点苏联徽章 `(210,285)` | 开场动画（屏幕仅窗口标题 `Yuri's Revenge`） | 0 |
| 14:09:55–56 | `VK_RETURN`×2（跳过影片） | — | 0→15 |
| 14:09:59–14:10:05 | 无输入 | 局内加载/运行 | 15→203 |
| **14:10:07** | 无输入 | **`Button GUI:Continue` + `Static GUI:HeadsTaken / GUI:ParTime / GUI:StandaloneScore / GUI:YourTime`**；截图 `screen_p3_I1_briefing_or_later.png` 显示黄字 **「任務完成」** 及我方苏军基地（建造场/电厂/步兵） | 210 |
| 14:10:09 | `BM_CLICK GUI:Continue` → posted=True | **`GUI:OK` 对话框**；截图 `screen_p3_I1_A1_ingame.png` / 放大 `crop_map_error.png` 显示 **「無法啟動選取地圖!」/「確定」** | 210（冻结） |
| 14:10:09–14:12:54 | 无输入（脚本在等胜利屏） | 错误框持续；frame 恒 210 | 210 |
| 14:12:54–14:13:03 | 无输入 | 游戏自行重置：frame→0→31→61，短暂出现局内 Esc 菜单 `GUI:ResumeMission / GUI:SaveGame / …`，随后主菜单 | 61 |
| 14:13:05+ | 无输入 | 进程自行退出（counters=None） | — |

- **目标文本 / 达成方式（如实记录）**：A1 的目标是地图自身编译的 `survive 8 s`（`ElapsedTime(8) → WinnerIs`）。**没有**改存档、改内存、注入或作弊；「加速」发生在 **design 阶段**：把首关目标设计成 8 秒生存，使引擎原生触发器在 ~8 s 自然判胜（这是本卡允许的「游戏内合法手段加速」的等价物，且已在 design JSON 与 BUILD_REPORT 中留痕）。另按了两次 `VK_RETURN` 跳过开场影片（普通 UI 输入）。
- **从 A1 结束到 A2 开始之间的界面变化**：`任務完成` 结算屏 → 点 `GUI:Continue` → **直接弹出错误对话框**，frame 冻结；**没有出现 A2 的加载/局内画面**。
- **D3 判别**（`out/p4_D3_q3.ndjson` 首趟，`out/screen_J1_ingame.png`）：把 `[SOV1] Scenario` 直接指向 `ECH02.MAP`，苏联徽章 → `frame=62/102` 持续推进、无错误框，截图为**雪地 A2 地图 + 苏军基地 + 完整侧边栏** ⇒ **A2 文件本身可被引擎加载**。
- **Q2 结论**：**不成立**。链被触发到「结算屏 → Continue → 尝试启动下一关」这一步，但 A2 没启动，错误表现是弹窗「無法啟動選取地圖!」/「確定」+「確定」按钮、frame 冻结于 210。D3 排除了「A2 地图坏」。
- ⚠️ **不确定性**：该观测来自**劫持 SOV1 的 D2 变体**。引擎的战役推进可能依赖 `BATTLEMD.INI` 的战役序列（而非仅地图 `[Basic] NextScenario`），因此错误可能部分是「劫持官方战役」的副作用，**不能**断定是 ra2forge 包的 `NextScenario` 写法错误。追加战役 `RA2F1` 本身因 Q1 不可选，**其 Q2 链未验证**。

## 5 · Q3 跨进程存读档（只在 D3 诊断变体下取得数据）

`out/p5_q3.ndjson`，D3 变体（`[SOV1] Scenario=ECH02.MAP`）。两趟独立实例 K1（存档）/ K2（读档）。

1. **局内存档**（14:30:46 → 14:30:59）
   - K1 进入 A2 局内：`frame=82`、无错误框、截图 `screen_K1_ingame.png`（雪地图 + 苏军基地 + 侧边栏，credits 12012）。
   - `VK_ESCAPE` → 局内菜单 `GUI:ResumeMission / GUI:GameControls / GUI:LoadGame / GUI:AbortMission / GUI:SaveGame / GUI:DeleteGame / Static GUI:GameOptions`（`#32770` 容器，与 W1/W4 一致）。
   - `BM_CLICK GUI:SaveGame` → 存档对话框：`Static GUI:SaveMissionMenu / GUI:SaveMission`、`Button GUI:Save`(rect `[813,151,896,168]`) / `GUI:Back`、`ListBox`(8 项)、`Edit`(名称框 rect `[269,331,534,346]`)。
   - 做了什么（全部普通 UI 输入，未改存档文件）：`LB_SETCURSEL(0)` + 真实鼠标点首槽 → 真实鼠标点名称框 → `keybd_event` 输入 `W27Q3SAVE` → `WM_SETTEXT` 同名 → `BM_CLICK GUI:Save`。
   - 产物：`sandbox_game\SAVE4823.SAV`，**559,553 B**，SHA-256 **`4800374bed3793ab1d292fd897a65eabe69c2dbdbcae9989cf9faa0a716bb1e0`**；副本 `out\save_SAVE4823.SAV`（同哈希）。存档前 8 个 `.sav` → 后 9 个，`added=[SAVE4823.SAV]`、`changed=[]`。
2. **完全退出**：`WM_CLOSE → taskkill → taskkill /F`，`Q3_process_exit.residual=[]`，`instance_closed.all_gamemd_residual=[]`。
3. **重启读档**（14:31:30 → 14:31:38）
   - K2 主菜单 → `GUI:SinglePlayer` → `GUI:LoadSavedGame` → 载入对话框：`Button GUI:Load`（`load_dialog_buttons=["GUI:Load"]`）。
   - 按名称选中：`Q3_load_selected.selected=null`（列表项名未匹配到 `W27Q3SAVE`/`SAVE4823`，**如实记录**；实际是该存档已是高亮首槽）。`BM_CLICK GUI:Load` → posted。
   - **进入成功**：`frame=198`（`Q3_load_ingame`，elapsed 0.0 s）→ `frame=276`；无错误弹窗；`VK_ESCAPE` 后局内菜单 `GUI:AbortMission / GUI:DeleteGame / GUI:GameControls / GUI:GameOptions / GUI:LoadGame / GUI:ResumeMission / GUI:SaveGame`。
   - 画面证据 `out/screen_K2_after_load.png`：与存档前 `out/screen_K1_after_save.png` **同一张 A2 雪地地图、同一苏军基地布局、同一侧边栏与建筑图标**；credits 28314（游戏在读档后继续运行、采矿收入增长，属于正常推进，非状态重置）。
   - 内存标记（只读 RPM）：`ECH02.MAP|ascii=3`、`W27LIVE|utf16le=4`；`W27 A2|ascii/utf16le=0`（地图 `Name` 不以明文驻留，该标记不可用作关卡身份判据，已在 §7 记入未覆盖）。
   - 存档副本读后哈希 `4800374b…b1e0`，`save_copy_matches=true`（读档未改写存档文件）。
4. **Q3 结论**：**成立（D3 诊断变体）** —— 能读回、落在同一 DLC 地图、局内菜单/帧计数/画面一致、我方建筑与单位在画面中可见、存档文件字节未变。
   - ⚠️ **特别说明**：读档时引擎确实重新解析了包内资源（散装 `ECH02.MAP` + `expandmd98.mix`），但这是从 `SOV1` 入口进入的，**不是**从追加战役 `RA2F1` 的菜单条目进入的；追加包自身的 Q3 仍未验证。
   - 「我方单位是否存在」的可观测证据是**画面**（卡面允许「画面/控件文本/状态值」）：`screen_K2_after_load.png` 中苏军建造场、电厂、战车工厂、磁能反应堆及单位清晰可见；未从控件文本或已证语义的内存地址读到「单位清单」，不夸大。

## 6 · 诊断变体清单与还原自证（全部沙箱内）

| ID | 改动 | 目的 | 还原 |
|---|---|---|---|
| D1 | `BATTLEMD98.INI`: `Description=W27LIVE…` → `Description=DESC:ALL1` | 判定 CSF 是否为不可见根因 | `D1_restore.byte_identical=true`，SHA `61ed5013…` |
| D2 | `BATTLEMD.INI`: `[SOV1] Scenario=SOV01umd.MAP` → `ECH01.MAP` | 借官方徽章进入 A1，测 Q2 | `D2_restore.byte_identical=true`，SHA `7e40691a…` |
| D3 | 同上改 → `ECH02.MAP` | 判定 A2 文件是否可加载；提供 Q3 对局 | `D3_restore.byte_identical=true`，SHA `7e40691a…` |
| D4 | `BATTLEMD98.INI`: `15=RA2F1`/`[RA2F1]` → `15=YURI1`/`[YURI1]` | 判定菜单是否按 battle id 生成徽章 | `D4_restore.byte_identical=true`，SHA `61ed5013…`；本趟菜单快照落在主菜单，**结论未验证** |

所有变体文件原件保存在 `out/BATTLEMD.INI.asbuilt`、`BATTLEMD.INI.D2_sov1_ech01`、`BATTLEMD.INI.D3_sov1_ech02`、`BATTLEMD98.INI.asbuilt`、`BATTLEMD98.INI.D1_desc_all1`、`BATTLEMD98.INI.D4_yuri1`。

## 7 · 收尾自证 / 能力边界 / 未覆盖

### 7.1 还原与残留
- 沙箱 `RA2MD.INI` 收尾 **`c91c6a475b816fab8f4ab45b567c162f6b4ece9cc45d90abd69edab8dcd3c27d`**（每趟 `restore_configs` 从 `out/pristine_*` 逐字节复制 + 实算 SHA 双自证，`all_match=true`）；`ddraw.ini` = `c983abad…9d52`、`RA2MD.INI.benchbak` = `c91c6a47…`；`gamemd.exe`/`ddraw.dll` 未改（`verify_only`，哈希同 §1）。
- `BATTLEMD.INI`/`BATTLEMD98.INI` 收尾哈希同 §2/§6；`verify` 收尾 **exit 0**、seal OK、4 文件全 ok。
- `gamemd` 残留 **0**（`p5_done` / `p6_done` / 最终 `Get-Process`）；实例锁已恢复 `owner=lead`（14:39:24）。
- 真实 `ra2youli`：`IDENTICAL_TREE=True`，0 增 / 0 删 / 0 改，`RA2MD.INI` = `c91c6a47…`，地图类 **277**。
- `sandbox_game/` **保留未删**（1.9 GB；报告在此明确写明：为便于 Lead 复核，未删除；如需省空间可整目录删除，交付数据已在 `out/`、`designs/`、`pkg/`）。

### 7.2 能力边界（哪层是引擎、哪层是工具）
- **工具层（ra2forge 0.9）**：design→build→uninstall/install/verify 全链 exit 0；产物哈希/清单/seal 自洽；`NextScenario` 字符串正确写入 `[Basic]`。这一层**已闭合**。
- **引擎层（本次实测新证）**：① 通配 `BATTLEMD*.INI` 枚举 + 全局 Battle 表合并（Count=15、RA2F1 对象）成立；② `Description` 是 CSF 标签位，纯文本 → `MISSING:'…'`（与 Lead 的 `LEAD_FINDING_campaign_text_is_csf.md` 一致）；③ `GUI:CampaignMenu` 只呈现两个固定 side 徽章，追加 battle id 不生成 UI 条目（D1 证伪 CSF 为根因）；④ DLC 地图本身可被引擎加载（A1/A2 均实测）；⑤ 引擎原生 `survive` 触发器可判胜；⑥ 跨进程存读档在 DLC 地图上成立；⑦ 胜利后「下一关」解析会失败（弹「無法啟動選取地圖!」），但**是否由劫持 SOV1 引起未定**。
- **未触碰的层**：未做静态逆向（不属本卡）、未改任何 exe/dll、未写目标进程内存、未下断点/挂线程/注入/抓 dump。

### 7.3 未覆盖与不确定项（详见 `UNCOVERED.md`）
1. 追加战役 `RA2F1` 的**菜单可达性**：全部穷举只覆盖 `GUI:CampaignMenu` 一屏、两种方向键、7 个空槽、2 个徽章；未覆盖其它分辨率 / 汉化版本 / 是否有第三页（`GUI:Back` 实测是返回而非翻页）。「没看到」≠「绝对不存在」，但已用控件文本+画面+点击穷举证伪到本环境可观测范围。
2. D4（battle id = `YURI1`）的菜单快照因该趟点击未生效落在主菜单 ⇒ **菜单是否按 id 生成第三徽章，未验证**。
3. Q2 根因未定：D3 排除 A2 文件坏，但未证明是 `[Basic] NextScenario` 写法、战役序列状态、还是 D2 劫持副作用。追加包自身 Q2 未验证。
4. Q3 的 `Q3_load_selected=null`（列表项名未匹配）；读档成功依赖高亮首槽，未验证「按名字精确选中任意存档」。
5. 「我方单位」仅有画面证据，无控件文本或已证语义的内存计数。
6. `W27 A1`/`W27 A2` 地图名不以明文驻留内存 ⇒ 内存字符串标记**不能**用作关卡身份判据（已用画面/frame/控件文本替代）。
7. 未测：其它难度、其它战役包、多关>2、跨包升级后存读档、不同 ddraw 后端。

## 8 · 交付清单
- `designs/w27_two_missions.json` — 两关 design
- `pkg/W27 Live Campaign/` — build 产物（含 `BUILD_REPORT.txt`）
- `sandbox_game/` — 游戏副本（**保留**）
- `out/` — 每步命令/原始输出/退出码（`*.log`）、各趟 NDJSON 原始证据、菜单枚举、截图、存档文件 `save_SAVE4823.SAV` 及其哈希、real_pre/real_post 全量清单
- `tools/` — 复跑脚本（`live_lib.py`、`phase_*.py`、`manifest.py`、`diff_real.py`）
- `CAMPAIGN_LIVE.md`（本文件）、`UNCOVERED.md`、`DISAGREE.md`

## 9 · 建议的 C 线下一步
1. **优先**：定位 `GUI:CampaignMenu` 的徽章生成条件（静态逆向 `0x46CE10` 之后的 UI 构建路径 + 真机 D4 重跑），判定「追加 battle id 是否可能生成第三条 UI 条目」。这决定「追加式 DLC」路线是否可行；若不可行，需要改用「官方 id + 散装覆盖」并重新评估 W22 的包身份语义。
2. **其次**：单独立项查 Q2 的「無法啟動選取地圖!」——用不劫持的入口（一旦 §9.1 找到可达路径）复跑 A1→A2；静态对照官方战役地图的 `NextScenario` 与 `BATTLEMD.INI` 序列关系。
3. 补 CSF 能力（读/写 `ra2md.csf`、散装 vs MIX 覆盖顺序专项）——但按 D1 结果，**它只修显示、不修菜单可达性**，不应冒充 Q1 的修复。
4. 把 `verify` 纳入安装后自检（HANDOFF §10 建议 4）仍在。
