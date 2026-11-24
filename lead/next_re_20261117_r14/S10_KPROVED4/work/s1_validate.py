"""s1: validate core RTTI + call sweep against known-good prior-card facts."""
import sys, json, os
sys.path.insert(0, os.path.dirname(__file__))
from core import Bin, build_rtti, holding_tables, attribute_base, cls_short, sweep_calls

b = Bin()
print('sections', [(s['name'], hex(s['va']), s['vsize']) for s in b.sections])
r = build_rtti(b)
print('n_cols', len(r['cols']), 'n_vtables', len(r['vtables']),
      'n_slots', sum(len(t['slots']) for t in r['vtables']))
# distribution of strength
from collections import Counter
print('strength', Counter(t['strength'] for t in r['vtables']))

known = {
    0x004D85D0: '2 tables slot99 (Aircraft+Foot) => FootClass',
    0x004DF040: '3 tables slot330 (Foot+Infantry+Unit) => FootClass',
    0x00702D40: '5 tables slot56 => TechnoClass',
    0x00706640: '6 tables slot273 => TechnoClass',
    0x004D74E0: '1 table slot81 => FootClass',
}
for e, expect in known.items():
    hs = holding_tables(b, r, e)
    cls, note = attribute_base(hs)
    print(f'{e:08X} expect[{expect}] n={len(hs)} cls={cls} note={note}')
    for h in hs:
        print(f'   vt={h["vt"]:#x} slot={h["slot"]} col={h["col"]:#x} td={h["td"]:#x} name={h["name"]} str={h["strength"]}')

sw = sweep_calls(b)
print('sweep n_ins', sw['n_ins'], 'n_e8_bytes', sw['n_e8'], 'n_boundary_calls', len(sw['calls']))
# check known direct sites
sites = {0x0051A9FC: 0x004D85D0, 0x0073A4FB: 0x004D85D0, 0x0073B0A0: 0x004D85D0,
         0x00417C4E: 0x004D74E0}
for s, e in sites.items():
    print(f'site {s:#x} boundary={s in sw["boundaries"]} target={sw["calls"].get(s):#x} expect={e:#x}')
