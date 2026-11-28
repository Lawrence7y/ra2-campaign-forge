#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R217-A card A: independent MI-vtable / thunk / QueryInterface survey.
Single-shot evidence script. Uses streaming capstone disasm_lite only.
"""
import sys, os, re, struct, hashlib, collections
ROOT = '/home/t628/projects/ra2-campaign-forge'
sys.path.insert(0, ROOT + '/_r185')
import pe185 as P
from capstone import Cs, CS_ARCH_X86, CS_MODE_32

mdl = Cs(CS_ARCH_X86, CS_MODE_32)          # disasm_lite only for bulk work
mdf = Cs(CS_ARCH_X86, CS_MODE_32)          # full form only for <=64B snippets

def sec(name):
    s = P.B[name]
    return s['lo'], s['hi_file']

TLO, THI = sec('.text')

def in_text(va):
    return va is not None and TLO <= va < THI

def sdw(va):
    v = P.dw(va)
    if v is None:
        return None
    return v - 0x100000000 if v & 0x80000000 else v

def lit(va, n=2, maxbytes=48):
    off = P.r2o(va)
    if off is None:
        return []
    return list(mdl.disasm_lite(P.RAW[off:off+maxbytes], va, count=n))

def full(va, n=5, maxbytes=64):
    off = P.r2o(va)
    if off is None:
        return []
    return list(mdf.disasm(P.RAW[off:off+maxbytes], va, count=n))

def fmt(insns):
    return ' | '.join('%08X %s %s' % (a, m, o) for a, sz, m, o in insns)

print('=' * 100)
print('R217-A evidence  binary=%s  sha256=%s  sections=%d' % (
    ROOT + '/ra2bench/gamemd.exe',
    hashlib.sha256(P.RAW).hexdigest(), len(P.B)))
for nm in sorted(P.B):
    s = P.B[nm]
    print('  SEC %-8s lo=%08X hi_file=%08X rawsize=%08X' % (nm, s['lo'], s['hi_file'], s['rawsize']))

# ---------------- A1: COL candidates + vftables ----------------
print('\n' + '=' * 100)
print('A1  RTTI / VFTABLE SURVEY')

def valid_chd(c):
    if c is None or P.r2o(c) is None:
        return False
    sig, attrs, nb, bca = P.dw(c), P.dw(c+4), P.dw(c+8), P.dw(c+0xc)
    return (sig == 0 and nb is not None and 0 <= nb <= 64 and
            bca is not None and P.r2o(bca) is not None)

cols = []
stage = collections.Counter()
per_sec = collections.Counter()
# Structural COL: sig=0, pCD=0, pTD -> TypeDescriptor(.?A name), pCHD -> valid CHD.
# The +0x14 "self" field is frequently 0 in this binary, so do not require it.
tds = set()
for nm in sorted(P.B):
    if nm == '.text':
        continue
    s = P.B[nm]; lo, hi = s['lo'], s['hi_file']
    o = s['rawptr']; blob = P.RAW[o:o+s['rawsize']]
    start = 0
    while True:
        i = blob.find(b'.?A', start)
        if i < 0:
            break
        start = i + 1
        va = lo + i
        nm8 = P.cstr(va, 80)
        if nm8 and (nm8.startswith(b'.?AV') or nm8.startswith(b'.?AU')):
            tds.add(va - 8)
stage['typedefs'] = len(tds)
for nm in sorted(P.B):
    if nm == '.text':
        continue
    lo, hi = sec(nm)
    for a in range(lo, hi - 23, 4):
        if P.dw(a) != 0 or P.dw(a+8) != 0 or P.dw(a+0xc) not in tds:
            continue
        stage['sig_pcd_ptd_ok'] += 1
        chd = P.dw(a+0x10)
        if not valid_chd(chd):
            continue
        stage['chd_ok'] += 1
        ptd = P.dw(a+0xc)
        nm8 = P.cstr(ptd+8, 64)
        cols.append({'a': a, 'sig': 0, 'disp': sdw(a+4), 'ptd': ptd,
                     'name': nm8.decode('latin1') if nm8 else '', 'chd': chd,
                     'nb': P.dw(chd+8), 'bca': P.dw(chd+0xc),
                     'self': P.dw(a+0x14)})
        per_sec[nm] += 1
print('A1 COL filter stages: %s ; per-section: %s' % (dict(stage), dict(per_sec)))
print('A1 COL candidate count = %d' % len(cols))
for c in cols[:12]:
    print('   COL %08X sig=%d mdisp=%d pTD=%08X name=%s CHD=%08X nb=%d BCA=%08X' %
          (c['a'], c['sig'], c['disp'], c['ptd'], c['name'], c['chd'], c['nb'], c['bca']))

colmap = {c['a']: c for c in cols}
vts = []
for nm in sorted(P.B):
    if nm == '.text':
        continue
    lo, hi = sec(nm)
    for p in range(lo, hi - 3, 4):
        col = P.dw(p)
        if col not in colmap:
            continue
        V = p + 4
        slots = []
        for k in range(256):
            d = P.dw(V + 4*k)
            if not in_text(d):
                break
            slots.append(d)
        vts.append({'V': V, 'col': col, 'disp': colmap[col]['disp'],
                    'name': colmap[col]['name'], 'slots': slots})
byV = {t['V']: t for t in vts}
print('A1 vftable count = %d ; mdisp!=0 count = %d ; slot0-not-.text count = %d' % (
    len(vts), sum(1 for t in vts if t['disp'] != 0),
    sum(1 for t in vts if not t['slots'])))
print('A1 slot-count distribution (slots -> tables) = %s' %
      dict(sorted(collections.Counter(len(t['slots']) for t in vts).items())))
print('A1 mdisp distribution = %s' %
      dict(sorted(collections.Counter(t['disp'] for t in vts).items())))
print('A1 mdisp!=0 tables:')
for t in vts:
    if t['disp'] != 0:
        print('   V=%08X COL=%08X mdisp=%+d slots=%d slot0=%08X name=%s' %
              (t['V'], t['col'], t['disp'], len(t['slots']),
               t['slots'][0] if t['slots'] else 0, t['name']))

# ---------------- A2: adjustor thunk law ----------------
print('\n' + '=' * 100)
print('A2  ADJUSTOR THUNK LAW (U)')
slot0_of = collections.defaultdict(list)
any_slot_of = collections.defaultdict(list)
for t in vts:
    if t['slots']:
        slot0_of[t['slots'][0]].append(t['V'])
    for f in set(t['slots']):
        any_slot_of[f].append(t['V'])

RE_SUB = re.compile(r'^dword ptr \[esp \+ (0x[0-9a-f]+|\d+)\], (0x[0-9a-f]+|\d+)$')
thunks = []
for t in vts:
    if t['disp'] == 0 or not t['slots']:
        continue
    ins = lit(t['slots'][0], 2)
    if len(ins) < 2:
        continue
    m = RE_SUB.match(ins[0][3])
    if ins[0][2] != 'sub' or not m or int(m.group(1), 0) != 4:
        continue
    if ins[1][2] != 'jmp' or not re.match(r'^(0x[0-9a-f]+|\d+)$', ins[1][3]):
        continue
    thunks.append({'V': t['V'], 'disp': t['disp'], 'f': t['slots'][0],
                   'N': int(m.group(2), 0), 'jmp': int(ins[1][3], 0),
                   'bytes': fmt(ins)})
print('A2 thunk-shaped tables = %d' % len(thunks))
ok = viol = 0
for th in thunks:
    tgts = slot0_of.get(th['jmp'], [])
    anytgts = any_slot_of.get(th['jmp'], [])
    exps = [th['disp'] - byV[u]['disp'] for u in tgts]
    good = th['N'] in exps
    ok += good
    viol += (not good)
    print('   V=%08X mdisp=%+d f=%08X N=%d jmp=%08X slot0-targets=%s any-slot-targets=%s expected=%s %s | %s' %
          (th['V'], th['disp'], th['f'], th['N'], th['jmp'],
           ['%08X' % u for u in tgts], ['%08X' % u for u in anytgts], exps,
           'OK' if good else 'VIOLATION', th['bytes']))
print('A2 lawU hold=%d violate=%d' % (ok, viol))
ctrl = [th for th in thunks if th['N'] == th['disp'] - 1]
print('A2 control N==mdisp-1 hold=%d (of %d thunks)' % (len(ctrl), len(thunks)))
for th in ctrl[:20]:
    print('   CTRL V=%08X mdisp=%+d N=%d' % (th['V'], th['disp'], th['N']))

# ---------------- A3: primary-interface forwarding stub ----------------
print('\n' + '=' * 100)
print('A3  PRIMARY-OBJECT FORWARDING STUB')
R1 = re.compile(r'^mov eax, dword ptr \[esp \+ (0x[0-9a-f]+|\d+)\]$')
R2 = re.compile(r'^mov (\w+), dword ptr \[eax - ?(0x[0-9a-f]+|\d+)\]$')
R3 = re.compile(r'^lea (\w+), \[eax - ?(0x[0-9a-f]+|\d+)\]$')
R4 = re.compile(r'^call dword ptr \[(\w+) \+ (0x[0-9a-f]+|\d+)\]$')
R5 = re.compile(r'^ret (0x[0-9a-f]+|\d+)$')
funcs = set()
for t in vts:
    funcs.update(t['slots'])
hits = []
for f in sorted(funcs):
    ins = lit(f, 5, 40)
    if len(ins) < 5:
        continue
    a, b, c, d, e = ins
    g1 = R1.match(a[3]);  g2 = R2.match(b[3]);  g3 = R3.match(c[3])
    g4 = R4.match(d[3]);  g5 = R5.match(e[3])
    if not (a[2] == 'mov' and g1 and int(g1.group(1), 0) == 4):
        continue
    if not (b[2] == 'mov' and g2 and int(g2.group(2), 0) == 4):
        continue
    if not (c[2] == 'lea' and g3 and int(g3.group(2), 0) == 4):
        continue
    if not (d[2] == 'call' and g4 and g4.group(1) == g3.group(1)):
        continue
    if not (e[2] == 'ret' and g5 and int(g5.group(1), 0) > 0):
        continue
    K = int(g4.group(2), 0)
    places = []
    for t in vts:
        idx = [i for i, x in enumerate(t['slots']) if x == f]
        if idx:
            places.append((t['V'], idx))
    hits.append({'f': f, 'K': K, 'places': places, 'ret': int(g5.group(1), 0),
                 'full': full(f, 5, 40)})
# Also scan raw .text for the 5-insn byte pattern (the stub may live in a slot
# we did not enumerate, e.g. shared across several COL-derived tables).
TSEC = P.B['.text']
base = TSEC['lo']; blob = P.RAW[TSEC['rawptr']:TSEC['rawptr']+TSEC['rawsize']]
for i in range(len(blob)-4):
    if blob[i:i+4] != bytes.fromhex('8b442404'):
        continue
    va = base + i
    ins = full(va, 5, 40)
    if len(ins) < 5:
        continue
    mns = [x.mnemonic for x in ins]; ops = [x.op_str for x in ins]
    if not (mns[:3] == ['mov','mov','lea'] and 'esp + 4' in ops[0]
            and 'eax - 4' in ops[1] and 'eax - 4' in ops[2]
            and mns[3] == 'call' and 'dword ptr' in ops[3]
            and mns[4] == 'ret' and ops[4]):
        continue
    if any(h['f'] == va for h in hits):
        continue
    K = int(re.search(r'\+ (0x[0-9a-f]+|\d+)\]$', ops[3]).group(1), 0)
    places = [(t['V'], [j for j,x in enumerate(t['slots']) if x == va]) for t in vts if va in t['slots']]
    hits.append({'f': va, 'K': K, 'places': places, 'ret': int(ops[4], 0), 'full': ins})
print('A3 hit functions = %d ; involved tables = %d ; K distribution = %s' % (
    len(hits), len(set(v for h in hits for v, _ in h['places'])),
    dict(sorted(collections.Counter(h['K'] for h in hits).items()))))
for h in hits:
    slots = ','.join('%08X#%s' % (v, ','.join(str(i) for i in ix)) for v, ix in h['places'])
    print('   HIT f=%08X K=0x%X ret=0x%X places=%s' % (h['f'], h['K'], h['ret'], slots))
if hits:
    print('A3 full example at %08X:' % hits[0]['f'])
    for i in hits[0]['full']:
        print('   %08X  %-20s %s %s' % (i.address, i.bytes.hex(), i.mnemonic, i.op_str))
    print('A3 all slot indices (0-based) sorted: %s' %
          sorted(i for h in hits for _, ix in h['places'] for i in ix))

# ---------------- A4: 0x410260 QueryInterface ----------------
print('\n' + '=' * 100)
print('A4  QUERYINTERFACE @ 0x410260, 0xb0 bytes')
QA = 0x410260
off = P.r2o(QA)
code = P.RAW[off:off+0xb0]
print('A4 raw: ' + code.hex(' '))
for i in mdf.disasm(code, QA):
    print('   %08X  %-20s %s %s' % (i.address, i.bytes.hex(), i.mnemonic, i.op_str))

print('A4 esp-delta tracking (control-flow aware; esp = original esp - delta):')
print('   push ebx @410264 -> delta=4; jne 410272 keeps that push, so at 410272 delta=4')
print('   push esi @410276, push edi @410277 -> delta=12 at 41028C')
block_delta = {0x410260: 0, 0x410272: 4, 0x41028C: 12}
for i in mdf.disasm(code, QA):
    op = i.op_str
    m = re.search(r'\[esp(?: \+ (0x[0-9a-f]+|\d+))?\]', op)
    if m and i.address in block_delta:
        x = int(m.group(1), 0) if m.group(1) else 0
        d = block_delta[i.address]
        print('   %08X delta=%2d  [esp + 0x%X] -> original esp+%d   ; %s %s' %
              (i.address, d, x, x - d, i.mnemonic, op))
print('   IID pointer read count = 1 (edx at 410272, original esp+8)')
print('   output pointer (eax) from original esp+0xC (at 410260, delta=0)')
print('   ebx = this from original esp+4 (at 41028C, delta=12, encoded +0x10)')
print('A4 data-section immediates -> candidate 16-byte GUID blobs:')
seen = set()
for i in mdf.disasm(code, QA):
    for tok in re.findall(r'0x[0-9a-f]+', i.op_str):
        v = int(tok, 16)
        if v in seen or P.r2o(v) is None or v in (TLO, THI):
            continue
        # only keep immediates pointing into non-.text data sections
        if P.where(v) == '.text':
            continue
        seen.add(v)
        blob = P.RAW[P.r2o(v):P.r2o(v)+16]
        if len(blob) < 16:
            continue
        a, b, c = struct.unpack_from('<IHH', blob, 0)
        tail = blob[8:16]
        guid = '%08X-%04X-%04X-%s-%s' % (a, b, c, tail[:2].hex().upper(), tail[2:].hex().upper())
        print('   imm %s at %08X (instr %08X): raw=%s guid=%s' %
              (tok, v, i.address, blob.hex(' '), guid))
print('A4 control flow note: pop ebp@4102BB, pop edi@4102D0, pop esi@4102D1 restore stack; pop ebx on exits')
print('=' * 100)
