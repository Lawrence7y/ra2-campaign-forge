# -*- coding: utf-8 -*-
# R216 audit (deepseek): A6 law U + A3 full disasm + A8 exact 10-byte shape
import sys, struct, json
sys.path.insert(0, '/home/t628/projects/ra2-campaign-forge/_r185')
import pe185 as P
from capstone import Cs, CS_ARCH_X86, CS_MODE_32
MD = Cs(CS_ARCH_X86, CS_MODE_32)

D = json.load(open('/home/t628/projects/ra2-campaign-forge/_r216/audit_ds_views.json'))
VIEWS = {int(k, 16): v for k, v in D['views'].items()}
COLA = {int(k, 16): v for k, v in D['cola'].items()}
UNIQ = {int(k, 16): v for k, v in D['preamble2view'].items()}
VM = {}   # view start -> mdisp
for col, st in UNIQ.items(): VM[st] = COLA[col][0]
print("views=%d  with_mdisp_neq0=%d  mdisp_hist=%s" % (
    len(VM), sum(1 for v in VM.values() if v != 0),
    {m: sum(1 for v in VM.values() if v == m) for m in sorted(set(VM.values()))}))

def blob(va, n):
    o = P.r2o(va)
    return P.RAW[o:o+n]

print("\n== A6 law U ==")
cand = 0; ok = 0; bad = []
shape_other = 0
for st, m in sorted(VM.items()):
    if m == 0: continue
    ins = list(MD.disasm_lite(blob(st, 16), st))
    if len(ins) < 2: shape_other += 1; continue
    a0, a1 = ins[0], ins[1]
    # a0 = sub/add dword ptr [esp + 4], N
    if a0[2] not in ('sub', 'add'): shape_other += 1; continue
    if 'dword ptr [esp + 4]' not in a0[3]: shape_other += 1; continue
    try: N = int(a0[3].rsplit(',', 1)[1].strip(), 0)
    except Exception: shape_other += 1; continue
    if a0[2] == 'sub': N = N
    else: N = -N
    if a1[2] != 'jmp' or not a1[3].startswith('0x'): shape_other += 1; continue
    tgt = int(a1[3], 16)
    if tgt not in VM: shape_other += 1; continue
    cand += 1
    want = m - VM[tgt]
    if N == want: ok += 1
    else: bad.append((st, m, tgt, VM[tgt], N, want))
print(" adjustor-shaped views=%d  of which N==mdisp-t.mdisp: %d  counterexamples: %d  non-shape(mdisp!=0)=%d"
      % (cand, ok, len(bad), shape_other))
for b in bad[:10]:
    print("   BAD self=%08x mdisp=%d tgt=%08x tmdisp=%d N=%d want=%d" % b)
print(" A6:", "PASS" if (sum(1 for v in VM.values() if v != 0) == 260 and cand == 101 and ok == 101 and not bad) else "FAIL")

print("\n== A8 exact 10-byte shape ==")
allok = True
for va, tgt in ((0x4105e0, 0x410260), (0x4105f0, 0x410300), (0x410600, 0x410310)):
    b = blob(va, 10)
    got = b.hex()
    ins = list(MD.disasm_lite(blob(va, 12), va))
    jmptgt = int(ins[1][3], 16) if len(ins) > 1 and ins[1][2] == 'jmp' else None
    good = got[:12] == '836c240404e9' and jmptgt == tgt
    allok &= good
    print("  %08x %s  jmp->%s want %08x  %s" % (va, got, '%08x' % jmptgt if jmptgt else '?', tgt, 'OK' if good else 'MISMATCH'))
print(" A8:", "PASS" if allok else "FAIL")

print("\n== A3 full 0x410260 disasm ==")
for off, sz, mn, ops in MD.disasm_lite(blob(0x410260, 0x9a), 0x410260):
    print("  %08x  %-24s %-8s %s" % (off, blob(off, sz).hex(), mn, ops))
