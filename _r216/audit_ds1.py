# -*- coding: utf-8 -*-
# R216 audit (deepseek, read-only): view table rebuild + A1..A5, A8, A9
import sys, struct
sys.path.insert(0, '/home/t628/projects/ra2-campaign-forge/_r185')
import pe185 as P

def u32(va):
    o = P.r2o(va)
    return None if o is None else struct.unpack_from('<I', P.RAW, o)[0]
def s32(va):
    o = P.r2o(va)
    return None if o is None else struct.unpack_from('<i', P.RAW, o)[0]
def blob(va, n):
    o = P.r2o(va)
    return None if o is None else P.RAW[o:o+n]
def kname(va):
    b = P.cstr(va, 200)
    return None if b is None else b.decode('latin1', 'replace')

print("== sections ==")
for s in P.SECS:
    print(" %-8s lo=%08x rawptr=%08x rawsize=%08x vsize=%08x hi_file=%08x" % (
        s['name'], s['lo'], s['rawptr'], s['rawsize'], s['vsize'], s['hi_file']))

text = P.B['.text']

# ---- a) COLA
COLA = {}
def scan_sec(name):
    s = P.B[name]; n = 0
    for va in range(s['lo'], s['hi_file'] - 20 + 1, 4):
        mdisp = s32(va)
        if mdisp is None or mdisp > 2: continue
        ptd = u32(va+4); z = u32(va+8); nm = u32(va+12); pchd = u32(va+16)
        if ptd is None or ptd == 0: continue
        if P.where(ptd) != '.data': continue
        if z != 0: continue
        if nm is None or P.where(nm) not in ('.data', '.rdata'): continue
        if pchd is None or P.where(pchd) != '.rdata': continue
        nmv = kname(nm)
        if not nmv or not nmv.startswith('.?A') or '@@' not in nmv: continue
        tdn = None
        if u32(ptd) == 0 and P.where(u32(ptd+4) or 0) == '.data':
            tdn = kname(u32(ptd+4))
        chd = u32(pchd+8)
        COLA[va] = (mdisp, ptd, chd, nmv)
        n += 1
    return n
n1 = scan_sec('.rdata'); n2 = scan_sec('.data')
print("\n== a) COLA ==\n rdata=%d data=%d total=%d" % (n1, n2, len(COLA)))
names = sorted(set(v[3] for v in COLA.values()))
print(" distinct names=%d" % len(names))
for k, v in sorted(COLA.items()):
    if v[3] == '.?AVAbstractClass@@':
        print("  COLA %08x mdisp=%d td=%08x chd=%d name=%s" % (k, v[0], v[1], v[2], v[3]))

# ---- b) preambles
pre = {}
for sname in ('.rdata', '.data'):
    s = P.B[sname]
    for va in range(s['lo'], s['hi_file'] - 8 + 1, 4):
        if va not in COLA: continue
        nx = u32(va+4)
        if nx is not None and text['lo'] <= nx < text['hi_file']:
            pre.setdefault(va, []).append(va+4)
print("\n== b) preambles ==\n preamble hits=%d exact1=%d" % (len(pre), sum(1 for k, v in pre.items() if len(v) == 1)))
uniq = {k: v[0] for k, v in pre.items() if len(v) == 1}
starts = sorted(uniq.values())
starts_set = set(starts)
print(" views=%d" % len(starts))

# slots: consecutive dwords in .text from start until next start or .rdata end
VIEWS = {}
tot_slots = 0
for st in starts:
    sl = []
    va = st
    while va < text['hi_file']:
        if va in starts_set and va != st: break
        d = u32(va)
        if d is None: break
        if not (text['lo'] <= d < text['hi_file']): break
        sl.append(d); va += 4
    VIEWS[st] = sl
    tot_slots += len(sl)
print(" slots=%d distinct_targets=%d" % (tot_slots, len(set(x for v in VIEWS.values() for x in v))))

def view_of(name, mdisp):
    out = []
    for k, st in uniq.items():
        if COLA[k][3] == name and COLA[k][0] == mdisp:
            out.append((st, VIEWS[st], k))
    return out

print("\n== A1 AbstractClass views ==")
got = {}
for m in (0, 4, 8, 12):
    r = view_of('.?AVAbstractClass@@', m)
    for st, sl, k in r:
        got[m] = (st, len(sl))
        print("  mdisp=%2d start=%08x slots=%d cola=%08x" % (m, st, len(sl), k))
exp = {0: (0x7e1f50, 24), 4: (0x7e1f34, 6), 8: (0x7e1f2c, 1), 12: (0x7e1f24, 1)}
print(" A1:", "PASS" if got == exp else "FAIL", "got=%s" % {k: (hex(v[0]), v[1]) for k, v in got.items()})

print("\n== A5 main view slot targets ==")
main = VIEWS[0x7e1f50]
card = [0x410260,0x410300,0x410310,0x4c9150,0x410450,0x4c9150,0x4c9150,0x4103e0,
        0x4105a0,0x410470,0x410480,0x4c9150,0x4c9150,0x410410,0x410490,0x4104a0,
        0x4104b0,0x410440,0x4104c0,0x4104f0,0x410520,0x410530,0x410540,0x410570]
print("  got n=%d -> %s" % (len(main), ' '.join('%08x' % x for x in main)))
print("  A5 list match:", "PASS" if main == card else "FAIL")
if main != card:
    for i, (a, b) in enumerate(zip(main, card)):
        if a != b: print("   slot%d got %08x want %08x" % (i, a, b))
    print("   len got %d want %d" % (len(main), len(card)))
bytemarks = [(0x410300, 'b801000000c20400'), (0x4c9150, '33c0c3'), (0x410440, 'b001c3'),
             (0x410490, '83c8ffc3'), (0x410520, '32c0c3'), (0x410530, '32c0c3'),
             (0x410470, 'c3'), (0x410570, 'c3'), (0x410480, 'c20800')]
okall = True
for va, hexs in bytemarks:
    gotb = blob(va, len(hexs)//2).hex()
    ok = gotb == hexs
    okall &= ok
    print("  %08x want=%s got=%s %s" % (va, hexs, gotb, 'ok' if ok else 'MISMATCH'))
print("  A5 bytemarks:", "PASS" if okall else "FAIL")

print("\n== A8 adjustor thunk bytes ==")
for va, tgt in ((0x4105e0, 0x410260), (0x4105f0, 0x410300), (0x410600, 0x410310)):
    print("  %08x: %s   tgt=%08x" % (va, blob(va, 11).hex(), tgt))

print("\n== A9 0x410210 ==")
print("  bytes:", blob(0x410210, 32).hex())

print("\n== A2 0x4105a0 region (forced) ==")
print("  bytes 0x4105a0..0x4105e0:", blob(0x4105a0, 64).hex())

print("\n== A3 consts ==")
for va in (0x7f7c90, 0x7f7c80, 0x7f7c70, 0x7e9ae0):
    b = blob(va, 16)
    print("  %08x sec=%-7s hex=%s" % (va, P.where(va), b.hex() if b else 'None'))
