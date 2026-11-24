# -*- coding: utf-8 -*-
import sys,re
sys.path.insert(0,__import__('os').path.dirname(__file__))
import pe_common as p
sys.stdout.reconfigure(encoding='utf-8')
VTS=[0x7e17cc,0x7e17e4,0x7e1e84,0x7e1e9c,0x7e1ed4,0x7e1eec,0x7e4678,0x7e4690,0x7e5170,0x7e5184]
for vt in VTS:
 sites=[x for x in p.imm_refs(vt) if p.TSTART<=x<p.TEND]
 print(f'\n=== VT {vt:#x} refs {[hex(x) for x in sites]} ===')
 for s in sites[:8]:
  lo=max(p.TSTART,s-0x80); ins=p.dis(lo,0x200)
  print(f'-- around {s:#x} --')
  for a,bb,txt,i in ins:
   mark='<<<' if a==s else ''
   if a in range(s-0x20,s+0x20) or 'call' in txt:
    print(f'{a:08X} {bb:<16} {txt} {mark}')
