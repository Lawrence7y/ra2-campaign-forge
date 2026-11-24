# S06-K3 LAYOUT（CellClass 字段 + MapClass + 矿石子系统）

## T0 访问形式与剔除口径（纪律 E）
- 两种访问形式全查：①绝对寻址 `[0x87F924]`/`[0x886FA0]` 等；②立即数载入基址 `mov reg,[0x87F924]`→`[reg+idx*4]`→`[cell+off]`。
- `call/jmp [reg+disp]` = 虚槽调用，不计数据字段读点。剔除数：方法集内 **43**、全 .text `call/jmp [reg+disp]` **18,949**（审计 18,946，差 3→D2）。
- provenance 四源：S1 GetCellAt 返回 eax(1326)、S2 cell 数组元素(367+444)、S3 INVALIDCELL 单例 0xABDC50(384)、S4 CellClass 方法 this=ecx。

## T1 CellClass 字段双支撑表（63 字段）
`W`=写点数、`R`=CellClass provenance 读点数。`★`=本卡新增双支撑。级：`已证`=字节级读写指令；`静态推断`=语义靠上下文；`未证`=仅 ctor 写/无读。

| off | W | R | 双支撑 | 语义 | 级 |
|---|---|---|---|---|---|
| +0x24 | 1 | 28 | ✓ | MapCoords.X (short) | 已证 |
| +0x26 | 0 | 6 | ✓(审) | MapCoords.Y (short, dword@+0x24 覆盖) | 已证 |
| +0x28 | 2 | 1 | ✓(审) | FoggedObjects 指针 | 静态推断 |
| +0x2C | 1 | 6 | ✓(审) | ctor=0，格邻接读 | 静态推断 |
| +0x30 | 2 | 0 | — | 格对象链表元素 next | 已证(结构) |
| +0x34 | 2 | 1 | ✓(审) | ctor=0，dtor 读 | 静态推断 |
| +0x38 | 1 | 32 | ✓ | TerrainType/LandType (ctor=-1) | 已证 |
| +0x3C | 2 | 7 | ★✓ | 内嵌子对象指针：ctor=0，读后 test 非空才 call 0x6E53A0 | 静态推断 |
| +0x40 | 1 | 0 | — | ctor=0 | 未证 |
| +0x44 | 11 | 25 | ✓ | Overlay/Tiberium 类型 ID (ctor=-1)，0x485020 读 | 已证 |
| +0x48 | 1 | 0 | — | ctor=-1 | 未证 |
| +0x4C | 1 | 1 | — | ctor=0，通行判定读 | 静态推断 |
| +0x50 | 1 | 1 | — | ctor=-1 | 未证 |
| +0x54..0x64 | 1 | 0 | — | ctor=-1/0 初始化 | 未证 |
| +0x68..0x74 | 0 | 0 | — | 4-dword 块 (rep stosd 区各计1) | 静态推断 |
| +0x78 | 1 | 0 | — | ctor=0 | 未证 |
| +0x7C/+0xAC | 0 | 0 | — | 12-dword 零填充区起点 | 静态推断 |
| +0xDC | 1 | 1 | — | ctor=0，通行判定读 | 静态推断 |
| +0xE0 | 1 | 0 | — | ctor=0 | 未证 |
| +0xE4 | 5 | 4 | ✓ | FirstObject 占格链头 A（ground） | 已证 |
| +0xE8 | 3 | 2 | ✓(审) | AltObject 桥上链头 B（门控 cell+0x140 bit0x100=cf_Bridge） | 已证 |
| +0xEC..0xF8 | 1 | 0/2 | — | ctor=0；+0xEC 有 2 读(cmp,2) | 未证 |
| +0xFC | 3 | 1 | ✓(审) | dtor 中 virtual-delete 指针 | 静态推断 |
| +0x100 | 6 | 3 | ✓(审) | attach/detach wrapper 读 | 静态推断 |
| +0x104 | 1 | 0 | — | ctor=0x10000 | 静态推断 |
| +0x108 | 1 | 0 | — | word, ctor=0；带内读 0 | 未证 |
| +0x10A..0x116 | 1 | 0 | — | word 初始化 (0x3e8/0xffff) | 静态推断 |
| +0x118 | 1 | 0 | — | byte, ctor=0xff | 静态推断 |
| +0x119 | 1 | 0 | — | byte, ctor=0 | 未证 |
| +0x11A | 1 | 52 | ✓(审) | 格通行标志（常量 8/5/0xc/1） | 静态推断 |
| +0x11B | 32 | 53 | ✓ | Height level (byte signed, movsx 于寻路) | 已证 |
| +0x11C | 2 | 4 | ★✓ | 格状态 byte：与 +0x11B 相邻读取，参与 can-place/移动判定 | 静态推断 |
| +0x11D..0x11F | 1 | 0 | — | byte ctor=0 | 未证 |
| +0x11E | 36 | 17 | ✓ | Tiberium 密度 (byte)，ore=(密度+1)×单位价值 | 已证 |
| +0x120/+0x121 | 1 | 0 | — | byte ctor=0xfe | 静态推断 |
| +0x122 | 1 | 1 | — | byte, 寻路读 | 静态推断 |
| +0x124/+0x128 | 1 | 0 | — | byte ctor=0 | 未证 |
| +0x12C | 5 | 4 | ✓ | 状态 flags dword（ctor AND ~0x1f；bit3=shroud） | 静态推断 |
| +0x130 | 3 | 1 | — | dword ctor=1，attach 读 | 静态推断 |
| +0x134/+0x138 | 1-2 | 0 | — | ctor=0 | 未证 |
| +0x13C | 1 | 3 | ✓ | dword，attach/detach 读 | 静态推断 |
| +0x140 | 1 | 60 | ✓ | 位标志 dword（ctor AND 0xff800000）；bit0x100=cf_Bridge | 已证 |

**双支撑合计 19/63**：审计 17（+24/26/28/2C/34/38/44/E4/E8/FC/100/11A/11B/11E/12C/13C/140）+ 本卡新增 +0x3C、+0x11C。其余 44 字段无 CellClass 自己的读点（多数仅 ctor 写），不构成双支撑，不凑数。

## T3 MapClass（30 槽，只引用不重开 179 槽之争）
- RTTI：vtable `0x7ED404`→COL `0x8054C8`→TD `0x816BC0`→名 `.?AVMapClass@@`；30 槽，槽后 `0x7ED47C`=COL(0x8055E0)。
- 逐槽函数见 `EVIDENCE/k3_t3_mapslots.txt`。槽 18–21 = 共享桩 `0x4C9150`(`AbstractClass`, 3B)。槽 3/6/9/11/12/13/15/17/22/23/24 属 MouseClass；槽 28/29 属 DisplayClass——反映 MapClass 的多继承链（Map→Display→GScreen→Mouse）。
- `+0x13C`/`0x87F924`：格数组基址指针字段，全镜像 0 绝对写/399 绝对读；写走 `[MapClass+0x13C]` 间接。stride=4 (`0x5657C1 8B 04 81`)，idx=(Y<<9)+X∈[0,0x40000)。
- 滚动原点全镜像写各 2 处（§4.4 一致），0x4A8960 函数是相机视口设置路径。

## T4 矿石/覆盖物子系统（经济价值）
- 表：`DynamicVectorClass<TiberiumClass*>`，vt `0x7F56BC`→名 `.?AV?$DynamicVectorClass@PAVTiberiumClass@@@@`（RTTI 实测，fail-closed 通过）；静态初始化 `0x721640`（Items=0, Count=0, Growth=10, vt 写入）；元素数 = 规则矿石类型数（个位数，运行时定）。
- 单位价值：`+0xB8` 从 INI `[Resource]Type` 的 `Value=` 键读（`0x721A50` 内 `0x721B0C`，`CCINIClass::ReadInteger`=0x5276D0 [已证]）；`Power=`→+0xBC。atlas strings 列证字段集 = Spread|Growth|Value|Power|Color|Debris|Image。
- 每格价值：`0x485020` = `[type+0xB8] × (cell+0x11E 密度 + 1)`；overlay/矿类型 ID 来自 cell+0x44。
- 调用点全集：20 处直接 E8，7 调用者函数（见 PROGRESS）。调用者以 `AnimClass::vslot23`/`AircraftClass::slot206`/`BuildingClass::slot206` 等对象更新路径为主；`0x6D7840` 邻近绘制遍历层。
- **链**：地图加载/规则 INI → `0x721A50` 读 Value→+0xB8 → 对象 Update/绘制每格调 GetCellAt→`0x485020` → 返回价值。⚠️ "每格每帧"来自 EIP 21.6% 归因（§923 已入账），本卡静态只确证调用点集合，[静态推断] 未跑真机。
