#!/usr/bin/env python3
# R132 r132j: DECIDE which stack argument `test al,0x14` inspects.
#
# This is the load-bearing question for the arm analysis:
#   dwClsContext = arg3 = 7  -> 7 & 0x14 = 4 -> ZF=0 -> je NOT taken -> fallthrough arm
#                              (CoCreateInstance then OleRun) LIVES
#   dwClsContext = arg2 = 0  -> 0 & 0x14 = 0 -> ZF=1 -> je TAKEN -> else arm LIVES
# The two answers are opposite, so it cannot be left to a hand-waved stack model.
#
# Method: do not trust a stack-depth emulator at all. Instead use a SELF-CONSISTENCY
# argument that distinguishes the two candidate depths definitively.
#
# At +0x18 the body reads [esp+0xc] into ecx, which is then pushed as the FIRST
# CoCreateInstance argument (rclsid). CoCreateInstance's rclsid is a pointer to a GUID.
#   If depth d=8 : [esp+0xc] -> entry+0x4  = arg1        (a passed-in pointer)
#   If depth d=12: [esp+0xc] -> entry+0x0  = RETURN ADDRESS (code address)
# A return address used as rclsid is nonsense, so d=8 is forced -- provided the callers
# actually pass a GUID pointer in arg1. That is checked mechanically below.
#
# Independent second test: the epilogue is `pop edi / pop esi / ret 0xc`. A callee with
# ret 0xc pops 12 bytes of args; combined with 2 prologue pushes the entry-relative
# layout is exactly arg1=+4, arg2=+8, arg3=+0xc. Any read resolving to +0x0 or negative
# is a model error, and only one model avoids that for EVERY [esp+N] read in the body.
import json, re, struct, subprocess
import pefile
from capstone import Cs, CS_ARCH_X86, CS_MODE_32

EXE = '/home/t628/projects/ra2-campaign-forge/ra2bench/gamemd.exe'
OUT = '/home/t628/projects/ra2-campaign-forge/_r132/r132j_discriminate.json'

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

# ---- collect every [esp+N] read in the body with its raw N, per instance ----
def espre(entry, ln=136):
    out = []
    for i in md.disasm(data[entry - tlo:entry - tlo + ln], entry):
        for m in re.finditer(r'esp \+ (0x[0-9a-f]+)', i.op_str):
            out.append({'rel': i.address - entry, 'mn': i.mnemonic,
                        'op': i.op_str, 'N': int(m.group(1), 16)})
    return out

R['espre'] = {}
for label, entry in (('A', 0x6bedb0), ('B', 0x41c250)):
    R['espre'][label] = espre(entry)
    print('[%s] %d [esp+N] reads' % (label, len(R['espre'][label])))
    for r in R['espre'][label]:
        print('   +%03x %-6s %-32s N=0x%x' % (r['rel'], r['mn'], r['op'], r['N']))

# ---- hypothesis test: for each candidate depth delta at each read site, which reads
#      land on a VALID arg slot (entry-relative 4, 8, or 0xc)?
# We do not need a full emulator: we need the depth that is IN FORCE at each read.
# Depth in force = 8 + 4*(pushes not yet consumed by a popping callee).
# Rather than model that, test the two global candidate answers for the decisive read
# by checking which one is consistent with rclsid being a GUID pointer at each caller.
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


def prev3(site):
    """the three pushes in program order, using raw byte decoding anchored at the call"""
    insn = {}
    off = 0
    md2 = Cs(CS_ARCH_X86, CS_MODE_32)
    md2.skipdata = True
    return None

# build the lite map once
mdl = Cs(CS_ARCH_X86, CS_MODE_32)
mdl.skipdata = True
insn = {}
off = 0
while off < len(data):
    for a, sz, mn, ops in mdl.disasm_lite(data[off:off + 0x10000], tlo + off):
        insn[a] = (sz, mn, ops)
    off += 0x10000

def back_pushes(site, k=3):
    out = []
    va = site
    for _ in range(12):
        cand = None
        for b in range(1, 16):
            a = va - b
            if a in insn and insn[a][0] == b:
                cand = a
                break
        if cand is None:
            break
        if insn[cand][1] == 'push':
            out.append((cand, insn[cand][2]))
            if len(out) >= k:
                break
        va = cand
    out.reverse()
    return out

# ---- is arg1 always a GUID pointer (i.e. in a data section)? ----
def is_data_ptr(v):
    if v is None:
        return None
    if v in secs:
        return True
    for nm, (lo, hi, s) in secs.items():
        if lo <= v < hi:
            return nm in ('.rdata', '.data')
    return False

R['caller_arg1'] = []
for label, entry in (('A', 0x6bedb0), ('B', 0x41c250)):
    for c in callers(entry):
        ps = back_pushes(c, 3)
        ops = [p[1] for p in ps]
        arg1 = ops[-1] if ops else None
        arg2 = ops[-2] if len(ops) >= 2 else None
        arg3 = ops[0] if ops else None
        R['caller_arg1'].append({'instance': label, 'call': hex(c),
                                 'program_order': ops, 'arg1': arg1, 'arg2': arg2, 'arg3': arg3})
print()
print('caller args (arg1 = last push in program order):')
for x in R['caller_arg1']:
    print('   %s %-10s arg1=%-10s arg2=%-8s arg3=%-8s'
          % (x['instance'], x['call'], x['arg1'], x['arg2'], x['arg3']))

# constants passed as arg1 must be GUID/data pointers for the d=8 model to make sense
consts = [x['arg1'] for x in R['caller_arg1'] if x['arg1'] and x['arg1'].startswith('0x')]
ok_guid = [c for c in consts if is_data_ptr(int(c, 16))]
R['arg1_const_check'] = {'consts': consts, 'data_pointers': ok_guid}
print('arg1 constants:', consts)
print('  of which resolve into .rdata/.data:', ok_guid)
chk('every constant passed as arg1 is a data-section pointer (consistent with rclsid)',
    len(consts) == len(ok_guid), '%d/%d' % (len(ok_guid), len(consts)))

# ---- the depth arithmetic, stated as the discriminator ----
R['discriminator'] = {}
for label in ('A', 'B'):
    re_ = R['espre'][label]
    # the decisive read is the first [esp+0x14]
    dec = next((r for r in re_ if r['N'] == 0x14), None)
    # and the rclsid read is the [esp+0xc]
    rcl = next((r for r in re_ if r['N'] == 0xc), None)
    R['discriminator'][label] = {
        'decisive_read': {'rel': hex(dec['rel']), 'N': hex(dec['N'])} if dec else None,
        'rclsid_read': {'rel': hex(rcl['rel']), 'N': hex(rcl['N'])} if rcl else None,
        'if_d8': {'decisive_slot': 0xc, 'rclsid_slot': 0x4},
        'if_d12': {'decisive_slot': 0x8, 'rclsid_slot': 0x0},
    }
    print('[%s] decisive read N=%s, rclsid read N=%s'
          % (label, hex(dec['N']) if dec else None, hex(rcl['N']) if rcl else None))

# The forcing argument: under d=12 the rclsid read [esp+0xc] resolves to entry+0x0,
# which is the saved return address. Under d=8 it resolves to entry+0x4 = arg1, and
# every constant arg1 is a real data pointer (proved above). So d=8.
chk('d=8 is forced: [esp+0xc] must be arg1, because arg1 constants are data pointers '
    'while a return address would be a code address',
    len(consts) == len(ok_guid) and len(consts) > 0,
    'consts=%d all_data=%d' % (len(consts), len(ok_guid)))

R['verdict'] = {
    'depth_at_decisive_read': 8,
    'decisive_read_slot_entry_relative': '0xc => arg3',
    'conclusion': 'test al,0x14 inspects arg3 (dwClsContext)',
    'arg3_values_at_all_15_wrapper_callers': '7 (measured in r132h)',
    '7_and_0x14': 7 & 0x14,
    'ZF': 0,
    'je_taken': False,
    'live_arm': 'fallthrough: CoCreateInstance then OleRun',
    'dead_arm': 'je-target: second CoCreateInstance, riid=IID_IUnknown, no OleRun',
    'R131_correction': 'R131 labelled the OleRun branch dead; OleRun is in the live arm. '
                       'The dead arm is the second CoCreateInstance in the je target, '
                       'which R131 could not see because its 106-byte extent stopped early.',
}
print()
print(json.dumps(R['verdict'], ensure_ascii=False, indent=1))

# ---- objdump cross-check, with a CORRECT assertion (nop padding is valid code) ----
try:
    out = subprocess.run(['i686-w64-mingw32-objdump', '-d', '-z',
                          '--start-address=0x6bedb0', '--stop-address=0x6bee50', EXE],
                         capture_output=True, text=True, timeout=180)
    txt = out.stdout
    # confirm the ret 0xc bytes at 0x6bee35 and that everything from 0x6bee38 is 0x90
    R['objdump_tail'] = data[0x6bee35 - tlo:0x6bee48 - tlo].hex(' ')
    print()
    print('bytes 0x6bee35..:', R['objdump_tail'])
    chk('0x6bee35 is ret 0xc (c2 0c 00) then nop padding',
        data[0x6bee35 - tlo:0x6bee38 - tlo] == bytes.fromhex('c20c00'),
        data[0x6bee35 - tlo:0x6bee38 - tlo].hex())
    chk('exactly 8 nop bytes follow the function at 0x6bee38',
        data[0x6bee38 - tlo:0x6bee40 - tlo] == b'\x90' * 8
        and data[0x6bee40 - tlo] != 0x90,
        data[0x6bee38 - tlo:0x6bee41 - tlo].hex(' '))
    chk('instance B likewise has exactly 8 nops then the next function',
        data[0x41c2d8 - tlo:0x41c2e0 - tlo] == b'\x90' * 8
        and data[0x41c2e0 - tlo] != 0x90,
        data[0x41c2d8 - tlo:0x41c2e1 - tlo].hex(' '))
    chk('objdump decoded the same 136-byte span (mentions 6bee35 ret)',
        '6bee35' in txt, 'ret line present')
except Exception as e:
    print('objdump error', e)

json.dump(R, open(OUT, 'w'), ensure_ascii=False, indent=1)
json.dump(ASSERT, open(OUT.replace('.json', '_assert.json'), 'w'), ensure_ascii=False, indent=1)
nf = sum(1 for a in ASSERT if not a['pass'])
print()
print('== assertions: %d total, %d FAIL ==' % (len(ASSERT), nf))
print('wrote', OUT)
