
import json,collections,csv
from pathlib import Path
import pefile
ROOT=Path(r'D:\Project\ra2-campaign-forge')
OUT=ROOT/'lead/next_re_20261117_r14/SURVEY_RING24'
raw=open(ROOT/'ra2youli'/'gamemd.exe','rb').read()
pe=pefile.PE(data=raw,fast_load=True); ib=pe.OPTIONAL_HEADER.ImageBase
secs=[dict(name=s.Name.rstrip(b'\0').decode('latin1'),va=ib+s.VirtualAddress,vs=s.Misc_VirtualSize,rs=s.SizeOfRawData,ptr=s.PointerToRawData) for s in pe.sections]
def va2off(va):
    for s in secs:
        if s['va']<=va<s['va']+s['rs']:
            o=s['ptr']+va-s['va']
            if o+4<=len(raw): return o
    return None
def u32(va):
    o=va2off(va)
    return int.from_bytes(raw[o:o+4],'little') if o is not None else None
idx=json.load(open(OUT/'work'/'index.json'))
installs={int(k,16):v for k,v in idx['installs'].items()}
livevt={int(k,16):v for k,v in idx['livevt'].items()}
rows=json.load(open(OUT/'work'/'rows2.json'))
unamb=set()
for e,wl in livevt.items():
    for g,vt,slot,inst,disp in wl:
        vts={v for v,s in installs.get(g,[])}
        vals={u32(v2+4*slot) for v2 in vts}; vals.discard(None)
        if len(vals)==1 and e in vals: unamb.add(e)
def hs(r): return r['n_direct_out']>0 or (r['n_livevt']>0 and int(r['entry'],16) in unamb)
def cls(r,strict,yrpp):
    a=r['has2_rtti'] or (yrpp and r['yrpp_conf'] and r['yrpp_conf']['ok'])
    b=hs(r) if strict else r['has4']
    return 'A' if a and b else ('B' if a else ('C' if b else 'D'))
with (OUT/'EVIDENCE'/'classification.tsv').open('w',encoding='utf-8',newline='') as f:
    w=csv.writer(f,delimiter='\t')
    w.writerow(['entry','subsystem','class_PRIMARY','class_loose4','class_yrpp','has2_rtti','has2_yrpp',
                'has4_loose','has4_strict','livevt_valid','n_direct_all','n_direct_out','n_livevt',
                'rtti_classes','rtti_vt','rtti_slot','ring4_direct_sites','ring4_livevt','yrpp_binding',
                'ext_lo','ext_hi','atlas_size','name'])
    for r in rows:
        yc=r['yrpp_conf']; e=int(r['entry'],16)
        w.writerow([r['entry'],r['sub'],cls(r,True,False),cls(r,False,False),cls(r,True,True),
            int(r['has2_rtti']),int(bool(yc and yc['ok'])),int(r['has4']),int(hs(r)),
            int(r['n_livevt']>0 and e in unamb),
            r['n_direct_all'],r['n_direct_out'],r['n_livevt'],
            ';'.join(r['rtti_cls']),r['rtti_vt'],r['rtti_slot'],
            ';'.join('%08X'%x for x in r['direct_out']),
            ';'.join('g%08X/vt%08X/s%d/inst%08X/disp%08X'%tuple(x) for x in r['livevt']),
            ('%s:%d %s %s'%(r['yrpp'][0],r['yrpp'][1],r['yrpp'][2],r['yrpp'][3])) if r['yrpp'] else '',
            '%08X'%r['ext_lo'],'%08X'%r['ext_hi'],r['size'],r['name']])
A=[r for r in rows if r['has2_rtti'] and hs(r)]
with (OUT/'EVIDENCE'/'A_samples.tsv').open('w',encoding='utf-8',newline='') as f:
    w=csv.writer(f,delimiter='\t'); w.writerow(['entry','subsystem','channel','rtti_class','vt','slot','ring4_site','name'])
    for r in [x for x in A if x['n_direct_out']>0][:20]:
        w.writerow([r['entry'],r['sub'],'direct',';'.join(r['rtti_cls']),r['rtti_vt'],r['rtti_slot'],'%08X'%r['direct_out'][0],r['name']])
    for r in [x for x in A if x['n_direct_out']==0][:5]:
        lv=r['livevt'][0]
        w.writerow([r['entry'],r['sub'],'livevt-unanimous',';'.join(r['rtti_cls']),r['rtti_vt'],r['rtti_slot'],
                    'install@%08X/dispatch@%08X/g%08X'%(lv[3],lv[4],lv[0]),r['name']])
# rejected livevt (ambiguous) samples -> transparency
rej=[r for r in rows if r['has2_rtti'] and r['n_direct_out']==0 and r['n_livevt']>0 and int(r['entry'],16) not in unamb]
with (OUT/'EVIDENCE'/'livevt_rejected_samples.tsv').open('w',encoding='utf-8',newline='') as f:
    w=csv.writer(f,delimiter='\t'); w.writerow(['entry','subsystem','g','installed_vt_set','slot','values_at_slot','name'])
    for r in rej[:15]:
        lv=r['livevt'][0]; g=lv[0]
        vts=sorted({v for v,s in installs.get(g,[])})
        vals=[u32(v+4*lv[2]) for v in vts]
        w.writerow([r['entry'],r['sub'],'%08X'%g,';'.join('%08X'%v for v in vts),lv[2],
                    ';'.join('%08X'%v if v else 'null' for v in vals),r['name']])
C=[r for r in rows if (not r['has2_rtti']) and hs(r)]
with (OUT/'EVIDENCE'/'C_samples.tsv').open('w',encoding='utf-8',newline='') as f:
    w=csv.writer(f,delimiter='\t'); w.writerow(['entry','subsystem','n_direct_out','n_livevt','yrpp','name'])
    for r in C[:20]: w.writerow([r['entry'],r['sub'],r['n_direct_out'],r['n_livevt'],'y' if r['yrpp'] else '',r['name']])
s=json.load(open(OUT/'work'/'summary.json'))
s.update(dict(A_primary_strict=len(A),A_loose=sum(1 for r in rows if r['has2_rtti'] and r['has4']),
  livevt_unanimous_entries=len(unamb),
  livevt_rejected=sum(1 for r in rows if r['has2_rtti'] and r['n_direct_out']==0 and r['n_livevt']>0 and int(r['entry'],16) not in unamb),
  totals=dict(n=len(rows),A=len(A),B=sum(1 for r in rows if r['has2_rtti'] and not hs(r)),
              C=len(C),D=sum(1 for r in rows if not r['has2_rtti'] and not hs(r)))))
json.dump(s, open(OUT/'work'/'summary.json','w'), ensure_ascii=False, indent=1)
print('A strict',len(A),'rejected livevt',s['livevt_rejected'],'C',len(C))
print('samples written')
