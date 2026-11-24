import sys,struct
from pathlib import Path
sys.path.insert(0,r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S10_K13\work')
import re_lib as R
name,base,vsz,rsz,ptr=[s for s in R.sections() if s[0]=='.text'][0]
data=R.PE.__data__[ptr:ptr+rsz]
needles=[
 ('CMP_WHATAMI_2', bytes.fromhex('8b06 8bce ff502c 83f802'.replace(' ',''))),
 ('CALL_6FDD50', bytes.fromhex('e8')+struct.pack('<i',0x6FDD50-(0+5))),
 ('WRITE_140', bytes.fromhex('898140010000')),
 ('WRITE_144', bytes.fromhex('898144010000')),
]
for nm,pat in needles:
 hits=[];pos=0
 while True:
  i=data.find(pat,pos)
  if i<0:break
  hits.append(base+i);pos=i+1
 print(nm,len(hits),','.join(f'{x:08X}' for x in hits[:50]))
