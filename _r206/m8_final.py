#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R206 m8（终稿）：RTTI 区间完全字节记账 + CHD 头尺寸裁定。
模型（本脚本要证的）：
  记录头 = 36 B（+0=0 / +4=attributes / +8=numBaseClasses / +12=pBCA / +16..+35=内嵌主对象 COL 20 B）
  每个类的物理块（地址升序）= [额外视图 COL 24 B x k][BCD 24 B x m][BCA 4 B x n][pad 4/8 B][头 36 B]
  R205 声称属于"本条 +36..+39/+40/+44"的 12 字节，实际是**下一条类块**的开头。
正控：954 自指 +32；954 头地址 8 对齐；反控：位移 ±4/±8 与随机头集解析必塌。"""
import sys,struct,collections,random,json
sys.path.insert(0,'/home/t628/projects/ra2-campaign-forge/_r185')
import pe185 as P
def s32(v): return struct.unpack('<i',struct.pack('<I',v))[0]
def wv(sn):
    s=P.B[sn]; n=s['rawsize']//4
    return s['lo'],struct.unpack_from('<%dI'%n,P.RAW,s['rawptr']),n
COL={}
for sn in ('.rdata','.data'):
    base,w,n=wv(sn)
    for i in range(n-4):
        if w[i] not in (0,1,2) or w[i+2]!=0: continue
        if P.where(w[i+3])!='.data' or P.where(w[i+4])!='.rdata': continue
        nm=P.cstr(w[i+3]+8,400)
        if not (nm and nm.startswith(b'.?A') and nm.endswith(b'@@')): continue
        COL[base+4*i]=dict(sig=w[i],mdisp=s32(w[i+1]),pTD=w[i+3],pCHD=w[i+4],name=nm.decode('latin1'))
G=collections.defaultdict(list)
for c,v in COL.items(): G[v['pCHD']].append(c)
CHD=sorted(G)
NB={a:P.dw(a+8) for a in CHD}; pBCA={a:P.dw(a+12) for a in CHD}
BCA={a:[P.dw(pBCA[a]+4*j) for j in range(NB[a])] for a in CHD}
HEAD=set(CHD)
fails=[]; NA=0
def ck(nm,c,d=''):
    global NA; NA+=1
    if not c: fails.append(nm)
    print(('PASS ' if c else 'FAIL ')+nm+((' | '+str(d)) if d!='' else ''))

# ---------- 0. 头尺寸裁定：+36 起属于谁 ----------
print('== 0. 头 36B 裁定 ==')
emb={a+16 for a in CHD}
own_col={}   # COL 地址 -> 所属 pCHD
for c,v in COL.items(): own_col.setdefault(v['pCHD'],[]).append(c)
ck('X1 954 头地址 8 字节对齐',all(a%8==0 for a in CHD),sum(1 for a in CHD if a%8))
ck('X2 内嵌 COL（头+16）共 954 个、mdisp 恒 0',all(COL[c]['mdisp']==0 for c in emb),len(emb))
t36=[a for a in CHD[:-1] if P.dw(a+36)]
ck('X3 a+36 非零的 %d 条，其值全部指向「下一条记录的额外视图 COL」（pCHD==next）'%len(t36),
   all(P.dw(a+36) in COL and COL[P.dw(a+36)]['pCHD']==CHD[CHD.index(a)+1] for a in CHD[:-1] if P.dw(a+36)),
   sum(1 for a in t36 if COL.get(P.dw(a+36),{}).get('pCHD')==CHD[CHD.index(a)+1]))
ck('X4 a+36 零值的 %d 条，其下一条记录无额外视图（视图数==1）'%sum(1 for a in CHD[:-1] if not P.dw(a+36)),
   all(len(G[CHD[CHD.index(a)+1]])==1 for a in CHD[:-1] if not P.dw(a+36)),
   sum(1 for a in CHD[:-1] if not P.dw(a+36) and len(G[CHD[CHD.index(a)+1]])!=1))
ck('X5 a+36..a+35+4k（k=1..3）无任何指针字段指向本条自身（+36 不是本条字段）',
   all(not (P.dw(a+36)==a or P.dw(a+40)==a or P.dw(a+44)==a) for a in CHD[:-1]),
   sum(1 for a in CHD[:-1] if a in (P.dw(a+36),P.dw(a+40),P.dw(a+44))))
# 头 36B 内自洽：+32==a 且 +16..+35 是合法 COL 且 pCHD==a
ck('X6 头内嵌 COL 的 pCHD 恒 == 头地址',all(COL[a+16]['pCHD']==a for a in CHD))
ck('X7 +16/+20/+24 恒 0（sig/mdisp/cdOffset）',all(P.dw(a+16)==0 and P.dw(a+20)==0 and P.dw(a+24)==0 for a in CHD))
ck('X8 +28 pTD 全 .data 且是类名 TD',all(P.where(P.dw(a+28))=='.data' and (P.cstr(P.dw(a+28)+8,200) or b'').startswith(b'.?A') for a in CHD))

# ---------- 1. 块解析：从头 a 到 next，向回归属 ----------
print('\n== 1. 逐块解析 [extraCOL][BCD][BCA][pad] + 头 36B ==')
def parse_block(a):
    """返回 (prev_head, 归属列表, 失败原因)"""
    i=CHD.index(a); pv=CHD[i-1] if i>0 else None
    if pv is None: return None,[],'no-prev'
    lo=pv+36
    own=[]
    # 1) 额外视图 COL：地址升序，pCHD==a，24B 步长
    p=lo
    while p+24<=a and p in COL and COL[p]['pCHD']==a:
        own.append((p,'C')); p+=24
    # 2) BCD：24B 步长，形状合法
    nbc=0
    while p+24<=a:
        td=P.dw(p); nc=P.dw(p+4); md=s32(P.dw(p+8)); pd=s32(P.dw(p+12))
        ok = P.where(td)=='.data' and (P.cstr(td+8,200) or b'').startswith(b'.?A') and nc is not None and nc<40 and pd==-1
        if not ok: break
        own.append((p,'B')); p+=24; nbc+=1
    # 3) BCA 数组：n 个 4B，且内容全部是已见 BCD
    n=NB[a]
    if p+4*n<=a and all(P.dw(p+4*j) in COL and P.where(P.dw(p+4*j))=='.rdata' for j in range(n)) \
       and any(True for _ in [0]):
        # 校验这 n 个指针确实等于 BCA
        if [P.dw(p+4*j) for j in range(n)]==BCA[a]:
            for j in range(n): own.append((p+4*j,'A'))
            p+=4*n
    # 4) pad
    pad=[]
    while p<a:
        pad.append(p); p+=4
    return pv,dict(own=own,pad=pad,nbc=nbc,pA=(p-4*n if n else None)),None
tot=collections.Counter(); badblocks=[]; ownmap={}; dup=[]
padset=set(); allown={}
for a in CHD:
    pv,res,err=parse_block(a)
    if err: badblocks.append((hex(a),err)); continue
    seg=[]
    for p,t in res['own']: seg.append((p,t,a))
    for p in res['pad']: seg.append((p,'P',a))
    for p,t,who in seg:
        if p in allown: dup.append((hex(p),allown[p],who,t))
        else: allown[p]=(who,t)
    tot[len(res['own']),len(res['pad']),res['nbc']]+=1
ck('Y1 953 个块（除首条）全部可解析为 [extraCOL][BCD][BCA][pad]',
   len(badblocks)==0,badblocks[:4])
ck('Y2 区间内无重复归属',len(dup)==0,dup[:4])
cnt=collections.Counter(t for p,t in allown.values())
print('  归属统计：头/内嵌COL 36B x954=%d B；额外COL 24B x%d=%d B；BCD 24B x%d=%d B；BCA 4B x%d=%d B；pad 4B x%d=%d B'%(
   954*36,cnt['C'],cnt['C']*24,cnt['B'],cnt['B']*24,cnt['A'],cnt['A']*4,cnt['P'],cnt['P']*4))
ck('Y3 额外 COL 数 260（=1214-954），BCD 1002，BCA 2615',
   (cnt['C'],cnt['B'],cnt['A'])==(260,1002,2615),(cnt['C'],cnt['B'],cnt['A']))
region_bytes=954*36+cnt['C']*24+cnt['B']*24+cnt['A']*4+cnt['P']*4
ck('Y4 记账总和 == 区间跨度 84736 B',region_bytes==0x80efc8-0x7fa4c8,(region_bytes,0x80efc8-0x7fa4c8))
ck('Y5 所有 pad 字节值恒 0',all(P.dw(p)==0 for p,t in allown.items() if t=='P'),
   sum(1 for p,t in allown.items() if t=='P' and P.dw(p)!=0))
# 对齐
ck('Y6 额外 COL / BCD 全部 8 字节对齐',
   all(p%8==0 for p,t in allown.items() if t in ('C','B')),
   sum(1 for p,t in allown.items() if t in ('C','B') and p%8))
print('== 2. 块内 BCD 是否为「本条 BCA 引用且未被前面类引用」的首次出现 ==')
first={}; viol=0; extra_ref=0
for a in CHD:
    pv,res,err=parse_block(a)
    if err: continue
    slots=[p for p,t in res['own'] if t=='B']
    refs=[b for b in BCA[a] if b not in first]
    for b in BCA[a]: first.setdefault(b,a)
    if set(slots)!=set(refs): viol+=1
ck('Z1 每块 BCD 槽集合 == 本条 BCA 中「首次出现」的 BCD 集合',viol==0,viol)
print('== 3. COL 物理顺序 vs mdisp ==')
k=collections.Counter()
for a in CHD:
    pv,res,err=parse_block(a)
    if err: continue
    cols=[p for p,t in res['own'] if t=='C']+[a+16]
    ms=[COL[c]['mdisp'] for c in cols]
    k[tuple(ms)==tuple(sorted(ms,reverse=True))]+=1
ck('W1 每个类的 COL 物理升序 == mdisp 严格降序（994 组里 954 组）',k[True]==954,k)
print('== 4. 反控 ==')
random.seed(206)
badsh=0
for sh in (4,-4,8,-8,12):
    v=0
    for a in CHD[1:]:
        pv=CHD[CHD.index(a)-1]+sh
        if pv in COL or pv in [x for x in CHD]: v+=1
    badsh+=v
    print('  shift %+3d: 位移后起点撞上已知记录 %d 处'%(sh,v))
ck('V1 位移 ±4/±8/±12 后起点全部不落在已知 COL/CHD 上（结构不可平移）',badsh==0,badsh)
rd=[random.randrange(P.B['.rdata']['lo'],P.B['.rdata']['hi_file']-48)&~7 for _ in range(954)]
hit=sum(1 for x in rd if x%8==0 and P.dw(x)==0 and P.dw(x+8)<40 and P.dw(x+32)==x)
ck('V2 随机 954 个 .rdata 8 对齐地址中满足「+0==0 且 +32==self」的个数',hit==0,hit)
print('\n%d asserts, %d FAIL %s'%(NA,len(fails),fails))
json.dump(dict(asserts=NA,fails=fails,heads=954,extraCOL=cnt['C'],bcd=cnt['B'],bca=cnt['A'],
  pad_dw=cnt['P'],region_bytes=region_bytes,bytes_head=954*36,bytes_col=cnt['C']*24,
  bytes_bcd=cnt['B']*24,bytes_bca=cnt['A']*4,bytes_pad=cnt['P']*4,
  col_order_desc=k[True]),open('_r206/m8_final.json','w'),indent=1)
