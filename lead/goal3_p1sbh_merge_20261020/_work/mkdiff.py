import re, sys

SRC = 'sbh.diff'
BASE = 'p1base.cpp'

raw = open(SRC, 'rb').read().decode('utf-8')
lines = raw.split('\r\n')
hdr = []
hunks = []
cur = None
for ln in lines:
    if ln.startswith('@@'):
        m = re.match(r'^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@(.*)$', ln)
        cur = {'old_start': int(m.group(1)),
               'old_len': int(m.group(2)) if m.group(2) is not None else 1,
               'new_len': int(m.group(4)) if m.group(4) is not None else 1,
               'tail': m.group(5), 'body': []}
        hunks.append(cur)
    elif cur is None:
        hdr.append(ln)
    else:
        cur['body'].append(ln)

print('hunks parsed:', len(hunks))

base = open(BASE, 'rb').read().decode('utf-8').split('\r\n')
if base and base[-1] == '':
    base = base[:-1]
print('base lines:', len(base))

def find_ctx(ctx):
    n = len(ctx)
    hits = [i + 1 for i in range(len(base) - n + 1)
            if all(base[i + k] == ctx[k] for k in range(n))]
    return hits

# ---------- hunk 1: rebuild against P1 base (bcrypt dedupe) ----------
h1 = hunks[0]
add1 = [l[1:] for l in h1['body'] if l[:1] == '+']
print('hunk1 original adds:')
for a in add1:
    print('   +', a)
drop = [a for a in add1 if 'bcrypt' in a]
keep = [a for a in add1 if 'bcrypt' not in a]
print('dedupe dropped (already present in P1 base):')
for a in drop:
    print('   -', a)
keep = ['// [SBH-GUARD] bcrypt.h / bcrypt.lib 已由 [VER-GATE V1] 引入（合批去重，不重复 include）'] + keep
ctx1 = base[0:5]
assert ctx1[0].startswith('#include "ra2render.h"')
assert ctx1[3].lstrip().startswith('#include <bcrypt.h>')
assert ctx1[4].lstrip().startswith('#pragma comment(lib, "bcrypt.lib")')
body1 = [' ' + l for l in ctx1] + ['+' + l for l in keep] + [' ' + base[5]]
hunks[0] = {'old_start': 1, 'old_len': 6, 'new_len': 6 + len(keep),
            'tail': '', 'body': body1}
print('hunk1 rebuilt: old 1,6 new 1,%d' % (6 + len(keep)))

# ---------- hunks 2..N: locate by context, recompute numbers only ----------
for idx in range(1, len(hunks)):
    h = hunks[idx]
    ctx = [l[1:] for l in h['body'] if l[:1] == ' ']
    hits = find_ctx(ctx)
    print('hunk%d ctx=%d original_old_start=%d hits=%s' % (idx + 1, len(ctx), h['old_start'], hits))
    if len(hits) != 1:
        sys.exit('hunk %d context not unique' % (idx + 1))
    h['new_old_start'] = hits[0]

added_total = 0
out = list(hdr)
print()
print('%-5s %-22s %-22s %s' % ('hunk', 'orig old_start', 'applied old_start', 'delta'))
for idx, h in enumerate(hunks):
    if idx == 0:
        old_start = 1
        new_start = 1
    else:
        old_start = h['new_old_start']
        new_start = old_start + added_total
    delta = old_start - h['old_start']
    hdrline = '@@ -%d,%d +%d,%d @@%s' % (old_start, h['old_len'], new_start, h['new_len'], h['tail'])
    print('%-5d %-22s %-22s %+d   %s' % (idx + 1, '%d,%d' % (h['old_start'], h['old_len']),
                                         '%d,%d' % (old_start, h['old_len']), delta, hdrline))
    added_total += h['new_len'] - h['old_len']
    out.append(hdrline)
    out.extend(h['body'])

data = '\r\n'.join(out) + '\r\n'
open('sbh_on_p1_input.diff', 'wb').write(data.encode('utf-8'))
print()
print('wrote sbh_on_p1_input.diff bytes=%d' % len(data.encode('utf-8')))
