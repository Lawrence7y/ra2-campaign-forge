#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R192 B：1,013 个直接槽「同组同序号无匹配」的机械解释 + 四个实现的接口身份。
B1 535 个可比对对全是跨层（mdisp 不同）—— 逐对实测。
B2 逐对解出两个目标的结尾 ret imm16，统计「调用约定不兼容」对数（ret N 不同 ⇒ 物理上不可能共用入口）。
B3 逐对比较两目标前 16 字节，统计「同体不同址」（重复编出）对数。
B4 0x410450/0x410580/0x410590/0x4C9150 四个实现落到哪些 (接口层, 槽号) 上 —— 用接口身份而非猜名。
B5 四个地址在 .text 里被直接 call（E8 rel32）的次数。
"""
import sys, os, struct, collections, json, capstone
sys.path.insert(0,'/home/t628/projects/ra2-campaign-forge/_r185')
import pe185 as P

fails=[]; N=0
def ck(nm,c,d=''):
    global N; N+=1
    if not c: fails.append(nm)
    print(('PASS ' if c else 'FAIL ')+nm+((' | '+str(d)) if d!='' else ''))

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
        COL[base+4*i]=dict(mdisp=w[i+1],ptd=w[i+3],pchd=w[i+4],name=nm.decode('latin1'))
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
grp=collections.defaultdict(list)
for vt in sorted(VT): grp[COL[VT[vt]]['name']].append(vt)
ck('B0 基线 COL=1214 VT=1214 槽=14044 组=954',
   (len(COL),len(VT),sum(NS.values()),len(grp))==(1214,1214,14044,954),
   (len(COL),len(VT),sum(NS.values()),len(grp)))

def is_adj(va):
    o=P.r2o(va)
    if o is None: return False
    r=P.RAW[o:o+4]
    return (r[0:3]==b'\x83\x6c\x24' or r[0:3]==b'\x81\x6c\x24') and r[3]==0x04
direct=[]
for vt in sorted(VT):
    if COL[VT[vt]]['mdisp']==0: continue
    for k in range(NS[vt]):
        v=P.dw(vt+4*k)
        if not is_adj(v): direct.append((vt,k,v))
ck('B1 直接槽 1013', len(direct)==1013, len(direct))

md=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32)
def retn(va,budget=96):
    o=P.r2o(va)
    if o is None: return None
    for ins in md.disasm(P.RAW[o:o+budget],va):
        if ins.mnemonic=='ret':
            if ins.op_str: return int(ins.op_str,16)
            return 0
        if ins.mnemonic in ('jmp','int3','hlt') and ins.address>va: return 'jmp/other'
    return 'noret%db'%budget
def head(va,n=16):
    o=P.r2o(va)
    return None if o is None else P.RAW[o:o+n]

pairs=[]
for vt,k,v in direct:
    nm=COL[VT[vt]]['name']
    sibs=[t for t in grp[nm] if t!=vt and k<NS[t]]
    if not sibs: continue
    t=sorted(sibs)[0]; w=P.dw(t+4*k)
    if w==v: continue
    pairs.append((vt,k,v,t,w))
ck('B2 可比对对 535', len(pairs)==535, len(pairs))

cross=[p for p in pairs if COL[VT[p[0]]]['mdisp']!=COL[VT[p[3]]]['mdisp']]
ck('B3 535 对全部跨层（mdisp 不同）', len(cross)==535, len(cross))

retn_diff=0; retn_same=0; retn_inc=0; detail=[]
samebody=0
for vt,k,v,t,w in pairs:
    r1=retn(v); r2=retn(w)
    if isinstance(r1,int) and isinstance(r2,int):
        if r1!=r2: retn_diff+=1
        else: retn_same+=1
    else: retn_inc+=1
    h1=head(v); h2=head(w)
    if h1 and h2 and h1==h2: samebody+=1
    if len(detail)<8: detail.append((COL[VT[vt]]['name'],COL[VT[vt]]['mdisp'],k,hex(v),r1,COL[VT[t]]['mdisp'],hex(w),r2,h1.hex() if h1 else '',h2.hex() if h2 else ''))
print('B4 ret-N 不同 %d / 相同 %d / 不可解 %d（合计 %d）'%(retn_diff,retn_same,retn_inc,retn_diff+retn_same+retn_inc))
for d in detail: print('   ',d)
ck('B5 ret-N 不同 + 相同 + 不可解 == 535', retn_diff+retn_same+retn_inc==535)
print('B6 前 16 字节完全相同的对 =', samebody)

# 专门看「都返回 0」的对：0x410590(ret 4) vs 0x4C9150(ret 0) vs 0x410580(ret 8)
zero=collections.Counter()
for vt,k,v,t,w in pairs:
    if v in (0x410580,0x410590,0x4C9150) or w in (0x410580,0x410590,0x4C9150):
        zero[(hex(v),hex(w),retn(v),retn(w))]+=1
ck('B7 涉及三个零值桩的对数合计记录', True, sum(zero.values()))
for kk,c in zero.most_common(10): print('   ZERO-PAIR',kk,c)

# ---- B4/B5 四个实现的接口身份 ----
VF=0x7F9594
TD={}
for sn in ('.data','.rdata'):
    base,w,n=wv(sn)
    for i in range(n-2):
        if w[i]!=VF: continue
        va=base+4*i; nm=P.cstr(va+8,160)
        if nm and nm.startswith(b'.?A') and nm.endswith(b'@@'): TD[va]=nm.decode('latin1')
def layer_name(colva):
    c=COL[colva]; cand=[b for b in [P.dw(P.dw(c['pchd']+12)+4*j) for j in range(P.dw(c['pchd']+8))] if b is not None and P.dw(b+8)==c['mdisp']]
    return TD.get(P.dw(cand[0]),'?') if cand else '?'
TGT=[0x410450,0x410580,0x410590,0x4C9150]
idn=collections.defaultdict(collections.Counter)
refs=collections.Counter()
allslots=collections.Counter()
for vt,colva in VT.items():
    ln=layer_name(colva)
    for k in range(NS[vt]):
        v=P.dw(vt+4*k)
        allslots[v]+=1
        if v in TGT: idn[v][(ln,k)]+=1
for v in TGT:
    refs[v]=allslots[v]
    print('B8 %08x 被 %d 个槽引用；接口身份 Top6:'%(v,refs[v]))
    for (ln,k),c in idn[v].most_common(6): print('     ',ln,'槽',k,'x',c)
    ck('B8x %08x 至少被 1 个槽引用'%v, refs[v]>=1, refs[v])

# 直接 call 引用数（E8 rel32 与 FF15 绝对间址）
o0=P.r2o(LO); o1=P.r2o(HI)
body=P.RAW[o0:o1]
callc={v:0 for v in TGT}; callcc={v:0 for v in TGT}
for i in range(len(body)-5):
    if body[i]==0xE8:
        tgt=LO+i+5+struct.unpack_from('<i',body,i+1)[0]
        if tgt in callc: callc[tgt]+=1
    if body[i]==0xFF and body[i+1]==0x15:
        tgt=P.dw(struct.unpack_from('<I',body,i+2)[0])
        if tgt in callcc: callcc[tgt]+=1
for v in TGT: print('B9 %08x 直接 call rel32 = %d，call [abs] = %d'%(v,callc[v],callcc[v]))
ck('B9x 四地址 call 计数实测记录', True, {hex(k):(callc[k],callcc[k]) for k in TGT})

json.dump(dict(pairs=len(pairs),retn_diff=retn_diff,retn_same=retn_same,retn_inc=retn_inc,
               samebody=samebody,refs={hex(k):v for k,v in refs.items()},
               calls={hex(k):[callc[k],callcc[k]] for k in TGT},
               idn={hex(k):[[list(x),c] for x,c in idn[k].most_common(8)] for k in TGT},
               detail=detail), open('/home/t628/projects/ra2-campaign-forge/_r192/r192b.json','w'), indent=1)
print('断言 %d 条，FAIL %d 条'%(N,len(fails)))
sys.exit(1 if fails else 0)
