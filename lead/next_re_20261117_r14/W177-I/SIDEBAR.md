# W177-I · SIDEBAR（T1 程序化像素定位侧栏 NAPOWR 图标）

> 目标只读；全部坐标由像素分析推导，无目测、无硬编码。抓图先自检非黑占比
> （`t1_fresh.png` nonblack=0.4908，非黑，抓图可靠）。脚本 `work/sidebar_locate.py`，
> 原始剖面 `EVIDENCE/sidebar_profiles.json`、逐槽数据 `EVIDENCE/sidebar_grid.json`、
> 标注图 `EVIDENCE/t1_detected_annotated.png`。

## 1. 结论（核心数字）

| 项 | 值 |
|---|---|
| NAPOWR tile bbox（物理 px） | **x 2272..2400, y 426..518** |
| 中心（物理 px） | **(2336, 472)** |
| 离四边最小余量 | **46 px**（安全，非边界） |
| 判据 | 彩色度最大槽（colorfulness=26.28 vs 空槽≈暗灰），且位于 row0/col0 |
| 图标确认 | 裁图 OCR 形：磁能反應爐（Tesla Reactor=NAPOWR），建筑页首槽 |
| 与审计参考 (2346,475) | 中心相差 (10,3) px，均在 tile 内部；本卡用自己复测值 (2336,472) |

## 2. 方法（可复算）

1. 全屏 2560×1440 抓图；非黑占比自检 ≥0.49。
2. 侧栏搜索带 x∈[2246,2560]（任务给定物理范围）、全高。
3. **列结构**：在"空槽行带" y∈[560,1330] 取 1px 列亮度剖面 → 近黑间隙 (lum<8, 连续≥3px)
   在 x≈2397..2403 找到列间隔 → 两列 span [2272,2400]、[2400,2530]（凸缘高光峰 x≈2277/2394/2514）。
4. **行结构**：在左列 interior 取 1px 行亮度剖面 → 近黑间隙给出行分隔 y≈518,612,706,800,893…;
   用中位周期 94px 外推首槽顶 y=426（首槽图标干扰使顶部 1px 暗谷未被 minrun=3 捕获）。
   行 span: [426,518],[518,612],…, 周期≈94px。
5. **图标槽判定**：逐槽 interior 算彩色度 mean(max−min of RGB)。含图标槽=26.28，空槽≈个位数；
   取彩色度最大者 → row0/col0 = NAPOWR。中心=槽 bbox 中心=(2336,472)。
6. 稳定性：两张不同帧抓图（frame 1827 / 8721）locate 结果逐字段全等。
7. 标注图证明十字落在图标中心、离边 46px，绝非上轮的"点左边界余量 0–3px"。

## 3. 换页/换建筑后 tile 位置是否变

- **网格几何不变（已证）**：切到防御页再切回，`col_spans`/`row_sep` 逐项相同（行 sep ±1px），
  中心仍 (2336,472)。证据 `sidebar_grid_t1_tab_buildings/defense/back.json`。
- **槽位内容会变（结构性事实）**：row0/col0 放的是"当前页建造列表的第 1 项"。
  本卡当前在建筑页、已部署建造场且未建前置 ⇒ 第 1 项=磁能反应炉(NAPOWR)。
  若切到防御页，row0/col0 变成防御建筑（彩色度同样高，检测器仍会选它——
  故 NAPOWR 身份只能靠"当前在建筑页+标签形"确认，不能只靠彩色度）。
  若先建了其它建筑或页数变化，首槽图标会变。
- **实操纪律**：下单前必须停在建筑页并二次确认标签为磁能反应炉，再点 (2336,472)。

## 4. 点击前台校验

点击统一走 `w177_click.click_client`（`GetForegroundWindow()==hwnd` + `WindowFromPoint`
root owner==pid，不过则 force_foreground 重试）。本卡所有点击前均执行并打印
`foreground_ready`；实测 True、WFP->root owner=3928。节奏 SetCursorPos→0.15s→down→0.09s→up。
