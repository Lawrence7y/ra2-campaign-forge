# -*- coding: utf-8 -*-
"""R135-DS · 旁证 6（只读）：40 处 8 字节桩中，有多少处的地址被 .rdata/.data 里的 dword 引用（=「槽内」）。"""
import struct, io
D = io.open('/home/t628/projects/ra2-campaign-forge/ra2bench/gamemd.exe','rb').read()
e=struct.unpack_from('<I',D,0x3C)[0]; opt=e+24; soh=struct.unpack_from('<H',D,e+20)[0]
nsec=struct.unpack_from('<H',D,e+6)[0]; S=[]
for i in range(nsec):
    o=opt+soh+i*40; nm=D[o:o+8].rstrip(b'\0').decode()
    vs,va,rs,ro=struct.unpack_from('<IIII',D,o+8); S.append((nm,va,vs,ro,rs))
def secname_off(o):
    for nm,va,vs,ro,rs in S:
        if ro<=o<ro+rs: return nm
    return '<none>'
def off(rva):
    for nm,va,vs,ro,rs in S:
        if va<=rva<va+max(vs,rs): return ro+(rva-va)
STUB=b'\xB8\x01\x00\x00\x00\xC2\x04\x00'
offs=[]; p=D.find(STUB)
while p>=0: offs.append(p); p=D.find(STUB,p+1)
vtext = 0x00401000
ins=0; out=0
print('40 处桩的 VA 是否作为 dword 被引用（引用点所在节）:')
for o in offs:
    va = vtext + (o-0x1000)
    b=struct.pack('<I',va); hits=[]; q=D.find(b)
    while q>=0:
        hits.append((hex(q), secname_off(q))); q=D.find(b,q+1)
    ref = [h for h in hits if h[1] in ('.rdata','.data','.detour')]
    tag = '槽内(数据节有 dword 引用)' if ref else '槽外(无数据节引用)'
    if ref: ins+=1
    else: out+=1
    print('  VA=0x%08X %-28s refs=%s' % (va, tag, ref[:4]))
print('\n汇总: 有数据节引用 %d 处 / 无引用 %d 处（合计 %d）' % (ins, out, ins+out))
print('F29 limitations 说「槽内 14 / 槽外 26」 -> 与本次口径对比见 REPORT')
