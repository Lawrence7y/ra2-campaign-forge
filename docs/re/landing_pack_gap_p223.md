# ZCode 落地卡 · P-2.2/P-2.3 裂缝保护（RevealArea3 / Reshroud 清 `GapsCoveringThisCell`）

> **卡号**：`ZC-GAP-P223` · **优先级**：P1（SpySat 路线 + 旁路必打点；P0 已由 P21 封 RevealArea2）  
> **执行方**：ZCode（真机/补丁安装唯一写者）· **起草**：MiMo（R-GAP-P223 静态定谳）  
> **上游**：`docs/re/gap_psychic_reveal_deep_dive.md`（R-GAP-PSY）§4–§5 · `docs/re/landing_pack_gap_p21.md`（ZC-GAP-P21）· 复算脚本 `out/re_work/re_sprint/R_gap_psy/`  
> **本卡范围**：**仅 P-2.2 + P-2.3 两点**（SpySat/Reshroud 侧清零点）。P-2.1 **已另卡**（ZC-GAP-P21）。  
> **证据基线**：`gamemd.exe` 1.001 · SHA-256 `73201CC021497C9567742F718BF1DC78C22E9AE16C7E7365354B65F3FCF67476` · MD5 `4f37486e…` · ImageBase `0x00400000` · `file_off = VA − 0x00400000`  
> 【W3 勘误 E-W3-01】原句 `FileOffset = VA − 0x400000` 仅在 `.text/.rdata/.data` 成立；
> 通用式为 `FileOffset = 段.PointerToRawData + (VA − 段.VirtualAddress)`，
> 本镜像 `.rsrc`/`.detour` 为 `VA − 0x6FC000`。依据：out/re_work/_lead_baseline/W3/LEAD_ERRATUM_E-W3-01_fileoffset_rule.md；分级：[实证]
> **静态证据**：`out/re_work/re_sprint/R_gap_p223/claims_p223.txt`（字节窗独立复核）· 引用 `gap_psy_bytes_report.txt` MATCH 3/3

---

## 0. 一句话

把 `MapClass::RevealArea3` 内 `mov [eax+0x134], edi`（`0x577EC5`）与 `MapClass::Reshroud` 内 `mov [eax+0x134], ebx`（`0x577B60`）的 **各 6 字节**换成 **`90×6`**，删除「SpySat 全图开 / 离线重遮 都废缝」的副作用；其余写入（`ShroudCounter`、`CopyFlags`、`RedrawFlags`）**原样保留**。

---

## 1. 执行表（字节级，等长替换）

### 1.0 总表

| 项 | **P-2.2** | **P-2.3** |
|---|---|---|
| **步骤 ID** | `P-2.2` | `P-2.3` |
| **VA** | `0x00577EC5` | `0x00577B60` |
| **文件偏移** | `0x00177EC5` | `0x00177B60` |
| **节** | `.text` | `.text` |
| **函数** | `MapClass::RevealArea3` @ `0x00577D90` | `MapClass::Reshroud` @ `0x00577AB0` |
| **原字节（6B）** | `89 B8 34 01 00 00` | `89 98 34 01 00 00` |
| **原指令** | `mov [eax+0x134], edi`（`edi=0` 零常量） | `mov [eax+0x134], ebx`（`ebx=0` 零常量） |
| **新字节（6B）** | `90 90 90 90 90 90` | `90 90 90 90 90 90` |
| **新指令** | `nop ×6` | `nop ×6` |
| **改动长度** | **必须 6==6 等长**（禁 trampoline / 禁动 `.detour`） | 同左 |
| **语义（NOP 前）** | SpySat 全图开：每格 `GapsCovering ← 0`（废缝） | SpySat 离线重遮：每格 `GapsCovering ← 0`（废缝） |
| **语义（NOP 后）** | 保留 `ShroudCounter←0`、`CopyFlags\|=0x18`；**仅删清计数** | 保留 `ShroudCounter←1`、`CopyFlags&=~0x18`、`RedrawFlags&=~0x3`；**仅删清计数** |
| **核验** | **[实证] MATCH**（`gap_psy_bytes_report.txt` §1） | **[实证] MATCH** |

### 1.1 上下文窗（安装前后自检用）

#### P-2.2 窗（`0x577EC5` 邻域，全指令边界）

| VA | 原字节 | 说明 |
|---|---|---|
| `0x577EBB` | `3B CA` | `cmp ecx, edx` —— 产生 `je` 所需 flags |
| `0x577EBD` | `74 2A` | `je +0x2A` —— **消费上一条 `cmp` 的 flags**（在 ShroudCounter 写之前，与本点无 flags 邻接） |
| `0x577EBF` | `89 B8 30 01 00 00` | `mov [eax+0x130], edi` —— `ShroudCounter ← 0`（**保留**） |
| `0x577EC5` | `89 B8 34 01 00 00` | **★ 本卡替换点（P-2.2）** |
| `0x577ECB` | `8B 90 2C 01 00 00` | `mov edx, [eax+0x12C]` —— 加载 `CopyFlags`（**保留**） |
| `0x577ED1` | `83 CA 18` | `or edx, 0x18` |
| `0x577ED4` | `89 90 2C 01 00 00` | `mov [eax+0x12C], edx` —— `CopyFlags \|= 0x18`（Mapped\|Explored，**保留**） |

**flags 安全性（优于 P-2.1）**：替换点前后均为 `mov`（不改 flags），**无**「`cmp` → 本点 → `jcc`」三明治；紧邻的 `je` 在 ShroudCounter 写之前消费 flags，与本点隔离。仍**只许 `90`**（统一约定，禁 1B 翻法）。

#### P-2.3 窗（`0x577B60` 邻域，全指令边界）

| VA | 原字节 | 说明 |
|---|---|---|
| `0x577B3B` | `3B C3` | `cmp eax, ebx` |
| `0x577B3D` | `74 39` | `je +0x39`（消费 `cmp` flags，在 CopyFlags 写之前，与本点无 flags 邻接） |
| `0x577B4E` | `89 88 2C 01 00 00` | `mov [eax+0x12C], ecx` —— `CopyFlags &= ~0x18`（**保留**） |
| `0x577B56` | `C7 80 30 01 00 00 01 00 00 00` | `mov dword [eax+0x130], 1` —— `ShroudCounter ← 1`（**保留**） |
| `0x577B60` | `89 98 34 01 00 00` | **★ 本卡替换点（P-2.3）** |
| `0x577B66` | `89 90 40 01 00 00` | `mov [eax+0x140], edx` —— `RedrawFlags ← (edx & ~0x3)`（**保留**） |
| `0x577B6C` | `E8 1F 07 00 00` | `call …`（后续 `3B C3`/`75 C7` 仍用 `ebx`） |

**flags 安全性**：替换点前为 `mov imm32`、后为 `mov`，**无 flags 三明治**；但 `ebx` 零常量在 `0x577B71` `cmp eax,ebx` 仍被消费 ⇒ **禁 `89→8B` 载入翻法**（同 P-2.1 R-5）。

### 1.2 语义边界（只许删这一件事）

| 写点 | 动作 | 本卡 |
|---|---|---|
| **RevealArea3** `0x577EBF` `mov [eax+0x130], edi` | `ShroudCounter ← 0` | **保留** |
| **RevealArea3** `0x577EC5` `mov [eax+0x134], edi` | `GapsCoveringThisCell ← 0` | **删除（NOP）** |
| **RevealArea3** `0x577ED4` `mov [eax+0x12C], edx` | `CopyFlags \|= 0x18` | **保留** |
| **Reshroud** `0x577B4E` `mov [eax+0x12C], ecx` | `CopyFlags &= ~0x18` | **保留** |
| **Reshroud** `0x577B56` `mov dword [eax+0x130], 1` | `ShroudCounter ← 1` | **保留** |
| **Reshroud** `0x577B60` `mov [eax+0x134], ebx` | `GapsCoveringThisCell ← 0` | **删除（NOP）** |
| **Reshroud** `0x577B66` `mov [eax+0x140], edx` | `RedrawFlags &= ~0x3` | **保留** |

**禁止改写零常量寄存器**：P-2.2 的 `edi`、P-2.3 的 `ebx` 在循环内反复用作 0；只许 NOP，禁任何改寄存器的替换。

---

## 2. 安装前置（全部 PASS 才允许写）

| # | 检查 | 期望 | 失败则 |
|---|---|---|---|
| G0.1 | 目标文件 SHA-256 | `73201CC0…F67476` | **拒绝安装** |
| G0.2a | `VA 0x577EC5` 文件偏移 `0x177EC5` 首 6B | `89 B8 34 01 00 00` | 若已是 `90×6`：报告「已打」并跳过；其它：**拒绝** |
| G0.2b | `VA 0x577B60` 文件偏移 `0x177B60` 首 6B | `89 98 34 01 00 00` | 同上 |
| G0.3a | P-2.2 窗前 `0x577EBF` = `89 B8 30 01 00 00` | MATCH | 拒绝 |
| G0.3b | P-2.2 窗后 `0x577ECB` = `8B 90 2C 01 00 00` | MATCH | 拒绝 |
| G0.4a | P-2.3 窗前 `0x577B56` = `C7 80 30 01 00 00 01 00 00 00` | MATCH | 拒绝 |
| G0.4b | P-2.3 窗后 `0x577B66` = `89 90 40 01 00 00` | MATCH | 拒绝 |
| G0.5 | `.text` 节可写性/映像基址 | PE32 / base `0x400000` | 拒绝 |
| G0.6 | 开关键 `EnableGapProtection` | 显式 `1` 才安装 | 默认 **0=不装**（零行为变化） |
| G0.7 | P-2.1 状态（推荐，非硬性） | 若 P-2.1 已装则记录；未装则**警告**「仅装 P-2.2/2.3，PsychicReveal 路线仍废缝」 | 警告不拒绝 |

**Q1 真机首字节（安装前）**：

| 点 | 断点/读地址 | 首字节判定 |
|---|---|---|
| P-2.2 | `0x577EC5` | `89`=未打 / `90`=已有外部补丁（**停手并上报**，禁止覆盖未知安装者） |
| P-2.3 | `0x577B60` | `89`=未打 / `90`=已有外部补丁（**停手并上报**） |

---

## 3. 开关 · 遥测 · 回滚

### 3.1 开关（推荐：与 P21 **同键** `EnableGapProtection`）

| 键 | 默认 | 语义 |
|---|---|---|
| `EnableGapProtection` | **`0`** | `1` 时安装 **本构建已实现的全部 P-2.x 点**（P21 构建=P-2.1；本卡构建=P-2.1+P-2.2+P-2.3）；`0` 时不碰 `.text` |

**推荐同键的理由（裁决）**：

1. **产品契约已按「一键 + 计数」设计**：`savegame_product_checklist.md` G2.1「仅当 `gapProtectionPatchesInstalled==3` 才写 `GapProt Version=1`」、G4.1「握手键含 `EnableGapProtection` + `gapProtectionPatchesInstalled`（期望 **3**）」——三点是**一个保护包**。
2. **同一 bug 语义**：三点均为「清 `Cell+0x134 GapsCoveringThisCell`」，用户心智=「裂缝保护」一个开关。
3. **P21 已裁「键名勿占用」**：`landing_pack_gap_p21.md` §3.1 明文「`EnableGapProtectP22`/`P23` 键名勿提前占用」——本卡**不建独立键**，正好遵守。
4. **回滚不依赖键粒度**：字节级可分点 `memcpy` 还原（见 §3.3），无需独立键即可单点回滚。

**备选（不推荐）**：独立键 `EnableGapProtectP22`/`EnableGapProtectP23`——需同步改握手契约、存档标记矩阵、安装包文案三处，与现有产品检查单「期望 3」冲突，成本高收益低。

**计数遥测**：`gapProtectionPatchesInstalled`（0..3）= 本进程实际写入的 NOP 点数。分阶段安装时中间态可能为 1（仅 P-2.1）或 3（全装）；**仅 ==3 时写存档标记流**（对齐 G2.1）。

**联机**：`MpActive` 为真时 **强制不安装**（与 `EnableMinimapFog` / P21 同级门控）；启动日志打印 `GapProtection=on|off|forced-off-mp`（追加 `installed=N`）。

### 3.2 遥测（只读计数，禁止热路径膨胀）

| 计数器 | 含义 |
|---|---|
| `gapProtectionPatchesInstalled` | 0..3，实际写入点数（握手/存档标记判据） |
| `gapProtectSkipClearCount` | 可选软计数 |
| `gapProtectRevealArea3Calls` / `gapProtectReshroudCalls` | 可选，仅诊断档 |

### 3.3 回滚

**顺序（硬回滚时强制逆序）**：**先 P-2.3 → 再 P-2.2 → 最后 P-2.1**。

| 层级 | 操作 | 效果 |
|---|---|---|
| **软** | `EnableGapProtection=0` + 重启游戏/重载 DLL | 新进程不写补丁（安装态在 init 决定，`LoadConfig` 仅 init 读一次） |
| **硬·单点** | 备份 `s_origP22[6]` / `s_origP23[6]` → `memcpy` 还原 | 可独立还原任一点；逆序 P-2.3→P-2.2→P-2.1 |
| **硬·整组** | `s_origGapProtectBytes[3][6]` 一次 `memcpy` | 三点同时还原 |
| **卸载工具** | `--uninstall-p23` / `--uninstall-p22` / `--uninstall-p21` / `--uninstall-gap-all` | 分点或整组 |

**逆序理由**：安装顺序 P-2.1→P-2.2→P-2.3（先封 22-caller 高频面）；回滚逆序保证「后装先拆」，避免中间态只剩 P-2.3（Reshroud 单点）而 P-2.2 仍 NOP 的语义撕裂。

### 3.4 与 P21 同装 / 分装风险

| 模式 | 描述 | 优点 | 风险 | 裁决 |
|---|---|---|---|---|
| **同装**（一次写 3 点） | `EnableGapProtection=1` 一次装齐 P-2.1+2.2+2.3 | `gapProtectionPatchesInstalled=3` 一步到位；存档标记契约简单（G2.1 直接满足） | 若 P-2.2/2.3 有未知问题，需字节级分点回滚（软键一关全关） | **推荐**（产品契约默认） |
> 【W3 勘误 · W3-A6/ISSUE-DEFAULT-GAPPROTECTION】改前：EnableGapProtection=1；改后：EnableGapProtection=0  ; [代码/出厂默认0，安全侧；测试或启用时显式置1]；依据：ra2render/blitter_hooks.cpp:606; ra2render/ra2render.ini:199; config_key_matrix.md:109；分级：P0
| **分装**（先 P-2.1，后 P-2.2/2.3） | 两次安装会话 | P0 先封最大面（22 caller），风险分期 | 中间态 `installed=1≠3` 不写存档标记；混端检测复杂（0 点/1 点/3 点三种端）；若中间态存档，卸载后档兼容性更难 | **允许但不推荐**；分装期间**禁止**联机、**禁止**存档作为补丁档 |

**分装过渡期硬约束**：`gapProtectionPatchesInstalled < 3` 时——(a) 不写 `GapProt Version` 标记流；(b) 读档按原版档处理（不拒读，因未标记）；(c) 启动日志打 `GapProtection=on installed=N (PARTIAL)` 告警。

---

## 4. 真机验收用例（Z- 系列，最小 5 条）

| ID | 步骤 | 期望 |
|---|---|---|
| **A1** | 默认配置启动（`EnableGapProtection=0`） | 两点字节仍为原版（`0x577EC5`/`0x577B60` = `89 …`）；无崩溃；日志 `GapProtection=off` |
| **A2** | `EnableGapProtection=1` 启动 | `0x577EC5`= `90×6`；`0x577B60`= `90×6`；上下文窗 G0.3/G0.4 未变；日志 `GapProtection=on installed=3`（或 `installed=N` 如实） |
| **A3** | **SpySat 在线**：造 SpySat 建筑通电 → `UpdateSpySat` 走 `0x509064 call RevealArea3`；同时敌方 GapGenerator 覆盖己方建筑 | 全图开后**裂缝遮挡仍在**（`GapsCoveringThisCell` 未被清）；`CopyFlags\|=0x18` 生效（地图已探索）；对比未打补丁的「全图开后永久废缝」 |
| **A4** | **SpySat 离线**：断电/关闭 SpySat → `UpdateSpySat` 走 `0x509012 call Reshroud`；随后存 `.SAV` → 读档 | 重遮后该格可回黑雾（`ShroudCounter=1` 且 `GapsCovering>0` 时钳位生效）；缝态保持；`except.txt` 空 |
| **A5** | **旁路覆盖**：(a) 触发 `0x481FC3` 路径调 `RevealArea3`（非 UpdateSpySat）；(b) 触发 `0x50BD20` 路径调 `Reshroud`（非 UpdateSpySat，如 SpySat 建筑摧毁） | 两条旁路后 `GapsCoveringThisCell` **均未被清零**；裂缝遮挡仍在；无崩溃 |

**禁止把「没崩」当成功**：A3/A4/A5 必须有「缝仍在」的截图/像素或逻辑计数（`GapsCoveringThisCell` 抽样读值 > 0）证据。

**A5 旁路说明**（为何必须单测）：

| 旁路 | 调用点 | 函数 | 与 SpySat 门控关系 |
|---|---|---|---|
| `0x481FC3` | `call RevealArea3` | 非 `UpdateSpySat` 的 RevealArea3 caller（全 .text 仅 2 个 E8，另一个是 `0x509064`） | **不被** `House+0x577A=0` 恒写覆盖 |
| `0x50BD20` | `call Reshroud` | 非 `UpdateSpySat` 的 Reshroud caller（全 .text 3 个 E8：`0x481F93`/`0x509012`/`0x50BD20`） | 同上；`0x50BD12` 附近读 `House+0x577A`，疑为建筑摧毁/SpySat 失效路径 |

⇒ 现网「关 `Type+0x16A5` + 恒写 `House+0x577A=0`」只能挡 `UpdateSpySat` 分支，**挡不住这两条旁路**；P-2.2/P-2.3 是旁路的**唯一字节级封堵**。

---

## 5. 风险（执行方必读）

| ID | 风险 | 要求 |
|---|---|---|
| R-1 | **混端 DESYNC**（`+0x134` 进 `.SAV`） | 禁止联机混端；全端同构建同开关；`installed` 计数必须全端一致 |
| R-2 | 存档与原版不互通 | 补丁局存档标记（仅 `installed==3` 时写）；卸载后不读补丁档 |
| R-3 | 外部安装者 | G0.2/Q1 首字节门禁（两点分别判） |
| R-4 | flags/寄存器邻接 | 只许 `90`；**禁止** `89→8B`、`add/or/and/xor/cmp` 类 1B 改法；P-2.2 的 `edi`、P-2.3 的 `ebx` 零常量不得改写 |
| R-5 | 只打 P-2.2/2.3 不打 P-2.1 | PsychicReveal 路线（22 caller）仍废缝；G0.7 警告；落地顺序强制 P-2.1 优先 |
| R-6 | 分装中间态 | `installed<3` 时禁联机、禁存补丁档、日志 PARTIAL 告警 |
| R-7 | 回滚顺序错误 | 硬回滚强制逆序 P-2.3→P-2.2→P-2.1；禁止只拆中间点造成语义撕裂 |

---

## 6. 交付回执（填完交回）

```
ZC-GAP-P223 RESULT
- build/md5(gamemd):
- install path: (ra2render hook | external patcher | ...)
- EnableGapProtection:
- gapProtectionPatchesInstalled:
- G0.1–G0.7: PASS/FAIL
- Q1 first byte before @0x577EC5 / @0x577B60:
- bytes after @0x577EC5:
- bytes after @0x577B60:
- A1..A5: (each PASS/FAIL + evidence path)
- except.txt: empty|path
- rollback order tested (P-2.3→P-2.2→P-2.1): y/n
- same-install / split-install mode: (same|split)
```

---

## 7. 不在本卡

- P-2.1 `0x568273`（RevealArea2）— 已由 `ZC-GAP-P21` 覆盖  
- MP 握手字段扩展 — 维持既有 MP 门控，不加新握手键（沿用 P21 裁决）  
- SpySat 门控 `0x508F8F je→jmp`（P-2 / `EnableSpySatGate`）— 另轨（`landing_pack_gap_spysat.md` §2）  
- S1 TYPE 补丁 / G-07 Remove 还原 — 另轨  
- `ra2render` 源码重构 / 绘制谓词 H-20-B / 私有雷达窗 H-20-C  
- 台账/看板登记 — 由 Lead 收口

---

## 8. 落地顺序与依赖（与 P21 合并视图）

| 序 | 动作 | 卡 | 理由 |
|---|---|---|---|
| 1 | P-2.1 `0x568273` 6×NOP | ZC-GAP-P21 | 封 PsychicReveal + 22 个 RevealArea2 caller（P0） |
| 2 | P-2.2 `0x577EC5` 6×NOP | **本卡** | 封 SpySat 全图开 + `0x481FC3` 旁路 |
| 3 | P-2.3 `0x577B60` 6×NOP | **本卡** | 封 SpySat 离线重遮 + `0x50BD20` 旁路 |
| 4 | 真机 Q1 三点首字节 | 两卡共用 | 确认无外部安装者 |
| 5 | MP 门控矩阵 + 双端对拍 | 两卡共用 | R-1/R-2 验收 |

**回滚顺序（逆）**：P-2.3 → P-2.2 → P-2.1，或整组 `memcpy` 还原 `s_origGapProtectBytes[3][6]`。

---

*依据：R-GAP-PSY 深潜 §4–§5（RevealArea3/Reshroud 清零点 + caller 表）；`gap_psy_bytes_report.txt` 三点 MATCH + 上下文窗；`savegame_product_checklist.md` G1/G2/G4（一键+计数=3 产品契约）；`gap_protection_install_spec.md`（P-2.1 安装路径模板）；`landing_pack_gap_p21.md`（同键裁决 + 键名不占用）。P-2.2/P-2.3 原字节 2/2 MATCH；6×NOP 为唯一「不写内存、不改 flags、不碰寄存器」的 6B 替换。*
