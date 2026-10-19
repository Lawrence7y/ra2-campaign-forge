# W3_20261001 · Lead 裁决备忘录 + 派工总表（承接 W2_20261001）

> **2026-10-02 用户确认的项目方向**：后续目标、优先级和新任务卡字段以 [PROJECT_DIRECTION.md](../../PROJECT_DIRECTION.md) 为准：性能与稳定性、关键系统安全修改、DLC 框架与工具，持续定向逆向。下文 W3 裁决、证据和既有任务保留；技术门禁与写域纪律继续有效。当前审计先按最新记录收尾，再进入新的 P1 三线队列。

> 出单：DeepSeek Harness 调度台（Lead 会话）　基线时点：W2_20261001 收工态
> 本文件是 W3 三个 harness（ZCode / Antigravity / Qoder CN）的**共同权威输入**。凡与本文冲突的旧口径，以本文为准；本文未覆盖处一律沿用旧口径。
> **裁决性质声明**：§2 的 8 条裁决由 Lead 依 `out/re_work/qc/W2_20261001/keys/decision_cards.md` 各卡的"本包推荐"落槌，性质为**临时裁决（provisional）**，用于解除排期死锁；用户书面否决即回滚。凡据临时裁决改动文档处，必须在改动点标注 `[W3-Lead临时裁决]`。

---

## 1. 进度基线（W2 收工态，Lead 复核）

| 维度 | 事实 | 口径 |
|---|---|---|
| 主目标二进制 | `ra2youli/gamemd.exe` = `ra2bench/gamemd.exe`，sha256 `73201cc0…`，MD5 `4f37486e5b0dbe2ae5f45aeee0f98367`，ImageBase `0x400000`，`.text` VA `0x401000`，FileOffset = VA − 0x400000 | `[实证]` |
> 【W3-Lead勘误 E-W3-01】改前：FileOffset = VA − 0x400000；改后：FileOffset = 段.PointerToRawData + (VA − 段.VirtualAddress)（本镜像 .text/.rdata/.data 为 VA − 0x400000，但 .rsrc/.detour 为 VA − 0x6FC000）；依据：out/re_work/_lead_baseline/W3/LEAD_ERRATUM_E-W3-01_fileoffset_rule.md；分级：[实证]
| 原版二进制 | `ra2youli/game.exe` = `ra2bench/game.exe` = `D:\Red2\ra2youli\game.exe`，sha256 `c4bf2a57a80f…`，4,497,680 B，`.text` raw 3,772,416 B，RTTI 977 类；**均为 StreamHook 注入版**（多 `.detour` 节） | `[实证]`，纯度仅 `[推演]` |
| 断言覆盖率 | A（ATLAS 唯一 VA 覆盖）1249/1731 = **72.15%**；并入 QC4 154 条 = **80.42%**（若采纳） | 分母定义见 `out/re_work/qc/W2_20261001/scope/DENOMINATORS.md` |
| 定名率 | B 104/988 = **10.53%**；B2 90/350 = **25.71%** | 同上 |
| 函数级 | C2 340/6719 = **5.06%** | 同上 |
| 字节级 | C1 12451/4,063,232 = **0.31%**（**不含语义**） | 同上 |
| 原版侧 | A_game 分子 = **0**；931/931 同名类 vtable RVA **全不同** ⇒ 必须另建整套 VA 账 | `[实证]` |
| 代码轨 | `ra2render.dll` 三处同步 = `626f98b6…`；P-2.x/VCX/SW 三补丁层已落地并真机 A1/A2/A3/A5 验收 | `out/re_work/zcode_live/MASTER_STATUS.md` |
| 未落地字节包 | P-3 粒子双槽 / P-4 CRT 池 / P-5 音频（cave 零重叠，407 条自检全 PASS） | `out/re_work/qc/W2_20261001/static_prep/**` |
| 决策卡 | DC-01…DC-08 **8/8 `待裁`** | `keys/decision_cards.md` |

### 1.1 W3 要打的七个缺口

1. **原版 `game.exe` 侧零建账**（分母翻倍的工作量级阻断）——`scope/NEXT_BATCH.md` B-0…B-7；
2. **ATLAS 悬空 339 条** 未补证（§2 68 / §5 42 / §1 40 …）+ **78 条未命名指令锚点**；
3. **QC1/QC2/QC4 勘误块全部"待采纳"**，未落入 `docs/re/**` 正文；
4. **P-3/P-4/P-5 未落地**，且前置有 5 条"落地即错"缺陷（B-1…B-5）；
5. **15 条未实现键**（其中 11 条连要门控的补丁都 0 引用）；
6. **真机未闭环**：VXL 热路径计数器 / SW 到点帧号对拍 / MP ≥5000 帧 CRC 对拍 / A4 存读档替代路径 / 会话静默退出根因 / `vision-dirty`+`vanilla` 档 / H1 U0800 塌方；
7. **B-6 ini 三键半落地**（源 23 键 vs 游戏目录 20 键 ⇒ 代码在、开关缺 ⇒ 实际全关）。

---

## 2. Lead 临时裁决（DC-01…DC-08）

| 卡 | 裁决 | 依据（可实测维度） | 回写目标 |
|---|---|---|---|
| **DC-01** 池化节名 | **甲 `[System]`** | `[System]` 已存在于三 ini 且被 `blitter_hooks.cpp:541,544` 实际读取 ⇒ 零新增节、零补 ini | 只改 `crt_pool_landing.md:19` |
| **DC-02** 音频键集 | **乙 8 键 `[AudioThrottle]` + 宿主仍 `ra2render.ini`** | 乙是唯一与既有三钩判定序自洽的方案；宿主改独立文件需改读取器基建（`blitter_hooks.cpp:519-521`），不随键口径顺带批准 | `pending_execution_master_table.md:415-419` + `execution_runbook.md:367-368` |
| **DC-03** 音频默认与单位 | **默认 `0` + 单位取「帧」，键名带 `_frames`** | 默认 0 = 键缺失即原版（安全侧）；帧钟利于回放稳定 | `pending_execution_master_table.md:417,419` |
| **DC-04** `PoolBlockCount` | **丙 保持未定**（不入冻结面，P-4 的 `EnableMemoryPool` 可单独按 0 冻结） | 甲/乙均无文本依据，仅数量级直觉 | `crt_pool_landing.md` §3 补定义 + 总表 `:413` |
| **DC-05** MP 四键 | **乙 全部 `[Logic]` + 极性统一为 `Enable*=1 表示启用该行为`**；`MpStateWrites` 仍成键（不采丙） | `[Logic]` 三 ini 均已存在且被 `:531/:561/:624` 实读 ⇒ 零新增节、零补 ini | 总表 `:432-440` + `mp_autodowngrade_spec.md:401-412` + `ARCHITECTURE_ATLAS.md:2193,2195` |
| **DC-06** `EnableSpySatGate` | **默认 `0` + MP 语义保持总表「强一致」**（**不**加 forced-off-mp） | 默认 0 属可实测安全侧；"联机不装"是新增产品行为，不随口径统一顺带做出 | 总表 `:402,453` 或 `landing_pack_gap_spysat.md:158-159` |
| **DC-07** G-R1 握手 | **折中 C4**：开发期采**甲**（不加任何协议字段，文档级禁混端）；**发布门（G4.1/G4.2）前**由用户书面二选一。同时：`blitter_hooks.cpp:814-816` 的「[v1.8.35] 裁决：不采纳握手校验」字样**降级为「待裁」口径**，须给出该裁决的书面来源；给不出即订正为待裁 | 现网代码 = 事实上的甲但**无签字依据**；代码内部对"握手期望值"表述自相矛盾（`:940`） | `g_r1_decision_card.md:24-26,49-53` + `blitter_hooks.cpp:814-816`（代码侧由 ZCode 改） |
| **DC-08** 裂缝 MP 语义 vs P0 遥测 | **丙 分档判据**（`MpActive ⇒ 恒 0；单机且显式 =1 ⇒ 3`） | 行为零变化（代码 `:3321-3323` 已如此），只消解「P0 判据恒为假」；不跨写域、不新增协议字段 | 总表 `:44,451,502` |

> **DC-04 的后果**：`PoolBlockCount` 键**不得**出现在任何冻结/落地清单；P-4 落地只做 `EnableMemoryPool`（默认 0）。
> **DC-07 的后果**：W3 内不得实施握手协议字段；只允许文档口径归一 + 代码注释订正。

---

## 3. W3 派工总表（写域互斥，禁重叠）

| # | Host / 模型 | 包 | 写域（越界即不合格） | 依赖 |
|---|---|---|---|---|
| W3-Q1 | **Qoder CN** / Qwen3.8-Flash | **原版建账最小可交付**：B-0 基线冻结 + B-1 RTTI 全量入库 + B-7 exclusions | `out/re_work/qc/W3_20261001/**` | 无 |
| W3-Q2 | 同上 | **B-2** 153 类 vtable 槽数逐类重数（4 片并行） | 同上 | W3-Q1 |
| W3-Q3 | 同上 | **ATLAS 悬空补齐**：§2 68 + §5 42 + §1 40 + 78 未命名指令锚点 | 同上 | 无（只读 atlas） |
| W3-Q4 | 同上 | **B-3/B-4/B-6**：atlas_game 骨架 + vamap + yuri_only | 同上 | W3-Q1/W3-Q2 |
| W3-Q5 | 同上 | **B-5** 第二血缘（NSIS 沙箱提取，只读源 / 只写沙箱） | 同上 + `_extract_sandbox/` | 无 |
| W3-A1 | **Antigravity** / Gemini-3.8-Flash-High | **docs/re 勘误落地**：QC1 17 块 + QC2 16 处 + forge 4 处 | `docs/re/**`（指定文件） | 无 |
| W3-A2 | 同上 | **ARCHITECTURE_ATLAS.md 本体**：QC4 五章 154 条 + 11 条 BSS 降级改写 | `docs/re/ARCHITECTURE_ATLAS.md` | 无 |
| W3-A3 | 同上 | **独立第二方法复验**：门禁复跑 + 977/988/964 第二算法 + LZO 最小例 + ECHGAP 8 节 | `out/re_work/agy/W3_20261001/**` | 无 |
| W3-A4 | 同上 | **原版 `.detour` 注入不改代码** 的独立复核（与 Qoder 方法不同） | 同上 | 无 |
| W3-Z1 | **ZCode** / GLM-5.3-Flash → step-5-preview | **B-6 ini 三键闭环** + 三键生效真机验证 + 字节级还原证据 | `ra2render/ra2render.ini`、`ra2bench/ra2render.ini`、`ra2youli/ra2render.ini`、`out/re_work/zcode_live/W3_20261001/**` | 无 |
| W3-Z2 | 同上 | **`session_stability` 出 RESULT**（该目录现无 RESULT） | `out/re_work/zcode_live/W3_20261001/**` | 无 |
| W3-Z3 | 同上 | **A4 存读档替代路径**（绕描述框，要求有效 MAD≈0） | 同上 | 无 |
| W3-Z4 | 同上 | （**额度允许才做**）P-3/P-4/P-5 落地，吸收 B-1…B-5 勘误后**串行** CRT→AUDIO→PART | `ra2render/**` | W3-A1（勘误落地）+ §2 裁决 |

**串行红线（全局）**
- `ra2render/**` 唯一写者 = **ZCode**；任何其他 host 一律只提交规格。
- `docs/re/**` W3 唯一写者 = **Antigravity**；Qoder 的勘误一律以可审查文本块交 Antigravity 落盘。
- `gamemd.exe` / `game.exe` 两目录 + `D:\Red2\**` + `YRpp/**` **全程只读**，前后 sha256 对拍须贴原文。
- 同一 VA 点位安装串行；`vision-dirty` 档在 P1+P2+P4 全绿前不得开。
- 游戏目录任何改动（ini/BATTLEMD/地图/.sav）**先备份、后字节级还原**，并留 before/after sha256。

---

## 4. 证据与回报纪律（全员强制）

- 证据三档：`[实证]`（VA + FileOffset + 原始字节 + Capstone + xref）/ `[推演]` / `[待实测]`；**不得把推测写成结论**。
- 回报**必须**按 `docs/re/AGENT_DELIVERY_FORMAT.md §A` 的 10 节骨架逐节填写，缺节即不合格。
- 派工任务卡前缀模板见 `docs/re/AGENT_TASK_TEMPLATE.md`。
- 门禁必跑并**原文粘贴**：`python tools\verify_anchors.py`（须 323/323 PASS）、`python tools\audit_bytes.py <claims.txt>`（须全 OK）。
- **若本机 shell 起不来**（例如 `pwsh` 报 `0xC0000142` / `STATUS_DLL_INIT_FAILED`）：如实记录并在回报 `[6]` 节写明，改用 `python` 直调或 `cmd /c`，**不得静默跳过门禁**。
- 崩溃零容忍 / 伪造零容忍 / 零生效禁止放行：见 `docs/re/EVIDENCE_STANDARD.md` v3。

---

## 5. 【W3 追加 · Lead 独立发现，全员必读】`gamemd.exe` 基线的真实血缘

> 全文与可重放命令：`out/re_work/_lead_baseline/W3/LEAD_FINDING_gamemd_lineage.md`

Lead 亲跑复算（触发源：Antigravity W3-A4 的独立普查）：

1. **项目主基线 `73201cc0…` 不等于出厂原版**。出厂件哈希 = **`DB264305C8A6963D17F5D189…`**，本机有两份：`ra2youli\.ra2opt\orig\gamemd.exe`（`ra2opt` 的 `apply perf` 前备份）与 `D:\Red2\ra2youli\gamemd.exe`。
2. **差异仅 2 个 PE 头字节，不落在任何节内**：`file 0xAE` = `DllCharacteristics`（`0x0000 → 0x0020`，置 `NX_COMPAT`）；`file 0xB0..B3` = `SizeOfStackReserve`（`1 MB → 4 MB`）。`e_lfanew=0x50`，COFF `Characteristics` 两份同为 `0x032F`（LAA 位本已置）。
3. **⇒ 全部节（`.text/.rdata/.data/.rsrc/.detour`）逐字节相同 ⇒ 既有语料、`verify_anchors` 323 条、一切 claims 字节断言与 `audit_bytes` 结论继续有效，无需重算。**
4. **但口径须订正**：`MASTER_STATUS.md:4` 的「只读基线」含义是"每轮作业期间不被改写"，**不是**"等于出厂件"。任何人引用"原版/出厂"时必须写明是 `DB264305…` 还是 `73201cc0…`，否则会误判语料被污染。
5. **`game.exe` 侧第二血缘问题不变**：三份 `C4BF2A57A80FF8D1AA9FBC77…` 同哈希、本机无未注入对照件 ⇒ `NEXT_BATCH` B-5（NSIS 沙箱提取）仍是唯一路径。
6. **对 W3-Q1（B-0 基线冻结）的追加要求**：基线普查必须**枚举全机全部副本并给出哈希**（含 `.ra2opt/orig`、`D:\Red2`、`ra2bench`、`out/forge2_verify/**`），并把"出厂件 vs 项目基线"两列分列；不得只登记 `ra2youli` 一份。
7. **对 W3-A6（文档 vs 实况审计）的追加检查项**：凡文档出现"原版/出厂/gamemd.exe 基线"处，核其指向的是哪个哈希。

**Lead 本轮基线副本**（开工态，供事后独立校验）：
`out/re_work/_lead_baseline/W3/ra2youli_ra2render.ini.baseline`（`B8BB8238E5BD06E132FAFB72…`）、`ra2bench_ra2render.ini.baseline`（同）、`src_ra2render.ini.baseline`（`FD9EBB32DCB6CDA7952381BA…`）。
