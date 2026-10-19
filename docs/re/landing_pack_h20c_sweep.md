# ZCode 落地卡 · H-20-C 私有扫窗（Private Sweep Window）

> **卡号**：`ZC-H20C-SWEEP` · **优先级**：P0（雷达扫描表现唯一 MP SAFE 路线）  
> **执行方**：ZCode（真机/补丁安装唯一写者）· **起草**：MiMo（R-H20C 静态定谳，T47）  
> **上游**：`docs/re/h20c_private_sweep_spec.md`（R-H20C）· 证据 `out/re_work/re_sprint/R_h20c/`（`claims.txt` / `verify_h20c_bytes.py` / `verify_bytes_out.txt` **14 MATCH / 0 MISMATCH**）  
> **格式对齐**：`docs/re/landing_pack_gap_p21.md`  
> **本卡范围**：**仅 H-20-C 私有扫窗**（T-b 触发 + 三谓词合流 + R-c 私有半径 + 开关默认 0）。R-a `Rules+0xFEC` / R-a+ 解夹紧 / SpyPlane 线 **本卡不做**。  
> **证据基线**：`gamemd.exe` 1.001 · SHA-256 `73201CC021497C9567742F718BF1DC78C22E9AE16C7E7365354B65F3FCF67476` · ImageBase `0x00400000` · `file_off = VA − 0x00400000`  
> 【W3 勘误 E-W3-01】原句 `FileOffset = VA − 0x400000` 仅在 `.text/.rdata/.data` 成立；
> 通用式为 `FileOffset = 段.PointerToRawData + (VA − 段.VirtualAddress)`，
> 本镜像 `.rsrc`/`.detour` 为 `VA − 0x6FC000`。依据：out/re_work/_lead_baseline/W3/LEAD_ERRATUM_E-W3-01_fileoffset_rule.md；分级：[实证]
> **写作用域**：本文件 + `out/re_work/re_sprint/R_h20c_card/**`。**只读** `ra2render/**`、`gamemd.exe`、`tools/**`、台账、看板。

---

## 0. 一句话

在 DLL 私有网格 `s_radarSweepExpireFrame[512*512]` 上盖印「有期限的临时直视窗」，由 **T-b 钩**（ClickFire `0x6CB920` / Launch `0x6CC390`，过滤 `Type+0xB4==11`）触发；三谓词合流放行绘制/不灰化；**0 Cell 写 / 0 RNG / 0 CRC**，**MP SAFE**。开关 `EnableRadarSweepWindow` **默认 0**（零行为变化）。

---

## 1. 执行表

### 1.1 触发钩（二选一；推荐 T-b；禁止在共享尾声开窗）

| 项 | **T-b（推荐）** | T-a（备选，仅当 T-b 不可用） |
|---|---|---|
| **步骤 ID** | `SW-1b` | `SW-1a` |
| **VA** | `0x006CB920` ClickFire 入口 **或** `0x006CC390` Launch 入口 | `0x006CD7C4` |
| **文件偏移** | `0x2CB920` / `0x2CC390` | `0x2CD7C4` |
| **原字节** | `83 EC 10 53 56 8B F1…` / `81 EC D4 01 00 00 53…` | `8A 84 24 EC 01 00 00`（**7B** `mov al,[esp+0x1EC]`） |
| **补丁形态** | **5B** `E9 rel32` + 跳板回放序言 → 回跳 | **7B** `E9 rel32` + `90 90` + 跳板回放 7B → `jmp 0x6CD7CB` |
| **改动长度** | 5B（序言对齐，不碰 case 体） | **必须 7B**（旧文「5B」已勘误；5B 会切断指令，**禁止**） |
| **过滤谓词** | `*(int*)(pSWType+0xB4) == 11`（PsychicReveal）且 `*(uint8_t*)(pSuper+0x6F) != 0`（IsCharged） | 同左（case11 体内已隐含） |
| **开窗动作** | 置 `s_sweepTriggerPending`；DLL 侧下一消费点 `OpenSweepWindow` | 同左 |
| **侵入面** | 低（入口序言） | 中（Launch case11 体内） |
| **备份** | `s_origClickFireBytes[5]` | `s_origCase11Bytes[7]` |

**禁止点（红线）**：共享尾声 `0x006CDE36`（`pop edi/esi/ebp/ebx; add esp,0x1D4; ret 8`）**禁止**作为唯一开窗点——12 case 汇合、无 case id，无法区分 PsychicReveal。

**T-a 上下文窗（安装前后自检，共 16B）**：

| VA | 原字节 | 说明 |
|---|---|---|
| `0x6CD7BF` | `E8 5C 36 08 00` | `call 0x750E20` VocClass 雷达音效 |
| `0x6CD7C4` | `8A 84 24 EC 01 00 00` | ★ **T-a 7B 补丁点**（`mov al,[esp+0x1EC]`） |
| `0x6CD7CB` | `84 C0` | `test al,al`（跳板回跳目标） |
| `0x6CD7CD` | `0F 84 63 06 00 00` | `jz 0x6CDE36` 早退 |

### 1.2 谓词合流（唯一实现，禁止两套逻辑）

私有数据（DLL 静态；**不进档 / 不进 CRC / 不进 Checksum**）：

```cpp
uint32_t s_radarSweepExpireFrame[512 * 512]; // idx = y*512+x；0=无窗，否则=过期帧
uint32_t s_radarSweepRadiusCells_eff;        // R-c 私有半径，clamp 4..64
uint32_t s_radarSweepDurationFrames = 600;   // clamp 60..3600
// SweepVisible(idx,frame) = idx∈[0,512*512) && s_radarSweepExpireFrame[idx] >= frame
// OpenSweepWindow(cx,cy)：圆域盖印 expire=frame+duration；置 s_minimapForceRefresh=10
```

| # | 消费面 | 合流判定 | 源码行（`blitter_hooks.cpp`，只读参照） |
|---|---|---|---|
| 1 | 世界·机动单位 | `!visible && SweepVisible` ⇒ 放行 | `:1689` `ShouldDrawMobileObject` |
| 2 | 世界·建筑 | 同上；**`everSeen` 优先**（`:1798`），扫窗不撤销常驻 | `:1766` `ShouldDrawBuilding` |
| 3 | 世界·子弹 | `!visible && SweepVisible` ⇒ 放行 | `:1812` `ShouldDrawBullet` |
| 4 | 世界·格绘制 | `SweepVisible` ⇒ 全彩/不灰化 | `:1888` `Hook_CellClass_Draw` |
| 5 | 小地图·自绘 | `SweepVisible` ⇒ 跳过灰化、允许红点 | `:2736` `RadarHook_SelfDrawn` |
| 6 | 小地图·原生减暗 | `SweepVisible` ⇒ 强制 `*pFlag = 0` | `:2811` `RadarHook_NativeDecide` |
| 7 | 过期回灰 | `expire>0 && expire<frame` ⇒ 清 0 + `s_fogRampFrame[i]=4` + `s_minimapForceRefresh=10` | `:1501` / 环 `:1649-1664` |
| 8 | 帧源 | `ADDR_CURRENT_FRAME = 0x00A8ED84` | `ra2render.h:201` |

**U5 裁决**：`everSeen` 优先于扫窗；扫窗只「临时加可见」，不写 `s_everSeenGrid`（无永久侦察章）。  
**双路径**：`RadarFogGuardMode=3`（默认，原生减暗）走 H2；自绘走 H1。**两条路径都要查 `SweepVisible`**。

### 1.3 路线 A 三钩零改写（兼容红线）

| 钩 | VA / 长度 | 原版字节 | H-20-C 动作 | 约束 |
|---|---|---|---|---|
| H1 `Hook_RadarPlot_Cell_Proxy` | `0x655D38` **9B** | `89 44 24 28 A1 50 35 B7 00` | 仅 C++ 谓词加 `SweepVisible` 短路 | **不动 9B 补丁** |
| H2 `Hook_RadarNativeDecide_Proxy` | `0x655D87` **7B** | `8B 47 04 89 6C 24 14` | 仅 C++ 谓词 `SweepVisible ⇒ *pFlag=0` | **不动 7B 补丁** |
| H3 `Hook_RadarPending_Proxy` | `0x65719A` **5B** | `E8 91 93 00 00` | 复用 `s_minimapForceRefresh`（`:2949` 已读） | **零改动** |

**红线**：SW-1 只允许挂 `0x6CD7C4`（T-a 7B）或 `0x6CB920/0x6CC390`（T-b 5B）；**禁止触碰** `0x655D38 / 0x655D87 / 0x65719A`。卸载顺序：先卸 SW-1（`RemoveRadarSweepHooks`），再 `RemoveRadarFogHooks :3046`，避免跳板悬空。
> 【W3 勘误 · W3-A6/ISSUE-RADAR-SWEEP-5B】改前：0x6CD7C4`（T-a 7B）或 `0x6CB920/0x6CC390`（T-b 5B；改后：0x006CD7C4 处指令为 7B (8A 84 24 EC 01 00 00)；依据：ra2youli/gamemd.exe:0x2CD7C4; errata_sync_master_table.md:18 (R-E03); h20c_private_sweep_spec.md:40-43；分级：P0

---

## 2. 安装前置（全部 PASS 才允许写）

| # | 检查 | 期望 | 失败则 |
|---|---|---|---|
| G0.1 | 目标文件 SHA-256 | `73201CC0…F67476` | **拒绝安装** |
| G0.2 | T-b 首 5B @ `0x6CB920` 或 `0x6CC390` | `83 EC 10 53 56…` / `81 EC D4 01 00 00…` | 若已是 `E9`：报告「已打」并停手上报；其它：**拒绝** |
| G0.3 | T-a 首 7B @ `0x6CD7C4`（若走备选） | `8A 84 24 EC 01 00 00` | 若已是 `E9`：同上停手；其它：**拒绝** |
| G0.4 | 路线 A 三钩现状 | 由 `InstallRadarFogHooks` 管；H-20-C **不写** | — |
| G0.5 | `EnableRadarSweepWindow` | 显式 `1` 才装 SW-1 | **默认 0 = 不装（零行为变化）** |
| G0.6 | 前置闸 `EnableSpySatRadarSweep` | `=0` 时 SW-1 不装 | 默认不装 |
| G0.7 | `.text` 可写性/映像基址 | PE32 / base `0x400000` | 拒绝 |

**Q1 真机首字节（安装前）**：读 T-b（或 T-a）首字节 → 原版序言 = 未打 / `E9` = 已有外部补丁（**停手上报，禁止覆盖未知安装者**）。

---

## 3. 死键 R-c · 开关 · 遥测 · 回滚

### 3.1 死键修复 = 方案 R-c（本卡必做）

| 项 | 值 |
|---|---|
| **定谳** | `PatchSpySatBuildingTypes:1412-1413` 写 `SW+0xF8 = RadarSweepRadiusCells` 是**死写**（12/12 Launch case 不读 `+0xF8`；唯一活消费 = 鼠标瞄准圈 `fld [edi+0xF8] @ 0x6DC1C6`，**[勘误]** 旧文 `0x6DC1C8` 为 disp32 中段） |
| **做法** | **不动引擎半径**；扫窗圆域用 DLL 私有 `s_radarSweepRadiusCells_eff` |
| **数据源** | `LoadConfig :540-542` 读 `RadarSweepRadiusCells`，clamp **4..64** |
| **可达域** | **1..64，无 `min(10)`**（对照 `RevealArea2` 夹紧 `0x567A4A`） |
| **.text** | 无 |
| **类型陷阱** | `SW+0xF8` = **float**；`Rules+0xFEC` = **i32**。**禁止**把发射半径改读 `SW+0xF8` |
| **R-b 文档化（必做）** | ini 注释/日志改「瞄准圈 UI-only」；**禁止**再打「探测半径生效」 |
| **R-a（本卡不做）** | 写 `Rules+0xFEC` 仅当产品同时启用原版 `RevealArea2` 开图；clamp 1..10；留后续卡 |

### 3.2 开关（ini，`[FogOfWar]`）

| 键 | 默认 | 语义 |
|---|---|---|
| `EnableRadarSweepWindow`（新） | **`0`** | `1` = 私有扫窗 + 装 SW-1；`0` = 不装（回原版 Case11 永久开图语义，须知 gap 风险） |
| `RadarSweepDurationFrames`（新） | `600` | 扫窗时长（帧），钳 **60..3600** |
| `RadarSweepRadiusCells` | `16` | R-c 私有窗半径，钳 **4..64**（死键修复后活） |
| `EnableSpySatRadarSweep` | 既有 | 前置闸；`=0` 时 SW-1 不装 |
| `RadarSweepCooldownFrames` | 既有活键 | 写 `SW+0xB0`；**与本包分开开关**（改 CD 平移其它 case RNG） |

**同进程开关**：`EnableRadarSweepWindow` 1→0 ⇒ 立即 `memset` 网格 + 还原 SW-1 字节；三钩保持。

### 3.3 遥测（只读计数，禁止热路径膨胀）

| 计数器 | 含义 | 验收 |
|---|---|---|
| `s_radarSweepWindowsOpened` | 开窗次数 | 线性递增，**严禁恒 0** |
| `s_radarSweepCellsLit` | 点亮格数 | 同上 |
| `s_radarSweepExpiredCells` | 过期清格数 | 同上 |

### 3.4 回滚

| 对象 | 备份 | 卸载/关闭动作 | 验证 |
|---|---|---|---|
| T-b `0x6CB920` 或 `0x6CC390` 5B | `s_origClickFireBytes[5]` | `RemoveRadarSweepHooks` 还原 5B | `verify_h20c_bytes.py` / `audit_bytes.py` |
| T-a `0x6CD7C4` 7B（若装） | `s_origCase11Bytes[7]` | 同上还原 7B | 同上 |
| `s_radarSweepExpireFrame` | — | `memset 0`；跨战局随 `:1515` 帧回退一并清 | 遥测归零 |
| 路线 A 三钩 | 既有 `s_orig*Bytes` | **不动**；由 `RemoveRadarFogHooks :3046` 管 | H1/H2/H3 字节 MATCH |

1. **软**：`EnableRadarSweepWindow=0` + 重启/重载 DLL（安装态 init 一次读）。  
2. **硬**：`memcpy` 还原备份字节。  
3. **卸载顺序**：先 `RemoveRadarSweepHooks`，后 `RemoveRadarFogHooks`。

---

## 4. 确定性红线（0 Cell / 0 RNG / 0 CRC · MP SAFE）

| 档位 | 配置 | 判定 |
|---|---|---|
| **混联（对方原版）** | 四键全 0（`EnableSpySatRadarSweep` / `EnableRadarSweepWindow` / `EnableGapProtection` / `EnableMinimapFog`） | 唯一安全；任一开启 = VIOLATION |
| **全端同 DLL+ini** | 全键同值（含 CD/半径/时长） | 可开 S1+扫窗；仍禁止单端差异化发射 |
| **纯表现增强** | 仅 `EnableRadarSweepWindow=1` | 逻辑零写 ⇒ **SAFE**；观感混联分叉可接受 |

**红线（违者 = 本卡失败）**：

1. **0 Cell 写**：禁止写 `Cell+0x12C / +0x130 / +0x134 / +0x140`（尤其 `+0x134` gap 计数，锚点 `0x568273` 保持原版）。
2. **0 RNG**：禁止新增 `ScenarioClass::Random / RandomRanged`。
3. **0 CRC**：私有网格/半径/时长 **不进帧 CRC、不进 .SAV、不进 Checksum v[13]**。
4. `SW+0xB0` CD 改写会平移其它 case 的 Launch 帧 ⇒ RNG 流；与扫窗包**分开开关**。

---

## 5. 真机验收用例（A1–A10）

| ID | 步骤 | 期望 | 档 |
|---|---|---|---|
| **A1** | 死键回归：`RadarSweepRadiusCells=8` 与 `=16` 各施放（R-a 未装） | 原版开图亮区**无差异**；私有窗直径随键变 | R-c |
| **A2** | 窗口过期：施放后截 T+0 / T+300 / T+700 帧 | T+0/T+300 亮；**T+700 回灰/回黑** | H-20-C |
| **A3** | gap 保全：裂缝覆盖区施放扫描 | 过期后**裂缝仍在**（`Cell+0x134` 未清） | H-20-C |
| **A4** | 三谓词合流：窗内敌方单位/建筑/子弹 | 世界视图可见；小地图不灰化、有红点 | 合流 |
| **A5** | 过期强刷：窗过期后 10 帧内 | 小地图无残留亮像素（`s_minimapForceRefresh` 生效） | H3 |
| **A6** | 路线 A 回归：灰化/减暗/强刷 | H1/H2/H3 行为与装扫窗前一致（窗内除外） | 兼容 |
| **A7** | 回滚：同进程 `EnableRadarSweepWindow` 1→0 或卸载 DLL | SW-1 字节 MATCH 原版；三钩仍 MATCH；私有网格清零 | 回滚 |
| **A8** | 遥测 | `WindowsOpened/CellsLit/ExpiredCells` 线性递增，**严禁恒 0** | 遥测 |
| **A9** | MP 遥测 | 混联档 3 局无 desync | MP |
| **A10** | 字节门 | `python out/re_work/re_sprint/R_h20c/verify_h20c_bytes.py` | **14 MATCH / 0 MISMATCH** | 静态 |

**禁止把「没崩」当成功**：A2/A3 必须有截帧或计数证据；A8 遥测恒 0 = 失败。

---

## 6. 风险（执行方必读）

| ID | 风险 | 要求 |
|---|---|---|
| R-1 | T-a 误用 5B 切断指令 | **T-a 必须 7B**（`E9+90+90`）；优先走 T-b |
| R-2 | 只在 `0x6CDE36` 开窗 ⇒ 12 case 误触发 | 禁止；必须带 `Type+0xB4==11` 过滤 |
| R-3 | 覆盖路线 A 三钩 | 禁止触碰 `0x655D38/0x655D87/0x65719A`；只改 C++ 谓词 |
| R-4 | 卸载顺序错误 ⇒ 跳板悬空 | 先 SW-1 后三钩 |
| R-5 | `SW+0xF8` float 当 i32 ⇒ 爆炸半径 | 本卡只用 R-c 私有半径；不读 `SW+0xF8` 当整数 |
| R-6 | 混端 DESYNC | 本卡纯表现 = SAFE；若叠加 R-a/CD 改写则全端同值 |
| R-7 | 外部安装者 | G0.2/Q1 首字节门禁，未知 `E9` 停手 |
| R-8 | 遥测恒 0（谓词未接上） | A8 强制；三消费面任一未合流都算未完成 |

---

## 7. 交付回执（填完交回，写入 `out/re_work/re_sprint/R_h20c_card/`）

```
ZC-H20C-SWEEP RESULT
- build/sha256(gamemd):
- install path: (ra2render hook | external patcher | ...)
- EnableRadarSweepWindow / Duration / Radius:
- trigger site used: (T-b ClickFire | T-b Launch | T-a 7B)
- G0.1–G0.7: PASS/FAIL
- Q1 first byte before:
- bytes after @trigger:
- Route A H1/H2/H3: untouched y/n
- A1..A10: (each PASS/FAIL + evidence path)
- telemetry Opened/CellsLit/Expired:
- except.txt: empty|path
- rollback tested: y/n
- MP verdict: SAFE|VIOLATION
```

---

## 8. 不在本卡

- R-a 写 `Rules+0xFEC` / R-a+ 解夹紧 `0x567A4A` — 仅当产品叠加原版 `RevealArea2` 时另卡  
- Case 8 SpyPlane 扫描线 `0x65EAB0` 接入扫窗（U4）— 待产品  
- `RadarSweepCooldownFrames` / `SW+0xB0` CD 改写 — 与本包分开开关、分开评估  
- 台账/看板登记 — 由 Lead 收口  
- `ra2render/**` 源码重构 — 本卡只给行号合流点，实现另派  

---

## 9. 复现

```text
python out/re_work/re_sprint/R_h20c/verify_h20c_bytes.py
  → verify_bytes_out.txt（14 MATCH / 0 MISMATCH）
对照 out/re_work/re_sprint/R_h20c/claims.txt
阅读 docs/re/h20c_private_sweep_spec.md（主规格）
     docs/re/radar_sweep_sw_deep_dive.md · sw_radius_deadkey_fix_spec.md · radar_hook_routeA_spec.md
```

---

*依据：R-H20C 可执行规格 §1–§11；字节门 14/14；T-a 7B 勘误、瞄准圈 VA `0x6DC1C6` 勘误已定谳。本卡 = ZCode 照表落地，不做静态推理。*
