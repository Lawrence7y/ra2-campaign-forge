from common import Image, EV
img=Image(); lines=[]
def words(va,n=32):
  return " ".join(f"{va+4*i:08X}:{img.u32(va+4*i):08X}" for i in range(n))
for vt in (0x7F3650,0x7F3634,0x7F362C,0x7F3624,0x7F36D4,0x7E920C):
  lines.append(f"--- VT {vt:08X} ---")
  lines.append(words(vt-16,20))
  col=img.u32(vt-4)
  lines.append(f"candidate COL=vt-4 {col:08X}")
  lines.append(words(col,8))
  # try all offsets near col with name-like pointer
  for off in range(0,0x20,4):
    v=img.u32(col+off)
    if img.imagebase<=v<img.imagebase+0x400000:
      try: s=img.cstr(v,60)
      except: s='<unmapped>'
      if s and all(32<=ord(ch)<127 for ch in s[:6]): lines.append(f"  col+{off:X} -> {v:08X} str {s!r}")
(EV/"rtti_layout_probe.txt").write_text("\n".join(lines),encoding="utf-8")
print("\n".join(lines))
