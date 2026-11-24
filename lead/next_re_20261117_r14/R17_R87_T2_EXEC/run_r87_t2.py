#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R87-T2 executor: independently recompute gate experiment numbers.

- Reads live tree only. All writes go under this script's own output directory.
- Self-written copy routine (does NOT import _r87/decap2_r87.py).
- Produces sha256 manifests of the live R14 tree before and after all work.
"""
import os, io, re, sys, shutil, subprocess, hashlib, json

ROOT = '/home/t628/projects/ra2-campaign-forge'
SRC = os.path.join(ROOT, 'lead', 'next_re_20261117_r14')
OUT = os.path.dirname(os.path.abspath(__file__))
WORK = os.path.join(OUT, '_work')
MANIFEST_BEFORE = os.path.join(OUT, 'live_manifest.before.sha256')
MANIFEST_AFTER = os.path.join(OUT, 'live_manifest.after.sha256')
RAW = os.path.join(OUT, 'raw_results.json')


def sha256_file(path, chunk=1 << 20):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        while True:
            b = f.read(chunk)
            if not b:
                break
            h.update(b)
    return h.hexdigest()


def manifest():
    """Deterministic sha256 manifest of every file under live R14 + the ledger file."""
    entries = []
    for base, dirs, files in os.walk(SRC):
        dirs.sort()
        for fn in sorted(files):
            p = os.path.join(base, fn)
            entries.append((os.path.relpath(p, ROOT).replace(os.sep, '/'), sha256_file(p)))
    ledger = os.path.join(ROOT, 'lead', 'GOAL_THREE_TARGETS_20261018.md')
    entries.append(('lead/GOAL_THREE_TARGETS_20261018.md', sha256_file(ledger)))
    entries.sort()
    return entries


def write_manifest(path, entries):
    with io.open(path, 'w', encoding='utf-8', newline='\n') as f:
        for rel, digest in entries:
            f.write('%s  %s\n' % (digest, rel))


def assert_skips_unreferenced():
    """Hard-check: gate inputs must not reference any SKIP_DIRS product path."""
    gate_inputs = ['check_disc.py', 'recheck_verify.py', 'DISC_ESTABLISH.tsv',
                   'DISC_NS_MAP.tsv', 'DISC_RECHECK.tsv', 'DISC_UNVERIFIABLE.tsv']
    skips = ('R17_LEAD_BASELINE', 'R17_R87_T1_AUDIT')
    for fn in gate_inputs:
        p = os.path.join(SRC, fn)
        if not os.path.isfile(p):
            continue
        txt = io.open(p, encoding='utf-8', errors='replace').read()
        # Comments/docstrings mention R17_LEAD_BASELINE as provenance only; strip them
        # and assert no *code/data* path references a skipped directory.
        if fn.endswith('.py'):
            import io as _io, tokenize as _tok
            code_parts = []
            try:
                for tok in _tok.generate_tokens(_io.StringIO(txt).readline):
                    if tok.type in (_tok.COMMENT, _tok.STRING):
                        continue
                    code_parts.append(tok.string)
            except Exception:
                code_parts = [txt]
            code = '\n'.join(code_parts)
        else:
            code = '\n'.join(ln for ln in txt.split('\n') if not ln.strip().startswith('#'))
        for d in skips:
            assert d not in code, 'gate input %s references skipped dir %s (non-comment)' % (fn, d)
    # Also, no DISC_RECHECK.tsv product path may point into a skipped dir.
    for row in rows_of(SRC):
        for d in skips:
            assert d not in row[4], 'DISC_RECHECK product path references skipped dir %s: %s' % (d, row[4])


def build(dst):
    """Self-written copy of the gate-required subtree (referenced products + gate files).

    Excludes large dirs that the gate never reads: R17_LEAD_BASELINE, R17_R87_T1_AUDIT,
    R17_R72_T1_CLEANSCALE, _cards, __pycache__, and this executor's own output dir.
    Skipped products are verified to be unreferenced by gate inputs before copying.
    """
    # NOTE: R17_R72_T1_CLEANSCALE is NOT skipped -- discipline 16's product lives there.
    SKIP_DIRS = {'R17_LEAD_BASELINE', 'R17_R87_T1_AUDIT',
                 '_cards', '__pycache__', 'R17_R87_T2_EXEC'}
    if os.path.exists(dst):
        shutil.rmtree(dst)
    d14 = os.path.join(dst, 'lead', 'next_re_20261117_r14')
    os.makedirs(d14, exist_ok=True)
    for name in sorted(os.listdir(SRC)):
        s = os.path.join(SRC, name)
        if os.path.isdir(s):
            if name in SKIP_DIRS:
                continue
            shutil.copytree(s, os.path.join(d14, name))
        elif os.path.isfile(s):
            shutil.copy2(s, os.path.join(d14, name))
    shutil.copy2(os.path.join(ROOT, 'lead', 'GOAL_THREE_TARGETS_20261018.md'),
                 os.path.join(dst, 'lead', 'GOAL_THREE_TARGETS_20261018.md'))
    return d14


def gate(d14):
    r = subprocess.run([sys.executable, os.path.join(d14, 'check_disc.py')],
                       capture_output=True, text=True, cwd=d14)
    out = r.stdout + r.stderr
    m = re.search(
        r'C11 col7 machine-check: ok=(\d+) fail=(\d+) frozen-unverifiable=(\d+) claims-none=(\d+)',
        out)
    counts = tuple(int(x) for x in m.groups()) if m else None
    return {'exit': r.returncode, 'c11': counts, 'output': out,
            'fails': re.findall(r'(?m)^\s*FAIL\s+(.*)$', out)}


def rows_of(d14):
    p = os.path.join(d14, 'DISC_RECHECK.tsv')
    return [ln.split('\t') for ln in io.open(p, encoding='utf-8').read().split('\n')[1:] if ln.strip()]


def prod_path(d14, row):
    rel = row[4].strip().replace('\\', os.sep).replace('/', os.sep)
    # check_disc.py resolves ROOT as dirname^3 of itself = d14/../.. (the work root)
    work_root = os.path.dirname(os.path.dirname(d14))
    return os.path.join(work_root, rel) if not os.path.isabs(rel) else rel


def append_line(d14, disc, round_s, at_s, concl):
    row = [r for r in rows_of(d14) if int(r[0]) == disc][0]
    anchor = hashlib.sha256(row[3].encode('utf-8')).hexdigest()
    line = ('DISC_RECHECK discipline=%d round=%s at=%s anchors=sha256:%s conclusion=%s\n'
            % (disc, round_s, at_s, anchor, concl))
    p = prod_path(d14, row)
    assert os.path.isfile(p), 'product missing: %s' % p
    with io.open(p, 'a', encoding='utf-8', newline='\n') as f:
        f.write(line)
    return p, line


def change_at(d14, disc, new_at):
    """Change ONLY the at value of disc's existing self-description line (no other chars)."""
    row = [r for r in rows_of(d14) if int(r[0]) == disc][0]
    p = prod_path(d14, row)
    txt = io.open(p, encoding='utf-8', newline='').read()
    pat = re.compile(r'^(DISC_RECHECK discipline=%d round=R\d+ at=)\S+( anchors=sha256:[0-9a-f]{64} conclusion=\S+)$'
                     % disc, re.M)
    txt2, n = pat.subn(lambda m: m.group(1) + new_at + m.group(2), txt)
    assert n == 1, 'expected exactly 1 matching self-description line for disc %d, got %d' % (disc, n)
    # Preserve original newline convention exactly (use newline='' on read/write).
    with io.open(p, 'w', encoding='utf-8', newline='') as f:
        f.write(txt2)
    return p


def main():
    with io.open(MANIFEST_BEFORE.replace('.sha256', '.files.txt'), 'w', encoding='utf-8') as f:
        pass
    before = manifest()
    write_manifest(MANIFEST_BEFORE, before)
    assert_skips_unreferenced()
    results = {'baseline_live': None, 'posctl': None, 'A': None, 'B': None, 'C': None}
    try:
        # Baseline: live gate (read-only)
        d_live = SRC
        results['baseline_live'] = gate(d_live)

        # Copy sanity: unmodified copies run before each experiment.
        # A positive control for the copy technique itself.
        pos = build(os.path.join(WORK, 'posctl'))
        results['posctl'] = gate(pos)

        # Experiment A: append a compliant self-description line to a frozen discipline.
        # Pick discipline 1 from DISC_UNVERIFIABLE.tsv; its product is R14_COMMON.md.
        a = build(os.path.join(WORK, 'A'))
        a_pos = gate(a)  # unmodified copy positive control for A
        a_prod, a_line = append_line(a, 1, 'R55', '2026-11-22T17:45:00+08:00', 'UNKNOWN')
        a_gate = gate(a)
        results['A'] = {'positive_control': a_pos, 'product': a_prod, 'appended_line': a_line,
                        'gate': a_gate}

        # Experiment B: only change at values on existing lines for disciplines 3,4,22,27,28.
        b = build(os.path.join(WORK, 'B'))
        b_pos = gate(b)  # unmodified copy positive control for B
        b_changes = []
        for disc in (3, 4, 22, 27, 28):
            b_changes.append(change_at(b, disc, '2026-11-22T17:45:00+08:00'))
        b_gate = gate(b)
        results['B'] = {'positive_control': b_pos, 'changed_products': b_changes, 'gate': b_gate}

        # Experiment C: on top of B's copy, put discipline 3's at back to an out-of-window time.
        c = build(os.path.join(WORK, 'C'))
        for disc in (3, 4, 22, 27, 28):
            change_at(c, disc, '2026-11-22T17:45:00+08:00')
        c_pos = gate(c)  # positive control: B-state copy before the out-of-window mutation
        c_prod = change_at(c, 3, '2026-11-22T18:45:00+08:00')
        c_gate = gate(c)
        results['C'] = {'positive_control': c_pos, 'changed_product': c_prod, 'gate': c_gate}
    finally:
        after = manifest()
        write_manifest(MANIFEST_AFTER, after)
        results['manifest'] = {'before_file': MANIFEST_BEFORE,
                               'after_file': MANIFEST_AFTER,
                               'file_count_before': len(before),
                               'file_count_after': len(after),
                               'identical': before == after,
                               'before_digest': hashlib.sha256(
                                   ('\n'.join('%s  %s' % x for x in before)).encode()).hexdigest(),
                               'after_digest': hashlib.sha256(
                                   ('\n'.join('%s  %s' % x for x in after)).encode()).hexdigest()}
        # Strip bulky stdout for JSON compactness but keep full outputs in separate files.
        compact = {}
        for k, v in results.items():
            if isinstance(v, dict):
                compact[k] = {}
                for kk, vv in v.items():
                    if kk == 'output':
                        compact[k][kk] = '<see raw_output_%s.txt>' % k
                    elif isinstance(vv, dict):
                        compact[k][kk] = {x: ('<see raw_output_%s.txt>' % k if x == 'output' else y)
                                          for x, y in vv.items()}
                    else:
                        compact[k][kk] = vv
            else:
                compact[k] = v
        with io.open(RAW, 'w', encoding='utf-8', newline='\n') as f:
            f.write(json.dumps(compact, ensure_ascii=False, indent=2))
        # Full gate outputs
        def dump_output(key, obj):
            if not isinstance(obj, dict):
                return
            if 'output' in obj and isinstance(obj['output'], str):
                with io.open(os.path.join(OUT, 'raw_output_%s.txt' % key), 'w',
                             encoding='utf-8', newline='\n') as f:
                    f.write(obj['output'])
            for kk, vv in obj.items():
                if isinstance(vv, dict):
                    dump_output('%s_%s' % (key, kk), vv)
        dump_output('baseline_live', results)
        for k in ('posctl', 'A', 'B', 'C'):
            dump_output(k, results[k])

    # Console summary (numbers from scripts only)
    def line(label, d):
        print('%-24s exit=%d C11=%s' % (label, d['exit'], d['c11']))
    line('baseline_live', results['baseline_live'])
    line('posctl', results['posctl'])
    for k in ('A', 'B', 'C'):
        r = results[k]
        line(k + '_posctl', r['positive_control'])
        line(k + '_gate', r['gate'])
    m = results['manifest']
    print('manifest %d->%d files identical=%s' %
          (m['file_count_before'], m['file_count_after'], m['identical']))


if __name__ == '__main__':
    main()
