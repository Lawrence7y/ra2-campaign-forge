import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import core as C
import b3

C.build_jt()

def dbg(e):
    fn = b3.Fn(e)
    print('=== %08X blocks=%d ins=%d' % (e, len(fn.blocks), len(fn.ins)))
    for (site, tgts) in b3.jt_arms(fn):
        print(' jt site %08X targets %s' % (site, [hex(t) for t in tgts]))
        arms = [fn.order[t] for t in tgts]
        R = {a: fn.reach[a] for a in arms}
        for a, t in zip(arms, tgts):
            others = set()
            for b in arms:
                if b != a: others |= R[b]
            excl = R[a] - others
            calls = set(); slots = set(); writes = set(); terms = set()
            for n in sorted(excl):
                c, s, w = b3.block_effect(fn.blocks[n]); calls |= c; slots |= s; writes |= w
                terms.add(b3.term_shape(fn.blocks[n]))
            print('   arm %08X blocks=%d excl=%d calls=%s slots=%s writes=%s term=%s' % (
                t, len(R[a]), len(excl), sorted(hex(x) for x in calls)[:4],
                sorted(str(x) for x in slots)[:4], sorted(str(x) for x in writes)[:5],
                sorted(str(x) for x in terms)[:3]))
        print('   -> nq,nd =', b3.multiway(fn, arms)[:2])

for e in (0x00702D40, 0x00706640, 0x0053AF40):
    dbg(e)

# address boundary probe for 004D82B0
o = 0x004D82B0 - C.TVA
print('SZ at 004D82B0 =', C.SZ[o], 'KIND', C.KIND[o])
k = o
while k > 0 and C.SZ[k] == 0: k -= 1
print('nearest preceding boundary', hex(C.TVA+k), 'size', C.SZ[k], '-> covers to', hex(C.TVA+k+C.SZ[k]))
