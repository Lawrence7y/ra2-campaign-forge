# 《红色警戒2：尤里的复仇》（gamemd.exe 1.001）弹道抛物线与微粒系统迷雾剔除深度逆向报告

> **目标二进制**：`gamemd.exe` 1.001（尤里的复仇），ImageBase = `0x00400000`。  
> **核心模块**：`BulletClass::Draw`（`0x00468090`，虚表槽 69 @ `0x007E47F8`）、`ParticleClass::Draw`（`0x0062CEC0`，虚表槽 69 @ `0x007EFA68`）、`ParticleSystemClass::Draw`（`0x0062E280`，虚表槽 69 @ `0x007EFCB0`）。  
> **任务目标**：彻底堵住敌军弹药在迷雾中的视觉泄露（如黑雾中飞出的 V3 火箭、无畏级导弹、基洛夫炸弹与尾迹烟雾），设计零侵入、零同步风险的智能视觉剔除方案。

---

## 1. 架构总览与视觉泄露根因剖析

### 1.1 弹药与微粒渲染链架构

在原版引擎中，渲染管线是由战术视图主循环（`TacticalClass::Render` / `DisplayClass::Draw_It`）按图层遍历各类对象链表，并统一通过虚表偏移 `+0x114`（即虚函数槽 69：`ObjectClass::Draw`）进行多态调用的：

```
+----------------------------------------------------------------------------------------------------+
|                                    战术视图主循环 (TacticalClass::Render)                          |
|                                   遍历世界对象链表，逐对象分发 Draw                                |
+-------------------------------------------------+--------------------------------------------------+
                                                  |
                                                  v  call [esi + 0x114] (槽 69)
         +----------------------------------------+----------------------------------------+
         |                                        |                                        |
         v                                        v                                        v
+-------------------------------+  +-------------------------------+  +--------------------------------+
|    BulletClass::Draw          |  |   ParticleClass::Draw         |  |   ParticleSystemClass::Draw    |
|    VA: 0x00468090             |  |   VA: 0x0062CEC0              |  |   VA: 0x0062E280               |
|    虚表: 0x007E46E4           |  |   虚表: 0x007EF954            |  |   虚表: 0x007EFB9C             |
|    槽地址: 0x007E47F8         |  |   槽地址: 0x007EFA68          |  |   槽地址: 0x007EFCB0           |
+---------------+---------------+  +---------------+---------------+  +---------------+----------------+
                |                                  |                                  |
                v                                  v                                  v
+-------------------------------+  +-------------------------------+  +--------------------------------+
| 1. 废弃 Fog 门控 (0x4680A8)   |  | 1. 废弃 Fog 门控 (0x62CF23)   |  | 1. Laser 激光标志门 (0x62E28D) |
|    Scenario.Flags & 0x1000    |  |    Scenario.Flags & 0x1000    |  |    Type->Laser @ +0x30C        |
|    [实测恒被跳过或失效]       |  |    [实测恒被跳过或失效]       |  |                                |
| 2. 状态门: Inviso/NextAnim    |  | 2. 行为分发: BehavesLike      |  | 2. 若 Laser=0: 立即 ret 8      |
| 3. 分支 A (Voxel):            |  |    Smoke/Gas/Fire (0x62CF83)  |  |    若 Laser=1:                 |
|    3D 姿态角与四元数矩阵构建  |  |    -> TacticalClass::Draw_SHP |  |    绘制两点间 3D 激光线段      |
|    -> 0x46B0C0 (Draw_Voxel)   |  |    Spark/Railgun (0x62D02C)   |  |                                |
| 4. 分支 B (SHP):              |  |    -> 深度视口裁剪点线绘制    |  |                                |
|    投影阴影 + 调色盘适配      |  |                               |  |                                |
|    -> 0x4AED70 (Draw_SHP)     |  |                               |  |                                |
+-------------------------------+  +-------------------------------+  +--------------------------------+
```

---

### 1.2 敌军弹药迷雾视觉泄露的根本原因（实证）

在原版引擎中，敌军发射的导弹、炸弹与尾迹烟雾之所以能在 pitch-black 黑雾（Shroud）或半透明灰雾（Fog of War）中直接暴露，是由以下**双重致命缺陷**导致的：

#### 缺陷 1：`Scenario.Flags & 0x1000` 历史废弃开关

在 `BulletClass::Draw`（`0x00468090`）的指令 `0x004680A8` 处：
```asm
0046809C  mov  eax, dword ptr [0x00A8B230]  ; ScenarioClass::Instance
004680A5  mov  ecx, dword ptr [eax]         ; Scenario.Flags
004680A8  test ch, 0x10                     ; Flags & 0x1000 (历史 FogOfWar 遗留标志)
004680AB  je   0x004680E2                   ; 标志为 0 时：完全跳过迷雾检查！
```
- 在现代联机对战、单人战役及自定义渲染器（如 L3 星际式三态迷雾）中，为了修复原版 `FOG.SHP` 迷雾瓦片反色/错位崩溃的历史 Bug，引擎全局设置中 `Scenario.Flags & 0x1000` 被**强制置 0**。
- 一旦该位为 0，程序直接无条件跳转至 `0x004680E2`，下方的 `MapClass::IsCellShrouded` 检查**一次都不会被执行**！

#### 缺陷 2：`MapClass::IsCellShrouded`（`0x005865E0`）已被原版 Stub 化

即使强行让 `Flags & 0x1000` 生效，深入反汇编 `0x005865E0` 发现：
```asm
005865E0  xor  al, al                       ; 返回 false (0 = 未被迷雾遮挡)
005865E2  ret  4
```
Westwood/EA 官方在 `gamemd.exe` 最终编译发布时，将 `0x005865E0` 硬编码为一个直接返回 0 的桩函数（Stub）！  
因此原版迷雾检查不仅被前置标志跳过，其内部检测逻辑本身也已彻底失效。

#### 缺陷 3：粒子绘制链（`ParticleClass::Draw`）存在完全同构的致命漏洞

反汇编 `0x0062CEC0` 在 `0x0062CF2B` 处取证：
```asm
0062CF23  mov  edx, dword ptr [0x00A8B230]  ; ScenarioClass::Instance
0062CF29  mov  eax, dword ptr [edx]         ; Scenario.Flags
0062CF2B  test ah, 0x10                     ; Flags & 0x1000
0062CF2E  je   0x0062CF65                   ; 同样跳过，直接向下进入绘制！
0062CF58  call 0x005865E0                   ; 同一个返回 0 的桩函数
```
这意味着：
1. **导弹本体**：V3、无畏级火箭、基洛夫飞艇炸弹等在黑雾中直接渲染。
2. **尾迹烟雾**：弹药挂载的 `AttachedParticleSys`（如火箭尾烟、白烟、黑烟）每帧生成的粒子同样无视迷雾，直接渲染在屏幕上。
3. 玩家在黑雾边缘甚至黑雾深处，会清晰看到几枚导弹带着浓烟呼啸飞出，完全暴露了敌方攻城单位的埋伏位置，严重破坏了战术侦察与迷雾博弈的公平性。

---

## 2. BulletClass::Draw（0x00468090）深度反汇编全剖析

### 2.1 完整反汇编注释流程（入口至 `ret 8`）

函数原型：
```cpp
void __thiscall BulletClass::Draw(Point2D* pLocation, RectangleStruct* pBounds) const;
// ecx = this (BulletClass*); 栈参: [esp+4] = pLocation, [esp+8] = pBounds; 出口: ret 8
```

#### 阶段一：序言与废弃迷雾检查（0x00468090 - 0x004680E1）
```asm
00468090  push ebp                          ; 建立栈帧
00468091  mov  ebp, esp
00468093  and  esp, 0xFFFFFFF8              ; 8 字节对齐（浮点数与向量运算优化）
00468096  sub  esp, 0xB4                    ; 分配 180 字节本地栈空间
0046809C  mov  eax, dword ptr [0x00A8B230]  ; eax = ScenarioClass::Instance
004680A1  push ebx
004680A2  push esi
004680A3  mov  esi, ecx                     ; esi = this (BulletClass*)
004680A5  mov  ecx, dword ptr [eax]         ; ecx = Scenario.Flags
004680A7  push edi
004680A8  test ch, 0x10                     ; [门控 1] Flags & 0x1000 (FogOfWar)
004680AB  je   0x004680E2                   ; 遗留机制：未置位则直接跳过迷雾检查
004680AD  lea  ecx, [esi + 0x9C]            ; &Location (CoordStruct)
004680B3  mov  edx, dword ptr [esi + 0x9C]  ; Location.X
004680B9  mov  dword ptr [esp + 0x1C], edx
004680BD  lea  edx, [esp + 0x1C]
004680C1  mov  eax, dword ptr [ecx + 4]     ; Location.Y
004680C4  push edx
004680C5  mov  dword ptr [esp + 0x24], eax
004680C9  mov  ecx, dword ptr [ecx + 8]     ; Location.Z
004680CC  mov  dword ptr [esp + 0x28], ecx
004680D0  mov  ecx, 0x0087F7E8              ; MapClass::Instance
004680D5  call 0x005865E0                   ; MapClass::IsCellShrouded (内部已 stub 化为 xor al, al)
004680DA  test al, al
004680DC  jne  0x00468422                   ; 若在黑雾中则退出 (ret 8)
```

#### 阶段二：类型可见性与动画衍生门控（0x004680E2 - 0x00468111）
```asm
004680E2  mov  eax, dword ptr [esi + 0xAC]  ; eax = this->Type (BulletTypeClass*)
004680E8  mov  cl, byte ptr [eax + 0x29E]   ; [门控 2] Type->Inviso (bool)
004680EE  test cl, cl
004680F0  jne  0x00468422                   ; Inviso=yes 隐形弹药（如磁暴/无形射线）：跳过绘制
004680F6  mov  cl, byte ptr [esi + 0x158]   ; [门控 3] this->SpawnNextAnim (bool)
004680FC  test cl, cl
004680FE  jne  0x00468422                   ; 正处于生成下一个动画过渡态：跳过绘制
00468104  mov  cl, byte ptr [eax + 0x236]   ; [分支选择] Type->Voxel (bool @ +0x236)
0046810A  test cl, cl
0046810C  je   0x00468258                   ; Voxel == 0: 走 SHP 精灵/点弹道分支
```

#### 阶段三 A：VXL 体素导弹三维姿态与四元数变换渲染（0x00468112 - 0x00468255）
```asm
00468112  lea  ecx, [esp + 0x30]            ; 准备 Matrix3D
00468116  call 0x005AE860                   ; Matrix3D::Identity
; 逆向速度向量 Vector3D<double> Velocity (+0xE8: X, +0xF0: Y, +0xF8: Z)
0046811B  mov  eax, dword ptr [esi + 0xEC]  ; Velocity.X 高 32 位
00468121  mov  ecx, dword ptr [esi + 0xE8]  ; Velocity.X 低 32 位
00468127  fld  qword ptr [esi + 0xF0]       ; st(0) = Velocity.Y
0046812D  push eax
0046812E  push ecx
0046812F  sub  esp, 8
00468132  fchs                              ; -Velocity.Y
00468134  fstp qword ptr [esp]
00468137  call 0x004CAE30                   ; atan2(-Velocity.Y, Velocity.X) -> 计算水平航向角 (Yaw)
0046813C  fsub qword ptr [0x007E2820]
00468142  fmul qword ptr [0x007E2818]
00468148  call 0x007C5F00                   ; 浮点角度转换为二进制朝向角
0046814D  mov  word ptr [esp + 0x20], ax
...
0046817F  fld  qword ptr [esi + 0xF0]       ; Velocity.Y
00468185  fld  qword ptr [esi + 0xE8]       ; Velocity.X
0046818B  fld  st(0)
0046818D  fmul st(1)                        ; Vx * Vx
0046818F  fld  st(2)
00468191  fmul st(3)                        ; Vy * Vy
00468196  faddp st(1)                       ; Vx^2 + Vy^2
0046819F  call 0x004CAC40                   ; sqrt(Vx^2 + Vy^2) -> 水平合成速率
004681B7  mov  eax, dword ptr [esi + 0xF8]  ; Velocity.Z
004681C0  call 0x004CAE30                   ; atan2(Velocity.Z, 水平速率) -> 俯仰角 (Pitch)
...
0046823A  mov  edx, dword ptr [esi + 0xAC]  ; BulletTypeClass*
00468241  add  edx, 0xB0                    ; &Type->MainVoxel (VoxelStruct @ +0xB0)
00468247  mov  ecx, esi                     ; this
00468249  push edx                          ; pVoxel
0046824A  call 0x0046B0C0                   ; BulletClass::Draw_Voxel(pVoxel, pMatrix)
0046824F  pop  edi
00468250  pop  esi
00468251  pop  ebx
00468252  mov  esp, ebp
00468254  pop  ebp
00468255  ret  8                            ; VXL 分支安全退出
```

#### 阶段三 B：SHP 精灵弹道、地面阴影与调色盘分发（0x00468258 - 0x00468428）
```asm
00468258  mov  eax, dword ptr [esi]         ; vtable
0046825A  mov  ecx, esi
0046825C  call dword ptr [eax + 0x6C]       ; [虚表槽 27] ObjectClass::GetCell()
0046825F  test eax, eax
00468261  mov  dword ptr [esp + 0x10], eax  ; pCell
00468265  je   0x00468422                   ; 若所在 Cell 为空，退出不画
0046826F  call dword ptr [edx + 0x1E8]      ; GetHeight()
0046827D  call dword ptr [eax + 0x1C8]      ; GetZ()
00468283  lea  edi, [esi + 0x9C]            ; &Location
00468289  mov  ebx, eax                     ; ebx = Z 高度
...
; 桥梁与地形高度校正
004682E1  mov  ecx, dword ptr [eax + 0x140] ; Cell->Flags
004682E7  test ch, 1                        ; 桥梁标记
004682EA  je   0x00468301
004682F1  cmp  ebx, dword ptr [0x0089DE64]  ; BridgeHeight (通常 0x100)
...
; 地面投影阴影渲染
00468308  mov  ecx, dword ptr [esi + 0xAC]  ; BulletTypeClass*
0046830E  mov  al, byte ptr [ecx + 0x29A]   ; Type->Shadow (bool @ +0x29A)
00468314  test al, al
00468316  je   0x00468379                   ; 无阴影则跳过
00468374  call 0x004AED70                   ; TacticalClass::Draw_SHP 绘制地面投影阴影
...
; 弹药主体调色盘判定
00468385  mov  cl, byte ptr [eax + 0x2A8]   ; Type->AnimPalette (bool)
0046838D  je   0x00468397
0046838F  mov  ebx, dword ptr [0x0087F6C0]  ; 动画全局色盘
00468397  mov  cl, byte ptr [eax + 0x2A9]   ; Type->FirersPalette (bool)
0046839D  je   0x004683D7
004683A1  mov  eax, dword ptr [esi + 0x114] ; this->InheritedColor
004683B2  mov  edx, dword ptr [ecx + eax*4] ; 对应阵营色盘
004683B5  mov  ebx, dword ptr [edx + 0x30C]
...
; 弹药主体精灵绘制
004683EA  call dword ptr [edx + 0x1D0]      ; GetAnimFrame()
004683F2  call 0x006D20E0                   ; 2.5D 等轴测屏幕投影坐标换算
0046841D  call 0x004AED70                   ; TacticalClass::Draw_SHP 绘制弹体
00468422  pop  edi
00468423  pop  esi
00468424  pop  ebx
00468425  mov  esp, ebp
00468427  pop  ebp
00468428  ret  8                            ; 标准出口退出
```

---

### 2.2 弹体定点坐标到地图格子（Cell）转换实证

引擎中所有的位置信息均为 **Lepton（微点）** 定点数表示，其中：
$$1 \text{ 格 (Cell)} = 256 \text{ Leptons} = 2^8 \text{ Leptons}$$

反汇编 `MapClass::GetCellAt(CoordStruct*)`（`0x00565730`）：
```asm
00565736  mov  eax, dword ptr [edi]         ; Location.X (Leptons)
00565738  cdq                               ; 符号扩展
00565739  and  edx, 0xFF                    ; 负数向下取整修正
0056573F  add  eax, edx
00565741  mov  esi, eax
00565743  mov  eax, dword ptr [edi + 4]     ; Location.Y (Leptons)
00565746  cdq
00565747  and  edx, 0xFF
0056574D  add  eax, edx
0056574F  sar  eax, 8                       ; CellY = Location.Y >> 8
00565752  mov  edx, eax
00565754  sar  esi, 8                       ; CellX = Location.X >> 8
00565757  shl  edx, 9                       ; edx = CellY * 512
0056575A  add  edx, esi                     ; cellIndex = CellY * 512 + CellX
```
**实证结论**：  
直接读取弹体 `[esi + 0x9C]`（X）与 `[esi + 0xA0]`（Y），执行算术右移 8 位（`sar reg, 8`），即可无损换算为 `s_visionGrid` 一维索引：`cellY * 512 + cellX`。

---

### 2.3 阵营所有权（Owner）寻址树逆向

在 `BulletClass::Construct`（`0x004664C0`）中实证了字段赋值链：
```asm
004664FB  mov  dword ptr [ecx + 0xAC], eax  ; this->Type = pType (BulletTypeClass*)
00466501  mov  dword ptr [ecx + 0xB0], esi  ; this->Owner = pOwner (TechnoClass*)
00466527  mov  eax, dword ptr [esi + 0x21C] ; eax = pOwner->OwnerHouse (HouseClass*)
0046652D  mov  eax, dword ptr [eax + 0x16054]; eax = House->ColorSchemeIndex
00466533  mov  dword ptr [ecx + 0x114], eax ; this->InheritedColor = ColorIndex
```
**完整寻址链**：
```
BulletClass* (pBullet)
  │
  ├─> +0xAC: BulletTypeClass* Type
  │
  └─> +0xB0: TechnoClass* Owner (发射该弹药的单位/建筑对象)
        │
        └─> +0x21C: HouseClass* OwnerHouse (所属作战阵营)
              │
              ├─> +0x30:   int ArrayIndex (阵营索引 0..31)
              └─> +0x5788: uint32_t Allies (盟军掩码位，bit[N]=1 表示与第 N 阵营结盟)
```
- 若 `pOwner == nullptr`（由触发器或地图中立事件生成的野生投射物）：视为无阵营，按严格迷雾直视规则处理。
- 若 `pOwnerHouse == HouseClass::Player`（本地人类玩家）：**100% 豁免绘制**。
- 若 `(HouseClass::Player->Allies & (1 << pOwnerHouse->ArrayIndex)) != 0`（玩家盟友）：**100% 豁免绘制**。

---

### 2.4 抛物线轨迹（Velocity）与目标跟踪过程逆向

#### 1. 速度向量与动力学字段（`BulletClass`）
- `+0xE8`: `double Velocity.X`
- `+0xF0`: `double Velocity.Y`
- `+0xF8`: `double Velocity.Z`
- `+0x108`: `int CourseLockDuration`（航向锁定倒计时）
- `+0x10C`: `AbstractClass* Target`（跟踪目标对象）
- `+0x140`: `CoordStruct TargetCoords`（目标空间绝对坐标）

#### 2. 每逻辑帧推进（`BulletClass::Update` @ `0x004666E0`）
反汇编 `0x00467B1A` 取证：
```asm
00467B1A  fld  qword ptr [ebp + 0xF8]       ; Velocity.Z
00467B20  fld  qword ptr [ebp + 0xF0]       ; Velocity.Y
00467B26  fld  qword ptr [ebp + 0xE8]       ; Velocity.X
; 计算 3D 欧氏空间合成速率 sqrt(Vx^2 + Vy^2 + Vz^2)
00467B48  call 0x004CAC40
```
- **位置积分**：
  $$\text{Location}_{t+1} = \text{Location}_t + \text{Velocity}$$
- **抛物线重力衰减**（`Type->Arcing` @ `+0x29B == true`）：  
  每帧对 `Velocity.Z` 累加负向重力加速度（取自 `RulesClass::Instance->Gravity`，默认固定步长），形成完美的平抛/斜抛弹道二次曲线。
- **制导跟踪修正**（`Type->ROT` @ `+0x2DC > 0`）：  
  当 `CourseLockDuration` 递减至 0 时，每帧计算当前弹体指向目标 `TargetCoords`（`+0x140`）的视线角差，限制以最大 `ROT` 角速度旋转 `Velocity` 向量，实现红外/雷达寻的追踪。
- **着靶与引爆**：  
  当弹体碰撞到地形表面（`Location.Z <= 0`）或与目标进入杀伤引信半径时，在 `0x004690B0` 调用 `BulletClass::Detonate`，生成弹坑/辐射/伤害波与爆炸动画。

---

## 3. 粒子与微粒系统绘制链路全剖析

### 3.1 ParticleClass::Draw（0x0062CEC0）逆向取证

`ParticleClass` 继承自 `ObjectClass`，实例大小为 `0x138` 字节，代表单个动态烟雾团、火星、火焰团或光束微粒。

#### 1. 虚表与入口
- 虚表地址：`0x007EF954`
- 虚表槽 69：`0x007EFA68` -> `0x0062CEC0`
- 栈参约定：`void __thiscall ParticleClass::Draw(Point2D* pLocation, RectangleStruct* pBounds) const`，出口 `ret 8`。

#### 2. 字段映射表
| 偏移 | 类型 | 字段语义 | 证据与用途 |
|---|---|---|---|
| `+0x9C` | `CoordStruct` | `Location` (X, Y, Z in leptons) | 当前粒子空间位置 |
| `+0xAC` | `ParticleTypeClass*` | `Type` | 粒子类型指针 |
| `+0x124` | `ParticleSystemClass*` | `ParticleSystem` | 所属发射系统指针 |
| `+0x12C` | `BYTE` | `StateAI` | 粒子生命周期状态机推进进度 |
| `+0x12F` | `BYTE` | `Translucency` | 半透明度（`0x19`=25%, `0x32`=50%, `0x4B`=75%） |

#### 3. 行为类型分发（`ParticleTypeClass->BehavesLike` @ `+0x314`）
```
BehavesLike 枚举值：
0 = Smoke   (常规烟雾：膨胀淡出动画，走 Draw_SHP)
1 = Gas     (飘散气体：受风力漂移影响，走 Draw_SHP)
2 = Fire    (火焰团：循环翻滚，走 Draw_SHP)
3 = Spark   (微小火星：受重力坠落，走 0x62D02C 深度裁剪点阵绘制)
4 = Railgun (磁轨炮尾迹：走 0x62D02C 直线段光栅化绘制)
```

---

### 3.2 ParticleSystemClass::Draw（0x0062E280）逆向取证

`ParticleSystemClass` 继承自 `ObjectClass`，是粒子发射器管理容器，用于持续发射烟雾尾迹或绘制持续激光束。

#### 1. 虚表与入口
- 虚表地址：`0x007EFB9C`
- 虚表槽 69：`0x007EFCB0` -> `0x0062E280`
- 栈参约定：`void __thiscall ParticleSystemClass::Draw(Point2D* pLocation, RectangleStruct* pBounds) const`，出口 `ret 8`。

#### 2. 核心分支门控反汇编
```asm
0062E285  mov  edi, ecx                     ; edi = this (ParticleSystemClass*)
0062E287  mov  eax, dword ptr [edi + 0xAC]  ; eax = this->Type (ParticleSystemTypeClass*)
0062E28D  mov  cl, byte ptr [eax + 0x30C]   ; cl = Type->Laser (bool @ +0x30C)
0062E293  test cl, cl
0062E295  je   0x0062E376                   ; [关键] 若 Laser == 0: 立即跳至尾部 ret 8！
```
**关键发现**：  
- `ParticleSystemClass::Draw` 本身**并不负责绘制容器内成百上千个粒子**（具体粒子的绘制是由各粒子自身挂在战术层，通过 `ParticleClass::Draw` 单独调用的）。
- 该函数仅在 `Type->Laser == true` 时，负责在发射源 `[edi + 0x9C]` 与目标 `[edi + 0xD4]` 之间绘制一条 3D 持续激光光束。
- 其所属阵营位于 `[edi + 0xFC]`（`HouseClass* OwnerHouse`），所属发射单位位于 `[edi + 0xE0]`（`TechnoClass* Owner`）。

---

## 4. 弹道与微粒迷雾隐形剔除 Hook 方案设计

### 4.1 核心设计红线（绝对同步保证）

> [!IMPORTANT]
> **联机一致性绝对红线（Deterministic Golden Rule）**：  
> 1. 本 Hook **仅且只能**拦截虚函数槽 69（`ObjectClass::Draw`），在渲染管线入口处短路退出（`ret 8`）。  
> 2. **严禁修改** `BulletClass::Update`、`BulletClass::Fly`、`BulletClass::MoveTo`、`BulletClass::Detonate` 等任何逻辑物理推进函数。  
> 3. 弹药在被剔除期间，其空间坐标更新、重力计算、目标跟踪、与防御建筑（爱国者/爱国者飞弹）的拦截判定、最终落地伤害计算**100% 保持原生逻辑同步运行**。  
> 4. 该剔除仅对本地画面的视觉像素生效，保证本地帧率优化与战争迷雾机密性，联机对战双方各视口互不干扰，零网络同步风险（Zero OOS Risk）。

---

### 4.2 智能视野判定谓词矩阵

| 实体分类 | 阵营关系 | 直视判定状态（`s_visionGrid`） | 决策结果 | 行为语义 |
|---|---|---|---|---|
| **BulletClass** | 己方 / 盟军 | 任意状态（无论迷雾与否） | **绘制 (Draw)** | 玩家与盟友发射的弹药全航程可见 |
| **BulletClass** | 敌军 / 中立 | 处于 `s_visionGrid` 视野圈内 | **绘制 (Draw)** | 飞入我方直视空域的导弹正常显现 |
| **BulletClass** | 敌军 / 中立 | 未在 `s_visionGrid` 视野圈内 | **剔除 (Cull / ret 8)** | 黑雾/灰雾中的导弹完全隐形，杜绝报位 |
| **ParticleClass** | 己方系统 | 任意状态 | **绘制 (Draw)** | 己方单位与武器尾烟正常显示 |
| **ParticleClass** | 敌军 / 中立 | 粒子所在格在直视圈内 | **绘制 (Draw)** | 飞入视野内的烟雾/火星正常渲染 |
| **ParticleClass** | 敌军 / 中立 | 粒子所在格在迷雾中 | **剔除 (Cull / ret 8)** | 黑雾深处射出的导弹尾烟彻底隐形 |
| **ParticleSystemClass** | 敌军激光 | 源格与目标格均在迷雾中 | **剔除 (Cull / ret 8)** | 雾中暗处激光完全剔除 |

---

### 4.3 C++ Hook 实现代码原型

以下代码遵循工程现有的 `blitter_hooks.cpp` 零侵入代码段注入范式，通过 `PatchVTablePointer` 动态改写虚表指针：

```cpp
// ============================================================================
// bullet_particle_fog_hooks.cpp
// 弹道抛物线与微粒系统战争迷雾智能剔除模块
// ============================================================================

#include <windows.h>
#include <cstdint>

// 引擎既有全局变量与符号定义 (参考 docs/re/visibility_gap_spysat.md)
#define ADDR_HOUSE_PLAYER                0x00A83D4C  // HouseClass::Player
#define ADDR_MAP_CELLS_ARRAY             0x00A8ED78  // MapClass::Instance->Cells

// 目标虚表槽 69 条目地址 (每个类虚表偏移 +0x114)
#define ADDR_VTABLE_ENTRY_BULLET_DRAW    0x007E47F8  // BulletClass::Draw (0x00468090)
#define ADDR_VTABLE_ENTRY_PARTICLE_DRAW  0x007EFA68  // ParticleClass::Draw (0x0062CEC0)
#define ADDR_VTABLE_ENTRY_PARSYS_DRAW    0x007EFCB0  // ParticleSystemClass::Draw (0x0062E280)

// 引用外部由 UpdateVisionGrid() 维护的直视视距网格与帧 Token
extern uint32_t s_visionGrid[512 * 512];
extern uint32_t s_visionToken;
extern bool g_enableStarCraftFog;

// 原始虚表函数指针保存
typedef void (__thiscall *BulletDrawFn)(void *pThis, void *pLocation, void *pBounds);
typedef void (__thiscall *ParticleDrawFn)(void *pThis, void *pLocation, void *pBounds);
typedef void (__thiscall *ParticleSystemDrawFn)(void *pThis, void *pLocation, void *pBounds);

static BulletDrawFn         g_pOrigBulletDraw         = nullptr;
static ParticleDrawFn       g_pOrigParticleDraw       = nullptr;
static ParticleSystemDrawFn g_pOrigParticleSystemDraw = nullptr;

// 遥测计数器统计
struct FogCullTelemetry {
    uint32_t bulletsCulledByFog;
    uint32_t totalBulletsRendered;
    uint32_t particlesCulledByFog;
    uint32_t totalParticlesRendered;
} g_fogCullTelemetry = {0};

// ----------------------------------------------------------------------------
// 辅助判定函数：判断所属 HouseClass 是否为己方或盟军
// ----------------------------------------------------------------------------
static inline bool IsHousePlayerOrAlly(void *pHouse, void *pPlayer) {
    if (!pHouse || !pPlayer) return false;
    if (pHouse == pPlayer) return true; // 己方

    int ownerIdx = *reinterpret_cast<const int*>(reinterpret_cast<const uint8_t*>(pHouse) + 0x30);
    uint32_t playerAllies = *reinterpret_cast<const uint32_t*>(reinterpret_cast<const uint8_t*>(pPlayer) + 0x5788);
    if (ownerIdx >= 0 && ownerIdx < 32 && ((1u << ownerIdx) & playerAllies) != 0) {
        return true; // 盟友
    }
    return false;
}

// ----------------------------------------------------------------------------
// 辅助判定函数：检查给定 Lepton 坐标是否在玩家直视网格或心灵感应探测范围内
// ----------------------------------------------------------------------------
static inline bool IsCoordInPlayerVision(int locX, int locY, void *pPlayer) {
    int cellX = locX >> 8;
    int cellY = locY >> 8;

    if (cellX < 0 || cellX >= 512 || cellY < 0 || cellY >= 512) {
        return false;
    }

    // 1. 直视网格匹配
    if (s_visionGrid[cellY * 512 + cellX] == s_visionToken) {
        return true;
    }

    // 2. 心灵探测仪 (Psychic Sensor) 兼容支持
    uintptr_t cellsBase = *reinterpret_cast<const uintptr_t*>(ADDR_MAP_CELLS_ARRAY);
    if (cellsBase && pPlayer) {
        uint8_t *pCell = *reinterpret_cast<uint8_t**>(cellsBase + (cellY * 512 + cellX) * 4);
        if (pCell) {
            int playerIdx = *reinterpret_cast<const int*>(reinterpret_cast<const uint8_t*>(pPlayer) + 0x30);
            if (playerIdx >= 0 && playerIdx < 24) {
                const uint16_t *sensors = reinterpret_cast<const uint16_t*>(pCell + 0xAC);
                if (sensors[playerIdx] > 0) {
                    return true;
                }
            }
        }
    }
    return false;
}

// ----------------------------------------------------------------------------
// 核心谓词：判定弹体是否应该被渲染
// ----------------------------------------------------------------------------
static inline bool ShouldDrawBullet(void *pBullet) {
    if (!pBullet) return false;

    void *pPlayer = *reinterpret_cast<void**>(ADDR_HOUSE_PLAYER);
    if (!pPlayer) return true;

    // 1. 读取发射者 Owner (TechnoClass* @ +0xB0)
    void *pOwner = *reinterpret_cast<void**>(reinterpret_cast<uintptr_t>(pBullet) + 0xB0);
    if (pOwner) {
        // 读取所属阵营 OwnerHouse (HouseClass* @ +0x21C)
        void *pHouse = *reinterpret_cast<void**>(reinterpret_cast<uintptr_t>(pOwner) + 0x21C);
        if (IsHousePlayerOrAlly(pHouse, pPlayer)) {
            return true; // 己方与盟军发射的弹药：100% 正常绘制
        }
    }

    // 2. 敌军/中立弹药：读取弹体绝对空间坐标 (Location @ +0x9C)
    int locX = *reinterpret_cast<const int*>(reinterpret_cast<const uint8_t*>(pBullet) + 0x9C);
    int locY = *reinterpret_cast<const int*>(reinterpret_cast<const uint8_t*>(pBullet) + 0xA0);

    return IsCoordInPlayerVision(locX, locY, pPlayer);
}

// ----------------------------------------------------------------------------
// 核心谓词：判定微粒是否应该被渲染
// ----------------------------------------------------------------------------
static inline bool ShouldDrawParticle(void *pParticle) {
    if (!pParticle) return false;

    void *pPlayer = *reinterpret_cast<void**>(ADDR_HOUSE_PLAYER);
    if (!pPlayer) return true;

    // 1. 尝试溯源所属微粒系统 (ParticleSystemClass* @ +0x124)
    void *pSys = *reinterpret_cast<void**>(reinterpret_cast<uintptr_t>(pParticle) + 0x124);
    if (pSys) {
        // 读取微粒系统的 OwnerHouse (@ +0xFC) 或 Owner->OwnerHouse (@ +0xE0->+0x21C)
        void *pHouse = *reinterpret_cast<void**>(reinterpret_cast<uintptr_t>(pSys) + 0xFC);
        if (!pHouse) {
            void *pOwner = *reinterpret_cast<void**>(reinterpret_cast<uintptr_t>(pSys) + 0xE0);
            if (pOwner) {
                pHouse = *reinterpret_cast<void**>(reinterpret_cast<uintptr_t>(pOwner) + 0x21C);
            }
        }
        if (IsHousePlayerOrAlly(pHouse, pPlayer)) {
            return true; // 己方微粒：恒定绘制
        }
    }

    // 2. 敌军/中立微粒：按当前微粒坐标 (Location @ +0x9C) 进行迷雾裁剪
    int locX = *reinterpret_cast<const int*>(reinterpret_cast<const uint8_t*>(pParticle) + 0x9C);
    int locY = *reinterpret_cast<const int*>(reinterpret_cast<const uint8_t*>(pParticle) + 0xA0);

    return IsCoordInPlayerVision(locX, locY, pPlayer);
}

// ----------------------------------------------------------------------------
// 核心谓词：判定微粒系统（激光束）是否应该被渲染
// ----------------------------------------------------------------------------
static inline bool ShouldDrawParticleSystem(void *pSys) {
    if (!pSys) return false;

    void *pPlayer = *reinterpret_cast<void**>(ADDR_HOUSE_PLAYER);
    if (!pPlayer) return true;

    void *pHouse = *reinterpret_cast<void**>(reinterpret_cast<uintptr_t>(pSys) + 0xFC);
    if (IsHousePlayerOrAlly(pHouse, pPlayer)) {
        return true;
    }

    // 激光束检查：源坐标 (+0x9C) 或 目标坐标 (+0xD4) 只要有一端在我方直视内即绘制
    int srcX = *reinterpret_cast<const int*>(reinterpret_cast<const uint8_t*>(pSys) + 0x9C);
    int srcY = *reinterpret_cast<const int*>(reinterpret_cast<const uint8_t*>(pSys) + 0xA0);
    int dstX = *reinterpret_cast<const int*>(reinterpret_cast<const uint8_t*>(pSys) + 0xD4);
    int dstY = *reinterpret_cast<const int*>(reinterpret_cast<const uint8_t*>(pSys) + 0xD8);

    return IsCoordInPlayerVision(srcX, srcY, pPlayer) || IsCoordInPlayerVision(dstX, dstY, pPlayer);
}

// ----------------------------------------------------------------------------
// Hook 入口实现 (thiscall, 对应虚表槽 69)
// ----------------------------------------------------------------------------

void __thiscall Hook_Bullet_Draw(void *pLocation, void *pBounds) {
    void *pThis = this;
    if (g_enableStarCraftFog && !ShouldDrawBullet(pThis)) {
        g_fogCullTelemetry.bulletsCulledByFog++;
        return; // 直接 ret 8，跳过所有 VXL 与 SHP 绘制
    }

    g_fogCullTelemetry.totalBulletsRendered++;
    if (g_pOrigBulletDraw) {
        g_pOrigBulletDraw(pThis, pLocation, pBounds);
    }
}

void __thiscall Hook_Particle_Draw(void *pLocation, void *pBounds) {
    void *pThis = this;
    if (g_enableStarCraftFog && !ShouldDrawParticle(pThis)) {
        g_fogCullTelemetry.particlesCulledByFog++;
        return; // 直接 ret 8，跳过烟雾/火星绘制
    }

    g_fogCullTelemetry.totalParticlesRendered++;
    if (g_pOrigParticleDraw) {
        g_pOrigParticleDraw(pThis, pLocation, pBounds);
    }
}

void __thiscall Hook_ParticleSystem_Draw(void *pLocation, void *pBounds) {
    void *pThis = this;
    if (g_enableStarCraftFog && !ShouldDrawParticleSystem(pThis)) {
        return; // 直接 ret 8，跳过激光线段绘制
    }

    if (g_pOrigParticleSystemDraw) {
        g_pOrigParticleSystemDraw(pThis, pLocation, pBounds);
    }
}

// ----------------------------------------------------------------------------
// 虚表注入与卸载管理
// ----------------------------------------------------------------------------
static bool PatchVTable(uintptr_t slotAddr, uintptr_t newFn, uintptr_t *pOrigFn, const char *name) {
    DWORD oldProtect = 0;
    if (!VirtualProtect(reinterpret_cast<void*>(slotAddr), sizeof(uintptr_t), PAGE_EXECUTE_READWRITE, &oldProtect)) {
        return false;
    }
    if (pOrigFn && *pOrigFn == 0) {
        *pOrigFn = *reinterpret_cast<uintptr_t*>(slotAddr);
    }
    *reinterpret_cast<uintptr_t*>(slotAddr) = newFn;
    VirtualProtect(reinterpret_cast<void*>(slotAddr), sizeof(uintptr_t), oldProtect, &oldProtect);
    return true;
}

void InstallBulletParticleFogHooks() {
    PatchVTable(ADDR_VTABLE_ENTRY_BULLET_DRAW,
                reinterpret_cast<uintptr_t>(&Hook_Bullet_Draw),
                reinterpret_cast<uintptr_t*>(&g_pOrigBulletDraw),
                "BulletClass::Draw");

    PatchVTable(ADDR_VTABLE_ENTRY_PARTICLE_DRAW,
                reinterpret_cast<uintptr_t>(&Hook_Particle_Draw),
                reinterpret_cast<uintptr_t*>(&g_pOrigParticleDraw),
                "ParticleClass::Draw");

    PatchVTable(ADDR_VTABLE_ENTRY_PARSYS_DRAW,
                reinterpret_cast<uintptr_t>(&Hook_ParticleSystem_Draw),
                reinterpret_cast<uintptr_t*>(&g_pOrigParticleSystemDraw),
                "ParticleSystemClass::Draw");
}

void UninstallBulletParticleFogHooks() {
    if (g_pOrigBulletDraw) {
        PatchVTable(ADDR_VTABLE_ENTRY_BULLET_DRAW, reinterpret_cast<uintptr_t>(g_pOrigBulletDraw), nullptr, "BulletClass::Draw");
        g_pOrigBulletDraw = nullptr;
    }
    if (g_pOrigParticleDraw) {
        PatchVTable(ADDR_VTABLE_ENTRY_PARTICLE_DRAW, reinterpret_cast<uintptr_t>(g_pOrigParticleDraw), nullptr, "ParticleClass::Draw");
        g_pOrigParticleDraw = nullptr;
    }
    if (g_pOrigParticleSystemDraw) {
        PatchVTable(ADDR_VTABLE_ENTRY_PARSYS_DRAW, reinterpret_cast<uintptr_t>(g_pOrigParticleSystemDraw), nullptr, "ParticleSystemClass::Draw");
        g_pOrigParticleSystemDraw = nullptr;
    }
}
```

---

## 5. 关键实证地址与数据结构速查表

### 5.1 虚表与入口地址表

| 目标类与方法 | 虚表基址 (VA) | 虚表槽 (Slot) | 虚表条目地址 (VA) | 原始函数入口 (VA) | 栈清理约定 |
|---|---|---|---|---|---|
| `BulletClass::Draw` | `0x007E46E4` | 69 (`+0x114`) | `0x007E47F8` | `0x00468090` | `ret 8` (__thiscall) |
| `ParticleClass::Draw` | `0x007EF954` | 69 (`+0x114`) | `0x007EFA68` | `0x0062CEC0` | `ret 8` (__thiscall) |
| `ParticleSystemClass::Draw` | `0x007EFB9C` | 69 (`+0x114`) | `0x007EFCB0` | `0x0062E280` | `ret 8` (__thiscall) |
| `BulletClass::AI/Update` | `0x007E46E4` | 23 (`+0x5C`) | `0x007E4740` | `0x004666E0` | `ret` (__thiscall) |
| `BulletClass::MoveTo` | `0x007E46E4` | 124 (`+0x1F0`) | `0x007E48D4` | `0x00468670` | `ret 8` (__thiscall) |
| `BulletClass::Detonate` | — | 非虚函数 | — | `0x004690B0` | `ret 4` (__thiscall) |
| `MapClass::IsCellShrouded` | — | 全局方法 | — | `0x005865E0` | `ret 4` (已 Stub 化) |

---

### 5.2 核心对象字段偏移对照

```
[BulletClass] (Size = 0x160)
  +0x00:  void* vtable               (0x007E46E4)
  +0x6C:  int Health / Damage
  +0x8C:  BYTE InAir
  +0x9C:  int Location.X             (Leptons, >>8 得到 CellX)
  +0xA0:  int Location.Y             (Leptons, >>8 得到 CellY)
  +0xA4:  int Location.Z             (Leptons, 空间飞行高度)
  +0xAC:  BulletTypeClass* Type      (弹药类型)
  +0xB0:  TechnoClass* Owner         (发射者对象，->+0x21C 索引所属 HouseClass)
  +0xE0:  bool Bright
  +0xE8:  double Velocity.X          (三维空间飞行动力学速度向量)
  +0xF0:  double Velocity.Y
  +0xF8:  double Velocity.Z
  +0x108: int CourseLockDuration     (航向锁定帧倒计时)
  +0x10C: AbstractClass* Target      (跟踪目标对象)
  +0x110: int Speed                  (弹道标称飞行速度)
  +0x114: int InheritedColor         (阵营调色盘映射索引)
  +0x128: WarheadTypeClass* WH       (战斗部弹头)
  +0x12C: BYTE AnimFrame             (当前动画帧号)
  +0x130: WeaponTypeClass* WeaponType(对应武器类型)
  +0x134: CoordStruct SourceCoords   (发射点起点坐标)
  +0x140: CoordStruct TargetCoords   (目标点终点坐标)
  +0x14C: CellStruct LastMapCoords   (上一帧所在格子坐标)
  +0x154: AnimClass* NextAnim        (后续过渡动画指针)
  +0x158: bool SpawnNextAnim         (是否正处于生成下阶段动画门)

[ParticleClass] (Size = 0x138)
  +0x00:  void* vtable               (0x007EF954)
  +0x9C:  int Location.X             (Leptons, >>8 得到 CellX)
  +0xA0:  int Location.Y             (Leptons, >>8 得到 CellY)
  +0xA4:  int Location.Z             (Leptons)
  +0xAC:  ParticleTypeClass* Type    (微粒类型)
  +0x124: ParticleSystemClass* Sys   (所属微粒系统容器，->+0xFC 索引所属 HouseClass)
  +0x12C: BYTE StateAIAdvance
  +0x12F: BYTE Translucency          (透明度等级: 0x19, 0x32, 0x4B)

[ParticleSystemClass] (Size = 0x100)
  +0x00:  void* vtable               (0x007EFB9C)
  +0x9C:  CoordStruct Location       (系统发射源坐标)
  +0xAC:  ParticleSystemTypeClass* Type
  +0xBC:  DynamicVectorClass Particles (子微粒动态数组)
  +0xD4:  CoordStruct TargetCoords   (激光/粒子目标坐标)
  +0xE0:  TechnoClass* Owner         (所属发射单位)
  +0xFC:  HouseClass* OwnerHouse     (所属阵营指针)
```
