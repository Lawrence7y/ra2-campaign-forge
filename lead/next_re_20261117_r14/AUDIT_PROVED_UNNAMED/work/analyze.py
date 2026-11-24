
import sys, json, pefile
from capstone import *
from capstone.x86 import *

EXE = r'D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe'
pe = pefile.PE(EXE, fast_load=True)
IB = pe.OPTIONAL_HEADER.ImageBase
secs=[(s.Name.rstrip(b'\x00').decode('latin1'), IB+s.VirtualAddress, s.Misc_VirtualSize, s.PointerToRawData, s.SizeOfRawData) for s in pe.sections]
raw=open(EXE,'rb').read()
SECT={n:(b,vs,pr,rs) for n,b,vs,pr,rs in secs}
def sec_of(va):
    for n,(b,vs,pr,rs) in SECT.items():
        if b<=va<b+max(vs,rs): return (n,b,vs,pr,rs)
def read(va,n):
    s=sec_of(va)
    if not s: return b''
    n_,b,vs,pr,rs=s
    return raw[pr+(va-b):pr+(va-b)+n]
def dword(va):
    b=read(va,4); return int.from_bytes(b,'little') if len(b)==4 else None
md=Cs(CS_ARCH_X86,CS_MODE_32); md.detail=True; md.skipdata=True
ATLAS={}
for ln in open(r'D:\Project\ra2-campaign-forge\lead\next_re_20261112_r10\W130_atlas\function_atlas.tsv',encoding='utf-8'):
    p=ln.rstrip('\n').split('\t')
    if len(p)<6 or p[0]=='entry': continue
    try: ATLAS[int(p[0],16)]=(int(p[1]),int(p[2]),int(p[3]),int(p[4]))
    except: pass
def decode(va,n): return [i for i in md.disasm(read(va,n),va) if i.id!=0]
def bounds(entry):
    hint=ATLAS.get(entry,(0,0,0,0))[0]
    insns=decode(entry,max(4096,hint+64))
    if hint:
        end=entry+hint
        body=[i for i in insns if i.address<end]
        ok=bool(body) and body[-1].address+body[-1].size==end
        tail=read(end,8)
        pad=all(c in (0xCC,0x90,0x00) for c in tail) if tail else True
        return body,end,{'hint':hint,'decode_exact':ok,'pad_after':pad,'next_atlas':end in ATLAS,'tail':tail.hex()}
    pos=entry
    for i,ins in enumerate(insns):
        pos=ins.address+ins.size
        t=read(pos,8)
        if t and all(c in (0xCC,0x90,0x00) for c in t) and i>0: break
    return [x for x in insns if x.address<pos],pos,{'hint':0,'decode_exact':True,'pad_after':True,'next_atlas':pos in ATLAS,'tail':read(pos,8).hex()}
RDATA=(0x7e1000,0x811074)
def in_rdata(va): return RDATA[0]<=va<RDATA[1]
def rtti(vt):
    col=dword(vt-4)
    if not col or not (0x400000<=col<0x8A0000): return None
    td=dword(col+0xC)
    if not td or not (0x400000<=td<0x8A0000): return None
    try: return read(td+8,160).split(b'\x00')[0].decode('latin1')
    except: return None

def analyze(entry):
    body,end,bf=bounds(entry)
    aliases={'ecx'}
    changed=True
    while changed:
        changed=False
        for ins in body:
            o=ins.operands
            if ins.mnemonic in ('mov','lea') and len(o)==2 and o[0].type==CS_OP_REG and o[1].type==CS_OP_REG:
                if ins.reg_name(o[1].reg) in aliases and ins.reg_name(o[0].reg) not in aliases:
                    aliases.add(ins.reg_name(o[0].reg)); changed=True
    thisw=[];thisr=[];otherw=[];otherr=[];gr=set();gw=set();imms=set();calls=[];rets=[];jcc=0
    for ins in body:
        o=ins.operands
        for idx,op in enumerate(o):
            if op.type==CS_OP_MEM:
                base=ins.reg_name(op.mem.base) if op.mem.base else ''
                if op.mem.base==0 and op.mem.index==0:
                    (gw if idx==0 else gr).add(op.mem.disp)
                elif base in aliases:
                    (thisw if idx==0 else thisr).append((base,op.mem.disp,'%08X'%ins.address,ins.mnemonic))
                elif base not in ('esp','ebp'):
                    (otherw if idx==0 else otherr).append((base,op.mem.disp,'%08X'%ins.address,ins.mnemonic))
            if op.type==CS_OP_IMM and 0x400000<=op.imm<0x8A0000: imms.add(op.imm)
        if ins.mnemonic in ('call','jmp'):
            for op in ins.operands:
                if op.type==CS_OP_IMM: calls.append(('%08X'%ins.address,ins.mnemonic,'%08X'%op.imm))
        if ins.mnemonic.startswith('ret'): rets.append(('%08X'%ins.address,ins.op_str))
        if ins.mnemonic.startswith('j') and ins.mnemonic!='jmp': jcc+=1
    vptr=[]
    for ins in body:
        o=ins.operands
        if ins.mnemonic=='mov' and len(o)==2 and o[0].type==CS_OP_MEM and o[1].type==CS_OP_IMM:
            nm=rtti(o[1].imm) if 0x400000<=o[1].imm<0x8A0000 else None
            if nm: vptr.append(('%08X'%ins.address, ins.reg_name(o[0].mem.base) if o[0].mem.base else '', o[0].mem.disp, hex(o[1].imm), nm))
    vts=[];strs=[]
    for v in imms:
        nm=rtti(v)
        if nm: vts.append((hex(v),nm))
        b=read(v,40) if in_rdata(v) else b''
        if len(b)>=4 and all(32<=c<127 for c in b[:4]):
            s=b.split(b'\x00')[0]
            if 4<=len(s)<40: strs.append((hex(v),s.decode('latin1')))
    return dict(entry='%08X'%entry, insns=len(body), size=end-entry, bflags=bf, jcc=jcc,
        thisw=sorted(set((d,m) for b_,d,a_,m in thisw)), thisr=sorted(set((d,m) for b_,d,a_,m in thisr)),
        otherw=sorted(set((b_,d,m) for b_,d,a_,m in otherw)),
        w94=[x for x in thisw+otherw if x[1]==0x94],
        ncalls=len(calls), calls=calls, rets=rets, vts=vts, strings=strs, vptr=vptr,
        globals_w=sorted(gw), globals_r=sorted(gr))
if __name__=='__main__':
    ents=[int(x,16) for x in sys.argv[1:]]
    res={}
    for e in ents:
        a=analyze(e); res[a['entry']]=a
        body,end,bf=bounds(e)
        with open(r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\AUDIT_PROVED_UNNAMED\EVIDENCE\asm_%08X.txt'%e,'w',encoding='utf-8') as f:
            f.write('# entry=%08X atlas=%d my_size=%d n=%d flags=%s\n'%(e,bf['hint'],end-e,len(body),bf))
            for ins in body: f.write('%08X  %-26s %s %s\n'%(ins.address,ins.bytes.hex(),ins.mnemonic,ins.op_str))
    open(r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\AUDIT_PROVED_UNNAMED\work\last.json','w',encoding='utf-8').write(json.dumps(res,ensure_ascii=True,default=str))
