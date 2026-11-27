#!/usr/bin/env python3
"""R168 R：收口总校验（以磁盘为准，五项 CR 不变量 + 三道门 + 四件套一致性 + 无孤儿进程）。"""
import hashlib, json, os, re, subprocess, sys
ROOT = '/home/t628/projects/ra2-campaign-forge'
T = ROOT + '/lead/next_re_20261117_r14'
FILES = {
 'R14_COMMON': (T + '/R14_COMMON.md', 1081),
 'STATUS_BOARD': (T + '/STATUS_BOARD.md', 0),
 'BOARD_ARCHIVE': (T + '/BOARD_ARCHIVE.md', 2952),
 'LEAD_LOCK': (ROOT + '/lead/LEAD_LOCK', 137),
 'LEDGER': (ROOT + '/lead/GOAL_THREE_TARGETS_20261018.md', 337),
}
A = []; rec = {}
for k, (p, cr) in FILES.items():
    b = open(p, 'rb').read()
    rec[k] = {'sha256': hashlib.sha256(b).hexdigest(), 'bytes': len(b),
              'cr': b.count(b'\r'), 'lf': b.count(b'\n')}
    A.append({'id': 'R_CR %s CR==%d' % (k, cr), 'ok': b.count(b'\r') == cr, 'detail': str(b.count(b'\r'))})
A.append({'id': 'R_board 行数 <= 300', 'ok': rec['STATUS_BOARD']['lf'] <= 300,
          'detail': str(rec['STATUS_BOARD']['lf'])})
# 四件套新段落存在
rc = open(FILES['R14_COMMON'][0], encoding='utf-8').read()
led = open(FILES['LEDGER'][0], encoding='utf-8').read()
lock = open(FILES['LEAD_LOCK'][0], encoding='utf-8').read()
brd = open(FILES['STATUS_BOARD'][0], encoding='utf-8').read()
A.append({'id': 'R_sec 四件套新段各恰 1 处',
          'ok': rc.count('## 2.173 ·') == 1 and led.count('## §1223 ·') == 1
          and lock.count('## OY · R17 第 168 轮') == 1 and brd.count('## 🟢 R17 第 168 轮') == 1})
# FACT_INDEX V548
v548 = T + '/R17_R120_FACTINDEX_V548/FACT_INDEX.tsv'
b548 = open(v548, 'rb').read()
A.append({'id': 'R_facts V548 = 113,574 B / 55 行 / LF-only / ef1716cf…',
          'ok': len(b548) == 113574 and b548.count(b'\n') == 55 and b548.count(b'\r') == 0
          and hashlib.sha256(b548).hexdigest().startswith('ef1716cf')})
v547 = T + '/R17_R119_FACTINDEX_V547/FACT_INDEX.tsv'
A.append({'id': 'R_facts V547 一字未改（919263cf… / 109,220 B）',
          'ok': hashlib.sha256(open(v547, 'rb').read()).hexdigest().startswith('919263cf')
          and len(open(v547, 'rb').read()) == 109220})
# 三道门
env = dict(os.environ)
def run(cmd):
    r = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, timeout=600)
    return r.returncode, r.stdout
e1, o1 = run([sys.executable, T + '/check_disc.py'])
e2, o2 = run([sys.executable, ROOT + '/_r160/facts_floors.py'])
e3, o3 = run([sys.executable, ROOT + '/_r161/gate_runner.py'])
A.append({'id': 'R_gate check_disc exit 0 且 FAIL 0', 'ok': e1 == 0 and 'FAIL  0' not in o1,
          'detail': 'exit=%d' % e1})
A.append({'id': 'R_gate facts_floors exit 0', 'ok': e2 == 0, 'detail': 'exit=%d' % e2})
A.append({'id': 'R_gate gate_runner exit 0 且 G1=G2=G3=ok', 'ok': e3 == 0
          and 'G1=ok' in o3 and 'G2=ok' in o3 and 'G3=ok' in o3, 'detail': 'exit=%d' % e3})
m = re.search(r'C16 per-section floors: (\d+) sections measured \(pinned (\d+)\).*unpinned (\d+)', o1)
A.append({'id': 'R_C16 167 节全钉、unpinned 0',
          'ok': bool(m) and m.group(1) == '167' and m.group(2) == '167' and m.group(3) == '0',
          'detail': m.group(0) if m else 'NO NOTE'})
# 无孤儿进程
ps = subprocess.run(['pgrep', '-fa', 'r168[abcdefghijklmnopq]'], capture_output=True, text=True)
A.append({'id': 'R_orphan 无 r168 脚本残留进程', 'ok': ps.returncode != 0 or not ps.stdout.strip(),
          'detail': ps.stdout.strip()[:200]})
out = {'files': rec, 'gates': {'check_disc': e1, 'facts_floors': e2, 'gate_runner': e3},
       'v548_sha': hashlib.sha256(b548).hexdigest(),
       'assertions': A, 'fail': sum(1 for a in A if not a['ok'])}
json.dump(out, open(ROOT + '/_r168/r168r_final_verify.json', 'w'), ensure_ascii=False, indent=1)
for k, v in rec.items(): print('%-14s CR=%-5d LF=%-6d %s' % (k, v['cr'], v['lf'], v['sha256'][:16]))
print('gates:', out['gates'])
for a in A: print(('PASS' if a['ok'] else 'FAIL'), a['id'], a.get('detail', '')[:120])
print('FAIL count =', out['fail'])
