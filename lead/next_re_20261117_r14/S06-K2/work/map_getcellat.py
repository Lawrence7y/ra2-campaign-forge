"""Dump MapClass GetCellAt (0x5657A0) and TryGetCellAt + related to show cell-array indexing/stride."""
from pehelp import *
import struct
OUT=r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S06-K2\EVIDENCE\map_getcellat.txt"
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
for name,va in [('GetCellAt(0x5657A0)',0x5657A0)]:
    sz=atlas.get(va,0x200)
    p(f"===== {name} size(atlas)={sz} =====")
    for ins in disasm(va,sz):
        if ins.id==0: continue
        p(f"  {ins.address:08X}: {ins.bytes.hex():<18} {ins.mnemonic} {ins.op_str}")
# Also scan xrefs to 0x87f924 (pointer field) with base+disp forms
p("\n===== xrefs to singleton 0x87f7E8 / field 0x87f924 (raw dword scan) =====")
for target in (0x87f7e8,0x87f924,0x886fa0,0x886fa4):
    hits=[]
    for s in SECTIONS:
        if s[4]!='.text': continue
        data=pe.get_data(s[2],s[3])
        pat=struct.pack('<I',target)
        i=0
        while True:
            j=data.find(pat,i)
            if j<0: break
            hits.append(s[0]+j); i=j+1
    p(f"  target {target:#x}: {len(hits)} raw dword refs, first={[hex(x) for x in hits[:10]]}")
with open(OUT,'w') as f: f.write('\n'.join(_l)+'\n')
p(f"\n[saved] {OUT}")
