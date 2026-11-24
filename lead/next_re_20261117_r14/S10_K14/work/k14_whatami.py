from k14_image import Image, ATL
import capstone.x86
img=Image()
out=[]

def atlas_size(va):
    with open(ATL,"r",encoding="utf-8",errors="replace") as f:
        for ln in f:
            c=ln.rstrip("\r\n").split("\t")
            if c and c[0].lower()==f"{va:08x}":
                return int(c[1])
    return None

out.append("WHATAMI SLOT 0x2C TARGETS:")
for name,va in [("FootClass",0x004C9150),("AircraftClass",0x0041C180),("BuildingClass",0x00459EC0),("InfantryClass",0x00523340),("UnitClass",0x00746E20)]:
    ins=list(img.md.disasm(img.read(va,0x20),va,count=6))
    txt=" | ".join(f"{i.address:08X}: {i.mnemonic} {i.op_str}" for i in ins)
    out.append(f"{name:<14} {va:08X}  {txt}")

out.append("")
out.append("SLOT 0x18C OVERRIDE CALL SITES INTO 004D85D0:")
for name,va in [("InfantryClass",0x00519630),("UnitClass",0x00739EC0)]:
    size=atlas_size(va)
    ins=list(img.md.disasm(img.read(va,size),va))
    hits=[k for k,i in enumerate(ins) if i.mnemonic=="call" and i.operands and i.operands[0].type==capstone.x86.X86_OP_IMM and i.operands[0].imm==0x4D85D0]
    out.append(f"{name} {va:08X} atlas_size={size} call_hits={[hex(ins[k].address) for k in hits]}")
    for k in hits:
        for j in range(max(0,k-8),min(len(ins),k+3)):
            out.append(f"  {ins[j].address:08X}  {ins[j].mnemonic:<8} {ins[j].op_str}")
        out.append("")

res="\n".join(out)
open(r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S10_K14\EVIDENCE\WHATAMI_OVERRIDES.txt","w",encoding="utf-8").write(res+"\n")
print(res)
