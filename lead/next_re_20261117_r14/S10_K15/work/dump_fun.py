import sys,collections
sys.path.insert(0,r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S10_K15\work")
import common
rows,cov,atl=common.load_rows()
for s in sys.argv[1:]:
 a=int(s,16); key=f'{a:08X}'.lower()
 size=int(atl[key][1]) if key in atl else 0x100
 print('\n###',f'{a:08X}','size',size,'class_slots',common.class_at_slot(a))
 cr=cov.get(f'{a:08X}')
 if cr: print('COV','\t'.join(cr[:5]))
 ins=common.disasm(a,size)
 for i in ins:
  line=common.fmt(i)
  t=common.call_target(i)
  if t is not None:
   r=cov.get(f'{t:08X}')
   if r: line+='    ; '+r[2]
  print(line)
