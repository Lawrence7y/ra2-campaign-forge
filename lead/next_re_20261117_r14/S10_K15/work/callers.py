import sys,collections
sys.path.insert(0,r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S10_K15\work")
import common
rows,cov,atl=common.load_rows()
targets=[int(x,16) for x in sys.argv[1:]]
found={t:[] for t in targets}
for k,r in atl.items():
 if k=='entry': continue
 a=int(k,16); size=int(r[1])
 for i in common.disasm(a,size):
  t=common.call_target(i)
  if t in found: found[t].append((i.address,a))
for t in targets:
 print('\n### CALLERS',f'{t:08X}')
 cr=cov.get(f'{t:08X}')
 print('TARGET',cr[1:5] if cr else None,'class_slots',common.class_at_slot(t))
 by=collections.defaultdict(list)
 for site,a in found[t]: by[a].append(site)
 for a,sites in sorted(by.items()):
  crr=cov.get(f'{a:08X}')
  print(f'  caller {a:08X} sites={[hex(x) for x in sites]}', (crr[1],crr[2],crr[4]) if crr else ('?', '?', '?'))
 print('TOTAL call sites',len(found[t]),'caller funcs',len(by))
