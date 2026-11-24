import sys,re,collections
sys.path.insert(0,r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S10_K15\work")
import common
rows,cov,atl=common.load_rows()
slots=[int(x,0) for x in sys.argv[1:]]
for disp in slots:
 print('\n### VCALL disp',hex(disp))
 pat=re.compile(r'\[\w+ \+ 0x'+f'{disp:x}'+r'\]')
 hits=[]
 for k,r in atl.items():
  if k=='entry': continue
  a=int(k,16); size=int(r[1]); ins=common.disasm(a,size)
  for j,i in enumerate(ins):
   if i.mnemonic=='call' and pat.search(i.op_str):
    hits.append((i.address,a,j,ins))
 by=collections.defaultdict(list)
 for site,a,j,ins in hits: by[a].append((site,j,ins))
 for a,lst in sorted(by.items()):
  cr=cov.get(f'{a:08X}')
  print(' caller',f'{a:08X}',(cr[1],cr[2],cr[4]) if cr else ('?','?','?'),'sites',[hex(x[0]) for x in lst])
  for site,j,ins in lst[:3]:
   for p in ins[max(0,j-5):j+2]: print('   ',common.fmt(p))
 print('TOTAL sites',len(hits),'funcs',len(by))
