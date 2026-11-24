"""For each S05 A-set entry: compute function extent (linear from entry until ret-then-pad,
bounded by atlas_size), detect ③b features (backedge, jumptable, errcode, guard chain,
ctor shape), and list ④ direct call sites (outside body, non-self-loop)."""
import sys, csv, pickle, struct
sys.path.insert(0, r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S05_KPROVED2\work")
from pe_helpers import *
from capstone import *
from capstone.x86 import *

MD = Cs(CS_ARCH_X86, CS_MODE_32); MD.detail=True; MD.skipdata=True
D = pickle.load(open(r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S05_KPROVED2\work\call_sites.pkl",'rb'))
call_sites, insns, addr2i = D['call_sites'], D['insns'], D['addr2i']

CLS = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\SURVEY_RING24\EVIDENCE\classification.tsv"
rows = list(csv.DictReader(open(CLS,encoding='utf-8'),delimiter='\t'))
A = [r for r in rows if r['subsystem']=='S05' and r['has2_rtti']=='1' and r['has4_strict']=='1']

# disasm a contiguous range using addr2i-indexed insns (instruction boundaries from full sweep)
def disasm_range(lo,hi):
    out=[]
    i=addr2i.get(lo)
    if i is None: return out
    for a,sz,m,o,b in insns[i:]:
        if a>=hi: break
        out.append((a,sz,m,o,b))
    return out

def analyze(r):
    e=int(r['entry'],16); sz=int(r['atlas_size'])
    body=disasm_range(e, e+sz)
    if not body: return None
    # features
    backedges=[]; jumptables=[]; errcmp=[]; getlasterror=[]; guards=[]
    vtwrites=[]; fieldwrites=0; ret_count=0; calls_out=[]
    for a,s,m,o,b in body:
        if m.startswith('ret'): ret_count+=1
        if m in ('jmp','je','jne','jz','jnz','ja','jae','jb','jbe','jg','jge','jl','jle','ja','jnb','jna','jo','jo','jp','jnp','js','jns','jo','jno','jecxz','loop','loope','loopne') or m.startswith('j'):
            # target parse
            t=None
            if o.startswith('0x'):
                try: t=int(o.split()[0],16)
                except: pass
            if t is not None and t<=a and e<=t<e+sz:
                backedges.append((a-e,m,t-e))
        # indirect jmp with index scale -> jumptable
        if m=='jmp' and ('*' in o or ('[' in o and 'reg' in o)):
            jumptables.append((a-e,o))
        if m=='call' and o.startswith('0x'):
            try: calls_out.append(int(o.split()[0],16))
            except: pass
        if m=='cmp' and ('-1' in o or '0xffffffff' in o.lower()):
            errcmp.append((a-e,o))
        # guard: cmp/test followed by jcc (track last cmp/test)
    # guard chain: consecutive cmp/test then jcc with distinct distinct targets
    last_flag=None
    for idx,(a,s,m,o,b) in enumerate(body):
        if m in ('cmp','test'):
            last_flag=(m,o,a-e)
        elif m.startswith('j') and m!='jmp' and last_flag:
            t=None
            if o.startswith('0x'):
                try: t=int(o.split()[0],16)
                except: pass
            guards.append((last_flag[2],last_flag[0],last_flag[1],a-e,m,t-e if t else None))
            last_flag=None
    # direct call sites externally
    ext_sites=[s for s in call_sites.get(e,[]) if not (e<=s<e+sz) and s!=e]
    return dict(entry=f'{e:08X}',name=r['name'],atlas_size=sz,nins=len(body),nret=ret_count,
                backedges=backedges,jumptables=jumptables,errcmp=errcmp,
                guards=guards,next_sites=len(ext_sites),ext_sites=[f'{s:X}' for s in ext_sites[:20]])

res=[]
for r in A:
    x=analyze(r)
    if x: res.append(x)

import json
json.dump(res,open(r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S05_KPROVED2\work\features.json",'w'),indent=1)

print(f"{'entry':8} {'nin':>5} {'ret':>3} {'back':>4} {'jt':>2} {'err':>3} {'grd':>3} {'dir':>4}  name")
for x in res:
    print(f"{x['entry']:8} {x['nins']:5} {x['nret']:3} {len(x['backedges']):4} {len(x['jumptables']):2} {len(x['errcmp']):3} {len(x['guards']):3} {x['next_sites']:4}  {x['name']}")
