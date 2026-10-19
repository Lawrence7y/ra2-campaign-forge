# ZCode 落地卡 · RadarSweepRadiusCells 语义复活（R-a 改 Rules+0xFEC）

> **卡号**：`ZC-SW-RADIUS-RA` · **优先级**：P1（可选；半径 ≤10 时首选原生路径）  
> **执行方**：ZCode（真机/补丁安装唯一写者）· **起草**：MiMo（R-SWRA-CARD，接 R-SW-RADIUS / R-SWR-CARD）  
> **上游**：`docs/re/sw_radius_deadkey_fix_spec.md`（§2.2 三方案 / §2.3 钩点 / §4 确定性 / §5 验收）· 证据 `out/re_work/re_sprint/R_sw_radius/`  
> **本卡工作区**：`out/re_work/re_sprint/R_swra_card/`（`claims.txt` / `card_checklist.md`）  
> **格式对齐**：`docs/re/landing_pack_sw_radius_rc.md` / `docs/re/landing_pack_sw_charge.md`  
> **本卡范围**：**仅 R-a 数据改源**——进程内写 `Rules+0xFEC`（i32）= `clamp(RadarSweepRadiusCells, 1, 10)`，**保留** `SW+0xF8` 写仅为瞄准圈一致。**不做** R-a+ 解夹紧（附录警告）；**不做** R-c 私有扫窗（另卡 `ZC-SW-RADIUS-RC`）；**不改** `gamemd.exe` `.text`。  
> **证据基线**：`gamemd.exe` 1.001 · SHA-256 `73201CC021497C9567742F718BF1DC78C22E9AE16C7E7365354B65F3FCF67476` · ImageBase `0x00400000`  
> **写作用域**：本文件 + `out/re_work/re_sprint/R_swra_card/**`。**只读** `ra2render/**`、`gamemd.exe`、`tools/**`、台账、看板。

---

## 0. 一句话

`RadarSweepRadiusCells` 对开图是 **死写**（12/12 发射 case 均不读 `SW+0xF8`）；本卡走 **R-a 数据改源**：把键值写入 **`Rules+0xFEC`（i32 PsychicRevealRadius）**，让 Case11 真实读到它——但仍被 `RevealArea2` **`min(10,·)` 夹紧**，故有效域 **1..10**。`SW+0xF8` 继续写同值 float **仅为瞄准圈**。改可见性 Cell O(r²) ⇒ **MP 必须全端同半径**（CONDITIONAL，非 RNG 红线）。

---

## 1. 背景定谳（只读引用，本卡不重扫）

| # | 事实 | 等级 | 出处 |
|---|---|---|---|
| 1 | 12/12 超武发射 case **0 次**读 `SW+0xF8`；唯一活消费 = 鼠标瞄准圈 `fld [edi+0xF8] @ 0x6DC1C8` | [实证] | R-SW-RADIUS A13/B4 |
| 2 | PsychicReveal 真实开图半径 = `Rules+0xFEC`（i32），被 `RevealArea2` **`min(10,·)` @ `0x567A4A`** 夹紧 | [实证] | C1–C5 |
| 3 | `SW+0xF8` = **float**，`Rules+0xFEC` = **i32**；**禁止**把发射半径改读 `SW+0xF8` | [实证] | B5 / X1 |
| 4 | 改半径 **0 次 RNG**；真实副作用 = Cell 写入 O(r²)（`+0x12C/0x130/0x134/0x140`） | [实证]+[推演] | E1–E8 |
| 5 | 现网 `PatchSpySatBuildingTypes:1412-1413` 写 `SW+0xF8 = g_radarSweepRadiusCells` 为死写；ini 注释「探测半径」误导 | [实证] | D1/D4 |

---

## 2. 主项 R-a · 数据改源（本卡唯一必做）

### 2.1 语义

```
RadarSweepRadiusCells (ini, clamp 4..64；产品侧允许 1..10 见 §4.1)
  → g_radarSweepRadiusCells
  → Rules+0xFEC (i32) = clamp(key, 1, 10)   ← 本卡语义落点（R-a）
  → Case11 0x6CD75F/0x6CD784 读它 → RevealArea2
  → min(10, r) @ 0x567A4A                    ← 仍在；故有效域 1..10
  → 并行：SW+0xF8 = (float)同值              ← 仅瞄准圈 UI；消「圈 16 / 图 10」谎报
  → R-c 私有扫窗 / R-a+ 解夹紧                ← 本卡不碰
```

### 2.2 执行表（无 .text 补丁；纯进程内数据写）

| 项 | 值 |
|---|---|
| **步骤 ID** | `L-SWRA-RA` |
| **数据落点** | `RulesClass::Instance` = `[0x8871E0]`，字段 **`+0xFEC`（i32）** |
| **SW-1 备份** | 首次安装前读原 `+0xFEC` → `s_origPsychicRevealRadius`（int32）；幂等：已备份则跳过 |
| **SW-2 赋值** | `*(int32*)(pRules+0xFEC) = clamp(RadarSweepRadiusCells, 1, 10)`；LoadConfig 时一次性定型（禁热切换语义，见 §6 X6） |
| **SW-3 瞄准圈** | `PatchSpySatBuildingTypes` **继续**写 `SW+0xF8 = (float)同值`（**UI-only**）；日志改口径（R-b §5） |
| **SW-4 回滚** | `RemoveVTableHooks` / 卸载：回写 `s_origPsychicRevealRadius`；TYPE 四字段按 G-07 |
| **.text** | **零字节改动**（本卡不装 U-1；那是 R-a+，见附录） |
| **写 Cell** | 间接：引擎 `RevealArea2` 按新半径写 `Cell+0x12C/0x130/0x134/0x140` O(r²)——**本卡不直接写 Cell** |
| **RNG** | **0**（不新增 `ScenarioClass::Random/RandomRanged`；改半径不平移 RNG 流） |

### 2.3 与键协调

| 键 | 层级 | 本卡动作 | 说明 |
|---|---|---|---|
| `EnableSpySatRadarSweep` | 进程，前置闸 | **保持**；=0 时 SW-1/2/3 均不装 | 总闸 |
| **`RadarSweepRadiusCells`** | 进程 | **语义复活**：从死写 → `Rules+0xFEC`（1..10）+ 瞄准圈（UI） | **本卡标的** |
| `RadarSweepCooldownFrames` | 进程 | **本卡不写**（`SW+0xB0` 会平移其它 case RNG，独立开关/独立评估） | 切割 |
| `UnclampRevealRadius` | 进程 | **不实现**（附录警告；R-a+ 另卡） | 切割 |
| `EnableRadarSweepWindow` | 进程 | **不实现**（R-c / H-20-C 卡） | 切割 |

**复活路径（时序）**

1. `EnableSpySatRadarSweep=1` 装 TYPE 补丁（既有 `PatchSpySatBuildingTypes`）；  
2. SW-1 备份 `Rules+0xFEC` 原值；SW-2 写 `clamp(key,1,10)`；  
3. SW-3 瞄准圈同值 float，R-b 死键注释/日志勘误同批落地；  
4. 验收 V2/V3/V5（§4.2）量「瞄准圈直径 vs 原生亮区直径」。

**协调红线**

- R-a **不解** `RevealArea2` 的 `min(10,·)`；键值 >10 时真实开图仍 ≤10（V3 证明）。  
- 键值 >10 且未装 R-a+：日志必须打出「clamped to 10 by RevealArea2」，禁止再报「探测半径生效」。  
- 与 gap：R-a 经引擎写 Cell 可见性字段；**不直接**写 `Cell+0x134` gap 计数；与 `EnableGapProtection` 正交。

---

## 3. 与 R-c / R-a+ 的边界切割

| 路径 | 半径源 | 夹紧 | Cell 写 | MP | 本卡 |
|---|---|---|---|---|---|
| **R-a 改源（本卡）** | `Rules+0xFEC` = clamp(key,1,10) | 仍被 `min(10,·)` 夹 | **O(r²)**（引擎） | **CONDITIONAL：全端同值** | **本卡做** |
| R-c 私有窗 | `s_radarSweepRadiusCells_eff` | 无 min(10)，1..64 | **0** | **MP SAFE**（表现） | **不做**（`ZC-SW-RADIUS-RC`） |
| R-a+ 解夹紧 | 改 `0x567A4A` 16B | 解除后 1..64 | 同 R-a + 全端同补丁 | CONDITIONAL + 面大 | **附录警告，不安装** |
| 原版 Case11 | `Rules+0xFEC` 默认约 10 | `min(10,·)` | 原样 | — | 不动（备份/还原） |

**裁决（写入实现注释）**

1. **R-a 与 R-c 语义车道互斥**：R-a = 原生开雾（写 Cell）；R-c = 表现层扫窗（不写 Cell）。二者可作为**独立开关**并存，但**禁止**合并进同一安装步骤或共用回滚。  
2. **R-a 不解夹紧**：键值 >10 时本卡仍只到 10；要真 16 格必须 R-a+（附录）或 R-c（私有窗）。  
3. **类型陷阱（X1）**：禁止把发射半径改读 `SW+0xF8`（float vs i32，IEEE 位型当整数 ⇒ 爆炸半径）。  
4. **禁止**在本卡内「顺手」改 `0x567A4A` 或装 `UnclampRevealRadius`。

---

## 4. 开关 · 验收 · 回滚 · 确定性

### 4.1 开关矩阵

| 键 | 默认 | =0 | =1 / 值域 |
|---|---|---|---|
| `EnableSpySatRadarSweep` | 0 | 不装 TYPE/半径写 | 装（前置闸） |
| **`RadarSweepRadiusCells`** | 16 | — | LoadConfig clamp 4..64；**R-a 实写 clamp(...,1,10)**；瞄准圈同值 |
| `RadarSweepCooldownFrames` | — | — | **本卡不写** |
| `UnclampRevealRadius` | **不实现** | — | 附录（R-a+） |
| `EnableRadarSweepWindow` | **不实现** | — | R-c 卡 |

启动日志（R-b 口径）：`RadarSweepRadius=N ra-rules=<eff> aim-circle=ui-only`（`<eff>` = clamp(N,1,10)）；键 >10 时追加 `warn: clamped to 10 by RevealArea2`。**禁止**打印「探测半径生效」。

### 4.2 验收（瞄准圈 vs 原生亮区半径）

| ID | 步骤 | 期望 | 证据要求 |
|---|---|---|---|
| **V1** | 修复前死键回归：`RadarSweepRadiusCells=8` 与 `=16` 各施放一次（R-a 未装） | **亮区直径无差异** | 双截图量直径 |
| **V2** | R-a 后：键=4 / 8 / 10 各施放；peek `Rules+0xFEC` | 亮区直径随键变；`Rules+0xFEC` 生效值 = clamp(key,1,10) | 截图 + 内存读数 |
| **V3** | 键值=16 且**未装** R-a+ | 仍 ≤10（夹紧证明）；日志有 clamped warn | 截图 + 日志 |
| **V5** | 鼠标瞄准圈直径 | 与 `SW+0xF8` 一致（UI-only 语义）；键 ≤10 时圈径 ≈ 亮区径 | 同帧对照截图 |
| **V6** | RNG | 同种子双端，改半径后帧 CRC / `ScenarioClass::Random` 抽取序一致 | 双端日志/CRC |
| **V7** | 回滚 | 卸载后 `Rules+0xFEC` == `s_origPsychicRevealRadius`；`0x567A4A` 字节 MATCH 原版 | 内存/字节 MATCH |

**禁止把「没崩」当成功**：V2 必须有「`Rules+0xFEC` 读数 = 期望值」的内存证据；V3 必须有「键 16 仍 ≤10」的夹紧证据。

### 4.3 回滚

1. `Remove*` / 卸载：回写 `s_origPsychicRevealRadius` → `Rules+0xFEC`。  
2. G-07：还原 `SW+0xB0/+0xF8`、`Bld+0x16A5/+0x16F0`（TYPE 四字段）。  
3. 本卡**不装** U-1，故 `0x567A4A` 无需还原；若它卡装过，按该卡契约单独回滚。  
4. 静态门：`audit_bytes.py` 对 `0x567A4A` 与 `0x6CD75F/0x6CD784` 做 MATCH（本卡未改它们）。

### 4.4 确定性 / MP

| 项 | R-a（本卡） | R-c（另卡） | R-a+（附录） |
|---|---|---|---|
| RNG | **0**（不新增 Random/RandomRanged；改半径不平移流） | 0 | 0 |
| Cell 写 | **O(r²) 可见性**（引擎 `RevealArea2`） | **0** | 同左 + 全端同补丁 |
| 帧 CRC / .SAV | `Rules+0xFEC` 不进 CRC；可见性进 .SAV 间接 | 不进 | 同左 |
| 判定 | **CONDITIONAL：全端同半径**（混端 = 可见性分叉，非 RNG 红线） | MP SAFE | CONDITIONAL + 面大 |

**红线**

1. 0 RNG：禁止新增 `ScenarioClass::Random/RandomRanged`。  
2. 本卡不**直接**写 `Cell+0x12C/0x130/0x134/0x140`；引擎间接写 O(r²) ⇒ **MP 必须全端同半径**。  
3. `SW+0xB0` CD 与本卡**分开开关**（会平移其它 case Launch 帧 ⇒ RNG 流）。  
4. `s_origPsychicRevealRadius` **不进帧 CRC、不进 .SAV、不进 Checksum v[13]**。

---

## 5. R-b 死键文档化（本卡同批必做）

| 对象 | 动作 |
|---|---|
| `ra2render.ini:93` 注释 | 「探测半径」→「瞄准圈显示半径（UI-only）；原生开图半径 = Rules.PsychicRevealRadius（本卡写入，仍 min10）」 |
| LoadConfig 日志 `:540-542` | 禁止打「探测半径生效」；改打 §4.1 口径 |
| `telemetry_and_switches_spec.md` #17 / `REVERSE_ENGINEERING_AND_PATCHES.md:155` | 补「死写（开图）」标注（台账/看板由 Lead 收口，本卡不写） |
| rules `SuperWeaponType` `Range=`（PsychicReveal） | 文档注明对 Case11 开图无效，仅瞄准圈 |

---

## 6. 禁区（红线）

| ID | 项 | 说明 |
|---|---|---|
| X1 | 禁止发射半径改读 `SW+0xF8` | float vs i32；12 case 从未读它 |
| X2 | 禁止本卡内做 R-a+（`0x567A4A` 16B） | 附录警告；另卡 + 独立开关 `UnclampRevealRadius` + 全端同补丁 |
| X3 | 禁止本卡**直接**写 `Cell+0x12C/0x130/0x134/0x140` | 可见性/gap 红线；引擎间接写已计入 MP |
| X4 | 禁止新增同步 PRNG | G-R4 |
| X5 | 禁止把 R-c 私有窗逻辑并进本卡 | 语义车道互斥；`ZC-SW-RADIUS-RC` |
| X6 | 禁止热切换安装态开关语义 | `LoadConfig` init 读一次 |
| X7 | `SW+0xB0` CD 不进本包 | 独立评估 |
| X8 | 禁止把 IEEE754 位型当整数半径 | 类型陷阱实现注释必写 |

---

## 7. 交付回执（填完交回）

```
ZC-SW-RADIUS-RA RESULT
- build/sha256(gamemd):
- install path: (ra2render hook | ...)
- EnableSpySatRadarSweep / RadarSweepRadiusCells:
- s_origPsychicRevealRadius (backup) =:
- Rules+0xFEC effective written =:
- SW+0xF8 aim-circle value =:
- .text bytes changed by THIS card: (expect 0)
- 0x567A4A touched by THIS card: (expect no)
- V1..V7: (each PASS/FAIL + evidence path)
- V2 Rules+0xFEC peek values at key=4/8/10:
- V3 key=16 without R-a+ reveal diameter:
- R-b log wording checked: y/n
- rollback tested (Rules+0xFEC restore MATCH): y/n
- MP: (single | all-endpoints-same-radius | ...) + RNG/Cell note
- except.txt: empty|path
```

---

## 8. 不在本卡

- **R-a+ 解夹紧** `0x567A4A`（默认禁止；见附录警告；影响 22 caller；另卡）  
- **R-c 私有扫窗** / H-20-C 本体 —— `landing_pack_sw_radius_rc.md` / `landing_pack_h20c_sweep.md`  
- `RadarSweepCooldownFrames` / `SW+0xB0` CD 策略  
- 台账/看板登记 —— 由 Lead 收口  
- `ra2render` / `gamemd` / tools 写操作  

---

## 9. 复现 / 证据索引

```text
上游定谳：docs/re/sw_radius_deadkey_fix_spec.md（§2.2 三方案 / §2.3 钩点 / §4 确定性 / §5 验收）
证据：out/re_work/re_sprint/R_sw_radius/claims.txt（A13 B4 C5 D1 E1–E9 F1–F4）
      out/re_work/re_sprint/R_sw_radius/scan_output.txt / scan_refine.txt / scan_depth2.txt
本卡工作区：out/re_work/re_sprint/R_swra_card/（claims.txt / card_checklist.md）
边界卡：docs/re/landing_pack_sw_radius_rc.md（R-c）
```

---

## 附录 A · R-a+ 解夹紧 —— **仅警告，本卡不安装**

> **状态**：**警告 / 默认禁止 / 高风险**。本附录**不是**落地步骤，仅登记边界与风险，供产品决策「键值 >10 真 16 格」时另开卡。

| 项 | 内容 |
|---|---|
| **若要做** | 在 R-a 基础上**再**改 `0x567A4A` 夹紧（16B）为直通或自定上限 |
| **原字节** | `83 F8 0B 7D 05 83 F8 0A 7E 09 B8 0A 00 00 00`（`min(10,r)`；`r==0` 早退） |
| **键值可达域** | 解夹后 1..64（与键 clamp 对齐） |
| **独立开关** | **必须**新增 `UnclampRevealRadius`，**默认 0**；=0 时保留 `min(10,·)` |
| **全端同值** | **必须**全端同补丁 + 同 `Rules+0xFEC` 值；一侧 10 格一侧 16 格 ⇒ **Cell 状态分叉** |
| **爆炸半径** | `RevealArea2` **全部 22 个 caller**（任务脚本/其它开图同被解夹）——非 PsychicReveal 专属 |
| **回滚** | 还原 16B 原字节（`audit_bytes` MATCH）+ 还原 `Rules+0xFEC` |
| **与本卡关系** | 本卡 `L-SWRA-RA` **零 .text 改动**；U-1 **禁止**顺手做进本卡（X2） |
| **推荐** | 键值 ≤10 只装 R-a；键值 >10 优先评估 R-c（MP SAFE 私有窗），R-a+ 仅当产品坚持「原生开雾真 16 格」且接受全端同补丁 |

**一句话警告**：R-a+ 是**面补丁**（22 caller）+ **可见性语义**（Cell O(r²)）+ **全端同步**三重约束，任缺一即分叉；默认不装。

---

*依据：R-SW-RADIUS 死键定谳（12/12 不读 SW+0xF8；Rules+0xFEC + min(10)；0 RNG / Cell O(r²)）· 本卡 = R-a 数据改源（1..10）+ 瞄准圈同值 + R-b 勘误；R-a+ 仅附录警告（全端同值 / 独立开关 / 高风险）；与 R-c 边界切割（原生开雾 vs 私有窗）。*
