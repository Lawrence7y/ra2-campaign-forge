# 存档版本门 · 安装包产品检查清单（R-SAV-PROD / SG-GATE）

> **文档标识**：`docs/re/savegame_product_checklist.md`
> **上游**：`docs/re/savegame_block_manifest.md`（块清单 / OLE / 红线）、`docs/re/sav_gap_cell_abi_deep_dive.md`（T7 Cell `0x148`）、`docs/re/sbh_uaf_residual_deep_dive.md`（T20 无堆地址进档）、`docs/re/gap_protection_install_spec.md`、`docs/re/landing_pack_gap_p21.md`
> **复核产物**：`out/re_work/re_sprint/R_sav_prod/**`（claims **OK=90 / FAIL=0**）
> **范围**：安装包「存档版本门」静态门禁清单。**不写** `ra2render/**` / `gamemd.exe` / `ra2youli/**` / `tools/**` / 台账 / 看板 / ATLAS。
> **目标二进制**：`ra2youli/gamemd.exe`（ImageBase `0x400000`，`file_off = VA − 0x400000`）。方法：全静态，未启动游戏。
> 【W3 勘误 E-W3-01】原句 `FileOffset = VA − 0x400000` 仅在 `.text/.rdata/.data` 成立；
> 通用式为 `FileOffset = 段.PointerToRawData + (VA − 段.VirtualAddress)`，
> 本镜像 `.rsrc`/`.detour` 为 `VA − 0x6FC000`。依据：out/re_work/_lead_baseline/W3/LEAD_ERRATUM_E-W3-01_fileoffset_rule.md；分级：[实证]

---

## 0. 一句话

**`.SAV` 的版本身份只有 `Internal Version = 0x0002B898` 一道闸；补丁语义必须另开 OLE 标记流，禁止改闸、禁止改 `CONTENTS`。安装包出厂前必须过完 G0–G6 六组门禁，并按 §4 矩阵拒绝混语义读档。**

---

## 1. 版本闸事实基线（禁改，安装包不得漂移）

| # | 事实 | 值 / 位置 | 等级 | 安装包含义 |
|---|---|---|---|---|
| B1 | 容器 | OLE2 / CFB（签名 `D0 CF 11 E0 A1 B1 1A E1`） | `[实证]` | 不得改容器格式 |
| B2 | 游戏状态流 | `CONTENTS`（`ALL01UMD.sav` = 1,205,666 B） | `[实证]` | 禁插字段 / 禁改序 |
| B3 | **版本闸** | OLE 流 `Internal Version` = LE32 `98 B8 02 00`（`0x0002B898`）；镜像常量 `Game::Savegame_Magic @ 0x83D560` | `[实证]` | **禁改**；改了原版档全拒 |
| B4 | 无块级版本 | Cell / 35 块 / 28 向量 / S-1 **均无独立版本号** | `[实证]` | 只能靠标记流区分补丁身份 |
| B5 | 入档单元口径 | **A** 35 模板块 + **B** 28 内联向量块 + **C** S-1 标量块（含 `CurrentFrame 0xA8ED84`）+ **D** Map/Cell 裸倾倒（Map 自体 `0x556c`、Cell `0x148`） | `[实证]` | 「35 块 = 全部」是**错误口径** |
| B6 | 对象寻址 | `ole32!OleSaveToStream/OleLoadFromStream`（IAT `0x7E15F4/0x7E15F8`）= CLSID；**无自研 swizzle 表**（Cell 仅 8 字段指针表 `0x6CF240`） | `[实证]` | 产品文案勿写「指针重定位表」 |
| B7 | 堆地址 | `Save_Core` 内 43 处 `mov ecx/edx,imm32` **全为 .bss 子系统 this**，用户堆地址进档 **0** | `[实证]`（T20） | SBH/UAF **无需**为存档做序列化防护 |
| B8 | CLSID/类名 | 35 块实参对象类名 **34/35 仍为 U-1 真机项**（RTTI 静态不可解析） | `[待实测]` | **禁止**假设「块名 = 类名」 |

---

## 2. 补丁标记流契约（安装包必须遵守）

### 2.1 谁需要标记

| 补丁 | 是否改 `.SAV` 语义 | 是否写语义标记流 | 理由 |
|---|---|---|---|
| **P-2.1 / P-2.2 / P-2.3**（裂缝保护，`Cell+0x134` 不再清零） | **是** | **必须** | ABI 同构，格式面不可区分 |
| P-3.x（VXL / Particle Draw） | 否 | **禁止**写语义标记 | 表现层；写了会**过度拒绝** |
| P-5.x（audio 限频） | 否 | **禁止**写语义标记 | 音频不进 `.SAV` |
| P-6.x（L4 视口） | 否 | 禁止 | — |
| P-4.x（CRT 池） | 否 | 禁止 | 无堆地址进档（B7） |
| 任意构建 | — | 可选 `Forge Build Tag`（诊断指纹，**不参与拒读**） | 售后定位用 |

### 2.2 标记流格式（只追加，不改既有流）

| 流名 | 大小 | 内容 | 写入时机 | 谁写 |
|---|---|---|---|---|
| `GapProt Version` | 4 B | u32 LE = 格式号（建议 `1`） | `Game::Save` 收尾 / `Save_Core ret` 前 | 仅当 `gapProtectionPatchesInstalled==3`（P-2.1+2.2+2.3 全装） |
| `Forge Build Tag`（可选） | 16 B | 构建指纹（补丁位图 + 版本） | 同上 | 安装包/补丁器；**只诊断，不拒读** |

**兼容性四条（红线）**：

1. 原版读档按**流名** `OpenStream`（`Load_Core 0x67E56C` 开 `CONTENTS`），多余流被忽略 → **前向兼容成立**；
2. 原版写档**不**写上述流 → 补丁档必有、原版档必无 → **可判定**；
3. **禁止**改 `Internal Version` 做标记（触 B3 / manifest §12.5）；
4. **禁止**在 `CONTENTS` 内插字段（破坏 A/B/C/D 字节布局，读档即崩）。

### 2.3 读档拒读矩阵（安装包文案与实现必须一致）

判定时机：`Game::Load 0x67CEF0` 版本闸通过后、`OpenStream("CONTENTS")`（`0x67E56C`）之前。
`STG_E_FILENOTFOUND` = 无标记流。

| 标记流 | `EnableGapProtection` | 行为 | 产品文案 |
|---|---|---|---|
| 有 | 1 | **正常加载** | 补丁档 + 补丁端 |
| 有 | 0 | **拒绝** | 「本存档由裂缝保护补丁写入，当前未启用 EnableGapProtection」 |
| 无 | 1 | **产品默认拒绝**（可选 (b) 加载 + post-load 重建 `+0x134`，需全端同算法） | 「原版存档与裂缝保护语义不兼容」 |
| 无 | 0 | **正常加载** | 双原版 |

**MP 联动（安装包须写入握手说明）**：

- 握手键必须含 `EnableGapProtection` + `gapProtectionPatchesInstalled`（期望 **3**）；
- 混端（一端 P-2.x、一端原版）**拒绝开局**；
- 注意：DESYNC **触发点**是补丁后第一次 `RevealArea2/3/Reshroud`，**不是**读档瞬间（T7 §3）。

---

## 3. ra2forge 地图/触发器：进档污染面（安装包须知）

图面声明（`[Triggers]/[Events]/[Actions]/[Tags]/[IsoMapPack5]`）只决定**开局初值**；存档后**以档为准**。

| 对象 | 可被存档污染的字段 | 后果 | ra2forge 图面对应 |
|---|---|---|---|
| **TriggerClass** `0x48` | `Destroyed@+0x30`、`Timer@+0x34(12B)`、`OccuredEvents@+0x40`、`Enabled@+0x44` | 事件位序/定时器/启用态被覆盖 | `[Triggers]` `DISABLED`、`[Events]` |
| | `NextTrigger@+0x28`（链序） | 链序错乱 → `OccuredEvents` 位图错位 | `[Triggers]` `LINKED` |
| | `Type@+0x24`、`House@+0x2C` | 归属漂移 | `HOUSE` |
| **TagClass** `0x38` | `InstanceCount@+0x2C`、`Destroyed@+0x34`、`IsExecuting@+0x35` | 重复触发 / 误判执行中 | `[Tags]` `REPEATING` |
| **Tag 向量（S-1）** | 整表按原序进档、按原序重建 | **序 = 语义**；重排即错位 | `[Tags]` 声明序 |
| **CellClass** `0x148` 裸块 | `CopyFlags@+0x12C`、`ShroudCounter@+0x130`、**`GapsCoveringThisCell@+0x134`** | 探索/遮蔽/裂缝语义被覆盖；P-2.x 与原版在此分叉 | `[IsoMapPack5]` 仅初始地形 |
| **MapClass** | 自体 `0x556c` 裸块（含 tube/索引表） | 寻路 tube 被覆盖 | `[Waypoints]` 仅初始 |
| **CurrentFrame（S-1）** | `0xA8ED84` | 全部 Timer/触发器时刻错乱 | — |
| **RNG**（`ScenarioClass::Random`） | 状态字 | 联机 desync / `RandomDelay` 不可复现 | — |
| 单位/建筑/步兵 | 量化坐标（`÷10`）、朝向、血量等 | 与图面预置行不一致 | `[Units]/[Infantry]/[Structures]` |

**产品三条**：

1. **图面 ≠ 存档**：读档后再改图面热更**无效**；
2. **触发器链序不可重排**（Save/Load 严格保持，ATLAS C10）；
3. **标记流只判补丁身份，不判真伪** —— 伪造 `.SAV` 仍可写坏 Trigger 链序/`Enabled`/`OccuredEvents`；「存档版本门」**不能**当完整性校验用。

---

## 4. 安装包出厂检查清单（G0–G6）

> 勾选即出厂门禁。任一 **P0** 未过 = **No-Go**。

### G0 · 介质与二进制基线（P0）

| ID | 检查项 | 判定 | 等级 |
|---|---|---|---|
| G0.1 | `gamemd.exe` SHA-256 = `73201CC021497C9567742F718BF1DC78C22E9AE16C7E7365354B65F3FCF67476`（1.001） | 与基线一致 | P0 |
| G0.2 | ImageBase = `0x00400000`，无 `.reloc`；目标写点均落在 `.text`（禁动 `.detour`） | 一致 | P0 |
| G0.3 | P-2.1 点 `0x568273` 原字节 `89 99 34 01 00 00`；上下文窗 `0x568271=3B C3` / `0x568279=7C 14` | 6B 窗 MATCH | P0 |
| G0.4 | P-2.2 点 `0x577EC5` 原字节 `89 B8 34 01 00 00`；P-2.3 点 `0x577B60` 原字节 `89 98 34 01 00 00` | MATCH | P0 |
| G0.5 | 复算：`python out/re_work/re_sprint/R_sav_prod/tools/cross_check_manifest.py` → claims **OK=90 FAIL=0** | 全 OK | P0 |

### G1 · 开关与默认值（P0）

| ID | 检查项 | 判定 | 等级 |
|---|---|---|---|
| G1.1 | `[FogOfWar] EnableGapProtection` API 默认 **`0`**；ini 出厂建议 **`0`** | 默认不碰 `.text` | P0 |
| G1.2 | `MpActive()==true` ⇒ **强制不安装** P-2.x（对齐 `GetEffectiveMinimapFog` 模式） | 有强制关逻辑 | P0 |
| G1.3 | 启动日志必打 `GapProtection=on\|off\|forced-off-mp\|already\|external-installer-detected` | 五态齐全 | P1 |
| G1.4 | `RemoveVTableHooks` / 进程卸载时 `memcpy` **还原原 6B**（A/B 路径同一还原契约） | 有还原 | P0 |
| G1.5 | A（ra2render 加载期）与 B（外部补丁器）**禁止同时生效**（Q1 外部已装则停手） | 互斥 | P0 |

### G2 · 标记流写侧（P0）

| ID | 检查项 | 判定 | 等级 |
|---|---|---|---|
| G2.1 | 仅当 `gapProtectionPatchesInstalled==3` 才写 `GapProt Version=1` | 条件正确 | P0 |
| G2.2 | VXL/audio/L4/CRT 补丁**不**写入语义标记流 | 无过度标记 | P0 |
| G2.3 | **未**改 `Internal Version`；**未**改 `CONTENTS` / 既有 15 元数据流 | 红线未破 | P0 |
| G2.4 | 写入时机：`Save_Core` 收尾（`0x67E3FB/0x67E410/0x67E429` 后或 `ret 0x67E43A` 前） | 锚点正确 | P1 |
| G2.5 | 原版写档**不会**产生 `GapProt Version`；补丁档**必有** | 可判定 | P0 |

### G3 · 读档门控（P0）

| ID | 检查项 | 判定 | 等级 |
|---|---|---|---|
| G3.1 | 查标记时机：版本闸后、`OpenStream("CONTENTS")` 前 | 窗口正确 | P0 |
| G3.2 | 按 §2.3 四格矩阵实现拒绝/加载；拒绝走**原版读档失败 UI** | 矩阵落地 | P0 |
| G3.3 | 拒绝日志含：档名、标记有无、`EnableGapProtection`、`gapProtectionPatchesInstalled` | 可审计 | P1 |
| G3.4 | 策略 (b)（无标记 + 开闸 = 加载后重建 `+0x134`）仅在**全端同算法**时启用；默认 (a) 拒绝 | 默认安全 | P0 |
| G3.5 | `Forge Build Tag` 只提示、不拒读 | 无过度拒绝 | P1 |

### G4 · MP 门（P0）

| ID | 检查项 | 判定 | 等级 |
|---|---|---|---|
| G4.1 | 握手键含 `EnableGapProtection` + `gapProtectionPatchesInstalled`（期望 3） | 已含 | P0 |
| G4.2 | 混端（补丁/原版）**拒绝开局**，不是等 DESYNC | 硬拒 | P0 |
| G4.3 | 对局内读档（Kind `0x1D`）全体同帧；保存后双方档内 `GapsCoveringThisCell` 抽样哈希可选告警 | 命令语义保持 | P1 |
| G4.4 | 真机 ≥5000 帧双端逐帧 CRC 对拍（**本清单不代替**，记 `[待实测]`） | 已排期 | P0* |

### G5 · ra2forge / 内容侧（P1）

| ID | 检查项 | 判定 | 等级 |
|---|---|---|---|
| G5.1 | 依赖裂缝迷雾的地图/任务，在安装包标注「需 `EnableGapProtection` 且全端同值」 | 有标注 | P1 |
| G5.2 | 文档写明：图面只决定开局初值；读档后以档为准；**禁止**读档后热更图面覆盖存档 | 有说明 | P1 |
| G5.3 | 触发器链序 / `[Tags]` 声明序被列为「存档敏感」，工具侧不得重排 | 有约束 | P1 |
| G5.4 | 伪造 `.SAV` 投毒面（Trigger 链序/`Enabled`/`OccuredEvents`）已知会；版本门**不是**完整性校验 | 已知会 | P1 |

### G6 · 收口与回归（P0）

| ID | 检查项 | 判定 | 等级 |
|---|---|---|---|
| G6.1 | 字节断言全绿：`R_sav_prod/claims.txt` OK=90 FAIL=0；`save_blocks/claims.txt` OK=82；`da4/claims.txt` 12/12 | 全 OK | P0 |
| G6.2 | 安装/卸载对称：装 P-2.x 后存档有标记；卸载还原 6B 后**新档无标记**、旧档按 G3 矩阵处理 | 对称 | P0 |
| G6.3 | 样例档矩阵自测：原版档×原版端、补丁档×补丁端、原版档×补丁端、补丁档×原版端 —— 四格结果与 §2.3 一致 | 四格过 | P0 |
| G6.4 | U-1（35 块类名）仍 `[待实测]`：产品文案**不得**写具体块类名 | 无越权命名 | P1 |
| G6.5 | 本清单版本与 `R_sav_prod/cross_check_report.md` 同源；变更须同步 claims | 同源 | P1 |

---

## 5. 禁止事项（安装包 / 补丁器硬红线）

| # | 禁止 | 后果 |
|---|---|---|
| X1 | 改 `Internal Version = 0x0002B898` | 原版档全拒；触 manifest §12.5 |
| X2 | 改 `CONTENTS` 字段序 / Count / 35 块调用序 | 流错位、读档崩溃 |
| X3 | 改 `CurrentFrame`（S-1）或 RNG 状态 | 触发器错乱 / 联机 desync |
| X4 | 把 VXL/audio 补丁写入**语义**标记流 | 表现层档被误拒（过度拒绝） |
| X5 | 用「存档版本门」当防篡改/完整性校验 | 伪造档仍可投毒 Trigger |
| X6 | 产品文案假设「块名 = 类名」 | U-1 未闭环 |
| X7 | A/B 两条补丁路径同时生效 | 双写 6B，还原契约破裂 |
| X8 | 在 `MpActive` 下安装 P-2.x 而不握手 | 混端 DESYNC（极高） |

---

## 6. 风险速查

| ID | 风险 | 等级 | 缓解 |
|---|---|---|---|
| R-1 | 混端 → 第一次开图后 `+0x134` 分叉 → 间接 DESYNC | 极高 | G4.1/G4.2 + §2.3 |
| R-2 | 补丁档被原版读取（或反向）→ 裂缝语义错乱 | 高 | G2/G3 标记流 + 拒读 |
| R-3 | 误改 `Internal Version` → 原版全拒 | 高 | X1 |
| R-4 | VXL/audio 进语义标记 → 过度拒绝 | 中 | X4 |
| R-5 | 图面热更覆盖存档的误解 | 中 | G5.2 |
| R-6 | 标记流被当作完整性校验 | 中 | G5.4 / X5 |
| R-7 | U-1 未闭环 → 文案误写块名 | 低 | G6.4 / X6 |
| R-8 | 补丁档 + 关闸读取 → `+0x134` 假活/假死 | 中 | §2.3「有+0」拒读 |

---

## 7. 证据等级与未闭环

| 断言 | 等级 |
|---|---|
| B1–B7 事实基线 | `[实证]` |
| 标记流前向兼容（原版忽略未知流） | `[推演]`（由按名 `OpenStream` 实证推导） |
| 仅 P-2.x 需语义标记 | `[推演]`（补丁触面推导） |
| ra2forge 字段进档并可被污染 | `[实证]`（ABI/入档链）+ `[推演]`（后果） |
| 拒读矩阵可落地 | `[推演]`（静态可写，未真机） |
| 真机读写档对拍 / 四格矩阵 / U-1 类名 / MP 5000 帧 CRC | **`[待实测]`** |

**复算入口**：

```powershell
python out/re_work/re_sprint/R_sav_prod/tools/cross_check_manifest.py
# -> out/re_work/re_sprint/R_sav_prod/claims.txt  (OK=90 FAIL=0)
```

**交叉报告**：`out/re_work/re_sprint/R_sav_prod/cross_check_report.md`
