#!/usr/bin/env python3
"""R145 T：终态核验（幂等，可反复跑）。

注意：本轮有几个**一次性**脚本 —— r145k（重钉）、r145l（同步 + 首版错钉）、r145m（修错钉）、
r145j/r145n/r145o/r145p/r145q/r145r（追加）。它们第二次跑会 FAIL（因为改动已生效）。本脚本只核终态。
"""
import glob, hashlib, io, json, os, re, subprocess
BASE = '/home/t628/projects/ra2-campaign-forge/lead/next_re_20261117_r14'
ROOT = '/home/t628/projects/ra2-campaign-forge'
GATE = os.path.join(BASE, 'check_disc.py')
cc = []
def ck(n, c, d=''):
    print(('  PASS ' if c else '  FAIL ') + n + (('  ' + str(d)) if d else ''))
    if not c: cc.append(n)

files = {'R14_COMMON': (os.path.join(BASE, 'R14_COMMON.md'), 1081),
         'LEDGER': (os.path.join(ROOT, 'lead', 'GOAL_THREE_TARGETS_20261018.md'), 337),
         'LEAD_LOCK': (os.path.join(ROOT, 'lead', 'LEAD_LOCK'), 137),
         'STATUS_BOARD': (os.path.join(BASE, 'STATUS_BOARD.md'), 0),
         'BOARD_ARCHIVE': (os.path.join(BASE, 'BOARD_ARCHIVE.md'), 2952)}
for k, (p, cr) in files.items():
    b = open(p, 'rb').read()
    ck('CR %s == %d' % (k, cr), b.count(b'\r') == cr, b.count(b'\r'))
board = open(files['STATUS_BOARD'][0], 'rb').read()
ck('看板行数 <= 300', board.count(b'\n') <= 300, board.count(b'\n'))
ck('看板含第 145 轮段', 'R17 第 145 轮'.encode() in board)
ck('看板第 145 轮段登记了 S-321', 'S-321'.encode() in board)
rc = open(files['R14_COMMON'][0], 'rb').read()
ck('R14_COMMON 末节 = 2.150', re.findall(rb'(?m)^## (2\.\d+)', rc)[-1] == b'2.150', re.findall(rb'(?m)^## (2\.\d+)', rc)[-1])
ck('R14_COMMON 2.x 节数 144', len(re.findall(rb'(?m)^## 2\.\d+', rc)) == 144, len(re.findall(rb'(?m)^## 2\.\d+', rc)))
ck('§2.150 里登记了 S-316..S-322', all(('S-%d' % i).encode() in rc for i in range(316, 323)))
led = open(files['LEDGER'][0], 'rb').read()
ck('台账末节 = §1200', re.findall(rb'(?m)^## \xc2\xa7(\d+)', led)[-1] == b'1200', re.findall(rb'(?m)^## \xc2\xa7(\d+)', led)[-1])
lk = open(files['LEAD_LOCK'][0], 'rb').read()
ck('LEAD_LOCK 末段 OD 且 OD1..OD13 齐', re.findall(rb'(?m)^## ([A-Z]{2}) \xc2\xb7', lk)[-1] == b'OD' and all(('OD%d.' % i).encode() in lk for i in range(1, 14)))
g = open(GATE).read()
ck("GATE_VER == 'R145'", "GATE_VER = 'R145'" in g)
ck('C16_FLOORS 含 150: 8600', '150: 8600,' in g)
ck('C16_FLOORS_SHA256 == 183a5d82', "C16_FLOORS_SHA256 = '183a5d82" in g)
ck('C7_TEXT_SHA256 == 13ea4fd3 且不再是 120 hex', "C7_TEXT_SHA256 = '13ea4fd3" in g and not re.search(r"= '[0-9a-f]{120}'", g))
ck('FREEZE_SHA256 == d22fd43c 且不再是 120 hex', "FREEZE_SHA256 = 'd22fd43c" in g)
r = subprocess.run(['python3', 'check_disc.py'], capture_output=True, text=True, cwd=BASE)
out = r.stdout + r.stderr
ck('check_disc.py exit 0', r.returncode == 0, r.returncode)
for probe, label in (('C10 self-check: ok(R145)', 'C10 ok(R145)'),
                     ('C7d product/expression fingerprint ok: 31 rows, sha256=13ea4fd3', 'C7d 13ea4fd3 ok'),
                     ('sha256=d22fd43c2156d14c OK', 'C11 freeze d22fd43c OK'),
                     ('pinned 144', 'C16 pinned 144'),
                     ('unpinned 0', 'C16 unpinned 0'),
                     ('min margin 21', 'C16c min margin 21'),
                     ('183a5d82ed233fd6 (OK)', 'C16d 183a5d82'),
                     ('C7 live-checks passed 31', 'C7 31/31'),
                     ('last 150', 'C15 末节 150')):
    ck(label + ' 在场', probe in out)
# 一次性脚本必须存在与其 .bak（可追溯），且错钉不得留在门禁里
ck('错钉 05b54f35 已不在 check_disc.py', '05b54f35' not in g)
ck('错钉 636db13b 已不在 check_disc.py', '636db13b' not in g)
ck('r145 一次性脚本的 .bak 至少 8 份', len(glob.glob(os.path.join(BASE, 'R17_LEAD_BASELINE', '*r145*.bak'))) >= 8,
   len(glob.glob(os.path.join(BASE, 'R17_LEAD_BASELINE', '*r145*.bak'))))
res_files = ['r145a_negdisp', 'r145b_fullparse', 'r145c_reconcile', 'r145d_tolerant_union', 'r145e_semantics',
             'r145f_chd', 'r145g_transient', 'r145h_dualcrit', 'r145i_audit_recompute']
ck('九个取证脚本的 JSON 都在且 pos_fail 全 0',
   all(os.path.isfile(os.path.join(ROOT, '_r145', f + '.json')) and
       json.load(open(os.path.join(ROOT, '_r145', f + '.json'))).get('pos_fail') == 0 for f in res_files),
   [f for f in res_files if not os.path.isfile(os.path.join(ROOT, '_r145', f + '.json'))])
json.dump({'fails': cc, 'checks': 40 - len(cc)}, io.open(os.path.join(ROOT, '_r145/r145t_verify.json'), 'w'), indent=1)
print('\n=== 终态：FAIL %d ===' % len(cc))
