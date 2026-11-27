import sys,os,struct,collections
sys.path.insert(0,'/home/t628/projects/ra2-campaign-forge/_r185')
import pe185 as P
T=P.B['.text']; LO=T['lo']; HI=T['hi_file']
def in_text(x): return x is not None and LO<=x<HI
def wv(sn):
    s=P.B[sn]; n=s['rawsize']//4
    return s['lo'], struct.unpack_from('<%dI'%n,P.RAW,s['rawptr']), n
COL={}
for sn in ('.rdata','.data'):
    base,w,n=wv(sn)
    for i in range(n-4):
        if w[i] not in (0,1) or w[i+2]!=0: continue
        if P.where(w[i+3])!='.data' or P.where(w[i+4])!='.rdata': continue
        nm=P.cstr(w[i+3]+8,200)
        if not (nm and nm.startswith(b'.?A') and nm.endswith(b'@@')): continue
        COL[base+4*i]=(w[i+1],w[i+3],w[i+4],nm.decode('latin1'))
VT={}
for sn in ('.rdata','.data'):
    base,w,n=wv(sn)
    for i in range(n):
        if in_text(w[i]) and P.dw(base+4*i-4) in COL: VT[base+4*i]=P.dw(base+4*i-4)
def nslot(vt):
    k=0
    while in_text(P.dw(vt+4*k)): k+=1
    return k
NS={vt:nslot(vt) for vt in VT}
group=collections.defaultdict(list)
for vt in sorted(VT): group[COL[VT[vt]][3]].append(vt)
print('COL',len(COL),'VT',len(VT),'slot',sum(NS.values()),'grp',len(group),'multi',sum(1 for v in group.values() if len(v)>1))
def is_adj(va):
    o=P.r2o(va)
    if o is None: return False
    raw=P.RAW[o:o+4]
    return (raw[0:3]==b'\x83\x6c\x24' or raw[0:3]==b'\x81\x6c\x24') and raw[3]==0x04
direct=[]
for vt in sorted(VT):
    if COL[VT[vt]][0]==0: continue
    for k in range(NS[vt]):
        v=P.dw(vt+4*k)
        if not is_adj(v): direct.append((vt,k,v))
print('direct',len(direct))
# 同组同序号：兄弟表在槽 k 上是什么形态
import capstone
md=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32)
def dis1(va,n=3):
    o=P.r2o(va); out=[]
    if o is None: return out
    for ins in md.disasm_lite(P.RAW[o:o+16],va):
        out.append(ins)
        if len(out)>=n: break
    return out
stat=collections.Counter()
examples=[]
for vt,k,v in direct:
    nm=COL[VT[vt]][3]
    sib=[t for t in group[nm] if t!=vt and k<NS[t]]
    if not sib: stat['nosib']+=1; continue
    for t in sib:
        w2=P.dw(t+4*k)
        if w2==v: stat['same_value']+=1; break
        if is_adj(w2):
            # thunk: 找 jmp 目标
            d=dis1(w2,3)
            tgt=None
            for it in d:
                if it[2].startswith('jmp'): tgt=it[1] if False else None
            # 用 capstone detail 单点
            cs_ins=list(md.disasm(P.RAW[P.r2o(w2):P.r2o(w2)+16],w2))
            tgt=None
            for ins in cs_ins:
                if ins.mnemonic=='jmp' and ins.op_str.startswith('0x'): tgt=int(ins.op_str,16)
            if tgt==v: stat['thunk_to_same']+=1
            else: stat['thunk_to_other']+=1
            break
        else:
            stat['direct_other']+=1
            if len(examples)<8: examples.append((hex(vt),k,hex(v),hex(t),hex(w2),nm))
            break
print(stat)
for e in examples: print(e)
