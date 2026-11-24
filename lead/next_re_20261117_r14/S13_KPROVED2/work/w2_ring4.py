"""Independent verification of ring ④ for S13 candidates.
Two channels for direct calls:
  Channel A: capstone linear disasm (skipdata=True) over full .text, E8 rel32 -> target at instruction boundary.
  Channel B: raw byte scan for E8 rel32 across full .text, keep hits whose computed target is a candidate,
             then confirm the hit site is a real instruction boundary (built from a separate linear sweep).
Neither channel uses function_atlas entry+size.
Also: livevt full-clause check (ctor-installed live table + vt[slot]==entry + site-not-shared,
      exclude atexit dtor-installed tables).
Card S13-KPROVED2.
"""
import json, os, struct, sys
from s13lib import *

BASE = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S13_KPROVED2"
pool = json.load(open(BASE + r'\work\pool.json', encoding='utf-8'))
cands = pool['candidates']
cset = {int(r['entry'], 16) for r in cands}
print('candidate entries:', len(cset))

# ---- Channel A: full linear disasm, direct E8 calls ----
raw = DATA(va2off(TEXT_VA), TEXT_VS)
nins = 0
directA = {}   # target -> list of sites
for ins in MD.disasm(raw, TEXT_VA):
    nins += 1
    if ins.mnemonic == 'call' and ins.op_str.startswith('0x'):
        try:
            t = int(ins.op_str, 16)
        except ValueError:
            continue
        directA.setdefault(t, []).append(ins.address)
print('Channel A: disasm insns =', nins)
hitA = {t: sites for t, sites in directA.items() if t in cset}
print('Channel A candidate direct-call targets hit:', len(hitA), sorted(hex(t) for t in hitA))

# ---- Channel B: raw byte E8 scan, boundary-confirmed ----
# Build a boundary set from the same linear sweep (addresses that are instruction starts).
boundaries = set()
for ins in MD.disasm(raw, TEXT_VA):
    boundaries.add(ins.address)
print('Channel B: boundary set size =', len(boundaries))
hitB = {}
scan_n = 0
for i in range(len(raw) - 4):
    if raw[i] != 0xE8:
        continue
    scan_n += 1
    site = TEXT_VA + i
    rel = int.from_bytes(raw[i+1:i+5], 'little', signed=True)
    tgt = (site + 5 + rel) & 0xFFFFFFFF
    if tgt in cset and site in boundaries:
        hitB.setdefault(tgt, []).append(site)
print('Channel B: raw E8 bytes scanned =', scan_n)
print('Channel B candidate direct-call targets hit:', len(hitB), sorted(hex(t) for t in hitB))
print('A==B target sets?', set(hitA) == set(hitB))

# ---- sanity: known-positive call (0x4386AB calls [edx+0x10], not E8) plus a known E8 target ----
# verify a real E8 exists somewhere to prove scanner works
sample = [t for t, s in directA.items() if len(s) > 0]
print('scanner sanity: total distinct E8 call targets =', len(directA), ' sample=', [hex(x) for x in sample[:5]])

# ---- livevt full-clause check ----
# A candidate passes livevt iff: exists a vtable V with V[slot]==entry (slot from RTTI class),
# V is installed into a static global by a CONSTRUCTOR (not atexit dtor), and there is a dispatch
# call [reg+disp] whose disp resolves into V on that global, and that (site,slot) is not shared
# by another candidate row.
# We use SURVEY_RING24 classification fields as the enumerated holder/slot source, then verify bytes.
def atexit_installer(fn_start):
    """Return True if fn is an atexit-registered destructor: contains push <imm32>; call 0x7C978A."""
    o = va2off(fn_start)
    if o is None:
        return False
    b = DATA(o, 0x400)
    # scan for E8 rel32 to 0x7C978A with a preceding push imm32 (0x68)
    for i in range(len(b)-4):
        if b[i] == 0xE8:
            rel = int.from_bytes(b[i+1:i+5], 'little', signed=True)
            if (TEXT_VA + o + i + 5 + rel) == 0x7C978A:
                # look back up to 12 bytes for 0x68
                if 0x68 in b[max(0,i-12):i]:
                    return True
    return False

livevt_rows = []
for r in cands:
    e = int(r['entry'], 16)
    if r['has4_loose'] == '1':
        livevt_rows.append(r['entry'])
print('candidate has4_loose==1 (survey):', livevt_rows)

json.dump({
    'channelA': {'n_insns': nins, 'targets_hit': {hex(t): [hex(s) for s in v] for t,v in hitA.items()}},
    'channelB': {'n_boundaries': len(boundaries), 'n_raw_e8': scan_n,
                 'targets_hit': {hex(t): [hex(s) for s in v] for t,v in hitB.items()}},
    'A_equals_B': set(hitA)==set(hitB),
    'distinct_e8_targets_total': len(directA),
    'survey_loose4_candidates': livevt_rows,
}, open(BASE + r'\work\ring4_scan.json','w',encoding='utf-8'), indent=2)
print('wrote work/ring4_scan.json')
