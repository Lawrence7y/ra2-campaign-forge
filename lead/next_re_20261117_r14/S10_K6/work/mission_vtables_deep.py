#!/usr/bin/env python3
import sys
sys.path.insert(0,r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S10_K6\work')
import re_lib as R
stubs={R.u32(0x7EDCC0+4*i) for i in range(129,157)}
res=[]
for s in sorted(stubs):
 for ref,best in R.find_vtable_containing(s,max_back=512):
  if best:
   base,col,rtti,slot=best
   res.append((s,ref,base,col,rtti,slot))
for s,ref,base,col,rtti,slot in res:
 print('%08X ref=%08X vbase=%08X col=%08X slot=%d rtti=%s'%(s,ref,base,col,slot,rtti[1]))
print('unique vtables',','.join('%08X'%x for x in sorted({x[2] for x in res})))
