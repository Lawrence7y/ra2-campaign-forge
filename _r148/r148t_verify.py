#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R148 T：终态自检。五项 CR + 门禁实跑 + C16 钉 + 三个钉等于现算 + 无孤儿进程 + 三件产物一致。"""
import hashlib, io, json, os, re, subprocess, sys

ROOT = '/home/t628/projects/ra2-campaign-forge'
R14 = os.path.join(ROOT, 'lead', 'next_re_20261117_r14')
fails = []


def ck(n, c, d=''):
    print(('  PASS ' if c else '  FAIL ') + n + (('  ' + str(d)) if d else ''))
    if not c:
        fails.append(n)


def cr(p):
    return open(p, 'rb').read().count(b'\r')


T = {'R14_COMMON': (os.path.join(R14, 'R14_COMMON.md'), 1081),
     'LEDGER': (os.path.join(ROOT, 'lead', 'GOAL_THREE_TARGETS_20261018.md'), 337),
     'LEAD_LOCK': (os.path.join(ROOT, 'lead', 'LEAD_LOCK'), 137),
     'STATUS_BOARD': (os.path.join(R14, 'STATUS_BOARD.md'), 0),
     'BOARD_ARCHIVE': (os.path.join(R14, 'BOARD_ARCHIVE.md'), 2952)}
for k, (p, want) in T.items():
    got = cr(p)
    ck('CR %s == %d' % (k, want), got == want, got)

nl = open(T['STATUS_BOARD'][0], 'rb').read().count(b'\n')
ck('看板行数 <= 300', nl <= 300, nl)

# FACT_INDEX v5.40
fi = os.path.join(R14, 'R17_R112_FACTINDEX_V540', 'FACT_INDEX.tsv')
raw = open(fi, 'rb').read()
ck('FACT_INDEX v5.40 88,786 B', len(raw) == 88786, len(raw))
ck('FACT_INDEX v5.40 sha == fabd1e57…', hashlib.sha256(raw).hexdigest().startswith('fabd1e57'),
   hashlib.sha256(raw).hexdigest()[:16])
ck('FACT_INDEX 全 LF', b'\r' not in raw, raw.count(b'\r'))
ck('FACT_INDEX 54 数据行', len([l for l in raw.decode('utf-8').split('\n')[1:] if l.strip()]) == 54,
   len([l for l in raw.decode('utf-8').split('\n')[1:] if l.strip()]))

# 门禁实跑
r = subprocess.run([sys.executable, 'check_disc.py'], cwd=R14, capture_output=True, text=True,
                   timeout=300)
ck('门禁 exit 0', r.returncode == 0, r.returncode)
ck('门禁 C10 自检 ok(R148)', 'C10 self-check: ok(R148)' in r.stdout, '')
ck('门禁 C16 pinned 147 / unpinned 0',
   '147 sections measured (pinned 147)' in r.stdout and 'unpinned 0' in r.stdout, '')
ck('门禁 C16 min margin 20', 'min margin 20' in r.stdout, '')
_c16pin = re.search(r"C16_FLOORS_SHA256 = '([0-9a-f]{64})'",
                    io.open(os.path.join(R14, 'check_disc.py'), encoding='utf-8').read()).group(1)
ck('门禁 C16d pin OK（用现钉比对，不写死常量）',
   ('C16d floor-table pin: %s (OK)' % _c16pin[:16]) in r.stdout, _c16pin[:16])
ck('门禁 PASS 行', 'PASS  structure/paths/sections/self all ok' in r.stdout, '')

# 三钉等于现算
g = io.open(os.path.join(R14, 'check_disc.py'), encoding='utf-8', newline='').read()
m = re.search(r'C16_FLOORS = \{(.*?)\n\}', g, re.S)
tbl = {int(a): int(b) for a, b in re.findall(r'(\d+):\s*(\d+)', m.group(1))}
norm = '\n'.join('%d:%d' % (k, tbl[k]) for k in sorted(tbl))
ck('C16 钉 == 现算', hashlib.sha256(norm.encode()).hexdigest() ==
   re.search(r"C16_FLOORS_SHA256 = '([0-9a-f]{64})'", g).group(1), '')
dr = io.open(os.path.join(R14, 'DISC_RECHECK.tsv'), encoding='utf-8', newline='').read()
rows = [l.split('\t') for l in dr.split('\n')[1:] if l.strip()]
blob = '\n'.join('%s\t%s\t%s' % (x[0], x[4].strip(), x[5].strip()) for x in rows if len(x) == 7)
ck('C7d 钉 == 现算', hashlib.sha256(blob.encode()).hexdigest() ==
   re.search(r"C7_TEXT_SHA256 = '([0-9a-f]{64})'", g).group(1), '')
r20 = [x for x in rows if x[0] == '20'][0]
ck("C7_ROW_SHA['20'] == 现算",
   hashlib.sha256(('%s\t%s\t%s' % (r20[0], r20[4].strip(), r20[5].strip())).encode()).hexdigest()
   == re.search(r"'20': '([0-9a-f]{64})'", g).group(1), '')
du = io.open(os.path.join(R14, 'DISC_UNVERIFIABLE.tsv'), encoding='utf-8', newline='').read()
ck('FREEZE 钉 == 现算', hashlib.sha256(du.encode()).hexdigest() ==
   re.search(r"FREEZE_SHA256 = '([0-9a-f]{64})'", g).group(1), '')

# 四件套新节/新段存在且各恰 1 次
rc = io.open(os.path.join(R14, 'R14_COMMON.md'), encoding='utf-8', newline='').read()
ck('R14_COMMON §2.153 恰 1 次', rc.count('## 2.153 R148') == 1, rc.count('## 2.153 R148'))
led = io.open(os.path.join(ROOT, 'lead', 'GOAL_THREE_TARGETS_20261018.md'), encoding='utf-8',
              newline='').read()
ck('台账 §1203 恰 1 次', led.count('## §1203 R148') == 1, led.count('## §1203 R148'))
lk = io.open(os.path.join(ROOT, 'lead', 'LEAD_LOCK'), encoding='utf-8', newline='').read()
ck('LEAD_LOCK OG1 恰 1 次', lk.count('OG1. ✅ **交付一：FACT_INDEX v5.39') == 1,
   lk.count('OG1. ✅ **交付一：FACT_INDEX v5.39'))
ck('LEAD_LOCK OG10 恰 1 次', lk.count('OG10.') == 1, lk.count('OG10.'))
ck('LEAD_LOCK 无重复标签', len(re.findall(r'^(O[A-Z]\d+)\.', lk, re.M)) ==
   len(set(re.findall(r'^(O[A-Z]\d+)\.', lk, re.M))),
   len(re.findall(r'^(O[A-Z]\d+)\.', lk, re.M)))
bd = io.open(os.path.join(R14, 'STATUS_BOARD.md'), encoding='utf-8', newline='').read()
ck('看板第 148 轮恰 1 次', bd.count('## 🟢 R17 第 148 轮') == 1, bd.count('## 🟢 R17 第 148 轮'))
ck('看板 3 段', sum(1 for l in bd.split('\n') if l.startswith('## ')) == 3,
   sum(1 for l in bd.split('\n') if l.startswith('## ')))
arc = io.open(os.path.join(R14, 'BOARD_ARCHIVE.md'), encoding='utf-8', newline='').read()
ck('归档含 144/145 轮各 1 次',
   arc.count('## 🟢 R17 第 144 轮') == 1 and arc.count('## 🟢 R17 第 145 轮') == 1,
   (arc.count('## 🟢 R17 第 144 轮'), arc.count('## 🟢 R17 第 145 轮')))

# 孤儿进程
ps = subprocess.run(['bash', '-c',
                     "ps -eo pid,etimes,args | grep -E 'python3? .*(_r148/r148[a-z]|check_disc\\.py)' "
                     "| grep -v grep | grep -v r148t_verify || true"],
                    capture_output=True, text=True)
ck('无孤儿进程', ps.stdout.strip() == '', ps.stdout.strip()[:200])

print('\n=== FAILS: %d ===' % len(fails))
for f in fails:
    print('  ' + f)
json.dump(dict(fails=fails, board_lines=nl), open(os.path.join(ROOT, '_r148', 'r148t_verify.json'),
                                                  'w', encoding='utf-8'), ensure_ascii=False, indent=1)
sys.exit(1 if fails else 0)
