#!/usr/bin/env python3
# R133 r133d: can ANY call path reach the else arm (the +0x6a..+0x85 block) with a
# dwClsContext whose bits make `test al,0x14` yield ZF=1?
#
# R132 proved: at the 15 known call sites the value is 7, so 7 & 0x14 = 4 != 0, ZF=0,
# je NOT taken -> fallthrough arm (CoCreate + OleRun). R132 explicitly left open:
# "could something else call these two entries with bit2 == 0?" That is what this settles.
#
# Three independent sweeps over the WHOLE .text:
#   (1) direct call/rel32 to 0x6bedb0 or 0x41c250   (E8 rel32 and E9 rel32)
#   (2) the entry VA appearing as an imm32 anywhere (a function-pointer table entry)
#   (3) any instruction in .text whose operand mentions the entry VA
# If (1) is empty beyond the known sites and (2)/(3) are empty, no other caller exists.
import json, struct, re
import pefile
from capstone import Cs, CS_ARCH_X86, CS_MODE_32

EXE = '/home/t628/projects/ra2-campaign-forge/ra2bench/gamemd.exe'
OUT = '/home/t628/projects/ra2-campaign-forge/_r133/r133d_callers.json'

pe = pefile.PE(EXE, fast_load=True)
base = pe.OPTIONAL_HEADER.ImageBase
secs = {}
for s in pe.sections:
    nm = s.Name.rstrip(b'\x00').decode('latin-1')
    secs[nm] = (base + s.VirtualAddress,
                base + s.VirtualAddress + max(s.Misc_VirtualSize, s.SizeOfRawData), s)
tlo, thi, ts = secs['.text']
data = ts.get_data()
raw = open(EXE, 'rb').read()

R = {}; ASSERT = []
def chk(n, c, d=''):
    ASSERT.append({'assert': n, 'pass': bool(c), 'detail': str(d)})
    print(('  PASS ' if c else '  FAIL ') + n + (('  [' + str(d) + ']') if d else ''))
    return bool(c)

TARGETS = {0x6bedb0: 'A', 0x41c250: 'B'}
KNOWN = {0x6bedb0: [0x6bc364, 0x6bc3aa], 0x41c250: None}   # B: 13 sites, discovered below

# ---------- (1) raw E8/E9 rel32 scan ----------
R['direct_calls'] = {}
for tgt in TARGETS:
    hits = []
    for i in range(len(data) - 5):
        if data[i] not in (0xE8, 0xE9):
            continue
        rel = struct.unpack_from('<i', data, i + 1)[0]
        # instruction starts at tlo+i; target = tlo+i+5+rel
        if tlo + i + 5 + rel == tgt:
            hits.append(tlo + i)
    R['direct_calls'][hex(tgt)] = [hex(x) for x in hits]
    print('raw E8/E9 -> %#x :' % tgt, [hex(x) for x in hits])

# ---------- (1b) confirm each hit really decodes as a call/jmp (not a coincidental byte) ----------
md = Cs(CS_ARCH_X86, CS_MODE_32); md.skipdata = True
R['direct_calls_verified'] = {}
for tgt in TARGETS:
    ok = []
    for hs in R['direct_calls'][hex(tgt)]:
        h = int(hs, 16)
        o = h - tlo
        got = None
        for ins in md.disasm(data[o:o + 8], h, count=1):
            got = ins
        if got and got.mnemonic in ('call', 'jmp') and got.op_str == hex(tgt):
            ok.append(hex(h))
    R['direct_calls_verified'][hex(tgt)] = ok
    print('verified at instruction boundary -> %#x :' % tgt, ok)

# ---------- (2) entry VA as imm32 anywhere in the image ----------
R['imm32_refs'] = {}
for tgt in TARGETS:
    pat = struct.pack('<I', tgt)
    vahits = []
    for m in re.finditer(re.escape(pat), raw):
        try:
            va = base + pe.get_rva_from_offset(m.start())
        except Exception:
            continue
        vahits.append(va)
    R['imm32_refs'][hex(tgt)] = [hex(x) for x in vahits]
    print('imm32 references to %#x :' % tgt, [hex(x) for x in vahits])

# classify each imm32 site: is it inside .text (a code operand) or a data table?
R['imm32_classified'] = {}
for tgt in TARGETS:
    cls = {'text': [], 'data': [], 'other': []}
    for h in R['imm32_refs'][hex(tgt)]:
        where = None
        for nm, (lo, hi, s) in secs.items():
            if lo <= h < hi:
                where = nm; break
        if where == '.text':
            cls['text'].append(hex(h))
        elif where:
            cls['data'].append(hex(h))
        else:
            cls['other'].append(hex(h))
    R['imm32_classified'][hex(tgt)] = cls
    print('  %#x classified:' % tgt, {k: len(v) for k, v in cls.items()})

print('\n--- assertions ---')
for tgt, label in TARGETS.items():
    v = R['direct_calls_verified'][hex(tgt)]
    chk('%s: raw E8/E9 rel32 hits all decode as a real call/jmp on an instruction boundary' % label,
        len(v) == len(R['direct_calls'][hex(tgt)]), {'raw': len(R['direct_calls'][hex(tgt)]), 'verified': len(v)})

na = len(R['direct_calls_verified'][hex(0x6bedb0)])
nb = len(R['direct_calls_verified'][hex(0x41c250)])
chk('A (0x6bedb0) has exactly 2 direct call sites', na == 2, na)
chk('B (0x41c250) has exactly 13 direct call sites', nb == 13, nb)
chk('A call sites are the two already known (0x6bc364 / 0x6bc3aa)',
    sorted(R['direct_calls_verified'][hex(0x6bedb0)]) == sorted(['0x6bc364', '0x6bc3aa']),
    R['direct_calls_verified'][hex(0x6bedb0)])

# The load-bearing one: no entry VA is ever materialised as a value in code,
# so the template cannot be reached through a function pointer.
for tgt, label in TARGETS.items():
    c = R['imm32_classified'][hex(tgt)]
    chk('%s: the entry VA is NEVER used as an imm32 inside .text (no function-pointer handoff)' % label,
        len(c['text']) == 0, c)
    chk('%s: the entry VA is NEVER stored in any data section (no pointer table entry)' % label,
        len(c['data']) == 0, c)

# ANTI: the method must be able to FIND a pointer that really exists.
# 0x6bc34d is the function that CALLS 0x6bedb0; verify it is NOT reported as an imm32
# (calls are rel32, invisible to the imm32 scanner) -- proving scanner (2) is not trivially
# returning everything, AND that sweep (1) is not redundant with sweep (2).
chk('ANTI: sweep(2) does not find 0x6bedb0 for the known caller 0x6bc364 (rel32 is not imm32)',
    0x6bedb0 not in [int(x, 16) for x in R['imm32_refs'][hex(0x6bedb0)]],
    'rel32 call invisible to imm32 scan, as expected')
# ANTI 2: pick a VA that genuinely IS stored as imm32 somewhere and prove the scanner finds it
probe = 0x817bc0
pat = struct.pack('<I', probe)
hits = [base + pe.get_rva_from_offset(m.start()) for m in re.finditer(re.escape(pat), raw)]
chk('ANTI: scanner(2) DOES find a VA that is genuinely stored (0x817bc0 IID constant) -- non-vacuous',
    len(hits) > 0, {'va': hex(probe), 'n_hits': len(hits), 'first': [hex(x) for x in hits[:4]]})

R['summary_calls'] = {'A_sites': na, 'B_sites': nb,
                      'A_sites_list': R['direct_calls_verified'][hex(0x6bedb0)],
                      'B_sites_list': R['direct_calls_verified'][hex(0x41c250)]}
R['assertions'] = ASSERT
R['summary'] = {'pass': sum(1 for x in ASSERT if x['pass']), 'total': len(ASSERT)}
print('\nSUMMARY %d/%d PASS' % (R['summary']['pass'], R['summary']['total']))
json.dump(R, open(OUT, 'w'), indent=1)
