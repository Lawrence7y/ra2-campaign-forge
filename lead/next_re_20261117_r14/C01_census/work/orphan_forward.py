"""C01 FIX — independent forward (orphan-entry) channel.

Discovery does NOT use the call/jmp target sweep and does NOT use atlas entries
for discovery. It walks capstone linear instruction starts over all of .text,
then flags slice-range addresses that are:
  * 16-byte aligned (classic MSVC function alignment),
  * NOT inside any atlas function interval (interval containment, R13 §6-17),
  * carry a real function prologue,
  * and whose immediate predecessor (skipping nop/int3 padding) is a
    terminator ret/jmp/int3 with no gap.
Then it verifies the 5 audit orphans + 2 additional candidates individually.
"""
import os, bisect, struct, json
import pefile, capstone
HERE=os.path.dirname(os.path.abspath(__file__))
BASE=os.path.abspath(os.path.join(HERE,'..')); PROJECT=os.path.abspath(os.path.join(HERE,'..','..','..','..'))
EVID=os.path.join(BASE,'EVIDENCE'); EXE=os.path.join(PROJECT,'ra2youli','gamemd.exe')
ATLAS=os.path.join(PROJECT,'lead','next_re_20261112_r10','W130_atlas','function_atlas.tsv')
LO,HI=0x401000,0x456DFC
TAB=chr(9)

pe=pefile.PE(EXE,fast_load=True); IB=pe.OPTIONAL_HEADER.ImageBase
secs=[]
for s in pe.sections:
    nm=s.Name.decode(errors='replace').rstrip('\x00'); va=IB+s.VirtualAddress
    secs.append(dict(name=nm,va=va,raw=s.PointerToRawData,rawsize=s.SizeOfRawData))
text=next(s for s in secs if s['name']=='.text'); DATA=pe.__data__
md=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32); md.detail=True; md.skipdata=True

# atlas intervals (for EXCLUSION only, never discovery)
rows=[]
for ln in open(ATLAS,encoding='utf-8',errors='replace').read().splitlines()[1:]:
    p=ln.split(TAB)
    if len(p)<2: continue
    try: rows.append((int(p[0],16),int(p[0],16)+int(p[1])))
    except: pass
rows.sort(); starts=[r[0] for r in rows]; ends=[r[1] for r in rows]
def covered(va):
    i=bisect.bisect_right(starts,va)-1
    return i>=0 and va<ends[i]
def prev_atlas(va):
    i=bisect.bisect_right(starts,va)-1
    return rows[i] if i>=0 else None

# full linear instruction sweep (independent of atlas)
buf=DATA[text['raw']:text['raw']+text['rawsize']]
istarts=[]; iinfo={}
for insn in md.disasm(buf,text['va']):
    if insn.id==0: continue
    istarts.append(insn.address); iinfo[insn.address]=(insn.mnemonic,insn.op_str,insn.size)
iset=set(istarts)
print('linear instruction starts:',len(istarts))

def prologue(va):
    seq=[]
    i=bisect.bisect_left(istarts,va)
    for a in istarts[i:i+5]:
        m,o,s=iinfo[a]; seq.append((m,o))
    if not seq: return '',seq
    m=[x[0] for x in seq]; o=[x[1] for x in seq]
    tags=[]
    if m[0]=='mov' and o[0]=='edi, edi': tags.append('hotpatch')
    if m[0]=='push' and o[0]=='ebp': tags.append('push-ebp')
    elif m[0]=='push' and len(m)>1 and m[1]=='push' and o[1]!='ebp': tags.append('push-regs')
    if m[0]=='sub' and o[0].startswith('esp,') and len(o[0])<14: tags.append('sub-esp')
    if m[0] in ('mov','push') and 'dword ptr [esp + 4]' in o[0]: tags.append('param-store')
    return '+'.join(tags),seq

def pred_info(va):
    """Previous real instruction; skip a nop/int3 only when it ends exactly at va.
    This is the strict audit-compatible protocol (avoids the 80-candidate noise
    from treating arbitrary padding runs as one gap)."""
    i=bisect.bisect_left(istarts,va); j=i-1
    while j>=0:
        pa=istarts[j]; pm,po,ps=iinfo[pa]
        if pa+ps==va and pm in ('nop','int3'):
            j-=1; continue
        return (pa,pm,po,ps), va-(pa+ps)
    return None,0

# forward discovery: 16-byte-aligned, not covered, prologue, prev terminator
cands=[]
for a in istarts:
    if not (LO<=a<=HI): continue
    if a%16: continue
    if covered(a): continue
    if a not in iset: continue
    tag,seq=prologue(a)
    if not tag or 'hotpatch' in tag: continue  # hotpatch-only at aligned addr = often mid-insn artifact
    p,gap=pred_info(a)
    # Strict protocol (matches audit s4): function entry begins IMMEDIATELY
    # after a terminator (gap==0 after skipping a single trailing nop).
    # 0x433060 / 0x432BF0 have nop-padding gaps and are handled as
    # individually-verified extras in rebuild_atlas_gaps.py, not here.
    term=bool(p and gap==0 and (p[1].startswith('ret') or p[1] in ('jmp','int3')))
    if not term: continue
    cands.append(dict(addr=a,prologue=tag,prev=('%s %s @%08X'%(p[1],p[2],p[0])) if p else '',
                      gap=gap,body=' ; '.join('%s %s'%(m,o) for m,o in seq[:5]),
                      prev_atlas=('%08X..%08X'%prev_atlas(a) if prev_atlas(a) else '-')))
print('forward orphan candidates (align16 + prologue + prev-term + uncovered):',len(cands))
for c in cands:
    print('  %08X pro=%-16s prev=%-26s gap=%d body=%s'%(c['addr'],c['prologue'],c['prev'],c['gap'],c['body'][:60]))

# verify the 7 specific addresses with full context (independent of cands)
audit5=[0x4093C0,0x412280,0x427850,0x42E990,0x435B50]
extra2=[0x432BF0,0x433060]
detail=[]
for va in audit5+extra2:
    tag,seq=prologue(va)
    p,gap=pred_info(va)
    detail.append(dict(addr=va,aligned16=(va%16==0),is_instruction=(va in iset),
        covered=covered(va),prev_atlas=('%08X..%08X'%prev_atlas(va) if prev_atlas(va) else '-'),
        prologue=tag,prev=('%s %s @%08X'%(p[1],p[2],p[0])) if p else '',gap=gap,
        body=' ; '.join('%s %s'%(m,o) for m,o in seq[:6]),in_forward_cands=any(c['addr']==va for c in cands)))
print('\n=== 7-address detailed verification ===')
for d in detail:
    print('%08X a16=%s insn=%s covered=%s prev_atlas=%s'%(d['addr'],d['aligned16'],d['is_instruction'],d['covered'],d['prev_atlas']))
    print('   pro=%-16s prev=%-26s gap=%d fcand=%s'%(d['prologue'],d['prev'],d['gap'],d['in_forward_cands']))
    print('   body:',d['body'])

json.dump(dict(n_starts=len(istarts),forward_cands=cands,detail=detail),
          open(os.path.join(EVID,'orphan_forward_verification.json'),'w',encoding='utf-8'),ensure_ascii=False,indent=1)
