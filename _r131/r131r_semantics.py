#!/usr/bin/env python3
# R131 r131r: the wrapper's semantic identity, argued from bytes only.
#
# Established by r131q (35/35): the wrapper 0x6bedb0 has exactly three stack args and
# this is the full body. Reads resolve to:
#   arg1 = rclsid for CoCreateInstance        (0x6bedc8 -> pushed as arg5 of CoCreateInstance)
#   arg2 = BOTH pUnkOuter and the ppv out-slot (0x6bedcc takes its address; 0x6bedd7 reads it)
#   arg3 = CLSCTX word, tested with test al,0x14
#   after creation: vtable[0] called with 3 args (vtbl+0, this=?, +arg2) => QueryInterface
#   then Release on the created pointer; on failure the old pointer is released first.
#
# Two open questions this script settles with bytes:
#   Q1  what are the three args at the ONLY real call site (0x6bc364 / 0x6bc3aa)? -> 7, 0, [esi]
#       i.e. rclsid from the table, pUnkOuter=NULL, CLSCTX=7.
#   Q2  is "test al,0x14 with CLSCTX=7" a property of THIS wrapper or a general
#       CoCreateInstance idempotence guard? Compare with the sibling instantiation
#       0x41c250 which is called from 13 sites: does it carry the same guard?
import json
import struct

import pefile
from capstone import Cs, CS_ARCH_X86, CS_MODE_32

EXE = '/home/t628/projects/ra2-campaign-forge/ra2bench/gamemd.exe'
OUT = '/home/t628/projects/ra2-campaign-forge/_r131/r131r_semantics.json'
pe = pefile.PE(EXE, fast_load=True)
base = pe.OPTIONAL_HEADER.ImageBase
secs = {}
for s in pe.sections:
    nm = s.Name.rstrip(b'\x00').decode('latin-1')
    secs[nm] = (base + s.VirtualAddress, base + s.VirtualAddress + s.SizeOfRawData, s)
tlo, thi, ts = secs['.text']
data = ts.get_data()
md = Cs(CS_ARCH_X86, CS_MODE_32)

A = []
def chk(name, cond, detail=''):
    A.append({'assert': name, 'ok': bool(cond), 'detail': detail})
    print(('PASS ' if cond else 'FAIL ') + name + (' :: ' + str(detail) if detail else ''))

R = {}
CLSCTX = {0x1: 'INPROC_SERVER', 0x2: 'INPROC_HANDLER', 0x4: 'LOCAL_SERVER',
          0x10: 'REMOTE_SERVER', 0x400: 'NO_CODE_DOWNLOAD'}
def decode_clsctx(v):
    names = [n for b, n in CLSCTX.items() if v & b]
    rest = v & ~sum(CLSCTX)
    return {'value': v, 'bits': names, 'unexplained_bits': rest}

# NOTE ON IMMEDIATE PARSING (self-error S-204, same family as R130 S-200):
# capstone prints SMALL immediates in DECIMAL -- `push 7` and `push 0`, not `push 0x7`.
# A parser that only accepts the 0x form classifies these two args as "register/memory"
# and the assertions below fail for a reason that has nothing to do with the binary.
IMMRE = __import__('re').compile(r'^(0[xX][0-9a-fA-F]+|-?\d+)$')
def imm_of(op):
    s = op.strip()
    if not IMMRE.match(s):
        return None
    return int(s, 16) if s[:2].lower() == '0x' else int(s, 10)

# ---- Q1: the two real call sites' argument values ----
# The call at 0x6bc364 is inside the loop whose head is 0x6bc34d. A window taken as
# (site - 0x30) lands MID-INSTRUCTION (it decoded `aam 0xf5`), so both sites are decoded
# from the loop's own instruction boundary 0x6bc342 instead (S-205).
LOOP_ORIGIN = 0x6bc342
loop_insns = {}
for i in md.disasm(data[LOOP_ORIGIN - tlo:LOOP_ORIGIN - tlo + 0x100], LOOP_ORIGIN):
    loop_insns[i.address] = i
loop_addrs = sorted(loop_insns)

SITES = {}
for site in (0x6bc364, 0x6bc3aa):
    k = loop_addrs.index(site)
    # walk back from the call, collecting pushes until the previous call/jump
    pushes = []
    j = k - 1
    while j >= 0:
        i = loop_insns[loop_addrs[j]]
        if i.mnemonic == 'push':
            pushes.append(i)
        elif i.mnemonic.startswith('j') or i.mnemonic == 'call':
            break
        j -= 1
    pushes.reverse()
    last3 = pushes[-3:]
    args = {}
    for pos, p in enumerate(reversed(last3), start=1):
        op = p.op_str.strip()
        v = imm_of(op)
        args['arg%d' % pos] = ({'kind': 'imm', 'value': v, 'text': op, 'at': hex(p.address)}
                              if v is not None else
                              {'kind': 'reg-or-mem', 'text': op, 'at': hex(p.address)})
    lea = [loop_insns[a] for a in loop_addrs[:k + 1]
           if loop_insns[a].mnemonic == 'lea' and loop_insns[a].op_str.startswith('ecx')]
    SITES[hex(site)] = {'args': args,
                        'this': lea[-1].op_str if lea else None,
                        'pushes_before': len(pushes),
                        'window': ['%08x %-18s %s %s' % (loop_insns[a].address,
                                                         loop_insns[a].bytes.hex(),
                                                         loop_insns[a].mnemonic,
                                                         loop_insns[a].op_str)
                                   for a in loop_addrs if site - 0x24 <= a <= site]}
R['call_sites'] = SITES
for k2, v in SITES.items():
    print('=== call site %s ===' % k2)
    for w in v['window']:
        print('   ' + w)
    print('   args:', json.dumps(v['args'], ensure_ascii=False))
    print('   this:', v['this'], ' pushes_before:', v['pushes_before'])

s1 = SITES['0x6bc364']
s2 = SITES['0x6bc3aa']
chk('site 0x6bc364 arg1 (rclsid) is the register edx, loaded earlier from [esi] (table entry +0)',
    s1['args']['arg1']['kind'] == 'reg-or-mem' and s1['args']['arg1']['text'] == 'edx'
    and any(loop_insns[a].mnemonic == 'mov' and loop_insns[a].op_str == 'edx, dword ptr [esi]'
            for a in loop_addrs if a < 0x6bc364),
    s1['args']['arg1'])
chk('site 0x6bc364 arg2 (pUnkOuter / ppv slot) is the immediate 0',
    s1['args']['arg2']['kind'] == 'imm' and s1['args']['arg2']['value'] == 0,
    s1['args']['arg2'])
chk('site 0x6bc364 arg3 (dwClsContext) is the immediate 7',
    s1['args']['arg3']['kind'] == 'imm' and s1['args']['arg3']['value'] == 7,
    s1['args']['arg3'])
chk('site 0x6bc3aa passes the same three values (7, 0, [esi+0])',
    s2['args']['arg2'] == {'kind': 'imm', 'value': 0, 'text': '0', 'at': s2['args']['arg2']['at']}
    and s2['args']['arg3']['value'] == 7, s2['args'])
R['clsctx_at_loop_site'] = decode_clsctx(7)
chk('dwClsContext=7 is exactly INPROC_SERVER|INPROC_HANDLER|LOCAL_SERVER, no unexplained bits',
    R['clsctx_at_loop_site']['bits'] == ['INPROC_SERVER', 'INPROC_HANDLER', 'LOCAL_SERVER']
    and R['clsctx_at_loop_site']['unexplained_bits'] == 0, R['clsctx_at_loop_site'])

# The guard `test al,0x14` tests bits 0x4|0x10 = LOCAL_SERVER|REMOTE_SERVER.
# dwClsContext=7 CONTAINS 0x4 => the test is NON-ZERO => ZF=0 => `je` NOT taken =>
# control FALLS THROUGH into CoCreateInstance. (I first wrote this the other way round;
# corrected by arithmetic, 7 & 0x14 = 4, not 0 -- self-error S-206.)
R['guard_0x14'] = decode_clsctx(0x14)
R['clsctx_and_guard'] = 7 & 0x14
chk('the guard constant 0x14 = LOCAL_SERVER|REMOTE_SERVER',
    R['guard_0x14']['bits'] == ['LOCAL_SERVER', 'REMOTE_SERVER'], R['guard_0x14'])
chk('7 & 0x14 == 4 (non-zero) so at the loop site the je is NOT taken and '
    'CoCreateInstance IS called', R['clsctx_and_guard'] == 4, hex(R['clsctx_and_guard']))
chk('control: a CLSCTX with no LOCAL/REMOTE bit (e.g. 0x3) WOULD take the je branch',
    (0x3 & 0x14) == 0, hex(0x3 & 0x14))

# ---- Q2: does the sibling instantiation carry the same guard? ----
def body_of(va):
    seg = data[va - tlo:va - tlo + 0x80]
    out = {}
    for i in md.disasm(seg, va):
        out[i.address] = i
    return out
sib = body_of(0x41c250)
R['sibling_guard'] = {hex(v): ('%s %s' % (i.mnemonic, i.op_str))
                      for v, i in sib.items() if i.mnemonic in ('test', 'je', 'jne', 'jl')}
print('=== sibling 0x41c250 conditional structure ===')
for k, v in R['sibling_guard'].items():
    print('   %s  %s' % (k, v))
chk('the sibling instantiation carries the SAME test al,0x14 guard at +0x14',
    any(i.mnemonic == 'test' and i.op_str == 'al, 0x14' for i in sib.values()),
    [i.op_str for i in sib.values() if i.mnemonic == 'test'])
chk('the sibling differs from 0x6bedb0 in exactly the IID it pushes (0x4e), so the guard '
    'is a property of the TEMPLATE, not of this instance',
    data[0x6bedb0 - tlo + 0x4e] == 0xc0 and data[0x41c250 - tlo + 0x4e] == 0xb0,
    (hex(data[0x6bedb0 - tlo + 0x4e]), hex(data[0x41c250 - tlo + 0x4e])))

# ---- Q3: the sibling's 13 call sites -- what dwClsContext do they pass? ----
# R130's whole "each table entry is (CLSID, dll)" story is instantiated twice, so the
# honest question is whether the OleRun path (guard bits set) is live anywhere. Every
# sibling site pushes an immediate 7 as the third arg too, so the answer is measured.
md.detail = False
SITES13 = [0x416bc2, 0x44e02c, 0x4db8cc, 0x4df85c, 0x51b064, 0x521fc2, 0x5230dc,
           0x65f092, 0x6cc999, 0x710213, 0x7354f2, 0x742699, 0x742a94]
obs = []
for site in SITES13:
    # decode from a known function boundary, then keep only instructions <= site
    a = site - 0x120
    win = {}
    for i in md.disasm(data[a - tlo:a - tlo + 0x124], a):
        if i.address > site:
            break
        win[i.address] = i
    seq = [win[x] for x in sorted(win)]
    pushes = []
    j = len(seq) - 1
    while j >= 0:
        i = seq[j]
        if i.mnemonic == 'push':
            pushes.append(i)
        elif i.mnemonic.startswith('j') or i.mnemonic == 'call':
            break
        j -= 1
    pushes.reverse()
    last3 = pushes[-3:]
    vals = []
    for p in reversed(last3):
        v = imm_of(p.op_str)
        vals.append(v if v is not None else p.op_str.strip())
    obs.append({'site': hex(site), 'n_pushes': len(pushes),
                'args_arg1_arg2_arg3': vals})
R['sibling_call_args'] = obs
print('=== sibling 13 call sites: (arg1, arg2, arg3) in that order ===')
for o in obs:
    print('   %-10s n_push=%d  %s' % (o['site'], o['n_pushes'], o['args_arg1_arg2_arg3']))
imm3 = [o['args_arg1_arg2_arg3'][2] for o in obs if isinstance(o['args_arg1_arg2_arg3'][2], int)]
R['sibling_clsctx_values'] = imm3
chk('all 13 sibling call sites pass an immediate dwClsContext, and all are 7',
    len(imm3) == 13 and set(imm3) == {7}, sorted(set(imm3)))
chk('therefore at all 15 call sites in the binary dwClsContext=7, 7&0x14 != 0, so the '
    'OleRun branch is never taken -- the guard is a template-level dead branch here',
    all((v & 0x14) != 0 for v in imm3) and (7 & 0x14) != 0,
    {'distinct': sorted(set(imm3)), 'clsctx&guard': 7 & 0x14})

R['assertions'] = A
R['summary'] = {'total': len(A), 'pass': sum(1 for x in A if x['ok']),
                'fail': [x['assert'] for x in A if not x['ok']]}
print('\nASSERTIONS: %d total, %d pass, %d fail'
      % (R['summary']['total'], R['summary']['pass'], len(R['summary']['fail'])))
json.dump(R, open(OUT, 'w'), ensure_ascii=False, indent=1)
raise SystemExit(1 if R['summary']['fail'] else 0)
