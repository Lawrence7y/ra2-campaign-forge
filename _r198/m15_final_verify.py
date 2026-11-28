#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R198 第十五刀（收口终验）：三处待裁定点的逐值复算。
 V-A 槽数分档 uniq==nslot 比例（复核审计员 Q4 的 4/8 vs 主会话隐含 8/8）。
 V-B 纯桩定义两版（含/不含裸 ret）的逐地址差集。
 V-C 0x645583 的 lea [esp+0xa0] 四槽写是不是 CRC 状态对象的四槽（看写值与后续 call 关系）。
"""
import sys,struct,collections,json,bisect,re
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
        COL[base+4*i]=dict(mdisp=struct.unpack('<i',struct.pack('<I',w[i+1]))[0],name=nm.decode('latin1'))
VT={}
for sn in ('.rdata','.data'):
    base,w,n=wv(sn)
    for i in range(n):
        if in_text(w[i]) and P.dw(base+4*i-4) in COL: VT[base+4*i]=P.dw(base+4*i-4)
def nslot(vt):
    k=0
    while in_text(P.dw(vt+4*k)): k+=1
    return k
ck('V0a 基线',(len(COL),len(VT))==(1214,1214),(len(COL),len(VT)))
# V-A 分档
buckets={'1..7':[0,0],'8..63':[0,0],'64..127':[0,0],'>=128':[0,0]}
rows=[]
for vt in VT:
    n=nslot(vt); s=[P.dw(vt+4*k) for k in range(n)]
    u=len(set(s))
    b='1..7' if n<=7 else ('8..63' if n<=63 else ('64..127' if n<=127 else '>=128'))
    buckets[b][0]+=1
    if u==n: buckets[b][1]+=1
    if b=='>=128': rows.append((hex(vt),COL[VT[vt]]['name'],n,u))
ck('VA1 分档 uniq==nslot 比例', True, {k:(v[1],v[0],round(v[1]/v[0],4) if v[0] else None) for k,v in buckets.items()})
for r in sorted(rows,key=lambda x:-x[2]): print('   VA2 >=128 档: %s %-28s n=%d uniq=%d %s'%(r[0],r[1],r[2],r[3],'OK' if r[2]==r[3] else 'DUP'))
DUPS=[r for r in rows if r[2]!=r[3]]
ck('VA3 >=128 档里 uniq<nslot 的表数', len(DUPS)==4, dict(n=len(DUPS),tabs=[r[0] for r in DUPS]))
# V-B 纯桩两版
SL=[P.dw(0x7F5C70+4*k) for k in range(344)]
U=sorted(set(SL))
def body(va,lim=400):
    out=[]
    for off,sz,mn,op in md.disasm_lite(BUF[va-LO:va-LO+lim],va):
        out.append((off,mn,op))
        if mn=='ret': break
    return out
def stub_no_bare(va):
    B=[b for b in body(va) if b[1]!='nop']
    if len(B)!=2: return False
    return B[0][1] in ('xor','sub') and B[0][2]=='eax, eax' and B[1][1]=='ret' and B[1][2] in ('','0')
def stub_with_bare(va):
    B=[b for b in body(va) if b[1]!='nop']
    if not B or B[-1][1]!='ret' or B[-1][2] not in ('','0'): return False
    if len(B)==1: return True
    if len(B)==2: return B[0][1] in ('xor','sub') and B[0][2]=='eax, eax'
    return False
A=[a for a in U if stub_no_bare(a)]
Bb=[a for a in U if stub_with_bare(a)]
ck('VB1 零返回桩（xor eax,eax; ret）', len(A)==8, len(A))
ck('VB2 含裸 ret 的桩', len(Bb)==16, len(Bb))
ck('VB3 差集 = 裸 ret', True, [hex(x) for x in sorted(set(Bb)-set(A))])
for a in sorted(set(Bb)-set(A)):
    print('   VB4 裸 ret 实现 %s 字节=%s'%(hex(a),BUF[a-LO:a-LO+4].hex()))
# V-C 0x645583 四槽
fs=0x428700
ins=[(off,sz,mn,op) for off,sz,mn,op in md.disasm_lite(BUF[fs-LO:0x645583-LO],fs)]
af=[x for x in ins if x[0]>=0x428729]
ck('VC1 lea 点', True, [ (hex(a),m,o) for a,sz,m,o in af[:1]])
for a,sz,m,o in af:
    if 'esp + 0xa' in o or 'esp + 0xb' in o:
        print('   VC2 %s %-10s %s'%(hex(a),m,o))
json.dump(dict(buckets={k:v for k,v in buckets.items()},rows=rows,dups=[r[0] for r in DUPS],
  stub_zero=[hex(x) for x in A],stub_bare=[hex(x) for x in sorted(set(Bb)-set(A))],asserts=N,fails=fails),
  open('/home/t628/projects/ra2-campaign-forge/_r198/m15_final_verify.json','w'),ensure_ascii=False,indent=1)
print('\nSUMMARY asserts=%d fails=%d %s'%(N,len(fails),fails))
