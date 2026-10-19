# ZCode 落地卡 · net_sync 诊断钩（H-D1 / H-D2）+ 对拍规格（H-D5 / H-D6）

> **卡号**：`ZC-HD-DIAG` · **任务 ID**：`R-HD-CARD` · **优先级**：P0（落地序 W1 诊断钩）  
> **执行方**：ZCode（真机/补丁安装唯一写者）· **起草**：MiMo（R-HD 静态定谳）  
> **上游**：`docs/re/net_sync_fix_spec.md`（规格）· `docs/re/landing_pack_net_fix.md`（字节级执行包，M-8）· `docs/re/net_sync_desync_map.md`（演进/desync 裁决）· `out/re_work/re_sprint/R_net_sync/`（claims / hook_landing_order）  
> **格式对齐**：`docs/re/landing_pack_h20c_sweep.md`  
> **本卡范围**：**W1 = H-D1 + H-D2 诊断钩（默认关）**；**W2 规格登记 = H-D5 / H-D6(/H-D6b) 对拍**（含 `0F B6 C0` 取模硬约束）。**不改演进、零补丁语义变更**。  
> **证据基线**：`ra2youli/gamemd.exe` 1.001 · ImageBase `0x00400000` · `file_off = VA − 0x00400000` · 全部原字节已机读复核（`landing_pack_net_fix.md` 附录 D）  
> 【W3 勘误 E-W3-01】原句 `FileOffset = VA − 0x400000` 仅在 `.text/.rdata/.data` 成立；
> 通用式为 `FileOffset = 段.PointerToRawData + (VA − 段.VirtualAddress)`，
> 本镜像 `.rsrc`/`.detour` 为 `VA − 0x6FC000`。依据：out/re_work/_lead_baseline/W3/LEAD_ERRATUM_E-W3-01_fileoffset_rule.md；分级：[实证]
> **写作用域**：本文件 + `out/re_work/re_sprint/R_hd_card/**`。**禁写** `ra2render/**`、`gamemd.exe`、`ra2youli/**`、`tools/**`、台账/看板/ATLAS、`out/reverse/**`。

---

## 0. 一句话

给同步演进装「行车记录仪」：H-D1 在 desync 判据旁路**早记** `DESYNC_PREDICT`，H-D2 在 DESYNC 处理器入口**快照** `SYNC_SNAP_%u.bin`；两开关 **`SyncEarlyLog` / `SyncSnapshotOnDesync` 默认 0**。H-D5/H-D6 仅作对拍规格（W2），镜像取模 **必须 `movzx eax,al`（`0F B6 C0`）**。**禁改演进**；自证门 = **A 开 / B 关 ≥300 帧零 OOS**。MP 策略：**诊断默认关**。

---

## 1. 落地序与本卡边界

| 波 | 内容 | 本卡 |
|---|---|---|
| **W1** | H-D1（`0x64C6F2`）+ H-D2（`0x64CC61`）诊断钩 | **本卡落地**（照表写入） |
| W2 | H-D5（`0x64DE75`）+ H-D6（`0x64C911`）+ H-D6b（`0x64CC0A`）对拍 | **本卡只登记规格/红线**（可同包装，但验收以 W1 为准） |
| W3 | 混端门禁 / S2/S3/TYPE `MpActive` 旁路 | **不在本卡**（归 MP 轨） |
| 不做 | H-D10 静默早停（L2） | 本批明确不做 |
| **禁止** | H-D11 改 CRC / H-D12 改命令序（L3） | **红线** |

**立场**：**诊断钩优先，不改演进**。任何写 `Cell+0x134`、改 CRC 混合、插 RNG、改 `Timestamp` 的「诊断」一律 L3 禁止。

---

## 2. 开关矩阵（默认全 0）

| 键（`[SyncDiag]`） | 槽位 | 随动 Hook | **默认** | 开 = 写什么 | 改演进？ | 卸载对称 |
|---|---|---|---|---|---|---|
| **`SyncEarlyLog`** | `0x01B00400` | **H-D1** | **0** | `DESYNC_PREDICT` 日志行 | **否** | 还原 6B |
| **`SyncSnapshotOnDesync`** | `0x01B00404` | **H-D2** | **0** | `SYNC_SNAP_%u.bin` | **否** | 还原 5B |
| `SyncMirror` | `0x01B00408` | H-D5 | **0** | 独立 `g_MirrorRing`（**不碰** `0xB04474`） | **否** | 还原尾声 8B |
| `SyncCmdMirror` | `0x01B0040C` | H-D6/H-D6b | **0** | 命令镜像日志 | **否** | 还原 call 5B ×2 |
| （不做）`SyncSilentDesync` | — | H-D10 | 0 | — | **是（L2）** | **本批禁** |
| （禁）— | — | H-D11/H-D12 | — | — | **是（L3）** | **禁** |

**硬规则**：
1. **默认全 0** = 零行为变化；软关（键=0 跳板直通）与硬关（Remove 还原字节）都要提供。
2. Install/Remove **必须对称**；开关关不干净 = 缺陷。
3. 安装时先把 `p_HD*` 三槽填 NoopHelper（`0x01B00200` = `C3`），再按需替换——开关误开也不因空指针崩溃。

---

## 3. W1 执行表（照表写入，不做静态推理）

> 全量机器码、rel32、cave 布局以 `docs/re/landing_pack_net_fix.md` 为准（T0 = `0x01B00000`）。本节只钉**本卡裁决点**。  
> **cave 分配失败（`VirtualAlloc` ≠ `0x01B00000`）→ 该项不安装**（跳过 + 红字日志 + 遥测计数）；**禁止**写 `.detour` 节、**禁止**换基址写死未重算 rel32 的 hex。

### 3.1 H-D1 — desync 预测旁路日志（L0，早记，非早退）

| 项 | 值 |
|---|---|
| **VA** | **`0x64C6F2`**（`jne 0x64CC61`，6B `0F 85 69 05 00 00`） |
| 改动 | `E9 09 39 4B 01 90`（T0=0x01B00000） |
| 开关 | **`[SyncDiag] SyncEarlyLog`，默认 `0`** |
| 语义 | `cmp edx,esi`（`0x64C6F0`）后、原 `jne` 前：ZF=0 且开关开 → 打 `DESYNC_PREDICT frame/idx/local/remote/house/ts/delay` → **落入原 `jne`** |
| 控制流 | **无早退**。`jne` 目标恒 `0x64CC61`，相等路径恒 `0x64C6F8` |
| 寄存器 | `pushfd/pushad` 包裹；`edx/esi/eflags` 与原路径一致（**ZF 探测用 `test byte [esp+0x20],0x40`**，不是 `esp+0x24`） |
| 风险 | **L0**：唯一触碰 = 指令槽 6B；跳板内**禁写游戏内存、禁 `Random()`** |
| **Remove** | `0x64C6F2` ← **`0F 85 69 05 00 00`**；键置 0；跳板废弃 |

### 3.2 H-D2 — desync 现场快照（L1）

| 项 | 值 |
|---|---|
| **VA** | **`0x64CC61`**（DESYNC 处理器入口，5B `A0 80 48 B0 00`） |
| 改动 | `E9 DA 33 4B 01`（T0=0x01B00000） |
| 开关 | **`[SyncDiag] SyncSnapshotOnDesync`，默认 `0`** |
| 语义 | **在读 `ExtraSyncInfo@0xB04880` 之前**写 `SYNC_SNAP_%u.bin`（`%u=CurrentFrame@0xA8ED84`），再执行原 `mov al`，`jmp 0x64CC66` |
| ★ EAX 硬约束 | 原首条 `mov al` 会毁 EAX 低字节。跳板**必须** `pushfd→pushad` 先于一切；助手从 `frame[0]` 取 `slot×37`，**不得**假设当前 EAX 完好。验收 **V2.7 必测** |
| 快照内容 | `"SNAP"`+ver、`CurrentFrame`、`CurrentFrameCRC`、`LatestFramesCRC[256]`、Random 状态指针（**只存指针、不抽**）、Queue 计数/游标、event 原文 111B、local/remote CRC |
| 失败安全 | 写失败只 `syncSnapshotFail++` 并**静默跳过**，绝不改控制流；禁 SEH 泄漏 |
| 风险 | **L1**：只加文件写。**禁**占 `SYNC%01d.TXT` / `SYNC%01d_%03d.TXT`（会与原版报告互踩）；禁跳过 `0x64DEA0`/`0x6516F0` 原报告 |
| **Remove** | `0x64CC61` ← **`A0 80 48 B0 00`**；键置 0；跳板废弃 |

### 3.3 安装前置（全部 PASS 才允许写）

| # | 检查 | 期望 | 失败则 |
|---|---|---|---|
| G0.1 | 目标文件 SHA-256 / ImageBase | 1.001 · base `0x400000` | **拒绝安装** |
| G0.2 | `0x64C6F2` 首 6B | `0F 85 69 05 00 00` | 若已是 `E9`：报「已打」停手上报；其它：**拒绝** |
| G0.3 | `0x64CC61` 首 5B | `A0 80 48 B0 00` | 同上 |
| G0.4 | cave | `VirtualAlloc(0x01B00000,0x1000,RWX)` 返回 `0x01B00000` | **该项不安装**（禁带病写入） |
| G0.5 | 四键默认 | 全 **0** | 默认 0 = 不装（零行为变化） |
| G0.6 | `HOOK_POINT_MATRIX.md` | 无冲突；四条均为**只读探针** | 拒绝 |
| G0.7 | 未装字节门 | `verify_hook_bytes.py` 全 `ORIG_OK` | 拒绝 |

---

## 4. W2 对拍规格（H-D5 / H-D6）— 只登记红线与验收

### 4.1 H-D5 逐帧 CRC 镜像 — 取模必须 `0F B6 C0`

| 项 | 值 |
|---|---|
| **VA** | **`0x64DE75`**（`0x64DAB0` 尾声 8B `5F 5E 5D 5B 83 C4 14 C3`） |
| 改动 | `E9 06 22 4B 01 90 90 90` |
| 开关 | **`SyncMirror`，默认 `0`** |
| 镜像目标 | `g_MirrorRing[256] @ 0x01B00600` — **独立内存，绝不写 `0xB04474`** |

**★ 取模硬约束（勘误修复，违反即缺陷）**：

| 指令 | 编码 | 裁决 |
|---|---|---|
| **`movzx eax, al`** | **`0F B6 C0`** | **必须**。等长 3B，清零高位，语义 = `CurrentFrame & 0xFF` |
| `and eax, 0xFFFFFFFF` | `83 E0 FF` | **禁止**。等价 no-op（掩码全 1），高位残留 → `g_MirrorRing` 越界写 / 索引污染 |

TRAMP_HD5 连写 hex（48B，已含修复）：

```
9C 60 83 3D 08 04 B0 01 00 74 1B A1 84 ED A8 00 0F B6 C0 8B 15 FC 51 AC 00 89 14 85 00 06 B0 01 FF 05 1C 04 B0 01 61 9D 5F 5E 5D 5B 83 C4 14 C3
```

装后 dump 必须含 `0F B6 C0`；出现 `83 E0 FF` = **整包拒绝验收**。

### 4.2 H-D6 / H-D6b 命令流镜像

| 项 | H-D6 主站点 | H-D6b 次站点（建议成对） |
|---|---|---|
| **VA** | **`0x64C911`** `call 0x4C6CB0` | **`0x64CC0A`** `call 0x4C6CB0` |
| 原字节 | `E8 9A A3 E7 FF` | `E8 A1 A0 E7 FF` |
| 改动 | `E9 AA 37 4B 01` | `E9 F1 34 4B 01` |
| event 缓冲 | `0x8B4204` 主环（`ecx`=event*） | `0xA83EDC` MegaMission 二级缓冲 |
| 开关 | **`SyncCmdMirror`，默认 `0`** | 同左 |
| 语义 | 只读 event 记 `(frame,kind,house,ts,extra)`，**`call 0x4C6CB0` 次数/`ecx`/后继不变** | 同左 |

**H-D6 对拍规格（验收核心）**：

1. **镜像只读**：禁改写 `Kind/Timestamp/Checksum`；禁「本地先执行、远端后补」。
2. **命令序不变**：开/关 `SyncCmdMirror` 同输入回放，战局结果一致；镜像日志 `(frame,kind,house,ts)` 按帧单调。
3. **双端对拍 MATCH（V4.4）**：A、B 同开镜像 → `g_MirrorRing` 逐帧 CRC + 命令镜像序列**逐帧一致** = `MATCH`。
4. **缺口知情**：不装 H-D6b 时命令镜像缺 MegaMission 痕迹——对拍脚本须知晓，或强制成对安装。
5. **L0 强判据（V4.5）**：A 开 / B 关 ≥300 帧无 `SYNC*.TXT`。

---

## 5. 禁改演进（红线 checklist，违反 = L3 / 本卡失败）

- [ ] **不改** `0x64DAB0` 混合式、÷10 量化、`0x650A90` 调用次数、`0x64C6E2` 比较宽度（H-D11 禁）
- [ ] **不改** `Random` 流与消费次数；跳板/助手/镜像/日志/快照内 **零 RNG**
- [ ] **不改** 命令执行序、`Timestamp` 语义；不「本地立即生效」（H-D12 禁）
- [ ] **不写** 任何可序列化游戏字段；**不写** `0xB04474`（镜像必须独立 `g_MirrorRing`）
- [ ] **不占** `SYNC%01d.TXT` / `SYNC%01d_%03d.TXT`（快照只用 `SYNC_SNAP_%u.bin`）
- [ ] **不把** 跳板写入 gamemd `.detour` 节
- [ ] 阈值 `0xA8E30C` **不改**
- [ ] H-D5 取模 **只许** `0F B6 C0`，**禁** `83 E0 FF`
- [ ] Install/Remove **对称**；`verify_hook_bytes.py` Remove 后全 `RESTORED_OK`
- [ ] 落地前过 `docs/re/HOOK_POINT_MATRIX.md` 冲突核对
- [ ] 本卡写作用域仅本文 + `out/re_work/re_sprint/R_hd_card/**`

---

## 6. 自证门（自证「零语义」可执行证明）

> 任一钩装上后必须成立；**未过自证门不得宣称安全**。

| # | 门 | 通过判据 | 对应 |
|---|---|---|---|
| **S-G1** | **A 开 / B 关 ≥300 帧零 OOS** | 联机：端 A 开诊断钩、端 B 不装/关钩，≥300 帧：**零 `SYNC*.TXT`、零 `TXT_OUT_OF_SYNC` 弹窗** | **V1.4 / V2.2 / V3.6 / V4.5（L0 强判据）** |
| S-G2 | 帧 CRC 序列一致 | 同种子 ≥500 帧：开/关 **逐帧 `CurrentFrameCRC@0xAC51FC` 完全一致** | V1.2 / V3.2 |
| S-G3 | RNG 次数不变 | `0x64DAB0` 与内部 `0x650A90` 调用次数不变（每帧恰 1 次） | V1.3 / V3.7 |
| S-G4 | 字节 A/B | Install 后 dump = 改动字节；Remove 后逐字节还原 | V1.1 / V2.1 / V3.1 / V4.1 |
| S-G5 | 快照只增不改 | 先出 `SYNC_SNAP_*.bin`，随后**仍**生成原版 `SYNC*.TXT` 与 UI 弹窗；目录无原名被占 | V2.3 / V2.4 |
| S-G6 | EAX 快照时序 | 助手入口断点：`frame[0]` 低字节 = `slot×37` 低字节（先于 `mov al`） | **V2.7 必测** |
| S-G7 | 对拍 MATCH | A/B 同开镜像：CRC 环 + 命令镜像逐帧一致 | V3.5 / V4.4 |
| S-G8 | 遥测自洽 | 非零当且仅当键=1 且事件发生；失败路径 `syncSnapshotFail` 可增、控制流不变 | §8 验收 7 |

**一句话**：H-D1/H-D2 = **给演进装行车记录仪**，不是改演进。S-G1（A 开 B 关 300 帧零 OOS）是「零语义」的可执行证明。

---

## 7. MP 策略（诊断默认关）

| 场景 | `SyncEarlyLog` | `SyncSnapshotOnDesync` | `SyncMirror` / `SyncCmdMirror` | 说明 |
|---|---|---|---|---|
| **发行 / 正式联机** | **0** | **0** | **0 / 0** | **默认零副作用**；诊断不进 MP 默认路径 |
| 诊断联机（怀疑 desync） | 1 | 1 | 按需 | **双端同开**；对拍 `DESYNC_PREDICT` 条数应一致 |
| 单机回归 | 0（或 1 做噪声统计） | 0 | 0 | `0x647260` 在 `0xA8D5F8` bit2/4 早退，本就无对端 CRC；开 1 只为噪声统计 |
| 排障复现 | 1 | 1 | 1 / 1 | 快照 bin + 原版 `SYNC*.TXT` 并存 |

**MP 裁决**：
1. **诊断钩默认关 = MP 默认策略**。发行镜像四键全 0；任何联机包不得预置 `=1`。
2. 诊断钩本身 **L0/L1、不改演进**，开钩不构成 desync 源；但**仍默认关**以保持零文件写/零日志噪声。
3. 混端（对端原版无 DLL）：诊断钩只读旁路，**不引入**分叉改集；真正的混端必分叉源是 gap NOP / S1/S2/S3 / L2 节流等——**不在本卡**，归 MP 轨（W3）。
4. 若产品需要正式联机排障：走「诊断联机」档（双端同开），排完即回 0；**禁止**把诊断开关键入默认发行配置。

---

## 8. 真机验收用例（A1–A8）

| ID | 步骤 | 期望 | 档 |
|---|---|---|---|
| **A1** | 未装字节门 | `verify_hook_bytes.py` 全 `ORIG_OK` | [实证] |
| **A2** | 装 H-D1/H-D2 后 dump | `0x64C6F2`=`E9 09 39 4B 01 90`；`0x64CC61`=`E9 DA 33 4B 01` | [待实测] |
| **A3** | 单机同种子开/关各一次 | 逐帧 `CurrentFrameCRC` 序列一致；存档哈希一致 | [待实测] |
| **A4** | **S-G1 自证门** | **A 开 B 关 ≥300 帧：零 `SYNC*.TXT`、零弹窗** | [待实测] |
| **A5** | 人为造一次 CRC 不一致（测试镜像） | 打出 1 条 `DESYNC_PREDICT`；H-D2 落 `SYNC_SNAP_<frame>.bin`；**仍进原 DESYNC 流程与原版 SYNC*.TXT** | [待实测] |
| **A6** | H-D5 dump（若装） | 尾声含 **`0F B6 C0`**；**不得**出现 `83 E0 FF` | [待实测] |
| **A7** | Remove | 5 处补丁点逐字节还原；`verify_hook_bytes.py` → 全 `RESTORED_OK` | [待实测] |
| **A8** | 遥测 | `syncEarlyLogCount`/`syncSnapshotsWritten` 非零当且仅当键=1 且事件发生；`syncSnapshotFail` 失败路径 +1 且控制流不变 | [待实测] |

**禁止把「没崩」当成功**：A4 必须有帧数与零 OOS 证据；A6 出现 `83 E0 FF` = 拒绝验收；A5 快照替代了原版报告 = 失败。

---

## 9. 风险（执行方必读）

| ID | 风险 | 要求 |
|---|---|---|
| R-1 | H-D2 EAX 被 `mov al` 毁掉 | `pushad` 先于一切；助手读 `frame[0]`；**V2.7 必测** |
| R-2 | 快照占 `SYNC%01d.TXT` 原名 | 只用 `SYNC_SNAP_%u.bin` |
| R-3 | H-D5 取模写成 `83 E0 FF`（no-op） | **强制 `0F B6 C0`**；dump 断言 |
| R-4 | 镜像写进 `0xB04474` | 只写 `g_MirrorRing@0x01B00600` |
| R-5 | 跳板进 `.detour` 节 / 换基址未重算 rel32 | cave 失败 = 不装；附录 C 仅离线预备 |
| R-6 | 开关关不干净 / 卸载不对称 | 软关（键=0）+ 硬关（还原字节）双路径 |
| R-7 | 跳板内 RNG / 写游戏内存 | 零 RNG、零游戏内存写 |
| R-8 | 与外部补丁抢字节 | G0.2/G0.3 首字节门禁，未知 `E9` 停手上报 |

---

## 10. 交付回执（填完交回，写入 `out/re_work/re_sprint/R_hd_card/`）

```
ZC-HD-DIAG RESULT
- build/sha256(gamemd):
- install path: (ra2render hook | external patcher | ...)
- cave T0: (0x01B00000 OK | FAIL→not installed)
- SyncEarlyLog / SyncSnapshotOnDesync / SyncMirror / SyncCmdMirror:
- G0.1–G0.7: PASS/FAIL
- bytes after @0x64C6F2 / @0x64CC61:
- HD5 tramp contains 0F B6 C0: y/n (83 E0 FF present: y/n → must be n)
- S-G1 A-open B-closed ≥300f: frames= , SYNC*.TXT=0 y/n, popup=0 y/n
- S-G2 CRC seq match: y/n
- S-G3 RNG count unchanged: y/n
- A1..A8: (each PASS/FAIL + evidence path)
- telemetry early/snapWritten/snapFail/mirror/cmd:
- except.txt: empty|path
- rollback tested (RESTORED_OK): y/n
- MP verdict: DIAG-DEFAULT-OFF | DIAG-ON (both ends) | VIOLATION
```

---

## 11. 不在本卡

- H-D10 `SyncSilentDesync` 静默早停（L2，改客户端交互）— 本批不做  
- H-D11 改 CRC 混合/量化/抽样/比较宽度 — **L3 禁止**  
- H-D12 命令序/`Timestamp`/本地先执行 — **L3 禁止**  
- W3 混端门禁（S2/S3/TYPE `MpActive` 旁路）— 归 MP 轨  
- path cache / AI 时间片 / CRT L2 等改演进落地 — 不在本批  
- `ra2render/**` 源码实现 — 本卡只给钩位/开关/红线，实现另派  
- 台账/看板登记 — 由 Lead 收口  

---

## 12. 复现

```text
阅读 docs/re/landing_pack_net_fix.md（字节级执行包，照表写入）
     docs/re/net_sync_fix_spec.md（规格）
     docs/re/net_sync_desync_map.md（演进/desync 裁决）
对照 out/re_work/re_sprint/R_net_sync/hook_landing_order.txt
     out/re_work/re_sprint/R_hd_card/claims.txt
卸载后：python out/re_work/net_sync_fix/verify_hook_bytes.py → 全 RESTORED_OK
```

---

*依据：R-HD-CARD · 落地序 W1 诊断钩；H-D1 `0x64C6F2` 早记 / H-D2 `0x64CC61` 快照默认 0；H-D5 取模强制 `0F B6 C0`（禁 `83 E0 FF`）；H-D6 对拍规格；禁改演进；自证门 A 开 B 关 ≥300 帧零 OOS；MP 诊断默认关。本卡 = ZCode 照表落地，不做静态推理。*
