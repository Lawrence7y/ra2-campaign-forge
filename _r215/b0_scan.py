# -*- coding: utf-8 -*-
"""R215 B0：独立表重建（视图/槽）+ slot18 27 落点基础画像。只读，不写业务文件。"""
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
PREDADDR=collections.defaultdict(list)
for sn in ('.rdata','.data'):
    w,base=words(sn)
    for k in range(len(w)-1):
        if w[k] in COLA and P.where(w[k+1])=='.text': PREDADDR[w[k]].append(base+4*k)
starts=sorted(min(v)+4 for v in PREDADDR.values() if len(v)==1)
S2C={min(v)+4:c for c,v in PREDADDR.items() if len(v)==1}
VIEWS=[]
for i,st in enumerate(starts):
    end=starts[i+1] if i+1<len(starts) else P.B['.rdata']['hi_file']
    sl=[]; a=st
    while a<end and P.where(P.dw(a))=='.text':
        sl.append(P.dw(a)); a+=4
    md_,ptd,pchd,nm=COLA[S2C[st]]
    n=nm[1:] if nm.startswith('.') else nm
    VIEWS.append(dict(col=S2C[st],base=st,slots=sl,mdisp=md_,nm=n))
MAIN=[v for v in VIEWS if v['mdisp']==0]; SEC=[v for v in VIEWS if v['mdisp']!=0]
NM=collections.defaultdict(list)
for v in VIEWS: NM[v['nm']].append(v)
TGT=collections.Counter(x for v in VIEWS for x in v['slots'])
has18=[v for v in VIEWS if len(v['slots'])>18]
c18=collections.Counter(v['slots'][18] for v in has18)
print('VIEWS=%d MAIN=%d SEC=%d SLOTS=%d DISTINCT=%d has18=%d d18=%d'%(
    len(VIEWS),len(MAIN),len(SEC),sum(len(v['slots']) for v in VIEWS),len(TGT),len(has18),len(c18)))
# 27 落点画像
md_lite=None
import capstone
md=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32); md.detail=True
def first_bytes(a,n=48):
    o=P.r2o(a)
    if o is None: return b''
    return P.RAW[o:o+n]
def dis(a,n=8):
    out=[]
    for ins in md.disasm(first_bytes(a,64),a,count=n):
        out.append((ins.address,ins.bytes.hex(),ins.mnemonic,ins.op_str))
    return out
INFO={}
for t,n in sorted(c18.items(), key=lambda kv:-kv[1]):
    # 该目标在全体视图里出现的 (槽号) 分布 与 类名
    pos=collections.Counter(); cls=collections.defaultdict(list)
    for v in VIEWS:
        for i,x in enumerate(v['slots']):
            if x==t:
                pos[i]+=1; cls[v['nm']].append((i,v['mdisp']))
    INFO['0x%08x'%t]=dict(cnt=n, total=TGT[t], pos=dict(sorted(pos.items())),
        nclass=len(cls), classes={k:v for k,v in sorted(cls.items())} if len(cls)<=12 else {},
        ins=dis(t,8))
print(json.dumps({'views':len(VIEWS),'main':len(MAIN),'sec':len(SEC),
  'slots':sum(len(v['slots']) for v in VIEWS),'distinct':len(TGT),'d18':len(c18),
  'slot18':[('0x%08x'%k,v) for k,v in c18.most_common()],'info':INFO},ensure_ascii=False,indent=1))
