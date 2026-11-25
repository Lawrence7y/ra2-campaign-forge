# -*- coding: utf-8 -*-
"""r134ds_t3b_proof.py -- prove the appended branch is vacuous: on an EMPTY file,
the ORIGINAL expression yields 0 hits and the AUGMENTED expression yields >= 1."""
import io, re, sys, os

ROOT = '/home/t628/projects/ra2-campaign-forge'
EMPTY = os.path.join(ROOT, '_r134/sub_deepseek/r134ds_empty.txt')
txt = io.open(EMPTY, encoding='utf-8').read()
assert txt == '', 'empty probe file is not empty: %r' % txt
print('probe file bytes = %d' % os.path.getsize(EMPTY))

orig = u'逐字节闭合'
aug = u'逐字节闭合|(?m:^)'
for name, pat in (('ORIGINAL grep=逐字节闭合', orig), ('AUGMENTED grep=逐字节闭合|(?m:^)', aug)):
    n = len(re.findall(pat, txt, re.M))
    print('%-34s hits on empty = %d' % (name, n))

# full gate expressions as they appear in column 6 (first token stripped)
o_expr = u'grep=逐字节闭合'
a_expr = u'grep=逐字节闭合|(?m:^)'
for name, expr in (('ORIGINAL', o_expr), ('AUGMENTED', a_expr)):
    pat = expr[len('grep='):].strip()
    n = len(re.findall(pat, txt, re.M))
    ok = (n >= 1)
    print('%s full col6 %-28r -> hits=%d gate_verdict=%s' % (name, expr, n, ok))

# also: does the AUGMENTED pattern still hit the real product file?
real = os.path.join(ROOT, 'lead/next_re_20261117_r14/R17_R75_T2_DRIFT/REPORT.md')
rt = io.open(real, encoding='utf-8', errors='replace').read()
print('real product hits: original=%d augmented=%d'
      % (len(re.findall(orig, rt, re.M)), len(re.findall(aug, rt, re.M))))

# DELETE-the-pattern proof: augmented pattern is true on a file the original rejects
other = os.path.join(ROOT, 'lead/next_re_20261117_r14/R17_R61_FACTINDEX_V58/anchor_check.txt')
ot = io.open(other, encoding='utf-8', errors='replace').read()
print('FALSE-file hits: original=%d augmented=%d'
      % (len(re.findall(orig, ot, re.M)), len(re.findall(aug, ot, re.M))))
