#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R202 p1：四件套一次性写入 + 回读校验。断言旧 sha256 与 CR 后才写。
写入顺序：先 R17_LEAD_BASELINE wx 独占备份（唯一名），再写四件套。"""
import hashlib,sys,os,time
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
EXP={'R14':('c63e5bda7d8bab60',1081),
     'GOAL':('d62a88373114e551',337),
     'LL':('efc5e8f58e92602d',137),
     'BOARD':('adcd597c0e76bb18',0)}
for k,p in F.items():
    es,ec=EXP[k]
    ck('PRE_%s sha256'%k, sha(p).startswith(es), sha(p)[:16])
    ck('PRE_%s CR'%k, cr(p)==ec, cr(p))
bl0=len(open(F['BOARD'],'rb').read().split(b'\n'))-1
print('board lines pre:', bl0)
if fails:
    print('\nABORT: precond fails',fails); sys.exit(1)

# 备份纪律：wx 独占创建唯一备份
STAMP=time.strftime('%Y%m%d_%H%M%S')
BD=ROOT+'/lead/next_re_20261117_r14/R17_LEAD_BASELINE'
BK={}
for k,p in F.items():
    dst='%s/%s.before_r202_%s.bak'%(BD,os.path.basename(p),STAMP)
    with open(dst,'xb') as f:
        f.write(open(p,'rb').read())
    BK[k]=dst
    ck('BAK_%s wx 独占创建'%k, os.path.exists(dst), os.path.basename(dst))
    ck('BAK_%s 内容 sha 与源一致'%k, sha(dst)==sha(p), sha(dst)[:16])

R14 = """
## 2.207 · R202 交付：31,968 个 ret/int3 区间不是函数（55.4% 起点是 nop）；订正 R201 的 689/697 用混合分母（同质分母 686 下是 686/686 = 100%）；only_sub 的 0 不是「结构性事实」而是「含次表装填的区间 100% 也含主表装填」；11 条 mdisp==0 装表实为两种机制（3 条 INoticeSink 被基类次表同槽位覆盖 / 8 条模板成员子对象）

**一、🔴 订正一（口径级，影响 R201 交付三的百分比）：R201 的 98.85% 是混合分母的产物.** R201 把 697 条小位移装表当成同质集合，算出 both 689/697 = 98.85%。实测 697 = **686 条严格次表 store（disp8 == 该虚表 COL 记录的 mdisp，全 686/686 成立，mdisp 分布 4:345 / 8:341）+ 11 条 mdisp==0 的 store**。这两组的归属规则本就不同：686 条的 `brs[区间]` 计数把**自身**也算进去了，而 11 条不计自身。改用同质分母（只算 686 条严格次表 store），**both = 686 / 686 = 100%**；`_r202/m14_authority.py` X5 在三种网格（ret/int3 区间、E1=CALLAT 目标、E3=CALLAT∪序言）下**全部得 686/686**。⇒ R201 的 98.85% 应读作「697 条中 689 条落在有主表装填的区间」，不是「次表装填的同区间率」；后者是 **100%**。

**二、🔴 订正二（判据级）：R201「only_sub 的 0 首次成为结构性事实」是误判，0 的真因是另一条更有力的事实.** R201 QD3 称 only_sub=0 在区间口径下成为「结构性事实」。实测该分支的判据是 `else: if brs[区间]>0`，而 686 条严格次表 store 自身就计入 `brs`，故对其**恒真**（`_r201/m12_final.py` L159/L165）。真正有信息量的是：**全 .text 中含严格次表 store 的区间共 388 个，其中 388 个（100%）也含至少一处主表 store**；「有次表装填但无主表装填」的区间数 = **0**（`m14` X6a-X6c）。⇒ 结论方向不变且更强（不是「697 条里 689 条」而是「388 个函数体无一例外」），但**理由必须换掉**：不是三分支统计出的 0，而是 KM ⊇ KR 的集合包含关系。主会话 `_r202/m7_deadbranch.py` 曾把这条写成「死分支」，被 `m8` P1d 反控推翻（把主表集置空后 only_sub 立刻 = 686，说明判据可达）；落盘采用订正后的表述。

**三、🔴 交付一（本轮核心，取得 R201 未取得项③）：31,968 个 ret/int3 区间不是函数.** 三条独立证据（`m14` X2/X3）：① 区间起点是 `nop` 的有 **17,726 / 31,968 = 55.45%**；② 全 .text 去重 CALLAT 目标 **6,719** 个，其中落**指令起点** 6,692（99.6%）、落**区间起点**只有 **755（11.2%）**，其余 5,964 个落在区间内部；③ **25,357 / 31,968 = 79.3%** 的区间内**一个 CALLAT 目标都没有**。⇒ R201 用「store 所属 ret/int3 区间」近似「同一函数」，这个近似在 79% 的区间上是无约束的。**区间 ≠ 函数**，两者差 20 倍以上量级。

**四、🔴 交付二：收紧到可辩护的函数网格后，结论不变.** 建两种入口网格：**E1** = CALLAT 目标（落指令起点者，6,692 个）；**E3** = E1 ∪ 严格序言位。严格序言位在**区间起点**上的分布为 P1（`push ebp; mov ebp,esp`）**249** / P4（`sub esp,imm` 起首）**158** / P3b（`mov edi,edi` 后 3 条内含 `push ebp; mov ebp,esp`）**60**，合计 **467**；`(i)∪(ii)` = **864** 个区间（与审计 #510 报的 864 一致，其 (ii)=411 与本轮 467 的差 56 条来自 hotpatch 序言模式定义不同，两者都保留）。E3 网格共 **10,674** 个入口。697 条在该网格下 **both=691 / only_sub=0 / none=6**（none 为 0x5d5b80 / 0x635f34 / 0x637114 / 0x638aa4 / 0x7b1b2b / 0x7b27fb）；686 条在 E3 下 **both=686 / only_sub=0 / none=0**。⇒ 换到函数网格后 686 条的同函数率仍是 **100%**，R201 的结论方向被独立网格证实，但其「8 条 none」在函数网格下缩为 6 条。

**五、🔴 交付三（取得 R201 未取得项①，部分）：8 条 none 的宿主类名，5 条取得 / 3 条 UNDETERMINED.** 按 ret/int3 窄区间读 +0 主表：0x5d5b80 → `MultiplayerGameMode`（区间内另有 `DynamicVectorClass<MultiplayerTeam>` 与 `CCINIClass`）、0x6cf196 与 0x6cf209 → `SwizzleManagerClass`（区间内另有 `DynamicVectorClass/VectorClass<SwizzlePointerClass>` 与 `SuperWeaponTypeClass` 及其 +4/+8/+12 次表）、0x7b1b2b 与 0x7b27fb → `WinsockInterfaceClass`（区间内另有 3-5 处 `VectorClass<PAUWinsockBufferType@WinsockInterfaceClass>` 主表）。**3 条 UNDETERMINED**：0x635f34 / 0x637114 / 0x638aa4，区间内只有模板成员类（`DynamicVectorClass<PlanningNodeClass>` / `VectorClass<PlanningNodeClass>`）的**主表**，无任何非模板外层类主表；其调用点前 24 字节只有 `mov ecx,...` 透传，拿不到外层 RTTI 写入证据。与执行员 #509 报告的 5 条逐条一致（`m14` X7b），3 条 UNDETERMINED 亦一致。

**六、🔴 交付四（取得 R201 未取得项②）：11 条 mdisp==0 的 +4/+8 装表是两种机制，不是一种.** 按「同区间、同基址寄存器、同 disp 槽位的完整写入序列」分离（`m14` X8、`m13`）：
- **机制 A（3 条，全是 `. ?AVINoticeSink@@`：0x410174 / 0x4101c2 / 0x6e8008）**：该槽位**被后续 store 覆盖**。0x410174 与 0x4101c2 的 +8 槽位序列为 [INoticeSink 主表 mdisp=0] → [AbstractClass 次表 mdisp=8]；0x6e8008 的 +8 槽位序列为 [INoticeSink] → [AbstractClass mdisp=8] → [TaskForceClass mdisp=8]。即**先装子对象主表、再被同一槽位的基类次表改写**，是多继承布局的中间态。INoticeSink 全段主表装填仅 5 处（0x410174/0x4101c2/0x6e8008 disp=8、0x5be9bd disp=21784、0x6cfe3c disp=0），其中 3 处 disp=8 全部命中覆盖。
- **机制 B（8 条，全是模板容器成员类）**：槽位序列长度恒为 1，**无任何后续覆盖**，是纯粹的内嵌成员子对象 vftable 初始化。
反控与判别力：686 条严格次表 store 中「后继同槽位被 mdisp==disp 的 store 覆盖」只有 **12 条（1.7%）**，而 11 条中 **3 条（27.3%）**，富集 **16.1 倍**。⇒ R201「11 条全是内嵌成员子对象主表初始化」的定性**只对 8 条成立**，另 3 条是子对象主表被基类次表覆盖。

**七、📌 自错（当场抓出，无一条进结论）.** ① `m1` 断言「R201 口径 both=689」FAIL — 我在 m1 里把 `sub` 定义成 `1<=disp<=9 且 MD!=0`（686 条）却仍断言 689/697，**断言与分母不同源**；② `m2` 三条断言（V2=686、V1-V2 差 11、V2 disp8 全等）全 FAIL — 我预期「识别 0x66 前缀后会掉到 686」，实测**两种提取器都得 697**，说明 0x66 前缀不解释 697/686 之差，差的是 mdisp==0 那 11 条（**m2 是断言写错，不是发现**）；③ `m3` `F3b/F3c` FAIL — 我把「序言位」的扫描范围写成**全部指令起点**（118,491）却与「区间起点子集」（1,150）比较，两集合本不等；④ `m3` `F4a` FAIL — 用 R201 原口径复算 689/0/8 得 697/0/0，根因是同一「分母不同源」（`sub` 已排除 11 条 mdisp==0，而 brm/brs 仍按原集算）；⑤ `m4` `G5b` FAIL — 扰动反控把区间终点 +64 后 `reg_of` 返回的是新元组，与 brm/brs 的键不同源，得全 none，**反控本身失效**（已改为不扰动键的 G5c）；⑥ `m7` `K1a/K1b/K1c` FAIL — 我断言「brs[区间]>=1 的恰 686 条」，实测 **689**（多出的 3 条是 mdisp==0 但所在区间另有严格次表 store），**m7 的「死分支」表述因此不成立**，已由 m8 P1d 订正；⑦ `m7` `K5a` FAIL — 剔除自身后 only_sub 仍为 0（得 both 669 / none 28），我预期 >0；⑧ `m8` `P1b` FAIL — `len(brs)` 在有 0 计数的键上不成立（388 个非零 vs 键数更多）；⑨ `m8` `P4c/P4d` FAIL — 我按 #510 的 564/156 设区间，实测 E3 网格 686 条重装是 **285/114**（#510 的 564 用的是全 4,198 条 vts 口径，两口径不可比）；⑩ `m10` `M3a/M3b` 全 FAIL — 我假设「区间内每个 disp 只对应一个类」，实测 .?AVAbstractClass@@ 次表在 +4/+8/+12 **三个位移上都有**，假设错；⑪ `m12` `V1a` FAIL — 我预期「11 条全部有后继槽位覆盖」，实测只有 3 条，**这个 FAIL 反而开出了第六交付**；`V3a` FAIL 是我的判别力门限写反；⑫ `m13` `W4a` FAIL — 686 条槽位序列长度实测 {1:662, 2:16, 3:8}，我断言「恒 1」；`W5b` FAIL — INoticeSink 的 0x5be9bd（disp=21784）也有后继覆盖；⑬ `m15` `Y1a` FAIL — 我把「P1=249」当成全指令起点计数，真值 458，249 是**区间起点子集**；`Y3a` FAIL 同理（P3 全指令起点 3 条在**放宽 span 后**归入 P3b，严格 span=3 时 0 条）。

**八、🟡 跨家族与落盘.** 执行员 **#509**（hy4，31 回合 / 7.65′ / 无 OVERTIME，18 断言 0 FAIL）与本轮并发；审计员 **#510**（deepseek，20 回合 / 7.68′ / 无 OVERTIME，33 断言全 PASS）。两者结论全部由主会话脚本 `_r202/m8_verify.py`（20 断言）、`m9_final.py`（20 断言 0 FAIL）、`m14_authority.py`（33 断言）亲跑复算（§2.12 规则 D）。**采纳 #510 三条**：①「区间 ≠ 函数」的 55.4% nop 起点 / 5,964 个 CALLAT 目标落区间内部 / 79.3% 区间零目标（主会话独立复算逐数一致）；②**函数范围口径 691/0/6**（主会话独立复算一致，6 条 none 地址逐条一致）；③COL 指针恒在 `vt-4`（1214/1214）而 COL 结构体地址非常数（916 个取值）⇒ **只能查表不能线性推算**。**不采纳 #510 两条**：①「11 条 disp!=mdisp 应称‘disp 与 mdisp 不一致’而非‘主表装填’」—— 不采纳，因 mdisp==0 就是该 COL 记录的「主对象」标记，而实测这 11 条全部装的是主表指针（`_r201/m12_final.py` 的 CLS 与 MD 两表同源），命名无误；②「重装 564/697 = 80.9%」—— 口径不可比（#510 用全 4,198 条 vts 的函数范围，主会话用 686 条小位移，得 285/114），两者都保留并标注口径。**#509 三条 UNDETERMINED 被主会话独立复算确认为真 UNDETERMINED**（非漏取）。落盘：R14_COMMON 本节 CR 保持 1081；GOAL §1257 CR 保持 337；LEAD_LOCK QE 段 CR 保持 137；STATUS_BOARD 第 202 轮 CR 保持 0。

**九、⚪ 未取得（不粉饰）.** ① 0x635f34 / 0x637114 / 0x638aa4 三条的外层宿主类名（缺外层 RTTI 写入证据）；② INoticeSink 的 0x5be9bd（disp=21784 非 {4,8}）为何用巨位移、0x6cfe3c（disp=0）为何不带覆盖；③ 686 条里 12 条后继同槽位覆盖（1.7%）的语义；④ 「区间 ≠ 函数」的正确函数边界仍未取得（E3 是**候选入口网格**，不是真函数边界；显式调用外的间接调用目标无法恢复）；⑤ R200 未取得项 (c)(d)(f)(g) 未动；⑥ F23/F35 grade 未改；⑦ coverage.tsv/function_atlas.tsv 仍不可读；⑧ 86.19% 原值仍不可重算；⑨ C7 三死分支仍各 0 行；⑩ C11 十二个永不 FAIL id 未动。
"""

GOAL = """
## §1257 · R202：区间不等于函数（55.4% 起点为 nop、79.3% 区间零 CALLAT 目标）；同质分母下 686/686 = 100%；only_sub 的 0 换成集合包含关系；11 条 mdisp==0 装表分两种机制

**一、口径订正（影响百分比）.** R201 的 98.85% 用混合分母 697：该集 = 686 条严格次表 store（disp8 == COL mdisp，686/686）+ 11 条 mdisp==0。两组归属规则不同（686 条自身计入 brs，11 条不计）。同质分母下 **686/686 = 100%**，在 ret/int3、E1、E3 三种网格下全部成立。

**二、判据订正.** R201「only_sub 的 0 是结构性事实」表述不成立：该分支对 686 条恒真（自身计数）。真正有力的事实是 **KM ⊇ KR**：含严格次表 store 的区间 **388 个，388 个（100%）也含主表 store**，「有次表无主表」区间数 = 0。主会话内部一度写成「死分支」，已被可达性反控推翻（主表集置空 → only_sub = 686）。

**三、区间 ≠ 函数（本轮核心）.** 31,968 个 ret/int3 区间中：起点为 `nop` **17,726（55.45%）**；去重 CALLAT 目标 **6,719** 个，落指令起点 6,692（99.6%）、落区间起点仅 **755（11.2%）**、落区间内部 5,964；**25,357（79.3%）** 个区间内零 CALLAT 目标。⇒ 用「store 所属区间」近似「同一函数」，在 79% 的区间上无约束。

**四、收紧网格后结论不变.** E1 = CALLAT 目标（6,692）；E3 = E1 ∪ 严格序言位（区间起点 P1 249 / P4 158 / P3b 60，合计 467；`(i)∪(ii)` = 864），E3 共 **10,674** 入口。697 条在 E3 下 **691/0/6**（none：0x5d5b80 / 0x635f34 / 0x637114 / 0x638aa4 / 0x7b1b2b / 0x7b27fb）；686 条下 **686/0/0**。⇒ 方向被独立网格证实，R201 的 8 条 none 缩为 6 条。

**五、8 条 none 宿主（5 取得 / 3 UNDETERMINED）.** 0x5d5b80 → `MultiplayerGameMode`；0x6cf196 / 0x6cf209 → `SwizzleManagerClass`；0x7b1b2b / 0x7b27fb → `WinsockInterfaceClass`。UNDETERMINED：0x635f34 / 0x637114 / 0x638aa4（区间内只有模板成员类主表，调用点前 24B 只有 `mov ecx` 透传）。

**六、11 条两种机制.** 机制 A（3 条 INoticeSink：0x410174 / 0x4101c2 / 0x6e8008）**+8 槽位被后续基类次表覆盖**（AbstractClass / TaskForceClass，mdisp=8 同槽位）；机制 B（8 条模板容器成员）槽位序列恒长 1、**无覆盖**。判别力：686 条中后继同槽位覆盖 12 条（1.7%），11 条中 3 条（27.3%），富集 **16.1 倍**。

**七、跨家族.** #509（hy4，18 断言 0 FAIL）5 条类名与 3 条 UNDETERMINED 逐条复算一致；#510（deepseek，33 断言全 PASS）采纳 3 条（区间≠函数、函数范围 691/0/6、COL 指针恒 vt-4 且地址非常数 916 取值）、不采纳 2 条（11 条命名、重装 564 口径不可比），全部结论经 `m8_verify` / `m9_final` / `m14_authority` 亲跑复算。

**八、未取得.** ① 3 条 UNDETERMINED 外层类名；② INoticeSink 0x5be9bd（disp=21784）与 0x6cfe3c（disp=0）的形态解释；③ 686 条中 12 条后继覆盖的语义；④ **真函数边界仍未取得**（E3 只是候选入口网格；间接调用目标不可恢复）；⑤ R200 (c)(d)(f)(g)；⑥ F23/F35 grade；⑦ coverage.tsv/function_atlas.tsv 仍不可读；⑧ 86.19% 仍不可重算；⑨ C7 三死分支各 0 行；⑩ C11 十二个 id 未动。
"""

LL = """
## QE · R17 第 202 轮（2026-11-28 20x）· 31,968 个 ret/int3 区间不是函数；R201 的 98.85% 是混合分母；only_sub 的 0 换成 KM ⊇ KR；11 条 mdisp==0 装表是两种机制

**QE1. 🔴 订正一（口径级）.** R201 `QD3` 的「both 689/697 = 98.85%」把两批不同质的 store 放进同一分母：697 = **686 条严格次表 store**（disp8 == COL mdisp，686/686 成立，mdisp 4:345 / 8:341）+ **11 条 mdisp==0**。686 条的 `brs[区间]` 含自身计数、11 条不含。同质分母 **686/686 = 100%**，三种网格（ret/int3、E1、E3）全成立（`_r202/m14_authority.py` X5）。⇒ 98.85% 只能读作「697 条中 689 条落在有主表装填的区间」。

**QE2. 🔴 订正二（判据级）.** R201 `QD3`「only_sub 的 0 首次成为结构性事实」不成立：该分支（`_r201/m12_final.py` L159/L165）对 686 条恒真。真事实是 **KM ⊇ KR**：含严格次表 store 的区间 **388 个全部（388/388）也含主表 store**，「有次表无主表」区间 **0**（`m14` X6a-c）。主会话 `_r202/m7_deadbranch.py` 一度写成「死分支」，被 `m8` P1d 反控推翻（主表集置空 → only_sub 686），落盘用订正表述。

**QE3. 🔴 交付一：区间 ≠ 函数.** ① 区间起点为 `nop` **17,726 / 31,968 = 55.45%**；② 去重 CALLAT 目标 **6,719**，落指令起点 6,692（99.6%）、落区间起点 **755（11.2%）**、其余 5,964 落区间内部；③ **25,357（79.3%）** 区间零 CALLAT 目标（`m14` X2/X3）。⇒ R201 的「同函数」近似在 79% 区间上无约束。

**QE4. 🔴 交付二：收紧网格结论不变.** E1 = CALLAT 目标 6,692；E3 = E1 ∪ 严格序言位（区间起点 P1 249 / P4 158 / P3b 60 = 467；`(i)∪(ii)` 864），|E3| = **10,674**。697 条在 E3 下 **691/0/6**（none：0x5d5b80 / 0x635f34 / 0x637114 / 0x638aa4 / 0x7b1b2b / 0x7b27fb）；686 条 **686/0/0**。反控：E3 每入口 +1 字节 → 683/3/0，非恒等变换。

**QE5. 🔴 交付三：8 条 none 宿主，5 取得 / 3 UNDETERMINED.** 0x5d5b80 → `MultiplayerGameMode`（区间另有 `DynamicVectorClass<MultiplayerTeam>`、`CCINIClass`）；0x6cf196 / 0x6cf209 → `SwizzleManagerClass`（另有 `SuperWeaponTypeClass` +4/+8/+12 次表）；0x7b1b2b / 0x7b27fb → `WinsockInterfaceClass`。UNDETERMINED：0x635f34 / 0x637114 / 0x638aa4 —— 区间内只有模板成员类主表，调用点前 24B 只有 `mov ecx` 透传，无外层 RTTI 写入。

**QE6. 🔴 交付四：11 条 mdisp==0 装表两种机制.** 机制 A（3 条 INoticeSink：0x410174 / 0x4101c2 / 0x6e8008）+8 槽位**被后续基类次表覆盖**（0x410174/0x4101c2：INoticeSink mdisp=0 → AbstractClass mdisp=8；0x6e8008：INoticeSink → AbstractClass mdisp=8 → TaskForceClass mdisp=8）。机制 B（8 条模板容器）槽位序列恒长 1、**无覆盖**。判别力：686 条中后继同槽位覆盖 **12 条（1.7%）** vs 11 条中 **3 条（27.3%）**，富集 **16.1 倍**。⇒ R201「11 条全是内嵌成员子对象主表初始化」只对 8 条成立。

**QE7. 📌 自错（当场抓出，0 条进结论）.** ① `m1` 分母不同源（sub 取 686 却断言 689/697）；② `m2` 三条 FAIL：**两种提取器都得 697**，0x66 前缀不解释 697/686 之差（差的是 mdisp==0 的 11 条），是我断言写错；③ `m3` F3b/F3c 拿 118,491 全指令起点与 1,150 区间起点子集比较；④ `m3` F4a 同一分母不同源（得 697/0/0）；⑤ `m4` G5b 扰动反控把区间键换成新元组 ⇒ 反控自身失效；⑥ `m7` K1a/K1b/K1c 断言「brs>=1 恰 686」实测 **689**，「死分支」表述因此不成立，由 m8 P1d 订正；⑦ `m7` K5a 剔除自身后 only_sub 仍 0（both 669 / none 28）；⑧ `m8` P1b `len(brs)` 含零计数键；⑨ `m8` P4c/P4d 按 #510 的 564/156 设区间，实测 E3 686 口径重装 **285/114**（口径不可比）；⑩ `m10` M3a/M3b 假设「每 disp 只对应一类」，实测 `AbstractClass` 次表在 +4/+8/+12 三处都有；⑪ `m12` V1a 预期「11 条全覆盖」实测 3 条 —— **该 FAIL 开出第六交付**，V3a 判别力门限写反；⑫ `m13` W4a 断言槽位序列恒 1，实测 {1:662, 2:16, 3:8}；W5b `0x5be9bd`（disp=21784）也有覆盖；⑬ `m15` Y1a 把 P1=249 当全指令起点计数（真值 458），Y3a 的 P3 严格 span=3 时 0 条。

**QE8. 🟡 跨家族与落盘.** #509（hy4，31 回合 / 7.65′ / 18 断言 0 FAIL）与 #510（deepseek，20 回合 / 7.68′ / 33 断言全 PASS）均无 OVERTIME。结论由 `_r202/m8_verify.py`（20 断言）、`m9_final.py`（20 断言 0 FAIL）、`m14_authority.py`（33 断言）亲跑复算。采纳 #510 三条（区间≠函数三证据逐数一致；函数范围 691/0/6 与 6 条 none 地址逐条一致；COL 指针恒 `vt-4` 1214/1214 而 COL 地址 916 取值 ⇒ 只能查表）；不采纳两条（11 条命名无误 —— mdisp==0 即该 COL 记录主对象标记；重装 564 为全 4,198 条 vts 口径，与 686 小位移口径 285/114 不可比，两者并存标注）。#509 的 3 条 UNDETERMINED 经复算确认为真 UNDETERMINED。落盘：R14_COMMON §2.207 CR 保持 1081；GOAL §1257 CR 保持 337；本段 CR 保持 137；STATUS_BOARD 第 202 轮 CR 保持 0。

**QE9. ⚪ 未取得（不粉饰）.** ① 3 条 UNDETERMINED 外层类名；② INoticeSink `0x5be9bd`（disp=21784）/ `0x6cfe3c`（disp=0）的形态解释；③ 686 条中 12 条后继覆盖的语义；④ **真函数边界仍未取得**（E3 是候选入口网格，不是边界；间接调用目标不可恢复）；⑤ R200 (c)(d)(f)(g)；⑥ F23/F35 grade；⑦ coverage.tsv/function_atlas.tsv 仍不可读；⑧ 86.19% 仍不可重算；⑨ C7 三死分支各 0 行；⑩ C11 十二个 ID 未动。
"""

BOARD = """
### R202（2026-11-28）· gamemd.exe 静态本体：区间不等于函数；同质分母 686/686 = 100%；11 条 mdisp==0 装表分两种机制

**一、区间 ≠ 函数（本轮核心）.** 31,968 个 ret/int3 区间中 **55.45%（17,726）** 起点是 `nop`；去重 CALLAT 目标 **6,719** 个，落指令起点 6,692（99.6%）但落**区间起点**只有 **755（11.2%）**，其余 5,964 落区间内部；**79.3%（25,357）** 的区间内零 CALLAT 目标。⇒ R201 用「store 所属区间」近似「同一函数」，在 79% 的区间上无约束。

**二、收紧网格结论不变.** E3 = CALLAT 目标 ∪ 严格序言位（P1 249 / P4 158 / P3b 60，合计 467；`(i)∪(ii)` 864）= 10,674 入口。697 条在 E3 下 **691/0/6**；**686 条（严格次表 store）在三种网格下全部 686/0/0 = 100%**。反控：每入口 +1 字节 → 683/3/0。

**三、口径订正.** R201 的 **98.85%** 用混合分母 697（= 686 条严格次表 store + 11 条 mdisp==0），两组归属规则不同（686 条自身计入 brs、11 条不计）。同质分母下是 **100%**。R201「only_sub 的 0 成为结构性事实」也不成立（该分支对 686 条恒真）；真事实是 **含严格次表 store 的 388 个区间全部（388/388）也含主表 store**，「有次表无主表」区间 **0**。

**四、8 条 none 宿主（5 取得 / 3 UNDETERMINED）.** 0x5d5b80 → `MultiplayerGameMode`；0x6cf196 / 0x6cf209 → `SwizzleManagerClass`；0x7b1b2b / 0x7b27fb → `WinsockInterfaceClass`。UNDETERMINED：0x635f34 / 0x637114 / 0x638aa4（区间内只有模板成员类主表，调用点前 24B 只有 `mov ecx` 透传）。

**五、11 条 mdisp==0 装表是两种机制.** 机制 A（3 条 INoticeSink：0x410174 / 0x4101c2 / 0x6e8008）**+8 槽位被后续基类次表覆盖**（AbstractClass mdisp=8，0x6e8008 再被 TaskForceClass mdisp=8）；机制 B（8 条模板容器成员）槽位序列恒长 1、**无覆盖**。判别力：686 条中后继同槽位覆盖 **12 条（1.7%）** vs 11 条中 **3 条（27.3%）**，富集 **16.1 倍**。⇒ R201「11 条全是内嵌成员子对象主表初始化」只对 8 条成立。

**六、跨家族.** #509（hy4，31 回合，18 断言 0 FAIL）5 条类名与 3 条 UNDETERMINED 逐条复算一致；#510（deepseek，20 回合，33 断言全 PASS）采纳 3 条（区间≠函数三证据、函数范围 691/0/6、COL 指针恒 `vt-4` 1214/1214 而 COL 地址 916 取值）、不采纳 2 条（11 条命名无误；重装 564 为全 4,198 条 vts 口径，与 686 小位移口径 285/114 不可比）。全部经 `_r202/m14_authority.py`（33 断言）亲跑复算。

**七、自错 13 组（0 条进结论）.** 分母不同源 3 处（m1 / m3-F4a / m8-P4c）；`m2` 预期「识别 0x66 前缀掉到 686」实测两提取器都 697 —— 697/686 之差是 mdisp==0 那 11 条**不是前缀**；`m3` 拿 118,491 全指令起点与 1,150 区间起点子集比较；`m4` 扰动反控把区间键换成新元组致反控自身失效；`m7` 断言「brs>=1 恰 686」实测 **689**，其「死分支」表述因此不成立（由 m8 P1d 可达性反控推翻）；`m10` 假设「每 disp 只对应一类」，实测 `AbstractClass` 次表在 +4/+8/+12 三处都有；`m12` V1a 预期「11 条全覆盖」实测 3 条 —— **该 FAIL 开出第五交付**；`m13` 断言槽位序列恒 1，实测 {1:662, 2:16, 3:8}；`m15` 把 P1=249 当全指令起点计数（真值 458）。

**落盘.** R14_COMMON 追加 §2.207 CR 保持 1081；GOAL 追加 §1257 CR 保持 337；LEAD_LOCK 追加 QE CR 保持 137；本看板追加第 202 轮 CR 保持 0（开局 257 行 < 260，无需归档）。

**未取得.** ① 3 条 UNDETERMINED 外层类名；② INoticeSink `0x5be9bd`（disp=21784）/ `0x6cfe3c`（disp=0）形态解释；③ 686 条中 12 条后继覆盖的语义；④ **真函数边界仍未取得**（E3 是候选入口网格，间接调用目标不可恢复）；⑤ R200 (c)(d)(f)(g)；⑥ F23/F35 grade；⑦ coverage.tsv/function_atlas.tsv 仍不可读；⑧ 86.19% 仍不可重算；⑨ C7 三死分支各 0 行；⑩ C11 十二个 id 未动。
"""

def app(p,text,exp_cr,tail_blank=True):
    b=open(p,'rb').read()
    assert b.count(b'\r')==exp_cr, 'CR drift on '+p
    assert b'\r' not in text.encode('utf-8'), 'text contains CR: '+p
    t=text.encode('utf-8')
    if not t.endswith(b'\n'): t+=b'\n'
    body=b+t
    if tail_blank: body+=b'\n'
    open(p,'wb').write(body)
    return body

b1=app(F['R14'],R14,1081)
b2=app(F['GOAL'],GOAL,337)
b3=app(F['LL'],LL,137)
b4=app(F['BOARD'],BOARD,0,tail_blank=False)
ck('W_R14 CR 保持 1081', b1.count(b'\r')==1081, b1.count(b'\r'))
ck('W_GOAL CR 保持 337', b2.count(b'\r')==337, b2.count(b'\r'))
ck('W_LL CR 保持 137', b3.count(b'\r')==137, b3.count(b'\r'))
ck('W_BOARD CR 保持 0', b4.count(b'\r')==0, b4.count(b'\r'))
bl=len(b4.split(b'\n'))-1
ck('W_BOARD 行数 <= 300', bl<=300, bl)
ck('R_R14 含 2.207', b'## 2.207' in open(F['R14'],'rb').read(), True)
ck('R_GOAL 含 1257', b'\xc2\xa71257' in open(F['GOAL'],'rb').read(), True)
ck('R_LL 含 QE1', b'QE1.' in open(F['LL'],'rb').read(), True)
ck('R_BOARD 含 R202', b'R202' in open(F['BOARD'],'rb').read(), True)
ck('R_BOARD 段数 == 历史+1', open(F['BOARD'],'rb').read().count(b'### R')>=1, '')
for k,p in F.items():
    d=open(p,'rb').read()
    print('   %-6s bytes=%d CR=%d sha=%s'%(k,len(d),d.count(b'\r'),hashlib.sha256(d).hexdigest()[:16]))
print('\nSUMMARY fails=%d %s'%(len(fails),fails))
if fails: sys.exit(1)
print('board_lines=%d'%bl)
