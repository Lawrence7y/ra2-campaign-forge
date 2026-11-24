#!/usr/bin/env python3
"""Fresh non-specific B8 imm32 C3 counterexample scan across all RTTI vtables.

Uses COL+0xC->TD and TD+8 inline name, .rdata vtable[-1] delim; no atlas boundaries.
Focus: documented slot35/36 counterexamples Foot/Object/Radio/Mission/Techno,
and any slot returning 0x7FFFFFFF or .data address (.data base from PE).
"""
from pathlib import Path
import pefile,struct,re,json,hashlib,collections
ROOT=Path(r'D:\Project\ra2-campaign-forge'); EXE=ROOT/'ra2youli/gamemd.exe'; CARD=ROOT/'lead/next_re_20261117_r14/S11_K4'
d=EXE.read_bytes(); pe=pefile.PE(str(EXE),fast_load=True); IB=pe.OPTIONAL_HEADER.ImageBase
secs=[]
for s in pe.sections:
 secs.append({'name':s.Name.rstrip(b'\0').decode('latin1'),'va':IB+s.VirtualAddress,'end':IB+s.VirtualAddress+max(s.Misc_VirtualSize,s.SizeOfRawData),'raw':s.PointerToRawData,'rsize':s.SizeOfRawData})
def off(va):
 for s in secs:
  if s['va']<=va<s['end']:
   o=va-s['va']
   if o<s['rsize']: return s['raw']+o
 return None
def u32(va):
 o=off(va); return None if o is None else struct.unpack_from('<I',d,o)[0]
def cstr(va,n=200):
 o=off(va)
 if o is None: return None
 b=d[o:o+n]; z=b.find(b'\0')
 if z<0: return None
 try: return b[:z].decode('ascii')
 except: return None
def in_sec(va,name):
 s=next((x for x in secs if x['name']==name),None); return bool(s and s['va']<=va<s['end'])
def hx(x): return f'{x:08X}'
# all TDs with inline .?A names
tds={}
for s in secs:
 if s['rsize']<=0: continue
 st=s['raw']; en=min(len(d),st+s['rsize'])
 for m in re.finditer(rb'\.\?A[VU][A-Za-z0-9_?@$]{0,180}@@\x00',d[st:en]):
  nva=s['va']+(m.start()); name=m.group()[:-1].decode('ascii'); td=nva-8
  pvf=u32(td)
  if pvf is None or not in_sec(pvf,'.rdata'): continue
  if u32(td+4)!=0 or cstr(nva)!=name: continue
  tds[td]=name
# COLs
cols={}
for s in secs:
 if s['rsize']<=0: continue
 st=s['raw']; en=min(len(d),st+s['rsize'])
 for rel in range(0,en-st-3,4):
  val=struct.unpack_from('<I',d,st+rel)[0]
  if val in tds:
   va=s['va']+rel; col=va-0xC
   if in_sec(col,'.rdata') and u32(col)==0 and u32(col+0xC)==val:
    cols[col]=(tds[val],u32(col+4))
# vtable slots from .rdata refs to COL
hits=[]; nvt=0; nslots=0
rd=next(s for s in secs if s['name']=='.rdata')
for rel in range(0,rd['rsize']-3,4):
 va=rd['va']+rel; val=struct.unpack_from('<I',d,rd['raw']+rel)[0]
 if val not in cols: continue
 cname,off0=cols[val]; vt=va+4; nvt+=1
 slots=[]
 while True:
  f=u32(vt+4*len(slots))
  if f is None or not in_sec(f,'.text'): break
  slots.append(f)
  if len(slots)>400: break
 nslots+=len(slots)
 for i,f in enumerate(slots):
  b=bytes_at=off(f)
  if b is None: continue
  raw=d[b:b+6]
  if len(raw)>=6 and raw[0]==0xB8 and raw[5]==0xC3:
   imm=struct.unpack_from('<I',raw,1)[0]
   hits.append({'class':cname,'offset':off0,'slot':i,'entry':hx(f),'imm':imm,'imm_hex':hx(imm),'vtable':hx(vt),'col':hx(val)})
lines=[]
lines.append('ALL_RTTI_VTABLE_B8_IMM32_C3_SCAN')
lines.append('TD_COUNT=%d COL_COUNT=%d VTABLE_COUNT=%d SLOTS=%d'%(len(tds),len(cols),nvt,nslots))
lines.append('B8_IMM32_C3_ANCHORED_HITS=%d'%len(hits))
data_base=IB+pe.OPTIONAL_HEADER.SectionAlignment*0 # informational only
for key in ['FootClass','ObjectClass','RadioClass','MissionClass','TechnoClass']:
 sel=[h for h in hits if key in h['class'] and h['slot'] in (35,36)]
 lines.append('COUNTEREXAMPLE_CLASS=%s SLOT35_36_HITS=%d'%(key,len(sel)))
 for h in sel: lines.append('  '+json.dumps(h,ensure_ascii=False))
# shared stub
sel=[h for h in hits if h['entry']=='004C9150']
lines.append('SHARED_STUB_4C9150_ANCHORED_HITS=%d'%len(sel))
for h in sel[:50]: lines.append('  '+json.dumps(h,ensure_ascii=False))
(CARD/'work/shape_counterexamples.json').write_text(json.dumps(hits,indent=2),encoding='utf-8')
(CARD/'EVIDENCE/shape_counterexamples.txt').write_text('\n'.join(lines)+'\n',encoding='utf-8')
print('\n'.join(lines[:80]))
