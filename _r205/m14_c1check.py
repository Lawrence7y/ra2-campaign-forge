#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R205 m14（§2.12 规则 D：审计/执行员结论必须主会话复算）：
逐条复算 R205_EXEC_X1 (#518) 的 C1 反控 132/5000 与 X2=891 两项分歧。
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
CHD=sorted(G); CHDSET=set(CHD)

# ---------- 复算 #518 的 X2 = 891（它的 vftable 判据） ----------
# 它说：遍历所有段中指向 .text 的 dword v，且 dw(v_addr-4) in COL
VTI_all=set()
for s in P.B.values():
    base,w,n=wv(s['name'])
    for i in range(n):
        if P.B['.text']['lo']<=w[i]<P.B['.text']['hi_file']:
            if P.dw(base+4*i-4) in COL: VTI_all.add(w[i])
ck('M1 #518 的 X2 口径复算 == 891',len(VTI_all)==891,len(VTI_all))
# 主会话口径：只遍历 .rdata/.data
VTI_ms=set()
for sn in ('.rdata','.data'):
    base,w,n=wv(sn)
    for i in range(n):
        if P.B['.text']['lo']<=w[i]<P.B['.text']['hi_file'] and P.dw(base+4*i-4) in COL:
            VTI_ms.add(w[i])
ck('M2 主会话口径（仅 .rdata/.data）== 1214',len(VTI_ms)==1214,len(VTI_ms))
diff=VTI_ms-VTI_all
ck('M3 差集 %d 个：都在被 #518 漏掉的段里'%len(diff),len(diff)==1214-891,len(diff))
bysec=collections.Counter()
for sn in ('.rdata','.data'):
    base,w,n=wv(sn)
    for i in range(n):
        v=w[i]
        if v in diff and P.dw(base+4*i-4) in COL: bysec[sn]+=1
ck('M4 差集来源段',True,dict(bysec))
# #518 漏的根因：它遍历含 .text 自身 -> .text 里的 dword 被当 vftable 起点（伪）
spurious=collections.Counter()
for s in P.B.values():
    if s['name'] in ('.rdata','.data'): continue
    base,w,n=wv(s['name'])
    for i in range(n):
        if P.B['.text']['lo']<=w[i]<P.B['.text']['hi_file'] and P.dw(base+4*i-4) in COL:
            spurious[s['name']]+=1
ck('M5 #518 多扫的段贡献 0 个（说明它不是多扫而是少扫）',sum(spurious.values())==0,dict(spurious))
# 找 323 个差集的真实来源
found=collections.Counter()
for sn in ('.rdata','.data'):
    base,w,n=wv(sn)
    for i in range(n):
        v=w[i]
        if v in diff and P.dw(base+4*i-4) in COL:
            found[(sn,i)]+=1
ck('M6 差集 %d 个在主会话口径内可见'%len(diff),len(found)==len(diff),len(found))

# ---------- 复算 #518 的 C1 = 132/5000（40 字节对齐随机采样） ----------
def five(x):
    return (P.dw(x)==0 and P.dw(x+20)==0 and P.dw(x+24)==0
            and P.where(P.dw(x+28))=='.data' and P.dw(x+32)==x)
rlo=P.B['.rdata']['lo']; rhi=P.B['.rdata']['hi_file']
r=random.Random(205)
fp=[]; n=0
while n<5000:
    x=rlo+40*r.randrange((rhi-rlo)//40)
    n+=1
    if five(x): fp.append(x)
print('   M7 40 字节对齐抽样 5000：命中 %d 个，其中真 CHD %d 个'%(len(fp),sum(1 for x in fp if x in CHDSET)))
ck('M7a #518 的 C1 命中 132 复算一致',len(fp)==132,len(fp))
ck('M7b 其命中**全部**是真 CHD（#518 把真值算进了假阳）',all(x in CHDSET for x in fp),
   len([x for x in fp if x not in CHDSET]))
ck('M7c 剔除真值后 C1 假阳为 0',len([x for x in fp if x not in CHDSET])==0,
   len([x for x in fp if x not in CHDSET]))
# 正确口径：任意 4 字节对齐抽样并剔除真值
r2=random.Random(206); fp2=[]; pool=0
while pool<20000:
    x=rlo+4*r2.randrange((rhi-rlo)//4-12); pool+=1
    if x in CHDSET: continue
    if five(x): fp2.append(x)
ck('M7d 正确口径（剔除真值、4 字节粒度、20000 池）假阳 0',len(fp2)==0,len(fp2))

# ---------- 复算 X8 的 956 vs 22 口径分歧 ----------
BCA={a:[P.dw(P.dw(a+12)+4*j) for j in range(P.dw(a+8))] for a in CHD}
uniq=sorted(set(b for v in BCA.values() for b in v))
m0=[b for b in uniq if s32(P.dw(b+8))==0]
def cname(b):
    t=P.cstr(P.dw(b)+8,400); return None if t is None else t.decode('latin1')
owntd=set(P.dw(a+28) for a in CHD)
byname_own=set(COL[a+16]['name'] for a in CHD)
p_in=sum(1 for b in m0 if P.dw(b) in owntd)
n_in=sum(1 for b in m0 if cname(b) in byname_own)
print('   M8 978 = 指针口径自有 %d + 非自有 %d ；名字口径自有 %d + 非自有 %d'%(
    p_in,978-p_in,n_in,978-n_in))
ck('M8a 指针口径 956/22（主会话口径）',(p_in,978-p_in)==(956,22),(p_in,978-p_in))
ck('M8b 名字口径 958/20（#518 提到的另一种口径）',(n_in,978-n_in)==(958,20),(n_in,978-n_in))
# 两者差 2 源：两个 TD 被 2 条 BCD 共享
d=collections.Counter(P.dw(b) for b in m0)
dup=[td for td,n2 in d.items() if n2>1]
ck('M8c 差 2 的来源：%d 个 TD 各有 2 条 mdisp==0 记录'%len(dup),len(dup)==2,
   [(cname([b for b in m0 if P.dw(b)==td][0]),d[td]) for td in dup])
print('\n%d asserts, %d FAIL %s'%(N,len(fails),fails))
json.dump(dict(asserts=N,fails=fails,x2_518=len(VTI_all),x2_ms=len(VTI_ms),diff=len(diff),
               c1_518=len(fp),c1_true=sum(1 for x in fp if x in CHDSET),
               c1_fp=len([x for x in fp if x not in CHDSET]),
               p_in=p_in,n_in=n_in,dup=len(dup)),open('_r205/m14_c1check.json','w'),indent=1)
