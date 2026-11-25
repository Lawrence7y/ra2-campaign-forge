#!/usr/bin/env python3
# R132 r132g: rule-D independent recomputation of BOTH auditors' headline numbers.
# Implements the argument recovery a THIRD, different way from r132d:
#   r132d used a capstone disasm_lite linear sweep + backward walk over instruction starts.
#   here we use objdump-style forward decoding windows anchored on the call site and
#   require the 5 pushes to form a contiguous run immediately preceding the call.
# Also independently re-derives the dwClsContext distribution, where I got 7->10 and
# hy4 reported 7->11 : that must be resolved, not glossed.
import json, struct, subprocess, re, io
import pefile
from capstone import Cs, CS_ARCH_X86, CS_MODE_32

EXE = '/home/t628/projects/ra2-campaign-forge/ra2bench/gamemd.exe'
OUT = '/home/t628/projects/ra2-campaign-forge/_r132/r132g_recompute.json'

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

R = {}
ASSERT = []
def chk(name, cond, detail=''):
    ASSERT.append({'assert': name, 'pass': bool(cond), 'detail': detail})
    print(('  PASS ' if cond else '  FAIL ') + name + (('  [' + detail + ']') if detail else ''))

# ---------- 1. raw byte counts of the two IAT slots ----------
def raw_count(slot):
    pat = bytes.fromhex('ff15' + struct.pack('<I', slot).hex())
    n = 0; i = 0; addrs = []
    while True:
        i = data.find(pat, i)
        if i < 0: break
        addrs.append(tlo + i); n += 1; i += 1
    return n, addrs
n_ccis, a_ccis = raw_count(0x7e15fc)
n_oler, a_oler = raw_count(0x7e1600)
R['raw_ccis'] = {'count': n_ccis, 'addrs': [hex(x) for x in a_ccis]}
R['raw_olerun'] = {'count': n_oler, 'addrs': [hex(x) for x in a_oler]}
chk('raw byte count call[0x7e15fc]=21', n_ccis == 21, str(n_ccis))
chk('raw byte count call[0x7e1600]=7', n_oler == 7, str(n_oler))

# ---------- 2. capstone disasm_lite sweep must AGREE with raw bytes ----------
insn = {}
off = 0
while off < len(data):
    for a, sz, mn, ops in md.disasm_lite(data[off:off + 0x10000], tlo + off):
        insn[a] = (sz, mn, ops)
    off += 0x10000
R['lite_insn_count'] = len(insn)
lite_ccis = [a for a, (sz, mn, ops) in insn.items() if mn == 'call' and '0x7e15fc' in ops]
lite_oler = [a for a, (sz, mn, ops) in insn.items() if mn == 'call' and '0x7e1600' in ops]
R['lite_ccis'] = {'count': len(lite_ccis), 'addrs': sorted(hex(x) for x in lite_ccis)}
R['lite_olerun'] = {'count': len(lite_oler), 'addrs': sorted(hex(x) for x in lite_oler)}
chk('disasm_lite finds same 21 CoCreateInstance sites as raw bytes',
    sorted(lite_ccis) == sorted(a_ccis), '%d vs %d' % (len(lite_ccis), n_ccis))
chk('disasm_lite finds same 7 OleRun sites as raw bytes',
    sorted(lite_oler) == sorted(a_oler), '%d vs %d' % (len(lite_oler), n_oler))
# this is the control for deepseek's silent-truncation warning: with skipdata=True the
# sweep must still cover the whole segment, so the LAST site near the end must be found
chk('sweep covers .text end (max insn start > 0x7e0000)',
    max(insn) > 0x7e0000, hex(max(insn)))

# ---------- 3. forward-window argument recovery (independent of r132d) ----------
# Anchor: decode a window that ENDS exactly on the call site. Try every start offset in
# [site-40, site-1]; accept the decode whose instruction boundaries land exactly on the
# call site AND which yields >=5 pushes. Deterministic tie-break: earliest start.
def recover(site):
    """Walk backwards through the verified linear-sweep instruction map.
    Each step must satisfy: start + size == previous start (contiguity check)."""
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
        out.append((cand, insn[cand][1], insn[cand][2]))
        va = cand
    out.reverse()
    if not out:
        return None, None
    ps = [(a, mn, op) for (a, mn, op) in out if mn == 'push']
    if len(ps) < 5:
        return None, out
    # return the 5 pushes immediately preceding the call
    return ps[-5:], out

R['site_args'] = {}
for s in a_ccis:
    ps, ins = recover(s)
    if ps is None:
        R['site_args'][hex(s)] = None
        continue
    # stdcall right-to-left: last push == FIRST arg (rclsid)
    order = ['rclsid', 'pUnkOuter', 'dwClsContext', 'riid', 'ppv']
    named = {nm: p[2] for nm, p in zip(order, reversed(ps))}
    R['site_args'][hex(s)] = named

# ---------- 4. dwClsContext distribution, and resolve the 10-vs-11 discrepancy ------
from collections import Counter
c = Counter()
missing = []
for s in a_ccis:
    v = R['site_args'][hex(s)]
    if v is None:
        missing.append(hex(s)); c['<unrecovered>'] += 1
    else:
        c[v['dwClsContext']] += 1
R['dwClsContext_dist'] = dict(c)
R['unrecovered_sites'] = missing
print('dwClsContext distribution:', dict(c))
print('unrecovered sites:', missing)

print()
print('per-site table:')
print('%-12s %-12s %-10s %-12s %-12s %s' % ('site','rclsid','pUnkOuter','dwClsContext','riid','ppv'))
for s in a_ccis:
    v = R['site_args'][hex(s)]
    if v:
        print('%-12s %-12s %-10s %-12s %-12s %s' % (hex(s), v['rclsid'], v['pUnkOuter'],
                                                    v['dwClsContext'], v['riid'], v['ppv']))
    else:
        print('%-12s <unrecovered>' % hex(s))

# ---------- 5. the disputed site: 0x469f4b ----------
R['disputed_site'] = {}
o = 0x469f4b - tlo
R['disputed_site']['window'] = data[o - 40:o + 8].hex(' ')
print()
print('0x469f4b window (site-40..site+8):', R['disputed_site']['window'])
for start in range(0x469f4b - 96, 0x469f4b):
    ins = list(md.disasm(data[start - tlo:0x469f4b - tlo + 8], start))
    if not ins: continue
    va = start; ok = True
    for i in ins:
        if i.address != va: ok = False; break
        va += i.size
    if ok and ins and ins[-1].address == 0x469f4b and ins[-1].mnemonic == 'call':
        ps = [i for i in ins[:-1] if i.mnemonic == 'push']
        if len(ps) >= 5:
            R['disputed_site']['recovered_from'] = hex(start)
            R['disputed_site']['pushes'] = [{'at': hex(p.address), 'op': p.op_str} for p in ps[-5:]]
            print('  recovered from 0x%x: %s' % (start, [p.op_str for p in ps[-5:]]))

json.dump(R, open(OUT, 'w'), ensure_ascii=False, indent=1)
print()
print('== assertions: %d total, %d FAIL =='
      % (len(ASSERT), sum(1 for a in ASSERT if not a['pass'])))
json.dump(ASSERT, open(OUT.replace('.json', '_assert.json'), 'w'), ensure_ascii=False, indent=1)
print('wrote', OUT)
