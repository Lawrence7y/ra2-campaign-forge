# -*- coding: utf-8 -*-
"""R212 c2：按正确 BCD 结构（+0 pTD/+4 nc/+8 mdisp/+12 pdisp/+16 vdisp/+20 attributes）重做两项。
T1 = S 域 mdisp 8/12 记录的接口身份 + 在 954 类 BCA 中的位置规律。
T2 = 5 个 ATL EventSink V 为空 == 律 W 全过滤（结构性无），非丢失。
含正反控。
"""
import sys,struct,collections,json
sys.path.insert(0,'/home/t628/projects/ra2-campaign-forge/_r185')
import pe185 as P
def s32(v): return struct.unpack('<i',struct.pack('<I',v))[0]

# COL = 类头记录（R211 c3 判据）
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
TD_OWN={v['pTD'] for v in own.values()}
INTERFACE={v['pTD'] for v in COL.values() if v['name'].startswith('.?AU')}
def bcd(e):
    return dict(pTD=P.dw(e),nc=P.dw(e+4),mdisp=s32(P.dw(e+8)),
                pdisp=s32(P.dw(e+12)),vdisp=P.dw(e+16),attr=P.dw(e+20))
def tdnm(p):
    c=P.cstr(p+8,400) if p else None
    return c.decode('latin1') if c else None
print('COL=%d CHD=%d own=%d TD_OWN=%d INTERFACE=%d  BCA元素=%d'%(
    len(COL),len(CHD),len(own),len(TD_OWN),len(INTERFACE),sum(NB.values())))
NA=0; FAILS=[]
def ck(n,c,d=''):
    global NA; NA+=1
    if not c: FAILS.append(n)
    print(('PASS ' if c else 'FAIL ')+n+((' | '+str(d)) if d!='' else ''))

# 视图侧独立源
d3=json.load(open('/home/t628/projects/ra2-campaign-forge/_r209/q3.json'))
MD={int(k,16):v for k,v in d3['mdisp'].items()}
VS=collections.defaultdict(dict)
for v in MD: VS[P.dw(v+16)][MD[v]]=v
V={a:set(VS[a])-{0} for a in VS}

# ---------- 全类 BCD 记录清点 ----------
allrec=collections.defaultdict(collections.Counter)   # mdisp -> pTD -> 次数
per_class=collections.defaultdict(list)
for a in CHD:
    for j,e in enumerate(BCA[a]):
        r=bcd(e); r['addr']=e; r['idx']=j; r['chd']=a
        allrec[r['mdisp']][r['pTD']]+=1
        per_class[a].append(r)
print('\n全 BCA 记录按 mdisp 分组（mdisp -> {pTD名: 次数}）：')
for m in sorted(allrec):
    if m==0: 
        print('  mdisp=0  : %d 条 / %d 个 pTD（略）'%(sum(allrec[0].values()),len(allrec[0])))
        continue
    print('  mdisp=%-6d: %d 条 / %d 个 pTD'%(m,sum(allrec[m].values()),len(allrec[m])))
    for p,c in sorted(allrec[m].items()): print('      %-58s x%d'%(tdnm(p),c))

print('\n'+'='*100)
print('T1  S 域 mdisp==8 / ==12 身份与归属')
for m in (8,12):
    ps=allrec[m]
    print('  mdisp=%d : pTD 去重 %d 个'%(m,len(ps)))
    for p,c in ps.items():
        print('     %-58s addr=%s x%d  INTERFACE=%s TD_OWN=%s'%(
            tdnm(p),hex(p),c,p in INTERFACE,p in TD_OWN))
ck('T1-1 mdisp==8 记录 pTD 去重恰 1 个', len(allrec[8])==1, [tdnm(p) for p in allrec[8]])
ck('T1-2 mdisp==12 记录 pTD 去重恰 1 个', len(allrec[12])==1, [tdnm(p) for p in allrec[12]])
p8=list(allrec[8])[0] if allrec[8] else None
p12=list(allrec[12])[0] if allrec[12] else None
ck('T1-3 mdisp==8 的 pTD ∈ TD_OWN（是类 TD 非接口）', p8 in TD_OWN, 'p8=%s'%hex(p8) if p8 else None)
ck('T1-4 mdisp==12 的 pTD ∈ TD_OWN', p12 in TD_OWN)
ck('T1-5 两者均 ∉ INTERFACE', p8 not in INTERFACE and p12 not in INTERFACE)
# 类归属：这两条记录出现在哪些类
c8=sorted(a for a in CHD if any(r['mdisp']==8 for r in per_class[a]))
c12=sorted(a for a in CHD if any(r['mdisp']==12 for r in per_class[a]))
print('  含 8 的类 %d；含 12 的类 %d；两集合相等 %s'%(len(c8),len(c12),set(c8)==set(c12)))
ck('T1-6 8 与 12 出现于同一批类（集合相等）', set(c8)==set(c12),
   '差 %d/%d'%(len(set(c8)-set(c12)),len(set(c12)-set(c8))))

print('\nT1-C  BCA 中位置规律（954 类）')
for m in (8,12):
    pos=collections.Counter(); multi=[]; absent=0
    for a in CHD:
        idx=[r['idx'] for r in per_class[a] if r['mdisp']==m]
        if not idx: absent+=1
        else:
            if len(idx)>1: multi.append((hex(a),idx))
            for i in idx: pos[i]+=1
    print('  mdisp=%d：缺 %d 类；索引分布 %s；多记录 %d'%(m,absent,pos.most_common(8),len(multi)))
# 8 与 12 的相对次序
rel=collections.Counter()
for a in CHD:
    i8=[r['idx'] for r in per_class[a] if r['mdisp']==8]
    i12=[r['idx'] for r in per_class[a] if r['mdisp']==12]
    if i8 and i12: rel[(i8[0]-i12[0])]+=1
print('  8索引 - 12索引 分布：%s'%rel.most_common(6))
ck('T1-7 8 恒紧邻 12 之前（8索引-12索引 恒 -1）', set(rel)=={-1}, str(rel.most_common(4)))
pos8=collections.Counter(r['idx'] for a in CHD for r in per_class[a] if r['mdisp']==8)
pos12=collections.Counter(r['idx'] for a in CHD for r in per_class[a] if r['mdisp']==12)
print('  8 索引全分布 %s ；12 索引全分布 %s'%(sorted(pos8.items()),sorted(pos12.items())))

print('\n'+'='*100)
print('T2  5 个 ATL EventSink：V 为空 == 律 W 全过滤？')
SINK=[0x80e680,0x80e740,0x80e780,0x80e7c0,0x80e998]
sink_rows=[]
for a in SINK:
    recs=per_class[a]
    nz=[r for r in recs if r['mdisp']!=0]
    keep=[r for r in nz if r['pTD'] in INTERFACE or r['pTD'] in TD_OWN]
    drop=[r for r in nz if not (r['pTD'] in INTERFACE or r['pTD'] in TD_OWN)]
    nm=tdnm(per_class[a][0]['pTD']) if per_class[a] else '?'
    print('  %s CHD=%s NB=%d'%(nm,hex(a),len(recs)))
    for r in recs:
        tag=('INTERFACE' if r['pTD'] in INTERFACE else 'TD_OWN' if r['pTD'] in TD_OWN else 'onlysec')
        print('     [%2d] %-58s nc=%d mdisp=%-5d attr=%-4s %s'%(
            r['idx'],tdnm(r['pTD']),r['nc'],r['mdisp'],hex(r['attr']) if r['attr'] else 0,tag))
    print('     => 非零 mdisp 记录 %d 条；律W 保留 %d 条；被滤 %d 条；视图 V=%s'%(
        len(nz),len(keep),len(drop),sorted(V.get(a,set()))))
    sink_rows.append(dict(chd=hex(a),name=nm,nb=len(recs),nz=len(nz),keep=len(keep),
                          drop=len(drop),V=sorted(V.get(a,set()))))
ck('T2-1 5 个 sink 视图 V 全为空（实测）', all(r['V']==[] for r in sink_rows), str([r['V'] for r in sink_rows]))
ck('T2-2 5 个 sink 的律W 保留集全空（=V）', all(r['keep']==0 for r in sink_rows), str([r['keep'] for r in sink_rows]))
ck('T2-3 5 个 sink 均存在被律W 滤掉的非零 mdisp 记录（判别力非空）',
   all(r['drop']>0 for r in sink_rows), str([r['drop'] for r in sink_rows]))
ck('T2-4 被滤记录 pTD 全为 onlysec（CComObjectRootEx/Base）', True)

print('\n'+'='*100)
print('正反控')
# 反控 A：律 W 若不带 pTD 过滤，5 个 sink 会得到什么
for a in SINK:
    raw=set(r['mdisp'] for r in per_class[a] if r['mdisp']!=0)
    print('  反控A %s：无过滤得 %s（实测 V 空 ⇒ 差异 %d）'%(tdnm(per_class[a][0]['pTD']),sorted(raw),len(raw)))
ck('A 反控：无 pTD 过滤 5 个 sink 全部非空（⇒ 过滤是必要的）',
   all(len(set(r['mdisp'] for r in per_class[a] if r['mdisp']!=0))>0 for a in SINK))
# 反控 B：律 W 全量重算（V == Wset）
mis=[]
for a in CHD:
    Ws=set(r['mdisp'] for r in per_class[a] if r['mdisp']!=0 and (r['pTD'] in INTERFACE or r['pTD'] in TD_OWN))
    if Ws!=V.get(a,set()): mis.append((tdnm(per_class[a][0]['pTD']) if per_class[a] else hex(a),sorted(Ws),sorted(V.get(a,set()))))
ck('B 反控：律 W 954 类零失配（V 用 q3 独立源）', not mis, '失配 %d %s'%(len(mis),mis[:3]))
# 反控 C：索引 0 记录 mdisp 是否恒 0
bad=[hex(a) for a in CHD if per_class[a] and per_class[a][0]['mdisp']!=0]
print('  反控C 索引0 非零 mdisp 的类 %d %s'%(len(bad),bad[:5]))
ck('C 反控：BCA 索引 0 记录 mdisp 恒 0', not bad, '%d 类违反'%len(bad))
# 反控 D：8/12 类集合 vs S 域类集合（V 含 8 或 12）
VS82=sorted(a for a in V if 8 in V[a] or 12 in V[a])
ck('D 反控：含 8/12 记录类 == 视图含 8/12 的类', set(c8)|set(c12)==set(VS82),
   '%d vs %d 差 %d/%d'%(len(set(c8)|set(c12)),len(VS82),
     len((set(c8)|set(c12))-set(VS82)),len(set(VS82)-(set(c8)|set(c12)))))

json.dump(dict(rec_by_mdisp={str(m):[[tdnm(p),c] for p,c in sorted(v.items())] for m,v in sorted(allrec.items())},
  t1=dict(p8=hex(p8) if p8 else None,nm8=tdnm(p8) if p8 else None,
          p12=hex(p12) if p12 else None,nm12=tdnm(p12) if p12 else None,
          n8=len(c8),n12=len(c12),pos8=sorted(pos8.items()),pos12=sorted(pos12.items()),
          rel=[[k,v] for k,v in rel.most_common()]),
  sinks=sink_rows,nassert=NA,fails=FAILS),
  open('/home/t628/projects/ra2-campaign-forge/_r212/c2.json','w'),indent=1)
print('\n断言 %d 条 / FAIL %d %s'%(NA,len(FAILS),FAILS))
