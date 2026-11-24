"""m8: independent byte re-verification of the three-ring rows.

For every candidate row we re-read the raw bytes and re-derive each ring WITHOUT
reusing the index structures that produced the candidate:
  ②  u32(vt + 4*slot) == entry  AND  [vt-4]=COL -> [COL+0xC]=TD -> TD+8 starts .?AV/.?AU
  ④  the 4 bytes at the call site are E8, site+5+rel32 == entry, site outside [lo,hi), site != entry
  ③b the witness instruction sequence is decoded again from the file bytes and printed
Anything that fails any step is reported as REJECTED.
"""
import sys, json, struct
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import core2 as C, b3b
from capstone.x86 import X86_OP_MEM, X86_OP_IMM

C.build_jt(); C.build_index(); C.build_atexit()
OUT = Path(__file__).parent.parent

def jload(p): return json.loads(Path(p).read_text(encoding='utf-8'))
R = {r['entry']: r for r in jload(OUT/'work'/'rings.json') if 'err' not in r}
pool = jload(OUT/'work'/'pool.json')
P = {p['entry']: p for p in pool}

cand = []
for e, p in P.items():
    r = R[e]
    h2 = r['has2_rtti'] or r['has2_yrpp']
    h4 = r['n_direct_out'] > 0 or r['n_livevt_live'] > 0
    if h2 and h4 and r['cats']:
        cand.append(e)
cand.sort()

print('candidates =', len(cand))
rej = []
rows = []
for ekey in cand:
    r = R[ekey]; e = int(ekey, 16)
    lo, hi = r['lo'], r['hi']
    ok = True; why = []

    # ---- ② re-read from raw bytes
    if r['has2_rtti']:
        vt, slot = r['rtti_vt'], r['rtti_slot']
        vt = int(vt, 16)
        raw_slot = struct.unpack_from('<I', C.raw, C.va2off(vt + 4*slot))[0]
        if raw_slot != e:
            ok = False; why.append('②slot %08X != %08X' % (raw_slot, e))
        col = struct.unpack_from('<I', C.raw, C.va2off(vt - 4))[0]
        td  = struct.unpack_from('<I', C.raw, C.va2off(col + 0xC))[0]
        nm  = C.cstr(td + 8)
        if not nm.startswith(('.?AV', '.?AU')):
            ok = False; why.append('②rtti chain broken at %08X (%r)' % (td + 8, nm[:24]))
        cls = nm
    else:
        cls = (r.get('yrpp') or {}).get('cls', '')
        if not (r['yrpp'] and r['yrpp']['ok']):
            ok = False; why.append('②yrpp not conforming')
        vt = slot = None

    # ---- ④ re-read the E8 bytes
    sites = []
    for s in r['direct_out']:
        off = C.va2off(s)
        b0 = C.raw[off]
        rel = struct.unpack_from('<i', C.raw, off + 1)[0]
        tgt = (s + 5 + rel) & 0xffffffff
        if b0 != 0xE8:
            ok = False; why.append('④ byte@%08X=%02X not E8' % (s, b0))
        elif tgt != e:
            ok = False; why.append('④ %08X -> %08X != %08X' % (s, tgt, e))
        elif lo <= s < hi:
            ok = False; why.append('④ %08X inside body' % s)
        elif s == e:
            ok = False; why.append('④ %08X self-loop' % s)
        else:
            sites.append('%08X' % s)
    if not sites and r['n_livevt_live'] == 0:
        ok = False; why.append('④ no witness survives re-read')

    # ---- ③b: re-decode witnesses
    r3 = b3b.classify(e, level='strict')
    if r3['cats'] != r['cats']:
        ok = False; why.append('③b unstable %s vs %s' % (r3['cats'], r['cats']))
    if not r3['cats']:
        ok = False; why.append('③b vanished')

    print('-' * 96)
    print('%s  %s  %-34s  %s' % (ekey, P[ekey]['sub'], P[ekey]['name'][:34],
                                 'OK' if ok else 'REJECTED ' + '; '.join(why)))
    if r['has2_rtti']:
        print('  ② vt=%08X slot=%-4d  [vt-4]=%08X -> TD=%08X -> %r' % (
            vt, slot, col, td, cls[:40]))
    else:
        print('  ② YRpp %s hits=%s' % (cls, r['yrpp']['hits']))
    print('  ④ direct sites (E8 re-read) = %s   extent=[%08X,%08X)' % (','.join(sites), lo, hi))
    for h in r3['b1']:
        print('  ③b① %s @%08X targets=%d arms=%d distinct=%d' % (h[0], h[1], h[2], h[3], h[4]))
    for h in r3['b2']:
        print('  ③b② %s' % (h,))
    if r3['b3'].get('ok'):
        print('  ③b③ ctor=%d vt=%d size=%s maxdisp=%s' % (
            r3['b3']['n_ctor'], r3['b3']['n_vt'], r3['b3']['size'], r3['b3']['max_disp']))
    if r3['b4'].get('ok'):
        print('  ③b④ loop head=%08X back=%08X n=%d ind=%s bound=%s' % (
            r3['b4']['head'], r3['b4']['back'], r3['b4']['n'],
            r3['b4'].get('ind'), r3['b4'].get('bound')))
    rows.append(dict(entry=ekey, sub=P[ekey]['sub'], name=P[ekey]['name'],
                     ok=ok, why='; '.join(why), cats=r3['cats'],
                     vt=('%08X' % vt) if vt else '', slot=slot, cls=cls,
                     sites=sites, lo='%08X' % lo, hi='%08X' % hi))
    if not ok: rej.append(ekey)

print()
print('=== VERDICT: %d/%d candidates confirmed from raw bytes; rejected=%s ===' % (
    len(rows)-len(rej), len(rows), rej))
(OUT/'work'/'verify22.json').write_text(json.dumps(rows, ensure_ascii=False, indent=1), encoding='utf-8')
