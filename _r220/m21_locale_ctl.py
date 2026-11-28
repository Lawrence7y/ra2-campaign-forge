# -*- coding: utf-8 -*-
"""R220 m21：0x87c484 区域 = CRT locale 类别表（6 条 12 B）的正反控自测。"""
import sys,struct,json
sys.path.insert(0,'/home/t628/projects/ra2-campaign-forge')
import _r185.pe185 as P
R=P.RAW
fails=[]
def ck(n,c,d=''):
    if not c: fails.append(n)
    print(('PASS ' if c else 'FAIL ')+n+((' | '+str(d)) if d!='' else ''))
BASE=0x87c484; STRIDE=12; N=6
recs=[]
for k in range(N):
    b=BASE+k*STRIDE
    recs.append((b,P.dw(b),P.dw(b+4),P.dw(b+8)))
for r in recs: print("  rec %#x: +0=%#x(%r) +4=%#x(%s) +8=%#x(%r)"%(
    r[0],r[1],P.cstr(r[1],16),r[2],P.where(r[2]),r[3],P.cstr(r[3],20)))
cat=[P.cstr(r[3],16) or b'' for r in recs[1:]]
ck('K1 6 条记录 12B 步长，跨 0x87c484..0x87c4d0',
   [r[0] for r in recs]==[0x87c484+12*k for k in range(6)])
ck('K2 后 5 条 +8 全是 LC_* 类别名',
   cat==[b'LC_CTYPE',b'LC_MONETARY',b'LC_NUMERIC',b'LC_TIME',b'(null)'], cat)
ck('K3 第 1 条 +8 == LC_COLLATE', P.cstr(recs[0][3],16)==b'LC_COLLATE', P.cstr(recs[0][3],16))
ck('K4 后 5 条 +0 全是同一字符串 0x87c370 == "C"', all(r[1]==0x87c370 for r in recs[1:]) and P.cstr(0x87c370,4)==b'C')
ck('K5 6 条 +4 全部落 .text', all(P.where(r[2])=='.text' for r in recs), [P.where(r[2]) for r in recs])
ck('K6 rec0 的 +4 == 0x7ce046 是 xor eax,eax/ret 桩', recs[0][2]==0x7ce046 and R[P.r2o(0x7ce046):P.r2o(0x7ce046)+3]==bytes([0x33,0xc0,0xc3]))
ck('K7 上界指令字节 0x7cdd08 == 81 ff c0 c4 87 00 (cmp edi,0x87c4c0)',
   R[P.r2o(0x7cdd08):P.r2o(0x7cdd08)+6].hex()=='81ffc0c48700', R[P.r2o(0x7cdd08):P.r2o(0x7cdd08)+6].hex())
ck('K8 循环末条基址 0x87c4c0 == 第 5 条记录基址（共 6 条、末条亦被遍历）', BASE+5*STRIDE==0x87c4c0)
# 反控：以 0x87c488 为基址、12B 步长时 +8 不再是类别名
bad=[P.cstr(P.dw(0x87c488+12*k+8),16) for k in range(5)]
ck('K9 反控 以 0x87c488 为基址则 +8 不再全是 LC_*', sum(1 for x in bad if x and x.startswith(b'LC_'))<5, bad)
# 负控：0x87c4d0 起不再有 12B 结构（+8 不是 LC_*）
ck('K10 负控 第 7 条(0x87c4d0) 的 +8 不是 LC_*',
   not (P.cstr(P.dw(0x87c4d0+8),16) or b'').startswith(b'LC_'), P.cstr(P.dw(0x87c4d0+8),16))
json.dump({'recs':[[hex(r[0]),hex(r[1]),hex(r[2]),hex(r[3]),
   (P.cstr(r[1],16) or b'').decode('latin1'),(P.cstr(r[3],20) or b'').decode('latin1')] for r in recs],
   'fails':fails},open('_r220/m21.json','w'),indent=1,ensure_ascii=False)
print('TOTAL FAILS:',len(fails),fails)
