# ZCode 落地卡 · 微粒迷雾剔除（Particle/PSys 虚表槽 69 双钩）

> **卡号**：`ZC-PART-FOG` · **优先级**：P1（表现层剔除；默认关，零行为变化）  
> **执行方**：ZCode（真机/补丁安装唯一写者）· **起草**：MiMo（R-PART-FOG 偏移定谳）  
> **上游**：`docs/re/particle_fog_owner_landing.md`（T15）· `docs/re/landing_pack_particle.md`（M-9 执行包）· 复算脚本 `out/re_work/re_sprint/R_part_fog/`  
> **本卡范围**：**仅 Particle + ParticleSystem 两个槽 69 双钩**（`0x007EFA68` / `0x007EFCB0`）。Unit/Inf/Air/Bld/Bullet 五槽、L4 脏矩形、灰雾层 **本卡不动**。  
> **证据基线**：`ra2youli/gamemd.exe` 1.001 · MD5 `4F37486E5B0DBE2AE5F45AEEE0F98367` · size 4,825,360 B · ImageBase `0x00400000` · `file_off = VA − 0x00400000`
> 【W3 勘误 E-W3-01】原句 `FileOffset = VA − 0x400000` 仅在 `.text/.rdata/.data` 成立；
> 通用式为 `FileOffset = 段.PointerToRawData + (VA − 段.VirtualAddress)`，
> 本镜像 `.rsrc`/`.detour` 为 `VA − 0x6FC000`。依据：out/re_work/_lead_baseline/W3/LEAD_ERRATUM_E-W3-01_fileoffset_rule.md；分级：[实证]

---

## 0. 一句话

在 `InstallVTableHooks()` **hook13（Bullet）之后**追加 hook14/15，把 `0x007EFA68` / `0x007EFCB0` 两个虚表 DWORD 分别覆写为 `Hook_Particle_Draw` / `Hook_ParticleSystem_Draw`；谓词走 **`pSys+0xFC → +0xE0→+0x21C → +0x9C>>8×visionGrid`** 三级归属链；`EnableParticleFog` **默认 0 且不受 `EnableStarCraftFog` 总闸**；卸载写回原 DWORD。**禁重装已装 5 槽**。

---

## 1. 执行表（槽 69 DWORD 覆写，与 `Hook_Bullet_Draw` 同批）

| 项 | 值 |
|---|---|
| **步骤 ID** | `PART-FOG-双钩`（工程步骤号沿用 M-9 `P10`/`P11`） |
| **安装点** | `ra2render/blitter_hooks.cpp` `InstallVTableHooks()`，**hook13（Bullet `0x007E47F8`）之后追加 hook14/15** |
| **卸载点** | `RemoveVTableHooks()`，`g_pOrigBulletDraw` 分支之后（与 Bullet **同批**装/卸） |
| **合并约束** | 只写上述两函数；**禁**新开独立 install 函数 / 第二 DLL 入口 / inline patch `0x0062CEC0`/`0x0062E280` / 写 `.detour` 节 |
| **禁重装** | 已装 5 槽 **一字节不许再写**：Unit `0x007F5D84` / Inf `0x007EB16C` / Air `0x007E23B8` / Bld `0x007E3FD0` / Bullet `0x007E47F8` |
| **幂等** | `g_pOrigParticleDraw == nullptr` 才写；已装则 skip + 日志 |

### 1.1 双钩原 DWORD（小端，`.rdata`）

| # | 类 | 槽 69 条目 VA | 文件偏移 | **原 DWORD（LE 4B）** | 原入口 | 新入口（本卡） | 动作 |
|---|---|---|---|---|---|---|---|
| hook14 | `ParticleClass` | **`0x007EFA68`** | `0x003EFA68` | **`C0 CE 62 00`** | `0x0062CEC0` | `Hook_Particle_Draw` | DWORD 覆写 |
| hook15 | `ParticleSystemClass` | **`0x007EFCB0`** | `0x003EFCB0` | **`80 E2 62 00`** | `0x0062E280` | `Hook_ParticleSystem_Draw` | DWORD 覆写 |

> **字节序红线**：必须按 **LE** 写 `C0 CE 62 00` / `80 E2 62 00`。误抄 BE `00 62 CE C0` 会写入 `0xC0CE6200` → 崩。[实证]
> 【W3 勘误 · W3-A6/ISSUE-PARTICLE-BE-BYTES】改前：00 62 CE C0；改后：C0 CE 62 00 / 80 E2 62 00 (小端 LE)；依据：errata_sync_master_table.md:23 (R-E08); FIXPACK_F01-F13_report.md F-04；分级：P0

### 1.2 语义边界（只拦 Draw，不碰逻辑）

| 位置 | 动作 | 本卡 |
|---|---|---|
| `0x0062CEC0` / `0x0062E280` 函数体 | 原 Draw | **不变**（禁 inline） |
| `ParticleClass::Update 0x0062CE40` / `PSys::AI 0x0062FD60` | 寿命/AI | **不变** |
| `+0x128` 寿命 / `+0x9C` 坐标 / `+0xE0`/`+0xFC` Owner | 对象字段 | **只读，零写** |
| `IsCellShrouded 0x005865E0` / `RevealArea*` | 原版雾门 | **不变**（`0x5865E0` 本就空桩） |
| 槽 69 五连（Unit…Bullet） | 已装钩子 | **不变** |

签名同 `ret 8`（`__thiscall` 2 栈参，callee 清栈），早退直接 `return`，无需 trampoline。[实证：`ParticleClass::Draw` 双 `ret 8` @ `0x0062D029`/`0x0062D292`；`PSys::Draw` 唯一 `ret 8` @ `0x0062E37B`]

---

## 2. 谓词（归属链三级，只读）

**取值路径（Particle；PSys 直接从第 2 级起）**：

```
pSys = *(p + 0x124)                    // Particle → 父系统
pHouse = *(pSys + 0xFC)                // ① HouseClass* OwnerHouse（首选）
if (!pHouse) {
    pTech = *(pSys + 0xE0)             // ② TechnoClass* Owner
    if (pTech) pHouse = *(pTech + 0x21C)  //    → TechnoClass::OwnerHouse
}
// ③ 坐标：*(p+0x9C)>>8 / *(p+0xA0)>>8 → s_visionGrid（PSys 激光两端 OR：+0x9C/+0xA0 与 +0xD4/+0xD8）
```

**判定骨架**（对齐 `ShouldDrawBullet` 风格）：

1. `VisibilityMode=vanilla` ⇒ **第一分支放行**（`FogModeVanillaPassThrough` 新增 kind=粒子）——**M-9 缺口，本卡必须补**，否则 vanilla 档机器判据（三处剔除 ≡0）会因粒子计数破功。
2. `IsHousePlayerOrAlly(pHouse, pPlayer)` ⇒ 己方/盟友恒画。
3. 否则 `IsLeptonInPlayerVision(locX, locY)` 查 `s_visionGrid`；无主粒子（`+0x124==NULL` 或两路皆空）只按坐标（产品可放宽为无主恒画）。
4. 异常 `__try/__except` **放行**，防悬挂指针崩溃（`+0xE0` Owner 可能已析构）。

**红线**：谓词只读；**禁写** `+0x128` 寿命 / `+0x9C` 坐标 / `+0xE0`/`+0xFC` Owner。[前证 net_sync]

---

## 3. 开关 · 遥测 · 回滚

### 3.1 开关 `EnableParticleFog`

| 键 | 默认 | 语义 |
|---|---|---|
| `[FogOfWar] EnableParticleFog` | **`0`** | `1` 时启用敌方粒子/激光剔除；`0` 时钩子仍在但直通原 Draw（零行为变化） |
| 代码 | `bool g_enableParticleFog = false;`（`ra2render.h` + `blitter_hooks.cpp`） | `LoadConfig()` 紧随 `EnableBulletFog` 读取 |

**与总闸关系**：**不受 `EnableStarCraftFog` 总闸约束**（与 `EnableBuildingFog` / `EnableBulletFog` / `EnableUnitFog` 三逻辑可见性键同级）。启动日志需与三键同句打印「不受总闸影响」。[前证]

**与 VisibilityMode**：`vanilla` 档第一分支放行（纳入 `FogModeVanillaPassThrough`，见 §2）。

### 3.2 遥测（尾部追加，只加不改序）

`particlesCulledByFog` / `particlesRendered` / `particleSystemsCulledByFog` / `particleSystemsRendered`。

**生效性断言**：`EnableParticleFog=1` 且敌方尾烟进雾场景下 `particlesCulledByFog > 0`，否则 **UNVERIFIED** 禁 PASS。[待实测]

### 3.3 回滚（写回原 DWORD）

| 层级 | 动作 | 效果 |
|---|---|---|
| **软** | `EnableParticleFog=0` | 钩子在、直通原 Draw；画面原版 |
| **硬** | `RemoveVTableHooks()` 写回 **`0x007EFA68`←`C0 CE 62 00`**、**`0x007EFCB0`←`80 E2 62 00`**，随后 `g_pOrig* = nullptr` | 幂等，二次卸载无异常 |
| **事故** | 卸 DLL | 无 inline / 无 trampoline / 不写 `.detour` ⇒ 零残留 |

---

## 4. 真机验收用例（A1–A5）

| ID | 步骤 | 期望 |
|---|---|---|
| **A1** | 默认配置启动（`EnableParticleFog` 不写或 =0） | 两槽仍为原 DWORD `C0 CE 62 00` / `80 E2 62 00`（若钩子已装则值为新入口但**行为直通**）；敌方尾烟仍可见；`particlesCulledByFog==0`；日志 `EnableParticleFog=false`；无崩溃 |
| **A2** | `EnableParticleFog=1` 启动，敌方 V3/无畏级开火进黑雾 | 黑雾内尾烟/弹道粒子消失；`particlesCulledByFog > 0`；己方/盟友尾烟恒可见（`particlesRendered` 增、剔除不增） |
| **A3** | 同局 `Laser=yes` 粒子系统武器：敌方激光进黑雾 | 两端皆不可见 → 光束消失；一端可见 → 仍画（两端 OR） |
| **A4** | **vanilla 档**（`VisibilityMode=vanilla`）再跑 A2 场景 | **粒子零剔除**（第一分支放行）；`particlesCulledByFog==0`；与 Unit/Bld/Bullet 三钩 vanilla 短路同构。**【M-9 缺口提示】**：M-9 执行表未写 vanilla 联动，本卡 §2 第 1 条强制补齐，否则模式判据破 |
| **A5** | 硬回滚演练：`RemoveVTableHooks()` / 卸载 DLL | `0x007EFA68`=`C0 CE 62 00`、`0x007EFCB0`=`80 E2 62 00` 复原；再启不崩溃；二次卸载无异常；`except.txt` 空 |

**禁止把「没崩」当成功**：A2 必须有「雾内粒子消失」截图/像素或 `particlesCulledByFog > 0` 计数证据；A4 必须有 vanilla 档零剔除计数。忘开开关导致计数恒 0 = **UNVERIFIED**，禁 PASS。

---

## 5. 风险（执行方必读）

| ID | 风险 | 等级 | 要求 |
|---|---|---|---|
| R-1 | 字节序写反（BE `00 62 CE C0`） | 高 | 必须 LE `C0 CE 62 00` / `80 E2 62 00` |
| R-2 | vanilla 档未纳入粒子短路 | **高** | A4 强制；`FogModeVanillaPassThrough` 新增 kind=粒子 |
| R-3 | `+0xE0` Owner 悬挂指针解引用崩 | 中 | `__try/__except` 放行 + 首选 `+0xFC` 路径 |
| R-4 | 无主/环境粒子误杀废墟烟 | 中 | 产品决策「无主恒画」或收窄到 `pSys!=0` 才剔；遥测分列 |
| R-5 | 忘开 `EnableParticleFog` 误判 PASS | 中 | EVIDENCE_STANDARD v3：开启但计数 0 = UNVERIFIED |
| R-6 | 重装已装 5 槽 / 新开独立 install | 高 | 只写 `InstallVTableHooks`/`RemoveVTableHooks`；hook13 后追加 |
| R-7 | 谓词误写对象字段 → 联机 DESYNC | 高 | 只读；禁写 `+0x128`/`+0x9C`/`+0xE0`/`+0xFC` |

---

## 6. MP：表现层 SAFE 可保留

| 检查项 | 本包行为 | 判定 |
|---|---|---|
| 拦截点 | 仅虚表槽 69 `Draw` 早退（`ret 8` 语义） | **SAFE** |
| Update / AI / 寿命 | 未触碰；寿命 `dec [esi+0x128]` 在 Update，早退不造成永生粒子 | **SAFE** |
| 状态写入 | 钩子与谓词 **零写** 对象字段 | **SAFE** |
| Checksum / `.SAV` | 不改逻辑坐标 / RNG / Owner；绘制钩不进档 | **SAFE** |
| 联机两端 | 画面剔除是**本地视口**效果；两端可不同开，逻辑帧仍一致 | **SAFE（零 OOS）** |

**结论**：与已装 `Hook_Bullet_Draw` / `Hook_Unit_Draw` 同属「绘制层 + 私有视野缓存」，落在 net_sync **可动**象限。**MP 表现层 SAFE 特性可保留**，无需 MP 强制关闭；不加新握手键。

---

## 7. 交付回执（填完交回）

```
ZC-PART-FOG RESULT
- build/md5(gamemd):
- install path: (ra2render InstallVTableHooks hook14/15)
- EnableParticleFog: (default 0 | explicit 1 for A2/A3)
- 0x007EFA68 before/after: (C0 CE 62 00 -> ?)
- 0x007EFCB0 before/after: (80 E2 62 00 -> ?)
- 已装5槽未重写: y/n
- A1..A5: (each PASS/FAIL + evidence path)
  A4 vanilla 短路: PASS/FAIL (M-9 缺口已补)
- particlesCulledByFog (A2): (must >0)
- MP: SAFE 保留 / 其它
- except.txt: empty|path
- rollback tested: y/n (原 DWORD 复原)
```

---

## 8. 不在本卡

- Unit/Inf/Air/Bld/Bullet 五槽 —— 已装，禁重装  
- L4 脏矩形 `0x006D3D99` / 灰雾层 `Draw_Fog` / 未探索黑幕 —— 正交，零耦合  
- `IsCellShrouded` / `RevealArea*` 改写 —— 禁止  
- 无主恒画的产品决策落地 —— 留后续卡  
- MP 握手字段扩展 —— 维持既有 MP 门控，不加新握手键  
- 台账/看板登记 —— 由 Lead 收口

---

*依据：`docs/re/particle_fog_owner_landing.md`（T15 偏移定谳）· `docs/re/landing_pack_particle.md`（M-9 P0–P20）· `docs/re/HOOK_POINT_MATRIX.md` §3.2 · `docs/re/net_sync_checksum.md`。原 DWORD 2/2 MATCH；槽 69 双钩为唯一写入面。*
