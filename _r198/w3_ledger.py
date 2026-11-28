#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R198 台账 V581 -> V582：只改 F55（追加本轮实测与 limitations），其余 56 行逐字节不动。
fail-closed：任一回读/不变量断言失败即不写盘。
"""
import io, os, sys, hashlib, time
ROOT = '/home/t628/projects/ra2-campaign-forge'
T = os.path.join(ROOT, 'lead/next_re_20261117_r14')
BL = os.path.join(T, 'R17_LEAD_BASELINE')
SRC = os.path.join(T, 'R17_R131_FACTINDEX_V581', 'FACT_INDEX.tsv')
DSTD = os.path.join(T, 'R17_R131_FACTINDEX_V582')
DST = os.path.join(DSTD, 'FACT_INDEX.tsv')
fails = []; n = 0
def ck(nm, c, d=''):
    global n; n += 1
    if not c: fails.append(nm)
    print(('PASS ' if c else 'FAIL ') + nm + ((' | ' + str(d)) if d != '' else ''))
def sha(b): return hashlib.sha256(b).hexdigest()

raw = open(SRC, 'rb').read()
ck('P0a V581 字节 201352 / sha 140b1e5e / CR=0',
   len(raw) == 201352 and sha(raw).startswith('140b1e5e') and raw.count(b'\r') == 0,
   (len(raw), sha(raw)[:16], raw.count(b'\r')))
txt = raw.decode('utf-8')
lines = txt.split('\n')
ck('P0b 58 行（1 表头 + 56 数据 + 1 尾空）', len(lines) == 58, len(lines))
hdr = lines[0]
body = lines[1:57]
ck('P0c 每行 5 列', all(len(r.split('\t')) == 5 for r in body),
   [i for i, r in enumerate(body) if len(r.split('\t')) != 5])
ck('P0d fact_id F01..F56 连续', [r.split('\t')[0] for r in body] == ['F%02d' % i for i in range(1, 57)])

i55 = [i for i, r in enumerate(body) if r.startswith('F55\t')][0]
c55 = body[i55].split('\t')
old_stmt, old_lim, old_evid = c55[1], c55[4], c55[3]
ck('P0e F55 旧长度 stmt 27509 / lim 19650 / evid 892',
   (len(old_stmt.encode()), len(old_lim.encode()), len(old_evid.encode())) == (27509, 19650, 892),
   (len(old_stmt.encode()), len(old_lim.encode()), len(old_evid.encode())))

ADD_STMT = (
'（**V582 追加 · R198 最长虚表与槽位唯一性**）'
'①**0x7F5C70 = .?AVUnitClass@@ 主表 344 槽，344 个目标地址两两不同**：不同实现 344、出现 >=2 次的实现 0、'
'连续相同实现的 run 数 344 且每 run 长 1。体形态（400 B 窗口到首个 ret）：`ret 立即数` 140 / 裸 `ret` 170 / '
'窗口内无 ret 34；窗口放宽到 4096 B 后只剩 1 个仍无 ret（`0x73B470`，1244 条 / `sub esp,0x1b4` / `ret 0x20`）。'
'纯桩（体内等价 `xor eax,eax; ret`）8 个；放宽到裸 `c3 90 90 90` 再得 9 个，合计 16 个（与执行员 #489 逐地址一致）。'
'②**一条被推翻的隐含前提**：不能把「344 槽两两不同」当长表通例。按槽数分档的 uniq == nslot 比例是 '
'`1..7` **960/964 = 0.9959**、`8..63` **205/229 = 0.8952**、`64..127` **12/13 = 0.9231**、'
'`>=128` **4/8 = 0.5000**（0x7E8C94 341→339、0x7F4960 309→305、0x7F0508 161→159、0x7EDCC0 157→154 各有重复）。'
'⇒ 0x7F5C70 是长表里最干净的一张，不是长表通例（由审计 #491 指出、主会话 m15 逐表复算成立）。'
'反控：判据改「目标体前 16 字节互异」⇒ 344 → **287**（−57 / −16.6%），掉幅全来自常量桩成片堆叠'
'（`mov eax,0x1C2; ret` 14 个不同入口、`ret` 6、`xor al,al;ret` 8、`xor eax,eax;ret` 7、`ret 4` 6）⇒ '
'字节前缀去重系统性低报，按地址判 344 才对。'
'③**18 个 (槽号, 默认实现) 在全 14,044 个槽位上槽位唯一**：14 个不同实现地址每个只出现在它那一个槽号'
'（槽0 0x410260/75 张、槽1 0x410300/74、槽2 0x410310/74、槽4 0x410450/77、槽5 0x5F5E80/3、槽7 0x4103E0/61、'
'槽8 0x4105A0/**1**、槽9 0x410470/72、槽10 0x410480/35、槽13 0x5F6250/8、槽14 0x410490/72、槽15 0x4104A0/72、'
'槽16 0x4104B0/59、槽17 0x410440/57）。**唯一例外是纯桩 0x4C9150**（`33 C0 C3`），它出现在 **33 个不同槽号**上、'
'覆盖 39 张表 205 个槽位（槽3 22 张、槽1/11/12 各 13、槽4/6 各 11、…、槽238/292 各 1）⇒ '
'纯桩地址**不携带槽位信息**、不能当槽号指纹；非纯桩实现地址是稳定不变量。'
'反控：收窄到 L 的 78 张表结论不变（0x4C9150 收窄到 9 个槽号）；主表/子表拆分后也不变；'
'0x7F5C70 自身命中 6 个（槽 0/1/2/4/7/16），与期望槽号逐一相符。'
'④**CRC 状态对象 +0 初值来源的上溯终止分类（覆盖 331/331 = 100%）**：按「同函数内 ecx 最近一次整字赋值」'
'逐跳上溯最多 6 跳，得 **NODEF 122（36.9%）/ 结构体字段 107（32.3%）/ 全局对象字段 51（15.4%）/ '
'全局绝对地址寄存器 33（10.0%）/ 本地栈 18（5.4%）**。'
'**全局绝对地址类（33 条）的初值来源已取得**：形态 `mov ecx,0xA8B238`；0xA8B238 落在 .data 的 vsize 内 / '
'rawsize 外（`P.where()` = virt-only、`P.r2o()` = None）⇒ **BSS，文件内没有任何初值字节，映像加载即全 0**，'
'不需要任何指令写入；该地址在 .text 有 **219** 处 `mov ecx,imm32` 引用（无一处后 64 B 内直接调 CRC 族），'
'另有 **5** 处绝对寻址写（`0x5EF73A` / `0x67E4E8` 写 +0，`0x789E77` 写 +0xC，`0x76EDBA` 写 +0x8）。'
'对照 0x817BD0（真 .data，文件初值 `53475259534d4b31…`）有 **0** 处绝对寻址写。'
'⑤**本地栈 18 站点的调用者准备（18/18）**：每个站点的宿主函数，其调用者在调用点前 24 B 内 **18/18** 都有 '
'`lea ecx,[esp+K]`（K ∈ {0x1C, 0x4C, 0xA0, 0x0C, 0x6C}），且 lea 之后紧邻的 call 目标**就是该宿主**'
'（0x41F6EE→0x5117D0 / 0x772925→0x644630 / 0x428729→0x645430 / 0x672795→0x6F1920 / 0x5A2BE9→0x71DD80）。'
'其中 0x645583 一路给出**四槽全写**字节证据：`lea ecx,[esp+0xa0]`(0x428729) → '
'`mov dword ptr [esp+0xa0],ecx`(+0) / `[esp+0xa4],0`(+4) / `[esp+0xa8],0`(+8) / `[esp+0xac],eax`(+0xC)。'
'⑥**0x410410 的 27 个调用点落在 27 个不同宿主**（一对一、每宿主 1 次）；其中只有 **2 个**是虚表实现且'
'**恰好占槽 13**：`0x410BE0`（.?AVAbstractTypeClass@@ / .?AVObjectTypeClass@@）、'
'`0x5F6250`（.?AVBulletClass@@ / .?AVIsometricTileClass@@ / .?AVObjectClass@@ / .?AVOverlayClass@@ 等 8 张）；'
'其余 25 个不在任何虚表内。'
)

ADD_LIM = (
'（l）**V582 追加 · R198 未取得与口径限定**：① 18 个「本地栈」站点里**只有 0x645583 一路**拿到了四槽写入的字节，'
'其余 17 个只证到「调用者准备了栈缓冲」、未逐个验证四槽是否都被初始化；② NODEF 122 条的 +0 来源仍未取得'
'（同函数内找不到 ecx 的整字赋值）；③ 结构体字段 107 + 全局对象字段 51 共 158 条的宿主结构体语义名未取得；'
'④ 18+6 个虚表实现的**游戏语义名**仍未取得；⑤ 本节第一条的「344 槽两两不同」**不是**长表通例'
'（`>=128` 档只有 4/8 张 uniq == nslot），引用时必须带这个限定；⑥ 0x7F5C70 的纯桩计数有**两个口径**并存：'
'按语义「xor eax,eax; ret」得 8、放宽到裸 `c3 90 90 90` 得 16（差集 9，其中 0x4104B0 同属两类），'
'两者都与执行员 #489 的 16 相容，引用时须注明口径。'
'**R198 自错（无一条进入结论）**：m1 把裸 `ret` 排除在桩外致「8 vs 16」分歧；m1 有两条断言**预期值写错**'
'（`Q2d 目标地址单调递增`、`R3a 前 16 字节去重 344`，实测分别只有 196/343 对递增与 287 个前缀）；'
'm9 第一版 `find4` 为 O(n²)、跑 8 分钟被 kill，改滑窗后完成；m10 把 `mov ecx,edi` 当终点不跟 edi ⇒ 假 265 条 OTHER；'
'm12 用 `CALLERS[host][0]` 取单个调用者跨层 ⇒ **18 条假 STACK**，由 m16 复算证明这 18 个 lea 后紧邻 call 目标'
'**全不是** CRC 族（0/18）后否掉，改按「宿主 → 全部调用者前 24 B」重测才 18/18 成立 ⇒ '
'「本地栈 18」这一行的证据链是**修补后口径**、不是初版口径。'
'**R198 跨家族**：执行员 #489（hy4）20/20 断言 PASS，Q1/Q2/Q5/Q6 与主会话逐值一致、16 个纯桩地址逐地址一致，'
'其体形态四分口径（122/151/59+12）与主会话三分口径（140/170/34）**不可比**、两者都保留；'
'执行员 #490（hy4）卡在 `md_lite.disasm` 解包错误（`TypeError: cannot unpack non-iterable CsInsn`），'
'**未交付结论**（`_r198/exec_b/probe_stdout.txt` 0 B）；审计员 #491（deepseek，9 回合 / 1.83 分 / 预算 8 分）'
'三条主张（A1 三数、A2 六项、A3 十五个地址的槽号集合）**全部复算一致**，并额外指出两处主会话口径问题且均被采纳：'
'(a) `>=128` 档只有 4/8 张 uniq == nslot，故「两两不同」不能当长表通例；(b) 前 16 字节去重是 287 不是 344、'
'掉幅来自常量桩成片堆叠；其对「18 对清单不来自任何单张表」的观察（最接近的 0x7E1F50 16/18、0x7EF060 15/18）'
'主会话复算成立。'
)

ADD_EVID = (';_r198/m1_vtslot.py;_r198/m1_vtslot.json;_r198/m2_vtslot2.py;_r198/m3_slotuniq.py;'
            '_r198/m4_locality.py;_r198/m5_crctree.py;_r198/m6_hosts.py;_r198/m7_recon.py;'
            '_r198/m8_crcinit2.py;_r198/m9b_alloc.py;_r198/m10_origin.py;_r198/m11_origin2.py;'
            '_r198/m12_final.py;_r198/m13_bss.py;_r198/m14_bss2.py;_r198/m15_final_verify.py;'
            '_r198/m16_selfcheck.py;_r198/m17_stack2.py;_r198/exec_a/vtslot.txt')

new_stmt = old_stmt + ADD_STMT
new_lim = old_lim + ADD_LIM
new_evid = old_evid + ADD_EVID
c55n = list(c55); c55n[1] = new_stmt; c55n[4] = new_lim; c55n[3] = new_evid
body[i55] = '\t'.join(c55n)
newtxt = '\n'.join([hdr] + body + [''])
nt = newtxt.encode('utf-8')
ck('P1 新 CR == 0（全 LF）', nt.count(b'\r') == 0, nt.count(b'\r'))
ck('P2 行数仍 58', nt.decode('utf-8').split('\n').__len__() == 58, nt.decode('utf-8').split('\n').__len__())
ck('P3 每行 5 列', all(len(r.split('\t')) == 5 for r in nt.decode('utf-8').split('\n')[1:57]))
ck('P4 其余 55 行逐字节未动',
   [r for r in nt.decode('utf-8').split('\n')[1:57] if not r.startswith('F55\t')]
   == [r for r in body if not r.startswith('F55\t')])
ck('P5 新长度 stmt/lim/evid 均大于旧', (len(new_stmt.encode()) > len(old_stmt.encode())
   and len(new_lim.encode()) > len(old_lim.encode()) and len(new_evid.encode()) > len(old_evid.encode())),
   (len(old_stmt.encode()), len(new_stmt.encode()), len(old_lim.encode()), len(new_lim.encode()),
    len(old_evid.encode()), len(new_evid.encode())))
ck('P6 grade 列未动', c55n[2] == c55[2], (c55[2], c55n[2]))
ck('P7 反控：stmt 少 1 字节则 sha 变', sha((new_stmt[:-1] + '\t'.join([c55n[0]] + [new_stmt[:-1]] + c55n[2:])).encode()) != sha(nt))
if fails:
    print('ABORT before ledger write: %s' % fails); sys.exit(1)
os.makedirs(DSTD, exist_ok=True)
stamp = time.strftime('%Y%m%d_%H%M%S')
bak = os.path.join(BL, 'FACT_INDEX_V582.before_r198_%s.bak' % stamp)
fd = os.open(bak, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o644)
with os.fdopen(fd, 'wb') as f: f.write(nt)
ck('W1 备份 sha 一致', sha(open(bak, 'rb').read()) == sha(nt))
open(DST, 'wb').write(nt)
ck('W2 回读一致', sha(open(DST, 'rb').read()) == sha(nt))
NEWSHA = sha(nt)
print('V582 写入：%d B / sha %s' % (len(nt), NEWSHA[:16]))
print('F55 stmt %d -> %d / lim %d -> %d / evid %d -> %d'
      % (len(old_stmt.encode()), len(new_stmt.encode()), len(old_lim.encode()), len(new_lim.encode()),
         len(old_evid.encode()), len(new_evid.encode())))
open('/tmp/r198_v582.txt', 'w').write('%d %s %d %d %d' % (len(nt), NEWSHA,
    len(new_stmt.encode()), len(new_lim.encode()), len(new_evid.encode())))
print('FAILS=%d' % len(fails))
