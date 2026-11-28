# -*- coding: utf-8 -*-
"""R216 m0：主会话前置探针（只读）。重建视图表，打印 AbstractClass 主视图 slot0..25 与 slot17/19/20/21 组结构。"""
import sys,struct,collections
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
print('views=%d slots=%d distinct=%d'%(len(VIEWS),sum(len(v['slots']) for v in VIEWS),
      len({x for v in VIEWS for x in v['slots']})))
g=[v for v in VIEWS if v['nm']=='?AVAbstractClass@@' and v['mdisp']==0]
m=g[0]
print('AbstractClass main 0x%x slots=%d'%(m['base'],len(m['slots'])))
for i,x in enumerate(m['slots'][:26]): print('  slot%-2d 0x%08x'%(i,x))
for k in (17,18,19,20,21):
    has=[v for v in VIEWS if len(v['slots'])>k]
    c=collections.Counter(v['slots'][k] for v in has)
    print('slot%-2d views=%d distinct=%d top6=%s'%(k,len(has),len(c),
      ' '.join('0x%08x:%d'%(a,b) for a,b in c.most_common(6))))
# slot>=3 区域里出现次数 top20 的目标及其槽号分布
POS=collections.defaultdict(collections.Counter)
for v in VIEWS:
    for i,x in enumerate(v['slots']): POS[x][i]+=1
cnt=[(x,sum(POS[x].values())) for x in POS]
cnt.sort(key=lambda t:-t[1])
print('top20 目标（次数/槽号分布前6）:')
for x,c in cnt[:20]:
    print('  0x%08x n=%d slots=%s'%(x,c,' '.join('%d:%d'%(a,b) for a,b in POS[x].most_common(6))))
