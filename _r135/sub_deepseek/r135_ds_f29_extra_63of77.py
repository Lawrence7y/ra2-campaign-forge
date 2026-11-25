# -*- coding: utf-8 -*-
"""R135-DS · 卡外补充（只读，非交付项）：独立复核 F29「77 张工厂表、产品类主虚表 slot1&slot2 双槽皆 8 字节桩 = 63/77」。
修正产品类名形态：产品类具名行程 = '.?AV' + X + '@@'（不是 @@@@）。"""
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
    return None
def dw_va(va):
    o=off_va(va); return None if o is None else struct.unpack_from('<I',D,o)[0]
def cstr_va(va,n=200):
    o=off_va(va)
    return '' if o is None else D[o:o+n].split(b'\0')[0].decode('latin-1')
STUB=bytes.fromhex('B801000000C20400')
def body8(va):
    o=off_va(va); return D[o:o+8] if o is not None else b''
rd=[s for s in S if s['name']=='.rdata'][0]
by=collections.defaultdict(list)
for o in range(rd['ro'], rd['ro']+rd['rs']-4, 4):
    v0=struct.unpack_from('<I',D,o)[0]
    if not (0x401000<=v0<0x7E1000): continue
    va=IMG+(o-rd['ro']+rd['va'])
    col=dw_va(va-4)
    if col is None: continue
    td=dw_va(col+0xC)
    if td is None: continue
    nm=cstr_va(td+8)
    if not nm.startswith('.?A'): continue
    n=0
    while True:
        v=dw_va(va+4*n)
        if v is None or not (0x401000<=v<0x7E1000): break
        n+=1
    by[nm].append((va,n))
FAC=re.compile(r'^\.\?AV\?\$TClassFactory@V([^@]+)@@@@$')
Xs=sorted({m.group(1) for nm in by for m in [FAC.match(nm)] if m})
rows=[]
for x in Xs:
    lst=by.get('.?AV%s@@' % x)
    if not lst:
        rows.append((x,None,None,None,None,None)); continue
    va,n=max(lst, key=lambda t:(t[1], -t[0]))
    s1=dw_va(va+4); s2=dw_va(va+8)
    rows.append((x,va,n,s1,s2,(body8(s1)==STUB, body8(s2)==STUB)))
both=sum(1 for r in rows if r[5]==(True,True))
print('工厂类型名 %d 种 ; 具名 vtable 总数 %d ; 不同名字 %d' % (len(Xs), sum(len(v) for v in by.values()), len(by)))
print('主表(槽数最多/并列最小地址) slot1&slot2 双槽皆 8 字节桩 = %d / %d   [F29 主张 63/77]' % (both, len(rows)))
print('  缺产品类具名 vtable = %d' % sum(1 for r in rows if r[1] is None))
print('  slot1桩 且 slot2非桩 / 反之 = %d' % sum(1 for r in rows if r[5] and r[5][0]!=r[5][1]))
print('  双槽皆非桩          = %d' % sum(1 for r in rows if r[5]==(False,False)))
print('\n逐类明细（按是否双桩分组打印）:')
for x,va,n,s1,s2,st in sorted(rows, key=lambda r:(-(r[5]==(True,True)), r[0])):
    print('  %-28s vt=%-10s slots=%-4s s1=%-10s s2=%-10s 双桩=%s'
          % (x, ('0x%08X'%va) if va else '-', n or '-',
             ('0x%08X'%s1) if s1 else '-', ('0x%08X'%s2) if s2 else '-',
             'YES' if st==(True,True) else 'no'))
