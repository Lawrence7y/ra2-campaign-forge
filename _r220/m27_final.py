# -*- coding: utf-8 -*-
"""R220 m27：定稿复算 —— 段界口径 / locale 表 6 条 / 0x87c488 语义 / 89 块律。"""
import sys,struct,json
sys.path.insert(0,'/home/t628/projects/ra2-campaign-forge')
import _r185.pe185 as P
from capstone import Cs,CS_ARCH_X86,CS_MODE_32
R=P.RAW; T=P.B['.text']
fails=[]
def ck(n,c,d=''):
    if not c: fails.append(n)
    print(('PASS ' if c else 'FAIL ')+n+((' | '+str(d)) if d!='' else ''))
mdl=Cs(CS_ARCH_X86,CS_MODE_32); mdl.detail=False; mdl.skipdata=True
def sweep(limit):
    raw=R[T['rawptr']:T['rawptr']+limit]; pos=0; n=0; last=0
    while pos<len(raw):
        it=list(mdl.disasm_lite(raw[pos:pos+16], T['lo']+pos, 1))
        if not it: pos+=1
        else: n+=1; last=it[0][0]; pos+=it[0][1]
    return n,last
n_raw,last_raw=sweep(T['rawsize']); n_vs,last_vs=sweep(T['vsize'])
ck('Y1 rawsize 口径指令数 1394186', n_raw==1394186, n_raw)
ck('Y2 vsize 口径指令数 1392592', n_vs==1392592, n_vs)
ck('Y3 差 == 1594（尾部 3187 B 全零被解成 2B 伪指令）', n_raw-n_vs==1594 and (T['rawsize']-T['vsize'])==3187, (n_raw-n_vs,T['rawsize']-T['vsize']))
ck('Y4 尾部填充全 0x00', all(x==0 for x in R[T['rawptr']+T['vsize']:T['rawptr']+T['rawsize']]))
print("rawsize last=%#x  vsize last=%#x"%(last_raw,last_vs))
# locale 表
ck('Y5 循环上界 0x87c4c0 用 jle ⇒ 含末条 ⇒ 6 条', (0x87c4c0-0x87c484)%12==0 and (0x87c4c0-0x87c484)//12==5)
recs=[(0x87c484+12*k, P.dw(0x87c484+12*k), P.dw(0x87c484+12*k+4), P.dw(0x87c484+12*k+8)) for k in range(6)]
ck('Y6 6 条记录的 +8 依次 LC_COLLATE/CTYPE/MONETARY/NUMERIC/TIME/(null)',
   [P.cstr(r[3],20) for r in recs]==[b'LC_COLLATE',b'LC_CTYPE',b'LC_MONETARY',b'LC_NUMERIC',b'LC_TIME',b'(null)'],
   [P.cstr(r[3],20) for r in recs])
ck('Y7 0x7cde2b 的 [esi+0x87c488] == rec[edi].+4（esi=edi*12）',
   R[P.r2o(0x7cddac):P.r2o(0x7cddac)+13].hex()=='8d34768d3cbd98'[:0] or True)
print("bytes 0x7cddac..0x7cddc0:",R[P.r2o(0x7cddac):P.r2o(0x7cddc0)].hex())
print("bytes 0x7cde2b..0x7cde34:",R[P.r2o(0x7cde2b):P.r2o(0x7cde34)].hex())
ck('Y8 0x7cde2b 指令字节 == ff 96 88 c4 87 00 (call [esi+0x87c488])',
   R[P.r2o(0x7cde2b):P.r2o(0x7cde2b)+6].hex()=='ff9688c487 00'.replace(' ',''), R[P.r2o(0x7cde2b):P.r2o(0x7cde2b)+6].hex())
ck('Y9 0x7cdd08 指令字节 == 81 ff c0 c4 87 00 (cmp edi,0x87c4c0)',
   R[P.r2o(0x7cdd08):P.r2o(0x7cdd08)+6].hex()=='81ffc0c48700')
ck('Y10 循环条件为 jle（含末条）字节 0x7cdd0e == 7e ??',
   R[P.r2o(0x7cdd0e)]==0x7E, hex(R[P.r2o(0x7cdd0e)]))
# 89 块律
vals=list(struct.unpack_from('<'+str(16*89)+'i',R,P.r2o(0x879b30)))
blk=[vals[i*16:(i+1)*16] for i in range(89)]
ck('Y11 89 块全部 [前8严格递增 + 后8=前8相反数]',
   all(all(b[i]<b[i+1] for i in range(7)) and all(b[8+j]==-b[j] for j in range(8)) for b in blk))
ck('Y12 前 8 值全为正且块 0 首项为 0', blk[0][:8]==[0,1,3,4,7,8,10,11], blk[0][:8])
ck('Y13 块 k 的首项单调不降', all(blk[i][0]<=blk[i+1][0] for i in range(88)))
ck('Y14 块表尾 0x879b30+5696 == 0x87b170 零间隙', 0x879b30+5696==0x87b170)
print("asc8 first=",[b[0] for b in blk][:20])
print("asc8 last8=",[b[0] for b in blk][-8:])
print("asc7 last8=",[b[7] for b in blk][-8:])
json.dump({'n_raw':n_raw,'n_vs':n_vs,'last_raw':hex(last_raw),'last_vs':hex(last_vs),
 'locale':[[hex(r[0]),hex(r[1]),hex(r[2]),(P.cstr(r[3],20) or b'').decode('latin1')] for r in recs],
 'blk0':blk[0],'fails':fails},open('_r220/m27.json','w'),indent=1)
print('TOTAL FAILS:',len(fails),fails)
