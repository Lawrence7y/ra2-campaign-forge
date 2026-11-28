# -*- coding: utf-8 -*-
"""R213 x8：律 X 的形态细则 —— 次视图内 adjustor 槽的位置分布（哪些槽是 adjustor、哪些是真函数体），
并核验 「adjustor 视图 = 该视图覆盖的多继承基类方法集」，含 jmp 目标归属与正反控。
"""
import sys,struct,collections,json
sys.path.insert(0,'/home/t628/projects/ra2-campaign-forge/_r185')
import pe185 as P
from capstone import Cs,CS_ARCH_X86,CS_MODE_32
md=Cs(CS_ARCH_X86,CS_MODE_32)
def s32(v): return struct.unpack('<i',struct.pack('<I',v&0xffffffff))[0]
def ins(a,n=6,maxb=48):
    o=P.r2o(a); out=[]
    if o is None: return out
    for i in md.disasm(P.RAW[o:o+maxb],a):
        out.append((i.address,i.mnemonic,i.op_str))
        if len(out)>=n: break
    return out
def adj(a):
    q=ins(a,3)
    if len(q)<2: return (False,None,None)
    if q[0][1]=='sub' and 'esp + 4' in q[0][2] and q[1][1]=='jmp':
        try: imm=int(q[0][2].split(',')[-1].strip(),16)
        except Exception: return (False,None,None)
        jt=int(q[1][2],16) if q[1][2].startswith('0x') else None
        return (True,imm,jt)
    return (False,None,None)
COL={}
for sn in ('.rdata','.data'):
    s=P.B[sn]; n=s['rawsize']//4; base=s['lo']
    w=struct.unpack_from('<%dI'%n,P.RAW,s['rawptr'])
    for k in range(n-4):
        if w[k] not in (0,1,2) or w[k+2]!=0: continue
        if P.where(w[k+3])!='.data' or P.where(w[k+4])!='.rdata': continue
        nm=P.cstr(w[k+3]+8,400)
        if not (nm and nm.startswith(b'.?A') and nm.endswith(b'@@')): continue
        COL[base+4*k]=dict(mdisp=s32(w[k+1]),pTD=w[k+3],pCHD=w[k+4],name=nm.decode('latin1'))
VT={}
for sn in ('.rdata','.data'):
    s=P.B[sn]; n=s['rawsize']//4; base=s['lo']
    w=struct.unpack_from('<%dI'%n,P.RAW,s['rawptr'])
    for k in range(n-1):
        if w[k] in COL and P.where(w[k+1])=='.text': VT[w[k]]=base+4*k+4
SL={}
for c in COL:
    k=0
    while k<4096 and P.where(P.dw(VT[c]+4*k))=='.text': k+=1
    SL[c]=[P.dw(VT[c]+4*i) for i in range(k)]
NA=0;F=[]
def ck(n,c,d=''):
    global NA; NA+=1
    if not c: F.append(n)
    print(('PASS ' if c else 'FAIL ')+n+((' | '+str(d)) if d!='' else ''))
SEC=[c for c in COL if COL[c]['mdisp']!=0]
# 按 (mdisp, 视图长度) 分组，统计每个槽位 idx 是 adjustor 的类数
grp=collections.defaultdict(list)
for c in SEC:
    if adj(SL[c][0])[0]: grp[(COL[c]['mdisp'],len(SL[c]))].append(c)
print('=== 次视图形态分组 ===')
for k in sorted(grp):
    cs=grp[k]; L=k[1]
    pat=[]
    for i in range(L):
        n_adj=sum(1 for c in cs if adj(SL[c][i])[0] and adj(SL[c][i])[1]==k[0])
        n_other=len(cs)-n_adj
        pat.append('A' if n_adj==len(cs) else ('F' if n_adj==0 else '?'))
    cnt=collections.Counter(''.join(pat))
    print('  mdisp=%-6d len=%-3d n=%-3d 槽型(全类一致)=%s'%(k[0],L,len(cs),cnt.most_common(3)))
    ck('G%r 全类槽型一致（无 ? 混合）'%(k,), '?' not in ''.join(pat), ''.join(pat))
# 反控：jmp 目标是否落在 .text 且 != adjustor 自身
print('\n=== adjustor 的 jmp 目标核验 ===')
tgt=collections.Counter(); selfj=0; out_text=0
for c in SEC:
    for s in SL[c]:
        ok,imm,jt=adj(s)
        if not ok: continue
        if jt is None: out_text+=1; continue
        tgt[jt]+=1
        if jt==s: selfj+=1
print('  不同 jmp 目标数=%d ; 跳回自身=%d ; 目标不可解=%d'%(len(tgt),selfj,out_text))
print('  目标段分布 =',collections.Counter(P.where(t) for t in tgt).most_common())
ck('X1 全部 adjustor 的 jmp 目标是 .text', all(P.where(t)=='.text' for t in tgt), len(tgt))
ck('X2 无 adjustor 跳到自身（非空转）', selfj==0, selfj)
# 目标是否被别的视图共享（跳板复用）
print('  最高频 jmp 目标 top6 =',[(hex(k),v) for k,v in tgt.most_common(6)])
# 反控：同一类的两视图（主/次）是否共享 jmp 目标
print('\n=== 反控：次视图 adjustor 目标 vs 主视图槽 ===')
share=0; tot=0
byt=collections.defaultdict(list)
for c in COL: byt[COL[c]['pCHD']].append(c)
for chd,cs in byt.items():
    main=[c for c in cs if COL[c]['mdisp']==0]
    if len(main)!=1: continue
    m=main[0]; mset=set(SL[m])
    for c in cs:
        if COL[c]['mdisp']==0: continue
        for s in SL[c]:
            ok,imm,jt=adj(s)
            if ok and jt is not None:
                tot+=1
                if jt in mset: share+=1
print('  次视图 adjustor 总数=%d ; 其 jmp 目标出现在本类主视图槽中 = %d'%(tot,share))
ck('X3 至少部分 adjustor 目标是本类主视图方法（多继承 forwarding）', share>0, '%d/%d'%(share,tot))
print('\n断言 %d / FAIL %d %s'%(NA,len(F),F))
json.dump({'grp':{'%d_%d'%k:len(v) for k,v in grp.items()},'tgt':len(tgt),
 'share':share,'tot':tot,'selfj':selfj,'nassert':NA,'fails':F},
 open('_r213/x8.json','w'),indent=1,ensure_ascii=False)
