[META]
task=UNIT-VIS  executor=DSH 子代理（parent agent id = session-852a2193-df41-4859-b6f3-cd17f595410f）  mode=read-only（仅新建文档 + out/re_work/unit_vis/**）
scope_declared=允许写：新 docs/re/unit_visibility_mechanism.md + out/re_work/unit_vis/**；禁止写：ra2render/**、ra2youli/**、台账、docs/RE_COORDINATION.md、其他 docs
baseline=ra2youli\gamemd.exe MD5 4F37486E5B0DBE2AE5F45AEEE0F98367（只读） / ra2render\ra2render.dll MD5 59671E8BC333A999820C788D76A5B375（= 部署件 ra2youli\ra2render.dll）
gate=verify_anchors.py 323/323 PASS；audit_bytes.py gamemd 47/47 OK、dll 22/22 OK

---

# UNIT-VIS —「关掉灰雾后远处敌人仍『靠近才显现』」机制归属定谳

> 任务卡：UNIT-VIS　执行方：DSH 子代理（parent session-852a2193-df41-4859-b6f3-cd17f595410f）
> 模式：**只读调查**（未启动游戏、未注入、未改任何二进制）；新建本文件 + out/re_work/unit_vis/**
> 基线：ra2youli\gamemd.exe MD5 4F37486E5B0DBE2AE5F45AEEE0F98367（4,825,360 B，.text SHA-256 c0368a17...4eb738）
> 　　　ra2render\ra2render.dll（= ra2youli\ra2render.dll）MD5 59671E8BC333A999820C788D76A5B375（138,752 B）
> 源码基线：ra2render/blitter_hooks.cpp = **2,516 行**（任务卡写 ~1,996 行，见 §3 勘误 E3）
> 证据等级：**[实证]** VA+FileOffset+原始字节+Capstone 反汇编+xref ／ **[推演]** ／ **[待实测]**

---

## [0] 结论摘要

1. **用户观察 100% 由我方剔除造成，与引擎无关**：总闸 `EnableStarCraftFog` 已与玩法可见性解耦，机动单位剔除由**独立键** `EnableUnitFog`（现网 ini:79 = **1**）单独门控；总闸=0 时三个钩子仍在生效，敌方机动单位在「不在我方/盟军实时直视网格」时于 v[69] 直接 `ret 8`，根本不调用原版 `Draw`。
2. **引擎侧不存在任何生效的「灰雾（已探索无视野）隐藏单位」门控**：对象绘制簇与各类 `Draw` 内**唯一**的迷雾门 `call 0x005865E0` 而该地址是 3 字节恒假 stub（`32 C0 C2 04 00` = `xor al,al; ret 4`）；灰雾谓词族（0x5864A0/0x586540）**只被雷达调用**。⇒ 「即使完全不剔除，原版也不会『靠近才现』」在**灰雾档**成立。
3. **引擎对「未探索黑幕」档确有原生介入**，但只对建筑/步兵且只是把亮度/掩码归零（`xor edi,edi`），不是硬跳过；`UnitClass::Draw` / `AircraftClass::Draw` 内**未发现**任何黑幕分支（负向结论，见 §4 U1）。
4. **引擎自身的半透明灰雾层在现网部署下不可达**：DLL 每逻辑帧把 `Scenario` 首 dword bit12（0x1000，= `ScenarioClass::FogOfWar`）强制清零（blitter_hooks.cpp:1043），故 `CellClass::Draw` 的 `test dh,0x10` 门（0x480251）恒不走 0x47F250。用户看到的灰雾**全部**是我方 FOG.SHP 图层。
5. 最大风险：把 `EnableUnitFog` 置 0 是**纯绘制层**改动（不写引擎状态、不消费 RNG、不改命令序），但它改变「可见性→玩家输入」链路，MP 需门控矩阵 / 真机对拍，**禁止宣称零风险**。

---

## [1] 逐条必答项结论表

### F1 我方路径定谳

| # | 问题 | 结论 | 证据等级 | 证据锚点 |
|---|---|---|---|---|
| F1-1 | `EnableUnitFog` 门控的全部单位绘制剔除点 | **共 3 处，且仅 3 处**：`UnitClass::Draw`(v[69]) / `InfantryClass::Draw`(v[69]) / `AircraftClass::Draw`(v[69]) 三个虚表槽覆写钩子 | [实证] | 产物 RVA `0x1950`/`0x2330`/`0x2600`；源码 `ra2render/blitter_hooks.cpp:2260`(Unit)/`:2272`(Infantry)/`:2284`(Aircraft)；安装表 DLL RVA `0x2DA9/0x2DAE`（Unit）、`0x2DC2/0x2DC7`（Infantry）、`0x2DDB/0x2DE0`（Aircraft） |
| F1-2 | 全 DLL 是否还有别的 `g_enableUnitFog` 读取点 | **无**。全 `.text` 扫描 `80 3D 0F 10 02 10 00` 仅 4 处：RVA `0x1950`(Aircraft 钩)、`0x2330`(Infantry 钩)、`0x2608`(Unit 钩)、`0x35BF`(LoadConfig) | [实证] | out/re_work/unit_vis/dllpat2.py 输出（g_enableUnitFog 全局 = DLL VA `0x1002100F`） |
| F1-3 | 钩子内的判据函数与判据链 | `ShouldDrawMobileObject`（DLL RVA `0x4530` ↔ 源码 `:1153-1220`）：己方⇒画／盟友(bitmask `pPlayer+0x5788`)⇒画／**格越界(0..511)⇒剔除**／`s_visionGrid[cell]==s_visionToken`⇒画／格 `+0xAC` 每屋传感器计数 `SensorsOfHouses[playerIdx]>0`⇒画／否则剔除 | [实证] | 源码 `:1153-1220`；DLL 反汇编 RVA `0x4575`(`mov esi,[0xA83D4C]`)、`0x4583`(`[edi+0x21C]` Owner)、`0x45F6`(`mov eax,[0x87F924]`) |
| F1-4 | **总闸=0 且 EnableUnitFog=1 时哪些单位被跳过** | 敌方（非己方非盟友）**全部机动单位**——坦克/载具(Unit)、步兵(Infantry)、战机(Aircraft)——只要其格**不在**我方/盟军实时直视网格内、且该格无心灵探测仪传感，即被跳过绘制（钩子直接 `ret 8`，不调用原版 `Draw`） | [实证] | RVA `0x1969`（剔除⇒`unitsCulledByFog` 64 位计数器 `0x10021980/84` +1）、RVA `0x1978`（`C2 08 00` = `ret 8`）、RVA `0x197B`（放行⇒`totalUnitsRendered` `0x10021978/7C` +1） |
| F1-5 | 判据是否看「格是否已探索」 | **完全不看**。钩子代码块内不读 `CellClass::CopyFlags(+0x12C)`、不读 `Shroudedness(+0x120)`/`Foggedness(+0x121)`、不调用引擎任何 shroud 谓词 ⇒ 判据只有「敌方 + 是否出视野圈 + 传感器」三项 | [实证] | RVA `0x1950-0x19A0` / `0x2330-0x2380` / `0x2600-0x2655` 全函数体反汇编（out/re_work/unit_vis/dis_Hook_Unit_Draw.txt） |
| F1-6 | 钩子是否读总闸 `g_enableStarCraftFog` | **不读**。三个钩子函数体各只含 1 处字节门（`0x1002100F`） | [实证] | 同上；对照旧版源码注释 `:2253-2254` 明示旧门控为 `g_enableStarCraftFog && ...` |

### F2 引擎原生路径定谳（关键）

| # | 问题 | 结论 | 证据等级 | 证据锚点 |
|---|---|---|---|---|
| F2-1 | 引擎是否隐藏**灰雾中**（已探索无视野）的单位 | **不存在生效路径**。对象绘制簇与各 Draw 内唯一的迷雾门是 call 0x005865E0，而 0x005865E0 = 32 C0 C2 04 00（xor al,al; ret 4）**恒返回 FALSE** 的 stub ⇒ 所有「跳过绘制」分支恒不执行 | [实证] | 0x005865E0 原始字节；调用点 0x006D8FDA / 0x006D920E / 0x006D929F / 0x006D965D（对象绘制簇）、0x00414543 / 0x0041456A（Aircraft）、0x0043DBBE / 0x0043DBD1（Building）、0x004680D5（Bullet）；全 exe 共 25 处（out/re_work/unit_vis/xref_fog_predicates.txt） |
| F2-2 | 灰雾谓词还有没有别的消费者 | 灰雾谓词只存在于 0x5864A0（判 [cell+0x13C] > 0）与 0x586540（同判据）；0x5864A0 **全 exe 仅 1 个调用点** = 雷达 RadarClass::Plot_Cell 内 0x00655D74；0x586540 **0 引用**。⇒ 战术对象绘制路径**从不**查询灰雾状态 | [实证] | out/re_work/unit_vis/xref_fog_predicates.txt；0x005865B9（mov ecx,[eax+0x13C]）、0x005865C1（jle）、0x005865C3（mov al,1） |
| F2-3 | ObjectClass::DrawIfVisible（v[65]，0x5F4B10）是否含迷雾逻辑 | **不含**。它是「一次性锁存 + 脏矩形 NeedsRedraw 门 + 视口裁剪 + call v[69]」。早退条件：[0xA8ED6B]==0 且 [0xB73550](Game::hWnd)!=0 且（(arg2==0 且 [this+0x80](NeedsRedraw)==0) 或 [this+0x81](InLimbo)!=0）⇒ xor al,al; ret 0xC | [实证] | 0x005F4B10 全函数 129 条指令反汇编；0x5F4B13（mov al,[0xA8ED6B]）、0x5F4B23（mov eax,[0xB73550]）、0x5F4B7F、0x5F4B85、0x5F4CFD（call [eax+0x114]） |
| F2-4 | TechnoClass::Draw / UnitClass::DrawIfVisible 是否隐藏单位 | TechnoClass **没有** Draw 虚函数（Draw 由 Unit/Infantry/Aircraft/Building/Bullet 各自 v[69] 实现）；UnitClass::DrawIfVisible（v[65]=0x73B0B0）只做开火/死亡动画态判断后转发基类 0x5F4B10，**无迷雾逻辑**；UnitClass::Draw（0x73CEC0）全程**零** shroud 引用 | [实证] | RTTI 符号表 out/reverse/symbols.json（UnitClass::v[65]=0x73B0B0、v[69]=0x73CEC0）；0x73B0B0-0x73B139 反汇编；0x73CEC0-0x73D450 内对 0x487950 / 0x586360 / 0x5864A0 / 0x5865E0 / +0x120 / +0x121 / +0x13C 命中数 = 0 |
| F2-5 | 引擎对**黑幕（未探索）**档做什么 | 两类 Draw 会查黑幕并**把亮度/掩码归零**（非硬跳过）：BuildingClass::Draw 0x43D539 call 0x487950 → 0x43D542 xor edi,edi；InfantryClass::Draw 0x5190D1 call 0x487950 → 0x5190DA mov [esp+0x14],edi(=0)。UnitClass::Draw / AircraftClass::Draw 内**未发现**黑幕分支（负向，见 §4 U1） | [实证]（建筑/步兵）／[推演]（Unit/Aircraft「未发现」） | 上述 4 锚点；黑幕谓词判据 0x5863F2 test byte [ecx+0x12C],8 → 0x586483 mov al,1 / 0x58648C xor al,al |
| F2-6 | 黑幕谓词语义与开关 | CellClass::IsShrouded（0x487950）→ MapClass::IsLocationShrouded（0x586360）判 **CellClass::CopyFlags(+0x12C) bit3 = cf_Explored**：位清 ⇒ 返回 1（未探索）。引擎侧**无 rules 键**；唯一相关开关是 ScenarioClass 首 dword bit12（0x1000，YRpp ScenarioClass.h:30 bool FogOfWar:1），在 0x47F01F（选 SHROUD.SHP / FOG.SHP）与 0x480251（是否走引擎灰雾层 0x47F250）被读 | [实证] | 0x4A98E6（or al,8 → mov [ebp+0x12C],eax）；0x480230、0x480251、0x480278 |
| F2-7 | 现网部署下引擎自身灰雾层是否可达 | **不可达**。UpdateVisionGrid 每逻辑帧清 Scenario bit12（blitter_hooks.cpp:1037-1043）⇒ 0x480251 test dh,0x10 恒「位清」⇒ 0x480278 / 0x480290 两条 call 0x47F250 永不执行；0x47EFE0 恒选 SHROUD.SHP（0x47F01F 位清分支） | [实证] | 0x480251、0x47F01F 原始字节；blitter_hooks.cpp:1038-1043 |
| F2-8 | 对象绘制簇是否有其它迷雾/可见性门 | 只有「视口裁剪 + v[65] 调用」：0x6D8DB0 内两条路径分别 0x6D909E、0x6D916C 调 v[65]；0x6D8FB2-0x6D8FAC 为屏幕/世界矩形裁剪，0x6D9038-0x6D906A 为视口边界比较；**无** +0x120 / +0x121 / +0x13C 读取 | [实证] | 0x6D8DB0-0x6D9172 反汇编（out/re_work/unit_vis/dis_ObjDrawCluster_6D8DB0.txt） |

### F3 区分测试设计

真机单变量四档（T1 / T2 / T3 / T4）见 **§2.5**（交 ZCode 执行；判据 = 截图 3 区 + 2 秒遥测行原文 + 计数归零）。

### F4 可达性结论

| 目标 | 需要动什么 | 可行性 | 代价/风险 |
|---|---|---|---|
| 「关掉灰雾后能看见**已探索但无视野**区的远处敌人」 | **只改配置**：EnableUnitFog=0（+ EnableBuildingFog / EnableBulletFog 视需要） | **可达**（现成键，零代码改动） | **纯绘制层**：钩子在 v[69] 内 ret 8，不写引擎对象状态、不消费 RNG、不改命令序、不碰 IsShrouded 判定；但可见性→玩家输入链路变化 ⇒ MP 需门控矩阵 + 真机对拍（§7） |
| 引擎原生隐藏（灰雾档）是否需绕过 | **不需要**（不存在生效门控，见 F2-1 / F2-2） | 可达 | —— |
| 引擎黑幕档若真机证明仍隐藏单位，是否可绕过 | 唯一静态可动点 = 让 0x5865E0 从 stub 恢复语义，或在 v[69] 层按 cf_Explored 放行 | **不可达**（在保留「未探索=未知」语义前提下） | 0x5865E0 全 exe 25 处调用（含弹道/建筑/飞机/对象绘制簇）；改它等于**开图**，直接触碰既存红线「禁改 IsShrouded(0x487950) / IsCellShrouded(0x5865E0) 判定」（net_sync_checksum.md §5.1、MP_SAFETY_REVIEW.md §5.3、mp_autodowngrade_spec.md:301），并摧毁「未探索黑幕」玩法。**不建议，标不可达** |
| 建筑 / 弹道是否可独立于单位控制 | 已独立：三键各自门控、各自钩子 | 可达 | 低 |

### F5 与用户期望的对照表

| 语义 | 需要改什么 | 能否保留未探索黑幕 | 是否影响玩法平衡 |
|---|---|---|---|
| **(A) 只去灰雾层、敌人仍按迷雾隐藏（= 现状）** | EnableStarCraftFog=0（+ 三键保持 1） | **能**。黑幕层由引擎 0x47EFE0 承载，我方只读计数、零介入（ra2render.h:71-81 注释；0x480230 恒定调用） | 维持我方「SC 式视距剔除」语义：单位可见性受视距限制，侦察仍有价值 |
| **(B) 关灰雾 ⇒ 同时看见雾中敌人（视距不再限制单位可见性）** | EnableStarCraftFog=0 **且** EnableUnitFog=0 **且** EnableBuildingFog=0 **且** EnableBulletFog=0（三者独立，缺一不可） | **能保留**（我方不介入黑幕绘制）；但「敌方单位位于**从未探索**区是否可见」取决于引擎黑幕档语义（§4 U1，静态未闭环 ⇒ 需 F3-T3 真机确认） | **显著改变**：已探索区域变成「全知」，等价于原版关掉 shroud 的对战设置；埋伏 / 侦察 / 信息战价值大幅下降 |
| **(C) 单位 / 建筑 / 弹道各自独立开关** | **已是现状**，无需改动：EnableUnitFog(:79) / EnableBuildingFog(:71) / EnableBulletFog(:74) 三键与总闸解耦 | 能 | 按启用的键逐项影响：单位=侦察价值、建筑=敌方基地暴露、弹道=开火可见性 |

---

## [2] 关键证据块

### 2.1 F1 —— 我方单位绘制剔除点（产物字节级）

三个钩子同构，以 Hook_Unit_Draw（DLL RVA 0x2600；另两个 RVA 0x2330 / 0x1950 仅入口偏置不同）：

```asm
RVA 0x002600  56                     push esi
RVA 0x002601  8B F1                  mov esi,ecx                    ; pThis
RVA 0x002603  E8 D8 EE FF FF         call 0x100014E0                ; CheckTelemetry()
RVA 0x002608  80 3D 0F 10 02 10 00   cmp byte ptr [0x1002100F],0    ; ★ g_enableUnitFog
RVA 0x00260F  74 1F                  je  0x10002630                 ; 键=0 则 不剔除
RVA 0x002611  56                     push esi
RVA 0x002612  E8 19 1F 00 00         call 0x10004530                ; ShouldDrawMobileObject(pThis)
RVA 0x002617  83 C4 04               add esp,4
RVA 0x00261A  84 C0                  test al,al
RVA 0x00261C  75 12                  jne 0x10002630                 ; 判据为真 则 放行绘制
RVA 0x00261E  83 05 80 19 02 10 01   add dword ptr [0x10021980],1   ; unitsCulledByFog++（低 32）
RVA 0x002625  83 15 84 19 02 10 00   adc dword ptr [0x10021984],0   ;                    （高 32）
RVA 0x00262D  C2 08 00               ret 8                          ; ★ 直接返回：不调用原版 Draw
RVA 0x002630  83 05 78 19 02 10 01   add dword ptr [0x10021978],1   ; totalUnitsRendered++
RVA 0x002637  A1 D0 19 02 10         mov eax,dword ptr [0x100219D0] ; g_pOrigUnitDraw
RVA 0x00263C  83 15 7C 19 02 10 00   adc dword ptr [0x1002197C],0
RVA 0x002643  85 C0                  test eax,eax
RVA 0x002645  74 0C                  je  0x10002653
RVA 0x002647  ...                    push / push / call eax         ; 转发原版 Draw(this,pLoc,pBounds)
```

安装表（InstallVTableHooks，DLL RVA 0x2D9F-0x2E1F）逐条给出「槽位 → 钩子 → 原入口保存槽」：

| vtable 槽（gamemd VA） | 目标类 | 装填的钩子（DLL RVA） | 原入口保存槽 | 槽内原始 dword 证据 |
|---|---|---|---|---|
| 0x007F5D84 | UnitClass::v[69] | 0x2600 | 0x100219D0 | C0 CE 73 00 → 0x0073CEC0 |
| 0x007EB16C | InfantryClass::v[69] | 0x2330 | 0x100219D4 | 90 8F 51 00 → 0x00518F90 |
| 0x007E23B8 | AircraftClass::v[69] | 0x1950 | 0x100219D8 | B0 44 41 00 → 0x004144B0 |
| 0x007E3FD0 | BuildingClass::v[69] | 0x1F50 | 0x100219DC | 90 D2 43 00 → 0x0043D290 |
| 0x007E47F8 | BulletClass::v[69] | 0x1FA0 | 0x100219E0 | 90 80 46 00 → 0x00468090 |

三个 EnableUnitFog 门控全局 = DLL VA 0x1002100F；紧邻的 0x1002100D / 0x1002100E 分别是 g_enableBuildingFog / g_enableBulletFog（与源码声明序 blitter_hooks.cpp:15-17 一致，由两个钩子的字节门反证）。

RTTI 交叉校验（out/reverse/symbols.json，988 类 RTTI 反解）：UnitClass::v[65]=0x73B0B0、v[69]=0x73CEC0；InfantryClass::v[69]=0x518F90；AircraftClass::v[69]=0x4144B0；BuildingClass::v[69]=0x43D290；BulletClass::v[69]=0x468090；ObjectClass / BulletClass / TechnoClass / FootClass 等 v[65] 均 = 0x5F4B10（基类共享体）。

### 2.2 F2 —— 引擎侧「雾中隐藏」门控全部死掉（stub 实证）

0x005865E0（FileOffset 0x001865E0）：

```asm
0x005865E0  32 C0        xor al,al
0x005865E2  C2 04 00     ret 4
```

即：以 MapClass::Instance(0x0087F7E8) 为 this、以 CoordStruct* 为唯一栈参的**迷雾谓词 stub，恒返回 0**。25 个调用点中与绘制直接相关的「死门」：

| 调用点 | 所在函数 | 被永久关闭的判定 | 原始字节 |
|---|---|---|---|
| 0x006D8FDA | 对象绘制簇 0x6D8DB0 | 0x6D8FE1 jne 0x6D940C（跳过该对象全部绘制） | E8 01 D6 EA FF / 0F 85 25 04 00 00 |
| 0x006D920E、0x006D929F、0x006D965D | 同上（另三条对象路径） | 同上 | —— |
| 0x00414543、0x0041456A | AircraftClass::Draw 0x4144B0 | 0x41454A je 0x414586（stub=0 则 恒跳走，连所有权过滤 0x50B6F0 都不做） | E8 98 20 17 00 / 74 3A |
| 0x0043DBBE、0x0043DBD1 | BuildingClass::Draw 0x43D290 | 0x43DBC5 jne 0x43DC0D（跳过建筑本体绘制） | E8 1D 8A 14 00 / 75 46 |
| 0x004680D5 | BulletClass::Draw 0x468090 | 0x4680DC jne 0x468422（跳过弹道绘制） | E8 06 E5 11 00 / 0F 85 40 03 00 00 |

**对象绘制簇不存在其它迷雾门**：0x6D8DB0 的 400 条指令窗口内，与「格迷雾」相关的读取只有上述 stub 调用；call [reg+0x104]（v[65] DrawIfVisible）仅 0x6D909E、0x6D916C 两处；无 +0x120 / +0x121 / +0x13C 内存读取。

**灰雾谓词只服务雷达**：

```asm
0x005865B9  8B 88 3C 01 00 00   mov ecx,[eax+0x13C]   ; 灰雾谓词族判据
0x005865C1  7E 09               jle 0x5865CC          ; <=0 则 非灰雾
0x005865C3  B0 01               mov al,1              ; >0  则 灰雾
```

xref：0x5864A0 唯一调用者 = 0x00655D74（RadarClass::Plot_Cell 0x655C50 内）；0x586540 零调用者。

### 2.3 F2 —— 黑幕谓词判据（同时构成 §3 勘误 E1 的反证）

```asm
0x00586360  83 EC 08               sub esp,8
0x00586363  56                     push esi
0x00586364  8B 74 24 10            mov esi,[esp+0x10]            ; CoordStruct*
0x005863F2  F6 81 2C 01 00 00 08   test byte ptr [ecx+0x12C],8   ; ★ CellClass::CopyFlags & cf_Explored
0x005863F9  0F 85 8D 00 00 00      jne 0x58648C                 ; 位=1（已探索）则 返回 0
0x00586483  B0 01                  mov al,1                     ; 位=0 则 返回 1（未探索 = shrouded）
0x0058648C  32 C0                  xor al,al
```

揭示路径写同一位：

```asm
0x004A98E6  8B 85 2C 01 00 00   mov eax,[ebp+0x12C]
0x004A98EC  0C 08               or  al,8             ; CopyFlags |= cf_Explored
0x004A98EE  6A 00               push 0
0x004A98F0  89 85 2C 01 00 00   mov [ebp+0x12C],eax
; 同函数 0x4A9924: or al,0x10  =>  bit4 = 当前可见
```

### 2.4 F2 —— 引擎灰雾层的唯一开关与「现网不可达」链

```asm
0x0047F018  A1 30 B2 A8 00      mov eax,[0xA8B230]    ; ScenarioClass::Instance
0x0047F01D  8B 08               mov ecx,[eax]
0x0047F01F  F6 C5 10            test ch,0x10          ; ★ Scenario FogOfWar bit 0x1000
0x0047F022  74 0B               je  0x47F02F          ; 位清 则 SHROUD.SHP (0x89E794)
;                                 位=1 则 FOG.SHP (0x89E790)

0x00480230  E8 AB ED FF FF      call 0x47EFE0         ; 黑幕/灰雾层（唯一承载，恒执行）
0x00480251  F6 C6 10            test dh,0x10          ; ★ 同一 bit 门
0x00480254  74 3F               je  0x480295          ; 位清 则 直接返回，不走引擎灰雾混色
0x00480278  E8 D3 EF FF FF      call 0x47F250         ; 引擎自身半透明灰雾混色（仅位=1 可达）
0x00480290  E8 BB EF FF FF      call 0x47F250
```

DLL 侧每逻辑帧清零该位（ra2render/blitter_hooks.cpp:1037-1043）：

```c
uintptr_t scenarioBase = *reinterpret_cast<uintptr_t*>(ADDR_SCENARIO_INSTANCE);
*reinterpret_cast<uint32_t*>(scenarioBase) &= ~0x1000u;
```

### 2.5 F3 —— 真机单变量区分测试设计（交 ZCode）

**纪律**：全程同一张地图、同一录像 / 同一开局脚本、同分辨率与渲染设置；每次只改一个键；每档截 3 张图（A 区=已探索无视野、B 区=从未探索、C 区=直视圈内）+ 粘贴 2 秒遥测行原文（[ra2render-telemetry-fogsplit] / [ra2render-fog]）。

| 档 | 变更（单变量） | 其余键 | 判据 | 结论口径 |
|---|---|---|---|---|
| **T1** | EnableUnitFog: 1 → 0 | EnableStarCraftFog=0；EnableBuildingFog=1；EnableBulletFog=1 | ① 遥测「机动单位剔除」是否变为 0；② A 区远处敌方坦克 / 步兵 / 战机是否出现 | 「出现」则 主因 = 我方剔除（= 本报告 F1 结论）；「仍不出现」则 存在第二隐藏源，进 T2 |
| **T2** | EnableBuildingFog、EnableBulletFog 同时置 0（在 T1 基础上） | EnableStarCraftFog=0 | 同 T1 + 「建筑剔除」「弹道剔除」计数归 0 | 「仍不出现」则 已排除我方全部剔除，指向引擎黑幕档（进 T3）；「出现」则 混入建筑 / 弹道遮挡，需分键再测 |
| **T3** | 不改键，做位置对照：同一敌方单位分别置于 A 区（已探索无视野）与 B 区（从未探索） | T2 档（三键全 0） | A 区可见性 vs B 区可见性 | A 可见 / B 不可见 则 引擎对黑幕档另有隐藏机制（§4 U1 成立）；A、B 均可见 则 引擎完全无隐藏（U1 反证） |
| **T4（反证档）** | 全键恢复默认（三键=1、总闸=1） | —— | 复核用户原始现象可复现 | 确认「观察本身」未受其它设置影响 |

**附加静态辅助（若可用调试器）**：① 在 0x006D8FE1（jne 0x6D940C）下断点，预期从不跳转；② 在 0x73CEC0（UnitClass::Draw 入口）对位于 B 区（未探索）的敌方坦克下条件断点——若从未命中，则该对象在更外层被跳过（继续向上游定位「对象绘制层数组」0x8A0360 族 LayerClass 填充点）；若命中且画面无变化，则引擎黑幕档靠「先画后被黑幕覆盖 / 亮度归零」实现。

---
## [3] 勘误（最小订正清单，交 Lead；本轮未改任何他人文件）

| # | 目标文件:行号 | 改前原文 | 改后文本 | 理由 | 影响面 |
|---|---|---|---|---|---|
| **E1** | ra2render/ra2render.h:147-153（OFF_CELL_FLAGS 注释与 [FOG-SPLIT 勘误]）；连带 docs/re/fog_split_report.md:148（§勘误 E3） | 「+0x12C 是 CopyFlags…其 0x08 = cf2_NoShadow…『已探索』位 cf_Explored = 0x08 在 **+0x140**」 | 「CellClass::CopyFlags(+0x12C) 的 **bit3 = cf_Explored**（引擎自身黑幕谓词 0x5863F2 test byte [ecx+0x12C],8 判据 + 揭示路径 0x4A98EC or al,8 写点双向实证）；cf2_NoShadow 属另一族命名，不能据以否证 +0x12C 的『已探索』语义」 | 原注释「bit3 = 已探索」**是对的**；FOG-SPLIT 的「证伪」结论被本次实证**反向证伪** | 影响所有以 +0x12C / +0x140 判「已探索」的实现与文档（fog_split_report.md §E3、ra2render.h）。docs/re/dirty_rect_l4.md:254、radar_fix2_report.md:137、radar_minimap_dots.md:135 与本结论**一致**，无需改 |
| **E2** | docs/re/visibility_gap_spysat.md:93 | 「004680DC jne 0x468422　; 黑雾 → 不画（原版行为）」 | 「004680DC jne 0x468422　; 黑雾 → 不画（**原版预留门，谓词 0x5865E0 为恒假 stub，实际永不生效**）」 | 分支存在但谓词恒 0（32 C0 C2 04 00）；landing_pack_particle.md:357 已记「0x5865E0 本就是 stub」，此处表述未同步 | 影响「原版是否隐藏雾中弹道 / 单位」的产品判断；可能也需同步 bullet_particle_fog_deep_dive.md、fx_draw_chain.md:158 |
| **E3** | 任务卡基线描述 | 「ra2render/blitter_hooks.cpp ~1,996 行」 | 实测 **2,516 行** | read 工具 totalLines = 2516 | 无产品影响（仅基线描述） |
| **E4** | 任务卡现网键快照 | 隐含「现网 EnableStarCraftFog=0」 | 本次快照 ra2youli\ra2render.ini（MD5 2DEB8F3B32A3EA57E2026FC1F292579B）：EnableStarCraftFog=1（**L33**）、EnableUnitFog=1（**L79**）、EnableBuildingFog=1（L71）、EnableBulletFog=1（L74） | 双快照口径：用户报告的 EnableStarCraftFog=0 属运行期 / 另一次快照，本次静态调查看到的是 =1 | 不影响 F1 / F2 结论（结论基于代码与字节，不依赖 ini 现值），但真机复现前须先确认实际生效值 |

---

## [4] 未闭环清单

| # | 缺口 | 为何无法静态闭环 | 下一步取证方法（可直接执行） | 阻塞级别 |
|---|---|---|---|---|
| **U1** | **引擎「未探索黑幕」档是否会隐藏机动单位**（UnitClass::Draw / AircraftClass::Draw 内未见黑幕分支，但游戏观感上黑幕内单位应不可见） | 对象绘制簇的唯一对象级迷雾门已被 stub 关闭；若隐藏机制存在于「绘制顺序 / 脏矩形-可见格调度 / 对象入层时机」三者之一，则需动态观察绘制序而非静态可判 | ① F3-T3 位置对照实验；② 调试器：0x006D8FE1 断点确认恒不跳；0x73CEC0 对未探索区敌坦克下条件断点确认是否被调用；③ 若确认外层跳过，向上游定位「对象绘制层数组」填充点（0x8A0360 族，LayerClass 8 层） | **P1** |
| **U2** | rules.ini [General] FogOfWar=（YRpp RulesClass.h:851）、会话设置 GameModeOptionsClass::FogOfWar（GameModeOptionsClass.h:42）在**绘制路径**上的消费点 | 只定位到 ScenarioClass bit12 这一处绘制侧开关；rules / 会话两字段的消费点分布在战役 / 遭遇战初始化等其它子系统，未在本轮 xref 范围内收敛 | ① xref RulesClass 实例字段偏移的写点，回溯其源 INI 键字符串 FogOfWar；② 在 0x480251 与 0x47F01F 处对 [Scenario+0] 下写断点，看谁置位 | P2 |
| **U3** | CellClass+0x13C 的精确语义（YRpp 标注 unknown_13C，但 0x5864A0 / 0x586540 用它作灰雾谓词） | 该偏移在本镜像中被大量非单元格结构复用（结构偏移扫描命中 232 处），无法仅靠静态归属 | 在 0x4A9890（揭示）与 0x6D8700（迷雾档计算，被 0x48023E 以 which=1 调用）上下文下写断点，观察 +0x13C 的写入者 | P2 |
| **U4** | 0x5865E0 的**原语义**（Westwood 曾实现后被存根化，还是发行版即如此） | 无符号 / 无 PDB；但 .text 段哈希与基线一致（c0368a17...4eb738），可确认现存 stub 属发行镜像原生 | 与其它版本 gamemd.exe（非 RA2OPT 变体）做同址字节比对 | P2 |
| **U5** | 关闭三键后对 MP **可感观一致性**的量化影响 | 需多人实机 | MP 门控矩阵 + 双端同帧对拍（见 §7） | P2 |

---

## [5] 写作用域合规声明

**新增（唯一改动）**：

| 路径 | 规模 | 说明 |
|---|---|---|
| docs/re/unit_visibility_mechanism.md | 本文件（10 节骨架 [0]-[9] + META 头） | 新建 |
| out/re_work/unit_vis/** | 见 §8 | 新建目录（脚本 / 反汇编 dump / claims / audit JSON） |

**未触碰**：ra2render/**（源码、obj、dll、ini 全部只读）、ra2youli/**（只读）、docs/RE_COORDINATION.md、台账文档、docs/re/** 其它既有文件、任何二进制。**未启动游戏、未注入、未下断点、未改任何二进制。**

**只读对象哈希（快照时点 = 本次会话）**：

| 文件 | 大小 | MD5 | 与任务卡基线 |
|---|---|---|---|
| ra2youli\gamemd.exe | 4,825,360 | 4F37486E5B0DBE2AE5F45AEEE0F98367 | 一致 |
| ra2render\ra2render.dll | 138,752 | 59671E8BC333A999820C788D76A5B375 | 一致 |
| ra2youli\ra2render.dll（部署件） | 138,752 | 59671E8BC333A999820C788D76A5B375 | 与源码树副本一致 |
| ra2youli\ra2render.ini | 9,459 | 2DEB8F3B32A3EA57E2026FC1F292579B | 见 §3 E4（总闸现值 = 1） |

---

## [6] 门禁实跑输出（原文）

### 6.1 python tools\verify_anchors.py

```text
===================================================================================================================
  RA2/YR 二进制决定性锚点自动化回归测试套件 (verify_anchors.py)
===================================================================================================================
目标文件 : D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe (大小: 4,825,360 字节, ImageBase: 0x400000)
断言文件 : D:\Project\ra2-campaign-forge\docs\re\anchor_claims.txt
反汇编器 : Capstone x86-32 引擎已就绪
-------------------------------------------------------------------------------------------------------------------
[基线完整性审计]
  [PASS] .text 原始段哈希: c0368a179f6e1a0f85bf94ebeb3a3e62efc8b1a2000abe164e5e1c61714eb738 (口径: raw(SizeOfRawData=0x3E0000))
  [INFO] PE头特征判定 : RA2OPT_PERF_APPLIED (0xAE=0x20, Stack=4MB, .text未变) (DllChar: 0x20, StackReserve: 0x400000)
  [PASS] .detour 原生签名: 40 00 00 00 44 74 72 00 ('@\0\0\0Dtr\0' @ VA 0xb93000) -> 严禁写入/注入原则确立
-------------------------------------------------------------------------------------------------------------------
回归汇总 : 断言总数 323 条 | PASS: 323 (100.00%) | FAIL: 0 | NOREAD: 0
★ 最终裁决 : [100% ALL PASS] 全库决定性锚点与二进制基线完全一致，生产环境可安全放行！
===================================================================================================================
```

### 6.2 python tools\audit_bytes.py out\re_work\unit_vis\claims_gamemd.txt

```text
0x6d8fda   e8 01 d6 ea ff             e8 01 d6 ea ff         OK     对象绘制簇: call 0x5865E0（stub） [.text FO=0x2D8FDA] | call 0x5865e0
0x6d8fe1   0f 85 25 04 00 00          0f 85 25 04 00 00      OK     对象绘制簇: jne 0x6D940C（跳过该对象）—— 因 stub 恒 0 而恒不执行 [.text FO=0x2D8FE1] | jne 0x6d940c
0x6d909e   ff 92 04 01 00 00          ff 92 04 01 00 00      OK     对象绘制簇: call [edx+0x104] = v[65] DrawIfVisible [.text FO=0x2D909E] | call dword ptr [edx + 0x104]
0x6d916c   ff 92 04 01 00 00          ff 92 04 01 00 00      OK     对象绘制簇第二条路径: call [edx+0x104] = v[65] DrawIfVisible [.text FO=0x2D916C] | call dword ptr [edx + 0x104]
0x47f01f   f6 c5 10                   f6 c5 10               OK     黑幕/灰雾层选图: test ch,0x10（Scenario FogOfWar 位=0x1000，位清则用 SHROUD.SHP） [.text FO=0x07F01F] | test ch, 0x10
0x480230   e8 ab ed ff ff             e8 ab ed ff ff         OK     CellClass::Draw: call 0x47EFE0（唯一黑幕层/灰雾层承载函数，恒执行） [.text FO=0x080230] | call 0x47efe0
0x480251   f6 c6 10                   f6 c6 10               OK     CellClass::Draw: test dh,0x10（Scenario FogOfWar 位门）：位清 则 不走引擎灰雾层 [.text FO=0x080251] | test dh, 0x10
0x480278   e8 d3 ef ff ff             e8 d3 ef ff ff         OK     CellClass::Draw: 引擎自身 call 0x47F250（半透明灰雾混色）—— 仅 FogOfWar 位=1 可达 [.text FO=0x080278] | call 0x47f250
--------------------------------------------------------------------------------------------------------------
合计 47 条：OK=47  MISMATCH/NOREAD=0
JSON -> out\re_work\unit_vis/audit_gamemd.json
```

### 6.3 python tools\audit_bytes.py out\re_work\unit_vis\claims_dll.txt --exe ra2youli\ra2render.dll

```text
0x402da9   68 00 26 00 10             68 00 26 00 10         OK     InstallVTableHooks: push 0x10002600（Hook_Unit_Draw） [.text FO=0x0021A9] | push 0x10002600
0x402dae   68 84 5d 7f 00             68 84 5d 7f 00         OK     InstallVTableHooks: push 0x007F5D84（UnitClass v[69] 槽） [.text FO=0x0021AE] | push 0x7f5d84
0x402dc2   68 30 23 00 10             68 30 23 00 10         OK     InstallVTableHooks: push 0x10002330（Hook_Infantry_Draw） [.text FO=0x0021C2] | push 0x10002330
0x402ddb   68 50 19 00 10             68 50 19 00 10         OK     InstallVTableHooks: push 0x10001950（Hook_Aircraft_Draw） [.text FO=0x0021DB] | push 0x10001950
0x402df4   68 50 1f 00 10             68 50 1f 00 10         OK     InstallVTableHooks: push 0x10001F50（Hook_Building_Draw） [.text FO=0x0021F4] | push 0x10001f50
0x402e10   68 a0 1f 00 10             68 a0 1f 00 10         OK     InstallVTableHooks: push 0x10001FA0（Hook_Bullet_Draw） [.text FO=0x002210] | push 0x10001fa0
0x404575   8b 35 4c 3d a8 00          8b 35 4c 3d a8 00      OK     ShouldDrawMobileObject: mov esi,[0xA83D4C] HouseClass::Player [.text FO=0x003975] | mov esi, dword ptr [0xa83d4c]
0x404583   8b 87 1c 02 00 00          8b 87 1c 02 00 00      OK     ShouldDrawMobileObject: mov eax,[edi+0x21C] TechnoClass::Owner [.text FO=0x003983] | mov eax, dword ptr [edi + 0x21c]
0x4045f6   a1 24 f9 87 00             a1 24 f9 87 00         OK     ShouldDrawMobileObject: mov eax,[0x87F924] MapClass 格数组（传感器例外分支） [.text FO=0x0039F6] | mov eax, dword ptr [0x87f924]
--------------------------------------------------------------------------------------------------------------
合计 22 条：OK=22  MISMATCH/NOREAD=0
JSON -> out\re_work\unit_vis/audit_dll.json
```

> **DLL 侧 claims 的 VA 约定（重要）**：audit_bytes.py 的段基准写死为 0x400000 + VirtualAddress，对 ImageBase=0x10000000 的 DLL 无法直接用真实 VA（会报 NOREAD 未映射）。故 claims_dll.txt 一律用 **0x00400000 + RVA** 书写（例：RVA 0x1950 写 0x00401950），段映射后落点 = 正确 FileOffset。该约定已实测两向验证：0x10002B50 报 NOREAD，0x401F50 正确落点并 OK。

---

## [7] 风险与红线提示

| 维度 | 是否触及 | 说明 |
|---|---|---|
| ① 同步语义 / 命令序 | **本结论（只读调查）不触及**；但据结论落地改键则需评估 | EnableUnitFog=0 只改变 v[69] 内 ret 8 的早晚——不写引擎对象状态、不改对象数组 / 层、不调 IsShrouded 判定、不改命令队列。但「可见性」直接进入玩家**输入**链路（点选 / 框选 / 寻敌所依据的可见信息），MP 语义上属可感观差异，故**需要 MP 门控矩阵 + 双端真机对拍验收**，禁止宣称「零风险 / 零 Desync」 |
| ② 随机数消费序 | 不触及 | 本轮无任何 RNG 相关改动；钩子代码内不调用 0x65C6D0 族 |
| ③ 存档结构 | 不触及 | 无任何存档字段读写 |
| ④ 渲染像素等价性 | **触及** | EnableUnitFog 由 1 改 0 会使输出像素等价于「不做迷雾剔除」档（敌方单位像素由被剔除变为被绘制），需真机对拍（F3-T1 / T2）确认与期望一致，禁止只靠静态断言 |

**红线重申（本轮遵守；后续任何落地亦不得触碰）**：不改 IsShrouded(0x487950) / IsCellShrouded(0x5865E0) / RevealArea* 的任何**判定**语义（net_sync_checksum.md §5.1、MP_SAFETY_REVIEW.md §5.3、mp_autodowngrade_spec.md:301）；不写 Scenario 状态（除既有 bit12=0 约定）；不改 .detour 段。

---

## [8] 交付物清单

| 类型 | 路径 | 规模 |
|---|---|---|
| 新文档 | docs/re/unit_visibility_mechanism.md | 本文件（META + [0]-[9] 十节） |
| 断言 | out/re_work/unit_vis/claims_gamemd.txt | **47** 条（全部 OK） |
| 断言 | out/re_work/unit_vis/claims_dll.txt | **22** 条（全部 OK） |
| 断言（合并） | out/re_work/unit_vis/claims.txt | 69 条 |
| 审计 JSON | out/re_work/unit_vis/audit_gamemd.json、audit_dll.json | 逐条 verdict |
| 脚本 | uvis.py（gamemd 反汇编 / xref / 字节）、symq.py（RTTI 虚表查询）、scan2.py（结构偏移扫描）、dllq.py、dllwin.py、dllpat.py、dllpat2.py、dllcall.py、emit_claims.py、mkclaims.py、find_writer.py | 11 个 |
| dump | dis_Infantry_Draw_518F90.txt、dis_Unit_Draw_73CEC0.txt、dis_Building_Draw_43D290.txt、dis_ObjDrawCluster_6D8DB0.txt、dis_Hook_Unit_Draw.txt、_sweep.tsv | 6 个 |

---

## [9] 待裁决项

| # | 分叉 | 建议方案 | 理由 |
|---|---|---|---|
| **D1** | 是否把 EnableUnitFog 默认值改为 0（= 关掉灰雾即看见远处敌人） | **建议保持默认 1**，改在 ra2render.ini 与用户文档中显式给出「想看远处敌人 则 EnableUnitFog=0」的组合键说明 | 默认 1 是已裁决的「SC 式视距剔除」语义；默认 0 会静默改变玩法平衡 |
| **D2** | 是否修正 §3 E1（+0x12C bit3 = cf_Explored） | **建议修**（ra2render.h:147-153 注释 + fog_split_report.md §E3） | 纯注释 / 文档，零行为影响；不修会让后续任何「判已探索」的实现继续误用 +0x140 |
| **D3** | 是否新增「一键回到原版可见性」聚合键（如 ClassicVisibility=1 则内部等价三键=0） | **建议可做**（纯门控聚合，不改判定） | 用户语义 (B) 需同时改 3 个键，易漏；聚合键可显著降低误配置成本 |
| **D4** | 是否为 §4 U1（引擎黑幕档是否隐藏单位）投入真机工时 | **建议投**（F3-T1 / T2 / T3 + 两个断点，预计 1 小时内可闭环） | U1 是「(B) 语义下未探索区是否也暴露」的唯一未知量；不闭环则 F5 表 B 行只能给条件结论 |
| **D5** | 用户报告的 EnableStarCraftFog=0 与本次快照（=1）不一致 | 真机复现前先抓 ra2render.log 的 [ra2render-fog] 行确认生效值 | 避免把「设置未生效 / 改错文件」误判为机制问题（§3 E4） |
