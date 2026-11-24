import pefile, capstone, os
EXE=r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe"
OUT=r"D:\Project\ra2-campaign-forge\lead\next_re_20261116_r13\W170_mode2\EVIDENCE"
pe=pefile.PE(EXE,fast_load=True); ib=pe.OPTIONAL_HEADER.ImageBase
secs=[]
for s in pe.sections:
    secs.append((s.Name.decode(errors="replace").rstrip("\x00"),ib+s.VirtualAddress,s.PointerToRawData,s.SizeOfRawData))
def rd(va,n):
    for nm,v,r,rs in secs:
        if v<=va and va+n<=v+rs:
            return pe.__data__[r+(va-v):r+(va-v)+n]
    raise ValueError(hex(va))
m=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32); m.detail=True; m.skipdata=True
lines=[]
for va,n,label in [(0x565730,0x100,"MapClass helper 0x565730 (called by slot+0x1BC)"),
                   (0x70E380,0x60,"0x70E380 (called by 0x70E360)"),
                   (0x70E4B0,0x60,"0x70E4B0 (called by 0x70E360)")]:
    lines.append("=== %s ==="%label)
    for ins in m.disasm(rd(va,n),va):
        if ins.id==0: continue
        lines.append("  %08X  %-8s %s"%(ins.address,ins.mnemonic,ins.op_str))
    lines.append("")
open(os.path.join(OUT,"Q1_helpers.txt"),"w",encoding="utf-8").write("\n".join(lines)+"\n")
print("\n".join(lines))
