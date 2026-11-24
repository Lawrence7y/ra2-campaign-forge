# -*- coding: utf-8 -*-
"""D29 read-only source verification and pure arithmetic; no sampling implementation."""
from pathlib import Path
from decimal import Decimal
import ast
import hashlib
import json
import sys

ROOT = Path('D:/Project/ra2-campaign-forge')
OUT = ROOT / 'lead/d29_ruling_20261106/_d29_facts_out.txt'
FILES = {
    'draft': 'lead/control_20261106/D29_ENTRY_DRAFT.md',
    'definition': 'lead/stall_event_def_20261106/STALL_EVENT_DEFINITION.md',
    'probe': 'lead/stall_event_def_20261106/_stall_probe.py',
    'decisions': 'lead/PENDING_DECISIONS.md',
    'd28': 'lead/d28_ruling_20261106/RULING_D28.md',
    'budget': 'lead/d13b_timing_clarify_20261106/BUDGET_SCENARIOS.json',
    'timeline': 'lead/d13b_timing_clarify_20261106/TIMELINE_MODEL.json',
    'clarify': 'lead/d13b_timing_clarify_20261106/TIMING_SPEC_CLARIFY.md',
}
texts = {}
result = {'sourceFingerprints': {}, 'verbatim': {}, 'checks': {}, 'budget': []}
for key, rel in FILES.items():
    raw = (ROOT / rel).read_bytes()
    texts[key] = raw.decode('utf-8-sig')
    result['sourceFingerprints'][rel] = {'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}
for key, numbers in {'definition': [177, 190, 191], 'probe': [28, 86, 93, 95, 96], 'decisions': [260], 'd28': [28, 30, 32, 34, 36, 42], 'clarify': [50, 54, 55, 141]}.items():
    lines = texts[key].splitlines()
    for number in numbers:
        result['verbatim'][f'{FILES[key]}:{number}'] = lines[number - 1]
checks = result['checks']
checks['line177_has_50ms'] = '且必须在停滞发生后 50ms 内捕获' in texts['definition'].splitlines()[176]
checks['D12_B_is_authoritative'] = '口径 B 为准' in texts['decisions'].splitlines()[259]
tree = ast.parse(texts['probe'])
threshold = next(ast.literal_eval(n.value) for n in tree.body if isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id == 'T_DEFAULT' for t in n.targets))
checks['T_DEFAULT_seconds'] = threshold
checks['line96_condition'] = texts['probe'].splitlines()[95].strip()
quote = '并未禁止所有提前触发'
section2 = texts['d28'].split('## 2 D 链处置', 1)[1].split('## 3 ', 1)[0]
checks['claimed_D28_exact_quote_in_section2'] = quote in section2
checks['claimed_D28_exact_quote_anywhere'] = quote in texts['d28']
checks['clarification_repeats_claimed_quote'] = quote in texts['clarify']
scenarios = json.loads(texts['budget'], parse_float=Decimal)
for scenario in scenarios:
    values = [Decimal(str(s['ms'])) for s in scenario['segments']]
    total = sum(values, Decimal(0))
    reported = Decimal(str(scenario['totalMs']))
    post_detection = values[2] + values[3]
    result['budget'].append({
        'name': scenario['name'], 'segmentsMs': [str(v) for v in values],
        'computedTotalMs': str(total), 'reportedTotalMs': str(reported),
        'differenceMs': f'{total-reported:.4f}',
        'evidenceGrades': [s['evidenceGrade'] for s in scenario['segments']],
        'postDetectionMs': str(post_detection), 'postDetectionStrictlyBelow50': post_detection < 50,
        'captureWithin50FromStart': total <= 50,
    })
checks['A_B_all_four_values_equal'] = [s['ms'] for s in scenarios[0]['segments']] == [s['ms'] for s in scenarios[1]['segments']]
checks['A_B_entire_segments_equal'] = scenarios[0]['segments'] == scenarios[1]['segments']
checks['measuredSegmentCount'] = sum(s['evidenceGrade'] == '实测' for v in scenarios for s in v['segments'])
checks['segmentCount'] = sum(len(v['segments']) for v in scenarios)
timeline = json.loads(texts['timeline'])
result['timeline'] = [{'kind': v['kind'], 'hardDeadline': v['hardDeadline'], 'verified': v.get('verified')} for v in timeline]
# Logical countermodel only: these assigned times are not empirical timings or a capture design.
start, trigger, capture, classify, duration = map(Decimal, ['0', '30', '40', '120', '120'])
result['pureLogicalCounterexampleMs'] = {
    'status': 'hypothetical assignments, not measured and not an implementation',
    'start': str(start), 'trigger': str(trigger), 'capture': str(capture), 'classify': str(classify), 'duration': str(duration),
    'line177_captureWithin50': capture - start <= 50,
    'line190_postTriggerBelow50': capture - trigger < 50,
    'line190_safetyAtMost20': capture - trigger <= 20,
    'line191_triggerAccumBelow100': trigger - start < 100,
    'B_durationAtLeast100': duration >= 100,
    'classificationAfterDuration': classify >= start + duration,
}
checks['wait_until_B_then_capture_cannot_meet_50'] = Decimal(str(threshold)) * 1000 > 50
result['scope'] = 'Only source reads and pure model calculations; original probe not imported or executed; no corpus reanalysis, gates, live processes or sampling APIs run.'
output = json.dumps(result, ensure_ascii=False, indent=2)
OUT.write_text(output + '\n', encoding='utf-8')
sys.stdout.reconfigure(encoding='utf-8')
print(output)
