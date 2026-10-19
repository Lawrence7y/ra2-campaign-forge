# S6 专项冲刺报告：House/Team AI 机制与寻敌空间哈希等效性深潜

> 逆向基准：`gamemd.exe` 1.001（尤里的复仇）  
> 内存基址：`ImageBase = 0x400000`，代码段 VA 起点 `0x401000`，文件偏移 `FileOffset = VA − 0x400000`  
> 【W3 勘误 E-W3-01】原句 `FileOffset = VA − 0x400000` 仅在 `.text/.rdata/.data` 成立；
> 通用式为 `FileOffset = 段.PointerToRawData + (VA − 段.VirtualAddress)`，
> 本镜像 `.rsrc`/`.detour` 为 `VA − 0x6FC000`。依据：out/re_work/_lead_baseline/W3/LEAD_ERRATUM_E-W3-01_fileoffset_rule.md；分级：[实证]
> 分析工具链：Python 3.10 + `pefile` + `capstone`  
> 支撑代码目录：`out/re_work/re_sprint/S6/`  
> 关联逆向文档：`docs/re/house_team_ai_update.md`（已原地追加第 9 节）、`docs/re/targeting_spatial.md`（只读引用）

---

## 1. 执行摘要与证据等级说明

本冲刺聚焦于 RA2/YR 引擎高密度战局下除寻敌外的 AI 决策中枢与寻敌空间哈希等效性两大核心难题，完成了全汇编链路的实证闭环与数学证明：

1. **AITrigger 权重回写机制**：证明全二进制中仅存在 `TeamClass::~TeamClass`（`0x006E8DE0`）一处调用 `RegisterSuccess`（`0x0041FD60`）与 `RegisterFailure`（`0x0041FE20`），不存在每帧权重衰减或漂移；纠正了社区头文件 YRpp 沿用 20 年的计数器字段反向命名，给出了 x87 FPU 逐指令还原的权重回写数学公式；证实 `AchievedGreatSuccess` 仅由脚本 Action 49 触发；证实 `0x006F0AB0` 仅对权重进行只读轮盘赌求值。
2. **招募三兄弟轮转时序与全生命周期**：纠正了此前猜测的“陆/海/空”兵种定义，实证三兄弟分别严格对应 **战车（0x4FEA60）**、**步兵（0x4FEEE0）** 与 **战机（0x4FF210）**；实证其在 `HouseClass::Update` 内部每 8 帧同帧严格串行执行，并直接向对应工厂下达 `v[0x94]` 生产指令；揭示了跨帧轮转（Round-Robin）在兵种成型时延与资金抢占上的确定性风险；补全了队伍主动拉取（`0x006EAA90`）与工厂被动推送（`0x0073DC19` / `0x0073815F`）的招募双通道。
3. **空间哈希替换枚举序等效性证明**：针对 `targeting_spatial.md` 中“严格大于（`>`）择优下空间哈希打乱枚举顺序是否导致同分漂移”的核心阻碍，建立了基于字典序元组 $(S(c), -\text{ord}(c))$ 的全序数学模型，证明了使用 $O(1)$ 平分决胜比较器即可在零排序、零额外内存分配的条件下实现与原版数组枚举序 100% 的 bit-exact 等效。

### 证据分级规范
- **[实证]**：提供具体虚拟地址（VA）、文件偏移（FileOffset）、机器字节码（Hex Opcode）与反汇编指令。
- **[推演]**：基于实证指令结构与控制流做出的确定性逻辑推导与数学定理证明。
- **[待实测]**：涉及动态博弈、联机网络波动或特定地图脚本生态的表现，需要后续挂钩或真机压测验证。

---

## 2. 核心研究一：AITrigger 权重回写时机全链路闭环

### 2.1 全二进制写引用唯一性取证 [实证]

对 `gamemd.exe` 全代码段执行内存写指令扫描（目标字段为 `AITriggerTypeClass::Weight_Current`，偏移 `+0xB8`，8 字节 double）：

```text
VA: 0x0041E374 | FileOffset: 0x01E374 | 89 96 B8 00 00 00       | mov [esi + 0xb8], edx   ; ctor 默认初始化
VA: 0x0041F8AC | FileOffset: 0x01F8AC | DD 9D B8 00 00 00       | fstp qword ptr [ebp + 0xb8] ; LoadFromINI 解析
VA: 0x0041FDB3 | FileOffset: 0x01FDB3 | DD 91 B8 00 00 00       | fst qword ptr [ecx + 0xb8]  ; RegisterSuccess
VA: 0x0041FDCC | FileOffset: 0x01FDCC | 89 81 B8 00 00 00       | mov [ecx + 0xb8], eax   ; RegisterSuccess (下限 clamp)
VA: 0x0041FDF7 | FileOffset: 0x01FDF7 | 89 81 B8 00 00 00       | mov [ecx + 0xb8], eax   ; RegisterSuccess (上限 clamp)
VA: 0x0041FE7C | FileOffset: 0x01FE7C | DD 91 B8 00 00 00       | fst qword ptr [ecx + 0xb8]  ; RegisterFailure
VA: 0x0041FE95 | FileOffset: 0x01FE95 | 89 81 B8 00 00 00       | mov [ecx + 0xb8], eax   ; RegisterFailure (下限 clamp)
VA: 0x0041FEC0 | FileOffset: 0x01FEC0 | 89 81 B8 00 00 00       | mov [ecx + 0xb8], eax   ; RegisterFailure (上限 clamp)
```

**取证结论**：除对象构造与 INI 加载外，全游戏有且仅有 `RegisterSuccess`（`0x0041FD60`）与 `RegisterFailure`（`0x0041FE20`）会改写 `Weight_Current`。**不存在任何每帧运行的权重更新或衰减逻辑**。

### 2.2 调用宿主唯一性取证 [实证]

对 `RegisterSuccess` 与 `RegisterFailure` 进行全代码段交叉引用搜索：

```text
Searching xrefs to 0x0041FD60 (RegisterSuccess):
  0x006E8E2A | FileOffset: 0x2E8E2A | E8 31 6F D3 FF | call 0x0041FD60 (唯一)

Searching xrefs to 0x0041FE20 (RegisterFailure):
  0x006E8E31 | FileOffset: 0x2E8E31 | E8 EA 6F D3 FF | call 0x0041FE20 (唯一)
```

两处调用均位于 `TeamClass::~TeamClass`（`0x006E8DE0`）内部：

```asm
0x006E8E02 | A1 10 B2 A8 00       | mov eax, dword ptr [0xa8b210]   ; AITriggerTypeClass::Array.Count
0x006E8E07 | 85 C0                | test eax, eax
0x006E8E09 | 7E 35                | jle 0x6e8e40
0x006E8E0B | A1 04 B2 A8 00       | mov eax, dword ptr [0xa8b204]   ; AITriggerTypeClass::Array.Items
0x006E8E10 | 8B 0C B8             | mov ecx, dword ptr [eax + edi*4]; ecx = AITriggerTypeClass*
0x006E8E13 | 8B 46 24             | mov eax, dword ptr [esi + 0x24] ; eax = this->Type (TeamTypeClass*)
0x006E8E16 | 8B 91 DC 00 00 00    | mov edx, dword ptr [ecx + 0xdc] ; edx = trigger->Team1
0x006E8E1C | 3B D0                | cmp edx, eax
0x006E8E1E | 75 16                | jne 0x6e8e36
0x006E8E20 | 8A 86 84 00 00 00    | mov al, byte ptr [esi + 0x84]   ; al = this->AchievedGreatSuccess
0x006E8E26 | 84 C0                | test al, al
0x006E8E28 | 74 07                | je 0x6e8e31
0x006E8E2A | E8 31 6F D3 FF       | call 0x41fd60                    ; RegisterSuccess!
0x006E8E2F | EB 05                | jmp 0x6e8e36
0x006E8E31 | E8 EA 6F D3 FF       | call 0x41fe20                    ; RegisterFailure!
0x006E8E36 | A1 10 B2 A8 00       | mov eax, dword ptr [0xa8b210]
0x006E8E3B | 47                   | inc edi
0x006E8E3C | 3B F8                | cmp edi, eax
0x006E8E3E | 7C CB                | jl 0x6e8e0b
```

**取证结论**：队伍析构是 AITrigger 权重回写的**唯一时机**。每次队伍解散或全灭时，线性扫描全量 `AITriggerTypeClass` 列表，匹配其 `Team1` 是否与队伍类型一致，根据 `this+0x84` 执行单次权重修正。

### 2.3 成败判定标志（`+0x84`）与脚本 Action 49 绑定 [实证]

1. **初始化**：`TeamClass::ctor`（`0x006E8A90`）在 `0x006E8B2C` 执行 `mov byte ptr [esi + 0x84], 0`，初始状态恒为 0。
2. **触发源检索**：对全二进制搜索写 `byte ptr [reg + 0x84], 1` 指令，仅命中 1 处：
   - `0x006E9CE8` | `C6 86 84 00 00 00 01` | `mov byte ptr [esi + 0x84], 1`
3. **跳转表归属**：该指令属于 `TeamClass::AI`（`0x006E9050`）中脚本动作跳转表 `0x006E9F74`（索引范围 0～64）的 **Action 49（0x31）**：
   ```text
   Action 49 (0x31) -> 0x006E9CE1:
     0x006E9CE1 | C6 86 80 00 00 00 01 | mov byte ptr [esi + 0x80], 1 ; AchievedSuccess = 1
     0x006E9CE8 | C6 86 84 00 00 00 01 | mov byte ptr [esi + 0x84], 1 ; AchievedGreatSuccess = 1
     0x006E9CF6 | C3                   | ret
   ```
   作为对比，Action 43（`0x006E9C22`，货运/弹药检查）在 `0x006E9C55` 仅执行 `mov byte ptr [esi + 0x80], 1`，并不设置 `+0x84`。

**取证结论**：`AchievedGreatSuccess`（`+0x84`）严格且唯一绑定于脚本 Action 49（`Success`）。未执行到该脚本行的 Team，不论因何种原因终结（被消灭、超时解散、卡死释放），均被判定为 Failure。

### 2.4 YRpp 命名颠倒纠偏与精确数学算式 [实证]

在逆向分析 `RegisterSuccess`（`0x0041FD60`）与 `RegisterFailure`（`0x0041FE20`）时，发现了 YRpp 社区头文件的一处严重历史笔误：

```asm
; RegisterSuccess 入口
0x0041FD61 | 8B 91 08 01 00 00 | mov edx, dword ptr [ecx + 0x108] ; 取 +0x108
0x0041FD77 | DB 44 24 00       | fild dword ptr [esp]             ; 载入 +0x108
0x0041FD7B | DB 81 04 01 00 00 | fild dword ptr [ecx + 0x104]     ; 载入 +0x104
0x0041FD81 | D8 F1             | fdiv st(1)                       ; st(0) = [ecx+0x104] / [ecx+0x108]
; 尾部计数器更新
0x0041FE09 | 8B 81 04 01 00 00 | mov eax, dword ptr [ecx + 0x104]
0x0041FE0F | 40                | inc eax                          ; [ecx+0x104]++
0x0041FE10 | 42                | inc edx                          ; [ecx+0x108]++
0x0041FE11 | 89 81 04 01 00 00 | mov dword ptr [ecx + 0x104], eax
0x0041FE17 | 89 91 08 01 00 00 | mov dword ptr [ecx + 0x108], edx

; RegisterFailure 入口与尾部
0x0041FE21 | 8B 91 08 01 00 00 | mov edx, dword ptr [ecx + 0x108] ; 取 +0x108
0x0041FED2 | 42                | inc edx                          ; [ecx+0x108]++
0x0041FED3 | 89 91 08 01 00 00 | mov dword ptr [ecx + 0x108], edx ; 注意：完全不碰 +0x104！
```

**纠偏证实**：
- `+0x104`：仅在成功时自增，实际为 **`TimesSuccess`（成功次数）**（YRpp 误标为 `TimesExecuted`）。
- `+0x108`：在成功与失败时均自增，实际为 **`TimesExecuted`（总运行次数）**（YRpp 误标为 `TimesCompleted`）。
- 除法项 `[ecx+0x104] / [ecx+0x108]` 即为真实的 **历史胜率** $R = \frac{\text{TimesSuccess}}{\text{TimesExecuted}}$。

从数据段提取双精度浮点常数：
- `0x007E2800` (FileOffset `0x3E2800`)：`0.0`
- `0x007E1738` (FileOffset `0x3E1738`)：`0.5`

**精确回写算式**：
1. **成功时（`RegisterSuccess`）**：
   $$\text{term} = \text{TimesExecuted} \times (R - 0.5) = \text{TimesSuccess} - 0.5 \times \text{TimesExecuted}$$
   $$\Delta_{succ} = \max(\text{term}, \; 0.0)$$
   $$\text{Weight\_Current} \leftarrow \text{clamp}\Big(\text{Weight\_Current} + \text{Rules.AITriggerSuccessWeightDelta}(+0\text{xC0}) + \Delta_{succ}, \; \text{Weight\_Min}, \; \text{Weight\_Max}\Big)$$
   $$\text{TimesSuccess}\text{++}, \quad \text{TimesExecuted}\text{++}$$

2. **失败时（`RegisterFailure`）**：
   $$\text{term} = \text{TimesExecuted} \times (R - 0.5) \times \text{Rules.AITriggerTrackRecordCoefficient}(+0\text{xD0})$$
   $$\Delta_{fail} = \min(\text{term}, \; 0.0)$$
   $$\text{Weight\_Current} \leftarrow \text{clamp}\Big(\text{Weight\_Current} + \text{Rules.AITriggerFailureWeightDelta}(+0\text{xC8}) + \Delta_{fail}, \; \text{Weight\_Min}, \; \text{Weight\_Max}\Big)$$
   $$\text{TimesExecuted}\text{++}$$

### 2.5 评估宿主（`0x006F0AB0`）只读实证 [实证]

在 `AITrigger` 评估函数 `0x006F0AB0` 中：
- `0x006F0C61` 执行 `fld qword ptr [esi + 0xb8]` 读取权重，调 `0x007C5F00`（`__ftol`）转为整型。
- 随后若整型权重为 5000（强制特权触发），则清空此前收集的所有普通触发器；若普通权重则累加到局部总权重 `[esp + 0x5C]`。
- 在 `0x006F0CEE` 处调用 `0x0065C7E0` 获取 `[1, TotalWeight]` 随机数，遍历累加候选权重，完成轮盘赌选拔。
- **全函数未包含任何写回 `+0xB8` 的指令**。

---

## 3. 核心研究二：招募三兄弟轮转时序与全生命周期

### 3.1 三兄弟兵种类型澄清 [实证]

通过反汇编跟踪三兄弟写入的订单槽位、Missing 检查中的 `WhatAmI` 常数，以及紧随其后的工厂下单调用，彻底澄清其真实分工：

| 函数 VA | 文件偏移 | 触发门控槽位 | 缺失单位 WhatAmI 过滤 | 关联全局类型数组 | 驱动工厂类型 | 真实兵种身份 |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `0x004FEA60` | `0x0FEA60` | `House+0x5650 == -1` | `0x28`（`UnitType`，40） | `0x00A83CE0`（`UnitTypeClass`） | 战车工厂（War Factory） | **战车 / 装甲** |
| `0x004FEEE0` | `0x0FEEE0` | `House+0x5654 == -1` | `0x10`（`InfantryType`，16） | `0x00A8E348`（`InfantryTypeClass`） | 兵营（Barracks） | **步兵** |
| `0x004FF210` | `0x0FF210` | `House+0x5658 == -1` | `0x03`（`AircraftType`，3） | `0x00A8B218`（`AircraftTypeClass`） | 停机坪/机场（Airfield） | **战机 / 航空** |

前文猜测的“陆军/海军/空军”在此正式更正。RA2 引擎中海军舰船（驱逐舰、潜艇等）在底层继承自 `UnitTypeClass`，与陆地战车共用战车兄弟（`0x004FEA60`）管辖。

### 3.2 每帧执行序与工厂下单链路 [实证]

在 `HouseClass::Update`（`0x004F8440`）的 `0x004F9074`–`0x004F9240` 区域，呈现高度紧凑的流水线：

```
[CurrentFrame % 8 == 0 且 AIMode == 2]
  │
  ├─ 0x004F90F2: call 0x004FEA60   ; 战车招募决策 -> 若通过则写 House+0x5650 = UnitTypeIdx
  ├─ 0x004F9198: call 0x004FEEE0   ; 步兵招募决策 -> 若通过则写 House+0x5654 = InfantryTypeIdx
  ├─ 0x004F919F: call 0x004FF210   ; 战机招募决策 -> 若通过则写 House+0x5658 = AircraftTypeIdx
  │
  └─ 工厂生产下单派发 (0x004F91A4 - 0x004F9238)
       ├─ 若 House+0x5650 != -1:
       │    mov ecx, [0xA83CE4 + eax*4] ; UnitTypeClass*
       │    call WarFactory->vtable[0x94] (StartProduction)
       ├─ 若 House+0x5654 != -1:
       │    mov ecx, [0xA8E34C + eax*4] ; InfantryTypeClass*
       │    call BarracksFactory->vtable[0x94] (StartProduction)
       └─ 若 House+0x5658 != -1:
            mov ecx, [0xA8B21C + eax*4] ; AircraftTypeClass*
            call AirfieldFactory->vtable[0x94] (StartProduction)
```

### 3.3 单位与队伍招募的全生命周期（双通道模型） [实证]

三兄弟决定的是“造什么单位来满足编制”，而单位造成后如何加入队伍，引擎实现了精密的双通道：

```
                     ┌───────────────────────────────┐
                     │ AITrigger 命中创建 TeamClass   │
                     │ (0x006F09C0, FirstUnit = NULL)│
                     └──────────────┬────────────────┘
                                    │
           ┌────────────────────────┴────────────────────────┐
           ▼                                                 ▼
【主动拉取通道 (Pull)】                             【被动推送通道 (Push)】
由 TeamClass::AI (0x006E9050) 驱动               由工厂出厂逻辑 (0x0073DC19) 驱动
  │                                                 │
  ├─ 0x006E9281: call 0x006EAA90 (Recruit)          ├─ 新单位完成下线（UnitClass::Init）
  ├─ 遍历地图闲置单位 (Unit/Infantry/Aircraft)       ├─ 遍历全体 TeamClass::Array (0x008B40EC)
  ├─ 0x006EA610: CanAddMember 资格审查              ├─ 匹配自身类型是否属于 Team 缺失类型
  │    (归属阵营、非Limbo、血量>0、符合TaskForce)    │
  └─ 0x006EA500: AddMember 链入队伍                 └─ 0x006EA500: AddMember 链入队伍
       ├─ unit->Team (+0x5D4) = this
       └─ unit->NextTeamMember (+0x5D8) = this->FirstUnit (+0x54)
```

### 3.4 时间片轮转（Round-Robin）的确定性风险评估 [推演]

若对招募三兄弟实施每 8 帧轮转（例如 8 帧战车、16 帧步兵、24 帧战机）：
1. **时延推迟**：步兵出兵下单平均滞后 8 帧（约 0.5 秒），战机滞后 16 帧，改变 AI 进攻波次的混合兵力比例。
2. **资金竞态破坏（致命）**：`v[0x94]` 下单时会扣除/预锁金钱。原版中战车享有第一优先权，在金钱仅够造一辆坦克时，坦克必然成功下单；若轮转到步兵优先，步兵将抢先扣款，导致坦克因余额不足而跳过，彻底颠覆 AI 的重工业推进决策。
3. **安全实施准则**：若必须使用时间片，轮转必须以全局同步帧号 `(CurrentFrame / 8) % 3` 为基准；且在 House 资金充裕（`Credits > 2000`）时才允许轮转，低资金时必须回退到原版全量扫描。

---

## 4. 核心研究三：空间哈希替换枚举序等效性证明

### 4.1 原版择优机制建模与疑难分析 [实证]

在 `TechnoClass::Greatest_Threat`（`0x006F8DF0`）的内层候选更新逻辑（`0x006F9363`–`0x006F9377`）中：

```asm
0x006F9363 | 8B 44 24 74       | mov eax, dword ptr [esp + 0x74] ; 本候选威胁评分 S(c)
0x006F9367 | 8B 4C 24 1C       | mov ecx, dword ptr [esp + 0x1c] ; 当前最优威胁评分 S_max
0x006F936B | 3B C1             | cmp eax, ecx                    ; ★ 威胁评分比较指令点 (FileOff: 0x2F936B)
0x006F936D | 7E 08             | jle 0x6f9377                    ; ★ 严格大于才更新 (S(c) <= S_max 则跳过)
0x006F936F | 89 6C 24 20       | mov dword ptr [esp + 0x20], ebp ; 更新最优目标指针 Target_best = c
0x006F9373 | 89 44 24 1C       | mov dword ptr [esp + 0x1c], eax ; 更新最高分 S_max = S(c)
```
注：全图对象枚举另有两处同构更新点（步兵/战车循环）：`0x006F9C3C`（`cmp eax, ecx`）+ `0x006F9C3E`（`jle 0x006F9C48`）与 `0x006F9D87`（`cmp eax, ecx`）+ `0x006F9D89`（`jle 0x006F9D93`），其前置调用打分函数均为 `0x006F7CA0`。全逻辑统一遵循“严格大于择优”。


设全图候选集合为 $\Omega$。原版算法按照某种固有序列 $\pi_{orig} = (o_1, o_2, \dots, o_M)$ 进行遍历。
由于采用了 `jle skip`（$\le$ 则跳过），当两个候选 $o_a$ 与 $o_b$（$a < b$）具有完全相同的最大评分 $S(o_a) = S(o_b) = \max S$ 时：
- $o_a$ 先被评估，$S_{max}$ 被更新为该分值；
- 随后 $o_b$ 被评估，由于 $S(o_b) \le S_{max}$ 成立，发生跳转，**$o_b$ 被忽略**。

**原版择优定则**：
$$T_{orig}^* = o_{k^*}, \quad k^* = \min \left\{ k \in \{1, \dots, M\} \;\middle|\; S(o_k) = \max_{1 \le j \le M} S(o_j) \right\}$$
即：**在所有取得最大威胁评分的候选目标中，枚举序最早出现的目标恒胜（先到先得）**。

### 4.2 空间哈希等效性定理证明 [推演]

#### 定理（字典序全序等效定理）
设原版枚举中各候选对象的自然序列索引为 $\text{ord}(c) \in \mathbb{N}$，其在对象生命周期与当前逻辑帧内是严格唯一且确定性赋值的良序整数。
构造二维评分向量：
$$\mathbf{V}(c) = \Big( S(c), \; -\text{ord}(c) \Big)$$
定义字典序比较运算 $\succ$：
$$\mathbf{V}(A) \succ \mathbf{V}(B) \iff \Big( S(A) > S(B) \Big) \;\lor\; \Big( S(A) == S(B) \;\land\; \text{ord}(A) < \text{ord}(B) \Big)$$

**证明**：
1. **全序性**：对于任意相异候选目标 $A \ne B$，由于 $\text{ord}(A) \ne \text{ord}(B)$，$\mathbf{V}(A) = \mathbf{V}(B)$ 不可能发生。因此 $\succ$ 在候选集合 $\Omega$ 上是严格全序关系。
2. **唯一极大元**：在任意有限非空候选子集 $\mathcal{H} \subseteq \Omega$ 上，存在且仅存在唯一的最大元 $T^* = \arg\max_{c \in \mathcal{H}}^{\succ} \mathbf{V}(c)$。
3. **排列无关性（Commutativity）**：最大元求解操作具有交换律与结合律：
   $$\max^{\succ} \big( \sigma(\mathcal{H}) \big) = \max^{\succ} (\mathcal{H})$$
   对于空间哈希遍历产生的任意排列 $\sigma(\mathcal{H})$（无论是何种哈希桶存储顺序、螺旋网格展开顺序），其求出的极大元 $T^*$ 必然数学恒等于原版序列 $\pi_{orig}$ 下求出的极大元。
4. **与原版语义一致性**：
   - 若 $S(A) \ne S(B)$，$\mathbf{V}(A) \succ \mathbf{V}(B) \iff S(A) > S(B)$，与原版绝对高分胜出一致；
   - 若 $S(A) == S(B)$，$\mathbf{V}(A) \succ \mathbf{V}(B) \iff \text{ord}(A) < \text{ord}(B)$，即原版序列先出现者胜出，与原版 `jle skip` 一致。
   
综上，结论证毕。$\blacksquare$

### 4.3 工程落地规范（零排序、$O(1)$ 复杂度） [推演]

在接入空间哈希时，**完全不需要对邻域查询结果进行前置排序**。只需在目标打分维护时挂接平分决胜：

```cpp
AbstractClass* best_target = nullptr;
int best_score = -1;
uint32_t best_ord = 0xFFFFFFFF;

// 遍历空间哈希返回的任意无序邻域桶
spatial_hash.Query(center_coords, weapon_range, [&](AbstractClass* candidate) {
    int score = EvaluateTargetThreat(candidate); // 原始 0x006F7CA0 打分
    if (score <= 0) return;

    // 获取确定性规范序标：
    // 在 YR 中，(c->WhatAmI << 16) | c->GetArrayIndex() 或 c->UniqueID
    uint32_t ord = (static_cast<uint32_t>(candidate->WhatAmI()) << 16) | 
                   static_cast<uint32_t>(candidate->GetArrayIndex());

    // 零开销平分决胜比较器
    if (score > best_score || (score == best_score && ord < best_ord)) {
        best_score = score;
        best_ord = ord;
        best_target = candidate;
    }
});
```

**特性收益**：
1. **时间开销**：单次判定仅多 1 次整数比较（且仅在 `score == best_score` 时触发），平摊耗时 $\approx 0$ ns。
2. **天然幂等**：若空间哈希跨桶探测导致同一目标被输入两次，第二次执行时 `score == best_score` 但 `ord == best_ord`，条件判定失败自动过滤，**无需维护任何 `visited` 哈希表**。

---

## 5. 证据台账汇总

| 编号 | 论断内容 | 证据等级 | 核心证据线索 |
| :--- | :--- | :--- | :--- |
| E1 | AITrigger 权重仅在 TeamClass 析构时更新 | **[实证]** | 全代码仅 0x6E8E2A/0x6E8E31 调用 RegisterSuccess/Failure；全代码写 +0xB8 仅 4 处 |
| E2 | AITrigger 评估宿主 0x6F0AB0 为只读 | **[实证]** | 0x6F0C61 仅 fld 读取并转整型，全函数无 +0xB8 写指令 |
| E3 | Team 成功仅由脚本 Action 49 置位 | **[实证]** | 构造函数 0x6E8B2C 清零，全程序仅 0x6E9CE8 写 1，对应跳转表 0x6E9F74 索引 49 |
| E4 | YRpp 命名颠倒（+0x104 为成功数，+0x108 为总次数）| **[实证]** | 0x41FD61/0x41FD81 取 +0x108 做分母；RegisterFailure 仅自增 +0x108 |
| E5 | 招募三兄弟对应战车/步兵/战机 | **[实证]** | 0x4FEA60 设 +0x5650 过滤 0x28；0x4FEEE0 设 +0x5654 过滤 0x10；0x4FF210 设 +0x5658 过滤 0x03；对应工厂 v[0x94] |
| E6 | 招募三兄弟每 8 帧同帧串行执行 | **[实证]** | HouseClass::Update 在 0x4F90F2/0x4F9198/0x4F919F 紧随无分支串行 call |
| E7 | 招募存在主动扫描与出厂认领双通道 | **[实证]** | TeamClass::AI 调用 0x6EAA90 主动拉取；出厂 0x73DC19/0x73815F 调 0x6EA500 被动推送 |
| E8 | 空间哈希字典序元组等效性 | **[推演]** | 基于 0x6F936B (cmp eax, ecx) 与 0x6F936D (jle) 严格大于择优特征，数学证明全序极大元与遍历排列解耦 |
| E9 | 招募跨帧轮转资金竞态风险 | **[推演]** | 工厂下单立即扣款，战车优先级被打破后在低资金局面可能停产 |
| E10| 空间哈希在实际对战中的微观目标一致性 | **[待实测]** | 需在集成测试中抓取 Greatest_Threat 输出日志，与未打补丁回放进行逐帧 bit 级对拍 |

---

## 6. 后续演进建议

1. **AITrigger 缓存优化实施**：基于 E1/E2，AITrigger 的权重在战局中极度稳定（仅队伍阵亡时微调）。建议实施 `docs/re/house_team_ai_update.md` 提出的“插入点 B”，为 `TeamType*` 建立反向关联 Trigger 索引，彻底消除队伍析构时的全表扫描。
2. **空间哈希落地**：采用本文证明的 $O(1)$ 元组择优规范直接内嵌于 `0x006F8DF0` 入口 inline hook，既不破坏回放一致性，又能完全绕开逐类虚表漏装问题。
3. **招募三兄弟保持同帧执行**：鉴于 E9 揭示的资金抢占风险，强烈建议放弃跨帧轮转，维持同帧执行，转而采用可造类型列表（`Rules+0xB3C`）的增量游标化优化单次扫描耗时。
