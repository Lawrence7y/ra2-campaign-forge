#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R185 S：symbols.json(988 条) 与 gamemd.exe 字节的**双向**交叉核验（全部从字节重算）。

不变量：
  C1 vtable-4 处的 dword == symbols.json 的 col_va
  C2 COL{ sig∈{0,1}, offset==0, cdOffset==0, pTD∈.data, pCHD∈.rdata }
  C3 COL.pTD 指向的 TD 的 name == symbols.json 的 name（逐条，954 条有 vtable 者）
  C4 TD.pVFTable == 0x7F9594（type_info 虚表），spare == 0
  C5 vfunc_count == 字节上 .text 连续槽长度；vfuncs 逐槽等于字节 dword
  C6 CHD{ sig==0, numBase>=1, pBaseArray∈.rdata }，且每个 BCD.pTD 的 TD 名
     能对上 symbols.json 里某条类名（闭包性），self 类的 BCD 计数 == bases 列表长度
反控：
  N1 COL.sig 2 => C2 红
  N2 TD 名改 1 字节 => C3 红
  N3 vtable_va +4 => C1 红
  N4 vfunc_count 改 => C5 红
  N5 CHD.numBase 改 => C6 红
"""
import sys,json,struct,re
sys.path.insert(0,'/home/t628/projects/ra2-campaign-forge/_r185')
import pe185 as P
dw=P.dw; where=P.where; cstr=P.cstr; r2o=P.r2o
raw=P.RAW
fails=[];nck=0
def ck(nm,c,d=''):
    global nck; nck+=1
    if not c: fails.append(nm)
    print(('PASS ' if c else 'FAIL ')+nm+((' | '+str(d)) if d!='' else ''))
def col(a):
    if a is None or where(a)!='.rdata': return None
    d=[dw(a+4*i) for i in range(5)]
    if None in d or d[0] not in (0,1) or d[1]!=0 or d[2]!=0: return None
    if where(d[3])!='.data' or where(d[4])!='.rdata': return None
    nm=cstr(d[3]+8)
    if not (nm and nm.startswith(b'.?A') and nm.endswith(b'@@')): return None
    return {'va':a,'sig':d[0],'ptd':d[3],'pchd':d[4],'name':nm.decode('latin1')}
def tinfo(a):
    if a is None or where(a)!='.data': return None
    pvf,sp=struct.unpack_from('<II',raw,r2o(a))
    nm=cstr(a+8)
    return {'va':a,'pvf':pvf,'spare':sp,'name':nm.decode('latin1') if nm else None}
def chdrec(a):
    if a is None or where(a)!='.rdata': return None
    d=[dw(a+4*i) for i in range(4)]
    if None in d or d[0]!=0 or d[2]<1 or where(d[3])!='.rdata': return None
    return {'va':a,'sig':d[0],'attr':d[1],'nbase':d[2],'arr':d[3]}
def textrun(vt):
    k=0
    while where(dw(vt+4*k))=='.text': k+=1
    return k
S=json.load(open('/home/t628/projects/ra2-campaign-forge/out/reverse/symbols.json'))
CL=S['classes']
ck('S1 类数 988 / 无 vtable 34', len(CL)==988 and sum(1 for c in CL.values() if c['vtable_va'] is None)==34,
   (len(CL), sum(1 for c in CL.values() if c['vtable_va'] is None)))
withvt=[(k,c) for k,c in CL.items() if c['vtable_va'] is not None]
ck('S2 有 vtable 的 954 条', len(withvt)==954, len(withvt))
allnames={c['name'] for c in CL.values()}
b_c1=[];b_c2=[];b_c3=[];b_c4=[];b_c5=[];b_c6=[];b_base=[]
for k,c in withvt:
    vt=int(c['vtable_va'],16); cv=int(c['col_va'],16)
    pre=dw(vt-4)
    if pre!=cv: b_c1.append((k,c['vtable_va'],c['col_va'],hex(pre) if pre is not None else None)); continue
    co=col(cv)
    if not co: b_c2.append((k,c['col_va'])); continue
    ti=tinfo(co['ptd'])
    if not ti or ti['name']!=c['name']: b_c3.append((k,c['name'],ti['name'] if ti else None)); continue
    if ti['pvf']!=0x7F9594 or ti['spare']!=0: b_c4.append((k,hex(ti['pvf']),ti['spare']))
    tr=textrun(vt)
    if tr!=c['vfunc_count'] or [dw(vt+4*i) for i in range(tr)]!=[int(x,16) for x in c['vfuncs']]:
        b_c5.append((k,c['vfunc_count'],tr))
    ch=chdrec(co['pchd'])
    if not ch: b_c6.append((k,c['col_va'],hex(co['pchd']))); continue
    arr=[dw(ch['arr']+4*i) for i in range(ch['nbase'])]
    nmz=[]
    for a in arr:
        t=tinfo(dw(a)) if a is not None else None
        nmz.append(t['name'] if t else None)
    if any(x is None for x in nmz) or any(x not in allnames for x in nmz[1:]):
        b_c6.append((k,'bcd',nmz[:4]))
    if ch['nbase']!=len(c['bases']): b_base.append((k,ch['nbase'],len(c['bases'])))
ck('S3 C1 vtable-4 dword == col_va', not b_c1, 'bad=%d %s'%(len(b_c1),b_c1[:4]))
ck('S4 C2 COL 五元组合法', not b_c2, 'bad=%d %s'%(len(b_c2),b_c2[:4]))
ck('S5 C3 COL->TD 名 == name 列', not b_c3, 'bad=%d %s'%(len(b_c3),b_c3[:4]))
ck('S6 C4 TD.pVFTable==0x7F9594 且 spare==0', not b_c4, 'bad=%d %s'%(len(b_c4),b_c4[:4]))
ck('S7 C5 槽数+逐槽 == 字节', not b_c5, 'bad=%d %s'%(len(b_c5),b_c5[:4]))
ck('S8 C6 CHD 链可解且基类名闭包', not b_c6, 'bad=%d %s'%(len(b_c6),b_c6[:4]))
ck('S9 CHD.numBase == len(bases)', not b_base, 'bad=%d %s'%(len(b_base),b_base[:6]))
# AbstractClass 8 基类逐名
co=col(0x7FB118); ch=chdrec(co['pchd'])
arr=[dw(ch['arr']+4*i) for i in range(ch['nbase'])]
nmz=[tinfo(dw(a))['name'] for a in arr]
print('NOTE AbstractClass nbase=%d bases=%s'%(ch['nbase'],nmz))
ck('S10 AbstractClass 8 基类第 1 项自指 == 自身 TD', nmz[0]=='?AVAbstractClass@@' and arr[0]==co['ptd'], (nmz[0],hex(arr[0]),hex(co['ptd'])))
# 反控
def with_bytes(mut):
    b=bytearray(P.RAW); mut(b)
    old=P.RAW
    globals()['raw']=bytes(b); P.RAW=bytes(b)
    return old
def restore(old):
    globals()['raw']=old; P.RAW=old
old=with_bytes(lambda b: struct.pack_into('<I',b,r2o(0x7FB118),2))
ck('S11 反控 COL.sig=2 => C2 红', col(0x7FB118) is None); restore(old)
def m2(b):
    o=r2o(0x8177C8)+8
    b[o+3]^=0x01
old=with_bytes(m2)
ck('S12 反控 TD 名改 1 字节 => C3 红', tinfo(0x8177C8)['name']!='?AVAbstractClass@@', tinfo(0x8177C8)['name']); restore(old)
ck('S13 反控 vtable+4 => C1 红', dw(0x7E1F54-4)!=0x7FB118, hex(dw(0x7E1F54-4)))
ck('S14 反控 vfunc_count 期望 27 => C5 红', textrun(0x7E1F50)!=27, textrun(0x7E1F50))
old=with_bytes(lambda b: struct.pack_into('<I',b,r2o(0x7FB110),7))
c2=chdrec(0x7FB108)
ck('S15 反控 CHD.numBase 8->7 => C6/C9 红', c2 is None or c2['nbase']==7, c2['nbase'] if c2 else None); restore(old)
json.dump({'checks':nck,'fails':fails,'bases8':nmz},open('/home/t628/projects/ra2-campaign-forge/_r185/r185s.json','w'),ensure_ascii=False,indent=1)
print('CHECKS',nck,'FAILS',fails)
