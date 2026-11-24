# _sc_CLOSURE_20261108 · Q3 八项静态缺口闭口回件（静态只读检索）

```
任务     = PERF_REPAIR_HANDOFF.md:161 问题卡 Q3（S1/S2/S3/S4/P6/P7/P8/P11 均静态可闭、既有材料未做）
           → 本任务：只做静态只读检索，尝试闭口这 8 项
执行者   = 静态缺口闭口员（动态工作流子代理「静态闭口员·GLM」）
时刻     = 2026-11-08
铁律     = 零真机（未启动任何 .exe/.dll、未 taskkill、未读活进程内存）；
           零采样代码（未写 hook/MiniDump/SuspendThread/StackWalk/注入/ctypes/OpenProcess/ReadProcessMemory）；
           只读既有件（ra2youli/**、out/re_work/**、lead/GOAL_*、lead/PENDING_DECISIONS.md、
           lead/re_line_20261105/**、lead/static_spec_n9_20261107/**、lead/perf_repair_n11_20261108/** 未改一字）；
           唯一写域 = lead/spec_static_closure_20261108/；不 commit、不 push；
           Python 一律 python -I -X utf8 + 绝对路径；指纹一律 hashlib。
被核对象 = gamemd.exe（磁盘镜像只读）：SHA256 = 73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476，字节数 = 4825360
           （_sc_scan_out.txt:1-2 实算；与 W8:43 四方同值一致）
编排方指纹复验（本会话第一条命令，hashlib 实算）：
  STATIC_COUNT_SPEC.md    = 5b933fe2…3ccdb9 / 32281 B   MATCH
  PERF_REPAIR_HANDOFF.md  = 7a617a43…796e0   / 29619 B   MATCH
  W8_STATIC_LOCATE.md     = 20e4eeac…406262  / 26485 B   MATCH
  ERRATA_W8.md            = 660a9ecec…a4f05  / 28443 B   MATCH
产出件（全部在本写域，hashlib 实算）：
  _sc_scan.py      23880 B a034a6182f7a3f6e00fab8305aa456e7ad8575489549d85472f711032d11c91d
  _sc_scan_out.txt 44255 B c715898ee1339fa6fdd303a2e93a75f7fec4d92ff725d5f2e6251d76a001a075
  _sc_p7.py         6501 B fa2e4466e60e7bf455be873cf329cdcceb8b658c491e018a9cc4bc1401968cc9
  _sc_p7_out.txt    2836 B 23f52d3f0d227b8dac72e14128441b4b3aca948431a49ac3a04e1c835054c8e1
  _sc_mix.py        5308 B ae7a7adf27608525f9e370224759f06200935e4fdb41f8b063fdb4bf408d71e2
  _sc_mix_out.txt  25212 B ef8bb2ab468c478353d1b5d6c62e8eb4ad10fb16f26cb8a66634bbffabe8256e
  本件             _sc_CLOSURE_20261108.md
用语纪律 = 全文不出现任务禁令的两类中文断言用语；不对 W8 的 F7/F8 否定命题作任何升格；
           入口代理（口径 A）与完成扫描数（口径 B）全文分开登记。
行号约定 = 「_scan:nnn」= lead/spec_static_closure_20261108/_sc_scan_out.txt；
           「_p7:nnn」= …\_sc_p7_out.txt；「_mix:nnn」= …\_sc_mix_out.txt；
           N-9 / W8 / F6V / F7T / F8V / PERF / ERRATA 为编排方指纹所锚定的四件与 W8 三回件（缩写同 N-9:9-12）。
```

## 1 八项定义（逐项抄录自 N-9 §6.2 :198-208 原文表，本会话实读）

| # | N-9 原文（:199-208 逐行） | N-9 所载依据 |
|---|---|---|
| S1 | F6 五创建点宿主函数身份（→ 阶段归属标定的前置） | W8:154；F6V:254 |
| S2 | v[231]（0x709820）调用方追链 | F7_review.md:152-153（M3）；W8:102/:158 |
| S3 | 0x6E962A 所在 switch 宿主身份 | F7T:350（§7-5） |
| S4 | PatrolScan 部署值（需解 MIX） | LEDGER:8818；N-9 find：ra2youli 全树 ini 10 件、rules*.ini 0 件 |
| P6 | F8 两个 FPU 常量数值（静态 u64 窗口读可闭） | F8V:169/:222 |
| P7 | vtable[65] 派生覆写全集 | W8:162②；F8V:224 |
| P8 | 三张 vtable 类名（RTTI 全链） | F8V:219-220 |
| P11 | F7 口径 B（完成扫描数）最小推导规格（字段/顺序/代价） | W8:158 |

（N-9:218 SPEC_PARTIAL 四缺与本八项的关系、PERF:139 未验项转录，均实读核对过。）

## 2 逐项结果

### 2.1 P6 —— 部分闭口（两个常量一闭一开，开口为结构性）

**[0x7E1738] = 0.5（闭）。**
- 文件映射证据：_scan:85（.rdata 文件映射域 [0x7E1000,0x812000) 覆盖 0x7E1738）；
- 数值：_scan:86 `qword=0x3FE0000000000000 double=0.5 raw=000000000000e03f`（python -I -X utf8 内联 struct 读文件镜像，绝对路径）；
- 写点普查：_scan:87-99 该地址解码访存 647 条，全部为 FPU 读（fmul/fadd/fsub/fcomp，无写形态；样例 _scan:88-99；非 fmul/fadd 的 fsub/fcomp 样例见 _scan 输出 grep「0x7e1738」段）；
- 同段校验：_scan:24 `qword(0x7E27F8)==900.0` OK（F7T:165 已知值），证明本会话 VA→文件偏移映射在该段正确。
- 语义注记：F8V:178 的 `fadd [0x7E1738]` 在 `call 0x7C5F00`（double→int）之前，+0.5 与 F7T:166 同型——本回件只给数值与访问形态，不做取整语义的补猜。

**[0xB0CD48]（结构性开口；上游前提修正登记见 §4-a）。**
- 文件映射证据：_scan:58（.data 文件映射域 [0x812000,0x87E000)，0xB0CD48 在其上的零初始化域）——**该地址不在文件镜像内，静态 u64 窗口读无值可读**；
- 全部访存（_scan:59-77）：12 条解码指令 = 唯一写者 `0x6D1BDD fstp qword [0xb0cd48]` + 11 条 `fmul qword [0xb0cd48]` 读（含 F8V:178 所记 0x6D21E2 在内）；
- 写者宿主函数（_scan:763-774，函数头 0x6D1BB0，前邻 0x6D1BA8..0x6D1BAF nop 填充，尾 0x6D1BE3 ret）：
  `fld qword [0x7E1728]` → `fdiv qword [0xB0CD78]` → `fstp qword [0xB0CE18]` → `call 0x4CACB0`（实参 [0xB0CD88]、[0xB0CD8C]）→ `fmul qword [0xB0CE18]` → `fstp qword [0xB0CD48]`；
- 常量 [0x7E1728] = 60.0（0x404E000000000000，内联实读）；其余输入 [0xB0CD78]/[0xB0CD88]/[0xB0CD8C]/0x4CACB0 返回值全部为运行期初始化/运行期计算量——即 `[0xB0CD48] = ret(0x4CACB0,[0xB0CD88],[0xB0CD8C]) × (60.0 / [0xB0CD78])`，数值依赖运行期状态；
- 结构性原因：**值由运行期代码计算写入 BSS，静态文件镜像不含该值**；对其输入的继续追写（0xB0CD78/88/8C 的写者链）属另立搜索任务，本任务未展开（§5 未做项）。

### 2.2 P7 —— 闭口（文件镜像内 vtable[65] 槽位全集；方法与边界见 §5）

- 枚举方法：RTTI 全链（TypeDescriptor→COL→vftable；本镜像 COL 存绝对 VA，_p7 脚本按此约定）+ vtable 长度过滤（长度<66 的短表无槽65，滤除 1193/1214 张候选，_p7:4）；
- 槽65 == 基实现 0x5F4B10 的 vftable 恰 **16** 张（_p7:6-21）：AircraftClass(0x7E22A4)、BuildingLightClass(0x7E3AD0)、BulletClass(0x7E46E4)、FootClass(0x7E8C94)、InfantryClass(0x7EB058)、IsometricTileClass(0x7EC258)、MissionClass(0x7EDCC0)、**ObjectClass(0x7EF060)**、OverlayClass(0x7EF3D4)、ParticleClass(0x7EF954)、ParticleSystemClass(0x7EFB9C)、RadioClass(0x7F0508)、SmudgeClass(0x7F32FC)、TechnoClass(0x7F4960)、VeinholeMonsterClass(0x7F66A8)、WaveClass(0x7F6BF4)；
- 槽65 ≠ 基实现的覆写恰 **5** 个函数、各被 1 张 vftable 引用（_p7:23-31）：
  | 覆写函数 | vftable | RTTI 类名 |
  |---|---|---|
  | 0x422C70 | 0x7E3354 | AnimClass（=F8V:93 已知） |
  | **0x43CEA0** | 0x7E3EBC | **BuildingClass**（新增） |
  | **0x71CC50** | 0x7F522C | **TerrainClass**（新增；即 F8V:224 所记 W3「0x71CD7B 一带」所在函数体，0x71CD7B ∈ [0x71CC50, 0x71CD84) 尾段） |
  | 0x73B0B0 | 0x7F5C70 | UnitClass（=F8V:94 已知） |
  | 0x749B20 | 0x7F6318 | VoxelAnimClass（=F8V:95 已知，类名本轮 RTTI 得名） |
- 完备性对账（_p7:35-42）：全文件（4 对齐 dword）内 0x5F4B10 恰 16 处、5 个覆写值各恰 1 处，全部落 .rdata，位置与 RTTI 枚举的槽位**一一对应（差集=空）**；与 F8_review.md:38「dword 0x5F4B10=16 处全在 .rdata」独立同值；
- 5 个覆写均无 E8 直调者（_p7:24/26/28/30/32 `E8直调=[]`）——与 F8 的「经 vtable[65] 虚调用」口径一致（F8V:110-111 七处虚调用站点由本会话独立复现：_scan:46-53 恰 7 处，含 F8V 所列全集合）；
- 五维对账：本项是「覆写全集」清点，字段=槽位值+类名，覆盖范围=文件镜像 RTTI 可枚举 vftable ∪ 全文件 dword 对账，代价=枚举零反汇编（纯字节解析 0.3s，_p7 尾行）；遍历顺序/读数时机不适用于本项性质。
- 边界（如实）：运行期对 vtable 的改写（如注入体）不在文件镜像范围——该残余与 F8 §4 的注入残余同口径，不构成对本枚举的否定。

### 2.3 P8 —— 闭口（三张 vtable 类名，RTTI 全链）

_scan:777-779：
- 0x7E3354 → COL 0x7FBA60 → **`.?AVAnimClass@@`**
- 0x7F5C70 → COL 0x80CC68 → **`.?AVUnitClass@@`**
- 0x7F6318 → COL 0x80CDF8 → **`.?AVVoxelAnimClass@@`**
方法校验（同链同脚本）：_scan:773-774 前——vt=0x7F4348→`.?AVTactical@@`、vt=0x7E85D4→`.?AVDSurface@@`（后者=F6V:86 已知值，RTTI VAL 行 OK）；_p7:43-47 五表重列同值。F8V:219-220 的「名号采信 W3、未做 RTTI 全链」由此补齐：AnimClass/UnitClass 名号与 RTTI 一致；第三表获得本名 VoxelAnimClass（W8 回件原文未给名）。
（方法注记：本镜像 COL 的 pTypeDescriptor 字段存绝对 VA 而非 RVA——由 Tactical/DSurface 两条已知链实证，脚本按此约定并在 _p7 内联校验。）

### 2.4 S1 —— 闭口（五创建点宿主函数身份；「阶段归属」仍开放且不在 S1 定义内）

方法：capstone 线性解码全 .text（_scan:36-40，1,394,120 条/resync 66，与 W8:44 同数）→ 指令边界级回扫（≥3 字节填充边界 → 最近 call 目标 → 最近 ret/jmp 后边界三级启发，序言形态校验，全部原始字节随输出可复核）。
| 创建点 | 宿主（_scan 行） | 序言首 8B | E8 直调者 |
|---|---|---|---|
| 0x52C694 | **0x52BA60**（:794，call 目标级） | b8 302f0000 e8…（__chkstk 型栈检查） | 0x48CCCF（:810） |
| 0x599D80 | **0x599650**（:813） | 55 8bec 83e4f8… | 0x598A74（:829） |
| 0x6853B4 | **0x6851F0**（:832） | a1 30b2a800 53…（mov eax,[0xA8B230]） | 0x599A4B / 0x67E739 / 0x686B65（:847） |
| 0x687617 | **0x686B20**（:850） | 81ec 64010000 5355… | 0x599A56 / 0x686845（:866） |
| 0x6BF84F | **0x6BF740**（:869） | 8bc1 c74004000000… | 0x6BC5D6（:874） |
内部一致性校验（同表同法）：0x887324 的 11 处 W 点宿主（_scan:876-887）与创建点宿主逐一对齐（0x52C69B/BC→0x52BA60、0x599D8B→0x599650、0x6853BF→0x6851F0、0x687627→0x686B20），且 **0x6D1E1E→0x6D1C20 = ctor 本身**（自检通过）；0x599D90/0x6853C4 两处 `call 0x6DA980 清场例程` 落在宿主 0x599650/0x6851F0 体内（_scan:817-819/:844-845），与 card_00B0CE88.md:67 的「恰 2 处直接调用者」独立同值；宿主间调用链 0x599650→(0x599A4B)→0x6851F0、0x686B20→(0x686B65)→0x6851F0、0x67E730→(0x67E739)→0x6851F0 随 :847/:866 输出可见。
如实登记：宿主起点为启发式判定（方法与 F7T:155/F8V:89 同类），每个宿主的序言/直调者/体内调用原始字节均随 _scan 输出在案可复核；「首启/读档/重开局」阶段归属 = W8:154/F6V:254 的下游事项，本回件**不写**（F6V:212 装载链与 F6V:204 的 0x68762C 装载现场已在既有材料，本回件未新增阶段断言）。

### 2.5 S2 —— 闭口（v[231] 调用方枚举 + 宿主身份；「被调频率」=P4 永久缺口不在此闭）

- 直接 E8/E9 → 0x709820：**0 处**（_scan:890）；
- 虚派发 `call [reg+0x39C]` 恰 **6** 站（_scan:891-897）：0x4D5392、0x4D6F06、0x4DF402、0x4DF491、0x6FA6DC、0x7094B5（校验参照：同法 v[241] 槽 0x3C4 恰 14 站=F7T:128-130、vtable[65] 槽 0x104 恰 7 站=F8V:110-111，_scan:46-56 双双 OK）；
- 六站宿主（call 目标级，_scan:899-965）：0x4D5350（=FootClass vftable+0x228 虚方法，直调者 2）、0x4D6AA0（=FootClass vftable+0x220 虚方法，直调者 3，体内调 0x50B730×2/0x565730 等）、**0x4DF0D0（非虚、直调者 34，两个派发站都在其体内）**、0x6F9E50（=**TechnoClass vftable+0x5C = vtable[23]**，即 F6V:167 同槽族 AI 入口，直调者 2）、0x709480（直调者 1=0x719C31）；
- 0x709820 自身的六张虚表槽 RTTI 归属（_scan:966-972）：AircraftClass(0x7E22A4)/BuildingClass(0x7E3EBC)/FootClass(0x7E8C94)/InfantryClass(0x7EB058)/TechnoClass(0x7F4960)/UnitClass(0x7F5C70) 各 +0x39C——F7_review.md:187-190（M2）「0x7E2640 疑 AircraftClass」由此由 RTTI 具名；F7T:187「五张虚表」与 F7_review:189「第六张 0x7E22A4 系」两说在本表下合并为同一集合（6 张，RTTI 名齐全）。
- 如实登记：本项闭的是「调用方是谁、宿主是什么」；每站每帧是否走到、频次几何 = N-9:193 P4 运行期永久缺口，本回件只字未写频次（F7_review M3 纪律延续）。

### 2.6 S3 —— 闭口（0x6E962A 所在 switch 宿主身份）

- 宿主 = **0x6E9050**（call 目标级，_scan:977；序言 55 8b6c2408 56578b…；直调者 33：0x4153F1/0x416EF5/0x417395/0x6E93F4/0x6E942A/0x6E959F/0x6EC3A5/0x6EC753/0x6EC7B6/0x6EC889…，_scan:988）；
- switch 派发器恰 1 处：**0x6E945B `jmp dword ptr [eax*4 + 0x6E9F74]`**（_scan:995-997，FF 24 字节现场 ff2485749f6e00；全 .text disp32==0x6E9F74 的间接跳转仅此 1 条，_scan:998）；
- 跳转表 0x6E9F74 恰 **65 项**全为 .text VA（_scan:999），case 16 = **0x6E961E**（即 F7T:180-181 的 case 尾块，其 0x6E962A `call 0x6ECCE0 %14门宿主`、0x6E9643 `call 0x6ECE60` 与 F7T:180-181 逐字对上，_scan:983-984）；0x6E961E 的 .text dword 引用唯一落点=0x6E9FB4=表内第 16 项（_scan:1000-1001）；
- 宿主体内证据锚点：0x6E9304 `call 0x6E53A0`（建筑回调，F7T:212 同函数）、0x6E9245/体内 `call 0x50B730`、0x6E9184/0x6E91A1/0x6E9222/0x6E9281 调 0x6EA3E0/0x6EA0D0/0x6EAEE0/0x6EAA90（_scan:979-987）；
- 如实登记：本项给的是「宿主函数 = 0x6E9050 + 65 路 switch + 直调者 33 + 体内锚点」这一身份结构；F7T:350 的后半句「与它被调的频率」= 运行期（P4），不写；宿主的业务语义命名（游戏系统名）不作——无符号表，本回件不补造名号。

### 2.7 S4 —— 闭口（PatrolScan 部署值 = .016，三处 MIX 内容一致）

- 扫描方法：对 ra2youli 全部 54 个 .mix/.mmx 磁盘镜像做 b"PatrolScan"/b"patrolscan" 原始字节分块扫描（_mix:1-56 清单，共约 1.6 GB）；
- 恰 3 处命中，值行逐字节一致（_mix:132/:253/:353）：
  `PatrolScan=.016         ; minute interval between scanning for enemys while patrolling.`
  - expandmd01.mix @文件偏移 0x235948（_mix:94-132）
  - ra2.mix @0x7122DA3（_mix:206-253）
  - ra2md.mix @0x67EECC（_mix:315-353）
- 节属核验（命中点向前最近 INI 节头，python 内联绝对路径实跑）：三处最近节头均为 **`[AI]`**（其后跟 BuildConst=…）——与 ERRATA W8-4「PatrolScan 为 rules.ini [AI] 节 double 键」口径一致；内联复算 `N = int(0.016 × 900.0) = 14` 与既有默认值口径一致（默认值出处 F7T:178-179 构造器双写 0.016）；
- 覆盖排除：expandmd98.mix（含 .ra2forge.bak/.old-pre-migrate 两份历史件）、langmd/language、multi/multimd、theme/thememd、wdt、maps01/02/mapsmd03、全部 .mmx = 0 命中（_mix:57-93/:193-204/:414-416 等 NOHIT 行）；散置 BATTLEMD.INI 无 [AI] 节、无 PatrolScan（grep 实跑 0/0）；ra2youli 全树 rules*.ini=0 件（N-9:134 既有实跑，本会话未重跑）；
- 二进制内文件名锚点：gamemd.exe .data 字面串 `RULESMD.INI`(0x826260)/`RULEMD*.INI`(0x82626C)/`CONQMD.MIX`(0x826838)（_scan:31-33，=_audit_task12.py:51 线索复核）；
- 如实登记：三份 MIX 头部的计数/尺寸字段解析异常（_mix:95/:207/:316 header=(0,3,超大值)），条目级归属未做（不影响值行证据）；压缩形态条目未做解压穷举——若存在压缩的 rules 覆盖件则本扫不可见，标残余；「三份内容一致 ⇒ 无论加载优先级取哪份，值均为 .016」是本闭口的稳健性根据；运行期实际生效值仍属 N-9:194 P5 永久缺口，本回件不写。

### 2.8 P11 —— 部分闭口（口径 B 规格骨架已立；完整规格的两处开口为结构性/另需搜索）

按 W8:158（F7 没有 F8 §5 式最小推导规格）与 N-9:208，本回件给出骨架并明确未闭部分。**口径 A（入口累计代理 0xA8EC34）与口径 B（完成扫描数）全程分写。**

骨架（全部字段有既有/本轮出处）：
1. 可计数事件定义（口径 B）：一次 Greatest_Threat(0x6F8DF0) 调用进入其扫描段。入口计数器 0xA8EC34（口径 A 专用字段，D-19 定谳，不得当口径 B）恰 2 条访存 R@0x6F8DF3 / W@0x6F8E09（F7T:259-262；本会话 GT 体独立解码 _scan:1031 同值），早退 ret 0xC @0x6F8E41 在写回之后（F7T:265）——**口径 A 含早退、口径 B 以扫描段为对象，两量不可互算**（N-9:104-107 口径声明延续）。
2. 派发拓扑（谁的调用构成口径 B 候选）：v[241] 槽 +0x3C4 恰 14 派发站（F7T:128-130；_scan:54-56 复现）；链路 = 14 站 → 五类包装（Building 0x445F00 / Foot 0x4D9920 / Unit 0x743190→Foot / Infantry 0x51E140→Foot / Techno 本体）→ GT（F7T:122-135）；门分类 = %14 宏观门 1（宿主 0x6ECCE0，周期 N=int(PatrolScan×900)，部署值见 §2.7）+ 状态门 1（v[231] 宿主 0x709820 内 0x709932，[this+0x2B4]==0）+ 无门 12（F7T:244-246）；本轮 S2/S3 增量给出门站的宿主身份（§2.5/§2.6）。
3. GT 体静态代价结构（本轮实测，_scan:1003-1033）：体 [0x6F8DF0,0x6F9DB0) 共 **1255 条指令**；入口段 [0x6F8DF0,0x6F8E41) 29 条；call/jmp-imm 49 条（目标集含 0x412B40 空间桶查询×1、0x50B730 谓词×2、0x4F9A50×7、0x568300×4、0x6F3970×4、0x6F8960/0x6F8C10×4+4 等，_scan:1005-1028）；后向环边 7 条（jne 0x6F91EC←0x6F9385、jle 0x6F93DE←0x6F974B、jl 0x6F976D←0x6F9ADC、jmp 0x6F9593/0x6F93C1、jl 0x6F9B8D←0x6F9C50、jl 0x6F9C7A←0x6F9D9B，_scan:1029）——三层嵌套扫描环形态与 0x412B40 桶查询在场；体内零内存 inc/dec（_scan:1030）。
4. 未闭部分（结构性 + 另需搜索，如实列）：
   a. **环的行程次数 = 运行期量**（桶内对象数、威胁分布）→ 每次扫描的代价上界与每帧口径 B 数值的分布不可静态给出（N-9:193 P4 永久缺口；N-9:196 P10 同族）；
   b. 12 个无门派发站的宿主语义身份未逐一命名（F7T:357 自报未验；本轮仅覆盖 0x709932/0x6ECE06 两门站与其余站的宿主边界，未做 12 站逐站语义）→ 口径 B 的「覆盖范围」栏写不全；
   c. ra2render.dll 在场时整次跳过（口径 A 的 DLL 节流事实，LEDGER:7095-7099）对口径 B 同样构成整次跳过——部署趟是否在场 = 运行期（P3），规格内只能带注记。
5. 结论：P11 的「字段」栏（0xA8EC34=口径A专用；口径B 无字段、可数事件=扫描段进入）、「顺序」栏（14 站→包装→GT 拓扑）、「代价界」栏（静态下界：入口 29 条 + 环体指令数已知；上界不可静态定）已立；「读数时机/覆盖范围」两栏缺运行期与 12 站语义 → **部分闭口，单列**。

## 3 统计

| 判定 | 项 | 数 |
|---|---|---|
| 闭口 | P7、P8、S1、S2、S3、S4 | **6** |
| 部分闭口（单列，不计入上/下行） | P6（[0x7E1738]=0.5 闭 / [0xB0CD48] 结构性开口）、P11（骨架立 / 两栏缺） | **2** |
| 结构性不可闭（整项） | 无（两处结构性开口均居于部分闭口项内并已写明） | **0** |

closedCount = 6；unclosableCount = 0；部分闭口 = 2（P6、P11）。

## 4 登记疵点与上游前提修正（并存登记，不裁断）

- **a. N-9:205 前提修正**：「P6 = F8 两个 FPU 常量数值（静态 u64 窗口读可闭）」对 [0x7E1738] 成立（§2.1）；对 [0xB0CD48] **不成立**——该地址在 .data 零初始化域（_scan:58），文件镜像无值，且其唯一写者是运行期计算链（_scan:763-774）。N-9:139/PERF:139 的转录同受影响。
- **b. W3 名号并存**：W3_COSTBOUND/sections/Q1_C2_RENDER.md:145 写「0x0071CD7B：VoxelAnimClass::DrawIfVisible」；本轮 RTTI 显示 0x71CD7B 所在函数（0x71CC50..尾段）的槽65 虚表 0x7F522C 名为 `.?AVTerrainClass@@`（_p7:28 与 :47）。两说并存登记，不裁断；该函数的槽65 归属（=TerrainClass vftable 第 65 槽）是本轮新证据。
- **c. F7_review:187-190（M2）**「0x7E2640 疑 AircraftClass，类名未终证」——本轮 RTTI 具名（_scan:967），属补证非翻案。
- **d. 本会话自曝**：_sc_scan.py 前两版有三处脚本缺陷（capstone disasm 未切片、mem 命中漏寄存器基址、find_host 早期版本把指令长度当填充/用裸 ret 字节回扫），已在最终版（v4）修复；_sc_scan_out.txt 为 v4 单次完整运行的输出，早期中间输出未保留（诚实账口径：最终证据一律以 v4 输出与 _sc_p7_out.txt/_sc_mix_out.txt 为准）。

## 5 诚实账

**实跑命令清单（本会话）**：①hashlib 四件编排方指纹复验（python -I -X utf8 -c 内联，4/4 MATCH）；②Read 实读 N-9 全文、W8 全文、F7T/F8V/F6V 全文、F7_review(:140-207)、F8_review 全文、PERF(:130-192)、ERRATA(:160-199)、_w8_f6_out.txt(:150-230)；③grep/find 定向检索（PatrolScan 全仓后台 grep、rulesmd、0x709820、五创建点、三 vtable、0xB0CD48/0x7E1738、71CD7B、_audit_task12.py:51 线索）；④`python -I -X utf8 _sc_scan.py > _sc_scan_out.txt`（v4 最终，EXIT=0；capstone 5.0.7 全 .text 线性解码 1,394,120 条/resync 66，与 W8:44 同数）；⑤`python -I -X utf8 _sc_p7.py > _sc_p7_out.txt`（EXIT=0，0.3s）；⑥`python -I -X utf8 _sc_mix.py > _sc_mix_out.txt`（EXIT=0，54 个 .mix/.mmx 全扫）；⑦若干内联核验（0x7E1728/0x7E27F8 qword、MIX 节头回溯〔两版：首版相对路径、终版绝对路径，以终版为准〕、本写域产出件 hashlib 清点）；⑧`ls`/`wc`/`grep -c`（BATTLEMD.INI [AI]=0、PatrolScan=0）。
**校验通过项**：_scan:5-33 十二条 u32 已知值 + qword 900.0 + 六条 0x709820 槽 + 三条字面串全部 OK；_scan:46-56 call 0x5F4B10=3、call 0x6D2140=139、[+0x104] 虚调用=7、[+0x3C4] 派发=14 四组全 OK；_p7:35 16 槽位与 .rdata 全文件对账差集=空。
**未做项（如实，不补造）**：未追 [0xB0CD48] 输入链（0xB0CD78/88/8C 的写者、0x4CACB0 语义）；未对 MIX 做条目级解析与压缩条目解压穷举；未做 12 个无门 v[241] 派发站的逐站语义；未做 RTTI ClassDescriptor 基类链（层级推导）；未对 .data 段建 vftable 索引（MSVC 惯例在 .rdata，且 0x5F4B10 全文件 16 处均在 .rdata 支撑该惯例）；零真机、零采样、零活进程接触；未 commit、未 push。
**边界声明**：S1/S2/S3 宿主起点为指令边界启发式判定（方法与 F7T:155/F8V:89 同类），全部原始字节随输出可独立复核；本回件不写任何「运行期是否走到/频次/生效值」类量（分别属 N-9 §6.1 P2/P3/P4/P5）；W8 三项判定档维持其「回件判定×复核判定」合并性质（ERRATA:182-184），本回件未对其作任何复验或升格。

## 6 合规自检

全文无 PLAN:89（=NEXT_STEPS:89）所禁的两类中文断言用语；无采样/注入类接口代码；未生成采样候选清单；未补猜任何运行期值；入口代理与完成扫描数分写（§2.8-1）；唯一写域 = lead/spec_static_closure_20261108/（7 件，§0 清单）；未 commit、未 push。
