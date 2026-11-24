import csv,struct,pefile,collections
from pathlib import Path
from capstone import Cs,CS_ARCH_X86,CS_MODE_32
R=Path(r'D:\Project\ra2-campaign-forge'); EXE=R/'ra2youli/gamemd.exe'; data=EXE.read_bytes(); pe=pefile.PE(str(EXE),fast_load=True); IB=pe.OPTIONAL_HEADER.ImageBase
secs=[]
for s in pe.sections: secs.append((IB+s.VirtualAddress,IB+s.VirtualAddress+max(s.Misc_VirtualSize,s.SizeOfRawData),s.PointerToRawData,s.SizeOfRawData))
def at(va,n):
 for a,b,p,r in secs:
  if a<=va<b:
   d=va-a
   if d+n<=r:return data[p+d:p+d+n]
 return None
md=Cs(CS_ARCH_X86,CS_MODE_32); md.skipdata=True
def dis(va,n): 
 b=at(va,n); return [] if b is None else list(md.disasm(b,va,count=400))
cov=[r for r in csv.DictReader(open(R/'lead/next_re_20261117_r14/COVERAGE/coverage.tsv',encoding='utf-8',newline=''),delimiter='\t') if r['subsystem']=='S06']
atl={r['entry'].upper():r for r in csv.DictReader(open(R/'lead/next_re_20261112_r10/W130_atlas/function_atlas.tsv',encoding='utf-8',newline=''),delimiter='\t')}
anchors={0x485020:'GetContainedTiberiumValue',0x721A50:'TiberiumType_LoadRules',0x80A80:'ReduceTiberium',0x87190:'IncreaseTiberium',0x47C620:'CanThisExistHere',0x80510:'ConnectsToOverlay'}
out=[]
for r in cov:
 e=r['entry'].upper(); a=atl.get(e)
 if not a or r['grade'].strip()=='[已证]': continue
 va=int(e,16); sz=min(int(a['size']),2048); ins=dis(va,sz)
 calls=[]
 for it in ins:
  if it.mnemonic=='call' and it.op_str.startswith('0x'):
   t=int(it.op_str,16)
   if t in anchors: calls.append((hex(it.address),hex(t),anchors[t]))
 f44=sum(1 for it in ins if '+ 0x44]' in it.op_str or '+0x44]' in it.op_str)
 f11e=sum(1 for it in ins if '+ 0x11e]' in it.op_str.lower() or '+0x11e]' in it.op_str.lower())
 if calls or (f44 and f11e): out.append((e,r['grade'],r['name'],sz,len(ins),calls,f44,f11e))
print('behavior_probe_hits',len(out))
for x in out[:120]: print('\t'.join(map(str,x)))
