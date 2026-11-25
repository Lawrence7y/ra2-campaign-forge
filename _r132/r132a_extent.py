#!/usr/bin/env python3
# R132 r132a: TRUE function extent via CFG reachability.
#
# R131 (r131i) defined the "template body" as bytes from the entry up to the FIRST ret.
# That is a heuristic, not a proof. This script does a mechanical CFG reachability walk
# from the entry (follow fallthrough + all branch targets, stop at ret) and compares.
#
# Claim under test: the two known instantiations are 136 bytes, not 106, because a
# conditional branch leaves the function past the first ret into a reachable else-block.
import json, struct, hashlib, io
import pefile
from capstone import Cs, CS_ARCH_X86, CS_MODE_32

EXE = '/home/t628/projects/ra2-campaign-forge/ra2bench/gamemd.exe'
OUT = '/home/t628/projects/ra2-campaign-forge/_r132/r132a_extent.json'

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

JCC = {'je','jne','jl','jle','jg','jge','jb','jbe','ja','jae','js','jns','jo','jno',
       'jp','jnp','jz','jnz','jc','jnc','jecxz','jecxz'}

def one(va):
    o = va - tlo
    for i in md.disasm(data[o:o+16], va, count=1):
        return i
    return None

def cfg_extent(entry, limit=4096):
    seen = {}            # va -> (mnemonic, size, targets)
    work = [entry]
    addrs = []
    n = 0
    while work and n < limit:
        va = work.pop()
        if va in seen: continue
        if not (tlo <= va < thi):
            seen[va] = ('OUT_OF_TEXT', 0, [])
            continue
        i = one(va)
        if i is None:
            seen[va] = ('UNDECODABLE', 0, [])
            continue
        mn = i.mnemonic
        tgt = []
        if mn in JCC or mn == 'jmp':
            op = i.op_str.strip()
            try:
                t = int(op, 16) if op.startswith('0x') else int(op)
                tgt.append(t)
            except ValueError:
                pass
        seen[va] = (mn, i.size, tgt)
        addrs.append(va)
        n += 1
        if mn == 'ret':
            continue                       # terminal
        # fallthrough
        work.append(va + i.size)
        for t in tgt:
            work.append(t)
    addrs.sort()
    return seen, addrs

def first_ret_end(entry):
    o = entry - tlo
    for i in md.disasm(data[o:o+0x200], entry):
        if i.mnemonic == 'ret':
            return i.address + i.size
    return None

R = {'functions': {}, 'controls': {}}

for label, entry in (('A', 0x6bedb0), ('B', 0x41c250)):
    seen, addrs = cfg_extent(entry)
    end = max(a + seen[a][1] for a in addrs if seen[a][1])
    fr_end = first_ret_end(entry)
    fn = {'entry': hex(entry), 'cfg_end': hex(end), 'cfg_len': end - entry,
          'first_ret_end': hex(fr_end), 'first_ret_len': fr_end - entry,
          'insn_count': len(addrs)}
    # branch targets that lie BEYOND the first-ret end => first-ret heuristic truncates
    beyond = []
    for a in addrs:
        for t in seen[a][2]:
            if t >= fr_end:
                beyond.append({'from': hex(a), 'to': hex(t)})
    fn['branches_beyond_first_ret'] = beyond
    fn['truncation_proven'] = len(beyond) > 0 and end > fr_end
    R['functions'][label] = fn
    print('[%s] entry=%s cfg_end=%s len=%d | first_ret_end=%s len=%d | beyond=%d'
          % (label, hex(entry), hex(end), end - entry, hex(fr_end), fr_end - entry, len(beyond)))
    for b in beyond:
        print('     branch %s -> %s (past first ret)' % (b['from'], b['to']))

# ---- full-body byte diff over the TRUE extent ----
a0, a1 = 0x6bedb0, 0x6bedb0 + R['functions']['A']['cfg_len']
b0 = 0x41c250
A = data[a0 - tlo:a1 - tlo]
B = data[b0 - tlo:b0 - tlo + len(A)]
diff = [{'rel': k, 'A': A[k], 'B': B[k]} for k in range(len(A)) if A[k] != B[k]]
R['full_body'] = {'len': len(A), 'A_sha': hashlib.sha256(A).hexdigest()[:16],
                  'B_sha': hashlib.sha256(B).hexdigest()[:16],
                  'diff': diff, 'diff_count': len(diff)}
print('full body len=%d diffs=%d' % (len(A), len(diff)))
for d in diff:
    print('   rel 0x%02x  A=%02x  B=%02x' % (d['rel'], d['A'], d['B']))

# ---- what the truncated 106-byte view would have said ----
T = 106
At, Bt = A[:T], B[:T]
dt = [k for k in range(T) if At[k] != Bt[k]]
R['truncated_106'] = {'diff_rel': dt, 'diff_count': len(dt)}
print('truncated 106-byte view diffs:', ['0x%02x' % k for k in dt])

# ---- CONTROLS ----
# P1: a function that really is straight-line-to-first-ret must show NO branch beyond.
#     use 0x6bedb0's own main body only if it had no je past ret -- instead use a
#     synthetic control: run CFG on an entry whose first ret is truly terminal.
#     Use the else block entry 0x6bee1a which ends in ret with no forward branch out.
seen_e, addrs_e = cfg_extent(0x6bee1a)
end_e = max(a + seen_e[a][1] for a in addrs_e if seen_e[a][1])
fr_e = first_ret_end(0x6bee1a)
R['controls']['P1_else_block_no_branch_beyond'] = {
    'cfg_end': hex(end_e), 'first_ret_end': hex(fr_e), 'equal': end_e == fr_e,
    'pass': end_e == fr_e}
print('P1 else-block cfg_end=%s first_ret_end=%s equal=%s'
      % (hex(end_e), hex(fr_e), end_e == fr_e))

# P2: the CFG walk must actually have visited the else block addresses
else_start = 0x6bedb0 + 106
R['controls']['P2_else_block_reached'] = {
    'else_start': hex(else_start),
    'in_walk': else_start in addrs,
    'pass': else_start in addrs}
print('P2 else block 0x%x reached by CFG walk: %s' % (else_start, else_start in addrs))

# P3: negative control -- walking from a garbage entry must NOT reproduce 136.
#     start mid-instruction at entry+1 and confirm the extent differs.
seen_g, addrs_g = cfg_extent(0x6bedb1)
end_g = max((a + seen_g[a][1] for a in addrs_g if seen_g[a][1]), default=0)
R['controls']['P3_misaligned_different'] = {
    'misaligned_end': hex(end_g), 'differs_from_true': end_g != end_a if False else (end_g != a1),
    'pass': end_g != a1}
print('P3 misaligned entry 0x6bedb1 end=%s differs=%s' % (hex(end_g), end_g != a1))

# P4: decoding sanity -- the instruction at the je target must be a real instruction start
R['controls']['P4_je_target_decodes'] = {
    'pass': one(0x6bee1a) is not None and one(0x6bee1a).mnemonic == 'mov',
    'seen': one(0x6bee1a).mnemonic if one(0x6bee1a) else None}

ASSERT = []
def chk(n, c, d=''):
    ASSERT.append({'assert': n, 'pass': bool(c), 'detail': str(d)})
    print(('  PASS ' if c else '  FAIL ') + n + ((' [%s]' % d) if d else ''))
for lbl in ('A','B'):
    f = R['functions'][lbl]
    chk('extent %s is 136 bytes via CFG' % lbl, f['cfg_len'] == 136, f['cfg_len'])
    chk('first-ret heuristic on %s gives 106' % lbl, f['first_ret_len'] == 106, f['first_ret_len'])
    chk('%s truncation proven by a branch past the first ret' % lbl, f['truncation_proven'])
chk('full 136-byte diff count is 2', R['full_body']['diff_count'] == 2, R['full_body']['diff_count'])
chk('truncated 106-byte diff count is 1', R['truncated_106']['diff_count'] == 1, R['truncated_106']['diff_count'])
chk('P1 else block closes at same address', R['controls']['P1_else_block_no_branch_beyond']['pass'])
json.dump(ASSERT, open(OUT.replace('.json','_assert.json'),'w'), ensure_ascii=False, indent=1)
print('assertions:', len(ASSERT), 'FAIL', sum(1 for a in ASSERT if not a['pass']))
json.dump(R, open(OUT, 'w'), ensure_ascii=False, indent=1)
print('P4 je-target decodes as mov:', R['controls']['P4_je_target_decodes']['seen'])
print('wrote', OUT)
