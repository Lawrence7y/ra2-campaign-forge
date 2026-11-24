
import json, struct, hashlib, collections, sys, time
from pathlib import Path
import pefile, capstone
from capstone.x86 import X86_OP_IMM, X86_OP_MEM, X86_OP_REG

t0=time.time()
ROOT=Path(r'D:\Project\ra2-campaign-forge')
EXE=ROOT/'ra2youli'/'gamemd.exe'
OUT=ROOT/'lead/next_re_20261117_r14/SURVEY_RING24'
raw=EXE.read_bytes()
pe=pefile.PE(data=raw, fast_load=True); ib=pe.OPTIONAL_HEADER.ImageBase
secs=[]
for s in pe.sections:
    secs.append(dict(name=s.Name.rstrip(b'\0').decode('latin1'),
        va=ib+s.VirtualAddress, vs=s.Misc_VirtualSize, rs=s.SizeOfRawData, ptr=s.PointerToRawData))
by={s['name']:s for s in secs}
def va2off(va):
    for s in secs:
        if s['va']<=va<s['va']+s['rs']:
            o=s['ptr']+va-s['va']
            if o+4<=len(raw): return o
    return None
def u32(va):
    o=va2off(va)
    if o is None: return None
    return int.from_bytes(raw[o:o+4],'little')
def cstr(va,lim=200):
    o=va2off(va)
    if o is None: return ''
    b=raw[o:o+lim]; z=b.find(b'\0')
    if z>=0: b=b[:z]
    try: return b.decode('ascii')
    except: return ''
text=by['.text']; tva=text['va']; tend=tva+text['vs']
code=raw[text['ptr']:text['ptr']+text['vs']]
def in_text(v): return v is not None and tva<=v<tend

# ---- RTTI tables
def rtti_of_col(col):
    td=u32(col+0xC)
    if td is None: return None
    nm=cstr(td+8)
    if nm.startswith(('.?AV','.?AU')): return (td,nm)
    return None
vt_tables={}
lo=by['.rdata']['va']; hi=by['.data']['va']+by['.data']['rs']
for s in (by['.rdata'],by['.data']):
    base=(s['va']+3)//4*4; end=s['va']+s['rs']-4
    for p in range(base,end,4):
        col=u32(p)
        if col is None or col<lo or col>hi: continue
        r=rtti_of_col(col)
        if r: vt_tables[p+4]=r[1]
entry2slots=collections.defaultdict(list)
for vt,cls in vt_tables.items():
    k=0
    while k<700:
        v=u32(vt+4*k)
        if v is None or not in_text(v) or v==0: break
        entry2slots[v].append([vt,k,cls])
        k+=1
print('rtti vtables',len(vt_tables),'entries',len(entry2slots),'t=%.1f'%(time.time()-t0),flush=True)

# ---- disasm
md=capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32); md.detail=True; md.skipdata=True
direct=collections.defaultdict(list)
installs=collections.defaultdict(list)   # global -> [[vt,site]]
dispatches=collections.defaultdict(list) # global -> [[disp,site]]
nins=0; ne8=0; memops=0; noindex_attr=0; zeroindex=0
win=collections.deque(maxlen=24)
def rec_of(ins):
    a0=a1=None
    try: ops=ins.operands
    except Exception: return None
    if len(ops)>0:
        o=ops[0]
        if o.type==X86_OP_MEM: a0=('M',None,(o.mem.base,o.mem.index,o.mem.disp,o.size))
        elif o.type==X86_OP_REG: a0=('R',o.reg,None)
        else: a0=('I',None,(int(o.imm)&0xffffffff,))
    if len(ops)>1:
        o=ops[1]
        if o.type==X86_OP_IMM: a1=('I',None,(int(o.imm)&0xffffffff,))
        elif o.type==X86_OP_REG: a1=('R',o.reg,None)
        elif o.type==X86_OP_MEM: a1=('M',None,(o.mem.base,o.mem.index,o.mem.disp,o.size))
    return a0,a1
for ins in md.disasm(code,tva):
    nins+=1
    mn=ins.mnemonic
    r=rec_of(ins)
    if r is None:
        win.append((ins.address,'.byte',None,None)); continue
    a0,a1=r
    if mn=='call' and ins.size==5 and ins.bytes[0]==0xE8:
        ne8+=1
        tgt=(ins.address+5+int.from_bytes(ins.bytes[1:5],'little',signed=True))&0xffffffff
        direct[tgt].append(ins.address)
    if a0 and a0[0]=='M':
        memops+=1
    # install imm: mov [g], imm32
    if mn=='mov' and a0 and a0[0]=='M' and a1 and a1[0]=='I':
        b,i,disp,sz=a0[2]
        if b==0 and i==0 and disp and sz==4:
            v=a1[2][0]
            if not in_text(v) and v>0x700000: installs[disp&0xffffffff].append([v,ins.address])
    # install reg: mov [g], reg  where reg:=imm recently
    if mn=='mov' and a0 and a0[0]=='M' and a1 and a1[0]=='R':
        b,i,disp,sz=a0[2]
        if b==0 and i==0 and disp and sz==4:
            g=disp&0xffffffff; reg=a1[1]
            for (pa,pm,pa0,pa1) in reversed(win):
                if pm=='mov' and pa1 and pa0 and pa0[0]=='R' and pa0[1]==reg:
                    if pa1[0]=='I':
                        v=pa1[2][0]
                        if not in_text(v) and v>0x700000: installs[g].append([v,ins.address])
                    break
                if pa1 and pa0 and pa0[0]=='R' and pa0[1]==reg: break
    # dispatch: call [reg+disp]
    if mn=='call' and a0 and a0[0]=='M':
        b,i,disp,sz=a0[2]
        if b!=0 and i==0 and disp>=0 and disp%4==0:
            g=None
            for (pa,pm,pa0,pa1) in reversed(win):
                if pm=='mov' and pa0 and pa0[0]=='R' and pa0[1]==b and pa1 and pa1[0]=='M':
                    mb,mi,md2,msz=pa1[2]
                    if mb==0 and mi==0 and md2: g=md2&0xffffffff
                    break
                if pa1 and pa0 and pa0[0]=='R' and pa0[1]==b and pa1[0]=='I': break
            if g: dispatches[g].append([disp,ins.address])
    win.append((ins.address,mn,a0,a1))
print('insns',nins,'e8',ne8,'direct targets',len(direct),'install globals',len(installs),'dispatch globals',len(dispatches),'t=%.1f'%(time.time()-t0),flush=True)

# ---- live vtable dispatch (④ form B): install [g]=vt (site1) + dispatch g at slot with vt[slot]==entry (site2), site1!=site2
livevt=collections.defaultdict(list)
for g,lst in installs.items():
    dl=dispatches.get(g)
    if not dl: continue
    for vt,site1 in lst:
        if vt is None: continue
        for disp,site2 in dl:
            if site1==site2: continue
            v=u32(vt+disp)
            if v is None or not in_text(v): continue
            livevt[v].append([g,vt,disp//4,site1,site2])
print('livevt entries',len(livevt),'t=%.1f'%(time.time()-t0),flush=True)

json.dump({'vtables':{hex(k):v for k,v in vt_tables.items()},
  'entry2slots':{hex(k):v for k,v in entry2slots.items()},
  'direct':{hex(k):v for k,v in direct.items()},
  'installs':{hex(k):v for k,v in installs.items()},
  'dispatches':{hex(k):[[d,s] for d,s in v] for k,v in dispatches.items()},
  'livevt':{hex(k):v for k,v in livevt.items()},
  'stats':dict(nins=nins,e8=ne8,nvt=len(vt_tables),nentry=len(entry2slots),ninstall_globals=len(installs),ndispatch_globals=len(dispatches),nlivevt=len(livevt))
  }, open(OUT/'work'/'index.json','w'), indent=0)
print('saved index.json', (OUT/'work'/'index.json').stat().st_size)
