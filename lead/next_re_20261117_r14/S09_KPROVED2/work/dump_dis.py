import sys, struct
import pefile
from capstone import *
from capstone.x86 import *

PATH = r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe"
pe = pefile.PE(PATH, fast_load=True)
IB = pe.OPTIONAL_HEADER.ImageBase

secs = []
for s in pe.sections:
    nm = s.Name.rstrip(b'\x00').decode('latin-1')
    va = IB + s.VirtualAddress
    data = s.get_data()
    secs.append((nm, va, s.Misc_VirtualSize, data))

def va_to_off(va):
    for nm, sva, vs, data in secs:
        if sva <= va < sva + vs:
            return data, va - sva
    return None, None

md = Cs(CS_ARCH_X86, CS_MODE_32)
md.detail = True
md.skipdata = True

# candidates: entry, ext_hi (exclusive)
cands = [
    ('006A5840','006A5BE8','SidebarClass::slot53'),
    ('006D0680','006D09B6','TabClass::slot10'),
    ('0063FB20','0063FDB8','PowerClass::slot16'),
    ('005BE6D0','005BE935','MouseClass::slot31'),
    ('004E2690','004E2830','GaugeClass::slot27'),
    ('00654320','0065448C','RadarClass::slot34'),
    ('0069DEB0','0069DFB6','ShapeButtonClass::slot27'),
    ('00557730','005577F4','ListClass::slot42'),
]

for ent_s, hi_s, nm in cands:
    lo = int(ent_s,16); hi = int(hi_s,16)
    data, off = va_to_off(lo)
    code = data[off:off+(hi-lo)]
    out = []
    n = 0
    for ins in md.disasm(code, lo):
        n += 1
        out.append("%08X: %-24s %s %s" % (ins.address, ins.bytes.hex(), ins.mnemonic, ins.op_str))
    fn = "dis_%s.txt" % ent_s
    with open(fn,'w',encoding='utf-8') as f:
        f.write("; %s  [%08X,%08X)  %d bytes  %d insns\n" % (nm, lo, hi, hi-lo, n))
        f.write("\n".join(out))
    print("%s %s -> %s (%d insns)" % (ent_s, nm, fn, n))
