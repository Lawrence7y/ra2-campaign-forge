# -*- coding: utf-8 -*-
"""抽样取证（按站点）：直接用 rescan.py 写出的 _m1m2_sites.tsv 里的确切站点，
逐站点打印证据链，供人工判定。不重扫、不猜站点。

用法: python _dbg_sample.py 005AD130:0045AEA0 ...
      参数形式 entry:call_at（可只给 entry，取该行全部站点）
"""
import bisect
import csv
import sys

import pefile
from capstone import Cs, CS_ARCH_X86, CS_MODE_32
import capstone.x86 as cx86
from capstone.x86 import *

EXE = r'D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe'
ATLAS = r'D:\Project\ra2-campaign-forge\lead\next_re_20261112_r10\W130_atlas\function_atlas.tsv'
SITES = '_m1m2_sites.tsv'

pe = pefile.PE(EXE)
IB = pe.OPTIONAL_HEADER.ImageBase
sec = next(s for s in pe.sections if s.Name.rstrip(b'\x00') == b'.text')
VA = IB + sec.VirtualAddress
D = sec.get_data()
md = Cs(CS_ARCH_X86, CS_MODE_32); md.detail = True; md.skipdata = True

JCC = set(getattr(cx86, n) for n in dir(cx86)
          if n.startswith('X86_INS_J') and n != 'X86_INS_JMP'
          and isinstance(getattr(cx86, n), int))

atlas = {}
for ln in open(ATLAS, encoding='utf-8').read().splitlines()[1:]:
    p = ln.split('\t')
    if len(p) >= 3:
        try:
            atlas[int(p[0], 16)] = (int(p[1]), int(p[2]))
        except ValueError:
            pass
entries = sorted(atlas)


def func_of(va):
    i = bisect.bisect_right(entries, va) - 1
    ea = entries[i]
    if ea <= va < ea + atlas[ea][0]:
        return ea, atlas[ea][0]
    return None, 0


def dis(ea, size):
    return list(md.disasm(D[ea - VA:ea - VA + size], ea))


def fmt(x):
    return '%08X  %-16s %-8s %s' % (x.address, x.bytes.hex(' '), x.mnemonic, x.op_str)


def blocks_of(ins, start_addr, maxn=8):
    idx = {x.address: i for i, x in enumerate(ins)}
    i = idx.get(start_addr)
    if i is None:
        return None
    return ins[i:i + maxn]


def eax_returns(ea, size):
    ins = dis(ea, size)
    consts, mem, eaxcalls = set(), [], []
    cur = None
    for x in ins:
        if x.id == X86_INS_MOV and len(x.operands) == 2 \
                and x.operands[0].type == X86_OP_REG and x.operands[0].reg == X86_REG_EAX:
            if x.operands[1].type == X86_OP_IMM:
                cur = x.operands[1].imm & 0xFFFFFFFF
            elif x.operands[1].type == X86_OP_MEM:
                cur = None
                mem.append(x)
            else:
                cur = None
        elif x.id in (X86_INS_XOR, X86_INS_SUB) and len(x.operands) == 2 \
                and x.operands[0].type == X86_OP_REG and x.operands[0].reg == X86_REG_EAX \
                and x.operands[1].type == X86_OP_REG and x.operands[1].reg == X86_REG_EAX:
            cur = 0
        elif x.id == X86_INS_CALL:
            cur = None
            if x.operands and x.operands[0].type == X86_OP_IMM:
                eaxcalls.append(x.address)
        elif x.id == X86_INS_RET:
            if cur is not None:
                consts.add(cur)
            cur = None
    return sorted(consts), mem, len(ins), eaxcalls


sites = list(csv.DictReader(open(SITES, encoding='utf-8'), delimiter='\t'))
want = []
for a in sys.argv[1:]:
    if ':' in a:
        e, c = a.split(':')
        want.append((e, c.upper()))
    else:
        want.append((a, None))

for entry, only_call in want:
    cand = [s for s in sites if s['entry'].upper() == entry.upper()
            and (only_call is None or s['call_at'].upper() == only_call)]
    ea, size = func_of(int(entry, 16))
    print('=' * 106)
    print('== entry %s  函数 %08X size %d  站点 %d 个(n=%d)' % (entry, ea, size, len(cand), size))
    ins = dis(ea, size)
    for s in cand:
        print('-- [%s] call@%s  mov@%s  cmp@%s  witness=%s  jcc@%s -> %s' % (
            s['form'], s['call_at'], s['mov_at'], s['cmp_at'], s['witness'],
            s['jcc_at'], s['jcc_target']))
        for addr in (s['call_at'], s['mov_at'], s['cmp_at'], s['jcc_at']):
            blk = blocks_of(ins, int(addr, 16), 1)
            if blk:
                print('   %s' % fmt(blk[0]))
            else:
                print('   %s  (不在函数体内)' % addr)
        tgt = int(s['jcc_target'], 16) if s['jcc_target'] not in ('', 'OUT_OF_BODY') else None
        print('   taken 路径:')
        blk = blocks_of(ins, tgt, 6) if tgt is not None else None
        if blk:
            for x in blk:
                print('     %s' % fmt(x))
        else:
            print('     (目标在函数体外 — 尾部跳转/共享 epilogue)')
        print('   fall-through 路径:')
        jc = blocks_of(ins, int(s['jcc_at'], 16), 1)
        nxt = jc[0].address + jc[0].size if jc else None
        blk = blocks_of(ins, nxt, 6) if nxt else None
        if blk:
            for x in blk:
                print('     %s' % fmt(x))
        else:
            print('     (超出函数体)')
        c0 = blocks_of(ins, int(s['call_at'], 16), 1)
        if c0 and c0[0].operands and c0[0].operands[0].type == X86_OP_IMM:
            t2 = c0[0].operands[0].imm
            ce, cs2 = func_of(t2)
            if ce is None:
                print('   callee %08X: 不在 atlas' % t2)
            else:
                consts, mem, ni, ec = eax_returns(ce, cs2)
                print('   callee %08X (entry %08X, %d insns):' % (t2, ce, ni))
                print('     eax 立即数返回集 = %s' % ['0x%X' % c for c in consts])
                print('     mov eax,[mem] 处数 = %d ; callee 内直接 call 数 = %d'
                      % (len(mem), len(ec)))
        else:
            print('   callee: 间接调用（vtable/函数指针）%s'
                  % (c0[0].op_str if c0 else '?'))
    cmps = [(x.address, x.op_str) for x in ins
            if x.id == X86_INS_CMP and len(x.operands) == 2
            and x.operands[1].type == X86_OP_IMM]
    print('-- 本函数 cmp r/m,imm 共 %d 处: %s' % (
        len(cmps), ', '.join('%08X:%s' % t for t in cmps[:16])))
