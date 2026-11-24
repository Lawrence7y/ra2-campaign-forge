#!/usr/bin/env python3
"""S10-K3 candidate census: fresh RTTI/vtables + coverage shapes; no atlas discovery."""
from pathlib import Path
import csv,json,struct,hashlib,collections
import pefile
ROOT=Path(r'D:\Project\ra2-campaign-forge'); CARD=ROOT/'lead/next_re_20261117_r14/S10_K3'
EXE=ROOT/'ra2youli/gamemd.exe'; COV=ROOT/'lead/next_re_20261117_r14/COVERAGE/coverage.tsv'
ATL=ROOT/'lead/next_re_20261112_r10/W130_atlas/function_atlas.tsv'
data=EXE.read_bytes(); pe=pefile.PE(str(EXE),fast_load=True); IB=pe.OPTIONAL_HEADER.ImageBase
secs=[]
for s in pe.sections:
 secs.append({'name':s.Name.rstrip(b'\0').decode('latin1'),'va':IB+s.VirtualAddress,'end':IB+s.VirtualAddress+max(s.Misc_VirtualSize,s.SizeOfRawData),'raw':s.PointerToRawData,'rsize':s.SizeOfRawData})
def off(va):
 for s in secs:
  if s['va']<=va<s['end']:
   d=va-s['va']
   if d<s['rsize']: return s['raw']+d
 return None
def u32(va):
 o=off(va); return None if o is None or o+4>len(data) else struct.unpack_from('<I',data,o)[0]
def b(n): return format(n,'08X')
with (CARD/'work/all_rtti.json').open(encoding='utf-8') as f: rj=json.load(f)
anchor=collections.defaultdict(list)
for v in rj['vtables']:
 for i,s in enumerate(v['slots']):
  anchor[s.upper()].append({'vt':v['vt_hex'],'col':v['col_hex'],'class':v['class'],'offset':v['offset'],'slot':i,'nslots':v['nslots']})
norm=lambda x:x.strip().lower()
cov=[r for r in csv.DictReader(COV.open('r',encoding='utf-8',newline=''),delimiter='\t') if r['subsystem'].strip().upper()=='S10']
atl={norm(r['entry']) for r in csv.DictReader(ATL.open('r',encoding='utf-8',newline=''),delimiter='\t')}
inter=[r for r in cov if norm(r['entry']) in atl]
lines=['S10-K3 CANDIDATE CENSUS','SHA256='+hashlib.sha256(data).hexdigest().upper(),'TD=%d COL=%d VT=%d SLOTS=%d ENUM=%d OK=%s'%(len(rj['tds']),len(rj['cols']),len(rj['vtables']),sum(v['nslots'] for v in rj['vtables']),len(rj['enum']),rj['enum_ok']),'S10_ROWS=%d ATLAS_INTER=%d'%(len(cov),len(inter))]
shape_count=collections.Counter(); b8c3=[]; anchored_b8c3=[]; nonproved_anchors=[]
for r in inter:
 e=r['entry'].strip().upper(); va=int(e,16); o=off(va)
 raw=data[o:o+16].hex() if o is not None else ''
 kind='OTHER'
 if len(raw)>=12 and raw[:2]=='b8' and raw[10:12]=='c3': kind='B8_IMM32_C3'
 elif len(raw)>=14 and raw[:2]=='b8' and raw[10:12]=='c2': kind='B8_IMM32_C2'
 shape_count[kind]+=1
 a=anchor.get(e,[])
 if r['grade'].strip()!='[已证]' and a: nonproved_anchors.append((r,a,kind,raw))
 rec={'entry':e,'grade':r['grade'].strip(),'name':r['name'].strip(),'kind':kind,'raw16':raw,'imm':struct.unpack_from('<I',data,o+1)[0] if kind.startswith('B8') else None,'anchors':a}
 if kind=='B8_IMM32_C3':
  b8c3.append(rec)
  if a: anchored_b8c3.append(rec)
lines.append('SHAPE_COUNTS='+repr(dict(shape_count)))
lines.append('B8_IMM32_C3_ROWS=%d ANCHORED=%d NONPROVED=%d'%(len(b8c3),len(anchored_b8c3),sum(x['grade']!='[已证]' for x in b8c3)))
lines.append('NONPROVED_VTABLE_ANCHORED_ROWS=%d'%len(nonproved_anchors))
lines.append('--- ALL B8_IMM32_C3 IN S10 ---')
for x in b8c3: lines.append('B8C3 '+json.dumps(x,ensure_ascii=False))
lines.append('--- NONPROVED B8_IMM32_C3 ---')
for x in b8c3:
 if x['grade']!='[已证]': lines.append('NONPROVED_B8C3 '+json.dumps(x,ensure_ascii=False))
lines.append('--- NONPROVED VT-ANCHORED WITH CLASS NAMES ---')
for r,a,k,raw in nonproved_anchors:
 lines.append('ANCH %s\t%s\t%s\t%s\t%s'%(r['entry'],r['grade'],r['name'],k,' | '.join('%s off=%d slot=%d/%d vt=%s col=%s'% (x['class'],x['offset'],x['slot'],x['nslots'],x['vt'],x['col']) for x in a)))
(CARD/'EVIDENCE/candidate_census.txt').write_text('\n'.join(lines)+'\n',encoding='utf-8')
(CARD/'work/candidate_census.json').write_text(json.dumps({'b8c3':b8c3,'anchored_b8c3':anchored_b8c3,'shape_count':shape_count},ensure_ascii=False,indent=2),encoding='utf-8')
print('\n'.join(lines[:12]))
