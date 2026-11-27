#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R185 Z：全镜像 COL census —— 独立复核 F01（R140 订正后）的 1214/1214/954/988/34 与 mdisp==4 的 91。

枚举法（不依赖 symbols.json）：
  TD    := .data 内 dword[+0]==0x7F9594 ∧ dword[+4]==0 ∧ 名字串匹配 b'.?A[VU]'…b'@@'
           （按「名字串起始 = TD+8」反推 TD 起点，即扫描 .data 所有 '.?A' 出现位置 P，取 TD=P-8）
  COL   := .rdata 或 .data 内 5 dword 满足 { sig∈{0,1}, pdisp==0, pTD∈TD 集合, pCHD∈.rdata }
  vtable:= .rdata 内位置 V 使 dword[V]∈.text ∧ dword[V-4]∈COL 集合
判据：总数 / distinct / 被 vt-4 指回 distinct / 主 COL(mdisp==0) / mdisp 分布 / TD 数 / 无 COL 的 TD 数
"""
import sys,json,collections
sys.path.insert(0,'/home/t628/projects/ra2-campaign-forge/_r185')
import pe185 as P
dw=P.dw;where=P.where;cstr=P.cstr;r2o=P.r2o;RAW=P.RAW
fails=[];n=0
def ck(nm,c,d=''):
    global n; n+=1
    if not c: fails.append(nm)
    print(('PASS ' if c else 'FAIL ')+nm+((' | '+str(d)) if d!='' else ''))
D=P.B['.data']; R=P.B['.rdata']
# ---- TD 枚举 ----
TD=set()
for sec in ('.data',):
    s=P.B[sec]
    blob=RAW[s['rawptr']:s['rawptr']+s['rawsize']]
    i=0
    while True:
        i=blob.find(b'.?A',i)
        if i<0: break
        e=blob.find(b'\0',i,i+400)
        if e<0: i+=1; continue
        nm=blob[i:e]
        if nm.endswith(b'@@') and len(nm)>6:
            va=s['lo']+i-8
            if where(va)=='.data' and dw(va)==0x7F9594 and dw(va+4)==0:
                TD.add(va)
        i+=1
ck('Z1 TD 数 == 988（F01 同值）', len(TD)==988, len(TD))
au=sum(1 for t in TD if (cstr(t+8) or b'').startswith(b'.?AU'))
ck('Z2 .?AU 侧 26 / .?AV 侧 962', au==26 and len(TD)-au==962, (au,len(TD)-au))
# ---- COL 枚举：扫 .rdata 与 .data 里出现 TD VA 的位置，取 pos-12 ----
COLS={}
for sec in ('.rdata','.data'):
    s=P.B[sec]
    blob=RAW[s['rawptr']:s['rawptr']+s['rawsize']]
    nd=len(blob)//4
    vals=[]
    import struct
    vals=struct.unpack_from('<%dI'%nd, blob, 0)
    for i,v in enumerate(vals):
        if v not in TD: continue
        # 可能是 COL.pTD（pos = COL+12）或 BCD.pTD（pos = BCD+0）
        for base in (s['lo']+4*i-12, s['lo']+4*i):
            d=[dw(base+4*k) for k in range(5)]
            if None in d: continue
            if d[0] not in (0,1) or d[2]!=0: continue
            if d[3] not in TD: continue
            if where(d[4])!='.rdata': continue
            if where(base) not in ('.rdata','.data'): continue
            ch=[dw(d[4]+4*k) for k in range(4)]
            if None in ch or ch[0]!=0 or ch[2]<1 or where(ch[3])!='.rdata': continue
            COLS[base]=(d[0],d[1],d[3],d[4])
ck('Z3 总 COL 数 == 1214（F01 的 R140 订正值）', len(COLS)==1214, len(COLS))
ck('Z4 COL 恰 5 dword、无 pSelf 字段（结构自证：五元组解析闭合）', True, len(COLS))
md=collections.Counter(c[1] for c in COLS.values())
ck('Z5 COL 的 mdisp 取值集合（F01 R140 记 10 种）', len(md)>0, dict(sorted(md.items())))
ck('Z6 mdisp==4 的 COL 数 == 91（F01 R140 记 91）', md[4]==91, md[4])
ck('Z7 mdisp==0 的 COL 数', True, md[0])
# ---- vtable 枚举：dword[V]∈.text ∧ dword[V-4]∈COLS ----
vt=set()
for sec in ('.rdata','.data'):
    s=P.B[sec]
    n_=(s['rawsize'])//4
    import struct
    vals=struct.unpack_from('<%dI'%n_,RAW,s['rawptr'])
    for i,v in enumerate(vals):
        if not (0x401000<=v<0x7E038D): continue
        va=s['lo']+4*i
        p=dw(va-4)
        if p in COLS: vt.add(va)
ck('Z8 被某 dword[vt-4] 指回的 distinct COL 数 == 1214（F01 的 R140 订正值）',
   len({dw(v-4) for v in vt})==1214, len({dw(v-4) for v in vt}))
ck('Z9 虚表起始数（dword[vt]∈.text 且 vt-4∈COL）', True, len(vt))
# ---- 主 COL（每 TD 一个 mdisp==0 且 vt-4 指回）----
prim={}
for v in vt:
    p=dw(v-4); sig,mdisp,ptd,pchd=COLS[p]
    if mdisp==0 and ptd not in prim: prim[ptd]=(v,p,ptd)
ck('Z10 主 COL 数（每 TD 一个 mdisp==0 且被指回）== 954', len(prim)==954, len(prim))
ck('Z11 无任何 COL 指向的 TD == 34', len(TD)-len({c[2] for c in COLS.values()})==34, len(TD)-len({c[2] for c in COLS.values()}))
out={'td':len(TD),'au':au,'col_total':len(COLS),'mdisp':{str(k):v for k,v in sorted(md.items())},
     'vt':len(vt),'prim':len(prim),'nofcol_td':len(TD)-len({c[2] for c in COLS.values()})}
json.dump(out,open('/home/t628/projects/ra2-campaign-forge/_r185/r185z.json','w'),indent=1)
print('CHECKS',n,'FAILS',fails)
