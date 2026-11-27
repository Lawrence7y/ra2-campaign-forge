#!/usr/bin/env python3
"""R143 复核第四件：数据流健全性（跨基本块污染）+ 栈基址 disp0 feed 的样本抽检。

目的：主会话 C2 用“基址寄存器最近一次定义”回溯，但没有做基本块截断。
这里量化：18,803 个派发点里，回溯链是否跨越了控制流边界（中间有分支/ret/call，
或派发地址本身是某个分支的目标）。
"""
import re, json, struct, collections, random
import pefile
from capstone import Cs, CS_ARCH_X86, CS_MODE_32
P='ra2bench/gamemd.exe'; DATA=open(P,'rb').read()
pe=pefile.PE(P,fast_load=True); IB=pe.OPTIONAL_HEADER.ImageBase
SECS=[dict(name=s.Name.decode().rstrip('\x00'),va=s.VirtualAddress,vs=s.Misc_VirtualSize,
           raw=s.PointerToRawData,rs=s.SizeOfRawData) for s in pe.sections]
T=[s for s in SECS if s['name']=='.text'][0]
def va2off(va):
    for s in SECS:
        lo=IB+s['va']
        if lo<=va<lo+max(s['vs'],s['rs']):
            d=va-lo; return s['raw']+d if d<s['rs'] else None
def rd(va,l):
    o=va2off(va); return None if o is None else DATA[o:o+l]
def dw(va):
    b=rd(va,4); return None if b is None else struct.unpack('<I',b)[0]
def sec_of(va):
    for s in SECS:
        lo=IB+s['va']
        if lo<=va<lo+max(s['vs'],s['rs']): return s['name']
def build_vtset():
    pat=re.compile(rb'\.\?A[VU][!-~]{1,200}?@@'); TDs={}
    for s in SECS:
        if s['name'] in ('.data','.rdata'):
            blob=DATA[s['raw']:s['raw']+s['rs']]
            for m in pat.finditer(blob):
                S=IB+s['va']+m.start(); v=dw(S-8)
                if v is not None and dw(S-4)==0 and sec_of(v) in ('.data','.rdata'): TDs[S-8]=1
    td=set(TDs); COL=set()
    for s in SECS:
        if s['name'] in ('.data','.rdata'):
            blob=DATA[s['raw']:s['raw']+s['rs']]
            for i in range(len(blob)//4):
                v=struct.unpack_from('<I',blob,i*4)[0]
                if v in td:
                    c=IB+s['va']+i*4-12
                    if dw(c)==0 and dw(c+12)==v and dw(c+16)!=0: COL.add(c)
    V=set()
    for s in SECS:
        if s['name'] in ('.data','.rdata'):
            blob=DATA[s['raw']:s['raw']+s['rs']]
            for i in range(len(blob)//4):
                v=struct.unpack_from('<I',blob,i*4)[0]
                if v in COL:
                    vt=IB+s['va']+i*4+4
                    if dw(vt-4)==v: V.add(vt)
    return V
VTS=build_vtset()
GEN=('eax','ebx','ecx','edx','esi','edi'); STK=('esp','ebp')
SZ=('byte','word','dword','qword')
MEM=re.compile(r'^(?:(%s) ptr )?\[(.+)\]$'%'|'.join(SZ))
def pm(s):
    m=MEM.match(s or '')
    if not m: return None
    inner=re.sub(r'\s+','',m.group(2))
    toks=[t for t in inner.replace('-','+-').split('+') if t]
    b=i=None; sc=1; d=0
    for t in toks:
        if '*' in t:
            r,c=t.split('*'); i,sc=r,int(c,0)
        elif re.fullmatch(r'[a-z]{2,3}',t):
            if b is None: b=t
            else: i,sc=t,1
        else:
            try: d+=int(t,0)
            except ValueError: return None
    return m.group(1),b,i,sc,d
KILL={'mov','movzx','movsx','lea','pop','bswap','lods'}
RETM={'ret','retn','iret','iret','leave'}
md=Cs(CS_ARCH_X86,CS_MODE_32); md.detail=False
def sweep(chunk=32768):
    off=T['raw']; end=T['raw']+T['rs']
    while off<end:
        blob=DATA[off:min(off+chunk,end)]
        base=IB+(T['va']+(off-T['raw'])); cons=0
        for a,sz,mn,op in md.disasm_lite(blob,base):
            d=a-base
            if d+sz>len(blob): break
            cons=d+sz; yield a,sz,mn,op
        off+=cons if cons else 1

REG_JUMP={'jmp','ja','jae','jb','jbe','jc','je','jg','jge','jl','jle','jna','jnae',
          'jnb','jnbe','jnc','jne','jng','jnge','jnl','jnle','jno','jnp','jns','jnz',
          'jo','jp','jpe','jpo','js','jz','loop','loope','loopne','jecxz'}
branch_addr=set()      # 所有分支目标
branch_insn_idx=set()  # 分支/ret/call 所在指令序号
memo={}; pending={}; fed=[]
idx=0; n_sites=0
for a,sz,mn,op in sweep():
    if not op: idx+=1; continue
    ops=[x.strip() for x in re.split(r',(?![^\[]*\])',op)]
    mems=[pm(o) for o in ops]; mems=[m for m in mems if m]
    if mn in REG_JUMP or mn in RETM or mn in ('call',):
        branch_insn_idx.add(idx)
    if mn in REG_JUMP:
        m=re.fullmatch(r'(0x[0-9a-f]+)',op)
        if m: branch_addr.add(int(m.group(1),16))
    # 使用分类结束 pending（只为统计机会分母，沿用主脚本口径）
    ment=set(re.findall(r'\b(eax|ebx|ecx|edx|esi|edi)\b',op))
    for r in list(pending.keys()):
        if r in ment: pending.pop(r)
    if mn in ('call','jmp') and len(ops)==1 and mems and mems[0][0]=='dword' and mems[0][1] in GEN:
        n_sites+=1
        b=mems[0][1]
        l=memo.get(b)
        if l and l[0]=='load':
            fed.append((a,mn,b,mems[0][4],l[3],l[1],l[2],l[4],idx))
    if mn in ('call','jmp'):
        for r in ('eax','ecx','edx'): memo[r]=('clobber',None,None,None,idx)
        idx+=1; continue
    if mn=='mov' and len(ops)==2:
        m1=pm(ops[0]); m2=pm(ops[1])
        if m2 and m2[0]=='dword' and ops[0] in GEN:
            memo[ops[0]]=('load',m2[1],m2[4],a,idx)
        elif ops[0] in GEN and mn in KILL:
            memo[ops[0]]=('other',None,None,None,idx)
    elif ops and ops[0] in GEN and mn in KILL:
        memo[ops[0]]=('other',None,None,None,idx)
    idx+=1

# 交叉分析：中间是否有分支/ret/call，或派发地址本身是分支目标
res_cls=collections.Counter()
res_disp=collections.defaultdict(collections.Counter)
samples_cross=[]
for (a,mn,reg,d,la,lb,ld,li,di) in fed:
    cross_insn=any(j in branch_insn_idx for j in range(li+1,di))
    cross_target=a in branch_addr
    key='clean' if not (cross_insn or cross_target) else ('target' if cross_target else 'branch_inside')
    res_cls[key]+=1
    res_disp[d][key]+=1
    if key!='clean' and len(samples_cross)<8:
        samples_cross.append([hex(a),mn,reg,d,hex(la),lb,ld,di-li,key])

# 栈基址 disp0 feed 抽样
stk0=[(a,mn,reg,d,la,lb,ld) for (a,mn,reg,d,la,lb,ld,li,di) in fed if lb in STK and d==0][:12]
obj0=[(a,mn,reg,d,la,lb,ld) for (a,mn,reg,d,la,lb,ld,li,di) in fed if lb in GEN and d==0][:12]

out={
 'sites':n_sites,'fed_total':len(fed),
 'fed_soundness':dict(res_cls),
 'fed_by_dispatch_disp':{str(k):dict(v) for k,v in sorted(res_disp.items())[:12]},
 'cross_samples':samples_cross,
 'stk_disp0_fed_samples':[[hex(x[0]),x[1],x[2],hex(x[3]),hex(x[4]),x[5],x[6]] for x in stk0],
 'obj_disp0_fed_samples':[[hex(x[0]),x[1],x[2],hex(x[3]),hex(x[4]),x[5],x[6]] for x in obj0],
}
json.dump(out,open('_r143/sub_audit/audit_supplement3.json','w'),ensure_ascii=False,indent=1)
print(json.dumps(out,ensure_ascii=False,indent=1))
