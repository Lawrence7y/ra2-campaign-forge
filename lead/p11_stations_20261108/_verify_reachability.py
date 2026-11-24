# -*- coding: utf-8 -*-
# 独立复核：vtable 锚定宿主与派发站之间的「ret 后代码段」是否由宿主函数内部跳转到达
# （即：PASS2 跨 C3 的归属是否成立，还是把相邻独立函数误并）
import struct
from capstone import Cs, CS_ARCH_X86, CS_MODE_32

EXE = r'D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe'
d = open(EXE, 'rb').read()
def off(va): return va - 0x400000
def u32(va): return struct.unpack_from('<I', d, off(va))[0]
md = Cs(CS_ARCH_X86, CS_MODE_32)

# 收集一个区间内所有直接 jmp/call 目标 + 间接跳表基址
def edges(start, end):
    direct=set(); indirect=[]
    for ins in md.disasm(d[off(start):off(end)], start):
        if ins.address>end: break
        if ins.mnemonic=='jmp' and ins.op_str.startswith('0x'):
            direct.add(int(ins.op_str,16))
        if ins.mnemonic=='jmp' and 'ptr [' in ins.op_str and '*4' in ins.op_str:
            # 提取 disp32 绝对地址
            import re
            m=re.search(r'\+\s*(0x[0-9a-f]+)\]',ins.op_str)
            if m: indirect.append((ins.address,int(m.group(1),16)))
    return direct,indirect

def table_entries(base, n):
    return [u32(base+4*i) for i in range(n)]

print('=== 0x414A80 宿主区间 [0x414A80,0x414BA0) 的跳转边 ===')
dj,ij=edges(0x414A80,0x414BA0)
print('  direct jmp targets:', [hex(x) for x in sorted(dj)])
print('  indirect tables:',[(hex(a),hex(b)) for a,b in ij])
print('  -> 0x414AE5 (station #1 region) reached by direct jmp?', 0x414AE5 in dj)

print('\n=== 0x4D4280 宿主区间 [0x4D4280,0x4D4B04) 的跳转边 ===')
dj,ij=edges(0x4D4280,0x4D4B04)
print('  direct jmp targets (<=0x4D4B04):', [hex(x) for x in sorted(dj) if x<0x4D4B04][:30])
print('  indirect tables:',[(hex(a),hex(b)) for a,b in ij])
for tb in [b for a,b in ij]:
    # 尝试读 4/5/6 条目
    ents=table_entries(tb,8)
    print('  table 0x%X first8: %s'%(tb,[hex(x) for x in ents]))
print('  station regions 0x4D42EC / 0x4D45A2 / 0x4D498A reachable?')
for t in (0x4D42EC,0x4D45A2,0x4D498A):
    hit_dj = t in dj
    hit_tbl = any(u32(b+4*i)==t for a,b in ij for i in range(16) if 0x401000<=u32(b+4*i)<0x7E0000)
    print('    0x%X direct=%s in_switch_table=%s'%(t,hit_dj,hit_tbl))

print('\n=== 0x416D50 宿主区间 [0x416D50,0x4174A0) 的跳转边 ===')
dj,ij=edges(0x416D50,0x4174A0)
print('  indirect tables:',[(hex(a),hex(b)) for a,b in ij])
for tb in [b for a,b in ij]:
    ents=table_entries(tb,8)
    print('  table 0x%X first8: %s'%(tb,[hex(x) for x in ents]))
print('  direct jmp targets near station:',[hex(x) for x in sorted(dj) if 0x417300<=x<0x417500])
# 站 0x417481 所在段起点 0x417422 (last ret 0x417421+1) 是否被直接跳到
print('  station 0x417481; last ret before = 0x417421, segment start 0x417422')
print('  is 0x417422 a direct jmp target?', 0x417422 in dj)
print('  direct jmp targets in [0x417400,0x417500):',[hex(x) for x in sorted(dj) if 0x417400<=x<0x417500])

print('\n=== 0x4DDF90 / 0x51F330 区间内 ret 到站之间（应 NONE）复核 ===')
for host,site in ((0x4DDF90,0x4DE056),(0x51F330,0x51F382)):
    rets=[ins.address for ins in md.disasm(d[off(host):off(site)],host) if ins.mnemonic in ('ret','retf')]
    print('  host 0x%X -> site 0x%X  rets=%s'%(host,site,[hex(a) for a in rets] or 'NONE'))

print('\nDONE')
