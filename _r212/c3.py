# -*- coding: utf-8 -*-
"""R212 c3：修正 INTERFACE 判据（pTD 指向的 TD 名以 .?AU 开头，全域 26 个），
重做律 W 零失配复验 + T1 位置规律 + S 域 8/12 身份 + 21784 与 INoticeSink 重名交叉。
一次输出全部证据与正反控。
"""
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
CHD=sorted(G)
NB={a:P.dw(a+8) for a in CHD}; pBCA={a:P.dw(a+12) for a in CHD}
BCA={a:[P.dw(pBCA[a]+4*j) for j in range(NB[a])] for a in CHD}
own={a+16:COL[a+16] for a in CHD if a+16 in COL}
def tdnm(p):
    if not p: return None
    c=P.cstr(p+8,400)
    return c.decode('latin1') if c else None
def bcd(e):
    return dict(pTD=P.dw(e),nc=P.dw(e+4),mdisp=s32(P.dw(e+8)),
                pdisp=s32(P.dw(e+12)),vdisp=P.dw(e+16),attr=P.dw(e+20),addr=e)
per_class=collections.defaultdict(list)
for a in CHD:
    for j,e in enumerate(BCA[a]):
        r=bcd(e); r['idx']=j; per_class[a].append(r)
# 全域 pTD 池（COL 的 + 所有 BCA 记录的）
ALLPTD=set(v['pTD'] for v in COL.values()) | set(r['pTD'] for a in CHD for r in per_class[a])
INTERFACE={p for p in ALLPTD if (tdnm(p) or '').startswith('.?AU')}
TD_OWN={v['pTD'] for v in own.values()}
print('COL=%d CHD=%d own=%d 全域pTD=%d INTERFACE=%d TD_OWN=%d'%(
  len(COL),len(CHD),len(own),len(ALLPTD),len(INTERFACE),len(TD_OWN)))
print('INTERFACE 清单：')
for p in sorted(INTERFACE,key=lambda x:tdnm(x) or ''): print('   %s %s'%(hex(p),tdnm(p)))
NA=0;FAILS=[]
def ck(n,c,d=''):
    global NA;NA+=1
    if not c: FAILS.append(n)
    print(('PASS ' if c else 'FAIL ')+n+((' | '+str(d)) if d!='' else ''))
d3=json.load(open('/home/t628/projects/ra2-campaign-forge/_r209/q3.json'))
MD={int(k,16):v for k,v in d3['mdisp'].items()}
VS=collections.defaultdict(dict)
for v in MD: VS[P.dw(v+16)][MD[v]]=v
V={a:set(VS[a])-{0} for a in VS}
def Wset(a):
    return set(r['mdisp'] for r in per_class[a] if r['mdisp']!=0 and (r['pTD'] in INTERFACE or r['pTD'] in TD_OWN))
print('\n'+'='*100); print('律 W 复验（954 类，V 用 q3 独立源）')
mis=[]
for a in CHD:
    if Wset(a)!=V.get(a,set()): mis.append((tdnm(per_class[a][0]['pTD']),sorted(Wset(a)),sorted(V.get(a,set()))))
ck('W1 律 W 954 类零失配', not mis, '失配 %d %s'%(len(mis),mis[:3]))
ck('W2 INTERFACE 规模 26（R211 口径）', len(INTERFACE)==26, len(INTERFACE))

print('\n'+'='*100); print('T1  S 域 mdisp 8/12')
for m in (8,12):
    ps=collections.Counter(r['pTD'] for a in CHD for r in per_class[a] if r['mdisp']==m)
    print('  mdisp=%d: %d 条, pTD %s'%(m,sum(ps.values()),[(tdnm(p),c) for p,c in ps.items()]))
p8=list({r['pTD'] for a in CHD for r in per_class[a] if r['mdisp']==8})[0]
p12=list({r['pTD'] for a in CHD for r in per_class[a] if r['mdisp']==12})[0]
ck('T1-1 mdisp8 pTD == .?AVINoticeSink@@', tdnm(p8)=='.?AVINoticeSink@@', tdnm(p8))
ck('T1-2 mdisp12 pTD == .?AVINoticeSource@@', tdnm(p12)=='.?AVINoticeSource@@', tdnm(p12))
ck('T1-3 两者 ∈ TD_OWN 且 ∉ INTERFACE', p8 in TD_OWN and p12 in TD_OWN and p8 not in INTERFACE and p12 not in INTERFACE)
c8=set(a for a in CHD if any(r['mdisp']==8 for r in per_class[a]))
c12=set(a for a in CHD if any(r['mdisp']==12 for r in per_class[a]))
ck('T1-4 8/12 出现于同一批 78 类', c8==c12 and len(c8)==78, '%d vs %d'%(len(c8),len(c12)))
rel=collections.Counter()
for a in CHD:
    i8=[r['idx'] for r in per_class[a] if r['mdisp']==8]
    i12=[r['idx'] for r in per_class[a] if r['mdisp']==12]
    if i8 and i12: rel[i8[0]-i12[0]]+=1
ck('T1-5 8 恒紧邻 12 之前（差恒 -1，78/78）', rel=={-1:78}, str(dict(rel)))
pos8=collections.Counter(r['idx'] for a in CHD for r in per_class[a] if r['mdisp']==8)
pos12=collections.Counter(r['idx'] for a in CHD for r in per_class[a] if r['mdisp']==12)
print('  8 索引分布 %s'%sorted(pos8.items()))
print('  12 索引分布 %s'%sorted(pos12.items()))
print('  索引跨度：8 在 %d..%d，12 在 %d..%d'%(min(pos8),max(pos8),min(pos12),max(pos12)))
ck('T1-6 绝对索引不固定（跨度 > 1，随继承深度变化）', max(pos8)-min(pos8)>1 and max(pos12)-min(pos12)>1)
# 相对位置 vs BCA 长度
tail=collections.Counter()
for a in CHD:
    i8=[r['idx'] for r in per_class[a] if r['mdisp']==8]
    if i8: tail[len(per_class[a])-1-i8[0]]+=1
print('  8 距 BCA 末尾的记录数分布 %s'%sorted(tail.items()))
ck('T1-7 8/12 不是固定位于尾部（分布分散）', len(tail)>1, sorted(tail.items()))
# 反控：8/12 记录是否总在 own 记录之后（idx>0）
ck('T1-8 8/12 记录恒不在索引 0（恒在 own 之后）', all(
   all(r['idx']>0 for r in per_class[a] if r['mdisp'] in (8,12)) for a in CHD))

print('\n'+'='*100); print('T1-D  INoticeSink 在 21784 的重名交叉')
r217=[(hex(a),r['idx'],tdnm(r['pTD']),r['mdisp'],r['attr'])
      for a in CHD for r in per_class[a] if r['mdisp']==21784]
print('  mdisp=21784 记录 %d 条：'%len(r217))
for t in r217:
    print('    CHD=%s idx=%d pTD=%s mdisp=%d attr=%s'%t)
ck('T1-9 mdisp=21784 记录的 pTD 也是 .?AVINoticeSink@@', all(t[2]=='.?AVINoticeSink@@' for t in r217))
ck('T1-10 21784 记录共 3 条对应 3 类', len(r217)==3, len(r217))
# 这 3 类是谁
for a,_,_,_,_ in [(a,r['idx'],0,0,0) for a in CHD for r in per_class[a] if r['mdisp']==21784]:
    print('    类名(own) = %s'%tdnm(per_class[a][0]['pTD']))

print('\n'+'='*100); print('反控')
# 反控 A：无过滤
bad=0
for a in CHD:
    raw=set(r['mdisp'] for r in per_class[a] if r['mdisp']!=0)
    if raw!=V.get(a,set()): bad+=1
ck('A 无 pTD 过滤 ⇒ 失配类数（应 >0，证明过滤必要）', bad>0, bad)
# 反控 B：仅 TD_OWN
bad2=sum(1 for a in CHD if set(r['mdisp'] for r in per_class[a] if r['mdisp']!=0 and r['pTD'] in TD_OWN)!=V.get(a,set()))
ck('B 仅 TD_OWN ⇒ 失配类数（应 >0）', bad2>0, bad2)
# 反控 C：仅 INTERFACE
bad3=sum(1 for a in CHD if set(r['mdisp'] for r in per_class[a] if r['mdisp']!=0 and r['pTD'] in INTERFACE)!=V.get(a,set()))
ck('C 仅 INTERFACE ⇒ 失配类数（应 >0）', bad3>0, bad3)
# 反控 D：INTERFACE 用 COL 记录名判（错误判据）⇒ 应失配
I2={v['pTD'] for v in COL.values() if v['name'].startswith('.?AU')}
bad4=sum(1 for a in CHD if set(r['mdisp'] for r in per_class[a] if r['mdisp']!=0 and (r['pTD'] in I2 or r['pTD'] in TD_OWN))!=V.get(a,set()))
ck('D 用 COL 记录名判 INTERFACE（错判据）⇒ 失配 91（如实证）', bad4==91, bad4)
json.dump(dict(interface=sorted([[hex(p),tdnm(p)] for p in INTERFACE]),
  w_mis=mis, badA=bad,badB=bad2,badC=bad3,badD=bad4,
  p8=hex(p8),nm8=tdnm(p8),p12=hex(p12),nm12=tdnm(p12),
  c8=len(c8),pos8=sorted(pos8.items()),pos12=sorted(pos12.items()),
  rel=dict(rel),tail=sorted(tail.items()),r217=r217,nassert=NA,fails=FAILS),
  open('/home/t628/projects/ra2-campaign-forge/_r212/c3.json','w'),indent=1)
print('\n断言 %d 条 / FAIL %d %s'%(NA,len(FAILS),FAILS))
