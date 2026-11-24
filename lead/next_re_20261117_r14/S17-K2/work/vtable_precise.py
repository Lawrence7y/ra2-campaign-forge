#!/usr/bin/env python3
"""S17-K2: precise vtable boundary + slot resolution (FIXED).
A COL POINTER is stored at vtable[-4]; the COL STRUCTURE lives elsewhere in .rdata.
Scan .rdata for dwords whose value points to a valid COL structure; vtable base = that position + 4.
Vtable extent ends at the next such COL-pointer position.
"""
import sys, struct, os, re, io
sys.path.insert(0, r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S17-F1\work")
import pe_util as P

OUT = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S17-K2\EVIDENCE"
out=io.StringIO()
def p(*a): print(*a,file=out)

_colcache={}
def col_class(col):
    if col in _colcache: return _colcache[col]
    r=None
    if P.u32(col)==0:
        td=P.u32(col+0xC)
        if td is not None and 0x400000<=td<0x900000:
            raw=P.read(td+8, 100)
            if raw is not None:
                nm=raw.split(b'\x00')[0]
                try: s=nm.decode('ascii')
                except: s=''
                if s.startswith('.?AV') or s.startswith('.?AU'):
                    m=re.match(r'\.\?A[UV]([A-Za-z0-9_]+)@@',s)
                    r=m.group(1) if m else s
    _colcache[col]=r
    return r

# scan .rdata for positions a where dword[a] is a COL structure pointer
rdata=[s for s in P.sections() if s[0]=='.rdata'][0]
lo=rdata[1]; hi=lo+rdata[3]; data=P.read(lo,hi-lo)
colptr={}   # position a (vt-4) -> class
for i in range(0,len(data)-4,4):
    a=lo+i
    cp=struct.unpack_from('<I',data,i)[0]
    if cp==0: continue
    cls=col_class(cp)
    if cls: colptr[a]=cls

vt_bases=set(a+4 for a in colptr)
p(f"COL pointers in .rdata = {len(colptr)}; vtable bases = {len(vt_bases)}")

def vtable_extent(vb):
    slots=[]; k=0
    while True:
        a=vb+4*k
        if a in vt_bases and k>0: break
        sv=P.u32(a)
        if sv is None: break
        if not (0x401000<=sv<0x900000): break
        slots.append(sv); k+=1
        if k>200: break
    return slots

def find_hit_info(target):
    res=[]
    for hva,sname in P.scan_imm32_refs(target):
        if sname!='.rdata': continue
        vb=None
        for k in range(0,120):
            cand=hva-4*k
            if cand in vt_bases: vb=cand; break
        if vb is None: continue
        slot=(hva-vb)//4
        cls=colptr.get(vb-4)
        slots=vtable_extent(vb)
        res.append((hva,vb,slot,cls,vb-4,len(slots),slots))
    return res

for target,label in [(0x410410,'AbstractClass::Save'),
                     (0x41D6E0,'Airstrike target 0x41D6E0'),
                     (0x43A5D0,'Neuron target 0x43A5D0')]:
    p(f"\n{'='*90}\n{label} as vtable slot:")
    infos=find_hit_info(target)
    if not infos: p("  NO .rdata vtable hit")
    for hva,vb,slot,cls,col,nslots,slots in infos:
        p(f"  hit@0x{hva:08X} vt=0x{vb:08X} colptr@0x{col:08X} class={cls} slot={slot} nslots={nslots}")
        for k,sv in enumerate(slots):
            p(f"      slot{k:2d} (+0x{4*k:X}) = 0x{sv:08X}")

p(f"\n{'='*90}\nOther vtable constants seen in target disasm:")
for vt in (0x7E3A2C,0x7F743C,0x7E1B0C,0x7F4108):
    cp=P.u32(vt-4)
    p(f"  vt=0x{vt:08X} colptr@0x{vt-4:08X}->0x{cp:08X} class={col_class(cp)}")

with open(os.path.join(OUT,"vtable_precise.txt"),"w",encoding="utf-8") as f: f.write(out.getvalue())
print("wrote vtable_precise.txt")
