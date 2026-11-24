"""Dump CellClass ctor / dtor / linkadd / linkdel / ore / getcenter disassembly for semantics."""
from pehelp import *
OUT=r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S06-K2\EVIDENCE\cell_methods.txt"
_lines=[]
def p(s=''):
    print(s); _lines.append(str(s))
for name,va,n in [('ctor',0x47bbf0,0x260),('dtor',0x47bb60,0x90),
                  ('ore(0x485020)',0x485020,0x90),('getcenter(0x47ff80)',0x47ff80,0x40),
                  ('linkadd(0x47e8a0)',0x47e8a0,0x100),('linkdel(0x47ea90)',0x47ea90,0x100)]:
    p(f"\n===== {name} @ {va:#x} =====")
    for ins in disasm(va,n):
        if ins.id==0: continue
        p(f"  {ins.address:08X}: {ins.bytes.hex():<20} {ins.mnemonic} {ins.op_str}")
with open(OUT,'w') as f: f.write('\n'.join(_lines)+'\n')
p(f"\n[saved] {OUT}")
