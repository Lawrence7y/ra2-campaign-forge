# -*- coding: utf-8 -*-
"""R219 m10：.data 内 16 字节步长常量对表的定界与「唯一误报源」判定。

m9 已证：判据 dw(V-4) in COL 在 1218 个候选里产生 4 个误报（V 的 dw 不落 .text），
这 4 个全部位于 .data，且其 dw(V)=0x010000c0、dw(V-4)=0x800040。

本脚本定死这张表的形状：
  [1] 记录形态 = 4 dword，其中第 3、4 个满足 f3 == f2 + 0x00800080（实测关系）。
  [2] 用该关系在全 .data 求 16 字节对齐的完整记录集，报起止边界与相邻行证据。
  [3] 报全部记录（地址 | f2 | f3 | 差），确认差值恒为 0x00800080 的占比。
  [4] 反控 A：把关系放宽为 f3 - f2 == 0x00800000 / 0x00800100 时命中数必须为 0（关系不是随便成立）。
  [5] 反控 B：全 .text 中对该表地址区间的 dword 引用必须为 0（表不被代码以指针方式使用）。
  [6] 反控 C：把「记录起点」移位 4 字节后，关系命中数必须降到 0（对齐唯一）。
  [7] 全库核对：还有哪些 .data/.rdata 位置满足 dw(V-4) in COL 且 dw(V) 不落 .text（应仍为这 4 个）。
正控：真虚表 0x7e8278 的 V-4 是 COL 0x800040 且 dw(0x7e8278) 落 .text；0x7e1f50 槽数 24，0x7e8278 槽数 50。
"""
import sys, struct, collections, json
sys.path.insert(0, '/home/t628/projects/ra2-campaign-forge')
import _r185.pe185 as P

def s32(v): return struct.unpack('<i', struct.pack('<I', v))[0]
def words(sn):
    s = P.B[sn]
    return struct.unpack_from('<%dI' % (s['rawsize'] // 4), P.RAW, s['rawptr']), s['lo']

COL = {}
for sn in ('.rdata', '.data'):
    w, base = words(sn)
    for k in range(len(w) - 5):
        if w[k] > 2 or w[k + 2] != 0: continue
        if P.where(w[k + 3]) != '.data' or P.where(w[k + 4]) != '.rdata': continue
        nm = P.cstr(w[k + 3] + 8, 512)
        if not nm or nm[:3] != b'.?A' or nm[-2:] != b'@@': continue
        COL[base + 4 * k] = dict(md_=s32(w[k + 1]), pCHD=w[k + 4], name=nm.decode('latin1'))
CS = set(COL)

DELTA = 0x00800080
def rel(a):
    f2 = P.dw(a + 8); f3 = P.dw(a + 12)
    return f2, f3, (f3 - f2) & 0xFFFFFFFF

# ---------- [1]/[2] ----------
ANCHOR = 0x876ff4
print('[1] record shape at anchor %#x : f2=%08x f3=%08x diff=%#x (expect %#x)'
      % ((ANCHOR,) + rel(ANCHOR) + (DELTA,)))
def ok(a): return rel(a)[2] == DELTA
lo = ANCHOR
while ok(lo - 16): lo -= 16
hi = ANCHOR
while ok(hi + 16): hi += 16
print('[2] table containing %#x : start=%#x end=%#x records=%d'
      % (ANCHOR, lo, hi, (hi - lo) // 16 + 1))
print('    prev row %#x : %08x %08x %08x %08x' % (lo - 16, *[P.dw(lo - 16 + 4 * k) for k in range(4)]))
print('    first rows:')
for a in range(lo, min(hi + 1, lo + 16 * 5), 16):
    f2, f3, d = rel(a)
    print('      %#08x : %08x %08x %08x %08x   f2=%08x f3=%08x d=%#x'
          % (a, *[P.dw(a + 4 * k) for k in range(4)], f2, f3, d))
print('    last rows:')
for a in range(max(lo, hi - 16 * 4), hi + 1, 16):
    f2, f3, d = rel(a)
    print('      %#08x : %08x %08x %08x %08x   f2=%08x f3=%08x d=%#x'
          % (a, *[P.dw(a + 4 * k) for k in range(4)], f2, f3, d))
print('    next row %#x : %08x %08x %08x %08x' % (hi + 16, *[P.dw(hi + 16 + 4 * k) for k in range(4)]))

# ---------- [3] all records in .data with that relation ----------
da = P.B['.data']
recs = [a for a in range(da['lo'], da['lo'] + da['rawsize'] - 16, 16) if ok(a)]
print('\n[3] all 16B-aligned records in .data with f3-f2==%#x : %d' % (DELTA, len(recs)))
print('    addresses:', [hex(a) for a in recs])
print('    contiguous blocks:')
blocks = []
if recs:
    s = recs[0]; p = recs[0]
    for a in recs[1:]:
        if a == p + 16: p = a; continue
        blocks.append((s, p)); s = a; p = a
    blocks.append((s, p))
for s, p in blocks:
    print('      %#x .. %#x  (%d records)' % (s, p, (p - s) // 16 + 1))

# ---------- [4] 反控 A ----------
print('\n[4] NEG CONTROL A: other deltas')
for d in (0x00800000, 0x00800100, 0x00800040, 0x008000c0):
    n = sum(1 for a in range(da['lo'], da['lo'] + da['rawsize'] - 16, 16)
            if rel(a)[2] == d)
    print('    delta %#x -> %d records (window all .data)' % (d, n))

# ---------- [5] 反控 B ----------
T = P.B['.text']; traw = P.RAW[T['rawptr']:T['rawptr'] + T['rawsize']]
print('\n[5] NEG CONTROL B: .text dword references into the table range')
refs = 0
if blocks:
    tlo, thi = blocks[0][0], blocks[-1][1] + 16
    for a in range(tlo, thi, 4):
        pat = struct.pack('<I', a); st = 0
        while True:
            i = traw.find(pat, st)
            if i < 0: break
            refs += 1; st = i + 1
    print('    table range %#x..%#x ; .text dword refs = %d (expect 0)' % (tlo, thi, refs))

# ---------- [6] 反控 C ----------
print('\n[6] NEG CONTROL C: shift record start by 4 / 8 / 12 bytes')
for sh in (4, 8, 12, 16):
    n = sum(1 for a in range(lo + sh, hi + 1, 16) if rel(a)[2] == DELTA)
    print('    shift %2d -> %d hits' % (sh, n))
# window-based recompute to be fair (not just inside the discovered table)
for sh in (4, 8, 12):
    n = sum(1 for a in range(lo - 0x40 + sh, hi + 0x40, 16) if rel(a)[2] == DELTA)
    print('    shift %2d (widened window) -> %d hits' % (sh, n))

# ---------- [7] full-library recount ----------
print('\n[7] full-library recount of dw(V-4) in COL:')
ghost = []
for sn in ('.rdata', '.data'):
    w, base = words(sn)
    for k, v in enumerate(w):
        V = base + 4 * k + 4
        if v in CS and P.where(P.dw(V)) != '.text':
            ghost.append((V, v, sn))
print('    ghost count = %d' % len(ghost))
for V, c, sn in ghost:
    print('      %#08x in %s COL=%#x (%s) dw(V)=%#x' % (V, sn, c, COL[c]['name'], P.dw(V)))

# ---------- positive controls ----------
def nslots(vt, cap=65536):
    n = 0
    while n < cap and P.where(P.dw(vt + 4 * n)) == '.text': n += 1
    return n
print('\n[8] POSITIVE CONTROLS')
c = P.dw(0x7e8278 - 4)
print('    0x7e8278: V-4=%#x in COL=%s name=%s dw(V)=%#x where=%s slots=%d'
      % (c, c in CS, COL[c]['name'] if c in CS else None, P.dw(0x7e8278), P.where(P.dw(0x7e8278)), nslots(0x7e8278)))
print('    0x7e1f50: slots=%d (expect 24)' % nslots(0x7e1f50))

json.dump(dict(delta=hex(DELTA), table=[hex(lo), hex(hi)], recs=[hex(x) for x in recs],
               blocks=[[hex(s), hex(p)] for s, p in blocks], text_refs=refs,
               ghosts=[(hex(V), hex(c), sn) for V, c, sn in ghost]),
          open('/home/t628/projects/ra2-campaign-forge/_r219/m10.json', 'w'), indent=1)
print('\n[done] -> _r219/m10.json')
