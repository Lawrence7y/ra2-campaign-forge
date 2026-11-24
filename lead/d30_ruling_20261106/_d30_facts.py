"""D30 independent offline fact check; writes only its sibling output file."""
from pathlib import Path
import json
import re
import hashlib
import statistics
import bisect
from collections import Counter, defaultdict

ROOT = Path('D:/Project/ra2-campaign-forge')
OUT = ROOT / 'lead/d30_ruling_20261106/_d30_facts_out.txt'
lines = []
def emit(label, value):
    lines.append(label + ': ' + json.dumps(value, ensure_ascii=False, sort_keys=True))
def load(rel):
    return json.loads((ROOT / rel).read_text(encoding='utf-8-sig'))

stats_rel = 'lead/early_trigger_feasibility_20261106/FEASIBILITY_STATS.json'
stats = load(stats_rel)
for rel in [stats_rel, 'lead/control_20261106/D30_ENTRY_DRAFT.md',
            'lead/stall_event_def_20261106/STALL_EVENTS.json',
            'lead/d29_ruling_20261106/RULING_D29.md',
            'lead/stall_event_def_20261106/STALL_EVENT_DEFINITION.md']:
    emit('sha256 ' + rel, hashlib.sha256((ROOT / rel).read_bytes()).hexdigest())

base = ROOT / 'out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip'
cache = {}
files = sorted(base.rglob('measure_w*.json'))
for p in files:
    parts = p.relative_to(base).parts
    key = (parts[0] if len(parts) > 1 else '(root)', p.stem.replace('measure_', ''))
    assert key not in cache, key
    d = json.loads(p.read_text(encoding='utf-8-sig'))
    assert len(d.get('samples', {}).get('t', [])) == len(d.get('samples', {}).get('f', []))
    cache[key] = d
emit('corpus', {'files': len(files), 'samples': sum(len(d.get('samples', {}).get('t', [])) for d in cache.values())})
events = load('lead/stall_event_def_20261106/STALL_EVENTS.json')
real = [e for e in events if e.get('isRealMatch') is True]
real_keys = {(e['trip'], e['window'], e['startTick'], e['endTick']) for e in real}
assert len(real) == 1681
buckets = defaultdict(lambda: [0, 0])
errors = []
missing = []
recovered = 0
for e in real:
    d = cache[e['trip'], e['window']]['samples']
    ts, fs = d['t'], d['f']
    st, et = e['startTick'], e['endTick']
    duration = e['durationMs']
    bucket = '0.1-0.2s' if duration < 200 else '0.2-0.5s' if duration < 500 else '0.5-1.0s'
    buckets[bucket][0] += 1
    if st == 0:
        missing.append([e['trip'], e['window'], st])
        continue
    errors.append((ts[st] - ts[st-1]) * 1000)
    target = ts[st] + .05
    if target > ts[et]:
        recovered += 1
    elif fs[bisect.bisect_right(ts, target)-1] == fs[st]:
        buckets[bucket][1] += 1
for row in stats['q2']['coverageByDuration']:
    pair = buckets[row['bucket']]
    assert pair == [row['total'], row['capturableWithin50ms']]
    emit('Q2 bucket ' + row['bucket'], {'total': pair[0], 'capturable': pair[1], 'percent': pair[1]/pair[0]*100})
captured = sum(v[1] for v in buckets.values())
emit('Q2 total', {'capturable': captured, 'total': len(real), 'percent': captured/len(real)*100, 'insufficient': missing, 'recoveredBefore50ms': recovered, 'anchor': 'observed t[startTick], not measured physical S'})
q1 = {'medianMs': statistics.median(errors), 'maxMs': max(errors), 'valid': len(errors), 'meaning': 'preceding sample interval; upper bound on onset observation lag, not measured lag or proven thread-block cause'}
assert round(q1['medianMs'], 3) == stats['q1']['startObsErrorMsMedian']
assert round(q1['maxMs'], 3) == stats['q1']['startObsErrorMsMax']
emit('Q1', q1)

manifest = (ROOT / 'lead/goal3t_nightwatch_20261102/_stall_vs_gap_out.txt').read_text(encoding='utf-8-sig')
keys = []
for line in manifest.splitlines():
    m = re.match(r'^([a-zA-Z0-9_\(\)]+)\s+(w\d)\s+([0-9\.]+)', line.strip())
    if m:
        key = m[1], m[2]
        if key in cache:
            s = cache[key].get('samples', {})
            ts, fs = s.get('t', []), s.get('f', [])
            if len(ts) >= 2 and any(a != b for a, b in zip(fs, fs[1:])):
                keys.append(key)
assert len(keys) == len(set(keys)) == 64
runs = []
for trip, win in keys:
    s = cache[trip, win]['samples']
    ts, fs = s['t'], s['f']
    i = 0
    while i < len(fs):
        j = i
        while j+1 < len(fs) and fs[j+1] == fs[i]:
            j += 1
        runs.append((trip, win, i, j, (ts[j]-ts[i])*1000, j-i+1))
        i = j+1
expected = {10: (28294, 26590, 1704), 25: (5343, 3639, 1704), 50: (1866, 162, 1704)}
for row in stats['q3']['kTable']:
    k = row['k']
    triggered = [r for r in runs if r[5] >= k]
    good = [r for r in triggered if r[4] >= 100]
    bad = [r for r in triggered if r[4] < 100]
    hits = {r[:4] for r in triggered if r[:4] in real_keys}
    total, false, correct = len(triggered), len(bad), len(good)
    assert (total, false, correct) == expected[k]
    assert correct + false == total
    assert round(false/total, 4) == row['falseTriggerRate']
    counts = Counter('under32ms' if r[4] < 32 else '32to50ms' if r[4] <= 50 else 'over50toUnder100ms' for r in bad)
    delays = [(cache[r[0], r[1]]['samples']['t'][r[2]+k-1] - cache[r[0], r[1]]['samples']['t'][r[2]])*1000 for r in triggered]
    emit('Q3 k=' + str(k), {'total': total, 'false': false, 'correctDurationGE100': correct, 'sumEqualsTotal': correct+false == total,
        'falsePercent': false/total*100, 'precisionPercent': correct/total*100, 'realHits': len(hits),
        'durationGE100NotReal': len([r for r in good if r[:4] not in real_keys]), 'strictRealPrecisionPercent': len(hits)/total*100,
        'missedReal': len(real_keys-hits), 'falseDurationHistogram': counts,
        'triggerDelayFromObservedStartMs': {'min': min(delays), 'median': statistics.median(delays), 'max': max(delays)},
        'nominalKPointsSpanMs': (k-1)*2})
win_counts = Counter((e['trip'], e['window']) for e in real)
emit('real event windows', {'count': len(win_counts), 'meanEventsPerNonemptyWindow': len(real)/len(win_counts)})
for row in stats['q4']['quotaTable']:
    n = row['n']
    cap = sum(min(n, count) for count in win_counts.values())
    abandoned = len(real)-cap
    assert abandoned == row['abandonedEvents']
    assert round(cap/len(real), 4) == row['coverageRate']
    emit('Q4 N=' + str(n), {'captured': cap, 'abandoned': abandoned, 'percent': cap/len(real)*100, 'assumption': 'ideal quota spent only on real events, not online false triggers'})
emit('Q5', {'strictFalse': stats['q5']['verified'] is False, 'dependencyCount': len(stats['q5']['dependencies']), 'dependencies': stats['q5']['dependencies']})
assert stats['q5']['verified'] is False and len(stats['q5']['dependencies']) == 4
for fps in [30, 20]:
    emit('FPS ' + str(fps), {'frameMs': 1000/fps, 'samplePeriodsAt500Hz': 500/fps})
period_ms, k, onset_lag_ms, save_delay_ms = 2, 25, 0.5, 1
span_ms = (k-1)*period_ms
capture_ms = onset_lag_ms + span_ms + save_delay_ms
emit('finiteGridCounterexample', {'k': k, 'uniformPeriodMs': period_ms, 'points': k, 'observedSpanMs': span_ms, 'conditionalOnsetLagMs': onset_lag_ms, 'conditionalSaveDelayMs': save_delay_ms, 'conditionalCaptureFromPhysicalStartMs': capture_ms, 'below50ms': capture_ms <= 50, 'engineeringVerified': False, 'acceptableFalseRateDefined': False})
emit('frequencyAssuming64WindowsOf25Seconds', {'durationSeconds': 64*25, 'k10AllTriggersPerSecond': 28294/(64*25), 'k10FalseTriggersPerSecond': 26590/(64*25), 'note': '25s per window is an assumption for this arithmetic, not integrated measured duration'})
bad10 = [r for r in runs if r[5] >= 10 and r[4] < 100]
normal_band = sum(1000/30 <= r[4] <= 1000/20 for r in bad10)
emit('Q3 k10 FPS20to30DurationBand', {'falseRunsIn33.333to50ms': normal_band, 'allFalseRuns': len(bad10), 'percentInBand': normal_band/len(bad10)*100, 'note': 'run durations are sampled spans, not independently measured normal frame execution or rendering FPS'})
for rel, selected in [('lead/stall_event_def_20261106/STALL_EVENT_DEFINITION.md', [176,177,190,191]), ('lead/d29_ruling_20261106/RULING_D29.md', [3,4,6]), ('lead/control_20261106/D30_ENTRY_DRAFT.md', [34,39,54,66,88,95,96,125])]:
    source_lines = (ROOT / rel).read_text(encoding='utf-8-sig').splitlines()
    for number in selected:
        emit(rel + ':' + str(number), source_lines[number-1])
emit('scope', 'Independent read-only full offline corpus recomputation; original probes/gates not executed; no real machine, live process access, sampling code or implementations; actual engineering overhead and 20-30FPS causal attribution unverified.')
emit('checks', 'All numeric assertions passed')
text = '\n'.join(lines) + '\n'
OUT.write_text(text, encoding='utf-8')
print(text, end='')
