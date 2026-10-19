# errata_from_rtrack —— R 轨首批成果 × 既有勘误对照与补丁块（M 轨）

> [META]
> 任务=R-track 对接 · 补丁/勘误侧 · 起草方=MiMo（M 轨）· 日期 2026-09-30
> 性质：**只登记不就地改**（冻结源不改；补丁块供 Lead/用户解冻后粘贴）
> 上游只读：`docs/re/sbh_freelist_deep_dive.md`、`lightconvert_0x420140_deep_dive.md`、`warhead_abi_verses_deform_deep_dive.md`、`warhead_abi_residuals_deep_dive.md`
> 既有补丁包：`out/re_work/errata_patches/by_file/*.patch`（E-1/E-2/E-7/E-8/E-9/E-ZC11…）
> 写作用域：本文 + `out/re_work/errata_patches/**`（追加）+ `out/re_work/rtrack_bridge/**`；**不改**任何 `*_deep_dive.md` / `ARCHITECTURE_ATLAS*` / `out/reverse/**` / `ra2render/**` / 台账 / 工具脚本

---

## 0. 一句话

> R-03 把 **E-8 从「存疑」收口为「定谳：Deform=+0x98」**，并把 E-2-05/E-7-02 里「Verses 施加点未定位」**加强为已定位 8 处 FPU 站点**；R-06 再锁 `+0xAC=WeaponTypeClass` 与 V1 属主 `MapClass::GetTotalDamage`。R-02（SBH）与 E-ZC11 崩溃归因**一致且加强**（毒在 freelist-head 而非用户块）；R-01（LightConvert）**否定**「表内嵌 0.71875 / M1 向灰」，不与 E-1/E-2/E-8 冲突。**E-1（Blitter 4/8/12/16）R 轨未触碰，维持原补丁。**
> 【W3 勘误 · W3-A6/ISSUE-VERSES-SITES-COUNT】改前：Verses 施加点未定位」**加强为已定位 8 处；改后：Verses FPU 索引访存共 9 处 (V1/V2a/V2b/V3/V4/V5/V6a/V6b/V6c)；依据：errata_sync_master_table.md:22 (R-E07); warhead_verses_residual_p2.md:18, 58；分级：P1

> 【勘误 2026-09-30 · R-E07 · errata_sync】原文「已定位 8 处 FPU 站点」→ 订正为 **9 处**（V1/V2a/V2b/V3/V4/V5/V6a/V6b/V6c）。权威：warhead_verses_residual_p2.md:18,58 / warhead_abi_verses_deform_deep_dive.md §3.2（表实列 9 行）。原文保留不删字。

---

## 1. 一致性表：R 轨结论 vs 既有勘误

| # | R 轨结论（源:行号） | 既有勘误/口径 | 关系 | M 侧动作 |
|:---:|---|---|---|---|
| 1 | **Deform = +0x98**（double），`+0xA8 = Verses[1]`（`warhead_abi_verses_deform_deep_dive.md:17-24,72`） | **E-8**（`weapons_damage_production.md.patch` L136-145）：「`Deform\|0xA8` 与 Verses 重叠，闭环前不得按 +0xA8 读写」 | **加强 → 收口** | 追加 **E-8-D** 定谳补丁块（本文件 §2.1；`by_file/weapons_damage_production.md.patch` 已追加同文） |
| 2 | Verses[0]=**+0xA0**，`+0xB0=Verses[2]`，覆盖 `+0xA0..+0xF7`（`warhead_abi_verses_deform_deep_dive.md:76-91`） | **E-2**（8 处 +0xB0→+0xA0） | **一致**（字节级复核通过） | **不改 E-2**；仅在 E-2 统一声明后追加「R-03 复核通过」注 |
| 3 | **Verses 施加点已定位 8 处 FPU**（V1 `0x48923D` 主施加；`warhead_abi_verses_deform_deep_dive.md:94-122`） | **E-2-05 / E-7-02** 行末注：「Verses 实际施加点**未定位**（全 .text `*8+0xA0/0xB0` 0 命中）」 | **加强 / 局部改写**（旧「0 命中」因未扫 FPU `DC/DD` 形态，属扫描面缺口而非结论） | 追加 **E-2-S** 施加点补记块（§2.2）；不删原文「未定位」字样，只追加订正 |

> 【勘误 2026-09-30 · R-E07 · errata_sync】上表「8 处 FPU」→ 订正为 **9 处**（V1/V2a/V2b/V3/V4/V5/V6a/V6b/V6c）。原文保留不删字。
| 4 | V1 块属主 = **`MapClass::GetTotalDamage @ 0x489180`** 正伤害分支（`warhead_abi_residuals_deep_dive.md:18,94-137`） | E-2-05 另注 R6-E3「`0x701939` 非 Verses 点」 | **一致 + 补全** | 并入 **E-2-S** 块（一并订正「未定位」） |
| 5 | **`obj+0xAC` 宿主 = WeaponTypeClass.Warhead**；BulletClass WH 在 `+0x128`（`warhead_abi_residuals_deep_dive.md:17,27-90`） | 既有 E-1/E-2/E-8 **无此项**（R-03 曾标 [待实测]） | **新增** | 记入 **E-ABI-AC**（§2.3）；可供后续 ATLAS/武器文档解冻时粘贴 |
| 6 | `TechnoTypeClass+0x9C = Armor` 0..10（`warhead_abi_residuals_deep_dive.md:19,141-170`） | 同上，无冲突 | **新增确认** | 并入 **E-ABI-AC** |
| 7 | SBH：毒 class=**4**（req 57..72B），毒值在 **heap_info freelist-head**（`sbh_freelist_deep_dive.md:20-23,232-242`）；FE00FFFF 映像 0 次（L22） | **E-ZC11-7a/b**（崩溃=原版 `__sbh_alloc_block`，毒值 FE00FFFF） | **一致 + 加强**（指认毒槽位=class4 head，主候选 UAF 写穿 next） | **不改 E-ZC11**；机制增量进 `iface` §9 与 `except_watch` 判据提案（harness 侧，另卡） |
| 8 | size-class 64 类 / Region 0x14 / head 数组布局 / H1–H6 钩子规格（`sbh_freelist_deep_dive.md:16-18,282-314`） | 无既有勘误冲突 | **新增机制** | 接口增量（`iface_mimo_re.md` §9.1）；门禁判据增强提案 |
| 9 | LightConvert 表 **不含 0.71875**；`q=floor(lo·hi·(L−1)/32258)`；与 M1 向灰结构性不吻合（`lightconvert_0x420140_deep_dive.md:15-20,151-191`） | 无 E-1/E-2/E-8 冲突；`fog_firststage_site_locate.md` 候选 C1 为「首选[推演]」 | **否定 C1（降权）** | 不改冻结 fog 文档；挂接到 **ZC 段 G / 迷雾桩待办**（`iface` §9.2） |
| 10 | Blitter 分配 4/8/12/16（R 轨本批**未**产出 Blitter 新结论） | **E-1**（P0 微内核=8B） | **无冲突** | **维持 E-1 原补丁不动** |
| 11 | HouseClass Array 布局偏移差 +4/+0x10（`warhead_abi_residuals_deep_dive.md:23,209-217`） | 无既有勘误 | **[冲突-轻微] 新登记** | 记入 **E-ABI-AC** 附注（不升 P0） |

**摘要**：冲突 **0**；收口 **1**（E-8）；加强/局部改写 **1**（E-2-05/E-7-02 施加点）；新增 ABI **1**（E-ABI-AC）；一致加强 **2**（E-2 复核、E-ZC11×SBH）；无关维持 **1**（E-1）。

---

## 2. 可粘贴补丁块（Lead 解冻后粘贴；原文保留不删字）

### 2.1 E-8-D · Deform 偏移定谳（升级 E-8）

- **文件:行号**：`docs/re/weapons_damage_production.md:127`（与既有 E-8 同锚）
- **前 40 字符锚点**：`` | `Deform` | `0xA8` | double | 地形变形 |``
- **关系**：**取代**既有 E-8「存疑/禁令」表述的效力（原 E-8 块仍保留，本块追加在后）

```
【勘误 2026-09-30 · E-8-D 定谳 · R-03】原文「Deform | 0xA8」错误。实证：
`Deform` = `WarheadTypeClass+0x98`（double，`+0x98..+0x9F`），
锚点 `0x75D792 = DD 9E 98 00 00 00`（`fstp qword [esi+0x98]`，LoadFromINI）；
ctor `0x75CED8/0x75CEDE` 将 `+0x98/+0x9C` 清零印证。`+0xA8` 实为 `Verses[1]`。
「不得按 +0xA8 读写 Deform」禁令解除，改按 `+0x98` 读写；`+0xA8` 归 Verses[1]。
另：`Size()=0x1D0`（v[12]=`0x0075E4F0: B8 D0 01 00 00 C3`）。
权威：`docs/re/warhead_abi_verses_deform_deep_dive.md` §1 / §5.1。原文保留不删字。
```

### 2.2 E-2-S · Verses 施加点补记（加强 E-2-05 / E-7-02）

- **文件:行号**：`docs/re/weapons_damage_production.md:215`（E-2-05）、`:473`（E-7-01）、`:581`（E-7-02）
- **前 40 字符锚点（L215）**：``**Verses 应用点**：在 `ReceiveDamage` 的伤害归一化段``
- **关系**：既有块已改偏移 +0xA0 并注「施加点未定位」；本块**只追加**「已定位」，不删旧注

```
【勘误 2026-09-30 · E-2-S 施加点已定位 · R-03/R-06】前注「Verses 实际施加点未定位（全 .text *8+0xA0/0xB0 索引访存 0 命中）」→ 补记订正：**已定位 8 处 FPU 索引访存**（旧扫描 0 命中因未覆盖 `fmul/fld qword [reg+armor*8+0xA0]` 的 DC/DD 形态）：
V1 `0x48923D fmul [edi+edx*8+0xA0]`（伤害缩放，属主 `MapClass::GetTotalDamage @ 0x489180` 正伤害分支，R-06 §2）；
V2a/V2b `0x6F36FE/0x6F3731`、V4 `0x6FCB6A`（有效性 `Verses[armor]!=0`）；
V3 `0x6F7D3D`（阈值 >0.02）、V5 `0x708AF7`（阈值 >0.01）；
V6a/b/c `0x70CEB2/0x70CEC7/0x70CF49`（威胁/伤害加权，含 fchs）。
惯用式：`armor=[TechnoTypeClass+0x9C]`（0..10），`warhead=[WeaponTypeClass+0xAC]`（R-06 §1）。
`ReceiveDamage 0x701900` / `DamageArea 0x489280` / `Detonate 0x4690B0` **本体均无** Verses 访存（维持 R6-E3）。
权威：`docs/re/warhead_abi_verses_deform_deep_dive.md` §3；`docs/re/warhead_abi_residuals_deep_dive.md` §1–§3。原文保留不删字。
```

> 【勘误 2026-09-30 · R-E07 · errata_sync】上述 E-2-S 补丁块「已定位 8 处 FPU 索引访存」及块内「8 处」字样系计数笔误，粘贴时应同步改 **9 处**（块内站点列表 V1/V2a/V2b/V3/V4/V5/V6a/V6b/V6c 已列全 9 项，计数字样与列表不一致）。权威：warhead_verses_residual_p2.md:18,58。原文保留不删字。

### 2.3 E-ABI-AC · Warhead ABI 残余收口（新增）

- **落点**：无既有冻结行强制对应；建议在 `weapons_damage_production.md` 布局表（L126-128 区域）或 ATLAS §16.3 解冻时粘贴
- **前 40 字符锚点（可选，L126 区）**：``| *(AbstractTypeClass 尾)* | `0xA8` | | 基类尺寸推算值 |``

```
【勘误 2026-09-30 · E-ABI-AC · R-06】ABI 残余收口（新增条目，不改既有行）：
① Verses 惯用式中的 `obj+0xAC` 宿主 = **WeaponTypeClass.Warhead**（`WarheadTypeClass*`）；
   BulletClass+0xAC 是 `Type`（BulletTypeClass*），其 WH 在 **+0x128**——禁止混淆。
   锚点：WeaponTypeClass ctor `0x771CA9 mov [esi+0xAC],ebx`；LoadFromINI `0x772992 mov [esi+0xAC],eax`；
   BulletClass::Construct `0x4664FB/0x4664DC`。
② V1 块 `0x4891C6` **不是独立函数**，是 `MapClass::GetTotalDamage @ 0x489180` 的正伤害分支入口
   （`jge 0x4891C6`；函数边界 `0x489180..0x48926A`，三出口均 `ret 8`）。
③ `ObjectTypeClass/TechnoTypeClass+0x9C = Armor` 枚举 0..10（11 档，装载 `0x5F94CD`，解析表 `0x7E5210`）。
④ [冲突-轻微] HouseClass::Array：YRpp 记 `0xA80228`，二进制内部布局偏移差 +4/+0x10
   （`[0xA8022C]=Items`、`[0xA80238]=Count`）——字段级钉死仍 [待实测]。
权威：`docs/re/warhead_abi_residuals_deep_dive.md` §0–§4。原文保留不删字。
```

### 2.4 E-2 复核注（可选，贴在全文统一订正声明后）

```
【复核 2026-09-30 · R-03】E-2 偏移订正（+0xB0→+0xA0，Verses 覆盖 +0xA0..+0xF7）经 R 轨字节级复核**通过**：
装载器锚点 `0x75DE06/0x75DE0C/0x75DE48/0x75DE52` 与默认值串 `0x847C40` 一致；`+0xB0=Verses[2]` 维持。
无需改动 E-2 各处补丁块本身。权威：`docs/re/warhead_abi_verses_deform_deep_dive.md` §2。
```

---

## 3. 明确不做的动作

| 项 | 原因 |
|---|---|
| 就地改 `weapons_damage_production.md` / `ARCHITECTURE_ATLAS.md` / 任一 `*_deep_dive.md` | 冻结；R 轨 deep_dive 为对方写域 |
| 改 E-1（Blitter）补丁 | R 轨本批无 Blitter 新结论，无冲突 |
| 改 E-ZC11-7a/b/c/d | 与 R-02 一致，仅机制加强；崩溃归因不翻案 |
| 把 R-01「不含 0.71875」写成 fog 冻结文档勘误 | fog 文档候选 C1 原文是 [推演] 首选，R-01 否定后走**接口/待办降权**（`iface` §9.2），不改源 |
| 改 `tools/check_except_gate.py` / `bench_*.py` | harness 代码归 M 实现卡（T18/T19 并行）；本文件只出**判据提案** |

---

## 4. except_watch 判据增强提案（机制增量，非勘误；落地归 harness 卡）

> 来源：`docs/re/sbh_freelist_deep_dive.md` §7（L282-314）；**只提案不改脚本**。

| 判据 | 内容 | 优先级 | R 源 |
|---|---|:---:|---|
| 毒族 | `POIS_FE00FFFF=0xFE00FFFF`（P0）；`POIS_FFFF0000`（P1）；`POIS_XYFFFFxx` 高16∈{FE00,FF00,FFFF}×低16∈{0000,FFFF,FE00}（P1）；`POIS_SELFFREE` next==self 非 head（P2） | P0/P1 | L297-305 |
| 扫描位点 | heap_info freelist-head 数组（`head(g,c)=heap_info+0x144+g*0x204+c*8`，`head+4=next`）必查；崩溃样本毒址=`head(7,4)+4` | P0 | L21,166 |
| size-class 签名 | 毒 class∈{0..8}→小结构/名表节点；{19,22,28}→Particle/Bullet/Anim；{63}→page 顶 0xFF0 合并异常；**class=4（80B/req 57..72）=本次** | P0 | L20,112,307-314 |
| EIP 集合 | 崩溃读点 `0x7CFC9F`（`mov ecx,[edx]`）；入链/摘链传播点 `0x7CFD4C`/`0x7CFD52`/`0x7CFD26-0x7CFD39` | P0 | L74-83,278 |
| 全局状态 | `[0xB78B8C]` cur region / `[0xB78B94]` count / `[0xB78B98]` base / `[0xB78B9C]` hHeap | P1 | L137-144 |
| 位图口径 | class 空闲位 **bit=31-class（MSB=class0）**，分 lo/hi 半 dword | P1 | L16,99-101 |
| 对象归因 | class 4 在 U0200 下对应对象类型 [待实测]——门禁只记 (class,ret_addr) 直方图，不写死业务名 | P2 | L26,322 |

---

## 5. §九 草稿（供 Lead 台账合并，两轨只交草稿）

1. **[P0] E-8 收口**：Deform=Warhead+0x98（double）定谳，+0xA8=Verses[1]；「不得按 +0xA8 读写 Deform」禁令解除。补丁块 E-8-D 就绪。
2. **[P0] Verses 施加点已定位**：8 处 FPU（主施加 V1 `0x48923D`，属主 `MapClass::GetTotalDamage`）；E-2 偏移复核通过；E-2-05/E-7-02「未定位」补记 E-2-S。**伤害相关优化**（Verses 表驱动缩放、有效性预判、威胁加权）静态前置已齐，**放行仍要** ZC-RE1 段 A 真机命中确认 + INI 对照（动态 [待实测]）。

> 【勘误 2026-09-30 · R-E07 · errata_sync】上条「8 处 FPU」→ 订正为 **9 处**（V1/V2a/V2b/V3/V4/V5/V6a/V6b/V6c）。原文保留不删字。
3. **[P1] E-ABI-AC 新增**：`+0xAC=WeaponTypeClass.Warhead`、Armor@+0x9C、HouseClass Array 轻微偏移差。
4. **[P0] SBH 与 E-ZC11 一致加强**：毒 class=4 freelist-head；主候选 UAF 写穿 next；H1–H6 钩子与毒族签名提案交 harness 卡。
5. **[P1] LightConvert 否定 C1**：表公式不含 0.71875、非 M1 向灰；段 G 动态 dump 降为「增强置信」；迷雾第一段剩余=DrawTile 光照链/环境光（R-04）。

---

## 6. 产物索引

| 产物 | 路径 |
|---|---|
| 本文（对照 + 补丁块 + 判据提案 + §九草稿） | `docs/re/errata_from_rtrack.md` |
| by_file 追加（E-8-D / E-2-S / E-ABI-AC / E-2 复核注） | `out/re_work/errata_patches/by_file/weapons_damage_production.md.patch` |
| by_file 追加（ATLAS §16.3 施加点升级注，可选） | `out/re_work/errata_patches/by_file/ARCHITECTURE_ATLAS.md.patch` |
| by_file 追加（E-1 维持声明） | `out/re_work/errata_patches/by_file/blitter_microkernel_deep_dive.md.patch` |
| 对接报告 | `out/re_work/rtrack_bridge/bridge_report_rtrack.md` |
| 接口增量 | `docs/re/iface_mimo_re.md` §9（文末追加） |
| ZCode 增量附录 | `out/re_work/dispatch_v30/prompt_zcode_appendix_rtrack.txt` |
