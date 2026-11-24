
import sys,json,random,re
import pefile
from capstone import *
exec(open(sys.argv[1],encoding='utf8').read().split("if __name__")[0])
p=r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe"
pe=pefile.PE(p);img=pe.OPTIONAL_HEADER.ImageBase
text=[s for s in pe.sections if s.Name.rstrip(b'\0')==b'.text'][0]
tva=img+text.VirtualAddress;tsz=text.SizeOfRawData
random.seed(20261118)
tried=0;passes=[];examples=[]
for _ in range(2000):
 va=tva+random.randrange(0,tsz-200)&~0xF
 # require non-first-byte E8/E9/EB like K8 entry gate
 if raw[off(va)] in (0xE8,0xE9,0xEB): continue
 cls,txt=contract(va)
 tried+=1
 if cls!='other':
  passes.append((hex(va),cls))
  if len(examples)<5:examples.append((hex(va),cls,txt[:120]))
print(json.dumps({'tried':tried,'pass':len(passes),'rate':len(passes)/tried if tried else 0,'examples':examples},indent=1))
