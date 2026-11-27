# -*- coding: utf-8 -*-
"""R185 HH：四件套追加（fail-closed：旧 sha + CR 硬闸，全部断言在写盘之前）。
顺序：先归档看板最早 2 段到 BOARD_ARCHIVE（保持 CR=2952），再追加四件套。
  R14_COMMON.md  ## 2.190   (CR 1081)
  台账           ## §1240   (CR 337)
  LEAD_LOCK      ## PO · R17 第 185 轮 (CR 137)
  STATUS_BOARD   第 185 轮记录 (CR 0, 行数 <= 300)
"""
import hashlib,io,os,sys,time
ROOT='/home/t628/projects/ra2-campaign-forge'
TIER=os.path.join(ROOT,'lead/next_re_20261117_r14')
BL=os.path.join(TIER,'R17_LEAD_BASELINE')
RC=os.path.join(TIER,'R14_COMMON.md')
LED=os.path.join(ROOT,'lead/GOAL_THREE_TARGETS_20261018.md')
LOCK=os.path.join(ROOT,'lead/LEAD_LOCK')
BRD=os.path.join(TIER,'STATUS_BOARD.md')
ARC=os.path.join(TIER,'BOARD_ARCHIVE.md')
stamp=time.strftime('%Y%m%d_%H%M%S')
HARD={RC:1081,LED:337,LOCK:137,BRD:0,ARC:2952}
fails=[];n=0
def ck(nm,c,d=''):
    global n;n+=1
    if not c: fails.append(nm)
    print(('PASS ' if c else 'FAIL ')+nm+((' | '+str(d)) if d!='' else ''))
pre={}
for p,cr in HARD.items():
    b=open(p,'rb').read(); pre[p]=b
    ck('H0 %s 存在且 CR == %d'%(os.path.basename(p),cr), b.count(b'\r')==cr, b.count(b'\r'))
rc=io.open(RC,encoding='utf-8',newline='').read()
led=io.open(LED,encoding='utf-8',newline='').read()
lock=io.open(LOCK,encoding='utf-8',newline='').read()
brd=io.open(BRD,encoding='utf-8',newline='').read()
arc=io.open(ARC,encoding='utf-8',newline='').read()
ck('H1 R14_COMMON 末节 == 2.189', rc.rstrip().split('\n')[-1].startswith('## 2.189') or '\n## 2.189' in rc[-40000:], rc.rstrip().split('\n')[-1][:40])
ck('H2 台账末节 == §1239', led.rstrip().split('\n')[-1][:30]=='## §1239 R184：F24 那 14 B 的偏移集合按算术唯一定出，三处字节标签与一处裸计数就地订正（V564 → V565）' or '\n## §1239' in led[-60000:], led.rstrip().split('\n')[-1][:30])
ck('H3 LEAD_LOCK 末段码 == PN', lock.rstrip().split('\n\n')[-1].startswith('## PN · R17 第 184 轮') or '## PN · R17 第 184 轮' in lock[-30000:])
ck('H4 看板 274 行 >= 260 ⇒ 必须先归档两段', brd.count('\n')==274, brd.count('\n'))
ck('H5 归档现 CR 2952 且以 LF 结尾（母本末有 1 空行）', arc.count('\r')==2952 and arc.endswith('\n'), (arc.count('\r'), repr(arc[-3:])))

# ---- 归档看板最早两段（文件顺序前两节）----
lines=brd.split('\n')
if lines and lines[-1]=='': lines=lines[:-1]
idx=[i for i,l in enumerate(lines) if l.startswith('## ')]
ck('H6 看板有 11 个轮次段', len(idx)==11, len(idx))
cut=idx[2] if len(idx)>2 else len(lines)
head2=lines[:cut]; rest=lines[cut:]
ck('H7 归档段恰 2 节（R181 + R174）', sum(1 for l in head2 if l.startswith('## '))==2, sum(1 for l in head2 if l.startswith('## ')))
ck('H8 归档段第 1 节是 R181、第 2 节是 R174',
   head2[0].startswith('## 🟢 R17 第 181 轮') and head2[idx[1]].startswith('## 🔵 R17 第 174 轮'),
   (head2[0][:24], head2[idx[1]][:24]))
arch_block='\n'.join(head2).rstrip('\n')
new_arc=arc.rstrip('\n')+'\n\n'+arch_block+'\n'
ck('H9 归档后 CR 保持 2952', new_arc.count('\r')==2952, new_arc.count('\r'))
ck('H10 归档块字节 = 原看板前 %d 行'%cut, len(arch_block.encode())>0, len(arch_block.encode()))
ck('H11 归档增长为正、无字节丢失', len(new_arc.encode())>len(arc.encode()))
new_brd='\n'.join(rest)
ck('H12 移除两段后看板剩 %d 行（= 274 − %d）'%(len(rest),cut), len(rest)==274-cut, len(rest))
ck('H13 剩余首节是 R175', rest[0].startswith('## 🔵 R17 第 175 轮'), rest[0][:24])

SEC_COMMON='''
## 2.190 R185：gamemd.exe 类对象模型四条字节链全量复原（954 个 vtable / 1214 个 COL / 988 个 TD / 2615 条 BCD），并测出 symbols.json 的 vtable_va 对 12 条语义不同

R185 的入口是用户裁定的第一优先级：gamemd.exe 静态二进制本体取证。本轮选定的目标是「类对象模型的四条字节链」，即 vtable → COL → TypeDescriptor → ClassHierarchyDescriptor → BaseClassDescriptor，全部从字节重算，不引用任何既有报告里的派生数字。

**一·四条链各自的形状与全量通过率.** `_r185/r185v_final.py`（**27 断言 0 FAIL**）把链条切成四段，每段都是可失败的：A1 每个 vtable 的**前一个 dword** 是一个合法 MSVC CompleteObjectLocator，五元组为 {signature ∈ {0,1}, mdisp, pdisp, pTD ∈ .data, pCHD ∈ .rdata} —— 954/954 全通过；B 该 pTD 指向 TypeDescriptor，首 dword 恒为 **0x7F9594**（即 .data 里 type_info 虚表）、次 dword 恒 **0**、名字串内联在 TD+8，去前缀后缀后与 symbols.json 的 name 字段 **954/954** 相等；C vtable 的连续 `.text` 槽长度与 `vfunc_count` **954/954** 相等、逐槽地址也 **954/954** 相等，954 张表共 **13,204** 个函数指针槽；E 954 条的 CHD（{sig 0, attr, numBase≥1, pBaseArray ∈ .rdata}）与 BCD 数组全可解，BCD 条目共 **2,615** 条。

**二·全镜像 census 与 F01 的两个旧数.** `_r185/r185z_colcensus.py`（**11 断言 0 FAIL**）不依赖 symbols.json 独立枚举：TD **988**（`.?AV` 962 / `.?AU` 26）、总 COL **1,214**、被 `dword[vt−4]` 指回的 distinct COL **1,214**、主 COL（mdisp==0 每 TD 一个）**954**、无任何 COL 指向的 TD **34** —— 与 R140 的订正值逐项相同，而 F01 statement 里的 **1201 / 1211** 仍不可复现；1211 只能由「`COL+4 <= 0x1000`」这一事后阈值得到，被剔除的恰 **3** 个、其 `COL+4` 全为 `0x5518`（MouseClass `0x7FA9B8` / TabClass `0x805E48` / ScrollClass `0x809008`）—— `_r185/r185bb_257.py`（**7 断言 0 FAIL**）同时首次逐数复现了 F01/F31 limitations 记的「257/1211」：`dword[COL−4]==0` 在 1,214 上是 **260**、在 1,211 子集上是 **257**（260−3），而 `dword[COL−0x10]==COL` 在 1,214 上 **0** 条。

**三·两个 954 不可按数字相等互引.** `_r185/r185aa_claim.py`（**7 断言 0 FAIL**）复算：lowest-VA 主 COL 与 mdisp==0 主 COL 都恰 **954** 个，但两集合**对称差 188（94+94）**；机制是多 COL 类共 **94** 个、其 COL 按 mdisp **严格递减**排列（94 递减 / 0 递增 / 0 全等 / 0 混合），因此 mdisp==0 恒为类内**最高** VA，lowest-VA 恒非 mdisp==0。⇒ F01 括注与 F29 主表规则即便都得 954，也不能互相引证。

**四·mdisp==4 的第二条独立字节证据.** **954 个主 COL 的 mdisp 分布是 {0: 942, 4: 12}**，而**全部 1,214 个 COL 的 mdisp 恰 10 种** {0:954, 4:91, 8:78, 12:78, 24:6, 36:1, 40:1, 44:1, 1728:1, 21784:3}。那 12 个 mdisp==4 的类全为 Locomotion 系（Locomotion + Drive/DropPod/Fly/Hover/Jumpjet/Mech/Rocket/Ship/Teleport/Tunnel/Walk）。`_r185/r185y_iloco.py`（**8 断言 0 FAIL**）走**另一条链**：这 12 个类的 CHD → pBaseArray → BCD 里 ILocomotion 那一项的 mdisp **恒为 4**、pdisp 恒 **0xFFFFFFFF**、每类恰 1 项；反控把该项 mdisp 改 0 ⇒ 判据当场红。⇒「ILocomotion 位于对象偏移 4」不再是从主 COL 反推的措辞。

**五·symbols.json 的 vtable_va 对 12 条语义不同（本轮最重要的一条新事实）.** `_r185/r185ee_audit_recheck.py`（**14 断言**）与 `_r185/r185ff_subobj.py`（**6 断言**）复算：那 12 个类的 `vtable_va` 指向的是 **ILocomotion 次对象 vtable**（mdisp==4），而每类还有一张同 pTD 的 mdisp==0 vtable，两者地址差**恒为 +0xCC（12/12）**；两张表的 `.text` 槽数也不同（mdisp==0 那张 11 个类 **10** 槽、TeleportLocomotionClass **12** 槽，而 symbols.json 记 `vfunc_count` **50**）⇒ 引用「类的主虚表」时**不能直取 `vtable_va`**，F29 那条「取 mdisp==0 主虚表的 slot1/slot2」必须另行取那张表。另实测 TD 名前缀 **.?AV 952 / .?AU 2**（`INIEntry@INIClass`、`INISection@INIClass`），故「TD 名形如 .?AV<类名>@@」必须写成「.?A[VU]」，只去 `.?AV` 会让这 2 条解出 None。

**六·跨家族与被测反的审计数字.** 执行员 #444（hy4 / 4 回合 / 100 s）七项逐值复现，并**主动报出**「严格只去 .?AV ⇒ 952 而非 954」「8 个基类里 5 个 TD 名不以 .?AV 开头」两条边界（已采纳）。审计员 #445（deepseek / 30 回合 / 8.97 分 / **OVERTIME**）五条主张逐条判：「TD 前缀 952/2」「col_va ≠ dword(vt−4) 是 866 且 88 条的 pCHD 全同」「12 条是 Locomotion 且有 BCD 独立证据」「vtable_va 对 12 条语义不统一」四条**采纳并全部由主会话复算**；「全域 RTTI 形 vtable 1,215 个、mdisp≠0 共 231」两条**被测反** —— 本判据实测全域 **1,214**（= 总 COL 数）、mdisp≠0 的 vtable **260**（=1,214−954），其中 mdisp==4 的 **91**（= symbols 内 12 + symbols 外 79）；三条里只有「另 79 个、无一是 Locomotion」成立。

**七·落盘与门禁.** 台账 **V565 → V566 → V567**（两次各只在本列追加，statement / grade / evidence_paths 三列逐字节未动）：V566 = **138,507 B**（F01 limitations 5,036 → 7,612）、V567 = **140,546 B**（→ **9,651**）、sha **`2e502b68…`**、CR 0、55 行 5 列，其余 53 行逐单元格相同。重钉 `_r185/r185dd_repin.py`（**38 断言 0 FAIL**）：旧常量复算旧 MASTER 命中旧 pin 作硬闸 → `MASTER` **`6729de5d…` → `07136e79…` → `60f5b21c…`**，`FLOORS['F01']` (458,5036) → (458,7612) → (458,9651)，gate_runner 1 行，指针 5 字段（含把自述「530..565 / 36 份」改准为「530..567 / 38 份」）。**三门终态**：`check_disc.py` exit 0（C20 ok(R17_R131_FACTINDEX_V567)）、`facts_floors.py` exit 0（D9/D10 双一致）、`gate_runner.py` G1=G2=G3=ok。看板 274 行 ≥ 260 ⇒ 先归档最早两段（R181 + R174）到 BOARD_ARCHIVE 并保持 CR 2952，再追加本轮段。

**八·自错 S-185a1..S-185j1（十处，全部由可失败断言当场抓出，无一条进入结论）.** a1 `.text/.rdata` 上界按 vsize 取，写成 `0x7E1000/0x812000` 而真值是**文件上界**，`.text` 结束实为 `0x7E1000` 而虚界是 `0x7E038D`（用错一侧导致「28 槽全在 .text」假 FAIL）；a2 正则解析 class_ids 把 `m.group(3)` 当地址（那列是类名）；b1 首版 census 要求「紧接 dword==0」，漏掉「紧接 dword 是**另一层接口 COL**」这一合法形态 ⇒ 覆盖率 45/69 假 FAIL；c1 把「COL 在 vtable−4」误用到 `symbols.json` 的 `col_va` 上 ⇒ 88 条被判成「非 COL」假 FAIL；d1 `chd = dw(pchd)` 多解一层，把 CHD 本体当地址 ⇒ 12 个类全崩；x1 `r185x` 同处又犯一次（`colrec(vt-4)` 少解一层）；s1 `expect` 里把 5,036 写成 5,036/6,512 两个数混用；cc1 把 `split('\n')` 的 56 段当 55 行、行索引整体错位 1 ⇒ 「变化行 = [1]」被判成 [0]；cc2 直接把「旧 53 行不变」按 `range(1,54)` 比，漏了表头行；ee1 把「mdisp≠0 的 vtable 数」写成 231 去比（那是审计值）⇒ 断言恒红的写法被抓出后改成打印实测值。**族谱**：「把崩溃当判据失败」第四次（x1 崩在 TypeError 却一度当成判据红）；「把应然数当实测」第十六次（s1/cc1/ee1）。

**九·未取得（不粉饰）.** ① 审计的 **1,215 / 231** 两个全域数字的判据口径未穷举（可能要求 `dword[vt]` 落 .text 或含 .data 命中），登记为未取得；② F01 statement 的 **1201 / 1211** 仍不可复现，本轮未改 statement（改数字属裁定）；③ F23（`未取得`）/ F35（`[流程]`）grade 仍未改；④ `coverage.tsv` / `function_atlas.tsv` 仍不可读；⑤ 86.19% 原值仍不可重算；⑥ C7 三死分支仍各 0 行；⑦ 「哪份是当前版」仍无人覆盖；⑧ 指针自述字段仍不被任何门禁检查。
'''
SEC_LEDGER='''
## §1240 R185：gamemd.exe 类对象模型四条链全量复原；symbols.json 的 vtable_va 对 12 条指向次对象 vtable（+0xCC）

**一·链条形状（逐段可失败）.** `_r185/r185v_final.py` **27 断言 0 FAIL**：`vtable−4` → COL{signature∈{0,1}, mdisp, pdisp==0, pTD∈.data, pCHD∈.rdata} → TD{pVFTable==0x7F9594, spare==0, name@TD+8} → CHD{sig 0, attr, numBase≥1, pBaseArray∈.rdata} → BCD{6 dword, pTD, ncbase, mdisp, pdisp, pmdisp, attr}。954/954 COL、954/954 TD 名、954/954 槽数+逐槽、954/954 CHD 全通过；槽总数 **13,204**、BCD 总数 **2,615**。

**二·全镜像 census（不依赖 symbols.json）.** `_r185/r185z_colcensus.py` **11 断言 0 FAIL**：TD **988**（`.?AV` 962 / `.?AU` 26）、总 COL **1,214**、被指回 distinct COL **1,214**、主 COL **954**、无 COL 的 TD **34**；全 COL 的 mdisp 恰 **10 种** `{0:954,4:91,8:78,12:78,24:6,36:1,40:1,44:1,1728:1,21784:3}`；**954 个主 COL 的 mdisp 分布 {0:942, 4:12}**。`_r185/r185bb_257.py` **7 断言**复现 F01/F31 记的「257/1211」：`dword[COL−4]==0` 在 1,214 上 **260**、在 1,211 子集上 **257**；`COL−0x10==COL` **0** 条；1211 口径剔除的恰 3 个、`COL+4` 全为 `0x5518`。

**三·两个 954 差 188.** `_r185/r185aa_claim.py` **7 断言**：lowest-VA 与 mdisp==0 两集合对称差 **188（94+94）**，多 COL 类 **94** 个按 mdisp **严格递减**（94/0/0/0）⇒ 两条规则数字相等但选出的不是同一批 COL，不可互引。

**四·mdisp==4 的 BCD 侧独立证据.** `_r185/r185y_iloco.py` **8 断言**：12 个 Locomotion 系的 CHD→pBaseArray→BCD 里 ILocomotion 项 mdisp **恒 4**、pdisp **恒 0xFFFFFFFF**、每类恰 1 项；反控把该项 mdisp 改 0 ⇒ 红。

**五·vtable_va 语义不统一（新事实）.** `_r185/r185ff_subobj.py` **6 断言**：这 12 条的 `vtable_va` 指向 **mdisp==4 的次对象 vtable**，每类另有同 pTD 的 mdisp==0 vtable，差 **恒 +0xCC**；mdisp==0 那张的 .text 槽数 11 个类 **10**、TeleportLocomotionClass **12**，而 symbols.json 记 `vfunc_count` **50** ⇒ 不可直取。`_r185/r185ee_audit_recheck.py` **14 断言**另测：TD 前缀 **.?AV 952 / .?AU 2**；全域 vtable **1,214**、mdisp≠0 的 **260**、mdisp==4 的 **91**（审计主张的 1,215 / 231 被测反）。

**六·落盘.** V565 → V566（F01 limitations 5,036 → **7,612**，138,507 B）→ V567（→ **9,651**，**140,546 B / `2e502b68…` / CR 0 / 55 行 5 列**），只在本列追加、其余 53 行逐单元格相同；重钉 **38 断言 0 FAIL**（MASTER `6729de5d…`→`07136e79…`→**`60f5b21c…`**、`FLOORS['F01']`→(458,9651)、gate_runner 1 行、指针 5 字段含自述改准为「530..567 / 38 份」）；三门 exit 0 / G1=G2=G3=ok；看板 274 ≥ 260 ⇒ 归档 R181+R174 两段（CR 保持 2952）。
'''
SEC_LOCK='''
## PO · R17 第 185 轮（2026-11-28 1x–2x）· gamemd.exe 类对象模型四条链全量复原；symbols.json 的 vtable_va 对 12 条指向次对象 vtable（+0xCC）；审计两条全域数字被测反

**PO1. 🔴 交付一：把「vtable 前一个 dword 是 COL」做成 954/954 可失败.** `_r185/r185v_final.py` **27 断言 0 FAIL**：A 段 954/954 通过 `vtable−4 → COL{sig∈{0,1}, pdisp==0, pTD∈.data, pCHD∈.rdata}`；B 段 TD 名去前后缀 == symbols.json 的 name **954/954**，TD 首 dword 恒 **0x7F9594**、次 dword 恒 **0**；C 段槽数与逐槽地址 **954/954**，总槽 **13,204**；E 段 CHD + BCD 全可解，BCD **2,615** 条。反控五条真红（sig 改 2 / TD 名改 1 字节 / vtable+4 / 槽数期望 27 / CHD.numBase 8→7 / BCD.pTD 指 .rdata）。

**PO2. ✅ 交付二：全镜像 census 独立复算 F01 的四个数.** `_r185/r185z_colcensus.py` **11 断言**：TD **988**（962 AV + 26 AU）、总 COL **1,214**、被指回 **1,214**、主 COL **954**、无 COL 的 TD **34**；mdisp 全集 **10 种**、主 COL 分布 **{0:942, 4:12}**。F01 的 **1201 / 1211** 仍不可复现 —— 1211 只能由事后阈值 `COL+4<=0x1000` 得到，被剔除的恰 3 个且 `COL+4` 全为 `0x5518`。

**PO3. ✅ 交付三：F01/F31 的「257/1211」首次逐数复现.** `_r185/r185bb_257.py` **7 断言**：`dword[COL−4]==0` 在 1,214 上 **260**、在 1,211 子集上 **257**（260−3），`COL−0x10==COL` **0** 条 ⇒「COL 恰 5 dword、无 pSelf」与那个 257 自洽。

**PO4. 📌 交付四：两个 954 差 188，不可按数字互引.** `_r185/r185aa_claim.py` **7 断言**：lowest-VA 与 mdisp==0 两集合对称差 **188**，多 COL 类 **94** 个按 mdisp **严格递减**（94/0/0/0）⇒ mdisp==0 恒为最高 VA、lowest-VA 恒非 mdisp==0。F01 括注与 F29 主表规则的 954 是巧合相等。

**PO5. 🔴 交付五：mdisp==4 有了 BCD 侧的独立证据.** `_r185/r185y_iloco.py` **8 断言**：12 个 Locomotion 系（Locomotion + Drive/DropPod/Fly/Hover/Jumpjet/Mech/Rocket/Ship/Teleport/Tunnel/Walk）的 CHD→pBaseArray→BCD 里 ILocomotion 项 mdisp **恒 4**、pdisp **恒 0xFFFFFFFF**、每类恰 1 项；反控改该项 mdisp 为 0 ⇒ 红。

**PO6. 🔴 交付六：symbols.json 的 vtable_va 对 12 条语义不同.** `_r185/r185ff_subobj.py` **6 断言**：这 12 条的 `vtable_va` 指向 **mdisp==4 次对象 vtable**，每类另有同 pTD 的 mdisp==0 vtable，差 **恒 +0xCC（12/12）**；mdisp==0 那张 11 个类 **10** 槽、TeleportLocomotionClass **12** 槽，而 symbols.json 记 **50** ⇒ 引用「类的主虚表」不可直取 `vtable_va`（F29 的 slot1/slot2 规则必须另取 mdisp==0 那张）。

**PO7. 📌 交付七：审计两条全域数字被测反（第四、五次「审计被复算推翻」）.** `_r185/r185ee_audit_recheck.py` **14 断言**：审计 #445 主张「全域 1,215 个 RTTI 形 vtable、mdisp≠0 共 231」—— 本判据实测 **1,214** 与 **260**（mdisp==4 的 **91** = 12 + 79）；三条里只有「另 79 个、无一是 Locomotion」成立。TD 前缀 **.?AV 952 / .?AU 2**（`INIEntry@INIClass`、`INISection@INIClass`）采纳，正文「.?AV<类名>@@」须写成「.?A[VU]」。

**PO8. ✅ 交付八：落盘 + 重钉 + 三门 + 归档.** V565 → V566（F01 limitations 5,036 → **7,612**，**138,507 B**）→ V567（→ **9,651**，**140,546 B / `2e502b68…` / CR 0 / 55 行 5 列**）；重钉 `_r185/r185dd_repin.py` **38 断言 0 FAIL**：MASTER `6729de5d…`→`07136e79…`→**`60f5b21c…`**、`FLOORS['F01']`→(458,9651)、gate_runner 1 行、指针 5 字段（自述改准为「530..567 / 38 份」）。三门 `check_disc` exit 0（C20 ok(V567)）/ `facts_floors` exit 0（D9+D10 双一致）/ `gate_runner` G1=G2=G3=ok。看板 **274 ≥ 260** ⇒ 归档最早两段 R181+R174（CR 保持 **2952**），归档后 **222 行**，加段后 ≤ 300。

**PO9. 📌 自错 S-185a1..S-185j1（十处，全部当场抓出，无一条进入结论）.** `.text` 上界用 vsize 而非文件上界（假 FAIL）；class_ids 正则取错列；census 漏掉「紧接 dword 是另一层接口 COL」形态（覆盖率 45/69 假红）；把「COL 在 vtable−4」误用到 `col_va`（88 条判成非 COL）；`chd=dw(pchd)` 多解一层致 12 类全崩；`r185x` 同处再犯（`colrec(vt-4)` 少解一层）；断言里 5,036 与旧数混用；`split` 56 段当 55 行致行索引错位 1；「其余 53 行不变」漏了表头行；拿审计的 231 去比自己的实测。**族谱**：「把崩溃当判据失败」第四次；「把应然数当实测」第十六次。

**PO10. 📌 跨家族（执行一件 + 审计一件，审计有 OVERTIME）.** 执行员 **#444**（hy4 / 4 回合 / 1.67 分 / 100 s）七项逐值复现，并**主动报出**「严格只去 .?AV ⇒ 952 而非 954」「8 个基类里 5 个 TD 名不以 .?AV 开头」两条边界（已采纳进正文）。审计员 **#445**（deepseek / 30 回合 / 8.97 分 / **OVERTIME：实测 8.97 分 vs 预算 8.0 分**）五条主张：四条采纳并由主会话逐条复算（TD 前缀 952/2、col_va≠dword(vt−4) 的 866/88 且 88 条 pCHD 全同、12 条 Locomotion 且有 BCD 独立证据、`vtable_va` 语义不统一），两条全域数字（1,215 / 231）**被主会话实测推翻**（1,214 / 260）。

**PO11. 📌 未取得（不粉饰）.** ① 审计 1,215 / 231 的判据口径未穷举（是否要求 `dword[vt]` 落 .text、是否含 .data 命中），登记为未取得；② F01 statement 的 1201 / 1211 仍不可复现，本轮未改 statement（改数字属裁定不是取证）；③ F23 / F35 grade 未改；④ `coverage.tsv` / `function_atlas.tsv` 仍不可读；⑤ 86.19% 原值仍不可重算；⑥ C7 三死分支仍各 0 行；⑦ 「哪份是当前版」仍无人覆盖；⑧ 指针自述字段（声明轮次 / 版本范围）本轮又改准一次，但仍不被任何门禁检查。
'''
SEC_BOARD='''## 🟢 R17 第 185 轮（2026-11-28 1x–2x）· gamemd.exe 类对象模型四条链全量复原（954 vtable / 1,214 COL / 988 TD / 2,615 BCD）；测出 symbols.json 的 vtable_va 对 12 条指向**次对象** vtable（+0xCC）；审计两条全域数字被复算推翻

**入口**：用户裁定的第一优先级 —— gamemd.exe 静态二进制本体取证。本轮选「类对象模型的四条字节链」，全部从字节重算，不引用任何既有派生数字。

| 项 | 实测 |
|---|---|
| 链条通过率 | `r185v` **27 断言 0 FAIL**：COL 954/954、TD 名 954/954、槽数+逐槽 954/954、CHD+BCD 954/954 |
| 规模 | 954 张表共 **13,204** 槽；BCD **2,615** 条；TD **988**（.?AV 962 / .?AU 26） |
| census | `r185z` **11 断言**：总 COL **1,214**、被指回 **1,214**、主 COL **954**、无 COL 的 TD **34** |
| mdisp | 全 COL 恰 **10 种**；**主 COL {0:942, 4:12}**，12 个全为 Locomotion 系 |
| 首个复现 | `r185bb` **7 断言**：F01/F31 的 257/1211 —— `COL−4==0` 在 1,214 上 **260**、1,211 子集上 **257** |
| 两个 954 | `r185aa` **7 断言**：lowest-VA 与 mdisp==0 对称差 **188**，94 个多 COL 类按 mdisp 严格递减 |
| 新事实 | `r185ff` **6 断言**：12 条的 `vtable_va` 是 **mdisp==4 次对象**表，同 pTD 的 mdisp==0 表差 **恒 +0xCC**，槽数 10/12 对 symbols 记的 50 |
| 台账 | V565 → V566（**138,507 B**）→ **V567（140,546 B / `2e502b68…` / CR 0 / 55 行）**，只改 F01 limitations（5,036 → 9,651） |
| 门禁重钉 | `r185dd` **38 断言**；MASTER `6729de5d…`→`07136e79…`→**`60f5b21c…`**；gate_runner 1 行；指针 5 字段 |
| 三门终态 | `check_disc` exit 0（C20 ok(V567)）/ `facts_floors` exit 0 / `gate_runner` G1=G2=G3=ok |
| 五 CR | **1081 / 137 / 337 / 0 / 2952** 全保持；看板 274 ≥ 260 ⇒ 归档 R181+R174 两段，归档后 **222 行** |

**四条链的形状**：`vtable−4 →` COL{sig∈{0,1}, mdisp, pdisp==0, pTD∈.data, pCHD∈.rdata} `→` TD{pVFTable==**0x7F9594**, spare==0, name@TD+8} `→` CHD{sig 0, attr, numBase≥1, pBaseArray∈.rdata} `→` BCD{6 dword}。四条链在 954 条上逐条可失败（反控：sig 改 2 / TD 名改 1 字节 / vtable+4 / 槽数期望 27 / CHD.numBase 8→7 / BCD.pTD 指 .rdata 全部真红）。

**mdisp==4 的第二条独立证据**：`r185y` **8 断言** —— 12 个 Locomotion 类的 CHD→pBaseArray→BCD 里 ILocomotion 项 mdisp **恒 4**、pdisp 恒 `0xFFFFFFFF`、每类恰 1 项；反控改该项为 0 ⇒ 红。⇒「ILocomotion 位于偏移 4」不再是从主 COL 反推的措辞。

**跨家族**：执行员 **#444**（hy4 / 4 回合 / 1.67 分）七项逐值复现，**主动报出**「严格只去 .?AV ⇒ 952 而非 954」「8 个基类里 5 个 TD 名不以 .?AV 开头」两条边界（已采纳）；审计员 **#445**（deepseek / 30 回合 / 8.97 分 / **OVERTIME**）五条主张：四条采纳（TD 前缀 952/2、col_va 866/88 且 pCHD 全同、12 条有 BCD 独立证据、`vtable_va` 语义不统一），两条**被主会话实测推翻** —— 全域 vtable 实测 **1,214**（审计 1,215）、mdisp≠0 实测 **260**（审计 231），mdisp==4 的 **91** = 12 + 79。

**自错 S-185a1..S-185j1（十处，全部当场抓出，无一条进入结论）**：`.text` 上界用 vsize 而非文件上界；class_ids 正则取错列；census 漏「紧接 dword 是另一层接口 COL」形态（45/69 假红）；把「COL 在 vtable−4」误用到 `col_va`；`chd=dw(pchd)` 多解一层致 12 类全崩；`r185x` 同处再犯；5,036 与旧数混用；`split` 56 段当 55 行；「其余 53 行不变」漏表头行；拿审计的 231 比自己的实测。**族谱**：「把崩溃当判据失败」第四次；「把应然数当实测」第十六次。

**未取得**：① 审计 1,215 / 231 的判据口径未穷举（是否要求 `dword[vt]` 落 .text、是否含 .data 命中）；② F01 statement 的 **1201 / 1211** 仍不可复现，未改 statement（改数字属裁定）；③ F23 / F35 grade 未改；④ `coverage.tsv` / `function_atlas.tsv` 仍不可读；⑤ 86.19% 原值仍不可重算；⑥ C7 三死分支仍各 0 行；⑦ 「哪份是当前版」仍无人覆盖；⑧ 指针自述字段本轮又改准一次，仍不被任何门禁检查。
'''
new_rc=rc.rstrip('\n')+'\n'+SEC_COMMON
new_led=led.rstrip('\n')+'\n'+SEC_LEDGER
new_lock=lock.rstrip('\n')+'\n'+SEC_LOCK
new_brd2=new_brd.rstrip('\n')+'\n'+SEC_BOARD
ck('H14 R14_COMMON 新 CR 保持 1081', new_rc.count('\r')==1081, new_rc.count('\r'))
ck('H15 台账新 CR 保持 337', new_led.count('\r')==337, new_led.count('\r'))
ck('H16 LEAD_LOCK 新 CR 保持 137', new_lock.count('\r')==137, new_lock.count('\r'))
ck('H17 看板新 CR == 0', new_brd2.count('\r')==0, new_brd2.count('\r'))
ck('H18 看板新行数 <= 300', new_brd2.count('\n')<=300, new_brd2.count('\n'))
ck('H19 看板新行数 = 归档后 + 本轮段', new_brd2.count('\n')>len(rest), (new_brd2.count('\n'),len(rest)))
ck('H20 四件套都只追加（旧内容为新内容前缀）',
   new_rc.startswith(rc.rstrip('\n')) and new_led.startswith(led.rstrip('\n'))
   and new_lock.startswith(lock.rstrip('\n')) and new_brd2.startswith(new_brd.rstrip('\n')))
ck('H21 新段落含本轮关键串', 'PO · R17 第 185 轮' in new_lock and '2.190 R185' in new_rc and '§1240 R185' in new_led and 'R17 第 185 轮' in new_brd2)
ck('H22 三个台账文件字节增长为正、看板因归档而缩小', 
   len(new_rc.encode())>len(rc.encode()) and len(new_led.encode())>len(led.encode())
   and len(new_lock.encode())>len(lock.encode()) and len(new_brd2.encode())<len(brd.encode()),
   (len(new_rc.encode())-len(rc.encode()), len(new_led.encode())-len(led.encode()),
    len(new_lock.encode())-len(lock.encode()), len(new_brd2.encode())-len(brd.encode())))
_arc_inc=len(new_arc.encode())-len(arc.encode())
_board_dec=len(brd.encode())-len(new_brd.encode())
ck('H22b 看板重构恒等式：原看板 == 搬运块 + LF + 剩余 + LF（逐字节）',
   brd==head2_txt+'\n'+new_brd+'\n' if False else brd==('\n'.join(head2)+'\n'+new_brd+'\n'),
   (_board_dec, len('\n'.join(head2))+2))
ck('H22c 看板减少 == 搬运块行块长度 + 2', _board_dec==len('\n'.join(head2).encode())+2, (_board_dec, len('\n'.join(head2).encode())+2))
ck('H22d 归档增量 == 搬运块（rstrip 后）+ 1', _arc_inc==len(arch_block.encode())+1, (_arc_inc, len(arch_block.encode())+1))
ck('H22e 搬运块逐字节出现在新归档末尾', new_arc.rstrip('\n').endswith(arch_block), arch_block[-20:])
ck('H22f 看板最终 = 归档后 222 行 + 本轮段', new_brd2.count('\n')==len(rest)+SEC_BOARD.count('\n'), (new_brd2.count('\n'), len(rest)+SEC_BOARD.count('\n')))
if fails:
    print('★ fail-closed：%d 条未过，不写盘'%len(fails)); sys.exit(1)
print('== 写盘 ==')
for path,newtxt in ((ARC,new_arc),(RC,new_rc),(LED,new_led),(LOCK,new_lock),(BRD,new_brd2)):
    oldraw=open(path,'rb').read(); o=hashlib.sha256(oldraw).hexdigest()
    bak=os.path.join(BL,'%s.before_r185_%s.bak'%(os.path.basename(path),stamp))
    fd=os.open(bak,os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o644)
    with os.fdopen(fd,'wb') as f: f.write(oldraw)
    ck('H23 %s 备份独占且 sha 相同'%os.path.basename(path), hashlib.sha256(open(bak,'rb').read()).hexdigest()==o)
    assert open(path,'rb').read()==oldraw, '母本被外部改动: %s'%path
    io.open(path,'w',encoding='utf-8',newline='').write(newtxt)
    back=open(path,'rb').read()
    ck('H24 %s 回读一致'%os.path.basename(path), hashlib.sha256(back).hexdigest()==hashlib.sha256(newtxt.encode()).hexdigest())
    ck('H25 %s CR 保持 %d'%(os.path.basename(path),HARD[path]), back.count(b'\r')==HARD[path], back.count(b'\r'))
    print('   %-22s %d -> %d B / %d -> %d 行'%(os.path.basename(path),len(oldraw),len(back),oldraw.count(b'\n'),back.count(b'\n')))
print()
print('断言 %d 条，FAIL %d 条'%(n,len(fails)))
sys.exit(1 if fails else 0)
