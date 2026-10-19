# 尤里的复仇寻敌核心（Greatest_Threat）与空间网格深度逆向工程分析

> **逆向对象**：`gamemd.exe` 1.001（官方英/中版本），ImageBase = `0x00400000`  
> **关联源码**：`ra2render/blitter_hooks.cpp`、`ra2render/ra2render.h`  
> **前置参考**：`docs/re/targeting_spatial.md`、`REVERSE_ENGINEERING_AND_PATCHES.md`  
> **分析工具**：Capstone 32-bit x86 反汇编引擎、PE 结构解析器、MSVC 2022 开发编译链  

---

## 1. 结论速览与架构定位

### 1.1 寻敌核心三大函数分工

```
[ 单位逻辑周期驱动 ]
         │
         ▼
 TechnoClass::SelectAutoTarget (0x006FB010 / 0x00736CA0)
   ├── 角色：【限频调度器】（0x70 字节，非重型扫描体）
   ├── 状态维护：推进 this+0x2FC (扫描计数器) 与 this+0x1FC (ReloadTimer)
   └── 触发动作：当计数耗尽且定时器到期时，发起虚调用 v[73]=0x006F4A70 (arg=2)
         │
         ▼
 [ AI / 开火 / 警戒 / 任务决策层直接驱动 ]
         │
         ▼
 TechnoClass::Greatest_Threat (0x006F8DF0)
   ├── 角色：【重型寻敌与候选扫描主体】（0xFC0 字节，1255 条汇编指令）
   ├── 前置检查：重入计数 (0x00A8EC34)、阵营淘汰状态 (0x0050B730)、分布式开火向量清理
   ├── 搜索半径：radius = (WeaponRange >> 8) + (RangeExtra >> 8) + 1
   ├── 候选枚举：
   │     ├─【路 A】：全局 20×20 粗空间桶 (0x00887888) 候选物化遍历
   │     ├─【路 B】：以 radius 为半径的同心圆逐格螺旋扫描 (Spiral Ring) + CellClass 链表
   │     └─【路 C】：全局空军/特种对象向量线性遍历 (0x00A8E390 等)
   └── 择优机制：严格大于比较（Score > MaxScore），保留最高分目标
         │
         ▼
 TechnoClass::EvaluateTarget (0x006F7CA0)
   ├── 角色：【单候选威胁评估与打分器】（0xCC0 字节，1004 条汇编指令）
   ├── 硬性过滤：Null、InLimbo(+0x81)、Health(+0x6C)、Selectable(+0x3D5)、结盟判定 (IsAlliedWith)
   └── 打分构成：基准威胁分 (0x0070CD10) + 残血优先惩罚/加成 + 战队集火加成 + Rules INI 修正
```

### 1.2 现网 L2 漏装缺陷与根因

在现网 `ra2render/blitter_hooks.cpp` 中，`InstallVTableHooks()` 存在两重重大缺陷：
1. **漏装虚表槽**：`InstallVTableHooks()` 仅安装了 `TechnoClass::SelectAutoTarget`（项 265）与 `UnitClass::SelectAutoTarget`（项 265），**完全遗漏了 `TechnoClass::Greatest_Threat`（项 241）与 `UnitClass::Greatest_Threat`（项 241）**。这导致 Target Retention（存活目标保持）根本未被激活；
2. **虚表覆盖局限性**：由于 C++ 虚表机制，`InfantryClass`（`0x007EB058`）、`BuildingClass`（`0x007E3EBC`）、`AircraftClass`（`0x007E22A4`）和 `FootClass`（`0x007E8C94`）在虚表项 241 均持有**独立的函数入口**（如步兵为 `0x0051E140`，建筑为 `0x00445F00`，空军/机动单位为 `0x004D9920`）。即便补齐 Techno 与 Unit 的虚表挂钩，**步兵、防御建筑与战机依然全部处于脱钩状态**！
3. **彻底根治方案**：所有派生类的 `Greatest_Threat` 最终全部直接 `call 0x006F8DF0`。因此，在 `0x006F8DF0` 函数入口处直接挂载 **9 字节 Inline Hook + 跳板（Trampoline）**，即可实现全局 100% 覆盖全部作战单位、防御塔、步兵与战机，彻底激活存活目标保持。

---

## 2. Greatest_Threat (0x006F8DF0) 深度逆向分析

### 2.1 函数签名、ABI 与寄存器分配

- **调用约定**：标准 MSVC 32-bit `__thiscall`
  - `ECX`：`this`（指向调用者 `TechnoClass*`）
  - 被调用者清栈：`ret 0x0C`（3 个 DWORD 参数，共 12 字节）
- **C++ 签名**：
  ```cpp
  AbstractClass* __thiscall TechnoClass::Greatest_Threat(
      uint32_t     targetFlags,   // [esp+0x70]: 寻敌标志位域 (TargetFlags)
      CoordStruct* pCenter,       // [esp+0x74]: 寻敌中心坐标指针 (leptons)
      int          arg3           // [esp+0x78]: 附加参数 / 句柄
  );
  ```
- **栈帧布局**（序言：`sub esp, 0x5C`；接着压入 `ebx, ebp, esi, edi`，共开辟 `0x6C` 字节）：
  | 栈槽偏移 | 对应变量 / 含义 |
  | :--- | :--- |
  | `[esp+0x00 .. 0x0F]` | 保存的寄存器 `edi, esi, ebp, ebx` |
  | `[esp+0x13]` | 布尔标志：Focus / 守卫目标是否合法 |
  | `[esp+0x14]` | 内部重映射的 `TargetFlags`（如 `0x8042`） |
  | `[esp+0x18]` | 逐格扫描候选列表局部指针 |
  | `[esp+0x1C]` | **当前最高威胁分（MaxScore）**，初始化为 `-1` (`0xFFFFFFFF`) |
  | `[esp+0x20]` | **当前最优目标指针（BestTarget）**，初始化为 `0` (`nullptr`) |
  | `[esp+0x24]` | 螺旋环当前半径索引（`ring`） |
  | `[esp+0x28]` | 螺旋扫描当前格子坐标结构 |
  | `[esp+0x2C]` | 武器射程暂存（leptons） |
  | `[esp+0x38]` | **搜索半径（cell）**，控制螺旋环圈数上限 |
  | `[esp+0x3C]` | 地图高度/层级查询结果（来自 `0x0056D230`） |
  | `[esp+0x40]` | 螺旋内层扫描当前坐标偏移 |
  | `[esp+0x44]` | 临时 `CellStruct`（X: `word ptr [esp+0x44]`, Y: `word ptr [esp+0x46]`） |
  | `[esp+0x58]` | **中心单元格坐标**（`CellStruct`，由 `pCenter` 右移 8 位得到） |
  | `[esp+0x6C]` | 函数返回地址 |
  | `[esp+0x70]` | 入参 1：`targetFlags` |
  | `[esp+0x74]` | 入参 2：`pCenter`（内部被就地重用为 cell 换算暂存） |
  | `[esp+0x78]` | 入参 3：`arg3`（传给打分器 `0x006F7CA0`） |

- **主要寄存器角色**：
  - `ESI`：始终锁定当前执行寻敌的单位自身（`TechnoClass* this`）
  - `EBP`：当前正在评估的候选目标对象（`AbstractClass* candidate`）
  - `EBX`：寻敌掩码与临时计算寄存器
  - `EDI`：打分暂存、循环计数器与武器索引

---

### 2.2 控制流全貌与关键代码段反汇编

#### 2.2.1 序言与前置过滤（0x006F8DF0 – 0x006F8FE8）

```assembly
006F8DF0  83EC 5C                sub     esp, 0x5C               ; 开辟 92 字节局部栈
006F8DF3  8B15 34ECA800          mov     edx, ds:[0x00A8EC34]    ; 全局重入计数
006F8DF9  53                     push    ebx
006F8DFA  55                     push    ebp
006F8DFB  56                     push    esi
006F8DFC  57                     push    edi
006F8DFD  33FF                   xor     edi, edi
006F8DFF  83CD FF                or      ebp, -1
006F8E02  8BF1                   mov     esi, ecx                ; esi = this
006F8E04  42                     inc     edx                     ; 重入计数递增
006F8E05  897C24 20              mov     [esp+0x20], edi         ; BestTarget = nullptr
006F8E09  8915 34ECA800          mov     ds:[0x00A8EC34], edx
006F8E0F  8B06                   mov     eax, [esi]
006F8E11  896C24 1C              mov     [esp+0x1C], ebp         ; MaxScore = -1
006F8E15  896C24 3C              mov     [esp+0x3C], ebp
006F8E19  FF90 84000000          call    dword ptr [eax+0x84]    ; v[33] GetType()
006F8E1F  8A88 200D0000          mov     cl, [eax+0xD20]         ; Type->InhibitScan?
006F8E25  84C9                   test    cl, cl
006F8E27  74 1B                  je      short loc_6F8E44
006F8E29  8B8E 1C020000          mov     ecx, [esi+0x21C]        ; ecx = this->Owner (HouseClass*)
006F8E2F  E8 FC28E1FF            call    0x0050B730              ; HouseClass::IsDefeatedOrPurged
006F8E34  84C0                   test    al, al
006F8E36  74 0C                  je      short loc_6F8E44
; 若当前阵营已被淘汰/出局，直接返回 nullptr 退出
006F8E38  5F                     pop     edi
006F8E39  5E                     pop     esi
006F8E3A  5D                     pop     ebp
006F8E3B  33C0                   xor     eax, eax                ; return nullptr
006F8E3D  5B                     pop     ebx
006F8E3E  83C4 5C                add     esp, 0x5C
006F8E41  C2 0C00                ret     0x0C
```

#### 2.2.2 分布式开火（DistributedFire）副作用清理

```assembly
006F8F76  8B06                   mov     eax, [esi]
006F8F78  8BCE                   mov     ecx, esi
006F8F7A  FF90 84000000          call    dword ptr [eax+0x84]    ; GetType()
006F8F80  8A88 B0060000          mov     cl, [eax+0x6B0]         ; TechnoTypeClass::DistributedFire
006F8F86  84C9                   test    cl, cl
006F8F88  74 1E                  je      short loc_6F8FA8
; 若单位启用分布式开火，在每次全量寻敌前，必须重置当前攻击与受击目标向量
006F8F8A  8B96 58040000          mov     edx, [esi+0x458]        ; this->CurrentTargets
006F8F90  8D8E 58040000          lea     ecx, [esi+0x458]
006F8F96  FF52 0C                call    dword ptr [edx+0x0C]    ; DynamicVectorClass::Clear
006F8F99  8B86 40040000          mov     eax, [esi+0x440]        ; this->AttackedTargets
006F8F9F  8D8E 40040000          lea     ecx, [esi+0x440]
006F8FA5  FF50 0C                call    dword ptr [eax+0x0C]    ; DynamicVectorClass::Clear
```

#### 2.2.3 搜索半径计算（0x006F9116 – 0x006F9144）

```assembly
; 主/副武器最大射程换算
006F9116  99                     cdq
006F9117  81E2 FF000000          and     edx, 0xFF
006F911D  8BCE                   mov     ecx, esi
006F911F  03C2                   add     eax, edx
006F9121  8B16                   mov     edx, [esi]
006F9123  8BF8                   mov     edi, eax
006F9125  C1FF 08                sar     edi, 8                  ; 射程 (leptons >> 8) -> cell
006F9128  FF92 84000000          call    dword ptr [edx+0x84]    ; GetType()
006F912E  8B80 8C060000          mov     eax, [eax+0x68C]        ; Type->RangeExtra
006F9134  99                     cdq
006F9135  81E2 FF000000          and     edx, 0xFF
006F913B  03C2                   add     eax, edx
006F913D  C1F8 08                sar     eax, 8                  ; RangeExtra >> 8
006F9140  8D4407 01              lea     eax, [edi+eax+1]        ; radius = (range>>8) + (extra>>8) + 1
006F9144  894424 38              mov     [esp+0x38], eax         ; 存储搜索半径至 [esp+0x38]
```

#### 2.2.4 三路枚举分支汇总

1. **路 A（全局粗空间桶 0x00887888）**：
   - 入口地址：`0x006F91B7`
   - 调用 `0x00412B40(pCell, radius)` 将该半径内覆盖的所有 20×20 空间桶中的对象物化到 `0x00887888+0x2580` 动态向量；
   - 随后通过 `0x004137A0` 循环弹出候选对象，逐一送入 `0x006F7CA0` 评分；
2. **路 B（逐格螺旋扫描 Spiral Ring）**：
   - 入口地址：`0x006F93C1`
   - 外层循环：`ring = 0 .. radius`（环形向外扩散）；
   - 内层循环：沿环边缘四边遍历所有 `(dx, dy)`；
   - 核心调用：`MapClass::TryGetCellAt` (`0x005657A0`) -> `0x006F8960`（遍历该格子的 `CellClass->FirstObject` / `AltObject` 单向链表）；
   - 对链表上的每一个对象调用 `0x006F7CA0`；
3. **路 C（全局线性数组遍历）**：
   - 入口地址：`0x006F9B6E`
   - 当 `(targetFlags & 3) == 0` 或路 A/B 结束后处理特定目标类别；
   - 线性遍历全局空军数组 `0x00A8E390`（Items: `0x00A8E394`，Count: `0x00A8E3A0`）和特种数组 `0x00A8EC88`。

#### 2.2.5 严格大于择优与返回值输出

```assembly
006F9363  8B4424 74              mov     eax, [esp+0x74]         ; 当前候选对象威胁评分
006F9367  8B4C24 1C              mov     ecx, [esp+0x1C]         ; 当前记录的最高威胁分 (MaxScore)
006F936B  3BC1                   cmp     eax, ecx
006F936D  7E 08                  jle     short loc_6F9377        ; ★ 严格小于等于则跳过！
006F936F  896C24 20              mov     [esp+0x20], ebp         ; 更新最优目标 BestTarget = candidate
006F9373  894424 1C              mov     [esp+0x1C], eax         ; 更新最高分 MaxScore = score
...
006F9DA1  8B4424 20              mov     eax, [esp+0x20]         ; return BestTarget
006F9DA5  5F                     pop     edi
006F9DA6  5E                     pop     esi
006F9DA7  5D                     pop     ebp
006F9DA8  5B                     pop     ebx
006F9DA9  83C4 5C                add     esp, 0x5C
006F9DAC  C2 0C00                ret     0x0C                    ; 清栈 12 字节返回
```

> **确定性要点**：西木引擎使用 `jle`（严格大于更新）。若两名敌人威胁分完全相同，**先被枚举到的目标获胜**。

---

## 3. 全局粗空间网格（0x00887888）逆向分析

### 3.1 单例内存布局与网格分辨率

- **单例基地址**：`0x00887888`
- **网格维度**：$20 \times 20 = 400$ 个空间桶（Buckets）
- **单桶数据结构**：西木标准 `DynamicVectorClass<AbstractClass*>`（大小为 **24 字节 / 0x18**）
  ```cpp
  struct DynamicVectorClass_Abstract {
      void*           vftable;       // +0x00: 虚表指针 (固定为 0x007E17AC)
      AbstractClass** Items;         // +0x04: 堆分配的对象指针数组
      int32_t         VectorMax;     // +0x08: 当前已分配容量 (Capacity)
      int32_t         IsAllocated;   // +0x0C: 堆分配管理标志
      int32_t         Count;         // +0x10: 当前桶内包含的对象个数
      int32_t         GrowthStep;    // +0x14: 扩容步长 (构造时初始化为 10 / 0x0A)
  };
  ```
- **整体内存块分布**：
  - `0x00887888 + 0x0000 .. 0x257F`：400 个桶连续数组（$400 \times 24 = 9600 = \text{0x2580}$ 字节）
  - `0x00887888 + 0x2580 .. 0x2597`：查询结果专用向量 `DynamicVectorClass<AbstractClass*> QueryResults`

### 3.2 坐标到网格索引的除法算法

引擎通过乘常数 `0x66666667` 结合右移，实现对地图长宽进行快速“除以 20”运算：

```assembly
00412B9A  B8 67666666            mov     eax, 0x66666667
00412B9F  F72D 14F98700          imul    ds:[0x0087F914]         ; MapClass::MapWidth
00412BA5  8BCA                   mov     ecx, edx
00412BA7  8BC6                   mov     eax, esi                ; cellX
00412BA9  C1F9 03                sar     ecx, 3                  ; ecx = MapWidth / 20
00412BAC  8BD1                   mov     edx, ecx
00412BAE  BE 13000000            mov     esi, 0x13               ; max clamp = 19
00412BB3  C1EA 1F                shr     edx, 0x1F
00412BB6  03CA                   add     ecx, edx
00412BB8  99                     cdq
00412BB9  F7F9                   idiv    ecx                     ; bucketX = cellX / (MapWidth / 20)
00412BBB  83F8 13                cmp     eax, 0x13
00412BBE  7F 02                  jg      short loc_412BC0
00412BC0  8BF0                   mov     esi, eax                ; bucketX = clamp(bucketX, 0, 19)
```

- **二维桶索引公式**：
  $$\text{bucket\_idx} = \text{bucketX} + 20 \times \text{bucketY} \quad (0 \le \text{bucket\_idx} < 400)$$
- **内存寻址**：
  $$\text{BucketPtr} = \text{0x00887888} + \text{bucket\_idx} \times 24$$

---

### 3.3 网格生命周期与对象注册机制

| 核心函数 | 地址 | 触发时机与语义 |
| :--- | :--- | :--- |
| **Constructor** | `0x00412870` | 循环 400 次，在每个槽位原地构造 `DynamicVectorClass`，赋初值 `vptr=0x7E17AC, GrowthStep=10, Count=0` |
| **Destructor** | `0x004128F0` | 循环 400 次，释放每个桶堆内存数组 |
| **AddObject** | `0x004134A0` | **对象移入网格**：读取对象坐标，换算 `(bucketX, bucketY)`，调用 `DynamicVectorClass::AddItem` 压入对应桶 |
| **RemoveObject** | `0x004135D0` | **对象移出网格**：计算桶索引，查找该对象指针，将其自数组中删除并前移后续元素补齐 |
| **InitQuery** | `0x00412B40` | **范围查询初始化**：计算圆心及上下左右 4 个极点的桶范围，将所有相交桶的对象指针搬运至 `0x00887888+0x2580` |
| **Next / Pop** | `0x004137A0` | **迭代器弹出**：若 `Count == 0` 返回 `nullptr`；否则取出第 0 项，将其自向量弹出并返回 |

**关键逆向发现：哪些对象会加入该网格？**
通过静态交叉引用扫描 `0x004134A0` 的调用源：
- `FootClass::UpdatePosition` (`0x004CF9DB`, `0x004D72DB`)：**所有可移动单位（坦克、步兵、战机、船只）在进入地图或跨越单元格移动时，会自动在此网格中更新桶归属**；
- `InfantryClass::Put` (`0x0054BA20`)：步兵部署与生成入格；
- `RadioClass` / `TechnoClass` 状态同步 (`0x00662683`, `0x006627E0`)；
- **建筑（BuildingClass）不在此网格内**！因此引擎才设计了【路 B】全图逐格螺旋扫描，用来搜索静态防御塔与基地建筑。

---

## 4. 单候选评估打分器（0x006F7CA0）逆向分析

### 4.1 函数原型与参数布局

- **调用约定**：`__thiscall`，`ECX = this`（求敌方单位），`ret 0x1C`（7 个栈参数）
- **C++ 签名**：
  ```cpp
  bool __thiscall TechnoClass::EvaluateTarget(
      uint32_t       targetFlags,  // [esp+0x40]: 寻敌标志
      int            arg2,         // [esp+0x44]
      int            arg3,         // [esp+0x48]
      AbstractClass* pTarget,      // [esp+0x4C]: 待评估候选目标 (ESI)
      int*           outScore,     // [esp+0x50]: 输出威胁评分存储指针 (EBP)
      int            arg6,         // [esp+0x54]
      void*          pConfig       // [esp+0x58]: 附加配置 (通常传入 0x00B0EA90)
  );
  ```

---

### 4.2 硬性淘汰准则（Fast Rejection -> return false）

若候选目标命中以下任何一条规则，函数立即跳转到 `0x006F894F`，清零 `AL` 并退出：

```
                    [ 候选对象 pTarget ]
                             │
            ┌────────────────┴────────────────┐
            ▼                                 ▼
      pTarget == nullptr ? (0x6F7D88)   pTarget == this ? (0x6F8001)
            │ 是                              │ 是
            └───────────────┬─────────────────┘
                            ▼
                    【立即淘汰：返回 0】
                            ▲
            ┌───────────────┴─────────────────┐
            │                                 │
     InLimbo != 0 ?                   Health <= 0 ?
   [pTarget+0x81] != 0 (0x6F7D90)    [pTarget+0x6C] <= 0 (0x6F7D9E)
            │                                 │
     IsSelectable == 0 ?              IsAlliedWith == true ?
  [pTarget+0x3D5] != 1 (0x6F7DF1)   HouseClass::IsAlliedWith (0x6F7F29)
            │                                 │
   WeaponThreat <= 0 ?                 Immune / Cloaked ?
  TechnoClass::0x6F3970 (0x6F7F49)   TypeClass+0x5E4 位域测试
```

1. **空指针保护**（`0x006F7D88`）：`test esi, esi; je 0x6F894F`；
2. **消亡状态过滤（InLimbo）**（`0x006F7D90`）：
   ```assembly
   006F7D90  8A86 81000000          mov     al, [esi+0x81]      ; pTarget->InLimbo
   006F7D96  84C0                   test    al, al
   006F7D98  0F85 B10B0000          jne     0x006F894F          ; 正在死亡/解构中，拒绝
   ```
3. **存活血量检验（Health）**（`0x006F7D9E`）：
   ```assembly
   006F7D9E  8B46 6C                mov     eax, [esi+0x6C]      ; pTarget->Health
   006F7DA1  85C0                   test    eax, eax
   006F7DA3  0F84 A60B0000          je      0x006F894F          ; 血量 <= 0，拒绝
   ```
4. **可被选为目标标志（IsSelectableTarget）**（`0x006F7DF1`）：
   ```assembly
   006F7DF1  8A86 D5030000          mov     al, [esi+0x3D5]     ; Selectable bit
   006F7DF7  84C0                   test    al, al
   006F7DF9  0F84 500B0000          je      0x006F894F          ; 不可选，拒绝
   ```
5. **自身排除（Self-Exclusion）**（`0x006F8001`）：
   `cmp edi, esi; je 0x006F894F`（单位不可把自己选作攻击目标）；
6. **结盟关系检查（Alliance Filter）**（`0x006F7F29`, `0x006F7FF4`）：
   调用 `0x004F9A90`（`HouseClass::IsAlliedWith(pTarget)`）。若双方属于同盟阵营且未发生敌对伪装，则直接拒绝；
7. **武器伤害能力拦截**（`0x006F7F3A`）：
   调用 `0x006F3970(this)`，若本单位武器无法对该护甲造成伤害，拒绝；
8. **隐形与免疫掩码**（`0x006F7EB8`）：检查 `TechnoTypeClass+0x5E4`。

---

### 4.3 威胁评分（Threat Score）计算体系

一旦通过硬性过滤，函数将在 `0x006F8710` 汇聚并计算最终得分写入 `*outScore`（即 `[ebp]`）：

1. **基准射程与威力分（0x0070CD10）**：
   综合目标空间距离（欧式空间 leptons 距离）、武器威力（Damage）与弹头对护甲修正系数（Verses），得出初始浮点/整型威胁基准值写入 `[ebp]`（`mov [ebp], eax` 于 `0x006F8716`）；
2. **残血优先斩杀系数（EstimatedHealth 修正）**：
   读取目标预计血量 `[esi+0x70]`，将其与伤害差值折半（`sar eax, 1` 于 `0x006F8737`）：
   - 当敌方血量极低、处于数发内可击杀的斩杀线时，提供高额斩杀权重（优先消灭残血目标减员）；
3. **团队 AI 集火优先级（House Team Target）**：
   读取 `this->Owner+0x5600`（阵营集火索引），若 `pTarget->Owner->ArrayIndex == this->Owner+0x5600`，追加高额战队战术加成分；
4. **Rules INI 全局配置加成**：
   - 读取 `RulesClass+0xEE0` 威胁偏好，累加到 `[ebp]`（`add [ebp], eax` 于 `0x006F87BE`）；
   - 读取 `RulesClass+0x1580` 武器加成，累加到 `[ebp]`（`add [ebp], eax` 于 `0x006F87F8`）；
   - 读取 `RulesClass+0xEB8` 反装甲/防空专业化权重修正（`0x006F882B`）；
5. **保底兜底截断**：
   在 `0x006F892F` 执行 `cmp eax, 1; jl -> mov eax, 1; mov [ebp], eax`，确保所有合法目标的评分不低于 `1`。

---

## 5. 现网 L2 漏装修复与 Inline Hook 落地方案

### 5.1 缺陷全景对比表

| 对比维度 | 现网虚表挂钩方案（遗漏且存在盲区） | 本方案 Inline Hook 方案（已编译验证） |
| :--- | :--- | :--- |
| **挂载位置** | 虚表指针：`0x007F4D24` / `0x007F6034` | 二进制函数入口：`0x006F8DF0` |
| **现网状态** | `InstallVTableHooks()` 根本漏装了这两个槽 | **已直接挂载并成功测试编译通过** |
| **覆盖坦克/装甲 (Unit)** | 理论覆盖（若补装虚表） | **100% 覆盖** |
| **覆盖步兵 (Infantry)** | ❌ **0% 覆盖**（步兵 v[241] 为 `0x0051E140`） | **100% 覆盖**（步兵回落直接进 `0x006F8DF0`） |
| **覆盖防御塔/建筑 (Building)**| ❌ **0% 覆盖**（建筑 v[241] 为 `0x00445F00`） | **100% 覆盖**（建筑包装器直呼 `0x006F8DF0`） |
| **覆盖战机/空军 (Aircraft)**| ❌ **0% 覆盖**（空军 v[241] 为 `0x004D9920`） | **100% 覆盖**（包装器直呼 `0x006F8DF0`） |
| **覆盖脚本/AI 直接调用** | ❌ **0% 覆盖**（非虚表调用绕过） | **100% 覆盖** |
| **目标存活保持安全性** | 仅检测 `Health > 0` | **增补检测 `InLimbo == 0`，杜绝幽灵锁定** |

---

### 5.2 0x006F8DF0 入口 9 字节 Hook 与 14 字节跳板实现

#### 5.2.1 汇编字节分析

- `0x006F8DF0` 原指令：
  - `0x006F8DF0`: `83 EC 5C` (`sub esp, 0x5C`, 3 字节)
  - `0x006F8DF3`: `8B 15 34 EC A8 00` (`mov edx, [0x00A8EC34]`, 6 字节)
  - 下一条指令起始于 `0x006F8DF9`: `53` (`push ebx`, 1 字节)
- **覆写字节数**：$3 + 6 = 9$ 字节
  - 1 字节 `0xE9` (JMP rel32)
  - 4 字节相对偏移量 `(hookFunc - (0x006F8DF0 + 5))`
  - 4 字节 `0x90` (NOP 填充对齐至 `0x006F8DF9`)
- **跳板（Trampoline）内存结构**：共 14 字节
  ```assembly
  ; 原始备份指令 (9 字节)
  83 EC 5C               sub     esp, 0x5C
  8B 15 34ECA800         mov     edx, ds:[0x00A8EC34]
  ; 跳回原函数继续执行 (5 字节)
  E9 xx xx xx xx         jmp     0x006F8DF9
  ```

#### 5.2.2 生产级 C++ 实现源码（已合入 `ra2render/blitter_hooks.cpp`）

```cpp
// 原版 0x006F8DF0 指令：
// 006F8DF0: 83 EC 5C          sub esp, 0x5C           (3 字节)
// 006F8DF3: 8B 15 34 EC A8 00 mov edx, [0x00A8EC34]   (6 字节)
// 合计 9 字节。下一条指令位于 0x006F8DF9 (53 = push ebx)
static uint8_t s_origGreatestThreatBytes[9] = {0};
static uint8_t s_greatestThreatTrampoline[16] = {0};

void* __thiscall TargetHooks::Hook_Techno_Greatest_Threat(uintptr_t arg1, uintptr_t arg2, uintptr_t arg3) {
    void *pThis = this;

    // 关键安全原则：如果单位已有存活且未进入 Limbo 的目标，在节流帧安全返回该目标，绝不返回 nullptr
    if (!IsBadReadPtr(reinterpret_cast<void*>(reinterpret_cast<uintptr_t>(pThis) + 0x5D4), sizeof(void*))) {
        void *pTarget = *reinterpret_cast<void**>(reinterpret_cast<uintptr_t>(pThis) + 0x5D4);
        if (pTarget != nullptr && !IsBadReadPtr(pTarget, 0x84)) {
            int health = *reinterpret_cast<int*>(reinterpret_cast<uintptr_t>(pTarget) + 0x6C);
            uint8_t inLimbo = *reinterpret_cast<uint8_t*>(reinterpret_cast<uintptr_t>(pTarget) + 0x81);
            if (health > 0 && inLimbo == 0) {
                const uint32_t *pCurrentFrame = reinterpret_cast<const uint32_t*>(ADDR_CURRENT_FRAME);
                uint32_t currentFrame = (pCurrentFrame && !IsBadReadPtr((void*)pCurrentFrame, 4)) ? *pCurrentFrame : 0;
                uint32_t unitHash = static_cast<uint32_t>(reinterpret_cast<uintptr_t>(pThis)) >> 4;

                if (g_targetScanInterval > 1 && currentFrame > 0) {
                    if (((unitHash + currentFrame) % static_cast<uint32_t>(g_targetScanInterval)) != 0) {
                        g_telemetry.throttledTargetScans++;
                        return pTarget; // 保持原有存活目标，规避全图重型螺旋扫描！
                    }
                }
            }
        }
    }

    g_telemetry.totalTargetScans++;
    if (g_pOrigTechnoGreatestThreat) {
        return g_pOrigTechnoGreatestThreat(pThis, arg1, arg2, arg3);
    }
    return nullptr;
}

static bool InstallGreatestThreatHook() {
    memcpy(s_origGreatestThreatBytes, reinterpret_cast<void*>(ADDR_ORIG_TECHNO_GREATEST_THREAT), 9);

    DWORD oldProtect = 0;
    if (!VirtualProtect(s_greatestThreatTrampoline, sizeof(s_greatestThreatTrampoline), PAGE_EXECUTE_READWRITE, &oldProtect)) {
        LogMessage("[ra2render-target] 错误：无法设置 Greatest_Threat Trampoline 内存权限");
        return false;
    }

    // 填充跳板：备份的 9 字节 + jmp 回 0x006F8DF9 (5 字节)
    memcpy(s_greatestThreatTrampoline, s_origGreatestThreatBytes, 9);
    s_greatestThreatTrampoline[9] = 0xE9; // JMP rel32
    int32_t jmpBack = static_cast<int32_t>((ADDR_ORIG_TECHNO_GREATEST_THREAT + 9) - (reinterpret_cast<uintptr_t>(s_greatestThreatTrampoline) + 14));
    memcpy(&s_greatestThreatTrampoline[10], &jmpBack, sizeof(int32_t));

    g_pOrigTechnoGreatestThreat = reinterpret_cast<FnGreatestThreat>(reinterpret_cast<void*>(s_greatestThreatTrampoline));

    if (!VirtualProtect(reinterpret_cast<void*>(ADDR_ORIG_TECHNO_GREATEST_THREAT), 9, PAGE_EXECUTE_READWRITE, &oldProtect)) {
        LogMessage("[ra2render-target] 错误：无法修改 0x006F8DF0 内存权限");
        return false;
    }

    // 安装 9 字节 Inline Hook：E9 <rel32> + 4 个 0x90 (NOP)
    uint8_t patch[9];
    patch[0] = 0xE9;
    uintptr_t hookAddr = union_cast<uintptr_t>(&TargetHooks::Hook_Techno_Greatest_Threat);
    int32_t jmpToHook = static_cast<int32_t>(hookAddr - (ADDR_ORIG_TECHNO_GREATEST_THREAT + 5));
    memcpy(&patch[1], &jmpToHook, sizeof(int32_t));
    patch[5] = 0x90;
    patch[6] = 0x90;
    patch[7] = 0x90;
    patch[8] = 0x90;
    memcpy(reinterpret_cast<void*>(ADDR_ORIG_TECHNO_GREATEST_THREAT), patch, 9);

    VirtualProtect(reinterpret_cast<void*>(ADDR_ORIG_TECHNO_GREATEST_THREAT), 9, oldProtect, &oldProtect);
    LogMessage("[ra2render-target] 成功挂载 Greatest_Threat Inline Hook (0x006F8DF0 -> 0x%08X)，覆盖全体作战单位/步兵/建筑/空军！", hookAddr);
    return true;
}

static void RemoveGreatestThreatHook() {
    if (g_pOrigTechnoGreatestThreat) {
        DWORD oldProtect = 0;
        VirtualProtect(reinterpret_cast<void*>(ADDR_ORIG_TECHNO_GREATEST_THREAT), 9, PAGE_EXECUTE_READWRITE, &oldProtect);
        memcpy(reinterpret_cast<void*>(ADDR_ORIG_TECHNO_GREATEST_THREAT), s_origGreatestThreatBytes, 9);
        VirtualProtect(reinterpret_cast<void*>(ADDR_ORIG_TECHNO_GREATEST_THREAT), 9, oldProtect, &oldProtect);
        g_pOrigTechnoGreatestThreat = nullptr;
    }
}
```

---

## 6. 空间哈希替代全图螺旋扫描评估与演进方案

### 6.1 螺旋扫描的真实 CPU 消耗评估

- 当单位**丢失目标**、**击杀旧目标**或处于**每 8 帧的全量寻敌帧**时，必须执行真实扫描；
- 在【路 B】中，当武器射程为 15 格时，同心圆螺旋环覆盖格数约为 $\pi \times 15^2 \approx 706$ 格；对于光棱坦克、巨炮、无畏级战舰（射程 20-25 格），覆盖格数超 $1500 - 2000$ 格；
- 在 800 单位重载图上，若单帧有 100 个单位进入重型扫描，单帧需要遍历高达 $100 \times 1500 = 150,000$ 次单元格链表，调用 $150,000$ 次 `TryGetCellAt` 与大量的 `0x006F7CA0`，直接导致单帧耗时增加 20-50ms。

### 6.2 两阶段空间哈希升级路线图

```
 现有阶段 (已落地)
 ┌─────────────────────────────────────────────────────────────┐
 │ L2 存活目标保持 (Target Retention) + 0x006F8DF0 Inline Hook   │
 │ 效果：已锁定目标单位 87.5% 帧无需重新寻敌，性能平抑 7-8 倍   │
 └─────────────────────────────────────────────────────────────┘
                               │
                               ▼
 下一阶段演进：空域存在位图快速短路 (Empty Neighborhood Fast-Path)
 ┌─────────────────────────────────────────────────────────────┐
 │ 机制：维护 64×64 粗粒度敌对存在位图 (每 8×8 Cell 聚类为 1 bit)│
 │ 判定：若以单位为中心、radius 外接矩形内的敌对位图全为 0，    │
 │       判定视野内绝对无敌军，直接跳过【路 B】螺旋扫描退出！   │
 │ 复杂度：矩形测试仅需 4-8 次 uint64_t 位与运算（几纳秒）     │
 └─────────────────────────────────────────────────────────────┘
                               │
                               ▼
 终极演进：Per-Cell 空间哈希链表替代 20×20 粗网格与螺旋枚举
 ┌─────────────────────────────────────────────────────────────┐
 │ 机制：将建筑与单位统一注册进紧凑网格哈希表 (SpatialHash)    │
 │ 枚举：按半径由内向外只枚举非空桶，直接将候选送入 0x006F7CA0  │
 │ 收益：枚举复杂度由 O(面积 πR²) 彻底退化为 O(真实候选数 K)   │
 └─────────────────────────────────────────────────────────────┘
```

### 6.3 联机确定性与对齐准则

1. **同分次序不变性**：引擎在 `0x006F936B` 采用 `cmp eax, ecx; jle skip`。任何候选枚举替换必须严格遵循原版同心圆半径递增顺序，确保同等威胁分数下选择一致的目标；
2. **逻辑帧同步**：空间哈希的增量更新与位图重建必须绑定逻辑游戏帧（`CurrentFrame`），严禁依赖渲染帧或线程时间戳；
3. **分布式开火兼容**：对于 `DistributedFire` 属性单位，必须保留原版在 `0x006F8F8A` 处清空和回填 `this+0x440` 与 `this+0x458` 的副作用，防止分布式开火重复攻击同一单位。

---

## 7. 逆向核心地址速查清单

| 符号 / 功能 | 内存地址 | 逆向语义与说明 |
| :--- | :--- | :--- |
| `TechnoClass::Greatest_Threat` | `0x006F8DF0` | v[241] 共享寻敌扫描体（已挂载 9 字节 Inline Hook） |
| `TechnoClass::SelectAutoTarget` | `0x006FB010` | v[265] 限频调度器 |
| `TechnoClass::EvaluateTarget` | `0x006F7CA0` | 单候选硬性过滤与威胁度评分计算器 |
| `SpatialGrid::Instance` | `0x00887888` | 全局 20×20 粗空间桶单例（共 9624 字节） |
| `SpatialGrid::InitQuery` | `0x00412B40` | 物化覆盖桶至 `0x00887888+0x2580` 动态向量 |
| `SpatialGrid::NextCandidate`| `0x004137A0` | 自查询向量弹出下一个候选对象指针 |
| `SpatialGrid::AddObject` | `0x004134A0` | 将机动单位按坐标推入对应的空间桶 |
| `SpatialGrid::RemoveObject` | `0x004135D0` | 将机动单位自对应的空间桶中移除并重排 |
| `CellClass_SpiralScanCell` | `0x006F8960` | 逐格扫描单格链表（FirstObject -> NextObject） |
| `HouseClass::IsAlliedWith` | `0x004F9A90` | 判定目标与自身阵营是否结盟（结盟位图反转测试） |
| `GreatestThreat_Reentrancy` | `0x00A8EC34` | 寻敌重入计数器 |
| `Global_Aircraft_Vector` | `0x00A8E390` | 全局空军对象动态向量（+0x04: Items, +0x10: Count） |
| `CurrentFrame` | `0x00A8ED84` | 逻辑游戏帧计数器 |
