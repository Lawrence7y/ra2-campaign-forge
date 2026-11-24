
# -*- coding: utf-8 -*-
import json,struct,pefile
EXE=r'D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe'
blob=open(EXE,'rb').read(); pe=pefile.PE(EXE,fast_load=True); base=pe.OPTIONAL_HEADER.ImageBase
for s in pe.sections:
    if s.Name.rstrip(b'\x00')==b'.text':
        TVA=s.VirtualAddress+base; TPR=s.PointerToRawData; TRS=s.SizeOfRawData
text=blob[TPR:TPR+TRS]
rows=json.load(open(r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S03_CRITERION\work\rows.json'))
live=json.load(open(r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S03_CRITERION\work\liveness.json'))
atl=set()
for l in open(r'D:\Project\ra2-campaign-forge\lead\next_re_20261112_r10\W130_atlas\function_atlas.tsv',encoding='utf-8').read().split('\n')[1:]:
    if l.strip(): atl.add(l.split('\t')[0].upper())
D=r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S03_CRITERION'
# 1) per-site byte check (all 105 S03 rows with direct call)
lines=['entry\tsite\tbytes5\trel32\tsite+5+rel32\tmatch\tcaller\tcaller_grade\trow_grade']
for r in rows:
    for c in r['callers']:
        s=int(c['site'],16); raw=text[s-TVA:s-TVA+5]
        rel=struct.unpack_from('<i',raw,1)[0]; tgt=(s+5+rel)&0xFFFFFFFF
        lines.append('\t'.join([r['hex'],c['site'],raw.hex(' '),str(rel),'%08X'%tgt,'OK' if tgt==r['entry'] else 'MISMATCH',
            c['caller'] or '-', c['grade'] or '-', r['grade']]))
open(D+r'\EVIDENCE\direct_sites_bytecheck.tsv','w',encoding='utf-8').write('\n'.join(lines)+'\n')
print('sites rows',len(lines)-1)
# 2) full 194-row ring table
lines=['entry\tin_atlas\tgrade\tname\tnsources\tconflict\tring1_align16\tring1_first_byte\tring1_pred_is_term\tring1_inside_other\tring2_rtti\tring2_class\tslot\tvt\tvt_liveness\tring4_n_direct_sites\tring4_callers\tring4_has_proved_caller']
for r in rows:
    init=atl.__contains__(r['hex'])
    rt=r['rtti'][0] if r['rtti'] else None
    lines.append('\t'.join([r['hex'],'Y' if init else 'N',r['grade'],r['name'],r['nsrc'],r['conf'],
      'Y' if r['align16'] else 'N', r['first_byte'], 'Y' if r['pred_term'] else 'N', 'Y' if r['inside_other'] else 'N',
      'Y' if r['n_rtti']>0 else 'N', rt['cls'] if rt else '-', str(rt['slot']) if rt else '-', rt['vt'] if rt else '-',
      live.get(r['hex'],'none'), str(r['n_direct']),
      ','.join((c['caller'] or 'NULLFN')+':'+(c['grade'] or 'NULL') for c in r['callers']) or '-',
      'Y' if any(c['grade']=='[已证]' for c in r['callers']) else 'N']))
open(D+r'\EVIDENCE\rings_by_row.tsv','w',encoding='utf-8').write('\n'.join(lines)+'\n')
print('ring rows',len(lines)-1)
