#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R192 四件套追加（R14_COMMON §2.197 / 台账 §1247 / LEAD_LOCK PU / 看板第 192 轮）。
★ 幂等保护：写任何一份前先断言现盘 sha == 开跑基线；不等则整体 fail-closed。
★ 同时把 R14_COMMON §2.193 与 §2.196 两节按既有规则「floor = 本节字节 // 2」钉进
   check_disc.py 的 C16_FLOORS，并重算 C16_FLOORS_SHA256 —— 否则新增 §2.197 后
   unpinned 会变成 3 > C16_UNPINNED_MAX(2)。
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
ck('B1 R14 1,675,806 B / CR 1081 / sha 7b67e950…',
   base['R14'][0]==1675806 and base['R14'][2]==1081 and base['R14'][1].startswith('7b67e950'), base['R14'][:3])
ck('B2 台账 5,344,747 B / CR 337 / sha dca3043e…',
   base['LED'][0]==5344747 and base['LED'][2]==337 and base['LED'][1].startswith('dca3043e'), base['LED'][:3])
ck('B3 LEAD_LOCK 1,337,766 B / CR 137 / sha f4a2283c…',
   base['LCK'][0]==1337766 and base['LCK'][2]==137 and base['LCK'][1].startswith('f4a2283c'), base['LCK'][:3])
ck('B4 看板 44,995 B / CR 0 / 211 行 / sha f52b9672…',
   base['BRD'][0]==44995 and base['BRD'][2]==0 and base['BRD'][3]==211
   and base['BRD'][1].startswith('f52b9672'), base['BRD'][:4])

# ---------- 1) R14_COMMON §2.197 ----------
S197='''## 2.197 R192：1,013 个非 thunk 直接槽「同组同序号无匹配」的机械解释（535 对**全部跨接口层**、跳板归并 COLLAPSE **0**、295 对 ret 立即数不同）；并给出四个高频实现的**结构身份**

**一、先把「同组」这件事测清楚.** 1,013 个直接槽按「同 COL 修饰名、不同表、且该槽号在兄弟表里也存在」取表地址最小的兄弟表，分三类：**NOSIB 478**（一个兄弟表都没有该槽号）、**DIRECT_OTHER 525**（兄弟槽是直接指针且值不同）、**THUNK_OTHER 10**（兄弟槽是调整器但 jmp 目标不同）、**SAME 0**。可比对的对共 **535**。

**二、535 对全部跨层，且全部跨接口层.** （i）两边 `COL.offset-to-top`（= COL 第 2 个 dword）不同的对 **535/535**；（ii）把每张表的「层基类身份」定义为 pCHD 基类数组里 `PMD.mdisp == COL.offset-to-top` 的那条 BCD，多条候选时取 `numContainedBases` 最大的一条（1,214 条 COL **全部解出唯一一条**，并列 **0**），其 pTD 名即层基类名；则 535 对里两边层基类名相同的 **0** 对。前六层基类对：`INoticeSink→INoticeSource` 75 / `INoticeSource→INoticeSink` 73 / `UIPiggyback→UILocomotion` 30 / `UILocomotion→UIPiggyback` 30 / `UILocomotion→{Fly,Hover,Locomotion,Mech,Rocket,Tunnel}LocomotionClass` 各 7。⇒ R191 ⑩ 里那句「没有同组同序号匹配」的正确读法是：**这 535 对压根不是「同组」，而是「同一宿主类的两个不同接口层在同一个槽号上」**。

**三、不存在「不同 thunk 壳包同一 impl」.** 把两目标的地址各自跟随无条件跳转（`E9 rel32` / `EB rel8` / `FF 25` 绝对间址，带环与越界保护）后比对：**1 跳口径 COLLAPSE 0 / DISTINCT 535，8 跳口径同样 0 / 535**；且 535 对的两侧目标**本身没有一个**是跳板（v 是跳板 0、w 是跳板 0）。反控：canon 换成恒等函数仍为 0（因为 525 对的两边值本来就不同）；只跟 `E9` 仍为 0；把兄弟值人为替换成自身值 ⇒ 分类改判 SAME（正控）。

**四、至少 295 对在调用约定层面就不可能共用同一入口.** 两侧目标的结尾 `ret` 立即数 **不同 295 对 / 相同 137 对 / 96 字节窗口内解不到 ret 103 对**；两侧前 16 字节**完全相同 0 对**。最典型：`INoticeSink`@mdisp 8 槽 0 = `0x410580`（`32 C0 C2 08 00` = xor al,al; ret 8，75 个类共用）与 `INoticeSource`@mdisp 12 槽 0 = `0x410590`（`C2 04 00` = ret 4，78 个类共用）—— 同槽号、不同接口、不同参数个数。

**五、接口子表层的槽一致性首次量化.** 键 = (层基类名, offset-to-top, 槽号)。260 张接口子表上共 **110** 个键：单宿主 **43**、多宿主 **67**（覆盖 **1,275** 个槽实例，其中调整器 288 + 直接槽 987）。键内取值**完全一致**的只有 **6** 个键，众数覆盖 **1,037/1,275 = 81.33%**。含主表的全镜像口径键数 **12,836**。主表侧另算：主表 954 张、槽 **12,726**；主表槽 4 的 954 个实现里 Top1 = `0x410450`（77），主表槽 0 的 954 个实现里 Top1 = `0x410260`（75）、不同实现 **863** 个。

**六、四个高频实现的**结构身份**（不猜游戏语义名）.** `0x410450`（`8B 4C 24 04 / 33 C0 / 8A 51 20 / 84 D2 / 0F 94 C0 / C2 04 00` = 读 this+0x20 字节、返回「该字节为 0」、ret 4）被 **77** 个槽引用，**77 个全在主表槽 4**，宿主类 77 个（每个类一次）；`0x410580`（`32 C0 C2 08 00` = xor al,al; ret 8）被 **75** 个槽引用，**75 个全在 `INoticeSink` 层槽 0**；`0x410590`（`C2 04 00` = ret 4）被 **78** 个槽引用，**78 个全在 `INoticeSource` 层槽 0**；`0x4C9150`（`33 C0 C3` = xor eax,eax; ret）被 **205** 个槽引用，**跨 33 个槽号**、**38 个宿主类**，其中 204 个在 offset-to-top==0 的主表、只有 1 个在 mdisp==4。四个地址在 `.text` 里被**直接** `call rel32` 与 `call [abs]` 引用的次数**全部为 0** —— 只经虚表调用。⇒ 语义名仍**未取得**，但「0x410580 是 INoticeSink 槽 0、0x410590 是 INoticeSource 槽 0」是结构判定，不是猜测。

**七、边界（不粉饰）.** （a）「层基类身份」是**结构判据不是语义判据**，不说明任何槽的语义名；（b）260 条非零 offset-to-top 的 COL 里 **159 条**层 BCD 候选唯一、**101 条**有 2 条候选（如 mdisp 4 上同时有 UIRTTITypeInfo（ncb 1）与 IUnknown（ncb 0）、mdisp 1728 上同时有 UIFlyControl（ncb 1）与 IUnknown（ncb 0）），「取 ncb 最大 = 最外层」在 101 条上**全部消解为唯一**，但这条规则本身**未取得**编译器侧依据，只证明它与「954 条 mdisp==0 表的首条 BCD 自证」口径一致；若改成「取第一条」，101 条会落到 IUnknown，接口键数从 110 掉到 43 —— 规则敏感，故显式写出；（c）「103 对 96 字节内解不到 ret」的口径是「线性反汇编，遇 jmp/int3/hlt 或窗口耗尽即判无 ret」，且 535 对两侧目标全部不是跳板，所以不是「跳板后面有 ret」，但**未**逐对做完整函数边界分析 ⇒「103 对里有多少真的没有 ret」未取得；（d）「众数覆盖 81.33%」的分母是 67 个多宿主键覆盖的 1,275 个实例，43 个单宿主键**不进分母**（它们恒 100%，计入会把覆盖率抬到 98%+，属口径混淆）；（e）把兄弟判据从「同 COL 修饰名」换成「同 pTD」时键空间从 954 组变 988 个 pTD，本轮**只做了键数核对**，未重跑五类分类。

**八、落盘与门禁.** 台账 **V576 → V577**：只改 F55 一行，第 ⑪ 段与 limitations 追加同批边界段 —— statement 10,455 → **13,249 B**、limitations 7,691 → **10,086 B**、第 4 列 311 → **375 B**，**177,011 B（+5,253）/ 57 行 5 列 / CR 0 / sha `81b3e116…`**（17 断言 0 FAIL）。重钉 **44 断言 0 FAIL**：旧常量复算旧 MASTER `86874cbe…` 命中旧 pin 作硬闸 → 新 MASTER **`2c70d253…`**；`FLOORS['F55']` (10455,7691)→**(13249,10086)**、`EVID['F55']` 14→**17** 条、`EVIDB['F55']` 311→**375**、`ITEMS` 197→**200**、`UNIQ` 89→**92**、`LOST` 保持 **43/16**、gate_runner LEDGER 1 行、指针四字段（「530..576 / 47 份」→「**530..577 / 48 份**」、声明轮次 R191→**R192**）。**三门 exit 0**：`check_disc`（C19 ok(81b3e116/177011/V577) / C20 ok(V577)）、`facts_floors`（D7 items=200 uniq=92、D8 floor==177,011、D9+D10 双一致）、`gate_runner`（G1=G2=G3=ok）。同一脚本把 R14_COMMON **§2.193（29,667 B ⇒ floor 14,833）**与 **§2.196（6,497 B ⇒ floor 3,248）**按既有规则「floor = 本节字节 // 2」钉进 `check_disc.py` 的 C16_FLOORS（186 → **188** 条）并重算 `C16_FLOORS_SHA256`，否则新增 §2.197 后 unpinned 会变 3 > `C16_UNPINNED_MAX`(2)。

'''
# ---------- 2) 台账 §1247 ----------
S1247='''## §1247 R192：1,013 直接槽「同组同序号无匹配」的机械解释 —— 535 对全部跨接口层、跳板归并 COLLAPSE 0、295 对 ret 立即数不同；四个高频实现的结构身份

**一、五类.** NOSIB **478** / DIRECT_OTHER **525** / THUNK_OTHER **10** / SAME **0**，可比对 **535** 对。三类互斥且合计 1,013。

**二、不是「同组」而是「跨接口层同槽号」.** 535 对两边 offset-to-top 不同 **535/535**；用「pCHD 基类数组里 PMD.mdisp == COL.offset-to-top、多条取 numContainedBases 最大」定义层基类身份（1,214 条 COL 全部唯一解、并列 0），则两侧层基类名相同 **0** 对。前六：INoticeSink→INoticeSource 75 / 反向 73 / UIPiggyback↔UILocomotion 各 30 / UILocomotion→六个 LocomotionClass 各 7。

**三、跳板归并.** 1 跳与 8 跳口径 COLLAPSE 均 **0/535**；两侧目标本身是跳板的 **0** 个。反控：恒等 canon ⇒ 0（正控：兄弟值换成自身值 ⇒ 改判 SAME）；只跟 E9 ⇒ 0。

**四、调用约定.** 两侧 ret 立即数不同 **295** / 相同 **137** / 96 B 内无 ret **103**；前 16 字节全同 **0** 对。

**五、接口子表键一致性.** (层基类名, offset-to-top, 槽号) 在 260 张接口子表上 **110** 个键（单宿主 43 / 多宿主 67，覆盖 1,275 槽实例 = 调整器 288 + 直接槽 987）；键内完全一致 **6** 个、众数覆盖 **1,037/1,275 = 81.33%**；全镜像键 **12,836**。主表 954 张 / 槽 12,726；主表槽 4 Top1 `0x410450`(77)、槽 0 Top1 `0x410260`(75)、槽 0 不同实现 **863**。

**六、四个实现的结构身份.** `0x410450` 77 槽**全在主表槽 4**；`0x410580` 75 槽**全在 INoticeSink 层槽 0**（ret 8）；`0x410590` 78 槽**全在 INoticeSource 层槽 0**（ret 4）；`0x4C9150` 205 槽跨 **33** 个槽号、**38** 个宿主类（204 在主表）。四地址直接 call rel32 与 call [abs] 引用**均为 0**，只经虚表调用。

**七、落盘.** 台账 V576→V577（stmt 13,249 B / lim 10,086 B / 第4列 375 B / 177,011 B / sha `81b3e116…` / 17 断言 0 FAIL）；重钉 44 断言 0 FAIL（MASTER `86874cbe…`→`2c70d253…`、ITEMS 200 / UNIQ 92 / EVID 17 条 / EVIDB 375 / LOST 43-16 / 指针 530..577、48 份、R192）；三门 exit 0。C16_FLOORS 186→188（钉 §2.193 floor 14,833、§2.196 floor 3,248）。

**八、未取得.** 四个实现的**游戏语义名**（本轮只给结构身份：接口层 + 槽号 + 参数个数）；「为什么这 5 个基类不需要副表」的机制；「ncb 最大 = 最外层」的编译器侧依据；103 对无 ret 里真无 ret 的数量。

'''
# ---------- 3) LEAD_LOCK PU ----------
PU='''## PU · R17 第 192 轮（2026-11-28 8x–9x）· 1,013 直接槽「同组同序号无匹配」的机械解释落成：535 对**全部跨接口层**、跳板归并 COLLAPSE **0**、**295** 对 ret 立即数不同；并给出四个高频实现的**结构身份**（不猜游戏语义名）

**PU1. 🔴 交付一：五类分齐，SAME 为 0.** 按「同 COL 修饰名、不同表、该槽号在兄弟表里也存在」取表地址最小的兄弟表：**NOSIB 478 / DIRECT_OTHER 525 / THUNK_OTHER 10 / SAME 0**，可比对 **535** 对。

**PU2. 🔴 交付二：535 对压根不是「同组」.** 两侧 `COL.offset-to-top` 不同 **535/535**。用「pCHD 基类数组里 `PMD.mdisp == COL.offset-to-top`、多条取 `numContainedBases` 最大」定义**层基类身份**（1,214 条 COL 全部唯一解、并列 **0**），则两侧层基类名相同的 **0** 对。前六层基类对：`INoticeSink→INoticeSource` 75 / 反向 73 / `UIPiggyback↔UILocomotion` 各 30 / `UILocomotion→{Fly,Hover,Locomotion,Mech,Rocket,Tunnel}LocomotionClass` 各 7。⇒ R191 ⑩ 那句「没有同组同序号匹配」的正确读法是「同一宿主类的两个不同接口层撞在同一个槽号上」。

**PU3. 🟠 交付三：跳板归并不产生折叠.** 两侧目标各自跟随 `E9 rel32`/`EB rel8`/`FF 25` 绝对间址（带环与越界保护）：**1 跳口径 COLLAPSE 0 / DISTINCT 535，8 跳口径 0 / 535**；两侧目标本身是跳板的 **0** 个。反控：恒等 canon ⇒ 0（正控：兄弟值换成自身值 ⇒ 改判 SAME）；只跟 `E9` ⇒ 0。

**PU4. 🟠 交付四：至少 295 对调用约定不兼容.** 两侧 ret 立即数**不同 295 / 相同 137 / 96 B 窗口内无 ret 103**；前 16 字节全同 **0** 对。最典型：`INoticeSink`@8 槽 0 = `0x410580`（ret 8，75 类共用）vs `INoticeSource`@12 槽 0 = `0x410590`（ret 4，78 类共用）。

**PU5. 🟠 交付五：接口子表键一致性首次量化.** (层基类名, offset-to-top, 槽号) 在 260 张接口子表上 **110** 键（单宿主 43 / 多宿主 67，覆盖 **1,275** 槽实例 = 调整器 288 + 直接槽 987）；键内完全一致 **6** 个、众数覆盖 **1,037/1,275 = 81.33%**；全镜像键 **12,836**。主表 954 张 / 槽 **12,726**；主表槽 4 Top1 `0x410450`(77)、槽 0 Top1 `0x410260`(75)、槽 0 不同实现 **863**。

**PU6. 🟠 交付六：四个实现的**结构身份**（不猜名）.** `0x410450`（`8B 4C 24 04 / 33 C0 / 8A 51 20 / 84 D2 / 0F 94 C0 / C2 04 00`，读 this+0x20、返回该字节为 0、ret 4）**77 槽全在主表槽 4**；`0x410580`（`32 C0 C2 08 00`）**75 槽全在 INoticeSink 层槽 0**；`0x410590`（`C2 04 00`）**78 槽全在 INoticeSource 层槽 0**；`0x4C9150`（`33 C0 C3`）**205 槽跨 33 个槽号 / 38 个宿主类**（204 在主表）。四地址被**直接** `call rel32` 与 `call [abs]` 引用**均为 0** ⇒ 只经虚表调用。

**PU7. 🟡 落盘与门禁.** 台账 **V576 → V577**（只改 F55：stmt 10,455→**13,249 B**、lim 7,691→**10,086 B**、第4列 311→**375 B**、**177,011 B**、sha `81b3e116…`、**17 断言 0 FAIL**）；重钉 **44 断言 0 FAIL**（旧常量复算旧 MASTER `86874cbe…` 命中旧 pin 作硬闸 → 新 MASTER **`2c70d253…`**；`FLOORS['F55']` (10455,7691)→**(13249,10086)**、`EVID['F55']` 14→**17**、`EVIDB` 311→**375**、`ITEMS` 197→**200**、`UNIQ` 89→**92**、`LOST` 43/16 未变、指针「530..576 / 47 份」→「**530..577 / 48 份**」、声明轮次 R191→**R192**）；**三门 exit 0**（`check_disc` C19 ok(81b3e116/177011/V577) / C20 ok(V577)；`facts_floors` D7 items=200 uniq=92、D8 floor==177,011、D9+D10 双一致；`gate_runner` G1=G2=G3=ok）。同脚本把 R14_COMMON **§2.193（29,667 B ⇒ floor 14,833）**与 **§2.196（6,497 B ⇒ floor 3,248）**按既有规则「floor = 本节字节 // 2」钉进 C16_FLOORS（186→**188**）并重算 `C16_FLOORS_SHA256`，否则新增 §2.197 后 unpinned 会变 3 > `C16_UNPINNED_MAX`(2)。看板本轮开局 **266 行 ≥ 260** ⇒ 先把最早两段（R182、R183，共 55 行）搬到 `BOARD_ARCHIVE.md`（21 断言 0 FAIL），追加后 **211 + 本轮段** 仍 ≤ 300。

**PU8. ⚪ 未取得（不粉饰）.** ① 四个实现的**游戏语义名**仍未取得（只到接口层 + 槽号 + 参数个数，**没有**装任何语义名）；② 「为什么这 5 个基类不需要副表」的机制未取得；③ 「`numContainedBases` 最大 = 最外层」这条规则的编译器侧依据未取得（只证明它在 101 条双候选上消解为唯一，且与 954 条主表首条 BCD 自证口径一致）；④ 「103 对 96 字节内无 ret」里真正没有 ret 指令的对数未取得（未做完整函数边界分析）；⑤ 审计员 **#467/#468**（deepseek）分别跑满 **23 / 21 回合** `error_max_turns` 失败，只有第三张极窄卡 **#469** 成功（0.88 分、10 回合），因此本轮**只有一条主张**通过跨家族复核（非主表 260 张 / 槽 1,318 / 调整器 305 / 直接槽 1,013 —— 审计员独立复算逐值一致，并额外指出「命中判定必须先解引用槽再比 4 字节」这个实现陷阱）；其余五条主张**无第二家族复核**；⑥ F23/F35 grade 未改；⑦ `coverage.tsv`/`function_atlas.tsv` 仍不可读；⑧ 86.19% 原值仍不可重算；⑨ C7 三死分支仍各 0 行；⑩ C11 十二个永不 FAIL id 未动。

'''
# ---------- 4) 看板第 192 轮 ----------
BRD_SEC='''## 🟢 R17 第 192 轮（2026-11-28 8x–9x）· R191 留下的「1,013 直接槽无同组同序号匹配」被做成**机械解释**：535 对**全部跨接口层**、跳板归并 COLLAPSE **0**、**295 对** ret 立即数不同；四个高频实现给出**结构身份**（不猜语义名）

**交付一·五类分齐.** `_r192/r192e_deliver.py`（**32 断言 0 FAIL**）：**NOSIB 478 / DIRECT_OTHER 525 / THUNK_OTHER 10 / SAME 0**，可比对 **535** 对。

**交付二·不是「同组」而是「跨接口层同槽号」.** 两侧 offset-to-top 不同 **535/535**；用「pCHD 基类数组里 `PMD.mdisp == COL.offset-to-top`、多条取 `numContainedBases` 最大」定义层基类身份（1,214 条 COL 唯一解、并列 **0**），两侧层基类名相同 **0** 对。前六：`INoticeSink→INoticeSource` 75 / 反向 73 / `UIPiggyback↔UILocomotion` 各 30 / `UILocomotion→六个 LocomotionClass` 各 7。

**交付三·跳板归并 0 折叠.** 两侧目标各自跟随 `E9 rel32`/`EB rel8`/`FF 25`（带环与越界保护）：1 跳与 8 跳口径 COLLAPSE 均 **0/535**；两侧目标本身是跳板的 **0** 个。反控：恒等 canon ⇒ 0（正控：兄弟值换成自身值 ⇒ 改判 SAME）；只跟 `E9` ⇒ 0。

**交付四·调用约定.** 两侧 ret 立即数**不同 295 / 相同 137 / 96 B 内无 ret 103**；前 16 字节全同 **0** 对。

**交付五·接口子表键一致性.** (层基类名, offset-to-top, 槽号) 在 260 张接口子表上 **110** 键（单宿主 43 / 多宿主 67，覆盖 **1,275** 槽实例 = 调整器 288 + 直接槽 987）；键内完全一致 **6** 个、众数覆盖 **1,037/1,275 = 81.33%**；全镜像键 **12,836**。主表 954 张 / 槽 **12,726**；主表槽 4 Top1 `0x410450`(77)、槽 0 Top1 `0x410260`(75)、槽 0 不同实现 **863**。

**交付六·四个实现的结构身份（不猜名）.** `0x410450` 77 槽**全在主表槽 4**；`0x410580` 75 槽**全在 INoticeSink 层槽 0**（ret 8）；`0x410590` 78 槽**全在 INoticeSource 层槽 0**（ret 4）；`0x4C9150` 205 槽跨 **33** 个槽号 / **38** 个宿主类（204 在主表）。四地址被直接 `call rel32` / `call [abs]` 引用**均为 0** ⇒ 只经虚表调用。

**落盘 · 三门 · 归档.** 看板开局 **266 ≥ 260** ⇒ 先归档最早两段（R182、R183，55 行，**21 断言 0 FAIL**，归档 1,419,491 B / 看板 44,995 B / 211 行）。台账 **V576 → V577**（只改 F55：stmt 13,249 B / lim 10,086 B / 第4列 375 B / **177,011 B** / sha `81b3e116…` / **17 断言 0 FAIL**）；重钉 **44 断言 0 FAIL**（MASTER `86874cbe…`→**`2c70d253…`**、FLOORS (10455,7691)→**(13249,10086)**、EVID 14→**17**、EVIDB 311→**375**、ITEMS 197→**200**、UNIQ 89→**92**、LOST 43/16 未变、指针 **530..577、48 份**、声明轮次 **R192**）；**三门 exit 0**（C19 ok(81b3e116/177011/V577) / C20 ok(V577)；D7 items=200 uniq=92、D8 floor==177,011、D9+D10 双一致；G1=G2=G3=ok）。同脚本把 **§2.193（floor 14,833）/ §2.196（floor 3,248）**钉进 C16_FLOORS（186→**188**）并重算 `C16_FLOORS_SHA256`。

**自错两处（当场抓出）：** s1 第一版把接口子表键数按直觉预填 **704**、单宿主键 **637**，实测 **110 / 43** —— 「把应然数当实测」再犯一次；s2 `r192f_archive.py` 由 `_r190` 改写时漏改 A4/A11/A12/A13/N2 五处断言里的段号字符串，运行后全部 PASS 是因为改前先把 `179/180` 批量替换成 `182/183` —— 但 `A13` 原写「以 R189 段结尾」被替换成「以 R189 段结尾」的等价错位，靠 `A13 看板仍以 R191 段结尾` 实测输出才看出来（该断言此时已由我手动改成 R191 才 PASS，属**改后验证**而非**改前发现**，记为流程瑕疵）。

**未取得**：① 四个实现的游戏语义名仍未取得（只到接口层 + 槽号 + 参数个数）；② 「为什么这 5 个基类不需要副表」的机制；③ 「ncb 最大 = 最外层」的编译器侧依据；④ 103 对无 ret 里真无 ret 的数量；⑤ 审计员 **#467/#468**（deepseek）**23 / 21 回合** `error_max_turns` 失败，仅第三张极窄卡 **#469** 成功（0.88 分）⇒ 本轮**只有一条主张**（260/1,318/305/1,013）过跨家族复核，其余五条**无第二家族复核**；⑥ F23/F35 grade 未改；⑦ `coverage.tsv`/`function_atlas.tsv` 仍不可读；⑧ 86.19% 原值不可重算；⑨ C7 三死分支各 0 行；⑩ C11 十二个永不 FAIL id 未动。

'''
for tag,s in (('2.197',S197),('§1247',S1247),('PU',PU),('board',BRD_SEC)):
    ck('C5 %s 反引号成对'%tag, s.count('`')%2==0, s.count('`'))
    ck('C5b %s 不含 CR'%tag, '\r' not in s)
ck('C1 R14_COMMON 尚未含 2.197', '2.197 R192' not in open(R14,encoding='utf-8',errors='replace').read())
ck('C2 台账尚未含 §1247', '§1247 R192' not in open(LED,encoding='utf-8',errors='replace').read())
ck('C3 LEAD_LOCK 尚未含 PU · R17 第 192 轮', 'PU · R17 第 192 轮' not in open(LCK,encoding='utf-8',errors='replace').read())
ck('C4 看板尚未含第 192 轮', 'R17 第 192 轮' not in open(BRD,encoding='utf-8',errors='replace').read())

def newtext(path,sec):
    b=open(path,'rb').read(); t=b.decode('utf-8')
    assert sec.count('\r')==0
    return (t.rstrip('\r\n')+'\n\n'+sec).encode('utf-8')
jobs=[('R14',R14,S197),('LED',LED,S1247),('LCK',LCK,PU),('BRD',BRD,BRD_SEC)]
plans=[]
for tag,path,sec in jobs:
    old=open(path,'rb').read()
    nb=newtext(path,sec)
    plans.append((tag,path,sec,nb))
    ck('C6 %s 追加后 CR 数与基线逐值相等'%tag, nb.count(b'\r\n')==base[tag][2], (nb.count(b'\r\n'),base[tag][2]))
    ck('C7 %s 新标记恰 1 次'%tag, nb.decode('utf-8').count(sec.split('\n')[0])==1)
    ck('C7b %s 体量按构造闭合'%tag,
       len(nb)==len(old)-(len(old)-len(old.rstrip(b'\r\n')))+2+len(sec.encode()),
       len(nb))
ck('C8 看板追加后行数 <= 300', plans[3][3].count(b'\n')<=300, plans[3][3].count(b'\n'))

# ---------- C16 重钉 ----------
cd=open(CD,'rb').read().decode('utf-8')
m=re.search(r'C16_FLOORS = \{\n(.*?)\n\}',cd,re.S)
F={int(k):int(v) for k,v in re.findall(r'^\s+(\d+): (\d+),',m.group(1),re.M)}
ck('C9 旧 C16_FLOORS 186 条 / 无 193 与 196', len(F)==186 and 193 not in F and 196 not in F, (len(F),193 in F,196 in F))
oldsha=re.search(r"^C16_FLOORS_SHA256 = '([0-9a-f]{64})'",cd,re.M).group(1)
ck('C9b 旧 C16_FLOORS_SHA256 == 由表重算', hashlib.sha256('\n'.join('%d:%d'%(k,F[k]) for k in sorted(F)).encode()).hexdigest()==oldsha)
# 新节 2.197 的字节数（先算出，用于 unpinned 检查）
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
sz197=secsizes(S197)[197]
sz193=secsizes(open(R14,'rb').read().decode('utf-8',errors='replace'))[193]
sz196=secsizes(open(R14,'rb').read().decode('utf-8',errors='replace'))[196]
F2=dict(F); F2[193]=sz193//2; F2[196]=sz196//2
ck('C10 §2.193 29,667 B ⇒ floor 14,833', (sz193,sz193//2)==(29667,14833), (sz193,sz193//2))
ck('C11 §2.196 6,497 B ⇒ floor 3,248', (sz196,sz196//2)==(6497,3248), (sz196,sz196//2))
ck('C12 §2.197 本节字节 %d ⇒ 钉前 unpinned 会变 1'%sz197, sz197>0, sz197)
newsha=hashlib.sha256('\n'.join('%d:%d'%(k,F2[k]) for k in sorted(F2)).encode()).hexdigest()
body='\n'.join('    %d: %d,'%(k,F2[k]) for k in sorted(F2))
cd2=cd[:m.start(1)]+body+cd[m.end(1):]
cd2=cd2.replace("C16_FLOORS_SHA256 = '%s'"%oldsha,"C16_FLOORS_SHA256 = '%s'"%newsha,1)
ck('C13 新 C16 表 188 条', len(F2)==188, len(F2))
ck('C13b 新 C16_FLOORS_SHA256 已换且只 1 处',
   cd2.count(newsha)==1 and oldsha not in cd2, (cd2.count(newsha), cd2.count(oldsha)))
ck('C13c 旧 186 条 floor 逐条未动', all(F2[k]==F[k] for k in F))
if fails:
    print('★ fail-closed：%d 条未过，四份都不写'%len(fails)); sys.exit(1)
print('== 写盘 ==')
stamp=time.strftime('%Y%m%d_%H%M%S')
for tag,path,sec,nb in plans:
    cur=open(path,'rb').read()
    if hashlib.sha256(cur).hexdigest()!=base[tag][1]:
        print('★ %s 已被改动，中止'%tag); sys.exit(1)
    bak=os.path.join(BL,'%s.before_r192_fourpiece_%s.bak'%(tag,stamp))
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
bak=os.path.join(BL,'check_disc.before_r192_c16_%s.bak'%stamp)
fd=os.open(bak,os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o644)
with os.fdopen(fd,'wb') as f: f.write(cur)
ck('W1 check_disc 备份 sha 一致',
   hashlib.sha256(open(bak,'rb').read()).hexdigest()==hashlib.sha256(cur).hexdigest())
io.open(CD,'w',encoding='utf-8',newline='').write(cd2)
ck('W2 check_disc 回读一致',
   hashlib.sha256(open(CD,'rb').read()).hexdigest()==hashlib.sha256(cd2.encode()).hexdigest())
print('\n断言 %d 条，FAIL %d 条'%(n,len(fails)))
for tag,path,sec,nb in plans:
    b=open(path,'rb').read()
    print('  %s %d B / CR %d / LF %d'%(tag,len(b),b.count(b'\r\n'),b.count(b'\n')))
print('  C16 186 -> 188 条 / sha %s -> %s'%(oldsha[:16],newsha[:16]))
sys.exit(1 if fails else 0)
