import sys
sys.path.insert(0,r"D:/Project/ra2-campaign-forge/lead/next_re_20261117_r14/S13_N1/work")
from re_lib import *
print('== vptr-like RTTI constants in residual bodies ==')
for k,c,a in residual_rows():
 vals=[]
 for i in fn_ins(k,int(a.get('size','512'))):
  try: ops=i.operands
  except Exception: continue
  for op in ops:
   if op.type==2 and BASE<=op.imm<BASE+0x1000000:
    nm=rtti_name_from_vt(op.imm)
    if nm: vals.append((i.address,op.imm,nm,i.mnemonic,i.op_str))
 if vals: print(f'{k:08X}',[(f'{a:08X}',f'{v:08X}',n,m,o) for a,v,n,m,o in vals])
print()
print('== known 00771C70 WeaponTypeClass ctor globals ==')
for i in dis(0x771C70,0x250):
 s=fmt(i)
 if '88756c' in s.lower() or '887578' in s.lower() or '7f73b8' in s.lower() or '258d0' in s.lower(): print(s)
print()
for lo,hi in [(0x46B350,0x46B390),(0x6CDAE0,0x6CDB10),(0x6E3480,0x6E34B0),(0x6E39B0,0x6E39E0)]:
 print('====',hex(lo),'====')
 for i in dis(lo,hi-lo): print(fmt(i))
