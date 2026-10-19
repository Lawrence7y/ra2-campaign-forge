# 侧边栏 / 鼠标点选 / 命令分发 逆向（gamemd.exe 1.001）

> 任务：逆向侧边栏（建造 Cameo / 超武图标）、鼠标点选与命令分发，供 UI 性能与迷雾一致性分析。
> 基址 ImageBase=0x400000。工具：`out/reverse/asm.py`（capstone 5.0.7）、`out/reverse/symbols.json`（988 类 vtable）、`YRpp` 具名地址交叉对照。
> 约束：只读逆向，不改总档案与源码/dll。本文档为纯逆向结论，不含补丁。
> 关联文档：`radar_minimap_dots.md`（小地图点绘）、`audio_input_hotspots.md`（输入环）、`dirty_rect_l4.md` / `dirty_rect_deep_dive.md`（脏区）、`pathfinding_deep_dive.md`（框选群体移动）。

---

## 0. 一页结论

| 问题 | 结论 |
|---|---|
| 侧边栏结构 | `SidebarClass`（Instance=0x87F7E8，与 MouseClass/DisplayClass 同一大对象）内嵌 **4 个 `TabDataStruct` Strip**（this+0x1544，每条 0xF94），每条含 **75 个 `CameoDataStruct`**（0x34/个）。Tab 索引 0=建造/1=防御/2=步兵/3=单位（`GetObjectTabIdx` 0x6ABC60/0x6ABCD0）。超武图标（ItemType=0x1F）走独立分支，不占 TechnoType cameo 槽。 |
| Cameo 纹理 | `TechnoTypeClass::Cameo / AltCameo`（SHP，+0x343/+0x347 附近），`FileSystem::CAMEO_PAL=0x87F6B0` 调色板；超武为 `SuperWeaponTypeClass::SidebarImage`（+0x60）。 |
| 每帧重绘还是脏区 | **混合**：`SidebarClass::Draw`（v[16]=0x6A6C30）每渲染帧执行；**侧边栏框体 chrome** 由 `SidebarNeedsRedraw(+0x53A6)/SidebarBackgroundNeedsRedraw(+0x53A7)` 脏标志门控（0x4AED70 blit ×7+行循环）；**Cameo 列表** 由 `TabDataStruct.AllowedToDraw(+0x1C)/NeedsRedraw(+0x3C)` 门控（0x6A9540 入口即判）；**电力条+雷达小地图链 0x63FB20 每帧跑**（与 radar 文档一致）。 |
| 鼠标 / 框选 | `WWMouseClass`（Instance=0x887640）只做光标合成/捕获；点选在 `DisplayClass::LeftMouseButtonUp`（0x4AB9B0）内：`DraggingRectangle`（this+0x11CF）为真时走 **`Tactical::ForEachInRect`（0x6DA5C0）对全局数组 0xB0CEC8 做线性扫描**（count=Tactical+0xDB0），逐条 12B `{obj,x,y}` 屏幕矩形测试——**不是空间哈希、不是全图 Techno 数组**，但也不是脏区增量。 |
| 框选过滤 | 仅 `0x50B6F0(House)`（本地玩家/盟军可控）+ `obj->v[78]/v[83]`（可选/可指挥）+ 建筑特判；**无迷雾判定**，也**不可能选中敌方**（被 0x50B6F0 挡掉）。 |
| 命令分发 | `CommandClass::Array`（DynamicVectorClass @ 0x87F658，Items 0x87F65C / Count 0x87F668）。46 个 `XxxCommandClass` 子类（symbols.json 全列），`Execute` = v[8]。快捷键→命令索引→`Execute`；侧边栏 Tab 命令（如 `SetDefenseTabCommandClass::Execute` 0x535E50）直接改 `SidebarClass::SetActiveTab`（0x6A7590）。右键目标不直接进 Techno，而是打包成 **NetworkEvent** 入环形缓冲（0xA802C8 计数 / 0xA802D0 写指针 / 0xA802D4 事件区），由网络层回放到 `TechnoClass::ClickedMission`。 |
| 工具提示 / CanBuild | Tooltip 缓冲 `SidebarClass::TooltipBuffer` @ 0xB07BC4（wchar[0x42]），悬停路径 `SidebarClass::v[34]=0x6ABD30`。**`HouseClass::CanBuild`（0x4F7870）在 Cameo 绘制循环内对每个可见槽各调 1 次**（0x6A9540 内 0x6A97D2），只在 Strip 需重绘时发生，不每帧全量扫描。 |
| 与迷雾关系 | ① Cameo 图标/可用性**与视野无关**（纯 House 状态+科技树）；② 小地图点绘见 radar 文档（fogged 不滤敌方点）；③ **点选敌方：`ProcessClickCoords`（0x692300）在 shrouded（未探索，`IsShrouded` 0x586360）时跳过“鼠标下对象解析”**，无法点到未探索区里的敌方；fogged（有探索无视野）分支里调用的 0x5865E0 **是空桩（xor al,al; ret 4）**，原版不因 fogged 拒绝点选；④ `DecideAction`（0x692610）再按 House 可控性/Action 类型过滤，敌方多数指令不会生成。 |
| 每帧成本 / 优化插入点 | 见 §6。真正的每帧固定成本是 **0x63FB20（电力+雷达）** 与 **0x6A6C30 调度壳**；Cameo 绘制被脏标志挡在门外。框选 O(N) 全扫仅在鼠标抬起瞬间。 |

---

## 1. 类层次与地址总表

### 1.1 继承链（symbols.json + YRpp）

```
IGameMap → GScreenClass → MapClass → DisplayClass → RadarClass → PowerClass → SidebarClass → TabClass → ScrollClass → MouseClass
                                                                    └─ 同一实例 0x87F7E8
TacticalClass (0x887324)  —— 视口/点选辅助，独立对象
WWMouseClass  (0x887640)  —— 硬件光标合成
```

| 符号 | vtable | 关键 vfunc |
|---|---|---|
| `SidebarClass` | 0x7F3058 | v[16]=**0x6A6C30 Draw**，v[33]=0x6AC210 Draw_It，v[34]=0x6ABD30 tooltip/悬停，v[50]=0x6A5BF0 建按钮，v[53]=0x6A5840 贴按钮图 |
| `SBGadgetClass@SidebarClass` | 0x7F2F44 | 侧边栏整体 gadget（收鼠标命中） |
| `SelectClass@StripClass@SidebarClass` | 0x7F2FCC | **Cameo 单格点击 gadget**，v[31]=**0x6AAD00**（点 Cameo 开始生产/出兵） |
| `MouseClass` | 0x7E1964 | v[19]=0x5BDC80 SetCursor，v[40]=0x40D280 RightMouseButtonUp |
| `WWMouseClass` | 0x7F7B2C | 光标画/捕获（18 槽） |
| `DisplayClass` | 0x7E6114 | v[33]=0x4AE4F0 Draw_It（世界），v[47]=0x4AC380 LMBDown，v[48]=**0x4AB9B0 LMBUp/点选**，v[45]=0x4AC310 清拖拽状态 |
| `Tactical` | 0x7F4348 | 视口辅助 |
| `CommandClass` | 0x7EBE3C | v[8]=Execute（46 个子类各覆写） |

### 1.2 全局/成员偏移

| 地址/偏移 | 含义 |
|---|---|
| `Sidebar+0x1544` | `Tabs[0]` 起点（TabDataStruct=0xF94，×4） |
| `Tab+0x1C` | `AllowedToDraw`（bool） |
| `Tab+0x38` | `TopRowIndex`（滚动顶行） |
| `Tab+0x3C` | `NeedsRedraw`（bool，画完清零） |
| `Tab+0x54` | `CameoCount` |
| `Tab+0x58…` | `Cameos[75]`（CameoDataStruct=0x34） |
| `Sidebar+0x539C` | `ActiveTabIndex` |
| `Sidebar+0x53A5/53A6/53A7` | 布局允许 / SidebarNeedsRedraw / SidebarBackgroundNeedsRedraw |
| `DSurface::Sidebar`=0x887300，`SidebarBounds`=0x886F90 | 侧边栏表面与边界 |
| `TooltipBuffer`=0xB07BC4 | wchar[0x42] |
| `0xB07E80` | **SelectClass gadget 数组**（每槽 0x38，最多 0x3C=60 格，按 TopRowIndex*60+col 寻址） |
| `0xB0B518` | 全局“侧边栏内容已变/需 present”标志 |
| `0xB07C48…0xB0B518`（步长 0x60） | 逐元素脏字节簇（Draw 末尾聚合成 0xB0B518） |
| `Display+0x11CF` | `DraggingRectangle` |
| `Display+0x11D0` | 拖拽附带状态（0x4AC310 成批清 0x11D0/11D4/11D8/11DC/11E0） |
| `0x88098C/90/94` | 点击/矩形角点暂存 |
| `0x886FA0/FA4` | 相机/视口偏移（屏幕→世界） |
| `0x887324` | `TacticalClass*` |
| `0xA802C8 / 0xA802D0 / 0xA802D4 / 0xA83A54` | NetworkEvent 环：计数(上限 0x80) / 写指针(&0x7F) / 事件体(0x73B/条) / 事件序号 |
| `0xB0CEC8` | **框选枚举源数组**（条目 12B：`{Object*, x, y}`），条数 `Tactical+0xDB0` |
| `0xA83D4C` | `PlayerHouse`（HouseClass*） |
| `0xA8ED6B` | 全局“某种禁绘/电影中”标志（Draw 入口短路） |
| `0xB73550` | 与 shroud 点击判定相与的开关（见 §5） |
| `CanBuild` | **0x4F7870**（`HouseClass::CanBuild(type, buildLimitOnly, allowIfInProduction)`） |
| `House+0x258` | `Supers`（SuperClass* 向量，超武 cameo 数据源） |

---

## 2. 侧边栏结构（Strip / Cameo / Tab）

### 2.1 TabDataStruct（即“Strip”）与 CameoDataStruct（即“Cameo”）

YRpp `SidebarClass.h` 给出的布局与汇编完全吻合：

```
CameoDataStruct (0x34):
  +0x00 ItemIndex      int      // TechnoType 数组下标，或超武索引
  +0x04 ItemType       AbstractType  // 0x1F = SuperWeaponType 走独立分支
  +0x08 IsAlt          bool     // 建筑放第二页（防御页）标志
  +0x0C CurrentFactory FactoryClass*
  +0x10 unknown_10
  +0x14 Progress       ProgressTimer  // 0..54 建造进度（gclock）
  +0x?? FlashEndFrame  int      // 闪烁（FlashCameo 触发器 0x6E4150）

TabDataStruct (0xF94):
  +0x00 Progress
  +0x1C AllowedToDraw
  +0x20 Location (Point2D)
  +0x28 Bounds (RectangleStruct)
  +0x38 TopRowIndex
  +0x3C NeedsRedraw
  +0x54 CameoCount
  +0x58 Cameos[75]           // 75 × 0x34 = 0xF3C；0xF3C+0x58 = 0xF94 ✓
```

排序：`CameoDataStruct::SortsBefore` = 0x6A8420（按 ItemType+Index 排序插入）。
进哪个 Tab：`SidebarClass::GetObjectTabIdx` = 0x6ABC60（abs+idx）/ 0x6ABCD0（abs+BuildCat+isNaval）——建筑可因 `IsAlt` 进第 2 页。

### 2.2 增删 Cameo

| 函数 | 地址 | 作用 |
|---|---|---|
| `RepaintSidebar` | 0x6A60A0 | 置脏并重排当前 tab（调 DisplayClass::v[14]） |
| `AddCameo` | 0x6A6300 | 784B：查重（SortsBefore 插入）→ 扩 CameoCount → 通知 gadget/音效（0x752700 EVA、0x723EA0/EB0 gadget 组） |
| `SetActiveTab` | 0x6A7590 | 切 tab：旧 tab `AllowedToDraw=0`，对 60 个 SelectClass gadget（0xB07E80 + (TopRowIndex*0x3C+i)*0x38）逐个 `v[13]=0x4F4450` 置脏，再 `0x723EA0` 显示新 tab gadget 组 |

### 2.3 超武图标（SW Cameo）特殊路径

`0x6A9540` 绘制循环里 `ItemType==0x1F` 跳 0x6A9936：

```
swType = [0xA8E334] (SuperWeaponTypeClass* 数组)[ItemIndex];
sidebarSH P = swType->+0x60;                 // SidebarImage
if (ItemIndex < [0xA8E340]) color = swType->+0xB8;
SuperClass* sw = PlayerHouse->Supers[ItemIndex];   // House+0x258
ready   = SuperClass::0x6CDE90(sw);          // IsReady（缓存到 [esp+0x14]）
charge  = SuperClass::0x6CC2B0(sw);          // GetCameoChargeState → 叠 charge overlay
state3  = SuperClass::0x6CBEE0(sw);
```

与 YRpp `SuperClass::HasChargeProgressed / GetCameoChargeState / ShouldDrawProgress / ShouldFlashTab` 一一对应。超武可用性**不走 CanBuild**，走 SuperClass 充能状态。

---

## 3. 每帧绘制链与脏区

### 3.1 总链

```
GScreenClass 每帧
 └─ SidebarClass::v[16] = 0x006A6C30   Draw(DWORD force)
      ├─ [条件] 侧边栏 chrome blit：0x004AED70 ×7 + 行数循环
      │        条件 = unknown_bool_53A5 && (arg || 53A6 || 53A7) && !0xA8ED6B
      ├─ ShapeButtonClass::v[27]=0x69DEB0 ×5   // 滚动钮/折叠钮等
      ├─ 0x006A9540(&Tabs[ActiveTabIndex], arg=53A7)   // ★ Cameo 条（见 3.2）
      ├─ PowerClass::v[16] = 0x0063FB20                // 电力条 + 雷达小地图（每帧）
      │    └─ RadarClass::v[16] = 0x00653100 …（详见 radar_minimap_dots.md）
      ├─ 脏字节簇 0xB07E4C/0xB0B3F4/0xB07C9C..0xB07E1C/0xB0B37C/0xB0B45C
      │    → OR 进 0xB0B518（“需要 present”）
      ├─ [0x887368]->v[3](1)                           // 呈现/tooltip 清理
      └─ 0x006A70E0(force)                             // 雷达激活/翻转状态机
      收尾: 清 53A6/53A7，恢复 0x887314（原 blit 目标）
```

### 3.2 Cameo 条 `0x6A9540` 的脏门

入口（ecx=&TabDataStruct）：

```
if (!tab->AllowedToDraw) return;                       // +0x1C
if (!tab->NeedsRedraw && !arg) return;                 // +0x3C
tab->NeedsRedraw = false;
0xB0B518 = 1;                                          // 通知 present
…按 SidebarBounds / 0xB0B4F8 等几何常量算行列…
for (row…col…) {  // 可见槽
    CameoDataStruct* c = &tab->Cameos[i];              // 步长 0x34
    if (c->ItemType == 0x1F) { SW 分支; continue; }
    TechnoTypeClass* type = 0x48DCD0(c->ItemType, c->ItemIndex);  // GetTechnoType
    if (!type) { 画灰/空 cameo; continue; }
    …
    if (!type->v[37](PlayerHouse,1,1,1)) …             // 科技/前置粗检（0x94 槽）
    r = HouseClass::CanBuild(PlayerHouse, type, 0, 0); // 0x4F7870  ★
    temporarilyUnbuildable = (r == -1);                // CanBuildResult::TemporarilyUnbuildable → 黑out
    0x50B370(PlayerHouse, …)                           // 再一道限制（工厂/占用）
    …叠 Progress 时钟、FlashEndFrame 闪烁、文本（SidebarCameoText）…
    blit cameo SHP → DSurface::Sidebar
}
```

**每帧成本判定**：tab 干净时 `0x6A9540` 直接返回（几次字节比较），CanBuild 0 次；生产/前置/金钱变化会置 `NeedsRedraw`，此时对**当前 tab 全部可见槽**各跑 1 次 CanBuild + 1 次 GetTechnoType + 1 次 SHP blit。槽上限 75（数据），可见数由分辨率/行高决定（经验 6×8~6×10 量级）。**CanBuild 不是每帧全量扫，而是“重绘时按槽扫”**。

### 3.3 与 dirty_rect 体系的关系

`0x4AED70` 是侧边栏框体的 shape blit（见 `rle_blit_family.md` / `blitter_microkernel_deep_dive.md` 的 blit 族）。chrome 部分只在脏时 blit；Cameo 表面写的是 `DSurface::Sidebar`（0x887300）而不是世界视图表面，因此**不进世界脏矩形队列**，优化侧边栏不会干扰世界 Draw_It 脏区。`0x887368->v[3](1)` 与 `0xB0B518` 是“侧边栏局部 present”通道。

---

## 4. 鼠标：WWMouse / MouseClass / 框选

### 4.1 分工

| 组件 | 地址 | 职责 |
|---|---|---|
| `WWMouseClass` | Instance 0x887640，vtable 0x7F7B2C | 硬件/合成光标绘制、`CaptureMouse/ReleaseMouse`；**不做点选逻辑** |
| `MouseClass` | Instance 0x87F7E8（同一超级对象） | `SetCursor/UpdateCursor`（v[84] 族）、`GetLastMouseCursor`；v[19]=0x5BDC80 在 Cameo 点击后换光标（引用 0x82D028 光标表） |
| `DisplayClass::LMBDown` 0x4A9DD0 / `LMBUp` 0x4AA050 | 规划/信标/地基模式的按下抬起 | 调 Tactical 0x6D8700 / 0x6DA7D0 |
| **`DisplayClass::LMBUp` 0x4AB9B0**（v[48]） | **真正的“点击+框选收口”** | 见下 |
| `DisplayClass::v[45]` 0x4AC310 | 清拖拽状态（0x11D0/11D4/11D8/11DC/11E0） | |

### 4.2 点选/框选主流程（0x4AB9B0，2400B）

签名（stdcall，ret 0x14）大致为 `LMBUp(Object* underMouse, CellStruct* cell, Action action, …)`。伪代码：

```
// 先处理 CurrentBuilding 放置、特殊对象（WhatAmI==7 建筑交换等）
if (this+0x11A4 /*CurrentBuilding*/ != null) { …放置/取消… }

if (this->DraggingRectangle) {                 // +0x11CF
    Tactical->+0xD7D = 1;
    if (!0x54F5C0(0x87F770, 0x10)) {           // 某种输入/修饰键检查
        if (0x6DA080(Tactical)==0) ebx=1; else 0x48DC90();
    }
    0x6D9FF0(Tactical, cb=0x4AC2B0);           // ★ 遍历矩形内对象（见 4.3）
    0x70D150();                                // 清/推选择集
    this->v[18](0, arg);                       // 虚函数收尾
    this->DraggingRectangle = 0;
    this->+0x11D0 = 0;
    0xA8ED9D = 1;
    if (!ebx) goto end;
}
// 然后按 Action switch 生成 NetworkEvent（见 §5）：
//  case 8  : 指挥（Guard/Attack 等）→ 0x732D00/0x7327D0/ v[0x14C]
//  case 7  : NoEnter/特殊
//  case 0  : 纯选择（v[78] 可选 + v[83] Select）
//  case 0x3D: 路径点（0x89C3B0 路径记录）
//  case 0x21/0x3C/0x0A/0x0D/0x0C: 维修/贩卖/部署… → 0x4C65E0/0x4C6650/0x4C6B60 事件
end:
    this->+0x11D0 = 0; 0x731CF0();  return;
```

### 4.3 框选枚举源：**0xB0CEC8 全数组线性扫描**

`0x6DA5C0`（由 `0x6D9FF0` 包装）是矩形遍历本体：

```
[0x822CF2]=1;
if (rect->w<=0 || rect->h<=0) end;
for (i=0; i < this+0xDB0; i++) {           // ★ O(N) 全量
    Entry* e = &([0xB0CEC8])[i];           // 12B: {Object* obj, int x, int y}
    obj = e->obj;
    if (!obj || !obj->+0x90) continue;     // +0x90 = 在图/激活
    dx = e->x - (this+0xB0);               // 0xB0/0xB4 = 相机偏移
    dy = e->y - (this+0xB4);
    if (dx < rect->x || dx >= rect->x+rect->w) continue;
    if (dy < rect->y || dy >= rect->y+rect->h) continue;
    // 命中矩形：
    if (0x732D00(obj)) { 0x7327D0(obj->v[34]()+0x24); continue; }  // 已是选择组
    if (callback) { callback(obj); continue; }
    // 内置过滤（无 callback 时）：
    bool buildingOk=false;
    if (obj->WhatAmI()==6) buildingOk = 0x465D40(obj->+0x520->+0x408);
    House = obj->v[15]();                  // GetOwningHouse
    if (!House || !0x50B6F0(House)) continue;      // ★ 仅本地玩家/盟军可控
    if (!obj->v[78]()) continue;                    // 可选中
    if (obj->WhatAmI()==6 && !buildingOk) continue; // 建筑需过特判
    if (!obj->v[83]()) continue;                    // Select()
    [0x822CF2]=0;                                    // 至少选中一个
}
[0x822CF2]=1;
```

**callback 0x4AC2B0** 同样过滤：`v[15] House → 0x50B6F0 → v[78] → v[79] → +0x81(未选?) → v[83] Select → [0x822CF2]=0`。

| 问题 | 答案 |
|---|---|
| 是否全图扫单位？ | **是线性全扫，但扫的是 `0xB0CEC8` 扁平条目数组（疑似“当前可交互/绘制清单”），不是 `TechnoClass::Array` 也不是 RTactical 空间哈希**。条数 = `Tactical+0xDB0`。 |
| 是否空间加速？ | **没有**。只有 int 矩形测试（4 次比较）作粗筛，随后才做虚函数过滤。 |
| 是否每帧？ | **否**。仅 `DraggingRectangle` 收口（鼠标抬起）时跑一次。 |
| 空间复杂度 | O(N)；N=数百~千级时抬起瞬间可感知，但远小于 pathfinding 群体移动热点（见 pathfinding 文档）。 |
| 与 RTactical 哈希关系 | 小地图点绘用的 RTactical（`Radar+0x1258`）**不参与**此处框选。二者枚举源不同。 |

### 4.4 `0x50B6F0` 语义（House 过滤器）

```c
// this = HouseClass*
if ([0xA8B238] != 0)            // 某“严格/观察”全局开关
    return this == PlayerHouse; // 仅本人
return this->+0x1EC || this->+0x1ED;  // IsControlledByPlayer / IsAlliedWithPlayer 类标志
```

即“本地玩家或其盟军可控”。**框选、点选、雷达点绘（radar 文档同址）共用此过滤**，这是“不能点选/框选敌方”的第一道闸。

---

## 5. 命令分发（CommandClass / 快捷键 / 右键）

### 5.1 命令表

- `CommandClass::Array`：DynamicVectorClass @ **0x87F658**（vtable 0x7E182C/0x7E184C）。
  内部：`Items` 0x87F65C，`Capacity` 0x87F660，`Count` 0x87F668，`+0x87F665` 容量可增标志，`+0x87F66C` 增长步长。
- 注册簇 **0x5321xx–0x5334xx**：`operator new` → 写 vtable（如 MultiplayerSync 0x7EBDEC、Follow 0x7EBDC4…）→ `Vector.Add`（0x538780）。每命令构造时常 `push <id>; call 0x535C00`（带数字 ID 的构造器）。
- symbols.json 收录 46 个具体命令（`SetDefenseTabCommandClass`、`DeployCommandClass`、`StopCommandClass`、`SelectTeamCommandClass`、`ToggleSellCommandClass`、`SidebarUp/DownCommandClass`…），v[0..8] 中 **v[8]=Execute**。

### 5.2 侧边栏相关命令示例

`SetDefenseTabCommandClass::Execute`（0x535E50）：

```
if (0x6ABAC0(0x881CC0))            // 命令可用性/焦点检查
    SidebarClass::SetActiveTab(1); // 0x6A7590 → 防御页
    0x7342B0();                    // EVA/音效
    …（可选）发网络事件…
```

同类：`SetInfantryTab/SetUnitTab/SetStructureTab`、`SidebarUp/Down`（滚动 TopRowIndex）、`ToggleRepair/ToggleSell`（改 Display+0x11AC/0x11AD RepairMode/SellMode）。

### 5.3 右键目标如何交给 Techno

**不直接调 Techno**。0x4AB9B0 / 0x4AE750 按 Action 生成 **NetworkEvent**（YRpp `Networking.h` 注释“click-command … TechnoClass::ClickedMission”）：

```
evt = 0x6E6AB0(target);                       // 取事件壳
0x4C65E0(houseIndex, kind, evt) / 0x4C6650 / 0x4C6AE0 / 0x4C6B60
   // kind 已见：1,2,0x12,0x15,0x16,0x17（移动/攻击/部署/维修/占领…）
// 写入环形缓冲：
if ([0xA802C8] < 0x80) {
    memcpy(0xA802D4 + [0xA802D0]*0x73 /*≈115B*/, evt, 0x73);
    [0xA83A54 + [0xA802D0]*4] = 0x7E1530();   // 序号/时间戳
    [0xA802D0] = (old+1) & 0x7F;
    [0xA802C8]++;
}
```

随后网络/逻辑层回放事件，最终落到 `TechnoClass::ClickedMission` / `ReceiveCommand(RadioCommand)`（`ObjectClass::v[169]` 族）。**右键=构造事件，不是同步调用 Techno**。

单选后的指挥分支（0x4AB9B0 内）会调 `0x732D00`（是否已在选择组）/ `0x7327D0` / `0x732600`（选择组增删）/ `obj->v[83]`（Select）/ `obj->v[0x14C]`（ClickedMission 相关）。

### 5.4 快捷键

- 输入环见 `audio_input_hotspots.md`（0x54F000 peek/pump）；按键 → 命令索引 → `CommandClass::Array[i]->v[8] Execute(dwUnk)`。
- `CommandClass` 基类 v[5]/v[6]/v[7]（0x535BD0/BE0/BF0）是可用性谓词（`vt_entry_14/18/1C`），Execute 前先测，故快捷键在菜单/打字时自动失效。
- 具体键位绑定表在 `keyboard.ini` / `ra2md.ini` 的 [Hotkeys] 类段（INI 侧），不在本 exe 常量表中。

---

## 6. 工具提示与 CanBuild

### 6.1 Tooltip

- 缓冲：`SidebarClass::TooltipBuffer` @ **0xB07BC4**（wchar[0x42]）。
- 悬停/绘制：`SidebarClass::v[34]` = **0x6ABD30**（1248B）。读 `0xB0B468…0xB0B510` 逐格状态、`SidebarClass.HideObjectNameInTooltip`（+0x53A4，代码在 0x6A9343 附近），叠 CSF 名称+成本+时间；经 `Drawing::TooltipColor`（0xB0FA1C）画框。
- `GameOptionsClass.Tooltips`（选项）可关。
- 另有 `CCToolTip` / `ToolTipManager`（vtable 0x7F57AC，`Vector<ToolTip*>` 0x7F57C8）做通用对话框提示，与战场侧边栏 tooltip 并行。

### 6.2 CanBuild 每帧扫多少

| 调用点 | 地址 | 频次 |
|---|---|---|
| **Cameo 绘制循环** | 0x6A9540 → 0x6A97D2 `call 0x4F7870` | **每个可见 cameo 槽 1 次**，仅当 `Tab.NeedsRedraw||force` |
| 0x6AA600 | 0x6AA781 | 邻接函数（补建 cameo 时） |
| BuildingClass::v[312] | 0x4456D0 ×4 | 建筑 AI/放置路径 |
| AI 生产 | 0x4FEA60 / 0x4FEEE0 / 0x4FF210 | AI 帧，非 UI |

结论：**UI 侧 CanBuild 与 cameo 数线性，且被 Strip 脏门挡着**；不是每帧扫 75 槽，也不是扫全科技树。`CanBuild` 内部含 `CanExpectToBuild`（前置 BFS，`HouseClass::AllPrerequisitesAvailable`）与 `CountOwned*` 计数，单次不便宜——**优化点是“合并重绘请求”而不是砍 CanBuild 本身**。

`CanBuildResult`：`-1=TemporarilyUnbuildable`（黑 cameo）、`0=Unbuildable`（移除 cameo）、`1=Buildable`。

---

## 7. 与迷雾关系

| 路径 | 迷雾行为 | 证据 |
|---|---|---|
| Cameo 图标 / 灰显 / 建造可用性 | **与视野完全无关** | 0x6A9540 只看 House 状态与科技，不碰 Cell 迷雾 |
| 超武 cameo | 与视野无关（看充能） | 0x6A9936 分支 |
| 小地图单位点 | **fogged 不滤敌方**（原版缺口）；shrouded 才滤 | `radar_minimap_dots.md`：0x655C50 内 `IsShrouded` 0x586360 → 0x50B6F0；`IsFogged` 0x5864A0 仅地形变暗 |
| **战术视口点选敌方** | **shrouded（未探索）：不允许** —— `ProcessClickCoords`（0x692300）中 `IsShrouded(cell)`（0x586360）为真且 `[0xB73550]` 非 0 时置 `outShrouded=1` 并 **跳过“鼠标下对象解析”**（0x6DA380），目标保持空 | 0x692480–0x69250E |
| 同上，fogged（有探索无视野） | **原版不拒绝** —— 0x5865E0 被当作“IsFogged”调用，但**函数体是 `xor al,al; ret 4` 空桩**，该分支永不触发；对象解析照常 | 0x5865E0 dump |
| 框选 | 只收 0x50B6F0（己方/盟军），**与迷雾无关也不会误选敌方** | 0x6DA5C0 / 0x4AC2B0 |
| 点选后 Action | `DecideAction`（0x692610）用 0x50B6F0 ×4 + `ObjectClass::MouseOverObject/Cell` 过滤；敌方可被“看见”时才可能给出 Attack 等 Action | 0x692610 feat |

**迷雾一致性缺口（与 radar 文档同源）**：小地图在 fogged 区仍画敌方点；战术视口在 fogged 区若对象已被绘制（如刚离开视野的残留）仍可点到。两处过滤条件不同（雷达：shrouded 才滤；点选：shrouded 才拒、fogged 不拒），**三态（unseen/fogged/visible）不一致的根因就在这里**。

---

## 8. 性能热点与优化插入点

### 8.1 UI 是否吃渲染帧预算

| 项 | 每帧？ | 量级 | 说明 |
|---|---|---|---|
| `SidebarClass::Draw` 壳 | 是 | 极小 | 字节标志判断 |
| chrome 0x4AED70 | 仅脏时 | 7+ 次 shape blit | 可忽略 |
| **Cameo 条 0x6A9540** | **仅 tab 脏时** | 可见槽 × (CanBuild + GetTechnoType + SHP blit) | 生产/金钱抖动时是 UI 主成本 |
| **电力+雷达 0x63FB20 → 0x653100** | **是（每帧）** | 小地图全格重算（radar 文档） | **UI 侧真正固定热点** |
| tooltip 0x6ABD30 | 悬停才画 | 文本 + 框 | 低 |
| 框选 0x6DA5C0 | 仅 LMB 抬起 | O(N) 全扫 0xB0CEC8 | 一次性，N 大时抬起卡一下 |
| 命令 Execute | 事件驱动 | 单次状态变更 | 低 |

**结论**：UI 不是世界 Draw_It 的预算黑洞；侧边栏固定成本几乎全在雷达小地图链（已在 radar 文档单列）。Cameo 的 CanBuild 只在重绘时按槽付费。

### 8.2 优化插入点（不改 exe 的 hook 面）

1. **Cameo 绘制入口 `0x6A9540`**：已有 `AllowedToDraw/NeedsRedraw` 双门，可在门前加“几何未变且仅 Progress 动画”增量——只重画进度条帧，不重跑 CanBuild。
2. **`HouseClass::CanBuild` 调用点 0x6A97D2**：把结果按 `CameoDataStruct` 缓存，仅当 `Money/Prereq/BuildLimit` 变化时失效（这三项是仅有的输入）。
3. **框选 0x6DA5C0**：对 0xB0CEC8 建粗粒度格/屏幕分块索引；或在 `DraggingRectangle` 期间增量维护矩形候选集（放下时只测候选）。
4. **`0x6A6C30` 末尾 0xB0B518 聚合**：若只需局部 present，可按脏字节簇拆矩形，避免整条侧边栏翻页（与 dirty_rect 文档同思路）。
5. **雷达链 0x63FB20**：见 `radar_minimap_dots.md` §5（fog 过滤与限频）。
6. **命令缓冲 0xA802C8 环**：0x80 上限已在，压力点是回放端（pathfinding 群体移动，见 pathfinding 文档），不在命令打包。

### 8.3 与 v1.5.2 结论的差异/确认

- 确认：`SidebarClass::v[16]=0x6A6C30` 为侧边栏整帧协调（含雷达区调用 0x63FB20）。
- 修正/细化：Cameo **不是**每帧全量重绘——tab 级脏门是真实存在的；每帧固定的是雷达小地图。
- 修正：框选**不是**“全图扫 Techno 数组”，而是扫 `0xB0CEC8` 扁平条目数组；与小地图 RTactical 哈希无关。
- 修正：fogged 点选拒绝逻辑在 1.001 里是**空桩**（0x5865E0），只有 shrouded 真正拦截。

---

## 9. 关键地址速查

| 用途 | 地址 |
|---|---|
| SidebarClass::Draw | 0x6A6C30 |
| Cameo 条绘制 | 0x6A9540 |
| RepaintSidebar / AddCameo / SetActiveTab | 0x6A60A0 / 0x6A6300 / 0x6A7590 |
| GetObjectTabIdx | 0x6ABC60 / 0x6ABCD0 |
| Cameo 排序 SortsBefore | 0x6A8420 |
| Cameo 点击（生产） | 0x6AAD00（SelectClass v[31]） |
| SW cameo 分支 | 0x6A9936 |
| CanBuild | 0x4F7870 |
| tooltip / 悬停 | 0x6ABD30；缓冲 0xB07BC4 |
| LMBUp 点选/框选收口 | 0x4AB9B0 |
| 框选矩形遍历 | 0x6D9FF0 → 0x6DA5C0 |
| ProcessClickCoords / DecideAction | 0x692300 / 0x692610 |
| IsShrouded / “IsFogged”桩 | 0x586360 / 0x5865E0（stub） |
| House 可控过滤 | 0x50B6F0 |
| NetworkEvent 构造 | 0x4C65E0 / 0x4C6650 / 0x4C6AE0 / 0x4C6B60 |
| CommandClass::Array | 0x87F658 |
| 命令注册簇 | 0x5321xx–0x5334xx |
| SetDefenseTab Execute | 0x535E50 |
| WWMouseClass / MouseClass Instance | 0x887640 / 0x87F7E8 |
| 电力+雷达链 | 0x63FB20 → 0x653100 → …（radar 文档） |

---

## 10. 静态取证方式

```
python out/reverse/asm.py feat 0x006A6C30
python out/reverse/asm.py dump 0x004AB9B0 0x004AC2B0
python out/reverse/asm.py who  0x004F7870
# vtable 归属：out/reverse/symbols.json（SelectClass@StripClass@SidebarClass 等）
# 字段位移：raw-byte 扫 0x11CC..0x11E4 得 DraggingRectangle=0x11CF 等 9 处引用
```
