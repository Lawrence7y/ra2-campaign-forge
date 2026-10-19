# 双轨状态说明 · R-DUALTRACK

> **任务号**：`R-DUALTRACK` · **性质**：状态口径 / 命名纪律（非规格变更、非落地动作）  
> **写作用域**：本文 + `out/re_work/re_sprint/R_dualtrack/**`  
> **禁写**：台账 `REVERSE_ENGINEERING_AND_PATCHES.md`、看板 `RE_COORDINATION.md`、`landing_pack_*` 本体、`ra2render/**`、`out/re_work/zcode_live/**`、`gamemd.exe` / `ra2youli/**`  
> **上游只读**：`docs/re/zcode_parallel_prompt_v3.md` · `docs/re/TRACK_BOUNDARY_MIMO_RE.md` · `docs/re/landing_pack_inventory.md` · `out/re_work/re_sprint/R_card_inv/cards_inventory.json` · `docs/re/preflight_e1_e4_corrections.md` E-3 · `docs/re/errata_sync_master_table.md`  
> **一句话**：同一件事在**两套轨**上各有独立落地状态；写状态、报进度、引证据时**必须带轨名**，禁止用「已落地 / 未落地」单轨含混表述。

---

## 0. 为什么要有本说明

已发生的真实混淆（E-3 / cards_inventory 对照）：

| 事实 | 哪里看 | 易误读成 |
|---|---|---|
| `ZC-GAP-P21` / `ZC-GAP-P223` 收据在 **zcode_live 二进制轨**（状态：**已落地**） | `out/re_work/zcode_live/gap_p21/RESULT_GAP_P21.md`、`gap_p223/RESULT_GAP_P223.md` | 「Gap 三点 NOP 代码里已经写了」 |
| 同三点在 **ra2render 代码轨** 当前 **0 命中**（状态：**未落地**） | 全源码 grep `568273/577EC5/577B60` 无命中（`ARCHITECTURE_ATLAS_REV` §20.6） | 「二进制装了 = 代码落了」 |

两轨状态**可以同时为真且互相独立**。`landing_pack_inventory.md` 与 `preflight_e1_e4_corrections.md` E-3 已明文：**两轨勿混淆**。本说明把定义、归属、核验、禁混称模板一次钉死。

---

## 1. 两轨定义

### 1.1 对照表

| 维 | **二进制轨**（Binary Track） | **代码轨**（Code Track） |
|---|---|---|
| **别名** | Track-L 落地安装轨 · `zcode_live` 轨 · 进程内补丁轨 | Track-R · `ra2render` 源码轨 · 注入实现轨 |
| **改什么** | **运行中 `gamemd.exe` 进程**（或其文件副本）的机器字节 / 虚表槽 / ini 开关 | **`ra2render/**` 源码**：Hook/跳板/开关解析/遥测/DETACH |
| **写者** | ZCode 真机子代理（安装/卸载唯一写者） | ZCode 代码子代理（**单写者、强制串行**）；无 Lead 授权则只交规格不写码 |
| **写作用域** | `out/re_work/zcode_live/**`（RESULT + evidence）· `ra2youli/ra2render.ini`（开关，须还原）· 各卡声明的安装工作区 | **仅** `ra2render/**`（及 `ra2youli/ra2render.*` 经授权） |
| **产物形态** | 进程内补丁 + `RESULT_*.md` 回执 + evidence 树（json/png/map/inibak/原字节备份） | `.h/.cpp/.ini` 源码变更 + 编译产物 + 启动/挂载日志 |
| **状态词（本项目已定）** | **已落地**（真机装上且有 RESULT）/ **就绪** / **待批**（`landing_pack_inventory.md` §1） | **已落地**（源码命中并编译生效）/ **未落地**（grep 0 命中或未进仓）/ **已勘误**（现码已用新值） |
| **并发** | 不同卡 / 不同 VA 点位可并行；**同一 VA 点位安装仍串行** | **同一时刻只允许一个写者**改 `ra2render`；禁止并行改同一文件 |
| **典型单卡主路径** | C 复算 → L 安装 → S 回执（**多数波次不动代码轨**） | 需要改源码的实现（三谓词合流、私有网格、遥测、开关解析）才进 R 轨 |

### 1.2 边界提醒（与 TRACK_BOUNDARY / v3 四轨一致）

- 二进制轨 ≠ 「随便改 `gamemd.exe` 文件」；安装动作按 landing_pack 字节契约执行，原字节备份 + 可回滚（G-R7）。
- 代码轨 ≠ 「文档里写了规格」；**纸面规格已定谳 ≠ 代码已写**（E-3 原文口径）。
- 复算审计轨（Track-C）与回执勘误轨（Track-S）是**核验/归档侧**，不改变上述两轨的落地状态。
- `ra2youli/**`、`ra2bench/**`、`gamemd.exe` 游戏文件默认只读；顶层台账仅 Lead 合并。

### 1.3 经典双状态样例（必读）

| 卡 | 纸面规格 | 二进制轨 | 代码轨 |
|---|---|---|---|
| `ZC-GAP-P21`（P-2.1 @ `0x568273` 6×NOP） | 已定谳（字节 17/17 PASS） | **已落地** `zcode_live/gap_p21/RESULT_GAP_P21.md` | **见 §2 注**（`InstallGapProtectionPatch` 与全源码 grep 口径须分列） |
| `ZC-GAP-P223`（P-2.2 `0x577EC5` / P-2.3 `0x577B60` 各 6×NOP） | 已定谳 | **已落地** `zcode_live/gap_p223/RESULT_GAP_P223.md` | **未落地**（grep `577EC5/577B60` 0 命中） |
> 【W3 勘误 · W3-A6/ISSUE-STALE-P2-LANDING】改前：P-2.2 `0x577EC5` / P-2.3 `0x577B60` 各 6×NOP） | 已定谳 | **已落地** `zcode_live/gap_p223/RESULT_GAP_P223.md` | **未落地；改后：P-2.1~P-2.3 裂缝三点 NOP 已于 09-30 完整落地进 blitter_hooks.cpp:3273-3287 并完成三处 DLL 同步；真机 A3 验收 PASS (带窗口限定)。；依据：ra2render/blitter_hooks.cpp:3273-3287, 3417-3446; out/re_work/zcode_live/gap_p21_a3/RESULT_GAP_P21_A3.md:18-23；分级：P0
| 总表 P-2.1～P-2.3 状态注记 | — | 收据并存于二进制轨 | E-3 要求增注「**ra2render 代码轨 0 命中（未落地）**」，防实施方误跳过写入 |

> 注：`p223_readiness_check.md` 另记「P-2.1 代码轨已落（`InstallGapProtectionPatch`）」——属**单点安装函数**已进代码轨，与「三点 NOP 常量 grep 命中」不是同一核验口径。报状态时必须写清核验口径（见 §3.2）。

---

## 2. 各卡归属

口径：`landing_pack_inventory.md` + `cards_inventory.json` + `zcode_parallel_prompt_v3.md` §2.1。  
轨列：**主轨** = 状态/收据记在哪条轨；**可触** = 本卡允许碰的轨。

### 2.1 v3 十卡队列（W1–W4）

| 波 | 卡号 | 主轨 | 可触 | 回执路径（约定后不换） | 备注 |
|---|---|---|---|---|---|
| W1 | `ZC-GAP-P21-A3` | **二进制轨**（行为验收，不改字节） | L+C | `R_p21_a3/**` + `zcode_live/gap_p21_a3/` | 备选方案 H-诊断钩若进 `ra2render` 才升代码轨，且须 Lead 书面授权 |
| W1 | `ZC-GAP-P223` | **二进制轨** | L+C | `R_gap_p223/**` | 与代码轨 0 命中并存；报「已落地」必须带「二进制轨」 |
| W1 | `ZC-VXL-PRE` | **二进制轨** | L+C | `R_vxl_card/**` | L-VXL-1 `0x706D78` imm8；默认开关 0 |
| W2 | `ZC-H20C-SWEEP` | **双轨**（L+C+R） | L+C+**R** | `R_h20c_card/**` | 三谓词合流 / 私有网格进 `ra2render` → **代码轨串行单写者** |
| W2 | `ZC-SW-RADIUS-RC` | **二进制轨**（零 .text） | L+C | `R_swr_card/**` | 半径语义复活；依赖 H20C 私有字段（跨轨协调） |
| W2 | `ZC-AUDIO-THROT` | **二进制轨** | L+C | `R_audio_card/**` | AT-A/B/C trampoline |
| W2 | `ZC-PART-FOG` | **二进制轨** | L+C | `R_part_card/**` | 槽 69 两虚表 DWORD（LE） |
| W3 | `ZC-CRT-L1` | **二进制轨** | L+C | `R_crt_card/**` | 启动期锁；禁热切 |
| W3 | `ZC-WPN-LW` | **二进制轨** | L+C | `R_wpn_card/**` | L-W1 保序 0 PRNG |
| W4 | `ZC-SW-CHARGE` L-SW-1/2 | **二进制轨** | L+C | `R_sw_card/**` | L-SW-2 待批（Q2） |
| 全波 | `R-PROMPT-V3` 编排 | **Track-S**（回执/勘误） | S | `R_prompt_v3/wave_W<N>_result.md` | 不改任一轨字节/源码 |

### 2.2 既有/历史卡（防重复装、防轨混标）

| 卡号 | 主轨 | 二进制轨状态 | 代码轨状态 | 收据/依据 |
|---|---|---|---|---|
| `ZC-GAP-P21` | 二进制轨 | **已落地** | 见 §1.3 注 | `zcode_live/gap_p21/RESULT_GAP_P21.md` |
| `ZC-GAP-P223` | 二进制轨 | **已落地** | **未落地**（grep 0） | `zcode_live/gap_p223/RESULT_GAP_P223.md` |
| `R-GAP-MERGE` | 二进制轨（编排） | **已落地**（installed==3） | 依赖上述 | `R_gap_merge/` |
| `ZC-SW-CHARGE-L2` | 二进制轨 | 就绪·**待批** Q2 | — | `R_sw_card/` |
| `ZC-CRT-L2-C34` | 二进制轨 | 就绪·**待批** A/B | — | `R_l2_card/` |
| `ZC-HD-DIAG` / `M-8-NET-FIX` | 二进制轨 | 就绪 | 同面勿双装 | `R_hd_card/` / `landing_net_fix/` |
| `M-10-GAP-SPYSAT` | 二进制轨 | 就绪 | 门控另面 | `out/re_work/landing_gap/` |
| `M-9-PARTICLE` / `ZC-PART-FOG` | 二进制轨 | 就绪 | 已收敛单卡 | `R_part_card/` |
| `ZB1..ZB4` 验收 | **验收**（消费开关） | 依赖前序装毕 | 不装新补丁 | `R_b_merge/evidence/ZBx-M0X/` |
| `ZB5` 联机对拍 | **验收** | **待批** DUAL-LAN | 不装新补丁 | 同上 |
| `R-ZC-MASTER` / `R-PROMPT-V3` | 编排（S） | — | — | ticket / prompt v3 |
| `PREFLIGHT-AUDIT` | 审计 | n/a | n/a | E-1..E-4 须先订正 |

### 2.3 归属速判（写状态前先答）

1. 本卡产物落在 `out/re_work/zcode_live/**` 的 `RESULT_*.md`？→ **二进制轨**。  
2. 本卡改了 `ra2render/**` 且编译/挂载生效？→ **代码轨**。  
3. 两者都有？→ **双轨分列两行写**，禁止合并成「已落地」。  
4. 只有 landing_pack / 纸面规格？→ 写 **「纸面已定谳」**，两轨均不得标「已落地」。

---

## 3. 核验方法

### 3.1 二进制轨（zcode_live / 进程内补丁）

| # | 核验项 | 方法 | 通过判据 |
|---|---|---|---|
| B1 | 回执存在 | 读 `out/re_work/zcode_live/<卡或批次>/RESULT_*.md` | 有 RESULT 且卡号/VA/开关与 landing_pack 一致 |
| B2 | 原字节/替换字节 | `python tools/audit_bytes.py <claims.txt>` | MISMATCH/NOREAD=0；换前换后与卡内契约一致 |
| B3 | 锚点基线 | `python tools/verify_anchors.py` | **323/323**（共享基线；失败先停手上报） |
| B4 | 证据树齐 | `evidence/` 内原字节备份、回滚记录、开关 ini 备份 | 可回滚（G-R7）；gap 类逆序拆点 |
| B5 | 真机行为 | 卡内 `verify_*.py` / 硬证据（到点帧号、计数、截图） | 「没崩」**≠** 成功；A3 类须硬证据 |
| B6 | 开关默认 | 读 `ra2youli/ra2render.ini`（或部署 ini） | 默认 0 = 字节零变化；禁热切安装态开关 |

**状态词**：仅当 B1+B2+B5 满足时写 **「二进制轨已落地」**；否则写就绪/待批/失败，并写明缺哪门。

### 3.2 代码轨（ra2render 源码）

| # | 核验项 | 方法 | 通过判据 |
|---|---|---|---|
| C1 | 源码命中 | 对 `ra2render/**` grep **VA 去 0x 前缀 hex**（如 `568273` / `577EC5` / `577B60`）或符号/函数名 | **有命中**且语义为安装点（非注释/非日志字符串误报） |
| C2 | 安装函数 | 检索 `Install*Patch` / Hook 表 / DETACH 对称 | 安装与卸载成对；计数/回滚完整 |
| C3 | 头文件/ini/日志一致 | `ra2render.h` · `ra2render.ini` · `ra2youli/ra2render.log` | 同一 VA/LE 槽值三处一致（样例：R-E01 后均为 `0x56829A`） |
| C4 | 编译与挂载 | 构建 + 注入日志 | 日志出现对应虚表/跳板「挂载成功」行；失败即回退 |
| C5 | 勘误锚点 | `errata_sync_master_table.md` R-E01..R-E10 | 禁用旧 VA/旧长度（如 T-a 必须 7B） |
| C6 | 串行锁 | 写前确认无其他写者；一卡一提交 | 与文档轨订正不并行（N-11） |

**状态词**：C1+C2+C4 满足写 **「代码轨已落地」**；C1 = 0 命中写 **「代码轨未落地（grep 0 命中）」**；仅文档勘误后现码已用新值写 **「代码轨已勘误」**（≠ 功能已装）。

### 3.3 双轨对照（推荐回执节模板）

```text
[双轨状态]
纸面规格：已定谳 / 待定（依据：…）
二进制轨：已落地 | 就绪 | 待批 | n/a
  证据：out/re_work/zcode_live/.../RESULT_*.md（B1–B5）
代码轨：  已落地 | 未落地（grep 0 命中）| 已勘误 | n/a
  证据：ra2render grep「…」+ ra2render.h:line / log:line（C1–C4）
混称检查：未出现无轨名的「已落地」；未用二进制收据证明代码轨
```

### 3.4 快速命令（只读）

```text
# 二进制轨收据是否存在
rg -n "RESULT_" out/re_work/zcode_live --glob "RESULT_*.md"

# 代码轨是否命中三点 VA（0 命中 = 未落地）
rg -n "568273|577EC5|577B60" ra2render

# 字节复算 / 锚点基线
python tools/audit_bytes.py <claims.txt>
python tools/verify_anchors.py

# 卡归属机读表
# out/re_work/re_sprint/R_card_inv/cards_inventory.json
```

---

## 4. 禁混称模板

### 4.1 禁止的说法（❌）→ 合规改写（✅）

| # | ❌ 禁混称 | ✅ 合规模板 | 原因 |
|---|---|---|---|
| 1 | 「Gap 三点已落地」 | 「**二进制轨**已落地（`RESULT_GAP_P21/P223`）；**代码轨**未落地（grep `568273/577EC5/577B60` 0 命中）」 | 单轨含混；E-3 事故源 |
| 2 | 「代码里已经装了」（仅有 zcode_live RESULT） | 「zcode_live **进程内补丁**已装；`ra2render` **源码**尚未写入」 | 用二进制收据冒充代码轨 |
| 3 | 「ra2render 已落地」（仅有 landing_pack/规格） | 「**纸面规格已定谳**；代码轨 / 二进制轨均为「未落地」」 | 规格 ≠ 落地 |
| 4 | 「P-2 未落地」（不写轨） | 「P-2.x **代码轨**未落地；**二进制轨**见 `RESULT_…`」或反向 | 缺轨名 |
| 5 | 「已安装 / 可跳过」（因规格入库） | 「规格已入库；实施方**仍须写入**；PsychicReveal 仍清 `Cell+0x134`，缺口在」 | E-3 明确禁止跳过误导 |
| 6 | 「两轨都好了」/「全绿」 | 分列 B 行 + C 行，各自证据路径 | 禁止合并状态词 |
| 7 | 「代码轨已勘误 = 功能已上」 | 「代码轨**已勘误**（VA 新值）；功能落地以安装/挂载证据为准」 | 勘误 ≠ 安装 |
| 8 | 把 `InstallGapProtectionPatch` 命中说成「三点常量全在源码」 | 「安装函数已在代码轨；三点 NOP 常量 grep 口径另列」 | 核验口径混用 |

### 4.2 状态句骨架（可直接粘贴）

```text
【双轨状态 · <卡号>】
二进制轨（zcode_live）：<已落地|就绪|待批|n/a> · <RESULT 路径>
代码轨（ra2render）：<已落地|未落地（grep N 命中）|已勘误|n/a> · <grep/头文件/日志依据>
纸面规格：<已定谳|待定> · <landing_pack 路径>
禁止从另一轨推断本轨状态。
```

### 4.3 命名对照（同义词表，写作用域内任选其一但全文统一）

| 推荐主用 | 可接受别名 | 禁止单独使用（须带轨） |
|---|---|---|
| 二进制轨 | zcode_live 轨 · Track-L · 落地安装轨 · 进程内补丁 | 「已落地」「装好了」 |
| 代码轨 | ra2render 轨 · Track-R · 源码轨 · 注入实现 | 「已实现」「代码里有」 |
| 纸面规格 | landing_pack 规格 · 字节契约 | 「已支持」「已修复」 |

---

## 5. 本说明的合规边界

- **未改**任何 landing_pack 冻结源、台账、看板、`ra2render/**`、`zcode_live` 证据树。  
- 状态数字以 `cards_inventory.json`（28 行：已落地 3 / 就绪 20 / 待批 4 / n/a 1）与 `RESULT_*.md` 为准；后续波次变更只更新 **带轨名** 的状态行。  
- 与 `TRACK_BOUNDARY_MIMO_RE.md` 冲突时以该边界文件的写域为准；本说明只管**状态怎么写、如何核验、如何禁混称**。

*产物：本文 + `out/re_work/re_sprint/R_dualtrack/**`。*

---

## 6. 状态注记（追加节 · 2026-10-01 · 工单 `T-W1-Q / PK-1`）

> **只追加、不删改**：§1–§5 的轨道定义、禁混称模板、状态词表逐字保留。本节正是该模板的一次实例化使用。

### D-1 · 本文 §2 表第 2 行（代码轨「0 命中」）已过期 —— 三点 NOP 现**双轨同时为「已落地」**

- **改前逐字**（`:18`）：「同三点在 **ra2render 代码轨** 当前 **0 命中**（状态：**未落地**） | 全源码 grep `568273/577EC5/577B60` 无命中（`ARCHITECTURE_ATLAS_REV` §20.6） | 「二进制装了 = 代码落了」」
- **改后表述**：自 2026-09-30（ZC-GAP-P223 合入，构建 `626f98b6…`）起，**代码轨亦为「已落地」**：`568273/577EC5/577B60` 三个地址在 `ra2render/**` 均命中。本文把这一行留作**反面教材原样不删**，但引用本文时必须知道：该行只在 2026-09-30 之前为真。
- **实测依据**：`ra2render/ra2render.h:113,116,119`；`ra2render/blitter_hooks.cpp:3273-3287`（三点表 + 各点前/后邻窗 2/6/10B）、`:3313`、`:3402`、`:3417`、`:3736`；收据 `out/re_work/zcode_live/gap_p223/RESULT_GAP_P223.md:56-59`。
- **口径提醒**：双轨「已落地」**不等于**行为验收通过——A3/A4/A5 仍「初判无法判定」（同收据 `:60-62`），战役轨 `RESULT_GAP_P21_A3.md` 本轮实测仍不存在。按本文 §3 状态词表，正确写法是：
  `代码轨=已落地｜二进制轨=已落地（A1/A2/C4/C5）｜行为验收=未闭环（A3–A5，Track-C 进行中）`。
  > 【W3 勘误 · PATCH_SUGGESTIONS BLK-N4-1】改前：战役轨 `RESULT_GAP_P21_A3.md` 本轮实测仍不存在；改后：该文件在场（23,820 B / mtime 2026-10-01 13:11:34），判级换代为 A3=PASS（带窗口限定）、A4=未闭环、A5=部分（`RESULT_GAP_P223.md:60-62` 12:44 终判 + `RESULT_GAP_P21_A3.md:160` 终稿）；依据：`os.path.exists` + `stat` 实测；分级：[实证]

### D-2 · 本文 §5「状态数字以 cards_inventory.json 为准」一行需换代

- **改前逐字**（`:202`）：「状态数字以 `cards_inventory.json`（28 行：已落地 3 / 就绪 20 / 待批 4 / n/a 1）与 `RESULT_*.md` 为准；后续波次变更只更新 **带轨名** 的状态行。」
- **改后表述**：权威计数已换代为 **v2**：`out/re_work/re_sprint/R_inv_refresh/counts_summary.md:15-17,24-28` —— 卡片总行 **29**；二进制轨 **已落地 5 / 就绪 18 / 待批 4 / n/a 2**；代码轨 **已落地 5 / 已勘误 1 / 未落地 2（`ZC-H20C-SWEEP`、`ZC-SW-RADIUS-RC`）/ n/a 21**。
- **实测依据**：`R_inv_refresh/counts_summary.md` 本文件本轮已逐行复读确认；对应两张卡的代码轨 0 命中亦经本次 grep 复算（`RE_PROGRESS_SURVEY.md` §5.1）。
- **新增一条本文未预见的混称风险**：**部署件与 ini 也会「半落地」**——三处 `ra2render.dll` 已同步为最终构建 `626f98b6…`（本次 `sha256sum` 实测，含 `ra2youli`，故 `MASTER_STATUS.md:21` 的「待同步」已过期），但两游戏目录的 `ra2render.ini`（各 18412 B）**不含** `EnableGapProtection` / `EnableVxlCachePrewarm` / `EnableSWChargeOpt` 三键（本次 grep 0 命中）⇒ 代码在、开关缺 ⇒ **实际生效 = 全关**。报进度时这第三态应单列，不得写成「已落地」了事。

### D-3 · ★终判回填（2026-10-01 13:15 之后追加）—— 战役轨收口，D-1 的推荐写法需更新

D-1 给的写法 `代码轨=已落地｜二进制轨=已落地（A1/A2/C4/C5）｜行为验收=未闭环（A3–A5，Track-C 进行中）` 已被同日 T-Z1 收口刷新，现应写作：

```
代码轨=已落地 ｜ 二进制轨=已落地（A1/A2/C4/C5）｜ 行为验收=A3 PASS（带窗口限定）/ A4 未闭环 / A5 部分
部署态=ini 缺键 ⇒ 实际生效 0（两游戏目录 ra2render.ini 无 EnableGapProtection）
```

- 依据：`out/re_work/zcode_live/gap_p21_a3/RESULT_GAP_P21_A3.md`（13:11 终稿）§A3/§A4/§A5；`gap_p223/RESULT_GAP_P223.md:7,20,60-62`（12:44 终判行）；`MASTER_STATUS.md:13,43`（12:45，Track-C 改「✅ 收口（2026-10-01）」）。
- **给本文 §3 状态词表的建议**：现有词表只有 `已落地 / 就绪 / 待批 / 未落地 / 已勘误`，缺「**验收档位**」这一维。本次同一张卡出现 A3 PASS / A4 未闭环 / A5 部分三种判级，正是词表表达不了的形态 ⇒ 建议追加子表「验收档位：PASS / PASS(限定) / 部分 / 未闭环 / 未测」，杜绝「A3 到底算不算落地」的含混。
- A4 死因更新（**不是**脚本 Bug 可解）：存档描述框对 `keybd_event VK` / `SendInput UNICODE` / `keybd_event SCANCODE` 三种注入均不响应，叠加读档歧路载入旧档；`A4-J2`（`except.txt` 无新增）成立。
