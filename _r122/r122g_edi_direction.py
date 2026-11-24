#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""r122g: 裁决「35 个 edx 是保存器实参还是输出缓冲」—— 靠对 edi 的读写方向做字节实证。

背景（R122 审计 A4 列的替代解释 4）：
  x86 调用约定下「edx 作为 this 传入」与「被调函数把结果写回 edx 指向的对象」
  在调用点字节形态相同（都是 mov edx, addr; call）。要区分必须看被调函数体对
  [edx] 的读写方向。r122a/r122b 都没做这一步。

本脚本的做法：
  G1  取 35 个孪生函数体（入口 = 35 个调用站的 call 目标），逐字节确认 35 份全同
  G2  对孪生体做指令级扫描，把 edx 的初值（序言 mov edi, edx）追到 edi，
      然后统计全部 edi-relative 访问的「读/写」方向
  G3  对 25 个主函数站的内联体做同样的读写方向统计（不同源，不能外推）
  G4  裁决：若对内联/孪生体对 edi 只有读、0 写 => edx 是只读实参，排除输出缓冲解释
  G5  给出被读的偏移值（字节实证）

内存纪律：全部 disasm_lite；只对少数目标函数开 detail=False 的单指令解码；
不对整段 .text 开 detail=True。
"""
import collections
import hashlib
import json
import struct
import sys

import capstone
import pefile

EXE = '/home/t628/projects/ra2-campaign-forge/ra2bench/gamemd.exe'
OUT = '/home/t628/projects/ra2-campaign-forge/_r122/r122g_edi_direction.json'
RES = []


def ck(name, cond, detail=''):
    RES.append({'check': name, 'ok': bool(cond), 'detail': str(detail)[:300]})
    return bool(cond)


pe = pefile.PE(EXE, fast_load=True)
IB = pe.OPTIONAL_HEADER.ImageBase
SECS = []
for s in pe.sections:
    SECS.append(dict(name=s.Name.rstrip(b'\0').decode(),
                     va=IB + s.VirtualAddress, vs=s.Misc_VirtualSize,
                     pr=s.PointerToRawData, rs=s.SizeOfRawData))
DATA = open(EXE, 'rb').read()
SHA = hashlib.sha256(DATA).hexdigest()
TXT = [x for x in SECS if x['name'] == '.text'][0]
DS = [x for x in SECS if x['name'] == '.data'][0]
TDATA = DATA[TXT['pr']:TXT['pr'] + TXT['rs']]
TBASE = TXT['va']
TEND = TBASE + len(TDATA)
BSS_LO, BSS_HI = DS['va'] + DS['rs'], DS['va'] + DS['vs']


def sec_of(va):
    for x in SECS:
        if x['va'] <= va < x['va'] + x['vs']:
            return x
    return None


def rd(va, n):
    x = sec_of(va)
    if x is None or va - x['va'] + n > x['rs']:
        return None
    o = x['pr'] + va - x['va']
    return DATA[o:o + n]


def u32(va):
    b = rd(va, 4)
    return None if b is None else struct.unpack('<I', b)[0]


# ---------------- G1：重算 35 个调用站与 35 个孪生入口 ----------------
calls = collections.defaultdict(list)
for i in range(len(TDATA) - 5):
    if TDATA[i] != 0xe8:
        continue
    rel = struct.unpack_from('<i', TDATA, i + 1)[0]
    va = TBASE + i
    tgt = va + 5 + rel
    if 0x67fdf0 <= tgt <= 0x680f80:
        calls[tgt].append(va)

ALL_SITES = sorted(s for ss in calls.values() for s in ss)
TWINS_SITES = sorted(s for ss in calls.values() for s in ss
                     if s not in (0x67d193, 0x67e62b))
ck('G1a 重扫 call rel32 得到 37 站 / 36 入口',
   len(ALL_SITES) == 37 and len(calls) == 36,
   'sites=%d entries=%d' % (len(ALL_SITES), len(calls)))

# 35 个孪生入口 = 每个孪生站所在 call 的目标
tw_entry = {}
for site in TWINS_SITES:
    rel = struct.unpack_from('<i', TDATA, site - TBASE + 1)[0]
    tw_entry[site] = site + 5 + rel
twin_entries = sorted(set(tw_entry.values()))
ck('G1b 35 个孪生站对应的入口去重后 == 35 个',
   len(tw_entry) == 35 and len(twin_entries) == 35,
   'sites=%d distinct_entries=%d' % (len(tw_entry), len(twin_entries)))

# ---------------- G2：孪生体字节全同 ----------------
mdl = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
mdl.skipdata = True


def func_bytes(entry, maxlen=0x200):
    """从入口线性解码到 ret（含），返回 (字节, 指令列表)。"""
    off = entry - TBASE
    ins = []
    end = None
    for a, size, mnem, ops in mdl.disasm_lite(TDATA[off:off + maxlen], entry):
        ins.append((a, size, mnem, ops))
        if mnem.startswith('ret'):
            end = a + size
            break
    if end is None:
        return None, None
    return TDATA[off:end - TBASE], ins


bodies = {}
for e in twin_entries:
    b, ins = func_bytes(e)
    bodies[e] = (b, ins)
n_none = sum(1 for e, (b, i) in bodies.items() if b is None)
lens = sorted({len(b) for b, i in bodies.values() if b is not None})
hashes = {hashlib.sha256(b).hexdigest() for b, i in bodies.values() if b is not None}
ck('G2a 35 个孪生体都能解到 ret，且长度集合单一',
   n_none == 0 and len(lens) == 1, 'n_none=%d lens=%s' % (n_none, lens))
ck('G2b 35 个孪生体字节全同（不同 sha256 数 == 1）',
   len(hashes) == 1 and len(bodies) == 35,
   'n_bodies=%d distinct_sha256=%d' % (len(bodies), len(hashes)))

# ---------------- G3：edi-relative 访问的读/写方向 ----------------
# x86 写方向的判定（保守即宁可漏判也不误判为写）：
#   1) mnem 以 mov/lea 开头但不是 mov → 只考虑 mov/store 族；写 = 目标操作数是内存
#   2) 目标操作数是第一个操作数（Intel 语法，capstone 默认）
#   3) 形如 mov/and/or/xor/add/sub/inc/dec/push/pop 等中，只有「首操作数含 [edi...]」
#      且 mnem 属于写内存的族时才算写
#   4) string 指令（movs/stos）单独处理，本函数体内实测不存在
WRITE_MNEMS = {'mov', 'movzx', 'movsx', 'and', 'or', 'xor', 'add', 'sub',
               'inc', 'dec', 'neg', 'not', 'shl', 'shr', 'sar', 'sal',
               'cmovz', 'cmovnz', 'xchg'}


def edi_accesses(ins):
    """返回 [(addr, mnem, ops, direction, disp)]，只统计含 edi 的内存操作数。
    方向由「edi 内存操作数是不是首操作数 + mnem 是否属写族」判定。"""
    out = []
    for a, size, mnem, ops in ins:
        if 'edi' not in ops:
            continue
        # 找到含 edi 且是内存引用的操作数
        parts = [p.strip() for p in ops.split(',')]
        # 首操作数是目标（Intel）
        first = parts[0] if parts else ''
        is_mem_first = '[' in first and 'edi' in first
        is_mem_any = any('[' in p and 'edi' in p for p in parts)
        if not is_mem_any:
            continue
        disp = None
        for p in parts:
            if '[' in p and 'edi' in p:
                inner = p[p.index('[') + 1:p.index(']')]
                if '+' in inner:
                    t = inner.split('+')[1].strip()
                    try:
                        disp = int(t, 16)
                    except ValueError:
                        disp = t
                elif 'edi' in inner and '-' in inner:
                    disp = -int(inner.split('-')[1].strip(), 16)
                break
        if is_mem_first and mnem in WRITE_MNEMS:
            direction = 'write'
        else:
            direction = 'read'
        out.append(dict(addr='0x%08x' % a, mnem=mnem, ops=ops,
                        direction=direction, disp=disp))
    return out


# 定义 edx->edi 是否成立：孪生体序言必须是 mov edi, edx
def edx_alias_edi(ins):
    for a, size, mnem, ops in ins:
        o = ops.replace(' ', '')
        if mnem == 'mov' and o == 'edi,edx':
            return True
        if mnem == 'mov' and o.startswith('eax,'):
            continue
        # 序言内出现对 edi 的其它定义就停止
        if mnem.startswith('mov') and o.startswith('edi,'):
            return False
    return False


alias_ok = sum(1 for e, (b, ins) in bodies.items() if edx_alias_edi(ins))
ck('G3a 35 个孪生体都存在 mov edi, edx（edx 实参被别名到 edi）',
   alias_ok == 35, 'ok=%d/35' % alias_ok)

twin_acc = []
for e in sorted(bodies):
    b, ins = bodies[e]
    twin_acc.extend(edi_accesses(ins))
dirs = collections.Counter(x['direction'] for x in twin_acc)
ck('G3b 35 个孪生体对 [edi...] 的全部访问中，写 = 0（即 edx 指向的对象只被读）',
   dirs.get('write', 0) == 0 and dirs.get('read', 0) > 0,
   'read=%d write=%d' % (dirs.get('read', 0), dirs.get('write', 0)))

twin_disps = collections.Counter(x['disp'] for x in twin_acc if x['direction'] == 'read')
ck('G3c 孪生体读取 edi 的偏移集合恰为 {0x4, 0x10}（字节实证）',
   set(twin_disps) == {0x4, 0x10},
   'disps=%s' % dict(twin_disps))

# ---------------- G4：25 个主函数站的内联体，同口径统计 ----------------
# 定义来源 r122e（勿混用）：主函数 0x67d300 内 25 站 = 形态为 push 0x7f7c80 的站点，
# 不是「call 到 0x67fdf0 区间」的站（那是 35 站的定义）。两批不同源。
# 记忆纪律说明：此处 mdD 对「单个函数 0x1120 字节」开 detail=True。
# 这不是对整段 .text（4MB）开 detail，堆占用约数 MB，安全。
mdD = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
mdD.detail = True
MAIN_INSNS = list(mdD.disasm(rd(0x67d300, 0x1120), 0x67d300))
main25 = [x.address for x in MAIN_INSNS if x.mnemonic == 'push' and x.op_str == '0x7f7c80']
ck('G4a 主函数 0x67d300 内 push 0x7f7c80 的站数 == 25（r122e 口径）',
   len(main25) == 25, 'n=%d' % len(main25))

# 主函数里没有 edi 承载 edx 的别名（edi 不是容器），所以主函数内联体不能按 edi 口径统计。
# 改成统计「25 站各自的循环体内联块」里的内存写操作，看有没有对被保存元素/容器的写。
# 循环体上下界沿用 r122e 的精确判据：
#   起点 = 站点之前最近的「mov reg, dword ptr [.data 全局]」
#   终点 = 站点之后最近的「jl <起点地址>」（回边目标恰为起点）
idx_of = {ins.address: k for k, ins in enumerate(MAIN_INSNS)}


def data_global_before(k, span=12):
    for j in range(k - 1, max(-1, k - span), -1):
        ins = MAIN_INSNS[j]
        if ins.mnemonic != 'mov' or len(ins.operands) != 2:
            continue
        o1 = ins.operands[1]
        if (o1.type == capstone.x86.X86_OP_MEM and o1.mem.base == 0
                and o1.mem.index == 0 and o1.mem.disp != 0):
            a = o1.mem.disp & 0xffffffff
            x = sec_of(a)
            if x and x['name'] == '.data':
                return j, a
    return None, None


blocks = []
for site in main25:
    k = idx_of[site]
    j0, g = data_global_before(k)
    if j0 is None:
        blocks.append(None)
        continue
    j1 = None
    for j in range(k + 1, min(len(MAIN_INSNS), k + 40)):
        ins = MAIN_INSNS[j]
        if (ins.mnemonic == 'jl' and ins.operands
                and ins.operands[0].type == capstone.x86.X86_OP_IMM
                and ins.operands[0].imm == MAIN_INSNS[j0].address):
            j1 = j
            break
    blocks.append((j0, j1, g))

ck('G4b 25 站的内联块上下界全部定位到（回边 jl 目标 == 块起点）',
   all(b and b[1] is not None for b in blocks),
   'located=%d/25' % sum(1 for b in blocks if b and b[1] is not None))

# 对内联块逐条统计：内存写操作（首操作数含 '[' 且 mnem 属写族）。
# 关键排除：栈相对（[esp...]，[ebp...]）是编译器溢出槽，不是对容器的写。
# 不排除的话会把 25 条「mov [esp+0x10], edi」这类 spill 误算成容器写。
WR = {'mov', 'movzx', 'movsx', 'and', 'or', 'xor', 'add', 'sub', 'inc', 'dec'}


def is_stack_rel(ops):
    inner = ops[:ops.index(']') + 1] if '[' in ops else ''
    return 'esp' in inner or 'ebp' in inner


def first_operand_is_mem(ops):
    return '[' in ops.split(',')[0]


blk_writes = []
blk_reads = []
spill_writes = []
for b in blocks:
    if not b or b[1] is None:
        continue
    lo = MAIN_INSNS[b[0]].address
    hi = MAIN_INSNS[b[1]].address + MAIN_INSNS[b[1]].size
    for x in MAIN_INSNS:
        if not (lo <= x.address < hi):
            continue
        ops = x.op_str
        if '[' not in ops:
            continue
        if first_operand_is_mem(ops) and x.mnemonic in WR:
            if is_stack_rel(ops):
                spill_writes.append((hex(x.address), x.mnemonic, ops))
            else:
                blk_writes.append((hex(x.address), x.mnemonic, ops))
        else:
            blk_reads.append((hex(x.address), x.mnemonic, ops))
ck('G4c 25 个内联块内对非栈内存的写 == 0（栈溢出槽 %d 条已单列）' % len(spill_writes),
   len(blk_writes) == 0 and len(spill_writes) > 0,
   'heap/heap-like writes=%d ; stack spills=%d ; reads=%d ; write_sample=%s'
   % (len(blk_writes), len(spill_writes), len(blk_reads), blk_writes[:4]))

# ---------------- G5：裁决 ----------------
ck('G5 裁决：孪生体对 edx 指向对象只读（70 读 / 0 写），主函数内联块亦无内存写 => '
   '可排除「edx 是输出缓冲」，支持「edx 是只读实参（容器持有者）」',
   dirs.get('write', 0) == 0 and dirs.get('read', 0) > 0
   and len(blk_writes) == 0 and len(blk_reads) > 0,
   'twin r/w=%d/%d ; inline blocks read=%d write=%d'
   % (dirs.get('read', 0), dirs.get('write', 0),
      len(blk_reads), len(blk_writes)))

# ---------------- 自测（正反控） ----------------
def selftest():
    ok = []

    def t(name, cond, det=''):
        ok.append(dict(name=name, ok=bool(cond), detail=str(det)[:200]))

    # 正控 1：手工构造一条 mov eax, [edi+0x10]，必须判为 read
    ins = list(mdl.disasm_lite(b'\x8b\x47\x10', 0x1000))
    a1 = edi_accesses(ins)
    t('st1 正控：mov eax,[edi+0x10] 判为 read 且 disp=0x10',
      len(a1) == 1 and a1[0]['direction'] == 'read' and a1[0]['disp'] == 0x10,
      repr(a1))

    # 正控 2：手工构造 mov dword ptr [edi+0x4], eax，必须判为 write
    ins = list(mdl.disasm_lite(b'\x89\x47\x04', 0x1000))
    a2 = edi_accesses(ins)
    t('st2 正控：mov [edi+0x4],eax 判为 write 且 disp=0x4',
      len(a2) == 1 and a2[0]['direction'] == 'write' and a2[0]['disp'] == 0x4,
      repr(a2))

    # 反控 1：把 edx 别名检测喂给一个不含 mov edi,edx 的序列，必须返回 False
    ins = list(mdl.disasm_lite(b'\x89\xc8\x90', 0x1000))  # mov eax, ecx
    t('st3 反控：不含 mov edi,edx 的序列，别名检测必须为 False',
      edx_alias_edi(ins) is False, repr(ins))

    # 反控 2：正控序列 mov edi, edx 必须返回 True
    ins = list(mdl.disasm_lite(b'\x89\xd7', 0x1000))
    t('st4 正控：mov edi,edx 序列别名检测必须为 True',
      edx_alias_edi(ins) is True, repr(ins))

    # 反控 3：造一个「序言 mov edi,edx + 一条 mov [edi+4],eax」的合成体，
    # 方向统计必须翻成 write>0。不能用往真实孪生体里插字节的做法——
    # 插入点会破坏后续指令对齐，解码器 desync 后得到的是垃圾指令，
    # 那样测的是插入位置选得好不好，不是检测器灵不灵。
    fake = b'\x89\xd7' + b'\x89\x47\x04' + b'\x8b\x47\x10' + b'\xc3'
    ins = list(mdl.disasm_lite(fake, 0x1000))
    a3 = edi_accesses(ins)
    t('st5 反控：合成体含一条 mov [edi+4],eax 时，检测器必须报 write',
      sum(1 for x in a3 if x['direction'] == 'write') == 1
      and sum(1 for x in a3 if x['direction'] == 'read') == 1
      and edx_alias_edi(ins) is True,
      'writes=%d reads=%d ins=%r'
      % (sum(1 for x in a3 if x['direction'] == 'write'),
         sum(1 for x in a3 if x['direction'] == 'read'),
         [(hex(a), m, o) for a, _, m, o in ins]))

    # 反控 4：把 edi 换成 esi 后不得被统计（口径只认 edi）
    ins = list(mdl.disasm_lite(b'\x8b\x46\x10', 0x1000))  # mov eax,[esi+0x10]
    t('st6 反控：mov eax,[esi+0x10] 不被 edi 口径统计', len(edi_accesses(ins)) == 0,
      repr(ins))

    return ok


ST = selftest()
for s in ST:
    print(('  ST-PASS ' if s['ok'] else '  ST-FAIL ') + s['name'] + ' :: ' + s['detail'])
if not all(s['ok'] for s in ST):
    print('SELFTEST FAILED')
    sys.exit(2)

json.dump(dict(exe_sha256=SHA,
               n_all_sites=len(ALL_SITES), n_twin_sites=len(TWINS_SITES),
               n_twin_entries=len(twin_entries),
               twin_len=lens, twin_distinct_sha256=len(hashes),
               alias_ok=alias_ok,
               twin_dirs=dict(dirs), twin_disps={str(k): v for k, v in twin_disps.items()},
               main25_n=len(main25),
               inline_blocks_located=sum(1 for b in blocks if b),
               inline_reads=len(blk_reads), inline_writes=len(blk_writes),
               inline_read_sample=blk_reads[:6],
               inline_write_sample=blk_writes[:6],
               selftest=ST, checks=RES,
               all_ok=all(r['ok'] for r in RES) and all(s['ok'] for s in ST)),
          open(OUT, 'w'), indent=1)

for r in RES:
    print(('  PASS  ' if r['ok'] else '  FAIL  ') + r['check'] + ' :: ' + r['detail'])
print('checks %d ; PASS %d ; selftest %d ; ST-PASS %d'
      % (len(RES), sum(1 for r in RES if r['ok']), len(ST), sum(1 for s in ST if s['ok'])))
sys.exit(0 if all(r['ok'] for r in RES) and all(s['ok'] for s in ST) else 1)
