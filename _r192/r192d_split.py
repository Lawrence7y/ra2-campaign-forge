#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R192 D：把「表」分成主表（mdisp==0，954）与接口子表（mdisp!=0，260），
分别计算「同接口同槽号」的一致性，纠正 C 段把主表槽当成自有接口槽的口径缺陷。

D1 接口子表键 (层基类名, mdisp, 槽号)：键数、宿主分布、一致率、众数覆盖率。
D2 主表槽号不按「自有层」键，改按「该槽在主表上被多少个类共用同一实现」统计（这是
   覆写率的反面）：对 0x410450 / 0x410580 / 0x410590 / 0x4C9150 各给 主表槽位宿主数。
D3 三个高频实现的语义身份：0x410450 读 this+0x20 字节返回 !b；0x410580 恒返 false(ret 8)；
   0x410590 恒返 true? （ret 4）；给出各自字节与返回约定。
"""
import sys, os, struct, collections, json
sys.path.insert(0,'/home/t628/projects/ra2-campaign-forge/_r185')
import pe185 as P

fails=[]; N=0
def ck(nm,c,d=''):
    global N; N+=1
    if not c: fails.append(nm)
    print(('PASS ' if c else 'FAIL ')+nm+((' | '+str(d)) if d!='' else ''))

T=P.B['.text']; LO=T['lo']; HI=T['hi_file']
def in_text(x): return x is not None and LO<=x<HI
def wv(sn):
    s=P.B[sn]; n=s['rawsize']//4
    return s['lo'], struct.unpack_from('<%dI'%n,P.RAW,s['rawptr']), n
COL={}
for sn in ('.rdata','.data'):
    base,w,n=wv(sn)
    for i in range(n-4):
        if w[i] not in (0,1) or w[i+2]!=0: continue
        if P.where(w[i+3])!='.data' or P.where(w[i+4])!='.rdata': continue
        nm=P.cstr(w[i+3]+8,200)
        if not (nm and nm.startswith(b'.?A') and nm.endswith(b'@@')): continue
        COL[base+4*i]=dict(mdisp=w[i+1],ptd=w[i+3],pchd=w[i+4],name=nm.decode('latin1'))
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
ck('D0 基线 1214/1214/14044', (len(COL),len(VT),sum(NS.values()))==(1214,1214,14044),
   (len(COL),len(VT),sum(NS.values())))
VF=0x7F9594
TD={}
for sn in ('.data','.rdata'):
    base,w,n=wv(sn)
    for i in range(n-2):
        if w[i]!=VF: continue
        va=base+4*i; nm=P.cstr(va+8,160)
        if nm and nm.startswith(b'.?A') and nm.endswith(b'@@'): TD[va]=nm.decode('latin1')
def bcds(c):
    return [P.dw(P.dw(c['pchd']+12)+4*j) for j in range(P.dw(c['pchd']+8))]
def layer_name(colva):
    c=COL[colva]
    m=[b for b in bcds(c) if b is not None and P.dw(b+8)==c['mdisp']]
    if not m: return '?'
    best=max(m,key=lambda b:P.dw(b+4))
    return TD.get(P.dw(best),'?')

main=[vt for vt in VT if COL[VT[vt]]['mdisp']==0]
sub=[vt for vt in VT if COL[VT[vt]]['mdisp']!=0]
ck('D1 主表 954 / 接口子表 260', (len(main),len(sub))==(954,260), (len(main),len(sub)))
ck('D2 两者槽实例合计 14044', sum(NS[t] for t in main)+sum(NS[t] for t in sub)==14044,
   (sum(NS[t] for t in main), sum(NS[t] for t in sub)))

# ---- D1 接口子表键 ----
key=collections.defaultdict(list)
for vt in sub:
    ln=layer_name(VT[vt]); m=COL[VT[vt]]['mdisp']
    for k in range(NS[vt]): key[(ln,m,k)].append((vt,P.dw(vt+4*k)))
ck('D3 接口子表键数（层,mdisp,槽）= 704', len(key)==704, len(key))
multi={k:v for k,v in key.items() if len(v)>1}
ck('D4 有 >=2 宿主的键 67 / 覆盖槽实例 1275',
   (len(multi),sum(len(v) for v in multi.values()))==(67,1275),
   (len(multi),sum(len(v) for v in multi.values())))
cons=sum(1 for k,v in multi.items() if len({x for _,x in v})==1)
ck('D5 完全一致的键 6 / 不一致 61', (cons,len(multi)-cons)==(6,61), (cons,len(multi)-cons))
mod=sum(collections.Counter([x for _,x in v]).most_common(1)[0][1] for v in multi.values())
tot=sum(len(v) for v in multi.values())
ck('D6 众数覆盖率 1037/1275 = 81.33%', (mod,tot)==(1037,1275), (mod,tot))
# 68.7% 的键只有 1 个宿主（接口子表基本不共享）
ck('D7 单宿主键 637 / 总键 704', len(key)-len(multi)==637, len(key)-len(multi))

# ---- D2 主表高频实现 ----
TGT=[0x410450,0x410580,0x410590,0x4C9150]
for tgt in TGT:
    slots=collections.Counter(); hosts=0
    for vt in main:
        for k in range(NS[vt]):
            if P.dw(vt+4*k)==tgt: slots[k]+=1; hosts+=1
    print('D8 主表 %08x 出现 %d 次，槽号分布 %s'%(tgt,hosts,dict(sorted(slots.items()))))
    ck('D8x 主表 %08x 槽号唯一'%tgt, len(slots)<=1, dict(sorted(slots.items())))
# 主表槽 4 的实现分布（954 张主表）
c4=collections.Counter(P.dw(vt+16) for vt in main if NS[vt]>4)
ck('D9 主表槽 4 的 954 个实现里 Top1 = 0x410450 出现 77 次',
   c4.most_common(1)[0]==(0x410450,77), c4.most_common(3))
c0=collections.Counter(P.dw(vt) for vt in main)
print('D10 主表槽 0 分布 Top5:', [(hex(a),c) for a,c in c0.most_common(5)])
ck('D10x 主表槽 0 共 %d 个不同实现'%len(c0), len(c0)>1, len(c0))

json.dump(dict(main=len(main),sub=len(sub),keys=len(key),multi=len(multi),multi_inst=tot,
               cons=cons,modal=mod,single=len(key)-len(multi),
               mainslot4=[[hex(a),c] for a,c in c4.most_common(5)],
               mainslot0=[[hex(a),c] for a,c in c0.most_common(5)]),
          open('/home/t628/projects/ra2-campaign-forge/_r192/r192d.json','w'), indent=1)
print('断言 %d 条，FAIL %d 条'%(N,len(fails)))
sys.exit(1 if fails else 0)
