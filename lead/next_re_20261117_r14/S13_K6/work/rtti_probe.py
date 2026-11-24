# -*- coding: utf-8 -*-
import sys,struct
sys.path.insert(0,__import__('os').path.dirname(__file__))
import pe_common as p
sys.stdout.reconfigure(encoding='utf-8')
for vt in [0xBE17CC,0xBE17E4,0xBE1E84,0xBE1E9C]:
 print('\nVT',hex(vt),'vt-4',hex(p.d32(vt-4)))
 for a in range(vt-0x20,vt+0x30,4):
  v=p.d32(a); extra=''
  try:
   col=v;sig,off,cdoff,td,chd=struct.unpack('<IIIII',p.rd(col,20)); b=p.rd(td+8,80);z=b.find(0);extra=f'COL off={off} TD={td:#x} name={b[:z]!r}'
  except Exception: pass
  print(f'{a:08X}: {v:08X} {extra}')
