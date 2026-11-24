from common import Image, EV
import struct
img=Image(); lines=[]
def dump(va,n,label):
 lines.append(f'===== {label} {va:08X} =====')
 for ins in list(img.cs.disasm(img.read(va,n),va))[:120]: lines.append(img.fmt(ins))
 lines.append('')
dump(0x006B6C90,0xA0,'candidate A')
dump(0x006B6EA0,0x80,'candidate B')
dump(0x006B6F90,0x80,'candidate C region')
# direct callers for candidate entries
for tgt in (0x006B6C90,0x006B6EA0,0x006B6FA0,0x006B6FC0,0x006B6FD0,0x006B6FE0):
 srcs=[]
 for vaddr,vs,ptr,rs,name in img.sections:
  if name!='.text': continue
  for off in range(ptr,ptr+rs-4):
   if img.data[off]!=0xE8: continue
   rel=struct.unpack('<i',img.data[off+1:off+5])[0]
   src=img.imagebase+vaddr+off-ptr
   if src+5+rel==tgt: srcs.append(src)
 lines.append(f'callers {tgt:08X}: '+', '.join(f'{x:08X}' for x in srcs))
(EV/'ctor_candidates.txt').write_text('\n'.join(lines),encoding='utf-8');print('\n'.join(lines))
