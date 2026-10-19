# R-GAP-MERGE · 裂缝保护三点合并核对单（P-2.1 + P-2.2 + P-2.3）

> **文档标识**：`docs/re/landing_pack_gap_merge_checklist.md` · **任务号**：`R-GAP-MERGE`  
> **上游依据**（三份，缺一不可）：  
> ① `docs/re/landing_pack_gap_p21.md`（`ZC-GAP-P21`，P-2.1）  
> ② `docs/re/landing_pack_gap_p223.md`（`ZC-GAP-P223`，P-2.2/P-2.3）  
> ③ `docs/re/gap_protection_install_spec.md`（`R-GAP-INST`，安装路径 A/B + 门控）  
> **交叉契约**：`docs/re/savegame_product_checklist.md` G1/G2/G4（`installed==3` 标记 / MP 门）· `docs/re/mp_autodowngrade_spec.md` 红线  
> **复算/底稿**：`out/re_work/re_sprint/R_gap_merge/**`  
> **范围**：**只出合并核对单**。不写 `ra2render/**` / `gamemd.exe` / `tools/**` / 台账 / 看板。执行方仍为 **ZCode**（真机唯一写者）。  
> **证据基线**：`gamemd.exe` 1.001 · SHA-256 `73201CC021497C9567742F718BF1DC78C22E9AE16C7E7365354B65F3FCF67476` · ImageBase `0x00400000` · `file_off = VA − 0x00400000`
> 【W3 勘误 E-W3-01】原句 `FileOffset = VA − 0x400000` 仅在 `.text/.rdata/.data` 成立；
> 通用式为 `FileOffset = 段.PointerToRawData + (VA − 段.VirtualAddress)`，
> 本镜像 `.rsrc`/`.detour` 为 `VA − 0x6FC000`。依据：out/re_work/_lead_baseline/W3/LEAD_ERRATUM_E-W3-01_fileoffset_rule.md；分级：[实证]

---

## 0. 一句话

把 P-2.1/P-2.2/P-2.3 **三个 6B 等长 NOP 点合并为一个保护包**：同键 `EnableGapProtection` 一次装齐；安装序 P-2.1→P-2.2→P-2.3、回滚逆序；**仅 `gapProtectionPatchesInstalled==3` 写存档标记**；路径 A 单挂点；MP 红线只强不松。

---

## 1. 三点一张表（字节级总表 · 唯一权威合并面）

| 项 | **P-2.1** | **P-2.2** | **P-2.3** |
|---|---|---|---|
| **VA** | `0x00568273` | `0x00577EC5` | `0x00577B60` |
| **文件偏移** | `0x00168273` | `0x00177EC5` | `0x00177B60` |
| **节** | `.text` | `.text` | `.text` |
| **函数** | `MapClass::RevealArea2` @ `0x005678E0` | `MapClass::RevealArea3` @ `0x00577D90` | `MapClass::Reshroud` @ `0x00577AB0` |
| **原字节（6B）** | `89 99 34 01 00 00` | `89 B8 34 01 00 00` | `89 98 34 01 00 00` |
| **原指令** | `mov [ecx+0x134], ebx` | `mov [eax+0x134], edi` | `mov [eax+0x134], ebx` |
| **零常量寄存器** | `ebx` | `edi` | `ebx` |
| **新字节（6B）** | `90 90 90 90 90 90` | `90 90 90 90 90 90` | `90 90 90 90 90 90` |
| **改动长度** | **6==6 等长**（禁 trampoline / 禁动 `.detour`） | 同左 | 同左 |
| **窗前（自检）** | `0x568271` = `3B C3` | `0x577EBF` = `89 B8 30 01 00 00` | `0x577B56` = `C7 80 30 01 00 00 01 00 00 00` |
| **窗后（自检）** | `0x568279` = `7C 14` | `0x577ECB` = `8B 90 2C 01 00 00` | `0x577B66` = `89 90 40 01 00 00` |
| **语义（NOP 前）** | 任一 `RevealArea2` 开图：`GapsCovering←0`（废缝） | SpySat 全图开 / 旁路 `0x481FC3`：`GapsCovering←0` | SpySat 离线重遮 / 旁路 `0x50BD20`：`GapsCovering←0` |
| **语义（NOP 后）** | 仅删清计数；**保留** `0x56824A ShroudCounter←0`、`0x568297 CopyFlags\|=0x10` | 仅删清计数；**保留** `0x577EBF ShroudCounter←0`、`0x577ED4 CopyFlags\|=0x18` | 仅删清计数；**保留** `0x577B4E CopyFlags&=~0x18`、`0x577B56 ShroudCounter←1`、`0x577B66 RedrawFlags&=~0x3` |
> 【W3 勘误 · W3-A6/ISSUE-VA-0X568297-OFFSET】改前：0x568297；改后：0x0056829A (7B: 83 89 2C 01 00 00 10 | or dword ptr [ecx+0x12c], 0x10)；依据：ra2youli/gamemd.exe:0x168295-0x1682A1; errata_sync_master_table.md:16 (R-E01); ra2render.h:96；分级：P0
| **flags 风险** | **有** `cmp(0x568271)→mov→jl(0x568279)` 三明治 | 无三明治（`je` 在 ShroudCounter 写之前消费） | 无三明治；但 `ebx` 于 `0x577B71 cmp eax,ebx` 仍被消费 |
| **替换约束** | **只许 `90`**；禁 `89→8B`、禁 `add/or/and/xor/cmp` 类 1B 翻法；禁改 `ebx` | 只许 `90`；禁改 `edi` | 只许 `90`；禁改 `ebx` |
| **覆盖面** | PsychicReveal + **22 个** `RevealArea2` caller（P0 最大面） | SpySat 全图开 + `0x481FC3` 旁路 | SpySat 离线重遮 + `0x50BD20` 旁路 |
| **落地优先级** | **P0**（必打） | P1 | P1 |
| **静态证据** | 原字节 MATCH（P21 §1） | MATCH 2/2（`R_gap_p223/claims_p223.txt`） | 同左 |

【勘误 2026-09-30 · R-E01 · errata_sync】原文 VA「0x568297」错误。该指令实际在 VA 0x0056829A（83 89 2C 01 00 00 10 = or dword [ecx+0x12C], 0x10）；0x568297 处字节为 50 DC AB 00，属上一条 mov ecx,0xABDC50 的立即数尾巴。权威：RESULT_GAP_P21.md §5 E-1。原文保留不删字。

**合并语义边界（只许删这三件事）**：三点均为「清 `Cell+0x134 GapsCoveringThisCell`」；**其余写入一律保留**。三点是**一个保护包**，不是三个补丁。

---

## 2. 同键 `EnableGapProtection`（一键 · 不拆键）

| 项 | 裁决 |
|---|---|
| **键名** | `[FogOfWar] EnableGapProtection`（**唯一**） |
| **API 默认 / ini 出厂** | **`0`** = 不碰 `.text`（零行为变化） |
| **`=1` 语义** | 安装**本构建已实现的全部 P-2.x 点**（合并构建 = P-2.1+P-2.2+P-2.3） |
| **独立键 `EnableGapProtectP22/P23`** | **不建、不占用**（P21 §3.1「键名勿提前占用」） |
| **热重载** | **禁止**。`LoadConfig` 仅 init 读一次；改键必须**重启游戏/重载 DLL** |
| **安装态判定** | init 一次决定（A 路径）；B 路径安装时决定 |

**同键四条理由（沿用 P223 §3.1 裁决，合并后仍成立）**：

1. 产品契约已按「一键 + 计数」设计（`savegame_product_checklist.md` G2.1 / G4.1，期望 `installed==3`）；
2. 同一 bug 语义（清 `+0x134`），用户心智 = 「裂缝保护」一个开关；
3. P21 已裁「键名勿占用」，拆键反而违约；
4. 回滚不依赖键粒度（字节级可分点 `memcpy` 还原）。

**分装中间态（允许但不推荐）**：`installed < 3` 时 —— (a) **不写** `GapProt Version` 标记流；(b) 读档按原版档处理；(c) 日志 `GapProtection=on installed=N (PARTIAL)` 告警；(d) **禁联机、禁存补丁档**。

**日志枚举（合并后必打，`installed=N` 追加）**：
`GapProtection=on|off|forced-off-mp|already|external-installer-detected|hash-mismatch|byte-mismatch|context-mismatch|pe-mismatch|virtualprotect-fail`（`on` 追加 `installed=N`）。

---

## 3. 安装顺序 / 回滚顺序

### 3.1 安装顺序（强制）

| 序 | 动作 | 卡 | 理由 |
|---|---|---|---|
| 1 | 门禁 G0.1 哈希 → G0.5 PE/base → 各点窗前/窗后 → 各点首 6B → G0.6 开关 → MP 门 | 三卡共用 | 任一 FAIL = **整包不写** |
| 2 | **P-2.1** `0x568273` 6×NOP | P21 | 封 PsychicReveal + 22 caller（P0 最大面） |
| 3 | **P-2.2** `0x577EC5` 6×NOP | P223 | 封 SpySat 全图开 + `0x481FC3` 旁路 |
| 4 | **P-2.3** `0x577B60` 6×NOP | P223 | 封 SpySat 离线重遮 + `0x50BD20` 旁路 |
| 5 | 遥测 `gapProtectionPatchesInstalled` 回写（期望 **3**） | 合并 | 存档标记 / MP 判据 |
| 6 | 真机 Q1 三点首字节复核 | 两卡共用 | 确认无外部安装者 |

**推荐模式 = 同装**（一次写 3 点）：`installed=3` 一步到位，存档契约简单。分装仅在风险分期时使用，且受 §2 中间态硬约束。

### 3.2 回滚顺序（强制逆序 · 后装先拆）

| 层级 | 操作 | 说明 |
|---|---|---|
| **软** | `EnableGapProtection=0` + **重启** | 新进程不写；A 的 DETACH 会还原本次会话写入 |
| **硬·单点** | 备份 `s_origP21[6]` / `s_origP22[6]` / `s_origP23[6]` → `memcpy` 还原 | **逆序 P-2.3 → P-2.2 → P-2.1** |
| **硬·整组** | `s_origGapProtectBytes[3][6]` 一次 `memcpy` | 三点同时还原 |
| **卸载工具（B）** | `--uninstall-p23` / `--uninstall-p22` / `--uninstall-p21` / `--uninstall-gap-all` | 分点或整组 |
| **灾难** | 重装/校验 `gamemd.exe` 原版哈希 | sidecar 丢失且字节窗被未知方改写 |

**逆序理由**：避免中间态只剩 P-2.3（Reshroud 单点）而 P-2.2 仍 NOP 的语义撕裂；禁止只拆中间点。  
**回滚验收**：还原后各点 6B 逐字节回到原版，且全部上下文窗**仍未改动**。

---

## 4. `installed==3` 存档标记（GapProt Version）

| 项 | 契约 |
|---|---|
| **计数器** | `gapProtectionPatchesInstalled` ∈ 0..3 = 本进程实际写入的 NOP 点数 |
| **写标记条件** | **仅当 `==3`** 才写 OLE 流 `GapProt Version` = u32 LE `1`（G2.1） |
| **写入时机** | `Game::Save` 收尾 / `Save_Core ret` 前（`0x67E3FB/0x67E410/0x67E429` 后或 `ret 0x67E43A` 前） |
| **`<3` 中间态** | **不写**标记流；读档按原版；日志 PARTIAL |
| **禁止** | 改 `Internal Version=0x0002B898`；改 `CONTENTS`；用标记当完整性校验（X1/X2/X5） |
| **可选** | `Forge Build Tag`（16B 诊断指纹，**不拒读**） |

**读档拒读矩阵（G3 · 文案必须一致）**：

| 标记流 | `EnableGapProtection` | 行为 | 产品文案 |
|---|---|---|---|
| 有 | 1 | **正常加载** | 补丁档 + 补丁端 |
| 有 | 0 | **拒绝** | 「本存档由裂缝保护补丁写入，当前未启用 EnableGapProtection」 |
| 无 | 1 | **默认拒绝**（可选加载+重建 `+0x134`，须全端同算法） | 「原版存档与裂缝保护语义不兼容」 |
| 无 | 0 | **正常加载** | 双原版 |

**卸载对称（G6.2）**：装 P-2.x 后存档有标记；卸载还原 6B 后**新档无标记**，旧补丁档按矩阵处理（卸载后不读补丁档）。  
**DESYNC 触发点**：补丁后**第一次** `RevealArea2/3/Reshroud`，**不是**读档瞬间。

---

## 5. 路径 A 行号合并（ra2render 加载期 · 单挂点统一视图）

> 依据 `gap_protection_install_spec.md` §2.1–§2.2。合并后 **挂点行号不变**，函数名由 P21 单点扩为三点整包；P223 不新增挂点。

### 5.1 生命周期（行号 = 合并锚点）

```
DllMain PROCESS_ATTACH                    dllmain.cpp:27
  └─ InstallVTableHooks()                 dllmain.cpp:31 → blitter_hooks.cpp:3177
       ├─ LoadConfig()                    blitter_hooks.cpp:3178 → :496
       │    └─ GetIniIntEx("FogOfWar","EnableGapProtection",0,...)   ★仅 init 读一次
       ├─ PatchVTablePointer ×13          :3181..:3257
       ├─ InstallCellClassDrawHook()      :3260
       ├─ InstallGreatestThreatHook()     :3263
       ├─ InstallRadarFogHooks()          :3266
       └─ ★ InstallGapProtection()        【合并挂点：紧随 :3266 之后、最终 Log 之前】
            ├─ G0.6 + MpActive 门控
            ├─ P-2.1 0x568273：读窗→备份→VirtualProtect→90×6→还原保护
            ├─ P-2.2 0x577EC5：同上
            ├─ P-2.3 0x577B60：同上
            └─ gapProtectionPatchesInstalled += 成功点数

DllMain PROCESS_DETACH                    dllmain.cpp:39
  └─ RemoveVTableHooks()                  dllmain.cpp:44 → blitter_hooks.cpp:3272
       ├─ RemoveCellClassDrawHook / RemoveGreatestThreatHook / RemoveRadarFogHooks  :3273-3275
       ├─ ★ RemoveGapProtection()         【合并：逆序 P-2.3→P-2.2→P-2.1，或整组 memcpy】
       └─ 虚表还原 + 遥测收口              :3277..:3351
```

### 5.2 行号合并对照（P21 单点 → 三点整包）

| 锚点 | 文件:行（安装规格原文） | P21 单点名 | **合并后名** | 合并变化 |
|---|---|---|---|---|
| LoadConfig 读键 | `blitter_hooks.cpp:3178` → `:496` | `EnableGapProtection` | 同 | 不变（仍 init-only） |
| 安装挂点 | `blitter_hooks.cpp:3266` 之后 | `InstallGapProtectionP21()` | **`InstallGapProtection()`** | 循环/顺序写 3 点；`installed` 计 0..3 |
| 卸载挂点 | `blitter_hooks.cpp:3275` 之后 | `RemoveGapProtectionP21()` | **`RemoveGapProtection()`** | 逆序还原 3 点 |
| 备份缓冲 | — | `s_origP21[6]` | **`s_origGapProtectBytes[3][6]`**（或三个 `s_origP2x[6]`） | 整组/分点均可 `memcpy` |
| 遥测 | — | `gapProtectInstalled` 0/1 | **`gapProtectionPatchesInstalled`** 0..3 | 对齐 G2.1/G4.1 |
| 伪代码骨架 | `gap_protection_install_spec.md` §2.2 | 单点 `InstallGapProtectionP21` | 三点同构展开 | **禁止漂移**原 6B 常量 |

**行号合并约束**：挂点**只增不移**（`:3266` 后 / `:3275` 后）；不得改 `LoadConfig` 调用序；不得把安装挪进热路径。若执行时行号与现网源漂移，以「`InstallRadarFogHooks` 之后 / `RemoveRadarFogHooks` 之后」语义锚为准，并在回执记录实际行号。

### 5.3 路径 B（离线回退 · 与 A 互斥）

- 命令面：`gap21 --install|--uninstall-p21|--status` → 合并后扩为 `--uninstall-p23/p22/p21/--uninstall-gap-all`。
- Sidecar `gamemd.exe.gap21.json` 必写（文件级改 exe，整文件哈希必变）；合并侧建议 `step` 数组或三条 sidecar 记录三点。
- **A+B 禁止同时生效**；Q1 见未知 `90×6` **停手上报**。

---

## 6. 验收总表（合并 A / I / S / R 系列 · 禁止「没崩」当成功）

### 6.1 安装与字节

| ID | 步骤 | 期望 | 判据 |
|---|---|---|---|
| **A1** | 默认配置启动（`=0`） | 三点 6B 仍为原版；上下文窗未动；无崩溃；日志 `GapProtection=off` | 字节 dump |
| **A2** | `EnableGapProtection=1` 启动 | 三点 = `90×6`；窗未动；日志 `GapProtection=on installed=3` | 字节 dump + 日志 |
> 【W3 勘误 · W3-A6/ISSUE-DEFAULT-GAPPROTECTION】改前：EnableGapProtection=1；改后：EnableGapProtection=0  ; [代码/出厂默认0，安全侧；测试或启用时显式置1]；依据：ra2render/blitter_hooks.cpp:606; ra2render/ra2render.ini:199; config_key_matrix.md:109；分级：P0
| **A2b** | 同局只装 P-2.1（分装中间态） | `installed=1 (PARTIAL)`；**不写** `GapProt Version`；禁联机 | 日志 + 存档流扫描 |
| **I1** | 启动前外部写 `90×6`，再 `=1` 启动 | `external-installer-detected`，**不覆盖** | 日志红字 |
| **I2** | `=1` 启动后游戏中改 `=0` | **不**立即还原；重启后 `off` 且三点原版 | 字节 + 重启 |
| **I3** | B：`--install` → `--status` → `--uninstall-gap-all` → `--status` | 三点往返为原版；sidecar 一致 | 工具输出 |
| **I4** | B 安装后二次 `--install` | `already` 幂等，不重复写 | 工具输出 |
| **I5** | 联机/`MpActive` 下 A 启动 | `forced-off-mp`；三点保持原版 | 日志 + 字节 |

### 6.2 行为（缝仍在 = 唯一成功判据）

| ID | 步骤 | 期望 | 对应点 |
|---|---|---|---|
| **Z1** | 敌方 Gap 覆盖 + PsychicReveal / 任一 `RevealArea2` | **裂缝遮挡仍在**；对比未打的「永久透亮」 | P-2.1 |
| **Z2** | SpySat 在线全图开（`UpdateSpySat`→`0x509064 call RevealArea3`） | 全图已探索（`CopyFlags\|=0x18`）但 **`GapsCovering` 未清**；缝仍在 | P-2.2 |
| **Z3** | SpySat 离线（`0x509012 call Reshroud`）→ 存 `.SAV` → 读档 | 可回黑雾（`ShroudCounter=1` 且 `GapsCovering>0` 钳位）；缝态保持；`except.txt` 空 | P-2.3 |
| **Z4** | 旁路：`0x481FC3` 调 `RevealArea3`；`0x50BD20` 调 `Reshroud` | 两条旁路后 `GapsCoveringThisCell` **均未清零** | P-2.2/2.3 |
| **Z5** | 摧毁缝建筑 / `DestroyGap` | 计数能回 0，无残留永久缝 | 整包 |

### 6.3 存档标记与回滚

| ID | 步骤 | 期望 |
|---|---|---|
| **S1** | `installed==3` 存 `.SAV` | 档内**有** `GapProt Version=1`；`Internal Version`/`CONTENTS` 未改 |
| **S2** | `installed<3` 或未装存档 | **无** `GapProt Version` |
| **S3** | 四格读档矩阵（原版档×原版端、补丁档×补丁端、原版档×补丁端、补丁档×原版端） | 与 §4 拒读矩阵一致；拒绝走原版读档失败 UI |
| **R1** | 硬回滚逆序 P-2.3→P-2.2→P-2.1 | 三点回原版；窗未动；**回滚顺序已测 = y** |
| **R2** | 软关 `=0` + 重启 | 三点原版（A）；B 需 `--uninstall-gap-all` |

**证据要求**：Z1–Z4 必须有「缝仍在」的截图/像素或逻辑计数（`GapsCoveringThisCell` 抽样读值 > 0）证据。**禁止把「没崩」当成功。**

### 6.4 MP 对拍（本单不代替真机）

| ID | 步骤 | 期望 |
|---|---|---|
| **M1** | 混端对局尝试（一端 NOP、一端原版） | **拒绝开局**（硬拒），不是等 DESYNC |
| **M2** | 全员同构建同 `EnableGapProtection` 双端 ≥5000 帧逐帧 CRC 对拍 | `[待实测]`（G4.4，本单只登记不代替） |
| **M3** | 对局内读档（Kind `0x1D`） | 全体同帧；可选 `GapsCoveringThisCell` 抽样哈希告警 |

---

## 7. MP 红线（只强不松）

| # | 红线 | 依据 | 违反后果 |
|---|---|---|---|
| **MP-1** | **严禁混端联机**（一端打 P-2.x、一端原版） | P21 R-1 / P223 R-1 / G4.2 / ATLAS H-20-A | `+0x134` 进 `.SAV` → 第一次开图分叉 → **必 DESYNC** |
| **MP-2** | `MpActive()==true` ⇒ **强制不安装**；启动日志 `forced-off-mp` | G1.2 / 安装规格 §2.2/§5.4 | — |
| **MP-3** | 全端**同构建 + 同 `EnableGapProtection` + 同 `installed` 计数**（期望皆 3 或皆 0） | P223 R-1 / G4.1 | 计数不一致 = 视同混端 |
| **MP-4** | 已装后中途进入 MP：**不在热路径拆除**（拆写有 flags/线程风险） | 安装规格 §5.4 | 仅日志审计；「MP 边沿还原」留后续卡 |
| **MP-5** | **禁止**在 `RevealArea*` / `Reshroud` 热路径加运行期开关分支（非 `90` 指令） | 安装规格 §8 / P21 R-4 | flags/寄存器邻接破裂 |
| **MP-6** | **禁止**改 `IsShrouded` / `IsCellShrouded` / RNG / 命令序 / `Compute_Frame_CRC` | `mp_autodowngrade_spec.md` 红线 | 降级只做旁路增强 |
| **MP-7** | 门控本身不得触碰网络消息 / 事件环 / `0xA8D5F8` 写入 | `mp_gate_residual_deep_dive.md` | — |
| **MP-8** | A/B 双写者 **禁止**；Q1 未知安装者 **停手** | G1.5 / X7 | 还原契约破裂 |

### 7.1 【冲突待裁决 · Lead】握手字段口径

| 方 | 口径 | 出处 |
|---|---|---|
| **甲（不加键）** | **不采纳**把 `EnableGapProtection`/`EnableSpySatGate` 纳入联机握手校验字段；策略 = 全员强制同值 + 禁混端（文档级） | `gap_protection_install_spec.md` §4.3 / `RE_COORDINATION.md`；P21 §7、P223 §7「不加新握手键」 |
| **乙（要握手）** | 握手键**必须含** `EnableGapProtection` + `gapProtectionPatchesInstalled`（期望 3）；混端**拒绝开局** | `savegame_product_checklist.md` G4.1/G4.2；`ARCHITECTURE_ATLAS.md` §12.4 |

**本单处置**：落地卡侧暂维持甲（不加协议字段）；但产品出厂门禁 G4.1/G4.2 为 **P0**，若 Lead 裁乙，则需补握手字段设计卡后方可宣称「MP 可发布」。**在裁决前，任何一方不得单方面改协议或宣称 G4.1 已满足。** 当前唯一安全混端姿势 = **本端整局不加载 `ra2render.dll`**，或全员同构建同开关（且仍需 Gate3 / M2 对拍）。

---

## 8. 禁止项（执行方红线 · 合并后仍有效）

1. **禁止**非 `90` 替换 / trampoline / 改 flags / 改 `ebx`·`edi` 零常量 / 动 `.detour`。
2. **禁止**只打 P-2.2/2.3 不打 P-2.1（G0.7 警告；顺序强制 P-2.1 优先）。
3. **禁止**占用 `EnableGapProtectP22/P23` 键名；**禁止**热重载 `EnableGapProtection`。
4. **禁止** A+B 双写者；禁止覆盖 Q1 未知安装者。
5. **禁止**改 `Internal Version` / `CONTENTS`；禁止用标记流当完整性校验。
6. **禁止** `installed<3` 时写 `GapProt Version` 或宣称「保护包已就绪」。
7. **禁止**回滚只拆中间点；硬回滚强制逆序。
8. **禁止**在热路径加运行期开关分支；禁止为 MP 新增握手字段（待 §7.1 裁决前）。
9. **禁止**把「没崩」当验收成功；Z 系列必须有缝仍在证据。

---

## 9. 交付回执（ZCode 填写 · 合并整包）

```
R-GAP-MERGE / ZC-GAP-P21+P223 RESULT
- build/md5(gamemd):
- install path: A ra2render | B external | (rejected)   [A/B 互斥]
- EnableGapProtection (ini/API):
- gapProtectionPatchesInstalled: (期望 3)
- G0.1–G0.7: PASS/FAIL
- Q1 first byte before @0x568273 / @0x577EC5 / @0x577B60:
- bytes after @0x568273 / @0x577EC5 / @0x577B60:
- context windows intact: y/n
- MpActive at install:
- GapProtection log line:
- install order used: P-2.1→P-2.2→P-2.3
- rollback order tested (P-2.3→P-2.2→P-2.1): y/n
- same-install / split-install mode: (same|split)
- GapProt Version stream (installed==3 only): written|absent
- A1..A2,I1..I5,Z1..Z5,S1..S3,R1..R2,M1..M3: (each PASS/FAIL + evidence path)
- except.txt: empty|path
- §7.1 handshake conflict status: (open|resolved-by-Lead: ...)
```

---

## 10. 不在本单

- SpySat 门控 `0x508F8F je→jmp`（`EnableSpySatGate`）— 另轨（`landing_pack_gap_spysat.md`）
- S1 TYPE 补丁 / G-07 Remove 还原 — 另轨
- `ra2render` 源码实现 / 绘制谓词 H-20-B / 私有雷达窗 H-20-C
- MP 握手字段扩展实现 — 待 §7.1 Lead 裁决后另卡
- 台账/看板登记 — 由 Lead 收口

---

*合并依据：`landing_pack_gap_p21.md` §1–§5 · `landing_pack_gap_p223.md` §1–§8 · `gap_protection_install_spec.md` §2–§8 · `savegame_product_checklist.md` G1/G2/G3/G4/X1–X8 · `mp_autodowngrade_spec.md` 红线。三点原字节 3/3 MATCH；6×NOP 为唯一「不写内存、不改 flags、不碰寄存器」的 6B 替换。*
