# -*- coding: utf-8 -*-
"""R212 c4：补证 —— 8/12 记录的 attr/nc/vdisp/pdisp；78 类名单与继承族；S2(8) 与 S3(21784) 同 pTD 的 attr 差异。"""
import sys,struct,collections,json
sys.path.insert(0,'/home/t628/projects/ra2-campaign-forge/_r185')
import pe185 as P
def s32(v): return struct.unpack('<i',struct.pack('<I',v))[0]
COL={}
for sn in ('.rdata','.data'):
    s=P.B[sn]; n=s['rawsize']//4; base=s['lo']
    w=struct.unpack_from('<%dI'%n,P.RAW,s['rawptr'])
    for i in range(n-4):
        if w[i] not in (0,1,2) or w[i+2]!=0: continue
        if P.where(w[i+3])!='.data' or P.where(w[i+4])!='.rdata': continue
        nm=P.cstr(w[i+3]+8,400)
        if not (nm and nm.startswith(b'.?A') and nm.endswith(b'@@')): continue
        COL[base+4*i]=dict(mdisp=s32(w[i+1]),pTD=w[i+3],pCHD=w[i+4],name=nm.decode('latin1'))
G=collections.defaultdict(list)
for c,v in COL.items(): G[v['pCHD']].append(c)
CHD=sorted(G); NB={a:P.dw(a+8) for a in CHD}; pBCA={a:P.dw(a+12) for a in CHD}
BCA={a:[P.dw(pBCA[a]+4*j) for j in range(NB[a])] for a in CHD}
def tdnm(p):
    c=P.cstr(p+8,400) if p else None
    return c.decode('latin1') if c else None
recs=[]
for a in CHD:
    nm=tdnm(P.dw(BCA[a][0])) if BCA[a] else '?'
    for j,e in enumerate(BCA[a]):
        recs.append(dict(chd=a,idx=j,pTD=P.dw(e),nc=P.dw(e+4),mdisp=s32(P.dw(e+8)),
                         pdisp=s32(P.dw(e+12)),vdisp=P.dw(e+16),attr=P.dw(e+20),addr=e,cls=nm))
print('全部 BCA 记录 %d 条'%len(recs))
for m in (8,12,21784,24,172,176,240,248,36,40,44,1728):
    sub=[r for r in recs if r['mdisp']==m]
    if not sub: continue
    nc=collections.Counter((r['nc'],r['pdisp'],r['vdisp'],r['attr']) for r in sub)
    print('\nmdisp=%-6d 记录 %-3d 条  pTD=%s'%(m,len(sub),
        sorted({tdnm(r['pTD']) for r in sub})))
    print('   (nc,pdisp,vdisp,attr) 分布：%s'%dict(nc))
sub8=[r for r in recs if r['mdisp']==8]
sub12=[r for r in recs if r['mdisp']==12]
print('\n8 的 78 类名单：')
names8=sorted(r['cls'] for r in sub8)
for i in range(0,len(names8),3):
    print('   '+'  '.join('%-32s'%x for x in names8[i:i+3]))
print('\n12 的类集合 == 8 的类集合：%s'%(sorted(r['cls'] for r in sub12)==names8))
# S3 三类
s3=[r for r in recs if r['mdisp']==21784]
print('\nS3(21784) 三类：%s'%[(r['cls'],hex(r['chd']),r['idx'],r['nc'],r['pdisp'],r['vdisp'],r['attr']) for r in s3])
print('S3 的 pTD == S2 的 pTD：%s（%s）'%(s3[0]['pTD']==sub8[0]['pTD'],[tdnm(r['pTD']) for r in s3]))
print('S3 attr=%s vs S2 attr=%s'%({r['attr'] for r in s3},{r['attr'] for r in sub8}))
# S3 三类是否也含 8/12
for r in s3:
    cls=[x for x in recs if x['chd']==r['chd']]
    print('  %s 的 mdisp 序列 %s'%(r['cls'],[x['mdisp'] for x in cls]))
json.dump(dict(n=len(recs),names8=names8,
  s3=[{k:(hex(v) if k in ('chd','addr','pTD') else v) for k,v in r.items()} for r in s3]),
  open('/home/t628/projects/ra2-campaign-forge/_r212/c4.json','w'),indent=1)
print('\nWROTE c4.json')
