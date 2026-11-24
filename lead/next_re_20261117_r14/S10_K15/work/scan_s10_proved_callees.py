import sys,os,collections
sys.path.insert(0,r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S10_K15\work")
import common
rows,cov,atl=common.load_rows()
s10=[r for r in rows if len(r)>=8 and r[1]=='S10' and r[0].lower() in atl and r[4]!='[已证]']
out=[]
for r in s10:
 va=int(r[0],16); size=int(atl[r[0].lower()][1])
 ins=common.disasm(va,size)
 calls=common.direct_calls(ins)
 ctr=collections.Counter(t for a,t in calls)
 ex=[]
 for t,n in ctr.items():
  cr=cov.get(f'{t:08X}')
  if cr and cr[4]=='[已证]':
   ex.append((t,n,cr[2],cr[3][:70]))
 if ex:
  out.append((len(ex),len([e for e in ex if e[0] not in [int(x[0],16) for x in s10]]),r[0],r[2],r[4],size,ex))
out.sort(key=lambda x:(-x[0],-x[1],x[2]))
for a in out[:80]:
 print('\n',a[2],a[3],a[4],'size',a[5],'distinct proved callees',a[0])
 for t,n,nm,sm in sorted(a[6]): print(f'  {t:08X} x{n} {nm} :: {sm}')
