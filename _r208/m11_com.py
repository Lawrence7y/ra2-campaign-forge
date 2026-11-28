# -*- coding: utf-8 -*-
"""R208 m11：mdisp=4 共享 6 槽数组的 COM 形态判定 + 3 条 mdisp=21784 异常 COL 的字节核验。
正控：6 槽逐槽反汇编 + 返回值常量识别；异常 COL 的 20 B 原字节与所在 32 B 上下文
反控：把 6 槽地址换成相邻无关 .text 地址，E_NOTIMPL/E_POINTER 常量命中应崩
"""
import sys,struct,collections,json
sys.path.insert(0,'/home/t628/projects/ra2-campaign-forge/_r185')
import pe185 as P
from capstone import Cs,CS_ARCH_X86,CS_MODE_32
def s32(v): return struct.unpack('<i',struct.pack('<I',v))[0]
md=Cs(CS_ARCH_X86,CS_MODE_32)
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
refidx=collections.defaultdict(list)
for sn in ('.rdata','.data'):
    s=P.B[sn]; n=s['rawsize']//4; base=s['lo']
    w=struct.unpack_from('<%dI'%n,P.RAW,s['rawptr'])
    for i,x in enumerate(w):
        if x in COL: refidx[x].append(base+4*i)
vt={}
for c in COL:
    q=[x for x in refidx.get(c,[]) if P.where(P.dw(x+4))=='.text']
    if len(q)==1: vt[c]=q[0]+4
def vlen(s,cap=4096):
    k=0
    while k<cap and P.where(P.dw(s+4*k))=='.text': k+=1
    return k
A={c:tuple(P.dw(vt[c]+4*k) for k in range(vlen(vt[c]))) for c in vt}
HR={0x80004001:'E_NOTIMPL',0x80004002:'E_NOINTERFACE',0x80004003:'E_POINTER',
    0x80004005:'E_FAIL',0x80070005:'E_ACCESSDENIED',0x8000ffff:'E_UNEXPECTED'}
def dump(a,n=48):
    o=P.r2o(a); ins=list(md.disasm(P.RAW[o:o+n],a))
    consts=[]
    for i in ins:
        if i.mnemonic=='mov' and i.op_str.startswith('eax, 0x'):
            try:
                v=int(i.op_str.split(',')[-1],16)
                if v in HR: consts.append(HR[v])
            except Exception: pass
    return ('; '.join('%s %s'%(i.mnemonic,i.op_str) for i in ins), consts)
print('== A mdisp=4 共享 6 槽数组：六个槽的落点与常量 ==')
base=tuple(P.dw(0x7fa4b0+0) for _ in [0])  # dummy
# 找那个 72 组的数组
groups=collections.defaultdict(list)
for c,a in A.items(): groups[a].append(c)
big=[(a,cl) for a,cl in groups.items() if len(cl)>=70]
for a,cl in sorted(big,key=lambda x:-len(x[1])):
    print(' 组 %d 条, 数组长度 %d, mdisp %s' % (len(cl),len(a),collections.Counter(COL[c]['mdisp'] for c in cl).most_common()))
    allc=[]
    for k,t in enumerate(a):
        txt,consts=dump(t)
        allc+=consts
        print('   slot%d 0x%-7x 常量 %-14s %s' % (k,t,','.join(consts) or '-',txt[:110]))
    print('   本组常量汇总 %s' % collections.Counter(allc).most_common())
print('== B 反控：相邻无关 .text 地址的常量命中 ==')
import random; random.seed(208)
hit=0
for _ in range(300):
    t=0x401000+random.randrange((0x7e1000-0x401000)//4)*4
    if any(x in HR for x in []): pass
    o=P.r2o(t); ins=list(md.disasm(P.RAW[o:o+48],t))
    for i in ins:
        if i.mnemonic=='mov' and i.op_str.startswith('eax, 0x'):
            try:
                if int(i.op_str.split(',')[-1],16) in HR: hit+=1; break
            except Exception: pass
print('  随机地址含 HRESULT 常量比例 %d/300' % hit)
print('== C 3 条 mdisp=21784 异常 COL 字节核验 ==')
anom=[c for c in COL if COL[c]['mdisp']==21784]
for c in anom:
    o=P.r2o(c)
    raw=P.RAW[o-8:o+24]
    print('  COL 0x%x sig=%d mdisp=%d cdOffset=%d pTD=0x%x pCHD=0x%x 名=%s' %
          (c,COL[c]['sig'],COL[c]['mdisp'],P.dw(c+8),COL[c]['pTD'],COL[c]['pCHD'],COL[c]['name']))
    print('    原 32 B: %s' % raw.hex())
    print('    前后 dword: %s' % [hex(P.dw(c-8+4*i)) for i in range(8)])
    H=COL[c]['pCHD']
    print('    所属类头 0x%x +0=0x%x +4(attrs)=0x%x +8(NB)=%d +12(pBCA)=0x%x' %
          (H,P.dw(H),P.dw(H+4),P.dw(H+8),P.dw(H+12)))
    nb=P.dw(H+8); pb=P.dw(H+12)
    rows=[]
    for j in range(nb):
        b=P.dw(pb+4*j)
        rows.append((hex(b),hex(P.dw(b)),P.dw(b+4),s32(P.dw(b+8)),s32(P.dw(b+12)),s32(P.dw(b+16)),P.dw(b+20)))
    print('    BCA: %s' % rows)
    print('    该类全部 COL: %s' % [(hex(x),COL[x]['mdisp'],COL[x]['name']) for x in COL if COL[x]['pCHD']==H])
print('== D 21784 == 0x5518 的相邻值核验 ==')
print('  0x5518=%d；若按两 16 位读: lo=0x%x hi=0x%x' % (21784,21784&0xffff,21784>>16))
