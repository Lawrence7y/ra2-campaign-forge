"""Settle per-frame entry: investigate 0x4F4480, 0x65381A owner, 0x47BBF0, 0x6D3660 chain."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
import s08lib as L
b=L.Bin(); rows=L.load_atlas(); sw=L.load_sweep(os.path.join(os.path.dirname(__file__),'sweep.json'))
def who(va):
    e=L.atlas_find(rows,va)
    return ('%08X+%d sz=%d ncall=%d'%(e['entry'],va-e['entry'],e['size'],e['n_callers'])) if e else 'NOATLAS'
def callers(va): return [hex(x) for x in sw['calls'].get(va,[])]
for va in [0x4F4480,0x4F8440,0x65381A,0x47BBF0,0x4801F0,0x6D3660,0x6D3D00,0x6D3716]:
    print('%08X who=%s callers=%s'%(va,who(va),callers(va)))
print()
print('## 0x4F4480 disasm (map update candidate)')
e=L.atlas_find(rows,0x4F4480)
print(L.dump(b,e['entry'],e['size']) if e else L.dump(b,0x4F4480,0x100))
print()
print('## 0x47BBF0 disasm')
e=L.atlas_find(rows,0x47BBF0)
print(L.dump(b,e['entry'],min(e['size'],0x100)) if e else L.dump(b,0x47BBF0,0x100))
print()
print('## 0x6D3660 disasm (contains 0x6D3716 cell draw call)')
e=L.atlas_find(rows,0x6D3660)
print(L.dump(b,e['entry'],min(e['size'],0x120)) if e else L.dump(b,0x6D3660,0x120))
