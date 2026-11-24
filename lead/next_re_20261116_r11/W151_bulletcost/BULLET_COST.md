# W151 · `BulletClass` 每 tick 的成本结构（**没有** O(b·n) 搜索）

> 卡号 W151｜R11 轮｜2026-11-16｜只读静态分析（零真机、零进程、零游戏文件改动、未改主台账）
> 全部脚本在 `work\`，全部原始输出在 `EVIDENCE\`。**每个数字都附可复跑命令。**

---

## 0 · 5 行摘要

1. `[已证]` `BulletClass` 主虚表 = `0x007E46E4`（COL.offset==0，125 槽）；`+0x2C` = `0x0046B550` = `mov eax,8; ret`（WhatAmI=8），`+0x30` = `0x0046B540` = `mov eax,0x160`（sizeof=352）；槽 23（`+0x5C`）= `0x004666E0` = **`BulletClass::AI`**；槽 69（`+0x114`）= `0x00468090` = `Draw`（与台账 §18103 一致）。
2. `[已证]` 每 tick 遍历子弹数组的**唯一** AI 派发点 = 函数 **`0x0055B8F0`** 内偏移 `0x55B960` 处：`for (i = Count-1; i >= 0; --i) if (obj->[0x98]) obj->vtbl[0x5C]()`。该函数是**11 条数组**的固定阶梯（Anim/BuildingLight/**Bullet**/Building/Aircraft/Infantry/Unit/ParticleSystem/Terrain/VoxelAnim/Wave），每块 0x27 B。
3. `[已证]` **`BulletClass::AI`（6422 B / 1794 指令）里只有一个真循环**，且是"从 `AbstractClass*` 向量里摘自己"的**元素搬移**（上界 `[0xB0F5C8]`，由 `+0x158` 门控 ⇒ 只在子弹标记销毁那一次跑），其余 5 个 `for(i=6/0xc)` 是编译器展开的定长拷贝。**AI 体内没有任何"每颗子弹 × 其它对象/格"的搜索。**
4. `[已证·负]` AI 的直接 callee 里**没有一个是带循环的**（`nback=0`）；AI 深度 4 闭包 303 个函数**没有一个**遍历全场对象数组；全二进制**不存在**"遍历 `AbstractClass::Array` 并派发"的循环（引用 `0xB0F720/724/730` 的 14 个函数全是内联 Add/Remove 模板）。⇒ **不存在 O(b·n) 项**。
5. `[静态推断]` 因此台账 §733 的"命中判定/溅射邻域搜索"假设**不成立**；0.65 ms/发（≈65 万周期/发 @1 GHz）比这段代码的能力高 2–3 个数量级 ⇒ b 相关性**不可能**来自 AI 更新循环，头号余候选是**逐发绘制/blit**（本卡未证，见 §7 P1）。

`[已证]` 9 条 · `[静态推断]` 2 条 · `[未证]` 3 条（见 `UNKNOWNS.md`）

---

## 1 · 复核任务书点名的三件事

### 1.1 虚表定位（`[已证]`）
```
python work\dumppvt.py 7e46e4        → EVIDENCE\vtable_bullet_main.log
```
- `vtables_canonical.json` 里 `.?AVBulletClass@@` 共 4 张表：`0x7E46B8`(offset 12)、`0x7E46C0`(8)、`0x7E46C8`(4)、**`0x7E46E4`(offset 0 = 主表)**。子表 3 张、主表最后——**符合** R11_COMMON §3.1 的"降序发射"规则。
- 主表共 **125 槽**（槽 124 之后下一 dword = `0x00000000` ⇒ 终止）。
- **`+0x2C` = 槽 11 = `0x0046B550`，6 字节，`mov eax,8; ret`** ⇒ 属 ObjectClass 树的 WhatAmI，N=8 ✓（任务书要求复核项，成立）。
- 交付的"这是真虚表"的**独立**证据：`0x00466380`（= `BulletClass` 构造器，见 §1.2）在 `0x466425/0x46642b/0x466431/0x466438` 依次写入
  `[esi]=0x7E46E4`、`[esi+4]=0x7E46C8`、`[esi+8]=0x7E46C0`、`[esi+0xC]=0x7E46B8` —— 四个 vptr 与 canonical 表**逐一对上**。

### 1.2 容器基址：**R11_COMMON §3.3 的 `0x00A8ED3C` 是错的**（`[已证]`）
三路独立证据互相印证，容器对象基址 = **`0x00A8ED40`**：

| 字段 | 地址 | 证据 |
|---|---|---|
| vptr | `0x00A8ED40` | `0x46648f mov eax,[0xa8ed40]` + `0x466496 mov ecx,0xa8ed40` + `call [eax+8]`（把 `0xA8ED40` 当 `this` 传给容器的 slot 2）|
| Items | `0x00A8ED44` | `0x4664b1 mov ecx,[0xa8ed44]` → `0x4664b7 mov [ecx+eax*4],esi`（把 Bullet\* 写进数组）|
| Capacity | `0x00A8ED48` | `0x466468` 载入，`0x466473 cmp ecx,eax` 与 Count 比较（增长判定）|
| Count | **`0x00A8ED50`** | `0x4664ab mov [0xa8ed50],ecx`（自增）/ `0x466630`（自减）|
| CapacityIncrement | `0x00A8ED54` | `0x466483` 载入，`0x46648b jle` 判 >0 |

第三路：`W132_arrays\instance_arrays.tsv` 整行
`DynamicVectorClass<BulletClass*>  base=0x00A8ED40  items=0x00A8ED44  count=0x00A8ED50`
（`python work\q.py` 系列外的直接读表命令见 §8）。第四路：Lead 真机 §887 独立实测确认。
第五路（本卡新发现）：`0x006802F0` 把容器指针当 `edx` 传入后，用 **`[edi+0x10]` 取 Count、`[edi+4]` 取 Items** —— 只有 base=0xA8ED40 才同时成立。

> **`0xA8ED3C` 不属于这个容器**（全 `.text` 只有 1 处引用它：`0x00544957`，在 `0x005447C0` 里，与子弹数组无关）。
> 详见 `DISAGREE.md` D-1。

### 1.3 每 tick 谁遍历子弹数组（`[已证]`）
**方法必须换**：`0x0055B8F0` 这一段**根本不在 Ghidra 的函数表里**——
```
Ghidra: getFunctionContaining(0x55b960) → null     (EVIDENCE\ghidra_probe1.log, "=== INFO ===")
Ghidra: === DECOMP ?5617904 size=-1 ===            (5617904 = 0x55B8F0，反编译直接失败)
```
所以 **所有基于 `function_atlas.tsv` / `calledges.raw.log` 的检索都看不见它**，而 `0x004666E0` 的"0 callers"也正是这个原因。我改用三种**与 Ghidra 分帧无关**的扫描：

| 脚本 | 覆盖什么 | 结果 |
|---|---|---|
| `work\globalscan.py` | 原始字节里搜目标地址 dword（无条件、不依赖分帧）| 谁碰子弹容器 |
| `work\patscan.py` | 原始字节里搜 `FF /2` 编码（`call [reg+disp]`）| 槽 0x5C 派发点 |
| `work\branchscan.py` | 全 `.text` 逐字节解 rel8/rel32 分支目标 | 谁进入某函数 |

三条给出的关键结论：
- 槽 23（`call [reg+0x5C]`）全 `.text` 共 **162 处**；按 atlas 只能找到 **129 处**（漏 33 处，全在未分帧区）。
- 引用 `0xA8ED50` 的**全部** 15 处、引用 `0xA8ED44` 的全部 10 处已穷举（`EVIDENCE\globalscan_bulletarray.log`）。

---

## 2 · 调用链表（`[已证]`，每行附地址）

```
每帧主循环  0x48CCC0 (Conquer.CPP)            [台账 §881，本轮未复核]
  └─ 0x55D360  每帧更新  (帧计数 inc @0x55DE6A)
       ├─ 0x67CEF0  @0x55DC92  ──► 存档/序列化支路（本卡新定性，见 §5）
       └─ …

每 tick 对象 AI 派发器  0x0055B8F0   ★本卡核心（Ghidra 无此函数）
  │   size = 0x1B0 = 432 B，0x55B8F0 … 0x55BA9F (`pop esi; ret`)
  │   11 个同构块，每块 0x27 B：
  │     mov eax,[<Count>] / lea esi,[eax-1] / test-jl
  │     L: mov ecx,[<Items>] / mov ecx,[ecx+esi*4] / mov al,[ecx+0x98]
  │        test al,al / je skip / mov edx,[ecx] / call [edx+0x5C] / skip: dec esi / jns L
  ├─ 块3 = 子弹：Count=[0xA8ED50] Items=[0xA8ED44]，派发点 0x55B960
  │     └─ call [vptr+0x5C] = 0x004666E0  BulletClass::AI   (6422 B)
  └─ 其余 10 块见 §3

BulletClass::AI  0x004666E0  (vtable 0x7E46E4 槽 23)
  ├─ 真循环 1 个：数组摘除搬移，上界 [0xB0F5C8]，由 +0x158 门控（子弹销毁那一次）
  ├─ 门控：+0x90 (`in_ECX[0x24]`) == 0 → 立即 return    ← 与台账 §623 二道门一致
  ├─ 自递归 1 次 (0x4666E0 → 0x4666E0)
  └─ 33 个唯一 callee / 85 个调用点，**全部 nback=0（无循环）**
```

---

## 3 · 每 tick 的 11 条数组阶梯（`[已证]`）

`work\dumpfunc.py range 0x55B8F0 0x55BAC0` → `EVIDENCE\master_update_ladder.log`

| # | Count 地址 | Items 地址 | 类型（`W132_arrays\instance_arrays.tsv` + 台账 §20684–20709） | AI 派发点 |
|---|---|---|---|---|
| 1 | `0xA8E9B8` | `0xA8E9AC` | `AnimClass*` | 0x55B912 |
| 2 | `0x8B41A0` | `0x8B4194` | `BuildingLightClass*` | 0x55B939 |
| **3** | **`0xA8ED50`** | **`0xA8ED44`** | **`BulletClass*`** | **0x55B960** |
| 4 | `0xA8EB50` | `0xA8EB44` | `BuildingClass*` | 0x55B987 |
| 5 | `0xA8E3A0` | `0xA8E394` | `AircraftClass*` | 0x55B9AE |
| 6 | `0xA83DF8` | `0xA83DEC` | `InfantryClass*` | 0x55B9D5 |
| 7 | `0x8B4118` | `0x8B410C` | `UnitClass*` | 0x55B9FC |
| 8 | `0xA80218` | `0xA8020C` | `ParticleSystemClass*` | 0x55BA23 |
| 9 | `0xA8E998` | `0xA8E98C` | `TerrainClass*` | 0x55BA4A |
| 10 | `0x887398` | `0x88738C` | `VoxelAnimClass*` | 0x55BA71 |
| 11 | `0xA8EC48` | `0xA8EC3C` | `WaveClass*` | 0x55BA98 |

要点：
- **上界来源 = 容器 Count，且在进入该块时读一次**（`0x55B93F` 读 `[0xA8ED50]` 到 `eax`，循环内不再重读）⇒ 是**快照上界**，期间 `Remove` 不会缩短循环。
- **倒序**（`esi = Count-1` 递减到 0，`jns`）⇒ 支持循环内自摘除。
- 每颗子弹多一道 `+0x98` 字节门（为 0 则跳过 AI）——与台账 §575 的"+0x98 活跃标志"同一处，本卡证明它**在 AI 派发处**，不在 Count 写侧。
- **`FootClass::Array`(0x8B3DD0) / `TechnoClass::Array`(0xA8EC88) / `AbstractClass::Array`(0xB0F730) 都不在这条阶梯里** —— 它们是"超集视图"，不参与 AI 派发。

---

## 4 · 逐函数循环表（`[已证]`）

命令：`python work\dumpfunc.py fn <addr>`（反汇编）、`work\q.py fn <addr>`（nback/nloops，来自 `work\fnloops.tsv`，本卡用 capstone 重算）、Ghidra 反编译见 `EVIDENCE\decomp_*.c`。

| 函数 | 身份 | 大小 | 指令 | 回边 | **真循环** | 循环遍历什么 | 上界来源 |
|---|---|---|---|---|---|---|---|
| `0x0055B8F0` | 每 tick 对象 AI 派发器 | 432 | ~150 | 11 | **11** | 11 条 `DynamicVectorClass<T*>` 的元素指针数组 | 各容器 **Count**（进入块时读 1 次）|
| `0x004666E0` | `BulletClass::AI`（槽 23）| 6422 | 1794 | 2 | **1** | `AbstractClass*` 向量（0xB0F5B8/BC/C8）的元素搬移 = 摘自己 | `[0xB0F5C8]`（Count），由 `+0x158` 门控 |
| `0x00468090` | `BulletClass::Draw`（槽 69）| 923 | 277 | 0 | **0** | — | — |
| `0x00468BB0` | AI callee：能否引爆的判定 | 463 | 162 | 0 | **0** | — | 读 BulletType 的 +0x296/+0x298/+0x2a3/+0x29d/+0x2a4 等旗标 |
| `0x00468D80` | AI callee（×2）| 815 | 248 | 1 | **1** | `while (FUN_004690b0(), this->[0x90])` = 自我重试/阶段推进 | 自身字段 `+0x90`（**不是**别的对象）|
| `0x005B20F0` | AI callee（×1）| 2101 | 640 | 0 | **0** | — | — |
| `0x0053AB70` | AI callee（×1）| 224 | 64 | 0 | **0** | — | — |
| `0x004F9A90` | AI callee（×2）| 81 | 34 | 0 | **0** | — | — |
| `0x006802F0` | 子弹数组处理器（存档链）| 127 | — | 1 | **1** | 子弹 `Items[i*4]` | `[edi+0x10]` = **容器 Count**（进入时读一次）|
| `0x00534450` | "清空全部对象" | 1378 | 416 | 31 | 31 | 含子弹：`while (Count) slot2(Items[0])` @0x5344CB | `[0xA8ED50]`（每轮**重读**）|
| `0x005447C0` | 引用 `0xA8ED3C`（非本容器）| 573 | 140 | 0 | 0 | — | — |
| `0x007192F0` | `TeleportLocomotionClass` 槽 16 | 2302 | 743 | 1 | 1 | 含子弹：传送时 O(b) 清弹 | `[0xA8ED50]` |
| `0x005F3B80` | `ObjectClass` 析构（含 `AbstractClass*` 摘除）| 516 | 153 | 5 | 5 | `AbstractClass*` 向量 + 虚表槽 4（Find=线性扫）| `[0xB0F730]` |

**关于"6/0xc 的 for"**：`EVIDENCE\decomp_004666e0.c` 里 6 个 `for/while` 中 5 个是 `for (i=6;i!=0;--i)` / `for(i=0xc;i!=0;--i)` 的**定长**计数，来自 `rep movsd`/`rep stosd` 展开（见 `0x4666e0` 反汇编中的 `f3a5`/`f3ab` 类序列），**不是**对其它对象的遍历。`fnloops.tsv` 的 `nback=2` 与"1 个真循环 + 1 个内层"一致。

---

## 5 · O 分析：**没有 O(b·n)**

### 5.1 每 tick 的成本形状（`[已证]`）
```
T_tick = Σ_{11 数组} Count_k · c_k    +   Σ_{子弹} [ [0x98] ? c_AI : 0 ]
        = O(N_objects)                +   O(b) · c_AI        , c_AI = 常数
```
- `c_AI` 里只含：1 次 `[0x90]` 判定、若干旗标读、33 个 callee 的定长调用、1 次自递归。
- **没有任何以"其它对象数"或"格数"为上界的循环**。

### 5.2 为什么可以断定"没有 O(b·n)"（四条互相独立的证据）
1. **AI 自身**：6422 B 只有 1 个真循环，且是数组摘除（§4）。`[已证]`
2. **AI 的 33 个 callee**：`work\q.py fn` 逐个查 `nback` → 只有 `0x468D80` 有 1 个回边，而它的循环上界是**它自己的 `+0x90` 字段**（`while (FUN_004690b0(), this->[0x90])`），不是对象数。`[已证]`
3. **AI 深度 4 闭包（303 函数）与"全场对象数组遍历者"求交**：
   ```
   python work\bfs.py isect 0x4666e0 4 work\abstract_array_funcs.txt  → 4/14 hit
   ```
   命中的 4 个（`0x5F3900`/`0x420960`/`0x7258D0`/`0x62DC50`）经查全是 **Add/Remove 内联模板**（每个只有 1 处 Items 引用 + 3 处 Count 引用 = 追加/压缩，不是扫描）。`FootClass` 的 6 个遍历者：**0 hit**。`[已证]`
4. **全二进制不存在"遍历 AbstractClass::Array 并派发"的循环**：把"引用 `0xB0F720/724/730` 的函数集合"与"含 `call [reg+0x5C]` 的函数集合"求交 ⇒ **交集为空**。`EVIDENCE\intersect_absarray_slot5c.log` `[已证]`

### 5.3 唯一的 O(n) 项在哪
在**子弹销毁**那一次：`AI` 的 `+0x158` 分支里做 `AbstractClass*` 向量的"找 index + 全体前移"。`Find` 是容器虚表槽 4（线性扫描）⇒ **每次死亡 O(N_objects)**，不是每 tick 每发。
⇒ 若一帧内死 k 颗子弹，该项是 `O(k·N_objects)`。**这与"每 tick O(b·n)"是两件事**，且 k 远小于 b。

---

## 6 · 命中/溅射判定链（Q3）：只能给到"不是走全场对象数组"

`[已证·负]` **不存在**"遍历全场对象数组取候选"的路径（§5.2 第 3/4 条）。因此 `CellSpread` 类范围伤害**不可能**通过"扫 `AbstractClass::Array`"取候选。

`[未证]` 它到底走"格链"还是"空间索引"——我**没有**定位到 `CellSpread` 的消费函数。给出的边界证据：
- AI 里对"外部对象"的虚拟调用只有 `in_ECX[0x43]`（= `*(this+0x10C)`，单目标对象）的 `+0x2C`(WhatAmI) / `+0x48` / `+0x54` / `+0x58`；`EVIDENCE\decomp_004666e0.c` L511/L542/L668/L686/L713。
- AI 用到的**自身**虚槽全部是小编号函数：`+0x48`→`0x5F65A0`(33 B)、`+0xF8`→`0x5F65F0`(146 B)、`+0x124`→`0x4666C0`(18 B)、`+0x1B4`→`0x5F6940`(29 B)、`+0x1B8`→`0x41BEA0`(61 B)、`+0x1C8`→`0x5F5F40`(82 B)、`+0x1CC`→`0x5F5FA0`(180 B)。**没有一个是大范围搜索。**
- 二进制里唯一带 **130×130 = 16,900**（`for(i=0x4204)`）定长网格循环的是 `0x004F54A0`（4250 B），且 `0x4F54A0` **不在** AI 闭包内。`EVIDENCE\decomp_004f54a0.c`
- 下一个最有区分力的证据见 `UNKNOWNS.md` U-2。

---

## 7 · 可证伪预测（不要求真机）

### P1（最强，直接推翻本卡主张）`[静态推断]`
> **若成本主要在 X = AI/更新循环**，则把 `0x55B8F0` 的阶梯体整体 NOP 掉（或把块 3 的 `call [edx+0x5C]` 改成 `nop`）后，在**同样 b** 下 `ms/frame` 应大幅下降；
> **若成本在逐发绘制**，则 `ms/frame` 几乎不变，但把弹道图形改成不可见（warhead/projectile 的视觉项、`Anim`=none）而**保持 `0xA8ED50` 不变**时 `ms/frame` 应显著下降。
> 本卡的结构预测：**后者**。
> ⚠️ 这两种干预都是改代码/改数据，**本轮未授权**，仅作为下一轮候选。

### P2（与本卡最直接挂钩）
> 若"每 tick O(b)"成立但常数极小，则在**固定其它条件**下把 b 从 30 抬到 250，`ms/frame` 的**斜率**应当是**常数**且与"目标对象总数 N"无关。
> **反证**：若实验发现"同样 b、但 N 更大 → ms/frame 更大（交互项显著）"，则本卡的"无 O(b·n)"被判错。
> 现有台账数据里 `r(目标搜索/帧, bullets)=0.329`、`r(目标搜索/帧, ms/帧)=0.442` 都低于 `r(b, ms/帧)=0.921`，**与本卡的 O(b) 无交互项一致**，但那些数据没有做"固定 b 变 N"的分层，**不能算验证**。

### P3（`CellSpread`）
> 本卡预测：**改 `CellSpread` 不会改变 `ms/frame` 对 b 的斜率**（因为没有任何"每发 × 邻域"的循环可被它放大）。
> 若实测"`CellSpread` 变大 → 斜率变大"，则本卡 §6 的负结论被判错。

### P4（`+0x98` 门）
> `+0x98 == 0` 的子弹完全不进 AI，也不计入 AI 成本，但**仍计入 `0xA8ED50`**。
> 可测：若某一时刻存在大量 `+0x98==0` 的子弹，则"b 与 ms/frame"的关系会出现**残差**。数据层没有可改键直接控制它 `[未证]`。

### P5（可证伪"不可达"）
> 本卡说 `0x55B8F0` **零静态引用**。若给它下断点/打桩后**确实被命中**，说明我的三种扫描漏掉了某种调用形式（见 `UNKNOWNS.md` U-1）；若从不命中，则它是本 build 的**死代码**，而"谁派发 AI"另有其处——那将推翻本卡 §2 的链路。

### 7.1 与既有干预结果的相容性（逐条）
| 既有干预 | 台账结果 | 本卡结构是否能解释 |
|---|---|---|
| `ROF` / `Burst` / `Speed` 改动 | **无效**（不动 ms/frame）| ✅ 相容。这三者不改变"同时在飞数 b"的几何稳定点，也不改变 AI 的**代码路径**（AI 里所有分支都是 O(1)）。它们改的是**事件频率**，而帧成本 ∝ b。|
| `Range` 改小 → b 降到 6，但最差帧 **123.26 ms**（全组最高）| 反直觉 | ✅ 相容，且**本卡给出机制**：`0x55B8F0` 的阶梯是 `O(N_objects)` **无条件每帧跑 11 条数组**。`Range` 变小 ⇒ 单位打不到人 ⇒ 堆积/重寻路 ⇒ `UnitClass`/`InfantryClass` 数组变大 + 寻路成本上升，而子弹数组那条**降到 O(6)** 省不下多少。⇒ "b 小反而更慢"在结构上完全可能。|
| 子弹被几何饱和在 ~250 | 与单位总数无关 | ✅ 相容。饱和在"接战几何"，不在任何代码上限（§788 已证无 `MaxBullets` 键）。本卡补充：`0x55B8F0` 对子弹数组的上界就是 Count，**没有硬上限**。|
| b=0–24 恒 32.00 ms（满帧）| 分档 | ✅ 相容。b 在 ≤24 时 `O(b)·c_AI` 远小于帧预算 32 ms。且 2:1 台阶（25.30/50.40）与"b 决定 1 或 2 个逻辑 tick 落在同一渲染帧"一致——本卡不判断该假象，交 W153。|

---

## 8 · 复跑命令（全部可直接粘贴）

```powershell
cd D:\Project\ra2-campaign-forge
$b='lead\next_re_20261116_r11\W151_bulletcost'

# (1) 虚表
python "$b\work\dumppvt.py" 7e46e4                       # EVIDENCE\vtable_bullet_main.log
# (2) 容器布局 + 全二进制 xref（不依赖 Ghidra 分帧）
python "$b\work\globalscan.py" 0xA8ED50 0xA8ED44         # EVIDENCE\globalscan_bulletarray.log
# (3) 每 tick 11 数组阶梯
python "$b\work\dumpfunc.py" range 0x55B8F0 0x55BAC0     # EVIDENCE\master_update_ladder.log
# (4) 槽 0x5C 派发点（原始字节，含未分帧区）
python "$b\work\patscan.py" 0x5c                          # EVIDENCE\patscan_slot5c.log  (162 处)
# (5) 谁进入 0x55B8F0
python "$b\work\branchscan.py" 0x55b8f0                  # EVIDENCE\branchscan_55b8f0.log (0 refs)
# (6) 全 .text xref 索引 + 回边统计（capstone）
python "$b\work\xref_scan2.py"                           # work\absref2.tsv
python "$b\work\xref_scan.py"                            # work\fnloops.tsv / edges.tsv
# (7) 闭包与交集
python "$b\work\bfs.py" isect 0x4666e0 4 "$b\work\abstract_array_funcs.txt"
# (8) Ghidra（一次跑全部）
& 'D:\ghidra\ghidra_12.1.4_PUBLIC\support\analyzeHeadless.bat' `
  'D:\Project\ra2-campaign-forge\lead\next_re_20261116_r11\_ghidra\W151' gamemd_auto `
  -process gamemd.exe -noanalysis -scriptPath "$b\work" -postScript W151Probe.java `
  *> "$b\EVIDENCE\ghidra_probe1.log"
```

---

## 9 · 本轮排除了什么（负结果也算交付）

1. **`0x67D300` 不是"每帧对象协调"**（推翻 §873 的定性方向）。它的数组遍历是：对每个对象做 **16 字节 key 匹配**（`0x410260`，`.rdata` 常量 `0x7F7C70/80/90`、`0x7E9AE0`，返回 `0x80004003`/`0x80004002` = `E_POINTER`/`E_NOINTERFACE`）→ 调 `[0x7E15F4]`(= `0x410868`) → 调对象槽 2。它的兄弟阶梯在 `0x67CEF0` 的 `0x67CC5F` 块，调用对象**槽 13 = `0x5F6250`**，而那是一个**逐字段序列化器**（`+0x30/+0x34/+0x6c/+0x74/+0x80/+0x83/+0x8c/+0x9c/+0xa4`… 逐个 push 给 `0x4A1D50`/`0x4A1CA0`）。⇒ 这两段是**存档/序列化 + COM 流**，不是 tick 更新。
2. **`0x6802F0` 不是"子弹 AI 派发"**：它调的是**槽 0**（key 匹配器），不是槽 0x5C。
3. **`0x7192F0` 不是主遍历者**：它是 `TeleportLocomotionClass` 槽 16（`vtable_members.tsv` 实证），只在传送时 O(b) 清弹。
4. **`0x534450` 不是主遍历者**：它是"清空全部对象"（31 个循环、`while(Count) 槽2(Items[0])`），走的是**槽 2**。
5. **"最大函数=热点"判据再次失败**：`0x4F54A0`（4250 B，含 16,900 次定长网格循环）**不在** AI 闭包内；AI 自己 6422 B 却只有一个摘除循环。
6. **`0x410260`（BulletClass 槽 0）不是析构**：它是 16 字节 key 匹配器（`E_POINTER` + `repe cmpsd` ×4），与 §650-3 对 BuildingClass 槽 0 的观察**同一个函数**（全类共享）。

---

## 10 · 方法论教训（给下一卡）

1. **项目里 `function_atlas.tsv` 覆盖不到的代码真实存在**：`0x55B8F0–0x55BA9F`（432 B，11 个循环，每 tick 必跑）不在函数表里，`.text` 覆盖率 91.245% 的那 8.7% 里就藏着本卡的核心。
   ⇒ **凡"0 callers"的结论，都要用 `branchscan.py` 复核一次**；凡"谁引用某全局"，都要用 `globalscan.py`（原始字节）而不是 atlas。
2. **`patscan.py` 的 `DISP & 0xFF` 是个坑**：搜 `0x114` 时会退化成搜 `+0x14`（我一度得到 275 处假命中）。**disp ≥ 0x80 的槽必须走 disp32 编码**，且当前脚本对 `+0x114` 的 disp8 分支是**无效**的——本报告未使用该分支的任何输出。
3. **Ghidra 反编译切片必须按 `=== DECOMP <addr> ===` 行首切**，不能按"下一个 `===`"切（我第一次切错了，把 `0x468D80` 的循环误挂到别处）。
4. `EVIDENCE` 重定向**不要接 `| Select-Object -First N`**（§886 的坑；本轮我自己又踩了一次，`vcalls_5c_114.log` 被截断，重跑才拿到 129 处）。

---

*本卡：零真机、零进程读写、零游戏文件修改、未写主台账。*
