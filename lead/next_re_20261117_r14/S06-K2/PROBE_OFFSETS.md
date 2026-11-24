# S06-K2 PROBE_OFFSETS（喂真机卡 W177-D，静态卡，不跑真机）

卡号 **S06-K2**｜目标 `ra2youli\gamemd.exe` SHA-256 `73201CC021497C9567742F718BF1DC78C22E9AE16C7E7365354B65F3FCF67476`｜ImageBase `0x400000`。
所有 `CellClass*` 由 `GetCellAt(0x5657A0)` / 格数组 `[singleton+0x13C]` 取得；取格公式：`idx=(short)Y<<9+(short)X`，`cell=[[0x87F7E8+0x13C]+idx*4]`（stride=4，字节证据 `0x5657C1 mov eax,[ecx+eax*4]`）。

**双支撑定义**：该类自有写点全集（ctor / 链 add/del / 方法）+ 读点（本类方法 + `CellClass*` 全局读），虚调用 `call [reg+disp]` 已剔除（方法集 51 处 / 全扫 4790 处）。仅列双支撑或单边强证据字段。

## A. 适合真机只读轮询的探针字段（双支撑，17 个全部列出）

| CellClass 偏移 | 宽度 | 语义（依据） | 分级 | 适合轮询 | 理由 / 读点(证据地址) |
|---|---|---|---|---|---|
| `+0x24` | word(short) | MapCoords.X；cell 格 X 坐标 | `[已证]` | **Y** | 稳定值非指针；写 `0x47BC02`，读 `0x47FF89`/`0x486845`/`0x47E925` 等 17 处；`EVIDENCE\t1_FINAL.txt` |
| `+0x26` | word(short) | MapCoords.Y；格 Y 坐标 | `[已证]` | **Y** | 同上；读 `0x47FF8D`/`0x486849`/`0x47EA14` 6 处 |
| `+0x38` | dword | IsoTileTypeIndex（地形/瓦片类型 ID，ctor=-1） | `[静态推断]` | **Y** | 小整型稳定值；读 13 处含 `0x4867E0`/`0x48001F`/`0x56A5A2`；注意 K1 已证此偏移非坐标 |
| `+0x44` | dword | OverlayTypeIndex（覆盖物/矿石类型 ID，ctor=-1；`0x485020` 查表键） | `[已证]` | **Y** | 小整型；读 24 处含 `0x485023`/`0x4886E9`/`0x5752F9`；矿石探针的主判据之一 |
| `+0x11B` | byte(signed) | Level（高度 level，movsx 读取） | `[已证]` | **Y** | 单字节小值；读 5 处含 `0x47FFE7`/`0x57538A`/`0x5756AC` |
| `+0x11E` | byte | Powerup/矿石密度（ore value = `[tib+0xB8]×(density+1)`） | `[已证]` | **Y** | 单字节小值；读 9 处含 `0x48503F`/`0x56F35C`/`0x56F6FD`；与 `+0x44` 联用判矿石格 |
| `+0x11A` | byte | Height（cell height；读点常量 8/5/0xC/1） | `[静态推断]` | **Y** | 单字节；读 15 处含 `0x48005C`/`0x56A5C0`/`0x56F400` |
| `+0xE4` | dword(pointer) | **FirstObject**：占格对象链 HEAD A（ground 层） | `[已证]` | **Y（非 NULL 判定）** | 写 `0x47BC82`/`0x47BBA7`/`0x47E91F`/`0x47EACF`，读 `0x47E8B8`/`0x47EAB3` + `0x47C657/683/712/79E/7D9`（can-place 扫描只扫此头）；**②-b 核心探针**：非空=有对象占格 |
| `+0xE8` | dword(pointer) | **AltObject**：桥上对象链 HEAD B（onBridge 层） | `[已证]` | **Y（非 NULL 判定）** | 写 `0x47BC88`/`0x47E90B`/`0x47EAC4`，读 `0x47E8B0`/`0x47EAAB`；选择键 `[obj+0x8C]=OnBridge`（`0x5684B1`/`0x5688E1`）；**②-b 第二探针** |
| `+0x12C` | dword(flags) | CopyFlags（低 5 位=infantry subposition；ctor `AND ~0x1F`） | `[静态推断]` | **Y（位掩码）** | 读 `0x47BC52`；位标志，稳定；`EVIDENCE\t1_FINAL.txt` |
| `+0x140` | dword(flags) | Flags / OccupationFlags（ctor `AND 0xFF800000`） | `[静态推断]` | **Y（位掩码）** | 读 32 处含 `0x486890`/`0x5683DF`/`0x56F353`；占格/可见性位，真机按位判读 |
| `+0x100` | dword | OccupyHeightsCoveringMe（占格高度覆盖计数） | `[静态推断]` | **Y（计数）** | 读 3 处含 `0x5687C2`/`0x568A91`；小整数计数 |

### 双支撑但**不建议**直接轮询（pointer / 语义弱）

| 偏移 | 宽度 | 语义 | 分级 | 不建议理由 |
|---|---|---|---|---|
| `+0x28` | dword(ptr) | FoggedObjects 指针（ctor=0） | `[静态推断]` | 堆指针，随局变化，轮询值无稳定语义；写 `0x47BC05`，读 `0x47BB66` |
| `+0x2C` | dword(ptr) | BridgeOwnerCell（ctor=0） | `[静态推断]` | 指针；读 `0x57027D`/`0x573763`（GetCellAt 窗口） |
| `+0x34` | dword(ptr) | LightConvert（ctor=0） | `[静态推断]` | 指针；读 `0x47BBC7` |
| `+0xFC` | dword(ptr) | unknown_FC（dtor virtual-delete 指针 `0x47BB91`） | `[静态推断]` | 生命周期指针，轮询无意义 |
| `+0x13C` | dword | unknown_13C（CellClass 自有；**不是** MapClass+0x13C） | `[静态推断]` | 语义未定；读 `0x568483`/`0x5688B3`。⚠️ 与 T3 的 MapClass+0x13C(`0x87F924`) 同名异类，勿混 |

> ⚠️ **别名警告**：`+0x13C` 在本表是 **CellClass** 字段（`CellClass*` 基址）；R14 §961 / T3 的 `0x87F924` 是 **MapClass+0x13C**（格数组基址指针字段）。两者偏移相同但对象类型不同，取址表达式不同，不得互换。

## B. `[未证]` 字段（46 个，不建议作探针判断依据）

以下 46 个偏移只有 ctor 初始化写点、无本类读点（或仅 `lea`/虚调用伪读已剔除），**不建议作探针**：
`+0x3C +0x40 +0x48 +0x4C +0x50 +0x54 +0x58 +0x5C +0x60 +0x64 +0x68 +0x6C +0x70 +0x74 +0x78 +0x7C +0xAC +0xDC +0xE0 +0xEC +0xF0 +0xF4 +0xF8 +0x104 +0x108 +0x10A +0x10C +0x10E +0x110 +0x112 +0x114 +0x116 +0x118 +0x119 +0x11C +0x11D +0x11F +0x120 +0x121 +0x122 +0x124 +0x128 +0x130 +0x134 +0x138`
（`+0x7C`/`+0xAC` 是 `rep stosd` 清零区 12 dword，非单值字段；`+0x30` 见下注。）

> **注 `+0x30`**：本类 ctor 写 0、linkdel 写，`CellClass+0x30` 无本类读点（audit 已列此异常）。任务所称「元素 +0x30 = next」指的是 **ObjectClass::NextObject**（链表元素/对象上的字段，`ObjectClass+0x30`），不是 `CellClass+0x30`。真机若要遍历占格链，应读链头指向的**对象**的 `+0x30`，而非 cell 的 `+0x30`。

## C. 给 W177-D 的最小探针组（②-b 重叠判定）

```
cell = [[0x87F7E8 + 0x13C] + idx*4]      ; idx=(Y<<9)+X
headA = dword[cell + 0xE4]               ; FirstObject  占格对象链（ground）
headB = dword[cell + 0xE8]               ; AltObject    桥上对象链
coords = { word[cell+0x24], word[cell+0x26] }   ; 应与 idx 反解一致
flags  = dword[cell + 0x140]             ; 占格/可见性位
ore    = { dword[cell+0x44], byte[cell+0x11E] } ; 矿石判据
```
判「重叠」：同一 idx 上 `headA`（及 `headB`）链沿对象的 `+0x30` 遍历，统计非空节点数 >1 即为多对象占格。此即 ②-b 要构造/观测的目标。

证据文件：`EVIDENCE\t1_FINAL.txt`（字段表）、`t1_field_table.txt`（写点全集/读点）、`t1_reads_complete.txt`（读点无截断）、`t4_lists.txt`（两链 W/R）、`t4_wrappers.txt`（onBridge 选择）、`map_getcellat.txt`（stride）。
