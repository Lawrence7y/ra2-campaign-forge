# -*- coding: utf-8 -*-
"""R219 m7：四个「幻影虚表」的真实来历 —— .data 里 16 字节静态记录表。

已知（R218）：0x877000 / 0x877010 / 0x87b17c / 0x87b18c 是 dw(V-4)==COL 但 dw(V) 不落 .text 的
「幻影虚表」，槽数 0，.text 内 dword 引用 0。

本脚本要回答：
  [1] 这 4 个地址处在什么结构里？用 16 字节窗口刻画记录边界与字段。
  [2] 这些记录的「COL 指针」字段分别指向哪几个 COL（0x800040 / 0xa00060 还是更多）？
      全 .data 里这些 COL 各出现多少次、在哪些地址？
  [3] 该记录表的起止范围（用字段 3 落 .rdata 且字段 0 形态稳定的判据，两端都要给出边界证据）。
  [4] 是否有代码以「基址 + 索引*16」方式访问它？（扫 `lea reg, [imm + reg*16]` 与 disp 形式）
  [5] 这些 COL（0x800040 / 0xa00060）指向的类名与 mdisp，以及它们各自真正的主视图地址。

正控：0x7e8278 与 0x7e1f50 是 R218 已确认的真虚表（.text 内有 dword 引用），本脚本要复现其引用计数。
反控：把「记录」步长改成 12 与 20 时，字段 3 落 .rdata 的比例必须显著低于 16 字节步长。
"""
import sys, struct, collections, json, re
sys.path.insert(0, '/home/t628/projects/ra2-campaign-forge')
import _r185.pe185 as P
from capstone import Cs, CS_ARCH_X86, CS_MODE_32

md = Cs(CS_ARCH_X86, CS_MODE_32); md.detail = False; md.skipdata = True
OUT = {}

def words(sn):
    s = P.B[sn]
    return struct.unpack_from('<%dI' % (s['rawsize'] // 4), P.RAW, s['rawptr']), s['lo']
def s32(v): return struct.unpack('<i', struct.pack('<I', v))[0]

# ---------- [1] 16-byte window around each phantom ----------
PH = [0x877000, 0x877010, 0x87b17c, 0x87b18c]
print('[1] 16-byte framed view (record start = V-4):')
frames = {}
for v in PH:
    rec = v - 4          # record starts at the COL pointer field -? see below
    print('  --- phantom V=%#x ; COL ptr at V-4=%#x = %#x ---' % (v, v - 4, P.dw(v - 4)))
    base = v - 4
    for j in range(-2, 3):
        a = base + 16 * j
        w = [P.dw(a + 4 * k) for k in range(4)]
        mark = ' <== COL ptr' if a == base else ''
        print('     %#08x: %08x %08x %08x %08x%s' % (a, *w, mark))
    frames[hex(v)] = [P.dw(base + 4 * k) for k in range(4)]
OUT['frames'] = frames

# ---------- [2] COL pointer multiplicity ----------
da = P.B['.data']; draw = P.RAW[da['rawptr']:da['rawptr'] + da['rawsize']]
def find_dword(seg_raw, seg_lo, val):
    pat = struct.pack('<I', val); out = []; st = 0
    while True:
        i = seg_raw.find(pat, st)
        if i < 0: break
        out.append(seg_lo + i); st = i + 1
    return out

COLPTRS = sorted(set(P.dw(v - 4) for v in PH))
print('\n[2] COL pointers found in the 4 phantom records: %s' % [hex(c) for c in COLPTRS])
for c in COLPTRS:
    occ_d = find_dword(draw, da['lo'], c)
    print('    COL %#x : .data occurrences = %d at %s' % (c, len(occ_d), [hex(x) for x in occ_d]))
    # name / mdisp
    nm = P.cstr(P.dw(c + 12) + 8, 256)
    print('      mdisp=%d pTD=%#x pCHD=%#x name=%s'
          % (s32(P.dw(c + 4)), P.dw(c + 12), P.dw(c + 16),
             nm.decode('latin1') if nm else None))
# 反控：0x800040 在 .rdata 里出现几次（R218 说 .data 恰 4 处）
rd = P.B['.rdata']; rdraw = P.RAW[rd['rawptr']:rd['rawptr'] + rd['rawsize']]
for c in COLPTRS:
    occ_r = find_dword(rdraw, rd['lo'], c)
    print('    COL %#x : .rdata occurrences = %d at %s' % (c, len(occ_r), [hex(x) for x in occ_r[:10]]))

# ---------- [3] extent of the 16-byte record table ----------
def is_rec(a):
    w = [P.dw(a + 4 * k) for k in range(4)]
    return P.where(w[3]) == '.rdata'
for anchor in (0x876ffc, 0x87b178):
    lo_a = anchor
    while is_rec(lo_a - 16):
        lo_a -= 16
    hi_a = anchor
    while is_rec(hi_a + 16):
        hi_a += 16
    n = (hi_a - lo_a) // 16 + 1
    print('\n[3] record table containing %#x : starts %#x ends %#x  records=%d'
          % (anchor, lo_a, hi_a, n))
    for a in range(lo_a, lo_a + 16 * min(n, 4)):
        w = [P.dw(a + 4 * k) for k in range(4)]
        print('     %#08x: %08x %08x %08x %08x' % (a, *w))
    print('     ... last 4:')
    for a in range(hi_a - 16 * min(n - 1, 3), hi_a + 1, 16):
        w = [P.dw(a + 4 * k) for k in range(4)]
        print('     %#08x: %08x %08x %08x %08x' % (a, *w))

# ---------- [3b] 反控：步长 12 / 20 时的字段命中率 ----------
def hit_rate(anchor, start_lo, start_hi, step):
    tot = ok = 0
    a = anchor
    while a - step >= start_lo: a -= step
    while a <= start_hi:
        tot += 1
        if P.where(P.dw(a + step - 4)) == '.rdata': ok += 1
        a += step
    return ok, tot
for step in (12, 16, 20, 24):
    ok, tot = hit_rate(0x876ffc, 0x876f00, 0x877100, step)
    print('[3b] step=%2d : field3-in-.rdata %d/%d = %.2f' % (step, ok, tot, ok / tot if tot else 0))

# ---------- [4] indexed/code access to the table ----------
T = P.B['.text']; LO, RAWOFF, RAWSZ = T['lo'], T['rawptr'], T['rawsize']
raw = P.RAW[RAWOFF:RAWOFF + RAWSZ]
insns = []
pos = 0
while pos < len(raw):
    got = False
    for a, sz, mn, ops in md.disasm_lite(raw[pos:pos + 16], LO + pos):
        insns.append((a, mn, ops)); pos += sz; got = True; break
    if not got: pos += 1
print('\n[4] sweep %d insns' % len(insns))

RANGES = [(0x876f00, 0x878000), (0x87b000, 0x87b300)]
def in_ranges(v):
    return any(lo <= v < hi for lo, hi in RANGES)
hits = []
for a, mn, ops in insns:
    for m in re.finditer(r'0x8[0-9a-f]{5}', ops):
        v = int(m.group(0), 16)
        if in_ranges(v):
            hits.append((a, mn, ops)); break
print('    insns referencing an address inside the two record-table ranges: %d' % len(hits))
for a, mn, ops in hits[:25]:
    print('      %#x %s %s' % (a, mn, ops))

# ---------- [5] positive controls ----------
print('\n[5] POSITIVE CONTROLS (real vtables):')
for t in (0x7e8278, 0x7e1f50):
    n_t = len(find_dword(raw, LO, t))
    n_r = len(find_dword(rdraw, rd['lo'], t))
    n_d = len(find_dword(draw, da['lo'], t))
    print('    %#x : .text refs=%d .rdata refs=%d .data refs=%d' % (t, n_t, n_r, n_d))
for v in PH:
    n_t = len(find_dword(raw, LO, v))
    print('    phantom %#x : .text dword refs=%d' % (v, n_t))

json.dump(dict(colptrs=[hex(c) for c in COLPTRS], hits=[(hex(a), mn, o) for a, mn, o in hits]),
          open('/home/t628/projects/ra2-campaign-forge/_r219/m7.json', 'w'), indent=1)
print('\n[done] -> _r219/m7.json')
