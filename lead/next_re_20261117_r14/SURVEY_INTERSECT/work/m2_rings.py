"""m2: classify every UNION entry on the three rings, bytes only.

  ② = RTTI chain (vt[slot]==entry, [vt-4]=COL -> [COL+0xC]=TD -> TD+8 .?AV/.?AU)
      OR YRpp CALL/JMP_THIS line + >=2 absolute class addresses appearing bytewise in the body
  ④ = direct call (E8 boundary, site+5+rel32==entry, site OUTSIDE body, non-self-loop)
      OR livevt (constructor-installed live table, vt[slot]==entry, install site outside body,
                 install site != dispatch site, and that slot takes the SAME value across every
                 vtable ever installed on that global — the literal D-40 wording)
  ③b = R14_COMMON §8.6 条 3, four channels (b3b.py)

The row body [lo,hi) is a SELF-WRITTEN CFG closure; function_atlas.tsv is used only for the
domain test and for the extent-agreement self-check — never to bound a body.
"""
import sys, json, time, collections
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import core2 as C, b3b

t0 = time.time()
C.build_jt(); C.build_index()
print('index ready t=%.1f' % (time.time()-t0), flush=True)

U = json.loads((C.OUT/'work'/'union.json').read_text(encoding='utf-8'))
pool = json.loads((C.OUT/'work'/'pool.json').read_text(encoding='utf-8'))
met = json.loads((C.OUT/'work'/'metrics.json').read_text(encoding='utf-8'))
atlas_size = {p['entry']: p['atlas_size'] for p in pool}
for k, v in met['metrics'].items(): pass
ATLAS = C.ROOT/'lead'/'next_re_20261112_r10'/'W130_atlas'/'function_atlas.tsv'
ah = ATLAS.read_text(encoding='utf-8-sig').splitlines()[0].split('\t')
A_SIZE = {}
for l in ATLAS.read_text(encoding='utf-8-sig').splitlines()[1:]:
    if not l.strip(): continue
    q = l.split('\t'); q += ['']*(len(ah)-len(q))
    r = dict(zip(ah, q[:len(ah)]))
    try: A_SIZE[r['entry'].strip().upper().replace('0X', '')] = int(r['size'], 0)
    except Exception: pass

yr = json.loads((C.OUT/'work'/'yrpp.json').read_text(encoding='utf-8'))
BIND  = {int(k, 16): v for k, v in yr['bindings'].items()}
CADDR = {k: set(v) for k, v in yr['class_addrs'].items()}

_names = {p['entry']: p['name'] for p in pool}

def yrpp_conform(entry, addrs):
    bl = BIND.get(entry)
    if not bl: return None
    cls = bl[0][3]
    cand = CADDR.get(cls, set())
    if not cand:
        return dict(ok=False, cls=cls, n_cand=0, n_hit=0, why='class_has_no_absolute_addrs')
    hits = set()
    for a in addrs:
        o = a - C.TVA
        b = C.CODE[o:o+C.SZ[o]]
        for c in cand:
            if c.to_bytes(4, 'little') in b: hits.add(c)
    return dict(ok=(len(hits) >= 2 and len(addrs) > 0), cls=cls, n_cand=len(cand),
                n_hit=len(hits), hits=sorted(hits)[:8], n_ins=len(addrs),
                why=('ok' if len(hits) >= 2 else 'insufficient_byte_match'))

rows = []
t_err = 0
for n, ekey in enumerate(U['union']):
    e = int(ekey, 16)
    try:
        lo, hi, addrs, blocks = C.extent(e, cap=6000)
    except Exception as ex:
        rows.append(dict(entry=ekey, err=repr(ex))); t_err += 1; continue
    # ---- ② RTTI
    slots = C.ENTRY2SLOTS.get(e, [])
    has2_rtti = bool(slots)
    # ---- ② YRpp (only tested when RTTI absent; recorded either way)
    yc = yrpp_conform(e, addrs) if e in BIND else None
    has2_yrpp = bool(yc and yc['ok'])
    # ---- ④ direct: sites outside own body, non-self-loop
    dall = C.DIRECT.get(e, [])
    dout = [s for s in dall if not (lo <= s < hi) and s != e]
    # ---- ④ livevt: install site outside own body; slot unanimous across every vt on g
    lv_all = C.LIVEVT.get(e, [])
    lv_out = [x for x in lv_all if not (lo <= x[3] < hi)]
    lv_unanimous = [x for x in lv_out if C.slot_unanimous(x[0], x[1], x[2])]
    lv_single = [x for x in lv_out if C.global_single_vt(x[0])]
    # ㉓: an install inside an atexit-registered dtor is NOT a live vptr
    lv_live = [x for x in lv_unanimous if not C.in_atexit_dtor(x[3])]
    # ---- ③b
    try:
        r3 = b3b.classify(e, level='strict')
        cats = r3['cats']; cats_alt = r3['cats_alt']; cats_sent = r3['cats_sent']
        b1 = [list(h) for h in r3['b1']]; b2 = [list(map(str, h)) for h in r3['b2_main']]
        b3d = r3['b3']; b4d = r3['b4']
        span = r3['hi'] - r3['lo']; nins = r3['n_ins']; nblk = r3['n_blk']
    except Exception as ex:
        cats = cats_alt = cats_sent = []; b1 = b2 = []; b3d = {}; b4d = {'ok': False}
        span = hi - lo; nins = len(addrs); nblk = len(blocks)
    asz = A_SIZE.get(ekey)
    rows.append(dict(
        entry=ekey, e=e,
        has2_rtti=has2_rtti, has2_yrpp=has2_yrpp, yrpp=yc,
        rtti_cls=sorted({s[2] for s in slots})[:3],
        rtti_vt=(hex(slots[0][0]) if slots else ''),
        rtti_slot=(slots[0][1] if slots else ''),
        n_direct_all=len(dall), n_direct_out=len(dout), direct_out=dout[:6],
        n_livevt_all=len(lv_all), n_livevt_out=len(lv_out),
        n_livevt_unanimous=len(lv_unanimous), n_livevt_single=len(lv_single),
        n_livevt_live=len(lv_live),
        livevt_unanimous=lv_unanimous[:4], livevt_single=lv_single[:4], livevt_live=lv_live[:4],
        cats=cats, cats_alt=cats_alt, cats_sent=cats_sent,
        b1=b1, b2=b2, b3={k: b3d.get(k) for k in ('ok','n_ctor','n_vt','size','max_disp','ctor','vt')},
        b4={k: b4d.get(k) for k in ('ok','head','back','n','why','read','test','write','write_stk','progress','bounds','bound')},
        lo=r3.get('lo', lo) if 'r3' in dir() else lo, hi=hi, span=span, n_ins=nins, n_blk=nblk,
        atlas_size=asz, ext_match=(span == asz) if asz is not None else None))
    if (n+1) % 500 == 0:
        print('%d/%d t=%.1f' % (n+1, len(U['union']), time.time()-t0), flush=True)

(C.OUT/'work'/'rings.json').write_text(json.dumps(rows, ensure_ascii=False, default=int), encoding='utf-8')
ok = [r for r in rows if 'err' not in r]
print('rows', len(rows), 'errors', t_err, 't=%.1f' % (time.time()-t0))
print('has2_rtti', sum(r['has2_rtti'] for r in ok), 'has2_yrpp', sum(r['has2_yrpp'] for r in ok))
print('④ direct_out', sum(r['n_direct_out'] > 0 for r in ok),
      '④ livevt_unanimous', sum(r['n_livevt_unanimous'] > 0 for r in ok),
      '④ livevt_single', sum(r['n_livevt_single'] > 0 for r in ok))
print('③b', sum(1 for r in ok if r['cats']))
print('extent==atlas_size', sum(1 for r in ok if r['ext_match']), '/', sum(1 for r in ok if r['ext_match'] is not None))
print('channel histogram', collections.Counter(c for r in ok for c in r['cats']))
