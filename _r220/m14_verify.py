# -*- coding: utf-8 -*-
"""R220 m14：主会话独立复算（不复用子代理代码），全部断言 fail-closed。"""
import sys,struct,hashlib,json
from collections import Counter,defaultdict
sys.path.insert(0,'/home/t628/projects/ra2-campaign-forge')
import _r185.pe185 as P
from capstone import Cs,CS_ARCH_X86,CS_MODE_32
R=P.RAW; seg=P.B['.text']; lo=seg['lo']; rp=seg['rawptr']; rs=seg['rawsize']
fails=[]; res={}
def ck(n,c,d=''):
    if not c: fails.append(n)
    print(('PASS ' if c else 'FAIL ')+n+((' | '+str(d)) if d!='' else ''))

IMA=[7,8,9,10,11,12,13,14,16,17,19,21,23,25,28,31,34,37,41,45,50,55,60,66,73,80,88,97,107,118,130,143,157,173,190,209,230,253,279,307,337,371,408,449,494,544,598,658,724,796,876,963,1060,1166,1282,1411,1552,1707,1878,2066,2272,2499,2749,3024,3327,3660,4026,4428,4871,5358,5894,6484,7132,7845,8630,9493,10442,11487,12635,13899,15289,16818,18500,20350,22385,24623,27086,29794,32767]
ck('V1 IMA 表 89 项逐项相同', list(struct.unpack_from('<89H',R,P.r2o(0x8758e4)))==IMA)
ck('V1b IMA 表落 .data 且 0x8758e4 是 .text 引用目标', P.where(0x8758e4)=='.data')

# 双副本
ck('V2 双副本 2576B 逐字节相同', R[P.r2o(0x876ff4):P.r2o(0x876ff4)+2576]==R[P.r2o(0x87b170):P.r2o(0x87b170)+2576])
h=hashlib.sha256(R[P.r2o(0x87b170):P.r2o(0x87b170)+2576]).hexdigest()
ck('V2b sha256 前缀 7b724b01', h.startswith('7b724b01'), h[:16])

# 记录表结构
o=P.r2o(0x87b170); w=list(struct.unpack_from('<1288H',R,o))
recs=[w[i*8:(i+1)*8] for i in range(161)]
pat=[r for r in recs if all(r[j]==r[0] for j in range(4)) and r[4]==r[0]+64 and r[5]==r[0]+128 and r[6]==r[0]+192 and r[7]==r[0]+256]
ck('V3 161 条记录全部符合 [a,a,a,a,a+64,a+128,a+192,a+256]', len(pat)==161, len(pat))
a=Counter(r[0] for r in pat)
ck('V4 a 取值=a*32 序列(0 x4, 32k x2)', sorted(set(a.values()))==[2,4] and a[0]==4 and all(set(a.keys())<=set([32*k for k in range(80)])))
ck('V5 max word == 2816', max(w)==2816, max(w))
ck('V5b 全表 word 全为 32 的倍数', all(x%32==0 for x in w))
ck('V5c 表尾后 16B == e009 x4 + 400a 800a c00a 000b', R[P.r2o(0x87b170)+2576:P.r2o(0x87b170)+2592].hex()=='e009e009e009e009400a800ac00a000b')

# delta/DCT 表
o2=P.r2o(0x879b30); vals=struct.unpack_from('<2000i',R,o2)
ok=0
for b in range(125):
    blk=vals[b*16:(b+1)*16]; asc=blk[:8]; neg=blk[8:]
    if all(neg[i]==-asc[i] for i in range(8)) and all(asc[i]<asc[i+1] for i in range(7)): ok+=1
ck('V6 前 89 块(16 dword)[升序8 + 相反数8] 成立，第 90 块起不成立', ok==89, ok)
ck('V6b 第 90 块(索引89)首值 == 0 且非严格升序', vals[89*16]==0 and not all(vals[89*16+i]<vals[89*16+i+1] for i in range(7)))

# dither 表
o3=P.r2o(0x87bd90)
ck('V7 0x87bd90 起 256B = 16x16 第 r 行全 2r', all(R[o3+r*16+c]==2*r for r in range(16) for c in range(16)))
ck('V7b 第 256 字节起 != 2*16', R[o3+256]!=32)

# ---- 全段 resync sweep（一次）----
mdl=Cs(CS_ARCH_X86,CS_MODE_32); mdl.detail=False; mdl.skipdata=True
md=Cs(CS_ARCH_X86,CS_MODE_32); md.detail=True; md.skipdata=True
pos=rp; n=0; last=0
cand=[]
while pos<rp+rs:
    got=False
    for ins in mdl.disasm_lite(R[pos:pos+16], lo+(pos-rp)):
        got=True; n+=1; last=ins[0]
        if ins[2] in ('mov','call','jmp','cmp','fmul','fstp','lea','add','or','test','and'): cand.append((ins[0],ins[2],ins[3]))
        break
    pos += ins[1] if got else 1
ck('V8 sweep 指令数 == 1394186', n==1394186, n)
ck('V8b 末指令地址 == 0x7e0ffd', hex(last)=='0x7e0ffd', hex(last))

# 表引用计数
tabs={0x8758e4:'IMA',0x87b170:'TAB',0x876ff4:'TAB2',0x879b30:'DELTA',0x87bd90:'DITH',0x87c484:'DISP'}
cnt=Counter(); forms=defaultdict(Counter)
for a_,mn,op in cand:
    for t,nm in tabs.items():
        if ('%x'%t) in op:
            cnt[nm]+=1; forms[nm][op.replace(hex(t),'T')[:28]]+=1
ck('V9 0x87b170 引用 24 条', cnt['TAB']==24, cnt['TAB'])
ck('V9b 0x876ff4 引用 8 条', cnt['TAB2']==8, cnt['TAB2'])
ck('V9c 0x879b30 引用 24 条且全为 [edx*2+..]', cnt['DELTA']==24 and all('[edx*2' in f for f in forms['DELTA']), (cnt['DELTA'],dict(forms['DELTA'])))
ck('V9d 0x87bd90 引用 24 条', cnt['DITH']==24, cnt['DITH'])
ck('V9e 0x87c484 引用 16 条', cnt['DISP']==16, cnt['DISP'])
ck('V9f IMA 表 .text 引用 3 条', cnt['IMA']==3, cnt['IMA'])

# 四 offset 口径
OFFS=[0x77c,0x780,0x784,0x788,0x7a4,0x778,0x78c]
C=defaultdict(lambda: defaultdict(int)); W=defaultdict(list)
for a_,mn,op in cand:
    o_=P.r2o(a_)
    for i in md.disasm(R[o_:o_+16], a_):
        if i.mnemonic!=mn: break
        for oper in i.operands:
            if oper.type==3 and oper.mem.disp in OFFS and oper.mem.base!=0 and oper.mem.index==0:
                off=oper.mem.disp
                k='other_'+i.mnemonic
                if i.mnemonic=='mov' and len(i.operands)==2:
                    if i.operands[0].type==3 and i.operands[1].type==2:
                        k='write_imm'; W[off].append((a_,i.op_str))
                    elif i.operands[0].type==3: k='write_reg'
                    elif i.operands[0].type==2: k='read_reg'
                    else: k='read'
                elif i.mnemonic=='call': k='call_ind'
                elif i.mnemonic=='jmp': k='jmp_ind'
                C[off][k]+=1
        break
def texthits(off):
    out=[]
    for a_,ops in W[off]:
        t=ops.split(', ')[-1]
        if t.startswith('0x') and 0x401000<=int(t,16)<0x801000: out.append((a_,t))
    return out
c3=sum(C[o_]['call_ind']+C[o_]['read']+C[o_]['read_reg']+C[o_]['write_imm']+C[o_]['write_reg']+C[o_].get('other_fmul',0)+C[o_].get('other_fstp',0) for o_ in (0x77c,0x780,0x784))
ck('V10 三 offset 指令引用合计 30（9/9/12）', c3==30, {hex(o_):sum(C[o_].values()) for o_ in (0x77c,0x780,0x784)})
imm3=[x for o_ in (0x77c,0x780,0x784) for x in texthits(o_)]
imm4=[x for o_ in (0x77c,0x780,0x784,0x788) for x in texthits(o_)]
ck('V10b 三 offset imm32->.text 写入 12 条（2/3/7）', len(imm3)==12, [len(texthits(o_)) for o_ in (0x77c,0x780,0x784)])
ck('V10c 含 0x788 则 imm32->.text 写入 21 条（2/3/7/9）', len(imm4)==21, [len(texthits(o_)) for o_ in (0x77c,0x780,0x784,0x788)])
ck('V11 负控 0x7a4 字段访问 15 条(非 0)', sum(C[0x7a4].values())==15, dict(C[0x7a4]))
ck('V11b 0x778 = 19, 0x78c = 32', sum(C[0x778].values())==19 and sum(C[0x78c].values())==32, (sum(C[0x778].values()),sum(C[0x78c].values())))
ck('V11c 0x7a4 的 imm32->.text 写入 0 条', len(texthits(0x7a4))==0, texthits(0x7a4))

# E8 站点
def e8sites(targets):
    hits=defaultdict(list); pos=rp
    while pos<rp+rs:
        got=False
        for ins in mdl.disasm_lite(R[pos:pos+16], lo+(pos-rp)):
            got=True
            if ins[2]=='call':
                try: t=int(ins[3],16)
                except: t=None
                if t in targets: hits[t].append(ins[0])
            break
        pos += ins[1] if got else 1
    return hits
e=e8sites({0x7c7371,0x7c7350})
ck('V12 0x7c7371 E8 站点 2 处', len(e[0x7c7371])==2, [hex(x) for x in e[0x7c7371]])
ck('V12b 站点地址 == 0x7c24a2/0x7c2557', sorted(e[0x7c7371])==[0x7c24a2,0x7c2557])
ck('V12c 0x7c7350 E8 站点 1 处 @0x7c2a74', e[0x7c7350]==[0x7c2a74], [hex(x) for x in e[0x7c7350]])

# 0x7c7778 分派表
ck('V13 0x7c7778 前 4 dword == 0x7c73e2/0x7c73f8/0x7c7408/0x7c7418',
   list(struct.unpack_from('<4I',R,P.r2o(0x7c7778)))==[0x7c73e2,0x7c73f8,0x7c7408,0x7c7418])

# 函数参数结构（字节锚点）
bs=R[P.r2o(0x7c7371):P.r2o(0x7c7371)+0x90]
ck('V14 0x7c737c 字节 = 66 8b 4d 10 (mov cx,[ebp+0x10])', bs[0x0b:0x0f].hex()=='668b4d10', bs[0x0b:0x0f].hex())
ck('V14b 0x7c7380 字节 = 66 8b 55 14 (mov dx,[ebp+0x14])', bs[0x0f:0x13].hex()=='668b5514', bs[0x0f:0x13].hex())
ck('V14c 0x7c73ef 字节 = ff 24 9d 78 77 7c 00 (jmp [ebx*4+0x7c7778])', R[P.r2o(0x7c73ef):P.r2o(0x7c73ef)+7].hex()=='ff249d78777c00')

res=dict(instrs=n,last=hex(last),tab_refs=dict(cnt),imm3=len(imm3),imm4=len(imm4),
 offs={hex(k):dict(v) for k,v in C.items()},fails=fails)
json.dump(res,open('_r220/m14.json','w'),indent=1)
print('TOTAL FAILS:',len(fails),fails)
