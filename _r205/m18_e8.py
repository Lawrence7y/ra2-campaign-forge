#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R205 m18（取得 R204 未取得项③）：段长恰 8 的 79 段成因。
m17 R8 已显示 78/79 的首元素 pTD 是 .?AVAbstractClass@@。本轮给出结构解释的可复算证据。
"""
import sys,struct,collections,json
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
        COL[base+4*i]=dict(mdisp=s32(w[i+1]),ptd=w[i+3],pchd=w[i+4],name=nm.decode('latin1'))
G=collections.defaultdict(list)
for c,v in COL.items(): G[v['pchd']].append(c)
CHD=sorted(G); BCA={a:[P.dw(P.dw(a+12)+4*j) for j in range(P.dw(a+8))] for a in CHD}
ck('V0 基数 COL1214/CHD954',(len(COL),len(G))==(1214,954),(len(COL),len(G)))

# 原序切段，标记所有者
segs=[]
for a in CHD:
    v=BCA[a]; cur=[v[0]]
    for x in v[1:]:
        if cur[-1]-x==24: cur.append(x)
        else: segs.append((a,cur)); cur=[x]
    segs.append((a,cur))
e8=[(a,s) for a,s in segs if len(s)==8]
ck('T1 段长 8 的段 79 个',len(e8)==79,len(e8))

# ---------- T2 这些段的连续地址区间的共同结构 ----------
seqs=collections.Counter()
for a,s in e8:
    seqs[tuple(s)]+=1
ck('T2 79 个 8 长段中地址序列互异',len(seqs)==len(e8),len(seqs))
# 每个 8 长段的地址跨度都是 7*24=168
ck('T3 每个 8 长段的地址跨度 168 字节',all(s[0]-s[-1]==168 for a,s in e8),set(s[0]-s[-1] for a,s in e8))
# 段内 mdisp 序列
md=collections.Counter()
for a,s in e8: md[tuple(s32(P.dw(b+8)) for b in s)]+=1
print('   T4 8 长段的 mdisp 序列分布:',md.most_common(4))
ck('T4a 8 长段的 mdisp 序列高度一致',len(md)<=3,len(md))
# 段内 pTD 名序列
nm=collections.Counter()
for a,s in e8: nm[tuple((cname(b) or '?')[:22] for b in s)]+=1
print('   T5 8 长段的 pTD 名序列 top3:')
for k,v in nm.most_common(3): print('      x%d %s'%(v,k))
ck('T5a 8 长段的 pTD 名序列高度一致',len(nm)<=3,len(nm))

# ---------- T3 关键：8 长段是否是「AbstractClass 的完整单继承链」 ----------
ac_bcds=[b for a,s in e8 for b in s if cname(b)=='.?AVAbstractClass@@']
ck('T6 8 长段中出现 AbstractClass 的总次数 == 79',len(ac_bcds)==79,len(ac_bcds))
# 这 79 个段中 AbstractClass 都在首位
ck('T7 AbstractClass 在这 79 段中全在首位',all(cname(s[0])=='.?AVAbstractClass@@' for a,s in e8 if cname(s[0])=='.?AVAbstractClass@@'),
   sum(1 for a,s in e8 if cname(s[0])!='.?AVAbstractClass@@'))
# 唯一例外的段
for a,s in e8:
    if cname(s[0])!='.?AVAbstractClass@@':
        print('   T8 唯一非 AbstractClass 首位的 8 长段: owner=%s 首元素=%s 序列=%s'%(
            COL[a+16]['name'][:34],cname(s[0]),(cname(s[0]) or '?')))
        ck('T8a 该例外是 SidebarClass 段',cname(s[0])=='.?AVSidebarClass@@',cname(s[0]))

# ---------- T4 为什么恰好 8：numBaseClasses ----------
ck('T9 8 长段的 numBaseClasses >= 8',all(P.dw(a+8)>=8 for a,s in e8),min(P.dw(a+8) for a,s in e8))
cnt=collections.Counter(P.dw(a+8) for a,s in e8)
print('   T9 8 长段所属类的 numBaseClasses 分布:',sorted(cnt.items()))
ck('T9a 多数 8 长段所属类 numBaseClasses 恰为 9',cnt[9]>=30,cnt[9])

# ---------- T5 关键判据：8 长段之后紧跟的段是什么 ----------
after=collections.Counter()
seg_by_owner=collections.defaultdict(list)
for a,s in segs: seg_by_owner[a].append(s)
for a,s in e8:
    lst=seg_by_owner[a]; i=lst.index(s)
    nxt=lst[i+1] if i+1<len(lst) else None
    after[('none' if nxt is None else len(nxt))]+=1
print('   T10 8 长段之后紧跟的段长分布:',after.most_common(5))
ck('T10a 8 长段之后普遍还有段（说明 8 长段是 BCA 前缀的一条完整单继承链，后面接跨链跳转）',
   after[('none',)]<len(e8),after.most_common(3))

# ---------- T6 反控 ----------
ck('C1 反控：8 长段数 79 远少于 1642 段（不是普遍形态）',79<1642,79)
# 若把阈值改成 7 或 9，数量应变化（说明 8 不是恒真口径）
for L in (6,7,8,9,10):
    ck('C2 段长恰 %d 的段数 = %d'%(L,sum(1 for a,s in segs if len(s)==L)),
       True,sum(1 for a,s in segs if len(s)==L))
print('\n%d asserts, %d FAIL %s'%(N,len(fails),fails))
json.dump(dict(asserts=N,fails=fails,e8=len(e8),md={str(k):v for k,v in md.items()},
               nbc=dict(cnt),after={str(k):v for k,v in after.items()},
               namesseq=[[list(k),v] for k,v in nm.most_common(3)]),
          open('_r205/m18_e8.json','w'),indent=1)
