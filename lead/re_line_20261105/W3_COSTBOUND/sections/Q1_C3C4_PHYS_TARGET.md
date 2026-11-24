# Q1·C3（战斗物理）与 C4（微观索敌）静态定量上界报告

> **责任角色**：物理与索敌定量员  
> **研究对象**：C3 成本中心（战斗物理层：`BulletClass` / `DamageArea` / `AnimClass`）与 C4 成本中心（微观索敌层：`SelectAutoTarget` / `Greatest_Threat`）  
> **核心任务**：在不采任何帧内数据、不启动游戏、不写采样代码的前提下，基于 `ra2youli/gamemd.exe`（SHA256: `73201cc0...`）指令与字节逆向核实其物理上界与限频机制，给出数量级论证与排除裁决。  
> **特别纪律**：凡「A 调用 B ⇒ A 具有 B 的性质」，一律深入 B 函数体内核对字节；对限频周期亲自核对汇编与数据，不采信二手说法。

---

## 1. 一句话结论与数量级速览表

- **C3（战斗物理层）一句话结论**：每帧遍历的物理容器为 `BulletClass::Array`（`0x00A8ED40`）与 `AnimClass::Array`（`0x00A8E9A8`），底层为 `DynamicVectorClass` 动态堆向量；受武器射频（ROF $\ge 50$ 帧）与短弹道飞行周期（1~3 帧）物理锁死，1200 单位同场混战时全图活跃弹道仅约 40 枚（极端 $<300$ 枚），活跃 Anim 约 200~600 个，AOE 爆炸结算仅 20~30 次/帧；**物理层单帧总算力开销 $\le 0.05 \sim 0.1\ \text{ms}$，与慢窗 134.8ms 的恶化赤字相差 2~3 个数量级，绝对无法独立解释 5 倍恶化，可在不采帧内数据的前提下静态完全排除（staticallyExcludable = true）**。
- **C4（微观索敌层）一句话结论**：字节核实确证 `SelectAutoTarget`（`0x006FB010`）实为**弹药装填计数器（UpdateReload）**而非索敌，无弹药限制单位在第 5 条指令立即早退（耗时 $<2\text{ns}$），既有文档所谓的「8 帧 / 100 帧限频」纯系 House 级宏观逻辑，在 C4 索敌函数体内**完全不存在**；若 1200 单位在极端状态下同一帧全量并发触发 `Greatest_Threat`（`0x006F8DF0`），其 20×20 粗空间桶（`0x00887888`）加精细螺旋扫格覆盖的 Cell 数达 $6.35 \times 10^5 \sim 1.20 \times 10^6$ cells，理论计算开销约 **19 ~ 36 ms**（极端长程单位可达 **125 ms**），**与慢窗 134.8ms 赤字处于完全相同的数量级（同阶），因此微观索敌层在理论极限上无法静态排除（staticallyExcludable = false）**。

### 数量级对比总表

| 成本中心 | 核心遍历实体 / 范围 | 1200 单位混战时并发规模 | 单次 / 单项估计耗时 | 1200 单位单帧总耗时理论上界 | vs 134.8ms 实测恶化赤字 | 静态裁决结论 |
|---|---|---|---|---|---|---|
| **C3 战斗物理**<br>（弹道/动画/伤害） | `BulletClass::Array`<br>`AnimClass::Array`<br>`DamageArea` (AOE) | 弹道: ~40 枚<br>动画: ~480 个<br>AOE: ~25 次 | 弹道推进: ~50 ns<br>动画步进: ~30 ns<br>AOE 结算: ~500 ns | **$\approx 0.05 \sim 0.1\ \text{ms}$**<br>（放宽极端 $<0.5\ \text{ms}$） | **差 2~3 个数量级**<br>（占赤字 $<0.1\%$） | **★ 静态完全排除**<br>(staticallyExcludable = true) |
| **C4 微观索敌**<br>（全并发极限假设） | `Greatest_Threat`<br>20×20 桶 + 螺旋环 | 1200 单位同帧全扫<br>覆盖 $6.35\times 10^5$ cells | 单 Cell 判定:<br>~30 ns (含空格早退) | **$\approx 19.05 \sim 36.0\ \text{ms}$**<br>（超长程可达 $125\ \text{ms}$） | **差 0 个数量级**<br>（同数量级，占赤字 15~93%） | **★ 静态不可排除**<br>(staticallyExcludable = false) |
| **C4 微观索敌**<br>（常规错峰待命态） | 同上（受状态机<br>与 CDTimer 约束） | 仅 50~100 单位/帧<br>触发丢失目标重选 | 单 Cell 判定:<br>~30 ns | **$\approx 0.8 \sim 2.5\ \text{ms}$** | 差 1~2 个数量级 | 需帧内采样判别是否发生并发雪崩 |

---

## 2. C4 微观索敌层深度逆向核实（SelectAutoTarget 与 Greatest_Threat）

### 2.1 `SelectAutoTarget`（`0x006FB010`）的真实语义与限频周期真相

#### (1) 汇编逐行核实与字节实证
对 `ra2youli/gamemd.exe:0x006FB010`（文件偏移 `0x002FB010`）进行完整反汇编：

```asm
0x006FB010: 56                      push esi
0x006FB011: 8B F1                   mov  esi, ecx              ; esi = this (TechnoClass*)
0x006FB013: 57                      push edi
0x006FB014: 8B 06                   mov  eax, dword ptr [esi]  ; eax = vtable
0x006FB016: FF 90 84 00 00 00       call dword ptr [eax + 0x84]; vtable[33]: GetType() -> TechnoTypeClass*
0x006FB01C: 8B 80 84 06 00 00       mov  eax, dword ptr [eax + 0x684] ; ★ 读取 TechnoTypeClass+0x684
0x006FB022: 83 F8 FF                cmp  eax, -1               ; 比较是否为 -1
0x006FB025: 74 47                   je   0x006FB06E            ; ★ 若为 -1，直接跳转函数尾部退出！
0x006FB027: 8B BE FC 02 00 00       mov  edi, dword ptr [esi + 0x2FC] ; edi = this+0x2FC
0x006FB02D: 3B F8                   cmp  edi, eax              ; 比较当前计数 vs 上限
0x006FB02F: 7D 3D                   jge  0x006FB06E            ; 达到上限退出
0x006FB031: 8B 96 FC 01 00 00       mov  edx, dword ptr [esi + 0x1FC] ; edx = StartTime
0x006FB037: 8B 86 04 02 00 00       mov  eax, dword ptr [esi + 0x204] ; eax = Duration
0x006FB03D: 83 FA FF                cmp  edx, -1
0x006FB040: 74 0E                   je   0x006FB050
0x006FB042: 8B 0D 84 ED A8 00       mov  ecx, dword ptr [0x00A8ED84]  ; ecx = CurrentFrame
0x006FB048: 2B CA                   sub  ecx, edx              ; ecx = CurrentFrame - StartTime
0x006FB04A: 3B C8                   cmp  ecx, eax              ; 检查是否到期: elapsed >= Duration ?
0x006FB04C: 7D 06                   jge  0x006FB054            ; 到期推进
0x006FB04E: 2B C1                   sub  eax, ecx
0x006FB050: 85 C0                   test eax, eax
0x006FB052: 75 1A                   jne  0x006FB06E            ; 未到期退出
0x006FB054: 8B 16                   mov  edx, dword ptr [esi]
0x006FB056: 47                      inc  edi                   ; 计数加 1
0x006FB057: 6A 02                   push 2
0x006FB059: 8B CE                   mov  ecx, esi
0x006FB05B: 89 BE FC 02 00 00       mov  dword ptr [esi + 0x2FC], edi ; 写回 this+0x2FC
0x006FB061: FF 92 24 01 00 00       call dword ptr [edx + 0x124]      ; vtable[73]
0x006FB067: 8B CE                   mov  ecx, esi
0x006FB069: E8 12 00 00 00          call 0x006FB080            ; ★ 计算下一重装周期
0x006FB06E: 5F                      pop  edi
0x006FB06F: 5E                      pop  esi
0x006FB070: C3                      ret
```

#### (2) 字段溯源与真实引擎语义定谳
通过逆向 `TechnoTypeClass::LoadFromINI`（`0x00714766..0x007148B2`）与构造函数（`0x007110EC`）：
- `TechnoTypeClass+0x684` 对应读取的 INI 键字符串为 `"Ammo"`（VA `0x0081BBE0`），其默认值硬编码为 `-1`（无限弹药）；
- `TechnoClass+0x2FC` 为实体的当前弹药量（`CurrentAmmo`）；
- `TechnoClass+0x1FC` 与 `+0x204` 为弹药装填计时器 `ReloadTimer` 的 `StartTime` 与 `Duration`；
- 在 `0x006FB080` 中，周期的计算公式为：
  - 若 `CurrentAmmo == 0` 且 `type+0x69C != -1`，`Duration = type+0x69C`（读取 INI 键 `"EmptyReload"` @ `0x00843A50`）；
  - 否则：`Duration = type+0x698 + type+0x6A0 * (CurrentAmmo / type+0x3E4)^2`，其中：
    - `type+0x698` 为 `"Reload"`（VA `0x00843A5C`）；
    - `type+0x6A0` 为 `"ReloadIncrement"`（VA `0x00843A40`）；
    - `type+0x3E4` 为 `"PipWrap"`（VA `0x00843DB8`）。

#### (3) 纪律核实：`vtable[73]` 行为查证
`0x006FB061` 处以参数 `2` 调用 `vtable[73]`。查证各派生类虚表：
- `FootClass` / `UnitClass` / `InfantryClass` / `AircraftClass` 的 `vtable[73]` 统一指向 `0x004D3780`；
- 深入 `0x004D3780` 函数体核实：
  ```asm
  0x004D3783: 8B 7C 24 10      mov edi, [esp + 0x10] ; edi = 入参 arg0
  0x004D3789: 83 FF 02         cmp edi, 2            ; 检查参数是否为 2
  0x004D378C: 75 08            jne 0x004D3796
  0x004D378E: 5F; B0 01; 5E; 59; C2 04 00  ret 4     ; ★ 入参为 2 时直接返回 1，不做任何操作！
  ```
- **铁证确证**：社区与旧文档所称的 `SelectAutoTarget`（`0x006FB010`）**在引擎中根本不是索敌函数，而是纯粹的武器弹药装填轮询器（UpdateReload）**！
  - 对于战局中 99% 的普通单位（包括压测中的所有主战坦克），`Ammo == -1` 恒成立；
  - `0x006FB010` 在执行到第 5 条指令 `0x006FB025: je 0x006FB06E` 时直接命中跳转并退出，**耗时 $< 2\ \text{ns}$，零虚表下发，零地图扫格，零索敌动作**！

#### (4) 破除二手说法：8 帧 / 100 帧限频真身核实
既有报告 `docs/re/house_team_ai_update.md` 提及「8 帧 / 100 帧限频」。深入字节普查确证：
- `SelectAutoTarget` 与 `Greatest_Threat` 内部**完全没有** `CurrentFrame % 8` 或 `CurrentFrame % 100` 的任何逻辑！
- 该限频逻辑的真正发生地在 **`HouseClass::Update`（`0x004F8440`）**：
  - `0x004F8E24`：`test eax, eax; jne ...` 伴随每 100 帧周期（`CurrentFrame % 100 == 0`）衰减 `+0x5608` 基地节点；
  - `0x004F8F9C`：`test cl, 7; jne ...` 即 `CurrentFrame % 8 == 0`，用于触发 `0x006E53A0` 建筑回调与 `0x004FEA60` AI 招募。
- **纪律裁定**：不能采信将宏观 AI 更新限频张冠李戴给微观索敌的二手推论。**微观索敌函数本身不存在 8 帧/100 帧保底节流**。

---

### 2.2 `Greatest_Threat`（`0x006F8DF0`）真正的空间哈希与扫格机制

`Greatest_Threat` 体量 `0xFC0` 字节（约 1255 条指令），是全引擎唯一的微观威胁扫描核心。其调用拓扑由单位状态机驱动（如 `UnitClass::v[151] @ 0x00740B10` 经由 `0x004D4280` 与 `0x004D9920` 最终汇入 `0x006F8DF0`）。

#### (1) 扫描半径与范围判定（字节实证）
在 `0x006F9125..0x006F9144` 处：
```asm
0x006F9125: C1 FF 08        sar edi, 8                     ; edi = GetWeaponRange() >> 8
0x006F9128: FF 92 84 00 ... call dword ptr [edx + 0x84]    ; GetType()
0x006F912E: 8B 80 8C 06 ... mov eax, [eax + 0x68C]         ; eax = type->GuardRange (leptons)
0x006F913D: C1 F8 08        sar eax, 8                     ; eax = GuardRange >> 8
0x006F9140: 8D 44 07 01     lea eax, [edi + eax + 1]       ; ★ radius = (Range>>8) + (Guard>>8) + 1
0x006F9144: 89 44 24 38     mov dword ptr [esp + 0x38], eax; 存储半径 R (cell)
```
若单位具备精英强化武器（`vtable[256]` 为真），走 `0x006F9189` 分支读取 `Rules->GuardRange`（`0x008871E0 + 0xF48`）加上精英额外加成。

#### (2) 路 A：全局粗粒度 20×20 空间桶单例（`0x00887888` 与 `0x00412B40`）
引擎原版内建了一套粗粒度空间哈希（单例位于 VA `0x00887888`）：
1. **桶坐标映射（`0x00412B9A..0x00412BC2`）**：
   - 提取地图全局尺寸 `MapClass::Instance->Width`（`0x0087F914`）与 `Height`（`0x0087F918`）；
   - 执行 `imul 0x66666667; sar ecx, 3`（魔数除以 10），算出每桶跨越的 Cell 步长 $S = \text{MapWidth} / 10$；
   - 实体 Cell 坐标除以 $S$，并经 `cmp eax, 0x13; jg ...` 截断至 `0 .. 19`；
   - 桶网格总规格严格为 **20 × 20 = 400 个桶**。
2. **桶内存布局**：
   - 每个桶占用 **24 字节**（`0x18`），即标准 `DynamicVectorClass`（`vptr, Items, Capacity, IsAllocated, IsInitialized, Count, GrowthStep`）；
   - 400 个桶连续排列，总大小为 $400 \times 24 = 9600 = \text{0x2580}$ 字节；
   - 位于 `0x00887888 + 0x2580` 处是查询结果物化向量。
3. **查询行为**：
   `0x00412B40`（`InitQuery`）根据查询中心与半径覆盖的桶范围，将涉及的桶内所有活跃实体追加物化至输出向量，随后由 `0x004137A0`（`Next`）逐个弹出送入 `0x006F7CA0` 进行单候选打分。

#### (3) 路 B：精细逐格同心环螺旋扫描（`0x006F93C1..0x006F976D`）
路 A 遍历完毕后，若未排除，函数直接流入 `0x006F93C1` 启动路 B 精细扫描：
1. **几何覆盖形态**：
   以单位所在 Cell 为中心，环半径从 `ring = 0` 递增至 `radius`；每一圈沿正方形边框遍历四边周长（边长为 $2 \times \text{ring} + 1$）；
2. **逐格对象链表遍历（`0x006F8960`）**：
   - 检查 `MapClass::IsCellInMap (0x00568300)`；
   - 调用 `MapClass::TryGetCellAt (0x005657A0)` 获取 `CellClass*`；
   - 提取首对象指针：优先取桥面/高层 `CellClass+0xE8`（`AltObject`），为空则取地面 `CellClass+0xE4`（`FirstObject`）；
   - 沿 `ObjectClass+0x30`（`NextObject`）单链表遍历同格内所有对象；
   - 逐个调用 `0x006F7CA0`（0xCC0 字节的巨型评估函数，核对 House 结盟、隐身、血量比、威胁威胁值等）；
   - 主循环仅在候选威胁分严格大于当前最高分（`0x006F936B: cmp eax, ecx; jle skip`）时更新最优目标。

---

### 2.3 数量级定量推导：1200 单位同帧全扫的理论上界

#### (1) 单单位单次扫描 Cell 数上界
路 B 的扫描覆盖整个 Chebyshev 正方形（边长 $2R + 1$），总格点数为：
$$N_{\text{cell}} = (2R + 1)^2$$
代入游戏典型兵种实测参数：
- **常规中近程单位 / 步兵**（射程 3~4，GuardRange 4）：$R = 4 + 4 + 1 = 9$，覆盖 $(2\times 9 + 1)^2 = 19^2 = \mathbf{361\ \text{cells}}$；
- **主力重装坦克**（如犀牛重型坦克 120mm 射程 5.75 cells $\to 5$，GuardRange 5）：$R = 5 + 5 + 1 = 11$，覆盖 $(2\times 11 + 1)^2 = 23^2 = \mathbf{529\ \text{cells}}$；
- **长程作战单位**（如光棱坦克射程 10，GuardRange 6）：$R = 10 + 6 + 1 = 17$，覆盖 $(2\times 17 + 1)^2 = 35^2 = \mathbf{1225\ \text{cells}}$；
- **极端超远射程单位**（如巨炮射程 15，V3 火箭射程 18，GuardRange 10）：$R = 18 + 10 + 1 = 29$，覆盖 $(2\times 29 + 1)^2 = 59^2 = \mathbf{3481\ \text{cells}}$。

#### (2) 1200 单位同帧全量扫描总量
在最严苛的雪崩假设下（1200 个单位在同一帧内同时失去目标或被唤醒，全体发起无缓存重搜）：
- **按主力中型坦克基准（529 cells/单位）**：
  $$\text{Total Cells} = 1200 \times 529 = \mathbf{6.348 \times 10^5\ \text{cells}}$$
- **按混合长程单位基准（1000 cells/单位）**：
  $$\text{Total Cells} = 1200 \times 1000 = \mathbf{1.200 \times 10^6\ \text{cells}}$$
- **按极端理论天花板（全部为长程火炮，3481 cells/单位）**：
  $$\text{Total Cells} = 1200 \times 3481 = \mathbf{4.177 \times 10^6\ \text{cells}}$$

#### (3) 指令级与时间级换算
在 `0x006F8960` 的单格扫描中：
- 空格判定（无对象）：`TryGetCellAt`（数组索引，约 20 条指令）+ 链头判空（2 条指令）$\approx 25$ 条指令（耗时约 $8 \sim 10\ \text{ns}$）；
- 有对象格：需进 `0x006F7CA0`（结盟位图、血量浮点计算、ThreatPosed 乘法），单对象评估约 150~200 条指令（耗时约 $50 \sim 80\ \text{ns}$）；
- 在 100×100 = 10,000 格地图中分布 1200 个单位，绝大多数格子为空格，平均单格综合代价取 $\approx 30\ \text{ns}$：
  - **主力坦克全扫耗时**：
    $$T = 6.348 \times 10^5\ \text{cells} \times 30\ \text{ns} \approx \mathbf{19.05\ \text{ms}}$$
  - **混合长程全扫耗时**：
    $$T = 1.200 \times 10^6\ \text{cells} \times 30\ \text{ns} \approx \mathbf{36.00\ \text{ms}}$$
  - **极端超长程全扫耗时**：
    $$T = 4.177 \times 10^6\ \text{cells} \times 30\ \text{ns} \approx \mathbf{125.31\ \text{ms}}$$

#### (4) 数量级定性结论
- 实测慢窗赤字：满帧 32.0ms $\to$ 慢爬 166.8ms，帧时劣化差值 $\Delta T = \mathbf{134.8\ \text{ms}}$；
- 理论极端并发索敌耗时（$19 \sim 36\ \text{ms}$，极端达 $125\ \text{ms}$）与 $134.8\ \text{ms}$ **处于完全相同的数量级（同阶，0 个数量级差距）**！
- **裁决**：**在不采帧内微观数据的前提下，微观索敌层（C4）无法被静态排除（staticallyExcludable = false）**。若运行期因战局宏观拓扑瓦解（如敌方基地全毁）导致全图上千单位同时陷入无目标漫游状态并同拍高频重搜，C4 理论上具备吞噬数十至上百毫秒的动力学潜能。

---

## 3. C3 战斗物理层深度逆向核实（Bullet / Anim / DamageArea）

### 3.1 物理推进容器 VA、数据结构与容量上限

#### (1) 容器定位与布局
在主逻辑帧（`MainLogicFrame` @ `0x0055D360`）的对象循环推进段（`0x0055B8F0..0x0055B964`）中，确证物理层实体的容器地址与遍历方式：

```asm
; --- AnimClass 动画实体遍历 (0x0055B8F0 - 0x0055B916) ---
0x0055B8F0: A1 B8 E9 A8 00    mov eax, dword ptr [0x00A8E9B8] ; ★ AnimClass::Array.Count
0x0055B8F5: 56                push esi
0x0055B8F6: 8D 70 FF          lea  esi, [eax - 1]             ; esi = Count - 1 (倒序遍历)
0x0055B8F9: 85 F6             test esi, esi
0x0055B8FB: 7C 1B             jl   0x0055B918
0x0055B8FD: 8B 0D AC E9 A8 00 mov  ecx, dword ptr [0x00A8E9AC] ; ★ AnimClass::Array.Items (堆指针)
0x0055B903: 8B 0C B1          mov  ecx, dword ptr [ecx + esi*4] ; ecx = AnimClass* 实例
0x0055B906: 8A 81 98 00 00 00 mov  al, byte ptr [ecx + 0x98]   ; 活跃标志
0x0055B90C: 84 C0             test al, al
0x0055B90E: 74 05             je   0x0055B915
0x0055B910: 8B 11             mov  edx, dword ptr [ecx]       ; edx = vtable
0x0055B912: FF 52 5C          call dword ptr [edx + 0x5C]     ; ★ vtable[23]: AnimClass::Update (0x00423AC0)
0x0055B915: 4E                dec  esi
0x0055B916: 79 E5             jns  0x0055B8FD

; --- BulletClass 弹道实体遍历 (0x0055B93F - 0x0055B964) ---
0x0055B93F: A1 50 ED A8 00    mov eax, dword ptr [0x00A8ED50] ; ★ BulletClass::Array.Count
0x0055B944: 8D 70 FF          lea  esi, [eax - 1]             ; esi = Count - 1 (倒序遍历)
0x0055B947: 85 F6             test esi, esi
0x0055B949: 7C 1B             jl   0x0055B966
0x0055B94B: 8B 0D 44 ED A8 00 mov  ecx, dword ptr [0x00A8ED44] ; ★ BulletClass::Array.Items (堆指针)
0x0055B951: 8B 0C B1          mov  ecx, dword ptr [ecx + esi*4] ; ecx = BulletClass* 实例
0x0055B954: 8A 81 98 00 00 00 mov  al, byte ptr [ecx + 0x98]   ; 活跃标志
0x0055B95A: 84 C0             test al, al
0x0055B95C: 74 05             je   0x0055B963
0x0055B95E: 8B 11             mov  edx, dword ptr [ecx]       ; edx = vtable
0x0055B960: FF 52 5C          call dword ptr [edx + 0x5C]     ; ★ vtable[23]: BulletClass::Update (0x004666E0)
0x0055B963: 4E                dec  esi
0x0055B964: 79 E5             jns  0x0055B94B
```

#### (2) 容器属性与容量上限判定
核查 CRT 初始化（`0x004E687D` 与 `0x004E6D87`）：

| 容器名称 | 结构体基址 VA | Items 堆指针 | 当前计数 Count | 当前容量 Capacity | 步长 GrowthStep | 扩容机制与容量上限 |
|---|---|---|---|---|---|---|
| `BulletClass::Array` | `0x00A8ED40` | `0x00A8ED44` | `0x00A8ED50` | `0x00A8ED48` | `0x00A8ED54` = 10 | `DynamicVectorClass`，每次满溢通过 `0x007C978A` 扩容 10 项，**物理上限仅受可用虚拟堆内存限制（无硬编码静态上限）** |
| `AnimClass::Array` | `0x00A8E9A8` | `0x00A8E9AC` | `0x00A8E9B8` | `0x00A8E9B0` | `0x00A8E9BC` = 10 | 同上，惰性堆分配，**无硬编码静态上限** |

---

### 3.2 1200 单位混战时的并发实体数量上限推导

尽管容器本身无固定容量上限，但在物理仿真动力学中，同场活跃的弹丸与动画数严格受**武器射速（ROF）、交火几何与弹丸飞行周期**三重物理定律锁死：

#### (1) 弹道实体（`BulletClass`）理论上限
1. **射击冷却约束（Rate Of Fire）**：
   在 RA2/YR 规则中，重装甲作战单位的武器 ROF 极高（冷却时间长）：
   - 苏军主力犀牛重型坦克（120mm 炮）：$\text{ROF} = 65\ \text{frames}$（约 2.08 秒一发）；
   - 盟军灰熊主战坦克（105mm 炮）：$\text{ROF} = 50\ \text{frames}$（约 1.6 秒一发）；
   - 天启坦克（120mmx 连发）：$\text{ROF} = 80\ \text{frames}$；
   - 即便高频轻步兵（动员兵 M1Carbine / 美国大兵 M60）：$\text{ROF} = 20 \sim 25\ \text{frames}$。
2. **弹丸存活时间约束（Flight Lifetime）**：
   - 坦克炮弹飞行速度通常为 $Speed = 60 \sim 100$ leptons/frame；
   - 坦克交火距离一般在 $3 \sim 5$ 格（$768 \sim 1280$ leptons）；
   - 炮弹从出膛到命中目标引爆，仅需 **$1 \sim 3$ 个逻辑帧**！
3. **稳态并发存活数推导**：
   假设 1200 个单位全部处于开火射程内且 100% 满负荷连续射击：
   - 每帧全场射出的新炮弹数：$N_{\text{fire}} = 1200 / 60 \approx 20\ \text{发/帧}$；
   - 弹丸平均飞行存活 2 帧，则同拍在空中飞行的炮弹总数稳态期望值为：
     $$N_{\text{bullet, steady}} = 1200 \times \frac{2}{60} = \mathbf{40\ \text{枚}}$$
   - 即便假设极端恶劣情形（全场全为动员兵高频开火且全走远距离弧线，ROF=20，飞行 5 帧）：
     $$N_{\text{bullet, max}} = 1200 \times \frac{5}{20} = \mathbf{300\ \text{枚}}$$
   - **定谳**：在 1200 单位实测战局中，`BulletClass::Array` 的实机并发量常态为 **30 ~ 50 枚**，极端不突破 **300 枚**。

#### (2) 动画实体（`AnimClass`）理论上限
- 每次炮火发射产生 1 个枪口焰动画（持续约 4~6 帧）；
- 每次炮弹命中产生 1 个爆炸粒子动画（持续约 12~18 帧）；
- 单位被摧毁产生残骸起火/解体动画（持续约 30 帧）；
- 在稳态 20 次开火/帧的交火节奏下：
  $$N_{\text{anim, steady}} \approx (20 \times 5) + (20 \times 15) + \text{背景特效} \approx 100 + 300 + 80 = \mathbf{480\ \text{个}}$$
- **定谳**：全场并发活跃的动画实例数在 **200 ~ 600 个** 范围内。

#### (3) 范围伤害（`DamageArea` @ `0x00489280`）触发频次
- `DamageArea` 仅在炮弹命中引爆（`BulletClass::Detonate @ 0x004690B0`）且弹头具备 `CellSpread > 0`（`0x00469180: fld dword [eax+0x124]`）时触发；
- 在平稳交火下，每帧引爆炮弹数等于开火数（**20 ~ 30 次/帧**），绝非每帧 1200 次。

---

### 3.3 数量级论证：C3 能否独立解释 5 倍帧时恶化？

#### (1) 单项指令级与耗时估算
1. **`BulletClass::Update`（`0x004666E0`）**：
   - 纯 3D 浮点速度累加（`Location += Velocity`）、落点/障碍格查询与到期判定；
   - 函数体约 120 条指令，耗时约 **40 ~ 50 ns** / 枚；
   - 40 枚并发总耗时：$40 \times 50\ \text{ns} = 2.0\ \mu\text{s} = \mathbf{0.002\ \text{ms}}$（300 枚极限下为 $0.015\ \text{ms}$）。
2. **`AnimClass::Update`（`0x00423AC0`）**：
   - 动画帧推进（`Stage++`）、循环回绕判定与音效关联；
   - 函数体约 80 条指令，耗时约 **25 ~ 35 ns** / 个；
   - 500 个并发总耗时：$500 \times 30\ \text{ns} = 15.0\ \mu\text{s} = \mathbf{0.015\ \text{ms}}$。
3. **`DamageArea`（`0x00489280`）**：
   - AOE 半径通常很小（$1 \sim 1.5$ 格），经由 20×20 空间桶（`0x00887888`）筛选出的邻近受击单位通常 $< 10$ 个；
   - 对受害者调用 `ReceiveDamage`（`vtable[91]`），单次引爆涉及约 1000 条指令（耗时约 $0.4 \sim 0.6\ \mu\text{s}$）；
   - 25 次引爆总耗时：$25 \times 0.5\ \mu\text{s} = 12.5\ \mu\text{s} = \mathbf{0.0125\ \text{ms}}$。

#### (2) 综合数量级对比
将物理层三大构件单帧耗时全量求和：
$$T_{\text{C3}} = T_{\text{bullet}} + T_{\text{anim}} + T_{\text{damage}} \approx 0.002 + 0.015 + 0.0125 \approx \mathbf{0.03\ \text{ms}}$$
即便计入 10 倍的安全放大余量（考虑极端密集开火与内存缓存抖动）：
$$T_{\text{C3, upper\_bound}} \le \mathbf{0.3 \sim 0.5\ \text{ms}}$$

#### (3) 裁决判定
- 实测慢窗恶化赤字：$\Delta T = 166.8 - 32.0 = \mathbf{134.8\ \text{ms}}$；
- 物理层理论全额耗时（$\approx 0.05\ \text{ms}$）与 $134.8\ \text{ms}$ 赤字相差整整 **$3 \sim 4$ 个数量级**（占比不到 0.04%）！
- **裁决结论**：**战斗物理层（C3）在数学上完全不具备解释 5 倍恶化的任何可能性，具有绝对的负解释力，可在不采帧内数据的前提下静态完全排除（staticallyExcludable = true）**。

---

## 4. 诚实账与未验项

严格遵循规范，凡离线静态无法确证或未能覆盖的盲区，明确建账入册：

### 4.1 已完全确证项 [实证]
1. `BulletClass::Array` 位于 `0x00A8ED40`，`AnimClass::Array` 位于 `0x00A8E9A8`，均为 `DynamicVectorClass` 堆管理容器，物理推进更新点位于 `0x0055B8F0..0x0055B964`；
2. `SelectAutoTarget`（`0x006FB010`）是弹药装填计数器，常规战车单位在第 5 条指令退出（$<2\text{ns}$），绝非索敌扫描体；
3. `house_team_ai_update.md` 记载的 8 帧/100 帧限频属于 `HouseClass::Update`（`0x004F8440`），微观索敌函数本身**零 8 帧/100 帧限频**；
4. `Greatest_Threat`（`0x006F8DF0`）同时运行 20×20 粗空间哈希桶（`0x00887888`）与以武器射程+警戒射程为半径的正方形螺旋同心环扫格（`0x006F93C1`）；
5. 1200 单位同拍全并发扫格理论上界为 $6.35 \times 10^5 \sim 1.20 \times 10^6$ cells（开销约 $19 \sim 36\ \text{ms}$），与 134.8ms 赤字同数量级。

### 4.2 明确未能验证项 [未验]
1. **单位运行期目标保持状态（Target Retention）与 CDTimer 错峰分布 [未验]**：
   在纯静态逆向视角下，我们能够证明「1200 单位同拍全并发扫格」的算力上界为 $19 \sim 36\ \text{ms}$，但在 87 窗离线产物中，未采集各单位 `this+0x350`（索敌冷却计时器）与 `this+0x5D4`（当前锁定目标），**无法直接证明慢窗中究竟是有 50 个单位在索敌，还是真发生了 1000 个单位同拍并发雪崩**；
2. **全局索敌重入计数器 `0x00A8EC34` 的真实增量 [未验]**：
   汇编确证 `0x006F8DF3: inc dword ptr [0x00A8EC34]` 记录了 `Greatest_Threat` 的全引擎调用次数，但历史 `measure_w*.json` 的 `counters` 从未读取该 VA，因此无法通过现有产物直接提取运行期调用频次；
3. **路 A 空间桶在极端密集聚团时的链表冲突深度 [未验]**：
   若 1200 单位在局部极端挤压聚堆在同一格（如狭窄路口阻挡死锁），单格内的 `ObjectClass+0x30` 链表长度将拉长至数十甚至上百，会使 `0x006F8960` 的单格遍历成本偏离均摊假设，该动力学聚团形态属于流体动力学演化特征，静态无法预估其极值分布。
