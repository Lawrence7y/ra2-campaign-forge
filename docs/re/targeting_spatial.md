# 寻敌 / 威胁评估数据结构与空间哈希插入点

> 逆向对象：`gamemd.exe` 1.001（尤里的复仇），ImageBase=`0x400000`，文件偏移 = VA − `0x400000`
> 【W3 勘误 E-W3-01】原句 `FileOffset = VA − 0x400000` 仅在 `.text/.rdata/.data` 成立；
> 通用式为 `FileOffset = 段.PointerToRawData + (VA − 段.VirtualAddress)`，
> 本镜像 `.rsrc`/`.detour` 为 `VA − 0x6FC000`。依据：out/re_work/_lead_baseline/W3/LEAD_ERRATUM_E-W3-01_fileoffset_rule.md；分级：[实证]
> 目标：为 L2「8 帧哈希节流」之后的空间哈希邻域查询提供数据结构与最小侵入插入点。
> 产出配套反汇编：`out/reverse/fn_6FB010_SelectAutoTarget.txt`、`fn_6FB080_SelectAutoTarget_impl.txt`、`fn_6F8DF0_GreatestThreat.txt`、`fn_6F7CA0_helper.txt`、`fn_6F8960.txt`、`fn_412B40.txt` 等。

---

## 0. 结论速览

| 问题 | 答案 |
| :--- | :--- |
| `SelectAutoTarget` 是不是 O(N²) 扫描体？ | **不是**。它只是 **限频调度器**（0x70 字节），负责推进 `this+0x2FC` 扫描计数与 `this+0x1FC` 定时器，真正扫描体在 `Greatest_Threat`。 |
| `Greatest_Threat` 从哪里枚举候选？ | **三路**：① 全局粗粒度空间桶对象 `0x00887888`（20×20 桶）；② 以武器射程为半径的 **逐格螺旋 + CellClass 链表**；③ 某些 TargetFlags 分支下 **全局 Aircraft/其他数组线性扫描**。 |
| 过滤条件？ | House 结盟位图（`HouseClass+0x5788`）、`Health/EstimatedHealth`、`InLimbo`、`TargetFlags` 类型位、`WhatAmI`、武器威胁值、若干 `TechnoTypeClass` 布尔位。 |
| 打分方式？ | 单候选评估函数 `0x006F7CA0` 写出威胁分，主函数按 **严格大于** 保留最高分（`[esp+0x1C]`=分数，`[esp+0x20]`=目标）。 |
| 空间哈希最小侵入点？ | **首选**：替换/增强全局桶对象 `0x00887888` 的填充逻辑（`0x00412B40`）；**次选**：inline hook `0x006F8DF0` 入口做邻域预过滤短接（比挂虚表更全）；**第三**：只替换螺旋枚举源。 |
| 与 Target Retention 兼容？ | 逻辑兼容——Retention 只依赖 `+0x5D4` 目标指针与 `+0x6C` 血量。但 **现网 `InstallVTableHooks` 漏装 Greatest_Threat 两个虚表槽**，且 Infantry/Building/Aircraft/Foot 各有独立 v[241] 入口——必须改为 hook `0x006F8DF0` 本体才能全覆盖。 |

---

## 1. 调用图与函数身份

### 1.1 虚表与覆盖关系（symbols.json + 实机虚表字节双重验证）

**v[241] `Greatest_Threat` —— 每个具体类各有一份入口，最终汇到 `0x006F8DF0`：**

| 类 | 虚表基址 | v[241] 入口 | 与 `0x006F8DF0` 的关系 |
| :--- | :--- | :--- | :--- |
| TechnoClass | `0x007F4960` | **`0x006F8DF0`** | 扫描本体 |
| FootClass | `0x007E8C94` | `0x004D9920` | 薄包装（+0x688 标志）→ 调 `0x006F8DF0` |
| AircraftClass | `0x007E22A4` | `0x004D9920` | 同上（与 Foot 共享） |
| UnitClass | `0x007F5C70` | `0x00743190` | TargetFlags 预处理 → `0x004D9920` → `0x006F8DF0` |
| InfantryClass | `0x007EB058` | **`0x0051E140`** | **快路径**：若 `Owner->+0x54E0`（House 级共享目标）存在且距离 < `0xF00` leptons（15 cell），**直接返回该目标**，完全不进 `0x006F8DF0`；否则补 flags 后走基类 |
| BuildingClass | `0x007E3EBC` | **`0x00445F00`** | 独立包装器，尾部 `call 0x006F8DF0`（0x00445F68） |

**v[265] `SelectAutoTarget`：**

| 类 | v[265] 入口 | 说明 |
| :--- | :--- | :--- |
| Techno / Foot / Infantry / Building / Aircraft | **`0x006FB010`** | 共享调度器 |
| UnitClass | `0x00736CA0` | 前置检查后回落 `0x006FB010` |

### 1.2 真实调用链

```
虚调用 v[265] SelectAutoTarget
 ├─ 0x00736CA0  UnitClass 覆盖（写 +0x1FC..+0x204 定时器后调基类）
 │    └─ 0x006FB010  TechnoClass::SelectAutoTarget   ← 限频调度器
 │         ├─ 虚调用 v[73] = 0x006F4A70（arg=2）      ← 计数耗尽时的动作
 │         └─ 0x006FB080  定时器/周期更新
 └─ 0x006FB010  同上（Foot/Infantry/Building/Aircraft 共享）

虚调用 v[241] Greatest_Threat（各类包装器）
 ├─ 0x00743190  Unit（flags 预处理）
 ├─ 0x004D9920  Foot/Aircraft（+0x688 标志）
 ├─ 0x0051E140  Infantry（独立包装）
 ├─ 0x00445F00  Building（独立包装，0x445F68 直 call）
 │    └─（全部最终）0x006F8DF0  TechnoClass::Greatest_Threat ← 真正扫描体
 │         ├─ 0x00412B40 / 0x004137A0   全局空间桶枚举器 0x00887888
 │         ├─ 0x005657A0                MapClass::TryGetCellAt
 │         ├─ 0x00568300                MapClass::IsCellInMap（菱形边界）
 │         ├─ 0x006F8960                逐格链表扫描（内部再调 0x006F7CA0）
 │         ├─ 0x006F7CA0                单候选过滤 + 打分（最重）
 │         ├─ 0x006F8960 / 0x006F8C10   逐格最优候选
 │         └─ 0x004F9A50 / 0x004F9A90   HouseClass::IsAlliedWith

其它直接 call：
 └─ 0x00701B62（TechnoClass::v[91] 0x00701900 内）→ 0x006FB080   ← SelectAutoTarget 的第二条触发路径
 └─ 0x0051E39F → 0x004D9920（Infantry 侧）
```

### 1.3 ⚠ 现网 L2 hook 覆盖缺口（与 `blitter_hooks.cpp` 对照）

`InstallVTableHooks()`（`blitter_hooks.cpp:970`）目前实际安装的是：

| 已安装 | 虚表槽 | Hook |
| :--- | :--- | :--- |
| ✅ | `ADDR_VTABLE_ENTRY_TECHNO_AUTO_TARGET` `0x007F4D84` | `Hook_Techno_SelectAutoTarget` |
| ✅ | `ADDR_VTABLE_ENTRY_UNIT_AUTO_TARGET` `0x007F6094` | `Hook_Unit_SelectAutoTarget` |
| ❌ **未安装** | `ADDR_VTABLE_ENTRY_TECHNO_GREATEST_THREAT` `0x007F4D24` | `Hook_Techno_Greatest_Threat`（函数体已写好，Remove 里有还原，但 **Install 中缺失对应 PatchVTablePointer**） |
| ❌ **未安装** | `ADDR_VTABLE_ENTRY_UNIT_GREATEST_THREAT` `0x007F6034` | `Hook_Unit_Greatest_Threat`（同上） |

即便补装这两个槽，也只覆盖 **Techno + Unit** 两张虚表；`InfantryClass / BuildingClass / AircraftClass / FootClass` 各自的 v[241] 入口（`0x51E140 / 0x445F00 / 0x4D9920`）**不会被改写**。同理 v[265]：这四类的虚表项仍指向 `0x006FB010` 本体，只有 Techno/Unit 两张表被 hook。

**推论：空间哈希与 Target Retention 都不应继续挂在「逐类虚表」上，应挂在共享扫描体 `0x006F8DF0` 入口（inline hook）或枚举源 `0x00887888` 上，才能对全体单位生效。**

### 1.4 签名

```cpp
// v[265]：无栈参，__thiscall，ret（不带弹栈）
void __thiscall TechnoClass_SelectAutoTarget(TechnoClass* this);

// v[241]：3 个 DWORD 栈参，ret 0xC（callee 清栈）
AbstractClass* __thiscall TechnoClass_Greatest_Threat(
    TechnoClass* this,
    uint32_t     targetFlags,   // [esp+0x70] = TargetFlags 位域
    CoordStruct* pCenter,       // [esp+0x74] 指向 leptons 坐标，内部 >>8 转 cell
    int          arg3           // [esp+0x78] 传入 0x00B0EA90 之类的标志/句柄
);
// 返回值 = 最优目标 AbstractClass*（存于 [esp+0x20]），无目标返回 0
```

YRpp `TechnoClass.h:262` 把返回值标成 `CellClass*`，与实机不符——实机返回的是目标对象指针（与 `this+0x5D4 = Target` 同型）。以汇编为准。

---

## 2. `SelectAutoTarget`（0x006FB010）— 限频调度器

### 2.1 汇编骨架

```asm
006FB010  push esi / push edi
          call [this->v + 0x84]          ; v[33] GetType（基类为桩，派生类返回真实类型）
          mov  eax, [type + 0x684]       ; 扫描预算（-1 表示禁止）
          cmp  eax, -1 / je  exit
          mov  edi, [this + 0x2FC]       ; 扫描计数器
          cmp  edi, eax / jge  exit      ; 预算用尽
          mov  edx, [this + 0x1FC]       ; 定时器 StartTime（-1 = 未启动）
          mov  eax, [this + 0x204]       ; 定时器 Duration
          ; —— 到期判定：CurrentFrame(0x00A8ED84) - StartTime >= Duration ——
          ; 未到期则直接 return
          inc  edi
          mov  [this + 0x2FC], edi
          push 2
          call [this->v + 0x124]         ; v[73] = 0x006F4A70
          call 0x006FB080                ; 重算下一周期
006FB06E  pop edi / pop esi / ret
```

### 2.2 周期更新（0x006FB080）

| 条件 | 写入 `this+0x1FC..+0x204` |
| :--- | :--- |
| `type+0x69C != -1` 且计数器==0 | `{CurrentFrame, 局部, type+0x69C}`（固定周期） |
| 否则 | `Duration = type+0x698 + type+0x6A0 * k²`，其中 `k = max(1, this+0x2FC / type+0x3E4)` |

含义：**扫描越频繁、后续间隔按计数器平方拉长**——原版自带的退避。`this+0x1FC` 一带即 YRpp 的 `TimerStruct ReloadTimer`（`unknown_bool_1F8` 之后）。

### 2.3 对空间哈希的含义

- L2 的 8 帧哈希节流作用在 **调度器** 上，跳过的是「推进计数 + 触发 v[73]」，而不是 `Greatest_Threat` 本体；
- 真正吃 CPU 的 `Greatest_Threat` 由 **其他调用方**（AI/开火/守卫）直接/间接驱动，因此单纯节流 `SelectAutoTarget` 收益有限；
- **空间哈希必须做在 `Greatest_Threat` 的候选枚举层**，而不是再包一层 `SelectAutoTarget`。

---

## 3. `Greatest_Threat`（0x006F8DF0）主循环

函数体量 `0xFC0`（约 1255 条指令）。栈上关键局部变量（函数序言 `sub esp,0x5c` + 4 个 push）：

| 栈槽 | 含义 |
| :--- | :--- |
| `[esp+0x14]` | 中间 TargetFlags（由入参 flags 重映射，如 `0x8042`） |
| `[esp+0x1C]` | **当前最高威胁分** |
| `[esp+0x20]` | **当前最优目标指针**（返回值） |
| `[esp+0x38]` | **搜索半径（cell）** |
| `[esp+0x44..]` | 中心 `CellStruct`（由 `pCenter` leptons >>8 得到） |
| `[esp+0x70]` | 入参 `targetFlags` |
| `[esp+0x58]` | 中心 CellStruct 备份 |

### 3.1 前置过滤（0x6F8DF0–0x6F8FE8）

1. 全局 `0x00A8EC34` 自增（**重入计数**）。
2. `type+0xD20` 为真且 `0x0050B730(this->Owner)` 为真 → **返回 null**（阵营已被判定「不扫描」）。
   - `0x0050B730`：读全局 `0x00A8B238`（非 0 直接过）+ `House+0x1EC / +0x1ED`（House 失败/淘汰状态）。
3. `arg1 bit0` 为 0 且 `WhatAmI ∉ {2=Unit, 6=Aircraft}` → 走「取自身格 + Map 查询」分支（`0x0056D230`，`this=MapClass::Instance 0x0087F7E8`）。
4. `WhatAmI == 0xF`（Building）或 `== 1`（Infantry）时用 `0x006F3970`（武器威力均值）微调 flags。
5. 按 `TargetFlags` 重映射出 `[esp+0x14]`（含 `0x8002/0x4008/0x4010/0x40/0x8000/0x2` 等位）。
6. `type+0x6B0`（对应 YRpp **`DistributedFire`**）为真 → **清空** `this+0x458`（`CurrentTargets`）与 `this+0x440`（`AttackedTargets`）两个向量。
7. `flags & 3 == 0` → 跳过前两路枚举，直进 0x6F9B6E 的数组扫描。

### 3.2 搜索半径

```
radius = ( GetWeaponRange() >> 8 ) + ( type+0x68C >> 8 ) + 1
; 若 vcall v[256] 为真（精英/特殊武器路径）：
radius = Rules->+0xF48 + vcall v[257]() + 1
```

`GetWeaponRange` = vcall v[90] `0x007012C0`。半径存 `[esp+0x38]`，是 **螺旋圈数上限**。

### 3.3 三路候选枚举

#### 路 A：全局空间桶枚举器 `0x00887888`（**原版自带的粗空间哈希！**）

```asm
006F91B7  lea  edx, [esp+0x58]          ; &center CellStruct
006F91BB  push [esp+0x38]               ; radius
006F91BC  push edx
006F91BD  mov  ecx, 0x87F7E8            ; MapClass::Instance
006F91C8  call 0x005657A0               ; TryGetCellAt(&cell) → CellClass*
006F91CD  push eax                      ; pCell
006F91CE  mov  ecx, 0x887888            ; ★ 空间桶单例
006F91D3  call 0x00412B40               ; InitQuery(pCell, radius)
006F91DD  mov  ecx, 0x887888
006F91DD  call 0x004137A0               ; Next() → 候选指针
loop:                                   ; 0x6F91EC
          ; ……过滤 + 0x6F7CA0 打分……
          call 0x004137A0               ; 下一个
          test ebp, ebp
          jne  loop                     ; 0x6F9385
```

`0x00412B40` 内部（摘要）：

- 由 `MapClass+0x12C / +0x130` 做 **除 10（magic `0x66666667`）** 的桶坐标换算，**各维 clamp 到 0..19**；
- 桶索引 `= bx + by * 20`，每桶 **24 字节**（vptr + 计数 + 取第 i 项的虚函数）；
- 把桶内对象 **物化** 到 `0x887888+0x2580` 处的 `DynamicVectorClass`；
- `0x004137A0` 从该向量 **无序弹出**（swap-with-last 风格）。

> 这是引擎内部现成的 **20×20 粗空间哈希**。粒度太粗（一桶 ≈ 一张 100×100 地图上的 5×5 或更大区域），但仍把「全图 N 个对象」缩到「桶 + 邻桶」。

#### 路 B：逐格螺旋 + CellClass 链表（射程内精确扫描）

```asm
; 半径 > 0 时进入，双层环形迭代
006F93C1  ring = 0 .. radius
006F93DE  for dx in [-ring, +ring]:          ; 第一维
006F93E2      cell = center + (dx, dy)
006F9404      mov  ecx, 0x87F7E8            ; MapClass::Instance
006F940E      call 0x00568300               ; IsCellInMap(cell) → bool
006F9415      je   next_cell
006F9440      call 0x006F8960               ; ★ 逐格扫描（见下）
006F9572      call 0x006F8C10               ; 次级候选（无最优目标时的 fallback）
… 006F974B  jle 0x6F93DE                    ; 内环
… 006F976D  for dy in ...:                  ; 第二维（对称的另一半环）
… 006F9ADC  jl  0x6F976D
```

`0x006F8960`（逐格对象扫描，0x2B0 字节）：

```asm
ebx = MapClass::TryGetCellAt(cell)           ; 0x5657A0
edi = [cell + 0xE8]                          ; CellClass 对象链头（空则用 +0xE4）
loop:
    if edi == this: skip
    test byte [edi+0x14], 1                  ; 对象有效位
    ; 过滤：House 结盟、type 布尔、Focus/护送逻辑……
    call 0x006F7CA0                          ; 单候选打分
    edi = [edi + 0x30]                       ; ★ ObjectClass::NextObject
    test edi / jne loop
```

**链表结构（YRpp 对照）**：

| 偏移 | YRpp 字段 | 用途 |
| :--- | :--- | :--- |
| `ObjectClass+0x30` | `NextObject` | 同格对象链表 |
| `CellClass+0xE4` | `FirstObject` | 链头（地面层） |
| `CellClass+0xE8` | `AltObject`（桥面等） | 优先取桥面链头 |

#### 路 C：全局数组线性扫描（flags 特定分支）

`flags & 3 == 0` 或进入 `0x6F9B6E` 后：

```asm
006F9B7E  mov  eax, [0x00A8E3A0]            ; 计数
006F9B8D  mov  edx, [0x00A8E394]            ; Items（Aircraft 向量）
          ; 逐项：结盟过滤 → 0x6F7CA0 打分 → 维护最优
006F9D93  mov  eax, [0x00A8EC88]            ; 另一个全局计数
006F9D9B  jl   0x6F9C7A                     ; 第二段数组扫描
006F9DA1  mov  eax, [esp+0x20]              ; ★ 返回最优目标
          ret 0xC
```

`0x00A8E390` 为 Aircraft 全局向量基址（项目 `ADDR_ARRAY_AIRCRAFT`），`+4`=Items、`+0x10`=Count（VectorClass **带 vptr**）。

### 3.4 打分与「严格大于」择优

单候选评估 `0x006F7CA0`（0xCC0 字节）输出 `bool`，并经出参写回威胁分。主循环侧：

```asm
006F9363  mov  eax, [esp+0x74]              ; 本候选分
          mov  ecx, [esp+0x1C]              ; 当前最高分
          cmp  eax, ecx
          jle  skip                         ; ★ 只接受严格更高分
          mov  [esp+0x20], ebp              ; 更新最优目标
          mov  [esp+0x1C], eax              ; 更新最高分
```

**并列时保留先被枚举到的候选** → 枚举顺序影响结果。替换枚举源时 **必须保持相同的枚举序**（或验证回放一致），否则开火目标会在同分敌人之间漂移。

`0x006F7CA0` 内部过滤要点（候选 `esi`）：

| 条件 | 汇编位置 | 说明 |
| :--- | :--- | :--- |
| `esi != null` | 0x6F7D88 | |
| `[esi+0x81] == 0` | 0x6F7D90 | `InLimbo`（死亡中/删除中） |
| `[esi+0x6C] != 0` | 0x6F7D9E | `Health` |
| `[esi+0x3D5] == 1` | 0x6F7DF1 | 「可被选为目标」标志 |
| `HouseClass::IsAlliedWith` | 0x6F7F22 → 0x4F9A90 | 见下 |
| `0x006F3970` 威胁值 | 0x6F7F36 | 无武器且非特例则淘汰 |
| `type+0x5E4` 等 | 0x6F7EBA | 免疫/伪装/不可选 |
| `Rules+0x16F8` 距离阈值 | 0x6F7F56 | 浮点比较 |
| `this+0x11C`（Focus/护送） | 0x6F7EA2 | 与候选 Owner 做结盟排除 |

---

## 4. 字段对照表

### 4.1 ObjectClass / TechnoClass（实例）

| 偏移 | 含义 | 依据 |
| :--- | :--- | :--- |
| `+0x14` bit0 | 对象有效/在图标志 | 逐格扫描 `test byte [edi+0x14],1` |
| `+0x30` | `NextObject` 同格链表 | YRpp `ObjectClass.h:267` + 0x6F8B3E |
| `+0x6C` | `Health` | YRpp + Target Retention 已用 |
| `+0x70` | `EstimatedHealth`（寻敌威胁估计用） | YRpp + 0x6F7CF7 |
| `+0x81` | `InLimbo` | YRpp + 0x6F7D90 |
| `+0x94` | 当前 Mission（2 = Hunt/Attack 类） | 0x6F9D13 |
| `+0x9C / +0xA0 / +0xA4` | `Location`（leptons） | `GetCoords` v[18]=0x5F65A0 读 `this+0x9C` |
| `+0xAC` | 某类型索引（比较 0x19/0x5/0xB） | 0x6F8FFB / 0x6F9030 |
| `+0x11C` | `Focus`（守卫/护送目标） | 0x6F8FA8 |
| `+0x1FC` | 扫描定时器 StartTime | SelectAutoTarget |
| `+0x200` | 定时器中间字段 | 0x6FB0DB |
| `+0x204` | 定时器 Duration | SelectAutoTarget |
| `+0x21C` | **`Owner`（HouseClass*）** | 0x6F8E29 / 0x4F9A90 |
| `+0x298` | 布尔（伪装/渗透中，排除目标） | 0x6F9218 |
| `+0x2FC` | 扫描计数器 | SelectAutoTarget |
| `+0x418` | `unknown_bool_418` | v[73] 0x6F4A81 |
| `+0x440` | **`AttackedTargets`**（DistributedFire 用） | 0x6F8F90 / 0x6F9318 |
| `+0x458` | **`CurrentTargets`**（DVC） | 0x6F8F8A / 0x6F92D1 |
| `+0x520` | `SpawnManager*` | 0x6F8B25 |
| `+0x5D4` | **`Target`（当前目标）** | 项目已用 |
| `+0x688` | Aircraft 包装器标志 | 0x4D9923 |
| `+0x6C0` | `TechnoTypeClass*`（缓存类型） | 0x6F8EEB 读 `[type+0xEC3]` |
| `+0x6C4` | 亦为类型指针（项目迷雾代码用 `type+0x5E8`=Sight） | `blitter_hooks.cpp:608` |

> `+0x6C0 / +0x6C4` 都被当作类型对象使用；`GetType` v[33]/v[34] 在基类是桩，派生类直接返回其中一个字段。使用 `+0x6C4` 与现网迷雾代码保持一致即可。

### 4.2 TechnoTypeClass（类型）

| 偏移 | 含义 | 依据 |
| :--- | :--- | :--- |
| `+0x394` | ==2 时的特殊淘汰条件 | 0x6F7D0D |
| `+0x3E4` | 扫描退避除数 | 0x6FB116 `idiv` |
| `+0x5B4` | 传给 Map 高度/层级查询 | 0x6F8EAE |
| `+0x5E4` | 目标免疫/不可选位 | 0x6F8FBF |
| `+0x5E8` | `Sight`（视距） | 迷雾代码已用 |
| `+0x684` | **扫描预算**（-1=禁） | 0x6FB01C |
| `+0x68C` | 射程附加（leptons） | 0x6F912E |
| `+0x698` | 周期基数 | 0x6FB13E |
| `+0x69C` | 固定周期（-1=用公式） | 0x6FB0B0 |
| `+0x6A0` | 周期二次项系数 | 0x6FB128 |
| `+0x6B0` | **`DistributedFire`** | 0x6F8F80；YRpp `TechnoTypeClass.h:328` |
| `+0x6C0` | 布尔（跳过某些过滤） | 0x6F920E |
| `+0xD20` | 布尔（配合 House 状态整体禁扫） | 0x6F8E1F |
| `+0xE12` | Unit 包装器禁扫位 | 0x7431A8 |
| `+0xEC3` | 布尔（Building 特例） | 0x6F8EF1 |

### 4.3 HouseClass

| 偏移 | 含义 | 依据 |
| :--- | :--- | :--- |
| `+0x30` | `ArrayIndex` | 0x4F9A63 |
| `+0x1EC / +0x1ED` | 失败/淘汰/观察者状态 | 0x50B730 |
| `+0x5600` | 当前 Team/编组相关索引 | 0x6F9284 |
| `+0x54E0` | **House 级共享攻击目标**（Infantry 快路径） | 0x51E174 |
| `+0x5788` | **`Allies` 结盟位图**（`1 << idx`） | 0x4F9A7E |
| `+0x577A` | `SpySatActive` | 迷雾文档已用 |

### 4.4 House 关系判定函数

| 地址 | YRpp 声明 | 语义 |
| :--- | :--- | :--- |
| `0x004F9A10` | `IsAlliedWith(int idxHouse)` | 同 idx 或位图 |
| `0x004F9A50` | `IsAlliedWith(HouseClass*)` | 同上 + 空指针 |
| `0x004F9A90` | `IsAlliedWith(ObjectClass*)` | 先 `GetOwner` v[15] 再判结盟 |

**敌我 = 结盟位图取反**。寻敌循环里 `IsAlliedWith==true` 时走「特例才保留」分支，`false` 才当常规敌人。

### 4.5 MapClass / 全局

| 地址 | 含义 |
| :--- | :--- |
| `0x0087F7E8` | `MapClass::Instance`（亦为 DisplayClass/GScreenClass 大单例） |
| `MapClass+0x13C` | `CellClass**` 格子数组（512×512，索引 `(y<<9)+x`） |
| `MapClass+0xF4 / +0xF8` | 菱形地图边界（`IsCellInMap`） |
| `0x005657A0` | `TryGetCellAt(CellStruct*)` → `CellClass*`（越界给哑元 `0x00ABDC50`） |
| `0x00568300` | `IsCellInMap(CellStruct*)` → bool |
| `0x008871E0` | `RulesClass::Instance` |
| `0x00887888` | **全局 20×20 空间桶枚举器**（Init `0x412B40` / Next `0x4137A0`） |
| `0x00A8EC34` | `Greatest_Threat` 重入计数 |
| `0x00A8ED84` | `CurrentFrame` |
| `0x00B0EA52` | 螺旋早退阈值（与环坐标比较） |
| `0x00B0EA90` | 传入 `0x6F7CA0` 的常量标志 |
| `0x00A8E394 / 0x00A8E3A0` | Aircraft 向量 Items / Count |
| `0x00A8EC88` | 路 C 第二段数组计数 |
| `0x00A8B238` | 非 0 时 `0x50B730` 直接判真（战局结束/特殊状态） |

---

## 5. 空间哈希插入点方案对比

### 方案 S1：增强/替换全局桶枚举器（推荐）

| 项 | 内容 |
| :--- | :--- |
| **插入点** | `0x00412B40`（InitQuery）入口挂 hook，或直接替换 `0x00887888` 对象的填充逻辑 |
| **做法** | 自建 **per-cell 或 2×2 cell 粒度** 的哈希表（512×512 可压成 `hash = (x*73856093) ^ (y*19349663)` 桶）；每 **N 帧**（建议 N=4~8，与 `TargetScanInterval` 对齐）全量重建一次；`0x412B40` 时只把 **半径内桶** 的对象指针灌进原有 `+0x2580` 向量，**保持 0x4137A0 弹出接口不变** |
| **优点** | ① 调用方零改动（路 A 自动加速）；② 弹出顺序可控（按桶、格、链表序，可复刻原序）；③ 与 `Greatest_Threat` 解耦，可单测 |
| **缺点** | 路 B（逐格螺旋）仍在，只优化了一部分；需要在对象创建/销毁/换格时增量维护或整表重建 |
| **确定性** | 高——只要重建时机是「逻辑帧确定」且枚举序固定 |

**建议数据结构**：

```cpp
// cell 粒度哈希（推荐 1 cell = 1 桶，查询时扩 1 圈）
struct SpatialHash {
    // 512x512 直接寻址也行（262144 * 4B = 1MB）；或 2^15 桶 + 链式
    uint32_t head[512 * 512];        // 单元首对象索引，0xFFFFFFFF 空
    uint32_t next[MAX_OBJECTS];      // NextObject 风格的并行数组
    AbstractClass* items[MAX_OBJECTS];
    uint32_t frameStamp;             // 重建帧号
    void Rebuild(int currentFrame);  // 每 N 帧一次，遍历 Units/Infantry/Aircraft/Buildings 四个全局向量
    void Query(CellStruct c, int r, auto&& out); // 环形扩圈，命中即停
};
```

重建成本：O(N) 一次，摊到 N 帧 → 每帧 O(1) 摊销；查询 O(命中数 + 环面积)。

### 方案 S2：`Greatest_Threat` 入口邻域预过滤短接

| 项 | 内容 |
| :--- | :--- |
| **插入点** | **inline hook `0x006F8DF0` 函数入口**（推荐——覆盖全部包装器路径）；或现有 `Hook_Techno/Unit_Greatest_Threat`（需先补装虚表槽，且仍漏 Infantry/Building/Aircraft/Foot） |
| **做法** | 在调用原函数前，用空间哈希在 `(center, radius)` 内取候选 → 若候选集为空 **直接返回 Retention 目标或 null**；若非空，把候选集写进一个线程本地列表，再让原函数只扫这个列表 |
| **优点** | 改动集中在现有 hook 文件；短路时收益最大（800 单位对峙图上大量空转） |
| **缺点** | 原函数内部仍是三路枚举，短路不掉时收益有限；「只扫预过滤列表」需要再 hook 枚举源（退化为 S1） |
| **确定性** | 中——短路条件必须与原函数的「找不到目标」语义逐位等价，否则会改变开火时机 |

### 方案 S3：只替换路 B 螺旋枚举源

| 项 | 内容 |
| :--- | :--- |
| **插入点** | `0x006F8960` 入口（逐格扫描）或螺旋环迭代器（`0x6F93DE` / `0x6F976D`） |
| **做法** | 螺旋只负责算格子；把「格 → 对象链表」换成「格 → 哈希桶」 |
| **优点** | 精确控制最内层热点；不影响路 A/C |
| **缺点** | 侵入二进制较深（需 patch 环体或劫持 `0x6F8960` 的链表头）；对 `CellClass` 桥面/`AltObject` 语义要复刻 |
| **确定性** | 中高——保持「环序 + 每格链表序」即可 |

### 对比表

| 维度 | S1 增强全局桶 | S2 入口短接 | S3 替换螺旋 |
| :--- | :--- | :--- | :--- |
| 侵入面 | 1 个数据对象 + 1 个填充函数 | 现有 hook 内 | 螺旋内层 |
| 加速范围 | 路 A | 空转短路 + 可选全量 | 路 B |
| 保留语义难度 | 低 | 高（短路等价性） | 中 |
| 与 L2 节流叠加 | 佳 | 佳 | 佳 |
| 推荐优先级 | **P0** | P1 | P2 |

**推荐落地顺序**：先 S1（把 `0x00887888` 的桶改成 cell 粒度并 N 帧重建）→ 再 S2 空集短路 → 视 profile 决定 S3。

---

## 6. 必须保持的行为（风险点）

### 6.1 联机 / 回放确定性

1. **枚举顺序敏感**：择优用 `>`（严格大于），同分保留先到者。任何替换必须复刻：
   - 路 A：`0x887888` 桶 → 桶内索引 → 弹出顺序（swap-with-last 本身会改顺序，但同一帧内一致）；
   - 路 B：环半径递增 + 环上固定起始角 + `CellClass` 链表头到尾；
   - 路 C：数组下标递增。
2. **重建时机必须是逻辑帧号的纯函数**（例如 `frame % N == 0`），禁止用渲染帧、线程时间、指针哈希乱序。
3. **禁止引入浮点不确定**：`Rules+0x16F8` 等浮点比较保持原样。
4. **`0x00A8EC34` 重入计数**、`0x00B0EA52` 早退阈值不要改语义。

### 6.2 目标保持与开火优先级

1. **已有目标保持**：现网 `Hook_*_Greatest_Threat` 在节流帧返回 `Target`（`+0x5D4`）当且仅当 `Health>0`。空间哈希不能把「有目标且存活」的单位改成返回 null。
2. **打分语义不变**：`0x6F7CA0` 的威胁分构成（`EstimatedHealth`、武器威力 `0x6F3970`、距离阈值、类型特例）不得改。
3. **DistributedFire 副作用**：`type+0x6B0` 为真时必须继续 **清空并回填** `this+0x440`（`AttackedTargets`）与 `this+0x458`（`CurrentTargets`），否则分布式开火会重复打同一目标或漏打。
4. **`Focus`/护送排除**（`this+0x11C`）与 **`+0x298` 伪装排除** 保持。
5. **各类 v[241] 包装器语义不一**：
   - Infantry `0x51E140` 有 **House 级共享目标快路径**（`Owner+0x54E0` 距离 <15 cell 直接返回），完全绕过 `0x006F8DF0`——空间哈希对这条路径无效，但也不需要（它本就 O(1)）；
   - Building `0x445F00` / Unit `0x743190` 只做 TargetFlags 合成后调基类；
   - Foot/Aircraft `0x4D9920` 处理 `+0x688` 标志后调基类。
   只 hook Techno/Unit 两张虚表时 Infantry/Building/Aircraft/Foot 均不受影响；且 `InstallVTableHooks` 当前 **根本没装** Greatest_Threat 两个槽。空间哈希/Retention 应改为 **inline hook `0x006F8DF0` 函数入口**（对所有进入扫描体的路径生效），或 hook 枚举源 `0x00887888`。

### 6.3 TargetFlags 语义

`TargetFlags`（YRpp `GeneralDefinitions.h:1296`）在函数内被重映射为 `[esp+0x14]`（`0x8042` 等）。改枚举源时 **不要** 顺手「整理」这些位，`0x6F7CA0` 与后续分支按位测试。

---

## 7. 与 ra2render 现有 Target Retention 的兼容性

### 7.1 现网行为（`blitter_hooks.cpp:344-443`）

| Hook | 行为 |
| :--- | :--- |
| `Hook_Techno/Unit_SelectAutoTarget` | `(unitHash + frame) % TargetScanInterval != 0` → 直接 return（不调原函数） |
| `Hook_Techno/Unit_Greatest_Threat` | 仅当 `Target(+0x5D4) != null && Health(+0x6C) > 0` 且命中节流帧 → **返回旧目标**；否则调原函数 |

### 7.2 兼容矩阵

| 场景 | 兼容性 | 说明 |
| :--- | :--- | :--- |
| S1/S2/S3 + 节流帧返回旧目标 | **兼容** | 哈希只改变「原函数内部枚举」，Retention 在 hook 层短接 |
| 节流帧且旧目标已死 | **兼容** | 现网会落到原函数 → 哈希加速本次扫描 |
| 节流帧且从未有目标 | **兼容** | 原函数（哈希路径）正常跑 |
| SelectAutoTarget 完全跳过 | **注意** | 跳过的是调度器，`Greatest_Threat` 仍会被 AI 调用——哈希仍生效 |
| Infantry / Building / Aircraft / Foot | **现网有缺口** | 它们各自 v[241] 入口（`0x51E140/0x445F00/0x4D9920`）未被 hook；`InstallVTableHooks` 也漏装了 Techno/Unit 的 Greatest_Threat 槽。空间哈希应 **inline hook `0x006F8DF0`** 才能全覆盖 |
| DistributedFire 单位 | **兼容（前提）** | 哈希路径必须仍调用原 `0x6F7CA0` / 向量回填，不能只返回预过滤列表的头 |
| 回放对拍 | **必须做** | 建议在 `Greatest_Threat` 返回后把 `(this, ret, frame)` 落日志，与未打补丁回放对齐 |

### 7.3 推荐的组合策略

1. **先补洞**：在 `InstallVTableHooks` 补上 `GREATEST_THREAT` 两个槽（或更好——直接 inline hook `0x006F8DF0` 入口，绕开逐类虚表覆盖不全问题）；
2. **保留** 现有 8 帧哈希节流（`TargetScanInterval`）作为粗粒度平抑；
3. **叠加** S1 空间哈希：把 `0x00887888` 的桶细化为 cell 粒度、每 `TargetScanInterval` 帧重建；
4. **叠加** S2 空集短路：半径内无敌 → 返回 Retention 目标或 null（与原函数找不到目标时一致）；
5. **回归**：`0x6F7CA0` 打分、`0x440/0x458` 向量、严格大于择优全部走原函数，不做内联重写。

这样节流砍次数、哈希砍单次枚举量，且 Target Retention 的「绝不丢锁」原则不变。

---

## 8. 附：关键地址速查

| 角色 | 地址 | 备注 |
| :--- | :--- | :--- |
| TechnoClass::SelectAutoTarget | `0x006FB010` | v[265]，调度器 |
| SelectAutoTarget 周期更新 | `0x006FB080` | |
| TechnoClass::Greatest_Threat | `0x006F8DF0` | v[241]，扫描体 `ret 0xC` |
| UnitClass::Greatest_Threat | `0x00743190` | flags 预处理 → `0x004D9920` |
| Aircraft 包装器 | `0x004D9920` | → `0x006F8DF0` |
| 单候选评估 | `0x006F7CA0` | 过滤 + 打分 |
| 逐格链表扫描 | `0x006F8960` | |
| 空间桶 Init/Next | `0x00412B40` / `0x004137A0` | 对象 `0x00887888` |
| MapClass::TryGetCellAt | `0x005657A0` | |
| MapClass::IsCellInMap | `0x00568300` | |
| HouseClass::IsAlliedWith | `0x004F9A50` / `0x004F9A90` | |
| BuildingClass::Greatest_Threat | `0x00445F00` | v[241]，尾部 0x445F68 调 `0x006F8DF0` |
| InfantryClass::Greatest_Threat | `0x0051E140` | v[241]；快路径直返 `Owner+0x54E0` |
| v[73] 动作 | `0x006F4A70` | SelectAutoTarget 触发 |
| TechnoClass vtable | `0x007F4960` | v[241]=`0x007F4D24`，v[265]=`0x007F4D84` |
| UnitClass vtable | `0x007F5C70` | v[241]=`0x007F6034`，v[265]=`0x007F6094` |
| 文件偏移 | VA − `0x400000` | 例：`0x006F8DF0` → `0x2F8DF0` |
> 【W3 勘误 E-W3-01】原句 `FileOffset = VA − 0x400000` 仅在 `.text/.rdata/.data` 成立；
> 通用式为 `FileOffset = 段.PointerToRawData + (VA − 段.VirtualAddress)`，
> 本镜像 `.rsrc`/`.detour` 为 `VA − 0x6FC000`。依据：out/re_work/_lead_baseline/W3/LEAD_ERRATUM_E-W3-01_fileoffset_rule.md；分级：[实证]

---

## 9. 遗留待确认

1. `0x00887888` 桶内对象集合的 **来源**（是「最近受击者」还是「全部 Techno」）——决定 S1 重建时是全量灌还是增量灌。`0x412B40` 里 6 组 `0x4129C0/0x412A40` 像是按 6 个对象类型/层分别收集，建议下轮动态断点确认。
2. `0x006F4A70`（v[73]）在 `SelectAutoTarget` 中 `push 2` 的确切语义（`Mission=2` 还是 `WeaponIndex=2`）。
3. `this+0x6C0` 与 `+0x6C4` 是否为同一 `TechnoTypeClass*` 的双写（迷雾用 `+0x6C4`，GT 用 `+0x6C0`）——不影响空间哈希落地。
4. 螺旋早退全局 `0x00B0EA52` 的配置来源（是否随 `Target` 数量动态调整）。
