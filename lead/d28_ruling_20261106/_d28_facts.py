# -*- coding: utf-8 -*-
"""D28 independent facts. Only writes _d28_facts_out.txt beside this script.
Does not import/execute candidate, mother, probes or sampling code.
Run: python -I -X utf8 -B D:/Project/ra2-campaign-forge/lead/d28_ruling_20261106/_d28_facts.py
"""
from pathlib import Path
import ast
import hashlib
import io
import json
import re
import sys
from contextlib import redirect_stdout
from decimal import Decimal

ROOT = Path('D:/Project/ra2-campaign-forge')
OUT = ROOT / 'lead/d28_ruling_20261106/_d28_facts_out.txt'

def read(rel):
    return (ROOT / rel).read_text(encoding='utf-8-sig')

def emit(key, value):
    print(key + ': ' + json.dumps(value, ensure_ascii=False, sort_keys=True))

def cite(rel, predicate):
    hits = [{'line': i, 'text': s} for i, s in enumerate(read(rel).splitlines(), 1) if predicate(s)]
    emit(rel, hits)
    return hits

def main():
    emit('command', 'python -I -X utf8 -B D:/Project/ra2-campaign-forge/lead/d28_ruling_20261106/_d28_facts.py')
    emit('isolated', bool(sys.flags.isolated))
    candidate = 'lead/b2b_candidate_20261106/qc151_trip.candidate.py'
    mother = 'out/re_work/work_chain/CONTINUE_20261003/lead/qc151_u0400_trip/qc151_trip.py'
    for label, rel, expected_sha, expected_size in (
        ('candidate', candidate, '9656e432f5b571590b757bb78869c274fba40220ce57b7a70da9b4a987b967cc', 420292),
        ('mother', mother, '517889c68f037ab63f9c38300e627d34457b7be9fab0362e425783c7ec5ba636', 399508)):
        data = (ROOT / rel).read_bytes()
        sha = hashlib.sha256(data).hexdigest()
        emit(label, {'path': rel, 'bytes': len(data), 'sha256': sha,
                     'matchesExpected': sha == expected_sha and len(data) == expected_size})
    text = read(candidate)
    tree = ast.parse(text)
    emit('H6_old_literal_count', text.count('copy_post_except_evidence(rec, carrier_dir, out_dir)'))
    calls = [n for n in ast.walk(tree) if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == 'copy_post_except_evidence']
    emit('H6_AST_calls', [{'line': n.lineno, 'endLine': n.end_lineno,
                           'keywords': {k.arg: ast.unparse(k.value) for k in n.keywords}} for n in calls])
    assert len(calls) == 1 and any(k.arg == 'pre_freshness_snapshot' and ast.unparse(k.value) == 'pre_freshness_snapshot' for k in calls[0].keywords)
    main_node = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'main')
    init = next(n for n in main_node.body if isinstance(n, ast.AnnAssign) and isinstance(n.target, ast.Name) and n.target.id == '_pre_freshness_snapshot')
    containing_try = next(n for n in main_node.body if isinstance(n, ast.Try) and n.lineno > init.lineno)
    wanted = {'EXIT_CARRIER_NOT_OWNED', 'EXIT_TARGET_MISSING', 'EXIT_TARGET_MISMATCH', 'EXIT_PRECHECK_SHA_MISMATCH', 'EXIT_PRECHECK_SIG_MISMATCH'}
    early = sorted([n for n in ast.walk(containing_try) if isinstance(n, ast.Return) and isinstance(n.value, ast.Name) and n.value.id in wanted], key=lambda n: n.lineno)
    emit('H7', {'initLine': init.lineno, 'init': ast.unparse(init), 'tryLine': containing_try.lineno,
                'earlyReturns': [{'line': n.lineno, 'value': n.value.id} for n in early],
                'allAfterInit': len(early) == 5 and all(n.lineno > init.lineno for n in early)})
    assert isinstance(init.value, ast.Constant) and init.value.value is None
    assert len(early) == 5 and all(n.lineno > init.lineno for n in early)
    review = 'lead/b2b_candidate_20261106/review/CANDIDATE_REVIEW.md'
    for key in ['motherUnchanged', 'nineHunksPresent', 'noImportMother', 'threeStatesDistinct', 'testsActuallyRun']:
        hits = cite(review, lambda s, k=key: bool(re.fullmatch(re.escape(k) + r':\s*(true|false)', s)))
        assert len(hits) == 1
    budget_rel = 'lead/d13b_design_20261106/BUDGET_MODEL.json'
    budget = json.loads(read(budget_rel), parse_float=Decimal)
    segments = [Decimal(str(s['ms'])) for s in budget['segments']]
    total = sum(segments)
    median = Decimal('129.93')
    emit('budget', {'segmentsMs': [str(s) for s in segments], 'sumMs': str(total),
                    'totalMs': str(budget['totalMs']), 'differenceMs': str(total-budget['totalMs']),
                    'meetsMedian': budget['meetsMedian'], 'computedTotalLessThan129_93': total < median,
                    'flagConsistent': budget['meetsMedian'] == (total < median),
                    'excessMs': str(total-median), 'otherSegmentsStrictBudgetMs': str(median-segments[1]),
                    'alternativeDispatchPlusCapture20MsTotal': str(segments[0]+segments[1]+Decimal('20')),
                    'alternativeMarginMs': str(median-(segments[0]+segments[1]+Decimal('20')))})
    assert total == budget['totalMs'] and budget['meetsMedian'] == (total < median)
    definition = 'lead/stall_event_def_20261106/STALL_EVENT_DEFINITION.md'
    cite(definition, lambda s: '累积判定耗时' in s or '端到端延迟必须' in s or '停滞发生后 50ms' in s)
    pending = 'lead/PENDING_DECISIONS.md'
    cite(pending, lambda s: 'D-12 已裁决' in s or '②停滞口径 = A' in s)
    wrong_probe = 'lead/d13b_design_20261106/_stall_probe.py'
    emit('requested_probe_path', {'path': wrong_probe, 'exists': (ROOT / wrong_probe).exists()})
    probe = 'lead/stall_event_def_20261106/_stall_probe.py'
    cite(probe, lambda s: 'T_DEFAULT' in s or 'dur = ts[j]' in s or 'if dur >= thr' in s)
    rul = 'lead/d27_ruling_20261106/RULING_D27.md'
    cite(rul, lambda s: '129.93' in s or '1681' in s or '1737' in s)
    emit('scope', {'candidateTestsRerun': False, 'd13bStateTestsRerun': False,
                   'reviewTestsActuallyRun': 'field read as true; historical execution provenance not independently established by reading the field',
                   'gameOrLiveMemoryOrSamplingExecuted': False})
    print('FACT_SCRIPT_COMPLETED')

if __name__ == '__main__':
    buffer = io.StringIO()
    with redirect_stdout(buffer):
        main()
    output = buffer.getvalue()
    OUT.write_text(output, encoding='utf-8')
    print(output, end='')
