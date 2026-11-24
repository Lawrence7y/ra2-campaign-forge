# W65 · B 线新判据真机采集结果

> 执行者 **Hy4**（W65，非 Lead）｜卡目录 `lead\next_re_20261112_r02\W65_bline_live_collect\`
> `STARTED.txt` 在读任何文件之前写入：`2026-11-13T15:41:55Z`（= 23:41:55+08:00）；`HEARTBEAT.txt` 每 10 分钟后台心跳 + 每阶段手动追加。
> 真机窗口：`2026-11-13T23:56:25+08:00 ~ 2026-11-14T00:07:53+08:00`（4 趟，约 11.5 分钟）；收尾 `00:08:57`。
> 依据：`W62_bline_new_criteria\CRITERIA_SPEC.md`（**FROZEN 2026-11-13T23:25:30+08:00，本卡未改任何阈值/常量/规则**）、`tool_b_stats.py`、`tool_c_writeaudit.py`（均未修改）；采集层 `tools\w65_collect.py` 是 `W45_b_line_equivalence\tools\w45_dual_track.py` 的**本卡副本**（未改副本 `tools\w45_skeleton_copied.py` 留证），路径重定向到本卡、新增 `Scen+0x34AC` 读取与 §2.1 NDJSON 输出，**未直接 import 别卡脚本**。
> **Lead 只看落盘原始产物与退出码**：本文所有数值可回对 `out\*.ndjson` / `out\*_result.json` / `out\screen_*.png` / `out\cmd_*.log` / `out\w65_run.ndjson`。

---

## 0 · 一句话结论（严格口径）

`[本次实测]` **按 FROZEN 判据逐字运行，未经修改的 `tool_b_stats.py --compare` 输出 `SHIFT_DETECTED`**（`out\b_compare.json`，exit 0），短路命中 **B-2 `discrete_or_ui_mismatch`**。

**必须连带说明（不得省略）**：该 `SHIFT_DETECTED` **不是「检出装包导致的行为分布差异」**。触发原因是 FROZEN §2.1 把离散字段定义为「多重集（值→**计数**）」、§2.4 的 B-2 在 KS 之前短路；四趟按任务卡「约 1–2 分钟固定墙钟时长」采集，行数天然不等（A 合并臂 20,113 行 vs B 合并臂 20,229 行），于是五个离散字段的**取值完全相同、仅计数不等** ⇒ 直接判 `SHIFT_DETECTED`，根本没有走到 B-3/B-4。

实测分布侧的全部数值都**未显示任何差异**：`N_ks(A)=0.001572`、`N_ks(B 臂补算)=0.004586`（均远小于 `N_max=0.30`，噪声带极稳）、`D_ks=0.001286`、`p=0.766117`、`J_ui=1.0`、`ΔQ=0.0`。

> **严格措辞**：本卡**不签发**「B 线等价性成立」，**不签发**「装包导致分布差异」，也**不签发**「等价/不等价」任何结论。本卡只按事先冻结的判据输出一个词表内的词并如实披露其触发机制。
> 按 §3.4 / W55b §2.2 纪律：**未事后放宽阈值、未截断/补齐行数、未加白名单、未改判据工具、未重跑凑数**。四份原始 NDJSON 即真机原始产物。

---

## 1 · 四趟逐趟结果（`[本次实测]`）

四趟全部成功，`ok=true`，`errors=[]`，`read_fail=0`，`residual_own_pid=0`，逐趟 `IDENTICAL_TREE=true`，退出码全为 **0**。

| 趟 | 臂 | 包 | 锁（前→占→放） | 自启 pid | 进图 | 采样行数 | dframe 点 | read_fail | 残留 | 逐字节还原 | 退出码 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| A1 | A（不装包） | — | lead→w65→lead | 18184 | `SOV01UMD.MAP` | 10,084 | 10,083 | 0 | 0 | `IDENTICAL_TREE=true` | 0 |
| A2 | A（不装包） | — | lead→w65→lead | 16204 | `SOV01UMD.MAP` | 10,029 | 10,028 | 0 | 0 | `IDENTICAL_TREE=true` | 0 |
| B1 | B（装 v15 包） | v15 append，install rc=0 / verify rc=0 | lead→w65→lead | 22784 | `SOV01UMD.MAP` | 10,023 | 10,022 | 0 | 0 | `IDENTICAL_TREE=true` | 0 |
| B2 | B（装 v15 包） | v15 append，install rc=0 / verify rc=0 | lead→w65→lead | 34992 | `SOV01UMD.MAP` | 10,206 | 10,205 | 0 | 0 | `IDENTICAL_TREE=true` | 0 |

- 入口（与 W55b/W63 同一）：主菜单 `GUI:SinglePlayer` → `GUI:NewCampaign` → `GUI:CampaignMenu` → 屏幕坐标 **(210, 285) 苏联徽章** → 进第一关。四趟 `0x125C` 均为 **`SOV01UMD.MAP`**（官方第一关），`battle_idx=1`，`stage_idx=0`，`end_of_game=0`，`skip_map_select=0`。
- 两臂 **同一沙箱起点**：`sandbox_base` = `ra2youli` 只读字节副本 → 用 v15 `uninstall` 统一清掉既存 v0.3 旧包（W45 C2 口径），`verify` 报 `manifest_present=false`。之后 A/B 每趟各自 `robocopy` 出全新沙箱。
- **B 臂包**：用 `W60_battlemd_inplace\ra2forge_patched_v15\` 工具链从固定 `designs\w65_design.json` 构建 **append 路线**包（仅 `BATTLEMD98.INI` + `W65M1.MAP` / `W65M2.MAP` / `expandmd98.mix`，**无 `BATTLEMD.INI` 就地改写**）。`[本次读码]` 选择理由：append 不改写 `[SOV1]`，两臂经同一苏联徽章进入**同一张官方图**，才满足任务卡「保证可比」；若用 `battlemd:inplace`，A/B 会加载不同 `map_name`，`dframe` 分布比较失去意义且必然由 `map_name` 触发 B-2。此选择记入 `DISAGREE.md` D1 供 Lead 裁决。
- 四趟 cadence 全部 **6 ms**（`out\cadence.json`，两臂同一节奏），每趟墙钟 **75 s**（`t` 为实测单调时间），均远超 `n_min=30`。
- 每趟截图 2 张（战役菜单 + 局内），共 8 张；局内截图 2.33 MB 级，为真实游戏画面：

| 趟 | 战役菜单截图 (SHA-256) | 局内截图 (SHA-256) |
|---|---|---|
| A1 | `screen_A1_campaign_menu.png` `9815a7cf…f56f76` | `screen_A1_ingame.png` `687028de…8a630b` |
| A2 | `screen_A2_campaign_menu.png` `59ba4297…8b42` | `screen_A2_ingame.png` `7aee421b…7a20` |
| B1 | `screen_B1_campaign_menu.png` `b5b13a14…cb6` | `screen_B1_ingame.png` `bbc78f7d…8c9f` |
| B2 | `screen_B2_campaign_menu.png` `8b9b03b8…ec1b` | `screen_B2_ingame.png` `15cdb187…3005` |

（完整 64 位哈希见 `out\w65_run.ndjson` 的 `step=screenshot` 行。）

---

## 2 · dframe 分布统计（`[本次实测]`）

`dframe` = 相邻 `frame` 一阶差分；`frame = *(DWORD*)0xA8ED84`（32 ms 定拍计时器，≈31.25 计数/s）。6 ms 采样下 `dframe ∈ {0,1}`：约 77% 为 0、23% 为 1，正是 32 ms 拍点在 6 ms 仪器下的伯努利投影。

| 趟 | frame 首..末 | Δframe | `dframe` 直方图 | P(dframe=1) | Q(p10,p25,p50,p75,p90) | CV |
|---|---|---|---|---|---|---|
| A1 | 45..2385 | 2340 | `0:7743, 1:2340` | 0.2321 | 0,0,0,0,1 | 1.8191 |
| A2 | 69..2412 | 2343 | `0:7685, 1:2343` | 0.2336 | 0,0,0,0,1 | 1.8111 |
| B1 | 65..2409 | 2344 | `0:7678, 1:2344` | 0.2339 | 0,0,0,0,1 | 1.8099 |
| B2 | 52..2392 | 2340 | `0:7865, 1:2340` | 0.2293 | 0,0,0,0,1 | 1.8333 |
| A = A1∪A2 | — | — | `-2316:1, 0:15428, 1:4683` | 0.2328 | 0,0,0,0,1 | 138.82 |
| B = B1∪B2 | — | — | `-2357:1, 0:15543, 1:4684` | 0.2316 | 0,0,0,0,1 | 144.12 |

- 合并臂各含 **1 个拼接边界伪差**（A1 末帧→A2 首帧 = −2316；B1→B2 = −2357），这是 `A = A1∪A2` 逐行拼接、`dframe` 跨边界计算的必然产物，`out\w65_descriptive_stats.json` 如实列出；它同时解释合并臂 `CV≈139/144` 的异常大值。**两臂各一个、对称存在**，对 KS 的贡献量级 ≈1/20000，`b_compare.json` 的 `D_ks=0.001286` 已包含它。此性质与 FROZEN 工具自检里 `_merge()` 的语义完全一致，本卡未做任何剔除。
- 逐趟离散字段多重集（值）：四趟全部为 `{SOV01UMD.MAP: n}` / `{0: n}` / `{0: n}` / `{0: n}` / `{1: n}`，`ui_controls` 恒为 `[0]`，取值集合完全相同；**只有计数 n 因采样行数不等而不同**。
- 复算脚本 `tools\w65_report.py` 不 import 别卡脚本，其两样本 KS 公式与 `tool_b_stats.py:111-127` 逐字一致；`out\w65_descriptive_stats.json` 为补充描述统计，**权威判定仍以 `out\b_compare.json` 为准**。

### 2.1 FROZEN 判据输出（`out\b_compare.json`，`tool_b_stats.py --compare` exit 0）

| 量 | 实测值 | 冻结常量/规则 |
|---|---|---|
| `n_a` / `n_b` | 20112 / 20228 | `n_min=30` → B-0 不命中 |
| 同臂重复数 | A=2, B=2 | `n_noise_min=2` → B-0 不命中 |
| **`N_ks`（A 臂同臂 KS）** | **0.0015720042** | `N_max=0.30` → B-1 **不命中**（噪声带稳定） |
| `N_ks`（B 臂，补算） | 0.0045860889 | 同 << 0.30（补充量，非工具字段） |
| `D_ks` | 0.0012858485 | — |
| `p_value` | 0.7661169415 | `perm_iters=2000`, `seed=20261113`, `alpha=0.05` |
| `J_ui` | 1.0 | `theta_ui=0.95` |
| `ΔQ` | 0.0 | `qs=[.10,.25,.50,.75,.90]`，仅报告量 |
| `discrete_mismatch` | 5 个字段全部列出（值相同、计数 20113 vs 20229） | §2.3/§2.4 **B-2 短路** |
| **`verdict`** | **`SHIFT_DETECTED`** | `reason=discrete_or_ui_mismatch` |

判定顺序复核（不擅自改）：B-0 未命中 → B-1 未命中 → **B-2 命中，短路返回**；因此 B-3（`D_ks ≤ max(N_ks, D_floor)` 且 `p ≥ α` ⇒ `SAME_DISTRIBUTION`）与 B-4 均**未被求值**。本卡不代为求值、不改写判定、不「如果走到 B-3 会怎样」当结论。

---

## 3 · 判据 C（安装期零越界写入，`[本次实测]`）

用未修改的 `tool_c_writeaudit.py --audit` 对 **B 臂真实装包过程**跑一次：从同一 `sandbox_base` 复制出惰性沙箱 → v15 `install`（与 B1/B2 同一命令，rc=0）→ `uninstall`（rc=0），取 `S_pre / S_post / S_uninst` 三份全树快照，`D` 由**包内容 + 事先写死的引擎白名单**构造（不是从运行时写集反推）。产物：`out\c_audit_{before,after,uninst,declared}.json`、`out\c_audit_B_arm.json`。

| 项 | 结果 |
|---|---|
| `W`（写入集） | `BATTLEMD98.INI`, `W65M1.MAP`, `W65M2.MAP`, `expandmd98.mix`, `ra2forge_install.json`, `ra2forge_install.json.seal`（6 项，全部 `added`） |
| `D`（声明写集） | 同上 6 项 ⇒ **`W ⊆ D`，`W \ D = ∅`**（C-1/C-2 `true`） |
| `P_prot` 受保护文件 | 641 个装前已存在文件，`protected_all_equal=true`，逐条哈希留证 ⇒ **受保护文件哈希全等**（C-3 `true`） |
| 卸载还原 | `restore.equal=true`，`residual_outside_whitelist=[]` ⇒ C-4/C-5 `true`，逐字节净零 |
| C-6 | `null`（append 路线，非 inplace，不适用） |
| **`verdict`** | **PASS**，`failed_checks=[]`，工具 exit **0** |

`[转引]` W62 交付的工具自检：C-A/C-B/C-NEG `C_ALL_PASS=True`；B-POS/B-NEG/B-NEG2 `TOOL_SELFTEST_PASS=True`（`W62_bline_new_criteria\EVIDENCE\*.exit.txt` = 0）。本卡未重做、未改其任何字节。

---

## 4 · 真机纪律（`[本次实测]`，逐项可回对）

| 红线 | 本卡 |
|---|---|
| 取锁/放锁，**lock per trip** | 每趟前读 `.game_instance.lock`，要求 `owner=lead` 且 `gamemd` 活体 0，否则等待；取锁写 `owner=w65`；**每趟结束（finally，无论成败）**写回 `owner=lead` + 状态。`w65_run.ndjson` 记录 4 组 `lock_before/claimed/released`，趟间锁文件始终为 `owner=lead`，**从未长期占锁** |
| 不写 `ra2youli` | 只作 `robocopy` 只读源 + 全树哈希目标；PRE/POST 全树 **647 文件 / 1,989,215,270 B**，added/removed/modified **全 0**，`IDENTICAL_TREE=True` → `REAL_DIR_PROOF.txt` |
| 不 `taskkill` 用户进程 | `pre_launch_guard` 每趟确认 0 个 gamemd；只关闭本趟 WMI 自启 pid（18184/16204/22784/34992），`WM_CLOSE` → `taskkill /PID <own>` → `/F`；`residual_own_pid=0`，收尾 `gamemd residual=[]` |
| 沙箱可写配置字节副本 + 哈希，收尾逐字节还原并实算自证 | 每趟启动前字节复制**全部根级文件**（A 419 / B 425 个）+ 全树哈希 manifest；收尾按 PRE/POST 差异逐文件还原并**重算全树哈希**，四趟 `IDENTICAL_TREE=true`（游戏仅改动 `SOV01UMD.sav`，已从 pristine 字节副本还原）。见 `out\restore_proof_*.json` |
| 只读采集 | `OpenProcess(PROCESS_VM_READ\|PROCESS_QUERY_INFORMATION)` + `ReadProcessMemory`；`EnumWindows/EnumChildWindows`；`PIL.ImageGrab`。**无写内存 / 断点 / 挂线程 / 注入 / 改 exe** |
| 桌面预检 | 每趟 WMI 启动后即刻 `step0_desktop_precheck`：`WinSta0\Default`、EnumWindows 405–418 / 22–25 可见、ImageGrab OK 2560×1440，`pass=true` |
| 只写本卡目录 / git 只读 | 所有产物在 `W65_bline_live_collect\`；无 commit、未改他卡交付物 |

内存读数（`tools\w65_collect.py:read_observables`）：`frame` ← `[0xA8ED84]`；`Scen* = *(DWORD*)0xA8B230`；`map_name` ← `Scen+0x125C`（260 B C 串）；`stage_idx` ← `+0x35A0`(WORD)；`end_of_game` ← `+0x34AC`(BYTE)；`skip_map_select` ← `+0x34B0`(BYTE)；`battle_idx` ← `+0x34CC`(DWORD)；`ui_controls` ← 可见控件 id 集合。全部字段与 `CRITERIA_SPEC.md §2.1` 一致，四趟 `read_fail=0`。

---

## 5 · 分级标注速查

- `[本次实测]`：四趟逐趟状态/截图/锁/残留/还原；dframe 全部统计；`b_compare.json` 判定与全部数值；C 审计 PASS 与逐文件哈希；真目录 PRE/POST 全树零改动；桌面预检；install/verify 退出码。
- `[本次读码]`：`CRITERIA_SPEC.md §2.1/§2.4/§2.5`、`tool_b_stats.py`（`multiset()` / `compare_arms()` 短路顺序）、`tool_c_writeaudit.py`、`w45_dual_track.py` 采集骨架、v15 `BATTLEMD98.INI` append 语义、`W63_route_a_e2e` 的入口与偏移。
- `[静态推断]`：合并臂拼接边界伪差对 KS 的影响量级 ≈1/n；append 路线不改写 `[SOV1]` 故两臂同图。
- `[转引]`：W55b 旧判据失效数值；W62 工具自检 PASS；W59/W63 内存偏移定义；W45 C2 清包口径。
- `[待运行验证]`：见 `UNKNOWNS.md`（判据 B-2 计数敏感性、inplace 臂、其它分辨率/语言、更长采样、其它观测量）。

---

## 6 · 未主张

- **不写**「B 线等价性成立」「行为等价已成立」——明确禁止。
- **不写**「检出装包导致的分布差异」——本次 `SHIFT_DETECTED` 由离散多重集计数不等触发，分布侧数值未显示差异；本卡不把判据输出误述为物理结论。
- **不签发**任何等价/不等价结论；签发权在 Lead。本卡是执行者，只交付「原始产物 + 退出码 + 判据逐字输出」。
