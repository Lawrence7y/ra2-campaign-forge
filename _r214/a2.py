# -*- coding: utf-8 -*-
"""R214-AUDIT(ds) a2: 补测——slot18/19 落点集重叠、0x723ea0 边界性质、mono 索引分母分布、
m1 断言是否为恒真、R213 A/F 模板口径来源。"""
import sys, struct, collections
ROOT = '/home/t628/projects/ra2-campaign-forge'
sys.path.insert(0, ROOT + '/_r185')
import pe185 as P
from capstone import Cs, CS_ARCH_X86, CS_MODE_32
RAW = P.RAW
SECS = [(s['lo'], s['hi_file'], s['name']) for s in P.SECS]
VIRT = [(s['lo'], s['hi_virt'], s['name']) for s in P.SECS]


def where(va):
    if va is None:
        return 'None'
    for lo, hi, nm in SECS:
        if lo <= va < hi:
            return nm
    for lo, hi, nm in VIRT:
        if lo <= va < hi:
            return 'virt-only'
    return 'other'


def dw(va):
    o = P.r2o(va)
    return None if o is None else struct.unpack_from('<I', RAW, o)[0]


def s32(v):
    return struct.unpack('<i', struct.pack('<I', v & 0xffffffff))[0]


def hx(v):
    return 'None' if v is None else '0x%08x' % v


COL = {}
for sn in ('.rdata', '.data'):
    s = P.B[sn]
    n = s['rawsize'] // 4
    w = struct.unpack_from('<%dI' % n, RAW, s['rawptr'])
    for k in range(n - 4):
        if w[k] not in (0, 1, 2) or w[k + 2] != 0:
            continue
        if where(w[k + 3]) != '.data' or where(w[k + 4]) != '.rdata':
            continue
        nb = P.cstr(w[k + 3] + 8, 400)
        if not (nb and nb.startswith(b'.?A') and nb.endswith(b'@@')):
            continue
        COL[s['lo'] + 4 * k] = dict(mdisp=s32(w[k + 1]), cls=nb.decode('latin1')[1:])
pred = collections.defaultdict(list)
for sn in ('.rdata', '.data'):
    s = P.B[sn]
    n = s['rawsize'] // 4
    w = struct.unpack_from('<%dI' % n, RAW, s['rawptr'])
    for k in range(n - 1):
        if w[k] in COL and where(w[k + 1]) == '.text':
            pred[w[k]].append(s['lo'] + 4 * k)
views = []
for c, v in COL.items():
    if len(pred[c]) != 1:
        continue
    vt = pred[c][0] + 4
    sl = []
    a = vt
    while True:
        d = dw(a)
        if d is None or where(d) != '.text' or len(sl) >= 4096:
            break
        sl.append(d)
        a += 4
    views.append(dict(C=c, base=vt, mdisp=v['mdisp'], cls=v['cls'], s=sl))
main = [v for v in views if v['mdisp'] == 0]

print('=== 1. slot18 / slot19 落点集重叠（替代“三者不等”的有效非平凡性判据）===')
S = {}
for i in (17, 18, 19):
    S[i] = [v['s'][i] for v in views if len(v['s']) > i]
for i in (17, 18, 19):
    print('  slot%-2d n=%3d distinct=%2d set=%s' % (i, len(S[i]), len(set(S[i])),
          [hx(x) for x in sorted(set(S[i]))]))
for a, b in ((17, 18), (18, 19), (17, 19)):
    print('  slot%d∩slot%d = %d |%s|  仅%d独有=%d' %
          (a, b, len(set(S[a]) & set(S[b])), [hx(x) for x in sorted(set(S[a]) & set(S[b]))],
           a, len(set(S[a]) - set(S[b]))))
print('  逐视图同址(同一张视图 slot18==slot19) 的视图数=%d ; slot17==slot18=%d' %
      (sum(1 for v in views if len(v['s']) > 19 and v['s'][18] == v['s'][19]),
       sum(1 for v in views if len(v['s']) > 18 and v['s'][17] == v['s'][18])))
c18 = collections.Counter(S[18]); c19 = collections.Counter(S[19])
print('  slot18 top6=%s' % [(hx(a), n) for a, n in c18.most_common(6)])
print('  slot19 top6=%s' % [(hx(a), n) for a, n in c19.most_common(6)])

print('\n=== 2. 0x723ea0 / 0x723eb0 的目标边界性质 ===')
md = Cs(CS_ARCH_X86, CS_MODE_32)


def lin(a, n=10):
    o = P.r2o(a)
    out = []
    for i in md.disasm(RAW[o:o + 48], a):
        out.append((i.address, i.mnemonic + ' ' + i.op_str))
        if len(out) >= n:
            break
    return out


for a0 in (0x723e80, 0x723e90, 0x723ea0, 0x723eb0):
    print('  linear @%s: %s' % (hx(a0), ['%s:%s' % (hx(x), s) for x, s in lin(a0, 8)]))
# 谁指向这个邻域
T = P.B['.text']
blob = RAW[T['rawptr']:T['rawptr'] + T['rawsize']]
hits = collections.Counter()
for op in (0xe8, 0xe9):
    ob = bytes([op]); pos = 0
    while True:
        i = blob.find(ob, pos)
        if i < 0 or i + 5 > len(blob):
            break
        pos = i + 1
        rel = struct.unpack_from('<i', blob, i + 1)[0]
        a = T['lo'] + i
        tg = a + 5 + rel
        if 0x723e00 <= tg < 0x723f40:
            hits[tg] += 1
print('  .text 内 e8/e9 直接指向 [0x723e00,0x723f40) 的落点分布=%s' %
      [(hx(a), n) for a, n in sorted(hits.items())])
# 0x723ea0 前是否有 ret/int3/jmp（上限边界）
pre = P.r2o(0x723ea0) - 16
print('  0x723ea0 前 16 字节=%s' % RAW[pre:pre + 16].hex())
print('  0x723ea0 本身 16 字节=%s' % RAW[P.r2o(0x723ea0):P.r2o(0x723ea0) + 16].hex())

print('\n=== 3. A4 mono 索引的分母分布 ===')
IDX = collections.defaultdict(collections.Counter)
for v in main:
    for i, d in enumerate(v['s']):
        IDX[i][d] += 1
den = {i: sum(IDX[i].values()) for i in IDX}
mono = [i for i in IDX if len(IDX[i]) == 1]
buckets = collections.Counter()
for i in mono:
    d = den[i]
    b = '1' if d == 1 else '2-4' if d <= 4 else '5-9' if d <= 9 else '10-99' if d <= 99 else '100-953' if d <= 953 else '954'
    buckets[b] += 1
print('  mono=%d 分母分桶=%s' % (len(mono), dict(buckets)))
print('  mono 中分母=1（仅一类有该槽）的 idx 数=%d 明细=%s' %
      (sum(1 for i in mono if den[i] == 1),
       [(i, hx(list(IDX[i])[0])) for i in mono if den[i] == 1][:12]))
print('  mono 中分母>=100 的：（idx,分母,值）=%s' %
      [(i, den[i], hx(list(IDX[i])[0])) for i in mono if den[i] >= 100])
print('  全部 954 张主视图都有的索引=%s' % [i for i in IDX if den[i] == 954])

print('\n=== 4. m1 断言恒真检查（源码层）===')
import re
src = open(ROOT + '/_r214/m1.py', encoding='utf-8').read().splitlines()
for ln, line in enumerate(src, 1):
    if 'ck(' in line:
        taut = re.search(r'ck\([^,]+,\s*(True|AMB\s*==\s*0\s+or\s+True)\s*[,)]', line)
        print('  L%-3d %s   <=恒真=%s' % (ln, line.strip()[:120], bool(taut)))
print('  参考 m0/ex1/ex2 恒真检查（or True / 无条件字面量）:')
for f in ('m0.py', 'ex1.py', 'ex2.py'):
    n = 0
    for line in open(ROOT + '/_r214/' + f, encoding='utf-8').read().splitlines():
        if 'ck(' in line and re.search(r'ck\([^,]+,\s*(True|True\s*[,)]|.*\bor\s+True\b)', line):
            n += 1
    print('    %s 疑似恒真=%d' % (f, n))

print('\n=== 5. R213 A/F 槽位模板口径来源检索 ===')
import subprocess
for pat in ('FFF", "AAA', "'F'", '"F"', 'atmpl', 'AAA'):
    r = subprocess.run(['rg', '-n', '--no-heading', '-l', pat, ROOT + '/_r213', ROOT + '/_r214'],
                       capture_output=True, text=True)
    print('  rg -l %-12r -> %s' % (pat, r.stdout.strip().splitlines()))
