"""S18-F1: locate EventClass network event type, containers, and FillEvent field writers."""
import sys, struct, re
sys.path.insert(0, r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S18-F1\work')
from pe_util import read, u32, sections, disasm_insns, scan_rel32_calls

# 1. raw scan for 'EventClass' substrings
print("===== raw 'EventClass' occurrences (all sections) =====")
for name,va_base,vsize,praw,rawsize,ch in sections():
    if rawsize<=0: continue
    data=read(va_base,rawsize)
    if not data: continue
    for m in re.finditer(b'EventClass', data):
        va=va_base+m.start()
        ctx=data[max(0,m.start()-6):m.start()+len('EventClass')+6]
        asc=''.join(chr(x) if 32<=x<127 else '.' for x in ctx)
        print(f"  0x{va:08X} [{name}] {asc}")

# 2. find vftables for DynamicVectorClass<EventClass*> (TD name at 0x8368C8) and VectorClass<EventClass*> (0x836898)
print("\n===== vftables pointing to EventClass container TDs =====")
# TD inline-name arrays: find TD base = nameva-8
for nm, nameva in [('DVec<EventClass*>',0x8368C8),('Vec<EventClass*>',0x836898)]:
    tdva=nameva-8
    # TD vptr should be 0x7F9594-ish; validate
    print(f"  {nm}: TD=0x{tdva:08X} vptr=0x{u32(tdva) or 0:08X} namebytes={read(nameva,40)}")
    # find COLs whose +0xC == tdva
    pat=struct.pack('<I',tdva)
    cols=[]
    for n2,vb,rs in [(x[0],x[1],x[4]) for x in sections() if x[4]>0]:
        d=read(vb,rs)
        if not d: continue
        p=0
        while True:
            j=d.find(pat,p)
            if j<0: break
            colva=vb+j-0xC
            if u32(colva)==0: cols.append((colva,u32(colva+4)))
            p=j+1
    for colva,off in cols:
        pat2=struct.pack('<I',colva)
        for n3,vb3,rs3 in [(x[0],x[1],x[4]) for x in sections() if x[4]>0]:
            d3=read(vb3,rs3)
            if not d3: continue
            p3=0
            while True:
                q=d3.find(pat2,p3)
                if q<0: break
                vt=vb3+q+4
                print(f"    vftable 0x{vt:08X} COL 0x{colva:08X} obj_off 0x{off:X}")
                p3=q+1
