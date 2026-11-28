# -*- coding: utf-8 -*-
"""R215 m2：反控与族归属检验（主会话独立）。
Q1 口径反控：槽18『目标只出现在本槽号』是否 slot18 特有？（对每个槽号做同法统计）
Q2 族归属：共享同一 slot18 目标的类，其视图是否共享一段相同的前缀槽序列？
Q3 18 个单类目标的族分布（Locomotion 等）。
"""
import sys,struct,json,collections
sys.path.insert(0,'/home/t628/projects/ra2-campaign-forge/_r185')
import pe185 as P, capstone
def s32(v): return struct.unpack('<i',struct.pack('<I',v&0xffffffff))[0]
def words(sn):
    s=P.B[sn]; n=s['rawsize']//4
    return struct.unpack_from('<%dI'%n,P.RAW,s['rawptr']), s['lo']
COLA={}
for sn in ('.rdata','.data'):
    w,base=words(sn)
    for k in range(len(w)-4):
        if w[k]>2 or w[k+2]!=0: continue
        if P.where(w[k+3])!='.data' or P.where(w[k+4])!='.rdata': continue
        nm=P.cstr(w[k+3]+8,512)
        if not nm or nm[:3]!=b'.?A' or nm[-2:]!=b'@@': continue
        COLA[base+4*k]=(s32(w[k+1]),w[k+3],w[k+4],nm.decode('latin1'))
PRE=collections.defaultdict(list)
for sn in ('.rdata','.data'):
    w,base=words(sn)
    for k in range(len(w)-1):
        if w[k] in COLA and P.where(w[k+1])=='.text': PRE[w[k]].append(base+4*k)
starts=sorted(min(v)+4 for v in PRE.values() if len(v)==1)
S2C={min(v)+4:c for c,v in PRE.items() if len(v)==1}
VIEWS=[]
for i,st in enumerate(starts):
    end=starts[i+1] if i+1<len(starts) else P.B['.rdata']['hi_file']
    sl=[]; a=st
    while a<end and P.where(P.dw(a))=='.text':
        sl.append(P.dw(a)); a+=4
    md_,ptd,pchd,nm=COLA[S2C[st]]
    VIEWS.append(dict(col=S2C[st],base=st,slots=sl,mdisp=md_,nm=nm[1:] if nm.startswith('.') else nm))
MAIN=[v for v in VIEWS if v['mdisp']==0]
POS=collections.defaultdict(collections.Counter)
for v in VIEWS:
    for i,x in enumerate(v['slots']): POS[x][i]+=1

print('=== Q1 每个槽号的『目标只出现在本槽号』占比（口径反控） ===')
for idx in list(range(0,21))+[30,40,55]:
    vs=[v for v in VIEWS if len(v['slots'])>idx]
    tg=set(v['slots'][idx] for v in vs)
    only=sum(1 for T in tg if set(POS[T])=={idx})
    multi=len(tg)-only
    print('slot%2d views=%4d distinct=%4d only_here=%4d multi=%4d (%.1f%% only)'%(
        idx,len(vs),len(tg),only,multi,100.0*only/max(1,len(tg))))

print('=== Q2 共享同一 slot18 目标的类：视图前导公共槽串长度 ===')
md=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32); md.detail=True
raw=P.RAW
def dis(a,k=10):
    o=P.r2o(a)
    if o is None: return []
    return [(x.address,x.bytes.hex(),x.mnemonic,x.op_str) for x in md.disasm(raw[o:o+96],a,count=k)]
h18=[v for v in VIEWS if len(v['slots'])>18]
c18=collections.Counter(v['slots'][18] for v in h18)
def lcp(seqs):
    if not seqs: return 0
    n=0
    while True:
        vals=set(s[n] for s in seqs if len(s)>n)
        if len(vals)!=1 or any(len(s)<=n for s in seqs): return n
        n+=1
RES={}
for T,n in c18.most_common():
    grp=[v for v in h18 if v['slots'][18]==T]
    cls=sorted(set(v['nm'] for v in grp))
    # 主视图优先取
    gp=[v for v in grp if v['mdisp']==0]
    l=lcp([v['slots'] for v in (gp if gp else grp)])
    RES['0x%08x'%T]=dict(cnt=n,ncls=len(cls),lcp=l,cls=cls[:6])
    print('0x%08x cnt=%2d ncls=%2d LCP(前导公共槽)=%2d'%(T,n,len(cls),l))
print('=== Q3 单类目标（cnt=1）的类名与族 ===')
loco=[T for T,n in c18.items() if n==1 and 'Locomotion' in ''.join(sorted(set(v['nm'] for v in h18 if v['slots'][18]==T)))]
print('cnt=1 目标数=%d 其中 Locomotion 相关系族=%d'%(sum(1 for T,n in c18.items() if n==1),len(loco)))
# LocomotionClass 家族全部视图（找 slot18 是否全族覆盖）
lname=[v for v in VIEWS if 'Locomotion' in v['nm']]
fam=sorted(set(v['nm'] for v in lname))
print('Locomotion 相关类名 %d 个：%s'%(len(fam),';'.join(fam)))
cov=[]
for nm in fam:
    g=[v for v in lname if v['nm']==nm and v['mdisp']==0]
    if not g: cov.append((nm,'NO_MAIN',None)); continue
    v=g[0]
    cov.append((nm,'slot18' if len(v['slots'])>18 else 'short',
                hex(v['slots'][18]) if len(v['slots'])>18 else 'n=%d'%len(v['slots'])))
for c in cov: print('  ',c)
nL=sum(1 for c in cov if c[1]=='slot18')
print('Locomotion 族主视图数=%d 有 slot18 的=%d'%(len(cov),nL))
print('=== Q4 前 5 目标的前 10 条指令 ===')
for T,n in c18.most_common(5):
    print('--- 0x%08x cnt=%d'%(T,n))
    for x in dis(T,10): print('   %08x %-20s %s %s'%x)
json.dump({'pos_only':{},'res':RES,'loco':cov},open('/home/t628/projects/ra2-campaign-forge/_r215/m2.json','w'),indent=1,default=str)
