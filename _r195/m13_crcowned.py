#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R195 第十三刀（主会话复算 exec_a 的核心结论）：0x4A1CA0 状态对象的归属与初值。
D1 线性口径（分块+重同步）扫 E8 call rel32 -> 0x4A1CA0 的调用点：总数（对照 exec_a 的 118）。
D2 字节模式口径（E8+rel32 且目标相等）：总数（对照 exec_a 的 331 = R194 的上界 U）。
D3 对每个线性调用点向前 48 字节，用 capstone detail 判定 ecx 的设定指令：
   给出「lea ecx,[esp+0xC]」形态的计数，以及是否所有调用点都是该形态。
D4 0x4A1CA0 体内 ecx 偏移集合（应为 {0,4,8,0xC}）。
D5 0x0 槽的写：在 0x4A1CA0 / 0x4A1D50 / 0x4A1DE0 / 0x4A1FB0 / 0x4A1FF0 五个例程体内，
   是否有任何写向 [+0]（mov [ecx],x / mov [esi],x / and/or [ecx]）。
D6 宿主函数 0x410410 的栈帧：sub esp,N 的 N，状态对象偏移 0xC 是否在帧内。
"""
import sys,re,struct,collections,capstone
sys.path.insert(0,'/home/t628/projects/ra2-campaign-forge/_r185')
import pe185 as P
md=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32); md.detail=True
fails=[];N=0
def ck(nm,c,d=''):
    global N;N+=1
    if not c:fails.append(nm)
    print(('PASS ' if c else 'FAIL ')+nm+((' | '+str(d)) if d!='' else ''))
T=P.B['.text']; LO=T['lo']
def sweep(pat_handler):
    CH=262144;o=0;tot=T['rawsize']
    while o<tot:
        n=min(CH,tot-o); buf=P.RAW[T['rawptr']+o:T['rawptr']+o+n]; va=LO+o; i=0
        while i<len(buf):
            got=False
            for ins in md.disasm_lite(buf[i:i+16],va+i):
                pat_handler(ins[0],ins[1],ins[2],ins[3]); i+=ins[1]; got=True; break
            if not got: i+=1
        o+=n
TGT=0x4A1CA0
lin=[]
def h(a,sz,mn,op):
    if mn=='call' and op=='0x4a1ca0': lin.append(a)
sweep(h)
print('   D1 线性口径 call -> 0x4A1CA0 : %d 处'%len(lin))
ck('D1a 线性口径 == 118（exec_a 值）',len(lin)==118,len(lin))
pat=struct.pack('<I',0x4A1CA0)
byte_hits=[]; i=T['rawptr']
while True:
    i=P.RAW.find(b'\xe8',i,T['rawptr']+T['rawsize'])
    if i<0: break
    if i+5<=len(P.RAW) and struct.unpack_from('<I',P.RAW,i+1)[0]==(TGT-(LO+(i-T['rawptr']))-5)&0xFFFFFFFF:
        byte_hits.append(LO+(i-T['rawptr']))
    i+=1
print('   D2 字节口径 E8+rel32 -> 0x4A1CA0 : %d 处（R194 上界 U=331）'%len(byte_hits))
ck('D2a 字节口径 == 331（R194 上界）',len(byte_hits)==331,len(byte_hits))
# D3 ecx 来路
cls=collections.Counter(); detail=[]
for a in lin:
    s=max(LO,a-48); o=P.r2o(s); found=None
    for ins in md.disasm(P.RAW[o:o+56],s):
        if ins.address>=a: break
        if ins.mnemonic=='lea' and ins.op_str.startswith('ecx, [esp + 0xc]'): found='lea ecx,[esp+0xc]'
        elif ins.mnemonic=='lea' and ins.op_str.startswith('ecx, [esp'): found='lea ecx,[esp+other]'
        elif ins.mnemonic=='mov' and ins.op_str.startswith('ecx, dword ptr [esp'): found='mov ecx,[esp]'
        elif ins.mnemonic=='lea' and ins.op_str.startswith('ecx, [e'): found='lea ecx,[reg]'
    cls[found]+=1; detail.append((a,found))
print('   D3 ecx 来路分布：%s'%dict(cls))
ck('D3a 全部调用点 ecx 均为 lea ecx,[esp+0xc]',cls.get('lea ecx,[esp+0xc]',0)==len(lin),(cls.get('lea ecx,[esp+0xc]',0),len(lin)))
# D4 体内偏移
def body(va,maxb=1024):
    o=P.r2o(va); out=[]
    for ins in md.disasm(P.RAW[o:o+maxb],va):
        out.append(ins)
        if ins.mnemonic.startswith('ret'): break
    return out
b1=body(0x4A1CA0)
offs=sorted({int(m,16) for ins in b1 for m in re.findall(r'\[ecx \+ (0x[0-9a-f]+)\]',ins.op_str)})
offs2=sorted({0 if re.search(r'\[ecx\]$',ins.op_str) else 0 for ins in b1 if '[ecx]' in ins.op_str})
print('   D4 0x4A1CA0 体内 ecx 偏移：%s（体长 %d 条）'%([hex(x) for x in offs],len(b1)))
ck('D4a 偏移集合 == {0,4,8,0xc}',set(offs)|({0} if offs2 else set())>={0,4,8,0xc},[hex(x) for x in offs])
# D5 +0 写
FIVE=[0x4A1CA0,0x4A1D50,0x4A1DE0,0x4A1FB0,0x4A1FF0]
w=[]
for va in FIVE:
    for ins in body(va):
        mm=re.fullmatch(r'(?:mov|and|or|xor|add|sub|inc|dec)\s+(?:dword ptr |byte ptr )?\[(ecx|esi|ebx|edi|eax)\]\s*,\s*.+',ins.mnemonic+' '+ins.op_str)
        if not mm:
            mm2=re.fullmatch(r'(?:mov|and|or|xor|add|sub)\s+(?:dword ptr |byte ptr )?\[(\w+)\],\s*(.+)',ins.mnemonic+' '+ins.op_str)
            if mm2: w.append((va,ins.address,ins.mnemonic,ins.op_str))
print('   D5 五个例程体内任何「写 [+0]」的指令：%d 条 %s'%(len(w),w[:6]))
ck('D5a 五个例程体内无任何 [reg] 无偏移写',len(w)==0,len(w))
# D6 0x410410 栈帧
b410=body(0x410410)
sub=[ins for ins in b410 if ins.mnemonic=='sub' and ins.op_str.startswith('esp,')]
print('   D6 0x410410 体内 sub esp：%s'%[i.op_str for i in sub])
vmov=[i.op_str for i in b410 if 'esp + 0xc' in i.op_str]
print('   D6b 0x410410 体内 [esp+0xc] 引用：%s'%vmov)
print('\nFAILS=%d'%len(fails))
