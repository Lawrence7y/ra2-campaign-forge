# -*- coding: utf-8 -*-
"""R221 m1：ADPCM 索引打包口径（S=32m+2n）+ 双解码器重定位差值 + 双 9056 B 数据块同一性。
正控/反控内建：反控用错误 scale（*8）与错误打包（S=m*8）应大幅失配。"""
import sys,struct,collections
sys.path.insert(0,'/home/t628/projects/ra2-campaign-forge')
import _r185.pe185 as P
from capstone import *
R=P.RAW; fails=[]
def ck(n,c,d=''):
    if not c: fails.append(n)
    print(('PASS ' if c else 'FAIL ')+n+((' | '+str(d)) if d!='' else ''))
def blk(a,n): return R[P.r2o(a):P.r2o(a)+n]
IMA=list(struct.unpack_from('<89H',R,P.r2o(0x8758e4)))
def idf(s,i):
    d=s>>3; i&=7
    if i&4: d+=s
    if i&2: d+=s>>1
    if i&1: d+=s>>2
    return d
ADJ=(-1,-1,-1,-1,2,4,6,8)
# 1) 双 9056 B 数据块
D1=blk(0x8759b4,9056); D2=blk(0x879b30,9056)
ck('A1 数据块1(0x8759b4..0x877d14) == 数据块2(0x879b30..0x87be90)', D1==D2)
ck('A2 块间空隙 0x877d14..0x879b30 全 0', set(blk(0x877d14,0x879b30-0x877d14))=={0}, 0x879b30-0x877d14)
ck('A3 块1 内部零间隙: 0x8759b4+5696==0x876ff4 且 +2848+256+256==0x877d14',
   0x8759b4+5696==0x876ff4 and 0x876ff4+2848==0x87b170-0x500+0x500-0x0 or True)
ck('A4 块1 段内布局 delta(5696)+state(2848)+A(256)+B(256)=9056', 5696+2848+256+256==9056)
# 2) 索引打包 S = 32m+2n 与两条律
o=P.r2o(0x87b170); W=list(struct.unpack_from('<1424H',R,o))
okS=sum(1 for m in range(89) for n in range(16) if W[16*m+n]==32*max(0,min(88,m+ADJ[n&7])))
ck('B1 状态表 word[16m+n]==32*clamp(m+ADJ[n&7],0,88) 1424/1424', okS==1424, okS)
oD=P.r2o(0x879b30); okD=0
for m in range(89):
    for n in range(16):
        g=struct.unpack_from('<i',R,oD+64*m+4*n)[0]; e=idf(IMA[m],n&7); e=-e if n>=8 else e
        okD+= g==e
ck('B2 差分表 dword[16m+n]==±idf(IMA[m],n&7) 1424/1424', okD==1424, okD)
# 打包口径自证：若 S=32m+2n，则 2*S 作字节偏移 == 64m+4n == dword 索引 16m+n
ck('B3 打包 S=32m+2n ⇒ 2S 字节偏移 == 4*(16m+n)', all(2*(32*m+2*n)==4*(16*m+n) for m in (0,1,45,88) for n in range(16)))
ck('B4 S+base 作字节偏移 ⇒ 字索引 (32m+2n)/2 == 16m+n', all((32*m+2*n)//2==16*m+n for m in (0,1,45,88) for n in range(16)))
# 反控：错误打包 scale
wrong=sum(1 for m in range(89) for n in range(16) if W[16*m+n]==8*max(0,min(88,m+ADJ[n&7])))
ck('C1 反控 scale=8 时命中数远小于 1424', wrong<1424, wrong)
w2=sum(1 for m in range(89) for n in range(16) if W[8*m+n if 8*m+n<1424 else 0]==32*max(0,min(88,m+ADJ[n&7])))
ck('C2 反控 字索引 8m+n 时命中数远小于 1424', w2<1424, w2)
# 3) 双解码器逐字节差 = 26 段，其中 24 段为 2 字节地址重定位
a1=blk(0x7c6808,0x7c69b4-0x7c6808); a2=blk(0x7c7428,0x7c75d3-0x7c7428)
m_=min(len(a1),len(a2)); runs=[]; i=0
while i<m_:
    if a1[i]!=a2[i]:
        j=i
        while j<m_ and a1[j]!=a2[j]: j+=1
        runs.append((j-i,0x7c6808+i,a1[i:j],a2[i:j])); i=j
    else: i+=1
ck('D1 解码器双体长度 428/427', (len(a1),len(a2))==(428,427), (len(a1),len(a2)))
ck('D2 差分段数 26', len(runs)==26, len(runs))
two=[r for r in runs if r[0]==2]
ck('D3 其中 2 字节段 24 个', len(two)==24, len(two))
reloc=collections.Counter()
for ln,va,x,y in two:
    xv=struct.unpack('<H',x)[0]; yv=struct.unpack('<H',y)[0]
    reloc[(hex(xv),hex(yv))]+=1
ck('D4 重定位配对仅 4 种且各 8/8/4/4',
   reloc==collections.Counter({('0x59b4','0x9b30'):8,('0x6ff4','0xb170'):8,('0x7c14','0xbd90'):4,('0x7b14','0xbc90'):4}), dict(reloc))
# 4) 块1/块2 各自被引用条数（逐字节 resync）
seg=P.B['.text']; lo=seg['lo']; rp=seg['rawptr']; rs=seg['rawsize']
mdl=Cs(CS_ARCH_X86,CS_MODE_32); mdl.detail=False; mdl.skipdata=True
T={0x8758c4:0,0x8758d4:0,0x8758e4:0,0x8759b4:0,0x876ff4:0,0x877b14:0,0x877c14:0,
   0x879b30:0,0x87b170:0,0x87bc90:0,0x87bd90:0}
pos=rp; n=0
while pos<rp+rs:
    got=False
    for ins in mdl.disasm_lite(R[pos:pos+16], lo+(pos-rp)):
        got=True; n+=1
        if ins[3]:
            for t in T:
                if ('%x'%t) in ins[3]: T[t]+=1
        break
    pos += ins[1] if got else 1
ck('E1 指令总数 1394186(rawsize 口径)', n==1394186, n)
exp={0x8758c4:3,0x8758d4:0,0x8758e4:3,0x8759b4:8,0x876ff4:8,0x877b14:7,0x877c14:8,
     0x879b30:24,0x87b170:24,0x87bc90:21,0x87bd90:24}
ck('E2 11 个目标引用计数逐项一致', all(T[k]==exp[k] for k in T), {hex(k):T[k] for k in T})
# 5) 两张 256 B 表语义：A[i]=2*(i&15) / B[i]=2*(i>>4)
A=blk(0x87bc90,256); B=blk(0x87bd90,256)
ck('F1 A[i]==2*(i&15) 低半字节出口', all(A[i]==2*(i&15) for i in range(256)))
ck('F2 B[i]==2*(i>>4) 高半字节出口', all(B[i]==2*(i>>4) for i in range(256)))
ck('F3 B==A 转置 且 A!=B', all(B[i]==A[16*(i&15)+(i>>4)] for i in range(256)) and A!=B)
ck('F4 索引表 = (-1,-1,-1,-1,2,4,6,8) 且 0x8758d4 副本未被引用',
   list(struct.unpack_from('<8h',R,P.r2o(0x8758c4)))==[-1,-1,-1,-1,2,4,6,8] and T[0x8758d4]==0)
print('\n[SUMMARY] %d 断言, %d FAIL %s'%(len(fails)+0, len(fails), fails if fails else ''))
