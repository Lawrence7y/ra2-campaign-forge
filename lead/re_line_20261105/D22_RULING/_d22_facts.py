"""Read-only offline D-22 probe; no subprocess or engine imports.
Run: find D:/Project/ra2-campaign-forge -type f '(' -name 'except_post_*.txt' -o -name 'EXCEPT_SINGLESTEP_0x7CFC9F_20261019T1352.txt' ')' -print0 | python -I -X utf8 D:/Project/ra2-campaign-forge/lead/re_line_20261105/D22_RULING/_d22_facts.py
Filesystem find + sha256sum was run first in the session.
Consumes binary find output, hashes and compares full bytes.
"""
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import re

ROOT = b'D:/Project/ra2-campaign-forge'
DEST = Path('D:/Project/ra2-campaign-forge/lead/re_line_20261105/D22_RULING/_d22_facts_out.txt')
lines = []
def emit(s):
    lines.append(str(s))
import sys
# Consume whole-repository find -print0 output without decoding filenames.
entries = [p for p in sys.stdin.buffer.read().split(b'\0') if p]
paths = sorted(p for p in entries if os.path.basename(p).startswith(b'except_post_'))
targets = [p for p in entries if os.path.basename(p) == b'EXCEPT_SINGLESTEP_0x7CFC9F_20261019T1352.txt']
emit('GENERATED ' + dt.datetime.now(dt.timezone.utc).isoformat())
emit('ENUMERATION full repository find -print0 via binary stdin; prior os.walk run stopped without result')
emit('FIND_COUNT ' + str(len(paths)))
emit('TARGET_COUNT ' + str(len(targets)))
if len(targets) != 1:
    raise RuntimeError('Unique target unavailable')
with open(targets[0], 'rb') as f:
    baseline = f.read()
basehash = hashlib.sha256(baseline).hexdigest()
def registers(data):
    return {key: [m.decode('ascii') for m in re.findall(key.encode() + rb'\s*:\s*([^\s\r\n]+)', data, re.I)] for key in ['Eip', 'Esp', 'Ebp', 'EFlags']}
emit('TARGET ' + os.fsdecode(targets[0]))
emit('TARGET_SIZE ' + str(len(baseline)))
emit('TARGET_SHA256 ' + basehash)
emit('TARGET_REGISTERS ' + json.dumps(registers(baseline)))
emit('ALL_ROWS: index | path | st_mtime_ns | mtime_UTC | mtime_UTC+08:00 | size | sha256 | hash_equal | byte_equal')
rows = []
for i, path in enumerate(paths, 1):
    st = os.stat(path)
    with open(path, 'rb') as f:
        data = f.read()
    digest = hashlib.sha256(data).hexdigest()
    equal = data == baseline
    timestamp = dt.datetime.fromtimestamp(st.st_mtime, dt.timezone.utc)
    row = {'path': os.fsdecode(path).replace('\\', '/'), 'ns': st.st_mtime_ns, 'utc': timestamp.isoformat(), 'utc8': timestamp.astimezone(dt.timezone(dt.timedelta(hours=8))).isoformat(), 'size': st.st_size, 'hash': digest, 'hash_equal': digest == basehash, 'byte_equal': equal, 'registers': registers(data)}
    rows.append(row)
    emit(' | '.join(map(str, [i, row['path'], row['ns'], row['utc'], row['utc8'], row['size'], digest, row['hash_equal'], equal])))

def summarize(name, selected):
    emit('SUMMARY ' + name)
    if not selected:
        emit('COUNT 0 (no mtime bounds)')
        return
    earliest = min(selected, key=lambda r: r['ns'])
    latest = max(selected, key=lambda r: r['ns'])
    emit(json.dumps({'count': len(selected), 'same_hash': sum(r['hash_equal'] for r in selected), 'same_bytes': sum(r['byte_equal'] for r in selected), 'distinct_hashes': len({r['hash'] for r in selected}), 'earliest': earliest, 'latest': latest, 'span_hours': (latest['ns'] - earliest['ns']) / 3600000000000}, ensure_ascii=True))

summarize('ALL_REPOSITORY', rows)
outqc = ROOT.decode() + '/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip'
summarize('OUT_QC161_SUBTREE', [r for r in rows if r['path'].startswith(outqc + '/')])
summarize('OUT_QC161_DIRECT_FILES', [r for r in rows if r['path'].rsplit('/', 1)[0] == outqc])
summarize('LIVE_LEAD_QC161_SUBTREE', [r for r in rows if r['path'].startswith(ROOT.decode() + '/lead/qc161_u0400_trip/')])
emit('DONE: no launch, injection, live process memory, engine imports, commit or push.')
DEST.write_text('\n'.join(lines) + '\n', encoding='utf-8')
print('\n'.join(s for s in lines if s.startswith(('SUMMARY', '{', 'FIND_COUNT', 'TARGET_', 'DONE'))))
