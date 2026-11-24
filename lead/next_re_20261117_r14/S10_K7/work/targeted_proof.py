from common import Image, EV
import struct, bisect
img=Image(); lines=[]

def sec_of_va(va):
    for vaddr,vs,ptr,rs,name in img.sections:
        if vaddr<=va-img.imagebase<vaddr+max(vs,rs): return name
    return '?'

def off_of_va(va):
    rva=va-img.imagebase
    for vaddr,vs,ptr,rs,name in img.sections:
        if vaddr<=rva<vaddr+max(vs,rs): return ptr+(rva-vaddr)
    return None

def rtti(vt):
    col=img.u32(vt-4); td=img.u32(col+0xC); nm=img.cstr(td+8,128)
    return col,td,nm

def dump(va,n,maxins=200,label=None):
    lines.append(f'===== {label or ""} {va:08X} ({n:#x} bytes) =====')
    for ins in list(img.cs.disasm(img.read(va,n),va))[:maxins]:
        lines.append(img.fmt(ins))
    lines.append('')

# section map
lines.append('=== PE ===')
lines.append(f'imagebase {img.imagebase:#x}')
for vaddr,vs,ptr,rs,name in img.sections:
    lines.append(f'{name:8} VA {img.imagebase+vaddr:08X}..{img.imagebase+vaddr+max(vs,rs):08X} raw {ptr:X}..{ptr+rs:X}')

# RTTI for five vtables
lines.append('\n=== RTTI chains (COL+0xC -> TD, TD+8 inline name) ===')
for vt in (0x7F3650,0x7F3634,0x7F362C,0x7F3624,0x7F36D4,0x7E920C):
    col,td,nm=rtti(vt)
    b=img.read(td+8,80)
    lines.append(f'vt={vt:08X} COL={col:08X} TD={td:08X} TD+8 raw={b.hex()} name={nm}')
    lines.append(f'  slots first16: '+' '.join(f'{img.u32(vt+4*i):08X}' for i in range(16)))

# exact u32 hits for function addresses
lines.append('\n=== exact u32 hits of function addresses ===')
for target in (0x006B7010,0x006B8140,0x004E0E80):
    pat=struct.pack('<I',target); st=0; hits=[]
    while True:
        i=img.data.find(pat,st)
        if i<0: break
        for vaddr,vs,ptr,rs,name in img.sections:
            if ptr<=i<ptr+rs:
                hits.append((img.imagebase+vaddr+i-ptr,name)); break
        st=i+1
    lines.append(f'{target:08X}: '+', '.join(f'{a:08X}/{s}' for a,s in hits))

# direct E8 callers, raw rel32 scan within .text
lines.append('\n=== direct E8 callers (raw rel32 scan, .text) ===')
callers={t:[] for t in (0x006B7010,0x006B8140,0x006B7F10,0x004E0E80,0x007C8B3D,0x007C8E17)}
for vaddr,vs,ptr,rs,name in img.sections:
    if name!='.text': continue
    for off in range(ptr,ptr+rs-4):
        if img.data[off]!=0xE8: continue
        rel=struct.unpack('<i',img.data[off+1:off+5])[0]
        src=img.imagebase+vaddr+off-ptr
        tgt=src+5+rel
        if tgt in callers: callers[tgt].append(src)
for t,srcs in callers.items():
    lines.append(f'{t:08X}: {len(srcs)} -> '+', '.join(f'{s:08X}' for s in srcs))
    for s in srcs[:12]:
        dis=[img.fmt(x) for x in img.cs.disasm(img.read(s-0x20,0x60),s-0x20)]
        lines.append('  near '+f'{s:08X}'+': '+' | '.join(dis[-8:]))

# dumps
dump(0x006B8140,0x60,label='scalar dtor wrapper')
dump(0x006B7010,0x20,label='dtor body head')
dump(0x006B7F10,0x120,label='same-group vptr writer function')
dump(0x004E0E80,0x50,label='candidate ctor full')
dump(0x007C8E17,0x30,label='allocator target of 004E0EB5')
dump(0x007C8B3D,0x10,label='CRT _delete wrapper')

(EV/'targeted_proof.txt').write_text('\n'.join(lines),encoding='utf-8')
print('\n'.join(lines[:500]))
