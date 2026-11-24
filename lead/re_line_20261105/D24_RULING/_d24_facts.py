"""Supplementary read-only probe. Required shell checks were run separately."""
from pathlib import Path
from datetime import datetime
import hashlib

ROOT = Path('D:/Project/ra2-campaign-forge')
OUT = ROOT / 'lead/re_line_20261105/D24_RULING/_d24_facts_out.txt'
HARNESS = ROOT / 'out/re_work/work_chain/CONTINUE_20261003/lead/qc151_u0400_trip/qc151_trip.py'
LOG = ROOT / 'lead/re_line_20261105/W11_EXCEPT_FRESHNESS/_w11_t3_test_out.txt'
parts = ['D24 supplementary probe: ' + datetime.now().astimezone().isoformat(),
         'V1 未验／未独立核: ListWorkflowRuns not exposed in this ask; no run-list check executed.',
         'D-24 transcription (PENDING_DECISIONS.md:68-72): W8/W10/W9/W11/D-22/D-23 completed; W7 stopped (stop_reason=user); W4 interrupted. Historical record only; current zero-inflight status unverified.',
         'Required sha256sum / wc -c / wc -l / stat checks executed separately in Bash; see FACTCHECK.md. This probe adds independent byte checks.']
data = HARNESS.read_bytes()
parts.extend(['V2_PATH=' + HARNESS.as_posix(),
              'SHA256=' + hashlib.sha256(data).hexdigest(),
              'BYTES=' + str(len(data)),
              'LF_COUNT=' + str(data.count(b'\n')),
              'MTIME=' + datetime.fromtimestamp(HARNESS.stat().st_mtime).astimezone().isoformat()])
parts.append('V3 historical log read only; tests not rerun: ' + LOG.as_posix())
lines = LOG.read_bytes().splitlines()
for number, line in enumerate(lines[-3:], start=len(lines) - 2):
    parts.append(str(number) + ': ' + line.decode('utf-8', errors='replace'))
parts.append('V3_EXPECTED_TAIL_MATCH=' + str(lines[-3:] == [b'OK', b'PASS=14 FAIL=0', b'EXIT=0']))
text = '\n'.join(parts) + '\n'
OUT.write_text(text, encoding='utf-8')
print(text, end='')
