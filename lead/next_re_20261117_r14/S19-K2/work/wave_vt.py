#!/usr/bin/env python3
import struct,pefile,os
p=pefile.PE(r'D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe',fast_load=False)
IB=p.OPTIONAL_HEADER.ImageBase; d=open(r'D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe','rb').read()
def u32(va): return struct.unpack_from('<I',d,va-IB)[0]
cols=[0x80D378,0x80D390,0x80D3A8,0x80D3B4,0x80D418]
# verify COL signature: COL+0 should be 0 (signature), +4 offset, +8 cdOffset
for c in cols:
    print(f'COL 0x{c:X}: sig=0x{u32(c):X} off=0x{u32(c+4):X} cd=0x{u32(c+8):X} TD=0x{u32(c+0xC):X} CHD=0x{u32(c+0x10):X}')
# vtable[-1] -> COL: dword==col
for c in cols:
    refs=[]
    for i in range(0,len(d)-4,4):
        if struct.unpack_from('<I',d,i)[0]==c: refs.append(IB+i)
    # vtable starts = ref+4
    vts=[r+4 for r in refs]
    print(f'COL 0x{c:X} -> vftable starts {[hex(x) for x in vts]}')
    for vt in vts:
        slots=[u32(vt+4*i) for i in range(40)]
        gs=[]
        for i,fn in enumerate(slots):
            if 0x401000<=fn<0x7E038D:
                b=d[fn-IB:fn-IB+6]
                if len(b)==6 and b[0]==0xB8 and b[5]==0xC3:
                    gs.append((i,fn,struct.unpack_from('<I',b,1)[0]))
        print(f'  vt 0x{vt:X} slots[0:8]={[hex(x) for x in slots[:8]]} GETSIZE={[(i,hex(f),hex(v)) for i,f,v in gs]}')
