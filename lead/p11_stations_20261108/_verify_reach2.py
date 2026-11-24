# -*- coding: utf-8 -*-
# 复核：扩大扫描范围（到 0x414D00 / 0x418000），确认 0x414AE5 / 0x417422 是否被任何 .text 直接跳转到达
import struct, re
from capstone import Cs, CS_ARCH_X86, CS_MODE_32
EXE=r'D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe'
d=open(EXE,'rb').read()
def off(va): return va-0x400000
def u32(va): return struct.unpack_from('<I',d,off(va))[0]
md=Cs(CS_ARCH_X86,CS_MODE_32)

def all_targets_in(lo,hi,accept):
    direct=set(); tables=[]
    # 线性解码（对齐从 lo 开始）
    for ins in md.disasm(d[off(lo):off(hi)],lo):
        if ins.address>hi: break
        if ins.mnemonic in ('jmp','call') and ins.op_str.startswith('0x'):
            try: direct.add(int(ins.op_str,16))
            except: pass
        if ins.mnemonic=='jmp' and '*4' in ins.op_str and 'ptr [' in ins.op_str:
            m=re.search(r'\+\s*(0x[0-9a-f]+)\]',ins.op_str)
            if m:
                tb=int(m.group(1),16)
                if 0x401000<=tb<0x7E0000: tables.append((ins.address,tb))
    return direct,tables

print('=== [0x414A00,0x414D00) 扩大范围 ===')
dj,tb=all_targets_in(0x414A00,0x414D00,None)
print('  direct jmp/call targets in 0x414AE0..0x414C00:',[hex(x) for x in sorted(dj) if 0x414AE0<=x<0x414C00])
print('  indirect tables:',[(hex(a),hex(b)) for a,b in tb])
for a,b in tb:
    print('    table 0x%X first6 %s'%(b,[hex(u32(b+4*i)) for i in range(6)]))

# 全 .text 中所有 jmp [reg*4+disp] 的跳表，看 0x414AE5 是否在任何表里
print('\n=== 全 .text 间接跳表枚举，查 0x414AE5 / 0x417422 是否作为条目 ===')
alltabs=[]
lo,hi=0x401000,0x7E0000
# 分段线性解码以收齐
for ins in md.disasm(d[off(lo):off(hi)],lo):
    if ins.mnemonic=='jmp' and '*4' in ins.op_str and 'ptr [' in ins.op_str:
        m=re.search(r'\+\s*(0x[0-9a-f]+)\]',ins.op_str)
        if m:
            tb=int(m.group(1),16)
            if 0x401000<=tb<0x7E0000: alltabs.append(tb)
print('  total jmp [reg*4+disp] tables:',len(alltabs))
for target in (0x414AE5,0x414B3D,0x417422,0x4D45A2,0x4D42EC,0x4D498A):
    found=[]
    for tb in set(alltabs):
        for i in range(80):
            v=u32(tb+4*i)
            if v==target: found.append((hex(tb),i)); break
            if not (0x401000<=v<0x7E0000): break
    print('  target 0x%X in jump tables: %s'%(target,found or 'NONE'))

# 全 .text 直接 E8/E9 目标
print('\n=== 全 .text E8/E9 目标命中 ===')
text=d[off(lo):off(hi)]
for target in (0x414AE5,0x414B3D,0x417422,0x4D45A2):
    hits=[]
    for i in range(len(text)-5):
        if text[i] in (0xE8,0xE9):
            rel=struct.unpack_from('<i',text,i+1)[0]
            if (lo+i+5+rel)&0xFFFFFFFF==target: hits.append(lo+i)
    print('  0x%X : %s'%(target,[hex(x) for x in hits[:8]] or 'NONE'))

print('\n=== 0x414A80 函数体的 jmp 指令（0x414A80..0x414AE5）===')
for ins in md.disasm(d[off(0x414A80):off(0x414AE5)],0x414A80):
    if ins.mnemonic.startswith('j'):
        print('  %08x %-6s %s'%(ins.address,ins.mnemonic,ins.op_str))

print('\nDONE')
