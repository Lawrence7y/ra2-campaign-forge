# 落地前预检订正清单 + 模板 · E-1～E-4
# Preflight E-1..E-4 Corrections · R-PRE-E14

> **文档标识**：`docs/re/preflight_e1_e4_corrections.md`  
> **任务**：R-PRE-E14（PREFLIGHT-AUDIT 字节 17/17 PASS 后，落地前须先订正的 4 处文档缺口）  
> **权威依据**：`docs/re/landing_pack_preflight_audit.md` §四勘误表 + §八 §9.2 须先订正清单  
> **配套工作区**：`out/re_work/re_sprint/R_pre_e14/`（模板 / 执行清单 / 证据索引）  
> **既有补丁块**：`out/re_work/errata_patches/by_file/*.patch`（本清单与之对齐，不重复改写源 patch）  
> **写作用域**：仅本文 + `out/re_work/re_sprint/R_pre_e14/**`；**未改** landing_pack 本体 / 总表 / 源 deep_dive / ra2render / 台账 / 看板

---

## 〇、总则

| 项 | 口径 |
|:---|:---|
| 原则 | **原文保留不删字**；仅追加【勘误】标注块或插入状态注记行 |
| 适用面 | E-1/E-2 = 跨文档知识风险（源 deep_dive 残留错误）；E-3 = 状态标注缺口（总表）；E-4 = 机械写入完整性缺口（总表） |
| landing_pack | **本体不改**。审计 C-7/C-8 确认 landing_pack **未写** Blitter=12B / Verses=+0xB0；E-3 可在 gap 包**可选加注**状态行（见 §3.3） |
| 字节面 | **无订正项**。P-1.1～P-6.2 原字节 17/17 PASS，实施方按总表机械写入不会踩字节坑 |
| 执行顺序 | E-1 → E-2（P0 知识风险，须在任何 Blitter/Verses 实现前完成）→ E-3（P0 状态）→ E-4（P1 完整性） |
| 禁写 | 台账、看板、`ra2render/**`、`ra2youli/**`、既有 landing_pack 本体 |

---

## 一、订正清单（每条：旧 / 新 / 证据 / 执行步骤）

### E-1 · Blitter 实例尺寸：统一 12B → 分级 4/8/12/16，P0 微内核 = 8B

| 字段 | 内容 |
|:---|:---|
| **编号 / 优先级** | **E-1 / P0**（产品决策阻断） |
| **目标文件** | `docs/re/blitter_microkernel_deep_dive.md`（L40、L45 图注；L48 隐含布局由 L45 标注覆盖） |
| **影响面** | 实施方按 12B 写 Blitter 结构体 → P0 路径 `this+0x08` 越界 4 字节 → 堆破坏（不保证立刻崩溃） |
| **landing_pack** | 未写错（审计 C-7），**不改** |

#### 旧（原文保留不删）

**E-1-a · L40**（锚点：`在西木引擎的工厂函数（`0x0048FAF8`–`0x0048FC98`）与析构`）

> 在西木引擎的工厂函数（`0x0048FAF8`–`0x0048FC98`）与析构函数（`0x0049A760`–`0x0049A860`）中，所有 Blitter 对象的分配大小统一为 **12 字节**（`push 0x0c; call operator new`）。

**E-1-b · L45**（锚点：`[ Blitter 内存对象布局 (12 字节) ]`）

> ```
> [ Blitter 内存对象布局 (12 字节) ]
> +0x00: void* __vfptr          (4 字节虚表指针)
> +0x04: 变体核心参数            (4 字节，语义分化，见下表)
> +0x08: 变体辅助参数 / 掩码      (4 字节)
> ```

#### 新（订正后口径）

- **分配尺寸按成员数分级 4 / 8 / 12 / 16 四级**（`push <size>; call operator new (0x007C8E17)`），**不存在「统一 12 字节」**。
- **P0 微内核（步兵/载具本体与影子主路径）= 8 字节**：仅 `+0x00` vtable + `+0x04` 一槽，**无 `+0x08`**。
- 12 字节仅属 Lucent/ZRemap/Alpha 双成员族（vtable + 2 槽）。
- **禁止**按 12B 声明结构体后访问 `this+0x08`（在 8B 对象上越界 4 字节）。
- 同文 L1028-1037 §8.1.2 已自勘误为 4/8/12/16，**以 L1029 为准**，L40/L45 为残留。

#### 证据

| # | 证据 | 内容 |
|:---:|:---|:---|
| 1 | `docs/re/blitter_microkernel_deep_dive.md:1028-1037` | 同文 §8.1.2「4 字节 / 8 字节 / 12 字节 / 16 字节」四级规格（自勘误） |
| 2 | `docs/re/ARCHITECTURE_ATLAS.md` §1.2〔勘误 R1〕; L448,L470 | 「8 字节：单成员变体——全部 P0 微内核均属此类」；按 12B 声明 `this+0x08` 越界 4 字节 |
| 3 | `docs/re/landing_pack_preflight_audit.md` C-7 / E-1 / §五 | 「源文档残留错误」；landing_pack 未写 12 |
| 4 | `docs/re/re_sprint_S13_report.md:17` | 4/8/12/16 分级旁证 |
| 5 | `out/re_work/errata_patches/by_file/blitter_microkernel_deep_dive.md.patch` | 既有可粘贴补丁块 E-1-a/b/c |

#### 执行步骤

1. **冻结确认**：Lead 解冻 `blitter_microkernel_deep_dive.md`（L1 冻结源）。
2. **定位**：`rg -n "所有 Blitter 对象的分配大小统一为"` 命中 L40；`rg -n "Blitter 内存对象布局"` 命中 L45。
3. **E-1-a**：在 L40 行末追加【勘误】标注块（模板见 `R_pre_e14/templates/E-1.md`）。
4. **E-1-b**：在 L45 围栏块**前**插入标注行（同上模板）。
5. **实施侧同步**（非源文档）：Blitter 结构体按**实测尺寸**声明；P0 路径用 8B 布局，禁读 `this+0x08`。
6. **验收**：
   - [ ] 原文两句仍在（`rg` 仍命中「统一为 **12 字节**」「(12 字节)」）
   - [ ] 新增【勘误 2026-09-29 · E-1】块 ≥2 处
   - [ ] 只增不删（Compare-Object removed=0）
   - [ ] 全库实施结构体无「Blitter 12B + this+0x08」组合引用

---

### E-2 · WarheadTypeClass.Verses：+0xB0 → +0xA0

| 字段 | 内容 |
|:---|:---|
| **编号 / 优先级** | **E-2 / P0**（静默错位 8 个 double） |
| **目标文件** | `docs/re/weapons_damage_production.md`（审计清单 8 处：L19,128,142,208,215,229,563,845；另有 E-7 扫描新增 L473/L581） |
| **影响面** | 按 `+0xB0` 写护甲乘数 → 把 `Verses[2]` 当数组起点，**静默错位 8 个 double**；按 `+0xB0` 读 11 项 → 越读 `+0xF8…+0x107` 非 Verses 字段 |
| **混淆红线** | 勿与超武 `SuperClass` / 总表 `SW+0xB0 RechargeTime` 混淆（不同类不同字段） |
| **landing_pack** | 未写 Verses 偏移（审计 C-8），**不改** |

#### 旧（原文保留不删 · 代表行）

| 行 | 旧文（摘录） |
|:---:|:---|
| L19 | `WarheadTypeClass.Verses[11]`（`double`）位于 **Warhead+0xB0** |
| L128 | \| **`Verses[11]`** \| **`0xB0`** \| double[11] \| |
| L142 | ``Verses[i]`` 的地址 = `Warhead + 0xB0 + i*8` |
| L208 | `护甲乘数：Warhead->Verses[armor]（+0xB0+armor*8）× damage` |
| L215 | 乘 `qword[warhead+0xB0+armor*8]` |
| L229 | \| `Verses` \| `0xB0..0x100` \| 护甲乘数表 \| |
| L563 | `VersesCalc["Verses 护甲乘数结算 (+0xB0+armor*8)"]` |
| L845 | 已确证 Verses 位于 `Warhead+0xB0+armor*8` |

（完整旧文见 `R_pre_e14/templates/E-2.md` 与 `errata_patches/by_file/weapons_damage_production.md.patch`。）

#### 新（订正后口径）

- **`Verses[0]` 起于 `Warhead+0xA0`**，覆盖 `+0xA0…+0xF7`（11 × 8B = 88B double 数组）。
- **`+0xB0` 实为 `Verses[2]`**（Plate/装甲档位之一），不是数组起点。
- 寻址公式：`Warhead + 0xA0 + i*8`；范围速查 `0xA0..0xF7`（非 `0xB0..0x100`）。
- 连带（E-8，非本条主项但须知）：`Deform` 旧记 `+0xA8` 与 `Verses[1]` 重叠，闭环前**不得按 `+0xA8` 读写 Deform**。
- 施加点：R-03/R-06 已定位 8 处 FPU 索引访存（E-2-S），含 `0x48923D fmul [edi+edx*8+0xA0]`。

#### 证据

| # | 证据 | 内容 |
|:---:|:---|:---|
| 1 | `docs/re/ARCHITECTURE_ATLAS.md` §16.3〔勘误 R6-E2〕L3250 | 「`Verses[0]` 落在 `+0xA0`…`+0xB0` 实为 `Verses[2]`」 |
| 2 | 同上 L3372-3374 | 装载器锚点 `0x0075DE06` = Verses 起始 `+0xA0`；默认值串 `0x00847C40`；倍率常数 `0x007E3808` |
| 3 | `docs/re/warhead_abi_verses_deform_deep_dive.md` §2 | R 轨字节级复核通过（E-2 复核注） |
| 4 | `docs/re/landing_pack_preflight_audit.md` C-8 / E-2 / §五 | 源文档残留错误；landing_pack 未写 Verses |
| 5 | `out/re_work/errata_patches/by_file/weapons_damage_production.md.patch` | 既有补丁块 E-2-01…08 + E-7 + E-8 + E-2-S |

#### 执行步骤

1. **冻结确认**：Lead 解冻 `weapons_damage_production.md`。
2. **定位**：`rg -n "Warhead\+0xB0|\+0xB0\+armor|0xB0\.\.0x100"` 命中审计清单各处。
3. **逐处粘贴**【勘误】块（模板 E-2.md；同文件多处合并一次开封）。
4. **E-7 补扫**：L473/L581 为清单外命中，一并加注（E-2 主清单 8 处 + E-7 2 处）。
5. **实施侧同步**：Verses 读写一律 `+0xA0 + armor*8`；禁止 `+0xB0` 当起点。
6. **验收**：
   - [ ] 原文 `Warhead+0xB0` 各行仍在（原文保留）
   - [ ] 新增【勘误 · E-2】覆盖 8+2 处
   - [ ] `rg "Verses\[0\].*\+0xA0|\+0xA0.*Verses"` 可命中订正口径
   - [ ] 实施代码/补丁无 `warhead+0xB0+armor*8` 作为 Verses 起点

---

### E-3 · 总表 P-2.1～P-2.3 增注「ra2render 代码轨未落地」
> 【W3 勘误 · W3-A6/ISSUE-STALE-P2-LANDING】改前：P-2.1～P-2.3 增注「ra2render 代码轨未落地；改后：P-2.1~P-2.3 裂缝三点 NOP 已于 09-30 完整落地进 blitter_hooks.cpp:3273-3287 并完成三处 DLL 同步；真机 A3 验收 PASS (带窗口限定)。；依据：ra2render/blitter_hooks.cpp:3273-3287, 3417-3446; out/re_work/zcode_live/gap_p21_a3/RESULT_GAP_P21_A3.md:18-23；分级：P0

| 字段 | 内容 |
|:---|:---|
| **编号 / 优先级** | **E-3 / P0**（实施方误以为已装、跳过写入 → 裂缝保护缺口） |
| **目标文件** | `docs/re/pending_execution_master_table.md` §一 P-2.1～P-2.3（L44-46） |
| **性质** | **状态注记（非规格变更）**；字节面 17/17 PASS，规格本身无需改 |
| **landing_pack** | gap 规格完整；**可选**在 gap 包加状态注记（见 §3.3） |

#### 旧（原文保留不删）

L44-46 三行均按「可安装补丁」列出 `90 90 90 90 90 90`（6B NOP），**未标注代码轨落地状态**：

- L44 锚点：`| **6** | **P-2.1** | M-10 Gap1 局部开图 | 裂`
- L45：P-2.2 @ `0x00577EC5` / `89 B8 34 01 00 00` → `90×6`
- L46：P-2.3 @ `0x00577B60` / `89 98 34 01 00 00` → `90×6`

#### 新（订正后口径）

状态注记（追加，不改规格列）：

> **纸面规格已定谳、ra2render 代码轨当前 0 命中（未落地）**。全源码 grep `568273/577EC5/577B60` 无命中。⇒ 实施方**不可误以为已装而跳过写入**；PsychicReveal 仍清 `Cell+0x134`，裂缝保护缺口仍在。

#### 证据

| # | 证据 | 内容 |
|:---:|:---|:---|
| 1 | `docs/re/ARCHITECTURE_ATLAS_REV.md` §20.6；L21,L104 | 「3×6B NOP 未落地 ⇒ PsychicReveal 经 `0x568273` 清 `Cell+0x134`，裂缝永久静默失能（P0）」；`ra2render/**` 检索 `568273/577EC5/577B60` 现 0 命中 |
| 2 | `docs/re/landing_pack_preflight_audit.md` C-9 / E-3 / §五 | 「总表状态缺口」；「ra2render 中 3×6B NOP 尚未落地」未收录 |
| 3 | `out/re_work/re_sprint/R_card_inv/cards_inventory.json` | ZC-GAP-P21/P223 收据在 **zcode_live 二进制轨**（已落地）；与 ra2render **代码轨** 0 命中并存——两轨勿混淆 |
| 4 | `out/re_work/errata_patches/by_file/pending_execution_master_table.md.patch` | 既有可粘贴补丁块 E-3 |

#### 执行步骤

1. **冻结确认**：Lead 解冻 `pending_execution_master_table.md`。
2. **定位**：L44-46（或 `rg -n "P-2\.[123]"` 于 §一表）。
3. **插入/追加**状态注记（模板 E-3.md）：可在表头行后插独立注记行，或三行备注列末尾追加。
4. **可选**：gap landing_pack 状态注记（§3.3 模板）。
5. **验收**：
   - [ ] 总表 P-2.1～P-2.3 旁可见「ra2render 代码轨未落地 / grep 0 命中」
   - [ ] 原规格列（VA/原字节/替换 `90×6`）**未改动**
   - [ ] 不出现「已安装 / skip」误导口径

---

### E-4 · 总表 P-6.2 原字节截断 → 补全可回滚窗口

| 字段 | 内容 |
|:---|:---|
| **编号 / 优先级** | **E-4 / P1**（回滚表无法机械还原） |
| **目标文件** | `docs/re/pending_execution_master_table.md` §一 P-6.2（L56） |
| **landing_pack** | L4 规格已有完整窗口（`l4_vision_dirty_final_spec.md` 等），**不改** |

#### 旧（原文保留不删）

L56 原字节列（锚点：`| **18**| **P-6.2** | L4 视口翻转格外扩 | 视口渲染调`）：

> `A1 F4 F7 87 00 ...` | 原生 API 调用（非 Hook） | N/A | 原生 API 驱动

问题：以 `...` 截断，**不足以机械回滚**。

#### 新（订正后口径）

**可回滚窗口（已实测确认）**：

```text
VA 0x006DA7D0 / FileOffset 0x002DA7D0
入口 5B：  A1 F4 F7 87 00          ; mov eax, [0x0087F7F4]
序言续：    83 EC 0C 85 C0          ; sub esp, 0xC; test eax, eax
扩展窗 15B：A1 F4 F7 87 00 83 EC 0C 85 C0 53 56 57 8B D9 0F
```

- 「原生 API 调用（非 Hook）」项若不写字节，应标 **N/A（非字节补丁）**，不得留 `...`。
- 本项为**文档完整性**订正，不是补丁变更。

#### 证据

| # | 证据 | 内容 |
|:---:|:---|:---|
| 1 | `out/re_work/landing_audit/audit_json.json`（P-6.2 节点） | `actual_window` = `A1 F4 F7 87 00 83 EC 0C 85 C0 53 56 57 8B D9 0F` |
| 2 | `out/re_work/landing_audit/preflight_claims.txt` L22 | `0x006DA7D0 = A1 F4 F7 87 00 # P-6.2 ORIG PASS` |
| 3 | `docs/re/l4_vision_dirty_final_spec.md:60-61` | 反汇编窗：`A1 F4 F7 87 00` + `83 EC 0C` |
| 4 | `docs/re/ARCHITECTURE_ATLAS.md:883-884` | 同款反汇编 |
| 5 | `docs/re/landing_pack_preflight_audit.md` P-6.2 行 / C-11 / E-4 | 「PASS\*」「截断」 |
| 6 | `out/re_work/errata_patches/by_file/pending_execution_master_table.md.patch` | 既有可粘贴补丁块 E-4 |

#### 执行步骤

1. **冻结确认**：Lead 解冻 `pending_execution_master_table.md`（与 E-3 同文件，合并一次开封）。
2. **定位**：L56 / `rg -n "A1 F4 F7 87 00"`。
3. **追加**【勘误】块（模板 E-4.md），写入完整窗口或标 N/A。
4. **验收**：
   - [ ] 总表 P-6.2 原字节列可机械还原（至少入口 5B + 序言注记）
   - [ ] 原文 `A1 F4 F7 87 00 ...` 保留不删
   - [ ] 回滚表/实施脚本按订正窗口可对拍 `gamemd.exe`

---

## 二、执行顺序与依赖

```text
W1 (P0 知识):  E-1（blitter） ──┐
                E-2（weapons） ──┴─→ 实施侧结构体/寻址同步
W2 (P0 状态):  E-3（总表 P-2 状态注记）
W3 (P1 完整):  E-4（总表 P-6.2 字节窗）  ← 与 E-3 同文件，合并开封
可选:          §3.3 gap landing_pack 状态注记
```

- E-1 / E-2 相互独立，可并行。
- E-3 / E-4 同文件，**一次开封两块都贴**，减少冻结源写次数。
- 全部完成前，**不得**开始依赖 Blitter 结构体 / Verses 寻址 / Gap-NOP 写入的实现工作。

---

## 三、模板（可粘贴）

> 完整分文件模板见 `out/re_work/re_sprint/R_pre_e14/templates/`。以下为汇总。

### 3.1 E-1 模板

**E-1-a（L40 行末追加）**：

```text
【勘误 2026-09-29 · E-1 · landing_audit】原文「所有 Blitter 对象的分配大小统一为 12 字节」→ 订正为：**按成员数分级 4/8/12/16 四级分配**（`push <size>; call operator new (0x007C8E17)`），**P0 微内核（步兵/载具本体与影子主路径）实测仅 8 字节**。按 12B 声明 `this+0x08` 将**越界 4 字节**（堆块尾部踩踏）。权威：`ARCHITECTURE_ATLAS.md` §1.2〔勘误 R1〕+ 同文 L1029 自勘误 + `re_sprint_S13_report.md:17`。原文保留不删字。
```

**E-1-b（L45 围栏块前插入）**：

```text
【勘误 2026-09-29 · E-1 · landing_audit】下图标题「(12 字节)」→ 订正为：**尺寸按成员数分级 4/8/12/16**；P0 微内核 = **8 字节**（仅 `+0x00` vtable + `+0x04` 一槽，**无 `+0x08`**）。Lucent/ZRemap/Alpha 族才是 12 字节（vtable + 2 槽）。按 12B 统一布局图声明结构体，在 8B 对象上访问 `this+0x08` 即越界 4 字节。原文围栏保留不删字。
```

### 3.2 E-2 模板（统一声明 + 逐处）

**统一声明（文首或首次命中处）**：

```text
【勘误 2026-09-29 · E-2 · landing_audit】本文多处将 `WarheadTypeClass.Verses[11]` 记为 `Warhead+0xB0` / `+0xB0+armor*8`，**偏移错误**。实证：**`Verses[0]` 起于 `+0xA0`**（覆盖 `+0xA0…+0xF7`，11 个 double），**`+0xB0` 实为 `Verses[2]`**（Plate/装甲档位之一）。按 `+0xB0` 写会把第 3 档护甲乘数当数组起点，**静默错位 8 个 double**；按 `+0xB0` 读「全部 11 项」会越读 `+0xF8…+0x107` 非 Verses 字段。勿与超武 `SuperClass` 的 `SW+0xB0 RechargeTime` 混淆（不同类不同字段）。权威：`ARCHITECTURE_ATLAS.md` §16.3〔勘误 R6-E2〕，装载器锚点 `0x75DE06/0x75DE0C/0x75DE48/0x75DE52` + 默认值串 `0x847C40`。下文逐处标注，原文保留不删字。
```

**逐处短标（8+2 处行末）**：

```text
【勘误 2026-09-29 · E-2】Verses 偏移 +0xB0 → **+0xA0**（`Verses[0]` 起于 `+0xA0`；`+0xB0`=`Verses[2]`）。原文保留不删字。
```

> 逐处细分措辞（含 E-7/E-8 连带）以 `errata_patches/by_file/weapons_damage_production.md.patch` 为准。

### 3.3 E-3 模板

**总表（L44-46 旁插入或备注列追加）**：

```text
【勘误 2026-09-29 · E-3 · landing_audit】状态注记（非规格变更）：P-2.1～P-2.3 三处 3×6B Gap NOP **纸面规格已定谳、ra2render 代码轨当前 0 命中（未落地）**。全源码 grep `568273/577EC5/577B60` 无命中（`ARCHITECTURE_ATLAS_REV` §20.6）。⇒ 实施方**不可误以为已装而跳过写入**；PsychicReveal 仍清 `Cell+0x134`，裂缝保护缺口仍在。字节面 17/17 PASS，规格本身无需改，仅补状态标注。原文保留不删字。
```

**landing_pack 可选加注**（`landing_pack_gap_p223.md` / `landing_pack_gap_spysat.md` 备注区；**非必须**）：

```text
【状态注 2026-09-29 · E-3 · 预检】本包 3×6B Gap NOP 纸面规格已定谳；**ra2render 代码轨 grep `568273/577EC5/577B60` 当前 0 命中（未落地）**。勿因「规格已入库」跳过写入。详见 `docs/re/preflight_e1_e4_corrections.md` E-3。
```

### 3.4 E-4 模板

**总表 L56 行末追加**：

```text
【勘误 2026-09-29 · E-4 · landing_audit】原文「`A1 F4 F7 87 00 ...`」以 `...` 截断，**不足以机械回滚**。订正为：至少补全入口 5 字节 `A1 F4 F7 87 00`，并标注函数序言后续 `83 EC 0C 85 C0`（已实测确认；扩展窗 15B=`A1 F4 F7 87 00 83 EC 0C 85 C0 53 56 57 8B D9 0F`）。替换类型「原生 API 调用（非 Hook）」项若不写字节，应标 **N/A（非字节补丁）** 而非留 `...`。原文保留不删字。
```

---

## 四、landing_pack 处置裁决（本体不改）

| 包 / 文档 | 与 E-1..E-4 关系 | 裁决 |
|:---|:---|:---|
| 全部 `landing_pack_*.md` | 未写 Blitter=12B、未写 Verses=+0xB0（审计 C-7/C-8） | **不改** |
| `landing_pack_gap_p223.md` / `landing_pack_gap_spysat.md` | 规格完整；缺的是 ra2render 落地状态 | **可选加注** §3.3 状态行 |
| `landing_pack_l4_opt1_checklist.md` 等 L4 包 | P-6.2 完整窗口已在细规格 | **不改** |
| `pending_execution_master_table.md` | E-3/E-4 目标文件（非 landing_pack） | **按模板加注**（Lead 解冻后） |
| `blitter_microkernel_deep_dive.md` / `weapons_damage_production.md` | E-1/E-2 目标文件（源文档） | **按模板加注**（Lead 解冻后） |

---

## 五、验收总表（执行后勾选）

| # | 检查项 | 期望 |
|:---:|:---|:---|
| 1 | 原文保留 | E-1 两句 / E-2 各行 / E-3 三行规格列 / E-4 `A1 F4 F7 87 00 ...` **均可 rg 命中** |
| 2 | 只增不删 | Compare-Object removed=0；added 含【勘误】 |
| 3 | E-1 覆盖 | blitter L40+L45 ≥2 处勘误块 |
| 4 | E-2 覆盖 | weapons ≥8 处（含 E-7 两处则 10） |
| 5 | E-3 状态 | 总表可见「ra2render 未落地 / grep 0 命中」 |
| 6 | E-4 窗口 | 总表 P-6.2 可机械还原（≥5B 入口 + 序言注） |
| 7 | landing_pack | 本体哈希不变（可选加注除外） |
| 8 | 禁写面 | 台账 / 看板 / `ra2render/**` 未改动 |
| 9 | 实施同步 | Blitter 8B / Verses +0xA0 已进入实施结构体与寻址 |

---

## 六、机读与配套产物

| 文件 | 内容 |
|:---|:---|
| `out/re_work/re_sprint/R_pre_e14/README.md` | 工作区索引 |
| `out/re_work/re_sprint/R_pre_e14/correction_list.md` | 本清单镜像（执行用精简版） |
| `out/re_work/re_sprint/R_pre_e14/templates/E-1.md` … `E-4.md` | 分条可粘贴模板 |
| `out/re_work/re_sprint/R_pre_e14/exec_checklist.md` | 执行勾选清单 |
| `out/re_work/re_sprint/R_pre_e14/evidence_index.md` | 证据路径索引 |
| `out/re_work/errata_patches/by_file/*.patch` | 既有补丁块（历史，未改） |
| `out/re_work/landing_audit/*` | 字节面复核产物（历史，未改） |

---

## 七、签署

| 项 | 值 |
|:---|:---|
| 任务 | R-PRE-E14 |
| 产出 | 订正清单 + 模板（E-1～E-4：旧/新/证据/执行步骤） |
| landing_pack | 本体未改（可选状态注记见 §3.3） |
| 字节面 | 无订正项（17/17 PASS 维持） |
| 残余风险 | Lead 解冻前源文档旧值仍在；实施方须以本清单 / 总表最终值为准，**禁止**绕过直接抄 `blitter_microkernel_deep_dive.md` L40/L45 或 `weapons_damage_production.md` +0xB0 旧段落 |
