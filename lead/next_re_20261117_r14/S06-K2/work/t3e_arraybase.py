"""T3e: examine candidate MapClass array-base write sites (singleton base)."""
from pehelp import *
OUT=r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S06-K2\EVIDENCE\t3e_arraybase_writes.txt"
_l=[]
def p(s=''):
    print(s); _l.append(str(s))
for site in (0x58fde5,0x649692,0x6fa145,0x749428):
    p(f"\n===== around write {site:#x} =====")
    for ins in disasm(site-0x30,0x50):
        if ins.id==0: continue
        mark=' <<<' if ins.address==site else ''
        p(f"  {ins.address:08X}: {ins.bytes.hex():<18} {ins.mnemonic} {ins.op_str}{mark}")
with open(OUT,'w') as f: f.write('\n'.join(_l)+'\n')
p(f"\n[saved] {OUT}")
