import sys,struct
sys.path.insert(0,r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S10_K13\work')
import re_lib as R
for target in [0x739EC0,0x4D85D0,0x4D7330,0x517FA0,0x519630,0x741970,0x6FB010]:
 pat=struct.pack('<I',target); hits=[]
 for name,base,vsz,rsz,ptr in R.sections():
  if name not in ('.rdata','.data'):continue
  data=R.PE.__data__[ptr:ptr+rsz];pos=0
  while True:
   i=data.find(pat,pos)
   if i<0:break
   hits.append((name,base+i));pos=i+1
 print(f'{target:08X}',len(hits),','.join(f'{n}:{x:08X}' for n,x in hits[:20]))
