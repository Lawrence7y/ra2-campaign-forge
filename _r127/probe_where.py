import struct
import pefile
pe=pefile.PE('ra2bench/gamemd.exe'); IB=pe.OPTIONAL_HEADER.ImageBase
S={s.Name.rstrip(b'\x00').decode():s for s in pe.sections}
def u32(va):
    b=pe.get_data(va-IB,4); return struct.unpack('<I',b)[0] if len(b)==4 else None
RD=S['.rdata']; DA=S['.data']
for t in (0x7e36c0,0x7e9b20):
    hits=[]
    for s in (RD,DA):
        lo=s.VirtualAddress+IB; hi=lo+s.Misc_VirtualSize
        for va in range(lo,hi-4,4):
            if u32(va)==t: hits.append((s.Name.rstrip(b'\x00').decode(),hex(va)))
    print(hex(t),hits)
