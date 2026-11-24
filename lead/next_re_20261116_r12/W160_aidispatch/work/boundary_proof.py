"""Boundary validation from atlas entries/known boundaries for disputed sites.
For sites outside any atlas entry, sweep forward from all atlas entries in the
preceding 8 KiB window that are <= site and see if linear decode hits exactly.
"""
import os, bisect, json
from capstone import Cs, CS_ARCH_X86, CS_MODE_32
import pefile
R=r"D:\Project\ra2-campaign-forge"
BIN=os.path.join(R,'ra2youli','gamemd.exe')
EV=os.path.join(R,'lead','next_re_20261116_r12','W160_aidispatch','EVIDENCE')
pe=pefile.PE(BIN,fast_load=True)
ts=next(s for s in pe.sections if s.Name.rstrip(b'\0')==b'.text')
base=0x400000+ts.VirtualAddress; raw=ts.PointerToRawData
data=open(BIN,'rb').read(); blob=data[raw:raw+ts.SizeOfRawData]
atlas=[]
with open(os.path.join(R,'lead','next_re_20261112_r10','W130_atlas','function_atlas.tsv'),encoding='utf-8') as f:
    next(f)
    for ln in f:
        p=ln.split()
        if len(p)>=2: atlas.append((int(p[0],16),int(p[1])))
atlas.sort(); starts=[a for a,s in atlas]
md=Cs(CS_ARCH_X86,CS_MODE_32); md.skipdata=True
for target in [0x617641,0x61CC5C,0x785132,0x7852CF,0x55B8F0]:
    print(f'\n=== {target:08X} ===')
    # candidate starts: nearest entries before target (up to 12)
    idx=bisect.bisect_right(starts,target)-1
    cands=starts[max(0,idx-11):idx+1]
    found=[]
    for st in cands:
        for ins in md.disasm(blob[st-base:target-base+8],st):
            if ins.address==target:
                found.append((st,ins.mnemonic,ins.op_str,ins.bytes.hex()))
                break
    for f in found: print('  from',hex(f[0]),f[1],f[2],f[3])
    print('  boundary_from_entry_linear=',bool(found))
