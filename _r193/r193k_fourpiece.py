#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R193 四件套追加（R14_COMMON §2.198 / 台账 §1248 / LEAD_LOCK PV / 看板第 193 轮）。
★ 幂等保护：写任何一份前先断言现盘 sha == 开跑基线；不等则整体 fail-closed。
★ 同时把 R14_COMMON §2.197（6,904 B ⇒ floor 3,452）按既有规则「floor = 本节字节 // 2」
   钉进 check_disc.py 的 C16_FLOORS 并重算 C16_FLOORS_SHA256（否则新增 §2.198 后
   unpinned 会变 2，下一轮再加一节就超 C16_UNPINNED_MAX(2)）。
"""
import hashlib, io, os, re, sys, time
ROOT='/home/t628/projects/ra2-campaign-forge'
TIER=os.path.join(ROOT,'lead/next_re_20261117_r14')
BL=os.path.join(TIER,'R17_LEAD_BASELINE')
R14=os.path.join(TIER,'R14_COMMON.md')
LED=os.path.join(ROOT,'lead/GOAL_THREE_TARGETS_20261018.md')
LCK=os.path.join(ROOT,'lead/LEAD_LOCK')
BRD=os.path.join(TIER,'STATUS_BOARD.md')
CD=os.path.join(TIER,'check_disc.py')
fails=[];n=0
def ck(nm,c,d=''):
    global n;n+=1
    if not c: fails.append(nm)
    print(('PASS ' if c else 'FAIL ')+nm+((' | '+str(d)) if d!='' else ''))

base={}
for tag,p in (('R14',R14),('LED',LED),('LCK',LCK),('BRD',BRD),('CD',CD)):
    b=open(p,'rb').read()
    base[tag]=(len(b),hashlib.sha256(b).hexdigest(),b.count(b'\r\n'),b.count(b'\n'))
print('开跑基线:',{k:(v[0],v[1][:8],v[2],v[3]) for k,v in base.items()})
ck('B1 R14 1,682,710 B / CR 1081 / sha 1845947e…',
   base['R14'][0]==1682710 and base['R14'][2]==1081 and base['R14'][1].startswith('1845947e'), base['R14'][:3])
ck('B2 台账 5,347,385 B / CR 337 / sha e1547419…',
   base['LED'][0]==5347385 and base['LED'][2]==337 and base['LED'][1].startswith('e1547419'), base['LED'][:3])
ck('B3 LEAD_LOCK 1,343,173 B / CR 137 / sha b9a9fb4c…',
   base['LCK'][0]==1343173 and base['LCK'][2]==137 and base['LCK'][1].startswith('b9a9fb4c'), base['LCK'][:3])
ck('B4 看板 49,482 B / CR 0 / 231 行 / sha a99eb3ed…',
   base['BRD'][0]==49482 and base['BRD'][2]==0 and base['BRD'][3]==231
   and base['BRD'][1].startswith('a99eb3ed'), base['BRD'][:4])

S198='''## 2.198 R193：四个高频实现落在**同一个 78 类血统集合**上（77+1 闭合、78==L、75⊂L 缺 3 类全为覆写）；并补 AbstractClass 序列化路径的字节闭合（+0x10 走定长块写、+0x20 走带 CRC32 的字节流）

**一、血统集合 L 的定义与规模.** 在 954 张主表（COL 第 2 个 dword == 0）里取「pCHD 基类指针数组里出现过 `.?AVAbstractClass@@`」的那些表，得 **78 张 / 78 个不同 COL 修饰名**（按名去重后仍是 78，无重名）。R191/R192 交的四个数（0x410450 77 槽 / 0x410220 78 槽 / 0x410580 75 槽 / 0x410590 78 槽）看起来互不相干，本轮证明它们全部落在 L 上，差异只由「覆写」与「缺层」解释。

**二、0x410450 双向唯一且是槽 4 的默认实现.** 在全部 1,214 张表的**所有**槽位上扫该地址，命中的槽号集合恰为 **{4}**（各 77 次，其余 33 个槽号各 0 次），且 77 张全在 mdisp==0 的主表。L 共 78 张，唯一不取 0x410450 的是 `.?AVHouseTypeClass@@`（主表 0x7EAB58，槽 4 = `0x512280` = `33 C0 C2 04 00`，与 0x410450 同为 ret 4，槽位替换不改调用约定）⇒ **77 + 1 = 78 闭合**。0x410450 的全函数体 6 条：`8B 4C 24 04 / 33 C0 / 8A 51 20 / 84 D2 / 0F 94 C0 / C2 04 00`（读 `[this+0x20]` 字节、test、sete ⇒ 返回「该字节为 0」、ret 4）；把「读 +0x20 + sete」当成形态判据去扫槽 5 的 546 个实现，命中 **0**（反控：形态不是普适垃圾判据）。

**三、0x410220 与 L 严格相等，且只在 IRTTITypeInfo 层.** 0x410220 的宿主**类名集合**与 L **严格相等**（各 78 个，双向差集都为 0），且**只**出现在 `(.?AUIRTTITypeInfo@@, offset-to-top 4)` 子表的**槽 4**（78/78，无其它层、无其它槽号）。其体 `8B 44 24 04 / 8B 40 0C / C2 04 00`（`mov eax,[esp+4]; mov eax,[eax+0xC]; ret 4`）读的是**相对该接口子对象 +0xC**；该子对象在完整对象里的 offset-to-top 是 4，折算到完整对象即 **+0x10**。这是「同一字段」的第二个观测面 —— R192 只到「0x410450 读 this+0x20」，本轮补上「同一个 78 类血统集合里还有一条读 +0x10 的路径」。

**四、0x410590 与 L 严格相等.** 宿主类名集合同为 78/78，只出现在 `(.?AVINoticeSource@@, offset-to-top 12)` 子表槽 0，体 `C2 04 00`（ret 4）。

**五、0x410580 是 L 的真子集，缺的 3 个是覆写不是缺层.** 75/78，缺 `.?AVAircraftClass@@` / `.?AVInfantryClass@@` / `.?AVUnitClass@@`；这 3 个类**都有** `(.?AVINoticeSink@@, offset-to-top 8)` 子表（链里该层的 mdisp 都是 8），只是槽 0 分别被覆写成 **0x41BC30**（`sub esp,0x20` 起首）/ **0x522A60**（`sub esp,0x10`）/ **0x746100**（`sub esp,0x18`），三个实现互不相同。

**六、直接引用面订正（R192 的一处错话作废）.** 0x410450 / 0x410580 / 0x410590 被直接 `call rel32` 与 `call [abs]` 引用各 **0** 处，但 **0x410220 有 14 处**（首个在 `0x413E89`）。⇒ R192 末句「四个地址直接引用均为 0 ⇒ 只经虚表调用」对 0x410220 **不成立**，正确说法是「三个只经虚表调用，一个另有 14 处直接调用」。

**七、AbstractClass 序列化路径的字节闭合.** `0x410410`（`.?AVAbstractClass@@` 主表 0x7E1F50 槽 13）体 15 条，顺序确定：先 `mov eax,[esi+0x10]; mov ecx,edi; push eax; call 0x4A1D50`，再 `mov cl,[esi+0x20]; push ecx; mov ecx,edi; call 0x4A1CA0`，`ret 4`。两条被调函数性质不同：**0x4A1D50**（7 条）= `push 4 / lea edx,[esp+4] / push / call 0x4A1DE0 / ret 4`，是**4 字节定长块写**的薄壳；**0x4A1CA0**（39 条）= 累计计数 `[ecx+4]`、逐字节写 `[eax+ecx+8]`、满 4 字节时（`cmp eax,4` + `jne` 跳过）把 4 字节折进 **CRC32** 并清零，表基 **0x81F7B4**：`t[0]=0 / t[1]=0x77073096 / t[255]=0x2D02EF8D`，是**标准反射 CRC-32 表**；代码里 `not eax` 出现 **2 次**（前置 + 收尾）、`shr eax,8` 一次，用「not 前后包裹的反射实现」在 **7 个样本（含空串）** 上与 `zlib.crc32` **逐样本一致**；不带 not 包裹的纯反射实现则不一致（空串除外）⇒ 那两次 not 是语义必需的，不是冗余。4 字节路径 0x4A1DE0（154 条）同样引用 0x81F7B4 ⇒ 两条路径最终折进同一张表。

**八、字段归属的独立字节证据（不依赖 kb/22）.** L 里「槽 4 读 `[this+0x20]` 且槽 13 也触及 `[this+0x20]`」的表有 **3 张**：`.?AVAbstractClass@@`（0x7E1F50）/ `.?AVCellClass@@`（0x7E4EEC）/ `.?AVTactical@@`（0x7F4348）。配合第七点「槽 13 先写 +0x10 再写 +0x20」与第三点「槽 4 经 IRTTITypeInfo 层读到完整对象 +0x10」，可得 +0x10 与 +0x20 是**在同一函数里被先后写出的两个字段**、走两条不同的序列化路径（定长块 vs 带 CRC 的字节流）。这与 kb/22 独立给出的 UniqueID(+0x10) / Dirty(+0x20) 双通道一致；但**语义名仍来自 kb/22 这一外部源**，本轮只补强字段归属的字节侧。

**九、口径裁定：主表 954 / 接口子表 260 的分裂字段是 d1 不是 d0.** COL 五个 dword 的实测分布：**d0 恒为 0**（signature，1,214/1,214）、**d2 恒为 0**（cdOffset）；真正区分主表与接口子表的是 **d1**（offset-to-top / mdisp）：0 有 954 条、非 0 有 260 条。用 d0 判主表会得「主表 1,214 / 子表 0」，这是本轮跨家族审计出现过的基线错误。同一批数据上两种分母给出的槽 4 Top1 也不同：954 主表口径 Top1 = **0x410450（77）**；1,214 全表口径 Top1 = **0x410220（78，全部落在接口子表，主表 0 次）**。两口径不可混用。

**十、103 对「96 字节内无 ret」的完整边界分析（R191/R192 待办 (c) 收口）.** 严格口径（从目标起线性反汇编，遇 `ret/retn` 或**指令边界上**的 >=2 连续 `90/CC` 即停，窗口 512 B）下：`STRICT_RET|STRICT_RET` **78** / `STRICT_RET|PAD_BEFORE_RET` **10** / `STRICT_RET|WINDOW_OUT` **11** / `WINDOW_OUT|STRICT_RET` **4** / **两侧都不可判 0**。10 个 PAD 侧**全部**是调整器 thunk（`83 6C 24 04` 或 `81 6C 24 04` 前缀 + `E9 rel32`），其 E9 落点（0x414290 / 0x4F6E60 / 0x4F6950 / 0x4F6830 / 0x410260）在严格口径下**都有 ret** ⇒ **「两侧都真的没有 ret 的对数 = 0」**。

**十一、边界（不粉饰）.** （a）L 是**RTTI 结构判据**：只说明该主表的 pCHD 基类指针数组里出现过 `.?AVAbstractClass@@` 这一条，不说明运行期对象布局，也不说明任何槽的语义名；78 只对 954 张主表口径成立，把 260 张接口子表并进来会得到不同分母。（b）集合比较必须**按 COL 修饰名**，不能按表地址：0x410580 / 0x410590 / 0x410220 只出现在接口子表上，而 L 是主表地址集合，按地址比必然互不相交（本轮第一版正是这么写的，5 条断言当场 FAIL，改正后保留作反控）。（c）「折算到完整对象 +0x10」依赖两条前提：接口子对象 offset-to-top == 4、实现体内位移相对该子对象；两条都只由字节与 RTTI 记录支撑，**未**做运行期内存采样。（d）CRC 结论只到「两个辅助函数各自做什么」：**没有**证明 +0x10 与 +0x20 在同一流里的先后顺序对应存档格式字段序，也**没有**确定校验覆盖范围（整段还是分块）；7 样本一致只证明表是标准表 + not 包裹形态，不等于证明调用点的入参与初值。（e）调度卡判据写法欠定：卡面写的「thunk = 首字节 E9/EB/FF25 或 引用<=1 且首指令 <=8 B」实测得 432/783/351/425/7，**不能**复现 478/525/10/1013/535；能复现的是「只剔除 `83/81 6C 24 04` 调整器」这一 R192 有效口径，基线一律用后者。（f）执行员 **#471**（hy4，60 回合 truncated，实测 6.63 分 vs 预算 3 分，OVERTIME）独立脚本在 535/1013/478/525/10 五数与本轮一致、103 对里两侧都有 ret 78 / 两侧都无 0 与本轮一致，但它**没有拆出 PAD 档**；审计员 **#472**（deepseek，21 回合 error_max_turns 失败）只产出基线错误的审计文本（用 d0 判主表得 1214/0、并把槽 13 的 `test byte[esp+0x20],2` 误记成 WRITE），其结论除「0x410450 在槽 4 出现 77 次」外**一律不采信**。

'''
S1248='''## §1248 R193：四个高频实现落在同一个 78 类血统集合（77+1 闭合 / 78==L / 75⊂L 缺 3 类全为覆写）；AbstractClass 序列化路径字节闭合（+0x10 定长块写、+0x20 带 CRC32 字节流）

**一、血统集合 L.** 954 张主表里 pCHD 基类指针数组含 `.?AVAbstractClass@@` 的 **78 张 / 78 个类名**。

**二、0x410450.** 全 1,214 张表所有槽位扫描：命中集合恰 **{槽 4} × 77 张**（余 33 个槽号各 0），77 张全在主表；L 的唯一例外是 `.?AVHouseTypeClass@@` 槽 4 = 0x512280（同 ret 4）⇒ 77+1=78 闭合。体 6 条 = 读 `[this+0x20]` + sete + ret 4。

**三、0x410220.** 宿主类名集合与 L **严格相等**（78/78，双向差集 0），只在 `(.?AUIRTTITypeInfo@@, mdisp 4)` 子表槽 4；体 `8B 44 24 04 / 8B 40 0C / C2 04 00` ⇒ 相对接口子对象 +0xC、折算完整对象 **+0x10**。

**四、0x410590.** 宿主类名集合与 L **严格相等**，只在 `(.?AVINoticeSource@@, mdisp 12)` 子表槽 0，体 `C2 04 00`。

**五、0x410580.** 真子集 75/78，缺 AircraftClass / InfantryClass / UnitClass；三者的 `(.?AVINoticeSink@@, mdisp 8)` 子表都在，槽 0 被覆写成 0x41BC30 / 0x522A60 / 0x746100 ⇒ **覆写不是缺层**。

**六、直接引用订正.** 0x410450 / 0x410580 / 0x410590 直接引用各 0 处，但 **0x410220 有 14 处**（首个 0x413E89）⇒ R192「四地址均为 0」对 0x410220 作废。

**七、序列化路径.** 0x410410（槽 13）先 `push [esi+0x10]; call 0x4A1D50` 再 `mov cl,[esi+0x20]; push ecx; call 0x4A1CA0`，ret 4。0x4A1D50 = 4 字节定长块写薄壳（push 4 / call 0x4A1DE0 / ret 4）；0x4A1CA0 = 1 字节写 + 计数满 4 折进 CRC32（表 0x81F7B4 = 标准反射表 t[1]=0x77073096 / t[255]=0x2D02EF8D，not 前后包裹，7 样本与 zlib 一致）。4 字节路径 0x4A1DE0 也引用同一张表。

**八、字段归属.** L 里「槽 4 读 [this+0x20] 且槽 13 触及 [this+0x20]」的表 3 张（AbstractClass 0x7E1F50 / CellClass 0x7E4EEC / Tactical 0x7F4348）⇒ +0x10 与 +0x20 是同一函数里被先后写出的两字段，走两条不同序列化路径；与 kb/22 的 UniqueID/Dirty 一致，但语义名仍来自 kb/22。

**九、口径裁定.** COL d0 恒 0（signature）、d2 恒 0；分裂字段是 **d1**：0 有 954 / 非 0 有 260。954 主表口径槽 4 Top1 = 0x410450(77)；1,214 全表口径 Top1 = 0x410220(78，全在子表，主表 0 次)。

**十、103 对边界分析.** STRICT|STRICT 78 / STRICT|PAD 10 / STRICT|WINDOW_OUT 11 / WINDOW_OUT|STRICT 4 / 两侧都不可判 **0**；10 个 PAD 侧全是调整器 thunk 且 E9 落点都有 ret ⇒ **两侧都真无 ret 的对数 = 0**。

**十一、落盘.** 台账 V577→V578（stmt 13,249→**17,512 B**、lim 10,086→**13,491 B**、第 4 列 375→**508 B**、**184,812 B**、sha `5093b704…`、17 断言 0 FAIL）；重钉 44 断言 0 FAIL（MASTER `2c70d253…`→**`cd0caea7…`**、FLOORS['F55'] (13249,10086)→**(17512,13491)**、EVID 17→**23**、EVIDB 375→**508**、ITEMS 200→**206**、UNIQ 92→**98**、LOST 43/16 未变、指针「530..577 / 48 份」→「**530..578 / 49 份**」、声明轮次 R192→**R193**）；三门 exit 0。C16_FLOORS 188→**189**（钉 §2.197 floor 3,452）。

**十二、未取得.** 四个实现的**游戏语义名**（仍只到接口层 + 槽号 + 参数个数）；「+0x10/+0x20 的流内先后顺序对应存档字段序」与「CRC 覆盖范围」；「ncb 最大 = 最外层」的编译器侧依据；L 为什么恰是这 78 个类（Positive mechanism 未取得）。跨家族：执行员 #471 五数一致但未拆 PAD 档；审计员 #472 error_max_turns 失败且基线错误，除 0x410450=77 外不采信。

'''
PV='''## PV · R17 第 193 轮（2026-11-28 9x–10x）· 四个高频实现落在**同一个 78 类血统集合**上（77+1 闭合、78==L、75⊂L 缺 3 类全为覆写）；补 AbstractClass 序列化路径字节闭合（+0x10 定长块写 / +0x20 带 CRC32 字节流）；103 对「96B 内无 ret」收口为**两侧都真无 ret = 0**

**PV1. 🔴 交付一：四个数其实是同一个集合.** R191/R192 交的 77 / 78 / 75 / 78 四组数看起来互不相干。本轮定义血统集合 **L = 954 张主表里 pCHD 基类指针数组含 `.?AVAbstractClass@@` 的 78 张**（按 COL 修饰名去重仍是 78），四个地址的宿主全部落在 L 上。

**PV2. 🔴 交付二：0x410450 双向唯一 + 77+1 闭合.** 全 1,214 张表的**所有**槽位扫该地址，命中槽号集合恰 **{4}**（77 次，其余 33 个槽号各 0），77 张全在 mdisp==0 主表。L 的唯一例外是 `.?AVHouseTypeClass@@`（主表 0x7EAB58，槽 4 = `0x512280` = `33 C0 C2 04 00`，同 ret 4）⇒ **77 + 1 = 78**。体 6 条 `8B 4C 24 04 / 33 C0 / 8A 51 20 / 84 D2 / 0F 94 C0 / C2 04 00`；「读 +0x20 + sete」形态扫槽 5 的 546 个实现命中 **0**（反控）。

**PV3. 🔴 交付三：0x410220 的宿主类名集合与 L 严格相等.** 各 78 个、双向差集都为 0；只出现在 `(.?AUIRTTITypeInfo@@, mdisp 4)` 子表**槽 4**（78/78）。体 `8B 44 24 04 / 8B 40 0C / C2 04 00` ⇒ 读**相对接口子对象 +0xC**，折算完整对象 **+0x10**。这是 R192 未取得的「同一字段的第二个观测面」。

**PV4. 🟠 交付四：0x410590 == L，0x410580 ⊂ L 缺 3.** 0x410590 宿主类名集合与 L 严格相等，只在 `(.?AVINoticeSource@@, mdisp 12)` 槽 0（ret 4）。0x410580 是 75/78，缺 AircraftClass / InfantryClass / UnitClass，三者的 `(.?AVINoticeSink@@, mdisp 8)` 子表**都存在**，槽 0 分别覆写成 0x41BC30 / 0x522A60 / 0x746100 ⇒ **覆写不是缺层**。

**PV5. 🟠 交付五：直接引用面订正.** 0x410450 / 0x410580 / 0x410590 直接 `call rel32` + `call [abs]` 各 **0**，但 **0x410220 有 14 处**（首个 `0x413E89`）。R192「四地址直接引用均为 0 ⇒ 只经虚表调用」对 0x410220 **作废**。

**PV6. 🟠 交付六：序列化路径字节闭合.** `0x410410`（槽 13）体 15 条，顺序确定：`mov eax,[esi+0x10] … call 0x4A1D50` → `mov cl,[esi+0x20] … call 0x4A1CA0` → `ret 4`。**0x4A1D50**（7 条）= `push 4 / lea / push / call 0x4A1DE0 / ret 4`，4 字节定长块写薄壳；**0x4A1CA0**（39 条）= 逐字节写 `[eax+ecx+8]` + 计数满 4 时（`cmp eax,4`+`jne`）折进 **CRC32** 并清零，表基 **0x81F7B4**（`t[0]=0 / t[1]=0x77073096 / t[255]=0x2D02EF8D` = 标准反射表），`not eax` 出现 **2 次**、`shr eax,8` 一次；「not 前后包裹的反射实现」在 **7 样本（含空串）**上与 `zlib.crc32` 逐样本一致，不带 not 包裹则不一致 ⇒ 两次 not 语义必需。4 字节路径 0x4A1DE0（154 条）同样引用 0x81F7B4。

**PV7. 🟠 交付七：字段归属的独立字节证据.** L 里「槽 4 读 `[this+0x20]` 且槽 13 也触及 `[this+0x20]`」的表 **3 张**（0x7E1F50 / 0x7E4EEC / 0x7F4348）⇒ +0x10 与 +0x20 是同一函数里先后写出的两字段、走两条不同序列化路径。与 kb/22 的 UniqueID(+0x10)/Dirty(+0x20) 一致，但**语义名仍来自 kb/22 这一外部源**。

**PV8. 🟡 交付八：103 对「96 B 内无 ret」收口（R191/R192 待办 (c)）.** 严格口径（遇 `ret/retn` 或**指令边界上** >=2 连续 `90/CC` 即停，窗口 512 B）：`STRICT|STRICT` **78** / `STRICT|PAD` **10** / `STRICT|WINDOW_OUT` **11** / `WINDOW_OUT|STRICT` **4** / **两侧都不可判 0**。10 个 PAD 侧**全是**调整器 thunk（`83/81 6C 24 04` + `E9`），E9 落点（0x414290 / 0x4F6E60 / 0x4F6950 / 0x4F6830 / 0x410260）都有 ret ⇒ **两侧都真无 ret 的对数 = 0**。

**PV9. 🟡 交付九：口径裁定（审计基线错误）. COL d0 恒 0（signature）**、d2 恒 0；分裂主表/子表的是 **d1**：0 有 954、非 0 有 260。954 主表口径槽 4 Top1 = **0x410450(77)**；1,214 全表口径 Top1 = **0x410220(78，全在子表，主表 0 次)**。审计员 #472 用 d0 判主表得「1214/0」并把槽 13 的 `test byte[esp+0x20],2` 记成 WRITE，两点均已复算否掉。

**PV10. 🟡 落盘与门禁.** 台账 **V577 → V578**（只改 F55：stmt 13,249→**17,512 B**、lim 10,086→**13,491 B**、第 4 列 375→**508 B**、**184,812 B**、sha `5093b704…`、**17 断言 0 FAIL**）；重钉 **44 断言 0 FAIL**（旧常量复算旧 MASTER `2c70d253…` 命中旧 pin 作硬闸 → 新 MASTER **`cd0caea7…`**；`FLOORS['F55']` (13249,10086)→**(17512,13491)**、`EVID['F55']` 17→**23**、`EVIDB` 375→**508**、`ITEMS` 200→**206**、`UNIQ` 92→**98**、`LOST` 43/16 未变、gate_runner LEDGER 1 行、指针「530..577 / 48 份」→「**530..578 / 49 份**」、声明轮次 R192→**R193**）；**三门 exit 0**（`check_disc` C19 ok(5093b704/184812/V578) / C20 ok(V578)；`facts_floors` D8 floor==184,812、D9+D10 双一致；`gate_runner` G1=G2=G3=ok）。同脚本把 **§2.197（6,904 B ⇒ floor 3,452）** 钉进 C16_FLOORS（188→**189**）并重算 `C16_FLOORS_SHA256`。看板开局 **231 行 < 260** ⇒ 本轮**不归档**。

**PV11. 📌 自错（当场抓出，无一条进入结论）.** r193a 15 断言 7 FAIL / r193b 14 断言 7 FAIL，**14 条全是判据缺陷**：F1 `bcds()` 少一次解引用（pCHD+12 是指针数组不是内联数组）；F2 `md.disasm` 未在 ret 处截断（0x410450 记成 80 条）；F3 this 别名只认 `mov r,[esp+4]`，漏 `mov esi,ecx`；F4 「写」只找 `mov [mem],x`，漏 `push dword ptr [reg+0xNN]`；F5 H1 用 954 主表当分母（模板容器类根本不继承 AbstractClass）；F6 BCD 落 .rdata 却用 .data 虚拟区间筛（全空）。r193e 第一版 classify 漏「指令边界填充」判定，把 10 对的 PAD 侧判成 HAS_RET（88 vs 78），由 r193f 的 `pad_at_boundary` 修正。r193g 第一版用**表地址**比「宿主集合」，而子表地址与主表地址必然不相交 ⇒ 5 条 FAIL，改按 COL 修饰名比才对（该错误保留为反控 N1）。r193h 4 FAIL 同样是判据写成应然（`op_str` 前缀、`cmp eax,4` 写法、CRC 的 not 包裹）。

**PV12. ⚪ 未取得（不粉饰）.** ① 四个实现的**游戏语义名**仍未取得（只到接口层 + 槽号 + 参数个数）；② 「+0x10/+0x20 的流内先后顺序对应存档字段序」「CRC 覆盖范围（整段 or 分块）」未取得；③ 「`numContainedBases` 最大 = 最外层」仍无编译器侧依据；④ L 为什么恰是这 78 个类的**正面机制**未取得（本轮只给出「它们共享同一个默认实现族」这一结构事实）；⑤ **跨家族**：执行员 **#471**（hy4，60 回合 truncated，实测 6.63 分 vs 预算 3 分 OVERTIME）独立脚本在 535/1013/478/525/10 与 78/0 上与本轮一致但**未拆 PAD 档**；审计员 **#472**（deepseek，21 回合 `error_max_turns` 失败）只产出基线错误的文本，除「0x410450 槽 4 = 77」外**一律不采信**；⑥ F23/F35 grade 未改；⑦ `coverage.tsv`/`function_atlas.tsv` 仍不可读；⑧ 86.19% 原值仍不可重算；⑨ C7 三死分支仍各 0 行；⑩ C11 十二个永不 FAIL id 未动。

'''
BRD_SEC='''## 🟢 R17 第 193 轮（2026-11-28 9x–10x）· 四个高频实现落在**同一个 78 类血统集合**（77+1 闭合 / 78==L / 75⊂L 缺 3 类全为覆写）；AbstractClass 序列化路径字节闭合（+0x10 定长块写、+0x20 带 CRC32 字节流）；103 对「96B 无 ret」收口为**两侧都真无 ret = 0**

**交付一·四个数是一个集合.** 定义 **L = 954 张主表里 pCHD 基类数组含 `.?AVAbstractClass@@` 的 78 张**（按名去重仍 78）。R191/R192 的 77/78/75/78 四组数全部落在 L 上，差异只由覆写与缺层解释。

**交付二·0x410450 双向唯一 + 77+1.** 全 1,214 张表所有槽位扫描：命中集合恰 **{槽 4} × 77 张**（余 33 槽号各 0），77 张全在主表；L 的唯一例外 `.?AVHouseTypeClass@@`（主表 0x7EAB58，槽 4 = `0x512280`，同 ret 4）⇒ **77+1=78**。体 6 条 = 读 `[this+0x20]` + sete + ret 4；同形态扫槽 5 命中 **0**。

**交付三·0x410220 宿主类名集合 == L.** 78/78、双向差集 0；只在 `(.?AUIRTTITypeInfo@@, mdisp 4)` 子表槽 4；体 `8B 44 24 04 / 8B 40 0C / C2 04 00` ⇒ 读接口子对象 +0xC、折算完整对象 **+0x10**。

**交付四·0x410590 == L，0x410580 ⊂ L 缺 3.** 0x410590 只在 `(.?AVINoticeSource@@, mdisp 12)` 槽 0（ret 4）。0x410580 75/78，缺 Aircraft / Infantry / Unit，三者的 `(.?AVINoticeSink@@, mdisp 8)` 子表都在，槽 0 覆写成 0x41BC30 / 0x522A60 / 0x746100 ⇒ **覆写不是缺层**。

**交付五·直接引用订正.** 0x410450 / 0x410580 / 0x410590 各 **0** 处，但 **0x410220 有 14 处**（首个 0x413E89）⇒ R192「四地址均为 0」**作废**。

**交付六·序列化路径.** 0x410410（槽 13）先 `push [esi+0x10]; call 0x4A1D50` 再 `mov cl,[esi+0x20]; call 0x4A1CA0`，ret 4。0x4A1D50 = 4 字节定长块写薄壳（→0x4A1DE0）；0x4A1CA0（39 条）= 逐字节写 + 满 4 折进 **CRC32**（表 0x81F7B4 标准反射表 t[1]=0x77073096 / t[255]=0x2D02EF8D，`not eax` 2 次 + `shr eax,8`；not 前后包裹实现在 **7 样本**上与 zlib 一致，不带 not 则不一致）。4 字节路径 0x4A1DE0（154 条）也引用同一表。

**交付七·字段归属.** L 里「槽 4 读 [this+0x20] 且槽 13 触及 [this+0x20]」3 张（0x7E1F50 / 0x7E4EEC / 0x7F4348）⇒ +0x10 与 +0x20 同函数先后写出、两条不同序列化路径。

**交付八·103 对收口.** `STRICT|STRICT` **78** / `STRICT|PAD` **10** / `STRICT|WINDOW_OUT` **11** / `WINDOW_OUT|STRICT` **4** / 两侧都不可判 **0**；10 个 PAD 侧全是调整器 thunk（`83/81 6C 24 04`+`E9`），落点 0x414290 / 0x4F6E60 / 0x4F6950 / 0x4F6830 / 0x410260 都有 ret ⇒ **两侧都真无 ret = 0**。

**交付九·口径裁定.** COL **d0 恒 0**（signature）、d2 恒 0；分裂字段是 **d1**：954 主表 / 260 子表。主表口径槽 4 Top1 = 0x410450(77)；全表口径 Top1 = 0x410220(78，全在子表)。审计员 #472 用 d0 判主表得 1214/0 并误记 WRITE，两点均已否掉。

**落盘 · 三门.** 台账 **V577 → V578**（只改 F55：stmt 17,512 B / lim 13,491 B / 第 4 列 508 B / **184,812 B** / sha `5093b704…` / **17 断言 0 FAIL**）；重钉 **44 断言 0 FAIL**（MASTER `2c70d253…`→**`cd0caea7…`**、FLOORS (13249,10086)→**(17512,13491)**、EVID 17→**23**、EVIDB 375→**508**、ITEMS 200→**206**、UNIQ 92→**98**、LOST 43/16 未变、指针 **530..578 / 49 份**、声明轮次 **R193**）；**三门 exit 0**（C19 ok(5093b704/184812/V578) / C20 ok(V578)；D8 floor==184,812、D9+D10 双一致；G1=G2=G3=ok）。C16_FLOORS 188→**189**（钉 §2.197 floor 3,452）。看板开局 **231 < 260** ⇒ **不归档**。

**自错（当场抓出，14 条判据缺陷全部拦下）.** r193a/r193b 共 14 FAIL 全是判据缺陷：`bcds()` 少一次解引用；`md.disasm` 未在 ret 截断（0x410450 记成 80 条）；this 别名漏 `mov esi,ecx`；「写」漏 `push dword ptr [reg+off]`；H1 用 954 主表当分母（容器类不继承 AbstractClass）；BCD 在 .rdata 却按 .data 筛（全空）。r193e 第一版漏「指令边界填充」⇒ PAD 侧判成 HAS_RET（88 vs 78），由 r193f 修正。r193g 第一版用**表地址**比宿主集合（子表 vs 主表必然不相交）⇒ 5 FAIL，改按 COL 修饰名才对，该错误保留为反控 N1。r193h 4 FAIL 同样是判据写成应然。

**跨家族 · 未取得.** 执行员 **#471**（hy4，60 回合 truncated、6.63 分 vs 预算 3 分 OVERTIME）五数与本轮一致（535/1013/478/525/10）且 103 对里 78/0 一致，但**未拆 PAD 档**；审计员 **#472**（deepseek，21 回合 `error_max_turns` 失败）只产出基线错误文本，除「0x410450 槽 4 = 77」外**不采信**。未取得：① 四个实现的游戏语义名；② +0x10/+0x20 的流内顺序与 CRC 覆盖范围；③ 「ncb 最大 = 最外层」的编译器依据；④ L 恰为这 78 个类的**正面机制**；⑤ F23/F35 grade；⑥ `coverage.tsv`/`function_atlas.tsv` 仍不可读；⑦ 86.19% 原值不可重算；⑧ C7 三死分支各 0 行；⑨ C11 十二个永不 FAIL id 未动。

'''
for tag,s in (('2.198',S198),('§1248',S1248),('PV',PV),('board',BRD_SEC)):
    ck('C5 %s 反引号成对'%tag, s.count('`')%2==0, s.count('`'))
    ck('C5b %s 不含 CR'%tag, '\r' not in s)
ck('C1 R14_COMMON 尚未含 2.198', '2.198 R193' not in open(R14,encoding='utf-8',errors='replace').read())
ck('C2 台账尚未含 §1248', '§1248 R193' not in open(LED,encoding='utf-8',errors='replace').read())
ck('C3 LEAD_LOCK 尚未含 PV · R17 第 193 轮', 'PV · R17 第 193 轮' not in open(LCK,encoding='utf-8',errors='replace').read())
ck('C4 看板尚未含第 193 轮', 'R17 第 193 轮' not in open(BRD,encoding='utf-8',errors='replace').read())

def newtext(path,sec):
    b=open(path,'rb').read(); t=b.decode('utf-8')
    assert sec.count('\r')==0
    return (t.rstrip('\r\n')+'\n\n'+sec).encode('utf-8')
jobs=[('R14',R14,S198),('LED',LED,S1248),('LCK',LCK,PV),('BRD',BRD,BRD_SEC)]
plans=[]
for tag,path,sec in jobs:
    old=open(path,'rb').read()
    nb=newtext(path,sec)
    plans.append((tag,path,sec,nb))
    ck('C6 %s 追加后 CR 数与基线逐值相等'%tag, nb.count(b'\r\n')==base[tag][2], (nb.count(b'\r\n'),base[tag][2]))
    ck('C7 %s 新标记恰 1 次'%tag, nb.decode('utf-8').count(sec.split('\n')[0])==1)
    ck('C7b %s 体量按构造闭合'%tag,
       len(nb)==len(old)-(len(old)-len(old.rstrip(b'\r\n')))+2+len(sec.encode()), len(nb))
ck('C8 看板追加后行数 <= 300', plans[3][3].count(b'\n')<=300, plans[3][3].count(b'\n'))

cd=open(CD,'rb').read().decode('utf-8')
m=re.search(r'C16_FLOORS = \{\n(.*?)\n\}',cd,re.S)
F={int(k):int(v) for k,v in re.findall(r'^\s+(\d+): (\d+),',m.group(1),re.M)}
ck('C9 旧 C16_FLOORS 188 条 / 无 197', len(F)==188 and 197 not in F, (len(F),197 in F))
oldsha=re.search(r"^C16_FLOORS_SHA256 = '([0-9a-f]{64})'",cd,re.M).group(1)
ck('C9b 旧 C16_FLOORS_SHA256 == 由表重算',
   hashlib.sha256('\n'.join('%d:%d'%(k,F[k]) for k in sorted(F)).encode()).hexdigest()==oldsha)
def secsizes(txt):
    out={};cur=None;buf=[]
    for l in txt.split('\n'):
        mm=re.match(r'^##\s+2\.(\d+)\b',l)
        if mm:
            if cur is not None: out[cur]=len('\n'.join(buf).encode())
            cur=int(mm.group(1)); buf=[l]
        elif cur is not None: buf.append(l)
    if cur is not None: out[cur]=len('\n'.join(buf).encode())
    return out
sz_now=secsizes(open(R14,'rb').read().decode('utf-8',errors='replace'))
ck('C10 §2.197 现盘 6,904 B ⇒ floor 3,452', (sz_now[197],sz_now[197]//2)==(6904,3452), (sz_now[197],sz_now[197]//2))
sz198=secsizes(S198)[198]
ck('C11 §2.198 本节字节 %d > 0'%sz198, sz198>0, sz198)
F2=dict(F); F2[197]=sz_now[197]//2
newsha=hashlib.sha256('\n'.join('%d:%d'%(k,F2[k]) for k in sorted(F2)).encode()).hexdigest()
body='\n'.join('    %d: %d,'%(k,F2[k]) for k in sorted(F2))
cd2=cd[:m.start(1)]+body+cd[m.end(1):]
cd2=cd2.replace("C16_FLOORS_SHA256 = '%s'"%oldsha,"C16_FLOORS_SHA256 = '%s'"%newsha,1)
ck('C13 新 C16 表 189 条', len(F2)==189, len(F2))
ck('C13b 新 C16_FLOORS_SHA256 已换且只 1 处', cd2.count(newsha)==1 and oldsha not in cd2,
   (cd2.count(newsha), cd2.count(oldsha)))
ck('C13c 旧 188 条 floor 逐条未动', all(F2[k]==F[k] for k in F))
if fails:
    print('★ fail-closed：%d 条未过，四份都不写'%len(fails)); sys.exit(1)
print('== 写盘 ==')
stamp=time.strftime('%Y%m%d_%H%M%S')
for tag,path,sec,nb in plans:
    cur=open(path,'rb').read()
    if hashlib.sha256(cur).hexdigest()!=base[tag][1]:
        print('★ %s 已被改动，中止'%tag); sys.exit(1)
    bak=os.path.join(BL,'%s.before_r193_fourpiece_%s.bak'%(tag,stamp))
    fd=os.open(bak,os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o644)
    with os.fdopen(fd,'wb') as f: f.write(cur)
    ck('W1 %s 备份 sha 一致'%tag,
       hashlib.sha256(open(bak,'rb').read()).hexdigest()==hashlib.sha256(cur).hexdigest())
    open(path,'wb').write(nb)
    ck('W2 %s 回读一致'%tag,
       hashlib.sha256(open(path,'rb').read()).hexdigest()==hashlib.sha256(nb).hexdigest())
    ck('W3 %s 新标记恰 1 次（回读）'%tag,
       open(path,encoding='utf-8').read().count(sec.split('\n')[0])==1)
cur=open(CD,'rb').read()
if hashlib.sha256(cur).hexdigest()!=base['CD'][1]:
    print('★ check_disc.py 已被改动，中止'); sys.exit(1)
bak=os.path.join(BL,'check_disc.before_r193_c16_%s.bak'%stamp)
fd=os.open(bak,os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o644)
with os.fdopen(fd,'wb') as f: f.write(cur)
ck('W1 CD 备份 sha 一致',
   hashlib.sha256(open(bak,'rb').read()).hexdigest()==hashlib.sha256(cur).hexdigest())
open(CD,'w',encoding='utf-8',newline='').write(cd2)
ck('W2 CD 回读一致', hashlib.sha256(open(CD,'rb').read()).hexdigest()==hashlib.sha256(cd2.encode()).hexdigest())
print('\n最终:',{k:(len(open(p,'rb').read()),hashlib.sha256(open(p,'rb').read()).hexdigest()[:8],
                 open(p,'rb').read().count(b'\r\n'),open(p,'rb').read().count(b'\n'))
                for k,p in (('R14',R14),('LED',LED),('LCK',LCK),('BRD',BRD),('CD',CD))})
print('断言 %d 条，FAIL %d 条'%(n,len(fails)))
sys.exit(1 if fails else 0)
