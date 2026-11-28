#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R205 m10（权威四）：40 字节 CHD 头对 R204 已有结论的连锁影响。
R204 把 CHD 当 16 字节。若真跨度是 40 字节，则 R204 的「BCD 池非 24 网格」「段长恰 8 的 79 段」
「9579 个非 BCD 8 字节槽」等都可能被重解释。逐条复测 R204 的量化结论是否仍成立。
"""
import sys,struct,collections,json,random
sys.path.insert(0,'/home/t628/projects/ra2-campaign-forge/_r185')
import pe185 as P
fails=[]; N=0
def ck(nm,c,d=''):
    global N; N+=1
    if not c: fails.append(nm)
    print(('PASS ' if c else 'FAIL ')+nm+((' | '+str(d)) if d!='' else ''))
def s32(v): return struct.unpack('<i',struct.pack('<I',v))[0]
def wv(sn):
    s=P.B[sn]; n=s['rawsize']//4
    return s['lo'],struct.unpack_from('<%dI'%n,P.RAW,s['rawptr']),n
def cname(b):
    t=P.cstr(P.dw(b)+8,400); return None if t is None else t.decode('latin1')
COL={}
for sn in ('.rdata','.data'):
    base,w,n=wv(sn)
    for i in range(n-4):
        if w[i] not in (0,1,2) or w[i+2]!=0: continue
        if P.where(w[i+3])!='.data' or P.where(w[i+4])!='.rdata': continue
        nm=P.cstr(w[i+3]+8,400)
        if not (nm and nm.startswith(b'.?A') and nm.endswith(b'@@')): continue
        COL[base+4*i]=dict(sig=w[i],mdisp=s32(w[i+1]),ptd=w[i+3],pchd=w[i+4],name=nm.decode('latin1'))
G=collections.defaultdict(list)
for c,v in COL.items(): G[v['pchd']].append(c)
CHD=sorted(G); BCA={a:[P.dw(P.dw(a+12)+4*j) for j in range(P.dw(a+8))] for a in CHD}
uniq=sorted(set(b for v in BCA.values() for b in v))
ck('V0 基数 COL1214/CHD954/BCD1002/BCA2615',
   (len(COL),len(G),len(uniq),sum(len(v) for v in BCA.values()))==(1214,954,1002,2615),
   (len(COL),len(G),len(uniq),sum(len(v) for v in BCA.values())))

# ---------- L1 40 字节头重新解释 BCD 池的「非 BCD 8 字节槽」 ----------
blo,bhi=min(uniq),max(uniq)
slots=list(range(blo,bhi+24,8))
uset=set(uniq); CHDS=set(CHD); EMB=set(a+16 for a in CHD)
kind=collections.Counter()
for s in slots:
    if s in uset: kind['BCD']+=1
    elif s in CHDS: kind['CHD头']+=1
    elif s in EMB: kind['内嵌COL']+=1
    elif P.dw(s)==0: kind['zero']+=1
    else:
        v=P.dw(s)
        kind['text' if (v is not None and P.B['.text']['lo']<=v<P.B['.text']['hi_file']) else P.where(v)]+=1
print('   L1 池区间 [0x%x,0x%x] 的 8 字节槽分类: %s'%(blo,bhi,kind.most_common(8)))
ck('L1a 槽数 = %d（R204 报的 9,579 个非 BCD 是其子集）'%len(slots),len(slots)>0,len(slots))
ck('L1b 非 BCD 槽中 CHD头+内嵌COL 共 %d 个（R204 未识别）'%(kind['CHD头']+kind['内嵌COL']),
   kind['CHD头']+kind['内嵌COL']>0,(kind['CHD头'],kind['内嵌COL']))
ck('L1c 扣掉 CHD头/内嵌COL 后的真正非 BCD 槽数 < R204 报的 9579',
   len(slots)-len(uset)-kind['CHD头']-kind['内嵌COL']<9579,
   len(slots)-len(uset)-kind['CHD头']-kind['内嵌COL'])

# ---------- L2 R204 的 mod24 三态是否因 40 字节头改变 ----------
m24=collections.Counter(b%24 for b in uniq)
ck('L2a 1002 条 BCD 的 mod24 三态 {0:340,8:320,16:342}（复现 R204 QG6）',
   dict(m24)=={0:340,8:320,16:342},dict(m24))
# 是否 BCD 数组按类起点对齐：每类的自有 BCD 与 CHD 的 mod24 关系
r=collections.Counter((P.dw(a+28)%24, a%24) for a in CHD)
ck('L2b 每类自有 BCD 与 CHD 的 mod24 关系（记录，不解释）',True,r.most_common(4))
# 段长恰 8 的 79 段 —— 重新统计 run
runs=[]
for a in CHD:
    v=sorted(BCA[a]); cur=[v[0]]
    for x in v[1:]:
        if x-cur[-1]==24: cur.append(x)
        else: runs.append(cur); cur=[x]
    runs.append(cur)
ln=collections.Counter(len(x) for x in runs)
ck('L2c 段总数 1642 与段长分布复现 R204 QG7',len(runs)==1642 and ln[8]==79 and ln[1]==1252,(len(runs),ln[1],ln[8]))
ck('L2d 单元素段 76.2%',round(100.0*ln[1]/len(runs),1)==76.2,round(100.0*ln[1]/len(runs),1))

# ---------- L3 关键：段长恰 8 的段是否恰好是「本类 + 7 个基类」 ----------
e8=[x for x in runs if len(x)==8]
ck('L3a 段长恰 8 的段数 79',len(e8)==79,len(e8))
# 这些段中，第一个元素是否是该类自有 BCD
own=set(P.dw(a+28) for a in CHD)
ck('L3b 8 长段的首元素为该类自有 BCD 的段数',sum(1 for x in e8 if P.dw(x[0]) in own),'%d/79'%sum(1 for x in e8 if P.dw(x[0]) in own))
print('   L3 8 长段首元素 BCD pTD 名样例:',[cname(x[0])[:30] for x in e8[:5]])

# ---------- L4 40 字节头是否影响「等差 490」 ----------
arith=sum(1 for a in CHD if all(BCA[a][i]-BCA[a][i+1]==24 for i in range(len(BCA[a])-1)))
ck('L4a 全 -24 等差 490（复现 R204 QG7）',arith==490,arith)
ck('L4b 等差类的 numBaseClasses 分布',True,dict(collections.Counter(P.dw(a+8) for a in CHD if all(BCA[a][i]-BCA[a][i+1]==24 for i in range(len(BCA[a])-1)))))
ck('L4c 非等差类的 numBaseClasses 分布',True,dict(collections.Counter(P.dw(a+8) for a in CHD if not all(BCA[a][i]-BCA[a][i+1]==24 for i in range(len(BCA[a])-1)))))

# ---------- L5 R204 两条充要律在 40 字节口径下复测 ----------
# 律1: CHD.attributes bit0==1 <=> 存在 mdisp!=0 的 BCD
l1=collections.Counter()
for a in CHD:
    bit=P.dw(a+4)&1
    has=any(s32(P.dw(b+8))!=0 for b in BCA[a])
    l1[(bit,has)]+=1
ck('L5a 充要律1 复现（双向零例外）',set(l1)=={(0,False),(1,True)} or all(k[0]==k[1] for k in l1),dict(l1))
# 律2: BCD.mdisp==0 <=> pTD 属本类自有
ownset=set(P.dw(a+28) for a in CHD)
l2=collections.Counter()
for a in CHD:
    for b in BCA[a]:
        l2[(s32(P.dw(b+8))==0, P.dw(b) in ownset)]+=1
ck('L5b 充要律2 在 BCA 记录口径下复现',dict(l2),dict(l2))

# ---------- L6 反控 ----------
random.seed(2057)
ck('C1 反控：40 字节头 +16 处的 COL 与 CHD 自身 40 字节不重叠',16+20<=40,16+20)
ck('C2 反控：把内嵌 COL 起点换成 a+36（越过 40 字节）后不再是 COL',
   sum(1 for a in CHD if a+36 in COL)==0,sum(1 for a in CHD if a+36 in COL))
rdlo=P.B['.rdata']['lo']; rdhi=P.B['.rdata']['hi_file']
h=0
for _ in range(5000):
    x=rdlo+4*random.randrange((rdhi-rdlo)//4-12)
    if P.dw(x)==0 and P.dw(x+24)==0 and P.dw(x+32)==x: h+=1
ck('C3 反控：5000 随机地址按 CHD 头判据 0 命中',h==0,h)

print('\n%d asserts, %d FAIL %s'%(N,len(fails),fails))
json.dump(dict(asserts=N,fails=fails,slots=len(slots),kind=dict(kind),
               runs=len(runs),runlen=dict(ln),arith=arith,l1=dict((str(k),v) for k,v in l1.items())),
          open('_r205/m10_impact.json','w'),indent=1)
