# N-9 · F6/F7/F8 静态规格（追既有材料版）—— lead/static_spec_n9_20261107/_n9_STATIC_COUNT_SPEC.md

任务：lead/nextstep_plan_20261106/NEXT_STEPS_20261106.md:85-91（N-9）。铁律：零真机、零采样代码、只读既有件、不 commit/push。
本文为唯一写域内新文件；所有引用 = 本会话实读的 文件:行 或本会话实跑命令输出。

## 0. 指纹核验（本会话实跑 `_n9_fingerprint.py`，python -I -X utf8，ALL_MATCH=True）

| 被核对象 | SHA256 | 字节数 |
|---|---|---|
| lead/nextstep_plan_20261106/NEXT_STEPS_20261106.md | c364467dea909da66bca16b98d12d1d625edb80dfbf831ea9e8a1077e9dad24c | 27225 |
| lead/re_line_20261105/W8_STATIC_LOCATE/W8_STATIC_LOCATE.md | 20e4eeac49254b274a8382e94505525a614ec5bf24ccb89316fcd8f914406262 | 26485 |
| lead/re_line_20261105/A1_ERRATA_MAP/ERRATA_W8.md | 660a9ecec48cabe86e8b7b8689465ff418c92b104ffa0eb1075b3ad7d96a4f05 | 28443 |
| lead/re_line_20261105/GOAL_RE_CONTINUOUS.md | 890deedd04f3b28d001737b31f6290bdca2978251f8854dc23312bc78edb7a19 | 186828 |
| lead/GOAL_THREE_TARGETS_20261018.md | 2baa0de45d4125549262eb595d7518c9ce99efeee120384bf640cded8a933ede | 759518 |

被核对象 SHA256 = c364467dea909da66bca16b98d12d1d625edb80dfbf831ea9e8a1077e9dad24c / 20e4eeac49254b274a8382e94505525a614ec5bf24ccb89316fcd8f914406262 / 660a9ecec48cabe86e8b7b8689465ff418c92b104ffa0eb1075b3ad7d96a4f05 / 890deedd04f3b28d001737b31f6290bdca2978251f8854dc23312bc78edb7a19 / 2baa0de45d4125549262eb595d7518c9ce99efeee120384bf640cded8a933ede，字节数 = 27225 / 26485 / 28443 / 186828 / 759518。

引用纪律（ERRATA_W8.md:174-186）：引 W8 三回件任一结论须与 W8_STATIC_LOCATE.md 及 ERRATA_W8.md 联引、按复核后口径读；ERRATA_W8.md:182-184 明令 W8 判定是「回件判定×复核判定」合并、**不是第三次独立重验**，F7/F8 的「无现成 VA」不得升格为 INFEASIBLE 或已证不存在。本文不写「已定位」「已证不存在」（F6 的 LOCATED 判定按 W8 原文转述并带联引）。

## 1. F6（W8 判 LOCATED：W8_STATIC_LOCATE.md:48/:151；复核 CONFIRMED：台账 §593:8758-8770）

### 1.1 字段（读数清单）——已有
- W8_STATIC_LOCATE.md:152：`[0x887324]`→`+0xB0/+0xB4`（像素原点）、`+0xD80/+0xD84`（左上格）、`+0xD88/+0xD8C`（跨度）、上游 `+0xD64..D78` 与 `0xB0CE30/34`。
- 字段表带证据：W8_STATIC_LOCATE.md:54-70（单例槽/原点/滚动/矩形/计算者 0x6D8B30/每帧驱动 vtable[23]=0x6D2540/ctor 0x6D1C20）。
- 每逻辑帧驱动链：F6_VIEWPORT.md:213（`0x55D83F..0x55D84A` → vtable[23] `0x6D2540` → 帧戳守卫 `[T+0xA8]` vs `CurrentFrame 0xA8ED84`（0x6D2556..65）→ `call 0x6D8B30`（0x6D267D/0x6D2778）重算六字段）。
- 生命周期表：F6_VIEWPORT.md:208-216（创建/每帧/显式跳转/销毁/读端五行；注意 W8-2 修正：+0xD80 族 ctor **装入非清零**（从 `[0xB0CD60..0xB0CD6C]` 四连拷贝 `0x6D1CE1..0x6D1D09`），「唯一业务写者 0x6D8B30」限运行期业务写——ERRATA_W8.md:71-75、W8_STATIC_LOCATE.md:170）。

### 1.2 五创建点（0x52C694/0x599D80/0x6853B4/0x687617/0x6BF84F）——VA 已有；阶段归属＝待核
- 创建点清单与字节现场：W8_STATIC_LOCATE.md:70；F6_VIEWPORT.md:112-113/:212；`_w8_f6_out.txt:210`（callers 全集恰 5）；reviews/_f6rev_probe_out.txt:122-192（五处 ctx 反汇编）；F6_review.md:38（0x687604 push 0xE18→0x687609 call 0x7C8E17 new→0x687617 ctor→0x687627 mov [0x887324],eax→0x68762C 装载链）。
- **游戏阶段归属（首启/读档/重开局）未标**：W8_STATIC_LOCATE.md:154（明写「未标——卡上时机行写不了」）；F6_VIEWPORT.md:254（§6-4 未逐一标注）；W8_STATIC_LOCATE.md:196（回件自曝未验要点含「5 创建点阶段归属」）。
- 既有材料中唯一定性旁证：card_00B0CE88.md:67（W4）——`0x6DA980` 直接 rel32 调用者恰 2 处 `0x599D90`/`0x6853C4`，上下文疑为「战局初始化/退出清场」，**触发条件与「是否每局必走」未验**（该卡自称「疑」，不升格）。台账 §601 区域未补此归属。

### 1.3 读数时机行——待核（被 1.2 阻塞）
- W8_STATIC_LOCATE.md:154：因五创建点阶段归属未标，「实例指针何时换绑、读数何时合法」的时机行**写不了**。
- 可用静态时机基线（不含换绑语义）：F6_VIEWPORT.md:205-206（0xB0CE30/34 仅视频模式/局面装载写、运行中不变；+0xB0/B4 每逻辑帧重算；+0xD80 族随 0x6D8B30 同步刷新）。

### 1.4 文档修正 3 处——已登记（落盘状态按 ERRATA 汇总件）
- W8-1 宿主区间：ERRATA_W8.md:62-66（0x4326B3 宿主 = 0x432690..0x4326BD，ret 4 @0x4326BB；落实=已落实，引用须联引 W8_STATIC_LOCATE.md:169）。
- W8-2 ctor 装入非清零：ERRATA_W8.md:71-75（落实=已落实，:59 承载）。
- W8-3 +0xD80 族证据链：ERRATA_W8.md:80（条目头；修订表述=联引 reviews/_f6rev_probe_out.txt:659-682，见 :176-177）。本会话未逐字复读 W8-3 的「汇总件落实」栏，如实登记。

### 1.5 F6 运行期未验边界——永久缺口
- W8_STATIC_LOCATE.md:155：运行期取值范围/帧间时序纯静态铁律**不可验**——「这是禁令造成的永久缺口，不是搜索缺口」；F6_VIEWPORT.md:256（运行期数值分布、帧间时序、+0xB0 实际取值范围不可验）。

## 2. F7（W8 判 UNLOCATED：W8_STATIC_LOCATE.md:87/:156；复核 PARTIAL 维持主判：台账 §593:8783-8798）

### 2.1 口径 A（入口累计代理 0xA8EC34）——字段已有，卡须带两点声明；差：无（W8_STATIC_LOCATE.md:157「声明是文字活」）
- 语义定谳：D-19 裁 A（限定版）——「索敌入口**调用累计**代理，无『每次工作量』信息」（台账 :6642；D19_RULING 经 A31 登记 GOAL_RE_CONTINUOUS.md:169）。
- 字节：恰 2 条绝对访存 `0x6F8DF3 R / 0x6F8E09 W`（inc 写回），早退 `0x6F8E41 ret 0xC` 在写回**之后**（F7_TARGETING.md:259-266；台账 §589:8399-8410 与 W4 卡一致）。
- 收紧口径：**是 `Greatest_Threat(0x6F8DF0)` 这一个函数的自增计数**，仍≠「索敌执行次数/成功数」（台账 §589:8408-8414；含早退：house 出局也计 1，F7_TARGETING.md:269-270）。
- 调用面：直调 2（0x445F68/0x4D9942）+ 14 处 `call [reg+0x3C4]` 派发点（五类 v[241] 各写不同函数，14 点不一定都到 GT；逐点 reg 归属未做——台账 §589:8416-8447/:8471-8472）。
- ra2render.dll 声明：`DllMain(DLL_PROCESS_ATTACH)` 无条件装 9 字节 Inline Hook（原 `83 EC 5C 8B 15 34 EC A8 00`→`E9 rel32`），跳板按 `interval`（默认 8）节流，被节流帧**整次跳过 0x6F8E04/0x6F8E09 自增** ⇒ DLL 在场时最多只统计 1/8 入口调用（台账 §573:7095-7099；card_00A8EC34.md:172-190，节流条件 `:184`）。
- 历史趟件污染普查：87 窗 clean 84 / hit 0，93 趟目录 clean 65 / hit 0，71 趟全部 gamemd.exe 直启 ⇒ 历史窗 0x6F8DF0 序言字节未被运行期改写（台账 §573:7101-7117）；边界不销：运行时刻模块表、enum_failed 2 趟、incomplete 5 趟未验（:7138-7141）。
- 部署态：ra2youli/ra2render.ini `[Gameplay]` 节 :151 起，TargetScanInterval 全部注释态（:155-157 实读），未启用覆盖；源树模板 ra2render/ra2render.ini:22-25 `TargetScanInterval=8`（与 card 所引 :22-25 一致）。具体某趟进程内 DLL 是否在场、实际 interval——运行期值，静态不可验（永久缺口，A3 边界同）。

### 2.2 口径 B（完成扫描数）——待核（最大缺口：无推导规格）
- W8_STATIC_LOCATE.md:158：F7 **没有给出 F8 §5 式的最小推导规格**（读哪些字段、什么顺序、代价多少条）；且任何「每帧/每 N 帧」频次句没有字节支撑（v[231] 调用方未追、0x6E962A switch 宿主身份未解）。
- F7_TARGETING.md:296-303：判定 UNLOCATED——「索敌执行计数（完成扫描数/成功锁定数/扫格工作量口径）无现成累加器」；四个门/计时器（frame%8 建筑回调门 0x4F8F8D、90 帧时长计时器 HouseClass+0x57A4..57AC、宏观派发门 frame%14 @0x6ECD40..63、状态门 [this+0x2B4]==0 @0x709918..20）无一以索敌执行为计数对象。
- 唯一实例级候选读量：`0x709932` 宿主帧戳 `this+0x4FC`（「该单位本轮是否已派发过索敌」候选），**语义未验**（F7_TARGETING.md:290）。

### 2.3 v[231] 调用方——待核（宿主身份已有、调用方未追）
- 宿主已有：v[231] 共享函数 0x709820，出现于 Techno/Unit/Foot/Infantry/Building 五张虚表 +0x39C；头两条写是 `this+0x4FC`/`this+0x180` 实例字段帧戳；真门是 `[this+0x2B4]==0` 状态门（0x709918..20），非帧限频（F7_TARGETING.md:185-196）。
- 调用方未追：F7_review.md:152-153（M3：v[231]（0x709820）自身的调用方 F7 未追，「每帧/每轮」频次措辞超前于字节）；W8_STATIC_LOCATE.md:102/:158 同口径；ERRATA_W8.md:100-103（W8-5 修订句明写「『每帧』频次无字节支撑（v[231] 调用方未追，F7_review.md M3）」）。
- F7_review.md:187-190（M2）：0x7E2640 结案为第六张虚表 @0x7E22A4 的 +0x39C（v[231]），同表 +0x3C4=0x4D9920（FOOT 包装），Foot 派生类（疑 AircraftClass，**类名未终证**）；并写「v[231] 共享实现 0x65A970 共被 7 张虚表引用」。⚠ 如实登记：0x65A970 在同复核件 §5 反例狩猎 4（:171-176）中是 **v[159]（+0x27C）槽**的共享实现——M2 句内 v[159]/v[231] 措辞不一致，本文不裁断，仅并存登记。
- 性质：静态可追的**搜索缺口**；其「被调频率」是运行期量（永久缺口）。

### 2.4 0x6E962A 宿主——待核
- 已有字节：0x6ECCE0（%14 门宿主）的唯一直接调用者 = 0x6E962A（`e8 b1 36 00 00`），一个 switch 型分发的 case 尾块（0x6E961E..0x6E9636；同族 case 还转发 0x6EC9A0/0x6ECE60），switch 宿主函数身份未深究（F7_TARGETING.md:180-181；F7_review.md:83；reviews/_f7rev_out.txt:33/:97）。
- 未解：0x6E962A 所在 switch 宿主函数（0x6E9xxx）的**身份**与它**被调的频率**（F7_TARGETING.md:350 §7-5）。宿主身份是搜索缺口；被调频率是运行期量（永久缺口）。

### 2.5 %14 宏观节律绑定约束——已有硬要求
- `N = int([AI]→PatrolScan × 900)`；PatrolScan 为 rules.ini [AI] 节 double 键（构造器默认 0.016→默认 N=14，**INI 可改**）；[Rules+0x1150] 写点恰 2 处：0x666E09/0x666E1A（构造器双写）+ 0x6739BF（fstp，LoadFromINI read-with-default）；capstone 对 fstp 不置 write 位的补判注记（W8_STATIC_LOCATE.md:101/:159/:175；ERRATA_W8.md:89-94；F7_review.md:110-125，键名串 `STR 0083d344 = b'PatrolScan'` @ reviews/_f7rev4_out.txt:3）。卡必须写「先读 PatrolScan」，**不得写死 14**（W8_STATIC_LOCATE.md:159）。
- PatrolScan 部署值＝未验（台账 §593:8818 自认「没有去 ini 里核」）。本会话静态核到文件级：ra2youli/ 下**无散置 rules.ini**（`find ra2youli -iname "*.ini"` 实跑仅 7 件：.ra2opt/orig/ddraw、ra2、RA2MD、BATTLEMD×2、ddraw、ra2render、Register），rules.ini 打包于 MIX（ra2md.mix/langmd.mix 等在目录实读清单内）未解包 ⇒ 部署值是**搜索缺口**（解 MIX 或运行期读可闭）；运行期实际生效值仍受运行期禁令约束（永久缺口）。

## 3. F8（W8 判 UNLOCATED：W8_STATIC_LOCATE.md:121/:160；推导路规格 F8_VISIBILITY.md §5 已有，五缺口如下；代理路 0xB0CE88 D-19 判未校准 W8_STATIC_LOCATE.md:161、台账 :6643）

推导路规格基线（已有）：字段 §5.1（F8_VISIBILITY.md:162-169，含一次性读 `[0x887324]`/视口原点/屏宽高/两 FPU 常量）、遍历顺序 §5.2（:171-180，5 层容器 `Items=[0x8A0364+L*0x18]`/`Count=[0x8A0370+L*0x18]`、坐标取法无统一偏移、投影 `0x6D2155..0x6D21CB`、边界 `[−360,W+360]×[−180,H+180]` 闭区间）、代价 §5.3（:184-185）、误差来源全列 §5.4（:188-198，9 条）。

### 3.1 ① 投影 FPU 常量数值——待核（搜索缺口）
- 地址与指令现场已有：`0x6D21E2 dc0d48cdb000 fmul qword [0xB0CD48]`、`0x6D21EC dc0538177e00 fadd qword [0x7E1738]`（F8_VISIBILITY.md:169/:178；_w8_f8_out.txt:323/:325）；第二读者 `0x53d48a fadd [0x7E1738]`（reviews/_f8rev_autopsy.txt:1995）。
- **数值（两个 8 字节 double）未读出**：「数值本轮未读出，标未验」（F8_VISIBILITY.md:169）；「规格阶段不需要，实现阶段必读」（:222；W8_STATIC_LOCATE.md:162①）。静态 u64 窗口读即可闭——本任务按铁律不新增探针，未读。

### 3.2 ② vtable[65]（+0x104）派生覆写全集——待核（只核 3 个直接覆写）
- 已核 3 个：0x422C70（vtable 0x7E3354 槽 65）/0x73B0B0（0x7F5C70）/0x749B20（0x7F6318），槽字节 u32 全 match、.rdata 引用 16 处（F8_VISIBILITY.md:93-95/:101-108；_w8_f8_out.txt:60/:66/:72；复核 F8_review.md:29 ✅）。
- 全集未逐一核：「只核 3 个直接覆写」（W8_STATIC_LOCATE.md:162②；F8_VISIBILITY.md:224-225 未验 5；三处覆写前置条件 `[ecx+0x184]`/`[edi+0x418]`/cell 标志 +0x12C&0x10 见 :180）。
- W10 增量：渲染簇内确有槽 65 虚调用 `0x006D909E call dword ptr [edx+0x104]` → `0x73B0B0` → `0x73B132 call 0x5F4B10`（W10_COSTBOUND_RECHECK/T2_C2.md:158-178/:201；W10_COSTBOUND.md:101）——A39「簇内 0 调用」系 E8 直扫误报的勘误；虚调用点全镜像 7 处（W8_STATIC_LOCATE.md:135；F8_VISIBILITY.md §1.1，引用须带 .text 范围注记 ERRATA_W8.md:163-170 W8-12）。仍非派生覆写全集。

### 3.3 ③ 三张 vtable 类名——待核（未终证）
- F8_VISIBILITY.md:219-220：「三个 vtable（0x7E3354/0x7F5C70/0x7F6318）的类名——无符号表；『AnimClass/UnitClass』名号采信 W3 §6.1，本轮以『槽 65 恰含对应函数头』佐证，**未做 RTTI 全链解析**」；W8_STATIC_LOCATE.md:162③「类名未终证」。
- W10 复用「UnitClass::vftable 首地址 0x007F5C70」名号（T2_C2.md:170-171/:201），其亲验清单（:197-202）未含对这三张表本身的 RTTI 读取 ⇒ 不构成终证。F7_review.md:188-189 的 0x7E2640 Foot 派生类「疑 AircraftClass，类名未终证」同口径。RTTI 全链解析静态可做——搜索缺口。

### 3.4 ④ 裁剪通过口径——未声明（口径不定，数就不定）
- W8_STATIC_LOCATE.md:162④：卡必须先声明「裁剪通过」口径，三点：含不含 **Smudge 例外**（RTTI==0x18 `0x5F4B7A cmp 0x18` 屏内仍画，F8_VISIBILITY.md:195）；含不含 **NeedsRedraw 早退对象**（`[obj+0x80]=0` 在 0x5F4B3C 直接早退**根本不进 IsVisible**、被读路径 0x5F4B56 清零、单帧内单调漂移，:190/:176）；**抑制位 `[0xA8ED6B]≠0`** 或 hwnd=0 时裁剪检查整体跳过、全员绘制、通过数无意义（:196/:175；字节 _w8_f8_out.txt:199 `0x5f4b13 mov al,[0xa8ed6b]`；写点 88 refs / W=3：reviews/_f6rev_probe_out.txt:695）。W10 旁证：`[0xa8ed6b]!=0` 时最短成功路径 65 条指令（T2_C2.md:42）；槽 11 WhatAmI 对特殊图元二次判定（:38）。
- 口径声明本身是文字活，但**选定前「数就不定」**（W8_STATIC_LOCATE.md:162④ 原文）；三个运行期量（抑制位值、逐对象 NeedsRedraw 状态、Smudge 实际绘制走向）是永久缺口。

### 3.5 ⑤ ~7 万条/帧外部复现代价——估算已有；接受度是决策项
- F8_VISIBILITY.md:184-185：每对象 ≈ 35–40 条外部等价操作（坐标 3 dword + 投影 ~25–30 条含 5 条 FPU + 边界 4 比较 + 早退标志 ~4 读）；按 W3 v3a 慢窗地面层 **1832 对象**（台账 :5828=`l3_1101v3a` 慢窗 1832；Q1_C2_RENDER §3.2）≈ **~7 万条/帧**，外加每类一次槽 18 解析。W8_STATIC_LOCATE.md:129 同口径；W10 复核另提 5.7 万→13.5 万条差距的物理来源待指认（reviews/T2_review.md:173）。
- 1832 是**单窗语料观测值**；运行期帧间对象数分布不可验（永久缺口）；「代价接受度」是 N-11 决策项（W8_STATIC_LOCATE.md:162⑤）。

## 4. 运行期未验边界汇总（纯静态铁律下不可验项；「永久」= 运行期才可定，「搜索」= 静态可闭、既有材料未做）

| # | 项 | 性质 | 依据 |
|---|---|---|---|
| P1 | F6 运行期取值范围/帧间时序/+0xB0 实际值 | 永久 | W8_STATIC_LOCATE.md:155（明写永久缺口）；F6_VIEWPORT.md:256 |
| P2 | 五创建点哪次运行实际走到（首启/读档/重开局的运行期确认） | 永久（宿主函数身份静态可追部分属搜索缺口 S1） | W8_STATIC_LOCATE.md:154；F6_VIEWPORT.md:254 |
| P3 | 口径 A 运行期：0xA8EC34 实际计数、单趟增量、具体趟 DLL 是否在场与实际 interval | 永久（历史窗已普查 84/87 clean，边界 :7138-7141 不销） | 台账 §573:7099/:7107-7117/:7138-7141 |
| P4 | v[231] 宿主与 0x6E962A switch 宿主的被调频率 | 永久（身份/调用方属搜索缺口 S2/S3） | F7_TARGETING.md:350；F7_review.md:152-153 |
| P5 | PatrolScan 部署值与运行期生效值 | 部署值=搜索缺口（MIX 未解包）；生效值=永久 | 台账 §593:8818；本会话 find 实跑 0 散置 rules.ini |
| P6 | F8 FPU 常量数值 | 搜索（静态 u64 窗口读可闭；本任务未执行） | F8_VISIBILITY.md:169/:222 |
| P7 | vtable[65] 派生覆写全集 | 搜索 | W8_STATIC_LOCATE.md:162②；F8_VISIBILITY.md:224 |
| P8 | 三张 vtable 类名（RTTI 全链） | 搜索 | F8_VISIBILITY.md:219-220 |
| P9 | 裁剪口径三个运行期量（抑制位值/NeedsRedraw 逐帧态/Smudge 走向） | 永久（口径声明=文字活） | F8_VISIBILITY.md:190/:195/:196 |
| P10 | ~7 万条/帧的运行期帧间对象数分布 | 永久（条数估算基线已有） | F8_VISIBILITY.md:184-185；台账 :5828 |
| P11 | F7 口径 B 推导规格（字段/顺序/代价） | 搜索（静态可推导、未做） | W8_STATIC_LOCATE.md:158 |

登记两条引用疵点（不裁断）：(a) GOAL_RE_CONTINUOUS.md:162（A24）写「F7/F8 仍 UNLOCATED（§601）」，台账 §601（:9418-9508）实读内容为 W9 收官单步件订正，未含 F7/F8 UNLOCATED 表述；F7 UNLOCATED 维持的实际台账承载为 §593:8787-8798，F8 为 W8_STATIC_LOCATE.md:121 与 D20_B_VISIBILITY_GAP（GOAL_RE_CONTINUOUS.md:176 A38）。(b) F7_review.md M2 与该件 §5 反例狩猎 4 对 0x65A970 的槽位表述不一致（v[231] vs v[159]），并存登记。

## 5. N-9 验收判级（NEXT_STEPS_20261106.md:89 原文对照）

- **REPORT_COMPLETE 成立**：本文对 F6 五创建点阶段/读数时机、F7 三锚点（0xA8EC34/v[231]/0x6E962A）、F8 常量/槽65覆写全集/类名/裁剪口径/代价界逐项给出状态（已有/待核/不可验）、来源（文件:行）、缺口与运行期未验边界（§1-§4），并区分入口代理（口径 A）与完成扫描数（口径 B）。
- **SPEC_CONFIRMED 不成立**（缺任一项即 PARTIAL 档，本节逐项列缺）：所选计数（口径 B 完成扫描数）**无推导规格**（W8_STATIC_LOCATE.md:158）；F8 推导路**覆盖范围因口径④未声明而不定**（W8_STATIC_LOCATE.md:162④）；F6/整体**读数时机行因创建点阶段未标而写不了**（W8_STATIC_LOCATE.md:154）；既有判定系「回件×复核合并」**不构成对规格的第三次独立重验**（ERRATA_W8.md:182-184）。允许按验收原文送 N-11 申请技术裁决。
- 本文未写「已定位」「已证不存在」（F6 LOCATED / UNLOCATED 均为对 W8 判定的转述并带联引），未生成采样候选，未补猜任何运行期值，未新增采样代码，未启动任何 .exe，未 commit/push。

—— 产出：lead/static_spec_n9_20261107/（_n9_fingerprint.py、_n9_anchor_scan.py、_n9_anchor_scan_out.txt、_n9_wide_scan.py、_n9_wide_scan_out.txt、本文）。
