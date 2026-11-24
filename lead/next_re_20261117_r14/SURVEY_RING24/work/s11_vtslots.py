
import json,collections
from pathlib import Path
import pefile
ROOT=Path(r'D:\Project\ra2-campaign-forge')
OUT=ROOT/'lead/next_re_20261117_r14/SURVEY_RING24'
idx=json.load(open(OUT/'work'/'index.json'))
vt={int(k,16):v for k,v in idx['vtables'].items()}
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
slots={}
for base,cls in vt.items():
    k=0
    while k<700:
        v=u32(base+4*k)
        if v is None or not in_text(v) or v==0: break
        k+=1
    slots[base]=k
for b,k in sorted(slots.items(), key=lambda kv:-kv[1])[:10]:
    print('  ',hex(b),k,vt[b])
print('total slots',sum(slots.values()),'tables',len(slots))
for nm in ('.?AVAbstractClass@@','.?AVTechnoClass@@','.?AVObjectClass@@','.?AVBuildingClass@@'):
    print(nm,[(hex(b),slots[b]) for b,c in vt.items() if c==nm])
