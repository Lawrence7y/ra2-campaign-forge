# -*- coding: utf-8 -*-
"""R221 m2：终稿正反控（ADPCM packed 索引 S=32m|2n 三表互锁 + 双解码器重定位 + 双 9056B 数据块）。
全部数字实测；FAIL 非 0 则不得落盘。"""
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
IDX=list(struct.unpack_from('<8h',R,P.r2o(0x8758c4)))
ADJ=list(IDX)  # (-1,-1,-1,-1,2,4,6,8) 完整 8 项
def shiftform(s,i):      # IMA 标准反量化（逐项右移）
    d=s>>3; i&=7
    if i&4: d+=s
    if i&2: d+=s>>1
    if i&1: d+=s>>2
    return d
def floorform(s,i):      # R220 用的口径（整体乘除）
    return (s*(2*(i&7)+1))//8
# ---------- 1. 索引表与 IMA 表 ----------
ck('A1 索引表 0x8758c4 = (-1,-1,-1,-1,2,4,6,8)', IDX==[-1,-1,-1,-1,2,4,6,8], IDX)
ck('A2 步长表 0x8758e4 = 标准 IMA 89 项（首 7 末 32767，严格递增）',
   IMA[0]==7 and IMA[-1]==32767 and all(IMA[i]<IMA[i+1] for i in range(88)))
# ---------- 2. 差分表律：移位式 vs floor 式 ----------
oD=P.r2o(0x879b30)
def cnt_delta(f):
    k=0
    for m in range(89):
        for n in range(16):
            g=struct.unpack_from('<i',R,oD+64*m+4*n)[0]
            e=f(IMA[m],n&7); e=-e if n>=8 else e
            k+= g==e
    return k
ck('B1 移位式律 D 命中 1424/1424（R220 的「余 22 块未解」= 口径错）', cnt_delta(shiftform)==1424, cnt_delta(shiftform))
ck('B2 floor 式律 D 只命中 1020/1424（R220 记 44/89 块精确）', cnt_delta(floorform)==1020, cnt_delta(floorform))
exact=sum(1 for m in range(89) if all(floorform(IMA[m],n)==shiftform(IMA[m],n) for n in range(8)))
ck('B3 floor 式精确块数 44/89（与 R220 的 44 一致）', exact==44, exact)
# 代数证明：floor(s(2a+1)/8) == (s>>3)+[a&4]s+[a&2](s>>1)+[a&1](s>>2)  <=>  s%8 in {0,1,2,4}
def exact_by_residue(s):
    # 设 s=8q+r。q 部恒等（2a+1 = 1 + 8[a>=4] + 4[bit1] + 2[bit0]），
    # 故 floor(s(2a+1)/8) == shiftform  <=>  floor(r(2a+1)/8) == [a>=4]*r + [(a>>1)&1]*(r>>1) + [a&1]*(r>>2)
    r=s%8
    for a in range(8):
        rhs=(1 if a&4 else 0)*r + (1 if a&2 else 0)*(r>>1) + (1 if a&1 else 0)*(r>>2)
        if (r*(2*a+1))//8 != rhs: return False
    return True
ck('B4 精确块判据 = s%8∈{0,1,2,4}（代数式，non-空证明：r=3 时 a=1 即失配）',
   all((all(floorform(IMA[m],n)==shiftform(IMA[m],n) for n in range(8)))==exact_by_residue(IMA[m]) for m in range(89))
   and exact_by_residue(8) and not exact_by_residue(3))
ck('B5 失配 residue 计数 3:11 5:10 6:13 7:11 共 45 块 = 89-44',
   [sum(1 for m in range(89) if IMA[m]%8==r) for r in (3,5,6,7)]==[11,10,13,11])
# ---------- 3. 状态表律 ----------
oW=P.r2o(0x87b170)
W=list(struct.unpack_from('<1424H',R,oW))
law=lambda m,n: 32*max(0,min(88,m+ADJ[n&7]))
ck('C1 状态表 word[16m+n]==32*clamp(m+ADJ[n&7],0,88) 1424/1424',
   all(W[16*m+n]==law(m,n) for m in range(89) for n in range(16)))
ck('C2 状态表 min/max/全 32 倍数', (min(W),max(W),all(w%32==0 for w in W))==(0,2816,True), (min(W),max(W)))
ck('C3 钳下界项数 = 8（仅 m=0 且 n&7∈0..3 即 n∈{0,1,2,3,8,9,10,11}）',
   sum(1 for m in range(89) for n in range(16) if m+ADJ[n&7]<0)==8
   and sum(1 for n in range(16) if 0+ADJ[n&7]<0)==8)
# ---------- 4. packed 索引 S=32m|2n 的自证 ----------
ck('D1 32m|2n == 32m+2n 对 m<89,n<16 恒成立（OR 拼接无进位冲突）',
   all((32*m)|(2*n)==32*m+2*n for m in range(89) for n in range(16)))
ck('D2 反控：33m|2n 会进位冲突（证明 32 这个乘数是结构性必需）',
   any((33*m)|(2*n)!=33*m+2*n for m in range(89) for n in range(16)))
ck('D3 字节偏移 S 用于 word 表 ⇒ 字索引 16m+n', all((32*m+2*n)//2==16*m+n for m in range(89) for n in range(16)))
ck('D4 字节偏移 2S 用于 dword 表 ⇒ dword 索引 16m+n', all((2*(32*m+2*n))//4==16*m+n for m in range(89) for n in range(16)))
ck('D5 状态表值 32m 的低 5 位恒 0（or dl 写入 2n 不冲突）', all((32*m)&31==0 for m in range(89)))
ck('D6 2n 占 bits1..4 且 n<=15（or 后回读唯一）', all((2*n)<=30 and (2*n)&1==0 for n in range(16)))
# ---------- 5. 双 9056 B 数据块 ----------
ck('E1 数据块1(0x8759b4..0x877d14) == 数据块2(0x879b30..0x87be90) 各 9056 B', blk(0x8759b4,9056)==blk(0x879b30,9056))
ck('E2 块间空隙 0x877d14..0x879b30 = 7708 B 全 0x00', set(blk(0x877d14,7708))=={0})
ck('E3 块内布局 D(5696)+S(2848)+A(256)+B(256) = 9056 且四段零间隙',
   5696+2848+256+256==9056 and 0x8759b4+5696==0x876ff4 and 0x876ff4+2848==0x877b14 and 0x877b14+256==0x877c14)
ck('E4 块1 的 A/B 与块2 的 0x87bc90/0x87bd90 逐字节相同',
   blk(0x877b14,256)==blk(0x87bc90,256) and blk(0x877c14,256)==blk(0x87bd90,256))
# ---------- 6. 双解码器 ----------
a1=blk(0x7c6808,0x7c69b4-0x7c6808); a2=blk(0x7c7428,0x7c75d3-0x7c7428)
m_=min(len(a1),len(a2)); runs=[]; i=0
while i<m_:
    if a1[i]!=a2[i]:
        j=i
        while j<m_ and a1[j]!=a2[j]: j+=1
        runs.append((j-i,0x7c6808+i,a1[i:j],a2[i:j])); i=j
    else: i+=1
r2=[r for r in runs if r[0]==2]
rel=collections.Counter((hex(struct.unpack('<H',r[2])[0]),hex(struct.unpack('<H',r[3])[0])) for r in r2)
ck('F1 双解码器长度 428 / 427 B', (len(a1),len(a2))==(428,427), (len(a1),len(a2)))
ck('F2 差分段 26 个：2 字节段 25 个 + 15 字节段 1 个',
   len(runs)==26 and len(r2)==25 and sum(1 for r in runs if r[0]==15)==1, (len(runs),len(r2)))
ck('F3 25 个 2 字节段 = 4 组表地址重定位 8/8/4/4 + 1 个跳转表地址',
   rel==collections.Counter({('0x59b4','0x9b30'):8,('0x6ff4','0xb170'):8,('0x7c14','0xbd90'):4,
                             ('0x7b14','0xbc90'):4,('0x6b38','0x7758'):1}), dict(rel))
ck('F4 跳转表成对偏移 == 函数体偏移 0xc20', 0x7c7758-0x7c6b38==0xc20==0x7c7428-0x7c6808)
ck('F5 两跳转表内容逐项差 0xc20', all(struct.unpack_from('<I',R,P.r2o(0x7c7758)+4*k)[0]
   -struct.unpack_from('<I',R,P.r2o(0x7c6b38)+4*k)[0]==0xc20 for k in range(8)))
# ---------- 7. 引用计数 ----------
seg=P.B['.text']; lo=seg['lo']; rp=seg['rawptr']; rs=seg['rawsize']
mdl=Cs(CS_ARCH_X86,CS_MODE_32); mdl.detail=False; mdl.skipdata=True
exp={0x8758c4:3,0x8758d4:0,0x8758e4:3,0x8759b4:8,0x876ff4:8,0x877b14:7,0x877c14:8,
     0x879b30:24,0x87b170:24,0x87bc90:21,0x87bd90:24}
T=dict.fromkeys(exp,0); pos=rp; n=0
while pos<rp+rs:
    got=False
    for ins in mdl.disasm_lite(R[pos:pos+16], lo+(pos-rp)):
        got=True; n+=1
        if ins[3]:
            for t in T:
                if ('%x'%t) in ins[3]: T[t]+=1
        break
    pos += ins[1] if got else 1
ck('G1 指令总数 1,394,186（rawsize 口径）', n==1394186, n)
ck('G2 11 个目标引用计数逐项一致', T==exp, {hex(k):T[k] for k in T})
ck('G3 块1 差分表被引用 8 条（R220 只记了块2 的 24 条；卡面 R221-A 第 9 项的「0」是主会话笔误）', T[0x8759b4]==8, T[0x8759b4])
# ---------- 8. 抖动表索引语义 ----------
A=blk(0x87bc90,256); B=blk(0x87bd90,256)
ck('H1 A[i]==2*(i&15)（低半字节出口）', all(A[i]==2*(i&15) for i in range(256)))
ck('H2 B[i]==2*(i>>4)（高半字节出口）', all(B[i]==2*(i>>4) for i in range(256)))
ck('H3 B==A 转置 且 A!=B 且逐项差 240 项', all(B[16*(i&15)+(i>>4)]==A[i] for i in range(256))
   and A!=B and sum(1 for i in range(256) if A[i]!=B[i])==240)
# ---------- 9. 反控（有意义的近邻变体） ----------
ck('I1 反控 状态表律倍数 32→8 命中 <1424', sum(1 for m in range(89) for n in range(16) if W[16*m+n]==8*law(m,n)//32)<1424)
ck('I2 反控 状态表基址右移 2 命中 564/1424',
   sum(1 for m in range(89) for n in range(16) if struct.unpack_from('<H',R,oW+2+2*(16*m+n))[0]==law(m,n))==564)
ck('I3 反控 状态表 clamp 上界 88→87 命中 1376',
   sum(1 for m in range(89) for n in range(16) if W[16*m+n]==32*max(0,min(87,m+ADJ[n&7])))==1376)
ck('I4 反控 差分表符号改按 n&7>=4 判 命中 713/1424',
   sum(1 for m in range(89) for n in range(16)
       if struct.unpack_from('<i',R,oD+64*m+4*n)[0]==(-1 if (n&7)>=4 else 1)*shiftform(IMA[m],n&7))==713)
ck('I5 反控 差分表符号阈值 n>=7 命中 1335/1424', cnt_delta(lambda s,i:(shiftform(s,i)))==1424 and
   sum(1 for m in range(89) for n in range(16)
       if struct.unpack_from('<i',R,oD+64*m+4*n)[0]==(-1 if n>=7 else 1)*shiftform(IMA[m],n&7))==1335)
print('\n[SUMMARY] %d FAIL %s'%(len(fails), fails if fails else ''))
sys.exit(1 if fails else 0)
