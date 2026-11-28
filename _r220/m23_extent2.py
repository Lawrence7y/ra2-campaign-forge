# -*- coding: utf-8 -*-
"""R220 m23：定 162 记录表真实跨度（R219 的 2576 B 是切片）+ 双副本完整比较。"""
import sys,struct,hashlib,json
sys.path.insert(0,'/home/t628/projects/ra2-campaign-forge')
import _r185.pe185 as P
R=P.RAW
fails=[]
def ck(n,c,d=''):
    if not c: fails.append(n)
    print(('PASS ' if c else 'FAIL ')+n+((' | '+str(d)) if d!='' else ''))
def recs(va,limit=400):
    o=P.r2o(va); out=[]
    for i in range(limit):
        r=list(struct.unpack_from('<8H',R,o+i*16))
        out.append(r)
    return out
A,B_=0x876ff4,0x87b170
rA,rB=recs(A),recs(B_)
# 有效记录判据: w0==w1==w2==w3 且 (w4,w5,w6,w7) 是固定两型之一
okA=[]; 
for i,r in enumerate(rA):
    d=tuple(r[j]-r[0] for j in range(8))
    good = d[:4]==(0,0,0,0) and d[4:] in ((64,128,192,256),(96,160,224,288))
    if not good: break
    okA.append((i,r[0],d[4:]))
okB=[]
for i,r in enumerate(rB):
    d=tuple(r[j]-r[0] for j in range(8))
    good = d[:4]==(0,0,0,0) and d[4:] in ((64,128,192,256),(96,160,224,288))
    if not good: break
    okB.append((i,r[0],d[4:]))
print("valid records A=%d  B=%d"%(len(okA),len(okB)))
print("A tail:",okA[-3:])
print("B tail:",okB[-3:])
print("first 6 a:",[x[1] for x in okB[:6]])
print("delta pattern counts B:", {k:sum(1 for x in okB if x[2]==k) for k in set(x[2] for x in okB)})
ck('X1 两份副本有效记录数相同且 == 162', len(okA)==len(okB)==162, (len(okA),len(okB)))
ck('X2 总字节 == 162*16 == 2592（R219 的 2576 是 161 记录的截断）', len(okB)*16==2592)
hA=hashlib.sha256(R[P.r2o(A):P.r2o(A)+2592]).hexdigest()
hB=hashlib.sha256(R[P.r2o(B_):P.r2o(B_)+2592]).hexdigest()
ck('X3 2592 B 完整 sha256 两份相同', hA==hB, (hA[:16],hB[:16]))
ck('X4 2592 B 逐字节相同', R[P.r2o(A):P.r2o(A)+2592]==R[P.r2o(B_):P.r2o(B_)+2592])
print("sha256(2592) =",hB)
print("after 2592 A:",R[P.r2o(A)+2592:P.r2o(A)+2624].hex())
print("after 2592 B:",R[P.r2o(B_)+2592:P.r2o(B_)+2624].hex())
# a 序列规律: 前 4 条 a=0，之后 32k 各两条?
seq=[x[1] for x in okB]
ck('X5 a 序列前 4 条为 0', seq[:4]==[0,0,0,0], seq[:6])
pair_ok = all(seq[i]==seq[i+1] for i in range(4,len(seq),2)) if len(seq)%2==0 else False
ck('X6 第 4 条起每两条同值', pair_ok, seq[4:12])
ck('X7 a 取值集合 == {0} ∪ {32k, k=1..79}', set(seq)==set([0])|set(32*k for k in range(1,80)), len(set(seq)))
ck('X8 max 16 位字 == 2816', max(max(r[1]) for r in [(0,x[0],x[2]) for x in okB])==2528 and True, max(x[1]+288 for x in okB))
vm=0
for i in range(162):
    vm=max(vm,max(struct.unpack_from('<8H',R,P.r2o(B_)+i*16)))
ck('X8b 全 162 记录 max word == 2816', vm==2816, vm)
ck('X9 幻影地址 0x877000/0x877010/0x87b17c/0x87b18c 回落到该表内',
   all(A<=v<A+2592 or B_<=v<B_+2592 for v in (0x877000,0x877010,0x87b17c,0x87b18c)),
   [(hex(v), 'A' if A<=v<A+2592 else ('B' if B_<=v<B_+2592 else '?')) for v in (0x877000,0x877010,0x87b17c,0x87b18c)])
json.dump({'nrec':162,'bytes':2592,'sha2592':hB,'seq_a':seq,'fails':fails},open('_r220/m23.json','w'),indent=1)
print('TOTAL FAILS:',len(fails),fails)
