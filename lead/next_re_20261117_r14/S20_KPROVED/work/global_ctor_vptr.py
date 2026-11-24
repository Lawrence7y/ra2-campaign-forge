import csv,os,struct,bisect
from collections import defaultdict
import pefile
from capstone import Cs,CS_ARCH_X86,CS_MODE_32
from capstone.x86 import X86_INS_MOV,X86_INS_LEA,X86_INS_CALL,X86_OP_REG,X86_OP_IMM,X86_OP_MEM,X86_REG_ECX
T=r'D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe'
ATLAS=r'D:\Project\ra2-campaign-forge\lead\next_re_20261112_r10\W130_atlas\function_atlas.tsv'
EV=r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S20_KPROVED\EVIDENCE'
raw=open(T,'rb').read(); pe=pefile.PE(T,fast_load=True); base=pe.OPTIONAL_HEADER.ImageBase
sec=next(s for s in pe.sections if s.Name.rstrip(b'\0').decode('latin1')=='.text'); tstart=sec.PointerToRawData; tend=tstart+sec.SizeOfRawData; tva=base+sec.VirtualAddress
def nv(x): return format(x&0xffffffff,'08X')
def va_off(va): return pe.get_offset_from_rva(int(va,16)-base)
atlas=[]; body={}; starts=[]
with open(ATLAS,encoding='utf-8') as f:
    next(f)
    for line in f:
        c=line.rstrip('\r\n').split('\t')
        if len(c)<2: continue
        e=nv(int(c[0],16)); sz=int(c[1]); atlas.append((e,sz)); starts.append(int(e,16))
atlas.sort(key=lambda x:int(x[0],16)); starts=[int(e,16) for e,sz in atlas]
def owner(va):
    v=int(va,16); i=bisect.bisect_right(starts,v)-1
    if i>=0 and v<starts[i]+atlas[i][1]: return atlas[i][0]
    return None
md=Cs(CS_ARCH_X86,CS_MODE_32); md.detail=True; md.skipdata=True
def getstate(st,r,idx,maxd=200):
    s=st.get(r)
    return s if s and idx-s['idx']<=maxd else None
def scan_state(entry, stop, init):
    try: off=va_off(entry); code=raw[off:off+dict(atlas)[entry]]
    except Exception: return None
    st=dict(init); idx=0
    for ins in md.disasm(code,int(entry,16)):
        if ins.id==0: continue
        idx+=1; site=nv(ins.address); ops=ins.operands
        if site==stop: return st.get(X86_REG_ECX),st,idx
        if ins.id in (X86_INS_MOV,X86_INS_LEA) and len(ops)==2:
            d,s=ops[0],ops[1]
            if d.type==X86_OP_REG:
                r=d.reg
                if s.type==X86_OP_IMM:
                    st[r]={'kind':'global','g':nv(s.imm),'off':0,'idx':idx}
                elif s.type==X86_OP_REG:
                    q=getstate(st,s.reg,idx)
                    if q: st[r]={**q,'idx':idx}
                    else: st.pop(r,None)
                elif s.type==X86_OP_MEM and s.mem.index==0:
                    if s.mem.base==0 and s.mem.disp:
                        st[r]={'kind':'globalptr','g':nv(s.mem.disp),'off':0,'idx':idx}
                    elif s.mem.base is not None:
                        q=getstate(st,s.mem.base,idx)
                        if q and q['kind'] in ('this','global','globalptr'):
                            st[r]={'kind':q['kind'],'g':q.get('g',''),'off':q.get('off',0)+s.mem.disp,'idx':idx}
                        else: st.pop(r,None)
                    else: st.pop(r,None)
                else: st.pop(r,None)
    return st.get(X86_REG_ECX),st,idx
# Collect this-derived vptr writes from raw C7 write sites.
write_rows=[]
with open(os.path.join(EV,'raw_c7_s20vt.tsv'),encoding='utf-8') as f:
    for r in csv.DictReader(f,delimiter='\t'): write_rows.append(r)
# raw E8 map for call sites to constructor owners
rawcalls=defaultdict(list)
for off in range(tstart,tend-4):
    if raw[off]!=0xE8: continue
    site=nv(tva+off-tstart); rel=struct.unpack_from('<i',raw,off+1)[0]; tgt=nv(tva+off-tstart+5+rel)
    rawcalls[tgt].append(site)
ctor=defaultdict(set)
for w in write_rows:
    if w['addr_mode']=='ABS': continue
    own=owner(w['site'])
    if not own: continue
    try: off=va_off(own); code=raw[off:off+dict(atlas)[own]]
    except Exception: continue
    st={X86_REG_ECX:{'kind':'this','g':'','off':0,'idx':0}}; idx=0
    hit=None
    for ins in md.disasm(code,int(own,16)):
        if ins.id==0: continue
        idx+=1; site=nv(ins.address); ops=ins.operands
        if site==w['site']:
            if ins.id==X86_INS_MOV and len(ops)==2 and ops[0].type==X86_OP_MEM and ops[1].type==X86_OP_IMM:
                q=getstate(st,ops[0].mem.base,idx) if ops[0].mem.base is not None else None
                if q and q['kind']=='this':
                    hit=q['off']+ops[0].mem.disp
            break
        if ins.id in (X86_INS_MOV,X86_INS_LEA) and len(ops)==2:
            d,s=ops[0],ops[1]
            if d.type==X86_OP_REG:
                r=d.reg
                if s.type==X86_OP_IMM:
                    st[r]={'kind':'addrimm','g':nv(s.imm),'off':0,'idx':idx}
                elif s.type==X86_OP_REG:
                    q=getstate(st,s.reg,idx)
                    if q: st[r]={**q,'idx':idx}
                    else: st.pop(r,None)
                elif s.type==X86_OP_MEM and s.mem.index==0 and s.mem.base is not None:
                    q=getstate(st,s.mem.base,idx)
                    if q and q['kind']=='this': st[r]={'kind':'this','g':'','off':q['off']+s.mem.disp,'idx':idx}
                    else: st.pop(r,None)
                else: st.pop(r,None)
    if hit is None: continue
    for site in rawcalls.get(own,[]):
        cown=owner(site)
        if not cown: continue
        ecx,_,_=scan_state(cown,site,{})
        if not ecx or ecx['kind'] not in ('global','globalptr','addrimm'): continue
        g=ecx['g']; ctor[(g,hit)].add(w['vt'])
# Persist
rows=[]
for (g,off),vts in sorted(ctor.items()):
    for vt in sorted(vts): rows.append((g,str(off),vt))
with open(os.path.join(EV,'global_ctor_vptr_writes.tsv'),'w',encoding='utf-8',newline='') as f:
    f.write('global\toff\tvt\n')
    for r in rows: f.write('\t'.join(r)+'\n')
print('GLOBAL_CTOR_VPTR_WRITES',len(rows),'KEYS',len(ctor))
for r in rows[:60]: print('\t'.join(r))
