# -*- coding: utf-8 -*-
"""R215 m7：slot18 落点的『基类继承』检验。
假设 H：共享同一 slot18 目标的那些类，其主视图(vftable)的前 18 槽与某个基类主视图逐槽相同，
        即 slot18 是该基类 vtable 里的槽，被派生类整段继承。
检验：对每个落点 T 的类集合，取其中最"短前缀共享"者做基类候选，逐槽比对。
另：对 Locomotion mdisp=4 的 50 槽次视图做逐槽 diff（找哪些槽是 per-class override）。
"""
import sys,struct,json,collections
sys.path.insert(0,'/home/t628/projects/ra2-campaign-forge/_r185')
import pe185 as P
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
BYNM=collections.defaultdict(list)
for v in VIEWS: BYNM[v['nm']].append(v)
def main(nm):
    g=[v for v in BYNM[nm] if v['mdisp']==0]
    return g[0] if len(g)==1 else None
h18=[v for v in VIEWS if len(v['slots'])>18]
c18=collections.Counter(v['slots'][18] for v in h18)
print('=== A. 每个落点：类集合内『前 18 槽完全一致』的规模 ===')
OUT={}
for T,n in c18.most_common():
    grp=[v for v in h18 if v['slots'][18]==T]
    mainv=[v for v in grp if v['mdisp']==0]
    # 按前18槽签名分组
    sig=collections.Counter(tuple(v['slots'][:18]) for v in mainv)
    top=sig.most_common(1)[0] if sig else ((),0)
    # 主导签名对应的类名（取最短者作基类候选）
    domcls=sorted(v['nm'] for v in mainv if tuple(v['slots'][:18])==top[0])
    base=min(domcls,key=len) if domcls else None
    # 逐槽与基类比对（前 18 槽）
    mb=main(base) if base else None
    eqv=sum(1 for i in range(18) if mb and i<len(mb['slots']) and mb['slots'][i]==top[0][i])
    OUT['0x%08x'%T]=dict(n=n,nmain=len(mainv),nsec=len(grp)-len(mainv),
        nsig=len(sig),dom=top[1],base=base,base_slots_len=len(mb['slots']) if mb else 0,
        eq18=eqv,domcls=domcls[:6])
    print('0x%08x 视图%2d(主%2d/次%2d) 前18槽签名种数=%d 主导签名类数=%2d 基类候选=%s(槽%d) 与主导签名逐槽等=%d/18'%(
        T,n,len(mainv),len(grp)-len(mainv),len(sig),top[1],base,len(mb['slots']) if mb else 0,eqv))
print()
print('=== B. Locomotion mdisp=4 的 50 槽次视图逐槽 diff（12 个派生类） ===')
loco=sorted([v for v in VIEWS if v['nm'].endswith('LocomotionClass@@') and not v['nm'].startswith('?AV?$') and v['mdisp']==4],
            key=lambda v:v['nm'])
print('参与比对的视图数=%d'%len(loco))
for v in loco: print('  %-32s 0x%x n=%d'%(v['nm'],v['base'],len(v['slots'])))
n=min(len(v['slots']) for v in loco)
diff=[]; same=[]
for i in range(n):
    vals=set(v['slots'][i] for v in loco)
    (same if len(vals)==1 else diff).append(i)
print('共同槽数=%d 全同槽=%d 有差异槽=%d'%(n,len(same),len(diff)))
print('有差异槽号:',diff)
print('全同槽号前 25:',same[:25])
print('slot18 在有差异槽中?',18 in diff)
for i in diff[:8]:
    print('  slot%2d:'%i, [(v['nm'].replace('LocomotionClass@@',''),hex(v['slots'][i])) for v in loco])
D={'A':OUT,'B':{'nviews':len(loco),'n':n,'same':same,'diff':diff,'slot18_diff':18 in diff,
  'per_slot':{str(i):[(v['nm'],hex(v['slots'][i])) for v in loco] for i in diff}}}
json.dump(D,open('/home/t628/projects/ra2-campaign-forge/_r215/m7.json','w'),indent=1)
