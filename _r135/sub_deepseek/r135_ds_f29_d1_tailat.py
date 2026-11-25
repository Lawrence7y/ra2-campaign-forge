# -*- coding: utf-8 -*-
"""R135-DS · D1 尾部 @ 个数核查（只读）：确认 77 个工厂类型名字符串尾部都是 4 个 @。"""
import re, io, collections
D = io.open('/home/t628/projects/ra2-campaign-forge/ra2bench/gamemd.exe','rb').read()
P = re.compile(rb'\.\?AV\?\$TClassFactory@V([^@]+)@')
ms = [(m.start(), m.group(1)) for m in P.finditer(D)]
PRE = b'.?AV?$TClassFactory@V'
tails = collections.Counter()
for s, x in ms:
    end = s + len(PRE) + len(x); k = 0
    while D[end+k:end+k+1] == b'@': k += 1
    tails[k] += 1
print('命中 %d ; 不同 X %d' % (len(ms), len({x for _, x in ms})))
print('X 之后紧跟的 @ 个数分布 = %s' % dict(tails))
for s, x in ms[:3]:
    print('  样例 RVA=0x%06X 全串=%r' % (s, D[s:s+len(PRE)+len(x)+4]))
