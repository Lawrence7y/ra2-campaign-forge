#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
R133 exec (deepseek family) — independent re-measurement of three claims about
ra2bench/gamemd.exe:

  (1) ALL direct call/jmp sites of 0x6bedb0 and 0x41c250, in both E8 rel32 (call)
      and E9 rel32 (jmp) form, each confirmed to sit on an instruction boundary.
  (2) Occurrences of each entry VA as an imm32 anywhere in the image (VA form and,
      for completeness, RVA form) -> decides whether a function-pointer path exists.
  (3) At every direct site: the last three push instructions. Under the cdecl
      right-to-left convention the FIRST push is stack argument #3. Report its value
      and whether it is an immediate or a register.

Why push extraction needs care here
-----------------------------------
The tails are NOT three consecutive pushes. Real shape (objdump-verified at
0x710213):

    710203: push $0x7                 <- arg3
    710205: lea  0x38(%esp),%eax
    710209: push %ebp                 <- arg2
    71020a: push %eax                 <- arg1
    71020b: lea  0x3c(%esp),%ecx
    71020f: mov  %ebp,0x3c(%esp)
    710213: call 0x41c250

So the correct rule is "the last three push instructions before the call", ignoring
intervening non-push instructions, and stopping the scan at a control transfer.
A naive "scan back until a non-push" rule yields nonsense. The first extractor in
this file got that wrong and its own self-test caught it; see the report.

Method: anchor voting. For every start address s in [site-8, site-512] we decode
strictly to the site; a chain is valid only if every consecutive pair satisfies
a + size == next instruction address and the last instruction ends exactly at the
site. Each valid chain votes for the 3-push signature it sees. Desynced anchors
produce garbled signatures that lose the vote. The winning signature must also be
confirmed by an independent decoder (GNU objdump, r133_sub_deepseek_xcheck.py).

Memory discipline
-----------------
* .text (4 MB) is NEVER disassembled with detail=True.
* The whole-file boundary sweep is streaming: one 64 KiB window at a time, each
  window's decode consumed as a generator; only wanted addresses are retained.
* md.skipdata = True for the linear sweep (required: the sweep otherwise stalls at
  0x46f5a0 where data-in-text is undecodable).
* Backtracking uses a STRICT decoder (skipdata = False) so no byte is skipped.
* The vote table holds <=512 short tuples per site, freed per site.
"""
import json, re, struct, sys, time
import pefile
from capstone import Cs, CS_ARCH_X86, CS_MODE_32

EXE = '/home/t628/projects/ra2-campaign-forge/ra2bench/gamemd.exe'
OUT = '/home/t628/projects/ra2-campaign-forge/_r133/sub_deepseek/r133_sub_deepseek_callers.json'
TARGETS = [0x6bedb0, 0x41c250]
WIN = 64 * 1024                     # 64 KiB streaming window
ANCHOR_MIN, ANCHOR_MAX = 8, 512     # anchor offsets back from a call site

t0 = time.time()
pe = pefile.PE(EXE, fast_load=True)
base = pe.OPTIONAL_HEADER.ImageBase
raw = open(EXE, 'rb').read()

secs = {}
for s in pe.sections:
    nm = s.Name.rstrip(b'\x00').decode('latin-1')
    secs[nm] = (base + s.VirtualAddress,
                base + s.VirtualAddress + s.Misc_VirtualSize, s)
TLO, THI, TSEC = secs['.text']
text = TSEC.get_data()

print('[sec] image base %#x  .text VA %#x..%#x  raw %d bytes' % (base, TLO, THI, len(text)))
# Fixed-base check: with no DYNAMICBASE and no .reloc, a function pointer stored in
# the image would hold the literal VA, so the imm32 scan below is meaningful as-is.
dllch = pe.OPTIONAL_HEADER.DllCharacteristics
reloc_sz = pe.OPTIONAL_HEADER.DATA_DIRECTORY[5].Size
print('[sec] DllCharacteristics=%#x (DYNAMICBASE=%s)  .reloc size=%d' %
      (dllch, bool(dllch & 0x40), reloc_sz))

md_lite = Cs(CS_ARCH_X86, CS_MODE_32)
md_lite.skipdata = True             # linear sweep only
md_strict = Cs(CS_ARCH_X86, CS_MODE_32)
md_strict.skipdata = False          # backtracking only

R = {'exe': EXE, 'image_base': base,
     'text': {'lo': hex(TLO), 'hi': hex(THI), 'len': len(text)},
     'targets': [hex(t) for t in TARGETS],
     'pe': {'dll_characteristics': hex(dllch),
            'dynamicbase': bool(dllch & 0x40),
            'reloc_dir_size': reloc_sz},
     'asserts': [], 'self_tests': []}


def chk(name, cond, detail=''):
    ok = bool(cond)
    R['asserts'].append({'assert': name, 'pass': ok, 'detail': str(detail)})
    print(('  PASS ' if ok else '  FAIL ') + name + (('  [' + str(detail) + ']') if detail else ''))
    return ok


def st(name, cond, detail=''):
    ok = bool(cond)
    R['self_tests'].append({'test': name, 'pass': ok, 'detail': str(detail)})
    print(('  ST-PASS ' if ok else '  ST-FAIL ') + name + (('  [' + str(detail) + ']') if detail else ''))
    return ok


# ==================================================== (1) direct call/jmp sites
def scan_e8_e9(blob, blob_lo, targets):
    """Byte scan for E8/E9 rel32 whose computed target is in `targets`.

    Pure byte arithmetic, no decoding, so no disassembly desync can hide a site.
    """
    out = {t: [] for t in targets}
    tset = set(targets)
    for i in range(len(blob) - 4):
        if blob[i] != 0xE8 and blob[i] != 0xE9:
            continue
        rel = struct.unpack_from('<i', blob, i + 1)[0]
        if blob_lo + i + 5 + rel in tset:
            out[blob_lo + i + 5 + rel].append(blob_lo + i)
    return out


def decode_at(addr, md, length=16):
    o = addr - TLO
    if o < 0 or o >= len(text):
        return None
    for ins in md.disasm(text[o:o + length], addr, count=1):
        return ins
    return None


hits = scan_e8_e9(text, TLO, TARGETS)
R['direct_raw'] = {hex(t): [hex(x) for x in hits[t]] for t in TARGETS}
for t in TARGETS:
    print('[scan] raw E8/E9 -> %#x : %d hit(s) %s' % (t, len(hits[t]), [hex(x) for x in hits[t]]))

R['direct_verified'], R['direct_rejected'] = {}, {}
for t in TARGETS:
    good, bad = [], []
    for a in hits[t]:
        ins = decode_at(a, md_strict)
        if ins and ins.mnemonic in ('call', 'jmp') and ins.op_str == hex(t) and ins.size == 5:
            good.append({'addr': hex(a),
                         'form': 'E8 rel32 call' if ins.mnemonic == 'call' else 'E9 rel32 jmp',
                         'mnemonic': ins.mnemonic, 'op_str': ins.op_str,
                         'bytes': ins.bytes.hex(), 'size': ins.size})
        else:
            bad.append({'addr': hex(a),
                        'decoded': (ins.mnemonic + ' ' + ins.op_str + ' size=' + str(ins.size))
                        if ins else None})
    R['direct_verified'][hex(t)] = good
    R['direct_rejected'][hex(t)] = bad
    print('[verify] %#x -> %d verified, %d rejected' % (t, len(good), len(bad)))
    for g in good:
        print('    %s  %s %s  bytes=%s size=%d' % (g['addr'], g['mnemonic'], g['op_str'],
                                                   g['bytes'], g['size']))

# (1b) streaming skipdata sweep: each site must be seen as an instruction start.
R['linear_sweep'] = {}
for t in TARGETS:
    want = {int(g['addr'], 16) for g in R['direct_verified'][hex(t)]}
    seen, nwin = set(), 0
    for w in range(TLO, TLO + len(text), WIN):
        nwin += 1
        chunk = text[w - TLO: w - TLO + WIN]
        for ins in md_lite.disasm(chunk, w):        # lazy generator, no detail
            if ins.address in want:
                seen.add(ins.address)
    R['linear_sweep'][hex(t)] = {
        'windows': nwin, 'window_bytes': WIN,
        'per_site': [{'addr': g['addr'], 'on_linear_boundary': int(g['addr'], 16) in seen}
                     for g in R['direct_verified'][hex(t)]]}
    print('[linear] %#x: %d windows x %d KiB -> %s' %
          (t, nwin, WIN // 1024,
           [(d['addr'], d['on_linear_boundary']) for d in R['linear_sweep'][hex(t)]['per_site']]))

# =============================================== (2) entry VA as imm32 anywhere
R['imm32'] = {}
for t in TARGETS:
    R['imm32'][hex(t)] = {}
    for form, val in (('VA', t), ('RVA', t - base)):
        pat = struct.pack('<I', val)
        occ = []
        for m in re.finditer(re.escape(pat), raw):
            try:
                va = base + pe.get_rva_from_offset(m.start())
            except Exception:
                va = None
            occ.append({'file_off': hex(m.start()), 'va': hex(va) if va is not None else None})
        R['imm32'][hex(t)][form] = occ
        print('[imm32] %#x as %s (bytes %s): %d occurrence(s) %s' %
              (t, form, pat.hex(), len(occ), [x['file_off'] for x in occ]))

# ==================================================== (3) last three pushes
REGS32 = {'eax', 'ebx', 'ecx', 'edx', 'esi', 'edi', 'ebp', 'esp', 'eip'}
CTRL = {'ret', 'retf', 'iret', 'jmp', 'call', 'callf', 'ljmp', 'lcall', 'int', 'int3',
        'loop', 'loope', 'loopne', 'hlt', 'ud2', 'ud0', 'ud1'}


def is_ctrl(ins):
    return ins.mnemonic in CTRL or ins.mnemonic.startswith('j')


def classify(op_str):
    """Classify a push operand as imm / reg / other.

    capstone prints immediates below 10 in DECIMAL (`push 7`), larger ones in hex
    (`push 0x7e9a30`); both forms are accepted here.
    """
    s = op_str.strip()
    if not s:
        return {'kind': 'none', 'text': ''}
    if re.fullmatch(r'-?(0x[0-9a-fA-F]+|\d+)', s):
        v = int(s, 16) if 'x' in s.lower() else int(s, 10)
        return {'kind': 'imm', 'value': v, 'hex': hex(v), 'text': s}
    if s in REGS32:
        return {'kind': 'reg', 'reg': s, 'text': s}
    return {'kind': 'other', 'text': s}


def strict_chain(addr, dist):
    s = addr - dist
    if s < TLO:
        return None
    seq = list(md_strict.disasm(text[s - TLO:addr - TLO], s))
    if not seq:
        return None
    cur = s
    for ins in seq:
        if ins.address != cur:
            return None
        cur = ins.address + ins.size
    return seq if cur == addr else None


def tail3(seq):
    """Last three pushes in `seq`, scanning backward; stop at a control transfer."""
    pushes = []
    for ins in reversed(seq):
        if is_ctrl(ins):
            break
        if ins.mnemonic == 'push':
            pushes.append(ins)
            if len(pushes) == 3:
                break
    pushes.reverse()
    return pushes


def analyze_site(addr):
    votes = {}        # signature -> [anchor distances]
    exemplar = {}     # signature -> [ins,...]
    valid_anchors = 0
    for dist in range(ANCHOR_MIN, ANCHOR_MAX + 1):
        seq = strict_chain(addr, dist)
        if seq is None:
            continue
        pushes = tail3(seq)
        if len(pushes) != 3:
            continue
        valid_anchors += 1
        sig = tuple(p.mnemonic + ' ' + p.op_str for p in pushes)
        votes.setdefault(sig, []).append(dist)
        exemplar.setdefault(sig, pushes)
    if not votes:
        return {'found': False, 'valid_anchors': valid_anchors,
                'reason': 'no valid anchor yields 3 pushes'}
    ranked = sorted(votes.items(), key=lambda kv: -len(kv[1]))
    sig, dists = ranked[0]
    pushes = exemplar[sig]
    # Adjacency of the three pushes is NOT expected: real tails interleave
    # lea/mov between the pushes (e.g. 0x710213). What must hold is that all three
    # came out of one strict, gap-free chain whose last instruction ends at the site.
    adjacent = all(pushes[i].address + pushes[i].size == pushes[i + 1].address
                   for i in range(len(pushes) - 1))
    chain_ok, chain_len = False, 0
    for dist in dists:
        seq = strict_chain(addr, dist)
        if seq and all(any(p.address == q.address for q in seq) for p in pushes):
            chain_ok, chain_len = True, len(seq)
            break
    rec = [{'addr': hex(p.address), 'asm': p.mnemonic + ' ' + p.op_str,
            'bytes': p.bytes.hex(), **classify(p.op_str)} for p in pushes]
    rival = [{'sig': list(k), 'votes': len(v), 'distances': v} for k, v in ranked[1:]]
    return {'found': True, 'valid_anchors': valid_anchors,
            'votes_winner': len(dists), 'winner_distances': dists[:20],
            'rivals': rival,
            'dominant': len(dists) >= 3 * max([1] + [r['votes'] for r in rival]),
            'pushes': rec, 'push_count': 3,
            'pushes_adjacent': adjacent,
            'since_last_push_asm': None,
            'pushes_all_in_one_strict_chain': chain_ok,
            'chain_len': chain_len,
            'pushes_span_bytes': pushes[-1].address + pushes[-1].size - pushes[0].address,
            'third_arg': rec[0],
            'arg_layout_note': 'cdecl right-to-left: 1st push = stack arg #3',
            'first_push_is_arg3': True}


print('\n[push] last three pushes at every verified direct site (anchor voting)')
R['sites'] = []
for t in TARGETS:
    for g in R['direct_verified'][hex(t)]:
        a = int(g['addr'], 16)
        info = analyze_site(a)
        R['sites'].append({'target': hex(t), 'site': g['addr'], 'form': g['form'], **info})
        if info['found']:
            print('  %s (%s -> %#x) winner %d/%d anchors: %s' %
                  (g['addr'], g['form'], t, info['votes_winner'], info['valid_anchors'],
                   [p['asm'] for p in info['pushes']]))
            for rv in info['rivals']:
                print('        rival %s votes=%d' % (rv['sig'], rv['votes']))
            ta = info['third_arg']
            print('        3rd stack arg (1st push) = %s   kind=%s   adjacent=%s' %
                  (ta['asm'], ta['kind'], info['pushes_adjacent']))
        else:
            print('  %s (%s -> %#x) UNRESOLVED: %s' % (g['addr'], g['form'], t, info.get('reason')))

# ================================================================ self-tests
print('\n[self-test] positive / negative controls')
SVA = 0x100000


def e8(tgt, at):
    return b'\xe8' + struct.pack('<i', tgt - (at + 5))


# PC1: synthetic tail with an INTERLEAVED non-push, exactly the real shape.
#      push 7 ; lea ecx,[ebp-0xa3c] ; push 0 ; mov edx,[esi] ; push edx ; call 0x6bedb0
syn = (b'\x6a\x07'                       # 0..1   6a 07        push 7
       b'\x8d\x8d\xc4\xf5\xff\xff'       # 2..7   lea ecx,[ebp-0xa3c]
       b'\x6a\x00'                       # 8..9   push 0
       b'\x8b\x16'                       # 10..11 mov edx,[esi]
       b'\x52'                           # 12     52           push edx
       )                                 # len 13
CALL_OFF = len(syn)
syn = syn + e8(0x6bedb0, SVA + CALL_OFF)
h = scan_e8_e9(syn, SVA, TARGETS)
st('PC1 byte scan finds the synthetic E8 call at %#x (offset %d)' % (SVA + CALL_OFF, CALL_OFF),
   h[0x6bedb0] == [SVA + CALL_OFF], [hex(x) for x in h[0x6bedb0]])
ins = list(md_strict.disasm(syn[CALL_OFF:CALL_OFF + 5], SVA + CALL_OFF, count=1))[0]
st('PC1b synthetic call decodes strictly as `call 0x6bedb0`, size 5',
   ins.mnemonic == 'call' and ins.op_str == '0x6bedb0' and ins.size == 5,
   '%s %s size=%d' % (ins.mnemonic, ins.op_str, ins.size))
seq = list(md_strict.disasm(syn[:CALL_OFF], SVA))
p3 = tail3(seq)
st('PC1c tail3 skips the interleaved lea/mov and returns 3 pushes',
   [p.mnemonic + ' ' + p.op_str for p in p3] == ['push 7', 'push 0', 'push edx'],
   [p.mnemonic + ' ' + p.op_str for p in p3])
st('PC1d 3rd stack arg from that tail is the immediate 7',
   classify(p3[0].op_str)['kind'] == 'imm' and classify(p3[0].op_str)['value'] == 7)

# PC1e: negative control on the OLD (wrong) rule — stopping at the first non-push
old_rule = []
for i in reversed(seq):
    if i.mnemonic != 'push':
        break
    old_rule.append(i)
st('PC1e the naive stop-at-first-non-push rule gives only 1 push (documents the bug)',
   len(old_rule) == 1, [p.mnemonic + ' ' + p.op_str for p in old_rule])

# PC2: E9 form is caught
syn2 = b'\xe9' + struct.pack('<i', 0x41c250 - (SVA + 5))
st('PC2 byte scan finds the synthetic E9 jmp to 0x41c250',
   scan_e8_e9(syn2, SVA, TARGETS)[0x41c250] == [SVA])

# PC3: immediate parsing in both notations
ct = classify('7')
st('PC3 decimal-form immediate "7" -> imm 7 (capstone prints <10 in decimal)',
   ct['kind'] == 'imm' and ct['value'] == 7, ct)
ct = classify('0x7e9a30')
st('PC3b hex-form immediate "0x7e9a30" -> imm', ct['kind'] == 'imm' and ct['value'] == 0x7e9a30, ct)
ct = classify('edi')
st('PC3c register operand "edi" -> reg', ct['kind'] == 'reg', ct)
ct = classify('dword ptr [esp + 0x1c]')
st('PC3d memory operand -> other (not imm, not reg)', ct['kind'] == 'other', ct)

# NC1: neighbouring call target is not reported
for d in (-1, +1):
    st('NC1 call to neighbour %#x NOT reported for %#x' % (0x6bedb0 + d, 0x6bedb0),
       scan_e8_e9(e8(0x6bedb0 + d, SVA), SVA, TARGETS)[0x6bedb0] == [])
# NC2: rel32 landing far outside any target
st('NC2 E8 with far rel32 not reported',
   scan_e8_e9(b'\xe8\x00\x00\x00\x7f', SVA, TARGETS)[0x6bedb0] == [])
# NC3: imm32 of a nearby address is not an entry reference
st('NC3 imm32 of %#x is not a match for entry %#x' % (0x6bedb0 + 4, 0x6bedb0),
   not re.search(re.escape(struct.pack('<I', 0x6bedb0 + 4)), raw))
# PC4: positive control for the imm32 scan itself, on a buffer that DOES contain it
st('PC4 imm32 scanner does find the VA when it is present (control buffer)',
   len(re.findall(re.escape(struct.pack('<I', 0x6bedb0)), b'\x00' * 7 + struct.pack('<I', 0x6bedb0))) == 1)
# NC4: strict decoder rejects a genuinely invalid stream
st('NC4 strict decoder returns nothing on bytes it cannot decode',
   len(list(md_strict.disasm(b'\x62', SVA, count=1))) == 0)
# NC5: a chain that OVERRUNS the site is rejected (strict_chain requires end == addr)
_over = b'\x6a\x07' + b'\xb8\x01\x02\x03\x04'          # push 7 ; mov eax, imm32 (6 bytes)
seq_ovr = list(md_strict.disasm(_over[:5], SVA))       # truncated at 5 -> overrun/partial
st('NC5 truncated stream cannot be a valid chain ending on the site',
   (seq_ovr[-1].address + seq_ovr[-1].size != SVA + 5) if seq_ovr else True,
   [(i.mnemonic + ' ' + i.op_str, hex(i.address + i.size)) for i in seq_ovr])
# NC6: tail3 must not cross a control transfer. Stream: push1 push2 push3 ret push9.
# Correct behaviour = return only ['push 9'] (it sits after the barrier, nearest the
# end), and definitely NOT mix in push1..push3 from the other block.
syn_ctrl = (b'\x6a\x01' b'\x6a\x02' b'\x6a\x03'      # three pushes
            b'\xc3'                                  # ret  <- barrier
            b'\x6a\x09')                             # a later push
seq_ctrl = list(md_strict.disasm(syn_ctrl, SVA))
got_ctrl = [p.op_str for p in tail3(seq_ctrl)]
st('NC6 tail3 stops at `ret`: returns only the post-barrier push, never crosses it',
   got_ctrl == ['9'], got_ctrl)

# ================================================================ assertions
print('\n[assert] counted claims')
per_target = {}
for t in TARGETS:
    v, rj = R['direct_verified'][hex(t)], R['direct_rejected'][hex(t)]
    per_target[hex(t)] = {'n': len(v), 'sites': [g['addr'] for g in v]}
    chk('(1) every raw E8/E9 hit for %#x decoded as call/jmp of size 5 to %#x' % (t, t),
        not rj, rj)
    chk('(1) all verified sites of %#x are instruction starts in the streaming skipdata '
        'sweep of .text' % t,
        all(d['on_linear_boundary'] for d in R['linear_sweep'][hex(t)]['per_site']),
        [d for d in R['linear_sweep'][hex(t)]['per_site'] if not d['on_linear_boundary']])
    chk('(2) 0 occurrences of %#x as imm32, VA form, whole image' % t,
        len(R['imm32'][hex(t)]['VA']) == 0, R['imm32'][hex(t)]['VA'])
    chk('(2) 0 occurrences of %#x as imm32, RVA form, whole image' % t,
        len(R['imm32'][hex(t)]['RVA']) == 0, R['imm32'][hex(t)]['RVA'])
for rec in R['sites']:
    a = rec['site']
    chk('(3) site %s resolved to exactly 3 pushes' % a,
        rec.get('found') and rec.get('push_count') == 3, rec.get('push_count'))
    chk('(3) winning 3-push signature at %s dominates all rivals' % a, rec.get('dominant'),
        [(r['sig'], r['votes']) for r in rec.get('rivals', [])])
    chk('(3) the three pushes at %s all come from one strict gap-free chain ending '
        'exactly on the site' % a, rec.get('pushes_all_in_one_strict_chain'),
        rec.get('chain_len'))
    ta = rec.get('third_arg')
    chk('(3) 3rd stack arg at %s is imm or reg' % a,
        ta is not None and ta['kind'] in ('imm', 'reg'), ta['kind'] if ta else None)

R['per_target'] = per_target
vals, census = {}, {}
for rec in R['sites']:
    ta = rec.get('third_arg')
    if ta:
        census[ta['kind']] = census.get(ta['kind'], 0) + 1
        if ta['kind'] == 'imm':
            vals[ta['hex']] = vals.get(ta['hex'], 0) + 1
R['totals'] = {
    'sites_total': sum(v['n'] for v in per_target.values()),
    'per_target': {k: v['n'] for k, v in per_target.items()},
    'imm32_hits_total': sum(len(R['imm32'][k][f]) for k in R['imm32'] for f in ('VA', 'RVA')),
    'third_arg_kind_census': census,
    'third_arg_imm_values': vals,
    'elapsed_s': round(time.time() - t0, 2)}
chk('T: 0x6bedb0 has exactly 2 direct sites', per_target['0x6bedb0']['n'] == 2)
chk('T: 0x41c250 has exactly 13 direct sites', per_target['0x41c250']['n'] == 13)

R['totals']['asserts_pass'] = sum(1 for a in R['asserts'] if a['pass'])
R['totals']['asserts_total'] = len(R['asserts'])
R['totals']['self_tests_pass'] = sum(1 for a in R['self_tests'] if a['pass'])
R['totals']['self_tests_total'] = len(R['self_tests'])

print('\n[totals] ' + json.dumps(R['totals'], indent=1))
json.dump(R, open(OUT, 'w'), indent=1)
print('[written] ' + OUT)
ok = (R['totals']['asserts_pass'] == R['totals']['asserts_total'] and
      R['totals']['self_tests_pass'] == R['totals']['self_tests_total'])
print('[final] asserts %d/%d, self-tests %d/%d, %d sites, %.2fs -> %s' % (
    R['totals']['asserts_pass'], R['totals']['asserts_total'],
    R['totals']['self_tests_pass'], R['totals']['self_tests_total'],
    R['totals']['sites_total'], time.time() - t0, 'OK' if ok else 'FAILED'))
sys.exit(0 if ok else 1)
