#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R157 终态收口校验：五项 CR 不变量、四件套落盘、门禁、无孤儿进程。

幂等：纯校验，可反复跑。
"""
import hashlib, io, os, re, subprocess, sys

R = '/home/t628/projects/ra2-campaign-forge'
D = R + '/lead/next_re_20261117_r14'
FILES = {
    'R14_COMMON': (D + '/R14_COMMON.md', 1081),
    'LEAD_LOCK': (R + '/lead/LEAD_LOCK', 137),
    'LEDGER': (R + '/lead/GOAL_THREE_TARGETS_20261018.md', 337),
    'STATUS_BOARD': (D + '/STATUS_BOARD.md', 0),
    'BOARD_ARCHIVE': (D + '/BOARD_ARCHIVE.md', 2952),
}
fails = []
def ck(n, c, d=''):
    ok = bool(c)
    print(('  PASS ' if ok else '  FAIL ') + n + (('  ' + str(d)) if d else ''))
    if not ok:
        fails.append(n)
    return ok

print('== 1 · 五项 CR 不变量 ==')
state = {}
for name, (p, want) in FILES.items():
    b = open(p, 'rb').read()
    cr = b.count(b'\r')
    h = hashlib.sha256(b).hexdigest()[:8]
    state[name] = (len(b), cr, h)
    ck('%s CR == %d' % (name, want), cr == want, cr)
    print('    %-14s %9d B / CR=%-5d / sha=%s' % (name, len(b), cr, h))

print()
print('== 2 · 本轮四件套落盘 ==')
rc = io.open(FILES['R14_COMMON'][0], encoding='utf-8', newline='').read()
ck('2.1 R14_COMMON 含 §2.162', '## 2.162 ' in rc, '')
secs = [int(x) for x in re.findall(r'(?m)^## 2\.(\d+)\b', rc)]
ck('2.2 R14_COMMON 节数 = 156、末节 = 162', len(secs) == 156 and max(secs) == 162,
   (len(secs), max(secs)))

led = io.open(FILES['LEDGER'][0], encoding='utf-8', newline='').read()
ck('2.3 台账含 §1212', '## §1212 ' in led, '')
lsecs = [int(x) for x in re.findall(r'(?m)^## §(\d+)\b', led)]
ck('2.4 台账 max 节 = 1212', max(lsecs) == 1212, max(lsecs))

lock = io.open(FILES['LEAD_LOCK'][0], encoding='utf-8', newline='').read()
codes = re.findall(r'(?m)^## ([A-Z]{1,3}) ·', lock)
ck('2.5 LEAD_LOCK 末段 = OH', codes[-1] == 'OH', codes[-3:])

board = io.open(FILES['STATUS_BOARD'][0], encoding='utf-8', newline='').read()
nb = board.count('\n')
ck('2.6 看板含第 157 轮段', '## 🟢 R17 第 157 轮' in board, '')
ck('2.7 看板总行数 <= 300', nb <= 300, nb)
print('    看板 %d 行 / %d B' % (nb, len(board.encode())))

ba = io.open(FILES['BOARD_ARCHIVE'][0], encoding='utf-8', newline='').read()
ck('2.8 归档含 R154 段（本轮搬入）', '## 🟢 R17 第 154 轮' in ba, '')
ck('2.9 归档含 R155 段（本轮搬入）', '## 🟢 R17 第 155 轮' in ba, '')
ck('2.10 看板已不含 R154/R155（已搬走）',
   '## 🟢 R17 第 154 轮' not in board and '## 🟢 R17 第 155 轮' not in board, '')

print()
print('== 3 · 门禁 ==')
r = subprocess.run([sys.executable, D + '/check_disc.py'], capture_output=True, text=True, timeout=300)
out = r.stdout + r.stderr
ck('3.1 门禁 exit code == 0', r.returncode == 0, r.returncode)
bad = [l for l in out.split('\n') if re.match(r'^\s*(FAIL|\[FAIL\])', l)]
ck('3.2 无 FAIL 行（行首锚定）', not bad, bad[:5])
m = re.search(r'C10 self-check: ok\((\w+)\)', out)
ck('3.3 C10 自检 ok(R157)', m and m.group(1) == 'R157', m.group(1) if m else None)
m = re.search(r'C16 per-section floors: (\d+) sections measured \(pinned (\d+)\).*unpinned (\d+)', out)
ck('3.4 C16 156/156、unpinned 0', m and m.group(1) == '156' and m.group(3) == '0',
   m.groups() if m else None)

print()
print('== 4 · 产物齐备 ==')
for f in ('r157a_f23_ruling_premises.py', 'r157a_f23_ruling_premises.json',
          'r157b_audit_recheck.py', 'r157b_audit_recheck.json',
          'r157c_write_rc.py', 'r157d_write_ledger.py', 'r157e_write_lock.py',
          'r157f_write_board.py', 'r157g_archive_board.py', 'r157h_gate.py'):
    p = os.path.join(R, '_r157', f)
    ck('4.%s %s' % ('x', f), os.path.exists(p), '')

print()
print('== 5 · 无孤儿进程 ==')
ps = subprocess.run(['ps', '-eo', 'pid,args'], capture_output=True, text=True).stdout
me = os.getpid()
orphans = []
for l in ps.split('\n')[1:]:
    l = l.strip()
    if not l:
        continue
    pid_s, _, args = l.partition(' ')
    try:
        pid = int(pid_s)
    except ValueError:
        continue
    if pid == me:
        continue
    # 只找本轮脚本残留，且排除本校验自身
    if re.search(r'_r157/r157[a-h]_', args) and 'r157i_final' not in args:
        orphans.append((pid, args[:90]))
ck('5.1 无本轮脚本孤儿进程', not orphans, orphans[:5])

print()
print('== 收口 ==')
if fails:
    print('FAIL 共 %d 条：' % len(fails))
    for f in fails:
        print('   -', f)
else:
    print('全部 PASS（无 FAIL）')
sys.exit(1 if fails else 0)
