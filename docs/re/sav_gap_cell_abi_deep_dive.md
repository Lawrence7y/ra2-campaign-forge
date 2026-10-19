# R-SAV-GAP 深潜：Cell 块 `.SAV` ABI 与 `GapsCoveringThisCell` 入档/同步/重建

任务：**R-SAV-GAP** ｜ 目标二进制：`ra2youli/gamemd.exe`（1.001，ImageBase `0x400000`，文件偏移 = VA − 0x400000）
> 【W3 勘误 E-W3-01】原句 `FileOffset = VA − 0x400000` 仅在 `.text/.rdata/.data` 成立；
> 通用式为 `FileOffset = 段.PointerToRawData + (VA − 段.VirtualAddress)`，
> 本镜像 `.rsrc`/`.detour` 为 `VA − 0x6FC000`。依据：out/re_work/_lead_baseline/W3/LEAD_ERRATUM_E-W3-01_fileoffset_rule.md；分级：[实证]
方法：**全静态**（python3 + pefile + capstone 5.0.7），未启动游戏。
证据三档：`[实证]` 字节/反汇编可复算；`[推演]` 由实证链推导；`[待实测]` 需真机。

字节断言与复算脚本：`out/re_work/re_sprint/R_sav_gap/`（§7）。
关联文档：`savegame_block_manifest.md`、`net_sync_checksum.md`、`gap_psychic_reveal_deep_dive.md`、`landing_pack_gap_p21.md`。

---

## 0. 结论速览

| 项 | 结论 | 等级 |
|---|---|---|
| **三字段是否入档** | **是，全部入档**。`+0x12C CopyFlags` / `+0x130 ShroudCounter` / `+0x134 GapsCoveringThisCell` 落在 `CellClass` 原始块 `0x148` B 内，无字段级过滤、无独立压缩 | `[实证]` |
| Cell 入档路径 | `Game::Save_Core 0x67D300` → `MapClass::Save 0x5BE6D0` → `CellIteratorReset/Next 0x578350/0x578290` → 逐格 `ole32!OleSaveToStream` → `CellClass::Save 0x483C10` → 通用倾倒器 `0x410320`（写 4 B 对象指针 + **`GetSize()=0x148` 裸字节**）+ `FoggedObjects(+0x28)` 向量 | `[实证]` |
| 读档对称路径 | `Game::Load_Core 0x67E440` → `MapClass::Load 0x5BDF70` → `CellClass::Load 0x4839F0` → `0x410380`（读 4 B + 0x148 裸字节）→ 指针 swizzle `0x6CF240`（仅 +0x2C/+0x30/+0x3C/+0x40/+0xE0/+0xE4/+0xE8/+0xF8）→ 重建 `FoggedObjects` → 重注册格子索引 `0x87F924` | `[实证]` |
| 序列化顺序/压缩 | 每格：`[obj_ptr:4][raw 0x148]`，再 `FoggedObjects` count+items；格子按 `CellIterator` 序；**无 RLE/位打包**；容器层 OLE2/CFB（见 `savegame_block_manifest.md §5`） | `[实证]` |
| 版本闸 | 仅流级 `Internal Version = 0x2B898`（`Game::Savegame_Magic @ 0x83D560`）；**无 Cell 块版本、无字段版本** | `[实证]` |
| 补丁档可否区分 | **格式面不可区分**（布局/尺寸与原版逐字节同构）；只能靠**值域差异**（`+0x134` 演化不同）或**新增 OLE 流做标记**（原版读档按名开流，多余流被忽略） | `[实证]`+`[推演]` |
| `+0x134==0` 可否重建 | **架构上可**：在世 `GapGenerator` 建筑（类型 + 坐标 + `GeneratingGap`）全部在档；但原版读档**不**重放 `CreateGap` ⇒ 补丁侧需自写 post-load 重建扫描 | `[实证]`（输入在档）+`[推演]`（需补丁扫描） |
| 进帧 CRC？ | **不直接进**。`CellClass::CalculateChecksum` v[13]=`0x410410` 只折叠 `cell+0x10`(dword)+`cell+0x20`(byte)；帧 CRC `0x64DAB0` 只哈希 Infantry/Unit/Building 量化坐标。但 `+0x134` 主导索敌/可见性谓词 ⇒ **间接分叉 → 坐标分叉 → DESYNC** | `[实证]`（CRC 面）+`[推演]`（间接） |
| MP/存档门控 | 全端同 `EnableGapProtection`；补丁档加 OLE 标记流；混端禁联；读档后可选重建；**禁改** `Internal Version` | 见 §6 |

---

## 1. Cell 块布局（序列化 ABI）

### 1.1 倾倒原语：`0x410320` / `0x410380`（`[实证]`）

全镜像通用对象倾倒器（Save 侧 54 个调用者 / Load 侧 42 个，含 `CellClass::Save/Load`）：

**Save `0x410320`**（stdcall，obj / stream / flag）：
```
0x410334  mov  edi, [esp+0xc]        ; obj
0x410338  mov  eax, [esi]            ; stream vtbl
0x410344  mov  [esp+0x20], edi       ; buf = obj 指针
0x410348  call [eax+0x10]            ; IStream::Write(4, &obj_ptr)   ← 对象指针头
0x41034F  mov  edx, [edi]            ; obj vtbl
0x410358  call [edx+0x30]            ; GetSize()
0x41035B  push eax                   ; size
0x41035C  push edi                   ; pv = obj
0x41035E  call [ebx+0x10]            ; IStream::Write(size, obj)     ← 裸内存
0x41036E  mov  byte [edi+0x20], 0    ; 清 dirty
```

**Load `0x410380`**：读 4 B → `0x6CF2C0` 建 swizzle 表 → 读 `GetSize()` B 进对象 → 恢复 `+0x1c`。

**CellClass::GetSize = vtable[0x30] = `0x487E70`**：
```
0x00487E70  b8 48 01 00 00    mov eax, 0x148
0x00487E75  c3                ret
```
`0x148` = `sizeof(CellClass)`（与 YRpp `CellClass` 尾部 `padding_144[4]` 吻合）。

⇒ **每个入档 Cell 在流上的足迹 = 4 + 0x148 = 0x14C B（未计 FoggedObjects 与 OLE 包装）**。

### 1.2 `CellClass::Save 0x483C10` / `Load 0x4839F0`（`[实证]`）

`Save`（50 insns, 0x6F B）：
1. `call 0x410320(this, stream, flag)` — 倾倒 0x148 裸字节；
2. 若 `this+0x28`（`FoggedObjects*`）非空：写 count（4 B）再逐项写 item（4 B 指针，经虚表[0]+OLE）。

`Load`（175 insns, 0x218 B）：
1. `call 0x410380` 恢复 0x148 裸字节 + 指针表；
2. 重建 vptr（`0x7E4EEC/0x7E4ED0/0x7E4EC8/0x7E4EC0`）；
3. 重建 `FoggedObjects` 向量；
4. 按 `MapCoords(x=+0x24,y=+0x26)` 以 `y<<9|x` 重注册进格子索引全局 `0x87F924`；
5. `0x6CF240` swizzle 指针字段：`+0x2C +0x30 +0x3C +0x40 +0xE0 +0xE4 +0xE8 +0xF8`；
6. 特例：`Rubble(+0x44) ∈ {0xB3, 0xF2}` → 置 `0xFFFFFFFF`，`+0x11E` 清 0。

### 1.3 三字段落点（`[实证]`）

| 偏移 | 字段 | 是否在 0x148 裸块内 | Save/Load 内是否有**独立**读写 | 说明 |
|---|---|---|---|---|
| `+0x12C` | `CopyFlags` | **是** | 否（随裸块） | bit3 Explored / bit4 Mapped |
| `+0x130` | `ShroudCounter` | **是** | 否（随裸块） | 遮蔽深度 |
| **`+0x134`** | **`GapsCoveringThisCell`** | **是** | 否（随裸块） | 裂缝引用计数 |

> `CellClass::Save/Load` 函数体对这三个偏移 **0 次** 直接 `disp32` 访问（`out/re_work/re_sprint/R_sav_gap/dumps/cell_save_load_fields.json`）；
> 但它们作为 `0x148` 连续内存的一部分被 `IStream::Write/Read` 整块带走 —— **入档成立**。
> 这与 `net_sync_checksum.md:902`「仅序列化原版格位数据（`CellClass + 0x12C` 迷雾标记等）」**一致且更强**：不只 `+0x12C`，`+0x130/+0x134` 同在。

### 1.4 格子遍历与过滤（`[实证]`）

`MapClass::Save 0x5BE6D0`（由 `Game::Save_Core @ 0x67D3B1` 调）：
```
0x5BE71A  IStream::Write(0x556c, this)     ; MapClass 自身 0x556c B 裸块（含 13 张 tube/索引表）
… count pass …
0x5BE7E2  call CellIteratorReset 0x578350
0x5BE7E9  call CellIteratorNext  0x578290
0x5BE800  call 0x5657E0                   ; 谓词
0x5BE809  inc  count
… write count (4 B) …
… save pass …
0x5BE84F  mov  ebp, [0x7E15F4]            ; ole32!OleSaveToStream
0x5BE86E  call ebp                        ; OleSaveToStream(cell, stream)
```

**谓词 `0x5657E0`**（`[实证]`）：
```
ecx+0x13C = 格子指针表基址
idx = (MapCoords.y << 9) + MapCoords.x
return (table[idx] != 0)
```
⇒ **凡在格子索引中存在的 Cell 全部入档**（无「只存脏格」优化）。

`MapClass::Load 0x5BDF70` 对称（重建 13 表、swizzle、`CellIterator` 重建），并调 `0x581F50` / `0x657CE0`（后者与 `Reshroud` 后刷新同函数，见 `gap_psychic_reveal_deep_dive.md`）。

### 1.5 顺序 / 压缩（`[实证]`）

| 维度 | 值 |
|---|---|
| 单格布局 | `[obj_ptr:u32][raw 0x148]` 然后 `FoggedObjects: count:u32 + item_ptr×count` |
| 格间顺序 | `CellIterator` 行扫描序（`CellIteratorReset` 自 `[Map+0xF4]` 宽、`y` 从 0 起） |
| 字段顺序 | **对象内存地址序**（0x00..0x147），不是字段表序 |
| 压缩 | **无**字段级压缩；整档由 OLE2/CFB 容器承担（`savegame_block_manifest.md §5`） |
| 指针 | 4 B 对象指针头 + `0x6CF240/0x6CF2C0` swizzle 表；**不是**值内编码 |

---

## 2. 版本 / 兼容

### 2.1 版本闸（`[实证]`）

| 项 | 值 / VA |
|---|---|
| 魔数 | `Game::Savegame_Magic @ 0x83D560 = 0x0002B898` |
| 写侧 | OLE 流 `Internal Version`（文件偏移 `0x0C40`，LE32 `98 B8 02 00`） |
| 读侧 | `Game::Load 0x67CF70` `mov eax,[0x83D560]` → `call 0x681080` 比对 |
| Cell 块版本 | **无** |
| 字段级版本 | **无** |

`net_sync_checksum.md §5.1` 已将 `Internal Version` 列为**存档布局红线（禁改）**；本报告维持。

### 2.2 补丁档可否标记区分

**格式面：不可区分。** P-2.1 只把 `mov [reg+0x134],0` 换成 `NOP×6`，不改序列化代码、不改 `GetSize`、不改块序 ⇒ 补丁档与原版档 **ABI 同构**。

**值面：可启发式区分但不可靠。** 补丁档在发生过 `RevealArea2/3` / `Reshroud` 的格子上保留非零 `+0x134`；原版档同场景恒 0。但「从未开过图」的档两者无法区分。

**推荐标记（`[推演]`，静态可写）**：在 `.SAV` 的 OLE 复合文档里**追加自定义流**（如 `GapProt Version`，4 B = 补丁档格式号）。
- 原版读档按**流名**打开 `CONTENTS` / `Internal Version` 等已知流，**多余流被忽略**（`savegame_block_manifest.md §5.2` 目录项按名访问）⇒ 前向兼容；
- 补丁读档侧检查该流：存在 ⇒ 补丁档；不存在且 `EnableGapProtection=1` ⇒ 拒绝加载或强制重建 `+0x134`；
> 【W3 勘误 · W3-A6/ISSUE-DEFAULT-GAPPROTECTION】改前：EnableGapProtection=1；改后：EnableGapProtection=0  ; [代码/出厂默认0，安全侧；测试或启用时显式置1]；依据：ra2render/blitter_hooks.cpp:606; ra2render/ra2render.ini:199; config_key_matrix.md:109；分级：P0
- **禁止**改 `Internal Version=0x2B898` 做标记（会把原版档全拒）。

### 2.3 `+0x134 == 0` 重建可能性

**输入是否在档**（`[实证]`）：

| 重建所需 | 在档？ | 证据 |
|---|---|---|
| 建筑列表（含 GapGenerator） | 是 | `BuildingClass::Array` 在 Save_Core 向量块 #10（`savegame_block_manifest.md §4`） |
| 建筑类型（是否 `GapGenerator`） | 是 | `TechnoType` 经 OLE 持久化 |
| 建筑坐标 | 是 | 对象 `+0x9C` 量化坐标进档（帧 CRC 同源） |
| `GeneratingGap` 跳变状态 | 是 | BuildingClass 状态字段随对象入档 |
| 半径（`SuperGapRadius` / Rules） | 是 | `RulesClass` 块 `0x674730` |

**原版行为（`[实证]`）**：`CreateGap 0x6FB170` 仅在 `GeneratingGap` **跳变**时调用（`inc [cell+0x134]` @ `0x6FB365`），**不**在读档后重放 ⇒ 存档里 `+0x134` 是多少读出来就是多少，**不自愈**。

**重建算法（`[推演]`，补丁侧可实现）**：
1. 读档完成后、进入逻辑帧前；
2. 清零全部 `cell+0x134`（或保留档内值后做差量）；
3. 遍历 `BuildingClass::Array`：`Type->GapGenerator==true && GeneratingGap==true` 的建筑，对其覆盖半径内每格 `cell+0x134++`（对齐 `CreateGap` 的敌我过滤：`0x6FB2D6 call 0x4F9A50` / `jne` 跳过己方/盟友 —— 见 `gap_psychic_reveal_deep_dive.md §2`）；
4. 重建后 `ShroudCounter` 按不变量 I-GAP-1 钳位：`ShroudCounter = max(ShroudCounter, ...)` 不成立，应为 `ReshroudCell` 的钳位语义 `ShroudCounter ≤ GapsCovering`（`0x4876BF`）⇒ 重建后对相关格重跑 `ReshroudCell` 或直接 `ShroudCounter = min(ShroudCounter, newGaps)`。

**结论**：**可以重建**（输入完备）；原版不重建；补丁侧 post-load 扫描是可行门控项。

---

## 3. 同步演进（对照 `net_sync_checksum.md`）

| 层 | 是否覆盖 `+0x134` | 证据 |
|---|---|---|
| `CellClass::CalculateChecksum` v[13]=`0x410410` | **否** — 只 `Add(cell+0x10,4)` + `Add((bool)cell+0x20)` | `[实证]` 反汇编 `0x410418/0x410423` |
| 帧 CRC `0x64DAB0` → `CurrentFrameCRC @ 0xAC51FC` | **否** — 遍历 Infantry(`0xA83DEC`)/Unit(`0x8B410C`)/Building(`0xA8EB44`) 取 `+0x9C` 量化坐标与 `+0x388/+0x3A0`，无 Cell 遍历 | `[实证]` |
| 存档字节流 | **是** — 0x148 裸块内 | `[实证]` |
| 行为分叉 | **是** — `Cell+0x134>0` 是「被敌方裂缝覆盖」索敌/可见性谓词（`gap_psychic_reveal_deep_dive.md §2`、`ARCHITECTURE_ATLAS.md §18.8`） | `[推演]` |
| 存档命令同步 | `NetworkEvent` Kind `0x1D SaveGame` 全端同帧读档；初值一致 | `[实证]`（`savegame_block_manifest.md §0/§6`） |

**净效果**：P-2.1 不改 CRC 算法、不改量化除数；混端（一端 NOP、一端原版）在**第一次 `RevealArea2/3/Reshroud`** 之后 `+0x134` 分叉 → 索敌/可见性分叉 → 单位坐标分叉 → **帧 CRC 间接 DESYNC**。
同构建全端 + 同开关 ⇒ 演化一致 ⇒ 无分叉。

---

## 4. 与既有文档的交叉核对

| 来源 | 说法 | 本报告 |
|---|---|---|
| `net_sync_checksum.md:902` | `CellClass::Save 0x483C10` / `Load 0x4839F0` 仅序列化原版格位数据（`+0x12C` 等） | ✅ 成立；**补强**：整块 `0x148` 裸倾倒，`+0x130/+0x134` 同在，且经 `MapClass::Save` 的 `OleSaveToStream` 循环入档 |
| `savegame_block_manifest.md` | OLE2 容器 + 35 模板块 + 28 内联向量；无裸指针落盘 | ✅ 一致；Cell 走 `OleSaveToStream`（对象寻址=CLSID/swizzle 表），与「无手工 swizzle 表」一致 |
| `gap_psychic_reveal_deep_dive.md` R-2 | `Cell+0x134` 进 `.SAV`，补丁后与原版不互通 | ✅ 实证坐实；「不互通」精确含义 = **格式互通、语义不互通**（值域演化不同），加 OLE 标记流可显式区分 |
| `landing_pack_gap_p21.md` R-1 | 混端 DESYNC，`+0x134` 进 `.SAV` | ✅ 坐实；补充：DESUC 触发点是**补丁后第一次开图事件**，不是读档瞬间 |

---

## 5. P-2.1 落地卡门控建议（静态可写部分）

### 5.1 存档门控

| # | 检查点 | 时机 | 判定 |
|---|---|---|---|
| S-1 | 写档时追加 OLE 流 `GapProt Version`（u32 = 补丁档格式号，建议 `1`） | `Game::Save` / `Save_Core` 收尾 | 流存在 = 补丁档 |
| S-2 | 读档时检查该流 | `Game::Load` 版本闸通过后 | 有流且 `EnableGapProtection=1` → 正常；有流且开关关 → **拒绝**（档内演化依赖 NOP） |
| S-3 | 无流且开关开 | 同上 | 两种策略二选一：**(a)** 拒绝加载原版档；**(b)** 允许加载 + 执行 §2.3 重建扫描后把 `+0x134` 校正到补丁语义 |
| S-4 | **禁改** `Internal Version 0x2B898` | — | 改了原版全拒，红线 |
| S-5 | 卸载补丁（开关关）后不得读补丁档 | 用户侧 | 菜单过滤或读档前检测 S-1 |

### 5.2 MP 门控

| # | 检查点 | 判定 |
|---|---|---|
| M-1 | 握手键/会话键必须包含 `EnableGapProtection`（与构建号一并） | 不一致 → 拒绝开局（`mp_autodowngrade_spec.md` 同族） |
| M-2 | 全端同构建、同开关；**禁止混端联机** | `landing_pack_gap_p21.md` R-1 红线 |
| M-3 | 对局内保存（Kind `0x1D`）后双方立即比对档内 `GapsCoveringThisCell` 抽样哈希（可选，诊断用） | 不一致即刻告警 |
| M-4 | 读档后不重放 `CreateGap`（原版语义）；若做重建，必须**全端同帧同算法** | 单端重建 = 新 DESYNC 源 |

### 5.3 帧 CRC 策略

| # | 建议 |
|---|---|
| C-1 | **不要**把 `+0x134` 塞进 `CellClass::CalculateChecksum`（会改 `*Class::v[13]` 契约 = 改诊断归因面） |
| C-2 | 若需强校验：在补丁侧追加**独立** gap 状态哈希（私有内存，不进 `0x64DAB0`），仅诊断 |
| C-3 | 间接分叉已足够触发原版 DESYNC 检测，无需动 CRC 算法 |

---

## 6. 风险登记

| ID | 风险 | 等级 | 缓解 |
|---|---|---|---|
| R-1 | 混端（一端 P-2.1、一端原版）→ 第一次开图后 `+0x134` 分叉 → DESYNC | 极高 | M-1/M-2 |
| R-2 | 补丁档被原版读取（或反向）→ 裂缝语义错乱、存档不可信 | 高 | S-1/S-2/S-5 |
| R-3 | 读档后 `+0x134` 全 0 且补丁期望非 0 → 裂缝「假活」 | 中 | §2.3 重建或 S-3(a) 拒绝 |
| R-4 | 若实施方误改 `Internal Version` 做标记 → 原版档全拒 | 高 | S-4 红线 |
| R-5 | `FoggedObjects` 与指针 swizzle 集合外的字段在跨版本 PE/不同构建下未验证 | 低 | 本报告只证 1.001 原版字节 |

---

## 7. 复算与产物

### 7.1 脚本（`out/re_work/re_sprint/R_sav_gap/tools/`）

| 脚本 | 作用 |
|---|---|
| `analyze_cell_sav_abi.py` | `CellClass::Save/Load` 反汇编 + 字段偏移提取 + `+0x12C/130/134` disp32 全镜像 xref |
| `analyze_parent_save.py` | 倾倒器 `0x410320/0x410380` / swizzle `0x6CF240` |
| `analyze_mapclass_cell_dump.py` | `MapClass::Save/Load` 字段面 |
| （见 dumps） | `GetSize 0x487E70`、`MapClass::Save 0x5BE6D0`、谓词 `0x5657E0`、帧 CRC `0x64DAB0`、版本闸 `0x67CF70` |

复算：
```powershell
python out/re_work/re_sprint/R_sav_gap/tools/analyze_cell_sav_abi.py
python out/re_work/re_sprint/R_sav_gap/tools/analyze_parent_save.py
python out/re_work/re_sprint/R_sav_gap/tools/analyze_mapclass_cell_dump.py
python out/re_work/re_sprint/R_sav_gap/tools/verify_claims.py
```

### 7.2 字节断言（`claims.txt`，见 `verify_claims.py`）

核心断言（节选）：

| VA | 期望 | 含义 |
|---|---|---|
| `0x00487E70` | `B8 48 01 00 00 C3` | `GetSize → 0x148` |
| `0x00483C10` | `8B 44 24 0C 53 8B 5C 24 08` | `CellClass::Save` 头 |
| `0x004839F0` | `51 53 55 8B 6C 24 14` | `CellClass::Load` 头 |
| `0x00410320` | `56 8B 74 24 0C 85 F6 57` | 倾倒器 Save 头 |
| `0x005BDF70` | `83 EC 30 53 55 8B E9` | `MapClass::Load` 头 |
| `0x005BE6D0` | `83 EC 20 53 55 56 8B 74 24 30` | `MapClass::Save` 头 |
| `0x005BE715` | `68 6C 55 00 00` | `push 0x556c` MapClass 裸块尺寸 |
| `0x005BE84F` | `8B 2D F4 15 7E 00` | `mov ebp, OleSaveToStream` |
| `0x005657E0` | `8B 44 24 04 8B 89 3C 01 00 00` | 格子入档谓词 |
| `0x00568273` | `89 99 34 01 00 00` | P-2.1 原字节（RevealArea2 清 `+0x134`） |
| `0x006FB365` | `inc` 形式（`FF 00` / `40` 族） | `CreateGap inc +0x134` |
| `0x00410418` | `8B 46 10` | Checksum 只折叠 `+0x10` |
| `0x0083D560` | `98 B8 02 00` | `Savegame_Magic` |

### 7.3 dumps（`out/re_work/re_sprint/R_sav_gap/dumps/`）

- `cell_save_load_disasm.txt` / `cell_save_load_fields.json`
- `parent_save_load_disasm.txt` / `parent_save_load_fields.json`
- `mapclass_save_load_disasm.txt` / `mapclass_save_load_fields.json`
- `disp_0x12C_all.txt` / `disp_0x130_all.txt` / `disp_0x134_all.txt`（全镜像 disp32 xref）
- `cell_sav_path_summary.txt`（入档链指令窗）

---

## 8. 证据等级汇总

| 断言 | 等级 |
|---|---|
| GetSize=0x148、三字段在裸块内、入档 | `[实证]` |
| MapClass::Save 经 OleSaveToStream 逐格、谓词=索引非空 | `[实证]` |
| Load 侧 0x148 恢复 + swizzle 集合 | `[实证]` |
| 版本闸仅 `Internal Version=0x2B898`，无 Cell 版本 | `[实证]` |
| CalculateChecksum / 帧 CRC 不直接覆盖 `+0x134` | `[实证]` |
| 补丁档格式不可区分 / OLE 标记流可区分 | `[推演]` |
| `+0x134` 可由在世 GapGenerator 重建 | `[实证]`（输入）+`[推演]`（算法） |
| 混端 DESYNC 为间接分叉 | `[推演]`（因果链）+ 既有文档 `[实证]`（谓词） |
| 真机读写档对拍 | `[待实测]`（本任务全静态，不宣称真机） |
