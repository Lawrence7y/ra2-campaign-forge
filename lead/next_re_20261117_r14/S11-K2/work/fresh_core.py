"""
S11-K2 fresh independent re-derivation of CORE byte facts (no reliance on prior conclusions).
Byte channel only; capstone skipdata=True; no function_atlas.tsv for discovery.
Produces: EVIDENCE/fresh_core.txt / EVIDENCE/fresh_core.json
Checks:
  T1: RTTI TD/COL/vtable + slot counts delimited from .rdata; class count; CHD parents
  T2: for EVERY vtable slot of EVERY class, dump B8 imm32 C3 hits WITH slot index.
      Explicitly report slot12 (off=4) and slot9 (off=0) contents per class.
      Baseline: raw B8 imm32 C3 count in .text and how many land in any Locomotion slot.
  T2: factory CreateInstance enumeration via registration fn -> factory ctor -> vtable slot3;
      per-CI scan of push imm (6A/68) and operator-new call; record enc form.
"""
import re, json, struct
from pehelp import (IMAGE_BASE, EXE, rd, u32, u16, sections, section_of, in_section,
                    is_code, disasm, fmt, MD)
from capstone.x86 import X86_OP_IMM, X86_OP_REG, X86_OP_MEM

OUT = r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S11-K2\EVIDENCE\fresh_core.txt'
JOUT = r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S11-K2\EVIDENCE\fresh_core.json'
L=[]
def P(s=''):
    L.append(str(s)); print(s)

SEC_RANGES=[(nm, IMAGE_BASE+vaoff, IMAGE_BASE+vaoff+max(vsize,rsize))
            for nm,vaoff,vsize,rsize,praw in sections()]

def read_cstr(va, maxb=128):
    b=rd(va,maxb); z=b.find(b'\x00')
    if z<0: return None
    try: return b[:z].decode('latin1')
    except: return None

# ---------------- T1: RTTI ----------------
P('===== T1 RTTI ENUMERATION (fresh) =====')
pat=re.compile(rb'\.\?A[UV][A-Za-z0-9_]*LocomotionClass@@\x00')
td={}
for nm,lo,hi in SEC_RANGES:
    blob=rd(lo,hi-lo)
    for m in pat.finditer(blob):
        nav=lo+m.start(); t=nav-8
        try: vf=u32(t); spare=u32(t+4)
        except: continue
        nmv=read_cstr(t+8)
        if in_section(vf,'.rdata') and spare==0 and nmv and 'LocomotionClass' in nmv:
            td[t]=nmv
P('valid TD count = %d'%len(td))
for t,nm in sorted(td.items()): P('  TD %08X  %s'%(t,nm))

tdset=set(td)
cols=[]  # (col,td,off,cdoff,chd)
for nm,lo,hi in SEC_RANGES:
    for va in range(lo,hi-0x10+1,4):
        try: v=u32(va)
        except: continue
        if v in tdset:
            col=va-0xC
            try:
                sig=u32(col); off=u32(col+4); cdoff=u32(col+8); chk=u32(col+0xC); chd=u32(col+0x10)
            except: continue
            if sig==0 and chk==v and in_section(chd,'.rdata'):
                cols.append((col,v,off,cdoff,chd))
colset={c[0] for c in cols}
P('COL count = %d'%len(cols))

def chd_bases(chd):
    try: sig=u32(chd); attr=u32(chd+4); nb=u32(chd+8); bca=u32(chd+0xC)
    except: return []
    if not in_section(bca,'.rdata') or nb==0 or nb>64: return []
    out=[]
    for i in range(nb):
        bcd=u32(bca+4*i)
        if not in_section(bcd,'.rdata'): out.append('?@%08X'%bcd); continue
        btd=u32(bcd)
        nm=read_cstr(btd+8) if (in_section(btd,'.rdata') or in_section(btd,'.data')) else None
        out.append(nm or ('?@%08X'%btd))
    return out

# vtables: vtable[-1]==COL, in .rdata, slot0 code
vts=[]
for nm,lo,hi in SEC_RANGES:
    for va in range(lo,hi-4+1,4):
        try: v=u32(va)
        except: continue
        if v in colset:
            vt=va+4
            if section_of(vt)!=('.rdata'): continue
            try:
                if not is_code(u32(vt)): continue
            except: continue
            col=v
            tdv=[c[1] for c in cols if c[0]==col][0]
            off=[c[2] for c in cols if c[0]==col][0]
            vts.append((vt,col,tdv,off,td[tdv]))

SEP={0x00004E40,0x399D52A2,0x469D913F}
def count_slots(vt,maxn=200):
    n=0
    for i in range(maxn):
        a=vt+4*i
        if section_of(a)!='.rdata': break
        try: v=u32(a)
        except: break
        if v in colset or v in SEP or not is_code(v): break
        n+=1
    return n

classes={}
P('\nper-class vtable inventory (off | VT | slots | end-delim):')
for vt,col,tdv,off,name in sorted(vts):
    n=count_slots(vt); end=vt+4*n
    try: delim=u32(end) if section_of(end)=='.rdata' else None
    except: delim=None
    dtxt=('COL' if delim in colset else ('SEP' if delim in SEP else ('noncode' if delim is not None and not is_code(delim) else (hex(delim) if delim is not None else '?'))))
    classes.setdefault(name,[]).append(dict(vt=vt,col=col,td=tdv,off=off,slots=n,end=end,delim=dtxt))
    P('  %-44s off=%-3d VT=%08X slots=%-3d delim=%s'%(name,off,vt,n,dtxt))
P('CLASS COUNT = %d'%len(classes))

P('\nCHD parents (primary COL off=4 per class):')
for name in sorted(classes):
    prim=[s for s in classes[name] if s['off']==4]
    if not prim: continue
    col=prim[0]['col']
    chd=[c[4] for c in cols if c[0]==col][0]
    P('  %-44s bases=%s'%(name,chd_bases(chd)))

# ---------------- T2: GetSize slot probe ----------------
P('\n\n===== T2 GETSIZE / SLOT PROBE (fresh) =====')
def get_imm_ret(a):
    b=rd(a,6)
    if len(b)>=6 and b[0]==0xB8 and b[5]==0xC3:
        return struct.unpack('<I',b[1:5])[0],'B8imm32C3'
    return None,None

all_slot_vals=set()
hits=[]   # (name,off,slot,addr,imm,form)
for name in sorted(classes):
    for s in sorted(classes[name], key=lambda x:x['off']):
        for i in range(s['slots']):
            a=u32(s['vt']+4*i)
            all_slot_vals.add(a)
            if not is_code(a): continue
            imm,form=get_imm_ret(a)
            if imm is not None:
                hits.append((name,s['off'],i,a,imm,form))
P('B8 imm32 C3 hits inside Locomotion vtables = %d'%len(hits))
for name,off,slot,a,imm,form in hits:
    P('  %-44s off=%-3d slot=%-2d addr=%08X imm=%d(0x%X)'%(name,off,slot,a,imm,imm))

# explicit slot12 (off4) and slot9 (off0) per class
P('\nexplicit per-class slot contents: [off4 slot11] [off4 slot12] [off0 slot9]')
for name in sorted(classes):
    def slot_info(off,idx):
        ss=[s for s in classes[name] if s['off']==off]
        if not ss or idx>=ss[0]['slots']: return 'NONE'
        a=u32(ss[0]['vt']+4*idx)
        if not is_code(a): return '%08X noncode'%a
        ins=list(disasm(a,10))
        sig=' | '.join(x.mnemonic+' '+x.op_str for x in ins[:2])
        imm,form=get_imm_ret(a)
        return '%08X %s%s'%(a,sig,(' [IMM=%d]'%imm) if imm is not None else '')
    P('  %-44s'%name)
    P('    off4 s11: '+slot_info(4,11))
    P('    off4 s12: '+slot_info(4,12))
    P('    off0 s09: '+slot_info(0,9))

# baseline raw count
P('\nbaseline: raw B8 imm32 C3 in .text')
nm,vaoff,vsize,rsize,praw=[s for s in sections() if s[0]=='.text'][0]
blob=rd(IMAGE_BASE+vaoff,rsize)
raw=[]
for i in range(len(blob)-5):
    if blob[i]==0xB8 and blob[i+5]==0xC3:
        raw.append(IMAGE_BASE+vaoff+i)
P('  raw count = %d'%len(raw))
P('  land in any Locomotion vtable slot = %d'%sum(1 for a in raw if a in all_slot_vals))
P('  16B-aligned among raw = %d'%sum(1 for a in raw if a%16==0))

# ---------------- T2: factory CreateInstance + alloc ----------------
P('\n\n===== T2 FACTORY CreateInstance + ALLOCATION PUSH (fresh) =====')
# discover factory ctors from registration fn 0x6BB9A0 range by call targets in 0x6C0000..0x6D0000
ctors=set()
for ins in disasm(0x6BC400,0x6BD700-0x6BC400):
    if ins.mnemonic=='call' and ins.operands and ins.operands[0].type==X86_OP_IMM:
        t=ins.operands[0].imm & 0xffffffff
        if 0x6C0000<=t<0x6D0000: ctors.add(t)
P('factory ctors found = %d'%len(ctors))
P('  '+', '.join('%08X'%c for c in sorted(ctors)))

def ci_from_ctor(ctor, nbytes=0x200):
    # find installed vtable (mov [mem],imm where imm in .rdata and slot3 is code)
    cand=[]
    for ins in disasm(ctor,nbytes):
        if ins.mnemonic=='mov' and len(ins.operands)==2 and ins.operands[0].type==X86_OP_MEM and ins.operands[1].type==X86_OP_IMM:
            v=ins.operands[1].imm & 0xffffffff
            if section_of(v)=='.rdata': cand.append(v)
    for vt in cand:
        try: s3=u32(vt+12)
        except: continue
        if is_code(s3): return vt,s3
    return None,None

def scan_alloc(ci,nbytes=0x200):
    out=[]
    for ins in disasm(ci,nbytes):
        if ins.mnemonic=='push' and ins.operands and ins.operands[0].type==X86_OP_IMM:
            v=ins.operands[0].imm & 0xffffffff
            out.append((ins.address,ins.bytes.hex(),v))
        if ins.mnemonic=='call' and ins.operands and ins.operands[0].type==X86_OP_IMM:
            t=ins.operands[0].imm & 0xffffffff
            out.append((ins.address,'call',t))
    return out

factory=[]
for c in sorted(ctors):
    vt,ci=ci_from_ctor(c)
    if ci:
        ops=scan_alloc(ci)
        pushes=[x for x in ops if x[1]!='call' and 0x20<=x[2]<=0x1000]
        calls=[x for x in ops if x[1]=='call']
        factory.append((c,vt,ci,pushes,calls))
        P('ctor %08X vt=%08X CI=%08X pushes=%s'%(c,vt,ci,[(('%08X'%a),h,v) for a,h,v in pushes[:3]]))
        P('   calls: '+', '.join('%08X@%08X'%(t,a) for a,_,t in calls[:8]))

# map GetSize imm per class (off0 slot9) for closure
gs_imm={}
for name,off,slot,a,imm,form in hits:
    if off==0 and slot==9:
        gs_imm[name.split('AV')[1].split('@@')[0]]=imm

# identify class of each factory via ctor installing canonical off0/off4 vtables
vt2class={}
for name,ss in classes.items():
    short=name.split('AV')[1].split('@@')[0]
    for s in ss:
        if s['off'] in (0,4): vt2class[s['vt']]=short

def class_from_ctor(ctor,n=0x600):
    res=[]
    for ins in disasm(ctor,n):
        if ins.mnemonic=='mov' and len(ins.operands)==2 and ins.operands[0].type==X86_OP_MEM and ins.operands[1].type==X86_OP_IMM:
            v=ins.operands[1].imm & 0xffffffff
            if v in vt2class: res.append((ins.address,v,vt2class[v]))
    return res

P('\nclosure per factory:')
nclose=0
for c,vt,ci,pushes,calls in factory:
    ch=class_from_ctor(c)
    cls=ch[0][2] if ch else '?'
    alloc=pushes[0][2] if pushes else None
    g=gs_imm.get(cls)
    ok=(alloc==g and alloc is not None)
    if ok: nclose+=1
    P('  CI=%08X ctor=%08X cls=%-24s alloc=%-5s GetSize=%-5s %s'%(ci,c,cls,alloc,g,'CLOSED' if ok else 'no'))
P('CLOSURE = %d/%d'%(nclose,len(factory)))

obj=dict(
    classes=classes,
    td={('%08X'%k):v for k,v in td.items()},
    cols=[dict(col=('%08X'%c[0]),td=('%08X'%c[1]),off=c[2],cdoff=c[3],chd=('%08X'%c[4]),name=td[c[1]]) for c in cols],
    chd_bases={('%08X'%[cc for cc in cols if cc[0]==s['col']][0][4]):chd_bases([cc for cc in cols if cc[0]==s['col']][0][4]) for name in classes for s in classes[name] if s['off']==4},
    getsize_hits=[[n,o,sl,('%08X'%a),im,f] for n,o,sl,a,im,f in hits],
    baseline=dict(raw=len(raw),in_slot=sum(1 for a in raw if a in all_slot_vals),aligned=sum(1 for a in raw if a%16==0)),
    factory=[dict(ctor=('%08X'%c),vt=('%08X'%vt),ci=('%08X'%ci),
                  pushes=[[('%08X'%a),h,v] for a,h,v in pushes],
                  calls=[[('%08X'%a),('%08X'%t)] for a,_,t in calls]) for c,vt,ci,pushes,calls in factory],
    closure=nclose,
)
with open(JOUT,'w',encoding='utf-8') as f: json.dump(obj,f,indent=1,ensure_ascii=False)
with open(OUT,'w',encoding='utf-8') as f: f.write('\n'.join(L)+'\n')
print('\nWROTE',OUT)
