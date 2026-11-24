import json,re,struct,pefile,collections
from capstone import Cs,CS_ARCH_X86,CS_MODE_32
from pathlib import Path
R=Path(r'D:\Project\ra2-campaign-forge'); data=(R/'ra2youli/gamemd.exe').read_bytes(); pe=pefile.PE(str(R/'ra2youli/gamemd.exe'),fast_load=True); IB=pe.OPTIONAL_HEADER.ImageBase
secs=[(IB+s.VirtualAddress,IB+s.VirtualAddress+max(s.Misc_VirtualSize,s.SizeOfRawData),s.PointerToRawData,s.SizeOfRawData) for s in pe.sections]
def at(va,n):
 for va0,va1,ptr,rs in secs:
  if va0<=va<va1:
   d=va-va0
   if d+n<=rs: return data[ptr+d:ptr+d+n]
 return None
md=Cs(CS_ARCH_X86,CS_MODE_32); md.skipdata=True
def dis(va,n=192,c=100):
 b=at(va,n); return [] if b is None else list(md.disasm(b,va,count=c))
j=json.load(open(R/'lead/next_re_20261117_r14/S06_K4/work/all_rtti.json',encoding='utf-8'))
fac=[v for v in j['vtables'] if 'TClassFactory' in v['class']]
cnt=collections.Counter()
for v in fac:
 ci=int(v['slots'][3],16)
 for it in dis(ci):
  if it.mnemonic=='call' and it.op_str.startswith('0x'):
   cnt[int(it.op_str,16)]+=1
print('callcounts',cnt.most_common(10))
newt=cnt.most_common(1)[0][0]
names=['CellClass','IsometricTileClass','IsometricTileTypeClass','OverlayClass','OverlayTypeClass','SmudgeClass','SmudgeTypeClass','TerrainClass','TerrainTypeClass','TiberiumClass','TubeClass','WaypointPathClass']
for n in names:
 facv=next((v for v in fac if n in v['class']),None)
 if not facv: print(n,'NOFACTORY'); continue
 ci=int(facv['slots'][3],16); ins=dis(ci)
 idx=next((i for i,it in enumerate(ins) if it.mnemonic=='call' and it.op_str.startswith('0x') and int(it.op_str,16)==newt),-1)
 push=None
 if idx>=0:
  for it in reversed(ins[:idx]):
   if it.mnemonic=='push':
    try: push=(it.address,it.bytes.hex(),int(it.op_str,16)); break
    except: pass
   if it.mnemonic=='call': break
 # ctor after new: first call after new that writes canonical vtable address
 vt0=next((v['vt_hex'] for v in j['vtables'] if v['class']=='.?AV'+n+'@@' and v['offset']==0),None)
 ctor=None
 if idx>=0 and vt0:
  for it in ins[idx+1:]:
   if it.mnemonic=='call' and it.op_str.startswith('0x'):
    try: t=int(it.op_str,16)
    except: continue
    writes=[hex(x.address) for x in dis(t,384,240) if x.mnemonic=='mov' and ('0x'+vt0.lower()) in x.op_str.lower() and '[' in x.op_str]
    if writes: ctor=(t,writes[:3]); break
 # get canonical slot12
 cv=next((v for v in j['vtables'] if v['class']=='.?AV'+n+'@@' and v['offset']==0),None)
 s12=None
 if cv and len(cv['slots'])>12: s12=cv['slots'][12]
 print(n,'vt0',vt0,'s12',s12,'ci',hex(ci),'new',hex(newt),'push',push,'ctor',ctor)
