from common import Image, EV
img=Image(); lines=[]
vals=[0x7F3650,0x7F3634,0x7F362C,0x7F3624,0x7E920C]
def va_from_off(off):
  for vaddr,vs,ptr,rs,name in img.sections:
    if ptr<=off<ptr+rs: return img.imagebase+vaddr+(off-ptr),name
  return None,None
for val in vals:
  pat=val.to_bytes(4,'little'); st=0; hits=[]
  while True:
    i=img.data.find(pat,st)
    if i<0: break
    va,sec=va_from_off(i)
    hits.append((i,va,sec,img.data[max(0,i-10):i+10].hex()))
    st=i+1
  lines.append(f"=== imm {val:08X} hits {len(hits)} ===")
  for off,va,sec,ctx in hits:
    line=f"off {off:X} va {va and format(va,'08X')} sec {sec} ctx {ctx}"
    if sec=='.text' and va:
      try:
        dis=[img.fmt(x) for x in img.cs.disasm(img.data[max(0,off-8):off+14],(va or 0)-8)]
        line+='\n    '+'\n    '.join(dis)
      except Exception as e: line+=' dis_err '+str(e)
    lines.append(line)
(EV/'imm_vptr_hits.txt').write_text('\n'.join(lines),encoding='utf-8')
print('\n'.join(lines[:500]))
