# ① 原版基线离线测量方案（U0800 · GOAL-3T）

> **本件性质**：纯离线设计。**未启动游戏、未发射任何 trip、未改任何母本/探针/trip 脚本/游戏目录**；唯一写入 = 本文件。
> **依据**：Notion D5（`ROUND_SUBAGENT_LOG_TRIGOAL_20261017.md:3312-3320`，关键约束原句在 `:3318`）+ 台账 §288（T55k 结果，`:3286-3298`）+ §290/§291。
> **证据分级**：`[实证]`（本轮亲读/亲算，附路径:行号或命令）/`[推演]`/`[设计假设]`/`[待实测]`。**不升格。**
> **日期**：2026-10-20。**被测二进制钉点**：`gamemd.exe` 4,825,360 B / `73201cc0…f67476`（本轮 `sha256sum` 复核）。
> **地址纪律**：VA 与 file_off 成对；本镜像 `.text` VAddr==RawPtr==0x1000，故 `file_off = VA − 0x400000`。

---

## 0. 判词（先给结论）

1. **基线臂 = 「直启原版」臂（Arm A），不是「P2 DLL + 全键关」臂。** 关键事实：`qc151_trip.py` 的每一次真机趟**本来就是 DLL-free 的原版直启**——脚本只 `Popen` 载体 `gamemd.exe`（`qc151_trip.py:1072-1099`），启动后由 S-4 模块闸门**硬性要求** `ra2render`/`ra2loader` 命中数 = 0（`:926-1030`、`:6464`），T55k 实测模块表 11 项、零命中（`t55k_20261020/s4_module_table.txt` + `qc151_fields.json` S4 组 `modules_total=11 / hit_count=0 / s4_gate=pass`）。因此 **Arm A 零代码、零新旗标、零新风险**。反过来，「P2 DLL + 全键关」**在科学上不能当基线**：该 DLL 在 `DLL_PROCESS_ATTACH` 里**无条件**挂 CellClassDraw / GreatestThreat / RadarFog 与 13 个虚表钩子（`blitter_hooks.cpp:3816-3819`、`:3896-3903`），灰雾混色桩 B1/B2/全量重刷补丁**不看任何开关**照装（`:2764`/`:2770`/`:2783`；独立审计同一结论 `docs/re/INSTALLED_HOOKS_AUDIT.md:193` A6）——「键全关」≠「原版行为」。
2. **负载 = `XMP29U2.MAP` = spawnfix8 `0add791d`**（U0800 内容，`[Units]` 3360 / `[Infantry]` 2240，h0/h1 各 240/160），预期 `units0 ≈ 971`（T50 单次实证），设计门 `units0 ≥ 800`。**不要**用 `[2]0LoadBench_U0800.yrm` 当身份锚——本轮算术证明**实际载入的是 `XMP29U2.MAP`**（§2.1）。
3. **指标**：主判据全用**帽无关**量——`frame_ms` 尾部（p90/p99/max）、`>34ms` 占比、**越帽面积 E**、`tick_miss`、`max_stall`、`logic_frames`、`n_multi_advance`、1 Hz 的 `units/infantry/ws_kb`；`fps_avg` **只作描述、不作判据**。**`Speed.UnlockGameSpeed=1` 不要设**——它是**空开关**（读进全局但执行体是空函数且从未被调用，`blitter_hooks.cpp:1169-1172`、`dllmain.cpp:25-38`、审计 `:190` A3），而且设它就得先经 loader 加载 DLL（被 S-4 禁止）。
4. **解除上限的唯一低成本路径 = `[Skirmish] GameSpeed` 上调**（2→6），但**该键是否作用于会话未经证实**（§6-U3），列为第二负载档 L2、带失败回退。
5. **必须先修一个「假门禁」认知**：`--target-map/--target-sha256` 的 PASS **不证明载入的是哪张图**（§2.1、§5.3-D1）。本方案把地图身份改为**运行期算术判据 + evidence 内 `XMP29U2.MAP` 哈希**双证。

---

## 1. 基线臂定义

### 1.1 三个候选与裁决

| 臂 | 构成 | 可行性（本轮亲读） | 代价 | 裁决 |
|:--|:--|:--|:--|:--|
| **A 直启原版** | 载体 `gamemd.exe`（`73201cc0`）直启；`ra2render.dll/ra2loader.exe` 在位但**证明未被加载**；`ddraw.dll`（cnc-ddraw）作为呈现包装器在位（与 T24→T55k 全部历史趟一致） | **已具备**：`launch_direct` 唯一 `Popen`，`lpApplicationName` = 载体 exe 全路径（`qc151_trip.py:1099`），禁止面明文禁止 loader/批处理/`start` 转接（`:21-35`）；S-4 命中数必须为 0（`:798-818`）。T55k 实测 11 模块、零命中 | **0 代码 / 0 新旗标 / 0 新签署**；代价=「原版」含 cnc-ddraw 呈现层，是**原版二进制 + 包装器**，须在报告抬头如实写 | **推荐（唯一当基线者）** |
| **B P2 DLL + 全部优化键关** | 经 `ra2loader.exe` 加载 `ra2render.dll`（`39cbd665`），`ra2render.ini` 全键置原版侧 | **当前被 S-4 结构性禁止**：`ra2loader` 命中即 `EXIT_INJECTION_SUSPECTED=62`（`:1005-1020`）；`ra2loader` 本身就是 `CreateProcess(CREATE_SUSPENDED)`+`VirtualAllocEx`+`CreateRemoteThread(LoadLibraryA)`（`ra2loader.cpp:36-58`） | 需**新旗标 + S-4 政策例外 + 新签署 + 异族核验**（一个新开项，非本步） | **驳回为基线**（非原版，且装钩无条件） |
| **C 两者都做** | A + B | B 不可行，故 C 不可行 | — | 驳回 |

**决定性理由（B 为何连"近似原版"都不成立）**：
- `InstallVTableHooks()` 里 `InstallCellClassDrawHook()` / `InstallGreatestThreatHook()` / `InstallRadarFogHooks()` 三行**不接受任何键门控**（`goal3_configsplit_20261019/blitter_hooks.cpp:3896-3903`）。
- 灰雾混色桩 B1/B2 与 `0x006D3D99` 全量重刷补丁在 `InstallCellClassDrawHook` 内**无条件**打字节（`:2764`=B1、`:2770`=B2、`:2783`=`0x006D3D99` 全量重刷；审计 `docs/re/INSTALLED_HOOKS_AUDIT.md:193`）。
- 独立审计早已把这条列为「开关关不干净」：`docs/re/INSTALLED_HOOKS_AUDIT.md:193`（A6，风险=中高：回滚实验会被污染基线）。
- 因此 **B 是"优化臂"的候选，不是基线的近似**。基线必须与优化臂在「是否加载 DLL」这一维上**硬分离**。

### 1.2 Arm A 的「原版」口径边界（必须写进报告抬头）

| 维度 | 状态 | 证据 |
|:--|:--|:--|
| 游戏二进制 | 原版 `73201cc0…`（`ct` 载体与母本同 sha） | `t55k_20261020/qc151_fields.json` CTRL1 组 pre/post 均 PASS |
| 是否注入 | 否（S-4 零命中、11 模块） | 同上 S4 组 + `s4_module_table.txt` |
| 进程注入面 | `ra2render` 字串在 `gamemd.exe` 内**出现 0 次**（无导入、无 LoadLibrary 名） | 本轮 `python` 扫描 `gamemd.exe` 字符串：`ra2render` 计数 0 |
| 呈现层 | **cnc-ddraw 包装器在位**（`ddraw.dll` `85e0f7d5…`、`ddraw.ini` `95949842…`） | 本轮 `sha256sum`；`ddraw.ini:1` `windowed=false` |
| 渲染/逻辑节拍 | 原版 `MainLogicFrame`（`0x55D360`）+ `LogicUpdate`（`0x55E160`） | `docs/re/clock_frame_loop.md:207-250`；本轮字节复核见 §3.2 |

> **⇒ 报告必须写：「本基线 = 原版二进制 + cnc-ddraw 呈现包装器 + 零注入；与优化臂的差异仅在是否加载 ra2render 及键值」。** 不得写成"纯净原版"。

---

## 2. 负载（U0800 + spawnfix）

### 2.1 ★ 先纠一个身份错误：载入的是 `XMP29U2.MAP`，不是 `--target-map` 指的 `[2]…yrm`

**本轮实证 + 算术封闭**：

| 事实 | 数据 | 来源 |
|:--|:--|:--|
| T55k 的 `--target-map` 是 `[2]0LoadBench_U0400.yrm`（`93c2974b`，222,799 B） | pin/actual 均 PASS | `t55k_20261020/qc151_fields.json` TARGET 组 |
| T55k 载体里另有 `XMP29U2.MAP` = `9e33585c`（spawnfix10lite，U0800 内容） | `sha256_dst` 实测 | `carrier_creation_receipt.json` `files["XMP29U2.MAP"]`；evidence 内同哈希 |
| T55k 窗内 h2/h3 `c5574` 均 = **240** | — | `qc151_fields.json` `p003774_h2_c5574=240` / `h3=240` |
| 而 `U0400` 图里 Neutral 预置**只有 120 车 / 80 步** | 本轮亲算 `[Units]` 1680 行 = 14×120 | 本轮解析 `_src_variant_800x600_csf/[2]0LoadBench_U0400.yrm` |
| `U0800` 族图里 Neutral = **240 车 / 160 步** | 本轮亲算 3360 行 = 14×240 | 本轮解析 `[2]0LoadBench_U0800.yrm` 与 `XMP29U2.MAP` 各版 |

**⇒ h2=240 在 U0400 图上是数学不可能的；载入体必为 U0800 内容，即 `XMP29U2.MAP`。** 旁证：T49 的 `--target-map` 明确钉的就是 `_src_variant_800x600_csf\XMP29U2.MAP`（`e3acc130`），得 `units0=491`（`archive_T49_u0800/qc151_fields.json` TARGET 组 + `measure_w0.json`），而 491 的构成，卡面原文为「探针实锤 h2 Neutral c5574=240 + h3 Special c5574=240 + 双方 MCV/单位」（`cards/QC161.md:760`）——与 raw U0800（14 户各 240/160）自洽。

**结论（写进方案，不留给判读）**：
- **`--target-map/--target-sha256` 的 PASS 不是地图身份证明**（脚本只校验该文件本身的哈希，`qc151_trip.py:6344-6363`；载图走后门）。
- 另有一处**恒假字段**：`F-4`（`slot_file_sha256_post`）路径写死为 `carrier_dir / "[2]0LoadBench_U0400.yrm"`（`:4206`）—— 无论载的是哪张图，它都去哈希那个 yrm。**任何以 F-4 论证载图身份的说法都是假证据。**

### 2.2 选哪个 spawnfix：`spawnfix8 = 0add791d`

本轮把候选逐版亲算（`[Units]`/`[Infantry]` 逐 owner 计数 + 逐节字节比对）：

| 变体 | sha256 | 与 raw U0800 的关系 | 车/步 行数 | h0 / h1 归属行 | 真机证书 |
|:--|:--|:--|:--|:--|:--|
| **raw `e3acc130`** | `e3acc130…8d9e39` | 原图 | 3360 / 2240（14×240 / 14×160） | 无令牌（Americans/Russians…）→ 实例化成 Neutral/Special | T49：**units0=491**，15 游戏秒人类容器清零、终局（`cards/QC161.md:760`） |
| **`spawnfix8 0add791d`** | `0add791d…60bc` | **只改 800 个 Owner 令牌**：`[Units]` 400→`<human player>`/400→`Computer`，`[Infantry]` 160/160；**其余字段 0 处改动、其余 9 节逐字节相同** | 3360 / 2240 | 240/160 与 240/160 | **T50：units0=971、四屋全活、20+ min 长战局、def1F5 全程 0**（`GOAL_THREE_TARGETS_20261018.md:94`） |
| `spawnfix9 92110131` | `92110131…0103` | sf8 + 800 行同格复制 | 3840 / 2560 | 480/320 与 480/320 | T55d：**units0=961、硬冻结@f437**（日志 §185，`:2152`） |
| `spawnfix10 5b47ee04` | `5b47ee04…e181` | sf9 − 400 行 | 3600 / 2400 | 480/320 与 240/160 | T55e：units0=1212，h1 30s 内被清洗（§190，`:2226`） |
| `spawnfix10c f3bb0a4e` | `f3bb0a4e…7b9a36` | sf10 + h1 错格复制 | 3840 / 2560 | 480/320 与 480/320 | T55f：units0=**1452**，h1 30s 败北、记分板（§192，`:2252-2254`） |
| `spawnfix10lite 9e33585c` | `9e33585c…2ab2bc` | sf10 − h0 半量 | 3480 / 2320 | 360/240 与 240/160 | T55g 1092（h0 7s 被清）、T55h 1092、T55j 710（跑到 f3950，但测窗全零） |

**为什么选 sf8**（三条同时成立的唯一一个）：
1. **只动 Owner 令牌**（本轮 diff 实测 4 hunk、800+/800−、非 owner 字段改动 = 0、其余节 identical）⇒ 对"单位数-帧质量"曲线的**唯一自变量是归属**，无复制行带来的同格堆叠/装载毒副作用。
2. **有 20+ 分钟长战局证书**（T50），这正是三窗 75 s 连续测量的前提。
3. sf9/sf10/sf10c **全部**在开局 30 s 内出现某屋败北或硬冻结（§190/§192/§185）⇒ 无法支撑 75 s 窗；raw U0800 只有 491 单位且 15 s 终局。

**代价**：sf8 在 T50 是**贴帽**（p90 35.2-37.4 ms、>34 ms 占 24.96%，`GOAL…:53`），**它本身可能不破帽**。所以负载设计必须配两个上探档（§2.4 的 L2/L3），不能指望 sf8 单独把 fps 压到 31 以下。

### 2.3 门禁：「ShortGame=no」如何满足；「每阵营有建筑」为何不用

- Notion 原话口径为「**ShortGame=no 或 每阵营有建筑**」（`ROUND_SUBAGENT_LOG_TRIGOAL_20261017.md:2791`）。本方案走**前者**。
- **满足方式**：源变体 `RA2MD.INI` 的 `[Skirmish] ShortGame=no`（`_src_variant_800x600_csf/RA2MD.INI:25`），**不靠点击**。T55k 实证：源 = no，收尾写回 `[Skirmish] ShortGame=no`（`t55k_20261020/evidence/20261020T092208043279/RA2MD.INI:25`），且探针 P3 全局/会话同读 = 0/0（`qc151_fields.json` `qc213p2_p3_shortgame_glob=0`、`p3_shortgame_sess=0`、`p3_equal=true`）。
- **运行时交叉验证**（免代码）：§288 的 P3 探针在 measure 起点自动快照；`shortgame_glob==0 ∧ equal==true` 即"会话内武装的是 no 分支"。
- **「每阵营有建筑」弃用理由**：U0800 全系列图**没有 `[Structures]` 节**（本轮解析：27 个节名里无 Structures；`h1_persist/H1_PERSIST.md:124` 同结论）。要造建筑只能改图 = 引入新自变量（且会改 `units_seen` 负载签名，`H1_PERSIST.md:442`）。**不采纳，除非 Lead 另裁。**

### 2.4 负载梯（三档，串行）

> 命名：**基线臂永远是 A**（§1）；此处是同一基线臂下的三个**负载档 L1/L2/L3**，避免与「优化臂 B」混淆。

| 档 | 图 | GameSpeed | 目的 | 预期 units0 | 破帽预期 |
|:--|:--|:--|:--|:--|:--|
| **L1（首发，推荐）** | sf8 `0add791d` | 2 | 拿到「有长战局证书」的基线与全部帽无关量 | ≈ 971（T50 单点） | 可能仍贴帽 → 靠尾部/E 判 |
| **L2** | sf8 `0add791d` | **6** | 抬上限，让低于帽的工作时间可见 | ≈ 971 | 若上限真的上移，p50 应显著下移 |
| **L3（上探）** | sf10c `f3bb0a4e` | 2 | 加负载到 fps 明显 <31 | ≈ 1452（T55f 单点） | 高（T55f p50=15.7 fps） |

L3 的硬风险：T55f 在 30 s 内出现 h1 败北 + 记分板（`§192`），三窗大概率测不到。**L3 只作"破帽支臂"，不作基线**；一旦 V5 门（§5.2）失败即如实记「负载上探失败」并回 L1。

---

## 3. 指标

### 3.1 为什么现有 `fps_avg` 量不出卡顿（本轮量化）

| 观测 | 值 | 来源 |
|:--|:--|:--|
| 41 单位局（T25） | 三窗 `fps_avg=31.24/31.24/31.28`（方差 0.04） | `GOAL_THREE_TARGETS_20261018.md:49`；日志 `:445` |
| 842 单位局（T55k） | 三窗 `31.24/31.28/31.24`，p50=32.24 ms | `t55k_20261020/measure_w0.json` `stats` |
| **20.5× 负载差 → fps 差 0.04** | — | 两句对照 |

**⇒ 31 fps 是限流器（limiter）而不是工作量的函数**。同一周期在 T55k 的 w0 上：`frame_ms p50=32.2425 / p90=36.7425 / p99=41.699 / max=48.165 / tick_miss=0 / logic=781 / edges=782`，本轮再算分布：**>32.24 ms 占 50.06%、>34 ms 占 28.17%、>40 ms 占 2.69%、>50 ms 占 0%**（脚本见 §8-A3）。中位数恰好钉在帽上、一半帧只比帽慢一丝 —— 典型的"限流器 + 轻微超额"形态。

### 3.2 帽的机器层依据（本轮字节复核，均 MATCH）

| 事实 | VA / file_off | 字节 | 判定 |
|:--|:--|:--|:--|
| 局内帧节拍 `Sleep(10)` | `0x55D3B2` / `0x15D3B2` | `6A 0A FF D6` | `[实证]` |
| 帧起点取样 | `0x55D3D4` / `0x15D3D4` | `FF 15 30 15 7E 00 A3 5C B5 A8 00` = `call [timeGetTime]` + 存 `0xA8B55C` | `[实证]` |
| 帧体耗时累计 | `0x55DE13` / `0x15DE13` | `2B 05 5C B5 A8 00` = `sub eax,[0xA8B55C]`（**不含 Sleep**） | `[实证]` |
| 累计/计数清零 | `0x6477ED`(xor eax,eax) → `0x6477EF` / `0x6477F4` | `33 C0` 后 `A3 60 B5 A8 00`(0xA8B560) `A3 64 B5 A8 00`(0xA8B564) | `[实证]` |
| 目标帧间隔 = `1000 / [0xA8B558]` | `0x55D51C` / `0x15D51C` | `B8 E8 03 00 00`(mov eax,1000) `99` `F7 3D 58 B5 A8 00`(idiv [0xA8B558]) | `[实证]`（与 `docs/re/clock_frame_loop.md:472`、`docs/re/b_class_static_closeout.md:65` 同址） |
| 结果落到节拍间隔 | `0x55D55E` / `0x15D55E` | `89 35 30 73 88 00` = `mov [0x887330], esi` | `[实证]` |
| 目标 fps 默认值 = 30 | `0x52DABD` / `0x12DABD` | `C7 05 58 B5 A8 00 1E 00 00 00` = `mov [0xA8B558], 0x1E` | `[实证]` |
| 引擎文档口径 | — | `GameSpeed 6=60fps / 3=30fps`；`0x887330` 门控 `LogicUpdate` | `docs/re/b_class_static_closeout.md:65`；`clock_frame_loop.md:244` |

**⇒ `[Skirmish] GameSpeed` 经 `[0xA8B558]`（目标 fps）→ `0x887330`（目标间隔 ms）影响节拍，是**唯一**能把上限抬起来的既有旋钮；`1000/30 = 33.3 ms` 与实测周期 32.0 ms 同量级（差 ~3%，机制细节未逐指令确认，见 §6-U4）。**注意**：`CurrentFrame` 每 `MainLogicFrame` 自增（`:22`、`:276`），而 `0x887330` 门的是 `LogicUpdate`（世界更新）——二者关系未逐指令闭合，**不得**在报告里把"fixtarget fps"写成因果定论。

### 3.3 帽无关指标集（本方案的判据全部出自这里）

| # | 指标 | 定义/来源 | 为什么帽无关 | 已有字段 |
|:--|:--|:--|:--|:--|
| M1 | `frame_ms` p90 / p99 / max | 帧沿差分（`_measure_stats`，`qc151_trip.py:3769-3795`） | 帽只抬**下界**；越帽部分如实反映工作 | `stats.frame_ms_p90/p99/max` |
| M2 | **越帽面积 E** | `E = mean(max(0, frame_ms − 32.24))`，毫秒/帧 | 帽以下记 0，帽以上线性累积 = 纯工作量外溢 | `frame_edges` 离线算（§8-A3） |
| M3 | `>34 ms` 占比 `f34` | 34 = 帽 32.24 + ~1.7 ms 量化余量（`goal1_c1c2_readj_20261018/C1C2_READJ_T50.md:28`） | 同上；是 C1/C2 历史唯一可测量口径 | `frame_edges` 离线算 |
| M4 | `tick_miss` | 沿间隔 > 1.5×p50 计数（`:3791-3792`） | 相对量，不依赖帽绝对值 | `stats.tick_miss` |
| M5 | `max_stall_s` | 最长连续 `df=0` 墙钟跨度（`:3750-3760`） | 直接量停顿，与帽无关 | `stats.max_stall_s` |
| M6 | `logic_frames` / 窗 | 首末帧差（`:3736`） | 帽无关；空窗/终局的直接判据 | `stats.logic_frames` |
| M7 | `n_multi_advance` | `df>1` 的沿数（`:3777-3779`） | 漏采/长间隔证据 | `stats.n_multi_advance` |
| M8 | 1 Hz `units/infantry/ws_kb/pf_kb` | `_rpm_counters`（`:2956-2978`） | 负载与内存的直接读数 | `counters[]` |
| M9 | **每帧体耗时累计差**（候选，需新探针） | `Δ[0xA8B560]/Δ[0xA8B564]` = 平均帧体 ms（**不含 Sleep、不含 `0x55E160` 世界更新**） | **完全不受帽影响**（量的是帧体） | **无现成字段** → 新开项（§6-U5） |
| M10 | 地图身份算术 | h2/h3 `c5574`（240=U0800 类 / 120=U0400 类） | 与帽无关 | `qc151_fields.json` QC213 组 |

**M9 的诚实边界**：`0x55D360` 的耗时记账点在 `CurrentFrame++` **之前**、`0x55E160()` **之前**（`clock_frame_loop.md:207-240` 伪码 + 本轮字节 `0x55DE13`），所以它**漏掉世界更新**这一段（恰恰是 N 单位卡顿的主嫌疑）。因此 M9 只能当**辅助**，不能单独作验收；主判据仍 M1/M2/M3。

### 3.4 是否用 `Speed.UnlockGameSpeed=1` —— **不设**

| 事实 | 证据 |
|:--|:--|
| 键被读进全局 | `goal3_configsplit_20261019/blitter_hooks.cpp:632-633`（`GetIniIntEx("Speed","UnlockGameSpeed",0,…)` → `g_unlockGameSpeed`） |
| **执行体是空函数** | `:1169-1172`（`EnforceGameSpeedUnlock(){ /* 注释 */ }`） |
| **且从未被调用** | `ra2render/dllmain.cpp:25-38`：ATTACH 只调 `InstallVTableHooks()` / `EnableLowFragmentationHeap()` / `timeBeginPeriod(1)` |
| 审计结论 | `docs/re/INSTALLED_HOOKS_AUDIT.md:190`（A3：「装了开关、没装生效路径」，建议注明 no-op） |
| 出厂值 | `ra2render.ini:54` = 0（且注释自称"保护原版速度控制权"） |

**⇒ 设 1 = 零行为；且要设它必须先让 DLL 进进程（被 S-4 禁）。** 方案里**不要**出现这个键作为杠杆，避免下一次误判成"已解上限"。

### 3.5 三窗 25 s 够不够

| 维度 | 数 | 判定 |
|:--|:--|:--|
| 单窗样本 | 782 帧 @ 500 Hz（`hz_effective=500.1`） | p90 有 78 帧、p99 有 7 帧 ⇒ p90/p99 可读；**p99.9（≤1 帧）不可读** |
| 三窗合计 | 2345 帧 / 75 s | 对 1% 尾部足够；对"偶发 1 次深停顿"**只能报"本次观测到的 max"**，不能报分位 |
| 覆盖的战役区间 | T55k：`nav_start` 结束 36.8 s → `frame` 段 126.2 s → `measure_w0` 起于 167.0 s（`qc151_fields.json` BUDGET 组）；窗内帧号 3899→6244 | **只覆盖稳态中段**；开局刷兵/集结段（T55e 的前 128 帧爬了 15.7 s，§190）**永远测不到** |
| 结论 | 25 s×3 **够判稳态卡顿与尾部**，**不够判"开局/终局段"** | 开局窗缺口见 §6-U6（需新旗标，新开项） |

### 3.6 阈值与误判边界

| 判据 | 取值 | 依据 | 误判边界（必须先排除才算） |
|:--|:--|:--|:--|
| 帽参考 `CAP_MS` | **32.24 ms**（31.24 fps 实测中位） | T55k w0 `frame_ms_p50`；与 `1000/30=33.3` 同量级 | 每趟用**同趟** p50 复算，不跨趟套死 |
| 可分辨最小越帽 | **34 ms** | 32.24 + ~1.7 ms 量化余量（`C1C2_READJ_T50.md:28`） | 轮询粒度 2.49 ms（T55k 实测 `dt` 中位 2.493 ms）⇒ 单帧 ±2.5 ms，故只对**占比**下结论、不对单帧下结论 |
| `E`（越帽面积） | 报告值，不设先验阈值 | — | 首次基线无历史分布 ⇒ **只做"基线 vs 优化臂"同条件对比**，不做绝对判定 |
| `f34` | 报告值；参照 T50=24.96%（`GOAL…:53`） | — | 同上 |
| `max_stall` | > **0.5 s** 记为"停顿事件"，> **2.0 s** 记为"疑似终局/冻结" | 因果：终局会冻结（T55h 373、T55e 378） | **停顿必须与 `def1F5` 翻转或记分板帧联动排除**，否则不得记作卡顿（§5.4-D4） |
| `logic_frames` | 单窗 < **0.8×中位窗** 记"降速窗"；=0 记"空窗" | `_measure_stats` 零推进 ⇒ 全 null（`:3761-3764`） | 空窗多半=终局/焦点丢失 ⇒ 先看 `verdict`/`forensics` |
| `tick_miss` | 报告值（T50 5/0/2；T55k 0/0/0） | `stats.tick_miss` | p50 钉帽时阈值=1.5×32.24≈48.4 ms ⇒ 只抓**深**停顿，不抓浅越 → 故必须配 `f34`/`E` |

---

## 4. 执行步骤

### 4.1 载体准备（全部在**新建专用目录**内，不动共享变体）

| 步 | 动作 | 硬要求 |
|:--|:--|:--|
| P1 | 新建源变体 `LEAD\qc161_u0400_trip\_src_variant_u0800_sf8_<YYYYMMDD>\`，从 `_src_variant_800x600_csf\`（94 件）**整树复制**（含 `ra2.csf`/`ra2md.csf`——缺它们会弹 "Unable to initialize 'ra2.csf'" 错误框，历史 T14 事故） | **不改动共享变体**（共享变体是 T55k 参照，`evidence/_EVID_REFERENCE.json` 依赖其字节） |
| P2 | 用 `_maps_fixed\XMP29U2.MAP.spawnfix8_0add791d`（311,822 B / `0add791d…60bc`）**覆盖**新变体的 `XMP29U2.MAP` | 覆盖后必须复核 sha = `0add791d…60bc` |
| P3 | 新变体里其余 loadbench yrm（`U0050/U0100/U0200/U0800/U0400`）留不留 | **待裁**（§6-U7）。默认**保留 `[2]0LoadBench_U0400.yrm`**（复刻 T55k 载体组成、减少自变量）；`F-4` 会哈希它，但该字段恒假（§2.1），不参与判读 |
| P4 | `RA2MD.INI`：`[Skirmish]` `ShortGame=no`、`GameSpeed=2`（L1/L3）或 `6`（L2）、`Credits=10000`、`UnitCount=10`、`Slot01=6,8,1`，其余同现变体（`_src_variant_800x600_csf/RA2MD.INI:18-36`） | 现值即满足；L2 只改 `GameSpeed` 一行并**留 backup** |
| P5 | `ddraw.ini`：`windowed=false`（`:1`，实际生效行是 `[ddraw]` 内 `:21`，见 §4.5 缺陷注记）、`fullscreen=false`（`:15`）、`maxfps=-1`（`:31`）、`maxgameticks=0`（`:89`，=emulate 60 Hz vblank，**不构成 31 帽**）、`vsync=false`（`:35`）、`renderer=direct3d9`（`:50`）、`hook=4`（`:94`）、`singlecpu=true`（`:109`） | **一字不改**（全历史趟同值，是常量）；若必须改须先证"为何不是自变量" |
| P6 | `ra2render.ini` / `ra2render.dll` / `ra2loader.exe`：**原样放进载体**（不删、不改） | 保留是为了让 S-4 闸门**有东西可查**（零命中才成立）；删掉反而降低证据强度 |
| P7 | 列 `--carrier-create-files` 名单：84 项（以 `_t31_create_files_list.txt` 为底，**必须含** `XMP29U2.MAP`、`[2]0LoadBench_U0400.yrm`、`RA2MD.INI`、`ddraw.ini`、`ra2render.ini`、`ra2md.csf`、`ra2.csf`；**必须排除** 任何 `ra2render.log`） | 名单是**单行逗号串**，含空格的 `RA2MD Update.ico` 必须整体加引号（否则词分割，历史 D-111 教训） |

> **载体件数 + 一个本轮查实的账目差异**：脚本自动追加 `CARRIER_FILES` 五件（`qc151_trip.py:213-214`、`:6318-6325`）⇒ t31 名单 84 + 5 = **89**。但 T55k receipt 只有 **88** 件（本轮 `len(receipt['files'])==88`），唯一缺项是 `RA2MD Update.ico`——而该文件在源变体里**确实存在**（4,710 B，本轮 `ls` 亲验）。⇒ **T55k 实跑用的名单不是 t31 那一串**，且**确切字符串未落进 trip 记录**（`qc151_fields.json` 无该字段）。本方案要求：**把确切字符串写进趟前回执**，否则载体组成不可复现。

### 4.2 trip 命令模板（占位符标清；**本步不发射**）

```bat
python "<LEAD>\qc151_u0400_trip\qc151_trip.py" ^
  --carrier "<OUT>\carrier_placeholder" ^
  --carrier-create-from "<LEAD>\qc161_u0400_trip\_src_variant_u0800_sf8_<YYYYMMDD>" ^
  --carrier-create-files "<84 项逗号串，含 RA2MD Update.ico>" ^
  --target-map "<LEAD>\qc161_u0400_trip\_src_variant_u0800_sf8_<YYYYMMDD>\XMP29U2.MAP" ^
  --target-sha256 "0add791d11aea84d7876aa3f908165259ec77f681ee721f83fd9966facdf60bc" ^
  --trip-id "QC161-U0800-L1" ^
  --out-dir "<LEAD>\qc161_u0400_trip\l1_u0800_<YYYYMMDD>" ^
  --measure 1 --fullscreen --evid-diff ^
  --probe-frames "3900,4200,4500,4800,5100,5400,5700,6000"
```

**逐项硬约束**：

| 项 | 说明 | 出处 |
|:--|:--|:--|
| `--carrier` 必填但被覆盖 | argparse `required=True`；`--carrier-create-from` 给出时 `--carrier` 被覆盖（值可写占位） | `:6070-6077`、`:6318-6325` |
| `--target-map` **指 `XMP29U2.MAP`** | 不是 yrm。理由 §2.1 | `:6344-6363`（只校验该文件哈希） |
| `--out-dir` 必须在批准域内 | 必须是 `LEAD\qc161_u0400_trip` 或其**后代**，且不得落在受保护子树 | `:6194-6221`、`:6206-6210` |
| `--measure 1` | 非 0 ⇒ `nav` 全绿后跑 settle 4 s + 3×25 s | `:6103-6106`、`:4066-4137` |
| `--fullscreen` | 必须给（boot-hang 修复后全屏链路；窗口模式 30 s/180 s 帽会爆）；它把 `STAGE_TIMEOUT_S→150`、`TRIP_BUDGET_S→540` | `:6128-6131`、`:6261-6263` |
| `--evid-diff` | 差异件模式；参照已存在（T55k）⇒ 本次应只落差异件 | `:6134-6138`、`evidence/_EVID_REFERENCE.json` |
| `--frozen-dump` | **本趟不给**（只在冻结时有用；给它是额外风险面） | 缺省 False |
| `--probe-frames` | **必须显式给**：缺省 `300,600,1800` 会在测窗首拍**一次性全部引爆**（T55k 实测 300/600/1800 三点全落在同一帧 f3774，`qc213_probe_final.latched=["1800","300","600"]`、快照 frame 均 3774）⇒ 无时间序列价值 | `:3051`、`:3214-3226`、`:6931-6939` |

**`--probe-frames` 怎么定**：`_qc213_tick` 每拍最多闩一个（命中即 `break`，`:3220-3224`），故阶梯**任意宽**都会在接下来几次 2.5 ms 轮询内快速追平。建议按"预期测窗起始帧 ±"给 8 点（上例 3900–6000，T55k 起始 f3774、窗末 f6244）。**这不是硬要求**：若起始帧偏离，只要阶梯点 ≤ 起始帧，就会按序补齐。

### 4.3 trip-id 命名

| 臂 | trip-id | 说明 |
|:--|:--|:--|
| L1 | `QC161-U0800-L1` | L=load 档；1=第一趟（基线主档） |
| L2 | `QC161-U0800-L2S6` | S6=GameSpeed 6（抬上限档） |
| L3 | `QC161-U0800-L3` | 上探档（sf10c） |
| 重跑 | `QC161-U0800-L1R2` | R=rerun；**不得复用旧 id**（EVID 参照/归档以 id 对账） |

沿历史命名 `QC161-U0400-T<n>` 风格，把档位段改成 `U0800`（`t55k_20261020/qc151_fields.json` META `trip_id`）。

### 4.4 out-dir 与趟后归档字段

`--out-dir <LEAD>\qc161_u0400_trip\l1_u0800_<YYYYMMDD>`（与 `t55k_20261020` 同级同风格；L2/L3 用 `l2_u0800_*`/`l3_u0800_*`）。

**趟后必须归档/抄录的字段**（缺一即视为「测量无效」，不得挑着读）：

| 组 | 字段 | 用途 |
|:--|:--|:--|
| META | `trip_id` / `started` / `finished` / `final_exit_code` / `cleanup_failures` / `fullscreen` | 趟身份与收尾 |
| TARGET | `full_path` / `actual_sha256` / `verdict` | 仅证明"被 pin 的那个文件没变"（**不是地图身份**，§2.1） |
| S4 | `modules_total` / `ra2render_hits` / `ra2loader_hits` / `hit_count` / `s4_gate` + `s4_module_table.txt` | 零注入证明 |
| MEASURE | `protocol` / `gate` / `w1_u0400_tier` / `window_{0,1,2}_stats` / `measure_forensics_w{0,1,2}` / `verdict` | 主数据 |
| MEASURE | `qc213_probe_final.latched` + 各 `p<frame>_h{0..3}_*` | h0–h3 |
| MEASURE | `qc213p2_probe_final` + `p<frame>_qc213p2_p3_shortgame_glob/sess/equal` | ShortGame 运行时证据 |
| 窗 JSON | `measure_w{0,1,2}.json` 的 `frame_edges`（原始沿表） | **离线重算 M1/M2/M3**（必须抄出来，不能只抄 stats） |
| WIN | `focus_ok`（每窗 `measure_forensics_w*`）/ `main_window_title` | 焦点/窗口 |
| CTRL1/2 | pre/post 全组 | 二进制未变 |
| RESTORE/T | `T0_T1_diff.json`、`RESTORE backup_sha256:*` | 零写 |
| EVID | `evidence/<stamp>/MANIFEST.json` + **`XMP29U2.MAP` 的 sha256** | **地图身份的第二证** |
| INI | `evidence/<stamp>/RA2MD.INI` 的 `[Skirmish]` 段（`ShortGame` / `GameSpeed` / `ScenIndex`） | 会话设置第二证 |

### 4.5 趟前必须知道的两个文件缺陷（**不改**）

1. **`ddraw.ini` 里有 3 个 0x01 控制字节**：`\x01false` 分别在第 **21 / 191 / 198** 行（本轮 `python` 逐行扫，`0x01` 计数=3）。第 21 行正是 `[ddraw]` 段里的 `windowed` 值行。**结论：不改**——T55k 全屏链路已用这份文件跑通（`F-9.fullscreen_mode=true`、`screen_wh=[2560,1440]`），动它=引入新自变量。**但必须在报告里登记**，并列为下锚窗口的手工清理候选（新开项）。
2. **`F-4` 恒假**（写死 U0400 yrm，`:4206`）与 **`scene_fixed.game_speed=2` 恒写死**（`:3941`）：L2 档（GameSpeed=6）跑完后，trip 记录仍会写 `game_speed: 2`。**这不是 bug 修复项，是读数纪律**：L2 的实际速度只能以 `evidence/<stamp>/RA2MD.INI` 为准，报告必须显式声明该字段不可信。

---

## 5. 验收矩阵

### 5.1 基线与优化臂对照表（优化臂=B，仅登记口径，不本步执行）

| 维度 | 基线臂 A（本方案） | 优化臂 B（后续） | 可比性规则 |
|:--|:--|:--|:--|
| 二进制 | `gamemd.exe 73201cc0` | 同 | 必须同 |
| DLL | **不加载**（S-4 零命中） | 经 loader 加载 `39cbd665`（`goal3_p2_build_20261020/RECEIPT_BUILD.md:32`）；需 S-4 政策例外 | 硬分离 |
| 地图 | `XMP29U2.MAP = 0add791d` | 同 | 必须同 |
| INI 设置 | `ShortGame=no`、`GameSpeed=2`、`Credits=10000`、`UnitCount=10`、`Slot01=6,8,1` | 同 | 必须同 |
| 呈现层 | cnc-ddraw `95949842`，`windowed=false`，`renderer=direct3d9`，`hook=4` | 同 | 必须同 |
| 测量协议 | `--measure 1 --fullscreen`，3×25 s，500 Hz | 同 | 必须同 |
| 判据 | **只用 M1–M8 + M10** | 同 | `fps_avg` **不作判据**（D5 第③点） |
| 对比方式 | 同条件配对：`f34 / E / p90 / p99 / max / tick_miss / max_stall` 逐窗比 | — | 不做绝对阈值，只做相对 |
| 不允许的对比 | 跨 GameSpeed、跨地图、跨 ShortGame、跨载体件集 | — | 任一跨维 = 作废 |

> **优化臂当前不可执行的硬理由**：S-4 闸门（`:1005-1020`）——`ra2loader` 命中即 `exit 62`。要跑 B 必须新增旗标（如 `--allow-loader`）并改政策；**本步不做，列新开项**（§6-U8）。

### 5.2 「测量有效」判据（V 门，全部过才读数据）

| # | 判据 | 通过线 | 证据字段 |
|:--|:--|:--|:--|
| V1 | 零注入 | `S4.hit_count==0` ∧ `s4_gate=="pass"` ∧ `modules_total` 非 null | S4 组 + `s4_module_table.txt` |
| V2 | 进图 | `NAV.verdict=="OK"` ∧ `burst` 成立 | NAV 组 |
| V3 | 三窗可测 | 每窗 `verdict=="ok"` ∧ `logic_frames>0` ∧ `n_edges≥50` ∧ `n_multi_advance` 已记 | `window_{k}_stats` |
| V4 | 负载成立 | `units0≥150`（脚本门）**且** `units0≥800`（本方案设计门，针对 U0800 档） | `gate.units0` |
| V5 | 四屋建制完整 | 起点快照 `meta_count==4`；h0 `isHuman1EC==1`；h1 `id30==1`；h0/h1 `def1F5==0`；h2/h3 `c5574>0` | `p<frame>_h*_*` |
| V6 | 会话 ShortGame=no | `p3_shortgame_glob==0` ∧ `p3_equal==true`；且 evidence INI `ShortGame=no` | P3 字段 + `evidence/…/RA2MD.INI` |
| V7 | 零写/无新异常 | `T0_T1_diff.json` `diff_count==0`；`new_exception_count==0`；CTRL1/2 post PASS | T/RESTORE/EXCEPT/CTRL |
| V8 | 焦点与轮询健康 | 三窗 `focus_ok==true`；`hz_effective≥480` | `measure_forensics_w*` / `stats` |
| V9 | **地图身份** | evidence `XMP29U2.MAP` sha == `0add791d…60bc` **且** 起点 h2 与 h3 的 `c5574` 均 ≥ 200（U0800 档 240/屋；U0400 档只有 120/屋 ⇒ 该判据有区分力） | MANIFEST + 探针 |
| V10 | 速度身份（仅 L2） | evidence INI `[Skirmish] GameSpeed==6` | 同上 |

**V9 是本次新增、且是唯一能挡"测错图"的门。** T55k 的 `TARGET.verdict=PASS` 在 V9 面前毫无信息量（§2.1）。

### 5.3 「卡顿复现」判据（R 门，按强度分层；**不与 V 门混用**）

| # | 判据 | 强度 | 说明 |
|:--|:--|:--|:--|
| R0 | 三窗 `fps_avg` 仍 ≥30 且 `f34 < 30%` 且 `E≈0` | **未复现（贴帽）** | 与 T50/T55k 同族 |
| R1 | `f34 ≥ 30%` 或 `p90 > 40 ms`（≥2 窗） | **浅越加剧** | T50=24.96%、T55e p90=54.8 ⇒ 有历史锚 |
| R2 | `p99 > 60 ms` 或 `max > 100 ms` 或 `tick_miss > 0`（≥2 窗） | **深越/尖峰** | T50 W0 max=110.7/5 miss |
| R3 | 任一窗 `max_stall > 1 s` 或 `logic_frames < 0.8×` 中位 | **停顿** | 必须过 D4 排除终局 |
| R4 | `fps_avg < 25`（明显破帽） | **破帽复现** | T55f p50=15.7 量级 |
| R5 | 窗口内某屋 `def1F5` 翻转 / 记分板帧 | **无效窗（非卡顿）** | 见 D4 |

### 5.4 判读纪律（防误判四条）

| # | 纪律 | 为什么 |
|:--|:--|:--|
| D1 | **不得用 `TARGET.verdict` / `F-4` / `F-5` 论证载图身份**；只认 V9 | §2.1：pin 只校验文件本身；F-4 写死 U0400 |
| D2 | **不得用 `fps_avg` 判优劣** | D5 第③点；41 单位与 842 单位同值 31.24 |
| D3 | **不得跨 GameSpeed 比 `frame_ms`** | 上限不同 ⇒ 分母不同 |
| D4 | **停顿先排除终局**：`max_stall>1 s` 时必须同帧看 `h*_def1F5` 与 `measure_w{k}_end_x.png`；有翻转/记分板 ⇒ 记"终局伪影"，不记卡顿 | T55h 冻结 373、T55e 378、T55f 380 全是终局（§190/§192） |
| D5 | **单帧 max 只报"观测值"**，不报分位；p99.9 不报 | 782 帧样本，p99.9 不足 1 帧 |

### 5.5 失败回退梯

| 失败 | 判据 | 回退 |
|:--|:--|:--|
| F0 载体建不起来 / sha 不符 | `--target-sha256` ≠ 实际 | 停，不改图，重建源变体（**不得**在旧变体上就地改） |
| F1 `units0 < 800` | V4 不过 | 记"U0800 档不成立"；**不**改用 yrm 目标；回查 `XMP29U2.MAP` sha 与载体件集 |
| F2 某屋开局即败（`def1F5=1`） | V5 不过 | 该趟只作"签名证据"；回 L1 重掷一次；二连败 ⇒ 报 Lead（可能回到 raw U0800/换图，属新开项） |
| F3 三窗有空窗/冻结 | V3 不过 | 该趟无效；若 `frozen_dump` 未开 ⇒ 下趟考虑开（**仅此一处**允许加旗标） |
| F4 焦点丢失 / `hz_effective<480` | V8 不过 | 该趟无效；重跑一次；连续两次 ⇒ 停（环境问题） |
| F5 破帽失败（R0） | — | **不是失败**，是"该负载不破帽"的结论；然后掷 L2（抬上限）；L2 若也未破 ⇒ 掷 L3（加负载） |

---

## 6. 未知与需 Lead 决策

| # | 事项 | 本轮能确定到哪一步 | 需决策什么 |
|:--|:--|:--|:--|
| **U1** | 「真原版臂」可行性 | **已定**：现有 trip 就是原版直启（S-4 实证零注入、`gamemd.exe` 无 `ra2render` 字符串）。**但**"原版"含 cnc-ddraw 包装器 | **是否接受"原版二进制 + cnc-ddraw"为 ① 基线口径？** 若不接受，则需一条不经 cnc-ddraw 的呈现路径（未验证；boot hang 的根因正是 cnc-ddraw `windowed=true` 呈现路径自旋，见 `GOAL_THREE_TARGETS_20261018.md:127` §163） |
| **U2** | U0800 实际 units | **只有单点**：T50=971（sf8）。且 **T50 的 measure JSON / archive 不在盘上**（本轮 `find` 只找到 `archive_T32..T49` + 根目录 T55j + `t55k_20261020`）⇒ 971 只有日志/卡面级证据（`GOAL…:94`、`cards/QC161.md:748`） | **是否接受"971（单点、无原始沿表）"作为参考点？** 本方案的态度：只当"预期量级"，不作判据；判据用 `units0≥800` |
| **U3** | `[Skirmish] GameSpeed` 是否作用于会话 | **不确定，且现有证据偏「不读」**。源变体 `[Skirmish] GameSpeed=2`（`_src_variant_800x600_csf/RA2MD.INI:22`），但收尾写回：T55e=`1`（`evidence/20261019T180440325218/RA2MD.INI:18`）、T55j=`1`（`evidence/20261019T223927830914/RA2MD.INI` 同位置）、T55k=`2`（`t55k_20261020/evidence/20261020T092208043279/RA2MD.INI:22`）——**同一源值三种写回** ⇒ INI 更像 UI 态的持久化产物而非输入 | **L2 档是否值得花一趟？** 若 GameSpeed 只读 UI，则 INI 改 6 无效，需新旗标去拖滑杆（新开项）。**建议先做一次零成本判别**：见 §7-C7 |
| **U4** | `GameSpeed=6` 对逻辑/物理的影响 | 未验证。已知 `1000/[0xA8B558]` 门的是 `LogicUpdate`（`clock_frame_loop.md:244`），`CurrentFrame++` 在它之前（`:240`）——两者耦合关系未逐指令闭合 | 换速度会**同时**改变世界更新频率（每秒 2× 模拟步）⇒ 玩法与终局时点都会变。**是否允许"抬速度"作为解上限手段？**（代价=与 Speed2 数据不可直接比） |
| **U5** | 是否需要"帧体耗时累计"探针（M9） | 地址已字节复核（`0xA8B560/0xA8B564`，清零点 `0x6477ED`–`0x6477F8`）；**但它不含世界更新段** | 若要一个真正"每帧逻辑耗时"的主指标，需**新探针 + 新旗标 + 核验**（新开项）。**当前方案不依赖它** |
| **U6** | 开局段永远测不到 | `frame` 阶段就要 126 s（T55k BUDGET），测窗从 f3774 起 | **是否要"更早开窗"的新旗标？**（会改 nav→measure 时序，是新开项）。本方案默认不追，如实登记"只测稳态" |
| **U7** | 新变体里其余 yrm 留不留 | 载图是 `XMP29U2.MAP`（§2.1），yrm 惰性 | 建议**保留 U0400.yrm 一行不动**以复刻 T55k 组成；若 Lead 认为要"消歧"，则删其余 yrm（会改变载体件数与 EVID 参照命中） |
| **U8** | 优化臂需要的新旗标 | `--allow-loader`（S-4 政策例外）+ 实际 GameSpeed 记录 + 帧体探针 | **明确标为新开项**：不在本步、不在本方案、不得随本方案"顺手加" |
| **U9** | `ddraw.ini` 的 3 个 `0x01` 字节 | 已定位（21/191/198 行）；当前配置实测可跑通 | 是否在本方案之外单开清理项（清理后需重验 boot）。**建议：不碰** |

---

## 7. 发射前检查清单（**一页，逐项打勾并填实测值**）

> 规则：**任何一项没有实测值 = 不发射**。禁止"看起来没问题"。

### A. 离线预检（不启动游戏，命令可复跑）

| # | 检查 | 命令 | 期望 | 实测值（填写） |
|:--|:--|:--|:--|:--|
| A1 | 母本二进制未变 | `sha256sum "<变体>\gamemd.exe"` | `73201cc0…f67476` / 4,825,360 B | |
| A2 | 图哈希 | `sha256sum "<变体>\XMP29U2.MAP"` | `0add791d11aea84d7876aa3f908165259ec77f681ee721f83fd9966facdf60bc` / 311,822 B | |
| A3 | 图内 owner 分布 | `python §8-A3 脚本` | `[Units]` 3360（h0/Computer 各 240 车行）/ `[Infantry]` 2240（各 160） | |
| A4 | 无 Structures 节 | `python §8-A3 脚本` | 27 节，无 `Structures` | |
| A5 | INI 设置 | 读 `<变体>\RA2MD.INI` | `[Skirmish] ShortGame=no` / `GameSpeed=2`（L2=6）/ `ScenIndex` 存在 | |
| A6 | 呈现层常量 | `sha256sum` 三件 | `ddraw.ini=95949842…`（若 §4.5 缺陷未清理）/ `ddraw.dll=85e0f7d5…` / `ra2render.dll=39cbd665…`（在位、不加载） | |
| A7 | `windowed=false` 生效行 | 读 `ddraw.ini` 第 1 行与第 21 行 | 第 1 行 `windowed=false`；第 21 行 `\x01false`（**已知缺陷，不改**） | |
| A8 | 残留进程 | `tasklist \| findstr /i "gamemd ra2loader YURI"` | 0 行 | |
| A9 | 载体目录干净 | `dir "<OUT>\ct"` | 空/无旧 `c_*` | |
| A10 | 磁盘余量 | `dir D:\` | ≥ 5 GB（EVID 差异件远小于 1.8 GB，但留余量） | |
| A11 | 锚哈希 | `sha256sum qc151_trip.py` | 现锚 `517889c6…`（本次设计读数；**发射时以卡面为准复验**，不一致先停） | |
| A12 | `--carrier-create-files` 字符串已落回执 | 人 | 与 §4.1-P7 一致，含空格项整体引号；**字符串已抄进本回执** | |

### B. 命令装配核对（表内编号 装1–装8）

| # | 检查 | 期望 |
|:--|:--|:--|
| 装1 | `--target-map` 指 **`XMP29U2.MAP`** | 不是任何 `.yrm` |
| 装2 | `--target-sha256` = `0add791d…60bc` | 与 A2 同值 |
| 装3 | `--trip-id` 符合 §4.3 | `QC161-U0800-L1` |
| 装4 | `--out-dir` 是 `lead\qc161_u0400_trip` 后代 | 否则落默认域/警告 |
| 装5 | 含 `--measure 1 --fullscreen --evid-diff` | 三件 |
| 装6 | **不含** `--frozen-dump` | 本趟不需要 |
| 装7 | 含 `--probe-frames` 且 ≥6 点、均 > 预期起始帧的一半 | 例 `3900,4200,4500,4800,5100,5400,5700,6000` |
| 装8 | 同刻只有一个真机趟（串行） | 无并发 trip |

### C. 趟中/趟后即时核对

| # | 检查 | 期望 | 失败即 |
|:--|:--|:--|:--|
| C1 | `S4.hit_count==0` | 0；模块表落盘 | V1 失败 ⇒ 本趟作废 |
| C2 | `NAV.verdict=="OK"` | OK | V2 失败 ⇒ 记 INCOMPLETE |
| C3 | `MEASURE.verdict=="ok"` 且三窗全 `logic_frames>0` | 三窗 | V3 失败 ⇒ 无效 |
| C4 | `gate.units0 ≥ 800` | ≥800 | V4 失败 ⇒ 回 F1 |
| C5 | 起点 `meta_count=4`、h0/h1 `def1F5=0` | 是 | V5 失败 ⇒ 回 F2 |
| C6 | `p3_shortgame_glob=0 ∧ p3_equal=true` | 是 | V6 失败 ⇒ 无效 |
| C7 | **速度判别（L2 前置）**：evidence INI 的 `GameSpeed` 是否 = 源值 | 若 = 1/2（非 6）⇒ **GameSpeed 不读 INI** ⇒ 停 L2，报 Lead | U3 定谳 |
| C8 | evidence `XMP29U2.MAP` sha == A2 | 相等 | V9 失败 ⇒ 测错图，作废 |
| C9 | `T0_T1_diff.diff_count==0`、`new_exception_count==0` | 0/0 | V7 失败 ⇒ 作废 |
| C10 | 三窗 `focus_ok==true`、`hz_effective≥480` | 是 | V8 失败 ⇒ 重跑 |
| C11 | 抄出 `measure_w{0,1,2}.json` 的 `frame_edges` 与 `counters` | 3 份原件 | 缺 ⇒ 无法算 M2/M3 |
| C12 | 载体已删、`ct` 清零、无残留进程 | 是 | 卫生失败 |

### D. 趟后判读（先 V 门，后 R 门）

| # | 检查 | 期望 |
|:--|:--|:--|
| D1 | V1–V10 全过 | 任一不过 ⇒ **本趟不进 R 门判读** |
| D2 | 用 `frame_edges` 重算 `CAP=p50`、`f34`、`E`、`p90/p99/max` | 与 `stats` 交叉一致（不直接用 stats 抄结论） |
| D3 | 判 R 层（R0–R4） | 按 §5.3 |
| D4 | 任何 `max_stall>1 s` 先查 `def1F5`/`_end_x.png` | 终局伪影不得记卡顿 |
| D5 | 报告首行写清：**原版二进制 + cnc-ddraw；零注入；只测稳态 75 s；`fps_avg` 非判据；`TARGET/F-4/scene_fixed.game_speed` 不可信** | 五条缺一不可 |

---

## 8. 附录：本件引用的自算脚本（离线、只读）

### A3 地图解析（本轮实际执行过；只读）

```python
import re, collections
def sect(txt, name):
    m = re.search(r'^\[' + re.escape(name) + r'\]\s*$', txt, re.M)
    if not m: return ''
    seg = txt[m.end():]
    m2 = re.search(r'^\[', seg, re.M)
    return seg[:m2.start()] if m2 else seg
t = open(r'<path>\XMP29U2.MAP', 'rb').read().decode('latin-1')
print([m.group(1) for m in re.finditer(r'^\[([^\]]+)\]', t, re.M)])
for n in ('Units', 'Infantry'):
    rows = [l for l in sect(t, n).splitlines() if l.strip()]
    print(n, len(rows),
          collections.Counter(r.split('=', 1)[1].split(',')[0] for r in rows))
```

### A4 越帽量离线重算（趟后对 `measure_w{k}.json` 跑）

```python
import json
d = json.load(open(r'<out>\measure_w0.json', encoding='utf-8'))
fe = d['frame_edges']
ms = [(b[1] - a[1]) * 1000 for a, b in zip(fe, fe[1:]) if b[0] - a[0] == 1]
cap = d['stats']['frame_ms_p50']          # 同趟帽参考，不跨趟套
n = len(ms)
f34 = 100.0 * sum(v > 34 for v in ms) / n
E = sum(max(0.0, v - cap) for v in ms) / n
print(n, 'cap', cap, 'f34', round(f34, 2), 'E(ms/frame)', round(E, 3))
```

> 本轮对 T55k w0/w1/w2 实跑该式得：`f34 = 28.17 / 24.81 / 24.71 %`（w0 用 34 ms；w0 `>32.24` 占 50.06%）。

---

## 9. 本件**不能**证明什么（诚实边界）

1. **本件未发射任何 trip**：`units0≈971` 是 T50 的单点历史值，**本轮没有复测**；U0800 在 sf8 下的实际 units 仍属 `[待实测]`。
2. **本件未验证** `GameSpeed=6` 能否抬上限（U3），也未验证 `[0xA8B558]/0x887330` 与 `CurrentFrame` 频率的因果链（只证明了字节与文档口径一致）。
3. **本件未验证** M9（帧体耗时累计）在真机的可读性——`0xA8B560/0xA8B564` 的字节与清零点成立，但**从未被任何探针读取**。
4. **本件未解决**"优化臂怎么跑"：S-4 政策例外是前置，本件只把它标成新开项。
5. **本件未复核** `F-6/F-7` 的帧分类（qc95 词表对"记分板"帧的归类不在本件范围）。
6. **本件的所有"预期"值（971 / p90 35–37 / f34≈25%）都是历史单点**，不得当作本次趟的通过线；通过线是 V 门（§5.2）。
