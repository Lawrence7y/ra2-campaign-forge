"""S18-F1: proper MSVC RTTI decoder (COL -> TypeDescriptor -> name)."""
import sys, struct, re
sys.path.insert(0, r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S18-F1\work')
from pe_util import read, u32, sections

def decode_vt(vt):
    col = u32(vt-4)
    if not col: return (None,None,None)
    td = u32(col+0xC)
    name = None
    if td and 0x400000 < td < 0xC00000:
        nv = u32(td+8)
        if nv and 0x400000 < nv < 0xC00000:
            b = read(nv, 160)
            if b: name = b.split(b'\x00')[0].decode('latin1')
    return (col, td, name)

print("===== vftable attribution (COL chain) =====")
for vt in [0x7F550C,0x7F554C,0x7F5554,0x7F555C,0x7F5578, 0x7F4108]:
    col,td,nm = decode_vt(vt)
    print(f"  vt 0x{vt:08X}: COL=0x{col or 0:08X} TD=0x{td or 0:08X} name={nm}")

# Find all COL entries whose TypeDescriptor name is EventClass / TEventClass
print("\n===== scan .data/.rdata for TypeDescriptors named *EventClass@@ =====")
sec_ranges=[]
for name,va_base,vsize,praw,rawsize,ch in sections():
    if rawsize>0: sec_ranges.append((name,va_base,rawsize))
rx=re.compile(rb'\x2e\x3f\x41\x56[\x20-\x7e]{0,80}')
for name,va_base,rawsize in sec_ranges:
    data=read(va_base,rawsize)
    if not data: continue
    for m in rx.finditer(data):
        s=m.group(0).decode('latin1')
        if s in ('.?AVEventClass@@','.?AVTEventClass@@','.?AVRadarEventClass@@'):
            nameva=va_base+m.start()
            # TypeDescriptor starts 8 bytes before name ptr target? name ptr is at TD+8
            # find TD candidates: scan for dword == nameva in nearby data
            print(f"\n  name {s} @0x{nameva:08X} [{name}]")
            # find TD by searching dwords pointing to nameva
            pat=struct.pack('<I',nameva)
            for nm2,vb,rs in sec_ranges:
                d2=read(vb,rs)
                if not d2: continue
                p=0
                while True:
                    j=d2.find(pat,p)
                    if j<0: break
                    tdva=vb+j-8  # TD+8 = nameptr
                    # validate TD: [td]=vptr into .data, [td+4]=0
                    vptr=u32(tdva); sp=u32(tdva+4)
                    if vptr and 0x400000<vptr<0xC00000 and sp==0:
                        # find COLs pointing to this TD (COL+0xC == tdva)
                        pat2=struct.pack('<I',tdva)
                        for nm3,vb3,rs3 in sec_ranges:
                            d3=read(vb3,rs3)
                            if not d3: continue
                            p2=0
                            while True:
                                k=d3.find(pat2,p2)
                                if k<0: break
                                colva=vb3+k-0xC
                                # COL signature [col]=0; [col+4]=offset; [col+8]=cdo
                                sig=u32(colva)
                                if sig==0:
                                    # find vtables pointing to this COL: vt-4==colva
                                    pat3=struct.pack('<I',colva)
                                    for nm4,vb4,rs4 in sec_ranges:
                                        d4=read(vb4,rs4)
                                        if not d4: continue
                                        p3=0
                                        while True:
                                            q=d4.find(pat3,p3)
                                            if q<0: break
                                            vtva=vb4+q+4
                                            print(f"    TD=0x{tdva:08X} COL=0x{colva:08X} vftable=0x{vtva:08X}")
                                            p3=q+1
                                        p2=k+1
                    p=j+1
