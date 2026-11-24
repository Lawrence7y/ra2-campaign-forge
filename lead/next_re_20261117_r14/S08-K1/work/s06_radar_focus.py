"""Focused radar analysis: DrawCell callers, dirty-check gates, this-source, buffer writes."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
import s08lib as L
import capstone
b=L.Bin(); rows=L.load_atlas(); sw=L.load_sweep(os.path.join(os.path.dirname(__file__),'sweep.json'))
def callers(va): return [hex(x) for x in sw['calls'].get(va,[])]
print('## caller lists (channel B, full .text skipdata)')
for va in [0x655C50,0x656EC0,0x655250,0x653100,0x657CE0,0x431800,0x6A6C30,0x63FB20,0x5864A0]:
    print('%08X n=%d %s'%(va,len(callers(va)),callers(va)))
print()
print('## ecx/this source: dump 0x63FD70..0x63FDC0 (caller of RadarClass::Draw_It 0x653100)')
print(L.dump(b,0x63FD70,0x60))
print()
print('## 0x656EC0 dirty gates window 0x657150..0x657260')
print(L.dump(b,0x657150,0x120))
print()
print('## 0x656EC0 render loops window 0x657480..0x657560')
print(L.dump(b,0x657480,0xE0))
print()
print('## full-map rebuild 0x657CE0 window 0x657D40..0x657DA0')
print(L.dump(b,0x657D40,0x70))
