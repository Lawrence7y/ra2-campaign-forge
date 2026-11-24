
import sys,os,re,collections
sys.path.insert(0,os.path.dirname(__file__)); import common,k16
for disp in [0x40c,0x410,0x414,0x418,0x41c,0x420,0x424,0x3d4]:
 pat=re.compile(r'\[\w+ \+ 0x'+f'{disp:x}'+r'\]')
 hits=[]
 for a,size in k16.FUNCS:
  ins=common.disasm(a,size)
  for j,i in enumerate(ins):
   if i.mnemonic=='call' and pat.search(i.op_str): hits.append((i.address,a,j,ins))
 by=collections.defaultdict(list)
 for site,a,j,ins in hits: by[a].append((site,j,ins))
 print('\n### DISP',hex(disp),'sites',len(hits),'funcs',len(by))
 for a,lst in sorted(by.items()):
  cr=k16.row(a)
  print(' CALLER',f'{a:08X}',cr[2] if cr else '?',cr[4] if cr else '?','sites',[f'{s:08X}' for s,j,_ in lst])
  for site,j,ins in lst[:2]:
   for p in ins[max(0,j-4):j+2]: print('   ',common.fmt(p))
