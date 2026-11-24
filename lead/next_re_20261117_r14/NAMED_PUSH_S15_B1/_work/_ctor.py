import sys
sys.path.insert(0, r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\NAMED_PUSH_S15_B1\_work")
import recore as R
from capstone import Cs, CS_ARCH_X86, CS_MODE_32
md = Cs(CS_ARCH_X86, CS_MODE_32); md.skipdata=True; md.detail=True
for e in ("00725FA0","00726C80","0071E6A0","0071F8C0","006DD000","006E4DE0","006E6410"):
    ea=int(e,16); info=R.ATLAS.get(e); size=info["size"] if info else 0x40
    print("=== %s size=%s ===" % (e, size))
    for i in list(md.disasm(R.read_va(ea,size), ea))[:9]:
        print("  %08X %-8s %s" % (i.address, i.mnemonic, i.op_str))
