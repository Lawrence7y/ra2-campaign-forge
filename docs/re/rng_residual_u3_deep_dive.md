# RNG 残差 U-3 深潜（R-RNG-U3）

> **目标二进制**：`ra2youli\gamemd.exe` 1.001（ImageBase `0x400000`）
> **证据分级**：`[实证]` = VA + 机器码（本轮 `out/re_work/re_sprint/R_rng_u3/identify_sites.py` 复算）；`[推演]` = 相邻实证 + x86/MSVC 习惯；`[待实测]` = 需真机。
> **边界**：本专章收口 R-TRIG-DET 遗留 U-3 残差（`0x722xxx` 簇 5×Random + `0x720ABE` + `0x55DE08`）；触发器状态机见 `trigger_determinism_deep_dive.md`；RNG 红线见 `net_sync_checksum.md`。
> **工作区**：`out/re_work/re_sprint/R_rng_u3/`（claims.txt / risk_table.md / identify_sites.py）

---

## 0. 结论速览

1. **`0x722xxx` 簇 5×`Random()` 归属 TiberiumClass 环境格生长调度**，非 TriggerTypeClass / AI / 网络。原「与 TriggerTypeClass 同区」为地址巧合。[实证]
2. **`0x720ABE` 归属 ThemeClass 音乐选曲**（`Theme::AI`），使用 `Randomizer::Global`（局外本地）→ **SAFE**。[实证]
3. **`0x55DE08` 是 MainLogicFrame 帧尾 RNG burn**：`RandomRanged(0,2)` 返回值被丢弃，纯消耗同步流 → **VIOLATION**，绝对禁止短路。[实证]
4. **0x722xxx 簇消费次数 = 合格格数**（每合格格 1×`Random()`），条件短路改序列 → **RISK** 禁区。[实证]
5. 与 S26 RNG 实例归属完全一致：局内 = `ScenarioClass::Random`；局外 = `Randomizer::Global`。无第三实例。[实证]

---

## 1. 站点清单与归属

### 1.1 总表

| # | VA | 调用 | PRNG 实例 | 所属系统 | 所属函数 | 分类 |
|---|---|---|---|---|---|---|
| 1 | `0x7224B9` | `Random()` | ScenarioRandom | TiberiumClass 生长调度 | fn `0x7224AE`（mid-label，真起点 ~`0x722440`） | RISK |
| 2 | `0x722B67` | `Random()` | ScenarioRandom | TiberiumClass 生长调度 | fn `0x722AF0` | RISK |
| 3 | `0x722F75` | `Random()` | ScenarioRandom | TiberiumClass 生长调度 | fn `0x722F6A`（mid-label，真起点 `0x722F00`） | RISK |
| 4 | `0x72304A` | `Random()` | ScenarioRandom | TiberiumClass 生长调度（堆插入） | fn `0x722FF2` | RISK |
| 5 | `0x723604` | `Random()` | ScenarioRandom | TiberiumClass 生长调度 | fn `0x7235A0` | RISK |
| 6 | `0x720ABE` | `RandomRanged()` | **Randomizer::Global** | ThemeClass 音乐选曲 | fn `0x720A80` | **SAFE** |
| 7 | `0x55DE08` | `RandomRanged(0,2)` | ScenarioRandom | MainLogicFrame 帧尾 burn | MainLogicFrame `0x55D360` 内 | **VIOLATION** |

### 1.2 归属证据链

#### `0x722xxx` 簇 → TiberiumClass

- 全部 5 站 `lea ecx,[0xA8B230]+0x218` → `call 0x65C780`（`ScenarioRandom`）[实证]
- 函数体使用 `0x42B1C0`（格坐标→索引）、`0x42B1F0`（总格数）[实证]
- 操作 `0xB0F4EC`（对象数组）+ `0xB0F4F8`（计数）[实证]
- `Random()%50` + `CurrentFrame`（`[0xA8ED84]`）→ 浮点定时器写入堆节点 `[+4]` [实证]
- `0x722FF2` 是优先队列插入（sift-up 比较 `[node+4]` 浮点）[实证]
- `TiberiumClass` 虚表 vfunc 紧邻 `0x7236E0-0x723700`；`DynamicVectorClass<TiberiumClass*>` 在 `0x723730+` [实证]
- `0x722240` 是 Load_Core 家族外块读取器（ATLAS R5 已证 RNG 零命中），`0x722xxx` 簇是其邻居——同属 Tiberium 存档/运行时体系 [实证]

**调用者**：
- `0x722AF0` ← `0x480B4F`（地图区域更新器）、`0x4875A4`（房级格扫描）、`0x722FF2`（内部堆弹出）
- `0x7235A0` ← `0x480BA1`、`0x487289`、`0x74A477`、`0x74A6CC`（全部 Tiberium 生长派发器）
- `0x7224AE` / `0x722F6A` 无直接 call/jmp xref——mid-function label，由前置块 fall-through / jmp 进入 [实证]

#### `0x720ABE` → ThemeClass（SAFE）

- `mov ecx,0x886B88`（`Randomizer::Global`）→ `call 0x65C7E0` [实证]
- 调用者 `0x720A53` in `0x7209D0`；字符串 `0x8447B8` = `"Theme::AI(Next song = %d)\n"` [实证]
- 门控 `[0xA8EC74]`（主题系统启用）、`[0xA8ED64]`（游戏结束）[实证]
- **局外本地 RNG，不进同步流** → 短路零确定性影响 [实证]

#### `0x55DE08` → MainLogicFrame 帧尾 burn（VIOLATION）

- `push 2; push edi(=0); lea ecx,[0xA8B230]+0x218; call 0x65C7E0` → `RandomRanged(0,2)` [实证]
- **返回值丢弃**：`0x55DE0D` 立即 `call [0x7E1530]` 覆盖 eax [实证]
- 门控：`GameMode[0xA8B238]∈{3,4}`、`[0xA8B23c]` 非空、虚表 `[edx+4]` 返回 false、玩家对象 `[obj+0x130]==1` 或 `[obj+0x12c]&0x18` [实证]
- 位于轮询器 `0x55DC9E` 之后、`CurrentFrame++` 附近 [实证]
- **纯消耗同步流**——任何跳过/改次数即联机分叉（帧 CRC `0x64DE3F` 当帧打出）[实证]

---

## 2. 消费次数与确定性影响

| 站点 | 每帧/每事件消费 | 可跳过？ | 跳过后果 |
|---|---|---|---|
| `0x722xxx` ×5 | 每合格格 1×`Random()`；合格格数由格状态决定 | 仅当合格格=0（原版已有早退） | 改条件短路 → RNG 序列错位 → 联机分叉 |
| `0x720ABE` | 每次选曲 1×`RandomRanged` | 是 | **无**（局外 RNG） |
| `0x55DE08` | 每帧 ≤1×`RandomRanged(0,2)` | **否** | 移除 → 同步流错位 → 当帧 CRC 分叉 |

---

## 3. 禁区清单（性能短路优化）

### 🔴 禁区 1：`0x55DE08` — 绝对禁止

- 返回值丢弃，纯 RNG burn。
- 禁改：调用次数、门控条件、`RandomRanged` 参数。
- 唯一「安全」做法 = 原样保留。

### 🔴 禁区 2：`0x722xxx` 簇 — 禁止条件短路

- 5 站共享同一条 `ScenarioRandom` 流；跳过任一即后续全错位。
- 禁改：调用次数、`idiv` 模数（50 或 5..50 浮点钳制）、合格格判定边界。
- 允许：原版「合格格=0 时不消费」的早退（多端一致）。

### 🟡 禁区 3：`0x720ABE` — 可安全短路

- `Randomizer::Global`，不进同步流。短路只影响本机音乐。

---

## 4. 与 ScenarioRandom / S26 交叉

| 实例 | 地址 | 用途 | 本任务命中 |
|---|---|---|---|
| `ScenarioClass::Random` | `[0xA8B230]+0x218` | 局内同步 | 0x7224B9 / 0x722B67 / 0x722F75 / 0x72304A / 0x723604 / 0x55DE08 |
| `Randomizer::Global` | `0x886B88` | 局外本地 | 0x720ABE |

与 S26 结论一致。`0x722xxx` 簇归属 **TiberiumClass**，不是 TriggerTypeClass / AI / 网络。原 U-3「紧邻 TriggerTypeClass」为地址巧合（`0x722xxx` 在 TiberiumClass 与 TriggerTypeClass `0x726xxx` 之间）。

---

## 5. 证据计数

- `[实证]` 12 · `[推演]` 1 · `[待实测]` 0
- 判定：**VIOLATION 1 · RISK 5 · SAFE 1**（+ 4 个 0x74Axxx 关联站点 RISK）

---

## 6. 只读引用

- `docs/re/trigger_determinism_deep_dive.md`（R-TRIG-DET U-3 原文）
- `docs/re/net_sync_checksum.md`（RNG/帧 CRC 红线）
- `docs/re/trigger_runtime_deep_dive.md`（PRNG 实例归属）
- `docs/re/ARCHITECTURE_ATLAS.md` §14 U-3 / §16.4
- `out/re_work/re_sprint/R_rng_u3/claims.txt`
- `out/re_work/re_sprint/R_rng_u3/risk_table.md`
- `out/re_work/re_sprint/R_rng_u3/identify_sites.py`
