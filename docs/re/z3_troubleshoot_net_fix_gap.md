# Z-3 排查手册：M-8 / M-10 落地自检失败与行为异常

> **派工**：RE_COORDINATION.md 派工 v16 · MiMo · 配合 Z-3  
> **读者**：**ZCode**（落地实施方 + 真机自检）。落地包见 `docs/re/landing_pack_net_fix.md`（M-8）与 `docs/re/landing_pack_gap_spysat.md`（M-10）。  
> **用法**：自检失败或真机异常 → 按「症状」表头对号入座 → 逐条走「可能原因 → 排查 → 修复 → 回滚」。  
> **写作用域**：本文。**禁止**改 `ra2render/**`、台账、`gamemd.exe`（盘上只读）。  
> **证据图例**：`[实证]` = 字节/算术已复核；`[待实测]` = 须真机复现后才能标 PASS。

---

## 0. 速查：装完后应当看到的字节

| 点 | 地址 | 装后应为 | 卸后应为 | 来源 |
|---|---|---|---|---|
| H-D1 | `0x64C6F2` | `E9 09 39 4B 01 90`（T0=`0x01B00000`） | `0F 85 69 05 00 00` | M-8 §2/§9 |
| H-D2 | `0x64CC61` | `E9 DA 33 4B 01` | `A0 80 48 B0 00` | M-8 §3/§9 |
| H-D5 | `0x64DE75` | `E9 06 22 4B 01 90 90 90` | `5F 5E 5D 5B 83 C4 14 C3` | M-8 §4/§9 |
| H-D6 | `0x64C911` | `E9 AA 37 4B 01` | `E8 9A A3 E7 FF` | M-8 §5/§9 |
| H-D6b | `0x64CC0A` | `E9 F1 34 4B 01` | `E8 A1 A0 E7 FF` | M-8 §5/§9 |
| gap1 | `0x568273` | `90×6` | `89 99 34 01 00 00` | M-10 §1.2 |
| gap2 | `0x577EC5` | `90×6` | `89 B8 34 01 00 00` | M-10 §1.2 |
| gap3 | `0x577B60` | `90×6` | `89 98 34 01 00 00` | M-10 §1.2 |
| SpySat | `0x508F8F` | `EB 65` | `74 65` | M-10 §2.2 |

> **Lead 三条运行时硬要求**（缺一即停）：① `VirtualAlloc` 失败**放弃该项**（禁止瞎写）；② H-D2 `pushad` **先于** `mov al`；③ 安装后**自检 5 处 `E9`**。

一键复核脚本：

```text
python out/re_work/net_sync_fix/verify_hook_bytes.py      # M-8 原字节 / 还原字节
python out/re_work/landing_net_fix/calc_tramp_bytes.py    # 换基址后重算跳板 hex
python out/re_work/landing_gap/verify_m10_bytes.py        # M-10 原字节（未装时）
```

---

## T1 · VirtualAlloc 基址冲突（`T0=0x01B00000` 分配失败）

| 项 | 内容 |
|---|---|
| **症状** | 安装日志出现 `VirtualAlloc failed` / `cave != 0x01B00000`；或跳板写入后 5 处 `E9` 目标跑飞、首帧即 `except.txt`；`GetProcAddress` 类无关崩溃。 |
| **可能原因** | ① `0x01B00000` 已被 DLL / 堆 / 其他注入器占用（`MEM_FREE` 不足 4K）；② 分配成功但返回了**别的地址**，却仍按 T0 写死 hex（rel32 全错）；③ 旧进程未退出，cave 页仍在。 |
| **排查命令 / 断点** | 1) `!address 0x01B00000`（WinDbg）看占用者；或 `VirtualQuery(0x01B00000,...)` 打印 `AllocationBase/State/Protect`。<br>2) 断点 `VirtualAlloc` 返回后比较 `eax` 与 `0x01B00000`。<br>3) 装后 dump 五段跳板首字节应为 `9C`（`pushfd`），若为 `00`/`CC` 说明没写进 cave。 |
| **修复** | **禁止**在错误基址上写 M-8 附录 A 的 hex。流程：<br>① `cave = VirtualAlloc(NULL, 0x1000, …)` 让系统选址（或试 `0x02B00000` 等空闲段）；<br>② `T0` 常量改为实际返回值，重跑 `python out/re_work/landing_net_fix/calc_tramp_bytes.py`，**整表替换**附录 A 五段 + 5 处 `E9` rel32（附录 C 机械重定位：所有 `imm32` 与 rel32 一律 `+= delta`）；<br>③ 按「0. 速查」新 hex 写入并自检。 |
| **回滚** | 若已按错误 hex 写入：按 M-8 §6「Remove 精确 hex」逐点还原五处 → `verify_hook_bytes.py` → `RESTORED_OK` → `VirtualFree(cave)`；再择基址重装。全程不碰 `.detour` 节。 |

---

## T2 · H-D2 `pushad` 顺序 / `frame[0]` 低字节 ≠ `slot×37`

| 项 | 内容 |
|---|---|
| **症状** | V2.7 不过：`p_HD2_Snapshot` 入口断点处 `frame[0]` 低字节 == `*(0xB04880)` 的装载值（`ExtraSyncInfo`），≠ `slot×37`；快照文件 `SYNC_SNAP_*.bin` 内 `event_raw` 全 0 / HouseIndex/Timestamp 乱；或 `event = frame[0]*3+0x8B4204` 指向非法内存。 |
| **可能原因** | ① 跳板把 `mov al,[0xB04880]` 放在了 `pushad` **之前**（破坏 EAX 低字节，M-8 §3.1 硬性约束）；② 助手用**当前 EAX** 而不是 `frame[0]`；③ `pushfd`/`pushad` 顺序颠倒导致 `frame` 指针偏移；④ 用了规格版 `test [esp+0x20+4]` 误测 EDI（M-8 §1.5 勘误：必须 `F6 44 24 20 40`）。 |
| **排查命令 / 断点** | 1) 反汇编 `0x01B00040` 起 34B，必须逐字节等于 M-8 §3.5：`9C 60 … 61 9D A0 80 48 B0 00 E9 …`——**`A0` 必须在 `61 9D` 之后**。<br>2) 断点 `p_HD2_Snapshot`：`frame == esp`（pushad 后）；`frame[0]` 与 `0x64CC61` 入口处 `eax` 一致。<br>3) 硬件执行断点 `0x64CC61`：记录入口 `eax`（= `slot*37`）再单步进跳板。<br>4) 校验 `event = frame[0]*3 + 0x8B4204` 落在 Queue 环内（`slot = frame[0]/37` 应 < `0x4000`）。 |
| **修复** | ① 跳板按 M-8 §3.5 重写：`pushfd → pushad → [开关/快照] → popad → popfd → mov al,[0xB04880] → jmp 0x64CC66`；② 助手一律 `frame[0]` 取 `slot×37`，**禁止**读当前 `EAX`；③ ZF 探测用 `F6 44 24 20 40`（`test byte [esp+0x20],0x40`）。 |
| **回滚** | `0x64CC61` ← `A0 80 48 B0 00`；键 `SyncSnapshotOnDesync=0`；`p_HD2_Snapshot` 回填 NoopHelper `C3`；`verify_hook_bytes.py` → `RESTORED_OK`。 |

---

## T3 · NOP 等长校验失败（gap 三处 6B、`0x508F8F` 2B）

| 项 | 内容 |
|---|---|
| **症状** | 装后 dump 与「0. 速查」不符：gap 处不是 `90×6`、或长度不是 6；`0x508F8F` 不是 `EB 65`、或写成了 `EB`+别的 rel8；游戏在 `RevealArea2/3` 附近崩溃 / 裂缝行为反常；`Remove` 后回不到原字节。 |
| **可能原因** | ① 只 NOP 了 `mov` 的部分字节（残指令，下一条被拆解）；② `0x508F8F` 写成 `90 65`（NOP+原 rel8）或 `E9` 长跳（破坏等长）；③ 备份数组未在**首次写入前**填好，Remove 写回了 `90×6`；④ 写错 VA（如把 gap3 的 `89 98` 行写到 `0x577EC5`）。 |
| **排查命令 / 断点** | 1) 装前/装后/卸后各 dump 一次三处 + `0x508F88..8F90` 共 9B：<br>`80 B8 A5 16 00 00 00 74 65` → 装后 `80 B8 A5 16 00 00 00 EB 65`。<br>2) `python out/re_work/landing_gap/verify_m10_bytes.py`（未装时 `ORIG` 应 PASS）；装后人工 hex 比对。<br>3) 硬件写断点 `0x568273`/`0x577EC5`/`0x577B60`/`0x508F8F` 看谁写入、写入值。<br>4) 反汇编确认 `0x568273` 等前后仍是完整指令流（无断在半条指令上）。 |
| **修复** | 严格等长：gap **整条 6B** `89 xx 34 01 00 00` → `90×6`；SpySat **只改 jcc 2B** `74 65` → `EB 65`（`cmp` 7B 保留）。备份：`s_origGapProtectBytes[3][6]` / `s_origSpySatGateBytes[2]` 在**写前** memcpy 原字节；`s_gapProtectInstalled` / `s_spySatGateInstalled` 幂等守卫。 |
| **回滚** | `RemoveGapProtectionPatches()` 写回三处原 6B；`RemoveSpySatGatePatch()` 写回 `74 65`；键 `EnableGapProtection=0` / `EnableSpySatGate=0` + 重启（安装门控=0 时不写）。彻底：移除 `ra2render.dll`（gamemd 从未写盘）。 |

---

## T4 · 安装后 5 处 `E9` 自检失败

| 项 | 内容 |
|---|---|
| **症状** | 装后自检打印 `HD1/HD2/HD5/HD6/HD6b` 某处 ≠ `E9 …`；或等于 `E9` 但 rel32 目标不是对应 TRAMP；单机 A/B 帧 CRC 不一致 / 联机立刻 `SYNC*.TXT`。 |
| **可能原因** | ① 漏装某条（Install 与 ini 键不对称：键=1 却没写、或写了键=0 也写）；② rel32 按 T0 算但实际 cave 换了基址（T1 遗留）；③ 5B `E9` 覆盖长度不对：H-D1 必须 6B（`E9 rel32 + 90`）、H-D5 必须 8B（`E9 rel32 + 90×3`）、其余 5B；④ 安装前原字节不匹配（游戏版本/已装其他补丁）仍强行写入；⑤ 只装了 H-D6 没装 H-D6b（或反之），MegaMission 路径缺口。 |
| **排查命令 / 断点** | 1) 装后立刻 dump 五点，逐字节比「0. 速查」；<br>2) `python out/re_work/net_sync_fix/verify_hook_bytes.py`：装前应 `ORIG_OK`，装后人工期望「改动字节」，卸后 `RESTORED_OK`；<br>3) 反汇编每个 TRAMP：末尾回跳目标必须是 `0x64CC61` / `0x64C6F8` / 原 `ret` / `0x64CAA8` / `0x64CC0F`（见 M-8 附录 B）；<br>4) 断点 `0x64C6F2` 单步应进入 `0x01B00000`，而不是 fall-through。 |
| **修复** | 按 M-8 §9 步骤 7–11 **逐条** Install；每条：备份原字节 → `VirtualProtect` → 写入 → 恢复保护 → **立刻自检该点**；5 条全过后再进真机。H-D6/H-D6b **成对装**（共键 `SyncCmdMirror`）。安装顺序建议 H-D1→H-D2→H-D5→H-D6→H-D6b；卸载逆序（M-8 附录 E）。 |
| **回滚** | 任一点自检失败：该点立刻按 M-8 §6 精确 hex 还原（H-D1 `0F 85 69 05 00 00`；H-D2 `A0 80 48 B0 00`；H-D5 `5F 5E 5D 5B 83 C4 14 C3`；H-D6 `E8 9A A3 E7 FF`；H-D6b `E8 A1 A0 E7 FF`）→ 键置 0 → 全部还原后 `verify_hook_bytes.py` → `RESTORED_OK`。**禁止**「先跑起来再说」。 |

---

## T5 · SyncDiag 键开了无日志

| 项 | 内容 |
|---|---|
| **症状** | `[SyncDiag] SyncEarlyLog=1`（或 Snapshot/Mirror/CmdMirror=1）但目录里无 `DESYNC_PREDICT` / 无 `SYNC_SNAP_*.bin` / `g_syncEarlyLogCount` 等遥测恒 0；或只有遥测数字涨但无文件。 |
| **可能原因** | ① **键默认全 0**，且安装是「键=1 才装」——改 ini 后**未重启**（进程级装载）；② 装了钩但开关槽 `0x01B00400/404/408/40C` 仍 0（LoadConfig 读错节/键名大小写/两份 ini 不一致）；③ 助手指针 `p_HD1_Log`/`p_HD2_Snapshot`/`p_HD6_Log` 仍是 NoopHelper `0x01B00200`（`C3` 直接 ret）；④ H-D1 只在 **CRC 不相等** 才记（ZF=1 不记）——单机无 desync 时 0 条是**正常**；⑤ H-D2 快照写失败（只读目录/磁盘满）走 `syncSnapshotFail` 且**静默**；⑥ 跳板 `je .restore` 跳过（键槽读到 0）。 |
| **排查命令 / 断点** | 1) 启动日志确认四键读入值；对比 `ra2render/ra2render.ini` 与 `ra2youli/ra2render.ini`。<br>2) 调试器读 `0x01B00400/404/408/40C` 与 `0x01B00410/414/418/41C/420`。<br>3) 读 `0x01B00500/504/50C`：应为真实助手地址，不是 `0x01B00200`。<br>4) 断点 `0x01B0000B`（HD1 的 ZF 测试）/ `0x01B0004B`（HD2 快照调用）确认是否走到。<br>5) H-D5 无助手：开 `SyncMirror` 后读 `g_MirrorRing`（`0x01B00600`）应非全 0 且 `syncMirrorFrames` 增。 |
| **修复** | ① 改 ini 后**重启游戏**；② LoadConfig 节名必须 `[SyncDiag]`（不是 `[FogOfWar]`——M-8 与 M-10 键名/默认值勿混）；③ 安装时三指针填真实助手（未就绪则保持 Noop，但要打日志「无日志函数」）；④ H-D1 无 DESYNC 时 0 条合法——造一次 CRC 不一致（测试镜像）验 V1.5；⑤ H-D2 失败计数看 `syncSnapshotFail`，不要当「没走到」。 |
| **回滚** | 四键全 0 + 重启；硬卸按 T4 回滚还原五点；遥测槽/镜像环随之废弃。**勿**占 `SYNC%01d.TXT` 文件名（快照必须 `SYNC_SNAP_%u.bin`）。 |

---

## T6 · 裂缝保护不生效 / SpySat 门控误伤单机

### T6a 裂缝保护不生效（扫图后裂缝仍「永远遮不回去」）

| 项 | 内容 |
|---|---|
| **症状** | PsychicReveal / SpySat 开图后，裂缝覆盖格扫描退去**不恢复黑雾**；`GapsCoveringThisCell` 仍被清 0；与原版 bug 相同。 |
| **可能原因** | ① `EnableGapProtection=0`（安装门控未写补丁）或改 ini 未重启；② 三处有漏装/被其他补丁改写（gap1 `0x568273` / gap2 `0x577EC5` / gap3 `0x577B60` 任一仍是 `89 xx 34 01 00 00`）；③ 与「SuperClass 覆写 `Cell+0x134`」方案叠加（互斥，语义打架）；④ 混端联机：一端 NOP 一端原版（条件安全，可见性分叉）。 |
| **排查命令 / 断点** | 1) 进程内读三处 6B 是否为 `90×6`；<br>2) 写断点 `0x568273`/`0x577EC5`/`0x577B60`：装 NOP 后**不应再有** `mov [reg+0x134],0` 落下；<br>3) 内存看 `Cell+0x134` 在开图扫描后是否保持非 0；<br>4) 确认无第二套 `Cell+0x134` 写者（grep 落地包互斥条款）。 |
| **修复** | 键置 `EnableGapProtection=1` + 重启；补齐三处 6B NOP；禁止叠加 Super 覆写方案；联机全端同 DLL + 同键。 |
> 【W3 勘误 · W3-A6/ISSUE-DEFAULT-GAPPROTECTION】改前：EnableGapProtection=1；改后：EnableGapProtection=0  ; [代码/出厂默认0，安全侧；测试或启用时显式置1]；依据：ra2render/blitter_hooks.cpp:606; ra2render/ra2render.ini:199; config_key_matrix.md:109；分级：P0
| **回滚** | 键 `=0` + 重启（不写补丁）；进程内 `RemoveGapProtectionPatches()` 写回三原 6B。反证：关键 =0 后 bug 应复现（M-10 步骤 9）。 |

### T6b SpySat 门控误伤单机（该开的图也不开了 / 单机行为异常）

| 项 | 内容 |
|---|---|
| **症状** | 单机剧情/遭遇需要 SpySat 全图开时**开不了**；小地图不整图亮；`House+0x577A SpySatActive` 不置 1；或门控开着导致依赖 SpySat 的任务无法完成。 |
| **可能原因** | ① **预期行为**：P-2 `EnableSpySatGate=1` 就是**阻止** `RevealArea3` 全图开（`0x508F8F` `74 65`→`EB 65` 恒走「非 SpySat」分支）——单机若需要原版全图开，这是**门控设计**而非 bug；② 与 S1（`EnableSpySatRadarSweep=1`）叠加后 TYPE 被改成 PsychicReveal 雷达，双重「不全图开」；③ `0x508F8F` 写坏（非 `EB 65`），控制流异常；④ G-07 未还原：同进程关 S1 后 TYPE 残留。 |
| **排查命令 / 断点** | 1) 读 `0x508F88..8F90` 9B：期望 `80 B8 A5 16 00 00 00 EB 65`；<br>2) 断点 `0x508F8F`：装门控后应**无条件**跳 `0x00508FF6`，`RevealArea3(0x577D90)` 不被调用；<br>3) 读 `BuildingType+0x16A5`（SpySat）与 `+0x16F0`、`SuperWeaponType+0xB0/+0xF8` 是否被 S1 改写；<br>4) 组合矩阵见 M-10 §2.4：要「干净最小侵入」用 P-1=1 + P-2=1 + S1=0。 |
| **修复** | **业务要原版全图开**：`EnableSpySatGate=0` + 重启（不写 `EB`）；若还需 S1 雷达改造则 S1=1 + P-3 G-07 还原必须接线。<br>**业务要门控**：保持 P-2=1，验收按 A2.4「不触发全图开」判 PASS，**不要**当缺陷回滚。<br>联机：全端同键；单机任务若硬依赖 SpySat，该局临时 `EnableSpySatGate=0`。 |
| **回滚** | `RemoveSpySatGatePatch()` 写回 `74 65`；S1 走 `RestoreSpySatBuildingTypes()` 写回 TYPE 四字段首次备份（`+0x16A5` 真 / `+0x16F0` -1 / `+0xB0` 实读原值 / `+0xF8` 实读原值）。彻底：移除 DLL + 重启（TYPE 由 rules 重解析）。 |

---

## 7. 跨包易混点（M-8 vs M-10）

| 项 | M-8（net 诊断） | M-10（gap/spysat） |
|---|---|---|
| 默认值 | **全 0**（诊断，装了不改行为） | **1**（bugfix，装了就改行为） |
| 补丁形态 | 5 处 `E9` + 跳板（需 VirtualAlloc） | 等长 NOP/`je→jmp`，**无跳板** |
| 开关键 | `[SyncDiag] Sync*` | `[FogOfWar] EnableGapProtection` / `EnableSpySatGate` / `EnableSpySatRadarSweep` |
| 同步契约 | 只读探针，L0/L1（不写游戏字段） | **条件**：Cell/House 演化被改，须全端同 DLL+ini |
| 回滚验证 | `verify_hook_bytes.py` → `RESTORED_OK` | 三处 6B + `74 65` 复原；TYPE 四字段 G-07 |
| 禁写 | `.detour`、`0xB04474`、`SYNC%01d.TXT`、阈值 `0xA8E30C` | `.detour`、Super 覆写叠加、盘上 `gamemd.exe` |

---

## 8. 仍无法定位时

1. 留存：装后五点 + gap 三处 + `0x508F88` 的 hex dump；`ra2youli/except.txt` 快照；`ra2render.log` 末 50 行；ini 全量。  
2. 对照 M-8 §8 验收清单 / M-10 §1.5、§2.6、§3.5 逐条勾。  
3. 按 RE_COORDINATION §6 上报格式回 Lead（含地址/字节/断点值），**不要**自行改字节「试一下」。  
4. 崩溃且 EIP 落 `0x54500000-0x545F0000`（ra2render 注入区）→ 转轨道 A，不属本手册 M-8/M-10 范围。
