#!/usr/bin/env python3
import os,re,struct
import pefile
ROOT=r'D:\Project\ra2-campaign-forge'; EXE=os.path.join(ROOT,r'ra2youli\gamemd.exe')
pe=pefile.PE(EXE,fast_load=False); IB=pe.OPTIONAL_HEADER.ImageBase; data=open(EXE,'rb').read()
def u32(va): return struct.unpack_from('<I',data,va-IB)[0]
def sections(name):
    return [(IB+s.VirtualAddress,s.Misc_VirtualSize) for s in pe.sections if s.Name.rstrip(b'\0')==name]
# full mangled name '.?AVWaveClass@@'
pat=rb'\.\?AVWaveClass@@'
m=re.search(pat,data)
nameva=IB+m.start()
td=nameva-8
print(f'.?AVWaveClass@@ @0x{nameva:X}, TD=0x{td:X}, TD+8 value=0x{u32(td+8):X} (should==0x{nameva:X})')
# RTTI COL: COL+0xC -> TD. Also TD+0x10 may point to COL via -; scan .data+.rdata for dword==td
col_hits=[]
for secname in ('.rdata','.data'):
    for base,sz in sections(secname):
        for off in range(0,sz-4,4):
            va=base+off
            if u32(va)==td:
                cand=va-0xC
                # verify COL: at cand, +0x8 ->... check some structure: COL typically has +0 = 0, +4/+8 ptrs
                col_hits.append((cand,secname))
print('COL candidates (COL+0xC==TD):',[(hex(x),s) for x,s in col_hits])
# vtable[-1] -> COL
for col,s in col_hits:
    vt=[]
    for base,sz in sections('.rdata'):
        for off in range(0,sz-4,4):
            va=base+off
            if u32(va)==col: vt.append(va+4)
    print(f'COL 0x{col:X} ({s}) -> vtable starts {[hex(x) for x in vt]}')
    for vstart in vt[:6]:
        slots=[u32(vstart+4*i) for i in range(24)]
        gs=[]
        for i,fn in enumerate(slots):
            if 0x401000<=fn<0x7E038D:
                b=data[fn-IB:fn-IB+6]
                if len(b)==6 and b[0]==0xB8 and b[5]==0xC3:
                    gs.append((i,fn,struct.unpack_from('<I',b,1)[0]))
        print(f'  vtable 0x{vstart:X}: nslots_sample(0x{vstart:X}..) getsize_patterns={[(i,hex(f),hex(v)) for i,f,v in gs]}')
