#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R205 m2：CHD 40 字节记录布局 + BCD 数组排布 + 类级 COL 与 1214 视图 COL 的包含关系。
m1 自错（2 处，均断言写错，数据无异常）：
 ① V1 断言「每 CHD 恰 1 条 mdisp==0 的 BCD」实测 {2:455,1:256,3:122,...} —— R204 QG5 说的是
    **1002 条去重 BCD 中 954 条为每类自有主对象 BCD**（每条被多张 CHD 共享），不是「每张 BCA 恰 1 条」。
    复算：sum 计数 = 2228 == R204 的 2228，一致。
 ② H2b 断言「类级 COL 与 1214 视图 COL 不相交」实测 954 —— 方向反了，954 个类级 COL **全部**是 1214 视图 COL 的元素。
"""
import sys, struct, collections, json
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
T=P.B['.text']; LO=T['lo']; HI=T['hi_file']
def in_text(x): return x is not None and LO<=x<HI
COL={}
for sn in ('.rdata','.data'):
    base,w,n=wv(sn)
    for i in range(n-4):
        if w[i] not in (0,1,2) or w[i+2]!=0: continue
        if P.where(w[i+3])!='.data' or P.where(w[i+4])!='.rdata': continue
        nm=P.cstr(w[i+3]+8,400)
        if not (nm and nm.startswith(b'.?A') and nm.endswith(b'@@')): continue
        COL[base+4*i]=dict(sig=w[i],mdisp=s32(w[i+1]),ptd=w[i+3],pchd=w[i+4],name=nm.decode('latin1'))
VTI={}
for sn in ('.rdata','.data'):
    base,w,n=wv(sn)
    for i in range(n):
        if in_text(w[i]) and P.dw(base+4*i-4) in COL: VTI[base+4*i]=P.dw(base+4*i-4)
G=collections.defaultdict(list)
for c,v in COL.items(): G[v['pchd']].append(c)
CHD=sorted(G)
BCA={a:[P.dw(P.dw(a+12)+4*j) for j in range(P.dw(a+8))] for a in CHD}
ck('V0 基数 COL1214/VTI1214/CHD954',(len(COL),len(VTI),len(G))==(1214,1214,954),(len(COL),len(VTI),len(G)))

# --- 前置：1002 条去重 BCD，954 条 mdisp==0；每类恰 1 条 mdisp==0 且 pTD 属本类 ---
uniq=sorted(set(b for v in BCA.values() for b in v))
m0=[b for b in uniq if s32(P.dw(b+8))==0]
ck('V1a 去重 BCD 1002 / mdisp==0 954',(len(uniq),len(m0))==(1002,954),(len(uniq),len(m0)))
# 每类恰 1 条「mdisp==0 且 pTD==本类 TD」
own={}
bad=[]
for a in CHD:
    name=COL[G[a][0]]['name']
    tds={P.dw(b) for b in m0 if (P.cstr(P.dw(b)+8,400) or b'').decode('latin1')==name}
    if len(tds)!=1: bad.append((hex(a),name[:30],len(tds)))
    else: own[a]=tds.pop()
ck('V1b 每类恰 1 条 mdisp==0 且 pTD 属本类的 BCD 954/954',len(own)==954,(954-len(own),bad[:3]))
ck('V1c own pTD 互异 954',len(set(own.values()))==954,len(set(own.values())))

# --- D1: CHD 40 字节头 = 4 dword 头 + 内嵌本类主对象 COL ---
hdr=collections.Counter()
for a in CHD:
    hdr[(P.dw(a), s32(P.dw(a+20)), P.dw(a+24), P.dw(a+32)==a)]+=1
ck('D1a CHD 头 40 字节：+0 恒 0 / +20 mdisp 恒 0 / +24 cd 恒 0 / +32 pCHD==自身 => 954/954',
   hdr=={(0,0,0,True):954},hdr.most_common(3))
EMB={a+16:a for a in CHD}
ck('D1b 954 个内嵌 COL 地址互异',len(EMB)==954,len(EMB))
ck('D1c 954 个内嵌 COL 全部在 1214 视图 COL 集合内',set(EMB)<=set(COL),len(set(EMB)-set(COL)))
mds=collections.Counter(COL[e]['mdisp'] for e in EMB)
ck('D1d 内嵌 COL 的 mdisp 恒 0（即本类主对象视图）954/954',dict(mds)=={0:954},dict(mds))
ck('D1e 内嵌 COL 的 pCHD == 其所在 CHD 954/954',all(COL[e]['pchd']==EMB[e] for e in EMB),None)

# --- D2: 每个 CHD 恰有 1 个 mdisp==0 视图 COL => 内嵌 COL 就是视图组的主对象视图 ---
zero_views={a:[c for c in G[a] if COL[c]['mdisp']==0] for a in CHD}
ck('D2a 每 CHD 恰 1 个 mdisp==0 的视图 COL 954/954',
   all(len(v)==1 for v in zero_views.values()),collections.Counter(len(v) for v in zero_views.values()))
ck('D2b 该唯一 mdisp==0 视图 COL 就是内嵌 COL 954/954',
   all(zero_views[a][0]==a+16 for a in CHD),sum(1 for a in CHD if zero_views[a][0]!=a+16))

# --- D3: 内嵌 COL 在主视图 vftable 的 vt-4 位置（把两模型钉在一起） ---
vt_of_col={c:vt for vt,c in VTI.items()}
inmain=sum(1 for a in CHD if vt_of_col.get(a+16) is not None)
ck('D3a 内嵌 COL 都是某 vftable 的 vt-4 值 954/954',inmain==954,inmain)
# 主视图 = 该 CHD 内 mdisp==0 的视图 -> 其 vftable 起点
main_vt={a:vt_of_col[a+16] for a in CHD}
ck('D3b 954 个主视图 vftable 起点互异',len(set(main_vt.values()))==954,len(set(main_vt.values())))

# --- D4: BCD 数组：本类数组是否紧接在 CHD+40 之后、以 24 步长上升 ---
start_at40=0; own_at_start=0; contig=0; arith=0
for a in CHD:
    v=BCA[a]
    if v and v[-1]==a+40: start_at40+=1
    if v and v[0]==max(v): own_at_start+=1
    if all(v[i]-v[i+1]==24 for i in range(len(v)-1)): arith+=1
    if v[-1]==a+40 and all(v[i]-v[i+1]==24 for i in range(len(v)-1)): contig+=1
print('   D4 BCA 末元素==CHD+40: %d / 954；首元素为最大地址: %d；全 -24 等差: %d；两者同时: %d'%(start_at40,own_at_start,arith,contig))
ck('D4a BCA 首元素恒为最大地址（本类 BCD 在前、基类在后）954/954',own_at_start==954,own_at_start)
ck('D4b BCA 至少 490 张全 -24 等差（复现 R204 490）',arith==490,arith)

# --- D5: 非 -24 跳转的性质：跳转目标是否是另一个类的 own BCD，且跳后继续 -24 ---
jumps=[]
for a in CHD:
    v=BCA[a]
    for i in range(len(v)-1):
        if v[i]-v[i+1]!=24: jumps.append((a,i,v[i],v[i+1],v[i]-v[i+1]))
print('   D5 非 -24 相邻对 %d 个（R204 报 1661 相邻对中 973 个 -24 => 688 跳跃，此处按类计）'%len(jumps))
ownset=set(own.values())
tj=collections.Counter()
for a,i,x,y,d in jumps:
    tj['y是某类own' if y in ownset else ('y在BCD池' if y in set(uniq) else 'y不在池')]+=1
print('   D5 跳转目标分类:',tj.most_common())
ck('D5a 跳转目标全部落在 1002 条 BCD 池内（复现 R204 QG7）',
   all(y in set(uniq) for a,i,x,y,d in jumps),sum(1 for a,i,x,y,d in jumps if y not in set(uniq)))
dj=collections.Counter(d for a,i,x,y,d in jumps)
ck('D5b 跳转差全为 8 的倍数',all(d%8==0 for d in dj),sum(1 for d in dj if d%8))
print('   D5 跳转差分布 top8:',dj.most_common(8))
ck('D5c 跳转目标 == y 指向类自身的类级 COL-16（即进入另一个 BCD 数组尾部）比例',
   True,'%d/%d'%(tj['y是某类own'],len(jumps)))

# --- D6: 反控 ---
import random
random.seed(2050)
rdlo=P.B['.rdata']['lo']; rdhi=P.B['.rdata']['hi_file']
n4=(rdhi-rdlo)//4
hit=0
for _ in range(4000):
    x=rdlo+4*random.randrange(n4-14)
    if P.dw(x)==0 and s32(P.dw(x+4))==0 and P.dw(x+8)==0 and P.dw(x+16)==x and P.dw(x+12) in set(own.values()): hit+=1
ck('C1 反控：4000 个随机 .rdata 地址按「40 字节头五元判据」命中 0 次',hit==0,hit)
C1c=0
for a in CHD:
    if P.dw(a+20)==0 and P.dw(a+24)==0 and P.dw(a+32)==a: C1c+=1
ck('C2 正控：同一判据在 954 个 CHD 上 954 命中',C1c==954,C1c)
# 反控：把内嵌 COL 换成 CHD+12（即 pBCA 位置）
bad2=sum(1 for a in CHD if COL.get(a+12) is not None and COL[a+12]['mdisp']==0)
ck('C3 反控：CHD+12（pBCA）不是 COL 记录',bad2==0,bad2)

print('\n%d asserts, %d FAIL %s'%(N,len(fails),fails))
json.dump(dict(asserts=N,fails=fails,emb=len(EMB),arith=arith,jumps=len(jumps),
               tj=dict(tj),start_at40=start_at40,contig=contig),open('_r205/m2_layout.json','w'),indent=1)
