# -*- coding: utf-8 -*-
# 独立复核：解码 0x6E9050 switch 派发 + case 块边界 + 0x6F0130/0x6ED090 的调用者归属
import struct
from capstone import Cs, CS_ARCH_X86, CS_MODE_32

EXE = r'D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe'
d = open(EXE, 'rb').read()
def off(va): return va - 0x400000
def u32(va): return struct.unpack_from('<I', d, off(va))[0]

md = Cs(CS_ARCH_X86, CS_MODE_32)
md.detail = False

TBL = 0x6E9F74
table = [u32(TBL + 4 * i) for i in range(65)]

# --- 1) switch 派发器 ---
print('=== 派发器 0x6E945B 邻域 ===')
code = d[off(0x6E9450):off(0x6E9470)]
for ins in md.disasm(code, 0x6E9450):
    print('  %08x  %-8s %s' % (ins.address, ins.mnemonic, ins.op_str))

# --- 2) case 块边界：从每个 entry 起点线性解码到首个 ret / 无条件 jmp ---
def block_end(start, maxn=80):
    code = d[off(start):off(start) + 0x200]
    n = 0
    for ins in md.disasm(code, start):
        n += 1
        if n > maxn: break
        if ins.mnemonic == 'ret' or ins.mnemonic == 'retf':
            return ins.address, ins.size, 'ret'
        if ins.mnemonic == 'jmp' and n > 1:
            return ins.address, ins.size, 'jmp'
    return None, None, 'noend'

print('\n=== 关键 case 块边界（入口 -> 终止） ===')
for idx in (0, 16, 49, 55, 56, 57, 58):
    s = table[idx]
    e, sz, kind = block_end(s)
    print('entry[%d]=0x%X  block=[0x%X,0x%X]  end=%s' %
          (idx, s, s, (e + sz) if e else 0, kind))

# --- 3) 调用 0x6ED090 和 0x6F0130 的指令落在哪个 entry 的块内 ---
print('\n=== 唯一直调者归属 ===')
for caller, target in [(0x6E978F, 0x6ED090), (0x6E9DD3, 0x6F0130)]:
    hits = []
    for idx, s in enumerate(table):
        e, sz, kind = block_end(s)
        if e is None: continue
        end = e + sz
        if s <= caller < end:
            hits.append((idx, s, end))
    print('caller 0x%X -> target 0x%X : in entry blocks %s' %
          (caller, target, [(i, hex(a), hex(b)) for i, a, b in hits]))

# --- 4) 0x6E9CE8 (Action49 Success 标志写) 落在哪个 entry 块 ---
print('\n=== Action49 标志写 0x6E9CE8 归属 ===')
for idx, s in enumerate(table):
    e, sz, kind = block_end(s)
    if e is None: continue
    if s <= 0x6E9CE8 < e + sz:
        print('  0x6E9CE8 in entry[%d]=0x%X block=[0x%X,0x%X]' % (idx, s, s, e + sz))

print('\nDONE')
