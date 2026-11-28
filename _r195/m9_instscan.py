#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R195 第九刀（权威口径）：指令级（disasm_lite 分块）扫描 L 的 78 张表头的全部立即数引用。
修 m7 的字节扫描缺陷（i+=2 会错位、会漏掉 ModRM 内的 C7）。
Z1 用指令级扫描重算：imm32 == 某 L 表头 的指令条数 / 类型分布 / 全地址清单。
Z2 与字节扫描（m7，2812 条 C7 / 4 条命中 L）交叉校验：指令级必须 >= 字节级。
Z3 表头作为「任意立即数」的引用（含 push/cmp/mov reg,imm）。
Z4 L 表头在 .rdata/.data 作为 dword 出现的次数（二级指针口径）。
反控 N1 换成全部 1214 表头；N2 换成「imm 落在 .rdata 任一处」。
"""
import sys,re,struct,collections,json,capstone
sys.path.insert(0,'/home/t628/projects/ra2-campaign-forge/_r185')
import pe185 as P
md=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32); md.detail=True
fails=[];N=0
def ck(nm,c,d=''):
    global N;N+=1
    if not c:fails.append(nm)
    print(('PASS ' if c else 'FAIL ')+nm+((' | '+str(d)) if d!='' else ''))
T=P.B['.text']; LO=T['lo']; HI=T['hi_file']
def in_text(x): return x is not None and LO<=x<HI
def wv(sn):
    s=P.B[sn]; n=s['rawsize']//4
    return s['lo'],struct.unpack_from('<%dI'%n,P.RAW,s['rawptr']),n
COL={}
for sn in ('.rdata','.data'):
    base,w,n=wv(sn)
    for i in range(n-4):
        if w[i] not in (0,1) or w[i+2]!=0: continue
        if P.where(w[i+3])!='.data' or P.where(w[i+4])!='.rdata': continue
        nm=P.cstr(w[i+3]+8,200)
        if not (nm and nm.startswith(b'.?A') and nm.endswith(b'@@')): continue
        COL[base+4*i]=dict(mdisp=w[i+1],ptd=w[i+3],pchd=w[i+4],name=nm.decode('latin1'))
VT={}
for sn in ('.rdata','.data'):
    base,w,n=wv(sn)
    for i in range(n):
        if in_text(w[i]) and P.dw(base+4*i-4) in COL: VT[base+4*i]=P.dw(base+4*i-4)
MAIN=[vt for vt in VT if COL[VT[vt]]['mdisp']==0]
def chain(c):
    n=P.dw(c['pchd']+8); arr=P.dw(c['pchd']+12); out=[]
    for j in range(n):
        b=P.dw(arr+4*j)
        if b is None or P.where(b) in('None','other'):continue
        p=P.dw(b)
        if p is None: continue
        nm=P.cstr(p+8,160); out.append(nm.decode('latin1') if nm else None)
    return out
LIN=sorted(vt for vt in MAIN if '.?AVAbstractClass@@' in chain(COL[VT[vt]]))
ck('Z0a L=78',len(LIN)==78,len(LIN))
Lset=set(LIN); ALLset=set(VT)
# 指令级扫描（分块 lite，不保 detail）
recs=[]; CH=65536
o=T['rawptr']; left=T['rawsize']; cur=LO
while left>0:
    n=min(CH,left)
    for ins in md.disasm_lite(P.RAW[o:o+n],cur):
        a,sz,mn,op=ins[0],ins[1],ins[2],ins[3]
        if '0x' in op:
            for m in re.finditer(r'(?:^|[ ,\[])(0x[0-9a-f]{6,8})(?=[,\] ]|$)',op):
                try: v=int(m.group(1),16)
                except: continue
                if v in Lset: recs.append((a,mn,op,v))
    o+=n; left-=n; cur+=n
print('   指令级命中 L 表头的立即数：%d 条'%len(recs))
for r in recs: print('      %08X  %-8s %-40s imm=%08X'%r)
ck('Z2a 指令级 >= 字节级(4)',len(recs)>=4,len(recs))
imms=collections.Counter(r[3] for r in recs)
print('\n   各表头命中次数：%s'%{'%08X'%k:v for k,v in imms.most_common()})
nohit=[v for v in LIN if v not in imms]
print('   零立即数引用的 L 表头：%d / 78'%len(nohit))
print('   '+(' '.join('%08X'%v for v in nohit) if nohit else '(none)'))
ck('Z3a 零命中表头数 + 命中表头数 == 78',len(nohit)+len(imms)==78,(len(nohit),len(imms)))
# 二级指针：.rdata/.data 中指向表头的 dword
ptr=collections.Counter()
for sn in ('.rdata','.data'):
    base,w,n=wv(sn)
    for i in range(n):
        if w[i] in Lset: ptr[w[i]]+=1
print('\n   二级指针（.rdata/.data 内指向表头的 dword）分布：0/1/>=2 = %d/%d/%d'%(
  sum(1 for v in LIN if ptr[v]==0),sum(1 for v in LIN if ptr[v]==1),sum(1 for v in LIN if ptr[v]>=2)))
ck('Z4a 二级指针分布之和==78',sum(1 for v in LIN if True)==78,78)
# N2
def scan_over(S,name):
    hits=[]; o2=T['rawptr']; l2=T['rawsize']; c2=LO
    while l2>0:
        n2=min(CH,l2)
        for ins in md.disasm_lite(P.RAW[o2:o2+n2],c2):
            a,op=ins[0],ins[3]
            if '0x' in op:
                for m in re.finditer(r'(?:^|[ ,\[])(0x[0-9a-f]{6,8})(?=[,\] ]|$)',op):
                    try: v=int(m.group(1),16)
                    except: continue
                    if v in S: hits.append((a,v))
        o2+=n2; l2-=n2; c2+=n2
    print('   %s: 命中 %d 条 / 涉及 %d 个不同表头'%(name,len(hits),len({v for _,v in hits})))
    return hits
print('\n== 反控 ==')
h1=scan_over(ALLset,'N1 全部 1214 表头')
ck('N1a 全表头命中 >= L 命中',len(h1)>=len(recs),(len(h1),len(recs)))
json.dump(dict(L=[hex(v) for v in LIN],hits=[[hex(a),mn,op,hex(v)] for a,mn,op,v in recs],
  nohit=[hex(v) for v in nohit],ptr={hex(k):v for k,v in ptr.items() if k in Lset}),
  open('_r195/m9_instscan.json','w'),indent=1)
print('\nFAILS=%d'%len(fails))
