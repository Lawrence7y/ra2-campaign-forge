# -*- coding: utf-8 -*-
"""对 value_dispatch（多值分派形态）行做紧凑画像：
每个站点给出  call → mov → cmp(值) → jcc(方向)  以及
  callee 的 eax 立即数返回集 / 该见证值在本函数内被比较的全部常量 / 是否循环回边。
"""
import bisect
import csv

import pefile
from capstone import Cs, CS_ARCH_X86, CS_MODE_32
import capstone.x86 as cx86
from capstone.x86 import *

pe = pefile.PE(r'D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe')
IB = pe.OPTIONAL_HEADER.ImageBase
sec = next(s for s in pe.sections if s.Name.rstrip(b'\x00') == b'.text')
VA = IB + sec.VirtualAddress
D = sec.get_data()
md = Cs(CS_ARCH_X86, CS_MODE_32); md.detail = True; md.skipdata = True

atlas = {}
for ln in open(r'D:\Project\ra2-campaign-forge\lead\next_re_20261112_r10\W130_atlas\function_atlas.tsv',
               encoding='utf-8').read().splitlines()[1:]:
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


def callee_consts(ea, size):
    consts, cur = set(), None
    for x in dis(ea, size)[:4000]:
        if x.id == X86_INS_MOV and len(x.operands) == 2 \
                and x.operands[0].type == X86_OP_REG and x.operands[0].reg == X86_REG_EAX:
            cur = x.operands[1].imm & 0xFFFFFFFF if x.operands[1].type == X86_OP_IMM else None
        elif x.id in (X86_INS_XOR, X86_INS_SUB) and len(x.operands) == 2 \
                and x.operands[0].type == X86_OP_REG and x.operands[0].reg == X86_REG_EAX \
                and x.operands[1].type == X86_OP_REG and x.operands[1].reg == X86_REG_EAX:
            cur = 0
        elif x.id == X86_INS_CALL:
            cur = None
        elif x.id == X86_INS_RET:
            if cur is not None:
                consts.add(cur)
            cur = None
    return consts


rows = {r['entry']: r for r in csv.DictReader(open('_rows.tsv', encoding='utf-8'), delimiter='\t')}
sites = list(csv.DictReader(open('_m1m2_sites.tsv', encoding='utf-8'), delimiter='\t'))
vd = {}
for s in sites:
    if s['value_dispatch'] == '1':
        vd.setdefault(s['entry'], []).append(s)

newvd = [e for e in vd if int(rows[e]['m0_sites'])==0]
print('value-dispatch 行 %d，其中新增(m0=0) %d' % (len(vd), len(newvd)))
for e in sorted(newvd):
    r = rows[e]
    ins = dis(int(e, 16), int(r['size']))
    idx = {x.address: i for i, x in enumerate(ins)}
    print('-' * 108)
    print('%s %s %s  (m1=%s m2=%s)' % (e, r['subsystem'], r['name'], r['m1_sites'], r['m2_sites']))
    for s in vd[e]:
        c = int(s['call_at'], 16); mv = int(s['mov_at'], 16)
        cm = int(s['cmp_at'], 16); jc = int(s['jcc_at'], 16)
        wit = s['witness']
        consts_here = []
        for x in ins:
            if x.id == X86_INS_CMP and len(x.operands) == 2 \
                    and x.operands[1].type == X86_OP_IMM:
                o = x.operands[0]
                if (o.type == X86_OP_REG and wit in ('ebx', 'ebp', 'esi', 'edi', 'ecx', 'edx')
                        and (o.reg == getattr(cx86, 'X86_REG_' + wit.upper(), -1)
                             or o.reg == getattr(cx86, 'X86_REG_' + wit.upper(), -2))):
                    consts_here.append(hex(x.operands[1].imm & 0xFFFFFFFF))
                elif o.type == X86_OP_MEM and wit.startswith('slot_') \
                        and o.mem.base in (X86_REG_EBP, X86_REG_ESP) and o.mem.disp == [
                            q for q in (int(s['cmp_at'], 16),)][0] % 0x10:
                    pass
        try:
            c0 = next(md.disasm(D[c - VA:c - VA + 8], c))
        except StopIteration:
            c0 = None
        callee_txt = ''
        if c0 is not None and c0.operands and c0.operands[0].type == X86_OP_IMM:
            t2 = c0.operands[0].imm
            ce, cs2 = func_of(t2)
            if ce is not None:
                cc = callee_consts(ce, cs2)
                callee_txt = 'callee %08X consts=%s' % (t2, sorted(hex(x) for x in cc))
            else:
                callee_txt = 'callee %08X 不在 atlas' % t2
        else:
            callee_txt = 'callee 间接 %s' % (c0.op_str if c0 else '?')
        # 循环回边判定：jcc 目标地址 < call 地址 ⇒ 反向跳（循环）
        tgt = int(s['jcc_target'], 16) if s['jcc_target'] != 'OUT_OF_BODY' else None
        back = (tgt is not None and tgt < c)
        # 该见证寄存器在本函数内的全部立即数比较
        wname = wit if wit in ('ebx', 'ebp', 'esi', 'edi', 'ecx', 'edx', 'eax') else None
        cmpall = []
        if wname:
            reg = getattr(cx86, 'X86_REG_' + wname.upper())
            for x in ins:
                if x.id == X86_INS_CMP and len(x.operands) == 2 \
                        and x.operands[0].type == X86_OP_REG and x.operands[0].reg == reg \
                        and x.operands[1].type == X86_OP_IMM:
                    cmpall.append(hex(x.operands[1].imm & 0xFFFFFFFF))
        print('   %s call@%08X mov@%08X cmp@%08X(%s=%s) jcc@%08X->%s%s' % (
            s['form'], c, mv, cm, s['cmp_kind'], s['cmp_imm'], jc,
            s['jcc_target'], '  [回边/循环]' if back else ''))
        print('     %s' % callee_txt)
        print('     该见证值在本函数内的立即数比较集: %s' % (sorted(set(cmpall)) or '无'))
        blk = ins[idx[tgt]:idx[tgt] + 4] if tgt in idx else []
        print('     taken : ' + ' | '.join('%s %s' % (x.mnemonic, x.op_str) for x in blk))
        nx = ins[idx[jc] + 1:idx[jc] + 5] if jc in idx else []
        print('     fallth: ' + ' | '.join('%s %s' % (x.mnemonic, x.op_str) for x in nx))
