# 复核员-V2 第二道独立复核报告：时代效应与版本混淆核验审查与独立复算

- **复核员代号**：复核员-V2（第二道独立复核员）
- **复核对象**：`lead/goal3t_nightwatch_20261102/swarm_20261104/XVERIFY_S544_ae38d56c/V2/REPORT.md`
- **复核日期**：2026-11-04
- **数据根目录（只读）**：`D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip`
- **复核纪律遵守情况**：
  1. **零真机**：未启动 `gamemd.exe` / `ra2loader.exe` / `YURI`，未执行 `taskkill`，未读取任何运行中进程内存；
  2. **零改动母本**：原始数据 JSON、PNG、日志、母本二进制与 carrier 全部以只读方式打开，未作任何增删改；
  3. **写域受限**：所有计算脚本与输出文件严格限制在 `D:/Project/ra2-campaign-forge/lead/goal3t_nightwatch_20261102/swarm_20261104/XVERIFY_S544_ae38d56c/V2/` 内部；
  4. **独立复算**：独立编写 Python 脚本（`recheck_scan.py`, `recheck_edges.py`, `recheck_v2_a1.py`, `recheck_v2_a2.py`, `recheck_v2_a3.py`, `recheck_v2_a4.py` 等），使用 `python -I -X utf8` 独立执行，从底层字节、哈希、时间戳、帧序号差分与 JSON 数据结构重新计算，未直接采信第一道核验报告的现成数字。

---

## 〇、复核总览与结论汇总

| 主张编号 | 核心命题 | 第一道自报结论与裁决 | 第二道复核判定 | 独立复算核心数值与验证事实 |
| :--- | :--- | :--- | :---: | :--- |
| **V2-A1** | 关键对照时段 fps 与 units0 负载跨度 | CONFIRMED（fps 复算属实但并非同负载） | **CONFIRMED（复核确认）** | 逐窗差分复算通过：`v4d/w0` live_fps=31.1807 (fps_avg=31.1619, units0=1225)；`v4e/w0` live_fps=31.2864 (fps_avg=31.2801, units0=1189)；`l1c/w0` live_fps=9.2213 (fps_avg=9.1603, units0=881)；`hb/w0` live_fps=6.7911 (fps_avg=6.7872, units0=1347)；`hb/w1` live_fps=4.7584 (fps_avg=4.7317, units0=1347)。快组 units0 均值 1207.0 vs 慢组 1114.0，负载差异 7.7% 至 35.0%，l1c units0=881 超出 [1180, 1360] 范围，同负载假说破产。 |
| **V2-A2** | 高负载带内快慢与 harness 工具链版本共线性 | REFUTED（推翻 §544 时代效应独立因果） | **CONFIRMED（确认推翻）** | 在 `units0 ∈ [1180, 1360]` 内 22 个有效推进窗中：快窗 (>=28fps) 8 个 100% 为 harness8_v4 (sha16: 38244d2907e7f7fa)；慢窗 (<15fps) 12 个 100% 为非 v4 旧版（5×v3, 4×h8, 3×h3）。2×2 列联表 fast_v4=8, fast_nonv4=0, slow_v4=0, slow_nonv4=12，相关系数 $\phi = +1.000000$ 绝对共线。且 `l1c` 地图为 `0add791d`（与 v4 的 `f3bb0a4e` 不同），`qc151_fields.json` 显示 `h7_measure_start_frame` 从旧版 400 帧变为 v4 的 800 帧，存在测量相位混淆。 |
| **V2-A3** | $\rho(\text{pre\_fps15}, \text{live\_fps}) = +0.89$ 同义反复与单趟重复计数 | REFUTED（推翻 §544 机制证据） | **CONFIRMED（确认推翻）** | `qc151_trip.harness8_v4.py:5184-5191` 与 `:4767-4770` 均取同一 CurrentFrame 与 perf_counter 差分，系同一物理量在相邻时段的两次测量（自相关）。代码行 5324 表明单趟 settle 仅测算一次 pre_fps15 并直接复制给全趟 3 窗；全库 16 个多窗推进趟 100% 存在重复赋值。units0>0 的 60 窗精确复现 Pearson r=+0.892512；全库 63 窗 r=+0.871733；消除重复计数的 34 趟均值样本降至 r=+0.813921。固定 v4 内 r(units0, live_fps)=-0.3705, Spearman rho=-0.8433。 |
| **V2-A4** | 趟内 vs 趟间方差锁定与跨窗跃迁反例 | CONFIRMED（整趟锁定显著但存在跃迁反例） | **CONFIRMED（复核确认）** | 16 个多窗趟内极差中位数 0.569669 fps (0.57 fps)；34 个独立趟均值共 561 对绝对差中位数 5.436805 fps (5.44 fps)，全库总极差 31.942314 fps，趟间差达趟内差的 9.5438 倍（9.54 倍）。同版同图反例属实：`l3_1101v4c` 三窗 live_fps 分别为 18.5396, 28.4161, 30.7053，趟内极差达 12.165676 fps (12.17 fps)。核心对照慢窗推进时长均在 24.79s–24.99s（占窗长 >99%），$|\text{live\_fps} - \text{fps\_avg}| \le 0.0610\text{ fps}$，排除尾段停摆假慢窗。 |

---

## 一、四大防陷阱专项审查（第一道核验员履职审查）

复核员根据审计规范，对第一道报告 `V2/REPORT.md` 进行反缺陷交叉审查：

1. **是否把「像素判据」当「OCR」**：
   - **审查结论：否，未发生任何 OCR 混淆。**
   - **依据**：第一道报告在提取 `units0` 时直接读取 `measure_w*.json` 中的 `gate.units0` 与 `counters`（来自 harness 内存直读结构体），在判定帧率推进时严格采用 `frame_edges` 的二元组 `[f, t]`，地图比对采用 SHA-256 哈希值（`f3bb0a4e...` 与 `0add791d...`），未将任何图像像素判据误述为 OCR 识别。
2. **是否把「样本」当「总体」**：
   - **审查结论：否，严格厘清了全量母本、推进活窗与特定负载子集。**
   - **依据**：第一道报告在第 0 节完整普查了全量 103 份 JSON（43 个趟来源，子目录 100 份 + 根目录 3 份），清晰区分出 `len(edges) >= 2` 的 64 窗、回绕 1 窗、正向推进活窗 63 窗、无推进 40 窗；在相关性计算中明确标定全量活窗 N=63、排除 0 单位 N=60 以及对标高负载带 N=22，未以偏概全。
3. **是否把「同一张图重复计数」当多个样本**：
   - **审查结论：否，报告不仅未犯此错，反而深度揭露了 §544 的伪重复（Pseudoreplication）。**
   - **依据**：报告在第 5.2 节穿透源码 `qc151_trip.harness8_v4.py:5324`，指出 harness 每一趟只在 settle 末测一次 `pre_fps15`，随后将其原样复制进全部 3 个测窗，导致 63 窗仅有 34 个独立样本。报告主动进行了按趟取均值的降维去重复算（N=34，r=+0.8139），彻底排除了重复计数干扰。
4. **是否把「相关」当「因果」**：
   - **审查结论：否，报告正是破除「伪相关」、还原「共线混淆」的严谨范式。**
   - **依据**：针对 §544 宣称的 $\rho=+0.89$ 及“时代效应”，报告从两个维度证伪了因果推断：
     - 构建 2×2 列联表，证明在 `[1180, 1360]` 负载带内快慢与 harness 版本存在 $\phi = +1.0$ 的完全共线；
     - 固定 harness 版本后，$\rho(\text{units0}, \text{live\_fps})$ 在不同版本间符号剧烈摆动（$-0.84$ 至 $+0.95$），指明总体负相关为分层版本与地图导致的辛普森悖论（Simpson's paradox）。

---

## 二、关键主张逐条独立复算过程与依据

复核员在隔离写域中编写并执行了独立验证脚本，以下为各主张的数据对账：

### 2.1 主张 V2-A1 独立复算：时段帧率与负载差异

- **复算脚本**：`python -I -X utf8 D:/Project/ra2-campaign-forge/lead/goal3t_nightwatch_20261102/swarm_20261104/XVERIFY_S544_ae38d56c/V2/recheck_v2_a1.py`
- **读取数据源**：
  - `.../qc161_u0400_trip/l3_1101v4d/measure_w{0,1,2}.json`
  - `.../qc161_u0400_trip/l3_1101v4e/measure_w{0,1,2}.json`
  - `.../qc161_u0400_trip/l1c_20261021/measure_w{0,1,2}.json`
  - `.../qc161_u0400_trip/l3_20261031hb/measure_w{0,1,2}.json`
- **重算结果对账表**：
  - `l3_1101v4d/w0`: $f_0=920, f_1=1699, \Delta f=779, \Delta t=24.9834\text{s} \implies \text{live\_fps} = 31.180659$ (`fps_avg` = 31.161901, `units0` = 1225)
  - `l3_1101v4d/w1`: $f_0=1700, f_1=2481, \Delta f=781, \Delta t=24.9774\text{s} \implies \text{live\_fps} = 31.268243$ (`fps_avg` = 31.242758, `units0` = 1225)
  - `l3_1101v4d/w2`: $f_0=2482, f_1=3263, \Delta f=781, \Delta t=24.9782\text{s} \implies \text{live\_fps} = 31.267323$ (`fps_avg` = 31.242973, `units0` = 1225)
  - `l3_1101v4e/w0`: $f_0=925, f_1=1707, \Delta f=782, \Delta t=24.9949\text{s} \implies \text{live\_fps} = 31.286406$ (`fps_avg` = 31.280130, `units0` = 1189)
  - `l3_1101v4e/w1`: $f_0=1707, f_1=2487, \Delta f=780, \Delta t=24.9696\text{s} \implies \text{live\_fps} = 31.238013$ (`fps_avg` = 31.202094, `units0` = 1189)
  - `l3_1101v4e/w2`: $f_0=2488, f_1=3269, \Delta f=781, \Delta t=24.9733\text{s} \implies \text{live\_fps} = 31.273346$ (`fps_avg` = 31.241971, `units0` = 1189)
  - `l1c_20261021/w0`: $f_0=957, f_1=1186, \Delta f=229, \Delta t=24.8337\text{s} \implies \text{live\_fps} = 9.221340$ (`fps_avg` = 9.160346, `units0` = 881)
  - `l1c_20261021/w1`: $f_0=1187, f_1=1415, \Delta f=228, \Delta t=24.9664\text{s} \implies \text{live\_fps} = 9.132282$ (`fps_avg` = 9.120621, `units0` = 881)
  - `l1c_20261021/w2`: $f_0=1415, f_1=1665, \Delta f=250, \Delta t=24.9125\text{s} \implies \text{live\_fps} = 10.035138$ (`fps_avg` = 10.000941, `units0` = 881)
  - `l3_20261031hb/w0`: $f_0=437, f_1=606, \Delta f=169, \Delta t=24.8856\text{s} \implies \text{live\_fps} = 6.791083$ (`fps_avg` = 6.787164, `units0` = 1347)
  - `l3_20261031hb/w1`: $f_0=607, f_1=725, \Delta f=118, \Delta t=24.7983\text{s} \implies \text{live\_fps} = 4.758393$ (`fps_avg` = 4.731722, `units0` = 1347)
  - `l3_20261031hb/w2`: $f_0=726, f_1=991, \Delta f=265, \Delta t=24.9828\text{s} \implies \text{live\_fps} = 10.607305$ (`fps_avg` = 10.600849, `units0` = 1347)
- **负载对标审查**：快组两趟 `units0` 均值为 $(1225 + 1189) / 2 = 1207.0$；慢组两趟 `units0` 均值为 $(881 + 1347) / 2 = 1114.0$。差异比率 $(1207 - 1114) / 1207 = 7.7\%$，而两极极差 $(1189 - 881) / 881 = 34.96\% \approx 35.0\%$。其中 `l1c` 的 881 远在所谓高负载带 `[1180, 1360]` 之外，两组绝非同负载。
- **复核裁决**：**CONFIRMED**。数值完全精确吻合，定性立论无懈可击。

---

### 2.2 主张 V2-A2 独立复算：工具链共线性与采样相位

- **复算脚本**：`python -I -X utf8 D:/Project/ra2-campaign-forge/lead/goal3t_nightwatch_20261102/swarm_20261104/XVERIFY_S544_ae38d56c/V2/recheck_v2_a2.py`
- **读取数据源**：
  - 43 个趟目录的 `_launch_result.json`、`qc151_fields.json` 及全量 `measure_w*.json`
- **复算事实**：
  1. 在高负载带 `units0 ∈ [1180, 1360]` 内，筛选出有效推进窗恰好 **22 个**；
  2. 快窗（$\text{live\_fps} \ge 28$）共 **8 窗**（`v4c/w1`, `v4c/w2`, `v4d/w0..w2`, `v4e/w0..w2`），**100% 采用 `harness8_v4.py`**（`sha16: 38244d2907e7f7fa`）；
  3. 慢窗（$\text{live\_fps} < 15$）共 **12 窗**（`v3a/w0..w2`, `v3b/w1..w2`, `l3_20261021/w0..w2`, `ha/w0`, `hb/w0..w2`），**100% 采用旧版工具链**（5 窗 `harness8_v3.py: 37a7c9cdf2ca97e3`，4 窗 `harness8.py: dd5459fe0cf3461c`，3 窗 `harness3.py`）；
  4. 过渡窗（$15 \le \text{fps} < 28$）共 2 窗（`v3b/w0` 为 16.74，`v4c/w0` 为 18.54）。
  5. **2×2 列联表与 $\phi$ 相关系数**：
     $$\begin{pmatrix} 8 & 0 \\ 0 & 12 \end{pmatrix} \implies \phi = \frac{8 \times 12 - 0 \times 0}{\sqrt{8 \times 12 \times 8 \times 12}} = \mathbf{+1.000000}$$
  6. **地图与起始相位混淆验证**：
     - `l1c_20261021` 载体地图哈希为 `0add791d11aea84d7876aa3f908165259ec77f681ee721f83fd9966facdf60bc`，而 `v4d/v4e` 为 `f3bb0a4efdedd067f5348d3acf01d294c602d3481203cf718809f7ec597b9a36`，地图完全不同；
     - 检查 `qc151_fields.json`，`v3a/v3b/ha/hb` 的 `h7_measure_start_frame` 恒为 `400`（实采首帧在 $f \approx 387 \sim 454$），而 `v4c/v4d/v4e` 的 `h7_measure_start_frame` 恒为 `800`（实采首帧在 $f \approx 869 \sim 925$）。
- **复核裁决**：**CONFIRMED**。版本与表现呈数学绝对共线，且测量逻辑相位被严重置换。推翻时代效应当之无愧。

---

### 2.3 主张 V2-A3 独立复算：同义反复与自相关

- **复算脚本**：`python -I -X utf8 D:/Project/ra2-campaign-forge/lead/goal3t_nightwatch_20261102/swarm_20261104/XVERIFY_S544_ae38d56c/V2/recheck_v2_a3.py`
- **源码逐行查证**：
  - 查阅 `qc151_trip.harness8_v4.py:5184-5191`：
    ```python
    t_cut = t0s + MEASURE_SETTLE_S - MEASURE_GATE_SPAN_S
    gate_pts = [(t, f) for t, f in s_samples if t >= t_cut]
    if len(gate_pts) >= 2:
        _gspan = gate_pts[-1][0] - gate_pts[0][0]
        if _gspan > 0:
            pre_fps15 = (gate_pts[-1][1] - gate_pts[0][1]) / _gspan
    ```
    `pre_fps15` 是 settle 期末尾 1.5 秒的帧差分速率。
  - 行 5324：在 3 窗采样循环 `for k in range(MEASURE_WINDOWS):` 中，落盘 JSON 的 `gate` 键被统一赋值为窗前一次性生成的 `gate_block`。
  - 实测遍历：全库 16 个有效多窗趟中，全部 16 趟（100%）在 w0、w1、w2 记录完全相同的 `pre_fps15` 浮点值；全量 30 个多窗趟中 29 趟严格一致（仅根目录趟因 w0=0 略异）。
- **相关系数纯公式重算**：
  1. **units0 > 0 正向推进活窗（N = 60）**：
     - $\text{Pearson } r(\text{pre\_fps15}, \text{live\_fps}) = \mathbf{+0.892512}$（精确复现 §544 声称的 $+0.8925$！）
     - $\text{Spearman } \rho = +0.744776$
     - $\text{Pearson } r(\text{units0}, \text{live\_fps}) = -0.585139$
  2. **全量正向推进活窗（含 units0=0，N = 63）**：
     - $\text{Pearson } r(\text{pre\_fps15}, \text{live\_fps}) = \mathbf{+0.871733}$
     - $\text{Spearman } \rho = +0.753426$
  3. **按趟均值消除重复计数后（N = 34 独立趟）**：
     - $\text{Pearson } r(\text{pre\_fps15}, \text{live\_fps}) = \mathbf{+0.813921}$
     - $\text{Spearman } \rho = +0.650928$
  4. **固定 `harness8_v4` 内部（N = 9 窗）**：
     - $\text{Pearson } r(\text{units0}, \text{live\_fps}) = \mathbf{-0.370478}$
     - $\text{Spearman } \rho = \mathbf{-0.843274}$
- **机制判定**：`pre_fps15` 与 `live_fps` 本质是相邻时间片段内读取同一进程时钟与帧计数器的自相关，且直接用包含复制样本的 60 窗去算相关系数人为虚增了自由度。消除重复后相关性明显回落；在固定 v4 版本内，高单位数反对应低帧率（$\rho=-0.8433$），彻底否定了正向负载机制假说。
- **复核裁决**：**CONFIRMED**。第一道核验员批判透彻，复算数字高度一致。

---

### 2.4 主张 V2-A4 独立复算：整趟锁定与同版跃迁反例

- **复算脚本**：`python -I -X utf8 D:/Project/ra2-campaign-forge/lead/goal3t_nightwatch_20261102/swarm_20261104/XVERIFY_S544_ae38d56c/V2/recheck_v2_a4.py`
- **复算事实**：
  1. **趟内极差（Intra-trip range）**：
     - 16 个包含 $\ge 2$ 活窗的趟，其内部窗间极差分布如下：
       `archive_T38`: 0.2365, `archive_T39`: 0.1817, `l1a_20261020`: 0.0441, `l1c_20261021`: 0.9029, `l1d_20261021`: 3.4354, `l1e_20261021`: 2.9864, `l3_1101v3a`: 8.1798, `l3_1101v3b`: 5.5266, `l3_1101v4c`: 12.1657, `l3_1101v4d`: 0.0876, `l3_1101v4e`: 0.0484, `l3_20261021`: 3.1970, `l3_20261023q`: 0.1642, `l3_20261023r`: 0.2214, `l3_20261031hb`: 5.8489, `t55k_20261020`: 0.0100。
     - **全量趟内极差中位数**：$(0.236482 + 0.902856) / 2 = \mathbf{0.569669\text{ fps}}$（即报告所述 **0.5697 fps**）；
     - 快趟组极差中位数为 $0.1259\sim 0.1642\text{ fps}$，慢趟组极差中位数为 $3.4354\sim 4.4810\text{ fps}$。
  2. **趟间差异（Inter-trip difference）**：
     - 34 个独立趟均值产生 $\binom{34}{2} = 561$ 个两两差值对；
     - **趟间两两绝对差中位数**：$\mathbf{5.436805\text{ fps}}$（即报告所述 **5.4368 fps**）；
     - 全库独立趟均值最低 2.0097 fps（`l1_20261023e1`），最高 33.9520 fps（`archive_T34`），总极差 $\mathbf{31.942314\text{ fps}}$；
     - **趟间差与趟内差比值**：$5.436805 / 0.569669 = \mathbf{9.543793\text{ 倍}}$（即 **9.54 倍**）。
  3. **同版跃迁反例**：
     - `l3_1101v4c`（`harness8_v4`, 地图 `f3bb0a4e`）：
       - `measure_w0.json`: live_fps = 18.5396, fps_avg = 18.5209
       - `measure_w1.json`: live_fps = 28.4161, fps_avg = 28.4018
       - `measure_w2.json`: live_fps = 30.7053, fps_avg = 30.6816
       - 趟内跨窗极差高达 $\mathbf{12.165676\text{ fps}}$，铁证同一版本同图同初始负载下，系统仍发生窗间动态跃迁。
  4. **尾段停摆假设排查**：
     - 对标慢窗 `l1c/w0` 有效跨度 $\Delta t = 24.8337\text{s}$（占窗长 99.3%），$|\text{live\_fps} - \text{fps\_avg}| = 0.0610\text{ fps}$；
     - `l3_20261031hb/w0` $\Delta t = 24.8856\text{s}$（占窗长 99.5%），差值 0.0039 fps；
     - `l3_20261031hb/w1` $\Delta t = 24.7983\text{s}$（占窗长 99.2%），差值 0.0267 fps；
     - 事实确凿：核心慢窗全窗 25 秒稳定低速爬行，绝非停摆稀释导致的伪慢窗。
- **复核裁决**：**CONFIRMED**。所有极差、中位数、反例数值与时长统计均 100% 独立复算闭环。

---

## 三、最终复核裁决结论

复核员-V2 对初核员-V2 提交的报告 `V2/REPORT.md` 进行独立全量代码重算与数据交叉复核，裁决如下：

1. 初核员所呈之 **四大核心主张（V2-A1、V2-A2、V2-A3、V2-A4）全部立论严密、证据链完备、数值计算精准无误**；
2. 四大防陷阱检查全绿：无图像 OCR 假判、无样本总体混淆、精准识别并剔除伪重复、彻底粉碎伪因果与共线混淆；
3. **§544 宣称的「同负载跨时段差 3 倍」时代效应被确凿证伪**。其核心快慢分界完全是由测试工具链从旧版（v3/h8/h3）切换至 `harness8_v4`，以及起始采样相位由 400 帧改至 800 帧造成的测量/运行混淆；
4. 第二道独立复核全面确认第一道报告结论，复核予以 **CONFIRMED 全量通过**。
