#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
R133 exec (deepseek family) — independent cross-check of the push tails and of the
direct call-site census, using GNU binutils objdump instead of capstone.

Rationale: r133_sub_deepseek_callers.py answers (1)(2)(3) with capstone. If capstone's
linear sweep or its decoding of a push tail were subtly wrong, the primary result would
be self-consistent but wrong. objdump is an unrelated decoder; agreement between the
two is real corroboration, not a restatement.

This script:
  A. runs `i686-w64-mingw32-objdump -d` over the image and parses the instruction
     stream, then re-derives the direct E8/E9 call-site census from THAT stream
     (independent of the byte-arithmetic scan in the primary script);
  B. for each site, walks objdump's own instruction list backwards to collect the
     last three `push` instructions and compares the signature with the primary
     script's JSON;
  C. re-runs the imm32 search with a different mechanism (mmap + bytes.find, not re).

objdump stops at undecodable bytes and emits `.byte` pseudo-instructions; those are
treated as stream breaks and never as instructions.
"""
import json, re, subprocess, sys, mmap, os

EXE = '/home/t628/projects/ra2-campaign-forge/ra2bench/gamemd.exe'
PRIMARY = '/home/t628/projects/ra2-campaign-forge/_r133/sub_deepseek/r133_sub_deepseek_callers.json'
OUT = '/home/t628/projects/ra2-campaign-forge/_r133/sub_deepseek/r133_sub_deepseek_xcheck.json'
OBJDUMP = 'i686-w64-mingw32-objdump'

res = {'asserts': []}


def chk(name, cond, detail=''):
    ok = bool(cond)
    res['asserts'].append({'assert': name, 'pass': ok, 'detail': str(detail)})
    print(('  PASS ' if ok else '  FAIL ') + name + (('  [' + str(detail) + ']') if detail else ''))
    return ok


prim = json.load(open(PRIMARY))
prim_sites = {s['site']: s for s in prim['sites']}

print('[objdump] disassembling %s' % EXE)
p = subprocess.run([OBJDUMP, '-d', '--no-show-raw-insn', EXE],
                   capture_output=True, text=True, timeout=900)
if p.returncode != 0:
    print('objdump failed:', p.stderr[:2000]); sys.exit(2)
lines = p.stdout.splitlines()
print('[objdump] %d output lines' % len(lines))

# Parse: "  6bc364:\te8 47 2a 00 00\tcall   0x6bedb0"  (with --no-show-raw-insn the
# raw bytes column is gone, leaving "addr:\tmnemonic operands")
LINE = re.compile(r'^\s*([0-9a-f]+):\t(.*)$')
insns = []           # (addr, text)
for ln in lines:
    m = LINE.match(ln)
    if not m:
        continue
    a = int(m.group(1), 16)
    txt = m.group(2).strip()
    insns.append((a, txt))
print('[objdump] parsed %d instructions' % len(insns))

if insns != sorted(insns):
    print('[warn] objdump output not strictly ascending; sorting')
    insns.sort()

# objdump renders comments like "call 0x45af20 <...>"; strip <...> and comments
def norm(t):
    t = re.sub(r'<[^>]*>', '', t)
    t = re.sub(r'#.*$', '', t)
    return ' '.join(t.split())

index = {a: i for i, (a, _) in enumerate(insns)}

# ---- A. call-site census from objdump's stream
TARGETS = [0x6bedb0, 0x41c250]
obj_calls = {t: [] for t in TARGETS}
for a, txt in insns:
    t = norm(txt)
    if not (t.startswith('call') or t.startswith('jmp')):
        continue
    mm = re.search(r'\$?(0x[0-9a-f]+)$', t.split(',')[-1].strip())
    if not mm:
        continue
    try:
        tgt = int(mm.group(1), 16)
    except ValueError:
        continue
    if tgt in obj_calls:
        obj_calls[tgt].append(a)

res['objdump_calls'] = {hex(k): [hex(x) for x in v] for k, v in obj_calls.items()}
for t in TARGETS:
    print('[objdump] direct -> %#x : %d  %s' % (t, len(obj_calls[t]),
                                                [hex(x) for x in obj_calls[t]]))
    prim_list = [int(g['addr'], 16) for g in prim['direct_verified'][hex(t)]]
    chk('A: objdump and capstone agree on the site SET for %#x' % t,
        sorted(obj_calls[t]) == sorted(prim_list),
        {'objdump': [hex(x) for x in obj_calls[t]], 'capstone': [hex(x) for x in prim_list]})
    chk('A: objdump count for %#x == capstone count' % t,
        len(obj_calls[t]) == len(prim_list), (len(obj_calls[t]), len(prim_list)))

# ---- B. push tails from objdump's instruction list
CTRLWORDS = ('ret', 'retf', 'iret', 'jmp', 'call', 'ljmp', 'lcall', 'int', 'int3',
             'hlt', 'ud2', 'ud0', 'ud1', 'loop', 'loope', 'loopne')


def is_ctrl(t):
    w = t.split()[0] if t.split() else ''
    return w in CTRLWORDS or w.startswith('j')


res['objdump_sites'] = []
for site_hex, rec in prim_sites.items():
    a = int(site_hex, 16)
    i = index.get(a)
    if i is None:
        chk('B: objdump has an instruction at site %s' % site_hex, False)
        continue
    pushes = []
    j = i - 1
    while j >= 0:
        t = norm(insns[j][1])
        if is_ctrl(t):
            break
        if t.split() and t.split()[0] == 'push':
            pushes.append((insns[j][0], t))
            if len(pushes) == 3:
                break
        j -= 1
    pushes.reverse()
    sig = [t for _, t in pushes]
    prim_sig = [p['asm'] for p in rec['pushes']]
    res['objdump_sites'].append({'site': site_hex, 'objdump_pushes': sig,
                                 'capstone_pushes': prim_sig,
                                 'push_addrs_objdump': [hex(x) for x, _ in pushes],
                                 'push_addrs_capstone': [p['addr'] for p in rec['pushes']]})
    print('[objdump] %s: %s' % (site_hex, sig))
    chk('B: objdump and capstone agree on the 3-push signature at %s' % site_hex,
        sig == prim_sig, {'objdump': sig, 'capstone': prim_sig})
    chk('B: objdump and capstone agree on each push ADDRESS at %s' % site_hex,
        [hex(x) for x, _ in pushes] == [p['addr'] for p in rec['pushes']],
        ([hex(x) for x, _ in pushes], [p['addr'] for p in rec['pushes']]))

# ---- C. imm32 search with a different mechanism (find, not regex)
res['imm32_find'] = {}
with open(EXE, 'rb') as f:
    mm = mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ)
    import struct as _s
    for t in TARGETS:
        for form, val in (('VA', t), ('RVA', t - prim['image_base'])):
            pat = _s.pack('<I', val)
            offs, pos = [], 0
            while True:
                pos = mm.find(pat, pos)
                if pos < 0:
                    break
                offs.append(pos)
                pos += 1
            res['imm32_find'].setdefault(hex(t), {})[form] = [hex(x) for x in offs]
            prim_off = [o['file_off'] for o in prim['imm32'][hex(t)][form]]
            print('[find] %#x %s: %d hits %s' % (t, form, len(offs), [hex(x) for x in offs]))
            chk('C: mmap find and regex agree on %#x %s hit offsets' % (t, form),
                [hex(x) for x in offs] == prim_off,
                {'find': [hex(x) for x in offs], 'regex': prim_off})
    mm.close()

res['asserts_pass'] = sum(1 for a in res['asserts'] if a['pass'])
res['asserts_total'] = len(res['asserts'])
json.dump(res, open(OUT, 'w'), indent=1)
print('\n[written] ' + OUT)
print('[final] cross-check asserts %d/%d -> %s' % (
    res['asserts_pass'], res['asserts_total'],
    'OK' if res['asserts_pass'] == res['asserts_total'] else 'FAILED'))
sys.exit(0 if res['asserts_pass'] == res['asserts_total'] else 1)
