"""T3d: dump map-array init region in fn 0x565c10 (singleton load + +0x13c writes)."""
from pehelp import *
OUT=r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S06-K2\EVIDENCE\t3d_map_init.txt"
_l=[]
def p(s=''):
    print(s); _l.append(str(s))
for name,start,n in [('fn0x565c10 around 0x566030',0x566030,0xA0),
                     ('fn0x565c10 around 0x566850',0x566850,0x80),
                     ('singleton-load 0x5670c0 region',0x5670c0,0x80)]:
    p(f"\n===== {name} =====")
    for ins in disasm(start,n):
        if ins.id==0: continue
        mark=''
        if any(x in ins.op_str for x in ('0x13c','0x14c','0x150','0x154','0x87f7e8','0x87f924')): mark=' <<<'
        p(f"  {ins.address:08X}: {ins.bytes.hex():<18} {ins.mnemonic} {ins.op_str}{mark}")
with open(OUT,'w') as f: f.write('\n'.join(_l)+'\n')
p(f"\n[saved] {OUT}")
