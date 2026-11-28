#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R200 主会话第十一刀：把「小位移装表 697 条」与「槽 0 的 538 条」做同一判据的对照，并给出 F55 可用的新事实候选。

U1 对照表：两类装表 store 的五维（基址寄存器 / 位移值 / imm 的 mdisp / imm 类名 / 是否同类）
U2 子表装填面：697 条里有多少是「同一宿主里既有主表装填又有 4/8 位移子表装填」
V1 槽 0 的 538 条里，位移分布只有 {0:532, 0x10:1, 0x34:1, 0x14:1, 0x18:1, 0x3f550:1, 0x3f338:1}
    —— 与 697 条的 {4:345, 8:341, 0:11} 完全不相交。这说明两者是**两类不同的构造指令序列**。
V2 对 11 条 disp8 命中但 imm 的 mdisp==0 的样本逐条给（宿主、imm 类名、disp8、宿主内是否另有子表装填）。
反控：
 R1 把 U1 的基数限定为「宿主在 954 主表对应的构造函数集合内」看比例是否变化。
"""
import sys, struct, collections, json, bisect, re
sys.path.insert(0, '/home/t628/projects/ra2-campaign-forge/_r185')
import pe185 as P
import capstone
md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
fails = []; N = 0
def ck(nm, c, d=''):
    global N; N += 1
    if not c: fails.append(nm)
    print(('PASS ' if c else 'FAIL ') + nm + ((' | ' + str(d)) if d != '' else ''))

def s32(v): return struct.unpack('<i', struct.pack('<I', v))[0]
def wv(sn):
    s = P.B[sn]; n = s['rawsize'] // 4
    return s['lo'], struct.unpack_from('<%dI' % n, P.RAW, s['rawptr']), n
T = P.B['.text']; LO = T['lo']; HI = T['hi_file']; RAW = P.RAW
def in_text(x): return x is not None and LO <= x < HI
COL = {}
for sn in ('.rdata', '.data'):
    base, w, n = wv(sn)
    for i in range(n - 4):
        if w[i] not in (0, 1, 2) or w[i + 2] != 0: continue
        if P.where(w[i + 3]) != '.data' or P.where(w[i + 4]) != '.rdata': continue
        nm = P.cstr(w[i + 3] + 8, 400)
        if not (nm and nm.startswith(b'.?A') and nm.endswith(b'@@')): continue
        COL[base + 4 * i] = dict(mdisp=s32(w[i + 1]), ptd=w[i + 3], pchd=w[i + 4], name=nm.decode('latin1'))
VT = {}
for sn in ('.rdata', '.data'):
    base, w, n = wv(sn)
    for i in range(n):
        if in_text(w[i]) and P.dw(base + 4 * i - 4) in COL: VT[base + 4 * i] = P.dw(base + 4 * i - 4)
NS = {}
def nslot(vt):
    if vt in NS: return NS[vt]
    k = 0
    while True:
        if not in_text(P.dw(vt + 4 * k)): break
        k += 1
    NS[vt] = k; return k
MD = {vt: COL[VT[vt]]['mdisp'] for vt in VT}
CLS = {vt: COL[VT[vt]]['name'] for vt in VT}

REGNAME = ['eax', 'ecx', 'edx', 'ebx', 'esp', 'ebp', 'esi', 'edi']
recs = []
pos = T['rawptr']; end = T['rawptr'] + T['rawsize']
while pos < end - 6:
    if RAW[pos] != 0xC7: pos += 1; continue
    modrm = RAW[pos + 1]; mod = modrm >> 6; reg = (modrm >> 3) & 7; rm = modrm & 7
    if reg != 0 or rm == 4 or (rm == 5 and mod == 0): pos += 1; continue
    va = LO + (pos - T['rawptr'])
    if mod == 1:
        disp = struct.unpack_from('<b', RAW, pos + 2)[0]
        imm = struct.unpack_from('<I', RAW, pos + 3)[0]
        recs.append((va, REGNAME[rm], disp, imm)); pos += 7
    elif mod == 2:
        disp = struct.unpack_from('<i', RAW, pos + 2)[0]
        imm = struct.unpack_from('<I', RAW, pos + 6)[0]
        recs.append((va, REGNAME[rm], disp, imm)); pos += 10
    else:
        pos += 1
sub = [r for r in recs if 1 <= r[2] <= 9 and r[3] in VT]
ck('U0a 小位移装表（imm 在 VT）697 条', len(sub) == 697, len(sub))
# 按宿主分组
BUF = RAW[T['rawptr']:T['rawptr'] + (HI - LO)]
CALLAT = []; p2 = 0
while p2 < len(BUF):
    got = False
    for off, sz, mn, op in md.disasm_lite(BUF[p2:p2 + 65536], LO + p2):
        got = True
        if mn == 'call' and op.startswith('0x'):
            t = int(op, 16)
            if in_text(t): CALLAT.append((off, t))
        p2 += sz
    if not got: p2 += 1
SORT = sorted(set(t for _, t in CALLAT))
def host_of(c):
    i = bisect.bisect_left(SORT, c) - 1
    return SORT[i] if i >= 0 else None
def next_entry(c):
    i = bisect.bisect_right(SORT, c)
    return SORT[i] if i < len(SORT) else HI
byhost = collections.defaultdict(list)
for r in sub: byhost[host_of(r[0])].append(r)
both = 0; only_sub = 0; only_main = 0
for h, rs in byhost.items():
    if h is None: continue
    hi = min(next_entry(h), h + 4096)
    o = P.r2o(h)
    if o is None: continue
    has_main = has_sub = False
    for i in md.disasm(RAW[o:o + (hi - h)], h):
        if i.mnemonic == 'mov' and i.op_str.startswith('dword ptr [') and ', 0x' in i.op_str:
            try: iv = int(i.op_str.rsplit(', ', 1)[1], 16)
            except Exception: continue
            if iv not in VT: continue
            if MD[iv] == 0: has_main = True
            else: has_sub = True
    if has_main and has_sub: both += 1
    elif has_sub: only_sub += 1
    else: only_main += 1
print('   U2 宿主内装填结构（%d 个宿主）: 主表+子表 both=%d / 只子表=%d / 只主表=%d' % (len(byhost), both, only_sub, only_main))
ck('U2a both >= 50', both >= 50, both)

# V1 槽 0 的 538 条位移分布 vs 697 条
d = json.load(open('/home/t628/projects/ra2-campaign-forge/_r199/m1_pair.json'))
pairs = [(int(a, 16), int(b, 16)) for a, b in d['pairs']]
s0d = []
for vt_d, vt_b in pairs:
    if min(nslot(vt_d), nslot(vt_b)) < 1: continue
    if P.dw(vt_d) != P.dw(vt_b): s0d.append((vt_d, P.dw(vt_d), vt_b))
def body(va, maxb=600, maxi=300):
    o = P.r2o(va)
    if o is None: return None
    ins = []
    for i in md.disasm(RAW[o:o + maxb], va):
        ins.append((i.address, i.size, i.mnemonic, i.op_str))
        if i.mnemonic.startswith('ret'): break
        if len(ins) >= maxi: break
    return ins
SR = re.compile(r'^dword ptr \[(e[a-z]{2})(?: ([\+\-]) (0x[0-9a-f]+|\d+))?\], (0x[0-9a-f]+)$')
s0disp = collections.Counter(); s0n = 0
for vt_d, a, vt_b in s0d:
    for ad, sz, mn, op in body(a) or []:
        if mn != 'mov': continue
        m = SR.match(op)
        if not m: continue
        val = m.group(3); off = 0
        if val is not None:
            off = int(val, 16) if val.startswith('0x') else int(val)
            if m.group(2) == '-': off = -off
        s0disp[off] += 1; s0n += 1
subdisp = collections.Counter(r[2] for r in sub)
ck('V1a 槽 0 的 538 条位移分布', s0n == 538, dict(sorted(s0disp.items())))
ck('V1b 697 条位移分布', len(sub) == 697, dict(sorted(subdisp.items())))
ck('V1c 两集合位移不相交（4/8 只在 697，0x10/0x14/0x18/0x34/0x3f3xx/0x3f550 只在 538）',
   all(k not in subdisp for k in s0disp), {'s0': sorted(s0disp), 'sub': sorted(subdisp)})

# V2 11 条 disp8 命中且 mdisp==0
main11 = [r for r in sub if MD[r[3]] == 0]
print('   V2 disp8 命中但 imm 是主表的 11 条:')
for r in main11:
    h = host_of(r[0]); hi = min(next_entry(h), h + 4096) if h else None
    print('        at=%s reg=%-4s disp=%d imm=%s cls=%s mdisp=0 host=%s' %
          (hex(r[0]), r[1], r[2], hex(r[3]), CLS[r[3]], hex(h) if h else None))
ck('V2a 11 条', len(main11) == 11, len(main11))

json.dump(dict(sub=len(sub), both=both, only_sub=only_sub, only_main=only_main,
               s0disp={hex(k): v for k, v in s0disp.items()}, subdisp={str(k): v for k, v in subdisp.items()},
               main11=[(hex(r[0]), r[1], r[2], hex(r[3]), CLS[r[3]]) for r in main11],
               hosts=len(byhost), asserts=N, fails=fails),
          open('/home/t628/projects/ra2-campaign-forge/_r200/m11_subfill.json', 'w'), ensure_ascii=False, indent=1)
print('\nSUMMARY asserts=%d fails=%d %s' % (N, len(fails), fails))
