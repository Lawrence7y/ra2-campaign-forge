import sys,re,collections
sys.path.insert(0,r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S10_K15\work")
import common
rows,cov,atl=common.load_rows()
for s in sys.argv[1:]:
 disp=int(s,0); pat=re.compile(r'\[\w+ \+ 0x'+f'{disp:x}'+r'\]')
 by=collections.defaultdict(list)
 for k,r in atl.items():
  if k=='entry': continue
  a=int(k,16); size=int(r[1])
  for i in common.disasm(a,size):
   if i.mnemonic=='call' and pat.search(i.op_str): by[a].append(i.address)
 print('\n###',hex(disp),'sites',sum(len(v) for v in by.values()),'funcs',len(by))
 for a,sites in sorted(by.items()):
  cr=cov.get(f'{a:08X}')
  print(f'{a:08X} sites={[hex(x) for x in sites]}', (cr[1],cr[2],cr[4]) if cr else ('?','?','?'))
