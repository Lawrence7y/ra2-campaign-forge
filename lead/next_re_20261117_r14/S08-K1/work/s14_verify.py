"""FINAL VERIFY of core numbers via independent capstone disasm + sweep."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
import s08lib as L
b=L.Bin(); rows=L.load_atlas(); sw=L.load_sweep(os.path.join(os.path.dirname(__file__),'sweep.json'))
def callers(va): return sw['calls'].get(va,[])
print('V1 cell predicate bounds: E01 already shows idx<0x40000 = %d = 512*512=%s'%(0x40000,512*512))
print('V2 cell array ptr base 0x87F924 stride 4, MapClass singleton 0x87F7E8 (+0x13C=0x%X)'%(0x87F7E8+0x13C))
for va,label in [(0x586360,'IsLocationShrouded'),(0x5864A0,'IsLocationFogged'),(0x5865E0,'stub IsCellShrouded'),
                 (0x487950,'CellClass::IsShrouded'),(0x4801F0,'CellClass::Draw'),(0x47EFE0,'shroud blit'),
                 (0x655C50,'Radar::DrawCell'),(0x656EC0,'Radar::DrawMap'),(0x508F60,'UpdateSpySat'),
                 (0x5678E0,'RevealArea2'),(0x6D8700,'cell shroud compute'),(0x4A9890,'RevealArea0')]:
    print('V3 callers(%08X %s) n=%d'%(va,label,len(callers(va))))
print()
print('V4 per-frame chain disasm 0x55E240..0x55E290 (aligned):')
print(L.dump(b,0x55E240,0x50))
