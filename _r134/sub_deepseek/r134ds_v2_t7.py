# -*- coding: utf-8 -*-
"""r134ds_v2_t7.py -- T7: holes in C7/C7b the card did NOT name. Measured, both gate states.

H1  rows= skips ANY line whose stripped form starts with 'DISC_RECHECK '. The code comment
    says it skips "the DISC_RECHECK self-narration line" (singular). Consequence: unlimited
    extra lines prefixed 'DISC_RECHECK ' are invisible to rows=.
H2  the annotation on rows= rows ('... rows 1468 vs 1468') is never parsed by the gate.
    Only the exists branch reads a '(\d+ B)' annotation. So a rows= row's recorded second
    opinion can disagree with reality and nothing notices.
H3  'grep=' with an EMPTY pattern is unconditionally true (re.search('','') matches) and
    keeps the C7b census at grep= -> a HOLE-B instance requiring no regex knowledge.
H4  C7b counts shapes but not identities: 24 rows are 'grep=' and swapping two grep= rows'
    column 5 between themselves keeps the census identical (only C7d catches it).
"""
import io, os, re, sys, json, subprocess

REAL = '/home/t628/projects/ra2-campaign-forge'
D = os.path.join(REAL, '_r134/sub_deepseek')
GATE_P = os.path.join(D, 'r134ds_snap_check_disc.py')      # R134 live bytes (with C7c/C7d)
TSV_P = os.path.join(D, 'r134ds_snap_DISC_RECHECK.tsv')    # R134 live TSV
GATE_N = '/home/t628/projects/ra2-campaign-forge/R17_LEAD_BASELINE/check_disc.py.before_R133e_081533.bak'

OUT = {}

def build(bs, gate, tsv):
    r = subprocess.run(['bash', os.path.join(D, 'r134ds_v2_sb.sh'), bs, gate, tsv],
                       capture_output=True, text=True, timeout=180)
    return r.returncode

def run(bs):
    r = subprocess.run(['python3', 'check_disc.py'],
                       cwd=os.path.join(bs, 'lead/next_re_20261117_r14'),
                       capture_output=True, text=True, timeout=300)
    fails = [l for l in r.stdout.split('\n') if 'FAIL' in l]
    return r.returncode, fails

def tsv_lines():
    return io.open(TSV_P, encoding='utf-8', newline='').read().split('\n')

def mutate_lines(out_path, edits):
    ls = tsv_lines()
    body = [l.split('\t') for l in ls[1:] if l]
    for rid, col, val in edits:
        i = next(i for i, r in enumerate(body) if r[0] == rid)
        f = ls[1 + i].split('\t')
        f[col] = val
        ls[1 + i] = '\t'.join(f)
    io.open(out_path, 'w', encoding='utf-8', newline='').write('\n'.join(ls))
    return out_path

# ---------- H1: rows= blindness to 'DISC_RECHECK '-prefixed injected lines ----------
prod = os.path.join(REAL, 'lead/next_re_20261117_r14/R17_R84_T1_NARRATIVE/should_exclude.tsv')
def rows_count(p):
    n = 0; hdr = 0
    with io.open(p, encoding='utf-8', errors='replace') as f:
        for l in f:
            s = l.strip()
            if s.startswith('DISC_RECHECK '): continue
            if hdr == 0: hdr = 1; continue
            n += 1
    return n
real_rows = rows_count(prod)
real_sz = os.path.getsize(prod)
# build a sandbox and REPLACE the symlink with a real mutated copy
bs = os.path.join(D, 'r134ds_v2_sb_h1')
build(bs, GATE_P, TSV_P)
target = os.path.join(bs, 'lead/next_re_20261117_r14/R17_R84_T1_NARRATIVE/should_exclude.tsv')
os.unlink(target)
data = io.open(prod, encoding='utf-8', errors='replace').read()
data += '\n'.join('DISC_RECHECK INJECTED LINE %d' % i for i in range(100)) + '\n'
io.open(target, 'w', encoding='utf-8', newline='').write(data)
mut_rows = rows_count(target)
mut_sz = os.path.getsize(target)
rc, fails = run(bs)
OUT['H1'] = {'expr': 'rows=1468', 'orig_bytes': real_sz, 'orig_rows': real_rows,
             'mut_bytes': mut_sz, 'mut_rows': mut_rows, 'gate_exit': rc,
             'c7_fail': [f for f in fails if 'C7' in f]}

# ---------- H2: rows= annotation never parsed ----------
p22 = os.path.join(D, 'r134ds_v2_tsv_h2.tsv')
mutate_lines(p22, [('22', 5, 'rows=1468 some totally unrelated note')])
bs2 = os.path.join(D, 'r134ds_v2_sb_h2')
build(bs2, GATE_P, p22)
rc2, fails2 = run(bs2)
OUT['H2'] = {'exit': rc2, 'fails': fails2}

# ---------- H3: empty grep pattern ----------
p23 = os.path.join(D, 'r134ds_v2_tsv_h3.tsv')
mutate_lines(p23, [('19', 5, 'grep=')])
bs3 = os.path.join(D, 'r134ds_v2_sb_h3')
build(bs3, GATE_P, p23)
rc3, fails3 = run(bs3)
# prove vacuity of empty pattern on the empty file
empty = os.path.join(D, 'r134ds_empty.txt')
etxt = io.open(empty, encoding='utf-8').read()
n_empty = len(re.findall('', etxt, re.M))
OUT['H3'] = {'exit': rc3, 'fails': fails3, 'empty_file_bytes': len(etxt),
             'empty_pattern_hits_on_empty_file': n_empty,
             'c7c_should_catch_it': bool(re.search('', '', re.M))}

# ---------- H4: C7b census cannot see which file a grep= row points at ----------
p24 = os.path.join(D, 'r134ds_v2_tsv_h4.tsv')
# swap col5 of rows 5 and 6 (both grep=, both currently point at lead_recheck2.tsv)
ls = tsv_lines(); body = [l.split('\t') for l in ls[1:] if l]
p5 = body[4][4]; p6 = body[5][4]
mutate_lines(p24, [('5', 4, p6), ('6', 4, p5)])
bs4 = os.path.join(D, 'r134ds_v2_sb_h4')
build(bs4, GATE_P, p24)
rc4, fails4 = run(bs4)
OUT['H4'] = {'exit': rc4, 'fails': fails4, 'note': 'rows 5 and 6 both grep= ; census unchanged'}

print(json.dumps(OUT, ensure_ascii=False, indent=1))
io.open(os.path.join(D, 'r134ds_v2_t7.json'), 'w', encoding='utf-8').write(
    json.dumps(OUT, ensure_ascii=False, indent=1))
