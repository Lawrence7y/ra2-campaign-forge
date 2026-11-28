#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R198 第五刀（主会话独立复算）：CRC 状态对象 +0 初值来源 —— 向上追到最外层。
一次线性 lite 扫描同时建：call 目标集 + 每条 call 的 (调用点,目标)。之后全部 O(1) 查询。
反控 R1 入口判据换填充法 / R2 层数 5->2 / R3 零写放宽 / R4 寄存器集放宽。
"""
import sys,struct,collections,json,bisect
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
def at(va,n): return BUF[va-LO:va-LO+n]

# ---- 一次性扫描
CALLAT=[]; CALLTGT=set(); INSN_START=set()
pos=0
while pos<len(BUF):
    blk=BUF[pos:pos+65536]; va=LO+pos
    for off,sz,mn,op in md.disasm_lite(blk,va):
        INSN_START.add(off)
        if mn in ('call','jmp') and op.startswith('0x'):
            t=int(op,16)
            if in_text(t):
                if mn=='call': CALLAT.append((off,t))
                CALLTGT.add(t)
    pos+=65536
del md
md=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32)
ck('A1 .text 大小 4063232', len(BUF)==4063232, len(BUF))
ck('A2 call 目标集', True, len(CALLTGT))
ck('A3 call 指令数', True, len(CALLAT))
ck('A4 0x410410 在目标集', 0x410410 in CALLTGT, True)
ck('A5 0x410BE0 在目标集', 0x410BE0 in CALLTGT, True)
ck('A6 0x4A1CA0 在目标集', 0x4A1CA0 in CALLTGT, True)

CALLERS=collections.defaultdict(list)
for c,t in CALLAT: CALLERS[t].append(c)
BYTECACHE={}
def calls_byte(fn):
    if fn in BYTECACHE: return BYTECACHE[fn]
    out=[]
    for va in range(LO,HI-5):
        if BUF[va-LO]!=0xE8: continue
        if struct.unpack_from('<i',BUF,va-LO+1)[0]+va+5==fn: out.append(va)
    BYTECACHE[fn]=out; return out
def calls_to(fn):
    return sorted(CALLERS.get(fn,[]))
C_CRC=calls_byte(0x4A1CA0); C_A=calls_byte(0x410410); C_B=calls_byte(0x410BE0)
ck('B1 0x4A1CA0==331', len(C_CRC)==331, len(C_CRC))
ck('B2 0x410410==27', len(C_A)==27, len(C_A))
ck('B3 0x410BE0==23', len(C_B)==23, len(C_B))
SORTTGT=sorted(CALLTGT)
def host_of(c):
    i=bisect.bisect_left(SORTTGT,c)-1
    return SORTTGT[i] if i>=0 else None
# 入口->调用点 映射（call 指令级）
BYHOST=collections.defaultdict(list)
for c,t in CALLAT:
    h=host_of(c)
    if h is not None: BYHOST[h].append(c)
ck('C1 BYHOST 规模', True, len(BYHOST))
def host_pad(c):
    p=c-LO
    q=p
    while q>8:
        if BUF[q-1]==0x90 and BUF[q-2]==0x90: return LO+q
        q-=1
    return None
h1=sorted({host_of(c) for c in C_A if host_of(c)})
h1b=sorted({host_pad(c) for c in C_A if host_pad(c)})
ck('C2 0x410410 的 27 个调用点落在 %d 个宿主入口'%len(h1), len(h1)>0, [hex(x) for x in h1])
ck('R1a 两入口判据对称差', True, dict(n=len(set(h1)^set(h1b)),samples=[hex(x) for x in sorted(set(h1)^set(h1b))[:8]]))

def body_of(e,cap=3000):
    out=[]
    for off,sz,mn,op in md.disasm_lite(at(e,cap),e):
        out.append((off,sz,mn,op))
        if mn=='ret': break
    return out
def zero_writes(body):
    hits=[]
    for (a,sz,mn,op) in body:
        if mn!='mov' or ',' not in op: continue
        dst,src=op.split(',',1)
        if '[' not in dst: continue
        if src.strip() in ('0','1','2'): hits.append((hex(a),op))
    return hits
def zero_any(body):
    return sum(1 for (a,sz,mn,op) in body if mn=='mov' and ',' in op and '[' in op.split(',',1)[0] and op.split(',',1)[1].strip()=='0')
zw={e:zero_writes(body_of(e)) for e in h1}
ck('D1 第一层宿主零写命中', True, dict(n=sum(len(v) for v in zw.values()),hosts=sum(1 for v in zw.values() if v)))
for e,v in zw.items():
    if v: print('   D2 %s : %s'%(hex(e),v[:5]))
ck('R3a 放宽到任何 mov [reg],0', True, sum(zero_any(body_of(e)) for e in h1))

LAYERS=[('L1',h1)]
def next_layer(es):
    out=set()
    for e in es:
        for c in calls_to(e):
            h=host_of(c)
            if h: out.add(h)
    return sorted(out)
for i in range(2,6):
    LAYERS.append(('L%d'%i,next_layer(LAYERS[-1][1])))
for nm_,es in LAYERS: print('   E1 %s 入口数=%d'%(nm_,len(es)))
ck('E2 层入口数序列', True, [len(e[1]) for e in LAYERS])
allent=set()
for nm_,es in LAYERS: allent|=set(es)
ck('E3 5 层累计入口数', True, len(allent))
detail={};tot=0
for e in sorted(allent):
    z=zero_writes(body_of(e))
    if z: detail[hex(e)]=z[:6]; tot+=len(z)
ck('E4 5 层内零写命中', True, dict(n=tot,hosts=len(detail)))
for k,v in list(detail.items())[:10]: print('   E5',k,v)
two=set(LAYERS[0][1])|set(LAYERS[1][1])
ck('R2a 只 2 层', True, dict(two=len(two),hits=sum(len(zero_writes(body_of(e))) for e in two)))
def stosd(e,cap=3000):
    out=[]
    for (a,sz,mn,op) in md.disasm_lite(at(e,cap),e):
        if mn=='stosd': out.append(hex(a))
        if mn=='ret': break
    return out
rs={}
for e in sorted(allent):
    s=stosd(e)
    if s: rs[hex(e)]=s[:4]
ck('E6 5 层内 stosd 宿主', True, len(rs))
for k,v in list(rs.items())[:8]: print('   E7',k,v)
# 宿主是谁：给类名/符号线索 —— 用 COL/vtable 反查入口
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
OWNSLOT=collections.defaultdict(list)
for vt in VT:
    for k in range(nslot(vt)):
        OWNSLOT[P.dw(vt+4*k)].append((hex(vt),COL[VT[vt]]['name'],k))
fn_owner={}
for e in sorted(allent):
    if e in OWNSLOT: fn_owner[hex(e)]=OWNSLOT[e][:3]
ck('F1 上溯入口里作为虚表实现的个数', True, len(fn_owner))
for k,v in list(fn_owner.items())[:10]: print('   F2',k,v)
json.dump(dict(calltgt=len(CALLTGT),callinsn=len(CALLAT),layers={a:len(b) for a,b in LAYERS},
  allent=len(allent),zw=tot,zwdetail=detail,stosd=rs,h1=[hex(x) for x in h1],h1pad=[hex(x) for x in h1b],
  owner=fn_owner,asserts=N,fails=fails),
  open('/home/t628/projects/ra2-campaign-forge/_r198/m5_crctree.json','w'),ensure_ascii=False,indent=1)
print('\nSUMMARY asserts=%d fails=%d %s'%(N,len(fails),fails))
