# -*- coding: utf-8 -*-
"""M82 phase 0: record BEFORE state (mtime/bytes/sha256) for the two COVERAGE files."""
import os, hashlib, datetime, json

R14 = r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14'
COV = os.path.join(R14, 'COVERAGE', 'coverage.tsv')
PAN = os.path.join(R14, 'COVERAGE', 'PANEL.md')
OUT = os.path.join(R14, 'MERGE_M82', '_before_state.json')
TZ = datetime.timezone(datetime.timedelta(hours=8))


def state(path):
    st = os.stat(path)
    b = open(path, 'rb').read()
    return {
        'path': path,
        'mtime': st.st_mtime,
        'mtime_iso': datetime.datetime.fromtimestamp(st.st_mtime, TZ).isoformat(),
        'bytes': len(b),
        'sha256': hashlib.sha256(b).hexdigest(),
    }


before = {'coverage.tsv': state(COV), 'PANEL.md': state(PAN)}
with open(OUT, 'w', encoding='utf-8', newline='\n') as f:
    json.dump(before, f, ensure_ascii=False, indent=2)
    f.write('\n')

for k, v in before.items():
    print('%s bytes=%d mtime=%s sha256=%s' % (k, v['bytes'], v['mtime_iso'], v['sha256']))

# baseline cross-check against M81 AFTER hash for PANEL.md
assert before['PANEL.md']['sha256'] == 'f65a15924e1739c0f4775f7bfbbdc1745ca00bf1f24f55980488dc98f66a736b', \
    'PANEL.md baseline does not match MERGE_M81 AFTER sha256 -- possible intermediate writer'
print('PANEL.md baseline OK (matches MERGE_M81 AFTER)')
print('BEFORE state written:', OUT)
