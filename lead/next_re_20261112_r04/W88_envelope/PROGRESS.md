# W88 ENVELOPE · PROGRESS

> **FINAL: 2026-11-14T15:04:51+08:00（Get-Date 实测）**
> 一句话判决：**崩溃边界 = `NAPOWR` 底座重叠（col 步长 2 ⇒ 同格链破坏）。
> 保留重叠：任何交战剂量间歇性崩（C1 1/3、C4 1/3、C7 1/1；崩法=0x47C538 垃圾 vptr
> 遍历被破坏的 CellClass 对象链）。步长改 3（零重叠）：同布局含全剂量 1200 Hunt 的
> 持续交战 0/4 崩、全部跑满 ≥120 s，配对对照 CPU 33.61% vs 18.10%（比值 1.857，
> 初估抬升 85.7%），A8ED50 非零拍 94.05% vs 0%。`Crewed=no` 不消除失效（C4 1/3）。
> 稳定/崩溃的边界配置：**W85 几何仅把 6×NAPOWR col 步长 2→3 一处改动。**

## FINAL 交付对照（任务卡 §七 逐条）

- [x] ENVELOPE.md：B0…C7 矩阵、逐步结论、驱动因素判决（重叠=必要因子，乘员=非必要）、
  最大稳定交战配置（C6：全剂量 1200 Hunt + 零重叠 + 全基建，150 s 稳定）+ 配对对照
  CPU 消耗率 33.61%/18.10% 与 A8ED50 占比 94.05%/0%、分级、未覆盖项。
- [x] 每趟 out\trip_*：ndjson、TRIP_RESULT、D1 归档（3 个崩趟全部 fresh except.txt+WER+
  ndjson 尾部/完整）、截图 ≥3 张（例外：trip_C1/trip_C3/trip_C4 因 U1/U4 事故为混合
  目录，细节见 UNKNOWNS §U1/U4 与 ENVELOPE §10；四趟丢失 ndjson 已用唯一目录干净
  重跑补齐）。
- [x] UNKNOWNS.md（U1–U7）/ DISAGREE.md（D-1…D-5）/ PROGRESS.md（本文件）/
  HEARTBEAT.txt / FINALIZE.json。
- [x] 真目录零改动自证：FINALIZE.json real_dir_diff.identical_tree=true、5 锚点全等、
  锁 owner=lead、gamemd 残留 0。
- [x] 判决含"稳定/崩溃"边界配置（见顶部一句话判决）。

---

> 卡：NEXT_RE_20261112_R04 · W88（安全交战包络定位，真机）
> 执行：子代理 `w88-envelope`（GLM-5.3-Flash）｜写域：`lead/next_re_20261112_r04/W88_envelope/`
> 本文件小步落盘：每趟结束立刻更新（时间戳一律 Get-Date 实测）。

---

## 已知输入与预注册

- **唯一问题**：vanilla YR 1.001 上"带基建的可持续交战"边界在哪？哪一个因素把
  「分钟级稳定」翻成「开火后 2.5–9 s 必崩」？
- **基线**：W84 df（r02 签发）= 60×60 / 1 TESLA / 30 British Hunt / 无基建 /
  32 对象，分钟级稳定。B0 = 该配置的**精确重建**（Lead 事实 3 提供的结构）。
- **Lead 事实 1/2 已采纳**：不复用 `w85_design_pressure.json`（该文件现存内容是
  P4 配置）；所有几何由本卡 `w88_build.py` 新写，并按 D4 归档到 `out/inputs/<step>/`。
- **工具缺陷整改**：D1（崩溃取证即时归档）、D2（outcome 语义拆分 + ok 门禁）、
  D4（每趟输入归档 + sha256）已在 `w88_run.py` 实现，注释内预注册。
- **配对对照判据（预注册，跑 CTRL 前冻结）**：主统计量 = 窗口线程 CPU 消耗率
  （Σ GetThreadTimes kernel+user ÷ 墙钟，单核占用率%）；窗口 = 两趟同取
  elapsed_ingame [0, min(T_end_combat, T_end_ctrl)]；同窗报 0xA8ED50 非零拍占比。
  比值 <1.10 ⇒ 「本配置下未观测到与交战成比例的负载抬升」；≥1.10 ⇒ 「初估抬升 X%」。
  禁止显著性语言。

## 设计改道（Lead 两次改道，全部留痕）

### 改道 1（2026-11-14 13:49，W89 复核结论转入）
- W89 + Lead 逐字节复核发现 R03 因果归因混杂：崩溃指令 `0x0051C2D3` 属
  `0x0051BF90` = **InfantryClass::IsCellOccupied**（vtable `0x007EB204`）——
  崩在"步兵单元格占用检查"，不是坦克开火。
- W85 静态对照非单变量：对照 `X87E8E0` 全程恒 `0xFFFFFFFF` 0 次变化（完全没动），
  Hunt 臂首非零前已变化 322–383 次。
- `0xA8ED50` = Bullet 向量 Count（遍历上界），不是开火锚。**报告禁用"开火后 X s"措辞**，
  改用两个机械锚：**A8ED50 首非零样本 idx** 与 **X87E8E0 首次变化 idx**（runner 已实现）。
- 两个高怀疑结构因子：① `Crewed=yes` 建筑被毁 → 生 InfantryClass 幸存兵
  （NAPOWR/NACNST/GAPOWR 均 Crewed=yes，TESLA=no，MTNK 默认 no）；
  ② NAPOWR Foundation 3×2 但 W85 摆位 col 步长 2 → 底座重叠。
- 原计划 R1/R2/R3/R4（P4 崩溃基线）——被改道 2 替换。

### 改道 2（2026-11-14 13:53，Lead 承认任务卡引用错误）
- **B0/B1 重新定性**：B0 terminal=defeat_restart_dialog @t≈9 s、B1 @t≈31 s ——
  都是"玩家被灭→重开框"，**不是稳定交战**。W84 df 本来就是故意必败局，
  任务卡把它当"分钟级稳定先例"是引用错误（Lead 自纠）。
- **新基线 = W85 已证绿对照臂几何**（100×100，1522 对象，玩家 NACNST+6 NAPOWR+12 TESLA+300 MTNK Guard，
  敌 3 house 各 400 Guard；300.15 s 全绿、A8ED50 全 0、X87E8E0 恒 -1）。

### 新阶梯 C0–C5（预注册判读，跑前写死）
| 臂 | 相对绿基线的唯一改动 | 目的 |
|---|---|---|
| C0 | 无（复跑确认绿） | 基线可复现 |
| C1 | 仅 British 30 MTNK → Hunt（其余 1170 Guard） | 最小交战剂量 |
| C2 | 全部 1200 敌 MTNK → Hunt | 阳性对照（预期崩，≈W85 P 系） |
| C3 | C2 + NAPOWR col 步长 2→3（去底座重叠；占地变化，非严格单变量——如实写明） | 判"底座重叠" |
| C4 | C2 + 包内地图追加 `[NAPOWR] Crewed=no`（ra2forge 无 rules 覆写支持 → 构建后字节追加段；引擎是否采纳无法静态保证——如实写明） | 判"乘员生兵" |
| C5 | C2 + C3 + C4 | 协同确认 |

**判读**：C1 就崩 ⇒ 30 单位交战+本基建/图即触发（与剂量无关），直接做 C3/C4 分离；
C1 绿、C2 崩 ⇒ 有剂量关系，再以中间剂量（100/300 Hunt）二分找阈值（正向结果）；
C3 或 C4 任一绿 ⇒ 该因素即主因；都崩 ⇒ 两因子均非充分，如实记录"驱动未定"。

### D2 语义 v2（本卡已实现）
- `defeat_restart_dialog` ⇒ ok=false，outcome=`DEFEAT_DIALOG_AT_<t>s` / `VALID_WINDOW_DEFEAT_DIALOG`；
- engine_internal_error_dialog ⇒ ok=false，`ABORTED_ENGINE_ERROR` / `VALID_WINDOW_WITH_ENGINE_ERROR`；
- 进程自杀（AV 码）⇒ ok=false；≥120 s 无终态或胜利屏 ⇒ ok=true。

## 趟矩阵（实时更新）

| 步 | 配置 | 状态 |
|---|---|---|
| B0 | W84 df 重建（必败局，重定性） | ✅ 跑完：defeat_restart_dialog @9.0 s，150 s 会话存活无引擎错误（**不算稳定交战**；D2v1 字段曾误标 ok=true，已修为 v2 语义，磁盘 TRIP_RESULT 保持历史原样，以本表为准） |
| B1 | B0+6 NAPOWR（col 步长 3，无重叠） | ✅ 跑完：defeat_restart_dialog @31.0 s，150 s 会话存活无引擎错误（同上重定性；无重叠+有 NAPOWR 下未崩，方向性参考点） |
| C0 | 绿基线复跑 | ✅ 2026-11-14 13:59:41 **绿**：150.003 s，无终态，A8ED50 全程 0（0/24874），outcome=VALID_WINDOW_target_reached ok=true |
| C1 | +30 Hunt | ❌→**崩** 2026-11-14 14:01:27：**30 个敌 Hunt（其余 1170 Guard）就够触发**——engine_internal_error_dialog @t_ingame≈55 s（A8ED50 首非零 idx=353 @2.55 s/frame140；X87E8E0 首变 idx=3 @0.02 s，127→128）；D1 已即时归档 except.txt（26,515 B，fresh）+WER+ndjson 尾部至 out/trip_C1/；outcome=ABORTED_ENGINE_ERROR ok=false。⇒ 剂量无关性成立（30 Hunt+本几何即崩），按预注册跳过 C2（W85 8 个崩溃臂已是阳性对照），直接 C3/C4 分离 |
| C2 | +1200 Hunt | **跳过**（C1 已崩 ⇒ 预注册走 C3/C4；阳性对照由 C1 本身 + W85 签发矩阵承担） |
| C3 | C1 布局 + NAPOWR col 步长 2→3（零重叠） | ✅ **0/3 崩**：a 绿（TRIP_RESULT_C3.json）、b 绿（trip_C3_b 干净目录）、c 绿 150.2 s（trip_C3_c 干净目录）；交战真实发生（b 趟 A8ED50 首非零 idx=434 @2.73 s）⇒ **去重叠把失效率降为 0（本样本量）** |
| C4 | C1 布局 + `[NAPOWR] Crewed=no`（重叠保留） | ❌→**1/3 崩**：a 绿（TRIP_RESULT_C4.json）、**b 崩 @55.08 s**（干净目录 trip_C4_b，完整 ndjson+D1）、c 绿 150.0 s ⇒ **乘员抑制不消除失效，1/3 与 C1 同率** |
| C5 | +两者 | **跳过**（C4 已证乘员抑制不消除失效，联合臂无判别信息） |
| C6 | C3 修复 + 全 1200 Hunt | ✅ 2026-11-14 14:13:03 **绿（单趟）**：150.145 s 无终态；A8ED50 首非零 idx=53 @0.32 s（交战即刻持续）；X87E8E0 首变 idx=5；全窗非零拍 94.05%。**间距修复后全剂量可持续** |
| CTRL_C6 | C6 布局全 Guard | ✅ 2026-11-14 14:20:51 **绿（单趟）**：150.002 s，A8ED50 全 0（0/24892）——零交战对照成立 |
| C7 | C2 基线（1200 Hunt，重叠保留）+ Crewed=no | ❌ **崩（单趟）** 2026-11-14 14:21:59：engine_internal_error_dialog @12.0 s（A8ED50 首非零 idx=194 @1.29 s；X87E8E0 首变 idx=1）；D1 已归档（except.txt 26,705 B fresh）。**判读**：乘员抑制未阻止全剂量崩溃 ⇒ 要么覆写未被引擎采纳，要么乘员生兵不是本崩法（0x47C538 垃圾 vptr）的必要条件——两解并存，[未证] |

## 间歇性失效与 k/N 预注册（Lead 硬要求，2026-11-14 14:25 后执行）

- **C1 是间歇性失效**：trip 1（14:01:27）崩 @55 s；trip 2（14:16:40，目录复用事故，
  run.ndjson 被覆盖，仅 D1 归档件留存崩溃侧证据）跑满 150 s 绿；trip 3（14:27，
  trip_C1_c 干净目录）绿。**单趟绿/崩都不能判别。**
- **预注册（跑前写死）**：C1 / C3 / C4 各 **N=3**，报 k/3。
  - 仅当 C1 k/3 ≥ 1 且 C3 或 C4 k/3 = 0 ⇒ 才可写"该因子使失效率降为 0（本样本量 N=3）"；
    **不得**写"主因/充分原因"。
  - 若三臂 k 都 >0 ⇒ 如实写"三因子都不足以在本样本量下消除失效"。
  - C6/CTRL_C6/C7 各单趟，一律标"单趟，不足判别"。
- **trip 目录唯一化（已修复）**：runner 现按 trip_<STEP>、_b、_c… 取新目录，
  Sink tag/截图/归档全部带后缀；TRIP_RESULT_<STEP><suffix>.json 不再覆盖。
  （事故：trip_C1 第二趟覆盖了第一趟 run.ndjson——崩溃侧证据因 D1 快照幸存，
  采样侧 ndjson 永久丢失，如实记录。）

## 两种崩法并存（Lead 反汇编，写进报告）

- **场景甲（本轮 C1/C7 新鲜现场，已归档）**：`EIP=0x0047C538`，
  `mov esi,[ecx+0xE4]`（CellClass::FirstObject）→ 链上对象取 `mov eax,[esi]`（vptr）
  → `call [eax+0x2C]`（WhatAmI，比较==6 BuildingClass）时 **EAX=0x000A0008（垃圾 vptr）**，
  访问 0x000A0034。全局门控 `[0xA8E9A0]` 为 0 时该遍历直接返回。
- **场景乙（R03 转述，未归档，不可复核运行时半部）**：`0x0051C2D3`
  `call [eax+0x1D4]`，EAX=0（NULL this），属 InfantryClass::IsCellOccupied。
- **两者不得混同**：R03 把 8 臂套用同一种崩法是错的。本轮归档件全部是场景甲。

**基线调整说明（2026-11-14 14:01，Get-Date）**：预注册原文 C3/C4 以 C2 为基线；
因 C1（30 Hunt）已崩，把 C3/C4 的对照基线改为 **C1**（唯一差异更小：30 Hunt vs 1200 Hunt
不影响待测因子——NAPOWR 间距 / Crewed——且更省时）。C3 = C1 布局 + NAPOWR col 步长 3；
C4 = C1 布局 + `[NAPOWR] Crewed=no`；C5 = 两者。构建包 C3/C4/C5 已在 13:56 按原 C2 基线
构建（1200 Hunt）——**需要按 C1 基线重建**（hunt 参数不同）。重建中。


### 工具修复记录（本卡实施中发现）
- r04 锁文件不存在 → runner 增加 bootstrap（无锁文件时先写 owner=lead 再 claim w88）。
- `ra2youli` 自带既存 `except.txt`（26,272 B，mtime 2026-11-13 06:29，随 robocopy 进沙箱基线）→
  D1 归档按 trip 起始时间分类 fresh/pre_existing，只归档崩溃新写件；finalize 增加崩溃后
  except.txt 从真目录逐字节还原（避免 identical_tree 误报）。基线既存件不视为崩溃证据。
- 2026-11-14 13:42–13:46（Get-Date）：trip_B0 完成；锁已还 owner=lead；残留 0；
  RA2MD.INI/ddraw.ini 逐字节还原自证（byte_identical=true）。


## 工具/环境事件

- 2026-11-14 13:28–13:39（Get-Date 实测区间）：卡目录建立，工具链自 W85 复制改名
  （w88_lib/common/build/run/offline/finalize），`w88_build.py` 全新生成
  （B0 精确重建 W84 df；B1/B2/B3 单因素；B4–B7 组合/扩展步预注册在案）。
  gamemd 残留 0；锁 owner=lead。
