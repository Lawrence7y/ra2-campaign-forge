# -*- coding: utf-8 -*-
"""M82 pre-write safety checks (read only)."""
import os, re, json
R14 = r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14'
RESOLVE = os.path.join(R14, 'EVID_RESOLVE', 'resolve.tsv')
PAN = os.path.join(R14, 'COVERAGE', 'PANEL.md')
SPLIT_KEEP_RE = re.compile(r'([;,|])')
SPLIT_RE = re.compile(r'[;,|]')
ABS_RE = re.compile(r'^(?:[A-Za-z]:[\\/]|\\\\|/)')
LINESPEC_RE = re.compile(r':(?:\d+[0-9A-Za-z\-]*|0x[0-9A-Fa-f\-]+)$')

def strip_anchor(part):
    p = part.split('#', 1)[0].strip()
    if not ABS_RE.match(p):
        p = LINESPEC_RE.sub('', p).strip()
    return p

rows = []
for raw in open(RESOLVE, 'r', encoding='utf-8').read().split('\n')[1:]:
    if not raw.strip():
        continue
    f = raw.split('\t')
    if f[5] == 'R_MISSING':
        rows.append(f[4])

bad = []
for val in rows:
    for tok in SPLIT_KEEP_RE.split(val):
        if tok == '' or SPLIT_RE.fullmatch(tok):
            continue
        if tok != tok.strip():
            bad.append((val, repr(tok)))
        rp = strip_anchor(tok)
        if not tok.startswith(rp):
            bad.append((val, 'prefix mismatch', repr(tok), repr(rp)))
print('parts with whitespace / prefix issues:', len(bad))
for b in bad[:20]:
    print(' ', b)

# PANEL anchors
plines = open(PAN, 'r', encoding='utf-8').read().split('\n')
s = next(i for i,x in enumerate(plines) if 'M81 披露' in x)
e = next(i for i,x in enumerate(plines) if x.startswith('> ⇒ **引用 `[已证]` = 1,654 时必须带此限定'))
print('M81 start idx(0-based)=%d (L%d), end idx=%d (L%d), span=%d' % (s, s+1, e, e+1, e-s))
print('end line tail:', repr(plines[e][-40:]))
print('next line L%d head:' % (e+2), repr(plines[e+1][:40]))
