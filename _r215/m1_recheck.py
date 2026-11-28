# -*- coding: utf-8 -*-
"""R215 主会话独立复算（不复用子代理代码）：slot18 27 落点的准入性/类归因/复用独立性。
防 OOM：全段只做逐字节 e8 扫描，capstone 仅对命中地址 count<=12。
"""
import sys,struct,json,collections
sys.path.insert(0,'/home/t628/projects/ra2-campaign-forge/_r185')
import pe185 as P, capstone
NA=0; F=[]
def ck(n,c,d=''):
    global NA; NA+=1
    if not c: F.append(n)
    print(('PASS ' if c else 'FAIL ')+n+((' | '+str(d)) if d!='' else ''))
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
    n=nm[1:] if nm.startswith('.') else nm
    VIEWS.append(dict(col=S2C[st],base=st,slots=sl,mdisp=md_,nm=n))
ck('A1 视图/主/次/槽/distinct = 1214/954/260/14044/6692',
   (len(VIEWS),sum(1 for v in VIEWS if v['mdisp']==0),sum(1 for v in VIEWS if v['mdisp']!=0),
    sum(len(v['slots']) for v in VIEWS),len(set(x for v in VIEWS for x in v['slots'])))==(1214,954,260,14044,6692))
h18=[v for v in VIEWS if len(v['slots'])>18]
T18=[v['slots'][18] for v in h18]
c18=collections.Counter(T18)
ck('A2 has18=137 d18=27', len(h18)==137 and len(c18)==27,'%d/%d'%(len(h18),len(c18)))
POS=collections.defaultdict(collections.Counter)   # target -> slot idx -> count
CLS=collections.defaultdict(set)                   # target -> set of class names (all views)
for v in VIEWS:
    for i,x in enumerate(v['slots']):
        POS[x][i]+=1; CLS[x].add(v['nm'])

# --- e8 callers scan (whole .text, byte-wise) ---
t=P.B['.text']; tb=t['lo']; n=t['rawsize']; o0=t['rawptr']; raw=P.RAW
CALL=collections.Counter()
i=o0
end=o0+n-4
while i<end:
    if raw[i]==0xe8:
        rel=struct.unpack_from('<i',raw,i+1)[0]
        CALL[tb+(i-o0)+5+rel]+=1
    i+=1
# reverse: who calls what — we need callers of each of 27 targets
T27=[a for a,_ in c18.most_common()]
print('--- 27 targets: count / totalOcc / nclass@anyPos / callers / entry-evidence ---')
md=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32); md.detail=True
def dis(a,k=6):
    o=P.r2o(a)
    if o is None: return []
    return [(x.address,x.bytes.hex(),x.mnemonic,x.op_str) for x in md.disasm(raw[o:o+64],a,count=k)]
ENT={}
for T in T27:
    pv=raw[P.r2o(T)-1] if P.r2o(T) else None
    # pad check: walk back while 0x90/0xcc
    j=P.r2o(T)-1; pad=0
    while j>=0 and raw[j] in (0x90,0xcc): pad+=1; j-=1
    ev='prev_ret' if pv in (0xc3,0xc2) else ('prev_pad' if pad>0 else 'none')
    ENT[T]=dict(ev=ev,pad=pad,prev=('%02x'%pv) if pv is not None else None)
    print('0x%08x n=%2d occ=%3d ncls=%3d callers=%3d entry=%s(pad=%d)'%(
        T,c18[T],sum(POS[T].values()),len(CLS[T]),CALL.get(T,0),ev,pad))
# --- G3: prefix-cluster independence ---
def cluster(keyfn,idx=18):
    g=collections.defaultdict(list)
    for v in h18: g[keyfn(v)].append(v['slots'][idx])
    same=sum(1 for k,vals in g.items() if len(set(vals))==1)
    return len(g),max(len(v) for v in g.values()),same,len(g)-same
k3=cluster(lambda v:tuple(v['slots'][:3]))
k2=cluster(lambda v:tuple(v['slots'][:2]))
k1=cluster(lambda v:(v['slots'][0],))
print('G3 3-tuple clusters=%d max=%d same=%d diff=%d'%k3)
print('G3 2-tuple clusters=%d max=%d same=%d diff=%d'%k2)
print('G3 1-tuple clusters=%d max=%d same=%d diff=%d'%k1)
# 反控：不同 slot 用同法（slot17 / slot19）
c17=collections.Counter(v['slots'][17] for v in VIEWS if len(v['slots'])>17)
c19=collections.Counter(v['slots'][19] for v in VIEWS if len(v['slots'])>19)
print('ctrl slot17 views=%d d=%d ; slot19 views=%d d=%d'%(
    sum(1 for v in VIEWS if len(v['slots'])>17),len(c17),
    sum(1 for v in VIEWS if len(v['slots'])>19),len(c19)))
ck('A3 slot18 交集 slot19 = 1', len(set(c18)&set(c19))==1, len(set(c18)&set(c19)))
# 27 目标是否也在别的槽号出现
also=[(T,c18[T],dict(sorted(POS[T].items()))) for T in T27]
print('--- 27 目标的全槽号分布 ---')
for T,n,pos in also:
    print('0x%08x slot18x%-3d also=%s'%(T,n,{k:v for k,v in pos.items() if k!=18}))
# 每目标的类名（完整）
print('--- 类名归因 ---')
for T in T27:
    cl=sorted(CLS[T])
    print('0x%08x nclass=%d :: %s'%(T,len(cl),';'.join(cl[:8])+('...' if len(cl)>8 else '')))
json.dump({'fail':F,'nassert':NA,'ent':{('0x%08x'%k):v for k,v in ENT.items()},
           'c18':{('0x%08x'%k):v for k,v in c18.most_common()},
           'callers':{('0x%08x'%k):CALL.get(k,0) for k in T27},
           'k3':k3,'k2':k2,'k1':k1},open('/home/t628/projects/ra2-campaign-forge/_r215/m1.json','w'),indent=1)
print('ASSERT=%d FAIL=%d %s'%(NA,len(F),F))
