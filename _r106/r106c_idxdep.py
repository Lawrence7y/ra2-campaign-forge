#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""r106c_idxdep.py —— 索引寄存器数据流分析（权威 op_access 版）

为什么需要这一层：
  19 张表的 holder 都是 jmp dword ptr [reg*4+base]，表项值只说明「跳去哪」。
  判断不同输入是否走**语义等价**的代码，不能只看项值是否相同，
  必须看目标块在定义 reg 之前**是否读取 reg（旧值）**：
    - 读 => 同一目标对不同索引行为不同，项值相同 != 语义等价
    - 不读（reg 在本块内先被定义/已死）=> 该块对到达它的所有索引行为相同，项值相同 = 真等价

本轮初版判据栽了两处（均由反控当场抓出，如实保留）：
  E1 「op0 是 idx 寄存器」就当成写 —— 对 cmp eax,6 这类只读指令会误判成写，
     把「依赖」判成「不依赖」。实测 0x728c0e cmp eax,6 被误判 IDX_DEAD_HERE。
  E2 只用 memory_index 判「内存是否用到 idx」——对 mov cl,[eax+disp] 这种
     **基址**是 eax 而 index 为空的寻址方式完全看不见。
修正：改用 iced 的 InstructionInfoFactory 取 op_access（权威的读/写分类），
      内存操作数另外判 memory_base 与 memory_index 两者。
"""
import struct, sys, os, json
from collections import Counter
sys.path.insert(0, '/home/t628/projects/ra2-campaign-forge/_r104/vendor')
import iced_x86

OpK = iced_x86.OpKind
FC = iced_x86.FlowControl
OA = iced_x86.OpAccess
REG = iced_x86.Register

_IIF = iced_x86.InstructionInfoFactory()
READS = (OA.READ, OA.READ_WRITE, OA.READ_COND_WRITE, OA.COND_READ)
WRITES = (OA.WRITE, OA.READ_WRITE, OA.READ_COND_WRITE, OA.COND_WRITE)

raw = open('/home/t628/projects/ra2-campaign-forge/ra2bench/gamemd.exe', 'rb').read()
e = struct.unpack_from('<I', raw, 0x3c)[0]
nsec, = struct.unpack_from('<H', raw, e + 6)
osz, = struct.unpack_from('<H', raw, e + 20)
opt = e + 24
IB = struct.unpack_from('<I', raw, opt + 28)[0]
secs = []
for i in range(nsec):
    o = opt + osz + i * 40
    nm = raw[o:o + 8].rstrip(b'\0').decode()
    vs, rva, rs, ra = struct.unpack_from('<IIII', raw, o + 8)
    secs.append((nm, rva, vs, ra, rs))

def off(va):
    r = va - IB
    for nm, srva, vs, ra, rs in secs:
        if srva <= r < srva + max(vs, rs):
            return ra + (r - srva)
    return None

def u32(va):
    return struct.unpack_from('<I', raw, off(va))[0]

def dec1(va):
    o = off(va)
    if o is None:
        return None
    d = iced_x86.Decoder(32, raw[o:o + 15], ip=va)
    return d.decode() if d.can_decode else None

def rw(i, idx):
    """权威 op_access：返回 (reads_old_idx, writes_idx)

    两条 idiom 必须显式豁免，否则会把「常量折叠」误判成「依赖旧值」（本轮 E3/E4）：
      E3 sbb r,r   —— 结果 = -CF，只依赖标志位，不依赖 r 的旧值
      E4 or  r,-1  —— 结果恒为全 1，不依赖 r 的旧值
    """
    info = _IIF.info(i)
    reads = False
    writes = False
    # E3/E4 常量折叠：无论 op_access 怎么标，结果与旧值无关
    # E4 附：or r,-1 的立即数在 iced 下 op_kind 是 IMMEDIATE8TO32、immediate32 = 0xff（8 位 -1
    #      符号扩展到 32 位 = 0xFFFFFFFF），故必须按 op_kind 分档取有符号值再扩位，
    #      不能只比 op_kind == IMMEDIATE32（这是本轮 E4 第二次栽的同一处）
    const_fold = False
    if i.op_count == 2 and i.op_kind(0) == OpK.REGISTER and i.op_register(0) == idx:
        if i.op_kind(1) == OpK.REGISTER and i.op_register(1) == idx \
                and i.mnemonic == iced_x86.Mnemonic.SBB:
            const_fold = True
        if i.mnemonic == iced_x86.Mnemonic.OR:
            k1 = i.op_kind(1)
            imm32 = None
            if k1 == OpK.IMMEDIATE32:
                imm32 = i.immediate32 & 0xFFFFFFFF
            elif k1 == OpK.IMMEDIATE8TO32:
                imm32 = (i.immediate32 | 0xFFFFFF00) & 0xFFFFFFFF if (i.immediate32 & 0x80) else i.immediate32 & 0xFFFFFFFF
            elif k1 == OpK.IMMEDIATE8:
                imm32 = (i.immediate8 | 0xFFFFFF00) & 0xFFFFFFFF if (i.immediate8 & 0x80) else i.immediate8 & 0xFFFFFFFF
            if imm32 == 0xFFFFFFFF:
                const_fold = True
    for op in range(i.op_count):
        acc = info.op_access(op)
        k = i.op_kind(op)
        if k == OpK.REGISTER and i.op_register(op) == idx:
            if acc in READS and not const_fold:
                reads = True
            if acc in WRITES:
                writes = True
        elif k == OpK.MEMORY:
            # E2 修正：基址与索引都要看
            if i.memory_base == idx or i.memory_index == idx:
                if acc in READS:
                    reads = True
                # 写内存不改 idx 寄存器本身
    return reads, writes

KILLED_BY_CALL = {REG.EAX, REG.ECX, REG.EDX}   # MSVC cdecl 默认毁 eax/ecx/edx
REGNAME = {REG.EAX: 'eax', REG.ECX: 'ecx', REG.EDX: 'edx', REG.EBX: 'ebx',
           REG.ESP: 'esp', REG.EBP: 'ebp', REG.ESI: 'esi', REG.EDI: 'edi'}

FMT = iced_x86.Formatter(iced_x86.FormatterSyntax.INTEL)

def scan(va, idx, limit=120, max_jmps=4):
    ip = va
    jmps = 0
    for st in range(limit):
        i = dec1(ip)
        if i is None:
            return 'UNDECODABLE', hex(ip), st + 1
        reads, writes = rw(i, idx)
        if reads:
            return 'DEPENDS_ON_IDX', hex(ip) + ' ' + FMT.format(i), st + 1
        if writes:
            return 'IDX_DEAD_HERE', hex(ip) + ' ' + FMT.format(i), st + 1
        fc = i.flow_control
        if fc in (FC.CALL, FC.INDIRECT_CALL):
            if idx in KILLED_BY_CALL:
                return 'CALL_CLOBBER', hex(ip) + ' ' + FMT.format(i), st + 1
            ip += i.len
            continue
        if fc == FC.RETURN:
            return 'IDX_DEAD_HERE', hex(ip) + ' ret', st + 1
        if fc == FC.UNCONDITIONAL_BRANCH:
            jmps += 1
            if jmps > max_jmps:
                return 'JMP_CHAIN', hex(ip), st + 1
            ip = i.near_branch_target
            continue
        ip += i.len
    return 'LIMIT', hex(ip), limit

def table_vals(base, n):
    return [u32(base + 4 * i) for i in range(n)]

ROWS = [
    (0x46f5a0, 4, REG.ECX), (0x48db10, 13, REG.EDX), (0x48dd10, 5, REG.ECX),
    (0x4c8114, 46, REG.EAX), (0x5001e4, 5, REG.EAX), (0x58bda4, 5, REG.ECX),
    (0x69b15c, 4, REG.EAX), (0x6a92c4, 3, REG.ECX), (0x6adbdc, 3, REG.ECX),
    (0x6b0238, 7, REG.EAX), (0x6dfdec, 145, REG.EDX), (0x708d54, 5, REG.EAX),
    (0x71f2c0, 14, REG.EDX), (0x71f328, 10, REG.ECX), (0x71f778, 2, REG.EAX),
    (0x71f9e0, 2, REG.ECX), (0x728e08, 7, REG.EAX), (0x7291ac, 7, REG.ECX),
    (0x79f028, 5, REG.EDX),
]

if __name__ == '__main__':
    print('=== 反控：判据必须能抓到真依赖（4 正 4 负） ===')
    ctrl = [
        (0x46e4be, REG.ECX, 'DEPENDS_ON_IDX', 'holder 自身 jmp [ecx*4+base] 读 ecx'),
        (0x46e4b8, REG.EAX, 'DEPENDS_ON_IDX', 'mov cl,[eax+byte] 基址读 eax（E2 修正点）'),
        (0x728c0e, REG.EAX, 'DEPENDS_ON_IDX', 'cmp eax,6 只读（E1 修正点）'),
        (0x728c0a, REG.EAX, 'IDX_DEAD_HERE', 'mov eax,[edi+14h] 全写 eax'),
        (0x728de0, REG.EAX, 'IDX_DEAD_HERE', 'mov eax,[B0F910h] 全写 eax'),
        (0x728e0e, REG.EAX, 'IDX_DEAD_HERE', '（同块后续）'),
        (0x4c8109, REG.EAX, 'IDX_DEAD_HERE', 'pop edi..ret 不读 eax'),
        (0x69af45, REG.EAX, 'IDX_DEAD_HERE', 'mov ecx,71h 后 xor eax,eax 自清零'),
    ]
    for va, idx, exp, why in ctrl:
        v, w, st = scan(va, idx)
        mark = 'OK ' if v == exp else 'BAD'
        print('  %s %-10s -> %-15s %-40s %s' % (mark, hex(va), v, w, why))

    print()
    print('=== 重复项值组（8 组）的索引依赖判定 ===')
    res = []
    for base, n, idx in ROWS:
        vals = table_vals(base, n)
        c = Counter(vals)
        for t, k in sorted((t, k) for t, k in c.items() if k > 1):
            v, w, st = scan(t, idx)
            res.append((hex(base), hex(t), k, idx, v, w))
            print('  %-9s tgt=%-9s x%d idx=%-3s -> %-15s %s'
                  % (hex(base), hex(t), k, REGNAME[idx], v, w))

    print()
    print('=== 276 个去重目标值整体分布 ===')
    allc = Counter()
    for base, n, idx in ROWS:
        for t in sorted(set(table_vals(base, n))):
            v, w, st = scan(t, idx)
            allc[v] += 1
    for k, v in allc.most_common():
        print('  %-15s %d' % (k, v))
