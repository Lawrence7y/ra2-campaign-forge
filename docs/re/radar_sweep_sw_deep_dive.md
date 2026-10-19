# 雷达扫描超武（SpySat / RadarSweep / PsychicReveal）静态深潜 — R-RADAR-SW

> **任务**：R-RADAR-SW · 全静态（只读 `gamemd.exe` 1.001）
> **交付**：本文件 + `out/re_work/re_sprint/R_radar_sw/**`
> **写作用域**：`docs/re/radar_sweep_sw_deep_dive.md` + `out/re_work/re_sprint/R_radar_sw/**`（未触碰 `ra2render/**` / 台账 / 看板）
> **证据图例**：**[实证]** 字节级核验（`verify_radar_sw_bytes.py`）/ **[前证]** 既有冲刺已核验 / **[推演]** 静态推导 / **[待实测]**
> **关联**：`superweapon_re.md` · `gap_psychic_reveal_deep_dive.md` · `gap_generator_spysat_deep_dive.md` · `visibility_gap_spysat.md` · `radar_minimap_dots.md` · `radar_hook_routeA_spec.md` · `landing_pack_gap_spysat.md`

---

## 0. 一句话结论

雷达扫描超武有 **四条并行链**（Case 11 PsychicReveal / UpdateSpySat 全图 / SpyPlane 扫描线 / 未落地 H-20-C 私有扫窗）。现网钩只覆盖 **小地图像素层**（路线 A 三钩）与 **TYPE 改写**（`PatchSpySatBuildingTypes`），**扫窗表现层完全空白**；且 `RadarSweepRadiusCells` 写的 `SW+0xF8` 对 Case 11 **是死写**（半径硬编码 `Rules+0xFEC`，再 `min(10,·)` 夹紧）——半径键当前无效。落地推荐 **H-20-C 私有扫窗**（不写 Cell / 不吃 RNG）；走原版 `RevealArea2` 则必须配 P-2.1 NOP 且全端同补丁，否则 gap 计数分叉。

---

## 1. Launch → 小地图/开图 完整链（四条并行）

### 1.1 主链：PsychicReveal Case 11（现网「星际人族雷达」所走）

```
SuperClass::Launch 0x006CC390
  ├─ mov eax,[ebp+0xB4]          ; SWType.Type 枚举          [实证 B7]
  ├─ cmp eax,0xB / ja 退出
  └─ jmp [eax*4 + 0x6CDE44]      ; 12 路绝对 VA 跳表
        └─ case 11 → 0x006CD70C
              ├─ mov al,[ebx+0x6F] / jz 0x6CDE36            ; IsCharged 门  [实证 B1]
              ├─ 0x5657A0 GetCellAt(目标格)
              ├─ Rules+0xFEC (PsychicRevealRadius)          ; ★不读 SW+0xF8  [实证 B2/B4]
              ├─ call 0x5678E0 RevealArea2 #1 (SkipReveal=0) [实证 B3]
              ├─ call 0x5678E0 RevealArea2 #2 (SkipReveal=1) [实证 B5]
              ├─ call 0x750E20 VocClass::PlayIndexAtPos      ; 雷达事件/音效  [实证 B6]
              └─ isPlayer → 写 UI 音效槽 0x8809A0 = -1
```

**RevealArea2（`0x5678E0`）圆域逐格写点**（半径夹紧 `min(10, radius)` @ `0x567A4A` **[前证 C2]**）：

| 偏移 | 字段 | 写值 | 后果 |
|---|---|---|---|
| `Cell+0x12C` | CopyFlags | `\|= 0x18`（Explored+Mapped） | 进档；小地图 `IsShrouded` 变假 |
| `Cell+0x130` | ShroudCounter | `0` | 进档 |
| **`Cell+0x134`** | **GapsCoveringThisCell** | **`0`** | **[实证 B8] 废缝源头**：`ReshroudCell` 钳位到 0 ⇒ 该格永远回不了黑雾 |
| `Cell+0x140` | RedrawFlags | 置位 | 重绘 |

**小地图消费侧**（`RadarClass::DrawCell 0x655C50`）：`IsShrouded 0x586360`（`Cell+0x12C` bit3）/ `IsFogged 0x5864A0`（`Cell+0x13C`）决定地形明暗与敌点过滤；开图后格子在小地图上**永久全彩**（除非 L3 灰化谓词介入）。

### 1.2 并行链 A：原版 SpySat（`HouseClass::UpdateSpySat 0x508F60`）

```
BuildingType+0x16A5 == 1 且有电存活     [实证 B11]
  ├─ House+0x577A SpySatActive==0 → call 0x577D90 RevealArea3（全图开）  [实证 B12]
  │     └─ 每格 +0x130=0 / +0x134=0 / +0x12C|=0x18     [实证 B9]
  │     └─ House+0x577A = 1
  └─ 否则 → call 0x577AB0 Reshroud（全图重遮）           [实证 B13]
        └─ 每格 +0x130=1 / +0x134=0 / +0x12C&=~0x18    [实证 B10]
        └─ House+0x577A = 0；0x657CE0 全图雷达重建
```

`House+0x577A` 全 `.text` disp32 普查 **9 处**（`0x45726E/0x4572A4/0x4F5C6F/0x509004/0x509019/0x509056/0x50906B/0x50BD12/0x6FB605`）**[实证 B18]**，主写点在 `UpdateSpySat` 尾部与 `DestroyGap` 邻域。现网 `UpdateVisionGrid` **恒写 `House+0x577A=0`**（`blitter_hooks.cpp:1554`）以解除废缝锁死。

### 1.3 并行链 B：SpyPlane Case 8（`0x6CD66F`）

- 同为「雷达扫描」语义，但**不写 Shroud/Cell 迷雾字段** **[实证 B16 / 前证]**；
- 生成侦察机（`0x65EAB0` → `SpawnAircraftEdge 0x4AA440`），用 `Rules+0xC4C/C68` 计数；
- **吃 RNG**（飞机入场边缘点）**[前证 C9]**；与 Case 11 的开图链完全独立。

### 1.4 并行链 C：H-20-C 私有扫窗（未落地）

`ARCHITECTURE_ATLAS.md:4155` 约定：`s_radarSweepExpireFrame[512*512]`（600 帧窗口），**只写 DLL 私有网格、不写引擎 `Cell+0x134`**，产品语义 =「透缝扫描后缝仍在」。**当前 0 实现**（全库 grep `s_radarSweepExpireFrame` 仅文档命中）**[前证 C10]**。

---

## 2. 现网钩覆盖矩阵（有什么 / 缺什么）

| # | 钩/补丁 | 安装点 | 覆盖什么 | 对「雷达扫描超武」缺什么 | 证据 |
|---|---|---|---|---|---|
| 1 | `Hook_RadarPlot_Cell_Proxy` | `0x655D38` 9B（路线 A） | 小地图像素灰化 `(c>>1)&0x7BEF` + 自绘跳过红点循环（敌点隐匿） | **不读扫窗**；无「扫描期临时亮起 / 过期回灰」；开图后由引擎 `IsShrouded` 直接全彩，钩不再介入 | [实证 C5] |
| 2 | `Hook_RadarNativeDecide_Proxy` | `0x655D87` 7B | 引擎减暗判定位改写（`s_fogMasterGate` 门） | 同上，无扫窗语义 | [实证 C6] |
| 3 | `Hook_RadarPending_Proxy` | `0x65719A` 5B | 视野迁移强制小地图全刷（`s_minimapForceRefresh`） | **扫窗开/关不会置 force-refresh** ⇒ 窗口开合可能残留旧像素 | [实证 C7] |
| 4 | `PatchSpySatBuildingTypes` | TYPE 内存（非 .text） | 关 `Bld+0x16A5` 全图恒亮；绑 `Bld+0x16F0=PsychicReveal`；写 `SW+0xB0` CD、`SW+0xF8` 半径 | ① **`+0xF8` 死写**（Case 11 不读，见 §3.1）② 无备份/还原（G-07）③ 无 `MpActive` 旁路（W3）④ 无扫窗表现 | [实证 C3/C4] |
| 5 | P-2.1/2.2/2.3 NOP×6 | `0x568273` / `0x577EC5` / `0x577B60` | 保护 `Cell+0x134` 不被清零 | **三点均未落地**（`gap_psychic_reveal` 定谳）⇒ 扫一次废一片缝 | [前证] |
| 6 | H-20-C 私有扫窗 | — | — | **整层缺失**（无数组、无 Trigger、无谓词合流、无过期回灰） | [前证 C10] |

**覆盖缺口总括**：现网 = 「小地图已灰化」+「SpySat 改绑 PsychicReveal」；缺 = 「扫描是**限时窗口**还是**永久开图**」的表现层与语义层、半径真实控制、gap 保护、TYPE 回滚、联机旁路。

---

## 3. 落地规格（表现层补全 / 开关）

### 3.1 先修死键：`RadarSweepRadiusCells` 无效（P0）

**事实**：Case 11 两次 `RevealArea2` 均 `Rules+0xFEC`（`8B 82 EC 0F 00 00` / `8B 88 EC 0F 00 00`）**[实证 B2/B4]**，且 `RevealArea2` 内 `min(10, radius)` **[前证 C2]**；`SW+0xF8` 全程序仅 INI 加载（`0x6CEBDA`）与鼠标瞄准圈（`0x6DC1C6`）读取 **[前证 C1]**。

⇒ `PatchSpySatBuildingTypes:1412-1413` 写 `SW+0xF8 = RadarSweepRadiusCells` **不改变任何开图半径**；`RadarSweepRadiusCells=16` 时实际仍约 10 格。

**修法（二选一，均为表现/数据层）**：

| 方案 | 做法 | 字节/钩点 | 回滚 | MP |
|---|---|---|---|---|
| **R-a（推荐）** | 改写 **`Rules+0xFEC`**（`0x8871E0` 单例 +0xFEC，i32）为 `RadarSweepRadiusCells`；或在 H-20-C 窗口内用**私有半径**画扫窗 | 数据写；无 .text 补丁 | 备份原 `Rules+0xFEC`，`Remove*` 还原 | TYPE/Rules 不进帧 CRC，但改可见性语义 ⇒ **全端同值** 或联机关 |
| **R-b** | 保留死写，文档与 ini 注释明确「半径以 Rules.PsychicRevealRadius 为准」；删/停用 `RadarSweepRadiusCells` 键 | 无 | 无 | 无新增风险 |

### 3.2 表现层补全：H-20-C 私有扫窗（P0 主方案）

**目标语义**：雷达扫描超武施放后，目标圆域在 **N 帧（默认 600）** 内于世界视图与小地图上「临时可见」；到期自动回灰/回黑；**裂缝计数不动**。

**数据**（DLL 私有，不进档、不进 CRC）：

```cpp
// 网格：512×512，与 s_visionGrid 同址映射
uint32_t s_radarSweepExpireFrame[512 * 512];   // 0 = 无窗口
uint32_t s_radarSweepRadiusCells_eff;          // 真实半径（来自 3.1）
uint32_t s_radarSweepDurationFrames = 600;     // 可 ini：RadarSweepDurationFrames
```

**触发点（不改 Launch 控制流）**：在 **Case 11 收尾音效之后**（`0x6CD7BF` call `0x750E20` 之后、`ret 8` 之前）挂 **5 字节 `jmp` 跳板**，或更稳妥地挂 **`SuperClass::ClickFire 0x6CB920` / Launch 返回后** 由 DLL 侧检测「本帧有 case11 发射」再盖窗。规格给出**双点任选**：

| 触发方案 | 钩点 | 侵入面 | 说明 |
|---|---|---|---|
| **T-a** | `0x6CD7BF` 后（`0x6CD7C4` 处 `mov al,[esp+0x1EC]` 前，5B） | 中（Launch 内部） | 与开图同帧；需保 isPlayer 栈槽 |
> 【W3 勘误 · W3-A6/ISSUE-RADAR-SWEEP-5B】改前：0x6CD7C4` 处 `mov al,[esp+0x1EC]` 前，5B；改后：0x006CD7C4 处指令为 7B (8A 84 24 EC 01 00 00)；依据：ra2youli/gamemd.exe:0x2CD7C4; errata_sync_master_table.md:18 (R-E03); h20c_private_sweep_spec.md:40-43；分级：P0
| **T-b（推荐）** | `SuperClass::Launch 0x6CC390` **函数出口** `0x6CDE36` 汇合处旁路观测 + DLL 侧 `ClickFire` 代理 | 低 | 不碰 case 体；用 `Type+0xB4==11 && IsCharged` 过滤 |

【勘误 2026-09-30 · R-E03 · errata_sync】原文「5B」错误。实测 0x6CD7C4 处指令为 7 字节 mov al,[esp+0x1EC]（8A 84 24 EC 01 00 00）；T-a 必须 7B 补丁（E9+2×90），5B jmp 会切断指令。推荐改挂 T-b（ClickFire 0x6CB920 / Launch 0x6CC390 5B）。权威：h20c_private_sweep_spec.md §T-a 边界勘误。原文保留不删字。

**谓词合流**（三处消费，统一函数，禁止两套逻辑）：

```cpp
// 与 s_visionGrid 同级：当前格是否「直视可见」
inline bool SweepVisible(int idx, uint32_t frame) {
    return s_radarSweepExpireFrame[idx] >= frame;
}
```

1. **世界视图**：`ShouldDrawMobileObject / ShouldDrawBuilding / ShouldDrawBullet / Hook_CellClass_Draw` 四谓词（现 `:984/:1056/:1105/:1141`）——`!visible && SweepVisible` ⇒ 放行（扫描期看见）。
2. **小地图**：`Hook_RadarPlot_Cell_Proxy` 自绘路径（`RadarHook_SelfDrawn`）——`SweepVisible` 时跳过灰化、不跳过红点循环逻辑上应**允许画点**（扫描要看见单位）；过期后回到灰化/隐匿。
3. **过期回灰**：`UpdateVisionGrid` 迁移扫描（`blitter_hooks.cpp:1649` 环）增加「窗口过期」转移 → `s_minimapForceRefresh` 置位 + `s_fogRampFrame[i]=4` 渐变。

**字节/钩点清单（全部可回滚）**：

| ID | 点 | 补丁 | 回滚 | 开关 |
|---|---|---|---|---|
| SW-1 | `0x6CD7C4`（T-a）或 ClickFire 代理（T-b） | 5B `E9 rel32` + 跳板 | 还原 5B | `EnableRadarSweepWindow` |
| SW-2 | 无（纯数据） `s_radarSweepExpireFrame` | — | `memset 0` | 同上 |
| SW-3 | 无新 .text；谓词合流在 DLL 内 | — | 关键即不查 | 同上 |
| SW-4 | （可选）`Rules+0xFEC` 数据写 | 备份/还原 | G-07 同款 | `RadarSweepRadiusCells` |

【勘误 2026-09-30 · R-E03 · errata_sync】原文「5B」错误。实测 0x6CD7C4 处指令为 7 字节 mov al,[esp+0x1EC]（8A 84 24 EC 01 00 00）；T-a 必须 7B 补丁（E9+2×90），5B jmp 会切断指令。推荐改挂 T-b（ClickFire 0x6CB920 / Launch 0x6CC390 5B）。权威：h20c_private_sweep_spec.md §T-a 边界勘误。原文保留不删字。
【勘误 R-E03：T-a 则 7B（E9+2×90）；T-b 才是 5B】

**ini 键**：

```ini
[FogOfWar]
EnableRadarSweepWindow=1        ; 0=回到「永久开图」原版 Case11 语义
RadarSweepDurationFrames=600    ; 扫窗时长（帧），钳 60..3600
RadarSweepRadiusCells=16        ; 真实半径（改 Rules+0xFEC 或仅私有窗），钳 4..30
```

**遥测**：`s_radarSweepWindowsOpened` / `s_radarSweepCellsLit` / `s_radarSweepExpiredCells`（线性递增，严禁恒 0）。

### 3.3 开关矩阵（与既有键关系）

| 键 | 作用 | 与扫窗关系 |
|---|---|---|
| `EnableSpySatRadarSweep` | S1 TYPE 补丁（关全图、绑 PsychicReveal） | 扫窗的**前置**：=1 才有「扫描超武」；=0 时 SW-1 不装 |
| `EnableRadarSweepWindow`（新） | H-20-C 窗口 | =0 ⇒ Case11 原版永久开图（须知 gap 风险） |
| `EnableGapProtection` | P-2.1/2.2/2.3 NOP | =1 且走原版 RevealArea2 时**必须**；走纯私有窗则不必 |
| `EnableMinimapFog` | 小地图灰化 | 与 SW-3 合流；=0 时扫窗在小地图上不可见差异（引擎全彩） |
| `MpStateWrites` / `MpActive()` | 状态写旁路 | SW 层零状态写 ⇒ 不需要；S1/S2/S3 仍需要 |

### 3.4 最小落地包（若不做 H-20-C）

1. **P-2.1** NOP×6 `0x568273`（1×6B，封 22 个 `RevealArea2` caller 的废缝）——字节 `89 99 34 01 00 00` → `90×6` **[实证 B8]**；
2. **G-07** TYPE 四字段备份/`Remove` 还原（`SW+0xB0/+0xF8`、`Bld+0x16A5/+0x16F0`）；
3. **W3** `PatchSpySatBuildingTypes` 入口 `if (MpActive()) return;`；
4. **R-a/R-b** 处理半径死键；
5. 文档声明：无扫窗 ⇒ 扫描 = 永久开图（与原版 SpySat 一致，产品可接受）。

---

## 4. 确定性裁决（Cell 计数 / gap 交叉 / RNG）

| 改动 | 写 Cell？ | gap 计数（`+0x134`） | 吃 RNG？ | 帧 CRC `0x64DAB0` | Checksum v[13] | 裁决 |
|---|---|---|---|---|---|---|
| **H-20-C 私有扫窗** | **否** | **不动** | **否** | 否 | 否 | **SAFE**（纯表现；混联观感分叉可接受） |
| 原版 Case11 `RevealArea2` | 是 `+0x12C/0x130/0x140` | **清 0**（废缝） | **是**（`RevealArea2→0x4837AB`）**[前证 C9]** | 间接（可见性→寻敌→位置） | Cell 进档 | **CONDITIONAL**：必须全端同 DLL + 同 `Rules+0xFEC`；且**禁止**单端发射 |
| **P-2.1 NOP**（保 `+0x134`） | 其余仍写 | **保留** | 仍吃 | 仍间接 | 仍进档 | **CONDITIONAL**：全端同补丁；一端 NOP 一端原版 ⇒ gap 语义分叉 ⇒ **VIOLATION** |
| S1 `SW+0xB0` CD | 否（TYPE 不进档） | 否 | 否（直接） | 间接（`IsCharged` 翻转帧→Launch 帧→RNG 流） | Super 状态进 v[13] | **CONDITIONAL**：全端同 CD 值 |
| S1 `SW+0xF8` 半径 | 否 | 否 | 否 | 否 | 否 | **当前死写**；修正为 `Rules+0xFEC` 后升级为 **CONDITIONAL**（改可见性） |
| S2 Scenario `&=~0x1000` / S3 `House+0x577A=0` | 是（全局/进档） | 间接（解废缝锁） | 否 | 视寻敌 | 是 | **CONDITIONAL** / 混端 **VIOLATION**（`mp_gate_residual` 已裁） |
| 新增局内 `Random/RandomRanged` | — | — | **是** | **是** | **是** | **禁止** |

**gap 交叉专条**：
- `Cell+0x134` 是 **CreateGap `inc` / DestroyGap `dec`** 的引用计数 **[前证]**；`RevealArea2/3/Reshroud` 三处 `mov [reg+0x134], 0` **[实证 B8/B9/B10]** 将其清零后，`ReshroudCell 0x487690` 钳位使该格 **ShroudCounter 永远无法 ≥1** ⇒ 裂缝对该格永久失效，且 `CreateGap` 只在 `GeneratingGap` 跳变时盖印、**不自愈**。
- 因此「雷达扫描是否改 Cell 计数」的答案是：
  - **走原版 `RevealArea2` = 改**（清 `+0x134` + 写探索位）→ 与 gap **强交叉**；
  - **走 H-20-C 私有窗 = 不改** → 与 gap **零交叉**（透缝可见但缝仍在，产品语义更优）。

**RNG 专条**：Case 11 子函数闭包含 `Random`（`superweapon_re.md §10.2` 树：`ShroudRnd = RevealArea2 → 0x4837AB`）**[前证 C9]**。任何使 Launch 发生帧变化的改动（尤其 `SW+0xB0` CD）都会平移 RNG 流。**扫窗本身不新增 RNG 调用**，故表现层安全。

---

## 5. 回滚 / MP / 验收

### 5.1 回滚契约

| 对象 | 备份 | 卸载/关闭动作 |
|---|---|---|
| `0x6CD7C4` 5B（若 T-a） | `s_origCase11Bytes[5]` | `RemoveRadarSweepHooks` 还原 |
| `Rules+0xFEC`（若 R-a） | `s_origPsychicRevealRadius` | 还原原值 |
| TYPE 四字段（G-07） | 首次 `Patch` 前实读 | `RestoreSpySatBuildingTypes` |
| `s_radarSweepExpireFrame` | — | `memset 0`；跨战局重载随 `s_lastFrameUpdated` 回退一并清 |

【勘误 2026-09-30 · R-E03 · errata_sync】原文「5B」错误。实测 0x6CD7C4 处指令为 7 字节 mov al,[esp+0x1EC]（8A 84 24 EC 01 00 00）；T-a 必须 7B 补丁（E9+2×90），5B jmp 会切断指令。推荐改挂 T-b（ClickFire 0x6CB920 / Launch 0x6CC390 5B）。权威：h20c_private_sweep_spec.md §T-a 边界勘误。原文保留不删字。
【勘误 R-E03：T-a 必须 7B，备份 s_origCase11Bytes[7]】（原文 `s_origCase11Bytes[5]` 保留不删字）

### 5.2 MP 策略

| 档位 | 配置 | 判定 |
|---|---|---|
| **混联（对方原版）** | `EnableSpySatRadarSweep=0` 且 `EnableRadarSweepWindow=0` 且 `EnableGapProtection=0` 且 `EnableMinimapFog=0` | 唯一安全；S1/S2/S3/P-2 任一开启 = VIOLATION |
| **全端同 DLL+ini** | 全键同值（含 CD/半径/时长） | 可开 S1+扫窗+P-2.1；仍禁止单端差异化发射 |
| **纯表现增强** | 仅 `EnableRadarSweepWindow=1`（无 S1、无 P-2） | 逻辑零写 ⇒ **SAFE**；但无扫描超武本体，只对已有开图做「限时窗」才有意义 |

### 5.3 验收用例

1. **半径生效**：`RadarSweepRadiusCells=8` 与 `=16` 各施放一次，量小地图亮区直径（修复 R-a 前应无差异 —— 用作死键回归证明）。
2. **窗口过期**：施放后截图 T+0 / T+300 / T+700 帧；T+700 必须回灰/回黑（H-20-C），或保持全彩（原版语义）。
3. **gap 保全**：裂缝覆盖区施放扫描；过期后裂缝仍在（H-20-C）或永久失效（原版+无 P-2.1）。
4. **回滚**：同进程 `EnableRadarSweepWindow` 1→0 或卸载 DLL，TYPE/`Rules+0xFEC`/`.text` 字节回到原值（`audit_bytes.py`）。
5. **MP 遥测**：混联档 3 局无 desync；`s_radarSweep*` 计数在单机档线性递增。

---

## 6. 未决

| # | 问题 | 影响 | 下一步 |
|---|---|---|---|
| U1 | T-a/T-b 触发点的寄存器/栈契约未做 capstone 逐条复核 | 落地补丁边界 | 反汇编 `0x6CD7C4` 窗与 `0x6CB920` ClickFire 尾 |
| U2 | 小地图 `RadarEvent`（`0x65FDD0`）扫描图标是否泄露缝外位置 | 产品 | U7（`radar_minimap_dots`）同源 |
| U3 | `Rules+0xFEC` 是否进帧 CRC / 存档 | R-a 的 MP 面 | 扫 `0x8871E0` 读点与 `RulesClass::Save` |
| U4 | Case 8 SpyPlane 扫描线 `0x65EAB0` 是否也应接入扫窗 | 表现统一 | 待产品 |
| U5 | 同格多对象、扫窗与 `s_everSeenGrid` 优先级 | 建筑常驻可见 vs 扫描临时 | 产品定义 |

---

## 7. 复现

```text
python out/re_work/re_sprint/R_radar_sw/verify_radar_sw_bytes.py
  → verify_bytes_out.txt（14 断言 MATCH / 0 MISMATCH）
对照 out/re_work/re_sprint/R_radar_sw/claims.txt
阅读 docs/re/superweapon_re.md §4/§5/§10、gap_psychic_reveal_deep_dive.md §3、visibility_gap_spysat.md §3.3-3.5
源码侧（只读）ra2render/blitter_hooks.cpp:1392-1451 / 2883-3065
```

---

*文档版本：R-RADAR-SW 静态深潜 · 证据脚本 `verify_radar_sw_bytes.py`（capstone 未用，纯 PE 字节断言；只读 gamemd.exe）*
