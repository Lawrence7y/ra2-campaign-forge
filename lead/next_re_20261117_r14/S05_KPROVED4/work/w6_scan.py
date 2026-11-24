# -*- coding: utf-8 -*-
"""扫描候选：条件分支中调用的不同虚表槽（③b① 互斥闸+异目标），以及 test/jl 返回约定。"""
import glob,re
for fn in sorted(glob.glob('DIS_*.txt')):
    lines=open(fn,encoding='utf-8').read().splitlines()
    vslots=set(); cond_vcall=0
    for i,l in enumerate(lines):
        m=re.search(r'call\s+dword ptr\s+\[\w+\s*\+\s*(0x[0-9a-f]+)\]',l)
        if m: vslots.add(m.group(1))
    # test eax / jl / ret 或 cmp eax,imm / 多 ret 常量
    negret=0
    for i,l in enumerate(lines):
        if re.search(r'\bjl\b|\bjle\b',l) and i>0 and re.search(r'test\s+eax,eax|cmp\s+eax',lines[i-1]):
            if any(re.search(r'\bret\b',x) for x in lines[i:i+4]): negret+=1
    if len(vslots)>=3 or negret>=1:
        print('%s: distinct_vslots=%d %s  negret_patterns=%d' % (fn,len(vslots),sorted(vslots)[:12],negret))
