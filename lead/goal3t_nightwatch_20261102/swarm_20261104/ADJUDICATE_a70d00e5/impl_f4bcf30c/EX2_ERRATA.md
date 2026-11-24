# EX-2「追加勘误候选」（域内候选件，2026-11-04）

本件是 `RULING.md` EX-2 行的落实候选稿，**历史原文不改**：台账 `GOAL_THREE_TARGETS_20261018.md`、`PENDING_DECISIONS.md`、`RULING.md`、`RECHECK.md`、`FACTBASE.md`、三路核验件与真机 json/png 全程只读；本件只写入指定写域 `.../ADJUDICATE_a70d00e5/impl_f4bcf30c/EX2_ERRATA.md`。未启动 gamemd.exe / ra2loader.exe / YURI，未 taskkill，未读活进程内存，未 commit，未产生任何采样/注入/运行期探针脚本。正文块（第 2 节）可整段追加到台账末尾；第 0、1、3 节是交付说明，不属于追加内容。

**本件的立场**：只撤销肯定归因的强度，不建立反向全称结论（`RULING.md:5`、`RULING.md:102`、`RULING.md:180`）。每处引用写「文件名 + 该件实际行号」；文件全路径见第 1 节。

## 0. 本件实际执行的检查（命令与输出）

**检查 A：grep 台账确认同号章节的实际行号**（只读，退出码 0）：

```bash
grep -n -E "^# §5(3[89]|4[0-4])|^## §544" "D:/Project/ra2-campaign-forge/lead/GOAL_THREE_TARGETS_20261018.md"
```

实际 stdout：

```text
3800:# §538　唤醒轮（维护+核查，零新分析）：**BOOT#9 稳定（uptime 42min，双轴未变）**；
3890:# §539　**P05（他会话中间产物）与本线 §529 的冲突辨析：不冲突，两段不重叠**（纯离线核查，零真机）：
4003:# §540　**P01（他会话已完成报告）重大发现：帧冻结机制已字节级定谳** —— 本线**独立核验三条核心断言全部通过**：
4091:# §541　**`dwfrun-169a2a53` 已 completed（3576 万 tokens）——`BATCH1_VERDICT.md` 收敛：5 项全 CONFIRMED**；
4207:# §543　**★ 重大反转（自我纠错）：所谓「29 个战斗段完全冻结窗」绝大多数是对局打完后的「遭遇战得分」结算屏** ——
4361:## §544 · 三模型独立核验：§543/§544 两次改判被收敛（2026-11-04）
```

**检查 B：`l3_1101v4c` 三窗字段身份核对**（`python -I -X utf8`，绝对路径，只读原始 JSON，退出码 0）。这是一次只读字段核对，未产生脚本文件、非采样/注入/运行期探针：

```bash
python -I -X utf8 -c 'import json; from pathlib import Path
root=Path("D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip/l3_1101v4c")
for w in range(3):
 p=root/("measure_w%d.json"%w); d=json.loads(p.read_text(encoding="utf-8-sig")); e=d["frame_edges"]; live=(e[-1][0]-e[0][0])/(e[-1][1]-e[0][1])
 print(json.dumps({"path":p.as_posix(),"stored_stats_fps_avg":d["stats"]["fps_avg"],"stored_stats_fps_p50":d["stats"]["fps_p50"],"derived_live_fps_first_to_last_edge":live,"has_stored_live_fps":("live_fps" in d or "live_fps" in d["stats"])},ensure_ascii=False))'
```

实际 stdout：

```text
{"path": "D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip/l3_1101v4c/measure_w0.json", "stored_stats_fps_avg": 18.520948494813613, "stored_stats_fps_p50": 19.81123852234025, "derived_live_fps_first_to_last_edge": 18.539626790502314, "has_stored_live_fps": false}
{"path": "D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip/l3_1101v4c/measure_w1.json", "stored_stats_fps_avg": 28.40179635682234, "stored_stats_fps_p50": 30.2016260596662, "derived_live_fps_first_to_last_edge": 28.416096013424877, "has_stored_live_fps": false}
{"path": "D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip/l3_1101v4c/measure_w2.json", "stored_stats_fps_avg": 30.681571141892938, "stored_stats_fps_p50": 30.84258868525148, "derived_live_fps_first_to_last_edge": 30.70530239738328, "has_stored_live_fps": false}
```

**检查 C**：追加正文的「已撤回旧支柱」禁用扫描在成文后执行，零命中；为避免把被撤回的数值/定性重新写进本件，扫描式样与输出不落在本文件内，记于交付结果的第 5 条验收自查。

**未做的检查（如实登记）**：未重跑 104 份全库重建、未重算 22 窗整体覆盖率、未新读/OCR 任何 PNG、未核截图时序/哈希、未做真机发射或运行期实验、未跑项目测试。21/32 覆盖与计分屏判定沿用已读原件，不冒充本件独立复核（`RULING.md:197`、`RECHECK.md:82`）。

## 1. 文件全路径对照（供第 2 节每个「文件名:行号」解析）

| 本件使用的文件名 | 绝对路径 |
|---|---|
| `RULING.md` | `D:/Project/ra2-campaign-forge/lead/goal3t_nightwatch_20261102/swarm_20261104/ADJUDICATE_a70d00e5/RULING.md` |
| `RECHECK.md` | `D:/Project/ra2-campaign-forge/lead/goal3t_nightwatch_20261102/swarm_20261104/ADJUDICATE_a70d00e5/RECHECK.md` |
| `FACTBASE.md` | `D:/Project/ra2-campaign-forge/lead/goal3t_nightwatch_20261102/swarm_20261104/ADJUDICATE_a70d00e5/FACTBASE.md` |
| `EX1_DATAFACE.md` | `D:/Project/ra2-campaign-forge/lead/goal3t_nightwatch_20261102/swarm_20261104/ADJUDICATE_a70d00e5/impl_f4bcf30c/EX1_DATAFACE.md` |
| `GOAL_THREE_TARGETS_20261018.md` | `D:/Project/ra2-campaign-forge/lead/GOAL_THREE_TARGETS_20261018.md` |
| `_LEADER_FROZEN_29_20261104.md` | `D:/Project/ra2-campaign-forge/lead/goal3t_nightwatch_20261102/swarm_20261104/_LEADER_FROZEN_29_20261104.md` |
| `_LEADER_FREEZE_INSTANT_20261104.md` | `D:/Project/ra2-campaign-forge/lead/goal3t_nightwatch_20261102/swarm_20261104/_LEADER_FREEZE_INSTANT_20261104.md` |
| `S543_FREEZE_WAS_SCORESCREEN_20261104.md` | `D:/Project/ra2-campaign-forge/lead/goal3t_nightwatch_20261102/swarm_20261104/S543_FREEZE_WAS_SCORESCREEN_20261104.md` |
| `S544_TRI_MODEL_VERDICT_20261104.md` | `D:/Project/ra2-campaign-forge/lead/goal3t_nightwatch_20261102/swarm_20261104/S544_TRI_MODEL_VERDICT_20261104.md` |
| `PENDING_DECISIONS.md` | `D:/Project/ra2-campaign-forge/lead/PENDING_DECISIONS.md` |

---

## 2. ★ 以下整段为可直接追加到台账末尾的勘误正文（历史原文不改）

<!-- BEGIN APPENDABLE ERRATA -->

### §545 · 勘误（2026-11-04）：撤销整批「在战引擎停摆」的肯定归因（追加节，原文不改）

> 本节为**追加勘误节**，`GOAL_THREE_TARGETS_20261018.md:3800`（§538 唤醒轮）、`GOAL_THREE_TARGETS_20261018.md:3890`（§539 P05 冲突辨析）、`GOAL_THREE_TARGETS_20261018.md:4003`（§540）、`GOAL_THREE_TARGETS_20261018.md:4091`（§541）、`GOAL_THREE_TARGETS_20261018.md:4207`（§543）、`GOAL_THREE_TARGETS_20261018.md:4361`（§544）及各散件的历史原文**一律不改、不删、不就地覆写**；裁定依据 `RULING.md:97`（D-15.2「追加勘误节，不就地改写，也不维持原叙事有效」）与 `RULING.md:167`（EX-2 行）。本节撤销的是**归因**，不改写任何原始读数。

#### 545.1 来源定位（防止同号错引）

历史散件 `_LEADER_FROZEN_29_20261104.md:1` 自题「§538 战斗段完全冻结：29 窗定谳」、`_LEADER_FREEZE_INSTANT_20261104.md:1` 自题「§539 冻结的精确时刻：从满速到零推进的断崖」，与台账 `GOAL_THREE_TARGETS_20261018.md:3800` 的 §538（唤醒轮·维护核查，该件 `:3806` 自记「本件不含任何机制结论」）及 `GOAL_THREE_TARGETS_20261018.md:3890` 的 §539（P05 与 §529 冲突辨析）**不是同一篇文章**（`RULING.md:187` 材料冲突表「低」行）。因此本节所有引用一律写「文件名 + 该件实际行号」，不单写章节号；台账同号章节的实际行号已由本轮 `grep -n` 核实为 `GOAL_THREE_TARGETS_20261018.md:3800` / `GOAL_THREE_TARGETS_20261018.md:3890` / `GOAL_THREE_TARGETS_20261018.md:4003` / `GOAL_THREE_TARGETS_20261018.md:4091` / `GOAL_THREE_TARGETS_20261018.md:4207` / `GOAL_THREE_TARGETS_20261018.md:4361`（完整命令与 stdout 见本件第 0 节检查 A；`RULING.md:34` 把台账代号固定为 L，`RULING.md:19–39` 固定各件全路径）。

#### 545.2 明确撤销的四项归因

1. **撤销「整批是战斗段完全冻结」**。`_LEADER_FROZEN_29_20261104.md:12`（判据 `f0!=0 且 df==0` 计 29 窗）、`_LEADER_FROZEN_29_20261104.md:17`（称「真正的绝对多数现象」）、`_LEADER_FROZEN_29_20261104.md:109`（R1「整窗冻结」29 窗、25s 零推进）所下的「**战斗段**」定性超出读数：这些读数只说明窗内帧号零推进，不说明当时处于战斗阶段（`RULING.md:97`、`RULING.md:101`）。`S543_FREEZE_WAS_SCORESCREEN_20261104.md:133` 与 `S544_TRI_MODEL_VERDICT_20261104.md:199–200` 亦记该叙事须降级。
2. **撤销「引擎停摆已定谳」**。`_LEADER_FREEZE_INSTANT_20261104.md:81–88`（「目标①的实测形态现已确定」→「这正是『引擎停摆』而非『崩溃』、也非『变慢』」）及 `GOAL_THREE_TARGETS_20261018.md:4054`（§540 §四「『帧冻结』的机制已被字节级定谳，不再是黑箱」）中，**把「已定谳」当作运行期因果/定位结论**的部分撤销；台账自身已在 `GOAL_THREE_TARGETS_20261018.md:4075` 把「目标①本质是被主动挂起」登记为「属推测性归纳，未经独立验证」，并在 `GOAL_THREE_TARGETS_20261018.md:4134–4135` 把两个行为学问题判为 DATA_INSUFFICIENT / 单通道不可分辨（`RULING.md:97`、`RULING.md:197`）。**§540/§541 的静态字节事实不随本项撤回**，见 545.3(2)。
3. **撤销「永不恢复」被用作超出观察窗的机制结论**。`_LEADER_FROZEN_29_20261104.md:95`（「再未恢复」）、`_LEADER_FROZEN_29_20261104.md:131`（「某个点之后就永久冻结了」）、`_LEADER_FREEZE_INSTANT_20261104.md:55`（「永不恢复」）、`_LEADER_FREEZE_INSTANT_20261104.md:74`（「从不恢复」）、`_LEADER_FREEZE_INSTANT_20261104.md:85`（「状态永久保持」）的**窗内观测**（后续 25 秒窗 `df=0`、帧号恒等于前窗末值）保留；被撤销的是把它外推为「引擎永久停摆、永不恢复」这一**超出观察窗范围的机制结论**（`RULING.md:97`、`RULING.md:102`）。`_LEADER_FREEZE_INSTANT_20261104.md:98` 自己已记该表述与 T38 存在「细微不符」。
4. **撤销「凭窗口停帧形态证明某条静态路径已在历史趟命中」**。`_LEADER_FROZEN_29_20261104.md:133–134` 以「形态上吻合」关联 §533 免-inc 出口（同件 `:134` 自记「矛盾未解」），`_LEADER_FREEZE_INSTANT_20261104.md:100–102` 自陈「本件没有把冻结与任何引擎机制关联起来」且 §533 假说「进一步被弱化」；`GOAL_THREE_TARGETS_20261018.md:4058–4063`（§540 §四「挂起计数器 → 免-inc 出口」解读）不得据窗口停帧形态升格为历史趟的运行期命中（`RULING.md:155`「已有静态反汇编只列『静态事实/候选路径』，不能把可达路径写成历史运行期命中」、`RULING.md:197`）。**可达的静态路径 ≠ 历史运行期命中**；运行期是否命中的证据为「缺」（见 545.3(2)）。

**本节撤销的是肯定归因，不是已证相反结论**：不得据此改写成「32 窗全部已证正常终局」或「全部冻结窗都不是引擎停摆」（`RULING.md:5`、`RULING.md:102`、`RULING.md:180`）；理由是撤销旧肯定结论的充分证据，不构成对全称相反命题的证明（`RULING.md:101–102`）。

#### 545.3 保留项：原始读数与 §540/§541 静态字节结论

**(1) 原始读数全部保留、不撤回、不改写。** 帧号、时间、零推进计数照旧有效：`_LEADER_FROZEN_29_20261104.md:51–63` 的三趟三窗字节级读数（`archive_T32` w0 `f=[296,778]` `df=482` `max_stall=9.575s`、w1/w2 `f=[778,778]` `df=0` `max_stall=24.999s`、`t_abs0=1792285955.9/1792285980.9/1792286006.0`；`archive_T38` w0 `f=[130,910]` `df=780`、w1 `f=[911,940]` `df=29` `max_stall=24.077s`、w2 `f=[940,940]` `df=0`；`l3_20261023r` w0 `f=[3100,3883]`、w1 `f=[3883,4367]`、w2 `f=[4367,4367]` `df=0` `max_stall=24.998s`）、`_LEADER_FROZEN_29_20261104.md:40–41`（`f0=3514` / `3594`、`df=0`、`4.000s`）、`_LEADER_FREEZE_INSTANT_20261104.md:10`（T32 w0 `frame_edges` 483 条、`f=[296,778]`、`span=25.0s`、`max_stall_s=9.574`）、`_LEADER_FREEZE_INSTANT_20261104.md:15–30`（末 12 个帧沿、`f=778` 落在 `t=15.42s`、此后 9.58 秒帧号恒为 778）、`_LEADER_FREEZE_INSTANT_20261104.md:66–75`（`f0!=0` 29/29、`df==0` 29/29、`max_stall_s≈窗长`、`rc=0` 正常退出）均不改动（`RULING.md:97`「保留原始帧号、时间、零推进等读数」）。上一阶段从 104 份原始 JSON 只读重建的 41 个零/负推进或样点不足窗及其逐窗首末帧号，见 `EX1_DATAFACE.md:265–313`（重建命令与输出见 `EX1_DATAFACE.md:11–15`）；按 `RULING.md:85`，这 41 窗**不得统称 41 个冻结**。

**(2) `GOAL_THREE_TARGETS_20261018.md:4003`（§540）与 `GOAL_THREE_TARGETS_20261018.md:4091`（§541）的静态字节结论不随本次勘误撤回**：`GOAL_THREE_TARGETS_20261018.md:4041–4050` 的四条字节断言复算（`0x55D877` 处 `c3`、`0x684174` 为 `inc [eax+0x62C]`、MLF 三 ret、`[0xA8B230]` 三写点，`:4050` 判「四条全部通过」）与 `GOAL_THREE_TARGETS_20261018.md:4114–4128` 的 `BATCH1_VERDICT.md` 字节主线表（`+0x62C` 挂起深度计数器写点恰 3 处、`0x55D877` 双门、`CurrentFrame` 唯一 RMW 链）按「静态事实／候选路径」全部保留（`RULING.md:97`「静态字节结论与运行期因果归因分开，§540/§541 字节结论不得随此自动撤回，也不得继续冒充运行期定位证据」、`RULING.md:155`）。**但它们不得再冒充运行期定位证据**：台账 `GOAL_THREE_TARGETS_20261018.md:4067–4075`（语义推断链未复核、P01 未经异族核验、§四解读属推测）与 `GOAL_THREE_TARGETS_20261018.md:4130–4137`（行为学问题不可判定）已自陈这一限度（`RULING.md:197`）。**运行期耗时落点、以及该静态路径在历史趟是否命中：缺**；已查阅 `RULING.md:155`、`RULING.md:197`、`RULING.md:202`、`_LEADER_FREEZE_INSTANT_20261104.md:100–102` 仍无该证据，按「缺」登记，不据其他窗/其他趟/推理补值（`RECHECK.md:82` 记本线未新读 PNG、未核截图时序/哈希、未做运行期实验）。

#### 545.4 证据范围写死：21/32，不是全部

对经来源和时序核验的计分屏，证据足以认定**相应采图时刻已处于终局/结算界面**，并足以撤销「仅凭 `df==0` 就已证实在战引擎停摆」的归因（`RULING.md:101`）。**冻结窗终局证据的覆盖为 21/32，不是全部**：`S543_FREEZE_WAS_SCORESCREEN_20261104.md:189–191`（`df==0 且 f0≠0` 共 32 窗，其中「有计分屏证据 21 个」、11 个须挂账）、`S543_FREEZE_WAS_SCORESCREEN_20261104.md:218–228`（11 个未覆盖窗的名单与原因：无截图／纯战斗画面副本；`:228` 明记「不判为『终局态』，明确挂账」）、`S544_TRI_MODEL_VERDICT_20261104.md:200`（覆盖 21/32）、`GOAL_THREE_TARGETS_20261018.md:4466`（§544 §七「覆盖 21/32 窗」）、`RULING.md:102`。截图在窗末，不能单靠该图把整个 25 秒每一时刻都标成终局，也不能从后续结算反推先前完全没有性能问题（`RULING.md:102`）。

**未充分覆盖的零推进窗一律归「零推进、原因未定」**：不贴「引擎停摆」标签，也**不**改记「终局已证实」（`RULING.md:103`「这是当前有效分类，执行无需等待新证据」、`RULING.md:180`）。另须区分：`RULING.md:120` 记明「这 32 个零推进窗中的 11 个未充分覆盖窗」与 D-15.3 的 **11 个有推进的停摆主导窗不是同一集合**，不得混算或互相替代。

#### 545.5 数据面分层（22 + 11 + 5）与主指标

按 D-15.1 分层表（`RULING.md:75–87`）与上一阶段数据面落实稿 `EX1_DATAFACE.md:38–84`（从 104 份原始 JSON 只读重建，命令与输出见 `EX1_DATAFACE.md:11–15`）：语料账 **104 = 子目录 101 + 根 3**（`EX1_DATAFACE.md:38–45`、`FACTBASE.md:42–47`）；净正推进窗 **63**，其中 **58** 个 25 秒窗、**5** 个 4 秒 settle 门控窗、**41** 个非正推进或样点不足窗（`EX1_DATAFACE.md:49–57`、`:265–313`）。58 窗三分类为 **25** 个 `fps_avg>=28` 对照、**22** 个持续低速核心（`fps_avg<28 且 fps_p50<28`，**8 个独立趟**）、**11** 个停摆主导（`fps_avg<28 且 fps_p50>=28`，11 趟，与 22 窗 `trip_id` 交集 0）（`EX1_DATAFACE.md:73–80`、`:119–164`）。

**22 + 11 + 5 分层与报数规定**：核心持续低速分析样本 = **22 个 25 秒窗 / 8 趟**（`RULING.md:82`、`EX1_DATAFACE.md:119–146`）；25 秒低 avg 总计 **33 = 22 持续低速 + 11 停摆主导**（`RULING.md:81`、`EX1_DATAFACE.md:320`）；**11** 个停摆主导窗整组另列「**停摆观测、待归因**」异常层，**既不作为已证在战卡顿正证，也不整组认定终局**（`RULING.md:111`、`RULING.md:5`、`EX1_DATAFACE.md:148–164`）；**5** 个 4 秒门控窗剔出 25 秒性能分析，保留测量失败/加载相位诊断用途（`RULING.md:84`、`EX1_DATAFACE.md:59–69`）。`38` 是混入 5 个 4 秒窗的旧混合计数（38 = 33 + 5），不得再冒充同质性能样本数（`EX1_DATAFACE.md:315–324`、`RULING.md:178`）。每次目标①摘要必须同时出现「核心持续低速 22/8 趟；25 秒低 avg 总计 33，其中 11 停摆另列；另 5 个 4 秒门控窗排除」；只用 22+25=47 窗的分析必须标为「排除 11 个待归因停摆窗后的持续低速/对照分析集」，不得把 22/47 写成全体真机卡顿发生率（`RULING.md:87`、`EX1_DATAFACE.md:324`）。

**主指标维持 `fps_avg`**（`RULING.md:89`、`EX1_DATAFACE.md:32`）；同时披露 `max_stall_s`、零推进数量、时长/门控状态与阶段证据。`fps_p50` 与派生 `live_fps` 仅作分型，不替换主指标、不用于给停摆窗出健康结论（`RULING.md:89`、`EX1_DATAFACE.md:326–330`）；窗口与独立趟两个单位同时报告，一趟多窗不得当成多个独立会话样本（`RULING.md:87`）。

#### 545.6 已撤回、禁止复用的三项旧支柱

以下三项旧支柱已被证伪，**不得再作为本勘误或后续归因的依据**（`RULING.md:105`「不能再以这些已撤回依据强化终局归因」、`RULING.md:167`）：

1. §543 的「屏显时间 ÷ 帧率常数 = 帧号」换算（`GOAL_THREE_TARGETS_20261018.md:4209`、`:4227–4245`）**撤销**：该常数实为健康窗 `stats.fps_avg` 成簇的**帧率帽瞬时值**，不是结算屏时钟换算常数，因果方向搞反（`S544_TRI_MODEL_VERDICT_20261104.md:115`、`GOAL_THREE_TARGETS_20261018.md:4417`）；不得再以该换算反推帧号或终局。
2. §543 的首版比分读数（`GOAL_THREE_TARGETS_20261018.md:4261–4262`）**撤销**：两路独立读得 **126/206/0/201034** 与 **198/731/4/126800**（`S544_TRI_MODEL_VERDICT_20261104.md:116`、`GOAL_THREE_TARGETS_20261018.md:4418`）；旧读数不得再引用。
3. §543 对 `archive_T38` 屏显秒数及 w1 图「时序错位」的判断（`GOAL_THREE_TARGETS_20261018.md:4234`、`:4254`）**撤销**：屏显实为 **`00:00:32`**，且该 w1 图是**磁盘残留件**（mtime 比窗尾早 4410.95 秒，与 T36/w1 同 sha、同字节、mtime 同到微秒），不是时序错位，不得作精确读数（`S544_TRI_MODEL_VERDICT_20261104.md:113–114`、`GOAL_THREE_TARGETS_20261018.md:4415–4416`）。

#### 545.7 ★ 字段身份（复查 R2）：`l3_1101v4c` 三窗速度序列

同版本同地图的 `l3_1101v4c` 趟内「由慢转快」线索，两组数**必须注明字段，不得把派生值填进 avg 栏**（`RULING.md:151–154`、`RECHECK.md:15–21`）：

| 窗口 | 主指标 `stats.fps_avg`（原始 JSON 存储字段） | 派生 `live_fps`（首末帧沿差商，**非存储字段**） |
|---|---:|---:|
| `measure_w0.json` | **18.52**（原值 `18.520948494813613`） | **18.54**（`18.539626790502314`） |
| `measure_w1.json` | **28.40**（原值 `28.40179635682234`） | **28.42**（`28.416096013424877`） |
| `measure_w2.json` | **30.68**（原值 `30.681571141892938`） | **30.71**（`30.70530239738328`） |

`S544_TRI_MODEL_VERDICT_20261104.md:147` 报的 `18.54→28.42→30.71` 是**派生 `live_fps`**（首末帧沿差商），不是源码/JSON 字段（`RECHECK.md:15–19`；该原件同时把这两处报数的全路径列在 `RECHECK.md:17`，分别对应代号 H 的 hy4free 核验件与代号 Q2 的 qfmodel V2 报告，路径对照见 `RULING.md:25`、`:28`）；**主指标 `fps_avg` 序列是 `18.52→28.40→30.68`**（`RULING.md:153`、`RECHECK.md:19`、`:77–79`）。本件生成时只读核对 `D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip/l3_1101v4c/measure_w0.json`、`.../measure_w1.json`、`.../measure_w2.json`（各为单行文件，源位置第 1 行），确认三窗 `stats.fps_avg` 与派生值如上，且三份原件**均无 `live_fps` 存储字段**（`has_stored_live_fps=false`；完整命令与 stdout 见本件第 0 节检查 B）。两组数都只支持「趟内由慢转快」这一**线索**，不据此归因寻路/会话/宿主/兵力变化；同版本同地图的趟内比较不得与跨日期的版本/地图/相位混杂合成因果配对（`RULING.md:150–151`、`:155`）。

#### 545.8 D-15 结案用语（供后续可维护既有件的轮次登记）

D-15 已裁（采用修正 A），历史叙事按「追加勘误、原文不改」处理，不维持原叙事有效（`RULING.md:5`、`RULING.md:97`）；本件为域内候选稿，当前轮次台账 `GOAL_THREE_TARGETS_20261018.md` 与 `PENDING_DECISIONS.md` 保持只读，**未追加、未删条、未登记、未 commit**（`RULING.md:13`、`:170`）。目标①的现象证据（22 个 25 秒持续低速窗 / 8 趟）成立，**运行期耗时落点与因果链未定位、机制未闭合**（`RULING.md:146`、`:204`）；D-13「当前 E3→① 实施路径关闭」不替代本节的证据限度说明（`RULING.md:128`、`:130`）。

<!-- END APPENDABLE ERRATA -->

---

## 3. 逐条验收自查与边界（不属于追加正文）

| # | 判据 | 落实位置 |
|---|---|---|
| 1 | 明确撤销四项归因（整批战斗段完全冻结／引擎停摆已定谳／「永不恢复」超窗机制化／凭停帧形态证明静态路径历史命中），且不写成已证相反结论 | 545.2 第 1–4 项 + 「撤销的是肯定归因，不是已证相反结论」段 |
| 2 | 保留帧号/时间/零推进计数；保留 §540/§541 静态字节结论；声明不得再冒充运行期定位证据；缺项写「缺」并列查阅件 | 545.3(1)、545.3(2) |
| 3 | 证据范围写死 21/32、未覆盖窗归「零推进、原因未定」、不贴停摆标签也不改记终局 | 545.4 |
| 4 | 22 + 11 + 5 分层、33/38 分母、报数规定、`fps_avg` 主指标 | 545.5 |
| 5 | 三项被证伪旧支柱只作「已撤回、禁止复用」列出并给出正确值，不作依据 | 545.6；禁用扫描见第 0 节检查 C |
| 6 | 每处引用写「文件名 + 实际行号」；显式说明散件 §538/§539 与台账同号章节不是同文；台账行号经 grep 核实 | 545.1、全篇引用；第 0 节检查 A |
| 7 | `l3_1101v4c` 三窗序列标明 `fps_avg` 与派生 `live_fps` 身份 | 545.7；第 0 节检查 B |

**边界**：本件只出文档，未写任何采样/注入/运行期探针脚本；第 0 节检查 B 是一次只读字段核对（内联 `python -I -X utf8 -c`，绝对路径，未产生脚本文件）。未改台账/PENDING/RULING/RECHECK/FACTBASE/核验件/真机件，未 commit。数据面数字引用上一阶段 `EX1_DATAFACE.md`，本件未重跑其重建脚本；21/32 覆盖、截图时序与计分屏判定沿用已读原件，未在本件独立复核（`RULING.md:197`、`RECHECK.md:82`）。
