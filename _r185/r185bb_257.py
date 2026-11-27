#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R185 BB：核验 F31/F01 limitations 里的「COL−0x4 处的另一结构（257/1211）」这两个数的来历。

候选谓词：
  Q0 dword[COL-4] == 0  在 1214 个 COL 上
  Q1 同上，但分母先按「COL+4 <= 0x1000」砍到 1211（F01 记录 1211 的唯一可复现口径）
  Q2 dword[COL-0x10] == COL（pSelf 形态）在 1214/1211 上
"""
import sys,json,struct
sys.path.insert(0,'/home/t628/projects/ra2-campaign-forge/_r185')
import pe185 as P
dw=P.dw;where=P.where;cstr=P.cstr;RAW=P.RAW
fails=[];n=0
def ck(nm,c,d=''):
    global n; n+=1
    if not c: fails.append(nm)
    print(('PASS ' if c else 'FAIL ')+nm+((' | '+str(d)) if d!='' else ''))
TD=set(); s=P.B['.data']; blob=RAW[s['rawptr']:s['rawptr']+s['rawsize']]
i=0
while True:
    i=blob.find(b'.?A',i)
    if i<0: break
    e=blob.find(b'\0',i,i+400)
    if e<0: i+=1; continue
    nm=blob[i:e]
    if nm.endswith(b'@@') and len(nm)>6:
        va=s['lo']+i-8
        if where(va)=='.data' and dw(va)==0x7F9594 and dw(va+4)==0: TD.add(va)
    i+=1
COLS={}
for sec in ('.rdata','.data'):
    ss=P.B[sec]; b2=RAW[ss['rawptr']:ss['rawptr']+ss['rawsize']]
    vals=struct.unpack_from('<%dI'%(len(b2)//4),b2,0)
    for i2,v in enumerate(vals):
        if v not in TD: continue
        for base in (ss['lo']+4*i2-12, ss['lo']+4*i2):
            d=[dw(base+4*k) for k in range(5)]
            if None in d or d[0] not in (0,1) or d[2]!=0: continue
            if d[3] not in TD or where(d[4])!='.rdata': continue
            ch=[dw(d[4]+4*k) for k in range(4)]
            if None in ch or ch[0]!=0 or ch[2]<1 or where(ch[3])!='.rdata': continue
            COLS[base]=d
ck('BB1 COL 总数 1214', len(COLS)==1214, len(COLS))
q0=sum(1 for c in COLS if dw(c-4)==0)
q0n=len(COLS)-q0
ck('BB2 Q0 dword[COL-4]==0 的条数', True, '%d/%d（非零 %d）'%(q0,len(COLS),q0n))
sub=[c for c in COLS if dw(c+4)<=0x1000]
ck('BB3 「COL+4 <= 0x1000」砍出的子集 == 1211', len(sub)==1211, len(sub))
q1=sum(1 for c in sub if dw(c-4)==0)
q1n=len(sub)-q1
ck('BB4 Q1 在 1211 子集上 dword[COL-4]==0 的条数 == 257', q1==257, '%d/%d（非零 %d）'%(q1,len(sub),q1n))
mx=sum(1 for c in COLS if dw(c-0x10)==c)
ck('BB5 Q2 pSelf 形态 dword[COL-0x10]==COL 的条数 == 0', mx==0, mx)
three=[c for c in COLS if dw(c+4)>0x1000]
ck('BB6 被 1211 口径剔除的恰 3 个且其 COL+4 全是 0x5518', len(three)==3 and all(dw(c+4)==0x5518 for c in three), [(hex(c),hex(dw(c+4))) for c in three])
ck('BB7 被剔除的 3 个在 COL-4 处均为 0（⇒ 260-3=257 自洽）', all(dw(c-4)==0 for c in three), [dw(c-4) for c in three])
json.dump({'col':len(COLS),'q0_zero':q0,'q0_nonzero':q0n,'sub1211':len(sub),'q1_zero':q1,'q1_nonzero':q1n,'pself':mx,
           'excluded':[(hex(c),hex(dw(c+4)),dw(c-4)) for c in three],'checks':n,'fails':fails},
          open('/home/t628/projects/ra2-campaign-forge/_r185/r185bb.json','w'),indent=1)
print('CHECKS',n,'FAILS',fails)
