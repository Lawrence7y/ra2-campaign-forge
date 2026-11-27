#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R179-EXEC-PCT: independent recomputation of literal '%%' doubles in FACT_INDEX.
One command prints all six items plus positive/negative controls.
Only reads production files; controls operate on /tmp copies.
"""
import csv
import hashlib
import os
import re
import shutil
import sys

ROOT = '/home/t628/projects/ra2-campaign-forge'
R14 = os.path.join(ROOT, 'lead', 'next_re_20261117_r14')
CUR = os.path.join(R14, 'R17_R129_FACTINDEX_V561', 'FACT_INDEX.tsv')
WRITER = os.path.join(ROOT, '_r141', 'r141h_write_v539.py')


def read_bytes(path):
    with open(path, 'rb') as f:
        return f.read()


def parse_tsv(path):
    with open(path, 'r', encoding='utf-8', newline='') as f:
        rows = list(csv.reader(f, delimiter='\t'))
    return rows


def count_doubles_in_cell(s):
    # non-overlapping count of adjacent '%' pairs; for runs of N '%' this yields floor(N/2)
    return sum(1 for i in range(len(s) - 1) if s[i] == '%' and s[i + 1] == '%')


def count_doubles_in_rows(rows):
    total = 0
    per_cell = []
    for r_idx, row in enumerate(rows):
        for c_idx, cell in enumerate(row):
            n = count_doubles_in_cell(cell)
            if n:
                total += n
                per_cell.append((r_idx, c_idx, row[0] if row else '', n))
    return total, per_cell


print('=' * 72)
print('ITEM 1: current-version file facts (csv module, delimiter=TAB)')
print('=' * 72)
cur_bytes = read_bytes(CUR)
rows = parse_tsv(CUR)
print('path            :', CUR)
print('bytes           :', len(cur_bytes))
print('sha256          :', hashlib.sha256(cur_bytes).hexdigest())
print('rows (csv.reader):', len(rows))
# header?
print('row lengths     :', sorted(set(len(r) for r in rows)))
print('first row       :', rows[0] if rows else None)
print('column count    :', len(rows[0]) if rows else 0)

print()
print('=' * 72)
print('ITEM 2: per-cell literal "%%" double counts')
print('=' * 72)
total, per_cell = count_doubles_in_rows(rows)
print('total doubles   :', total)
print('(row_index, col_index, fact_id, count):')
for rec in per_cell:
    print('  ', rec)
# also aggregate by (fact_id, col index 1-based)
from collections import Counter
agg = Counter()
for r_idx, c_idx, fid, n in per_cell:
    agg[(fid, c_idx + 1)] += n
print('aggregated (fact_id, 1-based column, count):')
for k, v in sorted(agg.items()):
    print('  ', k, v)

print()
print('=' * 72)
print('ITEM 3: version spectrum 530..561')
print('=' * 72)
spect = {}
for ver in range(530, 562):
    hits = []
    for d in sorted(os.listdir(R14)):
        if re.fullmatch(r'R17_R\d+_FACTINDEX_V%d' % ver, d):
            hits.append(os.path.join(R14, d, 'FACT_INDEX.tsv'))
    if len(hits) != 1:
        print('V%d: dir count=%d %s' % (ver, len(hits), hits))
        spect[ver] = None
        continue
    p = hits[0]
    if not os.path.exists(p):
        print('V%d %s: MISSING FILE' % (ver, p))
        spect[ver] = None
        continue
    vr = parse_tsv(p)
    vt, vc = count_doubles_in_rows(vr)
    spect[ver] = (vt, len(vc), p)
    print('V%d %-42s doubles=%d cells_with_double=%d rows=%d' %
          (ver, os.path.basename(os.path.dirname(p)), vt, len(vc), len(vr)))
zeros = [v for v, t in spect.items() if t and t[0] == 0]
nonzero = [v for v, t in spect.items() if t and t[0] > 0]
missing = [v for v, t in spect.items() if t is None]
print('zero versions   :', sorted(zeros))
print('nonzero versions:', sorted(nonzero))
print('missing versions:', sorted(missing))
if nonzero:
    first = min(nonzero)
    vals = set(spect[v][0] for v in nonzero)
    print('first nonzero   : V%d' % first)
    print('nonzero counts  :', sorted(vals), '(constant)' if len(vals) == 1 else '(NOT constant)')
    # how many versions from first nonzero onward including it are unchanged
    tail = [v for v in range(first, 562) if v in spect and spect[v] and spect[v][0] == spect[first][0]]
    print('versions from V%d..V561 with same count as first nonzero: %d (%s)' %
          (first, len(tail), ','.join('V%d' % v for v in tail)))

print()
print('=' * 72)
print('ITEM 4: cause verification via _r141/r141h_write_v539.py')
print('=' * 72)
src_lines = open(WRITER, encoding='utf-8').read().split('\n')
print('writer path     :', WRITER)
print('writer total lines:', len(src_lines))
for i, ln in enumerate(src_lines, 1):
    if '%%' in ln:
        print('  line %3d: %s' % (i, ln.strip()))
print('--- interpretation basis ---')
print('Lines 64,65,67,82,83 contain literal "%%" inside Python string literals that are NOT')
print('formatted with %-interpolation (no trailing % operator on those expressions);')
print('they are concatenated string literals assigned to F29_ADD/F24_ADD (lines 53-78 and 80-91).')
print('Write path: line 108 cols[4] = cols[4] + " " + add; line 109 join; line 111 encode;')
print('lines 114-116 open(DST,"wb") + f.write(out) -- no %-formatting, no replacement, no folding.')
print('Therefore the two "%" bytes in each literal "%%" are written verbatim to the TSV.')

print()
print('=' * 72)
print('ITEM 5: byte ledger if each of the 5 doubles becomes a single "%"')
print('=' * 72)
print('current bytes   :', len(cur_bytes))
print('double count    :', total)
new_bytes = len(cur_bytes) - total
print('formula         : %d - %d*1 = %d' % (len(cur_bytes), total, new_bytes))
print('new bytes       :', new_bytes)

print()
print('=' * 72)
print('ITEM 6: arithmetic cross-check of percentages')
print('=' * 72)
checks = [
    ('6.03', 44470975, 737517286),
    ('3.64', 26846620, 737517286),
    ('88.5', 177, 200),
    ('81.82', 63, 77),
]
for stated, num, den in checks:
    val = num / den * 100
    print('stated=%-6s %d/%d -> %.6f%% -> rounded 2dp = %.2f%%  match=%s' %
          (stated, num, den, val, round(val, 2), ('%.2f' % round(val, 2)) == stated))

print()
print('=' * 72)
print('CONTROL A: inject one extra "%%" into a /tmp copy -> count must +1')
print('=' * 72)
tmpA = '/tmp/r179_exec_pct_control_A.tsv'
with open(tmpA, 'wb') as f:
    f.write(cur_bytes + b'%%')
rowsA = parse_tsv(tmpA)
tA, _ = count_doubles_in_rows(rowsA)
print('injected bytes  : b"%%" appended at EOF (becomes its own cell in a new row)')
print('base count      :', total)
print('after injection :', tA)
print('delta           :', tA - total)
print('CONTROL A %s' % ('PASS' if tA - total == 1 else 'FAIL'))
os.remove(tmpA)

print()
print('=' * 72)
print('CONTROL B: replace one existing double with a single "%" in /tmp copy -> count must -1')
print('=' * 72)
# find first row/col with a double via csv roundtrip (preserving structure)
rowsB = [list(r) for r in rows]
target = None
for ri, row in enumerate(rowsB):
    for ci, cell in enumerate(row):
        pos = cell.find('%%')
        if pos >= 0:
            target = (ri, ci, pos)
            break
    if target:
        break
if not target:
    print('CONTROL B FAIL: no double found')
    sys.exit(1)
ri, ci, pos = target
old_cell = rowsB[ri][ci]
rowsB[ri][ci] = old_cell[:pos] + '%' + old_cell[pos + 2:]
tmpB = '/tmp/r179_exec_pct_control_B.tsv'
with open(tmpB, 'w', encoding='utf-8', newline='') as f:
    w = csv.writer(f, delimiter='\t', lineterminator='\n')
    w.writerows(rowsB)
rowsB_read = parse_tsv(tmpB)
tB, _ = count_doubles_in_rows(rowsB_read)
print('modified cell   : row=%d col=%d char_pos=%d' % (ri, ci, pos))
print('base count      :', total)
print('after rewrite   :', tB)
print('delta           :', tB - total)
print('CONTROL B %s' % ('PASS' if tB - total == -1 else 'FAIL'))
os.remove(tmpB)

print()
print('=== ALL ITEMS PRINTED ===')
