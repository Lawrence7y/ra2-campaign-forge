# 联机裁决收敛 + 六大落地包一致性审计（收尾-C）

> **文档标识**：`docs/re/mp_landing_consistency.md` · 任务 **task-13**（收尾-C）
> **责任方**：re-landing（收尾代理） · 日期 2026-09-26 · **纯静态审计，未启动游戏**
> **基准二进制**：`ra2youli/gamemd.exe`（4,825,360 B，MD5 `4f37486e5b0dbe2ae5f45aeee0f98367`）[实证]
> **被审对象**：
> 1. 裁决收敛：`docs/re/hook_gate_gap_table.md`、`docs/re/MP_SAFETY_REVIEW.md`
> 2. 落地包一致性：`docs/re/pending_execution_master_table.md`（执行总表） vs `landing_pack_net_fix.md` / `landing_pack_gap_spysat.md` / `landing_pack_particle.md` / `landing_pack_crt_audio_particle.md` / `l4_vision_dirty_final_spec.md`
> **只读纪律**：未改 `ra2render/**`、未改顶层台账、未改其他 `docs/re/*.md`；仅对本任务授权的两份文档**追加最小勘误标记**（附录 A）。
> **证据标注**：`[实证]` = 本任务可复算（字节 dump / 反汇编 / PE 解析 / 源码逐行）；`[推演]` = 由实证推导、未执行；`[待实测]` = 需真机验证。

---

## 0. 结论摘要（TL;DR）

1. **裁决已收敛，但被审的两份文档本身没有收敛。**
   `G-01…G-10` 的终局政策已完整落在 **`mp_release_safety_checklist.md` §一 L19-24（R-01…R-04）+ §三 L60-71（MP-G01…MP-G10）** 与 **`ARCHITECTURE_ATLAS.md` §9.4 L1530-1544（G-01…G-09 门控矩阵）**，且与 task-13 给定的 7 条政策**逐条一致**。
   而 `hook_gate_gap_table.md` §5（L174-185）仍以「建议改动」形态呈现 G-01…G-10（无裁定列），`MP_SAFETY_REVIEW.md` 全文 **0 次**出现 `G-01…G-10` 编号、其 §5（L395-404）/§6（L408-414）仍停留「或…」式二选一口径。→ 已按授权追加**最小勘误标记**（附录 A，不改正文）。
2. **政策已定 ≠ 已落地。** `ra2render/**` 现网源码中 `EnableThreatRetention` / `MpStateWrites` / `L4DirtyMode` / `EnableFogBlendStubs` / `MpAutoDowngrade` / `ForceSinglePlayer` / `EnableParticleFog` / `EnableGapProtection` / `EnableSpySatGate` / `EnableAudioThrottling` / `EnableMemoryPool` / `MpActive()` **全部 0 命中**；`blitter_hooks.cpp:103` 仍为 `GetPrivateProfileIntA(..., 1, ...)`（G-01 未落地）、`:1453` 仍只判 `s_minimapForceRefresh`（G-05 未落地）、`:596` 起的 `PatchSpySatBuildingTypes` 仍无备份结构、`RemoveVTableHooks()`（`:1712`）无 TYPE 还原调用（G-07 未落地）[实证]。
> 【W3 勘误 · W3-M6/ISSUE-STALE-L4-EXIST】改前：现网源码中 L4DirtyMode / EnableGapProtection 全部 0 命中；改后：L4DirtyMode 已在 blitter_hooks.cpp:757 读取并支持 force-full / vision-dirty 模式；三处 ini 均已配置出厂值；依据：blitter_hooks.cpp:606,757 与三处 ini 配置；分级：P0
3. **G-07 结论：采纳**（备份 4 字段 + `RemoveVTableHooks` 尾部还原）。它是**工程回滚能力**，本体不进同步契约（TYPE 单例不入 `.SAV`）；但 S1 的**写出**仍属「全端同 DLL + 同 ini」条件面。依据见 §2.3。
4. **G-09 结论：采纳**（`everSeen` 不进档，保持现状 + 文档声明）。`s_everSeenGrid` 是 DLL 私有 `static uint8_t[512*512]`，不入引擎存档管线、不进帧 CRC，判为**体验遗留而非 desync**。依据见 §2.3。
5. **落地包审计：18 个补丁项 × 5 字段 = 90 格 → 一致 71 / 冲突 12 / 缺失 1 / 不适用 6**（统计口径见 §3.1、机器产出 `out/re_work/mp_landing/matrix_5fields.md`）。
   三条已知修正：**① H-D5 `0F B6 C0` 已落表 ✓**、**② 音频 `ret 8` / `ret 4` / 早退 `eax=0` 已落表 ✓**、**③ 跳板三款只落了「禁写 `.detour`」与「P-1 统一基址 `0x01B00000`」，「`VirtualAlloc` 失败即放弃该项」在两份执行文档中均**未**落地（口径反而写成「失败走动态重定位」）** ✗**。
6. **12 格冲突集中在 3 个文档**：`landing_pack_crt_audio_particle.md`（P-3/P-4/P-5 的默认值、PlayAt 足迹、无字节级新字节）、`landing_pack_particle.md`（虚表 DWORD 字节序标注）。执行总表 `pending_execution_master_table.md` 侧另有 4 项**跨链缺口**（未纳入 MP 裁决键、`MpActive()` 地址误引、cave 布局缺遥测槽位、回滚表缺 G-07 行）。全部 13 条见 §4。

---

## 1. 方法与可复算证据

### 1.1 脚本与产物（全部位于 `out/re_work/mp_landing/**`）

| 脚本 | 作用 | 产物 |
|---|---|---|
| `claims_orig_bytes.txt` | 32 条「地址 = 期望字节」断言（6 包全部原字节 + G-03/G-04 裁决依据字节 + 原生音频分支 + 上下文） | `audit_orig_bytes.json` |
| `verify_rel32.py` | capstone 反汇编复核原指令与分支目标；独立重算 6 处 `E9 rel32` 落点 | `rel32_verify.json` |
| `verify_env.py` | PE 节表 / MD5 / VA→文件偏移规则 / 两份 ini 一致性 / cave 页与节区无重叠 | `env_facts.json` |
| `compare_landing_packs.py` | 18 项 × 5 字段 × 2 文档的机械比对（正则 + 行号定位） | `matrix_raw.json` |
| `emit_matrix_md.py` | 把 `matrix_raw.json` 渲染为可读矩阵 | `matrix_5fields.md` |
| `check_known_fixes.py` | 三条已知修正的落地核查 + 编码学复核 | `known_fixes.json` |

复算命令（工作树根目录）：

```powershell
python tools/audit_bytes.py out/re_work/mp_landing/claims_orig_bytes.txt --json out/re_work/mp_landing/audit_orig_bytes.json
python out/re_work/mp_landing/verify_rel32.py
python out/re_work/mp_landing/verify_env.py
python out/re_work/mp_landing/compare_landing_packs.py
python out/re_work/mp_landing/emit_matrix_md.py
python out/re_work/mp_landing/check_known_fixes.py
```

### 1.2 字节层结果（`[实证]`）

- **32 条断言：文档断言 31/31 全 `OK`**；第 32 条（`0x0087F7F4`）是我方附加的 BSS 存在性探测，落在 `.data` 虚拟段无文件数据 → 预期 `NOREAD`，不影响任何文档断言。
- **6 处 `E9 rel32` 落点独立重算全部命中**：H-D1→`0x01B00000`、H-D2→`0x01B00040`、H-D5→`0x01B00080`、H-D6→`0x01B000C0`、H-D6b→`0x01B00100`、L4(`force-full`)→`0x006D3E37`（与原版 `jge` 同落点）。
- **原指令解码与文档一致**：`0x508F8F je 0x508FF6`、`0x6D3D99 jge 0x006D3E37`、`0x75092E xor eax,eax; pop ecx; ret 8`、`0x7509EC xor eax,eax; pop ebx; ret 4`。
- **PE 事实**：`.detour` 节 **VA `0x00B93000`**（RVA `0x793000`，RawPtr `0x497000`，RawSize `0x3000`）；`.text` 满足 `文件偏移 = VA − 0x400000`（抽验 7 处全中）；`0x01B00000` 页**不与任何节区重叠**。
- **哈希**：`gamemd.exe` MD5 = `4f37486e5b0dbe2ae5f45aeee0f98367`，与执行总表流水线第 3 步（L436）钉的哈希**一致**；`ra2render/ra2render.ini` 与 `ra2youli/ra2render.ini` 字节相同（2747 B，md5 `190709d025c133757142062f996e0ed6`），满足「两份同步」约束。

---

## 2. 裁决收敛核对（G-01 … G-10）

### 2.1 权威裁决落点

- **`docs/re/mp_release_safety_checklist.md`**：§一 `L19-24`（R-01 G-01 / R-02 G-02 / R-03 G-08 / R-04 G-05，含「Lead 终局裁定内容 + 落地口径 + 优先级」四列）；§三 `L60-71`（MP-G01…MP-G10 逐条核验表）；§四 `L79-85` 发布门禁树。
- **`docs/re/ARCHITECTURE_ATLAS.md` §9.4 `L1530-1544`**：`G-01…G-09 联机安全门控矩阵`（关键配置键 + 默认值 + 拦截规则），另有 §`L145-152` 音频 ABI 与 L4 裁决定谳、§`L1520-1526` H-D1…H-D6b 探针表。
- **技术依据（字节级）**：`docs/re/net_sync_checksum.md` §13.3 `L844-909`（G-03/G-04/G-06/G-07/G-09 的代码位置与指令级实证）、§4.2 `L312-331`（序列化范围）。

### 2.2 逐条收敛对照

| 缺口 | Lead 终局政策（task-13 给定口径） | 权威落点 | `hook_gate_gap_table.md` 现状 | `MP_SAFETY_REVIEW.md` 现状 | 收敛判定 |
|---|---|---|---|---|---|
| **G-01** | `EnableMinimapFog` API 默认→**0** | checklist `L21`(R-01,P0)；atlas `L1536` | `L38`/`L129` 仍写「API 默认仍 **1**」为待补缺口（无裁定列） | 全文无 G-01 字样；`L400` 以「缺陷1 崩溃」为由建议默认 0 | 政策已定／文档未标 → **勘误 E-1/E-2** |
| **G-02** | 联机强制 `position` 键 | checklist `L22`(R-02,P0)；atlas `L1537` | `L177` 仍为「建议…强制 position」 | `L399` 只提 `TargetScanInterval=1`；未提强制键型 | 同上 |
| **G-03** | `[Logic] EnableThreatRetention=1`（MP 强制 0） | checklist `L64`(MP-G03,P1)；atlas `L1538`；net_sync `L857` | `L178`「补键」为建议 | `L271`/`L404` 为「修键后对拍／不过则禁短路」，键名未定 | 同上 |
| **G-04** | B1/B2 混色桩 + L4 补丁接入 **`EnableStarCraftFog` 总闸** | atlas `L1539`（总闸默认 1，置 0 联动关 B1/B2/L4 并逐字节还原）；net_sync `L866-868`；checklist `L65` | `L128`/`L179` 建议为**独立键**（`EnableFogBlendStubs`/`L4DirtyMode`）或随总闸 | `L381-386` 指出「全 fog 键 =0 时三处仍安装生效」；`L403` 建议独立键 | 政策＝**总闸**（独立键仅作补充）→ **勘误统一口径** |
| **G-05** | `Hook_RadarPending_Proxy` 受 `s_minimapFogGate` 门控 | checklist `L24`(R-04,P2)；atlas `L1540` | `L103`/`L180` 缺口描述 + 建议补 `cmp/je` | `L283` 只标 SAFE，`L404` 未提 #21 gate | 政策已定／文档未标 |
| **G-06** | `[Multiplayer] MpStateWrites=0` | checklist `L67`(MP-G06,P1)；atlas `L1541`；net_sync `L883` | `L114`/`L181`「或新键 `MpStateWrites`」 | `L402`「挂到 `EnableSpySatRadarSweep`（**或**新键 `MpStateWrites=0`）」 | 政策＝`MpStateWrites=0`（旁路为其实现）→ 二选一口径需**勘误收敛** |
| **G-07** | TYPE 补丁 Remove 还原 | checklist `L68`(MP-G07,P1)；atlas `L1542`；net_sync `L893`；落地规格见 `landing_pack_gap_spysat.md` §3 | `L182` 缺口行 | `L284`(S1 RISK)、`L401`（备份原值 + 提供 Remove） | **已收敛**（结论见 §2.3） |
| **G-08** | 联机强制 `TargetScanInterval=1` | checklist `L23`/`L69`(R-03/MP-G08,P0)；atlas `L1543` | `L183`「联机强制 1（W1）」为建议 | `L399` P0 写「ini 即时止血」，未写「联机**无条件强制**」 | 政策已定／口径需补 |
| **G-09** | `everSeen` 不进档 | checklist `L70`(MP-G09,P2)；atlas `L1544`；net_sync `L895-909` | `L184` 缺口行 | `L411`（§6.2 已述「不进档…进档须 bump 存档魔数」）**一致** | **已收敛**（结论见 §2.3） |
| **G-10** | 死符号／空开关清理（卫生项） | checklist `L71`(MP-G10,P2,SAFE) | `L185` 缺口行（含 `UnlockGameSpeed` 空开关、RLE 空转、死符号 #10） | 未涉及（不属其审计范围） | 政策已定／不阻断发布 |

**收敛口径结论**：`G-01…G-10` 的**政策面已全部收敛**且与本任务给定口径 7 条逐字一致（G-01/G-02/G-05/G-08 完整对应 R-01…R-04；G-03/G-04/G-06 对应 atlas §9.4 + net_sync §13.3；G-07/G-09 对应 MP-G07/MP-G09）[实证]。
**文档面未收敛**的是两份被审文档（`hook_gate_gap_table.md` §5 只有「建议改动」四列；`MP_SAFETY_REVIEW.md` 成文于裁定之前，全文不含 G 编号）→ 已在附录 A 追加**标记型勘误**（不改正文）。

> **证据陈旧勘误（重要）**：`hook_gate_gap_table.md` `L38`/`L129` 记 G-01 两方证据为「API 默认 1（`:103`）≠ **ini 现值 0**（`ra2render.ini:44`）」。工作树实测：`ra2render/ra2render.ini` **第 45 行** `EnableMinimapFog=1`（第 44 行是注释），两份 ini 副本字节一致 [实证]；源码 `blitter_hooks.cpp:103` 默认参数仍为 `1` [实证]。→ G-01 缺口应改写为「**API 默认 1 且 ini 现值亦为 1；真正风险是键缺失/安装包漏配时静默全开**」，**R-01（默认改 0）仍必需**。

### 2.3 专项结论：G-07 与 G-09

#### G-07（S1 TYPE 补丁无 Remove 还原）→ **采纳：备份 4 字段 + `RemoveVTableHooks` 尾部还原**

- 缺口客观存在 `[实证]`：`hook_gate_gap_table.md:182`；`INSTALLED_HOOKS_AUDIT.md` A8；源码侧 `ra2render/blitter_hooks.cpp:596 PatchSpySatBuildingTypes()` 无任何备份结构（全文检索 `RestoreSpySat` / `origRecharge` **0 命中**），`RemoveVTableHooks()`（`:1712`）亦无 TYPE 还原调用。
- 还原规格可直接落地 `[实证]`（规格级）：`landing_pack_gap_spysat.md` §3.2.1-3.2.3（`L229-279`）给出备份结构、**首次写前保存**、卸载尾部还原与调用顺序；§3.2.4（`L283-290`）给出值域自检（`+0xB0` 典型 4500、`+0xF8` 0.0、`+0x16A5` true、`+0x16F0` −1）；执行表第 5-8 步（`L378-385`）。
- 还原本体**不进同步契约** `[实证]`：`net_sync_checksum.md` §4.2 `L312-331` 的进档清单只有 `CurrentFrame`、`ScenarioClass`、对象数组、`House`、`Map/Cell`、命令队列 —— **TYPE 单例（`BuildingTypeClass`/`SuperWeaponTypeClass`）不在列**；还原只在卸载/退出路径发生，不参与对局内状态演化 → SAFE。
- 但 S1 的**写出**仍是条件面 `[实证+推演]`：改 `+0xB0` 充能帧 → 改 Launch 发生帧；改 `+0x16A5/+0x16F0` → 改超武授予/全图开语义（net_sync §13.3 `L885-893`）→ 联机仍须 `EnableSpySatRadarSweep=0` 或全端同值。
- 残留 `[推演]`：备份须「首次写前取、跨战局重载不覆盖」（`L227`/`L256`/`L319`）；`s_spyBldBackups[64]` 容量在 >64 个 SpySat 建筑类型时会丢弃备份，建议补「溢出告警 + 不写入」策略。

#### G-09（`everSeen` 不进档）→ **采纳：保持现状 + 文档声明，判为体验遗留（非 desync）**

- `[实证]` 源码：`s_everSeenGrid` 是 DLL 内部 `static uint8_t[512*512]`（`blitter_hooks.cpp:44`），战局重载/读早期档时 `memset` 清零（`:712-715`），与引擎存档管线无任何交互。
- `[实证]` 引擎侧：`CellClass::Save 0x483C10` / `CellClass::Load 0x4839F0` 只序列化格位数据（net_sync `L897`）；`net_sync_checksum.md` §4.2 进档清单不含该网格；帧 CRC `0x64DAB0` 不覆盖 DLL 私有内存（net_sync `L908`）。
- `[推演]`：因此「读档后侦察记忆清零」不构成锁步分叉，判 P2、**不作为发布阻断项**（checklist `L70`）。
- 边界 `[推演]`：若未来要持久化，则必须进档（bump 存档魔数 + 双端同构建，MP_SAFETY_REVIEW `L411`）→ 当前选择「不做」是正确取舍。

---

## 3. 六大落地包 × 5 字段一致性审计

### 3.1 口径与统计

- **5 字段**：`目标 VA` / `原字节` / `新字节` / `开关与默认值` / `回滚路径`（取自执行总表 §一 总表列头 L35 与各包字段表）。
- **比对方**：`pending_execution_master_table.md`（记 `M:行`） vs 各落地包文档（记 `P:行`；交叉覆盖包另注）。机械定位见 `out/re_work/mp_landing/matrix_5fields.md`（每格给出命中行号，`MISSING` 即该文档无此 token）。
- **判定**：`✓ 一致`＝两方 token 全命中且字节断言通过（`audit_orig_bytes.json`）/ `✗ 冲突`＝两方给出不同值（详见 §4）/ `缺失`＝一方无该字段 / `—`＝该项本就无此字段（如无字节补丁、原生 API 驱动）。
- **统计（90 格）**：**一致 71 / 冲突 12 / 缺失 1 / 不适用 6**。

### 3.2 P-1 · 联机同步诊断探针包（H-D1/H-D2/H-D5/H-D6/H-D6b）

| 补丁项 | 目标 VA | 原字节 | 新字节 | 开关与默认值 | 回滚路径 | 判定 |
|---|---|---|---|---|---|---|
| P-1.1 H-D1 | ✓ `M:37,382` / `P:152,651` `0x0064C6F2` | ✓ `M:37,382` / `P:152,651` | ✓ `M:37` / `P:159,651` | ✓ `SyncEarlyLog=0`（`M:37` / `P:217`） | ✓ `M:382` / `P:585,651` | **5/5 一致** |
| P-1.2 H-D2 | ✓ `M:38,383` / `P:262,652` `0x0064CC61` | ✓ `M:38,383` / `P:270,652` | ✓ `M:38` / `P:278,652` | ✓ `SyncSnapshotOnDesync=0`（`M:38` / `P:337`） | ✓ `M:383` / `P:586,652` | **5/5 一致** |
| P-1.3 H-D5 | ✓ `M:39,384` / `P:364,653` `0x0064DE75` | ✓ `M:39,384` / `P:380,653` | ✓ `M:39` / `P:386,653` | ✓ `SyncMirror=0`（`M:39` / `P:430`） | ✓ `M:384` / `P:587,653` | **5/5 一致**（含 ① 修正，见 §3.9） |
| P-1.4 H-D6 | ✓ `M:40,385` / `P:465,654` `0x0064C911` | ✓ `M:40,385` / `P:465,654` | ✓ `M:40` / `P:472,654` | ✓ `SyncCmdMirror=0`（`M:40` / `P:562`） | ✓ `M:385` / `P:588,654` | **5/5 一致** |
| P-1.5 H-D6b | ✓ `M:41,386` / `P:513,655` `0x0064CC0A` | ✓ `M:41,386` / `P:513,655` | ✓ `M:41` / `P:516,655` | ✓ `SyncCmdMirror=0`（`M:41` / `P:562`） | ✓ `M:386` / `P:589,655` | **5/5 一致** |

**留证（一致项比对依据）**
- 原字节 5/5 通过二进制断言（`claims_orig_bytes.txt` L1-5）`[实证]`。
- 新字节 5/5 的 `rel32` 独立重算命中声明的 cave 槽（`rel32_verify.json` → `patch_targets[*].MATCH=true`）`[实证]`。
- 回滚 hex = 原字节 hex（逐字节比对，`M:382-386` vs `P:585-589` / `P:651-655` 一致）`[实证]`。
- 开关默认值：两方均为 `0`（`M:283-288` / `P:100-109`），且 `P:109` 明确「软关 + 硬关都要提供，Install/Remove 必须对称」`[实证]`。
- 跳板约束：`P:25-35`（禁写 `.detour`、`VirtualAlloc(0x01B00000,0x1000)`）、`M:21-22`、`P:37-59`（cave 布局）——一致，但「分配失败」口径有差（→ **F-07**）。

### 3.3 P-2 · 裂缝保护 + SpySat 门控 + G-07 还原

| 补丁项 | 目标 VA | 原字节 | 新字节 | 开关与默认值 | 回滚路径 | 判定 |
|---|---|---|---|---|---|---|
| P-2.1 Gap1 | ✓ `M:42,387` / `P:54,66,378` `0x00568273` | ✓ `M:42,387` / `P:68,378` | ✓ `M:42` / `P:70,378` | ✓ `EnableGapProtection=1`（`M:42,292` / `P:80-83,358`） | ✓ `M:387` / `P:96,378` | **5/5 一致** |
> 【W3 勘误 · W3-A6/ISSUE-DEFAULT-GAPPROTECTION】改前：EnableGapProtection=1；改后：EnableGapProtection=0  ; [代码/出厂默认0，安全侧；测试或启用时显式置1]；依据：ra2render/blitter_hooks.cpp:606; ra2render/ra2render.ini:199; config_key_matrix.md:109；分级：P0
| P-2.2 Gap2 | ✓ `M:43,388` / `P:55,66,379` `0x00577EC5` | ✓ `M:43,388` / `P:68,379` | ✓ `M:43` / `P:70,379` | ✓ 同上 | ✓ `M:388` / `P:96,379` | **5/5 一致** |
| P-2.3 Gap3 | ✓ `M:44,389` / `P:56,66,380` `0x00577B60` | ✓ `M:44,389` / `P:68,380` | ✓ `M:44` / `P:70,380` | ✓ 同上 | ✓ `M:389` / `P:96,380` | **5/5 一致** |
| P-2.4 SpySat 门控 | ✓ `M:45,390` / `P:131,144,381` `0x00508F8F` | ✓ `M:45,390` / `P:143,145,381` | ✓ `M:45` / `P:146,381` | ✓ `EnableSpySatGate=1`（`M:45,293` / `P:157-159,360`） | ✓ `M:390` / `P:183,381` | **5/5 一致** |
| P-2.5 G-07 TYPE 还原 | — （动态内存，`M:46`） | — （运行时实读，`M:46`） | — （无字节补丁，`M:46`） | ✓ 无新增键，随 `EnableSpySatRadarSweep=1`（`M:46` / `P:296-297`） | **缺失**：`M:376-397` 逐字节回滚表**无 G-07 行**（仅 `M:405` 文字提到）；`P:261-279,385` 有 | **1 一致 / 1 缺失 / 3 不适用 → F-13** |

**留证（一致项比对依据）**
- 三处 6B 原字节 + SpySat 9B 窗口全部通过二进制断言（`claims_orig_bytes.txt` L8-12）`[实证]`；`je` 落点独立复算 `0x508F8F+2+0x65 = 0x508FF6` ✓（`rel32_verify.json`）。
- 新字节：Gap 三处 `90×6`、SpySat `EB 65`（等长、同落点）两方逐字一致 `[实证]`。
- 执行形态一致：两方均为**安装门控**（`=0` 时不写字节，非运行时空开关）`[实证]`（`P:83-84` / `M:42`）+ 硬卸载 `Remove*`（`P:86-87,96` / `M:405`）。
- MP 覆盖一致：两方都要求 `EnableGapProtection`/`EnableSpySatGate` **联机全员强制同值**（`M:320-321` / `P:346`）`[实证]`。
- 执行表（`P:376-389`）含「MD5 前置核对 = 4f37486e…」——与本任务实测一致（§1.2）`[实证]`。

### 3.4 P-3 · 微粒/粒子系统迷雾剔除（`particle` 为主包，`crt_audio` 模块三为覆盖包）

| 补丁项 | 目标 VA | 原字节 | 新字节 | 开关与默认值 | 回滚路径 | 判定 |
|---|---|---|---|---|---|---|
| P-3.1 Particle 槽 69 | ✓ `M:47,391` / `P:66,74,415` `0x007EFA68` | **✗ 冲突**：`M:47,391` `C0 CE 62 00` vs `P:66` `00 62 CE C0`（`P:74,378,415` 又写回 LE `C0 CE 62 00`） | ✓ `M:47` / `P:66,397,415`（符号 `Hook_Particle_Draw`） | **✗ 冲突**：`M:47`=`0` / `P:287,298`=`0` vs 覆盖包 `crt_audio:422`=`1` | ✓ `M:391` / `P:329,381,400,415` | **3 一致 / 2 冲突 → F-04/F-03** |
> 【W3 勘误 · W3-A6/ISSUE-PARTICLE-BE-BYTES】改前：00 62 CE C0；改后：C0 CE 62 00 / 80 E2 62 00 (小端 LE)；依据：errata_sync_master_table.md:23 (R-E08); FIXPACK_F01-F13_report.md F-04；分级：P0
| P-3.2 PSys 槽 69 | ✓ `M:48,392` / `P:67,74,416` `0x007EFCB0` | **✗ 冲突**：`M:48,392` `80 E2 62 00` vs `P:67` `00 62 E2 80`（`P:74,378,416` 为 LE） | ✓ `M:48` / `P:67,397,416` | **✗ 冲突**：同 P-3.1 | ✓ `M:392` / `P:329,381,400,416` | **3 一致 / 2 冲突 → F-04/F-03** |

**留证（一致项比对依据）**
- 槽 69 两条目地址 + LE 原字节通过二进制断言（`claims_orig_bytes.txt` L13-14，`env_facts.json` 亦证 `VA−0x400000 = 0x3EFA68`）`[实证]`。
- 新字节一致：两方均为**虚表 DWORD 覆写**（`PatchVTablePointer`），**禁止** inline patch `0x0062CEC0`/`0x0062E280`（`M:133-135` / `P:112-119,417-418`）`[实证]`。
- 早退契约一致：`ret 8`（callee 清栈，签名 `FnDrawObject`）—— `M:47-48` / `P:115` / `M:421`(TC-ST-03) `[实证]`。
- 回滚一致：写回原 DWORD（`0x0062CEC0` / `0x0062E280`），与 Bullet 槽同批装卸、幂等（`M:391-392` / `P:329,381,399-400`）`[实证]`。
- 主包 `P:379`「默认 0（验收时显式置 1）」与 `M:47` 一致；覆盖包 `crt_audio` 的「默认 1」为**陈旧口径**（→ F-03）。

### 3.5 P-4 · CRT 高频小对象池化

| 补丁项 | 目标 VA | 原字节 | 新字节 | 开关与默认值 | 回滚路径 | 判定 |
|---|---|---|---|---|---|---|
| P-4.1 operator new | ✓ `M:49,393` / `P:18,21,151` `0x007C8E17` | ✓ `M:49,393` / `P:151` | **✗ 冲突/缺失**：`M:49` 仅给占位 `E9 rel32 90`；`P` 无字节级新字节（只有 C++ 代码） | **✗ 冲突**：`M:49,301`=`0`（并注「启动期单次锁定」）vs `P:148`=`1` | ✓ `M:393` / `P:151` | **3 一致 / 2 冲突 → F-05/F-02** |
| P-4.2 operator delete | ✓ `M:50,394` / `P:25,28,152` `0x007C8B3D` | ✓ `M:50,394` / `P:152` | **✗ 冲突/缺失**：`M:50` 占位 `E9 rel32 90 90 90 90`；`P` 无字节表 | **✗ 冲突**：同 P-4.1 | ✓ `M:394` / `P:152` | **3 一致 / 2 冲突 → F-05/F-02** |

**留证（一致项比对依据）**
- 两处挂钩点原指令 6B/9B 通过二进制断言（`claims_orig_bytes.txt` L15-16），与 `crt_memory_pool_deep_dive.md` 的 `_nh_malloc` 链一致 `[实证]`。
- 回滚 hex 两方逐字一致（`6A 01 FF 74 24 08` / `FF 74 24 04 E8 A2 08 00 00`）`[实证]`；`M:399-409` 另给热卸载五阶段（含 `VirtualFree(0x01B00000)`）`[实证]`。
- 未闭合项另见 **F-06**（块头 4B vs 8B、magic 常量两套写法）。

### 3.6 P-5 · 音频并发削峰

| 补丁项 | 目标 VA | 原字节 | 新字节 | 开关与默认值 | 回滚路径 | 判定 |
|---|---|---|---|---|---|---|
| P-5.1 PlayGlobal | ✓ `M:51,395` / `P:159,162,282` `0x00750920` | ✓ `M:51,395` / `P:282` `51 A0 AC 64 84 00`（6B） | **✗ 冲突/缺失**：`M:51` 占位 `E9 rel32 90`；`P` 无字节表 | ✓ `EnableAudioThrottling=1` + `MaxSoundsPerFrame=4` + `SoundMinIntervalFrames=2`（`M:51,306-308` / `P:279`） | ✓ `M:395` / `P:282` | **4 一致 / 1 冲突 → F-05** |
| P-5.2 PlayAt | ✓ `M:52,396` / `P:165,168,283` `0x007509E0` | **✗ 冲突**：`M:52,396` = **5B** `A0 AC 64 84 00` vs `P:166-170,283` = **6B** `A0 AC 64 84 00 53` | **✗ 冲突/缺失**：`M:52` 占位 `E9 rel32`（5B）；`P` 无字节表 | ✓ 同 P-5.1 | **✗ 冲突**：`M:396` 5B vs `P:283` 6B | **2 一致 / 3 冲突 → F-01/F-05** |

**留证（一致项比对依据）**
- 目标 VA + PlayGlobal 6B 原字节通过二进制断言（`claims_orig_bytes.txt` L17）；PlayAt 首指令实测 `A0 AC 64 84 00`（5B），紧随 `0x7509E5` 为 `53 push ebx`（`claims_orig_bytes.txt` L19）→ 5B/6B 之争的物理事实已定（→ F-01）`[实证]`。
- 开关与默认值两方逐字一致（`M:51-52,306-308` / `P:279`）`[实证]`。
- ② 号修正（ABI 契约）两方均已落表且与原生分支一致 —— 见 §3.9。

### 3.7 P-6 · L4 视口局部打脏

| 补丁项 | 目标 VA | 原字节 | 新字节 | 开关与默认值 | 回滚路径 | 判定 |
|---|---|---|---|---|---|---|
| P-6.1 `0x006D3D99` 双模 | ✓ `M:53,254,397` / `P:30,35,47-48` | ✓ `M:53,397` / `P:35,48` `0F 8D 98 00 00 00` | ✓ `force-full` `E9 99 00 00 00 90`（`M:53,256` / `P:47`）；`vision-dirty` 恢复原指令（`M:53,258` / `P:48`） | ✓ `L4DirtyMode=force-full`（`M:53,312` / `P:251-258`） | ✓ 热回滚 `P:261-265`；硬卸载还原原字节 `M:397`（`P` 未单列 → 附注） | **5/5 一致**（附注） |
| P-6.2 `0x006DA7D0` 打脏 | ✓ `M:54,262` / `P:55,60,157` `0x006DA7D0` | ✓ `M:54` / `P:60` `A1 F4 F7 87 00`（原生 API） | — 原生 API（非 Hook，`M:54`） | — 随 `L4DirtyMode`（`M:53`） | — 无字节补丁 | **2 一致 / 3 不适用** |

**留证（一致项比对依据）**
- `0x006D3D99` 原 6B 与上下文（`0x006D3D97 cmp eax,edx`）通过二进制断言（`claims_orig_bytes.txt` L21-22）`[实证]`。
- `force-full` 的 `E9 99 00 00 00 90` 独立重算落点 `0x006D3E37` = 原 `jge` 落点（`rel32_verify.json`）`[实证]`。
- `0x006DA7D0` 原指令 `A1 F4 F7 87 00` 通过断言（`claims_orig_bytes.txt` L30）`[实证]`；两方均强调**严禁挂钩 `0x0048D000`**（`M:54,272` / `P` 同）`[实证]`。
- 两方均含「>350 格翻转 → 置 `+0xD7D Redrawing=1` 全屏保底」与遥测 `fallbackToFullCount`（`M:54,268,355` / `P:97,275`）`[实证]`。
- 独占约束一致：`P:287` 声明独占 `0x006D3D99` 6B，禁止叠加覆写 `[实证]`。

### 3.8 交叉文档速览（`crt_audio` 三合一包的角色）

`landing_pack_crt_audio_particle.md` 同时覆盖 P-3/P-4/P-5 三项，是本次**全部 12 格冲突中的 10 格来源**：P-3 默认值 2 格 + P-4 默认值 2 格 + P-4 新字节 2 格 + P-5 新字节 2 格 + P-5.2 原字节/回滚 2 格。其 CRT/音频的**正文字节事实**（`:18-31`、`:159-170`）与二进制断言一致，仅**字段口径**陈旧，属可低成本收敛的文档面差异（§4 给出裁定建议）。

### 3.9 三条已知修正的落表核查 `[实证]`

| # | 修正内容 | 落表状态 | 证据 |
|---|---|---|---|
| **①** | H-D5 由 `83 E0 FF`（no-op 符号扩展）改为 **`0F B6 C0`**（`movzx eax,al`） | **已落表 ✓** | 执行总表 `L39`（总表「★ 关键纠正」）、`L81-87`（§2.1.2 漏洞根因 + `0x01B00090` 3 字节替换 + 48B 连写 hex）、`L419`(`TC-ST-01` 一票否决「回滚回 `83 E0 FF`」)、`L440`(流水线)、`L481`(移交重点)；`net_fix:399,413,416,647`；权威侧 `ARCHITECTURE_ATLAS:144/1524`。编码学复核：`83 E0 FF` → `and eax, 0xffffffff`（**真 no-op，高 24 位不清零**），`0F B6 C0` → `movzx eax, al`（`known_fixes.json` → `C1_hd5_movzx.encoding_check`）；48B 跳板内 `0x01B00090` 位置与 §2.1.2 描述一致（逐字节核对 `9C 60 83 3D 08 04 B0 01 00 74 1B A1 84 ED A8 00 0F B6 C0 …`） |
| **②** | 音频 `PlayGlobal ret 8` / `PlayAt ret 4` / 早退 `eax=0`（对齐原生 `0x75092E` / `0x7509EC` 的 `xor eax,eax`） | **已落表 ✓** | 执行总表 `L51-52`（★★ 关键修正）、`L224-241`（§2.5.1 完整 ABI 契约，含「严禁 `or eax,-1; ret`」）、`L423`(`TC-ST-05`)、`L481`；`crt_audio:176-178`（明列原生禁用分支 `0x0075092E = 33 C0 59 C2 08 00`、`0x007509EC = 33 C0 5B C2 04 00`）。二进制复核：两处原生分支字节断言通过（`claims_orig_bytes.txt` L20-21），capstone 解码为 `xor eax,eax; pop ecx; ret 8` / `xor eax,eax; pop ebx; ret 4`（`known_fixes.json`） |
| **③** | 跳板禁写 `.detour` / 统一基址 `0x01B00000` / `VirtualAlloc` 失败**即放弃该项** | **部分落地：2/3** | **禁写 `.detour` ✓**：`M:21-22,64`；`net_fix:16,25,35,128`；`gap_spysat:74,393`；`particle:119,171,330,357`。**统一基址 ✓（仅 P-1）**：`M:22,63`；`net_fix:16,29,37,644`；cave 布局 `M:66-79` / `net_fix:41-59`。**「失败即放弃该项」✗ 未落地**：`M:22` 写「失败走**动态重定位**」、`net_fix:16,28,639,741` 写「失败则走**附录 C 重定位**」，两条执行链均**没有**「放弃该项／不得带病安装」约束；该约束只存在于顶层台账 `REVERSE_ENGINEERING_AND_PATCHES.md:1183`（Lead 运行时硬要求 ①）与 `z3_troubleshoot_net_fix_gap.md:25` → **F-07**。另：P-4/P-5 的 `E9 rel32` 仍是**占位符**、未分配 cave 槽位，与「统一基址」不闭合 → **F-05** |

---

## 4. 不一致清单（每条：涉及文档与行号 / 两方证据 / 建议裁定）

> 全 13 条。`F-01…F-06` 对应 12 格字段冲突与 1 格缺失；`F-07…F-13` 为策略面/文档面不一致或跨链缺口（不单独计格）。

### F-01 【高】P-5.2 `PlayAt` 字节足迹 5B vs 6B（2 格冲突）
- **涉及**：`pending_execution_master_table.md:52`（原字节 5B `A0 AC 64 84 00`，新字节 `E9 rel32`）、`:233-235`（§2.5.1「入口 VA `0x007509E0`（原 **5 字节**）」）、`:396`（§4.1 回滚表「**5 字节**」）；`landing_pack_crt_audio_particle.md:165-170`（「原版指令（**6 字节**）`A0 AC 64 84 00 53`」）、`:283`（回滚「还原 **6 字节**原指令 `A0 AC 64 84 00 53`」）。
- **两方证据**：二进制实测 `0x007509E0 = A0 AC 64 84 00`（5B，`mov al,[0x8464AC]`），下一指令 `0x007509E5 = 53`（`push ebx`）→ **5B 是首指令真实长度**（`claims_orig_bytes.txt` L18-19；`matrix_5fields.md` P-5.2）`[实证]`。执行表/回滚表全链（含 `TC-ST-05`）均按 5B 书写，仅覆盖包按 6B。
- **建议裁定**：**采纳 5B**。勘误 `crt_audio` §1/§4 为 5B；若坚持 6B，则必须同步改 master 总表 `L52` + §2.5.1 + §4.1，并让跳板额外重放 `53 push ebx`（否则回滚后栈语义不符）。

### F-02 【高】P-4 `EnableMemoryPool` 默认值 0 vs 1（2 格冲突）
- **涉及**：`pending_execution_master_table.md:49`（`EnableMemoryPool=0`「**启动期单次锁定配置**」）、`:301`、`:322`（MP 覆盖表 default `0`）；`landing_pack_crt_audio_particle.md:148`（`[System] EnableMemoryPool=1`（**默认 1**））。
- **两方证据**：`ra2render/**` 现网无该键（0 命中）→ 两文档都在**新定义**该键 `[实证]`；master 侧 §2.4.2 P-M1…P-M5 加固（8B 头 / 双释放 / 范围守卫 / CAS / 启动期锁定，`L185-218`）与「默认 0 = 保守 + 可单关」自洽；`crt_audio` 侧模块一为 4B 头旧草案（另见 F-06），无启动期锁定条款。
- **建议裁定**：**采纳 `0`**（并写入"启动期单次锁定、禁止局内热切换"，理由 `M:18-27`），勘误 `crt_audio:148`。

### F-03 【高】P-3 `EnableParticleFog` 默认值 1 vs 0（2 格冲突）
- **涉及**：`pending_execution_master_table.md:47`（默认 `0`）、`:297`、`:324`（MP 覆盖 `0`）；`landing_pack_particle.md:287,298,379,393`（默认 `0`，理由"先合入、验收时显式置 1"）；`landing_pack_crt_audio_particle.md:422`（默认 `1`）。
- **两方证据**：主包与执行表一致为 `0`；覆盖包为 `1`。默认值本身不涉字节断言，但**改变验收前提**（主包 `P:320` 要求 `=1` 时 `particlesCulledByFog > 0`，默认 0 时画面零变化）`[实证]`。
- **建议裁定**：**采纳 `0`**（与 G-01 的保守策略同构）；勘误 `crt_audio:422`。

### F-04 【中】粒子虚表原 DWORD 字节序标注冲突（2 格冲突）
- **涉及**：`pending_execution_master_table.md:47,48,391,392`（"原字节"列 = `C0 CE 62 00` / `80 E2 62 00`）；`landing_pack_particle.md:66,67`（"原虚表 DWORD"列 = `00 62 CE C0` / `00 62 E2 80`）vs 同文 `:74,378,415,416`（= `C0 CE 62 00` / `80 E2 62 00`）→ **包内自相矛盾**。
- **两方证据**：二进制 = `C0 CE 62 00` / `80 E2 62 00`（LE，即 DWORD `0x0062CEC0` / `0x0062E280`）`[实证]`（`claims_orig_bytes.txt` L13-14）。`00 62 CE C0` 是同一 DWORD 的**大端**书写，若被当作字节序列抄写将写入 `0xC0CE6200`（错误入口）。
- **建议裁定**：统一小端字节序，表头改「原字节（LE）」；`00 62 CE C0` 形态标注"= DWORD `0x0062CEC0`（BE 书写）"或删除。

### F-05 【高】P-4/P-5 新字节不可机械写入（rel32 占位 + 无 cave 槽位；4 格冲突）
- **涉及**：`pending_execution_master_table.md:18`（总则「零推演落地：仅机械式写入，**不得擅自修改指令编码与相对偏移**」）、`:49-52`（新字节列 `E9 rel32 90` / `E9 rel32 90 90 90 90` / `E9 rel32 90` / `E9 rel32`）、`:63-79`（§2.1.1 cave 布局**仅覆盖 P-1**；`net_fix` 反向印证 `:41-59`）；`landing_pack_crt_audio_particle.md:180-276`（音频只有 C++ 代码，**无字节级新字节表**）、`:196-199`（跳板为动态指针 `s_pPlayGlobalTrampoline`/`s_pPlayAtTrampoline`，**无统一基址**）、`:33-146`（CRT 侧同为 C++ 代码）。
- **两方证据**：P-1 五条全部"算好 rel32 + 分配槽位"（`net_fix:644-649`）并经本任务独立复算全部命中 `[实证]`；P-4/P-5 四条**缺 T0 槽位 → 无法算 rel32**，故 master 只能留占位符，`crt_audio` 连字节表都没有 `[实证]`。
- **建议裁定**：§2.1.1 增补 P-4/P-5 槽位（建议 `0x01B00140` CRT_NEW / `0x01B00180` CRT_DEL / `0x01B001C0` AUD_PG / `0x01B00240` AUD_PA，避让 `0x01B00200` NoopHelper 与 `0x01B00400` 起数据区），并把 4 条 `rel32` 填实；同时要求 `crt_audio` 补一张与 `net_fix` §9 同规格的执行表（步骤→地址→原字节→新字节→开关→回滚→验收）。若裁定走"运行时动态分配"，则须与 F-07 的「失败即放弃」一致，并把动态基址纳入自检。

### F-06 【中】CRT 块头 4B vs 8B、magic 两套写法（附加冲突，未单列格）
- **涉及**：`pending_execution_master_table.md:186-196`（`PoolBlockHeader{magic,poolIdx}` = 8B、`pack(8)`、`m_elemSize=(elemSize+7)&~7`、返回 `pBlock+8`）、`:422`（`TC-ST-04` 一票否决：「**头部为 4 字节**」或「返回地址非 8 字节对齐」→ FAIL）；`landing_pack_crt_audio_particle.md:34`（"头部预留 **4 字节** Tag（`MAGIC_POOLED = 0xA5A50000 | poolIdx`）"）、`:45-49`（`struct PoolHeader{uint32_t magic;}` + `pack(4)`）、`:54`（`(elemSize+3)&~3`）。
- **两方证据**：master 的 8B/8 对齐依据是 `Vector3D<double>` 的 8 字节自然对齐（`M:196`）`[实证+推演]`；4B 方案会把返回指针对齐降到 4 字节 → **与 `TC-ST-04` 直接冲突**（同一总表内部矛盾）。
- **建议裁定**：采纳 **8B 头 + 8B 对齐 + `pBlock+8`**，magic 统一 `0xA5A55A5A`（`poolIdx` 作独立字段）；据此改写 `crt_audio` 模块一。

### F-07 【高】「`VirtualAlloc` 失败」口径：放弃该项 vs 走重定位（修正 ③ 的第 3 条未落地）
- **涉及**：`pending_execution_master_table.md:22`（"失败走**动态重定位**"）；`landing_pack_net_fix.md:16`（"失败则走**附录 C 重定位**"）、`:28`（注释）、`:639`（"若实际分配不同，先跑附录 C 重定位再写"）、`:712-720`（附录 C 机械重定位表）、`:741`（`if cave != 0x01B00000: 用附录 C 重定位`）；**权威/台账侧**：`REVERSE_ENGINEERING_AND_PATCHES.md:1183`（"`VirtualAlloc(0x01B00000, 0x1000, …)` **失败必须放弃该项**（走重定位表），**不得带病安装**"）、`z3_troubleshoot_net_fix_gap.md:25`（"① 失败**放弃该项**（禁止瞎写）"）、`:37-44`（T1：让系统选址 + 整表重算）。
- **两方证据**：两份执行文档现行流程为"失败 → 换基址 → 重定位重写"，**不含**"放弃/不得带病安装"闸门；台账硬要求含"放弃该项"，但括注"（走重定位表）" → 政策表述本身存在**两种可执行解释**，执行文档只实现了宽的一种 `[实证]`。
- **建议裁定**：二段式落地 —— ① 先试 `0x01B00000`；② 失败 → **该项不安装**（跳过 + 红字日志 + 遥测计数），**严禁**在未重算 rel32 的其它基址写死 hex；③ 附录 C 重定位降级为"离线预备"，启用前提为"整表 rel32 重算 + 装后自检 5 处 `E9` + 跳板槽可执行"三项齐备（台账 `:1183` ③）。两份文档各补一行硬约束。

### F-08 【中】`.detour` 节 VA 误标（RVA 当 VA）
- **涉及**：`landing_pack_particle.md:119`（"PE 存在 `.detour` 节（`VA=0x00793000`）"）；对照 `pending_execution_master_table.md:22`（`VA 0x00B93000`）、`landing_pack_net_fix.md:35`（`VA 0xB93000`）。
- **两方证据**：PE 节表实测 `.detour` **VA `0x00B93000`**、RVA `0x00793000`、RawPtr `0x497000`、RawSize `0x3000`；`0x00793000` 不落在任何节区（`.rdata` 起 `0x7E1000`）`[实证]`（`env_facts.json`）。
- **建议裁定**：统一 `VA 0x00B93000`（若需 RVA 则注明"RVA `0x793000`"）；勘误 `particle:119`。

### F-09 【中】执行总表未纳入 MP 裁决键（跨链缺口）
- **涉及**：`pending_execution_master_table.md:282-313`（§3.1 INI 声明：仅 `[SyncDiag]`/`[FogOfWar]`/`[System]`/`[Audio]`/`[Render]` 的 P-1…P-6 新键）、`:315-325`（"联机强制覆盖规则表" 6 行）；对照 `:23-25`（自述"联机同步强红线（OOS 防护）"）。
- **两方证据**：全表 grep **0 命中** `EnableMinimapFog` / `TargetScanKey` / `TargetScanInterval` / `EnableThreatRetention` / `MpStateWrites` / `s_minimapFogGate` `[实证]`；而 Lead 的 7 条裁决（§2.2）全部落在这些键上（`mp_release_safety_checklist.md:21-24,62-69`）。
- **建议裁定**：§3.1 增补 `[FogOfWar] EnableMinimapFog=0`（API 默认 0）、`[Logic] TargetScanInterval`（MP 强制 1）、`[Logic] TargetScanKey`（MP 强制 position）、`[Logic] EnableThreatRetention`（默认 1、MP 强制 0）、`[Multiplayer] MpStateWrites=0`、`MpAutoDowngrade/ForceSinglePlayer`，MP 覆盖表补 4 行；否则执行方按总表操作会**整体漏掉 MP 硬红线**。

### F-10 【中】`MpActive()` 地址误引（`0x00A8ED84` 实为 `CurrentFrame`）
- **涉及**：`pending_execution_master_table.md:316`（"联机模式由 `MpActive()`（`0x00A8ED84` 处于对局网络循环）判定"）。
- **两方证据**：本项目其他文档一致将 `0x00A8ED84` 作 `CurrentFrame`（`landing_pack_net_fix.md:67` 只读符号表；同文 `:398` H-D5 跳板 `mov eax,[0xA8ED84] ; CurrentFrame`；`landing_pack_crt_audio_particle.md:205` 同）`[实证]`；`MpActive()` 权威定义 = `(*(uint8_t*)0x00A8D5F8 & 0x02)`（`mp_release_safety_checklist.md:33-34`；`mp_autodowngrade_spec.md:21,58-119`）`[实证]`。
- **建议裁定**：改为 `0x00A8D5F8` bit1（辅助判定 `0x00AA0444 == 2`）。理由：按 `0xA8ED84` 判联机 = 把"当前帧号"当会话标志 → MP 降级会误触发/失效。

### F-11 【中】G-01 两方证据陈旧（ini 现值 0 → 实测 1）
- **涉及**：`hook_gate_gap_table.md:38`、`:129`（"`EnableMinimapFog` ini 现值 **0**（`ra2render.ini:44`）"）。
- **两方证据**：工作树 `ra2render/ra2render.ini:45 = EnableMinimapFog=1`（`:44` 为注释），`ra2youli/ra2render.ini` 字节相同 `[实证]`（`env_facts.json`）；API 默认仍为 1（`blitter_hooks.cpp:103`）`[实证]`。
- **建议裁定**：勘误为"API 默认 1；ini 现值 1（`:45`）"，缺口重述为"**键被删/安装包漏配即静默全开**"（R-01 P0 不变）。

### F-12 【低】执行总表 cave 布局缺遥测计数器槽位
- **涉及**：`pending_execution_master_table.md:63-79`（布局：`+0x400..+0x40C` 开关、`+0x500/504/50C` 函数指针、`+0x600` 镜像环 → **无 `+0x410..+0x420`**）；同文 `:402`（H-D5 跳板 `inc dword ptr [0x01B0041C]`）；对照 `landing_pack_net_fix.md:51-55,118-119`。
- **两方证据**：H-D5 跳板实际写 `0x01B0041C`（`net_fix:402` + 连写 hex `FF 05 1C 04 B0 01`）`[实证]`，而总表未声明该地址。
- **建议裁定**：`:63-79` 增补 5 行计数器（`g_syncEarlyLogCount` … `g_syncCmdMirrorCount` @ `0x01B00410..0x420`）。

### F-13 【低-中】G-07 未进「逐字节回滚表」；`l4` spec 未列硬卸载还原（1 格缺失）
- **涉及**：`pending_execution_master_table.md:376-397`（§4.1 逐字节还原表 16 行，**无 G-07**；G-07 仅见 `:46`、`:126`、`:405` 的文字描述）；`l4_vision_dirty_final_spec.md:261-265`（§五.2 仅有"热回滚"，未写卸载时还原 `0F 8D 98 00 00 00`）。
- **两方证据**：`landing_pack_gap_spysat.md:261-279,385` 已给还原规格与调用顺序 `[实证]` → §4.1 缺行属**总表自身不完整**（非两方冲突）；`l4` 的回滚缺失可由 master §4.1 兜底（`M:397`），但单看该包无法得知卸载语义。
- **建议裁定**：§4.1 增补一行「**G-07 TYPE 4 字段**（`SW+0xB0/+0xF8`、`Bld+0x16A5/+0x16F0`，动态地址）| 首次写前实读值 | `RestoreSpySatBuildingTypes()` | `M:405` 第 3 阶段」；`l4` §五 补一句"卸载/进程退出时写回原版 `0F 8D 98 00 00 00`"。

---

## 5. 一致项的留证方式（逐类说明比对依据）

| 一致性类别 | 留证方式 | 证据产物 |
|---|---|---|
| 目标 VA / 槽位（18 项） | 每项在两文档的命中行号 + `VA − 0x400000 = 文件偏移` 抽验 7 处全中 | `matrix_5fields.md`、`env_facts.json` |
| 原字节（16 项有字节补丁） | 逐字节二进制断言（`tools/audit_bytes.py`），**31/31 全 OK** | `claims_orig_bytes.txt`、`audit_orig_bytes.json` |
| 新字节（P-1 五条 / P-2 四条 / P-6 一条） | capstone 反汇编原指令 + 独立重算 `E9 rel32` 落点，6/6 命中声明槽位 | `rel32_verify.json` |
| 新字节（P-3 两条） | 两方均为符号名（`&Hook_*`），机制一致（虚表 DWORD 覆写、禁止 inline） | `matrix_5fields.md` + `particle:112-119,415-418` |
| 开关与默认值（P-1/P-2/P-5/P-6） | 两文档键名 + 默认值逐字比对（P-1 四条 `0`、P-2 两条 `1`、P-5 三键 `1/4/2`、P-6 `force-full`） | `matrix_5fields.md`（`ini` 行） |
| 回滚路径（P-1/P-2/P-3/P-6） | 回滚 hex == 原字节 hex 逐字节比对；卸载函数/时序在两文档均出现 | `matrix_5fields.md` + `M:376-409` vs `net_fix:581-596` / `gap_spysat:91-99,178-184,302-308` / `particle:324-330` / `l4:261-265` |
| 红线类一致性 | 禁写 `.detour`、`IsShrouded`/`Compute_Frame_CRC`/RNG 不碰、`0xB04474` 不被镜像写、`0x48D000` 禁挂钩 —— 两文档均明文 | `net_fix:121-130,610-620` / `particle:336-362` / `gap_spysat:344-348` / `M:18-27,271-272` |
| 环境一致性 | `gamemd.exe` MD5 与总表钉值一致；两份 ini 字节相同 | `env_facts.json` |

---

## 6. 阻塞、风险与建议次序

- **阻塞**：无（本任务纯静态，全部结论可由上述脚本复算）。
- **待实测（本任务不可判）**：各包 `[待实测]` 条目与总表 `TC-ST-01…TC-ST-06`（`M:417-424`）全部需要真机：三条修正的**行为面**（H-D5 镜像环越界、音频早退栈平衡、跳板分配失败路径）均只完成静态/编码级证明。
- **建议裁定次序**（低成本 → 高成本）：
  1. **字段级勘误**（改字即可）：F-01 / F-02 / F-03 / F-04 / F-08 / F-11 / F-12 / F-13。
  2. **策略级收口**（需 Lead 定调）：F-07（失败即放弃 vs 重定位的边界）、F-05（P-4/P-5 槽位分配 + rel32 填实）。
  3. **跨链补齐**（连接 MP 裁决链与执行链）：F-09 / F-10。
  4. **F-06**（CRT 头尺寸）建议与 F-05 同批处理（同属 P-4 实现面）。
- **风险提示**：12 格冲突中 10 格来自 `landing_pack_crt_audio_particle.md` 的历史草案。建议**以勘误/附录方式**对齐（而非重写正文），保留"草案 → 定谳"的可追溯痕迹，符合本项目 `[实证]/[纠偏]` 惯例。

---

## 附录 A · 写入被审两份文档的「最小勘误标记」

按授权仅做**标记**（不动正文）。两份文档末尾各追加一节，**正文前缀逐字节未改**（`总长 = 原长 + 追加长` 已校，且前缀逐字节相等）`[实证]`：

- **E-1** → `docs/re/hook_gate_gap_table.md` **§8 附录 · 勘误标记（收尾-C / task-13，2026-09-26）**（起于第 255 行；原文件 254 行）：`G-01…G-10` 的「正文现状行号 → 终局裁决口径 → 权威落点」标记表 + 三条附注（① G-01 两方证据勘误：ini 现值实测 1 @ `:45`，非 0 @ `:44`；② §6「ini 键全表」需按 atlas §9.4 补键名与默认值；③ 所有「建议/或/二选一」措辞归零）。
- **E-2** → `docs/re/MP_SAFETY_REVIEW.md` **§8 附录 · 勘误标记（收尾-C / task-13，2026-09-26）**（起于第 442 行，原文件 438 行）：本文 §4.2/§5/§6 各条目 → 终局裁决的收敛映射表（§4.2 `L363`、§5 `L399-404`、§2.5 `L162-174`、§6.2 `L411`、§4.4 `L390`）+ 两条附注；并**声明 §0 判定、§3.1 `>>4` 推导、§4.1「一行止血」结论维持不变**。

两份文档正文（含 `hook_gate_gap_table.md` §5 四列缺口表、`MP_SAFETY_REVIEW.md` §5/§6 与台账草稿）**逐字未改**；勘误只登记差异、不覆盖原判断。G-07/G-09 的专项结论与依据见本文 §2.3。

## 附录 B · 产物清单

| 路径 | 说明 |
|---|---|
| `docs/re/mp_landing_consistency.md` | 本报告 |
| `out/re_work/mp_landing/claims_orig_bytes.txt` | 32 条字节断言输入 |
| `out/re_work/mp_landing/audit_orig_bytes.json` | 字节断言结果（31 OK / 1 预期 NOREAD） |
| `out/re_work/mp_landing/rel32_verify.json` | 原指令反汇编 + 6 处 `E9` 落点重算 |
| `out/re_work/mp_landing/env_facts.json` | PE 节表 / MD5 / VA→偏移 / ini 一致性 / cave 无重叠 |
| `out/re_work/mp_landing/matrix_raw.json` | 18 项 × 5 字段 × 2 文档的机械比对原始结果（含行号） |
| `out/re_work/mp_landing/matrix_5fields.md` | 上述结果的可读矩阵 |
| `out/re_work/mp_landing/known_fixes.json` | 三条已知修正落表核查 + 编码学复核 |
| `out/re_work/mp_landing/{verify_env,verify_rel32,compare_landing_packs,emit_matrix_md,check_known_fixes}.py` | 可复算脚本 |

---

## 7. F-01…F-13 处置状态表（修复包 / task-14 · 2026-09-26）

> **修复包性质**：依据 Lead `[v1.5.37]` 裁定，对六个落地包 + 执行总表做**最小就地订正 + 勘误标记**；每处改动均在原位附「**【F-0x 订正 · 2026-09-26 · task-14】** 改前 → 改后 + 依据 + 标注」，**原文与新文对照保留**，未做整体重写。
> **写作用域**：`pending_execution_master_table.md` / `landing_pack_net_fix.md` / `landing_pack_particle.md` / `landing_pack_crt_audio_particle.md` / `landing_pack_gap_spysat.md` / `l4_vision_dirty_final_spec.md` / 本文 / `out/re_work/fixpack/**`。**未改** `ra2render/**`、顶层台账 `REVERSE_ENGINEERING_AND_PATCHES.md`、`hook_gate_gap_table.md`、`MP_SAFETY_REVIEW.md`、`anchor_claims.txt`。
> **汇总口径**：**13/13 已订正**；**0 条标 `[待执行方计算]`**（F-05 的 rel32 与跳板字节已全部算实并机读复核）；**0 条无法订正**。余下唯一「执行方义务」是 **F-05 的 4 个助手函数体**（签名/返回语义已定死，标 `[待执行方实现]`）与 **P-M3 范围守卫**（总表 §2.4.2 已有规格）。

| 编号 | 严重度 | 状态 | 订正位置（改后行号 / 节） | 改前 → 改后 | 依据 |
|:---:|:---:|:---|:---|:---|:---|
| **F-01** | 高 | ✅ 已订正（3 处） | `C:173`（PlayAt 足迹）／`C:206`／`C:291` | **6B `A0 AC 64 84 00 53` → 5B `A0 AC 64 84 00`**（含「原版指令（6 字节）」标注、`s_origPlayAtBytes[6]`、回滚 hex） | `gamemd.exe` 机读：`0x007509E0 = A0 AC 64 84 00`（5B），第 6 字节 `53` 是**下一条** `push ebx`；`anchor_claims.txt:78` = `A0 AC 64 84 00 53 84 C0` `[实证]` |
| **F-02** | 高 | ✅ 已订正（1 处） | `C:154` | `[System] EnableMemoryPool=1`（默认 1）→ **`=0`（默认 0 + 启动期单次锁定、严禁局内热切）** | 执行总表 `M:49,301,322` 默认 `0` + §〇.4「启动期锁定，否则跨堆释放触发 `0xC0000374`」 `[推演 + 实证]` |
| **F-03** | 高 | ✅ 已订正（2 处） | `C:431`／`C:337` | `EnableParticleFog=1`（默认 1）→ **`=0`（默认 0，验收显式置 1）**；代码默认 `g_enableParticleFog = true → false` | 主包 `P:55,287,298,379,393` 与总表 `M:47,297,324` 一致为 0；主包验收断言以「默认 0」为前提 `[实证]` |
| **F-04** | 中 | ✅ 已订正（9 处） | `P:64`（列头）／`P:66`／`P:67`／`P:76`（勘误块） | `00 62 CE C0`/`00 62 E2 80`（BE 书写）→ **`C0 CE 62 00`/`80 E2 62 00`（LE）**；对照 5 行（Bullet/Unit/Inf/Air/Bld）保留 BE 但**显式标注（BE 书写）** | `gamemd.exe` 机读 `0x007EFA68 = C0 CE 62 00`、`0x007EFCB0 = 80 E2 62 00`；`anchor_claims.txt:72-73` `[实证]`；BE 照抄会写入 `0xC0CE6200`（错误入口） |
| **F-05** | 高 | ✅ 已订正（真实字节，**无占位符**） | `M:51`／`M:52`／`M:53`／`M:54`（总表 4 行新字节）；`M:240`、`M:316`（字节级节）；`M:73`（cave 布局）；`C:451`（覆盖包执行表） | `E9 rel32 90` / `E9 rel32 90 90 90 90` / `E9 rel32 90` / `E9 rel32` → **`E9 24 73 33 01 90`（→`0x01B00140`）/ `E9 3E 76 33 01 90 90 90 90`（→`0x01B00180`）/ `E9 9B F8 3A 01 90`（→`0x01B001C0`）/ `E9 5B F8 3A 01`（→`0x01B00240`）**；补 4 跳板槽 + `RetZeroStub`(`0x01B00204`) + 4 助手指针槽(`0x01B00510/514/518/51C`)，避让 `0x01B00200` NoopArea | `out/re_work/fixpack/gen_p45_tramp.py` → `p45_tramp_bytes.txt`：原字节 4/4 MATCH、槽位零重叠、capstone 落点校验全 OK `[实证]`；助手**函数体**（`P4_New` 等）属落地实现侧，签名字节面已定（`uint32_t __cdecl`，返回 0 = 直通） |
| **F-06** | 中 | ✅ 已订正（6 处） | `C:47`（`pack(8)` + `poolIdx` 独立字段）／`C:56`／`C:75`／`C:83`／`C:136`；`C:533` §六登记 | 4B Tag（`0xA5A50000 | poolIdx`）+ `pack(4)` + `(elemSize+3)&~3` → **8B 头（`magic=0xA5A55A5A` + `poolIdx` 独立字段）+ `pack(8)` + `(elemSize+7)&~7` + 返回 `pBlock+8` + 回收投毒 `0xDEADBEEF`** | 总表 §2.4.2 P-M1/P-M2（`M:186-196`）与 `TC-ST-04` 一票否决「头部为 4 字节 → FAIL」（`M:422`）`[实证 + 推演]`；原 4B 方案与同一总表内部冲突 |
| **F-07** | 高 | ✅ 已订正（8 处） | `N:16`（:16 一句话使用法）／`N:28`（解包后代码注释）／`N:640`（执行表抬头）／`N:645`（步骤 0 验收列）／`N:713`（附录 C 抬头 + 三前置）／`:749` 伪码；`M:22`（§〇.2 总则红线） | 「失败则走附录 C 重定位」→ **「失败 → 该项不安装（跳过 + 红字日志 + 遥测计数），严禁带病写入」**；附录 C **降为离线预备**，启用须三前置同时满足（① 整表 rel32 重算 ② 装后 5 处 `E9` 自检 ③ 槽可执行） | Lead [v1.5.37] 硬要求；`z3_troubleshoot_net_fix_gap.md:25,37-44`；顶层台账 `REVERSE_ENGINEERING_AND_PATCHES.md:1183` `[推演]` |
| **F-08** | 中 | ✅ 已订正（1 处） | `P:121` | `.detour` 节 `VA=0x00793000`（RVA 当 VA）→ **`VA 0x00B93000`（RVA `0x793000`）+ RawPtr/RawSize** | PE 节表实测 `.detour` VA `0x00B93000`/RVA `0x00793000`；`tools/verify_anchors.py` 基线审计行「签名 @ VA 0xb93000」`[实证]` |
| **F-09** | 中 | ✅ 已订正（2 处：6 键 + 4 行） | `M:424`…`M:436`（[Logic]/[Multiplayer] 块）；`M:454`…（覆盖表 4 行）；`M:439` | §3.1 仅 P-1…P-6 新键（6 个 MP 键 **0 命中**）→ **补 `EnableMinimapFog` / `TargetScanKey` / `TargetScanInterval` / `EnableThreatRetention` / `MpStateWrites` / `MpAutoDowngrade`（+ 逃生舱 `ForceSinglePlayer`）**；覆盖规则表 6 行 → **10 行** | 键名/默认值以 `ARCHITECTURE_ATLAS.md` §9.4 `L1536-1543` + `mp_release_safety_checklist.md` §一 R-01…R-04 / §三 MP-G01…MP-G10 为唯一口径 `[实证]` |
| **F-10** | 中 | ✅ 已订正（1 处） | `M:442` | `MpActive()`（`0x00A8ED84` 处于对局网络循环）→ **`(*(uint8_t*)0x00A8D5F8 & 0x02) != 0`（bit1）**，辅助 `*(int32_t*)0x00AA0444 == 2`；并注明 `0x00A8ED84` **实为 `CurrentFrame`** | `net_fix:68` 符号表 + `net_fix:399` H-D5 跳板反汇编 `A1 84 ED A8 00 mov eax,[0xA8ED84]`；`mp_release_safety_checklist.md:33-36`（`0x00647260` 原版 `A0 F8 D5 A8 00`）`[实证]` |
| **F-11** | 中 | ✅ 已订正（执行链；权威正文在写作用域外且已落） | `G:368`（§5 ini 增量 + G-01 口径注）；`M:404`（总表 §3.1） | 「API 默认 1 ≠ ini 现值 0」（旧证据）→ **「API 默认 1、**ini 现值 1**（`ra2render.ini:45`，`:44` 为注释）；缺口 = 键被删/安装包漏配即静默全开」** | 工作树两份 ini 现值均为 1、源码 `blitter_hooks.cpp:103` 默认仍 1 `[实证]`（`env_facts.json`）；**权威正文目标 `hook_gate_gap_table.md:38,129` 不在本任务写作用域**，task-13 已在同文 §8 附录 **E-1**（`L263,276-277`）落同口径勘误 → 本次只补**执行链**（总表 §3.1 + 本包落地侧注） |
| **F-12** | 低 | ✅ 已订正（5 行） | `M:83`…`M:87`（cave 布局） | 布局仅到 `+0x40C` 开关（**无 `+0x410`…`+0x420`**）→ 补 `g_syncEarlyLogCount` / `g_syncSnapshotsWritten` / `g_syncSnapshotFail` / `g_syncMirrorFrames`(`0x01B0041C`) / `g_syncCmdMirrorCount` | H-D5 跳板实际写 `0x01B0041C`（`net_fix:417,648` 连写 hex `FF 05 1C 04 B0 01`）而总表未声明 → 按旧布局执行会与 P-1 写入点冲突 `[实证]` |
| **F-13** | 低-中 | ✅ 已订正（2 处） | `M:532`（§4.1 增行）／`L:267`（§五.2 增行） | §4.1 逐字节还原表 16 行**无 G-07** → 补「G-07 TYPE 4 字段（`SW+0xB0/+0xF8`、`Bld+0x16A5/+0x16F0`，动态地址）| 首次写前实读值 | `RestoreSpySatBuildingTypes()`」；`l4` §五.2 仅「热回滚」→ **补硬卸载还原行**（写回 `0F 8D 98 00 00 00`） | `landing_pack_gap_spysat.md:261-279,385` 已给还原规格与调用顺序 `[实证]` → 属总表自身不完整（非两方冲突） |

### 7.1 未落在写作用域内的两条（已登记，非本次改动）

| 编号 | 目标文件 | 处置 |
|:---:|---|---|
| **F-11** | `docs/re/hook_gate_gap_table.md:38,129` | **不在写作用域**；同口径勘误已由 task-13 落在该文 §8 附录 **E-1**（`L263`、`L276-277`）→ 本次只做**执行链补齐**（`pending_execution_master_table.md` §3.1 增 `EnableMinimapFog=0`、`landing_pack_gap_spysat.md` §5 增键与口径注，见 §7 表 F-11 行） |
| **F-05（助手实现面）** | 落地源码 `ra2memorypool.cpp` / `ra2audio.cpp`（`ra2render/**`，**禁改**） | 助手指针槽、签名（`uint32_t __cdecl`，`0` = 直通）、缺省值（`RetZeroStub`）与 ABI 已定死于 `M:§2.4.3/§2.5.3` 与 `C:§五.4`；**函数体**由落地实现方按总表 §2.4.2 P-M1…P-M5 与 §2.5.2 削峰规则实现 `[待执行方实现]` |

### 7.2 自证（改后立即复跑）

```
python tools/verify_anchors.py
#   → 断言总数 323 条 | PASS: 323 (100.00%) | FAIL: 0 | NOREAD: 0  [100% ALL PASS]
python tools/audit_bytes.py docs/re/anchor_claims.txt
#   → 合计 323 条：OK=323  MISMATCH/NOREAD=0
python out/re_work/fixpack/gen_p45_tramp.py
#   → [自检] 原字节全 MATCH: PASS / [自检] 槽位零重叠: PASS
```

> 产物：`out/re_work/fixpack/{gen_p45_tramp.py,p45_tramp_bytes.txt,p45_tramp_bytes.json,fixpack_diff_F01-F13.md,FIXPACK_F01-F13_report.md,verify_output.txt}`。
