"""Dump 0x487950 (CellClass::IsShrouded), 0x6D8700 (vision->shroud/fog compute), radar DrawCell ctx."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
import s08lib as L
b=L.Bin(); rows=L.load_atlas()
for va,mx in [(0x487950,0x60),(0x6D8700,0x3E0),(0x655d40,0x60),(0x5678E0,0x4C0)]:
    e=L.atlas_find(rows,va)
    print('='*90)
    print('VA %08X atlas=%s'%(va, ('%08X/%d'%(e['entry'],e['size'])) if e else 'NONE'))
    print(L.dump(b, va if va!=0x487950 else 0x487950, mx))
