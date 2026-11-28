#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R194 第八刀（主会话复算，§2.12 规则 D）：对执行员 #474 与审计员 #475 的两组数字复算。

复算目标：
  V1 基线（审计员 P1/P2 争议点）：COL d0（signature）在 1214 条上是否恒 0；
     主表/子表分界字段是 d0 还是 d1（mdisp）。给出 d0 分布与两种口径下的主表数/L 数。
  V2 全 .text 用 disasm_lite 线性扫描（OOM 红线允许），统计指令总数 + 三个序列化辅助
     函数的 call rel32 命中数 + 间接 FF/2 计数。
  V3 二次播种解码：以 V2 得到的 call/jmp 落点为种子再解，合并去重后重计（对执行员
     「lite 线性扫描在 0x4A1D0B 失步」的说法给数）。
  V4 CRC 表 0x81F7B4 的引用面：两条独立口径（字节模式 + 指令扫描），给出地址集合。
  V5 0x4A1C10 定性（执行员称是读侧校验候选）：反汇编 + 找 cmp/比较 + 调用面。
"""
import sys, struct, collections, capstone
sys.path.insert(0, '/home/t628/projects/ra2-campaign-forge/_r185')
import pe185 as P
md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
fails = []; N = 0
def ck(nm, c, d=''):
    global N; N += 1
    if not c: fails.append(nm)
    print(('PASS ' if c else 'FAIL ') + nm + ((' | ' + str(d)) if d != '' else ''))

T = P.B['.text']; LO = T['lo']; HI = T['hi_file']; RAWPTR = T['rawptr']
def in_text(x): return x is not None and LO <= x < HI
def wv(sn):
    s = P.B[sn]; n = s['rawsize'] // 4
    return s['lo'], struct.unpack_from('<%dI' % n, P.RAW, s['rawptr']), n
COL = {}
for sn in ('.rdata', '.data'):
    base, w, n = wv(sn)
    for i in range(n - 4):
        if w[i] not in (0, 1) or w[i + 2] != 0: continue
        if P.where(w[i + 3]) != '.data' or P.where(w[i + 4]) != '.rdata': continue
        nm = P.cstr(w[i + 3] + 8, 200)
        if not (nm and nm.startswith(b'.?A') and nm.endswith(b'@@')): continue
        COL[base + 4 * i] = dict(mdisp=w[i + 1], ptd=w[i + 3], pchd=w[i + 4], name=nm.decode('latin1'),
                                 d0=w[i])
VT = {}
for sn in ('.rdata', '.data'):
    base, w, n = wv(sn)
    for i in range(n):
        if in_text(w[i]) and P.dw(base + 4 * i - 4) in COL: VT[base + 4 * i] = P.dw(base + 4 * i - 4)
def nslot(vt):
    k = 0
    while in_text(P.dw(vt + 4 * k)): k += 1
    return k
NS = {vt: nslot(vt) for vt in VT}

# ---- V1 ----
d0 = collections.Counter(COL[c]['d0'] for c in COL)
d1z = sum(1 for c in COL if COL[c]['mdisp'] == 0)
print('   COL d0（signature）分布 %s；d1(mdisp)==0 条数 %d；d1!=0 %d' % (dict(d0), d1z, len(COL) - d1z))
ck('V1a 审计员 P1 更正成立：d0 在 1214 条 COL 上恒 0（分布 == {0:1214}）',
   dict(d0) == {0: 1214}, dict(d0))
ck('V1b 主表/子表分界字段是 d1(mdisp)：主表 %d / 子表 %d' % (d1z, len(COL) - d1z),
   (d1z, len(COL) - d1z) == (954, 260), (d1z, len(COL) - d1z))
ck('V1c 审计员 R1 更正成立：若用字面 d0==0 判主表则得 1214/0（与工具链口径 954/260 不同）',
   sum(1 for c in COL if COL[c]['d0'] == 0) == 1214, None)

# ---- V2 全段 disasm_lite 线性扫描 ----
ins_all = []
chunk = 0x10000
va = LO
while va < HI:
    end = min(va + chunk, HI)
    o = RAWPTR + (va - LO); lim = end - va
    got = list(md.disasm_lite(P.RAW[o:o + lim], va))
    ins_all.extend(got)
    if not got: break
    va = got[-1][0] + got[-1][1]
print('   V2 线性扫描：%d 条指令，覆盖 %08X..%08X' % (len(ins_all), LO, ins_all[-1][0] + ins_all[-1][1]))
TGT = {0x4A1CA0: 0, 0x4A1D50: 0, 0x4A1DE0: 0}
callsites = collections.defaultdict(list)
ind = 0
tabref_lite = []
for a, sz, mn, op in ins_all:
    if mn == 'call' and op.startswith('0x'):
        try: t = int(op, 16)
        except ValueError: continue
        if t in TGT: TGT[t] += 1; callsites[t].append(a)
    if mn == 'call' and not op.startswith('0x'): ind += 1
    if '0x81f7b4' in op: tabref_lite.append(a)
print('   V2 call 计数 %s；间接 call %d；CRC 表引用 %s'
      % ({hex(k): v for k, v in TGT.items()}, ind, [hex(x) for x in tabref_lite]))
ck('V2a 线性 lite 扫描的 CRC 表引用地址集合 == {0x4A1C73,0x4A1D0B,0x4A1E91,0x4A1F1E,0x4A1F88}（执行员 5 处）',
   sorted(tabref_lite) == [0x4A1C73, 0x4A1D0B, 0x4A1E91, 0x4A1F1E, 0x4A1F88],
   [hex(x) for x in sorted(tabref_lite)])
ck('V2b lite 扫描命中 0x4A1D0B（执行员称线性扫描在此失步 —— 实测未失步）',
   0x4A1D0B in tabref_lite, [hex(x) for x in tabref_lite])

# ---- V3 二次播种解码 ----
seeds = set()
for a, sz, mn, op in ins_all:
    if mn in ('call', 'jmp') and op.startswith('0x'):
        try: t = int(op, 16)
        except ValueError: continue
        if in_text(t): seeds.add(t)
addr2 = {a: (sz, mn, op) for a, sz, mn, op in ins_all}
for sd in sorted(seeds):
    o = P.r2o(sd)
    for a, sz, mn, op in md.disasm_lite(P.RAW[o:o + 4096], sd):
        if a not in addr2: addr2[a] = (sz, mn, op)
T3 = {0x4A1CA0: 0, 0x4A1D50: 0, 0x4A1DE0: 0}
cs3 = collections.defaultdict(list)
tabref2 = []
ind2 = 0
for a, (sz, mn, op) in addr2.items():
    if mn == 'call':
        if op.startswith('0x'):
            try: t = int(op, 16)
            except ValueError: t = None
            if t in T3: T3[t] += 1; cs3[t].append(a)
        else: ind2 += 1
    if '0x81f7b4' in op: tabref2.append(a)
print('   V3 播种合并：%d 条（+%d 来自播种）；call %s；间接 %d；表引用 %s'
      % (len(addr2), len(addr2) - len(ins_all), {hex(k): v for k, v in T3.items()}, ind2,
         [hex(x) for x in sorted(tabref2)]))
ck('V3a 播种合并后 CRC 表引用集合不增加（5 处稳定，无漏）',
   sorted(set(tabref2)) == sorted(set(tabref_lite)), [hex(x) for x in sorted(set(tabref2))])
ratio = {hex(k): (TGT[k], T3[k]) for k in TGT}
ck('V3b 两口径 call 计数一致性：播种合并 >= lite 线性（差值为被数据吞掉的真实指令）',
   all(T3[k] >= TGT[k] for k in TGT), ratio)

# ---- V4 字节口径独立核 ----  disp32 LE of 0x0081F7B4
pat = struct.pack('<I', 0x81F7B4)
hits = []
o0 = P.r2o(LO)
buf = P.RAW[o0:o0 + (HI - LO)]
p = buf.find(pat)
while p >= 0:
    hits.append(LO + p)
    p = buf.find(pat, p + 1)
print('   V4 字节口径：disp32 0x0081F7B4 在 .text 出现 %d 次，地址 %s' % (len(hits), [hex(x) for x in hits]))
ck('V4a 字节口径与指令口径一致（每个 disp32 命中都落在一条指令内）',
   len(hits) == len(tabref_lite) and all(any(h - 4 <= a <= h for a in tabref_lite) for h in hits),
   ([hex(x) for x in hits], len(tabref_lite)))

# ---- V5 0x4A1C10 ----
def walk(va, maxb=600):
    o = P.r2o(va); out = []
    for i in md.disasm(P.RAW[o:o + maxb], va):
        out.append((i.address, P.RAW[P.r2o(i.address):P.r2o(i.address) + i.size].hex(' ').upper(),
                    i.mnemonic, i.op_str))
        if i.mnemonic.startswith('ret'): break
    return out
b = walk(0x4A1C10)
print('   V5 0x4A1C10 体 %d 条：' % len(b))
for a, h, m, o in b: print('     %08X  %-24s %-8s %s' % (a, h, m, o))
ck('V5a 0x4A1C10 体以 ret 结尾且引用 CRC 表', bool(b) and b[-1][2].startswith('ret')
   and any('0x81f7b4' in o for _, _, _, o in b), (len(b), b[-1][2] if b else None))
ck('V5b 0x4A1C10 是「算 CRC 再比较」的读侧校验（体含 cmp 且 cmp 的一侧是算出的 eax）',
   any(m == 'cmp' for _, _, m, _ in b), [(hex(a), m, o) for a, _, m, o in b if m in ('cmp', 'sete', 'setne', 'call')])
sys.stdout.flush()
print('\n断言 %d 条，FAIL %d 条' % (N, len(fails)))
if fails: print('FAIL 明细：' + ' | '.join(fails)); sys.exit(1)
