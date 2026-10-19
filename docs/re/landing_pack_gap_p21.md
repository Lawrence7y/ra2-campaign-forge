# ZCode 落地卡 · P-2.1 裂缝保护（RevealArea2 清 `GapsCoveringThisCell`）

> **卡号**：`ZC-GAP-P21` · **优先级**：P0（裂缝永久静默失能唯一必打点）  
> **执行方**：ZCode（真机/补丁安装唯一写者）· **起草**：MiMo（R-GAP-PSY 静态定谳）  
> **上游**：`docs/re/gap_psychic_reveal_deep_dive.md`（R-GAP-PSY）· 复算脚本 `out/re_work/re_sprint/R_gap_psy/`  
> **本卡范围**：**仅 P-2.1 一点**（方案 B 最小落地面）。P-2.2/P-2.3 **本卡不做**，留后续卡。  
> **证据基线**：`gamemd.exe` 1.001 · SHA-256 `73201CC021497C9567742F718BF1DC78C22E9AE16C7E7365354B65F3FCF67476` · MD5 `4f37486e…` · ImageBase `0x00400000` · `file_off = VA − 0x00400000`
> 【W3 勘误 E-W3-01】原句 `FileOffset = VA − 0x400000` 仅在 `.text/.rdata/.data` 成立；
> 通用式为 `FileOffset = 段.PointerToRawData + (VA − 段.VirtualAddress)`，
> 本镜像 `.rsrc`/`.detour` 为 `VA − 0x6FC000`。依据：out/re_work/_lead_baseline/W3/LEAD_ERRATUM_E-W3-01_fileoffset_rule.md；分级：[实证]

---

## 0. 一句话

把 `MapClass::RevealArea2` 内每格 `mov [ecx+0x134], ebx`（`GapsCoveringThisCell ← 0`）的 **6 字节**换成 **`90×6`**，删除「任何开图都废缝」的副作用；其余开图写入（`ShroudCounter=0`、`CopyFlags|=0x10`）**原样保留**。

---

## 1. 执行表（字节级，等长替换）

| 项 | 值 |
|---|---|
| **步骤 ID** | `P-2.1` |
| **VA** | `0x00568273` |
| **文件偏移** | `0x00168273` |
| **节** | `.text` |
| **函数** | `MapClass::RevealArea2` @ `0x005678E0` |
| **原字节（6B）** | `89 99 34 01 00 00` |
| **原指令** | `mov [ecx+0x134], ebx` （`ebx=0` 循环零常量） |
| **新字节（6B）** | `90 90 90 90 90 90` |
| **新指令** | `nop ×6` |
| **改动长度** | **必须 6==6 等长**（禁 trampoline / 禁动 `.detour`） |

### 1.1 上下文窗（安装前后自检用，共 21B）

> 【勘误 2026-09-30 · R-E02 · errata_sync】原文「共 21B」→ 订正为：指令对齐合计 **17B**（2+6+2+7）。若按首末 VA 跨度计则 45B，两种口径不可混用。权威：RESULT_GAP_P21.md §5 E-2 / p223_readiness_check.md:106。原文保留不删字。

| 偏移相对 VA | 原字节 | 说明 |
|---|---|---|
| `0x568271` | `3B C3` | `cmp eax, ebx` —— **产生后续 `jl` 所需 flags** |
| `0x568273` | `89 99 34 01 00 00` | **★ 本卡替换点** |
| `0x568279` | `7C 14` | `jl …` —— **消费上一条 `cmp` 的 flags**（`mov`/`nop` 均不改 flags） |
| `0x568297` | `83 89 2C 01 00 00 10` | `or dword [ecx+0x12C], 0x10`（保留，勿动） |

【勘误 2026-09-30 · R-E01 · errata_sync】原文 VA「0x568297」错误。该指令实际在 VA 0x0056829A（83 89 2C 01 00 00 10 = or dword [ecx+0x12C], 0x10）；0x568297 处字节为 50 DC AB 00，属上一条 mov ecx,0xABDC50 的立即数尾巴。权威：RESULT_GAP_P21.md §5 E-1。原文保留不删字。

### 1.2 语义边界（只许删这一件事）

| 写点 | 动作 | 本卡 |
|---|---|---|
| `0x56824A` `mov [ecx+0x130], ebx` | `ShroudCounter ← 0` | **保留** |
| `0x568273` `mov [ecx+0x134], ebx` | `GapsCoveringThisCell ← 0` | **删除（NOP）** |
| `0x568297` `or [ecx+0x12C], 0x10` | `CopyFlags \|= Mapped` | **保留** |

【勘误 2026-09-30 · R-E01 · errata_sync】原文 VA「0x568297」错误。该指令实际在 VA 0x0056829A（83 89 2C 01 00 00 10 = or dword [ecx+0x12C], 0x10）；0x568297 处字节为 50 DC AB 00，属上一条 mov ecx,0xABDC50 的立即数尾巴。权威：RESULT_GAP_P21.md §5 E-1。原文保留不删字。

---

## 2. 安装前置（全部 PASS 才允许写）

| # | 检查 | 期望 | 失败则 |
|---|---|---|---|
| G0.1 | 目标文件 SHA-256 | `73201CC0…F67476` | **拒绝安装** |
| G0.2 | `VA 0x568273` 文件偏移 `0x168273` 首 6B | `89 99 34 01 00 00` | 若已是 `90×6`：报告「已打」并跳过；其它：**拒绝** |
| G0.3 | 窗前 `0x568271` = `3B C3` | MATCH | 拒绝 |
| G0.4 | 窗后 `0x568279` = `7C 14` | MATCH | 拒绝 |
| G0.5 | `.text` 节可写性/映像基址 | PE32 / base `0x400000` | 拒绝 |
| G0.6 | 开关键 `EnableGapProtection` | 显式 `1` 才安装 | 默认 **0=不装**（零行为变化） |

**Q1 真机首字节（安装前）**：断点/读 `0x568273` 首字节 → `89`=未打 / `90`=已有外部补丁（此时**停手并上报**，禁止覆盖未知安装者）。

---

## 3. 开关 · 遥测 · 回滚

### 3.1 开关（ini，与现有门控风格一致）

| 键 | 默认 | 语义 |
|---|---|---|
| `EnableGapProtection` | **`0`** | `1` 时安装 P-2.1；`0` 时不碰 `.text` |
| （预留）`EnableGapProtectP22` / `P23` | `0` | **本卡不实现**；键名勿提前占用 |

**联机**：`MpActive` 为真时 **强制不安装**（与 `EnableMinimapFog` 同级门控）；启动日志打印 `GapProtection=on|off|forced-off-mp`。

### 3.2 遥测（只读计数，禁止热路径膨胀）

| 计数器 | 含义 |
|---|---|
| `gapProtectInstalled` | 0/1 |
| `gapProtectSkipClearCount` | 跳过清零次数（若做软计数；否则可省） |
| `gapProtectRevealArea2Calls` | 可选，仅诊断档 |

### 3.3 回滚

1. **软**：`EnableGapProtection=0` + 重启游戏/重载 DLL（安装态在 init 决定，参考 `LoadConfig` 仅 init 读一次的教训）。  
2. **硬**：备份 6B 原字节 `s_origP21[6] = 89 99 34 01 00 00` → `memcpy` 还原。  
3. **卸载工具**：若走补丁器，提供 `--uninstall-p21` 仅还原该 6B。

---

## 4. 真机验收用例（Z- 系列，最小 4 条）

| ID | 步骤 | 期望 |
|---|---|---|
| **A1** | 默认配置启动 | 三处字节仍为原版；无崩溃；`GapProtection=off` |
| **A2** | `EnableGapProtection=1` 启动 | `0x568273`= `90×6`；`0x568271/0x568279` 未变；日志 `GapProtection=on` |
> 【W3 勘误 · W3-A6/ISSUE-DEFAULT-GAPPROTECTION】改前：EnableGapProtection=1；改后：EnableGapProtection=0  ; [代码/出厂默认0，安全侧；测试或启用时显式置1]；依据：ra2render/blitter_hooks.cpp:606; ra2render/ra2render.ini:199; config_key_matrix.md:109；分级：P0
| **A3** | 造敌方 GapGenerator，覆盖己方建筑；再放 PsychicReveal（或任一 `RevealArea2` 开图） | **裂缝遮挡仍在**（扫描退去后该格可回到黑雾/缝层）；对比未打补丁的「永久透亮」 |
| **A4** | A3 后存 `.SAV` → 读档 | 缝态保持；`except.txt` 空 |
| **A5**（可选） | 同局再 `DestroyGap`/摧毁缝建筑 | 计数能回到 0，无残留永久缝 |

**禁止把「没崩」当成功**：A3 必须有「缝仍在」的截图/像素或逻辑计数证据。

---

## 5. 风险（执行方必读）

| ID | 风险 | 要求 |
|---|---|---|
| R-1 | **混端 DESYNC**（`+0x134` 进 `.SAV`） | 禁止联机混端；全端同构建同开关 |
| R-2 | 存档与原版不互通 | 补丁局存档标记；卸载后不读补丁档 |
| R-3 | 外部安装者 | G0.2/Q1 首字节门禁 |
| R-4 | **flags 邻接** | 只许 `90`；**禁止** `89→8B`、`add/or/and/xor/cmp` 一类 1B 改法 |
| R-5 | ebx 零常量仍被循环使用 | 不得改写 ebx |
| R-6 | 只打 P-2.2/2.3 不打本点 | 本卡是 P0；顺序强制 P-2.1 优先 |

---

## 6. 交付回执（填完交回）

```
ZC-GAP-P21 RESULT
- build/md5(gamemd):
- install path: (ra2render hook | external patcher | ...)
- EnableGapProtection:
- G0.1–G0.6: PASS/FAIL
- Q1 first byte before:
- bytes after @0x568273:
- A1..A5: (each PASS/FAIL + evidence path)
- except.txt: empty|path
- rollback tested: y/n
```

---

## 7. 不在本卡

- P-2.2 `0x577EC5`、P-2.3 `0x577B60`（SpySat/Reshroud）— 另卡  
- MP 握手字段扩展 — 维持既有 MP 门控，不加新握手键  
- `ra2render` 源码重构 / 绘制谓词 H-20-B / 私有雷达窗 H-20-C  
- 台账/看板登记 — 由 Lead 收口

---

*依据：R-GAP-PSY 深潜 §5–§10；原字节 3/3 MATCH；6×NOP 为唯一「不写内存、不改 flags、不碰寄存器」的 6B 替换。*
