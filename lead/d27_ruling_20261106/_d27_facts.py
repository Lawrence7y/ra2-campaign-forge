# -*- coding: utf-8 -*-
"""D-27 read-only fact reproduction; only stdout is written by caller.
Run: python -I -X utf8 D:/Project/ra2-campaign-forge/lead/d27_ruling_20261106/_d27_facts.py
No live processes, sampling APIs, or source modifications.
"""
from pathlib import Path
from collections import Counter
import contextlib
import hashlib
import io
import json
import math
import re
import runpy
import statistics
import subprocess
import sys

ROOT = Path('D:/Project/ra2-campaign-forge')
SRC = ROOT / 'lead/stall_event_def_20261106'

def show(label, value):
    print(label + ': ' + json.dumps(value, ensure_ascii=False, sort_keys=True))

def cite_lines(rel, predicate):
    for n, line in enumerate((ROOT / rel).read_text(encoding='utf-8-sig').splitlines(), 1):
        if predicate(line):
            print(f'{rel}:{n}: {line}')

print('COMMAND: python -I -X utf8 D:/Project/ra2-campaign-forge/lead/d27_ruling_20261106/_d27_facts.py')
for rel in ['lead/control_20261106/D27_ENTRY_DRAFT.md', 'lead/stall_event_def_20261106/STALL_EVENTS.json', 'lead/stall_event_def_20261106/_stall_probe.py', 'lead/stall_event_def_20261106/_stall_probe_out.txt', 'lead/stall_event_def_20261106/review/STALL_EVENT_DEF_REVIEW.md', 'lead/d26_ruling_20261106/RULING_D26.md', 'lead/PENDING_DECISIONS.md']:
    b = (ROOT / rel).read_bytes()
    show('fingerprint', {'path': rel, 'bytes': len(b), 'sha256': hashlib.sha256(b).hexdigest()})

rows = json.loads((SRC / 'STALL_EVENTS.json').read_text(encoding='utf-8-sig'))
assert isinstance(rows, list)
required = {'trip','window','startTick','endTick','durationMs','windowSet','isRealMatch','exclusionReason','evidence'}
issues = []
for i, r in enumerate(rows):
    if not required <= r.keys() or type(r['isRealMatch']) is not bool or not isinstance(r['durationMs'], (int, float)) or not math.isfinite(r['durationMs']) or r['durationMs'] < 100 or type(r['startTick']) is not int or type(r['endTick']) is not int or not 0 <= r['startTick'] <= r['endTick'] or (r['isRealMatch'] and r['exclusionReason'] is not None) or (not r['isRealMatch'] and not r['exclusionReason']):
        issues.append(i)
real = [r for r in rows if r['isRealMatch'] is True]
longs = [r for r in rows if r['durationMs'] >= 1000]
show('JSON independent counts', {'total':len(rows), 'real':len(real), 'false':len(rows)-len(real), 'real_ge1000':sum(r['durationMs']>=1000 for r in real), 'real_100_le_d_lt200':sum(100<=r['durationMs']<200 for r in real), 'real_200_le_d_lt500':sum(200<=r['durationMs']<500 for r in real), 'real_500_le_d_lt1000':sum(500<=r['durationMs']<1000 for r in real), 'real_max_ms':max(r['durationMs'] for r in real), 'real_median_ms':statistics.median(r['durationMs'] for r in real), 'all_max_ms':max(r['durationMs'] for r in rows), 'all_ge1000':len(longs), 'real_short_percent':100*sum(100<=r['durationMs']<200 for r in real)/len(real), 'schema_issues':issues})
show('ALL >=1000 grouped by exclusionReason', dict(Counter(r['exclusionReason'] for r in longs)))
show('ALL excluded grouped by exclusionReason', dict(Counter(r['exclusionReason'] for r in rows if not r['isRealMatch'])))
nc = {(r['trip'],r['window']) for r in rows if r['exclusionReason']=='whole_window_frozen_match_ended'}
show('JSON negative controls', {'windows':len(nc), 'real_events_in_these_windows':sum(r['isRealMatch'] for r in rows if (r['trip'],r['window']) in nc)})
cite_lines('lead/stall_event_def_20261106/_stall_probe_out.txt', lambda s: '负控测试窗数量' in s or '负控识别出的' in s or '说明：原始' in s)
cite_lines('lead/stall_event_def_20261106/review/STALL_EVENT_DEF_REVIEW.md', lambda s: any(k+':' in s for k in ['checkedEveryRow','negativeControlPassed','noSamplingCode']))
cite_lines('lead/d26_ruling_20261106/RULING_D26.md', lambda s: '不解除目标①机制挂账' in s or s.startswith('先补项目为'))
pending = (ROOT/'lead/PENDING_DECISIONS.md').read_text(encoding='utf-8-sig')
section = pending.split('## 待裁决事项（当前）',1)[1].split('## 已裁决记录',1)[0]
show('Pending section entry IDs', re.findall(r'^- \*\*(D-\d+)',section,re.M))
show('D26 occurrences in whole pending file', len(re.findall(r'D-26',pending)))

# Execute reviewed, offline-only source without modifying it, then compare its two outputs.
cmd = [sys.executable,'-I','-X','utf8',str(SRC/'_stall_probe.py')]
proc = subprocess.run(cmd+['--json'],capture_output=True,encoding='utf-8',check=False)
show('Original probe --json rerun', {'command':subprocess.list2cmdline(cmd+['--json']), 'returncode':proc.returncode, 'json_equal_existing':json.loads(proc.stdout)==rows if proc.returncode==0 else False, 'stderr':proc.stderr})
proc = subprocess.run(cmd,capture_output=True,encoding='utf-8',check=False)
show('Original probe text rerun', {'command':subprocess.list2cmdline(cmd), 'returncode':proc.returncode, 'text_equal_existing_normalized_newlines':proc.stdout==(SRC/'_stall_probe_out.txt').read_text(encoding='utf-8'), 'stderr':proc.stderr})

# Independently check every JSON record against its cited raw samples.
BASE = ROOT/'out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip'
cache = {}
raw_issues = []
long_metadata = []
for i,r in enumerate(rows):
    key=(r['trip'],r['window'])
    if key not in cache:
        p=BASE if r['trip']=='(root)' else BASE/r['trip']
        cache[key]=json.loads((p/('measure_'+r['window']+'.json')).read_text(encoding='utf-8-sig'))
    raw=cache[key]
    t=raw['samples']['t']; f=raw['samples']['f']; a=r['startTick']; b=r['endTick']
    if round((t[b]-t[a])*1000,2)!=r['durationMs'] or any(x!=f[a] for x in f[a:b+1]):
        raw_issues.append(i)
    if r['durationMs']>=1000:
        long_metadata.append({'trip':r['trip'],'window':r['window'],'reason':r['exclusionReason'],'durationMs':r['durationMs'],'frame':f[a], 'position':'WHOLE' if a==0 and b==len(f)-1 else ('LAST' if b==len(f)-1 else ('FIRST' if a==0 else 'MID')), 'next_frame':f[b+1] if b+1<len(f) else None})
show('Raw evidence checks all JSON rows', {'checked':len(rows),'issues':raw_issues,'distinct_event_windows':len(cache)})
for r in long_metadata:
    show('LONG raw evidence',r)

# Import reviewed script without __main__; synthetic inputs exercise the actual classifier.
ns = runpy.run_path(str(SRC/'_stall_probe.py'),run_name='d27_offline_definition_test')
func = ns['run_probe']; glob = func.__globals__

def synthetic_case(name, windows):
    def win(trip,w):
        t,f=windows[w]
        return {'trip':trip,'window':w,'ts':t,'fs':f,'span':t[-1]-t[0], 'moving':any(a!=b for a,b in zip(f,f[1:])), 'f0':f[0], 'rel_path':'SYNTHETIC/'+w, 'units0':10}
    glob['load_benchmark_manifest']=lambda:[('synthetic', w) for w in windows]
    glob['parse_window']=win
    out=io.StringIO(); argv=sys.argv
    try:
        sys.argv=['synthetic','--json']
        with contextlib.redirect_stdout(out):
            func()
    finally:
        sys.argv=argv
    show('SYNTHETIC actual classifier '+name,json.loads(out.getvalue()))

synthetic_case('internal 1.5s then resumes',{'w0':([0.0,0.1,1.6,1.7],[1,2,2,3])})
synthetic_case('whole-window 1.5s and next window resumes',{'w0':([0.0,0.5,1.5],[2,2,2]),'w1':([2.0,2.1],[2,3])})
synthetic_case('terminal 1.5s no next observation',{'w2':([0.0,0.1,1.6],[1,2,2])})
synthetic_case('terminal 1.5s next window resumes',{'w0':([0.0,0.1,1.6],[1,2,2]),'w1':([2.0,2.1],[2,3])})
show('Checks not run', ['check_stall_def.py gate (not requested as an execution check)', 'independent screenshot/state truth for every excluded event', 'live-process or game tests (prohibited)'])
print('END: descriptive counts are conditional on current corpus and labels; absence in these labels is not universal physical absence.')
