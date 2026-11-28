#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R198 第二刀：0x7F5C70 的 344 个实现「互不相同」这一结果的深入取证。
 Q1 NO_RET_WIN 34 个实现是什么（体长 / 是否为 thunk / 窗口外是否有 ret）。
 Q2 344 个实现的地址分布（是否集中在某段、是否都前有 0x90 填充 = 函数入口）。
 Q3 与 L 的 78 张表对比：0x7F5C70 的 uniq/N 与 L 的 Top1 覆盖率的反差，用同口径重算 L。
 Q4 去掉 0x7F5C70 后，其他 1213 张表的 uniq/N 分布。
反控：
 R1 把「前有 0x90 填充」判据换成「前 16 字节内有 ret 或 int3」，入口数变化。
 R2 把窗口从 400 字节放宽到 4096 字节，NO_RET_WIN 变成几个。
 R3 把 uniq 判据从「目标地址不同」改成「目标体字节前 16 字节不同」，uniq 变成多少。
"""
import sys, struct, collections, json
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
    n=P.dw(COL[colva]['pchd']+8); arr=P.dw(COL[colva]['pchd']+12); out=[]
    for j in range(n):
        b=P.dw(arr+4*j)
        ptd=P.dw(b); nm=P.cstr(ptd+8,400)
        out.append(nm.decode('latin1') if nm else None)
    return out
MAIN=[vt for vt in VT if COL[VT[vt]]['mdisp']==0]
LIN=sorted(vt for vt in MAIN if '.?AVAbstractClass@@' in chain(VT[vt]))
ck('Q0a COL=1214 VT=1214 槽总=14044 L=78',(len(COL),len(VT),sum(NS.values()),len(LIN))==(1214,1214,14044,78),
   (len(COL),len(VT),sum(NS.values()),len(LIN)))
VT_C=0x7F5C70; SLOTS=[P.dw(VT_C+4*k) for k in range(344)]
def body(va,lim=400):
    o=P.r2o(va); out=[]
    for i in md.disasm(RAW[o:o+lim],va):
        out.append(i)
        if i.mnemonic=='ret': break
    return out
# Q1 NO_RET_WIN
noret=[a for a in SLOTS if not any(i.mnemonic=='ret' for i in body(a,400))]
ck('Q1a 400B 窗口内无 ret 的实现数', len(noret)==34, len(noret))
def body_long(va,lim=4096):
    o=P.r2o(va); out=[]
    for i in md.disasm(RAW[o:o+lim],va):
        out.append(i)
        if i.mnemonic=='ret': break
    return out
info=[]
for a in noret:
    B=body_long(a,4096)
    has=any(i.mnemonic=='ret' for i in B)
    last=B[-1] if B else None
    info.append(dict(va=hex(a),long_ret=has,nins=len(B),ln=(B[-1].address+B[-1].size-a) if B else 0,
                     last=(last.mnemonic+' '+last.op_str) if last else None,
                     first=(B[0].mnemonic+' '+B[0].op_str) if B else None))
ck('Q1b 4096B 窗口下仍无 ret 的个数', True, sum(1 for x in info if not x['long_ret']))
print('   Q1c 前 8 个:', info[:8])
print('   Q1d 体长分布:', collections.Counter(x['ln']//64*64 for x in info).most_common(8))
# Q2 地址分布
hips=collections.Counter((a>>16) for a in SLOTS)
ck('Q2a 344 目标的 64KB 页分布 top6', True, [(hex(k<<16),v) for k,v in hips.most_common(6)])
def is_entry(a):
    o=P.r2o(a)
    if o is None: return False
    return o>=8 and RAW[o-1]==0x90
ent=sum(1 for a in SLOTS if is_entry(a))
ck('Q2b 前 1 字节是 0x90 的实现数', True, ent)
def is_entry2(a):
    o=P.r2o(a)
    if o is None or o<16: return False
    return any(b in (0xC3,0xCC) for b in RAW[o-16:o])
ent2=sum(1 for a in SLOTS if is_entry2(a))
ck('R1a 前 16 字节含 ret/int3 的实现数', True, ent2)
ck('Q2c 344 个目标是否全在 .text', all(in_text(a) for a in SLOTS), True)
ck('Q2d 目标地址是否单调递增', all(SLOTS[i]<SLOTS[i+1] for i in range(343)),
   sum(1 for i in range(343) if SLOTS[i]<SLOTS[i+1]))
# Q3 L 对比
lut={}
for vt in LIN:
    s=[P.dw(vt+4*k) for k in range(NS[vt])]
    lut[vt]=s
tot=uniq=0; per=[]
for vt,s in lut.items():
    u=len(set(s)); tot+=len(s); uniq+=u
    per.append((vt,len(s),u))
ck('Q3a L 的 78 张表 uniq/槽数', True, (uniq,tot))
print('   Q3b L 里 uniq/N == 1.0 的表数:', sum(1 for v,n,u in per if u==n), '/', len(per))
print('   Q3c L 里 uniq/N 最低的 6 张:', sorted([(hex(v),n,u,round(u/n,3)) for v,n,u in per],key=lambda x:x[3])[:6])
# Q4 全表 uniq/N
rows=[]
for vt in VT:
    s=[P.dw(vt+4*k) for k in range(NS[vt])]
    if not s: continue
    rows.append((vt,NS[vt],len(set(s))))
full1=[r for r in rows if r[1]==r[2]]
ck('Q4a 全 1214 张表里 uniq==N 的表数', True, len(full1))
ck('Q4b 全 1214 张表里 344 槽表 uniq==N', (VT_C,344,344) in rows, (VT_C,344,344) in rows)
buck=collections.Counter(round(r[2]/r[1],1) for r in rows)
ck('Q4c uniq/N 分布 top8', True, sorted(buck.items())[:8])
# R2/R3
b16=collections.Counter(RAW[P.r2o(a):P.r2o(a)+16] for a in SLOTS)
ck('R3a 前 16 字节去重后的个数', len(b16)==344, len(b16))
print('\nSUMMARY asserts=%d fails=%d %s'%(N,len(fails),fails))
json.dump(dict(noret=info,hips={hex(k):v for k,v in hips.items()},ent=ent,ent2=ent2,
  lut_full1=len(full1),lut=[(hex(v),n,u) for v,n,u in per],
  b16=len(b16),asserts=N,fails=fails),
  open('/home/t628/projects/ra2-campaign-forge/_r198/m2_vtslot2.json','w'),ensure_ascii=False,indent=1)
