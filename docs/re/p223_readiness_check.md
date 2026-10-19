# R-P223-READY · P-2.2/P-2.3 实施前就绪检查

> **任务号**：`R-P223-READY` · **性质**：只读对照 + 报告（不改冻结卡、不写 ra2render/gamemd/tools/台账/看板）  
> **对照源**：`ra2render/blitter_hooks.cpp` / `ra2render/ra2render.h` / `ra2render/ra2render.ini`（现码只读）  
> **卡片基线**：`docs/re/landing_pack_gap_p223.md`（ZC-GAP-P223）· `docs/re/landing_pack_gap_merge_checklist.md` · `docs/re/gap_protection_install_spec.md`  
> **上游勘误**：`out/re_work/zcode_live/gap_p21/RESULT_GAP_P21.md` §5（E-1 `0x56829A` / E-2 `17B`）  
> **静态证据**：`out/re_work/re_sprint/R_gap_p223/claims_p223.txt`（P-2.2/P-2.3 字节窗 MATCH）  
> **工作底稿**：`out/re_work/re_sprint/R_p223_ready/**`  
> **证据基线**：`gamemd.exe` 1.001 · SHA-256 `73201CC0…F67476` · ImageBase `0x00400000`

---

## 0. 一句话结论

**P-2.1 代码轨已落（`InstallGapProtectionPatch`）；P-2.2/P-2.3 尚未进 ra2render。就绪门四缺一：默认 0 ✓、MP 门 ✓、installed 计数 ✗（仅 0/1 bool）、回滚 ✗（仅单点）。推荐扩展现有 `InstallGapProtectionPatch` 为三点表驱动（不新增挂点），先补 `gapProtectionPatchesInstalled` 0..3 与逆序回滚，再执行 P223。**

---

## 1. P-2.2/P-2.3 接入点（对照 ra2render 现码）

### 1.1 现码盘点（只读）

| 项 | 现码位置 | 现状 | P223 需求 |
|---|---|---|---|
| 安装函数 | `blitter_hooks.cpp:3205` `InstallGapProtectionPatch()` | **仅 P-2.1 单点**（`ADDR_REVEALAREA2_GAP_CLEAR`） | 扩为三点（P-2.1→2.2→2.3） |
| 卸载函数 | `blitter_hooks.cpp:3280` `RemoveGapProtectionPatch()` | 仅还原 P-2.1 | 逆序 P-2.3→2.2→2.1 |
| 安装挂点 | `blitter_hooks.cpp:3418`（`InstallRadarFogHooks` `:3415` 之后） | 已挂 | **不新增挂点**（merge §5.2「挂点只增不移」） |
| 卸载挂点 | `blitter_hooks.cpp:3428`（`RemoveRadarFogHooks` 之后） | 已挂 | 同上 |
| 地址常量 | `ra2render.h:106-108` | 仅 P-2.1 三点（主点+窗前+窗后） | 增 P-2.2/2.3 各 3 组 |
| 开关键 | `blitter_hooks.cpp:37` + `:587-588` | `g_enableGapProtection` 默认 **false** | **沿用同键**，不建 P22/P23 键 |
| 遥测 | `blitter_hooks.cpp:38` `g_gapProtectInstalled` | **bool 0/1** | 需升 `gapProtectionPatchesInstalled` **int 0..3** |
| MP 门 | `blitter_hooks.cpp:3214-3217` `MpActive()` | 已强制不装 | 三点共用，**已具备** |
| 启动日志 | `blitter_hooks.cpp:591-592` | 已含 `0x56829A` 勘误后地址 | 扩三点描述 + `installed=N` |
| ini 说明 | `ra2render.ini:136-160` | 已写「P-2.2/P-2.3 另卡」 | 扩为整包语义 |

### 1.2 接入方案裁决：**扩展现有 `InstallGapProtectionPatch`（推荐）**

| 方案 | 描述 | 优点 | 风险 | 裁决 |
|---|---|---|---|---|
| **A. 扩展现有函数** | 保留函数名与挂点；内部改三点表驱动 + 公共门禁 | 挂点零漂移；门禁（G0.6/MP/Q1）一次复用；与 merge §5.2「P223 不新增挂点」一致 | 函数体变长 | **推荐** |
| B. 新函数 `InstallGapProtectionP223()` | 在 `:3418` 后再插一调用 | 隔离清晰 | 两次 MP/开关判定、installed 计数易撕裂、挂点+1 | 不推荐 |
| C. 重命名为 `InstallGapProtection()` | 对齐 merge §5.2 命名 | 文档一致 | 纯 rename 无功能收益，还动已验收 P21 符号 | 可选后置 rename，非阻塞 |

**推荐骨架（仅规格，本轮不写 ra2render）**：

```cpp
// 表驱动三点（常量禁止漂移；每点 6==6、只许 90）
struct GapPoint { uintptr_t va, winPre, winPost; size_t winPreN, winPostN;
                  const uint8_t *orig; const char *tag; };
// P-2.1 0x568273 / 0x568271(3B C3) / 0x568279(7C 14)   —— 现码已有
// P-2.2 0x577EC5 / 0x577EBF(89 B8 30 01 00 00) / 0x577ECB(8B 90 2C 01 00 00)
// P-2.3 0x577B60 / 0x577B56(C7 80 30 01 00 00 01 00 00 00) / 0x577B66(89 90 40 01 00 00)

// InstallGapProtectionPatch()：
//   G0.6 + MpActive（一次）→ for 每点(G0.2/Q1→G0.3/G0.4→backup→VirtualProtect→90×6)
//   → gapProtectionPatchesInstalled += 成功点数 → 日志 on installed=N
// RemoveGapProtectionPatch()：
//   for 逆序 {P-2.3, P-2.2, P-2.1}：仅当 s_orig[i].written 才 memcpy 还原
```

**P-2.2/P-2.3 窗尺寸注意**：P-2.2 窗前为 **6B**（`89 B8 30 01 00 00`，非 P21 的 2B）；P-2.3 窗前为 **10B**（`C7 80 30 01 00 00 01 00 00 00`）。现码 `GapProtectPeek(..., pre, 2)` / `nxt, 2` 的 2B 硬编码**不能**直接套用，需按点可变窗宽（见 merge §1 窗前/窗后列）。

### 1.3 必增常量（`ra2render.h`，规格级）

| 新增 | 值 | 原 6B |
|---|---|---|
| `ADDR_REVEALAREA3_GAP_CLEAR` | `0x00577EC5` | `89 B8 34 01 00 00` |
| `ADDR_REVEALAREA3_GAP_CLEAR_PREV` | `0x00577EBF`（6B） | `89 B8 30 01 00 00` |
| `ADDR_REVEALAREA3_GAP_CLEAR_NEXT` | `0x00577ECB`（6B） | `8B 90 2C 01 00 00` |
| `ADDR_RESHROUD_GAP_CLEAR` | `0x00577B60` | `89 98 34 01 00 00` |
| `ADDR_RESHROUD_GAP_CLEAR_PREV` | `0x00577B56`（10B） | `C7 80 30 01 00 00 01 00 00 00` |
| `ADDR_RESHROUD_GAP_CLEAR_NEXT` | `0x00577B66`（6B） | `89 90 40 01 00 00` |

---

## 2. 卡片 ↔ 代码行号对齐表（含勘误同步建议）

> **只写本报告，不改冻结卡**。勘误建议交 Lead 解冻后并入。

### 2.1 对齐总表

| 卡片锚点 | 卡内位置 | 现码位置 | 对齐？ | 备注 |
|---|---|---|---|---|
| P-2.1 主点 `0x568273` | p21 §1 / merge §1 | `ra2render.h:106` + `blitter_hooks.cpp:3206` | ✓ | 已落地 |
| P-2.1 窗前 `0x568271=3B C3` | p21 §1.1 | `ra2render.h:107` + `:3232-3236` | ✓ | |
| P-2.1 窗后 `0x568279=7C 14` | p21 §1.1 | `ra2render.h:108` + `:3237-3241` | ✓ | |
| **P-2.2 主点 `0x577EC5`** | p223 §1.0 / merge §1 | **无** | ✗ | 待接入 |
| **P-2.2 窗前 `0x577EBF`（6B）** | p223 §2 G0.3a | **无** | ✗ | 窗宽 6B≠2B |
| **P-2.2 窗后 `0x577ECB`（6B）** | p223 §2 G0.3b | **无** | ✗ | 窗宽 6B |
| **P-2.3 主点 `0x577B60`** | p223 §1.0 / merge §1 | **无** | ✗ | 待接入 |
| **P-2.3 窗前 `0x577B56`（10B）** | p223 §2 G0.4a | **无** | ✗ | 窗宽 10B |
| **P-2.3 窗后 `0x577B66`（6B）** | p223 §2 G0.4b | **无** | ✗ | 窗宽 6B |
| `EnableGapProtection` 默认 0 | p223 §3.1 / merge §2 | `blitter_hooks.cpp:587-588`、`ra2render.ini:160` | ✓ | |
| MP 门 `MpActive` 强制不装 | p223 §3.1 / merge §7 MP-2 | `blitter_hooks.cpp:3214-3217` | ✓ | |
| `gapProtectionPatchesInstalled` 0..3 | p223 §3.2 / merge §4 | **无**（仅 `g_gapProtectInstalled` bool） | ✗ | G2.1/G4.1 判据 |
| 硬回滚逆序 2.3→2.2→2.1 | p223 §3.3 / merge §3.2 | `RemoveGapProtectionPatch:3280` 仅单点 | ✗ | |
| 同装 `installed==3` 写 `GapProt Version` | merge §4 | **无** | ✗ | 存档侧另卡可接受，但计数必须先有 |
| 安装挂点「`:3266` 之后」 | merge §5.2 | `:3418`（语义锚=`InstallRadarFogHooks` 后） | ✓* | *行号已漂移，语义锚成立（见 2.3） |
| 卸载挂点「`:3275` 之后」 | merge §5.2 | `:3428`（语义锚=`RemoveRadarFogHooks` 后） | ✓* | 同上 |

### 2.2 勘误同步建议（ZCode P21 回执 E-1/E-2 → 冻结卡）

| ID | 冻结卡写法 | 实证 | 波及文件 | 建议 | 风险 |
|---|---|---|---|---|---|
| **E-1** | `0x568297` `or [ecx+0x12C],0x10` | 实际 **`0x0056829A`**（`0x568297` 是 `mov ecx,0xABDC50` 尾巴 `50 DC AB 00`） | `landing_pack_gap_p21.md` §1.1/§1.2；`gap_psychic_reveal_deep_dive.md` §3.3；`landing_pack_gap_merge_checklist.md` §1「保留 `0x568297 CopyFlags`」；`gap_protection_install_spec.md` §1 语义边界；`savegame_product_checklist.md` G0.3 邻域描述 | 统一改 **`0x0056829A`** | 文档级；**G0 门禁不引用此 VA**，无落地风险。现码 `ra2render.h:96` / `ra2render.ini:140` / 启动日志 `:591` **已是 0x56829A**（代码轨已勘误） |
| **E-2** | p21 §1.1「上下文窗共 **21B**」 | 各行 2+6+2+7=**17B**（首末跨度另计则 45B，不可混用） | `landing_pack_gap_p21.md` §1.1 | 标注「指令对齐合计 **17B**」 | 文档级 |
| E-3（新发现） | merge checklist §5.2 / install_spec §2.1 挂点行号 `:3266`/`:3275`/`:3177` 等 | 现码 `InstallVTableHooks` 挂点在 **`:3418`**、卸载 **`:3428`**（行号已漂移） | merge §5.2、install_spec §2.1 | 保留语义锚「`InstallRadarFogHooks` 之后」，回执记实际行号（merge §5.2 已预留此规则） | 无落地风险，回执须记 |

**P223 卡本身**（`landing_pack_gap_p223.md`）字节/VA **无 E-1 类错误**（其保留写点用的是 `0x577EBF`/`0x577ED4` 等 RevealArea3/Reshroud 侧地址，与 E-1 无交）。**merge checklist §1 语义边界列混入了 P-2.1 的 `0x568297`**，属 E-1 波及。

### 2.3 挂点行号漂移说明

merge §5.2 原文行号来自 install_spec 起草时点；现码 `InstallVTableHooks` 内容已增（13 虚表钩 + 3 inline 钩），`InstallGapProtectionPatch` 调用落在 `:3418`。merge 已规定「若行号与现网源漂移，以 `InstallRadarFogHooks` 之后 / `RemoveRadarFogHooks` 之后语义锚为准，并在回执记录实际行号」——**现码满足语义锚，P223 无需挪挂点**。

---

## 3. 就绪门（四门）

| # | 门 | 期望（卡片） | 现码状态 | 判定 |
|---|---|---|---|---|
| **G-DEF** | 默认 0 = 不碰 `.text` | `EnableGapProtection` API 默认 0 / ini 出厂 0 | `GetIniIntEx(..., 0, ...)` `blitter_hooks.cpp:587`；`g_enableGapProtection=false` `:37`；ini `EnableGapProtection=0` `:160`；off 分支 `:3210-3212` | **✓ 具备** |
| **G-CNT** | `gapProtectionPatchesInstalled` 0..3 | 仅 `==3` 写存档标记；分装 PARTIAL | 仅 `g_gapProtectInstalled` **bool** `:38`（`true/false`），**无 0..3 计数**；无 `GapProt Version` 写点 | **✗ 缺口**（P223 前必须补 int 计数；存档写点可另卡） |
| **G-RBK** | 硬回滚逆序 2.3→2.2→2.1 + 分点/整组 `memcpy` | `s_origP22/P23` + 逆序 | 仅 `s_origGapProtectP21[6]` `:3189` + `RemoveGapProtectionPatch` 单点 `:3280-3299` | **✗ 缺口**（扩三点时同步补逆序） |
| **G-MP** | `MpActive()` ⇒ 强制不装 + `forced-off-mp` | 同 P21/EnableMinimapFog 级 | `MpActive()` `:198-217`（`0xA8D5F8` bit1 / DirectPlay==2）；强制不装 `:3214-3217` | **✓ 具备**（三点共用同一门即可） |

**附加软门**：

| 项 | 状态 |
|---|---|
| Q1 外部安装者停手 | ✓（`:3242-3248` 已有；P223 须逐点独立判，禁止「一点 external 判全包」） |
| 热重载禁止（init-only） | ✓（`LoadConfig` 只 `:587` 读一次） |
| 只改内存映像、磁盘 exe 只读 | ✓（`:3187` 注释 + 实现无文件写） |
| 非 `90` 替换禁止 | ✓（`kNop[6]` 纯 90） |
| 窗宽可变（6B/10B） | ✗ 现码 2B 硬编码，P223 扩点时必须参数化 |

---

## 4. ZCode「P223 执行前检查单」

> 执行方勾选；任一 **G0.x FAIL = 整包不写**。

### 4.1 写前（代码轨）

- [ ] C1 只扩 `InstallGapProtectionPatch`/`RemoveGapProtectionPatch`（或 rename 后同构）；**不新增挂点**（仍 `InstallRadarFogHooks` 后 / `RemoveRadarFogHooks` 后）
- [ ] C2 新增 6 组地址常量（§1.3），**禁止漂移** 6B 原字节
- [ ] C3 窗宽参数化：P-2.1 前 2B/后 2B；P-2.2 前 **6B**/后 6B；P-2.3 前 **10B**/后 6B
- [ ] C4 遥测升 `gapProtectionPatchesInstalled` int 0..3（可保留 `g_gapProtectInstalled` 作兼容，但 G2.1 判据以 int 为准）
- [ ] C5 回滚逆序 P-2.3→P-2.2→P-2.1；每点独立 `s_origP2x[6]` + written 标志；external 点不还原
- [ ] C6 安装序强制 P-2.1→P-2.2→P-2.3；`installed<3` 日志 `(PARTIAL)`
- [ ] C7 同键 `EnableGapProtection`；**禁建** `EnableGapProtectP22/P23`
- [ ] C8 日志尾追 `installed=N`；枚举对齐 merge §2（含 `external-installer-detected` 等）
- [ ] C9 保留写点一字不动（p223 §1.2 七行表：只删两处 `+0x134` store）
- [ ] C10 禁改零常量 `edi`（P-2.2）/ `ebx`（P-2.3）；禁 `89→8B`；禁 trampoline / `.detour`

### 4.2 写前（真机门禁 G0，全 PASS 才写）

- [ ] G0.1 文件 SHA-256 = `73201CC0…F67476`
- [ ] G0.2a `0x577EC5` 首 6B = `89 B8 34 01 00 00`（`90×6` ⇒ external 停手）
- [ ] G0.2b `0x577B60` 首 6B = `89 98 34 01 00 00`（同上）
- [ ] G0.3a `0x577EBF` = `89 B8 30 01 00 00`
- [ ] G0.3b `0x577ECB` = `8B 90 2C 01 00 00`
- [ ] G0.4a `0x577B56` = `C7 80 30 01 00 00 01 00 00 00`
- [ ] G0.4b `0x577B66` = `89 90 40 01 00 00`
- [ ] G0.5 PE32 / ImageBase `0x400000` / 目标在 `.text`
- [ ] G0.6 `EnableGapProtection` 显式 =1
- [ ] G0.7 P-2.1 状态记录（未装则警告，不拒绝）
- [ ] Q1 三点首字节逐点判（`89`=未打 / `90`=external **停手上报**）
- [ ] MP 门：`MpActive()==true` ⇒ 不装，日志 `forced-off-mp`

### 4.3 装后自检

- [ ] A1 默认档：三点 6B 仍原版；日志 `GapProtection=off`
- [ ] A2 =1 档：三点 `90×6`；六条窗守未动；日志 `GapProtection=on installed=3`
- [ ] 回读逐点 `GapProtectLogBytes`
- [ ] `installed` 与实际写入点数一致；`<3` 打 PARTIAL 且不写 `GapProt Version`
- [ ] A3/A4/A5（SpySat 在线/离线/旁路）「缝仍在」证据（禁「没崩」当成功）
- [ ] R1 逆序回滚实测（P-2.3→P-2.2→P-2.1）三点回原版、窗未动
- [ ] `except.txt` 空；磁盘 `gamemd.exe` sha256 未变

### 4.4 回执必填（对齐 merge §9）

```
- install path: A ra2render | B external
- gapProtectionPatchesInstalled: (期望 3)
- G0.1–G0.7 / Q1 三点首字节 before/after
- context windows intact: y/n
- GapProtection log line: … installed=N
- install order: P-2.1→P-2.2→P-2.3
- rollback order tested (P-2.3→P-2.2→P-2.1): y/n
- same-install / split-install: same|split
- §7.1 handshake conflict status: open|resolved-by-Lead
```

---

## 5. 风险与阻塞（执行方必读）

| ID | 项 | 说明 | 级别 |
|---|---|---|---|
| RSK-1 | installed 计数缺口 | 无 0..3 则 G2.1/G4.1 判据落空；分装中间态无法判定 | **P0 阻塞发布语义** |
| RSK-2 | 回滚仅单点 | 只拆中间点/乱序会语义撕裂（R-7） | P0（随 C5 闭合） |
| RSK-3 | 窗宽 2B 硬编码 | 直接套用现码会 G0.3a/0.4a 误判（6B/10B 窗） | P1 实现风险 |
| RSK-4 | A3/A4/A5 真机环境 | P21 回执：ra2bench 遭遇战无预置建筑+触发器不触发；P223 的 SpySat 用例同样受限 | 验收风险，建议战役图/诊断钩另卡 |
| RSK-5 | §7.1 握手口径未裁 | 甲（不加键）vs 乙（握手必须含 installed）未决；裁前禁宣称「MP 可发布」 | 流程门 |
| RSK-6 | E-1 勘误未回写冻结卡 | 执行时**以现码 0x56829A 为准**；勿按 p21/merge 旧文 0x568297 写窗 | 文档 |

---

## 6. 就绪结论

| 问题 | 答案 |
|---|---|
| ① P-2.2/P-2.3 接入点 | **扩展现有 `InstallGapProtectionPatch`/`RemoveGapProtectionPatch`**（表驱动三点，挂点不动）；常量+窗宽参数化见 §1 |
| ② 卡片↔行号对齐 | §2；P223 字节面无误；E-1/E-2 波及 p21/merge/install_spec/deep_dive；挂点行号漂移但语义锚成立 |
| ③ 就绪门 | **G-DEF ✓ / G-MP ✓ / G-CNT ✗ / G-RBK ✗** ⇒ 未完全就绪；C4+C5 闭合后可执行 |
| ④ ZCode 检查单 | §4（C1–C10 + G0/Q1 + 装后 + 回执） |

**总判**：**CONDITIONAL-GO**——门禁与 MP 防护已具备，字节面静态证据齐（claims_p223 MATCH）；须先补 `gapProtectionPatchesInstalled` 0..3 与逆序回滚（可与 P223 同一 PR 内完成），并按 §4 检查单执行。回执按 merge §9 合并整包填写。

---

*依据：ra2render 现码只读对照（blitter_hooks.cpp / ra2render.h / ra2render.ini）；`landing_pack_gap_p223.md`；`landing_pack_gap_merge_checklist.md`；`gap_protection_install_spec.md`；`RESULT_GAP_P21.md` §5 勘误；`claims_p223.txt`。本文件为 R-P223-READY 报告，未改任何冻结卡/ra2render/gamemd/台账。*

---

## 追加节 · 就绪门状态复核（2026-10-01 · 工单 `T-W1-Q / PK-1`）

> **只追加、不删改**：上文（含引自 `out/re_work/re_sprint/R_p223_ready/readiness_gates.tsv` 的门表）逐字保留。
> **本节存在的原因**：本报告的对照基线是 **P223 合入之前** 的 `ra2render` 现码。合入发生在报告写出之后，因此 7 条门里有 4 条的判词已随代码演进失效。**原文不回改**，在此登记复核结论。

### 时序（本次实测 mtime）

| 事件 | 时间 | 证据 |
|---|---|---|
| `R_p223_ready/` 目录（本报告）产物 | 2026-09-30 **21:15** | `ls -d` mtime |
| ZC-10B 批次 `ra2render.ini` 写入 | 2026-09-30 21:50 | `ra2render/ra2render.ini` mtime |
| `blitter_hooks.cpp`（含三点表驱动）最后修改 | 2026-09-30 **22:01** | `ra2render/blitter_hooks.cpp` mtime（现 3833 行） |
| `MASTER_STATUS.md` 记队列 1–3 完成、构建 `626f98b6…` | 2026-09-30 22:07 | `out/re_work/zcode_live/MASTER_STATUS.md` mtime + `:10,19,29` |

⇒ 本报告的 `code_status` 列引用的是 **21:15 之前**的源码行号（如 `blitter_hooks.cpp:3189/3280` 单点、`:37` `g_gapProtectInstalled` bool），与 22:01 之后的现码不再是同一版本。

### 门复核（7 条逐条，结论均经本次 grep/读码复算）

| 门 | 报告原判 | **2026-10-01 复核** | 实测依据 |
|---|---|---|---|
| `G-DEF` default-0 | PASS | **仍 PASS** | `blitter_hooks.cpp:606` 默认 0；`ra2render.ini:199` `EnableGapProtection=0` |
| `G-CNT` installed-count（RSK-1：需 int 计数器，原「only bool `g_gapProtectInstalled` :38」） | **FAIL** | **现已满足**：`int g_gapProtectionPatchesInstalled ∈ 0..3` 存在并按点累加 | `blitter_hooks.cpp:39`（声明 + 注「只读计数，热路径不读」）、`:3402`（`= installed`）、`:3444`（卸载后回填）、`:942`（遥测行） |
| `G-RBK` rollback（RSK-2：需逆序 + 分点 memcpy，原「单点 `s_origGapProtectP21 :3189` / `RemoveGapProtectionPatch :3280`」） | **FAIL** | **现已满足**：整组备份 `s_origGapProtectBytes[3][6]` + 分点回滚资格位 + 逆序遍历 | `blitter_hooks.cpp:3289-3291`（三行声明）、`:3417 RemoveGapProtectionPatch()`、`:3446`（日志「逆序硬回滚 P-2.3->P-2.2->P-2.1」）；真机侧 `RESULT_GAP_P223.md:59` C5 **PASS** |
| `G-MP` mp-gate | PASS | **仍 PASS** | `blitter_hooks.cpp:3322`（`forced-off-mp` 日志行）；`RESULT_GAP_P223.md:55`（代码门保留，单机会话未触发，**不宣称联机验收**） |
| `soft` q1-external（原「:3242-3248 仅 P2.1 有，需逐点」） | **PARTIAL** | **已转 PASS（静态）**：外部安装者检测现为逐点判定 | `blitter_hooks.cpp:3358`（幂等 already 分支）、`:3374`（`external-installer-detected`，整包停手不写不还原）、`:3292`（`s_gapProtectExternal[3]` 逐点位）、`:3423`（卸载时不还原外部写入） |
| `soft` window-width（RSK-3：原「`GapProtectPeek` 硬编码 2B 前后窗」） | **PARTIAL** | **已转 PASS**：邻窗宽度入表逐点声明（P-2.1 前 2/后 2；P-2.2 前 6/后 6；P-2.3 前 **10**/后 6） | `blitter_hooks.cpp:3273-3287`（`kGapProtectPoints[3]` 宽度字段）、`:3338/:3350`（按声明宽度校验并拒装）；`_static/precheck_queue.md:231`（E2：P21 窗实为 **17B**）与之相容 |
| `soft` init-only（无热重载） | PASS | **仍 PASS** | `blitter_hooks.cpp:606` 在 `LoadConfig` 内单次读取；红线 `MASTER_STATUS.md:4`「禁热切换」 |

### 净结论与剩余缺口

- **7 条门现状**：5 条原 PASS/现 PASS 不变；**2 条 FAIL（G-CNT / G-RBK）与 2 条 PARTIAL（q1-external / window-width）全部转满足**——即 P223 合入正是照本报告「blocker」列（RSK-1/RSK-2/RSK-3）实现的。
- **仍未闭环 3 条**（不是本报告能静态消解的）：
  1. **`GapProt Version` 存档标记**（`installed==3` 才写）仍未实现——`grep -i "GapProt Version" ra2render/**` 本次 **0 命中**，且现码 `:3411` 明文「installed<3 ⇒ 不写标记、禁联机、禁存补丁档」；`RESULT_GAP_P223.md:36,129`、`MASTER_STATUS.md:55` 同记。⇒ **写档另卡**。
     > 【W3 勘误 · PATCH_SUGGESTIONS BLK-N5-1】改前：`grep -i "GapProt Version" ra2render/**` 本次 0 命中；改后：字面 grep `GapProt Version` 命中 `blitter_hooks.cpp:940,3411`、`ra2render.h:338`、`ra2render.ini:191` 及二进制 DLL，字面 0 命中不成立；但 `CreateStream` / `GapProtVersion` / `gap_prot_version` 在代码中 0 命中，无写 OLE 流实现，故结论不变：写档标记实现仍未落地；依据：`blitter_hooks.cpp:940,3411` 等实测；分级：[实证]
  2. **A3/A4/A5 行为验收**仍「初判无法判定」（`RESULT_GAP_P223.md:60-62`），战役轨结论文件不存在（`out/re_work/zcode_live/gap_p21_a3/RESULT_GAP_P21_A3.md`，本次 `find` 实测）。
  3. **MP 双端 ≥5000 帧 CRC 对拍**无真机联机窗口未测（`MASTER_STATUS.md:56`）；`errata_sync.md:18` 所述「冻结卡待 Lead 解冻」仍开放（另见 `R_pre_e14/exec_checklist.md` 全未勾）。
- 全量普查：`out/re_work/harness_survey/RE_PROGRESS_SURVEY.md` §6-D4（本条偏差首次登记处）、§5.2。

### ★终判回填（2026-10-01 13:15 之后追加）—— 上述「剩余缺口第 2 条」已部分闭环

上节写「A3/A4/A5 仍初判无法判定、`RESULT_GAP_P21_A3.md` 不存在」，属 12:2x 时点；同日 T-Z1 已收口（原文不删）：

| 判据 | 现判级 | 关键数值 |
|---|---|---|
| **A3** | **PASS（带窗口限定）** | on 档 3 会话（`r7on_full`/`r7bon_full`/`r9on_full`，最终构建 `626f98b6…`）`gap_cells=663` 全程 kept=100.0%、缝环核心 12 格 12/12、三点 in-process `90×6`、遥测 `installed=3/3`；off 对照 r1off 晚期 a5 `663→373→0` |
| **A4** | **未闭环（如实）** | 存档描述框三种注入均不进框 + 读档歧路载旧档；`A4-J2`（except 无新增）成立 |
| **A5** | **部分（PASS 方向）** | on 侧至 ~6min 全部已测窗零清零；`r9on` a5 = `[663, None, None, None]`；>6min 长窗未取得（跨档位会话静默退出，另卡） |

- **`G-CNT`/`G-RBK`/`q1`/`window` 四条门的状态不因终判而回退**——它们是代码面判据，已在上表按现码复算。
- **口径修正记录**：本报告若继续用「开图后缝是否被清」作唯一判据会误判——战役场景下缝环格**开局已 mapped** ⇒ `RevealArea2` 清零分支本就不触发，off 侧清零来自晚时 reshroud/crate 面（`RESULT_GAP_P21_A3.md` §A3 的 C-J3 修正）。⇒ 本目录 `R_p223_ready` 的 readiness 门表**不适用于战役验收**，两套判据不要混用。
- 仍未闭环（不变）：`GapProt Version` 存档标记（13:2x 复算 `grep` 0 命中）、MP 双端对拍、Lead 解冻项。
  > 【W3 勘误 · PATCH_SUGGESTIONS BLK-N5-1】注：字面 grep `GapProt Version` 有命中，但代码中无 `CreateStream` / 写 OLE 流实现，故写档标记未落地之实质结论不变。
- 证据：`gap_p21_a3/RESULT_GAP_P21_A3.md`（13:11）、`gap_p223/RESULT_GAP_P223.md:7,20,35,60-62`（12:44）、`MASTER_STATUS.md:13,36,43,44`（12:45）、`gap_p21_a3/{evidence/EVIDENCE_A3_RUNS.md, audit/AUDIT_HASH_RECORD.md}`。
