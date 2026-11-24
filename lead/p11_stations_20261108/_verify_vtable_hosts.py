# -*- coding: utf-8 -*-
# 独立复核：vtable 锚定「宿主起点」到派发站之间是否被 ret 分隔；
# 复核回件 §3 的 8 站「vtable dword 精确锚定」是否证明站点归属该 vtable 函数。
import struct
from capstone import Cs, CS_ARCH_X86, CS_MODE_32

EXE = r'D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe'
d = open(EXE, 'rb').read()
def off(va): return va - 0x400000
md = Cs(CS_ARCH_X86, CS_MODE_32)

text = d[off(0x401000):off(0x401000)+0x3df000]
def direct_callers(target):
    out=[]
    for i in range(len(text)-5):
        if text[i] in (0xE8,0xE9):
            rel=struct.unpack_from('<i',text,i+1)[0]
            va=0x401000+i
            if (va+5+rel)&0xFFFFFFFF==target: out.append(va)
    return out

stations = [
    (0x414B24, 0x414A80, 'Aircraft v138'),
    (0x414B64, 0x414A80, 'Aircraft v138 #2'),
    (0x4D4314, 0x4D4280, 'Foot/Inf v151 #1'),
    (0x4D4686, 0x4D4280, 'Foot/Inf v151 #2'),
    (0x4D49A3, 0x4D4280, 'Foot/Inf v151 #3'),
    (0x4D4E3E, 0x4D4DC0, 'Foot v132'),
    (0x4DE056, 0x4DDF90, 'v150 four-class'),
    (0x51F382, 0x51F330, 'Infantry v266'),
]
print('=== host -> station 之间的 ret(C3/C2) 与填充 ===')
for site, host, tag in stations:
    code = d[off(host):off(site)+8]
    rets=[]
    for ins in md.disasm(code, host):
        if ins.address > site: break
        if ins.mnemonic in ('ret','retf'):
            nxt = d[off(ins.address+ins.size)]
            rets.append((ins.address, ins.mnemonic, ins.op_str, hex(nxt)))
    hs = d[off(host)-8:off(host)].hex(' ')
    print('  %-22s site=0x%X host=0x%X  ret_between=%s  pad_before=%s' %
          (tag, site, host, [(hex(a),m,o,n) for a,m,o,n in rets[:6]] or 'NONE', hs))
    # 站点所在「自 ret 之后」的段是否有任何直接引用
    seg = site - (max([a for a,_,_,_ in rets], default=host) + 1)
    nxt_start = max([a+1 for a,_,_,_ in rets], default=host)
    refs = direct_callers(nxt_start)
    print('      post-ret segment start=0x%X len=0x%X  E8/E9 callers=%s' %
          (nxt_start, seg, [hex(x) for x in refs[:6]] or 'NONE'))

print('\n=== 0x4D4280 起点反汇编（前 30 条）===')
for ins in md.disasm(d[off(0x4D4280):off(0x4D4340)], 0x4D4280):
    print('  %08x  %-8s %s' % (ins.address, ins.mnemonic, ins.op_str))

print('\n=== 0x51F330 起点反汇编（前 25 条）===')
for ins in md.disasm(d[off(0x51F330):off(0x51F395)], 0x51F330):
    print('  %08x  %-8s %s' % (ins.address, ins.mnemonic, ins.op_str))

print('\nDONE')
