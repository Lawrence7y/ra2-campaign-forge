# -*- coding: utf-8 -*-
# 独立复核：从宿主起点线性解码到派发站，检查中途是否有 ret/int3/不可解码 断点
# （回件自承「未做 CFG 级确认」，此项检验 = 判断「起点锚定」是否足以证明站点归属）
import struct
from capstone import Cs, CS_ARCH_X86, CS_MODE_32

EXE = r'D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe'
d = open(EXE, 'rb').read()
def off(va): return va - 0x400000
md = Cs(CS_ARCH_X86, CS_MODE_32)

# (站点, 声称宿主, 备注)
pairs = [
    (0x414B24, 0x414A80, 'Aircraft v138'),
    (0x414B64, 0x414A80, 'Aircraft v138 #2'),
    (0x417481, 0x416D50, 'MISSION_MOVE sm'),
    (0x4D4314, 0x4D4280, 'Foot/Infantry v151 #1'),
    (0x4D4686, 0x4D4280, 'Foot/Infantry v151 #2'),
    (0x4D49A3, 0x4D4280, 'Foot/Infantry v151 #3'),
    (0x4D4E3E, 0x4D4DC0, 'Foot v132'),
    (0x4DE056, 0x4DDF90, 'v150'),
    (0x50D1D2, 0x50D170, 'PickTargetByType'),
    (0x51F382, 0x51F330, 'Infantry v266'),
    (0x6ED15E, 0x6ED090, 'case0 handler'),
    (0x6F0253, 0x6F0130, 'caseNN handler'),
]

for site, host, tag in pairs:
    span = site - host
    code = d[off(host):off(site) + 16]
    insns = list(md.disasm(code, host))
    # 断流检查：连续指令地址是否首尾相接（capstone 会在无效字节处停止）
    breaks = []
    covered = host
    for ins in insns:
        if ins.address != covered:
            breaks.append((covered, ins.address))
        covered = ins.address + ins.size
        if ins.address >= site:
            break
    # 中途 ret / int3 / jmp 出界
    stops = [(ins.address, ins.mnemonic, ins.op_str) for ins in insns
             if ins.address <= site and ins.mnemonic in ('ret', 'retf', 'int3')]
    farjmp = [(ins.address, ins.mnemonic, ins.op_str) for ins in insns
              if ins.address <= site and ins.mnemonic == 'jmp' and
              ins.op_str.startswith('0x') and not (host <= int(ins.op_str, 16) <= site + 0x100)]
    print('site=0x%X host=0x%X span=0x%-5X %-24s decoded=%-5d gaps=%s ret/int3=%s farjmp=%s' %
          (site, host, span, tag, len(insns), breaks[:3] if breaks else 'NONE',
           [(hex(a), m) for a, m, o in stops[:4]] if stops else 'NONE',
           [(hex(a), o) for a, m, o in farjmp[:2]] if farjmp else 'NONE'))

print('\n=== 明细：0x4D4280 -> 0x4D49A3 附近的 ret/分界 ===')
code = d[off(0x4D4280):off(0x4D4A10)]
for ins in md.disasm(code, 0x4D4280):
    if ins.mnemonic in ('ret', 'retf', 'int3') or (ins.mnemonic == 'jmp' and ins.op_str.startswith('0x')):
        print('  %08x  %-6s %s' % (ins.address, ins.mnemonic, ins.op_str))

print('\n=== 明细：0x416D50 -> 0x417481 附近的 ret/分界 + 跳表数据区 ===')
code = d[off(0x416D50):off(0x4174A0)]
for ins in md.disasm(code, 0x416D50):
    if ins.mnemonic in ('ret', 'retf', 'int3') or (ins.mnemonic == 'jmp' and ins.op_str.startswith('0x')):
        print('  %08x  %-6s %s' % (ins.address, ins.mnemonic, ins.op_str))
print('  (0x4172E4 跳表 4 dwords raw =', d[off(0x4172E4):off(0x4172F4)].hex(' '), ')')

print('\nDONE')
