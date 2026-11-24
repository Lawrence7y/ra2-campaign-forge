"""CFG-based function extent + ③b feature extraction on reachable instructions only.
Writes per-entry evidence data. Card S05-KPROVED3."""
import sys, pickle, csv, json, struct
sys.path.insert(0, r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S05_KPROVED3\work")
from pe_helpers import *
from capstone import *
from capstone.x86 import *

MD = Cs(CS_ARCH_X86, CS_MODE_32); MD.detail=True; MD.skipdata=True
D = pickle.load(open(r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S05_KPROVED3\work\call_sites.pkl",'rb'))
call_sites, insns, addr2i = D['call_sites'], D['insns'], D['addr2i']

def insn_at(a):
    i=addr2i.get(a)
    if i is None: return None
    return insns[i]

def cfg_extent(entry, cap=6000):
    seen=set(); work=[entry]; out=[]
    while work and len(seen)<cap:
        a=work.pop()
        if a in seen: continue
        x=insn_at(a)
        if x is None: continue
        seen.add(a); out.append(x)
        aa,sz,m,o,b=x
        nxt=aa+sz
        tgt=None
        if o.startswith('0x'):
            try: tgt=int(o.split()[0],16)
            except: pass
        if m.startswith('ret'): continue
        if m=='jmp':
            if tgt is not None: work.append(tgt)
            continue
        if m.startswith('j'):
            if tgt is not None: work.append(tgt)
            work.append(nxt); continue
        if m.startswith('call'):
            work.append(nxt); continue
        work.append(nxt)
    return sorted(out)

CC={'je','jne','jz','jnz','ja','jae','jb','jbe','jg','jge','jl','jle','jo','jno','jp','jnp','js','jns','jecxz','loop','loope','loopne'}

def features(entry, body):
    e=entry
    backedges=[]; jumptables=[]; errcmp=[]; guards=[]; calls=[]
    writeloop=[]   # memory writes and their offsets (for M7 loop write check)
    for a,s,m,o,b in body:
        if (m in CC or m=='jmp') and o.startswith('0x'):
            try: t=int(o.split()[0],16)
            except: t=None
            if t is not None and t<=a and e<=t:
                backedges.append((a-e,m,t-e))
        if m=='jmp' and '*' in o:
            jumptables.append((a-e,o))
        if m.startswith('call') and o.startswith('0x'):
            try: calls.append(int(o.split()[0],16))
            except: pass
        if m=='cmp' and ('-1' in o or '0xffffffff' in o.lower()):
            errcmp.append((a-e,o))
        # explicit memory write: mov [mem], reg/imm  (capstone op_str contains 'ptr' and comma)
        if m in ('mov','movzx','movsx','stos','stosd','and','or','add','sub','inc','dec','xor') and 'ptr' in o and ',' in o:
            # heuristic: destination is memory -> op_str starts with 'dword ptr'/'byte ptr'/'word ptr'
            if o.strip().lower().startswith(('dword ptr','byte ptr','word ptr','qword ptr')):
                writeloop.append((a-e,m,o))
    last=None
    for a,s,m,o,b in body:
        if m in ('cmp','test'): last=(m,o,a-e)
        elif m in CC and last:
            t=None
            if o.startswith('0x'):
                try: t=int(o.split()[0],16)
                except: pass
            guards.append((last[2],last[0],last[1],a-e,m,t-e if t else None))
            last=None
    return dict(backedges=backedges,jumptables=jumptables,errcmp=errcmp,guards=guards,calls=sorted(set(calls)),memwrites=writeloop)

CLS = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\SURVEY_RING24\EVIDENCE\classification.tsv"
rows = list(csv.DictReader(open(CLS,encoding='utf-8'),delimiter='\t'))
A = [r for r in rows if r['subsystem']=='S05' and r['has2_rtti']=='1' and r['has4_strict']=='1']

allres={}
for r in A:
    e=int(r['entry'],16)
    body=cfg_extent(e)
    fe=features(e,body)
    lo=body[0][0]; hi=max(a+s for a,s,m,o,b in body)
    ext_sites=[s for s in call_sites.get(e,[]) if not (lo<=s<hi) and s!=e]
    allres[f'{e:08X}']=dict(name=r['name'],nins=len(body),lo=f'{lo:08X}',hi=f'{hi:08X}',
                             features=fe,ext_site_count=len(ext_sites),ext_sites=[f'{s:08X}' for s in ext_sites],
                             body=[[f'+0x{a-e:04X}',m,o,b.hex()] for a,s,m,o,b in body])
    print(f"{e:08X} nins={len(body):5} ext=+0x{hi-e:04X} back={len(fe['backedges']):2} jt={len(fe['jumptables'])} err={len(fe['errcmp']):2} grd={len(fe['guards']):3} wr={len(fe['memwrites']):3} dir={len(ext_sites):3}  {r['name']}")

json.dump(allres,open(r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S05_KPROVED3\work\cfg_features.json",'w'),indent=1)
