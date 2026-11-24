"""Inspect reveal caller 0x653810 and spy-sat chain; list owners of RevealArea2 callers."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
import s08lib as L
b=L.Bin(); rows=L.load_atlas(); sw=L.load_sweep(os.path.join(os.path.dirname(__file__),'sweep.json'))
def who(va):
    e=L.atlas_find(rows,va)
    return ('%08X+%d sz=%d'%(e['entry'],va-e['entry'],e['size'])) if e else 'NOATLAS'
def callers(va): return [hex(x) for x in sw['calls'].get(va,[])]
print('## reveal 0x4A9890 caller 0x65381A owner',who(0x65381A))
print(L.dump(b,0x653810,0x30))
print('## callers of 0x653810:',callers(0x653810))
print()
print('## RevealArea2 0x5678E0 callers -> owner functions')
for c in sw['calls'].get(0x5678E0,[]):
    print('  site %08X owner %s'%(c,who(c)))
print()
print('## UpdateSpySat 0x508F60 caller 0x4F850C owner',who(0x4F850C))
print(L.dump(b,0x4F8500,0x30))
print('## callers of function owning 0x4F850C')
e=L.atlas_find(rows,0x4F850C)
if e: print(' owner',who(e['entry']),'callers',callers(e['entry']))
