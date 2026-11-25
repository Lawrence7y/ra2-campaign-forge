# -*- coding: utf-8 -*-
"""R135-DS · 卡外补充（只读）：63 张双桩表的 126 个槽引用去重后指向几个不同桩体地址。
回答「40 次桩」与「63/77 双槽皆桩」是否矛盾。"""
import struct, io, collections, re
D = io.open('/home/t628/projects/ra2-campaign-forge/ra2bench/gamemd.exe','rb').read()
e=struct.unpack_from('<I',D,0x3C)[0]; opt=e+24; soh=struct.unpack_from('<H',D,e+20)[0]
nsec=struct.unpack_from('<H',D,e+6)[0]; S=[]
for i in range(nsec):
    o=opt+soh+i*40; nm=D[o:o+8].rstrip(b'\0').decode()
    vs,va,rs,ro=struct.unpack_from('<IIII',D,o+8); S.append(dict(name=nm,va=va,vs=vs,ro=ro,rs=rs))
IMG=0x400000
def off_va(va):
    r=va-IMG
    for s in S:
        if s['va']<=r<s['va']+max(s['vs'],s['rs']): return s['ro']+(r-s['va'])
def dw_va(va):
    o=off_va(va); return None if o is None else struct.unpack_from('<I',D,o)[0]
def cstr(va,n=200):
    o=off_va(va); return '' if o is None else D[o:o+n].split(b'\0')[0].decode('latin-1')
STUB=bytes.fromhex('B801000000C20400')
rd=[s for s in S if s['name']=='.rdata'][0]
by=collections.defaultdict(list)
for o in range(rd['ro'], rd['ro']+rd['rs']-4, 4):
    if not (0x401000<=struct.unpack_from('<I',D,o)[0]<0x7E1000): continue
    va=IMG+(o-rd['ro']+rd['va']); col=dw_va(va-4)
    if col is None: continue
    td=dw_va(col+0xC)
    if td is None: continue
    nm=cstr(td+8)
    if not nm.startswith('.?A'): continue
    n=0
    while True:
        v=dw_va(va+4*n)
        if v is None or not (0x401000<=v<0x7E1000): break
        n+=1
    by[nm].append((va,n))
FAC=re.compile(r'^\.\?AV\?\$TClassFactory@V([^@]+)@@@@$')
Xs=sorted({m.group(1) for nm in by for m in [FAC.match(nm)] if m})
used=[]; owners=collections.defaultdict(list)
for x in Xs:
    lst=by.get('.?AV%s@@'%x)
    if not lst: continue
    va,n=max(lst,key=lambda t:(t[1],-t[0]))
    s1=dw_va(va+4); s2=dw_va(va+8)
    if D[off_va(s1):off_va(s1)+8]==STUB and D[off_va(s2):off_va(s2)+8]==STUB:
        used += [s1,s2]; owners[s1].append(x); owners[s2].append(x)
print('63 张双桩表共 %d 个槽引用，去重后 %d 个不同桩体地址:' % (len(used), len(set(used))))
for a in sorted(set(used)):
    print('  0x%08X 被引用 %d 次  (例: %s)' % (a, used.count(a), ','.join(owners[a][:4])))
print('对比: 全镜像 8 字节桩体出现 40 次（其中被数据节引用的 14 处、未引用 26 处）')
