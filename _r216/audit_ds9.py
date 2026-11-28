# -*- coding: utf-8 -*-
# R216 audit: verify 4195 anchor = capstone(skipdata) imm in VSET and base != esp
import sys, json, re
from collections import Counter
sys.path.insert(0, '/home/t628/projects/ra2-campaign-forge/_r185')
import pe185 as P
from capstone import Cs, CS_ARCH_X86, CS_MODE_32

D = json.load(open('/home/t628/projects/ra2-campaign-forge/_r216/audit_ds_views.json'))
VIEWS = {int(k, 16): v for k, v in D['views'].items()}
VSET = set(VIEWS)
lo, hi = P.B['.text']['lo'], P.B['.text']['hi_file']
def blob(a, n):
    o = P.r2o(a); return P.RAW[o:o+n]

MD = Cs(CS_ARCH_X86, CS_MODE_32); MD.skipdata = True
RX = re.compile(r'^dword ptr \[([a-z0-9]{2,3})((?:[+-](?:0x[0-9a-f]+|\d+))?)\],\s*(0x[0-9a-f]+)$')
per = Counter(); tot = 0; hits = 0; spos = 0
va = lo
while va < hi:
    n = min(0x10000, hi - va)
    for off, sz, mn, ops in MD.disasm_lite(blob(va, n), va):
        raw = blob(off, sz)
        if not (mn == 'mov' and raw and raw[0] == 0xC7): continue
        tot += 1
        m = RX.match(ops)
        if not m: continue
        imm = int(m.group(3), 16)
        if imm not in VSET: continue
        hits += 1
        r = m.group(1)
        per[r] += 1
        if r == 'esp': spos += 1
    va += n
print("[capstone skipdata] C7 mov sites=%d ; imm in VSET=%d ; of which esp-base=%d ; non-esp=%d" % (tot, hits, spos, hits - spos))
for k, v in sorted(per.items(), key=lambda x: -x[1]): print("   %s %d" % (k, v))
