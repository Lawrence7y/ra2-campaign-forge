
import json,collections,time
from pathlib import Path
import pefile
ROOT=Path(r'D:\Project\ra2-campaign-forge')
EXE=ROOT/'ra2youli'/'gamemd.exe'
OUT=ROOT/'lead/next_re_20261117_r14/SURVEY_RING24'
raw=EXE.read_bytes()
pe=pefile.PE(data=raw, fast_load=True); ib=pe.OPTIONAL_HEADER.ImageBase
secs=[dict(name=s.Name.rstrip(b'\0').decode('latin1'),va=ib+s.VirtualAddress,vs=s.Misc_VirtualSize,rs=s.SizeOfRawData,ptr=s.PointerToRawData) for s in pe.sections]
by={s['name']:s for s in secs}
def va2off(va):
    for s in secs:
        if s['va']<=va<s['va']+s['rs']:
            o=s['ptr']+va-s['va']
            if o+4<=len(raw): return o
    return None
def u32(va):
    o=va2off(va)
    return int.from_bytes(raw[o:o+4],'little') if o is not None else None
def cstr(va,lim=200):
    o=va2off(va)
    if o is None: return ''
    b=raw[o:o+lim]; z=b.find(b'\0')
    if z>=0: b=b[:z]
    try: return b.decode('ascii')
    except: return ''
text=by['.text']; tva=text['va']; tlen=text['vs']
def in_text(v): return v is not None and tva<=v<tva+tlen
def is_col(p):
    col=u32(p)
    if col is None: return False
    td=u32(col+0xC)
    if td is None: return False
    return cstr(td+8).startswith(('.?AV','.?AU'))

lo=by['.rdata']['va']; hi=by['.data']['va']+by['.data']['rs']
vt={}
for s in (by['.rdata'],by['.data']):
    b=(s['va']+3)//4*4
    for p in range(b,s['va']+s['rs']-4,4):
        col=u32(p)
        if col is None or col<lo or col>hi: continue
        td=u32(col+0xC)
        if td is None: continue
        nm=cstr(td+8)
        if nm.startswith(('.?AV','.?AU')): vt[p+4]=nm
print('vtables',len(vt),flush=True)

e2s_old=collections.defaultdict(list); e2s_new=collections.defaultdict(list)
cut_stats=collections.Counter()
for base,cls in vt.items():
    k=0
    while k<700:
        v=u32(base+4*k)
        if v is None or not in_text(v) or v==0: break
        e2s_old[v].append([base,k,cls]); k+=1
    k=0
    while k<700:
        p=base+4*k
        if k>0 and is_col(p-4):   # a new vtable starts here -> stop
            cut_stats['next_col']+=1; break
        v=u32(p)
        if v is None or not in_text(v) or v==0: break
        e2s_new[v].append([base,k,cls]); k+=1
print('entries old',len(e2s_old),'new',len(e2s_new),'stop reasons',dict(cut_stats))
print('old total slots',sum(len(v) for v in e2s_old.values()),'new',sum(len(v) for v in e2s_new.values()))
print('lost entries',len(set(e2s_old)-set(e2s_new)))
json.dump({'old':{hex(k):v for k,v in e2s_old.items()},'new':{hex(k):v for k,v in e2s_new.items()}},
          open(OUT/'work'/'e2s_compare.json','w'),indent=0)
# S21 anchor
COV=ROOT/'lead/next_re_20261117_r14/COVERAGE/coverage.tsv'
ATL=ROOT/'lead/next_re_20261112_r10/W130_atlas/function_atlas.tsv'
lines=COV.read_text(encoding='utf-8-sig').splitlines(); hdr=lines[0].split(',')
cov=[]
for l in lines[1:]:
    if not l.strip(): continue
    q=l.split('\t'); q+=['']*(8-len(q)); cov.append(dict(zip(hdr,q[:8])))
al=ATL.read_text(encoding='utf-8-sig').splitlines(); ah=al[0].split('\t')
atlas={}
for l in al[1:]:
    if not l.strip(): continue
    q=l.split('\t'); q+=['']*(len(ah)-len(q)); r=dict(zip(ah,q))
    atlas[r['entry'].strip().upper().replace('0X','')]=r
def norm(e): return e.strip().upper().replace('0X','')
s21=[r for r in cov if r['subsystem'].strip().upper()=='S21' and r['grade'].strip()=='[静态推断]' and norm(r['entry']) in atlas]
for nm,e2s in (('old',e2s_old),('new',e2s_new)):
    print('S21 has2', nm, sum(1 for r in s21 if e2s.get(int(norm(r['entry']),16))))
