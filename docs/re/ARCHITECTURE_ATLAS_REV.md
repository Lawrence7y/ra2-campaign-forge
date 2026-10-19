# ARCHITECTURE_ATLAS_REV.md —— v23 续做交付报告（Lead 主笔）

> 本报告是 **Agent Teams 模式** 下对 S17「全景架构图谱」的续做收口件：把 09-27 冻结之后产生的全部新结论并入 atlas，并补齐 V1 覆盖度审计查出的 10 个缺失子系统专章。
> 配套：`docs/re/atlas_rev/R1..R8_*.md`（8 条并行流的锚定补丁块原始交付）、`out/re_work/atlas_rev/**`（断言/门禁原文/脚本/dump）。

---

## [META]

```text
task=v23-atlas-rev        executor=Lead(step-5-preview) + 8 teammates(deepseek-v4.1-flash) + 2 muse-spark 子代理(只读)
mode=accept-edits         scope_declared=docs/re/ARCHITECTURE_ATLAS.md + tools/atlas_*.py + tools/verify_evidence.py + docs/re/atlas_rev/** + out/re_work/atlas_rev/**
真机=0 启动 / 注入=0 / 二进制=只读(gamemd.exe MD5 4f37486e5b0dbe2ae5f45aeee0f98367)
```

## [0] 结论摘要

1. **atlas 由 2001 行 / 140,159 B 扩至 4602 行 / 428,790 B**：机械套用 **50 个锚定补丁块**（49 自动 + 1 手工），新增 **§13–§22 十个专章**，章节编号 0→22 单调无冲突。
2. **证据面整体跃升**：唯一地址型 VA 530→**1731**，有机器可复核字节断言支撑者占比 **37.9%→72.15%**（1249/1731），多源同址字节**真实冲突 0**。
3. **门禁全绿**：`verify_anchors.py` 323/323 PASS；8 流 assertions 合计 **1990 条 OK / 0 MISMATCH**（Lead 独立复跑）；新增 `tools/atlas_audit.py` 结构合规 **ALL PASS**；TOC 0 缺 0 漂移。
4. **最大风险不在 atlas 本身，而在"纸面已定谳、代码未落地"**：§20.6 实证 3×6B NOP 未落地 ⇒ PsychicReveal 仍清 `Cell+0x134`，裂缝**永久静默失能**（P0，ra2render 域）。
5. **真机项全数挂起**：L4DirtyMode 像素等价性、ZC-11 模型判别、MP 对拍均为 `[待实测]`，本批**未**做任何"实测"升格。

## [1] 逐条必答项结论表

| # | 问题 | 结论 | 证据等级 | 证据锚点 |
|---|---|---|---|---|
| 1 | subagent 能否选模型？ | 能；本会话白名单仅 2 条路由（`step/step-5-preview`、`opencode1/muse-spark-1.3-contributor`），其余路由被 Session 级策略拒绝 | [实证] | `list_subagent_models` 实跑；探针子代理回报 `muse-spark-1.3-contributor` |
| 2 | teammate 能否选模型？ | **不能**：`spawn_teammate` 无 provider/model 入参；本批 8 名队友实际落 `deepseek-v4.1-flash`（profile agent-default-model），非 Lead 路由 | [实证] | `list_agents` roster；dsh-experimental-tool-agent-team/lib/index.js:268-292 |
| 3 | 09-28 波结论是否已并入？ | 12 份中 **9 份新增/更正进 atlas**，3 份（v160_acceptance / ZCODE_LIVE_ACCEPTANCE_TASK / EVIDENCE_STANDARD 流程面）以新 §13 收录 | [实证] | R1–R4 覆盖度自证表；本报告 [2] |
| 4 | 缺失子系统是否补齐？ | 是：**10 个缺口**全部落章（§14–§22 + §13 流程节） | [实证] | atlas §13–§22 存在性 + 章节单调 |
| 5 | 是否存在伪造/升格？ | **无伪造**；8 处「实测」误用（静态复算称实测）已按 v3 零容忍改为静态复算措辞 | [实证] | R4 PATCH-06/07/08 + ERRATUM-09；R4 claims 32/32 |
| 6 | 是否越界写入？ | 无：8 流全部零写 atlas 与他方文件（各流自证 mtime/MD5）；Lead 为 atlas 唯一写者 | [实证] | 各 R# 报告 [5] 节；本报告 [5] |
| 7 | 真机是否被启动？ | 未启动（0 进程、0 注入、二进制 mtime/MD5 未变） | [实证] | 各流 [5]；本报告 [5] |

## [2] 关键证据块（可复算）

**A. 套用台账（`out/re_work/atlas_rev/lead/atlas_apply_ledger.json`）**

| 流 | 补丁块 | 动作分布 | 替换文本行数 | 主题 |
|---|---|---|---|---|
| R1 | 9 | INSERT_AFTER×5 / REPLACE_BLOCK×2 / APPEND×2 | 177 | 渲染与 Blitter 族（含 **12B→8B 推翻性勘误**） |
| R2 | 9 | INSERT_AFTER×6 / ERRATUM×3 | 194 | 迷雾/视野/L4 脏矩形/建筑残影 |
| R3 | 10 | ERRATUM×3 / REPLACE×1 / INSERT×4 / APPEND×2 | 85 | 小队 AI + 钩子/补丁字节审计 |
| R4 | 9 | INSERT_AFTER×5 / REPLACE×3 / ERRATUM×1 | 101 | 证据标准合规 + **新 §13 验收闸门** |
| R5 | 3 | APPEND×2 / ERRATUM×1 | 432 | **§14 触发器 / §15 存档** |
| R6 | 2 | APPEND×2 | 398 | **§16 武器 / §17 MIX** |
| R7 | 4 | APPEND×4 | 633 | **§18 VXL / §19 FX 链 / §20 裂缝·SpySat** |
| R8 | 3 | APPEND×2 / INSERT×1 | 370 | **§21 UI·输入 / §22 CRT 调用图** |
| 合计 | **49 自动 + 1 手工（R2-10）** | — | **2390 行** | — |

**B. 双快照口径**

```text
[快照 A · pristine] docs/re/ARCHITECTURE_ATLAS.md  MD5 6e790b55b2709ff5c41ad3f73f7e49e4  mtime 2026-09-27T22:22:08  2001 行 / 140,159 B
[备份]             out/re_work/atlas_rev/lead/atlas_backup_preapply_20260929-132225.md
[快照 B · final]   docs/re/ARCHITECTURE_ATLAS.md  MD5 f0cb4b3cbaca382d5d6dacb2f8a5854d  mtime 2026-09-29T13:28:54  4605 行 / 429,359 B
  （快照 B 过程：套用 49 块 → 手工 R2-10 → §11.4 索引 → 附录 DA1 归位 → TOC 重建 → v93 术语清理 13 处）
[基线二进制]        ra2youli/gamemd.exe            MD5 4f37486e5b0dbe2ae5f45aeee0f98367（读前后一致，未写）
```

**C. 结构/合规体检（新增工具，Lead 自研）**

| 工具 | 作用 | 本批结果 |
|---|---|---|
| `tools/atlas_audit.py` | 围栏配对 / 章节编号单调 / 目录锚点 / 证据等级覆盖 / **作废阈值残留** / VA 清单导出 | **ALL PASS**（F1 68 对围栏 0 未闭合；F2 章节 0–22 单调；F5 0 未更正残留） |
| `tools/atlas_toc.py` | 目录重建与漂移检测（slug 规则以冻结文本自证 16/16） | 184 条目，**0 缺 0 漂移 0 stale** |
| `tools/atlas_va_crosscheck.py` | atlas VA ↔ 断言库交叉核验（悬空/前缀变体/真冲突） | 1731 VA；支撑 1249（**72.15%**）；悬空 482；**真冲突 0**（101 组同址均为前缀/窗口长度变体） |
| `tools/atlas_apply_patches.py` | 补丁块机械套用（锚点解析→倒序套用→台账→备份） | 50 块解析/49 自动套用/1 转手工；**锚点全部唯一命中或与声明行号一致** |

**D. 独立复算（不采信他人门禁）**

- Lead 自写读取器（非 `audit_bytes.py`）跨 5 流随机抽验 15 条断言 → **15/15 OK**（`out/re_work/atlas_rev/lead/lead_spotcheck.py`）。
- Lead 复跑 8 流全部门禁：R1 56、R2 114、R3 63、R4 32、R5 696、R6 405、R7 445、R8 179 = **1990 条 OK / 0 MISMATCH**。
- 跨模型独立验证（task-6，muse-spark-1.3-contributor）→ 见 `out/re_work/atlas_rev/verify/VERIFY_atlas_rev.md`。

## [3] 勘误总表（Lead 裁定：**既有文档保持冻结**，勘误登记不就地改写）

> 裁定理由：8 条并行流若各自改写既有 `docs/re/*.md`，将产生不可审计的并发变更面；本批统一"登记在案、单独立项执行"。

| # | 目标文件:行 | 改前 → 改后 | 来源流 | 影响面 |
|---|---|---|---|---|
| 1 | ARCHITECTURE_ATLAS.md:242-249（已就地更正） | 「所有 Blitter 固定 12 字节」→ **4/8/12/16 四级尺寸矩阵**，P0 微内核 8 字节；按 12 字节声明 `this+0x08` **越界 4 字节** | R1 | **产品级阻断**（ra2render 结构体声明） |
| 2 | ARCHITECTURE_ATLAS.md:347-351（已就地更正） | §1.6「流水线停顿 >40%」→ **撤回**（无来源且与作废采样冲突） | R1 | 性能论证口径 |
| 3 | ARCHITECTURE_ATLAS.md:875/968/959（已就地更正） | 招募三分支「陆军/海军/空军」→ **战车工场+步兵兵营 / 造船厂 / 机场+飞机场**（`cmp eax,0x28/0x10/0x03`） | R3 | 产品决策（轮转/时间片边界） |
| 4 | ARCHITECTURE_ATLAS.md 8 处（已就地更正） | 「实测」→ 静态复算措辞（472/473/1372/1375/1512/1513/1515/1710） | R4 | 标准 v3 零容忍合规 |
| 5 | patch_hex_audit.md:282 | 「每帧消费 1 次 RNG」→ **2 次**（独立复算 4 调用点；`0x64DE3F`+`0x650AB7/0x650AF2`） | R3/R5 | 联机确定性红线 |
| 6 | trigger_runtime_deep_dive.md:§7 | 3 处字节/偏移错位（`0x6E525E` 应 `A1 98 F6 B0 00`；`0x726509` 应 `8B CB`；`0x55DE9F` rel32=`1C`） | R5 | 触发器取证链 |
| 7 | trigger_system_manifest.md §1.1/§2.5 | 读侧调用点 17→**18**；OLE 引用面 8→**11/12** | R5 | 序列化审计口径 |
| 8 | l4_dirty_spec_v2.md:48/49/52 | :52 字节全错（实为 `8B 85 B0 00 00 00`）；:48/:49 交错 store 写成连续 | R2 | L4 打脏规格 |
| 9 | building_fog_residual_deep_dive.md:870 | 入口 `0x0043CEC0`（指令中部）→ **`0x0043CEA0`**；槽 313 = `0x0043DA80`（非 `0x0043D290`） | R2 | 建筑残影结论 |
| 10 | fog_strength_rootcause.md:47 / fog_split_report.md E0~E7 | 归属与产物侧口径 | R2 | 迷雾强度标定 |
| 11 | weapons_damage_production.md | `Verses` 起于 **+0xA0**（非 +0xB0）；`FactoryClass` 步数 **+0x24**、在造对象 **+0x58**；`FootClass` v[243]=`0x6FDD50` | R6 | **P0**（按 +0xB0 读会错位 16 字节） |
| 12 | fx_draw_chain.md:446/463 | `H-FX13` 风险 中→**高**（`+0x184`=DelayTimer，同时门控 Draw/Update 且消费 RNG）；淡出公式**不存在** | R7 | 特效链优化 |
| 13 | visibility_gap_spysat.md §2.1/§2.2 | 旧偏移三处 | R7 | 裂缝/卫星可见性 |
| 14 | shroud_click_interaction.md:102 | `IsLocationFogged` 直调点 0→**1**（`0x00655D74`） | R8 | 黑幕点击 |
| 15 | crt_callgraph.md | vsprintf 调用者 `0x005BD245`（相邻序言）→ **`0x005BD1F0`**，调用点 `0x005BD214`；`_delete` 4498→**4499** | R8 | CRT 池化论证 |
| 16 | EVIDENCE_STANDARD.md:31 / v160_acceptance_runbook.md:42,44 | 表内旧阈值加订正指针 | R4 | 验收门禁 |

> 【W3 勘误 · PATCH_SUGGESTIONS BLK-C4-1】改前：槽 313 = `0x0043DA80`（非 `0x0043D290`）；改后：第 9 行括注「（非 `0x0043D290`）」限定射程为仅否定 building_fog_residual 把 `call [edx+0x4E4]` 误标为 `0x007E3FD0`，不否定 atlas 的 v[69] = `0x0043D290`（两槽同属 `.?AVBuildingClass@@`，v[69]=`0x0043D290` 为 Draw 本体，v[313]=`0x0043DA80` 为绘制包装）；依据：`0x007E3EBC + 69*4 = 0x007E3FD0 (0x0043D290)` 与 `+ 313*4 = 0x007E43A0 (0x0043DA80)` / COL `0x7FC360`；分级：[实证]

## [4] 未闭环清单

| 级别 | 缺口 | 为何无法静态闭环 | 下一步取证方法 |
|---|---|---|---|
| **P0** | §20.6：3×6B NOP 未落地 ⇒ PsychicReveal 经 `0x568273` 清 `Cell+0x134`，裂缝**永久静默失能** | 属 ra2render 代码轨（本批禁改） | `ra2render/**` 检索 `568273/577EC5/577B60`（现 0 命中）→ 三处各打 6B NOP 后真机复现 |
| **P0** | L4DirtyMode 像素等价性 / ZC-11 模型判别 / MP 对拍 | 需真机（本批真机 0 启动） | 按 §13.4 两级过滤 + `tools/verify_evidence.py` 机械筛 → 人工抽验 |
| **P0** | P-2（`Cell+0x134` 三处 6B NOP + SpySat 门控）触 ①同步语义 ③存档结构 | 需双端对拍 | MP 门控矩阵 + 握手键取证（见 [9]-D1） |
| **P0** | 触发器轮询器锁存位 `[Scenario+0x34AA/34AB/34BE]` 是否含本机输入路径 | 决定触发器 MP 分叉面，静态无法判定 | 双端 hook `0x65C780/0x65C7E0` 对拍 |
| P1 | atlas **482 个 VA 无机器断言支撑**（28%） | 多为散文引用未附字节 | 逐条补 claims 或降级为非地址表述 |
| P1 | **46 个小节缺前置证据等级标签**（新章约 39：§13-15/18-20/22 各 4-5） | 等级标签常写在节内而非标题/首 3 行 | 下一轮统一补标签（纯格式，不改结论） |
| P1 | §13–§22 速查表**未去重并入 §11.1–§11.3 主表** | 需单一写者逐行去重 | 已加 §11.4 索引；合并单独立项（[9]-D5） |
| P1 | `Verses` 实际施加点未定位（全 .text 索引访存 0 命中） | 需扩大反汇编扫描面 | 建议 30 分钟专项：对 `*8 + 0xA0/0xB0` 变体做定点扫描 |
| P1 | 每帧 RNG 消费量真机分布 | 需双端 hook 计数 | hook `0x65C780/0x65C7E0` |
| P1 | §0.3 `>350` 翻转格阈值出处不可考 | 7 份来源 0 锚点 | 已标 `[待核对]`；建议改可实证口径 |
| P2 | [3] 表中 15 组源文档勘误未执行（既有文档保持冻结） | Lead 裁定先登记 | 授权后就地订正（[9]-D4） |
| P2 | R1 §1.2 结构体声明 12B→8B 需与代码轨联审 | 跨轨协调 | 与 ra2render 代码轨排期 |

## [5] 写作用域合规声明

**Lead 改动文件（唯一写者口径）**

| 文件 | 规模 | 说明 |
|---|---|---|
| `docs/re/ARCHITECTURE_ATLAS.md` | 4602 行 / 428,790 B | 49 块自动 + R2-10 手工 2 处 + §11.4 索引 + TOC 重建 |
| `tools/atlas_audit.py` / `atlas_toc.py` / `atlas_va_crosscheck.py` / `atlas_apply_patches.py` | 新增 4 件 | 结构/目录/证据/套用四类门禁 |
| `tools/verify_evidence.py` | 5 处编辑 | 阈值对齐 09-28 订正（≥600 采样 / ≥800 全画面），新增 `colors_full`，措辞 v2→v3 |
| `docs/re/ARCHITECTURE_ATLAS_REV.md` | 本文件 | — |

**未触碰**：`ra2render/**`、`ra2youli/**`（除 `tools/verify_evidence.py` 只读其日志路径）、`REVERSE_ENGINEERING_AND_PATCHES.md`、既有 `docs/re/*.md`（勘误仅登记）、`gamemd.exe`。
**8 名队友**：写作用域仅 `docs/re/atlas_rev/R#_*.md` 与 `out/re_work/atlas_rev/R#/**`；各自自证 atlas 0 次写入（mtime/MD5 未变）。

## [6] 门禁实跑输出（原文摘录）

```text
python tools\verify_anchors.py
  回归汇总 : 断言总数 323 条 | PASS: 323 (100.00%) | FAIL: 0 | NOREAD: 0
  ★ 最终裁决 : [100% ALL PASS] 全库决定性锚点与二进制基线完全一致

python tools\audit_bytes.py <各流 claims>          (Lead 复跑)
  R1 56/56 | R2 114/114 | R3 63/63 | R4 32/32 | R5 696/696 | R6 405/405 | R7 445/445 | R8 179/179   → 1990 条 OK / 0 MISMATCH

python tools\atlas_audit.py
  行数 / 字节 / mtime: 4601 / 428790 / 2026-09-29T13:24:16
  F1 代码围栏配对 PASS(68 对, 未闭合 0) | F2 章节编号单调唯一 PASS([0..22])
  F3 目录锚点 PASS | F5 作废阈值残留 PASS | 裁决: ALL PASS

python tools\atlas_toc.py --check
  目录条目 184 | slug 规则自证 0 偏差 | 缺失 H2 0 | stale 0

python tools\atlas_va_crosscheck.py --claims <8 流 claims>
  唯一地址型 VA 1731 | 有断言支撑 1249 (72.15%) | 证据悬空 482 | 真实字节冲突 0（前缀/窗口变体 101 组）
```

## [7] 风险与红线提示

本批新章**同时触及四项红线**，一律禁止宣称"零风险/零 Desync"：

1. **同步语义/命令序**：§16.4 伤害结算路径、§14 触发器条件消费、§21.6 方案 B（网络解包 `0x004C71CA` 单边启用）→ **必然 Desync**，仅限全网同构。
2. **随机数消费序**：§16.4 局内 27 处 PRNG 调用点；§19 EBolt 在 `DrawAll` 内衰减（整函数短路 ⇒ 电弧永生）会改变消费时序。
3. **存档结构**：§15 读/写侧不对称（8 段 OLE 读循环 vs 35 块 127B 模板块）；P-2 触 `Cell+0x134`。
4. **渲染像素等价性**：§1 overshoot 处 `zmap` 不推进是原版 off-by-overshoot 缺陷，SSE2 必须**原样复现**；L4DirtyMode 三档逐像素等价性未验。

## [8] 交付物清单

| 类别 | 路径 | 规模 |
|---|---|---|
| 主交付 | `docs/re/ARCHITECTURE_ATLAS.md` | 4602 行 / 428,790 B（新增 §13–§22 + §11.4） |
| 本报告 | `docs/re/ARCHITECTURE_ATLAS_REV.md` | 本文件 |
| 流交付 | `docs/re/atlas_rev/R1..R8_*.md` | 8 件，合计约 590 KB，50 补丁块 + 十节回执 + 覆盖度自证 |
| 断言库 | `out/re_work/atlas_rev/R1..R8/claims_R*.txt` | 1990 条（含复用既有 323 条） |
| 门禁工具 | `tools/atlas_audit.py` / `atlas_toc.py` / `atlas_va_crosscheck.py` / `atlas_apply_patches.py` | 4 件新增 |
| 台账/体检 | `out/re_work/atlas_rev/lead/{atlas_apply_ledger.json, atlas_audit.json, atlas_va_index.csv, atlas_va_crosscheck.json, atlas_toc_report.md, lead_spotcheck.py}` | 6 件 |
| 备份 | `out/re_work/atlas_rev/lead/atlas_backup_preapply_20260929-132225.md` | 140,159 B |
| 独立验证 | `out/re_work/atlas_rev/verify/VERIFY_atlas_rev.md` + V1 覆盖度审计回执 | 2 件 |

## [9] 待裁决项

**Lead 已裁定（可直接复核）**：L1 既有文档冻结、勘误登记（[3]）；L2 跨节 ERRATUM 采纳；L3 PATCH-R3-10 保留（与 §12.2 其余三条锚点不同、内容互补）；L4 PATCH-R7-04 采纳；L5 R2-10 手工落章采纳；L6 新增 §11.4 索引（主表合并另立项）；L7 `verify_evidence.py` 阈值对齐订正口径**已实施**（改 `<600` 判 FAIL + 新增全画面 `<800`）；L8 §13 清单不加责任人列；L9 「实测」误用按 v3 零容忍就地订正。

**需你裁决**：

- **D1** P-2 握手键（`EnableGapProtection` / `EnableSpySatGate`）是否强制联机门控？
- **D2** `G-04` 判据作废后，既有验收脚本是否清扫？
- **D3** §21.6 方案 B（单边网络解包）是否在 §12.2 增列**红灯**（当前仅章内标注）？
- **D4** [3] 表 15 组源文档勘误：授权 Lead 就地订正，还是继续保持冻结？
- **D5** §13–§22 速查表合并进 §11 主表是否立项（需单一写者逐行去重）？
- **D6** 8 流 1990 条 claims 是否作为 `verify_anchors.py` 附加断言库长期回归？
- **D7** `verify_evidence.py` 阈值改动是否正式写回 `EVIDENCE_STANDARD.md` 附录（现仅代码内注明依据）？

## [10] 收尾修复与独立验证记录（套用后，Lead）

**A. 独立验证（task-6，跨模型 muse-spark-1.3-contributor，只读）** —— 报告 `out/re_work/atlas_rev/verify/VERIFY_atlas_rev.md`

| 项 | 结果 |
|---|---|
| T1 字节复核（自写 reader，不依赖 audit_bytes.py） | **27/27 PASS**，覆盖 §15–§21 七章 |
| T2 证据等级真实性 | **0 违规**（扫描 307 条 [实证] 行；L4DirtyMode/迷雾/VXL/SpySat/UI 抽查无升格） |
| T3 重复/矛盾扫描 | **0 真矛盾**（201 处重复均为正文↔速查表复用；10 个高风险 VA 一致；v[65]/v[69] 分歧如实上报） |
| T4 标准合规 | 阈值合规（≥600/≥800）；**报出措辞违规**（处置见 B） |
| T5 结构 | **0 缺陷**（无标题跳级/空节/未闭合围栏/范围重叠） |
| 未验证项（非 FAIL） | xref 计数、未抽样 claims/重复项、全部真机行为 |
| **总裁决** | **PASS**（以 T4 措辞清理为条件，已完成） |

**B. T4 处置**：V6 给出的 13 个行号存在**行号漂移**（Lead 复核其中 12 行并不含「实测」）；Lead 全库重扫后确认的真问题是 **13 处把静态字节复算写成「实测」的措辞**（实测字节×4、映像内实测、槽数实测、（本流实测）、实测提取的静态尺寸、入口字节（本轮实测）、字节取自本镜像实测、引擎实测值、实测口径为、实测为 …），已按 v3 零容忍**逐条上下文精确改写为「复算」**（零语义变更），并在 §13.6 增补 Lead 口径说明。改写后复查：正文残留「实测」仅剩 §13.6 定义/禁令行与 [待实测] 标签。

**C. 套用后 Lead 自查发现并修复的结构缺陷**：机械套用把**原冻结附录 DA1 的标题与正文切开**（标题留在 §13 之后、正文被推到 §22 之后）。终检发现并**归位**（标题回到正文之前）；TOC 重建后 0 缺 0 漂移；最终章节序为 12 → 13 → 14 → … → 22 → 附录 DA1 → 附录 DA1-bis。此缺陷说明：**机械套用后必须做人眼终检**，仅靠结构门禁不足以发现「标题与正文被隔断」。

**D. tools/verify_evidence.py 阈值改动回归**（回应 R4 的 P0）：两批历史证据重跑 —— v160_test（伪造批）4 张全部 **FAIL**（唯一色数 = 1，命中伪造判据）；calib（校准批）c0 **PASS**（250 采样色）、c2 **PASS**（909 采样 / 6135 全画面）、c1 与 d0 **FAIL**（MD5 与 c0 重复 ⇒ 按键未生效推断成立）。即：**新口径未削弱任何既有拦截**，且不再误杀同量级合法证据（旧口径会把 250 色菜单误判为色数不足）。报告：`out/re_work/atlas_rev/lead/verify_regress_v160_test.json`、`out/re_work/atlas_rev/lead/verify_regress_calib.json`

**E. 最终门禁（快照 B 之上）**：`verify_anchors.py` **323/323 PASS**；`atlas_audit.py` **ALL PASS**；`atlas_toc.py --check` **0 缺 0 漂移**；`atlas_va_crosscheck.py` **真冲突 0**；8 流 claims 1990 条 **0 MISMATCH**。

---

## [11] 状态注记（追加节 · 2026-10-01 · 工单 `T-W1-Q / PK-1`）

> **只追加、不删改**：§[0]–§[10] 全部逐字保留（含 `[META]` 的「真机=0 启动」自证与本节要订正的 P0 条目原文）。
> 本文件所描述的 `docs/re/ARCHITECTURE_ATLAS.md` 本体在本轮**未被触碰**（工单明令禁改，落盘由 Lead 处理）。

### C-1 · §[0] 第 4 条 与 §[4] 表首行（§20.6 P0）：裂缝保护「纸面已定谳、代码未落地」→ **已落地，P0 消解**

- **改前逐字**（`:21`）：「**最大风险不在 atlas 本身，而在"纸面已定谳、代码未落地"**：§20.6 实证 3×6B NOP 未落地 ⇒ PsychicReveal 仍清 `Cell+0x134`，裂缝**永久静默失能**（P0，ra2render 域）。」
  （`:104` 未闭环清单同条目：「**P0** | §20.6：3×6B NOP 未落地 ⇒ PsychicReveal 经 `0x568273` 清 `Cell+0x134`，裂缝**永久静默失能** | 属 ra2render 代码轨（本批禁改）| `ra2render/**` 检索 `568273/577EC5/577B60`（现 0 命中）→ 三处各打 6B NOP 后真机复现」）
- **改后表述**：检索建议已可执行且**结果为命中**——三点 3×6B NOP 已于 2026-09-30 合入 `ra2render`（构建 `626f98b6…`），A1/A2 真机 PASS、C5 逆序回滚 PASS。故「永久静默失能」这条 **P0 已消解**；**残留的是行为验收**（A3/A4/A5 初判无法判定，战役轨进行中）与「`GapProt Version` 存档标记未实现」，二者不再是代码轨缺口。
- **实测依据**：`ra2render/ra2render.h:113,116,119`；`ra2render/blitter_hooks.cpp:3273-3287,3313,3402,3417,3736`；`out/re_work/zcode_live/gap_p223/RESULT_GAP_P223.md:56-59`（PASS 行）、`:60-62`（A3/A4/A5「初判无法判定」）、`:36,129`（存档标记未实现）；`out/re_work/harness_survey/RE_PROGRESS_SURVEY.md` §6-D1。

### C-2 · §[0] 第 5 条 / §[4] 表第 2、3 行的真机项：状态**未变**（如实保留，不升格）

- **改前逐字**（`:22`）：「**真机项全数挂起**：L4DirtyMode 像素等价性、ZC-11 模型判别、MP 对拍均为 `[待实测]`，本批**未**做任何"实测"升格。」
- **改后表述**：仍然成立，**但需补一条**：`L4DirtyMode` 的「不存在」已变为「三档已存在、仅默认档 force-full 经真机等价验证」，`vision-dirty` / `vanilla` 两档的像素等价性**继续** `[待实测]`（依据 `RESULT_ZC10B.md:26-27`、`RESULT_ZC11.md:38,43`）。MP 双端对拍仍「无真机联机窗口，未测」（`MASTER_STATUS.md:56`）。
- **另需补一条本轮新证**：`[4]` 表 P1 行「§0.3 `>350` 翻转格阈值出处不可考」→ 本轮普查期间**未**找到出处（仍 0 锚点），且 `0x6DA7D0` 侧静态实现 0 命中，因此该阈值既无出处也无实现体可反推；结论保持 `[待核对]`（`RE_PROGRESS_SURVEY.md` §7 U-6）。

### C-3 · §[3] 勘误总表 16 行 与 §[9] D4：登记面扩大，执行面未动

- **改前逐字**（`:114`）：「P2 | [3] 表中 15 组源文档勘误未执行（既有文档保持冻结） | Lead 裁定先登记 | 授权后就地订正（[9]-D4）」
- **改后表述**：截至 2026-10-01，该 15/16 组勘误**仍未就地执行**（本轮工单同样只登记不订正）。本轮**新增** 6 条同类「文档 vs 实况」偏差（编号 D1–D6，见 `RE_PROGRESS_SURVEY.md` §6），其中 5 条已按「只加注、不删原文」范式登记进四份文档的追加节（本文 `[11]`、`HOOK_POINT_MATRIX.md` §七、`pending_execution_master_table.md` §八、`dual_track_status_note.md` §6、`p223_readiness_check.md` 末节），第 6 条（`MASTER_STATUS.md` DLL 待同步）属 zcode 写域，未代改。
- **建议（给 Lead）**：§[3] 与本轮 6 条宜合并为一份「勘误执行包」，按 D4 裁决一次性就地订正，避免同一文件里出现三层追加节。

### C-4 · §[4] 两条 P1 证据债的静态消解路径已开工（未闭环）

- **改前逐字**（`:108`）：「P1 | atlas **482 个 VA 无机器断言支撑**（28%）」；（`:109`）「P1 | **46 个小节缺前置证据等级标签**」。
- **改后表述**：本轮 PK-7 已在 `out/re_work/atlas_debt/**` 产出**可套用的补丁块**（未落盘至 atlas 本体），并把「悬空」计数由脚本独立复算校验；消解率、逐条决策（补 `[实证]` claims / 降级为非地址表述）以该目录报告为准。
- **状态**：**进行中**——atlas 本体未改，故本文 §[4] 的两条计数**暂不得下调**，待 Lead 套用后由 `tools/atlas_va_crosscheck.py` 重跑给出新值。

### C-5 · ★终判回填（2026-10-01 13:15 之后追加）—— C-1 的「残留行为验收」已收口

C-1 写「残留的是行为验收（A3/A4/A5 初判无法判定，战役轨进行中）」——同日 T-Z1 收口，现结论：

- **A3 = PASS（带窗口限定）**：on 档 3 会话全程 `gap_cells=663` kept=100.0%、三点 in-process `90×6`、遥测 `installed=3/3`；off 对照晚期 a5 `663→373→0`。⇒ §[4] 表首行那条 P0 的**全部残留**只剩三项：A4 未闭环（存档 UI 注入 + 读档歧路）、A5 部分（on >6min 长窗未取得）、`GapProt Version` 存档标记未实现。
- **给 atlas §20.6 的一条方法论补充**：本次暴露「开图判据选面错误」——战役场景下裂缝格**开局已 mapped**，故 `RevealArea2` 的清零分支本就不执行，用「开图后是否被清」验 off 档会恒得 kept=100%（`C-J3` 口径修正）。建议 atlas 的裂缝章把这条写进「验收陷阱」类注记：**验 `+0x134` 清零面必须走晚时 reshroud / crate 旁路，不能只靠 PsychicReveal 开图**。
- 证据：`out/re_work/zcode_live/gap_p21_a3/RESULT_GAP_P21_A3.md`（13:11 终稿）、`gap_p223/RESULT_GAP_P223.md:60-62`（12:44 终判）、`MASTER_STATUS.md:13,36,43,44`。
- 本节所属的全部登记（本文 `[11]`、`HOOK_POINT_MATRIX.md` §七、`pending_execution_master_table.md` §八、`dual_track_status_note.md` §6、`p223_readiness_check.md`、`INSTALLED_HOOKS_AUDIT.md` §11）均经 `out/re_work/harness_survey/errata_addendum/verify_append_only.py` 自证为**只追加**（前缀逐字节相同 + diff 删除侧 0 行）。
