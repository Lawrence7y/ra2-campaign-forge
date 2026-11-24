# EX-3　11 个停摆主导窗：逐窗证据资格表

**交付件**：`D:/Project/ra2-campaign-forge/lead/goal3t_nightwatch_20261102/swarm_20261104/ADJUDICATE_a70d00e5/impl_f4bcf30c/EX3_STALL_EVIDENCE.md`
**依据**：`RULING.md` D-15.3（`RULING.md:109-122`）与 EX-3 行（`RULING.md:168`）；`RECHECK.md:1-5` 判定「需修改后执行」，两处漏洞（R1 47 窗混杂字段、R2 v4c 派生指标）已由 Leader 修补进 RULING，与本表无关。
**整组裁定（照抄用途，不加强）**：11 窗整组归「停摆观测、待归因」，**既不作为已证在战卡顿正证，也不整组认定终局**；主指标计数仍为 33（22 持续低速＋11 停摆主导），核心持续低速分析仍为 22 窗/8 趟（`RULING.md:81-83`、`RULING.md:111`）。本表**不得**用来删改原始 33 个低 avg 计数。

---

## 0. 方法、口径与边界（先读）

### 0.1 名单来源与独立重建

名单取自上一阶段底账 `EX1_DATAFACE.md:148-162`（其上游 `S544_TRI_MODEL_VERDICT_20261104.md:175-176`、`XVERIFY_S544_c1606d35/VERDICT.md:73`）。本轮**独立从 104 份原始 JSON 重建**以确认「恰好 11」：

**命令（本轮实际执行，`python -I -X utf8`，退出码 0）**：

```bash
python -I -X utf8 - <<'PY'
import json, os, glob
data=r'D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip'
allj=glob.glob(os.path.join(data,'**','measure_w*.json'),recursive=True)
cand=[]
for f in allj:
    j=json.load(open(f,encoding='utf-8-sig'))
    s=j.get('stats') or {}
    if j.get('span_s')==25.0 and s.get('fps_avg') is not None and s.get('fps_avg')<28 and s.get('fps_p50') is not None and s.get('fps_p50')>=28:
        cand.append(f)
print('CHECK-1 total measure_w*.json=',len(allj))
print('CHECK-1 25s avg<28 & p50>=28 count=',len(cand))
for f in sorted(cand): print('   ',os.path.relpath(f,data).replace(os.sep,'/'))
all25=[f for f in allj if json.load(open(f,encoding='utf-8-sig')).get('span_s')==25.0]
low=[f for f in all25 if (json.load(open(f,encoding='utf-8-sig')).get('stats') or {}).get('fps_avg') is not None and json.load(open(f,encoding='utf-8-sig'))['stats']['fps_avg']<28]
print('CHECK-1 25s windows=',len(all25),' 25s low avg=',len(low))
PY
```

**实际 stdout（节选）**：

```text
CHECK-1 total measure_w*.json= 104
CHECK-1 25s avg<28 & p50>=28 count= 11
    archive_T32/measure_w0.json
    archive_T33/measure_w0.json
    archive_T34/measure_w0.json
    archive_T36/measure_w0.json
    archive_T38/measure_w1.json
    archive_T39/measure_w1.json
    archive_T43/measure_w0.json
    archive_T47/measure_w0.json
    archive_T49_u0800/measure_w0.json
    l3_20261023q/measure_w2.json
    l3_20261023r/measure_w1.json
CHECK-1 25s windows= 89  25s low avg= 33
```

`25s windows=89` 是「`span_s==25.0`」的全部件数，含 31 个非正推进/不足样窗；本轮另以 `df>0` 交叉核对得 `span25&pos=58`、`span25&nonpos=31`、`span_other&pos=5`（4 秒门控窗）、`span_other&nonpos=10`，合计 104，正推进 63、非正推进 41。故可算 25 秒窗为 58（`EX1_DATAFACE.md:77-80`），其中低 avg **33**；33 = 22 持续低速 + 11 停摆主导。本表只用其中 11 个，**33 的计数不变**。

### 0.2 时序判据的可计算性（关键前提，已实测）

题定判据：`mtime - (t_abs0 + span_s)` 落在 **+0.05 ~ +0.20 秒**内算「来源与时序可确认」；**偏离数小时的是磁盘残留件**。

- `t_abs0` 在源码里由 `time.time()` 取得（[`qc151_trip.harness8_v4.py:5301`](D:/Project/ra2-campaign-forge/lead/goal1_harness8_20261031/qc151_trip.harness8_v4.py:5301)、[`:5322`](D:/Project/ra2-campaign-forge/lead/goal1_harness8_20261031/qc151_trip.harness8_v4.py:5322)、[`:5345`](D:/Project/ra2-campaign-forge/lead/goal1_harness8_20261031/qc151_trip.harness8_v4.py:5345)），是 **Unix 墙钟秒**；`span_s=25.0`，故 `t_abs0+span_s` 即窗尾的墙钟时刻，可直接与文件 `mtime`（同为 Unix 墙钟秒）相减。
- 窗 JSON 在窗尾即刻落盘（[`qc151_trip.harness8_v4.py:4821-4825`](D:/Project/ra2-campaign-forge/lead/goal1_harness8_20261031/qc151_trip.harness8_v4.py:4821)），末取证函数在 `end_stage` 之后调用（[`:5362-5363`](D:/Project/ra2-campaign-forge/lead/goal1_harness8_20261031/qc151_trip.harness8_v4.py:5362)）。

**本轮实测校验（11 个停摆窗的 JSON 自身 mtime 对其窗尾）**：`+0.013521s ~ +0.026548s`，全部为正且远小于 0.05 s，证明该时钟口径自洽、可用于判据。命令与输出见 §3 检查 C。

**判据适用对象**：本表第 2/3 列评估的是**当窗（该停摆窗）窗尾**的末截图。第 5 列另评估**同趟后续窗**的截图（按其**各自**窗尾对齐），二者严格分开记录，绝不混用。

### 0.3 截图的「来源」如何确认

harness 只在 `empty_window=True` 时落 `measure_w{k}_end_x.png`（[`qc151_trip.harness8_v4.py:4886-4889`](D:/Project/ra2-campaign-forge/lead/goal1_harness8_20261031/qc151_trip.harness8_v4.py:4886)、[`:4911-4919`](D:/Project/ra2-campaign-forge/lead/goal1_harness8_20261031/qc151_trip.harness8_v4.py:4911)），并把 `forensics_png`/`capture_ok` 写进 `qc151_fields.json` 的 `measure_forensics_w{k}` 记录。**来源可确认** = 该窗有对应 `qc151_fields.json` 声明（`capture_ok=true`、声明文件名）＋ 该文件确实在盘 ＋ mtime 对齐该窗窗尾。三者缺一即「不可确认／未知」。

### 0.4 图像内容判读的证据等级（不越权）

本轮**没有独立打开 PNG 做目视/OCR**（`FACTBASE.md:129` 已把「PNG 目视或 OCR、截图 sha/mtime 复核」列为前一步未运行项；本轮补做了 mtime/sha 复核与存在性，但**未做新的目视**）。表中「计分屏／无面板」等画面判读，一律**转述**已读材料 `_leader_fullcensus_out.txt:57-82`（像素判据 p + 逐窗判读）、`S543_FREEZE_WAS_SCORESCREEN_20261104.md:196-201, 209-230`（勘误 B、重复件、无证据清单）、`_leader_scorescreen_out.txt:13-37`，并**明确标注为「材料记载、非本轮独立读图」**。裁决已限定 `RULING.md:101-102`：经来源与时序核验的计分屏足以认定**相应采图时刻**已处于终局/结算界面，但**不足以**把整个 25 秒或前窗整段停顿判成终局，更不能反推先前无性能问题。

### 0.5 硬约束（裁决明文，逐条落到本表）

| # | 硬约束 | 本表落实位置 |
|---|---|---|
| H1 | `l3_20261023q/w2` **不得**标「已证终局」；单列「未知阶段停摆」 | 第 11 行，§2 第 11 行；`RULING.md:118` |
| H2 | `archive_T32/w0`、`archive_T47/w0` **不得**靠后续 `df==0` 确证终局（后续冻结窗无截图） | 第 1、8 行，§2 第 1、8 行，§4；`RULING.md:120`、`S543_FREEZE_WAS_SCORESCREEN_20261104.md:221-222` |
| H3 | 11 窗整组**不得**计为「已证在战机制」或「已证终局」 | 表头、§1 汇总行、§4；`RULING.md:111` |
| H4 | 本表**不得**删改原始 33 个低 avg 计数 | §0.1、§1、§4；`RULING.md:111`、`RULING.md:168` |
| H5 | **绝不把「后续窗零推进」当成「本窗停顿的原因」** | 全表第 4 列与第 5 列分列、§1 说明、§4；`RULING.md:113-120` |

---

## 1. 主表：恰好 11 行（6 列 + 窗标识）

> 列 2「当窗末截图是否实际落盘」：以该停摆窗自己的窗尾 `t_abs0+span_s` 为基准。所有 11 行的答案均为「否」，理由见 §0.3／§3 检查 A、B。
> 列 3「来源与时序是否可确认」：当窗截图既然不存在，即**不可确认**；另把当趟内任何偏离数小时的候选件逐一点名标为**磁盘残留件**。
> 列 4「同一趟后续窗整窗零推进」：只报 `logic_frames==0`／`df==0` 的**读数**，不作因果。
> 列 5「可确认的终局关联证据」：仅当**后续窗**存在「声明＋落盘＋mtime 对齐其自身窗尾＋材料记载为计分屏」时才记「有（终局关联旁证）」；且一律注明它只覆盖采图时刻、不覆盖本窗整段。
> 列 6「未知项」：查不到的一律写「未知」，并注明查阅了哪些文件仍是缺。

| # | ① 窗标识与绝对路径 | ② 当窗末截图是否实际落盘（文件存在？mtime 与窗尾相符？） | ③ 截图来源与时序是否可确认 | ④ 同一趟后续窗整窗零推进 | ⑤ 可确认的终局关联证据 | ⑥ 未知项 |
|---|---|---|---|---|---|---|
| 1 | **`archive_T32/w0`**<br>`D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip/archive_T32/measure_w0.json`<br>尾 `2026-10-18 01:13:00.913Z`（`t_abs0=1792285955.913532 + 25.0`） | **否**。窗尾 +0.05~+0.20 s 内**无任何 PNG**（本轮遍历该趟 49 张 PNG，命中 0）；`measure_w0_end_x.png` 不存在。**`mtime 与窗尾相符：不适用（无文件）`**。`qc151_fields.json` 中 `measure_forensics_w*` 记录**缺**（该趟为旧 harness，无 QC208-② 通道）。 | **不可确认**。`frame_target_01.png` mtime `01:12:31.871Z`、Δ`−29.042s`（窗**前**开局帧，非窗末）；`navsig_*` 多张偏离 `−5375.684s ~ −16314.661s`，属**磁盘残留件**（数小时级，非本窗采集）。按判据不得算「可确认」。 | **有**。`w1`：`logic_frames=0`、`df=0`；`w2`：`logic_frames=0`、`df=0`（`measure_w1.json` / `measure_w2.json` 顶层 `stats` 与 `frame_edges`）。**仅证明停摆序列，不证明本窗停顿原因**。 | **无／未知**。后续 `w1`/`w2` 均**无截图**（`measure_w1_end_x.png`、`measure_w2_end_x.png` 都不在盘；`qc151_fields.json` 无 forensics 声明）。`S543_FREEZE_WAS_SCORESCREEN_20261104.md:221` 明记 `archive_T32 w1/w2 无截图`。**不得靠后续 `df==0` 确证终局（H2）**。 | **未知**：本窗 25 s 内各时刻战术阶段、9.574864 s 停顿的运行期原因、是否/何时进入终局。已查 `measure_w0.json`、`measure_w1.json`、`measure_w2.json`、`qc151_fields.json`、`_leader_fullcensus_out.txt`、`S543_FREEZE_WAS_SCORESCREEN_20261104.md:218-230` 仍是**缺**。 |
| 2 | **`archive_T33/w0`**<br>`.../archive_T33/measure_w0.json`<br>尾 `2026-10-18 03:45:45.590Z` | **否**。窗尾 +0.05~+0.20 s 内命中 0；`measure_w0_end_x.png` 不存在。`qc151_fields.json:measure_forensics_w0` 明记 `empty_window=False`、无 `forensics_png`、无 `capture_ok`。**`mtime：不适用`**。 | **不可确认**（当窗无图）。同趟 `measure_w1_end_x.png` Δ`+25.103682s`、`measure_w2_end_x.png` Δ`+50.193619s`（相对**本窗**窗尾）均不在窗内；`frame_target_01.png` Δ`−29.030s` 为窗前开局帧；`navsig_nav_setup_post_01_g.png` 等偏离 `−25479.338s` 属**磁盘残留件**。 | **有**。`w1`：`logic_frames=0`、`df=0`；`w2`：`logic_frames=0`、`df=0`。**仅停摆序列**。 | **有（终局关联旁证，级别受限）**。后续 `w1` 的 `measure_w1_end_x.png` 存在，mtime `03:46:10.694Z`，对**其自身窗尾** `03:46:10.610Z` Δ`+0.084068s`（在 +0.05~+0.20）；`qc151_fields.json:measure_forensics_w1` 声明该文件且 `capture_ok=true`，来源可确认；`_leader_fullcensus_out.txt:58` 记 `p=0.349 3c55bc86b7076794 计分屏(待目视)`（**材料记载、非本轮独立读图**）。`w2` 图 Δ`+0.089937s` 亦对齐，但 `_leader_fullcensus_out.txt:59` 记 `p=0.040 … 无面板`（`S543_FREEZE_WAS_SCORESCREEN_20261104.md:209-211, 215-230` 计入「纯战斗画面／4 张同图副本」），**不构成计分屏正证**。⇒ 只可注「采图时刻处于终局/结算界面」的旁证，**不得把本窗整段停顿判成终局，也不得把后续零推进自动等同计分屏**（`RULING.md:117`）。 | **未知**：本窗 10.814527 s 停顿原因、本窗内是否已在结算界面、`w1` 与 `w2` 图像不同（计分屏→无面板）的含义——`S543_FREEZE_WAS_SCORESCREEN_20261104.md:229-230` 自承「要么截图陈旧、要么真是另一种停摆，本件分不清，不作结论」。已查上述 JSON、`qc151_fields.json`、`_leader_fullcensus_out.txt`、`_leader_scorescreen_out.txt` 仍是**缺**。 |
| 3 | **`archive_T34/w0`**<br>`.../archive_T34/measure_w0.json`<br>尾 `2026-10-18 04:18:07.086Z` | **否**。窗尾 +0.05~+0.20 s 内命中 0；`measure_w0_end_x.png` 不存在；`measure_forensics_w0` 记 `empty_window=False`、无 png、无 `capture_ok`。**`mtime：不适用`**。 | **不可确认**（当窗无图）。同趟 `measure_w1_end_x.png` Δ`+25.097453s`、`measure_w2_end_x.png` Δ`+50.179159s`（相对本窗窗尾）不在窗内；`frame_target_01.png` Δ`−29.025s` 为窗前开局帧；`navsig_nav_setup_post_01_g.png` 偏离 `−27420.834s` 属**磁盘残留件**。 | **有**。`w1`：`logic_frames=0`、`df=0`；`w2`：`logic_frames=0`、`df=0`。**仅停摆序列**。 | **有（终局关联旁证，级别受限）**。`w1`/`w2` 的 `measure_w1_end_x.png`（Δ`+0.079328s`）、`measure_w2_end_x.png`（Δ`+0.081706s`）均存在、声明一致、`capture_ok=true`、时序对齐各自窗尾；`_leader_fullcensus_out.txt:60-61` 记两图均为 `p=0.349 计分屏(待目视)`（**材料记载**）。⇒ 仅采图时刻的终局/结算界面旁证；`RULING.md:102` 明确「截图在窗末，不能单靠该图把整个 25 秒每一时刻都标成终局」。本窗 `max_stall_s=24.734761s`、`df=9`，**本窗内部状态仍未知**。 | **未知**：本窗 24.734761 s 长停顿的运行期原因、本窗末沿后到 w1 之间的阶段转换时点。已查 `measure_w0/w1/w2.json`、`qc151_fields.json`、`_leader_fullcensus_out.txt`、`FACTBASE.md:103`（1 微秒差披露）仍是**缺**。 |
| 4 | **`archive_T36/w0`**<br>`.../archive_T36/measure_w0.json`<br>尾 `2026-10-18 04:53:02.566Z` | **否**。窗尾 +0.05~+0.20 s 内命中 0；`measure_w0_end_x.png` 不存在；`measure_forensics_w0` 记 `empty_window=False`、无 png、无 `capture_ok`。**`mtime：不适用`**。 | **不可确认**（当窗无图）。同趟 `measure_w1_end_x.png` Δ`+25.090641s`、`measure_w2_end_x.png` Δ`+50.185656s`（相对本窗窗尾）不在窗内；`frame_target_01.png` Δ`−29.029s` 为窗前开局帧；`navsig_nav_setup_post_01_g.png` 偏离 `−18577.337s` 属**磁盘残留件**。 | **有**。`w1`：`logic_frames=0`、`df=0`；`w2`：`logic_frames=0`、`df=0`。**仅停摆序列**。 | **有（终局关联旁证，级别受限）**。`w1`/`w2` 两图存在、声明一致、`capture_ok=true`，对各自窗尾 Δ`+0.076847s` / `+0.094500s`；`_leader_fullcensus_out.txt:62-63` 记均 `p=0.349 计分屏(待目视)`（**材料记载**）。⇒ 仅采图时刻终局/结算界面旁证，不覆盖本窗整段；`S543_FREEZE_WAS_SCORESCREEN_20261104.md:61` 记 w1/w2 计时器逐像素相同（静态结算屏），亦只描述**后续窗**画面。 | **未知**：本窗 19.332772 s 停顿原因、本窗内是否已进入结算。已查 `measure_w0/w1/w2.json`、`qc151_fields.json`、`_leader_fullcensus_out.txt`、`S543_FREEZE_WAS_SCORESCREEN_20261104.md:54-77` 仍是**缺**。 |
| 5 | **`archive_T38/w1`**<br>`.../archive_T38/measure_w1.json`<br>尾 `2026-10-18 06:06:58.607Z` | **否**。窗尾 +0.05~+0.20 s 内命中 0；**`measure_w1_end_x.png` 虽在盘，但 mtime 为 `2026-10-18 04:53:27.657Z`，对窗尾 Δ`−4410.949692s`（≈ −1.23 小时）**，与窗尾**严重不符**；`qc151_fields.json:measure_forensics_w1` 明记 `empty_window=False`、无 `forensics_png`、无 `capture_ok`（即 harness 声明**该窗没有落图**），且 `focus_ok=False`。 | **不可确认，且该同名文件明确为磁盘残留件**：本轮实测其 sha256 `c1c1dbbd0881e694a1bea969b1de0ea1f056f9ce2f125f3077a04d195985fdb2`，与 `archive_T36/measure_w1_end_x.png` **逐字节相同**（同 269628 B、mtime 同到微秒）；与 `S544_TRI_MODEL_VERDICT_20261104.md:114`（错误清单第 2 条：「**磁盘残留件**：mtime 比窗尾早 4410.95 秒，与 T36/w1 同 sha `c1c1dbbd`」）一致。**不得把这残留件当作本窗或本趟的时序证据**。另有 `navsig_burst_01_g.png` Δ`−6560.752s` 等同趟数小时级残留件。（`S543_FREEZE_WAS_SCORESCREEN_20261104.md:72-77, 213-214` 曾把该残留件当「T38/w1 屏显 00:00:10 / 1 帧级时间错位」，该判读已被 `S544_TRI_MODEL_VERDICT_20261104.md:113-114`、`RULING.md:105` 撤回，**不再采信**。） | **有**。`w2`：`logic_frames=0`、`df=0`。**仅停摆序列**。 | **有（终局关联旁证，级别受限；不含 w1 残留件）**。后续 `w2` 的 `measure_w2_end_x.png` 存在，mtime `06:07:23.773Z`，对**其自身窗尾** `06:07:23.634Z` Δ`+0.138980s`（在 +0.05~+0.20），`qc151_fields.json:measure_forensics_w2` 声明一致且 `capture_ok=true`（但 `focus_ok=False`）；`_leader_fullcensus_out.txt:65` 记 `p=0.349 a7ca0134817abdd7 计分屏(待目视)`（**材料记载**）。⇒ 仅 w2 采图时刻的终局/结算界面旁证。**`measure_w1_end_x.png` 残留件不参与任何正面证据**；`RULING.md:105` 明确不得再用已撤回的 T38 时间/截图时序作依据。 | **未知**：本窗 24.077365 s 停顿原因、`w1` 残留件的来源与落盘路径（只知与 T36/w1 同字节，不知谁在何时拷入）、`focus_ok=False` 对截图内容的影响、本窗内阶段。已查 `measure_w1.json`、`measure_w2.json`、`qc151_fields.json`、`_leader_fullcensus_out.txt`、`S543_FREEZE_WAS_SCORESCREEN_20261104.md:67-77`、`S544_TRI_MODEL_VERDICT_20261104.md:113-114` 仍是**缺**。 |
| 6 | **`archive_T39/w1`**<br>`.../archive_T39/measure_w1.json`<br>尾 `2026-10-18 07:51:30.070Z` | **否**。窗尾 +0.05~+0.20 s 内命中 0；`measure_w1_end_x.png` 不存在；`measure_forensics_w1` 记 `empty_window=False`、无 png、无 `capture_ok`。**`mtime：不适用`**。 | **不可确认**（当窗无图）。同趟 `measure_w2_end_x.png` Δ`+25.097439s`（相对本窗窗尾）不在窗内；`frame_target_01.png` Δ`−54.044s` 为窗前开局帧；`navsig_nav_start_pre_03_g.png` 等偏离 `−34813.986s` 属**磁盘残留件**。 | **有**。`w2`：`logic_frames=0`、`df=0`。**仅停摆序列**。 | **有（终局关联旁证，级别受限）**。后续 `w2` 的 `measure_w2_end_x.png` 存在，mtime `07:51:55.167Z`，对其自身窗尾 `07:51:55.085Z` Δ`+0.082308s`，`qc151_fields.json:measure_forensics_w2` 声明一致、`capture_ok=true`；`_leader_fullcensus_out.txt:66` 记 `p=0.349 253956a689cf1ee6 计分屏(待目视)`（**材料记载**）。⇒ 仅 w2 采图时刻的终局/结算界面旁证，不覆盖本窗整段。 | **未知**：本窗 23.981746 s 停顿原因、本窗内阶段、`w1` 为何无末图。已查 `measure_w1/w2.json`、`qc151_fields.json`、`_leader_fullcensus_out.txt` 仍是**缺**。 |
| 7 | **`archive_T43/w0`**<br>`.../archive_T43/measure_w0.json`<br>尾 `2026-10-18 08:23:11.367Z` | **否**。窗尾 +0.05~+0.20 s 内命中 0；`measure_w0_end_x.png` 不存在；`measure_forensics_w0` 记 `empty_window=False`、无 png、无 `capture_ok`。**`mtime：不适用`**。 | **不可确认**（当窗无图）。同趟 `measure_w1_end_x.png` Δ`+25.114727s`、`measure_w2_end_x.png` Δ`+50.209925s`（相对本窗窗尾）不在窗内；`frame_target_01.png` Δ`−29.041s` 为窗前开局帧；`navsig_nav_start_pre_03_g.png` 偏离 `−36715.283s` 属**磁盘残留件**。 | **有**。`w1`：`logic_frames=0`、`df=0`；`w2`：`logic_frames=0`、`df=0`。**仅停摆序列**。 | **有（终局关联旁证，级别受限）**。`w1`/`w2` 两图存在、声明一致、`capture_ok=true`，对各自窗尾 Δ`+0.101206s` / `+0.094192s`；`_leader_fullcensus_out.txt:73-74` 记均 `p=0.349 计分屏(待目视)`（**材料记载**）；`S543_FREEZE_WAS_SCORESCREEN_20261104.md:65` 记计时器 w1/w2 逐像素相同。⇒ 仅后续窗采图时刻的终局/结算界面旁证，不覆盖本窗整段。 | **未知**：本窗 19.188367 s 停顿原因、本窗内阶段。已查 `measure_w0/w1/w2.json`、`qc151_fields.json`、`_leader_fullcensus_out.txt` 仍是**缺**。 |
| 8 | **`archive_T47/w0`**<br>`.../archive_T47/measure_w0.json`<br>尾 `2026-10-18 09:55:16.030Z` | **否**。窗尾 +0.05~+0.20 s 内命中 0；`measure_w0_end_x.png` 不存在；`measure_forensics_w0` 记 `empty_window=False`、无 png、无 `capture_ok`。**`mtime：不适用`**。 | **不可确认**（当窗无图）。`frame_target_01.png` Δ`−29.035s` 为窗前开局帧；`navsig_nav_start_pre_03_g.png` 等偏离 `−42239.946s` 属**磁盘残留件**。同趟 `measure_w1_end_x.png` / `measure_w2_end_x.png` **连文件都不存在**（无 mtime 可比对）。 | **有**。`w1`：`logic_frames=0`、`df=0`；`w2`：`logic_frames=0`、`df=0`。**仅停摆序列，不得外推原因**。 | **无／未知**。后续 `w1`/`w2` **无截图**：本轮实测两文件 `exists=False`；但 `qc151_fields.json:measure_forensics_w1/w2` 却声明 `empty_window=True`、`forensics_png=measure_w1_end_x.png` / `measure_w2_end_x.png`、`capture_ok=true`（**声明与盘面不一致，记为未知，不猜原因**）。`S543_FREEZE_WAS_SCORESCREEN_20261104.md:222` 明记 `archive_T47 w1/w2 无截图`。**不得靠后续 `df==0` 确证终局（H2）**；不得拿别趟、别的计分屏凑证（`RULING.md:120`）。 | **未知**：本窗 6.618178 s 停顿原因、本窗内阶段、后续两窗「声明有图但盘面无图」的原因、终局归属。已查 `measure_w0/w1/w2.json`、`qc151_fields.json`、`_leader_fullcensus_out.txt`、`S543_FREEZE_WAS_SCORESCREEN_20261104.md:218-230`、`RULING.md:120` 仍是**缺**。 |
| 9 | **`archive_T49_u0800/w0`**<br>`.../archive_T49_u0800/measure_w0.json`<br>尾 `2026-10-18 10:11:46.682Z` | **否**。窗尾 +0.05~+0.20 s 内命中 0；`measure_w0_end_x.png` 不存在；`measure_forensics_w0` 记 `empty_window=False`、无 png、无 `capture_ok`。**`mtime：不适用`**。 | **不可确认**（当窗无图）。同趟 `measure_w1_end_x.png` Δ`+25.093054s`、`measure_w2_end_x.png` Δ`+50.172883s`（相对本窗窗尾）不在窗内；`frame_target_01.png` Δ`−29.028s` 为窗前开局帧；`navsig_nav_start_pre_03_g.png` 偏离 `−43230.598s` 属**磁盘残留件**。 | **有**。`w1`：`logic_frames=0`、`df=0`；`w2`：`logic_frames=0`、`df=0`。**仅停摆序列**。 | **有（终局关联旁证，级别受限）**。`w1`/`w2` 两图存在、声明一致、`capture_ok=true`，对各自窗尾 Δ`+0.077891s` / `+0.079829s`；`_leader_fullcensus_out.txt:79-80` 记均 `p=0.349 计分屏(待目视)`（**材料记载**）；`S543_FREEZE_WAS_SCORESCREEN_20261104.md:66` 记计时器 w1/w2 逐像素相同。⇒ 仅后续窗采图时刻的终局/结算界面旁证，不覆盖本窗整段。 | **未知**：本窗 14.820029 s 停顿原因、本窗内阶段。已查 `measure_w0/w1/w2.json`、`qc151_fields.json`、`_leader_fullcensus_out.txt` 仍是**缺**。 |
| 10 | **`l3_20261023r/w1`**<br>`.../l3_20261023r/measure_w1.json`<br>尾 `2026-10-30 13:02:08.958Z` | **否**。窗尾 +0.05~+0.20 s 内命中 0；`measure_w1_end_x.png` 不存在；`measure_forensics_w1` 记 `empty_window=False`、无 png、无 `capture_ok`。**`mtime：不适用`**。 | **不可确认**（当窗无图）。同趟 `measure_w2_end_x.png` Δ`+25.123816s`（相对本窗窗尾）不在窗内；`frame_target_01.png` Δ`−54.074s` 为窗前开局帧。 | **有**。`w2`：`logic_frames=0`、`df=0`。**仅停摆序列**。 | **有（终局关联旁证，级别受限）**。后续 `w2` 的 `measure_w2_end_x.png` 存在，mtime `13:02:34.082Z`，对其自身窗尾 `13:02:33.982Z` Δ`+0.099388s`，`qc151_fields.json:measure_forensics_w2` 声明一致、`capture_ok=true`；`_leader_fullcensus_out.txt:82` 记 `p=0.347 7045326f8051b197 计分屏(待目视)`（**材料记载**）；`S543_FREEZE_WAS_SCORESCREEN_20261104.md:81-94` 记该图为**完整终局比分**结算屏（126/146 摧毁、201034/126800 分）。⇒ 仅 w2 采图时刻的终局/结算界面旁证；且 `S544_TRI_MODEL_VERDICT_20261104.md:116` 已把比分读数订正为 `126/206/0/201034` 与 `198/731/4/126800`，`RULING.md:105` 要求不再用已撤回支柱强化终局归因。**不覆盖本窗 9.436278 s 停顿的每一时刻**。 | **未知**：本窗 9.436278 s 停顿原因、本窗内阶段、`w1`→`w2` 阶段转换时点。已查 `measure_w1/w2.json`、`qc151_fields.json`、`_leader_fullcensus_out.txt`、`S543_FREEZE_WAS_SCORESCREEN_20261104.md:81-94`、`S544_TRI_MODEL_VERDICT_20261104.md:116` 仍是**缺**。 |
| 11 | **`l3_20261023q/w2`**　★单列「**未知阶段停摆**」<br>`.../l3_20261023q/measure_w2.json`<br>尾 `2026-10-30 12:50:40.467Z` | **否**。窗尾 +0.05~+0.20 s 内命中 0；`measure_w2_end_x.png` 不存在；`measure_forensics_w2` 记 `empty_window=False`、无 png、无 `capture_ok`。**`mtime：不适用`**。 | **不可确认**（当窗无图）。`frame_target_01.png` mtime `12:49:21.388Z`、Δ`−79.079s`，为窗**前**开局帧，不是窗末图。 | **无**。该趟 `w0`：`logic_frames=778`、`df=778`；`w1`：`logic_frames=782`、`df=782`；本窗 `w2` 是最后一窗，`logic_frames=120`、`df=120`。数据根内无 `measure_w3+`（本轮 `CHECK: any measure_w3+ ... []`）。⇒ **没有后续零推进窗作同向序列证据**（`RULING.md:118`、`XVERIFY_S544_c1606d35/VERDICT.md:73`）。 | **无／未知**。**不得标「已证终局」，也不标「正常终局」**（H1）。全趟三窗均 `empty_window=False`，harness 未落任何 `end_x` 图；无后续计分屏、无时序可确认的终局图。 | **未知**：本窗 21.155847 s 停顿的原因、战术阶段、是否/何时进入终局、`df=120` 后是否还有未采样时间。已查 `measure_w0/w1/w2.json`、`qc151_fields.json`（三窗 forensics 均非空窗、无 png）、`_leader_fullcensus_out.txt`、`RULING.md:118` 仍是**缺**。单列**未知阶段停摆**。 |

**表中 `.../` 均为前缀 `D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip/` 的省略；每个窗的完整绝对路径见 §2 清单。**

---

## 2. 11 窗绝对路径清单（不省略，供逐条追溯）

| # | 窗标识 | 绝对原件路径 |
|---|---|---|
| 1 | `archive_T32/w0` | `D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip/archive_T32/measure_w0.json` |
| 2 | `archive_T33/w0` | `D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip/archive_T33/measure_w0.json` |
| 3 | `archive_T34/w0` | `D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip/archive_T34/measure_w0.json` |
| 4 | `archive_T36/w0` | `D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip/archive_T36/measure_w0.json` |
| 5 | `archive_T38/w1` | `D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip/archive_T38/measure_w1.json` |
| 6 | `archive_T39/w1` | `D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip/archive_T39/measure_w1.json` |
| 7 | `archive_T43/w0` | `D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip/archive_T43/measure_w0.json` |
| 8 | `archive_T47/w0` | `D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip/archive_T47/measure_w0.json` |
| 9 | `archive_T49_u0800/w0` | `D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip/archive_T49_u0800/measure_w0.json` |
| 10 | `l3_20261023r/w1` | `D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip/l3_20261023r/measure_w1.json` |
| 11 | `l3_20261023q/w2` | `D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip/l3_20261023q/measure_w2.json` |

对应 `qc151_fields.json` 同目录；`end_x` 截图同目录，文件名在各行⑤列写明。

### 2.1 按裁决 D-15.3 的证据分组（`RULING.md:115-120`）

| 分组 | 窗 | 本轮核实结果 |
|---|---|---|
| 前 10 窗（除 q/w2 外的 9 个 archive 窗 + `l3_20261023r/w1`） | #1–#10 | 10/10 同趟后续有整窗零推进（`logic_frames==0` 且 `df==0`），**只证明停摆序列**。其中 #2、#3、#4、#5、#6、#7、#9、#10 共 8 窗另有「来源/时序可确认的后续计分屏」→ 可注**终局关联旁证**；#1、#8 两窗后续冻结窗**无截图** → 无可确认终局证据。 |
| `l3_20261023q/w2` | #11 | 无后续零推进窗；单列**未知阶段停摆**，不标已证终局、不标正常终局。 |

**分组只作证据用途登记，不是本轮独立图像核验**（`RULING.md:120`）。裁决还提示 `S543_FREEZE_WAS_SCORESCREEN_20261104.md:30-43` 与 `:200-201` 的计分屏趟名单本身未完全一致，本表**不强凑一个已确认图像子集数**；每一窗的图像判读均只按 `_leader_fullcensus_out.txt:57-82` 的逐窗行转述，未跨窗补齐。另：`RULING.md:120` 明确「这里 11 个有推进停摆窗，与 32 个零推进窗中『11 个未充分覆盖窗』不是同一集合」——本表**不把两者混谈**。

---

## 3. 本轮实际执行的检查（命令与输出）

全部为**离线只读**，未启动 `gamemd.exe`/`ra2loader.exe`/YURI，未 taskkill，未读运行中进程内存，未改动任何真机 json/png、核验件、`RULING.md`/`FACTBASE.md`/`RECHECK.md`、台账或 `PENDING_DECISIONS.md`，未 commit，未写任何采样/探针/注入脚本。Python 一律 `python -I -X utf8`，路径一律绝对路径。所有原始 JSON 为单行文件，源码位置均为各文件第 1 行（引用按 `路径:1` 记）。

**检查 A：11 窗名单与 33 计数独立重建** —— 命令与实际 stdout 见 §0.1。结果 `104` 份 JSON、`11` 个停摆主导窗、`33` 个 25 秒低 avg 窗，与 `EX1_DATAFACE.md:148-162`、裁决 `RULING.md:81` 一致。

**检查 B：当窗末截图存在性与时序（题定 +0.05~+0.20 s 判据）**。命令：

```bash
python -I -X utf8 - <<'PY'
import json, os, glob
data=r'D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip'
trips=[('archive_T32','measure_w0.json'),('archive_T33','measure_w0.json'),('archive_T34','measure_w0.json'),('archive_T36','measure_w0.json'),('archive_T38','measure_w1.json'),('archive_T39','measure_w1.json'),('archive_T43','measure_w0.json'),('archive_T47','measure_w0.json'),('archive_T49_u0800','measure_w0.json'),('l3_20261023q','measure_w2.json'),('l3_20261023r','measure_w1.json')]
for trip,fn in trips:
    d=os.path.join(data,trip)
    j=json.load(open(os.path.join(d,fn),encoding='utf-8'))
    tail=j['t_abs0']+j['span_s']
    pngs=sorted(glob.glob(os.path.join(d,'*.png')))
    near=[]
    for f in pngs:
        delta=os.stat(f).st_mtime-tail
        if 0.05<=delta<=0.20: near.append((os.path.basename(f),delta))
    print('%-20s stallTail=%f pngCount=%3d near(+0.05..+0.20)=%s'%(trip,tail,len(pngs),near))
PY
```

实际 stdout（11 行，全部 `near=[]`）：

```text
archive_T32          stallTail=1792285980.913532 pngCount= 49  near(+0.05..+0.20)=[]
archive_T33          stallTail=1792295145.590396 pngCount= 51  near(+0.05..+0.20)=[]
archive_T34          stallTail=1792297087.086869 pngCount= 50  near(+0.05..+0.20)=[]
archive_T36          stallTail=1792299182.566726 pngCount= 57  near(+0.05..+0.20)=[]
archive_T38          stallTail=1792303618.607058 pngCount= 57  near(+0.05..+0.20)=[]
archive_T39          stallTail=1792309890.070121 pngCount= 58  near(+0.05..+0.20)=[]
archive_T43          stallTail=1792311791.367030 pngCount= 55  near(+0.05..+0.20)=[]
archive_T47          stallTail=1792317316.030230 pngCount= 53  near(+0.05..+0.20)=[]
archive_T49_u0800    stallTail=1792318306.682727 pngCount= 55  near(+0.05..+0.20)=[]
l3_20261023q         stallTail=1793364640.467545 pngCount=  9  near(+0.05..+0.20)=[]
l3_20261023r         stallTail=1793365328.958254 pngCount= 10  near(+0.05..+0.20)=[]
```

补充范围检查：对**整个数据根 + lead 镜像树共 2254 张 PNG** 逐个比对 11 个停摆窗窗尾，`total aligned hits for stall-window tails: 0`（本轮执行）。⇒ **11/11 当窗末截图均未实际落盘**，第 2、3 列因此全部为「否／不可确认」。这与其 `qc151_fields.json` 的 `measure_forensics_w{k}` 一致：当窗 `empty_window=False`（无图声明），只有 `archive_T32` 连 forensics 记录都缺。

**检查 C：时序框架自洽性（JSON 自身 mtime 对窗尾）**。命令见 §0.2 同源脚本，实际 stdout：

```text
  archive_T32          measure_w0.json    delta=+0.021791s t_clock=time.perf_counter
  archive_T33          measure_w0.json    delta=+0.019614s t_clock=time.perf_counter
  archive_T34          measure_w0.json    delta=+0.018125s t_clock=time.perf_counter
  archive_T36          measure_w0.json    delta=+0.013793s t_clock=time.perf_counter
  archive_T38          measure_w1.json    delta=+0.026548s t_clock=time.perf_counter
  archive_T39          measure_w1.json    delta=+0.014128s t_clock=time.perf_counter
  archive_T43          measure_w0.json    delta=+0.013521s t_clock=time.perf_counter
  archive_T47          measure_w0.json    delta=+0.013859s t_clock=time.perf_counter
  archive_T49_u0800    measure_w0.json    delta=+0.015163s t_clock=time.perf_counter
  l3_20261023q         measure_w2.json    delta=+0.017914s t_clock=time.perf_counter
  l3_20261023r         measure_w1.json    delta=+0.023427s t_clock=time.perf_counter
```

⇒ `t_abs0+span_s` 与文件系统 mtime 同一墙钟口径，判据可计算。

**检查 D：全部 27 张 `end_x` 截图对其「各自窗尾」的对齐**（本轮执行），实际 stdout 关键行：

```text
archive_T33/measure_w1_end_x.png        delta=+0.084068s OK
archive_T33/measure_w2_end_x.png        delta=+0.089937s OK
archive_T34/measure_w1_end_x.png        delta=+0.079328s OK
archive_T34/measure_w2_end_x.png        delta=+0.081706s OK
archive_T36/measure_w1_end_x.png        delta=+0.076847s OK
archive_T36/measure_w2_end_x.png        delta=+0.094500s OK
archive_T38/measure_w1_end_x.png        delta=-4410.949692s MISMATCH
archive_T38/measure_w2_end_x.png        delta=+0.138980s OK
archive_T39/measure_w2_end_x.png        delta=+0.082308s OK
archive_T43/measure_w1_end_x.png        delta=+0.101206s OK
archive_T43/measure_w2_end_x.png        delta=+0.094192s OK
archive_T49_u0800/measure_w1_end_x.png  delta=+0.077891s OK
archive_T49_u0800/measure_w2_end_x.png  delta=+0.079829s OK
l3_20261023r/measure_w2_end_x.png       delta=+0.099388s OK
```

⇒ 除 `archive_T38/measure_w1_end_x.png` 外，26/27 张时序可确认；**唯一 MISMATCH 是数小时级偏离的磁盘残留件**，已在第 5 行③列点名。另 `archive_T32`、`archive_T47` 的 w1/w2 图**根本不在 27 张清单内**（`exists=False`），但 T47 的 `qc151_fields.json` 仍声明了文件名与 `capture_ok=true`，该不一致已如实写进第 8 行。

**检查 E：残留件字节同一性**（本轮执行）：

```text
  T38/w1 sha256 = c1c1dbbd0881e694a1bea969b1de0ea1f056f9ce2f125f3077a04d195985fdb2
  T36/w1 sha256 = c1c1dbbd0881e694a1bea969b1de0ea1f056f9ce2f125f3077a04d195985fdb2
  identical = True size 269628 269628
```

与 `S544_TRI_MODEL_VERDICT_20261104.md:114` 的 sha16 `c1c1dbbd`、269628 B、4410.95 秒记载一致。

**检查 F：同一趟后续窗零推进读数和 `qc151_fields.json` 声明**（本轮执行），命令/输出要点：

```text
CHECK: any measure_w3+ anywhere in data root? []
CHECK: subsequent-window zero-advance per trip (exact)
  archive_T32          w0:lf=482,df=482 | w1:lf=0,df=0 | w2:lf=0,df=0
  archive_T33          w0:lf=444,df=444 | w1:lf=0,df=0 | w2:lf=0,df=0
  archive_T34          w0:lf=9,df=9     | w1:lf=0,df=0 | w2:lf=0,df=0
  archive_T36          w0:lf=178,df=178 | w1:lf=0,df=0 | w2:lf=0,df=0
  archive_T38          w0:lf=780,df=780 | w1:lf=29,df=29 | w2:lf=0,df=0
  archive_T39          w0:lf=781,df=781 | w1:lf=32,df=32 | w2:lf=0,df=0
  archive_T43          w0:lf=182,df=182 | w1:lf=0,df=0 | w2:lf=0,df=0
  archive_T47          w0:lf=575,df=575 | w1:lf=0,df=0 | w2:lf=0,df=0
  archive_T49_u0800    w0:lf=317,df=317 | w1:lf=0,df=0 | w2:lf=0,df=0
  l3_20261023q         w0:lf=778,df=778 | w1:lf=782,df=782 | w2:lf=120,df=120
  l3_20261023r         w0:lf=783,df=783 | w1:lf=484,df=484 | w2:lf=0,df=0
```

⇒ 10/11 有后续整窗零推进；`l3_20261023q/w2` 无（且是末窗）。forensics 声明逐窗输出（含 `archive_T47` 声明有图但 `on_disk=False`、`archive_T32` 无 forensics 记录）已用于 §1 各行③/⑤列；`capture_ok` 缺失一律写「缺」，未补造。

**检查 G：未运行／未验证的项**（如实登记）：本轮未做 PNG 目视或 OCR；未重算 104 份全库统计、21/32 图像覆盖、旧 1734 段/87.7%、ρ/φ、argv/BOOT 归属、异常件普查、12 份镜像逐字节比对；未做运行期实验、E3 或项目测试；未启动/读取活进程。表中所有「计分屏／无面板／完整终局比分」均为**材料记载**，证据等级按 `RULING.md:197` 的「他方原件核验，本裁决未重做」处理。

---

## 4. 验收对照（逐条对应题定 4 条硬约束 + 6 列）

| 判据 | 结论 | 证据位置 |
|---|---|---|
| **H1 `l3_20261023q/w2` 不得标「已证终局」，单列「未知阶段停摆」** | **满足**。该行⑤列写「无／未知；不得标已证终局，也不标正常终局」，⑥列写「单列未知阶段停摆」；④列写「无」后续零推进。依据本轮 `CHECK F`（w0/w1/w2 分别 df=778/782/120，无 w3+）与 `RULING.md:118`。 | §1 第 11 行、§2 清单第 11 行、§2.1 分组表、§3 检查 F |
| **H2 `archive_T32/w0` 与 `archive_T47/w0` 不得靠后续 `df==0` 确证终局（后续冻结窗无截图）** | **满足**。两行④列只报 `logic_frames=0, df=0` 读数并注明「仅停摆序列」；⑤列明写「无／未知」「后续 w1/w2 均无截图」「不得靠后续 `df==0` 确证终局（H2）」。本轮实测 T32 两图 `exists=False` 且无 forensics 记录；T47 两图 `exists=False`（`qc151_fields.json` 却声明 `capture_ok=true`，不一致如实记为未知）。与 `S543_FREEZE_WAS_SCORESCREEN_20261104.md:221-222`、`RULING.md:120` 一致。 | §1 第 1、8 行、§2.1、§3 检查 F、`S543_FREEZE_WAS_SCORESCREEN_20261104.md:221-222` |
| **H3 11 窗整组不得计为「已证在战机制」或「已证终局」** | **满足**。文首、§1 表头、§2.1 之后、本节均固定「停摆观测、待归因」；8 个有后续计分屏的窗只写「**终局关联旁证**」并逐行限定「仅采图时刻／不覆盖本窗整段／后续零推进不得自动等同计分屏」，无一行把整窗判成已证终局或在战机制正证。 | 文首、§0.5 H3、§1 各行⑤列、§2.1、`RULING.md:111,117` |
| **H4 本表不得用来删改原始 33 个低 avg 计数** | **满足**。§0.1 本轮独立重建 `25s low avg= 33`；文首与 §1 明写「主指标计数仍为 33，核心持续低速分析仍为 22 窗/8 趟」；全表未删除、未重分类、未改写任何窗的 `fps_avg`。 | §0.1（命令与 stdout）、文首、§1 表头、`RULING.md:81-83,111,168` |
| **列 1 窗标识（趟名/窗号）与绝对路径** | **满足**，恰好 11 行，每行含趟名/窗号；§2 另给 11 条不省略的完整绝对路径。 | §1 列①、§2 清单 |
| **列 2 当窗末截图是否实际落盘（文件存在？mtime 是否与窗尾相符？）** | **满足**。11/11 写「否」，并给出窗尾绝对时刻、遍历该趟 PNG 的命中数 0、`mtime 与窗尾相符：不适用（无文件）`；`archive_T38/w1` 特别说明同名文件虽在盘但 Δ`−4410.949692s` 与窗尾**严重不符**。 | §1 列②、§3 检查 B/C/D |
| **列 3 截图来源与时序是否可确认（+0.05~+0.20 s；偏离数小时标磁盘残留件）** | **满足**。11/11 判「不可确认」并说明来源通道（`qc151_fields.json` 的 `empty_window=False`／记录缺）；逐窗点名数小时级候选件为**磁盘残留件**（含 T38/w1 的 −4410.95 s 与 T36/w1 同 sha）；判据在 §0.2 定义并在 §3 检查 B/C 实测。 | §1 列③、§0.2/§0.3、§3 检查 B/C/D/E |
| **列 4 同一趟后续窗是否有整窗零推进（`logic_frames==0` 或 `df==0`）** | **满足**。10 行写「有」并给逐窗 `logic_frames`/`df`；第 11 行写「无」并给 w0/w1/w2 读数与「无 w3+」。每行注明「仅停摆序列，不证明本窗停顿原因」。 | §1 列④、§3 检查 F |
| **列 5 是否有可确认的终局关联证据** | **满足**。8 行写「有（终局关联旁证，级别受限）」并给出后续窗截图文件名、mtime、对**其自身窗尾**的 Δ（全部 +0.076847~+0.138980 s）、`capture_ok=true`、材料记载的计分屏判读及「仅采图时刻」限定；3 行（T32、T47、q/w2）写「无／未知」。T33/w2 无面板、T38/w1 残留件明确排除出正面证据。 | §1 列⑤、§0.4、§3 检查 D/E、§2.1 |
| **列 6 未知项：查不到的一律写「未知」** | **满足**。11/11 有「未知」段，逐行列明未知内容（本窗停顿运行期原因、本窗内战术阶段、阶段转换时点、声明与盘面不一致的原因等），并**注明查阅了哪些文件仍是缺**；未从其他窗/其他趟/推理填值。 | §1 列⑥、§0.4、§3 检查 G |
| **H5 绝不把「后续窗零推进」当成「本窗停顿的原因」** | **满足**。④列与⑤列分列且各自限定；`RULING.md:113-117,120` 的措辞在 §0.5 H5、§1 表头、§2.1、本节反复固定。 | §0.5 H5、§1 表头及各行④⑤、§2.1、`RULING.md:113-120` |

---

## 5. 与裁决其他部分的关系（不越界）

- 本表是 **EX-3 单项交付**，写到题定 `EX3_STALL_EVIDENCE.md`；未改 `RULING.md`、`FACTBASE.md`、`RECHECK.md`、`D15_IMPLEMENTATION_CANDIDATE.md`（未创建）、`D13_MECHANISM_GAP_AND_OFFLINE_CARD.md`（未创建）、台账、`PENDING_DECISIONS.md`、任何真机 json/png 或三路核验件。
- 22 窗核心集、25 对照、47 窗混杂控制字段属 EX-1／EX-4，本表不重复也不代填；33/38 的完整分母解释见 `EX1_DATAFACE.md` 与 `RULING.md:81-89`。
- 「追加勘误、历史原文不改」属 EX-2；D-13「当前 E3→① 不执行、0/22 阈值覆盖」属 EX-4。本表不涉及其结论，也不写任何采样代码。
- `RULING.md:122`：完成 EX-3 时**允许明确未知**，不要求补真机，也不以未知阻塞结案。本表的 11 个「未知」按此处置。
