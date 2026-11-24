# -*- coding: utf-8 -*-
"""D25 source verification. Never execute/import the mother harness or B2 code.
Run: python -I -X utf8 D:/Project/ra2-campaign-forge/lead/d25_ruling_20261106/_d25_facts.py
Only output file beside this script is written. Synthetic models are hand transcribed.
"""
import ast
import contextlib
import hashlib
import io
from pathlib import Path
import re
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
B2 = 'lead/re_line_20261105/B1_HARNESS_PATCH/B2_FIX_DESIGN.md'
MOTHER = 'out/re_work/work_chain/CONTINUE_20261003/lead/qc151_u0400_trip/qc151_trip.py'
PRE = 'lead/b2_preaudit_20261106/B2_PREAUDIT.md'
REVIEW = 'lead/b2_preaudit_20261106/review/B2_PREAUDIT_REVIEW.md'
CAND = 'lead/re_line_20261105/W11_EXCEPT_FRESHNESS/candidate/except_freshness.py'
PD = 'lead/PENDING_DECISIONS.md'
SOURCES = [B2, MOTHER, PRE, REVIEW, CAND, PD,
           'lead/control_20261106/D25_ENTRY_DRAFT.md',
           'lead/re_line_20261105/A1_ERRATA_MAP/A1_ERRATA_MAP.md',
           'lead/a_residual_20261106/A_RESIDUAL_REFERENCES.md',
           'lead/re_line_20261105/D24_RULING/RULING_D24.md',
           'lead/nextstep_plan_20261106/NEXT_STEPS_20261106.md']

def raw(p):
    return (ROOT / p).read_bytes()

def text(p):
    return raw(p).decode('utf-8-sig')

def fingerprint(p):
    b = raw(p)
    return hashlib.sha256(b).hexdigest(), len(b)

def excerpt(p, a, b):
    for n, line in enumerate(text(p).splitlines(), 1):
        if a <= n <= b:
            print(f'{p}:{n}: {line}')

class OwnScope(ast.NodeVisitor):
    def __init__(self):
        self.returns = []
    def visit_Return(self, node):
        self.returns.append(node.lineno)
    def visit_FunctionDef(self, node):
        pass
    visit_AsyncFunctionDef = visit_FunctionDef
    def visit_Lambda(self, node):
        pass
    def visit_ClassDef(self, node):
        pass

def synthetic_b2(pre_snapshot, now_exists, post_sha='oldsha', post_mtime=100.0):
    # Hand transcription of B2:133-154 with filesystem observations supplied as values.
    pre = dict(pre_snapshot or {})
    pre_exists = bool(pre.get('exists'))
    if not now_exists:
        return ('vanished' if pre_exists else 'absent_both',
                'high' if pre_exists else 'n/a')
    if not pre_exists:
        return ('new_first_appearance', 'high')
    pre_sha = pre.get('sha256')
    pre_mtime = pre.get('mtime_pre')
    if pre_sha is not None and pre_sha != post_sha:
        return ('new_write', 'high')
    if pre_mtime is not None and post_mtime != pre_mtime:
        return ('rewritten_same_content', 'low' if post_mtime < pre_mtime else 'medium')
    return ('leftover_unchanged', 'high')

def synthetic_no_assignment(path):
    try:
        if path == 'early':
            return 7
        if path == 'exception':
            raise ValueError('original')
    finally:
        return _pre_freshness_snapshot

def synthetic_normal_assignment(path):
    try:
        if path == 'early':
            return 7
        if path == 'exception':
            raise ValueError('original')
        _pre_freshness_snapshot = {}
    finally:
        return _pre_freshness_snapshot

def run():
    before = {p: fingerprint(p) for p in SOURCES}
    for p in SOURCES:
        print('FINGERPRINT', p, *before[p])
    print('CHECK F1')
    assert before[B2] == ('deacab49b2bc02f44ecf629036427153affee422c2059c31ecc1471b1f311a5f', 11638)
    assert re.search(r'^verdict: NO$', text(PRE), re.M)
    excerpt(PRE, 3, 10)
    excerpt(PRE, 17, 22)
    print('CHECK F2')
    b2 = text(B2)
    occurrences = [(i, l) for i, l in enumerate(b2.splitlines(), 1) if '_pre_freshness_snapshot' in l]
    assigns = [(i, l) for i, l in enumerate(b2.splitlines(), 1)
               if re.search(r'\b_pre_freshness_snapshot\s*(?::[^=\n]+)?\s*=(?!=)', l)]
    print('SNAPSHOT_OCCURRENCES', occurrences)
    print('SNAPSHOT_ASSIGNMENTS', assigns)
    assert [i for i, _ in occurrences] == [35, 63, 200] and not assigns
    excerpt(PRE, 28, 32)
    print('CHECK F3')
    mother = ast.parse(text(MOTHER), filename=MOTHER)
    main = next(n for n in mother.body if isinstance(n, ast.FunctionDef) and n.name == 'main')
    walker = OwnScope()
    for node in main.body:
        walker.visit(node)
    early = sorted(n for n in walker.returns if n < 6387)
    print('MAIN_EARLY_RETURNS_BEFORE_6387', early)
    assert early == [6340, 6349, 6361, 6374, 6377]
    tr = next(n for n in main.body if isinstance(n, ast.Try) and n.lineno == 6313)
    print('TRY', tr.lineno, 'FINALLY_FIRST_STATEMENT', tr.finalbody[0].lineno)
    print('FINALLY_HEADER', text(MOTHER).splitlines()[7037])
    calls = [n.lineno for n in ast.walk(main) if isinstance(n, ast.Call)
             and isinstance(n.func, ast.Name) and n.func.id == 'finalize_trip']
    print('MAIN_FINALIZE_CALLS', calls)
    assert calls == [7117] and text(MOTHER).splitlines()[7037].strip() == 'finally:'
    excerpt(MOTHER, 6293, 6306)
    excerpt(MOTHER, 6385, 6388)
    excerpt(MOTHER, 7117, 7134)
    print('CHECK F4')
    hunks = [(i, l) for i, l in enumerate(b2.splitlines(), 1) if l.startswith('@@')]
    print('B2_HUNKS', hunks)
    assert [i for i, _ in hunks] == [43, 52, 75, 128]
    print('B2_COPY_NAME_LINES', [(i, l) for i, l in enumerate(b2.splitlines(), 1)
                                  if 'copy_post_except_evidence' in l or '5939' in l])
    excerpt(MOTHER, 5938, 5939)
    print('CHECK F5')
    for token in ('freshness_confidence', 'freshness_note', 'captured_at_iso'):
        print('B2_TOKEN_COUNT', token, b2.count(token))
        assert b2.count(token) == 0
    print('B2_FRESHNESS_VERDICT_LINES', [i for i, l in enumerate(b2.splitlines(), 1) if 'freshness_verdict' in l])
    print('CHECK F6')
    for a, b in [(140, 157), (187, 207)]:
        excerpt(CAND, a, b)
    for token in ('error_pre_snapshot', 'is_new'):
        print('B2_TOKEN_COUNT', token, b2.count(token))
        assert b2.count(token) == 0
    print('CHECK F7')
    assert before[MOTHER] == ('517889c68f037ab63f9c38300e627d34457b7be9fab0362e425783c7ec5ba636', 399508)
    print('MOTHER_HASH_AND_BYTES_MATCH', before[MOTHER])
    print('CHECK F8')
    pd = text(PD)
    ids = sorted(set(int(s) for s in re.findall(r'\bD-(\d+)\b', pd)))
    pending = pd.split('## 待裁决事项（当前）', 1)[1].split('## 已裁决记录', 1)[0]
    entries = re.findall(r'^- \*\*D-(\d+)（', pending, re.M)
    print('ALL_D_IDS', ids, 'MAX_D', max(ids), 'PENDING_ENTRY_IDS', entries)
    assert max(ids) == 24 and entries == ['13', '14', '24']
    print('CORE_CHECKS=8/8')
    print('ADDITIONAL: hand-transcribed B2 synthetic matrix, NOT integrated harness')
    for pre in [None, {}, {'exists': False}, {'exists': True, 'error': 'synthetic'}]:
        for exists in (True, False):
            print('B2_SYNTH', repr(pre), 'post_exists=', exists, '=>', synthetic_b2(pre, exists))
    print('ADDITIONAL: undefined-name distinction, synthetic Python only')
    for function in (synthetic_no_assignment, synthetic_normal_assignment):
        for path in ('early', 'exception', 'normal'):
            try:
                value = function(path)
                print('BINDING_SYNTH', function.__name__, path, '=>', repr(value))
            except Exception as exc:
                print('BINDING_SYNTH', function.__name__, path, '=>', type(exc).__name__,
                      'context=', type(exc.__context__).__name__ if exc.__context__ else None)
    print('ADDITIONAL: authoritative high IDs and review issue count')
    print('HIGH_IDS', re.findall(r'^- \*\*(N\d+) .*severity=high', text(PRE), re.M))
    review_issues = text(REVIEW).split('## 3 复核判定的问题项（issues）', 1)[1].split('## 4 ', 1)[0]
    print('REVIEW_ENUMERATED_ISSUES', re.findall(r'^([1-9]\d*)\. \*\*', review_issues, re.M))
    excerpt(REVIEW, 9, 18)
    excerpt(REVIEW, 158, 158)
    print('REVIEW_HASH_BINDS_CURRENT_PREAUDIT', before[PRE][0] in text(REVIEW))
    print('ADDITIONAL: background excerpt locations')
    for p, pattern in [
        ('lead/re_line_20261105/A1_ERRATA_MAP/A1_ERRATA_MAP.md', r'总判'),
        ('lead/a_residual_20261106/A_RESIDUAL_REFERENCES.md', r'17|12|5'),
        ('lead/nextstep_plan_20261106/NEXT_STEPS_20261106.md', r'^### N-[278] '),
    ]:
        hits = [(i, line) for i, line in enumerate(text(p).splitlines(), 1) if re.search(pattern, line)]
        for i, line in hits[:10]:
            print(f'{p}:{i}: {line}')
    after = {p: fingerprint(p) for p in SOURCES}
    changed = [p for p in SOURCES if before[p] != after[p]]
    print('READ_ONLY_SOURCES_CHANGED', changed)
    assert not changed
    print('UNVERIFIED: W11 14-test suite not rerun; full B2 integration/runtime; crash attribution; B-vs-A effort or smaller change surface; D-line zero risk; live workflow states')
    print('RESULT=PASS; eight core facts reproduced; draft overstatements reported separately')

if __name__ == '__main__':
    output = io.StringIO()
    status = 0
    with contextlib.redirect_stdout(output), contextlib.redirect_stderr(output):
        try:
            run()
        except Exception:
            import traceback
            traceback.print_exc()
            status = 1
        print('SCRIPT_EXIT', status)
    content = output.getvalue()
    (HERE / '_d25_facts_out.txt').write_text(content, encoding='utf-8')
    print(content, end='')
    sys.exit(status)
