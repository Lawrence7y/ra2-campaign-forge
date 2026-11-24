# S08-K1 · 迷雾/阴影视图与雷达小地图布局

> 卡号 S08-K1｜目标 `ra2youli\gamemd.exe`（SHA-256 `73201CC0…F67476`，ImageBase `0x400000`，只读）。
> 证据本卡自取：`EVIDENCE/E01..E13` 未截断；`work/` 可复跑（Python 3.12.10 + capstone 5.0.7 `skipdata=True` + pefile）。
> 分级：`[已证]`=字节+读写/调用双支撑；`[静态推断]`=字节实证但语义靠上下文；`[未证]`=仅单点证据。
> 双通道：A=`function_atlas.tsv` 的 `entry+size`（区间包含归属）；B=全 `.text` 线性反汇编（`skipdata=True`，1,394,120 指令/66 skip 字节）取 `call/jmp rel32` 目标。两通道不同源，逐项对账见 E13。

## 1. 迷雾/阴影数据结构（结论：**不是独立位图，是每格 CellClass 字段**）

### 1.1 格容器（=已入账事实，本卡复核一致）
| 项 | 值 | 证据 |
|---|---|---|
| `MapClass` 单例 | `0x87F7E8` | E01 `0x586360`/`0x487950` 调用点 `mov ecx,0x87F7E8`；E13 |
| 格指针数组基址 | **`0x87F924`**（=单例 `+0x13C`） | `0x5863D3 mov edx,[0x87F924]` / `0x5863D9 mov eax,[edx+eax*4]`（E01） |
| stride | **4**（`CellClass*`，不是 1 bit / 1 byte） | `mov eax,[edx+eax*4]`（E01/E13） |
| 尺寸 | **512×512 = `0x40000` 格** | `idx=(Y<<9)+X`（`shl eax,9; add eax,ecx`），边界 `cmp eax,0x40000 / jge`（E01，两处同构分支 `0x5863C5`/`0x586505`） |
| 数组内存范围 | `0x87F924 .. 0x97F924`（`0x40000×4 = 0x100000` B = 1 MB，BSS 运行时初始化，磁盘无初值） | 复算：`0x40000×4=0x100000`（E13 V1） |

**关键判定**：`MapClass::IsLocationShrouded 0x586360` 把 CoordStruct→格坐标→`idx=(Y<<9)+X`→`[0x87F924+idx*4]` 取 `CellClass*`，再 `test byte [cell+0x12C],8`（E01）。**全程没有任何「1 bit/格」或「1 byte/格」的独立迷雾位图**——谓词直接落在格对象字段上。⇒ 回答「位图还是字节数组」：**都不是**；是**每格对象字段**，经由 stride-4 指针数组索引。

### 1.2 每格迷雾字段（CellClass，GetSize `0x148`，63 字段）
| 偏移 | 宽 | 名/语义 | 写点 | 读点 | 级 |
|---|---|---|---|---|---|
| `+0x120` | 1(byte) | **Shroudedness**：`-2(0xFE)`=完全遮蔽/黑幕；`-1(0xFF)`=可见；`0..48`=灰度过渡帧 | `0x480207`(Draw)、`0x4A990F`/`0x4A9A98`(Reveal)、`0x47BD28` | `0x47F226`(黑幕层)、DLL 钩 `cmp [esi+0x120],0xFE`（线索一致） | 已证 |
| `+0x121` | 1(byte) | **Foggedness**（疑同上编码，灰雾档） | `0x480243`、`0x4A9947`/`0x4A9BD5`、`0x47BD2E` | 灰雾层映射（E03/E01） | 静态推断 |
| `+0x12C` | 4(dword, 位域) | **CopyFlags**：`bit3=0x08 cf_Explored`（已探索）；`bit4=0x10 cf_Mapped` | `0x4A98EC or al,8`、`0x4A9924 or al,0x10`、`0x4A9A28` | `0x5863F2 test [ecx+0x12C],8`（黑幕谓词，E01） | 已证 |
| `+0x130` | 4 | ShroudCounter（揭示/重遮计数） | `0x5678E0` RevealArea2 族、`0x577D90` | 重遮钳位 `0x487690`（E03 + 线索） | 静态推断 |
| `+0x134` | 4 | GapsCoveringThisCell（裂缝覆盖计数） | CreateGap/DestroyGap；RevealArea 写 0（`0x568273` 线索） | `0x487690` ReshroudCell | 静态推断 |
| `+0x13C` | 4 | 灰雾谓词计数：`>0` ⇒ 判「灰雾」 | 散见（E03：40 函数 52 写） | `0x58652E/0x5865B9 mov ecx,[eax+0x13C]; test; jle`（**IsLocationFogged 唯一读判据**，E01） | 已证（读判据） |
| `+0x140` | 4(dword, 位域) | Flags/RedrawFlags：`flags&3==0 ⇒ Shroudedness=-2`；bit0=需重绘 | `0x4A98E0`、`0x4A995E` | `0x6D8724 mov eax,[eax+0x140]; test al,3`（E02/E01） | 已证 |

### 1.3 Shroud 与 Fog 是几个数组？（**核心数字**）
**结论：0 个独立迷雾数组；1 个 `CellClass*` 格数组 + 每格 2 个独立字节字段（`+0x120` Shroudedness / `+0x121` Foggedness）+ `+0x12C` 两个 CopyFlags 位 + `+0x13C` 灰雾计数。**
- 证据（双通道）：读点 `0x5863F2 test [ecx+0x12C],8`（黑幕，43 调用者）、`0x58652E mov ecx,[eax+0x13C]; test ecx,ecx; jle`（灰雾，1 调用者）——两条谓词读**不同字段**（E01）。
- 写点：`0x4A98EC or [ebp+0x12C],8`（揭示写探索位）与 `0x4A990F mov [ebp+0x120],al` / `0x4A9947 mov [ebp+0x121],al`（分别写黑幕档/灰雾档）（E01）。
- ⇒ 不是「同一数组的两个 bit」，也不是「两个独立数组」；是**每格对象里两个分开的字节 + 分开的位/计数**。

### 1.4 每 House 一份？（**核心数字**）
**全局一份，非 per-House。** 路径唯一：`ecx=0x87F7E8`（MapClass 单例）→ `[0x87F924 + idx*4]` → `CellClass*` → `+0x120/+0x121/+0x12C/+0x13C`。
- 双证据：① `0x487950`（CellClass::IsShrouded，`this=CellClass*` 读 `[ecx+0x24]` 自身 MapCoords）内部 `mov ecx,0x87F7E8` 转调 `0x586360`（E02）；② `0x4A9890`（揭示路径，`this=ebx=MapClass 单例`，`call 0x5657A0` GetCellAt）写同组字段（E01）。
- 反证：全 `.text` 无任何「以 HouseClass 为基址取迷雾数组」的 `mov reg,[house+off]` 模式能给出格数组——格数组基址是硬编码立即数 `0x87F924`（E01 两处谓词 + E13）。
- `House+0x577A` 只是 SpySat 开/关标志（线索），**不是**迷雾数组句柄。

## 2. 更新触发器与每帧入口

### 2.1 状态迁移
| 迁移 | 触发 | 函数（本卡取证） |
|---|---|---|
| 黑→灰 | 单位/建筑视野揭示：`or [cell+0x12C],8`、`0x6D8700` 算 Shroudedness 写 `+0x120` | 揭示族 `0x4A9890`(1 调用者 `0x65381A`)、`0x5678E0 RevealArea2`(**22 调用者**：`0x43F4A8`/`0x4A…`/建筑放置/AI 等)、`0x577D90 RevealArea3`(2) |
| 灰→亮 | 当前直视：`Flags(+0x140)` 变化 → `0x6D8700` 返回 `-1/可见` → `+0x120=0xFF`；`+0x12C bit4` 置位 | 同上 + `0x6D8700`(**19 调用者**，含 `0x480202`/`0x48023E` Draw) |
| 亮→灰/黑 | 单位离开/摧毁、SpySat 掉电重遮：`ReshroudCell 0x487690`(2 调用者)、`0x577AB0`(线索) | `House::UpdateSpySat 0x508F60`(**1 调用者** `0x4F850C`) |
| 超武 | PsychicReveal case 11 (`0x6CD70C`)→2×`0x5678E0`；SpySat 全图 | E08 调用者表含 `0x6CD773`/`0x6CD79C` |

### 2.2 每帧入口（**核心数字：入口 `0x508F60`，调用者数 1**）
- **主逻辑帧链**：`0x55DE81 CurrentFrame+1` → `0x55DE9A call 0x55E160`（每逻辑帧，S16-K1 已证链）→ `0x55E261 mov ecx,[0x887324]` / `0x55E267 mov eax,[ecx]` / **`0x55E269 call [eax+0x5C]`**（House 虚槽 23 = `0x4F8440 HouseClass::Update`，atlas 洞）→ `0x4F850C mov ecx,esi; call 0x508F60`（E08/E09/E13 V4）。
- **每帧迷雾状态更新入口 = `HouseClass::UpdateSpySat 0x508F60`**（atlas `+0 sz=313`）：
  - 调用者数 **1**（通道 B 全扫 `0x4F850C`；通道 A atlas `n_callers=1`；E01/E13 V3）。
  - 遍历：每 House 每逻辑帧查 `+0x577A`/`+0x16A5`；切换时 `0x577D90`(全图 RevealArea3) 或 `0x577AB0`(全图 Reshroud) 遍历全部 `0x40000` 格写 `+0x12C|=0x18` / `+0x130=0` / `+0x134=0`（线索与 E03 写点一致）。
- **非每帧的渲染侧重算**：`CellClass::Draw 0x4801F0`（2 调用者 `0x6D3716`/`0x6D751A`，E06/E13）内 `0x480202 call 0x6D8700(which=0)` → `0x480207 mov [esi+0x120],al`；这是按可见格调用（战术逐格循环），**不能当「每帧更新入口」的调用计数证据**——规律每帧的是 House 链，不是它。
- 纪律 10：以上「每帧」结论来自**调用链结构 + `UpdateSpySat` 调用者数=1**（双通道一致），**未用** EIP 权重。

## 3. 可见性判定函数（`this` 归属）
| 函数 | 语义 | `this` | 调用者数 | 证据 |
|---|---|---|---|---|
| `0x586360` | `MapClass::IsLocationShrouded`：Coord→格→`[+0x12C]&8==0` ⇒ 返回 1（未探索/黑） | **MapClass 单例**（调用点 `mov ecx,0x87F7E8`；内部直用全局 `0x87F924`，不读 ecx） | **43**（A/B 一致） | E01/E13 |
| `0x5864A0` | `MapClass::IsLocationFogged`：`[cell+0x13C]>0` ⇒ 返回 1（灰雾） | 同上（内部 `0x87F924`） | **1**（`0x655D74` = 雷达 DrawCell） | E01/E13 |
| `0x487950` | `CellClass::IsShrouded`：`this=CellClass*`，读自身 `+0x24` MapCoords→转 Coord→转调 `0x586360` | **CellClass**（非 House） | **9** | E02/E13 |
| `0x5865E0` | `IsCellShrouded` **恒假 stub**：`xor al,al; ret 4`（5 字节） | 忽略 | **25**（线索记 25，通道 B=25；atlas `n_callers=24`，差 1 见 DISAGREE） | E01/E13 |
| `0x586540` | 不是独立函数：`0x5864A0+0xA0` 内部分支标签（0 调用者） | — | 0 | E01 |

**没有 `IsCellVisible` 命名的独立函数**：可见性=上述谓词取反 + `+0x140` flags；`0x5865E0` 是对象绘制簇里唯一「迷雾门」但恒假 ⇒ 战术对象绘制**不**因灰雾被剔除（E01 + 线索一致）。

## 4. 雷达小地图

### 4.1 缓冲地址与格式
| 项 | 值 | 证据 |
|---|---|---|
| 宿主对象 | `RadarClass` 基类嵌入 `SidebarClass`（ctor `0x652960` ← `0x63F6B0` ← Sidebar ctor `0x6A4E60` ← `0x6CFE20`）；字段偏移即相对该对象 `this` | E10/E11/E12 |
| 目标 Surface* | **`this+0x121C`**（`Surface::SetPixel` 走 `vtable+0x24`；全图重建取宽高走 `vtable+0x80`，`0x657D52`） | E04/E05 |
| 干净地形背景 Surface* | **`this+0x1220`**（脏矩形 Blit 来源，`0x657353` 附近 `call [eax+8]`) | E04/E05 + 线索 |
| 地形色缓存 | **`this+0x123C`**；缓冲宽 `+0x1240`、高 `+0x1244`；脏矩形 `+0x1248..0x1254` | E04/E05 |
| 脏点向量 | Items `+0x1260`、Count `+0x126C`（vector vtable `0x7EEB54`）；脏格列表 Items `+0x1228`、Count `+0x1234` | E04/E05 |
| 雷达缩放/原点 | `+0x1488` float 比例；`+0x148C=1`；`+0x1490/1494/14A0` 原点 | E10 + 线索 |
| 色深/每格像素 | 8-bit 调色板索引 Surface（**1 byte/pixel**）；`SetPixel` 写单字节；每地图格→1 雷达像素（缩放比 `+0x1488` 由 `RadarSizeFactor` 决定），色来自 House RGB 打包 | E04/E05 + 线索 |

### 4.2 重绘触发（**核心数字：不是每帧全量重绘**）
`RadarClass::DrawMap 0x656EC0`（1 调用者 `0x653374`）入口五道脏门（E05 原文）：
1. `0x65715C mov al,[esi+0x14d9]; test al,al; jne dirty`（强制标志）
2. `0x657166..0x657198`：视口矩形 4 dword（`+0x14EC/14F0/14F4/14F8`）与入参比较，任一不同→dirty
3. `0x65719A call 0x660530; test al,al; je early`（雷达事件未更新）
4. `0x6571A3 mov eax,[esi+0x126C]; test; jg dirty`（脏点计数）
5. `0x6571AD mov eax,[esi+0x1234]; test; jg dirty` + `0x6571BC call 0x431800`（屏幕脏区）
五者全无 → **`0x6571C3 je 0x657872` 直接返回**，跳过整幅小地图。
- 增量路径：脏矩形逐像素循环 `0x65749E..0x6574F1` 内 `0x6574C3 call 0x655C50`；脏点向量倒序循环 `0x657514..0x657526` 内 `0x657520 call 0x655C50`（E05）。
- 全量路径：`0x657CE0`（10 调用者：`0x577B91`/`0x577C76`/`0x577D79`/`0x577F0D`/`0x578069`/`0x67E6BD`/`0x687C84`/`0x6E2257`/`0x6FB44B`/`0x6FB728`，多为 SpySat/重遮/载入），遍历 Surface 全宽全高 `0x657D68..0x657D7F` 内 `0x657D77 call 0x655C50`（E05/E13）。
- ⇒ **正常帧走脏区/脏点增量，非每帧全量**；全量仅状态切换/载入时触发。

### 4.3 单位点绘制来源
`RadarClass::DrawCell 0x655C50`（3 调用者，见上）：反算格坐标→`0x586360 IsShrouded`(`0x655D4F`)/`0x5864A0 IsFogged`(`0x655D74`)→**RTactical 空间哈希**（`this+0x1258`，256 桶×`0x18`，桶内 16B 条目 `{Techno*, cellX, cellY, ?}`，hash `(X−Y*5)&0xFF`）逐对象可见性过滤（`0x50B6F0`）→House RGB 打包→`[this+0x121C]→vtable+0x24 Surface::SetPixel`（E04 + 线索）。未命中对象时：fogged⇒背景 `GetPixel` 后 `shr 1`；shrouded⇒写 0（黑）；clear⇒原样写回（线索 §9.1，与本卡 `+0x121C/+0x1220` 通道一致）。
- 与线索差异（DISAGREE）：线索称 `0x655D38 call 0x578080` 是 `MapClass::GetCell`，后勘误为 `GetCellFloorHeight` —— 本卡未复核该支，采用线索勘误口径 `[待复核]`。

## 5. 与渲染的层级关系（只给层级与调用点）
- **黑幕/灰雾是「绘制后叠加」**：`0x47EFE0`（黑幕层，唯一调用者 **`0x480230`**，E13 V3）在 `CellClass::Draw 0x4801F0` 内被 `mov ecx,esi / call`（`0x48022E/0x480230`）调用，位于 `0x480251 test dh,0x10` 第二道 FogOfWar 位门**之前**——即地形已画完后，用 SHROUD.SHP/FOG.SHP 逐格覆盖（线索 §2.1 + E01/E13）。
- **对象侧是「绘制前过滤」但引擎门恒假**：对象绘制簇 `0x6D8DB0` 唯一迷雾门 `0x6D8FDA call 0x5865E0`（stub 恒 0）⇒ 不过滤；建筑/步兵 Draw 内 `call 0x487950` 把亮度/掩码归零（非硬跳过，线索）。
- 层级：**地形 blit → CellClass::Draw 内黑幕覆盖（叠加层）→ LayerClass 对象绘制（v[65] 剔除/裁剪，迷雾门已 stub）→ 小地图独立脏区路径**。不深入 S07。

---
*行数 ≤200｜EVIDENCE/E01..E13 未截断｜复跑：见 PROGRESS.md*
