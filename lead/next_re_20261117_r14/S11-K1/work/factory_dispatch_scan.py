"""
S11-K1: find the 'create locomotor by CLSID' factory dispatcher.
Byte-level: scan .text for refs to each locomotion CLSID (first dword), group by proximity,
identify code regions referencing MANY distinct CLSIDs => dispatcher candidates.
"""
import struct
from pehelp import (IMAGE_BASE, rd, u32, sections, in_section, is_code, disasm, fmt, va2off)

OUT = r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S11-K1\EVIDENCE\factory_dispatch_scan.txt'
lines=[]
def P(s=''):
    lines.append(str(s)); print(s)

CLSIDS = {
  0x7E9A30:'Drive', 0x7E9A40:'Hover', 0x7E9A50:'Tunnel', 0x7E9A60:'Walk',
  0x7E9A70:'DropPod', 0x7E9A80:'Fly', 0x7E9A90:'Teleport', 0x7E9AA0:'Mech',
  0x7E9AB0:'Ship', 0x7E9AC0:'Jumpjet', 0x7E9AD0:'Rocket',
}
# also include 0x7E9A20 as candidate base
CLSIDS[0x7E9A20] = 'BASE?'

txt_lo = IMAGE_BASE + 0x1000
txt_hi = IMAGE_BASE + 0x1000 + 0x3DF38D
blob = rd(txt_lo, txt_hi - txt_lo)

xrefs = []  # (site, clsid, name)
for c, name in CLSIDS.items():
    pat = struct.pack('<I', c)
    idx = 0
    while True:
        j = blob.find(pat, idx)
        if j < 0: break
        site = txt_lo + j
        xrefs.append((site, c, name))
        idx = j + 1
xrefs.sort()
P('total first-dword CLSID xrefs: %d' % len(xrefs))

# group by proximity 0x400
groups=[]
for site,c,name in xrefs:
    if groups and site - groups[-1][-1][0] <= 0x400:
        groups[-1].append((site,c,name))
    else:
        groups.append([(site,c,name)])
P('groups (0x400 window): %d' % len(groups))
for g in groups:
    names = sorted(set(n for s,c,n in g))
    if len(names) >= 3:
        P('  GROUP %08X..%08X : %d xrefs, %d distinct CLSIDs: %s' %
          (g[0][0], g[-1][0], len(g), len(names), ','.join(names)))
        for s,c,n in g:
            P('     %08X -> %s (%08X)' % (s,n,c))

# For each distinct-CLSID group >=3, find enclosing function by scanning backward for
# prologue (push ebp/mov ebp,esp or sub esp) and forward for ret, using capstone linear.
P('')
P('===== disasm of multi-CLSID regions =====')
for g in groups:
    names = set(n for s,c,n in g)
    if len(names) < 3: continue
    lo = g[0][0] - 0x120
    hi = g[-1][0] + 0x120
    P('--- region %08X..%08X (CLSIDs=%s) ---' % (lo, hi, ','.join(sorted(names))))
    for ins in disasm(lo, hi-lo):
        P(fmt(ins))

with open(OUT,'w',encoding='utf-8') as f:
    f.write('\n'.join(lines)+'\n')
print('\nWROTE',OUT)
