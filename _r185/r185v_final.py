#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R185 V：gamemd.exe 类对象模型（vtable / COL / TypeDescriptor / ClassHierarchyDescriptor）
的字节级全量复原与可失败核验。全部数字实测，正反控同脚本。

结构定义（MSVC RTTI，逐字节确认后的形状）：
  COL  = 5 dwords { signature∈{0,1}, mdisp, pdisp, pTD∈.data, pCHD∈.rdata }
  TD   = { pVFTable==0x7F9594, spare==0, name = b'.?A[VU]' <demangled> b'@@' }
  CHD  = { signature==0, attributes, numBase>=1, pBaseArray∈.rdata }
  BCD  = 6 dwords { pTD, numContainedBases, mdisp, pdisp(0xFFFFFFFF=虚基类标记), pmdisp, attributes }
  vtable = 连续 .text 函数指针槽，其 **前一个 dword** 是主 COL（mdisp==0）
"""
import sys,json,struct,collections
sys.path.insert(0,'/home/t628/projects/ra2-campaign-forge/_r185')
import pe185 as P
dw=P.dw; where=P.where; cstr=P.cstr; r2o=P.r2o
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
    return {'va':a,'sig':d[0],'mdisp':d[1],'pdisp':d[2],'ptd':d[3],'pchd':d[4],'name':nm.decode('latin1')}
def td(a):
    if a is None or where(a)!='.data': return None
    pvf,sp=struct.unpack_from('<II',P.RAW,r2o(a))
    nm=cstr(a+8)
    return {'va':a,'pvf':pvf,'spare':sp,'name':nm.decode('latin1') if nm else None}
def chdrec(a):
    if a is None or where(a)!='.rdata': return None
    d=[dw(a+4*i) for i in range(4)]
    if None in d or d[0]!=0 or d[2]<1 or where(d[3])!='.rdata': return None
    return {'va':a,'sig':d[0],'attr':d[1],'nbase':d[2],'arr':d[3]}
def bcdrec(a):
    if a is None or where(a)!='.rdata': return None
    d=[dw(a+4*i) for i in range(6)]
    if None in d or where(d[0])!='.data': return None
    return {'va':a,'ptd':d[0],'ncbase':d[1],'mdisp':d[2],'pdisp':d[3],'pmdisp':d[4],'attr':d[5]}
def dem(n):
    b=n[4:] if n.startswith('.?A') else n
    return b[:-2] if b.endswith('@@') else b
def textrun(vt):
    k=0
    while where(dw(vt+4*k))=='.text': k+=1
    return k

S=json.load(open('/home/t628/projects/ra2-campaign-forge/out/reverse/symbols.json'))
CL=S['classes']
ok=[(k,c) for k,c in CL.items() if c['vtable_va'] is not None]
ck('V1 类 988 条 / 有 vtable 954 / 无 34', len(CL)==988 and len(ok)==954, (len(CL),len(ok)))

# ---- A: 主 COL 链 954/954 ----
bad=[]; mdisp=collections.Counter(); sig=collections.Counter()
prim={}
for k,c in ok:
    vt=int(c['vtable_va'],16); pre=dw(vt-4); r=colrec(pre)
    if not r: bad.append((k,hex(vt))); continue
    prim[k]=r; mdisp[r['mdisp']]+=1; sig[r['sig']]+=1
ck('V2 A vtable-4 是合法主 COL 954/954', not bad, 'bad=%d %s'%(len(bad),bad[:3]))
ck('V3 A 主 COL.mdisp 分布 == {0:942, 4:12}（12 条非 0，逐条登记）', mdisp[0]==942 and mdisp[4]==12 and len(mdisp)==2, dict(mdisp))
ck('V4 A 主 COL signature 只有 0 与 1', set(sig)<={0,1}, dict(sig))

# ---- B: TD 名 == 类名 ----
badn=[]; badpvf=0
for k,c in ok:
    r=prim[k]; t=td(r['ptd'])
    if not t or dem(t['name'])!=c['name']: badn.append((k,t and t['name']))
    if t and (t['pvf']!=0x7F9594 or t['spare']!=0): badpvf+=1
ck('V5 B 主 COL->TD 名（去 .?AV@@）== name 列 954/954', not badn, 'bad=%d %s'%(len(badn),badn[:3]))
ck('V6 B TD.pVFTable==0x7F9594 且 spare==0 954/954', badpvf==0, badpvf)
ck('V7 B symbols.json 的 type_descriptor_va 与主 COL.pTD 一致', all(int(c['type_descriptor_va'],16)==prim[k]['ptd'] for k,c in ok),
   sum(1 for k,c in ok if int(c['type_descriptor_va'],16)!=prim[k]['ptd']))

# ---- C: 槽数与逐槽 ----
badc=[]
for k,c in ok:
    vt=int(c['vtable_va'],16); tr=textrun(vt)
    if tr!=c['vfunc_count'] or [dw(vt+4*i) for i in range(tr)]!=[int(x,16) for x in c['vfuncs']]: badc.append((k,c['vfunc_count'],tr))
ck('V8 C vfunc_count + 逐槽 == 字节 954/954', not badc, 'bad=%d %s'%(len(badc),badc[:3]))
tot=sum(c['vfunc_count'] for _,c in ok)
ck('V9 C 954 个 vtable 共 %d 个函数指针槽'%tot, tot>0, tot)

# ---- D: 双 COL（symbols.json col_va vs vtable-4）----
same=0; pairs=[]
for k,c in ok:
    cv=int(c['col_va'],16); p=prim[k]['va']
    r2=colrec(cv)
    if cv==p: same+=1; continue
    pairs.append((k,p,cv,prim[k]['mdisp'],r2 and r2['mdisp'],prim[k]['ptd']==(r2 and r2['ptd']),
                  dem(prim[k]['name'])==(r2 and dem(r2['name']))))
ck('V10 D col_va == vtable-4 主 COL 的条数', same==866, same)
ck('V11 D 88 条不一致者：两 COL 的 pTD 全同且类名全同（仅 mdisp 不同）',
   all(x[5] and x[6] and x[3]!=x[4] for x in pairs), 'n=%d mdisp对=%s'%(len(pairs),collections.Counter((x[3],x[4]) for x in pairs).most_common(5)))
ck('V12 D 88 条不一致者：两 COL 的 pCHD 全同（同属一个类层次组）',
   all(colrec(int(CL[k]['col_va'],16))['pchd']==prim[k]['pchd'] for k,_,_,_,_,_,_ in pairs),
   'n=%d'%len(pairs))
ck('V12b D 次 COL 的 mdisp 全都 != 主 COL 的 mdisp 且 > 0', all(x[4]>0 and x[4]!=x[3] for x in pairs),
   dict(collections.Counter(x[4] for x in pairs)))

# ---- E: CHD / BCD 链 ----
badch=[]; totbase=0
for k,c in ok:
    r=prim[k]; ch=chdrec(r['pchd'])
    if not ch: badch.append((k,hex(r['pchd']))); continue
    totbase+=ch['nbase']
    arr=[dw(ch['arr']+4*i) for i in range(ch['nbase'])]
    if any(bcdrec(a) is None for a in arr): badch.append((k,'bcd'))
ck('V13 E 954 条主 COL 的 CHD 与 BCD 数组全可解', not badch, 'bad=%d %s'%(len(badch),badch[:3]))
ck('V14 E BCD 条目总数 = %d'%totbase, totbase>0, totbase)
# AbstractClass 逐名
r=prim['AbstractClass']; ch=chdrec(r['pchd'])
arr=[dw(ch['arr']+4*i) for i in range(ch['nbase'])]
bcds=[bcdrec(a) for a in arr]
names=[dem(td(b['ptd'])['name']) for b in bcds]
c=CL['AbstractClass']
ck('V15 E AbstractClass nbase==8 == len(bases)', ch['nbase']==8 and len(c['bases'])==8, (ch['nbase'],len(c['bases'])))
ck('V16 E AbstractClass 8 个 BCD 名（顺序）== symbols.json bases 列表', names==c['bases'], names)
ck('V17 E AbstractClass BCD[0].pTD == 自身主 COL.pTD（自指）', bcds[0]['ptd']==r['ptd'], (hex(bcds[0]['ptd']),hex(r['ptd'])))
ck('V18 E AbstractClass 根 BCD.numContainedBases == nbase-1 == 7',
   bcds[0]['ncbase']==7, [(b['ncbase'],b['mdisp']) for b in bcds])
ck('V18b E AbstractClass 8 个 BCD 的 pdisp 全为 0xFFFFFFFF（无虚基类）',
   all(b['pdisp']==0xFFFFFFFF for b in bcds), [hex(b['pdisp']) for b in bcds])
ck('V18c E AbstractClass 8 个 BCD 的 mdisp == [0,0,0,0,4,4,8,12]',
   [b['mdisp'] for b in bcds]==[0,0,0,0,4,4,8,12], [b['mdisp'] for b in bcds])
print('NOTE AbstractClass BCD (ncbase,mdisp,pdisp):',[(b['ncbase'],b['mdisp'],hex(b['pdisp'])) for b in bcds])

# ---- F: 反控 ----
def withb(mut):
    b=bytearray(P.RAW); mut(b)
    old=P.RAW; P.RAW=bytes(b)
    return old
def restore(old):
    P.RAW=old
old=withb(lambda b: struct.pack_into('<I',b,r2o(0x7FB118),2))
ck('V19 反控 主 COL.sig 0->2 => A 红', colrec(0x7FB118) is None); restore(old)
def m2(b):
    o=r2o(0x8177C8)+8; b[o+5]^=1   # 命中类名首字母 'A'（偏移 +8+4 是 '.?AV' 的 V，改它不触发）
old=withb(m2); ck('V20 反控 TD 名改 1 字节 => B 红', dem(td(0x8177C8)['name'])!='AbstractClass', dem(td(0x8177C8)['name'])); restore(old)
ck('V21 反控 vtable+4 => dword@-4 落在 .text（A 红）', where(dw(0x7E1F54-4))=='.text', hex(dw(0x7E1F54-4)))
ck('V22 反控 期望槽数 27 => C 红', textrun(0x7E1F50)!=27, textrun(0x7E1F50))
old=withb(lambda b: struct.pack_into('<I',b,r2o(0x7FB110),7))
ck('V23 反控 CHD.numBase 8->7 => E 红（nbase!=len(bases)）', chdrec(0x7FB108)['nbase']!=8, chdrec(0x7FB108)['nbase']); restore(old)
old=withb(lambda b: struct.pack_into('<I',b,r2o(0x7FB0E0),0x7E1000))
ck('V24 反控 BCD[0].pTD 指到 .rdata => E 红', bcdrec(0x7FB0E0) is None or where(bcdrec(0x7FB0E0)['ptd'])!='.data'); restore(old)

out={'checks':n,'fails':fails,'mdisp':{str(k):v for k,v in mdisp.items()},'sig':{str(k):v for k,v in sig.items()},
     'same_col':same,'pairs_mdisp':{str(k):v for k,v in collections.Counter(x[4] for x in pairs).items()},
     'total_slots':tot,'total_bcd':totbase,'abs_bases':names}
json.dump(out,open('/home/t628/projects/ra2-campaign-forge/_r185/r185v.json','w'),ensure_ascii=False,indent=1)
print('CHECKS',n,'FAILS',fails)
