"""m9: emit deliverables (MATRIX3RING.tsv + EVIDENCE\*) and the sensitivity block."""
import sys, json, math, collections
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import core2 as C

OUT = Path(__file__).parent.parent
SUBS = ['S%02d' % i for i in range(1, 22)]

def jload(p): return json.loads(Path(p).read_text(encoding='utf-8'))
R  = {r['entry']: r for r in jload(OUT/'work'/'rings.json') if 'err' not in r}
pool = jload(OUT/'work'/'pool.json')
met  = jload(OUT/'work'/'metrics.json')['metrics']
M    = jload(OUT/'work'/'matrix.json')
V22  = {v['entry']: v for v in jload(OUT/'work'/'verify22.json')}

P = {p['entry']: p for p in pool}
def h2(r):    return r['has2_rtti'] or r['has2_yrpp']
def h2R(r):   return r['has2_rtti']
def h4(r):    return r['n_direct_out'] > 0 or r['n_livevt_live'] > 0
def h3b(r):   return bool(r['cats'])
def h3bA(r):  return bool(r['cats_sent'])
def h3bB(r):  return bool(r['cats_alt'])

rows = []
tot = collections.Counter()
for s in SUBS:
    keys = [p['entry'] for p in pool if p['sub'] == s]
    rs = [R[k] for k in keys]
    d = dict(sub=s, n=len(rs),
             r2=sum(h2(x) for x in rs), r2R=sum(h2R(x) for x in rs),
             r4=sum(h4(x) for x in rs), r4d=sum(x['n_direct_out'] > 0 for x in rs),
             r4l=sum(x['n_livevt_live'] > 0 for x in rs),
             r3b=sum(h3b(x) for x in rs), r3bA=sum(h3bA(x) for x in rs),
             r3bB=sum(h3bB(x) for x in rs),
             A=sum(h2(x) and h4(x) for x in rs), AR=sum(h2R(x) and h4(x) for x in rs),
             three=sum(h2(x) and h4(x) and h3b(x) for x in rs),
             threeR=sum(h2R(x) and h4(x) and h3b(x) for x in rs),
             proved=met[s]['proved'], threshold=met[s]['threshold'], total_n=met[s]['n'])
    d['up'] = d['proved'] + d['three']
    d['ok_now'] = d['proved'] >= d['threshold']
    d['ok_up'] = d['up'] >= d['threshold']
    d['gap_up'] = max(0, d['threshold'] - d['up'])
    d['gap_now'] = max(0, d['threshold'] - d['proved'])
    rows.append(d)
    for k in d:
        if k != 'sub': tot[k] += d[k]

# ---------- MATRIX3RING.tsv ----------
lines = ['subsystem\tpool_n\tring2\tring2_rtti_only\tring4\tring4_direct\tring4_livevt'
         '\tring3b\tthree_ring\tproved_now\tthreshold\tproved_up\tachieved_now\tachieved_up\tgap_up']
for d in rows:
    lines.append('%s\t%d\t%d\t%d\t%d\t%d\t%d\t%d\t%d\t%d\t%d\t%d\t%s\t%s\t%d' % (
        d['sub'], d['n'], d['r2'], d['r2R'], d['r4'], d['r4d'], d['r4l'], d['r3b'],
        d['three'], d['proved'], d['threshold'], d['up'],
        'YES' if d['ok_now'] else 'no', 'YES' if d['ok_up'] else 'no', d['gap_up']))
lines.append('TOTAL\t%d\t%d\t%d\t%d\t%d\t%d\t%d\t%d\t%d\t%d\t%d\t%d\t%d\t%d' % (
    tot['n'], tot['r2'], tot['r2R'], tot['r4'], tot['r4d'], tot['r4l'], tot['r3b'],
    tot['three'], tot['proved'], tot['threshold'], tot['up'],
    tot['ok_now'], tot['ok_up'], tot['gap_up']))
(OUT/'MATRIX3RING.tsv').write_text('\n'.join(lines) + '\n', encoding='utf-8')

# ---------- EVIDENCE\classification_rings.tsv (all pool rows) ----------
hdr = ['entry', 'subsystem', 'name', 'ring2', 'ring2_rtti', 'ring2_yrpp', 'rtti_class',
       'rtti_vt', 'rtti_slot', 'ring4', 'ring4_direct', 'ring4_livevt', 'direct_sites',
       'livevt_witness', 'ring3b', 'channels', 'three_ring', 'ext_lo', 'ext_hi', 'span',
       'atlas_size', 'ext_match', 'b1', 'b2', 'b3ok', 'b4ok']
out = ['\t'.join(hdr)]
for p in sorted(pool, key=lambda x: (x['sub'], x['entry'])):
    r = R[p['entry']]
    lb = ('%08X\t%08X\tslot%d\t%d\t%d' % (r['livevt_live'][0][0], r['livevt_live'][0][1],
                                          r['livevt_live'][0][2], r['livevt_live'][0][3],
                                          r['livevt_live'][0][4])) if r['n_livevt_live'] else ''
    out.append('\t'.join(map(str, [
        p['entry'], p['sub'], p['name'],
        1 if h2(r) else 0, 1 if r['has2_rtti'] else 0, 1 if r['has2_yrpp'] else 0,
        (r['rtti_cls'] or [''])[0] if r['has2_rtti'] else ((r['yrpp'] or {}).get('cls') or ''),
        r['rtti_vt'], r['rtti_slot'],
        1 if h4(r) else 0, r['n_direct_out'], r['n_livevt_live'],
        ','.join('%08X' % s for s in r['direct_out']), lb,
        1 if h3b(r) else 0, '+'.join(r['cats']) or '-',
        1 if (h2(r) and h4(r) and h3b(r)) else 0,
        '%08X' % r['lo'], '%08X' % r['hi'], r['span'], r['atlas_size'],
        1 if r['ext_match'] else 0,
        len(r['b1']), len(r['b2']), 1 if (r['b3'] or {}).get('ok') else 0,
        1 if (r['b4'] or {}).get('ok') else 0])))
(OUT/'EVIDENCE'/'classification_rings.tsv').write_text('\n'.join(out) + '\n', encoding='utf-8')

# ---------- EVIDENCE\three_ring_rows.tsv (the rows themselves, with anchors) ----------
hdr = ['entry', 'subsystem', 'name', 'ring2_channel', 'rtti_class', 'rtti_vt', 'rtti_slot',
       'direct_call_sites', 'ext_lo', 'ext_hi', 'ring3b_channels', 'ring3b_witness_b1',
       'b4_loop', 'verified']
out = ['\t'.join(hdr)]
for d in rows:
    for p in sorted([q for q in pool if q['sub'] == d['sub']], key=lambda x: x['entry']):
        r = R[p['entry']]
        if not (h2(r) and h4(r) and h3b(r)): continue
        v = V22.get(p['entry'], {})
        b1 = ';'.join('%s@%08X:t%d/a%d/d%d' % (h[0], h[1], h[2], h[3], h[4]) for h in r['b1'])
        b4 = ''
        if (r['b4'] or {}).get('ok'):
            bd = r['b4'].get('bound')
            bs = ('%08X:%s' % (bd[0], bd[1])) if isinstance(bd, (list, tuple)) else str(bd)
            b4 = 'head=%08X;back=%08X;n=%d;bound=%s' % (
                r['b4']['head'], r['b4']['back'], r['b4']['n'], bs)
        out.append('\t'.join(map(str, [
            p['entry'], p['sub'], p['name'],
            'RTTI' if r['has2_rtti'] else 'YRpp',
            (r['rtti_cls'] or [''])[0] if r['has2_rtti'] else ((r['yrpp'] or {}).get('cls') or ''),
            r['rtti_vt'], r['rtti_slot'],
            ','.join('%08X' % s for s in r['direct_out']),
            '%08X' % r['lo'], '%08X' % r['hi'],
            '+'.join(r['cats']), b1, b4,
            'PASS' if v.get('ok') else ('FAIL:' + v.get('why', '?'))])))
(OUT/'EVIDENCE'/'three_ring_rows.tsv').write_text('\n'.join(out) + '\n', encoding='utf-8')

# ---------- sensitivity ----------
print('=== SENSITIVITY ===')
print('③b main            = %d (%.2f%%)' % (tot['r3b'], 100.0*tot['r3b']/tot['n']))
print('③b 敏感档A(+哨兵)   = %d' % tot['r3bA'])
print('③b 敏感档B(①loose)  = %d' % tot['r3bB'])
print('② 仅RTTI           = %d ; ②含YRpp = %d' % (tot['r2R'], tot['r2']))
print('A  ②仅RTTI∧④       = %d ; A ②含YRpp∧④ = %d' % (tot['AR'], tot['A']))
print('三环 ②仅RTTI       = %d ; 三环 ②含YRpp = %d' % (tot['threeR'], tot['three']))
n_yrpp_in22 = sum(1 for p in pool if h2(R[p['entry']]) and h4(R[p['entry']]) and h3b(R[p['entry']])
                  and not R[p['entry']]['has2_rtti'])
print('三环行里靠 YRpp 通② 的 = %d' % n_yrpp_in22)
ch = collections.Counter(c for p in pool if h2(R[p['entry']]) and h4(R[p['entry']]) and h3b(R[p['entry']])
                         for c in R[p['entry']]['cats'])
print('三环行通道分布 =', dict(ch))
print('三环占 A 的比例 = %d/%d = %.2f%%' % (tot['three'], tot['A'], 100.0*tot['three']/tot['A']))
print('三环占 ③b 的比例 = %d/%d = %.2f%%' % (tot['three'], tot['r3b'], 100.0*tot['three']/tot['r3b']))
print()
print('若把 0045A640（待裁行）按 ②∧③b∧④livevt 全兑现：S08 proved 9+1=10 / 门槛 11 ⇒ 仍不达标')
print('newly_crossing 主口径 =', [d['sub'] for d in rows if d['ok_up'] and not d['ok_now']])
print('达标子系统 =', [d['sub'] for d in rows if d['ok_up']], '（now =',
      [d['sub'] for d in rows if d['ok_now']], '）')

json.dump(dict(rows=rows, tot=dict(tot), sensitivity=dict(
    r3b=tot['r3b'], r3bA=tot['r3bA'], r3bB=tot['r3bB'], r2R=tot['r2R'], r2=tot['r2'],
    AR=tot['AR'], A=tot['A'], threeR=tot['threeR'], three=tot['three'],
    yrpp_in_three=n_yrpp_in22, channels=dict(ch))),
    open(OUT/'work'/'final.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('\nwrote MATRIX3RING.tsv + EVIDENCE\\classification_rings.tsv + EVIDENCE\\three_ring_rows.tsv')
