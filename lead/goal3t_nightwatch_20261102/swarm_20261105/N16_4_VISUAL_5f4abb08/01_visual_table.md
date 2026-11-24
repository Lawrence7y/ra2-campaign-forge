# N16-4 末截图逐文件目视复核表（2026-11-05）

**目视员声明**：本项目此前多次因「没打开图就用颜色比例推断画面」而出错。本目视员严格遵守纪律，全部 25 张子目录末图及 2 张根目录末图（合计 27 张）**均由本人使用 Read 工具逐张独立打开视觉窗口目视判读**。同字节重复件亦逐张单独打开看，绝未用哈希代替读图，绝未用辅助颜色比例 p 值推断画面语义。凡看不清处如实记「读不清」，绝不猜数字。

---

## 一、25 张子目录末图逐文件目视表（子目录口径，共 25 行）

| 序号 | 实际绝对路径 | 画面类别 | 画面文字元素 | 数值逐格读（摧毁数 / 失败数 / 建造数 / 分数） | 采集声明与落盘对齐（forensics、mtime、窗尾偏移） | 同字节判定（整文件 SHA-256） | 缺项说明 |
|:---:|---|---|---|---|---|---|---|
| 1 | `D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip/archive_T33/measure_w1_end_x.png` | 计分屏 | 右上标题「遭遇战□分」；计分表左上「游戏:1」；右上「时□:00:00:24」；表头「玩家」「摧毁数」「□失数」「建造数」「分数」；行1绿色玩家名「□□」；行2蓝色玩家名「[New Play...]」 | 行1(绿): 0 / 0 / 2 / 0<br>行2(蓝): 0 / 2 / 0 / 0 | forensics声明: ts=11:46:10+08:00, png=measure_w1_end_x.png, capture_ok=True, empty_window=True, focus_ok=True, frame=738。<br>PNG mtime: 11:46:10.694（较声明ts偏+0.6941s）；名义窗尾: 11:46:10.610（mtime偏+0.0841s）。对齐一致。 | 独立 (`fd1378bba8731002...`) | 无 |
| 2 | `D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip/archive_T33/measure_w2_end_x.png` | 主菜单 | RA2 主菜单背景立绘（磁暴步兵、克里姆林宫、闪电、坦克；右侧暗色按钮槽）；右上角 WARNING 仪表内微小文字「WARNING ...」；中央无计分表、无时钟、无玩家名 | 非计分屏，四项数值无 | forensics声明: ts=11:46:35+08:00, png=measure_w2_end_x.png, capture_ok=True, empty_window=True, focus_ok=True, frame=738。<br>PNG mtime: 11:46:35.784（较声明ts偏+0.7840s）；名义窗尾: 11:46:35.694（mtime偏+0.0899s）。对齐一致。 | 与 T42/w1、T42/w2、T45/w2 同字节 (`f61c9808dabd3aef...`) | 无（主菜单立绘无计分格） |
| 3 | `D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip/archive_T34/measure_w1_end_x.png` | 计分屏 | 右上标题「遭遇战□分」；计分表左上「游戏:1」；右上「时□:00:00:10」；表头「玩家」「摧毁数」「□失数」「建造数」「分数」；行1黄色「□□」；行2蓝色「[New Play...]」 | 行1(黄): 0 / 0 / 0 / 0<br>行2(蓝): 0 / 1 / 0 / 0 | forensics声明: ts=12:18:32+08:00, png=measure_w1_end_x.png, capture_ok=True, empty_window=True, focus_ok=True, frame=302。<br>PNG mtime: 12:18:32.184（较声明ts偏+0.1843s）；名义窗尾: 12:18:32.104（mtime偏+0.0793s）。对齐一致。 | 独立 (`f8290e34c4dd8369...`) | 无 |
| 4 | `D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip/archive_T34/measure_w2_end_x.png` | 计分屏 | 右上标题「遭遇战□分」；计分表左上「游戏:1」；右上「时□:00:00:10」；表头「玩家」「摧毁数」「□失数」「建造数」「分数」；行1黄色「□□」；行2蓝色「[New Play...]」 | 行1(黄): 0 / 0 / 0 / 0<br>行2(蓝): 0 / 1 / 0 / 0 | forensics声明: ts=12:18:57+08:00, png=measure_w2_end_x.png, capture_ok=True, empty_window=True, focus_ok=True, frame=302。<br>PNG mtime: 12:18:57.266（较声明ts偏+0.2660s）；名义窗尾: 12:18:57.184（mtime偏+0.0817s）。对齐一致。 | 独立 (`83b6798eca78a8df...`) | 无 |
| 5 | `D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip/archive_T36/measure_w1_end_x.png` | 计分屏 | 右上标题「遭遇战□分」；计分表左上「游戏:1」；右上「时□:00:00:10」；表头「玩家」「摧毁数」「□失数」「建造数」「分数」；行1绿色「□□」；行2蓝色「[New Play...]」 | 行1(绿): 0 / 0 / 0 / 0<br>行2(蓝): 0 / 1 / 0 / 0 | forensics声明: ts=12:53:27+08:00, png=measure_w1_end_x.png, capture_ok=True, empty_window=True, focus_ok=True, frame=310。<br>PNG mtime: 12:53:27.657（较声明ts偏+0.6574s）；名义窗尾: 12:53:27.580（mtime偏+0.0768s）。对齐一致。 | 与 T38/w1 同字节 (`c1c1dbbd0881e694...`) | 无 |
| 6 | `D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip/archive_T36/measure_w2_end_x.png` | 计分屏 | 右上标题「遭遇战□分」；计分表左上「游戏:1」；右上「时□:00:00:10」；表头「玩家」「摧毁数」「□失数」「建造数」「分数」；行1绿色「□□」；行2蓝色「[New Play...]」 | 行1(绿): 0 / 0 / 0 / 0<br>行2(蓝): 0 / 1 / 0 / 0 | forensics声明: ts=12:53:52+08:00, png=measure_w2_end_x.png, capture_ok=True, empty_window=True, focus_ok=True, frame=310。<br>PNG mtime: 12:53:52.752（较声明ts偏+0.7524s）；名义窗尾: 12:53:52.657（mtime偏+0.0945s）。对齐一致。 | 独立 (`c76dab3075695834...`) | 无 |
| 7 | `D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip/archive_T38/measure_w1_end_x.png` | 计分屏（磁盘残留件） | 右上标题「遭遇战□分」；计分表左上「游戏:1」；右上「时□:00:00:10」；表头「玩家」「摧毁数」「□失数」「建造数」「分数」；行1绿色「□□」；行2蓝色「[New Play...]」 | 行1(绿): 0 / 0 / 0 / 0<br>行2(蓝): 0 / 1 / 0 / 0 | 严重不一致！本趟 qc151_fields.json 声明 forensics_png=None, capture_ok=None, empty_window=False, focus_ok=False, frame=940（根本未声明截图落盘）。<br>PNG mtime 为 12:53:27.657，而本窗名义窗尾为 14:06:58.607，mtime 早于窗尾达 4410.9497s（早 73.5 分钟）。系 T36 磁盘残留件。 | 与 T36/w1 同字节 (`c1c1dbbd0881e694...`) | 缺本趟采集声明（声明为 None）；mtime 与本窗时序完全脱节（残留件） |
| 8 | `D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip/archive_T38/measure_w2_end_x.png` | 计分屏 | 右上标题「遭遇战□分」；计分表左上「游戏:1」；右上「时□:00:00:32」；表头「玩家」「摧毁数」「□失数」「建造数」「分数」；行1黄色「□□」；行2蓝色「[New Play...]」 | 行1(黄): 0 / 6 / 1 / 0<br>行2(蓝): 0 / 0 / 0 / 0 | forensics声明: ts=14:07:23+08:00, png=measure_w2_end_x.png, capture_ok=True, empty_window=True, focus_ok=False, frame=940。<br>PNG mtime: 14:07:23.773（较声明ts偏+0.7736s）；名义窗尾: 14:07:23.634（mtime偏+0.1390s）。落盘时间吻合。 | 独立 (`4bcbdc41da5dc8ca...`) | 采集声明中 focus_ok 为 false（前台焦点未获得，但截获到游戏画面） |
| 9 | `D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip/archive_T39/measure_w2_end_x.png` | 计分屏 | 右上标题「遭遇战□分」；计分表左上「游戏:1」；右上「时□:00:00:31」；表头「玩家」「摧毁数」「□失数」「建造数」「分数」；行1黄色「□□」；行2蓝色「[New Play...]」 | 行1(黄): 0 / 9 / 1 / 0<br>行2(蓝): 0 / 0 / 0 / 0 | forensics声明: ts=15:51:55+08:00, png=measure_w2_end_x.png, capture_ok=True, empty_window=True, focus_ok=True, frame=945。<br>PNG mtime: 15:51:55.167（较声明ts偏+0.1676s）；名义窗尾: 15:51:55.085（mtime偏+0.0823s）。对齐一致。 | 独立 (`989a7fc7d0d89bf4...`) | 无（本趟仅存 w2 截图，无 w1 图） |
| 10 | `D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip/archive_T40/measure_w1_end_x.png` | 计分屏 | 右上标题「遭遇战□分」；计分表左上「游戏:1」；右上「时□:00:00:30」；表头「玩家」「摧毁数」「□失数」「建造数」「分数」；行1红色「□□」；行2蓝色「[New Play...]」 | 行1(红): 0 / 6 / 0 / 0<br>行2(蓝): 0 / 0 / 0 / 0 | forensics声明: ts=16:04:28+08:00, png=measure_w1_end_x.png, capture_ok=True, empty_window=True, focus_ok=True, frame=908。<br>PNG mtime: 16:04:28.444（较声明ts偏+0.4445s）；名义窗尾: 16:04:28.350（mtime偏+0.0940s）。对齐一致。 | 独立 (`35f98a5c9f926c50...`) | 无 |
| 11 | `D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip/archive_T40/measure_w2_end_x.png` | 计分屏 | 右上标题「遭遇战□分」；计分表左上「游戏:1」；右上「时□:00:00:30」；表头「玩家」「摧毁数」「□失数」「建造数」「分数」；行1红色「□□」；行2蓝色「[New Play...]」 | 行1(红): 0 / 6 / 0 / 0<br>行2(蓝): 0 / 0 / 0 / 0 | forensics声明: ts=16:04:53+08:00, png=measure_w2_end_x.png, capture_ok=True, empty_window=True, focus_ok=True, frame=908。<br>PNG mtime: 16:04:53.525（较声明ts偏+0.5251s）；名义窗尾: 16:04:53.445（mtime偏+0.0796s）。对齐一致。 | 独立 (`e0b17ae3e6b5fd53...`) | 无 |
| 12 | `D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip/archive_T41/measure_w1_end_x.png` | 计分屏 | 右上标题「遭遇战□分」；计分表左上「游戏:1」；右上「时□:00:00:28」；表头「玩家」「摧毁数」「□失数」「建造数」「分数」；行1紫色「□□」；行2蓝色「[New Play...]」 | 行1(紫): 0 / 5 / 0 / 0<br>行2(蓝): 0 / 0 / 0 / 0<br>（注：第2列摧毁数下为0；第3列□失数下为非零5；建造数0；分数0） | forensics声明: ts=16:08:48+08:00, png=measure_w1_end_x.png, capture_ok=True, empty_window=True, focus_ok=True, frame=860。<br>PNG mtime: 16:08:48.476（较声明ts偏+0.4760s）；名义窗尾: 16:08:48.397（mtime偏+0.0788s）。对齐一致。 | 独立 (`39b7804479afcd1a...`) | 无 |
| 13 | `D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip/archive_T41/measure_w2_end_x.png` | 计分屏 | 右上标题「遭遇战□分」；计分表左上「游戏:1」；右上「时□:00:00:28」；表头「玩家」「摧毁数」「□失数」「建造数」「分数」；行1紫色「□□」；行2蓝色「[New Play...]」 | 行1(紫): 0 / 5 / 0 / 0<br>行2(蓝): 0 / 0 / 0 / 0 | forensics声明: ts=16:09:13+08:00, png=measure_w2_end_x.png, capture_ok=True, empty_window=True, focus_ok=True, frame=860。<br>PNG mtime: 16:09:13.560（较声明ts偏+0.5603s）；名义窗尾: 16:09:13.476（mtime偏+0.0843s）。对齐一致。 | 独立 (`2b696222609da796...`) | 无 |
| 14 | `D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip/archive_T42/measure_w1_end_x.png` | 主菜单 | RA2 主菜单背景立绘（磁暴步兵、克里姆林宫、闪电、坦克；右侧暗色按钮槽）；右上角 WARNING 仪表内微小文字「WARNING ...」；中央无计分表、无时钟、无玩家名 | 非计分屏，四项数值无 | forensics声明: ts=16:12:05+08:00, png=measure_w1_end_x.png, capture_ok=True, empty_window=True, focus_ok=True, frame=883。<br>PNG mtime: 16:12:05.859（较声明ts偏+0.8593s）；名义窗尾: 16:12:05.778（mtime偏+0.0812s）。对齐一致。 | 与 T33/w2、T42/w2、T45/w2 同字节 (`f61c9808dabd3aef...`) | 无（主菜单立绘无计分格） |
| 15 | `D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip/archive_T42/measure_w2_end_x.png` | 主菜单 | RA2 主菜单背景立绘（磁暴步兵、克里姆林宫、闪电、坦克；右侧暗色按钮槽）；右上角 WARNING 仪表内微小文字「WARNING ...」；中央无计分表、无时钟、无玩家名 | 非计分屏，四项数值无 | forensics声明: ts=16:12:30+08:00, png=measure_w2_end_x.png, capture_ok=True, empty_window=True, focus_ok=True, frame=883。<br>PNG mtime: 16:12:30.942（较声明ts偏+0.9427s）；名义窗尾: 16:12:30.859（mtime偏+0.0833s）。对齐一致。 | 与 T33/w2、T42/w1、T45/w2 同字节 (`f61c9808dabd3aef...`) | 无（主菜单立绘无计分格） |
| 16 | `D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip/archive_T43/measure_w1_end_x.png` | 计分屏 | 右上标题「遭遇战□分」；计分表左上「游戏:1」；右上「时□:00:00:10」；表头「玩家」「摧毁数」「□失数」「建造数」「分数」；行1红色「□□」；行2蓝色「[New Play...]」 | 行1(红): 0 / 0 / 0 / 0<br>行2(蓝): 0 / 1 / 0 / 0 | forensics声明: ts=16:23:36+08:00, png=measure_w1_end_x.png, capture_ok=True, empty_window=True, focus_ok=True, frame=314。<br>PNG mtime: 16:23:36.481（较声明ts偏+0.4818s）；名义窗尾: 16:23:36.380（mtime偏+0.1012s）。对齐一致。 | 独立 (`1c627fcb26d92a1d...`) | 无 |
| 17 | `D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip/archive_T43/measure_w2_end_x.png` | 计分屏 | 右上标题「遭遇战□分」；计分表左上「游戏:1」；右上「时□:00:00:10」；表头「玩家」「摧毁数」「□失数」「建造数」「分数」；行1红色「□□」；行2蓝色「[New Play...]」 | 行1(红): 0 / 0 / 0 / 0<br>行2(蓝): 0 / 1 / 0 / 0 | forensics声明: ts=16:24:01+08:00, png=measure_w2_end_x.png, capture_ok=True, empty_window=True, focus_ok=True, frame=314。<br>PNG mtime: 16:24:01.576（较声明ts偏+0.5770s）；名义窗尾: 16:24:01.482（mtime偏+0.0942s）。对齐一致。 | 独立 (`7e4245d038f64457...`) | 无 |
| 18 | `D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip/archive_T44/measure_w1_end_x.png` | 计分屏 | 右上标题「遭遇战□分」；计分表左上「游戏:1」；右上「时□:00:00:29」；表头「玩家」「摧毁数」「□失数」「建造数」「分数」；行1红色「□□」；行2蓝色「[New Play...]」 | 行1(红): 0 / 6 / 0 / 0<br>行2(蓝): 0 / 0 / 0 / 0 | forensics声明: ts=17:34:22+08:00, png=measure_w1_end_x.png, capture_ok=True, empty_window=True, focus_ok=True, frame=883。<br>PNG mtime: 17:34:22.594（较声明ts偏+0.5950s）；名义窗尾: 17:34:22.517（mtime偏+0.0778s）。对齐一致。 | 独立 (`8dd9b5e3a132335c...`) | 无 |
| 19 | `D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip/archive_T44/measure_w2_end_x.png` | 计分屏 | 右上标题「遭遇战□分」；计分表左上「游戏:1」；右上「时□:00:00:29」；表头「玩家」「摧毁数」「□失数」「建造数」「分数」；行1红色「□□」；行2蓝色「[New Play...]」 | 行1(红): 0 / 6 / 0 / 0<br>行2(蓝): 0 / 0 / 0 / 0 | forensics声明: ts=17:34:47+08:00, png=measure_w2_end_x.png, capture_ok=True, empty_window=True, focus_ok=True, frame=883。<br>PNG mtime: 17:34:47.674（较声明ts偏+0.6747s）；名义窗尾: 17:34:47.595（mtime偏+0.0788s）。对齐一致。 | 独立 (`6444e4f947a3cc69...`) | 无 |
| 20 | `D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip/archive_T45/measure_w1_end_x.png` | 计分屏 | 右上标题「遭遇战□分」；计分表左上「游戏:1」；右上「时□:00:00:28」；表头「玩家」「摧毁数」「□失数」「建造数」「分数」；行1红色「□□」；行2蓝色「[New Play...]」 | 行1(红): 0 / 4 / 0 / 0<br>行2(蓝): 0 / 0 / 0 / 0 | forensics声明: ts=17:48:09+08:00, png=measure_w1_end_x.png, capture_ok=True, empty_window=True, focus_ok=True, frame=845。<br>PNG mtime: 17:48:09.137（较声明ts偏+0.1380s）；名义窗尾: 17:48:09.060（mtime偏+0.0775s）。对齐一致。 | 独立 (`bc34f315e1f8e9f5...`) | 无 |
| 21 | `D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip/archive_T45/measure_w2_end_x.png` | 主菜单 | RA2 主菜单背景立绘（磁暴步兵、克里姆林宫、闪电、坦克；右侧暗色按钮槽）；右上角 WARNING 仪表内微小文字「WARNING ...」；中央无计分表、无时钟、无玩家名 | 非计分屏，四项数值无 | forensics声明: ts=17:48:34+08:00, png=measure_w2_end_x.png, capture_ok=True, empty_window=True, focus_ok=True, frame=845。<br>PNG mtime: 17:48:34.219（较声明ts偏+0.2193s）；名义窗尾: 17:48:34.139（mtime偏+0.0798s）。对齐一致。 | 与 T33/w2、T42/w1、T42/w2 同字节 (`f61c9808dabd3aef...`) | 无（主菜单立绘无计分格） |
| 22 | `D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip/archive_T49_u0800/measure_w1_end_x.png` | 计分屏 | 右上标题「遭遇战□分」；计分表左上「游戏:1」；右上「时□:00:00:15」；表头「玩家」「摧毁数」「□失数」「建造数」「分数」；行1红色「□□」；行2蓝色「[New Play...]」 | 行1(红): 0 / 0 / 0 / 0<br>行2(蓝): 0 / 13 / 0 / 0 | forensics声明: ts=18:12:11+08:00, png=measure_w1_end_x.png, capture_ok=True, empty_window=True, focus_ok=True, frame=448。<br>PNG mtime: 18:12:11.775（较声明ts偏+0.7758s）；名义窗尾: 18:12:11.697（mtime偏+0.0779s）。对齐一致。 | 独立 (`d23255ff7ebdae67...`) | 无 |
| 23 | `D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip/archive_T49_u0800/measure_w2_end_x.png` | 计分屏 | 右上标题「遭遇战□分」；计分表左上「游戏:1」；右上「时□:00:00:15」；表头「玩家」「摧毁数」「□失数」「建造数」「分数」；行1红色「□□」；行2蓝色「[New Play...]」 | 行1(红): 0 / 0 / 0 / 0<br>行2(蓝): 0 / 13 / 0 / 0 | forensics声明: ts=18:12:36+08:00, png=measure_w2_end_x.png, capture_ok=True, empty_window=True, focus_ok=True, frame=448。<br>PNG mtime: 18:12:36.855（较声明ts偏+0.8556s）；名义窗尾: 18:12:36.775（mtime偏+0.0798s）。对齐一致。 | 独立 (`443e94b9fc62ba2c...`) | 无 |
| 24 | `D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip/l1_20261023e4/measure_w2_end_x.png` | 桌面非游戏 | 左侧为 ZCode 客户端（「新建任务」「自动化」「插件市场」等）；右侧为弹窗「BuddySwitch 整合预览版」（「WorkBuddy 国内版 Lawrence · 3 个账号」「Buddy Switch 多平台账号管理」「账号」「用量」等） | 非游戏画面，四项数值无 | forensics声明: ts=20:00:48+08:00, png=measure_w2_end_x.png, capture_ok=True, empty_window=True, focus_ok=False, frame=null, fg_title="BuddySwitch 整合预览版"。<br>PNG mtime: 20:00:48.272（较声明ts偏+0.2726s）；名义窗尾: 20:00:48.182（mtime偏+0.0906s）。落盘时间吻合，但画面非游戏。 | 独立 (`942d6ca4e1f986a9...`) | 游戏画面缺失（采样失效，进程不在前台被桌面窗口占据）；forensics 中 current_frame 为 null、focus_ok 为 false |
| 25 | `D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip/l3_20261023r/measure_w2_end_x.png` | 计分屏 | 右上标题「遭遇战□分」；计分表左上「游戏:1」；右上「时□:00:02:56」；表头「玩家」「摧毁数」「□失数」「建造数」「分数」；行1蓝色「[New Player]」；行2红色「□□」 | 行1(蓝): 126 / 206 / 0 / 201034<br>行2(红): 198 / 731 / 4 / 126800 | forensics声明: ts=21:02:34+08:00, png=measure_w2_end_x.png, capture_ok=True, empty_window=True, focus_ok=True, frame=4367。<br>PNG mtime: 21:02:34.082（较声明ts偏+0.0821s）；名义窗尾: 21:02:33.982（mtime偏+0.0994s）。对齐一致。 | 独立 (`6877870d05497349...`) | 无（本趟仅存 w2 截图） |

---

## 二、全量口径另附：根目录 2 张末图目视表

| 序号 | 实际绝对路径 | 画面类别 | 画面文字元素 | 数值逐格读（摧毁数 / 失败数 / 建造数 / 分数） | 采集声明与落盘对齐（forensics、mtime、窗尾偏移） | 同字节判定（整文件 SHA-256） | 缺项说明 |
|:---:|---|---|---|---|---|---|---|
| 根1 | `D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip/measure_w1_end_x.png` | 计分屏 | 右上标题「遭遇战□分」；计分表左上「游戏:1」；右上「时□:00:00:13」；表头「玩家」「摧毁数」「□失数」「建造数」「分数」；行1紫色「□□」；行2蓝色「[New Play...]」 | 行1(紫): 11 / 359 / 0 / 4100<br>行2(蓝): 3 / 12 / 0 / 4021 | 根目录下无 qc151_fields.json 采集声明。<br>PNG mtime: 2026-10-19T19:23:56.119+08:00；根目录 measure_w1.json 名义窗尾: 19:23:56.030+08:00（mtime 较窗尾偏 +0.0888s，与 JSON 落盘高度对齐）。 | 独立 (`5aee8a6e8cb0b399...`) | 缺 qc151_fields.json 采集声明 |
| 根2 | `D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip/measure_w2_end_x.png` | 计分屏 | 右上标题「遭遇战□分」；计分表左上「游戏:1」；右上「时□:00:00:13」；表头「玩家」「摧毁数」「□失数」「建造数」「分数」；行1紫色「□□」；行2蓝色「[New Play...]」 | 行1(紫): 11 / 359 / 0 / 4100<br>行2(蓝): 3 / 12 / 0 / 4021 | 根目录下无 qc151_fields.json 采集声明。<br>PNG mtime: 2026-10-19T19:24:21.207+08:00；根目录 measure_w2.json 名义窗尾: 19:24:21.120+08:00（mtime 较窗尾偏 +0.0874s，与 JSON 落盘高度对齐）。 | 独立 (`63749afd71937035...`) | 缺 qc151_fields.json 采集声明 |

---

## 三、三个分母算法与来源严格说明

三个分母口径完全不同，分子与分母不可任意调换，必须分别数清：

1. **20/25（子目录口径下的计分屏截图占比）**：
   - **分母 25**：数据根目录下所有一级子目录中存在的 `measure_w*_end_x.png` 截图总数，实查精确为 25 张（分布在 14 个子目录）。
   - **分子 20**：在这 25 张子目录末截图中，经目视员逐张打开确认画面为「计分屏」的张数恰好为 20 张。
   - **非计分屏 5 张明细**：
     - 主菜单立绘 4 张：`archive_T33/w2`、`archive_T42/w1`、`archive_T42/w2`、`archive_T45/w2`（四图整文件同字节）。
     - 桌面非游戏 1 张：`l1_20261023e4/w2`（ZCode 客户端与 BuddySwitch 弹窗，属采样失效）。

2. **22/27（全量口径下的计分屏截图占比）**：
   - **分母 27**：数据根目录下所有递归 `measure_w*_end_x.png` 截图总数（即子目录 25 张 + 根目录 2 张 = 27 张）。
   - **分子 22**：在全量 27 张末截图中，经目视员逐张打开确认画面为「计分屏」的张数恰好为 22 张（子目录 20 张 + 根目录 2 张均显示 00:00:13 计分屏 = 22 张）。
   - **非计分屏仍为 5 张**（根目录 2 张均为计分屏）。

3. **21/32（冻结窗中具计分屏证据的窗数占比，注意是窗数而非截图数）**：
   - **分母 32**：数据根目录下全量递归扫描 104 个 `measure_w*.json`，其中满足首帧非零且完全零推进（`len(f) >= 2 且 f[0] != 0 且 f[-1] == f[0]`，即首帧非零的冻结窗）的窗口总数正好是 32 个（全库 35 个零推进窗减去 3 个首帧为 0 的采样失效/复位窗：`l1_20261023e4/w2`、`l3_1101v4f/w0`、`l3_1101v4g/w0`）。
   - **分子 21 的推导**：
     - 在这 32 个 `f0 != 0 且 df == 0` 的冻结窗中：
       - 有 7 个窗口根本**没有保存任何末截图**（`archive_T32/w1`、`archive_T32/w2`、`archive_T47/w1`、`archive_T47/w2`、`l1_20261023/w0`、`l1_20261023b/w0`、`根/measure_w0`）。
       - 其余 25 个窗口各自对应有一张 `measure_w*_end_x.png` 截图。
       - 在这 25 张对应截图中，经目视员实看，有 4 个窗口对应的是「主菜单立绘」（`archive_T33/w2`、`archive_T42/w1`、`archive_T42/w2`、`archive_T45/w2`）。
       - 剩下的 21 个窗口（子目录 19 个 + 根目录 2 个）所对应的末截图**经目视实看全部为计分屏**（明细：T33/w1、T34/w1、T34/w2、T36/w1、T36/w2、T38/w2、T39/w2、T40/w1、T40/w2、T41/w1、T41/w2、T43/w1、T43/w2、T44/w1、T44/w2、T45/w1、T49/w1、T49/w2、l3r/w2、根/w1、根/w2）。
     - 因此，「21/32」代表在 32 个首帧非零的冻结窗中，拥有自身计分屏实图证据的窗口覆盖数为 21 个。
     - （注：`archive_T38/w1` 的 logic_frames 为 29，即 df=29 > 0，属于 11 个正推进停摆窗之一，不在 32 个零推进冻结窗中；其磁盘上的残留图亦不计入这 21 个窗口证据）。

---

## 四、与既有材料冲突清单及目视纠偏

1. **关于 T41/w1 摧毁数 vs 失败数的冲突**：
   - **旧记录与提示词说法**：提示词指出「本线曾把 T41/w1 的摧毁数 5 误写成 0，你务必逐格核对」，且旧材料曾称两图「双方四项全零」。
   - **目视员亲见**：打开 `archive_T41/measure_w1_end_x.png`，计分表头从左到右依次为「玩家」「摧毁数」「□失数」（损失数/失败数）「建造数」「分数」。
     - 第二列「摧毁数」下方实际数字为 `0`；
     - 第三列「□失数」（失败数）下方实际数字清晰显示为非零的 `5`（紫色数字）；
     - 第四列「建造数」下方为 `0`；
     - 第五列「分数」下方为 `0`。
   - **纠偏裁定**：旧记录中将该非零项 5 混淆到了「摧毁数」，但实图排在第三列「□失数」（失败数）。无论称其为摧毁数还是失败数，**该图行1绝非全零，而是存在明确非零数值 5**，既有材料的「双方四项全零」概括必须撤销。

2. **关于「双方四项全零」的整体概括冲突**：
   - **旧记录说法**：L:4633 等历史段落概括称结算图「双方四项全 0」，并据此推断零建筑导致瞬时失败。
   - **目视员亲见**：
     - T33/w1 建造数 2、损失数 2；
     - T34/w1, w2 下方玩家损失数 1；
     - T36/w1, w2 下方玩家损失数 1；
     - T38/w2 上方玩家损失数 6、建造数 1；
     - T39/w2 上方玩家损失数 9、建造数 1；
     - T40/w1, w2 上方玩家损失数 6；
     - T41/w1, w2 上方玩家损失数 5；
     - T44/w1, w2 上方玩家损失数 6；
     - T45/w1 上方玩家损失数 4；
     - T49/w1, w2 下方玩家损失数 13；
     - l3r/w2 双方有大量杀伤与建造（126/206/0/201034 vs 198/731/4/126800）；
     - 根目录两图损失数 359 与 12，摧毁数 11 与 3。
   - **纠偏裁定**：目视结果彻底否定了「双方四项全零」的概括。

3. **关于 e4/w2 的集合归属与画面属性冲突**：
   - **旧记录说法**：P:60–63 把 e4/w2 塞入「11 个停摆窗」；L:4663 写成「32 个冻结窗里至少 1 趟（e4/w2）」。
   - **目视员亲见**：`l1_20261023e4/measure_w2_end_x.png` 画面完全不是游戏，而是 Windows 桌面上的 ZCode 客户端与 BuddySwitch 整合预览版弹窗。其 JSON 中首帧为 0（f0=0），5949 个样点后 ReadProcessMemory 连续失败 6190 次，forensics 声明 fg_hwnd 为 198964（BuddySwitch），focus_ok=False，current_frame=null。
   - **纠偏裁定**：e4/w2 是典型的采样失效（游戏未在前台或进程已退出）。它既不在 11 个正推进停摆窗中（11 窗全部 df>0），也不在 32 个首帧非零的冻结窗中（32 窗要求 f0!=0）。旧记录将 e4 混入 11 窗或 32 窗属于严重集合混淆，以原始 JSON 与本轮实查为准。

4. **关于 T42 等四张同字节图「绝对排除拷贝」的断言冲突**：
   - **旧记录说法**：P:34、L:4541 等处曾以 mtime 吻合断言四张同字节主菜单图「绝对不是拷贝」。
   - **目视员亲见与核验**：T33/w2、T42/w1、T42/w2、T45/w2 四图整文件 SHA-256 均为 `f61c9808dabd3aefcbdeaeb8e021564f3e4f310512a6bec539c24ed4c526f94b`。目视四图均为主菜单静态立绘（无动态元素、无时钟、无计分板）。虽然各自在 qc151_fields.json 中有声明且 mtime 距各自窗尾有 65~90ms 偏移，但在物理上主菜单静态画面逐像素完全一致本就成立，因此「四次独立采集到同一静态画面」是合理解释，但不能单凭哈希与 mtime 在逻辑上「绝对排除拷贝或系统缓存」，维持 RULING_D16 的审慎限定。

5. **关于 T38/w1 残留件与时钟倒退的冲突**：
   - **旧记录说法**：曾有记录怀疑 T38 时钟在倒退（w1 为 00:00:10，w2 为 00:00:32）。
   - **目视员亲见与核验**：`archive_T38/measure_w1_end_x.png` 与 `archive_T36/measure_w1_end_x.png` 完全同字节 (`c1c1dbbd0881e694...`)。T38 的 qc151_fields.json 中 w1 的 forensics 明确记录 `forensics_png: null`、`empty_window: False`（根本未声明截图落盘）。该 PNG 的 mtime 为 12:53:27，早于 T38 运行时间（14:06:33 起）达 4410.95 秒。这确证它是磁盘遗留的前序残留件，绝非 T38 时钟倒退。

6. **关于前序目视报告（GLM V:181/V:206）漏项的纠偏**：
   - **旧记录现状**：GLM 报告标题写「13 张」，后表列更多文件，且 V:206 自认 T36/w1 未单独打开。
   - **本次验收**：目视员对全部 25 张子目录图及 2 张根目录图独立逐张用 Read 打开视觉核验，T36/w1 与 T38/w1 均分别独立打开并确认画面，消除了前序记录的所有漏开与模糊之处。
