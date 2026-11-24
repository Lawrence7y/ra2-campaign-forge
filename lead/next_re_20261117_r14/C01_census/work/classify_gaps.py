"""Final atlas_gaps classifier: decide true function entries among non-covered targets.
Criteria for TRUE gap function entry:
  A) target not in atlas entries AND not inside any atlas function interval
  B) has a plausible prologue in first instructions
  C) EITHER a direct call target (E8), OR preceded (linear) by a terminator ret/jmp
Output final atlas_gaps.tsv (call-target gaps + high-confidence jmp-target gaps),
and EVIDENCE/atlas_gap_candidates.tsv with all 45 + verdict.
"""
import os, json, bisect
import pefile, capstone
HERE=os.path.dirname(os.path.abspath(__file__))
BASE=os.path.abspath(os.path.join(HERE,'..'))
PROJECT=os.path.abspath(os.path.join(HERE,'..','..','..','..'))
EVID=os.path.join(BASE,'EVIDENCE')
EXE=os.path.join(PROJECT,'ra2youli','gamemd.exe')
ATLAS=os.path.join(PROJECT,'lead','next_re_20261112_r10','W130_atlas','function_atlas.tsv')
TAB=chr(9)
pe=pefile.PE(EXE,fast_load=True); IB=pe.OPTIONAL_HEADER.ImageBase
secs=[]
for s in pe.sections:
    nm=s.Name.decode(errors='replace').rstrip('\x00'); va=IB+s.VirtualAddress
    secs.append(dict(name=nm,va=va,raw=s.PointerToRawData,rawsize=s.SizeOfRawData))
text=next(s for s in secs if s['name']=='.text'); DATA=pe.__data__
md=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32); md.detail=True; md.skipdata=True
with open(ATLAS,encoding='utf-8',errors='replace') as f: lines=f.read().splitlines()
rows=[]
for ln in lines[1:]:
    p=ln.split(TAB)
    if len(p)<9: continue
    try: e=int(p[0],16)
    except: continue
    rows.append((e,e+int(p[1]),p[0],int(p[1])))
rows.sort(); starts=[r[0] for r in rows]; ends=[r[1] for r in rows]
def readva(va,n):
    off=text['raw']+(va-text['va']); return DATA[off:off+n]
def linear(va,n=64):
    out=[]
    for insn in md.disasm(readva(va,n),va):
        if insn.id==0: continue
        out.append(insn)
    return out
def prologue(insns):
    seq=[(i.mnemonic,i.op_str) for i in insns[:6]]
    # classic prologues
    mn=[m for m,_ in seq]
    if mn and mn[0]=='push' and mn[0:1]==['push']:
        npush=sum(1 for m in mn[:5] if m=='push')
        if npush>=2: return 'push-regs'
    if mn and mn[0]=='sub' and seq[0][1].startswith('esp,'): return 'sub-esp'
    if mn and mn[0]=='mov' and seq[0][1]=='edi, edi': return 'hotpatch'
    if mn and mn[0]=='push' and mn[1:2]==['ebp']: return 'push-ebp'
    return ''
def prev_terminator(target):
    """Find the last real instruction starting strictly before target in a window,
    linear from target-64. Return (mnem, addr) or None."""
    start=target-96
    if start<text['va']: start=text['va']
    last=None
    for insn in md.disasm(readva(start,target-start+4),start):
        if insn.id==0: continue
        if insn.address>=target: break
        last=insn
    if last and (last.mnemonic.startswith('ret') or last.mnemonic=='jmp'):
        return (last.mnemonic,last.address)
    return None

d=json.load(open(os.path.join(EVID,'atlas_gaps_full.json'),encoding='utf-8'))
notcov=[x for x in d['gaps'] if not x['inside_atlas']]
results=[]
for x in notcov:
    t=x['target']
    insns=linear(t)
    pro=prologue(insns)
    pt=prev_terminator(t)
    iscall=x['ncall']>0
    # verdict
    if iscall and pro:
        verdict='TRUE_FUNC_ENTRY'; conf='high'
    elif iscall and not pro:
        verdict='CALL_TARGET_NO_PROLOGUE'; conf='med'
    elif pro and pt:
        verdict='LIKELY_FUNC_ENTRY'; conf='med'
    elif pro and not pt:
        verdict='PROLOGUE_NO_TERM'; conf='low'
    else:
        verdict='MID_FUNC_JMP'; conf='low'
    results.append(dict(target=t, ncall=x['ncall'], njmp=x['njmp'], prologue=pro,
                        prev_term=('%s@%08X'%pt if pt else ''), verdict=verdict, conf=conf,
                        body=' ; '.join('%s %s'%(i.mnemonic,i.op_str) for i in insns[:5]),
                        call_sites=x['call_sites'][:8], jmp_sites=x['jmp_sites'][:8]))
# Write all candidates TSV
with open(os.path.join(EVID,'atlas_gap_candidates.tsv'),'w',encoding='utf-8') as f:
    f.write('target\tncall\tnjmp\tprologue\tprev_term\tverdict\tconf\tbody\n')
    for r in results:
        f.write('%08X\t%d\t%d\t%s\t%s\t%s\t%s\t%s\n'%(r['target'],r['ncall'],r['njmp'],r['prologue'],r['prev_term'],r['verdict'],r['conf'],r['body'][:100]))
# Final atlas_gaps.tsv: TRUE + LIKELY (high/med)
final=[r for r in results if r['verdict'] in ('TRUE_FUNC_ENTRY','LIKELY_FUNC_ENTRY')]
with open(os.path.join(BASE,'atlas_gaps.tsv'),'w',encoding='utf-8') as f:
    f.write('target\tncall\tnjmp\tprologue\tprev_term\tverdict\tconf\tsites\n')
    for r in final:
        sites=','.join('%08X'%s for s in (r['call_sites'][:4]+r['jmp_sites'][:2]))
        f.write('%08X\t%d\t%d\t%s\t%s\t%s\t%s\t%s\n'%(r['target'],r['ncall'],r['njmp'],r['prologue'],r['prev_term'],r['verdict'],r['conf'],sites))
from collections import Counter
print('candidates:',len(results),'verdicts:',dict(Counter(r['verdict'] for r in results)))
print('final gaps written:',len(final))
for r in final:
    print('%08X'%r['target'],r['verdict'],r['conf'],'c%d j%d'%(r['ncall'],r['njmp']),r['prologue'],r['prev_term'],'|',r['body'][:70])
json.dump(results,open(os.path.join(EVID,'atlas_gap_verdicts.json'),'w',encoding='utf-8'),ensure_ascii=False,indent=1)
