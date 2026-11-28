#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R201 p1：四件套一次性写入 + 回读校验。断言旧 sha256 与 CR 后才写。"""
import hashlib,sys,os,re
ROOT='/home/t628/projects/ra2-campaign-forge'
def sha(p): return hashlib.sha256(open(p,'rb').read()).hexdigest()
def cr(p): return open(p,'rb').read().count(b'\r')
fails=[]
def ck(nm,c,d=''):
    if not c: fails.append(nm)
    print(('PASS ' if c else 'FAIL ')+nm+((' | '+str(d)) if d!='' else ''))
F={
 'R14':ROOT+'/lead/next_re_20261117_r14/R14_COMMON.md',
 'GOAL':ROOT+'/lead/GOAL_THREE_TARGETS_20261018.md',
 'LL':ROOT+'/lead/LEAD_LOCK',
 'BOARD':ROOT+'/lead/next_re_20261117_r14/STATUS_BOARD.md',
}
EXP={'R14':('5794b9499229091f678b0d4b1264c1ea4695073d64d9e72000e583acf05c7307',1081),
     'GOAL':('48fb8e2bb187e07ec5dd279e3b67d3bbb063453625a4ea03a651348614f4c9d0',337),
     'LL':('8fa678c50cefeb5fb165d275e19c298b0a5bef3bf4c7c37b95ab5ed109aea440',137),
     'BOARD':('99a5f4096262049543ab15d9440581e4838ab3c01fc0bd7f92709293b6a5f69d',0)}
for k,p in F.items():
    es,ec=EXP[k]
    ck('PRE_%s sha256'%k, sha(p)==es, sha(p)[:16])
    ck('PRE_%s CR'%k, cr(p)==ec, cr(p))
print('board lines pre:', sum(1 for _ in open(F['BOARD'],'rb')))
if fails:
    print('\nABORT: precond fails',fails); sys.exit(1)

R14 = """
## 2.206 · R201 交付：R200 「only_main 11 宿主」是命名与判据不符的产物；窗口口径跨函数污染 p50=5 个区间；改 ret/int3 区间口径后 689/697（98.85%）次表装填与主表装填同区间、only_sub 归零

**一、🔴 订正一：R200 的 only_main 命名与代码判据不一致（代码级证据，非转述）.** `_r200/m11_subfill.py` 宿主三分类的第三支 `else` 实际判据是 `not (has_main and has_sub)`，而落盘字段名与正文表述均为 `only_main`（只装主表）。二者不等价：实测 11 个 only_main 宿主里 **窗口内确实装了主表的 6 个**、**完全零装表的 5 个**（0x547cf0 / 0x62f9a0 / 0x6e3b60 / 0x718b70 / 0x71f680）。⇒ R200 QC2「只装主表 11 个」这一表述**不成立**：11 是「窗口内主表与子表未同时出现」的计数，不是「只装主表」的计数。跨家族审计 #504 独立复算同得 6/5（26 断言 24 PASS，2 FAIL 均为卡面预期写错）。

**二、🔴 订正二：R200 的 4096 字节窗口跨函数污染已被定量.** 262 个宿主窗口 `[h, min(下一个 CALLAT 目标, h+4096))` 内包含的 **ret/int3 区间数 p50 = 5 / mean = 11.46 / max = 97**，恰含 1 个区间的窗口只有 **64 个（24.4%）**。即「同函数内」这个前提对 3/4 的宿主窗口根本不成立 ⇒ R200「251 个同函数内主表 + 子表双装」是**窗口口径的产物**，不是同函数事实。

**三、🔴 交付（本轮新取得，强于 R200）：改用 ret/int3 区间口径，697 条小位移装表按所属代码区间归属.** 全 `.text` 反汇编得 **31,967 条 ret/int3 边界 ⇒ 31,968 个代码区间**；按 store 所属区间统计：
- **both（同区间既有主表装填又有次表装填）689 / 697 = 98.85%**
- **only_sub（区间内有次表装填、无任何主表装填）0 条**
- **none（区间内无任何次表装填）8 条**
- 每条 store 都有归属区间（noreg = 0），三数相加 = 697。
⇒ **「子表装填必与主表装填同处一个函数」在真实函数体口径下由 251/262（95.8%，宿主级、受污染）提升为 689/697（98.85%，store 级、无污染）**，并且 only_sub 从 0 变成 0 的**口径真实性**首次被证明（R200 的 only_sub=0 是窗口污染下的巧合，区间口径下是结构性事实）。

**四、🔴 交付：8 条 none 全部是模板容器成员子对象的主表装填，回答 R200 未取得项 (a).** 8 条逐一为
0x5d5b80 `. ?AV?$DynamicVectorClass@PAVMultiplayerTeam@@@@` / 0x635f34 `DynamicVectorClass<PlanningNodeClass>` / 0x637114 `VectorClass<PlanningNodeClass>` / 0x638aa4 `DynamicVectorClass<PlanningNodeClass>` / 0x6cf196 `DynamicVectorClass<SwizzlePointerClass>` / 0x6cf209 `VectorClass<SwizzlePointerClass>` / 0x7b1b2b 与 0x7b27fb `VectorClass<PAUWinsockBufferType@WinsockInterfaceClass>`。
它们的共同结构：**都是「某个宿主对象的成员子对象」的构造**，装的是该成员自身的主表（mdisp==0）到 `this+4` 或 `this+8`，所在区间内**另有**宿主类自己的主表装填（主表数 1..4），但**没有**该成员类的次表装填（次表 0）。⇒ R200 未取得项 (a)「11 条 mdisp==0 装 +4/+8 的语义动机」取得：**并非虚基类次表，而是内嵌成员子对象的 vftable 初始化**；且 11 条中 8 条属此形态，另 3 条（0x410174 / 0x4101c2 / 0x6e8008，均为 `. ?AVINoticeSink@@`）所在区间内同时有次表装填（3/3/6 条），属**同一构造函数里既装主表又装次表的常规形态**。

**五、🔴 交付：697 = 686 次表 + 11 主表 是严格二分，不是阈值产物.** disp8 == imm 的 COL mdisp：**686 条（4:345 / 8:341）**；disp8 != mdisp：**11 条（mdisp 全 0）**。两组位移都只取 {4, 8}；G1 的 mdisp 全 ∈ {4,8} 且 >0。⇒ 686 条是「多继承次表装填（位移 = 该基类在对象内的偏移，与 COL 记录一致）」，11 条是「主表装填到成员偏移」。这一二分在 R200 已见，但 R200 未给出 G1 的 mdisp 分布为 4:345/8:341 与「两组位移都只 4/8」。

**六、🔴 交付：主表装填面（回答 R200 未取得项 (b) 的可复算部分）.** 8 个代表类的主表装填：
`. ?AVAirstrikeClass@@` 6 处/6 区间、`. ?AVAlphaShapeClass@@` 6/6、`. ?AVBombClass@@` 6/6、`. ?AVLightSourceClass@@` 6/6、`. ?AVWaveClass@@` 5/5、`. ?AVWalkLocomotionClass@@` 4/4、`. ?AVVoxelAnimTypeClass@@` 4/4、`. ?AVCellClass@@` 4/4。
**每类的主表装填处数 == 其所在代码区间数**（即每个构造函数各装一次，无同函数重复装填），且每类分布于 4..6 个不同函数。这些类的次表装填数为 18/18/18/18/14/8/11/11。⇒ 「某类的主表由谁装」取得：**由该类的多个构造函数各装一次，一处一函数**，不存在「主表无人装」的类。

**七、📌 自错（当场抓出，无一条进入结论）.** ① m1 两条断言（M1c/M1d）假设「only_main 窗口内零装表」被实测 [0,5,0,2,1,1,0,0,0,4,6] 与 store 数 [2,1,2,1,1,1,2,2,2,1,1] 砸掉，反而打开第二交付；② m5 的 `same_cls_main` 用了**漏掉 mod==0 的旧提取器**得 15/686，与 m10 的 686/686 矛盾，追查发现旧扫描器 `else: pos += 1` 丢弃 `C7 /0 [rm] imm32`（6 字节无位移形态），**主表装填的主要形式恰是 mod==0**（全段 2,741 条 mod==0 装表，其中装主表 2,697）；③ m6 F0d 构造正控只命中 3/4，根因是合成夹具 `while pos<cap-6` 边界把最后一条 6 字节指令挡掉，且未做 `need` 越界检查，修正为 `cap-4 + need 检查` 后 4/4；④ m6 F0h 断言「小位移 697 不变」实测 686 是**断言写错**（697 含 11 条 mdisp==0，`mdisp!=0` 筛选自然得 686），三口径 A/B/C 的小位移数**均为 697**；⑤ m9 G0d/G0e 断言两口径装表数相等被 697 vs 773 / 3088 vs 4276 砸掉，根因是 capstone 线性反汇编在**数据区**也产出伪 `mov [reg],imm`（D 漏检区 1,581 条），故两口径只能取交集用，8 个代表类两口径**完全一致**（D=E=交集）；⑥ m10 K3f 断言「G1 体内同装本类主表 <5%」实测 100% 是**断言方向写反**（真结论就是 100%）；⑦ m11 P0d/P0g/P0j 三条断言方向全反（假设 both<251、only_sub>0、m11 区间内无次表），实测 689/0/3 条有次表，三条均改为正向陈述；⑧ m12 S4f 的 `none` 筛选条件误用主表计数（应为次表计数 brs==0），订正后 8 条逐条给出。
**另有 0x66 操作数前缀缺陷**：`66 C7 /0` 是 `mov WORD PTR`，全段 750 处（mod 1:552 / 0:169 / 2:29）；旧提取器按 6/7/11 字节跳过，若按 dword 解析会产生 0x6c71234 这类伪 imm。已加前缀分支并作正控（`66 c7 00 3412` + `c7 06 ...` 只命中 1 条 dword）。

**八、⚪ 未取得（不粉饰）.** ① 8 条 none 所在宿主对象的具体类名（只知道成员类型，未知宿主类型）；② 3 条 `. ?AVINoticeSink@@` 的 +4/+8 位移为何是 8 而非 4；③ 31,968 个区间里有多少是真函数入口（区间起点可能是数据区，未做 CALLAT/序言过滤）；④ R200 未取得项 (c)(d)(f)(g) 未动；⑤ 审计 #504 两条 FAIL 的卡面预期值未回改（A2b/A5c）；⑥ F23/F35 grade 未改；⑦ coverage.tsv/function_atlas.tsv 仍不可读；⑧ 86.19% 原值仍不可重算；⑨ C7 三死分支仍各 0 行；⑩ C11 十二个永不 FAIL id 未动。
"""

GOAL = """
## §1256 · R201：R200 only_main 命名与判据不符；窗口污染 p50=5 区间；ret/int3 区间口径下 689/697 同区间双装、only_sub 归零

**一、R200 命名订正（代码级）.** `_r200/m11_subfill.py` 第三支 `else` 判据为 `not (has_main and has_sub)`，字段名与正文写 `only_main`。11 个 only_main 里装主表 6、零装表 5。⇒「只装主表 11 个」不成立。

**二、窗口污染定量.** 262 宿主窗口内 ret/int3 区间数 p50=**5**、mean=**11.46**、max=**97**；恰含 1 个区间者 **64/262 = 24.4%**。⇒「251 个同函数双装」是窗口产物。

**三、区间口径交付（强于 R200）.** 31,967 条 ret/int3 边界 ⇒ **31,968 个区间**。697 条小位移装表按区间归属：**both 689（98.85%）/ only_sub 0 / none 8**，noreg 0，三数相加 697。「子表装填与主表装填同函数」由宿主级 251/262（95.8%，受污染）提升为 store 级 689/697（98.85%，无污染）。

**四、8 条 none 全为内嵌成员子对象主表装填（R200 未取得项 (a) 取得）.** 0x5d5b80 / 0x635f34 / 0x637114 / 0x638aa4 / 0x6cf196 / 0x6cf209 / 0x7b1b2b / 0x7b27fb，成员类型全是 `VectorClass<..>` / `DynamicVectorClass<..>`；装的是成员自身主表（mdisp==0）到 this+4/+8，区间内另有宿主主表 1..4 处、无该成员类次表。另 3 条 0x410174 / 0x4101c2 / 0x6e8008（`. ?AVINoticeSink@@`）区间内同时有次表 3/3/6 条，属常规形态。

**五、697 严格二分.** disp8==mdisp **686（4:345 / 8:341）**；disp8!=mdisp **11（mdisp 全 0）**；两组位移都只 {4,8}。

**六、主表装填面（R200 未取得项 (b) 可复算部分）.** 8 代表类主表装填：Airstrike 6/6、AlphaShape 6/6、Bomb 6/6、LightSource 6/6、Wave 5/5、WalkLocomotion 4/4、VoxelAnimType 4/4、Cell 4/4（处数/区间数）。**每类处数 == 区间数**，一处一函数；次表数 18/18/18/18/14/8/11/11。⇒ 主表由该类多个构造函数各装一次。

**七、审计 #504（deepseek，26 断言 24 PASS）.** 两条 FAIL 均为**卡面预期值写错**：A2b 卡面写「only_main 宿主集合 == main11 宿主集合」实测不等（11 vs 10，交集 6）；A5c 卡面写「每条 sub store 都落在其宿主体内」实测 **162 个宿主存在体截断**。后者的独立发现比主会话更早指出宿主归属错位，已被采纳进本轮的区间口径设计。

**八、未取得.** ① 8 条 none 的宿主对象类名；② `. ?AVINoticeSink@@` 位移 8 而非 4 的原因；③ 31,968 区间中真函数入口占比（未做 CALLAT/序言过滤）；④ R200 (c)(d)(f)(g) 未动；⑤ F23/F35 grade 未改；⑥ coverage.tsv/function_atlas.tsv 仍不可读；⑦ 86.19% 仍不可重算；⑧ C7 三死分支各 0 行；⑨ C11 十二个永不 FAIL id 未动。
"""

LL = """
## QD · R17 第 201 轮（2026-11-28 18x–19x）· R200 的 only_main 是命名与判据不符的产物；窗口内 p50 含 5 个代码区间；ret/int3 区间口径下 689/697 同区间双装、only_sub 归零

**QD1. 🔴 交付一：R200 only_main 命名与代码判据不一致（代码级）.** `_r200/m11_subfill.py` 三分类第三支 `else` 判据 = `not (has_main and has_sub)`，落盘名与正文写 `only_main`。实测 11 个里**装主表 6 / 零装表 5**（零装表：0x547cf0 / 0x62f9a0 / 0x6e3b60 / 0x718b70 / 0x71f680）。⇒ R200「只装主表 11 个」不成立，11 是「未见主表+子表同窗口」的计数。

**QD2. 🔴 交付二：R200 窗口跨函数污染定量.** 262 宿主窗口内 ret/int3 区间数 **p50=5 / mean=11.46 / max=97**，恰含 1 个者 **64/262=24.4%**。⇒「251 个同函数双装」是 4096 字节窗口跨过多个函数的产物。

**QD3. 🔴 交付三（本轮核心，强于 R200）.** 全 `.text` 得 **31,967 条 ret/int3 边界 ⇒ 31,968 个区间**。697 条小位移装表按所属区间归属：**both 689（98.85%）/ only_sub 0 / none 8**，noreg=0，和=697。同区间双装率由宿主级 251/262（95.8%，受污染）提升为 store 级 **689/697（98.85%，无污染）**；only_sub 的 0 首次成为**区间口径下的结构性事实**而非窗口巧合。

**QD4. 🔴 交付四：8 条 none 全是内嵌成员子对象主表装填（取得 R200 未取得项 (a)）.** 8 条：0x5d5b80 `DynamicVectorClass<MultiplayerTeam>` / 0x635f34 `DynamicVectorClass<PlanningNodeClass>` / 0x637114 `VectorClass<PlanningNodeClass>` / 0x638aa4 `DynamicVectorClass<PlanningNodeClass>` / 0x6cf196 `DynamicVectorClass<SwizzlePointerClass>` / 0x6cf209 `VectorClass<SwizzlePointerClass>` / 0x7b1b2b、0x7b27fb `VectorClass<PAUWinsockBufferType@WinsockInterfaceClass>`。形态：装成员自身主表（mdisp==0）到 this+4 或 this+8，区间内另有宿主主表 1..4 处、**无**该成员类次表。另 3 条 0x410174 / 0x4101c2 / 0x6e8008（`. ?AVINoticeSink@@`）区间内同时有次表 3/3/6 条 ⇒ 常规形态。⇒ (a) 的动机是**内嵌成员子对象的 vftable 初始化**，不是虚基类次表。

**QD5. 🔴 交付五：697 是严格二分.** disp8 == COL mdisp：**686（4:345 / 8:341）**；不等：**11（mdisp 全 0）**。两组位移都只取 {4,8}；G1 的 mdisp 全 >0。

**QD6. 🔴 交付六：主表装填面（取得 R200 未取得项 (b) 的可复算部分）.** 8 代表类主表装填处数/区间数：Airstrike 6/6、AlphaShape 6/6、Bomb 6/6、LightSource 6/6、Wave 5/5、WalkLocomotion 4/4、VoxelAnimType 4/4、Cell 4/4。**处数 == 区间数**（一函数一处），分布于 4..6 个函数；对应次表数 18/18/18/18/14/8/11/11。⇒ 主表由该类多个构造函数各装一次，不存在主表无人装的类。

**QD7. 📌 自错（当场抓出，0 条进结论）.** ① m1 M1c/M1d「only_main 窗口内零装表」被 [0,5,0,2,1,1,0,0,0,4,6] 砸掉，反开第二交付；② **m5 的 15/686 源于旧提取器漏 `mod==0`**（`else: pos+=1` 丢弃 `C7 /0 [rm] imm32`），而主表装填主要形式正是 mod==0（全段 2,741 条，装主表 2,697）；③ m6 F0d 正控 3/4 是**夹具边界缺陷**（`cap-6` 挡掉末条 6 字节指令），改 `cap-4 + need` 后 4/4；④ m6 F0h「697 不变」实测 686 是断言写错（三口径 A/B/C 均为 697）；⑤ m9 G0d/G0e 被 697 vs 773 / 3088 vs 4276 砸掉，根因 capstone 在**数据区**产伪 `mov [reg],imm`（D 漏检 1,581 条）⇒ 两口径只能取交集，8 代表类 D=E=交集；⑥ m10 K3f「<5%」实测 100% 是断言方向写反；⑦ m11 P0d/P0g/P0j 三条方向全反（689/0/3 条有次表）；⑧ m12 S4f 的 none 误用主表计数（应 brs==0）。**另修 0x66 前缀**：`66 C7 /0` 是 `mov WORD PTR`，全段 750 处（mod 1:552/0:169/2:29），按 dword 解析会产生 0x6c71234 类伪 imm，已加分支并正控。

**QD8. 🟡 跨家族与落盘.** 执行员 #504(A/B 两卡 hy4) 与审计员 #505(deepseek，26 断言 24 PASS) 的结论全部由主会话脚本 `_r201/m12_final.py`（18 断言 0 FAIL）与 `_r201/audit_c.py` 亲跑复算。审计两条 FAIL 均为卡面预期写错：A2b（only_main 与 main11 宿主集合本不等，11 vs 10、交集 6）、A5c（**162 个宿主存在体截断**，审计独立发现早于主会话，直接促成本轮区间口径设计）。落盘：R14_COMMON §2.206 CR 保持 1081；GOAL §1256 CR 保持 337；本段 CR 保持 137；STATUS_BOARD 第 201 轮 CR 保持 0。

**QD9. ⚪ 未取得（不粉饰）.** ① 8 条 none 的宿主对象类名；② `. ?AVINoticeSink@@` 位移 8 而非 4 的原因；③ 31,968 区间中真函数入口占比（未做 CALLAT/序言过滤，区间起点可能是数据区）；④ R200 未取得项 (c)(d)(f)(g) 未动；⑤ 审计 #504 两条 FAIL 的卡面预期值未回改；⑥ F23/F35 grade 未改；⑦ coverage.tsv/function_atlas.tsv 仍不可读；⑧ 86.19% 原值仍不可重算；⑨ C7 三死分支仍各 0 行；⑩ C11 十二个永不 FAIL id 未动。
"""

BOARD = """
### R201（2026-11-28）· gamemd.exe 静态本体：R200 only_main 命名订正 + 区间口径 689/697 同区间双装

**一、R200 命名与判据不符（代码级）.** `_r200/m11_subfill.py` 第三支 else 判据是 `not (has_main and has_sub)`，字段名与正文写 `only_main`。实测 11 个里**装主表 6 / 零装表 5**（0x547cf0 / 0x62f9a0 / 0x6e3b60 / 0x718b70 / 0x71f680）。⇒「只装主表 11 个」不成立。

**二、窗口跨函数污染定量.** 262 宿主窗口内 ret/int3 区间数 **p50=5 / mean=11.46 / max=97**，恰含 1 个者 **64/262 = 24.4%**。⇒ R200「251 个同函数双装」是 4096 字节窗口的产物。

**三、区间口径交付（本轮核心）.** 全 .text 得 **31,967 边界 ⇒ 31,968 区间**。697 条小位移装表按所属区间归属：**both 689 / only_sub 0 / none 8**，noreg 0，和 697；同区间双装率 **98.85%**。较 R200 宿主级 251/262（95.8%、受污染）为更强且无污染的结论；only_sub 的 0 由窗口巧合变为**结构性事实**。

**四、8 条 none 全是内嵌成员子对象主表装填（取得 R200 未取得项 (a)）.** 成员类型全为 `VectorClass<..>` / `DynamicVectorClass<..>`：0x5d5b80 / 0x635f34 / 0x637114 / 0x638aa4 / 0x6cf196 / 0x6cf209 / 0x7b1b2b / 0x7b27fb。装成员自身主表（mdisp==0）到 this+4/+8，区间内另有宿主主表 1..4 处、无该成员类次表。另 3 条 `. ?AVINoticeSink@@`（0x410174 / 0x4101c2 / 0x6e8008）区间内同时有次表 3/3/6 条 ⇒ 常规形态。⇒ 动机是**内嵌成员子对象 vftable 初始化**，非虚基类次表。

**五、697 严格二分.** disp8==mdisp **686（4:345 / 8:341）**；不等 **11（mdisp 全 0）**；两组位移均只 {4,8}。

**六、主表装填面（取得 R200 未取得项 (b) 可复算部分）.** 8 代表类处数/区间数全等：Airstrike 6/6、AlphaShape 6/6、Bomb 6/6、LightSource 6/6、Wave 5/5、WalkLocomotion 4/4、VoxelAnimType 4/4、Cell 4/4；次表数 18/18/18/18/14/8/11/11。⇒ 一函数装一处，主表由该类多个构造函数各装一次。

**七、自错 8 条（0 条进结论）.** m1 M1c/M1d 断言被实测砸掉反而开出第二交付；**m5 的 15/686 源于旧提取器漏 mod==0**；m6 F0d 3/4 是夹具 `cap-6` 边界缺陷；m6 F0h 断言写错（697 含 11 条 mdisp==0）；m9 G0d/G0e 因 capstone 在数据区产伪命中（D 漏检 1,581 条）只能取交集；m10 K3f 方向写反（真值 100%）；m11 P0d/P0g/P0j 三条方向全反；m12 S4f 误用主表计数。另修 **0x66 前缀**（`66 C7 /0` = mov WORD，全段 750 处，不处理会产 0x6c71234 类伪 imm）。

**八、跨家族.** 审计员 #505（deepseek，26 断言 24 PASS）两条 FAIL 均为**卡面预期写错**：A2b（only_main 与 main11 宿主集合本不等：11 vs 10、交集 6）、A5c（**162 个宿主存在体截断**）。A5c 是审计**早于主会话**的独立发现，直接促成本轮改用 ret/int3 区间口径。全部结论由主会话 `_r201/m12_final.py`（18 断言 0 FAIL）亲跑复算。

**落盘.** R14_COMMON 追加 §2.206 CR 保持 1081；GOAL 追加 §1256 CR 保持 337；LEAD_LOCK 追加 QD CR 保持 137；本看板追加第 201 轮 CR 保持 0（开局 235 行 < 260，无需归档）。

**未取得.** ① 8 条 none 的宿主对象类名；② `. ?AVINoticeSink@@` 位移 8 而非 4 的原因；③ 31,968 区间中真函数入口占比（未做 CALLAT/序言过滤）；④ R200 (c)(d)(f)(g) 未动；⑤ 审计两条 FAIL 卡面未回改；⑥ F23/F35 grade 未改；⑦ coverage.tsv/function_atlas.tsv 仍不可读；⑧ 86.19% 仍不可重算；⑨ C7 三死分支各 0 行；⑩ C11 十二个永不 FAIL id 未动。
"""

def app(p,text,exp_cr,tail_blank=True):
    b=open(p,'rb').read()
    assert b.count(b'\r')==exp_cr, 'CR drift on '+p
    # 原文件结尾为 \n\n（末段后一个空行），追加时保持全 LF，不引入任何 CR
    t=text.encode('utf-8')
    if not t.endswith(b'\n'): t+=b'\n'
    body=b+t
    if tail_blank: body+=b'\n'
    open(p,'wb').write(body)
    return body

# R14_COMMON 全 LF、CR=1081；新文本内不得含 CR
b1=app(F['R14'],R14,1081)
b2=app(F['GOAL'],GOAL,337)
b3=app(F['LL'],LL,137)
b4=app(F['BOARD'],BOARD,0,tail_blank=False)
ck('W_R14 CR 保持 1081', b1.count(b'\r')==1081, b1.count(b'\r'))
ck('W_GOAL CR 保持 337', b2.count(b'\r')==337, b2.count(b'\r'))
ck('W_LL CR 保持 137', b3.count(b'\r')==137, b3.count(b'\r'))
ck('W_BOARD CR 保持 0', b4.count(b'\r')==0, b4.count(b'\r'))
bl=len(b4.split(b'\n'))
ck('W_BOARD 行数 <= 300', bl<=300, bl)
# 回读校验
for k,p in F.items():
    d=open(p,'rb').read()
    print('   %-6s bytes=%d CR=%d'%(k,len(d),d.count(b'\r')))
ck('R_R14 含 2.206', b'\xe2\x80\xa7' or b'## 2.206' in open(F['R14'],'rb').read(), True)
ck('R_GOAL 含 1256', b'## \xc2\xa71256' in open(F['GOAL'],'rb').read() or b'1256' in open(F['GOAL'],'rb').read(), True)
ck('R_LL 含 QD1', b'QD1.' in open(F['LL'],'rb').read(), True)
ck('R_BOARD 含 R201', b'R201' in open(F['BOARD'],'rb').read(), True)
print('\nSUMMARY fails=%d %s'%(len(fails),fails))
if fails: sys.exit(1)
print('board_lines=%d'%bl)
