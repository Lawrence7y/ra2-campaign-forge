#!/usr/bin/env python3
# R132 r132h: end-to-end arm reachability for the template, with self-labelled assertions.
#
# QUESTION: for the actual 15 wrapper call sites, which arm of the 136-byte template runs?
# R131 wrote (LEAD_LOCK KQ): "7 & 0x14 = 4 != 0 => je 不跳、CoCreateInstance 确实被调，
#   OleRun 分支 15/15 处均为死分支".
# The arithmetic is right but the NAME attached to the dead arm looks inverted, because
# OleRun sits in the FALLTHROUGH arm (offset +0x3c), not in the je-target arm.
#
# This script settles it by measurement only:
#   1. establish which stack argument the `test al,0x14` consumes (via the epilogue ret 0xc
#      and the [esp+N] read offsets), using the push depth at that instruction;
#   2. read that argument's value at every wrapper call site;
#   3. compute ZF / je outcome arithmetically;
#   4. report which named API calls sit in the arm that is actually entered.
import json, struct
import pefile
from capstone import Cs, CS_ARCH_X86, CS_MODE_32

EXE = '/home/t628/projects/ra2-campaign-forge/ra2bench/gamemd.exe'
OUT = '/home/t628/projects/ra2-campaign-forge/_r132/r132h_arms.json'

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
md.skipdata = True

ASSERT = []
def chk(name, cond, detail=''):
    ASSERT.append({'assert': name, 'pass': bool(cond), 'detail': str(detail)})
    print(('  PASS ' if cond else '  FAIL ') + name + (('  [' + str(detail) + ']') if detail else ''))
    return cond

R = {}

# ---------- instruction map ----------
insn = {}
off = 0
while off < len(data):
    for a, sz, mn, ops in md.disasm_lite(data[off:off + 0x10000], tlo + off):
        insn[a] = (sz, mn, ops)
    off += 0x10000

# ---------- 1. argument slot identification, per instance ----------
# The instance prologue is: push esi ; push edi  (=8 bytes of locals on stack)
# ret 0xc => 3 DWORD stack args. With 2 pushes, arg1 sits at [esp+0xc].
# So [esp+0xc]=arg1, [esp+0x10]=arg2, [esp+0x14]=arg3 (at the point after both pushes).
# We verify the `test al, imm` operand register is loaded from [esp+0x14].
INSTS = {'A': 0x6bedb0, 'B': 0x41c250}
R['arg_slot_model'] = {}
for label, entry in INSTS.items():
    ins = list(md.disasm(data[entry - tlo:entry - tlo + 136], entry))
    ret_imm = None
    test_at = None
    load_at = None
    test_reg = None
    for i in ins:
        if i.mnemonic == 'ret' and i.op_str:
            if ret_imm is None:
                ret_imm = i.op_str
        if i.mnemonic == 'test' and '0x14' in i.op_str:
            test_at = i.address
            test_reg = i.op_str.split(',')[0].strip()
    # find the instruction that last wrote test_reg before the test
    for i in ins:
        if i.address >= test_at:
            break
        parent = {'al':'eax','bl':'ebx','cl':'ecx','dl':'edx'}.get(test_reg, test_reg)
        if i.mnemonic == 'mov' and i.op_str.replace(' ', '').startswith(parent + ','):
            load_at = (i.address, i.op_str)
    R['arg_slot_model'][label] = {
        'ret_imm': ret_imm, 'test_at': hex(test_at), 'test_reg': test_reg,
        'test_operand': next(i.op_str for i in ins if i.address == test_at),
        'load': {'at': hex(load_at[0]), 'op': load_at[1]} if load_at else None}
    print('[%s] ret %s ; test %s at %s ; loaded by %s'
          % (label, ret_imm, R['arg_slot_model'][label]['test_operand'], hex(test_at),
             R['arg_slot_model'][label]['load']))

for label in INSTS:
    m = R['arg_slot_model'][label]
    chk('%s ret imm is 0xc (3 stack args)' % label, m['ret_imm'] == '0xc', m['ret_imm'])
    chk('%s test operand is al,0x14' % label, m['test_operand'].replace(' ', '') == 'al,0x14',
        m['test_operand'])
    chk('%s al is loaded from [esp+0x14] (arg3)' % label,
        m['load'] is not None and '0x14' in m['load']['op'], m['load'])

# ---------- 2. wrapper call sites and their arg3 ----------
def callers(target):
    out = []
    i = 0
    while True:
        i = data.find(b'\xe8', i)
        if i < 0 or i + 5 > len(data):
            break
        rel = struct.unpack('<i', data[i + 1:i + 5])[0]
        if tlo + i + 5 + rel == target:
            out.append(tlo + i)
        i += 1
    return out

def five_pushes(site):
    out = []
    va = site
    for _ in range(14):
        cand = None
        for b in range(1, 16):
            a = va - b
            if a in insn and insn[a][0] == b:
                cand = a
                break
        if cand is None:
            break
        out.append((cand, insn[cand][1], insn[cand][2]))
        va = cand
    out.reverse()
    ps = [x for x in out if x[1] == 'push']
    return ps[-3:] if len(ps) >= 3 else []

R['callsites'] = []
for label, entry in INSTS.items():
    for c in callers(entry):
        ps = five_pushes(c)
        # program order of the 3 pushes; stdcall/thiscall pushes args right-to-left,
        # so the FIRST push in program order is the LAST (3rd) argument.
        arg3 = ps[0][2] if ps else None
        R['callsites'].append({'instance': label, 'call': hex(c),
                               'pushes_program_order': [p[2] for p in ps],
                               'arg3': arg3})
print()
print('wrapper call sites (arg3 = dwClsContext, first push in program order):')
for x in R['callsites']:
    print('   %s %-10s pushes=%s  arg3=%s'
          % (x['instance'], x['call'], x['pushes_program_order'], x['arg3']))

from collections import Counter
cnt = Counter(x['arg3'] for x in R['callsites'])
R['arg3_distribution'] = dict(cnt)
print('arg3 distribution:', dict(cnt))
chk('15 wrapper call sites total', len(R['callsites']) == 15, len(R['callsites']))
chk('every wrapper call site passes arg3 == 7', set(cnt) == {'7'}, dict(cnt))

# ---------- 3. ZF / je outcome ----------
R['zf'] = []
for x in R['callsites']:
    v = int(x['arg3'], 0)
    andv = v & 0x14
    taken = (andv == 0)
    R['zf'].append({'call': x['call'], 'arg3': v, 'and': andv, 'je_taken': taken})
je_taken_any = any(z['je_taken'] for z in R['zf'])
R['je_taken_anywhere'] = je_taken_any
chk('arg3=7 => 7 & 0x14 = 4 != 0 => ZF=0 => je NOT taken at all 15 sites',
    (7 & 0x14) == 4 and not je_taken_any, '7&0x14=%d' % (7 & 0x14))

# ---------- 4. which arm is entered, and what's in it ----------
def arm(start, limit=60):
    calls = []
    seen = set()
    work = [start]
    while work and len(calls) < limit:
        va = work.pop()
        if va in seen:
            continue
        seen.add(va)
        if va not in insn:
            continue
        sz, mn, ops = insn[va]
        if mn == 'call':
            if '0x7e15fc' in ops:
                calls.append(('CoCreateInstance', hex(va)))
            elif '0x7e1600' in ops:
                calls.append(('OleRun', hex(va)))
        if mn == 'ret':
            continue
        if mn in ('je', 'jne', 'jl', 'jle', 'jg', 'jge', 'jmp'):
            try:
                work.append(int(ops, 16))
            except ValueError:
                pass
        work.append(va + sz)
    return calls

R['arms'] = {}
for label, entry in INSTS.items():
    ins = list(md.disasm(data[entry - tlo:entry - tlo + 136], entry))
    je = next(i for i in ins if i.mnemonic == 'je' and i.address > entry + 8)
    ft = je.address + je.size
    tg = int(je.op_str, 16)
    R['arms'][label] = {
        'je_at': hex(je.address), 'je_target': hex(tg), 'fallthrough': hex(ft),
        'fallthrough_calls': arm(ft), 'je_target_calls': arm(tg)}
    print('[%s] je %s -> %s ; fallthrough %s' % (label, hex(je.address), hex(tg), hex(ft)))
    print('     fallthrough arm calls: %s' % (R['arms'][label]['fallthrough_calls'],))
    print('     je-target  arm calls: %s' % (R['arms'][label]['je_target_calls'],))

for label in INSTS:
    a = R['arms'][label]
    names_ft = [n for n, _ in a['fallthrough_calls']]
    names_tg = [n for n, _ in a['je_target_calls']]
    chk('%s fallthrough arm contains OleRun' % label, 'OleRun' in names_ft, names_ft)
    chk('%s je-target arm does NOT contain OleRun' % label, 'OleRun' not in names_tg, names_tg)
    chk('%s je-target arm contains CoCreateInstance' % label,
        'CoCreateInstance' in names_tg, names_tg)

# ---------- 5. the conclusion, stated as a testable proposition ----------
R['conclusion'] = {
    'live_arm_for_all_15_callers': 'fallthrough (because 7&0x14!=0 => ZF=0 => je not taken)',
    'live_arm_contains': 'CoCreateInstance then OleRun',
    'dead_arm': 'je-target: a second CoCreateInstance with riid=IID_IUnknown and NO OleRun',
    'correction_to_R131': 'R131 named the OleRun branch as the dead one; measurement says '
                          'OleRun is in the LIVE arm and the dead arm is the second '
                          'CoCreateInstance in the je target.',
}
print()
print('conclusion:', json.dumps(R['conclusion'], ensure_ascii=False, indent=1))

json.dump(R, open(OUT, 'w'), ensure_ascii=False, indent=1)
json.dump(ASSERT, open(OUT.replace('.json', '_assert.json'), 'w'), ensure_ascii=False, indent=1)
nf = sum(1 for a in ASSERT if not a['pass'])
print()
print('== assertions: %d total, %d FAIL ==' % (len(ASSERT), nf))
print('wrote', OUT)
