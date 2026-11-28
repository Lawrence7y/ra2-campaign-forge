# -*- coding: utf-8 -*-
# R216 audit: A7 计数口径对照 (capstone 无skipdata 重同步 vs objdump 流式)
import sys, json, re, subprocess, hashlib
sys.path.insert(0, '/home/t628/projects/ra2-campaign-forge/_r185')
import pe185 as P
from capstone import Cs, CS_ARCH_X86, CS_MODE_32

D = json.load(open('/home/t628/projects/ra2-campaign-forge/_r216/audit_ds_views.json'))
VIEWS = {int(k, 16): v for k, v in D['views'].items()}
VSET = set(VIEWS)
SLOTS = set(x for v in VIEWS.values() for x in v)
texte = P.B['.text']; lo, hi = texte['lo'], texte['hi_file']
print("VSET n=%d  sha1=%s" % (len(VSET), hashlib.sha1(b''.join(int(x).to_bytes(4,'little') for x in sorted(VSET))).hexdigest()[:16]))
print("SLOTS n=%d  overlap VSET&SLOTS=%d" % (len(SLOTS), len(VSET & SLOTS)))
print("text %08x..%08x (%d bytes)" % (lo, hi, hi-lo))

def blob(a, n):
    o = P.r2o(a); return P.RAW[o:o+n]

# ---------- caliber 1: capstone linear, NO skipdata, resync on failure
MD = Cs(CS_ARCH_X86, CS_MODE_32)
tot = v_hit = 0
d0 = dp = dn = 0
samples = []
va = lo
while va < hi:
    n = min(0x10000, hi - va)
    got = 0
    for off, sz, mn, ops in MD.disasm_lite(blob(va, n), va):
        got = off + sz - va
        if mn != 'mov': continue
        m = re.match(r'^dword ptr \[([a-z0-9]{2,3})((?:\s*[+-]\s*(?:0x[0-9a-f]+|\d+))?)\],\s*(0x[0-9a-f]+)$', ops)
        if not m: continue
        tot += 1
        imm = int(m.group(3), 16)
        if imm not in VSET: continue
        v_hit += 1
        d = m.group(2).replace(' ', '')
        if not d: d0 += 1
        elif d.startswith('+'): dp += 1
        else: dn += 1
        if dp + dn + d0 <= 6 and len(samples) < 6: samples.append((off, ops))
    if got == 0: va += 1
    else: va += max(0, (n) - (va + n - (va))) if False else va + n
print("\n[capstone no-skipdata] C7 mov-imm-to-mem sites=%d ; imm in VSET=%d (disp0=%d disp+=%d disp-=%d)" % (tot, v_hit, d0, dp, dn))
print(" samples:", samples)

# ---------- caliber 2: objdump streaming
cmd = ['i686-w64-mingw32-objdump', '-d', '-M', 'intel', '--no-show-raw-insn',
       '/home/t628/projects/ra2-campaign-forge/ra2bench/gamemd.exe']
p = subprocess.Popen(cmd, stdout=subprocess.PIPE, text=True, bufsize=1 << 20)
tot2 = hit2 = 0
d02 = dp2 = dn2 = 0
samp2 = []
line_re = re.compile(r'^\s*([0-9a-f]+):\s+mov\s+dword ptr \[([a-z0-9]{2,3})((?:\s*[+-]\s*(?:0x[0-9a-f]+|\d+))?)\],\s*(0x[0-9a-f]+)\s*$')
for line in p.stdout:
    m = line_re.match(line)
    if not m: continue
    a = int(m.group(1), 16)
    if not (lo <= a < hi): continue
    tot2 += 1
    imm = int(m.group(4), 16)
    if imm not in VSET: continue
    hit2 += 1
    d = m.group(3).replace(' ', '')
    if not d: d02 += 1
    elif d.startswith('+'): dp2 += 1
    else: dn2 += 1
    if len(samp2) < 6: samp2.append((a, line.strip()))
p.stdout.close(); p.wait()
print("\n[objdump intel] C7 mov-imm-to-mem sites=%d ; imm in VSET=%d (disp0=%d disp+=%d disp-=%d)" % (tot2, hit2, d02, dp2, dn2))
print(" samples:", samp2)
