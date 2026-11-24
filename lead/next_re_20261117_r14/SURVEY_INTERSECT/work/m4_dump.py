"""m4: dump the three-ring rows and the ring-4 disagreements for eyeball verification."""
import sys, json
from pathlib import Path
OUT = Path(__file__).parent.parent

def jload(p): return json.loads(Path(p).read_text(encoding='utf-8'))

R = {r['entry']: r for r in jload(OUT/'work'/'rings.json') if 'err' not in r}
pool = jload(OUT/'work'/'pool.json')
P = {p['entry']: p for p in pool}

print('=== 22 three-ring rows (② ∧ ④ ∧ ③b), pool = %d ===' % len(pool))
n = 0
for e in sorted(P):
    r = R[e]
    h2 = r['has2_rtti'] or r['has2_yrpp']
    h4 = r['n_direct_out'] > 0 or r['n_livevt_unanimous'] > 0
    if h2 and h4 and r['cats']:
        n += 1
        print('%s %s %-36s ②%s vt=%s slot=%s cls=%s | ④dir=%d lv=%d sites=%s | ③b=%s | b1=%s b2=%s b3=%s b4=%s' % (
            e, P[e]['sub'], P[e]['name'][:36],
            'rtti' if r['has2_rtti'] else 'yrpp', r['rtti_vt'], r['rtti_slot'], (r['rtti_cls'] or [''])[0][:28],
            r['n_direct_out'], r['n_livevt_unanimous'],
            ','.join('%08X' % s for s in r['direct_out'][:3]),
            '+'.join(r['cats']),
            'Y' if '③b①' in r['cats'] else '-', 'Y' if '③b②' in r['cats'] else '-',
            'Y' if '③b③' in r['cats'] else '-', 'Y' if '③b④' in r['cats'] else '-'))
print('total =', n)

print()
print('=== ring-④ rows where my n_direct_out differs from SURVEY-RING24 ===')
for e in ('004325A0', '004DA2B0', '005F1EE0', '0069BAB0'):
    r = R[e]
    print('%s mine dir_out=%d all=%d extent=[%08X,%08X) span=%d atlas=%s sites=%s' % (
        e, r['n_direct_out'], r['n_direct_all'], r['lo'], r['hi'], r['span'], r['atlas_size'],
        ','.join('%08X' % s for s in r['direct_out'])))
    print('     pools: %s' % (P.get(e, {}).get('sub', 'NOT-IN-MY-POOL'),))
