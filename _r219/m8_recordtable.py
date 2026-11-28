# -*- coding: utf-8 -*-
"""R219 m8：.data 内 16 字节记录表的精确结构（R218「4 个幻影虚表」的真实载体）。

m7 已证：0x800040(=DropPodLocomotionClass COL) 在 .data 只出现 4 次，
地址 0x876ffc / 0x87700c / 0x87b178 / 0x87b188；每个后面紧跟 0xc0000001。
R218 的判据 dw(V-4)==COL 把「记录字段 i=COL、字段 i+1=0xc0000001」误切成「COL / 虚表 V」。

本脚本定死记录表：
  [1] 以 16 字节为步长、从候选对齐起点枚举，找「字段 2 落 .data/.rdata 的指针 且 字段 3 是 0xc0000001 形态」
      的对齐方式与表范围（两端边界都要给出证据行）。
  [2] 报出表内所有记录（地址 + 4 字段 + 字段 3 的数值集合）。
  [3] 字段 2 指向的 COL 全集：类名、mdisp、以及该 COL 的真虚表（.rdata/.data 里 dw==COL 的位置+4，且 dw(V) 落 .text）。
  [4] 反控：把记录步长改成 8 / 12 / 20 时，「字段 3 == 0xc0000001 形态」命中率必须显著下降。
  [5] 反控：这些记录地址是否被 .text 以 dword 引用（m7 已报 0，此处复现）。
正控：0x7e8278（真虚表，COL=0x800040）与 0x7e1f50（COL 见输出）必须在 [3] 中被正确归到同一个 COL。
"""
import sys, struct, collections, json, re
sys.path.insert(0, '/home/t628/projects/ra2-campaign-forge')
import _r185.pe185 as P

def s32(v): return struct.unpack('<i', struct.pack('<I', v))[0]
def words(sn):
    s = P.B[sn]
    return struct.unpack_from('<%dI' % (s['rawsize'] // 4), P.RAW, s['rawptr']), s['lo']

# ---- COL / vtable rebuild ----
COL = {}
for sn in ('.rdata', '.data'):
    w, base = words(sn)
    for k in range(len(w) - 5):
        if w[k] > 2 or w[k + 2] != 0: continue
        if P.where(w[k + 3]) != '.data' or P.where(w[k + 4]) != '.rdata': continue
        nm = P.cstr(w[k + 3] + 8, 512)
        if not nm or nm[:3] != b'.?A' or nm[-2:] != b'@@': continue
        COL[base + 4 * k] = dict(md_=s32(w[k + 1]), pCHD=w[k + 4], name=nm.decode('latin1'))
CS = set(COL); VT = {}
for sn in ('.rdata', '.data'):
    w, base = words(sn)
    for k, v in enumerate(w):
        if v in CS: VT[base + 4 * k + 4] = v

# ---- [1] find the record lattice ----
# A record is [f0][f1][COLptr][magic] where magic is a dword with low byte 01 and high bits set (0xc0000001 / 0xe0002001)
def is_magic(v):
    return (v & 0xFF) == 0x01 and (v >> 28) in (0xc, 0xe, 0x1, 0x8)
def is_colptr(v):
    return v in CS or P.where(v) in ('.data', '.rdata')
ANCHORS = [0x876ffc, 0x87700c, 0x87b178, 0x87b188]
print('[1] alignment search: for each of the 4 known COL-ptr addresses, which 16B lattice fits?')
for aptr in ANCHORS:
    for start in range(aptr - 12, aptr + 1, 4):
        ok = True
        for a in (start, start + 16, start + 32):
            if not (is_colptr(P.dw(a + 8)) and is_magic(P.dw(a + 12))):
                ok = False; break
        if ok:
            print('   anchor %#x fits lattice with record start %#x (field2 at start+8)' % (aptr, start))
            break

# use the discovered lattice: record start = aptr-8
START = ANCHORS[0] - 8
print('\n[1b] lattice probe from %#x outward (16B step, predicate = field2 colptr AND field3 magic):' % START)
def rec_ok(a):
    return is_colptr(P.dw(a + 8)) and is_magic(P.dw(a + 12))
lo = START
while rec_ok(lo - 16): lo -= 16
hi = START
while rec_ok(hi + 16): hi += 16
print('    table start=%#x end=%#x  records=%d' % (lo, hi, (hi - lo) // 16 + 1))
print('    boundary evidence: prev row %#x fields=%s ; next row %#x fields=%s'
      % (lo - 16, ['%08x' % P.dw(lo - 16 + 4 * k) for k in range(4)],
         hi + 16, ['%08x' % P.dw(hi + 16 + 4 * k) for k in range(4)]))
for a in range(lo, lo + 16 * min((hi - lo) // 16 + 1, 8)):
    f = [P.dw(a + 4 * k) for k in range(4)]
    nm = COL[f[2]]['name'] if f[2] in COL else P.where(f[2])
    print('      %#08x: %08x %08x %08x %08x   COL->%s' % (a, *f, nm))

# ---- [2]/[3] all records of this lattice in .data ----
da = P.B['.data']
print('\n[2] full scan of .data for the same lattice:')
recs = []
A = da['lo']
while A + 16 <= da['lo'] + da['rawsize']:
    if rec_ok(A):
        recs.append(A)
    A += 4   # 4-byte step then filter by 16-alignment consistency below
# keep only maximal 16-aligned chains
recs16 = [a for a in recs if (a - lo) % 16 == 0]
print('    predicate hits at 4B step = %d ; of them 16B-aligned to %#x lattice = %d' % (len(recs), len(recs16)))
magics = collections.Counter(P.dw(a + 12) for a in recs)
print('    magic value distribution:', {hex(k): v for k, v in magics.most_common()})
colrefs = collections.Counter(P.dw(a + 8) for a in recs)
print('    field2 (pointer) distribution: %d distinct' % len(colrefs))
for v, c in colrefs.most_common(10):
    nm = COL[v]['name'] if v in COL else P.where(v)
    print('      %08x x%-3d %s' % (v, c, nm))

print('\n[3] for each COL referenced by a record with 0xc0000001 magic, find its real vtable:')
seen = {}
for a in recs:
    if P.dw(a + 12) != 0xc0000001: continue
    c = P.dw(a + 8)
    cands = [v for v, cc in VT.items() if cc == c]
    real = [v for v in cands if P.where(P.dw(v)) == '.text']
    ghost = [v for v in cands if P.where(P.dw(v)) != '.text']
    key = c
    seen.setdefault(key, dict(records=[], real=[], ghost=[]))
    seen[key]['records'].append(a)
    seen[key]['real'] += real
    seen[key]['ghost'] += ghost
for c, d in seen.items():
    nm = COL[c]['name'] if c in COL else '?'
    print('   COL %#x %-34s mdisp=%d' % (c, nm, COL[c]['md_'] if c in COL else -1))
    print('      records in .data : %s' % [hex(x) for x in d['records']])
    print('      real vtables     : %s' % [hex(x) for x in d['real']])
    print('      ghost "vtables"  : %s' % [hex(x) for x in d['ghost']])

# ---- [4] 反控：其他步长 ----
print('\n[4] NEG CONTROL step sizes (predicate = field at +8 is COL ptr AND +12 is magic), window %#x..%#x'
      % (lo - 0x40, hi + 0x40))
for step in (8, 12, 16, 20, 24):
    tot = ok = 0
    a = lo - 0x40
    while a <= hi + 0x40:
        tot += 1
        if is_colptr(P.dw(a + 8)) and is_magic(P.dw(a + 12)): ok += 1
        a += step
    print('    step=%2d : %d/%d = %.2f' % (step, ok, tot, ok / tot if tot else 0))

# ---- [5] 反控：.text dword refs ----
print('\n[5] .text dword references to the 4 R218-claimed phantom V addresses:')
T = P.B['.text']; traw = P.RAW[T['rawptr']:T['rawptr'] + T['rawsize']]
for v in (0x877000, 0x877010, 0x87b17c, 0x87b18c):
    pat = struct.pack('<I', v); n = 0; st = 0
    while True:
        i = traw.find(pat, st)
        if i < 0: break
        n += 1; st = i + 1
    print('    %#x : %d' % (v, n))
print('\n[6] POSITIVE CONTROL real vtables -> their COL:')
for v in (0x7e8278, 0x7e1f50):
    c = P.dw(v - 4)
    print('    vtable %#x -> COL %#x %s' % (v, c, COL[c]['name'] if c in COL else '?'))

json.dump(dict(table_lo=hex(lo), table_hi=hex(hi), recs=[hex(x) for x in recs],
               magics={hex(k): v for k, v in magics.items()},
               colrefs={hex(k): v for k, v in colrefs.items()}),
          open('/home/t628/projects/ra2-campaign-forge/_r219/m8.json', 'w'), indent=1)
print('\n[done] -> _r219/m8.json')
