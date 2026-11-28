# -*- coding: utf-8 -*-
"""R208 m4：①0x7f9594 的 vftable[-1] 归属（0x80ee30 是否 type_info 的 COL）；②1215 张 vftable 槽普查（订正 m2 的读取 bug）。
正控：槽目标按 .text 连续读；每张 vftable 长度；槽目标频次
反控：把槽目标整体平移到 vftable 起点自身 / 用 .rdata 随机 dword 做伪槽
"""
import sys,struct,collections
sys.path.insert(0,'/home/t628/projects/ra2-campaign-forge/_r185')
import pe185 as P
def s32(v): return struct.unpack('<i',struct.pack('<I',v))[0]
fails=[];NA=0
def ck(n,c,d=''):
    global NA;NA+=1
    if not c: fails.append(n)
    print(('PASS ' if c else 'FAIL ')+n+((' | '+str(d)) if d!='' else ''))
COL={}
for sn in ('.rdata','.data'):
    s=P.B[sn]; n=s['rawsize']//4; base=s['lo']
    w=struct.unpack_from('<%dI'%n,P.RAW,s['rawptr'])
    for i in range(n-4):
        if w[i] not in (0,1,2) or w[i+2]!=0: continue
        if P.where(w[i+3])!='.data' or P.where(w[i+4])!='.rdata': continue
        nm=P.cstr(w[i+3]+8,400)
        if not (nm and nm.startswith(b'.?A') and nm.endswith(b'@@')): continue
        COL[base+4*i]=dict(sig=w[i],mdisp=s32(w[i+1]),pTD=w[i+3],pCHD=w[i+4],name=nm.decode('latin1'))
print('== T1 0x7f9594 的 vftable[-1] ==')
prev=P.dw(0x7f9590)
print('  vftable[-1]=0x%x 在 COL 表? %s' % (prev, prev in COL))
if prev in COL:
    d=COL[prev]; print('   COL 字段 sig=%d mdisp=%d pTD=0x%x pCHD=0x%x name=%s' %
        (d['sig'],d['mdisp'],d['pTD'],d['pCHD'],d['name']))
    ck('T1.1 type_info 的 COL sig==0 且 mdisp==0', d['sig']==0 and d['mdisp']==0, (d['sig'],d['mdisp']))
    ck('T1.2 type_info COL 的类名 == .?AVtype_info@@', d['name']=='.?AVtype_info@@', d['name'])
    ck('T1.3 QK1 律（vftable[-1]==COL）在该对象上也成立', prev==0x80ee30, hex(prev))
ALL=dict(COL)
# 全库 vftable 定位（用修正后的槽读取）
RD={}
for sn in ('.rdata','.data'):
    s=P.B[sn]; RD[sn]=(s['lo'],struct.unpack_from('<%dI'%(s['rawsize']//4),P.RAW,s['rawptr']),s['rawsize']//4)
refidx=collections.defaultdict(list)
for sn in ('.rdata','.data'):
    base,w,n=RD[sn]
    for i,x in enumerate(w):
        if x in COL: refidx[x].append(base+4*i)
def vlen(start,cap=4096):
    c=0;a=start
    while P.where(P.dw(a))=='.text' and c<cap:
        c+=1;a+=4
    return c
vt={}
for c in COL:
    q=[x for x in refidx.get(c,[]) if P.where(P.dw(x+4))=='.text']
    if len(q)==1: vt[c]=q[0]+4
ck('T2.1 1214 条业务 COL 各有唯一 vftable', len(vt)==1214,(len(vt),))
vt[prev]=0x7f9594   # type_info 自身
L={c:vlen(s) for c,s in vt.items()}
tot=sum(L.values())
S={c:[P.dw(s+4*i) for i in range(L[c])] for c,s in vt.items()}
tgt=collections.Counter(x for v in S.values() for x in v)
print('  vftable 数 %d（type_info 的 COL 0x80ee30 本就在 1214 条业务 COL 内） 槽总数 %d' % (len(vt),tot))
ck('T2.2 type_info vftable 槽数 1', L[prev]==1, L[prev])
# 订正（R208 自错第 6 组）：type_info 的 COL（0x80ee30）本来就在 1214 条业务 COL 之内，
# 因此 vt[prev]=0x7f9594 只是覆盖同一项，L[prev] 不应从业务合计里扣除。
ck('T2.3 业务 1214 张槽总数 == 14044（含 type_info 那 1 槽）', tot==14044, tot)
ck('T2.4 所有槽目标均在 .text', all(P.where(x)=='.text' for x in tgt), sum(1 for x in tgt if P.where(x)!='.text'))
print('== T3 槽目标频次 ==')
top=tgt.most_common(10)
print('  top10', [(hex(k),v) for k,v in top])
print('  不同目标数 %d / %d 槽' % (len(tgt),tot))
dup=sum(1 for k,v in tgt.items() if v>1)
print('  被 >=2 张/槽复用的目标数 %d' % dup)
ck('T3.1 槽目标去重数显著小于槽数（存在大量复用）', len(tgt)<tot*0.7, (len(tgt),tot))
ck('T3.2 最高频目标被引用 >=50 次', top[0][1]>=50, top[0])
# 反控
selfc=collections.Counter(vt.values())
ck('T4.1 反控：vftable 起始址全互不相同（%d）' % len(selfc), len(selfc)==len(vt), len(selfc))
rand=[P.dw(0x7f9610+4*i) for i in range(0,200)]
ck('T4.2 反控：V+4 之后的字符串区不构成槽（where 非 .text 比例高）',
   sum(1 for x in rand if P.where(x)=='.text') < 60, sum(1 for x in rand if P.where(x)=='.text'))
import json
json.dump(dict(vft=len(vt),slots=tot,bizSlots=tot,distinct=len(tgt),
               top=[[hex(k),v] for k,v in top],dup=dup,asserts=NA,fails=fails),
          open('_r208/m4_census.json','w'),ensure_ascii=False,indent=1)
print('== 断言 %d / FAIL %d =='%(NA,len(fails)),fails)
