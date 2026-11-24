# -*- coding: utf-8 -*-
"""D-26 offline documentary verification; no imports of project code.
Run: python -I -X utf8 D:/Project/ra2-campaign-forge/lead/d26_ruling_20261106/_d26_facts.py
Stdout is the requested evidence artifact. Inputs are opened only for reading.
PASS means the specified documentary assertion, not experimental validation.
"""
from pathlib import Path
import hashlib
import math
import re
import statistics

ROOT = Path('D:/Project/ra2-campaign-forge')
PD = 'lead/PENDING_DECISIONS.md'
DRAFT = 'lead/control_20261106/D26_ENTRY_DRAFT.md'
D24 = 'lead/re_line_20261105/D24_RULING/RULING_D24.md'
D25 = 'lead/d25_ruling_20261106/RULING_D25.md'
NIGHT = 'lead/goal3t_nightwatch_20261102/'
REAL = 'lead/codex_round_20261030/LEADER_battle/E3_SAMPLING_PLAN_REVIEWABLE.md'
WRONG = NIGHT + 'E3_SAMPLING_PLAN_REVIEWABLE.md'
PHASE = NIGHT + 'PHASE_BY_BOOT_20261104.md'
GOAL = 'lead/GOAL_THREE_TARGETS_20261018.md'
cache = {}

def lines(rel):
    if rel not in cache:
        cache[rel] = (ROOT / rel).read_text(encoding='utf-8-sig').splitlines()
    return cache[rel]

def show(rel, start, end):
    for i in range(start, end + 1):
        print(f'{rel}:{i}: {lines(rel)[i - 1]}')

def require(rel, number, *parts):
    text = lines(rel)[number - 1]
    assert all(part in text for part in parts), (rel, number, parts, text)

def passed(label):
    print(f'PASS {label}')

print('Scope: documentary matching plus independent arithmetic on the published BOOT table.')
print('Not run: game, live-process operations, sampling, historical experimental scripts, raw 97-window recomputation, project gates.')
print('Fingerprints (binary hashlib.sha256 and len):')
files = [DRAFT, PD, NIGHT + 'E3_FOR_GOAL1_CARD_20261103.md',
         NIGHT + 'E3_TRIGGER_N_CORRECTION_20261103.md', REAL, PHASE,
         NIGHT + 'BATCH_XVERIFY_20261103.md', D24, D25, GOAL,
         NIGHT + '_phase_recompute.py', NIGHT + '_phase_recompute_out.txt']
for rel in files:
    data = (ROOT / rel).read_bytes()
    print(f'{rel}: bytes={len(data)} sha256={hashlib.sha256(data).hexdigest()}')

pd = lines(PD)
start = pd.index('## 待裁决事项（当前）')
end = pd.index('## 已裁决记录（最近在上）')
heads = [int(m.group(1)) for text in pd[start + 1:end]
         if (m := re.match(r'^- \*\*D-(\d+)（', text))]
maximum = max(int(n) for n in re.findall(r'D-(\d+)', '\n'.join(pd)))
print(f'F1 current section: lines={start + 1}..{end}; item_headers={heads}; full_document_max_D={maximum}')
assert heads == [13, 14] and maximum == 25
passed('F1 only two current item headers, maximum D-25 (references inside items are not extra headers)')

wrong_exists = (ROOT / WRONG).exists()
real_exists = (ROOT / REAL).is_file()
print(f'F2 wrong_path_exists={wrong_exists}; real_path_is_file={real_exists}')
assert not wrong_exists and real_exists
show(PD, 44, 45)
passed('F2 expanded same-directory evidence path is absent; actual file exists')
print('NOTE PD:45 uses only a bare basename; the fully expanded wrong path is an inference from PD:44, not a verbatim full path in PD.')

require(PD, 30, 'N=1.0s（K=400）误触率实测 0')
require(PD, 31, 'N=1.0s 站得住')
require(PD, 32, '1734', '87.7% 是 0.1–0.2s 短停')
show(PD, 30, 33)
show(GOAL, 3295, 3297)
show(GOAL, 3307, 3310)
passed('F3 quoted N/87.7%/stands-up statements exist (historical empirical validity not rerun)')

require(PD, 49, '64 moving', '窗内有推进')
require(PD, 50, '+0.0395', '−0.0403')
require(PD, 51, '97 全量窗', '含全窗冻结窗')
require(PD, 52, '+0.3461', '+0.3474')
show(PD, 48, 56)
passed('F4 all four coefficients and both window-set definitions match')
print('NOTE only rho(window,B%) changes sign; rho(uptime,B%) is positive in both sets.')

require(PD, 55, '8 个 BOOT', '4 负 / 2 正', '+0.4472')
require(GOAL, 3505, '8 个 BOOT', '负 4 / 正 2', '+0.4472')
show(GOAL, 3495, 3505)
show(PHASE, 60, 71)
passed('F5 documentary match: section 534 really contains the quoted summary')
vals = []
for text in lines(PHASE)[61:69]:
    cell = text.split('|')[3].strip().replace('**', '').replace('−', '-')
    vals.append(float('nan') if cell.startswith('nan') else float(cell))
finite = [v for v in vals if math.isfinite(v)]
print(f'F5 arithmetic: table_rows={len(vals)}; finite={len(finite)}; nan={len(vals)-len(finite)}; negative={sum(v < 0 for v in finite)}; positive={sum(v > 0 for v in finite)}')
print(f'F5 arithmetic: sorted_finite={sorted(finite)}; finite_median={statistics.median(finite):+.5f}; historical_index_value={sorted(vals)[len(vals)//2]:+.4f}')
assert len(finite) == 6 and len(vals) == 8
assert abs(statistics.median(finite) - (-0.34305)) < 1e-10
print('DISPUTED F5 statistical truth: 8 includes 2 undefined values; finite-value median is -0.34305 on the published rounded table, not +0.4472.')
show(NIGHT + '_phase_recompute.py', 181, 197)
print('The original script counts nan in len(within) and indexes sorted(within)[len(within)//2]; this is not a finite-value statistical median. Original script read, not executed.')

require(D24, 70, 'D-13', '建议保留执行暂停')
require(D24, 71, 'D-14', '建议选 C')
require(D24, 78, 'D-13', '继续暂停')
show(D24, 68, 71)
show(D24, 78, 78)
passed('F6 D24 line anchors 70, 71, 78 match')

require(D25, 40, '4 附带三问')
require(D25, 46, '(iii)', '只给建议', 'D-13 建议维持暂停', 'D-14 建议选 C')
show(D25, 46, 46)
passed('F7 D25 section 4(iii) recommends pause / C, not final adjudication')

require(PD, 40, '本线建议 A')
require(PD, 60, '本线建议 A')
show(PD, 40, 43)
show(PD, 57, 63)
passed('F8 source line recommends A / A, different from D24 and D25 pause / C')
print('LIMIT: differing recommendations are not inconsistent final rulings; D24 and D25 agree with each other.')
print('LIMIT: no timing, causality, statistical significance, raw false-positive rate, or real-world stall improvement has been validated by this documentary check.')
print('RESULT documentary_checks=8/8; arithmetic_dispute=BOOT summary; no protected files written by this script.')
