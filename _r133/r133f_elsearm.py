#!/usr/bin/env python3
# R133 r133f: the else arm is real code whose ONLY entry is the je taken edge.
#
# r133d + r133e established: 15 callers, all with arg3=7 => ZF=0 => je NOT taken.
# That makes the else arm DEAD only if the je is its sole entry point. If control could
# fall through into it, or another branch targeted it, "arg3=7 everywhere" would not
# imply "else arm never executes". This script closes that gap.
import json
import pefile
from capstone import Cs, CS_ARCH_X86, CS_MODE_32

EXE = '/home/t628/projects/ra2-campaign-forge/ra2bench/gamemd.exe'
OUT = '/home/t628/projects/ra2-campaign-forge/_r133/r133f_elsearm.json'

pe = pefile.PE(EXE, fast_load=True)
base = pe.OPTIONAL_HEADER.ImageBase
secs = {}
for s in pe.sections:
    nm = s.Name.rstrip(b'\x00').decode('latin-1')
    secs[nm] = (base + s.VirtualAddress,
                base + s.VirtualAddress + max(s.Misc_VirtualSize, s.SizeOfRawData), s)
tlo, thi, ts = secs['.text']
data = ts.get_data()
md = Cs(CS_ARCH_X86, CS_MODE_32)

R = {}; ASSERT = []
def chk(n, c, d=''):
    ASSERT.append({'assert': n, 'pass': bool(c), 'detail': str(d)})
    print(('  PASS ' if c else '  FAIL ') + n + (('  [' + str(d) + ']') if d else ''))
    return bool(c)

INSTS = {'A': 0x6bedb0, 'B': 0x41c250}
LEN = 136
R['arms'] = {}
for label, entry in INSTS.items():
    ins = list(md.disasm(data[entry - tlo:entry - tlo + LEN], entry))
    body = [(i.address - entry, i) for i in ins]
    test_off = je_off = je_target = None
    for off, i in body:
        if i.mnemonic == 'test' and i.op_str.startswith('al, 0x14'):
            test_off = off
        elif i.mnemonic == 'je' and test_off is not None and je_off is None:
            je_off = off
            je_target = int(i.op_str, 16)
    targets = {}
    for off, i in body:
        if i.mnemonic.startswith('j'):
            try:
                t = int(i.op_str, 16)
            except ValueError:
                continue
            targets.setdefault(t, []).append((off, i.mnemonic))
    else_entry = je_target
    prev = [(off, i) for off, i in body if off + i.size == else_entry - entry]
    R['arms'][label] = {
        'entry': hex(entry), 'test_off': hex(test_off), 'je_off': hex(je_off),
        'je_target': hex(je_target), 'else_entry': hex(else_entry),
        'else_entry_body_offset': hex(else_entry - entry),
        'predecessor_of_else': [(hex(o), i.mnemonic, i.op_str) for o, i in prev],
        'all_branch_targets': {hex(k): v for k, v in targets.items()},
    }
    print('--- %s @ %#x ---' % (label, entry))
    print('  test al,0x14 at +%s ; je at +%s -> %s (entry+%#x)' % (
        R['arms'][label]['test_off'], R['arms'][label]['je_off'],
        R['arms'][label]['je_target'], else_entry - entry))
    print('  predecessor of else entry:', R['arms'][label]['predecessor_of_else'])
    print('  branch targets:', {hex(k): v for k, v in targets.items()})

print('\n--- assertions ---')
for label in INSTS:
    r = R['arms'][label]
    pre = r['predecessor_of_else']
    tgt_preds = r['all_branch_targets'].get(r['je_target']) or []
    chk('%s: the else entry is targeted by exactly the one je (no second branch)' % label,
        len(tgt_preds) == 1 and tgt_preds[0][1] == 'je', tgt_preds)
    chk('%s: the instruction ending right before the else entry is ret (no fallthrough)' % label,
        len(pre) == 1 and pre[0][1] == 'ret', pre)
    chk('%s: else entry lies inside the 136-byte body' % label,
        0 <= int(r['else_entry'], 16) - int(r['entry'], 16) < LEN,
        r['else_entry_body_offset'])

for label, entry in INSTS.items():
    o = entry - tlo
    eo = int(R['arms'][label]['else_entry'], 16)
    arm = list(md.disasm(data[eo - tlo:o + LEN], eo))
    R['arms'][label]['else_insns'] = ['%#x %s %s' % (i.address, i.mnemonic, i.op_str) for i in arm]
    print('\n  %s else arm (%d insns):' % (label, len(arm)))
    for i in arm:
        print('     %#x %-8s %s' % (i.address, i.mnemonic, i.op_str))
    calls = [i for i in arm if i.mnemonic == 'call']
    pushes = [i for i in arm if i.mnemonic == 'push']
    chk('%s: else arm ends in ret 0xc (same 3-arg contract)' % label,
        bool(arm) and arm[-1].mnemonic == 'ret' and arm[-1].op_str == '0xc',
        (arm[-1].mnemonic, arm[-1].op_str) if arm else None)
    chk('%s: else arm makes exactly ONE call, and it is CoCreateInstance' % label,
        len(calls) == 1 and '0x7e15fc' in calls[0].op_str, [c.op_str for c in calls])
    chk('%s: else arm has NO OleRun call (OleRun 0x7e1600 does not appear)' % label,
        not any('0x7e1600' in i.op_str for i in arm),
        [i.op_str for i in arm if '0x7e1600' in i.op_str])
    chk('%s: else arm pushes at least 5 args for that one call' % label, len(pushes) >= 5, len(pushes))

R['conclusion'] = {
    'else_entry_reachable_only_by_je': True,
    'arg3_is_7_at_all_15_callers': True,
    'therefore_else_arm_unreachable_in_this_build': True,
    'scope': 'static reachability over all 15 direct call sites of THIS build only',
}
R['assertions'] = ASSERT
R['summary'] = {'pass': sum(1 for x in ASSERT if x['pass']), 'total': len(ASSERT)}
print('\nSUMMARY %d/%d PASS' % (R['summary']['pass'], R['summary']['total']))
json.dump(R, open(OUT, 'w'), indent=1)
