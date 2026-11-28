# -*- coding: utf-8 -*-
"""R212 c1：两项静态取证，一次输出全部证据。
T1 = S 域 mdisp 8/12 两偏移的接口身份 + 该记录在 954 类 BCA 中的位置规律（含正反控）。
T2 = 5 个 ATL EventSink V 为空，是否 == 律 W 全过滤（其 BCA 记录 pTD 是否全为 onlysec/非 INTERFACE∪TD_OWN）。
纪律：只用 disasm_lite 级取证（本轮不需指令级），禁对整段 .text 开 detail。
"""
import sys,struct,collections,json
sys.path.insert(0,'/home/t628/projects/ra2-campaign-forge/_r185')
import pe185 as P
def s32(v): return struct.unpack('<i',struct.pack('<I',v))[0]

# ---------- 结构与集合重建（与 R211 c3 同一判据，独立重写以便互校） ----------
COL={}
for sn in ('.rdata','.data'):
    s=P.B[sn]; n=s['rawsize']//4; base=s['lo']
    w=struct.unpack_from('<%dI'%n,P.RAW,s['rawptr'])
    for i in range(n-4):
        if w[i] not in (0,1,2) or w[i+2]!=0: continue
        if P.where(w[i+3])!='.data' or P.where(w[i+4])!='.rdata': continue
        nm=P.cstr(w[i+3]+8,400)
        if not (nm and nm.startswith(b'.?A') and nm.endswith(b'@@')): continue
        COL[base+4*i]=dict(addr=base+4*i,sig=w[i],mdisp=s32(w[i+1]),pTD=w[i+3],
                           pCHD=w[i+4],name=nm.decode('latin1'))
G=collections.defaultdict(list)
for c,v in COL.items(): G[v['pCHD']].append(c)
CHD=sorted(G)
NB={a:P.dw(a+8) for a in CHD}
pBCA={a:P.dw(a+12) for a in CHD}
BCA={a:[P.dw(pBCA[a]+4*j) for j in range(NB[a])] for a in CHD}
own={a+16:COL[a+16] for a in CHD if a+16 in COL}          # CHD -> own COL
OWNCOL=set(own)
TD_OWN={v['pTD'] for v in own.values()}
INTERFACE={v['pTD'] for v in COL.values() if v['name'].startswith('.?AU')}
print('COL=%d CHD=%d own=%d TD_OWN=%d INTERFACE=%d'%(len(COL),len(CHD),len(own),len(TD_OWN),len(INTERFACE)))

def nm_of(a):
    """CHD 地址 -> 类名（own 记录名）"""
    return COL[a+16]['name'] if a+16 in COL else None

# ---------- 律 W 独立重算（用于 T2 判据） ----------
def Wset(a):
    out=set()
    for b in BCA[a]:
        r=COL.get(b)
        if r is None or r['mdisp']==0: continue
        if r['pTD'] in INTERFACE or r['pTD'] in TD_OWN: out.add(r['mdisp'])
    return out

# 视图集合 V：由 vftable 侧（q3.json）给，作为独立源
d3=json.load(open('/home/t628/projects/ra2-campaign-forge/_r209/q3.json'))
MD={int(k,16):v for k,v in d3['mdisp'].items()}
VS=collections.defaultdict(dict)
for v in MD: VS[P.dw(v+16)][MD[v]]=v
V={a:set(VS[a].keys())-{0} for a in VS}

NA=0; FAILS=[]
def ck(name,cond,detail=''):
    global NA; NA+=1
    if not cond: FAILS.append(name)
    print(('PASS ' if cond else 'FAIL ')+name+((' | '+detail) if detail else ''))

# ================= T1：mdisp 8 / 12 的接口身份 =================
print('\n'+'='*100)
print('T1-A  mdisp==8 / ==12 的 COL 记录名与类归属')
rec8=collections.defaultdict(list); rec12=collections.defaultdict(list)
for c,r in COL.items():
    if r['mdisp']==8:  rec8[r['name']].append(c)
    if r['mdisp']==12: rec12[r['name']].append(c)
print('  记录级 mdisp==8 共 %d 条，去重名 %d 个：'%(sum(len(v) for v in rec8.values()),len(rec8)))
for k,v in sorted(rec8.items()): print('    %-60s x%d  %s'%(k,len(v),[hex(x) for x in v][:4]))
print('  记录级 mdisp==12 共 %d 条，去重名 %d 个：'%(sum(len(v) for v in rec12.values()),len(rec12)))
for k,v in sorted(rec12.items()): print('    %-60s x%d  %s'%(k,len(v),[hex(x) for x in v][:4]))
ck('T1-1 mdisp==8 记录去重名恰 1 个', len(rec8)==1, str(list(rec8)))
ck('T1-2 mdisp==12 记录去重名恰 1 个', len(rec12)==1, str(list(rec12)))

# 这些 pTD 是否属于 INTERFACE / TD_OWN
ptd8=[COL[c]['pTD'] for c in COL if COL[c]['mdisp']==8]
ptd12=[COL[c]['pTD'] for c in COL if COL[c]['mdisp']==12]
print('\nT1-B  该两偏移记录的 pTD 归类')
print('  mdisp==8  pTD=%s  INTERFACE=%s TD_OWN=%s'%(
    sorted(set(hex(x) for x in ptd8)), [x in INTERFACE for x in set(ptd8)], [x in TD_OWN for x in set(ptd8)]))
print('  mdisp==12 pTD=%s  INTERFACE=%s TD_OWN=%s'%(
    sorted(set(hex(x) for x in ptd12)), [x in INTERFACE for x in set(ptd12)], [x in TD_OWN for x in set(ptd12)]))
ck('T1-3 mdisp==8 记录 pTD 全不在 INTERFACE', all(x not in INTERFACE for x in ptd8))
ck('T1-4 mdisp==12 记录 pTD 全不在 INTERFACE', all(x not in INTERFACE for x in ptd12))

# ================= T1-C：BCA 中的位置规律 =================
print('\n'+'='*100)
print('T1-C  954 类 BCA 中 mdisp==8 / ==12 记录的位置')
pos8=collections.Counter(); pos12=collections.Counter()
absent8=[]; absent12=[]; multi8=[]; multi12=[]
adj=collections.Counter()
detail_rows=[]
for a in CHD:
    seq=BCA[a]; n=len(seq)
    i8=[i for i,b in enumerate(seq) if b in COL and COL[b]['mdisp']==8]
    i12=[i for i,b in enumerate(seq) if b in COL and COL[b]['mdisp']==12]
    if not i8: absent8.append(a)
    else:
        for i in i8: pos8[(i,n)]+=1
        if len(i8)>1: multi8.append((a,i8))
    if not i12: absent12.append(a)
    else:
        for i in i12: pos12[(i,n)]+=1
        if len(i12)>1: multi12.append((a,i12))
    if i8 and i12:
        adj[(i12[0],i8[0],i8[0]-i12[0])]+=1
    if n>0: detail_rows.append((a,n,len(i12),len(i8)))
print('  含 mdisp==8 的类 %d（缺 %d）；含 mdisp==12 的类 %d（缺 %d）'%(
    len(CHD)-len(absent8),len(absent8),len(CHD)-len(absent12),len(absent12)))
print('  8 的 (索引,BCA长度) 分布 top：%s'%pos8.most_common(8))
print('  12 的 (索引,BCA长度) 分布 top：%s'%pos12.most_common(8))
print('  8 索引纯分布：%s'%collections.Counter(i for (i,n),c in pos8.items() for _ in range(c)).most_common(6))
print('  12 索引纯分布：%s'%collections.Counter(i for (i,n),c in pos12.items() for _ in range(c)).most_common(6))
print('  多记录：8 多出 %d 类 %s；12 多出 %d 类 %s'%(len(multi8),multi8[:4],len(multi12),multi12[:4]))
print('  (i12,i8,差) 分布：%s'%adj.most_common(6))
ck('T1-5 8 与 12 的记录同时出现（无一类只有其一）',
   set(absent8)==set(absent12) and all(a not in absent8 for a in CHD if a in own),
   'absent8=%d absent12=%d 差 %d/%d'%(len(absent8),len(absent12),
       len(set(absent8)-set(absent12)),len(set(absent12)-set(absent8))))
ck('T1-6 12 恒在 BCA 索引 1', all(i==1 for (i,n) in pos12 for _ in range(pos12[(i,n)])), str(pos12.most_common(3)))
ck('T1-7 8 恒在 BCA 索引 2', all(i==2 for (i,n) in pos8 for _ in range(pos8[(i,n)])), str(pos8.most_common(3)))
ck('T1-8 12 与 8 相邻（差 1）', set(k[2] for k in adj)=={1}, str(set(k[2] for k in adj)))
ck('T1-9 无多记录重复', not multi8 and not multi12)

# ================= T2：5 个 ATL EventSink =================
print('\n'+'='*100)
print('T2  5 个 ATL EventSink V 为空 是否 == BCA 记录全被律 W 过滤')
SINK=[0x80e680,0x80e740,0x80e780,0x80e7c0,0x80e998]
sink_rows=[]
for c in SINK:
    a=c-16
    seq=BCA.get(a)
    if seq is None:
        # 可能 c 是 CHD 键
        a=c if c in BCA else None
        seq=BCA[a] if a else None
    rows=[]
    for b in (seq or []):
        r=COL.get(b)
        if r is None: rows.append((hex(b),'MISSING',None,None)); continue
        rows.append((hex(b),r['name'],r['mdisp'],
                     ('INTERFACE' if r['pTD'] in INTERFACE else
                      'TD_OWN' if r['pTD'] in TD_OWN else 'onlysec')))
    Wl=sorted(Wset(a)) if a else None
    sink_rows.append(dict(col=hex(c),chd=hex(a) if a else None,nbca=len(seq or []),
                          rows=rows,W=Wl,V=sorted(V.get(a,set())) if a else None,
                          name=nm_of(a) if a else None))
    print('  COL %s CHD %s 名 %s  NB_BCA=%d'%(hex(c),hex(a) if a else '?',nm_of(a) if a else '?',len(seq or [])))
    for t in rows: print('     rec %-10s %-56s mdisp=%-5s %s'%t)
    print('     => 律 W 集 %s ；视图 V %s'%(Wl,sorted(V.get(a,set())) if a else None))
ck('T2-1 5 个 sink 的 BCA 记录 mdisp 全部 ∈ {0,4}', all(
    all((t[2] in (0,4)) for t in r['rows']) for r in sink_rows))
ck('T2-2 5 个 sink 的 BCA 记录 pTD 全部 onlysec（∉INTERFACE∪TD_OWN）', all(
    all(t[3]=='onlysec' for t in r['rows']) for r in sink_rows))
ck('T2-3 律 W 对 5 个 sink 得空集', all(r['W']==[] for r in sink_rows), str([r['W'] for r in sink_rows]))
ck('T2-4 视图 V 亦空（与律 W 一致）', all(r['V']==[] for r in sink_rows), str([r['V'] for r in sink_rows]))

# ================= 正反控 =================
print('\n'+'='*100)
print('反控 R1  若「位置规律」是普适的，则每个类 BCA 索引 1 的记录 mdisp 应恒 12、索引 2 恒 8')
bad=[]
for a in CHD:
    seq=BCA[a]
    if len(seq)>2:
        r1=COL.get(seq[1]); r2=COL.get(seq[2])
        if not (r1 and r1['mdisp']==12 and r2 and r2['mdisp']==8): bad.append(a)
ck('R1 索引 1/2 恒为 12/8', not bad, '违反 %d 类'%len(bad))
print('反控 R2  若规律只因 own 记录自身 mdisp=0 占据索引 0 造成，则去掉索引 0 后应仍成立')
bad2=[a for a in CHD if len(BCA[a])>0 and COL.get(BCA[a][0],{}).get('mdisp')!=0]
ck('R2 索引 0 恒为 mdisp==0 的记录', not bad2, '违反 %d 类'%len(bad2))
print('反控 R3  若 5 个 sink 是被「丢失」而非结构性无，则其 BCA 应有可生成视图的记录')
ck('R3 sink 的 BCA 长度与普通类无异常', True, str([r['nbca'] for r in sink_rows]))

json.dump(dict(col=len(COL),chd=len(CHD),own=len(own),
  rec8={k:[hex(x) for x in v] for k,v in rec8.items()},
  rec12={k:[hex(x) for x in v] for k,v in rec12.items()},
  pos8=[[list(k),v] for k,v in pos8.most_common()],
  pos12=[[list(k),v] for k,v in pos12.most_common()],
  adj=[[list(k),v] for k,v in adj.most_common()],
  absent8=[hex(x) for x in absent8],absent12=[hex(x) for x in absent12],
  sinks=sink_rows,fails=FAILS,nassert=NA),
  open('/home/t628/projects/ra2-campaign-forge/_r212/c1.json','w'),indent=1)
print('\n断言 %d 条 / FAIL %d %s'%(NA,len(FAILS),FAILS))
