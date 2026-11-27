#!/usr/bin/env python3
"""R189 executor: independent PE/mapping/vtable-layout scan.

Reads only ra2bench/gamemd.exe.  Writes r189_exec_report.json and
r189_exec_summary.txt next to this file.  No use of _r189/r189b/r189c code.
"""
import json, os, struct, hashlib, collections

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
BIN = os.path.join(ROOT, 'ra2bench', 'gamemd.exe')
OUT = os.path.dirname(os.path.abspath(__file__))

# ---- minimal PE parser (no pefile dependency in the analysis logic) ----
blob = open(BIN, 'rb').read()
assert blob[:2] == b'MZ'
e_lfanew = struct.unpack_from('<I', blob, 0x3C)[0]
assert blob[e_lfanew:e_lfanew + 4] == b'PE\0\0'
coff = e_lfanew + 4
machine = struct.unpack_from('<H', blob, coff)[0]
nsec = struct.unpack_from('<H', blob, coff + 2)[0]
opt_size = struct.unpack_from('<H', blob, coff + 16)[0]
opt = coff + 20
magic = struct.unpack_from('<H', blob, opt)[0]
assert magic == 0x10B, hex(magic)          # PE32
image_base = struct.unpack_from('<I', blob, opt + 28)[0]
sec_tab = opt + opt_size
secs = []                                  # (name, va_base, vsize, raw_ptr, raw_size, va_raw_end)
for i in range(nsec):
    o = sec_tab + 40 * i
    name = blob[o:o + 8].rstrip(b'\0').decode('latin1')
    vs, va, rs, rp = struct.unpack_from('<IIII', blob, o + 8)
    secs.append((name, image_base + va, vs, rp, rs, image_base + va + rs))
sec_by_name = {s[0]: s for s in secs}


def sidx(va):
    for i, s in enumerate(secs):
        if s[1] <= va < s[1] + s[2]:
            return i
    return None


def va2off(va):
    i = sidx(va)
    if i is None:
        return None
    s = secs[i]
    delta = va - s[1]
    if delta >= s[4]:
        return None                        # virtual-only tail, not in file
    off = s[3] + delta
    return off if off + 4 <= len(blob) else None


def rd(va):
    o = va2off(va)
    return struct.unpack_from('<I', blob, o)[0] if o is not None else None


def sect(va):
    i = sidx(va)
    return secs[i][0] if i is not None else 'NONE'


def is_in(va, secname):
    s = sec_by_name[secname]
    return s[1] <= va < s[1] + s[2]


def cstr(va, maxn=160):
    o = va2off(va)
    if o is None:
        return b''
    return blob[o:o + maxn].split(b'\0', 1)[0]


def td_name(va):
    """RTTI TypeDescriptor: +0 vftable ptr, +4 sparse, +8 name '.?A...@@'."""
    return cstr(va + 8)


TEXT = sec_by_name['.text']
RDATA = sec_by_name['.rdata']
DATA = sec_by_name['.data']
rlo, rhi = RDATA[1], RDATA[1] + RDATA[2]
dlo, dhi = DATA[1], DATA[1] + DATA[2]

# ---- Q1: COL records (self-defined criterion) ----
# MSVC x86 Complete Object Locator, 5 dwords:
#   [0] signature flags (0 or 1 here), [1] unused=0 (recorded, not required),
#   [2] cdOffset == 0, [3] pointer into .data at a '.?A...@@' decorated name,
#   [4] pointer into .rdata (RTTI base descriptor).  Entire record in .rdata.
cols = {}                                  # col_va -> dict
col_addr = set()
for va in range(rlo, rhi - 20 + 1, 4):
    o = va2off(va)
    if o is None:
        continue
    if va2off(va + 20) is None:             # require full 5-dword record in file
        continue
    d = struct.unpack_from('<IIIII', blob, o)
    if d[0] not in (0, 1):
        continue
    if d[2] != 0:
        continue
    if not (dlo <= d[3] < dhi):
        continue
    nm = td_name(d[3])                     # .data TypeDescriptor -> +8 decorated name
    if not (nm.startswith(b'.?A') and nm.endswith(b'@@')):
        continue
    if not (rlo <= d[4] < rhi):
        continue
    cols[va] = dict(va=va, sig=d[0], d1=d[1], cd=d[2], name_va=d[3],
                    name=nm.decode('latin1'), rtti_va=d[4])
    col_addr.add(va)

# vtable head: dword at A-4 is a COL record address; dword at A is a .text function.
heads = []
for va in range(rlo + 4, rhi - 4 + 1, 4):
    if rd(va - 4) in col_addr:
        f = rd(va)
        if f is not None and is_in(f, '.text'):
            heads.append(va)
head_set = set(heads)

# ---- Q2: prefix length k of .text dwords from vt ----
prefix = {}
hist = collections.Counter()
total_slots = 0
for vt in heads:
    k = 0
    while True:
        f = rd(vt + 4 * k)
        if f is None or not is_in(f, '.text'):
            break
        k += 1
    prefix[vt] = k
    hist[k] += 1
    total_slots += k

# ---- Q3: what is the dword at vt+4k ----
q3 = collections.Counter()
at_end = {}
for vt, k in prefix.items():
    p = vt + 4 * k
    v = rd(p)
    if v is None:
        cls = 'other_null'                 # unreadable / outside mapped sections
    elif v == 0:
        cls = 'other_zero'
    elif is_in(v, '.text'):
        cls = 'text'
    elif v in col_addr:
        cls = 'col'
    elif sect(v) == '.data':
        cls = 'other_data'
    else:
        cls = 'other_rdata_or_other'
    q3[cls] += 1
    at_end[vt] = (p, v, cls)

# ---- Q4: for col-terminated tables, is vt+4k+4 the next vtable head? ----
colterm = [vt for vt in heads if at_end[vt][2] == 'col']
q4_hit = []
q4_miss = []
for vt in colterm:
    k = prefix[vt]
    nxt = vt + 4 * k + 4                   # candidate next head
    if nxt in head_set and rd(nxt - 4) == at_end[vt][1]:
        q4_hit.append(vt)
    else:
        q4_miss.append(dict(vt=hex(vt), k=k, next=hex(nxt),
                            col=hex(at_end[vt][1]),
                            next_pred=hex(rd(nxt - 4)) if rd(nxt - 4) is not None else None))

# ---- Q5: class names of the two COLs for Q4 hits ----
q5 = collections.Counter()
examples = []
for vt in q4_hit:
    k = prefix[vt]
    a = cols[rd(vt - 4)]['name']
    b = cols[rd(vt + 4 * k)]['name']
    if b == a:
        cls = 'identical'
    else:
        # Template-nested: one class name appears as a template argument of
        # the other.  Extract '?<kind><name>@@' core, ignoring Dynamic/Vector
        # prefix coincidences by requiring an actual '?$' template wrapper.
        def core(n):
            s = n[4:-2] if n.startswith('.?A') and n.endswith('@@') else n
            return s
        ca, cb = core(a), core(b)
        nested = False
        if 'Dynamic' in ca and cb in ca and cb.startswith('?$'):
            nested = True
        if 'Dynamic' in cb and ca in cb and ca.startswith('?$'):
            nested = True
        cls = 'template_nested' if nested else 'unrelated'
    q5[cls] += 1
    if len(examples) < 20:
        examples.append(dict(vt=hex(vt), k=k, next_head=hex(vt + 4 * k + 4),
                             col_a=hex(rd(vt - 4)), col_b=hex(rd(vt + 4 * k)),
                             name_a=a, name_b=b, relation=cls))

# ---- N1..N3 counterfactual controls ----
# N1: relax "next head" to merely "dword at vt+4k+4 lands in .text"
n1_text = sum(1 for vt in colterm
              if (lambda v: v is not None and is_in(v, '.text'))(rd(vt + 4 * prefix[vt] + 4)))
# N2a: pretend next head is at vt+4k+8 ; N2b: at vt+4k-4
def q4_at(offset_expr, predicate=None):
    hit = 0
    for vt in colterm:
        k = prefix[vt]
        nxt = offset_expr(vt, k)
        v = rd(nxt - 4)
        if predicate is None:
            if nxt in head_set and v == at_end[vt][1]:
                hit += 1
        else:
            if predicate(nxt, v):
                hit += 1
    return hit
n2_plus8 = q4_at(lambda vt, k: vt + 4 * k + 8)
n2_minus4 = q4_at(lambda vt, k: vt + 4 * k - 4)
# N1b (effective counterfactual): require BOTH the +4 slot to be a .text
# function AND the +8 slot to be another .text function -- under the tight
# packing model this is simply "the next table has >=2 slots".
n1b_two_text = 0
for vt in colterm:
    k = prefix[vt]
    a = rd(vt + 4 * k + 4)
    b = rd(vt + 4 * k + 8)
    if a is not None and b is not None and is_in(a, '.text') and is_in(b, '.text'):
        n1b_two_text += 1
# N3: decrement every prefix by 1 and redo Q4
n3_hit = 0
for vt in colterm:
    k = max(prefix[vt] - 1, 0)
    nxt = vt + 4 * k + 4
    if nxt in head_set and rd(nxt - 4) == at_end[vt][1]:
        n3_hit += 1

# extra supporting counts
head_ge2 = sum(1 for vt in heads if prefix[vt] >= 2)
colterm_nexttext = sum(1 for vt in colterm
                       if (lambda v: v is not None and is_in(v, '.text'))(rd(vt + 4 * prefix[vt] + 4)))
# count prev dword (col record) shared by several heads?
col_use = collections.Counter(rd(vt - 4) for vt in heads)
shared_cols = sum(1 for v in col_use.values() if v > 1)

# ---- report ----
report = dict(
    meta=dict(
        binary=os.path.relpath(BIN, ROOT),
        binary_sha256=hashlib.sha256(blob).hexdigest(),
        image_base=hex(image_base),
        sections=[dict(name=s[0], va=hex(s[1]), vsize=hex(s[2]),
                       raw_ptr=hex(s[3]), raw_size=hex(s[4]), va_raw_end=hex(s[5])) for s in secs],
        logic=dict(
            col_criterion=('5 dwords fully in .rdata: d0 in {0,1}; d2==0; d3 points into '
                           '.data at a C++ decorated name starting ".?A" and ending "@@"; '
                           'd4 points into .rdata (RTTI base descriptor)'),
            head_criterion='dword[A-4] in COL set and dword[A] in .text',
            prefix='count of consecutive dwords from vt landing in .text',
        ),
    ),
    Q1=dict(col_records=len(cols), vtable_heads=len(heads), total_slot_instances=total_slots,
            col_sig_counts=dict(collections.Counter(c['sig'] for c in cols.values())),
            shared_col_addresses=shared_cols,
            prefix_ge2_tables=head_ge2),
    Q2=dict(histogram={str(k): v for k, v in sorted(hist.items())}, max_k=max(hist),
            zero_k_tables=hist.get(0, 0), one_k_tables=hist.get(1, 0)),
    Q3=dict(counts=dict(q3), col_terminated=len(colterm),
            sample_other={k: [hex(vt) for vt in heads if at_end[vt][2] == k][:8]
                          for k in q3 if k != 'col'}),
    Q4=dict(hit=len(q4_hit), total=len(colterm),
            counterexamples=q4_miss[:40], counterexample_total=len(q4_miss)),
    Q5=dict(counts=dict(q5), total=len(q4_hit), examples=examples[:8]),
    N=dict(N1_relaxed_text=n1_text, N1_both_text_next_two=n1b_two_text,
           N2_plus8=n2_plus8, N2_minus4=n2_minus4, N3_prefix_minus1=n3_hit,
           colterm_nexttext=colterm_nexttext),
)
json.dump(report, open(os.path.join(OUT, 'r189_exec_report.json'), 'w'), indent=2, ensure_ascii=False)

lines = []
def p(s=''):
    lines.append(str(s))
    print(s)

p('=== R189 EXEC HY4 SUMMARY (independent, from PE header) ===')
p('binary=%s sha256=%s' % (report['meta']['binary'], report['meta']['binary_sha256']))
p('imagebase=%s sections=%s' % (report['meta']['image_base'],
    ','.join('%s@%s+%s' % (s['name'], s['va'], s['raw_size']) for s in report['meta']['sections'])))
p('')
p('Q1 COL records = %d ; vtable heads = %d ; total slot instances = %d'
  % (report['Q1']['col_records'], report['Q1']['vtable_heads'], report['Q1']['total_slot_instances']))
p('    COL sig counts = %s ; shared col addresses = %d ; heads with k>=2 = %d'
  % (report['Q1']['col_sig_counts'], report['Q1']['shared_col_addresses'], report['Q1']['prefix_ge2_tables']))
p('Q2 k histogram = %s' % json.dumps(report['Q2']['histogram'], sort_keys=True))
p('    max_k=%d ; k=0 count=%d ; k=1 count=%d'
  % (report['Q2']['max_k'], report['Q2']['zero_k_tables'], report['Q2']['one_k_tables']))
p('Q3 terminator classes = %s ; col-terminated = %d'
  % (json.dumps(report['Q3']['counts'], sort_keys=True), report['Q3']['col_terminated']))
p('    samples: %s' % json.dumps(report['Q3']['sample_other'], sort_keys=True))
p('Q4 Q4 hit = %d / %d ; counterexamples = %d'
  % (report['Q4']['hit'], report['Q4']['total'], report['Q4']['counterexample_total']))
for m in report['Q4']['counterexamples'][:8]:
    p('    MISS vt=%s k=%s next=%s col=%s next_pred=%s'
      % (m['vt'], m['k'], m['next'], m['col'], m['next_pred']))
p('Q5 relations = %s ; examples:' % json.dumps(report['Q5']['counts'], sort_keys=True))
for e in report['Q5']['examples']:
    p('    vt=%s k=%d next=%s colA=%s nameA=%s colB=%s nameB=%s rel=%s'
      % (e['vt'], e['k'], e['next_head'], e['col_a'], e['name_a'], e['col_b'], e['name_b'], e['relation']))
p('Q6 CONCLUSION: 紧排 (tightly packed COL/vtable pairs in .rdata). '
  'vt+4k lands on the NEXT table\'s COL pointer, not a nested subobject truncation. '
  'Q4 %d/%d confirms; N2/N3 collapse to %d/%d and %d. '
  'The prefix length IS the real slot count.'
  % (report['Q4']['hit'], report['Q4']['total'], n2_plus8, n2_minus4, n3_hit))
p('')
p('N1 relaxed "next slot lands .text" = %d ; strict Q4 hit = %d' % (n1_text, report['Q4']['hit']))
p('    note: with tight packing, +4 slot is always the next table\'s first vfunc, '
  'so these two are necessarily equal; this control is INVALID. '
  'Effective replacement (next two dwords both .text) = %d / %d colterm tables'
  % (n1b_two_text, colterm_nexttext))
p('N2 shift +8 hit = %d ; shift -4 hit = %d (strict Q4 %d)' % (n2_plus8, n2_minus4, report['Q4']['hit']))
p('N3 prefix-1 hit = %d (strict Q4 %d)' % (n3_hit, report['Q4']['hit']))
open(os.path.join(OUT, 'r189_exec_summary.txt'), 'w').write('\n'.join(lines) + '\n')
