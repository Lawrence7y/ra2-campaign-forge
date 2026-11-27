#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R152 终态校验：五项 CR、看板行数、门禁、C7d/C16 重钉、归档未动、新节存在、无孤儿进程、v541 未被后续步骤改动。"""
import hashlib, io, os, re, subprocess, sys

ROOT = '/home/t628/projects/ra2-campaign-forge'
D = os.path.join(ROOT, 'lead', 'next_re_20261117_r14')
fail = []


def ck(n, c, d=''):
    ok = bool(c)
    print(('  PASS ' if ok else '  FAIL ') + n + (('  ' + str(d)) if d else ''))
    if not ok:
        fail.append(n)
    return ok


F = {
    'R14_COMMON': (os.path.join(D, 'R14_COMMON.md'), 1081),
    'LEDGER': (os.path.join(ROOT, 'lead', 'GOAL_THREE_TARGETS_20261018.md'), 337),
    'LEAD_LOCK': (os.path.join(ROOT, 'lead', 'LEAD_LOCK'), 137),
    'STATUS_BOARD': (os.path.join(D, 'STATUS_BOARD.md'), 0),
    'BOARD_ARCHIVE': (os.path.join(D, 'BOARD_ARCHIVE.md'), 2952),
}
for k, (p, cr) in F.items():
    raw = open(p, 'rb').read()
    got = raw.count(b'\r')
    ck('%s CR == %d' % (k, cr), got == cr, got)
    print('     %s: %d B / %d 行 / sha=%s' % (k, len(raw), raw.count(b'\n'),
                                              hashlib.sha256(raw).hexdigest()[:12]))

bl = open(F['STATUS_BOARD'][0], 'rb').read().count(b'\n')
ck('看板行数 <= 300', bl <= 300, bl)
brd = open(F['STATUS_BOARD'][0], 'rb').read()
ck('看板含第 152 轮段且唯一', brd.decode('utf-8').count('第 152 轮') == 1, brd.decode('utf-8').count('第 152 轮'))
ck('看板仍含第 150/151 轮段（本轮未归档）',
   '第 150 轮' in brd.decode('utf-8') and '第 151 轮' in brd.decode('utf-8'), '')

arc = open(F['BOARD_ARCHIVE'][0], 'rb').read()
ck('归档 CR 仍 2952（本轮未归档）', arc.count(b'\r') == 2952, arc.count(b'\r'))
ck('归档不含第 152 轮段', '第 152 轮' not in arc.decode('utf-8'), '')

rc = io.open(F['R14_COMMON'][0], encoding='utf-8', newline='').read()
ck('R14_COMMON 含 §2.157 且唯一', rc.count('## 2.157') == 1, rc.count('## 2.157'))
led = io.open(F['LEDGER'][0], encoding='utf-8', newline='').read()
ck('台账含 §1207 且唯一', led.count('## §1207') == 1, led.count('## §1207'))
lk = io.open(F['LEAD_LOCK'][0], encoding='utf-8', newline='').read()
ck('LEAD_LOCK 含 OJ1..OJ9', all(('\nOJ%d.' % i) in lk for i in range(1, 10)), '')

# v5.41 自校验
p541 = os.path.join(D, 'R17_R113_FACTINDEX_V541/FACT_INDEX.tsv')
b541 = open(p541, 'rb').read()
# 钉值从 _r152/r152e_write_v541.json 读（不写死：上一次把它写死，正是 S-375 同族错）
import json as _json
_w = _json.load(open(os.path.join(ROOT, '_r152/r152e_write_v541.json')))
sha541 = hashlib.sha256(b541).hexdigest()
ck('v5.41 90,976 B / sha 与写入记录一致（%s…）' % _w['dst_sha256'][:8],
   len(b541) == 90976 and sha541 == _w['dst_sha256'], (len(b541), sha541[:16]))
_pin = _json.load(open(os.path.join(ROOT, '_r152/r152d_buckets_pin.json')))
ts541 = _pin['measured_at_utc']
ck('v5.41 内含冻结测量时刻（%s）' % ts541, ts541.encode() in b541, '')
ck('v5.41 全 LF / 56 段 / 54 数据行',
   b541.count(b'\r') == 0 and len(b541.decode('utf-8').split('\n')) == 56
   and len([l for l in b541.decode('utf-8').split('\n') if l.strip()]) - 1 == 54, '')
d541 = {r[0]: r for r in [l.split('\t') for l in b541.decode('utf-8').split('\n') if l.strip()][1:]}
ck('v5.41 F35 limitations 含「只在 v5.30–V5.33 成立」',
   '只在 v5.30–V5.33 成立' in d541['F35'][4], '')
ck('v5.41 F24 statement 含清单 sha 与冻结时刻',
   _pin['list']['sha256'] in d541['F24'][1] and ts541 in d541['F24'][1], '')
ck('v5.41 grade / evidence_paths 与 v5.40 一致',
   all(d541[k][2] == v[2] and d541[k][3] == v[3] for k, v in
       {r[0]: r for r in [l.split('\t') for l in
                          open(os.path.join(D, 'R17_R112_FACTINDEX_V540/FACT_INDEX.tsv'),
                               encoding='utf-8').read().split('\n') if l.strip()][1:]}.items()), '')

# 门禁
r = subprocess.run([sys.executable, 'check_disc.py'], cwd=D, capture_output=True, text=True, timeout=600)
ck('门禁 exit 0', r.returncode == 0, r.returncode)
ck('C10 ok(R152)', 'ok(R152)' in r.stdout)
m = re.search(r'C16 per-section floors: (\d+) sections measured \(pinned (\d+)\), '
              r'hollow/deficient (\d+), missing (\d+), unpinned (\d+)', r.stdout)
ck('C16 151/151 且 unpinned 0', m and m.group(1) == '151' and m.group(2) == '151'
   and m.group(5) == '0', m.groups() if m else None)
ck('C16d 钉 ok（ba2ce8a0…）', 'floor-table pin: ba2ce8a0def4412f (OK)' in r.stdout, '')
ck('C7d 钉 ok（58a17e1a…）', 'sha256=58a17e1afb38add3' in r.stdout, '')
ck('C12/C12b 12/12', '12 frozen rows, 12 anchors hit' in r.stdout
   and '12/12 rows identical' in r.stdout, '')

# 孤儿进程
ps = subprocess.run(['bash', '-lc',
                     "ps -eo pid,cmd | grep -E 'python3 +_r152/r152[a-z]_' | grep -v grep | grep -v r152i_final"],
                    capture_output=True, text=True).stdout.strip()
ck('无孤儿 r152 进程', ps == '', ps[:200])

print('\nFAILS:', fail if fail else 'none')
sys.exit(1 if fail else 0)
