# RadarSweepRadiusCells 死键定谳与产品修复规格

**任务**：R-SW-RADIUS（接 R-RADAR-SW）  
**性质**：全静态（`gamemd.exe` 只读）；本文为产品修复规格 + 死键勘误清单  
**证据目录**：`out/re_work/re_sprint/R_sw_radius/`（`claims.txt` / `scan_*.txt`）  
**exe**：`ra2bench/gamemd.exe` sha256 `73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476`

---

## 0. 结论摘要

| # | 结论 | 等级 |
|---|---|---|
| 1 | **12/12 超武发射 case 均不读 `SuperWeaponTypeClass+0xF8 (Range)`** ⇒ 产品写 `SW+0xF8 = RadarSweepRadiusCells` 对一切开图/杀伤半径是 **死写**；该字段唯一消费 = 鼠标瞄准虚线圈 `0x6DC1C8` | [实证] |
| 2 | PsychicReveal 真实半径 = **`Rules+0xFEC`（i32）**，且被 `RevealArea2` **`min(10, r)` 夹紧** ⇒ 键值 16 即便改对数据源仍被夹到 10 | [实证] |
| 3 | `SW+0xF8` 为 **float**，`Rules+0xFEC` 为 **i32**，不能只改读点地址 | [实证] |
| 4 | **改半径不平移 RNG**（RevealArea2/Case11 0 次 `ScenarioClass::Random`）；但改 Cell 写入量（存档/可见性） | [实证]+[推演] |
| 5 | ra2forge **未声明**该键；`ra2render.ini` 注释「探测半径」误导 | [实证] |

---

## 1. 跳表 12 case 定谳：谁读 `SW+0xF8`

跳表 `0x6CDE44`（12 dword，已字节复算）：  
`Nuke 0x6CDA67` / `IronCurtain 0x6CCE64` / `LightningStorm 0x6CCD3F` / `ChronoSphere 0x6CC3B9` / `ChronoWarp 0x6CC4B2` / `ParaDrop 0x6CD2EE` / `AmerParaDrop 0x6CD537` / `PsychicDominator 0x6CCDBD` / `SpyPlane 0x6CD66F` / `GeneticMutator 0x6CD7E7` / `ForceShield 0x6CD072` / `PsychicReveal 0x6CD70C`。

对每个 case 体（`[entry, next-entry)`）做 ModR/M disp32=`0xF8` 普查：

| case | 名 | `+0xF8` 读 | 半径/范围实际来源 | 对 `RadarSweepRadiusCells` |
|---|---|---|---|---|
| 0 | Nuke | **0** | 弹道/伤害参数（非 SW Range） | 死写 |
| 1 | IronCurtain | **0** | 无半径概念 | 死写 |
| 2 | LightningStorm | **0** | `LightningStorm::Start` 自带参数 | 死写 |
| 3 | ChronoSphere | **0** | 落点坐标 | 死写 |
| 4 | ChronoWarp | **0**（1 条伪命中非 ModR/M） | 落点坐标 | 死写 |
| 5 | ParaDrop | **0** | 空投清单 | 死写 |
| 6 | AmerParaDrop | **0** | 同上 | 死写 |
| 7 | PsychicDominator | **0** | 爆心 | 死写 |
| 8 | SpyPlane | **0** | 扫描线动画 | 死写 |
| 9 | GeneticMutator | **0** | 伤害域 | 死写 |
| 10 | ForceShield | **0** | 护盾/断电 | 死写 |
| **11** | **PsychicReveal** | **0** | **`Rules+0xFEC` → min(10,·)** | **死写（本键标的场景）** |

**⇒ 产品级定谳：不存在「读 SW+0xF8 有效」的超武发射逻辑。**  
`SW+0xF8` 全程序 R/W 仅：

| 类型 | VA | 指令 | 语义 |
|---|---|---|---|
| 写 | `0x6CE65C` | `mov [ebp+0xF8], ebx` | ctor 置 0 |
| 写 | `0x6CEC03` | `fstp [ebp+0xF8]` | rules INI `Range=` 解析 |
| 读 | `0x6CEBDC` | `fld [ebp+0xF8]` | INI 加载路径 |
| 读 | `0x6DC1C8` | `fld [edi+0xF8]` | **鼠标瞄准虚线圈（唯一活消费）** |

类型：x87 `fld/fstp` ⇒ **float**。产品源 `blitter_hooks.cpp:1413` 写 float，与此一致，但**没有任何发射逻辑读它**。

---

## 2. 产品修复规格

### 2.1 现状（缺陷）

```
RadarSweepRadiusCells (ini, clamp 4..64)
  → g_radarSweepRadiusCells
  → PatchSpySatBuildingTypes 写 SWType+0xF8 (float)     ← 死写
  → 玩家期望：扫图半径 16 格
  → 实际：Case11 读 Rules+0xFEC（默认约 10）再 min(10,·) ⇒ 恒 ≤10 格
  → 侧效应：仅鼠标瞄准圈显示 16 格（与真实开图不一致，属 UI 谎报）
```

### 2.2 三方案对比

| 方案 | 改哪里 | 字节/钩点 | 键值可达域 | 开关 | 回滚 | 风险 | 推荐 |
|---|---|---|---|---|---|---|---|
| **R-a 数据改源** | 写 `Rules+0xFEC`（`0x8871E0` 单例 +0xFEC，**i32**）= `RadarSweepRadiusCells`；**保留** `SW+0xF8` 写仅为瞄准圈一致 | 无 .text 补丁；进程内数据写 | **1..10**（仍被 `min(10,·)` 夹） | `EnableSpySatRadarSweep` | 备份原 `Rules+0xFEC`，`Remove*` 还原 | 改可见性语义 ⇒ MP 需全端同值 | ★ 半径≤10 时首选 |
| **R-a+ 解夹紧** | R-a **再**改 `0x567A4A` 夹紧（`83 F8 0B 7D 05 83 F8 0A 7E 09 B8 0A 00 00 00`，16 B）为直通或自定上限 | **.text 补丁**（影响 **全部 22 个** `RevealArea2` caller） | 1..64（与键 clamp 对齐） | 需独立开关 `UnclampRevealRadius`（默认 0） | 还原 16 B + 还原 `Rules+0xFEC` | 面大：任务脚本/其它开图同被解夹 | 键值>10 时唯一能真 16 格的原生路径 |
| **R-c 私有扫窗** | 不动引擎半径；`H-20-C` 用 `s_radarSweepExpireFrame[512*512]` + 私有 `s_radarSweepRadiusCells` 画窗 | 无 .text；不写 Cell | 1..64，**无 min(10)** | `EnableRadarSweepWindow` | 卸载即无 | 不写 Cell / 不吃 RNG ⇒ MP 最安全；但表现层自绘 | 产品若接受「扫窗非原生开雾」 |
| **R-b 死写文档化** | 0 代码；文档/ini 注释改「半径以 `Rules.PsychicRevealRadius` 为准」；删或停用 `RadarSweepRadiusCells` | 无 | n/a | 无 | 无 | 0 | 仅当放弃该键时 |

### 2.3 推荐落地组合

```
默认：R-a（半径 ≤10 生效）
可选：R-a + R-a+（键值 >10 才装 UnclampRevealRadius；默认关）
并行：R-c 作为 MP 安全旁路（扫窗表现）
文档：R-b 的死键声明无论选哪条都要做（见 §3）
```

**钩点/字节清单（R-a）**

| 项 | 位置 | 动作 |
|---|---|---|
| SW-1 | `RulesClass::Instance` = `[0x8871E0]` | 读原 `+0xFEC` → `s_origPsychicRevealRadius` |
| SW-2 | 同上 | 写 `i32 clamp(RadarSweepRadiusCells, 1, 10)`（未解夹时） |
| SW-3 | `SWType+0xF8` | **继续**写 float，仅为瞄准圈与真实半径一致；文档标明 UI-only |
| SW-4 | `RemoveVTableHooks` / 卸载 | 回写 `s_origPsychicRevealRadius`；TYPE 四字段按 G-07 |

**钩点/字节清单（R-a+ 解夹紧，可选）**

| 项 | 位置 | 原字节 | 建议 |
|---|---|---|---|
| U-1 | `0x567A4A` | `83 F8 0B 7D 05 83 F8 0A 7E 09 B8 0A 00 00 00` | 改为上限 `min(RadarSweepRadiusCells, 64)` 的等价短序列，或 NOP 夹紧后由 SW-2 预夹 |
| U-2 | — | — | **必须**全端同补丁，否则一侧 10 格一侧 16 格 ⇒ Cell 状态分叉 |
| U-3 | 回滚 | — | 16 B 原字节 `audit_bytes` 比对还原 |

**开关矩阵**

| 开关 | 层级 | =0 | =1 |
|---|---|---|---|
| `EnableSpySatRadarSweep` | 进程 | 不装 TYPE/半径补丁 | 装 |
| `RadarSweepRadiusCells` | 进程 | 默认 16 | clamp 4..64；真正生效依赖 R-a/R-a+/R-c |
| `UnclampRevealRadius`（新，仅 R-a+） | 进程 | 保留 `min(10,·)` | 解夹 |
| `EnableRadarSweepWindow`（H-20-C） | 进程 | 无扫窗 | 私有窗 |

**回滚（统一）**

1. `Remove*` 还原 `Rules+0xFEC` 原值；  
2. 若装 U-1，还原 `0x567A4A` 16 B；  
3. G-07：还原 `SW+0xB0/+0xF8`、`Bld+0x16A5/+0x16F0`；  
4. `audit_bytes.py` 对 `0x567A4A` 与 `0x6CD75F/0x6CD784` 做 MATCH。

**类型陷阱（必须写入实现注释）**  
`SW+0xF8` = float，`Rules+0xFEC` = i32。若将来有人把 Case11 的读「改成 `+0xF8`」而不做 `fistp`/类型转换，会把 IEEE754 位型当整数半径 ⇒ 爆炸性错误半径。**禁止**把发射半径改读 `SW+0xF8`。

---

## 3. 死键清单（文档勘误用；design/ini 只读）

> 用途：供文档/ini 注释勘误，**本轮不改**任何 design/ini。

| 键 / 字段 | 声明处（只读） | 现注释/假设 | 实际 | 勘误建议 |
|---|---|---|---|---|
| **`RadarSweepRadiusCells`** | `ra2render.ini:93`（`[FogOfWar]`）；`ra2bench`/`ra2youli` 同款 ini | 「雷达扫描超武**探测半径**（格子数）」 | **死键（开图）**：写 `SW+0xF8` 无发射逻辑读者；仅改变**鼠标瞄准圈**显示 | 注释改为「瞄准圈显示半径（UI-only）；真实开图半径见 Rules.PsychicRevealRadius / 私有窗」；或按 §2 落地后改注释为真实语义 |
| `RadarSweepRadiusCells` | `ra2render` LoadConfig `:540-542` clamp 4..64 | 键可配且打日志 | 配置链活着，**语义死** | 日志勿再打「探测半径生效」 |
| `RadarSweepRadiusCells` | `docs/re/telemetry_and_switches_spec.md` #17 | 「半径」改 TYPE | 同上 | 补「死写（开图）」标注 |
| `RadarSweepRadiusCells` | `REVERSE_ENGINEERING_AND_PATCHES.md:155` | 「半径修改为 16」 | 同上 | 补勘误 |
| **ra2forge / design.py / maplib.py** | `ra2forge/**` | — | **0 处声明**该键 | 无需勘误（未引入） |
| rules `SuperWeaponType` **`Range=`**（PsychicReveal 条目） | 游戏 rulesmd/rules 系 INI | 控制超武范围 | **对 PsychicReveal 开图为死字段**；仅瞄准圈 | 文档注明 Range= 对 Case11 无效 |
| （对照）`RadarSweepCooldownFrames` | 同 ini | CD 帧数 | **活键**：写 `SW+0xB0`，`Grant 0x6CB658` 读 | 保持；但注意改 CD 会平移**其它** case 的动画/空投 RNG（见 §4） |
| （对照）`EnableSpySatRadarSweep` | 同 ini | 总闸 | **活键** | 保持 |
| （历史）`TargetScanKey` | `ra2render.ini` 重复 `[Logic]` | — | 已在 v1.8.3 修复 | 不重复登记 |

**死键一句话（可直接贴文档）**  
> `RadarSweepRadiusCells` 当前**不改变任何开图/杀伤半径**（12 超武发射逻辑均不读 `SW+0xF8`）；它只改变超武鼠标瞄准虚线圈的显示半径。PsychicReveal 真实开图半径 = `Rules.PsychicRevealRadius`（`Rules+0xFEC`，i32），且被引擎 `min(10, ·)` 夹紧。

---

## 4. 确定性：改半径会否平移 RNG

| 检查 | 结果 | 证据 |
|---|---|---|
| `RevealArea2 0x5678E0` 直接 `call Random/RandomRanged` | **0** | `scan_refine` E8 字节级普查 |
| `RevealArea2 → 0x4837AB`（旧树「ShroudRnd」） | **0（旧边不成立）** | 同上 |
| `0x4837AB` 全体 caller | **仅 `0x47B5DD`**（不在 Case11 路径） | 同上 |
| `0x4837AB` 内 RNG | 1× `RandomRanged @ 0x483839`（离径） | `scan_refine` |
| RevealArea2 被调函数深度-2 RNG | **0**（`0x4A9DD0/4CAC40/4F9A50/653830/6D20E0/7C5F00`） | `scan_depth2` |
| Case11 体 / Launch 体 RNG | **0** | `scan_refine` |

**结论**

1. **改 `Rules+0xFEC`（或 R-a 数据写）⇒ 不改变 `ScenarioClass::Random` 的消费次数/顺序 ⇒ 不平移 RNG 流。**  
2. 半径变化的真实副作用是 **Cell 写入量 O(r²)**（`+0x12C/+0x130/+0x134/+0x140`），进 `.SAV` 与可见性，经「可见性→寻敌→位置」可**间接**影响后续含 RNG 的决策 ⇒ **MP 必须全端同半径**；混端 = 可见性分叉（CONDITIONAL，非 RNG 红线）。  
3. **`SW+0xB0` CD 改写**（现有 `PatchSpySatBuildingTypes`）会平移 Launch 发生帧 ⇒ 平移**其它 case**（Nuke/闪电/空投等动画与 `SpawnAircraftEdge`）的 RNG 序；**与本键无关**，但同一补丁包里必须分开评估。  
4. 旧证 C9「Case11 经 RevealArea2→0x4837AB 吃 RNG」**否决**（见 claims E2/F2/F3）。  
5. H-20-C 私有扫窗（R-c）不写 Cell、不调 RNG ⇒ **MP SAFE**。

---

## 5. 验收 / 回归

| # | 步骤 | 期望 |
|---|---|---|
| V1 | 修复前：`RadarSweepRadiusCells=8` 与 `=16` 各施放一次，量亮区直径 | **无差异**（死键回归证明） |
| V2 | R-a 后：同上，且 `Rules+0xFEC` 生效值 = 键值（≤10） | 直径随键变 |
| V3 | 键值=16 且未装 R-a+ | 仍 ≤10（夹紧证明） |
| V4 | R-a+ 后键值=16 | 亮区 ≈16 格 |
| V5 | 鼠标瞄准圈直径 | 与 `SW+0xF8` 一致（UI-only 语义） |
| V6 | RNG | 同种子双端，改半径后帧 CRC / `ScenarioClass::Random` 抽取序一致 |
| V7 | 回滚 | 卸载后 `Rules+0xFEC` 与 `0x567A4A` 字节 MATCH 原版 |

---

## 6. 风险与禁项

| ID | 项 | 说明 |
|---|---|---|
| X1 | 禁止把发射半径改读 `SW+0xF8` | float vs i32；且 12 case 从未读它 |
| X2 | R-a+ 的 `0x567A4A` 影响 22 个 `RevealArea2` caller | 必须独立开关 + 全端同补丁 |
| X3 | `Rules+0xFEC` 不进帧 CRC，但改可见性 | MP 红线从「RNG」改为「全端同可见性」 |
| X4 | 现网 `PatchSpySatBuildingTypes` 无备份/无 MpActive | 与 G-07 / W3 一并修（非本卡唯一范围） |
| X5 | 旧文档 ATLAS:4134 / gap 文档「SW.Range 优先」表述 | 已勘误，实施方勿按旧文写代码 |

---

## 7. 证据索引

- `out/re_work/re_sprint/R_sw_radius/claims.txt`（A13 / B4 / C5 / D1 / E1–E7 / F1–F4）  
- `out/re_work/re_sprint/R_sw_radius/scan_output.txt`（12 case 体 + 全局 +0xF8）  
- `out/re_work/re_sprint/R_sw_radius/scan_refine.txt`（E8 调用点）  
- `out/re_work/re_sprint/R_sw_radius/scan_depth2.txt`（RNG 可达性）  
- 前证：`docs/re/radar_sweep_sw_deep_dive.md`、`docs/re/gap_psychic_reveal_deep_dive.md`、`docs/re/superweapon_re.md` §7.4/§10.2
