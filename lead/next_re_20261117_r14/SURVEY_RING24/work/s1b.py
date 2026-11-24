
import json, struct, hashlib, collections, sys, time
from pathlib import Path
import pefile, capstone
from capstone.x86 import X86_OP_IMM, X86_OP_MEM, X86_OP_REG
import capstone.x86_const as XC

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
print('secs', [(s['name'],hex(s['va']),s['vs'],s['rs']) for s in secs], flush=True)

# ---------------- 1) RTTI vtable enumeration ----------------
# find dwords p where u32(p) = COL, u32(COL+0xC)=TD, cstr(TD+8) starts '.?A'
def rtti_of_col(col):
    td=u32(col+0xC)
    if td is None: return None
    nm=cstr(td+8)
    if nm.startswith(('.?AV','.?AU')): return (td,nm)
    return None

scan_secs=[by['.rdata'], by['.data']]
vt_tables={}   # vt -> class name
for s in scan_secs:
    base=(s['va']+3)//4*4
    end=s['va']+s['rs']-4
    for p in range(base,end,4):
        col=u32(p)
        if col is None or col<by['.rdata']['va'] or col> by['.data']['va']+by['.data']['rs']: continue
        r=rtti_of_col(col)
        if r: vt_tables[p+4]=r[1]
print('rtti vtables', len(vt_tables), 't=%.1fs'%(time.time()-t0), flush=True)

# slots
entry2slots=collections.defaultdict(list)   # entry -> [[vt,slot,cls]]
for vt,cls in vt_tables.items():
    if not in_text(vt): continue
    k=0
    while k<700:
        v=u32(vt+4*k)
        if not in_text(v): break
        if v==0: break
        entry2slots[v].append([vt,k,cls])
        k+=1
print('entries in rtti vtables', len(entry2slots), 't=%.1fs'%(time.time()-t0), flush=True)

# ---------------- 2) disassemble .text ----------------
md=capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32); md.detail=True; md.skipdata=True
direct=collections.defaultdict(list)     # target -> [site]
installs_imm=collections.defaultdict(list)   # global -> [[vt,site]]
reg_imm=collections.defaultdict(list)    # after mov reg,imm within window
dispatches=collections.defaultdict(list) # (global,disp) -> [site]
call_disp=[]                              # (site, disp, reg) for [reg+disp] calls
nins=0; ne8=0
win=[]  # rolling window of (addr,mnemonic,op0type,op0reg,op0imm or None, bytes)
WIN=14
for ins in md.disasm(code,tva):
    nins+=1
    mn=ins.mnemonic
    ops=ins.operands
    if mn=='call' and ins.size==5 and ins.bytes[0]==0xE8:
        ne8+=1
        tgt=(ins.address+5+int.from_bytes(ins.bytes[1:5],'little',signed=True))&0xffffffff
        direct[tgt].append(ins.address)
    # record for rolling window
    rec=[ins.address,mn,None,None,None]
    if ops:
        o0=ops[0]
        if o0.type==X86_OP_MEM:
            rec[2]='M'; rec[3]=(o0.mem.base,o0.mem.index,o0.mem.disp,o0.size)
        elif o0.type==X86_OP_REG:
            rec[2]='R'; rec[3]=o0.reg
        if len(ops)>1 and ops[1].type==X86_OP_IMM:
            rec[4]=int(ops[1].imm)&0xffffffff
    # install: mov dword ptr [g], imm32
    if mn=='mov' and len(ops)>=2 and ops[0].type==X86_OP_MEM and ops[1].type==X86_OP_IMM:
        m=ops[0].mem
        if m.base==0 and m.index==0 and m.disp and ops[0].size==4:
            v=int(ops[1].imm)&0xffffffff
            if not in_text(v):
                installs_imm[int(m.disp)&0xffffffff].append([v,ins.address])
    # install: mov dword ptr [g], reg   (reg刚刚载入 imm vt)
    if mn=='mov' and len(ops)>=2 and ops[0].type==X86_OP_MEM and ops[1].type==X86_OP_REG:
        m=ops[0].mem
        if m.base==0 and m.index==0 and m.disp and ops[0].size==4:
            g=int(m.disp)&0xffffffff; r=ops[1].reg
            for j in range(len(win)-1,max(-1,len(win)-9),-1):
                w=win[j]
                if w[1]=='mov' and w[2]=='R' and w[3]==r and w[4] is not None:
                    v=w[4]
                    if not in_text(v) and v>0x700000:
                        installs_imm[g].append([v,ins.address])
                    break
                if w[1]=='mov' and w[2]=='R' and w[3]==r and w[4] is None: break
    # dispatch: call dword ptr [reg+disp]
    if mn=='call' and ops and ops[0].type==X86_OP_MEM:
        m=ops[0].mem
        if m.base!=0 and m.index==0 and m.disp>=0 and m.disp%4==0:
            call_disp.append((ins.address,m.base,m.disp))
            # look back for mov reg, [global]
            g=None; ecximm=None
            for j in range(len(win)-1,max(-1,len(win)-20),-1):
                w=win[j]
                if w[1]=='mov' and w[2]=='R' and w[3]==m.base and w[4] is None:
                    # need the operand-0 mem info of that mov: stored as rec[5]? skip -> recompute
                    pass
            win.append(rec)
            if len(win)>40: win.pop(0)
            continue
    win.append(rec)
    if len(win)>40: win.pop(0)
print('insns',nins,'e8',ne8,'direct targets',len(direct),'installs globals',len(installs_imm),'call_disp',len(call_disp),'t=%.1fs'%(time.time()-t0), flush=True)
json.dump(dict(nins=nins,ne8=ne8,nvt=len(vt_tables),nentry=len(entry2slots),
               ndirect=len(direct),ninst=len(installs_imm),ncalldisp=len(call_disp)),
          open(OUT/'work'/'s1_stats.json','w'),indent=1)
