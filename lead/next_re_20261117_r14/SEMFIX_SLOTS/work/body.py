"""Print trimmed function body (entry -> first ret cluster) for a list of entries."""
import sys
import pefile
from capstone import Cs, CS_ARCH_X86, CS_MODE_32
sys.stdout.reconfigure(encoding="utf-8")
EXE=r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe"
pe=pefile.PE(EXE,fast_load=True); IB=pe.OPTIONAL_HEADER.ImageBase
md=Cs(CS_ARCH_X86,CS_MODE_32); md.skipdata=True
with open(EXE,"rb") as f: blob=f.read()
def off(va): return pe.get_offset_from_rva(va-IB)
entries=sys.argv[1:]
for e in entries:
    va=int(e,16); o=off(va); data=blob[o:o+0x1000]
    insns=list(md.disasm(data,va))
    rets=[i for i,x in enumerate(insns) if x.mnemonic in ("ret","retf")]
    if rets:
        endi=rets[0]
        for r in rets:
            if r-endi<=8: endi=r
            else: break
        endi=min(endi+1,len(insns))
    else: endi=min(80,len(insns))
    print(f"\n===== {e} body {endi} insns span 0x{insns[endi-1].address-va:X} =====")
    for ins in insns[:endi]:
        print(f"+0x{ins.address-va:04X} {ins.mnemonic:<7} {ins.op_str}")
