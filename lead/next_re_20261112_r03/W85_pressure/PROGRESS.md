# W85_pressure · PROGRESS

卡：A 线加压（真机）——"更重的战斗"下窗口线程每拍 CPU 是否 >20% 抬升。
唯一问题参照 DISPATCH_20261114_1152.md §5。

## 状态时间线

### 2026-11-14 ~11:53–12:20（读参考，未写盘——已收到 Lead 催促，本节即补）
已完成阅读（原文核对，非凭印象）：
- `r03/DISPATCH_20261114_1152.md`（全 71 行）：判卡口径 = 加压臂相对 W12/W20 基线 1.69 ms/拍
  中位抬升 >20% 且有独立实例化证据；否则如实写"仍未造出压力"+ 上限证据。
- `r02/W84_defeat_dialog/work/tools/w84_lib.py`（818 行）：可复用真机库——WMI 启动、
  只读 RPM、控件枚举、截图、锁、close_game、restore_configs、desktop_precheck。
- `r02/W84_defeat_dialog/work/tools/w84_common.py`（198 行）：manifest/diff/pristine/锁助手。
- `r02/W84_defeat_dialog/work/tools/w84_run.py`（559 行）：战役导航
  （SinglePlayer→NewCampaign→苏军徽章→wait_ingame 判据 frame>30 且
  scen_filename=RA2F_M1.MAP）+ 终态三分类。本卡复用其导航骨架。
- `r02/W84_defeat_dialog/work/tools/w84_build.py`（313 行）：design JSON schema
  （package/campaign/missions[0]{structures,units,infantry,objectives,waypoints,
  player{house,credits}}）、ra2forge build 命令行（v15 patched 包根作 cwd）、
  verify_pkg 校验点（BATTLEMD.INI Scenario= 唯一、MAP 计数、event/action 正则）。
- `r02/W20_combat/combat_probe.py`（2050 行全文）：6ms 逐拍采样实现——
  窗口线程 GetWindowThreadProcessId 返回值取 tid → OpenThread →
  QueryThreadCycleTime 每拍累计 Δ（主判读）+ GetThreadTimes（15.625ms 量子，交叉）；
  ADDR 表（frame 0xA8ED84 / mode 0xA8B238 / A8ED50 候选 BulletCnt / B0CE88 / 87E8E0）；
  cadence deadline 调度；自标定规则 cyc_per_ms = ΣcycΔ/ΣFILETIMEΔ；判据全预冻结。
- `r02/W20_combat/analyze_combat.py`（前 150 行）：A/HexBay/U800 三臂锚点数值与
  分析口径（pct/pearson/spearman 工具）。

## 选定设计（待 build 后按实算修正，先冻结框架）
- 双臂**同图同布局同对象数**，单变量 = 单位 mission 赋值（Hunt vs Guard）。
- 载体：ra2forge 战役包 → BATTLEMD.INI + RA2F_M1.MAP（走 W84 已验证的战役导航，
  避开 W20 的遭遇战选图 UI 路径）。地图拟 100x100 TEMPERATE（若 ra2forge 限制则回退 80x80，理由落盘）。
- 规模目标：总声明对象 ~1200（显著超 B″ 800）：玩家 Russians = NACNST1+NAPOWR6+TESLA12+MTNK280(Guard)；
  三个敌 house（British/Americans/Cubans，待核 ra2forge 支持名）各 MTNK300 全 Hunt + GAPOWR1。
- 对照臂：同布局，全部 units mission=Guard（敌 house 不动），预期 0xA8ED50 全程 0。
- 判据（预冻结，不得事后改）：
  - 主判读：窗口线程 cycle 每拍 Δ，cyc→ms 用本趟全段自标定；
    **加压臂局内段中位 > 1.6914×1.20 = 2.0297 ms/拍** ⇒ "造出负载"。
  - 同时报：≥64 ms 拍间隔计数、跳多拍(df≥2)计数、RPM 读失败数。
  - 独立负载证据 ≥2 项：0xA8ED50 非零拍占比/峰值（W20 仅见 0–3）、
    交战期截图逐字节差异（PNG 像素差 vs 对照臂）、（如可用）B0CE88/87E8E0 候选代理值变化。
- 真机纪律：锁 `r03/.game_instance.lock` owner=w85 起止各一次；只在
  `W85_pressure/out/sandbox_game/` 跑；`ra2youli` 跑前跑后锚点哈希（gamemd.exe/
  ddraw.dll/RA2MD.INI/BATTLEMD.INI）+ 残留进程 0；沙箱配置逐字节备份还原。

## 下一步命令（顺序）
1. 复制 W84 harness 4 件 + W20 analyze 骨架进 `W85_pressure/work/tools/`，记录双侧 sha256。
2. 读 `w84_finalize.py`（安装/卸载流程）+ ra2forge 源码核 house 白名单与地图尺寸/单位上限。
3. `python w85_build.py`（离线，无锁，无 gamemd）→ 构建双臂包 + verify。
4. robocopy `ra2youli` → `out/sandbox_game/`（约 2 GB，647 文件）+ 锚点哈希。
5. `python w85_run.py --arm pressure` → 采样 ≥240 s（目标 300 s）→ 收尾还原 → 释放锁。
6. `python w85_run.py --arm control` → 同上。
7. `python w85_analyze.py` → 双臂统计 + 判决 → PRESSURE.md。

## 2026-11-14T12:13:55+08:00 build PASS
- harness 6 件复制进 work/tools，双侧 sha256 逐对一致；已改指向（r03/W85_pressure、锁 owner=w85、V15 只读指回 r02）。
- [静态读码] ra2forge 能力证实：STANDARD_HOUSES 14 国（British=盟军、Confederation/Arabs=苏军均可作敌 house）；size 40..200 偶数方形；units/infantry 无数量上限校验；unit mission 自由字段（默认 Guard）。
- w85_build.py PASS（12:13:55）：双臂包 pkg_pressure / pkg_control，两臂 BATTLEMD.INI 同 sha256=8fb51769...（目标段一致）；MAP 实测声明：Russians MTNK=300+TESLA12+NACNST1+NAPOWR6，British/Confederation/Arabs MTNK 各 400+GAPOWR 各1；加压臂 Hunt=1200 / Guard=300，对照臂 Hunt=0 / Guard=1500；EndOfGame=yes；无 survive；Map Size=0,0,100,100。
- 声明对象总数 1522（units 1500，>> W19 B″ 800 声明）。
- 修正一处：w85_common import 笔误 w84_lib→w85_lib。
- 下一步：w85_offline.py（robocopy 沙箱 + pristine + 安装加压臂包）。

## 2026-11-14T12:20:33+08:00 offline fresh PASS
- 锁引导：r03/.game_instance.lock owner=lead（12:20:17，purpose 注明 W85 bootstrap）。
- w85_offline.py FRESH 全 PASS：real_pre 647 文件/1,989,215,270 B/277 maplike + 锚点哈希全中
  （gamemd.exe 73201cc0…、ddraw.dll 85e0f7d5…、RA2MD.INI c91c6a47…）；robocopy rc=1 成功；
  sandbox_pre 与 real 完全一致；pristine 23 项字节副本落盘；沙箱内 v0.3 uninstall exit 0
  （真目录未动；v0.3 全部文件字节在 pristine，收尾还原后树回到 v0.3 状态）；官方 BATTLEMD.INI
  2733 B 核对通过；pressure 包 inplace install exit 0；verify exit 0；installed map == pkg map。
- w85_run.py 已完成（W84 导航骨架 + W20 6ms 采样通道 + 终态三分类 + 每趟 RA2MD/ddraw 字节还原）。
- w85_analyze.py 已完成（预注册判读 + E1/E2/E3/E4 证据通道）。
- **加压臂真机 trip 已启动（12:21，后台）**：预计 ~10 分钟（含 100x100/1522 对象首载）。
- 风险预案（已冻结）：首趟异常退出/极端卡死 → 降规模 3x150 重建重跑； defeats before 240s →
  INSUFFICIENT 记录，不重试超过 1 次。

## 2026-11-14T12:24+08:00 加压臂首趟 = 引擎崩溃（如实记录）
- [本次实测] gamemd.exe 在 t_ingame 17.19 s（frame≈538）异常退出，exit code 0xC0000005
  （WER Application Error 1000：出错模块 unknown，偏移 0x15d63b8d，pid 32328，路径=sandbox_game）。
- 采样 2830 拍（6ms）已落盘 out/trip_pressure/run.ndjson；崩溃前 A8ED50 于 frame 76 转非零
  （value=1）—— 崩溃发生在 Hunt 大兵团交火开始后约 13 s。
- 崩溃时序链：加载成功（1522 对象 5s）→ 开火 → 13 s 后 AV。静态规模与交战剂量两个嫌疑未分。
- 收尾 bug：finally 格式串少一个参数 → TRIP_RESULT_pressure.json 未写、锁未释放；
  已修复脚本并手动恢复锁 owner=lead（12:23:59，purpose 注明崩溃与修复）；残留 0。
- 判别实验（预冻结预案的执行）：立即跑对照臂（同图同 1522 对象、全 Guard 零交战）
  —— 活满 300 s ⇒ 崩溃源=交战剂量 ⇒ 降加压剂量（敌 3x150+玩家 150=600 units）重跑加压臂；
  对照臂也崩 ⇒ 静态规模过大 ⇒ 两臂同降。
- [本次实测] 锚点：真目录未动（WER 路径=sandbox_game）；残留 0；配置已逐字节还原（RA2MD.INI/
  ddraw.ini 哈希==pristine）。

## 2026-11-14T12:30+08:00 判别实验 PASS + 降档决定（预冻结阶梯第 1 档）
- [本次实测] 对照臂（dose 400/300=1500 units，1522 对象，全 Guard）：300.147 s 完整窗口，
  49,751 拍 @6ms，读失败 0 / 线程查询失败 0 / 失焦 0；A8ED50 全程 0（a8ed50_first_nonzero=null）
  ⇒ 对照臂零交战被独立证实（E1 通过）；TRIP_RESULT_control_dose1500.json 已存。
- 判别结论：同图同布局同对象数下，静态 1522 对象稳定运行 300 s；唯一差异 Hunt 交战
  在 17.2 s 处 0xC0000005 ⇒ 崩溃源 = 交战剂量（同时开火的弹道/特效/寻路规模），
  **不是**静态对象规模。与 W20 四臂'静态声明量不是负载来源'结论一致且更硬。
- 降档阶梯（预冻结：800 → 600 → 400 units，最多 3 档）：第 1 档敌 3x200+玩家 200=800 units。
  旧产物已改名归档：trip_pressure_dose1500_crash / trip_control_dose1500_static /
  pkg_*_dose1500（dose1500 对照臂仍作'静态上限'旁证保留）。

## 2026-11-14T12:35+08:00 阶梯第 2 档 dose800 仍失败（如实记录）
- [本次实测] 加压臂 @敌3x200+玩家200=800 units：t_ingame 13.0-13.5 s（A8ED50 首非零 frame77
  之后 ~12.5 s）引擎弹出内部错误对话框（'has encountered an internal error'），进程未死但停摆；
  采样继续至 213.2 s 后进程自行退出（exit 0）。TRIP 已归档 trip_pressure_dose800_internalerror。
- [本次实测] 两个失败剂量（1500/800 units）的失效点都在接敌开火后 13-17 s（frame≈420-540），
  而同图 1522 静态对象 300 s 稳定 ⇒ 崩溃驱动 = 交战瞬时规模（候选：弹道/特效/寻路并发），
  非总对象数、非 Hunt 总量本身。
- 工具修正：w85_run.py terminal_kind 新增 engine_internal_error_dialog 终态识别（本次 trip
  是旧代码跑的，停摆到 213 s；下趟起会即时截断）。
- 阶梯第 3 档：敌 3x150 + 玩家 150 = 600 units（622 对象）。

## 2026-11-14T12:37+08:00 阶梯第 3 档 dose600 仍崩溃（如实记录）
- [本次实测] 加压臂 @敌3x150+玩家150=600 units：A8ED50 首非零 frame281（比前两档晚，blob 更小）
  但仍在 t_ingame 17.165 s（frame≈537，与 dose1500 崩溃帧 538 几乎一致）0xC0000005。
  已归档 trip_pressure_dose600_crash。
- 三档失效点对照：1500@17.19s(AV) / 800@~13.3s(内部错误对话框) / 600@17.16s(AV)；
  静态对照 1522 对象 300s 全绿。失效与敌 Hunt 数量弱相关、与'接敌开火'强相关，
  且 dose1500/600 崩溃帧几乎相同 ⇒ 有非剂量成分（候选：多 house 并发 Hunt、
  弹道/特效并发上限、固定调度事件）。
- 预冻结阶梯（800→600→400）用尽前先跑最后一档 400 units（敌3x100+玩家100）；
  若仍崩 ⇒ 追加单敌 house 探针（British 300 Hunt + 玩家 100）判别多-house 维度。

## 2026-11-14T12:45+08:00 阶梯末档 dose400 仍崩 + 崩溃根因取得（except.txt）
- [本次实测] except.txt（引擎在 dose800 内部错误时写入 sandbox_game/，26KB）：
  EXCEPTION_ACCESS_VIOLATION @ 0x0051C2D3，call dword ptr [eax+0x1D4] 且 EAX=0
  ⇒ **空 this 指针上的虚函数调用**（读地址 0x1D4）。栈含返回地址 0x42A595/0x429F5A/
  0x4DBE6B/0x42CC07 与重复出现的全局 0x0087E8B8（紧邻本卡监控代理 0x0087E8E0）。
  [静态读码] 崩溃 = 引擎 1.001 在某对象逻辑的 NULL 虚调用，非注入/外部因素。
- [本次实测] dose400（敌3x100+玩家100）仍在 t_ingame 14.0 s 内部错误（新终态识别即时
  截断 + 截图 screen_run_pressure_terminal_engine_internal_error_dialog.png）。
  计数阶梯（1500/800/600/400）全崩 @13-17s ⇒ 与单位数量弱相关。
- 剩余嫌疑维度：多 house 并发 Hunt（W84 先例 30 单位单 house 全程稳定）/
  tesla 大量并发 / 玩家建筑+战斗组合。判别探针（预冻结）：
  单 house（British）300 Hunt + 玩家 100 = 400 units；稳定 ⇒ 试点用单 house 设计；
  仍崩 ⇒ 降 150+50 再试一次，再崩则如实上报"安全交战规模上限"结论。

## 2026-11-14T12:49+08:00 单 house 探针仍崩（如实记录）
- [本次实测] British 300 Hunt + 玩家100（400 units）：内部错误 @ t_ingame 11.0 s
  （A8ED50 首非零 frame258=8.3s 后 ~2.7 s）；TRIP 归档 trip_pressure_singlehouse_crash。
- ⇒ 多 house 维度排除。崩溃时序规律（新增）：内部错误/崩溃出现在 A8ED50 首非零后
  ~2.5-17 s，剂量越小间隔越短（dose400=92 帧、单house=86 帧），非固定帧。
- 剩余首要嫌疑：TESLA 齐射（W84 先例 1 座稳定 vs 本卡 12 座）。判别探针（预冻结）：
  单 house + **零 TESLA**（W85_TESLA_N=0，玩家 = NACNST+6 NAPOWR+100 MTNK），
  其余不动。稳定 ⇒ 试点改用无 tesla 设计（配对对照重跑）；仍崩 ⇒ 判定
  '大兵团交战本身在 vanilla YR 1.001 上不可实例化'，转上限报告。
- build 工具已参数化：W85_TESLA_N（默认 12）。

## 2026-11-14T12:57+08:00 零 TESLA 探针仍崩（如实记录）
- [本次实测] 单 house British 300 Hunt + 玩家100无tesla：内部错误 @ t_ingame 11.0 s
  （A8ED50 首非零 frame259 后 ~2.7 s）；TRIP 归档 trip_pressure_notesla_crash。
- ⇒ TESLA 齐射排除。已排除维度：剂量(1500/800/600/400)、house 数(3/1)、TESLA(12/0)。
  常量只剩：敌方 Hunt 规模(300-1200) >> W84 已验证的 30、玩家 MTNK 大编制 Guard 回火、
  玩家基建(NACNST)在场、交战本身。
- 收尾判别（预冻结，至多 2 趟）：
  P2 = 敌 30 Hunt（W84 已验证规模）+ 玩家完整侧（100 MTNK Guard+NACNST+6 NAPOWR）；
       稳 ⇒ 悬崖在敌方 Hunt 数量（试点可跑 W84 规模敌+大玩家）；崩 ⇒ 崩溃驱动在玩家侧大编制交战。
  P1（视 P2）= W84 df 复刻×2（60 Hunt+1 TESLA，无玩家基建/坦克）。

## 2026-11-14T13:02+08:00 P2 仍崩 —— 失败矩阵收敛（如实记录）
- [本次实测] P2（敌 British 30 Hunt = W84 已验证规模 + 玩家 100 MTNK Guard + NACNST +
  6 NAPOWR + 12 TESLA）：内部错误 @ t_ingame 22.0 s（A8ED50 首非零 frame399=12.8s 后 ~9s）。
  TRIP 归档 trip_pressure_P2_enemy30_player100_crash。
- 失败矩阵（6 配置）：{1500,800,600,400}x{3house/单house}x{tesla12/0} + P2(30敌) 全崩
  @11-22s；稳定臂仅 dose1500 全 Guard 对照。唯一贯穿失败臂、缺席于全部稳定臂的要素 =
  **玩家 MTNK 大编制参与交战**（W84 df 稳定臂无玩家坦克；W19 800 对象无战斗）。
- 收官判别 P3（预冻结，最后一趟）：玩家 **0 坦克**（NACNST+6 NAPOWR+12 TESLA）+ 敌
  British 90 Hunt（>W84 的 30，<崩溃区 300）。稳 ⇒ 试点配对（对照臂同布局全 Guard）；崩 ⇒
  转上限报告（'更重战斗不可实例化'）。

## 2026-11-14T13:04+08:00 P3（零玩家坦克）仍崩 —— 失败矩阵最终收敛
- [本次实测] P3（敌 British 90 Hunt + 玩家 NACNST+6 NAPOWR+12 TESLA+0 坦克）：内部错误
  @ t_ingame 13.99 s（A8ED50 首非零 frame355=11.4s 后 2.6s）。归档 trip_pressure_P3_notanks_crash。
- 稳定/失败矩阵（8 真机趟）：
  稳定 = dose1500 全 Guard 静态对照（1522 对象，含 NACNST/NAPOWR/TESLA，300s 全绿）；
         W84 df 先例（1 TESLA vs 30 Hunt，**无 NACNST/无 NAPOWR**，分钟级稳定）[r02 签发]。
  失败 = 全部含交战的臂（7 个配置），唯一贯穿失败臂且缺席于稳定臂的要素 =
         **玩家 NACNST（建造场）在场 + 交战同时发生**（GAPOWR 被打已由 W83c 证稳定；
         tesla 被打已由 W83c/W84 证稳定；玩家坦克、house 数、tesla 数、剂量均已逐项排除）。
- 收官判别 P4（预冻结，最后一趟）：去掉 NACNST（玩家 = 6 NAPOWR + 12 TESLA + 0 坦克）+
  敌 British 90 Hunt。稳 ⇒ 试点配对照臂；崩 ⇒ P5（再无 NAPOWR，tesla 断电）仍崩则
  转上限报告；无论 P4/P5 结果如何，之后停止实验、进入分析+报告+finalize。

## 2026-11-14T13:08+08:00 P4 未生效（工具遗漏）—— 实际为 P3 复现
- [更正] W85_NO_NACNST 环境变量未实现进 w85_build.py，'P4' 构建产物与 P3 相同
  （installed map sha 05b2b5b4… 一致）；其崩溃 @14.0 s 与 P3 的 13.99 s 一致
  ⇒ [本次实测] P3 配置**可复现崩溃**（同配置两趟 13.99/14.0 s）。
- 该趟归档 trip_pressure_P4rerun_P3_replica。NO_NACNST 开关现已真正实现（含 verify 断言）。

## 2026-11-14T13:15+08:00 P4（真·无 NACNST）仍崩 —— 实验阶梯按时间盒终止
- [本次实测] P4（敌 British 90 Hunt + 玩家 6 NAPOWR+12 TESLA，无 NACNST 无坦克）：
  内部错误 @ 13.99 s（A8ED50 首非零 frame356 后 ~2.6 s）。归档 trip_pressure_P4_nonacnst_crash。
- 最终失败矩阵（8 失败配置 + 2 稳定先例）：剂量(1500/800/600/400)、house(3/1)、tesla(12/0)、
  玩家坦克(300/100/0)、NACNST(有/无) 全部逐项排除；失败臂仅剩公共要素 =
  交战 + {敌 GAPOWR / 玩家 NAPOWR / 地图 100x100 / Hunt>30} 的某个组合（[未证] 具体驱动，
  静态同布局对照稳定证明崩溃需要交战参与）。P2（30 Hunt）在 100x100+基建上 22s 崩
  ⇒ Hunt 规模悬崖假设大幅削弱（W84 30 Hunt/60x60/无基建 稳定）。
- **实验停止（时间盒，卡面规则 9）**：转入定量分析 —— 各崩溃趟的交战窗（A8ED50 首非零→
  终态）作趟内自对照（开火前 vs 开火后窗口线程 CPU 消耗率），对照臂 300s 静态窗作基线；
  产出效应量初估 + 上限证据，然后 finalize + PRESSURE.md。

---

FINAL: 2026-11-14T2026-11-14T13:22:37+08:00（一句话判决：**本卡未造出可持续观测的加压臂——全部 8 个含交战配置在 A8ED50 首非零后 2.5-9 s 触发引擎 NULL-虚调用崩溃（except.txt: 0x51C2D3 call [eax+0x1D4], eax=0），静态同布局对照 1522 对象 300 s 全绿（CPU 消耗率 20.38% 单核、0xA8ED50 全零、31.249 计数/s）；'更重战斗是否 >20% 抬 CPU' 在本轮剂量/布局内无 ≥240 s 有效窗可回答，可交付=失败矩阵上界 + 10 组短窗趟内自对照（交战/开火前 0.96-1.85×）+ 静态上界。**）

## §三 交付对照
- [x] 1. PRESSURE.md 主报告（设计/双臂对照/统计/判决/证据分级/未覆盖项）
- [x] 2. 原始产物：12 趟逐拍 ndjson（monotonic/UTC/frame/0xA8ED50/周期/cycle）；
      TRIP_RESULT_*.json；≥3 张截图（开局/交战中/终态对话框，全部 trip 齐备）
- [x] 3. UNKNOWNS.md（U1-U9）/ DISAGREE.md（D1-D8）/ PROGRESS.md（本文件）/
      HEARTBEAT.txt（全程小步落盘）
- [x] 4. 还原自证：FINALIZE.json ok=true —— 沙箱逐字节还原（identical_tree，含
      except.txt 从真目录回写——引擎崩溃时重写了沙箱内副本）；
      ra2youli 锚点哈希零改动（gamemd.exe 73201cc0… / ddraw.dll 85e0f7d5… /
      RA2MD.INI c91c6a47… / BATTLEMD.INI / ra2forge_install.json fe3bdf62…）；
      残留进程 0；锁 owner=lead。
- [x] 按任务卡 §六：未造出压力 = 如实写明 + 给出上界证据（§3 矩阵 / §5 定量）——同样算交付。

## 判据口径变更史（供复核）
1. 任务卡 §四 '相对 1.6914 ms/拍 >20%' —— 被 RULING_GPT61SOL.md Q1 作废（异图基线）。
2. Lead 指令改 'CPU 消耗率（ΣCPU/墙钟）主统计量 + 双臂试点 + 预注册比值判读' —— 已照办。
3. 引擎上界阻断预注册主比较 —— 改道『失败=交付』+ 补充性短窗自对照（PRESSURE.md §5.3）。

## 产物索引
- 主报告：W85_pressure/PRESSURE.md
- 定量：W85_pressure/out/analysis2.json + analysis2_screens.json（w85_analyze2.py 复算）
- 真机趟：W85_pressure/out/trip_*/（12 趟：10 失败配置 + 1 P3 复刻 + 1 对照静态）
- 安装/构建/收尾证明：W85_pressure/out/OFFLINE_*.json、BUILD_RESULT.json、FINALIZE.json
- 工具：W85_pressure/work/tools/w85_{build,offline,run,analyze2,finalize}.py（已参数化）
