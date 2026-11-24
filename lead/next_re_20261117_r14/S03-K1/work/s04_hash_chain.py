"""S03-K1 step4: hash function, MIX table base, call chain, allocation sizes, INI convergence.
"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from re_lib import *

b=Bin(); E=os.path.join(os.path.dirname(__file__),'..','EVIDENCE'); out=[]

# 1) CRC32 hash function 0x4A1DE0 full
seg=dump(b,0x4A1DE0,0x4A1EE0)
out.append("===== CRC32 hash 0x4A1DE0 =====\n"+seg)
# look for immediate polynomial constants
for va in range(0x4A1DE0,0x4A1EE0):
    pass

# 2) hash table at 0x81F7B4: dump first 32 bytes
raw=b.read(0x81F7B4,64)
out.append("\n===== crc table @0x81F7B4 first 64 bytes =====")
out.append(" ".join("%02X"%x for x in raw))
out.append("u32[0..7]: "+" ".join("%08X"%b.u32(0x81F7B4+4*i) for i in range(8)))

# 3) strupr 0x7DCFC4
out.append("\n===== strupr 0x7DCFC4 =====\n"+dump(b,0x7DCFC4,0x7DCFE0))

# 4) call chain: callers of Get_File 0x473D10, Find 0x5B4430, hash 0x4A1DE0, INIClass::Load 0x4741F0
calls,jmps,meta=scan_calls(b)
out.append("\n===== scan meta ====="); out.append(str(meta))
for tgt in (0x473D10,0x5B4430,0x4A1DE0,0x4741F0,0x7DCFC4,0x4739F0,0x5B3C20):
    sites=calls.get(tgt,[])
    out.append(f"\ncallers of {tgt:08X}: {len(sites)}")
    out.append("  "+" ".join(f"{s:08X}" for s in sites[:80]))

# 5) allocation size: callers of MixFileClass ctor 0x5B3C20 and CCFileClass ctor 0x4739F0
for tgt in (0x5B3C20,0x4739F0):
    sites=calls.get(tgt,[])
    out.append(f"\n===== new-size context for ctor {tgt:08X} ({len(sites)} sites) =====")
    for s in sites[:40]:
        out.append(f"--- context before call@ {s:08X} ---")
        out.append(dump(b,max(0x401000,s-0x30),s+0x10))

open(os.path.join(E,'E05_hash_chain_alloc.txt'),'w',encoding='utf-8').write("\n".join(out))
print("\n".join(out[:200]))
print("...full written to E05_hash_chain_alloc.txt")
