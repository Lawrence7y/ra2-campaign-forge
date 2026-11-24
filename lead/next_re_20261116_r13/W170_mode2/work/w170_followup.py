"""Targeted follow-ups: full disasm of 0x5F6960; mode2 call context inside 0x43FB20; reconcile +0x81 channels."""
import struct, pefile, capstone, os, re
EXE=r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe"
OUT=r"D:\Project\ra2-campaign-forge\lead\next_re_20261116_r13\W170_mode2\EVIDENCE"
LOG=os.path.join(OUT,"ghidra_W170Dump.log")

class Bin:
    def __init__(self):
        self.pe=pefile.PE(EXE,fast_load=True); self.ib=self.pe.OPTIONAL_HEADER.ImageBase; self.sections=[]
        for s in self.pe.sections:
            n=s.Name.decode(errors="replace").rstrip("\x00")
            self.sections.append(dict(name=n,va=self.ib+s.VirtualAddress,raw=s.PointerToRawData,rawsize=s.SizeOfRawData))
    def sec(self,n):
        for s in self.sections:
            if s["name"]==n:return s
        raise KeyError(n)
    def read(self,va,n):
        for s in self.sections:
            if s["va"]<=va and va+n<=s["va"]+s["rawsize"]:
                return self.pe.__data__[s["raw"]+(va-s["va"]):s["raw"]+(va-s["va"])+n]
        raise ValueError("%08X"%va)
def md():
    m=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32); m.detail=True; m.skipdata=True; return m
def dis(b,start,n,maxins=200):
    m=md(); out=[]
    for ins in m.disasm(b.read(start,n),start):
        if ins.id==0:continue
        out.append("  %08X  %-8s %s"%(ins.address,ins.mnemonic,ins.op_str))
        if len(out)>=maxins:break
    return out

b=Bin()
lines=[]
lines.append("=== full disasm 0x5F6960 (slot +0x1BC callee, 87 B) ===")
lines+=dis(b,0x5F6960,87)
lines.append("")
lines.append("=== 0x43FB20 around mode2 self-call at 0x43FDEB ===")
lines+=dis(b,0x43FDC0,0x60)
lines.append("")
open(os.path.join(OUT,"Q1_followup_disasm.txt"),"w",encoding="utf-8").write("\n".join(lines)+"\n")
print("\n".join(lines))

# reconcile channel A/B
A=set()
for line in open(os.path.join(OUT,"Q2_plus81_census.txt"),encoding="utf-8"):
    mm=re.search(r"^\s+([0-9A-F]{8})\s",line)
    if mm: A.add(int(mm.group(1),16))
B=set(); Bdetail={}
inB=False
for line in open(LOG,encoding="utf-8",errors="replace"):
    if "CHANNEL B" in line: inB=True; continue
    if not inB: continue
    if "obj hits" in line or "stack hits" in line: continue
    mm=re.search(r">\s+([0-9a-f]{8})\s+(.*?)\s+([WR])\s+([0-9a-f]+)\s",line)
    if mm:
        va=int(mm.group(1),16); B.add(va)
        Bdetail[va]=(mm.group(2).strip(),mm.group(3))
onlyA=sorted(A-B); onlyB=sorted(B-A); both=sorted(A&B)
rep=[]
rep.append("=== A/B reconciliation: byte[+0x81] object hits ===")
rep.append("Channel A (capstone full .text, skipdata=True): %d hits"%len(A))
rep.append("Channel B (Ghidra defined instructions): %d hits"%len(B))
rep.append("both: %d   onlyA: %d   onlyB: %d"%(len(both),len(onlyA),len(onlyB)))
rep.append("")
rep.append("--- onlyA (Ghidra not defined; atlas-gap effect) ---")
for va in onlyA: rep.append("  %08X"%va)
rep.append("")
rep.append("--- onlyB ---")
for va in onlyB: rep.append("  %08X"%va)
open(os.path.join(OUT,"Q2_AB_reconcile.txt"),"w",encoding="utf-8").write("\n".join(rep)+"\n")
print("\n".join(rep))
