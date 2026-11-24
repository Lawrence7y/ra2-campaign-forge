import sys, struct, pefile, capstone
from capstone import Cs, CS_ARCH_X86, CS_MODE_32

EXE = r'D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe'
pe = pefile.PE(EXE, fast_load=True)
IB = pe.OPTIONAL_HEADER.ImageBase
DATA = open(EXE, 'rb').read()

SECS = []
for s in pe.sections:
    nm = s.Name.rstrip(b'\x00').decode('latin1')
    SECS.append((nm, IB + s.VirtualAddress, IB + s.VirtualAddress + s.Misc_VirtualSize,
                 s.PointerToRawData, s.Misc_VirtualSize))

def sec_of(va):
    for nm, s, e, raw, sz in SECS:
        if s <= va < e:
            return nm, s, e, raw, sz
    return None

def off(va):
    for nm, s, e, raw, sz in SECS:
        if s <= va < e:
            return raw + (va - s)
    raise ValueError(hex(va))

def rd(va, n):
    o = off(va)
    return DATA[o:o+n]

def u32(va):
    return struct.unpack('<I', rd(va, 4))[0]

def u16(va):
    return struct.unpack('<H', rd(va, 2))[0]

md = Cs(CS_ARCH_X86, CS_MODE_32)
md.detail = True
md.skipdata = True

def dis(va, n, count=200):
    out = []
    for i in md.disasm(rd(va, n), va):
        out.append((i.address, i.mnemonic, i.op_str, i.size, i.bytes.hex()))
        if len(out) >= count:
            break
    return out

def show(va, n, count=200):
    res = dis(va, n, count)
    for a, m, o, sz, b in res:
        print('%08X  %-22s %s %s' % (a, b, m, o))
    return res
