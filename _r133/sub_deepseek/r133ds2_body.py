#!/usr/bin/env python3
"""R133 deepseek audit: C5 (test al,0x14 + je), C6 (single branch to else), C7 (call lists per arm).
Disassembles ONLY the 136-byte bodies (capstone detail=True on a 0x88 window, allowed)."""
import json
import pefile
from capstone import Cs, CS_ARCH_X86, CS_MODE_32, CS_OPT_DETAIL

BIN = '/home/t628/projects/ra2-campaign-forge/ra2bench/gamemd.exe'
A_VA = 0x6bedb0
B_VA = 0x41c250
LEN = 136

pe = pefile.PE(BIN, fast_load=True)
IB = pe.OPTIONAL_HEADER.ImageBase
IMG = pe.get_memory_mapped_image()


def rd(va, n):
    return bytes(IMG[va - IB:va - IB + n])


md = Cs(CS_ARCH_X86, CS_MODE_32)
md.detail = True

out = {}
for name, base in (('A', A_VA), ('B', B_VA)):
    code = rd(base, LEN)
    insns = []
    for i in md.disasm(code, base):
        insns.append({
            'va': i.address, 'off': i.address - base,
            'bytes': i.bytes.hex(), 'size': i.size,
            'mnem': i.mnemonic, 'op': i.op_str,
        })
    covered = sum(x['size'] for x in insns)
    out[name] = {'base': hex(base), 'insn_count': len(insns), 'coverage': covered,
                 'covers_exactly_136': covered == LEN, 'insns': insns}

    # ---------- C5 ----------
    tests = [x for x in insns if x['mnem'] == 'test' and x['op'] == 'al, 0x14']
    c5 = {'all_tests': [(x['mnem'], x['op'], hex(x['off'])) for x in insns if x['mnem'] == 'test']}
    if tests:
        t = tests[0]
        idx = insns.index(t)
        nxt = insns[idx + 1] if idx + 1 < len(insns) else None
        c5.update({
            'test_off': hex(t['off']), 'test_bytes': t['bytes'],
            'next_mnem': nxt['mnem'] if nxt else None,
            'next_off': hex(nxt['off']) if nxt else None,
            'next_op': nxt['op'] if nxt else None,
        })
        if nxt and nxt['mnem'].startswith('j'):
            c5['je_target_va'] = hex(nxt['va'] + nxt['size'])
            c5['je_target_off'] = hex(nxt['va'] + nxt['size'] - base)
            # confirm target lands on an instruction boundary
            c5['target_is_boundary'] = any(x['va'] == nxt['va'] + nxt['size'] for x in insns)
    out[name]['C5'] = c5

    # ---------- C6 ----------
    if 'je_target_va' in out[name]['C5']:
        tgt = int(out[name]['C5']['je_target_va'], 16)
        branches = []
        for x in insns:
            if x['mnem'] in ('call', 'ret', 'retn', 'jmp') or x['mnem'].startswith('j') or \
               x['mnem'].startswith('loop'):
                # compute branch target if it has an imm operand that resolved to a VA
                bv = x['op'].split(',')[0].strip()
                if bv.startswith('0x'):
                    bt = int(bv, 16)
                    branches.append({'off': hex(x['off']), 'mnem': x['mnem'],
                                     'target': hex(bt), 'targets_else': bt == tgt})
        to_else = [b for b in branches if b['targets_else']]
        # instruction ending immediately before else entry
        before = [x for x in insns if x['va'] + x['size'] == tgt]
        out[name]['C6'] = {
            'else_entry_va': hex(tgt),
            'branch_count_to_else': len(to_else),
            'branches_to_else': to_else,
            'all_branch_insns': branches,
            'insn_immediately_before_else': (
                {'mnem': before[0]['mnem'], 'op': before[0]['op'],
                 'off': hex(before[0]['off']), 'bytes': before[0]['bytes']}
                if before else None),
            'fallthrough_source': hex(tgt) if not before else None,
        }

        # ---------- C7 ----------
        def arms():
            # if arm = insns after the je up to (excluding) else entry; else arm = from else entry to ret
            je_i = next(k for k, x in enumerate(insns) if x['va'] + x['size'] == tgt and
                        x['mnem'].startswith('j'))
            ret_i = next((k for k, x in enumerate(insns) if x['mnem'].startswith('ret')), None)
            el_i = next(k for k, x in enumerate(insns) if x['va'] == tgt)
            if_arm = insns[je_i + 1:el_i]
            else_arm = insns[el_i:ret_i + 1] if ret_i else insns[el_i:]
            return if_arm, else_arm, ret_i

        if_arm, else_arm, ret_i = arms()

        def calls(arm):
            return [{'off': hex(x['off']), 'target': x['op'], 'bytes': x['bytes']}
                    for x in arm if x['mnem'] == 'call']

        def ole(arg):
            arm = if_arm if arg == 'if' else else_arm
            return {
                'arm_offsets': [hex(x['off']) for x in arm],
                'calls': calls(arm),
                'mentions_7e1600': [{'off': hex(x['off']), 'mnem': x['mnem'], 'op': x['op']}
                                    for x in arm if '0x7e1600' in x['op']],
                'mentions_7e15fc': [{'off': hex(x['off']), 'mnem': x['mnem'], 'op': x['op']}
                                    for x in arm if '0x7e15fc' in x['op']],
            }

        out[name]['C7'] = {'if': ole('if'), 'else': ole('else')}

print(json.dumps(out, indent=2))
with open('/home/t628/projects/ra2-campaign-forge/_r133/sub_deepseek/r133ds2_body.json', 'w') as f:
    json.dump(out, f, indent=2)
