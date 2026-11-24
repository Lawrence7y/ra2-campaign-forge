# W63 · C 线产品路线 (a) 真机 E2E 结果

> 执行者 **Hy4**（W63，非 Lead）｜卡目录 `lead\next_re_20261112_r02\W63_route_a_e2e\`
> 开始 `2026-11-13T15:25:37Z`（`STARTED.txt` 在读任何文件之前写入）｜真机趟 `2026-11-13T23:37:11+08:00 ~ 23:39:42+08:00`｜收尾 `23:41:43+08:00`
> 裁决前提：`REVIEW\LEAD_RULING_C_line_route_a_first.md` —— 先验 **(a) 就地改写官方 `BATTLEMD.INI` 的 `[SOV1]`**；(c) 改 exe 本轮不做。
> **Lead 只看落盘原始产物**：本文所有数值均可回对 `out\*.ndjson` / `out\*.json` / `out\screen_*.png` / `out\cmd_*.log`。

---

## 0 · 一句话结论

`[本次实测]` **路线 (a) 真机走通了完整三关链**：借被 `[SOV1]` 改写的苏联徽章进 M1 → 结算 `GUI:Continue` → M2 → 结算 → M3 → 结算；M3 `[Basic] EndOfGame=yes` 使 `Scen+0x34AC=1`，点最后一次 `Continue` 后**不再 `Start_Scenario` 到第 4 关**（71 秒 / 47 次采样 `0x125C` 冻结在 `RA2F_M3.MAP`，画面进入片尾职员表）。

**这不是「只验到进 M1」** —— 三关各自「进关 / 通关 / 推进」都有独立截图 + 逐帧内存读数，故按 `LEAD_RULING` §3 的口径可以写「多关链贯通」。

结论强度：`[本次实测]`（真机、只读 RPM、落盘原始产物）。不构成 `[签发]`：本卡是执行者，签发权在 Lead。

---

## 1 · 逐关判定表（`[本次实测]`）

| 关 | 期望 `0x125C` | 进关 | 通关（胜利） | 推进到下一关 | 关键截图 | 判据 |
|---|---|---|---|---|---|---|
| **M1** | `RA2F_M1.MAP` | ✅ | ✅ | ✅ → M2 | `screen_enter_RA2F_M1.png`、`screen_victory_M1.png` | `0x125C=RA2F_M1.MAP`、`frame=75` 进局内；`GUI:Continue` 出现、`frame` 210→210 停滞（结算屏）；点 `Continue` 后 `0x125C=RA2F_M2.MAP`、`frame` 15→92 继续推进 |
| **M2** | `RA2F_M2.MAP` | ✅ | ✅ | ✅ → M3 | `screen_enter_RA2F_M2.png`、`screen_victory_M2.png` | `0x125C=RA2F_M2.MAP`、`+0x35A0=8`；`GUI:Continue`、`frame` 210 停滞；点 `Continue` 后 `0x125C=RA2F_M3.MAP`、`frame` 15→93 推进 |
| **M3** | `RA2F_M3.MAP` | ✅ | ✅ | **终止（无第 4 关）** | `screen_enter_RA2F_M3.png`、`screen_victory_M3.png`、`screen_final_after_M3_continue.png` | `0x125C=RA2F_M3.MAP`、`+0x35A0=9`、**`+0x34AC=1`（进关即生效）**；`GUI:Continue`；点 `Continue` 后 71.38 s / 47 采样 `0x125C` 恒为 `RA2F_M3.MAP`、`frame` 恒为 210、`+0x34AC` 恒为 1 → `no_fourth_start=True`，画面走片尾职员表 |

**逐项判定（最终回复口径）**

| 关 | 进关 | 通关 | 推进 |
|---|---|---|---|
| M1 | 成立 | 成立 | 成立 → M2 |
| M2 | 成立 | 成立 | 成立 → M3 |
| M3 | 成立 | 成立 | **不适用（终关）**：`EndOfGame=yes` 生效，不再推进，无第 4 关 |

`trip_result` 原始记录：`out\TRIP_RESULT.json` → `ok=true`, `outcome=FULL_CHAIN_M1_M2_M3`；`out\run.ndjson` 共 198 行，`blocked/fatal/error events = 0`，全程**未出现 `MSG:UnableMapSelect`**。

---

## 2 · `Scen+0x125C` 轨迹（最硬指标）

```
S0 主菜单        ""              stage=0  eog=0  frame=0
战役菜单         ""              stage=0  eog=0  frame=0   (GUI:CampaignMenu)
点苏联徽章后     RA2F_M1.MAP     stage=0  eog=0  frame=0→28→75   [进 M1]
M1 结算          RA2F_M1.MAP     stage=0  eog=0  frame=210 (停滞) [通关 M1]
Continue        RA2F_M2.MAP     stage=0→8 eog=0  frame=0→14→92   [推进 M1→M2]
M2 结算          RA2F_M2.MAP     stage=8  eog=0  frame=210 (停滞) [通关 M2]
Continue        RA2F_M3.MAP     stage=0→9 eog=1  frame=0→15→93   [推进 M2→M3]
M3 结算          RA2F_M3.MAP     stage=9  eog=1  frame=210 (停滞) [通关 M3]
Continue        RA2F_M3.MAP     stage=9  eog=1  frame=210        [EOG 终止]
  ... ×47 采样 / 71.38 s，全部恒为 RA2F_M3.MAP / stage=9 / eog=1 / frame=210
```

`[本次实测]` 轨迹：**`RA2F_M1.MAP` → `RA2F_M2.MAP` → `RA2F_M3.MAP` →（冻结）**。三关文件名与 `Start_Scenario` 实参完全对应，无 `ECH0x.MAP`、无官方 `SOV01umd.MAP`、无第 4 个文件名。

内存读数方法（W59 / `LEAD_VERIFY_W59.md`）：`Scen* = *(DWORD*)0x00A8B230`；`+0x125C` `char[0x104]`（本卡读 260 B 后按 C 串截断）；`+0x35A0` WORD；`+0x34AC` BYTE；`+0x34AE` BYTE；`+0x34B0` BYTE；`+0x34CC` DWORD；`frame = *(DWORD*)0x00A8ED84`。全部只读 `OpenProcess(PROCESS_VM_READ|PROCESS_QUERY_INFORMATION)` + `ReadProcessMemory`，**未写内存 / 未下断点 / 未挂线程 / 未注入 / 未改 exe**。

### 2.1 `+0x35A0`（stage idx）

`[本次实测]` 进关即时读数：**0 → 8 → 9**，单调递增，满足 `LEAD_RULING` §3「`Scen+0x35A0` 递增」。
`[转引]` / `[静态推断]`：M1 是借官方 `[SOV1]` 徽章经 `Start_Scenario` **直接进入**（未走 MapSelect 阶段表），故初值 0；M2/M3 的 8/9 是 `0x5AE0B8 mov [ebx+0x35a0],ax` 在 `GUI:Continue` 状态机里写入的索引。`scen_stage_idx=8` 的**值语义**仍按 W59 U3 / Lead 早前降级为 `[转引]`，本卡不解释「为什么是 8 而不是 7」，只报告实测递增。
`[本次实测]` 一个有价值的细节：M2/M3 切换瞬间出现 `0x125C` 已变为新文件名但 `+0x35A0` 仍为 0 的中间态（如 `23:37:58 RA2F_M2.MAP stage=0 frame=0`），随后才写 8/9 —— 与 W59 静态链「`0x686700` 先写 `+0x125C`、`0x5CF830`+`mov [ebx+0x35a0],ax` 后写 stage idx」的先后次序一致。

### 2.2 `+0x34AC`（EndOfGame）

`[本次实测]` **0（M1）→ 0（M2）→ 1（M3）**，且 M3 一进关就是 1（由地图 `[Basic] EndOfGame=yes` 在加载时写入，对应 `0x68A11F mov [esi+0x34ac],al`）。
`[本次实测]` 最后一次 `GUI:Continue` 后 `+0x34AC` 恒为 1、`0x125C` 恒为 `RA2F_M3.MAP`、`frame` 恒为 210，71.38 秒不出现第 4 张图；画面是**片尾职员表**（`screen_final_after_M3_continue.png`，SHA `4309ccc7…`）。
⇒ 与 W59 签发「`EndOfGame` 是终止闸而非推进开关（`0x6859C7 je` 只在 `==0` 时进推进分支，`!=0` 直接 ret 到不了 `Start_Scenario`）」**真机一致**。

---

## 3 · 截图清单（`out\`，SHA-256 可回对）

| 文件 | 字节 | SHA-256 | 内容（`[本次实测]` 目视） |
|---|---|---|---|
| `screen_S0_main_menu.png` | 250,850 | `982cde29626081935476d9d849aaaa0727b4e711a906799ddc8241ff77e65659` | 主菜单 `GUI:SinglePlayer` |
| `screen_S2_campaign_menu.png` | 235,226 | `c8901bd59a6cdc3a968fef293f9112b89c27d34bb61cc0bd236db3ea593c75a2` | 战役菜单 `GUI:CampaignMenu`（两徽章屏） |
| `screen_after_SOVIET_badge.png` | 4,845 | `e2f372755d4f30018a5d669a72ab1377c0938d29e46b155ff75cf8bfb11d4c38` | 点徽章后的过渡帧（近黑，如实登记，不作进图证据） |
| `screen_enter_RA2F_M1.png` | 1,422,147 | `ab720e95c1480d3489c729798a1640f0693dc6e8ba20bf6a02a19d982cf3d8b8` | **M1 局内**：TEMPERATE 草地、苏军建造厂 + 电厂 + 2 坦克 + 步兵（我方设计） |
| `screen_enter_RA2F_M2.png` | 1,158,398 | `e76f01ccaf5d27b46dc3d03390adb35706e3b828a8dc8546d739d7770172f593` | **M2 局内** |
| `screen_enter_RA2F_M3.png` | 1,158,260 | `75cbfe85f10c577f359eef65cb2a7f66cb2da9d4620b74ad73551c15aed0048d` | **M3 局内**（1 坦克 + 1 步兵，与 M3 设计一致，与 M1 图不同） |
| `screen_victory_M1.png` | 247,585 | `c4ea0b252b76e759d368879ce93e868ec933408ac902c2a2fc403d8614e4964b` | **M1 结算屏**：「任務積分」「繼續」按钮、用时 `00:00:07` |
| `screen_victory_M2.png` | 246,905 | `99d3135c756d28cc81ad2af012dc60706f55b274325301629c23ecc72e4ad6ef` | **M2 结算屏** |
| `screen_victory_M3.png` | 246,905 | `99d3135c756d28cc81ad2af012dc60706f55b274325301629c23ecc72e4ad6ef` | **M3 结算屏**（与 M2 结算屏逐字节相同 —— 静态模板，如实登记，不夸大为不同画面） |
| `screen_final_after_M3_continue.png` | 151,169 | `4309ccc7e25fcac98b357af2e99c1738ccec651aca47b965f2e59561f2a58d4e` | **M3 终局片尾职员表**（`- Production Assistants -` 等），证明 EOG 终止而非进第 4 关 |

`[口径纪律]` 结算屏 M2/M3 哈希相同是静态结算模板所致，**不**当作「两次不同胜利」的独立证据；两次胜利各自另由 `level_victory` 事件的 `w59`（`0x125C` 分别为 `RA2F_M2.MAP` / `RA2F_M3.MAP`、`frame` 停滞）+ `GUI:Continue` 控件枚举独立支撑。

---

## 4 · 包与安装（`[本次实测]`，离线阶段不占锁）

| 项 | 实测 |
|---|---|
| 工具链 | `W60_battlemd_inplace\ra2forge_patched_v15\`（v15，`battlemd:inplace`，96/96 回归绿 `[转引 W60]`）；本卡未改其任何字节 |
| 构建 | `python -m ra2forge build --design work\w63_design.json --out work\pkg --feature-set work\w63_feature_set.json` → **exit 0** |
| `BATTLEMD.INI` | 2,732 B，145 CRLF，0 bare LF；`[SOV1] Scenario=RA2F_M1.MAP`（官方 `SOV01umd.MAP` 计 0 次）；基于官方 2,733 B 样板 `7e40691a…` 逐行 diff **1 行** |
| 三张地图 `[Basic]` | M1 `EndOfGame=no` / `NextScenario=RA2F_M2.MAP`；M2 `EndOfGame=no` / `NextScenario=RA2F_M3.MAP`；M3 `EndOfGame=yes` / `NextScenario=`（空）；三者 `SkipMapSelect=no`、`size=[40,40]`、TEMPERATE、`Russians` 有 `NACNST` 建造厂 + `NAPOWR` + `MTNK` + 步兵 |
| 胜利条件 | ra2forge 原生编译：`survive(8)` → `ElapsedTime(8)` 事件 + `WinnerIs(Russians)` 动作（`builder.py:910-924` `[本次读码]`）；真机结算屏用时 `00:00:07` |
| `MAPSELMD.INI` | 官方全文（5,573 B / `074ccccd…`）为基座 + **追加 3 阶段**；`[Nod]` 数字键 **1..10 连续**（≤100，两处 `cmp reg,0x64`）；阶段段 `Scenario=RA2F_M1/M2/M3.MAP`；**主用变体 A**：阶段数字子项 `1=<下一阶段名>`（从 1 连续）；M3 终关无数字子项 |
| 变体对照 | `out\MAPSELMD.INI.variant_from1`（主用，SHA `8064b783…`）/ `out\MAPSELMD.INI.variant_from2`（v15 原生 `2=`，W39/W44 已证变体，未运行）；单变量仅「追加阶段子项键 1= vs 2=」，其余字节一致 → `out\MAPSELMD_VARIANTS.json` |
| 官方 `[Battles]` 序号 | **未改**；`scen_stage_idx` **未手设**；**未 patch exe**（`gamemd.exe` PRE=POST `73201cc0…`） |

沙箱与安装（`out\offline.ndjson` / `out\cmd_*.log`）：

| 步 | 退出码 / 结果 |
|---|---|
| `real_pre` 全树清单 | 647 文件 / 1,989,215,270 B / 277 地图类，四项锚哈希与 W44 签发基线一致 |
| `robocopy ra2youli → sandbox_game`（只读源） | rc=1（robocopy 成功码） |
| `sandbox_pre` 全树清单 | 647 / 1,989,215,270 B（与真目录一致） |
| `verify_pre` | **exit 0** |
| `uninstall` 预存 v0.3 记录 | **exit 0** |
| 孤儿 `BATTLEMD.INI.ra2forge.bak`（241 B，无清单认领） | **仅从沙箱副本移除**（已存 `out\pristine\` 字节副本，收尾逐字节还原）；v15 `inplace_preflight` 否则会 exit 34 |
| inplace 目标预检 | 沙箱 `BATTLEMD.INI` SHA == 官方 `7e40691a…` |
| `install --feature-set` | **exit 0**（无需 `--allow-content-conflict`） |
| `verify --game sandbox --json` | **exit 0** |
| `.bak` / 清单 | `BATTLEMD.INI.ra2forge.bak` 在位且 == 官方 2,733 B；清单 `original_sha256 == 7e40691a…`、 `original_size_bytes=2733`、`post_install_sha256` == 磁盘、嵌入 `inplace_rewrite` 报告 |
| 安装的 MAPSELMD | `MAPSELMD.INI` == 变体 A（from1）逐字节 |

---

## 5 · 真机采集纪律（`[本次实测]`）

| 红线 | 本卡 |
|---|---|
| 取锁/放锁 | 趟前读 `.game_instance.lock` = `owner=lead` 且 `gamemd` 活体 0 → 写 `owner=w63`（`23:37:11.795`）；**趟结束无论成败**在 `finally` 写回 `owner=lead`（`23:39:42.496`）并注明 `ok=True / FULL_CHAIN_M1_M2_M3 / residual=0`。**未长期占锁**，收尾复核仍 `owner=lead` |
| 不写 `ra2youli` | 只跑沙箱副本；真目录 PRE/POST 全树 `IDENTICAL_TREE=True`（见 `REAL_DIR_PROOF.txt`） |
| 不 `taskkill` 用户进程 | `close_game` 先 `WM_CLOSE(hwnd)`；未关闭时才 `taskkill /PID 34668` / `/F /PID 34668`，**34668 是本卡 WMI 自行启动的 pid**，非用户进程；`residual_own_pid=0` |
| 只读采集 | `OpenProcess(PROCESS_VM_READ|PROCESS_QUERY_INFORMATION)` + `ReadProcessMemory`、`EnumWindows`/`EnumChildWindows`、`PIL.ImageGrab`；**无写内存 / 断点 / 挂线程 / 注入 / 改 exe** |
| 桌面预检 | WMI 启动后 1.1 s 内 `step0_desktop_precheck`：`WinSta0\Default`、392 窗口 / 20 可见、ImageGrab OK 2560×1440、`pass=True`（与 W44 成功侧一致） |
| 只写本卡目录 / git 只读 | 所有产物在 `W63_route_a_e2e\`；未 commit、未改他卡交付物 |

采集器：`work\tools\w63_lib.py` 是 `W44_c_line_e2e\tools\w44_lib.py` 的**本卡副本**（路径常量重指到 W63；新增 `Scen+0x34AC`/`+0x34AE` 读取、`+0x125C` 读 260 B），**未直接 import 他卡脚本**（其输出路径硬编码）。运行器结构另对照 `W55b_equivalence_rerun\tools\w55b_dual_track.py`（同族 ctypes/RPM/回落流程）。

---

## 6 · 收尾与还原（`[本次实测]`）

`out\FINALIZE.json` / `out\finalize.ndjson` / `out\cmd_uninstall_final.log`：

- `uninstall --game sandbox --json` → **exit 0**。
- `BATTLEMD.INI` **逐字节还原**：2,733 B，SHA `7e40691a3480b1e5ffe6d1cdfccb83f67da4447157607ec3ecb5d2278acf0791` == 清单 `original_sha256` == 官方样板 == `out\pristine\BATTLEMD.INI` == 真目录 PRE/POST；`Scenario=RA2F_M1.MAP` 消失、`SOV01umd.MAP` 回归。
- 21 项沙箱可写配置基线收尾处置：**20 项**从 `out\pristine\*` 逐字节还原（`byte_identical=True`，含 241 B 孤儿 `.bak` SHA `9f804531…`）；**1 项** `ra2forge_install.json.seal` 在基线中本就不存在 → 删除现存（`removed_absent_baseline`）；`all_ok=True`（21/21）。
- 游戏自生成的 3 个 `.sav`（`RA2F_M1/M2/M3.sav`，本身也是逐关进局的旁证）清除后，沙箱 `sandbox_post` vs `sandbox_pre` → **`identical_tree=True`**（added/removed/changed 全 0）。
- 还原态 `verify --game sandbox --json` → **exit 0**（回到 v0.3 原始记录，degraded 模式）。
- 沙箱目录 `sandbox_game\` 已删除（`cleaned=True`）。
- `.game_instance.lock` = `owner=lead`；`gamemd` 残留 **0**。

---

## 7 · 分级标注速查

- `[本次实测]`：三关逐关进关/通关/推进/终止的全部读数与截图；`0x125C`/`+0x35A0`/`+0x34AC` 轨迹；`identical_tree` 还原自证；锁与残留；桌面预检；安装/verify 退出码。
- `[本次读码]`：v15 `builder.py` 的 `survive→ElapsedTime/WinnerIs`、`EndOfGame=yes` 末关约定、`maplib.py` `SkipMapSelect=no`；`mapselmd.py` 追加阶段与 `CHILD_COLOUR_INDEX=2`；`resolve_integration.inplace_preflight` exit 34 条件。
- `[静态推断]` / `[转引]`：`0x35A0=8/9` 的索引语义（W59 U3 仍降级）；W39/W44 的 `2=` 变体可用；W59 的 `cmp reg,0x64` 两处 100 上限与 EOG 终止闸字节。
- `[待运行验证]`：见 `UNKNOWNS.md`（变体 B 未跑、`SkipMapSelect=yes` 臂、`0x35A0` 值语义、其它分辨率/语言版本）。

---

## 8 · 未签发 / 未主张

- 本卡**不签发**「(a) 是唯一可行路线」；`(c)` 未做，未比较优劣。
- 不主张「产品上可见第 3 个战役条目」——本卡就是**借官方 `[SOV1]` 入口**，菜单仍是两徽章（`screen_S2_campaign_menu.png` 与 W44 结论一致）。
- 不主张「MAPSELMD 子项键从 1 连续是必需项」：本卡只证明主用变体 A（from1）在 `SkipMapSelect=no` 上**够用**；W59 明确「`2=` 无 `1=` 疑点未定谳」，本卡未做 A/B 单变量真机对照（因主用未失败，按卡面「若失败请记录并回退对比」不需回退）。详见 `UNKNOWNS.md` U1 / `DISAGREE.md` D1。
