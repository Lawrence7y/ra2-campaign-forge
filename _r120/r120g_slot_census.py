#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""r120g_slot_census.py —— 站后虚调用落在**哪个 vtable 槽**：一个不依赖函数边界的量。

审计 B3 给了「站后 10 字节全是 COM 虚调用模板」这个量。本脚本把它再推一格：
模板里的 call 到底是 call dword ptr [ecx]（槽 0 = QueryInterface）还是 [ecx+0xc]（槽 3）等。
若 60 个站点**全部**落同一槽，则「这 60 处是同一类调用」这件事有第二个独立支撑；
若散在多个槽，则「专门用某接口」的说法就要打折。

判据（只看站点起 16 字节，不查函数边界、不算 IID-per-function）：
  - 读 opcode 68 imm32（push imm32）后逐字节判模板；
  - 取模板里 call 的 ModRM/SIB/disp，解出「[reg] / [reg+disp]」的 disp 值。
反控：
  N1 把 0x7f7c80 的站点逐个验一遍：imm32 必须真的等于 0x7f7c80（不是巧合字节）
  N2 对 0x7f7c90 的 56 个站点跑同一解析，必须**不**得出「全部槽 0」的结论
  N3 偏移量反控：站点 +1 处起算必须解不出合法模板（证明解析不是恒真）
"""
import array
import io
import json
import os
import struct
import sys

ROOT = '/home/t628/projects/ra2-campaign-forge'
sys.path.insert(0, os.path.join(ROOT, '_r119'))
from _pe119 import PE_, BUF                      # noqa: E402
import capstone                                  # noqa: E402

OUT = os.path.join(ROOT, '_r120', 'r120g_slot_census.json')
checks = []


def ck(name, cond, detail=''):
    checks.append({'name': name, 'ok': bool(cond), 'detail': detail})
    print(('PASS ' if cond else 'FAIL ') + name + ((' | ' + str(detail)) if detail != '' else ''), flush=True)
    return bool(cond)


TEXT = PE_.sec_by_name('.text')
MD = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
MD.detail = False
MD.skipdata = True


def push_sites(target):
    out = []
    for off in range(0, TEXT['vsize'], 65536):
        blob = BUF[TEXT['raw'] + off: TEXT['raw'] + min(off + 65536, TEXT['vsize'])]
        for (a, sz, mn, ops) in MD.disasm_lite(blob, TEXT['va'] + off):
            if mn == 'push' and ops.startswith('0x'):
                try:
                    if int(ops, 16) == target:
                        out.append(a)
                except ValueError:
                    pass
    return out


def decode_tail(va, shift=0):
    """从 va+shift 起逐条反汇编 3 条，返回 (mnemonic, ops) 列表。"""
    o = PE_.va2off(va + shift)
    if o is None:
        return []
    blob = BUF[o:o + 32]
    # 🐞 自错 S-82：初版只取前 3 条指令，而模板是 4 条（push imm32 / push eax /
    # mov ecx,[eax] / call [ecx]）⇒ 60/60 全部「解不出」，G1 假 FAIL。改为取前 6 条。
    return [(mn, ops) for (a, sz, mn, ops) in MD.disasm_lite(blob, va + shift)][:6]


def slot_of(insns, target):
    """从 3 条指令里找 call dword ptr [reg] 或 [reg+disp]，并核对 imm32 == target。"""
    if not insns:
        return None
    mn0, op0 = insns[0]
    if mn0 != 'push':
        return None
    try:
        imm = int(op0, 16)
    except ValueError:
        return None
    if imm != target:
        return None
    for mn, ops in insns[1:]:
        if mn == 'call' and ops.startswith('dword ptr ['):
            inner = ops[len('dword ptr ['):-1]
            if '+' in inner:
                base, disp = inner.split('+', 1)
                return {'base': base.strip(), 'disp': disp.strip()}
            return {'base': inner.strip(), 'disp': '0x0'}
    return None


res = {}
for target in (0x7f7c80, 0x7f7c90, 0x7f7d00, 0x817bc0):
    ss = push_sites(target)
    slots = {}
    fails = 0
    for s in ss:
        d = slot_of(decode_tail(s), target)
        if d is None:
            fails += 1
            continue
        k = '%s+%s' % (d['base'], d['disp'])
        slots[k] = slots.get(k, 0) + 1
    res[hex(target)] = {'sites': len(ss), 'slots': slots, 'unparsed': fails}

r80 = res['0x7f7c80']
ck('G1 0x7f7c80 的 %d 个站点里，解析出「call dword ptr [槽]」的 = %d，解不出 = %d；槽分布 = %s'
   % (r80['sites'], sum(r80['slots'].values()), r80['unparsed'],
      json.dumps(r80['slots'], ensure_ascii=False)),
   r80['sites'] == 60 and r80['unparsed'] == 0 and list(r80['slots']) == ['ecx+0x0'],
   r80)

r90 = res['0x7f7c90']
ck('G2 反控（不是一律给槽 0）：0x7f7c90 的 %d 个站点里解出槽的 = %d、解不出 = %d，槽分布 = %s'
   ' ⇒ 该解析器对另一批站点给出的是「解不出」而不是硬编槽 0'
   % (r90['sites'], sum(r90['slots'].values()), r90['unparsed'],
      json.dumps(r90['slots'], ensure_ascii=False)),
   r90['unparsed'] > 0 or len(r90['slots']) != 1, r90)

# N1：imm32 真的等于目标（逐个核对）
n1_bad = 0
for s in push_sites(0x7f7c80):
    o = PE_.va2off(s)
    if BUF[o] != 0x68 or struct.unpack_from('<I', BUF, o + 1)[0] != 0x7f7c80:
        n1_bad += 1
ck('N1 反控（imm32 精确）：0x7f7c80 的 60 个站点逐个核对「首字节 0x68 且 imm32 == 0x7f7c80」，'
   '不符的 = %d' % n1_bad, n1_bad == 0, {'n_bad': n1_bad})

# N3：站点 +1 处起算必须解不出模板
n3_ok = 0
for s in push_sites(0x7f7c80):
    if slot_of(decode_tail(s, 1), 0x7f7c80) is None:
        n3_ok += 1
ck('N3 反控（偏移敏感）：从站点 +1 处起算解模板，解出的 = %d / 60（必须 0，否则解析是恒真的）'
   % (60 - n3_ok), n3_ok == 60, {'n_ok': n3_ok})

json.dump(res, open(OUT, 'w'), ensure_ascii=False, indent=1)
print('\n%d/%d PASS -> %s' % (sum(1 for c in checks if c['ok']), len(checks), OUT))
sys.exit(0 if all(c['ok'] for c in checks) else 1)
