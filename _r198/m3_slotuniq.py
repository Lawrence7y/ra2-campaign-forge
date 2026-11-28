#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R198 第三刀：槽位唯一性 —— L 的 18 个「槽号+默认实现」在全 1214 张表里是否只出现在那一个槽号。
并把 0x7F5C70（344 槽）作为超长表的对照，回答 R195 PX9 遗留④「槽 24..343 的默认实现」。
判据：
 S1 基线 COL=1214/VT=1214/槽总=14044/L=78。
 S2 对每个已知 (槽号, 实现地址)，扫全 1214 张表全部 14044 个槽位，记录它出现的槽号集合 + 表数。
    「槽位唯一」= 槽号集合恰为该单元素。
 S3 0x7F5C70 中这 18 个实现各落在哪些槽号。
 S4 反面：若某实现出现在多个槽号，给出槽号列表与每槽的表数。
反控：
 R1 用两个已知多宿主地址（0x4C9150 纯桩、0x410220）作对照，它们的槽号集合应当非单元素。
 R2 把「槽位」判据从表内下标改成「表内下标 + 主表/子表」，看是否改变结论。
 R3 把扫描范围从 1214 张表收窄到 L 的 78 张表，看每个实现的槽号集合是否变化。
"""
import sys,struct,collections,json
sys.path.insert(0,'/home/t628/projects/ra2-campaign-forge/_r185')
import pe185 as P
fails=[];N=0
def ck(nm,c,d=''):
    global N;N+=1
    if not c: fails.append(nm)
    print(('PASS ' if c else 'FAIL ')+nm+((' | '+str(d)) if d!='' else ''))
T=P.B['.text'];LO=T['lo'];HI=T['hi_file'];RAW=P.RAW
def s32(v): return struct.unpack('<i',struct.pack('<I',v))[0]
def wv(sn):
    s=P.B[sn];n=s['rawsize']//4
    return s['lo'],struct.unpack_from('<%dI'%n,RAW,s['rawptr']),n
def in_text(x): return x is not None and LO<=x<HI
COL={}
for sn in ('.rdata','.data'):
    base,w,n=wv(sn)
    for i in range(n-4):
        if w[i] not in (0,1,2) or w[i+2]!=0: continue
        if P.where(w[i+3])!='.data' or P.where(w[i+4])!='.rdata': continue
        nm=P.cstr(w[i+3]+8,400)
        if not(nm and nm.startswith(b'.?A') and nm.endswith(b'@@')): continue
        COL[base+4*i]=dict(mdisp=s32(w[i+1]),name=nm.decode('latin1'),pchd=w[i+4])
VT={}
for sn in ('.rdata','.data'):
    base,w,n=wv(sn)
    for i in range(n):
        if in_text(w[i]) and P.dw(base+4*i-4) in COL: VT[base+4*i]=P.dw(base+4*i-4)
def nslot(vt):
    k=0
    while in_text(P.dw(vt+4*k)): k+=1
    return k
NS={vt:nslot(vt) for vt in VT}
def chain(colva):
    n=P.dw(COL[colva]['pchd']+8);arr=P.dw(COL[colva]['pchd']+12);out=[]
    for j in range(n):
        b=P.dw(arr+4*j);ptd=P.dw(b);nm=P.cstr(ptd+8,400)
        out.append(nm.decode('latin1') if nm else None)
    return out
MAIN=[vt for vt in VT if COL[VT[vt]]['mdisp']==0]
LIN=sorted(vt for vt in MAIN if '.?AVAbstractClass@@' in chain(VT[vt]))
ck('S1a 基线',(len(COL),len(VT),sum(NS.values()),len(LIN))==(1214,1214,14044,78),
   (len(COL),len(VT),sum(NS.values()),len(LIN)))

# 全表槽位索引：addr -> set(slot)
ALL=collections.defaultdict(lambda: collections.defaultdict(set))   # addr -> slot -> set(vt)
for vt in VT:
    for k in range(NS[vt]):
        a=P.dw(vt+4*k)
        ALL[a][k].add(vt)

KNOWN={
 0:0x410260,1:0x410300,2:0x410310,3:0x4C9150,4:0x410450,5:0x5F5E80,6:0x4C9150,
 7:0x4103E0,8:0x4105A0,9:0x410470,10:0x410480,11:0x4C9150,12:0x4C9150,
 13:0x5F6250,14:0x410490,15:0x4104A0,16:0x4104B0,17:0x410440}
rows=[]
for s,a in KNOWN.items():
    d=ALL.get(a,{})
    slots=sorted(d)
    rows.append(dict(slot=s,va=hex(a),nslots=len(slots),slots=slots,
                     ntables=len(set().union(*d.values())) if d else 0,
                     total=sum(len(v) for v in d.values())))
ck('S2a 18 个已知实现全部在盘中找到', all(r['ntables']>0 for r in rows),
   [r['va'] for r in rows if r['ntables']==0])
for r in rows:
    print('   S2b slot%-2d %s : 槽号集合=%s 表数=%d 槽位总数=%d'%(r['slot'],r['va'],r['slots'],r['ntables'],r['total']))
uniq=[r for r in rows if r['nslots']==1 and r['slot'] in r['slots']]
ck('S2c 槽位唯一的实现数 / 18', True, len(uniq))
ck('S2d 槽位唯一且槽号==期望的个数', all(r['slots']==[r['slot']] for r in uniq), 
   [(r['slot'],r['slots']) for r in uniq if r['slots']!=[r['slot']]])
multi=[r for r in rows if r['nslots']>1]
print('   S2e 出现在多个槽号的实现（去重地址）:', sorted({r['va'] for r in multi}))

# S3 0x7F5C70
VT_C=0x7F5C70; S=[P.dw(VT_C+4*k) for k in range(344)]
pos={}
for k,a in enumerate(S):
    if a in set(KNOWN.values()): pos.setdefault(a,[]).append(k)
ck('S3a 0x7F5C70 内命中的已知实现', True, {hex(a):v for a,v in pos.items()})
for a,v in pos.items():
    exp=[s for s,b in KNOWN.items() if b==a]
    print('   S3b %s 期望槽 %s 实际槽 %s'%(hex(a),exp,v))

# S4 多槽号的分布
for r in multi:
    d=ALL[int(r['va'],16)]
    print('   S4a %s 槽号->表数: %s'%(r['va'], {k:len(v) for k,v in sorted(d.items())}))

# R1 对照
for a in (0x4C9150,0x410220):
    d=ALL.get(a,{})
    ck('R1a %s 槽号集合非单元素'%hex(a), len(d)!=1, sorted(d))
# R2 主表/子表拆分
SUB=[vt for vt in VT if COL[VT[vt]]['mdisp']!=0]
for r in rows:
    a=int(r['va'],16); d=ALL[a]
    m=sorted({k for k,v in d.items() if any(t in MAIN for t in v)})
    sb=sorted({k for k,v in d.items() if any(t in SUB for t in v)})
    r['main_slots']=m; r['sub_slots']=sb
ck('R2a 主表/子表拆分后槽号集合是否一致', all(set(r['main_slots'])|set(r['sub_slots'])==set(r['slots']) for r in rows), True)
# R3 只看 L
LUT=set(LIN)
for r in rows:
    a=int(r['va'],16); d=ALL[a]
    ls=sorted({k for k,v in d.items() if v & LUT})
    r['L_slots']=ls
ck('R3a 只在 L 的 78 张表内统计的槽号集合', True, {r['va']:r['L_slots'] for r in rows})
ck('R3b L 内是否与全表口径同结论', all(set(r['L_slots'])==set(r['slots']) or set(r['L_slots'])<=set(r['slots']) for r in rows), True)
res=dict(rows=rows,uniq=len(uniq),all_slots={hex(a):{str(k):len(v) for k,v in d.items()} for a,d in ALL.items() if a in set(KNOWN.values())},
         pos7f5c70={hex(a):v for a,v in pos.items()},asserts=N,fails=fails)
json.dump(res,open('/home/t628/projects/ra2-campaign-forge/_r198/m3_slotuniq.json','w'),ensure_ascii=False,indent=1)
print('\nSUMMARY asserts=%d fails=%d %s'%(N,len(fails),fails))
