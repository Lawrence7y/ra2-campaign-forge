"""s3: classify every pool row (③b①..④ / ③a) from bytes only."""
import sys, json, time, collections
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import core as C, b3

t0 = time.time()
C.build_jt()
print('jtables', len(C.TGT_JT), 't=%.1f' % (time.time()-t0), flush=True)

pool = json.loads((C.OUT/'work'/'pool.json').read_text(encoding='utf-8'))
rows = []
for n, p in enumerate(pool):
    e = int(p['entry'], 16)
    try:
        r = b3.classify(e, level='strict')
        ra = b3.classify(e, level='loose')
    except Exception as ex:
        rows.append(dict(entry=p['entry'], sub=p['sub'], name=p['name'], err=repr(ex)))
        continue
    rows.append(dict(entry=p['entry'], sub=p['sub'], name=p['name'],
                     atlas_size=p['atlas_size'],
                     lo=r['lo'], hi=r['hi'], span=r['hi']-r['lo'],
                     n_ins=r['n_ins'], n_blk=r['n_blk'],
                     cats=r['cats'], verdict=r['verdict'],
                     cats_alt=ra['cats_alt'], verdict_alt=ra['verdict_alt'],
                     cats_sent=r['cats_sent'], verdict_sent=r['verdict_sent'],
                     b1=[list(h) for h in r['b1']], b1_alt=[list(h) for h in r['b1_alt']],
                     b2=[list(map(str, h)) for h in r['b2_main']],
                     b2_sent=[list(map(str, h)) for h in r['b2_sent']],
                     b3=r['b3'], b4={k: v for k, v in r['b4'].items() if k in
                                     ('ok','head','back','n','why','read','test','write','write_stk','progress','bounds','ind','bound')},
                     ext_match=(r['hi']-r['lo']) == p['atlas_size']))
    if (n+1) % 500 == 0:
        print('%d/%d t=%.1f' % (n+1, len(pool), time.time()-t0), flush=True)

(C.OUT/'work'/'rows3b.json').write_text(json.dumps(rows, ensure_ascii=False), encoding='utf-8')
print('rows', len(rows), 'errors', sum(1 for r in rows if 'err' in r), 't=%.1f' % (time.time()-t0))
print('verdict', collections.Counter(r.get('verdict') for r in rows))
print('cats(strict, row counted in each satisfied channel):',
      collections.Counter(c for r in rows for c in r.get('cats', [])))
print('no-instruction rows', sum(1 for r in rows if r.get('n_ins') == 0))
print('extent==atlas_size', sum(1 for r in rows if r.get('ext_match')), '/', len(rows))
