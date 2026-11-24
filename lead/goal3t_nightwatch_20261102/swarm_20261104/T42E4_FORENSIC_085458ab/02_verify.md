# T42E4 取证 · 独立核验报告（02_verify.md）

- 核验人：独立核验员（与取证员不同会话、独立复算路径）
- 日期：2026-11-05
- 数据根（只读）：`D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip`
- 结论总览：**C1–C13 全部 CONFIRMED（13/13）**；无 REFUTED、无 UNVERIFIABLE。disagreements = 无。
- 铁律遵守：零真机（未启动任何游戏/加载器，未 taskkill，未读进程内存）；母本/台账/候选件全部只读；未 commit、未 git add；全部产物只写在本目录；python 一律 `python -I -X utf8` + 绝对路径；全部 PNG 判读均为本人用 Read 工具目视，未以哈希或 p 值代替目视。

---

## 〇、我实际跑的命令与脚本（全部在本目录，stdlib + PIL）

| 脚本 | 作用 |
|---|---|
| `_probe_structure.py` | 探明 measure_w*.json / qc151_fields.json 结构 |
| `_verify_measures.py` | T42/e4 六窗全量数值复算（样点/帧号/边沿/stats/gate/连续性/墙钟换算） |
| `_probe_fields.py` → `_verify_captures.py` | qc151_fields META + measure_forensics_* 行逐键复读（T42/e4/T33/T34/T36/T38/T41/T45/l3r） |
| `_verify_files.py` | e4 `_launch_result.json`/`carrier_delete_result.json` 实读；T42 console/exitcode；archive_T42 mtime 清点；e4 文件清点 |
| `_verify_pngs.py` | 27 张 `measure_w*_end_x.png` 全量枚举：文件 sha256 + PIL 解码 RGB 像素 sha256 分组、mtime、组 A vs t_abs0、组 B 同微秒、C12 区域差分、T42/w1-vs-T33/w2 整幅差分 |
| `_t38_residue.py` | T38 残留件时差复算 |
| `_except_post.py` | e4 except_post mtime + 内容头实读 |
| `_except_census.py` | 全库 except_post 普查（107 件签名核验） |
| 内联 `-c` | 根目录 3 份 measure json 的 trip_id/df/span（T55j/T55h 归属）；T38 json mtime |

台账/harness 原文用 Read 工具直读：`GOAL_THREE_TARGETS_20261018.md` L4200-4354、L4356-4440、L4520-4549；`lead/goal1_harness8_20261031/qc151_trip.harness8_v4.py` L2676-2720、L4872-4931。

---

## 一、逐条复算结论（与取证员 C1–C13 一一对应）

### C1 — CONFIRMED
我实算（`_verify_measures.py`，全键实读 + 独立重算）：
- T42/w0：t_abs0=1792311075.7651892（墙钟 2026-10-18 16:11:15.765），t 187239.053864→187264.052356（span 24.998492s），12501 样点，f 131→883（df=752），frame_edges n=753（首 [131,187239.053864]、末 [883,187263.109514]），stats.fps_avg=30.081814…、fps_p50=31.107633…、logic_frames=752、max_stall_s=0.942842、note=''，verdict=ok；gate={pre_fps15:31.38, units0:242, ok:True}。我重算 fps_avg=df/span=30.0818、fps_p50=1/median(dt)=31.1076，与存储值一致。
- T42/w1：f 883→883（df=0），1 edge，logic_frames=0，note='frame not advancing'，max_stall 24.997711s，gate.ok=True；w2 同形态（t 187289.149742→187314.149223，df=0）。
- 首尾相接：w0 末样点→w1 首样点 Δ=15.8ms；w1 末→w2 首 Δ=83.9ms（我实算 15.8/83.9，与 timeline 逐位同）。
- units0=242 三窗同值（w0 前置闸一次）。

### C2 — CONFIRMED
`archive_T42/qc151_fields.json`（list[262]，group=MEASURE）逐键实读：
- w1 行：game_hwnd=9177688、game_title="Yuri's Revenge"、fg_hwnd=9177688、fg_title="Yuri's Revenge"、focus_ok=true、current_frame=883、empty_window=true、forensics_png="measure_w1_end_x.png"、capture_ok=true、capture_wh=[800,600]、ts=2026-10-18T16:12:05+08:00。
- w2 行：同 hwnd/title/focus/current_frame=883、capture 指向 measure_w2_end_x.png、ts=16:12:30+08:00。
- w0 行：empty_window=false、无 png 字段。

### C3 — CONFIRMED
- T42/w1、w2 目视（本人 Read 打开）：RA2 主菜单立绘——持电磁武器的士兵、背景克里姆林宫塔+闪电+坦克，右侧暗色菜单按钮列与黄色 WARNING 小屏；**无计分表、无时钟、无鼠标光标**。四张同字节件（T42/w1、T42/w2、T33/w2、T45/w2）我逐张打开，画面同一。
- e4/w2 目视：ZCode 桌面客户端（左侧「新建任务/自动化/插件市场/任务列表」，任务条目含「请在 D:\Project\brickkit 执行…」等）+ 前台弹窗标题**「BuddySwitch 整合预览版」**（内含 WorkBuddy 国内版/Buddy Switch/账号），完全非游戏画面——与取证记录 fg_title 逐字吻合。
- `l1_20261023e4/qc151_fields.json` measure_forensics_w2：game_title=""、fg_hwnd=198964、fg_title="BuddySwitch 整合预览版"、focus_ok=false、current_frame=null、capture_ok=true、wh=[800,600]。
- `l1_20261023e4/measure_w2.json` error 原文：`ReadProcessMemory 失败 6190 次（有效样本 5949）`。
- 台账 L4304-4305（§543 诚实账 4）确实将 T42 与 l1_20261023e4 挂账「仍未解释」；本案事实足以销账。

### C4 — CONFIRMED
`l1_20261023e4/measure_w1.json` 实算：
- frame_edges n=113：首 [3557,17133.074818]，推进段末 [3668,17136.768445]（推进 3.6936s、111 条推进沿），末沿 **[0,17142.340036]**；之后 samples 全为 f=0（我逐点核验 all-after-zero=True，首个零样点 idx=4633，前一点 f=3668 @17142.337524）。
- 墙钟换算：t_abs0(w1)=1793015998.1610854（19:59:58.161）+ 偏移 9.265218s ⇒ 复位读零 ≈ **20:00:07.426**（取证员写 ≈20:00:07.43，一致）。
- stats.logic_frames = **-3557**（=f 末 0 − 首 3557，负数复现）；n_edges=113；max_stall=15.732883s。
- 空窗判据 `qc151_trip.harness8_v4.py:4911-4912`：`_empty = (stats is None or stats.get("logic_frames")==0 or (stats.get("n_edges") or 0)<=1)` —— w1：logic_frames=-3557≠0 且 n_edges=113>1 且 stats 非 None ⇒ empty_window=false ⇒ 不存图（目录实测只有 measure_w2_end_x.png，无 w1 图）；forensics w1 行 cur=0、empty=False 复现。

### C5 — CONFIRMED
`l1_20261023e4/measure_w2.json` 实算：
- 5949 样点（=len(f)=len(t)=stats.samples），t 17158.095604→17169.990179（span 11.894575s）；我逐对算步长：**中位 2.482ms、>10ms 缺口 0 个**（最大步长 6.715ms）、f 全零。
- 最后有效样点墙钟 ≈20:00:35.076，窗口名义结束 ≈20:00:48.182 ⇒ **静默尾段 13.105s**（≈13.1s）无一有效读数——「前段读得到（帧恒 0）、后段读不到」成立。
- `except_post_20261026T200053072552.txt`：os.stat mtime=**2026-10-26 20:00:53.073824**；内容头 `Error code: EXCEPTION_SINGLE_STEP … Exception occurred at 007CFC9F`。
- §544 清算第 10 条「107/107 基线残件」我另行全库普查复现：`_except_census.py` 数得 **107 个 except_post*.txt，107 个都含 SINGLE_STEP@007CFC9F**（含成功趟），e4 只是其中之一 ⇒ 不作崩溃孤证成立。
- `_launch_result.json`：rc=0、duration_s=275.4、leftover_procs=[]、carriers_deleted=true。

### C6 — CONFIRMED
- e4 `_launch_result.json` 实读：rc=0、duration_s=275.4、leftover_procs=[]、carriers_deleted=true、harness=`lead\goal1_harness7_20261023\qc151_trip.harness7.py`（harness_sha16=d019e8beecfb5fd8）、trip_id=QC161-U0800-L1-20261023E4。
- e4 `carrier_delete_result.json` 实读全键：**无 rc/duration 字段**；有 deleted=true、deleted_at="2026-10-26T20:01:11+08:00"、residual_exists=false（另有 applicable/identity_check/revalidation 等）。
- `archive_T42/_launch_result.json`：os.path.exists=**False**（缺）。
- `archive_T42/T42_console.log`：size=0、mtime=2026-10-18 16:10:15.255；根级 `T42_console.exitcode` 内容 = **b'0\n'**。

### C7 — CONFIRMED
`_verify_files.py` os.listdir+os.stat 全清点：
- archive_T42 共 **61** 个文件；mtime 早于本趟窗开（16:10:15）的 **30** 个，分组：06:11:16×1、08:28×17（08:28:27–08:28:45 连续）、09:12:19×1、11:45×2、12:17×1、12:56×2+12:57×3（=12:56-12:57×5）、16:07×3——与取证员给出的分组逐组相同；多组与更早趟活动时段吻合（例：T33 META ts=11:44:11 vs 旧件 11:45×2；T34 META 12:16:43 vs 12:17 件；T36 META 12:51:40 vs 12:56-57 件；T41 META 16:06:55 vs 16:07×3）。06:11/08:28×17/09:12 三组（19 件）属哪些趟，本轮同样未盘点更早趟目录（与取证员同记为缺）。
- `archive_T42/qc151_fields.json` META 首行 ts=**2026-10-18T16:10:15+08:00**（card=QC151）。
- e4 顶层 **32** 个文件，单一连续时间线 mtime 19:56:49.275–20:01:11.315，无外来旧件。

### C8 — CONFIRMED
`_verify_pngs.py` 全量枚举 **27** 张（子目录 25 + 根 2），文件 sha256 与 PIL 解码 RGB 像素 sha256 双重分组（Counter）：
- 组 A（恰 4 件）：T33/w2、T42/w1、T42/w2、T45/w2——size=275504、文件 sha256=f61c9808dabd3aef…、像素 sha256=**2f5ddc609bb0d580…**；我目视四张为同一主菜单画面（三层全同）。
- 组 B（恰 2 件）：T36/w1、T38/w1——size=269628、sha256=c1c1dbbd0881e694…、mtime 同微秒 2026-10-18 12:53:27.657366。
- **无第三组**；文件级单例 21、像素级单例 21。与 ask 给的确定性哈希逐位一致。

### C9 — CONFIRMED
我的 os.stat 实测（全精度）：
- 四件组 A mtime 互不相同：11:46:35.784015 / 16:12:05.859326 / 16:12:30.942672 / 17:48:34.219313。
- 各自嵌在本趟窗口序列：png mtime = 同窗 measure json mtime + **66.8/66.8/70.7/65.9ms**（T42w1/T42w2/T33w2/T45w2）；e4/w2 png=json+71.4ms——「json+66~71ms」复现。
- w1 图 mtime 与同趟 w2 t_abs0 同微秒级咬合：T42 Δ=**+0.2384µs**（1792311125.8593264 vs 1792311125.8593261，取证员写 Δ=0.24µs ✓）；T33 Δ=**0.0000µs**（1792295170.694078 两边全同）；T45 Δ=**−1.51ms**（png 早 1.5ms，取证员写 Δ=1.5ms，量值一致）。对照组：非组 A 的 T33/w1 图同样与 T33/w2 t_abs0 Δ=0，说明这是 harness 的机械时序（窗末截图恰好落在开下一窗的时刻），不是拷贝特征。
- 三趟 game_hwnd 各异：T33=16582032、T42=9177688、T45=21695114，且各自 forensics capture_ok=true、wh=[800,600]、ts（秒级）与 png mtime 同秒。
- 组 B 对照：两件 mtime 同微秒 12:53:27.657366 = 单次写事件指纹；且 T38 自己的 forensics w1 声明 empty_window=false（无截图），T38 META ts=14:05:05 ⇒ 该 png 早于 T38 开趟；我复算它比「T38 自己 w1 json+66.8ms 的应有 png」早 **4411.04s**（§544 清算第 2 条写 4410.95s，Δ0.09s 系 offset 假设差，可解释）。
- 结论同意取证员：正面证据全部指向「四次独立采集到同一静态主菜单」，拷贝说无任何原件正面证据；但按铁律 8，字节同一本身不能独立排除拷贝——其措辞恰当地保留了这个限界。

### C10 — CONFIRMED
- `qc151_trip.harness8_v4.py:2680-2717` `write_png_no_filter` 实读：每行前置 filter type=0（L2708 `rows.append(0)`）、IHDR 固定 `struct.pack(">IIBBBBB", w,h,8,2,0,0,0)`（L2710）、`zlib.compress(bytes(rows), 6)`（L2715）⇒ 编码器确定，同像素必同字节。
- 我 PIL 解码四件 `convert("RGB").tobytes()` sha256 全等 = 2f5ddc609bb0d580… ✓。
- ImageChops.difference(T42/w1, T33/w2)：getbbox()=**None**、extrema 全 0 ✓。
- 注：该 harness 是 20261031 目录的旁证本，当趟（2026-10-18）实际执行哪份脚本无原件（与 missing 一致）；但「PNG 规范字节级确定性」这一方法学命题本身由代码与四件同字节事实互证。

### C11 — CONFIRMED
- 台账 L4231-4242 表实读：T33 738/00:00:24、T34 302/00:00:10、T36 310/00:00:10、T38 940/00:00:30、T39 945/00:00:31、T40 908/00:00:30、T41 860/00:00:28、T43 314/00:00:10、T44 883/00:00:29、T45 845/00:00:28、T49 448/00:00:15、l3r 4367/00:02:56。
- **我的目视读数**（全部亲自打开）：T33/w1=00:00:24 ✓、T34/w1=00:00:10 ✓、T41/w1=00:00:28 ✓、T45/w1=00:00:28 ✓、l3r/w2=00:02:56 且比分两行 **126/206/0/201034** 与 **198/731/4/126800**——与 §544 清算第 4 条（L4418）逐项一致（§543 四 的 146/171 是旧读数，已被 206/731 取代，我目视支持 206/731）；根目录两张=计分屏时钟 **00:00:13** ✓（两文件字节不同——sha 5aee8a6e/63749afd——但都是计分屏）。
- 「§543 表 T33/T45 出自 w1 而非同字节 w2」成立：T33/w1、T45/w1 是计分屏，而其 w2 属组 A 主菜单。
- 根目录归属我另核：根级 measure_w1/w2.json trip_id=**QC161-U0400-T55h**、f=[373,373]、df=0、span=25.0；w0=QC161-U0400-T55j、f=[3950,3950]、span=4.0、verdict=no_advance——与勘误八之二（L4341-4342）逐位同。「T55h」指认成立。

### C12 — CONFIRMED
我用同一区域 (430,118)-(640,150) 独立重算 ImageChops：
- T34 w1-vs-w2：maxdiff=**0**、getbbox()=None（复现 §543 方法与「逐像素不变」）。
- T33：maxdiff=**231**、bbox=(0,0,105,32)；T45：maxdiff=**231**、bbox=(0,0,105,32)——两值与取证员逐位相同；原因是 w2 已从计分屏整幅换成主菜单（我目视佐证）。
- §543 三 表（L4253-4254）确含 7 趟 maxdiff=0（T34/T36/T40/T41/T43/T44/T49_u0800）、未含 T33/T45；我用目视补充：这 7 趟的 w1/w2 时钟对（10/10、10/10、30/30、28/28、10/10、29/29、15/15）也逐对相同，T38 是 10→32 唯一反例——与 §543 三 完全一致。

### C13 — CONFIRMED
- 「T42 df==0 = 终局态（计分屏）」不成立：T42 窗末两图我目视均为主菜单立绘（无计分表/时钟/光标），§543 计分屏证据链对 T42 断裂——且 §543 自己在诚实账 4（L4304-4305）就把 T42 与 l1_20261023e4 排除在计分屏结论外挂账。
- 正确表述「对局结束后退回主菜单」与原件相容（fg==game、focus_ok、frame 冻结 883、菜单画面）。
- 20/25 与 22/27 两层宇宙：L4270「25 张末截图里 20 张是计分屏」（子目录口径）vs L4346/L4419「计分屏证据 22/27（漏根目录 T55h 两张 p=0.3481）」（全量口径）；分母 25=子目录 end png 数、27=25+根 2——与我的枚举一致。**我独立目视数出的分子：子目录 25 张中计分屏恰 20 张（非计分屏 5 张=T33/w2、T42/w1、T42/w2、T45/w2、e4/w2），全量 27 张中恰 22 张**——两个数我自己都数出来了，且都只能各配各的分母，不可混引。L4347 台账自req「引用须注明层级」属实。

---

## 二、ask 指定专项

### 专项 5：「独立整幅 21/25」与 2f5ddc60
- 我的计数（25 张子目录 universe）：**同字节**组仅两组——组 A 4 件（f61c9808）、组 B 2 件（c1c1dbbd）；**「像素同而字节不同」的组：0 个**（两个像素组各自 bytes_same=True）；独立文件 21 件；独立画面 21 幅（组 B 两件同画面计 1）⇒ **21/25 成立**（台账 L4302 原文「独立整幅仅 21/25」）；全量 27 universe 独立画面 **23** 幅 ⇒ 台账 L4346「独立整幅 23/27」也复现。
- **2f5ddc60 是什么**：它是 **PNG 解码后像素数据（PIL convert("RGB").tobytes()）的 sha256**，不是整文件 sha256（整文件是 f61c9808…，组 B 像素哈希是 7c25f7e9…）。台账 L4532 的表述（「整文件 sha256 f61c9808dabd3aef…，解码像素 sha 2f5ddc609bb0d580…」）与我的复算逐位一致；L4302 简写「同 sha 2f5ddc60」指的就是像素层。查到了，不缺。

### 专项 6：20/25 与 22/27 的分母/分子
- 20/25：分母=子目录 25 张 end png；分子=其中计分屏张数，我目视逐张数出 **20**（明细：T33w1、T34w1、T34w2、T36w1、T36w2、T38w1、T38w2、T39w2、T40w1、T40w2、T41w1、T41w2、T43w1、T43w2、T44w1、T44w2、T45w1、T49w1、T49w2、l3r w2）。
- 22/27：分母=25+根 2；分子=20+根 2（根两张我目视均计分屏 00:00:13）⇒ **22**。
- 两数是同一判据（计分屏）在两个目录层级宇宙的计数，分子分母都不相同，混引会同时错分子与分母；台账 L4347 已自req注明层级。另注：27 universe 的「独立整幅」是 23/27（L4346），与「计分屏 22/27」是两个不同指标，不冲突。

### 专项 7：关键交叉判定（同字节、mtime 跨 11:46→17:48 的物理含义）
我核查的正面证据链（全部原件实读）：
1. 四张各有本趟 forensics 采集声明：T33/w2 ts=11:46:35+08:00、T42/w1 ts=16:12:05、T42/w2 ts=16:12:30、T45/w2 ts=17:48:34，capture_ok=true、capture_wh=[800,600]、current_frame 各趟不同（738/883/883/845）——声明 ts 与 png mtime **逐秒吻合**。
2. png mtime = 各自 measure_w{k}.json mtime + 65.9~70.7ms（系统性小偏移，非整数、非零——拷贝不会恰好落在这个窗）。
3. w1 图 mtime 与「开下一窗」时刻同微秒咬合（T42 +0.24µs、T33 ±0、T45 −1.5ms），这是 harness「窗末截图≈下一窗 t_abs0」的机械时序；非组 A 的 T33/w1 也服从同一规律。
4. 三趟 game_hwnd 各异，且各自 forensics 嵌在各自 qc151_fields.json 的时间线里（META→w0→w1→w2 ts 连续）。
5. 反例对照组 B：同微秒 mtime = 单次写事件，且 T38 自身声明无截图、其趟 14:05 才开始 ⇒ 组 B 是磁盘残留件（与 §544 清算第 2 条独立复现一致；时差我算 4411.04s vs 台账 4410.95s，Δ0.09s 为 offset 假设差）。
6. 画面本身：主菜单立绘无光标、无动画元素、无计时器（我目视），「四次独立采集逐像素相同」在物理上无需再假设任何巧合。
**判定**：若为拷贝，必须同时伪造/巧合上述 1–4 的全部亚秒级嵌套关系，而原件无任何拷贝痕迹；故「四次独立采集到同一静态画面」是证据支持的读法，取证员 C9 的表述（含「哈希同一不能独立排除拷贝」的限界）我完全同意。采集声明**成立**，声明时间戳与文件 mtime**吻合**。

### 专项 8：取证员写了、我未核或无法核的条目
- 「Leader 交底」原文（l1_20261023e4 截图称「ZCode 桌面客户端」）：交底文本本体未见，我只核了取证员自己的描述与目视/forensics 一致（我的目视=ZCode 客户端+BuddySwitch 弹窗，一致）。
- p=0.040 / p=0.348 等像素判据分值（L4343、L4547）：本轮未复算该判据脚本，不作判定（取证员也未以其作结论依据）。
- archive_T42 内 06:11/08:28×17/09:12 三组旧 navsig 属于哪些趟：未盘点（与取证员 missing 相同）。
- T42 当趟实际执行的 harness 脚本本体：无原件（archive_T42 无 _launch_result.json），只有 harness8_v4.py 语义旁证——维持「缺」。
- C8 的「（Counter）」只是方法标注，我用等价分组实现，数值一致。

---

## 三、timeline 六窗全读对账（ask 要求至少 3 窗，我 6 窗全读）

| 窗 | 取证员 timeline 关键值 | 我的实算 | 判 |
|---|---|---|---|
| T42/w0 | 16:11:15.765–16:11:40.778；12501 样点；f 131→883；753 edges（末沿 [883,187263.109514]）；fps 30.0818/31.1076；stall 0.943；gate 31.38/242/ok | 全同（窗口结束点由 json mtime 16:12:05.792 佐证） | ✓ |
| T42/w1 | 16:11:40.778–16:12:05.792；12501；f 883→883；1 edge；stall 24.998；note=frame not advancing | 全同 | ✓ |
| T42/w2 | 16:12:05.859–16:12:30.875；t 187289.149742→187314.149223；12501；f 883→883；1 edge | 全同 | ✓ |
| E4/w0 | 19:59:33.138–19:59:58.160；f 2821→3557；737 edges；fps 29.4414/30.6515；stall 0.070；gate 30.692/702/ok | 全同（我重算 fps_p50=30.6513，与存储 30.6515 差 0.0002，系 median 取整方法差，可解释） | ✓ |
| E4/w1 | 19:59:58.161–20:00:23.180；f 3557→3668→0；末沿 [0,17142.340036]≈20:00:07.43；113 edges；logic=-3557；stall 15.733；未存图 | 全同（我算复位墙钟 20:00:07.426） | ✓ |
| E4/w2 | 20:00:23.182–20:00:48.201；5949 样点；11.8946s；f 0→0；1 edge；stall 11.895；error 6190/5949；png=json+71ms | 全同（静默尾 13.105s） | ✓ |
| 连续性 | T42 15.8ms/83.9ms；E4 24.3ms/22.7ms | 我算 15.8/83.9 与 24.3/22.7 | ✓ |

（取证员 timeline 只给了 T42/E4 连续性差值 15.8/83.9；E4 的 24.3/22.7 是我补算，无矛盾。）

## 四、三窗定性独立判定

我**同意**取证员的定性，且认为其证据充分：
- **T42/w1、T42/w2 = 已退回主菜单（主菜单一支）**：目视主菜单立绘（无计分表/时钟/光标）+ forensics fg==game、focus_ok=true、current_frame=883 + measure json f=[883,883]。该选项括注「不在前台或已退出」与 forensics 不符，取证员取主菜单支是对的。
- **l1_20261023e4/w2 = 已退回主菜单或客户端（游戏进程不在前台或已退出）**：目视 ZCode+BuddySwitch 弹窗 + forensics game_title=""/fg=198964/focus_ok=false/current_frame=null + RPM 6190 连败 + rc=0/leftover_procs=[]。df==0 源于采样失效而非画面静止——w1 内 3668→0 计数器复位（≈20:00:07.43）+ w2 前段 11.89s 有效读数全零、后段 13.1s 无读数，支持「采样对象失效」。
- 两者均排除「采样管线残留」：png mtime 与 forensics ts 各自嵌在本趟时间线（专项 7 链条）。
- 「诚实账第 8 条」（§543 诚实账 4，L4304-4305 挂账 T42/e4）**可销账**：T42=对局结束退回主菜单；e4=前台被客户端占据+RPM 失效（进程退出确切时刻无证据，维持 missing）。

## 五、missing 清单核验（取证员 8 条，我逐条核对）

1. archive_T42/_launch_result.json 不存在 —— ✓ 我复现（os.path.exists=False）。
2. T42 当趟 harness 本体缺 —— ✓（无 launch 记录；旁证 harness8_v4.py 语义一致）。
3. T42 在局→主菜单过渡画面缺 —— ✓（w0 末无截图，w1 末已是菜单；计分屏是否出现/被谁关——无证据，维持缺）。
4. e4 复位瞬间画面缺 —— ✓（w1 empty_window=false 未存图）。
5. e4 进程退出时刻/方式缺 —— ✓（最后有效样点 20:00:35.076 与窗末 20:00:48.20 之间无进程级证据；except_post 为 107/107 基线残件）。
6. 旧 navsig 三组归属缺 —— ✓（同未盘点）。
7. 逐窗 gate 只有 w0 前置闸三处复读 —— ✓（六窗 gate 字段完全相同：T42 31.38/242，E4 30.692/702）。
8. Leader 交底文本 —— 我未见原文（见专项 8）。

## 六、目视读图清单（13 张，全部本人 Read 打开）

| 图 | 我看到的画面 |
|---|---|
| T42/w1 | RA2 主菜单立绘（士兵+克里姆林+闪电+坦克；右列暗色按钮+WARNING 小屏）；无计分表/时钟/光标 |
| T42/w2 | 同上（与 w1 同画面） |
| T33/w2 | 同上 |
| T45/w2 | 同上 |
| e4/w2 | ZCode 客户端 + 「BuddySwitch 整合预览版」弹窗（WorkBuddy 国内版/Buddy Switch/账号），非游戏画面 |
| T33/w1 | 计分屏：遭遇战成绩，游戏#1 时□:00:00:24，小数字表格 |
| T34/w1 | 计分屏 00:00:10 |
| T34/w2 | 计分屏 00:00:10 |
| T36/w2 | 计分屏 00:00:10 |
| T38/w1 | 计分屏 00:00:10（=组 B 残留件画面，对应 T36 状态而非 T38 自己的 00:00:32） |
| T38/w2 | 计分屏 00:00:32 |
| T39/w2 | 计分屏 00:00:31 |
| T40/w1、T40/w2 | 计分屏 00:00:30（两窗同钟） |
| T41/w1、T41/w2 | 计分屏 00:00:28 |
| T43/w1、T43/w2 | 计分屏 00:00:10 |
| T44/w1、T44/w2 | 计分屏 00:00:29 |
| T45/w1 | 计分屏 00:00:28 |
| T49/w1、T49/w2 | 计分屏 00:00:15 |
| l3r/w2 | 计分屏 00:02:56；比分 126/206/0/201034 vs 198/731/4/126800 |
| 根 measure_w1/w2_end_x | 计分屏 00:00:13（两文件字节不同、画面同局同钟） |

（T36/w1 未单独贴图——与 T38/w1 同字节，且 T38/w1 已目视。）

## 七、结论

- 13/13 claims CONFIRMED；disagreements 无。
- 三窗定性（T42×2=主菜单；e4/w2=客户端前台/采样失效）我独立判定成立。
- 「诚实账」挂账的 T42/e4 df==0 定性可按取证员口径销账；组 A 四张按「四次独立采集同一静态主菜单」读取，组 B 为磁盘残留件——两条均有原件正面证据。
- 需要保留的缺项以本报告 §五 为准（T42 趟级 rc/harness 本体、过渡画面、e4 进程退出时刻、旧 navsig 归属、Leader 交底原文）。
