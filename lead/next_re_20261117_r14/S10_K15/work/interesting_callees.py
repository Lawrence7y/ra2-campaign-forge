import sys,json,collections
sys.path.insert(0,r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S10_K15\work")
import common
rows,cov,atl=common.load_rows()
with open(r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S10_K15\work\callmap.json",encoding='utf-8') as f: cm={int(k,16):v for k,v in json.load(f).items()}
targets=[int(x,16) for x in sys.argv[1:]]
s10=[r for r in rows if len(r)>=8 and r[1]=='S10' and r[0].lower() in atl]
for t in targets:
 print('\n### CALLEE',f'{t:08X}',cov.get(f'{t:08X}',[None]*5)[2:5])
 for r in s10:
  a=int(r[0],16); size=int(atl[r[0].lower()][1])
  sites=[i.address for i in common.disasm(a,size) if common.call_target(i)==t]
  if sites:
   print(f' {r[0]} {r[2]} {r[4]} sites={[hex(x) for x in sites]} callers={len(cm.get(a,[]))}')
