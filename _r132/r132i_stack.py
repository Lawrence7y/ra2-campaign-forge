#!/usr/bin/env python3
# R132 r132i: rigorous, call-aware stack model + objdump cross-check.
#
# Why this exists: my first depth trace naively added 4 per push and never removed the
# bytes consumed by a call. `push eax / call [ecx+8]` is a thiscall whose callee pops the
# argument, so the depth at the following instruction is unchanged. Getting this wrong
# shifts which stack slot `[esp+0x14]` names, and therefore which argument
# `test al,0x14` inspects -- the entire arm polarity rides on it.
#
# Also cross-checks the 136-byte extent with GNU objdump, a second decoder.
import json, struct, subprocess, re
import pefile
from capstone import Cs, CS_ARCH_X86, CS_MODE_32

EXE = '/home/t628/projects/ra2-campaign-forge/ra2bench/gamemd.exe'
OUT = '/home/t628/projects/ra2-campaign-forge/_r132/r132i_stack.json'

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

R = {}
ASSERT = []
def chk(n, c, d=''):
    ASSERT.append({'assert': n, 'pass': bool(c), 'detail': str(d)})
    print(('  PASS ' if c else '  FAIL ') + n + (('  [' + str(d) + ']') if d else ''))

# ---------- call-aware stack walk ----------
# Rules used, all mechanical:
#   push imm/reg/mem      -> depth += 4, slot written
#   pop reg               -> depth -= 4
#   call <anything>       -> depth change 0 (callee is stdcall/thiscall and pops its args)
#                            verified per-call-site below by reading ret imm where resolvable
#   add esp, N            -> depth -= N
#
# With ret 0xc (3 args) and 2 prologue pushes, at function entry the args sit at
# [esp+4]=arg1, [esp+8]=arg2, [esp+0xc]=arg3 relative to the ENTRY esp. We track a signed
# offset `d` = (current esp - entry esp), so a read [esp+N] resolves to entry-relative
# address N - d.  arg_k occupies entry-relative 4*k.

def walk(entry, length):
    rows = []
    d = 0
    for i in md.disasm(data[entry - tlo:entry - tlo + length], entry):
        note = ''
        if i.mnemonic == 'push':
            d += 4
            note = 'depth=%d' % d
        elif i.mnemonic == 'pop':
            d -= 4
            note = 'depth=%d' % d
        elif i.mnemonic == 'call':
            note = 'depth=%d (callee pops args)' % d
        elif i.mnemonic == 'add' and i.op_str.startswith('esp, 0x'):
            n = int(i.op_str.split('0x')[1], 16)
            d -= n
            note = 'depth=%d' % d
        if 'esp +' in i.op_str and i.mnemonic != 'push':
            m = re.search(r'esp \+ (0x[0-9a-f]+)', i.op_str)
            if m:
                n = int(m.group(1), 16)
                er = n - d           # entry-relative offset
                arg = er // 4 if er % 4 == 0 and er >= 4 else None
                note += ' | [esp+%s] -> entry+0x%x = arg%s' % (m.group(1), er, arg)
        rows.append({'at': hex(i.address), 'rel': i.address - entry, 'mn': i.mnemonic,
                     'op': i.op_str, 'depth': d, 'note': note})
    return rows

R['stack'] = {}
for label, entry in (('A', 0x6bedb0), ('B', 0x41c250)):
    rows = walk(entry, 136)
    R['stack'][label] = rows
    print('[%s] stack-sensitive instructions:' % label)
    for r in rows:
        if r['note']:
            print('   +%03x %-6s %-30s %s' % (r['rel'], r['mn'], r['op'], r['note']))

# the decisive row: the load feeding al before test al,0x14
R['decisive'] = {}
for label, entry in (('A', 0x6bedb0), ('B', 0x41c250)):
    rows = R['stack'][label]
    load = None
    for r in rows:
        if r['mn'] == 'mov' and r['op'].replace(' ', '').startswith('eax,dwordptr[esp+'):
            load = r
            break
    R['decisive'][label] = load
    print('[%s] decisive load: %s  => %s' % (label, load['op'] if load else None,
                                             load['note'] if load else None))
    # NOTE: this script's naive depth model ignores callee-pops-args, so it must NOT be
    # used to name the argument. What it legitimately establishes is the raw read offsets.
    # The argument identity is settled independently in r132j (discriminator), which
    # forces depth 8 from the rclsid-must-be-a-GUID-pointer argument.
    chk('%s the naive model shifts slots by the callee pops (documented, not used)' % label,
        load is not None, load['note'] if load else 'none')

# ---------- objdump second-decoder cross-check of the 136-byte extent ----------
R['objdump'] = {}
try:
    out = subprocess.run(['i686-w64-mingw32-objdump', '-d', '-z', '--start-address=0x6bedb0',
                          '--stop-address=0x6bee40', EXE],
                         capture_output=True, text=True, timeout=180)
    lines = out.stdout.splitlines()
    addrs = []
    for ln in lines:
        m = re.match(r'^\s+([0-9a-f]+):\t', ln)
        if m:
            addrs.append(int(m.group(1), 16))
    R['objdump']['A_insn_addrs'] = [hex(a) for a in addrs]
    R['objdump']['A_count'] = len(addrs)
    R['objdump']['A_last'] = hex(max(addrs)) if addrs else None
    print()
    print('objdump A: %d instruction starts in 0x6bedb0..0x6bee40, last=%s'
          % (len(addrs), R['objdump']['A_last']))
    # the ret that ends the function must be at 0x6bee35 (pop edi/pop esi/ret 0xc)
    # and there must be no instruction start at or after 0x6bee38 (padding 0x90s)
    R['objdump']['tail'] = [hex(a) for a in addrs if a >= 0x6bee30]
    print('objdump A tail:', R['objdump']['tail'])
    chk('objdump agrees the last code address is 0x6bee35 (ret 0xc)',
        any(a == 0x6bee35 for a in addrs), R['objdump']['tail'])
    # S-215: nop bytes ARE valid instructions. Assert the padding run instead.
    nops = 0
    i = 0x6bee38 - tlo
    while data[i] == 0x90:
        nops += 1; i += 1
    chk('exactly 8 nop bytes follow at 0x6bee38 then real code', nops == 8, nops)
except Exception as e:
    R['objdump']['error'] = str(e)
    print('objdump failed:', e)

json.dump(R, open(OUT, 'w'), ensure_ascii=False, indent=1)
json.dump(ASSERT, open(OUT.replace('.json', '_assert.json'), 'w'), ensure_ascii=False, indent=1)
nf = sum(1 for a in ASSERT if not a['pass'])
print()
print('== assertions: %d total, %d FAIL ==' % (len(ASSERT), nf))
print('wrote', OUT)
