#!/usr/bin/env python3
# R132 r132c: re-test R131's "OleRun branch is dead" claim on the TRUE 136-byte body.
#
# R131 analysed the truncated 106-byte body, in which the else-block (the second half)
# was invisible. It concluded, for 15/15 call sites, that dwClsContext=7 and that
# 7 & 0x14 != 0 so "je not taken", therefore "the OleRun branch is dead".
#
# Two things must be checked separately:
#   (1) is the vale-block reached at runtime?  (depends on test al,0x14 with al = LOW BYTE
#       of the dwClsContext argument -- only bit0..3 matter)
#   (2) does the else-block contain a CoCreateInstance+OleRun sequence that R131 never saw?
import json, struct
import pefile
from capstone import Cs, CS_ARCH_X86, CS_MODE_32

EXE = '/home/t628/projects/ra2-campaign-forge/ra2bench/gamemd.exe'
OUT = '/home/t628/projects/ra2-campaign-forge/_r132/r132c_olerun.json'

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

R = {'bodies': {}}

# --- structural facts about the full 136-byte body ---
for label, entry, ln in (('A', 0x6bedb0, 136), ('B', 0x41c250, 136)):
    o = entry - tlo
    b = data[o:o + ln]
    d = {'entry': hex(entry), 'len': ln,
         'ccis_sites': [], 'olerun_sites': [], 'push_imm': []}
    for i in md.disasm(b, entry):
        if i.mnemonic == 'call' and '0x7e15fc' in i.op_str:
            d['ccis_sites'].append(hex(i.address))
        if i.mnemonic == 'call' and '0x7e1600' in i.op_str:
            d['olerun_sites'].append(hex(i.address))
        if i.mnemonic == 'push' and i.op_str.startswith('0x'):
            d['push_imm'].append({'at': hex(i.address), 'rel': i.address - entry,
                                  'v': hex(int(i.op_str, 16))})
    R['bodies'][label] = d
    print('[%s] CoCreateInstance at %s ; OleRun at %s'
          % (label, d['ccis_sites'], d['olerun_sites']))

# --- the critical correction: test al,0x14 tests the LOW BYTE, so only 0..3 matter ---
# dwClsContext values observed at the 15 R131 call sites. Re-derive from the wrapper:
# the wrapper reads arg2 (dwClsContext) into eax then does test al,0x14.
# 0x14 = 0b00010100 -> bits 2 and 4. But AL only carries bits 0..7, so bit2 is visible.
# 7 = 0b111 -> bit2 SET -> (7 & 0x14) = 4 != 0 -> ZF=0 -> je NOT taken -> else block SKIPPED.
R['bitwise'] = {
    'const': 'al & 0x14',
    'value_7': 7 & 0x14,
    'value_1': 1 & 0x14,
    'value_0': 0 & 0x14,
    'note': 'AL holds only bits 0..7 of the dword argument; bit 4 of 0x14 can NEVER be '
            'set by AL, so an argument whose low byte has bit2 clear falls through to else',
}
print('bitwise:', R['bitwise'])

# --- which dwClsContext values actually reach here? census across ALL 21 ccis sites ---
pat = bytes.fromhex('ff15fc157e00')
sites = []
i = 0
while True:
    i = data.find(pat, i)
    if i < 0:
        break
    sites.append(tlo + i)
    i += 1
R['all_ccis_sites'] = [hex(s) for s in sites]
print('all call [CoCreateInstance] sites:', len(sites))

# For each site, walk backwards collecting the immediately preceding pushes
def pushes_before(site, maxn=8):
    out = []
    va = site
    for _ in range(maxn):
        # find an instruction start ending exactly at va: brute over short windows
        best = None
        for back in range(2, 16):
            cand = va - back
            if cand < tlo:
                break
            for ii in md.disasm(data[cand - tlo:cand - tlo + 16], cand, count=1):
                if ii.address + ii.size == va and ii.mnemonic in ('push', 'mov', 'lea', 'call'):
                    best = ii
                    break
            if best:
                break
            if best is None and back > 12:
                break
        if not best:
            break
        out.append({'at': hex(best.address), 'mn': best.mnemonic, 'op': best.op_str})
        if best.mnemonic == 'call':
            break
        va = best.address
    out.reverse()
    return out

R['site_contexts'] = {}
for s in sites:
    ctx = pushes_before(s)
    R['site_contexts'][hex(s)] = ctx

print()
print('--- context before each CoCreateInstance call (last 6 instrs) ---')
for s in sites:
    ctx = R['site_contexts'][hex(s)][-6:]
    print('0x%x:' % s)
    for c in ctx:
        print('    %s %-8s %s' % (c['at'], c['mn'], c['op']))

ASSERT = []
def chk(n, c, d=''):
    ASSERT.append({'assert': n, 'pass': bool(c), 'detail': str(d)})
    print(('  PASS ' if c else '  FAIL ') + n + ((' [%s]' % d) if d else ''))
for lbl in ('A','B'):
    d = R['bodies'][lbl]
    chk('%s body has 2 CoCreateInstance sites' % lbl, len(d['ccis_sites']) == 2, len(d['ccis_sites']))
    chk('%s body has 1 OleRun site' % lbl, len(d['olerun_sites']) == 1, len(d['olerun_sites']))
chk('bitwise 7 & 0x14 = 4', R['bitwise']['value_7'] == 4, R['bitwise']['value_7'])
chk('21 CoCreateInstance sites enumerated', len(R['all_ccis_sites']) == 21, len(R['all_ccis_sites']))
json.dump(ASSERT, open(OUT.replace('.json','_assert.json'),'w'), ensure_ascii=False, indent=1)
print('assertions:', len(ASSERT), 'FAIL', sum(1 for a in ASSERT if not a['pass']))
json.dump(R, open(OUT, 'w'), ensure_ascii=False, indent=1)
print('wrote', OUT)
