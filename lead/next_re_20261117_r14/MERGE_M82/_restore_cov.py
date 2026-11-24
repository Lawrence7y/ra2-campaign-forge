# -*- coding: utf-8 -*-
"""Restore coverage.tsv to BEFORE state by reversing the M82 annotation on col6."""
import os, hashlib
COV = r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\COVERAGE\coverage.tsv'
EXPECT_SHA = '4245191f94c47b6a291a29d5c85666dcc043c23410efa5faa6b54ce6e068372e'
EXPECT_LEN = 3954098
MARK = ';M82 指针修复：原记 '
SEP = '（缺卡目录），实为 '

b = open(COV, 'rb').read()
text = b.decode('utf-8')
lines = text.split('\n')
restored = 0
for i in range(1, len(lines)):
    f = lines[i].split('\t')
    if len(f) != 8:
        continue
    v = f[5]
    if MARK not in v:
        continue
    pos = v.index(MARK)
    new_main = v[:pos]                 # keep (sanity)
    rest = v[pos + len(MARK):]
    if SEP not in rest:
        raise RuntimeError('annotation SEP missing at line %d' % (i+1))
    old = rest[:rest.index(SEP)]
    # verify tail equals new_main
    tail = rest[rest.index(SEP) + len(SEP):]
    assert tail == new_main, ('tail mismatch at line %d' % (i+1), tail[:60], new_main[:60])
    f[5] = old
    lines[i] = '\t'.join(f)
    restored += 1

out = '\n'.join(lines).encode('utf-8')
print('restored rows:', restored)
print('len', len(out), 'sha', hashlib.sha256(out).hexdigest())
assert len(out) == EXPECT_LEN, 'length mismatch'
assert hashlib.sha256(out).hexdigest() == EXPECT_SHA, 'sha mismatch'
with open(COV, 'wb') as fh:
    fh.write(out)
print('coverage.tsv RESTORED to BEFORE state')
