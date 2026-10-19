# 三目标当前状态表（STATUS_TABLES · 2026-10-19）

> **性质**：Lead 令（2026-10-19 评审建议第 5 条 + P5 补遗）——三目标各一张"当前状态表"，替代在几十篇文档里找进度。
> **纪律**：本文件为唯一写入物；其余全部只读汇总。两线冲突或证据不足处显式标 **【待对账】**，不抹平。
> **快照时点**：2026-10-19 19:2x（日志 §204 后）；P1/P2 修复件回执落盘于 19:22/19:23（晚于日志末次追加，已并入表③）。

## 数据源索引

**缩写约定**（下文括注引用使用）：

| 缩写 | 全路径 |
|---|---|
| `GOAL` | `out\re_work\work_chain\CONTINUE_20261003\lead\GOAL_THREE_TARGETS_20261018.md`（状态日志在尾部） |
| `日志` | `out\re_work\work_chain\CONTINUE_20261003\lead\ROUND_SUBAGENT_LOG_TRIGOAL_20261017.md`（§180 以后最新最准；本文引用至 §204） |
| `卡面` | `out\re_work\work_chain\CONTINUE_20261003\lead\cards\QC161.md`（§T52-T59 趟级判读） |
| `docs\re\` | `D:\Project\ra2-campaign-forge\docs\re\`（render/bench 线证据件，只读引用勿深潜） |
| `crashspec_v4` | `out\re_work\work_chain\CONTINUE_20261003\crashspec_v4\`（RC_SPEC_V4.md 751 行 + M1_RULING_ANNOTATION.md） |

**Lead 线其余**：`lead\goal1_c1c2_readj_20261018\C1C2_READJ_T50.md` · `lead\goal2_poison_gen_20261018\POISON_GEN_DESIGN.md`（+DESIGN_REVIEW.md）· `lead\goal3_versioncheck_20261019\RECEIPT.md` · `lead\goal3_configsplit_20261019\RECEIPT.md` · `lead\boot_hang_triage_20261018\SINGLESTEP_0x7CFC9F_ANALYSIS.md` · `lead\crashspec_offline_close_20261018\` · `lead\qc151_p3dump_20261019\` · `lead\spawnfix9_freeze_20261019\` · `lead\evid_diffmode_20261019\`。

**bench/render 线**（只读）：`docs\re\h1_capacity_gap.md` · `docs\re\u0800_redesign_spec.md` · `docs\re\radar_crash_static_analysis.md` · `docs\re\radar_hook_routeA_spec.md` · `docs\re\except_zc11_forensics.md` · `out\re_work\zcode_live\h1_remeasure\RESULT_H1_REMEASURE.md`。

**未读声明**：`docs\re\ARCHITECTURE_ATLAS.md` 系移动靶未读（现行 atlas 在 `qc\scope\atlas_game\`，本轮未使用）。

---

## 表① 数百单位卡顿

| # | 已证实（带证据路径） | 待测（判据） | 下一步 |
|---|---|---|---|
| 1 | bench 三档单位数严格单调 67/177/724（美vs蘇 UC10，同档极差 0）（`docs\re\h1_capacity_gap.md` §1；RESULT_H1_REMEASURE [0]） | 同图 A/B＋原版基线对照，分离"图/协议/负载形态"三变量（日志 §204 ①口径第三条） | T55h=P3 首趟待用户发射（lite 图 7 秒局，--frozen-dump＋12 点阶梯锁存）（日志 §203） |
| 2 | bench 724 单位战斗局塌方：≈6fps（f10→f386/55s）、单帧 >10s、12s 窗零帧推进 ×2（`docs\re\u0800_redesign_spec.md` §1 P1/P2） | spawnfix9（~2400 档）掷出后按 §T56 判据裁决 C 岔：贴帽则 C 成立、破帽则复现环境＋复活双得；C 收卷硬条件=units0≥1500 且贴帽（GOAL L45；日志 §185） | 长战局杠杆=阻止 h1 早期败北拉长战局（10c 装载已验 OK；受害者选择机制交 P3DUMP 定谳）（日志 §192） |
| 3 | bench 724 档 5 局中 2 局进程静默死亡（无 except、RPM 失联）；3/3 局 perf 采样不可得（`docs\re\u0800_redesign_spec.md` §1 P3/P4） | 终局画面识别/记分板点击改进，根治 QC213 frozen 判据把记分板误读为冻结（日志 §192） | 评审建议映射：评分区间移到崩塌区＋原版对照热点分析（日志 §202） |
| 4 | Lead T50：971 单位（41→23.7×）2332 帧三窗全活跃、贴 31 帽无塌方（fps_avg 30.80-31.24、p90=35.2-37.4ms 浅越、唯一 110.7ms 深停顿）（GOAL L45/L76；卡面 §T53；C1C2_READJ_T50.md） | 971 的 p90 浅越须配"实际在场数"口径解读，1212 同理（本趟阶梯即得，日志 §204） | 静态 vs 战斗分界坐实实验：同图 A/B＋原版基线入 ① 实验队列（日志 §204） |
| 5 | 浅越随单位数单调缓升：>34ms 帧占比 41u≈0%→241u 21.6%→491u 22.7%→971u 24.96%，深越全程 <2%、85% 孤立单帧（C1C2_READJ_T50.md；卡面 §T52） | G16 悬空队号密度变体（1200-1440 vs 1120）是否致病，列 P3 阶梯观察项（日志 §195） | —— |
| 6 | frame_ms p90 随单位数爬升：971→35-37ms、1212→54.8ms（p50=34.1/p99=79.8/max=186）、1452→fps_p50=15.7（日志 §190/§192） | —— | —— |
| 7 | T34 判据：242 单位静态在场 p50=31.64ms/p99=35.08 ⇒ 静态在场不致卡、真实卡顿须战斗动态——**跨图推论未坐实**（GOAL L72；日志 §204 明示） | —— | —— |
| 8 | T49（U0800 缝补图 e3acc130）491 单位：317 帧@31fps 满帽健康＋终局冻结；fps_avg=12.68 系冻结稀释伪影已勘误（日志 §102/103/106；卡面 §T52） | —— | —— |
| 9 | T55d=961 单位 frame437 帧钟停，后翻案为战后记分板非挂死（日志 §185→§192） | —— | —— |

**★★ 两线张力（① 关键未决，显式登记不抹平）**：bench 724 单位战斗局 ~6fps 塌方 vs Lead 971 单位战斗局贴 31 帽无塌方——图（H1 100×100 新图 vs XMP29U2 缝补图）、协议（UC10 固定国家对 vs spawnfix 预置四方）、负载形态（bench CPU0 82% 寻路/AI 风暴 vs Lead 浅越为主）三变量未归一（`docs\re\u0800_redesign_spec.md` §1 P5；日志 §202/§204）；「静态在场 vs 战斗动态」分界只是场景差异假设、跨图推论未坐实（日志 §204）。**归一手段=同图 A/B＋原版基线（待测列第 1 行），归一前两线读数不得互为反证。**

**评审对 ① 的其余指摘（照录）**：评分区间错位、优化方向未对准瓶颈、缺原版对照、寻敌频率默认开违反房规（日志 §202）。

---

## 表② 主崩溃

**② 范围裁定（Lead 原句照录）**：「纳入 B/C，拆为 ②a（低负载，按原门禁验收）与 ②b（高负载，共用 ① 管道，先求现场可捕获、可复现，再谈修复）；C 类先完成版本对账」（日志 §204）。

| 分支 | 已证实/归因现状（带证据路径） | 缺口/待测 | 下一步 |
|---|---|---|---|
| **A 雷达钩子**（补丁自致） | 崩溃 EIP 0x5450202F=ra2render.dll `Hook_RadarPlot_Proxy`：MSVC 内联汇编把 `mov ecx,[0x0087F924]` 误编为 B9 立即数加载＋像素坐标误当格子索引（Y×512+X），0x1A0 小整数穿透护栏读零页（`docs\re\radar_crash_static_analysis.md` §一/二/三） | 新方案未上真机 | 路线 A：下沉挂钩点至 Plot_Cell 内 0x00655D38 取原版合法 CellClass*（9 字节覆盖+trampoline，规格 `docs\re\radar_hook_routeA_spec.md`）；验收=真机 3 局 except 零新增＋verify_evidence v3 PASS（radar_crash_static_analysis §七） |
| **B 分配器损坏**（静态归因，无真机复现对照） | 崩溃点 0x7CFC9F=原版 CRT SBH `__sbh_alloc_block`：freelist 节点指针被毒值 FE00FFFF 污染（mov ecx,[edx] read AV）；调用链全在原版 CRT、与注入钩子无执行路径关系；根因候选 R1 UAF 写穿/R2 double-free/R3 邻块越界写均 [推演]（`docs\re\except_zc11_forensics.md` [0]/[4]/[5]） | V1-V5 A/B 实测（无注入/有注入/LFH 关各 ≥3 局）未跑；毒值写者未指认（`docs\re\except_zc11_forensics.md` §8；GOAL L48） | P1 毒值事件捕获（QC205 7/0/0 放行，锚 1355dead）待真机 B 臂七连标定趟；P2 活性差分（P05 锚 6378b538）待真机首跑；#4 毒值事件发生器设计已交付＋修订核验 REVISION SOUND（GOAL L30/L31；`lead\goal2_poison_gen_20261018\POISON_GEN_DESIGN.md`） |
| **C 800 档静默消失**（无现场） | bench U0800 724 单位 5 局中 2 局进程静默死亡（无 except、RPM 失联、gate PASS），未捕获任何进程态/dump（`docs\re\u0800_redesign_spec.md` §1 P3；RESULT [7].2） | 现场可捕获可复现未达成（②b 口径即为此设） | ②b 共用 ① 管道首趟重测 U0800 档生产新现场；C 类版本对账见下方专节（日志 §204） |
| **Lead 线新增：T55 系「硬冻结」已翻案** | T55d frame437/T55e frame378 帧钟停=战后记分板等点击，非挂死（W1 窗尾截图实证）；QC213 frozen 判据把终局画面误读为冻结（日志 §192） | T55d frame437 的终审依赖 P3 dump 主线程终态（记分板良性 vs 真挂死）（日志 §192/§194） | T55h=P3DUMP 首趟（核验 CONFIRMED、终验 sha 5b5b21dc…、12 点阶梯）待用户发射（日志 §203） |
| **Lead 线新增：≥1080 预置行开场秒级清洗** | T55e(1200 行) h1 ~30s 败北、T55f(1440) h1 同、T55g(1080) h0 7 秒被清洗（84 亡/零击杀/杀者零损耗）=非战斗清洗；受害者选择机制未知（对照矩阵：T50 960 行无人灭；地图配置层两代逐字节同已排除）（日志 §190/§192/§194/§195） | 受害者选择机制未定谳；清洗时刻衰变曲线（一次性清洗 vs 渐进消耗）未采到（日志 §194） | P3DUMP 冻结 dump 在飞正是抓这类现场：衰变曲线＋主线程终态＋受害者落地质子（f15/f30 首闩锁 c5574）（日志 §203/§204） |
| **0x7CFC9F 单步异常** | 定性=真实外源调试机制陷阱（TF 单步或 DR 断点、布下后消费者缺席）；「同一条热指令上的巧合地址、非腐化链一环」高置信；但陷阱恰落在 PW-1 插桩窗、施动者身份 INSUFFICIENT（日志 §173；`lead\boot_hang_triage_20261018\SINGLESTEP_0x7CFC9F_ANALYSIS.md`） | E1/E2/E3 三实验未跑：E1=去包装配置+10Hz TF/DR 轮询至死、E2=摘 .mimosa hook 层 A/B（宿主插桩层列候选施动者）、E3=崩溃态 DR6 直读可并入 E1——留主会话＋用户在场串行、② 线排 T55 之后（日志 §174） | 附带勘误已入账：Esi=0x7FFFFFFF⇒请求 class=1（≤24B 小分配消费毒块）；「硬件断点已排除」降级为「未排除」（日志 §174） |

### C 类版本对账（专节 · P5 补遗）

**对账目标**：bench 侧「5 局里 2 局进程消失」（`docs\re\u0800_redesign_spec.md` §1 P3）vs Lead 线记忆「U0800 塌方 p50=0fps 但 W2 全存活」（日志 §102「H1 记忆在案」原句）。

| 维度 | bench 侧 | Lead 侧 | 对账判定 |
|---|---|---|---|
| 运行日期 | 2026-09-30（ZC-H1RM，RESULT_H1_REMEASURE META） | 记忆转述于 2026-10-18（日志 §102）；W2 原始记录日期不可考 | **不可对账**：W2 原始记录文件未定位，仅有 GOAL_HANDOFF_20261016.md L22 一句「W2 记录的选图漂移（协议假设 U0100，实测 U0800）」 |
| 地图/配置 | H1 新图 `[2]0LoadBench_U0800_H1.yrm`（H1FP1、100×100、cell 互斥、美vs蘇 UC10、units_seen=724）（RESULT [1]/[2]） | W2=旧代图（协议假设 U0100 漂移实测 U0800，sha/档名不可考）；Lead 自跑 T49（10-18）用第三张图=XMP29U2.MAP 缝补版 e3acc130、units0=491（日志 §103） | **三张图互不相同**；T49 的 491 单位读数（31fps 满帽＋终局冻结，日志 §106 勘误）不能互证 724 单位现象 |
| W2 窗定义 | —— | 两解并存：旧 W 系批次运行编号（GOAL_HANDOFF L22 口径，倾向此解）或 Lead harness 第三测量窗 W0/W1/W2 | **【待对账】**：盘面无 W2 原始记录件可仲裁 |
| 判据 | 「静默死亡」=进程级（wait_battle_ready 后 RPM 失联＋无 except）；「fps=0.0」=12s 窗零帧推进（RESULT [4.2] #1） | 「全存活」=进程活在（窗口级）；「p50=0fps」口径不明（fps p50 统计 or 窗零推进转述） | 两者可同时为真（同批 5 局 2 死 3 活、活局塌方），但**非同一记录**；「p50=0fps」与「fps=0.0 窗」口径无法对齐 |

**结论**：疑同源现象（同档 U0800 高载不稳）、非同一条证据；Lead 记忆句在盘面仅两处转述（日志 §102、GOAL_HANDOFF L22）、无第一手佐证件——**按 ②b 口径以 ① 管道重测 U0800 档生产新现场，即可替代历史对账**（日志 §204）。

---

## 表③ 安全改动能力

**Lead 评审结论（照录，日志 §202）**：③ 最成熟但有硬缺口；两硬缺口=**版本校验缺失**（DLL 安装无游戏版本/指纹门）＋**玩法配置混入默认**（玩法改动键混在默认 ini）；已有强项=**13/13 开关、卸载对称、联机门控**；次要缺口=**确定性对比、存档兼容未实测、运行中卸载未实测、25 个未用地址宏**。

| 项 | 现状（带证据路径） | 状态 |
|---|---|---|
| 硬缺口① 版本校验缺失 | 评审断言实测成立：`PatchVTablePointer` 仅查可读、无条件写；dllmain DLL_PROCESS_ATTACH 直接安装无任何指纹/时间戳核对（`lead\goal3_versioncheck_20261019\RECEIPT.md` §2） | 修复件 P1 已交付 |
| 硬缺口② 玩法配置混入默认 | 评审口径成立；P2 已盘点 ini 23 键全部读取点（`lead\goal3_configsplit_20261019\RECEIPT.md` §1） | 修复件 P2 已交付 |
| 强项 13/13 开关 | 安装 13 处（blitter_hooks.cpp:3702-3774）↔还原 13 处（:3812-3872）逐对成立，与 Lead 线历史核验一致（P1 RECEIPT §2；日志 §202/§204） | 已核验保持 |
| 强项 卸载对称 | `RemoveVTableHooks`=安装严格逆序＋sw→vxl→gap 逆序硬回滚；**例外已登记**：`PatchSpySatBuildingTypes` 无 Remove 对应件（进程级懒加载一次性；P2 拆分后默认=0 直接 return，不对称自动消解）（P2 RECEIPT §1） | 保持＋一处例外消解中 |
| 强项 联机门控 | MP 边沿同步 `MpGateEdgeSyncGapProtection` 单机→联机逆序回滚/联机→单机门禁重装（P2 RECEIPT §1）；MP-EDGE NC-1/2/5 长期挂起（GOAL L52） | 保持 |
| 次要缺口 确定性对比 | 补丁前后行为确定性 diff 流程未建（评审照录，日志 §202） | 未开工 |
| 次要缺口 存档兼容 / 运行中卸载实测 | 均未实测（评审照录，日志 §202） | 未开工 |
| 次要缺口 25 个未用地址宏 | 评审口径 25 个；本表快查（grep `#define ADDR_` 于 ra2render.h 计 96 个、未见 .cpp 引用者计 27 个）量级吻合、精确数待专核 | 已粗证、待专核 |
| 修复件 P1（版本校验补丁副本） | 已交付待独立核验：统一 diff 4 hunk＋补丁后整份副本＋编译自检产物；E1 写前核对期望旧值（不符拒写一字节不动）/E2 SHA-256 启动门（BCrypt）/E3 13 处虚表期望值表/E4 9 处直改位点表/E5 三道门全过才允许首笔写/版本门无 ini 开关无旁路（`lead\goal3_versioncheck_20261019\RECEIPT.md` §1） | **已交付，待独立核验＋施用** |
| 修复件 P2（玩法配置拆分补丁副本） | 已交付待独立核验：四键迁 [Gameplay] 默认关＋老用户迁移路径＋卸载对称判据④；语法门过（/Zs 零错零警）、未做完整链接（`lead\goal3_configsplit_20261019\RECEIPT.md` §0/§1） | **已交付，待独立核验＋施用** |
| P1/P2 验收判据补遗（已送） | P1=1 字节篡改整体不安装＋原版可跑/vtable 13 处＋直改 8 处全核/拒绝原因逐条留日志；P2=运行时生效值日志读回全关/老用户迁移保持/联机门控不变/卸载对称（日志 §204） | 判据在册待用 |
| 身份白名单基准（版本门语义） | 用户裁定 M-1 已落册：首版补丁白名单仅接受 W-A 指纹 73201cc0…67476、W-B 降候选、诊断≠补丁（`crashspec_v4\M1_RULING_ANNOTATION.md` §1） | 已生效，P1 白名单须遵此口径 |
| 保持态 | 全天 20+ 趟零母本污染、零语料写入；补丁副本制（builder 不碰母本）贯穿 P1/P2（GOAL L50；日志 §202） | 保持 |

**【待对账】口径注记**：评审「13/13 开关」指钩子安装/还原对（P1 回执已证实）；P2 回执另指认 Lead「13/13 配置键对应」与母本不符、实测 **23/23**（13 恰为本次迁入 [Gameplay] 的键数，疑口径错位）——两处「13/13」语义不同已并存落表，待 Lead 确认评审原意后统一。；**【2026-10-20 00:5x Notion 裁决定谳（日志 §244）】**：两者不同源各管各——配置键对应以 **23/23** 为准（P2 回执实测，5 节 23 键读取与 ini 一一对应；旧 INSTALLED_HOOKS_AUDIT 的「配置 13/13」基于 1757 行旧快照，作废），虚表安装/还原对以 **13/13** 为准（P2 RECEIPT:36 独立印证）；「13 迁入键数」纯属巧合；本表计数今后一律标来源快照（行数/哈希）

---

## 附：本表制作说明

- 只读汇总口径：全部事实取自上文索引所列盘面文件；P1/P2 回执（19:22/19:23 落盘）晚于日志 §204（19:17），已按"盘面产物为准"原则并入表③。
- 25 个未用地址宏的快查方法：`grep "#define ADDR_" ra2render/ra2render.h` 全集 96 个，逐一在 `ra2render/*.cpp` 检索引用、无命中者计 27——与评审"25 个"量级吻合但非同一口径的精确复算。
- 本文零裁决：所有"待对账/待测/下一步"均为登记，判定权在 Lead/用户。
