
import sys,os
sys.path.insert(0,os.path.dirname(__file__)); import common,k16
for a,size in k16.FUNCS:
 if 0x701000<=a<0x702000:
  r=k16.row(a)
  print(f'{a:08X} size={size:5}', (r[1],r[2],r[4]) if r else ('-','-','-'), 'slots',[(x[0],x[3]) for x in k16.cls(a)][:8])
