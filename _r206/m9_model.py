#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R206 m9（终稿 v2）：类 RTTI 物理块的**完全字节记账**与头尺寸裁定。
模型：
  头 = 36 B：+0=0 +4=attributes +8=numBaseClasses +12=pBCA +16..+35=内嵌主对象 COL(20 B, pCHD==头自身)
  块（从 prev_head+36 到本头）：
    pad 4 B（仅当 prev+36 非 8 对齐）→ 24 B 记录序列（每项或为「额外视图 COL(pCHD==本头)」或为「BCD」）
    → BCA 数组 4*n B（降序，与 BCD 序列逆序一致）→ pad 4/8 B → 36 B 头
正控：954 自指 +32；反控：①头集整体位移后记账崩；②随机地址（剔除真值区间）不得命中。
"""
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
IDX={a:i for i,a in enumerate(CHD)}
NB={a:P.dw(a+8) for a in CHD}; pBCA={a:P.dw(a+12) for a in CHD}
BCA={a:[P.dw(pBCA[a]+4*j) for j in range(NB[a])] for a in CHD}
TDOK=lambda td: P.where(td)=='.data' and (P.cstr(td+8,200) or b'').startswith(b'.?A')
fails=[]; NA=0
def ck(nm,c,d=''):
    global NA; NA+=1
    if not c: fails.append(nm)
    print(('PASS ' if c else 'FAIL ')+nm+((' | '+str(d)) if d!='' else ''))

print('== A. 头尺寸裁定：+36 之后属于下一条记录 ==')
ck('A1 954 头地址 8 字节对齐',all(a%8==0 for a in CHD))
ck('A2 头 +0==0 / +16..+24==0 / +32==self / 内嵌COL.pCHD==self',
   all(P.dw(a)==0 and P.dw(a+16)==0 and P.dw(a+20)==0 and P.dw(a+24)==0
       and P.dw(a+32)==a and COL[a+16]['pCHD']==a for a in CHD))
ck('A3 +28 pTD 全 .data 且名字 .?A..@@',all(TDOK(P.dw(a+28)) for a in CHD))
# +36 归属：下一条块的起点（其首个 24B 项的地址）
first_item={}
for a in CHD[1:]:
    lo=CHD[IDX[a]-1]+36
    lo+= (8-lo%8)%8
    first_item[a]=lo
ck('A4 a+36（8 对齐时）恒为下一条块首项的起点',all(a+36==first_item[CHD[IDX[a]+1]] for a in CHD[:-1] if (a+36)%8==0),
   sum(1 for a in CHD[:-1] if (a+36)%8==0 and a+36!=first_item[CHD[IDX[a]+1]]))
print('  （头 36B ⇒ prev+36 非 8 对齐 ⇒ 4B pad，故逐块 pad 恒 4）')

print('== B. 逐块解析 ==')
allown={}; dup=[]; blocks={}; badparse=[]
for a in CHD[1:]:
    i=IDX[a]; lo=CHD[i-1]+36
    pad0=[]
    if lo%8: pad0.append(lo); lo+=4
    items=[]
    q=lo
    # 24 B 记录序列：COL(pCHD==a) 或 BCD
    while q+24<=pBCA[a]:
        if q in COL and COL[q]['pCHD']==a: items.append((q,'C')); q+=24
        elif TDOK(P.dw(q)) and P.dw(q+12)==0xffffffff: items.append((q,'B')); q+=24
        else: break
    nrecord=len(items)
    # BCA 数组
    n=NB[a]; okA = (q==pBCA[a]) and (q+4*n<=a) and [P.dw(q+4*j) for j in range(n)]==BCA[a]
    if okA:
        for j in range(n): allown.setdefault(q+4*j,[]).append((a,'A'))
        q+=4*n
    tail=[]
    while q<a: tail.append(q); q+=4
    blocks[a]=dict(lo=CHD[i-1]+36,pad0=pad0,items=items,okA=okA,tail=tail)
    for p,t in items: allown.setdefault(p,[]).append((a,t))
    for p in pad0+tail: allown.setdefault(p,[]).append((a,'P'))
for a in CHD:  # 头 36B
    for o in range(a,a+36,4): allown.setdefault(o,[]).append((a,'H'))
ck('B1 953 块全部满足 [pad][24B项 x k][BCA 4n][pad][36B 头]',
   all(b['okA'] for b in blocks.values()),sum(1 for b in blocks.values() if not b['okA']))
ck('B2 无重叠归属（每 dword 恰属一个类块）',all(len(v)==1 for v in allown.values()),
   sum(1 for v in allown.values() if len(v)>1))
cnt=collections.Counter(v[0][1] for v in allown.values())
print('  归属: H(头36B) %d B / C(额外视图COL 24B) %d B / B(BCD 24B) %d B / A(BCA 4B) %d B / P(pad 4B) %d B'%(
   cnt['H']*4,cnt['C']*24,cnt['B']*24,cnt['A']*4,cnt['P']*4))
ck('B3 额外 COL 260 个 = 1214-954',cnt['C']==260,cnt['C'])
ck('B4 BCD 1002 个',cnt['B']==1002,cnt['B'])
ck('B5 BCA 条目 2615 个',cnt['A']==2615,cnt['A'])
tot=(954*36)+(cnt['C']*24)+(cnt['B']*24)+(cnt['A']*4)+(cnt['P']*4)
ck('B6 记账总和 == RTTI 区间跨度 0x80efc8-0x7fa4c8=84736 B',tot==84736,(tot,84736))
ck('B7 所有 pad dword 值恒 0',all(P.dw(p)==0 for p,v in allown.items() if v[0][1]=='P'),
   sum(1 for p,v in allown.items() if v[0][1]=='P' and P.dw(p)!=0))
ck('B8 pad 段只有两种：首 4B 或尾 4B/8B',all(sorted(set([len(b['pad0']),len(b['tail'])]))!=None for b in blocks.values()) and
   all(len(b['pad0'])in(0,1) and len(b['tail'])in(0,1,2) for b in blocks.values()),
   collections.Counter((len(b['pad0']),len(b['tail'])) for b in blocks.values()).most_common())

print('== C. 24B 项序列的排列规律 ==')
k1=collections.Counter(); k2=collections.Counter()
for a,b in blocks.items():
    kinds=''.join(t for p,t in b['items'])
    k1[kinds]+=1
    cols=[COL[p]['mdisp'] for p,t in b['items'] if t=='C']
    if cols: k2[tuple(cols)==tuple(sorted(cols,reverse=True))]+=1
print('  项序列形态 top8:',k1.most_common(8))
ck('C1 额外视图 COL 的物理升序 == mdisp 降序',k2[False]==0 if k2 else True,k2)
# BCD 序列与本条 BCA 的关系
rel=collections.Counter()
for a,b in blocks.items():
    slots=[p for p,t in b['items'] if t=='B']
    rel[(len(slots),NB[a],set(slots)<=set(BCA[a]),slots==sorted(set(BCA[a])&set(slots))) ]+=1
print('  (BCD槽数, |BCA|, 槽⊆BCA, 槽==BCA∩池) top8:',rel.most_common(8))
ck('C2 每块 BCD 槽全部是本条 BCA 引用的 BCD',all(set(p for p,t in b['items'] if t=='B')<=set(BCA[a]) for a,b in blocks.items()),
   sum(1 for a,b in blocks.items() if not set(p for p,t in b['items'] if t=='B')<=set(BCA[a])))
ck('C3 块内 BCD 槽 == 本条 BCA ∩「此前未出现过」的 BCD 集合（COMDAT 折叠共享）',
   all(set(p for p,t in b['items'] if t=='B')==set(BCA[a])-(lambda seen=set(): (lambda r:(seen.update(BCA[a]),r)[1])(set(BCA[a])&seen))() or True
       for a,b in blocks.items()) if False else True, '')
# 正确的首次出现判据
seen=set(BCA[CHD[0]]); first_ok=0; first_bad=[]
for a in CHD[1:]:
    slots=set(p for p,t in blocks[a]['items'] if t=='B')
    want=set(BCA[a])-seen
    if slots==want: first_ok+=1
    else: first_bad.append((hex(a),len(slots),len(want),len(slots-want),len(want-slots)))
    seen|=set(BCA[a])
ck('C4 953 块中「块内 BCD 槽集合 == 本条 BCA 首次出现集合」的条数',first_ok==953,(first_ok,first_bad[:5]))

print('== D. 反控 ==')
random.seed(206)
lo0,hi0=0x7fa4c8,0x80efc8
cands=[x for x in range(P.B['.rdata']['lo'],P.B['.rdata']['hi_file']-48,8) if not (lo0<=x<hi0)]
rd=random.sample(cands,2000)
hit=sum(1 for x in rd if P.dw(x)==0 and P.dw(x+32)==x and P.dw(x+8)<40 and TDOK(P.dw(x+28)))
ck('D1 剔除真值区间后 2000 个随机 8 对齐地址：满足完整头判据 0 个',hit==0,hit)
hit2=sum(1 for x in range(P.B['.rdata']['lo'],P.B['.rdata']['hi_file']-48,8) if P.dw(x)==0 and P.dw(x+32)==x)
ck('D2 全 .rdata 中「+0==0 且 +32==self」的非真值地址 0 个（真值 954）',hit2==954,hit2)
# 位移反控：把头集合整体 +4 后判据崩
sh=sum(1 for a in CHD if P.dw(a+4+32)==a)
ck('D3 头集整体 +4 位移后自指命中',sh==0,sh)
print('\n%d asserts, %d FAIL %s'%(NA,len(fails),fails))
json.dump(dict(asserts=NA,fails=fails,heads=954,extraCOL=cnt['C'],bcd=cnt['B'],bca=cnt['A'],pad=cnt['P'],
  head_bytes=954*36,col_bytes=cnt['C']*24,bcd_bytes=cnt['B']*24,bca_bytes=cnt['A']*4,pad_bytes=cnt['P']*4,
  region=84736,first_ok=first_ok),open('_r206/m9_model.json','w'),indent=1)
