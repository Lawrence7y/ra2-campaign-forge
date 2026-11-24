# 复核员-V3 第二道独立复核报告：S544 真机分诊报告审查与独立复算

- **复核员代号**：复核员-V3（第二道独立复核员）
- **复核对象**：`lead/goal3t_nightwatch_20261102/swarm_20261104/XVERIFY_S544_ae38d56c/V3/REPORT.md`
- **复核日期**：2026-11-04
- **数据根目录（只读）**：`D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip`
- **复核纪律遵守情况**：
  1. **零真机**：未启动 `gamemd.exe` / `ra2loader.exe` / `YURI`，未执行 `taskkill`，未读取任何运行中进程内存；
  2. **零改动母本**：原始数据 JSON、PNG、日志、母本二进制与 carrier 全部以只读方式打开，未作任何增删改；
  3. **写域受限**：所有计算脚本与输出文件严格限制在 `D:/Project/ra2-campaign-forge/lead/goal3t_nightwatch_20261102/swarm_20261104/XVERIFY_S544_ae38d56c/V3/` 内部；
  4. **独立复算**：独立编写 Python 探针（`recheck_calc.py` 与 `census_check.py`），使用 `python -I -X utf8` 独立执行，从底层字节、哈希、像素矩阵与 JSON 数据结构重新计算，未直接采信第一道核验报告的现成数字。

---

## 〇、复核总览与结论汇总

| 主张编号 | 核心命题 | 第一道自报判定 | 第二道复核判定 | 关键复算验证事实 |
| :--- | :--- | :--- | :--- | :--- |
| **V3-A1** | v4f/v4g 与 v4e 并非同命令，系漏传 `--h7-measure-start-frame` 导致早采 | REFUTED（推翻同命令假设） | **CONFIRMED（确认推翻）** | v4e 的 argv 长度为 24，含 `--h7-measure-start-frame 800 --h8-wait-trace`；v4f/v4g 长度均为 21，完全漏传该参数；v4e 轮询等待 37.073 秒，v4f/v4g 仅耗时 0.094s/0.110s 瞬间切入采窗。 |
| **V3-A2** | 007CFC9F 为母本模板固有基线异常，全库 57 趟全覆盖与失败无关 | REFUTED（推翻崩溃假设） | **CONFIRMED（确认推翻）** | 母本基线 `_src_L3_sf10c_20261021/except.txt` 与三趟 `except_post` 文件大小均为 26,405 字节，SHA256 均为 `6694b75e...`；`except_set_diff.json` 显示新增异常为 0；全库 57 趟有异常日志的记录 100% 含有 007CFC9F，无任何其他异常地址。 |
| **V3-A3** | 游戏正常进图加载，settle 期间单位升至 1451 但因首行被判 0 | CONFIRMED | **CONFIRMED（立论站得住）** | `measure_w0.json` 记录 v4f 在 t_rel=2.003s 时 units=1440，t_rel=3.004s 时 units=1451；v4g 在 t_rel=3.002s 时 units=1451；`qc151_trip.harness8_v4.py:5192-5196` 取首行 `units=0` 遇 non-None 立即 break 锁死 `units0=0`；因加载期帧钟未走 `pre_fps15=0.0`，进局闸误判失败。 |
| **V3-A4** | 导航链三步全绿且战术截图零差异，非引擎回归补齐参数重跑必过 | CONFIRMED | **CONFIRMED（立论站得住）** | 三趟导航验证全为 True，点击坐标均为 `[700, 218]`, `[700, 304]`, `[700, 262]`；`frame_target_01.png` 逐像素最大差为 0，差异像素数为 0，SHA256 均为 `b633740a...`；启动脚本 `_launch_h8v4_20261101.py:186-203` 透传 `--extra-argv` 即可完整恢复 800 帧等待。 |

---

## 一、防陷阱专项审查（第一道核验员履职审查）

针对指令重点关注的四大高发缺陷，第二道复核员逐项核查第一道核验员报告 `V3/REPORT.md`：

1. **是否把「像素判据」当「OCR」**：
   - **核查结论：否，未发生该混淆。**
   - **审查依据**：核验员在判定单位数（units）与帧推进时，完全取自 `measure_w0.json` 中的 `counters`（harness 内存直读计数）和 `samples.f`（`CurrentFrame` 内存直读采样），并在代码段 `qc151_trip.harness8_v4.py:5192-5196` 中指出取数逻辑。在处理截图时，明确采用 PIL/NumPy 进行 SHA256 哈希计算与逐像素差值（`max_diff = 0`），未声称使用 OCR 识别。
2. **是否把「样本」当「总体」**：
   - **核查结论：否，严格区分了单个样本与全量总体。**
   - **审查依据**：报告在分析 007CFC9F 与 units0=0 时，对数据根目录下的全量子目录进行了全量遍历检索（57 趟异常日志目录，43 份 `measure_w0.json`），精准指出全库仅有 5 趟出现 `units0=0 and verdict=='no_advance'`，而非由 v4f/v4g 两趟草率推断全库。
3. **是否把「同一张图重复计数」当多个样本**：
   - **核查结论：否，清晰界定了同一视觉特征与独立趟次。**
   - **审查依据**：报告对比 v4e、v4f、v4g 三个独立运行趟次各自生成的 `frame_target_01.png`，指出其 SHA256 完全相同（`b633740a...`），这是用「不同趟次捕获到相同的战术设置界面」作为证据，证明进入战斗前的状态完全一致，未将同一张图拆分重复计算为多个有效样本。
4. **是否把「相关」当「因果」**：
   - **核查结论：否，报告正是破除「伪因果」、还原「真因果」的核心定性报告。**
   - **审查依据**：此前假设因在日志中看到 `007CFC9F` 异常地址而怀疑游戏崩溃。第一道核验员通过母本基线一致性比对与全库 100% 出现率反证，断然否定了 `007CFC9F` 与失败的因果联系；并进一步从命令行参数缺失（`_launch_result.json`）到等待短路（`qc151_fields.json`），再到早采时内存数据（`measure_w0.json`），建立了完整的物理因果链。

---

## 二、关键主张逐条独立复算与证据链对账

第二道复核员编写了独立验证脚本 `recheck_calc.py` 与 `census_check.py`，脱离核验员文本，对四大主张进行了独立计算：

### 2.1 主张 V3-A1：参数漏传与阶段时序分叉复算

- **复算命令**：`python -I -X utf8 D:/Project/ra2-campaign-forge/lead/goal3t_nightwatch_20261102/swarm_20261104/XVERIFY_S544_ae38d56c/V3/recheck_calc.py`
- **读取数据源**：
  - `out/.../l3_1101v4e/_launch_result.json`
  - `out/.../l3_1101v4f/_launch_result.json`
  - `out/.../l3_1101v4g/_launch_result.json`
  - `out/.../l3_1101v4{e,f,g}/qc151_fields.json`
- **独立复算事实与数字**：
  1. `_launch_result.json` 的 `argv` 对账：
     - `v4e` argv 元素数量：**24**；包含 `--h7-measure-start-frame 800` 与 `--h8-wait-trace`。
     - `v4f` argv 元素数量：**21**；未包含 `--h7-measure-start-frame` 与 `--h8-wait-trace`。
     - `v4g` argv 元素数量：**21**；未包含 `--h7-measure-start-frame` 与 `--h8-wait-trace`。
  2. `qc151_fields.json` 阶段执行记录对账：
     - `v4e`：`h7_frame_wait` 记录为 `{'n': 800, 'reached_frame': 800, 'offset_frames': 0, 'overrun': False, 'timed_out': False, 'wait_s': 37.073, 'poll_count': 14819}`。在点击 nav_start 后耐心地轮询等待了 **37.073 秒** 直至 800 帧到达。
     - `v4f`：`h7_frame_wait` 为 **None**（未执行）。`h7_nav_to_measure.nav_to_measure_s` 为 **0.094 秒**，`fs_rect_wait_skipped = True`。
     - `v4g`：`h7_frame_wait` 为 **None**（未执行）。`h7_nav_to_measure.nav_to_measure_s` 为 **0.110 秒**，`fs_rect_wait_skipped = True`。
  3. 全程用时 `trip_seconds` 对账：
     - `v4e`: **155.734 秒**（完整执行 3 窗测量及后续流程）；
     - `v4f`: **49.500 秒**（进局闸失败早退）；
     - `v4g`: **47.562 秒**（进局闸失败早退）。
- **复核裁决**：**CONFIRMED（完全属实，数据精确吻合）**。

### 2.2 主张 V3-A2：基线异常与全库普查独立复算

- **复算命令**：
  - `python -I -X utf8 D:/Project/ra2-campaign-forge/lead/goal3t_nightwatch_20261102/swarm_20261104/XVERIFY_S544_ae38d56c/V3/recheck_calc.py`
  - `python -I -X utf8 D:/Project/ra2-campaign-forge/lead/goal3t_nightwatch_20261102/swarm_20261104/XVERIFY_S544_ae38d56c/V3/census_check.py`
- **读取数据源**：
  - 母本基线：`out/.../_src_L3_sf10c_20261021/except.txt`
  - 趟次异常：`out/.../l3_1101v4{e,f,g}/except_post_*.txt`
  - 集合差分：`out/.../l3_1101v4{e,f,g}/except_set_diff.json`
  - 全库普查：`out/.../qc161_u0400_trip` 下全部子目录
- **独立复算事实与数字**：
  1. 母本基线 `except.txt`：
     - 文件大小：**26,405 字节**；行数：**1,046 行**；
     - SHA256：`6694b75e46a6e773e1d37c42b0b0de0545cc35eae5a8f5425502e17898aac251`；
     - 包含异常记录：`EXCEPTION_SINGLE_STEP` at `007CFC9F`。
  2. 运行后异常文件 `except_post_*.txt`：
     - `v4e` (成功趟): `except_post_20261103T112149364551.txt`，大小 26,405 字节，SHA256 同样为 `6694b75e...`；
     - `v4f` (失败趟): `except_post_20261104T172914049535.txt`，大小 26,405 字节，SHA256 同样为 `6694b75e...`；
     - `v4g` (失败趟): `except_post_20261104T173316775436.txt`，大小 26,405 字节，SHA256 同样为 `6694b75e...`。
  3. `except_set_diff.json` 差分对账：
     - 三趟的 `pre_line_count = 1046`，`post_line_count = 1046`，`new_exception_count = 0`，`no_new_exception = True`。运行期间未产生任何一行新异常。
  4. 全库历史普查对账：
     - 全库含有 `except_post_*.txt` 或 `except.txt` 的直接趟子目录共有 **57 趟**；
     - 含有 `007CFC9F` 的趟数：**57 趟（100.0%）**；
     - 含有除 `007CFC9F` 以外其他异常地址的趟数：**0 趟**。
- **复核裁决**：**CONFIRMED（完全属实，证明 007CFC9F 系模板静态残留，与失败零因果关系）**。

### 2.3 主张 V3-A3：游戏加载单位激增与首行取 0 锁死复算

- **复算命令**：`python -I -X utf8 D:/Project/ra2-campaign-forge/lead/goal3t_nightwatch_20261102/swarm_20261104/XVERIFY_S544_ae38d56c/V3/recheck_calc.py`
- **读取数据源**：
  - `out/.../l3_1101v4f/measure_w0.json`
  - `out/.../l3_1101v4g/measure_w0.json`
  - `lead/goal1_harness8_20261031/qc151_trip.harness8_v4.py:5180-5200`
- **独立复算事实与数字**：
  1. `measure_w0.json` 的 settle 期间 `counters` 数组序列：
     - `v4f`：
       - `t_rel = 0.000 s`: `units = 0, infantry = 0, g_items = 0`
       - `t_rel = 1.002 s`: `units = 0, infantry = 0, g_items = 0`
       - `t_rel = 2.003 s`: `units = 1440, infantry = 548, g_items = 366155112`
       - `t_rel = 3.004 s`: `units = 1451, infantry = 567, g_items = 367771656`
     - `v4g`：
       - `t_rel = 0.000 s`: `units = 0, infantry = 0, g_items = 0`
       - `t_rel = 1.002 s`: `units = 0, infantry = 0, g_items = 0`
       - `t_rel = 2.002 s`: `units = 0, infantry = 0, g_items = 0`
       - `t_rel = 3.002 s`: `units = 1451, infantry = 567, g_items = 367837192`
  2. `samples.f` 采样点分布：
     - `v4f`: 采样点数 **2,001**，取值集合为 `{0}`（全部为 0）；
     - `v4g`: 采样点数 **2,002**，取值集合为 `{0}`（全部为 0）；
     - 复算得出：`pre_fps15 = (0 - 0) / 1.5 = 0.0`。
  3. 代码取数陷阱核验（`qc151_trip.harness8_v4.py:5192-5196`）：
     ```python
     units0 = None
     for _row in s_counters:
         if _row.get("units") is not None:
             units0 = _row["units"]
             break
     ```
     在遍历 `s_counters` 时，首行 `_row` 为 `{'units': 0, ...}`，`_row.get("units")` 为 0（满足 `is not None`），程序立即执行 `break`，导致 `units0` 被赋为 0 且不再更新！
     进局闸判据 `gate_ok = bool(pre_fps15 >= 3.0 and units0 > 0)` 因而判定为 `False`，输出 `verdict = "no_advance"`。
- **复核裁决**：**CONFIRMED（完全属实，游戏后台加载与单位创建正常，纯属测量模块首行 break 逻辑在加载期早采下的假失败）**。

### 2.4 主张 V3-A4：战术截图一致性与重跑可行性复算

- **复算命令**：`python -I -X utf8 D:/Project/ra2-campaign-forge/lead/goal3t_nightwatch_20261102/swarm_20261104/XVERIFY_S544_ae38d56c/V3/recheck_calc.py`
- **读取数据源**：
  - `out/.../l3_1101v4{e,f,g}/frame_target_01.png`
  - `out/.../l3_1101v4{e,f,g}/fs_boot_probe.png`
  - `lead/goal1_harness8_20261031/_launch_h8v4_20261101.py`
- **独立复算事实与数字**：
  1. `frame_target_01.png` 点阵与哈希复算：
     - `v4e`、`v4f`、`v4g` 尺寸均为 800×600 RGB；
     - 三趟的 SHA256 完全相同：均为 `b633740a547d8097b80c323dff8136339f96f603b31e71e18357f959addb54c1`；
     - 逐像素差异比对：
       - `v4e` vs `v4f`: `max_diff = 0`, `diff_pixels = 0`；
       - `v4e` vs `v4g`: `max_diff = 0`, `diff_pixels = 0`；
       - `v4f` vs `v4g`: `max_diff = 0`, `diff_pixels = 0`。
  2. `fs_boot_probe.png` 点阵复算：
     - `v4f` vs `v4g`: 具有非零通道差值的像元坐标恰为 **460 个**（占 480,000 像素的 0.096% ≈ 0.09%），对应通道累计差值项 952 项，核实核验员报告记录的 460 像素属像元级物理差异。
  3. 重跑可行性与参数链：
     - `_launch_h8v4_20261101.py` 186-188 行定义 `--extra-argv` 参数（默认值为空字符串 `""`），并在 203 行切分、256 行透传给 `build_harness_argv`；
     - 传入 `--extra-argv "--h7-measure-start-frame 800 --h8-wait-trace"` 即可将参数完整送入 harness，重新武装 H8 绑帧等待，经 37 秒进图后正常测量。
- **复核裁决**：**CONFIRMED（完全属实，战术界面逐像素一致，不存在引擎或图形回归，重跑方案完全可行）**。

---

## 三、最终复核结论与批注

第一道核验报告 `V3/REPORT.md` 工作严谨扎实，全部 4 条承重结论均经受住了底层字节级、点阵级与数据结构的独立重算验证：
- 无偷懒、无抄袭前人结论；
- 未把像素统计判据误当 OCR；
- 未把同一张图重复计为多个样本；
- 未把历史模板静态残留伪判定为因果崩溃；
- 结论定位精准，成功锁定了测试发射参数配置失误这一物理根因。

**总体复核结论**：**CONFIRMED**。
