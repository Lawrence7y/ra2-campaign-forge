# P11 残余开口 b · 12 个无门派发站语义身份 · 纯静态命名回件

- 执行：静态发站命名员（GLM 子代理）· 日期 2026-11-08
- 任务源：`lead/spec_static_closure_20261108/STATIC_GAP_CLOSURE.md:128`（P11 未闭部分 b：「12 个无门派发站语义身份未逐一命名（F7T:357 自报未验）」）
- 纪律：零真机 / 零采样代码 / 零注入 / 未读活进程；只读既有件；唯一写域 = `lead/p11_stations_20261108/`；未 commit、未 push。全部 Python 以 `python -I -X utf8` + 绝对路径实跑；指纹 hashlib 实算。

## 0. 绑定（本会话 hashlib 实算）

**被核对象 SHA256 = 73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476，字节数 = 4825360**（`ra2youli/gamemd.exe`，磁盘镜像只读；与 STATIC_GAP_CLOSURE.md:143 四方同值；本会话两次独立实算同值）。

| 引用件 | SHA256 | 字节数 |
|---|---|---|
| lead/spec_static_closure_20261108/STATIC_GAP_CLOSURE.md | e0c00683fb23b0b3777d71639f3d7d265208057969073e53fd2b7195d0c3e1f7 | 28648 |
| lead/spec_static_closure_20261108/_sc_scan_out.txt | c715898ee1339fa6fdd303a2e93a75f7fec4d92ff725d5f2e6251d76a001a075 | 44255 |
| lead/re_line_20261105/W8_STATIC_LOCATE/F7_TARGETING.md | 406816fcf6abe4245ea8c597242e3ae32f5d58fd8b6fbd1a0605f1a84afa8f79 | 25628 |
| lead/re_line_20261105/W8_STATIC_LOCATE/_w8_f7_out.txt | 81966c23fe1983ec42e5010ac014fce746dbb56aebad5da7fbce0c1f74b8d733 | 81105 |
| docs/re/house_team_ai_update.md | f7c3e8d7e64d3bf46113ff85fc643eafebe816e6d33c88563420b98eadb52233 | 35583 |
| docs/re/anchor_claims.txt | de153a3377c9278608368debabee07284b76564e768d80628b89ae2dd6d831bc | 35514 |
| docs/re/targeting_spatial.md | 628b58217d3e107ed6f832b545b9419d1fcf5d6626e2c9a49e3c67f8387bff4e | 31726 |
| lead/GOAL_THREE_TARGETS_20261018.md | 2baa0de45d4125549262eb595d7518c9ce99efeee120384bf640cded8a933ede | 759518 |
| lead/ROUND_SUBAGENT_LOG_TRIGOAL_20261017.md | 06a419ae5e788b4c08a64c7875c35067e3858083e2a4cbf554debf4095c45e0a | 1528751 |
| lead/re_line_20261105/W3_COSTBOUND/sections/Q1_C3C4_PHYS_TARGET.md | 0555b7b1331267dda8483e0aad876415371817f4ef021a995090b730b3f8946f | 26457 |
| lead/re_line_20261105/W4_FIELD_SPEC/sections/card_00A8EC34.md | 6cde19c881ab09f6f7b1246fe75dbc41d7538d0dbba59c9b528db9b35d821b46 | 31647 |

写域产出（本件与前缀 _p11_ 五件）：_p11_stations_scan.py（16629 B）、_p11_stations_out.txt（34806 B）、_p11_supplement.py（6275 B）、_p11_supplement_out.txt（12308 B）、_p11_supplement2.py / _p11_supplement2_out.txt（哈希见 §5）。

## 1. 任务对象抄录（逐条带行号，本会话实读）

- **14 虚派发站清单**（F7_TARGETING.md:129-130，探针 C2 段原始行 _w8_f7_out.txt:60-74）：`0x414B24, 0x414B64, 0x417481, 0x4D4314, 0x4D4686, 0x4D49A3, 0x4D4E3E, 0x4DE056, 0x50D1D2, 0x51F382, 0x6ECE06, 0x6ED15E, 0x6F0253, 0x709932`（`call [reg+0x3C4]` = v[241] Greatest_Threat 槽）。
- **门分类**（F7_TARGETING.md:244-246）：宏观门 1 = `0x6ECE06`（宿主 0x6ECCE0，`CurrentFrame % 14`，计数器 0xA8ED84，周期=构造器常量 14，F7T:158-183）；状态门 1 = `0x709932`（宿主 0x709820 = v[231] 五虚表共享，`[this+0x2B4]==0` 判空门，F7T:185-196）；**无门 12** = 其余 12 站（本轮对象）。
- **既有对照名**（口径 B 已有）：两直调包装 Building 0x445F00 / Foot 0x4D9920（F7T:124-125）；Unit/Infantry 包装 0x743190/0x51E140（F7T:131-132）；`0x4D4280`「v[241] 派发宿主之一，[esi+0xBC] 状态机 switch，无帧门」（F7T:241-242），上游链 `UnitClass::v[151] @0x740B10 → 0x4D4280`（F7T:136-138；C3C4 Q1_C3C4_PHYS_TARGET.md:106；card_00A8EC34.md:300）。
- **启发式窗口**（_w8_f7_out.txt:879-896，F7 自报起点为启发式、未做 CFG 级确认——F7T:352）。

## 2. 方法（本会话实跑）

1. **_p11_stations_scan.py**（只读解析 + capstone 5.0.7）：PE 节表口径照抄 _sc_scan.py:16-34；RTTI 口径照抄 _sc_p7.py:55-92（TD 名串基址=串址-8；COL=TD 引用位-12 且 sig==0；vtable 基=COL 指针位+4；vslot=条目偏移/4——与 +0x39C=231/+0x3C4=241/+0x25C=151 既有口径一致）。产出：1214 张 RTTI vtable（与 STATIC_GAP_CLOSURE.md:107 的「1214 张候选」独立同值）、6692 个虚表锚定函数起点、全 .text E8/E9 直调普查、逐站前后指令上下文、字符串立即数线索。
2. **真起点解析（PASS2）**：候选 = .rdata/.data 全 dword 引用值 ∪ E8/E9 目标 ∪ 前置 ≥2 字节 90/CC 填充起点；线性流验证 + 硬边界（途中 ret-imm / int3 / C3+填充 ⇒ 拒绝）。
3. **自校准（通过）**：两个已知门站必须解出已知宿主——`0x6ECE06→0x6ECCE0`（_p11_stations_out.txt:44，且唯一直调者 0x6E962A 与 F7T:180-181 同值，:635）、`0x709932→0x709820`（:45）。校准不过则全部结论作废。
4. **_p11_supplement.py / _p11_supplement2.py**：锚点性质（前置填充字节）、序言反汇编、跳表 0x6E9F74 全 65 条目、字符串读取、EB/E9 直入边全扫、vtable 成员位与槽位算术。

## 3. 逐站命名结论（三档制）

### 第①档 · 有静态证据支撑的语义身份 —— 12/12

判定基准：宿主起点被**独立结构**锚定（RTTI vtable dword 恰等于起点 / 既有材料同名同址 / 函数内调试字符串），非仅启发式边界。各站证据链（行号均为本会话实跑输出）：

| # | 站点 | 宿主起点 | 语义身份 | 证据链 |
|---|---|---|---|---|
| 1 | 0x414B24 | 0x414A80 | **AircraftClass v[138] 方法内的 GT 派发站**（实参 push 0x40；前置游戏模式全局门 `mov eax,[0xA8B238]; test; je 0x414b33`） | RTTI：vtable 0x7E22A4 条目 0x7E24CC 恰=0x414A80（_p11_stations_out.txt:52-53；COL/TD 直读 `.?AVAircraftClass@@` 于 _p11_supplement2_out.txt §3b）；0xA8B238 既有名 G_GAMEMODE（GOAL_THREE_TARGETS_20261018.md:3688）/ADDR_SESSION_GAMEMODE（ROUND_SUBAGENT_LOG_TRIGOAL_20261017.md:5121）；上下文 _p11_stations_out.txt:20-43 |
| 2 | 0x414B64 | 0x414A80 | **同上（AircraftClass v[138]）**，第二派发点（实参 push 0 + 栈上坐标结构），随后 `push eax; call [edi+0x3C8]`=v[242] 链 | _p11_stations_out.txt:99-100、:104-139 |
| 3 | 0x4D4314 | 0x4D4280 | **FootClass/InfantryClass 共享 v[151] 状态机（0x4D4280）** 内派发点，实参 push 2；唯一直调者 0x740B49 ∈ UnitClass v[151] 函数体 0x740B10 | RTTI：0x7E8EF0（Foot）/0x7EB2B4（Infantry）恰=0x4D4280 slot151（_p11_stations_out.txt:200-201）；直调者 :202 与 F7T:137 链吻合；F7T:241-242 既有名「v[241] 派发宿主之一」 |
| 4 | 0x4D4686 | 0x4D4280 | 同上状态机内派发点（实参 push 2，前置对 `[ecx]` vslot18 调用取参） | _p11_stations_out.txt:251-253、:255-293 |
| 5 | 0x4D49A3 | 0x4D4280 | 同上状态机内第三派发点（实参 push 2）；同帧结构（`add esp,0x90` 尾，:319） | _p11_stations_out.txt:300-302、:304-349 |
| 6 | 0x4D4E3E | 0x4D4DC0 | **FootClass v[132] 共享实现（0x4D4DC0）** 内派发点（实参 push 1；`[esi+0x68E]` 标志门→GT→v[242]→清 0x68E）；上游：UnitClass v[132] 0x7447A0 尾跳 thunk + InfantryClass v[266] 0x51F538 直调 | RTTI：0x7E8EA4 恰=0x4D4DC0 slot132（_p11_stations_out.txt:356-358）；thunk `jmp 0x4d4dc0` + func_slots UnitClass vslot132（_p11_supplement_out.txt:248-271）；直调 :359；体内调 0x5657A0=MapClass::TryGetCellAt（:362；既有名 targeting_spatial.md:383/:535） |
| 7 | 0x4DE056 | 0x4DDF90 | **Aircraft/Foot/Infantry/Unit 四类共享 v[150] 方法（0x4DDF90）** 内派发点（实参 push 0；开头 `mov ecx,0x87F7E8; call 0x565730` + `call 0x70C610`×2；清 `[esi+0x688]`） | RTTI：四表条目 0x7E24FC/0x7E8EEC/0x7EB2B0/0x7F5EC8 恰=0x4DDF90 slot150（_p11_stations_out.txt:411-413）；0x87F7E8 既有名「全局单例（运行期 vtable 0x7F0344，构造两次）」（ROUND_SUBAGENT_LOG_TRIGOAL_20261017.md:6869/:6893-6913）；0 E8 直调者=纯虚可达（:414） |
| 8 | 0x51F382 | 0x51F330 | **InfantryClass v[266] 方法（0x51F330）** 内派发点；0 直调者（纯虚可达） | RTTI：0x7EB480 恰=0x51F330 slot266（_p11_stations_out.txt:517-519） |
| 9 | 0x50D1D2 | 0x50D170 | **PickTargetByType（既有名）内派发站**：遍历 TeamArray（Items 0x8B40EC / Count 0x8B40F8）按 `[team+0x2C]`=Owner 过滤 → `call 0x6EC3D0` → 结果作 GT 的 this（实参 push ebx，前置 vslot18 调用）；上游 = AI_TryFireSW 0x5098F0 五处 call | 既有名同址：docs/re/house_team_ai_update.md:74「0x0050D170 PickTargetByType → 0x006EC3D0（扫 TeamArray）」、:97/:208（0x6E9050 脚本步进树）；本会话实证：五直调者全在 [0x5098F0,0x509F00)（_p11_stations_out.txt:466；_p11_supplement2_out.txt §4 末行 True）、0x5098F0 序言读 0xA8B238+House+0x1EC（_p11_supplement2_out.txt §4，+0x1EC=Defeated 既有口径 house_team_ai_update.md §2.2）、TeamArray/Owner 偏移（同件 §2.1/§2.3） |
| 10 | 0x6ED15E | 0x6ED090 | **TeamClass::AI（0x6E9050，既有名）脚本动作跳表 entry[0] 处理器**：case0 块 0x6E9783..0x6E979B 唯一 call 下游；读 TeamClass +0x3C/+0x54(FirstUnit)/+0x24(Type)（既有偏移口径 house_team_ai_update.md §2.3），TeamType+0xF7 字节入参；GT 结果回喂 TeamClass::AI（0x6ED167 `call 0x6e9050`，与既有「含自递归」:97 一致） | 10×90 填充起点（_p11_supplement_out.txt:132）；唯一直调者 0x6E978F 落在跳表 entry[0]=0x6E9783 的 case 块内（同件 :166-178 + 全 65 条目表 :214-216）；宿主体 call 0x6E9050（_p11_stations_out.txt:535） |
| 11 | 0x6F0253 | 0x6F0130 | **TeamClass::AI 脚本动作跳表 entry[56] 处理器**（0x6F0130）：case56 块 0x6E9DC7..0x6E9DDF 唯一 call 下游；读 `[ecx+0x54]`=FirstUnit、TeamType+0xF7 字节入参，形态与 #10 同构 | 10×90 填充起点（_p11_supplement_out.txt:147）；唯一直调者 0x6E9DD3 ∈ entry[56]=0x6E9DC7 块（同件 :189-213 + :214-216）；上下文 _p11_stations_out.txt:586-626 |
| 12 | 0x417481 | 0x416D50 | **AircraftClass v[139]（0x4166C0）条件尾跳进入的 [esi+0xBC] MISSION_MOVE 状态机**（case0 打调试日志「Do_MISSION_MOVE_Carryall - VALIDATE_LZ」/「…NavCom == NULL」→ 空桩 0x4068E0；GT 站位于其跳表 0x4172E4 之后的公共段，实参 push 2） | v[139]：.rdata 唯一引用位 0x7E24D0，(0x7E24D0−0x7E22A4)/4=139，且基表 RTTI 直读 `.?AVAircraftClass@@`（_p11_supplement2_out.txt §3/§3b）；stub 序言 `mov eax,[ecx+0x6C4]; mov dl,[eax+0xDFC]; test; je→0x4166E0 / fall→jmp 0x416D50`（同件 §4 + _p11_supplement_out.txt:32-40）；字符串实读（_p11_supplement2_out.txt §1）；状态机跳表 0x4172E4 四条目 = 0x416D6B/0x416F29/0x416FA3/0x41715E，entry[0]=0x416D6B 正是 VALIDATE_LZ 日志块（_p11_supplement2_out.txt §3c + _p11_supplement_out.txt:7-26）；空桩 0x4068E0 既有名（anchor_claims.txt:58「Release debug stub」） |

**namedCount = 12，unnamedCount = 0**（第②档候选 0、第③档无法命名 0）。

### 三档纪律说明（为何 12 站全部入①档）

- 12 站宿主起点均被**独立于启发式**的结构锚定：8 站由 RTTI vtable dword 精确等于起点（vtable 条目指向函数起点，同时证明起点与类归属）；1 站（0x50D170）与既有材料**同名同址**且其上游/下游/遍历对象逐字节吻合该材料的树；2 站（0x6ED090/0x6F0130）由「唯一直调者落在字节级验证的跳表 case 块内 + 10×90 填充起点 + TeamClass 既有偏移读数」三重锚定；1 站（0x416D50）由函数体内两条调试字符串 + 上游 v[139] RTTI 锚定。
- 残余不确定性（如实）：0x6ED090/0x6F0130 与 0x416D50 未做 F7T:352 所述「CFG 级确认」（本轮验证=线性流硬边界+锚点交叉，自校准两已知站通过）；此点不降档但保留记录。

## 4. 命名之外仍留白（不补猜，不升格）

1. **门分类未重裁**：12 站「无门」沿用 F7T:244-246 与探针 D 段（_w8_f7_out.txt:879-896）窗口级三类特征普查；本轮未在宿主全函数尺度重跑该普查（宿主比启发式窗口大，如 0x4D4280 跨 ≥0x709 B、含 ret 后块）。口径 B 若要写「覆盖范围」栏，建议以本轮宿主边界重跑一次特征普查（另立任务，未做）。
2. **GT 实参语义未命名**：各站实参形态（0x40 / 2 / 1 / 0 / ebx / vslot18 返回值）在既有材料中无语义名，本件只记录字节形态。
3. **字段/槽位语义未命名**：`[this+0x2B4]`（F7T:345 未验项 1 原样保留）、`type+0xDFC`、`TeamType+0xF7`、`TeamClass+0x3C`、`[ecx+0x6C4]`、vslot18(+0x48)、v[242](+0x3C8)、v[125](+0x1F4)、Aircraft v[138]/v[139] 的虚表槽语义名——既有材料未见，留白。
4. **TeamClass::AI 脚本动作 0 号 / 56 号的助记名**：既有材料只载「Action 49（0x31，Success）」（house_team_ai_update.md:385）；0/56 号动作名未找到，本件只给表下标定位，不猜名。
5. **运行期可达性**：各站宿主「是否在某局内实际触发」= 运行期量（P2/P3 同族），本件不判。P11 整项仍为「部分闭口」，本件只填充 :128 开口 b 的「命名」部分，不宣布 P11 状态变化、不改档。
6. 0x414A80 宿主内 `mov eax,[0xA8B238]` 的门语义：既有名 G_GAMEMODE/ADDR_SESSION_GAMEMODE 两说并存（GOAL:3688 / ROUND_SUBAGENT_LOG:5121），本件并存登记不裁断（同 STATIC_GAP_CLOSURE.md:118 的并存纪律）。

## 5. 实跑命令记录（均可复演）

```
python -I -X utf8 "D:\Project\ra2-campaign-forge\lead\p11_stations_20261108\_p11_stations_scan.py" > ...\​_p11_stations_out.txt   # EXIT=0, RUN TIME 20.6s（文件尾行）
python -I -X utf8 "D:\Project\ra2-campaign-forge\lead\p11_stations_20261108\_p11_supplement.py"   > ...\​_p11_supplement_out.txt   # EXIT=0
python -I -X utf8 "D:\Project\ra2-campaign-forge\lead\p11_stations_20261108\_p11_supplement2.py"  > ...\​_p11_supplement2_out.txt  # EXIT=0
```
（路径中 `\​_` 为排版防折行，实际为 `\_`。三脚本零写盘、零进程 API、零网络；输出由 shell 重定向进写域。）

写域产出指纹（本会话 hashlib 实算）：
_p11_stations_naming.md = c280d67376294a3842ac11eabd32085d796b93974447aa60e0acab8230d03f57 / 14689 B（§3 表行修订后字节数以最终文件为准）；
_p11_stations_scan.py = bbb273dd3dae4c99846ee073b6c8494a847626cd9e25390c0f01c2dc1268c4a9 / 16629 B；
_p11_stations_out.txt = ca3b4f484e22e5a2bfd45598cdc42d323e6e0e11fecd55cb3a31e95f1c7819db / 34806 B；
_p11_supplement.py = 803c54077166cf651a0d92204d431c5208a2909c5c165f9fa864edceb2125117 / 6275 B；
_p11_supplement_out.txt = e689d8004491657bd64d24db85bda011733ada19dc583ef92558f7922f91bf84 / 12308 B；
_p11_supplement2.py = 21a8cada12296bcbb16451302fcf650ce741b74f9c36eb21bb20e372b3997c2c / 4162 B；
_p11_supplement2_out.txt = 99ecf73c174c3189524e5b9e00705ecd1ecb161cd61b0c51548a8727ccc0fb3a / 2004 B。

## 6. 写域产出清单

| 件 | 说明 |
|---|---|
| _p11_stations_naming.md | 本回件 |
| _p11_stations_scan.py / _p11_stations_out.txt | 主扫描（PASS1 窗口 + PASS2 真起点 + 逐站归属/上下文/直调者） |
| _p11_supplement.py / _p11_supplement_out.txt | 锚点性质/序言/跳表 65 条目/直调者邻域 |
| _p11_supplement2.py / _p11_supplement2_out.txt | 字符串/EB·E9 全扫/vtable 成员位/RTTI 直读/序言 |
