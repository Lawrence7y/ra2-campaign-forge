"""Trace: (a) per-frame cell draw loop containing 0x6D3716 and its callers;
(b) CellClass::Draw 0x4801F0 callers; (c) RadarClass object this source; (d) radar ctor."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
import s08lib as L
b=L.Bin(); rows=L.load_atlas(); sw=L.load_sweep(os.path.join(os.path.dirname(__file__),'sweep.json'))
def who(va):
    e=L.atlas_find(rows,va)
    return ('%08X+%d ncall=%d'%(e['entry'],va-e['entry'],e['n_callers'])) if e else 'NOATLAS'
def callers(va): return [hex(x) for x in sw['calls'].get(va,[])]
print('## (a) function containing cell-draw call 0x6D3716')
print('  0x6D3716 belongs to',who(0x6D3716))
print('## (b) CellClass::Draw 0x4801F0 callers:',callers(0x4801F0))
print('   0x4801F0 belongs to',who(0x4801F0))
print('## 0x6D8700 callers:',callers(0x6D8700))
print('## 0x508F60 UpdateSpySat callers:',callers(0x508F60))
print('## 0x4A9890 callers:',callers(0x4A9890))
print()
print('## (c) function containing 0x63FDAC (radar Draw caller)')
print('  0x63FDAC belongs to',who(0x63FDAC))
print('  dump 0x63FB20 entry:')
print(L.dump(b,0x63FB20,0x50))
print()
print('## radar ctor 0x652960')
print('  belongs',who(0x652960),'callers',callers(0x652960))
print(L.dump(b,0x652960,0x80))
print()
print('## frame loop: 0x55E160 belongs',who(0x55E160))
print('  dump around 0x55E260..0x55E290')
print(L.dump(b,0x55E260,0x30))
