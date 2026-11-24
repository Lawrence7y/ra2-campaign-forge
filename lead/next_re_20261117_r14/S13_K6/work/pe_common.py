# -*- coding: utf-8 -*-
import hashlib, struct, pefile
from capstone import Cs, CS_ARCH_X86, CS_MODE_32
EXE = r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe"
data = open(EXE,'rb').read()
pe = pefile.PE(EXE, fast_load=True)
IB = pe.OPTIONAL_HEADER.ImageBase
SECS = [(s.Name.decode('latin1').rstrip('\x00'), IB+s.VirtualAddress, s.Misc_VirtualSize, s.SizeOfRawData, s.PointerToRawData) for s in pe.sections]
TEXT = pe.sections[0]
TSTART = IB + TEXT.VirtualAddress
TEND = TSTART + TEXT.Misc_VirtualSize
MD = Cs(CS_ARCH_X86, CS_MODE_32); MD.detail = True; MD.skipdata = True

def sha256(): return hashlib.sha256(data).hexdigest().upper()
def va2off(va):
    rva = va - IB
    for s in pe.sections:
        if s.VirtualAddress <= rva < s.VirtualAddress + max(s.Misc_VirtualSize, s.SizeOfRawData):
            return s.PointerToRawData + (rva - s.VirtualAddress)
    raise KeyError(hex(va))
def rd(va,n):
    o = va2off(va); return data[o:o+n]
def d32(va): return struct.unpack('<I', rd(va,4))[0]
def d16(va): return struct.unpack('<H', rd(va,2))[0]
def cstr(va, n=120):
    b = rd(va,n); z = b.find(b'\x00'); return b[:z if z>=0 else n]
def dis(va, maxbytes=400, stop_first_ret=False):
    out=[]
    for i in MD.disasm(rd(va,maxbytes), va):
        out.append((i.address, i.bytes.hex(), i.mnemonic+' '+i.op_str, i))
        if stop_first_ret and i.mnemonic in ('ret','retn'): break
    return out
def dump(va, maxbytes=400, stop_first_ret=False):
    for a,b,s,i in dis(va,maxbytes,stop_first_ret): print(f"{a:08X}  {b:<20s} {s}")
def imm_refs(va):
    pat = struct.pack('<I', va)
    blob = data[TEXT.PointerToRawData:TEXT.PointerToRawData+TEXT.Misc_VirtualSize]
    out=[]; p=0
    while True:
        j=blob.find(pat,p)
        if j<0: break
        out.append(TSTART+j); p=j+1
    return out
def vtinfo(vt):
    col=d32(vt-4)
    sig,off,cdoff,td,chd=struct.unpack('<IIIII', rd(col,20))
    b=rd(td+8,100); z=b.find(b'\x00')
    return dict(vt=vt, col=col, coloff=off, td=td, name=b[:z if z>=0 else 100])
