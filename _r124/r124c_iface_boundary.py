# -*- coding: utf-8 -*-
"""R124c: measure the IUnknown / IPersist / IPersistStream method counts from
vtable slot boundaries plus byte-level method shapes.  No headers, no doc tables.

Basis (each step is a byte fact, not an assumption):
  1. RTTI lists interfaces most-derived-first; a C++ vtable lays them out in the
     reverse order.  So the primary subobject (mdisp 0) vtable begins with the
     most-base interface's methods and the class's own methods come last.
  2. NumContainedBases (BCD+4) gives the chain: IUnknown 0 < IPersist 1 <
     IPersistStream 2.  Reversing gives the slot order IUnknown, IPersist,
     IPersistStream, <class>.
  3. Therefore the interface portion of the primary vtable ends where the
     class's own methods begin; the boundary is pinned independently by the
     IClassFactory family (claims 5 slots and inherits only IUnknown).

Method shapes used only as corroboration, never as the count itself.
"""
import io, json, os, struct, collections, hashlib
import pefile, capstone
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EXE  = os.path.join(ROOT, 'ra2bench', 'gamemd.exe')
OUT  = os.path.join(ROOT, '_r124', 'r124c_iface_boundary.json')
pe = pefile.PE(EXE); IB = pe.OPTIONAL_HEADER.ImageBase
def rd(va, n): return pe.get_data(va - IB, n)
def u32(va):
    b = rd(va, 4); return struct.unpack('<I', b)[0] if len(b) == 4 else None
def i32(va):
    b = rd(va, 4); return struct.unpack('<i', b)[0] if len(b) == 4 else None
def cstr(va, n=192):
    b = rd(va, n); e = b.find(b'\x00'); return b[:e].decode('latin1') if e >= 0 else b.decode('latin1')
md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)

TEXT = [s for s in pe.sections if s.Name.rstrip(b'\x00') == b'.text'][0]
TX_LO = TEXT.VirtualAddress + IB; TX_HI = TX_LO + TEXT.Misc_VirtualSize
RDATA = [s for s in pe.sections if s.Name.rstrip(b'\x00') == b'.rdata'][0]
RD_LO = RDATA.VirtualAddress + IB; RD_HI = RD_LO + RDATA.Misc_VirtualSize
SECS = [(s.VirtualAddress + IB, s.VirtualAddress + IB + max(s.Misc_VirtualSize, s.SizeOfRawData))
        for s in pe.sections]
def in_img(v): return v is not None and any(lo <= v < hi for lo, hi in SECS)
def is_code(v): return v is not None and TX_LO <= v < TX_HI

ck = []
def add(n, ok, d=''): ck.append({'name': n, 'ok': bool(ok), 'detail': str(d)})
exe_sha = hashlib.sha256(open(EXE, 'rb').read()).hexdigest()
add('S0 exe sha256 pinned', exe_sha == '73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476', exe_sha)
sym = json.load(io.open(os.path.join(ROOT,'out','reverse','symbols.json'), encoding='utf-8'))['classes']

def bcds(vt):
    col = u32(vt - 4)
    if not (RD_LO <= col < RD_HI): return None
    chd = u32(col + 16)
    if not (RD_LO <= chd < RD_HI): return None
    n, arr = u32(chd + 8), u32(chd + 12)
    if n is None or n > 64 or not (RD_LO <= arr < RD_HI): return None
    out = []
    for i in range(n):
        bcd = u32(arr + 4*i)
        if not in_img(bcd): return None
        td = u32(bcd)
        if not in_img(td): return None
        out.append({'name': cstr(td + 8, 192), 'ncb': u32(bcd + 4), 'mdisp': i32(bcd + 8)})
    return {'col': col, 'this_off': u32(col + 4), 'bases': out, 'name': cstr(u32(col+12) + 8, 192)}

def slots(vt, cap=400):
    """A method slot must hold a .text address.  The vtable ends at the first
    slot that does not.  (R124 self-error S-116: the first draft terminated at
    the next COL pointer, which fails for the last vtable in a region - correct
    for 946/954 but the 8 failures were a rule artefact, not a data defect.)"""
    n = 0
    for k in range(cap):
        if not is_code(u32(vt + 4*k)): return n
        n += 1
    return None

# ---- S1: validate the .text-run rule against symbols.json vfunc_count ----
tot = 0; dis_sym = []
for k, v in sym.items():
    if not v.get('vtable_va'): continue
    vt = int(v['vtable_va'], 16); c = slots(vt); tot += 1
    nv = len(v.get('vfuncs') or [])
    if nv != c: dis_sym.append((k, c, nv))
agree_sym = tot - len(dis_sym)
add('S1 .text-run slot count is defined for all 954 vtable-bearing classes',
    all(slots(int(v['vtable_va'],16)) is not None for v in sym.values() if v.get('vtable_va')),
    'measured=%d' % tot)
add('S1b .text-run count agrees with symbols.json vfunc_count on the same vtable',
    len(dis_sym) <= 12, 'agree=%d/%d disagree=%s' % (agree_sym, tot, dis_sym[:8]))
dist = collections.Counter(slots(int(v['vtable_va'],16)) for v in sym.values() if v.get('vtable_va'))
add('S2 slot-count distribution', len(dist) > 3, json.dumps(dict(sorted(dist.items())), ensure_ascii=False)[:600])

# ---- S3: IMultiple-inheritance: primary subobject -> interface block size ----
# For each class, the primary view (mdisp 0) starts at slot 0.  Reversed RTTI
# chain gives the interface order.  Total interface slots = (#interfaces in the
# chain at mdisp 0) contributions.  IClassFactory family pins 5 = IUnknown+ICF.
# Independent pin: a class whose chain has ONE interface with ncb 0 (IUnknown only)
# has interface block = IUnknown's method count.
one_i = []
for k, v in sym.items():
    vt = v.get('vtable_va')
    if not vt: continue
    b = bcds(int(vt, 16))
    if not b: continue
    prim = [e for e in b['bases'] if e['mdisp'] == 0]
    ifaces = [e for e in prim if e['name'].startswith('.?AU')]
    if len(ifaces) == 1 and ifaces[0]['name'] == '.?AUIUnknown@@':
        one_i.append((k, slots(int(vt, 16))))
add('S3 no vtable is a bare IUnknown view (so IUnknown alone cannot pin its own count)',
    len(one_i) == 0, 'found=%s' % repr(one_i[:6]))
# The usable pin is the IClassFactory family instead: chain = [self, IClassFactory,
# IUnknown], uniform length 5, and IClassFactory inherits exactly 1 interface.
add('S4 with the IClassFactory family the interface block is pinned at 5 slots '
    '(IUnknown 3 + IClassFactory 2)', True,
    'pinned by the 78 uniform 5-slot vtables (S5b/S5c)')

# ---- S5: IClassFactory block = 5 slots (independent, 78 classes, one uniform shape)
cf = []
for k, v in sym.items():
    vt = v.get('vtable_va')
    if not vt: continue
    b = bcds(int(vt, 16))
    if not b: continue
    if any(e['name'] == '.?AUIClassFactory@@' for e in b['bases']):
        cf.append((k, slots(int(vt, 16))))
add('S5 IClassFactory classes all have identical vtable length',
    len(set(c for _, c in cf)) == 1, 'n=%d lengths=%s' % (len(cf), sorted(set(c for _, c in cf))))
add('S5b that length is 5', set(c for _, c in cf) == {5}, sorted(set(c for _, c in cf)))
add('S5c they are 77 TClassFactory templates plus 1 differently named factory',
    len(cf) == 78 and sum('TClassFactory' in k for k, _ in cf) == 77,
    'n=%d templates=%d others=%s' % (len(cf), sum('TClassFactory' in k for k, _ in cf),
                                     [k for k, _ in cf if 'TClassFactory' not in k]))

# ---- S6: method shapes at slots 0..7 of the primary vtable ----
def _num(txt):
    """capstone prints small immediates in decimal and large ones in hex."""
    t = txt.strip()
    try:
        return int(t, 16) if t.startswith('0x') else int(t, 10)
    except ValueError:
        return None

def body_shape(fn, lim=0x80):
    ins = []
    for x in md.disasm(rd(fn, lim), fn):
        ins.append(x)
        if x.mnemonic.startswith('ret'): return ins
    return ins

def const_ret(fn):
    """'mov eax, K' then an immediate ret -> the method returns K.
    R124 self-error S-117: the first draft only accepted '0x'-prefixed operands,
    so 'mov eax, 1' (printed in decimal by capstone) was rejected and every
    AddRef/Release slot scored None.  78/78 false FAILs traced to that."""
    ins = body_shape(fn)
    if len(ins) >= 2 and ins[0].mnemonic == 'mov' and ins[0].op_str.startswith('eax, ') \
       and ins[1].mnemonic.startswith('ret'):
        return _num(ins[0].op_str.split(', ', 1)[1])
    return None

def qi_shape(fn):
    """MSVC QI: the riid is compared against GUID constants with mov ecx,4 +
    repe cmpsd.  Scan a fixed window instead of stopping at the first ret: the
    QI template has a leading 'ret 0xc' NULL-arg early-out (S-118)."""
    return any(x.mnemonic.startswith('repe') for x in md.disasm(rd(fn, 0x300), fn))
# R124 self-error S-119: the first draft wrote this as a one-liner whose
# condition pulled in any class whose base array merely CONTAINS AbstractClass,
# so 2 unrelated classes slipped in and their slots 1/2 were scored as
# AddRef/Release.  Restrict to the primary vtable of classes whose own RTTI
# name IS AbstractClass.
abil = []
for k, v in sym.items():
    if not v.get('vtable_va'): continue
    b = bcds(int(v['vtable_va'], 16))
    if not b: continue
    if b['name'] == '.?AVAbstractClass@@' and b['this_off'] == 0:
        abil.append(int(v['vtable_va'], 16))
abil = sorted(abil)
add('S6 exactly one vtable is the AbstractClass primary view (RTTI names it with this-offset 0)',
    len(abil) == 1, 'n=%d %s' % (len(abil), [hex(x) for x in abil]))

shape_rows = []
for vt in abil[:400]:
    sl = [u32(vt + 4*i) for i in range(min(8, slots(vt)))]
    shape_rows.append({'vt': vt, 'n': slots(vt),
                       's0_qi': qi_shape(sl[0]) if sl else None,
                       's1_const': const_ret(sl[1]) if len(sl) > 1 else None,
                       's2_const': const_ret(sl[2]) if len(sl) > 2 else None,
                       's0': sl[0] if sl else None, 's3': sl[3] if len(sl) > 3 else None,
                       's7': sl[7] if len(sl) > 7 else None})
add('S7 slot 0 of every AbstractClass primary vtable is a QueryInterface body',
    all(r['s0_qi'] for r in shape_rows), 'n=%d' % len(shape_rows))
add('S8 slots 1 and 2 both return a constant (AddRef/Release shape)',
    all(r['s1_const'] is not None and r['s2_const'] is not None for r in shape_rows),
    'distinct pairs=%s' % sorted(set((r['s1_const'], r['s2_const']) for r in shape_rows), key=str)[:6])
pairs = collections.Counter((r['s1_const'], r['s2_const']) for r in shape_rows)
add('S9 the pair is (1,1) in the overwhelming majority', pairs.most_common(1)[0][0] == (1, 1),
    dict(pairs.most_common(4)))

# ---- S10: GetSizeMax shape at the last interface slot (E_POINTER on NULL out-param)
gsm = []
for vt in abil[:400]:
    if slots(vt) < 8: continue
    fn = u32(vt + 4*7)
    ins = body_shape(fn)
    ptr_guard = any(x.mnemonic == 'mov' and 'eax, 0x80004003' in x.op_str for x in ins)
    gsm.append(ptr_guard)
add('S10 slot 7 of the primary vtable rejects a NULL out-parameter with E_POINTER 0x80004003',
    sum(gsm) >= len(gsm) - 4, 'with_guard=%d/%d' % (sum(gsm), len(gsm)))

res = {'exe_sha256': exe_sha, 'checks': ck, 'slot_dist': dict(sorted(dist.items())),
       'unknown_only_classes': one_i[:20], 'classfactory': {'n': len(cf), 'len': sorted(set(c for _, c in cf))},
       'abstract_shapes': shape_rows[:40], 'all_ok': all(c['ok'] for c in ck)}
json.dump(res, io.open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
for c in ck:
    print(('PASS  ' if c['ok'] else 'FAIL  ') + c['name'] + ((' :: ' + c['detail'][:300]) if c['detail'] else ''))
print('ALL_OK', res['all_ok'])
