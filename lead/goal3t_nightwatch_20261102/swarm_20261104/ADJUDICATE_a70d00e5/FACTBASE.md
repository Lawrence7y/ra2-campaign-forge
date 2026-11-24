# 第一步事实底账（2026-11-04）

本件只登记已确认事实、材料间不一致和验证范围，不选择 D-15 / D-13 的方案，不授予任何 E3 执行权限。

本次读取材料与原始 JSON；未启动 gamemd.exe / ra2loader.exe / YURI，未 taskkill，未读取运行中进程内存，未执行材料中的发射命令。所有显式写入均限于 `D:/Project/ra2-campaign-forge/lead/goal3t_nightwatch_20261102/swarm_20261104/ADJUDICATE_a70d00e5/`，未修改既有台账、PENDING、核验件或真机 json/png，未 commit。

## 一、已读材料与引用约定

下文的 M/G/H/Q/P/L/F/I/S 均指本表中的绝对路径；其后的行号指本次工作树实际行号。

| 代号 | 已读文件、范围 |
|---|---|
| M | [S544_TRI_MODEL_VERDICT_20261104.md](D:/Project/ra2-campaign-forge/lead/goal3t_nightwatch_20261102/swarm_20261104/S544_TRI_MODEL_VERDICT_20261104.md:1)，全文 1–234 行 |
| G | [gemini VERDICT.md](D:/Project/ra2-campaign-forge/lead/goal3t_nightwatch_20261102/swarm_20261104/XVERIFY_S544_ae38d56c/VERDICT.md:1)，全文 1–106 行 |
| H | [hy4free VERDICT.md](D:/Project/ra2-campaign-forge/lead/goal3t_nightwatch_20261102/swarm_20261104/XVERIFY_S544_c1606d35/VERDICT.md:1)，全文 1–122 行 |
| Q1 | [qfmodel V1/REPORT.md](D:/Project/ra2-campaign-forge/lead/goal3t_nightwatch_20261102/swarm_20261104/XVERIFY_S544_7255362d/V1/REPORT.md:134)，134–213 行，含判定摘要 |
| Q2 | [qfmodel V2/REPORT.md](D:/Project/ra2-campaign-forge/lead/goal3t_nightwatch_20261102/swarm_20261104/XVERIFY_S544_7255362d/V2/REPORT.md:242)，242–289 行，含结论与局限 |
| Q3 | [qfmodel V3/REPORT.md](D:/Project/ra2-campaign-forge/lead/goal3t_nightwatch_20261102/swarm_20261104/XVERIFY_S544_7255362d/V3/REPORT.md:20)，1–33、221–264 行，含结论与重跑预测 |
| Q3R | [qfmodel V3/RECHECK.md](D:/Project/ra2-campaign-forge/lead/goal3t_nightwatch_20261102/swarm_20261104/XVERIFY_S544_7255362d/V3/RECHECK.md:177)，174–196 行，补查重跑预测原话 |
| P | [PENDING_DECISIONS.md](D:/Project/ra2-campaign-forge/lead/PENDING_DECISIONS.md:22)，D-15 全文 22–77、D-13 全文 79–102 行 |
| F | [_LEADER_FROZEN_29_20261104.md](D:/Project/ra2-campaign-forge/lead/goal3t_nightwatch_20261102/swarm_20261104/_LEADER_FROZEN_29_20261104.md:1)，全文 1–154 行 |
| I | [_LEADER_FREEZE_INSTANT_20261104.md](D:/Project/ra2-campaign-forge/lead/goal3t_nightwatch_20261102/swarm_20261104/_LEADER_FREEZE_INSTANT_20261104.md:1)，全文 1–115 行 |
| S | [S543_FREEZE_WAS_SCORESCREEN_20261104.md](D:/Project/ra2-campaign-forge/lead/goal3t_nightwatch_20261102/swarm_20261104/S543_FREEZE_WAS_SCORESCREEN_20261104.md:1)，全文 1–277 行 |
| L | [GOAL_THREE_TARGETS_20261018.md](D:/Project/ra2-campaign-forge/lead/GOAL_THREE_TARGETS_20261018.md:4361)，先 rg 定位；读取 3800–3839、3890–3937、4003–4038、4091–4133、4266–4323、4361–4487 行，未整读 |

qfmodel 目录已用 `rg --files` 列出，未见其汇总 VERDICT；本次只按实际存在的 V1/V2/V3 及补查的 V3 RECHECK 引用，不把它写成第三份已完成的汇总判定书。M:216–217、L:4372 也明确记载其未跑汇总步。

另只读了 harness 的 `_measure_stats` 源码 4730–4818 行及 Q1 既有脚本前 92 行来辨认数据结构；实际抽查使用本目录新脚本，未执行已有核验脚本，也未导入 harness。

## 二、本次实际执行的三项数字抽查

执行命令如下，退出码 **0**，2026-11-04 **12:32:44–12:32:45 UTC**。时间、实际解释器路径和完整输出已保存于 [factbase_probe_output.txt](D:/Project/ra2-campaign-forge/lead/goal3t_nightwatch_20261102/swarm_20261104/ADJUDICATE_a70d00e5/factbase_probe_output.txt:1)。

```bash
python -I -X utf8 'D:/Project/ra2-campaign-forge/lead/goal3t_nightwatch_20261102/swarm_20261104/ADJUDICATE_a70d00e5/factbase_probe.py' --data-root 'D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip' --output-dir 'D:/Project/ra2-campaign-forge/lead/goal3t_nightwatch_20261102/swarm_20261104/ADJUDICATE_a70d00e5'
```

### a. 两层文件数及可推进数

独立递归枚举该指定数据根的全部 `measure_w*.json`，再按目录深度分账；`df` 由原始 `samples.f[-1]−samples.f[0]` 计算，至少须有两个配对样点。代码：[factbase_probe.py:20](D:/Project/ra2-campaign-forge/lead/goal3t_nightwatch_20261102/swarm_20261104/ADJUDICATE_a70d00e5/factbase_probe.py:20)、[同脚本:40](D:/Project/ra2-campaign-forge/lead/goal3t_nightwatch_20261102/swarm_20261104/ADJUDICATE_a70d00e5/factbase_probe.py:40)。

| 层级 | JSON 份数 | 原始样点净 df>0 窗数 |
|---|---:|---:|
| 根目录 | 3 | 0 |
| 一层子目录（各趟） | 101 | 63 |
| 更深层 | 0 | 0 |
| 合计 | **104** | **63** |

精确输出（输出件:4–8）：

```text
A recursive_total=104 parsed=104 parse_errors=0
A root: files=3 df_positive=0
A child: files=101 df_positive=63
A deeper: files=0 df_positive=0
A total_df_positive=63 nonpositive_or_insufficient=41
```

根层 w0 的 `trip_id=QC161-U0400-T55j`，w1/w2 为 `QC161-U0400-T55h`；三个净 df 均为 0（输出件:9）。因此根目录不是一个统一 trip，不能直接拿目录名代替独立趟 ID。

**与材料的关系**：104/63/41 与 M:160–168、L:4391–4399 一致。S:180–189 的 98+3=101 是较早切面；G:57 的 103 也不是当前切面。H:112 记载从 103 到 104 是新增 v4h 空样本窗，本次未追溯所有历史切面，只确认当前数目。读取前后文件集合、大小、mtime_ns 无变化（输出件:23），这是本次读取期间的稳定性检查，不是对全仓历史完整性的证明。

### b. 两种慢窗筛选的差值

严格使用题定的 JSON **`stats.fps_avg` 与 `stats.fps_p50`** 筛选，null 不参与数值比较；没有把 p50 当成已获批准的主指标。代码：[factbase_probe.py:81](D:/Project/ra2-campaign-forge/lead/goal3t_nightwatch_20261102/swarm_20261104/ADJUDICATE_a70d00e5/factbase_probe.py:81)。

| 窗集 | avg<28 | avg<28 且 p50<28 | 两者相差 |
|---|---:|---:|---:|
| 全部 104 份 | **38** | **24** | **14** |
| `span_s=25.0` | **33** | **22** | **11** |
| `span_s=4.0` | **5** | **2** | **3** |

精确输出（输出件:10–15）：

```text
B all: avg_lt28=38 avg_and_p50_lt28=24 difference=14
B 25s: avg_lt28=33 avg_and_p50_lt28=22 difference=11
B 4s: avg_lt28=5 avg_and_p50_lt28=2 difference=3
B positive_25s=58 positive_4s=5 healthy_25s=25
B 25s_low_both: windows=22 trip_ids=8 min_stall_s=0.103742 max_stall_s=0.749879
B 25s_low_avg_high_p50: windows=11 trip_ids=11 trip_overlap=0
```

22 窗的 8 个 `trip_id` 及 5 个 4 秒窗的完整绝对路径见输出件:16–17，与 M:162、171–173 和 P:58–59 的名单对应。22 窗与 11 个 25 秒低 avg、高 p50 窗的趟集合交集为 0。本次确认的是 avg/p50 筛选、名义时长和趟数；**没有全库重新计算派生 `live_fps`**，因此 M 的“三口径全低”仍部分属于已读核验结论，不冒充三项均由本次独立重算。

### c. T34/w0：采样缺口与最长零推进段

原始文件：`D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip/archive_T34/measure_w0.json`。

对所有相邻 `samples.t` 计算 dt，累计 **dt>0.010 秒的整个 dt**；最长停顿按 harness 的“值变化时刻减该值段起点，包含窗尾”定义独立重建。代码：[factbase_probe.py:103](D:/Project/ra2-campaign-forge/lead/goal3t_nightwatch_20261102/swarm_20261104/ADJUDICATE_a70d00e5/factbase_probe.py:103)、[同脚本:104](D:/Project/ra2-campaign-forge/lead/goal3t_nightwatch_20261102/swarm_20261104/ADJUDICATE_a70d00e5/factbase_probe.py:104)；定义来源：[qc151_trip.harness8_v4.py:4742](D:/Project/ra2-campaign-forge/lead/goal1_harness8_20261031/qc151_trip.harness8_v4.py:4742)、[同源码:4773](D:/Project/ra2-campaign-forge/lead/goal1_harness8_20261031/qc151_trip.harness8_v4.py:4773)。

精确输出（输出件:19–22）：

```text
C n_samples=12502 nominal_span_s=25.0 measured_span_s=24.999840000004 f_first=293 f_last=302 df=9
C dt_gt10ms_count=0 dt_gt10ms_sum_s=0.000000000000 dt_max_ms=3.887000 nonpositive_dt=0
C zero_advance_max_s=24.734759999992 rounded_6=24.734760 stored_max_stall_s=24.734761 frame=302 start_rel_s=0.265080000012 end_rel_s=24.999840000004
C fps_avg_recomputed=0.360002304015 stored_fps_avg=0.36000229681454066 stored_fps_p50=31.608659530882008 edges_recomputed=10 stored_edges_match=True
```

**确认**：采样无 >10ms 缺口，累计 **0 秒**；帧号仅推进 9 帧，随后约 **24.734760 秒**停在 302，但存储 p50 仍为 **31.608660 fps**。与 M:40–42、H:33、Q1:173–177 的核心转述一致。

**微差如实记录**：重建停顿四舍五入至 6 位为 24.734760，JSON 原存 `max_stall_s` 为 24.734761，相差 1 微秒；重新计算 avg 与原存 avg 也有约 7.2e-9 fps 的差别。该差量与时间戳落盘精度相容，但本次未追查完整序列化舍入链，不宣称逐位相等。这些微差不影响阈值分类。零缺口只证明本窗未出现题定的采样间隔异常，不能据此排除一切宿主扰动，更不能单独判定停顿原因。

## 三、确认存在的材料冲突及转述边界（不作方案裁决）

| 事项 | 本次从文件确认了什么 | 证据 |
|---|---|---|
| **D-15 正文与修订段冲突** | 正文把“29 冻结窗”转为“38 慢窗”；修订段改为“33 个 25 秒慢窗=22 全程低速+11 停摆主导”，另有 5 个 4 秒窗。二者不是同一可用样本定义。修订段已明写“取代”，但旧正文与选项仍同时存在。当前数据抽查支持后一个分层数字，38 则确实是未经时长分层的全量 avg<28 数。 | P:24–38、50–63；M:178–179；本件二 b |
| **D-15 选项仍残留旧状态/数字** | B 仍写“等两路独立核验回件”；M 已报告核验结果。C 仍用“那20张”，而修订段已写 22/27。这里只登记选项文本滞后，不替其选择方案。 | P:49、69–71；M:18–28、117 |
| **23 与 22 并非三路逐字一致** | G 的最终盘点写 23 个真慢窗；H 写 22 个 25 秒真慢窗。M 已公开此分歧并写本线复算采用 22；本次 25 秒双阈值计数确为 22。M 对 G 多算 `k` 的归因是材料记载，本次未复跑 G 的分类脚本来验证其具体误分路径。 | G:64、68–70；H:71–76；M:187；本件二 b |
| **终局覆盖被部分表述扩大** | P 正文的“df==0就是对局结束”、D-13 补注的“那些窗是已结束态”是泛化表述；M 同时只给 21/32 的冻结窗终局证据覆盖。更早 S 已明列 11 个无充分证据的冻结窗。本次没有独立读图，不把全部零推进窗定性为终局。 | P:31、80–81；M:199–205；S:218–230 |
| **11 个停摆主导窗全部终局，材料仍有边界** | M:204、P 的 A 选项、L:4464 把这 11 个窗写成终局态；H 对其表述更窄：10/11 所在趟后续有整窗零推进，`l3_20261023q/w2` 唯一无后续零推进，须挂账。两类“11”（低 avg 高 p50 的有推进窗、32 个冻结窗中无证据的11窗）也不是同一个集合。不能从筛选类别本身推出全部终局。 | M:175–176、204；P:66；H:73；S:218–230；本件二 b |
| **汇总件对 qfmodel 的“只是版本效应”归述失真** | M 剩余分歧表把 qfmodel 放在“只是版本效应=是”一栏，但已读 Q2 的结论明写“时代与版本/协议效应无法分离，不能作为结论”，其局限还说三者结构性不可分辨。原报告支持混杂/不可分离，不能据该表断言 qfmodel 已证明“仅版本导致”。 | M:188；Q2:271–278、286–288；L:4454 有同样归述 |
| **汇总件把 qfmodel 的重跑预测强化为“必过”** | M:132 写“三路，尤其 qfmodel V3-A2，建议补参重跑必过”。Q3 原文只写“大概率成功”，并承认约25%的 timeout；Q3R 又在读到 v4h 后把原成功率预测判 REFUTED。因此“必过”不是 qfmodel 这些已读结论段的忠实转述。G 则确有“预期100%成功”的原话，不能把各路强度合并。 | M:132–135；Q3:226–231；Q3R:177–194；G:89–100；L:4433 同样写“三路建议必过” |

还有一处引用定位问题：散件 F 的标题自称“§538 战斗段完全冻结”，I 自称“§539 冻结精确时刻”；当前上游台账实际 §538 是维护核查（L:3800），§539 是 P05 对照（L:3890），内容并非这两份散件标题。因此后续引用已按**文件名+实际行号**区分，不把章节号等同于同一篇原文。

## 四、与 D-13 直接相关、已确认但尚未裁决的事实

1. **现行 D-13 的对象、触发和授权范围尚未统一**。P:83–90 记载原 E3 服务目标②、触发 `latch_detected`，迁移到目标①则提议“帧号停推超 N 秒”；P:92–100 备选 A 为 N=1.0s 长停，C 为 SuspendThread+StackWalk64，另有暂停，并另问是否仅限候选件与离线单测。P:82、100 明示未裁前不执行。这是条目内容，未在本步验证其历史授权来源，也未授予新权限。
2. **22 个低速窗不等于 ≥1s 长停窗**。本次按 25 秒、avg<28、p50<28 识别的 22 窗，其 JSON 记录 `max_stall_s` 在 **0.103742–0.749879s**（输出件:14；本件二 b）。因此按记录值，D-13 的 N=1.0s 谓词在这组已观测历史窗中的覆盖是 **0/22**。这里是阈值比较的逻辑结果，未逐窗重算这 22 个 max_stall，也不预测未来趟次。M:204 / P:66 的“改绑22窗”本身没有解决这个触发覆盖差异。
3. **保持 avg 为主指标是已读核验材料的共同方向**：Q1:152–164、H:38、M:49–50 均明确反对用 p50/live 代替体验指标；本次 T34 抽查提供了该分型差异的直接数据。源码也直接称 avg 为主对照指标，并仅把 df==1 的沿差放入 p50 样本（[qc151_trip.harness8_v4.py:4733](D:/Project/ra2-campaign-forge/lead/goal1_harness8_20261031/qc151_trip.harness8_v4.py:4733)、[同源码:4794](D:/Project/ra2-campaign-forge/lead/goal1_harness8_20261031/qc151_trip.harness8_v4.py:4794)）。本步登记这一事实，不新设验收门槛。

## 五、证据与判断的边界

- **本次直接运行确认**：指定数据根的全量104份/两层分账/63净正推进；38→24与25秒33→22的双筛差；25秒58/健康25、22窗8趟及11窗11趟零交集；T34采样缺口、帧差、停顿和帧沿一致性。两层遍历无缩小规模替代。计数与筛选主要读取原存 stats，T34 才逐样点独立重建停顿与 avg。
- **本次直接阅读确认**：D-15 两段自相矛盾；D-13 的现行触发方案与禁执行句；各路文字的分歧、qfmodel 无汇总件，以及上述转述强化。对“全部终局”的证据不足属于从已读材料覆盖范围作出的判断，未冒充新读图结论。
- **未运行/未验证**：PNG目视或OCR、截图sha/mtime复核、107份异常件普查、全部argv/BOOT归属复算、ρ/φ重算、12份镜像逐字节比对、完整实时速度机制、1734段/87.7%短停分布及N=1s历史误触率。它们如在已读材料中出现，仍仅是材料记载。未运行任何真机、E3、项目测试或部署命令；这些不是本步的检查要求。
- **产物**：本件 FACTBASE.md；[factbase_probe.py](D:/Project/ra2-campaign-forge/lead/goal3t_nightwatch_20261102/swarm_20261104/ADJUDICATE_a70d00e5/factbase_probe.py:1)；[factbase_probe_output.txt](D:/Project/ra2-campaign-forge/lead/goal3t_nightwatch_20261102/swarm_20261104/ADJUDICATE_a70d00e5/factbase_probe_output.txt:1)。本步不写裁决书，不修改 PENDING 或台账。
