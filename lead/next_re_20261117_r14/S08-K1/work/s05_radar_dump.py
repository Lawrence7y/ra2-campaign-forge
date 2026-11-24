"""Dump radar functions + trace this/ecx, and frame-loop chain to fog writers."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
import s08lib as L
b=L.Bin(); rows=L.load_atlas(); sw=L.load_sweep(os.path.join(os.path.dirname(__file__),'sweep.json'))
# radar functions from clues
R=[0x653100,0x656EC0,0x655C50,0x655250,0x657CE0,0x657180,0x65719A,0x6A6C30,0x63FB20]
for va in R:
    e=L.atlas_find(rows,va)
    print('='*90)
    print('RADAR VA %08X atlas=%s callers=%s'%(
        va, ('%08X/%d'%(e['entry'],e['size'])) if e else 'NONE',
        [hex(x) for x in sw['calls'].get(va,[])[:20]]))
    if e:
        print(L.dump(b,e['entry'],max(e['size'],64)))
    else:
        print(L.dump(b,va,0x60))
