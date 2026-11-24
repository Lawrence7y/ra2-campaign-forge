# P11 残余开口 b · 12 个无门派发站语义身份命名 · 交付报告（命名回件 + 复核回件合并登记）

- 执行：命名报告撰写员（P11 命名任务的交付件撰写岗）· 日期 2026-11-08
- 任务源：`lead/spec_static_closure_20261108/STATIC_GAP_CLOSURE.md:128`（P11 未闭部分 b：「12 个无门派发站语义身份未逐一命名（F7T:357 自报未验）」→ 口径 B「覆盖范围」栏写不全，:126-129 原文）
- 上游件：命名回件 `_p11_stations_naming.md`（被核对象 SHA256 = 6722ddadf0e251861ca9e91dc40880e34f94fcb1fbbaea010c7695972bf65370，字节数 = 15454，本会话 hashlib 实算同值，见 §5）；复核回件 verdict = **partial**（任务材料所载，ranCommands=41）→ 按交付纪律标 **unconfirmed**。
- 纪律：纯静态（文件镜像只读）；零真机 / 零采样代码 / 零注入 / 未读活进程；只读既有件；唯一写域 = `lead/p11_stations_20261108/`；未 commit、未 push；不升格 W8 否定命题；不补猜。

## 1 目的与边界

**目的**：把 P11 命名子任务的两段产出——①命名回件（12 个无门派发站的语义身份）与②复核回件（verdict=partial 及其崩点）——合并为一份交付报告，逐站带证据行号登记，并如实记录复核修正，供 STATIC_GAP_CLOSURE.md:128 开口 b 与口径 B「覆盖范围」栏引用。

**三档区分纪律**（本件全篇执行）：
- 第①档 = 有静态证据支撑的语义身份（宿主起点被独立于启发式的结构锚定：RTTI vtable dword 恰等于起点 / 既有材料同名同址 / 字节级验证的跳表 case 块 + 填充起点 / 函数内调试字符串）；
- 第②档 = 仅候选（只有启发式窗口或形态相似性，无独立结构锚）；
- 第③档 = 无法命名（无任何可复核锚点）。
只有第①档计入 namedCount；②③档一律计入 unnamedCount。

**边界（如实）**：
- 本件为纯静态文件镜像推断，不含任何运行期判读；各站宿主「是否在某局内实际触发」不判。
- 命名回件与复核回件的命令未逐条重演；本会话亲手重算的部分仅限 §5 明列的载决性子集（哈希绑定、0x6E9F74 跳表、派发器字节、两处 call/jmp 目标），其余以「转录自命名稿/复核回件，行号本会话实读」标注。
- 禁语自查：本件不含任务禁语清单所列两类断言用语（定位类完成时断言、否定存在类断言，全文 grep=0，见文末自查记录）；不生成采样候选；不补猜运行期值。

## 2 12 个无名发站清单与已知有门派发对照

**上游口径**：`call [reg+0x3C4]`（v[241] Greatest_Threat 槽）恰 **14** 个派发站——F7_TARGETING.md:128-130（14 站清单）；_w8_f7_out.txt:60-74（探针 C2 原始行，count=14，:61-74 逐行列出）；STATIC_GAP_CLOSURE.md:124（派发拓扑同口径）。

**门分类**（F7_TARGETING.md:244-246 实读）：直接调用者（2 个包装）零帧限频；14 个派发点中 1 个有 `CurrentFrame % 14` 宏观门（计数器 0xA8ED84，周期=构造器常量 14）、1 个有 `[this+0x2B4]==0` 状态门、**其余 12 个无门**。

**对照表**（14 站逐条带原始行号；D 段窗口三类特征取自 _w8_f7_out.txt:879-896）：

| # | 站点 | 门 | D 段窗口（_w8_f7_out.txt 行） | 特征（test-and-imm7 / absdwordWR / CurrentFrame-read） |
|---|---|---|---|---|
| 1 | 0x6ECE06 | 宏观门（宿主 0x6ECCE0，CurrentFrame %14） | :889-890 | 0 / 0 / **1**（CFR 006ecd59） |
| 2 | 0x709932 | 状态门（宿主 0x709820，[this+0x2B4]==0） | :893-896 | 0 / 0 / **3** |
| 3 | 0x414B24 | **无门（本轮对象）** | :879 | 0 / 0 / 0 |
| 4 | 0x414B64 | **无门（本轮对象）** | :880 | 0 / 0 / 0 |
| 5 | 0x417481 | **无门（本轮对象）** | :881 | 0 / 0 / 0 |
| 6 | 0x4D4314 | **无门（本轮对象）** | :882 | 0 / 0 / 0 |
| 7 | 0x4D4686 | **无门（本轮对象）** | :883 | 0 / 0 / 0 |
| 8 | 0x4D49A3 | **无门（本轮对象）** | :884 | 0 / 0 / 0 |
| 9 | 0x4D4E3E | **无门（本轮对象）** | :885 | 0 / 0 / 0 |
| 10 | 0x4DE056 | **无门（本轮对象）** | :886 | 0 / 0 / 0 |
| 11 | 0x50D1D2 | **无门（本轮对象）** | :887 | 0 / 0 / 0 |
| 12 | 0x51F382 | **无门（本轮对象）** | :888 | 0 / 0 / 0 |
| 13 | 0x6ED15E | **无门（本轮对象）** | :891 | 0 / 0 / 0 |
| 14 | 0x6F0253 | **无门（本轮对象）** | :892 | 0 / 0 / 0 |

门分类沿用 F7T:244-246 与探针 D 段的**窗口级**三类特征普查，本轮未在 12 个宿主的全函数尺度重跑（naming 稿 §4-1 自承；F7T:352 同为窗口级口径）——见 §6 未验项。

## 3 逐站静态归属推断（上下文 / 宿主起点 / vtable·RTTI / 字符串线索）

方法（转录自命名稿 §2，探针输出本会话实读）：PASS2 真起点解析（候选 = .rdata/.data dword 引用 ∪ E8/E9 目标 ∪ ≥2 字节 90/CC 填充起点；线性流验证 + ret-imm/int3/C3+填充硬边界）；RTTI 口径 TD 名串基址=串址-8、COL=TD 引用位-12 且 sig==0、vtable 基=COL 指针位+4；自校准 = 两已知门站必须解出已知宿主（**通过**：0x6ECE06→0x6ECCE0、0x709932→0x709820，_p11_stations_out.txt:44-45）。PASS2 全 12 站起点汇总 _p11_stations_out.txt:14-45。

| # | 站点 | 上下文（本会话实读） | 宿主起点 | 归属证据（vtable/RTTI/字符串/直调者/跳表） |
|---|---|---|---|---|
| 1 | 0x414B24 | 前置游戏模式全局门 `mov eax,[0xA8B238]; test; je 0x414b33`（_p11_stations_out.txt:61-64），`push 0x40`（:74）后 `call [edi+0x3C4]`（:78） | 0x414A80（:14/:51） | vtable 0x7E22A4 条目 0x7E24CC 恰=0x414A80 slot138，TD `.?AVAircraftClass@@`（:52-53；_p11_supplement2_out.txt:21-25）；直调者 0=纯虚可达（:54）；ret 后段 0x414AE5 被宿主头 `jne 0x414ae5` 命中（_verify_reach3_out.txt:49/:4） |
| 2 | 0x414B64 | 同宿主第二派发点：`push 0`（0x414B45，:87）+ 栈上坐标结构（:85-92）；邻域内 0x414B2D `call [edi+0x3C8]`=v[242]（:81、:107） | 0x414A80（:15/:98） | 同上 slot138（:99-100）；直调者 0（:101） |
| 3 | 0x4D4314 | `6A 02 push 2` 实参（F7_TARGETING.md:138 既有精确化） | 0x4D4280（:17/:199） | vtable 0x7E8EF0(Foot)/0x7EB2B4(Infantry) 恰=slot151，TD 双名（:200-201）；唯一直调者 0x740B49（:202）∈ UnitClass v[151] 0x740B10（_p11_supplement_out.txt:272-274；链 F7_TARGETING.md:136-138 既有）；F7T:241-242 既有名「v[241] 派发宿主之一，[esi+0xBC] 状态机 switch，无帧门」；0x4D42EC 表条目命中（_verify_reach3_out.txt:24） |
| 4 | 0x4D4686 | 前置浮点比较链 `fcomp [ecx+0x1708]; fnstsw; test ah,0x41; jne`（_p11_stations_out.txt:256-259）；实参形态见命名稿 §3 行 4 | 0x4D4280（:18/:250） | 同上 slot151（:251-253）；0x4D45A2 direct=True（_verify_reach3_out.txt:26） |
| 5 | 0x4D49A3 | 同帧结构 `add esp,0x90` 尾（:319） | 0x4D4280（:19/:299） | 同上 slot151（:300-302）；0x4D498A 表条目命中（_verify_reach3_out.txt:31） |
| 6 | 0x4D4E3E | `[esi+0x68E]` 标志门→GT→v[242]→清 0x68E（命名稿 §3 行 6） | 0x4D4DC0（:20/:38/:355） | vtable 0x7E8EA4 恰=slot132（:356-358）；直调者 2：0x51F538(call)+0x7447A0(jmp)（:359；_p11_supplement2_out.txt:12/:15）；0x7447A0=`jmp 0x4d4dc0` thunk，func_slots UnitClass vslot132、rvals 0x7F5E80（_p11_supplement_out.txt:248-271）；体内调 0x5657A0=MapClass::TryGetCellAt（:362；既有名 docs/re/targeting_spatial.md:383/:535） |
| 7 | 0x4DE056 | 站前 `call [eax+0x48]`(vslot18) ×2、清 [esi+0x688]（_p11_stations_out.txt:437-441）；锚点 0x4DE023 `mov ecx,0x87F7E8`、0x4DE028 `call 0x565730`、0x4DE030 `call 0x70C610` 位于宿主体内 case 分发后的分支体（:424-428）——**非函数开头**（复核指摘，本会话实读坐实：起点 0x4DDF90，锚点在 +0x93 处） | 0x4DDF90（:21/:39/:410） | 四类 vtable 0x7E24FC/0x7E8EEC/0x7EB2B0/0x7F5EC8 恰=slot150，TD 四名（:411-413）；直调者 0=纯虚可达（:414）；0x87F7E8 既有名「全局单例，构造两次，运行期 vtable 0x7F0344」（ROUND_SUBAGENT_LOG_TRIGOAL_20261017.md:6869/:6893，既有材料转录未独立验） |
| 8 | 0x51F382 | 窗口极简（_p11_stations_out.txt:515-523） | 0x51F330（:23/:41/:516） | vtable 0x7EB480 恰=slot266 `.?AVInfantryClass@@`（:517-519）；直调者 0（:520） |
| 9 | 0x50D1D2 | 遍历 TeamArray：宿主序言 `mov esi,[0x8b40f8]`（Count，_p11_supplement_out.txt:64）、`mov edx,[0x8b40ec]`（Items，:69）；TeamClass+0x2C=Owner 过滤（既有口径 docs/re/house_team_ai_update.md:164；Items/Count :122/:127）；TeamClass+0x54=FirstUnit（:165） | 0x50D170（:22/:40/:463） | **既有名同址**：house_team_ai_update.md:74「0x0050D170 PickTargetByType → 0x006EC3D0（扫 TeamArray）」；直调者 5 全 call、落 [0x5098F0,0x509F00)（_p11_stations_out.txt:466；_p11_supplement2_out.txt:7-11/:49 True）；上游 0x5098F0 序言读 0xA8B238+[esi+0x1EC]（_p11_supplement2_out.txt:40-46；+0x1EC=Defeated 既有口径 house §2.2:138） |
| 10 | 0x6ED15E | 宿主序言读 [ebp+0x3C]（TeamClass 向量）与 [ebp+0x54]=FirstUnit（_p11_supplement_out.txt:142-145；house §2.3:158/:165） | 0x6ED090（:24/:42/:529） | 10×90 填充起点（_p11_supplement_out.txt:132）；唯一直调者 0x6E978F（_p11_stations_out.txt:532）落在跳表 **entry[0]** case 块 0x6E9783..0x6E979B 内（_p11_supplement_out.txt:166-178；全 65 条目 :215 entry[0]=0x6e9783）；宿主体内 `call 0x6E9050`=TeamClass::AI（_p11_stations_out.txt:535；本会话探针重算 0x6ED167 `e8 e4 be ff ff`→call 0x6E9050；house:97「33 个调用点，含自递归」既有口径吻合） |
| 11 | 0x6F0253 | 站前读 [ecx+0x24]=TeamType、[TeamType+0xF7]（_p11_stations_out.txt:604-605；house:162 +0x24=Type）；宿主起点字节 `83 ec 20 53 55 56 8b 71 54`=读 [ecx+0x54]=FirstUnit（本会话探针 + _verify_stations_out.txt:38；house:165） | 0x6F0130（:25/:43/:580） | 10×90 填充起点（_p11_supplement_out.txt:147）；唯一直调者 0x6E9DD3（_p11_stations_out.txt:583）落在跳表 **entry[57]** case 块 [0x6E9DC7,0x6E9DE0) 内（_p11_supplement_out.txt:189-213 块内 `call 0x6f0130` :207；:215 entry[57]=0x6e9dc7；本会话探针重算 0x6E9DD3 `e8 58 63 00 00`→call 0x6F0130，∈entry[57] 块 True / ∈entry[56] 块 False）。**★更正**：命名稿 :59/:74 写「entry[56] / case56 块 / Action 0/56」系 off-by-one（0x6E9F74 表 0-based，见 §5 崩点）；正确语义身份 = entry[57]（动作 57）处理器 |
| 12 | 0x417481 | GT 站位于 [esi+0xBC] 状态机跳表 0x4172E4（条目 0x416D6B/0x416F29/0x416FA3/0x41715E，_p11_supplement2_out.txt:27）之后的公共段；case0 打调试字符串 0x817F18「Do_MISSION_MOVE_Carryall - VALIDATE_LZ」/ 0x817EDC「…NavCom == NULL」→ 空桩 0x4068E0（_p11_supplement_out.txt:18-26；字符串实读 _p11_supplement2_out.txt:3-4；0x4068E0 既有名 anchor_claims.txt:58「Release debug stub」） | 0x416D50（:16/:34） | 上游 0x4166C0=AircraftClass v[139]：.rdata 唯一引用位 0x7E24D0、(0x7E24D0−0x7E22A4)/4=139、基表 RTTI `.?AVAircraftClass@@`（_p11_supplement2_out.txt:18-25）；条件尾跳序言 `mov eax,[ecx+0x6C4]; mov dl,[eax+0xDFC]; test; je 0x4166D5 / fall→jmp`（:30-35；本会话探针重算 0x4166D0 `e9 7b 06 00 00`→jmp 0x416D50）；0x416D50 序言 `mov eax,[esi+0xBC]; cmp eax,3; ja; jmp [eax*4+0x4172E4]`（_p11_supplement_out.txt:8-17）；ret 后段 0x417422 被跳表 0x4176DC 条目 2 命中（_verify_reach2_out.txt:11；_verify_reach3_out.txt:20） |

## 4 三档命名结论

**第①档（有静态证据支撑的语义身份）—— 12 站**（命名稿 §3 判 12/12，_p11_stations_naming.md:43/:62；锚型分布 naming:66：8 站 RTTI vtable dword 精确锚定 + 1 站既有同名同址 + 2 站跳表 case 块唯一直调者 + 10×90 填充起点 + 1 站函数内调试字符串 + 上游 RTTI）。

复核修正后的登记口径（本件采信）：
- 11 个 vtable dword 及槽位被复核独立重算 **11/11 全对**（_verify_stations_out.txt:21-31），本会话抽查同值；
- 0x50D170 同名同址站的上游/下游/遍历对象与既有材料树吻合（§3 行 9）；
- 站 11（0x6F0253）的**具体编号由 entry[56] 更正为 entry[57]（动作 57）**——其语义归属「TeamClass::AI 脚本动作跳表 case 处理器」不因编号错而倒（复核回件原话要点；本会话探针独立坐实）；
- 站 10/11/12（0x6ED090 / 0x6F0130 / 0x416D50）未做 F7T:352 所述 CFG 级确认（naming:67 自承），**不降档但如实留白**。

**第②档（仅候选）—— 0 站。**
**第③档（无法命名）—— 0 站。**

**总判**：命名稿「12/12 第①档」的全称判断，按复核 verdict=partial 不作为无瑕疵定论采信，标 **unconfirmed**（理由：1 站编号证据错已更正 + 3 站 CFG 级未确认；见 §5）。

## 5 复核回件（含 SHA256 加字节数绑定）+ 12 站状态汇总表

### 5.1 绑定（本会话 hashlib 实算，探针 `_p11_report_probe.py`）

**被核对象 SHA256 = 6722ddadf0e251861ca9e91dc40880e34f94fcb1fbbaea010c7695972bf65370，字节数 = 15454**（`_p11_stations_naming.md`；与复核回件 sha256Line 同值）。
编排方盘点 4 件重算 4/4 MATCH：STATIC_GAP_CLOSURE.md = e0c00683…/28648、_sc_scan_out.txt = c715898e…/44255、PERF_REPAIR_HANDOFF.md = 7a617a43…/29619、W8_STATIC_LOCATE.md = 20e4eeac…/26485。
被核镜像 ra2youli/gamemd.exe = 73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476 / 4825360 B（与 STATIC_GAP_CLOSURE.md:143 同值）。

### 5.2 复核判定：**partial → 按交付纪律标 unconfirmed**

复核回件（任务材料所载）ranCommands=41。以下通过面为转录 + 本会话抽查/重算坐实：

**通过面**：
1. **清单**：STATIC_GAP_CLOSURE.md:128 开口原文、F7T:129-130 的 14 站清单、_w8_f7_out.txt:60-74（count=14）、_sc_scan_out.txt:54-55（VAL v241 站点=14 expect14，转录）、F7T:244-246 门分类四处一致；命名稿 §1 抄录无错无漏（复核判定；本会话实读 :128/:129-130/:244-246/:60-74 吻合）。
2. **证据链主体**：11 个 vtable dword 及槽位独立重算 11/11 全对（_verify_stations_out.txt:21-31；本会话探针抽查同值）；命名稿所引探针行号逐一实读吻合（本会话抽读约 20 处全对上，见 §3 各行）；0x740B49∈UnitClass v[151] 0x740B10、0x7447A0 thunk、5 直调者区间、0x6ED167 call 0x6E9050（本会话重算）、0x4166C0 stub 序言、两调试字符串、0x5657A0 既有名、house §2.1/§2.3 偏移均独立实算/实读吻合。
3. **PASS2 线性流方法**：复核初查发现 6 站与声称宿主间跨 ret，但经条件跳转/跳表重算，每个 ret 后段起点均被宿主体内 jne/je/跳表命中（0x414AE5、0x4D42EC/0x4D498A、0x417422 等，_verify_reach3_out.txt:3-41、_verify_reach2_out.txt:7-14）——非把相邻独立函数误并；CFG 级确认未做一节 naming:67 自承为如实留白。
4. **禁语与纪律**：全写域 7 件对任务禁语及同根变体（定位类断言、否定存在类断言、认定/确认类强断言用词）grep =0、三套探针 import 仅 struct/hashlib/time/capstone、无进程 API/无 gamemd.exe 启动（复核判定，转录）；:75 明写 P11 仍「部分闭口」不升格。
5. **写域**：引用 11 件 + 盘点 4 件指纹 hashlib 全 OK、gamemd.exe 同值（本会话重算 4+1 件同值）；12 件只读保护件 mtime 早于写域产出、HEAD 仍 2657458、0 commit/0 push（复核判定，转录；本会话未改任何只读件、未 commit）。

**崩点（故不判 confirmed）——确凿事实错误（off-by-one）**：
命名稿 :59/:74 及其任务 what 字段称 0x6F0130 是跳表「entry[56]」处理器、「case56 块 0x6E9DC7..0x6E9DDF」、「0 号 / 56 号动作名未找到」。复核从镜像重算 0x6E9F74 全 65 条目：**entry[56]=0x6E9DAE、entry[57]=0x6E9DC7**；唯一直调者 0x6E9DD3 落在 **entry[57]** 块 [0x6E9DC7,0x6E9DE0) 内；派发器 0x6E945B `jmp [eax*4+0x6E9F74]` + 0x6E944B `cmp eax,0x40` 为 0-based 索引，Action 49（0x31，Success，house_team_ai_update.md:385 既有口径）对应 entry[49]=0x6E9CE1（_verify_stations_out.txt:16-18、_verify_caseblocks_out.txt:6/:17/:19-20/:25）。
**本会话独立重算坐实**（`_p11_report_probe.py` 输出）：entry[49]=0x6E9CE1、entry[56]=0x6E9DAE、entry[57]=0x6E9DC7；0x6E944B 字节 `83 f8 40`、0x6E945B 字节 `ff 24 85 74 9f 6e 00`；0x6E9DD3 `e8 58 63 00 00`→call 0x6F0130，∈entry[57] 块 True / ∈entry[56] 块 False。故正确编号为 **entry[57]（动作 57）**；语义身份本身不倒，但「56 号」这个具体编号错，且命名稿 :74 把它与「Action 0/56 助记名留白」绑定，污染留白记录（本件已在 §3 行 11 与 §6 更正）。另注：_p11_supplement2_out.txt:14 的「case56-handler」是探针脚本的硬编码标签、非计算事实，其原始 E8/E9 边数据无错。

**次要瑕疵**：
1. 命名稿 :88 写自身指纹 c280d673…/14689 B，实为 6722ddad…/15454 B（本会话 hashlib 重算坐实；同行虽有「字节数以最终文件为准」注记，表值仍陈旧）。
2. 命名稿 :55 对 0x4DDF90「开头 mov ecx,0x87F7E8; call 0x565730 + call 0x70C610×2」措辞不精确——实读锚点在宿主起点 0x4DDF90 之后 +0x93 处的 case 分支体内 0x4DE023/0x4DE028/0x4DE030（_p11_stations_out.txt:424-428；证据行 :415-418 本身属实）。
3. **本会话新发现（复核未列）**：命名稿 §2 把「1214 张候选」引到 STATIC_GAP_CLOSURE.md:107，实读该值在 **:106**（:107 是 P7 槽 65 结果行）；1214 张 vtable 计数本身两处独立同值（_p11_stations_out.txt:7「RTTI VTABLES 1214」）。

**口径提示（非事实错误）**：namedCount=12/unnamedCount=0/②③档 0 的总量与上游 14−2 一致、12 站逐站有可复核证据行，未见凑数；但站 10/11/12 未做 CFG 级确认且站 11 编号证据曾错——按默认怀疑不宜判「12/12 第①档铁定无瑕疵」。本件采信：12 站语义身份均成立（站 11 编号按 entry[57] 登记），其中 3 站带「CFG 级未确认」留白。

### 5.3 12 站状态汇总表

| # | 站点 | 语义身份（按复核修正后口径） | 复核状态 | 档位 |
|---|---|---|---|---|
| 1 | 0x414B24 | AircraftClass v[138]（0x414A80）内 GT 派发站，前置 [0xA8B238] 游戏模式全局门 | vtable 0x7E24CC slot138 重算 OK | ① |
| 2 | 0x414B64 | 同上宿主第二派发点（实参 push 0+坐标结构，v[242] 链邻接） | 同上 | ① |
| 3 | 0x4D4314 | Foot/Infantry 共享 v[151] 状态机（0x4D4280，F7T:241 既有名）内派发点 | 双表 slot151 重算 OK；唯一直调者 0x740B49 链闭合 | ① |
| 4 | 0x4D4686 | 同上状态机内派发点（前置浮点比较链） | 同上 | ① |
| 5 | 0x4D49A3 | 同上状态机内第三派发点 | 同上 | ① |
| 6 | 0x4D4E3E | FootClass v[132] 共享实现（0x4D4DC0）内派发点；上游 Unit v[132] thunk + Infantry 直调 | 0x7E8EA4 slot132 重算 OK；0x7447A0 thunk 重算 OK | ① |
| 7 | 0x4DE056 | Aircraft/Foot/Infantry/Unit 四类共享 v[150]（0x4DDF90）内派发点 | 四表 slot150 重算 OK；「开头」措辞已按实读修正 | ① |
| 8 | 0x51F382 | InfantryClass v[266]（0x51F330）内派发点 | 0x7EB480 slot266 重算 OK | ① |
| 9 | 0x50D1D2 | PickTargetByType（既有名同址，house:74）内派发站；上游 AI_TryFireSW 0x5098F0 五处 call | 5 直调者区间/序言/偏移实读吻合 | ① |
| 10 | 0x6ED15E | TeamClass::AI（0x6E9050，既有名）脚本动作跳表 **entry[0]** 处理器（0x6ED090）；GT 结果回喂自递归 | case0 块/唯一直调者重算 OK；CFG 级确认未做（未验） | ①（留白） |
| 11 | 0x6F0253 | 同表 **entry[57]（动作 57）** 处理器（0x6F0130）——命名稿原写 entry[56]，off-by-one 已更正 | 重算坐实 entry[57]；CFG 级确认未做（未验） | ①（编号更正+留白） |
| 12 | 0x417481 | AircraftClass v[139]（0x4166C0）条件尾跳进入的 [esi+0xBC] MISSION_MOVE 状态机（0x416D50，调试字符串锚定） | 0x7E24D0 slot139 重算 OK；CFG 级确认未做（未验） | ①（留白） |

**namedCount = 12，unnamedCount = 0**（第②档 0、第③档 0）——总量与上游 14 − 2 有门站一致。

### 5.4 本会话实跑记录（可复演）

```
python -I -X utf8 "D:\Project\ra2-campaign-forge\lead\p11_stations_20261108\_p11_report_probe.py"
grep -n -E "PickTargetByType|8B40EC|Action 49|0x6E9050|§2\.[123]|…偏移行" docs/re/house_team_ai_update.md   # 既有名/偏移行定位
```
探针输出要点已引于 §5.1/§5.2；其余为 Read 工具实读（STATIC_GAP_CLOSURE.md:100-179、F7_TARGETING.md:120-144/238-262/348-362、_w8_f7_out.txt:55-79/875-901、docs/re 四件定向行、_p11_stations_out.txt:1-19/20-55/55-94/95-110/195-210/250-260/295-320/350-365/405-470/510-540/580-640、_p11_supplement_out.txt:1-70/123-152/160-219/245-274、_p11_supplement2_out.txt 全文、_verify_stations_out.txt/_verify_caseblocks_out.txt/_verify_reach2_out.txt/_verify_reach3_out.txt 全文、命名稿全文）。

## 6 结论

1. **计数**：namedCount = **12**，unnamedCount = **0**；第②档（仅候选）0、第③档（无法命名）0。12 个无门派发站（发站）在纯静态口径下全部取得第①档语义身份；总量与上游 14 派发站 − 2 有门站自洽。
2. **对 P11「覆盖范围」栏的影响**：STATIC_GAP_CLOSURE.md:128 开口 b 阻塞的正是口径 B「覆盖范围」栏（:128「写不全」）——本轮 12 站命名使该栏的**静态身份部分可写**（12/12 站身份 + 宿主起点 + 证据行，见 §5.3 表）。但 P11 整项维持「**部分闭口**」不升格（STATIC_GAP_CLOSURE.md:120/:130/:176 既有判级；命名稿 :75 同口径），理由：开口 a（环行程次数=运行期量，:127）与开口 c（DLL 节流在场=运行期，:129）不因命名闭合，「读数时机」栏仍缺（:176）。
3. **更正记录（随本件入账）**：站 11 = 0x6F0130 为 TeamClass::AI 脚本动作跳表 **entry[57]（动作 57）** 处理器；命名稿 :59/:74 的「entry[56]/case56/Action 0/56」为 off-by-one 笔误，引用者应以本件为准。命名稿 :88 陈旧自指纹、:55「开头」措辞、§2「:107→应为 :106」三处引用瑕疵一并登记（§5.2）。
4. **缺什么材料（既有材料未见，未验，不补猜）**：
   - Action 0 与 Action 57 的助记名：既有材料只载 Action 49=0x31 Success（house_team_ai_update.md:385）；0/57 号动作名无出处。
   - 门分类重裁：12 站「无门」沿用 F7T:244-246 与 D 段窗口级特征（_w8_f7_out.txt:879-896）；全宿主尺度（如 0x4D4280 跨 ≥0x709 B、含 ret 后块）的特征重跑未做（命名稿 §4-1，另立任务）。
   - CFG 级确认：站 10/11/12 未做 F7T:352 口径的 CFG 级确认（命名稿 :67 自承；复核口径提示同）。
   - GT 实参语义：各站实参字节形态（0x40 / 2 / 1 / 0 / ebx / vslot18 返回值）无语义名（命名稿 §4-2）。
   - 字段/槽位语义名：[this+0x2B4]、type+0xDFC、TeamType+0xF7、TeamClass+0x3C、[ecx+0x6C4]、vslot18(+0x48)、v[242](+0x3C8)、v[125](+0x1F4)、Aircraft v[138]/v[139] 槽语义——既有材料未见（命名稿 §4-3；其中 +0x24/+0x2C/+0x54 三个 TeamClass 偏移**有**既有名 house:162/:164/:165，其余未验）。
   - 0xA8B238 两说并存不裁断：G_GAMEMODE（GOAL_THREE_TARGETS_20261018.md:3688）/ ADDR_SESSION_GAMEMODE（ROUND_SUBAGENT_LOG_TRIGOAL_20261017.md:5121），并存登记（命名稿 §4-6，同 STATIC_GAP_CLOSURE.md:118 并存纪律）。
   - 0x87F7E8 运行期 vtable 0x7F0344、构造两次：既有材料转录（ROUND:6869/:6893），本会话未独立验。
5. **未验项汇总**：CFG 级确认（3 站）；运行期可达性（12 站全部不判）；复核 41 条命令未逐条重演（本会话只重算 §5.4 明列的载决性子集）；门分类全宿主尺度重裁；0xA8B238/0x87F7E8 的语义裁断。
6. **不补猜声明**：上述留白一律不猜名、不猜值、不判运行期、不升格 W8 否定命题；本件不宣布 P11 状态变化、不改档、不 commit、不 push；未生成任何采样候选；交付自查：全文对任务禁语及同根变体（定位类断言、否定存在类断言、认定/确认类强断言用词）grep=0。
