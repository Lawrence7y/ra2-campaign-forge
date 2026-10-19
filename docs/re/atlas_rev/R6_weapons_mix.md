# R6 补写 atlas 新章 §16 + §17 —— 锚定补丁块与交付回执
> **任务**：task-8（流 R6）  **执行方**：DSH 子代理 `atlas-r6-weapons`  **模式**：read-only（不改 atlas / 不改任何既有 docs/re/*.md / 不启动游戏 / 不改二进制）
> **基线**：`ra2youli/gamemd.exe` MD5 `4f37486e5b0dbe2ae5f45aeee0f98367`，4,825,360 B，ImageBase `0x400000`，FileOffset = VA − 0x400000（.text/.rdata/.data 三段；.rsrc/.detour 不适用）
> **本文件性质**：**只产出补丁块 + 回执**。atlas 唯一写者是 Lead；本任务未触碰 `docs/re/ARCHITECTURE_ATLAS.md`（写前写后 MD5 见 [5]）。

---

## 0. 交付概览

| 项 | 值 |
|---|---|
| 新增章 | §16 武器/弹头/伤害与生产经济；§17 MIX 虚拟文件系统加载链（编号由 Lead 指定，未自选） |
| 补丁块 | **2** 条，均为 `APPEND_SECTION`，锚点 = atlas `L1981`「## 附录 DA1 …」行 |
| 机器可读断言 | `out/re_work/atlas_rev/R6/claims_R6.txt`，**405** 条（本任务新取值 82 条 + 复用既有只读断言库 323 条，逐条已与基线复核一致） |
| 门禁 | `verify_anchors.py` **323/323 PASS**；`audit_bytes.py claims_R6.txt` **405/405 OK** |
| 最大单点新证 | **WarheadTypeClass.Verses 的物理偏移 = `+0xA0`（不是源文档记的 `+0xB0`）**，见 PATCH-R6-01 §16.3 |
| 最大风险 | §16 触及「随机数消费序」红线（局内 PRNG 27 处调用点），任何伤害/AOE 侧优化必须走 MP 门控矩阵 + 真机对拍，禁止宣称零风险 |

---

## 1. 锚点核验（实跑 grep，贴命中行号）

命令（实跑原文）：

```powershell
PS D:\Project\ra2-campaign-forge> python -c "import re;ls=open(r'docs/re/ARCHITECTURE_ATLAS.md',encoding='utf-8').read().splitlines();print([(i+1,l) for i,l in enumerate(ls) if l.startswith('## 附录 DA1')])"
[(1981, '## 附录 DA1 · 勘误登记（雷达挂钩地址与 G-10 覆盖，2026-09-27）')]
```

即：工具 `grep(pattern="^## 附录 DA1", docs/re/ARCHITECTURE_ATLAS.md)` 命中 **唯一 1 行 = L1981**，无第二处，可作为 `APPEND_SECTION` 唯一锚点。

- **锚点行号**：`L1981`（atlas 共 2001 行，MD5 `6e790b55b2709ff5c41ad3f73f7e49e4`）
- **该行前 40 字符（逐字）**：`## 附录 DA1 · 勘误登记（雷达挂钩地址与 G-10 覆盖，2026-09`
- 动作语义：**在该行之前**插入以下整章（Lead 按流号顺序插入，行号漂移由 Lead 处理）。

---

## 2. 补丁块

### PATCH-R6-01  §16 武器/弹头/伤害与生产经济（新章，APPEND_SECTION）

- **目标锚点**：`L1981` ｜ 该行前 40 字符原文：`## 附录 DA1 · 勘误登记（雷达挂钩地址与 G-10 覆盖，2026-09`（实跑 grep 命中 L1981，唯一）
- **动作**：`APPEND_SECTION`（插入到 `## 附录 DA1` 之前；**不含 TOC 修改**）
- **现状问题**：atlas §0–§12 全库**零**覆盖武器/弹头/伤害/生产域（实测 `grep "0x489280|Warhead|DamageArea" docs/re/ARCHITECTURE_ATLAS.md` → **0 命中**）；仅有 3 处外围提及（L517 BulletClass 第二虚表剔除、L1722/L1803 `BulletClass` 尺寸 352 B）。缺失导致：① 开火链的虚表分发契约（v[243]）无权威表，钩子极易漏挂 Aircraft/Unit/Infantry 覆写路径；② 伤害结算的 PRNG 消费点与 §12.2 红线之间没有可追溯链条；③ `WarheadTypeClass`/`FactoryClass` 的成员偏移无实证表（源文档存在错位，见 [3] 勘误）。
- **替换文本**（完整可直接粘贴）：

````markdown
## 16. §16 武器/弹头/伤害与生产经济 (Weapons, Warheads, Damage & Production Economy)

本章给出「扣扳机 → 弹体飞行 → 爆点结算 → 建筑出厂」的**架构级契约**：虚表分发拓扑、关键 VA 表、与其他子系统的确定性契约、未闭环项。
地址基线：`gamemd.exe` 1.001（MD5 `4f37486e5b0dbe2ae5f45aeee0f98367`）；`FileOffset = VA − 0x400000`（仅 .text/.rdata/.data 三段）。机器可复核断言库：`out/re_work/atlas_rev/R6/claims_R6.txt`（`tools/audit_bytes.py` 405/405 OK）。

> **证据等级图例（本章遵守）**
> - `[实证]`：本任务以 **VA + 原始机器码 + Capstone** 亲自复算，且断言已落入 `claims_R6.txt`（可一键复跑）；
> - `[实证·引]`：结论来自源文档（`weapons_damage_production.md` S24/S26）的字节断言，该断言已落入既有断言库并被 `tools/audit_bytes.py` 全 OK；本任务另行抽验了其中的**入口/阈值/魔数/关键字段**锚点；
> - `[推演]`：由已实证代码结构推定（ABI/数据流/布局三重一致性）；
> - `[待实测]` / `[待定位]`：静态无法闭环者，一律如实标注并给下一步取证方法（见 §16.7）。
> **禁令**：本章不启动游戏、不注入、不改二进制；未真机运行的验证一律不写成「实测」。

---

### 16.1 开火链拓扑与 v[243] 分发契约 [实证]

**入口**：`TechnoClass::Fire` = 主虚表 **v[243]** 槽 `0x007F4D2C → 0x006FDD50`（序言 `55 8B EC 83 E4 F8 81 EC A4`）。

| 类 | 主虚表基址 | v[243] 槽址 | v[243] 目标 | 与 Fire 本体的关系 |
|:---|:---:|:---:|:---:|:---|
| `TechnoClass` | `0x007F4960` | `0x007F4D2C` | **`0x006FDD50`** | 本体（武器选型 / 弹体装配 / ROF / Ammo / 播音） |
| `BuildingClass` | `0x007E3EBC` | `0x007E4288` | **`0x006FDD50`** | 直接复用本体（建筑无独立开火实现） |
| `FootClass` | `0x007E8C94` | `0x007E9060` | **`0x006FDD50`** | 未覆写（继承本体） |
| `AircraftClass` | `0x007E22A4` | `0x007E2670` | `0x00415EE0` | 薄包装 → 本体 |
| `UnitClass` | `0x007F5C70` | `0x007F603C` | `0x00741340` | 薄包装（补载具特判）→ 本体 |
| `InfantryClass` | `0x007EB058` | `0x007EB424` | `0x0051DF60` | 薄包装 → 本体 |

> **〔勘误 R6-E1〕** `docs/re/weapons_damage_production.md:37,40` 的 §1.1 表把 `FootClass` 记为 `0x415EE0`、把 `AircraftClass` 记为「与 Foot 共享 `0x415EE0`」。本基线实测：**`FootClass` v[243] = `0x006FDD50`（本体直挂）**，`0x00415EE0` 属 **`AircraftClass`**（`0x007E2670`，断言 `claims_R6.txt:0x007E2670`）。

**契约（钩子必须遵守）**：任何针对开火链的 Hook 必须挂**共享本体 `0x006FDD50`**，不得逐类挂虚表槽——否则 `UnitClass / InfantryClass / AircraftClass` 三条覆写包装路径必然出现覆盖缺口（同 `targeting_spatial.md` §1.3 的教训）。

**同域虚表事实**：`BulletClass` 主虚表 `0x007E46E4`，**v[23] = `0x007E4740 → 0x004666E0`（`Update`）**；`ReceiveDamage` 的默认实现是 `TechnoClass` **v[91] = `0x007F4ACC → 0x00701900`**，但**五个子类各自覆写 v[91]**（见 §16.4 表）——这一点直接决定「承伤统计型 Hook」的覆盖面。

---

### 16.2 BulletClass：装配 → 飞行 → 引爆 [实证]

**装配**：`BulletClass::Construct` `0x004664C0`（尾声 `0x0046655D: C2 1C 00` = `ret 0x1C`，7 个栈参 callee 清栈）。参数落位（逐条实证）：

| 栈参序号 | 形参 | 写入偏移 | 断言 |
|:---:|:---|:---:|:---|
| arg0 | `BulletTypeClass*` | `this+0xAC` | `0x004664FB: mov [ecx+0xAC], eax` |
| arg1 | `AbstractClass* pTarget` | `this+0x10C` | `0x004664C8: mov [ecx+0x10C], edx` |
| arg2 | `TechnoClass* pOwner` | `this+0xB0` | `0x00466501: mov [ecx+0xB0], esi` |
| arg3 | `int damage` | `this+0x6C` | `0x004664F6: mov [ecx+0x6C], edx` |
| arg4 | `WarheadTypeClass*` | `this+0x128` | `0x004664DC: mov [ecx+0x128], edx` |
| arg5 | `int speed` | `this+0x110` | `0x004664D2: mov [ecx+0x110], edx` |
| arg6 | `bool bright` | `this+0xE0` | `0x004664E6: mov [ecx+0xE0], dl` |

**尺寸**：`BulletClass` 实例 352 B（`0x160`），由 `v[12] @ 0x0046B540: B8 60 01 00 00 C3` 实证——与 atlas §11.2 / §10.3（352 B 专用定长桶）一致，本章不重复建账。

**飞行**：`BulletClass::Update` = **v[23] @ `0x004666E0`**（序言 `55 8B EC 83 E4 F8 81 EC 98 01`）。每帧推进 `Vector3D<double>` 速度、做落点/阻挡地图查询、命中判定，命中后转 `BulletClass::Fire 0x00468D80`（序言 `83 EC 30 53 56 8B F1 33`）→ `Detonate`。

**引爆**：`BulletClass::Detonate` `0x004690B0`（序言 `55 8B EC 83 E4 F8 81 EC 94`）。弹头字段读取点（实证）：

| 读取点 | 指令 | 字段 |
|:---|:---|:---|
| `0x00469180` | `D9 80 24 01 00 00` = `fld dword [eax+0x124]` | `Warhead.CellSpread`（AOE 半径，决定是否走范围路径） |
| `0x00469705` | `8A 88 6C 01 00 00` = `mov cl,[eax+0x16C]` | `Warhead.MindControl` |
| `0x00469D0C` | `8B 81 C4 01 00 00` = `mov eax,[ecx+0x1C4]` | `Warhead.MaxDebris`（残骸件数） |
| `0x00469A83` | `E8 F8 F7 01 00` = `call 0x00489280` | **转 `DamageArea`（范围伤害总入口）** |

**与 §2.5 渲染剔除红线的对齐契约**：atlas §2.5（L517）把弹道剔除挂在 `BulletClass` **第二虚表 `0x007E47F8` 的 `Draw`（`0x00468090`）**，并明令「**严禁触碰 `Update / Detonate`**」。本章为该红线补上事实依据：`Update(v[23]=0x004666E0)` 与 `Detonate(0x004690B0)` 是**物理与伤害结算本体**，且 `Detonate` 内部直接消费局内/局外两套 RNG（见 §16.4 表）。杆杆剔除只能停留在 `Draw` 表现层。

---

### 16.3 WarheadTypeClass 物理布局与 Verses 表 [实证]（+ 一处源文档勘误）

**装载器**：`WarheadTypeClass::LoadFromINI` = **`0x0075D3A0`**（序言 `81 EC 3C 01 00 00 53 55 56 57`；`0x0075D3B1: 8B F1` = `mov esi,ecx` 是函数体内**唯一**一次 `esi` 赋值，故 `esi ≡ this` 全程成立；尾声 `0x0075DEAC: C2 04 00` = `ret 4`）。

**A. 已实证字段（读写点均在 `LoadFromINI` 内）**

| 字段 | 偏移 | 类型 | 实证锚点 |
|:---|:---:|:---:|:---|
| **`Verses[11]`** | **`+0xA0`** | `double[11]`（`+0xA0 … +0xF7`） | `0x0075DE06: 8D 9E A0 00 00 00` = `lea ebx,[esi+0xA0]`；`0x0075DE0C: BD 0B 00 00 00` = `mov ebp,0xB`（11 次）；`0x0075DE48: DD 1B` = `fstp qword [ebx]`；`0x0075DE52: 83 C3 08` = `add ebx,8`；`0x0075DE55: 4D` = `dec ebp` |
| `CellSpread` | `+0x124` | `float` | `0x0075D3D2: D9 86 24 01 00 00`（`fld`）/ `0x0075D3EB: D9 9E 24 01 00 00`（`fstp`） |
| `CellInset` | `+0x128` | `float` | `0x0075D40A: D9 9E 28 01 00 00` |
| `PercentAtMax` | `+0x12C` | `float` | `0x0075D429: D9 9E 2C 01 00 00` |

**B. Verses 的语义闭环 [实证]**
- INI 键字面量 = `"Verses"` @ `0x00847C38`；**默认值串** @ `0x00847C40` = `100%%,100%%,…,100%%`（**恰好 11 项**，与 11 种 `ArmorType` 一一对应）；
- 解析后每个数值执行 `0x0075DE31: DC 0D 08 38 7E 00` = `fmul qword [0x007E3808]`，而 `0x007E3808` 的 8 字节为 `7B 14 AE 47 E1 7A 84 3F` = **double `0.01`** ⇒ `Verses=100%` 落库为 `1.0`，即**百分数→倍率**换算。

> **〔勘误 R6-E2｜P0 级〕** `docs/re/weapons_damage_production.md:126-129`（§2.1 布局表）把 `Verses[11]` 记为 **`Warhead+0xB0`**、把 `Deform` 记为 `+0xA8`。本基线实测：**`Verses[0]` 落在 `+0xA0`**（`Verses` 覆盖 `+0xA0…+0xF7`），因此 **`+0xB0` 实为 `Verses[2]`**（Plate/装甲档位之一）。
> **影响面（产品决策级）**：任何按源文档偏移写 `+0xB0` 的补丁/工具会把**第 3 档护甲乘数**当成数组起点写，静默错位 8 个 double；按 `+0xB0` 读取「全部 11 项」会越读 `+0xF8…+0x107` 的非 Verses 字段。源文档 §2.1 的其余偏移在 `+0x124` 起与本基线**一致**（CellSpread/CellInset/PercentAtMax 逐条实证）。

**C. Verses 的「施加点」仍未定位 [待定位]**
- 本任务对 `.text` 全段（`0x00401000`–`0x007E1000`）做了两类模式扫描：
  1. `fld qword ptr [reg + reg*8 + 0xa0] / [+0xb0]` —— **0 命中**；
  2. 任意指令含 `*8` 且位移 `+0xa0]` / `+0xb0]` —— **0 命中**。
- 因此**未能在本基线上定位 `Verses[armor]` 的乘算点**（[待定位]）。同时，源文档 `weapons_damage_production.md:215,473` 声称「Verses 应用点在 `ReceiveDamage` 归一化段（`0x701939` 起）」，本任务实测该处是**火力/伤害归一化**而非 Verses 乘算：

```asm
0x00701939  DB 44 24 14          fild  dword ptr [esp+0x14]      ; 原始伤害 -> double
0x00701945  FF 90 84 00 00 00    call  dword ptr [eax+0x84]      ; v[0x84] GetType (TechnoType*)
0x00701952  E8 D9 A3 E0 FF       call  0x0050BD30              ; HouseType 火力系数 (this=House@+0x21C)
0x00701957  DC 8E 58 01 00 00    fmul  qword ptr [esi+0x158]     ; Techno.FirepowerMultiplier
0x0070195D  DC 7C 24 14          fdivr qword ptr [esp+0x14]      ; 伤害归一化 = dmg / (coeff × mult)
0x00701961  E8 9A 45 0C 00       call  0x007C5F00              ; double -> int 截断
0x0070196C  89 03                mov   dword ptr [ebx], eax     ; 写回调用者提供的伤害槽
```
> **〔勘误 R6-E3〕** 源文档把 `0x701939` 段的功能标注为「Verses 应用点」**不成立**（该段无任何数组索引访存；`fmul [esi+0x158]` 是 `Techno+0x158` 档位，非 `Warhead+0xB0`）。影响面：文档级的「护甲乘数在哪算」认知，不影响已落地的钩子（现网钩子清单未使用该结论）。

**D. 勘误的下一步取证（可执行）**：对 `WarheadTypeClass` 实例在 `+0xA0` 与 `+0xB0` 各下 8 字节写 watch（或静态回溯 `ReceiveDamage`/`DamageArea` 中 `WarheadTypeClass*` 的形参传递链），确认乘算点后即可把 `[待定位]` 升级为 `[实证]`。**在未闭环前，任何「按 Verses 加固/限频」的优化不得放行。**

---

### 16.4 伤害结算两条路径、子类覆写矩阵与 RNG 消费契约 [实证]

**A. 两条路径**
1. **点伤害（直击）**：`Detonate` 内 `Warhead.CellSpread == 0` → 直调承伤（`TechnoClass::ReceiveDamage 0x00701900`）；
2. **范围伤害（AOE）**：`CellSpread > 0` → `DamageArea 0x00489280`（序言 `55 8B EC 83 E4 F8 81 EC D4`）收集候选 → 逐个调承伤虚函数。

**B. `DamageArea` 的架构细节（全部实证）**[实证]

| 环节 | 锚点 | 说明 |
|:---|:---|:---|
| AOE 半径 | `0x004892DD / 0x00489347 / 0x004893C3 / 0x00489592` = `D9 86 24 01 00 00` | 反复 `fld dword [esi+0x124]`（`Warhead.CellSpread`） |
| 候选粗筛 | `0x004893D4 / 0x004893DE / 0x00489547` = `B9 88 78 88 00` | 与**索敌系统同一实例**的全局空间桶 `0x00887888`（20×20 桶） |
| 同心环表（计数） | `0x004895A3` = `8B 0C 85 D0 D3 7E 00` | `mov ecx,[eax*4 + 0x7ED3D0]`；该表是 `.rdata` **静态常数**，前 12 项 dword = `1, 9, 21, 37, 61, 89, 121, 161, 205, 253, 309, 369`（`claims_R6.txt:0x007ED3D0`） |
| 同心环表（偏移对） | `0x004895C7` = `66 8B 14 85 90 D4 AB 00` | `mov dx, word [eax*4 + 0xABD490]`；**`0x00ABD490` 落在 `.data` 虚拟尾（BSS），文件内无字节**，运行期填充 ⇒ 无法做文件级字节断言（已在断言库中显式排除） |
| 候选分配 | `0x004894AB / 0x0048975D / 0x0048A323 / 0x0048A3B1 / 0x0048A3F2 / 0x0048A449` = `call 0x007C8E17` | 每个候选 `DamageGroup` **逐个 `operator new`**（明确热点） |
| 候选释放 | `0x00489AE4 / 0x00489B33 / 0x0048A4A4 / 0x0048A4D0` = `call 0x007C8B3D` | 逐个 `operator delete` |

**复杂度定性**：`O(环格数 × 每格对象数) = O(πr² × 密度)`，且**每个候选一次堆分配**——这是全库武器域最贵的单点（源文档 §4.1 同结论）。

**C. 承伤虚函数的子类覆写矩阵 [实证]**（决定 Hook 覆盖面）

| 类 | v[91] 槽址 | v[91] 目标 |
|:---|:---:|:---:|
| `TechnoClass`（默认实现） | `0x007F4ACC` | **`0x00701900`** |
| `BuildingClass` | `0x007E4028` | `0x00442230` |
| `FootClass` | `0x007E8E00` | `0x004D7330` |
| `UnitClass` | `0x007F5DDC` | `0x00737C90` |
| `InfantryClass` | `0x007EB1C4` | `0x00517FA0` |
| `AircraftClass` | `0x007E2410` | `0x004165C0` |

> ⇒ **只挂 `0x00701900` 的 Hook 只能覆盖「未覆写 v[91] 的对象」**；要覆盖全部承伤需按上表 6 点分别挂，或挂到更上游的 `DamageArea`/`Detonate`（`0x00489280` / `0x004690B0`）。

**D. 随机数消费契约（与 §12.2 红线的接口）**[实证·引 + 本任务抽验]
- **局内同步 PRNG** = `ScenarioClass::Random`（`*(0x00A8B230)+0x218`），实现 `Randomizer::Random 0x0065C780` / `RandomRanged 0x0065C7E0`；
- **局外本地 RNG** = `Randomizer::Global`（`.data` `0x00886B88`，静态立即数装载 `B9 88 6B 88 00`），**不进同步流**；
- 本任务抽验的调用点（均在 `claims_R6.txt`）：`Detonate` L01/L02 `0x004690F0 / 0x00469121` 装载局外实例（震屏 ShakeX/Y，写 `0x0087F7EC / 0x0087F7F0`）；`ReceiveDamage` 内 9 处 RNG 中 4 处为局外（`0x00702169 / 0x007021D9 / 0x007026B3 / 0x007026D9`）、5 处为局内（`0x007022C8 / 0x0070232B / 0x00702473 / 0x0070253A / 0x007029D7`）。
- 每帧同步探针：`0x00650A90`（帧尾从局内 PRNG **恰抽 1 次**，回存 `0x00AFA26C`），与 `Compute_Frame_CRC 0x0064DAB0` 的折叠共同构成 §12.2 所述「每逻辑帧 2 次」口径（atlas §12.2 勘误 ASM-FIX2-1 不变，本章为其提供武器域侧调用点清单）。

**E. 确定性契约（架构级，禁止违反）**[推演·基于已实证控制流]
1. 不得增删武器链上任何一处局内 PRNG 调用（27 处清单见源文档 S26 §2，本任务抽验了其中承伤 5 处 + 引爆 6 处）；
2. AOE 候选的**枚举顺序**（格子链表序 ⊕ 空间桶序）不得置换——若两个被杀伤单位互换顺序，其残骸 RNG 消费时序即互换 ⇒ 帧 CRC 立刻分叉；
3. AOE 半径边界的浮点比较（`dist == radius`）在不同微架构上的舍入差异是真存在风险，未做真机对拍前**不得**宣称「等价」；
4. `WarheadTypeClass` 运行期可变字段不得缓存（`Verses` 本身除外）。

---

### 16.5 FactoryClass 生产时钟 [实证]（+ 一处源文档字段错位勘误）

**流水线（每环均已实证）**：

```text
DemandProduction 0x004C9C70 → 入队 QueuedObjects（+0x40 vftable / +0x44 Items / +0x50 Count）
StartProduction  0x004CA5A0 → 若 +0x58(在造对象) != 0 或 +0x50(队列数) <= 0 则拒绝；否则取 Items[0]
GetBuildTimeFrames 0x004C9FB0 → ecx = [ecx+0x58]（在造对象）→ call 0x006F47A0 GetBuildTime
                             → imul 0x4BDA12F7 ; sar edx,4  （等价 /54，0x004C9FC0..）
                             → clamp 1..255（0x004C9FD3 cmp eax,1 / 0x004C9FDE cmp eax,0xFF）
BuildingClass::FactoryUpdate 0x004500F0 → 每帧读 CurrentFrame [0x00A8ED84] 推进（0x00450126）
CompletedProduction 0x004CA1A0 → [ecx+0x24] == 0x36（54 步）则置位并记录完工帧
```

**字段表（以 `CompletedProduction` / `GetProgress` / `IsDone` 与 `StartProduction` 的访存为唯一依据）**：

| 偏移 | 语义 | 实证锚点 |
|:---:|:---|:---|
| `+0x24` | **建造步数**（`Production.Value`，完成判据 `== 0x36` = 54） | `0x004CA120: 8B 41 24`（`GetProgress` 返回值）；`0x004CA13C: 39 41 24`；`0x004CA1B3: 39 41 24`；`0x004CA1C3: 89 51 24`（清零） |
| `+0x2C` | 完工帧 `TimerStruct` 起始（`lea edi,[ecx+0x2C]` 后写 `[edi]=CurrentFrame`、`[edi+8]=0`） | `0x004CA1CC: 8D 79 2C`；`0x004CA1C6: 8B 35 84 ED A8 00` |
| `+0x38` | 完成后的延迟放置计数器（`CompletedProduction` 内被清零） | `0x004CA1CF: 89 51 38` |
| `+0x40 / +0x44 / +0x50` | `QueuedObjects`（`DynamicVectorClass`：vftable / `Items` / `Count`） | `0x004CA5C0: 8B 46 44`；`0x004CA5A4: 8B 46 50` |
| `+0x58` | **当前在造对象指针**（`TechnoClass*`；`GetBuildTimeFrames` 用它取建造总帧数，完工后被清 0） | `0x004C9FB0: 8B 49 58`；`0x004C9FB9: E8 E2 A7 22 00`（`call 0x006F47A0`）；`0x004CA1BA: 89 51 58` |
| `+0x5D` | `IsDifferent` 标志 | `0x004CA1C0: 88 41 5D` |
| `+0x68` | 手动/旁路分支哨兵（`-1` 表示已进入另一态） | `0x004CA144` / `0x004CA1F0` |
| `+0x70` | `IsSuspended`（资金/放置挂起，完工置 1） | `0x004CA1BD: 88 41 70` |

> **〔勘误 R6-E4｜P1 级〕** `docs/re/weapons_damage_production.md:243-251`（§3.1）表记 `ProgressTimer Production` @ `+0x20`、`TechnoClass* Object` @ `+0x50`。本基线实测：**54 步计数器在 `+0x24`（不是 `+0x20`）**，**在造对象指针在 `+0x58`（不是 `+0x50`；`+0x50` 是队列 Count）**。按源文档偏移读取会把「队列长度」当对象指针解引用（`+0x50` 是小整数，解引用即崩）。影响面：任何基于该表的工具/补丁（含建造加速类补丁）必须先订正偏移。

**「生产零 PRNG」认证**[实证·引]：源文档 S26 §5 对 `FactoryClass` 全域（`0x004C9000–0x004CB000`，8,192 B / 3,340 条指令 / 139 条 `call`）与 `BuildingClass` 工厂推进域（`0x0044FF00–0x00450400`，1,280 B / 424 条指令）做过 100% 全指令扫描，**命中 RNG 调用数 = 0**；本任务复核了其**判定阈值与魔数锚点**（`0x004CA133: B8 36 00 00 00`、`0x004C9FC0: B8 F7 12 DA 4B`、`0x00450126 / 0x004501D0` 的 `CurrentFrame` 读取）。⇒ 建造完成时刻是纯定点时钟函数。「建造时间有随机浮动」的说法在本基线上不成立。

**经济侧关联**：`HouseClass::Update 0x004F8440`（v[23]，序言 `83 EC 4C 53 55 56 8B F1`）每帧驱动工厂/超武/经济；前置依赖检查 `HouseClass::CanBuild 0x004F7870`（序言 `83 EC 3C 8A 44 24 44 53`）+ `0x0050B370` 是全库最重的可用性扫描之一（UI/AI 高频）。

---

### 16.6 §11 速查表并入建议：关键 VA 速查表（§16）

| VA | 名称/职责 | 证据等级 | 来源 |
|:---|:---|:---:|:---|
| `0x006FDD50` | `TechnoClass::Fire` 本体（**v[243] 共享入口**） | [实证] | §16.1；`claims_R6.txt` |
| `0x00741340 / 0x0051DF60 / 0x00415EE0` | Unit / Infantry / Aircraft 的 Fire 薄包装 | [实证] | §16.1 |
| `0x004664C0` | `BulletClass::Construct`（载荷装配，`ret 0x1C`） | [实证] | §16.2 |
| `0x004666E0` | `BulletClass::Update`（**v[23]**，飞行热点） | [实证] | §16.2 |
| `0x00468D80` | `BulletClass::Fire`（命中引爆） | [实证] | §16.2 |
| `0x004690B0` | `BulletClass::Detonate`（爆炸 + 双 RNG 域） | [实证] | §16.2 / §16.4 |
| `0x00489280` | `DamageArea`（CellSpread 分摊，环表 × 空间桶） | [实证] | §16.4 |
| `0x007ED3D0` | 同心环**计数表**（`.rdata` 静态常数，12 项） | [实证] | §16.4 |
| `0x00ABD490` | 同心环**偏移对表**（`.data` BSS，运行期填充，无文件字节） | [实证]（BSS 归属） | §16.4 |
| `0x00887888` | 全局 20×20 空间桶（伤害与索敌共用同一实例） | [实证] | §16.4 |
| `0x00701900` | `TechnoClass::ReceiveDamage`（**默认 v[91]**） | [实证] | §16.4 |
| `0x00442230 / 0x004D7330 / 0x00737C90 / 0x00517FA0 / 0x004165C0` | Building / Foot / Unit / Infantry / Aircraft 的 v[91] 覆写 | [实证] | §16.4 |
| `0x0075D3A0` | `WarheadTypeClass::LoadFromINI` | [实证] | §16.3 |
| `0x0075DE06` | `Verses` 数组起始 = **`Warhead+0xA0`** | [实证] | §16.3 |
| `0x00847C40` | `Verses` 默认值串（11 项 × `100%%`） | [实证] | §16.3 |
| `0x007E3808` | `Verses` 百分数→倍率常数 `0.01`（double） | [实证] | §16.3 |
| `0x004C9FB0` / `0x004CA1A0` / `0x004CA1A5` | `GetBuildTimeFrames` / `CompletedProduction` / 54 步阈值 | [实证] | §16.5 |
| `0x00772A42` | `WeaponTypeClass::CalculateSpeed` 回写 `Speed(+0xA8)` | [实证] | §16.5 关联 |
| `0x0065C7E0 / 0x0065C780 / 0x00886B88` | 局内 `RandomRanged/Random` 实现 与 局外 `Randomizer::Global` | [实证] | §16.4 |
| `0x00650A90` | 帧尾同步探针（每逻辑帧恰抽 1 次局内 PRNG） | [实证] | §16.4 |

---

### 16.7 §16 未闭环项（附可执行取证方法）

| # | 缺口 | 为何静态不闭环 | 下一步取证方法 | 级别 |
|:--:|:---|:---|:---|:--:|
| 1 | `Verses[armor]` 的**施加点**未定位 | 全 `.text` 未命中 `*8 + 0xA0/0xB0` 形态的 8 字节索引访存（0 命中）；可能经中间指针/临时变量 | ① `WarheadTypeClass+0xA0` 下 8B 写 watch；② 从 `ReceiveDamage 0x00701900` 与 `DamageArea 0x00489280` 的形参 `WarheadTypeClass*` 逆流回溯（`rdtsc`-free 静态回溯 or 动态断点） | **P1** |
| 2 | AOE 半径边界的浮点舍入跨 CPU 差异 | 需真机/多端 | 构造临界坐标（1 lepton 步进）单位，双端录像回放比对 `CurrentFrameCRC 0x00AC51FC` | P1 |
| 3 | `DamageArea` 候选枚举序的**设备级**复现 | 需运行期观察格子链表挂载序 | 在 `0x00489AE4`（释放点前）下断导出 `DamageGroup` 数组序，比对两端 | P1 |
| 4 | `CanBuild 0x004F7870` 内部前置表 | 46 KB 反汇编未逐一展开（源文档同项） | 单独立项：dump `0x004F7870`–`0x0050B400` 并建前置位图 | P2 |

---

````

- **证据**：等级 `[实证]`（本章全部 VA/字节均已复算并落入 `out/re_work/atlas_rev/R6/claims_R6.txt`，`tools/audit_bytes.py` 405/405 OK）+ `[实证·引]`（S26 全段扫描结论，本任务抽验其阈值锚点）；来源文档：`docs/re/weapons_damage_production.md:14-22,31-42,59-71,100-114,120-142,144-195,197-215,239-268,270-311,515-520,730-773,777-838`，本轮新增实证点见 `claims_R6.txt` PART R6-A。
- **影响面**：①**§11 速查表**——需并入 §16.6 的 20 行（新类/新表/新入口）；②**§12 契约**——§12.2「局内唯一随机数」需补挂武器域 27 处调用点清单的引用；③**§0 准则**——不冲突（本章不引入新公理，只补事实层）；④**§11.2/§11.3**——`BulletClass 0x160` 与本章一致，无需改；建议 §11.3 增加 `WarheadTypeClass`（Verses `+0xA0`）与 `FactoryClass`（+0x24/+0x58）两张子表。
- **不提交 TOC 修改**（按任务卡：TOC 由 Lead 统一重建）。

### PATCH-R6-02  §17 MIX 虚拟文件系统加载链（新章，APPEND_SECTION）

- **目标锚点**：`L1981` ｜ 该行前 40 字符原文：`## 附录 DA1 · 勘误登记（雷达挂钩地址与 G-10 覆盖，2026-09`（实跑 grep 命中 L1981，唯一）
- **动作**：`APPEND_SECTION`（紧接 PATCH-R6-01 的 §16 之后再插入；**不含 TOC 修改**）
- **现状问题**：atlas 全库**零**覆盖文件系统/MIX 域（实测 `grep "Mix|expandmd|BATTLEMD|CCFileClass" docs/re/ARCHITECTURE_ATLAS.md` → 仅 1 处无关命中 `BlitterFactory`）。缺失导致项目的**装机形态决策**（`expandmd98.mix` vs 散装 INI）在 atlas 层没有权威依据；且 `langmd.mix/language.mix` 的最高优先级事实、`BATTLEMD*.INI` 通配仅通文件系统的事实，都会直接影响「改哪些文件才会生效」。
- **替换文本**（完整可直接粘贴）：

````markdown
## 17. §17 MIX 虚拟文件系统加载链 (MIX Virtual Filesystem & Load Chain)

本章给出引擎「按名字要一个文件」时的完整解析链、MIX 优先级拓扑、容器装配与解密链、以及 INI 两条装载范式的架构契约。
基线同上（`gamemd.exe` 1.001，MD5 `4f37486e5b0dbe2ae5f45aeee0f98367`）。断言库：`out/re_work/atlas_rev/R6/claims_R6.txt`（`tools/audit_bytes.py` 405/405 OK）。

> 证据等级图例同 §16 开头（`[实证]` / `[实证·引]` / `[推演]` / `[待实测]`）。

---

### 17.1 三条通道与优先级链 [实证]

**通道定性**：

| 通道 | 机制 | 可见范围 | 优先级地位 | 关键地址 |
|:---|:---|:---|:---|:---|
| **A 散装文件** | `CreateFileA(原始名)`，相对 **CWD = exe 所在目录** | 仅游戏目录 | **最高**（同一请求内先于 MIX） | `0x00473D2D → 0x00431F10 → 0x0065CBF0 → 0x0065CC59 call [0x7E11BC]` |
| **B MIX 条目** | `MixFileClass::Find` 遍历全局优先级链表 + `CRC32(大写名)` 二分 | 全部已装载 MIX | 低于 A，链内 **FIFO（先装载者优先）** | `0x005B4430`；链表 `0x00ABEFD8` |
| **C CD 路径** | 仅次级装载器的**二次 `FindFirstFileA`** | 仅 CD 盘 | 仅在 `MAPS*/MOVIES*/MOVMD*` 等通配，且排在「原样尝试」之后 | `0x0047AF70 → 0x0047B020 → 0x0047B08A` |

**A 优先于 B 的字节证据**（`CCFileClass::Get_File` = `vtable 0x007E16B0` slot `+0x1C` = `0x00473D10`）：

```asm
0x00473D1D  F6 44 24 20 02   test byte ptr [esp+0x20],2   ; mode & 2（只读写盘）
0x00473D22  0F 85 11 01 00 00 jne  0x00473E39             ; → 直接走磁盘
0x00473D2D  E8 DE E1 FB FF   call 0x00431F10             ; ★先试散装文件
0x00473D34  0F 85 FF 00 00 00 jne  0x00473E39             ; 命中 → 磁盘读
0x00473D68  E8 C3 06 14 00   call 0x005B4430             ; ★失败才回落 MixFileClass::Find
```

⇒ 「同一名字既有散装又有 MIX 条目时，**散装赢**」在**分支顺序**层面为 [实证]；端到端行为仍需真机对拍（[待实测]，见 §17.6-2）。

**链内 FIFO 的两端证据**：
- **插入 = 尾插**：`MixFileClass` ctor 内 `0x005B3DE2: 8B 3D F0 EF AB 00`（取尾哨兵 `[0xABEFF0]`）→ `0x005B3E00: 89 77 04`（`mov [edi+4],esi` 挂尾）；
- **查找 = 从头开始**：`Find` 内 `0x005B44A1: 8B 2D E0 EF AB 00`（取头哨兵 `[0xABEFE0]` = 最早装载）→ 每轮二分条目表 `0x005B44E5: 3B F3`（`cmp esi,ebx`，`entry.id` vs CRC32）→ `0x005B44FD: 8B 6C 24 14`（`ebp = ebp->Next`，更晚装载者）。
=> **同名条目（CRC 相同）先装载者优先**。

> **注**：链表哨兵 `0x00ABEFDC / 0x00ABEFE0 / 0x00ABEFE8 / 0x00ABEFF0` 位于 `.data` **零填充虚拟尾（BSS）**，运行期才初始化 ⇒ **不可做文件级字节断言**（本任务已在断言库中显式排除，避免误报 NOREAD）。

---

### 17.2 装载序列与 `expandmd` 序号语义 [实证]

**入口**：`Init()` = `0x0052BA60`（唯一入口链 `0x0048CCCF: E8 8C ED 09 00 → call 0x0052BA60`）。关键调用点（地址即顺序）：

| # | 调用点 | 目标 | 内容 |
|:--:|:---|:---|:---|
| 0 | `0x006BD7EF` / `0x006BD81D` | `0x005B3C20` | **`LANGMD.MIX` / `LANGUAGE.MIX`（在 `Startup` 阶段，早于 `Init`）** |
| 1 | `0x0052BB64` | `0x005301A0` | `EXPANDMD99…00.MIX`、`RA2MD.MIX`、`RA2.MIX`、`CACHEMD/CACHE/LOCALMD/LOCAL.MIX` |
| 2 | `0x0052C307` | `0x00530000` | `ECACHE*.MIX` / `ELOCAL*.MIX`（`FindFirstFileA` 通配） |
| 3 | `0x0052C59C` | `0x00530460` | 次级：`CONQMD/GENERMD/…/MAPS*/MOVIES*/MOVMD*`（含 CD 感知通配） |
| 4 | `0x0052C5F3` | `0x005312A0` | `GLS*.PAL/SHP` 资源（**非 MIX**） |
| 5 | `0x0052C605` | `0x0052CB90` | `BATTLEMD*.INI`（见 §17.4） |

**`expandmd` 序号语义**（主装载器原文）：`0x005301BA: BF 63 00 00 00`（`mov edi,0x63` = 99 上界）→ `0x005301C4: 68 8C 66 82 00`（`push "EXPANDMD%02d.MIX" @ 0x0082668C`）→ `0x005301CA: E8 25 8D 29 00`（`call 0x007C8EF4` CRT `sprintf`）→ `0x005301E7: FF 52 14`（`call [edx+0x14]` 存在性探测）→ `0x00530289: 4F`（`dec edi`）+ `0x0053028A: 0F 89 2F FF FF FF`（`jns 0x005301BF`，99→0 递减）。
=> 合法名必须是**两位补零** `EXPANDMD00.MIX … EXPANDMD99.MIX`（`expandmd1.mix` 不会被找到）；**序号越大越先装载 ⇒ 优先级越高**。

**`langmd/language` 的最早装载铁证**：`0x006BD7E8: 68 5C 0D 84 00`（`push "LANGMD.MIX" @ 0x00840D5C`）→ `0x006BD7EF: E8 2C 64 EF FF`（`call 0x005B3C20`）；`0x006BD818: 68 4C 0D 84 00`（`push "LANGUAGE.MIX" @ 0x00840D4C`）；而 `Init` 的调用点 `0x006BE041: E8 7A EC DC FF`（`call 0x0048CCC0`）在**地址序之后**。且 `0x006BD7CB: B9 FE FF FF FF` / `0x006BD7D0: E8 DB B8 DB FF` 先把 CD 状态压成 `-2`（无需 CD）以短路 MIX ctor 的 CD 门禁。
=> **完整优先级（高→低）**：散装文件 > `langmd.mix` > `language.mix` > `expandmd99 … expandmd00` > `ra2md.mix` > `ra2.mix` > `cachemd.mix` > `cache.mix` > `localmd.mix` > `local.mix` > `ecache*` > `elocal*` >（次级）`conqmd … movies*`。
=> **推论（对 mod 直接有效）**：`expandmd99.mix` **无法**覆盖 `langmd.mix / language.mix` 内的同名（CRC 相同）条目；要覆盖这类条目只能靠**散装文件**。

---

### 17.3 MIX 容器装配与加密链 [实证]

**装配点**：`MixFileClass::MixFileClass(name, pPublicKey)` = `0x005B3C20`（序言 `81 EC DC 01 00 00 53 56`）。要点：
1. **每 MIX 装载前的 CD 门禁**：`0x005B3C58: A1 D0 C1 81 00`（读 CD 状态 `[0x81C1D0]`）→ `0x005B3C66: FF 15 30 4C 7E 00`（`call [0x7E4C30]`，即 `FileClass::CDCheck`，slot0 = `0x004790E0`）；`0x004790E4: 83 F8 FE`（`cmp eax,-2` ⇒ 状态「全本地/无需 CD」直接返真）。CD 子系统**只做门禁**，不是查找链的一部分。
2. **明文 4 字节头**：`format word + flags word` 恒为明文；`flags` bit1 = 加密 ⇒ 走 `PKStraw`，否则旁路（这就是本项目自产的**未加密** `expandmd98.mix` 能被直接读的原因）。
3. **解密链**：`PKStraw::PKStraw 0x00633050` → `Set_Key 0x00633110` → `Attach 0x006330C0` → `Get 0x00633130`：
   - 密钥块长度按模数位长动态算：`0x0063317F: 8B 80 00 02 00 00`（读 `keyStruct+0x200` = 位长−1）、`0x0063318E: B8 37 00 00 00`（`mov eax,0x37` = 55 = 56 字节密钥−1）⇒ 320 bit 模数下密钥块 = **80 字节**（= 2×40 字节 RSA 块）；`0x006331A6: E8 35 67 00 00`（`call 0x006C98E0` 读块）。
   - 公钥装配：`INIClass::BuildKeyStruct 0x0052A670` 内 `0x0052A6AF: BA 01 00 01 00`（`mov edx,0x10001`）⇒ **RSA 公开指数 e = 65537**；`0x0052A745: F3 A5`（`rep movsd`，拷出 **516 字节**公钥结构）；`BigNum<-DER 0x005C6370`（tag `0x02`）、公钥结构 ctor `0x00631F60`。
   - 公钥来源：内嵌 INI 文本 `[PublicKey]\n1=AihRvNoIbTn85FZRYNZRcT+i6KpU+maCsEqr3Q5q+LDB5tH7Tz2qQ38V` @ `0x007E1A80`；base64 字母表 @ `0x008189C8`。
   - **Blowfish 本体不在 exe 内**：字符串 `"blowfish.dll"` @ `0x00840A78`，其指针位于 COM 组件描述表 `0x007F3710`（首 dword = CLSID 指针），由绑定器 `0x006BEDB0` 动态加载。[实证]（表/串/绑定器）+ [推演]（该 COM 类即 MIX 用的分组密码；**`Blowfish.dll` 是运行前提**）。

**未闭环**：整包解密入 `MixFileClass+0x24` 的**填充点**未定位；`0x005B43E0`（被 `0x0053033B: E8 A0 40 08 00` 调用 + `0x00530342: 74 A0` 判定）实测为 `B0 01 C3` = `mov al,1; ret` —— **恒真桩**，即「bootstrap MIX 预载门槛」实际恒不触发（见 §17.5）。

---

### 17.4 INI 两种装载范式与 BATTLEMD 归并契约 [实证]

**范式对照（同一引擎内并存）**：

| 范式 | 名字来源 | 装载 API | MIX 内可读？ | 实例 |
|:---|:---|:---|:---:|:---|
| **通配** | 字面量通配串 | `KERNEL32!FindFirstFileA`（**纯文件系统**） | **否** | `BATTLEMD*.INI` @ `0x008261A8`（`0x0052CBA9: FF 15 08 12 7E 00`） |
| **显式名** | 字面量完整名 | `CCFileClass(name)` + `Open`（磁盘优先 → MIX 回落） | **是** | `BATTLEMD.INI` @ `0x00826198`（回退分支 `0x0052CCD6: E8 15 6D F4 FF → CCFileClass ctor`） |

**`BATTLEMD*.INI` 装载流程（`LoadBattleMdIni 0x0052CB90`，序言 `81 EC B4 01 00 00 53 56`）**：

```asm
0x0052CBA0  68 A8 61 82 00    push  "BATTLEMD*.INI"
0x0052CBA9  FF 15 08 12 7E 00 call  [0x007E1208]=FindFirstFileA   ; ★FS-only，看不到 MIX 条目
0x0052CBB1  83 FE FF          cmp   esi,-1                        ; INVALID_HANDLE_VALUE
0x0052CBB8  0F 84 0F 01 00 00 je    0x0052CCCD                    ; → 回退分支
...           每个枚举文件：CCFileClass ctor → CCINIClass → 0x004741F0 INIClass::Load
0x0052CC4E  68 98 61 82 00    push  "BATTLEMD.INI"
0x0052CC54  E8 C7 C0 29 00    call  0x007C8D20                    ; _stricmp(枚举名,"BATTLEMD.INI")
0x0052CC67  E8 A4 01 F4 FF    call  0x0046CE10                    ; ★归并进全局 Battle 表
0x0052CCAB  FF 15 0C 12 7E 00 call  [0x007E120C]=FindNextFileA
0x0052CCC5  3A C3             cmp   al,bl
0x0052CCC7  0F 85 92 00 00 00 jne   0x0052CD5F                    ; ★已见过 BATTLEMD.INI → 跳过回退
-- 回退分支（唯一 mix 感知的 BATTLEMD 通道）--
0x0052CCCD  68 98 61 82 00    push  "BATTLEMD.INI"
0x0052CCD6  E8 15 6D F4 FF    call  0x004739F0                    ; ★CCFileClass（磁盘优先 + MIX 回落）
0x0052CD25  E8 C6 74 F4 FF    call  0x004741F0 INIClass::Load
0x0052CD2C  E8 DF 00 F4 FF    call  0x0046CE10                    ; 同一归并函数
```

**归并契约（`Register_Battles 0x0046CE10`）**：
- 段名 `"Battles"` @ `0x0081B1D8`（`0x0046CE17: 68 D8 B1 81 00`）→ `0x0046CE1C: E8 3F 9B 0B 00` 取段条目数；
- 归并键 = `[Battles]` 段的**条目名**（战斗 ID），`_stricmp` 不分大小写；**同名跨文件复用同一对象后再 `vtbl+0x64(ini)` 覆写字段 ⇒ 后装载者赢**；不同名追加新对象（`0x0046CE97: 68 A0 03 00 00` = `new(0x3A0)` = **928 字节**）；
- 全局表：`DynamicVectorClass` 基址 `0x00A83CF8`，`Count @ 0x00A83D08`（`0x0046CE5A: A1 08 3D A8 00`），元素 `0x3A0` 字节，名字在 `+0x24`。

**架构级定论（三条，全部 [实证]）**：
1. **MIX 内的 `BATTLEMD98.INI` 永不加载**——通配是 Win32 API，`FindFirstFileA` 结构上不可能返回 MIX 条目；引擎内也**不存在** `"BATTLEMD98.INI"` 字面量（只有 `BATTLEMD.INI` 与 `BATTLEMD*.INI` 两个）；
2. **MIX 内的 `BATTLEMD.INI`（官方名）只在「目标机一个散装 `BATTLEMD*.INI` 都没有」时才会被读**（`0x0052CCC7` 跳过回退）；
3. 同名战斗 ID 的**最终胜者取决于目录枚举顺序**（`FindFirstFileA/FindNextFileA`），引擎不保证字母序 ⇒ 工程上禁止跨文件重复 ID（[待实测]，见 §17.6-3）。

---

### 17.5 对本项目的落地契约 [实证]（机制）+ [推演]（装机形态）

| 目标 | 散装（游戏目录） | 打包进 `expandmd98.mix` | 结论 |
|:---|:---|:---|:---|
| 新增/覆写战役条目（`BATTLEMD98.INI`） | ✅ 通配唯一可见域 | ❌ 永不加载 | **必须散装** |
| 覆写官方战役条目（官方名 `BATTLEMD.INI`） | ✅ 且会屏蔽 MIX 内那份 | ⚠️ 仅在目标机无任何散装 `BATTLEMD*.INI` 时生效 | 优先散装 |
| 覆盖官方 MIX 内同名资源 | ✅ 最高优先级 | ⚠️ 只赢过比它晚装载的 MIX；**赢不过 `langmd/language`** | 散装最稳；要压官方 MIX 用 `expandmd99` |
| 地图等非 INI 资源（`ECH01.MAP`） | ✅ | ✅ | 保持现有做法 |

**其它可直接引用的硬事实**：
- `expandmd*.mix` 文件名必须**两位补零**（`EXPANDMD%02d`），否则整包不会被装载；序号**大者先装载 ⇒ 优先级高**（与直觉相反：**98 先于 99？不——99 更大 ⇒ 99 先**；两包冲突时抢**大**号）；
- `0x005B3C20` 的 ctor 失败（文件打不开/头解析失败）**不会**中止启动：它跳过条目表与链表尾插、但**仍返回非空 this**（空壳实例，不在优先级链表里）——真正的失败在后续资源缺失时才暴露（经 `CDCheck 0x004790E0 → Force_CD_Available 0x004A8270`）；
- 「`Failed to initialize bootstrap mixfiles!`」打印目标是**单条 `ret` 桩** `0x004068E0`（`C3`），且「预载门槛」`0x005B43E0` 是 `mov al,1; ret` 恒真桩 ⇒ **1.001 下 Init 返回 −1 的实际可达路径只有 `operator new` 失败**；用户可见的硬门禁只有语言表自检（`LANGUAGE.MIX` 后 `0x006BD85C: 6A 10` / `0x006BD869: FF 15 60 14 7E 00` = `MessageBoxA`）。

---

### 17.6 §11 速查表并入建议：关键 VA 速查表（§17）

| VA | 名称/职责 | 证据等级 | 来源 |
|:---|:---|:---:|:---|
| `0x00473D10` | `CCFileClass::Get_File`（磁盘优先 + MIX 回落） | [实证] | §17.1 |
| `0x00431F10 / 0x0065CBF0 / 0x0065CC59` | 散装路径 → `RawFileClass::Open` → `CreateFileA` | [实证] | §17.1 |
| `0x005B4430` | `MixFileClass::Find`（CRC32 二分 + FIFO 链） | [实证] | §17.1 |
| `0x00ABEFD8` | `List<MixFileClass*>` 全局优先级链表（哨兵在 BSS） | [实证] | §17.1 |
| `0x00884D90` | `DynamicVectorClass<MixFileClass*>`（全部已装载 MIX） | [实证·引] | §17.1 |
| `0x0052BA60` | `Init()`（Init.CPP） | [实证] | §17.2 |
| `0x005301A0` | 主 MIX 装载器（`EXPANDMD99…00` + `RA2MD/RA2/CACHE/LOCAL`） | [实证] | §17.2 |
| `0x00530000 / 0x00530460 / 0x005312A0` | 通配 / 次级 / 收尾装载器 | [实证] | §17.2 |
| `0x006BD7EF / 0x006BD818 / 0x006BE041` | `LANGMD.MIX` / `LANGUAGE.MIX` / `Init` 的调用点（先后顺序铁证） | [实证] | §17.2 |
| `0x005B3C20` | `MixFileClass` ctor（CD 门禁 + 明文头 + 加密旁路 + 尾插） | [实证] | §17.3 |
| `0x00633050 / 0x006330C0 / 0x00633110 / 0x00633130` | `PKStraw` 解密流四件套 | [实证] | §17.3 |
| `0x0052A670 / 0x0052A6AF` | 公钥结构装配 / RSA `e=0x10001` | [实证] | §17.3 |
| `0x005C6370 / 0x00631F60` | DER INTEGER 解析 / 公钥结构 ctor（`+0x200`=位长−1） | [实证] | §17.3 |
| `0x00840A78 / 0x007F3710 / 0x006BEDB0` | `"blowfish.dll"` / COM 组件表 / 动态绑定器 | [实证] | §17.3 |
| `0x007E1A80 / 0x008189C8` | 内嵌 `[PublicKey]` INI 文本 / base64 字母表 | [实证] | §17.3 |
| `0x0052CB90` | `LoadBattleMdIni`（`BATTLEMD*.INI` 通配 + 回退） | [实证] | §17.4 |
| `0x0046CE10` | `Register_Battles`（`[Battles]` 归并 → 全局表 `0x00A83CF8`） | [实证] | §17.4 |
| `0x007E1208 / 0x007E120C / 0x007E1300` | IAT：`FindFirstFileA` / `FindNextFileA` / `FindClose` | [实证] | §17.4 |
| `0x004790E0 / 0x004A8270` | `CDCheck` / `Force_CD_Available`（门禁，非查找链） | [实证] | §17.3 |
| `0x005B43E0 / 0x004068E0` | 「预载门槛」恒真桩 / 调试打印 `ret` 桩 | [实证] | §17.5 |

---

### 17.7 §17 未闭环项（附可执行取证方法）

| # | 缺口 | 为何静态不闭环 | 下一步取证方法 | 级别 |
|:--:|:---|:---|:---|:--:|
| 1 | `MixFileClass::Cache()` 把整包解密写入 `+0x24` 的**填充点** | 对 `+0x24` 的写点全 `.text` 扫描未见；唯一「预载」入口 `0x005B43E0` 是恒真桩 | 静态回溯 `0x005B4430` 中 `[ebp+0x24] != 0` 分支的上游调用者，并反汇编 `0x005B3E90`（链表遍历家族）；动态：对 `MixFileClass+0x12 / +0x24` 设写 watch | P2 |
| 2 | 「散装文件一定压过 MIX」的**端到端**验证 | 只有分支顺序实证 | 投同名 `RULESMD.INI`（散装 + `expandmd98.mix` 内各一份，内容不同），在 `0x00473D2D / 0x00473D68` 下断或比对全局表内容 | P1 |
| 3 | 多 `BATTLEMD*.INI` 冲突时**谁最终赢**（目录枚举序） | `FindFirstFileA` 顺序引擎不保证 | 投 `BATTLEMD01.INI`/`BATTLEMD02.INI` 同 ID 不同 `Description`，对 `0x0046CF60` 下断观察覆写次序 | P2 |
| 4 | `-CD <path>` 的真实运行语义 | 静态链完整（`0x0052F7A0 strstr → 0x0052F7AF 置 [0x0089E3A0]=1 → 0x0052F7B6 → 0x0047AB10`），无运行验证 | 带 `-CD` 启动，在 `0x0047AFCF / 0x0047B08A` 下断观察实际模式串 | P2 |
| 5 | `0x00530460` 次级装载器逐分支优先级细节 | 仅按字符串引用地址序实证 | dump `0x00530460`–`0x0053129F` 逐段核对 `%02d` 循环边界 | P2 |

---

````

- **证据**：等级 `[实证]`（本章全部 VA/字节均已复算并落入 `out/re_work/atlas_rev/R6/claims_R6.txt`；`tools/audit_bytes.py` 405/405 OK）+ `[实证·引]`（`0x00884D90` 向量字段口径引自 `docs/re/fs_mix_load_chain.md`）+ `[推演]`（Blowfish COM 类归属、装机形态建议）；来源文档：`docs/re/fs_mix_load_chain.md:14-17,21-70,74-78,84-140,146-215,219-282,286-323` 与 `docs/re/fs_mix_load_chain_deep.md:18-24,38-160,168-260,269-329,335-379,412-435`。
- **影响面**：①**§11 速查表**——需并入 §17.6 的 20 行；②**§12 契约**——不冲突（本章无同步/PRNG 语义），但建议在 §12.4「补丁生命周期」补一句「资源类补丁的落地形态受 MIX 优先级链约束」；③**§0 准则**——不冲突；④**新引擎常量表**——`0x007E1A80`（内嵌公钥）、`0x008189C8`（base64）属新增静态数据锚点。
- **不提交 TOC 修改**（按任务卡）。

---

## 3. 覆盖度自证表

> 左列 = 我读过的每个来源文档小节；右列 = 命中的补丁块（或"不入 atlas 的理由"）。

### 3.1 `docs/re/weapons_damage_production.md`（1,094 行，全文已读）

| 来源小节 | 行号 | 命中 |
|---|---|---|
| §0 结论速览 | 10-23 | PATCH-R6-01 §16.1/§16.3/§16.5（速查表与入口表）；其"Verses+0xB0"一条被 §16.3 勘误 R6-E2 订正 |
| §1.1 虚表与真实入口 | 29-42 | §16.1 v[243] 六类表（含勘误 R6-E1） |
| §1.2 Fire 骨架 / Construct 调用方 | 44-83 | §16.2 参数落位表 + `ret 0x1C`；调用方 6 处未逐条复算 → 不入 atlas（属于函数级细节） |
| §1.3 Bullet::Update 热点 | 85-94 | §16.2（v[23]/序言/职责）；"6432 B / 1804 行 / 33 调用目标"为源文档度量，未复算 → 正文不引用该计数 |
| §1.4 Fire/Detonate 分支 | 96-114 | §16.2 弹头读取点表（+0x124/+0x16C/+0x1C4）+ §16.4 双 RNG 域；原文"RNG ×2 散布"被勘误为"局外震屏 RNG"（源文档 S24 自订正，本章采信） |
| §2.1 WarheadTypeClass 布局 | 120-142 | **§16.3（含 P0 勘误 R6-E2：Verses 起于 +0xA0）** |
| §2.2 DamageArea 算法 | 144-195 | §16.4-B（环表/空间桶/分配/释放/复杂度） |
| §2.3 ReceiveDamage | 197-215 | §16.4-C/D；原文"Verses 应用点在 0x701939 起"被勘误 R6-E3 否定 |
| §2.4 弹头标志 | 217-233 | §16.3-C 读取点表（+0x16C 等）；"Elusive 无此字段"结论未复算 → 不入 atlas |
| §3.1 FactoryClass 数据结构 | 239-251 | **§16.5 字段表（含 P1 勘误 R6-E4：+0x24/+0x58）** |
| §3.2 关键方法表 | 253-280 | §16.5 流水线（DemandProduction/StartProduction/GetBuildTimeFrames/CompletedProduction 逐条锚点）；其余 8 个 O(1)/O(队列) 方法未复算 → 以速查表形式部分保留 |
| §3.3 每帧生产推进 | 282-311 | §16.5（FactoryUpdate 0x004500F0 / HouseClass::Update 0x004F8440） |
| §3.4 Prerequisite | 313-326 | §16.5 经济侧关联（`0x004F7870` / `0x0050B370` 入口实证；内部前置表 → §16.7-4 未闭环） |
| §3.5 维修/回充/超武计时 | 328-348 | **不入本章**：超武状态机已由 atlas §7 建账（`SuperClass` vtable/字段持久化），本章避免重复建账 |
| §4 热点与可优化点 | 352-409 | §16.4-B 复杂度 + §16.4-E 四条确定性契约（优化建议本身属"建议"层，由现网补丁文档承载，不入架构章） |
| §5 Hook / 优化插入点 | 411-434 | §16.1 契约（挂共享本体 0x6FDD50，不逐类挂槽）+ §16.4-C 覆写矩阵 |
| §6 函数索引（速查） | 436-467 | §16.6 速查表（40+ 条已按架构价值筛选并入） |
| §7 未尽事项 | 471-476 | §16.7 未闭环项 1/2/4 |
| S24 §一 勘误 1-3 | 494-520 | §16.4-D（RNG 实例归属）+ §16.5（生产零 PRNG）——三条订正全部采信并抽验锚点 |
| S24 §二.1 命中链分支表 | 526-585 | §16.1/§16.2/§16.4（真随机 vs 确定性概率表的分支定性） |
| S24 §二.2 PRNG 消费清单 P01-P27/L01-L06 | 587-630 | §16.4-D（抽验承伤 5 处局内 + 6 处局外装载点；全 33 处清单以断言库引用，不逐条抄入 atlas） |
| S24 §二.3 消费次数矩阵 | 631-642 | §16.4-E 契约 1（表格本身为 [推演]，不入 atlas 正文） |
| S24 §二.4 desync 分叉点 | 644-664 | §16.4-E 契约 2/3 + §16.7-2/3 |
| S24 §三 决定性锚点表（90 条） | 777-838 | 断言库复用（`claims_R6.txt` PART R6-B 含其中武器域条目） |
| S24 §四 未闭环 | 842-857 | §16.7-1/2/4 |
| S26 §1 Randomizer ABI | 869-883 | §16.4-D（`Random`/`RandomRanged`/`Global` 三地址 + thiscall ecx 装载） |
| S26 §2/§3 ecx 装载证明 | 887-967 | §16.4-D（五大范式不逐条抄入；仅保留结论与代表锚点） |
| S26 §4 帧同步耦合 | 971-1015 | §16.4-D（`0x00650A90` 每帧恰抽 1 次，与 atlas §12.2 ASM-FIX2-1 对齐） |
| S26 §5 生产零随机认证 | 1018-1045 | §16.5「生产零 PRNG」段（[实证·引] + 本任务抽验阈值/魔数锚点） |
| S26 §6 断言摘要 | 1049-1093 | 断言库复用 |

### 3.2 `docs/re/fs_mix_load_chain.md`（410 行，全文已读）

| 来源小节 | 行号 | 命中 |
|---|---|---|
| §0 结论速览 | 10-17 | PATCH-R6-02 §17.1/§17.4 |
| §1.1 类与 vtable（RTTI） | 23-41 | §17.1/§17.3（`CCFileClass 0x7E16B0`、`RawFileClass`、`MixFileClass`、`PKStraw` 等 vtable 经本任务取值断言） |
| §1.2 CCFileClass 方法槽 | 43-56 | §17.1（slot `+0x14 Open` / `+0x1C Get_File`）；其余槽位未复算 → 不入 atlas |
| §1.3 搜索顺序总结 | 58-70 | §17.1（A/B 两通道）；`[CD]` 一条按 deep 文档 E4 升级为「不进入查找链」 |
| §1.4 缓存策略 | 72-78 | §17.1（`0x00884D90` 向量 [实证·引]）；`+0x24` 填充点 → §17.7-1 |
| §2.1 MIX ctor 装配 | 84-102 | §17.3（CD 门禁 / 明文头 / 加密旁路 / 尾插） |
| §2.2 PKStraw 解密链 | 104-140 | §17.3（密钥块公式 / e=0x10001 / DER / blowfish.dll 动态绑定） |
| §3.1 装载序列 | 146-171 | §17.2（六个调用点表 + expandmd 序号语义） |
| §3.2 覆盖规则 + 勘误 E1/E4 | 173-215 | §17.2（FIFO 两端证据 + 完整优先级链；已按 deep 文档 E1 把 langmd/language 移到链首） |
| §4 INI 追加语义 | 219-282 | §17.4（通配 vs 回退 + 归并契约） |
| §5 关键地址总表 | 286-323 | §17.6 速查表（全部条目已并入或标注为未复算） |
| §6 mixlib 交叉验证/勘误 | 327-344 | **不入 atlas**（属工具链侧结论，非引擎架构；已在 [3] 勘误中提示保留原状） |
| §7 对本项目的直接结论 | 348-354 | §17.5 落地契约表 |
| §8 未闭环 | 358-368 | §17.7-1/3/4/5（第 3 项「CCFileClass 字段语义」按 deep 文档部分闭环，余项保留） |
| §9/§10 证据清单与复算方法 | 372-407 | 不入 atlas（元数据） |

### 3.3 `docs/re/fs_mix_load_chain_deep.md`（512 行，全文已读）

| 来源小节 | 行号 | 命中 |
|---|---|---|
| §0 必答项速览 | 14-24 | PATCH-R6-02 §17.1–§17.5（六条结论全部落章） |
| §1.1 三条独立通道 | 30-36 | §17.1 通道表 |
| §1.2 通道 A 优先于 B 字节证据 | 38-69 | §17.1 asm 块（0x473D2D/0x473D34/0x473D68/0x431F10/0x65CC59 + IAT 槽） |
| §1.3 通道 B 装载顺序 | 71-99 | §17.2（调用点表 + expandmd 99→0 循环字节） |
| §1.4 覆盖规则 FIFO | 100-115 | §17.1 尾插/头遍历字节 |
| §1.5 完整优先级链图 | 116-141 | §17.2 优先级链（含 BSS 哨兵不可断言说明） |
| §1.6 langmd/language 勘误 | 142-160 | §17.2「最早装载铁证」（0x6BD7E8/0x6BD7EF/0x6BD818/0x6BE041 + CD 状态压 −2） |
| §2.1 BATTLEMD 通配枚举 | 168-194 | §17.4 asm 块 |
| §2.2 回退分支 | 196-205 | §17.4（唯一 mix 感知通道 + 触发条件） |
| §2.3 多文件合并语义 | 207-218 | §17.4 归并契约（含 0xA83CF8 / Count 0xA83D08 / 元素 0x3A0） |
| §2.4 "找不到"的行为 | 220-223 | §17.4 结论 3 的注脚（不入正文细节） |
| §3.1 INI 两范式对照 | 229-245 | §17.4 范式对照表 |
| §3.2 BATTLEMD98.INI 永不加载 | 247-255 | §17.4 定论 1/2 |
| §3.3 反例（官方名可读） | 257-261 | §17.4 定论 2 + §17.5 表第 2 行 |
| §4 [CD] 复核 | 265-329 | §17.1 通道 C + §17.3-1（门禁）+ §17.7-4 |
| §5 失败字符串与错误分支 | 335-379 | §17.5（恒真桩 0x5B43E0 / ret 桩 0x4068E0 / MessageBoxA 硬门禁） |
| §6 可操作结论 | 383-408 | §17.5 落地契约表 + 「两位补零」硬约束 |
| §7 与前序文档差异登记 E1–E6 | 412-421 | 已全部吸收进 §17.2/§17.4（E1→链首、E2→恒真桩、E4→不进入查找链） |
| §8 未闭环清单 1–7 | 425-435 | §17.7-1/4/5（第 2/3 项被本任务重新表述为可执行动态验证） |
| §9 改动文件与门禁输出 | 439-512 | 不入 atlas（元数据）；作为本任务门禁口径的参照 |

**覆盖度小结**：三份来源文档共 **65 个**小节全部登记（62 个落章 / 3 个显式说明不入章理由：超武状态机（atlas §7 已建账）、mixlib 工具链勘误、元数据章节）。

---

## 4. 十节回执（AGENT_DELIVERY_FORMAT.md v1 骨架）

```text
[META]
task=task-8 (R6)   executor=DSH 子代理 atlas-r6-weapons   elapsed≈见下方实时值   mode=read-only
scope_declared=允许写 docs/re/atlas_rev/R6_weapons_mix.md、out/re_work/atlas_rev/R6/**、out/re_work/atlas_rev/R6/claims_R6.txt

[0] 结论摘要
1) 已产出 §16/§17 两章完整可粘贴 markdown（PATCH-R6-01/02，APPEND_SECTION，锚点 atlas L1981「## 附录 DA1 …」行，唯一命中）。
2) 新增 4 条源文档勘误：R6-E1 FootClass v[243]（非 0x415EE0）、R6-E2 WarheadTypeClass.Verses 起于 +0xA0（非 +0xB0，**P0**）、R6-E3「Verses 在 ReceiveDamage 0x701939 乘算」不成立、R6-E4 FactoryClass 步数 +0x24 / 在造对象 +0x58（非 +0x20 / +0x50，**P1**）。
3) 门禁全绿：verify_anchors 323/323 PASS；audit_bytes claims_R6.txt 405/405 OK。
4) 最大风险：§16 触及随机数消费序红线（局内 PRNG 27 处调用点）；且 Verses 施加点未定位 ⇒ 任何基于 Verses 的优化在闭环前不得放行。

[1] 逐条必答项结论表
| # | 问题 | 结论 | 证据等级 | 证据锚点 |
|1| 开火链入口与分发 | v[243]：Techno/Building/Foot = 0x6FDD50；Aircraft=0x415EE0；Unit=0x741340；Infantry=0x51DF60 | [实证] | 0x7F4D2C/0x7E4288/0x7E9060/0x7E2670/0x7F603C/0x7EB424 |
|2| Bullet 装配/飞行/引爆 | Construct 0x4664C0（ret 0x1C）→ Update v[23] 0x4666E0 → Fire 0x468D80 → Detonate 0x4690B0 → DamageArea(0x469A83) | [实证] | claims_R6.txt |
|3| Warhead 布局 | Verses 起于 **+0xA0**（11×double，默认串 0x847C40，缩放 0.01）；CellSpread +0x124 / CellInset +0x128 / PercentAtMax +0x12C | [实证] | 0x75D3A0/0x75DE06/0x75DE0C/0x75DE31/0x75D3EB |
|4| Verses 施加点 | **未定位**（全 .text `*8 + 0xA0/0xB0` 索引访存 0 命中） | [待定位] | §16.3-C / §16.7-1 |
|5| AOE 复杂度与确定性 | DamageArea 环表(0x7ED3D0 静态/0xABD490 BSS)×空间桶(0x887888)，每候选 new/delete；候选序不得置换 | [实证]+[推演] | 0x4895A3/0x4895C7/0x4894AB/0x489AE4 |
|6| 承伤覆写矩阵 | v[91] 默认 0x701900；Building/Foot/Unit/Infantry/Aircraft 各自覆写 | [实证] | 0x7F4ACC/0x7E4028/0x7E8E00/0x7F5DDC/0x7EB1C4/0x7E2410 |
|7| 生产时钟 | 步数 +0x24，阈值 0x36=54，每步帧数 = clamp(Total/54,1,255)（魔数 0x4BDA12F7），在造对象 +0x58；全程 0 PRNG | [实证]+[实证·引] | 0x4C9FB0/0x4C9FC0/0x4CA133/0x4CA13C/0x4CA1BA |
|8| 文件解析链 | 散装(CreateFileA) 优先 → MIX Find(CRC32+FIFO) → CD 仅通配二次尝试 | [实证] | 0x473D2D/0x473D68/0x5B4430/0x5B44A1/0x47B020 |
|9| MIX 优先级 | 散装 > langmd > language > expandmd99…00 > ra2md… ；序号大者先装载 | [实证] | 0x6BD7EF/0x5301BA/0x53028A/0x5B3DE2/0x5B3E00 |
|10| INI 通道 | 通配=FS-only（BATTLEMD98.INI 在 MIX 内永不加载）；显式名=可读 MIX（BATTLEMD.INI 仅在无散装时走回退） | [实证] | 0x52CBA9/0x52CCC7/0x52CCD6/0x46CE10 |

[2] 关键证据块
全部 405 条为机器可读断言：0xVA = HEXBYTES # 注释，见 out/re_work/atlas_rev/R6/claims_R6.txt（MD5 32e7286ecc45dd72454fde71c1e589c8，413 行）。
代表 4 条（本任务新证，均含 Capstone 上下文）：
  0x0075DE06 = 8D 9E A0 00 00 00   # lea ebx,[esi+0xA0]  Verses 数组起点 = Warhead+0xA0
  0x0075DE0C = BD 0B 00 00 00      # mov ebp,0xB（11 次 = 11 种护甲）
  0x007E2670 = E0 5E 41 00         # AircraftClass v[243] -> 0x00415EE0
  0x0052CCC7 = 0F 85 92 00 00 00   # jne 0x0052CD5F 跳过回退（MIX 内 BATTLEMD.INI 不读）
xref 来源：Capstone 线性反汇编（out/re_work/atlas_rev/R6/probe_r6*.py / probe_verses*.py 全部落盘可复跑）。

[3] 勘误（交 Lead，未改任何既有文档）
docs/re/weapons_damage_production.md:126-129 | `Verses[11] | 0xB0`（及 `Deform 0xA8`） | `Verses[11] | 0xA0`（+0xA0…+0xF7）；`+0xB0` = Verses[2] | 装载器 0x75DE06/0x75DE0C/0x75DE48/0x75DE52 与默认值串 0x847C40 十一项 | **影响产品决策**（按错偏移写护甲乘数会静默错位 8×8 字节）
docs/re/weapons_damage_production.md:37,40 | FootClass v[243]=0x415EE0；AircraftClass「与 Foot 共享」 | FootClass v[243]=0x6FDD50；AircraftClass=0x415EE0 | 虚表槽字节 0x7E9060 / 0x7E2670 | 影响 Hook 覆盖面（漏挂风险）
docs/re/weapons_damage_production.md:215,473 | 「Verses 应用点在 ReceiveDamage 归一化段 0x701939 起」 | 该段为火力/伤害归一化（fild→call 0x50BD30→fmul [esi+0x158]→fdivr→call 0x7C5F00），无护甲数组索引 | 0x701939/0x701957/0x70195D/0x701961 | 文档级认知订正（不影响已落地钩子）
docs/re/weapons_damage_production.md:243-251 | `ProgressTimer Production +0x20`；`Object +0x50` | 步数计数器 **+0x24**；在造对象 **+0x58**；`+0x40/+0x44/+0x50` 是 QueuedObjects(vftable/Items/Count) | 0x4CA120/0x4CA13C/0x4CA1BA/0x4C9FB0/0x4CA5C0 | **影响产品决策**（建造类补丁/工具必须先订正偏移，否则把队列长度当指针解引用）
无对 docs/re/ARCHITECTURE_ATLAS.md 的勘误（本轮未发现 atlas 内武器/MIX 域的错误表述——该域此前完全空白）。

[4] 未闭环清单
1) Verses[armor] 施加点 | 全 .text 未命中索引访存形态（0 命中）| 对 Warhead+0xA0 设 8B 写 watch / 静态回溯 ReceiveDamage、DamageArea 的 WarheadTypeClass* 形参链 | **P1**
2) AOE 半径边界浮点舍入跨 CPU 差异 | 需真机多端 | 临界坐标(1 lepton 步进)单位 + 双端录像回放比对 0x00AC51FC | P1
3) DamageArea 候选枚举序设备级复现 | 需运行期 | 在 0x00489AE4 前下断导出 DamageGroup 序并双端比对 | P1
4) CanBuild(0x004F7870) 前置表 | 46 KB 未展开 | 单独立项 dump 0x004F7870–0x0050B400 | P2
5) MixFileClass::Cache() 填充点 | 写点未定位；0x5B43E0 为恒真桩 | 回溯 [ebp+0x24] 非零分支上游 + 对 MixFileClass+0x12/+0x24 设写 watch | P2
6) 「散装压过 MIX」端到端验证 | 仅分支顺序 | 同名 RULESMD.INI 双投 + 0x473D2D/0x473D68 下断 | P1
7) 多 BATTLEMD*.INI 冲突胜者 | 枚举序引擎不保证 | 0x46CF60 下断观察覆写次序 | P2

[5] 写作用域合规声明
改动文件清单（全部在允许作用域内；时间戳见文件 mtime）：
  docs/re/atlas_rev/R6_weapons_mix.md          （本文件，新建）
  out/re_work/atlas_rev/R6/claims_R6.txt       （新建，413 行 / 405 条断言）
  out/re_work/atlas_rev/R6/probe_r6.py / probe_r6b.py / probe_r6c.py / probe_r6d.py / probe_r6e.py / probe_r6f.py / probe_verses.py / probe_verses2.py / probe_verses3.py / probe_verses4.py / gen_claims_r6.py / probe_r6_out.json  （scratch/脚本，新建）
未触碰清单：docs/re/ARCHITECTURE_ATLAS.md（Lead 唯一写者，读前读后 MD5 均 6e790b55b2709ff5c41ad3f73f7e49e4）、其他 R# 文件、ra2render/**、ra2youli/**、REVERSE_ENGINEERING_AND_PATCHES.md、任何既有 docs/re/*.md（含三份来源文档）、ra2youli/gamemd.exe。
目标二进制只读证明：MD5 4f37486e5b0dbe2ae5f45aeee0f98367（与任务卡基线一致，4,825,360 B）；verify_anchors .text raw SHA-256 c0368a179f6e1a0f85bf94ebeb3a3e62efc8b1a2000abe164e5e1c61714eb738 PASS。
未运行游戏、未注入、未改二进制。

[6] 门禁实跑输出（原文粘贴）
$ python tools/verify_anchors.py
  [PASS] .text 原始段哈希: c0368a179f6e1a0f85bf94ebeb3a3e62efc8b1a2000abe164e5e1c61714eb738 (口径: raw(SizeOfRawData=0x3E0000))
  [INFO] PE头特征判定 : RA2OPT_PERF_APPLIED (0xAE=0x20, Stack=4MB, .text未变) (DllChar: 0x20, StackReserve: 0x400000)
  [PASS] .detour 原生签名: 40 00 00 00 44 74 72 00 ('@\0\0\0Dtr\0' @ VA 0xb93000) -> 严禁写入/注入原则确立
  回归汇总 : 断言总数 323 条 | PASS: 323 (100.00%) | FAIL: 0 | NOREAD: 0
  ★ 最终裁决 : [100% ALL PASS] 全库决定性锚点与二进制基线完全一致，生产环境可安全放行！

$ python tools/audit_bytes.py out/re_work/atlas_rev/R6/claims_R6.txt
  ...（逐条 OK，节选）...
  0x826674   52 41 32 2e 4d 49 58       52 41 32 2e 4d 49 58   OK     "RA2.MIX"
  0x82667c   52 41 32 4d 44 2e 4d 49 58 52 41 32 4d 44 2e 4d 49 58 OK     "RA2MD.MIX"
  0x840a78   62 6c 6f 77 66 69 73 68 2e 64 6c 6c 62 6c 6f 77 66 69 73 68 2e 64 6c 6c OK     "blowfish.dll"
  --------------------------------------------------------------------------------------------------------------
  合计 405 条：OK=405  MISMATCH/NOREAD=0

（另有 python -c 复核：atlas 2001 行 / MD5 6e790b55b2709ff5c41ad3f73f7e49e4；gamemd.exe MD5 4f37486e5b0dbe2ae5f45aeee0f98367 / 4825360 B）

[7] 风险与红线提示
①同步语义/命令序：**触及**（§16.4-E 契约 2：AOE 候选枚举序置换会改变帧内结算序）；
②随机数消费序：**触及**（§16.4-D：局内 27 处 + 局外 6 处调用点清单；Detonate/ReceiveDamage/DamageArea 均消费局内 PRNG）；
③存档结构：**不触及**（本章无存档路径变更；SuperClass 持久化归 atlas §7）；
④渲染像素等价性：**间接触及**（§16.2 与 atlas §2.5 的弹道剔除红线对齐——剔除必须留在 Draw 表现层，禁止触碰 Update/Detonate）。
⇒ 触及 ① ② ④，**必须走 MP 门控矩阵 + 真机对拍验收**；禁止宣称「零风险 / 零 Desync」。

[8] 交付物清单
  docs/re/atlas_rev/R6_weapons_mix.md      —— 658 行；补丁块 2 条 + 覆盖度自证表 65 小节行 + 十节回执（本文件）
  out/re_work/atlas_rev/R6/claims_R6.txt   —— 405 条字节断言（413 行）
  out/re_work/atlas_rev/R6/*.py            —— 11 个只读探针/生成脚本；probe_r6_out.json 为取值快照

[9] 待裁决项（建议方案 + 理由）
1) Verses 施加点是否立项（P1）——**建议立项 30 分钟专查**（唯一会阻塞「按 Verses 做护甲向优化」的缺口），取证路径已在 §16.7-1；
2) 源文档 4 条勘误是否进 atlas 附录 DA#——**建议进**（R6-E2/E4 属产品决策级，建议与 DA1 同格式登记），但**不写入 §16/§17 正文之外的位置**，由 Lead 决定落点；
3) §16.6/§17.6 速查表是否并入 §11——**建议并入**（否则 §11 无法索引武器/MIX 域），本任务已按 §11 五列格式给出；
4) claims_R6.txt 是否纳入常驻门禁——**建议作为 `verify_anchors.py --claims` 的附加库**（与 `docs/re/anchor_claims.txt` 分离维护，避免污染 323 条基线）；
5) §17.5 装机形态建议的对外口径——**建议标「仅纸面规格 / 建议」**，因为「散装优先」的端到端行为仍为 [待实测]（§17.7-2）。
```

---

*本文件由 DSH 子代理 `atlas-r6-weapons` 产出；atlas 写入权归 Lead。*