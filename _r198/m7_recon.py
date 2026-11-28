#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R198 第七刀：与执行员执行 A 的两处分歧逐值复算（口径对齐，不取信任一方）。
 D1 纯桩个数：主会话 8 vs 执行 A 16。逐地址比对，判断是判据松紧还是真错。
 D2 体形态分组：主会话 140/170/34（ret_imm/ret/no_ret），执行 A 122/151/59+12。逐实现比对。
 D3 唯一一个 4096 B 窗口内仍无 ret 的实现是哪个，它的体形态是什么。
"""
import sys,struct,collections,json
sys.path.insert(0,'/home/t628/projects/ra2-campaign-forge/_r185')
import pe185 as P
import capstone
md=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32); md.detail=False
fails=[];N=0
def ck(nm,c,d=''):
    global N;N+=1
    if not c: fails.append(nm)
    print(('PASS ' if c else 'FAIL ')+nm+((' | '+str(d)) if d!='' else ''))
T=P.B['.text'];LO=T['lo'];HI=T['hi_file'];RAW=P.RAW
BUF=RAW[T['rawptr']:T['rawptr']+(HI-LO)]
def in_text(x): return x is not None and LO<=x<HI
def at(va,n): return BUF[va-LO:va-LO+n]
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
SL=[P.dw(0x7F5C70+4*k) for k in range(nslot(0x7F5C70))]
ck('D0a 344 槽', len(SL)==344, len(SL))
UNIQ=sorted(set(SL))
ck('D0b uniq=344', len(UNIQ)==344, len(UNIQ))
def body(va,lim):
    o=va-LO; out=[]
    for off,sz,mn,op in md.disasm_lite(BUF[o:o+lim],va):
        out.append((off,sz,mn,op))
        if mn=='ret': break
    return out
# ---- 宽松纯桩判据（执行 A 口径复现）：[xor/sub eax,eax | mov eax,0 | and eax,0] + nop* + ret(imm 0)
def stub_broad(va):
    B=body(va,400)
    if not B: return False
    core=[b for b in B if b[2]!='nop']
    if not core: return False
    last=core[-1]
    if last[2]!='ret': return False
    if last[3] not in ('','0'): return False
    if len(core)==1: return True
    if len(core)==2:
        m,op=core[0][2],core[0][3]
        if m=='xor' and op=='eax, eax': return True
        if m=='sub' and op=='eax, eax': return True
        if m=='mov' and op in ('eax, 0','eax, 0x0'): return True
        if m=='and' and op in ('eax, 0','eax, 0x0'): return True
    return False
S_BROAD=[a for a in UNIQ if stub_broad(a)]
ck('D1a 宽松纯桩判据的实现数', True, len(S_BROAD))
print('   D1b 宽松纯桩地址:', [hex(a) for a in S_BROAD])
# ---- 严格判据（主会话 m1 口径）
def stub_strict(va):
    B=body(va,400)
    core=[b for b in B if b[2]!='nop']
    if not core or core[-1][2]!='ret': return False
    if len(core)==1: return core[0][3] in ('','0')
    return len(core)==2 and core[0][2] in ('xor','sub') and core[0][3]=='eax, eax' and core[1][3] in ('','0')
S_STRICT=[a for a in UNIQ if stub_strict(a)]
ck('D1c 严格纯桩判据的实现数', True, len(S_STRICT))
print('   D1d 严格纯桩地址:', [hex(a) for a in S_STRICT])
ck('D1e 宽松-严格 差集', True, [hex(x) for x in sorted(set(S_BROAD)-set(S_STRICT))])
ea=set(int(x,16) for x in json.load(open('/home/t628/projects/ra2-campaign-forge/_r198/exec_a/vtslot.json'))['Q4']['stub_addrs'])
ck('D1f 与执行 A 的 16 个地址逐值一致', set(S_BROAD)==ea, dict(only_mine=[hex(x) for x in sorted(set(S_BROAD)-ea)],
   only_exec=[hex(x) for x in sorted(ea-set(S_BROAD))]))
# ---- 体形态逐实现
def shape(va,lim):
    B=body(va,lim)
    if not B: return 'NOCODE'
    last=B[-1]
    if last[2]=='ret': return 'RET_IMM' if last[3] not in ('','0') else 'RET'
    if last[2]=='jmp': return 'JMP_TAIL'
    return 'NO_RET_WIN'
sh400={a:shape(a,400) for a in UNIQ}
sh4096={a:shape(a,4096) for a in UNIQ}
ck('D2a 400B 窗口形态分组', True, dict(collections.Counter(sh400.values())))
ck('D2b 4096B 窗口形态分组', True, dict(collections.Counter(sh4096.values())))
noret=[a for a in UNIQ if sh4096[a]!='RET' and sh4096[a]!='RET_IMM']
ck('D3a 4096B 窗口内仍无 ret 的实现', True, [hex(a) for a in noret])
for a in noret:
    B=body(a,8192)
    print('   D3b %s : 条数=%d 末=%s 首=%s'%(hex(a),len(B),B[-1][2]+' '+B[-1][3] if B else '-',
          B[0][2]+' '+B[0][3] if B else '-'))
# 4096 窗口里形态从 NO_RET_WIN 变 RET 的个数
moved=[a for a in UNIQ if sh400[a]=='NO_RET_WIN' and sh4096[a] in ('RET','RET_IMM')]
ck('D2c 400->4096 窗口由 NO_RET 变 RET 的实现数', len(moved)==len([a for a in UNIQ if sh400[a]=='NO_RET_WIN']), len(moved))
json.dump(dict(stub_broad=[hex(a) for a in S_BROAD],stub_strict=[hex(a) for a in S_STRICT],
  sh400=dict(collections.Counter(sh400.values())),sh4096=dict(collections.Counter(sh4096.values())),
  noret=[hex(a) for a in noret],asserts=N,fails=fails),
  open('/home/t628/projects/ra2-campaign-forge/_r198/m7_recon.json','w'),ensure_ascii=False,indent=1)
print('\nSUMMARY asserts=%d fails=%d %s'%(N,len(fails),fails))
