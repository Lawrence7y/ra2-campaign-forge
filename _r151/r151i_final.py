#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R151 终态校验：五项 CR、看板行数、门禁、C16 重钉、归档次数、无孤儿进程、FACT_INDEX 未改。"""
import hashlib, io, os, re, subprocess, sys

ROOT = '/home/t628/projects/ra2-campaign-forge'
D = os.path.join(ROOT, 'lead', 'next_re_20261117_r14')
fail = []
def ck(n, c, d=''):
    ok = bool(c)
    print(('  PASS ' if ok else '  FAIL ') + n + (('  ' + str(d)) if d else ''))
    if not ok: fail.append(n)
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
ck('看板含 R151 段且不含 R148/R149 段',
   '第 151 轮'.encode() in open(F['STATUS_BOARD'][0], 'rb').read()
   and '第 148 轮'.encode() not in open(F['STATUS_BOARD'][0], 'rb').read()
   and '第 149 轮'.encode() not in open(F['STATUS_BOARD'][0], 'rb').read())

# 归档：R148/R149 各出现 1 次（段标题）
arc = open(F['BOARD_ARCHIVE'][0], encoding='utf-8').read()
ck('归档含 R148 段标题 1 次', arc.count('第 148 轮') == 1, arc.count('第 148 轮'))
ck('归档含 R149 段标题 1 次', arc.count('第 149 轮') == 1, arc.count('第 149 轮'))

# 新节/新段存在性
rc = io.open(F['R14_COMMON'][0], encoding='utf-8', newline='').read()
ck('R14_COMMON 含 §2.156 且唯一', rc.count('## 2.156') == 1, rc.count('## 2.156'))
led = io.open(F['LEDGER'][0], encoding='utf-8', newline='').read()
ck('台账含 §1206 且唯一', led.count('## §1206') == 1, led.count('## §1206'))
lk = io.open(F['LEAD_LOCK'][0], encoding='utf-8', newline='').read()
ck('LEAD_LOCK 含 OI1..OI11', all(('\nOI%d.' % i) in lk for i in range(1, 12)))

# 门禁
r = subprocess.run([sys.executable, 'check_disc.py'], cwd=D, capture_output=True, text=True, timeout=300)
ck('门禁 exit 0', r.returncode == 0, r.returncode)
ck('C10 ok(R151)', 'ok(R151)' in r.stdout)
m = re.search(r'C16 per-section floors: (\d+) sections measured \(pinned (\d+)\), hollow/deficient (\d+), missing (\d+), unpinned (\d+)',
              r.stdout)
ck('C16 150/150 且 unpinned 0', m and m.group(1) == '150' and m.group(2) == '150'
   and m.group(5) == '0', m.groups() if m else None)
ck('C16d 钉 ok', 'floor-table pin: 5c67b2952a42cc80 (OK)' in r.stdout)
ck('C7d 新钉 a46f9253', 'sha256=a46f92530475a0b3' in r.stdout)
ck('C12/C12b 12/12', '12 frozen rows, 12 anchors hit' in r.stdout
   and '12/12 rows identical' in r.stdout)

# C16[156] = 体字节一半
cur, buf, out = None, [], {}
for l in rc.split('\n'):
    mm = re.match(r'^##\s+2\.(\d+)\b', l)
    if mm:
        if cur is not None: out[cur] = len('\n'.join(buf).encode('utf-8'))
        cur = int(mm.group(1)); buf = [l]
    elif cur is not None: buf.append(l)
if cur is not None: out[cur] = len('\n'.join(buf).encode('utf-8'))
src = open(os.path.join(D, 'check_disc.py'), encoding='utf-8').read()
T = {int(a): int(b) for a, b in re.findall(r'(\d+):\s*(\d+)',
     re.search(r'C16_FLOORS = \{(.*?)\n\}', src, re.S).group(1))}
ck('C16[156] == §2.156 含标题体 // 2', T.get(156) == out[156] // 2, (T.get(156), out[156]))

# FACT_INDEX 未改
fx = os.path.join(D, 'R17_R112_FACTINDEX_V540', 'FACT_INDEX.tsv')
h = hashlib.sha256(open(fx, 'rb').read()).hexdigest()
ck('FACT_INDEX v540 sha 仍 fabd1e57…', h.startswith('fabd1e57'), h[:12])

# 无孤儿进程
ps = subprocess.run(['bash', '-c', 'ps -eo pid,cmd | grep -E "r151|_r151" | grep -v grep | grep -v r151i || true'],
                    capture_output=True, text=True)
ck('无 r151 孤儿进程', ps.stdout.strip() == '', ps.stdout.strip()[:200])

print('\nFAIL %d：%s' % (len(fail), fail))
sys.exit(1 if fail else 0)
