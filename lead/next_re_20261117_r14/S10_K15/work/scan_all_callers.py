import sys,collections,json
sys.path.insert(0,r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S10_K15\work")
import common
rows,cov,atl=common.load_rows()
callmap=collections.defaultdict(list)
for k,r in atl.items():
 if k=='entry': continue
 a=int(k,16); size=int(r[1])
 for i in common.disasm(a,size):
  t=common.call_target(i)
  if t is not None: callmap[t].append((i.address,a))
with open(r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S10_K15\work\callmap.json","w",encoding='utf-8') as f:
 json.dump({f'{k:08X}':v for k,v in callmap.items()},f)
print('targets',len(callmap),'calls',sum(len(v) for v in callmap.values()))
