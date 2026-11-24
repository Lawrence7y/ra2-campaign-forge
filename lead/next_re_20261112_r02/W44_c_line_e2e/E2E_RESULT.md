# W44 · C 线整条链真机端到端验证（E2E_RESULT）

> run_id `NEXT_RE_20261112_R02`｜交付目录 `lead/next_re_20261112_r02/W44_c_line_e2e/`
> 执行：W44 子代理｜实测时间 2026-11-13 19:29–19:58 +08:00（≈29 min，预算 ≤100 min）
> 单趟进游戏到判定：K1 76 s（19:43:54→19:45:10）、K2 40 s（19:46:41→19:47:21）、
> 对照臂 K3 35 s（19:51:02→19:51:37），均 ≪10 min
> 写域仅 `W44_c_line_e2e/`；真实 `ra2youli/` 全程只读（仅作 robocopy 源）
> 工具：`W41_csf_install/ra2forge_patched_v12/ra2forge/`（回归 57/57，本卡复核 `out/SUMMARY.txt`）

---

## 0 · 分级口径

| 标签 | 本卡用法 |
|---|---|
| `[本次实测]` | 本卡亲自运行命令、哈希、WMI 启动、Win32 枚举、只读 RPM、截图、读图得到的输出 |
| `[本次读码]` | 直接查看 v12 `cli.py`/`builder.py`/`csf.py`/`mapselmd.py`、W27/W39/W40 驱动脚本与签发文件 |
| `[静态推断]` | 依据既有反汇编对地址/分支语义的推断（本卡不据此宣称实测结论） |
| `[转引]` | 来自 `REVIEW/LEAD_VERDICT_*.md`、`W27/CAMPAIGN_LIVE.md`、`W39/LIVE_RESULT.md` 等已签发结论 |
| `[待运行验证]` | 本卡未覆盖、需另立卡验证的部分 |

---

## 1 · 第 0 步：桌面可见性预检 —— **通过，环境未阻塞** `[本次实测]`

启动后 30 秒内独立完成：

| 项 | 值 |
|---|---|
| `EnumWindows` 顶层 / 可见 | **424 / 19**（≥1） |
| 虚拟屏 | 3584×967 |
| `ImageGrab.grab()` | **OK**，产物 `out/precheck_desktop.png`（364,055 B，sha `966740e6…`） |
| 截图内容 | 已人工读图：可见 Antigravity / DeepSeek 窗口，非黑屏、非异常 |

三趟真机各自在 WMI 启动后 ≤2 s 内另跑 `live_lib.desktop_precheck`（写进各 ndjson 的 `kind=meta` 记录）：

| 趟 | window_station | thread_desktop | input_desktop | EnumWindows 总/可见 | ImageGrab | pass |
|---|---|---|---|---|---|---|
| K1 | WinSta0 | Default | Default | 424 / 19 | OK 2560×1440 | **true** |
| K2 | WinSta0 | Default | Default | 428 / 19 | OK 2560×1440 | **true** |
| K3（对照臂） | WinSta0 | Default | Default | 383 / 20 | OK 2560×1440 | **true** |

⇒ 执行环境为 `WinSta0\Default`（与 W27/W39/W40 成功侧一致），**不是** W35 的 `exebox-…` 隔离桌面 `[转引]`。预检通过，继续实测。

---

## 2 · 六步逐步判定（**逐条判，不用「整体跑通」盖过**）

### S1 · 构建（v12，同时启用 `--mapselmd` + `--csf-out`/`--csf-base`）—— **成立** `[本次实测]`

命令（`out/cmd_build_v12.log`，exit 0）：

```
python -m ra2forge build --design designs/w44_two_missions.json --out out/pkg \
  --mapselmd \
  --csf-out out/csf_work/ra2md.csf \
  --csf-base W40_csf_live/out/official_ra2md.csf
```

复核点（逐条，`out/build.ndjson`）：

| 判据 | 实测 | 结论 |
|---|---|---|
| `--csf-base` 是**完整官方 CSF** | 332,973 B / `1b90bb07…`（= v12 内置 `RA2MD.OFFICIAL.CSF`，= `langmd.mix` 提取版）；v12 `assert_complete_csf` 通过 | ✅ **不是最小 CSF** |
| `validate` | `OK: 2 mission(s)`，exit 0 | ✅ |
| 包内 `ra2md.csf` | **333,078 B** / `d86a7e72…`，魔数 ` FSC`；`csf_patch.json`: `action=appended`, `num_labels=5212`, `complete_baseline_labels=5211` | ✅ 完整克隆官方 5,211 标签 + 追加 1 个 |
| `BATTLEMD98.INI` | 358 B，`Description=RA2F:942506FC`（**CSF 标签，非纯文本**），`15=RA2F1`，`Scenario=ECH01.MAP` | ✅ |
| CSF 标签值 | `W44_C_LINE_CSF_DESC_VISIBLE_20261113`（= design 的 `campaign.description`） | ✅ |
| 包内 `MAPSELMD.INI` | **6,108 B / `11cc1cac…`**，100% CRLF，追加 `[Nod] 8=RA2F_ECH01_2004FB14` / `9=RA2F_ECH02_1E0DEBE8` | ✅ **与 W39 成功侧逐字节相同** `[转引]` |
| 地图 `[Basic]` | ECH01 `NextScenario=ECH02.MAP`, `SkipMapSelect=no`, `EndOfGame=no`; ECH02 `NextScenario=`, `SkipMapSelect=no`, `EndOfGame=yes` | ✅ |
| `--csf-out` 落在游戏目录外 | `W44/out/csf_work/`，guard 判定 `in_game_dir=false`（只检查 ancestors） | ✅ 未走 `--allow-csf-out-in-game` 危险通道 |

`[本次读码]` 复核 `builder.py:148-193`：`desc_override=csf_label` 只改 `BATTLEMD98.INI` 的 `Description`；`csf_label_for` / `stage_names_for` 的 seed **不含 description** `[本次读码]`，所以本卡改 description **不影响** battle_id / MAPSELMD 阶段名 / CSF 标签名。这是 MAPSELMD 能与 W39 逐字节相同的原因。

> 作用域限定：这张包是**追加式**战役包，进图仍须借官方 `[SOV1]` 入口（见 S3），不外推成「菜单可选」。

---

### S2 · 沙箱准备 + 处理旧包 v0.3 + 装新包 + `verify` —— **成立** `[本次实测]`

- `[本次实测]` 从 `ra2youli` **只读复制**（`robocopy /E /COPY:DAT /DCOPY:DAT /R:1 /W:1`，rc=1 → 成功）；新沙箱 `W44_c_line_e2e/sandbox_game/`，PRE 全量清单 `out/sandbox_pre.json` = **647 文件 / 1,989,215,270 B / 277 地图类**，4 个基线哈希全对。复制后确认**无**散装 `MAPSELMD.INI`、无散装 `ra2md.csf`。
- `[本次实测]` 按 `W27/CAMPAIGN_LIVE.md §2` 流程（`out/install.ndjson`）：

| 步骤 | 命令 | exit | 说明 |
|---|---|---|---|
| 旧包 verify | `verify --game <sandbox> --json` | **0** | v0.3 旧清单 `fe3bdf62…` |
| 卸旧包 v0.3 | `uninstall --game <sandbox> --json` | **0** | `status=completed`，9 条 actions，degraded-mode 警告（v0.3 无 seal） |
| 卸后 verify | `verify --game <sandbox> --json` | **0** | `manifest_present=false` |
| 装新包（无 flag） | `install --package <pkg> --game <sandbox>` | **1** | 复现 W27 §2 的 `preflight` definite content conflict（官方还原出来的 ECH01/02.MAP），**零写入** |
| 装新包（`--allow-content-conflict`） | 同上 + flag | **0** | `created BATTLEMD98.INI / MAPSELMD.INI / ra2md.csf`、`backup+replaced ECH01/02.MAP`、`created expandmd98.mix` |
| 装后 verify | `verify --game <sandbox> --json` | **0** | `manifest 1.0 / seal era / structure OK / package_digest OK / seal OK`，记录 6 个包文件 |

- `[本次实测]` 装后沙箱：`MAPSELMD.INI` 6,108 B `11cc1cac…`、`ra2md.csf` 333,078 B `d86a7e72…`、`BATTLEMD98.INI` 358 B `2d364b4c…`、`BATTLEMD.INI` **仍是官方原样 `7e40691a…`**（包只加 `BATTLEMD98.INI`）。

---

### S3 · 真机运行（WMI 启动 → 战役菜单 → 借官方 `[SOV1]` 徽章进 A1）—— **成立** `[本次实测]`

`out/run.ndjson`（K1，pid 36120）：

| 判据 | 实测 |
|---|---|
| 单实例 / 残留 0 | `pre_launch_guard: gamemd_processes=[]`；WMI `Win32_Process.Create` → `38036\|0` |
| step-0 预检 | `pass=true`（见 §1） |
| 主菜单就绪 | 21.05 s，证据控件 `GUI:SinglePlayer`；hwnd rect `[0,0,1707,960]`，title `Yuri's Revenge` |
| 战役菜单 | `BM_CLICK GUI:SinglePlayer` → `GUI:NewCampaign` → `GUI:CampaignMenu`；`battle_cnt=15`（14 官方 + RA2F1） |
| **借 `[SOV1]` 入口** | 沙箱内 D2 变体：`BATTLEMD.INI [SOV1] Scenario=SOV01umd.MAP` → `ECH01.MAP`（sha `369592f0…`，2,730 B）；真实鼠标点苏联徽章 `(210,285)` |
| 进图 | 点徽章 3 s 后 `scen_filename=ECH01.MAP`、`scen_battle_idx=1`；`VK_RETURN`×2 跳影片 |
| A1 局内 | `frame=33` ＞30，`scen_next=ECH02.MAP`，`scen_skip_mapsel=0`(=no)，`ECH01.MAP\|ascii=3`、`ECH02.MAP\|ascii=1`（只读 RPM）；截图 `screen_w44_run_A1_ingame.png` |

> `[转引]` + `[本次实测]` 作用域限定：入口是 **W27 的 D2 诊断变体**（劫持官方苏联徽章），**不是**追加战役 `RA2F1` 自身的菜单条目。W27 Q1 / W32 / `LEAD_VERDICT_campaign_menu_q1.md` 已证 `RT_DIALOG id=148` 只有 2 个徽章 Static，结构上不可能出现第三个条目。本卡 S3 截图（`crop_w44_campaign_menu_content3x.png`）亦只显示 2 徽章 + 7 空槽，与该结论一致。

---

### S4 · 推进（打赢 A1 → `GUI:Continue` → 确认进入 A2 局内）—— **成立** `[本次实测]`

不是「游戏没崩」当「功能正常」，也不是「截图看着像」当唯一证据；按 4 项独立硬指标：

| # | 判据 | 原始证据（`out/run.ndjson`） | 结论 |
|---|---|---|---|
| 1 | **定时器真的推进** | `A2_confirmed`: `frame_t1=53 → frame_t2=131`，`frame_delta=78` / 2.5 s ≈ **31.2 计数/s**；另有 `post_continue` 序列 `0→6→53→131`（`elapsed_s=4.56` 为「点击→采到 frame=53」的耗时）。与 32 ms 定拍（31.25/s）一致 `[转引]` | ✅ |
| 2 | **`scen_filename` 切换** | 点击 `GUI:Continue` 后紧接快照 `scen_filename=ECH02.MAP`（原 `ECH01.MAP`），`scen_stage_idx` 0→8 | ✅ 最硬、无歧义 |
| 3 | **只读 RPM 标记** | `post_continue_A2_memory`: `ECH02.MAP\|ascii=2`、`ECH01.MAP\|ascii=2`、`RA2F1\|ascii` 命中；`battle_cnt=15` | ✅ |
| 4 | **局内控件 + 截图** | `A2_esc_menu_controls.hits = [GUI:AbortMission, GUI:GameControls, GUI:GameOptions, GUI:LoadGame, GUI:ResumeMission, GUI:SaveGame]`（6/6，非主菜单）；`screen_w44_run_A2_ingame.png`（961 KB，已人工读图：白色雪原 + 苏军建造场/核电/战车工厂/锤镰建筑群 + 右下角「未探索之地形」黄字提示；**本帧未见完整侧边栏**，故不据此宣称侧边栏存在） | ✅ |

- 胜利方式：`[本次实测]` A1 由 design 编译的 `survive(8)` 引擎原生触发器判胜（`frame 164→196→210→210` 出现 `GUI:Continue` + `GUI:HeadsTaken/ParTime/StandaloneScore/YourTime`），**无改存档、无写内存、无注入**。
- 点击 `GUI:Continue` → `result=posted` → 无错误框（`error_dialog_GUI_OK` 未出现），`run_outcome = A2_loaded`。
- `[转引]` 关于 `scen_stage_idx=8`：该字段按 `[Scen+0x35A0]` 读取，语义来自既有反汇编而非符号级证明，本卡**不**据此宣称「引擎选中了第 8 阶段」；与 W39 裁决口径一致。

---

### S5 · 存读档（A2 内存档 → 完全退出残留 0 → 重启 → 读档 → 回 A2 局内）—— **成立** `[本次实测]`

K1 存档（`out/run.ndjson`）：

| 判据 | 实测 |
|---|---|
| A2 局内存档 | `VK_ESCAPE` → 局内菜单 `GUI:SaveGame` → 存档对话框（`ListBox` 8 项 + `Edit`）→ 选首槽 + `type_ascii("W44Q3SAVE")` + `WM_SETTEXT` → `GUI:Save` |
| 产物 | `SAVE4823.SAV` **627,453 B** / `ef9e51e9…`，副本 `out/save_SAVE4823.SAV` 同哈希；`before_n=8 → after_n=9`，`added=[SAVE4823.SAV]`、`changed=[]` |
| 完全退出 | `WM_CLOSE → taskkill → taskkill /F`，`close_game.all_gamemd_residual=[]`，`K1 meta_end` 残留 0 |

K2 读档（`out/saveload.ndjson`，pid 7820，**新进程**）：

| 判据 | 实测 |
|---|---|
| 冷启动前 | `pre_launch_guard: []`；step-0 `pass=true`；19.51 s 主菜单就绪 |
| 读档路径 | `GUI:SinglePlayer` → `GUI:LoadSavedGame` → 载入对话框（`ListBox` 8 项、`GUI:Load`）→ `BM_CLICK GUI:Load` |
| 回到 A2 局内 | `K2_load_ingame`: `frame=283`、`scen_filename=ECH02.MAP`、`scen_stage_idx=8`；随后 `frame=396`（继续推进） |
| 只读 RPM | `ECH02.MAP\|ascii=2` |
| 局内控件 | `esc_hits` 6/6（`ResumeMission/SaveGame/AbortMission/GameControls/GameOptions/LoadGame`） |
| 画面 | `screen_w44_load_K2_after_load.png`（957 KB，已人工读图：雪地 A2 + 苏军建造场/核电/战车工厂/锤镰建筑群），非加载屏/错误框 |
| 存档未被改写 | `save_copy_sha256_after` = `ef9e51e9…`，`save_copy_matches=true` |
| 残留 | `close_game` 后 `[]`，`K2 meta_end` 残留 0 |

`[本次实测]` **K2 刻意不重新应用 D2 劫持**：读档路径不经过战役菜单徽章入口，因此 K2 的状态是「仅 v12 包安装、官方 `BATTLEMD.INI` 原样」的**正式管线状态**。这使本卡的 Q3 不再依赖 W27 的 D3 诊断变体（详见 §3 Q-B）。

如实记录的缺陷：`K2_load_selected = null` `[本次实测]` —— 按 `W44Q3SAVE` / `SAVE4823` 名字匹配列表项**未命中**（`LB_GETITEMDATA` 读到的首项名为 `玩qsave` 等），实际依赖**高亮首槽**完成读档。这与 W27 §5 的 `Q3_load_selected=null` 同型 `[转引]`，本卡未实现「按名字精确选中任意存档」。

---

### S6 · 卸载 → 逐字节还原自证 → `verify` exit 0 —— **成立** `[本次实测]`

| 判据 | 实测（`out/uninstall.ndjson` / `out/restore_proof.ndjson`） |
|---|---|
| `uninstall --json` | **exit 0**，`status=completed`，actions 含 `removed expandmd98.mix / ECH02.MAP / ra2md.csf / MAPSELMD.INI / BATTLEMD98.INI`、`restored ECH0*.MAP.ra2forge.bak` |
| `verify` 卸后 | **exit 0**，`manifest_present=false` |
| 无散装 `MAPSELMD.INI` | `present=false` ✅ |
| 无散装 `ra2md.csf` | `present=false` ✅ |
| 官方 `BATTLEMD.INI` 原样 | `7e40691a…`（= pristine = 基线）逐字节相等 ✅ |
| 全树逐字节 | `added=[] removed=[] changed=[]` **`IDENTICAL_TREE=True`**（相对**正确基线**）✅ |
| 15 项字节检查 | 全 pass（含 `RA2MD.INI`/`ddraw.ini`/`gamemd.exe`/`ddraw.dll`/`ECH0*.MAP`/`ECH01.sav`/无 manifest/无 seal）✅ |
| `verify` 最终 | **exit 0** |

**关于「正确基线」的必要说明（不掩盖自证脚本的一处误判）**：

`[本次实测]` 本卡第一版 `w44_phase_uninstall.py` 把 `sandbox_pre.json`（**复制瞬间 = v0.3 旧包已安装态**）当作还原基线，得到 `identical_tree=false` 并把自己的结果判为 `ok=false`。这个判定**用错了基线**：按卡面 §2，卸载 v0.3 旧包本就是流程的一步，卸载后自然不同于「旧包已安装态」。差异 6 项全部是 v0.3 旧包被正常移除/还原（`BATTLEMD98.INI`、`expandmd98.mix`、3 个 `.ra2forge.bak`、`ra2forge_install.json`），加 4 项 changed（官方地图从 `.bak` 还原、`ECH01.sav` 被游戏运行改写）。**卸载操作本身 exit 0、verify exit 0、三条硬判据全过**。

为严谨，本卡另行构造 `[本次实测]` **正确基线** `W44/baseline_clean/`：从 `ra2youli` 再次只读复制 → 只执行**同一条** `uninstall v0.3` → `verify` exit 0 → 全量清单（641 文件 / 1,988,126,654 B / 277 地图类）。把主沙箱与它逐文件对比，清理前仅 `ECH01.sav` 一处漂移，已从基线逐字节还原；最终 `added=[] removed=[] changed=[] identical_tree=true`。脚本 `w44_phase_uninstall.py` 的判据已修正（把 `identical_tree` 标为信息项而非通过条件），`w44_phase_restore_proof.py` 是权威自证。

---

## 3 · 三件单独判定

### Q-A · CSF 文案是否可见（战役菜单简介区）—— **不成立** `[本次实测·截图]`

**判据（按卡面）：把 `BATTLEMD98.INI` 的 `Description=` 写成我方 CSF 标签后，战役菜单的简介区是否渲染出我方文本；必须用截图，控件文本只用于判「控件存在/可见」。**

- 本卡 v12 包：`Description=RA2F:942506FC`，CSF 里该标签值 = `W44_C_LINE_CSF_DESC_VISIBLE_20261113`（`out/pkg/.../csf_patch.json`）。
- **主链臂截图证据**：`screen_w44_run_S2_campaign_menu.png` → 放大裁切 `crop_w44_campaign_menu_content3x.png`（3×，(0,0,860,620)，覆盖完整 800×600 游戏渲染区；`non-black bbox=(0,0,800,600)` 已实测）。**已人工读图**：
  - 盟军徽章下：「點選盟軍圖示以開始盟軍戰役。」
  - 苏联徽章下：「點選蘇聯圖示以開始蘇聯戰役。」
  - 右侧 7 条**空**列表槽 + 「上一頁」+「戰役」标题
  - **没有** `W44_C_LINE_CSF_DESC_VISIBLE_20261113`，**没有**第三个战役条目，**没有** `MISSING:`。
- **辅助证据（不作为显示判据）**：`[本次实测]` `S2_campaign_menu_memory` RPM —— 我方文本 `utf16le=3`、`ascii=0`，标签名 `RA2F:942506FC|ascii=2`，`MISSING:|ascii=0` ⇒ 散装 CSF 确实被引擎加载、标签值确实驻留内存，未出现降级 `MISSING`。控件文本 `["GUI:Back","GUI:Blank","GUI:CampaignMenu","GUI:Difficulty","GUI:Harder","Slider3"]` 仅用于确认该屏控件存在/可见。
- **阳性对照臂 D_CSF_POS（本卡自加，诊断臂，非 v12 主链包）** `[本次实测·截图]`：另造一份**完整官方 CSF 克隆**（5,212 标签、`assert_complete_csf` 通过），把同一我方文本写到 2 个**官方可见/官方简介标签**上：
  - `GUI:SinglePlayer`（原值「單人遊戲」）→ `crop_w44_ctrl_main_menu_content2x.png` **主菜单第一按钮渲染出黄色 `W44_C_LINE_CSF_DE… / …SIBLE_20261113`**（按钮宽度限制折行），其余按钮仍正常中文 ⇒ **散装 CSF 的值确实驱动 UI 渲染**（独立复现 W40 E 臂 `[转引]`）。
  - `DESC:SOV1`（原值「蘇聯戰役 - 毀天滅地大行軍」）→ `crop_w44_ctrl_campaign_menu_content3x.png` **战役菜单截图与主链臂逐字节相同**（两文件 SHA-256 均为 `0bdcfd8c18d636d5218fdd5f225351f2021fb416f08d9c9aff0921e6bf12ee76`，已用 `Get-FileHash` 复核），简介区仍是官方中文、无我方文本。
  - 对照臂结束 `ra2md.csf` **逐字节还原**为 `d86a7e72…`，`verify` exit 0（`out/csf_control.ndjson`）。
- **结论**：`[本次实测·截图]` **不成立**。把 `Description=` 写成我方 CSF 标签后，战役菜单简介区**不渲染**我方文本；且阳性对照证明这不是「CSF 没生效」或「截图没拍到」——CSF 值驱动渲染成立，但追加战役的 Description 在该屏**没有渲染槽位**；连覆盖 `DESC:SOV1` 都不改变徽章下文案（该文案另有来源，本卡未定位，见 `UNKNOWNS.md`）。
- `[转引]` 与 `LEAD_VERDICT_campaign_menu_q1.md`（`RT_DIALOG id=148` 只有 2 徽章 Static）、`LEAD_VERDICT_CSF_live.md §4.2/§6.1`（追加标签在内存被解析但不出现在可见 UI；控件文本 ≠ 渲染文本）一致。
- **限定**：本判定只覆盖「战役菜单简介区」这一屏、800×600 渲染区、本环境；不判定其它 UI 槽位、其它分辨率、其它汉化版本。

### Q-B · 存读档在正式管线下的成立性 —— **成立** `[本次实测]`

- W27 的 Q3 是在 **D3 诊断变体**（`[SOV1] Scenario=ECH02.MAP`，直接进 A2）下成立的 `[转引]`。
- 本卡在 **v12 包 + `--mapselmd` 追加 MAPSELMD 管线**下复验：K1 从 D2 入口（借 `[SOV1]` 徽章）进 A1 → `GUI:Continue` 推进到 A2 → 在 A2 局内存档；**完全退出残留 0**；K2 冷启动、**不重新应用 D2**（正式管线状态）、从主菜单 `LoadSavedGame` 读档 → 回到 A2 局内（`scen_filename=ECH02.MAP`、`frame 283→396`、`ECH02.MAP|ascii=2`、局内 Esc 菜单 6/6、雪地图截图、存档副本哈希不变）。
- ⇒ `[本次实测]` **v12 包 + MAPSELMD 管线下的跨进程存读档成立**，不再依赖 W27 的 D3 诊断变体。
- **限定** `[转引]`：K1 的进图入口仍是借官方苏联徽章的 D2 变体；追加战役 `RA2F1` 自身的菜单可达性仍结构性封死，因此**不得**外推成「追加式战役包可从菜单进入并通关」。读档路径不经过徽章，K2 是正式状态。

### Q-C · 卸载还原完整性 —— **成立** `[本次实测]`

见 S6：三条卡面判据逐字节通过 + 正确基线全树 `IDENTICAL_TREE=True` + 15 项字节检查全过 + `verify` exit 0。

补充 `[本次实测]` 真机纪律与收尾：

| 项 | 结果 |
|---|---|
| 单实例锁 | 开工 19:41:32 取 `owner=w44`（gamemd 残留 0 才取）；收尾 19:57:51 还原 **`owner=lead`**（已复核锁文件内容） |
| 启动方式 | 3 趟均 `Invoke-CimMethod Win32_Process.Create`；`pre_launch_guard` 各 `n=0` |
| 禁止注入 | 仅 `OpenProcess(PROCESS_VM_READ\|PROCESS_QUERY_INFORMATION)` + `ReadProcessMemory`（只读）、`EnumWindows/EnumChildWindows`、`PostMessageW(BM_CLICK)`、`keybd_event`、`mouse_event`、`ImageGrab`；**未**改 exe/dll、未写目标进程内存、未下断点/挂线程/注入 |
| `finally` 自愈 | 每趟 `close_game`（WM_CLOSE → taskkill → taskkill /F，仅本代理 pid）→ 残留 0 → 逐字节还原 `RA2MD.INI`/`ddraw.ini`/`RA2MD.INI.benchbak`/`BATTLEMD.INI` → 移除投放物 → `kind=meta_end`；总控 `w44_finalize.py` 再跑一次最终自愈 + 还锁 |
| 收尾残留 | `Get-Process`/Toolhelp `gamemd` = **0**（`final.ndjson`、`restore_proof.ndjson`、三趟 `meta_end`） |
| 真目录零改动 | `REAL_DIR_PROOF.txt`：PRE/POST 均 **647 / 1,989,215,270 B / 277**，`added=0 removed=0 changed=0`，**`IDENTICAL_TREE=True`**；`RA2MD.INI=c91c6a47…`、`gamemd.exe=73201cc0…`、`ddraw.dll=85e0f7d5…`、`ra2forge_install.json=fe3bdf62…` 四项 PRE=POST 全对 |
| `verify` 全流程 | 9 份 `cmd_verify*.log` 全部 `EXIT: 0` |
| 时间 | 总 ≈29 min ≪100 min；单趟 ≤76 s ≪10 min |

---

## 4 · 证据摘要

| 类别 | 产物 |
|---|---|
| 阶段 ndjson（10 份） | `out/prep.ndjson`(15) / `build.ndjson`(15) / `install.ndjson`(23) / `run.ndjson`(93) / `saveload.ndjson`(36) / `csf_control.ndjson`(35) / `repair.ndjson`(7) / `uninstall.ndjson`(21) / `restore_proof.ndjson`(15) / `final.ndjson`(16) |
| 截图（24 张） | `out/screen_*.png` + `out/crop_*.png`；判定用主图：`crop_w44_campaign_menu_content3x.png`、`crop_w44_ctrl_main_menu_content2x.png`、`crop_w44_ctrl_campaign_menu_content3x.png`、`screen_w44_run_A2_ingame.png`、`screen_w44_load_K2_after_load.png` |
| 包产物 | `out/pkg/W27 Live Campaign/`（11 文件：`BATTLEMD98.INI` / `MAPSELMD.INI` 6,108 B / `ra2md.csf` 333,078 B / `csf_patch.json` / `ECH01.MAP` / `ECH02.MAP` / `expandmd98.mix` / `BUILD_REPORT.txt` / `ra2forge_package.json` / `story.md` / `INSTALL.txt`）+ `out/csf_work/ra2md.csf` |
| `verify` 日志 | `out/cmd_verify*.log` 9 份全 `EXIT: 0`；`out/cmd_*.log` 全命令/exit 记录 |
| 全量清单 | `out/real_pre.json` / `real_post.json` / `real_diff.json` / `sandbox_pre.json` / `sandbox_installed.json` / `sandbox_post.json` / `baseline_clean.json` / `sandbox_diff_final.json` |
| 存档 | `out/save_SAVE4823.SAV`（627,453 B / `ef9e51e9…`）+ `out/save_meta.json` |
| 只读 RPM / 定时器 | 各 ndjson 的 `memory_search`、`read_counters`（`frame`/`scen_filename`/`scen_stage_idx`/`battle_cnt`）、`A2_confirmed.frame_delta=78`、`K2` frame 283→396 |
| 桌面预检 | `out/precheck_desktop.png` + 3 趟 `step0_desktop_precheck` 记录 |
| 真目录自证 | `REAL_DIR_PROOF.txt`、`out/real_pre/post.json` |
| 汇总 | `out/summary.json`（各阶段关键结论机器可读） |
| 可复跑脚本 | `tools/`（见 §7） |

---

## 5 · 失败点、驱动缺陷与下一步建议（**照实写，不放宽判据**）

六步 S1–S6 与三件单独判定 Q-A/Q-B/Q-C **均按其各自判据成立**；但本卡存在以下**驱动/工具缺陷与未覆盖项**，不是游戏行为，也不放宽任何判据：

1. **[本次实测] 工具缺陷 A（已修复并自证）**：K1 的第一版 `w44_common.heal()` 把 `ra2forge_install.json` 也列入还原列表，用 PREP 时保存的 **v0.3 旧清单**覆盖了 v12 安装记录。发现后立即：
   - 从 `install.ndjson` 里逐字节恢复 v12 清单（`ea34bada…`，与安装时记录一致），
   - `verify --json` 复核 **exit 0**、seal 完好（`out/repair.ndjson`），
   - 修 `heal()` 使其**永不触碰安装记录**（安装记录属 install/uninstall 生命周期，不属配置还原）。
   - **影响**：K1 结束时到修复之间（约 50 s）`verify` 会失败；修复后 K2/K3/卸载全部正常。已在报告中留痕，未粉饰。
   - **建议**：后续真机卡的 `finally` 只还原 `RA2MD.INI`/`ddraw.ini` 等游戏配置，**不要**把 `ra2forge_install.json`/`.seal` 放进还原集合。
2. **[本次实测] 工具缺陷 B（已修正判据）**：`w44_phase_uninstall.py` 初版用错还原基线（见 S6），把自己的结果记为 `ok=false`。卸载本身 exit 0 / verify 0 / 三条硬判据全过；已用 `w44_phase_restore_proof.py` 的**正确基线**重做并得 `ok=true`，脚本判据已修正。**建议**：任何「逐字节还原」自证必须先定义「应有状态」，不能拿「流程中途态」当基线。
3. **[本次实测] 工具缺陷 C（已修复，不影响结果）**：`w44_finalize.py` 的 `finally` 防御式还锁检查误写 `C.LOCK`（应为 `L.LOCK`），抛 `AttributeError` 并被记录；主流程 `lock_restore_lead()` 已成功，锁最终 `owner=lead`。已修脚本。
4. **[本次实测] `K2_load_selected=null`**：按存档名精确选中列表项未命中，依赖高亮首槽完成读档（与 W27 §5 同型）。**建议**：后续卡改用 `LB_GETTEXT`/`LB_GETTEXTLEN` 逐项比对，或先清空存档槽，验证「按名字精确选中任意存档」；本卡未验证该能力。
5. **[本次实测] 截图几何**：游戏实际渲染区是 `800×600`（`non-black bbox=(0,0,800,600)`），窗口 rect 为 `1707×960`，右/下为黑边；`crop_w44_campaign_menu_right.png` 因此全黑。已改用 `(0,0,860,620)` 3× 裁切覆盖完整渲染区，判定不受影响。
6. **[转引]/[待运行验证] 结构性未闭合**：追加战役 `RA2F1` 的菜单可达性仍封死（W27 Q1 / W32 / `LEAD_VERDICT_campaign_menu_q1.md`）；A2 之后 `EndOfGame` 终止行为、`SkipMapSelect=yes` 分支收窄、多包共存（whole-file `MAPSELMD.INI` 冲突）、其它分辨率/汉化版本、交互式 MapSelect 均未测。
7. **[待运行验证]** 战役菜单徽章下「點選…圖示以開始…戰役。」文案的**真实来源**未定位：覆盖 `DESC:SOV1` 后该文案不变（截图 SHA 与主链相同），说明它不是由 `DESC:SOV1` 渲染；可能是 exe 内建或其它标签。本卡只判定「不渲染我方文本」，不臆造来源。
8. **[待运行验证]** 本卡 K1 的 A2 判定复用 W39 的 4 项硬指标；`scen_stage_idx=8` 的字段语义仍是 `[静态推断]`/`[转引]`，未做符号级证明。

**下一步建议（按优先级）**：
- ① 若要让「追加式战役包」真正从菜单可达，需静态逆向 `0x46CE10` 之后的 UI 构建路径，判定能否生成第三条徽章；在找到可达路径前，C 线结论必须连写「借 `[SOV1]` 入口」的作用域限定。
- ② 补一张卡：定位战役菜单简介文案的真实 CSF 标签/字符串来源，并验证「追加标签显示在可见 UI」是否有其它槽位（例如选中列表项后的右侧说明区）。
- ③ 补测 `EndOfGame=yes` 的末关终止行为、多关（>2）链、以及跨包升级后的存读档。
- ④ 修 `K2_load_selected`：用 `LB_GETTEXT` 实现按名字精确选中。

---

## 6 · 与已签发事实的一致性（复核，不外推）

| 签发事实 | 本卡复核 | 一致 |
|---|---|---|
| 散装 `MAPSELMD.INI` 登记后 `GUI:Continue` 能推进（W39，`LEAD_VERDICT_Q2_CLOSED.md`） | S4：`A2_loaded`，且 v12 `--mapselmd` 产物与 W39 逐字节相同 `11cc1cac…` | ✅ |
| 散装 `ra2md.csf` 覆盖 `langmd.mix` 且值驱动 UI（W40，`LEAD_VERDICT_CSF_live.md`） | Q-A 对照臂：主菜单第一按钮渲染我方文本；官方 CSF 332,973 B `1b90bb07…` | ✅ |
| 战役菜单结构上不可能出现第三条目（`LEAD_VERDICT_campaign_menu_q1.md`） | S3/Q-A 截图：2 徽章 + 7 空槽，无第三条目 | ✅ |
| 官方 CSF 在 `langmd.mix`、`MAPSELMD.INI` 在 `ra2md.mix`（两容器别混） | 构建用 `W40/out/official_ra2md.csf`（332,973 B，与 v12 内置一致）；`MAPSELMD.OFFICIAL.INI` 5,573 B `074ccccd…` | ✅ |
| W27 Q3 只在 D3 诊断变体下成立 | Q-B 在 v12 包 + MAPSELMD 管线 + 无 D2 的 K2 下复验成立 | ✅ 且推进了一步 |
| v12 回归 57/57 | 本卡复核 `W41_csf_install/out/SUMMARY.txt`：`cases 57 passed 57 failed 0` | ✅ |

---

## 7 · 交付清单

```
W44_c_line_e2e/
├── E2E_RESULT.md            （本文件）
├── UNKNOWNS.md
├── DISAGREE.md
├── REAL_DIR_PROOF.txt
├── designs/w44_two_missions.json
├── tools/
│   ├── _bootstrap_lib.py            由 W39 live_lib.py 生成 w44_lib.py（改路径 + 补 W27 存档函数）
│   ├── w44_lib.py                   合并驱动库（W39 观测 + step0 预检 + W27 存档 UI）
│   ├── w44_common.py                路径 / 命令捕获 / 全量清单 / diff / heal
│   ├── w44_crops.py                 战役菜单 3× 裁切 + CSF 标签检查
│   ├── w44_phase_prep.py            阶段1 真目录PRE/锁/只读复制/pristine
│   ├── w44_phase_build.py           阶段2 v12 构建 + 产物复核
│   ├── w44_phase_install.py         阶段3 卸 v0.3 + 装 v12 + verify
│   ├── w44_phase_run.py             阶段4a K1 真机 A1→A2→存档→退出
│   ├── w44_phase_load.py            阶段4b K2 重启→读档→确认 A2
│   ├── w44_phase_csf_control.py     诊断臂 D_CSF_POS（阳性对照，逐字节还原）
│   ├── w44_fix_record.py            工具缺陷 A 的修复/自证
│   ├── w44_phase_uninstall.py       阶段5a 卸载 + 三条硬判据 + 中间 diff
│   ├── w44_phase_restore_proof.py   阶段5b 正确基线 + 全树逐字节自证
│   ├── w44_finalize.py              阶段6 真目录POST/零改动/还锁
│   └── run_all.ps1                  总控（try/finally 保证 finalize 必跑）
├── baseline_clean/                  （正确基线沙箱，离线副本，1.9 GB）
├── sandbox_game/                    （主沙箱，已还原到干净态）
└── out/                             （82 文件：10 份 ndjson / 24 张截图 / 包产物 /
                                        verify 日志 / real_pre,post / sandbox_* / 存档 / summary.json）
```

复跑：`powershell -File tools/run_all.ps1`（前提：持锁、无 gamemd 残留、`WinSta0\Default`）。

---

## 8 · 一句话总结（**不替代上面的逐条判定**）

`[本次实测]` 在 v12 包（`--mapselmd` + 完整官方 CSF 克隆 `--csf-out/--csf-base`）下，借官方 `[SOV1]` 入口的 C 线六步**逐步按各自判据成立**：构建、安装、运行、A1→A2 推进、A2 跨进程存读档、卸载逐字节还原；三件单独判定为「CSF 简介区**不渲染**（有阳性对照）、正式管线存读档**成立**、卸载还原**完整**」。全部结论均带「借 `[SOV1]` 入口 / 菜单第三条目结构封死」的作用域限定；3 个驱动缺陷与 8 项未覆盖已在 §5 照实列出。
