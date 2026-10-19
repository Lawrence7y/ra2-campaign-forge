# R-GAP-PSY 深潜：裂缝保护 NOP×3 未落地定谳 + PsychicReveal 清 `Cell+0x134` 完整链

> **任务**：R-GAP-PSY · 静态逆向取证 · gamemd.exe 1.001（YR）
> **交付**：本文件 + `out/re_work/re_sprint/R_gap_psy/**`
> **方法**：只读静态复算（PE 解析 + 字节断言 + 全 .text 扫描 + E8 xref）；**未启动游戏、未改动任何二进制**
> **写作用域**：`docs/re/gap_psychic_reveal_deep_dive.md` + `out/re_work/re_sprint/R_gap_psy/**`
>
> **证据图例**
> - **[实证]** = 已对 `ra2bench/gamemd.exe` 做字节级/扫描级核验（脚本见 `out/re_work/re_sprint/R_gap_psy/`）
> - **[推演]** = 由实证字节静态推导，未经真机行为确认
> - **[待实测]** = 需真机/调试器或外部安装清单才能定谳

---

## 0. 一句话结论

**三点成立**（P-2.1/P-2.2/P-2.3 原字节 3/3 MATCH、均为 6 字节 `mov [reg+0x134], 0`）；**PsychicReveal 清零链完整实证**（`SuperClass::Launch` 跳表 Case 11 → `0x6CD70C` → 双 `call RevealArea2` → `0x568273` 清 `GapsCoveringThisCell`）；**ra2render 代码轨 0 命中，三点均未落地** ⇒ 裂缝在任何 `RevealArea2` 开图后**永久静默失能**。建议落地顺序 **P-2.1 → P-2.2 → P-2.3**（先封 PsychicReveal 这条 22-call 高频路径）。
> 【W3 勘误 · W3-M6/ISSUE-STALE-P2-LANDING】改前：ra2render 代码轨 0 命中，三点均未落地；改后：P-2.1~P-2.3 裂缝三点 NOP 已于 09-30 完整落地进 blitter_hooks.cpp:3273-3287 并完成三处 DLL 同步；真机 A3 验收 PASS (带窗口限定)；依据：blitter_hooks.cpp:3273-3287 与 tools/verify_anchors.py；分级：P0

---

## 1. 证据基线

| 项 | 值 | 等级 |
|---|---|---|
| 目标二进制 | `ra2bench/gamemd.exe`（与 `ra2youli/gamemd.exe` 同哈希） | [实证] |
| 大小 | 4,825,360 B | [实证] |
| SHA-256 | `73201CC021497C9567742F718BF1DC78C22E9AE16C7E7365354B65F3FCF67476` | [实证] |
| PE | ImageBase `0x00400000`，PE32，5 节 | [实证] |
| `.text` | VA `0x00001000`，Raw `0x00001000`，RawSz `0x003E0000`（**raw = RVA**） | [实证] |
| 文件偏移公式 | `file_off = VA − 0x00400000`（三处均落 `.text`） | [实证] |
| 取证脚本 | `verify_gap_psy_bytes.py` / `verify_gap_psy_chain.py` | — |
| 取证输出 | `gap_psy_bytes_report.txt` / `gap_psy_chain_report.txt` | — |

---

## 2. `CellClass+0x134` 位域语义 [实证]

| 偏移 | 类型 | 名称 | 作用 | 实证写点 |
|---|---|---|---|---|
| `+0x12C` | u32 | `CopyFlags` | bit3 `0x08` Explored、bit4 `0x10` Mapped | `RevealArea2/3` 置位；`Reshroud` 清位 |
| `+0x130` | i32 | `ShroudCounter` | 遮蔽深度；直视=0，裂缝维持≥1 | `ReshroudCell` 累加；三处开图清 0 |
| **`+0x134`** | **u32** | **`GapsCoveringThisCell`** | **覆盖此格的敌方裂缝产生器引用计数** | **CreateGap `inc` / DestroyGap `dec` / 三处 bug 清 0** |
| `+0x140` | u32 | `RedrawFlags` | bit5 `0x20` 迷雾重绘 | `ReshroudCell` / 开图路径 |

**位域语义依据**：
- `CreateGap`（`0x6FB170`）：`mov ecx,[eax+0x134]; add eax,0x134; inc ecx; mov [eax],ecx` @ `0x6FB35C..0x6FB367` **[实证]**
- `DestroyGap`（`0x6FB470`）：`mov edx,[eax+0x134]; add eax,0x134; dec edx; mov [eax],edx` @ `0x6FB5EE..0x6FB5FD` **[实证]**
- `CreateGap` 对玩家/盟友裂缝**跳过盖印**（`0x6FB2D6 call 0x4F9A50` / `0x6FB2DD jne`）⇒ 计数**严格 = 对本地玩家敌对的裂缝数**（沿用 ATLAS §18.8 口径）**[实证]**

**不变量 I-GAP-1（硬）**：`CellClass::ReshroudCell`（`0x487690`）把 `ShroudCounter` **钳位为 `GapsCoveringThisCell` 的下界**：

```
00487690  56                      push esi
00487691  8B B1 30 01 00 00       mov esi, [ecx+0x130]     ; esi = ShroudCounter
00487697  83 FE FF                cmp esi, -1
0048769A  75 0A                   jnz +0x0A
0048769C  C7 81 30 01 00 00 00 00 00 00   mov [ecx+0x130], 0
004876A6  8B 81 30 01 00 00       mov eax, [ecx+0x130]
004876AC  40                      inc eax
004876AD  89 81 30 01 00 00       mov [ecx+0x130], eax     ; ShroudCounter++
004876B3  8B D0                   mov edx, eax
004876B5  8B 81 34 01 00 00       mov eax, [ecx+0x134]     ; eax = GapsCoveringThisCell
004876BB  3B D0                   cmp edx, eax
004876BD  7E 06                   jle +0x06
004876BF  89 81 30 01 00 00       mov [ecx+0x130], eax     ; ★钳位：ShroudCounter = GapsCovering
```

⇒ **若 `+0x134 == 0`，任何重遮蔽尝试都被截断为 0 ⇒ 该格永远无法回到黑雾（永久废缝）**。且 `CreateGap` 仅在裂缝建筑 `GeneratingGap` 跳变时调用，**不自愈**。 **[实证]**

---

## 3. PsychicReveal → `Cell+0x134` 完整链（文字化链路图）

### 3.1 超武分发层 [实证]

```
SuperClass::Launch (0x006CC390)
    │
    ├─ 8B 85 B4 00 00 00    mov eax, [ebp+0xB4]      ; SW Type index
    ├─ 83 F8 0B             cmp eax, 0x0B            ; 12 路跳表边界 @ 0x6CC3A9
    ├─ 0F 87 84 1A 00 00    ja  out_of_range
    └─ FF 24 85 44 DE 6C 00 jmp dword ptr [eax*4 + 0x6CDE44]
                              │
                              ▼
                    Jump Table @ 0x006CDE44 (12 × 4B)   [实证逐项复算]
                    ┌────────┬────────────┐
                    │ Case 0 │ 0x006CDA67 │
                    │ Case 1 │ 0x006CCE64 │
                    │ Case 2 │ 0x006CCD3F │
                    │ Case 3 │ 0x006CC3B9 │
                    │ Case 4 │ 0x006CC4B2 │
                    │ Case 5 │ 0x006CD2EE │  ParaDrop
                    │ Case 6 │ 0x006CD537 │
                    │ Case 7 │ 0x006CCDBD │
                    │ Case 8 │ 0x006CD66F │  SpyPlane
                    │ Case 9 │ 0x006CD7E7 │
                    │ Case10 │ 0x006CD072 │
                    │ Case11 │ 0x006CD70C │  ★ PsychicReveal
                    └────────┴────────────┘
```

### 3.2 PsychicReveal 函数体（`0x006CD70C`，218 B） [实证]

```
006CD70C  8A 43 6F                mov al, [ebx+0x6F]           ; SW 可用性旗
006CD70F  84 C0                   test al, al
006CD711  0F 84 1F 07 00 00       jz  0x6CDE36                 ; 不可用则退出
006CD717  8B 8C 24 E8 01 00 00    mov ecx, [esp+0x1E8]
006CD71E  51                      push ecx
006CD71F  B9 E8 F7 87 00          mov ecx, 0x0087F7E8          ; MapClass::Instance
006CD724  E8 77 80 E9 FF          call 0x005657A0              ; 目标坐标换算
        ...
006CD75F  8B 82 EC 0F 00 00       mov eax, [edx+0xFEC]         ; ★ Rules->PsychicRevealRadius
        ...
006CD773  E8 68 A1 E9 FF          call 0x005678E0              ; ★ RevealArea2 #1 (SkipReveal=0 开雾)
        ...
006CD784  8B 88 EC 0F 00 00       mov ecx, [eax+0xFEC]         ; ★ Rules->PsychicRevealRadius（第二次）
        ...
006CD79C  E8 3F A1 E9 FF          call 0x005678E0              ; ★ RevealArea2 #2 (SkipReveal=1 记探索)
        ...
006CD7BF  E8 5C 36 08 00          call 0x00750E20              ; 雷达事件/音效
```

**半径真相**：Case 11 **不读** `SW+0xF8 Range`（该假说在 ATLAS §7.4 已破产），而是**硬编码读 `Rules->PsychicRevealRadius`（`Rules+0xFEC`）**，两处读取（`0x6CD75F` / `0x6CD784`）均实证。 **[实证]**

### 3.3 RevealArea2 内层循环清零点（`0x00568273`） [实证]

`MapClass::RevealArea2`（`0x005678E0`）对圆域内每格执行：

```
    ; —— 每格三连写，前置同一套边界检查 + 从 [0x87F924 + index*4] 取 CellClass* ——
0056824A  89 99 30 01 00 00       mov [ecx+0x130], ebx     ; ShroudCounter = 0
00568250  7C 14                   jl  ...                  ; 消费 0x568248 cmp eax,ebx 的 flags
        ...
00568271  3B C3                   cmp eax, ebx
00568273  89 99 34 01 00 00       mov [ecx+0x134], ebx     ; ★★ BUG：GapsCovering = 0 ★★
00568279  7C 14                   jl  ...                  ; 消费同一 cmp 的 flags（mov 不改 flags）
        ...
00568297  83 89 2C 01 00 00 10    or  dword [ecx+0x12C], 0x10   ; CopyFlags |= Mapped
```

【勘误 2026-09-30 · R-E01 · errata_sync】原文 VA「0x568297」错误。该指令实际在 VA 0x0056829A（83 89 2C 01 00 00 10 = or dword [ecx+0x12C], 0x10）；0x568297 处字节为 50 DC AB 00，属上一条 mov ecx,0xABDC50 的立即数尾巴。权威：RESULT_GAP_P21.md §5 E-1。原文保留不删字。

**寄存器约定**：`ebx = 0`（全程零常量，循环内 `3B C3` / `3B CB` 反复使用）；`ecx = CellClass*`。 **[实证]**

### 3.4 完整因果链（PsychicReveal 路线）

```
玩家触发 PsychicReveal 超武
  → SuperClass::Launch 0x6CC390
  → jmp table 0x6CDE44[11] = 0x6CD70C
  → RevealArea2 0x5678E0  ×2（开雾 + 记探索）
  → 每格：GapsCoveringThisCell(+0x134) ← 0          【0x568273】
  → 扫描退去后 ReshroudCell 0x487690
       ShroudCounter = min(ShroudCounter, GapsCovering=0) = 0
  → 该格永远无法回到黑雾
  → 敌方 GapGenerator 覆盖区「永久静默失能」
```

---

## 4. SpySat / Reshroud 旁路链（另两点） [实证]

```
HouseClass::UpdateSpySat (0x00508F60)
    │
    ├─ 80 B8 A5 16 00 00 00   cmp byte [eax+0x16A5], 0     ; Type->SpySat  @ 0x508F88
    ├─ 74 65                  je  0x508FF6                 ; 非 SpySat 跳过  @ 0x508F8F
    │
    ├─ [在线] 0x509064  call 0x00577D90  RevealArea3
    │           └→ 每格：ShroudCounter=0 (0x577EBF)、GapsCovering=0 (0x577EC5) ★、CopyFlags|=0x18
    │              House+0x577A SpySatActive = 1
    │
    └─ [离线] 0x509012  call 0x00577AB0  MapClass::Reshroud
                └→ 每格：ShroudCounter=1 (0x577B56)、GapsCovering=0 (0x577B60) ★、CopyFlags&=~0x18
                   House+0x577A = 0  (0x509017)
```

| 函数 | 入口 | 含清零点 | E8 调用者（全 .text 扫描） |
|---|---|---|---|
| `MapClass::RevealArea2` | `0x005678E0` | `0x568273` | **22 处**（含 PsychicReveal 双调 `0x6CD773/0x6CD79C`） |
| `MapClass::RevealArea3` | `0x00577D90` | `0x577EC5` | 2 处：`0x481FC3`、`0x509064`（UpdateSpySat） |
| `MapClass::Reshroud` | `0x00577AB0` | `0x577B60` | 3 处：`0x481F93`、`0x509012`（UpdateSpySat）、`0x50BD20` |

**关键放大器**：`RevealArea2` 有 **22 个 E8 调用者**（`0x416557/0x416595/0x41AE5E/0x41AE95/0x41AF1A/0x41AF70/0x422689/0x4226BA/0x43F4A8/0x43F4FA/0x44082D/0x440856/0x6CD773/0x6CD79C/0x6E10E5/0x6E115B/0x6E12A6/0x6E1301/0x70B12C/0x70B170/0x70B1C2/0x70B26C`）—— **不止 PsychicReveal**。任何走 `RevealArea2` 的开图（超武、任务脚本、其它揭示能力）都会清计数。故 **P-2.1 是覆盖面最大的单点修复**。 **[实证]**

---

## 5. 三点落地表（可执行字节级）

| 项 | P-2.1 | P-2.2 | P-2.3 |
|---|---|---|---|
| **VA** | `0x00568273` | `0x00577EC5` | `0x00577B60` |
| **文件偏移** | `0x00168273` | `0x00177EC5` | `0x00177B60` |
| **节** | `.text` | `.text` | `.text` |
| **所在函数** | `RevealArea2` `0x5678E0` | `RevealArea3` `0x577D90` | `Reshroud` `0x577AB0` |
| **原字节** | `89 99 34 01 00 00` | `89 B8 34 01 00 00` | `89 98 34 01 00 00` |
| **原指令** | `mov [ecx+0x134], ebx` | `mov [eax+0x134], edi` | `mov [eax+0x134], ebx` |
| **源寄存器** | `ebx`（=0） | `edi`（=0） | `ebx`（=0） |
| **新字节** | `90 90 90 90 90 90` | `90 90 90 90 90 90` | `90 90 90 90 90 90` |
| **新指令** | NOP ×6 | NOP ×6 | NOP ×6 |
| **NOP 前语义** | 扫描区每格 `GapsCovering ← 0`（废缝） | 全图每格 `GapsCovering ← 0`（废缝） | 重遮蔽时每格 `GapsCovering ← 0`（废缝） |
| **NOP 后语义** | 保留 `ShroudCounter=0`、`CopyFlags\|=0x10` 等其余开图写入；**仅删除清计数副作用** | 保留 `ShroudCounter=0`、`CopyFlags\|=0x18`；仅删清计数 | 保留 `ShroudCounter=1`、`CopyFlags&=~0x18`；仅删清计数 |
| **回滚** | 备份 6B 原字节 → memcpy 还原；或 `EnableGapProtection=0` + 重启（安装门控） | 同左 | 同左 |
| **核验** | **[实证] MATCH** | **[实证] MATCH** | **[实证] MATCH** |

### 5.1 为什么是 6 字节 [实证]

- 编码为 `89 /r` + ModRM(`mod=10`, disp32) = **1 + 1 + 4 = 6 B**，无更短等价编码。
- **等长替换是硬约束**：不得引入 trampoline / 不得动 `.detour` 节（M-8 同款节约束，`landing_pack_gap_spysat.md:74`）；否则后续指令边界全部错位。
- 6×`90` 是**唯一**同时满足「不写内存、不改 flags、不碰寄存器」的 6B 替换。

### 5.2 是否有更小侵入替代 [实证/推演]

| 替代方案 | 改动面 | 结论 | 等级 |
|---|---|---|---|
| **A. 6×NOP（选定）** | 6 B × 3 点 | 最小语义侵入：只删一次 store | [实证] |
| **B. 只打 P-2.1（1×6B）** | 6 B × 1 点 | **最小落地面**，直接封 P0（PsychicReveal + 全部 22 个 RevealArea2 caller）；P-2.2/P-2.3 留待 SpySat 场景 | [推演] |
| **C. 翻 opcode `89`→`8B`（改 1 B）** | 1 B | `mov ebx,[ecx+0x134]` —— **破坏 ebx 零常量**（循环后续 `cmp eax,ebx` / `mov [r+off],ebx` 依赖）⇒ **不安全** | [实证] |
| **D. 翻 opcode 为 `add/or/and/xor/cmp`** | 1 B | 均**改 flags**；本点紧邻 `7C 14`(jl)，消费前一条 `cmp eax,ebx` 的 flags ⇒ **控制流被破坏，不安全** | [实证] |
| **E. disp32 `0x134`→`0x144`（改 1 B）** | 1 B | 改写为 CellClass 尾部 4 B；`sizeof=0x148`，`+0x144` 字段语义**未知**，可能踩到序列化尾巴 ⇒ **不推荐** | [推演] |
| **F. H-20-B 绘制谓词** | 0 B（.text 不动） | 只读 `Cell+0x134>0` 合成遮挡；**不阻止清零**，索敌/AI 仍会分叉 | [推演] |
| **G. H-20-C 私有雷达窗** | 代码侧 | 写 `s_radarSweepExploredFrame[]` 不动引擎字段；**绕开 RevealArea2**，产品语义改变 | [推演] |

**裁定**：字节长度**无法低于 6 B**；语义侵入**已是最小**（方案 A）；落地面可缩到 **1 点**（方案 B，推荐先做）。 **[实证/推演]**

---

## 6. 未落地影响范围

### 6.1 落地状态定谳

| 检查 | 结果 | 等级 |
|---|---|---|
| `ra2render/**` 全源码检索 `568273 / 577EC5 / 577B60` | **0 命中** | [实证] |
| `ra2render/**` 检索 `EnableGapProtection / InstallGapProtectionPatches / RemoveGapProtectionPatches` | **0 命中** | [实证] |
| gamemd.exe 三处原字节 | 3/3 仍为 `89 …`（**未被任何外部补丁改写**，本副本为原版） | [实证] |
| 现网 DLL 路线 | 「关 `BuildingType+0x16A5` + 绑 PsychicReveal + 恒写 `House+0x577A=0`」只封 **SpySat 路线** | [实证]（源码侧只读引用） |

⇒ **三点均未落地**。PsychicReveal 路线**完全未封**。 **[实证]**

### 6.2 影响面（未打补丁时）

| 维度 | 影响 | 等级 |
|---|---|---|
| **裂缝表现层** | GapGenerator 覆盖区在任何 `RevealArea2` 开图后永久失能（遮挡绘制消失、逻辑计数=0） | [实证] |
| **触发频率** | `RevealArea2` 共 22 个 caller —— PsychicReveal、任务脚本揭示、其它超武/能力开图均会踩中 | [实证] |
| **SpySat 路线** | 现网 `House+0x577A=0` 恒写可挡 `UpdateSpySat` 的 `RevealArea3/Reshroud` 分支；但 **`RevealArea3` 另有 caller `0x481FC3`、`Reshroud` 另有 caller `0x481F93/0x50BD20`**，未被该恒写覆盖 | [实证] |
| **索敌/开火** | `+0x134` 主导「被敌方裂缝覆盖」谓词；计数被清 ⇒ 索敌可见性分叉 | [推演]（ATLAS §18.8） |
| **存档 / 同步** | `Cell+0x134` 进 `.SAV` 且参与同步演进；补丁改变其演化 ⇒ **条件安全：必须全端同补丁**；混端必 DESYNC | [推演]（`net_sync_checksum.md` §4.2） |
| **自愈性** | 无。`CreateGap` 只在 `GeneratingGap` 跳变时调用，清零后不补计数 | [实证] |

---

## 7. Q4 回答：三函数内是否存在第 4 处 `+0x134` 写入

对三个函数带做全带 `89 /r`（mod=2, disp32=0x134）与 `C7 /0` 扫描：

| 函数带 | 范围 | `+0x134` 32-bit store | `+0x130` 写入（对照） |
|---|---|---|---|
| `RevealArea2` | `0x5678E0..0x568400` | **仅 `0x568273` 一处** | `0x5680A7`（=1）、`0x56824A`（=ebx） |
| `RevealArea3` | `0x577D90..0x578080` | **仅 `0x577EC5` 一处** | `0x577EBF`（=edi） |
| `Reshroud` 带 | `0x577A00..0x577D90` | **仅 `0x577B60` 一处** | `0x577B56`（=1） |

**⇒ 无第 4 处。三点清单完整。** **[实证]**（本流已把 ATLAS Q4/U8 从 P1 关闭为「已复算、无新增」）

全 .text 另有 20 处 `+0x134` store，但**不在这三函数内**（多为其它类型对象同偏移字段，或 `CreateGap/DestroyGap` 的 `inc/dec` 形式）；不在本补丁面内。

---

## 8. 文档勘误（只记于本文，不改旧文档）

| # | 冲突 | 旧文档写法 | 本流实证 | 处置 |
|---|---|---|---|---|
| **C-1** | 三点编号体系不一致 | `landing_pack_gap_spysat.md` 称整包为 **P-1**；`patch_hex_audit.md` / `landing_pack_preflight_audit.md` / `pending_execution_master_table` 称三点为 **P-2.1/P-2.2/P-2.3**；ATLAS §20.6 称 **H-20-A** | 同一地址同一字节，仅命名空间不同 | 新文档统一用 **P-2.1/P-2.2/P-2.3**（与 preflight/audit 对齐）；引用 landing_pack 时注明「其 P-1 = 本 P-2.1～P-2.3 合集」 |
| **C-2** | `Reshroud` 入口写法 | 部分段落只给清零点 `0x577B60`，未统一入口 | **入口 = `0x00577AB0`**（3 处 E8 实证 + ATLAS `0x509012`/`0x50BD20` 一致） | 本文以 `0x577AB0` 为准 |
| **C-3** | RevealArea2 caller 数 | 旧文档只点名 PsychicReveal 双调 | **全 .text 22 处 E8 caller**（见 §4 表） | 影响面扩大；强化「先打 P-2.1」依据 |
| **C-4** | PsychicReveal 半径来源 | 早期假说 `SW+0xF8 Range` | **只读 `Rules+0xFEC PsychicRevealRadius`**（`0x6CD75F`/`0x6CD784` 两处） | 与 ATLAS §7.4 一致，本文复证 |
| **C-5** | 「未落地」证据形态 | 旧文档为 `ra2render/**` grep 0 命中（源码轨） | 本流**双轨确认**：源码 0 命中 **且** gamemd.exe 副本三处原字节仍为 `89 …` | 已闭环「本副本未打补丁」；外部加载器仍属 Q1（见 §9） |

---

## 9. 风险与门控

| 风险 | 说明 | 等级 | 缓解 |
|---|---|---|---|
| **R-1 同步语义** | `+0x134` 演化被改 ⇒ 混端（一端 NOP、一端原版）必分叉 | 极高 | 全端同构建 + 同 `EnableGapProtection`；严禁混端联机 |
| **R-2 存档结构** | `Cell+0x134` 进 `.SAV`；补丁后存档与原版不互通 | 极高 | 补丁局存档标记版本；卸载后不读补丁档 |
| **R-3 Q1 外部安装者** | 本流只读了 `ra2render/**` + 本 gamemd.exe 副本；**不排除外部补丁器/加载器**已在他处安装 | P0 | 真机断点读 `0x568273` 首字节：`89`=未打、`90`=已打 |
| **R-4 flags 邻接** | P-2.1 位于 `cmp eax,ebx` 与 `jl` 之间；替换指令**绝不可改 flags** | 高 | 仅用纯 `90`；禁用任何 `add/or/and/xor/cmp` 类 1B 翻法（§5.2-D） |
| **R-5 ebx/edi 零常量** | P-2.1/P-2.3 的源寄存器是循环零常量，后续仍被使用 | 高 | 仅用 NOP；禁用 `89→8B` 载入翻法（§5.2-C） |
| **R-6 部分落地** | 只打 P-2.2/P-2.3 不打 P-2.1 ⇒ PsychicReveal 路线仍废缝 | 中 | 落地顺序强制 P-2.1 优先 |

---

## 10. 建议落地顺序

| 序 | 动作 | 理由 |
|---|---|---|
| **1** | **P-2.1** `0x568273` 6×NOP | 封 PsychicReveal + **全部 22 个 RevealArea2 caller**；P0 唯一必打点 |
| **2** | **P-2.2** `0x577EC5` 6×NOP | 封 SpySat 全图开 + `0x481FC3` 旁路 |
| **3** | **P-2.3** `0x577B60` 6×NOP | 封 SpySat 离线重遮 + `0x50BD20` 建筑摧毁旁路 |
| 4 | 真机读 `0x568273` 首字节（Q1） | 确认无外部安装者 |
| 5 | MP 门控矩阵 + 双端对拍 | R-1/R-2 验收 |

**回滚顺序**（逆）：先 P-2.3 → P-2.2 → P-2.1，或整组 memcpy 还原 `s_origGapProtectBytes[3][6]`。

---

## 11. 证据等级汇总

| 结论 | 等级 | 证据 |
|---|---|---|
| 三处原字节 3/3 MATCH | [实证] | `gap_psy_bytes_report.txt` §1 |
| 三点均为 6B `mov [reg+0x134], r32(=0)` | [实证] | 同上 §2 上下文窗 |
| PsychicReveal = 跳表 Case 11 | [实证] | `gap_psy_chain_report.txt` §E；跳表 12 项逐条 |
| PsychicReveal 双调 `RevealArea2` | [实证] | §B：`0x6CD773`/`0x6CD79C` → `0x5678E0` |
| 半径读 `Rules+0xFEC` | [实证] | `0x6CD75F`/`0x6CD784` |
| 三函数内各仅 1 处 `+0x134` 写（Q4 关闭） | [实证] | §F 全带扫描 |
| `ReshroudCell` 钳位 ⇒ 永久废缝 | [实证] | §2 反汇编 `0x4876B5..0x4876BF` |
| `CreateGap/DestroyGap` inc/dec | [实证] | §2 `0x6FB35C`/`0x6FB5EE` |
| `RevealArea2` 22 caller | [实证] | §4 E8 全扫 |
| ra2render 0 命中 | [实证] | §J |
| 6×NOP 语义等价（只删 store） | [实证] | §5.1 |
| 更小字节替代均不安全 | [实证] | §5.2 C/D（flags/寄存器邻接） |
| disp 改道 `+0x144` 可行性 | [推演] | §5.2 E |
| 索敌/开火分叉 | [推演] | 谓词 `+0x134>0` |
| 补丁后同步/存档影响 | [推演] | net_sync §4.2 |
| 真机首字节 / 行为验收 | [待实测] | Q1、A1.2–A1.5 |

---

## 12. 附件清单

| 文件 | 内容 |
|---|---|
| `out/re_work/re_sprint/R_gap_psy/verify_gap_psy_bytes.py` | PE 解析 + 三处字节断言 + 全 .text `+0x134` store 扫描 + xref |
| `out/re_work/re_sprint/R_gap_psy/verify_gap_psy_chain.py` | 指令边界安全 xref + PsychicReveal 链 + 函数带扫描 + ra2render grep |
| `out/re_work/re_sprint/R_gap_psy/gap_psy_bytes_report.txt` | pass-1 输出 |
| `out/re_work/re_sprint/R_gap_psy/gap_psy_chain_report.txt` | pass-2 输出 |

---

*本文为 R-GAP-PSY 静态取证交付。未启动游戏、未改写任何二进制、未触碰 `ra2render/**` / `gamemd.exe` / 台账 / 看板。*
