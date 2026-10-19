# 配置键名 / 默认值 单一口径对照表（PK-3 · T-W1-Q）
# Config Key Matrix — the single authoritative cross-reference

> **文档标识**：`docs/re/config_key_matrix.md`
> **工单**：T-W1-Q / **PK-3（键名/默认值口径统一包）**
> **编制日期**：2026-10-01 · **性质**：只读横切对照表（**不改** `ra2render/**`、**不改**任何既有 `docs/re/**` 正文）
> **配套机读件**：`out/re_work/static_prep/keys/keys_matrix.json`、`keys_matrix.csv`、`gen_key_matrix.py`、`verify_run.txt`
> **本文所有 `路径:行号` 均由 `gen_key_matrix.py` 从 `ra2render/ra2render.ini` + `ra2render/blitter_hooks.cpp` + 两游戏目录 ini **机械复算**得到**，非人工誊写；重跑 `python out/re_work/static_prep/keys/gen_key_matrix.py` 即可复核（9 条断言，退出码 0）。

---

## 0. 为什么需要这张表

`docs/re/pending_execution_master_table.md` §3.1（`:391-441`）给出六大落地补丁的 INI 声明，§一 总表（`:39-56`）给出每行 INI 门控，`:450-463` 给出联机强制覆盖表；但**实现面**（`ra2render/blitter_hooks.cpp` + `ra2render/ra2render.ini`）与它并不同名。执行方若按 §3.1 **字面**写 ini：

* 写 `[Render] L4DirtyMode` ⇒ 代码读的是 `[FogOfWar] L4DirtyMode`（`blitter_hooks.cpp:757`）⇒ **键永远读不到**，静默回落默认值；
> 【W3 勘误 · W3-A6/ISSUE-SECTION-L4DIRTYMODE】改前：[Render] L4DirtyMode；改后：[FogOfWar] L4DirtyMode=force-full；依据：ra2render/blitter_hooks.cpp:757; ra2render/ra2render.ini:251；分级：P0
* 写 `[FogOfWar] EnableGapProtection=1` 于游戏目录 ⇒ 该目录 ini **根本没有这个键**（`ra2youli/ra2render.ini`、`ra2bench/ra2render.ini` 各 20 键，均缺）⇒ 代码默认 `0`（`:606`）生效 ⇒ **补丁不装**，而总表 `:44` 的遥测契约要求 `installed==3`；
> 【W3 勘误 · W3-A6/ISSUE-DEFAULT-GAPPROTECTION】改前：EnableGapProtection=1；改后：EnableGapProtection=0  ; [代码/出厂默认0，安全侧；测试或启用时显式置1]；依据：ra2render/blitter_hooks.cpp:606; ra2render/ra2render.ini:199; config_key_matrix.md:109；分级：P0
* 写 `[Audio] EnableAudioThrottling=1` ⇒ 代码侧 0 命中，且音频落地卡用的是**另一套** `[AudioThrottle]` 8 键（`docs/re/audio_throttle_landing.md:19`）⇒ 「补丁静默不装」。
> 【W3 勘误 · W3-A6/ISSUE-SECTION-AUDIO】[W3-Lead临时裁决] 改前：[Audio] EnableAudioThrottling；改后：[AudioThrottle] ; DC-02 裁决口径: 8 键体系，宿主 ra2render.ini Enable=0 MaxVoicePerFrame=6 VoiceDedupMs=80；依据：docs/re/dispatch/W3_20261001_Lead_DECISION_AND_BOARD.md:41; docs/re/audio_throttle_landing.md:19, 139-147；分级：P0

本表把 **14 个主键 + 7 个 MP/裁决键** 逐一钉到「具体读取代码行」或「**未落地-待新建** + 定义它的卡面路径」，并登记全部口径分歧。

---

## 1. 口径裁决原则（本表用什么判「谁对」）

| 原则 | 内容 | 依据 |
|---|---|---|
| **P-唯一实现口径** | 「节名 + 键名 + 读取方式」以 `ra2render/blitter_hooks.cpp` 的 `GetIni*` 调用为**唯一真源**；文档与代码冲突时**改文档**，不改代码（`ra2render/**` 为 `ra2render` 团队独占写域，本工单只读） | 工单写域约束；`blitter_hooks.cpp:352-372` 统一读取器 |
| **P-默认值安全侧** | 「默认值」以**代码默认 ∩ 出厂 ini** 为口径；总表若写更激进默认（如 `EnableGapProtection=1`）视为**规格待落地意图**，不得当作现网事实 | `blitter_hooks.cpp:606`（0）vs `master_table:401`（1） |
| **P-缺键即默认** | 键在某 ini 中不存在 ⇒ 该行明确记「缺失 ⇒ 走代码默认」，不留空、不假设继承 | `GetIniIntEx` 哨兵机制 `blitter_hooks.cpp:350-370` |
| **P-同名节只读第一个** | `GetPrivateProfileStringA` 遇重复节名只读首节 ⇒ 本表断言 (i) 强制「一键不多节 / 同节不重名」 | `blitter_hooks.cpp:344-348` 注释 + `[RADAR-FIX F3]` 事故 |
| **P-单位显式** | 帧 vs 毫秒不得混写；`30 fps` 换算须注 | `master_table:419` vs `audio_throttle_landing.md:147` |

---

## 2. 代码侧读取器与 MP 判定锚点（实测）

| 项 | 位置 | 说明 |
|---|---|---|
| 字符串读 + 「键缺失」哨兵 | `ra2render/blitter_hooks.cpp:352-362`（哨兵串 `:350`） | 命中返回 `true`；缺失回落 API 默认 |
| 整数读 | `ra2render/blitter_hooks.cpp:364-370` | `!hit \|\| 空串 ⇒ def`，否则 `atoi` |
| 来源标注 | `ra2render/blitter_hooks.cpp:372` `IniSrc()` | 日志区分 `ini` / `默认值`（防「误读为已配置生效」） |
| `LoadConfig()` 入口 | `ra2render/blitter_hooks.cpp:518`，由 `:3644` 在 init 调用 | 出厂 ini 路径 = `GetCurrentDirectoryA + "\ra2render.ini"`（`:520-521`）⇒ **游戏目录 ini 才是运行期真身** |
| ini 路径拼接 | `ra2render/blitter_hooks.cpp:520-521` | 同上 |
| `MpActive()` | `ra2render/blitter_hooks.cpp:212-231` | 主判定 `*(uint8_t*)0x00A8D5F8 & 0x02`（`ra2render.h:153`），辅判定 `*(int32_t*)0x00AA0444 == 2`（`ra2render.h:154`）；`__try/__except` 兜底 false（`:227-229`） |
| `GetEffectiveTargetScanInterval()` | `ra2render/blitter_hooks.cpp:233-238` | MpActive ⇒ 恒 `1` |
| `GetEffectiveTargetScanKey()` | `ra2render/blitter_hooks.cpp:240-245` | MpActive ⇒ 恒 `1`(=position) |
| `GetEffectiveMinimapFog()` | `ra2render/blitter_hooks.cpp:257-267` | MpActive ⇒ 恒 `false`，并镜像 `s_minimapFogGate` |
| `GetEffectiveRadarFogGuardMode()` | `ra2render/blitter_hooks.cpp:249-255` | 越界收敛 `3` |
| `CheckMpGateTransition()` | `ra2render/blitter_hooks.cpp:314-341` | 运行期 MP 态迁移重判 + 红字告警（`:327`、`:338`），调用点 `:847`、`:1551` |
| MP 门控汇总日志 | `ra2render/blitter_hooks.cpp:801`（另有 MP 生效行 `:818`） | 打印 配置值 → 生效值 |
| 头文件 extern | `ra2render/ra2render.h:436-439`（+ `CheckMpGateTransition` `:440`） | `MpActive` / 三个 `GetEffective*` |

> **注意**：总表 §3.1 的 5 个键（`SyncDiag` 4 键、`Audio` 3 键、`System` 2 键、`EnableParticleFog`、`EnableSpySatGate`）与 §3.1 尾部的 `EnableThreatRetention`/`MpStateWrites`/`MpAutoDowngrade`/`ForceSinglePlayer` 在 `blitter_hooks.cpp` 中 **grep 0 命中**；`[SyncDiag]`、`[Audio]`、`[Multiplayer]` 三节在两 ini 与代码中**均不存在**（出厂 ini 仅 5 节：`[Render] [Logic] [Speed] [System] [FogOfWar]`）。

---

## 3. 表 A —— 六包 14 个主键（五列口径，逐格带 `路径:行号`）

| ① 规格节名+键名（含包号与出处） | ② 代码实际节名+键名+读取行号 | ③ 代码默认值 | ④ ini 出厂值（源码目录 / `ra2youli` / `ra2bench`） | ⑤ MP 覆盖规则 + 实现行号 |
|---|---|---|---|---|
<!-- BEGIN A -->
| **P-1** `SyncDiag`.`SyncEarlyLog` = `0`<br>`docs/re/pending_execution_master_table.md:394` | **未落地-待新建**：`ra2render/blitter_hooks.cpp` grep `SyncEarlyLog` 0 命中 ｜ 定义面：`docs/re/landing_pack_net_fix.md:218` | — 无读取点 ⇒ 无代码默认值 | `ra2render/ra2render.ini` **无此键** ⇒ 走代码默认<br>`ra2youli/ra2render.ini` **无此键** ⇒ 走代码默认<br>`ra2bench/ra2render.ini` **无此键** ⇒ 走代码默认 | 规格声明的 MP 覆盖（未落地，代码侧无实现） ｜ `未落地-待新建（0 命中：ra2render/blitter_hooks.cpp）` |
| **P-1** `SyncDiag`.`SyncSnapshotOnDesync` = `0`<br>`docs/re/pending_execution_master_table.md:395` | **未落地-待新建**：`ra2render/blitter_hooks.cpp` grep `SyncSnapshotOnDesync` 0 命中 ｜ 定义面：`docs/re/landing_pack_net_fix.md:338` | — 无读取点 ⇒ 无代码默认值 | `ra2render/ra2render.ini` **无此键** ⇒ 走代码默认<br>`ra2youli/ra2render.ini` **无此键** ⇒ 走代码默认<br>`ra2bench/ra2render.ini` **无此键** ⇒ 走代码默认 | 规格声明的 MP 覆盖（未落地，代码侧无实现） ｜ `未落地-待新建（0 命中：ra2render/blitter_hooks.cpp）` |
| **P-1** `SyncDiag`.`SyncMirror` = `0`<br>`docs/re/pending_execution_master_table.md:396` | **未落地-待新建**：`ra2render/blitter_hooks.cpp` grep `SyncMirror` 0 命中 ｜ 定义面：`docs/re/landing_pack_net_fix.md:431` | — 无读取点 ⇒ 无代码默认值 | `ra2render/ra2render.ini` **无此键** ⇒ 走代码默认<br>`ra2youli/ra2render.ini` **无此键** ⇒ 走代码默认<br>`ra2bench/ra2render.ini` **无此键** ⇒ 走代码默认 | 规格声明的 MP 覆盖（未落地，代码侧无实现） ｜ `未落地-待新建（0 命中：ra2render/blitter_hooks.cpp）` |
| **P-1** `SyncDiag`.`SyncCmdMirror` = `0`<br>`docs/re/pending_execution_master_table.md:397` | **未落地-待新建**：`ra2render/blitter_hooks.cpp` grep `SyncCmdMirror` 0 命中 ｜ 定义面：`docs/re/landing_pack_net_fix.md:563` | — 无读取点 ⇒ 无代码默认值 | `ra2render/ra2render.ini` **无此键** ⇒ 走代码默认<br>`ra2youli/ra2render.ini` **无此键** ⇒ 走代码默认<br>`ra2bench/ra2render.ini` **无此键** ⇒ 走代码默认 | 规格声明的 MP 覆盖（未落地，代码侧无实现） ｜ `未落地-待新建（0 命中：ra2render/blitter_hooks.cpp）` |
| **P-2** `FogOfWar`.`EnableGapProtection` = `1`<br>`docs/re/pending_execution_master_table.md:401` | `[FogOfWar] EnableGapProtection` @ `ra2render/blitter_hooks.cpp:606`（`GetIniIntEx`） | `0` | `ra2render/ra2render.ini:199` `0`<br>`ra2youli/ra2render.ini` **无此键** ⇒ 走代码默认<br>`ra2bench/ra2render.ini` **无此键** ⇒ 走代码默认 | MpActive() -> refuse install (forced-off-mp) ｜ `ra2render/blitter_hooks.cpp:3321-3322` ｜ `spec-side ra2render/blitter_hooks.cpp:610` |
| **P-2** `FogOfWar`.`EnableSpySatGate` = `1`<br>`docs/re/pending_execution_master_table.md:402` | **未落地-待新建**：`ra2render/blitter_hooks.cpp` grep `EnableSpySatGate` 0 命中 ｜ 定义面：`docs/re/landing_pack_gap_spysat.md:35,157-159` | — 无读取点 ⇒ 无代码默认值 | `ra2render/ra2render.ini` **无此键** ⇒ 走代码默认<br>`ra2youli/ra2render.ini` **无此键** ⇒ 走代码默认<br>`ra2bench/ra2render.ini` **无此键** ⇒ 走代码默认 | 规格声明的 MP 覆盖（未落地，代码侧无实现） ｜ `未落地-待新建（0 命中：ra2render/blitter_hooks.cpp）` |
| **P-2** `FogOfWar`.`EnableSpySatRadarSweep` = `1`<br>`docs/re/pending_execution_master_table.md:403` | `[FogOfWar] EnableSpySatRadarSweep` @ `ra2render/blitter_hooks.cpp:550`（`GetIniIntEx`） | `1` | `ra2render/ra2render.ini:120` `1`<br>`ra2youli/ra2render.ini:89` `1`<br>`ra2bench/ra2render.ini:89` `1` | indirect only: UpdateVisionGrid/PatchSpySatBuildingTypes bypass per W3/W4/W5 ｜ `docs/re/mp_autodowngrade_spec.md:278` ｜ `no ini-level MP branch in code` |
| **P-3** `FogOfWar`.`EnableParticleFog` = `0`<br>`docs/re/pending_execution_master_table.md:406` | **未落地-待新建**：`ra2render/blitter_hooks.cpp` grep `EnableParticleFog` 0 命中 ｜ 定义面：`docs/re/landing_pack_particle_fog.md:82 / docs/re/particle_fog_owner_landing.md:92 / docs/re/landing_pack_crt_audio_particle.md:431` | — 无读取点 ⇒ 无代码默认值 | `ra2render/ra2render.ini` **无此键** ⇒ 走代码默认<br>`ra2youli/ra2render.ini` **无此键** ⇒ 走代码默认<br>`ra2bench/ra2render.ini` **无此键** ⇒ 走代码默认 | 规格声明的 MP 覆盖（未落地，代码侧无实现） ｜ `未落地-待新建（0 命中：ra2render/blitter_hooks.cpp）` |
| **P-4** `System`.`EnableMemoryPool` = `0`<br>`docs/re/pending_execution_master_table.md:412` | **未落地-待新建**：`ra2render/blitter_hooks.cpp` grep `EnableMemoryPool` 0 命中 ｜ 定义面：`docs/re/landing_pack_crt_audio_particle.md:154-155（[System]，F-02 订正默认 0） vs docs/re/crt_pool_landing.md:19（[MemoryPool]）` | — 无读取点 ⇒ 无代码默认值 | `ra2render/ra2render.ini` **无此键** ⇒ 走代码默认<br>`ra2youli/ra2render.ini` **无此键** ⇒ 走代码默认<br>`ra2bench/ra2render.ini` **无此键** ⇒ 走代码默认 | 规格声明的 MP 覆盖（未落地，代码侧无实现） ｜ `未落地-待新建（0 命中：ra2render/blitter_hooks.cpp）` |
| **P-4** `System`.`PoolBlockCount` = `4096`<br>`docs/re/pending_execution_master_table.md:413` | **未落地-待新建**：`ra2render/blitter_hooks.cpp` grep `PoolBlockCount` 0 命中 ｜ 定义面：`无卡面定义 ⇒ 未闭环：crt_pool_landing.md 与 landing_pack_crt_audio_particle.md 全文 grep PoolBlockCount / BlockCount / 4096 均 0 命中（语义未定：每桶块数 or 总块数）` | — 无读取点 ⇒ 无代码默认值 | `ra2render/ra2render.ini` **无此键** ⇒ 走代码默认<br>`ra2youli/ra2render.ini` **无此键** ⇒ 走代码默认<br>`ra2bench/ra2render.ini` **无此键** ⇒ 走代码默认 | 规格声明的 MP 覆盖（未落地，代码侧无实现） ｜ `未落地-待新建（0 命中：ra2render/blitter_hooks.cpp）` |
| **P-5** `Audio`.`EnableAudioThrottling` = `1`<br>`docs/re/pending_execution_master_table.md:417` | **未落地-待新建**：`ra2render/blitter_hooks.cpp` grep `EnableAudioThrottling` 0 命中 ｜ 定义面：`docs/re/audio_throttle_landing.md:19,139-141（[AudioThrottle] Enable=0） vs docs/re/landing_pack_crt_audio_particle.md:287（[Audio] =1）` | — 无读取点 ⇒ 无代码默认值 | `ra2render/ra2render.ini` **无此键** ⇒ 走代码默认<br>`ra2youli/ra2render.ini` **无此键** ⇒ 走代码默认<br>`ra2bench/ra2render.ini` **无此键** ⇒ 走代码默认 | 规格声明的 MP 覆盖（未落地，代码侧无实现） ｜ `未落地-待新建（0 命中：ra2render/blitter_hooks.cpp）` |
| **P-5** `Audio`.`MaxSoundsPerFrame` = `4`<br>`docs/re/pending_execution_master_table.md:418` | **未落地-待新建**：`ra2render/blitter_hooks.cpp` grep `MaxSoundsPerFrame` 0 命中 ｜ 定义面：`docs/re/audio_throttle_landing.md:19,144（[AudioThrottle] MaxVoicePerFrame=6） vs docs/re/landing_pack_crt_audio_particle.md:287（[Audio] =4）` | — 无读取点 ⇒ 无代码默认值 | `ra2render/ra2render.ini` **无此键** ⇒ 走代码默认<br>`ra2youli/ra2render.ini` **无此键** ⇒ 走代码默认<br>`ra2bench/ra2render.ini` **无此键** ⇒ 走代码默认 | 规格声明的 MP 覆盖（未落地，代码侧无实现） ｜ `未落地-待新建（0 命中：ra2render/blitter_hooks.cpp）` |
| **P-5** `Audio`.`SoundMinIntervalFrames` = `2`<br>`docs/re/pending_execution_master_table.md:419` | **未落地-待新建**：`ra2render/blitter_hooks.cpp` grep `SoundMinIntervalFrames` 0 命中 ｜ 定义面：`docs/re/audio_throttle_landing.md:19,147（[AudioThrottle] VoiceDedupMs=80 **毫秒**） vs docs/re/landing_pack_crt_audio_particle.md:287（[Audio] =2 **帧**）` | — 无读取点 ⇒ 无代码默认值 | `ra2render/ra2render.ini` **无此键** ⇒ 走代码默认<br>`ra2youli/ra2render.ini` **无此键** ⇒ 走代码默认<br>`ra2bench/ra2render.ini` **无此键** ⇒ 走代码默认 | 规格声明的 MP 覆盖（未落地，代码侧无实现） ｜ `未落地-待新建（0 命中：ra2render/blitter_hooks.cpp）` |
| **P-6** `Render`.`L4DirtyMode` = `force-full`<br>`docs/re/pending_execution_master_table.md:423` | `[FogOfWar] L4DirtyMode` @ `ra2render/blitter_hooks.cpp:757`（`GetIniStringEx`） | `force-full` | `ra2render/ra2render.ini:251` `force-full`<br>`ra2youli/ra2render.ini:186` `force-full`<br>`ra2bench/ra2render.ini:186` `force-full` | none -- listed in the MP gate log but not overridden ｜ `ra2render/blitter_hooks.cpp:818` ｜ `spec-side docs/re/pending_execution_master_table.md:457 (independent per-client)` |
<!-- END A -->

**表 A 落地度小结**：14 键中 **3 键已在代码有具体读点**（`EnableGapProtection:606`、`EnableSpySatRadarSweep:550`、`L4DirtyMode:757`）；**11 键 = 未落地-待新建**（P-1 全 4 键、P-2 的 `EnableSpySatGate`、P-3 全 1 键、P-4 全 2 键、P-5 全 3 键）。⇒ **P-1/P-3/P-4/P-5 四包当前无任何键读取路径**，写 ini 无效。

---

## 4. 表 B —— 7 个 MP / 裁决键

| ① 规格节名+键名（含出处） | ② 代码实际节名+键名+读取行号 | ③ 代码默认值 | ④ ini 出厂值（三处） | ⑤ MP 覆盖规则 + 实现行号 |
|---|---|---|---|---|
<!-- BEGIN B -->
| **MP** `Logic`.`TargetScanKey` = `position`<br>`docs/re/pending_execution_master_table.md:428` | `[Logic] TargetScanKey` @ `ra2render/blitter_hooks.cpp:561`（`GetIniStringEx`） | `position` | `ra2render/ra2render.ini:31` `position`<br>`ra2youli/ra2render.ini:15` `position`<br>`ra2bench/ra2render.ini:15` `position` | GetEffectiveTargetScanKey() forced to position(1) ｜ `ra2render/blitter_hooks.cpp:240-245` ｜ `call sites ra2render/blitter_hooks.cpp:1009,:798 ; red-log ra2render/blitter_hooks.cpp:811` |
| **MP** `Logic`.`TargetScanInterval` = `8`<br>`docs/re/pending_execution_master_table.md:430` | `[Logic] TargetScanInterval` @ `ra2render/blitter_hooks.cpp:531`（`GetIniIntEx`） | `8` | `ra2render/ra2render.ini:25` `8`<br>`ra2youli/ra2render.ini:9` `8`<br>`ra2bench/ra2render.ini:9` `8` | GetEffectiveTargetScanInterval() == 1 when MpActive() ｜ `ra2render/blitter_hooks.cpp:233-238` ｜ `call sites ra2render/blitter_hooks.cpp:1280,:1302,:1341,:797` |
| **MP** `Logic`.`EnableThreatRetention` = `1`<br>`docs/re/pending_execution_master_table.md:432` | **未落地-待新建**：`ra2render/blitter_hooks.cpp` grep `EnableThreatRetention` 0 命中 ｜ 定义面：`docs/re/mp_release_safety_checklist.md:64 (MP-G03)` | — 无读取点 ⇒ 无代码默认值 | `ra2render/ra2render.ini` **无此键** ⇒ 走代码默认<br>`ra2youli/ra2render.ini` **无此键** ⇒ 走代码默认<br>`ra2bench/ra2render.ini` **无此键** ⇒ 走代码默认 | 规格声明的 MP 覆盖（未落地，代码侧无实现） ｜ `未落地-待新建（0 命中：ra2render/blitter_hooks.cpp）` |
| **MP** `Multiplayer`.`MpStateWrites` = `0`<br>`docs/re/pending_execution_master_table.md:436` | **未落地-待新建**：`ra2render/blitter_hooks.cpp` grep `MpStateWrites` 0 命中 ｜ 定义面：`docs/re/ARCHITECTURE_ATLAS.md:2193（G-06 行，仅键名+默认 0，无节名）；docs/re/mp_release_safety_checklist.md:139（MP-G06）⇒ grep 0 命中/未闭环` | — 无读取点 ⇒ 无代码默认值 | `ra2render/ra2render.ini` **无此键** ⇒ 走代码默认<br>`ra2youli/ra2render.ini` **无此键** ⇒ 走代码默认<br>`ra2bench/ra2render.ini` **无此键** ⇒ 走代码默认 | 规格声明的 MP 覆盖（未落地，代码侧无实现） ｜ `未落地-待新建（0 命中：ra2render/blitter_hooks.cpp）` |
| **MP** `Multiplayer`.`MpAutoDowngrade` = `1`<br>`docs/re/pending_execution_master_table.md:438` | **未落地-待新建**：`ra2render/blitter_hooks.cpp` grep `MpAutoDowngrade` 0 命中 ｜ 定义面：`docs/re/mp_autodowngrade_spec.md:401-409` | — 无读取点 ⇒ 无代码默认值 | `ra2render/ra2render.ini` **无此键** ⇒ 走代码默认<br>`ra2youli/ra2render.ini` **无此键** ⇒ 走代码默认<br>`ra2bench/ra2render.ini` **无此键** ⇒ 走代码默认 | 规格声明的 MP 覆盖（未落地，代码侧无实现） ｜ `未落地-待新建（0 命中：ra2render/blitter_hooks.cpp）` |
| **MP** `Multiplayer`.`ForceSinglePlayer` = `0`<br>`docs/re/pending_execution_master_table.md:440` | **未落地-待新建**：`ra2render/blitter_hooks.cpp` grep `ForceSinglePlayer` 0 命中 ｜ 定义面：`docs/re/mp_autodowngrade_spec.md:25,364` | — 无读取点 ⇒ 无代码默认值 | `ra2render/ra2render.ini` **无此键** ⇒ 走代码默认<br>`ra2youli/ra2render.ini` **无此键** ⇒ 走代码默认<br>`ra2bench/ra2render.ini` **无此键** ⇒ 走代码默认 | 规格声明的 MP 覆盖（未落地，代码侧无实现） ｜ `未落地-待新建（0 命中：ra2render/blitter_hooks.cpp）` |
| **MP** `FogOfWar`.`EnableMinimapFog` = `0`<br>`docs/re/pending_execution_master_table.md:408` | `[FogOfWar] EnableMinimapFog` @ `ra2render/blitter_hooks.cpp:593`（`GetIniIntEx`） | `0` | `ra2render/ra2render.ini:148` `0`<br>`ra2youli/ra2render.ini:117` `0`<br>`ra2bench/ra2render.ini:117` `0` | GetEffectiveMinimapFog() forced to false ｜ `ra2render/blitter_hooks.cpp:257-267` ｜ `gate mirror s_minimapFogGate ra2render/blitter_hooks.cpp:595,:2874` |
<!-- END B -->

**表 B 落地度小结**：7 键中 **3 键已落地且有 MP 强制实现**（`TargetScanKey`、`TargetScanInterval`、`EnableMinimapFog` —— 即 ATLAS §9.4 的 G-02/G-08/G-01，与 `ARCHITECTURE_ATLAS.md:2180` 「已由 MPS 落地为代码级门控」一致）；**4 键未落地**（`EnableThreatRetention` = G-03、`MpStateWrites` = G-06、`MpAutoDowngrade`、`ForceSinglePlayer`）。
⇒ **总表 `:450-463` 覆盖规则表里凡依赖这 4 键的强制项，现在都只存在于纸面**；`ARCHITECTURE_ATLAS.md:338,340` 自记「G-03 / G-06 / G-07 维持未落地」与此吻合。`MpAutoDowngrade=0` 的「一键回滚」当前**不可用**。

---

## 5. 表 C —— 口径分歧登记表（改前 / 改后 + 分级）

**分级定义**：`阻断` = 按规格字面执行会导致**补丁不装 / 键读不到 / 对拍判错**；`误导` = 结论可成立但引用/命名错，浪费取证或埋二次坑；`无害` = 记录性、不影响执行。

| # | 偏差 ID | 类型 | 规格侧（`路径:行号`） | 实测侧（`路径:行号`） | 改前 → 改后（一行建议） | 级别 |
|---|---|---|---|---|---|---|
<!-- BEGIN C -->
| C1 | `D-default:EnableGapProtection` | 代码默认值 vs 规格默认值 | docs/re/pending_execution_master_table.md:401 ⇒ EnableGapProtection=1 | ra2render/blitter_hooks.cpp:606 ⇒ 代码默认 0；出厂 ini ra2render/ra2render.ini:199=0 | 改前：规格默认 1 → 改后：规格默认 0（与代码/出厂一致，安全侧） | **阻断** |
| C2 | `D-ini-lag:EnableGapProtection:ra2bench/ra2render.ini` | 部署 ini 缺键 | ra2render/ra2render.ini:199 源码目录已出厂该键 | ra2bench/ra2render.ini 无 `EnableGapProtection` ⇒ 代码默认 0 生效 | 改前：仅更新 ra2render/ra2render.ini → 改后：同步补写两游戏目录 ini 的 [FogOfWar] EnableGapProtection | **阻断** |
| C3 | `D-ini-lag:EnableGapProtection:ra2youli/ra2render.ini` | 部署 ini 缺键 | ra2render/ra2render.ini:199 源码目录已出厂该键 | ra2youli/ra2render.ini 无 `EnableGapProtection` ⇒ 代码默认 0 生效 | 改前：仅更新 ra2render/ra2render.ini → 改后：同步补写两游戏目录 ini 的 [FogOfWar] EnableGapProtection | **阻断** |
| C4 | `D-ini-lag:EnableSWChargeOpt:ra2bench/ra2render.ini` | 部署 ini 缺键 | ra2render/ra2render.ini:46 源码目录已出厂该键 | ra2bench/ra2render.ini 无 `EnableSWChargeOpt` ⇒ 代码默认 0 生效 | 改前：仅更新 ra2render/ra2render.ini → 改后：同步补写两游戏目录 ini 的 [Logic] EnableSWChargeOpt | **阻断** |
| C5 | `D-ini-lag:EnableSWChargeOpt:ra2youli/ra2render.ini` | 部署 ini 缺键 | ra2render/ra2render.ini:46 源码目录已出厂该键 | ra2youli/ra2render.ini 无 `EnableSWChargeOpt` ⇒ 代码默认 0 生效 | 改前：仅更新 ra2render/ra2render.ini → 改后：同步补写两游戏目录 ini 的 [Logic] EnableSWChargeOpt | **阻断** |
| C6 | `D-ini-lag:EnableVxlCachePrewarm:ra2bench/ra2render.ini` | 部署 ini 缺键 | ra2render/ra2render.ini:19 源码目录已出厂该键 | ra2bench/ra2render.ini 无 `EnableVxlCachePrewarm` ⇒ 代码默认 0 生效 | 改前：仅更新 ra2render/ra2render.ini → 改后：同步补写两游戏目录 ini 的 [Render] EnableVxlCachePrewarm | **阻断** |
| C7 | `D-ini-lag:EnableVxlCachePrewarm:ra2youli/ra2render.ini` | 部署 ini 缺键 | ra2render/ra2render.ini:19 源码目录已出厂该键 | ra2youli/ra2render.ini 无 `EnableVxlCachePrewarm` ⇒ 代码默认 0 生效 | 改前：仅更新 ra2render/ra2render.ini → 改后：同步补写两游戏目录 ini 的 [Render] EnableVxlCachePrewarm | **阻断** |
| C8 | `D-notlanded:EnableAudioThrottling` | 规格键未落地（代码 0 命中） | docs/re/pending_execution_master_table.md:417 ⇒ [Audio] EnableAudioThrottling=1 | ra2render/blitter_hooks.cpp 全文 grep `EnableAudioThrottling` 0 命中；ra2render/ra2render.ini 无该节/键 ⇒ 代码不读，写了也不装 | 改前：按 docs/re/pending_execution_master_table.md:417 字面写 ini → 改后：先按 docs/re/audio_throttle_landing.md:19,139-141（[AudioThrottle] Enable=0） vs docs/re/landing_pack_crt_audio_particle.md:287（[Audio] =1） 建读取点（节名以代码侧为准：Audio） | **阻断** |
| C9 | `D-notlanded:EnableMemoryPool` | 规格键未落地（代码 0 命中） | docs/re/pending_execution_master_table.md:412 ⇒ [System] EnableMemoryPool=0 | ra2render/blitter_hooks.cpp 全文 grep `EnableMemoryPool` 0 命中；ra2render/ra2render.ini 无该节/键 ⇒ 代码不读，写了也不装 | 改前：按 docs/re/pending_execution_master_table.md:412 字面写 ini → 改后：先按 docs/re/landing_pack_crt_audio_particle.md:154-155（[System]，F-02 订正默认 0） vs docs/re/crt_pool_landing.md:19（[MemoryPool]） 建读取点（节名以代码侧为准：System） | **阻断** |
| C10 | `D-notlanded:EnableParticleFog` | 规格键未落地（代码 0 命中） | docs/re/pending_execution_master_table.md:406 ⇒ [FogOfWar] EnableParticleFog=0 | ra2render/blitter_hooks.cpp 全文 grep `EnableParticleFog` 0 命中；ra2render/ra2render.ini 无该节/键 ⇒ 代码不读，写了也不装 | 改前：按 docs/re/pending_execution_master_table.md:406 字面写 ini → 改后：先按 docs/re/landing_pack_particle_fog.md:82 / docs/re/particle_fog_owner_landing.md:92 / docs/re/landing_pack_crt_audio_particle.md:431 建读取点（节名以代码侧为准：FogOfWar） | **阻断** |
| C11 | `D-notlanded:EnableSpySatGate` | 规格键未落地（代码 0 命中） | docs/re/pending_execution_master_table.md:402 ⇒ [FogOfWar] EnableSpySatGate=1 | ra2render/blitter_hooks.cpp 全文 grep `EnableSpySatGate` 0 命中；ra2render/ra2render.ini 无该节/键 ⇒ 代码不读，写了也不装 | 改前：按 docs/re/pending_execution_master_table.md:402 字面写 ini → 改后：先按 docs/re/landing_pack_gap_spysat.md:35,157-159 建读取点（节名以代码侧为准：FogOfWar） | **阻断** |
| C12 | `D-notlanded:EnableThreatRetention` | 规格键未落地（代码 0 命中） | docs/re/pending_execution_master_table.md:432 ⇒ [Logic] EnableThreatRetention=1 | ra2render/blitter_hooks.cpp 全文 grep `EnableThreatRetention` 0 命中；ra2render/ra2render.ini 无该节/键 ⇒ 代码不读，写了也不装 | 改前：按 docs/re/pending_execution_master_table.md:432 字面写 ini → 改后：先按 docs/re/mp_release_safety_checklist.md:64 (MP-G03) 建读取点（节名以代码侧为准：Logic） | **阻断** |
| C13 | `D-notlanded:ForceSinglePlayer` | 规格键未落地（代码 0 命中） | docs/re/pending_execution_master_table.md:440 ⇒ [Multiplayer] ForceSinglePlayer=0 | ra2render/blitter_hooks.cpp 全文 grep `ForceSinglePlayer` 0 命中；ra2render/ra2render.ini 无该节/键 ⇒ 代码不读，写了也不装 | 改前：按 docs/re/pending_execution_master_table.md:440 字面写 ini → 改后：先按 docs/re/mp_autodowngrade_spec.md:25,364 建读取点（节名以代码侧为准：Multiplayer） | **阻断** |
| C14 | `D-notlanded:MaxSoundsPerFrame` | 规格键未落地（代码 0 命中） | docs/re/pending_execution_master_table.md:418 ⇒ [Audio] MaxSoundsPerFrame=4 | ra2render/blitter_hooks.cpp 全文 grep `MaxSoundsPerFrame` 0 命中；ra2render/ra2render.ini 无该节/键 ⇒ 代码不读，写了也不装 | 改前：按 docs/re/pending_execution_master_table.md:418 字面写 ini → 改后：先按 docs/re/audio_throttle_landing.md:19,144（[AudioThrottle] MaxVoicePerFrame=6） vs docs/re/landing_pack_crt_audio_particle.md:287（[Audio] =4） 建读取点（节名以代码侧为准：Audio） | **阻断** |
| C15 | `D-notlanded:MpAutoDowngrade` | 规格键未落地（代码 0 命中） | docs/re/pending_execution_master_table.md:438 ⇒ [Multiplayer] MpAutoDowngrade=1 | ra2render/blitter_hooks.cpp 全文 grep `MpAutoDowngrade` 0 命中；ra2render/ra2render.ini 无该节/键 ⇒ 代码不读，写了也不装 | 改前：按 docs/re/pending_execution_master_table.md:438 字面写 ini → 改后：先按 docs/re/mp_autodowngrade_spec.md:401-409 建读取点（节名以代码侧为准：Multiplayer） | **阻断** |
| C16 | `D-notlanded:MpStateWrites` | 规格键未落地（代码 0 命中） | docs/re/pending_execution_master_table.md:436 ⇒ [Multiplayer] MpStateWrites=0 | ra2render/blitter_hooks.cpp 全文 grep `MpStateWrites` 0 命中；ra2render/ra2render.ini 无该节/键 ⇒ 代码不读，写了也不装 | 改前：按 docs/re/pending_execution_master_table.md:436 字面写 ini → 改后：先按 docs/re/ARCHITECTURE_ATLAS.md:2193（G-06 行，仅键名+默认 0，无节名）；docs/re/mp_release_safety_checklist.md:139（MP-G06）⇒ grep 0 命中/未闭环 建读取点（节名以代码侧为准：Multiplayer） | **阻断** |
| C17 | `D-notlanded:PoolBlockCount` | 规格键未落地（代码 0 命中） | docs/re/pending_execution_master_table.md:413 ⇒ [System] PoolBlockCount=4096 | ra2render/blitter_hooks.cpp 全文 grep `PoolBlockCount` 0 命中；ra2render/ra2render.ini 无该节/键 ⇒ 代码不读，写了也不装 | 改前：按 docs/re/pending_execution_master_table.md:413 字面写 ini → 改后：先按 无卡面定义 ⇒ 未闭环：crt_pool_landing.md 与 landing_pack_crt_audio_particle.md 全文 grep PoolBlockCount / BlockCount / 4096 均 0 命中（语义未定：每桶块数 or 总块数） 建读取点（节名以代码侧为准：System） | **阻断** |
> 【W3 勘误 · W3-A6/ISSUE-KEY-POOLBLOCKCOUNT】[W3-Lead临时裁决] 改前：PoolBlockCount=4096；改后：; [DC-04 裁决: PoolBlockCount 保持未定，禁入冻结面，予以删除]；依据：docs/re/dispatch/W3_20261001_Lead_DECISION_AND_BOARD.md:43, 49；分级：P0
| C18 | `D-notlanded:SoundMinIntervalFrames` | 规格键未落地（代码 0 命中） | docs/re/pending_execution_master_table.md:419 ⇒ [Audio] SoundMinIntervalFrames=2 | ra2render/blitter_hooks.cpp 全文 grep `SoundMinIntervalFrames` 0 命中；ra2render/ra2render.ini 无该节/键 ⇒ 代码不读，写了也不装 | 改前：按 docs/re/pending_execution_master_table.md:419 字面写 ini → 改后：先按 docs/re/audio_throttle_landing.md:19,147（[AudioThrottle] VoiceDedupMs=80 **毫秒**） vs docs/re/landing_pack_crt_audio_particle.md:287（[Audio] =2 **帧**） 建读取点（节名以代码侧为准：Audio） | **阻断** |
| C19 | `D-notlanded:SyncCmdMirror` | 规格键未落地（代码 0 命中） | docs/re/pending_execution_master_table.md:397 ⇒ [SyncDiag] SyncCmdMirror=0 | ra2render/blitter_hooks.cpp 全文 grep `SyncCmdMirror` 0 命中；ra2render/ra2render.ini 无该节/键 ⇒ 代码不读，写了也不装 | 改前：按 docs/re/pending_execution_master_table.md:397 字面写 ini → 改后：先按 docs/re/landing_pack_net_fix.md:563 建读取点（节名以代码侧为准：SyncDiag） | **阻断** |
| C20 | `D-notlanded:SyncEarlyLog` | 规格键未落地（代码 0 命中） | docs/re/pending_execution_master_table.md:394 ⇒ [SyncDiag] SyncEarlyLog=0 | ra2render/blitter_hooks.cpp 全文 grep `SyncEarlyLog` 0 命中；ra2render/ra2render.ini 无该节/键 ⇒ 代码不读，写了也不装 | 改前：按 docs/re/pending_execution_master_table.md:394 字面写 ini → 改后：先按 docs/re/landing_pack_net_fix.md:218 建读取点（节名以代码侧为准：SyncDiag） | **阻断** |
| C21 | `D-notlanded:SyncMirror` | 规格键未落地（代码 0 命中） | docs/re/pending_execution_master_table.md:396 ⇒ [SyncDiag] SyncMirror=0 | ra2render/blitter_hooks.cpp 全文 grep `SyncMirror` 0 命中；ra2render/ra2render.ini 无该节/键 ⇒ 代码不读，写了也不装 | 改前：按 docs/re/pending_execution_master_table.md:396 字面写 ini → 改后：先按 docs/re/landing_pack_net_fix.md:431 建读取点（节名以代码侧为准：SyncDiag） | **阻断** |
| C22 | `D-notlanded:SyncSnapshotOnDesync` | 规格键未落地（代码 0 命中） | docs/re/pending_execution_master_table.md:395 ⇒ [SyncDiag] SyncSnapshotOnDesync=0 | ra2render/blitter_hooks.cpp 全文 grep `SyncSnapshotOnDesync` 0 命中；ra2render/ra2render.ini 无该节/键 ⇒ 代码不读，写了也不装 | 改前：按 docs/re/pending_execution_master_table.md:395 字面写 ini → 改后：先按 docs/re/landing_pack_net_fix.md:338 建读取点（节名以代码侧为准：SyncDiag） | **阻断** |
| C23 | `D4a` | 节名不一致（内存池） | docs/re/pending_execution_master_table.md:410-412 ⇒ [System] EnableMemoryPool；docs/re/landing_pack_crt_audio_particle.md:154（F-02 订正）同记 [System] | docs/re/crt_pool_landing.md:19 ⇒ [MemoryPool] EnableMemoryPool；代码 0 命中（ra2render/blitter_hooks.cpp） | 改前：[MemoryPool]（单点口径） → 改后：[System]（总表 + 落地包一致，且 [System] 节在代码:541/:544 已实际存在，不必新增节） | **阻断** |
> 【W3 勘误 · W3-A6/ISSUE-SECTION-MEMORYPOOL】[W3-Lead临时裁决] 改前：[MemoryPool] EnableMemoryPool；改后：[System] ; DC-01 裁决口径: 使用既有 [System] 节，零新增节 EnableMemoryPool=0；依据：docs/re/dispatch/W3_20261001_Lead_DECISION_AND_BOARD.md:40; docs/re/pending_execution_master_table.md:410-412；分级：P0
| C24 | `D5a` | 节名不一致 | docs/re/pending_execution_master_table.md:423 ⇒ [Render] L4DirtyMode | ra2render/blitter_hooks.cpp:757 ⇒ [FogOfWar] L4DirtyMode | 改前：`[Render] L4DirtyMode` → 改后：`[FogOfWar] L4DirtyMode`（改文档，代码为唯一口径） | **阻断** |
| C25 | `D6a:EnableAudioThrottling` | 同一功能两套键名/节名/单位 | docs/re/pending_execution_master_table.md:417 ⇒ [Audio] EnableAudioThrottling=1 | docs/re/audio_throttle_landing.md:139-141 ⇒ [AudioThrottle] Enable=0（另有 MaxSamePerWindow/Whitelist*/MaxAudibleDistSq/ThrottlePlayIndexAtPos 4+ 键总表不提） | 改前：两案并存 → 改后：以卡面 [AudioThrottle] Enable 为唯一口径，总表 §3.1 的 [Audio] 三键标注为废弃别名（单位口径：卡面 VoiceDedupMs=80ms，总表 SoundMinIntervalFrames=2 帧 @30fps≈66ms） | **阻断** |
| C26 | `D6a:MaxSoundsPerFrame` | 同一功能两套键名/节名/单位 | docs/re/pending_execution_master_table.md:418 ⇒ [Audio] MaxSoundsPerFrame=4 | docs/re/audio_throttle_landing.md:142-144 ⇒ [AudioThrottle] MaxVoicePerFrame=6（另有 MaxSamePerWindow/Whitelist*/MaxAudibleDistSq/ThrottlePlayIndexAtPos 4+ 键总表不提） | 改前：两案并存 → 改后：以卡面 [AudioThrottle] MaxVoicePerFrame 为唯一口径，总表 §3.1 的 [Audio] 三键标注为废弃别名（单位口径：卡面 VoiceDedupMs=80ms，总表 SoundMinIntervalFrames=2 帧 @30fps≈66ms） | **阻断** |
| C27 | `D6a:SoundMinIntervalFrames` | 同一功能两套键名/节名/单位 | docs/re/pending_execution_master_table.md:419 ⇒ [Audio] SoundMinIntervalFrames=2 | docs/re/audio_throttle_landing.md:147 ⇒ [AudioThrottle] VoiceDedupMs=80(ms)（另有 MaxSamePerWindow/Whitelist*/MaxAudibleDistSq/ThrottlePlayIndexAtPos 4+ 键总表不提） | 改前：两案并存 → 改后：以卡面 [AudioThrottle] VoiceDedupMs 为唯一口径，总表 §3.1 的 [Audio] 三键标注为废弃别名（单位口径：卡面 VoiceDedupMs=80ms，总表 SoundMinIntervalFrames=2 帧 @30fps≈66ms） | **阻断** |
| C28 | `D6b` | 音频总开关默认值互斥 | docs/re/pending_execution_master_table.md:417 ⇒ EnableAudioThrottling=1（默认开） | docs/re/audio_throttle_landing.md:19,165 ⇒ Enable=0（默认关，对拍基线）；docs/re/execution_runbook.md:365 ⇒ EnableAudioThrottling=0 | 改前：默认 1 → 改后：默认 0（落地卡与对拍基线口径，开箱零行为差） | **阻断** |
| C29 | `D-atlas-ref` | 「唯一口径」引用的行号/内容已失效 | docs/re/pending_execution_master_table.md:443 ⇒ 键名与默认值以 ARCHITECTURE_ATLAS.md §9.4 `L1536-1543` 为唯一口径 | docs/re/ARCHITECTURE_ATLAS.md §9.4 现起于 :2178（表体 :2184-2197）；该表内**无** MpAutoDowngrade / ForceSinglePlayer / MpStateWrites 键名（只有门控名 G-05 RadarPendingGate、G-07 RestoreTypeOffsets、G-08 MpThrottleForceInterval、G-09 MinimapEverSeenNotice —— 均非 ini 键） | 改前：引 §9.4 L1536-1543 → 改后：引 §9.4 表体（现 :2184-2197）+ mp_autodowngrade_spec.md:401-409（MpAutoDowngrade/ForceSinglePlayer 唯一带节名的口径） | **误导** |
| C30 | `D-gate-default` | 同键默认值文档互斥 | docs/re/pending_execution_master_table.md:402 ⇒ EnableSpySatGate=1；docs/re/pending_execution_master_table.md:452 ⇒ 联机全员强制同值 | docs/re/execution_runbook.md:360 ⇒ EnableSpySatGate=0（Baseline 安全模板）；代码 0 命中 | 改前：1/0 两写 → 改后：未落地期统一记 0（关闸=原版行为），并在卡上标「落地后方可置 1」 | **误导** |
| C31 | `D-mm-value` | 总表对出厂 ini 值的断言与实测不符 | docs/re/pending_execution_master_table.md:458 ⇒ 「API 默认已强制 0；**ini 现值 1**」 | ra2render/ra2render.ini:148 ⇒ EnableMinimapFog=0；ra2youli/ra2render.ini:117=0；ra2bench/ra2render.ini:117=0（三处皆 0） | 改前：「ini 现值 1」→ 改后：「ini 现值 0（三处一致）」 | **误导** |
| C32 | `D-mpsec:ForceSinglePlayer` | MP 键节名不一致（文档内部） | docs/re/pending_execution_master_table.md:440 ⇒ [Multiplayer] ForceSinglePlayer | docs/re/mp_autodowngrade_spec.md:25,364 ⇒ [Logic] ForceSinglePlayer | 改前：[Multiplayer] → 改后：[Logic]（与 [ForceSinglePlayer] 同族的 3 键一起归一；未落地，趁早定名） | **误导** |
| C33 | `D-mpsec:MpAutoDowngrade` | MP 键节名不一致（文档内部） | docs/re/pending_execution_master_table.md:438 ⇒ [Multiplayer] MpAutoDowngrade | docs/re/mp_autodowngrade_spec.md:401-409 ⇒ [Logic] MpAutoDowngrade | 改前：[Multiplayer] → 改后：[Logic]（与 [MpAutoDowngrade] 同族的 3 键一起归一；未落地，趁早定名） | **误导** |
| C34 | `D-phantom-stubs` | 文档声明的键无任何定义面 | docs/re/ARCHITECTURE_ATLAS.md:2191,2664 ⇒ `[FogOfWar] EnableFogBlendStubs`（G-04 组成键） | 代码 0 命中、ra2render/ra2render.ini 0 命中；ATLAS:338 自记「全源码 grep 0 命中」 | 改前：G-04 行内列出该键 → 改后：明确标注「未落地-待新建，无卡面定义」或从门控表移除 | **误导** |
| C35 | `D4b` | 规格键无卡面定义 | docs/re/pending_execution_master_table.md:413 ⇒ PoolBlockCount=4096 | docs/re/crt_pool_landing.md 全文 grep `PoolBlockCount` 0 命中（仅 master_table:504 遥测解释提到调大） | 改前：只总表出现 → 改后：在 crt_pool_landing.md §3 补 `[MemoryPool] PoolBlockCount=4096` 定义 + 桶数语义 | **误导** |
| C36 | `D6c` | 音频键单位口径 | docs/re/pending_execution_master_table.md:419 ⇒ SoundMinIntervalFrames=2（**帧**） | docs/re/audio_throttle_landing.md:147 ⇒ VoiceDedupMs=80（**毫秒**）；代码两者均 0 命中 | 改前：帧/毫秒混写 → 改后：统一毫秒（ms），或在键名后缀显式标 `_ms` / `_frames` 并给 30fps 换算注 | **误导** |
| C37 | `D6d` | 口径落后的方向未标注（谁该改） | docs/re/pending_execution_master_table.md（文件 mtime 2026-10-01 13:45，最新）§3.1 :415-419/:423 仍写 [Audio]/[Render]/默认 1 | docs/re/landing_pack_crt_audio_particle.md:287（2026-09-27）与总表同口径；docs/re/audio_throttle_landing.md:19（2026-09-30 16:51）为更新且更可实现的 [AudioThrottle] 8 键口径 | 改前：三处互不引用 → 改后：在总表 §3.1 代码块上方加一行「音频口径以 audio_throttle_landing.md §3.1 为准（本块 [Audio] 三键作废）」；P-4 相反（总表 + 落地包一致 [System]，crt_pool_landing.md 单点 [MemoryPool] 需改） | **误导** |
| C38 | `D-r01-stale` | MP 检查表的代码行号/默认值已过期 | docs/re/mp_release_safety_checklist.md:22（R-01）⇒ `blitter_hooks.cpp:103` 的 `GetPrivateProfileIntA("FogOfWar","EnableMinimapFog",1,...)` 默认值待改为 0 | ra2render/blitter_hooks.cpp:103 实为 `s_fogFirstStageGainUpstream` 定义；EnableMinimapFog 现读点 ra2render/blitter_hooks.cpp:593，默认值已是 0 ⇒ **R-01/MP-G01 实质已落地** | 改前：行号 :103 / 默认 1 → 改后：行号 :593 / 默认 0，并标注「已满足」 | **无害** |
| C39 | `D6-idnote` | 工单/普查编号错位（登记口径） | 工单 PK-3 表述：「census §6 行 D5/**D6** 已证明音频两套命名不一致」 | out/re_work/harness_survey/RE_PROGRESS_SURVEY.md:226 D5 = L4DirtyMode 节名 + EnableGapProtection 默认值（本表 D5a / D-default:EnableGapProtection）；:227 D6 = `results_verify_static_24.txt` UTF-16 行号问题，与音频无关 | 改前：沿用 D6 指音频 → 改后：音频口径另编号（本表 D6a/D6b/D6c），并在勘误表注明 「D6 原指 UTF-16 验证件，非音频」 | **无害** |
<!-- END C -->

### 5.1 分级计数

* **阻断 28 条**：C1（`EnableGapProtection` 默认 1 vs 0）、C2–C7（三键在两游戏目录 ini 缺失）、C8–C22（15 个规格键代码 0 命中）、C23（`[MemoryPool]` vs `[System]`）、C24（`[Render]` vs `[FogOfWar]`）、C25–C27（音频两套键名/节名）、C28（音频默认 1 vs 0）。
* **误导 9 条**：C29–C37。
* **无害 2 条**：C38、C39。

> 与本次普查编号的对应：**普查 D5（`RE_PROGRESS_SURVEY.md:226`）= 本表 C24 + C1**（节名 + 默认值两条，工单把它当作一条）。**音频两套命名** 在工单里被称作「D6」，但普查 `:227` 的 D6 实为 `results_verify_static_24.txt` 的 UTF-16 行号问题 ⇒ 见 **C39**（编号错位登记），音频口径在本表另编 **C25–C28 + C36**。

---

## 6. 表 D —— 仅存在于代码/ini 的键（补全矩阵，非规格驱动）

这些键**不在 14+7 之内**，但同属 `ra2render.ini` 出厂面；执行六包时必须知道它们的现值，尤其 `EnableStarCraftFog` / `RadarFogGuardMode` 与 P-6 `L4DirtyMode` 存在**同节互相影响**关系。

| 键名 | 代码节 + 读取行 + API | 代码默认值 | ini 出厂值（三处） | 规格/卡面出处 | 钳位·收敛分支（实测） |
|---|---|---|---|---|---|
<!-- BEGIN D -->
| `FogStrengthPct` | `FogOfWar` @ `ra2render/blitter_hooks.cpp`:691（`GetIniStringEx`） | `"auto"` | `ra2render/ra2render.ini:238` `auto`<br>`ra2youli/ra2render.ini:173` `auto`<br>`ra2bench/ra2render.ini:173` `auto` | `docs/re/fog_strength_calibration.md:1` | ra2render/blitter_hooks.cpp:691-721 非法/空串收敛 auto；数值 clamp [0,100]；>71.875 不可达→s=0 并告警；运行期重读 ra2render/blitter_hooks.cpp:477-509 (GetPrivateProfileStringA :484, 节拍 :849) |
| `EnableSIMD` | `Render` @ `ra2render/blitter_hooks.cpp`:535（`GetIniIntEx`） | `1` | `ra2render/ra2render.ini:3` `1`<br>`ra2youli/ra2render.ini:3` `1`<br>`ra2bench/ra2render.ini:3` `1` | `docs/re/INSTALLED_HOOKS_AUDIT.md:54（存量 L1 性能键，§3.1 未列）` | 无钳位分支（直接 bool 化/直取） |
| `UnlockGameSpeed` | `Speed` @ `ra2render/blitter_hooks.cpp`:538（`GetIniIntEx`） | `0` | `ra2render/ra2render.ini:52` `0`<br>`ra2youli/ra2render.ini:21` `0`<br>`ra2bench/ra2render.ini:21` `0` | `docs/re/INSTALLED_HOOKS_AUDIT.md:189（存量，§3.1 未列）` | 无钳位分支（直接 bool 化/直取） |
| `EnableLFH` | `System` @ `ra2render/blitter_hooks.cpp`:541（`GetIniIntEx`） | `1` | `ra2render/ra2render.ini:56` `1`<br>`ra2youli/ra2render.ini:25` `1`<br>`ra2bench/ra2render.ini:25` `1` | `docs/re/INSTALLED_HOOKS_AUDIT.md:236（存量，§3.1 未列）` | 无钳位分支（直接 bool 化/直取） |
| `HighPrecisionTimer` | `System` @ `ra2render/blitter_hooks.cpp`:544（`GetIniIntEx`） | `1` | `ra2render/ra2render.ini:58` `1`<br>`ra2youli/ra2render.ini:27` `1`<br>`ra2bench/ra2render.ini:27` `1` | `docs/re/INSTALLED_HOOKS_AUDIT.md:36（存量，§3.1 未列）` | 无钳位分支（直接 bool 化/直取） |
| `EnableStarCraftFog` | `FogOfWar` @ `ra2render/blitter_hooks.cpp`:547（`GetIniIntEx`） | `1` | `ra2render/ra2render.ini:64` `1`<br>`ra2youli/ra2render.ini:33` `1`<br>`ra2bench/ra2render.ini:33` `1` | `docs/re/fog_split_report.md:26 + docs/re/ARCHITECTURE_ATLAS.md:2189(G-04)` | 无钳位分支（直接 bool 化/直取） |
| `RadarSweepCooldownFrames` | `FogOfWar` @ `ra2render/blitter_hooks.cpp`:553（`GetIniIntEx`） | `600` | `ra2render/ra2render.ini:122` `600`<br>`ra2youli/ra2render.ini:91` `600`<br>`ra2bench/ra2render.ini:91` `600` | `ra2render/ra2render.ini:121（ini 注释即唯一口径，无卡面行）` | ra2render/blitter_hooks.cpp:554 clamp min 60 |
| `RadarSweepRadiusCells` | `FogOfWar` @ `ra2render/blitter_hooks.cpp`:556（`GetIniIntEx`） | `16` | `ra2render/ra2render.ini:124` `16`<br>`ra2youli/ra2render.ini:93` `16`<br>`ra2bench/ra2render.ini:93` `16` | `ra2render/ra2render.ini:123（同上）` | ra2render/blitter_hooks.cpp:557-558 clamp to [4,64] |
| `EnableBuildingFog` | `FogOfWar` @ `ra2render/blitter_hooks.cpp`:564（`GetIniIntEx`） | `1` | `ra2render/ra2render.ini:130` `1`<br>`ra2youli/ra2render.ini:99` `1`<br>`ra2bench/ra2render.ini:99` `1` | `docs/re/fog_split_report.md:42` | 无钳位分支（直接 bool 化/直取） |
| `EnableBulletFog` | `FogOfWar` @ `ra2render/blitter_hooks.cpp`:567（`GetIniIntEx`） | `1` | `ra2render/ra2render.ini:133` `1`<br>`ra2youli/ra2render.ini:102` `1`<br>`ra2bench/ra2render.ini:102` `1` | `docs/re/fog_split_report.md:42` | 无钳位分支（直接 bool 化/直取） |
| `FadeFogTransition` | `FogOfWar` @ `ra2render/blitter_hooks.cpp`:570（`GetIniIntEx`） | `1` | `ra2render/ra2render.ini:141` `1`<br>`ra2youli/ra2render.ini:110` `1`<br>`ra2bench/ra2render.ini:110` `1` | `docs/re/fog_split_report.md:195` | 无钳位分支（直接 bool 化/直取） |
| `EnableUnitFog` | `FogOfWar` @ `ra2render/blitter_hooks.cpp`:576（`GetIniIntEx`） | `1` | `ra2render/ra2render.ini:138` `1`<br>`ra2youli/ra2render.ini:107` `1`<br>`ra2bench/ra2render.ini:107` `1` | `docs/re/fog_split_report.md:28` | 无钳位分支（直接 bool 化/直取） |
| `VisibilityMode` | `FogOfWar` @ `ra2render/blitter_hooks.cpp`:584（`GetIniStringEx`） | `"starcraft"` | `ra2render/ra2render.ini:117` `starcraft`<br>`ra2youli/ra2render.ini:86` `starcraft`<br>`ra2bench/ra2render.ini:86` `starcraft` | `docs/re/fog_visibility_mode_report.md:28` | ra2render/blitter_hooks.cpp:587-591 非 vanilla（含未知/空值）收敛为 starcraft |
| `EnableVxlCachePrewarm` | `Render` @ `ra2render/blitter_hooks.cpp`:616（`GetIniIntEx`） | `0` | `ra2render/ra2render.ini:19` `0`<br>`ra2youli/ra2render.ini` **无此键** ⇒ 走代码默认<br>`ra2bench/ra2render.ini` **无此键** ⇒ 走代码默认 | `docs/re/landing_pack_vxl_prewarm.md:71` | 无钳位分支（直接 bool 化/直取） |
| `EnableSWChargeOpt` | `Logic` @ `ra2render/blitter_hooks.cpp`:624（`GetIniIntEx`） | `0` | `ra2render/ra2render.ini:46` `0`<br>`ra2youli/ra2render.ini` **无此键** ⇒ 走代码默认<br>`ra2bench/ra2render.ini` **无此键** ⇒ 走代码默认 | `docs/re/landing_pack_sw_charge.md:69` | 无钳位分支（直接 bool 化/直取） |
| `RadarFogGuardMode` | `FogOfWar` @ `ra2render/blitter_hooks.cpp`:632（`GetIniIntEx`） | `RADAR_FOG_GUARD_NATIVE (RADAR_FOG_GUARD_NATIVE=3)` | `ra2render/ra2render.ini:165` `3`<br>`ra2youli/ra2render.ini:134` `3`<br>`ra2bench/ra2render.ini:134` `3` | `docs/re/radar_fix2_report.md:24` | ra2render/blitter_hooks.cpp:632-633 + :249-255 越界收敛为 3 (RADAR_FOG_GUARD_NATIVE, ra2render.h:191) |
| `FogProbe` | `FogOfWar` @ `ra2render/blitter_hooks.cpp`:773（`GetIniIntEx`） | `0` | `ra2render/ra2render.ini:260` `0`<br>`ra2youli/ra2render.ini:195` `0`<br>`ra2bench/ra2render.ini:195` `0` | `docs/re/fog_stub_probe_report.md:95 + ra2render.ini:253-259（[ZC-10B ③] 注释）` | ra2render/blitter_hooks.cpp:773-775 bool 化 |
<!-- END D -->

**表 D 要点（与六包的耦合）**：

1. `L4DirtyMode` 与 `EnableStarCraftFog`、`RadarFogGuardMode` **同在 `[FogOfWar]` 节**（`ra2render.ini:60` 起，至文件尾无新节 ⇒ `:148/:165/:199/:238/:251/:260` 全属该节）。这是 `[Render] L4DirtyMode` 写法必然失效的结构性原因（C24）。
2. `[FOG-SPLIT]` 已把「总闸=0 时 L4 强制全刷」解耦：`ra2render.ini:86` 明写「② L4 视口全量刷（`0x006D3D99`）恒强制全量重绘（不再随总闸回退原版 `jge`）」⇒ **P-6 的 `vision-dirty` 档位实际受 `EnableStarCraftFog` 牵制**，对拍时两键必须同记。
3. `RadarFogGuardMode=3`（`ra2render.ini:165`，代码 `:632` 默认 `RADAR_FOG_GUARD_NATIVE=3`，`ra2render.h:191`）是 `EnableMinimapFog` 的子档：`:2874` `if (!s_minimapFogGate || s_radarFogGuardMode != 3)` ⇒ **G-01 联机强制 0 时，mode 3 一并失效**，表 B 的 `EnableMinimapFog` 覆盖规则实际覆盖了两键行为。
4. `EnableGapProtection` / `EnableVxlCachePrewarm` / `EnableSWChargeOpt` 三键是 **09-30 新入源码**（`ra2render.ini:19/:46/:199`），两游戏目录 ini（18412 B，20 键）**尚未跟进** ⇒ 见 C2–C7；「装了新 DLL 但用旧 ini」= 三能力全默认关。

---

## 7. 「悬空键」判定

**判据**：一个键算「已闭合」= ① 能落到 `blitter_hooks.cpp` 的**具体读取行**，或 ② 明确标注 **未落地-待新建** 并给出**定义它的卡面路径**。二者皆无 = 悬空。

```
14 + 7 = 21 键：代码有具体读点 = 6；未落地但已给定义面 = 13；
未落地 + 定义面自身记「未闭环」= 2（PoolBlockCount、MpStateWrites）；
无任何定义面（真空悬） = 0
```

> **悬空键 = 0 悬空（判据 = 「无代码读点 且 无文档定义面」）。**
> `PoolBlockCount`、`MpStateWrites` 记为「**未落地-待新建 + 卡面未闭环**」而非悬空，原因明示：
> * `PoolBlockCount` —— 仅 `pending_execution_master_table.md:413/:504` 出现，`crt_pool_landing.md` 与 `landing_pack_crt_audio_particle.md` 全文 grep `PoolBlockCount`/`BlockCount`/`4096` **0 命中** ⇒ 语义未定（每桶块数 or 总块数？8 桶各自 4096 还是合计？）⇒ **未闭环**；下一步取证 = 由 `crt_pool_landing.md` 作者补 §3 键定义。
> * `MpStateWrites` —— `ARCHITECTURE_ATLAS.md:2193`（G-06）只给「键名 + 默认 0」不给节名，`mp_release_safety_checklist.md:139` 自记「grep `MpStateWrites` = 0 命中 ⇒ 未闭环」⇒ **未闭环**；下一步取证 = 由 MP 卡面定名（建议 `[Logic]`，见 C32/C33）。

---

## 8. 给执行方（ZCode/MiMo）的三条硬结论

1. **先读表 A ②列再写 ini**：只有 `EnableGapProtection`、`EnableSpySatRadarSweep`、`L4DirtyMode` 三键「写了立即有读点」；其余 11 主键 + 4 MP 键必须**先落代码读取点**，写了 ini 也只是空气。写入的节名**必须**用 `[FogOfWar]` / `[Logic]` / `[System]` 等**代码实际节名**（P-6 尤其：不是 `[Render]`）。
2. **`[FogOfWar] EnableGapProtection=0` 需显式写入两游戏目录 ini**（`:44` 的 `installed==3` 契约否则必不满足）；且 MpActive 时**代码强制不装**（`:3321-3322`），与总表 `:452` 「全员强制同值」不是同一语义——总表说的是「同值」，代码做的是「联机直接不装」。
3. **音频 P-5 在定名前禁止开工**：`[Audio]` 3 键 与 `[AudioThrottle]` 8 键（含 `MaxSamePerWindow`/`WhitelistPriorityMin`/`WhitelistTypeMask`/`MaxAudibleDistSq`/`ThrottlePlayIndexAtPos`，见 `audio_throttle_landing.md:150-162`）互不兼容，且默认值（1 vs 0）与单位（帧 vs ms）都冲突（C25–C28、C36）。裁决建议见 §5 各行「改后」列，交接细节见 `out/re_work/static_prep/keys/pilot_handoff_for_zcode.md`。

---

## 9. 复算方式（本文可机械重放）

```bash
python out/re_work/static_prep/keys/gen_key_matrix.py        # 9 断言 + 写 json/csv，退出码 0
python out/re_work/static_prep/keys/gen_key_matrix.py --md    # 本文表 A/B/C/D 的行体（与 json 同源）
```

断言清单与最近一次实测输出：`out/re_work/static_prep/keys/verify_run.txt`。
本工单**只新建** `docs/re/config_key_matrix.md` 与 `out/re_work/static_prep/keys/**`；`ra2render/**`、`gamemd.exe`、两游戏目录、`tools/**`、兄弟工单目录 **0 写入**（`sha256sum ra2youli/gamemd.exe` 前后一致：`73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476`）。
