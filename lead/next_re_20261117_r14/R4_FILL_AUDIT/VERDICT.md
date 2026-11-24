# R4_FILL_91_R2 `fill_delta.tsv` 独立复核 — VERDICT

> 审计员：异族独立审计员（非执行器）。执行器为 Hy4 × DeepSeek 混合产出；本文**只采信我自己从 `ra2youli\gamemd.exe` 字节反汇编出的结果**，未引用 `R4_FILL_91_R2\evidence\ROW_*.txt` 的任何内容，也未复用 `fill.py` 的代码。

| 项 | 值 |
|---|---|
| 二进制 | `ra2youli\gamemd.exe`（4 825 360 字节）|
| SHA-256 | `73201CC021497C9567742F718BF1DC78C22E9AE16C7E7365354B65F3FCF67476` |
| 输入 | `R4_FILL_91_R2\fill_delta.tsv`（91 数据行，UTF-8，6 列）|
| 抽样 | 12 / 91（规则与命令见下）|
| 反汇编 | capstone 5.0.7（x86-32，`CS_MODE_32`），按需就地解码；PE 解析：pefile 2024.8.26 |
| 输出目录 | 只写 `R4_FILL_AUDIT\` |

## 0 · 抽样：命令与结果

规则：91 行按 `entry` 升序，取最小 1、最大 1，中间**均匀取 10**——即在 0..90 上取 `i = round(k*90/11), k=1..10`，与首尾索引 0、90 合并去重，共 12 个。

```powershell
$p="D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\R4_FILL_91_R2\fill_delta.tsv"
$rows=Get-Content $p | Select-Object -Skip 1
$e=$rows | ForEach-Object { ($_ -split "`t")[0] } | Sort-Object      # 91 个 entry 升序
$idx=@(0,90); 1..10 | ForEach-Object { $idx += [int][math]::Round(($_*90.0)/11.0) }
$idx | Sort-Object -Unique | ForEach-Object { $e[$_] }              # 12 个抽样 entry
```

| # | 索引 | entry | 行名类 | ④ 表属类（RTTI 实测）| 类名是否一致 |
|---:|---:|---|---|---|---|
| 1 | 0 | `00464AC0` | BuildingTypeClass | BuildingTypeClass | 是 |
| 2 | 8 | `0055A050` | LoadOptionsClass | LoadOptionsClass | 是 |
| 3 | 16 | `0055A950` | LocomotionClass | FlyLocomotionClass | **否** |
| 4 | 25 | `00597D50` | MapSeedClass | MapSeedClass | 是 |
| 5 | 33 | `005C0FE0` | MPGameModeClass | MultiplayerBattle | **否** |
| 6 | 41 | `005CA6D0` | MPGameModeClass | MultiplayerSiege | **否** |
| 7 | 49 | `005CB440` | MPGameModeClass | UnholyAlliance | **否** |
| 8 | 57 | `005D6540` | MPGameModeClass | MultiplayerBattle | **否** |
| 9 | 65 | `005D74A0` | MPGameModeClass | MultiplayerBattle | **否** |
| 10 | 74 | `0073C5F0` | UnitClass | UnitClass | 是 |
| 11 | 82 | `007B9C30` | WWMouseClass | WWMouseClass | 是 |
| 12 | 90 | `007BA380` | WWMouseClass | WWMouseClass | 是 |

## 1 · 判定口径（逐行五项）

| 项 | 判据（全部取自字节）|
|---|---|
| ① `vt` 与槽号 | `.rdata` 中 `u32(vt + slot*4) == entry`；且 `vt` 是表起点（`u32(vt-4)` 为合规 COL）|
| ② `COL` | `u32(vt-4)` 等于 ④ 的 COL，且 `u32(COL)==0`（sig），`COL+0x4`（offset）等于 ④ 写的 offset |
| ③ `TD` 与类名 | `u32(COL+0xC)`（绝对 VA）处为 TD；`TD+8` 按**内联串**读，须以 `.?A` 开头；去修饰后与 ④ 写的类名一致 |
| ④ 装表点与宿主 | 装表点处指令写到内存且立即数 == `vt`；该地址在 CFG 遍历（不跟 call）下从给出的宿主 entry 可达；宿主是函数起点（前有填充/`ret` 其后，且被 `call rel32` 指向）|
| ⑤ ㉓ | 枚举该 `vt` 的**全部**写点；④ 用的那个既不在 atexit 注册集（保守超集）、也不是删除析构器/基类析构器形态 |

> 本镜像的 `COL+0x14`（pSelf）实测恒为 0，**不能**用「pSelf 指向自身」判表起点；本文一律用 「`sig==0` + `offset<0x1000` + `pTD` 指向合规 TD 装饰名」判合规 COL。

---

## 行 1/12 · `00464AC0` — BuildingTypeClass::CanPlaceHere

④ 原文：`BuildingTypeClass::slot42（vt=007E4570，槽 42 值=00464AC0，COL=007FC618 offset=0，RTTI=008193A8→.?AVBuildingTypeClass@@；装表点 0045E2CD 位于 0045DD90 体内，entry 体外）`

### ① vt 与槽号 — 成立

| 读法 | 地址 | 字节 | 值 |
|---|---|---|---|
| `u32(vt-4)`（COL 守卫）| `007E456C` | `18 C6 7F 00` | `007FC618` |
| `u32(vt + slot*4)` | `007E4618` | `C0 4A 46 00` | `00464AC0` |

- 槽号 `42`（④ 内两处写法一致：是）；`u32(vt+slot*4) == entry` → **是**。
- `vt` 是表起点（`u32(vt-4)` 为合规 COL）→ **是**。
- 我独立全扫 `.rdata/.data` 中值 == `00464AC0` 的 dword：共 **1** 个 `(vt, slot)` 见证，④ 的 `(vt=007E4570, slot=42)` **是** 其中之一。

- 同 entry 的全部见证：

| vt | slot | COL | 表属类（TD）| COL.offset |
|---|---:|---|---|---:|
| `007E4570` | 42 | `007FC618` | BuildingTypeClass | 0 |

### ② COL — 成立

- `u32(vt-4)` 字节 `18 C6 7F 00` → `007FC618`；④ 写 `007FC618` → **一致**。
- COL 24 字节（sig / offset / cdOffset / pTD / pCHD / pSelf）：`00 00 00 00 00 00 00 00 00 00 00 00 A8 93 81 00 08 C6 7F 00 00 00 00 00`
- `sig = 0` → **0，成立**（卡面要求 `COL.sig == 0`）。
- `offset = 0`（④ 写 `offset=0`）→ **一致**；`pTD = 008193A8`，`pCHD = 007FC608`。

### ③ TD 与类名 — 成立

- `u32(COL+0xC)` 读出 `008193A8`；④ 写 RTTI=`008193A8` → **一致**（**绝对 VA**，不是 RVA）。
- TD 头部 8 字节 + `TD+8` 内联串字节：`94 95 7F 00 00 00 00 00 | 2E 3F 41 56 42 75 69 6C 64 69 6E 67 54 79 70 65 43 6C 61 73 73 40 40 00`
- `TD+8` 按**内联串**读得 `.?AVBuildingTypeClass@@`（不是指针解引用）→ 去修饰 **BuildingTypeClass**；④ 写的类名 `BuildingTypeClass` → **一致**。
- 行名类 = `BuildingTypeClass`，RTTI 类 = `BuildingTypeClass` → 类名**相同**。

### ④ 装表点与宿主 — 成立

- 装表点 `0045E2CD` 处字节 `C7 06 70 45 7E 00` → `mov dword ptr [esi], 0x7e4570`：目标为内存、立即数 == `vt` → **是**。
- 宿主 `0045DD90` 头部字节 `8B 44 24 04 83 EC 08 53 55 56 33 DB 57 53 8B F1`；从宿主做 CFG 遍历（不跟 call）**386** 条指令，装表点在其中 → **在体内**。
- 宿主是独立函数起点：前有 ≥2 字节 `CC/90` 填充 → 是；被 `call rel32` 指向的处数 = **3**（0046542A、00466067、006C29D1）→ 两条独立锚点互证。
- 行 entry `00464AC0` 自身的遍历体 11 条指令，**不含**该装表点 → ④ 的「entry 体外」**成立**（确认）。

### ⑤ ㉓（全写点枚举 + 排除 atexit / 删除析构器）— 成立

枚举 `vt=007E4570` 在 `.text` 里的全部写点（直接 `mov [mem], imm32` 字节定位 + 
`mov reg,imm32` 后紧接 `mov [mem],reg` 的寄存器中介形式；本镜像 `lea reg,[vt]` 中介形式实测 **0** 处）：

| 写点 | 指令 | 宿主 | 宿主在 atexit 超集 | 宿主形态 | initterm 表内 | ④ 用的 |
|---|---|---|---|---|---|---|
| `0045E2CD` | `mov dword ptr [esi], 0x7e4570` | `0045DD90` | 否 | 构造器/普通函数 | 否 | **✔** |
| `0045E558` | `mov dword ptr [esi], 0x7e4570` | `0045E520` | 否 | 构造器/普通函数 | 否 |  |
| `0045E58D` | `mov dword ptr [esi], 0x7e4570` | `0045E580` | 否 | 构造器/普通函数 | 否 |  |

- 共 **3** 个写点。④ 用的是 `0045E2CD`（宿主 `0045DD90`）：不在 atexit 注册超集内、非删除析构器/基类析构器形态 → **㉓ 成立**。
- atexit 口径（本镜像实测）：`push imm32; call 0x7C978A` 严格形态 **68** 个；按「call 前 48 字节内的 `push imm32`」取**保守超集** **172** 个（超集用于「不在集合内」的排除论证）；`call 0x7C978A` 的字节命中总数 336。
- 该 `vt` 的写点里没有析构路径写点；即便如此仍是**全枚举**后才下的判断（不是只查 ④ 那一处）。

**行结论：PASS**（五项全部成立，工程地址与字节如上，可逐条复核）

---

## 行 2/12 · `0055A050` — LoadOptionsClass::GetUIString_Load

④ 原文：`LoadOptionsClass::slot5（vt=007ED2E4，槽 5 值=0055A050，COL=008053B8 offset=0，RTTI=00829E80→.?AVLoadOptionsClass@@；装表点 00558770 位于 00558740 体内，entry 体外）`

### ① vt 与槽号 — 成立

| 读法 | 地址 | 字节 | 值 |
|---|---|---|---|
| `u32(vt-4)`（COL 守卫）| `007ED2E0` | `B8 53 80 00` | `008053B8` |
| `u32(vt + slot*4)` | `007ED2F8` | `50 A0 55 00` | `0055A050` |

- 槽号 `5`（④ 内两处写法一致：是）；`u32(vt+slot*4) == entry` → **是**。
- `vt` 是表起点（`u32(vt-4)` 为合规 COL）→ **是**。
- 我独立全扫 `.rdata/.data` 中值 == `0055A050` 的 dword：共 **1** 个 `(vt, slot)` 见证，④ 的 `(vt=007ED2E4, slot=5)` **是** 其中之一。

- 同 entry 的全部见证：

| vt | slot | COL | 表属类（TD）| COL.offset |
|---|---:|---|---|---:|
| `007ED2E4` | 5 | `008053B8` | LoadOptionsClass | 0 |

### ② COL — 成立

- `u32(vt-4)` 字节 `B8 53 80 00` → `008053B8`；④ 写 `008053B8` → **一致**。
- COL 24 字节（sig / offset / cdOffset / pTD / pCHD / pSelf）：`00 00 00 00 00 00 00 00 00 00 00 00 80 9E 82 00 A8 53 80 00 20 53 80 00`
- `sig = 0` → **0，成立**（卡面要求 `COL.sig == 0`）。
- `offset = 0`（④ 写 `offset=0`）→ **一致**；`pTD = 00829E80`，`pCHD = 008053A8`。

### ③ TD 与类名 — 成立

- `u32(COL+0xC)` 读出 `00829E80`；④ 写 RTTI=`00829E80` → **一致**（**绝对 VA**，不是 RVA）。
- TD 头部 8 字节 + `TD+8` 内联串字节：`94 95 7F 00 00 00 00 00 | 2E 3F 41 56 4C 6F 61 64 4F 70 74 69 6F 6E 73 43 6C 61 73 73 40 40 00 00`
- `TD+8` 按**内联串**读得 `.?AVLoadOptionsClass@@`（不是指针解引用）→ 去修饰 **LoadOptionsClass**；④ 写的类名 `LoadOptionsClass` → **一致**。
- 行名类 = `LoadOptionsClass`，RTTI 类 = `LoadOptionsClass` → 类名**相同**。

### ④ 装表点与宿主 — 成立

- 装表点 `00558770` 处字节 `C7 06 E4 D2 7E 00` → `mov dword ptr [esi], 0x7ed2e4`：目标为内存、立即数 == `vt` → **是**。
- 宿主 `00558740` 头部字节 `56 8B F1 33 C0 8D 4E 20 89 41 04 89 41 08 C6 41`；从宿主做 CFG 遍历（不跟 call）**22** 条指令，装表点在其中 → **在体内**。
- 宿主是独立函数起点：前有 ≥2 字节 `CC/90` 填充 → 是；被 `call rel32` 指向的处数 = **6**（004F136A、004F1469、004F14A0、004F17DD、0052D6A9、0052E0DA）→ 两条独立锚点互证。
- 行 entry `0055A050` 自身的遍历体 6 条指令，**不含**该装表点 → ④ 的「entry 体外」**成立**（确认）。

### ⑤ ㉓（全写点枚举 + 排除 atexit / 删除析构器）— 成立

枚举 `vt=007ED2E4` 在 `.text` 里的全部写点（直接 `mov [mem], imm32` 字节定位 + 
`mov reg,imm32` 后紧接 `mov [mem],reg` 的寄存器中介形式；本镜像 `lea reg,[vt]` 中介形式实测 **0** 处）：

| 写点 | 指令 | 宿主 | 宿主在 atexit 超集 | 宿主形态 | initterm 表内 | ④ 用的 |
|---|---|---|---|---|---|---|
| `00558770` | `mov dword ptr [esi], 0x7ed2e4` | `00558740` | 否 | 构造器/普通函数 | 否 | **✔** |
| `00558799` | `mov dword ptr [esi], 0x7ed2e4` | `00558790` | 否 | 构造器/普通函数 | 否 |  |
| `0055A0D6` | `mov dword ptr [edi], 0x7ed2e4` | `0055A0D0` | 否 | 构造器/普通函数 | 否 |  |

- 共 **3** 个写点。④ 用的是 `00558770`（宿主 `00558740`）：不在 atexit 注册超集内、非删除析构器/基类析构器形态 → **㉓ 成立**。
- atexit 口径（本镜像实测）：`push imm32; call 0x7C978A` 严格形态 **68** 个；按「call 前 48 字节内的 `push imm32`」取**保守超集** **172** 个（超集用于「不在集合内」的排除论证）；`call 0x7C978A` 的字节命中总数 336。
- 该 `vt` 的写点里没有析构路径写点；即便如此仍是**全枚举**后才下的判断（不是只查 ④ 那一处）。

**行结论：PASS**（五项全部成立，工程地址与字节如上，可逐条复核）

---

## 行 3/12 · `0055A950` — LocomotionClass::AddRef

④ 原文：`FlyLocomotionClass::slot1（vt=007E8AC0，槽 1 值=0055A950，COL=008006B8 offset=0，RTTI=008223E8→.?AVFlyLocomotionClass@@；装表点 004CCA0C 位于 004CC9A0 体内，entry 体外）`

### ① vt 与槽号 — 成立

| 读法 | 地址 | 字节 | 值 |
|---|---|---|---|
| `u32(vt-4)`（COL 守卫）| `007E8ABC` | `B8 06 80 00` | `008006B8` |
| `u32(vt + slot*4)` | `007E8AC4` | `50 A9 55 00` | `0055A950` |

- 槽号 `1`（④ 内两处写法一致：是）；`u32(vt+slot*4) == entry` → **是**。
- `vt` 是表起点（`u32(vt-4)` 为合规 COL）→ **是**。
- 我独立全扫 `.rdata/.data` 中值 == `0055A950` 的 dword：共 **6** 个 `(vt, slot)` 见证，④ 的 `(vt=007E8AC0, slot=1)` **是** 其中之一。

- 同 entry 的全部见证：

| vt | slot | COL | 表属类（TD）| COL.offset |
|---|---:|---|---|---:|
| `007E8AC0` | 1 | `008006B8` | FlyLocomotionClass | 0 |
| `007EADC8` | 1 | `00803288` | HoverLocomotionClass | 0 |
| `007EAEC0` | 1 | `008032E8` | LocomotionClass | 0 |
| `007EDC38` | 1 | `00805C88` | MechLocomotionClass | 0 |
| `007F0BE8` | 1 | `00808968` | RocketLocomotionClass | 0 |
| `007F5AF0` | 1 | `0080CB48` | TunnelLocomotionClass | 0 |

### ② COL — 成立

- `u32(vt-4)` 字节 `B8 06 80 00` → `008006B8`；④ 写 `008006B8` → **一致**。
- COL 24 字节（sig / offset / cdOffset / pTD / pCHD / pSelf）：`00 00 00 00 00 00 00 00 00 00 00 00 E8 23 82 00 A8 06 80 00 00 00 00 00`
- `sig = 0` → **0，成立**（卡面要求 `COL.sig == 0`）。
- `offset = 0`（④ 写 `offset=0`）→ **一致**；`pTD = 008223E8`，`pCHD = 008006A8`。

### ③ TD 与类名 — 成立

- `u32(COL+0xC)` 读出 `008223E8`；④ 写 RTTI=`008223E8` → **一致**（**绝对 VA**，不是 RVA）。
- TD 头部 8 字节 + `TD+8` 内联串字节：`94 95 7F 00 00 00 00 00 | 2E 3F 41 56 46 6C 79 4C 6F 63 6F 6D 6F 74 69 6F 6E 43 6C 61 73 73 40 40`
- `TD+8` 按**内联串**读得 `.?AVFlyLocomotionClass@@`（不是指针解引用）→ 去修饰 **FlyLocomotionClass**；④ 写的类名 `FlyLocomotionClass` → **一致**。
- 行名类 = `LocomotionClass`，RTTI 类 = `FlyLocomotionClass` → 类名**不同（见专项一）**。

### ④ 装表点与宿主 — 成立

- 装表点 `004CCA0C` 处字节 `C7 06 C0 8A 7E 00` → `mov dword ptr [esi], 0x7e8ac0`：目标为内存、立即数 == `vt` → **是**。
- 宿主 `004CC9A0` 头部字节 `56 8B F1 E8 18 DD 08 00 33 C0 8D 4E 1C 88 46 18`；从宿主做 CFG 遍历（不跟 call）**37** 条指令，装表点在其中 → **在体内**。
- 宿主是独立函数起点：前有 ≥2 字节 `CC/90` 填充 → 是；被 `call rel32` 指向的处数 = **1**（006C4ACC）→ 两条独立锚点互证。
- 行 entry `0055A950` 自身的遍历体 8 条指令，**不含**该装表点 → ④ 的「entry 体外」**成立**（确认）。

### ⑤ ㉓（全写点枚举 + 排除 atexit / 删除析构器）— 成立

枚举 `vt=007E8AC0` 在 `.text` 里的全部写点（直接 `mov [mem], imm32` 字节定位 + 
`mov reg,imm32` 后紧接 `mov [mem],reg` 的寄存器中介形式；本镜像 `lea reg,[vt]` 中介形式实测 **0** 处）：

| 写点 | 指令 | 宿主 | 宿主在 atexit 超集 | 宿主形态 | initterm 表内 | ④ 用的 |
|---|---|---|---|---|---|---|
| `004CCA0C` | `mov dword ptr [esi], 0x7e8ac0` | `004CC9A0` | 否 | 构造器/普通函数 | 否 | **✔** |
| `004CCA70` | `mov dword ptr [ecx], 0x7e8ac0` | `004CCA70` | 否 | base-dtor-tailjmp | 否 |  |
| `004CFCD8` | `mov dword ptr [esi], 0x7e8ac0` | `004CFCC0` | 否 | 构造器/普通函数 | 否 |  |
| `004D03A3` | `mov dword ptr [esi], 0x7e8ac0` | `004D03A0` | 否 | scalar-deleting-dtor | 否 |  |

- 共 **4** 个写点。④ 用的是 `004CCA0C`（宿主 `004CC9A0`）：不在 atexit 注册超集内、非删除析构器/基类析构器形态 → **㉓ 成立**。
- atexit 口径（本镜像实测）：`push imm32; call 0x7C978A` 严格形态 **68** 个；按「call 前 48 字节内的 `push imm32`」取**保守超集** **172** 个（超集用于「不在集合内」的排除论证）；`call 0x7C978A` 的字节命中总数 336。
- 该 `vt` 的写点里确实存在析构路径：`004CCA70`（base-dtor-tailjmp）、`004D03A3`（scalar-deleting-dtor）——它们都**不是** ④ 用的那一个，正说明枚举必要。

**行结论：PASS**（五项全部成立，工程地址与字节如上，可逐条复核）

---

## 行 4/12 · `00597D50` — MapSeedClass::DeleteMission

④ 原文：`MapSeedClass::slot3（vt=007ED8E4，槽 3 值=00597D50，COL=00805940 offset=0，RTTI=0082BA10→.?AVMapSeedClass@@；装表点 005956CB 位于 00595680 体内，entry 体外）`

### ① vt 与槽号 — 成立

| 读法 | 地址 | 字节 | 值 |
|---|---|---|---|
| `u32(vt-4)`（COL 守卫）| `007ED8E0` | `40 59 80 00` | `00805940` |
| `u32(vt + slot*4)` | `007ED8F0` | `50 7D 59 00` | `00597D50` |

- 槽号 `3`（④ 内两处写法一致：是）；`u32(vt+slot*4) == entry` → **是**。
- `vt` 是表起点（`u32(vt-4)` 为合规 COL）→ **是**。
- 我独立全扫 `.rdata/.data` 中值 == `00597D50` 的 dword：共 **1** 个 `(vt, slot)` 见证，④ 的 `(vt=007ED8E4, slot=3)` **是** 其中之一。

- 同 entry 的全部见证：

| vt | slot | COL | 表属类（TD）| COL.offset |
|---|---:|---|---|---:|
| `007ED8E4` | 3 | `00805940` | MapSeedClass | 0 |

### ② COL — 成立

- `u32(vt-4)` 字节 `40 59 80 00` → `00805940`；④ 写 `00805940` → **一致**。
- COL 24 字节（sig / offset / cdOffset / pTD / pCHD / pSelf）：`00 00 00 00 00 00 00 00 00 00 00 00 10 BA 82 00 30 59 80 00 00 00 00 00`
- `sig = 0` → **0，成立**（卡面要求 `COL.sig == 0`）。
- `offset = 0`（④ 写 `offset=0`）→ **一致**；`pTD = 0082BA10`，`pCHD = 00805930`。

### ③ TD 与类名 — 成立

- `u32(COL+0xC)` 读出 `0082BA10`；④ 写 RTTI=`0082BA10` → **一致**（**绝对 VA**，不是 RVA）。
- TD 头部 8 字节 + `TD+8` 内联串字节：`94 95 7F 00 00 00 00 00 | 2E 3F 41 56 4D 61 70 53 65 65 64 43 6C 61 73 73 40 40 00 00 54 58 54 5F`
- `TD+8` 按**内联串**读得 `.?AVMapSeedClass@@`（不是指针解引用）→ 去修饰 **MapSeedClass**；④ 写的类名 `MapSeedClass` → **一致**。
- 行名类 = `MapSeedClass`，RTTI 类 = `MapSeedClass` → 类名**相同**。

### ④ 装表点与宿主 — 成立

- 装表点 `005956CB` 处字节 `C7 06 E4 D8 7E 00` → `mov dword ptr [esi], 0x7ed8e4`：目标为内存、立即数 == `vt` → **是**。
- 宿主 `00595680` 头部字节 `56 57 8B F1 E8 B7 30 FC FF 8D 7E 78 33 C0 B9 01`；从宿主做 CFG 遍历（不跟 call）**43** 条指令，装表点在其中 → **在体内**。
- 宿主是独立函数起点：前有 ≥2 字节 `CC/90` 填充 → 是；被 `call rel32` 指向的处数 = **3**（00595745、005961D2、00596728）→ 两条独立锚点互证。
- 行 entry `00597D50` 自身的遍历体 4 条指令，**不含**该装表点 → ④ 的「entry 体外」**成立**（确认）。

### ⑤ ㉓（全写点枚举 + 排除 atexit / 删除析构器）— 成立

枚举 `vt=007ED8E4` 在 `.text` 里的全部写点（直接 `mov [mem], imm32` 字节定位 + 
`mov reg,imm32` 后紧接 `mov [mem],reg` 的寄存器中介形式；本镜像 `lea reg,[vt]` 中介形式实测 **0** 处）：

| 写点 | 指令 | 宿主 | 宿主在 atexit 超集 | 宿主形态 | initterm 表内 | ④ 用的 |
|---|---|---|---|---|---|---|
| `005956CB` | `mov dword ptr [esi], 0x7ed8e4` | `00595680` | 否 | 构造器/普通函数 | 否 | **✔** |

- 共 **1** 个写点。④ 用的是 `005956CB`（宿主 `00595680`）：不在 atexit 注册超集内、非删除析构器/基类析构器形态 → **㉓ 成立**。
- atexit 口径（本镜像实测）：`push imm32; call 0x7C978A` 严格形态 **68** 个；按「call 前 48 字节内的 `push imm32`」取**保守超集** **172** 个（超集用于「不在集合内」的排除论证）；`call 0x7C978A` 的字节命中总数 336。
- 该 `vt` 的写点里没有析构路径写点；即便如此仍是**全枚举**后才下的判断（不是只查 ④ 那一处）。

**行结论：PASS**（五项全部成立，工程地址与字节如上，可逐条复核）

---

## 行 5/12 · `005C0FE0` — MPGameModeClass::MPBattleClass

④ 原文：`MultiplayerBattle::slot0（vt=007EE184，槽 0 值=005C0FE0，COL=00806088 offset=0，RTTI=0082DAA8→.?AVMultiplayerBattle@@；装表点 005C0DF8 位于 005C0DD0 体内，entry 体外）`

### ① vt 与槽号 — 成立

| 读法 | 地址 | 字节 | 值 |
|---|---|---|---|
| `u32(vt-4)`（COL 守卫）| `007EE180` | `88 60 80 00` | `00806088` |
| `u32(vt + slot*4)` | `007EE184` | `E0 0F 5C 00` | `005C0FE0` |

- 槽号 `0`（④ 内两处写法一致：是）；`u32(vt+slot*4) == entry` → **是**。
- `vt` 是表起点（`u32(vt-4)` 为合规 COL）→ **是**。
- 我独立全扫 `.rdata/.data` 中值 == `005C0FE0` 的 dword：共 **1** 个 `(vt, slot)` 见证，④ 的 `(vt=007EE184, slot=0)` **是** 其中之一。

- 同 entry 的全部见证：

| vt | slot | COL | 表属类（TD）| COL.offset |
|---|---:|---|---|---:|
| `007EE184` | 0 | `00806088` | MultiplayerBattle | 0 |

### ② COL — 成立

- `u32(vt-4)` 字节 `88 60 80 00` → `00806088`；④ 写 `00806088` → **一致**。
- COL 24 字节（sig / offset / cdOffset / pTD / pCHD / pSelf）：`00 00 00 00 00 00 00 00 00 00 00 00 A8 DA 82 00 78 60 80 00 00 00 00 00`
- `sig = 0` → **0，成立**（卡面要求 `COL.sig == 0`）。
- `offset = 0`（④ 写 `offset=0`）→ **一致**；`pTD = 0082DAA8`，`pCHD = 00806078`。

### ③ TD 与类名 — 成立

- `u32(COL+0xC)` 读出 `0082DAA8`；④ 写 RTTI=`0082DAA8` → **一致**（**绝对 VA**，不是 RVA）。
- TD 头部 8 字节 + `TD+8` 内联串字节：`94 95 7F 00 00 00 00 00 | 2E 3F 41 56 4D 75 6C 74 69 70 6C 61 79 65 72 42 61 74 74 6C 65 40 40 00`
- `TD+8` 按**内联串**读得 `.?AVMultiplayerBattle@@`（不是指针解引用）→ 去修饰 **MultiplayerBattle**；④ 写的类名 `MultiplayerBattle` → **一致**。
- 行名类 = `MPGameModeClass`，RTTI 类 = `MultiplayerBattle` → 类名**不同（见专项一）**。

### ④ 装表点与宿主 — 成立

- 装表点 `005C0DF8` 处字节 `C7 06 84 E1 7E 00` → `mov dword ptr [esi], 0x7ee184`：目标为内存、立即数 == `vt` → **是**。
- 宿主 `005C0DD0` 头部字节 `8B 44 24 18 8B 54 24 10 56 8B F1 8B 4C 24 18 50`；从宿主做 CFG 遍历（不跟 call）**20** 条指令，装表点在其中 → **在体内**。
- 宿主是独立函数起点：前有 ≥2 字节 `CC/90` 填充 → 是；被 `call rel32` 指向的处数 = **1**（005D819E）→ 两条独立锚点互证。
- 行 entry `005C0FE0` 自身的遍历体 12 条指令，**不含**该装表点 → ④ 的「entry 体外」**成立**（确认）。

### ⑤ ㉓（全写点枚举 + 排除 atexit / 删除析构器）— 成立

枚举 `vt=007EE184` 在 `.text` 里的全部写点（直接 `mov [mem], imm32` 字节定位 + 
`mov reg,imm32` 后紧接 `mov [mem],reg` 的寄存器中介形式；本镜像 `lea reg,[vt]` 中介形式实测 **0** 处）：

| 写点 | 指令 | 宿主 | 宿主在 atexit 超集 | 宿主形态 | initterm 表内 | ④ 用的 |
|---|---|---|---|---|---|---|
| `005C0DF8` | `mov dword ptr [esi], 0x7ee184` | `005C0DD0` | 否 | 构造器/普通函数 | 否 | **✔** |
| `005C0E10` | `mov dword ptr [ecx], 0x7ee184` | `005C0E10` | 否 | base-dtor-tailjmp | 否 |  |
| `005C0FE3` | `mov dword ptr [esi], 0x7ee184` | `005C0FE0` | 否 | scalar-deleting-dtor | 否 |  |

- 共 **3** 个写点。④ 用的是 `005C0DF8`（宿主 `005C0DD0`）：不在 atexit 注册超集内、非删除析构器/基类析构器形态 → **㉓ 成立**。
- atexit 口径（本镜像实测）：`push imm32; call 0x7C978A` 严格形态 **68** 个；按「call 前 48 字节内的 `push imm32`」取**保守超集** **172** 个（超集用于「不在集合内」的排除论证）；`call 0x7C978A` 的字节命中总数 336。
- 该 `vt` 的写点里确实存在析构路径：`005C0E10`（base-dtor-tailjmp）、`005C0FE3`（scalar-deleting-dtor）——它们都**不是** ④ 用的那一个，正说明枚举必要。

**行结论：PASS**（五项全部成立，工程地址与字节如上，可逐条复核）

---

## 行 6/12 · `005CA6D0` — MPGameModeClass::vt_entry_14

④ 原文：`MultiplayerSiege::slot5（vt=007EE6FC，槽 5 值=005CA6D0，COL=00806498 offset=0，RTTI=0082FEC8→.?AVMultiplayerSiege@@；装表点 005CA658 位于 005CA630 体内，entry 体外）`

### ① vt 与槽号 — 成立

| 读法 | 地址 | 字节 | 值 |
|---|---|---|---|
| `u32(vt-4)`（COL 守卫）| `007EE6F8` | `98 64 80 00` | `00806498` |
| `u32(vt + slot*4)` | `007EE710` | `D0 A6 5C 00` | `005CA6D0` |

- 槽号 `5`（④ 内两处写法一致：是）；`u32(vt+slot*4) == entry` → **是**。
- `vt` 是表起点（`u32(vt-4)` 为合规 COL）→ **是**。
- 我独立全扫 `.rdata/.data` 中值 == `005CA6D0` 的 dword：共 **1** 个 `(vt, slot)` 见证，④ 的 `(vt=007EE6FC, slot=5)` **是** 其中之一。

- 同 entry 的全部见证：

| vt | slot | COL | 表属类（TD）| COL.offset |
|---|---:|---|---|---:|
| `007EE6FC` | 5 | `00806498` | MultiplayerSiege | 0 |

### ② COL — 成立

- `u32(vt-4)` 字节 `98 64 80 00` → `00806498`；④ 写 `00806498` → **一致**。
- COL 24 字节（sig / offset / cdOffset / pTD / pCHD / pSelf）：`00 00 00 00 00 00 00 00 00 00 00 00 C8 FE 82 00 88 64 80 00 00 00 00 00`
- `sig = 0` → **0，成立**（卡面要求 `COL.sig == 0`）。
- `offset = 0`（④ 写 `offset=0`）→ **一致**；`pTD = 0082FEC8`，`pCHD = 00806488`。

### ③ TD 与类名 — 成立

- `u32(COL+0xC)` 读出 `0082FEC8`；④ 写 RTTI=`0082FEC8` → **一致**（**绝对 VA**，不是 RVA）。
- TD 头部 8 字节 + `TD+8` 内联串字节：`94 95 7F 00 00 00 00 00 | 2E 3F 41 56 4D 75 6C 74 69 70 6C 61 79 65 72 53 69 65 67 65 40 40 00 00`
- `TD+8` 按**内联串**读得 `.?AVMultiplayerSiege@@`（不是指针解引用）→ 去修饰 **MultiplayerSiege**；④ 写的类名 `MultiplayerSiege` → **一致**。
- 行名类 = `MPGameModeClass`，RTTI 类 = `MultiplayerSiege` → 类名**不同（见专项一）**。

### ④ 装表点与宿主 — 成立

- 装表点 `005CA658` 处字节 `C7 06 FC E6 7E 00` → `mov dword ptr [esi], 0x7ee6fc`：目标为内存、立即数 == `vt` → **是**。
- 宿主 `005CA630` 头部字节 `8B 44 24 18 8B 54 24 10 56 8B F1 8B 4C 24 18 50`；从宿主做 CFG 遍历（不跟 call）**20** 条指令，装表点在其中 → **在体内**。
- 宿主是独立函数起点：前有 ≥2 字节 `CC/90` 填充 → 是；被 `call rel32` 指向的处数 = **1**（005D821E）→ 两条独立锚点互证。
- 行 entry `005CA6D0` 自身的遍历体 104 条指令，**不含**该装表点 → ④ 的「entry 体外」**成立**（确认）。

### ⑤ ㉓（全写点枚举 + 排除 atexit / 删除析构器）— 成立

枚举 `vt=007EE6FC` 在 `.text` 里的全部写点（直接 `mov [mem], imm32` 字节定位 + 
`mov reg,imm32` 后紧接 `mov [mem],reg` 的寄存器中介形式；本镜像 `lea reg,[vt]` 中介形式实测 **0** 处）：

| 写点 | 指令 | 宿主 | 宿主在 atexit 超集 | 宿主形态 | initterm 表内 | ④ 用的 |
|---|---|---|---|---|---|---|
| `005CA658` | `mov dword ptr [esi], 0x7ee6fc` | `005CA630` | 否 | 构造器/普通函数 | 否 | **✔** |
| `005CA670` | `mov dword ptr [ecx], 0x7ee6fc` | `005CA670` | 否 | base-dtor-tailjmp | 否 |  |
| `005CABD3` | `mov dword ptr [esi], 0x7ee6fc` | `005CABD0` | 否 | scalar-deleting-dtor | 否 |  |

- 共 **3** 个写点。④ 用的是 `005CA658`（宿主 `005CA630`）：不在 atexit 注册超集内、非删除析构器/基类析构器形态 → **㉓ 成立**。
- atexit 口径（本镜像实测）：`push imm32; call 0x7C978A` 严格形态 **68** 个；按「call 前 48 字节内的 `push imm32`」取**保守超集** **172** 个（超集用于「不在集合内」的排除论证）；`call 0x7C978A` 的字节命中总数 336。
- 该 `vt` 的写点里确实存在析构路径：`005CA670`（base-dtor-tailjmp）、`005CABD3`（scalar-deleting-dtor）——它们都**不是** ④ 用的那一个，正说明枚举必要。

**行结论：PASS**（五项全部成立，工程地址与字节如上，可逐条复核）

---

## 行 7/12 · `005CB440` — MPGameModeClass::SpawnBaseUnits

④ 原文：`UnholyAlliance::slot50（vt=007EE814，槽 50 值=005CB440，COL=00806588 offset=0，RTTI=00830058→.?AVUnholyAlliance@@；装表点 005CB3C8 位于 005CB3A0 体内，entry 体外）`

### ① vt 与槽号 — 成立

| 读法 | 地址 | 字节 | 值 |
|---|---|---|---|
| `u32(vt-4)`（COL 守卫）| `007EE810` | `88 65 80 00` | `00806588` |
| `u32(vt + slot*4)` | `007EE8DC` | `40 B4 5C 00` | `005CB440` |

- 槽号 `50`（④ 内两处写法一致：是）；`u32(vt+slot*4) == entry` → **是**。
- `vt` 是表起点（`u32(vt-4)` 为合规 COL）→ **是**。
- 我独立全扫 `.rdata/.data` 中值 == `005CB440` 的 dword：共 **1** 个 `(vt, slot)` 见证，④ 的 `(vt=007EE814, slot=50)` **是** 其中之一。

- 同 entry 的全部见证：

| vt | slot | COL | 表属类（TD）| COL.offset |
|---|---:|---|---|---:|
| `007EE814` | 50 | `00806588` | UnholyAlliance | 0 |

### ② COL — 成立

- `u32(vt-4)` 字节 `88 65 80 00` → `00806588`；④ 写 `00806588` → **一致**。
- COL 24 字节（sig / offset / cdOffset / pTD / pCHD / pSelf）：`00 00 00 00 00 00 00 00 00 00 00 00 58 00 83 00 78 65 80 00 00 00 00 00`
- `sig = 0` → **0，成立**（卡面要求 `COL.sig == 0`）。
- `offset = 0`（④ 写 `offset=0`）→ **一致**；`pTD = 00830058`，`pCHD = 00806578`。

### ③ TD 与类名 — 成立

- `u32(COL+0xC)` 读出 `00830058`；④ 写 RTTI=`00830058` → **一致**（**绝对 VA**，不是 RVA）。
- TD 头部 8 字节 + `TD+8` 内联串字节：`94 95 7F 00 00 00 00 00 | 2E 3F 41 56 55 6E 68 6F 6C 79 41 6C 6C 69 61 6E 63 65 40 40 00 00 00 00`
- `TD+8` 按**内联串**读得 `.?AVUnholyAlliance@@`（不是指针解引用）→ 去修饰 **UnholyAlliance**；④ 写的类名 `UnholyAlliance` → **一致**。
- 行名类 = `MPGameModeClass`，RTTI 类 = `UnholyAlliance` → 类名**不同（见专项一）**。

### ④ 装表点与宿主 — 成立

- 装表点 `005CB3C8` 处字节 `C7 06 14 E8 7E 00` → `mov dword ptr [esi], 0x7ee814`：目标为内存、立即数 == `vt` → **是**。
- 宿主 `005CB3A0` 头部字节 `8B 44 24 18 8B 54 24 10 56 8B F1 8B 4C 24 18 50`；从宿主做 CFG 遍历（不跟 call）**20** 条指令，装表点在其中 → **在体内**。
- 宿主是独立函数起点：前有 ≥2 字节 `CC/90` 填充 → 是；被 `call rel32` 指向的处数 = **1**（005D825E）→ 两条独立锚点互证。
- 行 entry `005CB440` 自身的遍历体 85 条指令，**不含**该装表点 → ④ 的「entry 体外」**成立**（确认）。

### ⑤ ㉓（全写点枚举 + 排除 atexit / 删除析构器）— 成立

枚举 `vt=007EE814` 在 `.text` 里的全部写点（直接 `mov [mem], imm32` 字节定位 + 
`mov reg,imm32` 后紧接 `mov [mem],reg` 的寄存器中介形式；本镜像 `lea reg,[vt]` 中介形式实测 **0** 处）：

| 写点 | 指令 | 宿主 | 宿主在 atexit 超集 | 宿主形态 | initterm 表内 | ④ 用的 |
|---|---|---|---|---|---|---|
| `005CB3C8` | `mov dword ptr [esi], 0x7ee814` | `005CB3A0` | 否 | 构造器/普通函数 | 否 | **✔** |
| `005CB3E0` | `mov dword ptr [ecx], 0x7ee814` | `005CB3E0` | 否 | base-dtor-tailjmp | 否 |  |
| `005CB543` | `mov dword ptr [esi], 0x7ee814` | `005CB540` | 否 | scalar-deleting-dtor | 否 |  |

- 共 **3** 个写点。④ 用的是 `005CB3C8`（宿主 `005CB3A0`）：不在 atexit 注册超集内、非删除析构器/基类析构器形态 → **㉓ 成立**。
- atexit 口径（本镜像实测）：`push imm32; call 0x7C978A` 严格形态 **68** 个；按「call 前 48 字节内的 `push imm32`」取**保守超集** **172** 个（超集用于「不在集合内」的排除论证）；`call 0x7C978A` 的字节命中总数 336。
- 该 `vt` 的写点里确实存在析构路径：`005CB3E0`（base-dtor-tailjmp）、`005CB543`（scalar-deleting-dtor）——它们都**不是** ④ 用的那一个，正说明枚举必要。

**行结论：PASS**（五项全部成立，工程地址与字节如上，可逐条复核）

---

## 行 8/12 · `005D6540` — MPGameModeClass::PopulateTeamDropdownForPlayer

④ 原文：`MultiplayerBattle::slot20（vt=007EE184，槽 20 值=005D6540，COL=00806088 offset=0，RTTI=0082DAA8→.?AVMultiplayerBattle@@；装表点 005C0DF8 位于 005C0DD0 体内，entry 体外）`

### ① vt 与槽号 — 成立

| 读法 | 地址 | 字节 | 值 |
|---|---|---|---|
| `u32(vt-4)`（COL 守卫）| `007EE180` | `88 60 80 00` | `00806088` |
| `u32(vt + slot*4)` | `007EE1D4` | `40 65 5D 00` | `005D6540` |

- 槽号 `20`（④ 内两处写法一致：是）；`u32(vt+slot*4) == entry` → **是**。
- `vt` 是表起点（`u32(vt-4)` 为合规 COL）→ **是**。
- 我独立全扫 `.rdata/.data` 中值 == `005D6540` 的 dword：共 **6** 个 `(vt, slot)` 见证，④ 的 `(vt=007EE184, slot=20)` **是** 其中之一。

- 同 entry 的全部见证：

| vt | slot | COL | 表属类（TD）| COL.offset |
|---|---:|---|---|---:|
| `007EE184` | 20 | `00806088` | MultiplayerBattle | 0 |
| `007EE50C` | 20 | `008063A8` | MultiplayerManBattle | 0 |
| `007EE5F4` | 20 | `008063F8` | Megawealth | 0 |
| `007EE6FC` | 20 | `00806498` | MultiplayerSiege | 0 |
| `007EE814` | 20 | `00806588` | UnholyAlliance | 0 |
| `007EED60` | 20 | `00806F88` | MultiplayerGameMode | 0 |

### ② COL — 成立

- `u32(vt-4)` 字节 `88 60 80 00` → `00806088`；④ 写 `00806088` → **一致**。
- COL 24 字节（sig / offset / cdOffset / pTD / pCHD / pSelf）：`00 00 00 00 00 00 00 00 00 00 00 00 A8 DA 82 00 78 60 80 00 00 00 00 00`
- `sig = 0` → **0，成立**（卡面要求 `COL.sig == 0`）。
- `offset = 0`（④ 写 `offset=0`）→ **一致**；`pTD = 0082DAA8`，`pCHD = 00806078`。

### ③ TD 与类名 — 成立

- `u32(COL+0xC)` 读出 `0082DAA8`；④ 写 RTTI=`0082DAA8` → **一致**（**绝对 VA**，不是 RVA）。
- TD 头部 8 字节 + `TD+8` 内联串字节：`94 95 7F 00 00 00 00 00 | 2E 3F 41 56 4D 75 6C 74 69 70 6C 61 79 65 72 42 61 74 74 6C 65 40 40 00`
- `TD+8` 按**内联串**读得 `.?AVMultiplayerBattle@@`（不是指针解引用）→ 去修饰 **MultiplayerBattle**；④ 写的类名 `MultiplayerBattle` → **一致**。
- 行名类 = `MPGameModeClass`，RTTI 类 = `MultiplayerBattle` → 类名**不同（见专项一）**。

### ④ 装表点与宿主 — 成立

- 装表点 `005C0DF8` 处字节 `C7 06 84 E1 7E 00` → `mov dword ptr [esi], 0x7ee184`：目标为内存、立即数 == `vt` → **是**。
- 宿主 `005C0DD0` 头部字节 `8B 44 24 18 8B 54 24 10 56 8B F1 8B 4C 24 18 50`；从宿主做 CFG 遍历（不跟 call）**20** 条指令，装表点在其中 → **在体内**。
- 宿主是独立函数起点：前有 ≥2 字节 `CC/90` 填充 → 是；被 `call rel32` 指向的处数 = **1**（005D819E）→ 两条独立锚点互证。
- 行 entry `005D6540` 自身的遍历体 79 条指令，**不含**该装表点 → ④ 的「entry 体外」**成立**（确认）。

### ⑤ ㉓（全写点枚举 + 排除 atexit / 删除析构器）— 成立

枚举 `vt=007EE184` 在 `.text` 里的全部写点（直接 `mov [mem], imm32` 字节定位 + 
`mov reg,imm32` 后紧接 `mov [mem],reg` 的寄存器中介形式；本镜像 `lea reg,[vt]` 中介形式实测 **0** 处）：

| 写点 | 指令 | 宿主 | 宿主在 atexit 超集 | 宿主形态 | initterm 表内 | ④ 用的 |
|---|---|---|---|---|---|---|
| `005C0DF8` | `mov dword ptr [esi], 0x7ee184` | `005C0DD0` | 否 | 构造器/普通函数 | 否 | **✔** |
| `005C0E10` | `mov dword ptr [ecx], 0x7ee184` | `005C0E10` | 否 | base-dtor-tailjmp | 否 |  |
| `005C0FE3` | `mov dword ptr [esi], 0x7ee184` | `005C0FE0` | 否 | scalar-deleting-dtor | 否 |  |

- 共 **3** 个写点。④ 用的是 `005C0DF8`（宿主 `005C0DD0`）：不在 atexit 注册超集内、非删除析构器/基类析构器形态 → **㉓ 成立**。
- atexit 口径（本镜像实测）：`push imm32; call 0x7C978A` 严格形态 **68** 个；按「call 前 48 字节内的 `push imm32`」取**保守超集** **172** 个（超集用于「不在集合内」的排除论证）；`call 0x7C978A` 的字节命中总数 336。
- 该 `vt` 的写点里确实存在析构路径：`005C0E10`（base-dtor-tailjmp）、`005C0FE3`（scalar-deleting-dtor）——它们都**不是** ④ 用的那一个，正说明枚举必要。

**行结论：PASS**（五项全部成立，工程地址与字节如上，可逐条复核）

---

## 行 9/12 · `005D74A0` — MPGameModeClass::AllyTeams

④ 原文：`MultiplayerBattle::slot34（vt=007EE184，槽 34 值=005D74A0，COL=00806088 offset=0，RTTI=0082DAA8→.?AVMultiplayerBattle@@；装表点 005C0DF8 位于 005C0DD0 体内，entry 体外）`

### ① vt 与槽号 — 成立

| 读法 | 地址 | 字节 | 值 |
|---|---|---|---|
| `u32(vt-4)`（COL 守卫）| `007EE180` | `88 60 80 00` | `00806088` |
| `u32(vt + slot*4)` | `007EE20C` | `A0 74 5D 00` | `005D74A0` |

- 槽号 `34`（④ 内两处写法一致：是）；`u32(vt+slot*4) == entry` → **是**。
- `vt` 是表起点（`u32(vt-4)` 为合规 COL）→ **是**。
- 我独立全扫 `.rdata/.data` 中值 == `005D74A0` 的 dword：共 **7** 个 `(vt, slot)` 见证，④ 的 `(vt=007EE184, slot=34)` **是** 其中之一。

- 同 entry 的全部见证：

| vt | slot | COL | 表属类（TD）| COL.offset |
|---|---:|---|---|---:|
| `007EE184` | 34 | `00806088` | MultiplayerBattle | 0 |
| `007EE424` | 34 | `00806358` | FreeForAll | 0 |
| `007EE50C` | 34 | `008063A8` | MultiplayerManBattle | 0 |
| `007EE5F4` | 34 | `008063F8` | Megawealth | 0 |
| `007EE6FC` | 34 | `00806498` | MultiplayerSiege | 0 |
| `007EE814` | 34 | `00806588` | UnholyAlliance | 0 |
| `007EED60` | 34 | `00806F88` | MultiplayerGameMode | 0 |

### ② COL — 成立

- `u32(vt-4)` 字节 `88 60 80 00` → `00806088`；④ 写 `00806088` → **一致**。
- COL 24 字节（sig / offset / cdOffset / pTD / pCHD / pSelf）：`00 00 00 00 00 00 00 00 00 00 00 00 A8 DA 82 00 78 60 80 00 00 00 00 00`
- `sig = 0` → **0，成立**（卡面要求 `COL.sig == 0`）。
- `offset = 0`（④ 写 `offset=0`）→ **一致**；`pTD = 0082DAA8`，`pCHD = 00806078`。

### ③ TD 与类名 — 成立

- `u32(COL+0xC)` 读出 `0082DAA8`；④ 写 RTTI=`0082DAA8` → **一致**（**绝对 VA**，不是 RVA）。
- TD 头部 8 字节 + `TD+8` 内联串字节：`94 95 7F 00 00 00 00 00 | 2E 3F 41 56 4D 75 6C 74 69 70 6C 61 79 65 72 42 61 74 74 6C 65 40 40 00`
- `TD+8` 按**内联串**读得 `.?AVMultiplayerBattle@@`（不是指针解引用）→ 去修饰 **MultiplayerBattle**；④ 写的类名 `MultiplayerBattle` → **一致**。
- 行名类 = `MPGameModeClass`，RTTI 类 = `MultiplayerBattle` → 类名**不同（见专项一）**。

### ④ 装表点与宿主 — 成立

- 装表点 `005C0DF8` 处字节 `C7 06 84 E1 7E 00` → `mov dword ptr [esi], 0x7ee184`：目标为内存、立即数 == `vt` → **是**。
- 宿主 `005C0DD0` 头部字节 `8B 44 24 18 8B 54 24 10 56 8B F1 8B 4C 24 18 50`；从宿主做 CFG 遍历（不跟 call）**20** 条指令，装表点在其中 → **在体内**。
- 宿主是独立函数起点：前有 ≥2 字节 `CC/90` 填充 → 是；被 `call rel32` 指向的处数 = **1**（005D819E）→ 两条独立锚点互证。
- 行 entry `005D74A0` 自身的遍历体 64 条指令，**不含**该装表点 → ④ 的「entry 体外」**成立**（确认）。

### ⑤ ㉓（全写点枚举 + 排除 atexit / 删除析构器）— 成立

枚举 `vt=007EE184` 在 `.text` 里的全部写点（直接 `mov [mem], imm32` 字节定位 + 
`mov reg,imm32` 后紧接 `mov [mem],reg` 的寄存器中介形式；本镜像 `lea reg,[vt]` 中介形式实测 **0** 处）：

| 写点 | 指令 | 宿主 | 宿主在 atexit 超集 | 宿主形态 | initterm 表内 | ④ 用的 |
|---|---|---|---|---|---|---|
| `005C0DF8` | `mov dword ptr [esi], 0x7ee184` | `005C0DD0` | 否 | 构造器/普通函数 | 否 | **✔** |
| `005C0E10` | `mov dword ptr [ecx], 0x7ee184` | `005C0E10` | 否 | base-dtor-tailjmp | 否 |  |
| `005C0FE3` | `mov dword ptr [esi], 0x7ee184` | `005C0FE0` | 否 | scalar-deleting-dtor | 否 |  |

- 共 **3** 个写点。④ 用的是 `005C0DF8`（宿主 `005C0DD0`）：不在 atexit 注册超集内、非删除析构器/基类析构器形态 → **㉓ 成立**。
- atexit 口径（本镜像实测）：`push imm32; call 0x7C978A` 严格形态 **68** 个；按「call 前 48 字节内的 `push imm32`」取**保守超集** **172** 个（超集用于「不在集合内」的排除论证）；`call 0x7C978A` 的字节命中总数 336。
- 该 `vt` 的写点里确实存在析构路径：`005C0E10`（base-dtor-tailjmp）、`005C0FE3`（scalar-deleting-dtor）——它们都**不是** ④ 用的那一个，正说明枚举必要。

**行结论：PASS**（五项全部成立，工程地址与字节如上，可逐条复核）

---

## 行 10/12 · `0073C5F0` — UnitClass::DrawAsSHP

④ 原文：`UnitClass::slot342（vt=007F5C70，槽 342 值=0073C5F0，COL=0080CC68 offset=0，RTTI=00842D80→.?AVUnitClass@@；装表点 0073543A 位于 007353C0 体内，entry 体外）`

### ① vt 与槽号 — 成立

| 读法 | 地址 | 字节 | 值 |
|---|---|---|---|
| `u32(vt-4)`（COL 守卫）| `007F5C6C` | `68 CC 80 00` | `0080CC68` |
| `u32(vt + slot*4)` | `007F61C8` | `F0 C5 73 00` | `0073C5F0` |

- 槽号 `342`（④ 内两处写法一致：是）；`u32(vt+slot*4) == entry` → **是**。
- `vt` 是表起点（`u32(vt-4)` 为合规 COL）→ **是**。
- 我独立全扫 `.rdata/.data` 中值 == `0073C5F0` 的 dword：共 **1** 个 `(vt, slot)` 见证，④ 的 `(vt=007F5C70, slot=342)` **是** 其中之一。

- 同 entry 的全部见证：

| vt | slot | COL | 表属类（TD）| COL.offset |
|---|---:|---|---|---:|
| `007F5C70` | 342 | `0080CC68` | UnitClass | 0 |

### ② COL — 成立

- `u32(vt-4)` 字节 `68 CC 80 00` → `0080CC68`；④ 写 `0080CC68` → **一致**。
- COL 24 字节（sig / offset / cdOffset / pTD / pCHD / pSelf）：`00 00 00 00 00 00 00 00 00 00 00 00 80 2D 84 00 58 CC 80 00 00 00 00 00`
- `sig = 0` → **0，成立**（卡面要求 `COL.sig == 0`）。
- `offset = 0`（④ 写 `offset=0`）→ **一致**；`pTD = 00842D80`，`pCHD = 0080CC58`。

### ③ TD 与类名 — 成立

- `u32(COL+0xC)` 读出 `00842D80`；④ 写 RTTI=`00842D80` → **一致**（**绝对 VA**，不是 RVA）。
- TD 头部 8 字节 + `TD+8` 内联串字节：`94 95 7F 00 00 00 00 00 | 2E 3F 41 56 55 6E 69 74 43 6C 61 73 73 40 40 00 94 95 7F 00 00 00 00 00`
- `TD+8` 按**内联串**读得 `.?AVUnitClass@@`（不是指针解引用）→ 去修饰 **UnitClass**；④ 写的类名 `UnitClass` → **一致**。
- 行名类 = `UnitClass`，RTTI 类 = `UnitClass` → 类名**相同**。

### ④ 装表点与宿主 — 成立

- 装表点 `0073543A` 处字节 `C7 06 70 5C 7F 00` → `mov dword ptr [esi], 0x7f5c70`：目标为内存、立即数 == `vt` → **是**。
- 宿主 `007353C0` 头部字节 `8B 44 24 08 83 EC 0C 53 55 56 57 8B F1 50 E8 0D`；从宿主做 CFG 遍历（不跟 call）**268** 条指令，装表点在其中 → **在体内**。
- 宿主是独立函数起点：前有 ≥2 字节 `CC/90` 填充 → 是；被 `call rel32` 指向的处数 = **6**（00446B8E、00449E44、00473892、00504CD5、005A6A26、005A8826）→ 两条独立锚点互证。
- 行 entry `0073C5F0` 自身的遍历体 676 条指令，**不含**该装表点 → ④ 的「entry 体外」**成立**（确认）。

### ⑤ ㉓（全写点枚举 + 排除 atexit / 删除析构器）— 成立

枚举 `vt=007F5C70` 在 `.text` 里的全部写点（直接 `mov [mem], imm32` 字节定位 + 
`mov reg,imm32` 后紧接 `mov [mem],reg` 的寄存器中介形式；本镜像 `lea reg,[vt]` 中介形式实测 **0** 处）：

| 写点 | 指令 | 宿主 | 宿主在 atexit 超集 | 宿主形态 | initterm 表内 | ④ 用的 |
|---|---|---|---|---|---|---|
| `0073543A` | `mov dword ptr [esi], 0x7f5c70` | `007353C0` | 否 | 构造器/普通函数 | 否 | **✔** |
| `00735794` | `mov dword ptr [esi], 0x7f5c70` | `00735780` | 否 | 构造器/普通函数 | 否 |  |
| `00744521` | `mov dword ptr [esi], 0x7f5c70` | `00744470` | 否 | 构造器/普通函数 | 否 |  |

- 共 **3** 个写点。④ 用的是 `0073543A`（宿主 `007353C0`）：不在 atexit 注册超集内、非删除析构器/基类析构器形态 → **㉓ 成立**。
- atexit 口径（本镜像实测）：`push imm32; call 0x7C978A` 严格形态 **68** 个；按「call 前 48 字节内的 `push imm32`」取**保守超集** **172** 个（超集用于「不在集合内」的排除论证）；`call 0x7C978A` 的字节命中总数 336。
- 该 `vt` 的写点里没有析构路径写点；即便如此仍是**全枚举**后才下的判断（不是只查 ④ 那一处）。

**行结论：PASS**（五项全部成立，工程地址与字节如上，可逐条复核）

---

## 行 11/12 · `007B9C30` — WWMouseClass::ReleaseMouse

④ 原文：`WWMouseClass::slot5（vt=007F7B2C，槽 5 值=007B9C30，COL=0080EC60 offset=0，RTTI=0084E638→.?AVWWMouseClass@@；装表点 007B8850 位于 007B8730 体内，entry 体外）`

### ① vt 与槽号 — 成立

| 读法 | 地址 | 字节 | 值 |
|---|---|---|---|
| `u32(vt-4)`（COL 守卫）| `007F7B28` | `60 EC 80 00` | `0080EC60` |
| `u32(vt + slot*4)` | `007F7B40` | `30 9C 7B 00` | `007B9C30` |

- 槽号 `5`（④ 内两处写法一致：是）；`u32(vt+slot*4) == entry` → **是**。
- `vt` 是表起点（`u32(vt-4)` 为合规 COL）→ **是**。
- 我独立全扫 `.rdata/.data` 中值 == `007B9C30` 的 dword：共 **1** 个 `(vt, slot)` 见证，④ 的 `(vt=007F7B2C, slot=5)` **是** 其中之一。

- 同 entry 的全部见证：

| vt | slot | COL | 表属类（TD）| COL.offset |
|---|---:|---|---|---:|
| `007F7B2C` | 5 | `0080EC60` | WWMouseClass | 0 |

### ② COL — 成立

- `u32(vt-4)` 字节 `60 EC 80 00` → `0080EC60`；④ 写 `0080EC60` → **一致**。
- COL 24 字节（sig / offset / cdOffset / pTD / pCHD / pSelf）：`00 00 00 00 00 00 00 00 00 00 00 00 38 E6 84 00 50 EC 80 00 00 00 00 00`
- `sig = 0` → **0，成立**（卡面要求 `COL.sig == 0`）。
- `offset = 0`（④ 写 `offset=0`）→ **一致**；`pTD = 0084E638`，`pCHD = 0080EC50`。

### ③ TD 与类名 — 成立

- `u32(COL+0xC)` 读出 `0084E638`；④ 写 RTTI=`0084E638` → **一致**（**绝对 VA**，不是 RVA）。
- TD 头部 8 字节 + `TD+8` 内联串字节：`94 95 7F 00 00 00 00 00 | 2E 3F 41 56 57 57 4D 6F 75 73 65 43 6C 61 73 73 40 40 00 00 00 00 00 00`
- `TD+8` 按**内联串**读得 `.?AVWWMouseClass@@`（不是指针解引用）→ 去修饰 **WWMouseClass**；④ 写的类名 `WWMouseClass` → **一致**。
- 行名类 = `WWMouseClass`，RTTI 类 = `WWMouseClass` → 类名**相同**。

### ④ 装表点与宿主 — 成立

- 装表点 `007B8850` 处字节 `C7 06 2C 7B 7F 00` → `mov dword ptr [esi], 0x7f7b2c`：目标为内存、立即数 == `vt` → **是**。
- 宿主 `007B8730` 头部字节 `8B 54 24 08 53 56 8B F1 8B 4C 24 0C 57 33 DB 83`；从宿主做 CFG 遍历（不跟 call）**111** 条指令，装表点在其中 → **在体内**。
- 宿主是独立函数起点：前有 ≥2 字节 `CC/90` 填充 → 是；被 `call rel32` 指向的处数 = **3**（00560D62、0056107A、006BDF1C）→ 两条独立锚点互证。
- 行 entry `007B9C30` 自身的遍历体 102 条指令，**不含**该装表点 → ④ 的「entry 体外」**成立**（确认）。

### ⑤ ㉓（全写点枚举 + 排除 atexit / 删除析构器）— 成立

枚举 `vt=007F7B2C` 在 `.text` 里的全部写点（直接 `mov [mem], imm32` 字节定位 + 
`mov reg,imm32` 后紧接 `mov [mem],reg` 的寄存器中介形式；本镜像 `lea reg,[vt]` 中介形式实测 **0** 处）：

| 写点 | 指令 | 宿主 | 宿主在 atexit 超集 | 宿主形态 | initterm 表内 | ④ 用的 |
|---|---|---|---|---|---|---|
| `007B8850` | `mov dword ptr [esi], 0x7f7b2c` | `007B8730` | 否 | 构造器/普通函数 | 否 | **✔** |
| `007B88D9` | `mov dword ptr [esi], 0x7f7b2c` | `007B88D0` | 否 | 构造器/普通函数 | 否 |  |

- 共 **2** 个写点。④ 用的是 `007B8850`（宿主 `007B8730`）：不在 atexit 注册超集内、非删除析构器/基类析构器形态 → **㉓ 成立**。
- atexit 口径（本镜像实测）：`push imm32; call 0x7C978A` 严格形态 **68** 个；按「call 前 48 字节内的 `push imm32`」取**保守超集** **172** 个（超集用于「不在集合内」的排除论证）；`call 0x7C978A` 的字节命中总数 336。
- 该 `vt` 的写点里没有析构路径写点；即便如此仍是**全枚举**后才下的判断（不是只查 ④ 那一处）。

**行结论：PASS**（五项全部成立，工程地址与字节如上，可逐条复核）

---

## 行 12/12 · `007BA380` — WWMouseClass::SetCoords

④ 原文：`WWMouseClass::slot14（vt=007F7B2C，槽 14 值=007BA380，COL=0080EC60 offset=0，RTTI=0084E638→.?AVWWMouseClass@@；装表点 007B8850 位于 007B8730 体内，entry 体外）`

### ① vt 与槽号 — 成立

| 读法 | 地址 | 字节 | 值 |
|---|---|---|---|
| `u32(vt-4)`（COL 守卫）| `007F7B28` | `60 EC 80 00` | `0080EC60` |
| `u32(vt + slot*4)` | `007F7B64` | `80 A3 7B 00` | `007BA380` |

- 槽号 `14`（④ 内两处写法一致：是）；`u32(vt+slot*4) == entry` → **是**。
- `vt` 是表起点（`u32(vt-4)` 为合规 COL）→ **是**。
- 我独立全扫 `.rdata/.data` 中值 == `007BA380` 的 dword：共 **1** 个 `(vt, slot)` 见证，④ 的 `(vt=007F7B2C, slot=14)` **是** 其中之一。

- 同 entry 的全部见证：

| vt | slot | COL | 表属类（TD）| COL.offset |
|---|---:|---|---|---:|
| `007F7B2C` | 14 | `0080EC60` | WWMouseClass | 0 |

### ② COL — 成立

- `u32(vt-4)` 字节 `60 EC 80 00` → `0080EC60`；④ 写 `0080EC60` → **一致**。
- COL 24 字节（sig / offset / cdOffset / pTD / pCHD / pSelf）：`00 00 00 00 00 00 00 00 00 00 00 00 38 E6 84 00 50 EC 80 00 00 00 00 00`
- `sig = 0` → **0，成立**（卡面要求 `COL.sig == 0`）。
- `offset = 0`（④ 写 `offset=0`）→ **一致**；`pTD = 0084E638`，`pCHD = 0080EC50`。

### ③ TD 与类名 — 成立

- `u32(COL+0xC)` 读出 `0084E638`；④ 写 RTTI=`0084E638` → **一致**（**绝对 VA**，不是 RVA）。
- TD 头部 8 字节 + `TD+8` 内联串字节：`94 95 7F 00 00 00 00 00 | 2E 3F 41 56 57 57 4D 6F 75 73 65 43 6C 61 73 73 40 40 00 00 00 00 00 00`
- `TD+8` 按**内联串**读得 `.?AVWWMouseClass@@`（不是指针解引用）→ 去修饰 **WWMouseClass**；④ 写的类名 `WWMouseClass` → **一致**。
- 行名类 = `WWMouseClass`，RTTI 类 = `WWMouseClass` → 类名**相同**。

### ④ 装表点与宿主 — 成立

- 装表点 `007B8850` 处字节 `C7 06 2C 7B 7F 00` → `mov dword ptr [esi], 0x7f7b2c`：目标为内存、立即数 == `vt` → **是**。
- 宿主 `007B8730` 头部字节 `8B 54 24 08 53 56 8B F1 8B 4C 24 0C 57 33 DB 83`；从宿主做 CFG 遍历（不跟 call）**111** 条指令，装表点在其中 → **在体内**。
- 宿主是独立函数起点：前有 ≥2 字节 `CC/90` 填充 → 是；被 `call rel32` 指向的处数 = **3**（00560D62、0056107A、006BDF1C）→ 两条独立锚点互证。
- 行 entry `007BA380` 自身的遍历体 5 条指令，**不含**该装表点 → ④ 的「entry 体外」**成立**（确认）。

### ⑤ ㉓（全写点枚举 + 排除 atexit / 删除析构器）— 成立

枚举 `vt=007F7B2C` 在 `.text` 里的全部写点（直接 `mov [mem], imm32` 字节定位 + 
`mov reg,imm32` 后紧接 `mov [mem],reg` 的寄存器中介形式；本镜像 `lea reg,[vt]` 中介形式实测 **0** 处）：

| 写点 | 指令 | 宿主 | 宿主在 atexit 超集 | 宿主形态 | initterm 表内 | ④ 用的 |
|---|---|---|---|---|---|---|
| `007B8850` | `mov dword ptr [esi], 0x7f7b2c` | `007B8730` | 否 | 构造器/普通函数 | 否 | **✔** |
| `007B88D9` | `mov dword ptr [esi], 0x7f7b2c` | `007B88D0` | 否 | 构造器/普通函数 | 否 |  |

- 共 **2** 个写点。④ 用的是 `007B8850`（宿主 `007B8730`）：不在 atexit 注册超集内、非删除析构器/基类析构器形态 → **㉓ 成立**。
- atexit 口径（本镜像实测）：`push imm32; call 0x7C978A` 严格形态 **68** 个；按「call 前 48 字节内的 `push imm32`」取**保守超集** **172** 个（超集用于「不在集合内」的排除论证）；`call 0x7C978A` 的字节命中总数 336。
- 该 `vt` 的写点里没有析构路径写点；即便如此仍是**全枚举**后才下的判断（不是只查 ④ 那一处）。

**行结论：PASS**（五项全部成立，工程地址与字节如上，可逐条复核）

---

## 专项一 · ④ 类名 ≠ 行名类（抽样 12 行中 6 行）

先给事实（全部字节实测）：

| entry | 行名类 | ④ 的表属类 | 该 entry 在同一镜像里的全部 `(vt, slot, 表属类)` | 行名类的表是否也持有该 entry |
|---|---|---|---|---|
| `0055A950` | LocomotionClass | FlyLocomotionClass | FlyLocomotionClass slot1；HoverLocomotionClass slot1；LocomotionClass slot1；MechLocomotionClass slot1；RocketLocomotionClass slot1；TunnelLocomotionClass slot1 | 是（`007EADF4、007EAEC0`） |
| `005C0FE0` | MPGameModeClass | MultiplayerBattle | MultiplayerBattle slot0 | 否（该名字在本镜像无 RTTI 表：`无表`） |
| `005CA6D0` | MPGameModeClass | MultiplayerSiege | MultiplayerSiege slot5 | 否（该名字在本镜像无 RTTI 表：`无表`） |
| `005CB440` | MPGameModeClass | UnholyAlliance | UnholyAlliance slot50 | 否（该名字在本镜像无 RTTI 表：`无表`） |
| `005D6540` | MPGameModeClass | MultiplayerBattle | MultiplayerBattle slot20；MultiplayerManBattle slot20；Megawealth slot20；MultiplayerSiege slot20；UnholyAlliance slot20；MultiplayerGameMode slot20 | 否（该名字在本镜像无 RTTI 表：`无表`） |
| `005D74A0` | MPGameModeClass | MultiplayerBattle | MultiplayerBattle slot34；FreeForAll slot34；MultiplayerManBattle slot34；Megawealth slot34；MultiplayerSiege slot34；UnholyAlliance slot34；MultiplayerGameMode slot34 | 否（该名字在本镜像无 RTTI 表：`无表`） |

**判断：这种情况下 ④ 里写哪个类名才不会误导？**

1. ④ 的命题是「**某张表的某个槽**装的是这个 entry」，所以类名必须是**那张表自己的类**（＝RTTI 实测类），否则与给出的 `vt/COL/RTTI` 三个字段自相矛盾。这一层 ④ 写对了：6 行的类名都等于 `TD+8` 去修饰结果。
2. 但「写对表属类」不等于「不会误导」。实测分两种：
   - **同一实现在另一张基类表里也有**（`0055A950`：行名类 `LocomotionClass` 的 `vt=007EAEC0` 直接读 `u32(0x7EAEC0+1*4)=0055A950`，同址，无须别名假设；`005D6540`/`005D74A0`：RTTI 名 `MultiplayerGameMode` 的表 `vt=007EED60`（COL=`00806F88`）直接读得 slot20=`005D6540`、slot34=`005D74A0`，同址——该 RTTI 名是否就是行名 `MPGameModeClass` 的别名，本审计不判，但「同一实现在另一张表里」本身是实测）。这时只写派生表（`FlyLocomotionClass::slot1`、`MultiplayerBattle::slot20/34`）会被读成「这是派生类的成员」，而实测是**同一实现被多张派生表共用**——方向恰好相反。
   - **行名类在本镜像根本没有 RTTI/表**（`MPGameModeClass`：全镜像搜不到 `.?AVMPGameModeClass@@`，连字符串 `MPGameModeClass` 都不存在；`005C0FE0`/`005CA6D0`/`005CB440` 的 entry 只出现在一张派生表里）。这时写行名类会给出**无法复核**的类名，反过来只写表属类又隐去了「行名类为何不同」这一点。
3. 因此不误导的写法是**双写 + 关系**：`<表属类>::slotN`（=RTTI 实测，可复核）**后面紧跟**一句「该槽亦/仅见于 <行名类> 的表：<vt>/<slot>」或「行名类在本镜像无 RTTI 表」。只写一个类名（无论哪个）都会在某一侧误导。
4. 另有一处与类名无关但同样会误导的事实：`005C0FE0` 本身是编译器生成的**标量删除析构器**（`push esi; mov esi,ecx; mov [esi],vt; call 0x5D5D20; test byte[esp+8],1; je; push esi; call 0x7C8B3D; ret 4`），它占的是 MSVC 虚表的**删除析构器槽（slot 0）**；④ 只写「MultiplayerBattle::slot0」，读者无从知道这一槽是析构器槽。这种行应在 ④ 里点明「该槽为删除析构器槽」。

**逐行表述判定**（不影响五项 PASS/FAIL，只判「表述是否恰当」）：

| entry | 表述 | 理由 |
|---|---|---|
| `00464AC0` | —（类名一致） | ④ 类名＝行名类，无歧义 |
| `0055A050` | —（类名一致） | ④ 类名＝行名类，无歧义 |
| `0055A950` | **不恰当** | ④ 写派生表 FlyLocomotionClass::slot1，而未写它同时是行名类 LocomotionClass::slot1（vt=007EAEC0）的同一实现；单独读会被误当成派生类的成员 |
| `00597D50` | —（类名一致） | ④ 类名＝行名类，无歧义 |
| `005C0FE0` | **不恰当** | ④ 未交代该 entry 是编译器生成的标量删除析构器、且槽 0 正是该类虚表的删除析构器槽；与行名类 MPGameModeClass 亦无 RTTI 支持的关联 |
| `005CA6D0` | **不恰当** | ④ 写 MultiplayerSiege::slot5，未说明行名类 MPGameModeClass 在该镜像无 RTTI/表可查，也未说明该表与行名类的关系 |
| `005CB440` | **不恰当** | ④ 写 UnholyAlliance::slot50，未说明行名类 MPGameModeClass 在该镜像无 RTTI/表可查 |
| `005D6540` | **不恰当** | ④ 写 MultiplayerBattle::slot20；同一实现（同址）也出现在 RTTI 名 MultiplayerGameMode 的 slot20（是否即行名类 MPGameModeClass 的别名，本审计不判）；只写派生表会被误当成 MultiplayerBattle 的成员 |
| `005D74A0` | **不恰当** | ④ 写 MultiplayerBattle::slot34；同一实现（同址）亦在 MultiplayerGameMode/FreeForAll/Megawealth/MultiplayerSiege/UnholyAlliance 的 slot34；未写基类那一侧 |
| `0073C5F0` | —（类名一致） | ④ 类名＝行名类，无歧义 |
| `007B9C30` | —（类名一致） | ④ 类名＝行名类，无歧义 |
| `007BA380` | —（类名一致） | ④ 类名＝行名类，无歧义 |

---

## 专项二 · 装表点宿主是 `initterm` 静态初始化函数（4 行）

执行器披露：`005519B0` / `0055B880` / `0055BAA0` / `006CF240` 的装表点宿主是 initterm 链上的静态初始化函数而非类构造器。我独立复核如下（这 4 行**不在**抽样 12 行内，按专项要求单独验）。

**先把 `_initterm` 从字节里认出来**：

- `0x7CBED3`：`push esi; mov esi,[esp+8]; cmp esi,[esp+0xc]; jae 0x7CBEEB; mov eax,[esi]; test eax,eax; je +4; call eax; add esi,4; jmp 0x7CBED8; pop esi; ret` —— 典型的 `_initterm(begin, end)`：遍历函数指针数组，非空即调用。
- 调用点（同一函数的尾部）：`0x7CBDBA push 0x815DBC` / `0x7CBDBF push 0x815DA8` / `0x7CBDC4 call 0x7CBED3`（区间 [0x815DA8, 0x815DBC)）；`0x7CBDC9 push 0x815DA4` / `0x7CBDCE push 0x812000` / `0x7CBDD3 call 0x7CBED3`（区间 **[0x812000, 0x815DA4)**，3 945 项）。

| entry | 装表点 | 宿主 | 宿主在初始化表中的位置 | 存储目标 | 目标所在节 | ④「全局对象」是否成立 |
|---|---|---|---|---|---|---|
| `005519B0` | `004A8660` | `004A8630` | `00812D20`（第 840 项）| `reg-loaded-static 008A0360` | `.data` | **是**（模块静态地址） |
| `0055B880` | `0040CBAC` | `0040CB80` | `00812130`（第 76 项）| `absolute 0087F778` | `.data` | **是**（模块静态地址） |
| `0055BAA0` | `0040CBAC` | `0040CB80` | `00812130`（第 76 项）| `absolute 0087F778` | `.data` | **是**（模块静态地址） |
| `006CF240` | `006CF0C8` | `006CF070` | `00814E10`（第 2948 项）| `absolute 00B0C110` | `.data` | **是**（模块静态地址） |

逐条要点：

- `005519B0`（MapClass::AddObject）：装表点 `004A8660` = `mov dword ptr [eax - 8], 0x7e6060`，字节 `C7 40 F8 60 60 7E 00`；从宿主 `004A8630` 的 CFG 遍历可达（体内 19 条指令），宿主头 `B8 68 03 8A 00 BA 05 00 00 00 33 C9 89 48 FC 89`；宿主地址本身作为 dword 出现在 `00812D20`，落在 initterm 表区间内 → **装表点确在 initterm 回调函数体内**。存储目标是 `reg-loaded-static 008A0360`（模块静态，.data），即写的是全局对象/全局对象数组，不是 `this`。
- `0055B880`（MapClass::PointerGotInvalid）：装表点 `0040CBAC` = `mov dword ptr [0x87f778], 0x7e18fc`，字节 `C7 05 78 F7 87 00 FC 18 7E 00`；从宿主 `0040CB80` 的 CFG 遍历可达（体内 12 条指令），宿主头 `33 C0 68 C0 CB 40 00 A3 7C F7 87 00 A3 80 F7 87`；宿主地址本身作为 dword 出现在 `00812130`，落在 initterm 表区间内 → **装表点确在 initterm 回调函数体内**。存储目标是 `absolute 0087F778`（模块静态，.data），即写的是全局对象/全局对象数组，不是 `this`。
- `0055BAA0`（MapClass::AddObject）：装表点 `0040CBAC` = `mov dword ptr [0x87f778], 0x7e18fc`，字节 `C7 05 78 F7 87 00 FC 18 7E 00`；从宿主 `0040CB80` 的 CFG 遍历可达（体内 12 条指令），宿主头 `33 C0 68 C0 CB 40 00 A3 7C F7 87 00 A3 80 F7 87`；宿主地址本身作为 dword 出现在 `00812130`，落在 initterm 表区间内 → **装表点确在 initterm 回调函数体内**。存储目标是 `absolute 0087F778`（模块静态，.data），即写的是全局对象/全局对象数组，不是 `this`。
- `006CF240`（SwizzleManager::Here_I_Am）：装表点 `006CF0C8` = `mov dword ptr [0xb0c110], 0x7f4108`，字节 `C7 05 10 C1 B0 00 08 41 7F 00`；从宿主 `006CF070` 的 CFG 遍历可达（体内 21 条指令），宿主头 `6A 00 6A 00 B9 14 C1 B0 00 E8 72 08 00 00 6A 00`；宿主地址本身作为 dword 出现在 `00814E10`，落在 initterm 表区间内 → **装表点确在 initterm 回调函数体内**。存储目标是 `absolute 00B0C110`（模块静态，.data），即写的是全局对象/全局对象数组，不是 `this`。

**专项二结论**：4 行全部独立确认——装表点落在 initterm 回调体内，且 `vt` 被写到 .data 的模块静态对象上；其中 `005519B0` 是 5 个一组的全局对象数组（宿主 `004A8630`：`mov eax,0x8A0368`，循环 `mov [eax-8],vt; add eax,0x18; dec edx; jne`），存储目标 `0x8A0360` 起、每 0x18 一件。Lead 的「由 initterm 写虚表比构造器更直接」裁定与字节一致；**但注意**：这 4 行的宿主不是类构造器，④ 句仍写「位于 <宿主 entry> 体内」而未标明其身份是静态初始化回调，措辞上同样应补一句。

---

## 附注 · 不属于五项判定、但审计中撞见的两点

1. `005C0FE0`（行名 `MPGameModeClass::MPBattleClass`）的字节是**编译器生成的标量删除析构器**，不是手写虚函数：`push esi; mov esi,ecx; mov [esi],0x7EE184; call 0x5D5D20; test byte[esp+8],1; je +9; push esi; call 0x7C8B3D; ret 4`。④ 的五项仍然成立（槽 0 的值确实是它、装表点在构造器里），但「活表槽位见证」对这类槽的含义只是「析构器槽被装表」，不是「某业务虚函数被派发」。
2. `0055A950`（行名 `LocomotionClass::AddRef`）的字节是 `mov eax,[esp+4]; mov edx,[0xABCD3C]; add eax,0x14; inc edx; push eax; mov [0xABCD3C],edx; call dword ptr [0x7E11C8]; ret 4` —— 形态更像「全局计数 + 间接调用」，不像典型 `AddRef`。④ 只证明它占着 `FlyLocomotionClass`/`LocomotionClass` 的 slot 1，**不证明**它就是 AddRef；名字是否成立属既有 `[已证]` 的范围，本审计不改判，只把看见的字节记在这里。

---

## 附 · 复核方式

```bash
cd R4_FILL_AUDIT/scripts
python audit.py      # 逐行取数，落 audit.json
python anchors.py    # 宿主 call-xref 独立锚点 + lea 中介枚举性检查
python render.py     # 生成本文件与 verdict.tsv
```

`reib.py` 是本次审计自写的取数库：PE 解析（pefile）、就地解码（capstone）、表起点回溯、COL/TD 读取、`mov [mem],imm32` 全写点枚举、CFG 遍历定界、initterm 表与 atexit 集合的字节级识别。**未** import 执行器的 `fill.py`，**未**读取 `evidence/ROW_*.txt`。
