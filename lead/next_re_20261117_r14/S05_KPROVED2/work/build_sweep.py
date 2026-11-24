"""Build full .text instruction map (capstone skipdata=True) + all E8 direct call sites.
Cache to pickle for reuse. Card S05-KPROVED2."""
import sys, pickle, time
sys.path.insert(0, r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S05_KPROVED2\work")
from pe_helpers import *
from capstone import *
from capstone.x86 import *

MD = Cs(CS_ARCH_X86, CS_MODE_32)
MD.detail = True
MD.skipdata = True

CACHE = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S05_KPROVED2\work\text_insns.pkl"

def build():
    t0=time.time()
    code = bytes_at(TEXT_LO, TEXT_HI-TEXT_LO)
    insns = []          # list of (addr, size, mnemonic, opstr, bytes)
    for ins in MD.disasm(code, TEXT_LO):
        insns.append((ins.address, ins.size, ins.mnemonic, ins.op_str, bytes(ins.bytes)))
    print("insns:", len(insns), "time:", round(time.time()-t0,1),"s")
    return insns

try:
    insns = pickle.load(open(CACHE,'rb'))
    print("loaded cache", len(insns))
except Exception:
    insns = build()
    pickle.dump(insns, open(CACHE,'wb'))

# addr -> index
addr2i = {a:i for i,(a,sz,m,o,b) in enumerate(insns)}
# E8 direct call sites at instruction boundary: byte[0]==0xE8, target=a+5+rel32
call_sites = {}   # target -> list of site addrs
for a,sz,m,o,b in insns:
    if len(b)>=5 and b[0]==0xE8 and sz==5:
        import struct
        rel=struct.unpack('<i', b[1:5])[0]
        tgt=a+5+rel
        call_sites.setdefault(tgt,[]).append(a)
print("distinct E8 targets:", len(call_sites), "total E8@boundary:", sum(len(v) for v in call_sites.values()))

with open(r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S05_KPROVED2\work\call_sites.pkl",'wb') as f:
    pickle.dump({'call_sites':call_sites,'insns':insns,'addr2i':addr2i},f)

# quick stats
import struct
print("total E8 raw bytes:", sum(1 for a in range(TEXT_LO,TEXT_HI-4) if u8(a)==0xE8))
