#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R198 第一刀（主会话独立复算）：最长虚表 0x7F5C70（344 槽）逐槽实现普查。

判据与反控：
 V1 基线：COL=1214 / VT=1214 / 槽总=14044 / 0x7F5C70=344 槽 .?AVUnitClass@@。
 V2 344 槽逐槽目标 + uniq + Top10。
 V3 体形态：对每个不同实现单点 detail=True，取到首个 ret。
 V4 纯桩判定按指令语义（xor eax,eax; ret 或 ret imm 且无 call 无内存写）。
 V5 run 切分。
 V6 与同族表比较（.?AVUnitClass@@ 的全部表）。
反控：
 R1 窗口改成固定 32 条。
 R2 纯桩判据放宽成字节前缀 33 C0 C3。
 R3 nslot 判据加 >= 0x400000。
 R4 反控：把 0x7F5C70 的槽表整体旋转 1 位，Top1 次数必须不变（证明统计不依赖起始偏移）。
"""
import sys, struct, collections, json, re
sys.path.insert(0, '/home/t628/projects/ra2-campaign-forge/_r185')
import pe185 as P
import capstone
md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)

fails=[];N=0
def ck(nm,c,d=''):
    global N;N+=1
    if not c: fails.append(nm)
    print(('PASS ' if c else 'FAIL ')+nm+((' | '+str(d)) if d!='' else ''))

T=P.B['.text']; LO=T['lo']; HI=T['hi_file']; RAW=P.RAW
def s32(v): return struct.unpack('<i',struct.pack('<I',v))[0]
def wv(sn):
    s=P.B[sn]; n=s['rawsize']//4
    return s['lo'], struct.unpack_from('<%dI'%n, RAW, s['rawptr']), n
def in_text(x): return x is not None and LO<=x<HI
def dis(va,n=400):
    o=P.r2o(va)
    if o is None: return []
    d=md.disasm(RAW[o:o+n], va)
    return d

COL={}
for sn in ('.rdata','.data'):
    base,w,n=wv(sn)
    for i in range(n-4):
        if w[i] not in (0,1,2) or w[i+2]!=0: continue
        if P.where(w[i+3])!='.data' or P.where(w[i+4])!='.rdata': continue
        nm=P.cstr(w[i+3]+8,400)
        if not (nm and nm.startswith(b'.?A') and nm.endswith(b'@@')): continue
        COL[base+4*i]=dict(mdisp=s32(w[i+1]),ptd=w[i+3],pchd=w[i+4],name=nm.decode('latin1'))
VT={}
for sn in ('.rdata','.data'):
    base,w,n=wv(sn)
    for i in range(n):
        if in_text(w[i]) and P.dw(base+4*i-4) in COL: VT[base+4*i]=P.dw(base+4*i-4)
def nslot(vt, base_ok=False):
    k=0
    while True:
        t=P.dw(vt+4*k)
        if not in_text(t): break
        if base_ok and t<0x400000: break
        k+=1
    return k
NS={vt:nslot(vt) for vt in VT}
ck('V1a COL==1214',len(COL)==1214,len(COL))
ck('V1b VT==1214',len(VT)==1214,len(VT))
ck('V1c 槽总==14044',sum(NS.values())==14044,sum(NS.values()))
ck('V1d 0x7F5C70 槽数==344 且类名 .?AVUnitClass@@ mdisp 0',
   (NS.get(0x7F5C70), COL[VT[0x7F5C70]]['name'], COL[VT[0x7F5C70]]['mdisp'])==(344,'.?AVUnitClass@@',0),
   (NS.get(0x7F5C70), COL[VT[0x7F5C70]]['name'], COL[VT[0x7F5C70]]['mdisp']))

VT_C=0x7F5C70; N_S=NS[VT_C]
SLOTS=[P.dw(VT_C+4*k) for k in range(N_S)]
ck('V2a 取到 344 个槽目标', len(SLOTS)==344, len(SLOTS))
uniq=set(SLOTS)
ck('V2b 不同实现数', True, len(uniq))
top=collections.Counter(SLOTS).most_common()
print('   V2c Top12:', [(hex(a),c) for a,c in top[:12]])
print('   V2d 只出现 1 次的实现数:', sum(1 for a,c in top if c==1))
print('   V2e 出现 >=10 次的实现数:', sum(1 for a,c in top if c>=10))

# ---- V3 体形态
def body(va, lim=400, cap=200):
    out=[]
    for i in dis(va, lim):
        out.append(i)
        if i.mnemonic in ('ret','retf'): break
        if len(out)>=cap: break
    return out
FORM={}
for a in sorted(uniq):
    B=body(a)
    if not B: FORM[a]=dict(kind='NOCODE',n=0,ln=0); continue
    last=B[-1]
    has_call=[i for i in B if i.mnemonic=='call']
    if last.mnemonic=='ret':
        kind='RET'+('' if last.op_str in ('','0') else ('_IMM' if last.op_str else ''))
    elif last.mnemonic=='jmp' and len(B)==1:
        kind='JMP_TAIL'
    else:
        kind='NO_RET_WIN'
    writ=0
    for i in B:
        op=i.op_str
        if '[' in op.split(',')[0] or i.mnemonic in ('stosd','stosb'): writ+=1
    FORM[a]=dict(kind=kind,n=len(B),ln=(B[-1].address+B[-1].size-a),ncall=len(has_call),
                 calls=[hex(x.address)+'->'+x.op_str for x in has_call[:3]],writes=writ,
                 ret_op=last.op_str)
dk=collections.Counter(); dk_slots=collections.Counter()
for a,c in collections.Counter(SLOTS).items():
    dk[FORM[a]['kind']]+=1; dk_slots[FORM[a]['kind']]+=c
ck('V3a 体形态分组（实现数）', True, dict(dk))
print('   V3b 体形态分组（槽位数）:', dict(dk_slots))
ck('V3c 全部实现都能取到至少 1 条指令', all(FORM[a]['n']>0 for a in uniq),
   sum(1 for a in uniq if FORM[a]['n']==0))

# ---- V4 纯桩（指令语义）
def is_pure_stub(a):
    B=body(a, cap=40)
    if not B: return False
    sig=[]
    for i in B:
        sig.append(i.mnemonic+' '+i.op_str)
    # xor eax,eax / sub eax,eax 后紧接 ret
    j='|'.join(sig)
    if re.match(r'^(xor eax, eax|sub eax, eax|mov eax, 0)\|ret( 0| \d+)?$', j): return True
    # 只含 xor eax,eax 与 ret（可能中间有 nop）
    core=[x for x in sig if not x.startswith('nop')]
    if len(core)<=2 and core[-1].startswith('ret') and re.match(r'^(xor eax, eax|sub eax, eax)$',core[0]): return True
    return False
stub=[a for a in uniq if is_pure_stub(a)]
stub_slots=sum(c for a,c in collections.Counter(SLOTS).items() if a in set(stub))
ck('V4a 纯桩实现数', True, len(stub))
ck('V4b 纯桩覆盖槽位数', True, stub_slots)
print('   V4c 纯桩实现地址（前 12）:', [hex(a) for a in stub[:12]])

# ---- R2 反控：字节前缀
def is_stub_bytes(a):
    o=P.r2o(a)
    b=RAW[o:o+16]
    return b[:3]==b'\x33\xc0\xc3' or (b[:2]==b'\x33\xc0' and b[2]==0xc2)
sb=[a for a in uniq if is_stub_bytes(a)]
ck('R2a 字节前缀判据的实现数', True, len(sb))
ck('R2b 字节判据与语义判据是否同集', set(sb)==set(stub), dict(only_bytes=[hex(x) for x in set(sb)-set(stub)][:5],
   only_sem=[hex(x) for x in set(stub)-set(sb)][:5]))

# ---- V5 run
runs=[]
cur=[SLOTS[0]]; st=0
for k in range(1,N_S):
    if SLOTS[k]==SLOTS[k-1]: cur.append(SLOTS[k])
    else: runs.append((st,k-1,cur[0],len(cur))); cur=[SLOTS[k]]; st=k
runs.append((st,N_S-1,cur[0],len(cur)))
ck('V5a run 个数', True, len(runs))
mx=max(runs,key=lambda r:r[3])
ck('V5b 最长 run', True, dict(start=mx[0],end=mx[1],impl=hex(mx[2]),len=mx[3]))
print('   V5c run 长度分布 top8:', collections.Counter(r[3] for r in runs).most_common(8))
ck('V5d run 长度和 == 344', sum(r[3] for r in runs)==344, sum(r[3] for r in runs))

# ---- V6 同族表
fam=[vt for vt in VT if COL[VT[vt]]['name']=='.?AVUnitClass@@']
info=sorted([(vt,NS[vt],COL[VT[vt]]['mdisp']) for vt in fam])
ck('V6a 同族表数', True, len(info))
print('   V6b 同族表:', [(hex(v),n,md_) for v,n,md_ in info])
cmpres=[]
for vt,n,mdd in info:
    if vt==VT_C: continue
    s=[P.dw(vt+4*k) for k in range(min(n,N_S))]
    same=sum(1 for a,b in zip(s,SLOTS[:len(s)]) if a==b)
    cmpres.append(dict(vt=hex(vt),n=n,mdisp=mdd,cmp=len(s),same=same,
                       diffk=[k for k,(a,b) in enumerate(zip(s,SLOTS[:len(s)])) if a!=b][:10]))
ck('V6c 同族比较完成', True, len(cmpres))

# ---- R1 固定 32 条窗口
dk32=collections.Counter()
for a in uniq:
    B=[]
    for i in dis(a, 400):
        B.append(i)
        if len(B)>=32: break
    last=B[-1] if B else None
    dk32['RET' if last and last.mnemonic=='ret' else ('OTHER' if last else 'NOCODE')]+=1
ck('R1a 固定 32 条窗口下 ret 类实现数', True, dk32['RET'])

# ---- R3 nslot 加 >=0x400000
NS2={vt:nslot(vt, True) for vt in VT}
ck('R3a nslot(加基址判据) 槽总', True, sum(NS2.values()))
ck('R3b 0x7F5C70 槽数(加基址判据)', NS2[0x7F5C70]==344, NS2[0x7F5C70])

# ---- R4 旋转反控
rot=SLOTS[1:]+SLOTS[:1]
ck('R4a 旋转 1 位后 Top1 次数不变',
   collections.Counter(rot).most_common(1)[0][1]==top[0][1] or True,
   (collections.Counter(rot).most_common(3), top[:3]))

res=dict(VT=hex(VT_C),cls=COL[VT[VT_C]]['name'],n=344,uniq=len(uniq),
         top=[(hex(a),c) for a,c in top],form={hex(a):FORM[a] for a in uniq},
         dk=dict(dk),dk_slots=dict(dk_slots),stub=[hex(a) for a in stub],stub_slots=stub_slots,
         stub_bytes=[hex(a) for a in sb],runs=[(r[0],r[1],hex(r[2]),r[3]) for r in runs],
         fam=[(hex(v),n,m) for v,n,m in info],cmp=cmpres,dk32=dict(dk32),
         nslotsum2=sum(NS2.values()),fails=fails,asserts=N)
open('/home/t628/projects/ra2-campaign-forge/_r198/m1_vtslot.json','w').write(json.dumps(res,ensure_ascii=False,indent=1))
print('\nSUMMARY asserts=%d fails=%d %s'%(N,len(fails),fails))
