# -*- coding: utf-8 -*-
"""R215 m11：检验『0x4104xx 家族 = 某基类 vtable 的通用桩，按槽号被大量派生类继承』。
输出 AbstractClass / AbstractTypeClass 主视图逐槽，以及每个槽值在全表的 (槽号) 绑定是否唯一。
"""
import sys,struct,json,collections
sys.path.insert(0,'/home/t628/projects/ra2-campaign-forge/_r185')
import pe185 as P
def s32(v): return struct.unpack('<i',struct.pack('<I',v&0xffffffff))[0]
def words(sn):
    s=P.B[sn];n=s['rawsize']//4
    return struct.unpack_from('<%dI'%n,P.RAW,s['rawptr']),s['lo']
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
    sl=[];a=st
    while a<end and P.where(P.dw(a))=='.text':
        sl.append(P.dw(a));a+=4
    md_,ptd,pchd,nm=COLA[S2C[st]]
    VIEWS.append(dict(base=st,slots=sl,mdisp=md_,nm=nm[1:] if nm.startswith('.') else nm))
POS=collections.defaultdict(collections.Counter)
for v in VIEWS:
    for i,x in enumerate(v['slots']): POS[x][i]+=1
for nm in ('?AVAbstractClass@@','?AVAbstractTypeClass@@','?AVObjectClass@@','?AVTechnoClass@@'):
    g=[v for v in VIEWS if v['nm']==nm and v['mdisp']==0]
    if not g: print(nm,'NO MAIN'); continue
    v=g[0]
    print('=== %s 主视图 0x%x 槽数=%d ==='%(nm,v['base'],len(v['slots'])))
    for i,x in enumerate(v['slots'][:30]):
        pos=dict(sorted(POS[x].items()))
        print('  slot%-2d 0x%08x  该目标出现的槽号=%s'%(i,x,pos))
# 单一槽号绑定的桩家族规模：统计"只在一个槽号出现 且 出现次数≥2"的目标
solo=[(T,c,next(iter(POS[T]))) for T,c in ((x,sum(POS[x].values())) for x in POS) if len(POS[T])==1 and c>=2]
solo.sort(key=lambda t:-t[1])
print('=== 单槽号绑定且出现≥2 次的目标数=%d ; top20 ==='%len(solo))
for T,c,i in solo[:20]: print('  0x%08x 次数=%d 槽号=%d'%(T,c,i))
json.dump({'solo_n':len(solo),'solo_top':[['0x%08x'%T,c,i] for T,c,i in solo[:40]]},
 open('/home/t628/projects/ra2-campaign-forge/_r215/m11.json','w'),indent=1)
