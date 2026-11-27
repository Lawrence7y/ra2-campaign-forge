# -*- coding: utf-8 -*-
"""R187 J：四件套追加（fail-closed：旧 sha + CR 硬闸，全部断言在写盘之前）。
看板已归档到 223 行 < 260 ⇒ 本轮不再归档，直接追加。
  R14_COMMON.md  ## 2.192   (CR 1081)
  台账           ## §1242   (CR 337)
  LEAD_LOCK      ## PQ · R17 第 187 轮 (CR 137)
  STATUS_BOARD   第 187 轮记录 (CR 0, 行数 <= 300)
"""
import hashlib, io, os, sys, time
ROOT = '/home/t628/projects/ra2-campaign-forge'
TIER = os.path.join(ROOT, 'lead/next_re_20261117_r14')
BL = os.path.join(TIER, 'R17_LEAD_BASELINE')
RC = os.path.join(TIER, 'R14_COMMON.md')
LED = os.path.join(ROOT, 'lead/GOAL_THREE_TARGETS_20261018.md')
LOCK = os.path.join(ROOT, 'lead/LEAD_LOCK')
BRD = os.path.join(TIER, 'STATUS_BOARD.md')
stamp = time.strftime('%Y%m%d_%H%M%S')
HARD = {RC: 1081, LED: 337, LOCK: 137, BRD: 0}
fails = []; n = 0
def ck(nm, c, d=''):
    global n; n += 1
    if not c: fails.append(nm)
    print(('PASS ' if c else 'FAIL ') + nm + ((' | ' + str(d)) if d != '' else ''))
pre = {}
for p, cr in HARD.items():
    b = open(p, 'rb').read(); pre[p] = b
    ck('H0 %s 存在且 CR == %d' % (os.path.basename(p), cr), b.count(b'\r') == cr, b.count(b'\r'))
ck('H4 看板 %d 行 < 260 ⇒ 本轮不归档' % pre[BRD].count(b'\n'), pre[BRD].count(b'\n') < 260,
   pre[BRD].count(b'\n'))

SEC_COMMON = '''
## 2.192 R187：R186 的两条**陈述**被逐字节测反 —— 「845 条假命中」其实是不可达的真指令（5,730/5,731 局部自洽）、「10 张表无 imm32 装点」实测 10/10 全有；三层数改用全口径 4,053/3,737 = 92.20%

R187 继续用户裁定的第一优先级：gamemd.exe 静态二进制本体取证。本轮挑的是 R186 自己列在「未取得」里的第②③条，结果是**两条陈述而不是两条待办**：它们都已经能被证伪了。

**一·「845 条假命中」这个词是错的.** R186 把字节模式口径里「不在递归下降起点集合」的 845 条叫「假命中（落在非指令边界上）」。`_r187/r187e_align.py`（**13 断言 / 2 FAIL 如实登记**）改用**不依赖可达性**的局部对齐判据：某处是不是一条 `C7 /0` 指令的立即数字段 —— 按操作数的 (mod,rm,SIB,disp) 自描述长度 L 反推起点 `o−L`，要求该处字节为 `C7`、`modrm.reg==0`、按该 modrm 算出的立即数偏移恰为 `o`。实测 **5,730/5,731 局部可对齐、仅 1 条孤立**（`00535A60`）。⇒ 那 845 条绝大多数是**真指令、只是种子集合没覆盖到它们的入口**；「假命中」把「不可达」误称成「不是指令」，**不宜再引**。反控：回看窗 15→1 使可对齐数从 1,200 降到 96；命中集合整体平移 +3 字节使比例从 **100.00%** 降到 **25.67%**。

**二·因此撤掉一层不必要的收缩.** 既然不可达 ≠ 不是指令，R186 的三层口径（交集 4,886 → 对象寄存器 3,666 → 3,204）就不必要。`_r187/r187f_recount.py`（**14 断言 0 FAIL**）用全 5,731 条重算：对象寄存器 store（基址为通用寄存器、非 esp/ebp、无索引）**4,053**（构成：对象寄存器 4,053 / 栈基址 1,337 / 绝对址 341 / 带索引 0，四类合计 **= 5,731** 算术闭合）；`disp == COL.mdisp` **3,737 = 92.20%**；放宽到「disp ∈ 该 TD 在全镜像 CHD 出现过的 mdisp」**3,788 = 93.46%**；残差 **265**（模板/容器 **262**：`?$TypeList@H` 70、`?$TypeList@PBVAnimTypeClass@@` 12、`?$VectorClass@H` 11 等；非模板 **3**：BaseClass / BlowPipe / LayerClass，与 R186 的真个例逐名相同）。⇒ **R186 的 87.40% 应改读 92.20%**，两者不是矛盾而是两个作用域；全口径既更大又更准，作主数字，87.40% 降为「交集作用域下的旧值」。

**三·「10 张表无 imm32 装点」被推翻（10/10 全有）.** `_r187/r187d_final.py`（**22 断言 0 FAIL**）对这 10 张表逐处做结构反查：**7 张**走 C7 对象寄存器 store（CarryoverClass `00473777 c706044c7e00`、Dial8Class `004A53DA`、`?$DynamicVectorClass@V?$DistributionObject@PAVCellClass@@@?$DiscreteDistributionClass@VCellClass@@@@` `004E0A8A`、TriColorGaugeClass `004E2AD5`、PKPipe `00632CF9`、TextButtonClass `0071FF65` 与 `0071FFC2` 两处、`?$DynamicVectorClass@PBVToolTip@@` `0072403A`）；**1 张**走 C7 栈 store（`?$DynamicVectorClass@PAU_DDSURFACEDESC@@` `004A4937 c74424200c5e7e00`，位移 +0x20 因为对象构造在栈上）；**2 张**走「mov r32,imm32 再把同一寄存器写进内存」（`?$DynamicVectorClass@PAE` `007B2DBA baec7a7f00` → `mov [esi+0x3F338], edx`；`?$DynamicVectorClass@PAUWinsockBufferType@WinsockInterfaceClass@@` `007B19C8` → `mov [esi+8], edx`）。位移 == COL.mdisp 的 **7/10**；不等的恰那 3 张，**不是异常、是形态不同**。口径 P 单口径覆盖 **1,212/1,214**，R186c 的 1,204 = 1,214 − 8（有 C7 但起点不可达）− 2（纯 B 形态），算术闭合。

**四·三个中间版本都错了，错误性质写清.** r187a 用 STARTS（可达起点）当「是不是指令边界」的判据 ⇒ 12 处全判「数据字节」；r187b 想甩开 STARTS 却从立即数中间盲解（`dec_at(va)`）拿到 `add al,0x4c` / `lodsb` / `in al,dx` 这类垃圾解码并当成起点 ⇒ 12 处全判「其它」，比 a 版更离谱；r187c 改对了方向（结构反查），但 B 形态判定里把**绝对文件偏移**当成 `.text` 相对偏移去索引，偏了 `rawptr = 4096` ⇒ 2 张 B 形态表被判「其它」。r187d 改为 `toff = off − rawptr` 后 **22 断言 0 FAIL**，且「判为数据字节的处数」三个版本里第一次归零。

**五·跨家族（执行一件已完成）.** 执行员 **#450**（hy4 / 独立脚本 `_r187/exec_hy4/r187_scan.py`）不复用主会话代码，独立推出段边界、TypeDescriptor、vtable，10 个类逐个给形态，结论与主会话**逐类相同**（7 A / 2 B / 1 C / 1 个 `.data` 指针槽），checks 10 fails 0。审计员 #451（deepseek）本轮**未在时限内回件**，如实登记。

**六·落盘与门禁.** 台账 **V568 → V569**：F01 limitations 12,239 → **14,490**、F29 limitations 16,840 → **19,204**，总 **149,333 B**（+4,615）、55 行 5 列、CR 0、sha **`b260f1f4…`**；只改两行、两行只有第 5 列变，statement / grade / evidence 逐字节未动（改数字属裁定，本轮不改）。重钉 `_r187/r187h_repin.py`（**40 断言 0 FAIL**）：旧常量复算旧 MASTER **`7ee9f8ac…`** 命中旧 pin 作硬闸 → MASTER → **`365d5930…`**，`FLOORS['F01']` (458,12239)→(458,14490)、`FLOORS['F29']` (3435,16840)→(3435,19204)，gate_runner 1 行，指针四字段（自述「530..568 / 39 份」改准为「530..569 / 40 份」、声明轮次 R186→R187）。**三门终态**：`check_disc.py` exit 0（C19 ok / C20 ok(V569)）、`facts_floors.py` exit 0（D8 floor == 149,333、D9/D10 双一致）、`gate_runner.py` G1=G2=G3=ok。看板 **271 ≥ 260** ⇒ 归档最早两段 R175 + R176（CR 保持 **2952**，归档 1,375,874 → 1,386,736 B，逐项算术闭合），归档后 **223 行**，加段后 ≤ 300。

**七·自错 S-187a1..S-187f4（十一处，全部当场抓出，无一条进入结论）.** **a1** r187a 把可达性当指令边界判据（方法论错误，12 处全判数据字节）；**a2** r187a 的反控 N2「只认 4 字节对齐出现数应下降」实测 12 == 12（这 10 个地址恰好全对齐）⇒ 反控本身不成立而不是判据错；**a3** r187a 的 N4 反控写成恒真式；**b1** r187b 从立即数中间盲解并把结果当指令起点（比 a1 更离谱）；**b2** r187b 的 N2「imm−1 当 vtable」实测 5,731 == 5,731（位移匹配本就唯一）；**c1** r187c 的 B 形态用绝对文件偏移索引 `.text` 相对 BLOB，偏 `rawptr=4096`；**c2** r187c 的 C6 算术闭合写错（把 1,212−2 当成 1,204 的来历，实际是 1,214−8−2）；**d1** r187d 的 D7c 用 `int(k,16)` 而 k 已是字符串形式地址 ⇒ `TypeError`（**崩溃当判据失败**）；**d2** r187d 的 N4 用全表线性扫找首次出现 ⇒ 跑满超时；**e1** r187e 无 memo 时每个命中点解 100+ 次 ⇒ 4 次测量跑不完；**f1** r187f 首版把 STARTS 递归下降又跑一遍（10+ 分钟）只为引用三个已在 `r186c.json` 里的数；**f2** r187f 首版把绝对址 store（base=None）算进「对象寄存器」⇒ 得 4,394 而非 4,053。**族谱**：「把崩溃当判据失败」**第六次**（d1）；「把应然数当实测」**第十八次**（c2）。

**八·未取得（不粉饰）.** ① 审计员 #451 本轮未回件，跨家族审计这一侧本轮无第二家族结论；② 「装点位移 == mdisp」的 265 条残差里那 **3** 条非模板（BaseClass / BlowPipe / LayerClass）仍只逐条登记、无统一解释；③ 局部对齐判据是**局部**的，它不能证明一条指令**可达**，只能证明它是编码自洽的指令；④ 那 1 条孤立处（`00535A60`）未逐字节解释；⑤ F01 statement 的 1201 / 1211 仍不可复现；⑥ F23 / F35 grade 未改；⑦ `coverage.tsv` / `function_atlas.tsv` 仍不可读；⑧ 86.19% 原值仍不可重算；⑨ C7 三死分支仍各 0 行；⑩ 「哪份是当前版」仍无人覆盖。
'''

SEC_LEDGER = '''
## §1242 R187：R186 两条陈述被逐字节测反（845「假命中」其实是不可达的真指令、10 张表 10/10 全有装点）；三层数改全口径 4,053/3,737 = 92.20%

**一·「845 假命中」撤回.** `_r187/r187e_align.py` **13 断言 / 2 FAIL 如实登记**：改用不依赖可达性的局部对齐判据（按 C7 操作数自描述长度反推起点、要求起点字节为 C7 且 modrm.reg==0 且立即数偏移恰为 o），实测 **5,730/5,731 局部可对齐、仅 1 条孤立**（`00535A60`）⇒ 那 845 条是**真指令但不可达**，不是「落在非指令边界上」。反控：回看窗 15→1 使 1,200 条里可对齐从 1,200 降到 96；平移 +3 字节使比例从 100.00% 降到 25.67%。

**二·撤掉一层收缩，三层数改全口径.** `_r187/r187f_recount.py` **14 断言 0 FAIL**：全 5,731 条里对象寄存器 store **4,053**（对象 4,053 / 栈基址 1,337 / 绝对址 341 / 带索引 0，合计 **= 5,731** 闭合）；`disp == COL.mdisp` **3,737 = 92.20%**；放宽 **3,788 = 93.46%**；残差 **265**（模板 **262** / 非模板 **3**：BaseClass / BlowPipe / LayerClass）。⇒ R186 的 87.40% 改读 **92.20%**，旧值降为「交集作用域」。

**三·「10 张表无 imm32 装点」撤回（10/10 全有）.** `_r187/r187d_final.py` **22 断言 0 FAIL**：**7 张** C7 对象寄存器 store（CarryoverClass 00473777 `c706044c7e00`、Dial8Class 004A53DA、DistributionObject/DiscreteDistributionClass 004E0A8A、TriColorGaugeClass 004E2AD5、PKPipe 00632CF9、TextButtonClass 0071FF65 与 0071FFC2、PBVToolTip 0072403A）；**1 张** C7 栈 store（PAU_DDSURFACEDESC 004A4937 `c74424200c5e7e00`，位移 +0x20）；**2 张** B 形态（PAE 007B2DBA `baec7a7f00` → `mov [esi+0x3F338], edx`；PAUWinsockBufferType 007B19C8 → `mov [esi+8], edx`）。位移 == mdisp **7/10**，不等的恰那 3 张（形态不同，非异常）。口径 P 覆盖 **1,212/1,214**；1,204 = 1,214 − 8 − 2 闭合。

**四·三个中间版本的方法错误.** r187a 用可达性当边界判据（12 处全判数据字节）；r187b 从立即数中间盲解（`add al,0x4c` / `lodsb` / `in al,dx`）并当起点；r187c 把绝对偏移当相对偏移索引（偏 rawptr=4096）。r187d 修正后 22 断言 0 FAIL，「判为数据字节」首次归零。

**五·落盘.** V568 → **V569**（F01 lim 12,239→**14,490**、F29 lim 16,840→**19,204**，**149,333 B / `b260f1f4…` / CR 0 / 55 行 5 列**），只改两行、两行只有第 5 列变，statement / grade / evidence 逐字节未动；重钉 **40 断言 0 FAIL**（MASTER `7ee9f8ac…`→**`365d5930…`**、F01/F29 两处 floor、gate_runner 1 行、指针四字段含自述改准为「530..569 / 40 份」与声明轮次 R187）；三门 exit 0 / exit 0 / G1=G2=G3=ok；看板 271 ≥ 260 ⇒ 归档 R175+R176（CR 保持 2952，1,375,874→1,386,736 B 逐项闭合），归档后 223 行。
'''

SEC_LOCK = '''
## PQ · R17 第 187 轮（2026-11-28 3x–4x）· R186 两条陈述被逐字节测反：「845 假命中」其实是不可达的真指令（5,730/5,731）、「10 张表无装点」实测 10/10 全有；三层数改全口径 3,737/4,053 = 92.20%

**PQ1. 🔴 交付一：把「845 条假命中」这个词测掉.** `_r187/r187e_align.py`（**13 断言 / 2 FAIL 如实登记**）用**不依赖可达性**的局部对齐判据（按 `C7` 操作数的 (mod,rm,SIB,disp) 自描述长度 L 反推起点 `o−L`，要求该处字节为 `C7`、`modrm.reg==0`、按该 modrm 算出的立即数偏移恰为 `o`）：5,731 条里 **5,730 局部可对齐、仅 1 条孤立**（`00535A60`）⇒ R186 的「845 条落在非指令边界上」把**不可达**误称成**不是指令**，该词不宜再引。反控三条：回看窗 15→1 使前 1,200 条可对齐从 1,200 降到 **96**；允许跨过起点也算 ⇒ 1,200 == 1,200（反控方向不成立，如实登记为 FAIL）；命中集合整体平移 +3 字节使比例从 **100.00%** 降到 **25.67%**。

**PQ2. 🔴 交付二：撤掉一层不必要的收缩，三层数改全口径.** `_r187/r187f_recount.py`（**14 断言 0 FAIL**）：全 5,731 条里对象寄存器 store（基址为通用寄存器、非 esp/ebp、无索引）**4,053**（构成：对象 4,053 / 栈基址 1,337 / 绝对址 341 / 带索引 0，四类合计 **= 5,731** 算术闭合）；`disp == COL.mdisp` **3,737 = 92.20%**；放宽到「disp ∈ 该 TD 在全镜像 CHD 出现过的 mdisp」**3,788 = 93.46%**；残差 **265**（模板/容器 **262**：`?$TypeList@H` 70、`?$TypeList@PBVAnimTypeClass@@` 12、`?$VectorClass@H` 11；非模板 **3**：BaseClass / BlowPipe / LayerClass，与 R186 逐名相同）。⇒ **87.40% 改读 92.20%**：两者不是矛盾，是交集作用域 vs 全口径；全口径既更大也更准。

**PQ3. 🔴 交付三：「10 张表找不到任何 imm32 装点」被推翻（10/10 全有）.** `_r187/r187d_final.py`（**22 断言 0 FAIL**）逐处结构反查：**7 张** C7 对象寄存器 store —— CarryoverClass `00473777 c706044c7e00`、Dial8Class `004A53DA c7063c5e7e00`、`?$DynamicVectorClass@V?$DistributionObject@PAVCellClass@@@?$DiscreteDistributionClass@VCellClass@@@@` `004E0A8A c7078c927e00`、TriColorGaugeClass `004E2AD5 c70630947e00`、PKPipe `00632CF9 c700acfd7e00`、TextButtonClass `0071FF65` 与 `0071FFC2` 两处 `c706dc557f00`、`?$DynamicVectorClass@PBVToolTip@@` `0072403A c701c8577f00`；**1 张** C7 栈 store —— `?$DynamicVectorClass@PAU_DDSURFACEDESC@@` `004A4937 c74424200c5e7e00`（对象构造在栈上，位移 +0x20）；**2 张** B 形态 —— `?$DynamicVectorClass@PAE` `007B2DBA baec7a7f00` → `mov [esi+0x3F338], edx`、`?$DynamicVectorClass@PAUWinsockBufferType@WinsockInterfaceClass@@` `007B19C8 ba1c7a7f00` → `mov [esi+8], edx`。位移 == COL.mdisp **7/10**，不等的恰那 3 张（形态不同，非异常）。

**PQ4. ✅ 交付四：算术闭合与口径 P 的覆盖.** 口径 P（`C7 /0` 含 SIB）单口径覆盖 **1,212/1,214** 张表，未覆盖的 2 张恰是走 B 形态那 2 张；R186c 的装点覆盖 1,204 **= 1,214 − 8（有 C7 但指令起点不在 STARTS）− 2（纯 B 形态）**，两条算术都闭合。反控四条全真红：imm 判等改 vt+1 **0** 命中、目标 VA 加 4 做结构反查 **10 张全空**、B 形态改用绝对偏移索引（复刻 r187c 的 bug）命中表数 **从 2 降到 0**、种子清空 **STARTS == 0**。

**PQ5. 📌 交付五：三个中间版本的方法错误逐个写清.** **r187a** 拿 STARTS（可达起点）当「是不是指令边界」的判据 ⇒ 12 处全判「数据字节」；**r187b** 想甩开 STARTS 却从立即数中间盲解（`dec_at(va)`），拿到 `add al,0x4c` / `lodsb` / `in al,dx` 这类垃圾解码并当成起点 ⇒ 12 处全判「其它」，比 a 版更离谱；**r187c** 方向对了（结构反查）但 B 形态判定里把**绝对文件偏移**当成 `.text` 相对偏移去索引，偏了 `rawptr = 4096` ⇒ 2 张 B 形态表被判「其它」，且 C6 的算术闭合写错。**r187d** 改 `toff = off − rawptr` 后 **22 断言 0 FAIL**，「判为数据字节的处数」三个版本里第一次归零。

**PQ6. ✅ 交付六：落盘 + 重钉 + 三门 + 归档.** 台账 **V568 → V569**：F01 limitations 12,239 → **14,490**、F29 limitations 16,840 → **19,204**，总 **149,333 B（+4,615）/ 55 行 5 列 / CR 0 / sha `b260f1f4…`**；只改两行、两行只有第 5 列变，statement / grade / evidence 逐字节未动（16 断言 0 FAIL）。重钉 `_r187/r187h_repin.py` **40 断言 0 FAIL**：旧常量复算旧 MASTER **`7ee9f8ac…`** 命中旧 pin 作硬闸 → MASTER **`365d5930…`**，`FLOORS['F01']` (458,12239)→(458,14490)、`FLOORS['F29']` (3435,16840)→(3435,19204)，gate_runner 1 行，指针四字段（自述「530..568 / 39 份」改准为「530..569 / 40 份」、声明轮次 R186→R187）。**三门终态**：`check_disc` exit 0（C20 ok(V569)）、`facts_floors` exit 0（D8 floor == 149,333、D9+D10 双一致）、`gate_runner` G1=G2=G3=ok。看板 **271 ≥ 260** ⇒ 归档最早两段 R175 + R176（`_r187/r187i_archive.py` **17 断言 0 FAIL**，CR 保持 **2952**，1,375,874 → **1,386,736 B** 按构造逐项闭合），归档后 **223 行**。

**PQ7. 📌 自错 S-187a1..S-187f4（十一处，全部当场抓出，无一条进入结论）.** **a1** 把可达性当指令边界判据；**a2** N2 反控「只认 4 字节对齐出现数应下降」实测 12 == 12（这 10 个地址恰好全对齐）⇒ 反控不成立；**a3** N4 反控写成恒真式；**b1** 从立即数中间盲解并当起点；**b2** N2「imm−1 当 vtable」实测 5,731 == 5,731；**c1** B 形态用绝对偏移索引相对 BLOB（偏 4096）；**c2** C6 算术闭合写错（1,212−2 当成 1,204 的来历）；**d1** D7c 用 `int(k,16)` 而 k 已是字符串地址 ⇒ `TypeError`（**崩溃当判据失败**）；**d2** N4 用全表线性扫找首次出现 ⇒ 跑满超时；**e1** 局部对齐无 memo 时每点解 100+ 次 ⇒ 跑不完；**f1** r187f 首版重跑 STARTS 递归下降只为引用三个已有数；**f2** r187f 首版把绝对址 store 算进对象寄存器 ⇒ 4,394 而非 4,053。**族谱**：「把崩溃当判据失败」**第六次**（d1）；「把应然数当实测」**第十八次**（c2）。

**PQ8. 📌 跨家族（执行一件已完成、审计未回件）.** 执行员 **#450**（hy4）用独立脚本 `_r187/exec_hy4/r187_scan.py`，不复用主会话任何代码，独立推段边界 / TypeDescriptor / vtable，10 个类逐类给形态，结论与主会话**逐类相同**（7 A / 2 B / 1 C / 1 个 `.data` 指针槽），自报 checks 10 fails 0；并主动报出「按 3 字节对齐才命中」这类细节差异。审计员 **#451**（deepseek）本轮**未在时限内回件**，如实登记为未取得项。

**PQ9. 📌 未取得（不粉饰）.** ① 审计员 #451 未回件，本轮无第二家族结论；② 残差 265 里那 **3** 条非模板（BaseClass / BlowPipe / LayerClass）仍只逐条登记、无统一解释；③ 局部对齐判据是**局部**的，只证明编码自洽、不证明可达；④ 那 1 条孤立处 `00535A60` 未逐字节解释；⑤ F01 statement 的 1201 / 1211 仍不可复现；⑥ F23 / F35 grade 未改；⑦ `coverage.tsv` / `function_atlas.tsv` 仍不可读；⑧ 86.19% 原值仍不可重算；⑨ C7 三死分支仍各 0 行；⑩ 「哪份是当前版」仍无人覆盖。
'''

SEC_BOARD = '''
## 🟢 R17 第 187 轮（2026-11-28 3x–4x）· R186 两条**陈述**被逐字节测反：「845 条假命中」其实是**不可达的真指令**（5,730/5,731 局部自洽）、「10 张表无 imm32 装点」实测 **10/10 全有**；三层数改全口径 **3,737/4,053 = 92.20%**

**交付一（撤回一个词）**：`_r187/r187e_align.py` **13 断言 / 2 FAIL 如实登记** —— 改用**不依赖可达性**的局部对齐判据（按 `C7` 操作数自描述长度反推起点，要求起点字节为 `C7` 且 `modrm.reg==0` 且立即数偏移恰为 o），5,731 条里 **5,730 局部可对齐、仅 1 条孤立**（`00535A60`）⇒ 「假命中（落在非指令边界上）」是把**不可达**误称成**不是指令**。反控：回看窗 15→1 时 1,200 条里可对齐从 1,200 降到 **96**；平移 +3 字节使比例从 **100.00%** 降到 **25.67%**。

**交付二（撤一层收缩）**：`_r187/r187f_recount.py` **14 断言 0 FAIL** —— 全 5,731 条：对象寄存器 store **4,053**（对象 4,053 / 栈基址 1,337 / 绝对址 341 / 带索引 0，合计 **= 5,731** 闭合）；`disp == COL.mdisp` **3,737 = 92.20%**、放宽 **3,788 = 93.46%**、残差 **265**（模板 **262** / 非模板 **3**：BaseClass / BlowPipe / LayerClass）。⇒ **87.40% 改读 92.20%**（两个作用域，不是矛盾）。

**交付三（10 张表全有装点）**：`_r187/r187d_final.py` **22 断言 0 FAIL** —— **7 张** C7 对象寄存器 store（CarryoverClass `00473777 c706044c7e00`、Dial8Class `004A53DA`、DistributionObject/DiscreteDistributionClass `004E0A8A`、TriColorGaugeClass `004E2AD5`、PKPipe `00632CF9`、TextButtonClass `0071FF65` 与 `0071FFC2`、PBVToolTip `0072403A`）；**1 张** C7 栈 store（PAU_DDSURFACEDESC `004A4937 c74424200c5e7e00`，位移 +0x20）；**2 张** B 形态（PAE `007B2DBA baec7a7f00` → `mov [esi+0x3F338], edx`；PAUWinsockBufferType `007B19C8` → `mov [esi+8], edx`）。位移 == mdisp **7/10**，不等的恰那 3 张（形态不同）。

**交付四（算术闭合）**：口径 P 覆盖 **1,212/1,214**，未覆盖 2 张恰是 B 形态那 2 张；R186c 的 1,204 **= 1,214 − 8 − 2** 闭合。反控四条全真红（imm+1 判等 0、VA+4 查 10 张全空、B 形态用绝对偏移命中从 2 降到 0、种子清空 STARTS 0）。

**交付五（三个中间版本都错了）**：r187a 用可达性当边界判据（12 处全判数据字节）；r187b 从立即数中间盲解（`add al,0x4c` / `lodsb` / `in al,dx`）并当起点；r187c 把绝对偏移当相对偏移索引（偏 rawptr=4096）。r187d 修正后 **22 断言 0 FAIL**、「判为数据字节」首次归零。

**交付六（落盘）**：V568 → **V569**：F01 lim 12,239→**14,490**、F29 lim 16,840→**19,204**，**149,333 B / `b260f1f4…` / CR 0 / 55 行 5 列**，只改两行且只有第 5 列变（16 断言 0 FAIL）；重钉 **40 断言 0 FAIL**（MASTER `7ee9f8ac…`→**`365d5930…`**、两处 floor、gate_runner 1 行、指针四字段含自述 530..569 / 40 份与声明轮次 R187）。**三门** exit 0 / exit 0 / G1=G2=G3=ok；看板 271 ≥ 260 ⇒ 归档 R175+R176（**17 断言 0 FAIL**，CR 保持 2952，1,375,874 → 1,386,736 B 逐项闭合），归档后 **223 行**。

**跨家族**：执行员 **#450**（hy4）用独立脚本不复用主会话代码，10 个类逐类给形态，结论**逐类相同**（7 A / 2 B / 1 C / 1 个 `.data` 指针槽），checks 10 fails 0；审计员 **#451**（deepseek）**未在时限内回件**，如实登记。

**自错 S-187a1..S-187f4（十一处，全部当场抓出）**：可达性当边界判据；N2 反控实测 12==12 不成立；N4 反控恒真；从立即数中间盲解；imm−1 判等 5,731==5,731；绝对偏移索引相对 BLOB（偏 4096）；算术闭合写错（1,212−2 当 1,204 来历）；`int(k,16)` 对字符串地址抛 `TypeError`（**崩溃当判据**）；全表线性扫跑满超时；局部对齐无 memo 跑不完；重跑 STARTS 只为引用已有数；绝对址 store 算进对象寄存器（4,394 vs 4,053）。**族谱**：「把崩溃当判据失败」**第六次**；「把应然数当实测」**第十八次**。

**未取得**：① 审计 #451 未回件；② 残差 265 里 3 条非模板只登记未解释；③ 局部对齐只证编码自洽、不证可达；④ `00535A60` 未逐字节解释；⑤ F01 的 1201/1211 仍不可复现；⑥ F23/F35 grade 未改；⑦ `coverage.tsv`/`function_atlas.tsv` 仍不可读；⑧ 86.19% 原值仍不可重算；⑨ C7 三死分支仍各 0 行；⑩ 「哪份是当前版」仍无人覆盖。
'''

for nm, s in (('R14_COMMON 2.192', SEC_COMMON), ('台账 §1242', SEC_LEDGER),
              ('LEAD_LOCK PQ', SEC_LOCK), ('看板 R187', SEC_BOARD)):
    ck('T1 %s 无 tab / CR' % nm, '\t' not in s and '\r' not in s)
    ck('T2 %s 以换行开头结尾' % nm, s.startswith('\n') and s.endswith('\n'))

rc = io.open(RC, encoding='utf-8', newline='').read()
led = io.open(LED, encoding='utf-8', newline='').read()
lock = io.open(LOCK, encoding='utf-8', newline='').read()
brd = io.open(BRD, encoding='utf-8', newline='').read()
ck('T3 R14_COMMON 末节 == 2.191', '## 2.191' in rc[-60000:], rc.rstrip().split('\n')[-1][:30])
ck('T4 台账末节 == §1241', '## §1241' in led[-60000:], led.rstrip().split('\n')[-1][:30])
ck('T5 LEAD_LOCK 末段码 == PP', '## PP · R17 第 186 轮' in lock[-40000:])
ck('T6 R14_COMMON 尚无 2.192', '## 2.192' not in rc)
ck('T7 台账尚无 §1242', '## §1242' not in led)
ck('T8 LEAD_LOCK 尚无 PQ 段', '## PQ · R17 第 187 轮' not in lock)
ck('T9 看板尚无 R187 段', 'R17 第 187 轮' not in brd)
ck('T9b 看板已归档：R175 / R176 段不在看板里',
   'R17 第 175 轮' not in brd and 'R17 第 176 轮' not in brd)

nrc = rc.rstrip('\n') + '\n' + SEC_COMMON
nled = led.rstrip('\n') + '\n' + SEC_LEDGER
nlock = lock.rstrip('\n') + '\n' + SEC_LOCK
nbrd = brd.rstrip('\n') + '\n' + SEC_BOARD
ck('T10 R14_COMMON CR 保持 1081', nrc.count('\r') == 1081, nrc.count('\r'))
ck('T11 台账 CR 保持 337', nled.count('\r') == 337, nled.count('\r'))
ck('T12 LEAD_LOCK CR 保持 137', nlock.count('\r') == 137, nlock.count('\r'))
ck('T13 看板 CR 保持 0', nbrd.count('\r') == 0, nbrd.count('\r'))
ck('T14 看板新行数 <= 300', nbrd.count('\n') <= 300, nbrd.count('\n'))
ck('T15 四件套都变大', all(len(x.encode()) > len(y.encode()) for x, y in
   ((nrc, rc), (nled, led), (nlock, lock), (nbrd, brd))),
   (len(nrc.encode()) - len(rc.encode()), len(nled.encode()) - len(led.encode()),
    len(nlock.encode()) - len(lock.encode()), len(nbrd.encode()) - len(brd.encode())))

if fails:
    print('★ fail-closed：%d 条未过，不写盘' % len(fails)); sys.exit(1)
print('== 写盘 ==')
for path, newtxt in ((RC, nrc), (LED, nled), (LOCK, nlock), (BRD, nbrd)):
    oldraw = open(path, 'rb').read(); o = hashlib.sha256(oldraw).hexdigest()
    bak = os.path.join(BL, '%s.before_r187_%s.bak' % (os.path.basename(path), stamp))
    fd = os.open(bak, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o644)
    with os.fdopen(fd, 'wb') as f: f.write(oldraw)
    ck('W1 %s 备份独占且 sha 相同' % os.path.basename(path),
       hashlib.sha256(open(bak, 'rb').read()).hexdigest() == o)
    assert open(path, 'rb').read() == oldraw, '母本被外部改动: %s' % path
    io.open(path, 'w', encoding='utf-8', newline='').write(newtxt)
    back = open(path, 'rb').read()
    ck('W2 %s 回读一致' % os.path.basename(path),
       hashlib.sha256(back).hexdigest() == hashlib.sha256(newtxt.encode()).hexdigest())
    print('   %-22s %d -> %d B' % (os.path.basename(path), len(oldraw), len(back)))
print('\n断言 %d 条，FAIL %d 条' % (n, len(fails)))
sys.exit(1 if fails else 0)
