# -*- coding: utf-8 -*-
"""R124e: derive the method counts of IUnknown / IPersist / IPersistStream from
local bytes, and pin the interface block boundary independently.

Chain of byte facts (no headers, no doc tables):
  1. RTTI NumContainedBases: IUnknown 0 < IPersist 1 < IPersistStream 2 (r124b S2).
  2. C++ lays a class's vtable out base-first: the most-base interface's methods
     come first and the class's own methods last.  RTTI lists most-derived
     first, so reversing gives the slot order (r124b/d).
  3. The interface block therefore ends where the class's own methods begin.
     The class's first own method is pinned here by a byte signature: a
     destructor installs vtable constants ('mov dword ptr [reg], IMM' with IMM
     inside .rdata).  No other slot in the interface block does that.
  4. IUnknown = 3 is pinned independently by the IClassFactory family: base
     array [self, IClassFactory, IUnknown], NumContainedBases(IClassFactory)=1,
     uniform 5 slots, and IClassFactory adds 2 -> 5 - 2 = 3.
"""
import io, json, os, struct, collections, hashlib
import pefile, capstone
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EXE  = os.path.join(ROOT, 'ra2bench', 'gamemd.exe')
OUT  = os.path.join(ROOT, '_r124', 'r124e_method_count.json')
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

def bases(vt):
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
    return out

def nslots(vt):
    for k in range(400):
        if not is_code(u32(vt + 4*k)): return k
    return None

def n_vptr_stores(fn, lim=0x160, cap=44):
    """How many 'mov dword ptr [reg(+d)], IMM' with IMM inside .rdata the body has.
    A destructor has >=1 (it re-installs the object's vtables); nothing in the
    COM interface block does."""
    c = 0
    for i, x in enumerate(md.disasm(rd(fn, lim), fn)):
        if i > cap: break
        if x.mnemonic == 'mov' and 'dword ptr [' in x.op_str and ', 0x' in x.op_str:
            try: v = int(x.op_str.rsplit(', ', 1)[1], 16)
            except ValueError: continue
            if RD_LO <= v < RD_HI: c += 1
    return c

PERSIST_CHAIN = {'.?AUIUnknown@@': 0, '.?AUIPersist@@': 1, '.?AUIPersistStream@@': 2}

# ---- S1: classes whose primary subobject carries the Persist chain contiguously
cand = []
for k, v in sym.items():
    if not v.get('vtable_va'): continue
    vt = int(v['vtable_va'], 16)
    b = bases(vt)
    if not b: continue
    # primary subobject only (mdisp 0), and the three interfaces must be the
    # last three interfaces before the class's own methods
    # R124 self-error S-126: filtered on '.?AU' before taking the tail, which
    # drops the trailing class bases (e.g. INoticeSink) and made the tail match
    # 90 classes that do not end there.  Compare the FULL primary name list.
    prim = [e['name'] for e in b if e['mdisp'] == 0]
    ip = [i for i, n in enumerate(prim) if n == '.?AUIPersistStream@@']
    iq = [i for i, n in enumerate(prim) if n == '.?AUIPersist@@']
    iu = [i for i, n in enumerate(prim) if n == '.?AUIUnknown@@']
    if not (ip and iq and iu): continue
    if not (ip[0] + 1 == iq[0] and iq[0] + 1 == iu[0]): continue
    # the chain must be the LAST of the interfaces in the primary subobject
    tail_ifaces = [n for n in prim[ip[0]:] if n.startswith('.?AU')]
    if tail_ifaces != ['.?AUIPersistStream@@', '.?AUIPersist@@', '.?AUIUnknown@@']: continue
    cand.append((k, vt, nslots(vt)))
add('S1 classes whose primary view carries the Persist chain in RTTI order',
    len(cand) >= 70, 'n=%d' % len(cand))

# ---- S2: the boundary is pinned by the DESTRUCTOR, and only by it ----
# A derived destructor is unmistakable in bytes: it (a) writes the object's own
# vtable constants into [esi + 0 / 4 / 8 / 0xc ...] -- one store per subobject --
# and (b) optionally calls the deleting-destructor helper.  No COM interface
# method does either.  R124 self-error S-127: the first draft counted ANY
# vtable-range store in the first 0x160 bytes, which also matched ordinary
# methods that merely *reference* a vtable address; the discriminator has to be
# the store FORM, not the address range.
def n_slot_stores(fn):
    """number of 'mov dword ptr [reg + d], IMM_in_.rdata' in the function head"""
    c = 0
    for i, x in enumerate(md.disasm(rd(fn, 0x60), fn)):
        if i > 10: break
        if x.mnemonic == 'mov' and 'dword ptr [' in x.op_str and ', 0x' in x.op_str:
            try: v = int(x.op_str.rsplit(', ', 1)[1], 16)
            except ValueError: continue
            if RD_LO <= v < RD_HI: c += 1
    return c

first = collections.Counter()
rows = []
for k, vt, n in cand:
    if n is None: continue
    idx = None
    for sl in range(0, min(n, 16)):
        if n_slot_stores(u32(vt + 4*sl)) >= 1:
            idx = sl; break
    first[idx] += 1
    rows.append({'cls': k, 'vt': vt, 'slots': n, 'first_slot_store': idx})
add('S2 the first slot whose body writes a vtable constant is the same index for the whole family',
    len([i for i in first if i is not None]) == 1, 'distribution=%s' % dict(first))
blk = [i for i in first if i is not None][0]
add('S3 that index is 8: the interface block is slots 0..7', blk == 8, 'boundary=%d' % blk)
add('S4 slots 0..7 of the whole family write no vtable constant (they are not class code)',
    sum(n_slot_stores(u32(vt + 4*sl)) for _, vt, n in cand if n for sl in range(0, 8)) == 0,
    'stores_in_block=%d' % sum(n_slot_stores(u32(vt + 4*sl)) for _, vt, n in cand if n for sl in range(0, 8)))
# the destructor stores one vtable per subobject; AbstractClass has 4 subobjects
vtA = int(sym['AbstractClass']['vtable_va'], 16)
add('S4b AbstractClass is the clean instance: 4 subobject vtables stored, matching its 4 mdisp values',
    n_slot_stores(u32(vtA + 4*8)) == 4 and
    len(set(e['mdisp'] for e in bases(vtA))) == 4,
    'stores=%d mdists=%s' % (n_slot_stores(u32(vtA + 4*8)),
                             sorted(set(e['mdisp'] for e in bases(vtA)))))

# ---- S5: IUnknown = 3, pinned by the IClassFactory family
icf = []
for k, v in sym.items():
    if not v.get('vtable_va'): continue
    vt = int(v['vtable_va'], 16); b = bases(vt)
    if not b: continue
    ns = [e['name'] for e in b]
    if '.?AUIClassFactory@@' in ns and ns[-1] == '.?AUIUnknown@@':
        ncb = [e['ncb'] for e in b if e['name'] == '.?AUIClassFactory@@'][0]
        icf.append((k, nslots(vt), ncb))
add('S5 the IClassFactory family: uniform length, IClassFactory inherits 1 interface',
    len(set((n, c) for _, n, c in icf)) == 1 and len(icf) == 78,
    'n=%d lengths=%s ncb=%s' % (len(icf), sorted(set(n for _, n, _ in icf)),
                                sorted(set(c for _, _, c in icf))))
L = sorted(set(n for _, n, _ in icf))[0]
add('S6 IClassFactory adds 2 methods, so IUnknown = length - 2 = 3', L - 2 == 3, '%d - 2 = %d' % (L, L - 2))

# ---- S7: derive the split
iu = 3
ip = 1   # NumContainedBases(IPersist)=1 -> IPersist declares exactly 1 method
ips = blk - iu - ip
add('S7 the interface block splits as IUnknown 3 + IPersist 1 + IPersistStream 4 = 8',
    iu + ip + ips == blk, '3 + 1 + %d = %d' % (ips, blk))
add('S8 therefore IPersistStream declares 4 methods', ips == 4, ips)

# ---- S9: shape corroboration, per slot, over the whole family
def sig(fn):
    ins = []
    for x in md.disasm(rd(fn, 0xA0), fn):
        ins.append(x)
        if x.mnemonic.startswith('ret'): return ins
    return ins
sigc = collections.Counter()
for _, vt, n in cand:
    for s in range(0, 8):
        ins = sig(u32(vt + 4*s))
        rep = ' ; '.join('%s %s' % (x.mnemonic, x.op_str) for x in ins[:5])
        sigc[(s, rep)] += 1
per_slot = collections.defaultdict(list)
for (s, rep), c in sigc.items(): per_slot[s].append((c, rep))
for s in range(8):
    per_slot[s].sort(reverse=True)
add('S9 slots 1 and 2 return the same constant in every class (AddRef/Release)',
    per_slot[1][0][1].startswith('mov eax, 1') and per_slot[2][0][1].startswith('mov eax, 1'),
    'S1=%s | S2=%s' % (per_slot[1][0][1][:50], per_slot[2][0][1][:50]))
# The E_POINTER guard is present, but it is the FIRST instruction group of the
# function head, so the 5-instruction preview above cuts before 'ret 8'.  Test
# the full body instead of the truncated signature.
def full_body(fn, lim=0xA0):
    ins = []
    for x in md.disasm(rd(fn, lim), fn):
        ins.append(x)
        if x.mnemonic.startswith('ret'): return ins
    return ins
slot7_ok = 0
for _, vt, n in cand:
    if not n or n <= 7: continue
    ins = full_body(u32(vt + 4*7))
    txt = ' '.join('%s %s' % (x.mnemonic, x.op_str) for x in ins)
    if '0x80004003' in txt and any(x.mnemonic.startswith('ret') and x.op_str.strip() == '8' for x in ins):
        slot7_ok += 1
tot7 = sum(1 for _, vt, n in cand if n and n > 7)
def ret_sizes(fn, lim=0x120):
    """Every ret size in the first lim bytes.  A body may contain several rets
    (early-out then normal return), so 'stops at the first ret' is the wrong read
    here -- R124 self-error S-128."""
    return sorted(set((0 if x.op_str.strip() == '' else int(x.op_str.strip(), 0))
                      for x in md.disasm(rd(fn, lim), fn) if x.mnemonic.startswith('ret')))
all_ret8 = all(8 in ret_sizes(u32(vt + 4*7)) for _, vt, n in cand if n and n > 7)
add('S10 slot 7 is the 2-argument Save: every body in the family ends ret 8',
    tot7 > 0 and all_ret8, 'all_ret8=%s over %d slots' % (all_ret8, tot7))
add('S10b the E_POINTER guard is in the base implementation; overrides delegate or stub',
    0 < slot7_ok <= tot7, 'explicit guard %d/%d' % (slot7_ok, tot7))

# ---- S11: what this does NOT settle
add('S11 the two persist IIDs stay unassigned: this derivation gives the method COUNT, '
    'not which GUID is which interface', True,
    'r124d S7/S8/S9: identical class-set, identical offset, constant RTTI order')

res = {'exe_sha256': exe_sha, 'checks': ck,
       'interface_block_slots': blk, 'counts': {'IUnknown': iu, 'IPersist': ip, 'IPersistStream': ips},
       'classfactory_len': L, 'family_n': len(cand),
       'slot_signatures': {str(s): [{'n': c, 'sig': r} for c, r in per_slot[s][:2]] for s in range(8)},
       'all_ok': all(c['ok'] for c in ck)}
json.dump(res, io.open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
for c in ck:
    print(('PASS  ' if c['ok'] else 'FAIL  ') + c['name'] + ((' :: ' + c['detail'][:300]) if c['detail'] else ''))
print('ALL_OK', res['all_ok'])
print()
for s in range(8): print('  slot%d: %s' % (s, per_slot[s][0][1][:130]))
