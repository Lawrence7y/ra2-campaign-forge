#!/usr/bin/env python3
# R131 r131q: RULE-D RECOMPUTATION of BOTH auditors' claims, by the lead session.
# Nothing here trusts the auditors; every number is recomputed from bytes and then
# compared to what each auditor reported.
#
# Auditors reported (verbatim numbers to check):
#   deepseek: 0x6bedb0 -> 2 call sites {0x6bc364,0x6bc3aa}
#             0x41c250 -> 13 call sites
#             body diff between the two 106-byte bodies: exactly 1 byte, offset 0x4e, c0 vs b0
#             exact copies of body A in .text: 1
#             GUID 0x817bb0 = {070F3290-9841-11D1-B709-00A024DDAFD1}, 0x817bc0 = IUnknown
#             imm32 of 0x817bc0 in .text: 9
#             capstone disasm_lite WITHOUT skipdata stops at 0x46f5a0 after 155215 insns
#   hy4:      loop call site 0x6bc34d pushes (in order) 7, 0, [esi]; ecx = lea [ebp-0xa3c]
#             wrapper ret imm = 0xc; test al, 0x14; je 0x6bee1a; call [ecx] / call [edx+8]
#
# Extra: a CORRECT thiscall/__stdcall stack model. The first version (r131g) ignored the
# fact that CoCreateInstance (5 args) and OleRun (1 arg) are __stdcall and pop their own
# arguments, which is why it produced esp conflicts. Here each call carries its known pop.
import json
import struct

import pefile
from capstone import Cs, CS_ARCH_X86, CS_MODE_32

EXE = '/home/t628/projects/ra2-campaign-forge/ra2bench/gamemd.exe'
OUT = '/home/t628/projects/ra2-campaign-forge/_r131/r131q_verify.json'

pe = pefile.PE(EXE, fast_load=True)
base = pe.OPTIONAL_HEADER.ImageBase
secs = {}
for s in pe.sections:
    nm = s.Name.rstrip(b'\x00').decode('latin-1')
    secs[nm] = (base + s.VirtualAddress, base + s.VirtualAddress + s.SizeOfRawData, s)
tlo, thi, ts = secs['.text']
data = ts.get_data()
md = Cs(CS_ARCH_X86, CS_MODE_32)

R = {}
A = []          # assertion log
def chk(name, cond, detail=''):
    A.append({'assert': name, 'ok': bool(cond), 'detail': detail})
    print(('PASS ' if cond else 'FAIL ') + name + (' :: ' + str(detail) if detail else ''))


# ---------- 1. call-site census, three independent ways ----------
def census_capstone(target, skipdata):
    md2 = Cs(CS_ARCH_X86, CS_MODE_32)
    md2.skipdata = skipdata
    hits = []
    for addr, size, mnem, op in md2.disasm_lite(data, tlo):
        if mnem != 'call':
            continue
        o = op.strip()
        try:
            v = int(o, 16) if o.lower().startswith('0x') else int(o, 10)
        except ValueError:
            continue
        if v == target:
            hits.append(addr)
    return hits


def census_e8(target):
    hits = []
    i = 0
    while True:
        i = data.find(b'\xe8', i)
        if i < 0 or i + 5 > len(data):
            break
        rel = struct.unpack('<i', data[i + 1:i + 5])[0]
        if tlo + i + 5 + rel == target:
            hits.append(tlo + i)
        i += 1
    return hits


def census_objdump(target):
    import subprocess
    p = subprocess.run(['i686-w64-mingw32-objdump', '-d', '--start-address=0x%x' % tlo,
                        '--stop-address=0x%x' % thi, EXE], capture_output=True, text=True, timeout=900)
    import re
    # objdump separates the byte column from the mnemonic with a TAB, and pads it with
    # spaces. A pattern that requires "call" immediately after one \s+ run fails on every
    # line (measured: 0 matches on a line that plainly reads "call 0x6bedb0").
    # Parse in two steps: address + byte column + mnemonic + operands.
    pat = re.compile(r'^\s+([0-9a-f]+):\s+((?:[0-9a-f]{2}\s)+)\s*(\w+)\s*(.*?)\s*$')
    hits = []
    for ln in p.stdout.splitlines():
        m = pat.match(ln)
        if not m or m.group(3) != 'call':
            continue
        op = m.group(4).strip()
        try:
            v = int(op, 16) if op.lower().startswith('0x') else int(op, 10)
        except ValueError:
            continue
        if v == target:
            hits.append(int(m.group(1), 16))
    return sorted(hits)


for tgt, expect in ((0x6bedb0, [0x6bc364, 0x6bc3aa]),
                    (0x41c250, None)):
    cap = sorted(census_capstone(tgt, True))
    e8 = sorted(census_e8(tgt))
    R.setdefault('census', {})[hex(tgt)] = {'capstone_skipdata': [hex(x) for x in cap],
                                           'raw_e8': [hex(x) for x in e8]}
    chk('census agrees capstone vs raw-E8 for 0x%x' % tgt, cap == e8, (len(cap), len(e8)))
    if expect:
        chk('0x%x site set == both auditors (2 sites)' % tgt, cap == expect, [hex(x) for x in cap])
    else:
        chk('0x%x site count == 13 (both auditors)' % tgt, len(cap) == 13, len(cap))

# negative control: capstone WITHOUT skipdata must be short (deepseek's 0x46f5a0 claim)
cap_noskip = census_capstone(0x6bedb0, False)
md3 = Cs(CS_ARCH_X86, CS_MODE_32)
n = 0
last = None
for addr, size, mnem, op in md3.disasm_lite(data, tlo):
    n += 1
    last = addr + size
R['noskip_stop'] = {'insns': n, 'last_end': hex(last) if last else None,
                    'target_hits': [hex(x) for x in cap_noskip]}
chk('without skipdata the 0x6bedb0 hits vanish (so skipdata is mandatory)',
    cap_noskip == [] and n < 200000, (n, hex(last) if last else None))

# objdump third decoder (only for the flagship target, it is slow)
obj = census_objdump(0x6bedb0)
R['census'][hex(0x6bedb0)]['objdump'] = [hex(x) for x in obj]
chk('third decoder (objdump) gives the same 2 sites', obj == [0x6bc364, 0x6bc3aa],
    [hex(x) for x in obj])

# ---------- 2. 106-byte body diff + exact copies ----------
FN = 0x6bedb0
LEN = 106
A_body = data[FN - tlo:FN - tlo + LEN]
B_body = data[0x41c250 - tlo:0x41c250 - tlo + LEN]
diff = [i for i in range(LEN) if A_body[i] != B_body[i]]
R['body'] = {'len': LEN, 'diff_offsets': diff,
             'diff_bytes': [('%02x' % A_body[i], '%02x' % B_body[i]) for i in diff]}
chk('two bodies differ in exactly 1 byte at offset 0x4e (c0 vs b0)',
    diff == [0x4e] and A_body[0x4e] == 0xc0 and B_body[0x4e] == 0xb0,
    R['body']['diff_bytes'])
chk('exactly one exact copy of body A in .text', data.count(A_body) == 1, data.count(A_body))
mut = bytearray(A_body)
mut[0x30] ^= 0xff
chk('negative control: flipped body has 0 copies', data.count(bytes(mut)) == 0, data.count(bytes(mut)))

# ---------- 3. GUID constants ----------
def guid(va):
    for nm, (lo, hi, s) in secs.items():
        if lo <= va < hi:
            o = va - (base + s.VirtualAddress)
            d = s.get_data()
            if o < 0 or o + 16 > min(s.SizeOfRawData, len(d)):
                return None
            g = d[o:o + 16]
            d1, d2, d3 = struct.unpack('<IHH', g[:8])
            return {'str': '{%08X-%04X-%04X-%s-%s}' % (d1, d2, d3, g[8:10].hex().upper(),
                                                        g[10:].hex().upper()),
                    'hex': g.hex(), 'section': nm}
    return None


g1, g2 = guid(0x817bc0), guid(0x817bb0)
R['guids'] = {'0x817bc0': g1, '0x817bb0': g2}
chk('0x817bc0 == IID_IUnknown {00000000-0000-0000-C000-000000000046}',
    g1['hex'] == '0000000000000000c000000000000046', g1['str'])
chk('0x817bb0 == {070F3290-9841-11D1-B709-00A024DDAFD1} (deepseek)',
    g2['str'] == '{070F3290-9841-11D1-B709-00A024DDAFD1}', g2['str'])
chk('both GUID constants live in .data', g1['section'] == '.data' == g2['section'],
    (g1['section'], g2['section']))
pat = struct.pack('<I', 0x817bc0)
R['imm_refs_0x817bc0'] = []
i = 0
while True:
    i = data.find(pat, i)
    if i < 0:
        break
    R['imm_refs_0x817bc0'].append(tlo + i)
    i += 1
chk('imm32 of 0x817bc0 occurs 9 times in .text (deepseek)', len(R['imm_refs_0x817bc0']) == 9,
    [hex(x) for x in R['imm_refs_0x817bc0']])

# ---------- 4. stack model of the wrapper ----------
# E0 = esp on entry; [E0+0]=retaddr, [E0+4]=arg1, [E0+8]=arg2, [E0+0xc]=arg3 (ret 0xc).
# Accounting (this is where TWO of my earlier attempts went wrong, kept as self-errors):
#   push X            => esp -= 4
#   pop               => esp += 4
#   call <stdcall n>  => net esp += 4*n
#        reason: call itself pushes retaddr (-4) and the callee pops args AND retaddr
#        (+4+4n), so -4+(4+4n) = 4n. The return address CANCELS; it is not an extra arg.
#   call cdecl/unknown => net 0
# Error 1 (r131g): push was given +4 (sign inverted).
# Error 2 (first r131q): call was given 4*(n+1), double-counting the return address,
#   which pushed 0x6bedf8 / 0x6bee09 out to E0+0x10 ("above-args") -- impossible for a
#   ret-0xc function, which is exactly the smell that should have caught it.
#
# The pop counts are not assumed either: n is DERIVED by counting the pushes in the
# straight-line run before each call, and the result must make the model consistent at
# every merge point (independent check d1).
md.detail = True
ins = {}
for insn in md.disasm(data[FN - tlo:FN - tlo + 0x100], FN):
    ins[insn.address] = insn
addrs = sorted(ins)


def solve(pops):
    """Propagate esp given {call_va: net_esp_delta}. Return (esp_map, conflicts)."""
    esp = {FN: 0}
    work = [FN]
    conf = []
    while work:
        a = work.pop()
        i = ins[a]
        mn = i.mnemonic
        if mn == 'push':
            delta = -4
        elif mn == 'pop':
            delta = 4
        elif mn == 'ret':
            delta = 4 + (int(i.op_str, 16) if i.op_str else 0)
        elif mn == 'call':
            delta = pops.get(a, 0)
        else:
            delta = 0
        out = esp[a] + delta
        if mn.startswith('j'):
            tgts = [o.imm for o in i.operands if o.type == 2]
            k = addrs.index(a)
            fall = addrs[k + 1] if k + 1 < len(addrs) else None
            nxt = [t for t in tgts if t in ins]
            if mn != 'jmp' and fall in ins:
                nxt.append(fall)
        elif mn == 'ret':
            nxt = []
        else:
            k = addrs.index(a)
            fall = addrs[k + 1] if k + 1 < len(addrs) else None
            nxt = [fall] if fall in ins else []
        for s_ in nxt:
            if s_ in esp:
                if esp[s_] != out:
                    conf.append((hex(a), hex(s_), esp[s_], out))
            else:
                esp[s_] = out
                work.append(s_)
    return esp, conf


# --- (d1) force all call deltas to 0 (i.e. treat every callee as cdecl) ---
_, conf0 = solve({})
R['d1_conflicts_with_all_call_deltas_zero'] = conf0
chk('(d1) treating every callee as cdecl makes the model inconsistent, and the conflicts '
    'name exactly the two COM calls that do pop', len(conf0) == 2,
    [c[0] + '->' + c[1] for c in conf0])

# --- (d2) derive the net delta = 4 * (number of pushes before the call) ---
def pushes_before(call_va):
    k = addrs.index(call_va)
    n = 0
    j = k - 1
    while j >= 0:
        i = ins[addrs[j]]
        if i.mnemonic == 'push':
            n += 1
        elif i.mnemonic.startswith('j') or i.mnemonic == 'call':
            break
        j -= 1
    return n


CALLS = [0x6bedbd, 0x6beddd, 0x6bedec, 0x6bee05, 0x6bee10, 0x6bee2b]
imp_by_va = {}
for e in getattr(pe, 'DIRECTORY_ENTRY_IMPORT', []):
    for im in e.imports:
        if im.address:
            imp_by_va[im.address] = (e.dll.decode(errors='replace'),
                                     im.name.decode() if im.name else '#%d' % im.ordinal)

derived = {}
detail_d2 = []
for c in CALLS:
    i = ins[c]
    n_push = pushes_before(c)
    if i.operands and i.operands[0].type == 3 and i.reg_name(i.operands[0].mem.base) == '':
        name = imp_by_va.get(i.operands[0].mem.disp, ('?', '?'))[1]
    else:
        name = i.op_str
    derived[c] = 4 * n_push
    detail_d2.append({'call': hex(c), 'pushes_before': n_push, 'nargs': n_push,
                      'derived_net_delta': 4 * n_push, 'target': name})
R['d2_derived'] = detail_d2
print('--- (d2) net esp delta derived from the push count (delta = 4 * nargs) ---')
for d in detail_d2:
    print('   %-10s nargs=%-2d net_delta=%-3d target=%s'
          % (d['call'], d['nargs'], d['derived_net_delta'], d['target']))

chk('(d2) CoCreateInstance is called with 5 args -> delta 20', derived[0x6beddd] == 20,
    derived[0x6beddd])
chk('(d2) OleRun is called with 1 arg -> delta 4', derived[0x6bedec] == 4, derived[0x6bedec])
chk('(d2) the QI-shaped indirect call has 3 args -> delta 12', derived[0x6bee05] == 12,
    derived[0x6bee05])
chk('(d2) both Release-shaped indirect calls have 1 arg -> delta 4',
    derived[0x6bedbd] == 4 and derived[0x6bee10] == 4,
    (derived[0x6bedbd], derived[0x6bee10]))

# --- the model must now be self-consistent ---
esp, conflict = solve(derived)
R['esp_conflicts'] = conflict
chk('using the derived deltas the model is consistent at every merge point',
    not conflict, conflict)


def slot(n):
    if n == 0:
        return 'retaddr'
    if n >= 4 and (n - 4) % 4 == 0 and n <= 0xc:
        return 'arg%d' % ((n - 4) // 4 + 1)
    if n > 0xc:
        return 'above-args@%d' % n
    return 'local@%d' % n


rows = []
for a in addrs:
    i = ins[a]
    for o in i.operands:
        if o.type == 3 and i.reg_name(o.mem.base) == 'esp' and a in esp:
            rel = esp[a] + o.mem.disp
            rows.append({'va': hex(a), 'op': i.mnemonic + ' ' + i.op_str,
                         'esp_rel': esp[a], 'E0': rel, 'slot': slot(rel)})
R['stack_model'] = rows
print('--- [esp+N] resolved (E0 = esp on entry, ret 0xc => exactly 3 stack args) ---')
for r in rows:
    print('   %-10s %-34s esp=%-4d E0+%-4d %s'
          % (r['va'], r['op'], r['esp_rel'], r['E0'], r['slot']))

by_va = {r['va']: r for r in rows}
chk('0x6bedc0 reads arg3 (the CLSCTX word tested by test al,0x14)',
    by_va['0x6bedc0']['E0'] == 0xc, by_va['0x6bedc0'])
chk('0x6bedc8 reads arg1 -> becomes the CoCreateInstance rclsid',
    by_va['0x6bedc8']['E0'] == 4, by_va['0x6bedc8'])
chk('0x6bedcc takes &(the arg2 stack slot) as the ppv out-slot',
    by_va['0x6bedcc']['E0'] == 8, by_va['0x6bedcc'])
chk('0x6bedd7 reads arg2 -> becomes CoCreateInstance pUnkOuter (SAME slot as ppv)',
    by_va['0x6bedd7']['E0'] == 8, by_va['0x6bedd7'])
chk('0x6bede7 / 0x6bedf8 / 0x6bee09 read the arg2 slot = the created interface pointer',
    by_va['0x6bede7']['E0'] == 8 and by_va['0x6bedf8']['E0'] == 8
    and by_va['0x6bee09']['E0'] == 8,
    (by_va['0x6bede7']['E0'], by_va['0x6bedf8']['E0'], by_va['0x6bee09']['E0']))
chk('0x6bee1a (the ole-run bypass path) reads the same arg1',
    by_va['0x6bee1a']['E0'] == 4, by_va['0x6bee1a'])
chk('no [esp+N] read resolves outside the three stack args',
    all(r['E0'] in (4, 8, 0xc) for r in rows),
    [r['va'] + '=E0+' + str(r['E0']) for r in rows if r['E0'] not in (4, 8, 0xc)])

# negative control: force the two indirect COM calls back to cdecl and require a conflict
_, conf_bad = solve({k: v for k, v in derived.items() if k not in (0x6bee05, 0x6bedbd, 0x6bee10)})
R['negctl_cdecl_on_com_calls'] = conf_bad
chk('negative control: declaring those calls cdecl makes the model inconsistent again',
    bool(conf_bad), [c[0] + '->' + c[1] for c in conf_bad])

chk('wrapper ends in ret 0xc (3 stack arguments)',
    ins[0x6bee17].op_str == '0xc' and ins[0x6bee35].op_str == '0xc',
    (ins[0x6bee17].op_str, ins[0x6bee35].op_str))
chk('branch constant is test al,0x14 / je 0x6bee1a (hy4)',
    ins[0x6bedc4].op_str == 'al, 0x14' and ins[0x6bedc6].op_str == '0x6bee1a',
    (ins[0x6bedc4].op_str, ins[0x6bedc6].op_str))
chk('indirect calls are [ecx] and [edx+8] (hy4 + R130)',
    ins[0x6bee05].op_str == 'dword ptr [ecx]' and ins[0x6bee10].op_str == 'dword ptr [edx + 8]',
    (ins[0x6bee05].op_str, ins[0x6bee10].op_str))
chk('0x6bee03 mov ecx,[eax]: ecx is loaded with the VTABLE, so the callee is vtable[0]',
    ins[0x6bee03].op_str == 'ecx, dword ptr [eax]', ins[0x6bee03].op_str)
chk('prologue 0x6bedb4/0x6bedbd reads and then releases the pointer stored at *this',
    ins[0x6bedb4].op_str == 'eax, dword ptr [edi]'
    and ins[0x6bedbd].op_str == 'dword ptr [ecx + 8]',
    (ins[0x6bedb4].op_str, ins[0x6bedbd].op_str))

# ---------- 5. call-site pushes (hy4 TASK1) ----------
site = {}
k = addrs.index(0x6bc357) if 0x6bc357 in ins else None
md4 = Cs(CS_ARCH_X86, CS_MODE_32)
win = []
for i in md4.disasm(data[0x6bc342 - tlo:0x6bc342 - tlo + 0x2a], 0x6bc342):
    win.append('%08x %-20s %s %s' % (i.address, i.bytes.hex(), i.mnemonic, i.op_str))
R['loop_window'] = win
chk('loop call site pushes 7 then 0 then [esi] (hy4)',
    any('push 7' in w for w in win) and any('push 0' in w for w in win)
    and any('push edx' in w for w in win)
    and any('mov edx, dword ptr [esi]' in w for w in win), win[3:9])
chk('loop this for the wrapper is lea ecx,[ebp - 0xa3c] (hy4)',
    any('lea ecx, [ebp - 0xa3c]' in w for w in win),
    [w for w in win if 'lea' in w])
chk('the rclsid pushed is [esi] where esi starts at 0x7f3710 (table head)',
    any('mov esi, 0x7f3710' in w for w in win), win[0])

R['assertions'] = A
R['summary'] = {'total': len(A), 'pass': sum(1 for x in A if x['ok']),
                'fail': [x['assert'] for x in A if not x['ok']]}
print('\nASSERTIONS: %d total, %d pass, %d fail'
      % (R['summary']['total'], R['summary']['pass'], len(R['summary']['fail'])))
json.dump(R, open(OUT, 'w'), ensure_ascii=False, indent=1)
raise SystemExit(1 if R['summary']['fail'] else 0)
