
import sys,json,random,re
import pefile
from capstone import *
exec(open(sys.argv[1],encoding='utf8').read().split("if __name__")[0])
p=r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe"
pe=pefile.PE(p);img=pe.OPTIONAL_HEADER.ImageBase
text=[s for s in pe.sections if s.Name.rstrip(b'\0')==b'.text'][0]
tva=img+text.VirtualAddress;tsz=text.SizeOfRawData
# full gate: candidate contract AND entry is a vtable slot value in .rdata with RTTI class + has vptr install
rawall=raw
# build set of all known slot entries with RTTI class from K8 registry
reg={}
for line in open(sys.argv[2],encoding='utf8'):
 m=re.match(r'([0-9A-F]{8}) ([0-9A-F]{8}) .* VT=([0-9A-F]{8}) SLOT=(\d+).*NAME=(\S+)',line.strip())
 if m: reg[int(m.group(2),16)]=(int(m.group(4)),m.group(5))
random.seed(20261118)
tried=0;passes=[];examples=[]
for _ in range(20000):
 va=tva+random.randrange(0,tsz-200)&~0xF
 if raw[off(va)] in (0xE8,0xE9,0xEB): continue
 if va not in reg: continue  # gate: must be a real vt slot
 tried+=1
 cls,txt=contract(va)
 # check slot agreement: map cls -> expected slot
 expected={'operator==':1,'GetItemIndex':5,'Clear':3,'FindItemIndex':4,'GetItem':6}
 if cls in expected and reg[va][0]==expected[cls]:
  passes.append((hex(va),cls))
  if len(examples)<5:examples.append((hex(va),cls))
print(json.dumps({'tried_vtslot':tried,'pass':len(passes),'examples':examples},indent=1))
