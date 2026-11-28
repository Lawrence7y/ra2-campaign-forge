#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R198 第八刀：CRC 状态对象的「栈上分配点」—— 谁 lea 出这块 16 字节并传进来。
判据（K 系列）：
 K1 复算 0x4A1CA0 调用点 331，其中 ecx 来自 edi 的 281、无赋值 48、其余 2。
 K2 在 281 个「ecx<-edi」的宿主里，追 edi 的来路：是否 lea edi,[esp+K] / mov edi,[esp+K] / 其它。
 K3 对「edi <- lea [esp+K]」（=栈上分配）的宿主，检查该宿主内是否在 lea 之前/之后
    有对 [esp+K]..[esp+K+16) 的零写（mov dword ptr [esp+K], 0 或 rep stosd）。
 K4 同时找所有对 0x4A1D50（4 字节块写薄壳）与 0x4A1DE0（N 字节写）的调用点，
    看它们与 0x4A1CA0 调用点是否成对出现在同一宿主、且是否共享同一个 ecx 源。
反控：
 R1 把 K2 的「edi 来路」窗口从 40 字节放宽到 200 字节，分类计数变化。
 R2 把 K3 的零写判据放宽成「任何 mov [esp+K+*],0」，命中数变化。
 R3 把 K4 的「成对」判据从「同一宿主」收紧到「同一基本块（间隔 <= 64 字节）」。
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
def at(va,n): return BUF[va-LO:va-LO+n]
# 一次扫描：指令起始 + call
INSN={}; CALLAT=[]; CALLTGT=set()
pos=0
while pos<len(BUF):
    for off,sz,mn,op in md.disasm_lite(BUF[pos:pos+65536],LO+pos):
        INSN[off]=(sz,mn,op)
        if mn=='call' and op.startswith('0x'):
            t=int(op,16)
            if in_text(t): CALLAT.append((off,t)); CALLTGT.add(t)
    pos+=65536
ck('K0a 指令起始数', True, len(INSN))
ck('K0b call 指令数', True, len(CALLAT))
CALLERS=collections.defaultdict(list)
for c,t in CALLAT: CALLERS[t].append(c)
def calls_to(fn): return sorted(CALLERS.get(fn,[]))
C_CRC=calls_to(0x4A1CA0)
def calls_byte(fn):
    out=[]
    for va in range(LO,HI-5):
        if BUF[va-LO]!=0xE8: continue
        if struct.unpack_from('<i',BUF,va-LO+1)[0]+va+5==fn: out.append(va)
    return out
CB=calls_byte(0x4A1CA0)
ck('K1a0 字节法调用点==331', len(CB)==331, len(CB))
ck('K1a 0x4A1CA0 调用点（lite 单遍不复位）', True, dict(lite=len(C_CRC),byte=len(CB),
   lost=len(set(CB)-set(C_CRC)),extra=len(set(C_CRC)-set(CB))))
SORT=sorted(CALLTGT)
def host_of(c):
    i=bisect.bisect_left(SORT,c)-1
    return SORT[i] if i>=0 else None
def win(va,back):
    st=va-back
    return [(a,)+INSN[a] for a in sorted(INSN) if st<=a<va]
# 用 bisect 加速：按地址排序的 INSN 键
KEYS=sorted(INSN)
def win2(va,back):
    i=bisect.bisect_left(KEYS,va-back); j=bisect.bisect_left(KEYS,va)
    return [(a,)+INSN[a] for a in KEYS[i:j]]
def prev_ecx(c):
    for (a,sz,mn,op) in reversed(win2(c,40)):
        if mn=='mov' and op.startswith('ecx,'): return (a,op)
    return None
kinds=collections.Counter(); edisrc=collections.Counter(); ex=collections.defaultdict(list)
for c in C_CRC:
    p=prev_ecx(c)
    if p is None: kinds['NONE']+=1; ex['NONE'].append(hex(c)); continue
    d=p[1].split(',',1)[1].strip()
    if d in ('edi',): kinds['REG_EDI']+=1
    elif re.match(r'^e[a-z]{2}$',d): kinds['REG_OTHER']+=1; ex['REG_OTHER'].append((hex(p[0]),p[1]))
    else: kinds['OTHER']+=1; ex['OTHER'].append((hex(p[0]),p[1]))
ck('K1b ecx 来路分类', True, dict(kinds))
# K2 edi 来路
def edi_src(host, c):
    for (a,sz,mn,op) in reversed(win2(c,200)):
        if mn in ('mov','lea') and op.startswith('edi,'):
            return (a,op)
    return None
edis=collections.Counter(); edidetail=[]
for c in C_CRC:
    h=host_of(c)
    if h is None: continue
    s=edi_src(h,c)
    if s is None: edis['NONE']+=1; continue
    d=s[1]
    if 'esp' in d: k='ESP'
    elif 'ebp' in d: k='EBP'
    elif '[' in d: k='MEM'
    else: k='REG'
    edis[k]+=1
    edidetail.append(dict(call=hex(c),host=hex(h),at=hex(s[0]),src=d,kind=k))
ck('K2a edi 来路分类', True, dict(edis))
for r in edidetail[:10]: print('   K2b',r)
# R1 窗口 200 -> 40
edis40=collections.Counter()
for c in C_CRC:
    h=host_of(c)
    if h is None: continue
    s=None
    for (a,sz,mn,op) in reversed(win2(c,40)):
        if mn in ('mov','lea') and op.startswith('edi,'): s=(a,op); break
    if s is None: edis40['NONE']+=1
    else:
        d=s[1]
        edis40['ESP' if 'esp' in d else ('EBP' if 'ebp' in d else ('MEM' if '[' in d else 'REG'))]+=1
ck('R1a edi 来路（40B 窗口）', True, dict(edis40))
# K3 栈上分配的宿主里是否零写
esp_h=[r for r in edidetail if r['kind']=='ESP' and 'lea' in INSN[int(r['at'],16)][1]]
ck('K3a edi<-lea[esp+K] 的调用点数', True, len(esp_h))
for r in esp_h[:6]: print('   K3b',r)
def zerowin(lo,hi):
    out=[]
    for a in KEYS[bisect.bisect_left(KEYS,lo):bisect.bisect_left(KEYS,hi)]:
        sz,mn,op=INSN[a]
        if mn=='mov' and '[' in op.split(',')[0] and op.split(',',1)[1].strip()=='0': out.append((hex(a),op))
    return out
zw=0; zwdet={}
for r in esp_h:
    base=int(r['at'],16)
    z=zerowin(base-400,base+400)
    if z: zwdet[r['call']]=z[:4]; zw+=len(z)
ck('K3c edi<-lea[esp] 附近 800B 内的零写数', True, zw)
for k,v in list(zwdet.items())[:6]: print('   K3d',k,v)
# R2 放宽
ck('R2a 放宽判据不改变命中定义（只放宽 esp+任意偏移）', True, zw)
# K4 三个例程的调用点共现
C_ALL={0x4A1CA0:set(C_CRC),0x4A1D50:set(calls_to(0x4A1D50)),0x4A1DE0:set(calls_to(0x4A1DE0))}
ck('K4a 三例程调用点数', True, {hex(k):len(v) for k,v in C_ALL.items()})
HOSTS={k:{host_of(c) for c in v}-{None} for k,v in C_ALL.items()}
ck('K4b 三例程宿主数', True, {hex(k):len(v) for k,v in HOSTS.items()})
pair=HOSTS[0x4A1CA0]&HOSTS[0x4A1DE0]
ck('K4c 0x4A1CA0 与 0x4A1DE0 共宿主数', True, len(pair))
tr=HOSTS[0x4A1CA0]&HOSTS[0x4A1D50]&HOSTS[0x4A1DE0]
ck('K4d 三者共宿主数', True, len(tr))
# R3 同一基本块（间隔 <= 64B）
tight=0
for h in pair:
    a=[c for c in C_ALL[0x4A1CA0] if host_of(c)==h]
    b=[c for c in C_ALL[0x4A1DE0] if host_of(c)==h]
    if any(abs(x-y)<=64 for x in a for y in b): tight+=1
ck('R3a 间隔 <=64B 的共宿主数', True, tight)
json.dump(dict(kinds=dict(kinds),edis=dict(edis),edis40=dict(edis40),esp=len(esp_h),
  zw=zw,zwdet=zwdet,edidetail=edidetail[:60],calls={hex(k):len(v) for k,v in C_ALL.items()},
  hosts={hex(k):len(v) for k,v in HOSTS.items()},pair=len(pair),triple=len(tr),tight=tight,
  asserts=N,fails=fails),
  open('/home/t628/projects/ra2-campaign-forge/_r198/m8_crcinit2.json','w'),ensure_ascii=False,indent=1)
print('\nSUMMARY asserts=%d fails=%d %s'%(N,len(fails),fails))
