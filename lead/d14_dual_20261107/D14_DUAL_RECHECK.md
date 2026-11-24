# D-14 双口径复算报告（D14_DUAL_RECHECK，2026-11-07）

- **性质**：纯离线文书。全程零真机：未启动任何游戏本体或启动器程序、未发起任何进程终止操作、未读取任何存活进程的内存。零采样代码：未编写任何采样、注入、转储、跨进程内存读写、线程控制、消息钩挂类代码（含其动态解析形式）。
- **写域**：本报告为本轮唯一新增产物，落 `lead/d14_dual_20261107/D14_DUAL_RECHECK.md`；母本与既有件零字节改动。
- **未 commit、未 push**（撰写时实测：`git log -1` = `2657458`，`git reflog -2` 无新增，`git status --porcelain -- lead/d14_dual_20261107` = `?? lead/d14_dual_20261107/`）。
- **本报告所有引用行号与指纹均为撰写会话实读/实算**；无法取得者一律标注「未验」，不补造。

---

## 1 目的与 D-14 未裁状态

**目的**：汇总并核定本轮 D-14 双口径复算的产出与其独立复核回件，形成可追溯的中文报告。覆盖三件事：① 两套窗口集口径（64 moving / 97 全量）下四个 Spearman 相关系数的复算与逐位比对；② 按真实 BOOT 反推的 BOOT 内方向复算（含「可算 8 个、中位 +0.4472」汇总句的核验）；③ 独立复核回件的判定与未验项登记。

**D-14 状态（按本轮任务书）**：**D-14 未裁**。本轮全部产出按双口径（64 moving / 97 全量）并列呈现，不替用户在「(A) 统一 64 moving 窗 / (B) 统一 97 全量 / (C) 双口径并列」之间做任何选择（三个选项的文字见 `lead/PENDING_DECISIONS.md:57-59`），不改任何统计口径。

**张力披露（并列呈报，不由本报告裁断）**：台账 `lead/PENDING_DECISIONS.md:138-147` 记载「D-26 已裁决（2026-11-06）……D-14 定谳 = C（双口径并列）」，并撤销「可算 8 个 BOOT、中位 +0.4472」；`lead/goal3t_nightwatch_20261102/PHASE_BY_BOOT_20261104.md:130-197` 有对应 ERRATUM。本轮任务书前提（D-14 未裁）与台账记载（D-26 定谳 C）之间的张力**不由本报告裁断**：本报告采用双口径并列写法是执行任务书铁律，不构成对任何裁决的采认或否认；复算与复核回件中使用「D-26 更正口径」仅作**计算约定**（滤 nan、偶数取中央均值），下游不得将其读作承认 D-14 已裁。

---

## 2 上游件与窗口集构造规则

### 2.1 上游件指纹（撰写会话实算 hashlib）

命令：`python -I -X utf8 -c "<逐件 sha256_file + getsize>"`（绝对路径）。结果与任务书【上游指纹】**全部 MATCH**：

| 文件 | SHA256 | 字节数 | 判定 |
|---|---|---|---|
| lead/PENDING_DECISIONS.md | `7f68fc6c6ed1ab6ba16210b611906c6189ad0af90a84b46b263a19379fbfcd48` | 50194 | MATCH |
| lead/GOAL_THREE_TARGETS_20261018.md | `2baa0de45d4125549262eb595d7518c9ce99efeee120384bf640cded8a933ede` | 759518 | MATCH |
| lead/goal3t_nightwatch_20261102/PHASE_BY_BOOT_20261104.md | `e492ce0d00828b60198a3b9583845fc408fc37d1556958b306bf965f02a55c12` | 9205 | MATCH |
| lead/goal3t_nightwatch_20261102/BATCH_XVERIFY_20261103.md | `4850e1e2eae68561b2aba814143d03d2ed8106b79e28746600dbce578379b986` | 16392 | MATCH |

同批实算的其余证据件（本会话指纹，供追溯）：`_phase_recompute.py` = `9648ef89548e8ad4b0f81a2a956af35dc642ee5775a93bf21f5f1d124e9dd725` / 8987；`_phase_recompute_out.txt` = `ca083e0292402eb6b6078f13ff2c7754da588cc92fe826569f6204ed3d143711` / 5417；`_xbatch_verify.py` = `206cbbaed070c5b7345af0ab742431245d2d627c7a4456b194100a5aabe1d68c` / 12735；`_xbatch_verify_out.txt` = `6121f747037ad0c015ed17d177810b7c38083c2d40ec9e0aa7cb9d7878562817` / 8280；`_dual_xcheck_scipy_out.txt` = `4c68a11faf29dfa7f26e03429fdf820bf5c712a834e01307e8ba53bb03049b60` / 1412；`_verify_independent_out.txt` = `f3a648f0bf1730bb67c10faf1619c5057fc7b156cab548b22365f788950b3bfc` / 4005。

### 2.2 语料与冻结口径

- 语料根：`out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip`（`_dual_recompute_out.txt:2`）。
- 现状枚举命中 `measure_w*.json` = **104 件**；公布输出 `_phase_recompute_out.txt` mtime = 2026-11-04 00:25:57，晚于该时刻的 3 件 `l3_1101v4f/g/h/measure_w0.json`（mtime 17:29/17:33/18:26）剔除 → **冻结语料 = 101 件**（`_dual_recompute_out.txt:18-22`）。
- 冻结语料：有效窗 = **97**，剔除 = 4（`l1_20261023c`、`l3_1101v3c`、`l3_1101v4b`、`l3_20261023` 的 w0，全部空样本），与公布剔除件逐一相同（`_dual_recompute_out.txt:24-29`；`_xbatch_verify_out.txt:5-13`；`BATCH_XVERIFY_20261103.md:56-59,62-68`）。
- **注意**：「公布时刻语料恰为 101 件」系 mtime 推断 + 枚举/计数/数值全吻合的间接证据，**无当时文件清单快照直证**（见 §5.2 未验(3)）。在现状语料上重跑**得不到**公布的 97 窗数字（见 §3.3）。

### 2.3 窗口集构造规则（只读既有件提取）

| 项 | 规则 | 依据（文件:行） |
|---|---|---|
| 枚举 | 趟子目录 sorted listdir + 数据根散件 w0/w1/w2 | `_phase_recompute.py:111-122`；`_dual_recompute.py:105-119` |
| 枚举（异族版） | 全递归目录遍历 | `_xbatch_verify.py:94-101` |
| 两规则等效性 | 冻结语料上两规则命中均 104、归一化集合差异 0 件；phase/xbatch 有效性差异 0 件 | `_verify_independent_out.txt:5-6`；`_dual_recompute_out.txt:30`（覆盖范围限制见 §5.2 未验(4)旁注） |
| 有效窗 | samples 存在、len(t)≥2（xbatch 规则）；phase 版另要求 t_abs0 存在 | `_xbatch_verify.py:117-125`；`_phase_recompute.py:102`；`_dual_recompute.py:133-139` |
| 64 moving 口径 | 有推进：∃k≥1 使 f[k]≠f[k−1] | `BATCH_XVERIFY_20261103.md:30`；`_dual_recompute.py:147` |
| 97 全量口径 | 全部有效窗（含无推进冻结窗） | `_xbatch_verify_out.txt:26-27` 的 all-valid 参考 |
| 变量 window | JSON 自带 window 字段（=趟内窗序 0/1/2；实证 archive_T32/w0→0、l3_20261023q/w2→2） | `_dual_recompute.py:142`；`_dual_recompute_out.txt:213,287` |
| 变量 uptime | samples.t[0] | `_dual_recompute.py:144` |
| B%（口径 B） | T=0.1s **严格大于**；平台=等 f 连续段闭区间 [i,j]，时长 t[j]−t[i]；B%=100×Σ计入/(t[-1]−t[0]) | `BATCH_XVERIFY_20261103.md:25-29`；`_dual_recompute.py:53-70` |
| BOOT 反推 | boot=round(t_abs0−t[0]) **先取整再聚类**、±2s 链式 | `_phase_recompute.py:105,124-132`；`_dual_recompute.py:145,153-162` |

B% 实现校验：15 个公布单段主导窗 B% 值最大偏差 **4.666e-06**（≤5e-6 即 5 位小数逐位吻合，`_dual_recompute_out.txt:34-50`；独立复核同值 `_verify_independent_out.txt:19-35`）；C1 旁证 n=64 Pearson r=−0.200527、Spearman ρ=−0.170611 与公布全对（`_dual_recompute_out.txt:52`；`_verify_independent_out.txt:38`；公布 `_xbatch_verify_out.txt:18`）。

---

## 3 两套口径四个相关系数复算

### 3.1 结果总表（双口径并列，不选口径）

| 口径 | n | ρ(window, B%) | ρ(uptime, B%) |
|---|---|---|---|
| **64 moving**（§522 口径） | 64 | **−0.040268**（4dp **−0.0403**；repr −0.04026776101462127） | **+0.039451**（4dp **+0.0395**；repr 0.03945103538787863） |
| **97 全量**（§528 异族口径） | 97 | **+0.347432**（4dp +0.3474；repr 0.347432459482872） | **+0.346119**（4dp **+0.3461**；repr 0.3461192878606675） |

公布值出处：64 moving 4dp 见 `GOAL_THREE_TARGETS_20261018.md:2465-2466` 与 `PHASE_BY_BOOT_20261104.md:13`、`:49`；6dp 见 `GOAL:2935`、`_xbatch_verify_out.txt:26`。97 全量见 `GOAL:2936`（+0.347432/+0.346119）、`PHASE_BY_BOOT_20261104.md:14`、`:50`、`_xbatch_verify_out.txt:27`。

### 3.2 逐项命令与输出

**命令①（复算主线，手写实现）**：`cd lead/d14_dual_20261107 && python -I -X utf8 _dual_recompute.py > _dual_recompute_out.txt 2>&1` —— 复算时 EXIT=0。本报告撰写会话复跑（subprocess 捕获 stdout 与既有件比对）：**EXIT=0、stderr=0 字节、311 行；去首行运行时刻戳后与 `_dual_recompute_out.txt` 逐字节相同**（两侧 rest SHA256 = `38db50a1df7f33c5823c8a689db952c8307481903b751108bced113ecfa7d5a3`，REST_IDENTICAL=True），四个系数 repr 与中位/P3/缺陷复现共 7 个关键值均在新鲜输出中出现。输出锚点：

- 64 moving ρ(window,B%)：`_dual_recompute_out.txt:58` → `−0.040268 (repr −0.04026776101462127)`
- 64 moving ρ(uptime,B%)：`:59` → `+0.039451 (repr 0.03945103538787863)`
- 97 全量 ρ(window,B%)：`:61` → `+0.347432 (repr 0.347432459482872)`
- 97 全量 ρ(uptime,B%)：`:62` → `+0.346119 (repr 0.3461192878606675)`

**命令②（scipy 独立实现交叉复核）**：`python -I -X utf8 _dual_xcheck_scipy.py > _dual_xcheck_scipy_out.txt 2>&1` —— EXIT=0。撰写会话直接复跑，输出与既有件逐行一致。四系数偏差：window-moving **6.939e-18**、uptime-moving **0.000e+00**、window-全量 **0.000e+00**、uptime-全量 **5.551e-17**，全部 ≤1e-16（`_dual_xcheck_scipy_out.txt:6-11`）。注：复算回件文字写「≤6.9e-18」，实文件 `:11` 为 5.551e-17，**以文件为准**（两者均 ≤1e-16，不影响结论）。

**命令③（独立复核员第三实现）**：`cd lead/d14_dual_20261107 && python -I -X utf8 _verify_independent.py > _verify_independent_out.txt 2>&1` —— 复核会话 EXIT=0。该实现不复用复算员或上游任何 .py 代码（逐样本扫描 B%、bisect 二分平均秩、独立 Pearson），四系数与复算员 repr **逐位相同、|dev|=0.000e+00**（`_verify_independent_out.txt:13-17`）。

**逐位比对公布值**：`_dual_recompute_out.txt:115-123` 九行全 **MATCH**（−0.0403 对 `GOAL:2465`；+0.0395 对 `GOAL:2466`；−0.040268/+0.039451 对 `_xbatch_verify_out.txt:26`；+0.347432/+0.346119 对 `_xbatch_verify_out.txt:27` 与 `GOAL:2936`；+0.3474/+0.3461 对 `PHASE_BY_BOOT_20261104.md:49-50`；P3 −0.2369 对 `_phase_recompute_out.txt:59` 与 `PHASE_BY_BOOT_20261104.md:19,96`）。

### 3.3 语料漂移敏感性（仅披露，非第三口径）

现状语料 104 件命中 → 99 有效（v4f/g 有效且无推进、v4h 空样本）：

- 64 moving 口径**逐位不变**（ρ(window)=−0.040268、ρ(uptime)=+0.039451；`_dual_recompute_out.txt:148-150`；`_verify_independent_out.txt:58`）。
- 97 全量口径变为 n=99：ρ(window)=**+0.314679**、ρ(uptime)=**+0.305584**（`:151-153`；`_verify_independent_out.txt:57`）；BOOT 数 11→12（新增 11-04 13:52，2 窗 0 推进，`:155,169`）；P3 变为 −0.235089（n=12，`:203`）。
- ⇒ **引用公布值必须注明「冻结语料=公布时 97 窗」**；在现状语料上重跑将得不到 97 窗数字。本节不构成第三口径（`:205-207`）。

---

## 4 BOOT 内方向复算

### 4.1 BOOT 反推与聚类（11 个，逐行吻合）

boot=round(t_abs0−t[0]) 先取整、±2s 链式聚类，冻结语料得 **11 个 BOOT**（`_dual_recompute_out.txt:64-77`），与公布 `_phase_recompute_out.txt:9-19` 逐行吻合（趟数/窗数/有推进/uptime 范围全同；独立复核「ALL 11 ROWS EXACT = True」；scipy 复跑亦 BOOT 数=11，`_dual_xcheck_scipy_out.txt:13`）。BOOT 反推的**绝对时刻真值**未与台账核对——`PHASE_BY_BOOT_20261104.md:120` 自述「只有 BOOT#6/#8 与台账对得上」（见 §5.2 未验(1)）。

### 4.2 P2 BOOT 内表（moving 且 n≥3，8 行）

| BOOT | n | ρ(uptime,B) | ρ(window,B) |
|---|---|---|---|
| 10-16 12:10 | 16 | −0.2176 | +0.4920 |
| 10-19 14:31 | 6 | +0.6547 | +0.5477 |
| 10-21 09:45 | 12 | −0.4685 | −0.3844 |
| 10-26 15:14 | 3 | −0.5000 | +0.0000 |
| 10-30 13:10 | 5 | +0.4472 | +0.8250 |
| 10-31 08:26 | 13 | −0.8061 | +0.0058 |
| 11-01 15:51 | 3 | nan（零方差） | nan |
| 11-03 08:54 | 3 | nan（零方差） | nan |

本算表 `_dual_recompute_out.txt:82-89`，与公布 `PHASE_BY_BOOT_20261104.md:62-69`、`_phase_recompute_out.txt:41-48` 的 n、两列、nan 位置**全 MATCH**（`:126-134`）；scipy 复跑同值（`_dual_xcheck_scipy_out.txt:16-23`）；独立复核同值（`_verify_independent_out.txt:42-49`）。

### 4.3 方向核验

- **uptime 列**：有限值 6 个（nan 2 个），**正 2 / 负 4**（`_dual_recompute_out.txt:91`；`_verify_independent_out.txt:50`）。有限值排序 = [−0.8061, −0.5000, −0.4685, −0.2176, +0.4472, +0.6547]（`:92`）。⇒「4 负/2 正」**成立，但只描述 uptime 列**。
- **window 列**：正 4 / 负 1 / 零 1（[+0.4920, +0.5477, −0.3844, +0.0000, +0.8250, +0.0058]），与 `PENDING_DECISIONS.md:147` 的指认一致——「4 负/2 正」**不能概括 window 列**。
- **「可算 8 个、中位 +0.4472」不成立**：8 行中 2 行为 nan（零方差），可算数 = **6**（非 8）。原句出处：`PHASE_BY_BOOT_20261104.md:71`、`GOAL_THREE_TARGETS_20261018.md:3505`、`PENDING_DECISIONS.md:55`。
- **原缺陷精确复现**：重跑同款缺陷实现 `sorted(within)[len//2]`（含 nan，未滤、未取中央均值；缺陷代码仍在 `_phase_recompute.py:189`（nan 也 append）、`:195-196`（len() 当可算数）、`:197`）得 **0.4472135954999579**（`_dual_recompute_out.txt:94,142`；`_verify_independent_out.txt:52`）——即公布「+0.4472」是该缺陷的**确定性产物**。
- **更正口径中位**：滤 nan、偶数取中央两项均值 → **−0.343089**（repr −0.343089263677499；`_dual_recompute_out.txt:93,141`；scipy `statistics.median` = −0.343089264，`_dual_xcheck_scipy_out.txt:24`；独立复核 −0.34308926367749898，`_verify_independent_out.txt:51`）。按公布四位小数表值推算的 −0.34305（`PENDING_DECISIONS.md:145`；`PHASE_BY_BOOT_20261104.md:152`）与本算差 3.9e-05，系表值 4dp 舍入所致——本算由此闭合 `PHASE_BY_BOOT_20261104.md:188`（ERRATUM §六.1「原始精度下的中位数未验」）。

### 4.4 P3 BOOT 间

ρ(BOOT均值 uptime, BOOT均值 B%) = **−0.236903**（repr −0.2369026647406667，n=11；`_dual_recompute_out.txt:110`）；scipy −0.236902665（`_dual_xcheck_scipy_out.txt:27`）；独立复核 −0.23690266474066671（`_verify_independent_out.txt:53`）；公布 4dp −0.2369（`_phase_recompute_out.txt:59`；`PHASE_BY_BOOT_20261104.md:19,96`）。

### 4.5 口径标注（本节双口径说明）

§4.1–§4.4 的 11-BOOT 表、P2/P3 表值均在**冻结语料（97 全量窗口集）**上计算——与公布口径一致。**64 moving 口径下的 BOOT 内方向表原公布未提供、本轮亦未单独复算 → 未验**；本报告不代用户补算选边（见 §5.2 未验(5)）。

---

## 5 独立复核回件与未验项

### 5.1 独立复核回件（verdict = confirmed）

**被核对象 SHA256 = a63b968edd900be829aff3a6b241bf047040dafc4b90376e3b4f2c8c6f00cf76，字节数 = 24580  <- lead/d14_dual_20261107/_dual_recompute_out.txt**（本报告撰写会话以 `python -I -X utf8` + hashlib 实算，与复核回件所报一致）。

- **判定**：`confirmed`（非 refuted/partial，故不标 unconfirmed）。复核自报 37 次命令实跑，其中 4 次为后台扫描；3 次全库遍历扫描超时未产出结果（复核如实标注、未计为通过），1 次 find 完成且结果为空。
- **五项复核全部实跑通过**：① 窗口集构造规则（自读上游件 + 两规则枚举对比 + 全 101 件 phase/xbatch 有效性交叉表：两者皆真 97、皆假 4、不同 0）；② 四系数独立复算（|dev|=0.000e+00 ×4，见 §3.2 命令③）；③ 无单报、未选口径、未把 D-26 当用户已裁（回件全程 64/97 并列，明写「未替用户选 A/B/C」「张力不由本线裁断」）；④ 四数值实跑支撑、未验未被写成已验（复算回件 4 条未验逐条核实仍为未验）；⑤ 写域之外零改动（上游 8 件指纹 MATCH、mtime 均早于复核时刻；find 写域外改动扫描为空；git HEAD 仍 2657458、reflog 无新增；禁用模式扫描无命中；复核自身仅写入 `_verify_*` 四件）。
- **复核员重跑复算员两脚本**：`_dual_recompute.py` 重跑件 `_verify_dual_rerun.txt`（24580 字节）与原 out.txt 除首行时刻戳外逐字节相同（复核口径 rest SHA256 双侧同为 `28354c2cb837bc2055ace01f899025cde2c5657fb0b16c3e0c411ded97146266`）；`_verify_scipy_rerun.txt` 与 `_dual_xcheck_scipy_out.txt` **逐字节相同**（本会话实算两者 SHA256 同为 `4c68a11faf29dfa7f26e03429fdf820bf5c712a834e01307e8ba53bb03049b60` / 1412）。
- **复核员指出的破口（均不改四个数字，本报告已采纳更正）**：
  1. **证据链行号错指**：复算回件把四系数值标作「PHASE_BY_BOOT:25-26/:30-31」、P3 标「PHASE_BY_BOOT:59」；实读 `PHASE_BY_BOOT_20261104.md` :25-26 为方法文字、:31/:59 为层次说明/空行，数值实际在 **:13/:14/:49-50**、P3 在 **:19/:96**；「PHASE:25/:26/:30/:31/:59」只有理解为 `_phase_recompute_out.txt` 才成立（该文件相应行本会话已实读核实）。本报告全部按正确行号引用。
  2. 「两规则等效」的原检验只在 phase-valid 行内查 len(t)==len(f)（`_dual_recompute.py:139,324-325`），查不出「xbatch 有效但 phase 无效（缺 t_abs0）」方向；复核员补跑全 101 件交叉表后差异 0，当前语料未触发。
  3. 「冻结语料=公布时 101 件」是 mtime 间接推断（→ 未验(3)）。
  4. D-14 未裁 vs 台账 D-26 定谳 C 的张力（本报告 §1 已披露）。
  5. 数字层潜在崩点（现状语料重跑 ≠ 97 窗数字；B% 全量无第三方逐窗值；缺陷脚本仍在仓）均已被复核覆盖或如实标注。

### 5.2 未验项（单独节，全部未验、未被写成已验）

1. **BOOT 反推时刻真值**未与台账核对——`PHASE_BY_BOOT_20261104.md:120` 自述仅 BOOT#6/#8 与台账对得上；本轮只验证「同规则重跑结果一致」，未验证 BOOT 时刻真值。
2. **`_phase_recompute.py:189,:195-197` 缺陷仍在仓内未修**（该文件本会话实算指纹 `9648ef89…d725` 与公布时一致，未改）；本线只在内存复现其行为，未改该文件（ERRATUM `:189` 同此状态）。复用者会重犯同一错误。
3. **「公布时刻语料恰为 101 件」**系 mtime 推断 + 枚举/计数/数值全吻合的间接证据，无当时文件清单快照直证；若有后到件被回填旧 mtime、或有当时存在后被删除的件，101→97→64 窗口集会变，97 全量系数随之变（现状 104 件时已实测变为 +0.314679/+0.305584）。
4. **97 窗全量 B% 无逐窗第三方公布值可对**：B% 仅 15 窗经公布值核对（≤5e-6）；scipy 交叉件与手写实现共用同一 B% 语料读取定义（定义同 `BATCH_XVERIFY_20261103.md:24-36`），非完全独立的 B% 定义复核。另，「两规则等效」检验对「缺 t_abs0 但样本完整」方向覆盖不全（当前语料未触发，见 §5.1 末条 2）。
5. **64 moving 口径下的 BOOT 内方向（P2）表**未公布、本轮未单独复算 → 未验。
6. **现状语料 BOOT 数 = 12** 仅由重跑复算脚本输出确认（`_dual_recompute_out.txt:155`），未做独立第三实现复核（复核员标注）。
7. 复核回件文字「四系数偏差 ≤6.9e-18」与实文件 `_dual_xcheck_scipy_out.txt:11`（5.551e-17）不符——以文件为准，两者均 ≤1e-16，不影响结论；登记为回件文字层面瑕疵。

---

## 6 结论

1. **四个系数两口径复现成立**：64 moving 口径 ρ(window,B%)=−0.040268、ρ(uptime,B%)=+0.039451；97 全量口径 +0.347432、+0.346119。三路实现（手写定义实现、scipy、独立复核员第三实现）+ 本报告撰写会话复跑（主线去首行时刻戳后逐字节一致、scipy 件逐字节一致）相互印证，与 §522（4dp）、§528 异族（6dp）、PHASE_BY_BOOT（4dp）公布值**逐位 MATCH**；scipy 交叉偏差最大 5.551e-17 ≤1e-16。
2. **「可算 8 个 BOOT、中位 +0.4472」确认不成立**：8 行中 2 行 nan，可算 = 6；「+0.4472」是原缺陷实现（未滤 nan、未取偶数中央均值）的确定性产物（精确复现 0.4472135954999579）；更正口径中位 = **−0.343089**（原始精度），与按公布 4dp 表值推算的 −0.34305 差 3.9e-05（表值舍入所致），闭合 ERRATUM §六.1。「4 负/2 正」只描述 uptime 列，window 列为负 1/正 4/零 1，方向不一致的定性仅在 uptime 列内成立，且不能据此强化任何机制结论（样本极小、BOOT 多为反推）。
3. **双口径并列、不选口径**：本报告全程 64 moving 与 97 全量并列呈现、逐项注明窗口定义/n/变量/出处；不替用户在 (A)/(B)/(C) 之间做选择，不改任何统计口径。语料漂移数字仅作披露，**不构成第三口径**。
4. **D-14 仍待裁**（按本轮任务书前提）。台账 `PENDING_DECISIONS.md:138-147` 关于 D-26 定谳 C 的记载如实披露、并列呈报，不由本报告采认或否认；「D-26 更正口径」在本文中仅为计算约定。
5. **引用纪律**：引用公布值须注明「冻结语料=公布时 97 窗」；在现状语料上重跑将得到不同数字（97 全量 → n=99：+0.314679/+0.305584）。§5.2 所列 7 项未验不得当已验引用。
6. **合规**：零真机、零采样代码、母本与既有件零字节改动、未 commit、未 push；本报告唯一写域产物为 `lead/d14_dual_20261107/D14_DUAL_RECHECK.md`。
