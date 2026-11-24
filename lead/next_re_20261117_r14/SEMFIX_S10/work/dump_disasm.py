import sys, json, os
import pefile
from capstone import Cs, CS_ARCH_X86, CS_MODE_32

EXE = r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe"
OUT = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\SEMFIX_S10\EVIDENCE"

pe = pefile.PE(EXE, fast_load=True)
image_base = pe.OPTIONAL_HEADER.ImageBase
# section VA range -> raw offset
secs = []
for s in pe.sections:
    va = image_base + s.VirtualAddress
    secs.append((va, va + s.Misc_VirtualSize, s.PointerToRawData, s.Name.rstrip(b'\x00').decode('latin1')))

def va2off(va):
    for (lo, hi, raw, nm) in secs:
        if lo <= va < hi:
            return raw + (va - lo)
    return None

def read(va, n):
    off = va2off(va)
    if off is None:
        return None
    with open(EXE,'rb') as f:
        f.seek(off); return f.read(n)

md = Cs(CS_ARCH_X86, CS_MODE_32)
md.detail = False

# entry,size from atlas
specs = [
 ("0045A560",176),("0045A610",38),("004D4200",126),("004D4280",2177),("004D4B20",388),
 ("004D4CB0",265),("004D4DC0",498),("004D5070",722),("004D5350",614),("004D6AA0",1732),
 ("004D9290",524),("004DA2C0",535),("004DA530",2520),("004DDF90",574),("0051F3E0",351),
 ("005B2FD0",99),("005B3060",1158),("005B3570",98),("005B35E0",101),("005B3650",83),
 ("005B36B0",40),("006B1850",176),("006B1900",38),("006B8660",176),("006B8710",38),
]

allins = {}
lines_out = []
for entry, size in specs:
    va = int(entry,16)
    code = read(va, size)
    if code is None:
        print("NO MAP", entry); continue
    ins = list(md.disasm(code, va))
    allins[entry] = [{"a":"%08X"%i.address,"b":i.bytes.hex(),"m":i.mnemonic,"o":i.op_str} for i in ins]
    lines_out.append("===== %s size=%d ins=%d ====="%(entry,size,len(ins)))
    for i in ins:
        lines_out.append("%08X  %-20s %-8s %s"%(i.address, i.bytes.hex(), i.mnemonic, i.op_str))
    lines_out.append("")

with open(os.path.join(OUT,"DISASM_25.txt"),"w",encoding="utf-8") as f:
    f.write("\n".join(lines_out))
with open(os.path.join(OUT,"DISASM_25.json"),"w",encoding="utf-8") as f:
    json.dump(allins,f,ensure_ascii=False,indent=0)
print("WROTE disasm for", len(allins), "functions; total ins", sum(len(v) for v in allins.values()))
