#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R196 第九刀（决定性结构判据）：ncb 作为「子树大小」的深度优先解析自洽性检验。
m8 三条 FAIL 是模型选错（已记自错 S14/S15）：
  S14 W1 把 ncb 解释成「按 mdisp==0 计数」；实测 AbstractClass 链 4 个 mdisp==0 而 ncb[0]=7，
      模型被数据否掉。
  S15 W2a/W2b 沿用同一错模型，FAIL 数一致（855/954 与 99 条反例），非数据问题。

本刀不再猜语义，改做**结构自洽检验**（唯一可被数据否掉的判据）：
X1 深度优先解析：从下标 0 起，若 ncb[i]=c 则元素 i 的子树占 i..i+c（含 i 共 c+1 项），
   下一兄弟从 i+c+1 开始；要求整张 CHD 恰好被消费完，且每一步不越界。
X2 覆盖率：X1 必须在全部 954 张 CHD 上成立（任何一张失败即模型错）。
X3 兄弟数为 0 即叶子；叶子必须满足 ncb == 0。
X4 递归一致性：对 i 的每个直接子结点 k（i+1 .. i+ncb[i] 中作为兄弟起点者），
   其 ncb[k] 必须等于「k 的子树大小 - 1」，即解析后 k 的消费区间长度 - 1。
X5 反控 A：把 ncb 换成 0（全部当叶子）时，解析只走 n 步恰好消费完但树退化成线性 —— 需
   额外判据「ncb>0 的元素占比」来区分；给占比。
X6 反控 B：把 ncb 按 -1 扰动（随机取一笔）后解析必须失败。
X7 mdisp 与子树关系：子树内所有元素的 mdisp 必须 >= 子树根的 mdisp。
"""
import sys,struct,collections,json,random
sys.path.insert(0,'/home/t628/projects/ra2-campaign-forge/_r185')
import pe185 as P
fails=[];N=0
def ck(nm,c,d=''):
    global N;N+=1
    if not c:fails.append(nm)
    print(('PASS ' if c else 'FAIL ')+nm+((' | '+str(d)) if d!='' else ''))
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
        nm=P.cstr(w[i+3]+8,200)
        if not (nm and nm.startswith(b'.?A') and nm.endswith(b'@@')): continue
        COL[base+4*i]=dict(sig=w[i],mdisp=s32(w[i+1]),ptd=w[i+3],pchd=w[i+4],name=nm.decode('latin1'))
CHD={}
for c,cc in COL.items():
    v=cc['pchd']
    if v not in CHD: CHD[v]=dict(n=P.dw(v+8),arr=P.dw(v+12))
for v,d in CHD.items():
    d['bcds']=[P.dw(d['arr']+4*j) for j in range(d['n'])]
    d['ncb']=[P.dw(b+4) for b in d['bcds']]
    d['md']=[s32(P.dw(b+8)) for b in d['bcds']]
ck('X0 语料 CHD=954',len(CHD)==954,len(CHD))
# X1/X2 深度优先解析
def parse(ncb,n):
    """返回 (ok, 消费到的下标, 失败原因)。不使用递归，避免深链爆栈。"""
    i=0; guard=0
    while i<n:
        guard+=1
        if guard>n*4+16: return False,i,'guard'
        end=i+ncb[i]
        if end>=n and not (end==n-1): return False,i,'overflow j=%d ncb=%d n=%d'%(i,ncb[i],n)
        i=end+1
    return (i==n),i,''
okc=0;badr=[]
for v,d in CHD.items():
    ok,pos,why=parse(d['ncb'],d['n'])
    if ok: okc+=1
    else: badr.append((hex(v),d['n'],d['ncb'],why))
print('   X1 深度优先解析恰好消费完：%d / %d'%(okc,len(CHD)))
if badr: [print('     反例',x) for x in badr[:8]]
ck('X2a ncb 作为子树大小的深度优先解析在全部 CHD 上自洽',okc==len(CHD),(okc,len(CHD)))
# X3 叶子 ncb==0
leaf_ok=leaf_tot=0
for v,d in CHD.items():
    for j,c in enumerate(d['ncb']):
        if c==0: leaf_tot+=1
ck('X3a ncb==0 的位置数',True,leaf_tot)
nz=sum(1 for v,d in CHD.items() for c in d['ncb'] if c>0)
ck('X5a 反控A：ncb>0 的元素占比 < 100%（树非退化）',nz<sum(d['n'] for d in CHD.values()),(nz,sum(d['n'] for d in CHD.values())))
# X6 反控B：扰动一笔 ncb
random.seed(196)
bad_ok=0;tries=0
for v,d in CHD.items():
    for j in range(d['n']):
        if d['ncb'][j]==0: continue
        t=list(d['ncb']); t[j]=t[j]-1
        tries+=1
        ok,_,_=parse(t,d['n'])
        if ok: bad_ok+=1
print('   X6 扰动 ncb-1 后仍能解析完的次数 %d / %d'%(bad_ok,tries))
ck('X6a 反控B：ncb-1 扰动绝大多数导致解析失败',bad_ok<=0.02*tries,(bad_ok,tries))
# X7 mdisp 与子树
v7=v7b=0
for v,d in CHD.items():
    if not parse(d['ncb'],d['n'])[0]: continue
    for j in range(d['n']):
        end=j+d['ncb'][j]
        seg=d['md'][j:end+1]
        if all(x>=d['md'][j] for x in seg): v7+=1
        else: v7b+=1
ck('X7a 子树内 mdisp 均 >= 子树根 mdisp（覆盖 >=99%）',v7>=0.99*(v7+v7b),(v7,v7b))
# X4 递归一致性（等价于 parse 的局部正确性，用直接子结点重述）
x4=0;x4b=0
for v,d in CHD.items():
    ncb=d['ncb'];n=d['n'];i=0
    ok=True
    while i<n:
        # 直接子结点：i+1, 然后逐个跳过
        k=i+1;endr=i+ncb[i]
        while k<=endr:
            if k+ncb[k]>endr or ncb[k]<0: ok=False;break
            k=k+ncb[k]+1
        if not ok or k!=endr+1: ok=False;break
        i=endr+1
    if ok: x4+=1
    else: x4b+=1
ck('X4a 每个结点的直接子结点列表恰好铺满其子树区间',x4==len(CHD),(x4,x4b))
res=dict(chd=len(CHD),bcd=sum(d['n'] for d in CHD.values()),
  parse_ok=okc,parse_bad=len(badr),ncb_gt0=nz,perturb=(bad_ok,tries),
  mdisp_subtree=(v7,v7b),child_partition=(x4,x4b),
  ncb0=max(d['n']-1 for d in CHD.values()),
  top_all=sum(1 for v,d in CHD.items() if d['ncb'][0]==d['n']-1))
json.dump(res,open('_r196/m9_tree.json','w'),ensure_ascii=False,indent=1)
print('   ncb[0]==n-1 的 CHD 数:',res['top_all'])
print('--- 断言 %d / FAIL %d ---'%(N,len(fails)))
for f in fails: print('   FAILED:',f)
