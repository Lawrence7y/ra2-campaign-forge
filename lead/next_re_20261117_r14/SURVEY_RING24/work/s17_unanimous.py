
import json,collections
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
t=secs[0]
def in_text(v): return v is not None and t['va']<=v<t['va']+t['vs']
idx=json.load(open(OUT/'work'/'index.json'))
installs={int(k,16):v for k,v in idx['installs'].items()}
livevt={int(k,16):v for k,v in idx['livevt'].items()}
rows=json.load(open(OUT/'work'/'rows2.json'))
A=[r for r in rows if r['has2_rtti'] and r['has4']]

unamb=set(); amb=set()
for e,wl in livevt.items():
    for g,vt,slot,inst,disp in wl:
        vts={v for v,s in installs.get(g,[])}
        vals={u32(v2+4*slot) for v2 in vts}
        vals.discard(None)
        if len(vals)==1 and (e in vals): unamb.add(e)
        else: amb.add(e)
print('livevt entries: unanimous-slot', len(unamb), 'ambiguous', len(amb- unamb))
A2=[]
for r in A:
    e=int(r['entry'],16)
    if r['n_direct_out']>0 or e in unamb: A2.append(r)
print('A with unanimous-slot livevt =', len(A2), '(loose was', len(A),', direct-only 337)')
for s in [f'S{i:02d}' for i in range(1,22)]:
    a=sum(1 for r in A if r['sub']==s); b=sum(1 for r in A2 if r['sub']==s)
    if a or b: print(f'  {s} A_loose={a:3d} A_unanimous={b:3d}')
json.dump(['%08X'%int(r['entry'],16) for r in A2], open(OUT/'work'/'A_unanimous.json','w'), indent=0)
json.dump({'loose':len(A),'unanimous':len(A2),'unamb_entries':len(unamb)}, open(OUT/'work'/'A_variants.json','w'), indent=1)
