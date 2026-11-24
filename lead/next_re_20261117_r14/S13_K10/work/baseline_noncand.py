
import sys,json,random,re
import pefile
from capstone import *
exec(open(sys.argv[1],encoding='utf8').read().split("if __name__")[0])
p=r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe"
pe=pefile.PE(p);img=pe.OPTIONAL_HEADER.ImageBase
text=[s for s in pe.sections if s.Name.rstrip(b'\0')==b'.text'][0]
tva=img+text.VirtualAddress;tsz=text.SizeOfRawData
cand=set(int(x,16) for x in json.load(open(sys.argv[3],encoding='utf8'))['entries'])
random.seed(20261118)
tried=0;passes=[];examples=[]
for _ in range(20000):
 va=tva+random.randrange(0,tsz-200)&~0xF
 if raw[off(va)] in (0xE8,0xE9,0xEB) or va in cand: continue
 tried+=1
 cls,txt=contract(va)
 if cls!='other':
  passes.append((hex(va),cls))
  if len(examples)<8:examples.append((hex(va),cls,txt[:160]))
print(json.dumps({'tried_noncand':tried,'contract_pass':len(passes),'rate':len(passes)/tried,'examples':examples},indent=1))
