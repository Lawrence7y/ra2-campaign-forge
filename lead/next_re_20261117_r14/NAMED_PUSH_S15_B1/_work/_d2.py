import sys
sys.path.insert(0, r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\NAMED_PUSH_S15_B1\_work")
import recore as R
from capstone import Cs, CS_ARCH_X86, CS_MODE_32
md = Cs(CS_ARCH_X86, CS_MODE_32); md.skipdata=True
for e in ("00726950",):
    ea=int(e,16); size=R.ATLAS[e]["size"]
    for i in md.disasm(R.read_va(ea,size), ea):
        print("%08X  %-22s %-8s %s" % (i.address, " ".join("%02X"%b for b in i.bytes), i.mnemonic, i.op_str))
