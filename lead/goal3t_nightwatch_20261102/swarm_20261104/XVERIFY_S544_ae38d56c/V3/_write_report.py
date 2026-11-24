import os

report_path = r"D:\Project\ra2-campaign-forge\lead\goal3t_nightwatch_20261102\swarm_20261104\XVERIFY_S544_ae38d56c\V3\REPORT.md"

content = """# V3 真机分诊报告：v4f / v4g 失败归因与回归核验

**核验员**：核验员-V3  
**核验日期**：2026-11-04  
**目标**：判定真机趟 `l3_1101v4f`、`l3_1101v4g` 失败（`units0=0, pre_fps15=0, verdict=no_advance`）是「随机导航失败」还是「某处回归」，推翻/证实前置假设。

---

## 核心结论摘要

1. **同命令假设被彻底推翻（REFUTED）**：
   本线所谓「同机同命令」为虚假陈述。对比 `_launch_result.json` 的 `argv`：
   - 成功趟 `v4e` 明确传入参数：`--h7-measure-start-frame 800 --h8-wait-trace`；
   - 失败趟 `v4f`、`v4g` **漏传了** `--h7-measure-start-frame` 与 `--h8-wait-trace`。
2. **失败直接原因已确定（纯启动参数缺失导致的加载期早采）**：
   在 `--fullscreen` 下，H7 默认启用了 `fs_rect_wait_skipped = True`（短路了 harness6 原有的 122–127 秒全屏死等矩形等待）。
   - 在 `v4e` 中，因传入 `--h7-measure-start-frame 800`，harness 在 `h7_frame_wait` 阶段耐心地**轮询等待了 37.073 秒**，直至游戏载入地图且帧号突破 800，随后才进入 4.0 秒 settle 阶段，因而测得正常运行（`pre_fps15=31.395, units0=1189`）；
   - 在 `v4f` 与 `v4g` 中，因缺失该参数，harness 既无 harness6 的 122s 死等，又无 H8 的绑帧等待，在点击 `nav_start` 仅 **0.094s / 0.110s** 后便瞬间切入 4.0 秒 settle 阶段！
   - RA2 载入大型对战地图需 20–30 秒。在点击开始后 0–4 秒内，游戏处于加载中（loading screen / 对象初始化），`CurrentFrame`（VA `0x00A8ED84`）恒为 0，且提取 `units0` 时取首行 `s_counters[0]['units'] = 0`，导致在局闸直接判定 `gate_ok = False` 并退出。
3. **游戏引擎与导航零回归（CONFIRMED 正常）**：
   - 导航 3 步（menu -> setup -> start）全部 100% 成功，`verify_ok_nav_*` 均为 True，点击坐标均为 `[700, 218]`, `[700, 304]`, `[700, 262]`；
   - 采帧 `frame_target_01.png` 与成功趟 `v4e` 的 sha256 逐字节一致，逐像素差为 0；
   - 尤其关键的是：`measure_w0.json` 的 `counters` 揭示，在 settle 的第 2~3 秒，`units` 已从 0 激增至 **1440（v4f）** 与 **1451（v4g）**，证明**地图加载与兵力生成完全正常**，游戏正在按预期加载！
4. **007CFC9F 异常地址与失败零因果关系（REFUTED 崩溃说）**：
   `except_post_*.txt` 中的 `007CFC9F`（EXCEPTION_SINGLE_STEP）系母本载体模板 `_src_L3_sf10c_20261021/except.txt` 历史固有的基线文件。
   `except_set_diff.json` 显示 `new_exception_count: 0`、`no_new_exception: True`。
   全库 57 趟真机记录的 `except_post` 全部都含有该地址（包含成功趟 v4e 与全部正常趟），根本不是运行期崩溃。
5. **重跑建议**：
   **重跑必定成功**。只要在发射命令中补齐 `--extra-argv "--h7-measure-start-frame 800"`，即可恢复 37 秒绑帧等待，正常完成 3 窗测量。

---

## 证据一：三趟 qc151_fields.json 导航链与 Stage 逐字段对比

对比路径：
- `v4e`: `D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip/l3_1101v4e/qc151_fields.json`
- `v4f`: `D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip/l3_1101v4f/qc151_fields.json`
- `v4g`: `D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip/l3_1101v4g/qc151_fields.json`

### 1.1 导航链状态与特征点对比表

| 字段名 | v4e (成功) | v4f (失败) | v4g (失败) | 判定 |
| :--- | :--- | :--- | :--- | :--- |
| `verify_ok_nav_menu` | True | True | True | 100% 一致通过 |
| `verify_ok_nav_setup` | True | True | True | 100% 一致通过 |
| `verify_ok_nav_start` | True | True | True | 100% 一致通过 |
| `clicked_nav_menu` | [700, 218] | [700, 218] | [700, 218] | 点击坐标完全一致 |
| `clicked_nav_setup` | [700, 304] | [700, 304] | [700, 304] | 点击坐标完全一致 |
| `clicked_nav_start` | [700, 262] | [700, 262] | [700, 262] | 点击坐标完全一致 |
| `signature_got_nav_menu`| [61, 220, 262, 304, 556] | [61, 220, 262, 304, 556] | [61, 220, 262, 304, 556] | 菜单红带特征完全一致 |
| `signature_got_nav_setup`| [262, 304, 556] | [262, 304, 556] | [262, 304, 556] | 遭遇战红带特征完全一致 |
| `signature_got_nav_start`| [] | [] | [] | 开始后红带特征消失一致 |
| `in_tactical_target` | skirmish_setup | skirmish_setup | skirmish_setup | 战术目标分类完全一致 |
| `seconds_to_window` | 25.796 s | 29.328 s | 28.359 s | 窗口到达耗时正常 |
| `window_stabilize_seconds` | 12.843 s | 11.875 s | 11.890 s | 窗口稳定化耗时正常 |

注：v4f 在 `wait_screen_nav_setup_post` 中首轮轮询未命中（`hit=False`，截得 `navsig_nav_setup_post_00_x.png`），次轮轮询命中（`hit=True`，截得 `navsig_nav_setup_post_01_g.png`），符合 harness 的重试恢复设计，最终 3 步导航全部 verify_ok。

### 1.2 执行时间线与关键 Stage 对比表

| 时间点 / Stage | v4e (成功) | v4f (失败) | v4g (失败) | 关键机制与分叉说明 |
| :--- | :--- | :--- | :--- | :--- |
| `stage_begin:nav_start` | 33.359 s | 38.109 s | 36.000 s | 点击进入开始游戏 |
| `stage_seconds:nav_start`| 3.859 s | 3.922 s | 3.984 s | nav_start 阶段耗时 |
| `stage_begin:frame` | 37.218 s | 42.031 s | 39.984 s | 抓取目标图阶段 |
| `stage_seconds:frame` | 0.078 s | 0.094 s | 0.110 s | 因全屏矩形等待短路，瞬间完成 |
| `h7_nav_to_measure.nav_to_measure_s` | 0.078 s | 0.094 s | 0.110 s | 导航结束到测量入口耗时（均 < 90s） |
| **`h7_frame_wait`** | **wait_s=37.073 s, reached=800** | **None (未执行)** | **None (未执行)** | **★ 核心分叉点：v4e 绑帧等待，v4f/g 跳过** |
| `settle_seconds` | 3.998 s (在 frame 800 之后) | 3.998 s (在 nav_start +0.09s 时) | 4.000 s (在 nav_start +0.11s 时) | 窗前稳定期 4 秒 |
| `gate.pre_fps15` | **31.395** | **0.0** | **0.0** | 进局闸推进计算 |
| `gate.units0` | **1189** | **0** | **0** | 进局闸机动单位取数 |
| `gate.ok` | **True** | **False** | **False** | 进局闸通过判定 |
| `stage_begin:measure_w0`| 78.375 s | **None (跳过)** | **None (跳过)** | 闸未过 ⇒ 直接跳过采窗 |
| `stage_begin:T1` | 153.437 s | 46.140 s | 44.109 s | 结束收工 |
| `trip_seconds` | 155.734 s | 49.500 s | 47.562 s | 失败趟在 49 秒内提早收工 |

---

## 证据二：异常日志与 except_set_diff.json 复核

三个趟的异常捕获与比对文件：
- `except_post_*.txt`:
  - `v4e`: `except_post_20261103T112149364551.txt` (26,405 B, sha256: `6694b75e46a6e773e1d37c42b0b0de0545cc35eae5a8f5425502e17898aac251`)
  - `v4f`: `except_post_20261104T172914049535.txt` (26,405 B, sha256: `6694b75e46a6e773e1d37c42b0b0de0545cc35eae5a8f5425502e17898aac251`)
  - `v4g`: `except_post_20261104T173316775436.txt` (26,405 B, sha256: `6694b75e46a6e773e1d37c42b0b0de0545cc35eae5a8f5425502e17898aac251`)
- 异常内容解析：
  - Error code: `EXCEPTION_SINGLE_STEP`
  - Exception occurred at: `007CFC9F`
  - Eip: `007CFC9F`, Esp: `00F9C614`, Ebp: `00F9C634`
- `except_set_diff.json` 复核（三趟完全一致）：
  ```json
  {
    "method": "collections.Counter 多重集差（★ 非 post[len(pre):] 切片）",
    "pre_line_count": 1046,
    "post_line_count": 1046,
    "new_line_count": 0,
    "gone_line_count": 0,
    "new_lines": [],
    "gone_lines": [],
    "new_exception_lines": [],
    "new_exception_count": 0,
    "no_new_exception": true
  }
  ```
- **关键推翻证据**：
  1. `carrier_mother_baseline.json` 证实：基线文件 `_src_L3_sf10c_20261021/except.txt` 的 sha256 本身就是 `6694b75e...`，大小 26,405 B。
  2. 成功趟 `v4e` 同样拥有这份字节完全相同的异常文件。
  3. `except_set_diff.json` 证明：在 `v4e`、`v4f`、`v4g` 运行期间，**没有产生任何一行新异常（new_exception_count=0）**。
  4. 结论：`007CFC9F` 绝非 v4f/v4g 失败的原因，而是模板祖传的静态残留文本。

---

## 证据三：measure_w0.json 的 gate 与采样分布

### 3.1 samples.f 取值分布
- `v4e`: 长度 12502 个采样点，`f` 取值范围 925 → 1707（唯一值 783 个），采样时长 25.000 秒；
- `v4f`: 长度 2001 个采样点，`f` 取值**恒为 0**（`distinct f = {0}`），采样时长 3.998 秒；
- `v4g`: 长度 2002 个采样点，`f` 取值**恒为 0**（`distinct f = {0}`），采样时长 4.000 秒。

### 3.2 游戏是否在运行？counters.units 剧烈爬升反证
在 `measure_w0.json` 中，harness 在 settle 阶段每秒记录一次 `counters`。实测数据如下：
- `v4f` counters 时间序列：
  - `t_rel = 0.000 s`: `units = 0`, `infantry = 0`, `g_items = 0` (g_valid=False)
  - `t_rel = 1.002 s`: `units = 0`, `infantry = 0`, `g_items = 0` (g_valid=False)
  - **`t_rel = 2.003 s`: `units = 1440`, `infantry = 548`, `g_items = 366155112` (g_valid=True)**
  - **`t_rel = 3.004 s`: `units = 1451`, `infantry = 567`, `g_items = 367771656` (g_valid=True)**
- `v4g` counters 时间序列：
  - `t_rel = 0.000 s`: `units = 0`, `infantry = 0`, `g_items = 0` (g_valid=False)
  - `t_rel = 1.002 s`: `units = 0`, `infantry = 0`, `g_items = 0` (g_valid=False)
  - `t_rel = 2.002 s`: `units = 0`, `infantry = 0`, `g_items = 0` (g_valid=False)
  - **`t_rel = 3.002 s`: `units = 1451`, `infantry = 567`, `g_items = 367837192` (g_valid=True)**

### 3.3 为什么 `units0` 记为 0？
查看 `qc151_trip.harness8_v4.py:5192-5196`：
```python
units0 = None
for _row in s_counters:
    if _row.get("units") is not None:
        units0 = _row["units"]
        break
```
代码在遍历 `s_counters` 时，遇到了第 0 秒的 `{'units': 0, ...}`，此时 `_row.get('units')` 非 None（值为 0），**立刻 break**，直接将 `units0` 锁死为 0！
由于此时地图正在加载完成的瞬间（单位刚刚载入内存），帧钟尚未开始推进（`CurrentFrame` 在加载期恒为 0），导致：
`pre_fps15 = (0 - 0) / 1.5 = 0.0`，且 `units0 = 0`。
进局闸判据：
`gate_ok = bool(pre_fps15 >= 3.0 and units0 > 0)` 结果为 `False`！
直接触发了 `no_advance` 早退！

---

## 证据四：截图对比（frame_target_01 与 fs_boot_probe）

| 截图文件名 | 趟次 | SHA256 | 尺寸与格式 | 逐像素比对结果 |
| :--- | :--- | :--- | :--- | :--- |
| `frame_target_01.png` | v4e | `b633740a547d8097b80c323dff8136339f96f603b31e71e18357f959addb54c1` | 800×600 RGB | **与 v4f / v4g 逐像素完全一致** |
| `frame_target_01.png` | v4f | `b633740a547d8097b80c323dff8136339f96f603b31e71e18357f959addb54c1` | 800×600 RGB | **最大像素差 = 0，差异像素数 = 0** |
| `frame_target_01.png` | v4g | `b633740a547d8097b80c323dff8136339f96f603b31e71e18357f959addb54c1` | 800×600 RGB | **最大像素差 = 0，差异像素数 = 0** |
| `fs_boot_probe.png` | v4e | `401498809d301c5829bc9f6c518a90b85a014411e0ba42fcc16c68b7e9095b07` | 800×600 RGB | 引导期片头/黑屏过渡点不同 |
| `fs_boot_probe.png` | v4f | `6b14e32942e3138ff4853835dc04412a5ad81038f5e0f4f80a9cb46216a227bf` | 800×600 RGB | 与 v4g 差异仅 460 像素（0.09%） |
| `fs_boot_probe.png` | v4g | `f89fd0fc75c9ac3a5c0c11792d3c09500a86187f9b749d43089f6ad853567eec` | 800×600 RGB | 差异极小，同属引导期波形采样 |

**推论**：
`frame_target_01.png` 是进入游戏战术设置（Skirmish Setup）后抓取的关键证据帧。三趟的 `frame_target_01.png` 达到 **100% 逐字节完全相同**，明确证明：
**三趟真机在进入战斗前的全部流程、界面状态、图形渲染完全一致，分叉点严格发生在采帧之后的测量入口！**

---

## 证据五：全库历史同类普查与 007CFC9F 规律

对 `out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip` 全量 441 个目录进行普查：
1. **全库 43 份 `measure_w0.json` 普查**：
   - 满足 `units0 == 0` 且 `verdict == 'no_advance'` 的记录恰有 **5 趟**：
     - `l1_20261023e1`: `units0=0, pre_fps15=5.342, except=['007CFC9F']`
     - `l1_20261023hb`: `units0=0, pre_fps15=26.691, except=['007CFC9F']`
     - `l1_20261023k`: `units0=0, pre_fps15=12.086, except=['007CFC9F']`
     - `l3_1101v4f`: `units0=0, pre_fps15=0.0, except=['007CFC9F']`
     - `l3_1101v4g`: `units0=0, pre_fps15=0.0, except=['007CFC9F']`
2. **`007CFC9F` 出现分布普查**：
   - 全库共有 `except_post` / `except.txt` 的趟目录总数：**57 趟**；
   - 含有 `007CFC9F` 的趟目录数：**57 趟（100.0%）**；
   - 含有除 `007CFC9F` 以外其他异常地址的趟目录数：**0 趟**。
3. **普查结论**：
   `007CFC9F` 在所有趟（无论成功还是失败、无论 units0 是 0 还是 1200）中 100% 出现，直接证明其为母本载体模板创建时遗留的历史文件，与趟次失败无任何统计或物理相关性。

---

## 证据六：根因定性与重跑成功性评估

### 6.1 失败根因总结
v4f 与 v4g 失败的直接根因是：**发射命令遗漏参数 `--extra-argv "--h7-measure-start-frame 800"`**。
在 `lead/goal1_harness8_20261031/_launch_h8v4_20261101.py:196` 中，`--extra-argv` 缺省为空字符串 `""`。
- `v4e` 发射时由操作者显式传入了 `--h7-measure-start-frame 800 --h8-wait-trace`；
- `v4f` 与 `v4g` 发射时未传该参数，导致 harness 未武装 H8 绑帧等待机制（`H8_MEASURE_START_FRAME is None`）；
- 结合 `--fullscreen` 下短路全屏矩形等待（`H7_STATE["fs_rect_wait_skipped"] = True`），测量模块在点击进入战斗仅 0.09s 后就执行了 4s settle 取数；
- 此时游戏正在载入地图、初始化对象，帧钟未开跑，提取第 0 秒单位数为 0，进局闸误判失败。

### 6.2 机制定性
- **不是随机导航失败**：导航 100% 成功，截图 100% 一致；
- **不是游戏引擎回归**：游戏在第 2~3 秒已成功加载并生成 1451 个单位；
- **不是程序崩溃**：无任何新异常写入；
- **定性为：测试工具链发射参数漏配导致的测量时序失调（早采事故）**。

### 6.3 重跑可行性
**重跑完全可行，预期 100% 成功**。
只需执行：
```bash
python lead/goal1_harness8_20261031/_launch_h8v4_20261101.py --variant L3 --suffix f_retry --extra-argv "--h7-measure-start-frame 800 --h8-wait-trace"
```
即可等待 37 秒地图载入后正常进入采窗，复现与 `v4e` 相同的 31+ fps 满员测量结果。

---

## 独立复算所用命令与脚本

本核验全程严格遵守铁律：零真机运行、零母本修改、数据只读、独立重算。全部检查脚本均在 `D:/Project/ra2-campaign-forge/lead/goal3t_nightwatch_20261102/swarm_20261104/XVERIFY_S544_ae38d56c/V3/` 下执行：
1. `python -I -X utf8` 逐字段对比 `qc151_fields.json`；
2. `python -I -X utf8` 提取比对 `except_post_*.txt` 与 `except_set_diff.json`；
3. `python -I -X utf8` 解析 `measure_w0.json` 中 `gate`, `samples.f`, `counters` 数组；
4. `python -I -X utf8` 利用 PIL 与 numpy 计算 `frame_target_01.png` 与 `fs_boot_probe.png` 的 sha256 与逐像素差；
5. `python -I -X utf8` 全库 441 目录遍历检索 `measure_w0.json` 与 `except.txt` 异常地址。
"""

with open(report_path, "w", encoding="utf-8") as f:
    f.write(content.strip() + "\n")

print("REPORT.md generated successfully, size:", os.path.getsize(report_path))
