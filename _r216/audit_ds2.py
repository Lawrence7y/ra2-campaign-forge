# -*- coding: utf-8 -*-
# R216 audit (deepseek) rebuild with corrected COL layout; A1,A5,A8,A9,A2,A3 + save views.json
import sys, struct, json
sys.path.insert(0, '/home/t628/projects/ra2-campaign-forge/_r185')
import pe185 as P
from capstone import Cs, CS_ARCH_X86, CS_MODE_32

MD = Cs(CS_ARCH_X86, CS_MODE_32); MD.detail = False

def dw(va):
    o = P.r2o(va)
    return None if o is None else struct.unpack_from('<I', P.RAW, o)[0]
def sw(va):
    o = P.r2o(va)
    return None if o is None else struct.unpack_from('<i', P.RAW, o)[0]
def blob(va, n):
    o = P.r2o(va)
    return None if o is None else P.RAW[o:o+n]
def nz(va, m=200):
    b = P.cstr(va, m)
    return None if b is None else b.decode('latin1', 'replace')

text = P.B['.text']

# ---------- a) COL records: [sig<=2][offset][cdOffset==0][pTD .data w/ .?A name][pCHD .rdata]
COLA = {}
bad = []
for sname in ('.rdata', '.data'):
    s = P.B[sname]
    for va in range(s['lo'], s['hi_file'] - 20 + 1, 4):
        sig = dw(va)
        if sig is None or sig > 2: continue
        off = sw(va+4); cd = dw(va+8); td = dw(va+12); chd = dw(va+16)
        if off is None or cd != 0: continue
        if td is None or P.where(td) != '.data': continue
        if chd is None or P.where(chd) != '.rdata': continue
        nm = nz(td+8)
        if not nm or not nm.startswith('.?A') or '@@' not in nm: continue
        # pCHD sanity: sig 0, attributes, numBaseClasses <= 0x400, base array in .rdata
        if dw(chd) != 0: continue
        nb = dw(chd+8)
        if nb is None or nb > 0x400: continue
        if P.where(dw(chd+12) or 0) != '.rdata': continue
        COLA[va] = (off, td, chd, nm)
print("== a) COL records ==\n total=%d  distinct_names=%d" % (len(COLA), len(set(v[3] for v in COLA.values()))))
for k in sorted(COLA):
    if COLA[k][3] == '.?AVAbstractClass@@':
        print("  COL %08x mdisp=%d td=%08x chd=%08x" % (k, COLA[k][0], COLA[k][1], COLA[k][2]))

# ---------- b) preambles
pre = {}
for sname in ('.rdata', '.data'):
    s = P.B[sname]
    for va in range(s['lo'], s['hi_file'] - 8 + 1, 4):
        d = dw(va)
        if d is None or d not in COLA: continue
        nx = dw(va+4)
        if nx is not None and text['lo'] <= nx < text['hi_file']:
            pre.setdefault(d, []).append(va+4)
uniq = {k: v[0] for k, v in pre.items() if len(v) == 1}
starts = sorted(uniq.values()); starts_set = set(starts)
print("\n== b) preambles ==\n cola_keys=%d preamble_hits=%d exact1=%d views=%d multi=%d"
      % (len(COLA), len(pre), len(uniq), len(starts), len(pre)-len(uniq)))

VIEWS = {}
def sec_of_va(va):
    for sc in P.SECS:
        if sc['lo'] <= va < sc['hi_file']: return sc
    return None
for st in starts:
    sc = sec_of_va(st); lim = sc['hi_file']
    sl = []; va = st
    while va < lim:
        if va != st and va in starts_set: break
        d = dw(va)
        if d is None or not (text['lo'] <= d < text['hi_file']): break
        sl.append(d); va += 4
    VIEWS[st] = sl
tot = sum(len(v) for v in VIEWS.values())
dist = len(set(x for v in VIEWS.values() for x in v))
print(" slots=%d distinct_targets=%d" % (tot, dist))
print(" BASELINE views=1214 slots=14044 distinct=6692 ->",
      "PASS" if (len(starts), tot, dist) == (1214, 14044, 6692) else "FAIL(see numbers above)")
json.dump({'views': {('%08x' % k): v for k, v in VIEWS.items()},
           'cola': {('%08x' % k): list(v) for k, v in COLA.items()},
           'preamble2view': {('%08x' % k): v for k, v in uniq.items()}},
          open('/home/t628/projects/ra2-campaign-forge/_r216/audit_ds_views.json', 'w'))

def find_view(name, mdisp):
    out = []
    for col, st in uniq.items():
        if COLA[col][3] == name and COLA[col][0] == mdisp: out.append((st, VIEWS[st], col))
    return out

print("\n== A1 AbstractClass views ==")
got = {}
for m in (0, 4, 8, 12):
    for st, sl, col in find_view('.?AVAbstractClass@@', m):
        got[m] = (st, len(sl)); print("  mdisp=%2d view=%08x slots=%2d COL=%08x" % (m, st, len(sl), col))
exp = {0: (0x7e1f50, 24), 4: (0x7e1f34, 6), 8: (0x7e1f2c, 1), 12: (0x7e1f24, 1)}
print(" A1:", "PASS" if got == exp else "FAIL", "got=", {k: (hex(v[0]), v[1]) for k, v in got.items()},
      "exp=", {k: (hex(v[0]), v[1]) for k, v in exp.items()})

print("\n== A5 main view 0x7e1f50 ==")
main = VIEWS.get(0x7e1f50, [])
card = [0x410260,0x410300,0x410310,0x4c9150,0x410450,0x4c9150,0x4c9150,0x4103e0,
        0x4105a0,0x410470,0x410480,0x4c9150,0x4c9150,0x410410,0x410490,0x4104a0,
        0x4104b0,0x410440,0x4104c0,0x4104f0,0x410520,0x410530,0x410540,0x410570]
print("  n=%d" % len(main))
print("  got :", ' '.join('%08x' % x for x in main))
print("  card:", ' '.join('%08x' % x for x in card))
print("  A5 slots:", "PASS" if main == card else "FAIL")
if main != card:
    for i in range(max(len(main), len(card))):
        a = main[i] if i < len(main) else None; b = card[i] if i < len(card) else None
        if a != b: print("   slot%-2d got %s want %s" % (i, '%08x' % a if a else '-', '%08x' % b if b else '-'))
marks = [(0x410300, 'b801000000c20400'), (0x4c9150, '33c0c3'), (0x410440, 'b001c3'),
         (0x410490, '83c8ffc3'), (0x410520, '32c0c3'), (0x410530, '32c0c3'),
         (0x410470, 'c3'), (0x410570, 'c3'), (0x410480, 'c20800')]
ok = True
for va, hx in marks:
    g = blob(va, len(hx)//2).hex(); same = (g == hx); ok &= same
    print("  %08x want %-16s got %-16s %s" % (va, hx, g, 'OK' if same else 'MISMATCH'))
print("  A5 bytemarks:", "PASS" if ok else "FAIL")

print("\n== A8 thunks ==")
for va, want_tgt in ((0x4105e0, 0x410260), (0x4105f0, 0x410300), (0x410600, 0x410310)):
    b = blob(va, 11)
    ins = list(MD.disasm_lite(b, va))
    line = ' ; '.join('%s %s' % (x[2], x[3]) for x in ins)
    print("  %08x bytes=%s | %s" % (va, b.hex(), line))
    print("         shape x836c240404e9xxxxxxxx:", b[:5].hex() == '836c240404' and b[5] == 0xe9 and len(ins) == 2)

def dis(va, n, label):
    print("\n== %s @ %08x (%d bytes) ==" % (label, va, n))
    for off, sz, mn, ops in MD.disasm_lite(blob(va, n), va):
        print("  %08x  %-32s  %-8s %s" % (off, blob(off, sz).hex(), mn, ops))

dis(0x410210, 24, 'A9 0x410210')
dis(0x4105a0, 0x40, 'A2 0x4105a0')
dis(0x410260, 0x100, 'A3 0x410260 QueryInterface')

print("\n== A3 constants ===")
import uuid
for va in (0x7f7c90, 0x7f7c80, 0x7f7c70, 0x7e9ae0):
    b = blob(va, 16)
    d1, d2, d3 = struct.unpack_from('<IHH', b, 0); rest = b[8:].hex()
    s = "%08X-%04X-%04X-%s-%s" % (d1, d2, d3, rest[:4], rest[4:])
    print("  %08x sec=%-7s hex=%s guid=%s" % (va, P.where(va), b.hex(), s))
