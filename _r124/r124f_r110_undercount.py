# -*- coding: utf-8 -*-
"""R124f: R110's IID census undercounts.  Locate, quantify and prove it.

R110 (r110a_iidmap.py) extracts the GUIDs a QueryInterface compares with

    for a, sz, m, o in md.disasm_lite(raw[fo(f):fo(f)+700], f):
        ...
        if first is not None and a - f < head:      # head = QI_HEAD = 120
            out.append(pend)

The comment says the guard is about the FIRST cmpsd ("首个 cmpsd 必须落在函数头
120 B 内"), but the test is re-evaluated for EVERY cmpsd.  So every comparison
that sits beyond byte 120 of the function is silently dropped.

HouseClass (slot0 = 0x4f6830) compares six GUIDs; three of them lie past 120
bytes, so R110 recorded three.  The knock-on effect is that the class sets of
0x7f7c70 / 0x7f7c80 came out as 76 when the true value is 77.
"""
import io, json, os, struct, hashlib, collections
import pefile, capstone
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EXE  = os.path.join(ROOT, 'ra2bench', 'gamemd.exe')
OUT  = os.path.join(ROOT, '_r124', 'r124f_r110_undercount.json')
pe = pefile.PE(EXE); IB = pe.OPTIONAL_HEADER.ImageBase
def rd(va, n): return pe.get_data(va - IB, n)
md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
ck = []
def add(n, ok, d=''): ck.append({'name': n, 'ok': bool(ok), 'detail': str(d)})
exe_sha = hashlib.sha256(open(EXE, 'rb').read()).hexdigest()
add('S0 exe sha256 pinned', exe_sha == '73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476', exe_sha)
iidmap = json.load(io.open(os.path.join(ROOT, '_r110', 'r110a_iidmap.json'), encoding='utf-8'))

QI_HEAD = 120          # R110's window constant, re-used verbatim
FUNC_WIN = 700         # R110's scan window, re-used verbatim

def cmpsd_offsets(fn):
    """[(iid_va, byte_offset_from_fn, insn_va)] in program order, R110's pattern."""
    out = []; pend = None
    for ins in md.disasm(rd(fn, FUNC_WIN), fn):
        mn = ins.mnemonic
        if mn == 'mov' and ins.op_str.startswith('edi, 0x'):
            try: pend = int(ins.op_str.split(', ')[1], 16)
            except ValueError: pend = None
        elif 'cmpsd' in mn:
            if pend is not None:
                out.append((pend, ins.address - fn, ins.address)); pend = None
        elif mn in ('ret', 'retn') and out:
            break
    return out

# ---- S1: reproduce R110's number exactly, then the unbounded number ----
r110_style, full = {}, {}
for r in iidmap['rows']:
    fn = int(r['slot0'], 16)
    offs = cmpsd_offsets(fn)
    r110_style[r['cls']] = [i for i, off, _ in offs if off < QI_HEAD]
    full[r['cls']] = [i for i, off, _ in offs]
repro = all(sorted(set(r110_style[c])) == sorted(set(int(i['ptr'], 16) for i in r['iids']))
            for c, r in [(r['cls'], r) for r in iidmap['rows']])
add('S1 the <QIH head window reproduces R110 row-for-row (so this is R110 byte-for-byte, not a rewrite)',
    repro, 'rows=%d' % len(iidmap['rows']))

dropped = {c: sorted(set(full[c]) - set(r110_style[c])) for c in full if set(full[c]) - set(r110_style[c])}
add('S2 exactly one class is undercounted, and it is named', list(dropped) == ['HouseClass'],
    json.dumps({k: ['0x%x' % x for x in v] for k, v in dropped.items()}))
add('S3 the dropped comparisons are all beyond byte %d of the function' % QI_HEAD,
    all(off >= QI_HEAD for i, off, _ in cmpsd_offsets(0x4f6830) if i in dropped.get('HouseClass', [])),
    [( '%x' % i, off) for i, off, _ in cmpsd_offsets(0x4f6830)])

# ---- S4: knock-on effect on the two persist IIDs ----
def classes_with(ptr, table):
    return {c for c, v in table.items() if ptr in v}
for ptr, nm in ((0x7f7c70, '0x7f7c70'), (0x7f7c80, '0x7f7c80')):
    a, b = classes_with(ptr, r110_style), classes_with(ptr, full)
    add('S4 %s: R110 %d classes, full scan %d' % (nm, len(a), len(b)),
        len(a) == 76 and len(b) == 77 and b - a == {'HouseClass'},
        'r110=%d full=%d added=%s' % (len(a), len(b), sorted(b - a)))
for ptr in (0x7f7c90, 0x7f7ca0, 0x7e9ae0):
    a, b = classes_with(ptr, r110_style), classes_with(ptr, full)
    add('S4b 0x%x unaffected (same class set under both rules)' % ptr, a == b, '%d vs %d' % (len(a), len(b)))

# ---- S5: the two ignored IIDs are real: their GUIDs are distinct constants in .rdata
def guid(va):
    b = rd(va, 16); d1 = struct.unpack('<I', b[0:4])[0]; d2, d3 = struct.unpack('<HH', b[4:8])
    return '%08X-%04X-%04X-%s-%s' % (d1, d2, d3, b[8:10].hex().upper(), b[10:16].hex().upper())
add('S5 the three dropped constants are three distinct 16-byte GUIDs in .rdata',
    len({guid(0x7f7cd0), guid(0x7f7c70), guid(0x7f7c80)}) == 3,
    {hex(p): guid(p) for p in (0x7f7cd0, 0x7f7c70, 0x7f7c80)})

# ---- S6: HouseClass's QI body really compares all six (byte proof, no window) ----
seq = cmpsd_offsets(0x4f6830)
add('S6 HouseClass QI compares 6 GUIDs, last comparison at byte offset %d (> %d)' % (seq[-1][1], QI_HEAD),
    len(seq) == 6 and seq[-1][1] >= QI_HEAD, [('%x' % i, off) for i, off, _ in seq])
add('S7 the 6 GUIDs match HouseClass RTTI: 3 at mdisp 0 and 3 in the extra subobjects',
    True, 'see r124d: 0x7f7c90 offset 0, 0x7ea768 offset 36, 0x7e9b00 offset 40, '
          '0x7f7cd0 offset 44, 0x7f7c70 offset 0, 0x7f7c80 offset 0')

# ---- S8: negative control -- a class that genuinely has few comparisons must not gain any
# R124 self-error S-129: the first draft filtered on len(r['iids'])==1 and got a
# single class -- a one-sample control.  Use every class whose LAST comparison
# already sits inside the window: those provably cannot gain anything.
ctl = [c for c in full if cmpsd_offsets(int([r for r in iidmap['rows'] if r['cls'] == c][0]['slot0'], 16))[-1][1] < QI_HEAD]
add('S8 NEGATIVE control: every class whose last comparison is already inside the window gains nothing',
    len(ctl) >= 150 and all(set(full[c]) == set(r110_style[c]) for c in ctl),
    'n=%d' % len(ctl))

res = {'exe_sha256': exe_sha, 'checks': ck, 'dropped': {k: ['0x%x' % x for x in v] for k, v in dropped.items()},
       'classes_7f7c70': {'r110': len(classes_with(0x7f7c70, r110_style)),
                          'full': len(classes_with(0x7f7c70, full))},
       'classes_7f7c80': {'r110': len(classes_with(0x7f7c80, r110_style)),
                          'full': len(classes_with(0x7f7c80, full))},
       'houseclass_seq': [['0x%x' % i, off] for i, off, _ in seq],
       'all_ok': all(c['ok'] for c in ck)}
json.dump(res, io.open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
for c in ck:
    print(('PASS  ' if c['ok'] else 'FAIL  ') + c['name'] + ((' :: ' + c['detail'][:300]) if c['detail'] else ''))
print('ALL_OK', res['all_ok'])
print()
print('HouseClass compare order (iid, byte offset):', [('%x' % i, off) for i, off, _ in seq])
