#!/usr/bin/env python3
# R130 r130d: does C11's claims-none check expression have DISCRIMINATING POWER?
#
# R129 wired the claims-none branch to actually run its check expression
# (check_disc.py around line 322). The claim made there was "14 rows, 14/14 hold on the
# real product, 0/14 hold on an empty product => discriminating, zero false positives".
#
# This script re-derives that claim for the CURRENT table (19 claims-none rows) and,
# critically, measures something R129 did not: for each expression, does it hold on the
# real product *and* is it coupled to the discipline it is supposed to certify? A grep
# for a phrase that the product contains for unrelated reasons has resolving power
# against an empty file but ZERO power against a wrong-but-nonempty product.
#
# Control design:
#   real   : the declared product
#   empty  : empty file            (proves it is not trivially true)
#   mutant : a product with the expression's own grep target removed / row count changed
#            (proves it is coupled to content it claims to certify)
#
# Memory: pure text, no disassembly. Bounded reads.
import io
import json
import os
import re
import sys

ROOT = '/home/t628/projects/ra2-campaign-forge'
R14 = os.path.join(ROOT, 'lead/next_re_20261117_r14')
TSV = os.path.join(R14, 'DISC_RECHECK.tsv')
OUT = os.path.join(ROOT, '_r130/r130d_tautology.json')

# mirrors check_disc.run_expr for the three forms used by claims-none rows
ROWS_EXPR = re.compile(r'^rows=(\d+)\b')


def eval_expr(txt, expr):
    """Apply the check_disc expression semantics to a supplied text."""
    head = expr.split(' ')[0]
    if head.startswith('grep='):
        pat = expr[len('grep='):].strip()
        try:
            return len(re.findall(pat, txt, re.M)) >= 1
        except re.error:
            return False
    if head.startswith('grepcount='):
        rest = expr[len('grepcount='):].strip()
        m0 = re.match(r'^(.*)=(\d+)$', rest, re.S)
        if not m0:
            return False
        try:
            return len(re.findall(m0.group(1), txt, re.M)) == int(m0.group(2))
        except re.error:
            return False
    m3 = ROWS_EXPR.match(head)
    if m3:
        # same rule as check_disc: skip header row and DISC_RECHECK self-lines
        n = 0
        hdr = 0
        for ln in txt.splitlines():
            s = ln.strip()
            if not s:
                continue
            if s.startswith('DISC_RECHECK '):
                continue
            if '\t' in ln and hdr == 0:
                hdr = 1
                continue
            n += 1
        return n == int(m3.group(1))
    return None      # unsupported form -> caller reports


def mutate(txt, expr):
    """Break the content the expression certifies, to test coupling."""
    head = expr.split(' ')[0]
    if head.startswith('grep='):
        pat = expr[len('grep='):].strip()
        try:
            return re.sub(pat, 'ZZQDELETEDZZ', txt, count=0, flags=re.M)
        except re.error:
            return txt
    if head.startswith('grepcount='):
        rest = expr[len('grepcount='):].strip()
        m0 = re.match(r'^(.*)=(\d+)$', rest, re.S)
        if not m0:
            return txt
        try:
            return re.sub(m0.group(1), 'ZZQDELETEDZZ', txt, count=1, flags=re.M)
        except re.error:
            return txt
    m3 = ROWS_EXPR.match(head)
    if m3:
        # drop one data row -> count no longer matches
        lines = txt.splitlines()
        out, hdr = [], 0
        dropped = False
        for ln in lines:
            s = ln.strip()
            if s and not s.startswith('DISC_RECHECK ') and '\t' in ln and hdr == 0:
                hdr = 1
                out.append(ln)
                continue
            if not dropped and s and not s.startswith('DISC_RECHECK '):
                dropped = True
                continue
            out.append(ln)
        return '\n'.join(out)
    return txt


def main():
    rows = [l.rstrip('\n').split('\t')
            for l in io.open(TSV, encoding='utf-8')]
    body = [r for r in rows[1:] if r and r[0].strip().isdigit()]
    res = []
    for r in body:
        if r[6].strip().startswith('有'):
            continue
        did, path, expr = r[0].strip(), r[4].strip(), r[5].strip()
        ap = os.path.join(ROOT, path.replace('\\', '/'))
        rec = {'id': did, 'expr': expr, 'path': path}
        if not os.path.isfile(ap):
            rec['real_ok'] = None
            rec['detail'] = 'FILE_MISSING'
            res.append(rec)
            continue
        txt = io.open(ap, encoding='utf-8', errors='replace').read()
        real = eval_expr(txt, expr)
        empty = eval_expr('', expr)
        mut = mutate(txt, expr)
        mutant = eval_expr(mut, expr)
        rec.update({
            'real_ok': real, 'empty_ok': empty, 'mutant_ok': mutant,
            'discriminates_vs_empty': (real is True and empty is False),
            'couples_to_content': (real is True and mutant is False),
        })
        res.append(rec)

    n = len(res)
    summary = {
        'claims_none_rows': n,
        'supported_forms': sum(1 for x in res if x.get('real_ok') is not None),
        'unsupported_or_missing': sum(1 for x in res
                                      if x.get('real_ok') is None),
        'real_holds': sum(1 for x in res if x.get('real_ok') is True),
        'empty_also_holds_TAUTOLOGY': sum(1 for x in res
                                          if x.get('empty_ok') is True),
        'mutant_still_holds_DECOUPLED': sum(1 for x in res
                                            if x.get('couples_to_content') is False
                                            and x.get('real_ok') is True),
        'both_controls_pass': sum(1 for x in res
                                  if x.get('discriminates_vs_empty')
                                  and x.get('couples_to_content')),
    }
    rec = {'summary': summary, 'rows': res}
    with io.open(OUT, 'w', encoding='utf-8') as f:
        json.dump(rec, f, ensure_ascii=False, indent=1)

    print(json.dumps(summary, ensure_ascii=False, indent=1))
    for x in res:
        print(' id', x['id'], 'real', x.get('real_ok'),
              'empty', x.get('empty_ok'), 'mutant', x.get('mutant_ok'),
              '|', x['expr'][:52])
    return 0


if __name__ == '__main__':
    sys.exit(main())
