
import sys
sys.stdout.reconfigure(encoding='utf-8')
import k5_lib as K
funcs=[(0x483710,112,'00483710 GrowIfAllowed (K4 proven)'),
       (0x483780,340,'00483780 TO PROVE'),
       (0x4838E0,272,'004838E0 candidate'),
       (0x4839F0,536,'004839F0 CellClass::slot5 candidate'),
       (0x5FDD20,190,'5FDD20 callee'),
       (0x487190,1181,'487190 IncreaseTiberium callee')]
lines=[]
for va,sz,name in funcs:
    lines.append("="*90)
    lines.append(f"FUNC {name} @ 0x{va:08X} size={sz}")
    lines.append("="*90)
    for i in K.dis(va,sz):
        lines.append(K.fmt(i))
    lines.append("")
open(r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S06_K5\work\disasm_region.txt','w',encoding='utf-8').write("\n".join(lines))
print("\n".join(lines[:220]))
print("... (full in work/disasm_region.txt)")
