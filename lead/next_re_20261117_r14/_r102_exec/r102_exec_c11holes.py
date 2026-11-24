#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R102 EXEC -- independent behavioral forensics of the C11 holes.

Runs ONLY in sandboxes under /tmp.  Real tree is read-only.
Writes: r102_exec_c11holes.json next to this script.
"""
import os, sys, io, re, ast, json, hashlib, shutil, tempfile, subprocess
from pathlib import Path

REAL_ROOT = Path('/home/t628/projects/ra2-campaign-forge')
REAL_R14  = REAL_ROOT / 'lead' / 'next_re_20261117_r14'
OUT_DIR   = Path(__file__).resolve().parent
JSON_PATH = OUT_DIR / 'r102_exec_c11holes.json'

MUTABLE = {'check_disc.py', 'DISC_RECHECK.tsv', 'DISC_UNVERIFIABLE.tsv'}

CHECKS = []
def check(name, cond, detail=''):
    ok = bool(cond)
    CHECKS.append({'name': name, 'ok': ok, 'detail': str(detail)[:400]})
    print(('[PASS] ' if ok else '[FAIL] ') + name + (' :: ' + str(detail)[:160] if detail else ''))
    return ok

def read_text(p):
    return io.open(str(p), encoding='utf-8', newline='').read()

def write_text(p, s):
    io.open(str(p), 'w', encoding='utf-8', newline='').write(s)

# ------------------------------------------------------------------ sandbox
def make_sandbox(tag):
    """Faithful /tmp mirror: top-level entries symlinked; R14 is a real dir
    with only the 3 gate files as real copies.  Nothing in the real tree is
    written.  _r102 is symlinked like every other entry but never opened."""
    root = Path(tempfile.mkdtemp(prefix='r102exec_' + tag + '_'))
    lead = root / 'lead'; lead.mkdir()
    for e in REAL_ROOT.iterdir():
        if e.name == 'lead':
            continue
        (root / e.name).symlink_to(str(e))
    for e in (REAL_ROOT / 'lead').iterdir():
        if e.name == 'next_re_20261117_r14':
            continue
        (lead / e.name).symlink_to(str(e))
    r14real = lead / 'r14_exec'; r14real.mkdir()
    for e in REAL_R14.iterdir():
        dst = r14real / e.name
        if e.name in MUTABLE:
            shutil.copy2(str(e), str(dst))
        else:
            dst.symlink_to(str(e))
    (lead / 'next_re_20261117_r14').symlink_to(str(r14real))
    return {'root': root, 'r14real': r14real, 'gate': lead / 'next_re_20261117_r14' / 'check_disc.py'}

def parse_gate(sb):
    cp = subprocess.run([sys.executable, str(sb['gate'])], cwd=str(sb['root']),
                        stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out = cp.stdout.decode('utf-8', 'replace')
    err = cp.stderr.decode('utf-8', 'replace')
    flines = [l[len('  FAIL  '):] for l in out.splitlines() if l.startswith('  FAIL  ')]
    c11_per_id = []
    for f in flines:
        m = re.match(r'C11 id (\d+) claims recheck but has no valid', f)
        if m:
            c11_per_id.append(int(m.group(1)))
    c11b_drift = [f for f in flines if f.startswith('C11b loadable gap drifted')]
    tampered = [f for f in flines if 'frozen-class registry TAMPERED' in f]
    c7 = next((l for l in out.splitlines() if l.startswith('C7 live-checks')), '')
    notes = [l.strip() for l in out.splitlines() if l.startswith('  NOTE  ')]
    return {'exit': cp.returncode, 'fails': flines, 'c11_per_id_fails': sorted(c11_per_id),
            'c11b_drift': c11b_drift, 'tampered': tampered, 'c7_line': c7,
            'notes': notes, 'stderr': err[-500:]}

# ------------------------------------------------------------------ mutations
def mut_freeze_clear(sb, repin_sha):
    f = sb['r14real'] / 'DISC_UNVERIFIABLE.tsv'
    hdr = read_text(f).split('\n')[0]
    write_text(f, hdr + '\n')
    if repin_sha:
        h = hashlib.sha256(f.read_bytes()).hexdigest()
        g = sb['r14real'] / 'check_disc.py'
        s = read_text(g)
        s2, n = re.subn(r"FREEZE_SHA256 = '[0-9a-f]{64}'", "FREEZE_SHA256 = '%s'" % h, s)
        assert n == 1, 'FREEZE_SHA256 not found exactly once'
        write_text(g, s2)
        return h
    return None

def mut_sha_only(sb):
    """Criterion-free control: change ONLY the registered FREEZE_SHA256 to a
    different digest, leaving the TSV untouched.  Expected: a TAMPERED FAIL
    but NO per-id C11 FAIL, proving per-id FAILs in Q2a come from the removed
    exemption and not from the hash edit itself."""
    g = sb['r14real'] / 'check_disc.py'
    s = read_text(g)
    fake = '0' * 64
    s2, n = re.subn(r"FREEZE_SHA256 = '[0-9a-f]{64}'",
                    "FREEZE_SHA256 = '%s'" % fake, s)
    assert n == 1
    write_text(g, s2)
    return fake

def mut_break_id3_evidence(sb):
    """Copy id-3 product into a sandbox-only real dir, delete its discipline=3
    self-description line, and point col5 at the copy.  Grep anchors stay,
    so C7 remains green: the mutation lands on C11 alone."""
    rel_dir = 'lead\\next_re_20261117_r14\\_R102EXEC_PRODUCTS\\anchor_check_id3.txt'
    pd = sb['r14real'] / '_R102EXEC_PRODUCTS'; pd.mkdir(exist_ok=True)
    src = REAL_R14 / 'R17_R61_FACTINDEX_V58' / 'anchor_check.txt'
    txt = read_text(src)
    kept = [l for l in txt.split('\n') if not l.startswith('DISC_RECHECK discipline=3 ')]
    write_text(pd / 'anchor_check_id3.txt', '\n'.join(kept))
    dr = sb['r14real'] / 'DISC_RECHECK.tsv'
    ls = read_text(dr).split('\n')
    out = []
    for l in ls:
        if l.startswith('3\t'):
            c = l.split('\t'); c[4] = rel_dir; l = '\t'.join(c)
        out.append(l)
    write_text(dr, '\n'.join(out))
    return rel_dir

def mut_id3_col7_none(sb):
    dr = sb['r14real'] / 'DISC_RECHECK.tsv'
    ls = read_text(dr).split('\n')
    out = []
    for l in ls:
        if l.startswith('3\t'):
            c = l.split('\t'); c[6] = '无（本轮未回跑）'; l = '\t'.join(c)
        out.append(l)
    write_text(dr, '\n'.join(out))

def mut_repin_c11b(sb, ids):
    g = sb['r14real'] / 'check_disc.py'
    s = read_text(g)
    s2, n = re.subn(r'C11B_PIN_GAP = \[[^\]]*\]',
                    'C11B_PIN_GAP = [%s]' % ', '.join(str(i) for i in sorted(ids)), s)
    assert n == 1, 'C11B_PIN_GAP not found exactly once'
    write_text(g, s2)

# ------------------------------------------------------------------ static facts
def static_facts():
    dr = read_text(REAL_R14 / 'DISC_RECHECK.tsv')
    rows = [l.split('\t') for l in dr.split('\n')[1:] if l]
    fr = read_text(REAL_R14 / 'DISC_UNVERIFIABLE.tsv')
    frozen = sorted(int(c[0]) for l in fr.split('\n')[1:] if l
                    for c in [l.split('\t')] if c[0].strip().isdigit())
    yes = sorted(int(r[0]) for r in rows if r[6].strip().startswith('有'))
    no  = sorted(int(r[0]) for r in rows if r[6].strip().startswith('无'))
    sys.path.insert(0, str(REAL_R14))
    import recheck_verify as rv
    verifier = {}
    for r in rows:
        if r[6].strip().startswith('有'):
            ok, detail = rv.verify_recheck_line(str(REAL_ROOT), r)
            verifier[int(r[0])] = (bool(ok), str(detail)[:120])
    true_fail = sorted(i for i in yes if i not in frozen and verifier[i][0])
    # "true-fail-able" = claims-有, non-frozen, currently has a valid self-description
    # (i.e. C11 can FAIL on it once that evidence is broken).  Also record the
    # claims-有/non-frozen rows whose verifier currently fails.
    latent_fail = sorted(i for i in yes if i not in frozen and not verifier[i][0])
    src = read_text(REAL_R14 / 'check_disc.py')
    tree = ast.parse(src)
    loads = sorted(n.lineno for n in ast.walk(tree)
                   if isinstance(n, ast.Name) and n.id == 'C11_LANDABLE'
                   and isinstance(n.ctx, ast.Load))
    sentinel_loads = sum(1 for n in ast.walk(tree) if isinstance(n, ast.Name)
                         and n.id == 'R102_NONEXISTENT_CONTROL_SENTINEL'
                         and isinstance(n.ctx, ast.Load))
    landable = None
    for n in tree.body:
        if isinstance(n, ast.Assign) and any(isinstance(t, ast.Name)
                and t.id == 'C11_LANDABLE' for t in n.targets):
            landable = sorted(ast.literal_eval(n.value))
    pin = None
    for n in tree.body:
        if isinstance(n, ast.Assign) and any(isinstance(t, ast.Name)
                and t.id == 'C11B_PIN_GAP' for t in n.targets):
            pin = sorted(ast.literal_eval(n.value))
    return {'n_rows': len(rows), 'yes': yes, 'no': no, 'frozen': frozen,
            'true_fail': true_fail, 'latent_fail': latent_fail,
            'verifier': {str(k): v for k, v in sorted(verifier.items())},
            'ast_load_lines': loads, 'ast_load_count': len(loads),
            'sentinel_load_count': sentinel_loads,
            'landable': landable, 'pin': pin}

# =================================================================== main
def main():
    sf = static_facts()
    print('ROOT =', REAL_ROOT)
    print('static: rows=%d yes=%d no=%d frozen=%d' %
          (sf['n_rows'], len(sf['yes']), len(sf['no']), len(sf['frozen'])))

    # ---- positive control must be green before any mutation carries info ----
    s0 = make_sandbox('S0'); r0 = parse_gate(s0)
    check('S0_positive_control_exit0', r0['exit'] == 0, 'exit=%d' % r0['exit'])
    check('S0_positive_control_c11_zero_fails', r0['c11_per_id_fails'] == [],
          str(r0['c11_per_id_fails']))
    check('S0_no_r102_path_in_gate_inputs',
          ('_r102' not in read_text(REAL_R14 / 'DISC_RECHECK.tsv') and
           '_r102' not in read_text(REAL_R14 / 'DISC_UNVERIFIABLE.tsv')),
          'gate TSVs never reference _r102; sandbox symlink is never dereferenced')

    # ---- Q1 ----
    q1_true = sf['true_fail']
    q1_frozen = sorted(set(sf['frozen']) & set(sf['yes']))
    q1_none = sf['no']
    check('Q1_partition_covers_all_31',
          len(set(q1_true) | set(q1_frozen) | set(q1_none)) == sf['n_rows'] ==
          len(q1_true) + len(q1_frozen) + len(q1_none) and
          not (set(q1_true) & set(q1_frozen)) and
          not (set(q1_true) & set(q1_none)) and
          not (set(q1_frozen) & set(q1_none)),
          'true=%d frozen=%d none=%d sum=%d' %
          (len(q1_true), len(q1_frozen), len(q1_none),
           len(q1_true)+len(q1_frozen)+len(q1_none)))
    check('Q1_background_17_yes_14_no_12_frozen',
          (len(sf['yes']), len(sf['no']), len(sf['frozen'])) == (17, 14, 12))
    check('Q1_hard_shortcircuit_none_bucket_14', len(q1_none) == 14,
          str(q1_none))
    check('Q1_current_state_structurally_no_fail_26',
          len(q1_frozen) + len(q1_none) == 26)
    check('Q1_true_fail_bucket_5', q1_true == [3, 4, 22, 27, 28], str(q1_true))

    # ---- Q2: freeze removed, sha explicitly repinned (Lead-legal path) ----
    s2a = make_sandbox('Q2a'); newsha = mut_freeze_clear(s2a, True)
    r2a = parse_gate(s2a)
    check('Q2a_exit_is_1', r2a['exit'] == 1, 'exit=%d' % r2a['exit'])
    check('Q2a_C11_fail_set_exactly_original_frozen',
          r2a['c11_per_id_fails'] == sf['frozen'],
          'got=%s expected=%s' % (r2a['c11_per_id_fails'], sf['frozen']))
    check('Q2a_no_other_gate_failure',
          all(f.startswith('C11 id ') for f in r2a['fails']),
          str(r2a['fails'][:3]))
    # "no-criterion" control: change ONLY the sha constant, leave TSV intact.
    # Expected: TAMPERED fail but no per-id C11 fails -- so the 12 per-id FAILs
    # in Q2a are caused by removing the exemption, not by the hash edit.
    s2b = make_sandbox('Q2b'); mut_sha_only(s2b)
    r2b = parse_gate(s2b)
    check('Q2b_sha_only_control_no_per_id_C11_fails',
          r2b['c11_per_id_fails'] == [], str(r2b['c11_per_id_fails']))
    check('Q2b_sha_only_control_has_TAMPERED_only',
          len(r2b['tampered']) == 1 and len(r2b['fails']) == 1 and r2b['exit'] == 1,
          str(r2b['fails']))
    check('Q2_sha_edit_alone_never_creates_C11_fails',
          len(r2b['c11_per_id_fails']) == 0 and len(r2a['c11_per_id_fails']) == 12)
    check('Q2_repin_hash_is_header_only_hash',
          newsha == hashlib.sha256(
              (read_text(REAL_R14 / 'DISC_UNVERIFIABLE.tsv').split('\n')[0] + '\n').encode()).hexdigest(),
          newsha)

    # ---- Q3: evidence broken on id3, then col7 flipped to 无 ----
    s3a = make_sandbox('Q3a'); mut_break_id3_evidence(s3a); r3a = parse_gate(s3a)
    check('Q3a_broken_evidence_C11_FAIL_id3_only',
          r3a['c11_per_id_fails'] == [3], str(r3a['c11_per_id_fails']))
    check('Q3a_C7_stays_green', 'C7 live-checks passed 31 ; none-skipped 0' in r3a['c7_line'],
          r3a['c7_line'])
    check('Q3a_exit_is_1', r3a['exit'] == 1, 'exit=%d' % r3a['exit'])

    s3b = make_sandbox('Q3b')
    mut_break_id3_evidence(s3b); mut_id3_col7_none(s3b); r3b = parse_gate(s3b)
    check('Q3b_col7_none_removes_C11_FAIL_id3',
          3 not in r3b['c11_per_id_fails'], str(r3b['c11_per_id_fails']))
    check('Q3b_C7_stays_green', 'C7 live-checks passed 31 ; none-skipped 0' in r3b['c7_line'],
          r3b['c7_line'])
    check('Q3b_exit_still_1_because_C11b_pin_drift',
          r3b['exit'] == 1 and len(r3b['c11b_drift']) == 1,
          'exit=%d drift=%s' % (r3b['exit'], r3b['c11b_drift']))

    s3c = make_sandbox('Q3c')
    mut_break_id3_evidence(s3c); mut_id3_col7_none(s3c)
    mut_repin_c11b(s3c, [3, 11, 12, 13, 14, 15, 17, 26]); r3c = parse_gate(s3c)
    check('Q3c_after_repin_exit0', r3c['exit'] == 0, 'exit=%d' % r3c['exit'])
    check('Q3c_after_repin_C7_stays_green',
          'C7 live-checks passed 31 ; none-skipped 0' in r3c['c7_line'], r3c['c7_line'])

    # ---- Q4 ----
    check('Q4_AST_load_count_measured_2', sf['ast_load_count'] == 2,
          'lines=%s count=%d' % (sf['ast_load_lines'], sf['ast_load_count']))
    check('Q4_AST_control_sentinel_load_0', sf['sentinel_load_count'] == 0)
    check('Q4_landable_size_12', len(sf['landable']) == 12, str(sf['landable']))
    g_none = sorted(set(sf['landable']) & set(q1_none))
    g_true = sorted(set(sf['landable']) & set(q1_true))
    g_froz = sorted(set(sf['landable']) & set(q1_frozen))
    check('Q4_landable_gap_7_ids_are_none_bucket',
          g_none == [11, 12, 13, 14, 15, 17, 26], str(g_none))
    check('Q4_landable_gap_equals_C11B_PIN_GAP', g_none == sf['pin'],
          'gap=%s pin=%s' % (g_none, sf['pin']))
    check('Q4_landable_true_fail_5', g_true == [3, 4, 22, 27, 28], str(g_true))
    check('Q4_landable_frozen_0', g_froz == [], str(g_froz))

    n_checks = len(CHECKS); n_fail = sum(1 for c in CHECKS if not c['ok'])
    print('\nn_checks=%d n_fail=%d' % (n_checks, n_fail))

    payload = {
        'generated_by': str(Path(__file__).resolve()),
        'real_tree_read_only': True,
        'positive_control': {'exit': r0['exit'], 'c11_fails': r0['c11_per_id_fails']},
        'Q1': {'true_fail_can_FAIL': q1_true, 'frozen_exempt': q1_frozen,
               'claims_none_exempt': q1_none,
               'structurally_cannot_FAIL_current_state': len(q1_frozen)+len(q1_none),
               'hard_shortcircuit_C11_only': len(q1_none),
               'latent_fail_claims_yes_nonfrozen': sf['latent_fail'],
               'verifier_outcomes': sf['verifier']},
        'Q2': {'repinned_sha256': newsha,
               'exit': r2a['exit'], 'c11_fail_ids': r2a['c11_per_id_fails'],
               'all_fail_lines': r2a['fails'],
               'sha_only_control': {'exit': r2b['exit'], 'fails': r2b['fails'],
                                    'c11_per_id_fails': r2b['c11_per_id_fails']}},
        'Q3': {'baseline_exit': r0['exit'],
               'broken_evidence': {'exit': r3a['exit'],
                                   'c11_fail_ids': r3a['c11_per_id_fails'],
                                   'c7': r3a['c7_line']},
               'broken_plus_col7_none': {'exit': r3b['exit'],
                                         'c11_fail_ids': r3b['c11_per_id_fails'],
                                         'c11b_drift': r3b['c11b_drift'],
                                         'c7': r3b['c7_line']},
               'broken_plus_none_plus_repin': {'exit': r3c['exit'],
                                               'c7': r3c['c7_line']}},
        'Q4': {'ast_load_lines': sf['ast_load_lines'],
               'ast_load_count': sf['ast_load_count'],
               'control_sentinel_load_count': sf['sentinel_load_count'],
               'landable': sf['landable'], 'pin_gap': sf['pin'],
               'landable_in_true_fail': g_true, 'landable_in_frozen': g_froz,
               'landable_in_none': g_none},
        'checks': CHECKS, 'n_checks': n_checks, 'n_fail': n_fail,
    }
    write_text(JSON_PATH, json.dumps(payload, ensure_ascii=False, indent=2) + '\n')
    print('wrote', JSON_PATH)
    return 0 if n_fail == 0 else 2

if __name__ == '__main__':
    sys.exit(main())
