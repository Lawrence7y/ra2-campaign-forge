from common import Image, EV
img=Image(); lines=[]
for td in (0x00840120,0x00840140,0x008225B8,0x00822640):
  lines.append(f"--- TD candidate {td:08X} ---")
  for i in range(10):
    va=td+4*i
    v=img.u32(va)
    s=''
    if img.imagebase<=v<img.imagebase+0x500000:
      try:
        z=img.cstr(v,80)
        if z and all(32<=ord(c)<127 for c in z[:8]): s=' str='+repr(z)
      except Exception as e: s=' <unmapped>'
    lines.append(f"  {va:08X}: {v:08X}{s}")
  try: lines.append("  raw cstr at TD+8: "+repr(img.cstr(td+8,80)))
  except Exception as e: lines.append("  raw cstr at TD+8 failed: "+str(e))
(EV/"td_probe.txt").write_text("\n".join(lines),encoding="utf-8");print("\n".join(lines))
