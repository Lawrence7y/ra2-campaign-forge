# ZCode 落地卡 · RadarSweepRadiusCells 语义复活（R-c 私有半径）

> **卡号**：`ZC-SW-RADIUS-RC` · **优先级**：P0（死键语义复活；MP SAFE 旁路）  
> **执行方**：ZCode（真机/补丁安装唯一写者）· **起草**：MiMo（R-SWR-CARD，接 R-SW-RADIUS / R-H20C）  
> **上游**：`docs/re/sw_radius_deadkey_fix_spec.md`（死键定谳 + 三方案）· `docs/re/h20c_private_sweep_spec.md`（H-20-C 私有扫窗）· 证据 `out/re_work/re_sprint/R_sw_radius/` · `out/re_work/re_sprint/R_h20c/`  
> **本卡工作区**：`out/re_work/re_sprint/R_swr_card/`  
> **格式对齐**：`docs/re/landing_pack_sw_charge.md` / `docs/re/landing_pack_gap_p21.md`  
> **本卡范围**：**仅 R-c 私有半径 1..64 + 与 H-20-C 键协调**（RadarSweepRadiusCells 语义复活路径）。**不做** R-a 改 `Rules+0xFEC`；**不做** R-a+ 解夹紧（另卡）；**不改** `gamemd.exe` `.text`。  
> **证据基线**：`gamemd.exe` 1.001 · SHA-256 `73201CC021497C9567742F718BF1DC78C22E9AE16C7E7365354B65F3FCF67476` · ImageBase `0x00400000`

---

## 0. 一句话

`RadarSweepRadiusCells` 对开图是 **死写**（12/12 发射 case 均不读 `SW+0xF8`）；本卡走 **R-c**：半径语义落到 **H-20-C 私有扫窗** `s_radarSweepRadiusCells_eff`（**1..64，无 `min(10)`**），与 `EnableRadarSweepWindow` / `RadarSweepDurationFrames` 键协调；瞄准圈继续由 `SW+0xF8`（float）驱动并**必须与私有窗半径同值**以消 UI 谎报。**不写 Cell、不吃 RNG** ⇒ **MP SAFE**。

---

## 1. 背景定谳（只读引用，本卡不重扫）

| # | 事实 | 等级 | 出处 |
|---|---|---|---|
| 1 | 12/12 超武发射 case **0 次**读 `SW+0xF8`；唯一活消费 = 鼠标瞄准圈 `fld [edi+0xF8] @ 0x6DC1C8` | [实证] | R-SW-RADIUS A13/B4 |
| 2 | PsychicReveal 真实开图半径 = `Rules+0xFEC`（i32），被 `RevealArea2` **`min(10,·)` @ `0x567A4A`** 夹紧 | [实证] | C1–C5 |
| 3 | `SW+0xF8` = **float**，`Rules+0xFEC` = **i32**；**禁止**把发射半径改读 `SW+0xF8` | [实证] | B5 / X1 |
| 4 | 改半径 **0 次 RNG**；真实副作用 = Cell 写入 O(r²) | [实证]+[推演] | E1–E8 |
| 5 | 现网 `PatchSpySatBuildingTypes:1412-1413` 写 `SW+0xF8 = g_radarSweepRadiusCells` 为死写；ini 注释「探测半径」误导 | [实证] | D1/D4 |

---

## 2. 主项 R-c · 私有半径（本卡唯一必做）

### 2.1 语义

```
RadarSweepRadiusCells (ini, clamp 4..64；产品侧允许 1..64 见 §5)
  → g_radarSweepRadiusCells
  → s_radarSweepRadiusCells_eff          ← 本卡语义落点（R-c）
  → OpenSweepWindow(cx,cy) 画私有窗       ← 实际扫窗半径
  → 并行：SW+0xF8 = (float)同值           ← 仅瞄准圈 UI；消「圈 16 格 / 窗 16 格」谎报
  → 引擎 Rules+0xFEC / RevealArea2        ← 本卡不碰（min(10) 原样）
```

### 2.2 执行表（无 .text 补丁；纯 DLL 数据 + 既有 H-20-C 开窗路径）

| 项 | 值 |
|---|---|
| **步骤 ID** | `L-SWR-RC` |
| **数据落点** | `s_radarSweepRadiusCells_eff`（H-20-C §2.1 私有字段） |
| **赋值** | `s_radarSweepRadiusCells_eff = clamp(RadarSweepRadiusCells, 1, 64)`；LoadConfig 时一次性定型（禁热切换语义，见 §3.1） |
| **消费** | `OpenSweepWindow` 圆域 `dx*dx+dy*dy <= r*r`（H-20-C §2.2） |
| **瞄准圈对齐** | `PatchSpySatBuildingTypes` 继续写 `SW+0xF8 = (float)s_radarSweepRadiusCells_eff`（**UI-only**）；日志改口径（R-b） |
| **.text** | **零字节改动**（本卡不装 T-a/T-b；那是 H-20-C 卡的职责） |
| **写 Cell** | **无** |
| **RNG** | **无** |

### 2.3 与 H-20-C 键协调（RadarSweepRadiusCells 语义复活路径）

| 键 | 层级 | 本卡动作 | 与 H-20-C 关系 |
|---|---|---|---|
| `EnableSpySatRadarSweep` | 进程，前置闸 | **保持**；=0 时 SW-1/私有窗均不装 | H-20-C 同闸 |
| `EnableRadarSweepWindow` | 进程 | 本卡**不新增**；由 H-20-C 卡实现。=1 时 R-c 半径才有人消费 | **依赖** |
| `RadarSweepDurationFrames` | 进程 | 本卡不碰（时长归 H-20-C） | 并列 |
| **`RadarSweepRadiusCells`** | 进程 | **语义复活**：从死写 → 私有窗半径（R-c）+ 瞄准圈（UI） | **本卡标的** |
| `RadarSweepCooldownFrames` | 进程 | **本卡不写**（`SW+0xB0` 会平移其它 case RNG，独立开关/独立评估） | 切割 |

**复活路径（时序）**

1. H-20-C 装 SW-1（T-b 推荐 5B / T-a 必须 7B）+ 私有网格 + 三谓词合流；  
2. 本卡把 `RadarSweepRadiusCells` 接到 `s_radarSweepRadiusCells_eff`，`OpenSweepWindow` 用它画圆；  
3. `SW+0xF8` 写同值 float **仅为瞄准圈**，R-b 死键注释/日志勘误同批落地；  
4. 验收 A1–A5（§4）量「瞄准圈直径 vs 实际扫窗直径」。

**协调红线**

- R-c **不解** `RevealArea2` 的 `min(10,·)`；私有窗半径与引擎开图半径**允许不一致**（产品语义 = 扫窗表现，非原生开雾）。  
- `EnableRadarSweepWindow=0` 时 R-c 半径无人消费（键回落为「仅瞄准圈」）；日志必须打出该状态，禁止再报「探测半径生效」。  
- 与 gap：纯 R-c **不依赖** `EnableGapProtection`；不写 `Cell+0x12C/0x130/0x134/0x140`。

---

## 3. 与 RevealArea2 `min(10)` 的关系（边界卡）

| 路径 | 半径源 | 夹紧 | 本卡 |
|---|---|---|---|
| **R-c 私有窗** | `s_radarSweepRadiusCells_eff` | **无 `min(10)`，可达 1..64** | **本卡做** |
| R-a 改源 | `Rules+0xFEC` = clamp(key,1,10) | 仍被 `min(10,·)` 夹 | **本卡不做**（可选叠加，另卡） |
| **R-a+ 解夹紧** | 改 `0x567A4A` 16B | 解除后 1..64 | **明确不在本卡**（影响 22 个 caller，另卡 + 独立开关 `UnclampRevealRadius`） |
| 原版 Case11 | `Rules+0xFEC` 默认约 10 | `min(10,·)` | 不动 |

**裁决（写入实现注释）**

1. **R-c 不解夹紧**：私有窗 >10 格时，原版 `RevealArea2` 仍只开 ≤10 格；二者并存、互不覆盖。  
2. **R-a+ 解夹紧另卡**：若产品要「原生开图真 16 格」，必须独立开关（默认 0）、全端同补丁、`audit_bytes` 回滚 16B——**禁止**顺手做进本卡。  
3. **类型陷阱（X1）**：禁止把发射半径改读 `SW+0xF8`（float vs i32，IEEE 位型当整数 ⇒ 爆炸半径）。

---

## 4. 开关 · 验收 · 回滚 · 确定性

### 4.1 开关矩阵

| 键 | 默认 | =0 | =1 / 值域 |
|---|---|---|---|
| `EnableSpySatRadarSweep` | 0 | 不装 TYPE/扫窗/半径 | 装（前置闸） |
| `EnableRadarSweepWindow` | 0 | 无私有窗；R-c 半径仅瞄准圈 | 私有窗消费 R-c 半径 |
| **`RadarSweepRadiusCells`** | 16 | — | **1..64**（R-c 私有半径）；瞄准圈同值 |
| `RadarSweepDurationFrames` | 600 | — | 60..3600（H-20-C） |
| `UnclampRevealRadius` | **不实现** | — | 另卡（R-a+） |

启动日志（R-b 口径）：`RadarSweepRadius=N rc-private=on|off aim-circle=ui-only`；**禁止**打印「探测半径生效」。

### 4.2 验收（瞄准圈 vs 实际扫窗半径）

| ID | 步骤 | 期望 | 证据要求 |
|---|---|---|---|
| **A1** | 死键回归：R-a 未装，`RadarSweepRadiusCells=8` 与 `=16` 各施放一次 | **原版开图亮区无差异**；私有窗直径随键变（8 vs 16） | 双截图量直径；原版侧零差 |
| **A2** | **瞄准圈 vs 扫窗**：键=8 / 16 / 32 各施放 | 鼠标瞄准虚线圈直径 ≈ 私有窗亮区直径 ≈ `2*R` 格；二者同键同值、无 UI 谎报 | 三组对照截图（圈与窗同帧） |
| **A3** | 窗口过期（依赖 H-20-C）：施放后 T+0 / T+300 / T+700 | T+0/T+300 亮；**T+700 回灰/回黑**；过期后瞄准圈语义不变 | 帧号截图 |
| **A4** | 边界：键=1 与 =64（或 clamp 后最小/最大） | 窗直径单调；无越界绘制；512 边界裁剪正确 | 截图 + 无 except |
| **A5** | 回滚：`EnableRadarSweepWindow` 1→0 或卸载 | 私有窗消失；`SW+0xF8`/TYPE 按 G-07 还原；`Rules+0xFEC` **未被改**（本卡未写） | 字节 MATCH |

**禁止把「没崩」当成功**：A2 必须有「瞄准圈直径 = 扫窗直径」的同帧对照证据。

### 4.3 回滚

1. `EnableRadarSweepWindow` 1→0 ⇒ `memset` 私有网格 + 还原 SW-1（H-20-C 契约）；本卡半径字段随之无效。  
2. G-07：还原 `SW+0xB0/+0xF8`、`Bld+0x16A5/+0x16F0`（TYPE 四字段）。  
3. 本卡**不写** `Rules+0xFEC`，故无需还原它；若叠加 R-a 则另卡带备份 `s_origPsychicRevealRadius`。  
4. 静态门：`verify_h20c_bytes.py` 14 MATCH；瞄准圈读点 `0x6DC1C8` 窗口原字节不变。

### 4.4 确定性 / MP

| 项 | R-c（本卡） | R-a（另卡） | R-a+（另卡） |
|---|---|---|---|
| RNG | **0**（不新增 `ScenarioClass::Random/RandomRanged`） | 0 | 0 |
| Cell 写 | **0**（不写 `+0x12C/0x130/0x134/0x140`） | **O(r²) 可见性** ⇒ **全端同值** | 同左 + 全端同补丁 |
| 帧 CRC / .SAV / Checksum v[13] | **不进** | 可见性间接 | 同左 |
| 判定 | **MP SAFE**（纯表现；混联观感分叉可接受） | CONDITIONAL | CONDITIONAL + 面大 |

**红线**

1. 0 RNG：禁止新增 `ScenarioClass::Random/RandomRanged`。  
2. 0 Cell 写（本卡）：尤其禁 `Cell+0x134` gap 计数。  
3. 若叠加 R-a：Cell 写入量随 r² 变 ⇒ **MP 必须全端同半径**（混端 = 可见性分叉，CONDITIONAL，非 RNG 红线）。  
4. `SW+0xB0` CD 与本卡**分开开关**（会平移其它 case Launch 帧 ⇒ RNG 流）。  
5. 私有网格/半径/时长 **不进帧 CRC、不进 .SAV、不进 Checksum v[13]**。

---

## 5. R-b 死键文档化（本卡同批必做）

| 对象 | 动作 |
|---|---|
| `ra2render.ini:93` 注释 | 「探测半径」→「瞄准圈显示半径（UI-only）+ 私有扫窗半径（R-c，EnableRadarSweepWindow=1 时）」 |
| LoadConfig 日志 `:540-542` | 禁止打「探测半径生效」；改打 §4.1 口径 |
| `telemetry_and_switches_spec.md` #17 / `REVERSE_ENGINEERING_AND_PATCHES.md:155` | 补「死写（开图）」标注（台账/看板由 Lead 收口，本卡不写） |
| rules `SuperWeaponType` `Range=`（PsychicReveal） | 文档注明对 Case11 开图无效，仅瞄准圈 |

---

## 6. 禁区（红线）

| ID | 项 | 说明 |
|---|---|---|
| X1 | 禁止发射半径改读 `SW+0xF8` | float vs i32；12 case 从未读它 |
| X2 | 禁止本卡内做 R-a+（`0x567A4A` 16B） | 另卡 + 独立开关 + 全端同补丁 |
| X3 | 禁止写 `Cell+0x12C/0x130/0x134/0x140` | gap/可见性红线 |
| X4 | 禁止新增同步 PRNG | G-R4 |
| X5 | 禁止触碰路线 A 三钩 `0x655D38`(9B)/`0x655D87`(7B)/`0x65719A`(5B) | H-20-C 合流只改 C++ 谓词 |
| X6 | 禁止热切换安装态开关语义 | `LoadConfig` init 读一次 |
| X7 | `SW+0xB0` CD 不进本包 | 独立评估 |

---

## 7. 交付回执（填完交回）

```
ZC-SW-RADIUS-RC RESULT
- build/sha256(gamemd):
- install path: (ra2render hook | ...)
- EnableSpySatRadarSweep / EnableRadarSweepWindow / RadarSweepRadiusCells:
- s_radarSweepRadiusCells_eff =:
- SW+0xF8 aim-circle value =:
- .text bytes changed by THIS card: (expect 0)
- Rules+0xFEC written by THIS card: (expect no)
- A1..A5: (each PASS/FAIL + evidence path)
- A2 aim-circle vs sweep-window diameter (R=8/16/32):
- R-b log wording checked: y/n
- rollback tested: y/n
- MP: (single | mp-safe-presentation | ...) + RNG/Cell note
- except.txt: empty|path
```

---

## 8. 不在本卡

- R-a 改写 `Rules+0xFEC`（可选叠加，另卡）  
- **R-a+ 解夹紧** `0x567A4A`（默认禁止；影响 22 caller；另卡）  
- H-20-C 本体（SW-1 触发钩 / 网格 / 三谓词合流 / 过期强刷）—— `h20c_private_sweep_spec.md` / ZC-H20C  
- `RadarSweepCooldownFrames` / `SW+0xB0` CD 策略  
- 台账/看板登记 —— 由 Lead 收口  
- `ra2render` / `gamemd` / tools 写操作  

---

## 9. 复现 / 证据索引

```text
上游定谳：docs/re/sw_radius_deadkey_fix_spec.md（§2.2 三方案 / §4 确定性 / §5 验收）
H-20-C：docs/re/h20c_private_sweep_spec.md（§2 私有网格 / §4 死键 / §8 A1–A10）
证据：out/re_work/re_sprint/R_sw_radius/claims.txt（A13 B4 C5 D1 E1–E9 F1–F4）
      out/re_work/re_sprint/R_h20c/verify_h20c_bytes.py → 14 MATCH
本卡工作区：out/re_work/re_sprint/R_swr_card/（claims.txt / card_checklist.md）
```

---

*依据：R-SW-RADIUS 死键定谳（12/12 不读 SW+0xF8；Rules+0xFEC + min(10)；0 RNG / Cell O(r²)）· H-20-C 私有窗（R-c 1..64 无 min10，MP SAFE）· 本卡 = R-c 语义复活 + 键协调 + 瞄准圈/扫窗同值验收；R-a+ 解夹紧明确另卡。*
