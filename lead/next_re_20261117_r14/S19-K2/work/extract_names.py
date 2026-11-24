#!/usr/bin/env python3
"""Extract precise naming evidence: EVA string->0x752700 sites, AudioController sub_ setters, PlayGlobal callees."""
import os,re,json,csv
import pefile
from capstone import *
from capstone.x86 import *
ROOT=r'D:\Project\ra2-campaign-forge'; EXE=os.path.join(ROOT,r'ra2youli\gamemd.exe')
pe=pefile.PE(EXE,fast_load=False); IB=pe.OPTIONAL_HEADER.ImageBase; data=open(EXE,'rb').read()
cov={}
with open(os.path.join(ROOT,r'lead\next_re_20261117_r14\COVERAGE\coverage.tsv'),encoding='utf-8') as f:
    for row in csv.DictReader(f,delimiter='\t'):
        cov[int(row['entry'],16)]=row['name']
def cstr(va,maxn=96):
    off=va-IB
    if off<0 or off>=len(data):return None
    b=data[off:off+maxn]; z=b.find(b'\0'); z=z if z>=0 else maxn; s=b[:z]
    return s.decode('ascii','replace') if len(s)>=3 and all(32<=c<127 for c in s) else None
md=Cs(CS_ARCH_X86,CS_MODE_32);md.skipdata=True;md.detail=True
EVA_CALL=0x752700
def find_eva_sites(va,size):
    raw=data[va-IB:va-IB+size]
    insns=list(md.disasm(raw,va))
    out=[]
    for i,ins in enumerate(insns):
        if ins.id==X86_INS_CALL and ins.op_str.strip().lower()==hex(EVA_CALL):
            # find nearest preceding mov ecx,<str> or push <str>
            ev=None; ev_ia=None
            for j in range(i-1,max(-1,i-12),-1):
                p=insns[j]
                if p.id==X86_INS_MOV and p.op_str.startswith('ecx,') and '0x' in p.op_str:
                    mm=re.search(r'0x([0-9a-fA-F]+)',p.op_str)
                    if mm:
                        s=cstr(int(mm.group(1),16))
                        if s and s.startswith('EVA_'):
                            ev=s; ev_ia=p.address; break
                if p.id==X86_INS_PUSH:
                    mm=re.search(r'0x([0-9a-fA-F]+)',p.op_str)
                    if mm:
                        s=cstr(int(mm.group(1),16))
                        if s and s.startswith('EVA_'):
                            ev=s; ev_ia=p.address; break
            out.append((ins.address,ev,ev_ia))
    return out
# EVA functions from evidence json
ev=json.load(open(os.path.join(ROOT,r'lead\next_re_20261117_r14\S19-K2\work\s19_evidence.json'),encoding='utf-8'))
atlas={}
with open(os.path.join(ROOT,r'lead\next_re_20261112_r10\W130_atlas\function_atlas.tsv'),encoding='utf-8') as f:
    for row in csv.DictReader(f,delimiter='\t'):
        atlas[row['entry'].upper()]=int(row['size'])
print('=== EVA trigger functions (string in ecx/push -> call 0x752700) ===')
for e,r in ev.items():
    if EVA_CALL in r['calls']:
        sites=find_eva_sites(int(e,16),atlas[e])
        strs=[x[2] for x in r['strops'] if x[2] and x[2].startswith('EVA_')]
        print(f"{e} {r['name']:<24} strs={len(strs)} EVA-sites={sites}")
print()
print('=== PlayGlobal 0x750920 direct callees ===')
pg=ev.get('00750920')
if pg:
    print('n_callees',len(pg['calls']))
    for t in pg['calls']:
        print(f'  0x{t:X} {cov.get(t,"sub_%X"%t)}')
print()
print('=== AudioController::sub_ functions - strings & callees ===')
for e,r in ev.items():
    if 'AudioController::sub_' in r['name']:
        print(f"{e} {r['name']} strs={[x[2] for x in r['strops'] if x[2]]}")
        print(f"   callees(top)={[ (hex(t),cov.get(t,'?')) for t in r['calls'][:12]]}")
