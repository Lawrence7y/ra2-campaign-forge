# 雷达小地图「单位点」绘制内层逆向（gamemd.exe 1.001）

> 任务：锁定侧边栏雷达小地图上单位/建筑色点的绘制内层函数，为「小地图与世界视图三态迷雾一致」做地址级准备。
> 本文档为纯逆向结论，不含补丁。基址 ImageBase=0x400000。工具：`tools/xref_scan.py`、`out/reverse/asm.py`（capstone 5.0.7）。

---

## 1. 结论（先看这里）

| 问题 | 结论 |
|---|---|
| 单位点是谁画的 | **`0x00655C50`**（`RadarClass::DrawCell`，逐雷达格内层）。它对每个雷达像素/格做：格坐标反算 → 迷雾判定 → **RTactical 空间哈希查该格上的 Techno 列表** → 逐对象可见性过滤 → 取 House 色 → `Surface::SetPixel`（vtable+0x24）写一个色点。 |
| 枚举源 | **不是** `House::Units/Infantry` 列表，也**不是** 全局 Techno 数组（v1.5.2 已排除 0x8B4108 系）。而是 **RTactical 哈希**（`RadarClass+0x1258`，256 桶 × 0x18，桶内 16 字节条目 `{Techno*, cellX, cellY, ?}`），由对象在格子上登记，雷达按 `(X − Y*5) & 0xFF` 选桶后线性扫桶内条目匹配 cellX/cellY。 |
| 颜色 | 按 **House 颜色查表**：`Object::v[49]`（0xC4）判是否走特殊色；否则 `ebx = House*`（`Techno+0x21C`），从 **`HouseClass+0x56F9/56FA/56FB`** 读 RGB 三字节，再用显示格式掩码 `0x8A0DD0..0x8A0DE4` 打包成像素。`UnitClass::v[52]`（0xD0）覆写：友军/己方返回 House，敌方返回 `Unit+0x51C`（伪装色源）。取不到时回退 `ColorSchemeClass::FindOrCreate(0x68CA50)` 从全局表 `0xB054D4` 查。 |
| 敌方「已探索无视野」行为 | **原版永久可见**。`0x586360`（IsShrouded，`Cell+0x12C` bit3 清=未探索）为真时才做 House 可见性过滤（`0x50B6F0`）；`0x5864A0`（IsFogged，`Cell+0x13C>0`）**只影响地形变暗**（RGB>>1），**不过滤对象点**。三态迷雾缺口就在：fogged 格仍画敌方点。 |
| 建筑 vs 移动单位 | **同一条路径**，均为 `0x655C50` 单点写像素。建筑占多格，每格各自命中并各画一点，自然形成多像素块；`FoundationTypePixels[22]`（`RadarClass+0x1278`，22×0x18 DynamicVectorClass，建筑地基像素）在本链未参与单位点绘（见 §6 未决）。类型标志 `Type+0x232 / Type+0xC9B / HouseType+0x1A6` 控制是否上雷达，`Type+0x22F` 要求「仅己方/盟军可见」。 |
| 最小侵入 Hook 点 | **`0x00655C50` 对象循环内、写像素前**（`0x00655F48` 处），按 `s_visionGrid` 对「敌方且 IsFogged 且 !IsShrouded」短路跳过。详见 §5。 |

---

## 2. 绘制链（自外向内）

```
GScreenClass::Draw / 主循环
  └─ SidebarClass::v[16] = 0x006A6C30          ; 侧边栏整帧协调（含雷达区）
       ├─ 0x004AED70 ×N                        ; 侧边栏框体/图标 blit（非单位点）
       ├─ 0x006A9540                           ; 侧边栏标签条（非雷达点）
       ├─ 0x0063FB20  PowerClass::v[16]        ; 电力条分段 blit
       │    └─ 0x00653100  RadarClass::v[16]   ; ★ 雷达小地图本体
       │         ├─ 0x0065FDD0                 ; 雷达事件闪烁图标（RadarEvent，非单位点）
       │         │    └─ 0x0065FE00 ×N         ; 单事件动画更新
       │         ├─ 0x00656EC0                 ; 雷达地形 + 视口矩形
       │         │    ├─ 0x00655250            ; 格子地形色缓存（写 +0x123C RGB 缓冲）
       │         │    ├─ 0x00655C50  ★★★      ; ★ 单位/建筑点内层（本文核心）
       │         │    ├─ 0x006562D0            ; 视口白框描边（叶子，直写像素）
       │         │    ├─ 0x00660000/0x006603B0 ; 雷达事件列表维护
       │         │    └─ 0x004AED70            ; 雷达框 blit
       │         ├─ 0x00653FA0                 ; 雷达上文字/标签（ColorScheme 查色）
       │         └─ 0x006579E0                 ; 雷达点击/音效分支
       └─ 0x006A70E0                           ; 雷达激活/翻转状态机
```

补充：
- `PowerClass::Draw_It`（`v[33]=0x00640450`）仅在 arg==0x3E7 时走文本路径（`0x734E60`），否则转发 `RadarClass::Draw_It`（`0x00658770` → `DisplayClass::Draw_It 0x004AE4F0`，即世界视图，不是小地图）。
- **小地图点绘完全不在 Draw_It 链上**，而在 `SidebarClass::v[16] → PowerClass::v[16] → RadarClass::v[16]` 链上。v1.5.2 建议的「Hook RTactical 33 槽」只能截获世界视图 Draw_It，**不能**截获小地图点绘。

### 2.1 `0x00655C50` 伪代码（单位点内层）

```c
// this = RadarClass* (0x87F7E8 = Instance)
// arg  = Point2D* radarPixel   (ret 4)
void RadarClass__DrawCell(Point2D* rp) {
    if (!PlayerHouse) return;                         // [0xA83D4C]
    // 1) 反算地图格: cell = f(rp, RadarSizeFactor=this+0x1488, offset=+0x1490/+0x1498)
    // 2) 迷雾判定
    bool shrouded = IsShrouded(cell);                 // 0x586360 → [esp+0x44]
    bool fogged   = IsFogged(cell);                   // 0x5864A0 → [esp+0x13]
    // 3) RTactical 哈希查该格对象
    //    bucket = ((cellX - cellY*5) & 0xFF);  base = [this+0x1258]->Items
    //    entry  = base[bucket] : { Items*, Count }   (桶 0x18B, 条目 16B)
    //    for each e in bucket.Items[0..Count):
    //      if e.cellX==cell.X && e.cellY==cell.Y:   // 命中
    Techno* obj = e.object;
    // 4) 可见性过滤
    if (shrouded && !HouseRadarVisible(obj->Owner))   // 0x50B6F0
        continue;                                     // 未探索: 只画己方/盟军
    //    ★ 缺口: fogged 时无此过滤 → 敌方点仍画
    if (Type+0x22F && !PlayerSeesHouse(obj))          // 0x4F9A90
        continue;
    if (!(Type+0x232 || Type+0xC9B || HouseType+0x1A6))
        continue;                                     // 不上雷达的类型
    // 5) 取色
    void* colorSrc = obj->Owner;                      // +0x21C
    if (obj->v[49]())                                 // 0xC4 → Techno+0x1D8
        colorSrc = obj->v[52](0);                     // 0xD0: Unit 覆写 → House 或 +0x51C
    uint32_t px;
    if (colorSrc)
        px = PackRGB(colorSrc+0x56F9, +0x56FA, +0x56FB, masks_0x8A0DD0);
    else
        px = ColorScheme_FindOrCreate(0x836ECC,1) [+0x330];   // 0x68CA50
    // 6) 选主自己/己方时按 timer 闪烁 (this+0x174/+0x17C, Camera+0x88)
    // 7) 写像素
    surface->SetPixel(rp, px);                        // this+0x121C, vtable+0x24
    return;                                           // 一格只画一个点(首个命中即出)
}
```

---

## 3. 枚举源与关键数据结构

### 3.1 RTactical 空间哈希（`RadarClass+0x1258`）

由 `RadarClass` 构造函数 `0x00652960` 分配：

| 地址/偏移 | 含义 |
|---|---|
| `this+0x1258` | `RTactical*`（16 字节对象，堆分配） |
| `RTactical+0x00` | `BucketArray*` → 256×0x18 桶（堆块 0x1804 = 4 + 256×0x18） |
| `RTactical+0x04` | 哈希函数指针 = **`0x006558B0`**（`return X + Y*251`） |
| `RTactical+0x08` | 桶数 = 256 |
| `RTactical+0x0C` | 初始桶容量 = 10 |
| 桶 +0x04 | `Items*`（对象条目数组，条目 16 字节） |
| 桶 +0x10 | `Count` |
| 桶 +0x14 | 容量（=10） |
| 条目 +0x00 | `TechnoClass*` |
| 条目 +0x04 | cellX |
| 条目 +0x08 | cellY |
| 条目 +0x0C | ？ |

- 哈希一致性：`X + Y*251 ≡ X − Y*5 (mod 256)`，故插入用 `0x6558B0`、查询用 `(X−Y*5)&0xFF` 等价。
- 一格命中多个对象时，**首个通过过滤的即画点并返回**（循环不继续），存在遮盖顺序问题（见 §6）。
- 插入/删除入口未在本轮完全定位（应为对象 `Put/Remove` 或 Cell 登记路径）；`0x00658DE0` 是桶内向量初始化。

### 3.2 雷达地形缓存与视口

| 偏移 | 含义 |
|---|---|
| `+0x121C` | 雷达图标 Surface*（`SetPixel` 走 `vtable+0x24`） |
| `+0x1224` | 向量对象（vtable `0x7E3890`，容量 10） |
| `+0x1228 / +0x1234` | 待重绘格列表 Items / Count（`0x655250` 消费） |
| `+0x123C` | 地形色缓冲（每格 3 字节 RGB） |
| `+0x1240 / +0x1244` | 缓冲宽/高 |
| `+0x1248` | 脏矩形（`0x655250` 产出） |
| `+0x1278..` | `FoundationTypePixels[22]`（22×0x18 DVector，地基像素） |
| `+0x1488` | `RadarSizeFactor`（float，像素/格比） |
| `+0x1490/1498/149C/14A0` | 雷达地图原点/缩放偏移 |
| `+0x14DC` | 雷达目的矩形 |
| `+0x1260 / +0x126C` | 脏点列表 Items / Count（`0x655C50` 调度源） |

### 3.3 可见性/颜色辅助

| 地址 | 作用 |
|---|---|
| `0x00586360` | **IsShrouded**：`Cell+0x12C` bit3（0x08）清 → 未探索 → 返回 1 |
| `0x005864A0` | **IsFogged**：`Cell+0x13C > 0` → 有遮蔽/雾 → 返回 1 |
| `0x0050B6F0` | `House::RadarVisible`：`[0xA8B238]!=0` 时仅 `House==PlayerHouse`；否则 `House+0x1EC \|\| House+0x1ED` |
| `0x004F9A90` | `PlayerHouse::SeesHouse(obj)`：v[0x3C] 取 Owner → 同 House 或 `House+0x5788` 位掩码测试 |
| `0x0068CA50` | `ColorScheme::FindOrCreate(name, idx)`，全局表 `0xB054D4`，Count `0xB054E0` |
| `0x0041C010` | `Techno::v[49]` = `return this+0x1D8`（是否特殊色/伪装） |
| `0x0041BE70` | `Object::v[52]` = `return 0`（基类） |
| `0x007465F0` | `Unit::v[52]`：`0x4F9A50(Owner,Player)` 为友且 arg==0 → 返回 Owner；否则 `this+0x51C` |
| `0x8A0DD0..0x8A0DE4` | 显示格式 RGB 移位/掩码（打包像素用） |
| `0xA83D4C` | `PlayerHouse*` |
| `0xA8ED84` | 当前帧号（闪烁 timer 用） |
| `0xB73550` | **〔勘误 E4 · 2026-09-27〕已就地更正**：该全局 = **`Game::hWnd`（游戏主窗口句柄 HWND）**，**不是迷雾开关、与编辑器/特殊模式无关**。原记（保留）：~~为 0 时跳过迷雾检测（编辑器/特殊模式）~~ ⇒ 正解：**= 0 表示主窗口尚未创建（`Game::hWnd` 未落地）**，即启动早期；窗口一旦由 `CreateWindowExA` 建立即恒非 0（**菜单与局内皆非 0**）。<br>证据：唯 2 写点 `0x777CD6`/`0x777D7E`（均 `A3 50 35 B7 00 mov [0x00B73550],eax`，紧随 `call [IAT 0x7E14D4 = USER32!CreateWindowExA]`）；77 处读点全部当 Win32 句柄用（`0x692489 A1 50 35 B7 00`、`0x6931DD`→`SetCapture`、`0x6938D5`→`ReleaseCapture`）；引擎 `Plot_Cell` 内 `0x00655D62 = 39 2D 50 35 B7 00 cmp dword [0x00B73550],ebp` 的语义 = 「主窗口是否已创建」（游戏内恒真）。<br>⚠️ **禁止写该全局**：会污染 70+ 处 Win32 调用。 |

### 3.4 类型标志（控制是否上雷达）

| 偏移 | 行为 |
|---|---|
| `TechnoType +0x22F` | 若置位：额外要求 `0x4F9A90(Player, obj)==true`（仅己方/盟军可见） |
| `TechnoType +0x232` | 若置位：**上雷达** |
| `TechnoType +0xC9B` | 若置位：**上雷达**（与上者 OR） |
| `HouseType  +0x1A6` | 若置位：**上雷达**（与上两者 OR） |

三者皆假则跳过。具体 YRpp 字段名待对号（疑 `RadarVisible` / `Invisible` / `ConsideredAircraft` 系，见 §6）。

---

## 4. 敌方单位在「已探索无视野」时的原版行为

三态对照（以 `0x655C50` 为准）：

| 格子状态 | 判定函数 | 地形 | 敌方单位点 | 己方/盟军点 |
|---|---|---|---|---|
| **未探索（Shrouded）** | `0x586360`=1 | 黑/图标 | **不画**（`0x50B6F0` 拦截） | 画 |
| **已探索无视野（Fogged）** | `0x5864A0`=1，`0x586360`=0 | 变暗（RGB>>1） | **仍画** ← 缺口 | 画 |
| **当前有视野（Clear）** | 两者皆 0 | 正常 | 画 | 画 |

**结论**：原版小地图对「已探索但无视野」的敌方单位是**永久可见**的；只有未探索区才按 House 过滤。这与 L3 世界视图的三态迷雾（未探索黑 / 已探索暗 / 视野内亮，敌方机动单位视野外剔除）不一致。要一致，必须在 `0x655C50` 对象循环里对 **fogged 且敌方** 补一条剔除。

注意：L3 自定义 `s_visionGrid` 不写引擎 `Cell+0x12C/0x13C`，因此 `0x586360/0x5864A0` 在 L3 环境下语义可能与原版不同（v1.5.2 已述「迷雾不退化到真图」问题）。Hook 时应直接查 `s_visionGrid`，不要依赖这两个引擎函数。

---

## 5. 最小侵入 Hook 点表

| 优先级 | 地址 | 函数/位置 | 建议写法 | 侵入面 | 风险 |
|---|---|---|---|---|---|
| **P0** | **`0x00655F48`** | `0x655C50` 对象命中后、取色前（`test ebp,ebp` 处） | JMP 到 trampoline：若 `obj` 为敌方 && `s_visionGrid` 无直视 && 该格已探索 → 跳回 `0x00655E66`（continue）；否则执行原 2 条指令后回 `0x00655F4A` | 仅 1 个分支点，不改枚举/不改虚表 | **低**；每格至多 1 次判断（短路），不扫全表 |
| P1 | `0x00655DEB` | `0x50B6F0` 调用点（shrouded 分支） | 将判定改为 `shrouded \|\| (fogged && enemy)` 后统一走 House 过滤 | 复用原有过滤路径 | **低**；语义与 P0 等价但更内聚 |
| P2 | `0x00655C50` 入口（`0x00655C50`） | 整函数包装 | 仅当雷达可见区域变化时才调用原函数（限频） | 大 | **中**；需自行维护脏区 |
| P3 | `0x0065336D` | `RadarClass::v[16]` 中 `call 0x65FDD0` 前 | 帧级入口：先按 `s_visionGrid` 重建「允许绘制」掩码，再进原链 | 中 | **中**；与 L4 脏矩形联动 |

### 5.1 推荐 P0 补丁形态（示意，非落地代码）

```
; 0x655F48 处 (原: test ebp,ebp / je 0x655e7e)
; trampoline:
    test ebp, ebp
    je   .orig_je              ; 无对象走地形
    pushad
    ; 取 obj->Owner, 判 IsEnemy(PlayerHouse)
    ; 取 cell → s_visionGrid[cell] 是否直视
    ; 若 enemy && !visible && explored → popad; jmp 0x655E66 (skip this obj)
    popad
.orig:
    ; 执行原 test/je 被覆盖的等价指令
    jmp  0x655F4A
```

### 5.2 性能约束

- `0x655C50` 是**按雷达像素/脏格**调用，不是每帧全量扫 N 单位；对象遍历发生在**该格的哈希桶内**（通常 0~3 个）。
- 雷达刷新由 `0x653100` 的脏矩形/`+0x14AC` 状态门控，并非每帧全图重绘。因此 P0 的每点一次 `s_visionGrid` 查询可接受。
- 若 L3 `s_visionGrid` 查询代价高，建议在 `0x653100` 入口（P3）做一次「本帧雷达可见掩码」烘焙（bitset，按雷达分辨率 ≤256×256），`0x655C50` 内 O(1) 查位。
- 严禁在 `0x655C50` 内做全 House 列表扫描；枚举源已是空间哈希，保持 O(桶内)。

---

## 6. 与 L3 衔接建议

1. **谓词统一**：`s_visionGrid` 三态判定谓词与世界视图 L3（`Hook_Unit/Infantry/Aircraft/Building_Draw` 系）共用同一函数，避免两处逻辑漂移。
2. **过滤语义**：
   - 未探索：沿用原版（仅己方/盟军点）。
   - 已探索无视野：**新增**敌方机动单位点剔除（与世界视图 L3 一致）；建筑点可保留（战术上建筑常按「最后已知位置」保留，需产品决策，见 §7）。
   - 视野内：全画。
3. **不要走虚表 33 槽**（`Draw_It`）做小地图迷雾——它只管世界视图。小地图入口是 `SidebarClass::v[16]` / `RadarClass::v[16]`。
4. **不要重新开启 `Scenario.Flags&0x1000`**（v1.5.2 红线）；L3 自建网格是唯一真源。
5. **与 L4 脏矩形**：`0x655C50` 写像素后会并入 `+0x120C` 视口矩形（函数尾部 rect-union）。L3 剔除点导致的像素差异需触发雷达区 dirty，否则小地图会残留旧点。可在 P0 跳过绘制时同步 `RegisterDirtyArea(0x6D2790)` 或置 `0xB0B518=1`（雷达重绘标志）。
6. **Hook 验收**：用 `out/BareTest` 或 loadbench 场景，造「已探索无视野敌方单位」用例，比对小地图与世界视图同帧截图。

---

## 7. 未决问题

| # | 问题 | 影响 | 下一步 |
|---|---|---|---|
| U1 | `TechnoType+0x22F/0x232/0xC9B`、`HouseType+0x1A6` 的 YRpp 正式字段名未对号 | 影响按类型精细过滤（如隐形/间谍） | 对 YRpp 属性区做偏移标定，或反汇编 Type 加载器 |
| U2 | RTactical 哈希的**插入/删除**函数未定位（对象上格/离格时登记） | 若改枚举源需知写入点 | 从 `0x658DE0` / `0x658D60` 的调用者与 `Techno::Put/Remove` 虚函数追 |
| U3 | `FoundationTypePixels[22]` 的实际消费点 | 建筑是否在高缩放下画多像素地基 | 扫 `this+0x1278` 位移引用（集中在 `0x666F9x/0x6749xx/0x4632xx`），确认是否与雷达点绘同路 |
| U4 | 同格多对象「首个命中即画」的优先级（己方/敌方、建筑/单位） | 一格多单位时点色归属 | 动态 Hook `0x655C50` 记录顺序；或产品定义优先级 |
| U5 | `House+0x1EC/0x1ED` 语义（`0x50B6F0` 用） | 与 L3「玩家/盟军」判定是否同一套 | 对 YRpp HouseClass 偏移标定 |
| U6 | `Cell+0x12C` bit3、`Cell+0x13C` 与 L3 `s_visionGrid` 的映射关系 | L3 清零引擎雾后这两个值是否恒「未探索」 | 跑局内对照；L3 Hook 直查网格即可，但需确认原函数不会误判 |
| U7 | 雷达事件（`0x65FDD0/0x65FE00`）在迷雾外是否也应抑制 | 事件图标会泄露位置 | 观察 `RadarEventClass` 可见性；按产品需求决定 |
| U8 | `0x6562D0` 视口白框是否受迷雾影响 | 无 | 只是 UI 框，应恒画 |

---

## 8. 附：本轮验证方式

- 静态：`tools/xref_scan.py fn/xrefs` + `out/reverse/asm.py dump/feat` 逐层展开 `0x6A6C30 → 0x63FB20 → 0x653100 → 0x656EC0 → 0x655C50`，交叉 `out/reverse/symbols.json` vtable 归属。
- 关键判定均基于反汇编原语：`0x50B6F0`/`0x586360`/`0x5864A0`/`0x7465F0`/`0x6558B0`/`0x68CA50` 全文反汇编确认。
- **未做动态 Hook 验证**（本轮纯调研）。落地补丁前建议按 §5.1 在调试器下对 `0x655F48` 设断，确认 `ebp` 为 Techno*、`[ebp+0x21C]` 为 House*、写像素走 `[this+0x121C]→v[9]`。

---

## 9. 冲刺结论（S10）

### 9.1 小地图“点绘内层”隔离定位与物理分界

在 S10 冲刺中，通过对 `0x00656EC0`（`RadarClass::DrawMap`）、`0x00655C50`（`RadarClass::DrawCell`）、`0x00655250`（`RadarClass::DrawTerrainCache`）及 `0x00657CE0` 的逐指令反汇编，彻底廓清了小地图点绘流程与其底层地形的物理边界与寄存器状态：

1. **帧级调度与脏门控（`0x00657180 - 0x006571C3`）** `[实证]`
   - 在 `0x00656EC0` 入口及坐标反算后，依次检查：
     - 视口矩形是否变化：`cmp [esi+0x14F4], [ebp+8]` 等；
     - 雷达事件是否有更新：`call 0x00660530`；
     - 待重绘脏点向量计数：`mov eax, [esi+0x126C]; test eax, eax; jg dirty`；
     - 待重绘格子列表计数：`mov eax, [esi+0x1234]; test eax, eax; jg dirty`；
     - 屏幕脏区检测：`call 0x00431800`。
   - 若五者皆无，直接 `je 0x00657872` 提前返回，跳过整幅小地图重绘。

2. **背景地形缓存与基底像素擦除** `[实证]`
   - `0x006571DA call 0x00655250`：消费 `[esi+0x1228..1234]` 脏格列表，从地图格读取基础 RGB 写入 `[esi+0x123C]` 缓冲，产出脏矩形 `[esi+0x1248]`（`RectangleStruct{X, Y, W, H}`）。
   - `0x0065733E - 0x00657353`（基底还原）：
     - `ecx = [esi+0x121C]`（雷达目标 `Surface*`）；
     - `edx = [esi+0x1220]`（干净地形背景 `Surface*`）；
     - `ebp = [esi+0x1248]`（脏矩形指针）；
     - `call dword ptr [eax + 8]`（`Surface::BlitRect`）。
     - **物理分界点**：该 Blit 将静态背景表面原样覆写到雷达目标表面，彻底擦除脏矩形内的前一帧旧色点与线条。

3. **双重点绘循环（Dot-Drawing Loops）** `[实证]`
   雷达向目标表面绘制单位/建筑色点严格发生在以下两个独立循环中：
   - **循环 1：脏矩形逐像素扫描循环（`0x0065749E - 0x006574F1`）**
     - 外层 X（`[esp+0x14]`）：`Rect.X` 到 `Rect.X + Rect.W`；
     - 内层 Y（`ebx`）：`Rect.Y` 到 `Rect.Y + Rect.H`；
     - 寄存器状态：`ecx = esi = RadarClass*`，栈上传入 `Point2D{X, Y}`；
     - `0x006574C3: call 0x00655C50`；
> 【W3 勘误 · W3-A6/ISSUE-DISAMBIG-RADAR-HOOK】改前：0x006574C3；改后：0x006574C3（RadarClass::Plot_Cell 主循环调用点，见 ra2render.h:158；实际补丁下沉点位于 0x00655D38，见 blitter_hooks.cpp:150, 3016）；依据：ra2render/ra2render.h:158; ra2render/blitter_hooks.cpp:150, 2711, 2920, 3016, 3090；分级：P2
     - 循环结束后，在 `0x006574F3 - 0x00657504` 将 `[esi+0x1248..1254]` 四个双字清零（清空脏矩形）。
   - **循环 2：脏点向量重绘循环（`0x0065750B - 0x00657526`）**
     - 遍历向量 `[esi+0x125C]`（`Items` 数组首地址 `[esi+0x1260]`，计数 `[esi+0x126C]`）；
     - `ebp = Count - 1` 倒序递减至 0；
     - `0x00657520: call 0x00655C50`，逐点重绘；
     - 循环结束后，在 `0x00657534: call dword ptr [edx + 0xC]` 清空该脏点向量（Count 置 0）。
   - **第 3 处调用点（全图重置）**：
     - 在 `0x00657CE0`（全图雷达重建），当 `[0x00B73550] != 0` 时，遍历表面全宽全高（`0x00657D68 - 0x00657D7F`），在 `0x00657D77: call 0x00655C50`。**【原记 · 见下条勘误 E4】**
       - **〔勘误 E4〕**该全局 = **`Game::hWnd`（主窗口句柄 HWND）**，此判据语义 = 「主窗口已创建（有渲染上下文）」，**不是迷雾状态**；窗口由 `CreateWindowExA` 建立后即恒真（菜单与局内皆非 0）。写它会污染 70+ 处 Win32 调用 ⇒ **禁止写入**。

4. **`0x00655C50`（`RadarClass::DrawCell`）内层判定与迷雾状态** `[实证]`
   - 入参：`[esp+0x44]`（`Point2D* radarPixel`）。
   - 浮点反算雷达格坐标，调用 `0x00578080`（`MapClass::GetCell`），返回值存入 `[esp+0x28]`（`CellClass*`）。**【原记 · 见下条勘误 E4b】**
     - **〔勘误 E4b · 2026-09-27〕本行两处旧述已被证伪（原句保留，不删除）**：① `0x00578080` 不是 `MapClass::GetCell`，而是 **`MapClass::GetCellFloorHeight()`**（`YRpp/MapClass.h:282`：`int GetCellFloorHeight(const CoordStruct&) const { JMP_THIS(0x578080); }`；尾部 `0x005780F6 = C2 04 00` = `ret 4`）；② 返回值**不是 `CellClass*`** 而是**格面高度 int**，`0x00655D38 mov [esp+0x28],eax` 写的是栈上 `CoordStruct.Z`（`0x655D2F` 已置 Z=0）。
     - 连带影响：依赖「`0x00655D38` 处 `EAX` 是 pCell」的旧路线 A 代理首道护栏 `cmp eax,0x10000 / jbe` 对高度值**恒真 ⇒ 恒拒静默早退**（真机「分支计数增长、灰化像素恒 0」的根因，RADAR-FIX2 定谳）。本文件其余关于 `0x00655C50` 绘制链的结论不受影响。
   - 迷雾状态提取：
     - `0x00655D4F: call 0x00586360`（`IsShrouded`）→ 暂存 `[esp+0x44]`（1=未探索）；
     - `0x00655D74: call 0x005864A0`（`IsFogged`）→ 暂存 `[esp+0x13]`（1=有灰雾/无直视）。
   - RTactical 哈希条目遍历（`0x00655D87 - 0x00655E78`）：
     - 哈希桶定位：`bucket = ((cell.X - cell.Y * 5) & 0xFF)`；
     - 桶首地址 `[esi+0x1258]`，每桶 24 字节（`0x18`），条目 16 字节；
     - 若命中格子且通过可见性过滤（`0x00655DF4` 系列类型/所有权判定），跳至 `0x00655F48` 打包 RGB，并由 `[esi+0x121C]->vtable+0x24`（`Surface::SetPixel`）写色点；
     - **未命中任何对象时的地形回退（`0x00655E7E`）**：
       - 若 `isFogged`（`[esp+0x13] != 0`）：调用背景表面 `[esi+0x1220]->vtable+0x28`（`GetPixel`），执行 `shr 1`（RGB 减半变暗），写回目标表面；
       - 若 `isShrouded`（`[esp+0x44] != 0`）：直接向目标表面写颜色 0（黑点）；
       - 若 clear：从背景表面 `GetPixel` 并直接 `SetPixel` 写回目标表面。

### 9.2 Cameo 脏门与 CanBuild (0x004F7870) 频率定论

1. **调用点 xref 普查** `[实证]`
   - `gamemd.exe` 全代码段直呼 `0x004F7870`（`HouseClass::CanBuild`）共 13 处：
     - AI 与建造放置逻辑：9 处（`0x004140CC`、`0x00445758/79D/7DE/81E`、`0x004FEDB7`、`0x004FF0E1`、`0x004FF411`、`0x00517DDB`、`0x005F79A3`、`0x007357DF`）；
     - UI 侧边栏：仅 **2 处**（`0x006A97D2` 在 `0x006A9540` 内，`0x006AA781` 在 `0x006AA600` 内）。
2. **渲染帧双门控机制** `[实证]`
   - 渲染主循环经 `SidebarClass::Draw`（`0x006A6C30`）每帧调度 `0x006A9540`。
   - `0x006A9540` 入口执行严格脏检测：
     - `0x006A954D: mov al, [esi+0x1C]; test al, al; je 0x6AA5A8`（`AllowedToDraw` 门）；
     - `0x006A9558: mov al, [esi+0x3C]; test al, al; jne 0x6A956E`（`NeedsRedraw` 门）；
     - `0x006A955F: mov al, [esp+0x484]; test al, al; je 0x6AA5A8`（`force` 门）。
   - **结论**：在侧边栏未脏且未强制刷新的常态渲染帧中，`0x006A9540` 在前 7 条指令内直接返回，**`CanBuild` 调用次数恒为 0**！
3. **重绘时的有限轮询** `[实证]`
   - 仅当逻辑层（如 `HouseClass::v[23]` 逻辑节拍）发现科技/资金变化而通过 `0x006A7D44: mov byte ptr [edi], 1` 置脏 `NeedsRedraw` 时，才会触发重绘。
   - 重绘时通过几何计算（`0x006A9607 - 0x006A9640`）**仅循环当前激活 Tab 的可见 Cameo 槽**（依分辨率为 6~10 个槽位），超武图标走独立充能判定，不查 `CanBuild`。
   - **瓶颈定论**：`CanBuild` 绝非每帧全量轮询 75×4 个图标；性能损耗仅出现在状态高频置脏帧，优化方向应为“状态脏标记合并”，无需侵入 `CanBuild` 算法内部。

### 9.3 鼠标选取、框选与迷雾交互定论

1. **画框选择（Band Select）与迷雾交互** `[实证]`
   - 入口为 `DisplayClass::LMBUp`（`0x004AB9B0`）中的 `DraggingRectangle` 分支。
   - 调用 `TacticalClass::ForEachInRect`（`0x006DA5C0`），以 `0x004AC2B0` 为回调扫描 `0x00B0CEC8` 交互列表。
   - 回调 `0x004AC2B0` 执行：
     - `0x004AC2B5: call dword ptr [eax + 0x3C]` 取所属 House；
     - `0x004AC2BE: call 0x0050B6F0`（`HouseClass::RadarVisible / IsControlledByPlayer`）。
   - 若非本地玩家或其盟军，`0x0050B6F0` 恒返回 false，直接退出（`je 0x4ac302`）。
   - **结论**：框选**未检查**迷雾状态（既不调 `0x00586360` 也不调 `0x005864A0`），但**敌方隐形/灰雾/迷雾单位绝对不可能被玩家误框选中**，因其所有权在首道门被 `0x0050B6F0` 硬性剔除；己方/友军单位即使处在迷雾中，只要矩形覆盖即可被选中。

2. **单键点击点选（Single Click）与迷雾交互** `[实证]`
   - 鼠标悬停/点击坐标解析位于 `ProcessClickCoords`（`0x00692300`）。
   - **黑雾硬拦截**（`0x00692480 - 0x00692500`）：
     - 调用 `IsShrouded`（`0x00586360`）。若置位且处于正常游戏模式，置 `*outShrouded = 1`。
     - 在 `0x006924FC: cmp byte ptr [esi], 0; jne 0x6925F0`，直接绕过“鼠标下对象解析”（`0x006DA380`），返回空对象。未探索黑雾中**绝对无法点中任何单位**。
   - **灰雾空桩漏洞**（`0x006924DF`）：
     - 灰雾判定调用 `0x005865E0`，但该函数在原版 gamemd.exe 中为**空桩**（`32 c0 c2 04 00`，即 `xor al, al; ret 4`），永远返回 0。因此 `*outFogged` 永远为 0，引擎原版不因灰雾而拒绝点击。
   - **屏幕交互列表依赖与隐形过滤（`0x006DA380`）**：
     - `0x006DA380`（`ObjectUnderCursor`）仅线性扫描 `0x00B0CEC8` 数组（上限 `Tactical+0xDB0`）。
     - 普查发现：`0x00B0CEC8` 的登记录入点 `0x006D9EF0` **仅在** `AircraftClass::v[69]`（`0x004148CC`）、`InfantryClass::v[69]`（`0x005192E6`）、`UnitClass::v[69]`（`0x0073CF6B`）等渲染绘制函数中调用；且每帧在 `TacticalClass::Draw`（`0x006D3D21`）中首先执行 `mov dword ptr [ebp + 0xDB0], 0` 清空计数。
     - **推论**：任何在当前视口内未被实际渲染绘制的单位（如未被探索、不在视野内因而未调 `Draw`），根本不会登记进 `0x00B0CEC8`，因而物理上不可被点击。
     - **隐形单位硬拦截**（`0x006DA409 - 0x006DA43C`）：`ObjectUnderCursor` 显式检测 `[eax + 0x220] == 2`（`CloakState == Cloaked`）。若隐形，调用 `0x004870D0` 检测玩家在该格是否有探测传感器（Sensor/Detector），若无探测器则直接跳过该单位。**敌方隐形单位在无探测器时绝对无法被盲点选中**。

