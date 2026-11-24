"""Exploratory: dump key fog/shroud predicate functions + atlas entries + callers."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
import s08lib as L

b=L.Bin(); rows=L.load_atlas(); sw=L.load_sweep(os.path.join(os.path.dirname(__file__),'sweep.json'))

TARGETS = [0x586360, 0x5864A0, 0x586540, 0x5865E0, 0x487950, 0x4A98E6,
           0x5678E0, 0x487690, 0x508F60, 0x577D90, 0x6D8700]
for va in TARGETS:
    e=L.atlas_find(rows,va)
    print('='*90)
    if e:
        print('TARGET %08X  ATLAS entry=%08X size=%d n_callers=%d n_callees=%d offset=%d'%(
            va,e['entry'],e['size'],e['n_callers'],e['n_callees'],va-e['entry']))
        start=e['entry']; mx=max(e['size'],64)
    else:
        print('TARGET %08X  NOT IN ATLAS'%va)
        start=va; mx=0x80
    print(L.dump(b,start,mx))
    callers=sw['calls'].get(va,[])
    print('-- direct call sites (channel B): %d %s'%(len(callers),[hex(x) for x in callers[:40]]))
