# XVERIFY_H8TRIPS_20261031 — B2 对账判定书（②批 2C 趟 · ①批 H8 两趟 · q/r 基线张力 · Δ n=14 · 台账 §485-487 审计）

> **族属声明（同族标注版）**：本判定书为**同族标注版——对账员与执行线同为 GLM 族（GLM start-plan），非异族对账**；
> 不以同族冒充异族。正式异族版留待 dfmodel 通道恢复后可补（resume 路径保持可达，§492 在案）。
> **mimosa 声明**：mimosa **未实际运行**——本 ask 为纯只读对账（零代码新增、零部署、零写域外改动），
> 安全扫描无变更对象；且硬约束禁真机/禁写域外，扫描器对本判定书无增益。如实登记。
>
> **对账纪律执行**：全程不采信台账/前任总结数字，逐字段回读原始 JSON 独立重算；闩→退一律 `timeline.close_rows`
> 原始时间戳（§477 R-1）；Δ 判据族限定（Y-481-E）；popen t0 锚（Y-481-D）；禁真机、零 git 写、零写域外。
> python 一律 `python -I -X utf8`。

---

## 0. 对账件与方法

- **被对账对象**（全部原始件亲算）：
  - ②批 2C：`lead/qc161_u0400_trip/c2ab_x/20261031T154139_9001_P3e_E12_T1/`（`_rec.json`+`timeline.json`+守卫日志直读）；
  - ①批 H8：`out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip/l3_20261031ha/` 与 `…/l3_20261031hb/`
    （`qc151_fields.json`、`measure_w*.json`、`_launch_result.json`、launcher tee）；
  - q/r 基线：`…/l3_20261023q/`、`…/l3_20261023r/`；
  - frame 语义旁证：`…/l1_20261023e1|hb|k/`（units>0 首样）、c2ab_x 菜单趟、`l3_20261021/`；
  - §486 侧：`XVERIFY_H8_20261031/XVERIFY_H8_20261031.md`（C-4 原文 ：295-296）、合成趟判档留档、
    `LEADER_battle/launcher_h8_t1/t2_20261031.txt`、`frozen_recheck_*.txt`、`C_BATCH2C_H14_20261031/` tee 三件。
- **前任探针**：写域实际在盘 **11 支**（`_xvh8_p01..p11`）+ `_raw/` 全套 stdout——比 ask/§492 所记「八支」多 3 支
  （p09/p10/p11，01:29–03:31 落盘，系前任第二次截停后续跑产物，台账 §490/§491 未记）。**11 支全部逐支配对读毕**
  （脚本+stdout），吸收情况逐一列于 §6。
- **亲验面**（本任自跑，stdout 留档 `_raw/_b2g_*.txt`）：
  - 前任探针复跑 diff：**p01/p02/p03/p06/p07/p10 逐字节 IDENTICAL**；p08 仅 list_procs 现值 500→513 浮动
    （其自身标注「随负载浮动，非常量」）；p04 未重跑（其 (B) 段 ZeroDivisionError 崩溃为已知，p05/p10/p11 接续）；
    p05/p09/p11 逐字复读吸收（与亲跑件覆盖重叠）。
  - 自写探针：`_b2g_v1_core.py`（2C/ha/hb/q/r/tee 全核心读数直读）、`_b2g_v2_framezero.py`
    （counters.t_rel→frame 内插，units>0 首样决定性检验）。
  - 判档器亲跑：`python -I -X utf8 lead/goal1_harness8_20261031/_judge_h8_20261031.py --trip-dir …/l3_20261031ha`
    ⇒ **EXITCODE=3**；对 hb ⇒ **EXITCODE=1**（留档 `_raw/_b2g_judge_ha.txt`/`_b2g_judge_hb.txt`）。
  - 台账对读：§477/§481（含 19774-19867 行边界谱系）/§485/§486/§487/§488/§489/§490-§492；
    `XVERIFY_481_20261031.md` §(6) n=13 基线口径对读。

---

## 1. ②批 2C 趟（hold=14.0，20261031T154139）——§485 逐字段判定：**CONFIRMED**

全部数字主张由 `_rec.json`/`timeline.json` 直读重算（`_b2g_v1_core.py` §(A)，stdout 在案）：

| §485 主张 | 亲算值 | 判定 |
|---|---|---|
| closed_at_s=15.194 ∈ 预测带 [14.996,15.289] | 15.194 ✓ | CONFIRMED |
| latch=True | True（原始行 exitstate==1 ×2，非仅 _rec 字段）✓ | CONFIRMED |
| Δ=0.101（首个 hwnd==0 行 t−rows[0].t） | rows[1].t−rows[0].t=0.101 ✓ | CONFIRMED |
| singleton 与 hwnd 同步 idx=1 归零 | 首 singleton==0 idx=1，同行 ✓ | CONFIRMED |
| 闩→退=2.003s（R-1：close_rows 原始时间戳） | 闩沿 idx55 t-rel=5.526；末行（含 DICT）t-rel=7.529 ⇒ 7.529−5.526=**2.003** ✓；数值行末口径=**1.001**（见黄 Y-3） | CONFIRMED（口径注 Y-3） |
| exitstate 0×55→1×2+DICT 尾行 | 0×55 → 1×2（idx55,56）+ DICT×1（idx57 `{'state':'read_fail'}`），0..54 连续 ✓ | CONFIRMED |
| hold_tl_n=14==ceil(14.0) | n=14，hold=14.0，ceil=14 ✓ | CONFIRMED |
| 量化律 closed=a+ceil(hold)+post，a+post=1.194∈[0.996,1.289] | a=hold_tl[0].t−t0(反推)=0.628∈[0.623,0.645]；post=closed−a−ceil=0.566∈[0.373,0.644]；a+post=**1.194** ✓ | CONFIRMED |
| a8=PASS / 载体删 / stop=None / except 恒 / exit_kind=natural / final_exitcode=0 | PASS / carrier_deleted=True / None / except sha16 三读恒 `6694b75e46a6e773` / natural / 0 ✓ | CONFIRMED |
| killed_on_cleanup=None | **键不存在**（非 None；probe_v2 仅 survivors 非空才写键，p09 §(6) 三趟先例同形） | **黄 Y-1** |
| 闩边界收窄 (14.997,16.272]⇒(15.194,16.272] | 下界上移 0.197（14.997→15.194，新闩点 closed=15.194）✓ 合法；上沿 16.272 非最紧（黄 Y-4） | CONFIRMED（上沿注 Y-4） |
| ~21s 带不适用（闩族归零=closed+0.101=15.295，锚=popen t0） | 15.194+0.101=15.295 ✓（t0 反推自洽：close_delivery.t−closed_at_s） | CONFIRMED |
| 挂死 T204123 单例未复现（本趟 exitstate==1 仅 2 行 vs 1017 行） | 2 行 vs 204123 趟 1017 行（p02/p06 表）✓ | CONFIRMED |
| preflight 10/10、selftest 110[OK]/0[RED] tee 落盘 | 亲点：preflight 11 行=10[OK]+「preflight: 全过」；selftest 110[OK]/0[RED]，驱动 sha256=90a1890a… ✓ | CONFIRMED（Y-3 闭合） |
| fork=spin_x_hook6_undetermined（不承重） | hook6_state=present_with_read_fail_rows ✓ | CONFIRMED |

**前任 p01 §(4) 点名**：p01 stdout 的 `post=close_delivery.t−hold_tl[-1].t=1.54 ⇒ a+post=2.168∈[0.996,1.289]? False`
系**探针内 post 定义漂移**（用末采样时刻而非 hold 终点 a+ceil；hold_tl 末样比 hold 终点早 0.974s）。
前任自己已在 p02 改用正确口径（`closed−a−ceil`，_xv481_p15:30 先例）并复算 n=14 全带 PASS——**非台账矛盾，吸收时以 p02 为准**。

---

## 2. ①批 H8 两趟（l3_20261031ha / hb）——§487 逐字段判定：**CONFIRMED**（hb 判档 EXIT 见下）

| §487 主张 | 亲算值 | 判定 |
|---|---|---|
| C-1 武装：META.h7_measure_start_frame==400 ∧ MEASURE.h7_frame_wait 在场（两趟） | 两趟 `qc151_fields.json` 亲读：META=400 ∧ frame_wait 在场 ✓；且 `_launch_result.json` argv 尾部两趟均含 `"--h7-measure-start-frame","400"`（显式 extra-argv）✓ | CONFIRMED |
| ha wait_s=73.135 / poll_count=25349；hb 94.676 / 26939；reached=400 / offset=0 | 逐位同 ✓；overrun=False、timed_out=False ✓ | CONFIRMED |
| ha units0=1342；settle 窗帧 400-412；fps≈3.0；p50=334.9 / p90=485.1ms；max_stall=0.491s；verdict=no_advance | gate.units0=1342、counters 首行 1342、窗 f[400→412]、fps_avg=3.0007、p50=334.907、p90=485.139、stall=0.4907、verdict=no_advance ✓（p04 复算与落盘 stats 仅浮点尾差） | CONFIRMED |
| hb w0(437-606, 6.8fps, p50 106.6, p90 296.8, stall 0.494) / w1(607-725, 4.7, 182.9, 398.6, 0.750) / w2(726-991, 10.6, 72.0, 154.3, 0.580)，三窗 verdict=ok | 逐位同 ✓（p04 (A) 独立重算吻合） | CONFIRMED |
| hb units 持续下降 1341→1262→1179 | counters 行口径：w0 1341→1298、w1 1297→1262、w2 1262→1179，10 窗全库严格非增（p06 §(2)）✓；行选择混口径见黄 Y-8 | CONFIRMED（注 Y-8/Y-9） |
| 「n=2 趟 5 窗全落满员域」 | 实为 **4 窗**（ha w0 + hb w0/w1/w2；ha no_advance 短路后 w1/w2 按设计不落，判档器 ha 输出明示） | **黄 Y-7** |
| 判档：ha=EXIT3 | 亲跑 **EXITCODE=3**（设计内短路 no_advance）✓ | CONFIRMED |
| 判档：hb=（ask 转述 EXIT0） | 亲跑 **EXITCODE=1**（2 FAIL：V11-a min pre_fps15=6.676<25 + boot 指纹目录缺失[重跑环境项]）。**ask 的「hb=EXIT0」与盘面不符——系 ask 转述失真**：§487 原文未主张 hb EXIT=0（仅「hb 6.676 过闸开满三窗」），§489 明记 RR 复核 EXIT=1。前任 judge_hb.txt 同为 EXIT=1。台账无错 | **ask 校正（非台账黄项）** |
| rc=0/0、170.2s/241.1s、harness_sha16=dd5459fe0cf3461c、载体清、procs=0 | `_launch_result.json`：rc=0/0、duration 170.2/241.1、sha16 dd5459fe、carriers_deleted=True、leftover=[] ✓；判档器 [0] 段 PASS 同 ✓ | CONFIRMED |
| 预检 A1/A2/A11/A8 行在 launcher tee | 亲读 `launcher_h8_t1/t2_20261031.txt` 第 7-10 行：A1 gamemd sha、A2 map sha、**A11 got=dd5459fe0cf3461c=want**、**A8 got=0=want**，全 OK ✓ | CONFIRMED |
| 晚相位基线 q/r frame 2955+/~950u：31-37ms@31fps | q w0 p50=31.905/p90=37.172@31.12fps；r w0 p50=32.106/p90=36.035@31.32fps ✓ | CONFIRMED |
| 批面卫生（except 1046/1046、WER 零新增、S4 hit=0、T0-T1 零写、ct 残留空） | p06 §(5) 亲跑复现 ✓ | CONFIRMED |
| 冻结六件批后逐位（v2 冻结维持） | p07 亲跑复现：frozen_recheck_h8_post.txt 六行 MATCH ✓（h8_pre 内 harness8 DIFF 行=v1→v2 替换史，§489 C-R6 作废标注在案） | CONFIRMED |
| 「强杀 0（两趟自然走完 rc=0）」 | 两趟 CLOSE.close_mode='terminate'、TERM.term_requested/terminate_sent=True、游戏进程 wait_returncode=**1**（p09 §(1)；q/r 同形）——收尾是缺省 terminate 而非游戏自然退出；「无中途强杀、harness 全程 rc=0」才准确 | **黄 Y-10** |
| 「①复现信号成立（限定域：满员早期交火相位）」 | headline 即带限定 + 设计件 §2.3 双命中（p90≫40 ∧ max_stall≥0.5）+ 保留项在案，措辞总体合格；建议补跨会话限定（黄 Y-11） | CONFIRMED（注 Y-11） |

---

## 3. q/r 基线张力消解（重点新增项）

### 3(a) frame 计数器起点语义 —— **定谳：battle 起点**（菜单/导航期不累计）

三条独立证据链（均本任亲算/亲读）：

1. **菜单不累计**：2C 趟 timeline close_rows 57 个数值行 frame 全 0（亲算 Counter）；前任 p03 §(1)（亲跑复现）：
   四趟未进 battle 趟 frame≡0（1176/1210/1211/72 行值域 {0}）。
2. **battle 出现时 frame≈0（决定性）**：`_b2g_v2_framezero.py` 对 l1_20261023e1/hb/k 三趟（H7）：
   counters units 首 >0 行（t_rel=1.00-2.03s，units=499~971）按同窗 samples.t↔samples.f 内插 ⇒ **frame=0**
   （前任 p10 得 0.4-1.2，同为 ≈0 量级，插值细节差异不影响结论）。此刻进程已活 ≈44-58s（导航+窗口稳定段）
   ⇒ 「自进程起累计」假设被否（若累计，读数必 ≫0）。
3. **H8 绑帧行为自洽**：ha/hb 入口（nav_end+4.1s）后等 73.1/94.7s 恰达 400、offset=0、零越界零跳帧
   ⇒ 入口读数 ≤400 且临近 0（等待期均速 4.2/5.5fps 与窗内 3.0/6.8fps 同量级）。

读点同址：驱动侧 `_drive_c2_x_probe_v2.py:69 G_FRAME=0x00A8ED84` 与 harness 侧
`qc151_trip.harness8.py:3831 MEASURE_CURRENT_FRAME_VA=0x00A8ED84`（p03 §(0) 亲读）。跨代（H6/H7/H8）同 VA 同语义。
NAV 组无 frame 读数（screen-signature 导航），「nav 段 frame 读数」证据面由 1/2/3 替代覆盖。

### 3(b) q/r 从 battle 起到 w0 的墙钟与早相平均 fps —— **≥23 成立**

`h7_nav_end_t` 与 `samples.t[0]` 同一 perf_counter 轴（同进程），直减（`_b2g_v1_core.py` §(D) 亲算）：

- q：27402.609 → 27527.346953 = **124.738s**，f0=2955 ⇒ **≥23.69 fps**
- r：28110.109 → 28240.852951 = **130.744s**，f0=3100 ⇒ **≥23.71 fps**

nav_end=post_start_burst 判 battle 场景出现之后 ⇒ 墙钟若含残余加载只会高估时长 ⇒ 真实平均只会更高。**上界口径成立**。

### 3(c) 张力消解判定 —— **消解两层；归因层未消解（如实）**

- **第一层（语义）——消解**：「frame 语义不同使对比无效」分支**被否**（3(a) 定谳）。q/r 与 ha/hb 的帧域同轴可比。
- **第二层（差异为真）——消解**：q/r 早相确实快，非测量假象。
  - V-无关反证：hb 的 0..991 帧实测 174.016s（5.69fps，p11 亲算口径我复核）＞ q 的全程 124.738s
    ⇒ **无论后续帧多快，q 的前 991 帧不可能同 hb 一样慢**。
  - 定量界（p10 亲跑复现）：设帧域 [437,991]（宽 554 帧）以 x fps 通过、其余按族内上限 V：V=31.4 ⇒ q 需 x≥11.5、
    r 需 x≥11.2（均＞hb 同域实测 4.7-10.6）；早相 0..991 域（p11）：V=31.4 ⇒ q 需 ≥15.93、r 需 ≥15.59 fps
    ⇒ 比 hb 实测 5.69 快 ≥2.7-2.8×。
- **归因层——未消解**：快慢差异成因（会话/日差 vs H8 347-500Hz 轮询观测影响）本批数据不可分。
  侧证：l3_20261021（H6，无 H8 轮询）早相亦慢（0→387 帧 ≤52.2s ⇒ ≥7.4fps；窗内 8.8-12fps）
  ⇒ **轮询非慢早相的必要条件**；但 ha/hb 的 3-5.5fps 与 l3_20261021 的 7-12fps 之差仍可能含轮询贡献。
  所需数据：harness8 v3 的 `H8_WAIT_HZ` 对照旋钮（§487 v3 候选已在案）或一次无轮询绑帧观察趟。
- **对 §487 保留项的处置**：保留项 ③（frame 语义）**关闭**（本节定谳）；保留项 ②（q/r 张力）**收窄**为
  「真会话级速度差（≥2.7×），归因待 v3 对照」；保留项 ①（轮询影响）维持开放。
- **对 §487 结论的反作用**：满员早相慢帧现为 **3 会话样本 2 慢 1 快**（10-21 慢 / 10-30 q+r 快 / 10-31 ha+hb 慢）
  ⇒ Y-11。

---

## 4. Δ 轴族内并入 n=14 —— **CONFIRMED（族内零例外）**

- 基线对读：`XVERIFY_481_20261031.md` §(6) n=13（闩族 8：Δ=0.100/0.101×4/0.102/0.122/0.101；不闩族 5：
  Δ=0.402/3.414/3.718/4.822/5.023）与本任 p02 亲算的 13 旧趟逐位吻合；族限定（P3e 早窗菜单族，Y-481-E）沿用。
- 并入 2C（Δ=0.101，闩）⇒ **n=14：闩族 9 / 不闩族 5**；闩侧 max Δ=**0.122**（E12-1029T2228）、不闩侧 min Δ=**0.402**
  （E5h20）、灰区 [0.15,0.35] 点数=**0** ⇒ 判据 Δ<0.15⇒闩 ∧ Δ>0.35⇒不闩 **n=14 零例外成立**（p02 (A) 亲跑复现）。
- 伴随检验：hwnd/singleton 同行归零 14/14 ✓；原始行 exitstate==1 计数 vs `latch_detected` 字段无不符
  （3 趟旧 schema 无该键，如实）✓。
- **适用域不变**：仅 P3e 早窗菜单族内、仅判闩/不闩不判正常退（挂死 204123 Δ=0.101 闩而不退在案 §477）。

---

## 5. 台账 §485/§486/§487 审计 —— **红项 0 · 黄项 11 + ask 校正 1**

**红项：无**——三节全部决策承重数字与盘面原始件一致，无足以误导决策的失实。

**黄项（表述收紧，均不动主结论）**：

- **Y-1（§485）**：「killed_on_cleanup=None」⇒ 实为**键缺席**（probe_v2 仅 survivors 非空才写键；
  既往自然退趟 205108/211741 同为键缺席，083340 趟有键=[[1896,'rc4_loader.exe'],[6000,'gamemd.exe']]，p09 §(6)）。
- **Y-2（§485）**：「既往带 2.004~2.108」系 §477 五趟带口径；族内自然退闩趟全量带=[**2.003, 3.102**]（n=8，
  含 E12-1029T2228=3.102、E12-1029T2316=2.013，p06 §(3)）。「2.003 新下沿」不受影响（2.003<2.004 仍成立）。
- **Y-3（§485）**：闩→退的退沿=**首个读败行**（wait=0，进程死亡**上界**；本趟真退时点 ∈(6.527,7.529]
  ⇒ 闩→退 ∈(1.001,2.003]）。族内先例（§477 五趟、_xv_s01 口径）同为末行口径故可比（p02 (B)：hold14 数值末 1.002 vs 末行 2.005）；
  建议表述补注数值行末口径 1.001s。
- **Y-4（§485/§481 谱系）**：闩边界上沿 16.272 **非最紧**——跨会话不闩点 E5h15 closed=16.091 在案
  （§477 Y-1 已登记「上界未收紧（E5 已有 16.091 不闩）」），最紧闭轴区间 **(15.194, 16.091]**；§485 边界句未复述该注。
  下界上移 0.197 的收窄主张本身合法（新闩点 closed=15.194＞14.997，跨会话全局闭轴下界）。
- **Y-5（§486/§488）**：RR「真机产物复算 75 窗 maxΔ 74×1+1×3」的窗口集口径与全库可测窗集不同——
  p06 §(1)（≥2 沿可测窗）：**49 窗 {1:47, 3:1, 2:1}**，其中 hb w1 maxΔ=2 系批后新点。引用该数须注明口径，否则读者无法复算。
- **Y-6（§486/§488）**：reviewer `__pycache__`「4 枚留置登记」vs 现盘 **3 枚**
  （qc151_trip.harness8 / _judge_h8 / _launch_h8；XVERIFY_H8 目录 0 枚，p09 §(5)）——差 1 枚去向未登记（gaps §7-5）。
- **Y-7（§487）**：「n=2 趟 **5 窗**全落满员域」实为 **4 窗**（ha w0 + hb w0/w1/w2；ha 短路后 w1/w2 按设计不落）。
- **Y-8（§487）**：units 链「1341→1262→1179」行选择混口径（1262=w1 **窗末**=w2 窗首，非 w1 窗首 1297）；
  建议改「窗首 1341/1297/1262、窗末 1298/1262/1179」。units 严格非增结论不变。
- **Y-9（§487）**：hb units0 **1341**（counters 首行，t_rel=1e-06）vs **1347**（gate 快照）双口径——§490 待裁项**闭合**：
  窗级主张用 counters 行口径 1341，gate 1347 并列注明（§487 已有脚注，建议在正文显式双列）。
- **Y-10（§487）**：「强杀 0（两趟自然走完 rc=0）」措辞误导——两趟收尾=**缺省 terminate**
  （harness8:1423 `proc.terminate()`，Windows=TerminateProcess；TERM.term_requested/terminate_sent=True，
  游戏进程等待退出码=1，q/r 同形）。准句：「无中途强杀/看门狗介入；harness 协议全程走完 rc=0；游戏进程按缺省 terminate 收尾」。
- **Y-11（§487 headline）**：「①复现信号成立（限定域）」建议补跨会话限定：满员早相慢帧 3 会话样本 **2 慢 1 快**
  （10-21 慢 / 10-30 q+r 快（≥23.7fps，§3(b)）/ 10-31 慢）⇒ 「复现」宜作「**再现于 2/3 会话**、会话强方差」，
  与 §487 保留项 ② 相容但应上升到 headline 限定域内。
- **ask 校正（非台账黄项）**：ask(2)「判档 hb=EXIT0」失真——亲跑 EXIT=**1**；§487 未主张 0、§489 记 1，台账无错。

**§486 专项核验（条件全采纳的合法性）**：
- **C-4 处置合法**：条件原文（B1 书 ：295-296）=「拒发留痕（N-4）：N<1 硬拒的提示同时写 stderr…使批 tee 日志可判读」
  ——其**意图=拒发行可入批日志**；处置=发射 tee 2>&1（stdout/stderr 均入日志）满足意图且不破 C-0 字节冻结，
  处置已登记。机制替换、意图保持、登记在案 ⇒ 合法。本批未发生 N<1 拒发（无可观察验证实例，属设计面而非失效）。
- C-0：冻结六件 MATCH（p07 复现）；h8_pre 的 harness8 DIFF=v1→v2 替换史、§489 C-R6 作废标注在案 ✓。
- C-1：两趟 META=400 ∧ frame_wait 在场 + argv 显式参数亲验 ✓（双核验兜住其未采的建议项，§488 已登记）。
- C-2：本批 offset=0×2 未触发；hb w1 窗内 maxΔ=2=容差边界（未拒），l1k w0 maxΔ=3 历史点在案 ✓。
- C-3：`LEADER_battle/c3_offline_adjudicate_h8.txt` 在盘，「H8 离线自检： 全过」✓。
- C-5：ha EXIT=3 ∈{2,3} ⇒ hb 补发，规则自洽 ✓；20min 帽=170.2/241.1s 均在内 ✓。
- 合成趟判档（前任留档复读）：synth_overrun/synth_timeout=**EXIT 3**（v2 短路集翻转生效）；synth_ok=EXIT 1
  系其夹具缺 qc151_fields.json（夹具限制，非判档器回归）。

---

## 6. 前任探针吸收清单（11 支逐一；比 §492 所记「八支」多 3 支续跑件）

| 探针 | 处置 | 备注 |
|---|---|---|
| p01_2c | **亲跑逐字节复现**，吸收 | §(4) post 定义漂移点名纠正（其 p02 已自纠，本判定书 §1 以正确口径定谳）；§(3) 双口径并列采纳 |
| p02_delta14 | **亲跑逐字节复现**，吸收 | n=14 全量、闩→退全带、边界 16.091 发现（→本 Y-4）全部采纳 |
| p03_framezero | **亲跑逐字节复现**，吸收 | VA 同址/菜单恒 0/全库 f0 表采纳；(4) ratio 列对 H8 趟无意义（n2w 不含绑帧等待，§490 已预注），不引用 |
| p04_stats_tension | stdout 复读吸收；(B) 段除零崩溃**未重跑**（复现崩溃无增益） | (A) stats 复算=浮点尾差采纳；崩溃段由 p05/p10/p11 接续 |
| p05_tension | stdout 复读吸收（与 p10/p11 覆盖重叠） | 全库 fps 分布（max 31.32）/Δu/Δf/P2 house 求和采纳 |
| p06_batchface | **亲跑逐字节复现**，吸收 | 75 窗口径注（→Y-5）、闩→退 n=8 全带（→Y-2）、units 严格非增、h8 +160−0、趟数 UNVERIFIED 采纳 |
| p07_frozen | **亲跑逐字节复现**，吸收 | 六件 MATCH + h8_pre DIFF 史采纳 |
| p08_a8_live | 亲跑复现（list_procs 500→513 浮动差，其余逐字节同） | launcher sha 9a1a795b / sizeof 568 / carrier len 130 采纳 |
| p09_term_paths（续跑件） | stdout 复读吸收 | term 形态（→Y-10）、killed_on_cleanup 键缺席先例（→Y-1）、载体 len=130（C-R2）、__pycache__ 3 枚（→Y-6）、C-2 文字落点采纳 |
| p10_qr_feasibility（续跑件） | **亲跑逐字节复现**，吸收 | units>0 首样 frame≈0.4-1.2（我内插得 0，量级一致）+ q/r 可行性界 + 进程起累计否证采纳 |
| p11_early_bound（续跑件） | stdout 复读吸收 | 早相 0..991=174.0s/5.69fps、x≥15.9/15.6 界、units 反推 frame0≈1227/1155/1471/1443（下界估计）采纳 |

**本任独立增量**：`_b2g_v1_core.py`、`_b2g_v2_framezero.py`（units>0 内插 frame=0 三趟决定性检验）、
判档器两趟亲跑、launcher tee 预检行亲读、preflight/selftest tee 亲点、argv C-1 亲验、481 书 n=13 口径对读、
台账 §481 边界谱系（19774-19867 行）对读。

---

## 7. gaps（无法独立判定项，如实）

1. **趟数账（31→32→34）**：盘上无单一权威清单可独立复算（c2ab_x 25 项含非趟件、l* 目录 24）——UNVERIFIED
   （非不符；前任 p06 §(7) 同判）。
2. **§486/§488 的 B1/RR 内部实测**（eq7p/eq8p 三轮、门禁演算 129/130/130、拒采边界 [None,900]/[399,401] 等）：
   留档在 `XVERIFY_H8_20261031/_raw`，本任未逐支复算（超出本 ask 点名检查面），按留档吸收并如实标注。
3. **q/r 快慢差异归因**（会话方差 vs H8 轮询观测影响）：本批数据不可分，需 v3 `H8_WAIT_HZ` 对照趟——开放。
4. **§485 批后「procs=0 真验、无部署无配置改动」**：未见独立落盘件（C 卡目录仅 frozen_recheck/selftest/preflight），
   按台账采信、未独立复验。
5. **前任 __pycache__ 4 枚 vs 现盘 3 枚**的差 1 枚去向：不可考（无人承认删除），登记在案（Y-6）。
6. **q/r 的 H7 「stage_seconds:frame」120.7/126.7s 的语义**（等待目标是什么）未从源码定谳——不影响 §3(b) 结论
   （该结论只依赖 nav_end→w0 墙钟与 f0），登记备查。

---

## 8. 判定终态

- **总判定：6 主读数 6 CONFIRMED 0 REFUTED；红项 0、黄项 11 + ask 校正 1；gaps 6。**
- ②批 2C 趟 §485 主张全数存活（量化律出样本 PASS、闩边界下界首次实际收窄 14.997→15.194 合法）。
- ①批 H8 两趟 §487 主张全数存活（C-1 武装/绑帧/窗统计/判档分类/卫生面全命中；hb 判档 EXIT=1）。
- q/r 张力：**frame 语义定谳=battle 起点；早相 ≥23.7fps 为真；对比有效、差异为真；归因待 v3 对照**。
- Δ 轴：**n=14 族内零例外**（闩 9 max 0.122 / 不闩 5 min 0.402 / 灰区 0），族限定保持。
- 三目标句态不受黄项影响：①受测域更新（满员早相慢帧、2/3 会话再现）· ②硬门槛未达成、RC-4 不收口 · ③保持态。
