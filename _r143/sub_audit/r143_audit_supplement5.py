#!/usr/bin/env python3
"""R143 复核第五件（最后一件）：一次跑完 5 组取证。
 (a) 0x556519 是否位于 0x90 填充区（唯一多出的 1 个站点）
 (b) 栈基址 disp0 feed 是否真实（抽 2 个站点看上下文）
 (c) 838 张被偏移0装表的虚表里，有多少能在 vt-4 找到合法 MSVC RTTI COL 并解析出 .?AV 名
 (d) 用最终解析器复算 feed 数据流健全性（分支/目标污染）
 (e) 总 dword 内存间接 call/jmp 的四分类闭合校验（应等于 18804+391+4212+137）
"""
import re, json, struct, collections
import pefile
from capstone import Cs, CS_ARCH_X86, CS_MODE_32
P='ra2bench/gamemd.exe'; DATA=open(P,'rb').read(); N=len(DATA)
pe=pefile.PE(P,fast_load=True); IB=pe.OPTIONAL_HEADER.ImageBase
SECS=[dict(n=s.Name.decode().rstrip('\x00'),va=s.VirtualAddress,vs=s.Misc_VirtualSize,
           raw=s.PointerToRawData,rs=s.SizeOfRawData) for s in pe.sections]
T=[s for s in SECS if s['n']=='.text'][0]
def va2off(va):
    for s in SECS:
        lo=IB+s['va']
        if lo<=va<lo+max(s['vs'],s['rs']):
            d=va-lo; return s['raw']+d if d<s['rs'] else None
def rd(va,l):
    o=va2off(va); return None if o is None or o+l>N else DATA[o:o+l]
def dw(va):
    b=rd(va,4); return None if b is None else struct.unpack('<I',b)[0]
def sec_of(va):
    for s in SECS:
        lo=IB+s['va']
        if lo<=va<lo+max(s['vs'],s['rs']): return s['n']
def build():
    pat=re.compile(rb'\.\?A[VU][!-~]{1,200}?@@'); TDs={}
    for s in SECS:
        if s['n'] in ('.data','.rdata'):
            blob=DATA[s['raw']:s['raw']+s['rs']]
            for m in pat.finditer(blob):
                S=IB+s['va']+m.start(); v=dw(S-8)
                if v is not None and dw(S-4)==0 and sec_of(v) in ('.data','.rdata'):
                    TDs[S-8]=m.group().decode('latin1')
    td=set(TDs); COL=set()
    for s in SECS:
        if s['n'] in ('.data','.rdata'):
            blob=DATA[s['raw']:s['raw']+s['rs']]
            for i in range(len(blob)//4):
                v=struct.unpack_from('<I',blob,i*4)[0]
                if v in td:
                    c=IB+s['va']+i*4-12
                    if dw(c)==0 and dw(c+12)==v and dw(c+16)!=0: COL.add(c)
    V=set()
    for s in SECS:
        if s['n'] in ('.data','.rdata'):
            blob=DATA[s['raw']:s['raw']+s['rs']]
            for i in range(len(blob)//4):
                v=struct.unpack_from('<I',blob,i*4)[0]
                if v in COL:
                    vt=IB+s['va']+i*4+4
                    if dw(vt-4)==v: V.add(vt)
    return TDs,COL,V
TDs,COL,VTS=build()
GEN=('eax','ebx','ecx','edx','esi','edi'); STK=('esp','ebp')
SZ=('byte','word','dword','qword')
MEM=re.compile(r'^(?:(%s) ptr )?\[(.+)\]$'%'|'.join(SZ))
def pm(s):
    m=MEM.match(s or '')
    if not m:return None
    inner=re.sub(r'\s+','',m.group(2))
    toks=[t for t in inner.replace('-','+-').split('+') if t]
    b=i=None;sc=1;d=0
    for t in toks:
        if '*' in t:
            r,c=t.split('*');i,sc=r,int(c,0)
        elif re.fullmatch(r'[a-z]{2,3}',t):
            if b is None:b=t
            else:i,sc=t,1
        else:
            try:d+=int(t,0)
            except ValueError:return None
    return m.group(1),b,i,sc,d
IMM=re.compile(r'^-?(?:0x[0-9a-f]+|\d+)$')
def iv(t): return (int(t,16) if t.lstrip('-').startswith('0x') else int(t))&0xFFFFFFFF
KILL={'mov','movzx','movsx','lea','pop','bswap','lods'}
JCC={'ja','jae','jb','jbe','jc','je','jg','jge','jl','jle','jna','jnae','jnb','jnbe','jnc',
     'jne','jng','jnge','jnl','jnle','jno','jnp','jns','jnz','jo','jp','jpe','jpo','js','jz',
     'loop','loope','loopne','jecxz'}
RETM={'ret','retn','iret','iretd','leave'}
md=Cs(CS_ARCH_X86,CS_MODE_32);md.detail=False
def sweep(chunk=32768):
    off=T['raw'];end=T['raw']+T['rs']
    while off<end:
        blob=DATA[off:min(off+chunk,end)]
        base=IB+(T['va']+(off-T['raw']));cons=0
        for a,sz,mn,op in md.disasm_lite(blob,base):
            d=a-base
            if d+sz>len(blob):break
            cons=d+sz;yield a,sz,mn,op
        off+=cons if cons else 1

# (a) 填充区取证
pad=DATA[0x556500-IB-T['va']+T['raw']:0x556500-IB-T['va']+T['raw']+0x40] if False else None
o=va2off(0x5564f0); region=DATA[o:o+0x60]
pad_rows=[[hex(0x5564f0+i), region[i:i+16].hex()] for i in range(0,len(region),16)]
pad_zeros=sum(1 for b in region if b==0x90)

# (c) 装表覆盖的虚表 -> COL -> TD 名
install_vt=set(); install_sites=0
for a,sz,mn,op in sweep():
    if mn!='mov' or not op: continue
    ops=[x.strip() for x in re.split(r',(?![^\[]*\])',op)]
    if len(ops)!=2: continue
    m1=pm(ops[0])
    if m1 and m1[0]=='dword' and m1[1] in GEN and m1[2] is None and m1[4]==0 and IMM.match(ops[1]):
        v=iv(ops[1])
        if v in VTS: install_vt.add(v); install_sites+=1
named=[]; withcol=0; withnames=0
for vt in sorted(install_vt):
    col=dw(vt-4)
    ok = col in COL
    if ok:
        withcol+=1
        td=dw(col+12)
        nm=TDs.get(td)
        if nm: withnames+=1
    else:
        td=None; nm=None
    if len(named)<6:
        named.append({'vt':hex(vt),'vt_minus4':hex(col) if col is not None else None,
                      'col_valid':bool(ok),'td':hex(td) if td else None,'name':nm,
                      'slots':{hex(k):(hex(dw(vt+k)) if dw(vt+k) else None) for k in (0,4,8,0x0c,0x48)}})
# (d) 健全性
branch_targets=set(); branch_idx=set(); memo={}; pending={}; fed=[]; idx=0; sites=0
for a,sz,mn,op in sweep():
    if not op: idx+=1; continue
    ops=[x.strip() for x in re.split(r',(?![^\[]*\])',op)]
    mems=[m for m in (pm(x) for x in ops) if m]
    if mn in JCC or mn=='jmp':
        m=re.fullmatch(r'(0x[0-9a-f]+)',op)
        if m: branch_targets.add(int(m.group(1),16))
    if mn in JCC or mn in RETM or mn in ('call','jmp'): branch_idx.add(idx)
    ment=set(re.findall(r'\b(eax|ebx|ecx|edx|esi|edi)\b',op))
    for r in list(pending.keys()):
        if r in ment: pending.pop(r)
    if mn in ('call','jmp') and len(ops)==1 and mems and mems[0][0]=='dword' and mems[0][1] in GEN and mems[0][2] is None:
        sites+=1
        b=mems[0][1]; d=mems[0][4]; l=memo.get(b)
        if l and l[0]=='load':
            fed.append((a,b,d,l[3],l[1],l[2],l[4],idx))
    if mn in ('call','jmp'):
        for r in ('eax','ecx','edx'): memo[r]=('clobber',None,None,None,idx)
        idx+=1; continue
    if mn=='mov' and len(ops)==2:
        m2=pm(ops[1])
        if m2 and m2[0]=='dword' and ops[0] in GEN:
            memo[ops[0]]=('load',m2[1],m2[4],a,idx);
        elif ops[0] in GEN and mn in KILL: memo[ops[0]]=('other',None,None,None,idx)
    elif ops and ops[0] in GEN and mn in KILL: memo[ops[0]]=('other',None,None,None,idx)
    idx+=1
snd=collections.Counter(); snd0=collections.Counter()
for (a,b,d,la,lb,ld,li,di) in fed:
    cross=any(j in branch_idx for j in range(li+1,di)) or (a in branch_targets)
    k='contaminated' if cross else 'clean'
    snd[k]+=1
    if d==0: snd0[k]+=1

# (b) 栈基址 disp0 抽检上下文
stk_ctx=[]
cnt=0
for a,sz,mn,op in sweep():
    if a in (0x4bac46,0x5259a4,0x58cc74):
        o2=va2off(a-6); blk=DATA[o2:o2+0x14]
        rows=[[hex(i.address),i.bytes.hex(),i.mnemonic,i.op_str] for i in md.disasm(blk,a-6)][:6]
        stk_ctx.append([hex(a),rows])

# (e) 闭合校验
tot=0; cls=collections.Counter()
for a,sz,mn,op in sweep():
    if mn not in ('call','jmp') or not op: continue
    ops=[x.strip() for x in re.split(r',(?![^\[]*\])',op)]
    if len(ops)!=1: continue
    m=pm(ops[0])
    if not m or m[0]!='dword': continue
    tot+=1
    if m[2] is not None: cls['scaled_index']+=1
    elif m[1] in GEN: cls['gen_reg']+=1
    elif m[1] in STK: cls['stack']+=1
    else: cls['absolute']+=1

out={
 'a_padding_0x556519': {'window':pad_rows,'nop_count_in_0x60':pad_zeros,
   'objdump_or_capstone_note':'capstone 在 0x556519 解出 repz call *-0x6f6f6f70(%eax)，前一条为 0x556518 sahf，周围全是 0x90'},
 'b_stack_disp0_context':stk_ctx,
 'c_install_vtables':{'install_sites':install_sites,'distinct':len(install_vt),
   'with_valid_COL':withcol,'with_decorated_name':withnames,'samples':named},
 'd_feed_soundness':{'sites':sites,'fed_total':len(fed),'class':dict(snd),'disp0':dict(snd0)},
 'e_mem_indirect_total':{'total':tot,'by_class':dict(cls)},
}
json.dump(out,open('_r143/sub_audit/audit_supplement5.json','w'),ensure_ascii=False,indent=1)
print(json.dumps(out,ensure_ascii=False,indent=1))
