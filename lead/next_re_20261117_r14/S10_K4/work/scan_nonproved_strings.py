
from pathlib import Path
import csv,pefile,struct,re,collections
from capstone import Cs,CS_ARCH_X86,CS_MODE_32
ROOT=Path(r'D:\Project\ra2-campaign-forge')
EXE=ROOT/'ra2youli/gamemd.exe'; COV=ROOT/'lead/next_re_20261117_r14/COVERAGE/coverage.tsv'
data=EXE.read_bytes(); pe=pefile.PE(str(EXE),fast_load=True); IB=pe.OPTIONAL_HEADER.ImageBase
secs=[]
for s in pe.sections: secs.append((IB+s.VirtualAddress,IB+s.VirtualAddress+max(s.Misc_VirtualSize,s.SizeOfRawData),s.PointerToRawData,s.SizeOfRawData))
def off(va):
 for a,b,r,z in secs:
  if a<=va<b and va-a<z: return r+va-a
 return None
def rd(va,n):
 o=off(va); return None if o is None or o+n>len(data) else data[o:o+n]
def cstr(va,maxn=120):
 b=rd(va,maxn)
 if not b: return None
 b=b.split(b'\0')[0]
 if len(b)<3 or len(b)>=maxn: return None
 try: s=b.decode('latin1')
 except: return None
 if not all(32<=ord(ch)<127 for ch in s): return None
 return s
md=Cs(CS_ARCH_X86,CS_MODE_32); md.skipdata=True
rows=list(csv.DictReader(COV.open('r',encoding='utf-8',newline=''),delimiter='\t'))
s10=[r for r in rows if r['subsystem'].strip().upper()=='S10' and r['grade'].strip()!='[已证]']
print('NONPROVED_S10=%d'%len(s10))
interesting=re.compile(r'(?i)(mission|attack|guard|capture|sabot|harvest|repair|sell|construct|paradrop|spyplane|wait|unload|return|stop|open|missile|harmless|ambush|anim|unit|infantry|building|team|target|path|move|load|save|serialize|ini|error|assert)')
hits=[]
for r in s10:
 va=int(r['entry'].strip(),16); b=rd(va,2048)
 if not b: continue
 ins=list(md.disasm(b,va,count=600))
 strs=[]
 for it in ins:
  for tok in re.findall(r'0x([0-9a-fA-F]{6,8})',it.op_str):
   x=int(tok,16); s=cstr(x)
   if s and (interesting.search(s) or len(s)>8): strs.append((hex(it.address),hex(x),s))
  # direct call target near evidence funcs maybe
 if strs:
  hits.append((r['entry'].strip().upper(),r['grade'].strip(),r['name'].strip(),strs[:12]))
print('FUNCTIONS_WITH_STRINGS=%d'%len(hits))
for e,g,n,strs in hits:
 print('ENTRY %s %s %s'% (e,g,n))
 for a,x,s in strs: print('  %s -> %s %r'%(a,x,s[:100]))
