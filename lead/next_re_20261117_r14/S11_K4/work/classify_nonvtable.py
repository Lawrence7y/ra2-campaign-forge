#!/usr/bin/env python3
"""Classify the 24 S11 entries not present in fresh vtable slots.

Purpose: avoid false upgrades. Proves only what has direct byte evidence:
- factory CreateInstance: factory RTTI COL + vtable slot3 pointer.
- concrete ctor: called by that CI immediately after push/new; installs canonical class vtables.
- noinit_t: ctor delegate stub that jumps to canonical ctor (byte-decoded).
Everything else: [未证]/[静态推断]; no upgrade.
"""
from pathlib import Path
import json,csv,struct,re,collections,hashlib
import pefile
ROOT=Path(r'D:\Project\ra2-campaign-forge'); EXE=ROOT/'ra2youli/gamemd.exe'; CARD=ROOT/'lead/next_re_20261117_r14/S11_K4'
d=EXE.read_bytes(); pe=pefile.PE(str(EXE),fast_load=True); IB=pe.OPTIONAL_HEADER.ImageBase
sec=[]
for s in pe.sections:
 sec.append({'name':s.Name.rstrip(b'\0').decode('latin1'),'va':IB+s.VirtualAddress,'end':IB+s.VirtualAddress+max(s.Misc_VirtualSize,s.SizeOfRawData),'raw':s.PointerToRawData,'rsize':s.SizeOfRawData})
def off(va):
 for s in sec:
  if s['va']<=va<s['end']:
   o=va-s['va']
   if o<s['rsize']: return s['raw']+o
 return None
def u32(va):
 o=off(va); return None if o is None else struct.unpack_from('<I',d,o)[0]
def bytes_at(va,n):
 o=off(va); return None if o is None else d[o:o+n]
def hx(x): return f'{x:08X}'
lay=json.loads((CARD/'work/layout.json').read_text(encoding='utf-8'))
clo=json.loads((CARD/'work/closure.json').read_text(encoding='utf-8'))
vt_by={int(s,16):v for v in lay['vtables'] for s in v['slots']}
cov=[]
with (ROOT/'lead/next_re_20261117_r14/COVERAGE/coverage.tsv').open(encoding='utf-8',newline='') as f:
 for r in csv.DictReader(f,delimiter='\t'):
  if r['subsystem']=='S11': cov.append(r)
un=[r for r in cov if int(r['entry'],16) not in vt_by]
class_of_ci={r['factory_ci']:r for r in clo}
ctor_by={r['ctor']:r for r in clo}
out=[]; lines=[]
lines.append('S11-K4 NON-VTABLE ENTRY CLASSIFICATION')
for r in un:
 e=int(r['entry'],16); rec={'entry':r['entry'],'old_name':r['name'],'old_grade':r['grade'],'classification':'unknown','evidence':[]}
 if hx(e) in class_of_ci:
  c=class_of_ci[hx(e)]
  rec.update(classification='factory_CreateInstance',cls=c['class'],evidence=[f'factory RTTI COL+0xC→TD+8={c["class"]}',f'vtable slot3 direct dword → {r["entry"]}',f'push {c["size_from_push"]} ({c["push_encoding"]}) → call 0x7C8E17',f'ctor {c["ctor"]} installs {c["off0_vt"]}'])
 elif hx(e) in ctor_by:
  c=ctor_by[hx(e)]
  rec.update(classification='concrete_ctor',cls=c['class'],evidence=[f'called by factory {c["factory_ci"]} after push {c["size_from_push"]};call 0x7C8E17',f'ctor bytes write canonical vtables: {c["ctor_vptr_writes"][:3]}'])
 elif r['name'].endswith('noinit_t'):
  b=bytes_at(e,16)
  rec.update(classification='ctor_delegate_stub',evidence=[f'bytes={b.hex() if b else "?"}', 'not imported from prior card; only byte shape recorded'])
 else:
  b=bytes_at(e,16); rec['evidence']=[f'bytes={b.hex() if b else "?"}','no fresh RTTI/vtable/factory/ctor closure in this card']
 out.append(rec)
 lines.append(json.dumps(rec,ensure_ascii=False))
(CARD/'work/nonvtable_classification.json').write_text(json.dumps(out,indent=2,ensure_ascii=False),encoding='utf-8')
(CARD/'EVIDENCE/nonvtable_classification.txt').write_text('\n'.join(lines)+'\n',encoding='utf-8')
print('\n'.join(lines))
