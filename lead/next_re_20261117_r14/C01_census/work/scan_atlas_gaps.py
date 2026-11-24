"""atlas_gaps.tsv generator — channel independent of function_atlas.tsv entry+size.

Sweep the full .text linearly with capstone skipdata=True; collect all call/jmp
rel32 targets. Restrict to C01 address range [0x401000, 0x456DFC] (slice span).
A 'gap' = target not present as an atlas entry AND not inside any atlas function
interval (interval containment, NOT entry_at_or_before — discipline R13 §6-17).
Each candidate is annotated with:
  - call/jmp hit count and sites
  - boundary_check from nearest preceding atlas function (span<max_bytes else unknown)
  - vftable slot membership (independent RTTI channel)
  - whether it falls in the known 0x482000..0x483400 hole (sanity, out of slice)
"""
import os, json, struct, bisect, re
import capstone, pefile

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.abspath(os.path.join(HERE,'..'))
PROJECT = os.path.abspath(os.path.join(HERE,'..','..','..','..'))
EVID = os.path.join(BASE,'EVIDENCE')
EXE = os.path.join(PROJECT,'ra2youli','gamemd.exe')
ATLAS = os.path.join(PROJECT,'lead','next_re_20261112_r10','W130_atlas','function_atlas.tsv')
TAB = chr(9)
LO, HI = 0x401000, 0x456DFC

pe = pefile.PE(EXE, fast_load=True)
IB = pe.OPTIONAL_HEADER.ImageBase
secs=[]
for s in pe.sections:
    nm=s.Name.decode(errors='replace').rstrip('\x00'); va=IB+s.VirtualAddress
    secs.append(dict(name=nm,va=va,vsize=s.Misc_VirtualSize,raw=s.PointerToRawData,rawsize=s.SizeOfRawData))
text=next(s for s in secs if s['name']=='.text')
DATA=pe.__data__

md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
md.detail=True; md.skipdata=True

# atlas entries + intervals
with open(ATLAS,encoding='utf-8',errors='replace') as f:
    lines=f.read().splitlines()
rows=[]
for ln in lines[1:]:
    p=ln.split(TAB)
    if len(p)<9: continue
    try: e=int(p[0],16)
    except: continue
    rows.append((e,e+int(p[1]),p[0],int(p[1])))
rows.sort()
entries=[r[0] for r in rows]
entry_set=set(entries)
starts=[r[0] for r in rows]
ends=[r[1] for r in rows]

def contains_atlas(va):
    """interval containment: is va inside [entry, entry+size) of some atlas fn? (discipline 14)"""
    i=bisect.bisect_right(starts,va)-1
    if i>=0 and va<ends[i]:
        return rows[i]
    return None

def boundary_from(entry, target, max_bytes=0x20000):
    """Return (status, detail). status in {boundary,inside,unknown}. Uses skipdata."""
    span=target-entry
    if span<0: return ('unknown','target < entry')
    if span>=max_bytes: return ('unknown','span %d>=max_bytes %d (R13 §6-3: unknown not False)'%(span,max_bytes))
    buf=DATA[text['raw']+(entry-text['va']):text['raw']+(entry-text['va'])+span+32]
    last=None
    for insn in md.disasm(buf,entry):
        if insn.id==0: continue
        if insn.address==target: return ('boundary','%s %s'%(insn.mnemonic,insn.op_str))
        if insn.address<target<insn.address+insn.size:
            return ('inside','covered by %s %s @%08X'%(insn.mnemonic,insn.op_str,insn.address))
        if insn.address>target: break
    return ('unknown','linear disasm did not reach')

# sweep full .text
calls={}; jmps={}
nb=0
buf=DATA[text['raw']:text['raw']+text['rawsize']]
for insn in md.disasm(buf,text['va']):
    if insn.id==0: continue
    nb+=1
    if insn.mnemonic=='call' and insn.op_str.startswith('0x'):
        t=int(insn.op_str,16); calls.setdefault(t,[]).append(insn.address)
    elif insn.mnemonic=='jmp' and insn.op_str.startswith('0x'):
        t=int(insn.op_str,16); jmps.setdefault(t,[]).append(insn.address)

# vftable membership (independent channel)
vf={}
j=os.path.join(EVID,'rtti_vtables.json')
if not os.path.exists(j):
    j=os.path.join(HERE,'rtti_vtables.json')
if os.path.exists(j):
    d=json.load(open(j,encoding='utf-8'))
    for k,v in d.get('func_map',{}).items(): vf[int(k)]=v

targets=set(calls)|set(jmps)
inrange=[t for t in targets if LO<=t<=HI]
gaps=[]
for t in sorted(inrange):
    if t in entry_set: continue
    cont=contains_atlas(t)
    # boundary check from nearest preceding atlas entry if contained; else from t-? use own linear from a nearby known entry
    if cont:
        bstat,bdet=boundary_from(cont[0],t)
        from_entry=cont[0]
    else:
        i=bisect.bisect_right(starts,t)-1
        if i>=0:
            bstat,bdet=boundary_from(starts[i],t)
            from_entry=starts[i]
        else:
            bstat,bdet=('unknown','no preceding atlas entry'); from_entry=None
    gaps.append(dict(target=t, call_sites=calls.get(t,[]), jmp_sites=jmps.get(t,[]),
                     ncall=len(calls.get(t,[])), njmp=len(jmps.get(t,[])),
                     inside_atlas=bool(cont), atlas_fn=('%08X'%cont[0] if cont else ''),
                     boundary=bstat, boundary_detail=bdet, from_entry=from_entry,
                     vftable=vf.get(t,[]), slice_range=(LO<=t<=HI)))

with open(os.path.join(EVID,'atlas_gaps_full.json'),'w',encoding='utf-8') as f:
    json.dump(dict(n_insns=nb, n_text_bytes=len(buf), n_targets=len(targets),
                   n_targets_in_range=len(inrange), gaps=gaps,
                   known_hole_hit={hex(t):(t in calls,t in jmps) for t in (0x4824D4,)}), f, ensure_ascii=False, indent=1)

# Write atlas_gaps.tsv: target(hex8) TAB ncall TAB njump TAB boundary TAB vftable TAB notes
with open(os.path.join(BASE,'atlas_gaps.tsv'),'w',encoding='utf-8') as f:
    f.write('target\tncall\tnjmp\tboundary\tvftable\tatlas_fn\tnotes\n')
    for g in gaps:
        vfdesc=';'.join('%s#%d'%(m['cls'],m['slot']) for m in g['vftable'][:3])
        f.write('%08X\t%d\t%d\t%s\t%s\t%s\t%s\n'%(
            g['target'],g['ncall'],g['njmp'],g['boundary'],vfdesc,g['atlas_fn'],
            g['boundary_detail'][:60]))
print('sweep insns:',nb,'targets total:',len(targets),'targets in slice range:',len(inrange))
print('gaps (not atlas entry):',len(gaps))
print('gaps by boundary:',{k:sum(1 for g in gaps if g['boundary']==k) for k in ('boundary','inside','unknown')})
print('0x4824D4 hit:', 0x4824D4 in calls, 0x4824D4 in jmps, 'sites', (calls.get(0x4824D4,[])+jmps.get(0x4824D4,[]))[:5])
for g in gaps[:30]:
    print('%08X'%g['target'],'call',g['ncall'],'jmp',g['njmp'],g['boundary'],g['boundary_detail'][:50],'vf',len(g['vftable']))
