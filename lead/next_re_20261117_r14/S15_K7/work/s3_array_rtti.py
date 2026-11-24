# -*- coding: utf-8 -*-
import sys,struct,re
sys.path.insert(0,__import__('os').path.dirname(__file__))
import pe_common as p
sys.stdout.reconfigure(encoding='utf-8')
ARRAYS={0xB0E780:'TagTypeClass',0xA8ECA0:'TeamTypeClass',0x8B4178:'TriggerTypeClass',0xB1D378:'VocClass',0xB1D4A0:'VoxClass'}
print('=== RTTI array element types: vptr writes at array initialization sites ===')
for arr,cls in ARRAYS.items():
 print(f'-- array {arr:#x} expected {cls} --')
 refs=p.imm_refs(arr)
 print('imm32 refs count',len(refs),[hex(x) for x in refs[:30]])
 for site in refs:
  # dump window around site, collect dword values written as vtable
  for a,bb,s,i in p.dis(site-0x10,0x60):
   try:
    for op in i.operands:
     if op.type==2: # x86 mem
      if op.mem.disp==arr:
       # check nearby immediate vtable candidates in +/- 0x20 bytes raw
       pass
   except Exception: pass
  # raw bytes around reference: list immediates that look like .rdata vtables with COL/TD
  lo=site-0x20; hi=site+0x40
  raw=p.rd(lo,hi-lo)
  cands=[]
  for k in range(0,len(raw)-3):
   v=struct.unpack_from('<I',raw,k)[0]
   if 0x7E1000<=v<0x811000 and v%4==0:
    try:
     info=p.vtinfo(v)
     cands.append((lo+k,v,info['name']))
    except Exception: pass
  for c in cands: print(f'  ref {site:#x} vt_at {c[0]:#x} val {c[1]:#x} name {c[2]!r}')
