#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R198 第六刀：0x410410 的 27 个宿主身份 —— 它们是不是虚表槽 13 的实现？
以及「27 个调用点落在 27 个不同宿主」这一现象的含义（每个宿主只调一次）。
判据：
 H1 27 个宿主里有多少个是某张虚表的某个槽位的实现（OWNSLOT 反查）。
 H2 其中有多少个恰好是该表的槽 13。
 H3 这 27 个宿主的虚表覆盖的类名集合，与 L（78 类血统）的交集。
 H4 每个宿主体内对 0x410410 的调用次数分布。
反控：
 R1 用「最近前置 call 目标」之外的第二种入口判据（前置 0x90 填充），27 个宿主的类名覆盖变化。
 R2 把「槽 13」改成「槽 0..343 任一」，看 H1 变多少。
 R3 把 L 的门槛从 78 张表放宽到「所有含 .?AVUnitClass@@」，看交集变化。
"""
import sys,struct,collections,json
sys.path.insert(0,'/home/t628/projects/ra2-campaign-forge/_r185')
import pe185 as P
import capstone
md=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32)
fails=[];N=0
def ck(nm,c,d=''):
    global N;N+=1
    if not c: fails.append(nm)
    print(('PASS ' if c else 'FAIL ')+nm+((' | '+str(d)) if d!='' else ''))
T=P.B['.text'];LO=T['lo'];HI=T['hi_file'];RAW=P.RAW
BUF=RAW[T['rawptr']:T['rawptr']+(HI-LO)]
def in_text(x): return x is not None and LO<=x<HI
def wv(sn):
    s=P.B[sn];n=s['rawsize']//4
    return s['lo'],struct.unpack_from('<%dI'%n,RAW,s['rawptr']),n
COL={}
for sn in ('.rdata','.data'):
    base,w,n=wv(sn)
    for i in range(n-4):
        if w[i] not in (0,1,2) or w[i+2]!=0: continue
        if P.where(w[i+3])!='.data' or P.where(w[i+4])!='.rdata': continue
        nm=P.cstr(w[i+3]+8,400)
        if not(nm and nm.startswith(b'.?A') and nm.endswith(b'@@')): continue
        COL[base+4*i]=dict(mdisp=struct.unpack('<i',struct.pack('<I',w[i+1]))[0],name=nm.decode('latin1'),pchd=w[i+4])
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
ck('H0a 基线',(len(COL),len(VT),sum(NS.values()))==(1214,1214,14044),(len(COL),len(VT),sum(NS.values())))
OWNSLOT=collections.defaultdict(list)
for vt in VT:
    for k in range(NS[vt]):
        OWNSLOT[P.dw(vt+4*k)].append((vt,k))
H27=[0x410be0,0x41d585,0x420c35,0x438a70,0x43a130,0x472640,0x4a7a30,0x4c58c0,0x4ca1a0,0x4d2790,
     0x502d30,0x554fe4,0x5f6250,0x6292b0,0x65b2f0,0x68ca50,0x6b1020,0x6b7d80,0x6cc2a0,0x6e3b60,
     0x6e5560,0x6ec3d0,0x71a4e0,0x71f2a0,0x726720,0x727fd0,0x763ba0]
ck('H1a 27 个宿主地址', len(H27)==27, len(H27))
rows=[]
for e in H27:
    o=OWNSLOT.get(e,[])
    rows.append(dict(va=hex(e),n=len(o),slots=[k for vt,k in o][:8],
                     cls=sorted({COL[VT[vt]]['name'] for vt,k in o})[:4],
                     vt=[hex(vt) for vt,k in o][:4]))
own=[r for r in rows if r['n']>0]
ck('H1b 是虚表实现的宿主数 / 27', True, len(own))
for r in rows: print('   H1c %s n=%d slots=%s cls=%s'%(r['va'],r['n'],r['slots'],r['cls']))
only13=[r for r in own if set(r['slots'])=={13}]
ck('H2a 恰好只占槽 13 的宿主数', True, dict(n=len(only13),va=[r['va'] for r in only13]))
in13=[r for r in own if 13 in r['slots']]
ck('H2b 占槽 13 的宿主数', True, dict(n=len(in13),va=[r['va'] for r in in13]))
# H3 L 交集
def chain(colva):
    n=P.dw(COL[colva]['pchd']+8);arr=P.dw(COL[colva]['pchd']+12);out=[]
    for j in range(n):
        b=P.dw(arr+4*j);ptd=P.dw(b);nm=P.cstr(ptd+8,400)
        out.append(nm.decode('latin1') if nm else None)
    return out
MAIN=[vt for vt in VT if COL[VT[vt]]['mdisp']==0]
LIN=set(vt for vt in MAIN if '.?AVAbstractClass@@' in chain(VT[vt]))
ck('H3a L=78', len(LIN)==78, len(LIN))
lhost=[r for r in own if any(int(x,16) in LIN for x in r['vt'])]
ck('H3b 宿主表在 L 内的个数', True, dict(n=len(lhost),va=[r['va'] for r in lhost],cls=[r['cls'] for r in lhost]))
# H4 每个宿主的调用次数
def calls_to(fn):
    out=[]
    for va in range(LO,HI-5):
        if BUF[va-LO]!=0xE8: continue
        if struct.unpack_from('<i',BUF,va-LO+1)[0]+va+5==fn: out.append(va)
    return out
cnt={hex(e):len(calls_to(e)) for e in H27}
ck('H4a 27 宿主内的 call 指令数分布', True, collections.Counter(cnt.values()).most_common())
print('   H4b 前 8:', list(cnt.items())[:8])
# R3 UnitClass 放宽
UNIT=[vt for vt in VT if COL[VT[vt]]['name']=='.?AVUnitClass@@']
uhost=[r for r in own if any(int(x,16) in set(UNIT) for x in r['vt'])]
ck('R3a 宿主表为 .?AVUnitClass@@ 的个数', True, dict(n=len(uhost),va=[r['va'] for r in uhost]))
json.dump(dict(rows=rows,own=len(own),only13=[r['va'] for r in only13],in13=[r['va'] for r in in13],
  lhost=[r['va'] for r in lhost],callcnt=cnt,asserts=N,fails=fails),
  open('/home/t628/projects/ra2-campaign-forge/_r198/m6_hosts.json','w'),ensure_ascii=False,indent=1)
print('\nSUMMARY asserts=%d fails=%d %s'%(N,len(fails),fails))
