# H-20-C 私有扫窗可执行规格（Private Sweep Window）

> **任务**：R-H20C（接 T22 R-RADAR-SW / R-SW-RADIUS 定谳）  
> **性质**：落地规格（可执行）；`gamemd.exe` 只读；本轮**不改** `ra2render/**`  
> **证据目录**：`out/re_work/re_sprint/R_h20c/`（`claims.txt` / `verify_h20c_bytes.py` / `verify_bytes_out.txt`）  
> **exe**：`ra2bench/gamemd.exe` sha256 `73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476`  
> **关联**：`radar_sweep_sw_deep_dive.md` · `sw_radius_deadkey_fix_spec.md` · `radar_hook_routeA_spec.md` · `ARCHITECTURE_ATLAS.md:4155`

---

## 0. 一句话结论

**H-20-C 私有扫窗**是唯一「不改 Cell 计数 / 不吃 RNG」的雷达扫描表现路线（**MP SAFE**）：
`s_radarSweepExpireFrame[512*512]` + 触发点 **T-b** + 三谓词合流 + 过期 `s_minimapForceRefresh`；
键 `EnableRadarSweepWindow` / `RadarSweepDurationFrames` / `RadarSweepRadiusCells`（**死键须修**，见 §4）。

| 裁决面 | H-20-C | 原版 Case11 `RevealArea2` |
|---|---|---|
| 写 Cell（`+0x12C/0x130/0x134/0x140`） | **否** | 是（`+0x134` 清 0 = 废缝） |
| gap 计数 | **不动** | 破坏 |
| 吃 RNG | **否** | 路径本体 0 次（R-SW-RADIUS 复证）；但改可见性可间接影响 |
| 帧 CRC / Checksum v[13] | **否** | 间接 / 进档 |
| 裁决 | **SAFE** | CONDITIONAL（须全端同 DLL + 同 Rules） |

---

## 1. 钩点清单（VA + 行号）

### 1.1 引擎侧钩点（gamemd.exe，全部可回滚）

| ID | 角色 | VA | 原版字节 | 补丁形态 | 侵入面 | 开关 |
|---|---|---|---|---|---|---|
| **SW-1a** | **T-a 触发**（备选） | `0x006CD7C4` | `8A 84 24 EC 01 00 00`（7B，`mov al,[esp+0x1EC]`） | **7B** `E9 rel32` + `90 90` + 跳板回放 7B → `jmp 0x6CD7CB` | 中（Launch case11 体内） | `EnableRadarSweepWindow` |
| **SW-1b** | **T-b 触发（推荐）** | `0x006CB920` ClickFire 入口 **或** `0x006CC390` Launch 入口 | `83 EC 10 53 56 8B F1…` / `81 EC D4 01 00 00 53…` | 5B `E9 rel32` + 跳板；**不碰 case 体** | 低 | 同上 |
| **SW-2** | 私有过期网格 | —（DLL 私有） | — | 纯数据 `s_radarSweepExpireFrame` | 无 | 同上 |
| **SW-3** | 谓词合流 | —（DLL 内） | — | 无新 .text；三处消费共用 `SweepVisible` | 无 | 同上 |
| **SW-4** | 死键半径（可选 R-a） | `RulesClass::Instance*[0x8871E0]` + `0xFEC` | — | **数据写 i32**；无 .text | 低 | `RadarSweepRadiusCells` |
| **SW-5** | 过期强刷 | 复用 `s_minimapForceRefresh` | — | 置位即可（已有 Pending 钩消费） | 无 | 同上 |

> **T-a 边界勘误（本规格定谳）**  
> 旧文写「`0x6CD7C4` 5B」。实测该指令为 **7 字节** `mov al,[esp+0x1EC]`，5B `jmp` 会切断指令。  
> 【W3 勘误 · W3-A6/ISSUE-RADAR-SWEEP-5B】改前：0x6CD7C4` 5B；改后：0x006CD7C4 处指令为 7B (8A 84 24 EC 01 00 00)；依据：ra2youli/gamemd.exe:0x2CD7C4; errata_sync_master_table.md:18 (R-E03); h20c_private_sweep_spec.md:40-43；分级：P0
> **T-a 必须 7B 补丁**（`E9` + 2×`90`），跳板回放 7B 后 `jmp 0x006CD7CB`。  
> 若坚持 5B，只能改挂 T-b（推荐）或另寻 5B 对齐点——**禁止**在 0x6CD7C4 上写 5B。

**T-a 上下文（已字节核验）**

```
0x6CD7BF  E8 5C 36 08 00     call 0x750E20          ; VocClass::PlayIndexAtPos 雷达音效
0x6CD7C4  8A 84 24 EC 01 00 00  mov al,[esp+0x1EC]  ; ★T-a 7B 补丁点
0x6CD7CB  84 C0              test al,al
0x6CD7CD  0F 84 63 06 00 00  jz 0x6CDE36            ; 早退到 Launch 共享尾声
0x6CD7D3  C7 05 A0 09 88 00 FF FF FF  mov dword [0x8809A0], -1  ; isPlayer UI 音效槽
```

**T-b 设计（推荐，低侵入）**

1. **观测点 A**：`SuperClass::ClickFire 0x006CB920` 入口 5B 钩——记录「本帧将发射的 SWType」；
2. **过滤谓词**：`*(int*)(pSWType+0xB4) == 11`（PsychicReveal）且 `*(uint8_t*)(pSuper+0x6F) != 0`（IsCharged）；
3. **观测点 B（可选加强）**：`SuperClass::Launch 0x006CC390` 入口 5B 钩，同谓词确认后置 `s_sweepTriggerPending`；
4. **开窗动作**：不写 case 体；DLL 侧在下一 `UpdateVisionGrid` / 首次消费点开窗。
5. **禁止**只在共享尾声 `0x006CDE36`（`pop edi/esi/ebp/ebx; add esp,0x1D4; ret 8`）开窗——该点无 case id，无法区分 12 路。

### 1.2 DLL 侧钩点（`ra2render/blitter_hooks.cpp` 行号，只读参照）

| 消费点 | 函数 | 行号 | 合流动作 |
|---|---|---|---|
| 世界·机动单位 | `ShouldDrawMobileObject` | `:1689` | `!visible && SweepVisible` ⇒ 放行 |
| 世界·建筑 | `ShouldDrawBuilding` | `:1766` | 同上（everSeen 仍优先生效） |
| 世界·子弹 | `ShouldDrawBullet` | `:1812` | 同上 |
| 世界·格绘制 | `Hook_CellClass_Draw` | `:1888` | `SweepVisible` ⇒ 按直视全彩/不灰化 |
| 小地图自绘 | `RadarHook_SelfDrawn` | `:2736` | `SweepVisible` ⇒ **跳过灰化**、允许红点 |
| 小地图原生减暗 | `RadarHook_NativeDecide` | `:2811` | `SweepVisible` ⇒ 强制 `*pFlag = 0`（不减暗） |
| 过期回灰 | `UpdateVisionGrid` 迁移环 | `:1501` / 环 `:1649-1664` | 过期转移 → `s_minimapForceRefresh=10` + `s_fogRampFrame[i]=4` |
| 帧源 | `ADDR_CURRENT_FRAME` | `ra2render.h:201` = `0x00A8ED84` | 过期比较基准 |
| 网格映射 | `s_visionGrid[512*512]` | `:108` | 同址映射 `idx = y*512+x` |
| 渐变 | `s_fogRampFrame[512*512]` | `:113` | 过期回灰渐变 4 帧 |
| 强刷 | `s_minimapForceRefresh` | `:115` / 写 `:1521,:1678` / 读 `:2949` | 过期/开窗置位 |
| LoadConfig | `EnableSpySatRadarSweep` | `:534-535` | 扫窗前置闸 |
| LoadConfig | `RadarSweepCooldownFrames` | `:537-538` | 活键（`SW+0xB0`） |
| LoadConfig | `RadarSweepRadiusCells` | `:540-542` | **死键**，按 §4 修 |
| TYPE 补丁 | `PatchSpySatBuildingTypes` | `:1392-1451`；`+0xF8` 写 `:1412-1413` | 死写现场 |
| 安装/卸载 | `InstallRadarFogHooks` / `RemoveRadarFogHooks` | `:2962` / `:3046` | SW-1 回滚并入 |

---

## 2. 数据与谓词（合流，禁止两套逻辑）

### 2.1 私有数据（DLL 静态；不进档、不进 CRC、不进 Checksum）

```cpp
// 与 s_visionGrid 同址映射：idx = (y << 9) + x
uint32_t s_radarSweepExpireFrame[512 * 512];   // 0 = 无窗口；否则 = 过期帧号
uint32_t s_radarSweepRadiusCells_eff;          // 私有半径（R-c）；见 §4
uint32_t s_radarSweepDurationFrames = 600;     // ini: RadarSweepDurationFrames
uint32_t s_radarSweepWindowsOpened = 0;        // 遥测
uint32_t s_radarSweepCellsLit = 0;
uint32_t s_radarSweepExpiredCells = 0;
```

### 2.2 统一谓词（唯一实现）

```cpp
// 当前格是否「扫窗期临时直视可见」
inline bool SweepVisible(int idx, uint32_t frame) {
    return idx >= 0 && idx < 512 * 512
        && s_radarSweepExpireFrame[idx] >= frame;
}

// 开窗：以 (cx,cy) 为圆心、s_radarSweepRadiusCells_eff 为半径盖印
void OpenSweepWindow(int cx, int cy) {
    const uint32_t frame = *reinterpret_cast<const uint32_t*>(ADDR_CURRENT_FRAME); // 0xA8ED84
    const uint32_t expire = frame + s_radarSweepDurationFrames;
    const int r = static_cast<int>(s_radarSweepRadiusCells_eff);
    for (int dy = -r; dy <= r; ++dy) {
        for (int dx = -r; dx <= r; ++dx) {
            if (dx * dx + dy * dy > r * r) continue;
            const int x = cx + dx, y = cy + dy;
            if (x < 0 || x >= 512 || y < 0 || y >= 512) continue;
            const int idx = y * 512 + x;
            if (s_radarSweepExpireFrame[idx] == 0) s_radarSweepCellsLit++;
            s_radarSweepExpireFrame[idx] = expire;
        }
    }
    s_radarSweepWindowsOpened++;
    s_minimapForceRefresh = 10;   // 开窗即强刷，避免残留旧像素
}
```

### 2.3 三处消费合流

| # | 消费面 | 判定 | 行号 |
|---|---|---|---|
| 1 | **世界视图** | `!visible && SweepVisible(idx, frame)` ⇒ 视为直视（放行绘制/不剔除） | `:1689/:1766/:1812/:1888` |
| 2 | **小地图** | `SweepVisible` ⇒ 跳过 `(c>>1)&0x7BEF` 灰化；红点循环**允许画点** | `:2736`（自绘）/`:2811`（原生减暗驱动） |
| 3 | **过期回灰** | `UpdateVisionGrid` 迁移环：`expire>0 && expire < frame` ⇒ 清 0、`s_fogRampFrame[i]=4`、`s_minimapForceRefresh=10` | `:1649-1664` |

**优先级（U5 裁决）**  
`ShouldDrawBuilding` 的 `everSeen`（`:1798`）**优先于**扫窗：扫窗只是「临时加可见」，不撤销「看见过即常驻」。  
同格多对象：任一对象落在 `SweepVisible` 格即对该对象放行；不写 `s_everSeenGrid`（扫窗不产生永久侦察章）。

---

## 3. 与路线 A 三钩兼容

路线 A 已装三钩（`InstallRadarFogHooks :2962`），H-20-C **不得覆盖、不得二次改写**：

| 钩 | VA / 长度 | 源码 | H-20-C 合流点 | 兼容约束 |
|---|---|---|---|---|
| H1 `Hook_RadarPlot_Cell_Proxy` | `0x655D38` **9B** | `:2883-2907` | `RadarHook_SelfDrawn` 内加 `SweepVisible` 短路 | 只改 C++ 谓词，**不动 9B 补丁** |
| H2 `Hook_RadarNativeDecide_Proxy` | `0x655D87` **7B** | `:2915-2937` | `RadarHook_NativeDecide` 内 `SweepVisible ⇒ *pFlag=0` | 只改 C++ 谓词，**不动 7B 补丁** |
| H3 `Hook_RadarPending_Proxy` | `0x65719A` **5B** | `:2942-2959` | 复用 `s_minimapForceRefresh`（`:2949` 已读） | **零改动**；开窗/过期只置位 |

**红线**
1. H-20-C 的 SW-1 只允许挂在 `0x6CD7C4`（T-a 7B）或 `0x6CB920/0x6CC390`（T-b 5B）；**禁止**触碰 `0x655D38 / 0x655D87 / 0x65719A`。
2. `RemoveRadarFogHooks :3046` 还原三钩时，必须先卸 SW-1（或 SW-1 独立 `RemoveRadarSweepHooks`），避免跳板悬空。
3. `RadarFogGuardMode=3`（原生减暗，现默认）时，小地图合流走 H2 路径而非自绘；H-20-C 在 **两条路径都要查 `SweepVisible`**。

---

## 4. 死键修复：`RadarSweepRadiusCells`（二选一，规格同时给出）

**定谳（R-SW-RADIUS）**：`PatchSpySatBuildingTypes:1412-1413` 写 `SW+0xF8 = RadarSweepRadiusCells` 是 **死写**（12/12 发射 case 均不读 `+0xF8`；唯一活消费 = 鼠标瞄准圈 `fld [edi+0xF8] @ 0x6DC1C6`）。  
PsychicReveal 真实开图半径 = `Rules+0xFEC`（i32），且被 `RevealArea2` **`min(10,·)` @ `0x567A4A`** 夹紧。

### 方案 R-c · 私有半径（**H-20-C 首选**）

| 项 | 值 |
|---|---|
| 做法 | **不动引擎半径**；扫窗圆域用 DLL 私有 `s_radarSweepRadiusCells_eff` |
| 数据源 | `g_radarSweepRadiusCells`（`LoadConfig :540-542`，clamp 4..64） |
| 可达域 | **1..64，无 `min(10)`** |
| .text | 无 |
| 写 Cell | 无 |
| MP | **SAFE**（纯表现） |
| 回滚 | 卸载即无 |

### 方案 R-a · 改源 `Rules+0xFEC`（仅当同时走原版 `RevealArea2` 时）

| 项 | 值 |
|---|---|
| 做法 | `*(int32_t*)(RulesInstance + 0xFEC) = clamp(RadarSweepRadiusCells, 1, 10)`；`RulesInstance = *(void**)0x8871E0` |
| 类型陷阱 | `SW+0xF8` = **float**，`Rules+0xFEC` = **i32**。**禁止**把发射半径改读 `SW+0xF8`（IEEE 位型当整数 ⇒ 爆炸半径） |
| 可达域 | **1..10**（仍被 `min(10,·)` 夹） |
| .text | 无（纯数据写）；若要 >10 须另开 R-a+ 解夹 `0x567A4A`（16B，**默认禁止**，影响 22 个 caller） |
| MP | CONDITIONAL（改可见性 ⇒ 全端同值） |
| 回滚 | 备份 `s_origPsychicRevealRadius`，`Remove*` 还原 |

### 本规格裁决

```
H-20-C 落地 = R-c 私有半径（必做）
             + R-b 死键文档化（必做：ini 注释/日志改「瞄准圈 UI-only」）
             + R-a 仅当产品同时启用原版 RevealArea2 开图时叠加（可选）
             + R-a+ 解夹紧：默认 0，非本包范围
```

`SW+0xF8` 写保留与否：
- **保留**（瞄准圈与私有窗半径一致）——可接受，但日志**禁止**再打「探测半径生效」；
- **或停写**并改注释为 UI-only。二者择一，不得继续声称「开图半径」。

---

## 5. ini 键契约

```ini
[FogOfWar]
EnableSpySatRadarSweep=1        ; 前置：=1 才有扫描超武本体；=0 时 SW-1 不装
EnableRadarSweepWindow=1        ; 0=回到「永久开图」原版 Case11 语义（须知 gap 风险）
RadarSweepDurationFrames=600    ; 扫窗时长（帧），钳 60..3600
RadarSweepRadiusCells=16        ; 私有窗半径（R-c），钳 4..64；见 §4
RadarSweepCooldownFrames=600    ; 活键：写 SW+0xB0；改 CD 平移其它 case RNG（与本包分开评估）
```

| 键 | 状态 | =0 | =1 / 值域 |
|---|---|---|---|
| `EnableRadarSweepWindow`（新） | 进程级 | 无扫窗，Case11 原版永久开图 | 私有窗 |
| `RadarSweepDurationFrames`（新） | 进程级 | — | 钳 60..3600，默认 600 |
| `RadarSweepRadiusCells` | **死键待修** | — | R-c 后活（私有窗）；R-a 后活（≤10） |
| `EnableSpySatRadarSweep` | 活键 | 不装 TYPE/扫窗 | 装 |
| `EnableMinimapFog` | 活键 | 小地图不灰化 ⇒ 扫窗在小地图差异不可见 | 合流可见 |
| `EnableGapProtection` | 活键 | 原版 RevealArea2 需要 | **纯 R-c 时不必** |

**LoadConfig 落点**：紧随 `:540-542` 之后新增两键读取；clamp 与日志口径按上表。

---

## 6. 回滚契约

| 对象 | 备份 | 卸载/关闭动作 | 验证 |
|---|---|---|---|
| T-a `0x6CD7C4` 7B | `s_origCase11Bytes[7]` | `RemoveRadarSweepHooks` 还原 7B | `verify_h20c_bytes.py` / `audit_bytes.py` |
| T-b `0x6CB920` 或 `0x6CC390` 5B | `s_origClickFireBytes[5]` | 同上还原 5B | 同上 |
| `s_radarSweepExpireFrame` | — | `memset 0`；跨战局随 `:1515` 帧回退一并清 | 遥测归零 |
| `Rules+0xFEC`（若 R-a） | `s_origPsychicRevealRadius` | 还原原值 | 读回比对 |
| TYPE 四字段（G-07，既有） | 首次 `Patch` 前实读 | `RestoreSpySatBuildingTypes` | 既有 |
| 路线 A 三钩 | 既有 `s_orig*Bytes` | **不动**；由 `RemoveRadarFogHooks :3046` 管 | H1/H2/H3 字节 MATCH |

**同进程开关**：`EnableRadarSweepWindow` 1→0 ⇒ 立即 `memset` 网格 + 还原 SW-1 字节；三钩保持。

---

## 7. MP / 确定性

| 档位 | 配置 | 判定 |
|---|---|---|
| **混联（对方原版）** | `EnableSpySatRadarSweep=0` 且 `EnableRadarSweepWindow=0` 且 `EnableGapProtection=0` 且 `EnableMinimapFog=0` | 唯一安全；任一开启 = VIOLATION |
| **全端同 DLL+ini** | 全键同值（含 CD/半径/时长） | 可开 S1+扫窗；仍禁止单端差异化发射 |
| **纯表现增强** | 仅 `EnableRadarSweepWindow=1`（无 S1、无 P-2） | 逻辑零写 ⇒ **SAFE**；观感混联分叉可接受 |

**红线**
1. H-20-C **禁止**新增 `ScenarioClass::Random/RandomRanged`。
2. H-20-C **禁止**写 `Cell+0x12C/0x130/0x134/0x140`（尤其 `+0x134` gap 计数）。
3. `SW+0xB0` CD 改写会平移其它 case 的 Launch 帧 ⇒ RNG 流；与扫窗包**分开开关**。
4. 私有网格/半径/时长 **不进帧 CRC、不进 .SAV、不进 Checksum v[13]**。

---

## 8. 验收用例

| # | 步骤 | 期望 | 档 |
|---|---|---|---|
| A1 | 死键回归：`RadarSweepRadiusCells=8` 与 `=16` 各施放（R-a 未装） | 原版开图亮区**无差异**；私有窗直径随键变 | R-c |
| A2 | 窗口过期：施放后截 T+0 / T+300 / T+700 帧 | T+0/T+300 亮；**T+700 回灰/回黑** | H-20-C |
| A3 | gap 保全：裂缝覆盖区施放扫描 | 过期后**裂缝仍在**（`Cell+0x134` 未清） | H-20-C |
| A4 | 三谓词合流：窗内敌方单位/建筑/子弹 | 世界视图可见；小地图不灰化、有红点 | 合流 |
| A5 | 过期强刷：窗过期后 10 帧内 | 小地图无残留亮像素（`s_minimapForceRefresh` 生效） | H3 |
| A6 | 路线 A 回归：灰化/减暗/强刷 | H1/H2/H3 行为与装扫窗前一致（窗内除外） | 兼容 |
| A7 | 回滚：同进程 `EnableRadarSweepWindow` 1→0 或卸载 DLL | SW-1 字节 MATCH 原版；三钩仍 MATCH；`Rules+0xFEC` 还原 | 回滚 |
| A8 | 遥测 | `s_radarSweepWindowsOpened/CellsLit/ExpiredCells` 线性递增，**严禁恒 0** | 遥测 |
| A9 | MP 遥测 | 混联档 3 局无 desync | MP |
| A10 | 字节门 | `python out/re_work/re_sprint/R_h20c/verify_h20c_bytes.py` | **14 MATCH / 0 MISMATCH** | 静态 |

---

## 9. 最小落地顺序（实现者 checklist）

1. LoadConfig 新增 `EnableRadarSweepWindow` / `RadarSweepDurationFrames`（`:540` 后）；`RadarSweepRadiusCells` 改注释口径。
2. 定义私有网格 + `SweepVisible` + `OpenSweepWindow`（§2）。
3. 装 **T-b**（推荐）：ClickFire/Launch 入口 5B + 谓词过滤 + 开窗；或 T-a 7B（禁止 5B）。
4. 三处合流：`:1689/:1766/:1812/:1888` → `:2736/:2811` → `:1649` 过期环。
5. 过期/开窗置 `s_minimapForceRefresh=10`。
6. （可选）R-a 写 `Rules+0xFEC`；（必做）R-b 死键文档/日志勘误。
7. `RemoveRadarSweepHooks` + 与 `RemoveRadarFogHooks` 的卸载顺序。
8. 跑 A1–A10；`verify_h20c_bytes.py` 保持 14/14。

---

## 10. 未决（落地前须闭环）

| # | 问题 | 影响 | 下一步 |
|---|---|---|---|
| U1 | T-a 7B / T-b 5B 的寄存器/栈契约未做 capstone 逐条复核 | 补丁边界 | 反汇编 `0x6CD7C4` 窗与 `0x6CB920` / `0x6CC390` 序言 |
| U2 | 小地图 `RadarEvent`（`0x65FDD0`）扫描图标是否泄露缝外位置 | 产品 | 与 `radar_minimap_dots` 同源 |
| U3 | `Rules+0xFEC` 是否进帧 CRC / 存档 | R-a 的 MP 面 | 扫 `0x8871E0` 读点与 `RulesClass::Save` |
| U4 | Case 8 SpyPlane 扫描线 `0x65EAB0` 是否接入扫窗 | 表现统一 | 待产品 |
| U5 | 同格 `everSeen` vs 扫窗优先级 | 已裁：`everSeen` 优先 | 实现按 §2.3 |
| U6 | T-a 指令长度 7B（旧文 5B）勘误是否波及其它文档 | 文档一致性 | 台账/ATLAS 勘误（本包不写） |

---

## 11. 复现

```text
python out/re_work/re_sprint/R_h20c/verify_h20c_bytes.py
  → verify_bytes_out.txt（14 MATCH / 0 MISMATCH）
对照 out/re_work/re_sprint/R_h20c/claims.txt
阅读 docs/re/radar_sweep_sw_deep_dive.md · sw_radius_deadkey_fix_spec.md · radar_hook_routeA_spec.md
源码侧（只读）ra2render/blitter_hooks.cpp:1392-1451 / 1501-1680 / 1689-1850 / 2736-3058
```

---

*文档版本：R-H20C 可执行规格 · 证据脚本 `verify_h20c_bytes.py`（PE 字节断言；只读 gamemd.exe）*
