# Trigger / Tag 进档污染路径（R-TRG-SAV）

> **文档标识**：`docs/re/trigger_save_pollution.md`
> **上游**：`docs/re/trigger_tag_abi_deep_dive.md`（R-08 ABI）、`docs/re/trigger_determinism_deep_dive.md`（T8）、
> `docs/re/savegame_block_manifest.md`（S-1 / 35 块 / 28 向量）、`docs/re/savegame_product_checklist.md`（R-SAV-PROD）、
> `docs/re/sav_gap_cell_abi_deep_dive.md`（T7 Cell）、`docs/re/sbh_uaf_residual_deep_dive.md`（T20）、
> `docs/re/ARCHITECTURE_ATLAS.md` §14/§15（C10）
> **产物**：`out/re_work/re_sprint/R_trg_sav/**`（claims **OK=23 / FAIL=0**）
> **目标二进制**：`ra2youli/gamemd.exe` 1.001（ImageBase `0x400000`，`file_off = VA − 0x400000`）。方法：全静态，未启动游戏。
> 【W3 勘误 E-W3-01】原句 `FileOffset = VA − 0x400000` 仅在 `.text/.rdata/.data` 成立；
> 通用式为 `FileOffset = 段.PointerToRawData + (VA − 段.VirtualAddress)`，
> 本镜像 `.rsrc`/`.detour` 为 `VA − 0x6FC000`。依据：out/re_work/_lead_baseline/W3/LEAD_ERRATUM_E-W3-01_fileoffset_rule.md；分级：[实证]
> **写域**：本文件 + `out/re_work/re_sprint/R_trg_sav/**`。**不写** `ra2render/**` / `gamemd.exe` / `tools/**` / 台账 / 看板 / Atlas。

---

## 0. 一句话

**Trigger `0x48` / Tag `0x38` 的运行时状态会随 `.SAV` 进档并可被伪造档污染；
求值序三层（Tag 向量序 / Tag→Trigger 头插序 / Trigger→Event 尾接序）= 语义，任一重排即不可复现；
ra2forge 图面只给开局初值，安装包必须按 §5 文案写明「图面 ≠ 存档、存档敏感序禁重排、版本门非完整性校验」。**

---

## 1. 结论速览

| # | 结论 | 等级 |
|---|---|---|
| **A1** | `TriggerClass` Size=`0x48`（`0x726930`），`TagClass` Size=`0x38`（`0x6E5890`）；T28 污染面定谳。 | [实证] |
| **A2** | 入档链：`Game::Save_Core 0x67D300` → S-1 标量块 `0x67F7E0`（含 `CurrentFrame` + Tag 向量）+ 35 模板块 + 28 向量块。 | [实证] |
| **A3** | Tag 向量 `0x8B40C8` **整表进档、按原序重建**（`0x67F8C5` 写 / `0x67FB8A`+`0x67FB9D` 重建）。**序 = 语义**。 | [实证] |
| **A4** | `TriggerClass` 可污染字段：`Type/NextTrigger/House/Destroyed/Timer(12B)/OccuredEvents/Enabled`；`TagClass`：`Type/FirstTrigger/InstanceCount/DefaultCoords/Destroyed/IsExecuting`。 | [实证] |
| **A5** | `OccuredEvents` **位序 = 事件链位次**；`[Events]` 事件序被重排 = 位图整体错位。硬不变量。 | [实证] |
| **A6** | ra2forge 图面（`[Triggers]/[Events]/[Actions]/[Tags]`）**只决定开局初值**；读档后以档为准。 | [实证]+[推演] |
| **A7** | Tag 序重建缺口 6 项（G1 标量是否随档为 P0 待实测），见产物 `tag_rebuild_gaps.md`。 | 混合 |
| **A8** | 安装包存档文案建议见 §5（四段成稿 + 排查 FAQ）。 | 交付 |

---

## 2. T28 污染面：Trigger `0x48` / Tag `0x38` 字段级

### 2.1 TriggerClass（Size `0x48`）

| 偏移 | 字段 | 进档 | 污染后果 | ra2forge 图面 |
|---|---|---|---|---|
| `+0x24` | `Type` (TriggerTypeClass*) | 是 | 归属漂移 / TriggerType 错绑 | `HOUSE` |
| `+0x28` | `NextTrigger`（链） | 是 | **链序错乱 → OccuredEvents 位序错位** | `LINKED` |
| `+0x2C` | `House` | 是 | 归属漂移 | `HOUSE` |
| `+0x30` | `Destroyed` | 是 | 误判已摧毁 → 永久静默 | 一次性条件 |
| `+0x34` | `Timer.StartTime` | 是 | 定时器相位错乱 | `Events` delay |
| `+0x38` | `Timer.<anon>` | 是 | 匿名 dword（checksum 跳过；语义 U-5） | delay |
| `+0x3C` | `Timer.TimeLeft` | 是 | 剩余帧错乱 → 延时事件错位 | `TimerExpired` |
| `+0x40` | `OccuredEvents` 位图 | 是 | **位序错位 / 重触发或漏触发** | `Events` 位次 |
| `+0x44` | `Enabled` | 是 | 启用态被覆盖 → 静默或误启 | `DISABLED` / Action 53 |

门控：`RegisterEvent 0x7264C0` / `FireActions 0x7265C0` 双点同义 —— `Enabled==0` 或 `Destroyed!=0` 即 `ret0`。
⇒ 污染 `+0x44`/`+0x30` 任一字节即可**整触发器静默**。

### 2.2 TagClass（Size `0x38`）

| 偏移 | 字段 | 进档 | 污染后果 | ra2forge 图面 |
|---|---|---|---|---|
| `+0x24` | `Type` (TagTypeClass*) | 是 | TagType 错绑 / Persistence 错位 | `[Tags]` 第 2 字段 |
| `+0x28` | `FirstTrigger`（头插链） | 是 | 链断裂 / 头插序被覆盖 | `[Tags]`→`[Triggers]` |
| `+0x2C` | `InstanceCount` | 是 | 重复触发计数漂移 | `REPEATING` |
| `+0x30` | `DefaultCoords` | 是 | 默认坐标漂移 | — |
| `+0x34` | `Destroyed` | 是 | 误判已摧毁 | 一次性 Tag |
| `+0x35` | `IsExecuting`（重入锁） | 是 | **误判执行中 → RaiseEvent 永久拒绝** | — |

**注意**：`TagClass` **无 `+0x44`**；`+0x44` 属 `TriggerClass::Enabled`，勿混（R-08 A2）。

### 2.3 向量 / 标量级

| 单元 | 进档 | 语义 | 污染 |
|---|---|---|---|
| Tag 向量 `0x8B40C8`（S-1） | 整表 | **下标升序 = 注册序 = 每帧求值序** | 重排即错位 |
| Tag 向量 `0x8B41A8`（anyevent） | 整表 | bit2 注册序 | 同上 |
| `TagClass::Array 0xB0E720` | 对象表 | 创建/销毁序 | GetInstance 命中漂移 |
| `CurrentFrame 0xA8ED84`（S-1） | 标量 | 全局帧钟 | **全部 Timer/触发器时刻错乱** |
| RNG（`ScenarioClass::Random+0x218`） | 状态字 | 确定性流 | desync / 不可复现 |

---

## 3. 入档 / 读档路径（Trigger/Tag 专项）

```
Game::Save 0x67D0C0
  └─ Game::Save_Core 0x67D300
       ├─ call S-1 writer 0x67F7E0          @ 0x67D421
       │    ├─ push CurrentFrame 0xA8ED84   @ 0x67F819
       │    └─ write Tag vector 0x8B40C8    @ 0x67F8C5   ★ 整表按当前序
       ├─ 28 内联向量块
       └─ 35 模板块（OLE CLSID）
            ├─ TriggerClass::Save 0x7268D0  → 基类 0x410320（U-1：标量是否随档）
            └─ TagClass::Save 0x6E57A0      → 基类 0x410320（同上）

Game::Load 0x67CEF0
  ├─ 版本闸 Internal Version = 0x0002B898（禁改）
  ├─ OpenStream("CONTENTS") 0x67E56C
  └─ Game::Load_Core 0x67E440
       ├─ call S-1 reader 0x67F9C0          @ 0x67E8B5
       │    ├─ read CurrentFrame
       │    └─ rebuild Tag vector 按原序    @ 0x67FB8A / 0x67FB9D  ★ 尾接保序
       ├─ TriggerClass::Load 0x726860       → 读 +0x24/+0x28/+0x2C（0x6CF240）
       └─ TagClass::Load 0x6E5730           → 读 +0x24/+0x28
```

**关键不对称（U-1，P0 待实测）**：Load 读指针字段，Save 只见基类倾倒 `0x410320`。
两种情形都会让 Trigger/Tag 语义漂移：
- 若倾倒器写整对象裸块 → 运行时字段（Destroyed/Timer/OccuredEvents/Enabled/InstanceCount/IsExecuting）**进档可被污染**；
- 若只写基类 → 读档后被 ctor 初值覆盖（`Enabled` 重置 1、Timer 相位重置）→ **同样错乱**。

---

## 4. Tag 序重建缺口（摘要，全文见产物 `tag_rebuild_gaps.md`）

| ID | 缺口 | 等级 | 产品临时处置 |
|---|---|---|---|
| **G1** | Trigger/Tag 标量是否随档（U-1） | **P0 [待实测]** | 文案写「触发器状态可能被存档覆盖」 |
| G2 | `TagTypeClass::Array` 加载序 = INI 文本序？ | P1 [待实测] | 声明序稳定；少用同帧竞争 |
| G3 | Tag→Trigger 头插链序重建保真 | P1 [推演] | 一 Tag 一 Trigger |
| G4 | 延迟析构队列 `0xB0F698` 是否进档 | P2 [待实测] | — |
| G5 | `IsExecuting` 进档语义 | P1 [推演] | FAQ 含静默排查 |
| **G6** | `OccuredEvents` 位序 = 事件链位次 | **P0 [实证]** | **禁止重排 `[Events]` 序** |

**硬不变量（G6）**：`OccuredEvents` bit i = 第 i 个 Event 是否已发生。
`[Events]` 事件序被工具重排而沿用旧存档 = 位图与事件不对位 = 已发生/未发生判定全面漂移。

**存档敏感序三元组**（任一变更须弃用旧档）：
1. `[Tags]` 声明序（= Tag 向量求值序）
2. `[Events]` 事件序（= OccuredEvents 位序）
3. `[Triggers]` 链接序（`LINKED` / `NextTrigger`）

---

## 5. 安装包存档文案建议（成稿，可直接抄）

### 5.1 主文案（安装包「存档说明」段）

> **关于存档与地图**
>
> 1. **地图只决定开局初值**。任务简报里的触发器、事件、动作、标签只在**首次开局**生效；
>    **存档之后，一切以存档为准**。读档后再修改地图文件不会改变已保存的进度。
> 2. **触发器状态会写入存档**。启用/禁用、是否已触发、计时器剩余、触发次数等都会随档保存；
>    因此**伪造或篡改存档可以让任务逻辑错乱**（例如触发器突然全部静默、计时器错位、重复触发）。
> 3. **存档版本门不是完整性校验**。它只识别存档格式与补丁身份，**不能**防止伪造档或恶意改档。
> 4. **触发器顺序是存档敏感的**：标签声明顺序、事件顺序、触发器链接顺序三者任一被工具重排，
>    **旧存档即不可信**，请开新档。任务编辑器/导出工具不得重排上述顺序。

### 5.2 依赖裂缝迷雾的地图（若有 P-2.x）

> 本任务使用裂缝保护语义，需要 `EnableGapProtection=1` 且**所有联机端同值**。
> 【W3 勘误 · W3-A6/ISSUE-DEFAULT-GAPPROTECTION】改前：EnableGapProtection=1；改后：EnableGapProtection=0  ; [代码/出厂默认0，安全侧；测试或启用时显式置1]；依据：ra2render/blitter_hooks.cpp:606; ra2render/ra2render.ini:199; config_key_matrix.md:109；分级：P0
> 补丁档与原版档**不可混读**；混端（一端补丁、一端原版）将**拒绝开局**。

### 5.3 排查 FAQ（售后三问）

| 症状 | 优先怀疑 | 处置 |
|---|---|---|
| 触发器突然全部静默 | 存档被改 `Enabled` / `Destroyed` / `IsExecuting` | 弃用该档，开新档；检查是否用过改档器 |
| 计时器 / 延时事件错位 | `CurrentFrame` 或 `Timer.StartTime` / `TimeLeft` 被改 | 同上 |
| 重复触发 / 事件重复执行 | `InstanceCount` 或 `Persistence`（`[Tags]` 首字段）被改 | 同上 |

### 5.4 文案红线（禁止出现的表述）

| 禁止 | 正确 |
|---|---|
| 「存档版本门可防止存档被篡改」 | 「版本门只识别格式/补丁身份，不是完整性校验」 |
| 「地图改了以后读档也会生效」 | 「图面只决定开局初值，读档后以档为准」 |
| 「触发器由地图文件唯一决定」 | 「触发器状态随档保存，可被存档覆盖」 |
| 「块名 = 类名」（U-1 未闭环） | 不写具体块类名 |

---

## 6. ra2forge 触发器存读档核对点（摘要，全文见产物 `ra2forge_checkpoints.md`）

| 类 | 核对点 | 等级 |
|---|---|---|
| 导出 | `[Tags]` 声明序 = 导出文本序 = 预期求值序 | **P0** |
| 导出 | 同一 design 两次导出 `[Tags]/[Events]/[Actions]/[Triggers]` 逐字节一致 | **P0** |
| 导出 | `LINKED` 指向有效 Trigger ID 或 `<none>`；`tag_id` 唯一且存在 | **P0** |
| 导出 | `repeating` 只写 `[Tags]` 首字段；`[Triggers]` 尾字段恒 0（现状） | P1 |
| 导出 | 多波次增援用 `repeating=1/2`（默认 0 = Volatile 一次即销毁） | P1 |
| 导出 | `ElapsedTime` 单位 = 秒（`Duration=15*arg` 逻辑帧） | P1 |
| 读档 | **图面 ≠ 存档**；读档后以档为准 | **P0** |
| 读档 | 存档敏感序三元组任一变更须弃用旧档 | **P0** |
| 读档 | 版本门 ≠ 完整性校验；伪造档可投毒 Trigger | **P0** |
| 读档 | 静默/计时器错乱/重复触发 三类排查提示已写入 FAQ | P1 |

**现状偏差登记（P1）**：`maplib.py:448-449` 将 `[Triggers]` 第 8 字段（REPEATING）写死 `0`，
而 `make_trigger(repeating=…)` 只写入 `[Tags]`。引擎 Persistence 由 `TagTypeClass+0x9C`（Tags 首字段）决定；
两者是否同义需对照官方图。**建议以 Tags 为准并在文档声明**；若官方图要求同步写，记录偏差。

---

## 7. 与 T8 确定性的耦合

| 序层 | 结构 | 插入 | 求值序 | 存档 |
|---|---|---|---|---|
| Tag 名单 | `0x8B40C8` | 尾接 | 下标升序 = 注册序 | **整表进档 / 按原序重建** |
| Tag→Trigger | `Tag+0x28` | **头插** | 创建序逆序 | 指针字段（G1/G3） |
| Trigger→Event | 单链尾接 | 尾接 | INI 序；**位图位次 = 链位次** | 指针字段 + 位图（G6） |

**T8 原结论**：求值/执行顺序全为插入序，全链无指针比较/地址哈希。
**本卡补充**：这三层序**全部进档**，因此「确定性」在存档面的充分条件是
**三层序在写档前一致、读档后保序、工具不重排**。任一层被重排，确定性即退化为不可复现。

另：`IgnoreGlobalAITriggers=yes`（ra2forge `maplib.py:230`）可整体关掉 AITrigger，
消除 AITrigger RNG 消费面，**有利确定性**。

---

## 8. 风险速查

| ID | 风险 | 等级 | 缓解 |
|---|---|---|---|
| R-1 | 伪造 `.SAV` 投毒 Trigger 链序/Enabled/OccuredEvents | **高** | §5.1 文案 2/3；版本门不当完整性校验 |
| R-2 | 工具重排 `[Tags]/[Events]/[Triggers]` 导致旧档不可信 | **高** | §6 导出核对点 CHK-S1/S2/S3 |
| R-3 | G1 未闭环 → 文案口径摇摆（状态进档 vs 被 ctor 覆盖） | 中 | 两种情形统一写成「状态可被存档覆盖」 |
| R-4 | `IsExecuting` 被污染为 1 → Tag 永久静默 | 中 | FAQ 排查提示 |
| R-5 | 图面热更覆盖存档的误解 | 中 | §5.1 文案 1 |
| R-6 | 同帧多 Tag 竞争 + G2 加载序未闭环 | 中 | 少用同帧竞争；声明序稳定 |
| R-7 | 混端读档（P-2.x）→ 裂缝语义分叉 | 极高 | §5.2 + 标记流拒读矩阵（R-SAV-PROD §2.3） |

---

## 9. 证据等级与未闭环

| 断言 | 等级 |
|---|---|
| A1–A5（ABI / 入档链 / Tag 向量序 / 字段污染面 / 位序不变量） | `[实证]`（claims 23/23 OK） |
| A6（图面 ≠ 存档） | `[实证]`（入档链）+ `[推演]`（后果） |
| G1 Trigger/Tag 标量是否随档 | **`[待实测]`**（U-1，P0） |
| G2 TagType 加载序 = INI 序 | **`[待实测]`** |
| G3/G5（链序保真 / IsExecuting） | `[推演]` |
| G4 延迟析构队列进档 | **`[待实测]`** |
| 安装包文案可落地 | `[推演]`（静态成稿，未真机） |

**复算入口**：

```powershell
python out/re_work/re_sprint/R_trg_sav/tools/verify_trg_sav.py
# -> SUMMARY ok=23 fail=0
```

**产物索引**：`out/re_work/re_sprint/R_trg_sav/INDEX.md`

---

## 10. 交付边界

- 本文档**不改** `trigger_runtime_deep_dive.md` / `trigger_system_manifest.md` / `trigger_tag_abi_deep_dive.md` / Atlas / 台账 / 看板。
- 与 `savegame_product_checklist.md` §3（ra2forge 进档污染面）为**互补细化**，字段级以本文 §2 为准，安装包出厂门禁仍以 G0–G6 为准。
- 若 G1 闭环后结论为「标量不随档」，须回写本文 §3 口径并同步 `savegame_product_checklist.md` §3 表格。
