"""m5: mandatory positive/negative controls, classified directly from bytes (pool membership irrelevant).

POS 0053AF40  expect ②∧④∧③b (③b① per R14_COMMON §8.6 条3 例) — no vtable, so ② must come from YRpp
POS 0045A640  expect ②∧③b with ④ satisfied by a livevt dispatch
NEG 0069DEB0 / 00704350 / 004DDDE0  expect ③b NOT established (all ③a)
NEG 004F4240  expect ④ livevt rejected: the same global carries another table unless the slot agrees
"""
import sys, json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import core2 as C, b3b

OUT = Path(__file__).parent.parent
C.build_jt(); C.build_index(); C.build_atexit()

yr = json.loads((OUT/'work'/'yrpp.json').read_text(encoding='utf-8'))
BIND  = {int(k, 16): v for k, v in yr['bindings'].items()}
CADDR = {k: set(v) for k, v in yr['class_addrs'].items()}

def yrpp_conform(entry, addrs):
    bl = BIND.get(entry)
    if not bl: return None
    cls = bl[0][3]; cand = CADDR.get(cls, set())
    if not cand: return dict(ok=False, cls=cls, n_cand=0, n_hit=0, why='class_has_no_absolute_addrs')
    hits = set()
    for a in addrs:
        o = a - C.TVA; b = C.CODE[o:o+C.SZ[o]]
        for c in cand:
            if c.to_bytes(4, 'little') in b: hits.add(c)
    return dict(ok=(len(hits) >= 2), cls=cls, n_cand=len(cand), n_hit=len(hits),
                hits=['%08X' % h for h in sorted(hits)][:8], n_ins=len(addrs),
                why=('ok' if len(hits) >= 2 else 'insufficient_byte_match'))

def report(entry, role, expect):
    e = int(entry, 16)
    lo, hi, addrs, blocks = C.extent(e, cap=6000)
    slots = C.ENTRY2SLOTS.get(e, [])
    yc = yrpp_conform(e, addrs) if e in BIND else None
    dall = C.DIRECT.get(e, [])
    dout = [s for s in dall if not (lo <= s < hi) and s != e]
    lv_all = C.LIVEVT.get(e, [])
    lv_out = [x for x in lv_all if not (lo <= x[3] < hi)]
    lv_una = [x for x in lv_out if C.slot_unanimous(x[0], x[1], x[2])]
    lv_sgl = [x for x in lv_out if C.global_single_vt(x[0])]
    lv_live = [x for x in lv_una if not C.in_atexit_dtor(x[3])]
    r3 = b3b.classify(e, level='strict')
    has2 = bool(slots) or bool(yc and yc['ok'])
    has4 = bool(dout) or bool(lv_live)
    has3 = bool(r3['cats'])
    three = has2 and has4 and has3
    gate = ('three' if three else
            '②∧③b(④=livevt)' if (has2 and has3 and lv_live) else
            'no')
    return dict(entry=entry, role=role, expect=expect,
                has2=has2, has2_rtti=bool(slots), has2_yrpp=bool(yc and yc['ok']),
                rtti_cls=sorted({s[2] for s in slots})[:3],
                rtti_vt=(hex(slots[0][0]) if slots else ''), rtti_slot=(slots[0][1] if slots else ''),
                yrpp=yc,
                lo=lo, hi=hi, span=hi-lo, n_ins=len(addrs),
                n_direct_all=len(dall), n_direct_out=len(dout),
                direct_out=['%08X' % s for s in dout[:6]],
                n_livevt_all=len(lv_all), n_livevt_out=len(lv_out),
                n_livevt_unanimous=len(lv_una), n_livevt_single=len(lv_sgl),
                livevt_unanimous=[['%08X' % x[0], '%08X' % x[1], x[2], '%08X' % x[3], '%08X' % x[4]] for x in lv_una[:3]],
                livevt_all_witness=[['%08X' % x[0], '%08X' % x[1], x[2], '%08X' % x[3], '%08X' % x[4]] for x in lv_all[:4]],
                global_vts={('%08X' % x[0]): [('%08X' % v) for v in sorted(C.GLOBAL_VTS.get(x[0], ()))] for x in lv_all[:2]},
                has3b=has3, cats=r3['cats'], b1=[list(h) for h in r3['b1']],
                b2=[list(map(str, h)) for h in r3['b2_main']],
                b3={k: r3['b3'].get(k) for k in ('ok', 'n_ctor', 'n_vt', 'size', 'max_disp')},
                b4={k: r3['b4'].get(k) for k in ('ok', 'head', 'back', 'n', 'why', 'read', 'test', 'write', 'bounds')},
                gate=gate)

CASES = [('0053AF40', 'POS', '②∧④∧③b (③b①)'),
         ('0045A640', 'POS', '②∧③b, ④ = livevt'),
         ('0069DEB0', 'NEG', '③b 不成立'),
         ('00704350', 'NEG', '③b 不成立'),
         ('004DDDE0', 'NEG', '③b 不成立'),
         ('004F4240', 'NEG', '④ livevt 因同 global 另装表而不成立')]

res = []
for e, role, exp in CASES:
    d = report(e, role, exp); res.append(d)
    print('=' * 100)
    print('%s [%s] expect=%s' % (e, role, exp))
    print('  extent   = [%08X,%08X) span=%d n_ins=%d' % (d['lo'], d['hi'], d['span'], d['n_ins']))
    print('  ② rtti=%s %s cls=%s vt=%s slot=%s' % (d['has2_rtti'], d['rtti_cls'], '', d['rtti_vt'], d['rtti_slot']))
    print('  ② yrpp=%s  %s' % (d['has2_yrpp'], d['yrpp']))
    print('  ④ direct all=%d out=%d sites=%s' % (d['n_direct_all'], d['n_direct_out'], d['direct_out']))
    print('  ④ livevt all=%d out=%d unanimous=%d single-vt=%d' % (
        d['n_livevt_all'], d['n_livevt_out'], d['n_livevt_unanimous'], d['n_livevt_single']))
    if d['livevt_all_witness']: print('     witnesses(all) =', d['livevt_all_witness'])
    if d['livevt_unanimous']: print('     survivors(una) =', d['livevt_unanimous'])
    if d['global_vts']: print('     global->installed vt =', d['global_vts'])
    print('  ③b = %s   b1=%s b2=%s b3=%s b4=%s' % (d['cats'], d['b1'], d['b2'], d['b3'], d['b4']))
    print('  VERDICT  = %s' % d['gate'])

(OUT/'work'/'controls.json').write_text(json.dumps(res, ensure_ascii=False, indent=1, default=int), encoding='utf-8')
print('\nwrote controls.json')
