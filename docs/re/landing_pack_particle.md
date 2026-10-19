# 落地包 · Particle / ParticleSystem 迷雾绘制剔除（M-9 / landing_pack_particle）

> 归属链状态：**已定谳（A-15 读取点实证 + Lead 逐字节复核 11/11）**——**A-4 版本即最终版本，偏移无需修改**。最终语义：`+0xE0=TechnoClass* Owner`、`+0xFC=HouseClass* OwnerHouse`、`+0x124=ParticleSystem*`、坐标在 `+0x9C`（`>>8` 得格）。（与 Lead 0x62DE54 `mov [esi+0xE0],ebx` 空参写 0 的指针语义一致。）

### 0.0 若定谳反转需改动的行（A-15 改判 A-14 语义时必改）

> 【已作废·存档】A-15 定谳为 A-4 语义，本表仅存档，勿执行

> **反转语义（A-14 / `[v1.5.24]`）**：`+0xFC` = `TechnoClass* Owner`（House 走 `+0x21C`）、`+0xE0` = `CoordStruct CenterCoords`（`>>8` 得格，**不是** Owner）。  
> **暂定语义（A-4 / `[v1.5.12]` / 本文现稿）**：`+0xFC` = `HouseClass* OwnerHouse`、`+0xE0` = `TechnoClass* Owner`。  
> 下表「行号」为**本节写入后**的文档行号（校验基准：`grep -n` 本文）；节号稳定，改时以节号 + 引文为准。**只改语义列与谓词取值路径，不改字节地址本身**（`0x0062DD9A`/`0x0062DE37`/`0x0062DE54` 三条写点指令与编码不变）。

| # | 节号 | 行号 | 现写法（A-4 暂定） | 反转后应改为（A-14） | 类别 |
|---|---|---|---|---|---|
| 1 | §0 红线 | **L54** | 「绝不写 … 坐标 / Owner」中 Owner 与坐标并列 | 若 `+0xE0` 是坐标，此处仍禁止写（表述可保留），无需改行为 | 措辞 |
| 2 | §1.5 字段图 | **L131** | `+0xE0  TechnoClass* Owner` | `+0xE0  CoordStruct CenterCoords` | 字段图 |
| 3 | §1.5 字段图 | **L132** | `+0xFC  HouseClass*  OwnerHouse` | `+0xFC  TechnoClass* Owner` | 字段图 |
| 4 | §1.5 写点表 | **L138** | `0x0062DD9A` 语义列 `PSys ctor 写 OwnerHouse` | `PSys ctor 写 Owner(Techno)` | 写点表 |
| 5 | §1.5 写点表 | **L139** | `0x0062DE37` 语义列 `PSys ctor 写 Owner（非空）` | `PSys ctor 写 CenterCoords（非空路径）` | 写点表 |
| 6 | §1.5 写点表 | **L140** | `0x0062DE54` 语义列 `PSys ctor 写 Owner=NULL` | `PSys ctor 写 CenterCoords=0` | 写点表 |
| 7 | §1.5 链注 | **L143** | 「Techno→House `Techno+0x21C`」标为 fallback | 升为**唯一** House 来源（`+0xFC` 不再是 House） | 链注 |
| 8 | §2.1 约束 | **L184** | `IsHousePlayerOrAlly` 同款（`House+0x30`/`+0x5788`） | 不变（拿到 House 后仍同款） | — |
| 9 | §2.2 谓词 | **L209** | `ShouldDrawParticle` 头注释 `+0xFC / +0xE0→+0x21C` | `+0xFC→+0x21C`（Owner→House）；`+0xE0` 坐标不参与归属 | 谓词注释 |
| 10 | §2.2 谓词 | **L218–L221** | `pHouse = *(pSys+0xFC)` + `*(pSys+0xE0)` fallback | `pTech = *(pSys+0xFC); pHouse = *(pTech+0x21C)`（**删除 `+0xE0` 归属分支**） | 谓词代码 |
| 11 | §2.2 谓词 | **L231** | `ShouldDrawParticleSystem` 头注释 `+0xFC / +0xE0` | 同 #9 | 谓词注释 |
| 12 | §2.2 谓词 | **L237–L240** | `ShouldDrawParticleSystem` 内同款链 | 同 #10 | 谓词代码 |
| 13 | §6.2 合规表 | **L349** | 「只读 `+0x9C/+0xA0/+0x124/+0xE0/+0xFC`」 | 字段清单可保留（仍只读）；若需注明语义则 `+0xE0` 标坐标 | 合规表 |
| 14 | §6.3 禁止 | **L361** | 「`+0xE0/+0xFC` Owner」 | 「`+0xE0` 坐标 / `+0xFC` Owner」 | 禁止清单 |
| 15 | §7 执行表 | **L383（P7）** | 谓词行 | 伪码按 #9–#12 换路径；验收重验偏移语义 | 执行表 |
| 16 | §7 执行表 | **L392（P16）** | 归属正确性 | 用例不变；断点应看 `*(Owner+0x21C)` 而非 `*(PSys+0xFC)` | 执行表 |
| 17 | §8 风险 | **L416（R3）** | 无主粒子 | `pSys==NULL` 判定不变；若 `+0xE0` 为坐标，「无主」识别键需复核 | 风险表 |

> **不在反转面**（两种语义下均不变，勿误改）：`+0x124` 父 PSys 指针、`+0x9C/+0xA0` Location、`+0xD4/+0xD8` TargetCoords、`House+0x30` 索引、`House+0x5788` 盟友掩码、`IsHousePlayerOrAlly` / `IsLeptonInPlayerVision` 本体、槽 69 地址与原 DWORD、`EnableParticleFog` 开关与遥测字段。

> **交付对象**：ZCode（照表执行 + 真机验证，不做静态推理）  
> **产物路径**：`docs/re/landing_pack_particle.md`  
> **工作副本**：`out/re_work/landing_particle/**`（取证脚本与输出）  
> **目标二进制**：`ra2youli/gamemd.exe`（尤里的复仇 1.001），ImageBase `0x00400000`  
> **本轮实测 MD5**：`4f37486e5b0dbe2ae5f45aeee0f98367` [实证]（`out/re_work/landing_particle/verify_slots.py`）  
> **警告**：`particle_fog_owner_evidence.md` 头部记 MD5 `1011CE1B58C9B9BA...`（截断/可能过期）。**以本轮实测 MD5 为准**；若 ZCode 现场 MD5 不一致，先停手回报，禁止硬套字节。  
> 【W3 勘误 · W3-A6/ISSUE-OUTDATED-MD5-1011CE1B】改前：1011CE1B58C9B9BA；改后：4F37486E5B0DBE2AE5F45AEEE0F98367；依据：ra2youli/gamemd.exe; doc_consistency_fix_list.md:64；分级：P2
> **证据图例**：`[实证]` = 本轮对 `gamemd.exe` 字节/反汇编复核；`[前证]` = 既有深潜文档已实证、本轮抽查一致；`[待实测]` = 需 ZCode 真机验证后才能标 PASS。

---

## 0. 一句话范围

在 **`ra2render/blitter_hooks.cpp` 的 `FogHooks::` 体系内**新增两个虚表槽 69 钩子：

| 目标 | 入口 VA | 槽 69 条目 VA | 状态 |
|---|---|---|---|
| `ParticleClass::Draw` | `0x0062CEC0` | **`0x007EFA68`** | 未装 → 本包新增 |
| `ParticleSystemClass::Draw` | `0x0062E280` | **`0x007EFCB0`** | 未装 → 本包新增 |

**不碰**已装的 Unit / Infantry / Aircraft / Building / Bullet 五个槽 69。  
**开关**：`[FogOfWar] EnableParticleFog`，**默认 0**（保守，验收时显式置 1）。  
**红线**：只拦 `Draw`，绝不写 Update / AI / 寿命 / 坐标 / Owner / `IsCellShrouded`。

---

## 1. 字节级实证（槽地址 / 原虚表 DWORD / 新入口 / trampoline）

### 1.1 虚表槽 69 条目（`.rdata`，DWORD 函数指针）[实证]

| 槽 | 类 | 虚表基址 | 槽 69 条目 VA | 文件偏移 | 节 | **原字节（LE，4B）/ 原虚表 DWORD** | 新入口（本包） |
|---|---|---|---|---|---|---|---|
| 69 (`+0x114`) | ParticleClass | `0x007EF954` | **`0x007EFA68`** | `0x003EFA68` | `.rdata` | **`C0 CE 62 00`** → `0x0062CEC0` | `FogHooks::Hook_Particle_Draw` |
| 69 (`+0x114`) | ParticleSystemClass | `0x007EFB9C` | **`0x007EFCB0`** | `0x003EFCB0` | `.rdata` | **`80 E2 62 00`** → `0x0062E280` | `FogHooks::Hook_ParticleSystem_Draw` |
| 69（对照，**禁止重装**） | BulletClass | `0x007E46E4` | `0x007E47F8` | `0x003E47F8` | `.rdata` | `00 46 80 90`（BE 书写）→ `0x00468090` | 已装 `Hook_Bullet_Draw` |
| 69（对照，禁止重装） | UnitClass | — | `0x007F5D84` | `0x003F5D84` | `.rdata` | `00 73 CE C0`（BE 书写） | 已装 |
| 69（对照，禁止重装） | InfantryClass | — | `0x007EB16C` | `0x003EB16C` | `.rdata` | `00 51 8F 90`（BE 书写） | 已装 |
| 69（对照，禁止重装） | AircraftClass | — | `0x007E23B8` | `0x003E23B8` | `.rdata` | `00 41 44 B0`（BE 书写） | 已装 |
| 69（对照，禁止重装） | BuildingClass | — | `0x007E3FD0` | `0x003E3FD0` | `.rdata` | `00 43 D2 90`（BE 书写） | 已装 |

> 小端序写入：`PatchVTablePointer(0x007EFA68, newFn, …)` 即把 4 字节 `C0 CE 62 00` 改为新入口地址。
>
> **【F-04 订正 · 2026-09-26 · task-14】** 改前：本表「原虚表 DWORD」列把 Particle/PSys 两行写成 **`00 62 CE C0` / `00 62 E2 80`（大端书写）**，而同文 `:74,378,415,416` 又写 LE `C0 CE 62 00` / `80 E2 62 00` → **包内自相矛盾**。改后：统一**小端字节序**（`C0 CE 62 00` / `80 E2 62 00`），列头改「原字节（LE）」；对照行（Bullet/Unit/Inf/Air/Bld）保持原 BE 书写并**显式标注（BE 书写）**以示区别。依据：`gamemd.exe` 机读实测 `0x007EFA68 = C0 CE 62 00`、`0x007EFCB0 = 80 E2 62 00` `[实证]`（`docs/re/anchor_claims.txt:72-73`；本包 `:415,:416` 一致）。**风险**：把 `00 62 CE C0` 当字节序列照抄将写入 `0xC0CE6200`（错误入口 → 崩）。
> 【W3 勘误 · W3-A6/ISSUE-PARTICLE-BE-BYTES】改前：00 62 CE C0；改后：C0 CE 62 00 / 80 E2 62 00 (小端 LE)；依据：errata_sync_master_table.md:23 (R-E08); FIXPACK_F01-F13_report.md F-04；分级：P0

### 1.2 被钩函数入口机器码 [实证]

```
ParticleClass::Draw @ 0x0062CEC0
  83 ec 24          sub  esp, 0x24
  53 55 56 57       push ebx/ebp/esi/edi
  8b f9             mov  edi, ecx          ; edi = this
  ...                                     ; 981 字节，两处 ret 8：0x62D029 / 0x62D292

ParticleSystemClass::Draw @ 0x0062E280
  83 ec 08          sub  esp, 8
  56 57             push esi/edi
  8b f9             mov  edi, ecx          ; edi = this
  8b 87 ac 00 00 00 mov  eax, [edi+0xAC]   ; Type
  8a 88 0c 03 00 00 mov  cl,  [eax+0x30C]  ; Type->Laser
  84 c9             test cl, cl
  0f 84 db 00 00 00 je   0x0062E376        ; Laser==0 → 直接 ret 8
  ...
  0x0062E376: 5f 5e 83 c4 08 c2 08 00     ; 唯一出口 ret 8
```

### 1.3 原版迷雾门（双失效，不可依赖）[实证 + 前证]

```
0x0062CF23  8b 15 30 b2 a8 00    mov edx, [0x00A8B230]   ; ScenarioClass::Instance
0x0062CF2B  f6 c4 10             test ah, 0x10           ; Flags & 0x1000
0x0062CF2E  74 35                je  0x0062CF65          ; L3 已强制清 0x1000 → 恒跳过
0x0062CF58  e8 83 96 f5 ff       call 0x005865E0         ; IsCellShrouded
0x0062CF5F  0f 85 26 03 00 00    jne 0x0062D28B          ; 黑雾 → Exit2
```

`MapClass::IsCellShrouded @ 0x005865E0` = **`32 C0 C2 04 00`**（`xor al,al; ret 4`）——发行版空桩，恒返回 0。  
**结论**：原版迷雾门永久失效，必须外部钩子 + `s_visionGrid` 自建判定。[实证]

### 1.4 Trampoline

**不需要代码跳板。** 本包是 **虚表 DWORD 覆写**（与现有 `Hook_Bullet_Draw` 同模式）：

- 保存原 DWORD 到 `g_pOrigParticleDraw` / `g_pOrigParticleSystemDraw`；
- 钩子内部条件不满足时 **直接 `return`**（等价 `ret 8`，callee 清栈，签名一致）；
- 需要放行时 `g_pOrigXxxDraw(pThis, pLocation, pBounds)` 调原函数。

与 `InstallCellClassDrawHook`（5 字节 inline + 跳板）**不同**——本包 **禁止** 对 `0x0062CEC0` / `0x0062E280` 做 inline patch。  
PE 存在 `.detour` 节（**VA `0x00B93000`**，RVA `0x00793000`，RawPtr `0x497000`，RawSize `0x3000`）：**本包不写 `.detour`**（对齐 net_sync 节约约束）。
> **【F-08 订正 · 2026-09-26 · task-14】** 改前：`.detour` 节 `VA=0x00793000`（把 **RVA 当 VA**，且 `0x00793000` 不落在任何节区——`.rdata` 起 `0x7E1000`）；改后：`VA 0x00B93000`（RVA `0x793000`）。依据：PE 节表机读实测 `.detour` VA `0x00B93000` / RVA `0x00793000` `[实证]`（`tools/verify_anchors.py` 基线审计第 3 行「`.detour` 原生签名 @ VA 0xb93000」）；同口径见 `pending_execution_master_table.md:22`、`landing_pack_net_fix.md:35`。

### 1.5 归属链字段写点（粒子 → 阵营）[实证 + 前证]

```
ParticleClass (sizeof 0x138)
  +0x9C  CoordStruct Location        (Lepton，>>8 = 格)
  +0xAC  ParticleTypeClass* Type
  +0x124 ParticleSystemClass* Parent ──┐
                                       │
ParticleSystemClass (sizeof 0x100)     │
  +0x9C  CoordStruct Location (源)     │
  +0xAC  ParticleSystemTypeClass* Type │
  +0xD4  CoordStruct TargetCoords      │
  +0xE0  TechnoClass* Owner  ──────────┤
  +0xFC  HouseClass*  OwnerHouse ──────┘
```

| 字节 | 指令 | 语义 |
|---|---|---|
| `0x0062B721`: `89 8E 24 01 00 00` | `mov [esi+0x124], ecx` | Particle ctor 写父 PSys [实证] |
| `0x0062DD9A`: `89 86 FC 00 00 00` | `mov [esi+0xFC], eax` | PSys ctor 写 OwnerHouse [实证] |
| `0x0062DE37`: `89 8E E0 00 00 00` | `mov [esi+0xE0], ecx` | PSys ctor 写 Owner（非空）[实证] |
| `0x0062DE54`: `89 9E E0 00 00 00` | `mov [esi+0xE0], ebx` | PSys ctor 写 Owner=NULL [实证] |

`ParticleClass::ctor 0x0062B5E0` 的 9 处调用点全部在 PSys 内部 → `+0x124` 恒指向合法父容器（无野粒子）[前证]。  
House 索引 `House+0x30`，盟军掩码 `House+0x5788`，Techno→House `Techno+0x21C`（与 `ShouldDrawBullet` 同源）[前证]。

---

## 1.6 定谳后 5 分钟切换对照表（给 ZCode）

> **A-15 已定谳为 A-4 语义，无需切换**。本表与 §0.0 一并仅存档备查；执行一律走 §7 执行表（A-4 路径）。  
> A-15 读取点实证一旦定谳，按本表**只换归属链取值路径**，其余（槽 69、开关、遥测、回滚、坐标迷雾判定）一律不动。目标：**5 分钟内完成语义切换 + 编译 + 一项针对性验证**。  
> 两版差异只在「House 指针从哪来」；`IsHousePlayerOrAlly` / `IsLeptonInPlayerVision` / 钩子体 / 安装卸载 **零改动**。

| 语义 | 取值路径（A-4 暂定） | 取值路径（A-15 若反转为 A-14） | 改哪几行 | 验证 |
|---|---|---|---|---|
| **Owner 指针** | `PSys+0xE0` → `TechnoClass*`（`0x0062DE37`/`0x0062DE54` 写点） | `PSys+0xFC` → `TechnoClass*`（`0x0062DD9A` 写点） | §1.5 字段图两行 + 写点表语义列（§0.0 #2–#6）；§2.2 两处读 `+0xE0`/`+0xFC` 的注释与代码 | 断点 `ShouldDrawParticle`：读出的对象 vtable 应落在 Techno 区（如 Unit `0x007F5D84` 起） |
| **OwnerHouse** | 直取 `*(PSys+0xFC)`；空则 `pTech=*(PSys+0xE0); *(pTech+0x21C)` | **无直取 House**：`pTech=*(PSys+0xFC); pHouse=*(pTech+0x21C)`；`+0xE0` 不参与归属 | §2.2 `ShouldDrawParticle` / `ShouldDrawParticleSystem` 各 ~4 行（§0.0 #10/#12） | 己方开火：`pHouse==pPlayer` 恒真（P16）；盟友掩码 `House+0x5788` 命中 |
| **盟友判定入口** | `IsHousePlayerOrAlly(pHouse, pPlayer)`：`House+0x30` 索引 + `Player+0x5788` 掩码 | **不变**（拿到 House 后同款调用） | 无 | 盟友开火零误杀（P16 反向：`particlesRendered` 增、剔除不增） |
| **迷雾谓词参数** | Particle：`+0x9C/+0xA0` Location；PSys：源 `+0x9C/+0xA0` + 目标 `+0xD4/+0xD8`（两端 OR） | **不变**（坐标字段无争议）。若 A-15 认 `+0xE0` 为 CenterCoords，仅可作可选中心点，**禁止替代** Location | §2.2 注释一句（§0.0 #9/#11）；勿改 `IsLeptonInPlayerVision` | P15：敌方尾烟进黑雾消失、`particlesCulledByFog>0`；P17：Laser 两端 OR |
| **执行表 P 步骤** | **P7** 谓词（A-4 伪码）；**P16** 归属正确性 | 同左步骤号，仅换谓词内部路径；P7 编译后重跑 P16 | P7 伪码体；P16 断点描述（§0.0 #15/#16） | P14 开关 0 直通零剔除；P15 开关 1 剔除生效；P16 零误杀；P19 硬回滚虚表 DWORD 复原 |

**5 分钟操作序列（定谳反转时）**：

1. **0–1 min**：改 §2.2 两处谓词的 House 解析 4+4 行（删 `+0xE0` 归属分支；`+0xFC` 当 Owner 走 `+0x21C`）。
2. **1–2 min**：同步改 §1.5 字段图与写点表语义列（字节地址不动）；§2.2/§2.3 注释对齐。
3. **2–3 min**：编译 `ra2render/build.bat`（0 error）；`LoadConfig` 日志确认 `EnableParticleFog` 读入。
4. **3–4 min**：跑 P16（己方/盟友开火零误杀）+ P15 一例（敌方进黑雾剔除）。
5. **4–5 min**：跑 P14（开关 0 直通）与 P19（`RemoveVTableHooks` 后 `0x007EFA68`=`C0 CE 62 00`、`0x007EFCB0`=`80 E2 62 00`）。【F-04 订正：改前 `0x007EFA68`=`00 62 CE C0`（BE 书写），与同文 `:378,:416` 的 LE 口径矛盾】

> **回退**：若 A-15 后续再次改判，按本表反向替换回 A-4 路径即可，无字节级残留（本包无 inline patch / 无 trampoline / 不写 `.detour`）。

---

## 2. 合并策略（禁止重复安装槽 69）

### 2.1 硬性约束

1. **槽 69 统一命名空间**：所有安装/卸载只写在 `ra2render/blitter_hooks.cpp` 的 `InstallVTableHooks()` / `RemoveVTableHooks()`，**禁止**新开独立 install 函数或第二个 DLL 入口再次改同一槽。[对齐 `HOOK_POINT_MATRIX.md` §3.2]
2. **禁止重复安装**：下列 5 个已装槽 69 **一个字节都不许再写**：
   - `0x007F5D84` Unit · `0x007EB16C` Infantry · `0x007E23B8` Aircraft · `0x007E3FD0` Building · `0x007E47F8` Bullet
3. **本包只新增 2 个未装槽**：`0x007EFA68`、`0x007EFCB0`。
4. **幂等安装**：`PatchVTablePointer` 前检查 `g_pOrigParticleDraw == nullptr`；已非空则视为已装，**跳过**并打日志，避免二次覆盖丢失原函数指针。
5. **共用谓词**：`ShouldDrawParticle` / `ShouldDrawParticleSystem` 与现有 `ShouldDrawMobileObject` / `ShouldDrawBullet` 共用：
   - `UpdateVisionGrid()`（帧 Token 网格）
   - `s_visionGrid[cellY*512+cellX] == s_visionToken`
   - `IsHousePlayerOrAlly` 同款（`House+0x30` / `+0x5788`）
   - 可选 Psychic Sensor（`Cell+0xAC`）
6. **谓词幂等**：同一对象同帧可能经 `0x6D8DB0` 与 `0x6D97D0/0x6D9920` 两条绘制路径各进一次 Draw——谓词是纯函数（只读），结果稳定，重复调用安全。

### 2.2 谓词伪码（写入 `blitter_hooks.cpp`，风格对齐 `ShouldDrawBullet`）

```cpp
// 通用：House 是否己方/盟友（与 ShouldDrawMobileObject 第 3–4 步同构）
static inline bool IsHousePlayerOrAlly(void *pHouse, void *pPlayer) {
    if (!pHouse || !pPlayer) return false;
    if (pHouse == pPlayer) return true;
    int idx = *(int*)((uint8_t*)pHouse + 0x30);
    uint32_t allies = *(uint32_t*)((uint8_t*)pPlayer + 0x5788);
    return idx >= 0 && idx < 32 && ((1u << idx) & allies) != 0;
}

// 通用：Lepton → 格 → s_visionGrid（含 Psychic Sensor）
static inline bool IsLeptonInPlayerVision(int locX, int locY, void *pPlayer) {
    int cx = locX >> 8, cy = locY >> 8;
    if (cx < 0 || cx >= 512 || cy < 0 || cy >= 512) return false;
    if (s_visionGrid[cy * 512 + cx] == s_visionToken) return true;
    // …Psychic Sensor 同 ShouldDrawMobileObject 第 7 步…
    return false;
}

// Particle：+0x124 → 父 PSys → +0xFC / +0xE0→+0x21C
static bool ShouldDrawParticle(void *p) {
    if (!p) return true;
    __try {
        void *pPlayer = *(void**)ADDR_HOUSE_PLAYER;
        if (!pPlayer) return true;
        void *pSys = *(void**)((uintptr_t)p + 0x124);
        void *pHouse = nullptr;
        if (pSys) {
            pHouse = *(void**)((uintptr_t)pSys + 0xFC);
            if (!pHouse) {
                void *pTech = *(void**)((uintptr_t)pSys + 0xE0);
                if (pTech) pHouse = *(void**)((uintptr_t)pTech + 0x21C);
            }
        }
        if (IsHousePlayerOrAlly(pHouse, pPlayer)) return true;   // 己方/盟友恒画
        int lx = *(int*)((uint8_t*)p + 0x9C);
        int ly = *(int*)((uint8_t*)p + 0xA0);
        return IsLeptonInPlayerVision(lx, ly, pPlayer);          // 敌方/无主：查直视
    } __except (EXCEPTION_EXECUTE_HANDLER) { return true; }      // 异常放行，防崩溃
}

// ParticleSystem（含 Laser 线段）：+0xFC / +0xE0；激光两端 OR
static bool ShouldDrawParticleSystem(void *p) {
    if (!p) return true;
    __try {
        void *pPlayer = *(void**)ADDR_HOUSE_PLAYER;
        if (!pPlayer) return true;
        void *pHouse = *(void**)((uintptr_t)p + 0xFC);
        if (!pHouse) {
            void *pTech = *(void**)((uintptr_t)p + 0xE0);
            if (pTech) pHouse = *(void**)((uintptr_t)pTech + 0x21C);
        }
        if (IsHousePlayerOrAlly(pHouse, pPlayer)) return true;
        int sx = *(int*)((uint8_t*)p + 0x9C),  sy = *(int*)((uint8_t*)p + 0xA0);
        int tx = *(int*)((uint8_t*)p + 0xD4),  ty = *(int*)((uint8_t*)p + 0xD8);
        return IsLeptonInPlayerVision(sx, sy, pPlayer)
            || IsLeptonInPlayerVision(tx, ty, pPlayer);          // 两端 OR
    } __except (EXCEPTION_EXECUTE_HANDLER) { return true; }
}
```

### 2.3 钩子体（合并进 `FogHooks::`，与 `Hook_Bullet_Draw` 并排）

```cpp
void __thiscall FogHooks::Hook_Particle_Draw(void *pLocation, void *pBounds) {
    void *pThis = this;
    if (g_enableParticleFog && !ShouldDrawParticle(pThis)) {
        g_telemetry.particlesCulledByFog++;
        return;                       // 等价 ret 8，跳过 Blit
    }
    g_telemetry.particlesRendered++;
    if (g_pOrigParticleDraw) g_pOrigParticleDraw(pThis, pLocation, pBounds);
}

void __thiscall FogHooks::Hook_ParticleSystem_Draw(void *pLocation, void *pBounds) {
    void *pThis = this;
    if (g_enableParticleFog && !ShouldDrawParticleSystem(pThis)) {
        g_telemetry.particleSystemsCulledByFog++;
        return;
    }
    g_telemetry.particleSystemsRendered++;
    if (g_pOrigParticleSystemDraw) g_pOrigParticleSystemDraw(pThis, pLocation, pBounds);
}
```

> **与 Hook_Bullet_Draw 的关系**：同属 `FogHooks::`、同走 `s_visionGrid`、同在 `InstallVTableHooks()` 一并装/卸；**不是**把粒子逻辑塞进 `Hook_Bullet_Draw` 函数体，也**不是**给 Bullet 槽二次安装。Bullet 槽 `0x007E47F8` 保持现状。

---

## 3. 开关 `EnableParticleFog`

| 项 | 值 |
|---|---|
| INI 节/键 | `[FogOfWar] EnableParticleFog` |
| **默认值** | **`0`**（关闭 = 原版直通，零行为变化） |
| 代码变量 | `bool g_enableParticleFog = false;`（`ra2render.h` + `blitter_hooks.cpp`） |
| 读取点 | `LoadConfig()`，紧随 `EnableBulletFog` |
| 语义 | `0`：钩子仍安装，但直接放行原 Draw（遥测 `particlesRendered/particleSystemsRendered` 照常计）；`1`：启用敌方粒子/激光剔除 |
| 为何默认 0 | 对齐 `EnableMinimapFog` 保守策略：先合入、真机验收显式置 1，避免未验证特性默认改变画面 |

`ra2render.ini` 增补：

```ini
; L5 微粒/粒子系统迷雾剔除（M-9，默认关闭，验收时置 1）
; 敌方尾烟/火星/爆炸粒子与 Laser=yes 粒子系统的持续激光束按直视网格剔除
EnableParticleFog=0
```

---

## 4. 遥测计数

`ForgeTelemetry` 追加 4 个字段（`ra2render.h`，**只加不改序**，或统一在结构体尾部追加避免与已有日志偏移冲突）：

```cpp
uint64_t particlesCulledByFog;         // Particle 被剔除次数
uint64_t particlesRendered;            // Particle 放行次数（含开关关闭时）
uint64_t particleSystemsCulledByFog;   // ParticleSystem 被剔除次数
uint64_t particleSystemsRendered;      // ParticleSystem 放行次数
```

`CheckTelemetry()` 与 `RemoveVTableHooks()` 末行日志追加：

```
粒子剔除: %llu / 粒子渲染: %llu | 粒子系统剔除: %llu / 粒子系统渲染: %llu
```

**生效性断言（对齐 `EVIDENCE_STANDARD.md` v3）**：`EnableParticleFog=1` 时，验收场景（敌方 V3/无畏级尾烟或爆炸）下 **`particlesCulledByFog` 必须 > 0**，否则标 **UNVERIFIED**，禁止 PASS。

---

## 5. 回滚

| 层级 | 动作 | 效果 |
|---|---|---|
| **软回滚（推荐）** | `ra2render.ini` 置 `EnableParticleFog=0` | 钩子仍在但直通原 Draw，画面与原版一致；无需重启（若 `LoadConfig` 仅启动时读，则需重启——**与现有键行为一致**） |
| **硬回滚** | `RemoveVTableHooks()` 将 `0x007EFA68` / `0x007EFCB0` 写回 `g_pOrigParticleDraw` / `g_pOrigParticleSystemDraw`（即 `0x0062CEC0` / `0x0062E280`） | 与其它槽 69 同批卸载，日志打印遥测终值 |
| **事故回滚** | 卸载 DLL / 移除 `ra2render.dll` 注入 | 无 inline patch、无 trampoline、不写 `.detour` → 退出后内存无残留代码补丁 |

**幂等卸载**：`g_pOrigParticleDraw` 置 `nullptr` 后再次进入卸载分支自然跳过。

---

## 6. 只拦绘制、不写逻辑（对照 net_sync SAFE）

### 6.1 契约来源

`docs/re/net_sync_checksum.md`：

- 联机 = **确定性锁步**；任何本地立即生效的逻辑优化都会分叉。
- **Particle / ParticleSystem 的逻辑状态（寿命 / 位置 / Owner / Type）进 `CalculateChecksum` 与存档**（§3.1 类目）→ **只许改绘制参数，不许改寿命/位置/Owner 字段**。
- 绘制层（`radar_minimap_dots.md` / `fx_draw_chain.md`）标 **条件安全**：不进同步契约。

### 6.2 本包合规论证

| 检查项 | 本包行为 | 判定 |
|---|---|---|
| 拦截点 | 仅虚表槽 69 `Draw`（`ret 8` 语义早退） | **SAFE** |
| Update / AI | 未触碰 `ParticleClass::Update 0x0062CE40`、`ParticleSystemClass::AI 0x0062FD60`、`0x0062DF20`/`0x0062E070` | **SAFE** |
| 状态写入 | 钩子与谓词 **零写** 对象字段；只读 `+0x9C/+0xA0/+0x124/+0xE0/+0xFC` 等 | **SAFE** |
| 寿命推进 | 粒子寿命 `dec [esi+0x128]` 在 Update，不在 Draw；**不像 EBolt 在 DrawAll 衰减** → 早退不会造成「永生粒子」 | **SAFE** |
| `IsCellShrouded` / `IsShrouded` / `RevealArea` | 未改（且 `0x5865E0` 本就是 stub） | **SAFE** |
| Checksum 影响 | 不改逻辑坐标 / RNG / Owner → `CurrentFrameCRC 0x0064DAB0` 与 `AbstractClass::CalculateChecksum` 输入不变 | **SAFE** |
| 存档 | 绘制钩不进 `.SAV` | **SAFE** |
| `.detour` 节 | 不写 | **SAFE** |
| 回放 / 联机两端 | 画面剔除是**本地视口**效果；两端可不同开（各自画面），逻辑帧仍一致 | **SAFE**（零 OOS） |

> **对照结论**：与已装的 `Hook_Bullet_Draw` / `Hook_Unit_Draw` 同属「绘制层 + 私有视野缓存」，落在 net_sync **可动**象限，**零同步风险**。

### 6.3 明确禁止（违者必回滚）

1. 禁止在谓词或钩子里写 `+0x128` 寿命、`+0x9C` 坐标、`+0xE0/+0xFC` Owner。
2. 禁止改 `0x0062CEC0` / `0x0062E280` 函数体内任何字节（inline patch）。
3. 禁止改 `IsCellShrouded 0x005865E0` / `IsShrouded 0x00487950` / `RevealArea*`。
4. 禁止在 Update/AI 路径限频或跳过（会改粒子寿命与伤害时序）。
5. 禁止二次安装已装的 5 个槽 69。

---

## 7. 给 ZCode 的执行表

> **归属链已定谳（A-15 读取点实证 + Lead 逐字节复核 11/11）**：按 **A-4 语义**落地（`+0xE0` Owner、`+0xFC` OwnerHouse、`+0x124` 父 PSys、坐标 `+0x9C`）。§0.0 / §1.6 反转表**仅存档，勿执行**。
>
> **执行前置约束（违者回滚）**：
> 1. **槽 69 与既有 `Hook_Bullet_Draw` 合并安装、禁止重复挂载**：只写在 `InstallVTableHooks()` / `RemoveVTableHooks()`，与 Bullet 槽同批装/卸。已装 5 槽（Unit `0x007F5D84` / Inf `0x007EB16C` / Air `0x007E23B8` / Building `0x007E3FD0` / Bullet `0x007E47F8`）**一个字节都不许再写**；本包只新增 2 个未装槽。
> 2. **Particle 槽 69** `0x007EFA68` 原 DWORD **`C0 CE 62 00`**（→ `0x0062CEC0`）；**PSys 槽 69** `0x007EFCB0` 原 DWORD **`80 E2 62 00`**（→ `0x0062E280`）。
> 3. **开关** `EnableParticleFog` **默认 0**（验收时显式置 1）。
> 4. **遥测** `particlesCulledByFog` / `particleSystemsCulledByFog`（及对应 `particlesRendered` / `particleSystemsRendered`）。
> 5. **卸载还原**：写回原 DWORD（`C0 CE 62 00` / `80 E2 62 00`）；幂等 `g_pOrig*==nullptr` 后自然跳过。
> 6. **列**：步骤 → 地址 → 原字节 → 新字节 → 开关 → 回滚 → 验收；标注 `[实证]`/`[待实测]`。
>
> 执行顺序严格自上而下。每行完成后在「验收」列打勾或写实测值。  
> `[实证]` = 本轮字节已核；`[待实测]` = 真机验证后才能标 PASS。

| 步骤 | 地址 / 位置 | 原字节 / 原值 | 新字节 / 新值 | 开关 | 回滚 | 验收 | 标注 |
|---|---|---|---|---|---|---|---|
| **P0** 现场 MD5 核对 | `ra2youli/gamemd.exe` | — | 期望 `4f37486e5b0dbe2ae5f45aeee0f98367` | — | 不一致则 **停手回报** | `certutil -hashfile … MD5` 一致 | [实证] 本轮值 / [待实测] 现场 |
| **P1** 头文件常量 | `ra2render/ra2render.h` | 无 `ADDR_VTABLE_ENTRY_PARTICLE_*` | `#define ADDR_VTABLE_ENTRY_PARTICLE_DRAW 0x007EFA68`<br>`#define ADDR_VTABLE_ENTRY_PARSYS_DRAW   0x007EFCB0` | — | 删除宏 | 编译通过 | [实证] 地址 |
| **P2** 原函数指针 | `ra2render.h` + `blitter_hooks.cpp` | 无 | `FnDrawObject g_pOrigParticleDraw = nullptr;`<br>`FnDrawObject g_pOrigParticleSystemDraw = nullptr;` | — | 删除变量 | 编译通过 | [实证] 签名 `ret 8` |
| **P3** 开关变量 | `ra2render.h` / `blitter_hooks.cpp` | 无 | `bool g_enableParticleFog = false;` | 默认 **0** | 删除 | `LoadConfig` 能读到 | [实证] 规格 |
| **P4** INI 键 | `ra2render/ra2render.ini` `[FogOfWar]` | 无 | `EnableParticleFog=0` + 注释 | 默认 0 | 删除键 | 启动日志打印 `EnableParticleFog=false` | [实证] 规格 |
| **P5** 遥测字段 | `ra2render.h` `ForgeTelemetry` 尾部 | 10 字段 | +`particlesCulledByFog` `particlesRendered` `particleSystemsCulledByFog` `particleSystemsRendered` | — | 删字段 | 结构仍可初始化 `{0}` | [实证] 规格 |
| **P6** `LoadConfig` | `blitter_hooks.cpp` `LoadConfig()` | 无 Particle 键 | 读 `EnableParticleFog`→`g_enableParticleFog`，日志追加 | — | 删代码 | 日志含新键值 | [待实测] |
| **P7** 谓词 | `blitter_hooks.cpp`（`ShouldDrawBullet` 旁） | 无 | `IsHousePlayerOrAlly` / `IsLeptonInPlayerVision` / `ShouldDrawParticle` / `ShouldDrawParticleSystem`（§2.2，含 `__try/__except` 放行） | — | 删函数 | 编译通过；异常路径放行 | [实证] 偏移 / [待实测] 行为 |
| **P8** 钩子体 | `blitter_hooks.cpp` `FogHooks::` | 无 | `Hook_Particle_Draw` / `Hook_ParticleSystem_Draw`（§2.3） | `g_enableParticleFog` | 删函数 | 编译通过 | [实证] 模式同 `Hook_Bullet_Draw` |
| **P9** 头声明 | `ra2render.h` `class FogHooks` | 无 | 两个 `static void __thiscall Hook_*` 声明 | — | 删声明 | 编译通过 | [实证] 规格 |
| **P10** 安装 | `InstallVTableHooks()`，`hook13`(Bullet) 之后追加 `hook14/15`（**合并安装，禁止新开 install 函数/重复挂载**） | 不动 `hook1..13`；已装 5 槽（Unit/Inf/Air/Building/Bullet）**零写入** | `PatchVTablePointer(0x007EFA68, Hook_Particle_Draw)`：`C0 CE 62 00`→新入口<br>`PatchVTablePointer(0x007EFCB0, Hook_ParticleSystem_Draw)`：`80 E2 62 00`→新入口<br>**幂等**：`g_pOrig*!=nullptr` 则 skip 并打日志 | 始终安装；行为由开关决定 | 见 P11 | 日志：`原入口 0x0062CEC0 -> 新入口 …`；**且** Bullet/Unit/Inf/Air/Building 槽日志不重复出现 | [实证] 原 DWORD / [待实测] 安装日志 |
| **P11** 卸载 | `RemoveVTableHooks()`，`g_pOrigBulletDraw` 分支之后（与 Bullet 同批） | 槽内为钩子入口 | **写回原 DWORD**：`0x007EFA68`←`C0 CE 62 00`、`0x007EFCB0`←`80 E2 62 00`；随后 `g_pOrigParticleDraw/g_pOrigParticleSystemDraw = nullptr`（**幂等**：已空则跳过，二次卸载无异常） | — | 自身即回滚 | 卸载日志含粒子遥测；再启不崩溃；二次卸载无异常 | [实证] 原 DWORD / [待实测] 还原 |
| **P12** 遥测日志 | `CheckTelemetry()` + `RemoveVTableHooks` 末行 | 现有字段 | 追加 4 个计数打印 | — | 删格式串 | 末行可见新计数 | [待实测] |
| **P13** 编译 | `ra2render/build.bat` | — | 产出 `ra2render.dll` | — | 还原源码 | 0 error | [待实测] |
| **P14** 真机·开关 0 | `ra2render.ini` `EnableParticleFog=0` | — | 启动遭遇敌方粒子 | 0 | — | 敌方尾烟**仍可见**；`particlesCulledByFog==0`；无 `except.txt` | [待实测] |
| **P15** 真机·开关 1 | `EnableParticleFog=1` | — | 敌方 V3/无畏级开火进黑雾 | 1 | — | 黑雾内尾烟/弹道粒子消失；`particlesCulledByFog > 0`；己方尾烟恒可见 | [待实测] |
| **P16** 归属正确性 | 同上 | — | 己方/盟友开火 | 1 | — | 己方/盟友粒子**零误杀**（`particlesRendered` 增、剔除不增） | [待实测] |
| **P17** Laser PSys | 使用 `Laser=yes` 粒子系统武器 | — | 敌方激光进黑雾 | 1 | — | 两端皆不可见 → 光束消失；一端可见 → 仍画 | [待实测] |
| **P18** 确定性 | 联机/回放或 CRC 对照 | — | 两端同补丁或仅本地开 | 1 | — | 无 OOS；`CurrentFrameCRC` 与未装时一致（逻辑帧） | [待实测] |
| **P19** 硬回滚演练 | `RemoveVTableHooks` / 卸载 DLL | — | — | — | 写回原 DWORD | 虚表 DWORD 复原为 `C0 CE 62 00` / `80 E2 62 00`；游戏画面原版 | [待实测] |
| **P20** 崩溃零容忍 | 验收窗口 | — | — | — | — | `ra2youli/except.txt` 无新增；若 EIP 落 `0x54500000-0x545F0000`（ra2render）判实施方缺陷 | [待实测] |

### 7.1 执行表关键行（字节速查）

| 地址 | 原字节 | 新字节 | 说明 |
|---|---|---|---|
| `0x007EFA68` (slot) | `C0 CE 62 00` | `XX XX XX XX`（`Hook_Particle_Draw`） | DWORD 覆写 [实证] |
| `0x007EFCB0` (slot) | `80 E2 62 00` | `XX XX XX XX`（`Hook_ParticleSystem_Draw`） | DWORD 覆写 [实证] |
| `0x0062CEC0` 函数体 | `83 EC 24 53 55 56 57 8B F9 …` | **不变** | 禁止 inline |
| `0x0062E280` 函数体 | `83 EC 08 56 57 8B F9 …` | **不变** | 禁止 inline |
| `0x007E47F8` Bullet slot | `90 80 46 00` | **不变** | 禁止重装 |

---

## 8. 风险与残留

| # | 风险 | 等级 | 缓解 |
|---|---|---|---|
| R1 | 现场 `gamemd.exe` MD5 与本包不一致 | 高 | P0 硬门；不一致停手 |
| R2 | `ParticleSystem::Draw` 对 `Laser==0` 本就立即 `ret 8`，钩子收益主要在 Laser 系统与统一遥测 | 低 | P17 单独验收 Laser |
| R3 | 无主粒子（`+0x124==NULL`）只能按坐标查网格，可能误杀中立环境烟（废墟烟） | 低 | 谓词对 `pSys==NULL` 走坐标判定；可选放宽为「无主恒画」（产品决策） |
| R4 | 双绘制路径重复计数 | 低 | 谓词幂等；遥测按调用次数计，不按对象去重（与现有 `bulletsCulledByFog` 一致） |
| R5 | `EnableParticleFog` 默认 0 → 验收若忘开则遥测恒 0 | 中 | EVIDENCE_STANDARD v3：断言开启但计数 0 = UNVERIFIED |

---

## 9. 取证索引

| 产物 | 路径 |
|---|---|
| 字节核验脚本 | `out/re_work/landing_particle/verify_slots.py` |
| 核验输出 | `out/re_work/landing_particle/verify_slots_out.txt` |
| 既有深潜 | `docs/re/bullet_particle_fog_deep_dive.md` · `docs/re/particle_fog_owner_evidence.md` · `docs/re/fx_draw_chain.md` · `docs/re/visibility_gap_spysat.md` |
| 冲突裁决 | `docs/re/HOOK_POINT_MATRIX.md` §3.2（槽 69 单点安装） |
| 同步红线 | `docs/re/net_sync_checksum.md`（Particle 逻辑状态进 Checksum；绘制层条件安全） |
| 现网实现 | `ra2render/blitter_hooks.cpp`（`FogHooks::Hook_Bullet_Draw` 1581–1590；`InstallVTableHooks` 1617–1710；`RemoveVTableHooks` 1712–1788） |
| 反汇编转储 | `out/re_work/particle_fog/disasm_ParticleClass_Draw.txt` · `disasm_ParticleSystemClass_Draw.txt` |
