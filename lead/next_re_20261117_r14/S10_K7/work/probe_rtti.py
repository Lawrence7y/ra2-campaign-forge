from common import Image, EV
img=Image()
lines=[]
def probe_vt(vt,n=16):
    col=img.u32(vt-4); td=img.u32(col+0xC); nm=img.cstr(img.u32(td+8))
    lines.append(f"VT {vt:08X}: COL {col:08X} TD {td:08X} TD+8 nameptr {img.u32(td+8):08X} name {nm}")
    lines.append(" slots: "+" ".join(f"{img.u32(vt+4*i):08X}" for i in range(n)))
for vt in (0x7F3650,0x7F3634,0x7F362C,0x7F3624,0x7F36D4,0x7E920C): probe_vt(vt)
lines.append("--- exact u32 hits in file for function addresses ---")
for target in (0x006B7010,0x006B8140,0x004E0E80):
    pat=target.to_bytes(4,"little")
    hits=[]; st=0
    while True:
        i=img.data.find(pat,st)
        if i<0: break
        hits.append(i); st=i+1
    addrs=[]
    for i in hits:
        rva=i # need map raw offset back to VA
        for vaddr,vs,ptr,rs,name in img.sections:
            if ptr<=i<ptr+rs: addrs.append((img.imagebase+vaddr+(i-ptr),name))
    lines.append(f"{target:08X}: {len(hits)} file hits -> "+", ".join(f"{a:08X}/{s}" for a,s in addrs))
(EV/"rtti_and_vtables.txt").write_text("\n".join(lines),encoding="utf-8")
print("\n".join(lines))
