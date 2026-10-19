# 勘误补丁块总表 E-1～E-9 + T1 标签插入包
# Errata Patch Blocks · Landing Pack Preflight Audit

> **文档标识**：`docs/re/errata_patch_blocks_E1E2.md`
> **生成日期**：2026-09-29
> **任务性质**：文档勘误准备 —— **只登记不就地改**（`docs/re/*.md` L1 冻结）
> **上游依据**：`docs/re/landing_pack_preflight_audit.md` §四 勘误表 E-1～E-6 + 本次全库扫描新增 E-7～E-9
> **分文件补丁**：`out/re_work/errata_patches/by_file/*.patch`
> **写作用域**：仅新建本文 + `out/re_work/errata_patches/**`；源文档 / 台账 / ra2render 均未改动

---

## 〇、总览（先看这里）

| 编号 | 主题 | 优先级 | 命中文件 | 命中处数 | 状态 |
|:---:|:---|:---:|:---|:---:|:---|
| **E-1** | Blitter 尺寸「统一 12 字节」→ 4/8/12/16，P0=8B | **P0** | `blitter_microkernel_deep_dive.md` | 2（L40/L45） | 补丁块就绪 |
| **E-2** | `Verses` 偏移 `+0xB0` → `+0xA0` | **P0** | `weapons_damage_production.md` | 8（清单内） | 补丁块就绪 |
| **E-3** | ra2render 3×6B Gap NOP 未落地（状态注记） | **P0** | `pending_execution_master_table.md` | 3（L44-46） | 补丁块就绪 |
| **E-4** | P-6.2 原字节截断 `...` | **P1** | `pending_execution_master_table.md` | 1（L56） | 补丁块就绪 |
| **E-5** | `EnableMinimapFog`「ini 现值 1」过时 | **P2** | `pending_execution_master_table.md` | 1（L454） | 补丁块就绪 |
| **E-6** | 细规格文件名 `landing_pack_equivalence_…` | **P3** | 任务书/引用 | 0（提示） | 仅提示 |
| **E-7** | E-2 清单外新增 Verses `+0xB0` 命中 | **P0** | `weapons_damage_production.md` | 2（L473/L581） | 补丁块就绪 |
| **E-8** | `Deform +0xA8` 与 `Verses[1]` 重叠 | **P1** | `weapons_damage_production.md` | 1（L127） | 补丁块就绪 |
| **E-9** | ATLAS mermaid 残留「分配 12 字节」 | **P1** | `ARCHITECTURE_ATLAS.md` | 1（L377） | 补丁块就绪 |
| **T1** | 46 节证据等级标签插入 | **P1** | `ARCHITECTURE_ATLAS.md` | 46 | 插入块就绪 |

**合计**：勘误条目 **9 条** + T1 标签包；行级补丁/插入块 **65 处**；涉及冻结源文档 **4 份**。

---

## 一、统一勘误清单

| 编号 | 位置 | 原文（保留） | 应为 | 影响面 | 优先级 |
|:---:|:---|:---|:---|:---|:---:|
| **E-1** | `blitter_microkernel_deep_dive.md:40,45` | 「所有 Blitter 对象的分配大小统一为 **12 字节**」「Blitter 内存对象布局 (12 字节)」 | **按成员数分级 4/8/12/16**；**P0 微内核对象 = 8 字节**。按 12B 声明 `this+0x08` **越界 4 字节** | 按 12B 写 Blitter 结构体 → 越界读写 | **P0** |
| **E-2** | `weapons_damage_production.md:19,128,142,208,215,229,563,845` | `WarheadTypeClass.Verses[11]` 位于 **`Warhead+0xB0`** / `+0xB0+armor*8` | **`Verses[0]` 起于 `+0xA0`**（覆盖 `+0xA0…+0xF7`）；`+0xB0` 实为 `Verses[2]` | 按 +0xB0 写会静默错位 8 个 double | **P0** |
| **E-3** | `pending_execution_master_table.md` §一 P-2.1～P-2.3 | 按「可安装」列出 3×6B NOP | 增注：**ra2render 代码轨 0 命中（未落地）**；PsychicReveal 仍清 `Cell+0x134` | 误以为已装、跳过写入 | **P0** |
> 【W3 勘误 · W3-A6/ISSUE-STALE-P2-LANDING】改前：P-2.1～P-2.3 | 按「可安装」列出 3×6B NOP | 增注：**ra2render 代码轨 0 命中；改后：P-2.1~P-2.3 裂缝三点 NOP 已于 09-30 完整落地进 blitter_hooks.cpp:3273-3287 并完成三处 DLL 同步；真机 A3 验收 PASS (带窗口限定)。；依据：ra2render/blitter_hooks.cpp:3273-3287, 3417-3446; out/re_work/zcode_live/gap_p21_a3/RESULT_GAP_P21_A3.md:18-23；分级：P0
| **E-4** | `pending_execution_master_table.md` §一 P-6.2 | `A1 F4 F7 87 00 ...` | 补全入口 5B `A1 F4 F7 87 00` + 序言 `83 EC 0C 85 C0`；或标 **N/A** | 回滚表无法机械还原 | **P1** |
| **E-5** | `pending_execution_master_table.md` §3.1 `EnableMinimapFog` 行 | 「**ini 现值 1**」 | **`ra2render.ini` 现值已为 `0`** | 误导验收基线 | **P2** |
| **E-6** | 任务书 / 口头引用 | `landing_pack_equivalence_static_proof.md` | 实际 **`landing_equivalence_static_proof.md`** | 脚本按名索引 miss | **P3** |
| **E-7** | `weapons_damage_production.md:473,581` | `qword[warhead+0xB0+armor*8]` / `Warhead+0xB0+armor*8` | 同 E-2：**`+0xA0`** | 同 E-2（E-2 清单漏收） | **P0** |
| **E-8** | `weapons_damage_production.md:127` | `Deform | 0xA8` | 与 `Verses[0]=+0xA0` 重叠（`+0xA8`=`Verses[1]`）；Deform 真实偏移待实证 | 误读 Deform 字段 | **P1** |
| **E-9** | `ARCHITECTURE_ATLAS.md:377` | mermaid「分配 12 字节 Blitter 对象」 | 「按成员数分级分配 4/8/12/16 字节」 | 读图踩 E-1 | **P1** |

> **未删改任何原文**：以上仅在本文件登记补丁块，源文档保持原样。

---

## 二、按文件分组的补丁块

### 2.1 `docs/re/blitter_microkernel_deep_dive.md`（E-1 × 2）

#### E-1-a  L40

- **锚点**（前 40 字符）：`在西木引擎的工厂函数（`0x0048FAF8`–`0x0048FC98`）与析构`
- **原文**：「所有 Blitter 对象的分配大小统一为 **12 字节**（`push 0x0c; call operator new`）。」

```
【勘误 2026-09-29 · E-1 · landing_audit】原文「所有 Blitter 对象的分配大小统一为 12 字节」→ 订正为：**按成员数分级 4/8/12/16 四级分配**（`push <size>; call operator new (0x007C8E17)`），**P0 微内核（步兵/载具本体与影子主路径）实测仅 8 字节**。按 12B 声明 `this+0x08` 将**越界 4 字节**（堆块尾部踩踏）。权威：`ARCHITECTURE_ATLAS.md` §1.2〔勘误 R1〕+ 同文 L1029 自勘误 + `re_sprint_S13_report.md:17`。原文保留不删字。
```

#### E-1-b  L45

- **锚点**：`[ Blitter 内存对象布局 (12 字节) ]`
- **原文**：围栏图标题 + 三行布局（`+0x00` / `+0x04` / `+0x08`）

```
【勘误 2026-09-29 · E-1 · landing_audit】下图标题「(12 字节)」→ 订正为：**尺寸按成员数分级 4/8/12/16**；P0 微内核 = **8 字节**（仅 `+0x00` vtable + `+0x04` 一槽，**无 `+0x08`**）。Lucent/ZRemap/Alpha 族才是 12 字节（vtable + 2 槽）。按 12B 统一布局图声明结构体，在 8B 对象上访问 `this+0x08` 即越界 4 字节。原文围栏保留不删字。
```

---

### 2.2 `docs/re/weapons_damage_production.md`（E-2 × 8 + E-7 × 2 + E-8 × 1 = 11 处）

#### 全文统一声明（建议插在标题下）

```
【勘误 2026-09-29 · E-2/E-7 · landing_audit】本文多处将 `WarheadTypeClass.Verses[11]` 记为 `Warhead+0xB0` / `+0xB0+armor*8`，**偏移错误**。实证：**`Verses[0]` 起于 `+0xA0`**（覆盖 `+0xA0…+0xF7`，11 个 double），**`+0xB0` 实为 `Verses[2]`**。按 `+0xB0` 写会把第 3 档护甲乘数当数组起点，**静默错位 8 个 double**。勿与超武 `SuperClass` 的 `SW+0xB0 RechargeTime` 混淆。权威：`ARCHITECTURE_ATLAS.md` §16.3〔勘误 R6-E2〕，装载器锚点 `0x75DE06/0x75DE0C/0x75DE48/0x75DE52` + 默认值串 `0x847C40`。下文逐处标注，原文保留不删字。
```

#### 逐处补丁（行号 + 锚点 + 勘误块）

| # | 行号 | 锚点（前 40 字符） | 订正要点 |
|:---:|:---:|:---|:---|
| E-2-01 | L19 | `| Verses 护甲乘数在哪？ | `WarheadTypeClass.Ver` | `Warhead+0xB0` → **`+0xA0`** |
| E-2-02 | L128 | ``| **`Verses[11]`** | **`0xB0`** | double`` | `0xB0` → **`0xA0`**（覆盖 `+0xA0…+0xF7`） |
| E-2-03 | L142 | `` `Verses[i]` 的地址 = `Warhead + 0xB0 + i*8` `` | `+0xB0` → **`+0xA0`** |
| E-2-04 | L208 | ` ├─ 护甲乘数：Warhead->Verses[armor]（+0xB0+ar` | `+0xB0` → **`+0xA0`** |
| E-2-05 | L215 | `**Verses 应用点**：在 `ReceiveDamage` 的伤害归一化段` | `+0xB0` → **`+0xA0`**；另注施加点未定位 |
| E-2-06 | L229 | ``| `Verses` | `0xB0..0x100` | 护甲乘数表 |`` | `0xB0..0x100` → **`0xA0..0xF7`** |
| E-2-07 | L563 | `    ReceiveDmg --> VersesCalc["Verses 护甲` | `+0xB0` → **`+0xA0`** |
| E-2-08 | L845 | `   - **未闭环现状**：已确证 Verses 位于 `Warhead+0x` | `+0xB0` → **`+0xA0`** |
| **E-7-01** | **L473** | `- `Verses` 的**精确乘法指令**在 `ReceiveDamage` ` | `+0xB0` → **`+0xA0`**（E-2 清单漏收） |
| **E-7-02** | **L581** | ``| **护甲乘数结算** | `0x00701900` | **确定性静态表**`` | `+0xB0` → **`+0xA0`**（E-2 清单漏收） |
| **E-8** | **L127** | ``| `Deform` | `0xA8` | double | 地形变形 |`` | 与 `Verses[1]` 重叠；待独立实证 |

**统一勘误块**（每处行末追加，可复用）：

```
【勘误 2026-09-29 · E-2】原文「Warhead+0xB0 / +0xB0+armor*8」→ 订正为：**`Warhead+0xA0+armor*8`**（`Verses[0]` 起于 `+0xA0`，`+0xB0`=`Verses[2]`）。原文保留不删字。
```

```
【勘误 2026-09-29 · E-7】原文「Warhead+0xB0+armor*8」→ 订正为：**`Warhead+0xA0+armor*8`**。本行未被 landing_pack_preflight_audit E-2 行号清单收录，系本次全库扫描新发现。原文保留不删字。
```

```
【勘误 2026-09-29 · E-8】原文「`Deform` | `0xA8`」与订正后 `Verses[0]=+0xA0` 重叠（`+0xA8` = `Verses[1]`）。R6-E2 已标注 Deform 偏移存疑；在独立实证闭环前**不得按 `+0xA8` 读写 Deform**。原文保留不删字。
```

---

### 2.3 `docs/re/pending_execution_master_table.md`（E-3 + E-4 + E-5）

#### E-3  L44-46  状态注记

- **锚点（L44）**：`| **6** | **P-2.1** | M-10 Gap1 局部开图 | 裂`

```
【勘误 2026-09-29 · E-3 · landing_audit】状态注记（非规格变更）：P-2.1～P-2.3 三处 3×6B Gap NOP **纸面规格已定谳、ra2render 代码轨当前 0 命中（未落地）**。全源码 grep `568273/577EC5/577B60` 无命中（`ARCHITECTURE_ATLAS_REV` §20.6）。⇒ 实施方**不可误以为已装而跳过写入**；PsychicReveal 仍清 `Cell+0x134`，裂缝保护缺口仍在。字节面 17/17 PASS，规格本身无需改，仅补状态标注。原文保留不删字。
```

#### E-4  L56  原字节补全

- **锚点**：`| **18**| **P-6.2** | L4 视口翻转格外扩 | 视口渲染调`

```
【勘误 2026-09-29 · E-4 · landing_audit】原文「`A1 F4 F7 87 00 ...`」以 `...` 截断，**不足以机械回滚**。订正为：至少补全入口 5 字节 `A1 F4 F7 87 00`，并标注函数序言后续 `83 EC 0C 85 C0`（已实测确认）。替换类型「原生 API 调用（非 Hook）」项若不写字节，应标 **N/A（非字节补丁）** 而非留 `...`。原文保留不删字。
```

#### E-5  L454  过时值

- **锚点**：`` | `EnableMinimapFog` | `0`（API 默认已强制 0；* ``

```
【勘误 2026-09-29 · E-5 · landing_audit】原文「**ini 现值 1**」已过时。实测 `ra2render.ini` 现值已为 **`0`**（L117），注释中仅历史提及 1。验收基线应以 `0` 为准。原文保留不删字。
```

---

### 2.4 `docs/re/ARCHITECTURE_ATLAS.md`（E-9 + T1 × 46）

#### E-9  L377  mermaid 残留

- **锚点**：`        F1 -->|"push 0x0C; call _new"| F2["分配 12`

```
【勘误 2026-09-29 · E-9 · landing_audit】下图 F2 节点「分配 12 字节 Blitter 对象」→ 订正为：**「按成员数分级分配 4/8/12/16 字节」**（P0 微内核 = 8 字节）。正文 §1.2 已勘误，本图为残留。原文保留不删字。
```

#### T1  46 节证据等级标签插入块

> 来源：`out/re_work/va_claims/grade_tags_p1.md`（人工校正后 46 条）
> 判定口径：`tools/atlas_audit.py` F4 —— 标题行或其后 3 行须含 `[实证]`/`[推演]`/`[待实测]` 之一。
> 用法：在各目标行**之前**插入标签行。原文标题不动。

**完整 46 条插入块见**：`out/re_work/errata_patches/by_file/ARCHITECTURE_ATLAS.md.patch` §T1

**标签分布**：`[实证]` × 26 · `[待实测]` × 11 · `[推演]` × 9

**速查表**（行号 → 标签）：

| 行号 | 小节 | 标签 | | 行号 | 小节 | 标签 |
|:---:|:---|:---:|:---|:---:|:---|:---:|
| 205 | 0.1 逆向目标 | [推演] | | 3141 | 15.11 VA 速查 | [实证] |
| 229 | 0.2 分层拓扑 | [推演] | | 3160 | 15.12 R5 勘误 | [实证] |
| 310 | 0.3 Lead 裁决 | [实证] | | 3355 | 16.6 VA 速查 | [实证] |
| 441 | 1.2 内存布局 | [实证] | | 3382 | 16.7 未闭环 | [待实测] |
| 608 | 1.6 吞吐瓶颈 | [推演] | | 3528 | 17.6 VA 速查 | [实证] |
| 2334 | 10.4 P-M1~M5 | [推演] | | 3555 | 17.7 未闭环 | [待实测] |
| 2539 | 12.2 联机红线 | [推演] | | 3716 | 18.6 Z 序 | [实证] |
| 2601 | 12.4 补丁生命周期 | [实证] | | 3756 | 18.9 Hook 面 | [待实测] |
| 2675 | 13.1 真机挂起 | [待实测] | | 3769 | 18.10 未闭环 | [待实测] |
| 2686 | 13.2 UNVERIFIED | [待实测] | | 3782 | 18.11 VA 速查 | [实证] |
| 2698 | 13.3 阈值口径 | [实证] | | 3939 | 19.8 成本中心 | [实证] |
| 2710 | 13.4 两级过滤 | [推演] | | 3950 | 19.9 归因红线 | [推演] |
| 2720 | 13.5 联机放闸 | [待实测] | | 3956 | 19.10 未闭环 | [待实测] |
| 2745 | 14.1 结论速览 | [实证] | | 3968 | 19.11 VA 速查 | [实证] |
| 2896 | 14.10 契约 | [实证] | | 4051 | 20.3 勘误收口 | [实证] |
| 2907 | 14.11 未闭环 | [待实测] | | 4140 | 20.6 落地状态 | [实证] |
| 2921 | 14.12 VA 速查 | [实证] | | 4149 | 20.7 联机门控 | [实证] |
| 2948 | 14.13 R5 勘误 | [实证] | | 4160 | 20.8 未闭环 | [待实测] |
| 2962 | 15.1 结论速览 | [实证] | | 4170 | 20.9 VA 速查 | [实证] |
| 3118 | 15.9 契约 | [实证] | | 4381 | 21.7 契约未闭环 | [推演] |
| 3129 | 15.10 未闭环 | [待实测] | | 4392 | 21.8 VA 速查 | [实证] |
| | | | | 4482 | 22.2 调用者归属 | [实证] |
| | | | | 4497 | 22.3 sprintf 治理 | [实证] |
| | | | | 4509 | 22.4 池化风险 | [推演] |
| | | | | 4550 | 22.7 VA 速查 | [实证] |

---

## 三、影响面统计

### 3.1 按优先级

| 优先级 | 编号 | 行级处数 | 阻断等级 |
|:---:|:---|:---:|:---|
| **P0** | E-1, E-2, E-3, E-7 | 2+8+3+2 = **15** | 产品决策阻断 / 落地跳过风险 |
| **P1** | E-4, E-8, E-9, T1 | 1+1+1+46 = **49** | 机械回滚 / 读图误导 / 标签缺失 |
| **P2** | E-5 | **1** | 验收基线误导 |
| **P3** | E-6 | **0**（提示） | 脚本索引 |

### 3.2 按文件

| 文件 | 勘误编号 | 行级处数 | 冻结状态 |
|:---|:---|:---:|:---|
| `docs/re/blitter_microkernel_deep_dive.md` | E-1 | 2 | L1 冻结 |
| `docs/re/weapons_damage_production.md` | E-2, E-7, E-8 | 11 | L1 冻结 |
| `docs/re/pending_execution_master_table.md` | E-3, E-4, E-5 | 5 | L1 冻结 |
| `docs/re/ARCHITECTURE_ATLAS.md` | E-9, T1 | 47 | L1 冻结 |
| 任务书 / 口头引用 | E-6 | 0 | — |

### 3.3 按风险类型

| 风险类型 | 涉及编号 | 后果 |
|:---|:---|:---|
| **结构体越界** | E-1 | 按 12B 声明 Blitter → P0 路径 `this+0x08` 越界 4B → 堆破坏 |
| **偏移静默错位** | E-2, E-7 | 按 `+0xB0` 写 Verses → 错位 8 个 double；读 11 项 → 越读 |
| **落地状态误判** | E-3 | 误以为 Gap NOP 已装 → 裂缝保护缺口 |
| **回滚不可机械** | E-4 | `...` 截断 → 无法还原 |
| **验收基线错** | E-5 | 按「ini=1」验收 → 与实际 `0` 不符 |
| **读图误导** | E-9 | mermaid 与正文矛盾 |
| **字段重叠** | E-8 | Deform/Verses[1] 共用 `+0xA8` |
| **标签缺失** | T1 | F4 审计不通过 |

---

## 四、与 landing_pack_preflight_audit E-1～E-6 的差异

| 项 | 审计表 | 本次扫描 | 说明 |
|:---|:---|:---|:---|
| E-1 | L40,45 | 同 | 一致 |
| E-2 | 8 处（19,128,142,208,215,229,563,845） | **10 处**（+L473,L581） | **E-7 新增** |
| E-3 | 状态注记 | 同 | 一致 |
| E-4 | P-6.2 截断 | 同 | 一致 |
| E-5 | ini 现值过时 | 同 | 一致 |
| E-6 | 文件名 | 同 | 一致 |
| — | — | **E-8** Deform 重叠 | **新发现** |
| — | — | **E-9** mermaid 残留 | **新发现** |

---

## 五、§九 草稿（给执行台账追加用；本文不改原总表）

> 建议以「附录：勘误补丁块登记」形式并入下一次总表修订；原文条目保留，仅追加订正行。

### §九 勘误补丁块登记附录（草稿 · 2026-09-29 · errata_patches）

#### 9.1 字节面结论（不变）
1. P-1.1～P-6.2 共 17 条原字节、9 条 E9 rel32、5 条跳板机器码，**全部与 `gamemd.exe` 一致**（MD5 `4f37486e5b0dbe2ae5f45aeee0f98367`）。
2. S23 31 条断言 **全 MATCH**，可作为落地后回归对拍基线。
3. 跳板页 `0x01B00000` 布局 **零重叠**；`VirtualAlloc` 失败 → **整项不安装**（F-07 口径已收录）。

#### 9.2 须先订正（合入前）—— 勘误补丁块已就绪
| 序 | 编号 | 动作 | 责任文档 | 补丁位置 |
|:---:|:---:|:---|:---|:---|
| 1 | E-1 | 标注：**P0 微内核实例 8 字节**（非 12）；禁按 12B 声明 `this+0x08` | blitter_microkernel_deep_dive.md | `by_file/blitter_microkernel_deep_dive.md.patch` |
| 2 | E-2+E-7 | 标注：**`Verses` 起于 `+0xA0`**（`+0xB0`=`Verses[2]`）；10 处 | weapons_damage_production.md | `by_file/weapons_damage_production.md.patch` |
| 3 | E-3 | 总表 P-2.1～P-2.3 增注：**ra2render 未落地** | pending_execution_master_table.md | `by_file/pending_execution_master_table.md.patch` |
| 4 | E-4 | 补全 P-6.2 原字节或标 N/A | pending_execution_master_table.md | 同上 |
| 5 | E-5 | 订正「ini 现值 1」→「现值 0」 | pending_execution_master_table.md | 同上 |
| 6 | E-8 | Deform `+0xA8` 存疑标注 | weapons_damage_production.md | 同 weapons |
| 7 | E-9 | mermaid「12 字节」残留订正 | ARCHITECTURE_ATLAS.md | `by_file/ARCHITECTURE_ATLAS.md.patch` |
| 8 | T1 | 46 节证据等级标签插入 | ARCHITECTURE_ATLAS.md | 同上 §T1 |

#### 9.3 可直接机械写入清单（无订正项，不变）
- P-1.1～P-1.5 五处 `E9 rel32` + TRAMP_HD1/2/5/6/6B
- P-2.1～P-2.3 三处 `90×6`、P-2.4 `EB 65`
- P-3.1/P-3.2 虚表槽 69（`PatchVTablePointer`，禁 inline）
- P-4.1/P-4.2 两处 `E9 rel32` + TRAMP_P4_* + P-M1…P-M5
- P-5.1/P-5.2 两处 `E9 rel32` + TRAMP_P5_*（早退 `33 C0 C2 08 00` / `33 C0 C2 04 00`）
- P-6.1 默认写 `E9 99 00 00 00 90`（force-full）
- INI 最终默认值按 §3.4（**忽略文中「改前」旧值**）

#### 9.4 安装后必做对拍（继承 TC-ST-01…06）
1. 5 处 Hook 机器码 + H-D5 `+0x10=0F B6 C0`
2. Gap 3×`90×6` + SpySat `EB 65` + TYPE 备份 4 字段
3. 虚表槽指向 Hook 且函数体出口 `ret 8`
4. `PoolBlockHeader==8`、返回 8 对齐、释放投毒
5. PlayGlobal/PlayAt 早退 `eax=0` + `ret 8`/`ret 4`
6. `0x006D3D99` Full 模式字节 + 全工程无 `0x0048D000` 挂钩

#### 9.5 遥测与回滚（不变）
- 回滚表按总表 §4.1；G-07 走 `RestoreSpySatBuildingTypes()`。
- 热卸载五阶段次序不变；第四阶段 `VirtualFree(0x01B00000)`。

---

## 六、复现 / 自查

```text
# 锚点自查（确认行号未漂移）
rg -n "分配大小统一为" docs/re/blitter_microkernel_deep_dive.md
rg -n "Warhead\+0xB0|0xB0\+armor|Warhead \+ 0xB0" docs/re/weapons_damage_production.md
rg -n "ini 现值 1" docs/re/pending_execution_master_table.md
rg -n "分配 12 字节 Blitter" docs/re/ARCHITECTURE_ATLAS.md

# 补丁块清单
ls out/re_work/errata_patches/by_file/
```

---

## 七、签署栏

| 项 | 值 |
|:---|:---|
| 复核方式 | 全库 grep 扫描 + 逐行锚点提取 + 与 landing_pack_preflight_audit 对拍 |
| 真机 | **未启动**（按任务约束） |
| 源文档改动 | **零**（L1 冻结，只登记不就地改） |
| 补丁块就绪 | **65 处**（E-1～E-9 行级 19 + T1 插入 46） |
| 新发现 | **E-7 / E-8 / E-9** 三条（审计表未列） |
| 残余风险 | Lead 解冻后须按块粘贴，勿手工改行号（锚点可自查） |
