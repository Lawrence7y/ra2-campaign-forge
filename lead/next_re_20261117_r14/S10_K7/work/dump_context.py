from common import Image, EV
img=Image(); lines=[]
def dump(va,n,maxins=200):
  lines.append(f'===== {va:08X} ({n:#x} bytes) =====')
  lines.append('bytes: '+img.read(va,min(n,256)).hex())
  for ins in img.cs.disasm(img.read(va,n),va):
    lines.append(img.fmt(ins))
    if len(lines)>200000: break
  lines.append('')
dump(0x006B7ED0,0x120)
dump(0x006B6CE0,0x80)
dump(0x004E0E80,0x70)
dump(0x007C8B3D,0x40)
dump(0x007C93E8,0x60)
dump(0x004101F0,0x80)
(EV/'target_context_disasm.txt').write_text('\n'.join(lines),encoding='utf-8')
print('\n'.join(lines))
