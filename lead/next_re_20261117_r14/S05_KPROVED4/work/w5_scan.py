# -*- coding: utf-8 -*-
"""扫描所有 DIS dump：计算型跳转/跳表 + ret 前常量返回值集合。"""
import glob,re,os
for fn in sorted(glob.glob('DIS_*.txt')):
    lines=open(fn,encoding='utf-8').read().splitlines()
    computed=[l.strip() for l in lines if re.search(r'jmp\s+(dword|word)\s+ptr|jmp\s+(eax|edx|ecx|ebx|esi|edi)\b|\*\s*4\s*\+',l)]
    # ret 前 mov eax,imm / xor eax,eax
    rets=[]
    for i,l in enumerate(lines):
        if re.search(r'\bret\b',l):
            for j in range(i-1,max(-1,i-6),-1):
                m=re.search(r'mov\s+eax,\s*(0x[0-9a-f]+|\d+)\s*$',lines[j])
                if m: rets.append(m.group(1)); break
                if re.search(r'xor\s+eax,eax',lines[j]): rets.append('0'); break
                if re.search(r'setge\s+cl|sete\s+cl|setne\s+cl',lines[j]): rets.append('cl+base'); break
    if computed or len(set(rets))>=2:
        print('===',fn,'computed_jmp=',len(computed),'retconsts=',sorted(set(rets)))
        for c in computed[:6]: print('   JMP',c)
