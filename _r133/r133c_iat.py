#!/usr/bin/env python3
# R133 r133c (v2): resolve the import names behind every call in the 136-byte template.
#
# SELF-ERROR CORRECTION (S-218): the first version keyed the IAT dict by base+imp.address.
# pefile's imp.address is ALREADY an absolute VA for this image (ole32 first slot 0x7e15c8
# lands inside .rdata VA 0x7e1000-0x811074; adding ImageBase would land at 0xbe15c8, which
# is outside every section and resolves nothing). After the fix all 6 IAT calls resolve.
#
# The .rdata content AT the IAT slots in the file is a block of .text-looking pointers
# (0x410854 ... 0x410936). Those are PRE-LOAD PLACEHOLDER bytes -- the loader overwrites
# the 15 dwords of ole32's FirstThunk at load time. Disassembling them as code yields
# garbage (mid-instruction starts), and treating them as a dispatch table would be wrong.
import json
import pefile
from capstone import Cs, CS_ARCH_X86, CS_MODE_32

EXE = '/home/t628/projects/ra2-campaign-forge/ra2bench/gamemd.exe'
OUT = '/home/t628/projects/ra2-campaign-forge/_r133/r133c_iat.json'

pe = pefile.PE(EXE)
base = pe.OPTIONAL_HEADER.ImageBase
img = pe.get_memory_mapped_image()
secs = {}
for s in pe.sections:
    nm = s.Name.rstrip(b'\x00').decode('latin-1')
    secs[nm] = (base + s.VirtualAddress,
                base + s.VirtualAddress + max(s.Misc_VirtualSize, s.SizeOfRawData), s)
tlo, thi, ts = secs['.text']  # VA-based
assert tlo == base + 0x1000, hex(tlo)
data = ts.get_data()

R = {}; ASSERT = []
def chk(n, c, d=''):
    ASSERT.append({'assert': n, 'pass': bool(c), 'detail': str(d)})
    print(('  PASS ' if c else '  FAIL ') + n + (('  [' + str(d) + ']') if d else ''))
    return bool(c)

# --- IAT keyed by the VA pefile reports (do NOT add ImageBase) ---
IAT = {}
R['dlls'] = {}
for entry in getattr(pe, 'DIRECTORY_ENTRY_IMPORT', []):
    dll = entry.dll.decode('latin-1', 'replace')
    R['dlls'][dll] = len(entry.imports)
    for imp in entry.imports:
        nm = (imp.name.decode('latin-1', 'replace') if imp.name else 'ord_%d' % imp.ordinal)
        IAT[imp.address] = dll + '!' + nm
R['iat_slots'] = len(IAT)
print('import slots:', len(IAT), ' ole32:', R['dlls'].get('ole32.dll'))

def imp_of(va):
    return IAT.get(va)

def sec_of(va):
    for nm, (lo, hi, s) in secs.items():
        if lo <= va < hi:
            return nm
    return None

# sanity: every IAT slot VA must fall inside a real section
R['iat_sections'] = {}
for va in IAT:
    sn = sec_of(va)
    R['iat_sections'][sn] = R['iat_sections'].get(sn, 0) + 1
print('IAT slot sections:', R['iat_sections'])

# --- calls inside the two bodies ---
INSTS = {'A': 0x6bedb0, 'B': 0x41c250}
md = Cs(CS_ARCH_X86, CS_MODE_32)
R['calls'] = {}
for label, entry in INSTS.items():
    body = data[entry - tlo: entry - tlo + 136]
    rows = []
    for i in md.disasm(body, entry):
        if i.mnemonic != 'call':
            continue
        op = i.op_str
        rec = {'off': hex(i.address - entry), 'ops': op}
        if op.startswith('dword ptr ['):
            inner = op[len('dword ptr ['):-1].replace(' ', '')
            if inner.startswith('0x'):
                va = int(inner, 16)
                rec.update({'iat_va': hex(va), 'slot_sec': sec_of(va), 'imp': imp_of(va)})
            else:
                rec['vtable'] = inner
        rows.append(rec)
    R['calls'][label] = rows
    print('--- %s @ %#x ---' % (label, entry))
    for r in rows:
        print('   +%s  call %-24s %s' % (r['off'], r['ops'], r.get('imp') or ('vtbl %s' % r.get('vtable'))))

print('\n--- assertions ---')
chk('IAT resolves to the same 372 slots as reported by the loader view', len(IAT) == 372, len(IAT))
chk('every IAT slot lies inside .rdata (VA consistently used, no RVA mix-up)',
    set(R['iat_sections']) == {'.rdata'}, R['iat_sections'])
chk('pefile imp.address is already an ABSOLUTE VA for this image (0x7e15fc sits in .rdata)',
    sec_of(0x7e15fc) == '.rdata' and sec_of(base + 0x7e15fc) is None,
    {'direct': sec_of(0x7e15fc), 'plus_base': sec_of(base + 0x7e15fc)})
chk('0x7e15fc is ole32!CoCreateInstance',
    imp_of(0x7e15fc) == 'ole32.dll!CoCreateInstance', imp_of(0x7e15fc))
chk('0x7e1600 is ole32!OleRun', imp_of(0x7e1600) == 'ole32.dll!OleRun', imp_of(0x7e1600))
chk('every IAT-directed call in both bodies resolves to a named import',
    all(r.get('imp') for lab in R['calls'] for r in R['calls'][lab] if 'iat_va' in r),
    [(lab, r['iat_va'], r.get('imp')) for lab in R['calls'] for r in R['calls'][lab] if 'iat_va' in r])
ra = [(r['off'], r['iat_va']) for r in R['calls']['A'] if 'iat_va' in r]
rb = [(r['off'], r['iat_va']) for r in R['calls']['B'] if 'iat_va' in r]
chk('STRUCTURE IDENTICAL: A and B call the same IAT slots at the same offsets', ra == rb, ra)
chk('instance A/B: 3 IAT calls each = CoCreate(create arm) + OleRun + CoCreate(else arm)',
    [r.get('imp') for r in R['calls']['A'] if 'iat_va' in r] ==
    ['ole32.dll!CoCreateInstance', 'ole32.dll!OleRun', 'ole32.dll!CoCreateInstance'],
    [r.get('imp') for r in R['calls']['A'] if 'iat_va' in r])
# vtable slots named: [ecx] is IUnknown slot 0 (QI), [ecx+8]/[edx+8] is slot 2 (Release)
chk('vtable calls hit IUnknown slot 0 (QI) then slot 2 (Release)',
    [r.get('vtable') for r in R['calls']['A'] if 'vtable' in r] == ['ecx + 8', 'ecx', 'edx + 8'],
    [r.get('vtable') for r in R['calls']['A'] if 'vtable' in r])
# ANTI: a neighbouring slot must be a different import
chk('ANTI: 0x7e15f8 and 0x7e1604 are NOT CoCreateInstance (lookup has resolution)',
    imp_of(0x7e15f8) == 'ole32.dll!OleLoadFromStream' and imp_of(0x7e1604) is None,
    (imp_of(0x7e15f8), imp_of(0x7e1604)))
# ANTI: prove the file content at the slot is NOT the runtime target (placeholder), i.e.
# the dword in the file at 0x7e15fc lies inside .text and would decode mid-instruction.
import struct
p = struct.unpack_from('<I', img, 0x7e15fc - base)[0]
sn = sec_of(p)
md2 = Cs(CS_ARCH_X86, CS_MODE_32); md2.skipdata = True
starts = set()
o = tlo - tlo
for a, sz, mn, ops in md2.disasm_lite(data, tlo):
    starts.add(a)
chk('ANTI: the on-disk dword at the IAT slot is the pre-load placeholder value, not a real thunk',
    sn == '.text' and p not in starts,
    {'value': hex(p), 'section': sn, 'is_instruction_start': p in starts})
R['placeholder_probe'] = {'slot': hex(0x7e15fc), 'file_value': hex(p), 'section': sn,
                          'is_instruction_start': p in starts}

R['assertions'] = ASSERT
R['summary'] = {'pass': sum(1 for x in ASSERT if x['pass']), 'total': len(ASSERT)}
print('\nSUMMARY %d/%d PASS' % (R['summary']['pass'], R['summary']['total']))
json.dump(R, open(OUT, 'w'), indent=1)
