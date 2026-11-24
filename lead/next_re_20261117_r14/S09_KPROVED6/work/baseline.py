"""S09-KPROVED6 ③b base rate, seed 20261119, 2000 draws of 8 without replacement.
strict = D-42 four HARD conditions; loose = strict OR rule#1 (>=3 gates, distinct arm actions)."""
import json, random
from pathlib import Path
import pefile, capstone
from capstone.x86 import X86_OP_IMM, X86_OP_MEM
REG_ESP=capstone.x86.X86_REG_ESP
ROOT=Path(r'D:\Project\ra2-campaign-forge'); OUT=ROOT/'lead/next_re_20261117_r14/S09_KPROVED6'
raw=(ROOT/'ra2youli/gamemd.exe').read_bytes(); pe=pefile.PE(data=raw,fast_load=True); ib=pe.OPTIONAL_HEADER.ImageBase
secs=[dict(va=ib+s.VirtualAddress,rs=s.SizeOfRawData,ptr=s.PointerToRawData) for s in pe.sections]; S0=secs[0]
tva=S0['va']; tlen=S0['rs']
def in_text(v): return v is not None and tva<=v<tva+tlen
md=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32); md.detail=True; md.skipdata=True
JCC={'je','jne','jz','jnz','jg','jge','jl','jle','ja','jae','jb','jbe','js','jns','jo','jno','jp','jnp','jecxz','jcxz'}
sz=bytearray(tlen+16); kind=bytearray(tlen+16); tgt={}; im={}; RET=1;JMP=2;JCCK=3
for ins in md.disasm(raw[S0['ptr']:S0['ptr']+tlen],tva):
    o=ins.address-tva
    if o>=len(sz): break
    sz[o]=ins.size; im[o]=ins; mn=ins.mnemonic
    if mn=='ret' or mn.startswith('ret'): kind[o]=RET
    elif mn=='jmp':
        kind[o]=JMP
        if ins.operands and ins.operands[0].type==X86_OP_IMM: tgt[o]=int(ins.operands[0].imm)&0xffffffff
    elif mn in JCC:
        kind[o]=JCCK
        if ins.operands and ins.operands[0].type==X86_OP_IMM: tgt[o]=int(ins.operands[0].imm)&0xffffffff
def extent(e,cap=6000):
    seen=set(); st=[e]; adds=[]; n=0; lo=hi=e
    while st:
        a=st.pop()
        while True:
            if not in_text(a) or a in seen: break
            o=a-tva; s=sz[o]
            if s==0: break
            seen.add(a); adds.append(a); n+=1
            if n>cap: st=[]; break
            if a<lo: lo=a
            if a+s>hi: hi=a+s
            k=kind[o]
            if k==RET: break
            if k==JMP:
                t=tgt.get(o)
                if t: st.append(t)
                break
            if k==JCCK:
                t=tgt.get(o)
                if t: st.append(t)
                a+=s; continue
            a+=s
    return lo,hi,sorted(adds)
HARD={'mov','add','sub','inc','dec','and','or','xor','movzx','movsx','lea'}
def detect(e):
    lo,hi,adds=extent(e)
    if len(adds)<3: return (False,False)
    rs=set(adds); jt=er=sh=lp=r1=False; vtw=0; flds=set(); arms=[]; be=[]; lw=0; bc=0; retconsts=set()
    for a in adds:
        o=a-tva; ins=im.get(o)
        if ins is None: continue
        mn=ins.mnemonic; ops=ins.operands
        if mn=='jmp' and ops and ops[0].type==X86_OP_MEM:
            m=ops[0].mem
            if m.index!=0 and m.scale in (2,4,8): jt=True
        if mn in ('cmp','test'):
            for op in ops:
                if op.type==X86_OP_IMM:
                    v=int(op.imm)&0xffffffff
                    if v==0xffffffff or 0x80000000<=v<=0x800fffff: er=True
        # return-convention constants: mov eax/reg, imm in 0x8000xxxx or -1 or 0/1 near a ret
        if mn in ('mov','xor','or') and ops and len(ops)>=2 and ops[0].type==capstone.x86.X86_OP_REG:
            if mn=='mov' and ops[1].type==X86_OP_IMM:
                v=int(ops[1].imm)&0xffffffff
                if 0x80000000<=v<=0x800fffff or v==0xffffffff: er=True
                if ops[0].reg==capstone.x86.X86_REG_EAX and v in (0,1,0xffffffff): retconsts.add(v)
            if mn in ('xor','or') and len(ops)>=2 and ops[0].type==capstone.x86.X86_OP_REG and ops[1].type==capstone.x86.X86_OP_REG and ops[0].reg==ops[1].reg: retconsts.add(0)
        if ops and ops[0].type==X86_OP_MEM and mn=='mov':
            if len(ops)>1 and ops[1].type==X86_OP_IMM:
                v=int(ops[1].imm)&0xffffffff
                if 0x7e0000<=v<0x800000 and ops[0].mem.base!=REG_ESP: vtw+=1
            m=ops[0].mem
            if m.disp and m.disp>=0x8 and m.base!=REG_ESP: flds.add(m.disp)
        if mn in JCC and ops and ops[0].type==X86_OP_IMM:
            t=int(ops[0].imm)&0xffffffff
            if t in rs and t>a:
                acts=set()
                for b in adds:
                    if a<b<t:
                        bi=im.get(b-tva)
                        if bi is None: continue
                        if bi.mnemonic=='call' and bi.operands and bi.operands[0].type==X86_OP_IMM: acts.add(('c',int(bi.operands[0].imm)&0xffffffff))
                        elif bi.operands and bi.operands[0].type==X86_OP_MEM and bi.mnemonic in HARD and bi.operands[0].mem.base!=REG_ESP: acts.add(('w',bi.operands[0].mem.disp))
                if acts: arms.append(acts)
        if o in tgt and kind[o] in (JMP,JCCK):
            t=tgt[o]
            if lo<=t<=a:
                be.append(1)
                for b in adds:
                    if t<=b<=a:
                        bi=im.get(b-tva)
                        if bi is None: continue
                        if bi.mnemonic in HARD and bi.operands and bi.operands[0].type==X86_OP_MEM: lw+=1
                        if bi.mnemonic in ('cmp','test') or (bi.mnemonic=='dec' and bi.operands and bi.operands[0].type==capstone.x86.X86_OP_REG): bc+=1
    if len(retconsts)>=2 or (len(retconsts)>=1 and er): er=True
    if vtw>=2 or len(flds)>=10: sh=True
    # loop: backedge + boundary cmp in loop span + (mem write or callee call in loop span)
    spans=[]
    for a in adds:
        o=a-tva
        if o in tgt and kind[o] in (JMP,JCCK):
            t=tgt[o]
            if lo<=t<=a: spans.append((t,a))
    has_action=False
    for (t,a) in spans:
        for b in adds:
            if not (t<=b<=a): continue
            bi=im.get(b-tva)
            if bi is None: continue
            if bi.mnemonic=='call' or (bi.mnemonic in HARD and bi.operands and bi.operands[0].type==X86_OP_MEM and bi.operands[0].mem.base!=REG_ESP):
                has_action=True
    if spans and bc>=1 and has_action: lp=True
    strict=jt or er or sh or lp
    aa=set()
    for x in arms: aa|=x
    nd=len([x for x in aa if x[0]=='c'])+len([x for x in aa if x[0]=='w'])
    if (len(arms)>=3 and nd>=2) or (len(arms)>=2 and nd>=3): r1=True
    return (strict, strict or r1)
COV=ROOT/'lead/next_re_20261117_r14/COVERAGE/coverage.tsv'; lines=COV.read_text(encoding='utf-8-sig').splitlines(); hdr=lines[0].split(',')
pool=[]
for l in lines[1:]:
    if not l.strip(): continue
    q=l.split('\t'); q+=['']*(8-len(q)); r=dict(zip(hdr,q[:8]))
    if r['subsystem'].strip().upper()!='S09' or r['grade'].strip()!='[静态推断]': continue
    en=r['entry'].strip().upper().replace('0X','')
    if in_text(int(en,16)): pool.append(en)
print('pool N=',len(pool))
fl={e:detect(int(e,16)) for e in pool}
ns=sum(1 for e in pool if fl[e][0]); nl=sum(1 for e in pool if fl[e][1]); ps=ns/len(pool); pl=nl/len(pool)
print('strict K=%d p=%.6f E8=%.6f'%(ns,ps,8*ps)); print('loose  K=%d p=%.6f E8=%.6f'%(nl,pl,8*pl))
random.seed(20261119); mcs=[]; mcl=[]
for _ in range(2000):
    sm=random.sample(pool,8); mcs.append(sum(fl[e][0] for e in sm)); mcl.append(sum(fl[e][1] for e in sm))
mc_s=sum(mcs)/2000; mc_l=sum(mcl)/2000
print('MC strict=%.6f MC loose=%.6f'%(mc_s,mc_l))
out=dict(pool_n=len(pool),seed=20261119,draws=2000,
   strict=dict(K=ns,p=ps,E8=8*ps,MC=mc_s),loose=dict(K=nl,p=pl,E8=8*pl,MC=mc_l),
   operation='strict=D42 four hard: scaled-index indirect jmp OR -1/HRESULT return-constant/falsifiable sentinel OR >=2 vt-writes/>=10 field writes OR backedge+boundary-cmp+action(call or mem-write) loop; loose=strict OR rule#1 >=3 gates with >=3 distinct arm actions(call target or write disp)')
json.dump(out,open(OUT/'EVIDENCE/baseline_3b.json','w'),ensure_ascii=False,indent=1)
json.dump({e:list(fl[e]) for e in pool},open(OUT/'work/baseline_flags.json','w'))
print('saved')

