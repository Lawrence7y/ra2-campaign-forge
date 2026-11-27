#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R185 AA：对 F01 正文的四条**可直接字节检验**的主张逐条判真伪（只读，不改台账）。

F01 statement 现状（V565）里可机械检验的四处：
  K1 「1201 条 COL 的 pTD 全部命中 988 个 TD(100%)」 → 分母 1201 是否可复现（R140 判不可复现）
  K2 「1201 条 COL 全被某 vtable 以 [-4] 指回」    → 同上
  K3 「954 为『主 COL』数（每类一个 lowest-VA 主 COL）」 → lowest-VA 与 mdisp==0 是否同一批（R140 判差 188）
  K4 「COL 恰 5 dword、无 pSelf 字段」 → COL−4 处是否确为另一结构（R140 记 257/1211）
判据全部从字节重算；本脚本不改任何仓内文件。
"""
import sys,json,collections
sys.path.insert(0,'/home/t628/projects/ra2-campaign-forge/_r185')
import pe185 as P
dw=P.dw;where=P.where;cstr=P.cstr
COLS=json.load(open('/home/t628/projects/ra2-campaign-forge/_r185/r185z.json'))
fails=[];n=0
def ck(nm,c,d=''):
    global n; n+=1
    if not c: fails.append(nm)
    print(('PASS ' if c else 'FAIL ')+nm+((' | '+str(d)) if d!='' else ''))
# 重建（复用 r185z 的枚举，直接内联）
import struct
RAW=P.RAW
TD=set()
s=P.B['.data']; blob=RAW[s['rawptr']:s['rawptr']+s['rawsize']]
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
            COLS[base]=(d[0],d[1],d[3],d[4])
vt=set()
for sec in ('.rdata','.data'):
    ss=P.B[sec]; vals=struct.unpack_from('<%dI'%(ss['rawsize']//4),RAW,ss['rawptr'])
    for i2,v in enumerate(vals):
        if 0x401000<=v<0x7E038D:
            va=ss['lo']+4*i2
            if dw(va-4) in COLS: vt.add(va)
print('枚举复算：TD=%d COL=%d vt=%d'%(len(TD),len(COLS),len(vt)))
# K1/K2：1201 可复现性 —— 以多种自然口径求「被指回的 distinct COL」数
backed={dw(v-4) for v in vt}
ck('K1 「被某 vtable 以 [-4] 指回的 COL」实测 == 1214（不是 1201）', len(backed)==1214, len(backed))
ck('K2 总 COL 实测 == 1214（不是 1211）', len(COLS)==1214, len(COLS))
ck('K3 「被指回的 COL 的 pTD 命中 TD」== 1214/1214（100%）', all(COLS[c][2] in TD for c in backed), sum(1 for c in backed if COLS[c][2] in TD))
# lowest-VA 主 COL vs mdisp==0
bytd=collections.defaultdict(list)
for c,(sig,md,ptd,pchd) in COLS.items(): bytd[ptd].append((c,md))
low=set(); m0=set()
for ptd,lst in bytd.items():
    low.add(min(lst)[0]); 
    z=[c for c,m in lst if m==0]
    m0.add(min(z) if z else None)
m0.discard(None)
ck('K4 lowest-VA 主 COL 数与 mdisp==0 主 COL 数都 == 954', len(low)==954 and len(m0)==954, (len(low),len(m0)))
diff=low^m0
ck('K5 两集合对称差 == 188（94+94），即「按数字相等互相引证」不成立', len(diff)==188, len(diff))
# 多 COL 类的 mdisp 单调性
multi=[(p,l) for p,l in bytd.items() if len(l)>=2]
dec=inc=mix=eq=0
for p,l in multi:
    seq=[m for c,m in sorted(l)]
    if all(seq[i]>seq[i+1] for i in range(len(seq)-1)): dec+=1
    elif all(seq[i]<seq[i+1] for i in range(len(seq)-1)): inc+=1
    elif all(x==seq[0] for x in seq): eq+=1
    else: mix+=1
ck('K6 多 COL 类（%d 个）按 mdisp 严格递减'%len(multi), dec==len(multi) and inc==0 and mix==0, (dec,inc,eq,mix))
# K7 COL−4 处是「另一结构」的比例
cnt=sum(1 for c in COLS if dw(c-4)!=0)
ck('K7 COL−4 处非零的条数（F01 记 257/1211；分母随 COL 总数变）', True, '%d/%d'%(cnt,len(COLS)))
json.dump({'td':len(TD),'col':len(COLS),'vt':len(vt),'backed':len(backed),'low':len(low),'m0':len(m0),
           'symdiff':len(diff),'multi':len(multi),'dec':dec,'col_m4_nonzero':cnt,'checks':n,'fails':fails},
          open('/home/t628/projects/ra2-campaign-forge/_r185/r185aa.json','w'),indent=1)
print('CHECKS',n,'FAILS',fails)
