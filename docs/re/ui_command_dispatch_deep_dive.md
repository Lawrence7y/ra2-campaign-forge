# UI 命令分发深潜（点选 / 框选 / 命令分发 / 确定性 / 优化面）

> 任务：**R-UI-CMD** · 逆向对象 `gamemd.exe` 1.001（YR，ImageBase `0x400000`，`FileOffset = VA − 0x400000`）
> 【W3 勘误 E-W3-01】原句 `FileOffset = VA − 0x400000` 仅在 `.text/.rdata/.data` 成立；
> 通用式为 `FileOffset = 段.PointerToRawData + (VA − 段.VirtualAddress)`，
> 本镜像 `.rsrc`/`.detour` 为 `VA − 0x6FC000`。依据：out/re_work/_lead_baseline/W3/LEAD_ERRATUM_E-W3-01_fileoffset_rule.md；分级：[实证]
> 性质：**纯逆向结论 + 可落地规格**，不含已应用补丁。
> 证据三档：`[实证]` / `[推演]` / `[待实测]`（`docs/re/EVIDENCE_STANDARD.md` v3）。
> 关联：`sidebar_selection_ui.md`（侧栏/点选/命令分发前序深潜）、`sw_charge_state_deep_dive.md`（T16 充能钩）、
> `dirty_rect_l4.md`（L4）、`net_sync_checksum.md`（NetworkEvent/确定性）、`trigger_determinism_deep_dive.md`（T8 VIOLATION）、
> `re_sprint_S14_report.md`（输入环 0x54F050 / WWMouse）、`radar_minimap_dots.md`、`shroud_click_interaction.md`。
> 本波次工作包：`out/re_work/re_sprint/R_ui_cmd/`（claims / 状态机 / 优化规格 / 兼容矩阵 / FINDINGS）。
>
> **取证备注**：本波次执行面 bash 只读被权限拦截，**未重跑 capstone**。文中 `[实证]` 均溯源到
> 已过 `tools/audit_bytes.py` 的既有 claims（主锚 `out/re_work/atlas_rev/R8/claims_R8.txt` 179/179 OK、
> `re_sprint_S14_report.md` 字节、`sw_charge_state_deep_dive.md` 字节）；新增交叉断言标 `[推演]`。

---

## 0. 一页结论

| 问题 | 结论 |
|---|---|
| 状态机 | **三段式**：① 本地输入层（InputRing/WWMouse/DisplayClass/Sidebar gadget）→ ② 事件化边界（`FillEvent_*` → NetworkEvent 本地环）→ ③ 锁步仿真（`Dispatcher 0x4C6CB0` → `ClickedMission` / `StartProduction`）。主收口 `DisplayClass::LMBUp 0x4AB9B0`。 |
| WWMouse `0x887640` | **`WWMouseClass*` 单例**。只做光标合成、Capture/Release、屏幕→客户区换算（`v[0x44]`）、`SetCoords`（`v[0x38]`）；**不做点选逻辑**。点选在同一大对象 `0x87F7E8` 的 DisplayClass/MouseClass 接口。**[实证]** |
| 点选/框选 | 框选 = `DraggingRectangle(+0x11CF)` 收口时 `0x6DA5C0` 对 **`0xB0CEC8` 12B 扁平数组 O(N) 全扫**（非 TechnoArray、非 RTactical）。过滤：House 闸 `0x50B6F0` + v[78] + 建筑特判 + v[83]；**无迷雾**。单选走 `ProcessClickCoords 0x692300` → `DecideAction 0x692610`。 |
| 命令分发 | `CommandClass::Array 0x87F658`（46 子类）→ v[8] Execute。**勘误**：基类 v[8] = `0x4C9150` 抽象默认桩，勿按基类虚表挂钩。**Execute 直调 FillEvent = 0**；同步经 handler 间接（Alliance/Stop）或经 Action/Cameo 路径事件化。Produce FillEvent 9 站点全在侧栏。 |
| 本地输入是否进同步流 | **输入事件本身不进**；只有「命令语义」经 NetworkEvent 进流。对照 T8：`SelectedByPlayer`/`PickupCrate*` 读**本地锁存位**才构成 VIOLATION。UI 打包前单向门控安全；解包层加门控 = Desync。 |
| UI 优化 | 7 条规格：P0 删冗余 `GetCameoChargeState`；主推 **Tab 脏合并/重绘限频**；`0x6A99AC` 读 `+0x78` 缓存（= T16-6.2）；CanBuild 槽缓存；present 矩形拆分；框选分块；fogged 点选门控。 |
| L4 / 充能钩 | **正交**（写表面分离）。L4=`0x6D3D99` tactical 全量刷；侧栏=`DSurface::Sidebar 0x887300` + `0xB0B518`；充能只读 `+0x78`。OPT-1 与 T16-6.2 同点需协调；禁改 `0x6CBEE0` 公式。 |

---

## 1. 类层次 · 单例 · WWMouse 身份交叉

### 1.1 拓扑

```
IGameMap → GScreenClass → MapClass → DisplayClass → RadarClass → PowerClass
    → SidebarClass → TabClass → ScrollClass → MouseClass
                 └── 单一物理实例 0x87F7E8

TacticalClass*        0x887324   视口几何 / 0xB0CEC8 枚举源计数 (Tactical+0xDB0)
WWMouseClass*         0x887640   光标合成 / 捕获 / 坐标换算          ← 本任务交叉点
InputManagerClass*    0x87F770   输入环 ring[256]
CommandClass::Array   0x87F658   命令表
```

### 1.2 WWMouse 交叉定谳 **[实证]**

| 锚 | 字节 / 引用 | 语义 |
|---|---|---|
| 单例槽 | `0x887640` | YRpp `WWMouseClass.h:13` `reference<WWMouseClass*, 0x887640u>` |
| 载入点 | `0x53E7B6 = 8B 0D 40 76 88 00` | `mov ecx, [0x887640]` |
| 换算虚调 | `0x53E7CE = FF 50 44` | `call [eax+0x44]` ScreenToClient/视口换算 |
| 落点虚调 | `0x53E827 = FF 52 38` | `call [edx+0x38]` `SetCoords` |
| 构造 | `0x5BDDB0`（CreateInstance） | 与 vtable `0x7F7B2C` 归属 |
| xref 量 | 文本绝对引用 ×266 | `va_claims_sample_p2.md` |

**职责边界**：
- ✅ 光标 SHP 合成/擦除、`CaptureMouse/ReleaseMouse`、坐标换算、光标逻辑位置。
- ❌ 点选判定、框选枚举、Action 决策、NetworkEvent 构造。
- `MouseClass::v[19]=0x5BDC80` 仅在 Cameo 点击后**换光标**（引用 `0x82D028` 光标表）。

> 与 `open_items_sweep.md` A-4 闭环一致：「`[0x887640]` 是西木基础类库单例 `WWMouseClass::Instance`」。
> 与 `sidebar_selection_ui.md` §4.1 一致：「只做光标合成/捕获；不做点选逻辑」。

---

## 2. 输入环状态机（0x54F050）

### 2.1 采集链 **[实证]**

```
USER32!PeekMessageA  ──(正常对局 [0xAA0444]!=2 直通 0x53EB01)──┐
                                                               ▼
InputManagerClass::WndProc 0x54F790
   ├─ [0x887640]->v[0x44]   屏幕→客户区
   ├─ [0x887640]->v[0x38]   SetCoords
   └─ PushWord 0x54F1C0 / 0x54F670
        → ring[256] @ this+0x114
        → head +0x314 / tail +0x318   （满环 PushWord 返回 0 = 丢弃）
```

### 2.2 出队解码 `GetEvent 0x54F050` **[实证]**

| 类型码 | 分支 | 消费 word | 展开 |
|---|---|---|---|
| 1 / 2 / 4 | 鼠标类 | **3**（EventCode+Mods, X, Y） | `this+0x00/04/08` |
| 0xA | 字符类 | **2**（EventCode, CharCode） | `this+0x08` |
| 其它 | 标准键 | **1** | — |

修饰键 OR 进 EventCode 高位：`0x100` Shift / `0x200` Ctrl / `0x400` Alt。

字节锚（S14）：
```
0x54F0F0  and ecx, 0xFF
0x54F0F6  cmp cx, 1 / 4 / 2   → 鼠标支（3 word）
0x54F17A  cmp cx, 0xA         → 字符支（2 word）
```

**未决 U-RUICMD-2**：类型码**语义命名**两材料冲突（`open_items_sweep.md` 称 1=LDown/2=LUp/4=Move/5=RDown/6=RUp；
S14 注释称 1/2/4 = L/M/R 同支）。字节只保证「1/2/4 同走鼠标坐标展开」。改队列编码前必须穷举。

---

## 3. 点选 / 框选主状态机（0x4AB9B0）

### 3.1 状态变量

| 变量 | 位置 | 含义 |
|---|---|---|
| `CurrentBuilding` | Display+0x11A4 | 建筑放置模式 |
| `DraggingRectangle` | Display+0x11CF | 框选拖拽中 |
| 拖拽附带 | +0x11D0/11D4/11D8/11DC/11E0 | `v[45]=0x4AC310` 成批清 |
| 矩形角点 | 0x88098C/90/94 | 暂存 |
| 选择组 | `0x732D00` / `0x7327D0` / `0x732600` | 增删查 |

### 3.2 转移图

```
S_IDLE
  │ LMBDown 0x4AC380
  ├─ CurrentBuilding≠0 ──► S_PLACE（放置/取消）
  ├─ 拖拽 ──► S_DRAGGING (DraggingRectangle=1)
  │              │ LMBUp
  │              ▼
  │         S_BOX_SELECT
  │           0x6D9FF0 → 0x6DA5C0  O(N) 扫 0xB0CEC8
  │           回调 0x4AC2B0
  │           0x70D150 清/推选择集
  │              │
  └─ 单击 ──► ProcessClickCoords 0x692300
                │ IsShrouded 0x586360 ?
                │  是 → 跳过 GetObjectAt（目标空）
                │  否 → GetObjectAt 0x6DA380
                ▼
              DecideAction 0x692610
                │
                ▼
              S_SELECTED / Action switch
                ├─ 0    纯选择        v[78] / v[83]
                ├─ 8    指挥          0x732D00 / 0x7327D0 / v[0x14C]
                ├─ 0x3D 路径点
                ├─ 0x21/3C/0A/0D/0C 维修/贩卖/部署/…
                ▼
              S_EVENT_PACK
                FillEvent_* → NetworkEvent 环
                ▼
              S_REPLAY（按 Timestamp）
                Dispatcher 0x4C6CB0 → ClickedMission / Place / Produce
```

### 3.3 框选枚举 `0x6DA5C0` **[实证]**

```
[0x822CF2] = 1
for i in 0 .. Tactical+0xDB0:          # ★ O(N)，非空间哈希
    e = [0xB0CEC8][i]                  # 12B {Object*, x, y}
    if (!e.obj || !e.obj+0x90) continue
    矩形 4 次 int 比较
    if (0x732D00(obj)) { 0x7327D0(...); continue }   # 已在选择组
    if (callback) { callback(obj); continue }
    House = obj->v[15]()               # GetOwningHouse
    if (!0x50B6F0(House)) continue     # ★ 敌方 100% 剔除
    if (!obj->v[78]()) continue
    建筑特判 WhatAmI==6
    if (!obj->v[83]()) continue        # Select()
    [0x822CF2] = 0
```

- **不是** `TechnoClass::Array`，**不是** RTactical（后者只服务小地图点绘）。
- **无迷雾判定**。
- 仅 LMB 抬起时一次，非每帧。

### 3.4 迷雾点击三态 **[实证]**

| 状态 | 点选行为 | 锚 |
|---|---|---|
| Shrouded | 跳过对象解析，目标空；只能地面移动 | `0x692480 → 0x6924FC` |
| Fogged | **原版不拒绝**（空桩 `0x5865E0 = 32 C0 C2 04 00`） | `0x6924DF` |
| Clear | 正常 | `0x692515` |
| 变卖 · Shrouded | 强制 `Action::NoSell (0x0E)` | `0x692A70 → 0x692AFE` |
| 变卖 · Fogged | 仍给 `Sell (0x0C)` | `0x692A87` |

三处过滤口径不一致（小地图 shrouded 才滤 / 点选 shrouded 才拒 / 框选不看迷雾）→ **三态漂移唯一根因**。

---

## 4. 命令分发

### 4.1 快捷键 → CommandClass

```
GetEvent(Key)
  → 命令索引（keyboard.ini / ra2md.ini [Hotkeys]，INI 侧）
  → CommandClass::Array 0x87F658
  → 谓词 v[5]/v[6]/v[7] = 0x535BD0/BE0/BF0   （菜单/打字自动失效）
  → v[8] Execute(dwUnk)
```

**勘误 [实证]**：基类 `CommandClass 0x7EBE3C` 的 v[8] 槽 `0x7EBE5C` = **`0x4C9150` 抽象默认桩**。
Execute 实体在 **46 个具体子类**各自虚表。
⇒ Hook 面必须是「子类实例虚表 + v[8]」；按基类虚表基址挂钩会命中所有未覆写子类默认路径（高危误伤）。

### 4.2 侧栏命令族

| 命令 | Execute | 效果 | 进同步流 |
|---|---|---|---|
| SetDefenseTab | `0x535E50` | `SetActiveTab(1)` + EVA | 否（纯 tab）[实证] |
| SetInfantry/Unit/StructureTab | 同族 | ActiveTabIndex | 否 [实证] |
| SidebarUp/Down | 同族 | TopRowIndex | 否 [实证] |
| **ToggleRepair / ToggleSell** | `0x536FA0` / `0x537020` | `call 0x4AC8C0` / `0x4AC660`（Display 模式位） | **否**（纯本地）[实证] |
| SelectTeam / AddTeam / CenterView… | 各子类 | 本地选择/视口 | 否 [实证] |
| **Alliance** | `0x536F20` → `0x7318F0` | 结盟 | **是（间接）** `FillEvent_PlayerBased` @ `0x73188A/99C` [实证] |
| **Stop** | `0x536B80` → `0x730EA0` | 停止 | **是（间接）** `FillEvent_Noopt` @ `0x730F6C` [实证] |
| Deploy / Guard / Scatter… | → `0x730AFx` | 对象虚调 | **间接**（深度 U-7）[待实测] |

**普查 [实证]**：46 个 `CommandClass::Execute` + 基类桩 `0x4C9150`，前 `0x120` 字节内
**0 处直调 FillEvent / 事件壳**。同步只经下游 handler **间接**发生。

### 4.2b FillEvent 全镜像直调点普查 **[实证]**

| FillEvent | n | 站点 | 归属 |
|---|---|---|---|
| `0x4C65E0` 通用 | 7 | `0x4AC187`… | 点选 Action |
| `0x4C6650` SellCell | 1 | `0x4AC1B2` | 变卖 |
| `0x4C66C0` Noopt | 10 | 含 `0x730F6C` | 开关 |
| `0x4C6720` PlayerBased | 7 | 含 `0x73188A/99C` | 结盟/选项 |
| `0x4C6780` Waypoints | 5 | `0x639577`… | 路径点 |
| `0x4C6800` Animation | 0 | — | — |
| **`0x4C6970` Produce\*** | **9** | **全在 `0x6AA7E7…0x6AB76E`（侧栏）** | ★Cameo 生产唯一源 |
| `0x4C6AE0` Place | 3 | `0x4ABB55` / `0x6A8EE8` / `0x6AB3FC` | 放置 |
| `0x4C6B60` SWPlace | 2 | `0x4AC23A` / `0x6AAF3C` | 超武落点 |
| `0x4C6CB0` Dispatcher | 2 | `0x64C911` / `0x64CC0A` | 回放 |

### 4.3 「右键 = 事件化」契约 **[实证]**

```
Action → FillEvent_*
   0x4C65E0  通用 / MegaMission / Repair…
   0x4C6650  SellCell
   0x4C6970  ProduceAbandonSuspend   ← 侧栏 0x6AAD00 / 0x6AA600
   0x4C6AE0  Place
   0x4C6B60  SWPlace
   0x4C6BE0  SWPlace 变体
→ 环: 计数 0xA802C8(上限0x80) / 写指针 0xA802D0(&0x7F) / 体 0xA802D4 / 序号 0xA83A54
→ Dispatcher 0x4C6CB0   跳表 0x4C8114（Kind−1）
→ handler → TechnoClass::ClickedMission (v[297] @+0x4A4)
          / FactoryClass::StartProduction (v[0x94])
          / Place handler 0x4C70E1
```

**解包链 `0x4C71CA → 0x4C73AA` 全程无迷雾校验** ⇒ 纯客户端改本地黑幕不产生即时 Desync；
只有单边改逻辑状态（写 Cell 探索位进 CRC）才在 FrameSync 爆 OOS。

### 4.4 侧栏 Cameo 生产子状态机

```
Click Cameo  SelectClass@Strip v[31] = 0x6AAD00
  → FillEvent_ProduceAbandonSuspend 0x4C6970
      Kind 0x0E Produce / 0x0F Suspend / 0x10 Abandon
  → 入环 → 回放 handler 0x4C711B / 0x4C7140 / 0x4C7163
  → FactoryClass::DemandProduction / StartProduction
  → 出兵时 Place (Kind 0x0B, handler 0x4C70E1)
```

超武 cameo（ItemType=0x1F，分支 `0x6A9936`）不查 CanBuild，走 `SuperClass` 充能；
发射 `SpecialPlace` Kind 0x12。

---

## 5. 确定性：本地输入 vs 同步流（对照 T8）

### 5.1 切分

| 通道 | 进同步？ | 证据 |
|---|---|---|
| 鼠标移动 / 光标 / WWMouse | **否** | [实证] 停在 InputRing |
| GetEvent 解码 / 原始 WM_* | **否** | [实证] |
| 选择集 0x732600 等 | **否**（但被 T8 0x21 消费） | [实证]+[推演] |
| Tab / 滚动 / tooltip / ToggleRepair·Sell 模式位 | **否** | [实证] D2 |
| CommandClass::Execute **直调** FillEvent | **否（0 处）** | [实证] D2 普查 |
| Action（移动/攻击/维修/贩卖/部署…） | **是** | [实证] FillEvent |
| 侧栏 Produce/Suspend/Abandon | **是** | [实证] 0x4C6970 ×9 全侧栏 |
| Place / SWPlace | **是** | [实证] 0x4C6AE0 / 0x4C6B60 |
| Alliance / Stop 等命令 | **是（间接）** | [实证] D3 |

### 5.2 对照 T8 VIOLATION

T8（`trigger_determinism_deep_dive.md` §2.1 / `R_trig_det/risk_table.md` #1）：

> `SelectedByPlayer(0x21)` / `EnemyInSpotlight(0x23)` / `PickupCrate*(0x31/0x32)` /
> `DiscoveredByPlayer(0x04)` 依赖本机交互/可见性。轮询器读锁存位
> `[Scenario+0x34BE]`(crate) / `0x34AA`(global/local set) 若由**本地动作**置位，
> 条件求值结果多端天然分叉。**VIOLATION**

| | 命令流（本任务） | T8 触发器事件 |
|---|---|---|
| 入口 | FillEvent → NetworkEvent 环 | 每帧轮询器本地求值 |
| 多端 | **一致**（同序回放） | **分叉**（本地锁存） |
| 点选的角色 | 选择集本地；**衍生命令**才同步 | `SelectedByPlayer` **直接读本地选择集** |
| 改造红线 | 禁在解包层单边加门控 | 禁改求值序/次数 |

**核心洞察 [推演·高置信]**：
1. **本地输入事件本身不进同步流** —— 命令语义才进。
2. ⇒ **UI 打包前单向门控安全**（广播合法替代包，如 NoSell）。
3. ⇒ **触发器把本地 UI 状态当条件输入**，才是 T8 根因（不是「有 UI」，而是「UI 状态被逻辑条件读取且未同步」）。
4. 修复方向：此类事件改由已同步命令/逻辑帧副作用置位，或 MP 下广播锁存。
5. **UI 优化不得把应进流的命令变成本地短路**，否则制造新 VIOLATION。

### 5.3 确定性矩阵

| ID | 点 | 判定 | 等级 |
|---|---|---|---|
| U1 | InputRing / GetEvent / WWMouse | SAFE | [实证] |
| U2 | 选择集（本地） | SAFE 本身；被 0x21 读 → 间接 VIOLATION | [实证]+[推演] |
| U3 | Action → FillEvent → 环 | SAFE（序/次数不可单端变） | [实证] |
| U4 | Produce 0x0E–0x10 | SAFE（出兵帧/序不可变） | [实证] |
| U5 | Place / SWPlace | SAFE | [实证] |
| U6 | 解包层 0x4C71CA 加门控 | **RISK** = Desync | [实证] |
| U7 | 打包层单向 UI 门控 | SAFE | [实证]+[推演] |
| U8 | CommandClass 基类 v[8] hook | **RISK** 误伤 | [实证] |
| U9 | 事件体 stride 0x73 vs 0x73B | **RISK** 口径不一 | [待实测] |
| U10 | ToggleRepair/Sell 模式位 | SAFE（Execute 纯本地） | [实证] |
| U11 | CommandClass Execute 直调 FillEvent | SAFE（0 处） | [实证] |
| U12 | Alliance/Stop 间接 FillEvent | SAFE（不可单端变序） | [实证] |
| U13 | Deploy/Guard 间接深度 | **RISK** 未穷举 | [待实测] |

---

## 6. 每帧成本与可落地 UI 优化

### 6.1 成本表

| 项 | 每帧？ | 量级 |
|---|---|---|
| `SidebarClass::Draw 0x6A6C30` 壳 | 是 | 极小 |
| chrome `0x4AED70` | 仅脏时 | 7+ blit |
| **Cameo `0x6A9540`** | **仅 tab 脏** | 可见槽 × (CanBuild + GetTechnoType + SHP) |
| SW 充能 `0x6A99AC` | 仅 SW 槽绘制时 | 2×fild/fmul/fdiv |
| 电力+雷达 `0x63FB20` | **是** | 小地图全格（radar 文档） |
| 框选 `0x6DA5C0` | 仅 LMB 抬起 | O(N) |
| 命令 Execute | 事件驱动 | 低 |

### 6.2 规格摘要（详 `out/re_work/re_sprint/R_ui_cmd/ui_opt_spec.md`）

| ID | 名称 | 挂载 | 优先级 | 确定性 |
|---|---|---|---|---|
| OPT-2 | 删冗余二次 `GetCameoChargeState` | `0x6CBE88` | **P0** | SAFE |
| OPT-4 | **Tab 脏合并 / 重绘限频** | `0x6A9540` 门前 | **P1 主推** | SAFE |
| OPT-1 | SW 充能帧读 `+0x78` 缓存 | `0x6A99AC` | P1 | SAFE（= T16-6.2） |
| OPT-7 | fogged 点选门控（替换空桩） | `0x6924DF` / `0x692A87` | P1 正确性 | SAFE（表现层） |
| OPT-3 | CanBuild 槽缓存 | `0x6A97D2` | P1 | SAFE |
| OPT-5 | present 矩形拆分 | `0xB0B518` | P2 | SAFE |
| OPT-6 | 框选 0xB0CEC8 分块 | `0x6DA5C0` | P2 | RISK（须同构） |

**OPT-4 建议参数**：`MIN_SIDEBAR_REDRAW_GAP = 2~4` 逻辑帧；`onlyProgressChanged` 分支须覆盖
CameoDataStruct.Progress **与 SW charge frame**（否则充能条卡住）。

**禁止清单**：改 `0x6CBEE0` 公式 / 写 `+0x78` / 解包层加门控 / 基类 v[8] 挂钩 /
改 InputRing 编码 / 框选源换 RTactical / Produce·Place 本地短路。

---

## 7. 与 L4 / 侧栏充能钩兼容

### 7.1 三通道正交 **[实证]**

| 通道 | 写表面 | 补丁/钩点 |
|---|---|---|
| L4 世界视口 | tactical（脏矩形 `0xB0CE78`） | **`0x6D3D99`** jge→jmp |
| 侧栏 chrome/Cameo | `DSurface::Sidebar 0x887300` + `0xB0B518` | `0x6A6C30` / `0x6A9540` |
| 超武充能显示 | 逻辑 `+0x78` → UI 叠图 | `0x6A99AC` → `0x6CBEE0` |

侧栏**不进世界脏矩形队列**；L4 全量刷与侧栏优化无字节交集。

### 7.2 兼容矩阵

| 改动 | 写 +0x78？ | 改 0x6CBEE0？ | 碰 0x6A99AC？ | 与 T16 钩 | 判定 |
|---|---|---|---|---|---|
| T16-6.1 删 e2 | 否 | 否 | 否 | 无 | ✅ |
| T16-6.2 / OPT-1 读缓存 | 否 | 否 | **是** | **同点** | ⚠ 协调 |
| OPT-4 限频 | 否 | 否 | 否（门前） | 无，减少调用 | ✅ |
| 改充能公式 | **是** | **是** | — | 破坏红线 | ❌ |

**协调约定**：OPT-1 ≡ T16-6.2，勿重复实现；`+0x78` 写侧只属逻辑（进 `CalculateChecksum v[13]=0x6CE020`）；
超武槽不查 CanBuild，OPT-3 不覆盖。

### 7.3 与 L4 模式

`L4FullRedraw` / `visual-dirty` / `full-skip-tiles` / `fog-layer` **均可与侧栏优化共存**。
唯一语义交集：迷雾三态谓词应与 OPT-7 / 雷达点绘统一到 `CellClass::IsVisibleToHouse 0x4870D0`。

---

## 8. 关键 VA 速查

| VA | 名称 | 等级 |
|---|---|---|
| 0x54F000 / **0x54F050** / 0x54F1C0 | InputMgr Peek / **GetEvent** / PushWord | [实证] |
| 0x54F790 | InputManagerClass::WndProc | [实证] |
| **0x887640** | WWMouseClass::Instance | [实证] |
| 0x87F770 | InputManagerClass::Instance | [实证] |
| 0x87F7E8 | Map/Display/Radar/Power/Sidebar/Mouse 共用实例 | [实证] |
| **0x4AB9B0** | DisplayClass::LMBUp 点选/框选收口 | [实证] |
| 0x4AC380 / 0x4AC310 | LMBDown / 清拖拽 | [实证] |
| **0x6DA5C0** | ForEachInRect（0xB0CEC8 O(N)） | [实证] |
| 0xB0CEC8 / Tactical+0xDB0 | 框选枚举源数组 / 计数 | [实证] |
| 0x692300 / 0x692610 | ProcessClickCoords / DecideAction | [实证] |
| 0x586360 / **0x5865E0** | IsShrouded / **fogged 空桩** | [实证] |
| 0x50B6F0 | House 控制权闸（217 直调） | [实证] |
| **0x6AAD00** | SelectClass@Strip Cameo 生产 | [实证] |
| 0x4F7870 | HouseClass::CanBuild（UI 侧 2 直调） | [实证] |
| **0x4C6970** | FillEvent_ProduceAbandonSuspend | [实证] |
| 0x4C65E0/6650/6AE0/6B60 | FillEvent 族 | [实证] |
| **0x4C6CB0 / 0x4C8114** | Dispatcher / Kind 跳表 | [实证] |
| 0xA802C8 / 2D0 / 2D4 | NetworkEvent 本地环 | [实证] |
| 0x87F658 | CommandClass::Array | [实证] |
| 0x535E50 | SetDefenseTabCommandClass::Execute | [实证] |
| **0x6A99AC → 0x6CBEE0** | 侧栏充能绘点 GetCameoChargeState | [实证] |
| 0x6CBE7E / 0x6CBE8A | 逻辑路径 e1 / 冗余 e2 | [实证] |
| **0x6D3D99** | L4 补丁点 | [实证] |
| 0x887300 / 0xB0B518 | DSurface::Sidebar / present 聚合 | [实证] |

---

## 9. 未决与后续

| ID | 项 | 等级 | 建议 |
|---|---|---|---|
| U-RUICMD-1 | NetworkEvent 事件体 stride 0x73 vs 0x73B | [待实测] | 对照 YRpp `NetworkEvents.h` + 单条 dump 定谳 |
| U-RUICMD-2 | GetEvent 类型码语义命名（含 5/6 右键） | [待实测] | 补 `0x54F050`–`0x54F2C0` 全量类型表 |
| ~~U-RUICMD-3~~ | ToggleRepair/Sell **已定谳纯本地** | [实证] | 残留：模式位多端读取 |
| U-RUICMD-4 | SetActiveTab 间接 FillEvent | [待实测] | xref 0x6A7590 下游 |
| U-RUICMD-5 | `0x6AAD00 → 0x4C6970` 调用链 | [待实测] | 逐指令展开（9 站点已锁侧栏） |
| U-RUICMD-6 | A/B 组断言补 audit 复算 | [待实测] | `tools/audit_bytes.py` |
| U-RUICMD-7 | Deploy/Guard handler 间接同步深度 | [待实测] | 对象虚调追踪 |

---

## 10. 静态取证方式（供后续波次）

```
python out/reverse/asm.py feat 0x004AB9B0
python out/reverse/asm.py dump 0x0054F050 0x006AAD00
python out/reverse/asm.py who  0x004C6970
# vtable：out/reverse/symbols.json
# 本包 claims：out/re_work/re_sprint/R_ui_cmd/claims_ui_cmd.txt
# 复算：tools/audit_bytes.py（A 组已 179/179）
```

---

## 11. 工作包索引

| 文件 | 内容 |
|---|---|
| `out/re_work/re_sprint/R_ui_cmd/claims_ui_cmd.txt` | 机器可读字节/地址断言（A/B/C 溯源） |
| `out/re_work/re_sprint/R_ui_cmd/state_machine.md` | 完整状态机 + WWMouse 交叉 + 确定性切面 |
| `out/re_work/re_sprint/R_ui_cmd/ui_opt_spec.md` | 7 条优化/修复规格 + 禁止清单 |
| `out/re_work/re_sprint/R_ui_cmd/compat_l4_charge.md` | L4 / 充能钩兼容矩阵 |
| `out/re_work/re_sprint/R_ui_cmd/FINDINGS.md` | 一页结论与未决 |
