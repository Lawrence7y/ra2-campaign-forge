#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R198 四件套其余三件：GOAL_THREE_TARGETS §1253 / LEAD_LOCK QA / STATUS_BOARD 第 198 轮。
CR 守恒：GOAL 337 / LOCK 137 / BOARD 0。wx 独占备份 + 回读校验。
"""
import os, sys, hashlib, time
ROOT = '/home/t628/projects/ra2-campaign-forge'
T = os.path.join(ROOT, 'lead/next_re_20261117_r14')
LR = os.path.join(ROOT, 'lead')
BL = os.path.join(T, 'R17_LEAD_BASELINE')
fails = []; n = 0
def ck(nm, c, d=''):
    global n; n += 1
    if not c: fails.append(nm)
    print(('PASS ' if c else 'FAIL ') + nm + ((' | ' + str(d)) if d != '' else ''))
def rd(p): return open(p, 'rb').read()
def sha(b): return hashlib.sha256(b).hexdigest()
stamp = time.strftime('%Y%m%d_%H%M%S')

def backup_and_write(path, old_raw, new_txt, tag):
    bak = os.path.join(BL, '%s.before_r198_%s.bak' % (tag, stamp))
    fd = os.open(bak, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o644)
    with os.fdopen(fd, 'wb') as f: f.write(old_raw)
    ck('W1 %s 备份 sha 一致' % tag, sha(rd(bak)) == sha(old_raw))
    assert rd(path) == old_raw, '%s 被外部改动' % tag
    with open(path, 'wb') as f: f.write(new_txt.encode('utf-8'))
    ck('W2 %s 回读一致' % tag, sha(rd(path)) == sha(new_txt.encode('utf-8')))

# ============ 二 · GOAL §1253 ============
PG = os.path.join(LR, 'GOAL_THREE_TARGETS_20261018.md')
g = rd(PG)
ck('G0a 旧 GOAL CR=337', g.count(b'\r') == 337, (g.count(b'\r'), sha(g)[:16]))
ck('G0b 旧 GOAL 以 0x0a 结尾', g.endswith(b'\n'), repr(g[-2:]))
SG = (
'\n## §1253 · R198（2026-11-28）最长虚表 344 槽普查 / 18 对槽位唯一 / CRC +0 上溯终止分类\n\n'
'- **0x7F5C70 = .?AVUnitClass@@ 主表 344 槽，目标地址两两不同**：uniq = 344、重复实现 0 个、'
'连续相同 run 数 = 344。体形态（400 B 窗口到首 ret）：`ret imm` 140 / 裸 `ret` 170 / 无 ret 34；'
'4096 B 窗口只剩 1 个仍无 ret（0x73B470，1244 条、`ret 0x20`）。'
'纯桩 8 个（`xor eax,eax; ret`）+ 裸 `ret` 9 个 = 16 个（与执行员 #489 逐地址一致）。\n'
'- **订正：长表不是通例**。槽数分档 uniq == nslot：`1..7` 960/964、`8..63` 205/229、`64..127` 12/13、'
'**`>=128` 4/8**（0x7E8C94 / 0x7F4960 / 0x7F0508 / 0x7EDCC0 各有重复）。'
'0x7F5C70 是长表里最干净的一张，不能当长表普遍形态。由审计 #491 指出、主会话 r198/m15 逐表复算成立。\n'
'- **反控**：判据改「前 16 字节互异」⇒ 344 掉到 287（−57 / −16.6%），掉幅全来自常量桩成片堆叠'
'（`mov eax,0x1C2; ret` 14 个入口、`ret` 6 个、`xor al,al;ret` 8 个）。按地址判 344 才对。\n'
'- **18 个 (槽号, 默认实现) 在全 14,044 槽上槽位唯一**：14 个不同地址每个只出现在它那一个槽号'
'（槽0/75、槽1/74、槽2/74、槽4/77、槽5/3、槽7/61、槽8/**1**、槽9/72、槽10/35、槽13/8、槽14/72、'
'槽15/72、槽16/59、槽17/57）。唯一例外是纯桩 **0x4C9150**：跨 **33 个槽号**、39 张表、205 个槽位。'
'⇒ 纯桩地址不携带槽位信息，不能当槽号指纹；非纯桩实现地址是稳定不变量。\n'
'- **CRC 状态对象 +0 初值来源（R195 PX6 / R196 PY8 / R197 PZ7 遗留①）终止分类**：331 个调用点逐跳上溯 '
'6 跳，得 NODEF 122（36.9%）/ 结构体字段 107（32.3%）/ 全局对象字段 51（15.4%）/ '
'全局绝对地址寄存器 33（10.0%）/ 本地栈 18（5.4%），合计 331 = 100%。\n'
'- **全局绝对地址类的初值来源已取得**：`mov ecx,0xA8B238` 形态，0xA8B238 落在 .data 的 vsize 内 / '
'rawsize 外（`P.where()` = virt-only、`P.r2o()` = None）⇒ **BSS，文件内无初值字节，映像加载即全 0**，'
'不需要任何指令写入。该地址有 **219** 处 `mov ecx,imm32` 引用、**5** 处绝对寻址写'
'（0x5EF73A/0x67E4E8 写 +0、0x789E77 写 +0xC、0x76EDBA 写 +0x8）。\n'
'- **本地栈 18 站点的调用者准备已取得**：18/18 在宿主调用点前 24 B 内都有 `lea ecx,[esp+K]`'
'（K ∈ {0x1C,0x4C,0xA0,0x0C,0x6C}），且 lea 后紧邻 call 目标即该宿主'
'（0x41F6EE→0x5117D0 / 0x772925→0x644630 / 0x428729→0x645430 / 0x672795→0x6F1920 / 0x5A2BE9→0x71DD80）。'
'其中 0x645583 一路有四槽全写字节证据（+0 = ecx、+4 = 0、+8 = 0、+0xC = eax）。\n'
'- **0x410410 的 27 个调用点落在 27 个不同宿主**（一对一，每宿主 1 次）。其中只有 **2 个**是虚表实现且'
'**恰好占槽 13**：0x410BE0（.?AVAbstractTypeClass@@ / .?AVObjectTypeClass@@）、'
'0x5F6250（.?AVBulletClass@@ / .?AVIsometricTileClass@@ / .?AVObjectClass@@ / .?AVOverlayClass@@ 等 8 张）。\n'
'- **两处自错当场撤回**：① `mov ecx,edi` 当终点不跟 edi ⇒ 假 265 条 OTHER；'
'② 用 `CALLERS[host][0]` 取单个调用者跨层 ⇒ 18 条假 STACK（复算证明这 18 个 lea 后紧邻 call 目标全不是 '
'CRC 族，0/18），改按「宿主 → 全部调用者前 24 B」重测才 18/18 成立。\n'
'- **未取得**：① 18 个栈站点里只有 1 路有四槽写入字节，其余 17 路未逐个验证；'
'② NODEF 122 条的 +0 来源；③ 结构体/全局对象字段 158 条的宿主结构体语义名；'
'④ 18+6 个虚表实现的游戏语义名；⑤ F23/F35 grade；⑥ coverage.tsv/function_atlas.tsv 不可读；'
'⑦ 86.19% 原值不可重算；⑧ C7 三死分支各 0 行；⑨ C11 十二个永不 FAIL id 未动。\n'
'- **跨家族**：执行员 #489（hy4）20/20 断言 PASS，Q1/Q2/Q5/Q6 逐值一致、16 个纯桩地址逐地址一致；'
'执行员 #490（hy4）卡在 `md_lite.disasm` 解包错误，**未交付**（probe_stdout.txt 0 B）；'
'审计员 #491（deepseek，9 回合 / 1.83 分）三条主张全部复算一致，并额外指出两处口径问题均被采纳'
'（长表 4/8 不是 8/8、前 16 字节去重 287 不是 344）。\n'
)
newg = g.decode('utf-8') + SG
ng = newg.encode('utf-8')
ck('G1 新 GOAL CR 保持 337', ng.count(b'\r') == 337, ng.count(b'\r'))
ck('G2 §1253 唯一', ng.count('## §1253 · R198'.encode()) == 1, ng.count('## §1253 · R198'.encode()))
if fails:
    print('ABORT: %s' % fails); sys.exit(1)
backup_and_write(PG, g, newg, 'GOAL')
print('GOAL %d -> %d B (CR %d)' % (len(g), len(ng), ng.count(b'\r')))

# ============ 三 · LEAD_LOCK QA ============
PL = os.path.join(LR, 'LEAD_LOCK')
l = rd(PL)
ck('L0a 旧 LOCK CR=137', l.count(b'\r') == 137, (l.count(b'\r'), sha(l)[:16]))
ck('L0b 旧 LOCK 以 0x0a 结尾', l.endswith(b'\n'), repr(l[-2:]))
ck('L0c 旧 LOCK 末段是 PZ', b'**PZ7.' in l, b'**PZ7.' in l)
SL = (
'\n\n## QA · R17 第 198 轮（2026-11-28 14x–15x）· 最长虚表 0x7F5C70 的 344 槽两两不同；'
'18 对 (槽号, 实现) 槽位唯一且唯一例外是纯桩；CRC 状态对象 +0 初值来源的上溯终止分类（BSS 零填充 / 本地栈 18 站点的调用者准备）\n\n'
'**QA1. 🔴 交付一：0x7F5C70（.?AVUnitClass@@ 主表）344 槽，目标地址两两不同.** '
'复算基线 COL 1214 / VT 1214 / 槽总 14,044 一致。344 个槽目标**无一对相同**（uniq 344、重复实现 0、'
'连续相同 run 数 344 且每 run 长 1）。体形态（400 B 窗口到首 ret）：`ret imm` 140 / 裸 `ret` 170 / 无 ret 34；'
'4096 B 窗口只剩 **1** 个仍无 ret（`0x73B470`，1244 条 / `sub esp,0x1b4` / `ret 0x20`）。'
'纯桩按语义 `xor eax,eax; ret` 得 **8**，放宽到裸 `c3 90 90 90` 再得 **9**，合计 **16**，与执行员 #489 逐地址一致。'
'**反控**：判据改「前 16 字节互异」⇒ 344 → **287**（−57 / −16.6%），掉幅全来自常量桩成片堆叠'
'（`mov eax,0x1C2; ret` 14 个入口、`ret` 6、`xor al,al;ret` 8）。\n\n'
'**QA2. 🔴 交付二：一条被推翻的隐含前提 —— 长表不是通例.** 槽数分档 uniq == nslot：'
'`1..7` **960/964 = 0.9959** / `8..63` **205/229 = 0.8952** / `64..127` **12/13 = 0.9231** / '
'`>=128` **4/8 = 0.5000**（0x7E8C94 341→339、0x7F4960 309→305、0x7F0508 161→159、0x7EDCC0 157→154）。'
'⇒ 0x7F5C70 是长表里最干净的一张，**不能**当长表普遍形态。'
'此处由审计 #491 指出、主会话 `_r198/m15_final_verify.py` 逐表复算成立（VA1/VA2/VA3 三断言）。\n\n'
'**QA3. 🟠 交付三：18 个 (槽号, 默认实现) 在全 14,044 个槽位上槽位唯一，唯一例外是纯桩.** '
'14 个不同地址每个**只出现在它那一个槽号**：槽0 0x410260/75 张、槽1 0x410300/74、槽2 0x410310/74、'
'槽4 0x410450/77、槽5 0x5F5E80/3、槽7 0x4103E0/61、槽8 0x4105A0/**1**、槽9 0x410470/72、槽10 0x410480/35、'
'槽13 0x5F6250/8、槽14 0x410490/72、槽15 0x4104A0/72、槽16 0x4104B0/59、槽17 0x410440/57。'
'**唯一例外 0x4C9150**（纯桩 `33 C0 C3`）跨 **33 个槽号**（0..24 除 25/26、27/28/29/32/35/40/238/292）、'
'39 张表、205 个槽位。⇒ 纯桩地址**不携带槽位信息**，不能当槽号指纹。'
'**反控**：收窄到 L 的 78 张表结论不变（0x4C9150 收窄到 9 个槽号）；主表/子表拆分后也不变。'
'0x7F5C70 自身命中 6 个（槽 0/1/2/4/7/16），与期望槽号逐一相符。\n\n'
'**QA4. 🟠 交付四：CRC 状态对象 +0 初值来源 —— 上溯终止分类（覆盖 331/331 = 100%）.** '
'按「同函数内 ecx 最近一次整字赋值」逐跳上溯 6 跳：**NODEF 122（36.9%）/ 结构体字段 107（32.3%）/ '
'全局对象字段 51（15.4%）/ 全局绝对地址寄存器 33（10.0%）/ 本地栈 18（5.4%）**。'
'**全局绝对地址类（33 条）已取得初值来源**：`mov ecx,0xA8B238` 形态；0xA8B238 在 .data 的 vsize 内 / '
'rawsize 外（`P.where()`=virt-only、`P.r2o()`=None）⇒ **BSS，文件内无初值字节，加载即全 0**，'
'无需任何指令写入。该地址有 **219** 处 `mov ecx,imm32`、**5** 处绝对寻址写（0x5EF73A/0x67E4E8 写 +0、'
'0x789E77 写 +0xC、0x76EDBA 写 +0x8）。对照 0x817BD0（真 .data，文件初值 `53475259534d4b31…`）有 **0** 处绝对写。\n\n'
'**QA5. 🟠 交付五：本地栈 18 站点的调用者准备（18/18）.** 每个站点的宿主函数，其调用者在调用点前 24 B 内'
'**18/18** 都有 `lea ecx,[esp+K]`（K ∈ {0x1C, 0x4C, 0xA0, 0x0C, 0x6C}），且 lea 之后紧邻的 call 目标**就是该宿主**：'
'0x41F6EE→0x5117D0 / 0x772925→0x644630 / 0x428729→0x645430 / 0x672795→0x6F1920 / 0x5A2BE9→0x71DD80。'
'其中 **0x645583 一路给出四槽全写字节证据**：`lea ecx,[esp+0xa0]`(0x428729) → `mov dword ptr [esp+0xa0],ecx`(+0) / '
'`[esp+0xa4],0`(+4) / `[esp+0xa8],0`(+8) / `[esp+0xac],eax`(+0xC)。\n\n'
'**QA6. 🟡 交付六：0x410410 的 27 个宿主身份.** 27 个调用点落在 **27 个不同**宿主入口（一对一，每宿主 1 次）。'
'其中只有 **2 个**是虚表实现且**恰好占槽 13**：`0x410BE0`（.?AVAbstractTypeClass@@ / .?AVObjectTypeClass@@）、'
'`0x5F6250`（.?AVBulletClass@@ / .?AVIsometricTileClass@@ / .?AVObjectClass@@ / .?AVOverlayClass@@ 等 8 张）。'
'其余 25 个不在任何虚表内。⇒ R194「槽 13 有 k 个族」在宿主间接面上再收一格：直接调 CRC 的 27 个宿主只有 2 个占槽 13。\n\n'
'**QA7. 📌 自错（当场抓出，无一条进入结论）.** ① m1「纯桩 8」vs 执行员「16」不是判据松紧，是我把裸 `ret` 排除在桩外；'
'② m1 的 `Q2d 目标地址单调递增` 与 `R3a 前 16 字节去重 344` 两条**断言预期值写错**（实测 343 对里只有 196 对递增、'
'前 16 字节去重是 287）；③ m9 第一版 `find4` 是 O(n²)，跑 8 分钟被 kill，改滑窗后完成；'
'④ m10 把 `mov ecx,edi` 当终点不跟 edi ⇒ 假 265 条 OTHER；'
'⑤ m12 用 `CALLERS[host][0]` 取单个调用者跨层 ⇒ **18 条假 STACK**，由 m16 复算证明这 18 个 lea 后紧邻 call 目标'
'**全不是** CRC 族（0/18）后否掉，改按「宿主 → 全部调用者前 24 B」重测才 18/18 成立。'
'⇒ QA5 那一行的证据链是**修补后口径**，不是初版口径，必须按此理解。\n\n'
'**QA8. 🟡 落盘与门禁.** R14_COMMON 追加 **§2.203（8,796 B ⇒ floor 4,398）**，CR 保持 1081；'
'GOAL 追加 **§1253**，CR 保持 337；LEAD_LOCK 追加 **QA**，CR 保持 137；STATUS_BOARD 追加第 198 轮，CR 保持 0。'
'看板开局 **231 行 < 260** ⇒ 本轮**不归档**。台账 V581 → V582（只改 F55）+ 重钉 + 三门回归见本节末。\n\n'
'**QA9. ⚪ 未取得（不粉饰）.** ① 18 个栈站点只有 1 路拿到四槽写入字节，其余 17 路只证到调用者准备了栈缓冲；'
'② NODEF 122 条的 +0 来源；③ 结构体字段 107 + 全局对象字段 51 共 158 条的宿主结构体语义名；'
'④ 18+6 个虚表实现的游戏语义名；⑤ F23/F35 grade 未改；⑥ `coverage.tsv`/`function_atlas.tsv` 仍不可读；'
'⑦ 86.19% 原值仍不可重算；⑧ C7 三死分支仍各 0 行；⑨ C11 十二个永不 FAIL id 未动。\n'
)
newl = l.decode('utf-8') + SL
nl = newl.encode('utf-8')
ck('L1 新 LOCK CR 保持 137', nl.count(b'\r') == 137, nl.count(b'\r'))
ck('L2 ## QA 唯一', nl.count('## QA · R17 第 198 轮'.encode()) == 1)
ck('L3 旧段 PZ 仍在', b'**PZ7.' in nl, True)
if fails:
    print('ABORT before LOCK write: %s' % fails); sys.exit(1)
backup_and_write(PL, l, newl, 'LEAD_LOCK')
print('LEAD_LOCK %d -> %d B (CR %d)' % (len(l), len(nl), nl.count(b'\r')))

# ============ 四 · STATUS_BOARD 第 198 轮 ============
PB = os.path.join(T, 'STATUS_BOARD.md')
b = rd(PB)
ck('B0a 旧 BOARD CR=0 / 行数', b.count(b'\r') == 0, (b.count(b'\r'), b.count(b'\n')))
ck('B0b 开局行数 < 260（不归档）', b.count(b'\n') < 260, b.count(b'\n'))
SB = (
'\n\n## 第 198 轮（2026-11-28）· 最长虚表 0x7F5C70 的 344 槽两两不同；'
'18 对槽位唯一（唯一例外是纯桩 0x4C9150 跨 33 槽号）；CRC +0 初值来源上溯分类（BSS 零填充 33 条 + 本地栈 18 站点）\n\n'
'**交付一.** 0x7F5C70 = .?AVUnitClass@@ 主表 344 槽，344 个目标地址**两两不同**（uniq 344 / 重复 0 / '
'run 数 344 每 run 长 1）。体形态（400 B 到首 ret）`ret imm` 140 / 裸 `ret` 170 / 无 ret 34；'
'4096 B 窗口只剩 1 个仍无 ret（0x73B470，1244 条 / `ret 0x20`）。纯桩 8 个 + 裸 `ret` 9 个 = 16 个，'
'与执行员 #489 **逐地址一致**。\n\n'
'**交付二（订正）.** 长表**不是**通例：槽数分档 uniq == nslot 为 `1..7` 960/964、`8..63` 205/229、'
'`64..127` 12/13、**`>=128` 4/8**（0x7E8C94 / 0x7F4960 / 0x7F0508 / 0x7EDCC0 各有重复）。'
'0x7F5C70 是长表里最干净的一张。由审计 #491 指出、主会话 `_r198/m15` 逐表复算成立。'
'**反控**：判据改「前 16 字节互异」⇒ 344 → 287（−57 / −16.6%），掉幅全来自常量桩成片堆叠'
'（`mov eax,0x1C2; ret` 14 个入口）。\n\n'
'**交付三.** 18 个 (槽号, 默认实现) 在全 14,044 槽上槽位唯一：14 个不同地址每个只出现在它那一个槽号'
'（槽0/75、槽1/74、槽2/74、槽4/77、槽5/3、槽7/61、槽8/**1**、槽9/72、槽10/35、槽13/8、槽14/72、槽15/72、'
'槽16/59、槽17/57）；**唯一例外 0x4C9150**（纯桩 `33 C0 C3`）跨 **33 个槽号** / 39 张表 / 205 槽位。'
'⇒ 纯桩地址不携带槽位信息；非纯桩实现地址是稳定槽号指纹。\n\n'
'**交付四.** CRC 状态对象 +0 初值来源的**上溯终止分类（331/331 = 100%）**：NODEF 122（36.9%）/ '
'结构体字段 107（32.3%）/ 全局对象字段 51（15.4%）/ 全局绝对地址寄存器 33（10.0%）/ 本地栈 18（5.4%）。'
'**全局绝对地址类已取得初值来源**：`mov ecx,0xA8B238`，该地址在 .data 的 vsize 内 / rawsize 外'
'（virt-only、`r2o()` = None）⇒ **BSS，文件内无初值字节，加载即全 0**，无需指令写入；'
'有 219 处 `mov ecx,imm32` 引用、5 处绝对寻址写（0x5EF73A/0x67E4E8 写 +0、0x789E77 写 +0xC、0x76EDBA 写 +0x8）。'
'对照 0x817BD0（真 .data，初值 `53475259534d4b31…`）有 0 处绝对写。\n\n'
'**交付五.** 本地栈 18 站点：宿主调用点前 24 B 内 **18/18** 有 `lea ecx,[esp+K]`'
'（K ∈ {0x1C,0x4C,0xA0,0x0C,0x6C}），lea 后紧邻 call 目标即该宿主（0x41F6EE→0x5117D0 / 0x772925→0x644630 / '
'0x428729→0x645430 / 0x672795→0x6F1920 / 0x5A2BE9→0x71DD80）。其中 0x645583 一路有四槽全写字节证据'
'（+0 = ecx、+4 = 0、+8 = 0、+0xC = eax）。\n\n'
'**交付六.** 0x410410 的 27 个调用点落在 **27 个不同宿主**（一对一）。只有 **2 个**是虚表实现且**恰好占槽 13**：'
'0x410BE0（.?AVAbstractTypeClass@@ / .?AVObjectTypeClass@@）、0x5F6250（.?AVBulletClass@@ 等 8 张）。'
'其余 25 个不在任何虚表内。\n\n'
'**自错（当场抓出，无一条进入结论）.** ① m1「纯桩 8」vs 执行员「16」是我把裸 `ret` 排除在桩外，不是判据松紧；'
'② m1 有两条断言预期值写错（`Q2d` 单调递增、`R3a` 前 16 字节去重 344）；③ m9 第一版 O(n²) 跑 8 分钟被 kill；'
'④ m10 把 `mov ecx,edi` 当终点不跟 edi ⇒ 假 265 条 OTHER；'
'⑤ m12 用 `CALLERS[host][0]` 取单个调用者跨层 ⇒ **18 条假 STACK**（复算证明 lea 后紧邻 call 目标全不是 CRC 族，0/18），'
'改按「宿主 → 全部调用者前 24 B」重测才 18/18 成立 ⇒ 交付五的证据链是修补后口径。\n\n'
'**跨家族.** 执行员 **#489**（hy4）20/20 断言 PASS，Q1/Q2/Q5/Q6 逐值一致、16 个纯桩地址逐地址一致；'
'执行员 **#490**（hy4）卡在 `md_lite.disasm` 解包错误（`TypeError: cannot unpack non-iterable CsInsn`），'
'**未交付**（`probe_stdout.txt` 0 B）；审计员 **#491**（deepseek，9 回合 / 1.83 分）三条主张全部复算一致，'
'并额外指出两处口径问题且均被采纳。\n\n'
'**未取得.** ① 18 个栈站点只有 1 路拿到四槽写入字节，其余 17 路只证到调用者准备了栈缓冲；'
'② NODEF 122 条的 +0 来源；③ 158 条结构体/全局对象字段的宿主语义名；④ 18+6 个虚表实现的游戏语义名；'
'⑤ F23/F35 grade；⑥ `coverage.tsv`/`function_atlas.tsv` 仍不可读；⑦ 86.19% 原值不可重算；'
'⑧ C7 三死分支各 0 行；⑨ C11 十二个永不 FAIL id 未动。\n'
)
newb = b.decode('utf-8') + SB
nbn = newb.encode('utf-8')
ck('B1 新 BOARD CR 保持 0', nbn.count(b'\r') == 0, nbn.count(b'\r'))
ck('B2 新 BOARD 行数 <= 300', nbn.count(b'\n') <= 300, nbn.count(b'\n'))
ck('B3 第 198 轮唯一', nbn.count('## 第 198 轮'.encode()) == 1)
if fails:
    print('ABORT before BOARD write: %s' % fails); sys.exit(1)
backup_and_write(PB, b, newb, 'STATUS_BOARD.md')
print('STATUS_BOARD %d -> %d B (CR %d, %d 行)' % (len(b), len(nbn), nbn.count(b'\r'), nbn.count(b'\n')))
print('FAILS=%d' % len(fails))
