#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R185 Y：mdisp==4 的 12 个 Locomotion 类，其 BCD 中 ILocomotion 项的 mdisp 也恒为 4。

这是 A2「主 COL.mdisp==4 因为这些类的 ILocomotion 位于对象偏移 4」的**独立字节证据**：
不是从主 COL 的 mdisp 反推，而是从 CHD -> pBaseArray -> BCD 的第二条独立链测得同一个 4。
"""
import sys,json,collections
sys.path.insert(0,'/home/t628/projects/ra2-campaign-forge/_r185')
import pe185 as P
dw=P.dw;where=P.where;cstr=P.cstr;r2o=P.r2o
fails=[];n=0
def ck(nm,c,d=''):
    global n; n+=1
    if not c: fails.append(nm)
    print(('PASS ' if c else 'FAIL ')+nm+((' | '+str(d)) if d!='' else ''))
def colrec(a):
    if a is None or where(a)!='.rdata': return None
    d=[dw(a+4*i) for i in range(5)]
    if None in d or d[0] not in (0,1) or d[2]!=0: return None
    if where(d[3])!='.data' or where(d[4])!='.rdata': return None
    nm=cstr(d[3]+8)
    if not (nm and nm.startswith(b'.?A') and nm.endswith(b'@@')): return None
    return {'va':a,'mdisp':d[1],'ptd':d[3],'pchd':d[4],'name':nm.decode('latin1')}
def dem(nm):
    b=nm[4:] if nm.startswith('.?A') else nm
    return b[:-2] if b.endswith('@@') else b
def bcd(a):
    if a is None or where(a)!='.rdata': return None
    d=[dw(a+4*i) for i in range(6)]
    if None in d or where(d[0])!='.data': return None
    return {'va':a,'ptd':d[0],'ncbase':d[1],'mdisp':d[2],'pdisp':d[3]}
S=json.load(open('/home/t628/projects/ra2-campaign-forge/out/reverse/symbols.json'))['classes']
t12=[]; rows=[]
for k,c in S.items():
    if c['vtable_va'] is None: continue
    vt=int(c['vtable_va'],16); r=colrec(dw(vt-4))
    if r['mdisp']!=4: continue
    t12.append(k)
    ch=r['pchd']; nb=dw(ch+8); arr=dw(ch+12)
    ent=[]
    for i in range(nb):
        b=bcd(dw(arr+4*i))
        ent.append((dem(cstr(b['ptd']+8).decode('latin1')),b['mdisp'],b['pdisp'],b['ncbase']))
    il=[e for e in ent if e[0]=='ILocomotion']
    rows.append({'cls':k,'vt':vt,'nbase':nb,'iloco':il,'bases_match':[e[0] for e in ent]==c['bases'],'ent':ent})
ck('Y1 主 COL.mdisp==4 的类恰 12 个', len(t12)==12, t12)
ck('Y2 12 个全是 Locomotion 系（类名以 LocomotionClass 结尾）', all(k.endswith('LocomotionClass') for k in t12), t12)
ck('Y3 每个类的 BCD 里都有且仅有 1 项 ILocomotion', all(len(r['iloco'])==1 for r in rows), [(r['cls'],len(r['iloco'])) for r in rows if len(r['iloco'])!=1])
ck('Y4 该 ILocomotion 项的 mdisp 恒为 4（12/12，且与主 COL.mdisp 同值）',
   all(r['iloco'][0][1]==4 for r in rows), [r['iloco'][0][1] for r in rows])
ck('Y5 该 ILocomotion 项 pdisp 恒为 0xFFFFFFFF（非虚基类）', all(r['iloco'][0][2]==0xFFFFFFFF for r in rows), [hex(r['iloco'][0][2]) for r in rows])
ck('Y6 BCD 名字序列 == symbols.json bases 列表 12/12', all(r['bases_match'] for r in rows), [r['cls'] for r in rows if not r['bases_match']])
# 反控
old=P.RAW
b=bytearray(old)
# LocomotionClass BCD 中 ILocomotion 项的 mdisp 改成 0
loc=[r for r in rows if r['cls']=='LocomotionClass'][0]
ch=colrec(dw(loc['vt']-4))['pchd']; arr=dw(ch+12); nb=dw(ch+8)
idx=[i for i in range(nb) if dem(cstr(bcd(dw(arr+4*i))['ptd']+8).decode('latin1'))=='ILocomotion'][0]
entry=dw(arr+4*idx)
P.RAW=bytes(b)
import struct
bb=bytearray(P.RAW); struct.pack_into('<I',bb,r2o(entry)+8,0)
P.RAW=bytes(bb)
v=bcd(entry)
ck('Y7 反控 把 ILocomotion BCD.mdisp 4->0 => Y4 红', v['mdisp']==0, v['mdisp'])
P.RAW=old
ck('Y8 复原后 mdisp 回到 4', bcd(entry)['mdisp']==4, bcd(entry)['mdisp'])
json.dump({'checks':n,'fails':fails,'twelve':t12,'rows':[{'cls':r['cls'],'nbase':r['nbase'],'iloco':r['iloco']} for r in rows]},
          open('/home/t628/projects/ra2-campaign-forge/_r185/r185y.json','w'),ensure_ascii=False,indent=1)
print('CHECKS',n,'FAILS',fails)
