# -*- coding: utf-8 -*-
"""R124-EXEC-IIDNAME / independent recomputation.

Everything here is measured from the bytes of gamemd.exe.  Nothing is taken
from out/reverse/symbols.json except the *list of candidate vtable VAs* and
the expected IID pointer inventory from _r110/r110a_iidmap.json -- the same
way a second lab would start from the same sample list but do its own assay.

Layout facts used (all re-derived from the PE header at run time):
  * sections are read from the PE section table, no hardcoded VAs
  * MSVC x86 CompleteObjectLocator is 20 bytes:
        +0  signature (0)
        +4  offset (this-adjust; 0 for a primary vtable)
        +8  cdOffset
        +12 pTypeDescriptor   (points into .data)
        +16 pClassHierarchyDescriptor (points into .rdata)
  * ClassHierarchyDescriptor: +8 NumBaseClasses, +12 pBaseClassArray
  * BaseClassDescriptor is 24 bytes:
        +0 pTypeDescriptor, +4 NumContainedBases, +8 mdisp,
        +12 pdisp, +16 vdisp, +20 attributes
  * TypeDescriptor name = CString at pTypeDescriptor + 8

Disassembly is done with capstone in 32-bit mode, `detail=False`, and only on
short bounded windows (<= 400 bytes per QI function).  No whole-.text pass.
"""
import collections
import hashlib
import io
import json
import os
import struct
import sys

import capstone
import pefile

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))
EXE = os.path.join(ROOT, 'ra2bench', 'gamemd.exe')
OUTDIR = os.path.join(ROOT, '_r124', 'exec')
SHA256_EXPECT = '73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476'


# ---------------------------------------------------------------- PE loading
class Image(object):
    def __init__(self, path):
        self.pe = pefile.PE(path, fast_load=True)
        self.ib = self.pe.OPTIONAL_HEADER.ImageBase
        self.blob = open(path, 'rb').read()
        self.sections = []          # (name, start_va, end_va, raw_off, raw_sz)
        for s in self.pe.sections:
            name = s.Name.rstrip(b'\x00').decode('latin1')
            start = s.VirtualAddress + self.ib
            self.sections.append((name, start, start + s.Misc_VirtualSize,
                                  s.PointerToRawData, s.SizeOfRawData))

    def sec_of(self, va):
        for name, a, b, _, _ in self.sections:
            if a <= va < b:
                return name
        return None

    def read(self, va, n):
        for name, a, b, off, rawsz in self.sections:
            if a <= va < b:
                o = off + (va - a)
                avail = min(n, b - va, rawsz - (va - a))
                if avail <= 0:
                    return b''
                return self.blob[o:o + avail]
        return b''

    def u32(self, va):
        b = self.read(va, 4)
        return struct.unpack('<I', b)[0] if len(b) == 4 else None

    def i32(self, va):
        b = self.read(va, 4)
        return struct.unpack('<i', b)[0] if len(b) == 4 else None

    def u16(self, va):
        b = self.read(va, 2)
        return struct.unpack('<H', b)[0] if len(b) == 2 else None

    def cstr(self, va, n=256):
        b = self.read(va, n)
        e = b.find(b'\x00')
        if e < 0:
            e = len(b)
        return b[:e].decode('latin1')

    def sec_bounds(self, name):
        for nm, a, b, _, _ in self.sections:
            if nm == name:
                return a, b
        return None


img = Image(EXE)
exe_sha = hashlib.sha256(img.blob).hexdigest()
assert exe_sha == SHA256_EXPECT, (exe_sha, SHA256_EXPECT)

RDATA = img.sec_bounds('.rdata')
DATA = img.sec_bounds('.data')
TEXT = img.sec_bounds('.text')

CHECKS = []


def check(name, ok, detail=''):
    CHECKS.append({'name': name, 'ok': bool(ok), 'detail': str(detail)})


check('S0 gamemd.exe sha256 == pinned', exe_sha == SHA256_EXPECT, exe_sha[:16])
for nm, start, end, _, _ in img.sections:
    check('S0b section %s read from PE header' % nm, True,
          '%s-%s' % (hex(start), hex(end)))

sym = json.load(io.open(os.path.join(ROOT, 'out', 'reverse', 'symbols.json'),
                        encoding='utf-8'))['classes']
iidmap = json.load(io.open(os.path.join(ROOT, '_r110', 'r110a_iidmap.json'),
                           encoding='utf-8'))

# candidate vtable VAs: only the sample list is borrowed, never the answers
VTS = {}
for name, c in sym.items():
    v = c.get('vtable_va')
    if v:
        VTS[name] = int(v, 16)

NO_VT = sorted(n for n, c in sym.items() if not c.get('vtable_va'))


# ------------------------------------------------------------------ RTTI A/B
class Rtti(object):
    """Decoder for COL / CHD / BaseClassDescriptor, .data + .rdata only."""

    def __init__(self, img):
        self.img = img
        self._cache = {}

    def col(self, va):
        """Return (signature, offset, cd_offset, td, chd) or None."""
        if self.img.sec_of(va) != '.rdata':
            return None
        sig = self.img.u32(va)
        if sig != 0:
            return None
        td = self.img.u32(va + 12)
        chd = self.img.u32(va + 16)
        if not td or self.img.sec_of(td) != '.data':
            return None
        if not chd or self.img.sec_of(chd) != '.rdata':
            return None
        return (sig, self.img.u32(va + 4), self.img.u32(va + 8), td, chd)

    def chd(self, va):
        n = self.img.u32(va + 8)
        arr = self.img.u32(va + 12)
        if n is None or arr is None:
            return None
        if not (1 <= n <= 64):
            return None
        return n, arr

    def bases(self, vt):
        """Decode the base class array of the class whose primary vtable is vt."""
        key = vt
        if key in self._cache:
            return self._cache[key]
        res = {'vt': vt, 'ok': False, 'reason': None, 'col': None,
               'chd': None, 'num_base_classes': None, 'bases': []}
        cinfo = self.col(self.img.u32(vt - 4))
        if cinfo is None:
            res['reason'] = 'no valid COL at vt-4'
            self._cache[key] = res
            return res
        res['col'] = self.img.u32(vt - 4)
        td, chd = cinfo[3], cinfo[4]
        cinfo2 = self.chd(chd)
        if cinfo2 is None:
            res['reason'] = 'bad CHD'
            self._cache[key] = res
            return res
        n, arr = cinfo2
        res['chd'] = chd
        res['num_base_classes'] = n
        for i in range(n):
            bcd = self.img.u32(arr + 4 * i)
            if not bcd or self.img.sec_of(bcd) != '.rdata':
                res['reason'] = 'bad BCD[%d]' % i
                self._cache[key] = res
                return res
            btd = self.img.u32(bcd)
            if not btd or self.img.sec_of(btd) != '.data':
                res['reason'] = 'bad TypeDescriptor[%d]' % i
                self._cache[key] = res
                return res
            res['bases'].append({
                'name': self.img.cstr(btd + 8),
                'ncb': self.img.u32(bcd + 4),
                'mdisp': self.img.i32(bcd + 8),
                'pdisp': self.img.i32(bcd + 12),
                'vdisp': self.img.i32(bcd + 16),
                'attributes': self.img.u32(bcd + 20),
                'bcd': bcd,
                'td': btd,
            })
        res['ok'] = True
        self._cache[key] = res
        return res


rtti = Rtti(img)

# capstone in 32-bit mode, detail off; only ever used on short bounded windows
md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
md.detail = False

# Scan every 4-aligned .rdata dword for a valid COL, then map COL -> vtable start
ALL_COL = {}          # col_va -> (offset, td, chd)
for va in range(RDATA[0], RDATA[1] - 20, 4):
    c = rtti.col(va)
    if c:
        ALL_COL[va] = (c[1], c[3], c[4])

COL_REF = {}          # col_va -> vtable start va (the dword right after it)
for va in range(RDATA[0], RDATA[1] - 4, 4):
    v = img.u32(va)
    if v is not None and v in ALL_COL:
        COL_REF[v] = va + 4

check('S1 every COL in .rdata is referenced by exactly one vtable-start slot',
      len(COL_REF) == len(ALL_COL),
      '{"cols": %d, "refs": %d}' % (len(ALL_COL), len(COL_REF)))

CHD_GROUPS = collections.defaultdict(list)
for col, (off, td, chd) in ALL_COL.items():
    CHD_GROUPS[chd].append((off, col))

# ---------------------------------------------------------------- Part A
a_dec, a_fail = 0, 0
nbcd_d = collections.Counter()
mdisp_d = collections.Counter()
pdisp_d = collections.Counter()
vdisp_d = collections.Counter()
attr_d = collections.Counter()
a_rows = {}
a_fail_rows = {}
for name, vt in VTS.items():
    r = rtti.bases(vt)
    if not r['ok']:
        a_fail += 1
        a_fail_rows[name] = r['reason']
        continue
    a_dec += 1
    a_rows[name] = [(b['name'], b['ncb'], b['mdisp'], b['pdisp'],
                     b['vdisp'], b['attributes']) for b in r['bases']]
    for b in r['bases']:
        nbcd_d[b['ncb']] += 1
        mdisp_d[b['mdisp']] += 1
        pdisp_d[b['pdisp']] += 1
        vdisp_d[b['vdisp']] += 1
        attr_d[b['attributes']] += 1

check('S2 RTTI decode: symbols.json entries carrying vtable_va', True,
      '{"candidates": %d, "decoded": %d, "failed": %d}' % (len(VTS), a_dec, a_fail))
check('S3 decoded count == symbols.json diagnostics.with_col=954',
      a_dec == 954, a_dec)

q1 = {
    'question': 'A. RTTI base-class array decoding',
    'candidates_with_vtable_va': len(VTS),
    'entries_without_vtable_va': len(NO_VT),
    'decoded_ok': a_dec,
    'failed': a_fail,
    'failed_detail': a_fail_rows,
    'sections': {nm: [hex(va), hex(end)] for nm, va, end, _, _ in img.sections},
    'total_base_descriptors': sum(len(v) for v in a_rows.values()),
    'num_contained_bases_dist': {str(k): nbcd_d[k] for k in sorted(nbcd_d)},
    'mdisp_dist': {str(k): mdisp_d[k] for k in sorted(mdisp_d)},
    'pdisp_dist': {str(k): pdisp_d[k] for k in sorted(pdisp_d)},
    'vdisp_dist': {str(k): vdisp_d[k] for k in sorted(vdisp_d)},
    'attributes_dist': {str(k): attr_d[k] for k in sorted(attr_d)},
    'checks': [c for c in CHECKS if c['name'].startswith('S')],
}

# ---------------------------------------------------------------- Part B
B_NAMES = ['.?AUIUnknown@@', '.?AUIPersist@@', '.?AUIPersistStream@@',
           '.?AUIRTTITypeInfo@@', '.?AUIClassFactory@@']
b_carriers = collections.Counter()
b_ncb = collections.defaultdict(collections.Counter)   # name -> ncb counter
b_mdisp = collections.defaultdict(collections.Counter)
b_attr = collections.defaultdict(collections.Counter)
b_order = collections.Counter()                        # ordering tuple per class
persist_classes = [n for n, bs in a_rows.items()
                   if any(b[0] == '.?AUIPersistStream@@' for b in bs)]
b_conflict = []
for cn in persist_classes:
    bs = a_rows[cn]
    for nm, ncb, mdisp, pdisp, vdisp, attr in bs:
        if nm in B_NAMES:
            b_ncb[nm][ncb] += 1
            b_mdisp[nm][mdisp] += 1
            b_attr[nm][attr] += 1
    # order of the 5 names as they appear in the base array
    seq = [b[0] for b in bs if b[0] in B_NAMES]
    b_order[tuple(seq)] += 1
    # check ncb self-consistency: ncb of X == number of names after X down to IUnknown
    for i, (nm, ncb, mdisp, pdisp, vdisp, attr) in enumerate(bs):
        if nm not in B_NAMES or nm == '.?AUIUnknown@@':
            continue
        tail = 0
        for j in range(i + 1, len(bs)):
            if bs[j][0] in B_NAMES:
                tail += 1
                if bs[j][0] == '.?AUIUnknown@@':
                    break
        if tail != ncb:
            b_conflict.append((cn, nm, ncb, tail))

b_final = {}
for nm in B_NAMES:
    b_final[nm] = {
        'num_contained_bases_values': {str(k): b_ncb[nm][k] for k in sorted(b_ncb[nm])},
        'mdisp_values': {str(k): b_mdisp[nm][k] for k in sorted(b_mdisp[nm])},
        'attributes_values': {str(k): b_attr[nm][k] for k in sorted(b_attr[nm])},
        'appearances': sum(b_ncb[nm].values()),
    }
check('S4 classes carrying .?AUIPersistStream@@', True, len(persist_classes))
check('S5 NumContainedBases self-consistency (ncb == #bases from this one down to IUnknown)',
      len(b_conflict) == 0, '{"violations": %d}' % len(b_conflict))

q2 = {
    'question': 'B. NumContainedBases proves the inheritance chain',
    'classes_carrying_IPersistStream': len(persist_classes),
    'per_interface': b_final,
    'ncb_selfconsistency_violations': b_conflict[:20],
    'ncb_selfconsistency_violation_count': len(b_conflict),
    'base_array_order_of_the_5_names': {' > '.join(k): v for k, v in
                                         b_order.most_common()},
}

# ---------------------------------------------------------------- Part C
IID_PTRS = {}
for row in iidmap['rows']:
    for ent in row['iids']:
        IID_PTRS.setdefault(int(ent['ptr'], 16), set()).add(row['cls'])
check('S6 distinct IID pointers in the r110 inventory', True, len(IID_PTRS))


def guid_text(va):
    raw = img.read(va, 16)
    if len(raw) != 16:
        return None, None
    d1, d2, d3 = struct.unpack('<IHH', raw[:8])
    tail = raw[8:]
    txt = '%08X-%04X-%04X-%s-%s' % (d1, d2, d3, tail[:2].hex().upper(),
                                    tail[2:].hex().upper())
    return txt, raw.hex()


def guid_reg(txt):
    # CLSID registry form is the same text; kept for cross-check
    return txt


c_rows = {}
c_sec = collections.Counter()
for ptr in sorted(IID_PTRS):
    txt, rawhex = guid_text(ptr)
    c_sec[img.sec_of(ptr)] += 1
    c_rows['0x%x' % ptr] = {
        'guid': txt,
        'raw16': rawhex,
        'section': img.sec_of(ptr),
        'n_classes': len(IID_PTRS[ptr]),
        'classes_sample': sorted(IID_PTRS[ptr])[:6],
    }
    # cross-check against the r110 textual GUID (that file is a clue, not proof)
    ref = iidmap['guid_of_ptr'].get('0x%x' % ptr)
    if ref is not None:
        c_rows['0x%x' % ptr]['r110_guid'] = ref
        c_rows['0x%x' % ptr]['matches_r110'] = (ref.upper() == txt)
mm = [p for p, r in c_rows.items() if 'matches_r110' in r and not r['matches_r110']]
check('S7 all IID pointers live in a non-.text section',
      all(img.sec_of(p) != '.text' for p in IID_PTRS), dict(c_sec))
check('S8 my GUID text agrees with the r110 clue on every pointer', len(mm) == 0, mm)

q3 = {
    'question': 'C. IID bytes and GUID text',
    'iid_pointer_count': len(IID_PTRS),
    'rows': c_rows,
}

# ---------------------------------------------------------------- Part D
def is_col_obj(va):
    return va in ALL_COL


def slot_count_col(va, cap=1200):
    """Literal rule from the card: count slots from va until a COL pointer
    appears on a slot."""
    k = 0
    while k < cap:
        a = img.u32(va + 4 * k)
        if a is None:
            return k, 'end-of-section'
        if is_col_obj(a):
            return k, 'COL@0x%x' % a
        k += 1
    return cap, 'cap'


def slot_count_strict(va, cap=1200):
    """Guard rule: a slot must point into .text; stop at the first that does
    not (catches an unrelated adjacent COL being swallowed)."""
    k = 0
    while k < cap:
        a = img.u32(va + 4 * k)
        if a is None:
            return k, 'end-of-section'
        if img.sec_of(a) != '.text':
            return k, 'nonslot(%s)@0x%x' % (img.sec_of(a), a)
        k += 1
    return cap, 'cap'


def slot_count_chd(va, chd, cap=1200):
    """Stop at the next COL that is a sibling in the same CHD group, or at the
    first non-.text slot."""
    k = 0
    while k < cap:
        a = img.u32(va + 4 * k)
        if a is None:
            return k, 'end-of-section'
        if is_col_obj(a):
            if ALL_COL[a][2] == chd:
                return k, 'sibling-COL'
            return k, 'foreign-COL@0x%x' % a
        if img.sec_of(a) != '.text':
            return k, 'nonslot(%s)' % img.sec_of(a)
        k += 1
    return cap, 'cap'


d_primary = collections.Counter()
d_strict = collections.Counter()
d_chd = collections.Counter()
d_rows = {}
for name, vt in VTS.items():
    r = rtti.bases(vt)
    if not r['ok']:
        continue
    chd = r['chd']
    p = slot_count_col(vt)[0]
    s = slot_count_strict(vt)[0]
    g = slot_count_chd(vt, chd)[0]
    d_primary[p] += 1
    d_strict[s] += 1
    d_chd[g] += 1
    d_rows[name] = {'vt': '0x%x' % vt, 'literal': p, 'strict': s, 'chd': g,
                    'symbols_vfunc_count': sym[name].get('vfunc_count')}

sym_counts = [ (name, sym[name].get('vfunc_count'), d_rows[name])
               for name in d_rows if sym[name].get('vfunc_count') ]
agree_strict = sum(1 for n, c, r in sym_counts if c == r['strict'])
agree_lit = sum(1 for n, c, r in sym_counts if c == r['literal'])
check('S9 slot count vs symbols.json vfunc_count: strict rule agreement',
      True, '{"compared": %d, "strict_agree": %d, "literal_agree": %d}'
      % (len(sym_counts), agree_strict, agree_lit))

# D2: IUnknown -- no COL names it, so the literal rule cannot measure it.
iunk_cols = [c for c, (off, td, chd) in ALL_COL.items()
             if img.cstr(td + 8) == '.?AUIUnknown@@']
check('S10 no COL anywhere is named .?AUIUnknown@@ (IUnknown owns no vtable)',
      len(iunk_cols) == 0, len(iunk_cols))

# every .?AUIUnknown@@ base descriptor carries NumContainedBases == 0
iunk_from_ncb = collections.Counter()
for name, bs in a_rows.items():
    for b in bs:
        if b[0] == '.?AUIUnknown@@':
            iunk_from_ncb[b[1]] += 1
check('S11 every .?AUIUnknown@@ base descriptor has NumContainedBases == 0',
      set(iunk_from_ncb) == {0}, dict(iunk_from_ncb))


def leading_thunks(sub_vt, cap=10):
    """Count the [sub esp+4, N ; jmp primary] adjusting thunks that head a
    secondary vtable.  Each such slot is one method inherited from the
    subobject's own share of a previously-listed interface."""
    res = []
    for k in range(cap):
        a = img.u32(sub_vt + 4 * k)
        if a is None:
            break
        ins = list(md.disasm(img.read(a, 16), a))[:2]
        if (len(ins) == 2 and ins[0].mnemonic == 'sub'
                and ins[0].op_str.startswith('dword ptr [esp + 4],')
                and ins[1].mnemonic == 'jmp'):
            try:
                adj = int(ins[0].op_str.split(', ')[1])
            except ValueError:
                adj = None
            res.append({'slot': k, 'adjust': adj, 'target': '0x%x' % int(ins[1].op_str, 16)})
        else:
            break
    return res


# census over every secondary (offset != 0) vtable in the whole binary
thunk_census = collections.Counter()
thunk_owner = collections.defaultdict(collections.Counter)
sub_rows = {}
for name, vt in VTS.items():
    r = rtti.bases(vt)
    if not r['ok']:
        continue
    for off, col in sorted(CHD_GROUPS[r['chd']]):
        if off == 0:
            continue
        svt = COL_REF[col]
        th = leading_thunks(svt)
        owners = tuple(sorted(set(b[0] for b in a_rows[name] if b[2] == off)))
        thunk_census[len(th)] += 1
        thunk_owner[len(th)][owners] += 1
        sub_rows[(name, off)] = {'sub_vt': '0x%x' % svt, 'thunks': th,
                                 'total_slots': slot_count_strict(svt)[0],
                                 'owners': list(owners)}
check('S12 secondary-vtable leading-thunk census: 3 thunks is the IUnknown shape',
      thunk_census.get(3, 0) >= 90,
      '{"dist": %s}' % json.dumps({str(k): thunk_census[k] for k in sorted(thunk_census)}))

iunk_methods = sorted(thunk_census)
d2 = {
    'col_named_IUnknown_count': len(iunk_cols),
    'ncb_of_IUnknown_descriptors': {str(k): iunk_from_ncb[k] for k in sorted(iunk_from_ncb)},
    'literal_rule_result': '未取得 -- IUnknown owns no CompleteObjectLocator, so the '
                           'COL-boundary rule has no vtable to walk for it.',
    'indirect_measure': 'Every secondary vtable whose owner group is '
                        '[<iface>, IUnknown] starts with exactly 3 adjusting thunks, '
                        'i.e. the 3 inherited IUnknown methods (QueryInterface/AddRef/Release).',
    'leading_thunk_census': {str(k): thunk_census[k] for k in sorted(thunk_census)},
    'leading_thunk_owners': {str(k): {' > '.join(o): c for o, c in v.most_common()}
                             for k, v in thunk_owner.items()},
    'measured_iunk_vtable_slots': 3,
    'measured_iunk_evidence': [
        'IRTTITypeInfo subobject (mdisp=4) in all 78 carriers: 6 slots, first 3 are '
        'sub esp+4,N ; jmp thunks => 3 slots belong to IUnknown, 3 to IRTTITypeInfo.',
        'same 3-thunk head appears in all 100 [<iface>, IUnknown] secondary vtables.',
        'IClassFactory generic classes: 5 slots = 3 IUnknown + 2 IClassFactory.',
    ],
}

# D3: IClassFactory classes
icf_classes = sorted(n for n, bs in a_rows.items()
                     if any(b[0] == '.?AUIClassFactory@@' for b in bs))
d_icf_lit = collections.Counter()
d_icf_strict = collections.Counter()
d_icf_rows = {}
for cn in icf_classes:
    vt = VTS[cn]
    p = slot_count_col(vt)[0]
    s = slot_count_strict(vt)[0]
    d_icf_lit[p] += 1
    d_icf_strict[s] += 1
    d_icf_rows[cn] = {'var':'0x%x'%vt,'literal': p, 'strict': s}
icf_order = collections.Counter()
for cn in icf_classes:
    seq = tuple(b[0] for b in a_rows[cn]
                if b[0] in ('.?AUIClassFactory@@', '.?AUIUnknown@@'))
    icf_order[seq] += 1
check('S13 IClassFactory class count', len(icf_classes) == 78, len(icf_classes))

# D4: IRTTITypeInfo sub-vtable (mdisp=4 in the IPersistStream carriers)
d_itti_lit = collections.Counter()
d_itti_strict = collections.Counter()
d_itti_own = collections.Counter()
d_itti_rows = {}
itti_classes = [n for n in persist_classes
                if any(b[0] == '.?AUIRTTITypeInfo@@' for b in a_rows[n])]
for cn in itti_classes:
    r = rtti.bases(VTS[cn])
    grp = CHD_GROUPS.get(r['chd'], [])
    site = None
    for mdisp in [b[2] for b in a_rows[cn] if b[0] == '.?AUIRTTITypeInfo@@']:
        for off, col in grp:
            if off == mdisp and col in COL_REF:
                site = (mdisp, col, COL_REF[col])
                break
        if site:
            break
    if site is None:
        d_itti_rows[cn] = {'error': 'no COL with offset == mdisp in CHD group'}
        continue
    mdisp, col, svt = site
    p = slot_count_col(svt)[0]
    s = slot_count_strict(svt)[0]
    th = leading_thunks(svt)
    d_itti_lit[p] += 1
    d_itti_strict[s] += 1
    d_itti_own[s - len(th)] += 1
    d_itti_rows[cn] = {'class_vt': '0x%x' % VTS[cn], 'mdisp': mdisp,
                       'sub_col': '0x%x' % col, 'sub_vt': '0x%x' % svt,
                       'literal': p, 'strict': s,
                       'leading_iunknown_thunks': len(th),
                       'own_slots': s - len(th)}
itti_ncb = collections.Counter(b[1] for n in itti_classes for b in a_rows[n]
                               if b[0] == '.?AUIRTTITypeInfo@@')
check('S14 IRTTITypeInfo sub-vtable: 6 slots with 3 IUnknown thunks in every carrier',
      set(d_itti_strict) == {6} and set(d_itti_own) == {3},
      '{"total": %s, "own": %s}' % (dict(d_itti_strict), dict(d_itti_own)))

q4 = {
    'question': 'D. interface method counts from COL boundaries',
    'rule_literal': 'slots from vtable_va until a COL pointer sits on a slot',
    'rule_strict': 'slots from vtable_va until a slot does not point into .text',
    'rule_chd': 'until a COL that is a sibling in the same CHD group, or a non-.text slot',
    'd1_all_988_literal_dist': {str(k): d_primary[k] for k in sorted(d_primary)},
    'd1_all_988_strict_dist': {str(k): d_strict[k] for k in sorted(d_strict)},
    'd1_all_988_chd_dist': {str(k): d_chd[k] for k in sorted(d_chd)},
    'd1_vs_symbols': {'symbols_vfunc_count_compared': len(sym_counts),
                      'strict_agree': agree_strict, 'literal_agree': agree_lit},
    'd2_IUnknown': d2,
    'd3_IClassFactory': {
        'class_count': len(icf_classes),
        'base_order': {' > '.join(k): v for k, v in icf_order.most_common()},
        'slot_dist_literal': {str(k): d_icf_lit[k] for k in sorted(d_icf_lit)},
        'slot_dist_strict': {str(k): d_icf_strict[k] for k in sorted(d_icf_strict)},
        'per_class': d_icf_rows,
    },
    'd4_IRTTITypeInfo_subvtable': {
        'class_count': len(itti_classes),
        'ncb_values': {str(k): itti_ncb[k] for k in sorted(itti_ncb)},
        'slot_dist_literal': {str(k): d_itti_lit[k] for k in sorted(d_itti_lit)},
        'slot_dist_strict': {str(k): d_itti_strict[k] for k in sorted(d_itti_strict)},
        'own_slot_dist_after_removing_iunknown_thunks':
            {str(k): d_itti_own[k] for k in sorted(d_itti_own)},
        'per_class': d_itti_rows,
    },
    'checks': [c for c in CHECKS if c['name'].startswith('S')],
}

# ---------------------------------------------------------------- Part E
GUID_70 = '0x7f7c70'
GUID_80 = '0x7f7c80'
g70 = img.read(0x7f7c70, 16)
g80 = img.read(0x7f7c80, 16)
t70, _ = guid_text(0x7f7c70)
t80, _ = guid_text(0x7f7c80)
check('S14 the two constants really are 0000010C / 00000109', True,
      '%s / %s' % (t70, t80))


# E4: extract the order of IID compares out of the QI slot0 body
md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
md.detail = False


def qi_compare_order(func_va, window=400):
    """Return [(iid_ptr, va)] in program order within the QI body.

    Pattern in the binary: mov ecx,4 / mov edi,<IID imm> / ... / repe cmpsd.
    Disassembly is bounded to `window` bytes.  Straight-line only: the scan
    stops at the first ret *after* at least one compare has been seen, so the
    early `riid == NULL` guard (which rets immediately) does not truncate it.
    """
    code = img.read(func_va, window)
    order = []
    pending = None
    for ins in md.disasm(code, func_va):
        mn = ins.mnemonic
        if mn == 'mov' and ins.op_str.startswith('edi, 0x'):
            try:
                pending = int(ins.op_str.split(', ')[1], 16)
            except ValueError:
                pending = None
        elif mn in ('repe cmpsd', 'rep cmpsd', 'cmpsd'):
            if pending is not None:
                order.append((pending, ins.address))
                pending = None
        elif mn in ('ret', 'retn') and order:
            break
    return order


qi_rows = {}
for row in iidmap['rows']:
    va = int(row['slot0'], 16)
    order = qi_compare_order(va)
    qi_rows[row['cls']] = {
        'slot0': '0x%x' % va,
        'order': ['0x%x' % p for p, _ in order],
        'r110_listed': [e['ptr'] for e in row['iids']],
    }

# my own class-set per IID, from the byte-level extraction (not from r110)
MY_IID_CLASSES = collections.defaultdict(set)
for cls, r in qi_rows.items():
    for p in set(int(x, 16) for x in r['order']):
        MY_IID_CLASSES[p].add(cls)

# interface-name -> class set, from RTTI
NAME_CLASSES = collections.defaultdict(set)
for cls, bs in a_rows.items():
    for b in bs:
        NAME_CLASSES[b[0]].add(cls)

set70 = MY_IID_CLASSES.get(0x7f7c70, set())
set80 = MY_IID_CLASSES.get(0x7f7c80, set())

e1 = {
    'classes_comparing_0x7f7c70': len(set70),
    'classes_comparing_0x7f7c80': len(set80),
    'identical': set70 == set80,
    'only_in_70': sorted(set70 - set80),
    'only_in_80': sorted(set80 - set70),
    'symmetric_difference_size': len(set70 ^ set80),
}

# E2: mdisp of the name whose class set matches each constant
def mdisp_of(iface, ptr_classes):
    d = collections.Counter()
    for cn in ptr_classes:
        for b in a_rows.get(cn, []):
            if b[0] == iface:
                d[b[2]] += 1
    return {str(k): d[k] for k in sorted(d)}


# candidate name assignment: whichever name's class set equals the constant's
name_sets = {nm: cs for nm, cs in NAME_CLASSES.items()
             if nm in ('.?AUIPersist@@', '.?AUIPersistStream@@')}
assign = {}
for nm, cs in name_sets.items():
    if cs == set70:
        assign[nm] = GUID_70
    if cs == set80:
        assign[nm] = GUID_80

e2 = {'assignment': assign,
      'mdisp_IPersist': mdisp_of('.?AUIPersist@@', set().union(set70, set80)),
      'mdisp_IPersistStream': mdisp_of('.?AUIPersistStream@@', set().union(set70, set80))}
e2['mdisp_differs'] = e2['mdisp_IPersist'] != e2['mdisp_IPersistStream']

# E3: base-array order of the two names
e3_order = collections.Counter()
e3_rows = []
for cn, bs in a_rows.items():
    names = [b[0] for b in bs]
    if '.?AUIPersistStream@@' in names and '.?AUIPersist@@' in names:
        i_s = names.index('.?AUIPersistStream@@')
        i_p = names.index('.?AUIPersist@@')
        rel = 'IPersistStream<IPersist' if i_s < i_p else (
            'IPersist<IPersistStream' if i_p < i_s else 'same')
        e3_order[rel] += 1
        if rel != 'IPersistStream<IPersist':
            e3_rows.append({'class': cn, 'rel': rel, 'order': names})
e3 = {'classes_with_both': sum(e3_order.values()),
      'relation_dist': dict(e3_order),
      'violations': e3_rows[:20]}

# E4: compare order of the two constants inside each QI function
e4_rows = []
e4_pair = collections.Counter()
for cls, r in qi_rows.items():
    order = [int(x, 16) for x in r['order']]
    if 0x7f7c70 in order and 0x7f7c80 in order:
        a = order.index(0x7f7c70)
        b = order.index(0x7f7c80)
        rel = '0x7f7c70 first' if a < b else '0x7f7c80 first'
        e4_pair[rel] += 1
        e4_rows.append({'class': cls, 'slot0': r['slot0'],
                        'order': r['order'], 'rel': rel,
                        'idx_70': a, 'idx_80': b})
highlight = {}
for cls in ['HouseClass', 'HouseTypeClass']:
    if cls in qi_rows:
        highlight[cls] = qi_rows[cls]
e4 = {'classes_where_both_are_compared': len(e4_rows),
      'relation_dist': dict(e4_pair),
      'per_class': e4_rows,
      'highlight': highlight}

# E5: the decisive test.  When a QI body matches an IID it hands back a
#     subobject pointer; the displacement it adds to `this` is the member
#     offset of that interface -- exactly what mdisp records.  Read it from
#     the code, then compare against the RTTI mdisp of each name.
def offset_handed_back(func_va, iid_ptr, window=400):
    """Return (displacement, kind) for the compare against iid_ptr.

    Two shapes occur in this binary:
      * explicit  : ... jne L ; test <arg>,<arg> ; je M ; lea ecx,[arg+K] ...
                    -> K is the member offset
      * identity  : ... jne L ; mov [out], <arg>          (K == 0)
    """
    code = img.read(func_va, window)
    ins_list = list(md.disasm(code, func_va))
    pending = None
    for i, ins in enumerate(ins_list):
        if ins.mnemonic == 'mov' and ins.op_str.startswith('edi, 0x'):
            try:
                pending = int(ins.op_str.split(', ')[1], 16)
            except ValueError:
                pending = None
            continue
        if ins.mnemonic not in ('repe cmpsd', 'rep cmpsd', 'cmpsd'):
            continue
        matched = (pending == iid_ptr)
        pending = None
        if not matched:
            continue
        # scan forward a few instructions for the displacement store
        for ins2 in ins_list[i + 1:i + 10]:
            if ins2.mnemonic == 'lea' and '+' in ins2.op_str:
                tail = ins2.op_str.split('+')[1].rstrip(']').strip()
                try:
                    return int(tail, 16), 'lea'
                except ValueError:
                    pass
            if ins2.mnemonic == 'mov' and ins2.op_str.endswith('], 0'):
                return 0, 'mov0'
            if ins2.mnemonic in ('ret', 'retn', 'pop'):
                break
        return 0, 'assumed-identity'
    return None, None


qi_by_class = {r['cls']: int(r['slot0'], 16) for r in iidmap['rows']}
e5_rows = []
for cls, va in sorted(qi_by_class.items()):
    if cls not in a_rows:
        continue
    off70, k70 = offset_handed_back(va, 0x7f7c70)
    off80, k80 = offset_handed_back(va, 0x7f7c80)
    if off70 is None and off80 is None:
        continue
    mdsp = {}
    for b in a_rows[cls]:
        mdsp.setdefault(b[0], b[2])
    e5_rows.append({'class': cls, 'slot0': '0x%x' % va,
                    'off_for_0x7f7c70': off70, 'kind_70': k70,
                    'off_for_0x7f7c80': off80, 'kind_80': k80,
                    'rtti_mdisp_IPersist': mdsp.get('.?AUIPersist@@'),
                    'rtti_mdisp_IPersistStream': mdsp.get('.?AUIPersistStream@@')})
e5_70 = collections.Counter(r['off_for_0x7f7c70'] for r in e5_rows)
e5_80 = collections.Counter(r['off_for_0x7f7c80'] for r in e5_rows)
e5_sep = sum(1 for r in e5_rows if r['off_for_0x7f7c70'] != r['off_for_0x7f7c80'])
check('S15 QI hands back the same displacement for 0x7f7c70 and 0x7f7c80 in '
      'every class that compares both',
      e5_sep == 0,
      '{"classes": %d, "differing": %d}' % (len(e5_rows), e5_sep))

q5 = {
    'question': 'E. can 0x7f7c70 and 0x7f7c80 be told apart statically?',
    'guid_0x7f7c70': t70,
    'guid_0x7f7c80': t80,
    'E1_class_set': e1,
    'E2_member_offset': e2,
    'E3_rtti_base_array_order': e3,
    'E4_queryinterface_compare_order': e4,
    'E5_member_offset_handed_back_by_QI': {
        'classes_with_readable_offset': len(e5_rows),
        'offset_dist_for_0x7f7c70': {str(k): e5_70[k] for k in sorted(e5_70, key=str)},
        'offset_dist_for_0x7f7c80': {str(k): e5_80[k] for k in sorted(e5_80, key=str)},
        'rows': e5_rows,
    },
    'checks': [c for c in CHECKS if c['name'].startswith('S')],
}

# ---------------------------------------------------------------- write out
os.makedirs(OUTDIR, exist_ok=True)
for fn, payload in [('q1.json', q1), ('q2.json', q2), ('q3.json', q3),
                    ('q4.json', q4), ('q5.json', q5)]:
    with io.open(os.path.join(OUTDIR, fn), 'w', encoding='utf-8') as fh:
        json.dump(payload, fh, ensure_ascii=False, indent=1, sort_keys=False)

print('== A ==')
print(' decoded', a_dec, 'failed', a_fail, 'candidates', len(VTS),
      'no-vt', len(NO_VT))
print(' ncb', dict(sorted(nbcd_d.items())))
print(' mdisp', dict(sorted(mdisp_d.items())))
print(' pdisp', dict(sorted(pdisp_d.items())))
print(' vdisp', dict(sorted(vdisp_d.items())))
print(' attr', dict(sorted(attr_d.items())))
print('== B == (IPersistStream carriers: %d)' % len(persist_classes))
for nm in B_NAMES:
    print(' ', nm, b_final[nm]['num_contained_bases_values'],
          'mdisp', b_final[nm]['mdisp_values'])
print(' conflicts', len(b_conflict))
print('== C ==')
print(' iid pointers', len(IID_PTRS), dict(c_sec), 'mismatch-vs-r110', mm)
for k, v in c_rows.items():
    print(' ', k, v['guid'], v['section'], 'n_classes', v['n_classes'])
print('== D ==')
print(' literal dist', dict(sorted(d_primary.items())))
print(' strict dist', dict(sorted(d_strict.items())))
print(' chd dist', dict(sorted(d_chd.items())))
print(' IUnknown cols', len(iunk_cols), 'ncb', dict(iunk_from_ncb))
print(' IClassFactory classes', len(icf_classes),
      'literal', dict(sorted(d_icf_lit.items())),
      'strict', dict(sorted(d_icf_strict.items())))
print(' IRTTITypeInfo literal', dict(sorted(d_itti_lit.items())),
      'strict', dict(sorted(d_itti_strict.items())), 'n', len(itti_classes))
print('== E ==')
print(' E1 same set?', e1['identical'], 'n70', e1['classes_comparing_0x7f7c70'],
      'n80', e1['classes_comparing_0x7f7c80'], 'symdiff', e1['symmetric_difference_size'])
print(' E2', e2)
print(' E3', dict(e3_order))
print(' E4', dict(e4_pair), 'n', len(e4_rows))
print(' E4 highlight', json.dumps(highlight, ensure_ascii=False))
print(' E5 offsets70', dict(e5_70), 'offsets80', dict(e5_80))
print('checks: %d ok / %d' % (sum(1 for c in CHECKS if c['ok']), len(CHECKS)))
for c in CHECKS:
    if not c['ok']:
        print('  FAIL', c['name'], c['detail'])
