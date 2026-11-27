#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""r158j1_final_verify.py — 收口前终态核验（只读）。
逐项断言四项 CR 不变量、四件套落盘、门禁、产物完整性；并检查无孤儿进程。
"""
import hashlib, io, os, re, subprocess, sys

R = '/home/t628/projects/ra2-campaign-forge'
D = R + '/lead/next_re_20261117_r14'
P = {
    'R14_COMMON': (D + '/R14_COMMON.md', 1081),
    'LEDGER':     (R + '/lead/GOAL_THREE_TARGETS_20261018.md', 337),
    'LEAD_LOCK':  (R + '/lead/LEAD_LOCK', 137),
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

print('=== 1 · 五项 CR 不变量 ===')
for k, (p, cr) in P.items():
    t = io.open(p, encoding='utf-8', newline='').read()
    ck('%s CR == %d' % (k, cr), t.count('\r') == cr, t.count('\r'))
    ck('%s LF 标记保留' % k, '\n' in t, t.count('\n'))

print('\n=== 2 · 四件套落盘 ===')
rc = io.open(P['R14_COMMON'][0], encoding='utf-8', newline='').read().replace('\r\n', '\n')
ck('2.1 R14_COMMON 含 §2.163', len(re.findall(r'(?m)^##\s+2\.163\b', rc)) == 1,
   len(re.findall(r'(?m)^##\s+2\.163\b', rc)))
secs = [int(x) for x in re.findall(r'(?m)^##\s+2\.(\d+)\b', rc)]
ck('2.2 R14_COMMON 末节 == 163', max(secs) == 163, max(secs))
ck('2.3 R14_COMMON 节数 == 157', len(secs) == 157, len(secs))
led = io.open(P['LEDGER'][0], encoding='utf-8', newline='').read().replace('\r\n', '\n')
ck('2.4 台账含 §1213 恰 1 次', len(re.findall(r'(?m)^##\s+§1213\b', led)) == 1,
   len(re.findall(r'(?m)^##\s+§1213\b', led)))
locks = [int(x) for x in re.findall(r'(?m)^##\s+§(\d+)\b', led)]
ck('2.5 台账末节 == 1213', max(locks) == 1213, max(locks))
lk = io.open(P['LEAD_LOCK'][0], encoding='utf-8', newline='').read().replace('\r\n', '\n')
codes = re.findall(r'(?m)^##\s+([A-Z]{2})\s+·', lk)
ck('2.6 LEAD_LOCK 末段 == OI', codes and codes[-1] == 'OI', codes[-1] if codes else None)
ck('2.7 OI 段小标 OI1..OI11 齐全',
   all(('OI%d.' % i) in lk for i in range(1, 12)), 'ok')
sb = io.open(P['STATUS_BOARD'][0], encoding='utf-8', newline='').read()
sb_n = sb.replace('\r\n', '\n')
ck('2.8 看板含第 158 轮', '## 🟢 R17 第 158 轮' in sb_n, True)
nl = sb_n.count('\n') + (0 if sb_n.endswith('\n') else 1)
ck('2.9 看板行数 <= 300', nl <= 300, nl)
ck('2.10 看板全 LF', sb.count('\r') == 0, sb.count('\r'))

print('\n=== 3 · 看板归档等价性（R158 已归档 156/157 两段）===')
ba = io.open(P['BOARD_ARCHIVE'][0], encoding='utf-8', newline='').read()
ck('3.1 归档含 156 轮', '## 🟢 R17 第 156 轮' in ba, ba.count('## 🟢 R17 第 156 轮'))
ck('3.2 归档含 157 轮', '## 🟢 R17 第 157 轮' in ba, ba.count('## 🟢 R17 第 157 轮'))
ck('3.3 归档 CR == 2952', ba.count('\r') == 2952, ba.count('\r'))

print('\n=== 4 · 门禁 ===')
r = subprocess.run([sys.executable, 'check_disc.py'], cwd=D, capture_output=True, text=True,
                   timeout=900)
ck('4.1 门禁 exit == 0', r.returncode == 0, r.returncode)
tail = r.stdout.strip().split('\n')[-6:]
ck('4.2 门禁无 FAIL 行（行首锚定）',
   not any(l.lstrip().startswith('FAIL') for l in r.stdout.split('\n')),
   [l for l in r.stdout.split('\n') if l.lstrip().startswith('FAIL')][:3])
ck('4.3 门禁 C10 自检 ok(R158)', 'C10 self-check: ok(R158)' in r.stdout, 'ok')
ck('4.4 门禁 C16 157 节全钉', '157 sections measured (pinned 157)' in r.stdout, 'ok')
ck('4.5 门禁 C12b 12/12 镜像', '12/12 rows identical' in r.stdout, 'ok')

print('\n=== 5 · 本轮产物完整性 ===')
art = ['r158a_fact_ledger_scan.py', 'r158a_fact_ledger_scan.json',
       'r158b_evidchain_recount.py', 'r158b_evidchain_recount.json',
       'r158c_version_scope.py', 'r158c_version_scope.json',
       'r158d_bounds_bytes.py', 'r158d_bounds_bytes.json',
       'r158e_ruleD_recheck.py', 'r158e_ruleD_recheck.json']
for a in art:
    ck('5.1 产物存在 %s' % a, os.path.exists(os.path.join(R, '_r158', a)),
       os.path.getsize(os.path.join(R, '_r158', a)) if os.path.exists(os.path.join(R, '_r158', a)) else 0)

print('\n=== 6 · 无孤儿进程 / 无遗留 tmp ===')
# S-442：首版 grep 'r158[a-z]' 会命中**本会话自身**的 claude 命令行（其中含「第 158 轮」字样），
# 那 3 个条目全是 pid 909747 的同一进程 ⇒ 假 FAIL。正确判据是「有无 python3 _r158/*.py 在跑」。
ps = subprocess.run(['bash', '-c',
                     "ps -eo pid,cmd | grep -E 'python3 .*_r158/[a-z0-9_]+\\.py' | grep -v grep | wc -l"],
                    capture_output=True, text=True)
ck('6.1 无 python3 _r158 脚本残留进程', ps.stdout.strip() in ('0', ''), ps.stdout.strip())
ps2 = subprocess.run(['bash', '-c',
                      "ps -eo pid,cmd | grep -c 'claude -p' || true"], capture_output=True, text=True)
print('  (参考：当前会话自身 claude -p 计数 = %s，非本卡残留)' % ps2.stdout.strip())
tmps = subprocess.run(['bash', '-c', "ls %s/*.r15*tmp 2>/dev/null | wc -l" % D],
                      capture_output=True, text=True)
ck('6.2 无遗留 .tmp', tmps.stdout.strip() == '0', tmps.stdout.strip())

print('\n=== 7 · 关键数字回归（防落盘后漂移）===')
for f, expect in (('r158c_version_scope.json', None), ('r158d_bounds_bytes.json', None)):
    import json
    d = json.load(open(os.path.join(R, '_r158', f), encoding='utf-8'))
    ck('7.1 %s 的断言全 PASS' % f,
       d.get('n_fail', d.get('checks') and sum(1 for x in d['checks'] if not x['pass'])) == 0,
       d.get('n_pass'))
import json
vb = json.load(open(os.path.join(R, '_r158', 'r158c_version_scope.json'), encoding='utf-8'))
ck('7.2 V532 part == 32', len(vb['table']['R17_R104_FACTINDEX_V532']['part']) == 32,
   len(vb['table']['R17_R104_FACTINDEX_V532']['part']))
ck('7.3 V542 part == 33', len(vb['table']['R17_R114_FACTINDEX_V542']['part']) == 33,
   len(vb['table']['R17_R114_FACTINDEX_V542']['part']))
bd = json.load(open(os.path.join(R, '_r158', 'r158d_bounds_bytes.json'), encoding='utf-8'))
ck('7.4 bounds 命中 1,392,592 / 未命中 0',
   bd['hit'] == 1392592 and bd['miss'] == 0, (bd['hit'], bd['miss']))

print('\nFAILS=%d' % len(fails))
sys.exit(0 if not fails else 1)
