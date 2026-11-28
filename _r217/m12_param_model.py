# -*- coding: utf-8 -*-
"""R217 m12：QI 0x410260 的实参模型裁定（card A 报 IID=esp+8、ppv=esp+0xc；主会话读点全为 esp+0xc 与 esp+0x18）。
事实：三处栈读的『原 esp 偏移』= 0xc(两次) / 0x18(一次)，push 累计 8。
判据：本函数 ret 0xc => 清 3 个栈参(+4/+8/+0xc)。因 +4 = this(ecx 传入，CALLCONV thiscall)，
      故 esp+8 = riid 或 ppv 之一，esp+0xc = 另一个。
关键：0x410294/0x4102a9/0x4102be 三条 mov dword ptr [eax], X 写入的是 [esp+0xc] 解引用的指针 => esp+0xc = ppv。
因此 IID = esp+8，且被 mov edx,[esp+0xc] 之后 mov esi,edx 复用 —— 这是编译器复用同一槽位而非读 esp+8。
反控：若 esp+0xc 是 IID，则 mov [eax],ebx 会写 IID（常量 IID 段），可在 .rdata 上验写保护。
"""
import sys,struct,json
sys.path.insert(0,'_r185'); import pe185 as P
from capstone import *
md=Cs(CS_ARCH_X86,CS_MODE_32)
o=P.r2o(0x410260); ins=list(md.disasm(P.RAW[o:o+0x9a],0x410260))
print('=== 全部栈写/读 ===')
for i in ins:
    if '[esp' in i.op_str:
        print('  %08x %-34s %s'%(i.address,i.bytes.hex(),i.mnemonic+' '+i.op_str))
print()
print('=== 决策点逐条 ===')
# 找出所有 'mov dword ptr [reg], src' 且 reg 来自 [esp+..] 的链
print('  0x410260 mov eax,[esp+0xc]  => eax = 栈参#1(原 esp+0xc)')
print('  0x410265 test eax,eax / jne => 该参数非空校验，失败返 0x80004003(E_POINTER)')
print('  => 被校验非空的是 ppv（输出指针），符合 COM 惯例')
print('  0x410272 mov edx,[esp+0xc]  => 再读同一参数 = ppv！！！  两者同为 0xc')
print('  0x41028c mov ebx,[esp+0x10] => 原 esp+0x18；此时已 push ebx/esi/edi => 3*4=12 不对，看实测 delta=8')
# 精确 delta 追踪
d=0; rows=[]
for i in ins:
    if i.mnemonic=='push': 
        rows.append((i.address,'push',d,i.op_str)); d+=4; continue
    if i.mnemonic=='pop':
        d-=4; rows.append((i.address,'pop',d,i.op_str)); continue
    if '[esp +' in i.op_str:
        x=int(i.op_str.split('[esp +')[1].split(']')[0].strip(),16)
        rows.append((i.address,'read',d,'原 esp+%#x  %s'%(x+d,i.mnemonic+' '+i.op_str)))
for r in rows: print('   %08x %-5s delta=%-2d %s'%r)
print()
print('结论：读取的原 esp 偏移 = 0xc(本函数首条) / 0xc(0x410272) / 0x18(0x41028c)。')
print('  ret 0xc 清 3 个栈参：this 由 ecx 传入（thiscall），栈参 3 个 = (?, ?, ?) @ esp+4/8/c。')
print('  0x41028c 在 push ebx/esi/edi 之后读 [esp+0x10]：delta 实测 8 => 原 esp+0x18，超出 3 参范围。')
print('  => 该读点不是入参，而是读调用者栈帧的上一参数槽/或 ebp 帧内局部，需以调用点 0x4142a2 实参顺序反推。')
