"""
S11-K2 fresh verification part 2: correct GetSize<->allocation closure + CLSID + slot12 identity.
Independent byte channel. Fixes part-1 bug: must use the CLASS ctor called by CreateInstance
(not the TClassFactory ctor), and bound CI disasm to one CreateInstance body.
"""
import json, struct
from pehelp import (rd, u32, section_of, is_code, disasm, fmt, MD)
from capstone.x86 import X86_OP_IMM, X86_OP_MEM

OUT=r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S11-K2\EVIDENCE\fresh_closure.txt'
L=[]
def P(s=''):
    L.append(str(s)); print(s)

FC=json.load(open(r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S11-K2\EVIDENCE\fresh_core.json',encoding='utf-8'))
classes=FC['classes']
# GetSize imm from off0 slot9 per class (fresh, part1)
gs_imm={}
for n,o,sl,a,im,f in FC['getsize_hits']:
    if o==0 and sl==9:
        gs_imm[n.split('AV')[1].split('@@')[0]]=im
# canonical class vtable installs (off0/off4) -> class short name
vt2class={}
for name,ss in classes.items():
    short=name.split('AV')[1].split('@@')[0]
    for s in ss:
        if s['off'] in (0,4): vt2class[s['vt']]=short

# ---- find class ctors: any code that installs a canonical vtable ----
P('===== class ctor discovery (writes canonical off0/off4 vtable immediate) =====')
ctor_vt={}
# scan a bounded code window around each known class vtable's likely ctor region:
# simpler: sweep whole .text for C7/mov [mem],imm where imm in vt2class
nm,vaoff,vsize,rsize,praw=[s for s in __import__('pehelp').sections() if s[0]=='.text'][0]
base=__import__('pehelp').IMAGE_BASE
blob=rd(base+vaoff,rsize)
# use linear disasm with skipdata over .text to find mov [mem],imm
import re
install_sites={}  # class -> list of (site,imm)
for ins in MD.disasm(blob, base+vaoff):
    if ins.mnemonic=='mov' and len(ins.operands)==2 and ins.operands[0].type==X86_OP_MEM and ins.operands[1].type==X86_OP_IMM:
        v=ins.operands[1].imm & 0xffffffff
        if v in vt2class:
            install_sites.setdefault(vt2class[v],[]).append((ins.address,v))
for cls in sorted(install_sites):
    sites=install_sites[cls]
    P('  %-24s installs=%s'%(cls,', '.join('%08X@%08X'%(v,a) for a,v in sites[:8])))

# Identify the ctor = function containing the install site. Use smallest install site and walk back
# to nearest 16B-aligned prologue is unreliable; instead find callers of install sites via E8 rel32
# in .text that target a function start which contains the install.
# Practical: a class ctor typically starts <=0x120 before its first vtable install site.
def ctor_start(site, back=0x200):
    # find 16B-aligned address with push ebp/53/55 prologue closest before site
    cand=[]
    for a in range(max(base+vaoff, site-back), site, 4):
        if a%16: continue
        b=rd(a,2)
        if b[0] in (0x55,0x53,0x56,0x57,0x6a) or (b[0]==0x83 and b[1]==0xec):
            cand.append(a)
    return cand[-1] if cand else None

P('\n===== per-class ctor + CreateInstance + allocation closure =====')
closure=[]
for cls in sorted(gs_imm):
    sites=install_sites.get(cls,[])
    if not sites:
        P('  %-24s NO vtable-install site found'%cls); continue
    first_site=min(a for a,v in sites)
    cs=ctor_start(first_site)
    P('  %-24s first_install=%08X ctor_guess=%s'%(cls,first_site,('%08X'%cs) if cs else '?'))

# The robust route: find, for each GetSize class, the Locomotion class ctor = the call target
# inside a TClassFactory CreateInstance that immediately follows push<size>;call new(0x7C8E17).
# Discover CIs by scanning .text for E8 rel32 call to 0x7C8E17 (operator new) preceded by push imm.
P('\n===== operator-new allocation sites whose ctor installs a Locomotion vtable =====')
# find all call sites to operator new 0x7C8E17
new_target=0x7C8E17
ci_candidates=[]
for ins in MD.disasm(blob, base+vaoff):
    if ins.mnemonic=='call' and ins.operands and ins.operands[0].type==X86_OP_IMM and (ins.operands[0].imm & 0xffffffff)==new_target:
        ci_candidates.append(ins.address)
P('  operator new call sites = %d'%len(ci_candidates))

# for each site, look back up to 12 instructions for push imm (size), look ahead for call <ctor>
def alloc_and_ctor(newsite, lookback=16, lookahead=16):
    start=max(base+vaoff,newsite-lookback*8)
    pre=list(disasm(start,newsite-start+8))
    push=None
    for ins in reversed(pre):
        if ins.address>=newsite: continue
        if ins.mnemonic=='push' and ins.operands and ins.operands[0].type==X86_OP_IMM:
            v=ins.operands[0].imm & 0xffffffff
            if 0x20<=v<=0x1000:
                push=(ins.address,ins.bytes.hex(),v); break
    post=list(disasm(newsite,lookahead*8))
    ctor=None
    for ins in post[1:]:
        if ins.mnemonic=='call' and ins.operands and ins.operands[0].type==X86_OP_IMM:
            t=ins.operands[0].imm & 0xffffffff
            if t!=0x7C8E17 and is_code(t): ctor=(ins.address,t); break
    return push,ctor

def cls_of_ctor(ctor,n=0x400):
    if not ctor: return None
    hits=[]
    for ins in disasm(ctor,n):
        if ins.mnemonic=='mov' and len(ins.operands)==2 and ins.operands[0].type==X86_OP_MEM and ins.operands[1].type==X86_OP_IMM:
            v=ins.operands[1].imm & 0xffffffff
            if v in vt2class: hits.append((ins.address,v,vt2class[v]))
    return hits[0][2] if hits else None

P('\n  site        push(enc)        ctor       class                 GetSize  CLOSED')
nclose=0
seen=set()
for site in ci_candidates:
    push,ctor=alloc_and_ctor(site)
    if not push or not ctor: continue
    cls=cls_of_ctor(ctor[1])
    if cls not in gs_imm: continue  # only Locomotion classes
    g=gs_imm[cls]; ok=(push[2]==g)
    if ok: nclose+=1
    key=(cls,push[0])
    if key in seen: continue
    seen.add(key)
    P('  %08X  %08X %-6s %08X  %-24s %-5s %s'%(site,push[0],push[1],ctor[1],cls,g,'YES' if ok else 'no'))
P('CLOSURE (Locomotion factory new-push == GetSize imm) = %d/%d classes'%(nclose,len(gs_imm)))

# ---- slot12 identity: disassemble off4 slot11/12 fully for Drive to show NOT GetSize ----
P('\n===== off4 slot 11/12 full disasm (Drive) — prove NOT B8 imm32 C3 =====')
d=classes['.?AVDriveLocomotionClass@@']
main=[s for s in d if s['off']==4][0]
for idx in (11,12):
    a=u32(main['vt']+4*idx)
    P('  off4 slot%d = %08X'%(idx,a))
    for ins in list(disasm(a,0x40))[:14]:
        P('     '+fmt(ins))
        if ins.mnemonic=='ret': break

# ---- CLSID: confirm 11 GUID array, no adjacent factory ptr table ----
P('\n===== CLSID region 0x7E9A20..0x7E9AE0 =====')
for va in range(0x7E9A20,0x7E9AE0,16):
    d16=rd(va,16)
    g1,g2,g3=struct.unpack('<IHH',d16[:8])
    P('  %08X  %08X-%04X-%04X-%s'%(va,g1,g2,g3,d16[8:].hex().upper()))

with open(OUT,'w',encoding='utf-8') as f: f.write('\n'.join(L)+'\n')
print('\nWROTE',OUT)
