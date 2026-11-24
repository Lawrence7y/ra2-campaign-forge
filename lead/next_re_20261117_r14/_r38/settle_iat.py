# -*- coding: utf-8 -*-
"""决胜测量：把三处容易混的东西分开——
  (A) ILT(OriginalFirstThunk) 的值 = IMAGE_IMPORT_BY_NAME 的 **RVA**      → 落在哪个节
  (B) IAT(FirstThunk) 数组本身的位置 = **RVA** → 落在哪个节
  (C) IAT 槽里的内容（绑定地址）= **VA** → 落在哪个节
上一轮我把 (A) 的值当 (C) 用、还在 sec_of 里又减了一次 ImageBase，故「339 全在 .text」是错的。
"""
import struct

IMG = r'D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe'
d = open(IMG, 'rb').read()
pe = struct.unpack_from('<I', d, 0x3C)[0]
nsec, = struct.unpack_from('<H', d, pe + 6)
optsz, = struct.unpack_from('<H', d, pe + 20)
opt = pe + 24
ib, = struct.unpack_from('<I', d, opt + 28)
st = opt + optsz
secs = []
for i in range(nsec):
    o = st + i * 40
    nm = d[o:o + 8].rstrip(b'\0').decode('ascii', 'replace')
    vs, va, rs, ra = struct.unpack_from('<IIII', d, o + 8)
    secs.append((nm, va, vs, ra, rs))

def sec_of_rva(rva):
    for nm, va, vs, ra, rs in secs:
        if va <= rva < va + max(vs, rs):
            return nm
    return '?'

def sec_of_va(va):
    return sec_of_rva(va - ib)

def r2o(rva):
    for nm, va, vs, ra, rs in secs:
        if va <= rva < va + max(vs, rs):
            dd = rva - va
            return ra + dd if dd < rs else None
    return '?'

imp_rva, imp_sz = struct.unpack_from('<II', d, opt + 96 + 8)
print('ImageBase = 0x%X ; Import dir RVA = 0x%X -> 节 %s' % (ib, imp_rva, sec_of_rva(imp_rva)))
print()
print('%-22s %-10s %-10s %-8s %-10s %-8s %-10s %-8s' %
      ('DLL', 'FirstThunkRVA', 'FT节', 'idx', 'ILT值(RVA)', 'ILT节', 'IAT槽内容(VA)', '槽节'))
p = r2o(imp_rva)
idx = 0
rows = []
while True:
    o = p + idx * 20
    oft, ts, fc, name_rva, ft = struct.unpack_from('<IIIII', d, o)
    if oft == 0 and name_rva == 0 and ft == 0:
        break
    do = r2o(name_rva)
    dll = d[do:d.find(b'\0', do)].decode('ascii', 'replace') if do not in (None, '?') else '?'
    ilt_rva = oft if oft else ft
    k = 0
    while True:
        to = r2o(ilt_rva + k * 4)
        if to in (None, '?'):
            break
        ilt_val, = struct.unpack_from('<I', d, to)
        if ilt_val == 0:
            break
        slot_rva = ft + k * 4
        so = r2o(slot_rva)
        slot_val = struct.unpack_from('<I', d, so)[0] if so not in (None, '?') else None
        if not (ilt_val & 0x80000000):
            rows.append((dll, ft, sec_of_rva(slot_rva), k, ilt_val, sec_of_rva(ilt_val),
                         slot_val, sec_of_va(slot_val) if slot_val else '?'))
        k += 1
    idx += 1

from collections import Counter
print('命名导入项 =', len(rows))
print()
print('统计：')
print('  (A) ILT 值(IBN RVA) 所在节分布 =', dict(Counter(r[5] for r in rows)))
print('  (B) IAT 数组位置 所在节分布   =', dict(Counter(r[2] for r in rows)))
print('  (C) IAT 槽内容(VA) 所在节分布 =', dict(Counter(r[7] for r in rows)))
print()
print('前 6 行明细：')
for r in rows[:6]:
    print('  %-14s FT=0x%X %-7s idx=%-3d ILT=0x%X %-8s 槽=0x%X %s' % r)
print()
tgt = [r for r in rows if r[3] == 62 and r[0].upper().startswith('KERNEL32')]
print('目标项 (KERNEL32 idx=62)：')
for r in tgt:
    print('  %-14s IAT位置 RVA=0x%X 节=%s ; ILT值 0x%X 节=%s ; 槽内容 0x%X 节=%s' %
          (r[0], r[1] + 62 * 4, r[2], r[4], r[5], r[6], r[7]))
