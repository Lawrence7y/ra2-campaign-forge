# R-05 专章：class 4 UAF 写者路径收敛

> [META]
> 任务=R-05 / SBH class-4 UAF writer · 执行=R 轨逆向取证代理 · 日期=2026-09-30
> 目标二进制：`ra2youli/gamemd.exe`（MD5 `4f37486e5b0dbe2ae5f45aeee0f98367`，ImageBase `0x00400000`）
> 写作用域：本文件 + `out/re_work/re_sprint/sbh_uaf/**`；二进制只读
> 上游：`docs/re/except_zc11_forensics.md`（`0x007CFC9F`，`EDX=FE00FFFF`，`EDI=4`）
> 上游：`docs/re/sbh_freelist_deep_dive.md`（R-02：size-class / heap_info / 毒值六候选）
> 证据分级：`[实证]` 字节+反汇编可复算 · `[推演]` 由代码逻辑推断 · `[待实测]` 需运行时

---

## [0] 结论速览（≤12 行）

1. **[实证]** `CRT::_new 0x7C8E17` 共 2832 处调用；其中 **31 处** push 立即数落在 0x39..0x48 → class 4（req 57..72B）。
2. **[实证]** class 4 尺寸分布：`0x3C×11 / 0x40×14 / 0x44×3 / 0x48×3`。
3. **[实证]** vtable 映射命中类型：TriggerClass/TagClass(0x48)、WaypointPathClass/AlphaShapeClass/DiskLaserClass(0x40)、PixelFXClass/Walk/TunnelLoco(0x3C)、BitFont/INI 节点(0x44)、MSAnim 族、GraphicMenuImageItem、Multiplayer* 模式类。
4. **[实证]** 另有 2 类**无 vtable** class 4：`0x408B7B` 链表+位表容器(0x3C)、`0x65FB80` 平面 FX 对象(0x40，+0 写入 type-id）。
5. **[实证]** `FE00FFFF` 作为 imm32 在 `.text` **0 命中**；`mov word,0xFE00` 立即数 **0 命中**；成对 int16 存储（-1 紧接 -512）**0 命中** → 毒值是**计算/拷贝产物**，非代码常量。
6. **[实证]** `-512` 以 `push 0xFFFFFE00` 出现于 `0x4163CF/0x4163D4/0x416437/0x41649F`，传入 **CoordStruct 构造** `0x41C230`（X/Y/Z int32）。
7. **[实证]** `CellStruct = Vector2D<short>`（2×int16）；`WaypointClass = { CellStruct Coords; DWORD unknown; }`，**Coords 在偏移 0**。
8. **[实证]** `DynamicVectorClass<WaypointClass>` 按值存 8B 元素；buffer = `cap×8` → **cap=8/9 时 64/72B = class 4**。
9. **[实证]** `FE00FFFF` 低字节 `0xFF` → **非 4 字节对齐**，不能是指针写；只可能是业务数据（int16 对 / RGB565 / 标量）。
10. **[推演] 主候选**：Waypoint 路径 `DynamicVectorClass` 扩容释放 class-4 buffer 后，过期 `WaypointClass*` 写 `Coords={-1,-512}` 到 buffer 起点（user+0 = free 节点 `next`）。
11. **[推演] 次候选**：RGB565 双像素（白 `0xFFFF` / 纯红 `0xFE00`）经悬垂绘制指针写入 class-4 块起点；`.text` 有 53 处 `shl reg,11` 打包点。
12. **[待实测]** 写者归因需 R-02 H1/H2/H6 钩子 + free 后影子内存；本轮仅静态收敛。

---

## [1] class 4 分配点清单

扫描器：`out/re_work/re_sprint/sbh_uaf/scan_c4_alloc.py`（可复算）。
匹配模式：`.text` 内 `push imm(0x39..0x48)` / `mov reg,imm; push reg` 后 28B 内 `call 0x7C8E17`。

| # | alloc VA | fileoff | size | 构造函数 / vtable | 类型 | 备注 |
|---|---|---|---|---|---|---|
| 1 | `0x408B7B` | `0x8B7B` | 0x3C | `0x4072D0` 列表头 init | **无 vtable** 列表+位表容器 | `rep stosd` 清零后自链；+0x10 挂独立 buffer |
| 2 | `0x4354D2` | `0x354D2` | 0x44 | `0x433880` → `0x7E3A78` | **BitFont** | `+0x24/0x26` 存 int16（0x7FFF/0x3555） |
| 3 | `0x4F1ED7` | `0xF1ED7` | 0x3C | `0x5CC760` → `0x7EE8E8` | **MSAnim** | UI/影片动画 |
| 4 | `0x4F1F12` | `0xF1F12` | 0x3C | `0x7B5400`（字符串辅助，非 ctor） | （二次分配） | 同函数内嵌套 new |
| 5 | `0x4F2FC0` | `0xF2FC0` | 0x40 | `0x5CB6D0` → `0x7EE910` | **MSShapeAnim** | |
| 6 | `0x4F352F` | `0xF352F` | 0x3C | `0x5CE640` → `0x7EEA2C` | **MSPCXAnim** | |
| 7 | `0x4F35B9` | `0xF35B9` | 0x3C | `0x5CE640` + `0x7EA674` | **GraphicMenuImageItem** | 菜单图元 |
| 8 | `0x5021A7` | `0x1021A7` | 0x40 | `0x763810` → `0x7F6E70` | **WaypointPathClass** | 内嵌 `DynamicVectorClass<WaypointClass>` |
| 9 | `0x525DEC` | `0x125DEC` | 0x44 | `0x7D5408` + `0x7EB74C/0x7EB744` | **Node\<INISection\*> / List\<INIEntry\*>** | INI 装载期 |
| 10 | `0x5286E5` | `0x1286E5` | 0x44 | `0x7D5408` + `0x7EB74C/0x7EB73C` | **INISection** | 同上 |
| 11-15 | `0x5D8172/0x5D81B2/0x5D81F2/0x5D8232/0x5D8272` | | 0x40 | `0x5C0DD0/0x5C6150/0x5CA630/0x5CB3A0/0x5C5CE0` | **MultiplayerBattle / MultiplayerManBattle / MultiplayerSiege / UnholyAlliance / FreeForAll** | 一局一次，低 churn |
| 16-17 | `0x65FB2A/0x6608F5` | | 0x40 | `0x65FB80`（无 vtable） | **平面 FX/视差对象** | +0=type-id；+0x10=float π/4 `0x3F490FDB` |
| 18 | `0x6C05BE` | `0x2C05BE` | 0x40 | `0x763730` → `0x7F6E70` | **WaypointPathClass** | 第二入口 |
| 19 | `0x6C0EBE` | `0x2C0EBE` | 0x40 | `0x4A7A30` → `0x7E5FB8` | **DiskLaserClass** | 武器特效 |
| 20 | `0x6C1ABE` | `0x2C1ABE` | 0x48 | `0x725FA0` → `0x7F5858` | **TriggerClass** | 失败返回 `0x8007000E` |
| 21 | `0x6C463E` | `0x2C463E` | 0x3C | `0x728A00` → `0x7F5A24` | **TunnelLocomotionClass** | |
| 22 | `0x6C47BE` | `0x2C47BE` | 0x3C | `0x75AA90` → `0x7F69F8` | **WalkLocomotionClass** | |
| 23 | `0x6C613E` | `0x2C613E` | 0x40 | `0x420AF0` → `0x7E32A4` | **AlphaShapeClass** | ctor 签名 `(Object*, nX, nY)` |
| 24 | `0x6D7AAF` | `0x2D7AAF` | 0x3C | `0x631E30` → `0x7EFDA4` | **PixelFXClass** | 像素特效 |
| 25 | `0x6E4F29` | `0x2E4F29` | 0x48 | `0x725FA0` + `0x7F44E0` | **TriggerClass（链入 Tag）** | 循环走 `+0xA0/+0xA8`，`[+0x28]` 串链 |
| 26 | `0x6FE470` | `0x2FE470` | 0x40 | `0x4A7A30` | **DiskLaserClass** | 第二入口 |
| 27 | `0x72665E` | `0x32665E` | 0x48 | `0x725FA0` | **TriggerClass** | |
| 28-30 | `0x768686/0x768869/0x7688FE` | | 0x3C | `0x5CC760/0x5CE640` | **MSAnim / MSPCXAnim** | |
| 31 | `0x76912B` | `0x32912B` | 0x40 | `0x5CB6D0` | **MSShapeAnim** | |

> [实证] 删除侧：`call CRT::_delete 0x7C8B3D` 共 4499 处；class-4 各分配点 0x300 窗口内 delete 密度见 `poison_and_lifetime.txt`（WaypointPath / AlphaShape / WalkLoco 窗口内 delete≥4，churn 较高）。

---

## [2] 毒值 `FE00FFFF` 业务语义反查

### 2.1 立即数 / 常量命中表

| 模式 | .text imm32 | .data/.rdata | 判定 |
|---|---|---|---|
| `FE00FFFF` | **0** | 0（dword 全段） | **排除**代码常量 / 分配器 fill |
| `FFFF0000` | 197（多为 `mov r/m,0xFFFFFFFF` 对齐残留 / 掩码） | 多 | 非毒源；见 2.3 栈同族 |
| `00FFFF00` | 28 | 少 | 无业务聚类 |
| `FFFFFE00`（-512） | **17**，其中 4 处 `push imm32` | — | **命中**：坐标构造 |
| `0000FE00` / `FE00` as u16 store | 0 次 `mov word,imm` | `.data` 中 `FE00` LE 100 次（指针低位/光强阶梯） | 排除直接 int16 立即数写 |
| 成对 int16 存储 `-1` 后 24B 内 `-512` | **0** | — | **排除**成对立即数写 |
| RGB565 打包（`shl reg,11`） | **53** | — | **命中**：存在 565 色打包路径 |

### 2.2 `-512` 坐标语义（`[实证]`）

```
0x4163CD: push 0 ; push 0xFFFFFE00 ; push 0xFFFFFE00
0x4163D9: lea ecx,[esp+0x34] ; call 0x41C230
0x41C230: mov [eax],ecx ; mov [eax+4],edx ; mov [eax+8],ecx ; ret 0xC
```
→ **CoordStruct 构造**（X/Y/Z 各 int32）。两组实参：`(-512,-512,0)` 与 `(512,-512,0)`。
`-512` 在 lepton 坐标（256 lepton=1 格）下 = **±2 格偏移**，符合包围盒/相对位移。

### 2.3 毒值位拆（`[推演]`，更新 R-02 §6.3）

| 视图 | 解读 | 支持 | 反证 |
|---|---|---|---|
| **int16 对 LE** `(0xFFFF, 0xFE00)` = `(-1, -512)` | `CellStruct{X=-1, Y=-512}` | `CellStruct=Vector2D<short>`；`WaypointClass.Coords` 在 +0；栈 `FFFF0000`=`{0,-1}` 像无效行哨兵 | 无成对立即数写；Y=-512 非合法格 |
| **RGB565 双像素** `(白, 纯红)` | 2 像素色对 | 53 处 565 打包；白/纯红是队伍色/受击闪典型 | 无「双像素写入 class4 起点」直接证据 |
| uint32 `0xFE00FFFF` | — | — | 无枚举/魔数命中 |
| float bit | 指数极小负 | — | 业务上不像 |

> [实证] 判别式：`FE00FFFF & 3 == 3` → **非对齐**，排除「链表 next 指针被写」类假设；必须是数据。

### 2.4 结构落点（`[实证]` YRpp + 反汇编）

```
WaypointClass          = { CellStruct Coords; DWORD unknown; }   // 8B，Coords@+0
DynamicVectorClass<T>  buffer = Capacity * sizeof(T)
  T=WaypointClass(8B) → cap 8 = 64B、cap 9 = 72B  ⇒ class 4
BasePlanningCell       = { int Weight; CellStruct Position; }    // 8B，Position@+4
BasePlanningCellContainer.Items 同为 cap*8 buffer（cap 8/9 = class 4）
```

---

## [3] class 4 生命周期热点（U0200 口径）

| 类型 | size | U0200 churn | 依据 |
|---|---|---|---|
| WaypointPathClass + 其 vector buffer | 0x40 / 64-72B buffer | **高** | 713 单位寻路重算；ctor `0x763810` 7 个调用点 |
| AlphaShapeClass | 0x40 | **高** | 视觉叠加随单位死亡/遮挡；ctor 仅 1 点但 delete 窗口密 |
| PixelFXClass | 0x3C | **高** | 像素特效 |
| TriggerClass / TagClass | 0x48 | 中 | 事件驱动；`0x6E4F29` 循环建链 |
| DiskLaserClass | 0x40 | 中低 | 武器开火才建 |
| Walk/Tunnel Locomotion | 0x3C | **低** | 随单位长寿 |
| MSAnim/BitFont/Menu/Multiplayer* | 0x3C-0x44 | 低 | UI/开局/字体 |
| INI 节点 | 0x44 | 极低 | 装载期 |

> [实证] delete 窗口密度（±0x600）：WaypointPath 4、AlphaShape 6、WalkLoco 7、MSPCXAnim 6 —— 与上表一致。
> [推演] 污染发生在 group=7 的 class-4 head，说明**已有多轮 alloc/free**（group 需提交过 page-group），与「高 churn 小结构」相符。

---

## [4] UAF 写者候选排序

| 序 | 候选 | 等级 | 支持证据 | 反证 / 缺口 |
|---|---|---|---|---|
| **1** | **WaypointClass.Coords 写穿已释放的 DynamicVectorClass buffer（cap 8/9 = class 4）** | `[推演]·主` | ①Coords 在对象偏移 0，与 free 节点 `next`（user+0）重合；②vector buffer 尺寸精确落 class 4；③扩容 free 旧 buffer 是经典 UAF；④`-1` 是常见无效格哨兵，栈 `FFFF0000`=`{0,-1}` 同族；⑤U0200 寻路高 churn | Y=-512 非典型格坐标；未指认具体写点 VA |
| **2** | **RGB565 双像素（白/纯红）经悬垂绘制/缓冲指针写入 class-4 起点** | `[推演]·次` | ①53 处 565 打包代码；②毒值=完美双像素；③PixelFX/AlphaShape/BitFont/MSAnim 均在绘制链；④受击闪/队伍色常用纯红 | 无「2 像素写到 class4 块头」直接字节证据；0x3C/0x40 对象 +0 多为 vtable |
| **3** | **AlphaShapeClass / PixelFXClass 视觉对象 UAF**（含 `AttachedTo` 悬垂） | `[推演]` | 高视觉 churn；AlphaShape ctor 含 nX/nY；PixelFX 与 565 相邻 | +0 是 vtable，业务写更像落在坐标字段（+4 起）而非 +0 |
| **4** | **TriggerClass/TagClass 链表节点**（`0x6E4F29` 循环建链） | `[推演]·弱` | size 0x48=class 4；`[+0x28]` 串链；事件风暴下 churn | +0 是 vtable；链表指针应对齐，`FE00FFFF` 未对齐 |
| **5** | **`0x408B7B` 无 vtable 列表+位表容器** | `[推演]·弱` | +0 即 freelist `next` 重合位；无 vtable 更易被数据写穿 | `FE00FFFF` 不是指针形态；容器偏业务位表 |

**已反证**（继承 R-02）：未初始化槽位（`MEM_COMMIT` 清零）；纯 double-free（自环不产生毒值）；分配器 imm fill（无 `CD/DD/FD` 且 imm 扫描 0 命中）。

---

## [5] 传播路径（收敛版，`[推演]`）

```
T0  vector/wpt-buffer (class4, cap8) 被 free → node->next=head, user+0 暂为 next 指针
T1  过期 WaypointClass* 写 Coords = (int16)-1, (int16)-512
        ⇒ user+0 = 0xFE00FFFF  (= node->next 被业务数据覆盖)
T2  alloc(class4) 摘链：head->next = node->next = 0xFE00FFFF   @ 0x7CFD4C/0x7CFD52
T3  alloc(class4) 再取：edx=head->next=0xFE00FFFF; mov ecx,[edx] @ 0x7CFC9F → AV
```

与崩溃现场（`EDI=4`，毒在 heap_info head 数组）完全同构。

---

## [6] 下一步（给 M 轨 harness / 后续 R 卡）

| # | 动作 | 目的 |
|---|---|---|
| 1 | H2+H6（R-02 §7）优先上线 | 毒族出现在 `head->next` 即 dump |
| 2 | `free_block` 后对 class-4 node 布写监视（影子内存） | 直接抓 T1 写者 VA |
| 3 | 对 `WaypointPathClass` vector 扩容点（`DynamicVectorClass` add）下断 | 验证 W1 |
| 4 | 对 RGB565 打包收尾存储下硬件断点（写 `0xFE00`/`0xFFFF` 相邻 u16） | 验证 W2 |
| 5 | A/B：禁用路径规划/AlphaShape 各一组 | 若毒值消失则归因成立 |

---

## [7] 证据锚点

| 证据 | 路径 |
|---|---|
| 分配点扫描器 | `out/re_work/re_sprint/sbh_uaf/scan_c4_alloc.py` |
| 31 个 class4 点（VA+size+ctor+vtable） | `c4_alloc_sites.json` / `c4_alloc_sites.txt` |
| 类型识别（988 类 vtable 映射） | `c4_type_identify.json` / `c4_type_identify.txt` |
| ctor 深挖 | `c4_ctor_deep.txt` |
| 尺寸直方图 | `c4_size_histogram.csv` |
| 毒值常量反查 | `poison_const_xref.txt` / `poison_semantics_deep.txt` |
| 生命周期/写者证据 | `poison_and_lifetime.txt` / `uaf_writer_evidence.txt` |
| claims | `claims.txt` |
| 上游 R-02（只读） | `docs/re/sbh_freelist_deep_dive.md` |
| 上游 except（只读） | `docs/re/except_zc11_forensics.md` |
| 二进制 | `ra2youli/gamemd.exe` MD5 `4f37486e5b0dbe2ae5f45aeee0f98367` |

**一句话**：class 4 在 gamemd 里是一撮小结构（Trigger/Tag/WaypointPath/AlphaShape/PixelFX/Loco/INI 节点…）；毒值 `FE00FFFF` 不是常量而是业务数据，最贴 `WaypointClass.Coords`（CellStruct 偏移 0 + vector buffer 尺寸落 class 4）或 RGB565 白/纯红双像素——写者归因待 H2/H6 影子监视收口。
