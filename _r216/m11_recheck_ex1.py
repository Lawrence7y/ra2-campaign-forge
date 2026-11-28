# -*- coding: utf-8 -*-
"""R216 m11：主会话独立复算 EX1（不复用子代理代码，§2.12 规则 D）。
① 0x4a1d50 / 0x4a1ca0 函数体与 ret imm；② call 站点数（E8 rel32 字节口径）；
③ [reg+0x20] byte 读/写与 [reg+0x10] dword 读/写计数（排除 [esp+X]）；
④ 0x4a1d50 = ??0?$array@... 构造函数假说：写 [esp+4] 后 call 0x4a1de0。"""
import sys,struct,json,collections
sys.path.insert(0,'/home/t628/projects/ra2-campaign-forge/_r185')
import pe185 as P
from capstone import *
mdl=Cs(CS_ARCH_X86,CS_MODE_32); mdl.skipdata=True
def o(va): return P.r2o(va)
CK=[]
def ck(n,ok,d=''):
    CK.append((n,bool(ok),d)); print('[%s] %s %s'%('PASS' if ok else 'FAIL',n,d))
# ① 函数体
def body(va,cap=200):
    out=[]
    for it in mdl.disasm_lite(P.RAW[o(va):o(va)+cap],va):
        out.append(it); 
        if it[2].startswith('ret') or (it[2]=='jmp' and it[3].startswith('0x')): break
    return out
b1=body(0x4a1d50); b2=body(0x4a1ca0)
print('=== 0x4a1d50 (%d ins) ==='%len(b1))
for it in b1: print('  %08x %-7s %s'%(it[0],it[2],it[3]))
print('=== 0x4a1ca0 (%d ins) ==='%len(b2))
for it in b2: print('  %08x %-7s %s'%(it[0],it[2],it[3]))
ck('0x4a1d50 末指令 ret 4', b1[-1][2]=='ret' and b1[-1][3]=='4', b1[-1][3])
ck('0x4a1ca0 末指令 ret 4', b2[-1][2]=='ret' and b2[-1][3]=='4', b2[-1][3])
ck('0x4a1d50 含 call 0x4a1de0', any(it[2]=='call' and it[3]=='0x4a1de0' for it in b1))
# ② E8 站点
t=P.B['.text']; tb=P.RAW[t['rawptr']:t['rawptr']+t['rawsize']]; lo=t['lo']
def e8sites(tgt):
    s=[];n=len(tb)
    for k in range(n-5):
        if tb[k]!=0xe8: continue
        rel=struct.unpack_from('<i',tb,k+1)[0]
        if (lo+k+5+rel)&0xffffffff==tgt: s.append(lo+k)
    return s
s1=e8sites(0x4a1d50); s2=e8sites(0x4a1ca0)
print('=== E8 站点 ===\n  0x4a1d50 -> %d ; 0x4a1ca0 -> %d'%(len(s1),len(s2)))
ck('call 0x4a1d50 站点数 == 460 (EX1)',len(s1)==460,len(s1))
ck('call 0x4a1ca0 站点数 == 1 (EX1)',len(s2)==1,s2)
ck('站点含 0x41041e / 0x410429',0x41041e in s1 and 0x410429 in s2)
# ③ 字段计数（排除 esp/ebp 帧址）
ADDR=[];MN=[];OPS=[]
sz=t['hi_file']-lo; CH=64*1024
for off in range(0,sz,CH):
    va=lo+off; c=P.RAW[o(va):o(va)+min(CH,sz-off)]
    for it in mdl.disasm_lite(c,va):
        ADDR.append(it[0]);MN.append(it[2]);OPS.append(it[3])
    del c
def cnt(disp,width):
    r={'read':0,'write':0,'rmw':0,'esp':0}
    for i in range(len(ADDR)):
        ops=OPS[i]
        m=MN[i]
        if width=='b':
            if ('byte ptr [' not in ops): continue
            forms=[x for x in ops.split(', ')]
        else: continue
    return r
def scan(off,width):
    rd=wr=sp=0; samples={'read':[],'write':[]}
    for i in range(len(ADDR)):
        ops=OPS[i];mn=MN[i]
        if width=='b':
            if 'byte ptr [' not in ops: continue
            pat='+ 0x%x]'%off
            if pat not in ops: continue
        else:
            if 'dword ptr [' not in ops: continue
            pat='+ 0x%x]'%off
            if pat not in ops: continue
        # 排除 esp/ebp
        import re
        mm=re.search(r'\[(esp|ebp) \+ 0x%x\]'%off,ops)
        if mm: sp+=1; continue
        if not re.search(r'\[(eax|ebx|ecx|edx|esi|edi) \+ 0x%x\]'%off,ops): continue
        dst=ops.split(', ')[0]
        if dst.startswith('byte ptr') or dst.startswith('dword ptr'):
            wr+=1
            if len(samples['write'])<6: samples['write'].append((hex(ADDR[i]),mn,ops))
        else:
            rd+=1
            if len(samples['read'])<6: samples['read'].append((hex(ADDR[i]),mn,ops))
    return rd,wr,sp,samples
b20=scan(0x20,'b'); d10=scan(0x10,'d')
print('=== [reg+0x20] byte（排除 esp/ebp）read=%d write=%d | 排除掉的 esp/ebp=%d'%(b20[0],b20[1],b20[2]))
print('   read 样例:',b20[3]['read'])
print('   write 样例:',b20[3]['write'])
print('=== [reg+0x10] dword（排除 esp/ebp）read=%d write=%d | 排除掉的 esp/ebp=%d'%(d10[0],d10[1],d10[2]))
print('   read 样例:',d10[3]['read'])
print('   write 样例:',d10[3]['write'])
print('=== EX1 原始数（含 esp/ebp）b20_all=113 (r24/w89) d10_all=8099 (r5099/w2994) ===')
ck('b20 排除 esp/ebp 后 read+write <= 113', b20[0]+b20[1]<=113, b20[0]+b20[1])
ck('d10 排除 esp/ebp 后 read+write <= 8099', d10[0]+d10[1]<=8099, d10[0]+d10[1])
ck('ESP/EBP 占 b20 的份额 > 50%', b20[2]>0.5*113, '%d/113'%b20[2])
ck('ESP/EBP 占 d10 的份额 > 50%', d10[2]>0.5*8099, '%d/8099'%d10[2])
# ④ 0x4a1d50 语义：体内 3 条指令 push 4 / push &buf / call 0x4a1de0
print('=== 0x4a1de0 前 25 条 ===')
for it in body(0x4a1de0,120)[:25]: print('  %08x %-7s %s'%(it[0],it[2],it[3]))
json.dump({'chk':[[n,p,d] for n,p,d in CK],'s1':len(s1),'s2':s2,'b20':b20[:3],'d10':d10[:3],
 'b20_samples':b20[3],'d10_samples':d10[3]},
 open('/home/t628/projects/ra2-campaign-forge/_r216/m11.json','w'),indent=1)
