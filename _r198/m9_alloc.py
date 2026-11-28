#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R198 第九刀：CRC 状态对象（16 字节四槽）的「构造/分配」字节取证。
判据（N 系列，均为可机械复算的字节形态）：
 N1 全 .text 内「push 0x10」+ 紧随 call 的分配点计数。
 N2 四槽连续初始化形态：同一基址寄存器上对 +0/+4/+8/+0xC 各至少一次写，且四写落在 64 字节窗口内。
 N3 上述命中里，基址寄存器是否之后再被作为 ecx/edi 传给 0x4A1CA0 一族（同函数内）。
 N4 反控：把窗口从 64B 放宽到 256B，命中数变化（说明判据窗口敏感度）。
 N5 反控：把「四槽全写」放宽成「至少两槽写」，命中数变化（说明特异性）。
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
INSN={};CALLAT=[]
pos=0
while pos<len(BUF):
    for off,sz,mn,op in md.disasm_lite(BUF[pos:pos+65536],LO+pos):
        INSN[off]=(sz,mn,op)
        if mn=='call': CALLAT.append((off,op))
    pos+=65536
KEYS=sorted(INSN)
ck('N0a 指令起始数', True, len(INSN))
ck('N0b call 数', True, len(CALLAT))
# N1 push 0x10
p16=[(a,INSN[a]) for a in KEYS if INSN[a][1]=='push' and INSN[a][2] in ('0x10','16')]
ck('N1a push 0x10 计数', True, len(p16))
with_call=0
for a,_ in p16:
    i=bisect.bisect_left(KEYS,a+1)
    if i<len(KEYS) and KEYS[i]-a<=8 and INSN[KEYS[i]][1]=='call': with_call+=1
ck('N1b push 0x10 后 <=8B 内紧跟 call 的个数', True, with_call)

# 解析 [reg + off] 写
def parse_wr(mn,op):
    """返回 (reg, off) 若这是一条对 [reg+off] 的写（off 为 int）。"""
    if mn not in ('mov','or','and','add','sub','xor'): return None
    if ',' not in op: return None
    dst,src=op.split(',',1)
    m=re.match(r'^(?:dword|word|byte) ptr \[([a-z]{3})(?:\s*\+\s*(0x[0-9a-f]+|\d+))?\]$',dst.strip())
    if not m: return None
    off=int(m.group(2),0) if m.group(2) else 0
    return (m.group(1),off)
WR=[]   # (addr, reg, off, op)
for a in KEYS:
    sz,mn,op=INSN[a]
    r=parse_wr(mn,op)
    if r: WR.append((a,r[0],r[1],mn+' '+op))
ck('N2a 对 [reg+off] 的写指令数', True, len(WR))
# 按 (reg, 窗口) 找四槽齐全
def find4(win, need):
    hits=[]
    byreg=collections.defaultdict(list)
    for a,reg,off,op in WR: byreg[reg].append((a,off,op))
    for reg,lst in byreg.items():
        for i in range(len(lst)):
            a0=lst[i][0]; grp={}
            for (a,off,op) in lst[i:]:
                if a-a0>win: break
                if off in (0,4,8,12): grp.setdefault(off,(a,op))
            if len(grp)>=need: hits.append(dict(base=hex(a0),reg=reg,slots=sorted(grp),detail={k:v for k,v in grp.items()}))
    return hits
H4=find4(64,4)
ck('N2b 64B 窗口内四槽齐全的候选', True, len(H4))
for h in H4[:8]: print('   N2c',h)
R4=find4(256,4)
ck('N4a 256B 窗口四槽齐全', True, len(R4))
R2=find4(64,2)
ck('N5a 64B 窗口两槽以上', True, len(R2))
# N3 这些候选之后是否把该寄存器传给 0x4A1CA0 一族
FAMSET={0x4A1CA0,0x4A1D50,0x4A1DE0,0x41B8D0,0x41CB80}
tgt={}
for a,op in CALLAT:
    if op.startswith('0x'): tgt[a]=int(op,16)
def follows(va, reg, span=400):
    i=bisect.bisect_left(KEYS,va)
    out=[]
    for k in KEYS[i:i+200]:
        if k-va>span: break
        sz,mn,op=INSN[k]
        if mn=='call' and tgt.get(k) in FAMSET: out.append((hex(k),hex(tgt[k])))
        if mn=='mov' and op.startswith(('ecx, '+reg,'ecx, '+reg+',')): out.append((hex(k),op))
    return out
res=[]
for h in H4:
    f=follows(int(h['base'],16),h['reg'])
    res.append(dict(base=h['base'],reg=h['reg'],follow=f[:4]))
    print('   N3a base=%s reg=%s follow=%s'%(h['base'],h['reg'],f[:4]))
ck('N3b 落在 CRC 族前面的候选数', True, sum(1 for r in res if r['follow']))
json.dump(dict(p16=len(p16),p16call=with_call,wr=len(WR),h4=len(H4),h4res=res,r4=len(R4),r2=len(R2),
  asserts=N,fails=fails),
  open('/home/t628/projects/ra2-campaign-forge/_r198/m9_alloc.json','w'),ensure_ascii=False,indent=1)
print('\nSUMMARY asserts=%d fails=%d %s'%(N,len(fails),fails))
