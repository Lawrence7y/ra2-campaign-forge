
import json, struct, hashlib, collections, sys
from pathlib import Path
import pefile, capstone

ROOT=Path(r'D:\Project\ra2-campaign-forge')
EXE=ROOT/'ra2youli'/'gamemd.exe'
OUT=ROOT/'lead/next_re_20261117_r14/SURVEY_RING24'
raw=EXE.read_bytes(); ib=None
pe=pefile.PE(data=raw, fast_load=True); ib=pe.OPTIONAL_HEADER.ImageBase
secs=[]
for s in pe.sections:
    secs.append(dict(name=s.Name.rstrip(b'\0').decode('latin1'),
        va=ib+s.VirtualAddress, vs=s.Misc_VirtualSize, rs=s.SizeOfRawData, ptr=s.PointerToRawData))
print([(s['name'],hex(s['va']),s['vs'],s['rs']) for s in secs])
by={s['name']:s for s in secs}
def va2off(va):
    for s in secs:
        if s['va']<=va<s['va']+s['rs'] and s['ptr']+va-s['va']<len(raw):
            return s['ptr']+va-s['va']
    return None
def u32(va):
    o=va2off(va)
    if o is None or o+4>len(raw): return None
    return int.from_bytes(raw[o:o+4],'little')
def cstr(va,lim=200):
    o=va2off(va)
    if o is None: return ''
    b=raw[o:o+lim]; z=b.find(b'\0')
    if z>=0: b=b[:z]
    try: return b.decode('ascii')
    except: return ''
text=by['.text']; code=raw[text['ptr']:text['ptr']+text['vs']]; tva=text['va']; tend=tva+text['vs']
def in_text(v): return v is not None and tva<=v<tend
print('sections ok; text', hex(tva), text['vs'])
