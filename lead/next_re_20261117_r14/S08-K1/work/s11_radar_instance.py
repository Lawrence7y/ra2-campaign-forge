"""Find RadarClass object instance: dump radar ctor caller 0x63F6B4 and Sidebar radar init."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
import s08lib as L
b=L.Bin(); rows=L.load_atlas(); sw=L.load_sweep(os.path.join(os.path.dirname(__file__),'sweep.json'))
def who(va):
    e=L.atlas_find(rows,va)
    return ('%08X+%d sz=%d'%(e['entry'],va-e['entry'],e['size'])) if e else 'NOATLAS'
print('## radar ctor 0x652960 caller site 0x63F6B4 owner',who(0x63F6B4))
print(L.dump(b,0x63F680,0x60))
print()
print('## find global instances: what is [0x887300],[0x887324],[0xA83D4C] etc')
for va in [0x887300,0x887324,0x87F7E8,0xA83D4C]:
    print('  global %08X'%va)
print()
print('## radar surface size creation: scan for push imm followed by Surface Create near radar fns')
# dump 0x652A00..0x652B00 (rest of ctor)
print(L.dump(b,0x6529D0,0xC0))
