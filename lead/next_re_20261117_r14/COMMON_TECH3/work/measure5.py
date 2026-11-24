import sys, struct
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import pefile
from capstone import Cs, CS_ARCH_X86, CS_MODE_32
IMG = r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe"
data = open(IMG, "rb").read()
pe = pefile.PE(IMG, fast_load=True); ib = pe.OPTIONAL_HEADER.ImageBase
secs = [(s.Name.rstrip(b"\x00").decode(), s.VirtualAddress+ib, s.Misc_VirtualSize, s.PointerToRawData, s.SizeOfRawData) for s in pe.sections]
def va2off(va):
    for n,sva,vs,raw,rs in secs:
        if sva <= va < sva+max(vs,rs):
            o = raw+(va-sva)
            if 0 <= o < len(data): return o
def rd(va,n):
    o=va2off(va); return None if o is None else data[o:o+n]
def u32(va):
    b=rd(va,4); return None if b is None or len(b)<4 else struct.unpack("<I",b)[0]
md = Cs(CS_ARCH_X86, CS_MODE_32)
def dis(va, cnt=8, nb=48):
    for i in md.disasm(rd(va,nb), va):
        print("  %08X  %-20s %s %s" % (i.address, i.bytes.hex(), i.mnemonic, i.op_str)); cnt-=1
        if cnt<=0: break
print("### D-47: the two pairs of rows and the single install instruction they share")
for vt, s5, s6, inst in ((0x007F6B30,0x0075E0C0,0x0075E2C0,0x0075D0BA),(0x007F73B8,0x00772CD0,0x00772EB0,0x00771E77)):
    print("  vt 0x%08X : slot5=0x%08X (want 0x%08X)  slot6=0x%08X (want 0x%08X)" % (vt,u32(vt+0x14),s5,u32(vt+0x18),s6))
    print("  install instruction:"); dis(inst,3,16)
print("\n### row 004F45B0 = MouseClass::slot17 ?  vt 0x007E1964 slot17 = 0x%08X" % u32(0x007E1964+4*17))
print("### 004F45B0 prologue:"); dis(0x004F45B0,10,48)
