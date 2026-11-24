# W70 · C 线产品结论加固：三关链重复性 + 卸载后官方战役可用性

> 执行者 **Hy4**（W70，**非 Lead**）｜卡目录 `lead\next_re_20261112_r02\W70_c_repeatability\`
> `STARTED.txt` 于读任何文件之前写入：`2026-11-14T00:12:48+08:00`（ISO + `Hy4` + "lock per trip"）
> 收尾 `2026-11-14T00:42:40+08:00`｜真机趟时段 `00:25:22–00:38:39+08:00`
> **Lead 独立验收，只看落盘产物**：本文所有数值可回对 `out\*.ndjson` / `out\*.json` / `out\screen_*.png` / `out\cmd_*.log`。
> 分级：`[本次实测]` / `[本次读码]` / `[静态推断]` / `[转引]` / `[待运行验证]`。

---

## 0 · 一句话结论（两件，分开判定）

- **T1 · 重复性**：`[本次实测]` **同一构建的三关链在 2 趟（W70 trip2、trip3）中一致通过**。两趟均 `ok=True`、`outcome=FULL_CHAIN_M1_M2_M3`，`Scen+0x125C` = `RA2F_M1.MAP → RA2F_M2.MAP → RA2F_M3.MAP`，M1/M2 `advance=true`，M3 `advance=false` + `EndOfGame=1` + 无第 4 关，全程 0 次 `MSG:UnableMapSelect`。
  `[转引]` W63 第 1 趟（`W63_route_a_e2e\out\TRIP_RESULT.json`，`REVIEW\LEAD_VERIFY_W63.md`）的落盘判据与上两趟**逐项一致**——三趟对照表见 §2。
  ⇒ `N = 2`（本卡实际跑成的趟数）；W63 第 1 趟为 `[转引]`，不计入本卡 N。

- **T2 · 卸载后官方战役可用性**：`[本次实测]` **`官方入口恢复可用`**（三分结论第一档）。**功能级已验**，不是「只验字节还原」：装包 → 卸载 → 逐字节还原 → **重启游戏** → 走官方苏联战役入口 → 进了**官方第一关**。见 §3。

- **真目录零改动自证**：`[本次实测]` **`IDENTICAL_TREE=True`**（`REAL_DIR_PROOF.txt`，647 文件 / 1,989,215,270 B / PRE==POST），全程 `ra2youli` 只读。

- **锁**：`[本次实测]` 每个游戏实例一趟一锁（取 `owner=w70`，收尾 `owner=lead`），最终 `owner=lead`，`gamemd.exe` 残留 0。

---

## 1 · 方法与纪律（`[本次实测]`）

| 项 | 本卡 |
|---|---|
| 复用构建 | `W63_route_a_e2e\work\pkg\W63RouteA\` 逐字节复制到本卡 `work\pkg\W63RouteA\`，**11/11 文件 SHA-256 一致、0 mismatches**（`out\PACKAGE_INVENTORY.json`），**包内容未改动一个字节** |
| 工具 | `W63_route_a_e2e\work\tools\w63_*.py` → 复制到本卡 `work\tools\w70_*.py` 并改输出路径（`_gen.py` 字面替换 + `py_compile` 通过），**未直接 import 他卡脚本**；新增 `w70_base/cycle/official/final.py` |
| 沙箱 | 每趟 `robocopy ra2youli → W70\sandbox_game`（只读源，`/COPY:DAT`），起点 `sandbox_pre_<tag>.json` 647 / 1,989,215,270 B；**每趟独立新沙箱**，收尾逐字节还原 + 删除 |
| 锁 | 每个游戏实例启动前读 `.game_instance.lock`，要求 `owner=lead` 且 `gamemd` 活体 0 → 写 `owner=w70`；**无论成败**在 `finally` 写回 `owner=lead` + 状态。3 次游戏启动 = 3 次独立取放锁，**未跨趟长期持锁** |
| 不写真目录 | 所有 install/uninstall/游戏启动只针对沙箱副本；`REAL_DIR_PROOF.txt` |
| 只关自己启动的进程 | `WM_CLOSE` → `taskkill /PID <own>` → `/F`，pid 记录 6256(T2) / 13952(trip2) / 16488(trip3)，收尾 `residual_own_pid=0`、全局 `gamemd` 残留 0；**未 taskkill 用户进程** |
| 只读采集 | `OpenProcess(PROCESS_VM_READ|PROCESS_QUERY_INFORMATION)` + `ReadProcessMemory` / `EnumWindows` / `PIL.ImageGrab`；无写内存、断点、挂线程、注入、改 exe |
| 桌面预检 | 三次启动 `WinSta0\Default`、417/411/423 窗口、ImageGrab 2560×1440，`pass=True` |
| 配置基线 | 启动前 21 项沙箱可写配置字节副本 + 哈希（`out\pristine\`），收尾逐字节还原并实算自证 |
| git | 只读，未做任何写操作 |

观测点（W59 签发）：`Scen*=*(DWORD*)0xA8B230`；`+0x125C`（图名，**主锚**）/ `+0x35A0`(WORD) / `+0x34AC`(EndOfGame) / `+0x34B0` / `+0x34CC`；帧号 `[0xA8ED84]`。
**判「进了第几关」只用 `+0x125C`**：`+0x35A0` 是「上一次跳转消费的阶段键」（`[转引]` `LEAD_VERIFY_W63.md` §8 / W59 U3），三趟实测均 0→8→9，不作为关序号。

---

## 2 · T1 三趟对照表（`[本次实测]` trip2/trip3；`[转引]` trip1）

**判据（同 W63）**：每趟 `0x125C` = M1→M2→M3；M1/M2 `advance=true`；M3 `advance=false` 且 `EndOfGame=1`；无 `MSG:UnableMapSelect`；每关进关/结算截图。

| 判据 | 第 1 趟 `[转引]` W63 | 第 2 趟 `[本次实测]` W70 `trip2` | 第 3 趟 `[本次实测]` W70 `trip3` | 三趟一致？ |
|---|---|---|---|---|
| 构建 | `W63RouteA`（同一包） | 同一包（逐字节复制，0 mismatches） | 同一包 | ✅ |
| `ok` / `outcome` | `True` / `FULL_CHAIN_M1_M2_M3` | `True` / `FULL_CHAIN_M1_M2_M3` | `True` / `FULL_CHAIN_M1_M2_M3` | ✅ |
| `0x125C` 进关轨迹 | `RA2F_M1.MAP → RA2F_M2.MAP → RA2F_M3.MAP` | 同左 | 同左 | ✅ |
| `0x125C` 终局 | 冻结 M3（47 samples / 71.38 s） | 冻结 M3（47 / 71.36 s） | 冻结 M3（47 / 71.34 s） | ✅ |
| M1 `enter/victory/advance` | ✅ / ✅ / ✅ → M2 | ✅ / ✅ / ✅ → M2 | ✅ / ✅ / ✅ → M2 | ✅ |
| M2 `enter/victory/advance` | ✅ / ✅ / ✅ → M3 | ✅ / ✅ / ✅ → M3 | ✅ / ✅ / ✅ → M3 | ✅ |
| M3 `enter/victory/advance` | ✅ / ✅ / **false（终关）** | ✅ / ✅ / **false** | ✅ / ✅ / **false** | ✅ |
| M3 `+0x34AC` EndOfGame | **1**（进关即置位） | **1** | **1** | ✅ |
| `no_fourth_start` / 第四关候选 | `True` / `[]` | `True` / `[]` | `True` / `[]` | ✅ |
| `+0x35A0` 轨迹（**非关序号**） | 0 → 8 → 9 | 0 → 8 → 9 | 0 → 8 → 9 | ✅ |
| `+0x34AC` 轨迹 | 0 → 0 → 1 | 0 → 0 → 1 | 0 → 0 → 1 | ✅ |
| `MSG:UnableMapSelect` | 0 次 | 0 次 | 0 次 | ✅ |
| `blocked/fatal/error` 事件 | 0 | 0 | 0 | ✅ |
| 每关进关/结算截图 | 有 | 有（`screen_trip2_*`） | 有（`screen_trip3_*`） | ✅ |
| 锁 / 残留 | `w63`→`lead` / 0 | `w70`→`lead` / 0 | `w70`→`lead` / 0 | ✅ |

**逐阶段 `+0x125C` 原始读数（主锚，`[本次实测]` / `[转引]`）**

| 阶段 | 第 1 趟 W63 | 第 2 趟 W70 | 第 3 趟 W70 |
|---|---|---|---|
| enter_M1 | `RA2F_M1.MAP` stage=0 eog=0 frame=75 | `RA2F_M1.MAP` stage=0 eog=0 frame=59 | `RA2F_M1.MAP` stage=0 eog=0 frame=73 |
| victory_M1 | `RA2F_M1.MAP` frame=210（停滞） | `RA2F_M1.MAP` frame=210 | `RA2F_M1.MAP` frame=210 |
| enter_M2 | `RA2F_M2.MAP` stage=8 eog=0 frame=92 | `RA2F_M2.MAP` stage=8 eog=0 frame=95 | `RA2F_M2.MAP` stage=8 eog=0 frame=89 |
| victory_M2 | `RA2F_M2.MAP` frame=210 | `RA2F_M2.MAP` frame=210 | `RA2F_M2.MAP` frame=210 |
| enter_M3 | `RA2F_M3.MAP` stage=9 **eog=1** frame=93 | `RA2F_M3.MAP` stage=9 **eog=1** frame=130 | `RA2F_M3.MAP` stage=9 **eog=1** frame=93 |
| victory_M3 | `RA2F_M3.MAP` eog=1 frame=210 | `RA2F_M3.MAP` eog=1 frame=210 | `RA2F_M3.MAP` eog=1 frame=210 |
| final（71 s / 47 采样） | `fn={RA2F_M3.MAP}` `eog={1}` `no_fourth_start=True` | 同左 | 同左 |

### 2.1 差异如实登记（**均为时序，非功能分歧**）

| # | 差异 | 分析 |
|---|---|---|
| D-1 | **终局截图内容不同**：`screen_trip2_final_after_M3_continue.png`（328,505 B, `f4b4a6f3…`）目视是**主選單**（`GUI:MainMenu`/`單人遊戲`/`版本 1.001`）；`screen_trip3_final_after_M3_continue.png`（151,811 B, `48772a52…`）与 W63 的 `screen_final_after_M3_continue.png`（151,169 B, `4309ccc7…`）目视是 **CREDITSMD.TXT 滚动职员表** | `[本次实测]` **时序**：`observe_final` 固定 71 s 窗口、1.5 s 采样；trip2 的窗口末尾恰好落在「职员表播完→回主菜单」之后（该末拍 `frame=0`、可见控件为主菜单），trip3/W63 落在职员表播放中。**三趟 71 s 轨迹逐项相同**（47 采样、`fn` 恒 `RA2F_M3.MAP`、`eog` 恒 1、无第 4 关），EOG 判定依据轨迹而非单张截图 ⇒ **不构成结论分歧**。见 `out\trip2.ndjson` / `trip3.ndjson` 的 `final_endofgame_observation` |
| D-2 | 进关瞬时 `frame` 抖动：M1 75/59/73、M2 92/95/89、M3 93/130/93 | `[本次实测]` **时序**：1.5 s 轮询命中局内的时刻不同；`frame>30` 判据三趟均满足，胜利帧恒 210，非状态差异 |
| D-3 | 结算屏哈希跨趟不完全相同（如 `screen_trip2_victory_M1.png` `99d3135c…` vs `screen_trip3_victory_M1.png` `c4ea0b25…`） | `[本次实测]` 静态结算模板 + 采样时刻/鼠标位置差异；W63 已如实登记 M2/M3 结算屏逐字节相同属静态模板。**两次胜利各自独立由 `level_victory` 事件的 `0x125C` + `GUI:Continue` 控件枚举支撑**，不靠截图哈希 |
| D-4 | `+0x35A0` 三趟都是 0/8/9 | `[转引]` 与 `LEAD_VERIFY_W63.md` §8「上一跳消费的阶段键」一致；本卡**未**把它当关序号（判关只用 `+0x125C`） |

**结论（严格按口径）**：`[本次实测]` **同一构建的三关链在 2 趟中一致通过**；`[转引]` W63 第 1 趟落盘判据与这两趟逐项一致（三趟对照表无一项判据分歧）。
❌ 不写「三方战役包通用可通关」；❌ 不写「B 线等价性任何结论」；❌ 不写「官方战役不受影响」（在**装包状态下** `[SOV1]` 被占用，见 §3 边界）。

---

## 3 · T2 卸载后官方战役可用性（**功能级，不只字节**）

### 3.1 步骤与实测（`[本次实测]`）

| 步 | 结果 | 落盘证据 |
|---|---|---|
| 1. 装包（inplace） | fresh sandbox → v15 `install --package W63RouteA --feature-set` **exit 0**；`verify` **exit 0**；`BATTLEMD.INI` 2,732 B、清单 `original_sha256=7e40691a3480b1e5ffe6d1cdfccb83f67da4447157607ec3ecb5d2278acf0791` | `out\cmd_t2_install.log`、`cmd_t2_verify_after_install.log`、`INPLACE_INSTALL_t2.json` |
| 2. 卸载 + 逐字节还原（与 W63 同口径） | `uninstall --game sandbox --json` **exit 0**；`BATTLEMD.INI` 2,733 B，SHA == 清单 `original_sha256` == 官方样板 == `pristine` == 真目录 PRE/POST（**7 项布尔全 True**）；`Scenario=RA2F_M1.MAP` 消失、`SOV01umd.MAP` 回归；21/21 可写配置逐字节还原 | `out\cmd_t2_uninstall_final.log`、`RESTORE_t2.json`、`t2_restore.ndjson` |
| 3. **重启游戏**（新进程，还原态） | WMI 自启 `gamemd.exe` pid **6256**；桌面预检 `WinSta0\Default` / 417 窗口 / ImageGrab 2560×1440 `pass=True` | `out\t2_official.ndjson` |
| 4. 走**官方苏联战役入口** | 主菜单 `GUI:SinglePlayer` → `GUI:NewCampaign` → 战役菜单（`GUI:CampaignMenu`/`GUI:Difficulty`/`Slider3`）→ 点苏联徽章 (210,285) | `screen_t2_S0_main_menu.png`、`screen_t2_S2_campaign_menu.png`、`screen_t2_after_SOVIET_badge.png` |
| 5. 进**官方第一关** | `Scen+0x125C = SOV01UMD.MAP`（官方 `[SOV1] Scenario=SOV01umd.MAP`，引擎大写化，**不是 `RA2F_M1.MAP` / M2 / M3**）；`frame=32`（>30，真进局内）；`scen_next=GDI2A.map`（官方关的 NextScenario，独立旁证）；`scen_stage_idx=0`、`EndOfGame=0`；**0 次 `MSG:UnableMapSelect`** | `out\T2_OFFICIAL.json`、`t2_official.ndjson`、`screen_t2_enter_official_mission.png` |
| 6. 收尾 | 只关自启 pid 6256，`residual=0`；`SOV01UMD.sav`（游戏覆写的 PRE 既有存档）从**只读真目录**逐字节还原并实算 SHA 自证；`sandbox_identical_tree=True`；沙箱删除；锁回 `lead` | `out\CLEANUP_t2.json`、`t2_cleanup.ndjson` |

**截图目视（`[本次实测]`）**：`screen_t2_enter_official_mission.png` 是**大幅官方海岸地图**（悬崖、建筑群、紫色尤里雕像、舰船、海面），与我方 40×40 小图（`screen_trip2_enter_RA2F_M1.png`：一小块草地 + 苏军建造厂 + 电厂 + 步兵 + 黑雾）**明显不同** ⇒ 确实进了官方第一关，而非我方注入图。

### 3.2 三分结论

> **`[本次实测]` `官方入口恢复可用`。**
> 不是「恢复但异常」，不是「不可用」，**也不是「功能级未验」**——字节还原与功能级进入官方第一关**都跑成了**。

**边界（防止外溢，必须连带引用）**
- 只验了 **官方苏联战役第一关的进入**（`[SOV1]` → `SOV01UMD.MAP`）；**未**通关官方全战役、**未**验盟军战役、**未**验官方后续关卡链、`+0x125C` 之外的官方内部状态。
- 只验了 **1 个包 / 1 台机 / 1 个镜像 / 1 次 install→uninstall 循环**；重复多轮安装卸载、其它分辨率/语言版本未测（`UNKNOWNS.md`）。
- 「卸载后可进官方第一关」**不等于**「装包状态下官方战役不受影响」：在装包状态下 `[SOV1]` 被就地改写为 `RA2F_M1.MAP`，官方苏联入口是被替换的（W63 `LEAD_VERIFY_W63.md` §6 已明确），本卡不改写该结论。
- 「能卸载」不等于「卸载后游戏正常」——本卡正是补上了此前**只验字节还原**所缺的功能级实测。

---

## 4 · 截图清单（`out\`，SHA-256 前 16 位可回对）

**T2（卸载后官方入口）**
| 文件 | 字节 | SHA-256[:16] | 内容 |
|---|---|---|---|
| `screen_t2_S0_main_menu.png` | 244,434 | `b2a1e7dd40c82493` | 主菜单 |
| `screen_t2_S2_campaign_menu.png` | 246,783 | `76cb6c6b1e577aa2` | 战役/难度菜单 |
| `screen_t2_after_SOVIET_badge.png` | 1,180,997 | `7c9d93f980c76589` | 点苏联徽章后过渡帧 |
| `screen_t2_enter_official_mission.png` | 2,332,230 | `406e1821ac5a12f0` | **官方第一关局内**（大幅海岸图） |

**T1 每关进关/结算（trip2 / trip3 各 11 张，共 22 张）**：`screen_trip{2,3}_S0_main_menu.png`、`_S2_campaign_menu.png`、`_after_SOVIET_badge.png`、`_enter_RA2F_M1/M2/M3.png`、`_victory_M1/M2/M3.png`、`_final_after_M3_continue.png`。示例：
| 文件 | 字节 | SHA-256[:16] |
|---|---|---|
| `screen_trip2_enter_RA2F_M1.png` | 1,424,200 | `682ecf2730280878` |
| `screen_trip2_enter_RA2F_M2.png` | 1,165,817 | `f6994925cf94a55b` |
| `screen_trip2_enter_RA2F_M3.png` | 1,095,394 | `f3edbad7d85563f0` |
| `screen_trip3_enter_RA2F_M1.png` | 1,424,016 | `c34cc27a9f4fe8c6` |
| `screen_trip3_enter_RA2F_M3.png` | 1,165,692 | `67a48f213772e611` |
| `screen_trip3_final_after_M3_continue.png` | 151,811 | `48772a52b9a5e857` | CREDITSMD.TXT 职员表 |

> `[口径纪律]` trip2 的 `_final_after_M3_continue.png` 是主菜单（时序，见 §2.1 D-1）；EOG 判定依据 71 s / 47 采样轨迹，不依据单张终局截图。

---

## 5 · `out\` 产物索引

- 逐趟 ndjson：`base.ndjson`、`t2_prep/t2_restore/t2_official/t2_cleanup.ndjson`、`trip2_prep/trip2/trip2_restore/trip2_cleanup.ndjson`、`trip3_prep/trip3/trip3_restore/trip3_cleanup.ndjson`、`final.ndjson`（共 14 个，198/198/150 行等）
- 逐趟判据 JSON：`TRIP_trip2.json`、`TRIP_trip3.json`（`ok/outcome/levels/trajectory`）；`T2_OFFICIAL.json`（三分结论）
- 还原自证：`RESTORE_t2.json`、`RESTORE_trip2.json`、`RESTORE_trip3.json`、`CLEANUP_t2.json`、`CLEANUP_trip2.json`、`CLEANUP_trip3.json`（均 `battlemd_restored=true` / `sandbox_identical_tree=true`）
- 安装/verify/卸载日志：`cmd_<tag>_install.log`、`cmd_<tag>_verify_after_install.log`、`cmd_<tag>_uninstall_final.log`、`cmd_<tag>_verify_pre.log`、`cmd_<tag>_uninstall_v03.log`、`cmd_<tag>_verify_after_v03.log`、`cmd_<tag>_robocopy.log`（3 组 × 7）
- 全树清单：`real_pre.json` / `real_post.json`、`sandbox_pre_<tag>.json` / `sandbox_post_<tag>.json`、`sandbox_precleanup_<tag>.json`
- 其它：`OFFICIAL_SOV1.json`、`PACKAGE_INVENTORY.json`、`INPLACE_INSTALL_<tag>.json`、`SUMMARY.json`、`FINAL.json`
- 工具：`work\tools\w70_*.py`（生成脚本 `_gen.py`、预检 `_preflight.py`）

---

## 6 · 收尾

| 项 | 实测 |
|---|---|
| `.game_instance.lock` | `owner=lead`（3 次取放锁后最终态；最后一次 `00:38:39` 归还） |
| `gamemd.exe` 残留 | **0**（自启 6256 / 13952 / 16488 均已关，`residual_own_pid=0`） |
| 沙箱 | 3 个 cycle 全部 `sandbox_identical_tree=True` 后删除，`sandbox_game\` 不存在 |
| 真目录 | **`IDENTICAL_TREE=True`**（`REAL_DIR_PROOF.txt`，PRE/POST 647 / 1,989,215,270 B，5 个锚哈希 PRE==POST，`mtime_diff_count=0`） |
| git | 只读，无写操作 |
| 只写本卡目录 | 是（含 `sandbox_game\` 在本卡内，收尾已删） |

**未签发**：本卡是执行者，签发权在 Lead。本文为 `[本次实测]` + `[转引]` 事实记录，不构成 `[签发]`。
