# particle_fog_owner_landing · R-PART-FOG 偏移定谳与落地规格

> **任务**：R-PART-FOG（微粒迷雾剔除 · 未落地清单收口）  
> **目标二进制**：`ra2youli/gamemd.exe`（YR 1.001）MD5 `4F37486E5B0DBE2AE5F45AEEE0F98367`，size 4,825,360 B，ImageBase `0x00400000` [实证]  
> **证据转储**：`out/re_work/re_sprint/R_part_fog/`（`s01_verify_offsets.py` / `s02_owner_chain.py` + `*_out.txt` + `claims_r_part_fog.txt`）  
> **前序**：`docs/re/particle_fog_owner_evidence.md`（A-15）、`docs/re/landing_pack_particle.md`（M-9 执行包）、`docs/re/bullet_particle_fog_deep_dive.md`  
> **证据三档**：`[实证]` 本轮对 gamemd.exe 字节/反汇编复算；`[前证]` 既有深潜已实证、本轮抽查一致；`[待实测]` 需真机验证后方可 PASS。

---

## 0. 一句话结论

**A-15 语义本轮独立复算全部命中，争议终结**：`PSys+0xE0=TechnoClass* Owner`、`PSys+0xFC=HouseClass* OwnerHouse`、`Particle+0x124=ParticleSystemClass*`、坐标在 `+0x9C`（`>>8` 得格）。迷雾剔除谓词**首选读 `pSys+0xFC`（House）**，空则回退 `pSys+0xE0 → Techno+0x21C`。落地走 M-9 虚表槽 69 双钩（`0x007EFA68`/`0x007EFCB0`），与 `Hook_Bullet_Draw` 同批装/卸，**禁重复装已装 5 槽**。

---

## 1. 偏移定谳（构造来源 + 读取点）

### 1.1 字段权威映射（本轮全命中）[实证]

| 结构体 | 偏移 | 语义 | 构造写点 | 读取点用法 | 判定 |
|---|:---:|---|---|---|---|
| `ParticleSystemClass` (sizeof `0x100`) | **`+0xFC`** | **`HouseClass* OwnerHouse`** | `0x0062DD9A: mov [esi+0xFC], eax`，`eax=[esp+0x40]`=ctor arg6；前置 `0x0062DD10` 零初始化 | **`0x0062C2CC: mov edx,[eax+0xFC]; push edx`** → 作调色板重映射参数压栈（`0x0062C2DC: push edx`） | 指针 + 作 House 实参消费 |
| `ParticleSystemClass` | **`+0xE0`** | **`TechnoClass* Owner`** | 非空 `0x0062DE37: mov [esi+0xE0], ecx`（`ecx=[esp+0x38]`=arg4）；空 `0x0062DE54` 写 ebx=0；前置 `0x0062DCC3` 零初始化 | **`0x0062DE6D: mov ecx,[esi+0xE0]` → `0x0062DE8C: call [eax+0x48]`**（vtable[18] `GetCoords`）；AI 侧 `0x0062ED70` 同款 | 指针 + 虚表方法调用 |
| `ParticleClass` (sizeof `0x138`) | **`+0x124`** | **`ParticleSystemClass*` 父系统** | `0x0062B721: mov [esi+0x124], ecx`，`ecx=[esp+0x38]`=ctor arg4 | **`0x0062C2C2: mov eax,[ebp+0x124]`** 紧接解引用 `+0xFC` | 容器反向指针 |
| 两者 | `+0x9C` | `CoordStruct Location`（Lepton） | ctor 多处 | `0x0062CF30 / 0x0062DE77` 等；`>>8` 得格 | 空间坐标 |

**与 A-14 反转语义（`+0xFC=Owner` / `+0xE0=CenterCoords`）的排伪**：
1. `0x0062DE54` 空参路径**写 0 到 `+0xE0`**——坐标字段无「空参写 NULL」语义；指针才有。[实证]
2. `+0xE0` 读出后 `call [eax+0x48]`（`ObjectClass::GetCoords`）——对 CoordStruct 无虚表可调。[实证]
3. `+0xFC` 读出后 `push edx` 作函数实参（调色板），且 ctor 来源是 arg6 `HouseClass*`（YRpp `ParticleSystemClass.h:40` 签名一致）。[实证]
4. A-14 早期草稿的 `+0xE0=CenterCoords` 记录已在 `landing_pack_crt_audio_particle.md` 更正；本报告维持 A-4/A-15 终局。

### 1.2 伴随字段（Owner 链）[实证]

| 字段 | 读点样本 | 语义 |
|---|---|---|
| `Techno+0x21C` | `0x005003F9: mov edi,[esi+0x21C]` 等 260+ 处 | `TechnoClass::OwnerHouse` |
| `House+0x30` | `0x004F9A16: cmp [eax+0x30], ecx` | `HouseClass::ArrayIndex`（0..31） |
| `House+0x5788` | `0x004F9A25: mov eax,[eax+0x5788]; shl edx,cl; and` | `HouseClass::Allies` 位掩码（整函数即 `IsAlliedWith`，`0x004F9A10` 起） |

**归属链全貌**：
```
Particle (+0x124) ──► ParticleSystem
                        ├─ +0xE0  TechnoClass* Owner ──► +0x21C HouseClass*
                        └─ +0xFC  HouseClass* OwnerHouse   ← 谓词首选
House: +0x30 index, +0x5788 allies ──► IsHousePlayerOrAlly
```

---

## 2. 迷雾剔除谓词应读哪个字段

**裁决：首选 `pSys+0xFC`（`HouseClass*`），空则回退 `pSys+0xE0 → Techno+0x21C`。**

| 优先级 | 路径 | 理由 |
|---|---|---|
| 1 | `pHouse = *(pSys + 0xFC)` | ctor 直写 House 指针；`0x62C2CC` 读点直接当 House 用；一步到位 |
| 2 | `pHouse = *(*(pSys + 0xE0) + 0x21C)` | `+0xFC` 可能为 0（ctor 允许 arg6 空）；Owner 可能已亡但字段仍在 |
| 3 | 坐标判定 `*(p+0x9C)>>8` 查 `s_visionGrid` | 无主粒子（`+0x124==NULL` 或两路皆空）只按坐标；产品可放宽为无主恒画 |

**谓词骨架**（对齐 `ShouldDrawBullet` 风格，细节见 M-9 §2.2）：
1. `VisibilityMode=vanilla` ⇒ 第一分支放行（与 `Hook_Bullet_Draw` 短路支③同构）[前证]
2. `IsHousePlayerOrAlly(pHouse, pPlayer)` ⇒ 己方/盟友恒画
3. 否则 `IsLeptonInPlayerVision(locX, locY)` 查 `s_visionGrid`（PSys 激光两端 OR）
4. 异常 `__except` 放行，防崩溃

**红线**：谓词只读；禁写 `+0x128` 寿命 / `+0x9C` 坐标 / `+0xE0`/`+0xFC` Owner。[前证 net_sync]

---

## 3. 落地规格（与 Hook_Bullet_Draw 合并）

### 3.1 虚表槽 69 · 禁重复装槽 [实证]

| 类 | 槽 69 条目 | 原 DWORD (LE) | 状态 |
|---|---|---|---|
| Unit `0x007F5D84` / Inf `0x007EB16C` / Air `0x007E23B8` / Bld `0x007E3FD0` / Bullet `0x007E47F8` | — | — | **已装，一字节不许再写** |
| **ParticleClass** | **`0x007EFA68`** | **`C0 CE 62 00` → `0x0062CEC0`** | 本包新增 |
| **ParticleSystemClass** | **`0x007EFCB0`** | **`80 E2 62 00` → `0x0062E280`** | 本包新增 |

**合并策略**（对齐 `HOOK_POINT_MATRIX.md` §3.2）：
- 全部安装/卸载只写 `blitter_hooks.cpp` 的 `InstallVTableHooks()` / `RemoveVTableHooks()`；在 **hook13（Bullet）之后追加 hook14/15**，与 Bullet 同批装/卸。
- **禁止**新开独立 install 函数、第二个 DLL 入口、对 `0x0062CEC0`/`0x0062E280` 做 inline patch、写 `.detour` 节。
- 幂等：`g_pOrigParticleDraw == nullptr` 才写；已装则 skip + 日志。
- 钩子体是**独立函数**（`Hook_Particle_Draw` / `Hook_ParticleSystem_Draw`），**不是**塞进 `Hook_Bullet_Draw` 函数体；共用 `s_visionGrid` / `IsHousePlayerOrAlly` / `IsLeptonInPlayerVision` / `FogModeVanillaPassThrough` 谓词与遥测哲学。

### 3.2 开关 `EnableParticleFog`

| 项 | 值 |
|---|---|
| INI | `[FogOfWar] EnableParticleFog` |
| **默认** | **`0`**（保守；验收显式置 1） |
| 代码 | `bool g_enableParticleFog = false;`（`ra2render.h` + `blitter_hooks.cpp`） |
| 读取 | `LoadConfig()`，紧随 `EnableBulletFog` |
| 与总闸关系 | **不受 `EnableStarCraftFog` 总闸约束**（与 Building/Bullet/Unit 三逻辑可见性键同级，对齐现网日志语义「逻辑可见性三键不受总闸影响」）[前证] |
| 与 VisibilityMode | `vanilla` 档第一分支放行（新增 kind=粒子，纳入 `FogModeVanillaPassThrough`） |

### 3.3 字节 / 钩点速查 [实证]

| 地址 | 原字节 | 动作 |
|---|---|---|
| `0x007EFA68` | `C0 CE 62 00` | DWORD 覆写 → `Hook_Particle_Draw` |
| `0x007EFCB0` | `80 E2 62 00` | DWORD 覆写 → `Hook_ParticleSystem_Draw` |
| `0x0062CEC0` / `0x0062E280` 函数体 | — | **不变**（禁 inline） |
| `0x007E47F8` 等 5 槽 | — | **不变**（禁重装） |

无需 trampoline：虚表 DWORD 覆写，签名同 `ret 8`（`__thiscall` 2 栈参，callee 清栈），早退直接 `return`。[实证：`ParticleClass::Draw` 双 `ret 8` @ `0x0062D029`/`0x0062D292`；`PSys::Draw` 唯一 `ret 8` @ `0x0062E37B`]

### 3.4 回滚

| 层级 | 动作 | 效果 |
|---|---|---|
| 软 | `EnableParticleFog=0` | 钩子在、直通原 Draw；画面原版 |
| 硬 | `RemoveVTableHooks()` 写回 `C0 CE 62 00` / `80 E2 62 00`，`g_pOrig*=nullptr` | 幂等，二次卸载无异常 |
| 事故 | 卸 DLL | 无 inline / 无 trampoline / 不写 `.detour` ⇒ 零残留 |

### 3.5 遥测（尾部追加，只加不改序）

`particlesCulledByFog` / `particlesRendered` / `particleSystemsCulledByFog` / `particleSystemsRendered`。  
**生效性断言**：`EnableParticleFog=1` 且敌方尾烟进雾场景下 `particlesCulledByFog > 0`，否则 **UNVERIFIED** 禁 PASS。[待实测]

---

## 4. 与 L4 / 灰雾门控交叉

| 交叉面 | 现状 | 与本包关系 | 裁决 |
|---|---|---|---|
| **L4 脏矩形** `0x006D3D99` | 原版 `jge 0x6D3E37`；现网 DLL 桩恒强刷且与总闸解耦（`L4DirtyMode` 未落地）[前证] | 粒子剔除是**对象层 Draw 早退**，不依赖 L4 标脏；L4=0 全刷时被剔粒子本就不画，无漏画风险 | **正交，零耦合**。禁把粒子剔除写进 L4 路径 |
| **灰雾层** `Draw_Fog 0x0047F250` | 逐格瓦片层，在对象层**之前**（`0x6D448B` < `0x6D465F`）[前证 layer_order] | 灰雾压暗先画，粒子后画；剔除只减少对象层像素，不改雾面 | **正交**。灰雾强度（`×0.71875` 未定位）与本包无关 |
| **原版粒子雾门** `0x0062CF23-0x0062CF5F` | 双失效：①`ScenarioFlags&0x1000` 被清 ⇒ 恒跳过；②`IsCellShrouded 0x005865E0` = `xor al,al; ret 4` 空桩 [实证本轮复算] | 原版无有效雾短路；本包钩子是**唯一**生效门 | **必须外挂**；禁改 `0x5865E0`/`IsShrouded`/`RevealArea*` |
| **VisibilityMode** | `vanilla` 放行 Unit/Bld/Bullet 三钩 | 粒子须纳入同一 vanilla 短路支 | **新增 kind**，否则 vanilla 档仍剔粒子 → 判据破 |
| **灰雾门控子键** | `EnableBuildingFog` / `EnableBulletFog` / `EnableUnitFog` | 新增第 4 键 `EnableParticleFog` | 同级、默认 0、不受总闸 |

**层序确认**：雾面（格层）→ 对象（含粒子，槽 69）。粒子剔除只动对象层，不影响雾面绘制与未探索黑幕（`0x47EFE0` SHROUD.SHP 路径零介入）。

---

## 5. 与 M-9 执行包的差异/补充（给实施方）

本文件是**定谳与交叉规格**；工程步骤仍以 `docs/re/landing_pack_particle.md` §7 执行表（P0–P20）为准。本轮补充三点：

1. **VisibilityMode 联动**（M-9 未写）：`Hook_Particle_Draw` / `Hook_ParticleSystem_Draw` 第一分支必须 `g_visibilityVanilla && FogModeVanillaPassThrough(<new kind>)` 短路放行，遥测「被 mode 覆盖」需纳入粒子计数。否则 vanilla 档机器判据（三处剔除 ≡0）会因粒子计数破功。
2. **总闸独立**：`EnableParticleFog` 不读 `EnableStarCraftFog`；日志需与三逻辑键同句打印「不受总闸影响」。
3. **早期零初始化写点**（A-15 未列）：ctor 内 `0x0062DCC3`（`+0xE0`）、`0x0062DD10`（`+0xFC`）各有一次 `mov [esi+..], ebx` 零初始化——**属 ctor 正常清零，不是坐标证据**；真写入以 `0x0062DD9A`/`0x0062DE37` 为准。断点调试时勿误判。

---

## 6. Top 风险

| # | 风险 | 等级 | 缓解 |
|---|---|---|---|
| R1 | 无主/环境粒子（`+0x124==NULL` 或 Owner 皆空）按坐标判定可能误杀废墟烟 | 中 | 产品决策「无主恒画」或收窄到 `pSys!=0` 才剔；遥测分列 |
| R2 | `+0xE0` Owner 可能已析构（悬挂指针），`Techno+0x21C` 解引用崩 | 中 | `__try/__except` 放行 + `IsBadReadPtr`；首选 `+0xFC` 路径避开 |
| R3 | 验收忘开 `EnableParticleFog` ⇒ 遥测恒 0 被误判 PASS | 中 | EVIDENCE_STANDARD v3：开启但计数 0 = UNVERIFIED |
| R4 | vanilla 档未纳入粒子短路 ⇒ 模式判据破 | 高 | 见 §5.1；P14/P15 用例补 vanilla 组 |
| R5 | 双绘制路径（`0x6D8DB0` / `0x6D97D0`）同帧两进 | 低 | 谓词幂等（纯函数）；遥测按调用次数计 |

---

## 7. 取证索引

| 产物 | 路径 |
|---|---|
| 偏移复算脚本 | `out/re_work/re_sprint/R_part_fog/s01_verify_offsets.py` |
| Owner 链复算 | `out/re_work/re_sprint/R_part_fog/s02_owner_chain.py` |
| 字节断言 | `out/re_work/re_sprint/R_part_fog/claims_r_part_fog.txt` |
| 前序定谳 | `docs/re/particle_fog_owner_evidence.md` §7（A-15） |
| 工程执行包 | `docs/re/landing_pack_particle.md`（M-9，P0–P20） |
| 槽 69 裁决 | `docs/re/HOOK_POINT_MATRIX.md` §3.2 |
| 同步红线 | `docs/re/net_sync_checksum.md` |
| 层序/灰雾 | `docs/re/layer_order_fog_vs_objects.md`、`docs/re/fog_gray_mix_offline_verify.md` |
| 现网钩子 | `ra2render/blitter_hooks.cpp` `Hook_Bullet_Draw:3155`、`InstallVTableHooks:3326` |
