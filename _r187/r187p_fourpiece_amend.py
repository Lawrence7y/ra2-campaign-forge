# -*- coding: utf-8 -*-
"""R187 P：四件套订正段追加（审计 #451 回来之后）。fail-closed：旧 sha + CR 硬闸。

本轮四件套已写过一次（§2.192 / §1242 / PQ / 看板 R187）。之后审计员 #451 回件，抓出我的一处
**口径错误**（7/10 应为 8/10），已落 V570 并重钉。本脚本在四件套各追加一个**订正段**，
不修改已写内容（append-only），把「错在哪、谁抓的、怎么复算的」留成可查记录。
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
    ck('H0 %s CR == %d' % (os.path.basename(p), b.count(b'\r') == cr), b.count(b'\r') == cr, b.count(b'\r'))

ADD_COMMON = '''
### 2.192 补订 · 审计 #451 抓出的一处口径错误：7/10 应为 8/10（V569 → V570）

上面第六节写的「位移 == COL.mdisp」在 10 张表上是 **7/10** —— **这一句错了**。跨家族审计员 **#451**（deepseek / 33 回合 / 14.85 分 / **OVERTIME，实测 14.85 分 vs 预算 8 分**）在主张 4 里点出：「r187d 直接拿原始 disp 比 mdisp，把这个算成不等，是本卡最实质的定量口径问题」。

**错在哪.** 那张走栈 store 的表（`?$DynamicVectorClass@PAU_DDSURFACEDESC@@`）在 `004A4937` 处是 `c74424200c5e7e00` = `mov dword ptr [esp + 0x20], 0x7E5E0C`。我拿 `disp = 0x20 ≠ mdisp = 0` 就判「不等」。但**对象基址不是 esp**：同函数 `004A492D` 有 `lea edx, [esp + 0x18]` 建立栈上临时对象，之后 **2 条 push** ⇒ 现行 esp = lea 时的 esp − 8，于是 `[esp + 0x20] = (S − 8) + 0x20 = S + 0x18 =` **对象基址 + 0**。同对象上 `[esp+0x30]`→基址 **+0x10** 置 0、`[esp+0x34]`→基址 **+0x14** 置 **0xa**，与另一 DynVec 位点 `0072403A` 的 `[ecx]=vt / [ecx+0x14]=0xa / [ecx+0x10]=ebx` 签名**完全一致**。⇒ **归一化基址后 8/10 落在对象自身 +0**，剩下 2 张是 B 形态、落在容器成员内。

**怎么复算的（§2.12 规则 D：审计结论必须主会话亲自复算）.** `_r187/r187l_audit_recheck.py`（**35 断言 0 FAIL**）：逐指令算 esp 相对量（`lea edx,[esp+0x18]` → 2 条 push → 现行 esp 相对量 −8）与 DynVec 成员初始化签名双证，两条独立判据同时指向「对象基址 +0」。

**审计另外两条我漏写的事实，已并入本条（均复算成立）.** (a) 那两张 B 形态表所在的**同一构造函数**里，稍后各有一条 C7 把**另一张 mdisp==0 的主表**装到 `[esi]+0`：`007B1A20 c706bc797f00` → **0x7F79BC WinsockInterfaceClass**、`007B2E2D c7066c7a7f00` → **0x7F7A6C UDPInterfaceClass** ⇒ 这两张 DynVec **不是对象基类虚表**，而是被构造对象内嵌容器成员自身的 vtbl；且这两张表在**整个文件**里各只出现 **1 次**。(b) 第 12 处（`00874F6C`，在 `.data`）是**数据侧偶合** —— 邻近 dword 串 `007F4FC3 / 007F51C4 / 007F53C6 / 007F54C7 / 007F57C8 / 007F59CA / 007F5BCB / 007F5DCC / 007F5FCD` 里除 `007F57C8` 外都不是 vtable 头，该处标为「非指令」。

**审计另外三条主张我复算成立并采纳.** ① COL+0 签名实测**只出现 0**（卡面允许 {0,1}）；COL 一对一（1214 个不同 COL 各被恰一张 vtable 引用）；CHD+0 签名 1214/1214 全 0。② `symbols.json` 988 类：34 个 `vtable_va` 为 null、954 个与 VTS 逐值且类名相同、**0 个不符**。③ C7 口径的旁证：`mod==3`（目的寄存器、非内存写）**0 条**；形态分布 mod0 无SIB **3,084** / mod1 无SIB **1,259** / mod1 有SIB **1,100** / mod2 无SIB **200** / mod2 有SIB **88**；imm 槽 **5,731** 个、冲突 **0**；imm 槽落 4 字节对齐的 **1,626**、不对齐 **4,105**。

**审计的一条口径提醒我记下但未改正文.** 它指出「vtable 的枚举规则本身就是『4 字节 dword 落在 .text 前、前一个 dword 恰为某 COL 基址』，所以『配对 1214/1214』有一部分是定义使然，不是独立发现」—— 这与 R186 §2.191 六「每 COL 恰一张表是构造性事实」是同一件事，已有登记，不重复改。

**落盘.** V569 → **V570**：F29 limitations 19,204 → **20,898**，总 **151,027 B / `67c18703…` / CR 0 / 55 行 5 列**；只改 F29 一行、只有第 5 列变，F01 **一字未动**（15 断言 0 FAIL）。重钉 40 断言 0 FAIL：MASTER `365d5930…` → **`e6762221…`**，`FLOORS['F29']` (3435,19204)→(3435,20898)、`FLOORS['F01']` 仍 (458,14490)，指针自述「530..569 / 40 份」→「530..570 / 41 份」。三门 exit 0 / exit 0 / G1=G2=G3=ok。

**自错 S-187m1（一处，审计抓出后主会话复算才认）.** 把「原始 disp ≠ mdisp」直接当成「装点位移 ≠ mdisp」，**没有归一化栈基址**。这是本轮唯一进入结论的错误，性质与族谱里「把应然数当实测」不同 —— 它是「**判据少了一步归一化**」，应新开一族：**「口径少一步」（第一次）**。
'''

ADD_LEDGER = '''
## §1242 补订 R187：审计 #451 抓出的一处口径错误（7/10 → 8/10），并入其三条成立主张

**一·错在哪.** F29 的 10 张表「位移 == COL.mdisp」我原报 **7/10**，错。那张走栈 store 的 `?$DynamicVectorClass@PAU_DDSURFACEDESC@@`（`004A4937 c74424200c5e7e00`）原始 `disp = 0x20`，但对象基址不是 esp：同函数 `004A492D` 的 `lea edx,[esp+0x18]` 建立栈上临时对象、之后 **2 条 push** ⇒ 现行 esp − 8，`[esp+0x20] = (S−8)+0x20 = S+0x18 =` **对象基址 + 0**；同对象 `[esp+0x30]`→基址 **+0x10** 置 0、`[esp+0x34]`→基址 **+0x14** 置 **0xa**，与 `0072403A` 的 DynVec 签名一致 ⇒ **8/10 落在对象自身 +0**。

**二·复算.** `_r187/r187l_audit_recheck.py` **35 断言 0 FAIL**（逐指令 esp 相对量 + DynVec 签名双证）。审计员 **#451**（deepseek / 33 回合 / **14.85 分 vs 预算 8 分 ⇒ OVERTIME**）主张 4 指出该错，主张 1/2/3/5 及三条补测经复算**全部成立并采纳**。

**三·并入审计两条漏写事实.** (a) 两张 B 形态所在同一构造函数里各有一条 C7 把**另一张 mdisp==0 主表**装到 `[esi]+0`：`007B1A20` → **0x7F79BC WinsockInterfaceClass**、`007B2E2D` → **0x7F7A6C UDPInterfaceClass** ⇒ 两张 DynVec 是**内嵌容器成员自身的 vtbl**、非对象基类虚表；两张表在整个文件里各只出现 **1 次**。(b) 第 12 处 `00874F6C`（`.data`）是**数据侧偶合**，邻近 dword 串除 `007F57C8` 外都不是 vtable 头。

**四·审计三条补测（复算成立）.** COL+0 签名只出现 0；COL 一对一 1214；CHD+0 全 0。`symbols.json` 988 类 = 34 null + 954 逐值且类名相同（**0 不符**）。C7 口径：`mod==3` **0 条**、形态分布 3,084 / 1,259 / 1,100 / 200 / 88、imm 槽 5,731 冲突 0、对齐 1,626 / 不对齐 4,105。

**五·落盘.** V569 → **V570**（F29 lim 19,204→**20,898**，**151,027 B / `67c18703…` / CR 0 / 55 行 5 列**，只改 F29 一行且只有第 5 列变、F01 一字未动）；重钉 **40 断言 0 FAIL**（MASTER `365d5930…`→**`e6762221…`**、F29 floor →(3435,20898)、指针自述 530..570 / 41 份）；三门 exit 0 / exit 0 / G1=G2=G3=ok。

**六·族谱新增.** S-187m1「判据少了一步归一化」⇒ **「口径少一步」第一次**（与「把应然数当实测」「把崩溃当判据失败」并列）。
'''

ADD_LOCK = '''
**PQ10. 🔴 审计 #451 回件（OVERTIME）并抓出本轮**唯一进入结论的错误**：7/10 应为 8/10。** 审计员 **#451**（deepseek / 33 回合 / **14.85 分 vs 预算 8 分 ⇒ OVERTIME**）主张 4 指出：`r187d` 直接拿**原始 disp** 比 mdisp，把栈那处算成「不等」，是**口径少了一步归一化**。复算成立 —— 那张 `?$DynamicVectorClass@PAU_DDSURFACEDESC@@` 在 `004A4937` 是 `c74424200c5e7e00` = `mov [esp+0x20], 0x7E5E0C`，但同函数 `004A492D` 的 `lea edx,[esp+0x18]` 建立栈上临时对象、之后 **2 条 push** ⇒ 现行 esp − 8，`[esp+0x20] = (S−8)+0x20 = S+0x18 =` **对象基址 + 0**；同对象 `[esp+0x30]`→基址 **+0x10** 置 0、`[esp+0x34]`→基址 **+0x14** 置 **0xa**，与 `0072403A` 的 DynVec 签名一致 ⇒ **8/10 落在对象自身 +0**。复算脚本 `_r187/r187l_audit_recheck.py` **35 断言 0 FAIL**（逐指令 esp 相对量 + DynVec 签名**双证**）。

**PQ11. ✅ 审计另两条我漏写的事实，已复算并入.** (a) 两张 B 形态表所在的**同一构造函数**里，稍后各有一条 C7 把**另一张 mdisp==0 的主表**装到 `[esi]+0`：`007B1A20 c706bc797f00` → **0x7F79BC WinsockInterfaceClass**、`007B2E2D c7066c7a7f00` → **0x7F7A6C UDPInterfaceClass** ⇒ 这两张 DynVec **不是对象基类虚表**，是**被构造对象内嵌容器成员自身的 vtbl**；两张表在**整个文件**里各只出现 **1 次**。(b) 第 12 处 `00874F6C`（`.db`，实为 `.data`）是**数据侧偶合** —— 邻近 dword 串 `007F4FC3 / 007F51C4 / 007F53C6 / 007F54C7 / 007F57C8 / 007F59CA / 007F5BCB / 007F5DCC / 007F5FCD` 里除 `007F57C8` 外都不是 vtable 头。

**PQ12. ✅ 审计三条补测，复算后全部采纳.** ① `COL+0` 签名实测**只出现 0**（卡面允许 {0,1}）；COL **一对一**（1214 个不同 COL 各被恰一张 vtable 引用）；`CHD+0` 签名 1214/1214 全 0。② `symbols.json` **988** 类 = **34** 个 `vtable_va` 为 null + **954** 个与 VTS 逐值且类名相同、**0 个不符**。③ C7 口径旁证：`mod==3`（目的寄存器、非内存写）**0 条**；形态分布 mod0 无SIB **3,084** / mod1 无SIB **1,259** / mod1 有SIB **1,100** / mod2 无SIB **200** / mod2 有SIB **88**；imm 槽 **5,731** 个、冲突 **0**；imm 槽落 4 字节对齐 **1,626**、不对齐 **4,105**。

**PQ13. 📌 审计一条口径提醒（登记不改正文）.** 它指出「vtable 的枚举规则本身就是『首 dword ∈ .text 且前一 dword == 某 COL』，故『配对 1214/1214』有一部分是**定义使然**、不是独立发现」—— 与 R186 §2.191 六「每 COL 恰一张表是构造性事实」同一件事，已有登记，不重复改。

**PQ14. ✅ 订正落盘 V569 → V570.** F29 limitations 19,204 → **20,898**，总 **151,027 B / `67c18703…` / CR 0 / 55 行 5 列**；只改 F29 一行、只有第 5 列变，**F01 一字未动**（15 断言 0 FAIL）。重钉 **40 断言 0 FAIL**：MASTER `365d5930…` → **`e6762221…`**，`FLOORS['F29']` (3435,19204)→(3435,20898)、`FLOORS['F01']` 仍 (458,14490)，指针自述「530..569 / 40 份」→「**530..570 / 41 份**」。三门 exit 0 / exit 0 / G1=G2=G3=ok。

**PQ15. 📌 族谱新增一族：S-187m1「判据少了一步归一化」.** 这不是「把应然数当实测」，也不是「把崩溃当判据失败」—— 判据本身算得出数、数也没错，错在**拿原始 disp 比 mdisp 而没有先归一化栈基址**。记为「**口径少一步**」**第一次**。⇒ 教训：凡是「某字段 == 某期望值」的判据，先问「这个字段是在哪个基址下量的」。
'''

ADD_BOARD = '''
**🔴 审计 #451 回件（OVERTIME）并抓出本轮唯一进入结论的错误：7/10 应为 8/10** —— 审计员 **#451**（deepseek / 33 回合 / **14.85 分 vs 预算 8 分 ⇒ OVERTIME**）指出 `r187d` 直接拿**原始 disp** 比 mdisp，把栈那处算成「不等」。复算成立：那张 `?$DynamicVectorClass@PAU_DDSURFACEDESC@@` 在 `004A4937` 是 `c74424200c5e7e00` = `mov [esp+0x20], 0x7E5E0C`，但同函数 `004A492D` 的 `lea edx,[esp+0x18]` 建立栈上临时对象、之后 **2 条 push** ⇒ 现行 esp − 8，`[esp+0x20] = (S−8)+0x20 = S+0x18 =` **对象基址 + 0**；同对象 `[esp+0x30]`→基址 **+0x10** 置 0、`[esp+0x34]`→基址 **+0x14** 置 **0xa**，与 `0072403A` 的 DynVec 签名一致 ⇒ **8/10 落在对象自身 +0**。复算 `_r187/r187l_audit_recheck.py` **35 断言 0 FAIL**（逐指令 esp 相对量 + DynVec 签名双证）。

**审计另两条漏写事实，已复算并入**：(a) 两张 B 形态表所在**同一构造函数**里各有一条 C7 把**另一张 mdisp==0 主表**装到 `[esi]+0` —— `007B1A20` → **0x7F79BC WinsockInterfaceClass**、`007B2E2D` → **0x7F7A6C UDPInterfaceClass** ⇒ 这两张 DynVec 是**内嵌容器成员自身的 vtbl**、非对象基类虚表，且两张表在整个文件里各只出现 **1 次**；(b) 第 12 处 `00874F6C`（`.data`）是**数据侧偶合**，邻近 dword 串除 `007F57C8` 外都不是 vtable 头。

**审计三条补测（复算采纳）**：COL+0 签名只出现 0 / COL 一对一 1214 / CHD+0 全 0；`symbols.json` 988 = 34 null + 954 逐值且类名相同（**0 不符**）；C7 口径 `mod==3` **0 条**、形态分布 3,084 / 1,259 / 1,100 / 200 / 88、imm 槽 5,731 冲突 0、对齐 1,626 / 不对齐 4,105。

**订正落盘 V569 → V570**：F29 lim 19,204→**20,898**，**151,027 B / `67c18703…` / CR 0 / 55 行 5 列**，只改 F29 一行且只有第 5 列变、**F01 一字未动**（15 断言 0 FAIL）；重钉 **40 断言 0 FAIL**（MASTER `365d5930…`→**`e6762221…`**、F29 floor →(3435,20898)、指针自述 **530..570 / 41 份**）；三门 exit 0 / exit 0 / G1=G2=G3=ok。

**族谱新增**：**S-187m1「判据少了一步归一化」⇒「口径少一步」第一次**（与「把应然数当实测」「把崩溃当判据失败」并列）。教训：凡「某字段 == 某期望值」的判据，先问「这个字段是在哪个基址下量的」。
'''

for nm, s in (('R14_COMMON 补订', ADD_COMMON), ('台账 补订', ADD_LEDGER),
              ('LEAD_LOCK 补订', ADD_LOCK), ('看板 补订', ADD_BOARD)):
    ck('T1 %s 无 tab / CR' % nm, '\t' not in s and '\r' not in s)
    ck('T2 %s 以换行开头结尾' % nm, s.startswith('\n') and s.endswith('\n'))

rc = io.open(RC, encoding='utf-8', newline='').read()
led = io.open(LED, encoding='utf-8', newline='').read()
lock = io.open(LOCK, encoding='utf-8', newline='').read()
brd = io.open(BRD, encoding='utf-8', newline='').read()
ck('T3 R14_COMMON 已有 2.192', '## 2.192' in rc[-60000:])
ck('T4 台账已有 §1242', '## §1242' in led[-60000:])
ck('T5 LEAD_LOCK 已有 PQ 段', '## PQ · R17 第 187 轮' in lock[-40000:])
ck('T6 四件套尚无补订标记',
   '2.192 补订' not in rc and '§1242 补订' not in led
   and 'PQ10.' not in lock and '审计 #451 回件' not in brd)
ck('T7 看板 CR == 0', brd.count('\r') == 0, brd.count('\r'))

nrc = rc.rstrip('\n') + '\n' + ADD_COMMON
nled = led.rstrip('\n') + '\n' + ADD_LEDGER
nlock = lock.rstrip('\n') + '\n' + ADD_LOCK
nbrd = brd.rstrip('\n') + '\n' + ADD_BOARD
ck('T10 R14_COMMON CR 保持 1081', nrc.count('\r') == 1081, nrc.count('\r'))
ck('T11 台账 CR 保持 337', nled.count('\r') == 337, nled.count('\r'))
ck('T12 LEAD_LOCK CR 保持 137', nlock.count('\r') == 137, nlock.count('\r'))
ck('T13 看板 CR 保持 0', nbrd.count('\r') == 0, nbrd.count('\r'))
ck('T14 看板新行数 <= 300', nbrd.count('\n') <= 300, nbrd.count('\n'))
ck('T15 四件套都变大', all(len(x.encode()) > len(y.encode()) for x, y in
   ((nrc, rc), (nled, led), (nlock, lock), (nbrd, brd))))
ck('T16 补订段含 8/10 与新 MASTER 前 8 位',
   '8/10' in ADD_COMMON and 'e6762221' in ADD_COMMON and 'V570' in ADD_COMMON)

if fails:
    print('★ fail-closed：%d 条未过，不写盘' % len(fails)); sys.exit(1)
print('== 写盘 ==')
for path, newtxt in ((RC, nrc), (LED, nled), (LOCK, nlock), (BRD, nbrd)):
    oldraw = open(path, 'rb').read(); o = hashlib.sha256(oldraw).hexdigest()
    bak = os.path.join(BL, '%s.before_r187p_%s.bak' % (os.path.basename(path), stamp))
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
