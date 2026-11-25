# -*- coding: utf-8 -*-
"""r134ds_mktsv.py -- build sandbox TSV variants. Writes ONLY under _r134/sub_deepseek/.
usage: r134ds_mktsv.py <variant>
"""
import io, os, sys

ROOT = '/home/t628/projects/ra2-campaign-forge'
SRC = os.path.join(ROOT, 'lead/next_re_20261117_r14/DISC_RECHECK.tsv')
OUT = os.path.join(ROOT, '_r134/sub_deepseek')

cur = io.open(SRC, encoding='utf-8', newline='').read()
lines = cur.split('\n')

# Every variant starts from the RECONSTRUCTED R133 state, not the live R134 state,
# so that row 20's self-registration does not contaminate the measurement.
_b0 = [l.split('\t') for l in lines[1:] if l]
_i20 = next(i for i, r in enumerate(_b0) if r[0] == '20')
_f = lines[1 + _i20].split('\t')
_f[5] = "grep=(?m)^GATE_VER = 'R133'"
lines[1 + _i20] = '\t'.join(_f)
R133 = list(lines)

def setrow(idx, col, val, ls=None):
    """idx = 0-based body index; col = 0-based column."""
    ls = list(lines) if ls is None else ls
    k = 1 + idx
    f = ls[k].split('\t')
    f[col] = val
    ls[k] = '\t'.join(f)
    return ls

def write(name, ls):
    p = os.path.join(OUT, name)
    io.open(p, 'w', encoding='utf-8', newline='').write('\n'.join(ls))
    print(p)

v = sys.argv[1]
body = [l.split('\t') for l in lines[1:] if l]

if v == 'r133':
    write('r134ds_tsv_r133.tsv', R133)

elif v == 't2':
    # HOLE A: move row 19 col5 from R17_R75_T2_DRIFT\REPORT.md to R17_R78_T1_RECLASS\REPORT.md
    # (both are in row 19's TRUE set, size 4)
    i19 = next(i for i, r in enumerate(body) if r[0] == '19')
    ls = setrow(i19, 4, r'lead\next_re_20261117_r14\R17_R78_T1_RECLASS\REPORT.md', list(R133))
    write('r134ds_tsv_t2.tsv', ls)

elif v == 't2b':
    # HOLE A, second instance: row 5 (set size 2) moved to R14_COMMON.md
    i5 = next(i for i, r in enumerate(body) if r[0] == '5')
    ls = setrow(i5, 4, r'lead\next_re_20261117_r14\R14_COMMON.md', list(R133))
    write('r134ds_tsv_t2b.tsv', ls)

elif v == 't3':
    # HOLE B: append a vacuously-true alternation to row 19 col6
    i19 = next(i for i, r in enumerate(body) if r[0] == '19')
    ls = setrow(i19, 5, 'grep=逐字节闭合|(?m:^)', list(R133))
    write('r134ds_tsv_t3.tsv', ls)

elif v == 't3b':
    # stronger HOLE B: replace the pattern entirely with a vacuous one, same first token
    i19 = next(i for i, r in enumerate(body) if r[0] == '19')
    ls = setrow(i19, 5, 'grep=(?m:^)', list(R133))
    write('r134ds_tsv_t3b.tsv', ls)

elif v == 't4a':
    # NEGATIVE CONTROL: change first token grep= -> exists on row 19
    i19 = next(i for i, r in enumerate(body) if r[0] == '19')
    ls = setrow(i19, 5, 'exists (逐字节闭合)', list(R133))
    write('r134ds_tsv_t4a.tsv', ls)

elif v == 't4b':
    # NEGATIVE CONTROL: point row 19 col5 at a file its expression is FALSE on
    i19 = next(i for i, r in enumerate(body) if r[0] == '19')
    ls = setrow(i19, 4, r'lead\next_re_20261117_r14\R17_R61_FACTINDEX_V58\anchor_check.txt', list(R133))
    write('r134ds_tsv_t4b.tsv', ls)

elif v == 'empty':
    write('r134ds_empty.txt', [])
else:
    sys.exit('unknown variant')
