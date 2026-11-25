#!/usr/bin/env python3
"""R133 deepseek audit v2: C5, C6, C7 with CORRECT je-target parsing (parse op_str, not va+size)."""
import json
import pefile
from capstone import Cs, CS_ARCH_X86, CS_MODE_32, CS_OPT_DETAIL

BIN = '/home/t628/projects/ra2-campaign-forge/ra2bench/gamemd.exe'
A_VA, B_VA, LEN = 0x6bedb0, 0x41c250, 136

pe = pefile.PE(BIN, fast_load=True)
IB = pe.OPTIONAL_HEADER.ImageBase
IMG = pe.get_memory_mapped_image()
rd = lambda va, n: bytes(IMG[va - IB:va - IB + n])

md = Cs(CS_ARCH_X86, CS_MODE_32)
md.detail = True

CTRL = ('call', 'jmp', 'ret', 'retn', 'iretd')

out = {'note': 'v2: je target parsed from operand (v1 wrongly used va+size)'}
for name, base in (('A', A_VA), ('B', B_VA)):
    insns = [{'va': i.address, 'off': i.address - base, 'bytes': i.bytes.hex(),
              'size': i.size, 'mnem': i.mnemonic, 'op': i.op_str}
             for i in md.disasm(rd(base, LEN), base)]
    assert sum(x['size'] for x in insns) == LEN

    # ---- C5: locate test al,0x14 and the je that follows it ----
    ti = next(k for k, x in enumerate(insns) if x['mnem'] == 'test' and x['op'] == 'al, 0x14')
    t, je = insns[ti], insns[ti + 1]
    tgt = int(je['op'], 16)
    c5 = {'test_off': hex(t['off']), 'test_va': hex(t['va']), 'test_bytes': t['bytes'],
          'je_off': hex(je['off']), 'je_va': hex(je['va']), 'je_bytes': je['bytes'],
          'je_op': je['op'], 'je_target_va': hex(tgt),
          'je_target_body_off': hex(tgt - base),
          'target_is_insn_boundary': any(x['va'] == tgt for x in insns),
          'je_fallthrough_va': hex(je['va'] + je['size'])}

    # ---- C6: branches in body targeting the else entry ----
    def btarget(x):
        if x['mnem'] in CTRL or x['mnem'].startswith(('j', 'loop')):
            o = x['op'].split(',')[0].strip()
            if o.startswith('0x'):
                return int(o, 16)
        return None

    to_else = [{'off': hex(x['off']), 'va': hex(x['va']), 'mnem': x['mnem'], 'op': x['op']}
               for x in insns if btarget(x) == tgt]
    # instruction whose END == else entry
    before = [x for x in insns if x['va'] + x['size'] == tgt]
    # also: is else entry reached by fallthrough from the preceding INSN in listing order?
    prev_in_listing = insns[insns.index(next(x for x in insns if x['va'] == tgt)) - 1]
    c6 = {'else_entry_va': hex(tgt),
          'branch_count_to_else': len(to_else), 'branches_to_else': to_else,
          'insn_ending_immediately_before_else':
              {'off': hex(before[0]['off']), 'va': hex(before[0]['va']),
               'mnem': before[0]['mnem'], 'op': before[0]['op'],
               'is_unconditional_terminator': before[0]['mnem'] in ('ret', 'retn', 'jmp')}
              if before else None,
          'preceding_insn_in_listing':
              {'off': hex(prev_in_listing['off']), 'mnem': prev_in_listing['mnem'],
               'op': prev_in_listing['op'],
               'falls_through': prev_in_listing['mnem'] not in ('ret', 'retn', 'jmp') and
                                not (prev_in_listing['mnem'].startswith('j') and
                                     not prev_in_listing['mnem'].startswith('jmp'))},
          'else_entry_insn': next({'off': hex(x['off']), 'mnem': x['mnem'], 'op': x['op']}
                                  for x in insns if x['va'] == tgt)}

    # ---- C7: arms. else arm = [je target .. end); if arm = (je .. je target) ----
    ei = next(k for k, x in enumerate(insns) if x['va'] == tgt)
    if_arm = insns[ti + 2:ei]          # fallthrough block
    else_arm = insns[ei:]              # je-taken block (runs to end incl. shared epilogue)

    def summ(arm):
        return {'offsets': [hex(x['off']) for x in arm],
                'calls': [{'off': hex(x['off']), 'va': hex(x['va']), 'target': x['op'],
                           'bytes': x['bytes']} for x in arm if x['mnem'] == 'call'],
                'refs_0x7e15fc': [hex(x['off']) for x in arm if '0x7e15fc' in x['op']],
                'refs_0x7e1600': [hex(x['off']) for x in arm if '0x7e1600' in x['op']],
                'rets': [hex(x['off']) for x in arm if x['mnem'].startswith('ret')]}

    out[name] = {'base': hex(base), 'C5': c5, 'C6': c6,
                 'C7': {'if_arm_fallthrough': summ(if_arm),
                        'else_arm_jtarget': summ(else_arm)}}

print(json.dumps(out, indent=2))
json.dump(out, open('/home/t628/projects/ra2-campaign-forge/_r133/sub_deepseek/r133ds2_body2.json', 'w'), indent=2)
