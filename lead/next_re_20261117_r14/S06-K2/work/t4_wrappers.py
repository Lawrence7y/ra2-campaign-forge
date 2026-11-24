"""T4: dump attach/detach wrappers (0x5683c0/0x5687f0) and 0x47C620 to determine list-head selection."""
from pehelp import *
OUT=r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S06-K2\EVIDENCE\t4_wrappers.txt"
_l=[]
def p(s=''):
    print(s); _l.append(str(s))
ATLAS=r"D:\Project\ra2-campaign-forge\lead\next_re_20261112_r10\W130_atlas\function_atlas.tsv"
atlas={}
with open(ATLAS) as f:
    next(f)
    for ln in f:
        q=ln.split('\t')
        if len(q)>=2:
            try: atlas[int(q[0],16)]=int(q[1])
            except: pass
for name,va,n in [('attach 0x5683c0',0x5683c0,0x440),('detach 0x5687f0',0x5687f0,0x3b0),('0x47C620',0x47c620,0x200)]:
    sz=atlas.get(va,n)
    p(f"\n===== {name} (atlas size={sz}) =====")
    for ins in disasm(va,min(n,sz if sz else n)):
        if ins.id==0: continue
        mark=''
        if any(x in ins.op_str for x in ('0xe4','0xe8','0x8c','0x30','0x47e8a0','0x47ea90','0x47c620')): mark=' <<<'
        p(f"  {ins.address:08X}: {ins.bytes.hex():<18} {ins.mnemonic} {ins.op_str}{mark}")
with open(OUT,'w') as f: f.write('\n'.join(_l)+'\n')
p(f"\n[saved] {OUT}")
