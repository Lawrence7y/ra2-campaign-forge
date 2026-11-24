import sys,json,collections
sys.path.insert(0,r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S10_K15\work")
import common
rows,cov,atl=common.load_rows()
with open(r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S10_K15\work\callmap.json",encoding='utf-8') as f: cm={int(k,16):v for k,v in json.load(f).items()}
s10=[r for r in rows if len(r)>=8 and r[1]=='S10' and r[0].upper() in cov and r[0].lower() in atl and r[4]!='[已证]']
res=[]
for r in s10:
 a=int(r[0],16); size=int(atl[r[0].lower()][1])
 callers=cm.get(a,[])
 extcall=[c for c in callers if c[1]!=a]
 subs=collections.Counter()
 for site,ca in extcall:
  cr=cov.get(f'{ca:08X}')
  if cr: subs[cr[1]]+=1
 pcal=set()
 for i in common.disasm(a,size):
  t=common.call_target(i)
  if t is None: continue
  cr=cov.get(f'{t:08X}')
  if cr and cr[4]=='[已证]' and t!=a: pcal.add(t)
 score=(len(extcall),len(pcal))
 res.append((score,r[0],r[2],r[4],len(extcall),dict(subs),len(pcal)))
res.sort(key=lambda x:(-x[4],-x[6],x[1]))
for x in res[:100]:
 print(x[1],x[2],x[3],'callers',x[4],'subs',x[5],'proved_callees',x[6])
