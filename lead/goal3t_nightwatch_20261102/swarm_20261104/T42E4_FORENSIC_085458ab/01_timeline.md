# 01_timeline.md — T42 / l1_20261023e4 窗级取证时间线（T42E4_FORENSIC_085458ab）

取证员：RA2 真机采样产物事故取证（离线只读）。
日期：2026-11-05。数据根（只读）：`D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip`。
铁律遵守：零真机（未启动任何游戏进程、未 taskkill、未读活进程内存）；母本/真机产物/台账全只读；零采样代码，只做离线读文件与统计；未 git add / commit；唯一写域为本目录。所有 python 以 `python -I -X utf8` 运行、绝对路径。
目视声明：下文所有「这张图是什么画面」的判断全部来自本取证员用 Read 工具直接打开图片目视，哈希只用于证明字节/像素同一，不用于判画面内容。

---

## 一、六窗时间线（字段名以文件实际内容为准）

时钟说明：measure 文件顶层 `t_clock='time.perf_counter'`，`t_abs0`＝窗起始的 `time.time()`（墙钟），`samples.t` 为 perf_counter 秒。墙钟换算＝`t_abs0 + (t_first - t_abs0)` 自洽映射（perf→epoch 偏移对每趟取 w0 一对求出）。

### archive_T42（trip_id `QC161-U0400-T42`，hz=500，span_s=25.0，gate 三窗同：pre_fps15=31.38, units0=242, ok=true, gate_fps15_min=3.0, gate_span_s=1.5）

| 窗 | 文件 | t_abs0→墙钟 | samples.t 首末 | f 首→末 | 样点数 | frame_edges | stats 关键值 | verdict / note |
|---|---|---|---|---|---|---|---|---|
| w0 | `archive_T42/measure_w0.json` | 1792311075.7651892 → 16:11:15.765 | 187239.053864 → 187264.052356 | **131 → 883** | 12501 | 753；首 `[131,187239.053864]`，末沿 **`[883,187263.109514]`**（窗末前 0.94s 达 883） | fps_avg=30.081814174065407，fps_p50=31.10763396778743，logic_frames=752，max_stall_s=0.942842，n_edges=753 | `ok` / `""` |
| w1 | `archive_T42/measure_w1.json` | 1792311100.778091 → 16:11:40.778 | 187264.068145 → 187289.065857 | **883 → 883（df=0）** | 12501 | 1；唯一边沿 `[883,187264.068145]`（=窗首） | fps_avg=null，fps_p50=null，logic_frames=0，max_stall_s=24.997711 | `ok` / `frame not advancing` |
| w2 | `archive_T42/measure_w2.json` | 1792311125.8593261 → 16:12:05.859 | 187289.149742 → 187314.149223 | **883 → 883（df=0）** | 12501 | 1；唯一边沿 `[883,187289.149742]` | fps_avg=null，fps_p50=null，logic_frames=0，max_stall_s=24.999481 | `ok` / `frame not advancing` |

三窗在 perf_counter 上**首尾相接**：w0 末 187264.052356 → w1 首 187264.068145（差 15.8ms）；w1 末 187289.065857 → w2 首 187289.149742（差 83.9ms）。w1 的 t_abs0 **恰等于 w0 的文件 mtime**（1792311100.778091）——w0 落盘瞬间即开 w1。

### l1_20261023e4（trip_id `QC161-U0800-L1-20261023E4`，hz=500，span_s=25.0，gate 三窗同：pre_fps15=30.692, units0=702, ok=true）

| 窗 | 文件 | t_abs0→墙钟 | samples.t 首末 | f 首→末 | 样点数 | frame_edges | stats 关键值 | verdict / note / error |
|---|---|---|---|---|---|---|---|---|
| w0 | `l1_20261023e4/measure_w0.json` | 1793015973.1387403 → 19:59:33.138 | 17108.051715 → 17133.050518 | **2821 → 3557** | 12501 | 737；末沿 `[3557,17133.050518]` | fps_avg=29.441409419151583，fps_p50=30.651481920341467，logic_frames=736，max_stall_s=0.06958 | `ok` / `""` |
| w1 | `l1_20261023e4/measure_w1.json` | 1793015998.1610854 → 19:59:58.161 | 17133.074818 → 17158.072918 | **3557 → 0（含复位）** | 12501 | 113；头 `[3557,…]`，先推进到 `[3668,17136.768445]`，**末沿 `[0,17142.340036]`** | fps_avg=null，fps_p50=null，**logic_frames=−3557**，max_stall_s=15.732883 | `ok` / `frame not advancing` |
| w2 | `l1_20261023e4/measure_w2.json` | 1793016023.1820877 → 20:00:23.182 | 17158.095604 → 17169.990179（仅 11.8946s，非 25s） | **0 → 0（df=0，f0=0）** | **5949**（非 12501） | 1；唯一边沿 `[0,17158.095604]` | fps_avg=null，fps_p50=null，logic_frames=0，max_stall_s=11.894575 | `ok` / `frame not advancing` / **error=`ReadProcessMemory 失败 6190 次（有效样本 5949）`** |

e4/w1 细节：f 在窗内前 3.7s 从 3557 推进到 3668（111 个推进边沿，至 perf 17136.768），保持到 perf **17142.340036 读到 0**（换算墙钟 ≈**20:00:07.43**，由 w0 的 t_abs0↔t_first 对求偏移 1793008865.0870253 所得，属计算值）——**帧计数器中途复位**，此后恒 0。
e4/w2 细节：5949 个样本在 11.8946s 内**连续无缺口**（中位步长 2.482ms，>10ms 缺口 0 个），f 全零；即窗的前 11.9s 读得动（读数恒 0），最后 ≈13.1s 无一有效读数（6190 次失败 ≈ 472Hz × 13.1s）。末有效样本 perf 17169.990179 → ≈20:00:35.08；窗按计划满 25s 后落盘（mtime 20:00:48.201）。

### 窗末取证记录（`qc151_fields.json`，group=MEASURE，key=measure_forensics_w{k}）

| 趟/窗 | game_hwnd | game_title | fg_hwnd | fg_title | focus_ok | current_frame | empty_window | forensics_png / capture |
|---|---|---|---|---|---|---|---|---|
| T42/w0 | 9177688 | Yuri's Revenge | 9177688 | Yuri's Revenge | true | 883 | false | 无图 |
| T42/w1 | 9177688 | Yuri's Revenge | 9177688 | Yuri's Revenge | **true** | 883 | true | `measure_w1_end_x.png`，capture_ok=true，capture_wh=[800,600]，ts=16:12:05+08:00 |
| T42/w2 | 9177688 | Yuri's Revenge | 9177688 | Yuri's Revenge | **true** | 883 | true | `measure_w2_end_x.png`，capture_ok=true，capture_wh=[800,600]，ts=16:12:30+08:00 |
| e4/w0 | 662272 | Yuri's Revenge | 662272 | Yuri's Revenge | true | 3557 | false | 无图 |
| e4/w1 | 662272 | Yuri's Revenge | 662272 | Yuri's Revenge | true | **0** | **false**（因 logic_frames=−3557≠0 且 n_edges=113>1，见 harness 判据） | **无图** |
| e4/w2 | 662272 | **""（读空）** | 198964 | **BuddySwitch 整合预览版** | **false** | **null** | true | `measure_w2_end_x.png`，capture_ok=true，capture_wh=[800,600]，ts=20:00:48+08:00 |

harness 语义（只读源码佐证，非 T42 当趟原件）：`_measure_window_forensics` 空窗判据 `stats is None or logic_frames==0 or n_edges<=1`，空窗才存 `_end_x.png`，帧计数读 VA 0x00A8ED84 —— `lead/goal1_harness8_20261031/qc151_trip.harness8_v4.py:4877-4928`（4911-4912 判据、4907-4908 RPM、4914-4919 存图）。T42 当趟所用 harness 脚本本体**缺**（见 §八）。

---

## 二、mtime 全量对账与不兼容件

### archive_T42（61 个文件）
本趟原生序列（16:10:15→16:12:44.980，全部互相咬合）：
- `T42_console.log` **0 字节**，mtime 2026-10-18 16:10:15.255465；
- navsig 序列 21 张 16:10:31–16:11:11；`frame_target_01.png` 16:11:11.742；
- `measure_w0.json` 16:11:40.778 → `measure_w1.json` 16:12:05.792 → `measure_w1_end_x.png` **16:12:05.859326** → `measure_w2.json` 16:12:30.875 → `measure_w2_end_x.png` **16:12:30.942672** → `qc151_fields_post.json` 16:12:30.962 → `qc151_fields.json` 16:12:44.980。
- 签名：每窗 `measure json 落盘 → +67ms 端窗截图 → 立即开下一窗`。**T42/w1 png mtime 与 w2 的 t_abs0 同微秒**（|Δ|=0.24µs，float 精度内相同）；T33 同微秒（Δ=0.00µs）；T45 Δ=1.5ms。

**不兼容件：30 个** mtime 早于本趟窗（16:10:15）的 navsig/frame 文件，跨 06:11→16:07 六个时段：
1 张 06:11:16（`navsig_nav_start_pre_03_g.png`）；17 张 08:28:27–08:28:45（`navsig_nav_setup_post_04..20_x.png`）；1 张 09:12:19；2 张 11:45:02/11:45:05（与 T33 活动时段吻合）；1 张 12:17:37（与 T34 时段吻合）；1 张 12:56:41 + 4 张 12:56:58–12:57:14（与 T36/T38 时段吻合）；3 张 16:07:33–16:07:48（与 T41 时段吻合）。这些文件**不可能由 T42 趟（16:10:15 后运行）写出**——archive 目录混入了他趟旧件（保留原 mtime）。06:11/08:28/09:12 三组各属哪趟：缺（未盘点）。
关键对照：**四张同字节 end 截图的 mtime 全部是本趟新鲜件**（无一同微秒、各自嵌在自己趟的窗口序列里），与上述 30 个旧件形成鲜明反差；也与已知真残留件 `T38/w1`（与 `T36/w1` **同微秒** mtime 12:53:27.657366）反差鲜明。

### l1_20261023e4（32 个文件）
全部落在单一连续时间线 **2026-10-26 19:56:49.275 → 20:01:11.315**，无一异常：carrier_creation_receipt 19:56:49 → 探针/导航 19:56:56–19:59:29 → measure_w0 19:59:58.160 → measure_w1 20:00:23.180 → measure_w2 20:00:48.201 → `measure_w2_end_x.png` 20:00:48.272643（json+71ms）→ fields_post 20:00:48.285 → **`except_post_20261026T200053072552.txt` 20:00:53.073**（文件名内嵌 20261026T20:00:53.072552）→ carrier/清理/manifest/fields 20:00:53–20:01:11。无他趟旧件。

### 根目录层级（勘误对账）
`measure_w1.json`/`measure_w2.json` + 两张 end png：19:23:56.047/.119 与 19:24:21.137/.207（同一趟，72ms/70ms 签名）；**`measure_w0.json` mtime 2026-10-19 22:39:25.714401，比根 w1/w2 晚 3h15m** —— 与根 w1/w2 不同趟，和 §543 勘误「根目录 3 json 属旧趟 T55h/T55j」相容（勘误行 4332-4342）。

---

## 三、趟级退出证据

| 件 | 结果 |
|---|---|
| `archive_T42/T42_console.log` | **存在，0 字节**（mtime 16:10:15.255）——无任何控制台输出可读 |
| 根级 `T42_console.exitcode` | 内容 `0\n`（rc=0） |
| `archive_T42/_launch_result.json` | **不存在**（os.path.exists=False；目录清单亦无）——T42 的趟级 rc/duration_s/harness 路径**缺** |
| `l1_20261023e4/_launch_result.json` | **rc=0，duration_s=275.4**，`carriers_deleted=true`，`leftover_procs=[]`，harness=`lead/goal1_harness7_20261023/qc151_trip.harness7.py`，argv 含 `--fullscreen` |
| `l1_20261023e4/carrier_delete_result.json` | **无 rc/duration 字段**；`deleted=true`，`deleted_at=2026-10-26T20:01:11+08:00`，`residual_exists=false`，`refused_reason=null`，identity_check.same_object=true |
| `l1_20261023e4/qc151_run_log.json` | `final_exit=0`，`cleanup_failures=[]` |
| `l1_20261023e4/except_post_20261026T200053072552.txt` | **EXCEPTION_SINGLE_STEP at 007CFC9F**（游戏自带异常处理器文本，含寄存器/栈转储）。注意：§544 清算第 10 条已判「全库 107/107 同一基线残件，成功趟同样有」——单凭此件**不能**证明 w2 内致命崩溃 |

---

## 四、目视读图记录（12 张，全部本取证员亲眼读）

**同字节四连（f61c9808…，275504B）——四张同一画面：RA2 主菜单式标题画面**：左侧 2/3 为苏军步兵立绘（持巨型武器），背景燃烧的克里姆林塔楼、闪电、坦克群；右侧 1/3 为竖排菜单按钮栏，约 10 个按钮槽**全部空槽/暗态**（无可读按钮文字），右上一个「WARNING」雷达表盘（橙红刻度），底部一条空横栏。**画面中没有任何计分表、没有玩家行、没有时钟/计时文字。**
1. `archive_T42/measure_w1_end_x.png` —— 上图画面。
2. `archive_T42/measure_w2_end_x.png` —— 与 w1 同一画面（目视无差）。
3. `archive_T33/measure_w2_end_x.png` —— 与上同一画面。
4. `archive_T45/measure_w2_end_x.png` —— 与上同一画面。

5. `l1_20261023e4/measure_w2_end_x.png`（942d6ca4…，52833B）—— **完全不是游戏画面**：ZCode 桌面客户端窗口截图——左上 Z 字 logo 与前进/后退钮，左侧栏「新建任务 Ctrl+N / 自动化 / 插件市场」，任务列表含「请在 D:\Project\brickkit…」「继续本项目三目标。请完…」「继续本项目 RE-ATLAS 独…」等条目，右侧还有前台弹窗「**BuddySwitch 整合预览版**」（WorkBuddy 国内版 · Lawrence · 3 个账号；Buddy Switch 多平台账号管理；概览/账号/用量/会话）。与取证记录 fg_title 完全吻合。

**计分屏抽检（5 张子目录 + 2 张根目录）——「计分屏」判读站得住**：皆为同一版式：右上标题「遭遇战□分」，表头「玩家/摧毁数/□失数/建造数/分数」，两行数据，右上「游戏:1」与时钟：
6. `archive_T33/measure_w1_end_x.png` —— 时钟 **00:00:24**；□□ 行 0/0/2/0，[New Player] 行 0/2/0/0。与 §543 表 T33 行「738→00:00:24」吻合 ⇒ §543 的 T33 时钟读数出自 **w1**，非同字节的 w2。
7. `archive_T45/measure_w1_end_x.png` —— 时钟 **00:00:28**；数值与 T33/w1 不同（row1 建造列不同）⇒ T33/w1 与 T45/w1 互相独立。
8. `archive_T34/measure_w1_end_x.png` —— 时钟 **00:00:10**；□□ 0/0/0/0，[New Player] 0/1/0/0。与 §543 表 T34 行吻合。
9. `archive_T41/measure_w1_end_x.png` —— 时钟 **00:00:28**；数值又与 T45/w1 不同。与 §543 表 T41 行（860→00:00:28）吻合。
10. `l3_20261023r/measure_w2_end_x.png` —— 时钟 **00:02:56**；[New Player] **126/206/0/201034**，□□ **198/731/4/126800** —— 与 §544 清算第 4 条修正读数逐项一致（§543 首版 146/171 确系误读）。
11. 根 `measure_w1_end_x.png`（10-19 19:23:56）—— 计分屏，时钟 **00:00:13**，□□ 11/359/0/4100、[New Player] 3/12/0/4021（小字号，个位数字为近读）。
12. 根 `measure_w2_end_x.png`（10-19 19:24:21）—— 与根 w1 同画面同时钟 00:00:13（两文件字节不同、269683 vs 269776B，差异在计时区外）。§543 勘误「两张根目录图也是计分屏」目视成立（其 p=0.3481 引用值未复算）。

像素差分（PIL convert('RGB') + ImageChops）：
- §543 计时区 (430,118)-(640,150)：T33 w1-vs-w2 **maxdiff=231**（bbox 覆盖全区）——因为 w1=计分屏、w2=主菜单，整屏已换；T45 同 231；T34 对照 **maxdiff=0**（复现 §543）；T42 w1-vs-w2 **maxdiff=0**（同字节）。
- 全幅：T42/w1 vs T33/w2 bbox=None（零差）；T33/w1 vs T45/w1 差异区 (99,47)-(763,244)（计分面板区）；T33/w2 vs e4/w2 全幅皆异。

---

## 五、像素级比对：同到哪一层（§543 重复件的判定方法与数字）

方法：三层递进——①整文件字节 sha256（hashlib，全量 27 张枚举分组 Counter）；②解码像素 sha256（PIL 解码为 RGB 后 tobytes() 再哈希）；③目视同一画面（Read 打开）。编码器 `write_png_no_filter`（harness8_v4.py:2680-2717）全确定（filter type 恒 0、zlib level 恒 6、IHDR 固定）⇒ 同像素必同字节、同字节必同像素。

全库 27 张 `measure_w*_end_x.png`（子目录 25 + 根 2）中重复组**恰两组**，无第三组：
- **组 A（4 张）**：`archive_T33/w2`、`archive_T42/w1`、`archive_T42/w2`、`archive_T45/w2`，275504B，整文件 sha256=`f61c9808dabd3aefcbdeaeb8e021564f3e4f310512a6bec539c24ed4c526f94b`（4/4 相同），解码像素 sha256=`2f5ddc609bb0d5806936fa88df8f3c88cac3dc9ba105c3c2929ec666f6a6f759`（4/4 相同），目视同一主菜单画面。**三层全同。**
- **组 B（2 张）**：`archive_T36/w1`、`archive_T38/w1`，269628B，整文件 sha256=`c1c1dbbd0881e694a1bea969b1de0ea1f056f9ce2f125f3077a04d195985fdb2`，且 **mtime 同微秒 2026-10-18 12:53:27.657366** —— 与 §544 清算第 2 条「T38/w1=磁盘残留件（与 T36/w1 同 sha/同字节/同微秒 mtime）」独立复现一致。
- 台账 §543 诚实账 3 引用的「同 sha `2f5ddc60`」经查是**解码像素 sha256 前缀**，非文件 sha256（文件为 f61c9808…）——口径已辨明，数值本身无误。

§543「独立整幅仅 21/25」复算：分母 25=子目录 end 截图数（27−根 2，实测）；组 A 记 1（省 3）、组 B 记 1（省 1），25−3−1=**21** ✓（口径：每组记一个代表本）。
§543 勘误「独立整幅 23/27」复算：27−3−1=**23** ✓。

---

## 六、三窗定性（只在四个允许值中取）

### T42/w1 ＝ **已退回主菜单或客户端**
- 支持它的原件事实：①窗末取证记录 fg==game(hwnd 9177688)、focus_ok=true、game_title='Yuri's Revenge'、current_frame=883、empty_window=true、capture_ok=true（`archive_T42/qc151_fields.json` measure_forensics_w1 行）；②measure_w1.json f=[883,883]、logic_frames=0、note='frame not advancing'；③端窗截图目视=RA2 主菜单式画面（§四-1），**非计分屏**；④png mtime 16:12:05.859326 与 w2 t_abs0 同微秒 + measure json+67ms 签名 ⇒ 文件是本趟 harness 在窗边界现场写盘；⑤w0 帧推进 131→883、fps_avg=30.08 ⇒ w0 时仍在局。
- 若本定性成立、必须为真但我们没看到的：**w1 窗内（16:11:40.8–16:12:05.9）发生过「对局结束→（计分屏）→主菜单」的过渡**——计分屏是否出现过、被谁（用户/ harness/自动）关闭，无任何截图或记录，缺。定性中「游戏进程不在前台或已退出」这一括注**不成立**（进程在前台且聚焦）——本定性取的是「已退回主菜单」这一支。
- 排除「采样管线残留」：mtime 链如④；排除「对局结束（计分屏）」：画面无计分表无时钟。

### T42/w2 ＝ **已退回主菜单或客户端**
- 支持它的原件事实：同上（measure_forensics_w2 行同构：fg==game、focus_ok=true、current_frame=883、empty_window=true、capture_ok=true；截图目视同菜单；png mtime=json+67ms）；且与 w1 图同字节 ⇒ 25s 间隔内画面静态不变。
- 未看到的必要证据：同 T42/w1（过渡过程无画面）。

### l1_20261023e4/w2 ＝ **已退回主菜单或客户端（游戏进程不在前台或已退出）**
- 支持它的原件事实：①窗末取证记录 game_title=**""**（读空）、fg=198964「BuddySwitch 整合预览版」、**focus_ok=false**、current_frame=**null**、empty_window=true、capture_ok=true；②measure_w2.json error='ReadProcessMemory 失败 6190 次（有效样本 5949）'、f0=0=df=0、样本只覆盖前 11.9s 且连续、后 ≈13.1s 零有效读数；③截图目视=ZCode 客户端+BuddySwitch 弹窗（§四-5），与 fg_title 互证；④`_launch_result.json` rc=0、leftover_procs=[]、`carrier_delete_result.json` deleted=true ——趟以进程清零收尾；⑤w1 中帧计数器 3668→0 复位（perf 17142.34 ≈ 20:00:07.4）。
- 若本定性成立、必须为真但我们没看到的：**游戏进程退出/终止的确切时刻与方式**——20:00:35（末有效样本）到 20:00:48（取证读空）之间进程如何死掉（自行退出/被终止/崩溃），无进程表快照；except_post（20:00:53）是基线残件不能单独作证。复位瞬间（20:00:07）的画面**缺**（w1 末因空窗判据未命中未存图——harness8_v4.py:4911-4912 判据被 logic_frames=−3557 绕过）。
- 排除「采样管线残留」：e4 目录 32 件单一连续时间线，截图 mtime=json+71ms；排除「对局结束（计分屏）」：画面是客户端非计分屏。

---

## 七、对台账 §543/§544 数字的对账

1. **「25 张」/「20/25」（§543 行 4208、4270，子目录口径）**：分母=各趟子目录下 `measure_w*_end_x.png`，实测 25（27−根 2）✓。分子 20 的构成按台账自述重构=25 − 组 A 4 张（诚实账 3）− e4/w2 1 张（诚实账 4「T42 与 l1_20261023e4 不算终局态」）=20，自洽 ✓；但我只目视了其中 10 张子目录图（+根 2 张），**未逐张目视全部 25 张**，「20」的逐张清单未独立复核。
2. **「22/27」（§543 勘误行 4346，全量口径）**：=20（子目录）+2（根目录两张，本轮目视确认计分屏）=22 ✓；分母 27=子目录 25+根 2 ✓。
3. **「21/25」「23/27」独立整幅**：算术复现成立（§五）✓。
4. **两个覆盖数不能不带层级引用**：20/25 与 22/27 分母不同宇宙（25=子目录层；27=子目录+根层），数值相差的恰是根目录 2 张；不带层级引用会把全库计分屏率错报成 20/27≈74%（实为 22/27≈81.5%）。台账自己也已明文要求注明层级（行 4347「引用须注明层级」）。
5. **§543 诚实账第 4 条（T42 与 e4 的 df==0 挂账）本轮可解**：T42=对局结束后已退回主菜单（游戏进程仍在前台）；e4=进程退出/采样失效（前台已是客户端）。两者都不是计分屏、也不是引擎停摆。

## 八、缺（现有离线件回答不了的）

1. `archive_T42/_launch_result.json` **缺**——T42 趟级 rc/duration/harness 路径无原件（查过：目录精确存在性检查+全目录清单）。
2. T42 当趟所用 **harness 脚本本体缺**——只能以 harness8_v4.py:4877-4928 的行为语义与 T42 记录吻合作旁证，不等于版本同一。
3. T42 从「在局」到「主菜单」的**过渡画面缺**（w0 末无截图、w1 末已是菜单；计分屏是否出现、如何消失——无证据）。
4. e4 **帧计数器复位瞬间（≈20:00:07.4）的画面缺**（w1 末未存图，见 §六）。
5. e4 **游戏进程退出时刻与方式缺**（20:00:35→20:00:48 之间无进程级证据；except_post 为基线残件，不作崩溃孤证）。
6. 「20 张计分屏」的**逐张清单缺**——`swarm_20261104/_leader_scorecensus*` 的输出本轮未读，20 的分子构成是按台账自述重构的自洽值，非逐张独立目视复核（本轮目视覆盖 12/27 张 + 4 张同字节等价）。
7. archive_T42 内 06:11/08:28/09:12 三组旧 navsig（19 张）**属于哪些趟缺**。
8. 根目录两张图的 p=0.3481 判据值未复算（目视已确认计分屏，p 值本身缺复算）。
9. §543/§544 正文所称「31.2 fps 帽瞬时值成簇 31.24」「126/206 修正」等与本两趟无关的旁证未逐一重算（超出本轮两窗范围）。
