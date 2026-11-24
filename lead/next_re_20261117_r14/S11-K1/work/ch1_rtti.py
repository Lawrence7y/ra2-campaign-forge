"""
S11-K1 Channel 1: byte-level RTTI enumeration of LocomotionClass family.
Independent of function_atlas.tsv. Uses pefile + raw dword reads only.
Method:
  1) scan ALL sections for TD names '.?AV*LocomotionClass@@\\0' (exact, 2 @)
  2) validate TD {+0:typeinfo-vftable-ptr (in .rdata), +4:spare=0, +8:name}
  3) scan aligned dwords (all sections) for references to TD => COL = ref-0xC; validate COL
  4) scan aligned dwords (all sections) for references to COL => vtable = ref+4
  5) count code slots per vtable (.text dwords), stop at next COL / separator const / non-code
"""
import re
import struct
from collections import defaultdict
from pehelp import (EXE, PE, IMAGE_BASE, rd, u32, sections, section_of, in_section,
                    is_code, va2off)

OUT = r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S11-K1\EVIDENCE\ch1_rtti_enum.txt'
lines = []
def P(s=''):
    lines.append(str(s))
    print(s)

# section byte ranges (use max(VirtualSize,SizeOfRawData) to cover padding)
SEC_RANGES = []
for nm, vaoff, vsize, rsize, praw in sections():
    SEC_RANGES.append((nm, IMAGE_BASE + vaoff, IMAGE_BASE + vaoff + max(vsize, rsize)))

# --- step 1: find TD name strings ending exactly 'LocomotionClass@@\0' ---
# TD name pattern: .?AV<Name>LocomotionClass@@  (2 trailing @), then \0
pat = re.compile(rb'\.\?A[UV][A-Za-z0-9_]*LocomotionClass@@\x00')
td_by_name = {}
for nm, lo, hi in SEC_RANGES:
    blob = rd(lo, hi - lo)
    for m in pat.finditer(blob):
        name = m.group(0)[:-1].decode('latin1')  # strip trailing \0
        name_va = lo + m.start()
        td_va = name_va - 8
        P('TD-cand sec=%s name@%08X td=%08X name=%s' % (nm, name_va, td_va, name))
        td_by_name.setdefault(td_va, name)

P('--- TD candidates: %d ---' % len(td_by_name))

# validate TDs
valid_td = {}
for td, name in sorted(td_by_name.items()):
    try:
        v = u32(td); spare = u32(td + 4)
    except Exception:
        continue
    ok = in_section(v, '.rdata') and spare == 0
    P('TD %08X %-42s vft=%08X spare=%d %s' % (td, name, v, spare, 'OK' if ok else 'BAD'))
    if ok:
        valid_td[td] = name
P('--- valid TDs: %d ---' % len(valid_td))

# --- step 2/3: scan aligned dwords for TD references => COLs ---
td_set = set(valid_td.keys())
cols = []
for nm, lo, hi in SEC_RANGES:
    for va in range(lo, hi - 4 + 1, 4):
        try:
            v = u32(va)
        except Exception:
            continue
        if v in td_set:
            col = va - 0xC
            try:
                sig = u32(col); off = u32(col + 4); cd = u32(col + 8)
                chk_td = u32(col + 0xC); chd = u32(col + 0x10)
            except Exception:
                continue
            ok = sig == 0 and chk_td == v and in_section(chd, '.rdata')
            P('COL-ref sec=%s @%08X col=%08X td=%08X %-42s sig=%d off=%d cd=%d chd=%08X %s' %
              (nm, va, col, v, valid_td[v], sig, off, cd, chd, 'OK' if ok else 'BAD'))
            if ok:
                cols.append((col, v, off, cd, chd))
P('--- COLs: %d ---' % len(cols))

# --- step 4: scan aligned dwords for COL references => vtables ---
col_set = {c[0] for c in cols}
col_info = {c[0]: c for c in cols}
vtables = []
for nm, lo, hi in SEC_RANGES:
    for va in range(lo, hi - 4 + 1, 4):
        try:
            v = u32(va)
        except Exception:
            continue
        if v in col_set:
            vt = va + 4
            col, td, off, cd, chd = col_info[v]
            try:
                slot0 = u32(vt)
            except Exception:
                continue
            vtables.append((vt, v, td, valid_td[td], off, slot0))
            P('VTABLE sec=%s @%08X col=%08X off=%d td=%08X %-42s slot0=%08X %s' %
              (nm, vt, v, off, td, valid_td[td], slot0, 'CODE' if is_code(slot0) else 'non-code'))
P('--- vtables total: %d ---' % len(vtables))
loco_vts = [x for x in vtables if 'LocomotionClass' in x[3]]
P('--- Locomotion vtables: %d ---' % len(loco_vts))

# --- step 5: count code slots ---
SEP = {0x00004E40, 0x399D52A2, 0x469D913F}
all_cols = col_set
def count_slots(vt, maxn=120):
    n = 0
    for i in range(maxn):
        a = vt + 4*i
        try:
            v = u32(a)
        except Exception:
            break
        if v in all_cols or v in SEP or not is_code(v):
            break
        n += 1
    return n

byclass = defaultdict(list)
for vt, col, td, name, off, slot0 in loco_vts:
    byclass[name].append((vt, off, col, slot0))

P('')
P('===== LocomotionClass family summary (RTTI-derived) =====')
classes = sorted(byclass)
P('CLASS COUNT = %d' % len(classes))
for name in classes:
    P('### %s' % name)
    for vt, off, col, slot0 in sorted(byclass[name], key=lambda x: -x[1]):
        n = count_slots(vt)
        P('  off=%-3d vt=%08X col=%08X slots=%d (end=%08X) slot0=%08X' %
          (off, vt, col, n, vt + 4*n, slot0))

with open(OUT, 'w', encoding='utf-8') as f:
    f.write('\n'.join(lines) + '\n')
print('\nWROTE', OUT)
